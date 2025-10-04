"""
Publisher for NATS and Kafka
Publishes historical data to message queues
"""
import logging
import json
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
from nats.aio.client import Client as NATSClient
from aiokafka import AIOKafkaProducer

logger = logging.getLogger(__name__)

class MessagePublisher:
    """Publish historical data to NATS and Kafka"""

    def __init__(self, nats_url: str, kafka_brokers: str):
        self.nats_url = nats_url
        self.kafka_brokers = kafka_brokers.split(',')

        self.nats_client = None
        self.kafka_producer = None

        self.stats = {
            'published_nats': 0,
            'published_kafka': 0,
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
        Publish aggregate bar to NATS and Kafka

        Args:
            aggregate_data: {
                'symbol': 'EUR/USD',
                'timeframe': '1m',
                'timestamp_ms': 1234567890000,
                'open': 1.0850,
                'high': 1.0855,
                'low': 1.0848,
                'close': 1.0852,
                'volume': 15234,
                'vwap': 1.0851,
                'source': 'polygon_historical'
            }
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

            # Publish to NATS
            subject = f"bars.{symbol_clean}.{aggregate_data['timeframe']}"
            await self.nats_client.publish(
                subject,
                json.dumps(message).encode('utf-8')
            )
            self.stats['published_nats'] += 1

            # Publish to Kafka (archive)
            await self.kafka_producer.send(
                'aggregate_archive',
                value=message
            )
            self.stats['published_kafka'] += 1

        except Exception as e:
            logger.error(f"Publish error for {aggregate_data.get('symbol')}: {e}")
            self.stats['errors'] += 1

    async def publish_batch(self, aggregates: List[Dict]):
        """Publish batch of aggregates"""
        tasks = [self.publish_aggregate(agg) for agg in aggregates]
        await asyncio.gather(*tasks, return_exceptions=True)

        if len(aggregates) % 1000 == 0:
            logger.info(f"Published {len(aggregates)} aggregates | "
                       f"NATS: {self.stats['published_nats']} | "
                       f"Kafka: {self.stats['published_kafka']} | "
                       f"Errors: {self.stats['errors']}")

    def get_stats(self) -> Dict:
        """Get publishing statistics"""
        return self.stats.copy()
