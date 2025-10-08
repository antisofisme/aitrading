"""
Technical Indicators Calculator for Tick Aggregator
Calculates 12 core technical indicators alongside OHLCV aggregation

Based on previous indicator implementation + recommended framework
Server-side calculation for consistency and performance
"""
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """
    Technical indicators calculator using pandas and numpy

    Implements 12 core indicators:
    1. SMA (Simple Moving Average)
    2. EMA (Exponential Moving Average)
    3. RSI (Relative Strength Index)
    4. MACD (Moving Average Convergence Divergence)
    5. Bollinger Bands
    6. ATR (Average True Range)
    7. Stochastic Oscillator
    8. CCI (Commodity Channel Index)
    9. MFI (Money Flow Index)
    10. OBV (On-Balance Volume)
    11. ADL (Accumulation/Distribution Line)
    12. VWAP (Volume Weighted Average Price)
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize indicator calculator

        Args:
            config: Optional configuration for indicator parameters
        """
        self.config = config or self._default_config()
        logger.info(f"Technical Indicators initialized with {len(self.config['indicators'])} indicators")

    def _default_config(self) -> Dict:
        """Default indicator configuration"""
        return {
            'indicators': {
                'sma': {
                    'enabled': True,
                    'periods': [7, 14, 21, 50, 200]
                },
                'ema': {
                    'enabled': True,
                    'periods': [7, 14, 21, 50, 200]
                },
                'rsi': {
                    'enabled': True,
                    'period': 14
                },
                'macd': {
                    'enabled': True,
                    'fast_period': 12,
                    'slow_period': 26,
                    'signal_period': 9
                },
                'bollinger': {
                    'enabled': True,
                    'period': 20,
                    'std_dev': 2.0
                },
                'atr': {
                    'enabled': True,
                    'period': 14
                },
                'stochastic': {
                    'enabled': True,
                    'k_period': 14,
                    'd_period': 3,
                    'smooth_k': 3
                },
                'cci': {
                    'enabled': True,
                    'period': 20
                },
                'mfi': {
                    'enabled': True,
                    'period': 14
                },
                'obv': {
                    'enabled': True
                },
                'adl': {
                    'enabled': True
                },
                'vwap': {
                    'enabled': True
                }
            }
        }

    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all enabled indicators on OHLCV data

        Args:
            df: DataFrame with columns [open, high, low, close, volume]

        Returns:
            DataFrame with additional indicator columns
        """
        if df.empty:
            logger.warning("Empty DataFrame provided for indicator calculation")
            return df

        # Make a copy to avoid modifying original
        result_df = df.copy()

        # Calculate each enabled indicator
        config = self.config['indicators']

        if config['sma']['enabled']:
            result_df = self._calculate_sma(result_df, config['sma']['periods'])

        if config['ema']['enabled']:
            result_df = self._calculate_ema(result_df, config['ema']['periods'])

        if config['rsi']['enabled']:
            result_df = self._calculate_rsi(result_df, config['rsi']['period'])

        if config['macd']['enabled']:
            result_df = self._calculate_macd(
                result_df,
                config['macd']['fast_period'],
                config['macd']['slow_period'],
                config['macd']['signal_period']
            )

        if config['bollinger']['enabled']:
            result_df = self._calculate_bollinger(
                result_df,
                config['bollinger']['period'],
                config['bollinger']['std_dev']
            )

        if config['atr']['enabled']:
            result_df = self._calculate_atr(result_df, config['atr']['period'])

        if config['stochastic']['enabled']:
            result_df = self._calculate_stochastic(
                result_df,
                config['stochastic']['k_period'],
                config['stochastic']['d_period'],
                config['stochastic']['smooth_k']
            )

        if config['cci']['enabled']:
            result_df = self._calculate_cci(result_df, config['cci']['period'])

        if config['mfi']['enabled']:
            result_df = self._calculate_mfi(result_df, config['mfi']['period'])

        if config['obv']['enabled']:
            result_df = self._calculate_obv(result_df)

        if config['adl']['enabled']:
            result_df = self._calculate_adl(result_df)

        if config['vwap']['enabled']:
            result_df = self._calculate_vwap(result_df)

        return result_df

    # ==================== MOVING AVERAGES ====================

    def _calculate_sma(self, df: pd.DataFrame, periods: List[int]) -> pd.DataFrame:
        """Calculate Simple Moving Average for multiple periods"""
        for period in periods:
            df[f'sma_{period}'] = df['close'].rolling(window=period).mean()
        return df

    def _calculate_ema(self, df: pd.DataFrame, periods: List[int]) -> pd.DataFrame:
        """Calculate Exponential Moving Average for multiple periods"""
        for period in periods:
            df[f'ema_{period}'] = df['close'].ewm(span=period, adjust=False).mean()
        return df

    # ==================== MOMENTUM INDICATORS ====================

    def _calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        Calculate Relative Strength Index
        RSI = 100 - (100 / (1 + RS))
        RS = Average Gain / Average Loss
        """
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        return df

    def _calculate_macd(self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """
        Calculate MACD (Moving Average Convergence Divergence)
        MACD Line = EMA(12) - EMA(26)
        Signal Line = EMA(9) of MACD Line
        Histogram = MACD Line - Signal Line
        """
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()

        df['macd'] = ema_fast - ema_slow
        df['macd_signal'] = df['macd'].ewm(span=signal, adjust=False).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']

        return df

    def _calculate_stochastic(self, df: pd.DataFrame, k_period: int = 14, d_period: int = 3, smooth_k: int = 3) -> pd.DataFrame:
        """
        Calculate Stochastic Oscillator
        %K = (Close - Lowest Low) / (Highest High - Lowest Low) * 100
        %D = SMA of %K
        """
        low_min = df['low'].rolling(window=k_period).min()
        high_max = df['high'].rolling(window=k_period).max()

        # Fast %K
        fast_k = 100 * (df['close'] - low_min) / (high_max - low_min)

        # Slow %K (smoothed)
        df['stoch_k'] = fast_k.rolling(window=smooth_k).mean()

        # %D (signal line)
        df['stoch_d'] = df['stoch_k'].rolling(window=d_period).mean()

        return df

    def _calculate_cci(self, df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        """
        Calculate Commodity Channel Index
        CCI = (Typical Price - SMA of TP) / (0.015 * Mean Deviation)
        """
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        sma_tp = typical_price.rolling(window=period).mean()
        mean_dev = typical_price.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())

        df['cci'] = (typical_price - sma_tp) / (0.015 * mean_dev)

        return df

    def _calculate_mfi(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        Calculate Money Flow Index
        MFI = 100 - (100 / (1 + Money Flow Ratio))
        """
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        money_flow = typical_price * df['volume']

        positive_flow = money_flow.where(typical_price > typical_price.shift(1), 0).rolling(window=period).sum()
        negative_flow = money_flow.where(typical_price < typical_price.shift(1), 0).rolling(window=period).sum()

        mfi_ratio = positive_flow / negative_flow
        df['mfi'] = 100 - (100 / (1 + mfi_ratio))

        return df

    # ==================== VOLATILITY INDICATORS ====================

    def _calculate_bollinger(self, df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
        """
        Calculate Bollinger Bands
        Middle Band = SMA(20)
        Upper Band = SMA(20) + 2*STD
        Lower Band = SMA(20) - 2*STD
        """
        sma = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()

        df['bb_middle'] = sma
        df['bb_upper'] = sma + (std_dev * std)
        df['bb_lower'] = sma - (std_dev * std)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']

        return df

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        Calculate Average True Range
        TR = max[(high - low), abs(high - close_prev), abs(low - close_prev)]
        ATR = EMA of TR
        """
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = true_range.ewm(span=period, adjust=False).mean()

        return df

    # ==================== VOLUME INDICATORS ====================

    def _calculate_obv(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate On-Balance Volume
        OBV = OBV_prev + volume (if close > close_prev)
        OBV = OBV_prev - volume (if close < close_prev)
        """
        obv = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()
        df['obv'] = obv

        return df

    def _calculate_adl(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Accumulation/Distribution Line
        CLV = [(close - low) - (high - close)] / (high - low)
        ADL = ADL_prev + CLV * volume
        """
        clv = ((df['close'] - df['low']) - (df['high'] - df['close'])) / (df['high'] - df['low'])
        clv = clv.fillna(0)

        df['adl'] = (clv * df['volume']).cumsum()

        return df

    def _calculate_vwap(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Volume Weighted Average Price
        VWAP = Cumulative(Typical Price * Volume) / Cumulative(Volume)
        """
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        df['vwap'] = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()

        return df

    def get_latest_indicators(self, df: pd.DataFrame) -> Dict:
        """
        Get latest indicator values as dictionary

        Args:
            df: DataFrame with calculated indicators

        Returns:
            Dictionary with latest indicator values
        """
        if df.empty:
            return {}

        latest = df.iloc[-1]
        indicators = {}

        # Extract all indicator columns (exclude OHLCV)
        exclude_cols = ['open', 'high', 'low', 'close', 'volume', 'timestamp']

        for col in df.columns:
            if col not in exclude_cols:
                value = latest[col]
                # Convert numpy types to Python types and handle NaN
                if pd.isna(value):
                    indicators[col] = None
                elif isinstance(value, (np.integer, np.floating)):
                    indicators[col] = float(value)
                else:
                    indicators[col] = value

        return indicators
