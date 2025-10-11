"""
NATS Publisher for Polygon.io market data
Uses NATS-only for real-time streaming (hybrid architecture)
"""
import asyncio
import json
import logging
from typing import Optional
from nats.aio.client import Client as NATS

logger = logging.getLogger(__name__)

class NATSPublisher:
    def __init__(self, nats_config: dict):
        self.nats_config = nats_config
        self.nc: Optional[NATS] = None
        self.nats_publish_count = 0

    async def connect(self):
        """
        Connect to NATS (Real-time streaming)

        Hybrid Architecture - Phase 1:
        - Market data (live quotes, OHLCV) → NATS (broadcast, <1ms latency)
        - User events (future) → Kafka (isolated, persistent)
        """
        try:
            self.nc = NATS()
            await self.nc.connect(
                servers=[self.nats_config.get('url', 'nats://suho-nats-server:4222')],
                max_reconnect_attempts=self.nats_config.get('max_reconnect', 10),
                reconnect_time_wait=self.nats_config.get('reconnect_delay', 2),
                ping_interval=self.nats_config.get('ping_interval', 120)
            )
            logger.info(f"✅ NATS Connected (Market data streaming) - {self.nats_config.get('url')}")

        except Exception as e:
            logger.error(f"❌ NATS connection FAILED: {e}")
            raise

    async def publish(self, tick_data: dict, is_confirmation: bool = False):
        """
        Publish market tick data to NATS

        Subject Pattern (from nats.json):
        - Real-time ticks: market.{symbol}.tick
        - Confirmation ticks: market.{symbol}.tick (same, identified by source)

        Args:
            tick_data: Tick data dictionary
            is_confirmation: True for confirmation pairs
        """
        # Get symbol (remove "/" if present: EUR/USD → EURUSD)
        symbol = tick_data.get('symbol', '').replace('/', '')

        # Subject: market.{symbol}.tick (from nats.json market_data.patterns.tick)
        subject = f"market.{symbol}.tick"

        # Add metadata
        tick_data['_transport'] = 'nats'
        if is_confirmation:
            tick_data['_pair_type'] = 'confirmation'

        message = json.dumps(tick_data).encode('utf-8')

        try:
            await self.nc.publish(subject, message)
            self.nats_publish_count += 1

            # Log progress
            if self.nats_publish_count % 10000 == 0:
                logger.info(f"📤 NATS published {self.nats_publish_count} ticks")

        except Exception as e:
            logger.error(f"❌ NATS publish failed for {symbol}: {e}")
            raise

    async def publish_aggregate(self, aggregate_data: dict):
        """
        Publish OHLCV aggregate data to NATS

        Subject Pattern (from nats.json):
        - Candles: market.{symbol}.{timeframe}

        Examples:
        - market.EURUSD.5m
        - market.EURUSD.1h
        - market.XAUUSD.15m

        Args:
            aggregate_data: OHLCV bar data
        """
        # Get symbol and timeframe
        symbol = aggregate_data.get('symbol', '').replace('/', '')
        timeframe = aggregate_data.get('timeframe', '1s')

        # Subject: market.{symbol}.{timeframe} (from nats.json market_data.patterns.candle)
        subject = f"market.{symbol}.{timeframe}"

        # Add metadata
        aggregate_data['_transport'] = 'nats'

        message = json.dumps(aggregate_data).encode('utf-8')

        try:
            await self.nc.publish(subject, message)
            self.nats_publish_count += 1

            # Log progress
            if self.nats_publish_count % 10000 == 0:
                logger.info(f"📊 NATS published {self.nats_publish_count} aggregates")

        except Exception as e:
            logger.error(f"❌ NATS aggregate publish failed for {symbol}: {e}")
            raise

    async def publish_status(self, status_data: dict):
        """
        Publish collector status

        Subject: system.health.live-collector
        """
        try:
            subject = "system.health.live-collector"
            message = json.dumps(status_data).encode('utf-8')
            await self.nc.publish(subject, message)

        except Exception as e:
            logger.error(f"Error publishing status: {e}")

    async def publish_error(self, error_data: dict):
        """
        Publish error message

        Subject: system.logs.error
        """
        try:
            subject = "system.logs.error"
            message = json.dumps(error_data).encode('utf-8')
            await self.nc.publish(subject, message)

        except Exception as e:
            logger.error(f"Error publishing error message: {e}")

    async def close(self):
        """Close NATS connection"""
        logger.info("Closing NATS connection...")

        if self.nc:
            await self.nc.close()
            logger.info("✅ NATS connection closed")

    def get_stats(self) -> dict:
        """Get publisher statistics"""
        return {
            'nats_publish_count': self.nats_publish_count,
            'nats_connected': self.nc is not None and self.nc.is_connected
        }
