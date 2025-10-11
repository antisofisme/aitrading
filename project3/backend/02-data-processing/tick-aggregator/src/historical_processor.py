"""
Historical Processor - Aggregate ClickHouse 1m bars to higher timeframes
Runs every 6 hours to check and aggregate new historical data
"""
import logging
from typing import List, Dict, Any
from datetime import datetime, timezone

from historical_aggregator import HistoricalAggregator

logger = logging.getLogger(__name__)


class HistoricalProcessor:
    """
    Historical data aggregation processor

    Priority: MEDIUM
    Trigger: Every 6 hours
    Source: ClickHouse.aggregates (1m bars, source='polygon_historical')
    Destination: ClickHouse.aggregates (source='historical_aggregated')

    Flow:
    1. Check each symbol for missing timeframes
    2. Aggregate 1m → 5m, 15m, 30m, 1h, 4h, 1d, 1w
    3. Calculate technical indicators
    4. Insert with source='historical_aggregated'
    5. Deduplication: Skip if live_aggregated already exists
    """

    def __init__(
        self,
        historical_aggregator: HistoricalAggregator,
        symbols: List[str]
    ):
        """
        Initialize historical processor

        Args:
            historical_aggregator: Historical aggregator instance
            symbols: List of symbols to process
        """
        self.historical_aggregator = historical_aggregator
        self.symbols = symbols

        # Target timeframes (exclude 1m - source data)
        self.target_timeframes = [
            {'name': '5m', 'interval_minutes': 5},
            {'name': '15m', 'interval_minutes': 15},
            {'name': '30m', 'interval_minutes': 30},
            {'name': '1h', 'interval_minutes': 60},
            {'name': '4h', 'interval_minutes': 240},
            {'name': '1d', 'interval_minutes': 1440},
            {'name': '1w', 'interval_minutes': 10080}
        ]

        # Statistics
        self.total_runs = 0
        self.total_symbols_processed = 0
        self.total_candles_generated = 0
        self.total_errors = 0
        self.last_run_time = None
        self.last_run_status = "not_started"

        logger.info("✅ HistoricalProcessor initialized")

    async def process(self):
        """
        Main processing routine - called by cron every 6 hours

        Steps:
        1. Check each symbol for 1m data
        2. Check if higher timeframes already exist
        3. Aggregate missing timeframes
        4. Skip if live_aggregated data exists (deduplication)
        """
        try:
            self.total_runs += 1
            self.last_run_time = datetime.now(timezone.utc)
            self.last_run_status = "running"

            logger.info(f"🔄 [HistoricalProcessor] Run #{self.total_runs} started")

            symbols_processed = 0
            candles_generated = 0

            for symbol in self.symbols:
                try:
                    # Check if 1m historical data exists
                    m1_count = self._check_1m_data(symbol)

                    if m1_count == 0:
                        logger.debug(f"⏭️  [HistoricalProcessor] {symbol}: No 1m data, skip")
                        continue

                    # Process each target timeframe
                    for tf_config in self.target_timeframes:
                        timeframe = tf_config['name']
                        interval_minutes = tf_config['interval_minutes']

                        # Check if timeframe already has data
                        existing_count = self._check_existing_data(symbol, timeframe)

                        # Skip if already has significant data (>1000 candles)
                        if existing_count >= 1000:
                            logger.debug(
                                f"⏭️  [HistoricalProcessor] {symbol} {timeframe}: "
                                f"{existing_count} candles exist, skip"
                            )
                            continue

                        # Aggregate 1m → timeframe
                        logger.info(
                            f"📊 [HistoricalProcessor] {symbol} {timeframe}: "
                            f"Aggregating from {m1_count:,} 1m bars..."
                        )

                        try:
                            count = self.historical_aggregator.aggregate_symbol_timeframe(
                                symbol=symbol,
                                target_timeframe=timeframe,
                                interval_minutes=interval_minutes
                            )

                            candles_generated += count
                            logger.info(
                                f"✅ [HistoricalProcessor] {symbol} {timeframe}: "
                                f"{count:,} candles generated"
                            )

                        except Exception as agg_err:
                            self.total_errors += 1
                            logger.error(
                                f"❌ [HistoricalProcessor] {symbol} {timeframe} failed: {agg_err}"
                            )

                    symbols_processed += 1

                except Exception as symbol_err:
                    self.total_errors += 1
                    logger.error(f"❌ [HistoricalProcessor] {symbol} failed: {symbol_err}")

            self.total_symbols_processed += symbols_processed
            self.total_candles_generated += candles_generated
            self.last_run_status = "success"

            logger.info(
                f"✅ [HistoricalProcessor] Run #{self.total_runs} complete: "
                f"{symbols_processed} symbols, {candles_generated:,} candles"
            )

        except Exception as e:
            self.total_errors += 1
            self.last_run_status = "error"
            logger.error(f"❌ [HistoricalProcessor] Error in run #{self.total_runs}: {e}", exc_info=True)

    def _check_1m_data(self, symbol: str) -> int:
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
            result = self.historical_aggregator.client.query(query)
            return result.result_rows[0][0] if result.result_rows else 0

        except Exception as e:
            logger.error(f"❌ Error checking 1m data for {symbol}: {e}")
            return 0

    def _check_existing_data(self, symbol: str, timeframe: str) -> int:
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
            result = self.historical_aggregator.client.query(query)
            return result.result_rows[0][0] if result.result_rows else 0

        except Exception as e:
            logger.error(f"❌ Error checking existing data for {symbol} {timeframe}: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """Get processor statistics"""
        return {
            'component': 'historical_processor',
            'priority': 'MEDIUM',
            'total_runs': self.total_runs,
            'total_symbols_processed': self.total_symbols_processed,
            'total_candles_generated': self.total_candles_generated,
            'total_errors': self.total_errors,
            'last_run_time': self.last_run_time.isoformat() if self.last_run_time else None,
            'last_run_status': self.last_run_status
        }
