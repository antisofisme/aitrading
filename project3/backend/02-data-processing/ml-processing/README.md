# ML Processing Service

## 🎯 Purpose
**AI/ML inference engine** yang mengkonversi feature vectors menjadi actionable trading predictions menggunakan multiple models (LSTM, CNN, XGBoost), real-time pattern recognition, dan confidence scoring dengan <15ms inference time untuk high-frequency trading.

---

## 📊 ChainFlow Diagram

```
Feature-Engineering → ML-Processing → Trading-Engine → Risk-Management
        ↓                  ↓              ↓              ↓
    Feature Vectors    AI Predictions   Trading Signals  Risk Assessment
    Technical Analysis  Multi-Models    Decision Logic   Position Sizing
    Market Context     Pattern Recog    Signal Conf      Portfolio Mgmt
    Cross-Asset Corr   15ms Inference   Entry/Exit       Drawdown Control
```

---

## 🏗️ AI/ML Architecture

### **Input Flow**: ML-ready feature vectors from Feature-Engineering
**Data Source**: Feature-Engineering → ML-Processing
**Format**: Protocol Buffers (FeatureVectorBatch)
**Frequency**: 50+ feature vectors/second across 10 trading pairs
**Performance Target**: <15ms AI inference (critical path requirement)

### **Output Flow**: AI predictions and trading insights to Trading-Engine
**Destination**: Trading-Engine Service
**Format**: Protocol Buffers (MLPredictionBatch)
**Processing**: Multi-model ensemble + pattern recognition + confidence scoring
**Performance Target**: <15ms total inference time

---

## 🚀 Transport Architecture & Contract Integration

### **Transport Decision Matrix Applied**:

#### **Kategori A: High Volume + Mission Critical**
- **Primary Transport**: NATS + Protocol Buffers (<1ms latency)
- **Backup Transport**: Kafka + Protocol Buffers (guaranteed delivery)
- **Failover**: Automatic dengan sequence tracking
- **Services**: Feature Engineering → ML Processing, ML → Trading Engine
- **Performance**: <15ms AI inference (critical path requirement)

#### **Kategori B: Medium Volume + Important**
- **Transport**: gRPC (HTTP/2 + Protocol Buffers)
- **Connection**: Pooling + circuit breaker
- **Services**: Model management, performance monitoring

#### **Kategori C: Low Volume + Standard**
- **Transport**: HTTP REST + JSON via Kong Gateway
- **Backup**: Redis Queue for reliability
- **Services**: AI configuration, model deployment

### **Global Decisions Applied**:
✅ **Multi-Transport Architecture**: NATS+Kafka for inference, gRPC for management, HTTP for config
✅ **Protocol Buffers Communication**: 60% smaller model payloads, 10x faster serialization
✅ **Multi-Tenant Architecture**: Company/user-level model isolation and access control
✅ **Request Tracing**: Complete correlation ID tracking through AI pipeline
✅ **Central-Hub Coordination**: Model registry and performance monitoring
✅ **JWT + Protocol Buffers Auth**: Optimized authentication for AI endpoints
✅ **Circuit Breaker Pattern**: Model failover and fallback predictions

### **Schema Dependencies**:
```python
# Import from centralized schemas
import sys
sys.path.append('../../../01-core-infrastructure/central-hub/static/generated/python')

from ml.feature_vectors_pb2 import FeatureVectorBatch, FeatureVector
from ml.ml_predictions_pb2 import MLPredictionBatch, Prediction, ModelEnsemble
from ml.model_metadata_pb2 import ModelInfo, ModelPerformance, ModelMetrics
from common.user_context_pb2 import UserContext, SubscriptionTier
from common.request_trace_pb2 import RequestTrace, TraceContext
from trading.market_patterns_pb2 import PatternPrediction, TrendAnalysis
```

### **Enhanced ML MessageEnvelope**:
```protobuf
message MLProcessingEnvelope {
  string message_type = 1;           // "ml_inference"
  string user_id = 2;                // Multi-tenant user identification
  string company_id = 3;             // Multi-tenant company identification
  bytes payload = 4;                 // MLPredictionBatch protobuf
  int64 timestamp = 5;               // Inference timestamp
  string service_source = 6;         // "ml-processing"
  string correlation_id = 7;         // Request tracing
  TraceContext trace_context = 8;    // Distributed tracing
  ModelInfo model_info = 9;          // Active model metadata
  AuthToken auth_token = 10;         // JWT + Protocol Buffers auth
}
```

---

## 🤖 Multi-Model AI Engine

### **1. Model Ensemble Manager**:
```python
class ModelEnsembleManager:
    def __init__(self, central_hub_client):
        self.central_hub = central_hub_client
        self.circuit_breaker = CircuitBreaker("ml-models")
        self.model_registry = ModelRegistry()
        self.models = {}

    async def initialize_models(self):
        """Load and initialize AI models with multi-tenant support"""

        # LSTM for price prediction
        self.models['lstm_price'] = await self.load_model(
            'lstm_price_v2.1', ModelType.LSTM
        )

        # CNN for pattern recognition
        self.models['cnn_patterns'] = await self.load_model(
            'cnn_patterns_v1.8', ModelType.CNN
        )

        # XGBoost for direction prediction
        self.models['xgboost_direction'] = await self.load_model(
            'xgboost_direction_v3.2', ModelType.XGBOOST
        )

        # Ensemble meta-model
        self.models['ensemble_meta'] = await self.load_model(
            'ensemble_meta_v1.5', ModelType.ENSEMBLE
        )

    async def predict_ensemble(self, feature_batch: FeatureVectorBatch,
                             user_context: UserContext,
                             trace_context: TraceContext) -> MLPredictionBatch:
        """Multi-model ensemble prediction with circuit breaker protection"""

        # Request tracing
        with self.tracer.trace("ml_ensemble_inference", trace_context.correlation_id):
            start_time = time.time()

            prediction_batch = MLPredictionBatch()
            prediction_batch.user_id = feature_batch.user_id
            prediction_batch.company_id = feature_batch.company_id
            prediction_batch.correlation_id = trace_context.correlation_id

            # Multi-tenant model selection
            available_models = await self.get_user_models(user_context)

            for feature_vector in feature_batch.feature_vectors:
                # Individual model predictions
                model_predictions = {}

                for model_name in available_models:
                    if self.circuit_breaker.is_open(model_name):
                        # Use fallback prediction
                        model_predictions[model_name] = await self.get_fallback_prediction(
                            feature_vector, model_name
                        )
                    else:
                        try:
                            prediction = await self.predict_single_model(
                                feature_vector, model_name, trace_context
                            )
                            model_predictions[model_name] = prediction

                        except Exception as e:
                            # Trip circuit breaker
                            self.circuit_breaker.trip(model_name)

                            # Fallback prediction
                            model_predictions[model_name] = await self.get_fallback_prediction(
                                feature_vector, model_name
                            )

                            # Add error to trace
                            self.tracer.add_error(trace_context.correlation_id,
                                                f"Model {model_name} failed: {str(e)}")

                # Ensemble combination
                ensemble_prediction = await self.combine_predictions(
                    model_predictions, user_context, trace_context
                )

                prediction_batch.predictions.append(ensemble_prediction)

            # Performance metrics
            inference_time = (time.time() - start_time) * 1000
            prediction_batch.performance_metrics.inference_time_ms = inference_time
            prediction_batch.performance_metrics.model_count = len(available_models)

            return prediction_batch
```

### **2. LSTM Price Prediction Engine**:
```python
class LSTMPricePrediction:
    def __init__(self, model_path: str):
        self.model = self.load_tensorflow_model(model_path)
        self.sequence_length = 50
        self.prediction_horizons = [1, 5, 15, 60]  # minutes

    async def predict_price(self, feature_vector: FeatureVector,
                          user_context: UserContext) -> PricePrediction:
        """Multi-horizon price prediction with LSTM"""

        price_prediction = PricePrediction()
        price_prediction.symbol = feature_vector.symbol
        price_prediction.base_price = feature_vector.price_features.mid_price

        # Prepare input sequence
        input_sequence = await self.prepare_lstm_input(feature_vector)

        # Multi-horizon predictions
        for horizon in self.prediction_horizons:
            # Subscription-based horizon access
            if not self.has_horizon_access(horizon, user_context.subscription_tier):
                continue

            # LSTM inference
            predicted_price = await self.model_predict(input_sequence, horizon)

            # Calculate confidence
            confidence = await self.calculate_prediction_confidence(
                input_sequence, predicted_price, horizon
            )

            # Add prediction
            horizon_prediction = HorizonPrediction()
            horizon_prediction.horizon_minutes = horizon
            horizon_prediction.predicted_price = predicted_price
            horizon_prediction.confidence = confidence
            horizon_prediction.direction = self.calculate_direction(
                price_prediction.base_price, predicted_price
            )

            price_prediction.horizon_predictions.append(horizon_prediction)

        return price_prediction

    def has_horizon_access(self, horizon: int, tier: SubscriptionTier) -> bool:
        """Multi-tenant horizon access control"""

        horizon_access = {
            SubscriptionTier.FREE: [1],           # 1 minute only
            SubscriptionTier.PRO: [1, 5, 15],    # Up to 15 minutes
            SubscriptionTier.ENTERPRISE: [1, 5, 15, 60]  # All horizons
        }

        return horizon in horizon_access.get(tier, [])
```

### **3. CNN Pattern Recognition Engine**:
```python
class CNNPatternRecognition:
    def __init__(self, model_path: str):
        self.model = self.load_tensorflow_model(model_path)
        self.pattern_types = [
            'head_and_shoulders', 'double_top', 'double_bottom',
            'triangle', 'flag', 'pennant', 'wedge'
        ]

    async def recognize_patterns(self, feature_vector: FeatureVector,
                               historical_data: List[float]) -> PatternPrediction:
        """Advanced pattern recognition with CNN"""

        pattern_prediction = PatternPrediction()
        pattern_prediction.symbol = feature_vector.symbol
        pattern_prediction.analysis_timestamp = feature_vector.timestamp

        # Convert price data to image representation
        price_image = await self.convert_to_image(historical_data)

        # CNN inference for pattern detection
        pattern_probabilities = await self.model_predict(price_image)

        # Process each pattern type
        for i, pattern_type in enumerate(self.pattern_types):
            probability = pattern_probabilities[i]

            if probability > 0.3:  # Threshold for pattern detection
                pattern_detection = PatternDetection()
                pattern_detection.pattern_type = pattern_type
                pattern_detection.probability = probability
                pattern_detection.confidence = await self.calculate_pattern_confidence(
                    pattern_type, probability, historical_data
                )

                # Pattern target calculation
                pattern_detection.target_price = await self.calculate_pattern_target(
                    pattern_type, historical_data, feature_vector.price_features.mid_price
                )

                # Pattern timeline
                pattern_detection.expected_completion_minutes = \
                    await self.estimate_pattern_timeline(pattern_type, historical_data)

                pattern_prediction.detected_patterns.append(pattern_detection)

        # Overall pattern signal
        pattern_prediction.overall_signal = await self.synthesize_pattern_signal(
            pattern_prediction.detected_patterns
        )

        return pattern_prediction
```

### **4. XGBoost Direction Prediction**:
```python
class XGBoostDirectionPredictor:
    def __init__(self, model_path: str):
        self.model = joblib.load(model_path)
        self.feature_importance = self.model.feature_importances_

    async def predict_direction(self, feature_vector: FeatureVector,
                              user_context: UserContext) -> DirectionPrediction:
        """Market direction prediction with XGBoost"""

        direction_prediction = DirectionPrediction()
        direction_prediction.symbol = feature_vector.symbol

        # Prepare features for XGBoost
        features = await self.prepare_xgboost_features(feature_vector, user_context)

        # XGBoost inference
        direction_probabilities = self.model.predict_proba([features])[0]

        # Direction classification (0: SELL, 1: HOLD, 2: BUY)
        direction_prediction.buy_probability = direction_probabilities[2]
        direction_prediction.hold_probability = direction_probabilities[1]
        direction_prediction.sell_probability = direction_probabilities[0]

        # Primary direction
        max_prob_index = np.argmax(direction_probabilities)
        direction_prediction.primary_direction = ['SELL', 'HOLD', 'BUY'][max_prob_index]
        direction_prediction.confidence = direction_probabilities[max_prob_index]

        # Feature importance analysis
        if user_context.subscription_tier >= SubscriptionTier.PRO:
            direction_prediction.feature_importance = await self.analyze_feature_importance(
                features, feature_vector
            )

        return direction_prediction

    async def prepare_xgboost_features(self, feature_vector: FeatureVector,
                                     user_context: UserContext) -> List[float]:
        """Prepare feature array for XGBoost model"""

        features = []

        # Price features (always included)
        features.extend([
            feature_vector.price_features.bid,
            feature_vector.price_features.ask,
            feature_vector.price_features.spread,
            feature_vector.price_features.mid_price
        ])

        # Technical indicators (subscription-based)
        if hasattr(feature_vector, 'technical_indicators'):
            indicators = feature_vector.technical_indicators
            features.extend([
                indicators.trend.sma_20,
                indicators.trend.ema_12,
                indicators.trend.ema_26,
                indicators.trend.macd,
                indicators.momentum.rsi_14,
                indicators.volatility.atr
            ])

        # Cross-asset features (Pro+ only)
        if (user_context.subscription_tier >= SubscriptionTier.PRO and
            hasattr(feature_vector, 'cross_asset')):
            features.extend(feature_vector.cross_asset.correlation_scores)

        # Normalize features
        features = self.normalize_features(features)

        return features
```

---

## 🔍 Model Performance Monitoring

### **Real-time Model Metrics**:
```python
class ModelPerformanceMonitor:
    def __init__(self):
        self.metrics_store = {}
        self.performance_threshold = 0.6  # Minimum accuracy

    async def track_prediction_accuracy(self, prediction: Prediction,
                                      actual_outcome: float,
                                      trace_context: TraceContext):
        """Track model prediction accuracy in real-time"""

        model_id = prediction.model_info.model_id

        # Calculate prediction error
        prediction_error = abs(prediction.predicted_value - actual_outcome)
        accuracy = 1.0 - min(prediction_error / actual_outcome, 1.0)

        # Update model metrics
        if model_id not in self.metrics_store:
            self.metrics_store[model_id] = ModelMetrics()

        metrics = self.metrics_store[model_id]
        metrics.total_predictions += 1
        metrics.cumulative_accuracy += accuracy
        metrics.average_accuracy = metrics.cumulative_accuracy / metrics.total_predictions

        # Track confidence vs accuracy
        confidence_bucket = int(prediction.confidence * 10)  # 0-10 buckets
        metrics.confidence_accuracy[confidence_bucket].append(accuracy)

        # Model drift detection
        if metrics.total_predictions % 100 == 0:  # Check every 100 predictions
            recent_accuracy = await self.calculate_recent_accuracy(model_id, 100)
            if recent_accuracy < self.performance_threshold:
                await self.trigger_model_retrain_alert(model_id, recent_accuracy, trace_context)

        # Log performance metrics
        self.logger.info(f"Model {model_id} accuracy: {accuracy:.3f}", extra={
            "correlation_id": trace_context.correlation_id,
            "model_id": model_id,
            "accuracy": accuracy,
            "confidence": prediction.confidence
        })

    async def trigger_model_retrain_alert(self, model_id: str, accuracy: float,
                                        trace_context: TraceContext):
        """Alert when model performance degrades"""

        alert = ModelPerformanceAlert()
        alert.model_id = model_id
        alert.current_accuracy = accuracy
        alert.threshold = self.performance_threshold
        alert.recommendation = "RETRAIN"
        alert.correlation_id = trace_context.correlation_id

        # Send to notification system
        await self.notification_service.send_model_alert(alert)

        # Circuit breaker consideration
        if accuracy < 0.4:  # Critical threshold
            self.circuit_breaker.trip(model_id)
```

### **Model A/B Testing**:
```python
class ModelABTesting:
    def __init__(self):
        self.ab_configs = {}
        self.test_results = {}

    async def run_ab_test(self, feature_vector: FeatureVector,
                        user_context: UserContext,
                        trace_context: TraceContext) -> Prediction:
        """A/B test different models for continuous improvement"""

        # Check if user is in A/B test
        test_config = await self.get_ab_config(user_context.user_id)

        if test_config:
            # Select model based on A/B test assignment
            model_variant = test_config.variant  # 'A' or 'B'
            model_id = test_config.models[model_variant]

            # Make prediction with assigned model
            prediction = await self.predict_with_model(
                feature_vector, model_id, trace_context
            )

            # Track A/B test result
            await self.track_ab_result(
                test_config.test_id, model_variant, prediction, trace_context
            )

            return prediction
        else:
            # Use production model
            return await self.predict_with_production_model(feature_vector, trace_context)
```

---

## 🔍 Multi-Tenant Model Management

### **User-Specific Model Access**:
```python
class TenantModelManager:
    def __init__(self):
        self.tenant_models = {}
        self.subscription_access = {
            SubscriptionTier.FREE: ['basic_lstm', 'simple_pattern'],
            SubscriptionTier.PRO: ['advanced_lstm', 'cnn_patterns', 'xgboost_direction'],
            SubscriptionTier.ENTERPRISE: ['all_models', 'custom_models', 'ensemble_meta']
        }

    async def get_user_models(self, user_context: UserContext) -> List[str]:
        """Get available models based on subscription tier"""

        tier = user_context.subscription_tier
        company_models = await self.get_company_models(user_context.company_id)

        # Base models from subscription
        available_models = self.subscription_access[tier].copy()

        # Add company-specific models
        if company_models:
            available_models.extend(company_models)

        # Add user custom models (Enterprise only)
        if tier == SubscriptionTier.ENTERPRISE:
            user_models = await self.get_user_custom_models(user_context.user_id)
            available_models.extend(user_models)

        return available_models

    async def get_company_models(self, company_id: str) -> List[str]:
        """Get company-specific trained models"""

        # Companies can have custom models trained on their data
        company_models = await self.database.get_company_models(company_id)
        return [model.model_id for model in company_models if model.status == 'active']
```

---

## ⚡ Performance Optimizations

### **Model Caching and Preloading**:
```python
class ModelCache:
    def __init__(self):
        self.model_cache = {}
        self.prediction_cache = TTLCache(maxsize=1000, ttl=30)  # 30 seconds TTL

    async def get_model(self, model_id: str):
        """Get model with intelligent caching"""

        if model_id not in self.model_cache:
            # Load model on-demand
            model = await self.load_model_from_storage(model_id)
            self.model_cache[model_id] = model

            # Warm up model (first prediction is often slower)
            await self.warm_up_model(model)

        return self.model_cache[model_id]

    async def warm_up_model(self, model):
        """Warm up model with dummy prediction"""
        try:
            dummy_input = self.create_dummy_input(model.input_shape)
            _ = await model.predict(dummy_input)
        except Exception as e:
            self.logger.warning(f"Model warm-up failed: {e}")
```

### **Batch Inference Optimization**:
```python
async def batch_inference(self, feature_batches: List[FeatureVectorBatch],
                        trace_context: TraceContext) -> List[MLPredictionBatch]:
    """Optimized batch processing for multiple symbols"""

    # Group by model requirements
    model_groups = self.group_by_models(feature_batches)

    # Process each model group in parallel
    tasks = []
    for model_id, batches in model_groups.items():
        task = asyncio.create_task(
            self.process_model_batch(model_id, batches, trace_context)
        )
        tasks.append(task)

    # Execute in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Combine results
    prediction_batches = []
    for result in results:
        if isinstance(result, Exception):
            self.logger.error(f"Batch inference failed: {result}")
            # Add error to trace
            self.tracer.add_error(trace_context.correlation_id, str(result))
        else:
            prediction_batches.extend(result)

    return prediction_batches
```

---

## 🔍 Health Monitoring & Alerts

### **Service Health Check**:
```python
@app.get("/health")
async def health_check():
    """Comprehensive ML service health check"""

    health_status = {
        "service": "ml-processing",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.1.0"
    }

    try:
        # Model availability check
        for model_id in self.active_models:
            model_health = await self.check_model_health(model_id)
            health_status[f"model_{model_id}"] = model_health

        # GPU/CPU resources
        health_status["gpu_memory"] = await self.get_gpu_memory_usage()
        health_status["cpu_usage"] = await self.get_cpu_usage()

        # Inference performance
        health_status["avg_inference_time_ms"] = await self.get_avg_inference_time()
        health_status["throughput_predictions_per_second"] = await self.get_throughput()

        # Circuit breaker status
        health_status["circuit_breakers"] = await self.get_circuit_breaker_summary()

        # Multi-tenant metrics
        health_status["active_tenants"] = await self.get_active_tenant_count()

    except Exception as e:
        health_status["status"] = "degraded"
        health_status["error"] = str(e)

    return health_status
```

---

## 🎯 Business Value

### **AI Performance Leadership**:
- **Sub-15ms Inference**: Critical path requirement for high-frequency trading
- **Multi-Model Ensemble**: LSTM + CNN + XGBoost untuk comprehensive analysis
- **Real-time Pattern Recognition**: Advanced chart pattern detection dengan CNN
- **Subscription-Based Access**: Tiered model access untuk revenue optimization

### **Technical Excellence**:
- **Circuit Breaker Protected**: Model failover dan fallback predictions
- **Multi-Tenant Isolation**: Company/user-level model access control
- **A/B Testing Framework**: Continuous model improvement
- **Performance Monitoring**: Real-time accuracy tracking dan drift detection

### **Operational Benefits**:
- **Protocol Buffers**: 60% smaller model payloads, 10x faster serialization
- **Request Tracing**: Complete correlation ID tracking through AI pipeline
- **Intelligent Caching**: Model preloading dan prediction caching
- **Batch Optimization**: Parallel inference untuk multiple symbols

---

## 🔗 Service Contract Specifications

### **ML Processing Proto Contracts**:
- **Input Contract**: Feature Vectors via NATS/Kafka dari Feature Engineering
- **Output Contract**: ML Predictions via NATS/Kafka ke Trading Engine
- **Model Management**: gRPC service untuk model deployment dan monitoring

### **Critical Path Integration**:
- **Feature-Engineering → ML-Processing**: NATS primary, Kafka backup
- **ML-Processing → Trading-Engine**: NATS primary, Kafka backup
- **Multi-Model Ensemble**: LSTM + CNN + XGBoost dengan intelligent routing

---

**Input Flow**: Feature-Engineering (feature vectors) → ML-Processing (AI inference)
**Output Flow**: ML-Processing → Trading-Engine (actionable predictions)
**Key Innovation**: Sub-15ms multi-model AI inference dengan multi-transport architecture, real-time pattern recognition dan subscription-based model access untuk optimal trading performance.