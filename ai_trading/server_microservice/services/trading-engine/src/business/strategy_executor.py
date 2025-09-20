"""
Trading Strategy Executor - Migrated from server_side for Trading-Engine Service
Enterprise-grade trading strategy execution and management for microservices architecture
"""

import asyncio
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

# Local infrastructure integration
from ...shared.infrastructure.core.logger_core import get_logger
from ...shared.infrastructure.core.config_core import get_config
from ...shared.infrastructure.core.error_core import get_error_handler
from ...shared.infrastructure.core.performance_core import get_performance_tracker
from ...shared.infrastructure.core.cache_core import CoreCache

# Initialize local infrastructure components
logger = get_logger("trading-engine", "strategy_executor")
config = get_config("trading-engine")
error_handler = get_error_handler("trading-engine")
performance_tracker = get_performance_tracker("trading-engine")
cache = CoreCache("trading-engine")


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
    BREAKOUT = "breakout"
    CONSOLIDATION = "consolidation"


class EntryTrigger(Enum):
    """Entry trigger types"""
    IMMEDIATE = "immediate"
    PULLBACK = "pullback"
    BREAKOUT = "breakout"
    CONFIRMATION = "confirmation"
    AI_CONSENSUS = "ai_consensus"


@dataclass
class TradingSignal:
    """Comprehensive trading signal for strategy execution"""
    strategy_id: str
    symbol: str
    timestamp: datetime
    
    # Signal details
    direction: str              # BUY, SELL, HOLD
    signal_strength: SignalStrength
    confidence: float           # 0-1 scale
    entry_trigger: EntryTrigger
    
    # Price levels
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward_ratio: float
    
    # Strategy specifics
    strategy_type: StrategyType
    timeframe_primary: str
    timeframes_supporting: List[str]
    
    # Pattern information
    patterns_detected: List[str] = field(default_factory=list)
    pattern_confidence: float = 0.0
    
    # AI insights
    ai_probability: float = 0.0
    ml_prediction: float = 0.0
    sentiment_score: float = 0.0
    
    # Risk metrics
    position_size: float = 0.0
    max_risk: float = 0.0
    expected_return: float = 0.0
    
    # Validation
    backtest_score: float = 0.0
    real_time_score: float = 0.0
    
    # Metadata
    generation_time_ms: float = 0
    data_quality: float = 0


@dataclass
class StrategyPerformance:
    """Strategy performance tracking"""
    strategy_id: str
    strategy_type: StrategyType
    timestamp: datetime
    
    # Performance metrics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    
    # Financial metrics
    total_return: float
    average_return: float
    sharpe_ratio: float
    max_drawdown: float
    profit_factor: float
    
    # Risk metrics
    var_95: float
    volatility: float
    beta: float
    
    # Timing metrics
    average_hold_time: float
    signal_frequency: float
    execution_speed: float
    
    # Market regime performance
    regime_performance: Dict[MarketRegime, float] = field(default_factory=dict)
    
    # Recent performance
    last_30_days: float = 0.0
    last_7_days: float = 0.0
    last_24_hours: float = 0.0


@dataclass
class StrategyConfiguration:
    """Strategy configuration settings"""
    # Strategy settings
    enabled_strategies: List[StrategyType] = field(default_factory=lambda: [
        StrategyType.TREND_FOLLOWING, 
        StrategyType.BREAKOUT, 
        StrategyType.AI_ENSEMBLE
    ])
    
    # Timeframe settings
    primary_timeframes: List[str] = field(default_factory=lambda: ["H1", "H4", "D1"])
    supporting_timeframes: List[str] = field(default_factory=lambda: ["M15", "M30"])
    
    # Signal settings
    min_signal_strength: SignalStrength = SignalStrength.MODERATE
    min_confidence: float = 0.6
    max_signals_per_hour: int = 10
    
    # Risk settings
    max_position_size: float = 0.05      # 5% max position
    max_portfolio_risk: float = 0.15     # 15% portfolio risk
    min_risk_reward: float = 1.5         # 1:1.5 min RR
    
    # Pattern settings
    min_pattern_confidence: float = 0.7
    required_pattern_count: int = 2
    pattern_timeout_minutes: int = 60
    
    # AI settings
    ai_weight: float = 0.4               # 40% weight to AI signals
    ml_threshold: float = 0.6            # ML prediction threshold
    ensemble_agreement: float = 0.7      # Required ensemble agreement


class StrategyExecutor:
    """
    Trading Strategy Executor for Trading-Engine Service
    
    Responsibilities:
    - Strategy lifecycle management
    - Signal generation coordination
    - Strategy performance tracking
    - Risk-adjusted position sizing
    - Inter-service communication coordination
    """
    
    def __init__(self, config: StrategyConfiguration = None):
        self.config = config or StrategyConfiguration()
        self.logger = get_logger("trading-engine", "strategy_executor")
        
        # Strategy tracking
        self.active_strategies: Dict[str, Dict[str, Any]] = {}
        self.strategy_performance: Dict[str, StrategyPerformance] = {}
        self.signal_history: deque = deque(maxlen=1000)
        
        # Performance metrics
        self.metrics = {
            "total_strategies_executed": 0,
            "successful_signals": 0,
            "failed_executions": 0,
            "avg_execution_time": 0.0,
            "total_return": 0.0,
            "active_strategies_count": 0
        }
        
        self.logger.info("🎯 Strategy Executor initialized for Trading-Engine")
    
    async def register_strategy(
        self,
        strategy_id: str,
        strategy_type: StrategyType,
        symbols: List[str],
        timeframes: List[str],
        parameters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Register a new trading strategy"""
        try:
            strategy_config = {
                "strategy_id": strategy_id,
                "strategy_type": strategy_type,
                "symbols": symbols,
                "timeframes": timeframes,
                "parameters": parameters or {},
                "status": "registered",
                "created_at": datetime.now(),
                "last_signal": None,
                "total_signals": 0,
                "active": False
            }
            
            self.active_strategies[strategy_id] = strategy_config
            
            # Initialize performance tracker
            self.strategy_performance[strategy_id] = StrategyPerformance(
                strategy_id=strategy_id,
                strategy_type=strategy_type,
                timestamp=datetime.now(),
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                total_return=0.0,
                average_return=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                profit_factor=1.0,
                var_95=0.0,
                volatility=0.0,
                beta=0.0,
                average_hold_time=0.0,
                signal_frequency=0.0,
                execution_speed=0.0
            )
            
            self.metrics["active_strategies_count"] = len(self.active_strategies)
            
            self.logger.info(f"📝 Strategy registered: {strategy_id} ({strategy_type.value})")
            
            return {
                "success": True,
                "strategy_id": strategy_id,
                "status": "registered",
                "message": f"Strategy {strategy_id} registered successfully"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to register strategy {strategy_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def activate_strategy(self, strategy_id: str) -> Dict[str, Any]:
        """Activate a registered strategy"""
        try:
            if strategy_id not in self.active_strategies:
                return {"success": False, "error": f"Strategy {strategy_id} not found"}
            
            self.active_strategies[strategy_id]["status"] = "active"
            self.active_strategies[strategy_id]["active"] = True
            self.active_strategies[strategy_id]["activated_at"] = datetime.now()
            
            self.logger.info(f"✅ Strategy activated: {strategy_id}")
            
            return {
                "success": True,
                "strategy_id": strategy_id,
                "status": "active",
                "message": f"Strategy {strategy_id} activated successfully"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to activate strategy {strategy_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def deactivate_strategy(self, strategy_id: str) -> Dict[str, Any]:
        """Deactivate an active strategy"""
        try:
            if strategy_id not in self.active_strategies:
                return {"success": False, "error": f"Strategy {strategy_id} not found"}
            
            self.active_strategies[strategy_id]["status"] = "inactive"
            self.active_strategies[strategy_id]["active"] = False
            self.active_strategies[strategy_id]["deactivated_at"] = datetime.now()
            
            self.logger.info(f"⏸️ Strategy deactivated: {strategy_id}")
            
            return {
                "success": True,
                "strategy_id": strategy_id,
                "status": "inactive",
                "message": f"Strategy {strategy_id} deactivated successfully"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to deactivate strategy {strategy_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_trading_signals(
        self,
        strategy_id: str,
        market_data: Dict[str, Any],
        technical_indicators: Dict[str, Any] = None,
        ai_insights: Dict[str, Any] = None
    ) -> List[TradingSignal]:
        """Generate trading signals for a specific strategy"""
        try:
            if strategy_id not in self.active_strategies:
                raise ValueError(f"Strategy {strategy_id} not found")
            
            strategy = self.active_strategies[strategy_id]
            if not strategy["active"]:
                return []
            
            signals = []
            strategy_type = strategy["strategy_type"]
            
            # Generate signals based on strategy type
            if strategy_type == StrategyType.TREND_FOLLOWING:
                signals = await self._generate_trend_following_signals(strategy, market_data, technical_indicators)
            elif strategy_type == StrategyType.BREAKOUT:
                signals = await self._generate_breakout_signals(strategy, market_data, technical_indicators)
            elif strategy_type == StrategyType.AI_ENSEMBLE:
                signals = await self._generate_ai_ensemble_signals(strategy, market_data, ai_insights)
            elif strategy_type == StrategyType.MEAN_REVERSION:
                signals = await self._generate_mean_reversion_signals(strategy, market_data, technical_indicators)
            elif strategy_type == StrategyType.SCALPING:
                signals = await self._generate_scalping_signals(strategy, market_data, technical_indicators)
            
            # Update strategy metrics
            strategy["total_signals"] += len(signals)
            strategy["last_signal"] = datetime.now()
            self.metrics["successful_signals"] += len(signals)
            
            # Store signals in history
            for signal in signals:
                self.signal_history.append({
                    "signal": signal,
                    "timestamp": datetime.now(),
                    "strategy_id": strategy_id
                })
            
            self.logger.info(f"📊 Generated {len(signals)} signals for strategy {strategy_id}")
            
            return signals
            
        except Exception as e:
            self.logger.error(f"❌ Signal generation failed for strategy {strategy_id}: {e}")
            self.metrics["failed_executions"] += 1
            return []
    
    async def _generate_trend_following_signals(
        self,
        strategy: Dict[str, Any],
        market_data: Dict[str, Any],
        technical_indicators: Dict[str, Any]
    ) -> List[TradingSignal]:
        """Generate trend following signals"""
        signals = []
        
        try:
            symbols = strategy["symbols"]
            
            for symbol in symbols:
                symbol_data = market_data.get(symbol, {})
                if not symbol_data:
                    continue
                
                # Simple trend following logic
                current_price = symbol_data.get("close", 0)
                sma_20 = technical_indicators.get(f"{symbol}_SMA_20", current_price)
                sma_50 = technical_indicators.get(f"{symbol}_SMA_50", current_price)
                
                # Trend identification
                if sma_20 > sma_50 and current_price > sma_20:
                    # Uptrend - Generate BUY signal
                    signal = TradingSignal(
                        strategy_id=strategy["strategy_id"],
                        symbol=symbol,
                        timestamp=datetime.now(),
                        direction="BUY",
                        signal_strength=SignalStrength.MODERATE,
                        confidence=0.7,
                        entry_trigger=EntryTrigger.CONFIRMATION,
                        entry_price=current_price,
                        stop_loss=current_price * 0.98,  # 2% stop loss
                        take_profit=current_price * 1.04,  # 4% take profit
                        risk_reward_ratio=2.0,
                        strategy_type=StrategyType.TREND_FOLLOWING,
                        timeframe_primary="H1",
                        timeframes_supporting=["M30", "M15"],
                        position_size=0.02,  # 2% position size
                        max_risk=0.02
                    )
                    signals.append(signal)
                
                elif sma_20 < sma_50 and current_price < sma_20:
                    # Downtrend - Generate SELL signal
                    signal = TradingSignal(
                        strategy_id=strategy["strategy_id"],
                        symbol=symbol,
                        timestamp=datetime.now(),
                        direction="SELL",
                        signal_strength=SignalStrength.MODERATE,
                        confidence=0.7,
                        entry_trigger=EntryTrigger.CONFIRMATION,
                        entry_price=current_price,
                        stop_loss=current_price * 1.02,  # 2% stop loss
                        take_profit=current_price * 0.96,  # 4% take profit
                        risk_reward_ratio=2.0,
                        strategy_type=StrategyType.TREND_FOLLOWING,
                        timeframe_primary="H1",
                        timeframes_supporting=["M30", "M15"],
                        position_size=0.02,  # 2% position size
                        max_risk=0.02
                    )
                    signals.append(signal)
            
        except Exception as e:
            self.logger.error(f"❌ Trend following signal generation failed: {e}")
        
        return signals
    
    async def _generate_breakout_signals(
        self,
        strategy: Dict[str, Any],
        market_data: Dict[str, Any],
        technical_indicators: Dict[str, Any]
    ) -> List[TradingSignal]:
        """Generate breakout signals"""
        signals = []
        
        try:
            symbols = strategy["symbols"]
            
            for symbol in symbols:
                symbol_data = market_data.get(symbol, {})
                if not symbol_data:
                    continue
                
                current_price = symbol_data.get("close", 0)
                high_20 = technical_indicators.get(f"{symbol}_HIGH_20", current_price)
                low_20 = technical_indicators.get(f"{symbol}_LOW_20", current_price)
                
                # Breakout logic
                if current_price > high_20:
                    # Upward breakout
                    signal = TradingSignal(
                        strategy_id=strategy["strategy_id"],
                        symbol=symbol,
                        timestamp=datetime.now(),
                        direction="BUY",
                        signal_strength=SignalStrength.STRONG,
                        confidence=0.8,
                        entry_trigger=EntryTrigger.BREAKOUT,
                        entry_price=current_price,
                        stop_loss=high_20 * 0.995,  # Just below breakout level
                        take_profit=current_price * 1.06,  # 6% take profit
                        risk_reward_ratio=3.0,
                        strategy_type=StrategyType.BREAKOUT,
                        timeframe_primary="H4",
                        timeframes_supporting=["H1", "M30"],
                        position_size=0.03,  # 3% position size
                        max_risk=0.015
                    )
                    signals.append(signal)
                
                elif current_price < low_20:
                    # Downward breakout
                    signal = TradingSignal(
                        strategy_id=strategy["strategy_id"],
                        symbol=symbol,
                        timestamp=datetime.now(),
                        direction="SELL",
                        signal_strength=SignalStrength.STRONG,
                        confidence=0.8,
                        entry_trigger=EntryTrigger.BREAKOUT,
                        entry_price=current_price,
                        stop_loss=low_20 * 1.005,  # Just above breakout level
                        take_profit=current_price * 0.94,  # 6% take profit
                        risk_reward_ratio=3.0,
                        strategy_type=StrategyType.BREAKOUT,
                        timeframe_primary="H4",
                        timeframes_supporting=["H1", "M30"],
                        position_size=0.03,  # 3% position size
                        max_risk=0.015
                    )
                    signals.append(signal)
            
        except Exception as e:
            self.logger.error(f"❌ Breakout signal generation failed: {e}")
        
        return signals
    
    async def _generate_ai_ensemble_signals(
        self,
        strategy: Dict[str, Any],
        market_data: Dict[str, Any],
        ai_insights: Dict[str, Any]
    ) -> List[TradingSignal]:
        """Generate AI ensemble signals"""
        signals = []
        
        try:
            if not ai_insights:
                return signals
            
            symbols = strategy["symbols"]
            
            for symbol in symbols:
                symbol_data = market_data.get(symbol, {})
                ai_data = ai_insights.get(symbol, {})
                
                if not symbol_data or not ai_data:
                    continue
                
                current_price = symbol_data.get("close", 0)
                ai_prediction = ai_data.get("prediction", 0)
                ai_confidence = ai_data.get("confidence", 0)
                sentiment = ai_data.get("sentiment", 0)
                
                # AI ensemble logic
                if ai_confidence > self.config.ml_threshold:
                    if ai_prediction > current_price * 1.01:  # 1% upward prediction
                        signal = TradingSignal(
                            strategy_id=strategy["strategy_id"],
                            symbol=symbol,
                            timestamp=datetime.now(),
                            direction="BUY",
                            signal_strength=SignalStrength.VERY_STRONG,
                            confidence=ai_confidence,
                            entry_trigger=EntryTrigger.AI_CONSENSUS,
                            entry_price=current_price,
                            stop_loss=current_price * 0.975,  # 2.5% stop loss
                            take_profit=ai_prediction * 0.95,  # Near AI prediction
                            risk_reward_ratio=2.5,
                            strategy_type=StrategyType.AI_ENSEMBLE,
                            timeframe_primary="H1",
                            timeframes_supporting=["M30", "M15"],
                            ai_probability=ai_confidence,
                            ml_prediction=ai_prediction,
                            sentiment_score=sentiment,
                            position_size=0.04,  # 4% position size
                            max_risk=0.025
                        )
                        signals.append(signal)
                    
                    elif ai_prediction < current_price * 0.99:  # 1% downward prediction
                        signal = TradingSignal(
                            strategy_id=strategy["strategy_id"],
                            symbol=symbol,
                            timestamp=datetime.now(),
                            direction="SELL",
                            signal_strength=SignalStrength.VERY_STRONG,
                            confidence=ai_confidence,
                            entry_trigger=EntryTrigger.AI_CONSENSUS,
                            entry_price=current_price,
                            stop_loss=current_price * 1.025,  # 2.5% stop loss
                            take_profit=ai_prediction * 1.05,  # Near AI prediction
                            risk_reward_ratio=2.5,
                            strategy_type=StrategyType.AI_ENSEMBLE,
                            timeframe_primary="H1",
                            timeframes_supporting=["M30", "M15"],
                            ai_probability=ai_confidence,
                            ml_prediction=ai_prediction,
                            sentiment_score=sentiment,
                            position_size=0.04,  # 4% position size
                            max_risk=0.025
                        )
                        signals.append(signal)
            
        except Exception as e:
            self.logger.error(f"❌ AI ensemble signal generation failed: {e}")
        
        return signals
    
    async def _generate_mean_reversion_signals(
        self,
        strategy: Dict[str, Any],
        market_data: Dict[str, Any],
        technical_indicators: Dict[str, Any]
    ) -> List[TradingSignal]:
        """Generate mean reversion signals"""
        signals = []
        
        try:
            symbols = strategy["symbols"]
            
            for symbol in symbols:
                symbol_data = market_data.get(symbol, {})
                if not symbol_data:
                    continue
                
                current_price = symbol_data.get("close", 0)
                rsi = technical_indicators.get(f"{symbol}_RSI_14", 50)
                bb_upper = technical_indicators.get(f"{symbol}_BB_UPPER", current_price * 1.02)
                bb_lower = technical_indicators.get(f"{symbol}_BB_LOWER", current_price * 0.98)
                
                # Mean reversion logic
                if rsi < 30 and current_price < bb_lower:
                    # Oversold - BUY signal
                    signal = TradingSignal(
                        strategy_id=strategy["strategy_id"],
                        symbol=symbol,
                        timestamp=datetime.now(),
                        direction="BUY",
                        signal_strength=SignalStrength.STRONG,
                        confidence=0.75,
                        entry_trigger=EntryTrigger.CONFIRMATION,
                        entry_price=current_price,
                        stop_loss=bb_lower * 0.98,
                        take_profit=(bb_upper + bb_lower) / 2,  # Mean reversion target
                        risk_reward_ratio=2.0,
                        strategy_type=StrategyType.MEAN_REVERSION,
                        timeframe_primary="M30",
                        timeframes_supporting=["M15", "M5"],
                        position_size=0.025,
                        max_risk=0.02
                    )
                    signals.append(signal)
                
                elif rsi > 70 and current_price > bb_upper:
                    # Overbought - SELL signal
                    signal = TradingSignal(
                        strategy_id=strategy["strategy_id"],
                        symbol=symbol,
                        timestamp=datetime.now(),
                        direction="SELL",
                        signal_strength=SignalStrength.STRONG,
                        confidence=0.75,
                        entry_trigger=EntryTrigger.CONFIRMATION,
                        entry_price=current_price,
                        stop_loss=bb_upper * 1.02,
                        take_profit=(bb_upper + bb_lower) / 2,  # Mean reversion target
                        risk_reward_ratio=2.0,
                        strategy_type=StrategyType.MEAN_REVERSION,
                        timeframe_primary="M30",
                        timeframes_supporting=["M15", "M5"],
                        position_size=0.025,
                        max_risk=0.02
                    )
                    signals.append(signal)
            
        except Exception as e:
            self.logger.error(f"❌ Mean reversion signal generation failed: {e}")
        
        return signals
    
    async def _generate_scalping_signals(
        self,
        strategy: Dict[str, Any],
        market_data: Dict[str, Any],
        technical_indicators: Dict[str, Any]
    ) -> List[TradingSignal]:
        """Generate scalping signals"""
        signals = []
        
        try:
            symbols = strategy["symbols"]
            
            for symbol in symbols:
                symbol_data = market_data.get(symbol, {})
                if not symbol_data:
                    continue
                
                current_price = symbol_data.get("close", 0)
                ema_5 = technical_indicators.get(f"{symbol}_EMA_5", current_price)
                ema_10 = technical_indicators.get(f"{symbol}_EMA_10", current_price)
                volume = symbol_data.get("volume", 0)
                
                # Scalping logic - fast EMA crosses with volume confirmation
                if ema_5 > ema_10 and current_price > ema_5 and volume > 1000:
                    # Fast upward momentum
                    signal = TradingSignal(
                        strategy_id=strategy["strategy_id"],
                        symbol=symbol,
                        timestamp=datetime.now(),
                        direction="BUY",
                        signal_strength=SignalStrength.MODERATE,
                        confidence=0.65,
                        entry_trigger=EntryTrigger.IMMEDIATE,
                        entry_price=current_price,
                        stop_loss=current_price * 0.995,  # 0.5% stop loss
                        take_profit=current_price * 1.01,  # 1% take profit
                        risk_reward_ratio=2.0,
                        strategy_type=StrategyType.SCALPING,
                        timeframe_primary="M5",
                        timeframes_supporting=["M1"],
                        position_size=0.01,  # Small position for scalping
                        max_risk=0.005
                    )
                    signals.append(signal)
                
                elif ema_5 < ema_10 and current_price < ema_5 and volume > 1000:
                    # Fast downward momentum
                    signal = TradingSignal(
                        strategy_id=strategy["strategy_id"],
                        symbol=symbol,
                        timestamp=datetime.now(),
                        direction="SELL",
                        signal_strength=SignalStrength.MODERATE,
                        confidence=0.65,
                        entry_trigger=EntryTrigger.IMMEDIATE,
                        entry_price=current_price,
                        stop_loss=current_price * 1.005,  # 0.5% stop loss
                        take_profit=current_price * 0.99,  # 1% take profit
                        risk_reward_ratio=2.0,
                        strategy_type=StrategyType.SCALPING,
                        timeframe_primary="M5",
                        timeframes_supporting=["M1"],
                        position_size=0.01,  # Small position for scalping
                        max_risk=0.005
                    )
                    signals.append(signal)
            
        except Exception as e:
            self.logger.error(f"❌ Scalping signal generation failed: {e}")
        
        return signals
    
    async def update_strategy_performance(
        self,
        strategy_id: str,
        trade_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update strategy performance metrics"""
        try:
            if strategy_id not in self.strategy_performance:
                return {"success": False, "error": f"Strategy {strategy_id} not found"}
            
            performance = self.strategy_performance[strategy_id]
            
            # Update trade counts
            performance.total_trades += 1
            
            # Update win/loss
            if trade_result.get("profit", 0) > 0:
                performance.winning_trades += 1
            else:
                performance.losing_trades += 1
            
            # Update financial metrics
            profit = trade_result.get("profit", 0)
            performance.total_return += profit
            performance.average_return = performance.total_return / performance.total_trades
            
            # Update win rate
            performance.win_rate = performance.winning_trades / performance.total_trades
            
            # Update timing metrics
            hold_time = trade_result.get("hold_time_minutes", 0)
            if hold_time > 0:
                performance.average_hold_time = (
                    (performance.average_hold_time * (performance.total_trades - 1) + hold_time) 
                    / performance.total_trades
                )
            
            # Update timestamp
            performance.timestamp = datetime.now()
            
            self.logger.info(f"📊 Updated performance for strategy {strategy_id}: "
                           f"Win Rate: {performance.win_rate:.2%}, "
                           f"Total Return: {performance.total_return:.2f}")
            
            return {
                "success": True,
                "strategy_id": strategy_id,
                "performance": performance
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update performance for strategy {strategy_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_strategy_performance(self, strategy_id: str = None) -> Dict[str, Any]:
        """Get performance metrics for strategies"""
        try:
            if strategy_id:
                if strategy_id not in self.strategy_performance:
                    return {"success": False, "error": f"Strategy {strategy_id} not found"}
                return {
                    "success": True,
                    "strategy_id": strategy_id,
                    "performance": self.strategy_performance[strategy_id]
                }
            else:
                # Return all strategies performance
                return {
                    "success": True,
                    "all_strategies": {
                        sid: perf for sid, perf in self.strategy_performance.items()
                    },
                    "total_strategies": len(self.strategy_performance)
                }
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get strategy performance: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_active_strategies(self) -> Dict[str, Any]:
        """Get list of active strategies"""
        try:
            active_list = [
                {
                    "strategy_id": sid,
                    "strategy_type": strategy["strategy_type"].value,
                    "symbols": strategy["symbols"],
                    "status": strategy["status"],
                    "total_signals": strategy["total_signals"],
                    "last_signal": strategy["last_signal"].isoformat() if strategy["last_signal"] else None
                }
                for sid, strategy in self.active_strategies.items()
                if strategy["active"]
            ]
            
            return {
                "success": True,
                "active_strategies": active_list,
                "total_active": len(active_list),
                "metrics": self.metrics
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get active strategies: {e}")
            return {"success": False, "error": str(e)}
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            # Save performance data to cache before cleanup
            for strategy_id, performance in self.strategy_performance.items():
                cache_key = f"strategy_performance_{strategy_id}"
                await cache.set(cache_key, performance.__dict__, ttl=86400)
            
            self.logger.info("🧹 Strategy Executor cleanup completed")
            
        except Exception as e:
            self.logger.error(f"❌ Cleanup failed: {e}")


# Export main classes for the Trading-Engine service
__all__ = [
    "StrategyExecutor",
    "TradingSignal",
    "StrategyConfiguration",
    "StrategyPerformance",
    "StrategyType",
    "SignalStrength",
    "MarketRegime",
    "EntryTrigger"
]