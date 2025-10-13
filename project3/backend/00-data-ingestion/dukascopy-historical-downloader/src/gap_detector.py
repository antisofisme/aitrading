"""
Gap Detection for Dukascopy Historical Data
Identifies missing dates in ClickHouse aggregates table
"""
import logging
from datetime import datetime, timedelta
from typing import List, Set
from clickhouse_driver import Client as ClickHouseClient

logger = logging.getLogger(__name__)


class GapDetector:
    """
    Detects missing dates in historical tick data

    Queries ClickHouse market_ticks table to find:
    - Missing dates (no tick data at all)
    - Weekends are automatically excluded
    """

    def __init__(self, clickhouse_config: dict):
        """
        Args:
            clickhouse_config: ClickHouse connection config
                Must include 'table' key (e.g., 'market_ticks')
        """
        self.config = clickhouse_config
        self.client: ClickHouseClient = None

    def connect(self):
        """Connect to ClickHouse"""
        try:
            self.client = ClickHouseClient(
                host=self.config['host'],
                port=self.config['port'],
                user=self.config['user'],
                password=self.config['password'],
                database=self.config['database']
            )
            logger.info(f"✅ Connected to ClickHouse: {self.config['host']}:{self.config['port']}")
        except Exception as e:
            logger.error(f"❌ ClickHouse connection failed: {e}")
            raise

    def get_date_range_gaps(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        source: str = 'dukascopy_historical'
    ) -> List[str]:
        """
        Find missing dates within a date range (for tick data)

        Args:
            symbol: Trading pair (e.g., 'EUR/USD')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            source: Data source filter (ignored - ClickHouse ticks table has no source column)

        Returns:
            List of missing dates (YYYY-MM-DD)
        """
        if not self.client:
            self.connect()

        # Query: Get all dates with tick data
        # Note: ClickHouse ticks table doesn't have 'source' or 'timeframe' columns
        query = f"""
        SELECT DISTINCT toDate(timestamp) as date
        FROM {self.config['database']}.{self.config['table']}
        WHERE symbol = %(symbol)s
          AND toDate(timestamp) BETWEEN %(start_date)s AND %(end_date)s
        ORDER BY date
        """

        try:
            result = self.client.execute(
                query,
                {
                    'symbol': symbol,
                    'start_date': start_date,
                    'end_date': end_date
                }
            )

            # Extract dates from result
            existing_dates = set(row[0].strftime('%Y-%m-%d') for row in result)

            # Generate expected date range (exclude weekends)
            expected_dates = self._generate_expected_dates(start_date, end_date)

            # Find missing dates
            missing_dates = sorted(expected_dates - existing_dates)

            logger.info(
                f"Gap detection: {symbol} {start_date} to {end_date} - "
                f"{len(missing_dates)} missing dates out of {len(expected_dates)} expected"
            )

            return missing_dates

        except Exception as e:
            logger.error(f"❌ Gap detection query failed: {e}")
            return []

    def _generate_expected_dates(self, start_date: str, end_date: str) -> Set[str]:
        """
        Generate set of expected trading dates (Mon-Fri only)

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Set of date strings (YYYY-MM-DD)
        """
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        expected = set()
        current = start

        while current <= end:
            # Only include weekdays (Mon-Fri)
            if current.weekday() < 5:
                expected.add(current.strftime('%Y-%m-%d'))
            current += timedelta(days=1)

        return expected

    def close(self):
        """Close ClickHouse connection"""
        if self.client:
            self.client.disconnect()
            logger.info("✅ ClickHouse connection closed")
