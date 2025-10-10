"""
Tick Aggregator - Query TimescaleDB and Aggregate to OHLCV + Technical Indicators
Batch processing with multi-timeframe support + 12 core technical indicators
"""
import asyncio
import asyncpg
import logging
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

        logger.info("TickAggregator initialized with technical indicators support")

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

        # Query ticks from TimescaleDB
        query = """
            SELECT
                symbol,
                timestamp,
                bid,
                ask,
                mid,
                spread,
                EXTRACT(EPOCH FROM timestamp)::BIGINT * 1000 as timestamp_ms
            FROM market_ticks
            WHERE symbol = ANY($1)
              AND timestamp >= $2
              AND timestamp < $3
            ORDER BY symbol, timestamp ASC
        """

        candles = []

        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    query,
                    symbols,
                    start_time,
                    end_time
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

                # Aggregate using mid price for OHLC
                resampled = group.resample(resample_rule).agg({
                    'mid': ['first', 'max', 'min', 'last', 'count'],
                    'bid': 'mean',
                    'ask': 'mean',
                    'spread': 'mean',
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

                # Generate candles with indicators
                for i, (timestamp, row) in enumerate(resampled.iterrows()):
                    open_price = row[('mid', 'first')]
                    high_price = row[('mid', 'max')]
                    low_price = row[('mid', 'min')]
                    close_price = row[('mid', 'last')]
                    tick_count = int(row[('mid', 'count')])

                    # Calculate VWAP (using mid price)
                    vwap = (open_price + high_price + low_price + close_price) / 4

                    # Calculate range and body in pips
                    range_pips = round((high_price - low_price) * 10000, 2)
                    body_pips = round(abs(close_price - open_price) * 10000, 2)

                    # Timestamp
                    timestamp_ms = int(timestamp.timestamp() * 1000)
                    end_timestamp = timestamp + timedelta(minutes=interval_minutes)

                    candle = {
                        'symbol': symbol,
                        'timeframe': timeframe,
                        'timestamp_ms': timestamp_ms,
                        'open': float(open_price),
                        'high': float(high_price),
                        'low': float(low_price),
                        'close': float(close_price),
                        'volume': tick_count,  # Tick volume (number of ticks)
                        'vwap': float(vwap),
                        'range_pips': float(range_pips),
                        'body_pips': float(body_pips),
                        'start_time': timestamp.isoformat(),
                        'end_time': end_timestamp.isoformat(),
                        'source': 'live_aggregated',
                        'event_type': 'ohlcv'
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

    def get_stats(self) -> Dict[str, int]:
        """Get aggregator statistics"""
        return {
            'total_ticks_processed': self.total_ticks_processed,
            'total_candles_generated': self.total_candles_generated,
            'total_indicators_calculated': self.total_indicators_calculated
        }
