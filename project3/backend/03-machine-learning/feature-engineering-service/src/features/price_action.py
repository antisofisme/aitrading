"""
Price Action & Structure Features (10 features - 18% importance)

Features:
1. support_resistance_distance
2. is_at_key_level
3. order_block_zone
4. swing_high_low_distance
5. price_rejection_wick
6. h4_trend_direction
7. h4_support_resistance_distance
8. d1_support_resistance_distance
9. w1_swing_high_low
10. multi_tf_alignment
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any

logger = logging.getLogger(__name__)


class PriceActionFeatures:
    """Calculate price action and structure-based features"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config['feature_groups']['price_action']
        self.sr_tolerance_pips = self.config.get('sr_tolerance_pips', 10)
        self.swing_lookback = self.config.get('swing_lookback_candles', 50)

    def calculate(self, candle: pd.Series, multi_tf_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Calculate all price action features"""
        features = {}

        h1_data = multi_tf_data.get('1h', pd.DataFrame())
        h4_data = multi_tf_data.get('4h', pd.DataFrame())
        d1_data = multi_tf_data.get('1d', pd.DataFrame())
        w1_data = multi_tf_data.get('1w', pd.DataFrame())

        current_price = float(candle.get('close', 0))

        # 1. Support/Resistance Distance (H1)
        features['support_resistance_distance'] = self._calc_sr_distance(
            current_price, h1_data
        )

        # 2. Is at key level (within tolerance)
        features['is_at_key_level'] = 1 if abs(features['support_resistance_distance']) < self.sr_tolerance_pips else 0

        # 3. Order block zone
        features['order_block_zone'] = self._detect_order_block(current_price, h1_data)

        # 4. Swing high/low distance
        features['swing_high_low_distance'] = self._calc_swing_distance(current_price, h1_data)

        # 5. Price rejection wick (%)
        features['price_rejection_wick'] = self._calc_rejection_wick(candle)

        # 6. H4 trend direction
        features['h4_trend_direction'] = self._calc_trend_direction(h4_data)

        # 7. H4 SR distance
        features['h4_support_resistance_distance'] = self._calc_sr_distance(current_price, h4_data)

        # 8. D1 SR distance
        features['d1_support_resistance_distance'] = self._calc_sr_distance(current_price, d1_data)

        # 9. W1 swing high/low
        features['w1_swing_high_low'] = self._calc_swing_level(current_price, w1_data)

        # 10. Multi-TF alignment (0-6 score)
        features['multi_tf_alignment'] = self._calc_tf_alignment(multi_tf_data)

        return features

    def _calc_sr_distance(self, current_price: float, data: pd.DataFrame) -> float:
        """Calculate distance to nearest support/resistance"""
        if data.empty:
            return 0.0

        # Find swing highs and lows (simplified)
        highs = data['high'].rolling(window=3, center=True).max()
        lows = data['low'].rolling(window=3, center=True).min()

        swing_highs = data[data['high'] == highs]['high'].values
        swing_lows = data[data['low'] == lows]['low'].values

        if len(swing_highs) == 0 and len(swing_lows) == 0:
            return 0.0

        # Find nearest level
        all_levels = np.concatenate([swing_highs, swing_lows])
        distances = all_levels - current_price
        nearest_distance = distances[np.argmin(np.abs(distances))]

        return float(nearest_distance * 10000)  # Convert to pips

    def _detect_order_block(self, current_price: float, data: pd.DataFrame) -> int:
        """Detect if price is in order block zone"""
        # Simplified: Check for consolidation before big move
        if data.empty or len(data) < 20:
            return 0

        # Look for consolidation (low volatility) followed by impulsive move
        recent_data = data.tail(20)
        ranges = (recent_data['high'] - recent_data['low']).values

        # Consolidation: low range
        consolidation_indices = np.where(ranges < np.percentile(ranges, 30))[0]

        if len(consolidation_indices) > 0:
            # Check if followed by impulsive move
            last_consolidation = consolidation_indices[-1]
            if last_consolidation < len(ranges) - 2:
                impulsive_range = ranges[last_consolidation + 1]
                if impulsive_range > np.percentile(ranges, 70):
                    # Order block detected
                    ob_level = float(recent_data.iloc[last_consolidation]['close'])
                    if abs(current_price - ob_level) < 20:  # Within 20 pips
                        return 1

        return 0

    def _calc_swing_distance(self, current_price: float, data: pd.DataFrame) -> float:
        """Calculate distance to nearest swing point"""
        if data.empty:
            return 0.0

        # Simplified swing detection
        swing_highs = data['high'].rolling(window=5, center=True).max()
        swing_lows = data['low'].rolling(window=5, center=True).min()

        recent_swing_high = data[data['high'] == swing_highs].tail(1)['high'].values
        recent_swing_low = data[data['low'] == swing_lows].tail(1)['low'].values

        if len(recent_swing_high) > 0:
            return float((recent_swing_high[0] - current_price) * 10000)
        elif len(recent_swing_low) > 0:
            return float((current_price - recent_swing_low[0]) * 10000)

        return 0.0

    def _calc_rejection_wick(self, candle: pd.Series) -> float:
        """Calculate wick length as % of candle range"""
        try:
            high = float(candle['high'])
            low = float(candle['low'])
            close = float(candle['close'])
            open_price = float(candle['open'])

            candle_range = high - low
            if candle_range == 0:
                return 0.0

            # Upper wick
            upper_wick = high - max(open_price, close)
            # Lower wick
            lower_wick = min(open_price, close) - low

            # Return longest wick as % of range
            max_wick = max(upper_wick, lower_wick)
            return float((max_wick / candle_range) * 100)

        except:
            return 0.0

    def _calc_trend_direction(self, data: pd.DataFrame) -> int:
        """Calculate trend direction: 1=up, 0=neutral, -1=down"""
        if data.empty or len(data) < 50:
            return 0

        # Use EMA_50 slope
        try:
            recent_data = data.tail(50)
            ema_50 = recent_data['close'].ewm(span=50).mean()

            slope = (ema_50.iloc[-1] - ema_50.iloc[-10]) / 10

            if slope > 0.0001:
                return 1  # Uptrend
            elif slope < -0.0001:
                return -1  # Downtrend
            else:
                return 0  # Neutral

        except:
            return 0

    def _calc_swing_level(self, current_price: float, data: pd.DataFrame) -> float:
        """Get W1 swing level"""
        if data.empty:
            return current_price

        # Return most recent swing high or low
        recent_high = data.tail(10)['high'].max()
        recent_low = data.tail(10)['low'].min()

        # Return nearest
        if abs(current_price - recent_high) < abs(current_price - recent_low):
            return float(recent_high)
        else:
            return float(recent_low)

    def _calc_tf_alignment(self, multi_tf_data: Dict[str, pd.DataFrame]) -> int:
        """Calculate multi-timeframe alignment score (0-6)"""
        timeframes = ['5m', '15m', '1h', '4h', '1d', '1w']
        aligned_count = 0

        trends = []
        for tf in timeframes:
            data = multi_tf_data.get(tf, pd.DataFrame())
            trend = self._calc_trend_direction(data)
            trends.append(trend)

        # Count how many agree on direction
        if len(set(trends)) == 1 and trends[0] != 0:
            # All same direction
            aligned_count = 6
        else:
            # Count majority
            up_count = sum(1 for t in trends if t == 1)
            down_count = sum(1 for t in trends if t == -1)
            aligned_count = max(up_count, down_count)

        return aligned_count
