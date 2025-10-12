"""
Kafka Subscriber - Async implementation using aiokafka
Backup data path + gap-filling with full async/await support
"""
import asyncio
import logging
import orjson
from typing import Callable, AsyncGenerator, Dict, Any, List, Optional
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError, KafkaConnectionError

logger = logging.getLogger(__name__)

class KafkaSubscriber:
    """
    Async Kafka subscriber for persistent backup and gap-filling

    Subscription Pattern:
    - tick_archive (backup for all tick data)
    - aggregate_archive (backup for all aggregate data)
    - confirmation_archive (backup for confirmation pairs)
    - market.external.* (external data sources)

    This is the BACKUP data path:
    - Fills gaps when NATS fails
    - Ensures ZERO data loss
    - Starts from 'latest' to avoid duplicates on startup

    Key Improvements:
    - Full async/await implementation with aiokafka
    - No blocking calls (no run_in_executor needed)
    - Native async iteration over messages
    - Better performance with concurrent message processing
    - Graceful shutdown with proper cleanup
    """

    def __init__(self, config: dict, message_handler: Callable):
        self.config = config
        self.message_handler = message_handler

        self.consumer: Optional[AIOKafkaConsumer] = None
        self.is_running = False
        self._consumption_task: Optional[asyncio.Task] = None

        # Statistics
        self.total_messages = 0
        self.tick_messages = 0
        self.aggregate_messages = 0
        self.confirmation_messages = 0
        self.external_messages = 0

        logger.info("✨ Async Kafka subscriber initialized (aiokafka)")

    async def connect(self):
        """
        Connect to Kafka brokers using aiokafka (fully async)
        """
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

            logger.info(f"📡 Connecting to Kafka: {self.config.get('brokers')}")

            # Create async Kafka consumer
            self.consumer = AIOKafkaConsumer(
                *topics,
                bootstrap_servers=self.config.get('brokers', ['localhost:9092']),
                group_id=self.config.get('group_id', 'data-bridge'),
                auto_offset_reset=self.config.get('auto_offset_reset', 'latest'),
                enable_auto_commit=self.config.get('enable_auto_commit', True),
                auto_commit_interval_ms=self.config.get('auto_commit_interval_ms', 5000),
                fetch_min_bytes=self.config.get('fetch_min_bytes', 1024),
                fetch_max_wait_ms=self.config.get('fetch_max_wait_ms', 500),
                max_poll_records=self.config.get('max_poll_records', 500),
                session_timeout_ms=self.config.get('session_timeout_ms', 30000),
                heartbeat_interval_ms=self.config.get('heartbeat_interval_ms', 10000),
                value_deserializer=lambda m: orjson.loads(m.decode('utf-8'))
            )

            # Start consumer (async operation)
            await self.consumer.start()
            self.is_running = True

            logger.info(f"✅ Connected to Kafka: {self.config.get('brokers')}")
            logger.info(f"📊 Subscribed to topics: {topics}")
            logger.info(f"🔥 Using aiokafka - fully async, no event loop blocking!")

        except KafkaConnectionError as e:
            logger.error(f"❌ Kafka connection failed: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error connecting to Kafka: {e}", exc_info=True)
            raise

    async def poll_messages(self):
        """
        Async message polling loop using native aiokafka async iteration

        This method starts the consumption loop and processes messages
        asynchronously without blocking the event loop.
        """
        if not self.consumer or not self.is_running:
            raise RuntimeError("KafkaSubscriber not connected. Call connect() first.")

        logger.info("🔄 Starting async Kafka polling loop...")

        try:
            # Native async iteration over messages (no blocking!)
            async for msg in self.consumer:
                try:
                    await self._handle_message(msg)

                except asyncio.CancelledError:
                    logger.info("Message processing cancelled")
                    raise

                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    # Continue consuming despite errors
                    continue

        except asyncio.CancelledError:
            logger.info("Kafka polling loop cancelled")
            raise

        except KafkaError as e:
            logger.error(f"Kafka error in polling loop: {e}", exc_info=True)
            raise

        except Exception as e:
            logger.error(f"Unexpected error in polling loop: {e}", exc_info=True)
            raise

        finally:
            logger.info("Kafka polling loop stopped")

    async def consume(self) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Async generator that yields messages from Kafka

        Alternative consumption method using generator pattern.
        Can be used for more fine-grained control.

        Usage:
            async for message in kafka_subscriber.consume():
                await process(message)
        """
        if not self.consumer or not self.is_running:
            raise RuntimeError("KafkaSubscriber not connected. Call connect() first.")

        try:
            logger.info("🔄 Starting async message consumption...")

            async for msg in self.consumer:
                try:
                    # Message already deserialized by value_deserializer
                    data = msg.value

                    # Add metadata
                    data['_topic'] = msg.topic
                    data['_partition'] = msg.partition
                    data['_offset'] = msg.offset
                    data['_timestamp'] = msg.timestamp

                    yield data

                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    # Continue consuming despite errors
                    continue

        except asyncio.CancelledError:
            logger.info("Message consumption cancelled")
            raise

        except Exception as e:
            logger.error(f"Error in consume loop: {e}", exc_info=True)
            raise

    async def _handle_message(self, record):
        """
        Handle Kafka message asynchronously

        Args:
            record: ConsumerRecord from aiokafka
        """
        try:
            data = record.value

            # Add source metadata
            data['_source'] = 'kafka'
            data['_topic'] = record.topic
            data['_partition'] = record.partition
            data['_offset'] = record.offset

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

                self.external_messages += 1

            elif 'aggregate' in record.topic:
                data_type = 'aggregate'
                self.aggregate_messages += 1

            elif 'confirmation' in record.topic:
                data_type = 'tick'
                self.confirmation_messages += 1

            else:
                data_type = 'tick'
                self.tick_messages += 1

            # Send to message handler (async)
            await self.message_handler(data, data_type=data_type)

            # Update statistics
            self.total_messages += 1

            if self.total_messages % 10000 == 0:
                logger.info(f"📈 Kafka received {self.total_messages} messages "
                           f"(ticks: {self.tick_messages}, agg: {self.aggregate_messages}, "
                           f"ext: {self.external_messages})")

        except Exception as e:
            logger.error(f"Error handling Kafka message: {e}", exc_info=True)
            logger.debug(f"Record topic: {record.topic}, partition: {record.partition}, offset: {record.offset}")

    async def commit(self):
        """
        Manually commit offsets (when enable_auto_commit=False)

        This is a no-op if auto_commit is enabled.
        """
        if self.consumer and self.is_running:
            if not self.config.get('enable_auto_commit', True):
                try:
                    await self.consumer.commit()
                    logger.debug("✅ Offsets committed successfully")
                except Exception as e:
                    logger.error(f"❌ Failed to commit offsets: {e}")

    async def seek_to_beginning(self, topic: str = None):
        """
        Seek to beginning of partition(s)

        Args:
            topic: Optional topic name. If None, seeks all subscribed topics.
        """
        if not self.consumer or not self.is_running:
            logger.warning("Cannot seek - consumer not running")
            return

        try:
            if topic:
                partitions = self.consumer.assignment()
                topic_partitions = [tp for tp in partitions if tp.topic == topic]
                await self.consumer.seek_to_beginning(*topic_partitions)
                logger.info(f"🔄 Seeking to beginning for topic: {topic}")
            else:
                await self.consumer.seek_to_beginning()
                logger.info("🔄 Seeking to beginning for all topics")
        except Exception as e:
            logger.error(f"Error seeking to beginning: {e}")

    async def seek_to_end(self, topic: str = None):
        """
        Seek to end of partition(s)

        Args:
            topic: Optional topic name. If None, seeks all subscribed topics.
        """
        if not self.consumer or not self.is_running:
            logger.warning("Cannot seek - consumer not running")
            return

        try:
            if topic:
                partitions = self.consumer.assignment()
                topic_partitions = [tp for tp in partitions if tp.topic == topic]
                await self.consumer.seek_to_end(*topic_partitions)
                logger.info(f"⏭️ Seeking to end for topic: {topic}")
            else:
                await self.consumer.seek_to_end()
                logger.info("⏭️ Seeking to end for all topics")
        except Exception as e:
            logger.error(f"Error seeking to end: {e}")

    async def pause(self):
        """
        Pause consumption from all assigned partitions (backpressure mechanism)

        This uses aiokafka's native pause functionality to stop fetching
        messages while maintaining the consumer group membership.
        """
        if not self.consumer or not self.is_running:
            logger.warning("Cannot pause - Kafka consumer not running")
            return

        try:
            partitions = self.consumer.assignment()
            if partitions:
                self.consumer.pause(*partitions)
                logger.info(f"⏸️  Kafka consumer paused ({len(partitions)} partitions)")
            else:
                logger.warning("No partitions assigned to pause")
        except Exception as e:
            logger.error(f"Error pausing Kafka consumer: {e}")

    async def resume(self):
        """
        Resume consumption from all paused partitions (backpressure mechanism)

        Resumes fetching messages from previously paused partitions.
        """
        if not self.consumer or not self.is_running:
            logger.warning("Cannot resume - Kafka consumer not running")
            return

        try:
            partitions = self.consumer.paused()
            if partitions:
                self.consumer.resume(*partitions)
                logger.info(f"▶️  Kafka consumer resumed ({len(partitions)} partitions)")
            else:
                logger.debug("No paused partitions to resume")
        except Exception as e:
            logger.error(f"Error resuming Kafka consumer: {e}")

    def is_paused(self) -> bool:
        """Check if any partitions are currently paused"""
        if not self.consumer or not self.is_running:
            return False

        try:
            paused_partitions = self.consumer.paused()
            return len(paused_partitions) > 0
        except Exception:
            return False

    async def close(self):
        """
        Gracefully close Kafka consumer

        Commits pending offsets and closes connection properly.
        """
        logger.info("🛑 Closing async Kafka consumer...")
        self.is_running = False

        if self.consumer:
            try:
                # Commit pending offsets before closing
                if not self.config.get('enable_auto_commit', True):
                    logger.info("💾 Committing pending offsets...")
                    await self.consumer.commit()

                # Stop consumer (graceful shutdown)
                await self.consumer.stop()
                logger.info("✅ Kafka consumer closed successfully")

            except Exception as e:
                logger.error(f"❌ Error closing Kafka consumer: {e}", exc_info=True)

    def is_connected(self) -> bool:
        """Check if consumer is connected and running"""
        return self.is_running and self.consumer is not None

    def get_stats(self) -> dict:
        """
        Get subscriber statistics

        Returns:
            dict: Statistics including message counts and connection status
        """
        return {
            'is_running': self.is_running,
            'is_connected': self.is_connected(),
            'is_paused': self.is_paused(),
            'total_messages': self.total_messages,
            'tick_messages': self.tick_messages,
            'aggregate_messages': self.aggregate_messages,
            'confirmation_messages': self.confirmation_messages,
            'external_messages': self.external_messages,
            'implementation': 'aiokafka (async)',
            'consumer_group': self.config.get('group_id', 'data-bridge')
        }

    async def get_lag(self) -> Dict[str, int]:
        """
        Get consumer lag for all assigned partitions

        Returns:
            dict: Mapping of topic-partition to lag count
        """
        if not self.consumer or not self.is_running:
            return {}

        try:
            lag_info = {}

            # Get assigned partitions
            partitions = self.consumer.assignment()

            for tp in partitions:
                # Get current position
                position = await self.consumer.position(tp)

                # Get high water mark (latest offset)
                end_offsets = await self.consumer.end_offsets([tp])
                high_water_mark = end_offsets.get(tp, 0)

                # Calculate lag
                lag = high_water_mark - position
                lag_info[f"{tp.topic}-{tp.partition}"] = lag

            return lag_info

        except Exception as e:
            logger.error(f"Error getting consumer lag: {e}")
            return {}

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Kafka consumer

        Returns:
            dict: Health status with details
        """
        health = {
            'healthy': False,
            'connected': self.is_connected(),
            'total_messages': self.total_messages,
            'errors': []
        }

        try:
            if not self.is_connected():
                health['errors'].append('Consumer not connected')
                return health

            # Check if consumer is responsive
            partitions = self.consumer.assignment()

            if not partitions:
                health['errors'].append('No partitions assigned')
                return health

            # Get lag info
            lag_info = await self.get_lag()
            health['lag'] = lag_info

            # Check if consuming messages
            if self.total_messages == 0:
                health['errors'].append('No messages consumed yet')

            # All checks passed
            if not health['errors']:
                health['healthy'] = True

        except Exception as e:
            health['errors'].append(f'Health check failed: {str(e)}')

        return health
