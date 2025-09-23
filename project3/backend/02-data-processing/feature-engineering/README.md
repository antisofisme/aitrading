# Feature Engineering Service

## 🎯 Purpose
**Advanced technical analysis and feature extraction engine** yang mengkonversi validated tick data menjadi ML-ready feature vectors dengan sophisticated indicators, cross-asset correlation, dan market regime detection untuk optimal AI trading performance.

---

## 📊 ChainFlow Diagram

```
Data-Bridge → Feature Engineering → ML-Processing → Trading-Engine
    ↓              ↓                    ↓              ↓
Validated Data  Advanced Features    AI Predictions  Trading Signals
Quality Score   Pattern Analysis     Model Inference  Decision Logic
User Context    Cross-pair Corr      15ms Inference   Signal Generation
Real-time       Market Regime        Confidence      Risk Assessment
```

---

## 🏗️ Service Architecture

### **Input Flow**: Validated, enriched tick data from Data-Bridge
**Data Source**: Data-Bridge → Feature-Engineering
**Format**: Protocol Buffers (EnrichedBatchData)
**Frequency**: 50+ ticks/second across 10 trading pairs
**Performance Target**: <8ms advanced feature calculation

### **Output Flow**: ML-ready feature vectors to ML-Processing
**Destination**: ML-Processing Service
**Format**: Protocol Buffers (FeatureVectorBatch)
**Processing**: Technical indicators + market context + correlation analysis
**Performance Target**: <8ms feature engineering per batch

---

## 🔧 Protocol Buffers Integration

### **Global Decisions Applied**:
✅ **Protocol Buffers Communication**: 60% smaller payloads, 10x faster serialization
✅ **Multi-Tenant Architecture**: Company/user-level feature filtering
✅ **Request Tracing**: Correlation ID tracking through feature pipeline
✅ **Central-Hub Coordination**: Service discovery and health monitoring
✅ **JWT + Protocol Buffers Auth**: Optimized authentication tokens
✅ **Circuit Breaker Pattern**: Protection for external market data calls

### **Schema Dependencies**:
```python
# Import from centralized schemas
import sys
sys.path.append('../../../01-core-infrastructure/central-hub/static/generated/python')

from trading.enriched_data_pb2 import EnrichedBatchData, EnrichedTickData
from ml.feature_vectors_pb2 import FeatureVectorBatch, FeatureVector, TechnicalIndicators
from common.user_context_pb2 import UserContext, SubscriptionTier
from common.api_response_pb2 import APIResponse, ErrorInfo
from common.request_trace_pb2 import RequestTrace, TraceContext
```

### **Enhanced MessageEnvelope with Tracing**:
```protobuf
message FeatureProcessingEnvelope {
  string message_type = 1;           // "feature_processing"
  string user_id = 2;                // Multi-tenant user identification
  string company_id = 3;             // Multi-tenant company identification
  bytes payload = 4;                 // FeatureVectorBatch protobuf
  int64 timestamp = 5;               // Processing timestamp
  string service_source = 6;         // "feature-engineering"
  string correlation_id = 7;         // Request tracing
  TraceContext trace_context = 8;    // Distributed tracing
  AuthToken auth_token = 9;          // JWT + Protocol Buffers auth
}
```

---

## 🔄 Advanced Feature Engineering Pipeline

### **1. Technical Indicators Engine**:
```python
class TechnicalIndicatorsEngine:
    def __init__(self, central_hub_client):
        self.central_hub = central_hub_client
        self.circuit_breaker = CircuitBreaker("market-data-api")

    async def process_enriched_batch(self, enriched_data: EnrichedBatchData,
                                   trace_context: TraceContext) -> FeatureVectorBatch:
        """Advanced technical analysis with circuit breaker protection"""

        # Request tracing
        with self.tracer.trace("feature_engineering", trace_context.correlation_id):
            start_time = time.time()

            # Multi-tenant filtering
            user_features = await self.filter_by_subscription(
                enriched_data.user_context.subscription_tier
            )

            feature_batch = FeatureVectorBatch()
            feature_batch.user_id = enriched_data.user_context.user_id
            feature_batch.company_id = enriched_data.user_context.company_id
            feature_batch.correlation_id = trace_context.correlation_id

            for enriched_tick in enriched_data.enriched_ticks:
                # Advanced feature extraction
                feature_vector = await self.extract_features(
                    enriched_tick, user_features, trace_context
                )
                feature_batch.feature_vectors.append(feature_vector)

            # Performance tracking
            processing_time = (time.time() - start_time) * 1000
            feature_batch.processing_metrics.latency_ms = processing_time

            return feature_batch
```

### **2. Cross-Asset Correlation Analysis**:
```python
async def calculate_cross_asset_correlation(self, symbols: List[str],
                                          trace_context: TraceContext) -> CorrelationMatrix:
    """Real-time cross-pair correlation with circuit breaker protection"""

    correlation_matrix = CorrelationMatrix()

    # Circuit breaker for external market data
    if self.circuit_breaker.is_open("market-data-api"):
        # Use cached correlation data
        correlation_matrix = await self.get_cached_correlation(symbols)
        correlation_matrix.source = "cache_fallback"
    else:
        try:
            # Real-time correlation calculation
            market_data = await self.fetch_market_data(symbols, trace_context)
            correlation_matrix = self.compute_correlation(market_data)
            correlation_matrix.source = "real_time"

            # Cache for fallback
            await self.cache_correlation(correlation_matrix)

        except Exception as e:
            # Circuit breaker trip
            self.circuit_breaker.trip()

            # Fallback to cached data
            correlation_matrix = await self.get_cached_correlation(symbols)
            correlation_matrix.source = "error_fallback"

            # Request tracing error
            self.tracer.add_error(trace_context.correlation_id, str(e))

    return correlation_matrix
```

### **3. Market Regime Detection**:
```python
async def detect_market_regime(self, historical_data: List[TickData],
                             user_context: UserContext) -> MarketRegime:
    """ML-based market regime classification with multi-tenant filtering"""

    regime = MarketRegime()

    # Multi-tenant feature access
    if user_context.subscription_tier >= SubscriptionTier.PRO:
        # Advanced regime detection for Pro+ users
        regime.regime_type = await self.advanced_regime_detection(historical_data)
        regime.confidence = await self.calculate_regime_confidence(historical_data)
        regime.regime_indicators = await self.extract_regime_indicators(historical_data)
    else:
        # Basic regime detection for free users
        regime.regime_type = await self.basic_regime_detection(historical_data)
        regime.confidence = 0.8  # Fixed confidence for free tier
        regime.regime_indicators = []  # Limited indicators

    regime.user_tier = user_context.subscription_tier
    regime.analysis_timestamp = int(time.time() * 1000)

    return regime
```

### **4. Feature Vector Assembly**:
```python
async def assemble_feature_vector(self, enriched_tick: EnrichedTickData,
                                user_features: UserFeatureConfig,
                                trace_context: TraceContext) -> FeatureVector:
    """Comprehensive feature vector assembly with performance optimization"""

    feature_vector = FeatureVector()
    feature_vector.symbol = enriched_tick.original_tick.symbol
    feature_vector.timestamp = enriched_tick.original_tick.timestamp
    feature_vector.correlation_id = trace_context.correlation_id

    # Core price features (always included)
    feature_vector.price_features.bid = enriched_tick.original_tick.bid
    feature_vector.price_features.ask = enriched_tick.original_tick.ask
    feature_vector.price_features.spread = enriched_tick.original_tick.ask - enriched_tick.original_tick.bid
    feature_vector.price_features.mid_price = enriched_tick.normalized_price

    # Technical indicators (subscription-based)
    if "technical_indicators" in user_features.enabled_features:
        feature_vector.technical_indicators = await self.calculate_technical_indicators(
            enriched_tick, user_features.technical_config
        )

    # Market microstructure (Pro+ only)
    if user_features.subscription_tier >= SubscriptionTier.PRO:
        feature_vector.microstructure = await self.analyze_microstructure(enriched_tick)

    # Cross-asset features (Enterprise only)
    if user_features.subscription_tier >= SubscriptionTier.ENTERPRISE:
        feature_vector.cross_asset = await self.calculate_cross_asset_features(
            enriched_tick, trace_context
        )

    # Quality and metadata
    feature_vector.quality_score = enriched_tick.tick_quality_score
    feature_vector.feature_count = len(feature_vector.ListFields())

    return feature_vector
```

---

## 📊 Advanced Technical Indicators

### **Core Indicators Suite**:
```python
class AdvancedIndicators:
    async def calculate_all_indicators(self, price_series: List[float],
                                     volume_series: List[float]) -> TechnicalIndicators:
        """Comprehensive technical analysis suite"""

        indicators = TechnicalIndicators()

        # Trend Indicators
        indicators.trend.sma_20 = self.simple_moving_average(price_series, 20)
        indicators.trend.ema_12 = self.exponential_moving_average(price_series, 12)
        indicators.trend.ema_26 = self.exponential_moving_average(price_series, 26)
        indicators.trend.macd = indicators.trend.ema_12 - indicators.trend.ema_26
        indicators.trend.macd_signal = self.exponential_moving_average([indicators.trend.macd], 9)

        # Momentum Indicators
        indicators.momentum.rsi_14 = self.relative_strength_index(price_series, 14)
        indicators.momentum.stochastic_k = self.stochastic_k(price_series, 14)
        indicators.momentum.stochastic_d = self.stochastic_d(indicators.momentum.stochastic_k, 3)
        indicators.momentum.williams_r = self.williams_r(price_series, 14)

        # Volatility Indicators
        indicators.volatility.bollinger_upper, indicators.volatility.bollinger_lower = \
            self.bollinger_bands(price_series, 20, 2)
        indicators.volatility.atr = self.average_true_range(price_series, 14)
        indicators.volatility.volatility_ratio = self.volatility_ratio(price_series, 10, 30)

        # Volume Indicators (if available)
        if volume_series:
            indicators.volume.volume_sma = self.simple_moving_average(volume_series, 20)
            indicators.volume.volume_ratio = volume_series[-1] / indicators.volume.volume_sma
            indicators.volume.obv = self.on_balance_volume(price_series, volume_series)

        # Advanced Pattern Recognition
        indicators.patterns = await self.detect_chart_patterns(price_series)

        return indicators
```

### **Pattern Recognition Engine**:
```python
async def detect_chart_patterns(self, price_series: List[float]) -> PatternRecognition:
    """Advanced chart pattern detection"""

    patterns = PatternRecognition()

    # Classical patterns
    patterns.head_and_shoulders = self.detect_head_and_shoulders(price_series)
    patterns.double_top = self.detect_double_top(price_series)
    patterns.double_bottom = self.detect_double_bottom(price_series)
    patterns.triangle = self.detect_triangle_patterns(price_series)

    # Support/Resistance levels
    patterns.support_levels = self.find_support_levels(price_series)
    patterns.resistance_levels = self.find_resistance_levels(price_series)

    # Trend lines
    patterns.trend_lines = self.detect_trend_lines(price_series)

    # Breakout detection
    patterns.breakout_signals = self.detect_breakouts(price_series, patterns)

    # Pattern confidence scoring
    patterns.overall_confidence = self.calculate_pattern_confidence(patterns)

    return patterns
```

---

## 🔍 Multi-Tenant Feature Management

### **Subscription-Based Feature Access**:
```python
class FeatureAccessManager:
    def __init__(self):
        self.feature_tiers = {
            SubscriptionTier.FREE: {
                "basic_indicators": True,
                "advanced_indicators": False,
                "pattern_recognition": False,
                "cross_asset_correlation": False,
                "market_regime": False,
                "custom_indicators": False
            },
            SubscriptionTier.PRO: {
                "basic_indicators": True,
                "advanced_indicators": True,
                "pattern_recognition": True,
                "cross_asset_correlation": True,
                "market_regime": True,
                "custom_indicators": False
            },
            SubscriptionTier.ENTERPRISE: {
                "basic_indicators": True,
                "advanced_indicators": True,
                "pattern_recognition": True,
                "cross_asset_correlation": True,
                "market_regime": True,
                "custom_indicators": True
            }
        }

    async def get_user_features(self, user_context: UserContext) -> UserFeatureConfig:
        """Get subscription-based feature configuration"""

        tier = user_context.subscription_tier
        company_features = await self.get_company_features(user_context.company_id)

        # Combine subscription tier + company-specific features
        user_features = UserFeatureConfig()
        user_features.subscription_tier = tier
        user_features.enabled_features = self.feature_tiers[tier].copy()

        # Apply company-level overrides
        if company_features:
            user_features.enabled_features.update(company_features)

        # Apply user-specific preferences
        user_preferences = await self.get_user_preferences(user_context.user_id)
        if user_preferences:
            user_features.preferences = user_preferences

        return user_features
```

---

## ⚡ Performance Optimizations

### **Caching Strategy**:
```python
class FeatureCache:
    def __init__(self):
        self.indicator_cache = TTLCache(maxsize=1000, ttl=60)  # 1 minute TTL
        self.pattern_cache = TTLCache(maxsize=500, ttl=300)   # 5 minute TTL
        self.correlation_cache = TTLCache(maxsize=100, ttl=600) # 10 minute TTL

    async def get_cached_indicators(self, symbol: str, timestamp: int,
                                  timeframe: int) -> Optional[TechnicalIndicators]:
        """Smart caching for technical indicators"""

        cache_key = f"{symbol}:{timestamp}:{timeframe}"

        # Check cache first
        if cache_key in self.indicator_cache:
            return self.indicator_cache[cache_key]

        return None

    async def cache_indicators(self, symbol: str, timestamp: int,
                             timeframe: int, indicators: TechnicalIndicators):
        """Cache calculated indicators with smart TTL"""

        cache_key = f"{symbol}:{timestamp}:{timeframe}"
        self.indicator_cache[cache_key] = indicators
```

### **Parallel Processing**:
```python
async def process_multiple_symbols(self, enriched_batches: List[EnrichedBatchData],
                                 trace_context: TraceContext) -> List[FeatureVectorBatch]:
    """Parallel feature processing for multiple symbols"""

    # Create processing tasks
    tasks = []
    for batch in enriched_batches:
        task = asyncio.create_task(
            self.process_enriched_batch(batch, trace_context)
        )
        tasks.append(task)

    # Execute in parallel
    feature_batches = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle exceptions
    successful_batches = []
    for i, result in enumerate(feature_batches):
        if isinstance(result, Exception):
            self.logger.error(f"Feature processing failed for batch {i}: {result}")
            # Add error to trace
            self.tracer.add_error(trace_context.correlation_id, str(result))
        else:
            successful_batches.append(result)

    return successful_batches
```

---

## 🔍 Monitoring & Health Checks

### **Performance Metrics**:
```python
async def get_service_metrics() -> ServiceMetrics:
    """Comprehensive service health metrics"""

    return {
        "status": "healthy",
        "feature_processing_latency_ms": await get_avg_processing_latency(),
        "throughput_features_per_second": await get_feature_throughput(),
        "cache_hit_rate": await get_cache_hit_rate(),
        "pattern_detection_accuracy": await get_pattern_accuracy(),
        "circuit_breaker_status": await get_circuit_breaker_status(),
        "active_subscriptions": await get_active_subscription_count(),
        "correlation_id_tracking": await get_trace_status()
    }
```

### **Health Check Endpoint**:
```python
@app.get("/health")
async def health_check():
    """Multi-tenant aware health check"""

    health_status = {
        "service": "feature-engineering",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

    # Check critical dependencies
    try:
        # Central Hub connectivity
        await central_hub_client.ping()
        health_status["central_hub"] = "connected"

        # Protocol Buffers schema validation
        test_message = FeatureVector()
        health_status["protobuf_schemas"] = "valid"

        # Multi-tenant database access
        await test_user_access()
        health_status["multi_tenant_access"] = "valid"

        # Circuit breaker status
        health_status["circuit_breakers"] = await get_circuit_breaker_summary()

    except Exception as e:
        health_status["status"] = "degraded"
        health_status["error"] = str(e)

    return health_status
```

---

## 🔗 Service Integration

### **Central-Hub Registration**:
```python
async def register_with_central_hub():
    """Register service with Central-Hub coordination"""

    service_info = {
        "name": "feature-engineering",
        "host": os.getenv("SERVICE_HOST", "localhost"),
        "port": int(os.getenv("SERVICE_PORT", "8002")),
        "protocol": "http",
        "health_endpoint": "/health",
        "capabilities": [
            "technical_indicators",
            "pattern_recognition",
            "cross_asset_correlation",
            "market_regime_detection"
        ],
        "auth_required": True,
        "multi_tenant": True,
        "circuit_breaker_enabled": True
    }

    await central_hub_client.register_service(service_info)
```

### **Contract Definitions**:
- **Input Contract**: `contracts/inputs/from-data-bridge.md`
- **Output Contract**: `contracts/outputs/to-ml-processing.md`
- **Internal Contract**: `contracts/internal/feature-calculation.md`

---

## 🎯 Business Value

### **AI Performance Enhancement**:
- **Advanced Features**: 50+ technical indicators untuk comprehensive analysis
- **Pattern Recognition**: Classical + ML-based pattern detection
- **Market Context**: Real-time regime detection dan correlation analysis
- **Subscription Optimization**: Tier-based feature access untuk monetization

### **Technical Excellence**:
- **Sub-8ms Processing**: Contributing to <30ms total latency
- **Multi-Tenant Ready**: Company/user level feature isolation
- **Circuit Breaker Protected**: Resilient external API integration
- **Request Tracing**: Complete correlation ID tracking

### **Operational Benefits**:
- **Intelligent Caching**: Optimized performance dengan smart TTL
- **Parallel Processing**: Concurrent feature calculation
- **Health Monitoring**: Comprehensive service observability
- **Protocol Buffers**: 60% bandwidth savings, 10x faster serialization

---

**Input Flow**: Data-Bridge (validated data) → Feature-Engineering (advanced analysis)
**Output Flow**: Feature-Engineering → ML-Processing (ML-ready feature vectors)
**Key Innovation**: Advanced technical analysis dengan subscription-based feature access dan real-time market regime detection untuk optimal AI trading performance.