#!/usr/bin/env python3
"""
Tick Aggregator Service V2 - Redesigned with 4 Parallel Components

ARCHITECTURE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[1] LiveProcessor        (CRITICAL) - Every 1 minute
    ├─ Source: TimescaleDB.ticks
    ├─ Destination: ClickHouse (source='live_aggregated')
    └─ Gap Check: Last 24h before each run

[2] LiveGapMonitor       (HIGH)     - Every 5 minutes
    ├─ Scan: ClickHouse gaps (last 7 days)
    ├─ Fill: From TimescaleDB ticks
    └─ Mark: source='live_gap_filled'

[3] HistoricalProcessor  (MEDIUM)   - Every 6 hours
    ├─ Source: ClickHouse 1m bars
    ├─ Aggregate: 1m → 5m,15m,30m,1h,4h,1d,1w
    └─ Mark: source='historical_aggregated'

[4] HistoricalGapMonitor (LOW)      - Daily 02:00 UTC
    ├─ Scan: Historical gaps (>7 days old)
    ├─ Fill: From 1m bars
    └─ Smart Skip: Don't touch recent data
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DATA PRIORITY (deduplication via ReplacingMergeTree):
    live_aggregated (highest version) > live_gap_filled > historical_aggregated
"""
import asyncio
import logging
import signal
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.events import EVENT_JOB_MISSED

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from aggregator import TickAggregator
from nats_publisher import AggregatePublisher
from gap_detector import GapDetector
from historical_aggregator import HistoricalAggregator

# NEW: Import 4 parallel components
from live_processor import LiveProcessor
from live_gap_monitor import LiveGapMonitor
from historical_processor import HistoricalProcessor
from historical_gap_monitor import HistoricalGapMonitor

# Central Hub SDK
from central_hub_sdk import ProgressLogger

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class TickAggregatorServiceV2:
    """
    Enhanced Tick Aggregator Service with 4 parallel components

    Key Features:
    - Continuous gap monitoring and auto-recovery
    - Priority-based data handling (live > historical)
    - Deduplication via ClickHouse ReplacingMergeTree
    - Comprehensive metrics and monitoring
    """

    def __init__(self):
        self.config = Config()

        # Core components (shared across processors)
        self.aggregator: Optional[TickAggregator] = None
        self.publisher: Optional[AggregatePublisher] = None
        self.gap_detector: Optional[GapDetector] = None
        self.historical_aggregator: Optional[HistoricalAggregator] = None

        # NEW: 4 parallel processors
        self.live_processor: Optional[LiveProcessor] = None
        self.live_gap_monitor: Optional[LiveGapMonitor] = None
        self.historical_processor: Optional[HistoricalProcessor] = None
        self.historical_gap_monitor: Optional[HistoricalGapMonitor] = None

        # Scheduler
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.heartbeat_task: Optional[asyncio.Task] = None

        # Runtime state
        self.start_time = datetime.now(timezone.utc)
        self.is_running = False

        # Symbols to process
        self.symbols = [
            'XAU/USD', 'GBP/USD', 'EUR/USD', 'AUD/USD', 'USD/JPY', 'USD/CAD',
            'AUD/JPY', 'EUR/GBP', 'GBP/JPY', 'EUR/JPY',
            'NZD/USD', 'USD/CHF', 'NZD/JPY', 'CHF/JPY'
        ]

        logger.info("=" * 80)
        logger.info("TICK AGGREGATOR SERVICE V2 - 4 PARALLEL COMPONENTS")
        logger.info("=" * 80)
        logger.info(f"Instance ID: {self.config.instance_id}")
        logger.info(f"Symbols: {len(self.symbols)}")

    async def start(self):
        """Initialize and start all 4 components"""
        try:
            logger.info("🚀 Starting Tick Aggregator Service V2...")

            # Initialize Central Hub
            await self.config.initialize_central_hub()

            # STEP 1: Initialize shared components
            await self._initialize_shared_components()

            # STEP 2: Initialize 4 parallel processors
            await self._initialize_processors()

            # STEP 3: Setup scheduler
            await self._setup_scheduler()

            # STEP 4: Start scheduler
            self.scheduler.start()
            self.is_running = True

            logger.info("=" * 80)
            logger.info("✅ SERVICE STARTED - ALL 4 COMPONENTS ACTIVE")
            logger.info("=" * 80)
            logger.info("📋 Scheduled Jobs:")
            for job in self.scheduler.get_jobs():
                logger.info(f"   - {job.name}: {job.trigger}")
            logger.info("=" * 80)

            # Start heartbeat
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            # Keep service running
            while self.is_running:
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"❌ Fatal error starting service: {e}", exc_info=True)
            await self.stop()

    async def _initialize_shared_components(self):
        """Initialize components shared across processors with retry logic"""
        logger.info("📦 Initializing shared components with retry logic...")

        # Import retry utility
        sys.path.insert(0, '/app')
        from shared.utils.connection_retry import connect_with_retry, sync_connect_with_retry

        # Tick aggregator (TimescaleDB → candles)
        logger.info("   [1/4] Tick Aggregator...")
        self.aggregator = TickAggregator(
            db_config=self.config.database_config,
            aggregation_config=self.config.aggregation_config
        )
        await connect_with_retry(
            self.aggregator.connect,
            "TimescaleDB (Tick Aggregator)",
            max_retries=10
        )

        # NATS/Kafka publisher (with circuit breaker + PostgreSQL fallback)
        logger.info("   [2/4] NATS/Kafka Publisher...")
        self.publisher = AggregatePublisher(
            nats_config=self.config.nats_config,
            kafka_config=self.config.kafka_config,
            db_config=self.config.database_config  # PostgreSQL for fallback queue
        )
        await connect_with_retry(
            self.publisher.connect,
            "NATS/Kafka (Publisher)",
            max_retries=10
        )

        # Gap detector (ClickHouse gap scanning)
        logger.info("   [3/4] Gap Detector...")
        self.gap_detector = GapDetector(
            clickhouse_config=self.config.clickhouse_config
        )
        try:
            sync_connect_with_retry(
                self.gap_detector.connect,
                "ClickHouse (Gap Detector)",
                max_retries=10
            )
        except Exception as e:
            logger.warning(f"⚠️ Gap Detector failed after retries: {e}")
            logger.warning("⚠️ Gap detection will be disabled")
            self.gap_detector = None

        # Historical aggregator (1m → timeframes)
        logger.info("   [4/4] Historical Aggregator...")
        self.historical_aggregator = HistoricalAggregator(
            clickhouse_config=self.config.clickhouse_config,
            aggregation_config=self.config.aggregation_config
        )
        sync_connect_with_retry(
            self.historical_aggregator.connect,
            "ClickHouse (Historical Aggregator)",
            max_retries=10
        )

        logger.info("✅ Shared components initialized")

    async def _initialize_processors(self):
        """Initialize 4 parallel processors"""
        logger.info("🔧 Initializing 4 parallel processors...")

        # [1] LiveProcessor (CRITICAL)
        logger.info("   [1/4] LiveProcessor (CRITICAL priority)...")
        self.live_processor = LiveProcessor(
            aggregator=self.aggregator,
            publisher=self.publisher,
            gap_detector=self.gap_detector,
            symbols=self.symbols,
            timeframes=self.config.timeframes
        )

        # [2] LiveGapMonitor (HIGH)
        logger.info("   [2/4] LiveGapMonitor (HIGH priority)...")
        self.live_gap_monitor = LiveGapMonitor(
            aggregator=self.aggregator,
            publisher=self.publisher,
            gap_detector=self.gap_detector,
            symbols=self.symbols,
            timeframes=self.config.timeframes,
            lookback_days=2  # Match TimescaleDB retention (2-3 days max for live ticks)
        )

        # [3] HistoricalProcessor (MEDIUM)
        logger.info("   [3/4] HistoricalProcessor (MEDIUM priority)...")
        self.historical_processor = HistoricalProcessor(
            historical_aggregator=self.historical_aggregator,
            symbols=self.symbols
        )

        # [4] HistoricalGapMonitor (LOW)
        logger.info("   [4/4] HistoricalGapMonitor (LOW priority)...")
        self.historical_gap_monitor = HistoricalGapMonitor(
            historical_aggregator=self.historical_aggregator,
            gap_detector=self.gap_detector,
            symbols=self.symbols,
            min_age_days=7
        )

        logger.info("✅ All 4 processors initialized")

    def _monitor_job_duration(self, job_name: str, start_time: datetime) -> float:
        """Monitor and alert on long-running jobs"""
        duration = (datetime.now(timezone.utc) - start_time).total_seconds() / 3600  # hours

        if duration > 5:
            logger.warning(
                f"⚠️ Job '{job_name}' running for {duration:.1f} hours "
                f"(threshold: 5h). Next scheduled run may be skipped."
            )

        return duration

    async def _run_historical_processor_with_monitoring(self):
        """Wrapper to monitor historical processor execution"""
        start_time = datetime.now(timezone.utc)
        job_name = "HistoricalProcessor"

        try:
            logger.info(f"🚀 Starting {job_name}")
            await self.historical_processor.process()

            duration = self._monitor_job_duration(job_name, start_time)
            logger.info(f"✅ {job_name} completed in {duration:.2f} hours")

        except Exception as e:
            logger.error(f"❌ {job_name} failed: {e}", exc_info=True)
            raise

    def _job_missed_listener(self, event):
        """Log when jobs are skipped due to coalesce"""
        logger.warning(
            f"⏭️ Job skipped due to previous run still active: {event.job_id} "
            f"(scheduled for {event.scheduled_run_time})"
        )

    async def _setup_scheduler(self):
        """Setup APScheduler with 4 cron jobs"""
        logger.info("⏰ Setting up scheduler...")
        self.scheduler = AsyncIOScheduler()

        # Register event listener for skipped jobs
        self.scheduler.add_listener(
            self._job_missed_listener,
            EVENT_JOB_MISSED
        )

        # [1] LiveProcessor - Every 1 minute (CRITICAL)
        self.scheduler.add_job(
            self.live_processor.process,
            'cron',
            minute='*',  # Every minute
            id='live_processor',
            name='LiveProcessor (1min)',
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=30
        )
        logger.info("   ✅ LiveProcessor: */1 * * * * (every 1 min, max_instances=1, coalesce=True)")

        # [2] LiveGapMonitor - Every 5 minutes (HIGH)
        self.scheduler.add_job(
            self.live_gap_monitor.monitor,
            'cron',
            minute='*/5',  # Every 5 minutes
            id='live_gap_monitor',
            name='LiveGapMonitor (5min)',
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=60
        )
        logger.info("   ✅ LiveGapMonitor: */5 * * * * (every 5 min, max_instances=1, coalesce=True)")

        # [3] HistoricalProcessor - Every 6 hours (MEDIUM) - WITH MONITORING
        self.scheduler.add_job(
            self._run_historical_processor_with_monitoring,
            'cron',
            hour='*/6',  # Every 6 hours
            minute='30',  # At :30 past the hour
            id='historical_processor',
            name='HistoricalProcessor (6h)',
            replace_existing=True,
            max_instances=1,  # Only one instance at a time
            coalesce=True,  # Skip if previous run still active
            misfire_grace_time=300  # Allow 5 min delay for startup
        )
        logger.info("   ✅ HistoricalProcessor: 30 */6 * * * (every 6h at :30, max_instances=1, coalesce=True)")

        # [4] HistoricalGapMonitor - Daily at 02:00 UTC (LOW)
        self.scheduler.add_job(
            self.historical_gap_monitor.monitor,
            'cron',
            hour='2',  # 02:00 UTC
            minute='0',
            id='historical_gap_monitor',
            name='HistoricalGapMonitor (daily)',
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=600
        )
        logger.info("   ✅ HistoricalGapMonitor: 0 2 * * * (daily at 02:00 UTC, max_instances=1, coalesce=True)")

        logger.info("✅ Scheduler configured with 4 cron jobs (all with max_instances=1 and coalesce=True)")

    async def _heartbeat_loop(self):
        """Send periodic heartbeat with metrics from all 4 components"""
        interval = 60  # Every 60 seconds

        while self.is_running:
            try:
                await asyncio.sleep(interval)

                if hasattr(self.config, 'central_hub') and self.config.central_hub:
                    # Collect metrics from all components
                    metrics = self._collect_metrics()

                    try:
                        await self.config.central_hub.send_heartbeat(metrics=metrics)
                        logger.debug("💓 Heartbeat sent (all components)")
                    except Exception as hb_err:
                        logger.warning(f"⚠️ Heartbeat failed: {hb_err}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Heartbeat loop error: {e}")

    def _collect_metrics(self) -> Dict[str, Any]:
        """Collect metrics from all 4 components"""
        metrics = {
            'service': 'tick-aggregator-v2',
            'uptime_seconds': (datetime.now(timezone.utc) - self.start_time).total_seconds(),
            'components': {}
        }

        # Add metrics from each component
        if self.live_processor:
            metrics['components']['live_processor'] = self.live_processor.get_stats()

        if self.live_gap_monitor:
            metrics['components']['live_gap_monitor'] = self.live_gap_monitor.get_stats()

        if self.historical_processor:
            metrics['components']['historical_processor'] = self.historical_processor.get_stats()

        if self.historical_gap_monitor:
            metrics['components']['historical_gap_monitor'] = self.historical_gap_monitor.get_stats()

        # Calculate aggregate statistics
        metrics['summary'] = {
            'total_live_candles': metrics['components'].get('live_processor', {}).get('total_candles_generated', 0),
            'total_gaps_filled': (
                metrics['components'].get('live_gap_monitor', {}).get('total_gaps_filled', 0) +
                metrics['components'].get('historical_gap_monitor', {}).get('total_gaps_filled', 0)
            ),
            'total_historical_candles': metrics['components'].get('historical_processor', {}).get('total_candles_generated', 0)
        }

        return metrics

    def get_metrics(self) -> Dict[str, Any]:
        """Public method to get current metrics (for API endpoint)"""
        return self._collect_metrics()

    async def stop(self):
        """Stop service and cleanup"""
        logger.info("🛑 Stopping Tick Aggregator Service V2...")
        self.is_running = False

        # Cancel heartbeat
        if self.heartbeat_task and not self.heartbeat_task.done():
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
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

        if self.gap_detector:
            self.gap_detector.close()

        if self.historical_aggregator:
            self.historical_aggregator.close()

        logger.info("✅ Service stopped")

    def handle_signal(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}. Shutting down...")
        asyncio.create_task(self.stop())


async def main():
    """Main entry point"""
    service = TickAggregatorServiceV2()

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
