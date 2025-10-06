"""
Tick Aggregator - Query TimescaleDB and Aggregate to OHLCV
Batch processing with multi-timeframe support
"""
import asyncio
import asyncpg
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import pandas as pd

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

        # Statistics
        self.total_ticks_processed = 0
        self.total_candles_generated = 0

        logger.info("TickAggregator initialized")

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

        logger.info(f"📊 Aggregating {timeframe} for {len(symbols)} symbols...")

        # Calculate time window
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=lookback_minutes)

        # Query ticks from TimescaleDB
        query = """
            SELECT
                symbol,
                time,
                bid,
                ask,
                mid,
                spread,
                timestamp_ms
            FROM market_ticks
            WHERE tenant_id = $1
              AND symbol = ANY($2)
              AND time >= $3
              AND time < $4
            ORDER BY symbol, time ASC
        """

        candles = []

        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    query,
                    self.db_config['tenant_id'],
                    symbols,
                    start_time,
                    end_time
                )

            if not rows:
                logger.debug(f"No ticks found for {timeframe} in window {start_time} to {end_time}")
                return []

            self.total_ticks_processed += len(rows)
            logger.info(f"📈 Fetched {len(rows)} ticks from TimescaleDB for {timeframe}")

            # Convert to pandas for efficient aggregation
            df = pd.DataFrame(rows, columns=['symbol', 'time', 'bid', 'ask', 'mid', 'spread', 'timestamp_ms'])

            # Group by symbol and aggregate
            for symbol, group in df.groupby('symbol'):
                # Resample to timeframe intervals
                group = group.set_index('time')

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

                # Generate candles
                for timestamp, row in resampled.iterrows():
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

                    candles.append(candle)
                    self.total_candles_generated += 1

            logger.info(f"✅ Generated {len(candles)} candles for {timeframe}")
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
            'total_candles_generated': self.total_candles_generated
        }
