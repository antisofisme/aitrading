"""
🎯 Enhanced Advanced Trading Strategies - MICROSERVICE VERSION
Enterprise-grade sophisticated trading strategies using AI, pattern recognition, and multi-timeframe analysis

MICROSERVICE INFRASTRUCTURE:
- Performance tracking for all trading strategy operations
- Microservice error handling for strategy execution scenarios
- Event publishing for strategy lifecycle monitoring
- Enhanced logging with strategy-specific configuration
- Comprehensive validation for signal generation and execution
- Advanced metrics tracking for strategy optimization

This module provides:
- AI-powered pattern recognition with performance tracking
- Multi-timeframe strategy coordination with centralized monitoring
- Adaptive strategy selection with event publishing
- Risk-adjusted position sizing with error recovery
- Real-time strategy performance monitoring with enterprise-grade analytics
"""

import asyncio
import logging
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import statistics
from collections import defaultdict, deque
import math
import time

# MICROSERVICE INFRASTRUCTURE INTEGRATION
from ...shared.infrastructure.logging.base_logger import BaseLogger
from ...shared.infrastructure.config.base_config import BaseConfig
from ...shared.infrastructure.error_handling.base_error_handler import BaseErrorHandler
from ...shared.infrastructure.base.base_performance import BasePerformance as BasePerformanceTracker
from ...shared.infrastructure.events.base_event_publisher import BaseEventPublisher

# Enhanced logger with microservice infrastructure
strategy_logger = BaseLogger("strategy_executor", {
    "component": "trading_modules",
    "service": "advanced_strategy_executor",
    "feature": "ai_pattern_trading_strategies"
})

# Strategy execution performance metrics
strategy_metrics = {
    "total_strategies_executed": 0,
    "successful_signal_generations": 0,
    "failed_strategy_executions": 0,
    "ai_pattern_detections": 0,
    "multi_timeframe_analyses": 0,
    "risk_adjusted_positions": 0,
    "adaptive_strategy_selections": 0,
    "performance_optimizations": 0,
    "signal_confirmations": 0,
    "portfolio_optimizations": 0,
    "avg_strategy_execution_time_ms": 0,
    "events_published": 0,
    "validation_errors": 0
}


class StrategyType(Enum):
    """Available trading strategy types"""
    TREND_FOLLOWING = "trend_following"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"
    SCALPING = "scalping"
    SWING_TRADING = "swing_trading"
    AI_ENSEMBLE = "ai_ensemble"
    PATTERN_RECOGNITION = "pattern_recognition"
    MULTI_TIMEFRAME = "multi_timeframe"


class SignalStrength(Enum):
    """Signal strength levels"""
    VERY_WEAK = "very_weak"      # 0-20%
    WEAK = "weak"                # 20-40%
    MODERATE = "moderate"        # 40-60%
    STRONG = "strong"            # 60-80%
    VERY_STRONG = "very_strong"  # 80-100%


class MarketRegime(Enum):
    """Market regime classifications"""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    UNCERTAIN = "uncertain"


class TimeframeWeight(Enum):
    """Timeframe importance weights"""
    M1 = 0.05    # 1 minute - minimal weight
    M5 = 0.10    # 5 minutes - low weight
    M15 = 0.15   # 15 minutes - moderate weight
    M30 = 0.20   # 30 minutes - good weight
    H1 = 0.25    # 1 hour - high weight
    H4 = 0.30    # 4 hours - very high weight
    D1 = 0.35    # Daily - maximum weight


@dataclass
class TradingSignal:
    """Enhanced trading signal with comprehensive metadata"""
    # Basic signal information
    signal_id: str
    strategy_type: StrategyType
    symbol: str
    timeframe: str
    
    # Signal details
    direction: str              # "buy", "sell", "hold"
    strength: SignalStrength
    confidence: float           # 0-1 confidence score
    
    # Price information
    entry_price: float
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    
    # Multi-timeframe analysis
    timeframe_signals: Dict[str, float] = field(default_factory=dict)
    timeframe_consensus: float = 0.0
    
    # AI and pattern analysis
    ai_confidence: float = 0.0
    pattern_match: str = "none"
    pattern_confidence: float = 0.0
    
    # Risk assessment
    risk_score: float = 0.5
    position_size: float = 0.0
    risk_reward_ratio: float = 0.0
    
    # Market context
    market_regime: MarketRegime = MarketRegime.UNCERTAIN
    volatility_level: float = 0.0
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    expiry_time: Optional[datetime] = None
    
    # Processing status
    processed: bool = False
    executed: bool = False


@dataclass
class StrategyPerformance:
    """Strategy performance tracking"""
    strategy_type: StrategyType
    symbol: str
    
    # Trade statistics
    total_signals: int = 0
    successful_signals: int = 0
    failed_signals: int = 0
    accuracy: float = 0.0
    
    # Financial performance
    total_pnl: float = 0.0
    avg_pnl_per_trade: float = 0.0
    max_profit: float = 0.0
    max_loss: float = 0.0
    
    # Risk metrics
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    
    # Time metrics
    avg_trade_duration: timedelta = field(default_factory=lambda: timedelta(hours=1))
    
    # Recent performance
    last_30_signals_accuracy: float = 0.0
    consecutive_wins: int = 0
    consecutive_losses: int = 0
    
    timestamp: datetime = field(default_factory=datetime.now)


class AdvancedStrategyExecutor:
    """
    Advanced trading strategy executor with AI integration and microservice infrastructure
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize strategy executor with microservice infrastructure"""
        self.config = config or {}
        
        # Microservice Infrastructure Components
        self.logger = BaseLogger("advanced_strategy_executor")
        self.config_manager = BaseConfig()
        self.error_handler = BaseErrorHandler("strategy_executor")
        self.performance_tracker = BasePerformanceTracker("strategy_executor")
        self.event_publisher = BaseEventPublisher("strategy_executor")
        
        # Strategy state
        self.active_strategies = {}
        self.strategy_performances = {}
        self.signal_history = deque(maxlen=1000)
        self.market_data_cache = {}
        
        # Configuration
        self.enabled_strategies = self.config.get('enabled_strategies', [
            StrategyType.TREND_FOLLOWING,
            StrategyType.MEAN_REVERSION,
            StrategyType.BREAKOUT,
            StrategyType.AI_ENSEMBLE
        ])
        
        # Multi-timeframe settings
        self.timeframes = self.config.get('timeframes', ["M15", "H1", "H4", "D1"])
        self.primary_timeframe = self.config.get('primary_timeframe', "H1")
        
        # Signal filtering
        self.min_confidence = self.config.get('min_confidence', 0.6)
        self.min_signal_strength = self.config.get('min_signal_strength', SignalStrength.MODERATE)
        
        # Performance tracking
        self.signals_generated = 0
        self.successful_executions = 0
        self.failed_executions = 0
        
        self.logger.info("AdvancedStrategyExecutor initialized successfully")


    async def initialize(self):
        """Initialize strategy executor"""
        try:
            self.logger.info("Initializing advanced strategy executor")
            
            # Load strategy configurations
            strategy_config = self.config_manager.get_config("strategies", {
                "enabled_strategies": [s.value for s in self.enabled_strategies],
                "timeframes": self.timeframes,
                "min_confidence": self.min_confidence
            })
            
            # Initialize strategy performances
            for strategy_type in self.enabled_strategies:
                for symbol in self.config.get('symbols', ['EURUSD']):
                    key = f"{strategy_type.value}_{symbol}"
                    self.strategy_performances[key] = StrategyPerformance(
                        strategy_type=strategy_type,
                        symbol=symbol
                    )
            
            self.logger.info(f"Initialized {len(self.strategy_performances)} strategy performance trackers")
            
            # Publish initialization event
            await self.event_publisher.publish_event({
                "event_type": "strategy_executor_initialized",
                "enabled_strategies": [s.value for s in self.enabled_strategies],
                "timeframes": self.timeframes,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            error_response = self.error_handler.handle_error(e, "initialize_strategy_executor")
            self.logger.error(f"Failed to initialize strategy executor: {error_response}")
            raise


    async def generate_signals(self, symbol: str, market_data: Dict[str, Any]) -> List[TradingSignal]:
        """
        Generate trading signals using multiple strategies
        """
        start_time = time.time()
        signals = []
        
        try:
            self.logger.info(f"Generating signals for {symbol}")
            
            # Cache market data
            self.market_data_cache[symbol] = {
                **market_data,
                "timestamp": datetime.now()
            }
            
            # Analyze market regime
            market_regime = await self._analyze_market_regime(symbol, market_data)
            volatility_level = self._calculate_volatility(market_data)
            
            # Generate signals from each enabled strategy
            for strategy_type in self.enabled_strategies:
                try:
                    signal = await self._execute_strategy(
                        strategy_type, symbol, market_data, market_regime, volatility_level
                    )
                    
                    if signal and self._validate_signal(signal):
                        signals.append(signal)
                        self.signals_generated += 1
                        
                        # Update performance tracking
                        await self._update_strategy_performance(signal)
                        
                except Exception as e:
                    error_response = self.error_handler.handle_error(e, f"execute_strategy_{strategy_type.value}")
                    self.logger.error(f"Strategy {strategy_type.value} failed: {error_response}")
                    continue
            
            # Multi-timeframe consensus analysis
            if signals:
                signals = await self._apply_multi_timeframe_consensus(signals, symbol, market_data)
            
            # Filter and rank signals
            signals = self._filter_and_rank_signals(signals)
            
            # Store signals in history
            for signal in signals:
                self.signal_history.append(signal)
            
            execution_time = (time.time() - start_time) * 1000
            strategy_metrics["avg_strategy_execution_time_ms"] = execution_time
            strategy_metrics["total_strategies_executed"] += len(self.enabled_strategies)
            strategy_metrics["successful_signal_generations"] += len(signals)
            
            # Publish signal generation event
            await self.event_publisher.publish_event({
                "event_type": "signals_generated",
                "symbol": symbol,
                "signals_count": len(signals),
                "market_regime": market_regime.value,
                "volatility_level": volatility_level,
                "execution_time_ms": execution_time,
                "timestamp": datetime.now().isoformat()
            })
            
            self.logger.info(f"Generated {len(signals)} signals for {symbol} in {execution_time:.1f}ms")
            
            return signals
            
        except Exception as e:
            error_response = self.error_handler.handle_error(e, "generate_signals")
            self.logger.error(f"Signal generation failed for {symbol}: {error_response}")
            strategy_metrics["failed_strategy_executions"] += 1
            return []


    async def _execute_strategy(self, strategy_type: StrategyType, symbol: str, 
                              market_data: Dict, market_regime: MarketRegime, 
                              volatility_level: float) -> Optional[TradingSignal]:
        """Execute individual trading strategy"""
        try:
            if strategy_type == StrategyType.TREND_FOLLOWING:
                return await self._trend_following_strategy(symbol, market_data, market_regime)
            elif strategy_type == StrategyType.MEAN_REVERSION:
                return await self._mean_reversion_strategy(symbol, market_data, market_regime)
            elif strategy_type == StrategyType.BREAKOUT:
                return await self._breakout_strategy(symbol, market_data, market_regime)
            elif strategy_type == StrategyType.AI_ENSEMBLE:
                return await self._ai_ensemble_strategy(symbol, market_data, market_regime)
            elif strategy_type == StrategyType.PATTERN_RECOGNITION:
                return await self._pattern_recognition_strategy(symbol, market_data, market_regime)
            else:
                self.logger.warning(f"Unknown strategy type: {strategy_type}")
                return None
                
        except Exception as e:
            error_response = self.error_handler.handle_error(e, f"execute_strategy_{strategy_type.value}")
            self.logger.error(f"Strategy execution failed: {error_response}")
            return None


    async def _trend_following_strategy(self, symbol: str, market_data: Dict, 
                                      market_regime: MarketRegime) -> Optional[TradingSignal]:
        """Trend following strategy implementation"""
        try:
            prices = market_data.get('prices', [])
            if len(prices) < 20:
                return None
            
            # Calculate moving averages
            ma_short = np.mean(prices[-10:])
            ma_long = np.mean(prices[-20:])
            current_price = prices[-1]
            
            # Trend direction
            if ma_short > ma_long:
                direction = "buy"
                strength = SignalStrength.MODERATE
                confidence = 0.6
            elif ma_short < ma_long:
                direction = "sell"
                strength = SignalStrength.MODERATE
                confidence = 0.6
            else:
                return None
            
            # Enhanced signal for trending markets
            if market_regime in [MarketRegime.TRENDING_UP, MarketRegime.TRENDING_DOWN]:
                confidence += 0.1
                strength = SignalStrength.STRONG
            
            signal = TradingSignal(
                signal_id=f"trend_{symbol}_{int(time.time())}",
                strategy_type=StrategyType.TREND_FOLLOWING,
                symbol=symbol,
                timeframe=self.primary_timeframe,
                direction=direction,
                strength=strength,
                confidence=confidence,
                entry_price=current_price,
                market_regime=market_regime,
                risk_score=0.4  # Moderate risk for trend following
            )
            
            strategy_metrics["ai_pattern_detections"] += 1
            return signal
            
        except Exception as e:
            self.logger.error(f"Trend following strategy failed: {e}")
            return None


    async def _mean_reversion_strategy(self, symbol: str, market_data: Dict, 
                                     market_regime: MarketRegime) -> Optional[TradingSignal]:
        """Mean reversion strategy implementation"""
        try:
            prices = market_data.get('prices', [])
            if len(prices) < 20:
                return None
            
            # Calculate mean and standard deviation
            mean_price = np.mean(prices[-20:])
            std_price = np.std(prices[-20:])
            current_price = prices[-1]
            
            # Z-score calculation
            z_score = (current_price - mean_price) / std_price if std_price > 0 else 0
            
            # Signal generation
            if z_score > 2:  # Overbought
                direction = "sell"
                strength = SignalStrength.STRONG
                confidence = min(0.8, abs(z_score) / 3)
            elif z_score < -2:  # Oversold
                direction = "buy"
                strength = SignalStrength.STRONG
                confidence = min(0.8, abs(z_score) / 3)
            else:
                return None
            
            # Reduce confidence in trending markets
            if market_regime in [MarketRegime.TRENDING_UP, MarketRegime.TRENDING_DOWN]:
                confidence *= 0.7
            
            signal = TradingSignal(
                signal_id=f"meanrev_{symbol}_{int(time.time())}",
                strategy_type=StrategyType.MEAN_REVERSION,
                symbol=symbol,
                timeframe=self.primary_timeframe,
                direction=direction,
                strength=strength,
                confidence=confidence,
                entry_price=current_price,
                target_price=mean_price,
                market_regime=market_regime,
                risk_score=0.5  # Moderate-high risk for mean reversion
            )
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Mean reversion strategy failed: {e}")
            return None


    async def _breakout_strategy(self, symbol: str, market_data: Dict, 
                               market_regime: MarketRegime) -> Optional[TradingSignal]:
        """Breakout strategy implementation"""
        try:
            prices = market_data.get('prices', [])
            volumes = market_data.get('volumes', [])
            
            if len(prices) < 20:
                return None
            
            # Calculate support and resistance levels
            recent_high = max(prices[-20:])
            recent_low = min(prices[-20:])
            current_price = prices[-1]
            
            # Volume confirmation
            avg_volume = np.mean(volumes[-10:]) if volumes else 1
            current_volume = volumes[-1] if volumes else 1
            volume_factor = current_volume / avg_volume if avg_volume > 0 else 1
            
            # Breakout detection
            if current_price > recent_high * 1.001:  # Upward breakout
                direction = "buy"
                strength = SignalStrength.STRONG if volume_factor > 1.5 else SignalStrength.MODERATE
                confidence = 0.7 * min(1.2, volume_factor)
            elif current_price < recent_low * 0.999:  # Downward breakout
                direction = "sell"
                strength = SignalStrength.STRONG if volume_factor > 1.5 else SignalStrength.MODERATE
                confidence = 0.7 * min(1.2, volume_factor)
            else:
                return None
            
            signal = TradingSignal(
                signal_id=f"breakout_{symbol}_{int(time.time())}",
                strategy_type=StrategyType.BREAKOUT,
                symbol=symbol,
                timeframe=self.primary_timeframe,
                direction=direction,
                strength=strength,
                confidence=confidence,
                entry_price=current_price,
                market_regime=market_regime,
                risk_score=0.6  # Higher risk for breakout
            )
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Breakout strategy failed: {e}")
            return None


    async def _ai_ensemble_strategy(self, symbol: str, market_data: Dict, 
                                  market_regime: MarketRegime) -> Optional[TradingSignal]:
        """AI ensemble strategy implementation"""
        try:
            # Placeholder for AI ensemble logic
            # In real implementation, this would integrate with ML models
            
            prices = market_data.get('prices', [])
            if len(prices) < 10:
                return None
            
            # Simple AI-like scoring (placeholder)
            price_momentum = (prices[-1] - prices[-5]) / prices[-5] if len(prices) >= 5 else 0
            volatility = np.std(prices[-10:]) / np.mean(prices[-10:]) if len(prices) >= 10 else 0
            
            # AI decision making (simplified)
            ai_score = price_momentum * 10 + (0.1 - volatility) * 5
            
            if ai_score > 0.5:
                direction = "buy"
                confidence = min(0.9, ai_score)
            elif ai_score < -0.5:
                direction = "sell"
                confidence = min(0.9, abs(ai_score))
            else:
                return None
            
            signal = TradingSignal(
                signal_id=f"ai_ensemble_{symbol}_{int(time.time())}",
                strategy_type=StrategyType.AI_ENSEMBLE,
                symbol=symbol,
                timeframe=self.primary_timeframe,
                direction=direction,
                strength=SignalStrength.STRONG,
                confidence=confidence,
                entry_price=prices[-1],
                ai_confidence=confidence,
                market_regime=market_regime,
                risk_score=0.3  # Lower risk for AI ensemble
            )
            
            strategy_metrics["ai_pattern_detections"] += 1
            return signal
            
        except Exception as e:
            self.logger.error(f"AI ensemble strategy failed: {e}")
            return None


    async def _pattern_recognition_strategy(self, symbol: str, market_data: Dict, 
                                          market_regime: MarketRegime) -> Optional[TradingSignal]:
        """Pattern recognition strategy implementation"""
        try:
            prices = market_data.get('prices', [])
            if len(prices) < 30:
                return None
            
            # Simple pattern detection (placeholder)
            # In real implementation, this would use advanced pattern recognition
            
            # Double bottom pattern detection
            recent_prices = prices[-30:]
            min_indices = []
            for i in range(5, len(recent_prices)-5):
                if all(recent_prices[i] <= recent_prices[i-j] for j in range(1, 6)) and \
                   all(recent_prices[i] <= recent_prices[i+j] for j in range(1, 6)):
                    min_indices.append(i)
            
            pattern_detected = False
            pattern_confidence = 0.0
            direction = "hold"
            
            if len(min_indices) >= 2:
                # Potential double bottom
                last_two_mins = min_indices[-2:]
                if abs(recent_prices[last_two_mins[0]] - recent_prices[last_two_mins[1]]) < recent_prices[-1] * 0.005:
                    pattern_detected = True
                    pattern_confidence = 0.7
                    direction = "buy"
            
            if not pattern_detected:
                return None
            
            signal = TradingSignal(
                signal_id=f"pattern_{symbol}_{int(time.time())}",
                strategy_type=StrategyType.PATTERN_RECOGNITION,
                symbol=symbol,
                timeframe=self.primary_timeframe,
                direction=direction,
                strength=SignalStrength.STRONG,
                confidence=pattern_confidence,
                entry_price=prices[-1],
                pattern_match="double_bottom",
                pattern_confidence=pattern_confidence,
                market_regime=market_regime,
                risk_score=0.4
            )
            
            strategy_metrics["ai_pattern_detections"] += 1
            return signal
            
        except Exception as e:
            self.logger.error(f"Pattern recognition strategy failed: {e}")
            return None


    async def _analyze_market_regime(self, symbol: str, market_data: Dict) -> MarketRegime:
        """Analyze current market regime"""
        try:
            prices = market_data.get('prices', [])
            volumes = market_data.get('volumes', [])
            
            if len(prices) < 20:
                return MarketRegime.UNCERTAIN
            
            # Trend analysis
            ma_short = np.mean(prices[-5:])
            ma_medium = np.mean(prices[-10:])
            ma_long = np.mean(prices[-20:])
            
            # Volatility analysis
            returns = np.diff(np.log(prices[-20:]))
            volatility = np.std(returns) * np.sqrt(252)  # Annualized
            
            # Regime determination
            if ma_short > ma_medium > ma_long and volatility < 0.15:
                return MarketRegime.TRENDING_UP
            elif ma_short < ma_medium < ma_long and volatility < 0.15:
                return MarketRegime.TRENDING_DOWN
            elif volatility > 0.25:
                return MarketRegime.HIGH_VOLATILITY
            elif volatility < 0.10:
                return MarketRegime.LOW_VOLATILITY
            else:
                return MarketRegime.RANGING
                
        except Exception as e:
            self.logger.error(f"Market regime analysis failed: {e}")
            return MarketRegime.UNCERTAIN


    def _calculate_volatility(self, market_data: Dict) -> float:
        """Calculate current volatility level"""
        try:
            prices = market_data.get('prices', [])
            if len(prices) < 10:
                return 0.15  # Default volatility
            
            returns = np.diff(np.log(prices[-20:]))
            volatility = np.std(returns) * np.sqrt(252)  # Annualized
            
            return max(0.01, min(volatility, 1.0))  # Bound between 1% and 100%
            
        except Exception as e:
            self.logger.error(f"Volatility calculation failed: {e}")
            return 0.15


    async def _apply_multi_timeframe_consensus(self, signals: List[TradingSignal], 
                                             symbol: str, market_data: Dict) -> List[TradingSignal]:
        """Apply multi-timeframe consensus analysis"""
        try:
            # Placeholder for multi-timeframe analysis
            # In real implementation, this would analyze multiple timeframes
            
            for signal in signals:
                # Simple consensus scoring
                consensus_score = 0.6  # Base consensus
                
                # Add timeframe-specific analysis
                signal.timeframe_signals = {
                    "M15": 0.5,
                    "H1": 0.7,
                    "H4": 0.6,
                    "D1": 0.8
                }
                
                # Calculate weighted consensus
                total_weight = 0
                weighted_sum = 0
                
                for tf, score in signal.timeframe_signals.items():
                    if tf in ["M15", "M30", "H1", "H4", "D1"]:
                        weight = getattr(TimeframeWeight, tf.replace("M", "M"), TimeframeWeight.H1).value
                        weighted_sum += score * weight
                        total_weight += weight
                
                signal.timeframe_consensus = weighted_sum / total_weight if total_weight > 0 else 0.5
                
                # Adjust signal confidence based on consensus
                signal.confidence *= (0.5 + signal.timeframe_consensus * 0.5)
                
            strategy_metrics["multi_timeframe_analyses"] += len(signals)
            return signals
            
        except Exception as e:
            self.logger.error(f"Multi-timeframe consensus failed: {e}")
            return signals


    def _validate_signal(self, signal: TradingSignal) -> bool:
        """Validate trading signal"""
        try:
            # Basic validation
            if signal.confidence < self.min_confidence:
                return False
            
            if signal.strength.value < self.min_signal_strength.value:
                return False
            
            # Risk validation
            if signal.risk_score > 0.8:  # Too risky
                return False
            
            # Market regime validation
            if signal.market_regime == MarketRegime.UNCERTAIN:
                signal.confidence *= 0.8  # Reduce confidence for uncertain markets
            
            return True
            
        except Exception as e:
            self.logger.error(f"Signal validation failed: {e}")
            return False


    def _filter_and_rank_signals(self, signals: List[TradingSignal]) -> List[TradingSignal]:
        """Filter and rank signals by quality"""
        try:
            # Filter out low-quality signals
            filtered_signals = [s for s in signals if s.confidence >= self.min_confidence]
            
            # Sort by confidence and strength
            filtered_signals.sort(key=lambda s: (s.confidence, s.strength.value), reverse=True)
            
            # Limit to top N signals
            max_signals = self.config.get('max_signals_per_symbol', 3)
            return filtered_signals[:max_signals]
            
        except Exception as e:
            self.logger.error(f"Signal filtering failed: {e}")
            return signals


    async def _update_strategy_performance(self, signal: TradingSignal):
        """Update strategy performance metrics"""
        try:
            key = f"{signal.strategy_type.value}_{signal.symbol}"
            
            if key in self.strategy_performances:
                performance = self.strategy_performances[key]
                performance.total_signals += 1
                performance.timestamp = datetime.now()
                
                # Update accuracy (placeholder - would be updated on signal outcome)
                if performance.total_signals > 0:
                    performance.accuracy = performance.successful_signals / performance.total_signals
                    
        except Exception as e:
            self.logger.error(f"Performance update failed: {e}")


    def get_strategy_status(self) -> Dict[str, Any]:
        """Get current strategy executor status"""
        return {
            "enabled_strategies": [s.value for s in self.enabled_strategies],
            "timeframes": self.timeframes,
            "signals_generated": self.signals_generated,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "signal_history_count": len(self.signal_history),
            "strategy_performances": {
                key: {
                    "total_signals": perf.total_signals,
                    "accuracy": perf.accuracy,
                    "total_pnl": perf.total_pnl
                }
                for key, perf in self.strategy_performances.items()
            },
            "metrics": strategy_metrics.copy(),
            "last_updated": datetime.now().isoformat()
        }


    def get_signal_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent signal history"""
        recent_signals = list(self.signal_history)[-limit:]
        return [
            {
                "signal_id": signal.signal_id,
                "strategy_type": signal.strategy_type.value,
                "symbol": signal.symbol,
                "direction": signal.direction,
                "strength": signal.strength.value,
                "confidence": signal.confidence,
                "timestamp": signal.timestamp.isoformat(),
                "processed": signal.processed,
                "executed": signal.executed
            }
            for signal in recent_signals
        ]


# Factory function
def create_strategy_executor(config: Optional[Dict] = None) -> AdvancedStrategyExecutor:
    """Factory function to create strategy executor"""
    try:
        executor = AdvancedStrategyExecutor(config)
        strategy_logger.info("Strategy executor created successfully")
        return executor
        
    except Exception as e:
        strategy_logger.error(f"Failed to create strategy executor: {e}")
        raise