#!/usr/bin/env python3
"""
ClickHouse Consumer - NATS+Kafka Complementary Pattern
Implements dual-subscribe pattern for zero data loss
"""
import asyncio
import logging
import signal
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from clickhouse_client import ClickHouseClient
from deduplicator import Deduplicator
from nats_subscriber import NATSSubscriber
from kafka_subscriber import KafkaSubscriber

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class ClickHouseConsumer:
    """
    Main orchestrator for ClickHouse Consumer

    Implements NATS+Kafka Complementary Pattern:
    1. Subscribe to BOTH NATS (fast) and Kafka (reliable)
    2. Deduplicate messages (same message from both sources)
    3. Batch insert to ClickHouse for performance

    Result: ZERO data loss, high performance
    """

    def __init__(self):
        self.config = Config()

        self.clickhouse_client = None
        self.deduplicator = None
        self.nats_subscriber = None
        self.kafka_subscriber = None

        self.start_time = datetime.utcnow()
        self.is_running = False

        logger.info("=" * 80)
        logger.info("CLICKHOUSE CONSUMER - NATS+KAFKA COMPLEMENTARY PATTERN")
        logger.info("=" * 80)
        logger.info(f"Instance ID: {self.config.instance_id}")
        logger.info(f"Log Level: {self.config.log_level}")

    async def start(self):
        """Start the consumer"""
        try:
            logger.info("🚀 Starting ClickHouse Consumer...")

            # Initialize ClickHouse client
            self.clickhouse_client = ClickHouseClient(
                config=self.config.clickhouse_config,
                batch_config=self.config.batch_config
            )
            await self.clickhouse_client.connect()

            # Initialize deduplicator
            self.deduplicator = Deduplicator(self.config.dedup_config)

            # Message handler (called by both NATS and Kafka)
            async def handle_message(data: dict, data_type: str):
                """
                Central message handler

                Args:
                    data: Message data
                    data_type: "tick" or "aggregate"
                """
                source = data.get('_source', 'unknown')

                # Generate message ID for deduplication
                message_id = self.deduplicator.generate_message_id(data)

                # Check for duplicates
                if self.deduplicator.is_duplicate(message_id, source):
                    # Skip duplicate (already processed from other source)
                    logger.debug(f"Skipped duplicate {data_type} from {source}: {message_id}")
                    return

                # Process message based on type
                if data_type == 'tick':
                    await self.clickhouse_client.add_tick(data)
                elif data_type == 'aggregate':
                    await self.clickhouse_client.add_aggregate(data)
                else:
                    logger.warning(f"Unknown data type: {data_type}")

                # Mark as processed
                self.deduplicator.mark_processed(data, source)

            # Initialize NATS subscriber (PRIMARY path)
            self.nats_subscriber = NATSSubscriber(
                config=self.config.nats_config,
                message_handler=handle_message
            )
            await self.nats_subscriber.connect()
            await self.nats_subscriber.subscribe_all()

            # Initialize Kafka subscriber (BACKUP path)
            self.kafka_subscriber = KafkaSubscriber(
                config=self.config.kafka_config,
                message_handler=handle_message
            )
            await self.kafka_subscriber.connect()

            self.is_running = True

            logger.info("=" * 80)
            logger.info("✅ ClickHouse Consumer STARTED")
            logger.info("📊 NATS: Real-time data path (PRIMARY)")
            logger.info("📊 Kafka: Backup + gap-filling (COMPLEMENTARY)")
            logger.info("🔍 Deduplication: ENABLED")
            logger.info("=" * 80)

            # Run Kafka poller and status reporter concurrently
            await asyncio.gather(
                self.kafka_subscriber.poll_messages(),
                self._periodic_flush(),
                self._status_reporter()
            )

        except Exception as e:
            logger.error(f"❌ Error starting consumer: {e}", exc_info=True)
            await self.stop()

    async def _periodic_flush(self):
        """Periodically flush buffers"""
        while self.is_running:
            try:
                await asyncio.sleep(1)  # Check every second

                # Flush if time-based trigger
                await self.clickhouse_client.flush_all()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic flush: {e}")

    async def _status_reporter(self):
        """Report status periodically"""
        interval = self.config.monitoring_config.get('report_interval_seconds', 60)

        while self.is_running:
            try:
                await asyncio.sleep(interval)

                # Collect statistics
                uptime = datetime.utcnow() - self.start_time

                nats_stats = self.nats_subscriber.get_stats() if self.nats_subscriber else {}
                kafka_stats = self.kafka_subscriber.get_stats() if self.kafka_subscriber else {}
                dedup_stats = self.deduplicator.get_stats() if self.deduplicator else {}
                ch_stats = self.clickhouse_client.get_stats() if self.clickhouse_client else {}

                # Log status
                logger.info("=" * 80)
                logger.info(f"📊 STATUS REPORT - Uptime: {uptime}")
                logger.info(f"NATS Messages: {nats_stats.get('total_messages', 0)} | "
                           f"Ticks: {nats_stats.get('tick_messages', 0)} | "
                           f"Aggregates: {nats_stats.get('aggregate_messages', 0)}")
                logger.info(f"Kafka Messages: {kafka_stats.get('total_messages', 0)} | "
                           f"Ticks: {kafka_stats.get('tick_messages', 0)} | "
                           f"Aggregates: {kafka_stats.get('aggregate_messages', 0)}")
                logger.info(f"Deduplication: {dedup_stats.get('total_duplicates', 0)} duplicates | "
                           f"Rate: {dedup_stats.get('duplicate_rate', 0):.2%} | "
                           f"Cache size: {dedup_stats.get('cache_size', 0)}")
                logger.info(f"ClickHouse: {ch_stats.get('total_ticks_inserted', 0)} ticks | "
                           f"{ch_stats.get('total_aggregates_inserted', 0)} aggregates | "
                           f"{ch_stats.get('total_batch_inserts', 0)} batches")
                logger.info(f"Buffers: Ticks {ch_stats.get('tick_buffer_size', 0)} | "
                           f"Aggregates {ch_stats.get('aggregate_buffer_size', 0)}")
                logger.info("=" * 80)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in status reporter: {e}")

    async def stop(self):
        """Stop the consumer"""
        logger.info("🛑 Stopping ClickHouse Consumer...")
        self.is_running = False

        # Stop subscribers
        if self.nats_subscriber:
            await self.nats_subscriber.close()

        if self.kafka_subscriber:
            await self.kafka_subscriber.close()

        # Flush remaining data
        if self.clickhouse_client:
            await self.clickhouse_client.flush_all()
            await self.clickhouse_client.close()

        logger.info("✅ Consumer stopped")

    def handle_signal(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}. Shutting down...")
        asyncio.create_task(self.stop())

async def main():
    """Main entry point"""
    consumer = ClickHouseConsumer()

    # Register signal handlers
    signal.signal(signal.SIGINT, consumer.handle_signal)
    signal.signal(signal.SIGTERM, consumer.handle_signal)

    try:
        await consumer.start()

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        await consumer.stop()

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        await consumer.stop()
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())
