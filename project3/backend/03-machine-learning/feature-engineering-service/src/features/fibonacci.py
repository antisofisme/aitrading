"""
Fibonacci Retracement & Extension Features (9 features - 8% importance)

Based on: FIBONACCI_ANALYSIS_AND_INTEGRATION.md

Features:
1. fib_current_level (Float 0-1)
2. fib_distance_to_golden_zone (Float pips)
3. is_in_golden_zone (Boolean)
4. fib_level_strength (Integer 0-5)
5. fib_confluence_score (Integer 0-3)
6. fib_timeframe_alignment (Integer 0-3)
7. fib_extension_target_1272 (Float price)
8. fib_extension_target_1618 (Float price)
9. distance_to_nearest_extension (Float pips)
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)


class FibonacciFeatures:
    """Calculate Fibonacci retracement and extension features"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config['feature_groups'].get('fibonacci', {})
        self.swing_lookback = self.config.get('swing_lookback_candles', 10)
        self.golden_zone_lower = 0.50  # 50% retracement
        self.golden_zone_upper = 0.618  # 61.8% retracement
        self.confluence_tolerance_pips = 10

    def calculate(self, candle: pd.Series, multi_tf_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Calculate all Fibonacci features"""
        features = {}

        h1_data = multi_tf_data.get('1h', pd.DataFrame())
        h4_data = multi_tf_data.get('4h', pd.DataFrame())
        d1_data = multi_tf_data.get('1d', pd.DataFrame())

        current_price = float(candle.get('close', 0))

        # Detect swing points on H1 (primary timeframe)
        swing_high, swing_low, is_uptrend = self._detect_swing_points(h1_data)

        if swing_high is None or swing_low is None:
            # No valid swing detected - return zero values
            return self._default_features()

        # Calculate Fibonacci levels
        fib_levels, fib_extensions, golden_zone = self._calculate_fibonacci_levels(
            swing_high, swing_low, is_uptrend
        )

        # 1. Current Fibonacci level (0-1)
        features['fib_current_level'] = self._calc_current_fib_level(
            current_price, swing_high, swing_low
        )

        # 2. Distance to Golden Zone (pips)
        features['fib_distance_to_golden_zone'] = self._calc_distance_to_golden_zone(
            current_price, golden_zone
        )

        # 3. Is in Golden Zone (Boolean)
        features['is_in_golden_zone'] = 1 if self._is_in_golden_zone(
            features['fib_current_level']
        ) else 0

        # 4. Fibonacci level strength (0-5)
        features['fib_level_strength'] = self._calc_fib_level_strength(
            current_price, fib_levels, h1_data
        )

        # 5. Confluence score (0-3)
        features['fib_confluence_score'] = self._calc_confluence_score(
            current_price, fib_levels, candle
        )

        # 6. Multi-timeframe alignment (0-3)
        features['fib_timeframe_alignment'] = self._calc_multi_tf_alignment(
            current_price, h1_data, h4_data, d1_data
        )

        # 7. Fibonacci extension 127.2% (price)
        features['fib_extension_target_1272'] = fib_extensions['ext_1272']

        # 8. Fibonacci extension 161.8% (price)
        features['fib_extension_target_1618'] = fib_extensions['ext_1618']

        # 9. Distance to nearest extension (pips)
        features['distance_to_nearest_extension'] = self._calc_distance_to_extension(
            current_price, fib_extensions
        )

        return features

    def _detect_swing_points(
        self,
        data: pd.DataFrame,
        lookback: int = None
    ) -> Tuple[Optional[float], Optional[float], bool]:
        """
        Detect significant swing high and low using pivot points

        Returns:
            (swing_high, swing_low, is_uptrend)
        """
        if data.empty or len(data) < 10:
            return None, None, True

        lookback = lookback or self.swing_lookback

        # Simple swing detection: highest high and lowest low in lookback period
        recent_data = data.tail(lookback)

        swing_high = recent_data['high'].max()
        swing_low = recent_data['low'].min()

        # Determine trend: if close > midpoint, uptrend
        current_close = data.iloc[-1]['close']
        midpoint = (swing_high + swing_low) / 2
        is_uptrend = current_close > midpoint

        return swing_high, swing_low, is_uptrend

    def _calculate_fibonacci_levels(
        self,
        swing_high: float,
        swing_low: float,
        is_uptrend: bool
    ) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float]]:
        """
        Calculate Fibonacci retracement and extension levels

        Uptrend: Draw from swing_low to swing_high (retracement from high)
        Downtrend: Draw from swing_high to swing_low (retracement from low)
        """
        price_range = swing_high - swing_low

        # Fibonacci retracement levels
        if is_uptrend:
            # Uptrend: retracement from swing_high down
            fib_levels = {
                'fib_0': swing_high,                                    # 0%
                'fib_236': swing_high - (price_range * 0.236),         # 23.6%
                'fib_382': swing_high - (price_range * 0.382),         # 38.2%
                'fib_50': swing_high - (price_range * 0.5),            # 50%
                'fib_618': swing_high - (price_range * 0.618),         # 61.8% (Golden)
                'fib_786': swing_high - (price_range * 0.786),         # 78.6%
                'fib_100': swing_low                                    # 100%
            }
            # Extension levels (profit targets above swing_high)
            fib_extensions = {
                'ext_1272': swing_high + (price_range * 0.272),        # 127.2%
                'ext_1414': swing_high + (price_range * 0.414),        # 141.4%
                'ext_1618': swing_high + (price_range * 0.618),        # 161.8% (Golden)
                'ext_2000': swing_high + (price_range * 1.0)           # 200%
            }
        else:
            # Downtrend: retracement from swing_low up
            fib_levels = {
                'fib_0': swing_low,                                     # 0%
                'fib_236': swing_low + (price_range * 0.236),          # 23.6%
                'fib_382': swing_low + (price_range * 0.382),          # 38.2%
                'fib_50': swing_low + (price_range * 0.5),             # 50%
                'fib_618': swing_low + (price_range * 0.618),          # 61.8% (Golden)
                'fib_786': swing_low + (price_range * 0.786),          # 78.6%
                'fib_100': swing_high                                   # 100%
            }
            # Extension levels (profit targets below swing_low)
            fib_extensions = {
                'ext_1272': swing_low - (price_range * 0.272),         # 127.2%
                'ext_1414': swing_low - (price_range * 0.414),         # 141.4%
                'ext_1618': swing_low - (price_range * 0.618),         # 161.8% (Golden)
                'ext_2000': swing_low - (price_range * 1.0)            # 200%
            }

        # Golden Zone boundaries
        golden_zone = {
            'upper': fib_levels['fib_50'],
            'lower': fib_levels['fib_618'],
            'mid': (fib_levels['fib_50'] + fib_levels['fib_618']) / 2
        }

        return fib_levels, fib_extensions, golden_zone

    def _calc_current_fib_level(
        self,
        current_price: float,
        swing_high: float,
        swing_low: float
    ) -> float:
        """
        Calculate current Fibonacci level (0-1)

        0 = at swing_low, 1 = at swing_high
        """
        price_range = swing_high - swing_low
        if price_range == 0:
            return 0.5

        fib_level = (current_price - swing_low) / price_range
        return float(np.clip(fib_level, 0, 1))

    def _calc_distance_to_golden_zone(
        self,
        current_price: float,
        golden_zone: Dict[str, float]
    ) -> float:
        """Calculate distance to Golden Zone in pips"""
        upper = golden_zone['upper']
        lower = golden_zone['lower']

        if lower <= current_price <= upper:
            # Inside Golden Zone
            return 0.0

        # Distance to nearest boundary
        distance_to_upper = abs(current_price - upper)
        distance_to_lower = abs(current_price - lower)
        distance = min(distance_to_upper, distance_to_lower)

        return float(distance * 10000)  # Convert to pips

    def _is_in_golden_zone(self, fib_level: float) -> bool:
        """Check if current Fibonacci level is in Golden Zone (50%-61.8%)"""
        return self.golden_zone_lower <= fib_level <= self.golden_zone_upper

    def _calc_fib_level_strength(
        self,
        current_price: float,
        fib_levels: Dict[str, float],
        data: pd.DataFrame
    ) -> int:
        """
        Calculate strength of nearest Fibonacci level (0-5)

        Based on historical respect count (touches without breaking)
        """
        if data.empty or len(data) < 20:
            return 0

        # Find nearest Fibonacci level
        levels = list(fib_levels.values())
        distances = [abs(current_price - level) for level in levels]
        nearest_level = levels[np.argmin(distances)]

        # Count touches in last 50 candles
        tolerance = nearest_level * 0.001  # 0.1% tolerance
        recent_data = data.tail(50)

        touches = 0
        for _, candle in recent_data.iterrows():
            high = candle['high']
            low = candle['low']

            # Check if level was touched
            if low <= nearest_level + tolerance and high >= nearest_level - tolerance:
                touches += 1

        # Strength score: 0-5 (capped at 5)
        return min(touches, 5)

    def _calc_confluence_score(
        self,
        current_price: float,
        fib_levels: Dict[str, float],
        candle: pd.Series
    ) -> int:
        """
        Calculate confluence score (0-3)

        Checks if Fibonacci level overlaps with:
        1. Support/Resistance level (within tolerance)
        2. Order block zone
        3. Round number (2650, 2700, etc)
        """
        score = 0

        # Find nearest Fibonacci level
        levels = list(fib_levels.values())
        distances = [abs(current_price - level) for level in levels]
        nearest_fib = levels[np.argmin(distances)]

        tolerance_pips = self.confluence_tolerance_pips / 10000

        # 1. Check for SR confluence (simplified - would need SR data)
        # For now, check if near swing high/low
        candle_high = float(candle.get('high', 0))
        candle_low = float(candle.get('low', 0))

        if abs(nearest_fib - candle_high) < tolerance_pips or \
           abs(nearest_fib - candle_low) < tolerance_pips:
            score += 1

        # 2. Check for order block confluence (would need order block detection)
        # Placeholder - always add 0 for now
        score += 0

        # 3. Check for round number confluence
        round_numbers = [
            2600, 2650, 2700, 2750, 2800, 2850, 2900, 2950, 3000,
            3050, 3100, 3150, 3200, 3250, 3300, 3350, 3400, 3450,
            3500, 3550, 3600, 3650, 3700, 3750, 3800, 3850, 3900,
            3950, 4000, 4050, 4100, 4150, 4200
        ]

        for round_num in round_numbers:
            if abs(nearest_fib - round_num) < tolerance_pips:
                score += 1
                break

        return min(score, 3)

    def _calc_multi_tf_alignment(
        self,
        current_price: float,
        h1_data: pd.DataFrame,
        h4_data: pd.DataFrame,
        d1_data: pd.DataFrame
    ) -> int:
        """
        Calculate multi-timeframe Fibonacci alignment (0-3)

        Checks if Fibonacci levels from H1, H4, D1 align near same price
        """
        alignment_score = 0
        tolerance_pips = self.confluence_tolerance_pips / 10000

        timeframes_data = {
            'H1': h1_data,
            'H4': h4_data,
            'D1': d1_data
        }

        fib_levels_by_tf = {}

        for tf_name, tf_data in timeframes_data.items():
            if tf_data.empty:
                continue

            swing_high, swing_low, is_uptrend = self._detect_swing_points(tf_data)

            if swing_high is None or swing_low is None:
                continue

            fib_levels, _, _ = self._calculate_fibonacci_levels(
                swing_high, swing_low, is_uptrend
            )

            # Find nearest Fibonacci level to current price
            levels = list(fib_levels.values())
            distances = [abs(current_price - level) for level in levels]
            nearest_level = levels[np.argmin(distances)]

            fib_levels_by_tf[tf_name] = nearest_level

        # Check alignment between timeframes
        if len(fib_levels_by_tf) >= 2:
            tf_levels = list(fib_levels_by_tf.values())

            # Check if all levels are within tolerance
            max_diff = max(tf_levels) - min(tf_levels)

            if max_diff < tolerance_pips:
                alignment_score = len(fib_levels_by_tf)

        return min(alignment_score, 3)

    def _calc_distance_to_extension(
        self,
        current_price: float,
        fib_extensions: Dict[str, float]
    ) -> float:
        """Calculate distance to nearest extension level in pips"""
        ext_1272 = fib_extensions['ext_1272']
        ext_1618 = fib_extensions['ext_1618']

        distance_1272 = abs(current_price - ext_1272)
        distance_1618 = abs(current_price - ext_1618)

        nearest_distance = min(distance_1272, distance_1618)

        return float(nearest_distance * 10000)  # Convert to pips

    def _default_features(self) -> Dict[str, Any]:
        """Return default zero values when Fibonacci calculation fails"""
        return {
            'fib_current_level': 0.0,
            'fib_distance_to_golden_zone': 0.0,
            'is_in_golden_zone': 0,
            'fib_level_strength': 0,
            'fib_confluence_score': 0,
            'fib_timeframe_alignment': 0,
            'fib_extension_target_1272': 0.0,
            'fib_extension_target_1618': 0.0,
            'distance_to_nearest_extension': 0.0
        }
