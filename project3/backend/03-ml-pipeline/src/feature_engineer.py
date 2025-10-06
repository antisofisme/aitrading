"""
Feature Engineering Service for ML Trading Platform

Computes technical indicators and features from raw OHLCV data
Stores results in ClickHouse ml_features table
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import talib
from clickhouse_driver import Client as ClickHouseClient
import aiohttp


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Computes ML features from raw OHLCV data
    """

    def __init__(
        self,
        clickhouse_host: str = 'localhost',
        clickhouse_port: int = 8123,
        clickhouse_db: str = 'ml_training',
        clickhouse_user: str = 'default',
        clickhouse_password: str = ''
    ):
        self.clickhouse = ClickHouseClient(
            host=clickhouse_host,
            port=clickhouse_port,
            database=clickhouse_db,
            user=clickhouse_user,
            password=clickhouse_password
        )

    # =========================================================================
    # MAIN FEATURE COMPUTATION
    # =========================================================================

    def compute_features(
        self,
        ohlcv_df: pd.DataFrame,
        tenant_id: str,
        user_id: str,
        symbol: str,
        timeframe: str
    ) -> pd.DataFrame:
        """
        Compute all features from OHLCV data

        Args:
            ohlcv_df: DataFrame with columns [timestamp, open, high, low, close, volume]
            tenant_id: Tenant identifier
            user_id: User identifier
            symbol: Trading pair (e.g., 'EUR/USD')
            timeframe: Timeframe (e.g., '1h')

        Returns:
            DataFrame with 100+ feature columns
        """
        logger.info(f"Computing features for {symbol} {timeframe} ({len(ohlcv_df)} rows)")

        df = ohlcv_df.copy()

        # Add identifiers
        df['tenant_id'] = tenant_id
        df['user_id'] = user_id
        df['symbol'] = symbol
        df['timeframe'] = timeframe
        df['timestamp_ms'] = (df['timestamp'].astype(np.int64) // 10**6).astype(np.int64)

        # 1. Price derivatives
        df = self._compute_price_derivatives(df)

        # 2. Trend indicators
        df = self._compute_trend_indicators(df)

        # 3. Momentum indicators
        df = self._compute_momentum_indicators(df)

        # 4. Volatility indicators
        df = self._compute_volatility_indicators(df)

        # 5. Volume indicators
        df = self._compute_volume_indicators(df)

        # 6. Pattern recognition
        df = self._compute_pattern_features(df)

        # 7. Market structure (support/resistance, pivots)
        df = self._compute_market_structure(df)

        # 8. External data enrichment (placeholder - implement based on your external data)
        df = self._enrich_external_data(df, symbol)

        # 9. Multi-horizon labels
        df = self._compute_labels(df, timeframe)

        # 10. Data quality scoring
        df = self._compute_quality_score(df)

        # 11. Metadata
        df['feature_version'] = '1.0.0'
        df['created_at'] = datetime.utcnow()
        df['updated_at'] = datetime.utcnow()

        return df

    # =========================================================================
    # PRICE DERIVATIVES
    # =========================================================================

    def _compute_price_derivatives(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute basic price-based features"""
        # Mid price (if bid/ask available, otherwise use close)
        if 'bid' in df.columns and 'ask' in df.columns:
            df['mid_price'] = (df['bid'] + df['ask']) / 2
            df['spread'] = df['ask'] - df['bid']
        else:
            df['mid_price'] = df['close']
            df['spread'] = 0.0

        df['range_pips'] = (df['high'] - df['low']) * 10000  # Convert to pips
        df['body_pips'] = abs(df['close'] - df['open']) * 10000

        return df

    # =========================================================================
    # TREND INDICATORS
    # =========================================================================

    def _compute_trend_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute trend-following indicators"""
        close = df['close'].values

        # Moving Averages
        for period in [10, 20, 50, 100, 200]:
            df[f'sma_{period}'] = talib.SMA(close, timeperiod=period)
            df[f'ema_{period}'] = talib.EMA(close, timeperiod=period)

        # Moving Average Crosses
        df['ma_cross_10_20'] = np.where(df['sma_10'] > df['sma_20'], 1, -1)
        df['ma_cross_20_50'] = np.where(df['sma_20'] > df['sma_50'], 1, -1)
        df['ma_cross_50_200'] = np.where(df['sma_50'] > df['sma_200'], 1, -1)  # Golden/Death cross

        # MACD
        df['macd_line'], df['macd_signal'], df['macd_histogram'] = talib.MACD(
            close, fastperiod=12, slowperiod=26, signalperiod=9
        )
        df['macd_cross'] = np.where(df['macd_line'] > df['macd_signal'], 1, -1)

        # ADX (Trend Strength)
        df['adx_14'] = talib.ADX(df['high'].values, df['low'].values, close, timeperiod=14)
        df['plus_di_14'] = talib.PLUS_DI(df['high'].values, df['low'].values, close, timeperiod=14)
        df['minus_di_14'] = talib.MINUS_DI(df['high'].values, df['low'].values, close, timeperiod=14)

        # ADX trend classification
        df['adx_trend'] = 'weak'
        df.loc[(df['adx_14'] > 25) & (df['plus_di_14'] > df['minus_di_14']), 'adx_trend'] = 'strong_up'
        df.loc[(df['adx_14'] > 25) & (df['plus_di_14'] < df['minus_di_14']), 'adx_trend'] = 'strong_down'

        # Ichimoku Cloud
        df['tenkan_sen'] = (df['high'].rolling(9).max() + df['low'].rolling(9).min()) / 2
        df['kijun_sen'] = (df['high'].rolling(26).max() + df['low'].rolling(26).min()) / 2
        df['senkou_span_a'] = ((df['tenkan_sen'] + df['kijun_sen']) / 2).shift(26)
        df['senkou_span_b'] = ((df['high'].rolling(52).max() + df['low'].rolling(52).min()) / 2).shift(26)
        df['chikou_span'] = df['close'].shift(-26)

        # Cloud position
        df['cloud_position'] = 'inside'
        df.loc[df['close'] > df[['senkou_span_a', 'senkou_span_b']].max(axis=1), 'cloud_position'] = 'above'
        df.loc[df['close'] < df[['senkou_span_a', 'senkou_span_b']].min(axis=1), 'cloud_position'] = 'below'

        return df

    # =========================================================================
    # MOMENTUM INDICATORS
    # =========================================================================

    def _compute_momentum_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute momentum oscillators"""
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values

        # RSI
        df['rsi_14'] = talib.RSI(close, timeperiod=14)
        df['rsi_zone'] = 'neutral'
        df.loc[df['rsi_14'] >= 70, 'rsi_zone'] = 'overbought'
        df.loc[df['rsi_14'] <= 30, 'rsi_zone'] = 'oversold'

        # RSI Divergence (simplified - needs price action confirmation)
        df['rsi_divergence'] = 0  # Placeholder - complex logic needed

        # Stochastic Oscillator
        df['stoch_k'], df['stoch_d'] = talib.STOCH(
            high, low, close,
            fastk_period=14, slowk_period=3, slowd_period=3
        )
        df['stoch_cross'] = np.where(df['stoch_k'] > df['stoch_d'], 1, -1)
        df['stoch_zone'] = 'neutral'
        df.loc[df['stoch_k'] >= 80, 'stoch_zone'] = 'overbought'
        df.loc[df['stoch_k'] <= 20, 'stoch_zone'] = 'oversold'

        # CCI
        df['cci_20'] = talib.CCI(high, low, close, timeperiod=20)
        df['cci_zone'] = 'neutral'
        df.loc[df['cci_20'] >= 100, 'cci_zone'] = 'overbought'
        df.loc[df['cci_20'] <= -100, 'cci_zone'] = 'oversold'

        # Williams %R
        df['williams_r_14'] = talib.WILLR(high, low, close, timeperiod=14)

        # Rate of Change
        df['roc_10'] = talib.ROC(close, timeperiod=10)
        df['roc_20'] = talib.ROC(close, timeperiod=20)
        df['momentum_10'] = talib.MOM(close, timeperiod=10)

        return df

    # =========================================================================
    # VOLATILITY INDICATORS
    # =========================================================================

    def _compute_volatility_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute volatility-based indicators"""
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values

        # Bollinger Bands
        df['bb_upper_20_2'], df['bb_middle_20_2'], df['bb_lower_20_2'] = talib.BBANDS(
            close, timeperiod=20, nbdevup=2, nbdevdn=2
        )
        df['bb_width'] = (df['bb_upper_20_2'] - df['bb_lower_20_2']) / df['bb_middle_20_2']
        df['bb_percent_b'] = (close - df['bb_lower_20_2']) / (df['bb_upper_20_2'] - df['bb_lower_20_2'])

        # Bollinger Band Squeeze
        df['bb_squeeze'] = np.where(df['bb_width'] < df['bb_width'].rolling(20).mean() * 0.8, 1, 0)

        # ATR
        df['atr_14'] = talib.ATR(high, low, close, timeperiod=14)
        df['atr_percent'] = (df['atr_14'] / close) * 100

        # Keltner Channels
        ema_20 = talib.EMA(close, timeperiod=20)
        atr_10 = talib.ATR(high, low, close, timeperiod=10)
        df['kc_upper'] = ema_20 + (2 * atr_10)
        df['kc_middle'] = ema_20
        df['kc_lower'] = ema_20 - (2 * atr_10)

        # Donchian Channels
        df['dc_upper_20'] = df['high'].rolling(20).max()
        df['dc_lower_20'] = df['low'].rolling(20).min()

        # Historical Volatility (20-period standard deviation of returns)
        returns = df['close'].pct_change()
        df['realized_vol_20'] = returns.rolling(20).std() * np.sqrt(252)  # Annualized

        return df

    # =========================================================================
    # VOLUME INDICATORS
    # =========================================================================

    def _compute_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute volume-based indicators"""
        close = df['close'].values
        volume = df['volume'].values
        high = df['high'].values
        low = df['low'].values

        # Volume SMA
        df['volume_sma_20'] = talib.SMA(volume.astype(float), timeperiod=20)
        df['volume_ratio'] = volume / df['volume_sma_20']

        # On-Balance Volume
        df['obv'] = talib.OBV(close, volume.astype(float))
        df['obv_sma_20'] = talib.SMA(df['obv'].values, timeperiod=20)

        # VWAP (Volume Weighted Average Price)
        df['vwap'] = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
        df['vwap_distance'] = (close - df['vwap']) / df['vwap']

        # Money Flow Index
        df['mfi_14'] = talib.MFI(high, low, close, volume.astype(float), timeperiod=14)

        return df

    # =========================================================================
    # PATTERN RECOGNITION
    # =========================================================================

    def _compute_pattern_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Detect candlestick patterns"""
        open_price = df['open'].values
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values

        # Candlestick patterns (TA-Lib returns -100/0/100)
        df['pattern_doji'] = talib.CDLDOJI(open_price, high, low, close) / 100
        df['pattern_hammer'] = talib.CDLHAMMER(open_price, high, low, close) / 100
        df['pattern_shooting_star'] = talib.CDLSHOOTINGSTAR(open_price, high, low, close) / 100
        df['pattern_engulfing'] = talib.CDLENGULFING(open_price, high, low, close) / 100
        df['pattern_morning_star'] = talib.CDLMORNINGSTAR(open_price, high, low, close) / 100
        df['pattern_evening_star'] = talib.CDLEVENINGSTAR(open_price, high, low, close) / 100

        # Support/Resistance (simplified - store as JSON string)
        df['pattern_support_resistance'] = '{}'  # Placeholder - complex logic

        # Trend channel
        df['pattern_trend_channel'] = 'none'  # Placeholder

        return df

    # =========================================================================
    # MARKET STRUCTURE
    # =========================================================================

    def _compute_market_structure(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute support/resistance and pivot points"""
        high = df['high']
        low = df['low']
        close = df['close']

        # Support/Resistance levels (simplified - using rolling min/max)
        df['support_level_1'] = low.rolling(50).min()
        df['support_level_2'] = low.rolling(100).min()
        df['resistance_level_1'] = high.rolling(50).max()
        df['resistance_level_2'] = high.rolling(100).max()

        # Pivot Points (Standard)
        pivot = (high.shift(1) + low.shift(1) + close.shift(1)) / 3
        df['pivot_point'] = pivot
        df['pivot_r1'] = 2 * pivot - low.shift(1)
        df['pivot_r2'] = pivot + (high.shift(1) - low.shift(1))
        df['pivot_s1'] = 2 * pivot - high.shift(1)
        df['pivot_s2'] = pivot - (high.shift(1) - low.shift(1))

        # Higher timeframe trend (placeholder - needs actual HTF data)
        df['htf_trend_1h'] = 'ranging'
        df['htf_trend_4h'] = 'ranging'
        df['htf_trend_1d'] = 'ranging'

        return df

    # =========================================================================
    # EXTERNAL DATA ENRICHMENT
    # =========================================================================

    def _enrich_external_data(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        Add external data features (economic calendar, sentiment, etc.)
        Placeholder - implement based on your external data sources
        """
        # Economic Calendar
        df['upcoming_event_impact'] = 'none'
        df['time_to_event_minutes'] = -1

        # Sentiment
        df['sentiment_score'] = 0.0  # -1 to 1
        df['fear_greed_index'] = 50  # 0-100

        # Correlations (placeholder - needs actual correlation computation)
        df['corr_eurusd'] = 0.0
        df['corr_gold'] = 0.0
        df['corr_dxy'] = 0.0

        return df

    # =========================================================================
    # LABEL COMPUTATION (SUPERVISED LEARNING)
    # =========================================================================

    def _compute_labels(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """
        Compute multi-horizon labels for supervised learning

        Labels:
        - Direction (classification): 1 (up), 0 (neutral), -1 (down)
        - Returns (regression): percentage change
        - Max gain/loss: for risk assessment
        """
        close = df['close']
        high = df['high']
        low = df['low']

        # Horizon mapping (adjust based on timeframe)
        horizon_map = {
            '1m': {'1h': 60, '4h': 240, '1d': 1440},
            '5m': {'1h': 12, '4h': 48, '1d': 288},
            '15m': {'1h': 4, '4h': 16, '1d': 96},
            '1h': {'1h': 1, '4h': 4, '1d': 24},
            '4h': {'1h': 0, '4h': 1, '1d': 6},
            '1d': {'1h': 0, '4h': 0, '1d': 1}
        }

        horizons = horizon_map.get(timeframe, {'1h': 1, '4h': 4, '1d': 24})

        for label, periods in horizons.items():
            if periods > 0:
                # Direction label
                future_close = close.shift(-periods)
                df[f'label_direction_{label}'] = np.where(
                    future_close > close * 1.001, 1,  # Up if > 0.1% gain
                    np.where(future_close < close * 0.999, -1, 0)  # Down if > 0.1% loss
                )

                # Return label (percentage)
                df[f'label_return_{label}'] = ((future_close - close) / close) * 100

                # Max gain/loss in next N periods
                future_highs = high.rolling(periods).max().shift(-periods)
                future_lows = low.rolling(periods).min().shift(-periods)
                df[f'label_max_gain_{label}'] = ((future_highs - close) / close) * 100
                df[f'label_max_loss_{label}'] = ((future_lows - close) / close) * 100

        # Trading outcome labels (placeholder - needs actual trade simulation)
        df['label_trade_outcome'] = ''
        df['label_profit_pips'] = 0.0
        df['label_optimal_entry'] = close
        df['label_optimal_exit'] = close

        return df

    # =========================================================================
    # DATA QUALITY SCORING
    # =========================================================================

    def _compute_quality_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Assess data quality (0-1 score)

        Quality criteria:
        - No missing values in critical features
        - Reasonable value ranges
        - Sufficient history for indicators
        """
        # Count missing values per row
        missing_count = df.isnull().sum(axis=1)
        total_features = len(df.columns)

        # Base score
        df['data_quality_score'] = 1.0 - (missing_count / total_features)

        # Penalize early rows (insufficient indicator history)
        df.loc[:200, 'data_quality_score'] *= 0.5

        # Track missing features
        df['missing_features'] = df.apply(
            lambda row: [col for col in df.columns if pd.isnull(row[col])],
            axis=1
        ).apply(lambda x: str(x) if x else '[]')

        return df

    # =========================================================================
    # DATABASE OPERATIONS
    # =========================================================================

    def save_to_clickhouse(self, features_df: pd.DataFrame) -> int:
        """
        Save computed features to ClickHouse ml_features table

        Returns:
            Number of rows inserted
        """
        # Select columns matching ml_features schema
        columns_to_save = [
            'tenant_id', 'user_id', 'symbol', 'timeframe', 'timestamp', 'timestamp_ms',
            'open', 'high', 'low', 'close', 'volume',
            'mid_price', 'spread', 'range_pips', 'body_pips',
            # ... (all feature columns - truncated for brevity)
            'data_quality_score', 'missing_features', 'feature_version',
            'created_at', 'updated_at'
        ]

        # Filter to columns that exist
        available_columns = [col for col in columns_to_save if col in features_df.columns]
        df_to_save = features_df[available_columns].copy()

        # Replace NaN with NULL (ClickHouse compatible)
        df_to_save = df_to_save.where(pd.notnull(df_to_save), None)

        # Convert to list of tuples
        data = [tuple(row) for row in df_to_save.values]

        # Insert
        query = f"""
            INSERT INTO ml_features ({', '.join(available_columns)})
            VALUES
        """

        self.clickhouse.execute(query, data)

        logger.info(f"Inserted {len(data)} rows into ml_features")
        return len(data)

    def compute_and_save(
        self,
        start_date: datetime,
        end_date: datetime,
        tenant_id: str,
        user_id: str,
        symbol: str,
        timeframe: str
    ) -> int:
        """
        Full pipeline: Load OHLCV → Compute features → Save to ClickHouse

        Args:
            start_date: Start date for feature computation
            end_date: End date
            tenant_id, user_id, symbol, timeframe: Identifiers

        Returns:
            Number of rows processed
        """
        # 1. Load OHLCV data from ClickHouse (aggregates table)
        query = f"""
            SELECT
                timestamp,
                open,
                high,
                low,
                close,
                volume
            FROM forex_data.aggregates
            WHERE symbol = '{symbol}'
              AND timeframe = '{timeframe}'
              AND timestamp >= '{start_date.isoformat()}'
              AND timestamp <= '{end_date.isoformat()}'
            ORDER BY timestamp
        """

        result = self.clickhouse.execute(query, with_column_types=True)
        columns = [col[0] for col in result[1]]
        ohlcv_df = pd.DataFrame(result[0], columns=columns)

        if ohlcv_df.empty:
            logger.warning(f"No data found for {symbol} {timeframe}")
            return 0

        # 2. Compute features
        features_df = self.compute_features(
            ohlcv_df=ohlcv_df,
            tenant_id=tenant_id,
            user_id=user_id,
            symbol=symbol,
            timeframe=timeframe
        )

        # 3. Save to ClickHouse
        rows_inserted = self.save_to_clickhouse(features_df)

        return rows_inserted


# =============================================================================
# MAIN EXECUTION
# =============================================================================

async def main():
    """Example usage"""
    engineer = FeatureEngineer(
        clickhouse_host='localhost',
        clickhouse_port=9000,
        clickhouse_db='ml_training'
    )

    # Compute features for EUR/USD 1h for last 30 days
    rows = engineer.compute_and_save(
        start_date=datetime.utcnow() - timedelta(days=30),
        end_date=datetime.utcnow(),
        tenant_id='tenant_001',
        user_id='user_123',
        symbol='EUR/USD',
        timeframe='1h'
    )

    logger.info(f"Feature engineering complete: {rows} rows processed")


if __name__ == '__main__':
    asyncio.run(main())
