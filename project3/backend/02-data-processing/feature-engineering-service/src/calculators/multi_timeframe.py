"""
Multi-Timeframe Calculator - 10 features
Calculate higher/lower timeframe context (simplified for Phase 1)
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional

class MultiTimeframeCalculator:
    """Calculate 10 multi-timeframe features"""

    def __init__(self, timeframe_mapping: dict):
        """
        Args:
            timeframe_mapping: Dict mapping current TF to higher/lower TFs
        """
        self.tf_map = timeframe_mapping

    def calculate(self, df: pd.DataFrame, current_timeframe: str) -> Dict[str, Optional[float]]:
        """
        Calculate multi-timeframe features (simplified)

        Args:
            df: DataFrame with OHLC data
            current_timeframe: Current timeframe string

        Returns:
            Dictionary with 10 multi-TF features
        """
        features = {
            'htf_trend_direction': None,
            'htf_rsi': None,
            'htf_macd': None,
            'htf_sma_50': None,
            'ltf_volatility': None,
            'ltf_volume': None,
            'is_all_tf_aligned': 0,
            'tf_alignment_score': 0.0,
            'htf_support_level': None,
            'htf_resistance_level': None
        }

        # Simplified: Use same timeframe data for Phase 1
        # TODO: Implement actual multi-TF queries in Phase 2
        if df.empty or len(df) < 20:
            return features

        try:
            close = df['close'].values
            high = df['high'].values
            low = df['low'].values

            # Simplified HTF trend (using current TF's longer MA)
            if len(close) >= 50:
                sma_50 = np.mean(close[-50:])
                features['htf_sma_50'] = float(sma_50)

                # Trend direction
                if close[-1] > sma_50:
                    features['htf_trend_direction'] = 'up'
                elif close[-1] < sma_50:
                    features['htf_trend_direction'] = 'down'
                else:
                    features['htf_trend_direction'] = 'sideways'

            # Support/Resistance from recent highs/lows
            if len(high) >= 20 and len(low) >= 20:
                features['htf_support_level'] = float(np.min(low[-20:]))
                features['htf_resistance_level'] = float(np.max(high[-20:]))

            # Simplified alignment score
            features['tf_alignment_score'] = 0.5  # Neutral for Phase 1

        except Exception as e:
            print(f"Error calculating multi-timeframe features: {e}")

        return features
