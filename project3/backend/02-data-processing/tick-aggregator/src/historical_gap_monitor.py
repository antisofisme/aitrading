"""
Historical Gap Monitor - Scan and fill gaps in historical aggregated data
Runs daily to ensure historical data completeness
"""
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta, timezone

from historical_aggregator import HistoricalAggregator
from gap_detector import GapDetector

logger = logging.getLogger(__name__)


class HistoricalGapMonitor:
    """
    Historical data gap monitoring and filling

    Priority: LOW
    Trigger: Daily (02:00 UTC)
    Source: ClickHouse.aggregates (1m bars)
    Lookback: All historical data (>7 days ago)
    Destination: ClickHouse.aggregates (source='historical_aggregated')

    Flow:
    1. Scan for gaps in historical_aggregated (older than 7 days)
    2. Re-aggregate from 1m bars
    3. Fill old historical gaps
    4. Smart skip: Don't touch recent data (live owns it)
    """

    def __init__(
        self,
        historical_aggregator: HistoricalAggregator,
        gap_detector: GapDetector,
        symbols: List[str],
        min_age_days: int = 7
    ):
        """
        Initialize historical gap monitor

        Args:
            historical_aggregator: Historical aggregator instance
            gap_detector: Gap detector instance
            symbols: List of symbols to monitor
            min_age_days: Only check gaps older than this (default: 7 days)
        """
        self.historical_aggregator = historical_aggregator
        self.gap_detector = gap_detector
        self.symbols = symbols
        self.min_age_days = min_age_days

        # Target timeframes
        self.timeframes = [
            {'name': '5m', 'interval_minutes': 5},
            {'name': '15m', 'interval_minutes': 15},
            {'name': '30m', 'interval_minutes': 30},
            {'name': '1h', 'interval_minutes': 60},
            {'name': '4h', 'interval_minutes': 240},
            {'name': '1d', 'interval_minutes': 1440},
            {'name': '1w', 'interval_minutes': 10080}
        ]

        # Statistics
        self.total_scans = 0
        self.total_gaps_found = 0
        self.total_gaps_filled = 0
        self.total_errors = 0
        self.last_scan_time = None
        self.last_scan_status = "not_started"

        logger.info(f"✅ HistoricalGapMonitor initialized (min_age: {min_age_days} days)")

    async def monitor(self):
        """
        Main monitoring routine - called by cron daily

        Steps:
        1. Scan for gaps in historical data (>7 days old)
        2. Re-aggregate from 1m bars
        3. Track statistics
        """
        try:
            self.total_scans += 1
            self.last_scan_time = datetime.now(timezone.utc)
            self.last_scan_status = "running"

            logger.info(f"🔍 [HistoricalGapMonitor] Scan #{self.total_scans} started")

            gaps_found = 0
            gaps_filled = 0

            # Scan each symbol/timeframe
            for symbol in self.symbols:
                for tf_config in self.timeframes:
                    timeframe = tf_config['name']
                    interval_minutes = tf_config['interval_minutes']

                    try:
                        # Detect gaps in historical data
                        # Note: We look back further than live monitor (30 days vs 7 days)
                        missing_timestamps = self.gap_detector.detect_recent_gaps(
                            symbol=symbol,
                            timeframe=timeframe,
                            interval_minutes=interval_minutes,
                            lookback_hours=30 * 24  # 30 days
                        )

                        if missing_timestamps:
                            # Filter: Only gaps older than min_age_days
                            cutoff_time = datetime.now(timezone.utc) - timedelta(days=self.min_age_days)
                            old_gaps = [
                                ts for ts in missing_timestamps
                                if ts.replace(tzinfo=timezone.utc) < cutoff_time
                            ]

                            if old_gaps:
                                gaps_found += len(old_gaps)
                                self.total_gaps_found += len(old_gaps)

                                logger.info(
                                    f"🔍 [HistoricalGapMonitor] {symbol} {timeframe}: "
                                    f"{len(old_gaps)} old gaps found"
                                )

                                # Re-aggregate from 1m bars (limit to 50 gaps per run)
                                for gap_ts in old_gaps[:50]:
                                    try:
                                        # Find date range for this gap
                                        gap_start = gap_ts
                                        gap_end = gap_ts + timedelta(minutes=interval_minutes)

                                        # Re-aggregate this specific range
                                        count = self.historical_aggregator.aggregate_symbol_timeframe(
                                            symbol=symbol,
                                            target_timeframe=timeframe,
                                            interval_minutes=interval_minutes,
                                            start_date=gap_start,
                                            end_date=gap_end
                                        )

                                        if count > 0:
                                            gaps_filled += count
                                            self.total_gaps_filled += count
                                            logger.debug(
                                                f"🔧 [HistoricalGapMonitor] Filled: {symbol} {timeframe} @ {gap_ts}"
                                            )

                                    except Exception as fill_err:
                                        self.total_errors += 1
                                        logger.error(
                                            f"❌ [HistoricalGapMonitor] Fill failed: "
                                            f"{symbol} {timeframe} @ {gap_ts}: {fill_err}"
                                        )

                    except Exception as tf_err:
                        self.total_errors += 1
                        logger.error(
                            f"❌ [HistoricalGapMonitor] Error for {symbol} {timeframe}: {tf_err}"
                        )

            self.last_scan_status = "success"

            logger.info(
                f"✅ [HistoricalGapMonitor] Scan #{self.total_scans} complete: "
                f"{gaps_found} gaps found, {gaps_filled} filled"
            )

        except Exception as e:
            self.total_errors += 1
            self.last_scan_status = "error"
            logger.error(f"❌ [HistoricalGapMonitor] Error in scan #{self.total_scans}: {e}", exc_info=True)

    def get_stats(self) -> Dict[str, Any]:
        """Get monitor statistics"""
        return {
            'component': 'historical_gap_monitor',
            'priority': 'LOW',
            'total_scans': self.total_scans,
            'total_gaps_found': self.total_gaps_found,
            'total_gaps_filled': self.total_gaps_filled,
            'total_errors': self.total_errors,
            'last_scan_time': self.last_scan_time.isoformat() if self.last_scan_time else None,
            'last_scan_status': self.last_scan_status,
            'min_age_days': self.min_age_days
        }
