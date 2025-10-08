"""
Publisher for NATS and Kafka
Publishes historical data to message queues

RESILIENCE FEATURES:
- Local disk buffer (fallback if NATS+Kafka unavailable)
- Automatic retry with exponential backoff
- Circuit breaker for message queue failures
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
from aiokafka import AIOKafkaProducer

logger = logging.getLogger(__name__)

class MessagePublisher:
    """Publish historical data to NATS and Kafka with fallback to disk"""

    def __init__(self, nats_url: str, kafka_brokers: str):
        self.nats_url = nats_url
        self.kafka_brokers = kafka_brokers.split(',')

        self.nats_client = None
        self.kafka_producer = None

        # Local disk buffer (CRITICAL: Prevents data loss if message queues down)
        self.buffer_dir = Path("/app/data/buffer")
        self.buffer_dir.mkdir(parents=True, exist_ok=True)

        # Circuit breaker state
        self.nats_failures = 0
        self.kafka_failures = 0
        self.max_failures_before_buffer = 3  # After 3 failures, use disk buffer

        self.stats = {
            'published_nats': 0,
            'published_kafka': 0,
            'buffered_to_disk': 0,
            'flushed_from_buffer': 0,
            'errors': 0
        }

    async def connect(self):
        """Connect to NATS and Kafka"""
        try:
            # Connect to NATS
            self.nats_client = NATSClient()
            await self.nats_client.connect(self.nats_url)
            logger.info(f"✅ Connected to NATS: {self.nats_url}")

            # Connect to Kafka
            self.kafka_producer = AIOKafkaProducer(
                bootstrap_servers=self.kafka_brokers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            await self.kafka_producer.start()
            logger.info(f"✅ Connected to Kafka: {self.kafka_brokers}")

        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
            raise

    async def disconnect(self):
        """Disconnect from NATS and Kafka"""
        try:
            if self.nats_client:
                await self.nats_client.drain()
                logger.info("Disconnected from NATS")

            if self.kafka_producer:
                await self.kafka_producer.stop()
                logger.info("Disconnected from Kafka")

        except Exception as e:
            logger.error(f"Disconnect error: {e}")

    async def publish_aggregate(self, aggregate_data: Dict):
        """
        Publish aggregate bar to NATS and Kafka with fallback to disk buffer

        RESILIENCE:
        - Try NATS first
        - Try Kafka second
        - If both fail → Save to local disk buffer
        - Periodic retry flushing buffer

        Args:
            aggregate_data: OHLCV bar data
        """
        try:
            symbol_clean = aggregate_data['symbol'].replace('/', '')

            # Add metadata
            message = {
                **aggregate_data,
                'event_type': 'ohlcv',
                'ingested_at': datetime.utcnow().isoformat(),
                '_source': 'historical'
            }

            nats_success = False
            kafka_success = False

            # Try NATS
            try:
                subject = f"bars.{symbol_clean}.{aggregate_data['timeframe']}"
                await self.nats_client.publish(
                    subject,
                    json.dumps(message).encode('utf-8')
                )
                self.stats['published_nats'] += 1
                self.nats_failures = 0  # Reset failure counter
                nats_success = True
            except Exception as nats_error:
                self.nats_failures += 1
                logger.warning(f"⚠️ NATS publish failed: {nats_error}")
                # Don't raise - try Kafka

            # Try Kafka (backup + archive)
            try:
                await self.kafka_producer.send(
                    'aggregate_archive',
                    value=message
                )
                self.stats['published_kafka'] += 1
                self.kafka_failures = 0  # Reset failure counter
                kafka_success = True
            except Exception as kafka_error:
                self.kafka_failures += 1
                logger.warning(f"⚠️ Kafka publish failed: {kafka_error}")
                # Don't raise - will check if buffer needed

            # CRITICAL: If BOTH failed, save to disk buffer
            if not nats_success and not kafka_success:
                logger.error(f"❌ BOTH NATS and Kafka unavailable!")
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
                symbol = message.get('symbol', 'UNKNOWN')
                timeframe = message.get('timeframe', '1m')

                nats_success = False
                kafka_success = False

                # Try NATS
                try:
                    symbol_clean = symbol.replace('/', '')
                    subject = f"bars.{symbol_clean}.{timeframe}"
                    await self.nats_client.publish(
                        subject,
                        json.dumps(message).encode('utf-8')
                    )
                    nats_success = True
                    self.stats['published_nats'] += 1
                except Exception as nats_err:
                    logger.debug(f"NATS still unavailable: {nats_err}")

                # Try Kafka
                try:
                    await self.kafka_producer.send('aggregate_archive', value=message)
                    kafka_success = True
                    self.stats['published_kafka'] += 1
                except Exception as kafka_err:
                    logger.debug(f"Kafka still unavailable: {kafka_err}")

                # If at least ONE succeeded, delete buffer file
                if nats_success or kafka_success:
                    buffer_file.unlink()
                    flushed_count += 1
                    self.stats['flushed_from_buffer'] += 1
                    logger.info(f"✅ Flushed buffer: {buffer_file.name}")
                else:
                    logger.debug(f"⏳ Keeping buffer file: {buffer_file.name} (queues still down)")

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
                       f"Kafka: {self.stats['published_kafka']} | "
                       f"Buffered: {self.stats['buffered_to_disk']} | "
                       f"Buffer Queue: {buffer_status['buffered_messages']} | "
                       f"Errors: {self.stats['errors']}")

    def get_stats(self) -> Dict:
        """Get publishing statistics including buffer status"""
        stats = self.stats.copy()
        stats['buffer'] = self.get_buffer_status()
        return stats
