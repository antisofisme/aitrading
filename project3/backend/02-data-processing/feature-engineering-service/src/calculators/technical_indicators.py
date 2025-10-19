"""
Technical Indicator Calculator - 14 features
Uses TA-Lib for indicator calculation
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional

try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    print("⚠️  TA-Lib not available, using simplified calculations")

class TechnicalIndicatorCalculator:
    """Calculate 14 technical indicators"""

    def calculate(self, df: pd.DataFrame) -> Dict[str, Optional[float]]:
        """
        Calculate technical indicators

        Args:
            df: DataFrame with OHLC data (sorted by time ascending)

        Returns:
            Dictionary with 14 technical indicator features
        """
        features = {
            'rsi_14': None,
            'macd': None,
            'macd_signal': None,
            'macd_histogram': None,
            'bb_upper': None,
            'bb_middle': None,
            'bb_lower': None,
            'stoch_k': None,
            'stoch_d': None,
            'sma_50': None,
            'sma_200': None,
            'ema_12': None,
            'cci': None,
            'mfi': None
        }

        if df.empty or len(df) < 14:
            return features

        try:
            close = df['close'].values
            high = df['high'].values
            low = df['low'].values
            volume = df.get('tick_count', df.get('volume', pd.Series([0] * len(df)))).values

            if TALIB_AVAILABLE:
                # RSI
                rsi = talib.RSI(close, timeperiod=14)
                features['rsi_14'] = float(rsi[-1]) if not np.isnan(rsi[-1]) else None

                # MACD
                macd, macd_signal, macd_hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
                features['macd'] = float(macd[-1]) if not np.isnan(macd[-1]) else None
                features['macd_signal'] = float(macd_signal[-1]) if not np.isnan(macd_signal[-1]) else None
                features['macd_histogram'] = float(macd_hist[-1]) if not np.isnan(macd_hist[-1]) else None

                # Bollinger Bands
                bb_upper, bb_middle, bb_lower = talib.BBANDS(close, timeperiod=20)
                features['bb_upper'] = float(bb_upper[-1]) if not np.isnan(bb_upper[-1]) else None
                features['bb_middle'] = float(bb_middle[-1]) if not np.isnan(bb_middle[-1]) else None
                features['bb_lower'] = float(bb_lower[-1]) if not np.isnan(bb_lower[-1]) else None

                # Stochastic
                stoch_k, stoch_d = talib.STOCH(high, low, close)
                features['stoch_k'] = float(stoch_k[-1]) if not np.isnan(stoch_k[-1]) else None
                features['stoch_d'] = float(stoch_d[-1]) if not np.isnan(stoch_d[-1]) else None

                # SMAs
                sma_50 = talib.SMA(close, timeperiod=50)
                sma_200 = talib.SMA(close, timeperiod=200)
                features['sma_50'] = float(sma_50[-1]) if len(sma_50) > 0 and not np.isnan(sma_50[-1]) else None
                features['sma_200'] = float(sma_200[-1]) if len(sma_200) > 0 and not np.isnan(sma_200[-1]) else None

                # EMA
                ema_12 = talib.EMA(close, timeperiod=12)
                features['ema_12'] = float(ema_12[-1]) if not np.isnan(ema_12[-1]) else None

                # CCI
                cci = talib.CCI(high, low, close, timeperiod=20)
                features['cci'] = float(cci[-1]) if not np.isnan(cci[-1]) else None

                # MFI
                if len(volume) == len(close):
                    mfi = talib.MFI(high, low, close, volume, timeperiod=14)
                    features['mfi'] = float(mfi[-1]) if not np.isnan(mfi[-1]) else None

            else:
                # Simplified calculations without TA-Lib
                if len(close) >= 14:
                    # Simple RSI
                    delta = np.diff(close)
                    gain = np.where(delta > 0, delta, 0)
                    loss = np.where(delta < 0, -delta, 0)
                    avg_gain = np.mean(gain[-14:])
                    avg_loss = np.mean(loss[-14:])
                    if avg_loss > 0:
                        rs = avg_gain / avg_loss
                        features['rsi_14'] = float(100 - (100 / (1 + rs)))

                if len(close) >= 20:
                    # Simple Bollinger Bands
                    sma_20 = np.mean(close[-20:])
                    std_20 = np.std(close[-20:])
                    features['bb_middle'] = float(sma_20)
                    features['bb_upper'] = float(sma_20 + 2 * std_20)
                    features['bb_lower'] = float(sma_20 - 2 * std_20)

                if len(close) >= 50:
                    features['sma_50'] = float(np.mean(close[-50:]))

                if len(close) >= 200:
                    features['sma_200'] = float(np.mean(close[-200:]))

        except Exception as e:
            print(f"Error calculating technical indicators: {e}")

        return features
