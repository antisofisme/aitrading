"""
Configuration settings for ML Processing modules
Centralized configuration for machine learning models and processing
"""

import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Import centralized configuration manager
from ....shared.infrastructure.config_manager import get_config_manager


class MLModelType(Enum):
    """Machine learning model types"""
    CATBOOST = "catboost"
    XGBOOST = "xgboost"
    LIGHTGBM = "lightgbm"
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOST = "gradient_boost"
    SVM = "svm"
    NEURAL_NETWORK = "neural_network"
    ENSEMBLE = "ensemble"


class LearningMode(Enum):
    """Learning modes"""
    SUPERVISED = "supervised"
    UNSUPERVISED = "unsupervised"
    REINFORCEMENT = "reinforcement"
    SEMI_SUPERVISED = "semi_supervised"
    ONLINE = "online"
    BATCH = "batch"


class TrainingStrategy(Enum):
    """Training strategies"""
    FULL_RETRAIN = "full_retrain"
    INCREMENTAL = "incremental"
    TRANSFER_LEARNING = "transfer_learning"
    FINE_TUNING = "fine_tuning"
    ENSEMBLE_UPDATE = "ensemble_update"


@dataclass
class ModelEnsembleConfig:
    """Model ensemble configuration"""
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
    
    lightgbm_enabled: bool = bool(os.getenv("ML_LIGHTGBM_ENABLED", "true").lower() == "true")
    lightgbm_n_estimators: int = int(os.getenv("ML_LIGHTGBM_N_ESTIMATORS", "100"))
    lightgbm_learning_rate: float = float(os.getenv("ML_LIGHTGBM_LEARNING_RATE", "0.1"))
    lightgbm_max_depth: int = int(os.getenv("ML_LIGHTGBM_MAX_DEPTH", "6"))
    
    random_forest_enabled: bool = bool(os.getenv("ML_RANDOM_FOREST_ENABLED", "true").lower() == "true")
    random_forest_n_estimators: int = int(os.getenv("ML_RANDOM_FOREST_N_ESTIMATORS", "100"))
    random_forest_max_depth: int = int(os.getenv("ML_RANDOM_FOREST_MAX_DEPTH", "10"))
    
    gradient_boost_enabled: bool = bool(os.getenv("ML_GRADIENT_BOOST_ENABLED", "true").lower() == "true")
    gradient_boost_n_estimators: int = int(os.getenv("ML_GRADIENT_BOOST_N_ESTIMATORS", "100"))
    gradient_boost_learning_rate: float = float(os.getenv("ML_GRADIENT_BOOST_LEARNING_RATE", "0.1"))
    
    # Ensemble aggregation
    aggregation_method: str = os.getenv("ML_ENSEMBLE_AGGREGATION_METHOD", "weighted_average")
    confidence_weighting: bool = bool(os.getenv("ML_ENSEMBLE_CONFIDENCE_WEIGHTING", "true").lower() == "true")
    dynamic_weights: bool = bool(os.getenv("ML_ENSEMBLE_DYNAMIC_WEIGHTS", "true").lower() == "true")
    
    # Performance-based weighting
    performance_weighting: bool = bool(os.getenv("ML_ENSEMBLE_PERFORMANCE_WEIGHTING", "true").lower() == "true")
    performance_window: int = int(os.getenv("ML_ENSEMBLE_PERFORMANCE_WINDOW", "100"))
    min_performance_threshold: float = float(os.getenv("ML_ENSEMBLE_MIN_PERFORMANCE_THRESHOLD", "0.6"))
    
    # Model selection
    adaptive_model_selection: bool = bool(os.getenv("ML_ENSEMBLE_ADAPTIVE_MODEL_SELECTION", "true").lower() == "true")
    model_selection_criteria: str = os.getenv("ML_ENSEMBLE_MODEL_SELECTION_CRITERIA", "accuracy")
    
    # Fallback handling
    fallback_enabled: bool = bool(os.getenv("ML_ENSEMBLE_FALLBACK_ENABLED", "true").lower() == "true")
    fallback_model: str = os.getenv("ML_ENSEMBLE_FALLBACK_MODEL", "random_forest")


@dataclass
class RealtimeTrainingConfig:
    """Real-time training configuration"""
    # Real-time training
    realtime_training_enabled: bool = bool(os.getenv("ML_REALTIME_TRAINING_ENABLED", "true").lower() == "true")
    training_mode: LearningMode = LearningMode(os.getenv("ML_REALTIME_TRAINING_MODE", "online"))
    
    # Training frequency
    training_frequency: str = os.getenv("ML_REALTIME_TRAINING_FREQUENCY", "hourly")  # continuous, hourly, daily
    min_training_samples: int = int(os.getenv("ML_REALTIME_MIN_TRAINING_SAMPLES", "100"))
    max_training_samples: int = int(os.getenv("ML_REALTIME_MAX_TRAINING_SAMPLES", "10000"))
    
    # Incremental learning
    incremental_learning_enabled: bool = bool(os.getenv("ML_REALTIME_INCREMENTAL_LEARNING", "true").lower() == "true")
    learning_rate_decay: float = float(os.getenv("ML_REALTIME_LEARNING_RATE_DECAY", "0.99"))
    batch_size: int = int(os.getenv("ML_REALTIME_BATCH_SIZE", "32"))
    
    # Data preprocessing
    feature_scaling: bool = bool(os.getenv("ML_REALTIME_FEATURE_SCALING", "true").lower() == "true")
    feature_selection: bool = bool(os.getenv("ML_REALTIME_FEATURE_SELECTION", "true").lower() == "true")
    feature_engineering: bool = bool(os.getenv("ML_REALTIME_FEATURE_ENGINEERING", "true").lower() == "true")
    
    # Model validation
    cross_validation_enabled: bool = bool(os.getenv("ML_REALTIME_CROSS_VALIDATION", "true").lower() == "true")
    validation_split: float = float(os.getenv("ML_REALTIME_VALIDATION_SPLIT", "0.2"))
    validation_method: str = os.getenv("ML_REALTIME_VALIDATION_METHOD", "time_series_split")
    
    # Performance monitoring
    performance_monitoring_enabled: bool = bool(os.getenv("ML_REALTIME_PERFORMANCE_MONITORING", "true").lower() == "true")
    performance_metrics: List[str] = field(default_factory=lambda: 
        os.getenv("ML_REALTIME_PERFORMANCE_METRICS", "accuracy,precision,recall,f1_score,auc").split(",")
    )
    
    # Model drift detection
    drift_detection_enabled: bool = bool(os.getenv("ML_REALTIME_DRIFT_DETECTION", "true").lower() == "true")
    drift_detection_method: str = os.getenv("ML_REALTIME_DRIFT_DETECTION_METHOD", "psi")  # psi, ks_test, wasserstein
    drift_threshold: float = float(os.getenv("ML_REALTIME_DRIFT_THRESHOLD", "0.1"))
    
    # Automatic retraining
    auto_retrain_enabled: bool = bool(os.getenv("ML_REALTIME_AUTO_RETRAIN", "true").lower() == "true")
    retrain_threshold: float = float(os.getenv("ML_REALTIME_RETRAIN_THRESHOLD", "0.05"))  # 5% performance drop
    retrain_strategy: TrainingStrategy = TrainingStrategy(os.getenv("ML_REALTIME_RETRAIN_STRATEGY", "incremental"))


@dataclass
class LearningAdaptationConfig:
    """Learning adaptation configuration"""
    # Adaptation settings
    adaptation_enabled: bool = bool(os.getenv("ML_ADAPTATION_ENABLED", "true").lower() == "true")
    adaptation_frequency: str = os.getenv("ML_ADAPTATION_FREQUENCY", "daily")  # continuous, hourly, daily, weekly
    
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


@dataclass
class FeatureEngineeringConfig:
    """Feature engineering configuration"""
    # Feature engineering
    feature_engineering_enabled: bool = bool(os.getenv("ML_FEATURE_ENGINEERING_ENABLED", "true").lower() == "true")
    
    # Technical indicators as features
    technical_indicators: bool = bool(os.getenv("ML_FEATURE_TECHNICAL_INDICATORS", "true").lower() == "true")
    indicator_periods: List[int] = field(default_factory=lambda: 
        [int(x) for x in os.getenv("ML_FEATURE_INDICATOR_PERIODS", "5,10,14,20,50").split(",")]
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


@dataclass
class MlProcessingSettings:
    """Main ML processing settings"""
    # Module settings
    enabled: bool = field(default_factory=lambda: get_config_manager().get('service.enabled', True))
    debug_mode: bool = field(default_factory=lambda: get_config_manager().get('service.debug', False))
    
    # Configuration components
    ensemble: ModelEnsembleConfig = field(default_factory=ModelEnsembleConfig)
    realtime_training: RealtimeTrainingConfig = field(default_factory=RealtimeTrainingConfig)
    adaptation: LearningAdaptationConfig = field(default_factory=LearningAdaptationConfig)
    feature_engineering: FeatureEngineeringConfig = field(default_factory=FeatureEngineeringConfig)
    
    # Processing settings
    batch_size: int = field(default_factory=lambda: get_config_manager().get('machine_learning.batch_size', 1000))
    max_workers: int = field(default_factory=lambda: get_config_manager().get('performance.concurrent_processes', 4))
    processing_timeout: int = field(default_factory=lambda: get_config_manager().get('machine_learning.training_timeout_seconds', 300))  # 5 minutes
    
    # Model storage
    model_storage_enabled: bool = field(default_factory=lambda: get_config_manager().get('machine_learning.model_storage_enabled', True))
    model_storage_path: str = field(default_factory=lambda: get_config_manager().get('machine_learning.model_storage_path', 'models/'))
    model_versioning: bool = field(default_factory=lambda: get_config_manager().get('machine_learning.model_versioning', True))
    
    # Prediction settings
    prediction_enabled: bool = field(default_factory=lambda: get_config_manager().get('machine_learning.prediction_enabled', True))
    prediction_horizon: int = field(default_factory=lambda: get_config_manager().get('machine_learning.prediction_horizon', 10))  # 10 periods ahead
    prediction_confidence: bool = field(default_factory=lambda: get_config_manager().get('machine_learning.prediction_confidence', True))
    
    # Performance monitoring
    performance_monitoring_enabled: bool = bool(os.getenv("ML_PROCESSING_PERFORMANCE_MONITORING", "true").lower() == "true")
    performance_metrics: List[str] = field(default_factory=lambda: 
        os.getenv("ML_PROCESSING_PERFORMANCE_METRICS", "accuracy,precision,recall,f1_score,mse,mae").split(",")
    )
    
    # Database integration
    database_enabled: bool = bool(os.getenv("ML_PROCESSING_DATABASE_ENABLED", "true").lower() == "true")
    store_predictions: bool = bool(os.getenv("ML_PROCESSING_STORE_PREDICTIONS", "true").lower() == "true")
    store_model_metadata: bool = bool(os.getenv("ML_PROCESSING_STORE_MODEL_METADATA", "true").lower() == "true")
    
    # Logging and monitoring
    logging_enabled: bool = bool(os.getenv("ML_PROCESSING_LOGGING_ENABLED", "true").lower() == "true")
    logging_level: str = os.getenv("ML_PROCESSING_LOGGING_LEVEL", "INFO")
    metrics_enabled: bool = bool(os.getenv("ML_PROCESSING_METRICS_ENABLED", "true").lower() == "true")
    
    # Error handling
    error_handling_enabled: bool = bool(os.getenv("ML_PROCESSING_ERROR_HANDLING", "true").lower() == "true")
    max_retries: int = int(os.getenv("ML_PROCESSING_MAX_RETRIES", "3"))
    retry_delay: int = int(os.getenv("ML_PROCESSING_RETRY_DELAY", "5"))
    
    # Health checks
    health_check_enabled: bool = bool(os.getenv("ML_PROCESSING_HEALTH_CHECK", "true").lower() == "true")
    health_check_interval: int = int(os.getenv("ML_PROCESSING_HEALTH_CHECK_INTERVAL", "600"))  # 10 minutes


# Global settings instance
ml_processing_settings = MlProcessingSettings()


def get_ml_processing_settings() -> MlProcessingSettings:
    """Get ML processing settings"""
    return ml_processing_settings


def get_enabled_models() -> List[str]:
    """Get list of enabled ML models"""
    enabled_models = []
    settings = ml_processing_settings.ensemble
    
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
    
    return enabled_models


def get_model_parameters(model_type: str) -> Dict[str, Any]:
    """Get model-specific parameters"""
    settings = ml_processing_settings.ensemble
    
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


def get_feature_engineering_config() -> Dict[str, Any]:
    """Get feature engineering configuration"""
    settings = ml_processing_settings.feature_engineering
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


def get_training_config() -> Dict[str, Any]:
    """Get training configuration"""
    settings = ml_processing_settings.realtime_training
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