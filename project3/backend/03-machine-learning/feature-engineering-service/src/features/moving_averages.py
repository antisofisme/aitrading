"""
Moving Average Features (2 features - 2% importance)

Features:
1. sma_200
2. ema_50
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any
import json

logger = logging.getLogger(__name__)


class MovingAverageFeatures:
    """Calculate moving average features"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config['feature_groups']['moving_averages']
        self.sma_period = self.config.get('sma_period', 200)
        self.ema_period = self.config.get('ema_period', 50)

    def calculate(self, candle: pd.Series, h1_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate all moving average features"""
        features = {}

        # Parse indicators from candle
        indicators = self._parse_indicators(candle)

        # 1. SMA 200 (from indicators or calculate)
        features['sma_200'] = self._get_sma_200(candle, h1_data, indicators)

        # 2. EMA 50 (from indicators or calculate)
        features['ema_50'] = self._get_ema_50(candle, h1_data, indicators)

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

    def _get_sma_200(self, candle: pd.Series, h1_data: pd.DataFrame, indicators: dict) -> float:
        """
        Get SMA 200 value
        Priority: 1) From indicators, 2) Calculate from H1 data
        """
        # Try from indicators first
        sma_200 = indicators.get('sma_200', None)
        if sma_200 is not None and sma_200 > 0:
            return float(sma_200)

        # Calculate from H1 data
        if not h1_data.empty and len(h1_data) >= self.sma_period:
            try:
                sma = h1_data.tail(self.sma_period)['close'].mean()
                return float(sma)
            except:
                pass

        # Fallback to current close
        try:
            return float(candle['close'])
        except:
            return 0.0

    def _get_ema_50(self, candle: pd.Series, h1_data: pd.DataFrame, indicators: dict) -> float:
        """
        Get EMA 50 value
        Priority: 1) From indicators, 2) Calculate from H1 data
        """
        # Try from indicators first
        ema_50 = indicators.get('ema_50', None)
        if ema_50 is not None and ema_50 > 0:
            return float(ema_50)

        # Calculate from H1 data
        if not h1_data.empty and len(h1_data) >= self.ema_period:
            try:
                ema = h1_data.tail(self.ema_period)['close'].ewm(span=self.ema_period).mean().iloc[-1]
                return float(ema)
            except:
                pass

        # Fallback to current close
        try:
            return float(candle['close'])
        except:
            return 0.0
