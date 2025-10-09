"""
Structure-Based SL/TP Features (5 features - 5% importance)

Features:
1. nearest_support_distance
2. nearest_resistance_distance
3. structure_risk_reward
4. atr_based_sl_distance
5. structure_based_tp_distance
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any
import json

logger = logging.getLogger(__name__)


class StructureSLTPFeatures:
    """Calculate structure-based SL/TP features"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config['feature_groups']['structure_sl_tp']
        self.lookback_candles = self.config.get('lookback_candles', 50)
        self.atr_multiplier = self.config.get('atr_multiplier', 1.5)
        self.min_rr_ratio = self.config.get('min_risk_reward', 2.0)

    def calculate(self, candle: pd.Series, h1_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate all structure-based SL/TP features"""
        features = {}

        current_price = float(candle['close'])

        # Parse indicators from candle
        indicators = self._parse_indicators(candle)

        # 1. Nearest support distance (pips)
        features['nearest_support_distance'] = self._calc_support_distance(current_price, h1_data)

        # 2. Nearest resistance distance (pips)
        features['nearest_resistance_distance'] = self._calc_resistance_distance(current_price, h1_data)

        # 3. Structure risk/reward ratio
        features['structure_risk_reward'] = self._calc_structure_rr(
            features['nearest_support_distance'],
            features['nearest_resistance_distance']
        )

        # 4. ATR-based SL distance (pips)
        features['atr_based_sl_distance'] = self._calc_atr_sl(indicators)

        # 5. Structure-based TP distance (pips)
        features['structure_based_tp_distance'] = self._calc_structure_tp(
            features['atr_based_sl_distance'],
            features['nearest_resistance_distance']
        )

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

    def _calc_support_distance(self, current_price: float, h1_data: pd.DataFrame) -> float:
        """Calculate distance to nearest support level (pips)"""
        if h1_data.empty or len(h1_data) < 20:
            return 100.0  # Default 100 pips

        try:
            # Get recent swing lows
            recent = h1_data.tail(self.lookback_candles)
            lows = recent['low'].values

            # Find swing lows (local minima)
            swing_lows = []
            for i in range(2, len(lows) - 2):
                if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
                   lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                    swing_lows.append(lows[i])

            # Find nearest support below current price
            supports_below = [s for s in swing_lows if s < current_price]

            if supports_below:
                nearest_support = max(supports_below)
                distance_pips = (current_price - nearest_support) * 10000
                return round(distance_pips, 1)

        except:
            pass

        return 100.0  # Default

    def _calc_resistance_distance(self, current_price: float, h1_data: pd.DataFrame) -> float:
        """Calculate distance to nearest resistance level (pips)"""
        if h1_data.empty or len(h1_data) < 20:
            return 100.0  # Default 100 pips

        try:
            # Get recent swing highs
            recent = h1_data.tail(self.lookback_candles)
            highs = recent['high'].values

            # Find swing highs (local maxima)
            swing_highs = []
            for i in range(2, len(highs) - 2):
                if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
                   highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                    swing_highs.append(highs[i])

            # Find nearest resistance above current price
            resistances_above = [r for r in swing_highs if r > current_price]

            if resistances_above:
                nearest_resistance = min(resistances_above)
                distance_pips = (nearest_resistance - current_price) * 10000
                return round(distance_pips, 1)

        except:
            pass

        return 100.0  # Default

    def _calc_structure_rr(self, support_distance: float, resistance_distance: float) -> float:
        """
        Calculate structure-based risk/reward ratio
        RR = (Distance to TP) / (Distance to SL)
        """
        try:
            if support_distance > 0:
                rr_ratio = resistance_distance / support_distance
                return round(rr_ratio, 2)
        except:
            pass

        return 1.0

    def _calc_atr_sl(self, indicators: dict) -> float:
        """
        Calculate ATR-based stop loss distance (pips)
        SL = ATR * multiplier (typically 1.5x)
        """
        try:
            atr = indicators.get('atr', 0)
            if atr > 0:
                sl_distance = atr * self.atr_multiplier * 10000  # Convert to pips
                return round(sl_distance, 1)
        except:
            pass

        return 50.0  # Default 50 pips

    def _calc_structure_tp(self, atr_sl: float, resistance_distance: float) -> float:
        """
        Calculate structure-based take profit distance (pips)
        TP = min(resistance_distance, atr_sl * min_rr_ratio)
        """
        try:
            # ATR-based TP (minimum 2:1 RR)
            atr_tp = atr_sl * self.min_rr_ratio

            # Use nearest of: structure resistance or ATR-based TP
            tp_distance = min(resistance_distance, atr_tp)

            return round(tp_distance, 1)
        except:
            pass

        return 100.0  # Default 100 pips
