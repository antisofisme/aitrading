"""
Gap Fill Verifier
Verifies that downloaded gap data reached ClickHouse after propagating through the pipeline:
Historical Downloader -> NATS -> Tick Aggregator -> Data Bridge -> ClickHouse
"""
import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List, Tuple
from clickhouse_driver import Client

logger = logging.getLogger(__name__)

class GapFillVerifier:
    """Verifies that downloaded gap data reached ClickHouse"""

    def __init__(self, clickhouse_config: Dict[str, Any]):
        """
        Initialize verifier with ClickHouse connection

        Args:
            clickhouse_config: Dict with connection parameters
                - host: ClickHouse host
                - port: Native protocol port (default: 9000)
                - database: Database name
                - user: Username
                - password: Password
        """
        self.clickhouse = Client(
            host=clickhouse_config['host'],
            port=clickhouse_config.get('port', clickhouse_config.get('native_port', 9000)),
            database=clickhouse_config['database'],
            user=clickhouse_config['user'],
            password=clickhouse_config['password']
        )
        logger.info(
            f"GapFillVerifier initialized: {clickhouse_config['host']}:"
            f"{clickhouse_config.get('port', 9000)}/{clickhouse_config['database']}"
        )

    def verify_date_has_data(
        self,
        symbol: str,
        timeframe: str,
        target_date: date,
        min_bars: int = 1
    ) -> bool:
        """
        Verify that ClickHouse has data for a specific date

        Args:
            symbol: Trading pair (e.g., 'XAU/USD')
            timeframe: Timeframe (e.g., '1m', '5m')
            target_date: Date to verify
            min_bars: Minimum number of bars expected

        Returns:
            True if data exists, False otherwise
        """
        query = """
            SELECT count() as cnt
            FROM live_aggregates
            WHERE symbol = %(symbol)s
              AND timeframe = %(timeframe)s
              AND toDate(time) = %(date)s
              AND open IS NOT NULL
              AND high IS NOT NULL
              AND low IS NOT NULL
              AND close IS NOT NULL
        """

        try:
            result = self.clickhouse.execute(
                query,
                {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'date': target_date
                }
            )

            count = result[0][0] if result else 0
            has_data = count >= min_bars

            logger.info(
                f"Verification: {symbol} {timeframe} {target_date} - "
                f"{count} bars (min: {min_bars}) - {'✅ PASS' if has_data else '❌ FAIL'}"
            )

            return has_data

        except Exception as e:
            logger.error(f"Verification failed: {symbol} {timeframe} {target_date} - {e}")
            return False

    async def verify_with_retry(
        self,
        symbol: str,
        timeframe: str,
        target_date: date,
        min_bars: int = 1,
        max_retries: int = 3,
        retry_delay: int = 10
    ) -> bool:
        """
        Verify with retry logic - wait for data to propagate through pipeline

        Pipeline: NATS -> Tick Aggregator -> Data Bridge -> ClickHouse
        Total propagation time: ~30-60 seconds

        Args:
            symbol: Trading pair
            timeframe: Timeframe
            target_date: Date to verify
            min_bars: Minimum bars expected
            max_retries: Maximum retry attempts
            retry_delay: Seconds between retries

        Returns:
            True if verification succeeds within retries
        """
        for attempt in range(1, max_retries + 1):
            logger.info(
                f"Verification attempt {attempt}/{max_retries}: "
                f"{symbol} {timeframe} {target_date}"
            )

            if self.verify_date_has_data(symbol, timeframe, target_date, min_bars):
                logger.info(f"✅ Verification succeeded on attempt {attempt}")
                return True

            if attempt < max_retries:
                logger.warning(
                    f"⏳ Data not found, waiting {retry_delay}s before retry..."
                )
                await asyncio.sleep(retry_delay)

        logger.error(
            f"❌ Verification failed after {max_retries} attempts: "
            f"{symbol} {timeframe} {target_date}"
        )
        return False

    def verify_date_range(
        self,
        symbol: str,
        timeframe: str,
        start_date: date,
        end_date: date,
        min_bars: int = 1
    ) -> Tuple[bool, List[date], List[date]]:
        """
        Verify entire date range has data

        Args:
            symbol: Trading pair
            timeframe: Timeframe
            start_date: Start date
            end_date: End date
            min_bars: Minimum bars per date

        Returns:
            Tuple of (all_verified, verified_dates, failed_dates)
        """
        verified_dates = []
        failed_dates = []

        current_date = start_date
        while current_date <= end_date:
            # Skip weekends (Forex closed)
            if current_date.weekday() < 5:
                if self.verify_date_has_data(symbol, timeframe, current_date, min_bars):
                    verified_dates.append(current_date)
                else:
                    failed_dates.append(current_date)

            current_date += timedelta(days=1)

        all_verified = len(failed_dates) == 0

        logger.info(
            f"Date range verification: {symbol} {timeframe} "
            f"{start_date} to {end_date} - "
            f"Verified: {len(verified_dates)}, Failed: {len(failed_dates)}"
        )

        return all_verified, verified_dates, failed_dates

    async def verify_date_range_with_retry(
        self,
        symbol: str,
        timeframe: str,
        start_date: date,
        end_date: date,
        min_bars: int = 1,
        max_retries: int = 3,
        retry_delay: int = 10
    ) -> Tuple[bool, List[date], List[date]]:
        """
        Verify entire date range with retry logic

        Args:
            symbol: Trading pair
            timeframe: Timeframe
            start_date: Start date
            end_date: End date
            min_bars: Minimum bars per date
            max_retries: Maximum retry attempts per date
            retry_delay: Seconds between retries

        Returns:
            Tuple of (all_verified, verified_dates, failed_dates)
        """
        verified_dates = []
        failed_dates = []

        current_date = start_date
        while current_date <= end_date:
            # Skip weekends (Forex closed)
            if current_date.weekday() < 5:
                verified = await self.verify_with_retry(
                    symbol=symbol,
                    timeframe=timeframe,
                    target_date=current_date,
                    min_bars=min_bars,
                    max_retries=max_retries,
                    retry_delay=retry_delay
                )

                if verified:
                    verified_dates.append(current_date)
                else:
                    failed_dates.append(current_date)

            current_date += timedelta(days=1)

        all_verified = len(failed_dates) == 0

        logger.info(
            f"Date range verification with retry: {symbol} {timeframe} "
            f"{start_date} to {end_date} - "
            f"Verified: {len(verified_dates)}, Failed: {len(failed_dates)}"
        )

        return all_verified, verified_dates, failed_dates

    def get_date_bar_count(
        self,
        symbol: str,
        timeframe: str,
        target_date: date
    ) -> int:
        """
        Get actual bar count for a date

        Args:
            symbol: Trading pair
            timeframe: Timeframe
            target_date: Date to check

        Returns:
            Number of bars found
        """
        query = """
            SELECT count() as cnt
            FROM live_aggregates
            WHERE symbol = %(symbol)s
              AND timeframe = %(timeframe)s
              AND toDate(time) = %(date)s
        """

        try:
            result = self.clickhouse.execute(
                query,
                {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'date': target_date
                }
            )
            return result[0][0] if result else 0
        except Exception as e:
            logger.error(f"Failed to get bar count: {e}")
            return 0

    def get_date_range_stats(
        self,
        symbol: str,
        timeframe: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a date range

        Args:
            symbol: Trading pair
            timeframe: Timeframe
            start_date: Start date
            end_date: End date

        Returns:
            Dict with statistics:
                - total_bars: Total bar count
                - dates_with_data: Number of dates with data
                - dates_expected: Expected trading days
                - min_date: Earliest date with data
                - max_date: Latest date with data
                - avg_bars_per_day: Average bars per trading day
        """
        query = """
            SELECT
                COUNT(*) as total_bars,
                COUNT(DISTINCT toDate(time)) as dates_with_data,
                MIN(time) as min_date,
                MAX(time) as max_date
            FROM live_aggregates
            WHERE symbol = %(symbol)s
              AND timeframe = %(timeframe)s
              AND toDate(time) BETWEEN %(start_date)s AND %(end_date)s
        """

        try:
            result = self.clickhouse.execute(
                query,
                {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'start_date': start_date,
                    'end_date': end_date
                }
            )

            if not result or not result[0]:
                return {
                    'total_bars': 0,
                    'dates_with_data': 0,
                    'dates_expected': 0,
                    'min_date': None,
                    'max_date': None,
                    'avg_bars_per_day': 0
                }

            total_bars, dates_with_data, min_date, max_date = result[0]

            # Calculate expected trading days (Mon-Fri)
            dates_expected = 0
            current = start_date
            while current <= end_date:
                if current.weekday() < 5:
                    dates_expected += 1
                current += timedelta(days=1)

            avg_bars = total_bars / dates_with_data if dates_with_data > 0 else 0

            stats = {
                'total_bars': total_bars,
                'dates_with_data': dates_with_data,
                'dates_expected': dates_expected,
                'min_date': min_date,
                'max_date': max_date,
                'avg_bars_per_day': avg_bars,
                'completeness': dates_with_data / dates_expected if dates_expected > 0 else 0
            }

            logger.info(
                f"Date range stats: {symbol} {timeframe} - "
                f"{total_bars} bars across {dates_with_data}/{dates_expected} dates "
                f"({stats['completeness']*100:.1f}% complete)"
            )

            return stats

        except Exception as e:
            logger.error(f"Failed to get date range stats: {e}")
            return {
                'total_bars': 0,
                'dates_with_data': 0,
                'dates_expected': 0,
                'min_date': None,
                'max_date': None,
                'avg_bars_per_day': 0,
                'completeness': 0
            }
