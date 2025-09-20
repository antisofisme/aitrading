"""
🤖 ML Processing Settings - MICROSERVICE IMPLEMENTATION
Enterprise-grade configuration settings for ML Processing microservice

CENTRALIZED INFRASTRUCTURE:
- Performance tracking untuk configuration operations
- Centralized error handling untuk configuration validation
- Event publishing untuk configuration lifecycle monitoring
- Enhanced logging dengan configuration-specific context
- Comprehensive validation untuk configuration data
- Advanced metrics tracking untuk configuration performance optimization
"""

import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time

# CENTRALIZED INFRASTRUCTURE - VIA BASE MICROSERVICE
from ..business.base_microservice import MlProcessingBaseMicroservice

# Import centralized configuration manager
from ...shared.infrastructure.config_manager import get_config_manager

# ML Processing configuration metrics for microservice
ml_processing_config_metrics = {
    "total_configurations_loaded": 0,
    "successful_configurations": 0,
    "failed_configurations": 0,
    "configuration_validations": 0,
    "config_cache_hits": 0,
    "config_cache_misses": 0,
    "avg_config_load_time_ms": 0,
    "events_published": 0,
    "microservice_uptime": time.time(),
    "total_api_calls": 0
}


class MlProcessingModelType(Enum):
    """Machine learning model types for ML Processing microservice"""
    CATBOOST = "catboost"
    XGBOOST = "xgboost"
    LIGHTGBM = "lightgbm"
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOST = "gradient_boost"
    SVM = "svm"
    NEURAL_NETWORK = "neural_network"
    ENSEMBLE = "ensemble"


class MlProcessingLearningMode(Enum):
    """Learning modes for ML Processing microservice"""
    SUPERVISED = "supervised"
    UNSUPERVISED = "unsupervised"
    REINFORCEMENT = "reinforcement"
    SEMI_SUPERVISED = "semi_supervised"
    ONLINE = "online"
    BATCH = "batch"


class MlProcessingTrainingStrategy(Enum):
    """Training strategies for ML Processing microservice"""
    FULL_RETRAIN = "full_retrain"
    INCREMENTAL = "incremental"
    TRANSFER_LEARNING = "transfer_learning"
    FINE_TUNING = "fine_tuning"
    ENSEMBLE_UPDATE = "ensemble_update"


@dataclass
class MlProcessingModelEnsembleConfig:
    """Model ensemble configuration for ML Processing microservice"""
    # Ensemble settings
    ensemble_enabled: bool = field(default_factory=lambda: get_config_manager().get('models.ensemble.enabled', True))
    ensemble_size: int = field(default_factory=lambda: get_config_manager().get('model_ensemble.max_models', 5))
    
    # Individual model settings
    catboost_enabled: bool = field(default_factory=lambda: get_config_manager().get('models.catboost.enabled', True))
    catboost_iterations: int = field(default_factory=lambda: get_config_manager().get('models.catboost.iterations', 1000))
    catboost_learning_rate: float = field(default_factory=lambda: get_config_manager().get('models.catboost.learning_rate', 0.1))
    catboost_depth: int = field(default_factory=lambda: get_config_manager().get('models.catboost.depth', 6))
    
    xgboost_enabled: bool = field(default_factory=lambda: get_config_manager().get('models.xgboost.enabled', True))
    xgboost_n_estimators: int = field(default_factory=lambda: get_config_manager().get('models.xgboost.n_estimators', 100))
    xgboost_learning_rate: float = field(default_factory=lambda: get_config_manager().get('models.xgboost.learning_rate', 0.1))
    xgboost_max_depth: int = field(default_factory=lambda: get_config_manager().get('models.xgboost.max_depth', 6))
    
    lightgbm_enabled: bool = field(default_factory=lambda: get_config_manager().get('models.lightgbm.enabled', True))
    lightgbm_n_estimators: int = field(default_factory=lambda: get_config_manager().get('models.lightgbm.n_estimators', 100))
    lightgbm_learning_rate: float = field(default_factory=lambda: get_config_manager().get('models.lightgbm.learning_rate', 0.1))
    lightgbm_max_depth: int = field(default_factory=lambda: get_config_manager().get('models.lightgbm.max_depth', 6))
    
    random_forest_enabled: bool = field(default_factory=lambda: get_config_manager().get('models.random_forest.enabled', True))
    random_forest_n_estimators: int = field(default_factory=lambda: get_config_manager().get('models.random_forest.n_estimators', 100))
    random_forest_max_depth: int = field(default_factory=lambda: get_config_manager().get('models.random_forest.max_depth', 10))
    
    gradient_boost_enabled: bool = field(default_factory=lambda: get_config_manager().get('models.gradient_boost.enabled', True))
    gradient_boost_n_estimators: int = field(default_factory=lambda: get_config_manager().get('models.gradient_boost.n_estimators', 100))
    gradient_boost_learning_rate: float = field(default_factory=lambda: get_config_manager().get('models.gradient_boost.learning_rate', 0.1))
    
    # Ensemble aggregation
    aggregation_method: str = field(default_factory=lambda: get_config_manager().get('model_ensemble.voting_strategy', 'weighted_average'))
    confidence_weighting: bool = field(default_factory=lambda: get_config_manager().get('model_ensemble.confidence_weighting', True))
    dynamic_weights: bool = field(default_factory=lambda: get_config_manager().get('model_ensemble.dynamic_weights', True))
    
    # Performance-based weighting
    performance_weighting: bool = field(default_factory=lambda: get_config_manager().get('model_ensemble.performance_weighting', True))
    performance_window: int = field(default_factory=lambda: get_config_manager().get('model_ensemble.performance_window', 100))
    min_performance_threshold: float = field(default_factory=lambda: get_config_manager().get('model_ensemble.performance_threshold', 0.6))
    
    # Model selection
    adaptive_model_selection: bool = field(default_factory=lambda: get_config_manager().get('model_ensemble.adaptive_selection', True))
    model_selection_criteria: str = field(default_factory=lambda: get_config_manager().get('model_ensemble.selection_criteria', 'accuracy'))
    
    # Fallback handling
    fallback_enabled: bool = field(default_factory=lambda: get_config_manager().get('model_ensemble.fallback_enabled', True))
    fallback_model: str = field(default_factory=lambda: get_config_manager().get('model_ensemble.fallback_model', 'random_forest'))
    
    # Enhanced tracking for microservice
    microservice_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize config with microservice centralization"""
        self.microservice_metadata.update({
            "creation_method": "ensemble_config_microservice",
            "microservice": "ml-processing",
            "centralized_infrastructure": True,
            "config_timestamp": time.time(),
            "environment": "microservice"
        })


@dataclass
class MlProcessingRealtimeTrainingConfig:
    """Real-time training configuration for ML Processing microservice"""
    # Real-time training
    realtime_training_enabled: bool = field(default_factory=lambda: get_config_manager().get('realtime_training.enabled', True))
    training_mode: MlProcessingLearningMode = field(default_factory=lambda: MlProcessingLearningMode(get_config_manager().get('realtime_training.mode', 'online')))
    
    # Training frequency
    training_frequency: str = field(default_factory=lambda: get_config_manager().get('realtime_training.update_frequency_minutes', 'hourly'))  # continuous, hourly, daily
    min_training_samples: int = field(default_factory=lambda: get_config_manager().get('realtime_training.min_samples_required', 100))
    max_training_samples: int = field(default_factory=lambda: get_config_manager().get('realtime_training.max_samples', 10000))
    
    # Incremental learning
    incremental_learning_enabled: bool = field(default_factory=lambda: get_config_manager().get('realtime_training.incremental_learning', True))
    learning_rate_decay: float = field(default_factory=lambda: get_config_manager().get('realtime_training.learning_rate_decay', 0.99))
    batch_size: int = field(default_factory=lambda: get_config_manager().get('realtime_training.batch_size', 32))
    
    # Data preprocessing
    feature_scaling: bool = field(default_factory=lambda: get_config_manager().get('feature_engineering.feature_scaling_enabled', True))
    feature_selection: bool = field(default_factory=lambda: get_config_manager().get('feature_engineering.feature_selection_enabled', True))
    feature_engineering: bool = field(default_factory=lambda: get_config_manager().get('feature_engineering.enabled', True))
    
    # Model validation
    cross_validation_enabled: bool = field(default_factory=lambda: get_config_manager().get('training.cross_validation.enabled', True))
    validation_split: float = field(default_factory=lambda: get_config_manager().get('data_processing.validation.validation_split', 0.2))
    validation_method: str = field(default_factory=lambda: get_config_manager().get('data_processing.validation.time_series_split', 'time_series_split'))
    
    # Performance monitoring
    performance_monitoring_enabled: bool = field(default_factory=lambda: get_config_manager().get('monitoring.performance_tracking', True))
    performance_metrics: List[str] = field(default_factory=lambda: 
        get_config_manager().get('evaluation.metrics.classification', 'accuracy,precision,recall,f1_score,auc').split(',')
    )
    
    # Model drift detection
    drift_detection_enabled: bool = field(default_factory=lambda: get_config_manager().get('realtime_training.drift_detection', True))
    drift_detection_method: str = field(default_factory=lambda: get_config_manager().get('realtime_training.drift_method', 'psi'))  # psi, ks_test, wasserstein
    drift_threshold: float = field(default_factory=lambda: get_config_manager().get('realtime_training.drift_threshold', 0.1))
    
    # Automatic retraining
    auto_retrain_enabled: bool = field(default_factory=lambda: get_config_manager().get('realtime_training.auto_retrain', True))
    retrain_threshold: float = field(default_factory=lambda: get_config_manager().get('realtime_training.retrain_threshold', 0.05))  # 5% performance drop
    retrain_strategy: MlProcessingTrainingStrategy = field(default_factory=lambda: MlProcessingTrainingStrategy(get_config_manager().get('realtime_training.strategy', 'incremental')))
    
    # Enhanced tracking for microservice
    microservice_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize config with microservice centralization"""
        self.microservice_metadata.update({
            "creation_method": "training_config_microservice",
            "microservice": "ml-processing",
            "centralized_infrastructure": True,
            "config_timestamp": time.time(),
            "environment": "microservice"
        })


@dataclass
class MlProcessingLearningAdaptationConfig:
    """Learning adaptation configuration for ML Processing microservice"""
    # Adaptation settings
    adaptation_enabled: bool = field(default_factory=lambda: get_config_manager().get('realtime_training.adaptation_enabled', True))
    adaptation_frequency: str = field(default_factory=lambda: get_config_manager().get('realtime_training.adaptation_frequency', 'daily'))  # continuous, hourly, daily, weekly
    
    # Market regime detection
    regime_detection_enabled: bool = bool(os.getenv("ML_ADAPTATION_REGIME_DETECTION", "true").lower() == "true")
    regime_detection_method: str = os.getenv("ML_ADAPTATION_REGIME_DETECTION_METHOD", "hmm")  # hmm, clustering, change_point
    regime_lookback_period: int = int(os.getenv("ML_ADAPTATION_REGIME_LOOKBACK_PERIOD", "100"))
    
    # Model adaptation strategies
    adaptation_strategies: List[str] = field(default_factory=lambda: 
        os.getenv("ML_ADAPTATION_STRATEGIES", "parameter_tuning,feature_selection,model_selection").split(",")
    )
    
    # Parameter optimization
    parameter_optimization_enabled: bool = bool(os.getenv("ML_ADAPTATION_PARAMETER_OPTIMIZATION", "true").lower() == "true")
    optimization_method: str = os.getenv("ML_ADAPTATION_OPTIMIZATION_METHOD", "bayesian")  # grid, random, bayesian
    optimization_iterations: int = int(os.getenv("ML_ADAPTATION_OPTIMIZATION_ITERATIONS", "50"))
    
    # Feature adaptation
    feature_adaptation_enabled: bool = bool(os.getenv("ML_ADAPTATION_FEATURE_ADAPTATION", "true").lower() == "true")
    feature_importance_threshold: float = float(os.getenv("ML_ADAPTATION_FEATURE_IMPORTANCE_THRESHOLD", "0.01"))
    adaptive_feature_selection: bool = bool(os.getenv("ML_ADAPTATION_ADAPTIVE_FEATURE_SELECTION", "true").lower() == "true")
    
    # Model ensemble adaptation
    ensemble_adaptation_enabled: bool = bool(os.getenv("ML_ADAPTATION_ENSEMBLE_ADAPTATION", "true").lower() == "true")
    ensemble_weight_adaptation: bool = bool(os.getenv("ML_ADAPTATION_ENSEMBLE_WEIGHT_ADAPTATION", "true").lower() == "true")
    model_replacement_enabled: bool = bool(os.getenv("ML_ADAPTATION_MODEL_REPLACEMENT", "true").lower() == "true")
    
    # Performance-based adaptation
    performance_based_adaptation: bool = bool(os.getenv("ML_ADAPTATION_PERFORMANCE_BASED", "true").lower() == "true")
    performance_window: int = int(os.getenv("ML_ADAPTATION_PERFORMANCE_WINDOW", "100"))
    adaptation_threshold: float = float(os.getenv("ML_ADAPTATION_THRESHOLD", "0.03"))  # 3% performance improvement
    
    # Memory-based learning
    memory_based_learning: bool = bool(os.getenv("ML_ADAPTATION_MEMORY_BASED_LEARNING", "true").lower() == "true")
    memory_size: int = int(os.getenv("ML_ADAPTATION_MEMORY_SIZE", "1000"))
    memory_decay_factor: float = float(os.getenv("ML_ADAPTATION_MEMORY_DECAY_FACTOR", "0.95"))
    
    # Contextual adaptation
    contextual_adaptation: bool = bool(os.getenv("ML_ADAPTATION_CONTEXTUAL_ADAPTATION", "true").lower() == "true")
    context_features: List[str] = field(default_factory=lambda: 
        os.getenv("ML_ADAPTATION_CONTEXT_FEATURES", "market_volatility,trading_session,economic_events").split(",")
    )
    
    # Enhanced tracking for microservice
    microservice_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize config with microservice centralization"""
        self.microservice_metadata.update({
            "creation_method": "adaptation_config_microservice",
            "microservice": "ml-processing",
            "centralized_infrastructure": True,
            "config_timestamp": time.time(),
            "environment": "microservice"
        })


@dataclass
class MlProcessingFeatureEngineeringConfig:
    """Feature engineering configuration for ML Processing microservice"""
    # Feature engineering
    feature_engineering_enabled: bool = field(default_factory=lambda: get_config_manager().get('feature_engineering.enabled', True))
    
    # Technical indicators as features
    technical_indicators: bool = field(default_factory=lambda: get_config_manager().get('feature_engineering.technical_indicators.enabled', True))
    indicator_periods: List[int] = field(default_factory=lambda: 
        [int(x) for x in get_config_manager().get('feature_engineering.technical_indicators.indicators', '5,10,14,20,50').split(',')]
    )
    
    # Price-based features
    price_features: bool = bool(os.getenv("ML_FEATURE_PRICE_FEATURES", "true").lower() == "true")
    price_transformations: List[str] = field(default_factory=lambda: 
        os.getenv("ML_FEATURE_PRICE_TRANSFORMATIONS", "returns,log_returns,rolling_mean,rolling_std").split(",")
    )
    
    # Volume-based features
    volume_features: bool = bool(os.getenv("ML_FEATURE_VOLUME_FEATURES", "true").lower() == "true")
    volume_transformations: List[str] = field(default_factory=lambda: 
        os.getenv("ML_FEATURE_VOLUME_TRANSFORMATIONS", "volume_profile,vwap,volume_ratio").split(",")
    )
    
    # Time-based features
    time_features: bool = bool(os.getenv("ML_FEATURE_TIME_FEATURES", "true").lower() == "true")
    time_components: List[str] = field(default_factory=lambda: 
        os.getenv("ML_FEATURE_TIME_COMPONENTS", "hour,day_of_week,month,quarter,trading_session").split(",")
    )
    
    # Market structure features
    market_structure_features: bool = bool(os.getenv("ML_FEATURE_MARKET_STRUCTURE", "true").lower() == "true")
    structure_components: List[str] = field(default_factory=lambda: 
        os.getenv("ML_FEATURE_STRUCTURE_COMPONENTS", "support_resistance,trend_strength,volatility_regime").split(",")
    )
    
    # Sentiment features
    sentiment_features: bool = bool(os.getenv("ML_FEATURE_SENTIMENT_FEATURES", "true").lower() == "true")
    sentiment_sources: List[str] = field(default_factory=lambda: 
        os.getenv("ML_FEATURE_SENTIMENT_SOURCES", "news,economic_calendar,cot_reports").split(",")
    )
    
    # Feature selection
    feature_selection_enabled: bool = bool(os.getenv("ML_FEATURE_SELECTION_ENABLED", "true").lower() == "true")
    feature_selection_method: str = os.getenv("ML_FEATURE_SELECTION_METHOD", "recursive_feature_elimination")
    max_features: int = int(os.getenv("ML_FEATURE_MAX_FEATURES", "50"))
    
    # Feature scaling
    feature_scaling_enabled: bool = bool(os.getenv("ML_FEATURE_SCALING_ENABLED", "true").lower() == "true")
    scaling_method: str = os.getenv("ML_FEATURE_SCALING_METHOD", "standard")  # standard, minmax, robust
    
    # Feature importance
    feature_importance_enabled: bool = bool(os.getenv("ML_FEATURE_IMPORTANCE_ENABLED", "true").lower() == "true")
    importance_method: str = os.getenv("ML_FEATURE_IMPORTANCE_METHOD", "permutation")  # permutation, shap, tree_based
    
    # Enhanced tracking for microservice
    microservice_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize config with microservice centralization"""
        self.microservice_metadata.update({
            "creation_method": "feature_config_microservice",
            "microservice": "ml-processing",
            "centralized_infrastructure": True,
            "config_timestamp": time.time(),
            "environment": "microservice"
        })


@dataclass
class MlProcessingSettings:
    """Main ML processing settings for microservice"""
    # Module settings
    enabled: bool = field(default_factory=lambda: get_config_manager().get('service.enabled', True))
    debug_mode: bool = field(default_factory=lambda: get_config_manager().get('service.debug', False))
    
    # Configuration components
    ensemble: MlProcessingModelEnsembleConfig = field(default_factory=MlProcessingModelEnsembleConfig)
    realtime_training: MlProcessingRealtimeTrainingConfig = field(default_factory=MlProcessingRealtimeTrainingConfig)
    adaptation: MlProcessingLearningAdaptationConfig = field(default_factory=MlProcessingLearningAdaptationConfig)
    feature_engineering: MlProcessingFeatureEngineeringConfig = field(default_factory=MlProcessingFeatureEngineeringConfig)
    
    # Processing settings
    batch_size: int = field(default_factory=lambda: get_config_manager().get('machine_learning.batch_size', 1000))
    max_workers: int = field(default_factory=lambda: get_config_manager().get('performance.concurrent_processes', 4))
    processing_timeout: int = field(default_factory=lambda: get_config_manager().get('machine_learning.training_timeout_seconds', 300))  # 5 minutes
    
    # Model storage
    model_storage_enabled: bool = field(default_factory=lambda: get_config_manager().get('machine_learning.model_storage_enabled', True))
    model_storage_path: str = field(default_factory=lambda: get_config_manager().get('machine_learning.model_storage_path', 'models/'))
    model_versioning: bool = field(default_factory=lambda: get_config_manager().get('machine_learning.model_versioning', True))
    
    # Prediction settings
    prediction_enabled: bool = bool(os.getenv("ML_PROCESSING_PREDICTION_ENABLED", "true").lower() == "true")
    prediction_horizon: int = int(os.getenv("ML_PROCESSING_PREDICTION_HORIZON", "10"))  # 10 periods ahead
    prediction_confidence: bool = bool(os.getenv("ML_PROCESSING_PREDICTION_CONFIDENCE", "true").lower() == "true")
    
    # Performance monitoring
    performance_monitoring_enabled: bool = field(default_factory=lambda: get_config_manager().get('monitoring.performance_tracking', True))
    performance_metrics: List[str] = field(default_factory=lambda: 
        get_config_manager().get('evaluation.metrics.regression', 'accuracy,precision,recall,f1_score,mse,mae').split(',')
    )
    
    # Database integration
    database_enabled: bool = field(default_factory=lambda: get_config_manager().get('database.enabled', True))
    store_predictions: bool = field(default_factory=lambda: get_config_manager().get('database.store_predictions', True))
    store_model_metadata: bool = field(default_factory=lambda: get_config_manager().get('database.store_metadata', True))
    
    # Logging and monitoring
    logging_enabled: bool = field(default_factory=lambda: get_config_manager().get('logging.enabled', True))
    logging_level: str = field(default_factory=lambda: get_config_manager().get('logging.level', 'INFO'))
    metrics_enabled: bool = field(default_factory=lambda: get_config_manager().get('monitoring.metrics_enabled', True))
    
    # Error handling
    error_handling_enabled: bool = field(default_factory=lambda: get_config_manager().get('error_handling.enabled', True))
    max_retries: int = field(default_factory=lambda: get_config_manager().get('error_handling.max_retries', 3))
    retry_delay: int = field(default_factory=lambda: get_config_manager().get('error_handling.retry_delay', 5))
    
    # Health checks
    health_check_enabled: bool = field(default_factory=lambda: get_config_manager().get('monitoring.health_check_enabled', True))
    health_check_interval: int = field(default_factory=lambda: get_config_manager().get('monitoring.health_check_interval_seconds', 600))  # 10 minutes
    
    # Enhanced tracking for microservice
    microservice_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize settings with microservice centralization"""
        self.microservice_metadata.update({
            "creation_method": "ml_processing_settings_microservice",
            "microservice": "ml-processing",
            "centralized_infrastructure": True,
            "settings_timestamp": time.time(),
            "environment": "microservice"
        })


class MlProcessingSettingsManager(MlProcessingBaseMicroservice):
    """
    Settings Manager for ML Processing Microservice - ENHANCED WITH FULL CENTRALIZATION
    Enterprise-grade configuration management for microservice architecture
    
    CENTRALIZED INFRASTRUCTURE:
    - Performance tracking untuk configuration operations
    - Centralized error handling untuk configuration validation
    - Event publishing untuk configuration lifecycle monitoring
    - Enhanced logging dengan configuration-specific context
    - Comprehensive validation untuk configuration data
    - Advanced metrics tracking untuk configuration performance optimization
    """
    
    @performance_tracked(service_name="ml-processing", operation_name="initialize_settings_manager_microservice")
    def __init__(self):
        """Initialize ML Processing Settings Manager dengan FULL CENTRALIZATION"""
        try:
            # Initialize base microservice infrastructure
            super().__init__(service_name="ml-processing", component_name="settings_manager")
            
            # Component-specific initialization
            self.settings = MlProcessingSettings()
            self.config_cache: Dict[str, Any] = {}
            
            # Publish component initialization event
            self.publish_event(
                event_type="settings_manager_initialized",
                message="Settings manager component initialized with full centralization",
                data={
                    "enabled": self.settings.enabled,
                    "debug_mode": self.settings.debug_mode,
                    "microservice_version": "2.0.0"
                }
            )
            ml_processing_config_metrics["events_published"] += 1
            ml_processing_config_metrics["successful_configurations"] += 1
            
            self.logger.info(f"✅ ML Processing settings manager initialized with centralization infrastructure")
            
        except Exception as e:
            error_response = self.handle_error(e, "initialize", {"component": "settings_manager"})
            self.logger.error(f"Failed to initialize ML Processing settings manager: {error_response}")
            raise
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for settings manager component"""
        return {
            "enabled": True,
            "config_cache_size": 100,
            "config_cache_ttl": 3600,
            "validation_enabled": True,
            "health_check_interval": 30
        }
    
    def _perform_health_checks(self) -> Dict[str, Any]:
        """Perform settings manager specific health checks"""
        try:
            return {
                "healthy": True,
                "settings_loaded": self.settings is not None,
                "cache_size": len(self.config_cache),
                "settings_enabled": self.settings.enabled if self.settings else False,
                "ensemble_enabled": self.settings.ensemble.ensemble_enabled if self.settings else False,
                "training_enabled": self.settings.realtime_training.realtime_training_enabled if self.settings else False
            }
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    @performance_tracked(service_name="ml-processing", operation_name="get_ml_processing_settings")
    def get_ml_processing_settings(self) -> MlProcessingSettings:
        """Get ML processing settings with caching"""
        start_time = time.perf_counter()
        
        try:
            # Check cache first
            cache_key = "ml_processing_settings"
            if cache_key in self.config_cache:
                ml_processing_config_metrics["config_cache_hits"] += 1
                return self.config_cache[cache_key]
            
            # Load settings
            settings = self.settings
            
            # Cache the settings
            self.config_cache[cache_key] = settings
            ml_processing_config_metrics["config_cache_misses"] += 1
            
            # Calculate load time
            load_time = (time.perf_counter() - start_time) * 1000
            ml_processing_config_metrics["avg_config_load_time_ms"] = (
                ml_processing_config_metrics["avg_config_load_time_ms"] * 0.9 + load_time * 0.1
            )
            
            # Update metrics
            ml_processing_config_metrics["total_configurations_loaded"] += 1
            
            self.logger.debug(f"Settings loaded successfully in {load_time:.2f}ms")
            return settings
            
        except Exception as e:
            load_time = (time.perf_counter() - start_time) * 1000
            ml_processing_config_metrics["failed_configurations"] += 1
            
            error_response = self.handle_error(e, "get_settings", {"load_time_ms": load_time})
            self.logger.error(f"❌ Failed to get ML processing settings: {error_response}")
            raise
    
    @performance_tracked(service_name="ml-processing", operation_name="get_enabled_models")
    def get_enabled_models(self) -> List[str]:
        """Get list of enabled ML models"""
        try:
            enabled_models = []
            settings = self.get_ml_processing_settings().ensemble
            
            if settings.catboost_enabled:
                enabled_models.append("catboost")
            if settings.xgboost_enabled:
                enabled_models.append("xgboost")
            if settings.lightgbm_enabled:
                enabled_models.append("lightgbm")
            if settings.random_forest_enabled:
                enabled_models.append("random_forest")
            if settings.gradient_boost_enabled:
                enabled_models.append("gradient_boost")
            
            self.logger.debug(f"Enabled models: {enabled_models}")
            return enabled_models
            
        except Exception as e:
            error_response = self.handle_error(e, "get_enabled_models", {})
            self.logger.error(f"❌ Failed to get enabled models: {error_response}")
            return []
    
    @performance_tracked(service_name="ml-processing", operation_name="get_model_parameters")
    def get_model_parameters(self, model_type: str) -> Dict[str, Any]:
        """Get model-specific parameters"""
        try:
            settings = self.get_ml_processing_settings().ensemble
            
            if model_type == "catboost":
                return {
                    "iterations": settings.catboost_iterations,
                    "learning_rate": settings.catboost_learning_rate,
                    "depth": settings.catboost_depth
                }
            elif model_type == "xgboost":
                return {
                    "n_estimators": settings.xgboost_n_estimators,
                    "learning_rate": settings.xgboost_learning_rate,
                    "max_depth": settings.xgboost_max_depth
                }
            elif model_type == "lightgbm":
                return {
                    "n_estimators": settings.lightgbm_n_estimators,
                    "learning_rate": settings.lightgbm_learning_rate,
                    "max_depth": settings.lightgbm_max_depth
                }
            elif model_type == "random_forest":
                return {
                    "n_estimators": settings.random_forest_n_estimators,
                    "max_depth": settings.random_forest_max_depth
                }
            elif model_type == "gradient_boost":
                return {
                    "n_estimators": settings.gradient_boost_n_estimators,
                    "learning_rate": settings.gradient_boost_learning_rate
                }
            
            return {}
            
        except Exception as e:
            error_response = self.handle_error(e, "get_model_parameters", {"model_type": model_type})
            self.logger.error(f"❌ Failed to get model parameters: {error_response}")
            return {}
    
    @performance_tracked(service_name="ml-processing", operation_name="get_feature_engineering_config")
    def get_feature_engineering_config(self) -> Dict[str, Any]:
        """Get feature engineering configuration"""
        try:
            settings = self.get_ml_processing_settings().feature_engineering
            return {
                "enabled": settings.feature_engineering_enabled,
                "technical_indicators": settings.technical_indicators,
                "price_features": settings.price_features,
                "volume_features": settings.volume_features,
                "time_features": settings.time_features,
                "market_structure_features": settings.market_structure_features,
                "sentiment_features": settings.sentiment_features,
                "feature_selection": settings.feature_selection_enabled,
                "feature_scaling": settings.feature_scaling_enabled,
                "max_features": settings.max_features
            }
            
        except Exception as e:
            error_response = self.handle_error(e, "get_feature_engineering_config", {})
            self.logger.error(f"❌ Failed to get feature engineering config: {error_response}")
            return {}
    
    @performance_tracked(service_name="ml-processing", operation_name="get_training_config")
    def get_training_config(self) -> Dict[str, Any]:
        """Get training configuration"""
        try:
            settings = self.get_ml_processing_settings().realtime_training
            return {
                "enabled": settings.realtime_training_enabled,
                "mode": settings.training_mode.value,
                "frequency": settings.training_frequency,
                "min_samples": settings.min_training_samples,
                "max_samples": settings.max_training_samples,
                "incremental_learning": settings.incremental_learning_enabled,
                "batch_size": settings.batch_size,
                "validation_split": settings.validation_split,
                "performance_monitoring": settings.performance_monitoring_enabled,
                "drift_detection": settings.drift_detection_enabled,
                "auto_retrain": settings.auto_retrain_enabled
            }
            
        except Exception as e:
            error_response = self.handle_error(e, "get_training_config", {})
            self.logger.error(f"❌ Failed to get training config: {error_response}")
            return {}
    
    def get_enhanced_health_status(self) -> Dict[str, Any]:
        """Get enhanced health status with settings manager specific metrics"""
        # Get base health status from parent
        base_health = super().get_health_status()
        
        # Add settings manager specific metrics
        base_health.update({
            "config_metrics": {
                "total_configurations": ml_processing_config_metrics["total_configurations_loaded"],
                "successful_configurations": ml_processing_config_metrics["successful_configurations"],
                "failed_configurations": ml_processing_config_metrics["failed_configurations"],
                "cache_hits": ml_processing_config_metrics["config_cache_hits"],
                "cache_misses": ml_processing_config_metrics["config_cache_misses"],
                "avg_load_time_ms": ml_processing_config_metrics["avg_config_load_time_ms"]
            },
            "settings_status": {
                "settings_loaded": self.settings is not None,
                "cache_size": len(self.config_cache),
                "ensemble_enabled": self.settings.ensemble.ensemble_enabled if self.settings else False,
                "training_enabled": self.settings.realtime_training.realtime_training_enabled if self.settings else False,
                "adaptation_enabled": self.settings.adaptation.adaptation_enabled if self.settings else False
            },
            "microservice_version": "2.0.0"
        })
        
        return base_health


# Global microservice instance
ml_processing_settings_manager = MlProcessingSettingsManager()


# Global settings instance for backward compatibility
ml_processing_settings = ml_processing_settings_manager.get_ml_processing_settings()


def get_ml_processing_settings() -> MlProcessingSettings:
    """Get ML processing settings"""
    return ml_processing_settings_manager.get_ml_processing_settings()


def get_enabled_models() -> List[str]:
    """Get list of enabled ML models"""
    return ml_processing_settings_manager.get_enabled_models()


def get_model_parameters(model_type: str) -> Dict[str, Any]:
    """Get model-specific parameters"""
    return ml_processing_settings_manager.get_model_parameters(model_type)


def get_feature_engineering_config() -> Dict[str, Any]:
    """Get feature engineering configuration"""
    return ml_processing_settings_manager.get_feature_engineering_config()


def get_training_config() -> Dict[str, Any]:
    """Get training configuration"""
    return ml_processing_settings_manager.get_training_config()


def get_settings_manager_microservice() -> MlProcessingSettingsManager:
    """Get the global settings manager microservice instance"""
    return ml_processing_settings_manager