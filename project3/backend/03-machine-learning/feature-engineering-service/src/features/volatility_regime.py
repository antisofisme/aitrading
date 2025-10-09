"""
Volatility & Market Regime Features (6 features - 12% importance)

Features:
1. atr_current
2. atr_expansion
3. true_range_pct
4. volatility_regime
5. adx_value
6. bb_width
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any
import json

logger = logging.getLogger(__name__)


class VolatilityRegimeFeatures:
    """Calculate volatility and market regime features"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config['feature_groups']['volatility_regime']
        self.atr_periods = self.config.get('atr_periods', 14)
        self.adx_trending = self.config.get('adx_threshold_trending', 25)
        self.adx_ranging = self.config.get('adx_threshold_ranging', 20)

    def calculate(self, candle: pd.Series, h1_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate all volatility/regime features"""
        features = {}

        # Parse indicators from candle
        indicators = self._parse_indicators(candle)

        # 1. ATR current (from indicators)
        features['atr_current'] = indicators.get('atr', 0) * 10000  # Convert to pips

        # 2. ATR expansion (ATR increasing)
        features['atr_expansion'] = self._is_atr_expanding(h1_data)

        # 3. True range % (current candle)
        features['true_range_pct'] = self._calc_true_range_pct(candle)

        # 4. Volatility regime (1=low, 2=medium, 3=high)
        features['volatility_regime'] = self._classify_regime(features['atr_current'])

        # 5. ADX value (trend strength)
        features['adx_value'] = self._calc_adx(h1_data)

        # 6. BB width (Bollinger Band width %)
        features['bb_width'] = self._calc_bb_width(h1_data)

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

    def _is_atr_expanding(self, h1_data: pd.DataFrame) -> int:
        """Check if ATR is expanding"""
        if h1_data.empty or len(h1_data) < self.atr_periods + 5:
            return 0

        try:
            # Calculate ATR
            tr = self._calc_true_range_series(h1_data)
            atr = tr.rolling(window=self.atr_periods).mean()

            # Check if increasing
            current_atr = atr.iloc[-1]
            past_atr = atr.iloc[-5]

            if current_atr > past_atr * 1.1:  # 10% increase
                return 1
        except:
            pass

        return 0

    def _calc_true_range_series(self, h1_data: pd.DataFrame) -> pd.Series:
        """Calculate True Range series"""
        high = h1_data['high']
        low = h1_data['low']
        close_prev = h1_data['close'].shift(1)

        tr1 = high - low
        tr2 = abs(high - close_prev)
        tr3 = abs(low - close_prev)

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr

    def _calc_true_range_pct(self, candle: pd.Series) -> float:
        """Calculate true range as % of price"""
        try:
            high = float(candle['high'])
            low = float(candle['low'])
            close = float(candle['close'])

            tr = high - low
            if close > 0:
                tr_pct = (tr / close) * 100
                return round(tr_pct, 3)
        except:
            pass

        return 0.0

    def _classify_regime(self, atr_pips: float) -> int:
        """Classify volatility regime for Gold"""
        # Gold-specific thresholds
        if atr_pips < 100:
            return 1  # Low volatility
        elif atr_pips < 300:
            return 2  # Medium volatility
        else:
            return 3  # High volatility

    def _calc_adx(self, h1_data: pd.DataFrame) -> float:
        """Calculate ADX (simplified)"""
        if h1_data.empty or len(h1_data) < 14:
            return 0.0

        try:
            # Simplified ADX calculation
            high = h1_data['high'].values
            low = h1_data['low'].values
            close = h1_data['close'].values

            # +DM and -DM
            plus_dm = np.maximum(high[1:] - high[:-1], 0)
            minus_dm = np.maximum(low[:-1] - low[1:], 0)

            # True Range
            tr = self._calc_true_range_series(h1_data).values[1:]

            # Smoothed indicators
            plus_di = (pd.Series(plus_dm).rolling(14).sum() / pd.Series(tr).rolling(14).sum() * 100)
            minus_di = (pd.Series(minus_dm).rolling(14).sum() / pd.Series(tr).rolling(14).sum() * 100)

            # DX and ADX
            dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100
            adx = dx.rolling(14).mean().iloc[-1]

            return round(adx, 2) if not pd.isna(adx) else 0.0
        except:
            pass

        return 0.0

    def _calc_bb_width(self, h1_data: pd.DataFrame) -> float:
        """Calculate Bollinger Band width %"""
        if h1_data.empty or len(h1_data) < 20:
            return 0.0

        try:
            close = h1_data['close']
            sma = close.rolling(window=20).mean()
            std = close.rolling(window=20).std()

            bb_upper = sma + (2 * std)
            bb_lower = sma - (2 * std)

            bb_width = ((bb_upper - bb_lower) / sma * 100).iloc[-1]

            return round(bb_width, 2) if not pd.isna(bb_width) else 0.0
        except:
            pass

        return 0.0
