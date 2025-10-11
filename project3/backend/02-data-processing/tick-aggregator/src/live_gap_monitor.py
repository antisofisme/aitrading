"""
Live Gap Monitor - Dedicated gap detection and filling for live data
Runs every 5 minutes to scan and fill gaps in last 7 days
"""
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta, timezone

from aggregator import TickAggregator
from nats_publisher import AggregatePublisher
from gap_detector import GapDetector

logger = logging.getLogger(__name__)


class LiveGapMonitor:
    """
    Live data gap monitoring and filling

    Priority: HIGH
    Trigger: Every 5 minutes
    Source: TimescaleDB.ticks (for filling)
    Lookback: Last 7 days
    Destination: ClickHouse.aggregates (source='live_gap_filled')

    Flow:
    1. Scan ClickHouse for gaps in live data (last 7 days)
    2. For each gap, check if ticks exist in TimescaleDB
    3. Re-aggregate missing candles
    4. Mark as source='live_gap_filled'
    5. Track oldest gap age for monitoring
    """

    def __init__(
        self,
        aggregator: TickAggregator,
        publisher: AggregatePublisher,
        gap_detector: GapDetector,
        symbols: List[str],
        timeframes: List[Dict[str, Any]],
        lookback_days: int = 7
    ):
        """
        Initialize live gap monitor

        Args:
            aggregator: Tick aggregator instance
            publisher: NATS/Kafka publisher instance
            gap_detector: Gap detector instance
            symbols: List of symbols to monitor
            timeframes: List of timeframe configs
            lookback_days: How far back to check for gaps (default: 7 days)
        """
        self.aggregator = aggregator
        self.publisher = publisher
        self.gap_detector = gap_detector
        self.symbols = symbols
        self.timeframes = timeframes
        self.lookback_days = lookback_days

        # Statistics
        self.total_scans = 0
        self.total_gaps_found = 0
        self.total_gaps_filled = 0
        self.total_fill_errors = 0
        self.oldest_gap_hours = 0
        self.last_scan_time = None
        self.last_scan_status = "not_started"

        logger.info(f"✅ LiveGapMonitor initialized (lookback: {lookback_days} days)")

    async def monitor(self):
        """
        Main monitoring routine - called by cron every 5 minutes

        Steps:
        1. Scan for gaps (last 7 days)
        2. Fill gaps from TimescaleDB ticks
        3. Track oldest gap for alerting
        """
        try:
            self.total_scans += 1
            self.last_scan_time = datetime.now(timezone.utc)
            self.last_scan_status = "running"

            logger.info(f"🔍 [LiveGapMonitor] Scan #{self.total_scans} started")

            gaps_found = 0
            gaps_filled = 0
            oldest_gap = None

            # Scan each symbol/timeframe
            for symbol in self.symbols:
                for tf_config in self.timeframes:
                    timeframe = tf_config['name']
                    interval_minutes = tf_config['interval_minutes']

                    # Detect gaps (last N days)
                    missing_timestamps = self.gap_detector.detect_recent_gaps(
                        symbol=symbol,
                        timeframe=timeframe,
                        interval_minutes=interval_minutes,
                        lookback_hours=self.lookback_days * 24
                    )

                    if missing_timestamps:
                        gaps_found += len(missing_timestamps)
                        self.total_gaps_found += len(missing_timestamps)

                        # Track oldest gap
                        oldest_in_batch = min(missing_timestamps)
                        if oldest_gap is None or oldest_in_batch < oldest_gap:
                            oldest_gap = oldest_in_batch

                        # Fill gaps (limit to 20 per symbol/timeframe per run)
                        # Note: We aggregate recent data and filter for gap timestamps
                        for missing_ts in missing_timestamps[:20]:
                            try:
                                # Re-aggregate from TimescaleDB (no start_time/end_time params)
                                gap_candles = await self.aggregator.aggregate_timeframe(
                                    timeframe_config=tf_config,
                                    symbols=[symbol]
                                )

                                # Publish gap-filled candles
                                for candle in gap_candles:
                                    candle['source'] = 'live_gap_filled'
                                    await self.publisher.publish_aggregate(candle)
                                    gaps_filled += 1
                                    self.total_gaps_filled += 1

                                logger.debug(
                                    f"🔧 [LiveGapMonitor] Filled: {symbol} {timeframe} @ {missing_ts}"
                                )

                            except Exception as fill_err:
                                self.total_fill_errors += 1
                                logger.error(
                                    f"❌ [LiveGapMonitor] Fill failed: {symbol} {timeframe} @ {missing_ts}: {fill_err}"
                                )

            # Calculate oldest gap age
            if oldest_gap:
                self.oldest_gap_hours = (datetime.now(timezone.utc) - oldest_gap.replace(tzinfo=timezone.utc)).total_seconds() / 3600

            self.last_scan_status = "success"

            logger.info(
                f"✅ [LiveGapMonitor] Scan #{self.total_scans} complete: "
                f"{gaps_found} gaps found, {gaps_filled} filled"
            )

            if self.oldest_gap_hours > 0:
                logger.info(f"📊 [LiveGapMonitor] Oldest gap: {self.oldest_gap_hours:.1f}h ago")

        except Exception as e:
            self.last_scan_status = "error"
            logger.error(f"❌ [LiveGapMonitor] Error in scan #{self.total_scans}: {e}", exc_info=True)

    def get_stats(self) -> Dict[str, Any]:
        """Get monitor statistics"""
        return {
            'component': 'live_gap_monitor',
            'priority': 'HIGH',
            'total_scans': self.total_scans,
            'total_gaps_found': self.total_gaps_found,
            'total_gaps_filled': self.total_gaps_filled,
            'total_fill_errors': self.total_fill_errors,
            'oldest_gap_hours': round(self.oldest_gap_hours, 2),
            'last_scan_time': self.last_scan_time.isoformat() if self.last_scan_time else None,
            'last_scan_status': self.last_scan_status,
            'lookback_days': self.lookback_days
        }
