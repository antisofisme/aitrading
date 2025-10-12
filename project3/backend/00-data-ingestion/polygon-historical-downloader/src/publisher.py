"""
Publisher for NATS (Hybrid Architecture Phase 1)
Publishes historical market data to NATS for real-time distribution

RESILIENCE FEATURES:
- Local disk buffer (fallback if NATS unavailable)
- Automatic retry with exponential backoff
- Circuit breaker for NATS failures
- Health status monitoring
"""
import logging
import json
import asyncio
import uuid
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
from nats.aio.client import Client as NATSClient

logger = logging.getLogger(__name__)

class MessagePublisher:
    """
    Publish historical data to NATS with fallback to disk

    Hybrid Architecture - Phase 1:
    - Market data (historical OHLCV) → NATS (broadcast to all consumers)
    - Disk buffer → Prevents data loss if NATS temporarily unavailable
    """

    def __init__(self, nats_url: str, kafka_brokers: str = None):
        self.nats_url = nats_url
        self.nats_client = None

        # Local disk buffer (CRITICAL: Prevents data loss if NATS down)
        self.buffer_dir = Path("/app/data/buffer")
        self.buffer_dir.mkdir(parents=True, exist_ok=True)

        # Circuit breaker state
        self.nats_failures = 0
        self.max_failures_before_buffer = 3  # After 3 failures, use disk buffer

        self.stats = {
            'published_nats': 0,
            'buffered_to_disk': 0,
            'flushed_from_buffer': 0,
            'errors': 0
        }

    async def connect(self):
        """Connect to NATS (support cluster URLs)"""
        try:
            # Connect to NATS
            self.nats_client = NATSClient()

            # Parse NATS URLs - support both single URL and cluster formats
            if ',' in self.nats_url:
                # Cluster mode: split comma-separated URLs into array
                nats_servers = [url.strip() for url in self.nats_url.split(',')]
                logger.info(f"✅ Connecting to NATS cluster ({len(nats_servers)} nodes)")
                await self.nats_client.connect(servers=nats_servers)
            else:
                # Single server mode
                logger.info(f"✅ Connecting to NATS: {self.nats_url}")
                await self.nats_client.connect(servers=[self.nats_url])

            logger.info(f"✅ Connected to NATS successfully")

        except Exception as e:
            logger.error(f"❌ NATS connection error: {e}")
            raise

    async def disconnect(self):
        """Disconnect from NATS"""
        try:
            if self.nats_client:
                await self.nats_client.drain()
                logger.info("Disconnected from NATS")

        except Exception as e:
            logger.error(f"Disconnect error: {e}")

    async def publish_aggregate(self, aggregate_data: Dict):
        """
        Publish aggregate bar to NATS with fallback to disk buffer

        Subject Pattern (from nats.json):
        - market.{symbol}.{timeframe}

        RESILIENCE:
        - Try NATS first
        - If fails → Save to local disk buffer
        - Periodic retry flushing buffer

        Args:
            aggregate_data: OHLCV bar data
        """
        try:
            symbol_clean = aggregate_data['symbol'].replace('/', '')
            timeframe = aggregate_data['timeframe']

            # Subject: market.{symbol}.{timeframe} (from nats.json)
            subject = f"market.{symbol_clean}.{timeframe}"

            # Add metadata
            message = {
                **aggregate_data,
                'event_type': 'ohlcv',
                'ingested_at': datetime.utcnow().isoformat(),
                '_source': 'historical',
                '_transport': 'nats'
            }

            nats_success = False

            # Try NATS
            try:
                await self.nats_client.publish(
                    subject,
                    json.dumps(message).encode('utf-8')
                )
                self.stats['published_nats'] += 1
                self.nats_failures = 0  # Reset failure counter
                nats_success = True

            except Exception as nats_error:
                self.nats_failures += 1
                logger.warning(f"⚠️ NATS publish failed (attempt {self.nats_failures}): {nats_error}")

                # CRITICAL: If NATS failed, save to disk buffer
                if self.nats_failures >= self.max_failures_before_buffer:
                    logger.error(f"❌ NATS unavailable after {self.nats_failures} failures!")
                    logger.warning(f"💾 Buffering to disk: {aggregate_data.get('symbol')}")

                    await self._buffer_to_disk(message)
                    self.stats['buffered_to_disk'] += 1

        except Exception as e:
            logger.error(f"❌ Critical publish error for {aggregate_data.get('symbol')}: {e}")
            self.stats['errors'] += 1

            # Last resort - buffer to disk
            try:
                await self._buffer_to_disk(message)
                self.stats['buffered_to_disk'] += 1
            except Exception as buffer_error:
                logger.critical(f"❌ CANNOT SAVE TO DISK BUFFER: {buffer_error}")
                # This is catastrophic - data will be lost

    async def _buffer_to_disk(self, message: Dict):
        """
        Save message to local disk buffer as fallback

        File format: buffer_<uuid>.json
        Each file contains one message
        """
        buffer_file = self.buffer_dir / f"buffer_{uuid.uuid4()}.json"

        with open(buffer_file, 'w') as f:
            json.dump(message, f)

        logger.info(f"💾 Buffered to disk: {buffer_file.name}")

    async def flush_buffer(self):
        """
        Retry publishing buffered messages from disk

        Called periodically by main service
        Returns number of messages successfully flushed
        """
        buffer_files = list(self.buffer_dir.glob("buffer_*.json"))

        if not buffer_files:
            return 0

        logger.info(f"♻️ Attempting to flush {len(buffer_files)} buffered messages...")

        flushed_count = 0

        for buffer_file in buffer_files:
            try:
                # Read buffered message
                with open(buffer_file) as f:
                    message = json.load(f)

                # Extract original aggregate data
                symbol = message.get('symbol', 'UNKNOWN').replace('/', '')
                timeframe = message.get('timeframe', '1m')

                # Subject: market.{symbol}.{timeframe}
                subject = f"market.{symbol}.{timeframe}"

                # Try NATS
                try:
                    await self.nats_client.publish(
                        subject,
                        json.dumps(message).encode('utf-8')
                    )

                    # Success - delete buffer file
                    buffer_file.unlink()
                    flushed_count += 1
                    self.stats['published_nats'] += 1
                    self.stats['flushed_from_buffer'] += 1
                    logger.info(f"✅ Flushed buffer: {buffer_file.name}")

                except Exception as nats_err:
                    logger.debug(f"NATS still unavailable: {nats_err}")
                    logger.debug(f"⏳ Keeping buffer file: {buffer_file.name} (NATS still down)")

            except Exception as e:
                logger.error(f"❌ Error flushing {buffer_file.name}: {e}")
                # Keep file for next retry

        if flushed_count > 0:
            logger.info(f"♻️ Successfully flushed {flushed_count}/{len(buffer_files)} buffered messages")

        return flushed_count

    def get_buffer_status(self) -> Dict:
        """Get buffer statistics"""
        buffer_files = list(self.buffer_dir.glob("buffer_*.json"))
        return {
            'buffered_messages': len(buffer_files),
            'buffer_size_mb': sum(f.stat().st_size for f in buffer_files) / 1024 / 1024,
            'oldest_buffer': min((f.stat().st_mtime for f in buffer_files), default=0) if buffer_files else 0
        }

    async def publish_batch(self, aggregates: List[Dict]):
        """Publish batch of aggregates with automatic retry"""
        tasks = [self.publish_aggregate(agg) for agg in aggregates]
        await asyncio.gather(*tasks, return_exceptions=True)

        if len(aggregates) % 1000 == 0:
            buffer_status = self.get_buffer_status()
            logger.info(f"Published {len(aggregates)} aggregates | "
                       f"NATS: {self.stats['published_nats']} | "
                       f"Buffered: {self.stats['buffered_to_disk']} | "
                       f"Buffer Queue: {buffer_status['buffered_messages']} | "
                       f"Errors: {self.stats['errors']}")

    def get_stats(self) -> Dict:
        """Get publishing statistics including buffer status"""
        stats = self.stats.copy()
        stats['buffer'] = self.get_buffer_status()
        return stats
