"""
Gap Analyzer - Detect and analyze data gaps in historical aggregates

This module handles:
- Date coverage checking
- Gap detection across time ranges
- Aggregation strategy determination
- Gap prioritization and grouping
"""
import logging
from typing import List, Dict, Any
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


class GapAnalyzer:
    """
    Analyzes gaps in historical aggregated data

    Responsibilities:
    - Check date range coverage of existing data
    - Detect missing timestamps across full historical period
    - Determine optimal aggregation strategy (full vs incremental)
    - Group consecutive gaps into periods
    """

    def __init__(self, clickhouse_client, clickhouse_config):
        """
        Initialize gap analyzer

        Args:
            clickhouse_client: ClickHouse client instance
            clickhouse_config: ClickHouse configuration dict
        """
        self.client = clickhouse_client
        self.clickhouse_config = clickhouse_config
        logger.debug("✅ GapAnalyzer initialized")

    def check_date_coverage(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """
        Check date range coverage of existing data

        Args:
            symbol: Symbol to check
            timeframe: Timeframe to check

        Returns:
            Dict with keys: count, earliest, latest, is_complete
        """
        try:
            query = f"""
            SELECT
                COUNT(*) as count,
                MIN(timestamp_ms) as earliest_ms,
                MAX(timestamp_ms) as latest_ms
            FROM aggregates
            WHERE symbol = '{symbol}'
              AND timeframe = '{timeframe}'
              AND source = 'historical_aggregated'
            """
            result = self.client.query(query)

            if not result.result_rows or result.result_rows[0][0] == 0:
                return {'count': 0, 'earliest': None, 'latest': None, 'is_complete': False}

            count = result.result_rows[0][0]
            earliest_ms = result.result_rows[0][1]
            latest_ms = result.result_rows[0][2]

            # Convert to datetime
            earliest = datetime.fromtimestamp(earliest_ms / 1000, tz=timezone.utc) if earliest_ms else None
            latest = datetime.fromtimestamp(latest_ms / 1000, tz=timezone.utc) if latest_ms else None

            # Check if date range is complete
            # Complete means: earliest <= 2015-01-10 AND latest >= (now - 3 days) AND count >= 1000
            target_earliest = datetime(2015, 1, 10, tzinfo=timezone.utc)
            target_latest = datetime.now(timezone.utc) - timedelta(days=3)

            is_complete = (
                count >= 1000 and
                earliest is not None and earliest <= target_earliest and
                latest is not None and latest >= target_latest
            )

            return {
                'count': count,
                'earliest': earliest,
                'latest': latest,
                'is_complete': is_complete
            }

        except Exception as e:
            logger.error(f"❌ Error checking date coverage for {symbol} {timeframe}: {e}")
            return {'count': 0, 'earliest': None, 'latest': None, 'is_complete': False}

    def determine_aggregation_range(
        self,
        symbol: str,
        timeframe: str,
        coverage: Dict[str, Any]
    ) -> tuple:
        """
        Determine optimal date range - detects ALL gaps (even 1 day) including middle gaps

        Strategy:
        1. Query ALL existing timestamps from ClickHouse
        2. Generate expected timestamps based on timeframe interval
        3. Find missing timestamps (actual gap detection)
        4. Group consecutive missing timestamps into gap periods
        5. Return earliest gap period to fill

        This detects gaps of ANY SIZE (1 day, 1 week, 1 month, etc.) at ANY POSITION.

        Args:
            symbol: Trading pair
            timeframe: Target timeframe
            coverage: Dict with count, earliest, latest, is_complete

        Returns:
            (start_date, end_date, strategy_name)
        """
        # If no data at all, do full backfill
        if coverage['count'] == 0:
            return None, None, "FULL_BACKFILL"

        # Use gap_detector to find ALL missing timestamps (handles weekends!)
        try:
            # Get timeframe interval in minutes
            interval_map = {
                '5m': 5, '15m': 15, '30m': 30, '1h': 60,
                '4h': 240, '1d': 1440, '1w': 10080
            }
            interval_minutes = interval_map.get(timeframe, 5)

            # Detect gaps for FULL historical period (2015 to now)
            # We'll check in chunks to avoid memory issues
            from gap_detector import GapDetector
            gap_detector = GapDetector(self.clickhouse_config)
            gap_detector.connect()

            # Check last 11 years in chunks of 1 year
            all_missing = []
            now = datetime.now(timezone.utc)

            for year_offset in range(11):  # 2015-2025 = 11 years
                chunk_end = now - timedelta(days=365 * year_offset)
                chunk_start = chunk_end - timedelta(days=365)

                # Clamp to 2015
                if chunk_start < datetime(2015, 1, 1, tzinfo=timezone.utc):
                    chunk_start = datetime(2015, 1, 1, tzinfo=timezone.utc)

                # Detect gaps in this year chunk
                missing_in_chunk = self.detect_gaps_in_range(
                    gap_detector=gap_detector,
                    symbol=symbol,
                    timeframe=timeframe,
                    interval_minutes=interval_minutes,
                    start_time=chunk_start,
                    end_time=chunk_end
                )

                all_missing.extend(missing_in_chunk)

                # Stop if we've reached 2015
                if chunk_start <= datetime(2015, 1, 1, tzinfo=timezone.utc):
                    break

            gap_detector.close()

            if not all_missing:
                return None, None, "COMPLETE"

            # Sort missing timestamps
            all_missing.sort()

            # Group consecutive missing timestamps into gap periods
            gap_periods = self._group_gap_periods(all_missing, interval_minutes)

            # Return FIRST (oldest) gap to fill
            first_gap = gap_periods[0]

            # Extend end by 1 interval for safety
            gap_end_extended = first_gap['end'] + timedelta(minutes=interval_minutes)

            logger.info(
                f"📊 [GapDetection] {symbol} {timeframe}: Found {len(gap_periods)} gap periods, "
                f"total {len(all_missing)} missing timestamps"
            )

            return first_gap['start'], gap_end_extended, f"GAP_FILL ({len(gap_periods)} gaps, {len(all_missing)} missing)"

        except Exception as e:
            logger.error(f"❌ Error detecting gaps for {symbol} {timeframe}: {e}")
            # Fallback: If error, do incremental from latest
            if coverage['latest']:
                start_date = coverage['latest'] - timedelta(days=1)
                return start_date, None, "INCREMENTAL_FALLBACK"
            else:
                return None, None, "FULL_BACKFILL"

    def detect_gaps_in_range(
        self,
        gap_detector,
        symbol: str,
        timeframe: str,
        interval_minutes: int,
        start_time: datetime,
        end_time: datetime
    ) -> List[datetime]:
        """
        Detect gaps AND data quality issues in specific time range

        Detects TWO types of problems:
        1. Missing rows (timestamp tidak ada)
        2. Incomplete rows (NULL values di OHLCV columns)

        Args:
            gap_detector: GapDetector instance
            symbol: Symbol to check
            timeframe: Timeframe to check
            interval_minutes: Interval in minutes
            start_time: Start of range
            end_time: End of range

        Returns:
            List of missing/incomplete timestamps that need re-aggregation
        """
        try:
            # Query actual timestamps WITH data quality check
            # Only count rows with COMPLETE data (no NULLs in critical columns)
            query = f"""
            SELECT DISTINCT toDateTime(timestamp_ms / 1000) as ts
            FROM aggregates
            WHERE symbol = '{symbol}'
              AND timeframe = '{timeframe}'
              AND source = 'historical_aggregated'
              AND timestamp_ms >= {int(start_time.timestamp() * 1000)}
              AND timestamp_ms < {int(end_time.timestamp() * 1000)}
              AND open IS NOT NULL
              AND high IS NOT NULL
              AND low IS NOT NULL
              AND close IS NOT NULL
              AND volume IS NOT NULL
              AND volume > 0
            ORDER BY ts ASC
            """

            # gap_detector uses clickhouse_driver.Client (native protocol)
            # Method is .execute(), not .query()
            result = gap_detector.client.execute(query)
            complete_timestamps = {row[0] for row in result}

            # Also query ALL existing rows (including incomplete) for logging
            query_all = f"""
            SELECT toDateTime(timestamp_ms / 1000) as ts, open, high, low, close, volume
            FROM aggregates
            WHERE symbol = '{symbol}'
              AND timeframe = '{timeframe}'
              AND source = 'historical_aggregated'
              AND timestamp_ms >= {int(start_time.timestamp() * 1000)}
              AND timestamp_ms < {int(end_time.timestamp() * 1000)}
              AND (open IS NULL OR high IS NULL OR low IS NULL OR close IS NULL OR volume IS NULL OR volume = 0)
            LIMIT 10
            """

            result_incomplete = gap_detector.client.execute(query_all)
            if result_incomplete:
                logger.warning(
                    f"⚠️ Found {len(result_incomplete)} incomplete rows for {symbol} {timeframe} "
                    f"(showing first 10 with NULL values)"
                )
                for row in result_incomplete[:5]:
                    ts, o, h, l, c, v = row
                    logger.warning(f"   - {ts}: open={o}, high={h}, low={l}, close={c}, volume={v}")

            # Generate expected timestamps (excluding weekends)
            expected_timestamps = gap_detector._generate_expected_timestamps(
                start_time, end_time, interval_minutes
            )

            # Find missing OR incomplete (treat both as gaps)
            missing = [ts for ts in expected_timestamps if ts not in complete_timestamps]

            return missing

        except Exception as e:
            logger.error(f"❌ Error detecting gaps in range: {e}")
            return []

    def _group_gap_periods(self, all_missing: List[datetime], interval_minutes: int) -> List[Dict[str, datetime]]:
        """
        Group consecutive missing timestamps into gap periods

        Args:
            all_missing: Sorted list of missing timestamps
            interval_minutes: Interval in minutes

        Returns:
            List of gap periods with 'start' and 'end' keys
        """
        gap_periods = []
        gap_start = all_missing[0]
        gap_end = all_missing[0]

        for i in range(1, len(all_missing)):
            prev_ts = all_missing[i - 1]
            curr_ts = all_missing[i]

            # Expected next timestamp
            expected_next = prev_ts + timedelta(minutes=interval_minutes)

            # Allow small tolerance for timestamp drift
            tolerance = timedelta(minutes=interval_minutes * 0.1)

            if abs(curr_ts - expected_next) <= tolerance:
                # Consecutive, extend gap
                gap_end = curr_ts
            else:
                # Non-consecutive, save current gap
                gap_periods.append({'start': gap_start, 'end': gap_end})
                gap_start = curr_ts
                gap_end = curr_ts

        # Add last gap
        gap_periods.append({'start': gap_start, 'end': gap_end})

        return gap_periods
