"""
Fibonacci Calculator - 7 features
Calculate Fibonacci retracement levels
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional

class FibonacciCalculator:
    """Calculate Fibonacci retracement levels"""

    def calculate(self, df: pd.DataFrame, lookback: int = 50) -> Dict[str, Optional[float]]:
        """
        Calculate Fibonacci levels from swing high/low

        Args:
            df: DataFrame with OHLC data
            lookback: Number of candles to look back for swing points

        Returns:
            Dictionary with 7 Fibonacci levels
        """
        features = {
            'fib_0': None,
            'fib_236': None,
            'fib_382': None,
            'fib_50': None,
            'fib_618': None,
            'fib_786': None,
            'fib_100': None
        }

        if df.empty or len(df) < lookback:
            return features

        try:
            # Get recent data
            recent_df = df.tail(lookback)
            high_values = recent_df['high'].values
            low_values = recent_df['low'].values

            # Find swing high and low
            swing_high = float(np.max(high_values))
            swing_low = float(np.min(low_values))

            # Calculate Fibonacci levels
            diff = swing_high - swing_low

            features['fib_0'] = swing_low
            features['fib_236'] = swing_low + (diff * 0.236)
            features['fib_382'] = swing_low + (diff * 0.382)
            features['fib_50'] = swing_low + (diff * 0.50)
            features['fib_618'] = swing_low + (diff * 0.618)
            features['fib_786'] = swing_low + (diff * 0.786)
            features['fib_100'] = swing_high

        except Exception as e:
            print(f"Error calculating Fibonacci levels: {e}")

        return features
