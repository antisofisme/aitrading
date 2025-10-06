"""
NATS/Kafka Publisher for Aggregated Data
Publishes OHLCV candles to message queue
"""
import asyncio
import json
import logging
from typing import Dict, Any
from nats.aio.client import Client as NATS
from kafka import KafkaProducer

logger = logging.getLogger(__name__)

class AggregatePublisher:
    """
    Publishes aggregated OHLCV data to NATS and Kafka

    Flow:
    Aggregator → NATS/Kafka → Data Bridge → ClickHouse
    """

    def __init__(self, nats_config: Dict[str, Any], kafka_config: Dict[str, Any]):
        self.nats_config = nats_config
        self.kafka_config = kafka_config

        self.nats: NATS = None
        self.kafka: KafkaProducer = None

        self.nats_publish_count = 0
        self.kafka_publish_count = 0

        logger.info("Aggregate Publisher initialized")

    async def connect(self):
        """Connect to NATS and Kafka"""
        # Connect to NATS
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

        # Connect to Kafka
        try:
            self.kafka = KafkaProducer(
                bootstrap_servers=self.kafka_config['brokers'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                compression_type=self.kafka_config.get('compression_type', 'lz4')
            )
            logger.info(f"✅ Connected to Kafka: {self.kafka_config['brokers']}")

        except Exception as e:
            logger.error(f"❌ Kafka connection failed: {e}")
            # Continue without Kafka (NATS is primary)

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

        # Kafka topic
        kafka_topic = self.kafka_config.get('topics', {}).get('aggregate_archive', 'aggregate_archive')

        # Add metadata
        aggregate_data['_source'] = 'live_aggregated'
        aggregate_data['_subject'] = subject

        message = json.dumps(aggregate_data).encode('utf-8')

        # Publish to NATS (primary)
        nats_success = False
        try:
            await self.nats.publish(subject, message)
            self.nats_publish_count += 1
            nats_success = True

            if self.nats_publish_count % 50 == 0:
                logger.debug(f"📤 Published {self.nats_publish_count} aggregates to NATS")

        except Exception as e:
            logger.error(f"❌ NATS publish failed: {e}")

        # Publish to Kafka (backup)
        kafka_success = False
        if self.kafka:
            try:
                self.kafka.send(kafka_topic, value=aggregate_data)
                self.kafka_publish_count += 1
                kafka_success = True

            except Exception as e:
                logger.error(f"❌ Kafka publish failed: {e}")

        # Log status
        if nats_success or kafka_success:
            status = "✅" if nats_success else "⚠️"
            if self.nats_publish_count % 50 == 0:
                logger.info(f"{status} {symbol} {timeframe} | NATS: {self.nats_publish_count} | Kafka: {self.kafka_publish_count}")
        else:
            logger.error(f"❌ BOTH NATS and Kafka failed - aggregate LOST! {symbol} {timeframe}")

    async def close(self):
        """Close connections"""
        if self.nats:
            await self.nats.close()
            logger.info("✅ NATS connection closed")

        if self.kafka:
            self.kafka.close()
            logger.info("✅ Kafka connection closed")

    def get_stats(self) -> Dict[str, int]:
        """Get publisher statistics"""
        return {
            'nats_publish_count': self.nats_publish_count,
            'kafka_publish_count': self.kafka_publish_count
        }
