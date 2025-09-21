"""
Market Regime Detection with Multiple State Classification
Advanced market regime detection using statistical and ML methods.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.mixture import GaussianMixture
import warnings
warnings.filterwarnings('ignore')

from .strategy_engine import MarketRegime, MarketData

logger = logging.getLogger(__name__)

@dataclass
class RegimeState:
    """Market regime state information"""
    regime: MarketRegime
    confidence: float
    probability_distribution: Dict[MarketRegime, float]
    regime_duration: int  # Number of periods in current regime
    last_regime_change: float  # Timestamp of last regime change
    volatility: float
    trend_strength: float
    mean_reversion_strength: float

class MarketRegimeDetector:
    """Advanced market regime detection system"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = {
            'lookback_period': 60,
            'volatility_threshold_low': 0.015,
            'volatility_threshold_high': 0.035,
            'trend_threshold': 0.02,
            'regime_change_threshold': 0.7,
            'min_regime_duration': 5,
            'feature_lookback': 30,
            **config or {}
        }

        self.regime_history = []
        self.feature_history = []
        self.volatility_history = []
        self.current_regime = MarketRegime.SIDEWAYS
        self.regime_start_time = 0
        self.regime_duration = 0

        # ML models for regime classification
        self.kmeans_model = None
        self.gmm_model = None
        self.scaler = StandardScaler()
        self.is_trained = False

    def detect_regime(self, market_data: MarketData) -> RegimeState:
        """Detect current market regime using multiple methods"""

        if len(market_data.close) < self.config['lookback_period']:
            return RegimeState(
                regime=MarketRegime.SIDEWAYS,
                confidence=0.5,
                probability_distribution={regime: 1.0/len(MarketRegime) for regime in MarketRegime},
                regime_duration=0,
                last_regime_change=0,
                volatility=0.02,
                trend_strength=0.0,
                mean_reversion_strength=0.0
            )

        # Extract features for regime classification
        features = self._extract_regime_features(market_data)
        self.feature_history.append(features)

        # Keep feature history manageable
        if len(self.feature_history) > 200:
            self.feature_history.pop(0)

        # Statistical regime detection
        statistical_regime = self._detect_statistical_regime(features)

        # ML-based regime detection (if trained)
        ml_regime = self._detect_ml_regime(features) if self.is_trained else statistical_regime

        # Combine predictions
        regime_probabilities = self._combine_regime_predictions(statistical_regime, ml_regime, features)

        # Determine final regime with confidence
        final_regime = max(regime_probabilities, key=regime_probabilities.get)
        confidence = regime_probabilities[final_regime]

        # Apply regime stability filter
        if confidence < self.config['regime_change_threshold'] and self.regime_duration < self.config['min_regime_duration']:
            final_regime = self.current_regime  # Stick with current regime
            confidence = 0.6

        # Update regime tracking
        if final_regime != self.current_regime:
            self.current_regime = final_regime
            self.regime_start_time = market_data.timestamp[-1]
            self.regime_duration = 0
        else:
            self.regime_duration += 1

        # Train ML models periodically
        if len(self.feature_history) >= 100 and len(self.feature_history) % 50 == 0:
            self._train_ml_models()

        return RegimeState(
            regime=final_regime,
            confidence=confidence,
            probability_distribution=regime_probabilities,
            regime_duration=self.regime_duration,
            last_regime_change=self.regime_start_time,
            volatility=features['volatility'],
            trend_strength=features['trend_strength'],
            mean_reversion_strength=features['mean_reversion_strength']
        )

    def _extract_regime_features(self, market_data: MarketData) -> Dict[str, float]:
        """Extract features for regime classification"""

        prices = market_data.close[-self.config['lookback_period']:]
        highs = market_data.high[-self.config['lookback_period']:]
        lows = market_data.low[-self.config['lookback_period']:]
        volumes = market_data.volume[-self.config['lookback_period']:]

        # Price-based features
        returns = np.diff(np.log(prices))
        volatility = np.std(returns) * np.sqrt(252)  # Annualized volatility

        # Trend strength
        price_change = (prices[-1] - prices[0]) / prices[0]
        trend_strength = abs(price_change) / (volatility + 1e-10)

        # Mean reversion features
        sma_20 = np.mean(prices[-20:])
        distance_from_mean = abs(prices[-1] - sma_20) / sma_20
        bollinger_position = self._calculate_bollinger_position(prices)

        # Momentum features
        rsi = self._calculate_rsi(prices, 14)
        macd_signal = self._calculate_macd_signal(prices)

        # Volume features
        volume_trend = self._calculate_volume_trend(volumes, prices)
        volume_volatility = np.std(volumes[-20:]) / np.mean(volumes[-20:])

        # Range and breakout features
        range_ratio = (max(highs[-20:]) - min(lows[-20:])) / prices[-1]
        recent_high = max(highs[-10:])
        recent_low = min(lows[-10:])
        near_high = (prices[-1] - recent_high) / recent_high
        near_low = (prices[-1] - recent_low) / recent_low

        # Regime persistence features
        volatility_ma = np.mean([self._calculate_volatility(prices[i:i+10]) for i in range(len(prices)-10)])
        volatility_trend = (volatility - volatility_ma) / volatility_ma if volatility_ma > 0 else 0

        return {
            'volatility': volatility,
            'trend_strength': trend_strength,
            'price_change': price_change,
            'distance_from_mean': distance_from_mean,
            'bollinger_position': bollinger_position,
            'rsi': rsi,
            'macd_signal': macd_signal,
            'volume_trend': volume_trend,
            'volume_volatility': volume_volatility,
            'range_ratio': range_ratio,
            'near_high': near_high,
            'near_low': near_low,
            'volatility_trend': volatility_trend,
            'mean_reversion_strength': distance_from_mean + abs(bollinger_position)
        }

    def _detect_statistical_regime(self, features: Dict[str, float]) -> MarketRegime:
        """Detect regime using statistical rules"""

        volatility = features['volatility']
        trend_strength = features['trend_strength']
        price_change = features['price_change']
        near_high = features['near_high']
        near_low = features['near_low']
        distance_from_mean = features['distance_from_mean']

        # High volatility regime
        if volatility > self.config['volatility_threshold_high']:
            return MarketRegime.HIGH_VOLATILITY

        # Low volatility regime
        if volatility < self.config['volatility_threshold_low']:
            return MarketRegime.LOW_VOLATILITY

        # Breakout detection
        if abs(near_high) < 0.01 or abs(near_low) < 0.01:  # Within 1% of recent high/low
            if features['volume_trend'] > 0.2:  # High volume confirmation
                return MarketRegime.BREAKOUT

        # Trending regimes
        if trend_strength > 1.5 and abs(price_change) > self.config['trend_threshold']:
            if price_change > 0:
                return MarketRegime.TRENDING_UP
            else:
                return MarketRegime.TRENDING_DOWN

        # Default to sideways if no clear trend or breakout
        return MarketRegime.SIDEWAYS

    def _detect_ml_regime(self, features: Dict[str, float]) -> MarketRegime:
        """Detect regime using trained ML models"""

        if not self.is_trained:
            return MarketRegime.SIDEWAYS

        try:
            # Prepare feature vector
            feature_vector = np.array([[
                features['volatility'],
                features['trend_strength'],
                features['price_change'],
                features['distance_from_mean'],
                features['bollinger_position'],
                features['rsi'],
                features['macd_signal'],
                features['volume_trend'],
                features['range_ratio'],
                features['near_high'],
                features['near_low'],
                features['volatility_trend']
            ]])

            # Normalize features
            feature_vector_scaled = self.scaler.transform(feature_vector)

            # KMeans prediction
            kmeans_cluster = self.kmeans_model.predict(feature_vector_scaled)[0]

            # GMM prediction
            gmm_proba = self.gmm_model.predict_proba(feature_vector_scaled)[0]
            gmm_cluster = np.argmax(gmm_proba)

            # Map clusters to regimes (simplified mapping)
            regime_mapping = [
                MarketRegime.SIDEWAYS,
                MarketRegime.TRENDING_UP,
                MarketRegime.TRENDING_DOWN,
                MarketRegime.HIGH_VOLATILITY,
                MarketRegime.LOW_VOLATILITY,
                MarketRegime.BREAKOUT
            ]

            # Use GMM prediction as primary (more probabilistic)
            if gmm_cluster < len(regime_mapping):
                return regime_mapping[gmm_cluster]
            else:
                return MarketRegime.SIDEWAYS

        except Exception as e:
            logger.error(f"Error in ML regime detection: {e}")
            return MarketRegime.SIDEWAYS

    def _combine_regime_predictions(self, statistical_regime: MarketRegime, ml_regime: MarketRegime,
                                  features: Dict[str, float]) -> Dict[MarketRegime, float]:
        """Combine statistical and ML regime predictions"""

        # Initialize probabilities
        probabilities = {regime: 0.1 for regime in MarketRegime}

        # Statistical prediction weight
        statistical_weight = 0.6 if not self.is_trained else 0.4
        probabilities[statistical_regime] += statistical_weight

        # ML prediction weight
        ml_weight = 0.4 if not self.is_trained else 0.6
        probabilities[ml_regime] += ml_weight

        # Feature-based adjustments
        volatility = features['volatility']
        trend_strength = features['trend_strength']

        # Boost high volatility if conditions are met
        if volatility > self.config['volatility_threshold_high']:
            probabilities[MarketRegime.HIGH_VOLATILITY] *= 1.5

        # Boost low volatility if conditions are met
        if volatility < self.config['volatility_threshold_low']:
            probabilities[MarketRegime.LOW_VOLATILITY] *= 1.5

        # Boost trending regimes based on trend strength
        if trend_strength > 1.0:
            if features['price_change'] > 0:
                probabilities[MarketRegime.TRENDING_UP] *= (1 + trend_strength)
            else:
                probabilities[MarketRegime.TRENDING_DOWN] *= (1 + trend_strength)

        # Boost breakout if near extremes with volume
        if (abs(features['near_high']) < 0.02 or abs(features['near_low']) < 0.02) and features['volume_trend'] > 0.1:
            probabilities[MarketRegime.BREAKOUT] *= 1.3

        # Normalize probabilities
        total_prob = sum(probabilities.values())
        probabilities = {regime: prob / total_prob for regime, prob in probabilities.items()}

        return probabilities

    def _train_ml_models(self):
        """Train ML models for regime detection"""

        try:
            if len(self.feature_history) < 50:
                return

            # Prepare training data
            X = []
            for features in self.feature_history[-100:]:  # Use last 100 samples
                X.append([
                    features['volatility'],
                    features['trend_strength'],
                    features['price_change'],
                    features['distance_from_mean'],
                    features['bollinger_position'],
                    features['rsi'],
                    features['macd_signal'],
                    features['volume_trend'],
                    features['range_ratio'],
                    features['near_high'],
                    features['near_low'],
                    features['volatility_trend']
                ])

            X = np.array(X)

            # Fit scaler
            self.scaler.fit(X)
            X_scaled = self.scaler.transform(X)

            # Train KMeans
            self.kmeans_model = KMeans(n_clusters=6, random_state=42, n_init=10)
            self.kmeans_model.fit(X_scaled)

            # Train Gaussian Mixture Model
            self.gmm_model = GaussianMixture(n_components=6, random_state=42)
            self.gmm_model.fit(X_scaled)

            self.is_trained = True
            logger.info(f"ML regime detection models trained with {len(X)} samples")

        except Exception as e:
            logger.error(f"Error training ML regime models: {e}")
            self.is_trained = False

    def _calculate_bollinger_position(self, prices: np.ndarray, period: int = 20, std_dev: float = 2) -> float:
        """Calculate position within Bollinger Bands"""
        if len(prices) < period:
            return 0.0

        sma = np.mean(prices[-period:])
        std = np.std(prices[-period:])
        upper_band = sma + (std_dev * std)
        lower_band = sma - (std_dev * std)

        current_price = prices[-1]
        if upper_band == lower_band:
            return 0.0

        # Return position: -1 = at lower band, 0 = at SMA, 1 = at upper band
        position = (current_price - sma) / (upper_band - sma)
        return max(-1, min(1, position))

    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """Calculate RSI"""
        if len(prices) < period + 1:
            return 50.0

        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_macd_signal(self, prices: np.ndarray) -> float:
        """Calculate MACD signal strength"""
        if len(prices) < 26:
            return 0.0

        ema_12 = self._calculate_ema(prices, 12)
        ema_26 = self._calculate_ema(prices, 26)
        macd_line = ema_12[-1] - ema_26[-1]

        # Normalize by price
        macd_signal = macd_line / prices[-1]
        return macd_signal

    def _calculate_ema(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average"""
        alpha = 2 / (period + 1)
        ema = np.zeros_like(prices)
        ema[0] = prices[0]
        for i in range(1, len(prices)):
            ema[i] = alpha * prices[i] + (1 - alpha) * ema[i-1]
        return ema

    def _calculate_volume_trend(self, volumes: np.ndarray, prices: np.ndarray) -> float:
        """Calculate volume trend relative to price movement"""
        if len(volumes) < 10 or len(prices) < 10:
            return 0.0

        # Volume moving average
        volume_ma = np.mean(volumes[-10:])
        current_volume = volumes[-1]

        # Price movement
        price_change = (prices[-1] - prices[-5]) / prices[-5]

        # Volume trend: positive if volume increases with price movement
        volume_ratio = (current_volume / volume_ma) - 1
        volume_trend = volume_ratio * np.sign(price_change)

        return max(-1, min(1, volume_trend))

    def _calculate_volatility(self, prices: np.ndarray) -> float:
        """Calculate volatility for a price series"""
        if len(prices) < 2:
            return 0.02

        returns = np.diff(np.log(prices))
        volatility = np.std(returns) * np.sqrt(252)
        return volatility

    def get_regime_summary(self) -> Dict[str, Any]:
        """Get comprehensive regime analysis summary"""
        return {
            'current_regime': self.current_regime.value if self.current_regime else 'unknown',
            'regime_duration': self.regime_duration,
            'is_ml_trained': self.is_trained,
            'feature_history_length': len(self.feature_history),
            'regime_history': [r.value for r in self.regime_history[-20:]],  # Last 20 regimes
            'config': self.config
        }

    def get_strategy_recommendations(self, regime_state: RegimeState) -> Dict[str, float]:
        """Get strategy weight recommendations based on current regime"""

        recommendations = {
            'trend_following': 0.0,
            'mean_reversion': 0.0,
            'breakout': 0.0,
            'hold_cash': 0.0
        }

        regime = regime_state.regime
        confidence = regime_state.confidence

        if regime == MarketRegime.TRENDING_UP or regime == MarketRegime.TRENDING_DOWN:
            recommendations['trend_following'] = confidence * 0.8
            recommendations['breakout'] = confidence * 0.2

        elif regime == MarketRegime.SIDEWAYS:
            recommendations['mean_reversion'] = confidence * 0.7
            recommendations['trend_following'] = confidence * 0.2
            recommendations['hold_cash'] = confidence * 0.1

        elif regime == MarketRegime.HIGH_VOLATILITY:
            recommendations['breakout'] = confidence * 0.5
            recommendations['trend_following'] = confidence * 0.3
            recommendations['hold_cash'] = confidence * 0.2

        elif regime == MarketRegime.LOW_VOLATILITY:
            recommendations['mean_reversion'] = confidence * 0.6
            recommendations['trend_following'] = confidence * 0.3
            recommendations['hold_cash'] = confidence * 0.1

        elif regime == MarketRegime.BREAKOUT:
            recommendations['breakout'] = confidence * 0.8
            recommendations['trend_following'] = confidence * 0.2

        return recommendations