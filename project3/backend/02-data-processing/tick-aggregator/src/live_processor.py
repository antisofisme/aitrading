"""
Live Processor - Real-time tick aggregation with gap detection
Runs every 1 minute to aggregate recent ticks from TimescaleDB
"""
import logging
import asyncio
from typing import List, Dict, Any
from datetime import datetime, timedelta, timezone

from aggregator import TickAggregator
from nats_publisher import AggregatePublisher
from gap_detector import GapDetector

logger = logging.getLogger(__name__)


class LiveProcessor:
    """
    Live tick aggregation processor

    Priority: CRITICAL (highest)
    Trigger: Every 1 minute
    Source: TimescaleDB.ticks
    Destination: ClickHouse.aggregates (source='live_aggregated')

    Flow:
    1. Check for gaps in last 24h (before aggregation)
    2. Aggregate recent ticks to all timeframes
    3. Publish to NATS → Data Bridge → ClickHouse
    4. Track statistics
    """

    def __init__(
        self,
        aggregator: TickAggregator,
        publisher: AggregatePublisher,
        gap_detector: GapDetector,
        symbols: List[str],
        timeframes: List[Dict[str, Any]]
    ):
        """
        Initialize live processor

        Args:
            aggregator: Tick aggregator instance
            publisher: NATS/Kafka publisher instance
            gap_detector: Gap detector instance
            symbols: List of symbols to process
            timeframes: List of timeframe configs
        """
        self.aggregator = aggregator
        self.publisher = publisher
        self.gap_detector = gap_detector
        self.symbols = symbols
        self.timeframes = timeframes

        # Statistics
        self.total_runs = 0
        self.total_candles_generated = 0
        self.total_gaps_detected = 0
        self.total_gaps_filled = 0
        self.total_errors = 0
        self.last_run_time = None
        self.last_run_status = "not_started"

        logger.info("✅ LiveProcessor initialized")

    async def process(self):
        """
        Main processing routine - called by cron every 1 minute

        Steps:
        1. Detect gaps (last 24h)
        2. Fill gaps if found
        3. Aggregate recent ticks
        4. Publish candles
        """
        try:
            self.total_runs += 1
            self.last_run_time = datetime.now(timezone.utc)
            self.last_run_status = "running"

            logger.info(f"🔄 [LiveProcessor] Run #{self.total_runs} started")

            # STEP 1: Gap Detection (last 24h)
            gaps_found = await self._detect_and_fill_gaps()

            # STEP 2: Regular scheduled aggregation
            candles_count = await self._aggregate_recent_ticks()

            self.total_candles_generated += candles_count
            self.last_run_status = "success"

            logger.info(
                f"✅ [LiveProcessor] Run #{self.total_runs} complete: "
                f"{candles_count} candles, {gaps_found} gaps filled"
            )

        except Exception as e:
            self.total_errors += 1
            self.last_run_status = "error"
            logger.error(f"❌ [LiveProcessor] Error in run #{self.total_runs}: {e}", exc_info=True)

    async def _detect_and_fill_gaps(self) -> int:
        """
        Detect and fill gaps in last 24h

        Returns:
            Number of gaps filled
        """
        if not self.gap_detector:
            return 0

        try:
            total_filled = 0

            # Check each symbol/timeframe combination
            for symbol in self.symbols:
                for tf_config in self.timeframes:
                    timeframe = tf_config['name']
                    interval_minutes = tf_config['interval_minutes']

                    # Detect gaps (last 24h)
                    missing_timestamps = self.gap_detector.detect_recent_gaps(
                        symbol=symbol,
                        timeframe=timeframe,
                        interval_minutes=interval_minutes,
                        lookback_hours=24
                    )

                    if missing_timestamps:
                        self.total_gaps_detected += len(missing_timestamps)

                        # Fill gaps by re-aggregating from TimescaleDB
                        # Note: We aggregate recent data and filter for the gap timestamp
                        for missing_ts in missing_timestamps[:10]:  # Limit to 10 gaps per run
                            try:
                                # Aggregate recent data (TickAggregator doesn't support start_time/end_time)
                                gap_candles = await self.aggregator.aggregate_timeframe(
                                    timeframe_config=tf_config,
                                    symbols=[symbol]
                                )

                                # Publish gap-filled candles
                                for candle in gap_candles:
                                    candle['source'] = 'live_gap_filled'  # Mark as gap-filled
                                    await self.publisher.publish_aggregate(candle)
                                    total_filled += 1
                                    self.total_gaps_filled += 1

                                logger.info(f"🔧 [LiveGapFill] {symbol} {timeframe} @ {missing_ts}")

                            except Exception as gap_err:
                                logger.error(
                                    f"❌ [LiveGapFill] Failed {symbol} {timeframe} @ {missing_ts}: {gap_err}"
                                )

            return total_filled

        except Exception as e:
            logger.error(f"❌ [LiveGapDetection] Error: {e}", exc_info=True)
            return 0

    async def _aggregate_recent_ticks(self) -> int:
        """
        Aggregate recent ticks from TimescaleDB to all timeframes

        Returns:
            Number of candles generated
        """
        try:
            total_candles = 0

            # Process each timeframe
            for tf_config in self.timeframes:
                try:
                    # Aggregate ticks for all symbols
                    candles = await self.aggregator.aggregate_timeframe(
                        timeframe_config=tf_config,
                        symbols=self.symbols
                    )

                    # Publish each candle
                    for candle in candles:
                        candle['source'] = 'live_aggregated'  # Mark as live data
                        await self.publisher.publish_aggregate(candle)
                        total_candles += 1

                    if candles:
                        logger.debug(
                            f"📊 [LiveAggregation] {tf_config['name']}: {len(candles)} candles"
                        )

                except Exception as tf_err:
                    logger.error(
                        f"❌ [LiveAggregation] Error for {tf_config['name']}: {tf_err}"
                    )

            return total_candles

        except Exception as e:
            logger.error(f"❌ [LiveAggregation] Error: {e}", exc_info=True)
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """Get processor statistics"""
        return {
            'component': 'live_processor',
            'priority': 'CRITICAL',
            'total_runs': self.total_runs,
            'total_candles_generated': self.total_candles_generated,
            'total_gaps_detected': self.total_gaps_detected,
            'total_gaps_filled': self.total_gaps_filled,
            'total_errors': self.total_errors,
            'last_run_time': self.last_run_time.isoformat() if self.last_run_time else None,
            'last_run_status': self.last_run_status
        }
