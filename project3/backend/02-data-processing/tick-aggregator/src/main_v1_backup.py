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
from gap_detector import GapDetector
from historical_aggregator import HistoricalAggregator

# Central Hub SDK for progress logging
from central_hub_sdk import ProgressLogger

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
        self.gap_detector: GapDetector = None
        self.historical_aggregator: HistoricalAggregator = None
        self.scheduler: AsyncIOScheduler = None
        self.status_task: Optional[asyncio.Task] = None
        self.heartbeat_task: Optional[asyncio.Task] = None

        self.start_time = datetime.utcnow()
        self.is_running = False

        # Backfill settings
        self.enable_historical_backfill = True  # Set to False to skip backfill

        # Get symbols to aggregate (from config or default list)
        # ALL 14 PAIRS - matches historical downloader and live collector
        self.symbols = [
            # Trading Pairs (Priority 1-2) - 6 pairs
            'XAU/USD', 'GBP/USD', 'EUR/USD', 'AUD/USD', 'USD/JPY', 'USD/CAD',
            # Analysis Pairs (Priority 3) - 4 pairs
            'AUD/JPY', 'EUR/GBP', 'GBP/JPY', 'EUR/JPY',
            # Confirmation Pairs (Priority 4) - 4 pairs
            'NZD/USD', 'USD/CHF', 'NZD/JPY', 'CHF/JPY'
        ]

        # Gap detection settings
        self.gap_detection_enabled = True  # Enable by default
        self.gap_detection_lookback_hours = 72  # Check last 3 days

        logger.info("=" * 80)
        logger.info("TICK AGGREGATOR SERVICE + GAP DETECTION")
        logger.info("=" * 80)
        logger.info(f"Instance ID: {self.config.instance_id}")
        logger.info(f"Log Level: {self.config.log_level}")
        logger.info(f"Gap Detection: {'Enabled' if self.gap_detection_enabled else 'Disabled'}")

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

            # Initialize gap detector (for ClickHouse gap detection)
            if self.gap_detection_enabled:
                logger.info("🔍 Initializing Gap Detector...")
                self.gap_detector = GapDetector(
                    clickhouse_config=self.config.clickhouse_config
                )
                try:
                    self.gap_detector.connect()
                    logger.info("✅ Gap Detector initialized")
                except Exception as gap_err:
                    logger.warning(f"⚠️ Gap Detector failed to connect: {gap_err}")
                    logger.warning("⚠️ Gap detection disabled - continuing without it")
                    self.gap_detection_enabled = False

            # Run historical backfill if enabled
            if self.enable_historical_backfill:
                await self._run_historical_backfill()

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

            # Run status reporter and heartbeat as background tasks (not blocking!)
            self.status_task = asyncio.create_task(self._status_reporter())
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())

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
            replace_existing=True,
            misfire_grace_time=60  # Allow 60s grace time for startup/timing issues
        )

        logger.info(f"✅ Scheduled {timeframe} aggregation: {cron}")

    async def _run_historical_backfill(self):
        """
        Run historical backfill: aggregate 1m bars to all higher timeframes

        Checks EACH symbol individually for historical 1m data and missing H1 data
        """
        logger.info("=" * 80)
        logger.info("🔄 CHECKING HISTORICAL DATA PER SYMBOL...")
        logger.info("=" * 80)

        try:
            # Initialize historical aggregator
            self.historical_aggregator = HistoricalAggregator(
                clickhouse_config=self.config.clickhouse_config,
                aggregation_config=self.config.aggregation_config
            )
            self.historical_aggregator.connect()

            # Target timeframes (exclude 1m - already exists)
            target_timeframes = [
                {'name': '5m', 'interval_minutes': 5},
                {'name': '15m', 'interval_minutes': 15},
                {'name': '30m', 'interval_minutes': 30},
                {'name': '1h', 'interval_minutes': 60},
                {'name': '4h', 'interval_minutes': 240},
                {'name': '1d', 'interval_minutes': 1440},
                {'name': '1w', 'interval_minutes': 10080}
            ]

            symbols_to_backfill = []

            # Check EACH symbol individually
            for symbol in self.symbols:
                # Check if 1m historical data exists
                m1_query = f"""
                SELECT COUNT(*) as count
                FROM aggregates
                WHERE symbol = '{symbol}'
                  AND timeframe = '1m'
                  AND source = 'polygon_historical'
                """
                m1_result = self.historical_aggregator.client.query(m1_query)
                m1_count = m1_result.result_rows[0][0] if m1_result.result_rows else 0

                # Check if H1 historical data already exists
                h1_query = f"""
                SELECT COUNT(*) as count
                FROM aggregates
                WHERE symbol = '{symbol}'
                  AND timeframe = '1h'
                  AND source = 'historical_aggregated'
                """
                h1_result = self.historical_aggregator.client.query(h1_query)
                h1_count = h1_result.result_rows[0][0] if h1_result.result_rows else 0

                # Decision logic
                if m1_count > 0 and h1_count < 1000:
                    # Has 1m data but missing H1 → needs backfill
                    logger.info(f"✅ {symbol}: {m1_count:,} bars (1m) → Needs backfill (H1: {h1_count:,})")
                    symbols_to_backfill.append(symbol)
                elif m1_count > 0 and h1_count >= 1000:
                    # Has both 1m and H1 → already backfilled
                    logger.info(f"⏭️  {symbol}: {m1_count:,} bars (1m) + {h1_count:,} candles (H1) → Skip (already backfilled)")
                elif m1_count == 0:
                    # No 1m data → skip (REST API pairs)
                    logger.info(f"⏭️  {symbol}: No 1m historical data → Skip (REST API only)")

            # Run backfill for symbols that need it
            if symbols_to_backfill:
                logger.info("=" * 80)
                logger.info(f"🚀 Running backfill for {len(symbols_to_backfill)} symbols...")
                logger.info("=" * 80)

                total_candles = 0
                backfill_start = datetime.utcnow()

                # Calculate total tasks for progress tracking
                total_tasks = len(symbols_to_backfill) * len(target_timeframes)

                # Initialize progress logger for overall backfill
                backfill_progress = ProgressLogger(
                    task_name="Historical backfill",
                    total_items=total_tasks,
                    service_name="tick-aggregator",
                    milestones=[25, 50, 75, 100],
                    heartbeat_interval=30
                )
                backfill_progress.start()

                task_idx = 0

                # Process each symbol that needs backfill
                for symbol in symbols_to_backfill:
                    for tf_config in target_timeframes:
                        task_idx += 1

                        try:
                            candles_count = self.historical_aggregator.aggregate_symbol_timeframe(
                                symbol=symbol,
                                target_timeframe=tf_config['name'],
                                interval_minutes=tf_config['interval_minutes']
                            )
                            total_candles += candles_count

                            # Update overall backfill progress
                            backfill_progress.update(
                                current=task_idx,
                                additional_info={
                                    "symbol": symbol,
                                    "timeframe": tf_config['name'],
                                    "total_candles": total_candles
                                }
                            )

                        except Exception as e:
                            logger.error(f"❌ Failed {symbol} {tf_config['name']}: {e}")
                            # Still update progress on error
                            backfill_progress.update(
                                current=task_idx,
                                additional_info={
                                    "symbol": symbol,
                                    "timeframe": tf_config['name'],
                                    "error": str(e)[:50]
                                }
                            )
                            continue

                # Complete backfill
                backfill_progress.complete(summary={
                    "symbols_backfilled": len(symbols_to_backfill),
                    "total_candles": total_candles
                })

                # Summary
                elapsed = (datetime.utcnow() - backfill_start).total_seconds()
                logger.info("=" * 80)
                logger.info("✅ BACKFILL COMPLETE")
                logger.info(f"📊 Symbols backfilled: {len(symbols_to_backfill)}/{len(self.symbols)}")
                logger.info(f"📈 Total candles generated: {total_candles:,}")
                logger.info(f"⏱️ Time elapsed: {elapsed:.1f}s")
                logger.info(f"🚀 Throughput: {total_candles / max(elapsed, 1):.0f} candles/sec")
                logger.info("=" * 80)

            else:
                logger.info("=" * 80)
                logger.info("✅ All symbols with 1m data already have H1 data - no backfill needed")
                logger.info("=" * 80)

        except Exception as e:
            logger.error(f"❌ Backfill error: {e}", exc_info=True)
            logger.warning("⚠️ Continuing without backfill...")

    async def _aggregate_and_publish(self, tf_config: Dict[str, Any]):
        """
        Aggregate ticks and publish candles

        NEW: Auto Gap Detection & Filling
        1. BEFORE scheduled aggregation, check for recent gaps
        2. If gaps found, re-aggregate missing timestamps
        3. Then run scheduled aggregation as normal

        This ensures service restarts don't cause data loss!

        Args:
            tf_config: Timeframe configuration
        """
        timeframe = tf_config['name']
        interval_minutes = tf_config['interval_minutes']

        try:
            logger.info(f"🔄 Starting {timeframe} aggregation...")

            # STEP 1: Gap Detection & Filling (NEW!)
            if self.gap_detection_enabled and self.gap_detector:
                logger.info(f"🔍 Checking for gaps in {timeframe}...")

                # Check gaps for each symbol
                total_gaps_filled = 0
                for symbol in self.symbols:
                    gaps = self.gap_detector.detect_recent_gaps(
                        symbol=symbol,
                        timeframe=timeframe,
                        interval_minutes=interval_minutes,
                        lookback_hours=self.gap_detection_lookback_hours
                    )

                    # Fill gaps by re-aggregating
                    if gaps:
                        logger.info(f"🔧 Filling {len(gaps)} gaps for {symbol} {timeframe}...")

                        for missing_timestamp in gaps:
                            try:
                                # Create custom config for this specific timestamp
                                gap_config = tf_config.copy()

                                # Calculate lookback window for this gap
                                # We need enough data to calculate indicators (200+ candles)
                                gap_config['lookback_minutes'] = interval_minutes + 10

                                # Aggregate just this missing candle
                                gap_candles = await self.aggregator.aggregate_timeframe(
                                    timeframe_config=gap_config,
                                    symbols=[symbol]  # Single symbol
                                )

                                # Find the candle matching our missing timestamp
                                for candle in gap_candles:
                                    candle_time = datetime.fromisoformat(candle['start_time'].replace('Z', ''))

                                    # Remove timezone info for comparison (both should be UTC)
                                    if candle_time.tzinfo is not None:
                                        candle_time = candle_time.replace(tzinfo=None)

                                    # Match timestamp (within 1 minute tolerance)
                                    if abs((candle_time - missing_timestamp).total_seconds()) < 60:
                                        # Publish gap-filled candle
                                        await self.publisher.publish_aggregate(candle)
                                        total_gaps_filled += 1
                                        logger.info(
                                            f"✅ Gap filled: {symbol} {timeframe} "
                                            f"at {missing_timestamp}"
                                        )
                                        break

                            except Exception as gap_err:
                                logger.error(
                                    f"❌ Failed to fill gap for {symbol} {timeframe} "
                                    f"at {missing_timestamp}: {gap_err}"
                                )

                if total_gaps_filled > 0:
                    logger.info(f"🔧 Filled {total_gaps_filled} gaps for {timeframe}")
                else:
                    logger.info(f"✅ No gaps detected for {timeframe}")

            # STEP 2: Regular Scheduled Aggregation
            logger.info(f"📊 Running scheduled {timeframe} aggregation...")

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

    async def _heartbeat_loop(self):
        """Send periodic heartbeat to Central Hub"""
        heartbeat_interval = 30  # 30 seconds

        while self.is_running:
            try:
                await asyncio.sleep(heartbeat_interval)

                # Send heartbeat with metrics if Central Hub is available
                if hasattr(self.config, 'central_hub') and self.config.central_hub:
                    # Get aggregator and publisher stats
                    aggregator_stats = self.aggregator.get_stats() if self.aggregator else {}
                    publisher_stats = self.publisher.get_stats() if self.publisher else {}

                    metrics = {
                        'ticks_processed': aggregator_stats.get('total_ticks_processed', 0),
                        'candles_generated': aggregator_stats.get('total_candles_generated', 0),
                        'nats_published': publisher_stats.get('nats_publish_count', 0),
                        'kafka_published': publisher_stats.get('kafka_publish_count', 0),
                        'scheduled_jobs': len(self.scheduler.get_jobs()) if self.scheduler else 0,
                        'uptime_seconds': (datetime.utcnow() - self.start_time).total_seconds()
                    }

                    try:
                        await self.config.central_hub.send_heartbeat(metrics=metrics)
                        logger.debug("💓 Heartbeat sent to Central Hub")
                    except Exception as hb_err:
                        logger.warning(f"⚠️  Failed to send heartbeat: {hb_err}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")

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

        # Cancel heartbeat task
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
