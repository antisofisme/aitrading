"""
Hybrid AI Trading Framework - Core Engine
Combines existing 40+ indicator system with proven AI frameworks for forex/gold trading

Features:
- Integration with existing TradingIndicatorManager (14 indicators)
- Forex/Gold specific AI models and indicators
- Multi-asset correlation analysis (DXY, commodities)
- FinBERT sentiment analysis
- Session-based forex trading analysis
- Adaptive learning and AutoML optimization
- Ensemble prediction system
"""

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
import json
from pathlib import Path
import pickle

# External ML libraries for AI integration
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_squared_error, accuracy_score
    import optuna
    HAS_ML_LIBS = True
except ImportError:
    HAS_ML_LIBS = False
    logging.warning("ML libraries not available. Running in basic mode.")

# Local imports - integrate with existing trading engine
from .market_regime_detector import MarketRegimeDetector
from .session_analyzer import ForexSessionAnalyzer
from .correlation_engine import MultiAssetCorrelationEngine
from .sentiment_analyzer import FinBERTSentimentAnalyzer
from .automl_optimizer import AutoMLOptimizer


class TradingAsset(Enum):
    """Supported trading assets"""
    XAUUSD = "XAUUSD"  # Gold
    EURUSD = "EURUSD"
    GBPUSD = "GBPUSD"
    USDJPY = "USDJPY"
    USDCHF = "USDCHF"
    AUDUSD = "AUDUSD"
    USDCAD = "USDCAD"
    NZDUSD = "NZDUSD"
    DXY = "DXY"  # Dollar Index


class AIModelType(Enum):
    """AI model types"""
    FINBERT_SENTIMENT = "finbert_sentiment"
    ENSEMBLE_PREDICTOR = "ensemble_predictor"
    REGIME_CLASSIFIER = "regime_classifier"
    CORRELATION_PREDICTOR = "correlation_predictor"
    GOLD_SPECIALIST = "gold_specialist"
    FOREX_SPECIALIST = "forex_specialist"


@dataclass
class HybridAIConfig:
    """Configuration for hybrid AI framework"""
    # Asset-specific settings
    primary_asset: TradingAsset = TradingAsset.XAUUSD
    correlation_assets: List[TradingAsset] = field(default_factory=lambda: [
        TradingAsset.DXY, TradingAsset.EURUSD, TradingAsset.GBPUSD
    ])

    # AI model settings
    enable_finbert: bool = True
    enable_ensemble: bool = True
    enable_automl: bool = True
    sentiment_weight: float = 0.2

    # Trading session settings
    enable_session_analysis: bool = True
    primary_sessions: List[str] = field(default_factory=lambda: ["london", "newyork"])

    # Learning settings
    adaptation_period: int = 100  # trades
    retraining_period: int = 1000  # trades
    confidence_threshold: float = 0.75

    # Risk management
    max_correlation_exposure: float = 0.6
    regime_sensitivity: float = 0.8

    # Performance settings
    cache_predictions: bool = True
    async_processing: bool = True


@dataclass
class MarketInsight:
    """Enhanced market insight with AI analysis"""
    asset: str
    timestamp: datetime

    # Traditional indicators (from existing system)
    technical_score: float
    volume_score: float
    momentum_score: float

    # AI insights
    sentiment_score: float
    regime_prediction: str
    correlation_strength: Dict[str, float]
    session_activity: Dict[str, float]

    # Ensemble predictions
    price_prediction: float
    confidence: float
    prediction_range: Tuple[float, float]

    # Metadata
    model_contributions: Dict[str, float]
    risk_factors: List[str]
    opportunities: List[str]


@dataclass
class TradingSignal:
    """Enhanced trading signal with AI components"""
    asset: str
    signal_type: str  # buy, sell, hold
    strength: float
    confidence: float

    # Price targets
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: float

    # AI insights
    ai_confidence: float
    sentiment_impact: float
    regime_alignment: float
    correlation_risk: float
    session_favorability: float

    # Supporting data
    rationale: str
    risk_level: str
    holding_period: str
    market_insight: MarketInsight

    timestamp: datetime = field(default_factory=datetime.now)


class HybridAITradingEngine:
    """
    Core hybrid AI trading engine combining traditional indicators with modern AI

    Architecture:
    1. Traditional Indicators (40+) -> Technical Analysis Layer
    2. Market Regime Detection -> AI Classification Layer
    3. Sentiment Analysis -> FinBERT Layer
    4. Correlation Analysis -> Multi-Asset Layer
    5. Session Analysis -> Forex-Specific Layer
    6. Ensemble Prediction -> ML Fusion Layer
    7. Adaptive Learning -> AutoML Optimization Layer
    """

    def __init__(self, config: HybridAIConfig = None):
        self.config = config or HybridAIConfig()
        self.logger = logging.getLogger(__name__)

        # Core components
        self.regime_detector = MarketRegimeDetector()
        self.session_analyzer = ForexSessionAnalyzer()
        self.correlation_engine = MultiAssetCorrelationEngine()
        self.automl_optimizer = AutoMLOptimizer()

        # AI models
        self.ai_models: Dict[AIModelType, Any] = {}
        self.model_cache: Dict[str, Any] = {}

        # Performance tracking
        self.performance_history: List[Dict] = []
        self.prediction_accuracy: Dict[str, float] = {}

        # State management
        self.last_market_insight: Optional[MarketInsight] = None
        self.active_signals: List[TradingSignal] = []

        self.logger.info(f"Hybrid AI Trading Engine initialized for {self.config.primary_asset.value}")

    async def initialize(self) -> bool:
        """Initialize all AI components and models"""
        try:
            self.logger.info("Initializing Hybrid AI Trading Engine...")

            # Initialize sentiment analyzer if enabled
            if self.config.enable_finbert and HAS_ML_LIBS:
                self.sentiment_analyzer = FinBERTSentimentAnalyzer()
                await self.sentiment_analyzer.initialize()
                self.logger.info("FinBERT sentiment analyzer initialized")

            # Initialize regime detector
            await self.regime_detector.initialize()
            self.logger.info("Market regime detector initialized")

            # Initialize session analyzer
            await self.session_analyzer.initialize()
            self.logger.info("Forex session analyzer initialized")

            # Initialize correlation engine
            await self.correlation_engine.initialize(self.config.correlation_assets)
            self.logger.info(f"Multi-asset correlation engine initialized for {len(self.config.correlation_assets)} assets")

            # Load or train AI models
            if self.config.enable_ensemble and HAS_ML_LIBS:
                await self._initialize_ai_models()
                self.logger.info("AI ensemble models initialized")

            # Initialize AutoML optimizer
            if self.config.enable_automl and HAS_ML_LIBS:
                await self.automl_optimizer.initialize()
                self.logger.info("AutoML optimizer initialized")

            self.logger.info("✅ Hybrid AI Trading Engine fully initialized")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Hybrid AI Trading Engine: {e}")
            return False

    async def analyze_market(self, market_data: Dict[str, Any]) -> MarketInsight:
        """
        Comprehensive market analysis using all AI components

        Args:
            market_data: Dictionary containing OHLCV data and additional market info

        Returns:
            MarketInsight with comprehensive AI analysis
        """
        try:
            asset = market_data.get('symbol', self.config.primary_asset.value)
            timestamp = market_data.get('timestamp', datetime.now())

            # 1. Traditional Technical Analysis (from existing indicator system)
            technical_scores = await self._calculate_technical_scores(market_data)

            # 2. Market Regime Analysis
            regime_analysis = await self.regime_detector.analyze_regime(market_data)

            # 3. Sentiment Analysis (if news data available)
            sentiment_score = 0.5  # Neutral default
            if 'news_data' in market_data and self.config.enable_finbert:
                sentiment_score = await self._analyze_sentiment(market_data['news_data'])

            # 4. Multi-Asset Correlation Analysis
            correlation_analysis = await self.correlation_engine.analyze_correlations(
                asset, market_data
            )

            # 5. Session Analysis (for forex pairs)
            session_analysis = await self.session_analyzer.analyze_session_activity(
                asset, timestamp
            )

            # 6. Ensemble Price Prediction
            price_prediction, confidence, pred_range = await self._ensemble_prediction(
                market_data, technical_scores, regime_analysis, sentiment_score
            )

            # 7. Create comprehensive market insight
            insight = MarketInsight(
                asset=asset,
                timestamp=timestamp,
                technical_score=technical_scores['overall'],
                volume_score=technical_scores['volume'],
                momentum_score=technical_scores['momentum'],
                sentiment_score=sentiment_score,
                regime_prediction=regime_analysis['regime'],
                correlation_strength=correlation_analysis['correlations'],
                session_activity=session_analysis['activity_scores'],
                price_prediction=price_prediction,
                confidence=confidence,
                prediction_range=pred_range,
                model_contributions=await self._calculate_model_contributions(),
                risk_factors=await self._identify_risk_factors(market_data, correlation_analysis),
                opportunities=await self._identify_opportunities(market_data, regime_analysis)
            )

            self.last_market_insight = insight
            self.logger.info(f"Market analysis completed for {asset}: {regime_analysis['regime']} regime, {confidence:.2f} confidence")

            return insight

        except Exception as e:
            self.logger.error(f"❌ Market analysis failed: {e}")
            raise

    async def generate_trading_signal(self, market_data: Dict[str, Any]) -> Optional[TradingSignal]:
        """
        Generate comprehensive trading signal using hybrid AI analysis

        Args:
            market_data: Market data for analysis

        Returns:
            TradingSignal with AI-enhanced recommendations
        """
        try:
            # Get comprehensive market insight
            market_insight = await self.analyze_market(market_data)

            # Calculate signal components
            signal_components = await self._calculate_signal_components(market_insight)

            # Determine signal type and strength
            signal_type, strength = await self._determine_signal_type(signal_components)

            if signal_type == "hold" or strength < 0.3:
                return None

            # Calculate position sizing and risk parameters
            position_params = await self._calculate_position_parameters(
                market_insight, signal_type, strength
            )

            # Create trading signal
            signal = TradingSignal(
                asset=market_insight.asset,
                signal_type=signal_type,
                strength=strength,
                confidence=signal_components['overall_confidence'],
                entry_price=position_params['entry_price'],
                stop_loss=position_params['stop_loss'],
                take_profit=position_params['take_profit'],
                position_size=position_params['position_size'],
                ai_confidence=signal_components['ai_confidence'],
                sentiment_impact=signal_components['sentiment_impact'],
                regime_alignment=signal_components['regime_alignment'],
                correlation_risk=signal_components['correlation_risk'],
                session_favorability=signal_components['session_favorability'],
                rationale=await self._generate_rationale(market_insight, signal_components),
                risk_level=position_params['risk_level'],
                holding_period=position_params['holding_period'],
                market_insight=market_insight
            )

            # Validate signal against risk parameters
            if await self._validate_signal(signal):
                self.active_signals.append(signal)
                self.logger.info(f"✅ Generated {signal_type} signal for {signal.asset} with {signal.confidence:.2f} confidence")
                return signal
            else:
                self.logger.warning(f"⚠️ Signal validation failed for {market_insight.asset}")
                return None

        except Exception as e:
            self.logger.error(f"❌ Signal generation failed: {e}")
            return None

    async def update_performance(self, signal: TradingSignal, trade_result: Dict[str, Any]) -> None:
        """
        Update performance metrics and trigger adaptive learning

        Args:
            signal: Original trading signal
            trade_result: Actual trade outcome
        """
        try:
            # Record performance
            performance_record = {
                'timestamp': datetime.now().isoformat(),
                'asset': signal.asset,
                'signal_type': signal.signal_type,
                'predicted_confidence': signal.confidence,
                'actual_pnl': trade_result.get('pnl', 0.0),
                'success': trade_result.get('pnl', 0.0) > 0,
                'market_regime': signal.market_insight.regime_prediction,
                'sentiment_score': signal.market_insight.sentiment_score,
                'session': await self._get_active_session(signal.timestamp)
            }

            self.performance_history.append(performance_record)

            # Update prediction accuracy metrics
            await self._update_accuracy_metrics(signal, trade_result)

            # Trigger adaptive learning if enough data
            if len(self.performance_history) % self.config.adaptation_period == 0:
                await self._adaptive_learning_update()

            # Trigger model retraining if needed
            if len(self.performance_history) % self.config.retraining_period == 0:
                await self._retrain_models()

            self.logger.info(f"Performance updated for {signal.asset} signal: {performance_record['success']}")

        except Exception as e:
            self.logger.error(f"❌ Performance update failed: {e}")

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status and performance metrics"""
        try:
            # Calculate recent performance
            recent_performance = self._calculate_recent_performance()

            # Get model status
            model_status = await self._get_model_status()

            # Get correlation status
            correlation_status = await self.correlation_engine.get_status()

            status = {
                'system_health': 'healthy',
                'primary_asset': self.config.primary_asset.value,
                'models_loaded': len(self.ai_models),
                'active_signals': len(self.active_signals),
                'total_trades': len(self.performance_history),
                'recent_performance': recent_performance,
                'model_status': model_status,
                'correlation_status': correlation_status,
                'last_analysis': self.last_market_insight.timestamp.isoformat() if self.last_market_insight else None,
                'configuration': {
                    'enable_finbert': self.config.enable_finbert,
                    'enable_ensemble': self.config.enable_ensemble,
                    'enable_automl': self.config.enable_automl,
                    'confidence_threshold': self.config.confidence_threshold
                }
            }

            return status

        except Exception as e:
            self.logger.error(f"❌ Failed to get system status: {e}")
            return {'system_health': 'error', 'error': str(e)}

    # Private helper methods

    async def _initialize_ai_models(self) -> None:
        """Initialize AI/ML models"""
        try:
            if not HAS_ML_LIBS:
                self.logger.warning("ML libraries not available, skipping AI model initialization")
                return

            # Initialize ensemble predictor
            self.ai_models[AIModelType.ENSEMBLE_PREDICTOR] = await self._create_ensemble_model()

            # Initialize regime classifier
            self.ai_models[AIModelType.REGIME_CLASSIFIER] = await self._create_regime_classifier()

            # Initialize asset-specific models
            if self.config.primary_asset == TradingAsset.XAUUSD:
                self.ai_models[AIModelType.GOLD_SPECIALIST] = await self._create_gold_specialist_model()
            else:
                self.ai_models[AIModelType.FOREX_SPECIALIST] = await self._create_forex_specialist_model()

            self.logger.info(f"Initialized {len(self.ai_models)} AI models")

        except Exception as e:
            self.logger.error(f"❌ AI model initialization failed: {e}")

    async def _calculate_technical_scores(self, market_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate technical analysis scores using existing indicator system"""
        try:
            # This would integrate with the existing TradingIndicatorManager
            # For now, we'll simulate the scores

            prices = market_data.get('close_prices', [])
            volumes = market_data.get('volumes', [])

            if not prices:
                return {'overall': 0.5, 'volume': 0.5, 'momentum': 0.5}

            # Simple technical score calculation
            # In production, this would use the full 40+ indicator suite
            recent_prices = prices[-20:] if len(prices) >= 20 else prices

            # Momentum score
            momentum = (prices[-1] - recent_prices[0]) / recent_prices[0] if recent_prices[0] != 0 else 0
            momentum_score = min(max((momentum + 0.1) / 0.2, 0), 1)  # Normalize to 0-1

            # Volume score
            if volumes:
                recent_volumes = volumes[-20:] if len(volumes) >= 20 else volumes
                avg_volume = sum(recent_volumes) / len(recent_volumes)
                current_volume = volumes[-1] if volumes else avg_volume
                volume_score = min(current_volume / avg_volume, 2.0) / 2.0 if avg_volume > 0 else 0.5
            else:
                volume_score = 0.5

            # Overall technical score (weighted average)
            overall_score = (momentum_score * 0.6 + volume_score * 0.4)

            return {
                'overall': overall_score,
                'volume': volume_score,
                'momentum': momentum_score
            }

        except Exception as e:
            self.logger.error(f"❌ Technical score calculation failed: {e}")
            return {'overall': 0.5, 'volume': 0.5, 'momentum': 0.5}

    async def _analyze_sentiment(self, news_data: List[Dict]) -> float:
        """Analyze market sentiment using FinBERT"""
        try:
            if not hasattr(self, 'sentiment_analyzer'):
                return 0.5  # Neutral

            sentiment_score = await self.sentiment_analyzer.analyze_news(news_data)
            return sentiment_score

        except Exception as e:
            self.logger.error(f"❌ Sentiment analysis failed: {e}")
            return 0.5

    async def _ensemble_prediction(self, market_data: Dict, technical_scores: Dict,
                                 regime_analysis: Dict, sentiment_score: float) -> Tuple[float, float, Tuple[float, float]]:
        """Generate ensemble price prediction"""
        try:
            if not self.config.enable_ensemble or AIModelType.ENSEMBLE_PREDICTOR not in self.ai_models:
                # Fallback prediction
                current_price = market_data.get('close', 1.0)
                return current_price, 0.5, (current_price * 0.99, current_price * 1.01)

            # Prepare features for ensemble model
            features = [
                technical_scores['overall'],
                technical_scores['momentum'],
                sentiment_score,
                regime_analysis.get('trend_strength', 0.5),
                regime_analysis.get('volatility', 0.5)
            ]

            # Get prediction from ensemble model
            model = self.ai_models[AIModelType.ENSEMBLE_PREDICTOR]
            prediction = model.predict([features])[0]

            # Calculate confidence based on model uncertainty
            confidence = min(max(abs(prediction - 0.5) * 2, 0.1), 0.95)

            # Calculate prediction range
            current_price = market_data.get('close', 1.0)
            predicted_price = current_price * (1 + prediction * 0.1)  # Max 10% move
            range_width = current_price * 0.05 * (1 - confidence)  # Wider range for lower confidence

            pred_range = (
                predicted_price - range_width,
                predicted_price + range_width
            )

            return predicted_price, confidence, pred_range

        except Exception as e:
            self.logger.error(f"❌ Ensemble prediction failed: {e}")
            current_price = market_data.get('close', 1.0)
            return current_price, 0.3, (current_price * 0.99, current_price * 1.01)

    async def _calculate_model_contributions(self) -> Dict[str, float]:
        """Calculate contribution weights of different models"""
        return {
            'technical_indicators': 0.4,
            'sentiment_analysis': 0.2,
            'regime_detection': 0.2,
            'correlation_analysis': 0.1,
            'session_analysis': 0.1
        }

    async def _identify_risk_factors(self, market_data: Dict, correlation_analysis: Dict) -> List[str]:
        """Identify current risk factors"""
        risk_factors = []

        # High volatility risk
        if market_data.get('volatility', 0) > 0.7:
            risk_factors.append("High market volatility")

        # Correlation risk
        if max(correlation_analysis.get('correlations', {}).values(), default=0) > 0.8:
            risk_factors.append("High correlation risk")

        # Session risk (for forex)
        current_hour = datetime.now().hour
        if 0 <= current_hour <= 6:  # Low liquidity hours
            risk_factors.append("Low liquidity session")

        return risk_factors

    async def _identify_opportunities(self, market_data: Dict, regime_analysis: Dict) -> List[str]:
        """Identify trading opportunities"""
        opportunities = []

        # Strong trend opportunity
        if regime_analysis.get('trend_strength', 0) > 0.7:
            opportunities.append("Strong trend momentum")

        # High volume opportunity
        if market_data.get('volume_ratio', 1) > 1.5:
            opportunities.append("Above average volume")

        # Session opportunity
        current_hour = datetime.now().hour
        if 8 <= current_hour <= 16:  # Active trading hours
            opportunities.append("Active trading session")

        return opportunities

    async def _calculate_signal_components(self, insight: MarketInsight) -> Dict[str, float]:
        """Calculate signal strength components"""
        try:
            # AI confidence component
            ai_confidence = insight.confidence

            # Sentiment impact
            sentiment_impact = abs(insight.sentiment_score - 0.5) * 2  # 0-1 scale

            # Regime alignment (how well current conditions match prediction)
            regime_strength = 0.8 if insight.regime_prediction in ['trending', 'bullish', 'bearish'] else 0.4

            # Correlation risk (inverse of max correlation)
            max_correlation = max(insight.correlation_strength.values()) if insight.correlation_strength else 0
            correlation_risk = 1 - max_correlation

            # Session favorability
            session_favorability = max(insight.session_activity.values()) if insight.session_activity else 0.5

            # Overall confidence
            overall_confidence = (
                ai_confidence * 0.3 +
                regime_strength * 0.3 +
                sentiment_impact * 0.2 +
                correlation_risk * 0.1 +
                session_favorability * 0.1
            )

            return {
                'ai_confidence': ai_confidence,
                'sentiment_impact': sentiment_impact,
                'regime_alignment': regime_strength,
                'correlation_risk': correlation_risk,
                'session_favorability': session_favorability,
                'overall_confidence': overall_confidence
            }

        except Exception as e:
            self.logger.error(f"❌ Signal component calculation failed: {e}")
            return {
                'ai_confidence': 0.5,
                'sentiment_impact': 0.5,
                'regime_alignment': 0.5,
                'correlation_risk': 0.5,
                'session_favorability': 0.5,
                'overall_confidence': 0.5
            }

    async def _determine_signal_type(self, components: Dict[str, float]) -> Tuple[str, float]:
        """Determine signal type and strength"""
        try:
            overall_confidence = components['overall_confidence']

            if overall_confidence < self.config.confidence_threshold:
                return "hold", 0.0

            # Determine direction based on multiple factors
            bullish_factors = 0
            bearish_factors = 0

            if components['ai_confidence'] > 0.6:
                bullish_factors += 1
            elif components['ai_confidence'] < 0.4:
                bearish_factors += 1

            if components['sentiment_impact'] > 0.6:
                bullish_factors += 1
            elif components['sentiment_impact'] < 0.4:
                bearish_factors += 1

            if components['regime_alignment'] > 0.7:
                bullish_factors += 1

            # Determine signal
            if bullish_factors > bearish_factors:
                signal_type = "buy"
                strength = min(overall_confidence * (bullish_factors / 3), 1.0)
            elif bearish_factors > bullish_factors:
                signal_type = "sell"
                strength = min(overall_confidence * (bearish_factors / 3), 1.0)
            else:
                signal_type = "hold"
                strength = 0.0

            return signal_type, strength

        except Exception as e:
            self.logger.error(f"❌ Signal type determination failed: {e}")
            return "hold", 0.0

    async def _calculate_position_parameters(self, insight: MarketInsight,
                                           signal_type: str, strength: float) -> Dict[str, Any]:
        """Calculate position sizing and risk parameters"""
        try:
            current_price = insight.price_prediction

            # Dynamic position sizing based on confidence and volatility
            base_position_size = 0.02  # 2% base risk
            confidence_multiplier = insight.confidence
            volatility_adjustment = 1 - (insight.technical_score * 0.3)  # Lower size for high volatility

            position_size = base_position_size * confidence_multiplier * volatility_adjustment
            position_size = min(max(position_size, 0.005), 0.05)  # 0.5% to 5% range

            # Calculate stop loss and take profit
            if signal_type == "buy":
                stop_loss = current_price * (1 - 0.02 * (1 / insight.confidence))  # Dynamic SL
                take_profit = current_price * (1 + 0.04 * insight.confidence)  # Dynamic TP
            else:  # sell
                stop_loss = current_price * (1 + 0.02 * (1 / insight.confidence))
                take_profit = current_price * (1 - 0.04 * insight.confidence)

            # Determine risk level
            if insight.confidence > 0.8 and strength > 0.7:
                risk_level = "low"
                holding_period = "short"
            elif insight.confidence > 0.6:
                risk_level = "medium"
                holding_period = "medium"
            else:
                risk_level = "high"
                holding_period = "short"

            return {
                'entry_price': current_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'position_size': position_size,
                'risk_level': risk_level,
                'holding_period': holding_period
            }

        except Exception as e:
            self.logger.error(f"❌ Position parameter calculation failed: {e}")
            return {
                'entry_price': insight.price_prediction,
                'stop_loss': insight.price_prediction * 0.98,
                'take_profit': insight.price_prediction * 1.02,
                'position_size': 0.01,
                'risk_level': 'medium',
                'holding_period': 'short'
            }

    async def _generate_rationale(self, insight: MarketInsight, components: Dict) -> str:
        """Generate human-readable trading rationale"""
        try:
            rationale_parts = []

            # Market regime
            rationale_parts.append(f"Market regime: {insight.regime_prediction}")

            # Confidence level
            conf_level = "high" if insight.confidence > 0.8 else "medium" if insight.confidence > 0.6 else "low"
            rationale_parts.append(f"AI confidence: {conf_level} ({insight.confidence:.2f})")

            # Sentiment
            if insight.sentiment_score > 0.6:
                rationale_parts.append("Positive market sentiment")
            elif insight.sentiment_score < 0.4:
                rationale_parts.append("Negative market sentiment")

            # Session activity
            if insight.session_activity:
                active_sessions = [k for k, v in insight.session_activity.items() if v > 0.7]
                if active_sessions:
                    rationale_parts.append(f"Active sessions: {', '.join(active_sessions)}")

            # Risk factors
            if insight.risk_factors:
                rationale_parts.append(f"Risk factors: {', '.join(insight.risk_factors[:2])}")

            return "; ".join(rationale_parts)

        except Exception as e:
            self.logger.error(f"❌ Rationale generation failed: {e}")
            return f"AI analysis for {insight.asset} with {insight.confidence:.2f} confidence"

    async def _validate_signal(self, signal: TradingSignal) -> bool:
        """Validate trading signal against risk parameters"""
        try:
            # Check confidence threshold
            if signal.confidence < self.config.confidence_threshold:
                return False

            # Check correlation risk
            if signal.correlation_risk > self.config.max_correlation_exposure:
                return False

            # Check position size limits
            if signal.position_size > 0.05 or signal.position_size < 0.005:
                return False

            # Check for conflicting signals
            for active_signal in self.active_signals:
                if (active_signal.asset == signal.asset and
                    active_signal.signal_type != signal.signal_type and
                    active_signal.timestamp > datetime.now() - timedelta(hours=1)):
                    return False

            return True

        except Exception as e:
            self.logger.error(f"❌ Signal validation failed: {e}")
            return False

    async def _update_accuracy_metrics(self, signal: TradingSignal, trade_result: Dict) -> None:
        """Update prediction accuracy metrics"""
        try:
            asset = signal.asset
            if asset not in self.prediction_accuracy:
                self.prediction_accuracy[asset] = {'total': 0, 'correct': 0}

            self.prediction_accuracy[asset]['total'] += 1

            # Check if prediction was correct
            actual_pnl = trade_result.get('pnl', 0.0)
            predicted_direction = signal.signal_type

            if ((predicted_direction == 'buy' and actual_pnl > 0) or
                (predicted_direction == 'sell' and actual_pnl > 0)):
                self.prediction_accuracy[asset]['correct'] += 1

        except Exception as e:
            self.logger.error(f"❌ Accuracy metrics update failed: {e}")

    async def _adaptive_learning_update(self) -> None:
        """Perform adaptive learning based on recent performance"""
        try:
            if not self.config.enable_automl or not HAS_ML_LIBS:
                return

            # Analyze recent performance patterns
            recent_trades = self.performance_history[-self.config.adaptation_period:]

            # Update model weights based on performance
            await self.automl_optimizer.update_model_weights(recent_trades)

            # Adjust confidence thresholds
            success_rate = sum(1 for trade in recent_trades if trade['success']) / len(recent_trades)

            if success_rate < 0.5:
                self.config.confidence_threshold = min(self.config.confidence_threshold * 1.05, 0.9)
            elif success_rate > 0.7:
                self.config.confidence_threshold = max(self.config.confidence_threshold * 0.98, 0.6)

            self.logger.info(f"Adaptive learning update completed. New confidence threshold: {self.config.confidence_threshold:.3f}")

        except Exception as e:
            self.logger.error(f"❌ Adaptive learning update failed: {e}")

    async def _retrain_models(self) -> None:
        """Retrain AI models with latest data"""
        try:
            if not self.config.enable_ensemble or not HAS_ML_LIBS:
                return

            self.logger.info("Starting model retraining...")

            # Prepare training data from performance history
            training_data = await self._prepare_training_data()

            if len(training_data) < 100:  # Need minimum data for training
                self.logger.warning("Insufficient data for model retraining")
                return

            # Retrain ensemble model
            await self._retrain_ensemble_model(training_data)

            # Retrain regime classifier if needed
            await self._retrain_regime_classifier(training_data)

            self.logger.info("Model retraining completed")

        except Exception as e:
            self.logger.error(f"❌ Model retraining failed: {e}")

    async def _calculate_recent_performance(self) -> Dict[str, float]:
        """Calculate recent performance metrics"""
        if not self.performance_history:
            return {'win_rate': 0.0, 'total_trades': 0, 'avg_pnl': 0.0}

        recent_trades = self.performance_history[-50:]  # Last 50 trades

        win_rate = sum(1 for trade in recent_trades if trade['success']) / len(recent_trades)
        total_trades = len(recent_trades)
        avg_pnl = sum(trade['actual_pnl'] for trade in recent_trades) / len(recent_trades)

        return {
            'win_rate': win_rate,
            'total_trades': total_trades,
            'avg_pnl': avg_pnl
        }

    async def _get_model_status(self) -> Dict[str, str]:
        """Get status of all AI models"""
        status = {}
        for model_type, model in self.ai_models.items():
            if model is not None:
                status[model_type.value] = "active"
            else:
                status[model_type.value] = "inactive"
        return status

    async def _get_active_session(self, timestamp: datetime) -> str:
        """Get active trading session for timestamp"""
        hour = timestamp.hour
        if 0 <= hour < 6:
            return "sydney"
        elif 6 <= hour < 15:
            return "london"
        elif 15 <= hour < 22:
            return "newyork"
        else:
            return "asian"

    # Placeholder methods for AI models (to be implemented)
    async def _create_ensemble_model(self):
        """Create ensemble ML model"""
        if not HAS_ML_LIBS:
            return None
        # Placeholder for actual ensemble model creation
        return RandomForestRegressor(n_estimators=100, random_state=42)

    async def _create_regime_classifier(self):
        """Create market regime classifier"""
        if not HAS_ML_LIBS:
            return None
        # Placeholder for regime classifier
        return GradientBoostingRegressor(n_estimators=50, random_state=42)

    async def _create_gold_specialist_model(self):
        """Create gold-specific ML model"""
        if not HAS_ML_LIBS:
            return None
        # Placeholder for gold specialist model
        return RandomForestRegressor(n_estimators=75, random_state=42)

    async def _create_forex_specialist_model(self):
        """Create forex-specific ML model"""
        if not HAS_ML_LIBS:
            return None
        # Placeholder for forex specialist model
        return GradientBoostingRegressor(n_estimators=75, random_state=42)

    async def _prepare_training_data(self):
        """Prepare training data from performance history"""
        # Placeholder for training data preparation
        return []

    async def _retrain_ensemble_model(self, training_data):
        """Retrain the ensemble model"""
        # Placeholder for ensemble retraining
        pass

    async def _retrain_regime_classifier(self, training_data):
        """Retrain the regime classifier"""
        # Placeholder for regime classifier retraining
        pass


# Export main components
__all__ = [
    'HybridAITradingEngine',
    'HybridAIConfig',
    'TradingAsset',
    'MarketInsight',
    'TradingSignal',
    'AIModelType'
]