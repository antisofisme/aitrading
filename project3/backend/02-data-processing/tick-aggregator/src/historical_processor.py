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
                    m1_count = self._check_1m_data(symbol)

                    if m1_count == 0:
                        logger.debug(f"⏭️  [HistoricalProcessor] {symbol}: No 1m data, skip")
                        continue

                    # Process each target timeframe
                    for tf_config in self.target_timeframes:
                        timeframe = tf_config['name']
                        interval_minutes = tf_config['interval_minutes']

                        # Track memory before timeframe processing
                        mem_before_tf = self._get_memory_usage_mb()

                        # Check date range coverage (not just count)
                        coverage = self._check_date_coverage(symbol, timeframe)

                        # Skip if date range is complete (>1000 candles AND full 2015-2025 range)
                        if coverage['is_complete']:
                            logger.debug(
                                f"⏭️  [HistoricalProcessor] {symbol} {timeframe}: "
                                f"{coverage['count']} candles, range {coverage['earliest'].date()} to {coverage['latest'].date()} - COMPLETE, skip"
                            )
                            continue

                        # Determine aggregation strategy (incremental vs full)
                        start_date, end_date, strategy = self._determine_aggregation_range(symbol, timeframe, coverage)

                        logger.info(
                            f"📊 [HistoricalProcessor] {symbol} {timeframe}: "
                            f"Strategy: {strategy} | Range: {start_date.date() if start_date else 'ALL'} to {end_date.date() if end_date else 'NOW'}"
                        )

                        # NOTE: Per-candle validation now done in aggregator (skip incomplete candles only)
                        # No need to skip whole range if some 1m data missing

                        try:
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
                            self.total_errors += 1
                            logger.error(
                                f"❌ [HistoricalProcessor] {symbol} {timeframe} failed: {agg_err}"
                            )

                        finally:
                            # Force garbage collection after each timeframe
                            gc.collect()

                            # Track memory after timeframe processing
                            mem_after_tf = self._get_memory_usage_mb()
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

    def _check_date_coverage(self, symbol: str, timeframe: str) -> Dict[str, Any]:
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
            result = self.historical_aggregator.client.query(query)

            if not result.result_rows or result.result_rows[0][0] == 0:
                return {'count': 0, 'earliest': None, 'latest': None, 'is_complete': False}

            count = result.result_rows[0][0]
            earliest_ms = result.result_rows[0][1]
            latest_ms = result.result_rows[0][2]

            # Convert to datetime
            from datetime import datetime, timezone, timedelta
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

    def _determine_aggregation_range(self, symbol: str, timeframe: str, coverage: Dict[str, Any]) -> tuple:
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
        from datetime import datetime, timezone, timedelta

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
            gap_detector = GapDetector(self.historical_aggregator.clickhouse_config)
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
                missing_in_chunk = self._detect_gaps_in_range(
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

    def _validate_source_1m_complete(
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
            from datetime import datetime, timezone, timedelta

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
                result = self.historical_aggregator.client.query(query)
                if result.result_rows and result.result_rows[0][0]:
                    start_date = result.result_rows[0][0]
                else:
                    logger.warning(f"⚠️ No 1m data found for {symbol}")
                    return False

            if not end_date:
                end_date = datetime.now(timezone.utc)

            # Use gap_detector to check for gaps in 1m data
            gap_detector = GapDetector(self.historical_aggregator.clickhouse_config)
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

    def _detect_gaps_in_range(
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
