"""
Candlestick Pattern Features (9 features - 15% importance)

Features:
1. bullish_engulfing
2. bearish_engulfing
3. pin_bar_bullish
4. pin_bar_bearish
5. doji_indecision
6. hammer_reversal
7. shooting_star
8. morning_star
9. evening_star
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any

logger = logging.getLogger(__name__)


class CandlestickPatternFeatures:
    """Calculate candlestick pattern features"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config['feature_groups']['candlestick_patterns']

    def calculate(self, candle: pd.Series, h1_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate all candlestick pattern features"""
        features = {}

        # Get last 3 candles for pattern recognition
        if not h1_data.empty and len(h1_data) >= 3:
            last_3 = h1_data.tail(3)
            prev2 = last_3.iloc[0] if len(last_3) > 0 else candle
            prev1 = last_3.iloc[1] if len(last_3) > 1 else candle
            current = last_3.iloc[2] if len(last_3) > 2 else candle
        else:
            prev2 = prev1 = current = candle

        # 1. Bullish Engulfing
        features['bullish_engulfing'] = self._is_bullish_engulfing(prev1, current)

        # 2. Bearish Engulfing
        features['bearish_engulfing'] = self._is_bearish_engulfing(prev1, current)

        # 3. Pin Bar Bullish
        features['pin_bar_bullish'] = self._is_pin_bar_bullish(current)

        # 4. Pin Bar Bearish
        features['pin_bar_bearish'] = self._is_pin_bar_bearish(current)

        # 5. Doji (indecision)
        features['doji_indecision'] = self._is_doji(current)

        # 6. Hammer (bullish reversal)
        features['hammer_reversal'] = self._is_hammer(current)

        # 7. Shooting Star (bearish reversal)
        features['shooting_star'] = self._is_shooting_star(current)

        # 8. Morning Star (3-candle bullish)
        features['morning_star'] = self._is_morning_star(prev2, prev1, current)

        # 9. Evening Star (3-candle bearish)
        features['evening_star'] = self._is_evening_star(prev2, prev1, current)

        return features

    def _is_bullish_engulfing(self, prev: pd.Series, current: pd.Series) -> int:
        """Bullish engulfing pattern"""
        try:
            prev_open = float(prev['open'])
            prev_close = float(prev['close'])
            curr_open = float(current['open'])
            curr_close = float(current['close'])

            # Prev is bearish, current is bullish
            prev_bearish = prev_close < prev_open
            curr_bullish = curr_close > curr_open

            # Current engulfs previous
            engulfs = curr_open < prev_close and curr_close > prev_open

            if prev_bearish and curr_bullish and engulfs:
                return 1
        except:
            pass

        return 0

    def _is_bearish_engulfing(self, prev: pd.Series, current: pd.Series) -> int:
        """Bearish engulfing pattern"""
        try:
            prev_open = float(prev['open'])
            prev_close = float(prev['close'])
            curr_open = float(current['open'])
            curr_close = float(current['close'])

            # Prev is bullish, current is bearish
            prev_bullish = prev_close > prev_open
            curr_bearish = curr_close < curr_open

            # Current engulfs previous
            engulfs = curr_open > prev_close and curr_close < prev_open

            if prev_bullish and curr_bearish and engulfs:
                return 1
        except:
            pass

        return 0

    def _is_pin_bar_bullish(self, candle: pd.Series) -> int:
        """Bullish pin bar (long lower wick)"""
        try:
            high = float(candle['high'])
            low = float(candle['low'])
            close = float(candle['close'])
            open_price = float(candle['open'])

            body = abs(close - open_price)
            total_range = high - low
            lower_wick = min(close, open_price) - low

            if total_range > 0:
                # Lower wick > 2x body
                if lower_wick > body * 2:
                    return 1
        except:
            pass

        return 0

    def _is_pin_bar_bearish(self, candle: pd.Series) -> int:
        """Bearish pin bar (long upper wick)"""
        try:
            high = float(candle['high'])
            low = float(candle['low'])
            close = float(candle['close'])
            open_price = float(candle['open'])

            body = abs(close - open_price)
            total_range = high - low
            upper_wick = high - max(close, open_price)

            if total_range > 0:
                # Upper wick > 2x body
                if upper_wick > body * 2:
                    return 1
        except:
            pass

        return 0

    def _is_doji(self, candle: pd.Series) -> int:
        """Doji pattern (open ≈ close)"""
        try:
            close = float(candle['close'])
            open_price = float(candle['open'])
            high = float(candle['high'])
            low = float(candle['low'])

            body = abs(close - open_price)
            total_range = high - low

            if total_range > 0:
                # Body < 10% of total range
                if (body / total_range) < 0.1:
                    return 1
        except:
            pass

        return 0

    def _is_hammer(self, candle: pd.Series) -> int:
        """Hammer pattern (bullish reversal)"""
        try:
            high = float(candle['high'])
            low = float(candle['low'])
            close = float(candle['close'])
            open_price = float(candle['open'])

            body = abs(close - open_price)
            total_range = high - low
            lower_wick = min(close, open_price) - low
            upper_wick = high - max(close, open_price)

            if total_range > 0:
                # Long lower wick, small body, minimal upper wick
                if lower_wick > body * 2 and upper_wick < body * 0.5:
                    return 1
        except:
            pass

        return 0

    def _is_shooting_star(self, candle: pd.Series) -> int:
        """Shooting star pattern (bearish reversal)"""
        try:
            high = float(candle['high'])
            low = float(candle['low'])
            close = float(candle['close'])
            open_price = float(candle['open'])

            body = abs(close - open_price)
            total_range = high - low
            lower_wick = min(close, open_price) - low
            upper_wick = high - max(close, open_price)

            if total_range > 0:
                # Long upper wick, small body, minimal lower wick
                if upper_wick > body * 2 and lower_wick < body * 0.5:
                    return 1
        except:
            pass

        return 0

    def _is_morning_star(self, c1: pd.Series, c2: pd.Series, c3: pd.Series) -> int:
        """Morning star (3-candle bullish reversal)"""
        try:
            # C1: Bearish
            c1_bearish = float(c1['close']) < float(c1['open'])

            # C2: Small body (doji-like)
            c2_body = abs(float(c2['close']) - float(c2['open']))
            c2_range = float(c2['high']) - float(c2['low'])
            c2_small = (c2_body / c2_range) < 0.3 if c2_range > 0 else False

            # C3: Bullish
            c3_bullish = float(c3['close']) > float(c3['open'])

            if c1_bearish and c2_small and c3_bullish:
                return 1
        except:
            pass

        return 0

    def _is_evening_star(self, c1: pd.Series, c2: pd.Series, c3: pd.Series) -> int:
        """Evening star (3-candle bearish reversal)"""
        try:
            # C1: Bullish
            c1_bullish = float(c1['close']) > float(c1['open'])

            # C2: Small body (doji-like)
            c2_body = abs(float(c2['close']) - float(c2['open']))
            c2_range = float(c2['high']) - float(c2['low'])
            c2_small = (c2_body / c2_range) < 0.3 if c2_range > 0 else False

            # C3: Bearish
            c3_bearish = float(c3['close']) < float(c3['open'])

            if c1_bullish and c2_small and c3_bearish:
                return 1
        except:
            pass

        return 0
