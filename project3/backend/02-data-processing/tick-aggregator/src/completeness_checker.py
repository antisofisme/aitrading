"""
Completeness Checker - Validate data quality and completeness

This module handles:
- 1m source data validation
- Data completeness checking
- Quality verification before aggregation
- Coverage calculation
"""
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


class CompletenessChecker:
    """
    Validates data completeness and quality

    Responsibilities:
    - Check if 1m historical data exists
    - Check if aggregated data already exists
    - Validate 1m data completeness (no gaps)
    - Ensure data quality before aggregation
    """

    def __init__(self, clickhouse_client, clickhouse_config):
        """
        Initialize completeness checker

        Args:
            clickhouse_client: ClickHouse client instance
            clickhouse_config: ClickHouse configuration dict
        """
        self.client = clickhouse_client
        self.clickhouse_config = clickhouse_config
        logger.debug("✅ CompletenessChecker initialized")

    def check_1m_data(self, symbol: str) -> int:
        """
        Check if 1m historical data exists for symbol

        Args:
            symbol: Symbol to check

        Returns:
            Count of 1m bars
        """
        try:
            query = f"""
            SELECT COUNT(*) as count
            FROM aggregates
            WHERE symbol = '{symbol}'
              AND timeframe = '1m'
              AND source = 'polygon_historical'
            """
            result = self.client.query(query)
            return result.result_rows[0][0] if result.result_rows else 0

        except Exception as e:
            logger.error(f"❌ Error checking 1m data for {symbol}: {e}")
            return 0

    def check_existing_data(self, symbol: str, timeframe: str) -> int:
        """
        Check if historical aggregated data already exists

        Args:
            symbol: Symbol to check
            timeframe: Timeframe to check

        Returns:
            Count of existing candles
        """
        try:
            query = f"""
            SELECT COUNT(*) as count
            FROM aggregates
            WHERE symbol = '{symbol}'
              AND timeframe = '{timeframe}'
              AND source = 'historical_aggregated'
            """
            result = self.client.query(query)
            return result.result_rows[0][0] if result.result_rows else 0

        except Exception as e:
            logger.error(f"❌ Error checking existing data for {symbol} {timeframe}: {e}")
            return 0

    def validate_source_1m_complete(
        self,
        symbol: str,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> bool:
        """
        Validate that source 1m data is complete (no gaps) before aggregating

        CRITICAL: Don't aggregate if source 1m has gaps → results akan invalid!
        Wait until historical-downloader or live-collector fills 1m gaps first.

        Args:
            symbol: Trading pair
            start_date: Start of aggregation range (None = from earliest)
            end_date: End of aggregation range (None = until now)

        Returns:
            True if 1m data is complete (no gaps), False if gaps detected
        """
        try:
            from gap_detector import GapDetector

            # Determine date range to check
            if not start_date:
                # Get earliest 1m data
                query = f"""
                SELECT MIN(timestamp) as earliest
                FROM aggregates
                WHERE symbol = '{symbol}'
                  AND timeframe = '1m'
                  AND source = 'polygon_historical'
                """
                result = self.client.query(query)
                if result.result_rows and result.result_rows[0][0]:
                    start_date = result.result_rows[0][0]
                else:
                    logger.warning(f"⚠️ No 1m data found for {symbol}")
                    return False

            if not end_date:
                end_date = datetime.now(timezone.utc)

            # Use gap_detector to check for gaps in 1m data
            gap_detector = GapDetector(self.clickhouse_config)
            gap_detector.connect()

            # Check in chunks (max 90 days per query to avoid timeout)
            current_start = start_date
            has_gaps = False

            while current_start < end_date:
                chunk_end = min(current_start + timedelta(days=90), end_date)

                # Query 1m timestamps in this chunk
                query = f"""
                SELECT DISTINCT toDateTime(timestamp_ms / 1000) as ts
                FROM aggregates
                WHERE symbol = '{symbol}'
                  AND timeframe = '1m'
                  AND source = 'polygon_historical'
                  AND timestamp_ms >= {int(current_start.timestamp() * 1000)}
                  AND timestamp_ms < {int(chunk_end.timestamp() * 1000)}
                  AND open IS NOT NULL
                  AND high IS NOT NULL
                  AND low IS NOT NULL
                  AND close IS NOT NULL
                  AND volume IS NOT NULL
                ORDER BY ts ASC
                """

                # Use .execute() for clickhouse_driver.Client
                result = gap_detector.client.execute(query)
                actual_timestamps = {row[0] for row in result}

                # Generate expected 1m timestamps (excluding weekends)
                expected_timestamps = gap_detector._generate_expected_timestamps(
                    current_start, chunk_end, interval_minutes=1
                )

                # Find gaps
                missing = [ts for ts in expected_timestamps if ts not in actual_timestamps]

                if missing:
                    has_gaps = True
                    logger.warning(
                        f"⚠️ [1m Validation] {symbol}: Found {len(missing)} gaps in 1m data "
                        f"({current_start.date()} to {chunk_end.date()})"
                    )
                    # Log first few gaps
                    for ts in missing[:3]:
                        logger.warning(f"   - Missing 1m: {ts}")
                    break  # No need to check further

                current_start = chunk_end

            gap_detector.close()

            if has_gaps:
                logger.warning(
                    f"⚠️ [1m Validation] {symbol}: Source 1m data incomplete. "
                    f"Wait for historical-downloader or live-collector to fill gaps."
                )
                return False

            logger.debug(f"✅ [1m Validation] {symbol}: Source 1m data complete, safe to aggregate")
            return True

        except Exception as e:
            logger.error(f"❌ Error validating 1m source data for {symbol}: {e}")
            # On error, be conservative: don't aggregate
            return False

    def calculate_coverage_percentage(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """
        Calculate coverage percentage for a date range

        Args:
            symbol: Symbol to check
            timeframe: Timeframe to check
            start_date: Start of range
            end_date: End of range

        Returns:
            Coverage percentage (0.0 to 100.0)
        """
        try:
            from gap_detector import GapDetector

            # Get interval minutes
            interval_map = {
                '1m': 1, '5m': 5, '15m': 15, '30m': 30, '1h': 60,
                '4h': 240, '1d': 1440, '1w': 10080
            }
            interval_minutes = interval_map.get(timeframe, 5)

            # Use gap detector to generate expected timestamps
            gap_detector = GapDetector(self.clickhouse_config)
            expected_timestamps = gap_detector._generate_expected_timestamps(
                start_date, end_date, interval_minutes
            )
            expected_count = len(expected_timestamps)

            if expected_count == 0:
                return 100.0

            # Get actual count
            actual_count = self.check_existing_data(symbol, timeframe)

            # Calculate percentage
            coverage = (actual_count / expected_count) * 100
            return min(coverage, 100.0)

        except Exception as e:
            logger.error(f"❌ Error calculating coverage for {symbol} {timeframe}: {e}")
            return 0.0
