"""
Gap Detector - Detects missing candles in ClickHouse
Checks for recent data gaps and triggers re-aggregation
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from clickhouse_driver import Client

logger = logging.getLogger(__name__)


class GapDetector:
    """
    Detects missing candles in ClickHouse aggregates table

    Strategy:
    1. Query actual candles from ClickHouse for recent period
    2. Generate expected candle timestamps based on timeframe
    3. Find gaps (expected - actual)
    4. Return list of missing timestamps for re-aggregation
    """

    def __init__(self, clickhouse_config: Dict[str, Any]):
        """
        Initialize gap detector with ClickHouse connection

        Args:
            clickhouse_config: ClickHouse connection config
        """
        self.config = clickhouse_config
        self.client: Optional[Client] = None

        # Gap detection settings
        self.max_gap_check_hours = 72  # Check last 3 days for gaps

    def connect(self):
        """Connect to ClickHouse"""
        try:
            self.client = Client(
                host=self.config['host'],
                port=self.config.get('port', 9000),
                database=self.config.get('database', 'suho_analytics'),
                user=self.config.get('user', 'suho_analytics'),
                password=self.config.get('password', ''),
                settings={'use_numpy': False}
            )

            # Test connection
            self.client.execute('SELECT 1')
            logger.info(f"✅ Gap Detector connected to ClickHouse: {self.config['host']}")

        except Exception as e:
            logger.error(f"❌ Failed to connect to ClickHouse for gap detection: {e}")
            raise

    def detect_recent_gaps(
        self,
        symbol: str,
        timeframe: str,
        interval_minutes: int,
        lookback_hours: int = 24
    ) -> List[datetime]:
        """
        Detect missing candles for a symbol/timeframe in recent period

        Args:
            symbol: Trading pair (e.g., 'XAU/USD')
            timeframe: Timeframe name (e.g., '1d')
            interval_minutes: Candle interval in minutes (e.g., 1440 for 1d)
            lookback_hours: How far back to check (default: 24 hours)

        Returns:
            List of missing candle timestamps
        """
        if not self.client:
            logger.warning("⚠️ ClickHouse not connected, skipping gap detection")
            return []

        try:
            # Time window for gap check
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=lookback_hours)

            # Query actual candles from ClickHouse
            query = """
                SELECT DISTINCT toDateTime(timestamp) as ts
                FROM aggregates
                WHERE symbol = %(symbol)s
                  AND timeframe = %(timeframe)s
                  AND timestamp >= %(start_time)s
                  AND timestamp < %(end_time)s
                ORDER BY ts ASC
            """

            rows = self.client.execute(
                query,
                {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'start_time': start_time,
                    'end_time': end_time
                }
            )

            actual_timestamps = [row[0] for row in rows]

            # Generate expected timestamps
            expected_timestamps = self._generate_expected_timestamps(
                start_time,
                end_time,
                interval_minutes
            )

            # Find gaps (expected but not in actual)
            missing = []
            for expected_ts in expected_timestamps:
                if expected_ts not in actual_timestamps:
                    missing.append(expected_ts)

            if missing:
                logger.warning(
                    f"⚠️ Gap detected for {symbol} {timeframe}: "
                    f"{len(missing)} missing candles in last {lookback_hours}h"
                )
                for ts in missing[:5]:  # Log first 5
                    logger.warning(f"   - Missing: {ts}")
                if len(missing) > 5:
                    logger.warning(f"   ... and {len(missing) - 5} more")
            else:
                logger.debug(
                    f"✅ No gaps detected for {symbol} {timeframe} "
                    f"(last {lookback_hours}h)"
                )

            return missing

        except Exception as e:
            logger.error(
                f"❌ Error detecting gaps for {symbol} {timeframe}: {e}",
                exc_info=True
            )
            return []

    def _generate_expected_timestamps(
        self,
        start_time: datetime,
        end_time: datetime,
        interval_minutes: int
    ) -> List[datetime]:
        """
        Generate expected candle timestamps based on interval

        Args:
            start_time: Start of period
            end_time: End of period
            interval_minutes: Candle interval

        Returns:
            List of expected candle start times
        """
        expected = []
        current = self._floor_timestamp(start_time, interval_minutes)

        while current < end_time:
            # Only include timestamps in the past (not future candles)
            if current <= datetime.utcnow():
                expected.append(current)
            current += timedelta(minutes=interval_minutes)

        return expected

    def _floor_timestamp(self, dt: datetime, interval_minutes: int) -> datetime:
        """
        Floor timestamp to nearest interval boundary

        Examples:
            - 1d (1440 min): Floor to 00:00 UTC
            - 1h (60 min): Floor to xx:00
            - 5m (5 min): Floor to xx:x5

        Args:
            dt: Input datetime
            interval_minutes: Interval in minutes

        Returns:
            Floored datetime
        """
        if interval_minutes >= 1440:  # Daily or longer
            # Floor to midnight UTC
            return dt.replace(hour=0, minute=0, second=0, microsecond=0)

        elif interval_minutes >= 60:  # Hourly
            # Floor to hour boundary
            return dt.replace(minute=0, second=0, microsecond=0)

        else:  # Intraday (5m, 15m, 30m)
            # Floor to nearest interval
            total_minutes = dt.hour * 60 + dt.minute
            floored_minutes = (total_minutes // interval_minutes) * interval_minutes

            hour = floored_minutes // 60
            minute = floored_minutes % 60

            return dt.replace(hour=hour, minute=minute, second=0, microsecond=0)

    def close(self):
        """Close ClickHouse connection"""
        if self.client:
            self.client.disconnect()
            logger.info("✅ Gap Detector disconnected from ClickHouse")
