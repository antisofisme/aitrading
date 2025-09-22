"""
ML Service Architecture for Business Integration
==============================================

Multi-tenant ML serving architecture that enables monetization and scalability
while maintaining existing ML performance (68-75% accuracy) for 1000+ concurrent users.

Key Features:
- Per-user model customization and isolation
- Subscription tier access controls
- Real-time API serving (<100ms inference)
- Usage tracking for billing
- Performance monitoring per tenant
- Cost optimization per user
"""

import asyncio
import numpy as np
import pandas as pd
import redis
import json
import time
import uuid
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
import hashlib
import pickle
import warnings
warnings.filterwarnings('ignore')

# Configuration for multi-tenant architecture
class SubscriptionTier(Enum):
    """Subscription tiers with different feature access"""
    FREE = "free"
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

class ModelType(Enum):
    """Available ML model types"""
    XGBOOST_ENSEMBLE = "xgboost_ensemble"
    MARKET_REGIME_CLASSIFIER = "market_regime_classifier"
    DYNAMIC_RETRAINING = "dynamic_retraining"
    CROSS_ASSET_CORRELATION = "cross_asset_correlation"
    PROBABILISTIC_SIGNAL = "probabilistic_signal"

@dataclass
class TierLimits:
    """Limits for each subscription tier"""
    requests_per_minute: int
    requests_per_day: int
    models_available: List[ModelType]
    custom_model_training: bool
    real_time_predictions: bool
    historical_data_years: int
    concurrent_requests: int
    api_rate_limit_ms: int
    features_enabled: List[str]
    storage_gb: int
    support_level: str

# Subscription tier configurations
TIER_CONFIGURATIONS = {
    SubscriptionTier.FREE: TierLimits(
        requests_per_minute=10,
        requests_per_day=100,
        models_available=[ModelType.XGBOOST_ENSEMBLE],
        custom_model_training=False,
        real_time_predictions=False,
        historical_data_years=1,
        concurrent_requests=1,
        api_rate_limit_ms=1000,
        features_enabled=["basic_predictions"],
        storage_gb=1,
        support_level="community"
    ),
    SubscriptionTier.BASIC: TierLimits(
        requests_per_minute=100,
        requests_per_day=2000,
        models_available=[ModelType.XGBOOST_ENSEMBLE, ModelType.MARKET_REGIME_CLASSIFIER],
        custom_model_training=False,
        real_time_predictions=True,
        historical_data_years=2,
        concurrent_requests=5,
        api_rate_limit_ms=500,
        features_enabled=["basic_predictions", "market_regime", "real_time"],
        storage_gb=5,
        support_level="email"
    ),
    SubscriptionTier.PROFESSIONAL: TierLimits(
        requests_per_minute=1000,
        requests_per_day=20000,
        models_available=[ModelType.XGBOOST_ENSEMBLE, ModelType.MARKET_REGIME_CLASSIFIER,
                         ModelType.DYNAMIC_RETRAINING, ModelType.CROSS_ASSET_CORRELATION],
        custom_model_training=True,
        real_time_predictions=True,
        historical_data_years=5,
        concurrent_requests=20,
        api_rate_limit_ms=100,
        features_enabled=["basic_predictions", "market_regime", "real_time",
                         "custom_training", "correlation_analysis"],
        storage_gb=25,
        support_level="priority"
    ),
    SubscriptionTier.ENTERPRISE: TierLimits(
        requests_per_minute=10000,
        requests_per_day=200000,
        models_available=list(ModelType),
        custom_model_training=True,
        real_time_predictions=True,
        historical_data_years=10,
        concurrent_requests=100,
        api_rate_limit_ms=50,
        features_enabled=["all"],
        storage_gb=100,
        support_level="dedicated"
    )
}

@dataclass
class UserContext:
    """User context for multi-tenant operations"""
    user_id: str
    tenant_id: str
    subscription_tier: SubscriptionTier
    api_key: str
    tier_limits: TierLimits
    usage_stats: Dict[str, Any] = field(default_factory=dict)
    custom_models: Dict[str, str] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PredictionRequest:
    """ML prediction request with user context"""
    request_id: str
    user_context: UserContext
    model_type: ModelType
    input_data: Dict[str, Any]
    timestamp: datetime
    priority: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PredictionResponse:
    """ML prediction response with billing info"""
    request_id: str
    user_id: str
    prediction: Union[float, np.ndarray, Dict[str, Any]]
    confidence: float
    model_version: str
    processing_time_ms: float
    billing_info: Dict[str, Any]
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

class RateLimiter:
    """Redis-based rate limiter for API requests"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def check_rate_limit(self, user_id: str, tier_limits: TierLimits) -> Tuple[bool, Dict[str, Any]]:
        """Check if user is within rate limits"""
        current_time = int(time.time())
        minute_key = f"rate_limit:{user_id}:minute:{current_time // 60}"
        day_key = f"rate_limit:{user_id}:day:{current_time // 86400}"

        # Get current counts
        minute_count = int(self.redis.get(minute_key) or 0)
        day_count = int(self.redis.get(day_key) or 0)

        # Check limits
        minute_allowed = minute_count < tier_limits.requests_per_minute
        day_allowed = day_count < tier_limits.requests_per_day

        rate_limit_info = {
            "minute_count": minute_count,
            "minute_limit": tier_limits.requests_per_minute,
            "day_count": day_count,
            "day_limit": tier_limits.requests_per_day,
            "minute_remaining": max(0, tier_limits.requests_per_minute - minute_count),
            "day_remaining": max(0, tier_limits.requests_per_day - day_count)
        }

        if minute_allowed and day_allowed:
            # Increment counters
            pipe = self.redis.pipeline()
            pipe.incr(minute_key, 1)
            pipe.expire(minute_key, 60)
            pipe.incr(day_key, 1)
            pipe.expire(day_key, 86400)
            pipe.execute()

            return True, rate_limit_info
        else:
            return False, rate_limit_info

class UsageTracker:
    """Track usage for billing and analytics"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def record_usage(self, user_id: str, model_type: ModelType,
                          processing_time_ms: float, input_size: int,
                          subscription_tier: SubscriptionTier):
        """Record usage for billing calculations"""
        timestamp = int(time.time())
        usage_key = f"usage:{user_id}:{timestamp // 3600}"  # Hourly buckets

        usage_data = {
            "model_type": model_type.value,
            "processing_time_ms": processing_time_ms,
            "input_size": input_size,
            "subscription_tier": subscription_tier.value,
            "timestamp": timestamp,
            "cost_units": self._calculate_cost_units(model_type, processing_time_ms,
                                                   input_size, subscription_tier)
        }

        # Store in Redis with TTL
        self.redis.lpush(usage_key, json.dumps(usage_data))
        self.redis.expire(usage_key, 86400 * 30)  # Keep for 30 days

        # Update daily aggregates
        daily_key = f"usage_daily:{user_id}:{timestamp // 86400}"
        self.redis.hincrby(daily_key, "total_requests", 1)
        self.redis.hincrby(daily_key, "total_processing_time", int(processing_time_ms))
        self.redis.expire(daily_key, 86400 * 365)  # Keep for 1 year

    def _calculate_cost_units(self, model_type: ModelType, processing_time_ms: float,
                            input_size: int, subscription_tier: SubscriptionTier) -> float:
        """Calculate cost units for billing"""

        # Base cost per model type (normalized to complexity)
        model_costs = {
            ModelType.XGBOOST_ENSEMBLE: 1.0,
            ModelType.MARKET_REGIME_CLASSIFIER: 1.5,
            ModelType.DYNAMIC_RETRAINING: 2.0,
            ModelType.CROSS_ASSET_CORRELATION: 1.8,
            ModelType.PROBABILISTIC_SIGNAL: 2.2
        }

        # Tier multipliers (lower tiers cost more per unit to encourage upgrades)
        tier_multipliers = {
            SubscriptionTier.FREE: 1.0,
            SubscriptionTier.BASIC: 0.8,
            SubscriptionTier.PROFESSIONAL: 0.6,
            SubscriptionTier.ENTERPRISE: 0.4
        }

        base_cost = model_costs.get(model_type, 1.0)
        time_factor = processing_time_ms / 100.0  # Normalize to 100ms
        size_factor = max(1.0, input_size / 1000.0)  # Normalize to 1000 features
        tier_multiplier = tier_multipliers.get(subscription_tier, 1.0)

        return base_cost * time_factor * size_factor * tier_multiplier

class ModelRegistry:
    """Registry for managing user models and versions"""

    def __init__(self, redis_client: redis.Redis, storage_path: str):
        self.redis = redis_client
        self.storage_path = storage_path
        self.global_models = {}
        self.user_models = {}

    async def register_global_model(self, model_type: ModelType, model_instance: Any,
                                  version: str, metadata: Dict[str, Any]):
        """Register a global model available to all users"""
        model_key = f"global_model:{model_type.value}:{version}"

        model_info = {
            "model_type": model_type.value,
            "version": version,
            "metadata": metadata,
            "created_at": datetime.now().isoformat(),
            "status": "active"
        }

        # Store model info in Redis
        self.redis.hset(model_key, mapping=model_info)

        # Store model instance in memory (in production, use proper model storage)
        self.global_models[f"{model_type.value}:{version}"] = model_instance

    async def register_user_model(self, user_id: str, model_type: ModelType,
                                model_instance: Any, version: str,
                                metadata: Dict[str, Any]):
        """Register a user-specific custom model"""
        model_key = f"user_model:{user_id}:{model_type.value}:{version}"

        model_info = {
            "user_id": user_id,
            "model_type": model_type.value,
            "version": version,
            "metadata": metadata,
            "created_at": datetime.now().isoformat(),
            "status": "active"
        }

        # Store model info in Redis
        self.redis.hset(model_key, mapping=model_info)

        # Store model instance (in production, use persistent storage)
        user_key = f"{user_id}:{model_type.value}:{version}"
        self.user_models[user_key] = model_instance

    async def get_model(self, user_context: UserContext, model_type: ModelType,
                       version: str = "latest") -> Optional[Any]:
        """Get model instance for user"""

        # First check for user-specific model
        user_key = f"{user_context.user_id}:{model_type.value}:{version}"
        if user_key in self.user_models:
            return self.user_models[user_key]

        # Fall back to global model
        global_key = f"{model_type.value}:{version}"
        if global_key in self.global_models:
            return self.global_models[global_key]

        return None

class MLServiceOrchestrator:
    """Main orchestrator for multi-tenant ML service"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)
        self.rate_limiter = RateLimiter(self.redis)
        self.usage_tracker = UsageTracker(self.redis)
        self.model_registry = ModelRegistry(self.redis, "/tmp/models")

        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=50)

        # Performance metrics
        self.performance_metrics = {
            "total_requests": 0,
            "total_processing_time": 0.0,
            "error_count": 0,
            "cache_hits": 0
        }

        self.logger = logging.getLogger("MLServiceOrchestrator")

    async def authenticate_user(self, api_key: str) -> Optional[UserContext]:
        """Authenticate user and return context"""
        # In production, this would query a user database
        user_data = self.redis.hgetall(f"api_key:{api_key}")

        if not user_data:
            return None

        user_id = user_data.get(b'user_id', b'').decode()
        tenant_id = user_data.get(b'tenant_id', b'').decode()
        tier_str = user_data.get(b'subscription_tier', b'free').decode()

        subscription_tier = SubscriptionTier(tier_str)
        tier_limits = TIER_CONFIGURATIONS[subscription_tier]

        return UserContext(
            user_id=user_id,
            tenant_id=tenant_id,
            subscription_tier=subscription_tier,
            api_key=api_key,
            tier_limits=tier_limits
        )

    async def validate_request(self, user_context: UserContext,
                             model_type: ModelType) -> Tuple[bool, str]:
        """Validate if user can access the requested model"""

        # Check if model is available for user's tier
        if model_type not in user_context.tier_limits.models_available:
            return False, f"Model {model_type.value} not available for {user_context.subscription_tier.value} tier"

        # Check rate limits
        rate_allowed, rate_info = await self.rate_limiter.check_rate_limit(
            user_context.user_id, user_context.tier_limits
        )

        if not rate_allowed:
            return False, f"Rate limit exceeded. Requests remaining: {rate_info['minute_remaining']}/minute, {rate_info['day_remaining']}/day"

        return True, "Valid"

    async def process_prediction_request(self, request: PredictionRequest) -> PredictionResponse:
        """Process ML prediction request with full business logic"""
        start_time = time.time()

        try:
            # Validate request
            is_valid, message = await self.validate_request(
                request.user_context, request.model_type
            )

            if not is_valid:
                raise ValueError(message)

            # Get model for user
            model = await self.model_registry.get_model(
                request.user_context, request.model_type
            )

            if model is None:
                raise ValueError(f"Model {request.model_type.value} not found")

            # Check cache first
            cache_key = self._generate_cache_key(request)
            cached_result = self.redis.get(cache_key)

            if cached_result:
                self.performance_metrics["cache_hits"] += 1
                cached_data = json.loads(cached_result)
                processing_time = (time.time() - start_time) * 1000

                return PredictionResponse(
                    request_id=request.request_id,
                    user_id=request.user_context.user_id,
                    prediction=cached_data["prediction"],
                    confidence=cached_data["confidence"],
                    model_version=cached_data["model_version"],
                    processing_time_ms=processing_time,
                    billing_info=cached_data["billing_info"],
                    timestamp=datetime.now(),
                    metadata={"from_cache": True}
                )

            # Process prediction
            prediction, confidence = await self._run_prediction(model, request.input_data)

            processing_time = (time.time() - start_time) * 1000

            # Calculate billing info
            input_size = len(str(request.input_data))
            cost_units = await self._calculate_billing(
                request.user_context, request.model_type, processing_time, input_size
            )

            billing_info = {
                "cost_units": cost_units,
                "subscription_tier": request.user_context.subscription_tier.value,
                "processing_time_ms": processing_time
            }

            # Record usage
            await self.usage_tracker.record_usage(
                request.user_context.user_id,
                request.model_type,
                processing_time,
                input_size,
                request.user_context.subscription_tier
            )

            # Cache result (if enabled for tier)
            if request.user_context.subscription_tier != SubscriptionTier.FREE:
                cache_data = {
                    "prediction": prediction if isinstance(prediction, (int, float, str)) else prediction.tolist(),
                    "confidence": confidence,
                    "model_version": "1.0",
                    "billing_info": billing_info
                }
                self.redis.setex(cache_key, 300, json.dumps(cache_data))  # 5-minute cache

            # Update metrics
            self.performance_metrics["total_requests"] += 1
            self.performance_metrics["total_processing_time"] += processing_time

            return PredictionResponse(
                request_id=request.request_id,
                user_id=request.user_context.user_id,
                prediction=prediction,
                confidence=confidence,
                model_version="1.0",
                processing_time_ms=processing_time,
                billing_info=billing_info,
                timestamp=datetime.now(),
                metadata={"from_cache": False}
            )

        except Exception as e:
            self.performance_metrics["error_count"] += 1
            self.logger.error(f"Prediction request failed: {e}")
            raise

    async def _run_prediction(self, model: Any, input_data: Dict[str, Any]) -> Tuple[Any, float]:
        """Run prediction on model"""
        # Convert input data to format expected by model
        if hasattr(model, 'predict'):
            # For sklearn-style models
            features = np.array(list(input_data.values())).reshape(1, -1)
            prediction = model.predict(features)[0]

            # Calculate confidence (simplified)
            if hasattr(model, 'predict_proba'):
                probabilities = model.predict_proba(features)
                confidence = float(np.max(probabilities))
            else:
                confidence = 0.85  # Default confidence

            return prediction, confidence
        else:
            # For custom models
            prediction = await model.predict(input_data)
            confidence = 0.80
            return prediction, confidence

    async def _calculate_billing(self, user_context: UserContext, model_type: ModelType,
                               processing_time_ms: float, input_size: int) -> float:
        """Calculate billing units for request"""
        return self.usage_tracker._calculate_cost_units(
            model_type, processing_time_ms, input_size, user_context.subscription_tier
        )

    def _generate_cache_key(self, request: PredictionRequest) -> str:
        """Generate cache key for request"""
        data_hash = hashlib.md5(str(request.input_data).encode()).hexdigest()
        return f"prediction:{request.user_context.user_id}:{request.model_type.value}:{data_hash}"

    async def get_user_analytics(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """Get analytics for user"""
        analytics = {
            "total_requests": 0,
            "total_cost_units": 0.0,
            "avg_processing_time": 0.0,
            "model_usage": {},
            "daily_usage": []
        }

        # Get usage data for the last N days
        current_time = int(time.time())
        for i in range(days):
            day_timestamp = current_time - (i * 86400)
            daily_key = f"usage_daily:{user_id}:{day_timestamp // 86400}"
            daily_data = self.redis.hgetall(daily_key)

            if daily_data:
                day_requests = int(daily_data.get(b'total_requests', 0))
                day_processing_time = int(daily_data.get(b'total_processing_time', 0))

                analytics["total_requests"] += day_requests
                analytics["daily_usage"].append({
                    "date": datetime.fromtimestamp(day_timestamp).strftime('%Y-%m-%d'),
                    "requests": day_requests,
                    "processing_time": day_processing_time
                })

        # Calculate averages
        if analytics["total_requests"] > 0:
            total_processing_time = sum(day["processing_time"] for day in analytics["daily_usage"])
            analytics["avg_processing_time"] = total_processing_time / analytics["total_requests"]

        return analytics

    async def health_check(self) -> Dict[str, Any]:
        """Get service health metrics"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "performance_metrics": self.performance_metrics,
            "redis_status": "connected" if self.redis.ping() else "disconnected",
            "active_models": len(self.model_registry.global_models),
            "cache_hit_rate": (
                self.performance_metrics["cache_hits"] /
                max(1, self.performance_metrics["total_requests"])
            )
        }

# Example usage and integration
async def example_integration():
    """Example of how to integrate existing ML components"""

    # Initialize orchestrator
    orchestrator = MLServiceOrchestrator()

    # Register existing ML models (simplified examples)
    class MockXGBoostEnsemble:
        def predict(self, X):
            return np.random.random(X.shape[0])

        def predict_proba(self, X):
            return np.random.random((X.shape[0], 2))

    class MockMarketRegimeClassifier:
        def predict(self, X):
            return np.random.randint(0, 12, X.shape[0])

    # Register models
    await orchestrator.model_registry.register_global_model(
        ModelType.XGBOOST_ENSEMBLE,
        MockXGBoostEnsemble(),
        "1.0",
        {"accuracy": 0.72, "training_date": "2024-01-15"}
    )

    await orchestrator.model_registry.register_global_model(
        ModelType.MARKET_REGIME_CLASSIFIER,
        MockMarketRegimeClassifier(),
        "1.0",
        {"accuracy": 0.68, "regimes": 12}
    )

    # Create test user
    user_context = UserContext(
        user_id="user_123",
        tenant_id="tenant_456",
        subscription_tier=SubscriptionTier.PROFESSIONAL,
        api_key="api_key_789",
        tier_limits=TIER_CONFIGURATIONS[SubscriptionTier.PROFESSIONAL]
    )

    # Create prediction request
    request = PredictionRequest(
        request_id=str(uuid.uuid4()),
        user_context=user_context,
        model_type=ModelType.XGBOOST_ENSEMBLE,
        input_data={
            "feature_1": 0.5,
            "feature_2": -0.2,
            "feature_3": 1.1,
            "feature_4": 0.0,
            "feature_5": 0.8
        },
        timestamp=datetime.now()
    )

    # Process request
    response = await orchestrator.process_prediction_request(request)

    print(f"Prediction: {response.prediction}")
    print(f"Confidence: {response.confidence}")
    print(f"Processing time: {response.processing_time_ms:.2f}ms")
    print(f"Cost units: {response.billing_info['cost_units']:.4f}")

    # Get health check
    health = await orchestrator.health_check()
    print(f"Service health: {health}")

    return orchestrator

if __name__ == "__main__":
    asyncio.run(example_integration())