"""
Historical Processor - Aggregate ClickHouse 1m bars to higher timeframes
Runs every 6 hours to check and aggregate new historical data
"""
import gc
import os
import logging
from typing import List, Dict, Any
from datetime import datetime, timezone

import psutil

from historical_aggregator import HistoricalAggregator
from gap_analyzer import GapAnalyzer
from completeness_checker import CompletenessChecker
from batch_aggregator import BatchAggregator

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

        # Initialize helper modules
        self.gap_analyzer = GapAnalyzer(
            historical_aggregator.client,
            historical_aggregator.clickhouse_config
        )
        self.completeness_checker = CompletenessChecker(
            historical_aggregator.client,
            historical_aggregator.clickhouse_config
        )
        self.batch_aggregator = BatchAggregator(
            historical_aggregator,
            self._get_memory_usage_mb
        )

        # Statistics
        self.total_runs = 0
        self.total_symbols_processed = 0
        self.total_candles_generated = 0
        self.total_errors = 0
        self.last_run_time = None
        self.last_run_status = "not_started"

        logger.info("✅ HistoricalProcessor initialized")

    def _get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB"""
        try:
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024
        except Exception as e:
            logger.warning(f"Failed to get memory usage: {e}")
            return 0.0

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
            symbol_count = 0

            for symbol in self.symbols:
                symbol_count += 1

                # Track memory before processing symbol
                mem_before_symbol = self._get_memory_usage_mb()
                try:
                    # Check if 1m historical data exists
                    m1_count = self.completeness_checker.check_1m_data(symbol)

                    if m1_count == 0:
                        logger.debug(f"⏭️  [HistoricalProcessor] {symbol}: No 1m data, skip")
                        continue

                    # Process all target timeframes using batch aggregator
                    symbol_candles, self.total_errors = self.batch_aggregator.aggregate_timeframes(
                        symbol=symbol,
                        target_timeframes=self.target_timeframes,
                        gap_analyzer=self.gap_analyzer,
                        total_errors=self.total_errors
                    )

                    candles_generated += symbol_candles
                    symbols_processed += 1

                    # Force garbage collection after each symbol
                    gc.collect()

                    # Track memory after symbol processing
                    mem_after_symbol = self._get_memory_usage_mb()
                    mem_freed_symbol = mem_before_symbol - mem_after_symbol

                    logger.info(
                        f"📊 Symbol {symbol} complete | Memory: {mem_before_symbol:.1f}MB → {mem_after_symbol:.1f}MB "
                        f"(freed {mem_freed_symbol:.1f}MB after gc.collect())"
                    )

                except Exception as symbol_err:
                    self.total_errors += 1
                    logger.error(f"❌ [HistoricalProcessor] {symbol} failed: {symbol_err}")

                finally:
                    # Periodic aggressive GC every 5 symbols
                    if symbol_count % 5 == 0:
                        gc.collect()
                        mem_current = self._get_memory_usage_mb()
                        logger.info(
                            f"📊 Periodic GC after {symbol_count} symbols | Memory: {mem_current:.1f}MB"
                        )

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


    def get_stats(self) -> Dict[str, Any]:
        """Get processor statistics"""
        try:
            vm = psutil.virtual_memory()
            memory_available_mb = vm.available / 1024 / 1024
            memory_percent = vm.percent
        except Exception:
            memory_available_mb = 0
            memory_percent = 0

        return {
            'component': 'historical_processor',
            'priority': 'MEDIUM',
            'total_runs': self.total_runs,
            'total_symbols_processed': self.total_symbols_processed,
            'total_candles_generated': self.total_candles_generated,
            'total_errors': self.total_errors,
            'last_run_time': self.last_run_time.isoformat() if self.last_run_time else None,
            'last_run_status': self.last_run_status,
            'memory_mb': self._get_memory_usage_mb(),
            'memory_available_mb': memory_available_mb,
            'memory_percent': memory_percent
        }
