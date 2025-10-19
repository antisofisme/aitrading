"""
Target Calculator - 5 features
Calculate future returns for supervised learning (historical data only)
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional

class TargetCalculator:
    """Calculate 5 target variables"""

    def __init__(self, calculate_targets: bool = True):
        """
        Args:
            calculate_targets: Whether to calculate targets (False for live data)
        """
        self.calculate_targets = calculate_targets

    def calculate(self,
                  current_time: datetime,
                  current_close: float,
                  future_df: pd.DataFrame) -> Dict[str, Optional[float]]:
        """
        Calculate target variables from future data

        Args:
            current_time: Current candle timestamp
            current_close: Current close price
            future_df: DataFrame with future candles

        Returns:
            Dictionary with 5 target features
        """
        features = {
            'target_return_5min': None,
            'target_return_15min': None,
            'target_return_1h': None,
            'target_direction': None,
            'target_is_profitable': None
        }

        if not self.calculate_targets or future_df.empty:
            return features

        try:
            # Ensure future data is AFTER current time (prevent look-ahead bias)
            future_df = future_df[future_df['time'] > current_time].copy()

            if future_df.empty:
                return features

            # Target return 5min (1st candle ahead for 5m timeframe)
            if len(future_df) >= 1:
                future_close_5m = future_df.iloc[0]['close']
                features['target_return_5min'] = ((future_close_5m - current_close) / current_close) * 100

            # Target return 15min (3rd candle ahead for 5m TF, 1st for 15m TF)
            if len(future_df) >= 3:
                future_close_15m = future_df.iloc[2]['close']
                features['target_return_15min'] = ((future_close_15m - current_close) / current_close) * 100
            elif len(future_df) >= 1:
                # Fallback for higher TFs
                future_close_15m = future_df.iloc[0]['close']
                features['target_return_15min'] = ((future_close_15m - current_close) / current_close) * 100

            # Target return 1h (12th candle for 5m, 4th for 15m, etc)
            if len(future_df) >= 12:
                future_close_1h = future_df.iloc[11]['close']
            elif len(future_df) >= 1:
                future_close_1h = future_df.iloc[-1]['close']  # Use last available
            else:
                future_close_1h = None

            if future_close_1h:
                features['target_return_1h'] = ((future_close_1h - current_close) / current_close) * 100

                # Target direction (based on 1h return with threshold)
                if features['target_return_1h'] > 0.15:
                    features['target_direction'] = 'up'
                elif features['target_return_1h'] < -0.15:
                    features['target_direction'] = 'down'
                else:
                    features['target_direction'] = 'neutral'

                # Binary profitability (simplified)
                features['target_is_profitable'] = 1 if features['target_return_1h'] > 0 else 0

        except Exception as e:
            print(f"Error calculating targets: {e}")

        return features
