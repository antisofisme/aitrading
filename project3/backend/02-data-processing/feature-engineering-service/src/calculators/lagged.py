"""
Lagged Feature Calculator - 15 features
Calculate lagged price, indicators, returns, volume, spread
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional

class LaggedFeatureCalculator:
    """Calculate 15 lagged features"""

    def calculate(self, df: pd.DataFrame) -> Dict[str, Optional[float]]:
        """
        Calculate lagged features from historical data

        Args:
            df: DataFrame with OHLC and indicator data (sorted by time)

        Returns:
            Dictionary with 15 lagged features
        """
        features = {
            'close_lag_1': None,
            'close_lag_2': None,
            'close_lag_3': None,
            'close_lag_5': None,
            'close_lag_10': None,
            'rsi_lag_1': None,
            'rsi_lag_2': None,
            'macd_lag_1': None,
            'return_lag_1': None,
            'return_lag_2': None,
            'return_lag_3': None,
            'volume_lag_1': None,
            'volume_lag_2': None,
            'spread_lag_1': None,
            'spread_lag_2': None
        }

        if df.empty or len(df) < 2:
            return features

        try:
            close = df['close'].values
            current_close = close[-1]

            # Lagged close prices
            if len(close) >= 2:
                features['close_lag_1'] = float(close[-2])
            if len(close) >= 3:
                features['close_lag_2'] = float(close[-3])
            if len(close) >= 4:
                features['close_lag_3'] = float(close[-4])
            if len(close) >= 6:
                features['close_lag_5'] = float(close[-6])
            if len(close) >= 11:
                features['close_lag_10'] = float(close[-11])

            # Lagged returns
            if features['close_lag_1']:
                features['return_lag_1'] = ((current_close / features['close_lag_1']) - 1) * 100
            if features['close_lag_2']:
                features['return_lag_2'] = ((features['close_lag_1'] / features['close_lag_2']) - 1) * 100
            if features['close_lag_3']:
                features['return_lag_3'] = ((features['close_lag_2'] / features['close_lag_3']) - 1) * 100

            # Lagged volume
            if 'tick_count' in df.columns:
                volume = df['tick_count'].values
                if len(volume) >= 2:
                    features['volume_lag_1'] = int(volume[-2])
                if len(volume) >= 3:
                    features['volume_lag_2'] = int(volume[-3])

            # Lagged spread
            if 'avg_spread' in df.columns:
                spread = df['avg_spread'].values
                if len(spread) >= 2:
                    features['spread_lag_1'] = float(spread[-2])
                if len(spread) >= 3:
                    features['spread_lag_2'] = float(spread[-3])

        except Exception as e:
            print(f"Error calculating lagged features: {e}")

        return features
