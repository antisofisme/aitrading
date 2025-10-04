"""
Gap Detection for Historical Data
Detects missing data and triggers backfill
"""
import logging
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from clickhouse_driver import Client

logger = logging.getLogger(__name__)

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
                SELECT timestamp
                FROM {self.config.get('table', 'ticks')}
                WHERE symbol = %(symbol)s
                  AND timestamp >= now() - INTERVAL {days} DAY
                ORDER BY timestamp ASC
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

    def get_date_range_gaps(self, symbol: str, start_date: str, end_date: str) -> List[str]:
        """
        Get missing dates in a range

        Returns: List of missing dates (YYYY-MM-DD)
        """
        try:
            query = f"""
                SELECT DISTINCT toDate(timestamp) as date
                FROM {self.config.get('table', 'ticks')}
                WHERE symbol = %(symbol)s
                  AND toDate(timestamp) BETWEEN %(start_date)s AND %(end_date)s
                ORDER BY date ASC
            """

            result = self.client.execute(query, {
                'symbol': symbol,
                'start_date': start_date,
                'end_date': end_date
            })

            existing_dates = {row[0] for row in result}

            # Generate expected dates
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')

            expected_dates = set()
            current = start
            while current <= end:
                # Skip weekends (Forex closed)
                if current.weekday() < 5:
                    expected_dates.add(current.date())
                current += timedelta(days=1)

            # Find missing
            missing_dates = expected_dates - existing_dates

            return sorted([d.strftime('%Y-%m-%d') for d in missing_dates])

        except Exception as e:
            logger.error(f"Error getting date range gaps for {symbol}: {e}")
            return []
