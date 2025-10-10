"""
NATS Publisher for Polygon.io tick data
"""
import asyncio
import json
import logging
from typing import Optional
from nats.aio.client import Client as NATS
from kafka import KafkaProducer

logger = logging.getLogger(__name__)

class NATSPublisher:
    def __init__(self, nats_config: dict, kafka_config: dict = None):
        self.nats_config = nats_config
        self.kafka_config = kafka_config

        self.nc: Optional[NATS] = None
        self.kafka: Optional[KafkaProducer] = None

        self.nats_publish_count = 0
        self.kafka_publish_count = 0
        self._kafka_unavailable_logged = False  # Flag to log warning only once

    async def connect(self):
        """
        Connect to NATS and Kafka (Hybrid Architecture)

        NATS: Real-time streaming (low latency)
        Kafka: Persistent archive (replay capability)
        """
        # Connect to NATS (REQUIRED - Real-time streaming)
        try:
            self.nc = NATS()
            await self.nc.connect(
                servers=[self.nats_config.get('url', 'nats://suho-nats-server:4222')],
                max_reconnect_attempts=self.nats_config.get('max_reconnect', 10),
                reconnect_time_wait=self.nats_config.get('reconnect_delay', 2),
                ping_interval=self.nats_config.get('ping_interval', 120)
            )
            logger.info(f"✅ NATS Connected (Real-time streaming) - {self.nats_config.get('url')}")

        except Exception as e:
            logger.error(f"❌ NATS connection FAILED: {e}")
            raise

        # Connect to Kafka (REQUIRED - Persistent archive) with retry logic
        if self.kafka_config and self.kafka_config.get('enabled', True):
            max_retries = 5
            retry_delay = 2  # seconds

            for attempt in range(1, max_retries + 1):
                try:
                    logger.info(f"🔄 Attempting Kafka connection (attempt {attempt}/{max_retries})...")
                    self.kafka = KafkaProducer(
                        bootstrap_servers=self.kafka_config.get('brokers', ['suho-kafka:9092']),
                        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                        compression_type=self.kafka_config.get('compression', 'lz4'),
                        linger_ms=self.kafka_config.get('linger_ms', 10),
                        api_version_auto_timeout_ms=10000,  # Increase timeout for slow starts
                        request_timeout_ms=30000,
                        max_block_ms=10000
                    )
                    logger.info(f"✅ Kafka Connected (Persistent archive) - {self.kafka_config.get('brokers')}")
                    break

                except Exception as e:
                    logger.warning(f"⚠️ Kafka connection attempt {attempt}/{max_retries} failed: {e}")
                    if attempt < max_retries:
                        logger.info(f"⏳ Retrying in {retry_delay} seconds...")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        logger.error(f"❌ Kafka connection FAILED after {max_retries} attempts")
                        logger.warning("⚠️ Running without Kafka - no persistent archive!")
                        self.kafka = None

    async def publish(self, tick_data: dict, is_confirmation: bool = False):
        """
        HYBRID PUBLISH: Complementary NATS+Kafka Pattern

        Pattern Explanation:
        - Publisher: Dual-write to NATS (real-time) AND Kafka (durability backup)
        - Consumer: Subscribes to BOTH NATS and Kafka
        - If NATS fails: Kafka "melengkapi" (complements) with the missed message
        - Success: If NATS succeeds (even if Kafka fails temporarily)

        This ensures:
        1. Real-time delivery via NATS (<1ms latency)
        2. No data loss via Kafka backup (durable storage)
        3. Consumer receives from both, deduplicates if needed
        4. Kafka fills gaps when NATS misses messages

        Args:
            tick_data: Tick data dictionary
            is_confirmation: True for confirmation pairs, False for real-time trading
        """
        # Determine subject/topic
        symbol = tick_data.get('symbol', '').replace('/', '')  # EUR/USD → EURUSD

        if is_confirmation:
            subject_pattern = self.nats_config.get('subjects', {}).get('confirmation', 'confirmation.{symbol}')
            kafka_topic = self.kafka_config.get('topics', {}).get('confirmation_archive', 'confirmation_archive')
        else:
            subject_pattern = self.nats_config.get('subjects', {}).get('realtime_quotes', 'ticks.{symbol}')
            kafka_topic = self.kafka_config.get('topics', {}).get('tick_archive', 'tick_archive')

        subject = subject_pattern.format(symbol=symbol)
        message = json.dumps(tick_data).encode('utf-8')

        # DUAL-WRITE: Execute both independently (like Promise.allSettled)
        nats_result = None
        kafka_result = None

        # 1. NATS publish (PRIMARY for real-time)
        try:
            await self.nc.publish(subject, message)
            self.nats_publish_count += 1
            nats_result = "success"
        except Exception as e:
            nats_result = f"failed: {e}"
            logger.error(f"❌ NATS publish failed: {e}")

        # 2. Kafka publish (BACKUP for durability - runs independently)
        if self.kafka:
            try:
                self.kafka.send(kafka_topic, value=tick_data)
                self.kafka_publish_count += 1
                kafka_result = "success"
            except Exception as e:
                kafka_result = f"failed: {e}"
                logger.error(f"❌ Kafka publish failed: {e}")
        else:
            kafka_result = "not_connected"
            # Log warning only ONCE per session
            if not self._kafka_unavailable_logged:
                logger.warning(f"⚠️ Kafka unavailable - running without backup storage (this will only be logged once)")
                self._kafka_unavailable_logged = True

        # COMPLEMENTARY PATTERN: Success if NATS succeeded (Kafka is backup)
        # If NATS failed but Kafka succeeded, consumers will still get message from Kafka
        if nats_result == "success":
            # Log dual-write status
            if self.nats_publish_count % 10000 == 0:
                status = "✅ Both" if kafka_result == "success" else "⚠️ NATS only"
                logger.info(f"📤 {status} | NATS: {self.nats_publish_count} | Kafka: {self.kafka_publish_count}")
        else:
            # NATS failed - rely on Kafka backup
            if kafka_result == "success":
                logger.warning(f"⚠️ NATS failed but Kafka succeeded - consumers will receive from Kafka backup")
            else:
                logger.error(f"❌ BOTH NATS and Kafka failed - message LOST! {tick_data.get('symbol')}")

    async def publish_aggregate(self, aggregate_data: dict):
        """
        Publish OHLCV aggregate data (like MT5 bars with tick volume)

        Pattern: Same complementary NATS+Kafka dual-write

        Args:
            aggregate_data: OHLCV bar data with tick volume
        """
        # Determine subject/topic
        symbol = aggregate_data.get('symbol', '').replace('/', '')  # EUR/USD → EURUSD
        timeframe = aggregate_data.get('timeframe', '1s')

        # Subject pattern: bars.EURUSD.1s
        subject_pattern = self.nats_config.get('subjects', {}).get('aggregates', 'bars.{symbol}.{timeframe}')
        subject = subject_pattern.format(symbol=symbol, timeframe=timeframe)

        # Kafka topic for aggregate archive
        kafka_topic = self.kafka_config.get('topics', {}).get('aggregate_archive', 'aggregate_archive')

        message = json.dumps(aggregate_data).encode('utf-8')

        # DUAL-WRITE: Execute both independently
        nats_result = None
        kafka_result = None

        # 1. NATS publish (PRIMARY for real-time)
        try:
            await self.nc.publish(subject, message)
            self.nats_publish_count += 1
            nats_result = "success"
        except Exception as e:
            nats_result = f"failed: {e}"
            logger.error(f"❌ NATS aggregate publish failed: {e}")

        # 2. Kafka publish (BACKUP for durability)
        if self.kafka:
            try:
                self.kafka.send(kafka_topic, value=aggregate_data)
                self.kafka_publish_count += 1
                kafka_result = "success"
            except Exception as e:
                kafka_result = f"failed: {e}"
                logger.error(f"❌ Kafka aggregate publish failed: {e}")
        else:
            kafka_result = "not_connected"
            # Use same flag - already logged once in publish()
            if not self._kafka_unavailable_logged:
                logger.warning(f"⚠️ Kafka unavailable - running without backup storage (this will only be logged once)")
                self._kafka_unavailable_logged = True

        # Log status
        if nats_result == "success":
            if self.nats_publish_count % 10000 == 0:
                status = "✅ Both" if kafka_result == "success" else "⚠️ NATS only"
                logger.info(f"📊 {status} | Aggregates NATS: {self.nats_publish_count} | Kafka: {self.kafka_publish_count}")
        else:
            if kafka_result == "success":
                logger.warning(f"⚠️ NATS failed but Kafka succeeded - consumers will receive from Kafka backup")
            else:
                logger.error(f"❌ BOTH NATS and Kafka failed - aggregate LOST! {symbol}")

    async def publish_status(self, status_data: dict):
        """Publish collector status"""
        try:
            subject = self.nats_config.get('subjects', {}).get('status', 'collector.status')
            message = json.dumps(status_data).encode('utf-8')
            await self.nc.publish(subject, message)

        except Exception as e:
            logger.error(f"Error publishing status: {e}")

    async def publish_error(self, error_data: dict):
        """Publish error message"""
        try:
            subject = self.nats_config.get('subjects', {}).get('errors', 'collector.errors')
            message = json.dumps(error_data).encode('utf-8')
            await self.nc.publish(subject, message)

        except Exception as e:
            logger.error(f"Error publishing error message: {e}")

    async def close(self):
        """Close connections"""
        logger.info("Closing NATS/Kafka connections...")

        if self.nc:
            await self.nc.close()
            logger.info("✅ NATS connection closed")

        if self.kafka:
            self.kafka.close()
            logger.info("✅ Kafka connection closed")

    def get_stats(self) -> dict:
        """Get publisher statistics"""
        return {
            'nats_publish_count': self.nats_publish_count,
            'kafka_publish_count': self.kafka_publish_count,
            'nats_connected': self.nc is not None and self.nc.is_connected,
            'kafka_connected': self.kafka is not None
        }
