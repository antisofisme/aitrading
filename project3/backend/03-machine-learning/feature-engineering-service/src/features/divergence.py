"""
Divergence Features (4 features - 10% importance)

Features:
1. rsi_price_divergence
2. macd_price_divergence
3. volume_price_divergence
4. divergence_strength
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any
import json

logger = logging.getLogger(__name__)


class DivergenceFeatures:
    """Calculate divergence features"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config['feature_groups']['divergence']
        self.lookback_periods = self.config.get('lookback_periods', 10)

    def calculate(self, candle: pd.Series, h1_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate all divergence features"""
        features = {}

        # Parse indicators from candle
        indicators = self._parse_indicators(candle)

        # 1. RSI/Price divergence
        features['rsi_price_divergence'] = self._detect_rsi_divergence(h1_data)

        # 2. MACD/Price divergence
        features['macd_price_divergence'] = self._detect_macd_divergence(h1_data)

        # 3. Volume/Price divergence
        features['volume_price_divergence'] = self._detect_volume_divergence(h1_data)

        # 4. Divergence strength (combined score)
        features['divergence_strength'] = self._calc_divergence_strength(features)

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

    def _detect_rsi_divergence(self, h1_data: pd.DataFrame) -> int:
        """
        Detect RSI/Price divergence
        Returns: 1=bullish divergence, -1=bearish divergence, 0=no divergence
        """
        if h1_data.empty or len(h1_data) < self.lookback_periods:
            return 0

        try:
            recent = h1_data.tail(self.lookback_periods)

            # Price trend
            price_first = recent['close'].iloc[0]
            price_last = recent['close'].iloc[-1]
            price_trend = 1 if price_last > price_first else -1

            # RSI trend (from indicators)
            rsi_values = []
            for idx, row in recent.iterrows():
                indicators = self._parse_indicators(row)
                rsi = indicators.get('rsi', 50)
                rsi_values.append(rsi)

            if len(rsi_values) < 2:
                return 0

            rsi_first = rsi_values[0]
            rsi_last = rsi_values[-1]
            rsi_trend = 1 if rsi_last > rsi_first else -1

            # Divergence detection
            if price_trend == -1 and rsi_trend == 1:
                return 1  # Bullish divergence (price down, RSI up)
            elif price_trend == 1 and rsi_trend == -1:
                return -1  # Bearish divergence (price up, RSI down)

        except:
            pass

        return 0

    def _detect_macd_divergence(self, h1_data: pd.DataFrame) -> int:
        """
        Detect MACD/Price divergence
        Returns: 1=bullish divergence, -1=bearish divergence, 0=no divergence
        """
        if h1_data.empty or len(h1_data) < self.lookback_periods:
            return 0

        try:
            recent = h1_data.tail(self.lookback_periods)

            # Price trend
            price_first = recent['close'].iloc[0]
            price_last = recent['close'].iloc[-1]
            price_trend = 1 if price_last > price_first else -1

            # MACD trend (from indicators)
            macd_values = []
            for idx, row in recent.iterrows():
                indicators = self._parse_indicators(row)
                macd = indicators.get('macd', 0)
                macd_values.append(macd)

            if len(macd_values) < 2:
                return 0

            macd_first = macd_values[0]
            macd_last = macd_values[-1]
            macd_trend = 1 if macd_last > macd_first else -1

            # Divergence detection
            if price_trend == -1 and macd_trend == 1:
                return 1  # Bullish divergence
            elif price_trend == 1 and macd_trend == -1:
                return -1  # Bearish divergence

        except:
            pass

        return 0

    def _detect_volume_divergence(self, h1_data: pd.DataFrame) -> int:
        """
        Detect Volume/Price divergence
        Returns: 1=bullish divergence, -1=bearish divergence, 0=no divergence
        """
        if h1_data.empty or len(h1_data) < self.lookback_periods:
            return 0

        try:
            recent = h1_data.tail(self.lookback_periods)

            # Price trend
            price_slope = (recent['close'].iloc[-1] - recent['close'].iloc[0]) / self.lookback_periods

            # Volume trend
            volume_slope = (recent['volume'].iloc[-1] - recent['volume'].iloc[0]) / self.lookback_periods

            # Divergence: price up + volume down = bearish divergence (weak move)
            if price_slope > 0 and volume_slope < 0:
                return -1  # Bearish divergence
            elif price_slope < 0 and volume_slope > 0:
                return 1  # Bullish divergence (selling climax)

        except:
            pass

        return 0

    def _calc_divergence_strength(self, features: Dict[str, int]) -> float:
        """
        Calculate overall divergence strength
        Returns: Score from -3 to +3 (sum of all divergences)
        """
        try:
            rsi_div = features.get('rsi_price_divergence', 0)
            macd_div = features.get('macd_price_divergence', 0)
            volume_div = features.get('volume_price_divergence', 0)

            strength = rsi_div + macd_div + volume_div

            return float(strength)
        except:
            return 0.0
