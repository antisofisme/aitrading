"""
NATS Publisher for Dukascopy historical data
Reuses pattern from polygon-historical-downloader
"""
import asyncio
import json
import logging
import os
from typing import Optional, List, Dict
from nats.aio.client import Client as NATS

logger = logging.getLogger(__name__)


class NATSPublisher:
    """
    Publishes 1-minute OHLCV bars to NATS cluster

    Features:
    - Cluster support (3-node NATS)
    - Batch publishing (100 bars at a time)
    - Automatic reconnection
    - Publishing statistics
    """

    def __init__(self, nats_config: dict):
        """
        Args:
            nats_config: NATS configuration from Central Hub
                {
                    'url': 'nats://nats-1:4222,nats://nats-2:4222,nats://nats-3:4222',
                    'max_reconnect_attempts': -1,
                    'reconnect_time_wait': 2
                }
        """
        self.nats_config = nats_config
        # Use environment variable NATS_URL as fallback (configured in docker-compose.yml)
        default_nats_url = os.getenv('NATS_URL', 'nats://nats-1:4222,nats://nats-2:4222,nats://nats-3:4222')
        self.nats_url = nats_config.get('url', default_nats_url)
        self.nc: Optional[NATS] = None

        # Statistics
        self.publish_count = 0
        self.error_count = 0

    async def connect(self):
        """
        Connect to NATS cluster

        Supports both single server and cluster URLs:
        - Single: 'nats://nats-1:4222'
        - Cluster: 'nats://nats-1:4222,nats://nats-2:4222,nats://nats-3:4222'
        """
        try:
            self.nc = NATS()

            # Parse NATS URLs - support both single URL and cluster formats
            if ',' in self.nats_url:
                # Cluster mode: split comma-separated URLs into array
                nats_servers = [url.strip() for url in self.nats_url.split(',')]
                logger.info(f"✅ Connecting to NATS cluster ({len(nats_servers)} nodes)")
            else:
                # Single server mode
                nats_servers = [self.nats_url]
                logger.info(f"✅ Connecting to NATS: {self.nats_url}")

            await self.nc.connect(
                servers=nats_servers,
                max_reconnect_attempts=self.nats_config.get('max_reconnect_attempts', -1),
                reconnect_time_wait=self.nats_config.get('reconnect_time_wait', 2),
                ping_interval=self.nats_config.get('ping_interval', 120)
            )

            logger.info(f"✅ NATS Connected (Dukascopy historical data)")

        except Exception as e:
            logger.error(f"❌ NATS connection FAILED: {e}")
            raise

    async def publish_tick(self, tick: Dict):
        """
        Publish single raw tick to NATS

        Subject Pattern:
        - market.{symbol}.tick

        Example:
        - market.EURUSD.tick
        - market.GBPUSD.tick

        Format (matching TimescaleDB market_ticks):
        {
            'timestamp': datetime,
            'symbol': 'EUR/USD',
            'bid': 1.09990,
            'ask': 1.10000,
            'mid': 1.09995,
            'spread': 0.00010,
            'volume': 2.0,
            'source': 'dukascopy_historical'
        }

        Args:
            tick: Raw tick data dictionary
        """
        # Get symbol
        symbol = tick.get('symbol', '').replace('/', '')

        # Subject: market.{symbol}.tick (same as polygon-live-collector)
        subject = f"market.{symbol}.tick"

        # Ensure metadata is set
        tick['_transport'] = 'nats'
        tick['source'] = 'dukascopy_historical'

        message = json.dumps(tick, default=str).encode('utf-8')

        try:
            await self.nc.publish(subject, message)
            self.publish_count += 1

            # Log progress
            if self.publish_count % 50000 == 0:
                logger.info(f"📤 NATS published {self.publish_count} ticks")

        except Exception as e:
            logger.error(f"❌ NATS publish failed for {symbol}: {e}")
            self.error_count += 1
            raise

    async def publish_batch(self, ticks: List[Dict], batch_size: int = 1000):
        """
        Publish ticks in batches for efficiency

        Args:
            ticks: List of raw ticks
            batch_size: Number of ticks per batch (default 1000)
        """
        for i in range(0, len(ticks), batch_size):
            batch = ticks[i:i + batch_size]

            # Publish all ticks in batch
            for tick in batch:
                await self.publish_tick(tick)

            # Small delay between batches to avoid overwhelming NATS
            if i + batch_size < len(ticks):
                await asyncio.sleep(0.01)  # 10ms delay

    async def close(self):
        """Close NATS connection"""
        logger.info("Closing NATS connection...")

        if self.nc:
            await self.nc.close()
            logger.info("✅ NATS connection closed")

    def get_stats(self) -> dict:
        """Get publisher statistics"""
        return {
            'publish_count': self.publish_count,
            'error_count': self.error_count,
            'nats_connected': self.nc is not None and self.nc.is_connected,
            'success_rate': (
                self.publish_count / (self.publish_count + self.error_count)
                if (self.publish_count + self.error_count) > 0
                else 1.0
            )
        }
