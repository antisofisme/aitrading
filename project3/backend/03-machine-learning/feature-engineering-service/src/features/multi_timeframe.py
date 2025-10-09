"""
Multi-Timeframe Context Features (9 features - 15% importance)

Features:
1. m5_momentum
2. m15_consolidation
3. h1_trend
4. h4_structure
5. d1_bias
6. w1_major_level
7. tf_alignment_score
8. h4_h1_divergence
9. d1_w1_alignment
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any

logger = logging.getLogger(__name__)


class MultiTimeframeFeatures:
    """Calculate multi-timeframe context features"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config['feature_groups']['multi_timeframe']

    def calculate(
        self,
        multi_tf_data: Dict[str, pd.DataFrame],
        current_timestamp: pd.Timestamp
    ) -> Dict[str, Any]:
        """Calculate all multi-timeframe features"""
        features = {}

        m5_data = multi_tf_data.get('5m', pd.DataFrame())
        m15_data = multi_tf_data.get('15m', pd.DataFrame())
        h1_data = multi_tf_data.get('1h', pd.DataFrame())
        h4_data = multi_tf_data.get('4h', pd.DataFrame())
        d1_data = multi_tf_data.get('1d', pd.DataFrame())
        w1_data = multi_tf_data.get('1w', pd.DataFrame())

        # 1. M5 momentum (ROC - Rate of Change)
        features['m5_momentum'] = self._calc_momentum(m5_data, periods=5)

        # 2. M15 consolidation (BB width < threshold)
        features['m15_consolidation'] = self._is_consolidating(m15_data)

        # 3. H1 trend (1=up, 0=neutral, -1=down)
        features['h1_trend'] = self._calc_trend(h1_data)

        # 4. H4 structure (bullish/bearish/neutral)
        features['h4_structure'] = self._calc_structure(h4_data)

        # 5. D1 bias (price above/below 200 EMA)
        features['d1_bias'] = self._calc_bias(d1_data)

        # 6. W1 major level (nearest swing level)
        features['w1_major_level'] = self._get_major_level(w1_data)

        # 7. TF alignment score (0-6)
        features['tf_alignment_score'] = self._calc_alignment_score(multi_tf_data)

        # 8. H4/H1 divergence (trends conflict)
        features['h4_h1_divergence'] = self._check_divergence(
            self._calc_trend(h4_data),
            self._calc_trend(h1_data)
        )

        # 9. D1/W1 alignment
        features['d1_w1_alignment'] = 1 if self._calc_bias(d1_data) == self._calc_bias(w1_data) else 0

        return features

    def _calc_momentum(self, data: pd.DataFrame, periods: int = 5) -> float:
        """Calculate momentum (ROC)"""
        if data.empty or len(data) < periods + 1:
            return 0.0

        try:
            current = data['close'].iloc[-1]
            past = data['close'].iloc[-(periods + 1)]

            if past != 0:
                roc = ((current - past) / past) * 100
                return float(roc)
        except:
            pass

        return 0.0

    def _is_consolidating(self, data: pd.DataFrame, threshold: float = 2.0) -> int:
        """Check if consolidating (BB width < threshold)"""
        if data.empty or len(data) < 20:
            return 0

        try:
            # Calculate Bollinger Band width
            sma = data['close'].rolling(window=20).mean()
            std = data['close'].rolling(window=20).std()

            bb_upper = sma + (2 * std)
            bb_lower = sma - (2 * std)
            bb_width = ((bb_upper - bb_lower) / sma) * 100

            latest_width = bb_width.iloc[-1]

            return 1 if latest_width < threshold else 0
        except:
            return 0

    def _calc_trend(self, data: pd.DataFrame) -> int:
        """Calculate trend direction (1=up, 0=neutral, -1=down)"""
        if data.empty or len(data) < 50:
            return 0

        try:
            ema_50 = data['close'].ewm(span=50).mean()
            slope = (ema_50.iloc[-1] - ema_50.iloc[-10]) / 10

            if slope > 0.0001:
                return 1
            elif slope < -0.0001:
                return -1
        except:
            pass

        return 0

    def _calc_structure(self, data: pd.DataFrame) -> str:
        """Calculate structure (bullish/bearish/neutral)"""
        if data.empty or len(data) < 10:
            return 'neutral'

        try:
            # Check for higher highs/lows (bullish) or lower highs/lows (bearish)
            recent = data.tail(10)

            highs = recent['high'].values
            lows = recent['low'].values

            # Simple: check if making higher highs
            if highs[-1] > highs[-5] and lows[-1] > lows[-5]:
                return 'bullish_structure'
            elif highs[-1] < highs[-5] and lows[-1] < lows[-5]:
                return 'bearish_structure'
        except:
            pass

        return 'neutral'

    def _calc_bias(self, data: pd.DataFrame) -> int:
        """Calculate bias (1=bullish, -1=bearish, 0=neutral)"""
        if data.empty or len(data) < 200:
            return 0

        try:
            ema_200 = data['close'].ewm(span=200).mean().iloc[-1]
            current_price = data['close'].iloc[-1]

            if current_price > ema_200:
                return 1  # Bullish
            elif current_price < ema_200:
                return -1  # Bearish
        except:
            pass

        return 0

    def _get_major_level(self, data: pd.DataFrame) -> float:
        """Get nearest W1 major level"""
        if data.empty:
            return 0.0

        try:
            # Return most recent swing high or low
            recent_high = data.tail(4)['high'].max()
            recent_low = data.tail(4)['low'].min()

            current_price = data['close'].iloc[-1]

            # Return nearest
            if abs(current_price - recent_high) < abs(current_price - recent_low):
                return float(recent_high)
            else:
                return float(recent_low)
        except:
            return 0.0

    def _calc_alignment_score(self, multi_tf_data: Dict[str, pd.DataFrame]) -> int:
        """Calculate TF alignment score (0-6)"""
        timeframes = ['5m', '15m', '1h', '4h', '1d', '1w']
        trends = []

        for tf in timeframes:
            data = multi_tf_data.get(tf, pd.DataFrame())
            trend = self._calc_trend(data)
            trends.append(trend)

        # Count how many agree on direction
        if len(set(trends)) == 1 and trends[0] != 0:
            return 6  # All aligned
        else:
            up_count = sum(1 for t in trends if t == 1)
            down_count = sum(1 for t in trends if t == -1)
            return max(up_count, down_count)

    def _check_divergence(self, h4_trend: int, h1_trend: int) -> int:
        """Check if H4 and H1 trends diverge"""
        if h4_trend != 0 and h1_trend != 0 and h4_trend != h1_trend:
            return 1  # Divergence
        return 0
