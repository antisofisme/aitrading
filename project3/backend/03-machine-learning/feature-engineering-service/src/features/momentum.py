"""
Momentum Indicator Features (3 features - 5% importance)

Features:
1. rsi_value
2. macd_histogram
3. stochastic_k
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any
import json

logger = logging.getLogger(__name__)


class MomentumFeatures:
    """Calculate momentum indicator features"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config['feature_groups']['momentum_indicators']
        self.rsi_period = self.config.get('rsi_period', 14)
        self.stoch_period = self.config.get('stochastic_period', 14)

    def calculate(self, candle: pd.Series, h1_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate all momentum features"""
        features = {}

        # Parse indicators from candle
        indicators = self._parse_indicators(candle)

        # 1. RSI value (already calculated in aggregates)
        features['rsi_value'] = indicators.get('rsi', 50.0)

        # 2. MACD histogram (already calculated in aggregates)
        features['macd_histogram'] = indicators.get('macd', 0.0)

        # 3. Stochastic %K (calculate from H1 data)
        features['stochastic_k'] = self._calc_stochastic_k(h1_data)

        return features

    def _parse_indicators(self, candle: pd.Series) -> dict:
        """Parse indicators JSON from candle"""
        try:
            indicators_str = candle.get('indicators', '{}')
            if isinstance(indicators_str, str):
                return json.loads(indicators_str)
            elif isinstance(indicators_str, dict):
                return indicators_str
        except:
            pass

        return {}

    def _calc_stochastic_k(self, h1_data: pd.DataFrame) -> float:
        """
        Calculate Stochastic %K
        Formula: %K = (Current Close - Lowest Low) / (Highest High - Lowest Low) * 100
        """
        if h1_data.empty or len(h1_data) < self.stoch_period:
            return 50.0

        try:
            # Get last N periods
            recent = h1_data.tail(self.stoch_period + 1)

            # Current close
            current_close = recent['close'].iloc[-1]

            # Highest high and lowest low over period
            highest_high = recent['high'].max()
            lowest_low = recent['low'].min()

            if highest_high - lowest_low > 0:
                stoch_k = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100
                return round(stoch_k, 2)

        except:
            pass

        return 50.0
