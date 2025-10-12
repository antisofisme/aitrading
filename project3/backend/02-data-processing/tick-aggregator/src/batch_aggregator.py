"""
Batch Aggregator - Handle batch aggregation operations

This module handles:
- Batch processing coordination
- Timeframe aggregation execution
- Memory management during batch operations
- Error handling for aggregation tasks
"""
import gc
import logging
from typing import List
from datetime import datetime

logger = logging.getLogger(__name__)


class BatchAggregator:
    """
    Manages batch aggregation operations

    Responsibilities:
    - Coordinate aggregation across multiple timeframes
    - Execute aggregation for individual timeframes
    - Manage memory during batch operations
    - Handle errors during aggregation
    """

    def __init__(self, historical_aggregator, memory_tracker):
        """
        Initialize batch aggregator

        Args:
            historical_aggregator: HistoricalAggregator instance
            memory_tracker: Callable that returns current memory usage in MB
        """
        self.historical_aggregator = historical_aggregator
        self.get_memory_usage = memory_tracker
        logger.debug("✅ BatchAggregator initialized")

    def aggregate_timeframes(
        self,
        symbol: str,
        target_timeframes: List[dict],
        gap_analyzer,
        total_errors: int
    ) -> tuple:
        """
        Aggregate all target timeframes for a symbol

        Args:
            symbol: Trading pair to aggregate
            target_timeframes: List of timeframe configs with 'name' and 'interval_minutes'
            gap_analyzer: GapAnalyzer instance for coverage checking
            total_errors: Current error count (will be updated)

        Returns:
            (candles_generated, updated_total_errors)
        """
        candles_generated = 0

        for tf_config in target_timeframes:
            timeframe = tf_config['name']
            interval_minutes = tf_config['interval_minutes']

            # Track memory before timeframe processing
            mem_before_tf = self.get_memory_usage()

            try:
                # Check date range coverage (not just count)
                coverage = gap_analyzer.check_date_coverage(symbol, timeframe)

                # Skip if date range is complete (>1000 candles AND full 2015-2025 range)
                if coverage['is_complete']:
                    logger.debug(
                        f"⏭️  [HistoricalProcessor] {symbol} {timeframe}: "
                        f"{coverage['count']} candles, range {coverage['earliest'].date()} to {coverage['latest'].date()} - COMPLETE, skip"
                    )
                    continue

                # Determine aggregation strategy (incremental vs full)
                start_date, end_date, strategy = gap_analyzer.determine_aggregation_range(
                    symbol, timeframe, coverage
                )

                logger.info(
                    f"📊 [HistoricalProcessor] {symbol} {timeframe}: "
                    f"Strategy: {strategy} | Range: {start_date.date() if start_date else 'ALL'} to {end_date.date() if end_date else 'NOW'}"
                )

                # NOTE: Per-candle validation now done in aggregator (skip incomplete candles only)
                # No need to skip whole range if some 1m data missing

                # Execute aggregation
                count = self.historical_aggregator.aggregate_symbol_timeframe(
                    symbol=symbol,
                    target_timeframe=timeframe,
                    interval_minutes=interval_minutes,
                    start_date=start_date,  # ← INCREMENTAL: Only process missing range
                    end_date=end_date
                )

                candles_generated += count
                logger.info(
                    f"✅ [HistoricalProcessor] {symbol} {timeframe}: "
                    f"{count:,} candles generated"
                )

            except Exception as agg_err:
                total_errors += 1
                logger.error(
                    f"❌ [HistoricalProcessor] {symbol} {timeframe} failed: {agg_err}"
                )

            finally:
                # Force garbage collection after each timeframe
                gc.collect()

                # Track memory after timeframe processing
                mem_after_tf = self.get_memory_usage()
                mem_freed_tf = mem_before_tf - mem_after_tf

                logger.debug(
                    f"📊 {symbol} {timeframe} complete | Memory: {mem_before_tf:.1f}MB → {mem_after_tf:.1f}MB "
                    f"(freed {mem_freed_tf:.1f}MB after gc.collect())"
                )

                # Alert if memory usage is too high
                if mem_after_tf > 500:
                    logger.warning(
                        f"⚠️ High memory usage after {symbol} {timeframe}: {mem_after_tf:.1f}MB "
                        f"(threshold: 500MB)"
                    )

        return candles_generated, total_errors

    def aggregate_single_timeframe(
        self,
        symbol: str,
        timeframe: str,
        interval_minutes: int,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> int:
        """
        Aggregate a single timeframe for a symbol

        Args:
            symbol: Trading pair
            timeframe: Target timeframe (e.g., '5m', '1h')
            interval_minutes: Interval in minutes
            start_date: Start date for aggregation (None = from earliest)
            end_date: End date for aggregation (None = until now)

        Returns:
            Number of candles generated
        """
        try:
            count = self.historical_aggregator.aggregate_symbol_timeframe(
                symbol=symbol,
                target_timeframe=timeframe,
                interval_minutes=interval_minutes,
                start_date=start_date,
                end_date=end_date
            )

            logger.info(
                f"✅ [BatchAggregator] {symbol} {timeframe}: {count:,} candles generated"
            )

            return count

        except Exception as e:
            logger.error(f"❌ [BatchAggregator] {symbol} {timeframe} failed: {e}")
            raise
