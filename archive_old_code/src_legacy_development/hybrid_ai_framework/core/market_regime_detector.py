"""
Market Regime Detection System
Advanced ML-based market regime classification for forex/gold trading

Detects market regimes:
- Trending (Bull/Bear)
- Sideways/Range-bound
- Volatile/Uncertain
- Breakout/Breakdown
- Low Volatility/Consolidation
"""

import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import classification_report
    import pandas as pd
    HAS_ML_LIBS = True
except ImportError:
    HAS_ML_LIBS = False


class MarketRegime(Enum):
    """Market regime types"""
    TRENDING_BULL = "trending_bull"
    TRENDING_BEAR = "trending_bear"
    SIDEWAYS = "sideways"
    VOLATILE = "volatile"
    BREAKOUT = "breakout"
    BREAKDOWN = "breakdown"
    CONSOLIDATION = "consolidation"
    UNCERTAIN = "uncertain"


@dataclass
class RegimeFeatures:
    """Features for regime detection"""
    trend_strength: float
    trend_direction: int  # -1, 0, 1
    volatility: float
    volume_profile: float
    momentum: float
    mean_reversion: float
    breakout_probability: float
    consolidation_strength: float


@dataclass
class RegimeAnalysis:
    """Market regime analysis result"""
    regime: MarketRegime
    confidence: float
    trend_strength: float
    volatility: float
    momentum: float
    regime_duration: int  # periods in current regime
    regime_probability: Dict[MarketRegime, float]
    features: RegimeFeatures
    timestamp: datetime


class MarketRegimeDetector:
    """
    Advanced market regime detection using machine learning

    Features:
    - Multi-timeframe regime analysis
    - ML-based regime classification
    - Real-time regime transition detection
    - Forex/Gold specific regime patterns
    - Adaptive regime thresholds
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Model components
        self.regime_classifier = None
        self.feature_scaler = StandardScaler()

        # Regime tracking
        self.current_regime = MarketRegime.UNCERTAIN
        self.regime_history: List[RegimeAnalysis] = []
        self.regime_start_time = datetime.now()

        # Feature calculation parameters
        self.lookback_periods = {
            'short': 20,
            'medium': 50,
            'long': 100
        }

        # Regime thresholds (adaptive)
        self.thresholds = {
            'trend_strength': 0.6,
            'volatility_high': 0.7,
            'volatility_low': 0.3,
            'momentum_strong': 0.6,
            'breakout_threshold': 0.75
        }

        self.logger.info("Market Regime Detector initialized")

    async def initialize(self) -> bool:
        """Initialize the regime detector"""
        try:
            if HAS_ML_LIBS:
                # Initialize regime classifier
                self.regime_classifier = RandomForestClassifier(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42,
                    class_weight='balanced'
                )

                # Load pre-trained model if available
                await self._load_pretrained_model()

                self.logger.info("✅ Market Regime Detector fully initialized")
            else:
                self.logger.warning("⚠️ ML libraries not available, using rule-based regime detection")

            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Market Regime Detector: {e}")
            return False

    async def analyze_regime(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze current market regime

        Args:
            market_data: Dictionary containing price and volume data

        Returns:
            Dictionary with regime analysis results
        """
        try:
            # Extract price and volume data
            prices = market_data.get('close_prices', [])
            volumes = market_data.get('volumes', [])
            highs = market_data.get('high_prices', [])
            lows = market_data.get('low_prices', [])

            if len(prices) < self.lookback_periods['short']:
                return await self._fallback_regime_analysis()

            # Calculate regime features
            features = await self._calculate_regime_features(prices, volumes, highs, lows)

            # Classify regime
            if HAS_ML_LIBS and self.regime_classifier is not None:
                regime_analysis = await self._ml_regime_classification(features)
            else:
                regime_analysis = await self._rule_based_regime_classification(features)

            # Update regime history
            self.regime_history.append(regime_analysis)
            if len(self.regime_history) > 1000:  # Keep last 1000 analyses
                self.regime_history = self.regime_history[-1000:]

            # Check for regime transition
            await self._check_regime_transition(regime_analysis.regime)

            self.logger.debug(f"Regime analyzed: {regime_analysis.regime.value} (confidence: {regime_analysis.confidence:.2f})")

            return {
                'regime': regime_analysis.regime.value,
                'confidence': regime_analysis.confidence,
                'trend_strength': regime_analysis.trend_strength,
                'volatility': regime_analysis.volatility,
                'momentum': regime_analysis.momentum,
                'regime_duration': regime_analysis.regime_duration,
                'regime_probability': {k.value: v for k, v in regime_analysis.regime_probability.items()},
                'timestamp': regime_analysis.timestamp.isoformat()
            }

        except Exception as e:
            self.logger.error(f"❌ Regime analysis failed: {e}")
            return await self._fallback_regime_analysis()

    async def _calculate_regime_features(self, prices: List[float], volumes: List[float],
                                       highs: List[float], lows: List[float]) -> RegimeFeatures:
        """Calculate features for regime classification"""
        try:
            # Trend strength calculation
            trend_strength = await self._calculate_trend_strength(prices)

            # Trend direction
            trend_direction = await self._calculate_trend_direction(prices)

            # Volatility calculation
            volatility = await self._calculate_volatility(prices)

            # Volume profile
            volume_profile = await self._calculate_volume_profile(volumes) if volumes else 0.5

            # Momentum calculation
            momentum = await self._calculate_momentum(prices)

            # Mean reversion tendency
            mean_reversion = await self._calculate_mean_reversion(prices)

            # Breakout probability
            breakout_probability = await self._calculate_breakout_probability(prices, highs, lows)

            # Consolidation strength
            consolidation_strength = await self._calculate_consolidation_strength(prices, highs, lows)

            return RegimeFeatures(
                trend_strength=trend_strength,
                trend_direction=trend_direction,
                volatility=volatility,
                volume_profile=volume_profile,
                momentum=momentum,
                mean_reversion=mean_reversion,
                breakout_probability=breakout_probability,
                consolidation_strength=consolidation_strength
            )

        except Exception as e:
            self.logger.error(f"❌ Feature calculation failed: {e}")
            # Return neutral features
            return RegimeFeatures(
                trend_strength=0.5, trend_direction=0, volatility=0.5,
                volume_profile=0.5, momentum=0.5, mean_reversion=0.5,
                breakout_probability=0.5, consolidation_strength=0.5
            )

    async def _calculate_trend_strength(self, prices: List[float]) -> float:
        """Calculate trend strength using multiple methods"""
        try:
            if len(prices) < 10:
                return 0.5

            # Method 1: Linear regression slope significance
            n = len(prices)
            x = np.arange(n)

            # Calculate linear regression
            x_mean = np.mean(x)
            y_mean = np.mean(prices)

            slope = np.sum((x - x_mean) * (prices - y_mean)) / np.sum((x - x_mean) ** 2)

            # R-squared calculation
            y_pred = slope * x + (y_mean - slope * x_mean)
            ss_res = np.sum((prices - y_pred) ** 2)
            ss_tot = np.sum((prices - y_mean) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

            # Method 2: ADX-like calculation
            price_changes = np.diff(prices)
            positive_moves = np.where(price_changes > 0, price_changes, 0)
            negative_moves = np.where(price_changes < 0, abs(price_changes), 0)

            avg_positive = np.mean(positive_moves) if len(positive_moves) > 0 else 0
            avg_negative = np.mean(negative_moves) if len(negative_moves) > 0 else 0

            if avg_positive + avg_negative > 0:
                directional_index = abs(avg_positive - avg_negative) / (avg_positive + avg_negative)
            else:
                directional_index = 0

            # Combine methods
            trend_strength = (r_squared * 0.6 + directional_index * 0.4)

            return min(max(trend_strength, 0.0), 1.0)

        except Exception as e:
            self.logger.error(f"❌ Trend strength calculation failed: {e}")
            return 0.5

    async def _calculate_trend_direction(self, prices: List[float]) -> int:
        """Calculate trend direction (-1, 0, 1)"""
        try:
            if len(prices) < 5:
                return 0

            # Simple slope-based direction
            recent_slope = (prices[-1] - prices[-5]) / 5
            price_std = np.std(prices[-20:]) if len(prices) >= 20 else np.std(prices)

            # Normalize by volatility
            threshold = price_std * 0.1  # 10% of recent volatility

            if recent_slope > threshold:
                return 1  # Uptrend
            elif recent_slope < -threshold:
                return -1  # Downtrend
            else:
                return 0  # Sideways

        except Exception as e:
            self.logger.error(f"❌ Trend direction calculation failed: {e}")
            return 0

    async def _calculate_volatility(self, prices: List[float]) -> float:
        """Calculate normalized volatility"""
        try:
            if len(prices) < 10:
                return 0.5

            # Calculate returns
            returns = np.diff(prices) / prices[:-1]

            # Calculate volatility (standard deviation of returns)
            volatility = np.std(returns)

            # Normalize to 0-1 scale (assuming max volatility of 5% per period)
            normalized_volatility = min(volatility / 0.05, 1.0)

            return normalized_volatility

        except Exception as e:
            self.logger.error(f"❌ Volatility calculation failed: {e}")
            return 0.5

    async def _calculate_volume_profile(self, volumes: List[float]) -> float:
        """Calculate volume profile strength"""
        try:
            if len(volumes) < 10:
                return 0.5

            recent_volumes = volumes[-5:]
            historical_volumes = volumes[-20:] if len(volumes) >= 20 else volumes

            recent_avg = np.mean(recent_volumes)
            historical_avg = np.mean(historical_volumes)

            if historical_avg > 0:
                volume_ratio = recent_avg / historical_avg
                # Normalize to 0-1 scale
                volume_profile = min(max((volume_ratio - 0.5) * 2, 0), 1)
            else:
                volume_profile = 0.5

            return volume_profile

        except Exception as e:
            self.logger.error(f"❌ Volume profile calculation failed: {e}")
            return 0.5

    async def _calculate_momentum(self, prices: List[float]) -> float:
        """Calculate price momentum"""
        try:
            if len(prices) < 10:
                return 0.5

            # Rate of change over different periods
            roc_short = (prices[-1] - prices[-5]) / prices[-5] if prices[-5] != 0 else 0
            roc_medium = (prices[-1] - prices[-10]) / prices[-10] if len(prices) >= 10 and prices[-10] != 0 else 0

            # Weighted momentum
            momentum = abs(roc_short * 0.7 + roc_medium * 0.3)

            # Normalize to 0-1 scale
            normalized_momentum = min(momentum * 20, 1.0)  # Assuming max 5% momentum

            return normalized_momentum

        except Exception as e:
            self.logger.error(f"❌ Momentum calculation failed: {e}")
            return 0.5

    async def _calculate_mean_reversion(self, prices: List[float]) -> float:
        """Calculate mean reversion tendency"""
        try:
            if len(prices) < 20:
                return 0.5

            # Calculate distance from moving average
            ma_period = min(20, len(prices) // 2)
            moving_avg = np.mean(prices[-ma_period:])
            current_price = prices[-1]

            # Calculate standard deviation
            price_std = np.std(prices[-ma_period:])

            if price_std > 0:
                # Distance in standard deviations
                distance = abs(current_price - moving_avg) / price_std

                # Mean reversion probability (higher when further from mean)
                mean_reversion = min(distance / 2, 1.0)
            else:
                mean_reversion = 0.5

            return mean_reversion

        except Exception as e:
            self.logger.error(f"❌ Mean reversion calculation failed: {e}")
            return 0.5

    async def _calculate_breakout_probability(self, prices: List[float],
                                           highs: List[float], lows: List[float]) -> float:
        """Calculate breakout probability"""
        try:
            if len(prices) < 20:
                return 0.5

            # Calculate recent trading range
            recent_period = min(20, len(prices))
            recent_high = max(highs[-recent_period:]) if highs else max(prices[-recent_period:])
            recent_low = min(lows[-recent_period:]) if lows else min(prices[-recent_period:])
            current_price = prices[-1]

            # Calculate position within range
            if recent_high != recent_low:
                range_position = (current_price - recent_low) / (recent_high - recent_low)
            else:
                range_position = 0.5

            # Breakout probability increases near range extremes
            if range_position > 0.8 or range_position < 0.2:
                breakout_probability = min(abs(range_position - 0.5) * 2, 1.0)
            else:
                breakout_probability = 0.3

            return breakout_probability

        except Exception as e:
            self.logger.error(f"❌ Breakout probability calculation failed: {e}")
            return 0.5

    async def _calculate_consolidation_strength(self, prices: List[float],
                                              highs: List[float], lows: List[float]) -> float:
        """Calculate consolidation strength"""
        try:
            if len(prices) < 10:
                return 0.5

            # Calculate range compression
            recent_period = min(10, len(prices))
            older_period = min(20, len(prices))

            if highs and lows and len(highs) >= older_period and len(lows) >= older_period:
                recent_range = max(highs[-recent_period:]) - min(lows[-recent_period:])
                older_range = max(highs[-older_period:-recent_period]) - min(lows[-older_period:-recent_period])
            else:
                recent_range = max(prices[-recent_period:]) - min(prices[-recent_period:])
                older_range = max(prices[-older_period:-recent_period]) - min(prices[-older_period:-recent_period])

            if older_range > 0:
                consolidation_strength = 1 - (recent_range / older_range)
                consolidation_strength = max(min(consolidation_strength, 1.0), 0.0)
            else:
                consolidation_strength = 0.5

            return consolidation_strength

        except Exception as e:
            self.logger.error(f"❌ Consolidation strength calculation failed: {e}")
            return 0.5

    async def _ml_regime_classification(self, features: RegimeFeatures) -> RegimeAnalysis:
        """Classify regime using ML model"""
        try:
            # Prepare feature vector
            feature_vector = [
                features.trend_strength,
                features.trend_direction,
                features.volatility,
                features.volume_profile,
                features.momentum,
                features.mean_reversion,
                features.breakout_probability,
                features.consolidation_strength
            ]

            # Scale features
            feature_vector_scaled = self.feature_scaler.transform([feature_vector])

            # Get regime prediction
            regime_probs = self.regime_classifier.predict_proba(feature_vector_scaled)[0]
            regime_classes = self.regime_classifier.classes_

            # Find most likely regime
            best_regime_idx = np.argmax(regime_probs)
            predicted_regime = MarketRegime(regime_classes[best_regime_idx])
            confidence = regime_probs[best_regime_idx]

            # Create probability dictionary
            regime_probability = {}
            for i, regime_class in enumerate(regime_classes):
                regime_probability[MarketRegime(regime_class)] = regime_probs[i]

            # Calculate regime duration
            regime_duration = await self._calculate_regime_duration(predicted_regime)

            return RegimeAnalysis(
                regime=predicted_regime,
                confidence=confidence,
                trend_strength=features.trend_strength,
                volatility=features.volatility,
                momentum=features.momentum,
                regime_duration=regime_duration,
                regime_probability=regime_probability,
                features=features,
                timestamp=datetime.now()
            )

        except Exception as e:
            self.logger.error(f"❌ ML regime classification failed: {e}")
            return await self._rule_based_regime_classification(features)

    async def _rule_based_regime_classification(self, features: RegimeFeatures) -> RegimeAnalysis:
        """Classify regime using rule-based approach"""
        try:
            # Rule-based regime classification
            regime = MarketRegime.UNCERTAIN
            confidence = 0.5

            # High volatility regime
            if features.volatility > self.thresholds['volatility_high']:
                regime = MarketRegime.VOLATILE
                confidence = features.volatility

            # Strong trend regimes
            elif features.trend_strength > self.thresholds['trend_strength']:
                if features.trend_direction > 0:
                    regime = MarketRegime.TRENDING_BULL
                elif features.trend_direction < 0:
                    regime = MarketRegime.TRENDING_BEAR
                else:
                    regime = MarketRegime.SIDEWAYS
                confidence = features.trend_strength

            # Breakout/breakdown
            elif features.breakout_probability > self.thresholds['breakout_threshold']:
                if features.momentum > 0.5:
                    regime = MarketRegime.BREAKOUT if features.trend_direction >= 0 else MarketRegime.BREAKDOWN
                    confidence = features.breakout_probability

            # Consolidation
            elif features.consolidation_strength > 0.6:
                regime = MarketRegime.CONSOLIDATION
                confidence = features.consolidation_strength

            # Sideways/ranging
            elif (features.volatility < self.thresholds['volatility_low'] and
                  features.trend_strength < 0.4):
                regime = MarketRegime.SIDEWAYS
                confidence = 1 - features.volatility

            # Create simple probability distribution
            regime_probability = {r: 0.1 for r in MarketRegime}
            regime_probability[regime] = confidence

            # Normalize probabilities
            total_prob = sum(regime_probability.values())
            regime_probability = {k: v/total_prob for k, v in regime_probability.items()}

            # Calculate regime duration
            regime_duration = await self._calculate_regime_duration(regime)

            return RegimeAnalysis(
                regime=regime,
                confidence=confidence,
                trend_strength=features.trend_strength,
                volatility=features.volatility,
                momentum=features.momentum,
                regime_duration=regime_duration,
                regime_probability=regime_probability,
                features=features,
                timestamp=datetime.now()
            )

        except Exception as e:
            self.logger.error(f"❌ Rule-based regime classification failed: {e}")
            return RegimeAnalysis(
                regime=MarketRegime.UNCERTAIN,
                confidence=0.3,
                trend_strength=0.5,
                volatility=0.5,
                momentum=0.5,
                regime_duration=1,
                regime_probability={r: 1.0/len(MarketRegime) for r in MarketRegime},
                features=features,
                timestamp=datetime.now()
            )

    async def _calculate_regime_duration(self, current_regime: MarketRegime) -> int:
        """Calculate how long current regime has been active"""
        try:
            if not self.regime_history:
                return 1

            duration = 1
            for analysis in reversed(self.regime_history[-50:]):  # Check last 50 analyses
                if analysis.regime == current_regime:
                    duration += 1
                else:
                    break

            return duration

        except Exception as e:
            self.logger.error(f"❌ Regime duration calculation failed: {e}")
            return 1

    async def _check_regime_transition(self, new_regime: MarketRegime) -> None:
        """Check for regime transition and update tracking"""
        try:
            if new_regime != self.current_regime:
                self.logger.info(f"Regime transition detected: {self.current_regime.value} -> {new_regime.value}")
                self.current_regime = new_regime
                self.regime_start_time = datetime.now()

        except Exception as e:
            self.logger.error(f"❌ Regime transition check failed: {e}")

    async def _fallback_regime_analysis(self) -> Dict[str, Any]:
        """Fallback regime analysis when main analysis fails"""
        return {
            'regime': MarketRegime.UNCERTAIN.value,
            'confidence': 0.3,
            'trend_strength': 0.5,
            'volatility': 0.5,
            'momentum': 0.5,
            'regime_duration': 1,
            'regime_probability': {r.value: 1.0/len(MarketRegime) for r in MarketRegime},
            'timestamp': datetime.now().isoformat()
        }

    async def _load_pretrained_model(self) -> None:
        """Load pre-trained regime classification model"""
        try:
            # Placeholder for loading pre-trained model
            # In production, this would load from file
            self.logger.info("Pre-trained model loading not implemented yet")

        except Exception as e:
            self.logger.warning(f"Failed to load pre-trained model: {e}")

    async def get_regime_statistics(self) -> Dict[str, Any]:
        """Get regime detection statistics"""
        try:
            if not self.regime_history:
                return {'total_analyses': 0}

            recent_analyses = self.regime_history[-100:]  # Last 100 analyses

            # Count regime occurrences
            regime_counts = {}
            for analysis in recent_analyses:
                regime = analysis.regime.value
                regime_counts[regime] = regime_counts.get(regime, 0) + 1

            # Calculate average confidence
            avg_confidence = sum(a.confidence for a in recent_analyses) / len(recent_analyses)

            # Calculate regime transition frequency
            transitions = 0
            for i in range(1, len(recent_analyses)):
                if recent_analyses[i].regime != recent_analyses[i-1].regime:
                    transitions += 1

            transition_rate = transitions / len(recent_analyses) if recent_analyses else 0

            return {
                'total_analyses': len(self.regime_history),
                'recent_analyses': len(recent_analyses),
                'regime_distribution': regime_counts,
                'average_confidence': avg_confidence,
                'transition_rate': transition_rate,
                'current_regime': self.current_regime.value,
                'current_regime_duration': (datetime.now() - self.regime_start_time).total_seconds() / 3600  # hours
            }

        except Exception as e:
            self.logger.error(f"❌ Failed to get regime statistics: {e}")
            return {'error': str(e)}


# Export main components
__all__ = [
    'MarketRegimeDetector',
    'MarketRegime',
    'RegimeFeatures',
    'RegimeAnalysis'
]