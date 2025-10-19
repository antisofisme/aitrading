"""
Gap Detection for Historical Data
Detects missing data and triggers backfill
"""
import logging
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from clickhouse_driver import Client
import sys
import os
import pytz

# Add shared components to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from shared.components.utils.data_validator import DataValidator

logger = logging.getLogger(__name__)

# Forex Market Hours Constants
FOREX_OPEN_DAY = 6       # Sunday
FOREX_OPEN_HOUR = 17     # 5 PM EST
FOREX_CLOSE_DAY = 4      # Friday
FOREX_CLOSE_HOUR = 17    # 5 PM EST
EST = pytz.timezone('America/New_York')  # US Eastern Time (handles EDT/EST automatically)

# Timeframe-specific threshold configuration
INTRADAY_TIMEFRAMES = ['5m', '15m', '30m', '1h', '4h']
DAILY_PLUS_TIMEFRAMES = ['1d', '1w']

INTRADAY_THRESHOLD = 1.0  # 100% - expect all bars (any missing = incomplete)
DAILY_THRESHOLD = 0.8     # 80% - weekends/holidays OK (20% missing allowed)


def is_forex_market_open(dt: datetime) -> bool:
    """
    Check if forex market is open at given time

    Forex Market Hours:
    - Opens: Sunday 17:00 EST (5 PM Eastern)
    - Closes: Friday 17:00 EST (5 PM Eastern)
    - Market CLOSED: Friday 17:00 - Sunday 17:00 EST
    - Market OPEN: Sunday 17:00 - Friday 17:00 EST

    Args:
        dt: Timezone-aware datetime (preferably UTC or EST)

    Returns:
        True if market is open, False if closed

    Examples:
        >>> # Friday 16:59 EST - Market OPEN
        >>> dt = EST.localize(datetime(2025, 10, 10, 16, 59))
        >>> is_forex_market_open(dt)
        True

        >>> # Friday 17:00 EST - Market CLOSED
        >>> dt = EST.localize(datetime(2025, 10, 10, 17, 0))
        >>> is_forex_market_open(dt)
        False

        >>> # Sunday 16:59 EST - Market CLOSED
        >>> dt = EST.localize(datetime(2025, 10, 12, 16, 59))
        >>> is_forex_market_open(dt)
        False

        >>> # Sunday 17:00 EST - Market OPEN
        >>> dt = EST.localize(datetime(2025, 10, 12, 17, 0))
        >>> is_forex_market_open(dt)
        True
    """
    # Convert to EST for consistency
    if dt.tzinfo is None:
        # Assume UTC if naive
        dt = pytz.UTC.localize(dt)

    dt_est = dt.astimezone(EST)

    weekday = dt_est.weekday()  # Monday=0, Sunday=6
    hour = dt_est.hour

    # Monday-Thursday: Always open
    if 0 <= weekday <= 3:
        logger.debug(f"Market OPEN: {dt_est} (weekday={weekday}, Mon-Thu)")
        return True

    # Friday: Open until 17:00 EST
    if weekday == FOREX_CLOSE_DAY:
        is_open = hour < FOREX_CLOSE_HOUR
        logger.debug(
            f"Market {'OPEN' if is_open else 'CLOSED'}: {dt_est} "
            f"(Friday, hour={hour}, close_hour={FOREX_CLOSE_HOUR})"
        )
        return is_open

    # Sunday: Open from 17:00 EST onwards
    if weekday == FOREX_OPEN_DAY:
        is_open = hour >= FOREX_OPEN_HOUR
        logger.debug(
            f"Market {'OPEN' if is_open else 'CLOSED'}: {dt_est} "
            f"(Sunday, hour={hour}, open_hour={FOREX_OPEN_HOUR})"
        )
        return is_open

    # Saturday: Always closed
    logger.debug(f"Market CLOSED: {dt_est} (Saturday)")
    return False


class GapDetector:
    def __init__(self, clickhouse_config: dict):
        self.config = clickhouse_config
        self.client = Client(
            host=clickhouse_config.get('host', 'suho-clickhouse'),
            port=clickhouse_config.get('port', 9000),
            user=clickhouse_config.get('user', 'suho_analytics'),
            password=clickhouse_config['password'],
            database=clickhouse_config.get('database', 'suho_analytics')
        )

    def detect_gaps(self, symbol: str, days: int = 7, max_gap_minutes: int = 60) -> List[Tuple[datetime, datetime]]:
        """
        Detect gaps in tick data

        Returns: List of (gap_start, gap_end) tuples
        """
        try:
            # Query for timestamps
            query = f"""
                SELECT time
                FROM {self.config.get('table', 'live_aggregates')}
                WHERE symbol = %(symbol)s
                  AND time >= now() - INTERVAL {days} DAY
                ORDER BY time ASC
            """

            result = self.client.execute(query, {'symbol': symbol})

            if not result:
                logger.warning(f"No data found for {symbol}")
                return []

            # Find gaps
            gaps = []
            for i in range(1, len(result)):
                prev_time = result[i-1][0]
                curr_time = result[i][0]

                gap_minutes = (curr_time - prev_time).total_seconds() / 60

                if gap_minutes > max_gap_minutes:
                    gaps.append((prev_time, curr_time))
                    logger.warning(f"Gap detected in {symbol}: {prev_time} -> {curr_time} ({gap_minutes:.1f} min)")

            return gaps

        except Exception as e:
            logger.error(f"Error detecting gaps for {symbol}: {e}")
            return []

    def get_date_range_gaps(self, symbol: str, start_date: str, end_date: str, timeframe: str = '1m') -> List[str]:
        """
        Get missing dates in a range

        Also checks for data quality issues (NULL values in OHLC)

        Args:
            symbol: Trading pair symbol (e.g., 'EURUSD', 'XAUUSD')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            timeframe: Timeframe to check (default: '1m', can be '5m', '15m', '1h', etc.)

        Returns: List of missing dates (YYYY-MM-DD)
        """
        try:
            # Query dates with COMPLETE data (no NULLs in OHLC)
            # Using centralized DataValidator for consistent validation
            # Note: live_aggregates uses tick_count, not volume - use include_volume=False
            query = f"""
                SELECT DISTINCT toDate(time) as date
                FROM {self.config.get('table', 'live_aggregates')}
                WHERE symbol = %(symbol)s
                  AND toDate(time) BETWEEN %(start_date)s AND %(end_date)s
                  AND timeframe = %(timeframe)s
                  AND {DataValidator.validate_ohlcv_sql_clause(include_volume=False)}
                ORDER BY date ASC
            """

            result = self.client.execute(query, {
                'symbol': symbol,
                'start_date': start_date,
                'end_date': end_date,
                'timeframe': timeframe
            })

            # Dates with complete, valid data
            complete_dates = {row[0] for row in result}

            # Also check for dates with NULL/invalid data
            # Using inverted validation to find BAD data
            quality_check_query = f"""
                SELECT DISTINCT toDate(time) as date, COUNT(*) as bad_count
                FROM {self.config.get('table', 'live_aggregates')}
                WHERE symbol = %(symbol)s
                  AND toDate(time) BETWEEN %(start_date)s AND %(end_date)s
                  AND timeframe = %(timeframe)s
                  AND NOT ({DataValidator.validate_ohlcv_sql_clause(include_volume=False)})
                GROUP BY date
                ORDER BY date ASC
            """

            quality_result = self.client.execute(quality_check_query, {
                'symbol': symbol,
                'start_date': start_date,
                'end_date': end_date,
                'timeframe': timeframe
            })

            if quality_result:
                logger.warning(
                    f"⚠️ [DataQuality] {symbol}: Found {len(quality_result)} dates with NULL/invalid OHLC data"
                )
                for row in quality_result[:5]:
                    date, bad_count = row
                    logger.warning(f"   - {date}: {bad_count} bars with invalid data")

            # Generate expected dates (timezone-aware)
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')

            # Make timezone-aware (assume UTC)
            start = pytz.UTC.localize(start)
            end = pytz.UTC.localize(end)

            expected_dates = set()
            current = start
            while current <= end:
                # Use timezone-aware forex market hours check
                if is_forex_market_open(current):
                    expected_dates.add(current.date())
                current += timedelta(days=1)

            # Find missing OR dates with bad data
            missing_dates = expected_dates - complete_dates

            if missing_dates:
                logger.info(
                    f"📊 [GapDetection] {symbol}: Found {len(missing_dates)} dates with missing or invalid data"
                )

            return sorted([d.strftime('%Y-%m-%d') for d in missing_dates])

        except Exception as e:
            logger.error(f"❌ Error getting date range gaps for {symbol}: {e}")
            return []

    def check_period_completeness(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        timeframe: str
    ) -> Tuple[bool, float, int, int]:
        """
        Check if a period has complete data based on timeframe-specific thresholds

        Intraday timeframes (5m, 15m, 30m, 1h, 4h): 100% threshold - ANY missing = incomplete
        Daily+ timeframes (1d, 1w): 80% threshold - weekends/holidays tolerated

        Args:
            symbol: Trading pair symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            timeframe: Timeframe (e.g., '5m', '1h', '1d')

        Returns:
            (is_complete, completeness_ratio, bars_found, bars_expected)
        """
        try:
            # Determine threshold based on timeframe
            if timeframe in INTRADAY_TIMEFRAMES:
                threshold = INTRADAY_THRESHOLD
                logger.debug(f"Using intraday threshold: {threshold*100}% for {timeframe}")
            else:
                threshold = DAILY_THRESHOLD
                logger.debug(f"Using daily+ threshold: {threshold*100}% for {timeframe}")

            # Calculate expected bar count based on timeframe
            bars_expected = self._calculate_expected_bars(start_date, end_date, timeframe)

            # Query actual bar count
            # Using centralized DataValidator for consistent validation
            query = f"""
                SELECT COUNT(*) as count
                FROM {self.config.get('table', 'live_aggregates')}
                WHERE symbol = %(symbol)s
                  AND toDate(time) BETWEEN %(start_date)s AND %(end_date)s
                  AND timeframe = %(timeframe)s
                  AND {DataValidator.validate_ohlcv_sql_clause(include_volume=False)}
            """

            result = self.client.execute(query, {
                'symbol': symbol,
                'start_date': start_date,
                'end_date': end_date,
                'timeframe': timeframe
            })

            bars_found = result[0][0] if result else 0

            # Calculate completeness ratio
            completeness = bars_found / bars_expected if bars_expected > 0 else 0.0

            # Determine if complete based on threshold
            is_complete = completeness >= threshold

            logger.info(
                f"📊 Completeness Check - {symbol} {timeframe}: "
                f"{bars_found}/{bars_expected} bars ({completeness*100:.1f}%) "
                f"- Threshold: {threshold*100}% - Status: {'COMPLETE' if is_complete else 'INCOMPLETE'}"
            )

            return is_complete, completeness, bars_found, bars_expected

        except Exception as e:
            logger.error(f"❌ Error checking period completeness for {symbol}: {e}")
            # On error, assume incomplete to trigger re-download
            return False, 0.0, 0, 0

    def _calculate_expected_bars(self, start_date: str, end_date: str, timeframe: str) -> int:
        """
        Calculate expected number of bars for a date range and timeframe

        Accounts for:
        - Forex market hours (24/5 - closed weekends, timezone-aware)
        - Timeframe intervals
        - Holidays (approximate)

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            timeframe: Timeframe (e.g., '5m', '1h', '1d')

        Returns:
            Expected number of bars
        """
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')

            # Make timezone-aware
            start = pytz.UTC.localize(start)
            end = pytz.UTC.localize(end)

            # Count trading days (timezone-aware forex market hours)
            trading_days = 0
            current = start
            while current <= end:
                if is_forex_market_open(current):
                    trading_days += 1
                current += timedelta(days=1)

            # Calculate bars per day based on timeframe
            if timeframe == '5m':
                # Forex: 24 hours * 60 min / 5 min = 288 bars per day
                bars_per_day = 288
            elif timeframe == '15m':
                # 24 hours * 60 min / 15 min = 96 bars per day
                bars_per_day = 96
            elif timeframe == '30m':
                # 24 hours * 60 min / 30 min = 48 bars per day
                bars_per_day = 48
            elif timeframe == '1h':
                # 24 hours = 24 bars per day
                bars_per_day = 24
            elif timeframe == '4h':
                # 24 hours / 4 = 6 bars per day
                bars_per_day = 6
            elif timeframe == '1d':
                # 1 bar per day
                bars_per_day = 1
            elif timeframe == '1w':
                # 1 bar per week (5 trading days)
                return trading_days // 5
            else:
                logger.warning(f"Unknown timeframe {timeframe}, assuming 1 bar per day")
                bars_per_day = 1

            expected_bars = trading_days * bars_per_day

            logger.debug(
                f"Expected bars calculation: {trading_days} trading days * "
                f"{bars_per_day} bars/day = {expected_bars} bars for {timeframe}"
            )

            return expected_bars

        except Exception as e:
            logger.error(f"Error calculating expected bars: {e}")
            return 0
