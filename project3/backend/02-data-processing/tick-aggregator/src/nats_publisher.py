"""
NATS Publisher for Aggregated Data
Publishes OHLCV candles to NATS (Hybrid Architecture: NATS for market data)
"""
import asyncio
import json
import logging
from typing import Dict, Any
from nats.aio.client import Client as NATS

logger = logging.getLogger(__name__)

class AggregatePublisher:
    """
    Publishes aggregated OHLCV data to NATS ONLY

    Hybrid Architecture:
    - NATS: Market data (ticks, aggregates) ← THIS SERVICE
    - Kafka: User events only

    Flow:
    Aggregator → NATS → Data Bridge → ClickHouse
    """

    def __init__(self, nats_config: Dict[str, Any], kafka_config: Dict[str, Any] = None):
        self.nats_config = nats_config
        self.nats: NATS = None
        self.nats_publish_count = 0

        logger.info("Aggregate Publisher initialized (NATS-only)")

    async def connect(self):
        """Connect to NATS"""
        try:
            self.nats = NATS()
            await self.nats.connect(
                servers=[self.nats_config['url']],
                max_reconnect_attempts=self.nats_config.get('max_reconnect_attempts', -1),
                reconnect_time_wait=self.nats_config.get('reconnect_time_wait', 2),
                ping_interval=self.nats_config.get('ping_interval', 120)
            )
            logger.info(f"✅ Connected to NATS: {self.nats_config['url']}")

        except Exception as e:
            logger.error(f"❌ NATS connection failed: {e}")
            raise

    async def publish_aggregate(self, aggregate_data: Dict[str, Any]):
        """
        Publish aggregated OHLCV data

        Args:
            aggregate_data: OHLCV candle data
                {
                    'symbol': 'EUR/USD',
                    'timeframe': '5m',
                    'timestamp_ms': 1706198400000,
                    'open': 1.0850,
                    'high': 1.0855,
                    'low': 1.0848,
                    'close': 1.0852,
                    'volume': 1234,
                    'vwap': 1.0851,
                    'range_pips': 0.70,
                    'body_pips': 0.20,
                    'start_time': '2024-01-25T10:00:00+00:00',
                    'end_time': '2024-01-25T10:05:00+00:00',
                    'source': 'live_aggregated',
                    'event_type': 'ohlcv'
                }
        """
        symbol = aggregate_data.get('symbol', '').replace('/', '')  # EUR/USD → EURUSD
        timeframe = aggregate_data.get('timeframe', '5m')

        # NATS subject pattern: bars.EURUSD.5m
        subject_pattern = self.nats_config.get('subjects', {}).get('aggregates', 'bars.{symbol}.{timeframe}')
        subject = subject_pattern.format(symbol=symbol, timeframe=timeframe)

        # Add metadata
        aggregate_data['_source'] = 'live_aggregated'
        aggregate_data['_subject'] = subject

        message = json.dumps(aggregate_data).encode('utf-8')

        # Publish to NATS
        try:
            await self.nats.publish(subject, message)
            self.nats_publish_count += 1

            if self.nats_publish_count % 50 == 0:
                logger.info(f"✅ {symbol} {timeframe} | NATS: {self.nats_publish_count}")

        except Exception as e:
            logger.error(f"❌ NATS publish failed: {e}")
            raise

    async def close(self):
        """Close NATS connection"""
        if self.nats:
            await self.nats.close()
            logger.info("✅ NATS connection closed")

    def get_stats(self) -> Dict[str, int]:
        """Get publisher statistics"""
        return {
            'nats_publish_count': self.nats_publish_count
        }
