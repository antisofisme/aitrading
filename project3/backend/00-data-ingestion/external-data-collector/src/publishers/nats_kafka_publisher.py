"""
Generic NATS+Kafka Publisher for External Data
Supports multiple data types with flexible topic routing
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from nats.aio.client import Client as NATS
from kafka import KafkaProducer
from enum import Enum

logger = logging.getLogger(__name__)


class DataType(Enum):
    """Supported external data types"""
    ECONOMIC_CALENDAR = "economic_calendar"
    NEWS = "news"
    SENTIMENT = "sentiment"
    COT_REPORT = "cot_report"
    MARKET_CONTEXT = "market_context"
    ALTERNATIVE_DATA = "alternative_data"

    # Active data types (implemented)
    FRED_ECONOMIC = "fred_economic"              # FRED economic indicators
    CRYPTO_SENTIMENT = "crypto_sentiment"        # CoinGecko crypto sentiment
    FEAR_GREED_INDEX = "fear_greed_index"        # Crypto fear & greed index
    COMMODITY_PRICES = "commodity_prices"        # Yahoo Finance commodities
    MARKET_SESSIONS = "market_sessions"          # Forex market sessions

    # Future data types
    CENTRAL_BANK = "central_bank"
    SOCIAL_MEDIA = "social_media"
    SEARCH_TRENDS = "search_trends"
    CRYPTO_DATA = "crypto_data"


class ExternalDataPublisher:
    """
    Generic publisher for external market data

    Architecture:
    External Data → Publisher → NATS (real-time) + Kafka (persistence)

    Features:
    - Multi data-type support
    - Flexible topic routing
    - Batch publishing
    - Error handling + retry
    """

    def __init__(self, nats_config: Dict[str, Any], kafka_config: Dict[str, Any]):
        self.nats_config = nats_config
        self.kafka_config = kafka_config

        self.nats: Optional[NATS] = None
        self.kafka: Optional[KafkaProducer] = None

        # Statistics
        self.nats_publish_count = 0
        self.kafka_publish_count = 0
        self.total_published = 0
        self.errors = 0

        logger.info("ExternalDataPublisher initialized")

    async def connect(self):
        """Connect to NATS and Kafka"""
        # Connect to NATS (real-time, primary)
        if self.nats_config.get('enabled', False):
            try:
                self.nats = NATS()
                await self.nats.connect(
                    servers=[f"nats://{self.nats_config['host']}:{self.nats_config['port']}"],
                    max_reconnect_attempts=-1,
                    reconnect_time_wait=2,
                    ping_interval=120
                )
                logger.info(f"✅ Connected to NATS: {self.nats_config['host']}:{self.nats_config['port']}")

            except Exception as e:
                logger.error(f"❌ NATS connection failed: {e}")
                logger.warning("⚠️  Continuing without NATS...")

        # Connect to Kafka (persistence, backup)
        if self.kafka_config.get('enabled', False):
            try:
                self.kafka = KafkaProducer(
                    bootstrap_servers=self.kafka_config['bootstrap_servers'],
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    compression_type='lz4'
                )
                logger.info(f"✅ Connected to Kafka: {self.kafka_config['bootstrap_servers']}")

            except Exception as e:
                logger.error(f"❌ Kafka connection failed: {e}")
                logger.warning("⚠️  Continuing without Kafka...")

        if not self.nats and not self.kafka:
            logger.error("❌ Both NATS and Kafka failed - no message queue available!")
            raise RuntimeError("Failed to connect to any message queue")

    async def publish(
        self,
        data: Dict[str, Any],
        data_type: DataType,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Publish external data to NATS+Kafka

        Args:
            data: Data to publish (will be JSON serialized)
            data_type: Type of data (determines topic routing)
            metadata: Optional metadata (source, timestamp, etc.)
        """
        try:
            # Build message
            message = self._build_message(data, data_type, metadata)

            # Get topic/subject
            nats_subject = self._get_nats_subject(data_type)
            kafka_topic = self._get_kafka_topic(data_type)

            message_json = json.dumps(message).encode('utf-8')

            # Publish to NATS (primary, real-time)
            nats_success = False
            if self.nats:
                try:
                    await self.nats.publish(nats_subject, message_json)
                    await self.nats.flush()  # Force flush to ensure delivery
                    self.nats_publish_count += 1
                    nats_success = True
                except Exception as e:
                    logger.error(f"❌ NATS publish failed: {e}")

            # Publish to Kafka (backup, persistence)
            kafka_success = False
            if self.kafka:
                try:
                    self.kafka.send(kafka_topic, value=message)
                    self.kafka_publish_count += 1
                    kafka_success = True
                except Exception as e:
                    logger.error(f"❌ Kafka publish failed: {e}")

            # Check success
            if nats_success or kafka_success:
                self.total_published += 1
                status = "✅" if nats_success else "⚠️"

                if self.total_published % 100 == 0:
                    logger.info(f"{status} Published {self.total_published} messages | "
                               f"NATS: {self.nats_publish_count} | Kafka: {self.kafka_publish_count}")
            else:
                self.errors += 1
                logger.error(f"❌ BOTH NATS and Kafka failed - data LOST! Type: {data_type.value}")

        except Exception as e:
            self.errors += 1
            logger.error(f"❌ Error publishing {data_type.value}: {e}")

    async def publish_batch(
        self,
        data_list: List[Dict[str, Any]],
        data_type: DataType,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Publish batch of data

        Args:
            data_list: List of data to publish
            data_type: Type of data
            metadata: Optional metadata
        """
        logger.info(f"📤 Publishing batch of {len(data_list)} {data_type.value} items...")

        for data in data_list:
            await self.publish(data, data_type, metadata)

        logger.info(f"✅ Batch publish complete: {len(data_list)} items")

    def _build_message(
        self,
        data: Dict[str, Any],
        data_type: DataType,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build message with metadata

        Message format:
        {
            "data": {...},
            "metadata": {
                "type": "economic_calendar",
                "source": "mql5",
                "timestamp": "2025-10-06T12:00:00Z",
                "version": "1.0.0",
                ...
            }
        }
        """
        message = {
            "data": data,
            "metadata": {
                "type": data_type.value,
                "timestamp": datetime.utcnow().isoformat() + 'Z',
                "version": "1.0.0",
                **(metadata or {})
            }
        }
        return message

    def _get_nats_subject(self, data_type: DataType) -> str:
        """
        Get NATS subject for data type

        Subject pattern: market.external.{data_type}
        Examples:
        - market.external.economic_calendar
        - market.external.news
        - market.external.sentiment
        """
        base = self.nats_config.get('topics', {}).get('base', 'market.external')
        return f"{base}.{data_type.value}"

    def _get_kafka_topic(self, data_type: DataType) -> str:
        """
        Get Kafka topic for data type

        Topic pattern: market.external.{data_type}
        """
        # Check if specific topic configured
        topics = self.kafka_config.get('topics', {})
        if data_type.value in topics:
            return topics[data_type.value]

        # Default pattern
        return f"market.external.{data_type.value}"

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
            'total_published': self.total_published,
            'nats_publish_count': self.nats_publish_count,
            'kafka_publish_count': self.kafka_publish_count,
            'errors': self.errors
        }
