"""
Tick Aggregator - Query TimescaleDB and Aggregate to OHLCV + Technical Indicators
Batch processing with multi-timeframe support + 12 core technical indicators
"""
import asyncio
import asyncpg
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import pandas as pd
from technical_indicators import TechnicalIndicators

logger = logging.getLogger(__name__)

class TickAggregator:
    """
    Aggregates tick data from TimescaleDB into OHLCV candles

    Process:
    1. Query ticks from TimescaleDB (batch)
    2. Aggregate to OHLCV per timeframe (M5, M15, M30, H1, H4, D1, W1)
    3. Calculate derived metrics (range_pips, body_pips, VWAP)
    4. Publish to NATS/Kafka
    """

    # Query timeout settings
    QUERY_TIMEOUT_SHORT = 10.0  # 10 seconds for simple queries
    QUERY_TIMEOUT_MEDIUM = 30.0  # 30 seconds for aggregations
    QUERY_TIMEOUT_LONG = 60.0  # 60 seconds for complex queries

    # Slow query threshold for logging
    SLOW_QUERY_THRESHOLD = 5.0  # Log queries > 5 seconds

    def __init__(self, db_config: Dict[str, Any], aggregation_config: Dict[str, Any]):
        self.db_config = db_config
        self.aggregation_config = aggregation_config
        self.pool: Optional[asyncpg.Pool] = None

        # Initialize technical indicators calculator
        indicator_config = aggregation_config.get('technical_indicators', None)
        self.indicators_calculator = TechnicalIndicators(indicator_config)

        # Statistics
        self.total_ticks_processed = 0
        self.total_candles_generated = 0
        self.total_indicators_calculated = 0

        # Query performance statistics
        self.query_stats = {
            'total_queries': 0,
            'slow_queries': 0,
            'timeout_errors': 0,
            'total_duration': 0.0
        }

        logger.info("TickAggregator initialized with technical indicators support")

    async def _execute_query_with_timeout(
        self,
        conn,
        query: str,
        *args,
        timeout: float = 30.0,
        query_name: str = "unknown"
    ):
        """
        Execute query with timeout and performance logging

        Args:
            conn: AsyncPG connection
            query: SQL query string
            args: Query parameters
            timeout: Timeout in seconds
            query_name: Name for logging

        Returns:
            Query results

        Raises:
            asyncio.TimeoutError: If query exceeds timeout
        """
        start_time = time.time()

        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                conn.fetch(query, *args),
                timeout=timeout
            )

            # Log slow queries
            duration = time.time() - start_time
            if duration > self.SLOW_QUERY_THRESHOLD:
                logger.warning(
                    f"🐌 Slow query '{query_name}': {duration:.2f}s "
                    f"(threshold: {self.SLOW_QUERY_THRESHOLD}s)"
                )
            else:
                logger.debug(f"✅ Query '{query_name}': {duration:.2f}s")

            # Update statistics
            self._update_query_stats(duration, timed_out=False)

            return result

        except asyncio.TimeoutError:
            duration = time.time() - start_time
            logger.error(
                f"❌ Query timeout '{query_name}' after {duration:.2f}s "
                f"(limit: {timeout}s)\nQuery: {query[:200]}..."
            )
            self._update_query_stats(duration, timed_out=True)
            raise
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"❌ Query error '{query_name}' after {duration:.2f}s: {e}"
            )
            raise

    def _update_query_stats(self, duration: float, timed_out: bool = False):
        """Update query performance statistics"""
        self.query_stats['total_queries'] += 1
        self.query_stats['total_duration'] += duration

        if duration > self.SLOW_QUERY_THRESHOLD:
            self.query_stats['slow_queries'] += 1

        if timed_out:
            self.query_stats['timeout_errors'] += 1

    def get_query_stats(self):
        """Get query performance statistics"""
        total = self.query_stats['total_queries']
        if total == 0:
            return self.query_stats

        avg_duration = self.query_stats['total_duration'] / total
        slow_pct = (self.query_stats['slow_queries'] / total) * 100

        return {
            **self.query_stats,
            'avg_duration_seconds': round(avg_duration, 2),
            'slow_query_percentage': round(slow_pct, 1)
        }

    async def connect(self):
        """Create database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                min_size=2,
                max_size=self.db_config.get('pool_size', 5)
            )
            logger.info(f"✅ Connected to TimescaleDB: {self.db_config['host']}:{self.db_config['port']}")

        except Exception as e:
            logger.error(f"❌ TimescaleDB connection failed: {e}")
            raise

    async def aggregate_timeframe(
        self,
        timeframe_config: Dict[str, Any],
        symbols: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Aggregate ticks to OHLCV for specific timeframe

        Args:
            timeframe_config: Timeframe configuration (name, interval, lookback)
            symbols: List of symbols to aggregate

        Returns:
            List of OHLCV candles
        """
        timeframe = timeframe_config['name']
        lookback_minutes = timeframe_config['lookback_minutes']
        interval_minutes = timeframe_config['interval_minutes']

        logger.debug(f"📊 Aggregating {timeframe} for {len(symbols)} symbols...")

        # Calculate time window
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=lookback_minutes)

        # Query ticks from TimescaleDB (calculate mid and spread on-the-fly)
        query = """
            SELECT
                symbol,
                time as timestamp,
                bid,
                ask,
                (bid + ask) / 2 as mid,
                ask - bid as spread,
                EXTRACT(EPOCH FROM time)::BIGINT * 1000 as timestamp_ms
            FROM live_ticks
            WHERE symbol = ANY($1)
              AND time >= $2
              AND time < $3
            ORDER BY symbol, time ASC
        """

        candles = []

        try:
            async with self.pool.acquire() as conn:
                rows = await self._execute_query_with_timeout(
                    conn,
                    query,
                    symbols,
                    start_time,
                    end_time,
                    timeout=self.QUERY_TIMEOUT_MEDIUM,
                    query_name=f"aggregate_ticks_{timeframe}"
                )

            if not rows:
                logger.debug(f"No ticks found for {timeframe} in window {start_time} to {end_time}")
                return []

            self.total_ticks_processed += len(rows)
            logger.debug(f"📈 Fetched {len(rows)} ticks from TimescaleDB for {timeframe}")

            # Convert to pandas for efficient aggregation
            df = pd.DataFrame(rows, columns=['symbol', 'timestamp', 'bid', 'ask', 'mid', 'spread', 'timestamp_ms'])

            # Group by symbol and aggregate
            for symbol, group in df.groupby('symbol'):
                # Resample to timeframe intervals
                group = group.set_index('timestamp')

                # Determine resample rule
                resample_rule = self._get_resample_rule(timeframe)

                # Aggregate using mid price for OHLC + spread metrics
                resampled = group.resample(resample_rule).agg({
                    'mid': ['first', 'max', 'min', 'last', 'count'],
                    'spread': ['mean', 'max', 'min'],  # NEW: avg, max, min spread for ML
                    'timestamp_ms': 'first'
                }).dropna()

                # Prepare OHLCV DataFrame for indicator calculation
                ohlcv_df = pd.DataFrame({
                    'open': resampled[('mid', 'first')],
                    'high': resampled[('mid', 'max')],
                    'low': resampled[('mid', 'min')],
                    'close': resampled[('mid', 'last')],
                    'volume': resampled[('mid', 'count')]
                })

                # Calculate technical indicators on OHLCV data
                if not ohlcv_df.empty and len(ohlcv_df) > 1:
                    ohlcv_with_indicators = self.indicators_calculator.calculate_all(ohlcv_df)
                else:
                    ohlcv_with_indicators = ohlcv_df

                # Generate candles with spread metrics for ML
                for i, (timestamp, row) in enumerate(resampled.iterrows()):
                    open_price = row[('mid', 'first')]
                    high_price = row[('mid', 'max')]
                    low_price = row[('mid', 'min')]
                    close_price = row[('mid', 'last')]
                    tick_count = int(row[('mid', 'count')])

                    # Spread metrics (critical for ML features)
                    avg_spread = row[('spread', 'mean')]
                    max_spread = row[('spread', 'max')]
                    min_spread = row[('spread', 'min')]

                    # Price range in pips
                    price_range = round((high_price - low_price) * 10000, 2)

                    # Percentage change (momentum feature)
                    pct_change = ((close_price - open_price) / open_price * 100) if open_price != 0 else 0

                    # Completeness flag (1 if tick_count > minimum threshold)
                    is_complete = 1 if tick_count >= 5 else 0  # Require at least 5 ticks for complete candle

                    # Timestamp
                    timestamp_ms = int(timestamp.timestamp() * 1000)

                    # NEW: 15-column schema aligned with live_aggregates table
                    candle = {
                        'symbol': symbol,
                        'timeframe': timeframe,
                        'timestamp_ms': timestamp_ms,
                        'open': float(open_price),
                        'high': float(high_price),
                        'low': float(low_price),
                        'close': float(close_price),
                        'tick_count': tick_count,  # Renamed from 'volume'
                        'avg_spread': float(avg_spread),  # NEW: ML feature
                        'max_spread': float(max_spread),  # NEW: ML feature
                        'min_spread': float(min_spread),  # NEW: ML feature
                        'price_range': float(price_range),  # Renamed from 'range_pips'
                        'pct_change': float(pct_change),  # NEW: momentum feature
                        'is_complete': is_complete  # NEW: quality flag
                    }

                    # Add technical indicators for this candle
                    if i < len(ohlcv_with_indicators):
                        indicator_row = ohlcv_with_indicators.iloc[i]
                        indicators = {}

                        # Extract all indicator columns (exclude OHLCV)
                        exclude_cols = ['open', 'high', 'low', 'close', 'volume']
                        for col in ohlcv_with_indicators.columns:
                            if col not in exclude_cols:
                                value = indicator_row[col]
                                if pd.notna(value):
                                    indicators[col] = float(value)

                        if indicators:
                            candle['indicators'] = indicators
                            self.total_indicators_calculated += 1

                    candles.append(candle)
                    self.total_candles_generated += 1

            logger.debug(f"✅ Generated {len(candles)} candles for {timeframe}")
            return candles

        except Exception as e:
            logger.error(f"❌ Error aggregating {timeframe}: {e}", exc_info=True)
            return []

    def _get_resample_rule(self, timeframe: str) -> str:
        """
        Convert timeframe to pandas resample rule

        Args:
            timeframe: Timeframe name (5m, 15m, 30m, 1h, 4h, 1d, 1w)

        Returns:
            Pandas resample rule string
        """
        mapping = {
            '5m': '5T',
            '15m': '15T',
            '30m': '30T',
            '1h': '1H',
            '4h': '4H',
            '1d': '1D',
            '1w': 'W-MON'  # Week starting Monday
        }
        return mapping.get(timeframe, '5T')

    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("✅ TimescaleDB connection pool closed")

    def get_stats(self) -> Dict[str, Any]:
        """Get aggregator statistics"""
        query_stats = self.get_query_stats()
        return {
            'total_ticks_processed': self.total_ticks_processed,
            'total_candles_generated': self.total_candles_generated,
            'total_indicators_calculated': self.total_indicators_calculated,
            'query_performance': query_stats
        }
