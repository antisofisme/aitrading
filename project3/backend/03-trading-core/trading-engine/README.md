# Trading Engine Service

## 🎯 Purpose
**Core trading decision engine** yang mengkonversi AI predictions menjadi actionable trading signals dengan intelligent decision synthesis, risk-aware signal generation, dan real-time execution strategy untuk optimal trading performance.

---

## 📊 ChainFlow Diagram

```
ML-Processing → Trading-Engine → Risk-Management → API-Gateway → Client-MT5
      ↓              ↓               ↓              ↓              ↓
  AI Predictions  Trading Signals  Risk Assessment  Auto Execution  Order Placement
  Pattern Recog   Decision Logic   Position Sizing  Signal Routing  Market Orders
  Confidence      Entry/Exit       Portfolio Limits  User Prefs     Real Trading
  Model Ensemble  Timing Strategy  Drawdown Control  Subscription   MT5 Terminal
```

---

## 🏗️ Trading Decision Architecture

### **Input Flow**: AI predictions and market insights from ML-Processing
**Data Source**: ML-Processing → Trading-Engine
**Format**: Protocol Buffers (MLPredictionBatch)
**Frequency**: 50+ AI predictions/second across 10 trading pairs
**Performance Target**: <5ms signal generation (critical path)

### **Output Flow**: Trading signals and execution commands to multiple destinations
**Destinations**: Risk-Management, API-Gateway (auto-execution), Analytics-Service
**Format**: Protocol Buffers (TradingSignalBatch)
**Processing**: Decision synthesis + signal generation + execution strategy
**Performance Target**: <5ms total decision processing

---

## 🚀 Transport Architecture & Contract Integration

### **Transport Decision Matrix Applied**:

#### **Kategori A: High Volume + Mission Critical**
- **Primary Transport**: NATS + Protocol Buffers (<1ms latency)
- **Backup Transport**: Kafka + Protocol Buffers (guaranteed delivery)
- **Failover**: Automatic dengan sequence tracking
- **Services**: ML Predictions → Trading Signals, Signal → Risk Assessment
- **Performance**: <5ms signal generation (critical path)

#### **Kategori B: Medium Volume + Important**
- **Transport**: gRPC (HTTP/2 + Protocol Buffers)
- **Connection**: Pooling + circuit breaker
- **Services**: Strategy management, performance analytics

#### **Kategori C: Low Volume + Standard**
- **Transport**: HTTP REST + JSON via Kong Gateway
- **Backup**: Redis Queue for reliability
- **Services**: Trading configuration, strategy settings

### **Global Decisions Applied**:
✅ **Multi-Transport Architecture**: NATS+Kafka for signals, gRPC for management, HTTP for config
✅ **Protocol Buffers Communication**: 60% smaller signal payloads, 10x faster serialization
✅ **Multi-Tenant Architecture**: Company/user-level trading strategy isolation
✅ **Request Tracing**: Complete correlation ID tracking through decision pipeline
✅ **Central-Hub Coordination**: Strategy registry and performance monitoring
✅ **JWT + Protocol Buffers Auth**: Optimized authentication for trading endpoints
✅ **Circuit Breaker Pattern**: Risk service failover and fallback strategies

### **Schema Dependencies**:
```python
# Import from centralized schemas
import sys
sys.path.append('../../../01-core-infrastructure/central-hub/static/generated/python')

from ml.ml_predictions_pb2 import MLPredictionBatch, Prediction, PatternPrediction
from trading.trading_signals_pb2 import TradingSignalBatch, TradingSignal, ExecutionCommand
from trading.strategy_config_pb2 import StrategyConfig, RiskParameters, UserPreferences
from common.user_context_pb2 import UserContext, SubscriptionTier
from common.request_trace_pb2 import RequestTrace, TraceContext
from risk.risk_assessment_pb2 import RiskAssessment, PositionSizing
```

### **Enhanced Trading MessageEnvelope**:
```protobuf
message TradingProcessingEnvelope {
  string message_type = 1;           // "trading_decision"
  string user_id = 2;                // Multi-tenant user identification
  string company_id = 3;             // Multi-tenant company identification
  bytes payload = 4;                 // TradingSignalBatch protobuf
  int64 timestamp = 5;               // Decision timestamp
  string service_source = 6;         // "trading-engine"
  string correlation_id = 7;         // Request tracing
  TraceContext trace_context = 8;    // Distributed tracing
  StrategyInfo strategy_info = 9;    // Active strategy metadata
  AuthToken auth_token = 10;         // JWT + Protocol Buffers auth
}
```

---

## 📋 Standard Implementation Patterns

### **BaseService Integration:**
```python
# Trading Engine menggunakan Central Hub standardization
from central_hub.static.utils import BaseService, ServiceConfig
from central_hub.static.utils.patterns import (
    StandardResponse, StandardDatabaseManager, StandardCacheManager,
    RequestTracer, StandardCircuitBreaker, PerformanceTracker, ErrorDNA
)

class TradingEngineService(BaseService):
    def __init__(self):
        config = ServiceConfig(
            service_name="trading-engine",
            version="5.0.0",
            port=8002,
            environment="production"
        )
        super().__init__(config)

        # Service-specific components
        self.strategy_registry = {}
        self.signal_processor = None

    async def custom_health_checks(self):
        """Trading Engine-specific health checks"""
        return {
            "signals_generated_24h": await self.get_daily_signal_count(),
            "avg_signal_generation_ms": await self.get_avg_signal_time(),
            "strategy_success_rates": await self.get_strategy_success_rates(),
            "active_trading_pairs": await self.get_active_pairs_count()
        }
```

### **Standard Error Handling dengan ErrorDNA:**
```python
async def process_ml_prediction(self, prediction: MLPredictionBatch, correlation_id: str):
    """Process ML prediction dengan standardized error handling"""
    try:
        return await self.process_with_tracing(
            "signal_generation",
            self._generate_trading_signal,
            correlation_id,
            prediction
        )
    except Exception as e:
        # ErrorDNA automatic analysis
        error_analysis = self.error_analyzer.analyze_error(
            error_message=str(e),
            stack_trace=traceback.format_exc(),
            correlation_id=correlation_id,
            context={"operation": "signal_generation", "symbol": prediction.symbol}
        )

        self.logger.error(f"Signal generation failed: {error_analysis.suggested_actions}")
        return StandardResponse.error_response(str(e), correlation_id=correlation_id)
```

### **Standard Cache & Database Patterns:**
```python
# Strategy configuration caching
strategy_config = await self.cache.get_or_set(
    f"strategy:{strategy_id}:{user_id}",
    lambda: self.db.fetch_one(
        "SELECT * FROM trading_strategies WHERE strategy_id = $1 AND user_id = $2",
        {"strategy_id": strategy_id, "user_id": user_id}
    ),
    ttl=600  # 10 minutes
)

# Market conditions caching
market_conditions = await self.cache.get_or_set(
    f"market:{symbol}",
    lambda: self.analyze_market_conditions(symbol),
    ttl=60  # 1 minute
)
```

### **Circuit Breaker untuk External Services:**
```python
# Risk Management service dengan circuit breaker protection
if not await self.check_circuit_breaker("risk_management"):
    try:
        risk_assessment = await self.risk_client.assess_signal(signal)
        await self.record_external_success("risk_management")
        return risk_assessment
    except Exception as e:
        await self.record_external_failure("risk_management")
        # Fallback to conservative risk assessment
        return await self.apply_conservative_risk_limits(signal)
else:
    return await self.apply_conservative_risk_limits(signal)
```

---

## 🧠 Trading Decision Engine

### **1. Decision Synthesis Manager**:
```python
class TradingDecisionEngine:
    def __init__(self, central_hub_client):
        self.central_hub = central_hub_client
        self.circuit_breaker = CircuitBreaker("risk-management")
        self.strategy_registry = StrategyRegistry()
        self.decision_cache = DecisionCache()

    async def process_ml_predictions(self, prediction_batch: MLPredictionBatch,
                                   user_context: UserContext,
                                   trace_context: TraceContext) -> TradingSignalBatch:
        """Convert AI predictions to trading signals with intelligent synthesis"""

        # Request tracing
        with self.tracer.trace("trading_decision_synthesis", trace_context.correlation_id):
            start_time = time.time()

            signal_batch = TradingSignalBatch()
            signal_batch.user_id = prediction_batch.user_id
            signal_batch.company_id = prediction_batch.company_id
            signal_batch.correlation_id = trace_context.correlation_id

            # Load user trading strategy
            strategy_config = await self.get_user_strategy(user_context)

            # Multi-tenant strategy isolation
            company_strategy = await self.get_company_strategy(user_context.company_id)
            merged_strategy = self.merge_strategies(strategy_config, company_strategy)

            for prediction in prediction_batch.predictions:
                # Decision synthesis
                trading_signal = await self.synthesize_trading_decision(
                    prediction, merged_strategy, user_context, trace_context
                )

                if trading_signal:
                    signal_batch.trading_signals.append(trading_signal)

            # Performance metrics
            decision_time = (time.time() - start_time) * 1000
            signal_batch.performance_metrics.decision_time_ms = decision_time
            signal_batch.performance_metrics.signal_count = len(signal_batch.trading_signals)

            return signal_batch

    async def synthesize_trading_decision(self, prediction: Prediction,
                                        strategy: StrategyConfig,
                                        user_context: UserContext,
                                        trace_context: TraceContext) -> Optional[TradingSignal]:
        """Core decision synthesis logic"""

        # Check prediction confidence threshold
        if prediction.confidence < strategy.min_confidence_threshold:
            return None

        # Multi-model consensus check
        consensus_score = await self.calculate_model_consensus(prediction)
        if consensus_score < strategy.min_consensus_score:
            return None

        # Market condition validation
        market_condition = await self.assess_market_condition(prediction.symbol)
        if not self.is_favorable_market(market_condition, strategy):
            return None

        # Generate trading signal
        trading_signal = TradingSignal()
        trading_signal.symbol = prediction.symbol
        trading_signal.correlation_id = trace_context.correlation_id
        trading_signal.user_id = user_context.user_id
        trading_signal.company_id = user_context.company_id

        # Signal direction and strength
        trading_signal.signal_type = await self.determine_signal_type(
            prediction, strategy, market_condition
        )
        trading_signal.signal_strength = await self.calculate_signal_strength(
            prediction, consensus_score, market_condition
        )

        # Entry strategy
        trading_signal.entry_strategy = await self.determine_entry_strategy(
            prediction, strategy, user_context
        )

        # Risk management parameters
        trading_signal.risk_params = await self.calculate_risk_parameters(
            prediction, strategy, user_context
        )

        # Execution preferences
        trading_signal.execution_prefs = await self.get_execution_preferences(
            user_context, strategy
        )

        return trading_signal
```

### **2. Signal Generation Engine**:
```python
class SignalGenerationEngine:
    async def determine_signal_type(self, prediction: Prediction,
                                  strategy: StrategyConfig,
                                  market_condition: MarketCondition) -> SignalType:
        """Determine BUY/SELL/HOLD signal with intelligent logic"""

        # Base signal from AI prediction
        base_signal = prediction.primary_direction

        # Pattern-based signal enhancement
        if hasattr(prediction, 'pattern_prediction'):
            pattern_signal = self.extract_pattern_signal(prediction.pattern_prediction)
            base_signal = self.combine_signals(base_signal, pattern_signal)

        # Market condition adjustment
        if market_condition.regime == MarketRegime.HIGH_VOLATILITY:
            if strategy.volatility_mode == VolatilityMode.CONSERVATIVE:
                # Reduce signal strength in high volatility
                if base_signal == SignalType.BUY:
                    return SignalType.WEAK_BUY
                elif base_signal == SignalType.SELL:
                    return SignalType.WEAK_SELL
            elif strategy.volatility_mode == VolatilityMode.AGGRESSIVE:
                # Enhance signal strength in high volatility
                if base_signal == SignalType.WEAK_BUY:
                    return SignalType.BUY
                elif base_signal == SignalType.WEAK_SELL:
                    return SignalType.SELL

        # Trend alignment check
        if strategy.trend_following_enabled:
            market_trend = market_condition.primary_trend
            if not self.is_signal_aligned_with_trend(base_signal, market_trend):
                # Counter-trend signals require higher confidence
                if prediction.confidence < strategy.counter_trend_confidence_threshold:
                    return SignalType.HOLD

        return base_signal

    async def calculate_signal_strength(self, prediction: Prediction,
                                      consensus_score: float,
                                      market_condition: MarketCondition) -> float:
        """Calculate signal strength (0.0 - 1.0)"""

        strength_factors = []

        # Model confidence
        strength_factors.append(prediction.confidence)

        # Model consensus
        strength_factors.append(consensus_score)

        # Pattern strength (if available)
        if hasattr(prediction, 'pattern_prediction'):
            pattern_strength = max([p.probability for p in prediction.pattern_prediction.detected_patterns])
            strength_factors.append(pattern_strength)

        # Market condition favorability
        market_favorability = self.assess_market_favorability(market_condition)
        strength_factors.append(market_favorability)

        # Volume confirmation (if available)
        if hasattr(prediction, 'volume_confirmation'):
            strength_factors.append(prediction.volume_confirmation)

        # Calculate weighted average
        weights = [0.3, 0.25, 0.2, 0.15, 0.1]  # Adjust based on importance
        signal_strength = sum(f * w for f, w in zip(strength_factors[:len(weights)], weights))

        return min(max(signal_strength, 0.0), 1.0)
```

### **3. Entry Strategy Engine**:
```python
class EntryStrategyEngine:
    async def determine_entry_strategy(self, prediction: Prediction,
                                     strategy: StrategyConfig,
                                     user_context: UserContext) -> EntryStrategy:
        """Determine optimal entry strategy and timing"""

        entry_strategy = EntryStrategy()

        # Subscription-based strategy access
        available_strategies = await self.get_available_entry_strategies(
            user_context.subscription_tier
        )

        # Market order vs limit order decision
        if strategy.prefer_market_orders:
            entry_strategy.order_type = OrderType.MARKET
            entry_strategy.execution_urgency = ExecutionUrgency.IMMEDIATE
        else:
            entry_strategy.order_type = OrderType.LIMIT
            entry_strategy.execution_urgency = ExecutionUrgency.PATIENT

            # Calculate optimal limit price
            entry_strategy.limit_price = await self.calculate_optimal_limit_price(
                prediction, strategy
            )

        # Position sizing strategy
        entry_strategy.position_sizing = await self.determine_position_sizing_strategy(
            prediction, strategy, user_context
        )

        # Entry timing optimization
        if "advanced_timing" in available_strategies:
            entry_strategy.timing_strategy = await self.optimize_entry_timing(
                prediction, strategy
            )

        # Stop loss and take profit
        entry_strategy.stop_loss = await self.calculate_stop_loss(
            prediction, strategy
        )
        entry_strategy.take_profit = await self.calculate_take_profit(
            prediction, strategy
        )

        # Multi-leg strategy (Pro+ only)
        if (user_context.subscription_tier >= SubscriptionTier.PRO and
            strategy.enable_multi_leg_strategies):
            entry_strategy.legs = await self.create_multi_leg_strategy(
                prediction, strategy
            )

        return entry_strategy

    async def calculate_optimal_limit_price(self, prediction: Prediction,
                                          strategy: StrategyConfig) -> float:
        """Calculate optimal limit order price"""

        current_price = prediction.current_price
        predicted_price = prediction.predicted_price

        if prediction.signal_type == SignalType.BUY:
            # For buy signals, set limit below current price
            limit_discount = strategy.limit_order_discount_pips / 10000
            optimal_price = current_price - limit_discount
        else:
            # For sell signals, set limit above current price
            limit_premium = strategy.limit_order_premium_pips / 10000
            optimal_price = current_price + limit_premium

        # Ensure price is within reasonable bounds
        max_deviation = strategy.max_limit_deviation_pips / 10000
        if abs(optimal_price - current_price) > max_deviation:
            if prediction.signal_type == SignalType.BUY:
                optimal_price = current_price - max_deviation
            else:
                optimal_price = current_price + max_deviation

        return optimal_price
```

### **4. Risk-Aware Signal Processing**:
```python
class RiskAwareSignalProcessor:
    def __init__(self):
        self.circuit_breaker = CircuitBreaker("risk-management")

    async def process_with_risk_assessment(self, trading_signal: TradingSignal,
                                         user_context: UserContext,
                                         trace_context: TraceContext) -> TradingSignal:
        """Process signal with risk management integration"""

        # Circuit breaker check for risk service
        if self.circuit_breaker.is_open("risk-management"):
            # Use cached risk parameters
            risk_params = await self.get_cached_risk_params(user_context)
            trading_signal.risk_status = RiskStatus.FALLBACK_USED
        else:
            try:
                # Real-time risk assessment
                risk_assessment = await self.risk_service.assess_signal_risk(
                    trading_signal, user_context, trace_context
                )

                # Apply risk adjustments
                trading_signal = await self.apply_risk_adjustments(
                    trading_signal, risk_assessment
                )

                trading_signal.risk_status = RiskStatus.ASSESSED

            except Exception as e:
                # Trip circuit breaker
                self.circuit_breaker.trip("risk-management")

                # Fallback to conservative risk parameters
                risk_params = await self.get_conservative_risk_params(user_context)
                trading_signal = await self.apply_conservative_risk(
                    trading_signal, risk_params
                )

                trading_signal.risk_status = RiskStatus.ERROR_FALLBACK

                # Add error to trace
                self.tracer.add_error(trace_context.correlation_id,
                                    f"Risk assessment failed: {str(e)}")

        return trading_signal

    async def apply_risk_adjustments(self, signal: TradingSignal,
                                   risk_assessment: RiskAssessment) -> TradingSignal:
        """Apply risk management adjustments to trading signal"""

        # Position size adjustment
        if risk_assessment.recommended_position_size < signal.position_size:
            signal.position_size = risk_assessment.recommended_position_size
            signal.risk_adjustments.append("Position size reduced by risk management")

        # Stop loss tightening
        if risk_assessment.recommended_stop_loss_tighter:
            original_sl = signal.entry_strategy.stop_loss
            tighter_sl = risk_assessment.recommended_stop_loss
            signal.entry_strategy.stop_loss = tighter_sl
            signal.risk_adjustments.append(f"Stop loss tightened from {original_sl} to {tighter_sl}")

        # Signal cancellation for high risk
        if risk_assessment.risk_level >= RiskLevel.EXTREME:
            signal.signal_type = SignalType.HOLD
            signal.cancellation_reason = "Extreme risk level detected"

        return signal
```

---

## 📊 Multi-Tenant Strategy Management

### **User Strategy Configuration**:
```python
class UserStrategyManager:
    async def get_user_strategy(self, user_context: UserContext) -> StrategyConfig:
        """Get user-specific trading strategy configuration"""

        # Base strategy from subscription tier
        base_strategy = await self.get_tier_strategy(user_context.subscription_tier)

        # User customizations
        user_customizations = await self.get_user_customizations(user_context.user_id)
        if user_customizations:
            base_strategy = self.apply_user_customizations(base_strategy, user_customizations)

        # Company-level strategy overrides
        company_overrides = await self.get_company_overrides(user_context.company_id)
        if company_overrides:
            base_strategy = self.apply_company_overrides(base_strategy, company_overrides)

        return base_strategy

    def get_tier_strategy(self, tier: SubscriptionTier) -> StrategyConfig:
        """Get default strategy based on subscription tier"""

        tier_strategies = {
            SubscriptionTier.FREE: StrategyConfig(
                min_confidence_threshold=0.8,      # Higher threshold for free users
                min_consensus_score=0.7,
                max_position_count=3,              # Limited positions
                available_instruments=["EURUSD", "GBPUSD"],  # Limited pairs
                advanced_features_enabled=False
            ),
            SubscriptionTier.PRO: StrategyConfig(
                min_confidence_threshold=0.7,
                min_consensus_score=0.6,
                max_position_count=10,
                available_instruments=self.get_major_pairs(),
                advanced_features_enabled=True,
                pattern_trading_enabled=True
            ),
            SubscriptionTier.ENTERPRISE: StrategyConfig(
                min_confidence_threshold=0.6,
                min_consensus_score=0.5,
                max_position_count=50,
                available_instruments=self.get_all_instruments(),
                advanced_features_enabled=True,
                pattern_trading_enabled=True,
                custom_strategies_enabled=True,
                algorithmic_execution_enabled=True
            )
        }

        return tier_strategies.get(tier, tier_strategies[SubscriptionTier.FREE])
```

### **Strategy Performance Tracking**:
```python
class StrategyPerformanceTracker:
    async def track_signal_performance(self, trading_signal: TradingSignal,
                                     execution_result: ExecutionResult,
                                     trace_context: TraceContext):
        """Track trading signal performance for strategy optimization"""

        # Calculate signal outcome
        if execution_result.status == ExecutionStatus.FILLED:
            # Track from signal generation to execution
            signal_performance = SignalPerformance()
            signal_performance.signal_id = trading_signal.signal_id
            signal_performance.user_id = trading_signal.user_id
            signal_performance.correlation_id = trace_context.correlation_id

            # Performance metrics
            signal_performance.execution_latency_ms = (
                execution_result.execution_time - trading_signal.generation_time
            )
            signal_performance.price_slippage = abs(
                execution_result.executed_price - trading_signal.target_price
            )

            # Store for analysis
            await self.store_signal_performance(signal_performance)

            # Real-time strategy adjustment
            await self.update_strategy_parameters(trading_signal.user_id, signal_performance)

    async def update_strategy_parameters(self, user_id: str,
                                       performance: SignalPerformance):
        """Dynamic strategy parameter adjustment based on performance"""

        user_stats = await self.get_user_performance_stats(user_id)

        # Adjust confidence threshold based on accuracy
        if user_stats.accuracy < 0.6:
            # Increase confidence threshold for low-performing users
            await self.increase_confidence_threshold(user_id, 0.05)
        elif user_stats.accuracy > 0.8:
            # Decrease confidence threshold for high-performing users
            await self.decrease_confidence_threshold(user_id, 0.02)

        # Adjust position sizing based on drawdown
        if user_stats.max_drawdown > 0.1:  # 10% drawdown
            await self.reduce_position_sizing(user_id, 0.8)  # 20% reduction
```

---

## ⚡ Performance Optimizations

### **Signal Caching and Deduplication**:
```python
class SignalCache:
    def __init__(self):
        self.signal_cache = TTLCache(maxsize=1000, ttl=60)  # 1 minute TTL
        self.duplicate_detector = DuplicateSignalDetector()

    async def get_cached_signal(self, prediction_hash: str) -> Optional[TradingSignal]:
        """Check for cached trading signals to avoid duplicate processing"""

        return self.signal_cache.get(prediction_hash)

    async def cache_signal(self, prediction_hash: str, signal: TradingSignal):
        """Cache trading signal with intelligent TTL"""

        # Dynamic TTL based on signal strength
        ttl = max(30, int(signal.signal_strength * 120))  # 30-120 seconds
        self.signal_cache[prediction_hash] = signal

    async def detect_duplicate_signal(self, new_signal: TradingSignal,
                                    user_context: UserContext) -> bool:
        """Detect duplicate signals to prevent over-trading"""

        # Check recent signals for same symbol
        recent_signals = await self.get_recent_signals(
            user_context.user_id, new_signal.symbol, minutes=5
        )

        for existing_signal in recent_signals:
            if self.signals_are_similar(new_signal, existing_signal):
                return True

        return False

    def signals_are_similar(self, signal1: TradingSignal,
                           signal2: TradingSignal) -> bool:
        """Check if two signals are substantially similar"""

        # Same direction
        if signal1.signal_type != signal2.signal_type:
            return False

        # Similar entry price (within 5 pips)
        price_diff = abs(signal1.entry_strategy.target_price -
                        signal2.entry_strategy.target_price)
        if price_diff > 0.0005:  # 5 pips for major pairs
            return False

        return True
```

### **Parallel Signal Processing**:
```python
async def process_multiple_predictions(self, prediction_batches: List[MLPredictionBatch],
                                     trace_context: TraceContext) -> List[TradingSignalBatch]:
    """Parallel processing of multiple prediction batches"""

    # Create processing tasks
    tasks = []
    for batch in prediction_batches:
        task = asyncio.create_task(
            self.process_ml_predictions(batch, trace_context)
        )
        tasks.append(task)

    # Execute in parallel
    signal_batches = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle exceptions and compile results
    successful_batches = []
    for i, result in enumerate(signal_batches):
        if isinstance(result, Exception):
            self.logger.error(f"Signal processing failed for batch {i}: {result}")
            # Add error to trace
            self.tracer.add_error(trace_context.correlation_id, str(result))
        else:
            successful_batches.append(result)

    return successful_batches
```

---

## 🔍 Health Monitoring & Performance

### **Service Health Check**:
```python
@app.get("/health")
async def health_check():
    """Comprehensive trading engine health check"""

    health_status = {
        "service": "trading-engine",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "3.2.0"
    }

    try:
        # Decision engine performance
        health_status["avg_decision_time_ms"] = await self.get_avg_decision_time()
        health_status["signal_generation_rate"] = await self.get_signal_generation_rate()

        # Strategy performance
        health_status["active_strategies"] = await self.get_active_strategy_count()
        health_status["avg_strategy_accuracy"] = await self.get_avg_strategy_accuracy()

        # Risk management integration
        health_status["risk_service_status"] = await self.check_risk_service_health()
        health_status["circuit_breaker_status"] = await self.get_circuit_breaker_summary()

        # Multi-tenant metrics
        health_status["active_users"] = await self.get_active_user_count()
        health_status["signals_generated_today"] = await self.get_daily_signal_count()

        # Protocol Buffers performance
        health_status["protobuf_serialization_ms"] = await self.get_protobuf_performance()

    except Exception as e:
        health_status["status"] = "degraded"
        health_status["error"] = str(e)

    return health_status
```

---

## 🎯 Business Value

### **Trading Performance Excellence**:
- **Sub-5ms Signal Generation**: Critical path contribution to <30ms total latency
- **Intelligent Decision Synthesis**: Multi-model consensus + pattern recognition
- **Risk-Aware Strategies**: Integrated risk management for capital protection
- **Subscription-Based Features**: Tiered strategy access untuk revenue optimization

### **Technical Innovation**:
- **Circuit Breaker Protected**: Risk service failover dengan fallback strategies
- **Multi-Tenant Strategy Isolation**: Company/user-level trading strategy management
- **Dynamic Strategy Adjustment**: Real-time parameter optimization based on performance
- **Advanced Entry Strategies**: Market/limit orders dengan optimal timing

### **Operational Excellence**:
- **Protocol Buffers**: 60% smaller signal payloads, 10x faster processing
- **Request Tracing**: Complete correlation ID tracking through decision pipeline
- **Signal Deduplication**: Intelligent caching untuk prevent over-trading
- **Performance Monitoring**: Real-time strategy accuracy tracking

---

## 🔗 Service Contract Specifications

### **Trading Engine Proto Contracts**:
- **Input Contract**: ML Predictions via NATS/Kafka from `/trading/ml_predictions.proto`
- **Output Contract**: Trading Signals via NATS/Kafka to `/trading/trading_signals.proto`
- **Strategy Management**: gRPC service for strategy configuration dan performance tracking

### **Critical Path Integration**:
- **ML-Processing → Trading-Engine**: NATS primary, Kafka backup
- **Trading-Engine → Risk-Management**: NATS primary, Kafka backup
- **Trading-Engine → API-Gateway**: gRPC for approved signals

---

**Input Flow**: ML-Processing (AI predictions) → Trading-Engine (decision synthesis)
**Output Flow**: Trading-Engine → Risk-Management → API-Gateway → Client-MT5
**Key Innovation**: Sub-5ms intelligent trading decision synthesis dengan multi-transport architecture, multi-tenant strategy management dan risk-aware signal generation untuk optimal trading performance.