#!/usr/bin/env python3
"""
Tick Aggregator Service
Aggregates tick data from TimescaleDB to OHLCV candles
Scheduled execution for multiple timeframes
"""
import asyncio
import logging
import signal
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from aggregator import TickAggregator
from nats_publisher import AggregatePublisher

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class TickAggregatorService:
    """
    Main service for tick aggregation

    Architecture:
    1. Query ticks from TimescaleDB (scheduled)
    2. Aggregate to OHLCV (7 timeframes)
    3. Publish to NATS/Kafka
    4. Data Bridge routes to ClickHouse
    """

    def __init__(self):
        self.config = Config()
        self.aggregator: TickAggregator = None
        self.publisher: AggregatePublisher = None
        self.scheduler: AsyncIOScheduler = None
        self.status_task: Optional[asyncio.Task] = None

        self.start_time = datetime.utcnow()
        self.is_running = False

        # Get symbols to aggregate (from config or default list)
        self.symbols = [
            'EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD',
            'USD/CAD', 'NZD/USD', 'USD/CHF', 'XAU/USD'
        ]

        logger.info("=" * 80)
        logger.info("TICK AGGREGATOR SERVICE")
        logger.info("=" * 80)
        logger.info(f"Instance ID: {self.config.instance_id}")
        logger.info(f"Log Level: {self.config.log_level}")

    async def start(self):
        """Start the aggregator service"""
        try:
            logger.info("🚀 Starting Tick Aggregator Service...")

            # Initialize Central Hub
            await self.config.initialize_central_hub()

            # Initialize aggregator
            logger.info("📊 Initializing Tick Aggregator...")
            self.aggregator = TickAggregator(
                db_config=self.config.database_config,
                aggregation_config=self.config.aggregation_config
            )
            await self.aggregator.connect()

            # Initialize publisher
            logger.info("📤 Initializing NATS/Kafka Publisher...")
            self.publisher = AggregatePublisher(
                nats_config=self.config.nats_config,
                kafka_config=self.config.kafka_config
            )
            await self.publisher.connect()

            # Initialize scheduler
            logger.info("⏰ Setting up aggregation schedules...")
            self.scheduler = AsyncIOScheduler()

            # Schedule each timeframe
            for tf_config in self.config.timeframes:
                self._schedule_timeframe(tf_config)

            # Start scheduler
            self.scheduler.start()
            self.is_running = True

            logger.info("=" * 80)
            logger.info("✅ TICK AGGREGATOR STARTED")
            logger.info(f"📊 Symbols: {len(self.symbols)}")
            logger.info(f"⏰ Timeframes: {len(self.config.timeframes)}")
            for tf in self.config.timeframes:
                logger.info(f"   - {tf['name']}: {tf['cron']}")
            logger.info("=" * 80)

            # Run status reporter as background task (not blocking!)
            self.status_task = asyncio.create_task(self._status_reporter())

            # Keep service running
            while self.is_running:
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"❌ Error starting Tick Aggregator: {e}", exc_info=True)
            await self.stop()

    def _schedule_timeframe(self, tf_config: Dict[str, Any]):
        """
        Schedule aggregation job for a timeframe

        Args:
            tf_config: Timeframe configuration (name, cron, etc.)
        """
        timeframe = tf_config['name']
        cron = tf_config['cron']

        # Parse cron expression (minute hour day month day_of_week)
        parts = cron.split()
        if len(parts) != 5:
            logger.error(f"Invalid cron expression for {timeframe}: {cron}")
            return

        minute, hour, day, month, day_of_week = parts

        # Schedule job
        self.scheduler.add_job(
            self._aggregate_and_publish,
            'cron',
            args=[tf_config],
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            id=f"aggregate_{timeframe}",
            name=f"Aggregate {timeframe}",
            replace_existing=True
        )

        logger.info(f"✅ Scheduled {timeframe} aggregation: {cron}")

    async def _aggregate_and_publish(self, tf_config: Dict[str, Any]):
        """
        Aggregate ticks and publish candles

        Args:
            tf_config: Timeframe configuration
        """
        timeframe = tf_config['name']

        try:
            logger.info(f"🔄 Starting {timeframe} aggregation...")

            # Aggregate ticks to candles
            candles = await self.aggregator.aggregate_timeframe(
                timeframe_config=tf_config,
                symbols=self.symbols
            )

            # Publish each candle
            for candle in candles:
                await self.publisher.publish_aggregate(candle)

            logger.info(f"✅ {timeframe} aggregation complete: {len(candles)} candles published")

        except Exception as e:
            logger.error(f"❌ Error in {timeframe} aggregation: {e}", exc_info=True)

    async def _status_reporter(self):
        """Report status periodically"""
        interval = self.config.monitoring_config.get('report_interval_seconds', 300)

        while self.is_running:
            try:
                await asyncio.sleep(interval)

                # Collect statistics
                uptime = datetime.utcnow() - self.start_time
                aggregator_stats = self.aggregator.get_stats() if self.aggregator else {}
                publisher_stats = self.publisher.get_stats() if self.publisher else {}

                # Log status
                logger.info("=" * 80)
                logger.info(f"📊 STATUS REPORT - Uptime: {uptime}")
                logger.info(f"Ticks Processed: {aggregator_stats.get('total_ticks_processed', 0)}")
                logger.info(f"Candles Generated: {aggregator_stats.get('total_candles_generated', 0)}")
                logger.info(f"Published to NATS: {publisher_stats.get('nats_publish_count', 0)}")
                logger.info(f"Published to Kafka: {publisher_stats.get('kafka_publish_count', 0)}")
                logger.info(f"Scheduled Jobs: {len(self.scheduler.get_jobs()) if self.scheduler else 0}")
                logger.info("=" * 80)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in status reporter: {e}")

    async def stop(self):
        """Stop the aggregator service"""
        logger.info("🛑 Stopping Tick Aggregator Service...")
        self.is_running = False

        # Cancel status reporter task
        if self.status_task and not self.status_task.done():
            self.status_task.cancel()
            try:
                await self.status_task
            except asyncio.CancelledError:
                pass

        # Stop scheduler
        if self.scheduler:
            self.scheduler.shutdown()

        # Close connections
        if self.aggregator:
            await self.aggregator.close()

        if self.publisher:
            await self.publisher.close()

        logger.info("✅ Tick Aggregator stopped")

    def handle_signal(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}. Shutting down...")
        asyncio.create_task(self.stop())

async def main():
    """Main entry point"""
    service = TickAggregatorService()

    # Register signal handlers
    signal.signal(signal.SIGINT, service.handle_signal)
    signal.signal(signal.SIGTERM, service.handle_signal)

    try:
        await service.start()

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        await service.stop()

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        await service.stop()
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())
