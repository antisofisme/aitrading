"""
Historical Aggregator - Aggregate ClickHouse 1m bars to higher timeframes
Backfills: 1m → 5m, 15m, 30m, 1h, 4h, 1d, 1w with technical indicators
"""
import logging
import clickhouse_connect
from typing import Dict, Any, List
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from technical_indicators import TechnicalIndicators
import json

logger = logging.getLogger(__name__)


class HistoricalAggregator:
    """
    Aggregates historical 1m bars from ClickHouse to higher timeframes

    Process:
    1. Read 1m bars from ClickHouse aggregates table (source='polygon_historical')
    2. Aggregate to 5m, 15m, 30m, 1h, 4h, 1d, 1w
    3. Calculate 26 technical indicators per timeframe
    4. Write back to ClickHouse aggregates table
    """

    def __init__(self, clickhouse_config: Dict[str, Any], aggregation_config: Dict[str, Any]):
        self.clickhouse_config = clickhouse_config
        self.aggregation_config = aggregation_config
        self.client = None

        # Initialize technical indicators calculator
        indicator_config = aggregation_config.get('technical_indicators', {})
        self.indicators_calculator = TechnicalIndicators(indicator_config)

        # Statistics
        self.total_1m_bars_read = 0
        self.total_candles_generated = 0

        logger.info("HistoricalAggregator initialized")

    def connect(self):
        """Connect to ClickHouse"""
        try:
            # Force HTTP port 8123 (clickhouse-connect uses HTTP, not native protocol)
            self.client = clickhouse_connect.get_client(
                host=self.clickhouse_config['host'],
                port=8123,  # Always use HTTP port
                username=self.clickhouse_config['user'],
                password=self.clickhouse_config['password'],
                database=self.clickhouse_config['database']
            )
            logger.info(f"✅ Connected to ClickHouse: {self.clickhouse_config['host']}")

        except Exception as e:
            logger.error(f"❌ ClickHouse connection failed: {e}")
            raise

    def aggregate_symbol_timeframe(
        self,
        symbol: str,
        target_timeframe: str,
        interval_minutes: int,
        start_date: datetime = None,
        end_date: datetime = None,
        batch_size: int = 50000  # Reduced from 100k to save memory
    ) -> int:
        """
        Aggregate 1m bars to target timeframe for one symbol

        Args:
            symbol: Symbol to aggregate (e.g., 'XAU/USD')
            target_timeframe: Target timeframe (5m, 15m, 30m, 1h, 4h, 1d, 1w)
            interval_minutes: Interval in minutes
            start_date: Start date for aggregation (default: earliest available)
            end_date: End date for aggregation (default: latest available)
            batch_size: Number of 1m bars to process per batch

        Returns:
            Number of candles generated
        """
        logger.info(f"📊 Aggregating {symbol} 1m → {target_timeframe}...")

        try:
            # Get total count first
            count_query = f"""
            SELECT COUNT(*) as count
            FROM aggregates
            WHERE symbol = '{symbol}'
              AND timeframe = '1m'
              AND source = 'polygon_historical'
            """
            count_result = self.client.query(count_query)
            total_rows = count_result.result_rows[0][0] if count_result.result_rows else 0

            if total_rows == 0:
                logger.warning(f"⚠️ No 1m bars found for {symbol}")
                return 0

            logger.info(f"📊 Total 1m bars to process: {total_rows:,} (batch size: {batch_size:,})")

            # Process in batches to limit memory usage
            total_candles_generated = 0
            offset = 0

            while offset < total_rows:
                logger.info(f"📦 Processing batch {offset//batch_size + 1}/{(total_rows + batch_size - 1)//batch_size} (offset: {offset:,})")

                # Query batch
                query = f"""
                SELECT
                    symbol,
                    timestamp,
                    timestamp_ms,
                    open,
                    high,
                    low,
                    close,
                    volume,
                    vwap,
                    range_pips,
                    body_pips,
                    start_time,
                    end_time,
                    source
                FROM aggregates
                WHERE symbol = '{symbol}'
                  AND timeframe = '1m'
                  AND source = 'polygon_historical'
                """

                if start_date:
                    query += f" AND timestamp >= '{start_date.strftime('%Y-%m-%d %H:%M:%S')}'"
                if end_date:
                    query += f" AND timestamp <= '{end_date.strftime('%Y-%m-%d %H:%M:%S')}'"

                query += f" ORDER BY timestamp ASC LIMIT {batch_size} OFFSET {offset}"

                # Execute query
                result = self.client.query(query)

                if not result.result_rows:
                    break

                # Convert to DataFrame
                df = pd.DataFrame(result.result_rows, columns=result.column_names)
                self.total_1m_bars_read += len(df)

                # Convert timestamp to datetime
                df['timestamp'] = pd.to_datetime(df['timestamp'])

                # Convert all numeric columns from Decimal to float
                numeric_cols = ['timestamp_ms', 'open', 'high', 'low', 'close', 'volume', 'vwap', 'range_pips', 'body_pips']
                for col in numeric_cols:
                    if col in df.columns:
                        try:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                        except Exception as e:
                            logger.warning(f"⚠️ Failed to convert {col} to numeric: {e}")

                df = df.set_index('timestamp')

                # Aggregate to target timeframe
                aggregated_candles = self._aggregate_bars(
                    df=df,
                    symbol=symbol,
                    target_timeframe=target_timeframe,
                    interval_minutes=interval_minutes
                )

                if aggregated_candles:
                    # Insert into ClickHouse
                    self._insert_candles(aggregated_candles)
                    total_candles_generated += len(aggregated_candles)
                    logger.info(f"✅ Batch complete: {len(aggregated_candles)} candles inserted")

                # Free memory
                del df
                del aggregated_candles

                offset += batch_size

            logger.info(f"✅ Total generated: {total_candles_generated} {target_timeframe} candles for {symbol}")
            return total_candles_generated

        except Exception as e:
            logger.error(f"❌ Error aggregating {symbol} {target_timeframe}: {e}", exc_info=True)
            return 0

    def _aggregate_bars(
        self,
        df: pd.DataFrame,
        symbol: str,
        target_timeframe: str,
        interval_minutes: int
    ) -> List[Dict[str, Any]]:
        """
        Aggregate 1m bars DataFrame to target timeframe with indicators

        Args:
            df: DataFrame with 1m bars (indexed by timestamp)
            symbol: Symbol name
            target_timeframe: Target timeframe
            interval_minutes: Interval in minutes

        Returns:
            List of aggregated candles with indicators
        """
        try:
            # Determine resample rule
            resample_rule = self._get_resample_rule(target_timeframe)

            # Aggregate OHLCV
            resampled = df.resample(resample_rule).agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum',  # Sum tick counts
                'vwap': 'mean',
                'range_pips': 'sum',
                'body_pips': 'sum'
            }).dropna()

            if resampled.empty:
                return []

            # Convert aggregated results to float (critical for indicators calculation)
            for col in ['open', 'high', 'low', 'close', 'volume', 'vwap', 'range_pips', 'body_pips']:
                if col in resampled.columns:
                    resampled[col] = resampled[col].astype(float)

            # Prepare OHLCV for indicator calculation
            ohlcv_df = pd.DataFrame({
                'open': resampled['open'].astype(float),
                'high': resampled['high'].astype(float),
                'low': resampled['low'].astype(float),
                'close': resampled['close'].astype(float),
                'volume': resampled['volume'].astype(float)
            })

            # Calculate technical indicators
            if len(ohlcv_df) > 1:
                ohlcv_with_indicators = self.indicators_calculator.calculate_all(ohlcv_df)
            else:
                ohlcv_with_indicators = ohlcv_df

            # Generate candle records
            candles = []
            for i, (timestamp, row) in enumerate(resampled.iterrows()):
                end_timestamp = timestamp + timedelta(minutes=interval_minutes)
                timestamp_ms = int(timestamp.timestamp() * 1000)

                candle = {
                    'symbol': symbol,
                    'timeframe': target_timeframe,
                    'timestamp': timestamp,
                    'timestamp_ms': timestamp_ms,
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': int(row['volume']),
                    'vwap': float(row['vwap']),
                    'range_pips': float(row['range_pips']),
                    'body_pips': float(row['body_pips']),
                    'start_time': timestamp,  # Keep as datetime object for ClickHouse DateTime64
                    'end_time': end_timestamp,  # Keep as datetime object for ClickHouse DateTime64
                    'source': 'historical_aggregated'
                }

                # Add technical indicators
                if i < len(ohlcv_with_indicators):
                    indicator_row = ohlcv_with_indicators.iloc[i]
                    indicators = {}

                    # Extract all indicator columns (exclude OHLCV)
                    exclude_cols = ['open', 'high', 'low', 'close', 'volume']
                    for col in ohlcv_with_indicators.columns:
                        if col not in exclude_cols:
                            value = indicator_row[col]
                            # Filter out NaN, Inf, and invalid values
                            if pd.notna(value) and np.isfinite(value):
                                try:
                                    indicators[col] = float(value)
                                except (ValueError, TypeError):
                                    pass  # Skip invalid values

                    if indicators:
                        candle['indicators'] = json.dumps(indicators)

                candles.append(candle)
                self.total_candles_generated += 1

            return candles

        except Exception as e:
            logger.error(f"❌ Error in _aggregate_bars: {e}", exc_info=True)
            return []

    def _insert_candles(self, candles: List[Dict[str, Any]]):
        """Insert candles into ClickHouse aggregates table"""
        try:
            # Prepare data for insertion
            data = []
            for candle in candles:
                # Convert indicators dict to JSON string if not already
                indicators_json = candle.get('indicators', '{}')
                if not isinstance(indicators_json, str):
                    indicators_json = json.dumps(indicators_json)

                # Ensure all numeric values are valid (not NaN/Inf)
                # Convert timestamp to datetime object if it's a string
                timestamp = candle['timestamp']
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', ''))

                row = [
                    candle['symbol'],
                    candle['timeframe'],
                    timestamp,
                    int(candle['timestamp_ms']),  # Ensure integer
                    float(candle['open']),
                    float(candle['high']),
                    float(candle['low']),
                    float(candle['close']),
                    int(candle['volume']),  # Volume as integer
                    float(candle['vwap']),
                    float(candle['range_pips']),
                    float(candle['body_pips']),
                    candle['start_time'],
                    candle['end_time'],
                    candle['source'],
                    indicators_json
                ]

                # Validate no NaN/Inf in numeric fields
                numeric_indices = [3, 4, 5, 6, 7, 8, 9, 10, 11]
                if all(np.isfinite(row[i]) for i in numeric_indices):
                    data.append(row)
                else:
                    logger.warning(f"⚠️ Skipping candle with invalid numeric values: {candle['symbol']} {candle['timestamp']}")

            # Insert into ClickHouse
            self.client.insert(
                'aggregates',
                data,
                column_names=[
                    'symbol', 'timeframe', 'timestamp', 'timestamp_ms',
                    'open', 'high', 'low', 'close', 'volume',
                    'vwap', 'range_pips', 'body_pips',
                    'start_time', 'end_time', 'source', 'indicators'
                ]
            )

            logger.debug(f"✅ Inserted {len(candles)} candles into ClickHouse")

        except Exception as e:
            logger.error(f"❌ Error inserting candles: {e}", exc_info=True)
            raise

    def _get_resample_rule(self, timeframe: str) -> str:
        """Convert timeframe to pandas resample rule"""
        mapping = {
            '5m': '5T',
            '15m': '15T',
            '30m': '30T',
            '1h': '1H',
            '4h': '4H',
            '1d': '1D',
            '1w': 'W-MON'
        }
        return mapping.get(timeframe, '5T')

    def close(self):
        """Close ClickHouse connection"""
        if self.client:
            self.client.close()
            logger.info("✅ ClickHouse connection closed")

    def get_stats(self) -> Dict[str, int]:
        """Get aggregator statistics"""
        return {
            'total_1m_bars_read': self.total_1m_bars_read,
            'total_candles_generated': self.total_candles_generated
        }
