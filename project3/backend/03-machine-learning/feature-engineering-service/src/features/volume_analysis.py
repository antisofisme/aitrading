"""
Volume & Order Flow Analysis Features (8 features - 15% importance)

Features:
1. volume_spike
2. volume_profile
3. buying_pressure
4. selling_pressure
5. volume_momentum
6. volume_at_level
7. delta_volume
8. volume_divergence
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any

logger = logging.getLogger(__name__)


class VolumeFeatures:
    """Calculate volume and order flow features"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config['feature_groups']['volume_analysis']
        self.spike_threshold = self.config.get('volume_spike_threshold', 2.0)

    def calculate(self, candle: pd.Series, h1_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate all volume features"""
        features = {}

        current_volume = int(candle.get('volume', 0))

        # 1. Volume spike (> 2x average)
        features['volume_spike'] = self._is_volume_spike(current_volume, h1_data)

        # 2. Volume profile (simplified: volume rank)
        features['volume_profile'] = self._calc_volume_profile(current_volume, h1_data)

        # 3. Buying pressure (close near high)
        features['buying_pressure'] = self._calc_buying_pressure(candle)

        # 4. Selling pressure (close near low)
        features['selling_pressure'] = self._calc_selling_pressure(candle)

        # 5. Volume momentum (increasing over 3 candles)
        features['volume_momentum'] = self._calc_volume_momentum(h1_data)

        # 6. Volume at level (cumulative at SR)
        features['volume_at_level'] = self._calc_volume_at_level(candle, h1_data)

        # 7. Delta volume (buy - sell approximation)
        features['delta_volume'] = self._calc_delta_volume(candle)

        # 8. Volume divergence (price up + volume down)
        features['volume_divergence'] = self._check_volume_divergence(h1_data)

        return features

    def _is_volume_spike(self, current_volume: int, h1_data: pd.DataFrame) -> int:
        """Check if volume is spiking (> threshold × average)"""
        if h1_data.empty or len(h1_data) < 20:
            return 0

        try:
            avg_volume = h1_data.tail(20)['volume'].mean()
            if current_volume > avg_volume * self.spike_threshold:
                return 1
        except:
            pass

        return 0

    def _calc_volume_profile(self, current_volume: int, h1_data: pd.DataFrame) -> float:
        """Volume profile: percentile rank"""
        if h1_data.empty:
            return 0.5

        try:
            volumes = h1_data.tail(100)['volume'].values
            percentile = (volumes < current_volume).sum() / len(volumes)
            return float(percentile)
        except:
            return 0.5

    def _calc_buying_pressure(self, candle: pd.Series) -> float:
        """Buying pressure: (Close - Low) / (High - Low)"""
        try:
            high = float(candle['high'])
            low = float(candle['low'])
            close = float(candle['close'])

            if high - low > 0:
                pressure = (close - low) / (high - low)
                return round(pressure, 3)
        except:
            pass

        return 0.5

    def _calc_selling_pressure(self, candle: pd.Series) -> float:
        """Selling pressure: (High - Close) / (High - Low)"""
        try:
            high = float(candle['high'])
            low = float(candle['low'])
            close = float(candle['close'])

            if high - low > 0:
                pressure = (high - close) / (high - low)
                return round(pressure, 3)
        except:
            pass

        return 0.5

    def _calc_volume_momentum(self, h1_data: pd.DataFrame) -> float:
        """Volume momentum: rate of change over 3 candles"""
        if h1_data.empty or len(h1_data) < 4:
            return 0.0

        try:
            recent_vols = h1_data.tail(4)['volume'].values
            current = recent_vols[-1]
            past = recent_vols[0]

            if past > 0:
                momentum = ((current - past) / past) * 100
                return round(momentum, 2)
        except:
            pass

        return 0.0

    def _calc_volume_at_level(self, candle: pd.Series, h1_data: pd.DataFrame) -> int:
        """Cumulative volume at current price level"""
        if h1_data.empty:
            return 0

        try:
            current_price = float(candle['close'])
            tolerance = 10  # 10 pips

            # Find candles near current price
            near_price = h1_data[
                (h1_data['close'] >= current_price - tolerance / 10000) &
                (h1_data['close'] <= current_price + tolerance / 10000)
            ]

            total_volume = near_price['volume'].sum()
            return int(total_volume)
        except:
            pass

        return 0

    def _calc_delta_volume(self, candle: pd.Series) -> float:
        """Delta volume: buy vs sell approximation"""
        try:
            # Simplified: Use buying pressure as proxy
            buying_pressure = self._calc_buying_pressure(candle)
            selling_pressure = self._calc_selling_pressure(candle)

            delta = buying_pressure - selling_pressure
            return round(delta, 3)
        except:
            pass

        return 0.0

    def _check_volume_divergence(self, h1_data: pd.DataFrame) -> int:
        """Check for price/volume divergence"""
        if h1_data.empty or len(h1_data) < 10:
            return 0

        try:
            recent = h1_data.tail(10)

            # Price trend
            price_slope = (recent['close'].iloc[-1] - recent['close'].iloc[0]) / 10

            # Volume trend
            volume_slope = (recent['volume'].iloc[-1] - recent['volume'].iloc[0]) / 10

            # Divergence: price up + volume down (or vice versa)
            if price_slope > 0 and volume_slope < 0:
                return 1  # Bearish divergence
            elif price_slope < 0 and volume_slope > 0:
                return -1  # Bullish divergence (coded as -1)

        except:
            pass

        return 0
