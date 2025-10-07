"""
Kafka Subscriber - Backup data path + gap-filling
"""
import asyncio
import logging
import orjson
from typing import Callable
from kafka import KafkaConsumer

logger = logging.getLogger(__name__)

class KafkaSubscriber:
    """
    Kafka subscriber for persistent backup and gap-filling

    Subscription Pattern:
    - tick_archive (backup for all tick data)
    - aggregate_archive (backup for all aggregate data)
    - confirmation_archive (backup for confirmation pairs)

    This is the BACKUP data path:
    - Fills gaps when NATS fails
    - Ensures ZERO data loss
    - Starts from 'latest' to avoid duplicates on startup
    """

    def __init__(self, config: dict, message_handler: Callable):
        self.config = config
        self.message_handler = message_handler

        self.consumer = None
        self.is_running = False

        # Statistics
        self.total_messages = 0
        self.tick_messages = 0
        self.aggregate_messages = 0
        self.confirmation_messages = 0

        logger.info("Kafka subscriber initialized")

    async def connect(self):
        """Connect to Kafka brokers"""
        try:
            topics_config = self.config.get('topics', {})
            topics = [
                topics_config.get('tick_archive', 'tick_archive'),
                topics_config.get('aggregate_archive', 'aggregate_archive'),
                topics_config.get('confirmation_archive', 'confirmation_archive')
            ]

            # Add external data topics
            external_topics = [
                'market.external.economic_calendar',
                'market.external.fred_economic',
                'market.external.crypto_sentiment',
                'market.external.fear_greed_index',
                'market.external.commodity_prices',
                'market.external.market_sessions'
            ]
            topics.extend(external_topics)

            self.consumer = KafkaConsumer(
                *topics,
                bootstrap_servers=self.config.get('brokers', ['localhost:9092']),
                group_id=self.config.get('group_id', 'data-bridge'),
                auto_offset_reset=self.config.get('auto_offset_reset', 'latest'),
                enable_auto_commit=self.config.get('enable_auto_commit', True),
                auto_commit_interval_ms=self.config.get('auto_commit_interval_ms', 5000),
                fetch_min_bytes=self.config.get('fetch_min_bytes', 1024),
                fetch_max_wait_ms=self.config.get('fetch_max_wait_ms', 500),
                max_poll_records=self.config.get('max_poll_records', 500),
                value_deserializer=lambda m: orjson.loads(m.decode('utf-8'))
            )

            logger.info(f"✅ Connected to Kafka: {self.config.get('brokers')}")
            logger.info(f"📊 Subscribed to topics: {topics}")

            self.is_running = True

        except Exception as e:
            logger.error(f"❌ Kafka connection failed: {e}")
            raise

    async def poll_messages(self):
        """Poll messages from Kafka"""
        logger.info("🔄 Starting Kafka polling loop...")

        while self.is_running:
            try:
                # Poll messages (non-blocking with timeout)
                # Run in executor to avoid blocking event loop
                loop = asyncio.get_event_loop()
                messages = await loop.run_in_executor(
                    None,
                    lambda: self.consumer.poll(timeout_ms=1000, max_records=500)
                )

                # Process messages
                for topic_partition, records in messages.items():
                    for record in records:
                        await self._handle_message(record)

            except Exception as e:
                logger.error(f"Error polling Kafka: {e}")
                await asyncio.sleep(1)

        logger.info("Kafka polling loop stopped")

    async def _handle_message(self, record):
        """Handle Kafka message"""
        try:
            data = record.value

            # Add source metadata
            data['_source'] = 'kafka'
            data['_topic'] = record.topic

            # Determine data type from topic
            if 'market.external' in record.topic:
                data_type = 'external'

                # Extract external type from topic name
                # Topic format: market.external.{data_type}
                # Examples: market.external.fear_greed_index, market.external.crypto_sentiment
                topic_parts = record.topic.split('.')
                if len(topic_parts) >= 3:
                    external_type = topic_parts[2]  # fear_greed_index, crypto_sentiment, etc.
                    data['_external_type'] = external_type
                else:
                    logger.warning(f"⚠️ Cannot extract external type from topic: {record.topic}")
                    data['_external_type'] = 'unknown'

            elif 'aggregate' in record.topic:
                data_type = 'aggregate'
                self.aggregate_messages += 1
            elif 'confirmation' in record.topic:
                data_type = 'tick'
                self.confirmation_messages += 1
            else:
                data_type = 'tick'
                self.tick_messages += 1

            # Send to message handler
            await self.message_handler(data, data_type=data_type)

            # Update statistics
            self.total_messages += 1

            if self.total_messages % 1000 == 0:
                logger.info(f"📈 Kafka received {self.total_messages} messages")

        except Exception as e:
            logger.error(f"Error handling Kafka message: {e}")
            logger.debug(f"Record: {record}")

    async def close(self):
        """Close Kafka consumer"""
        logger.info("Closing Kafka consumer...")
        self.is_running = False

        if self.consumer:
            self.consumer.close()
            logger.info("✅ Kafka consumer closed")

    def get_stats(self) -> dict:
        """Get subscriber statistics"""
        return {
            'is_running': self.is_running,
            'total_messages': self.total_messages,
            'tick_messages': self.tick_messages,
            'aggregate_messages': self.aggregate_messages,
            'confirmation_messages': self.confirmation_messages
        }
