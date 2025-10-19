"""
Rolling Statistics Calculator - 8 features
Calculate rolling mean, std, min/max for support/resistance
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional

class RollingStatCalculator:
    """Calculate 8 rolling statistics"""

    def calculate(self, df: pd.DataFrame) -> Dict[str, Optional[float]]:
        """
        Calculate rolling statistics

        Args:
            df: DataFrame with OHLC data

        Returns:
            Dictionary with 8 rolling statistics
        """
        features = {
            'price_rolling_mean_10': None,
            'price_rolling_mean_20': None,
            'price_rolling_mean_50': None,
            'price_rolling_std_10': None,
            'price_rolling_std_20': None,
            'price_rolling_max_20': None,
            'price_rolling_min_20': None,
            'dist_from_rolling_mean_20': None
        }

        if df.empty:
            return features

        try:
            close = df['close'].values
            current_close = close[-1]

            # Rolling means
            if len(close) >= 10:
                features['price_rolling_mean_10'] = float(np.mean(close[-10:]))
                features['price_rolling_std_10'] = float(np.std(close[-10:]))

            if len(close) >= 20:
                features['price_rolling_mean_20'] = float(np.mean(close[-20:]))
                features['price_rolling_std_20'] = float(np.std(close[-20:]))
                features['price_rolling_max_20'] = float(np.max(close[-20:]))
                features['price_rolling_min_20'] = float(np.min(close[-20:]))

                # Z-score distance from mean
                if features['price_rolling_std_20'] > 0:
                    features['dist_from_rolling_mean_20'] = (
                        (current_close - features['price_rolling_mean_20']) /
                        features['price_rolling_std_20']
                    )

            if len(close) >= 50:
                features['price_rolling_mean_50'] = float(np.mean(close[-50:]))

        except Exception as e:
            print(f"Error calculating rolling statistics: {e}")

        return features
