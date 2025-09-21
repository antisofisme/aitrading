"""
Trading Strategy Engine with Intelligent Decision Framework
Implements multiple trading strategies with AI-driven risk management and adaptive selection.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import time
import logging
from concurrent.futures import ThreadPoolExecutor
import asyncio
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketRegime(Enum):
    """Market regime classifications"""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    BREAKOUT = "breakout"

class SignalType(Enum):
    """Trading signal types"""
    BUY = 1
    SELL = -1
    HOLD = 0

@dataclass
class TradingSignal:
    """Trading signal with confidence and metadata"""
    signal: SignalType
    confidence: float
    price: float
    timestamp: float
    strategy: str
    metadata: Dict[str, Any]
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    position_size: Optional[float] = None

@dataclass
class MarketData:
    """Market data structure"""
    symbol: str
    open: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    volume: np.ndarray
    timestamp: np.ndarray

class BaseStrategy(ABC):
    """Base class for all trading strategies"""

    def __init__(self, name: str, params: Dict[str, Any]):
        self.name = name
        self.params = params
        self.performance_metrics = {}
        self.last_signal_time = 0

    @abstractmethod
    def generate_signal(self, data: MarketData) -> Optional[TradingSignal]:
        """Generate trading signal from market data"""
        pass

    @abstractmethod
    def update_performance(self, signal: TradingSignal, actual_return: float):
        """Update strategy performance metrics"""
        pass

class TrendFollowingStrategy(BaseStrategy):
    """Trend following strategy with momentum indicators"""

    def __init__(self, params: Dict[str, Any] = None):
        default_params = {
            'ema_fast': 12,
            'ema_slow': 26,
            'macd_signal': 9,
            'rsi_period': 14,
            'atr_period': 14,
            'volume_ma': 20,
            'min_confidence': 0.6
        }
        if params:
            default_params.update(params)
        super().__init__("TrendFollowing", default_params)

    def generate_signal(self, data: MarketData) -> Optional[TradingSignal]:
        """Generate trend following signal with multiple confirmations"""
        try:
            if len(data.close) < max(self.params['ema_slow'], self.params['rsi_period']):
                return None

            # Calculate indicators
            ema_fast = self._calculate_ema(data.close, self.params['ema_fast'])
            ema_slow = self._calculate_ema(data.close, self.params['ema_slow'])
            macd_line = ema_fast - ema_slow
            macd_signal = self._calculate_ema(macd_line, self.params['macd_signal'])
            macd_histogram = macd_line - macd_signal

            rsi = self._calculate_rsi(data.close, self.params['rsi_period'])
            atr = self._calculate_atr(data.high, data.low, data.close, self.params['atr_period'])
            volume_ma = np.mean(data.volume[-self.params['volume_ma']:])

            # Current values
            current_price = data.close[-1]
            current_macd = macd_line[-1]
            current_macd_signal = macd_signal[-1]
            current_macd_hist = macd_histogram[-1]
            current_rsi = rsi[-1]
            current_volume = data.volume[-1]
            current_atr = atr[-1]

            # Signal generation logic
            confidence = 0.0
            signal_type = SignalType.HOLD

            # MACD crossover
            if current_macd > current_macd_signal and macd_line[-2] <= macd_signal[-2]:
                confidence += 0.3
                signal_type = SignalType.BUY
            elif current_macd < current_macd_signal and macd_line[-2] >= macd_signal[-2]:
                confidence += 0.3
                signal_type = SignalType.SELL

            # EMA trend confirmation
            if ema_fast[-1] > ema_slow[-1] and signal_type == SignalType.BUY:
                confidence += 0.2
            elif ema_fast[-1] < ema_slow[-1] and signal_type == SignalType.SELL:
                confidence += 0.2

            # RSI momentum confirmation
            if signal_type == SignalType.BUY and 30 < current_rsi < 70:
                confidence += 0.2
            elif signal_type == SignalType.SELL and 30 < current_rsi < 70:
                confidence += 0.2

            # Volume confirmation
            if current_volume > volume_ma:
                confidence += 0.15

            # MACD histogram momentum
            if signal_type == SignalType.BUY and current_macd_hist > macd_histogram[-2]:
                confidence += 0.15
            elif signal_type == SignalType.SELL and current_macd_hist < macd_histogram[-2]:
                confidence += 0.15

            if confidence < self.params['min_confidence']:
                return None

            # Calculate stop loss and take profit
            if signal_type == SignalType.BUY:
                stop_loss = current_price - (2 * current_atr)
                take_profit = current_price + (3 * current_atr)
            elif signal_type == SignalType.SELL:
                stop_loss = current_price + (2 * current_atr)
                take_profit = current_price - (3 * current_atr)
            else:
                stop_loss = take_profit = None

            return TradingSignal(
                signal=signal_type,
                confidence=min(confidence, 1.0),
                price=current_price,
                timestamp=time.time(),
                strategy=self.name,
                stop_loss=stop_loss,
                take_profit=take_profit,
                metadata={
                    'macd': current_macd,
                    'macd_signal': current_macd_signal,
                    'rsi': current_rsi,
                    'atr': current_atr,
                    'volume_ratio': current_volume / volume_ma
                }
            )

        except Exception as e:
            logger.error(f"Error in TrendFollowing strategy: {e}")
            return None

    def _calculate_ema(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average"""
        alpha = 2 / (period + 1)
        ema = np.zeros_like(prices)
        ema[0] = prices[0]
        for i in range(1, len(prices)):
            ema[i] = alpha * prices[i] + (1 - alpha) * ema[i-1]
        return ema

    def _calculate_rsi(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate Relative Strength Index"""
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gains = np.zeros(len(prices))
        avg_losses = np.zeros(len(prices))

        # Initial values
        avg_gains[period] = np.mean(gains[:period])
        avg_losses[period] = np.mean(losses[:period])

        # Calculate RSI
        for i in range(period + 1, len(prices)):
            avg_gains[i] = (avg_gains[i-1] * (period - 1) + gains[i-1]) / period
            avg_losses[i] = (avg_losses[i-1] * (period - 1) + losses[i-1]) / period

        rs = avg_gains / (avg_losses + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_atr(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int) -> np.ndarray:
        """Calculate Average True Range"""
        tr1 = high - low
        tr2 = np.abs(high - np.roll(close, 1))
        tr3 = np.abs(low - np.roll(close, 1))
        tr = np.maximum(tr1, np.maximum(tr2, tr3))

        atr = np.zeros_like(tr)
        atr[period-1] = np.mean(tr[:period])

        for i in range(period, len(tr)):
            atr[i] = (atr[i-1] * (period - 1) + tr[i]) / period

        return atr

    def update_performance(self, signal: TradingSignal, actual_return: float):
        """Update strategy performance metrics"""
        if 'total_signals' not in self.performance_metrics:
            self.performance_metrics = {
                'total_signals': 0,
                'winning_signals': 0,
                'total_return': 0.0,
                'avg_confidence': 0.0
            }

        self.performance_metrics['total_signals'] += 1
        self.performance_metrics['total_return'] += actual_return
        self.performance_metrics['avg_confidence'] = (
            (self.performance_metrics['avg_confidence'] * (self.performance_metrics['total_signals'] - 1) +
             signal.confidence) / self.performance_metrics['total_signals']
        )

        if actual_return > 0:
            self.performance_metrics['winning_signals'] += 1

class MeanReversionStrategy(BaseStrategy):
    """Mean reversion strategy with statistical analysis"""

    def __init__(self, params: Dict[str, Any] = None):
        default_params = {
            'bollinger_period': 20,
            'bollinger_std': 2,
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'volume_ma': 20,
            'min_confidence': 0.6
        }
        if params:
            default_params.update(params)
        super().__init__("MeanReversion", default_params)

    def generate_signal(self, data: MarketData) -> Optional[TradingSignal]:
        """Generate mean reversion signal"""
        try:
            if len(data.close) < self.params['bollinger_period']:
                return None

            # Calculate Bollinger Bands
            sma = np.mean(data.close[-self.params['bollinger_period']:])
            std = np.std(data.close[-self.params['bollinger_period']:])
            upper_band = sma + (self.params['bollinger_std'] * std)
            lower_band = sma - (self.params['bollinger_std'] * std)

            # Calculate RSI
            rsi = self._calculate_rsi(data.close, self.params['rsi_period'])

            # Volume analysis
            volume_ma = np.mean(data.volume[-self.params['volume_ma']:])

            current_price = data.close[-1]
            current_rsi = rsi[-1]
            current_volume = data.volume[-1]

            confidence = 0.0
            signal_type = SignalType.HOLD

            # Bollinger Band mean reversion signals
            if current_price <= lower_band:
                confidence += 0.4
                signal_type = SignalType.BUY
            elif current_price >= upper_band:
                confidence += 0.4
                signal_type = SignalType.SELL

            # RSI confirmation
            if signal_type == SignalType.BUY and current_rsi <= self.params['rsi_oversold']:
                confidence += 0.3
            elif signal_type == SignalType.SELL and current_rsi >= self.params['rsi_overbought']:
                confidence += 0.3

            # Volume confirmation
            if current_volume > volume_ma:
                confidence += 0.2

            # Price distance from mean
            price_distance = abs(current_price - sma) / sma
            if price_distance > 0.02:  # At least 2% away from mean
                confidence += 0.1

            if confidence < self.params['min_confidence']:
                return None

            # Calculate stop loss and take profit based on Bollinger Bands
            atr = np.std(data.close[-14:])  # Use 14-period volatility as ATR proxy

            if signal_type == SignalType.BUY:
                stop_loss = current_price - (1.5 * atr)
                take_profit = sma  # Target mean reversion to SMA
            elif signal_type == SignalType.SELL:
                stop_loss = current_price + (1.5 * atr)
                take_profit = sma
            else:
                stop_loss = take_profit = None

            return TradingSignal(
                signal=signal_type,
                confidence=min(confidence, 1.0),
                price=current_price,
                timestamp=time.time(),
                strategy=self.name,
                stop_loss=stop_loss,
                take_profit=take_profit,
                metadata={
                    'bollinger_upper': upper_band,
                    'bollinger_lower': lower_band,
                    'sma': sma,
                    'rsi': current_rsi,
                    'price_distance_from_mean': price_distance
                }
            )

        except Exception as e:
            logger.error(f"Error in MeanReversion strategy: {e}")
            return None

    def _calculate_rsi(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate Relative Strength Index"""
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gains = np.zeros(len(prices))
        avg_losses = np.zeros(len(prices))

        avg_gains[period] = np.mean(gains[:period])
        avg_losses[period] = np.mean(losses[:period])

        for i in range(period + 1, len(prices)):
            avg_gains[i] = (avg_gains[i-1] * (period - 1) + gains[i-1]) / period
            avg_losses[i] = (avg_losses[i-1] * (period - 1) + losses[i-1]) / period

        rs = avg_gains / (avg_losses + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def update_performance(self, signal: TradingSignal, actual_return: float):
        """Update strategy performance metrics"""
        if 'total_signals' not in self.performance_metrics:
            self.performance_metrics = {
                'total_signals': 0,
                'winning_signals': 0,
                'total_return': 0.0,
                'avg_confidence': 0.0
            }

        self.performance_metrics['total_signals'] += 1
        self.performance_metrics['total_return'] += actual_return
        self.performance_metrics['avg_confidence'] = (
            (self.performance_metrics['avg_confidence'] * (self.performance_metrics['total_signals'] - 1) +
             signal.confidence) / self.performance_metrics['total_signals']
        )

        if actual_return > 0:
            self.performance_metrics['winning_signals'] += 1

class BreakoutStrategy(BaseStrategy):
    """Breakout strategy with volume confirmation"""

    def __init__(self, params: Dict[str, Any] = None):
        default_params = {
            'lookback_period': 20,
            'volume_multiplier': 1.5,
            'atr_period': 14,
            'min_breakout_size': 0.01,  # 1% minimum breakout
            'min_confidence': 0.6
        }
        if params:
            default_params.update(params)
        super().__init__("Breakout", default_params)

    def generate_signal(self, data: MarketData) -> Optional[TradingSignal]:
        """Generate breakout signal with volume confirmation"""
        try:
            if len(data.close) < self.params['lookback_period']:
                return None

            # Calculate support and resistance levels
            lookback_high = np.max(data.high[-self.params['lookback_period']:-1])  # Exclude current candle
            lookback_low = np.min(data.low[-self.params['lookback_period']:-1])

            # Calculate ATR for volatility adjustment
            atr = self._calculate_atr(data.high, data.low, data.close, self.params['atr_period'])

            # Volume analysis
            avg_volume = np.mean(data.volume[-self.params['lookback_period']:])

            current_price = data.close[-1]
            current_high = data.high[-1]
            current_low = data.low[-1]
            current_volume = data.volume[-1]
            current_atr = atr[-1]

            confidence = 0.0
            signal_type = SignalType.HOLD

            # Upward breakout
            if current_high > lookback_high:
                breakout_size = (current_high - lookback_high) / lookback_high
                if breakout_size >= self.params['min_breakout_size']:
                    confidence += 0.4
                    signal_type = SignalType.BUY

                    # Volume confirmation
                    if current_volume >= self.params['volume_multiplier'] * avg_volume:
                        confidence += 0.3

                    # Price closing near high
                    if current_price >= current_high - (0.2 * current_atr):
                        confidence += 0.2

                    # Momentum confirmation
                    if data.close[-1] > data.close[-2]:
                        confidence += 0.1

            # Downward breakout
            elif current_low < lookback_low:
                breakout_size = (lookback_low - current_low) / lookback_low
                if breakout_size >= self.params['min_breakout_size']:
                    confidence += 0.4
                    signal_type = SignalType.SELL

                    # Volume confirmation
                    if current_volume >= self.params['volume_multiplier'] * avg_volume:
                        confidence += 0.3

                    # Price closing near low
                    if current_price <= current_low + (0.2 * current_atr):
                        confidence += 0.2

                    # Momentum confirmation
                    if data.close[-1] < data.close[-2]:
                        confidence += 0.1

            if confidence < self.params['min_confidence']:
                return None

            # Calculate stop loss and take profit
            if signal_type == SignalType.BUY:
                stop_loss = lookback_high - (0.5 * current_atr)  # Just below breakout level
                take_profit = current_price + (3 * current_atr)
            elif signal_type == SignalType.SELL:
                stop_loss = lookback_low + (0.5 * current_atr)  # Just above breakout level
                take_profit = current_price - (3 * current_atr)
            else:
                stop_loss = take_profit = None

            return TradingSignal(
                signal=signal_type,
                confidence=min(confidence, 1.0),
                price=current_price,
                timestamp=time.time(),
                strategy=self.name,
                stop_loss=stop_loss,
                take_profit=take_profit,
                metadata={
                    'resistance_level': lookback_high,
                    'support_level': lookback_low,
                    'volume_ratio': current_volume / avg_volume,
                    'atr': current_atr,
                    'breakout_size': (current_high - lookback_high) / lookback_high if signal_type == SignalType.BUY
                                   else (lookback_low - current_low) / lookback_low
                }
            )

        except Exception as e:
            logger.error(f"Error in Breakout strategy: {e}")
            return None

    def _calculate_atr(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int) -> np.ndarray:
        """Calculate Average True Range"""
        tr1 = high - low
        tr2 = np.abs(high - np.roll(close, 1))
        tr3 = np.abs(low - np.roll(close, 1))
        tr = np.maximum(tr1, np.maximum(tr2, tr3))

        atr = np.zeros_like(tr)
        atr[period-1] = np.mean(tr[:period])

        for i in range(period, len(tr)):
            atr[i] = (atr[i-1] * (period - 1) + tr[i]) / period

        return atr

    def update_performance(self, signal: TradingSignal, actual_return: float):
        """Update strategy performance metrics"""
        if 'total_signals' not in self.performance_metrics:
            self.performance_metrics = {
                'total_signals': 0,
                'winning_signals': 0,
                'total_return': 0.0,
                'avg_confidence': 0.0
            }

        self.performance_metrics['total_signals'] += 1
        self.performance_metrics['total_return'] += actual_return
        self.performance_metrics['avg_confidence'] = (
            (self.performance_metrics['avg_confidence'] * (self.performance_metrics['total_signals'] - 1) +
             signal.confidence) / self.performance_metrics['total_signals']
        )

        if actual_return > 0:
            self.performance_metrics['winning_signals'] += 1