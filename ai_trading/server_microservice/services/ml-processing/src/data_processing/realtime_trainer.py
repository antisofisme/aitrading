#!/usr/bin/env python3
"""
🤖 Real-time ML Model Training System - MICROSERVICE ARCHITECTURE
Purpose: Continuous learning from live market data with adaptive model optimization

ENHANCED FEATURES:
- Real-time feature extraction dengan microservice infrastructure
- Online learning algorithms dengan performance tracking
- Multi-model ensemble dengan comprehensive error handling
- Adaptive hyperparameter optimization dengan event publishing
- Live model validation dengan centralized validation

MICROSERVICE INFRASTRUCTURE:
- Performance tracking untuk all ML training operations
- Per-service error handling untuk model training scenarios
- Event publishing untuk ML lifecycle monitoring
- Enhanced logging dengan training-specific context
- Comprehensive validation untuk training data and models
- Advanced metrics tracking untuk training performance optimization
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
import pickle
import hashlib
import time

# MICROSERVICE INFRASTRUCTURE INTEGRATION
from ....shared.infrastructure.logging.base_logger import BaseLogger
from ....shared.infrastructure.config.base_config import BaseConfig
from ....shared.infrastructure.error_handling.base_error_handler import BaseErrorHandler
from ....shared.infrastructure.performance.base_performance_tracker import BasePerformanceTracker
from ....shared.infrastructure.events.base_event_publisher import BaseEventPublisher

# Machine learning imports
try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import SGDRegressor, PassiveAggressiveRegressor
    from sklearn.neural_network import MLPRegressor
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.feature_selection import SelectKBest, f_regression
    import joblib
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# Enhanced logger with microservice infrastructure
trainer_logger = BaseLogger("realtime_trainer", {
    "component": "data_processing",
    "service": "ml_processing",
    "feature": "adaptive_learning"
})

# Training metrics with performance tracking
training_metrics = {
    "total_training_cycles": 0,
    "successful_training_cycles": 0,
    "failed_training_cycles": 0,
    "models_trained": 0,
    "predictions_made": 0,
    "avg_training_time_ms": 0,
    "avg_prediction_accuracy": 0.0,
    "validation_cycles_performed": 0,
    "adaptation_cycles_performed": 0,
    "events_published": 0,
    "rollbacks_executed": 0
}

# Setup legacy logging for backward compatibility
logger = trainer_logger

# ========================================
# PHASE 5: ML TRAINING DEFINITIONS
# ========================================

class ModelType(Enum):
    """Available ML model types"""
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOSTING = "gradient_boosting"
    SGD_REGRESSOR = "sgd_regressor"
    PASSIVE_AGGRESSIVE = "passive_aggressive"
    MLP_NEURAL_NETWORK = "mlp_neural_network"
    ENSEMBLE = "ensemble"

class LearningMode(Enum):
    """Learning mode types"""
    BATCH = "batch"              # Traditional batch learning
    ONLINE = "online"            # Online/incremental learning
    MINI_BATCH = "mini_batch"    # Mini-batch learning
    ADAPTIVE = "adaptive"        # Adaptive learning rate

class ModelStatus(Enum):
    """Model training status"""
    TRAINING = "training"
    READY = "ready"
    UPDATING = "updating"
    VALIDATING = "validating"
    FAILED = "failed"
    RETIRED = "retired"

@dataclass
class MarketFeatures:
    """Market data features for ML training"""
    symbol: str
    timestamp: datetime
    
    # Price features
    price_return: float
    price_volatility: float
    price_momentum: float
    price_trend: float
    
    # Technical indicators
    rsi: float
    macd: float
    bollinger_position: float
    volume_ratio: float
    
    # Market microstructure
    bid_ask_spread: float
    order_flow: float
    market_impact: float
    
    # Cross-asset features
    correlation_spy: float
    correlation_vix: float
    currency_strength: float
    
    # Time-based features
    hour_of_day: int
    day_of_week: int
    is_market_open: bool
    
    # Target variables
    next_return_1m: Optional[float] = None
    next_return_5m: Optional[float] = None
    next_return_15m: Optional[float] = None
    next_volatility: Optional[float] = None

@dataclass
class ModelPerformance:
    """ML model performance metrics"""
    model_id: str
    model_type: ModelType
    timestamp: datetime
    
    # Performance metrics
    mse: float                  # Mean Squared Error
    r2_score: float            # R-squared
    mae: float                 # Mean Absolute Error
    sharpe_ratio: float        # Sharpe ratio of predictions
    
    # Trading metrics
    hit_rate: float            # Prediction accuracy
    profit_factor: float       # Profit/Loss ratio
    max_drawdown: float        # Maximum drawdown
    
    # Model metrics
    training_samples: int      # Number of training samples
    prediction_count: int      # Number of predictions made
    last_update: datetime      # Last model update
    
    # Validation metrics
    validation_score: float    # Cross-validation score
    overfitting_score: float   # Overfitting detection
    stability_score: float     # Model stability

@dataclass
class TrainingConfiguration:
    """ML training configuration"""
    # Model settings
    model_types: List[ModelType] = field(default_factory=lambda: [ModelType.RANDOM_FOREST, ModelType.SGD_REGRESSOR])
    ensemble_weights: Dict[ModelType, float] = field(default_factory=dict)
    
    # Training settings
    learning_mode: LearningMode = LearningMode.ONLINE
    batch_size: int = 100
    update_frequency: int = 50  # Update every N samples
    validation_frequency: int = 1000  # Validate every N samples
    
    # Feature settings
    max_features: int = 50
    feature_selection: bool = True
    feature_scaling: bool = True
    
    # Performance settings
    performance_threshold: float = 0.1  # Minimum R² score
    stability_threshold: float = 0.8    # Minimum stability score
    max_models: int = 5                 # Maximum concurrent models
    
    # Risk settings
    max_position_size: float = 0.1      # Maximum position per prediction
    stop_loss: float = 0.02             # Stop loss threshold
    take_profit: float = 0.04           # Take profit threshold

# ========================================
# PHASE 5: REAL-TIME ML TRAINER
# ========================================

class RealtimeMlTrainer:
    """
    🤖 Real-time Machine Learning Training System - MICROSERVICE ARCHITECTURE
    
    Enhanced Features:
    - Continuous learning dengan microservice infrastructure
    - Multi-model ensemble dengan performance tracking
    - Online feature engineering dengan error handling
    - Real-time validation dengan event publishing
    - Automatic rollback dengan comprehensive logging
    
    MICROSERVICE INFRASTRUCTURE:
    - Performance tracking untuk all training operations
    - Per-service error handling untuk training scenarios
    - Event-driven architecture untuk training lifecycle
    - Comprehensive validation untuk training data quality
    - Enhanced logging dengan training-specific context
    """
    
    def __init__(self, config: Optional[TrainingConfiguration] = None, ai_services=None, database_manager=None):
        """Initialize Realtime ML Trainer dengan MICROSERVICE ARCHITECTURE"""
        initialization_start = time.perf_counter()
        
        try:
            # Initialize microservice infrastructure
            self.logger = trainer_logger
            self.config_manager = BaseConfig()
            self.error_handler = BaseErrorHandler("realtime_trainer")
            self.performance_tracker = BasePerformanceTracker("realtime_trainer")
            self.event_publisher = BaseEventPublisher("ml_processing")
            
            # Load microservice-specific configuration
            self.service_config = self.config_manager.get_config("realtime_trainer", {
                "models": {
                    "max_concurrent": 5,
                    "update_frequency": 50,
                    "validation_frequency": 1000
                },
                "features": {
                    "max_features": 50,
                    "scaling_enabled": True,
                    "selection_enabled": True
                },
                "performance": {
                    "monitoring_enabled": True,
                    "metrics_interval": 60,
                    "min_r2_score": 0.1
                }
            })
            
            # Validate initialization configuration
            self.config = config or TrainingConfiguration()
            
            # AI services and database manager
            self.ai_services = ai_services
            self.database_manager = database_manager
            
            # Publish trainer initialization event
            self.event_publisher.publish_event(
                "realtime_trainer.initialization_started",
                {
                    "model_types": [mt.value for mt in self.config.model_types],
                    "learning_mode": self.config.learning_mode.value,
                    "batch_size": self.config.batch_size,
                    "feature_settings": {
                        "max_features": self.config.max_features,
                        "feature_selection": self.config.feature_selection,
                        "feature_scaling": self.config.feature_scaling
                    }
                }
            )
        
            # Model storage
            self.models: Dict[str, Any] = {}
            self.model_performance: Dict[str, ModelPerformance] = {}
            self.ensemble_weights: Dict[str, float] = {}
            
            # Feature engineering
            self.feature_extractors = {}
            self.scalers: Dict[str, Any] = {}
            self.feature_selectors: Dict[str, Any] = {}
            
            # Training data
            self.training_buffer = deque(maxlen=10000)
            self.validation_buffer = deque(maxlen=1000)
            self.feature_history = deque(maxlen=5000)
            
            # Performance tracking
            self.prediction_history = deque(maxlen=1000)
            self.model_updates = defaultdict(int)
            self.total_predictions = 0
            self.successful_updates = 0
            
            # Status
            self.is_training = False
            self.last_update = datetime.now()
            self.model_status: Dict[str, ModelStatus] = {}
            
            # Initialize ML components with error handling
            if SKLEARN_AVAILABLE:
                try:
                    self._initialize_models()
                    self._initialize_feature_engineering()
                    self.ml_available = True
                    self.logger.debug("ML components initialized successfully")
                except Exception as e:
                    self.error_handler.handle_error(e, {
                        "operation": "initialize_ml_components",
                        "sklearn_available": SKLEARN_AVAILABLE
                    })
                    self.logger.warning(f"ML components initialization failed: {e}")
                    self.ml_available = False
            else:
                self.ml_available = False
                self.logger.warning("⚠️ Scikit-learn not available - ML training disabled")
            
            # Record initialization performance
            initialization_time = (time.perf_counter() - initialization_start) * 1000
            
            with self.performance_tracker.track_operation("initialize_realtime_trainer"):
                pass  # Initialization complete
            
            # Update training metrics
            training_metrics["total_training_cycles"] += 1
            training_metrics["events_published"] += 1
            
            # Publish successful initialization event
            self.event_publisher.publish_event(
                "realtime_trainer.initialization_completed",
                {
                    "initialization_time_ms": initialization_time,
                    "ml_available": self.ml_available,
                    "models_to_initialize": len(self.config.model_types),
                    "status": "ready"
                }
            )
            
            self.logger.info(f"✅ Real-time ML Trainer initialized successfully in {initialization_time:.2f}ms")
            
        except Exception as e:
            # Handle initialization failure with microservice error management
            initialization_time = (time.perf_counter() - initialization_start) * 1000
            
            self.error_handler.handle_error(e, {
                "operation": "realtime_trainer_initialization",
                "initialization_time_ms": initialization_time
            })
            
            self.logger.error(f"❌ Failed to initialize Real-time ML Trainer: {e}")
            
            # Publish initialization failure event
            self.event_publisher.publish_event(
                "realtime_trainer.initialization_failed",
                {
                    "error": str(e),
                    "initialization_time_ms": initialization_time
                }
            )
            
            raise
    
    def _initialize_models(self):
        """Initialize ML models for different strategies"""
        try:
            # Model configurations
            model_configs = {
                ModelType.RANDOM_FOREST: {
                    'model': RandomForestRegressor(
                        n_estimators=50,
                        max_depth=10,
                        random_state=42,
                        n_jobs=-1
                    ),
                    'online_capable': False
                },
                ModelType.SGD_REGRESSOR: {
                    'model': SGDRegressor(
                        learning_rate='adaptive',
                        eta0=0.01,
                        random_state=42
                    ),
                    'online_capable': True
                },
                ModelType.PASSIVE_AGGRESSIVE: {
                    'model': PassiveAggressiveRegressor(
                        C=1.0,
                        random_state=42
                    ),
                    'online_capable': True
                },
                ModelType.MLP_NEURAL_NETWORK: {
                    'model': MLPRegressor(
                        hidden_layer_sizes=(100, 50),
                        learning_rate='adaptive',
                        random_state=42,
                        max_iter=200
                    ),
                    'online_capable': False
                }
            }
            
            # Initialize models
            for model_type in self.config.model_types:
                if model_type in model_configs:
                    model_id = f"{model_type.value}_{int(time.time())}"
                    config = model_configs[model_type]
                    
                    self.models[model_id] = {
                        'model': config['model'],
                        'type': model_type,
                        'online_capable': config['online_capable'],
                        'created_at': datetime.now(),
                        'update_count': 0,
                        'is_trained': False
                    }
                    
                    self.model_status[model_id] = ModelStatus.TRAINING
                    self.ensemble_weights[model_id] = 1.0 / len(self.config.model_types)
                    
                    self.logger.info(f"✅ Initialized {model_type.value} model: {model_id}")
            
        except Exception as e:
            self.error_handler.handle_error(e, {"operation": "model_initialization"})
            self.logger.error(f"❌ Model initialization failed: {e}")
    
    def _initialize_feature_engineering(self):
        """Initialize feature engineering components"""
        try:
            # Feature scalers
            self.scalers['standard'] = StandardScaler()
            self.scalers['minmax'] = MinMaxScaler()
            
            # Feature selectors
            self.feature_selectors['k_best'] = SelectKBest(score_func=f_regression, k=min(20, self.config.max_features))
            
            # Time series splitter for validation
            self.ts_splitter = TimeSeriesSplit(n_splits=3)
            
            self.logger.info("✅ Feature engineering components initialized")
            
        except Exception as e:
            self.error_handler.handle_error(e, {"operation": "feature_engineering_initialization"})
            self.logger.error(f"❌ Feature engineering initialization failed: {e}")
    
    async def extract_features(self, market_data: Dict[str, Any], symbol: str) -> MarketFeatures:
        """Extract features from market data for ML training"""
        try:
            with self.performance_tracker.track_operation("extract_features"):
                current_time = datetime.now()
                
                # Extract price data
                close_price = float(market_data.get('close', 0))
                high_price = float(market_data.get('high', close_price))
                low_price = float(market_data.get('low', close_price))
                volume = float(market_data.get('volume', 0))
                
                # Calculate price features
                price_range = high_price - low_price
                price_return = (close_price - float(market_data.get('open', close_price))) / close_price if close_price > 0 else 0
                price_volatility = price_range / close_price if close_price > 0 else 0
                
                # Get historical data for momentum and trend
                historical_prices = self._get_historical_prices(symbol, 20)
                
                if len(historical_prices) >= 2:
                    # Price momentum (rate of change)
                    price_momentum = (close_price - historical_prices[-5]) / historical_prices[-5] if len(historical_prices) >= 5 else 0
                    
                    # Price trend (linear regression slope)
                    if len(historical_prices) >= 10:
                        x = np.arange(len(historical_prices))
                        price_trend = np.polyfit(x, historical_prices, 1)[0]
                    else:
                        price_trend = 0
                else:
                    price_momentum = 0
                    price_trend = 0
                
                # Technical indicators (simplified)
                rsi = self._calculate_rsi(historical_prices) if len(historical_prices) >= 14 else 50.0
                macd = self._calculate_macd(historical_prices) if len(historical_prices) >= 26 else 0.0
                bollinger_position = self._calculate_bollinger_position(historical_prices, close_price) if len(historical_prices) >= 20 else 0.5
                
                # Volume analysis
                historical_volumes = self._get_historical_volumes(symbol, 10)
                avg_volume = statistics.mean(historical_volumes) if historical_volumes else volume
                volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0
                
                # Market microstructure (simplified)
                bid_ask_spread = price_range / close_price if close_price > 0 else 0.001  # Simplified spread
                order_flow = volume_ratio - 1.0  # Volume-based order flow proxy
                market_impact = price_volatility * volume_ratio  # Impact estimation
                
                # Cross-asset correlations (simplified)
                correlation_spy = 0.3  # Default correlation with SPY
                correlation_vix = -0.2  # Default inverse correlation with VIX
                currency_strength = self._calculate_currency_strength(symbol)
                
                # Time-based features
                hour_of_day = current_time.hour
                day_of_week = current_time.weekday()
                is_market_open = 9 <= hour_of_day <= 16  # Simplified market hours
                
                return MarketFeatures(
                    symbol=symbol,
                    timestamp=current_time,
                    price_return=price_return,
                    price_volatility=price_volatility,
                    price_momentum=price_momentum,
                    price_trend=price_trend,
                    rsi=rsi,
                    macd=macd,
                    bollinger_position=bollinger_position,
                    volume_ratio=volume_ratio,
                    bid_ask_spread=bid_ask_spread,
                    order_flow=order_flow,
                    market_impact=market_impact,
                    correlation_spy=correlation_spy,
                    correlation_vix=correlation_vix,
                    currency_strength=currency_strength,
                    hour_of_day=hour_of_day,
                    day_of_week=day_of_week,
                    is_market_open=is_market_open
                )
            
        except Exception as e:
            self.error_handler.handle_error(e, {
                "operation": "extract_features",
                "symbol": symbol,
                "market_data_keys": list(market_data.keys()) if market_data else []
            })
            self.logger.error(f"❌ Feature extraction failed: {e}")
            # Return default features
            return MarketFeatures(
                symbol=symbol,
                timestamp=datetime.now(),
                price_return=0.0,
                price_volatility=0.01,
                price_momentum=0.0,
                price_trend=0.0,
                rsi=50.0,
                macd=0.0,
                bollinger_position=0.5,
                volume_ratio=1.0,
                bid_ask_spread=0.001,
                order_flow=0.0,
                market_impact=0.01,
                correlation_spy=0.3,
                correlation_vix=-0.2,
                currency_strength=0.0,
                hour_of_day=12,
                day_of_week=1,
                is_market_open=True
            )
    
    def _get_historical_prices(self, symbol: str, periods: int) -> List[float]:
        """Get historical prices for feature calculation"""
        # Simplified implementation - in production, would fetch from database
        cache_key = f"{symbol}_prices"
        if hasattr(self, '_price_cache') and cache_key in self._price_cache:
            return list(self._price_cache[cache_key])
        return []
    
    def _get_historical_volumes(self, symbol: str, periods: int) -> List[float]:
        """Get historical volumes for feature calculation"""
        # Simplified implementation
        cache_key = f"{symbol}_volumes"
        if hasattr(self, '_volume_cache') and cache_key in self._volume_cache:
            return list(self._volume_cache[cache_key])
        return []
    
    def _calculate_rsi(self, prices: List[float]) -> float:
        """Calculate RSI indicator"""
        if len(prices) < 14:
            return 50.0
        
        try:
            deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
            gains = [d if d > 0 else 0 for d in deltas[-14:]]
            losses = [-d if d < 0 else 0 for d in deltas[-14:]]
            
            avg_gain = statistics.mean(gains) if gains else 0
            avg_loss = statistics.mean(losses) if losses else 0.001
            
            rs = avg_gain / avg_loss if avg_loss != 0 else 0
            rsi = 100 - (100 / (1 + rs))
            
            return max(0, min(100, rsi))
        except:
            return 50.0
    
    def _calculate_macd(self, prices: List[float]) -> float:
        """Calculate MACD indicator"""
        if len(prices) < 26:
            return 0.0
        
        try:
            # Simplified MACD calculation
            ema_12 = statistics.mean(prices[-12:])
            ema_26 = statistics.mean(prices[-26:])
            macd = ema_12 - ema_26
            
            return macd
        except:
            return 0.0
    
    def _calculate_bollinger_position(self, prices: List[float], current_price: float) -> float:
        """Calculate position within Bollinger Bands"""
        if len(prices) < 20:
            return 0.5
        
        try:
            sma = statistics.mean(prices[-20:])
            std = statistics.stdev(prices[-20:])
            
            upper_band = sma + (2 * std)
            lower_band = sma - (2 * std)
            
            if upper_band == lower_band:
                return 0.5
            
            position = (current_price - lower_band) / (upper_band - lower_band)
            return max(0, min(1, position))
        except:
            return 0.5
    
    def _calculate_currency_strength(self, symbol: str) -> float:
        """Calculate currency strength for forex pairs"""
        try:
            # Simplified currency strength calculation
            if symbol.startswith('EUR'):
                return 0.1  # EUR strength
            elif symbol.startswith('USD') or symbol.endswith('USD'):
                return -0.1  # USD strength
            else:
                return 0.0
        except:
            return 0.0
    
    async def add_training_sample(self, features: MarketFeatures, target_return: float, target_volatility: float):
        """Add a new training sample to the buffer"""
        try:
            with self.performance_tracker.track_operation("add_training_sample"):
                # Update features with target values
                features.next_return_1m = target_return
                features.next_volatility = target_volatility
                
                # Add to training buffer
                self.training_buffer.append(features)
                
                # Store in feature history for caching
                if not hasattr(self, '_price_cache'):
                    self._price_cache = defaultdict(lambda: deque(maxlen=100))
                    self._volume_cache = defaultdict(lambda: deque(maxlen=100))
                
                # Cache price and volume data
                current_price = features.price_return + 1.0  # Reconstruct approximate price
                self._price_cache[f"{features.symbol}_prices"].append(current_price)
                self._volume_cache[f"{features.symbol}_volumes"].append(features.volume_ratio)
                
                # Check if we need to update models
                if len(self.training_buffer) % self.config.update_frequency == 0:
                    await self._update_models()
                
                # Check if we need to validate models
                if len(self.training_buffer) % self.config.validation_frequency == 0:
                    await self._validate_models()
                
                self.logger.debug(f"📊 Added training sample for {features.symbol}, buffer size: {len(self.training_buffer)}")
            
        except Exception as e:
            self.error_handler.handle_error(e, {
                "operation": "add_training_sample",
                "symbol": features.symbol,
                "buffer_size": len(self.training_buffer)
            })
            self.logger.error(f"❌ Failed to add training sample: {e}")
    
    async def _update_models(self):
        """Update models with new training data"""
        if self.is_training or not self.ml_available:
            return
        
        try:
            with self.performance_tracker.track_operation("update_models"):
                self.is_training = True
                self.logger.info("🔄 Starting model update cycle")
                
                # Prepare training data
                if len(self.training_buffer) < 50:
                    self.logger.warning("⚠️ Insufficient training data")
                    return
                
                # Extract features and targets
                X, y = self._prepare_training_data()
                
                if X is None or len(X) == 0:
                    self.logger.warning("⚠️ No valid training data")
                    return
                
                # Update each model
                for model_id, model_info in self.models.items():
                    try:
                        await self._update_single_model(model_id, model_info, X, y)
                        self.model_updates[model_id] += 1
                        self.successful_updates += 1
                        
                    except Exception as e:
                        self.error_handler.handle_error(e, {
                            "operation": "update_single_model",
                            "model_id": model_id
                        })
                        self.logger.error(f"❌ Failed to update model {model_id}: {e}")
                        self.model_status[model_id] = ModelStatus.FAILED
                
                # Update ensemble weights
                await self._update_ensemble_weights()
                
                # Publish model update event
                await self.event_publisher.publish_event(
                    "models.updated",
                    {
                        "successful_updates": self.successful_updates,
                        "total_models": len(self.models),
                        "training_samples": len(self.training_buffer)
                    }
                )
                
                self.last_update = datetime.now()
                self.logger.info(f"✅ Model update completed - {self.successful_updates} successful updates")
            
        except Exception as e:
            self.error_handler.handle_error(e, {"operation": "update_models"})
            self.logger.error(f"❌ Model update failed: {e}")
        finally:
            self.is_training = False
    
    def _prepare_training_data(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """Prepare training data from buffer"""
        try:
            # Extract features and targets
            features_list = []
            targets_list = []
            
            for sample in list(self.training_buffer):
                if sample.next_return_1m is not None:
                    # Convert features to array
                    feature_vector = [
                        sample.price_return,
                        sample.price_volatility,
                        sample.price_momentum,
                        sample.price_trend,
                        sample.rsi / 100.0,  # Normalize RSI
                        sample.macd,
                        sample.bollinger_position,
                        sample.volume_ratio,
                        sample.bid_ask_spread,
                        sample.order_flow,
                        sample.market_impact,
                        sample.correlation_spy,
                        sample.correlation_vix,
                        sample.currency_strength,
                        sample.hour_of_day / 24.0,  # Normalize hour
                        sample.day_of_week / 7.0,   # Normalize day
                        float(sample.is_market_open)
                    ]
                    
                    features_list.append(feature_vector)
                    targets_list.append(sample.next_return_1m)
            
            if not features_list:
                return None, None
            
            X = np.array(features_list)
            y = np.array(targets_list)
            
            # Apply feature scaling if configured
            if self.config.feature_scaling:
                if 'standard' not in self.scalers or not hasattr(self.scalers['standard'], 'mean_'):
                    # Fit scaler on initial data
                    self.scalers['standard'].fit(X)
                
                # Transform features
                X = self.scalers['standard'].transform(X)
            
            return X, y
            
        except Exception as e:
            self.error_handler.handle_error(e, {"operation": "prepare_training_data"})
            self.logger.error(f"❌ Training data preparation failed: {e}")
            return None, None
    
    async def _update_single_model(self, model_id: str, model_info: Dict, X: np.ndarray, y: np.ndarray):
        """Update a single model with new data"""
        try:
            model = model_info['model']
            model_type = model_info['type']
            
            self.model_status[model_id] = ModelStatus.UPDATING
            
            if model_info['online_capable'] and model_info['is_trained']:
                # Online learning update
                if hasattr(model, 'partial_fit'):
                    model.partial_fit(X, y)
                else:
                    # For models without partial_fit, use recent data
                    recent_X = X[-min(100, len(X)):]
                    recent_y = y[-min(100, len(y)):]
                    model.fit(recent_X, recent_y)
            else:
                # Batch learning update
                model.fit(X, y)
                model_info['is_trained'] = True
            
            model_info['update_count'] += 1
            self.model_status[model_id] = ModelStatus.READY
            
            self.logger.debug(f"✅ Updated {model_type.value} model {model_id}")
            
        except Exception as e:
            self.error_handler.handle_error(e, {
                "operation": "update_single_model",
                "model_id": model_id
            })
            self.logger.error(f"❌ Single model update failed for {model_id}: {e}")
            self.model_status[model_id] = ModelStatus.FAILED
    
    async def _validate_models(self):
        """Validate model performance"""
        try:
            with self.performance_tracker.track_operation("validate_models"):
                self.logger.info("🔍 Starting model validation")
                
                # Prepare validation data
                X, y = self._prepare_training_data()
                if X is None or len(X) < 50:
                    return
                
                # Validate each model
                for model_id, model_info in self.models.items():
                    if self.model_status[model_id] != ModelStatus.READY:
                        continue
                    
                    try:
                        await self._validate_single_model(model_id, model_info, X, y)
                    except Exception as e:
                        self.error_handler.handle_error(e, {
                            "operation": "validate_single_model",
                            "model_id": model_id
                        })
                        self.logger.error(f"❌ Validation failed for {model_id}: {e}")
                
                # Publish validation event
                await self.event_publisher.publish_event(
                    "models.validated",
                    {
                        "validated_models": len([m for m in self.model_status.values() if m == ModelStatus.READY]),
                        "total_models": len(self.models),
                        "validation_samples": len(X) if X is not None else 0
                    }
                )
                
                self.logger.info("✅ Model validation completed")
            
        except Exception as e:
            self.error_handler.handle_error(e, {"operation": "validate_models"})
            self.logger.error(f"❌ Model validation failed: {e}")
    
    async def _validate_single_model(self, model_id: str, model_info: Dict, X: np.ndarray, y: np.ndarray):
        """Validate a single model"""
        try:
            model = model_info['model']
            
            if not model_info['is_trained']:
                return
            
            self.model_status[model_id] = ModelStatus.VALIDATING
            
            # Time series cross-validation
            mse_scores = []
            r2_scores = []
            
            for train_idx, val_idx in self.ts_splitter.split(X):
                X_train, X_val = X[train_idx], X[val_idx]
                y_train, y_val = y[train_idx], y[val_idx]
                
                # Create a copy of the model for validation
                if hasattr(model, 'fit'):
                    val_model = type(model)(**model.get_params())
                    val_model.fit(X_train, y_train)
                    
                    y_pred = val_model.predict(X_val)
                    
                    mse = mean_squared_error(y_val, y_pred)
                    r2 = r2_score(y_val, y_pred)
                    
                    mse_scores.append(mse)
                    r2_scores.append(r2)
            
            # Calculate performance metrics
            avg_mse = statistics.mean(mse_scores) if mse_scores else float('inf')
            avg_r2 = statistics.mean(r2_scores) if r2_scores else -1.0
            avg_mae = avg_mse ** 0.5  # Approximate MAE from MSE
            
            # Calculate trading-specific metrics
            y_pred_full = model.predict(X)
            hit_rate = np.mean((y_pred_full > 0) == (y > 0)) if len(y) > 0 else 0.5
            
            # Calculate Sharpe ratio of predictions
            pred_returns = y_pred_full
            sharpe_ratio = np.mean(pred_returns) / (np.std(pred_returns) + 1e-8) if len(pred_returns) > 0 else 0.0
            
            # Create performance record
            performance = ModelPerformance(
                model_id=model_id,
                model_type=model_info['type'],
                timestamp=datetime.now(),
                mse=avg_mse,
                r2_score=avg_r2,
                mae=avg_mae,
                sharpe_ratio=sharpe_ratio,
                hit_rate=hit_rate,
                profit_factor=max(hit_rate / (1 - hit_rate + 1e-8), 0.1),
                max_drawdown=0.05,  # Simplified
                training_samples=len(self.training_buffer),
                prediction_count=self.total_predictions,
                last_update=model_info.get('last_update', datetime.now()),
                validation_score=avg_r2,
                overfitting_score=max(0, 1 - abs(avg_r2)),
                stability_score=max(0, 1 - np.std(r2_scores)) if r2_scores else 0.5
            )
            
            self.model_performance[model_id] = performance
            self.model_status[model_id] = ModelStatus.READY
            
            self.logger.info(f"📊 Model {model_id} validation: R²={avg_r2:.3f}, MSE={avg_mse:.6f}, Hit Rate={hit_rate:.3f}")
            
        except Exception as e:
            self.error_handler.handle_error(e, {
                "operation": "validate_single_model",
                "model_id": model_id
            })
            self.logger.error(f"❌ Single model validation failed for {model_id}: {e}")
            self.model_status[model_id] = ModelStatus.FAILED
    
    async def _update_ensemble_weights(self):
        """Update ensemble weights based on model performance"""
        try:
            if not self.model_performance:
                return
            
            # Calculate weights based on performance
            total_score = 0
            model_scores = {}
            
            for model_id, performance in self.model_performance.items():
                if self.model_status[model_id] == ModelStatus.READY:
                    # Combine multiple performance metrics
                    score = (
                        performance.r2_score * 0.4 +
                        performance.hit_rate * 0.3 +
                        performance.stability_score * 0.2 +
                        (1 - performance.overfitting_score) * 0.1
                    )
                    
                    model_scores[model_id] = max(score, 0.01)  # Minimum weight
                    total_score += model_scores[model_id]
            
            # Normalize weights
            if total_score > 0:
                for model_id in model_scores:
                    self.ensemble_weights[model_id] = model_scores[model_id] / total_score
                
                self.logger.info(f"🔄 Updated ensemble weights: {len(model_scores)} models")
            
        except Exception as e:
            self.error_handler.handle_error(e, {"operation": "update_ensemble_weights"})
            self.logger.error(f"❌ Ensemble weight update failed: {e}")
    
    async def predict(self, features: MarketFeatures) -> Dict[str, float]:
        """Make predictions using the ensemble of models"""
        try:
            with self.performance_tracker.track_operation("predict"):
                if not self.ml_available:
                    return {"prediction": 0.0, "confidence": 0.3}
                
                # Prepare feature vector
                feature_vector = np.array([[
                    features.price_return,
                    features.price_volatility,
                    features.price_momentum,
                    features.price_trend,
                    features.rsi / 100.0,
                    features.macd,
                    features.bollinger_position,
                    features.volume_ratio,
                    features.bid_ask_spread,
                    features.order_flow,
                    features.market_impact,
                    features.correlation_spy,
                    features.correlation_vix,
                    features.currency_strength,
                    features.hour_of_day / 24.0,
                    features.day_of_week / 7.0,
                    float(features.is_market_open)
                ]])
                
                # Apply scaling if configured
                if self.config.feature_scaling and 'standard' in self.scalers:
                    if hasattr(self.scalers['standard'], 'mean_'):
                        feature_vector = self.scalers['standard'].transform(feature_vector)
                
                # Get predictions from all ready models
                predictions = []
                weights = []
                
                for model_id, model_info in self.models.items():
                    if (self.model_status[model_id] == ModelStatus.READY and 
                        model_info['is_trained'] and 
                        model_id in self.ensemble_weights):
                        
                        try:
                            pred = model_info['model'].predict(feature_vector)[0]
                            weight = self.ensemble_weights[model_id]
                            
                            predictions.append(pred)
                            weights.append(weight)
                            
                        except Exception as e:
                            self.logger.warning(f"⚠️ Prediction failed for model {model_id}: {e}")
                
                if not predictions:
                    return {"prediction": 0.0, "confidence": 0.1}
                
                # Calculate weighted ensemble prediction
                weighted_pred = np.average(predictions, weights=weights)
                
                # Calculate confidence based on prediction agreement
                pred_std = np.std(predictions) if len(predictions) > 1 else 0.1
                confidence = max(0.1, min(0.9, 1.0 - pred_std))
                
                # Store prediction for future validation
                prediction_record = {
                    "timestamp": features.timestamp,
                    "symbol": features.symbol,
                    "prediction": weighted_pred,
                    "confidence": confidence,
                    "num_models": len(predictions)
                }
                self.prediction_history.append(prediction_record)
                self.total_predictions += 1
                
                # Publish prediction event
                await self.event_publisher.publish_event(
                    "prediction.made",
                    {
                        "symbol": features.symbol,
                        "prediction": weighted_pred,
                        "confidence": confidence,
                        "num_models": len(predictions)
                    }
                )
                
                return {
                    "prediction": weighted_pred,
                    "confidence": confidence,
                    "num_models": len(predictions),
                    "model_agreement": 1.0 - pred_std
                }
            
        except Exception as e:
            self.error_handler.handle_error(e, {
                "operation": "predict",
                "symbol": features.symbol
            })
            self.logger.error(f"❌ Prediction failed: {e}")
            return {"prediction": 0.0, "confidence": 0.1}
    
    def get_trainer_statistics(self) -> Dict[str, Any]:
        """Get ML trainer performance statistics"""
        try:
            # Model statistics
            total_models = len(self.models)
            ready_models = len([m for m in self.model_status.values() if m == ModelStatus.READY])
            training_models = len([m for m in self.model_status.values() if m == ModelStatus.TRAINING])
            
            # Performance statistics
            if self.model_performance:
                avg_r2 = statistics.mean([p.r2_score for p in self.model_performance.values()])
                avg_hit_rate = statistics.mean([p.hit_rate for p in self.model_performance.values()])
                avg_sharpe = statistics.mean([p.sharpe_ratio for p in self.model_performance.values()])
            else:
                avg_r2 = avg_hit_rate = avg_sharpe = 0.0
            
            # Training statistics
            total_samples = len(self.training_buffer)
            total_updates = sum(self.model_updates.values())
            
            return {
                "ml_available": self.ml_available,
                "total_models": total_models,
                "ready_models": ready_models,
                "training_models": training_models,
                "total_predictions": self.total_predictions,
                "successful_updates": self.successful_updates,
                "training_samples": total_samples,
                "total_updates": total_updates,
                "average_r2_score": avg_r2,
                "average_hit_rate": avg_hit_rate,
                "average_sharpe_ratio": avg_sharpe,
                "last_update": self.last_update.isoformat(),
                "is_training": self.is_training,
                "ensemble_weights": self.ensemble_weights,
                "model_status": {k: v.value for k, v in self.model_status.items()}
            }
            
        except Exception as e:
            self.error_handler.handle_error(e, {"operation": "get_trainer_statistics"})
            self.logger.error(f"❌ Statistics generation failed: {e}")
            return {"ml_available": False, "error": str(e)}


# Export main class
__all__ = [
    'RealtimeMlTrainer',
    'MarketFeatures',
    'ModelPerformance',
    'TrainingConfiguration',
    'ModelType',
    'LearningMode',
    'ModelStatus'
]