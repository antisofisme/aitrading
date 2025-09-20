"""
🤖 Deep Learning Settings - MICROSERVICE IMPLEMENTATION
Enterprise-grade configuration settings for Deep Learning microservice

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
from ..business.base_microservice import DeepLearningBaseMicroservice

# Import configuration manager for centralized credential management
from ...shared.infrastructure.config_manager import get_config_manager

# Deep learning configuration metrics for microservice
deep_learning_config_metrics = {
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


class DeepLearningModelType(Enum):
    """Deep learning model types for Deep Learning microservice"""
    LSTM = "lstm"
    GRU = "gru"
    TRANSFORMER = "transformer"
    CNN = "cnn"
    CNN_LSTM = "cnn_lstm"
    AUTOENCODER = "autoencoder"
    GAN = "gan"
    VAE = "vae"
    ATTENTION = "attention"
    BERT = "bert"
    GPT = "gpt"


class DeepLearningMemoryType(Enum):
    """Memory enhancement types for Deep Learning microservice"""
    LETTA = "letta"
    WEAVIATE = "weaviate"
    LANGFUSE = "langfuse"
    VECTOR_DB = "vector_db"
    GRAPH_DB = "graph_db"
    NEURAL_MEMORY = "neural_memory"


class DeepLearningPatternComplexity(Enum):
    """Pattern complexity levels for Deep Learning microservice"""
    SIMPLE = "simple"
    INTERMEDIATE = "intermediate"
    COMPLEX = "complex"
    META = "meta"
    HIERARCHICAL = "hierarchical"
    NEURAL_ENHANCED = "neural_enhanced"


@dataclass
class DeepLearningModelConfig:
    """Deep learning model configuration for Deep Learning microservice"""
    
    def __post_init__(self):
        """Initialize config with configuration manager instead of hardcoded os.getenv"""
        config_manager = get_config_manager()
        
        # Deep learning settings using configuration manager
        self.deep_learning_enabled = config_manager.get('deep_learning.gpu_enabled', False) or True
        
        # Model architecture from AI coordination
        ai_config = config_manager.get_ai_coordination_config()
        self.model_architecture = ai_config.get('model_selection_strategy', 'ensemble')
        self.ensemble_size = config_manager.get('pattern_discovery.ensemble_size', 5)
        
        # LSTM configuration from model architectures
        lstm_config = config_manager.get('model_architectures.lstm', {})
        self.lstm_enabled = lstm_config.get('enabled', True)
        self.lstm_units = lstm_config.get('hidden_size', 128)
        self.lstm_layers = lstm_config.get('num_layers', 2)
        self.lstm_dropout = lstm_config.get('dropout', 0.2)
        self.lstm_sequence_length = 60  # Default sequence length
        
        # GRU configuration from model architectures
        gru_config = config_manager.get('model_architectures.gru', {})
        self.gru_enabled = gru_config.get('enabled', True)
        self.gru_units = gru_config.get('hidden_size', 128)
        self.gru_layers = gru_config.get('num_layers', 2)
        self.gru_dropout = gru_config.get('dropout', 0.2)
        
        # Transformer configuration from model architectures
        transformer_config = config_manager.get('model_architectures.transformer', {})
        self.transformer_enabled = transformer_config.get('enabled', True)
        self.transformer_heads = transformer_config.get('nhead', 8)
        self.transformer_layers = transformer_config.get('num_layers', 6)
        self.transformer_d_model = transformer_config.get('d_model', 512)
        self.transformer_dropout = transformer_config.get('dropout', 0.1)
        
        # CNN configuration from model architectures
        cnn_config = config_manager.get('model_architectures.cnn', {})
        self.cnn_enabled = cnn_config.get('enabled', True)
        self.cnn_filters = cnn_config.get('num_filters', 64)
        self.cnn_kernel_size = 3  # Default kernel size
        self.cnn_layers = 3  # Default layers
        self.cnn_dropout = cnn_config.get('dropout', 0.2)
        
        # CNN-LSTM hybrid configuration (derived from individual configs)
        self.cnn_lstm_enabled = self.cnn_enabled and self.lstm_enabled
        self.cnn_lstm_cnn_filters = 32  # Reduced for hybrid
        self.cnn_lstm_lstm_units = 64  # Reduced for hybrid
        
        # Training configuration
        training_config = config_manager.get_training_config() if hasattr(config_manager, 'get_training_config') else config_manager.get('training', {})
        self.batch_size = training_config.get('batch_size', 32)
        self.epochs = training_config.get('epochs', 100)
        self.learning_rate = training_config.get('learning_rate', 0.001)
        self.early_stopping_patience = training_config.get('patience', 10)
        
        # Optimization
        self.optimizer = training_config.get('optimizer', 'adam')
        self.loss_function = 'mse'  # Default loss function
        
        # Regularization
        self.l1_regularization = 0.0  # Default L1
        self.l2_regularization = 0.01  # Default L2
        self.dropout_rate = 0.2  # Default dropout
        
        # Model persistence
        self.model_save_enabled = True
        self.model_save_path = 'models/deep_learning/'
        self.model_versioning = True
        
        # Performance monitoring
        performance_config = config_manager.get_performance_config()
        self.performance_monitoring = performance_config.get('resource_monitoring', True)
        self.validation_split = training_config.get('validation_split', 0.2)
        self.test_split = 0.1  # Default test split
    
    # Enhanced tracking for microservice
    microservice_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize config with microservice centralization"""
        self.microservice_metadata.update({
            "creation_method": "dl_model_config_microservice",
            "microservice": "deep-learning",
            "centralized_infrastructure": True,
            "config_timestamp": time.time(),
            "environment": "microservice"
        })


@dataclass
class DeepLearningMemoryEnhancementConfig:
    """Memory enhancement configuration for Deep Learning microservice"""
    
    def __post_init__(self):
        """Initialize config with configuration manager instead of hardcoded os.getenv"""
        config_manager = get_config_manager()
        
        # Memory enhancement using configuration manager
        memory_systems = config_manager.get('memory_systems', {})
        
        # General memory enhancement
        self.memory_enhancement_enabled = bool(memory_systems)
        
        # Letta memory integration
        letta_config = memory_systems.get('letta', {})
        self.letta_enabled = letta_config.get('enabled', False)
        self.letta_memory_size = 10000  # Default memory size
        self.letta_context_window = 1000  # Default context window
        
        # Weaviate vector memory
        weaviate_config = memory_systems.get('weaviate', {})
        self.weaviate_enabled = weaviate_config.get('enabled', False)
        self.weaviate_vector_dimensions = weaviate_config.get('vector_dimensions', 1536)
        self.weaviate_similarity_threshold = 0.8  # Default similarity threshold
        
        # Langfuse tracking
        langfuse_config = memory_systems.get('langfuse', {})
        self.langfuse_enabled = langfuse_config.get('enabled', False)
        self.langfuse_session_tracking = True
        self.langfuse_performance_tracking = True
        
        # Memory fusion
        self.memory_manager_enabled = bool(memory_systems)
        self.fusion_strategy = 'weighted_average'  # Default fusion strategy
        
        # Neural memory networks
        self.neural_memory_enabled = True
        self.neural_memory_capacity = 1000
        self.neural_memory_layers = 3
        
        # Historical pattern memory
        pattern_config = config_manager.get('pattern_discovery', {})
        self.pattern_memory_enabled = pattern_config.get('enabled', True)
        self.pattern_memory_size = 5000
        self.pattern_decay_factor = 0.99
        
        # Contextual memory
        self.contextual_memory_enabled = True
        self.context_features = ["market_regime", "volatility", "trading_session", "economic_events"]
        
        # Memory optimization
        performance_config = config_manager.get_performance_config()
        self.memory_optimization_enabled = performance_config.get('parallel_processing', True)
        self.memory_compression = True
        self.memory_pruning = True
        
        # Adaptive memory
        self.adaptive_memory_enabled = True
        self.memory_adaptation_frequency = 'daily'
    
    # Enhanced tracking for microservice
    microservice_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize config with microservice centralization"""
        self.microservice_metadata.update({
            "creation_method": "memory_config_microservice",
            "microservice": "deep-learning",
            "centralized_infrastructure": True,
            "config_timestamp": time.time(),
            "environment": "microservice"
        })


@dataclass
class DeepLearningPatternDiscoveryConfig:
    """Pattern discovery configuration for Deep Learning microservice"""
    
    def __post_init__(self):
        """Initialize config with configuration manager instead of hardcoded os.getenv"""
        config_manager = get_config_manager()
        
        # Pattern discovery using configuration manager
        pattern_config = config_manager.get('pattern_discovery', {})
        model_config = config_manager.get_pattern_discovery_config()
        
        # Pattern discovery
        self.pattern_discovery_enabled = model_config.get('enabled', True)
        self.pattern_complexity = DeepLearningPatternComplexity.COMPLEX  # Default complexity
        
        # Neural pattern detection
        self.neural_pattern_detection = True
        self.neural_pattern_layers = 4
        self.neural_pattern_attention = True
        
        # Hierarchical pattern detection
        self.hierarchical_patterns = True
        self.hierarchy_levels = 3
        
        # Pattern of patterns (meta-patterns)
        self.pattern_of_patterns_enabled = True
        self.min_pattern_occurrences = pattern_config.get('ensemble_size', 5)
        
        # Multi-dimensional analysis
        self.multi_dimensional_analysis = True
        feature_config = config_manager.get('feature_engineering', {})
        if feature_config.get('enabled', True):
            indicators = feature_config.get('technical_indicators', 'sma,ema,rsi,macd,bollinger')
            self.analysis_dimensions = indicators.split(',') if isinstance(indicators, str) else indicators
        else:
            self.analysis_dimensions = ["price", "volume", "time", "volatility", "sentiment", "neural_features"]
        
        # Cross-asset pattern analysis
        self.cross_asset_patterns = True
        self.cross_asset_instruments = ["XAUUSD", "EURUSD", "XAGUSD", "AUDUSD", "USDCHF"]
        
        # Temporal pattern analysis
        self.temporal_patterns = True
        lookback_periods = feature_config.get('lookback_periods', '5,10,20,50')
        if isinstance(lookback_periods, str):
            self.temporal_scales = lookback_periods.split(',')
        else:
            self.temporal_scales = ["intraday", "daily", "weekly", "monthly"]
        
        # Pattern evolution tracking
        self.pattern_evolution_tracking = True
        self.evolution_window = pattern_config.get('pattern_length', 10) * 10  # 10x pattern length
        
        # Statistical significance
        self.statistical_significance = True
        self.significance_threshold = 0.05
        
        # Pattern validation
        self.pattern_validation_enabled = True
        self.validation_methods = ["bootstrap", "cross_validation", "monte_carlo", "neural_validation"]
    
    # Enhanced tracking for microservice
    microservice_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize config with microservice centralization"""
        self.microservice_metadata.update({
            "creation_method": "pattern_discovery_config_microservice",
            "microservice": "deep-learning",
            "centralized_infrastructure": True,
            "config_timestamp": time.time(),
            "environment": "microservice"
        })


@dataclass
class DeepLearningAICoordinationConfig:
    """AI coordination configuration for Deep Learning microservice"""
    
    def __post_init__(self):
        """Initialize config with configuration manager instead of hardcoded os.getenv"""
        config_manager = get_config_manager()
        
        # AI coordination using configuration manager
        ai_coord_config = config_manager.get_ai_coordination_config()
        
        # AI coordination
        self.ai_coordination_enabled = ai_coord_config.get('multi_model_ensemble', True)
        
        # Delta AI processing
        self.delta_ai_enabled = True
        self.delta_computation_method = 'adaptive'  # Default adaptive
        self.delta_threshold = 0.001
        
        # Incremental processing
        self.incremental_processing = True
        self.processing_window = 100
        
        # Change detection
        self.change_detection_enabled = True
        self.change_detection_method = 'neural'  # Neural detection
        
        # Adaptive thresholds
        self.adaptive_thresholds = True
        self.threshold_adaptation_rate = 0.1
        
        # Multi-model coordination
        self.multi_model_coordination = ai_coord_config.get('multi_model_ensemble', True)
        self.model_ensemble_size = 5  # Default ensemble size
        self.ensemble_strategy = ai_coord_config.get('model_selection_strategy', 'performance')
        
        # Performance optimization
        performance_config = config_manager.get_performance_config()
        self.performance_optimization = performance_config.get('parallel_processing', True)
        self.optimization_strategy = 'gpu_optimized' if config_manager.is_gpu_enabled() else 'memory_efficient'
        
        # Caching
        model_cache_config = config_manager.get_model_cache_config() if hasattr(config_manager, 'get_model_cache_config') else {}
        self.ai_caching_enabled = model_cache_config.get('cache_enabled', True)
        self.cache_size = model_cache_config.get('cache_size_gb', 10) * 1000  # Convert GB to units
        
        # Quality control
        monitoring_config = config_manager.get_monitoring_config()
        self.quality_control_enabled = monitoring_config.get('model_performance_tracking', True)
        self.quality_metrics = ["accuracy", "precision", "recall", "f1_score", "neural_confidence"]
    
    # Enhanced tracking for microservice
    microservice_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize config with microservice centralization"""
        self.microservice_metadata.update({
            "creation_method": "ai_coordination_config_microservice",
            "microservice": "deep-learning",
            "centralized_infrastructure": True,
            "config_timestamp": time.time(),
            "environment": "microservice"
        })


@dataclass
class DeepLearningSettings:
    """Main deep learning settings for microservice"""
    
    def __post_init__(self):
        """Initialize settings with configuration manager instead of hardcoded os.getenv"""
        config_manager = get_config_manager()
        
        # Module settings using configuration manager
        service_config = config_manager.get_service_config()
        self.enabled = True  # Deep learning service is always enabled
        self.debug_mode = service_config.get('debug', False)
        
        # Configuration components
        self.model_config = DeepLearningModelConfig()
        self.memory_enhancement = DeepLearningMemoryEnhancementConfig()
        self.pattern_discovery = DeepLearningPatternDiscoveryConfig()
        self.ai_coordination = DeepLearningAICoordinationConfig()
        
        # Processing settings
        performance_config = config_manager.get_performance_config()
        self.batch_processing = True  # Always enable batch processing
        self.max_workers = performance_config.get('cpu_cores', 8)
        inference_config = config_manager.get_inference_config() if hasattr(config_manager, 'get_inference_config') else {}
        self.processing_timeout = inference_config.get('timeout_seconds', 120)
        
        # GPU/TPU settings
        self.gpu_enabled = config_manager.is_gpu_enabled()
        self.gpu_memory_fraction = 0.8  # Default GPU memory fraction
        self.mixed_precision = True  # Enable mixed precision by default
        
        # Model storage
        model_cache_config = config_manager.get_model_cache_config() if hasattr(config_manager, 'get_model_cache_config') else {}
        self.model_storage_enabled = True
        self.model_storage_path = 'models/deep_learning/'
        self.model_versioning = True
        
        # Prediction settings
        self.prediction_enabled = True
        self.prediction_horizon = 10  # 10 periods ahead
        self.prediction_confidence = True
        
        # Performance monitoring
        monitoring_config = config_manager.get_monitoring_config()
        self.performance_monitoring_enabled = monitoring_config.get('model_performance_tracking', True)
        self.performance_metrics = ["accuracy", "precision", "recall", "f1_score", "neural_loss", "training_speed"]
        
        # Database integration
        db_config = config_manager.get_database_config()
        self.database_enabled = bool(db_config)
        self.store_predictions = monitoring_config.get('prediction_logging', True)
        self.store_model_metadata = True
        
        # Logging and monitoring
        logging_config = config_manager.get_logging_config()
        self.logging_enabled = logging_config.get('enable_model_logging', True)
        self.logging_level = logging_config.get('level', 'INFO').upper()
        self.metrics_enabled = monitoring_config.get('metrics_enabled', True)
        
        # Error handling
        self.error_handling_enabled = True
        self.max_retries = 3
        self.retry_delay = 5
        
        # Health checks
        self.health_check_enabled = True
        self.health_check_interval = monitoring_config.get('health_check_interval_seconds', 30)
    
    # Enhanced tracking for microservice
    microservice_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize settings with microservice centralization"""
        self.microservice_metadata.update({
            "creation_method": "deep_learning_settings_microservice",
            "microservice": "deep-learning",
            "centralized_infrastructure": True,
            "settings_timestamp": time.time(),
            "environment": "microservice"
        })


class DeepLearningSettingsManager(DeepLearningBaseMicroservice):
    """
    Settings Manager for Deep Learning Microservice - ENHANCED WITH FULL CENTRALIZATION
    Enterprise-grade configuration management for microservice architecture
    
    CENTRALIZED INFRASTRUCTURE:
    - Performance tracking untuk configuration operations
    - Centralized error handling untuk configuration validation
    - Event publishing untuk configuration lifecycle monitoring
    - Enhanced logging dengan configuration-specific context
    - Comprehensive validation untuk configuration data
    - Advanced metrics tracking untuk configuration performance optimization
    """
    
    @performance_tracked(operation_name="initialize_dl_settings_manager_microservice")
    def __init__(self):
        """Initialize Deep Learning Settings Manager dengan FULL CENTRALIZATION"""
        try:
            # Initialize base microservice infrastructure
            super().__init__(service_name="deep-learning", component_name="settings_manager")
            
            # Component-specific initialization
            self.settings = DeepLearningSettings()
            self.config_cache: Dict[str, Any] = {}
            
            # Publish component initialization event
            self.publish_event(
                event_type="dl_settings_manager_initialized",
                message="Deep learning settings manager component initialized with full centralization",
                data={
                    "enabled": self.settings.enabled,
                    "debug_mode": self.settings.debug_mode,
                    "gpu_enabled": self.settings.gpu_enabled,
                    "microservice_version": "2.0.0"
                }
            )
            deep_learning_config_metrics["events_published"] += 1
            deep_learning_config_metrics["successful_configurations"] += 1
            
            self.logger.info(f"✅ Deep learning settings manager initialized with centralization infrastructure")
            
        except Exception as e:
            error_response = self.handle_error(e, "initialize", {"component": "dl_settings_manager"})
            self.logger.error(f"Failed to initialize deep learning settings manager: {error_response}")
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
                "gpu_enabled": self.settings.gpu_enabled if self.settings else False,
                "model_config_enabled": self.settings.model_config.deep_learning_enabled if self.settings else False,
                "memory_enhancement_enabled": self.settings.memory_enhancement.memory_enhancement_enabled if self.settings else False
            }
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    @performance_tracked(operation_name="get_deep_learning_settings")
    def get_deep_learning_settings(self) -> DeepLearningSettings:
        """Get deep learning settings with caching"""
        start_time = time.perf_counter()
        
        try:
            # Check cache first
            cache_key = "deep_learning_settings"
            if cache_key in self.config_cache:
                deep_learning_config_metrics["config_cache_hits"] += 1
                return self.config_cache[cache_key]
            
            # Load settings
            settings = self.settings
            
            # Cache the settings
            self.config_cache[cache_key] = settings
            deep_learning_config_metrics["config_cache_misses"] += 1
            
            # Calculate load time
            load_time = (time.perf_counter() - start_time) * 1000
            deep_learning_config_metrics["avg_config_load_time_ms"] = (
                deep_learning_config_metrics["avg_config_load_time_ms"] * 0.9 + load_time * 0.1
            )
            
            # Update metrics
            deep_learning_config_metrics["total_configurations_loaded"] += 1
            
            self.logger.debug(f"Deep learning settings loaded successfully in {load_time:.2f}ms")
            return settings
            
        except Exception as e:
            load_time = (time.perf_counter() - start_time) * 1000
            deep_learning_config_metrics["failed_configurations"] += 1
            
            error_response = self.handle_error(e, "get_dl_settings", {"load_time_ms": load_time})
            self.logger.error(f"❌ Failed to get deep learning settings: {error_response}")
            raise
    
    @performance_tracked(operation_name="get_enabled_models")
    def get_enabled_models(self) -> List[str]:
        """Get list of enabled deep learning models"""
        try:
            enabled_models = []
            settings = self.get_deep_learning_settings().model_config
            
            if settings.lstm_enabled:
                enabled_models.append("lstm")
            if settings.gru_enabled:
                enabled_models.append("gru")
            if settings.transformer_enabled:
                enabled_models.append("transformer")
            if settings.cnn_enabled:
                enabled_models.append("cnn")
            if settings.cnn_lstm_enabled:
                enabled_models.append("cnn_lstm")
            
            self.logger.debug(f"Enabled deep learning models: {enabled_models}")
            return enabled_models
            
        except Exception as e:
            error_response = self.handle_error(e, "get_enabled_models", {})
            self.logger.error(f"❌ Failed to get enabled models: {error_response}")
            return []
    
    @performance_tracked(operation_name="get_model_configuration")
    def get_model_configuration(self, model_type: str) -> Dict[str, Any]:
        """Get model-specific configuration"""
        try:
            settings = self.get_deep_learning_settings().model_config
            
            if model_type == "lstm":
                return {
                    "units": settings.lstm_units,
                    "layers": settings.lstm_layers,
                    "dropout": settings.lstm_dropout,
                    "sequence_length": settings.lstm_sequence_length
                }
            elif model_type == "gru":
                return {
                    "units": settings.gru_units,
                    "layers": settings.gru_layers,
                    "dropout": settings.gru_dropout
                }
            elif model_type == "transformer":
                return {
                    "heads": settings.transformer_heads,
                    "layers": settings.transformer_layers,
                    "d_model": settings.transformer_d_model,
                    "dropout": settings.transformer_dropout
                }
            elif model_type == "cnn":
                return {
                    "filters": settings.cnn_filters,
                    "kernel_size": settings.cnn_kernel_size,
                    "layers": settings.cnn_layers,
                    "dropout": settings.cnn_dropout
                }
            elif model_type == "cnn_lstm":
                return {
                    "cnn_filters": settings.cnn_lstm_cnn_filters,
                    "lstm_units": settings.cnn_lstm_lstm_units
                }
            
            return {}
            
        except Exception as e:
            error_response = self.handle_error(e, "get_model_config", {"model_type": model_type})
            self.logger.error(f"❌ Failed to get model configuration: {error_response}")
            return {}
    
    def get_enhanced_health_status(self) -> Dict[str, Any]:
        """Get enhanced health status with settings manager specific metrics"""
        # Get base health status from parent
        base_health = super().get_health_status()
        
        # Add settings manager specific metrics
        base_health.update({
            "config_metrics": {
                "total_configurations": deep_learning_config_metrics["total_configurations_loaded"],
                "successful_configurations": deep_learning_config_metrics["successful_configurations"],
                "failed_configurations": deep_learning_config_metrics["failed_configurations"],
                "cache_hits": deep_learning_config_metrics["config_cache_hits"],
                "cache_misses": deep_learning_config_metrics["config_cache_misses"],
                "avg_load_time_ms": deep_learning_config_metrics["avg_config_load_time_ms"]
            },
            "settings_status": {
                "settings_loaded": self.settings is not None,
                "cache_size": len(self.config_cache),
                "gpu_enabled": self.settings.gpu_enabled if self.settings else False,
                "model_config_enabled": self.settings.model_config.deep_learning_enabled if self.settings else False,
                "memory_enhancement_enabled": self.settings.memory_enhancement.memory_enhancement_enabled if self.settings else False,
                "pattern_discovery_enabled": self.settings.pattern_discovery.pattern_discovery_enabled if self.settings else False
            },
            "microservice_version": "2.0.0"
        })
        
        return base_health


# Global microservice instance
deep_learning_settings_manager = DeepLearningSettingsManager()


# Global settings instance for backward compatibility
deep_learning_settings = deep_learning_settings_manager.get_deep_learning_settings()


def get_deep_learning_settings() -> DeepLearningSettings:
    """Get deep learning settings"""
    return deep_learning_settings_manager.get_deep_learning_settings()


def get_enabled_models() -> List[str]:
    """Get list of enabled deep learning models"""
    return deep_learning_settings_manager.get_enabled_models()


def get_model_configuration(model_type: str) -> Dict[str, Any]:
    """Get model-specific configuration"""
    return deep_learning_settings_manager.get_model_configuration(model_type)


def get_dl_settings_manager_microservice() -> DeepLearningSettingsManager:
    """Get the global deep learning settings manager microservice instance"""
    return deep_learning_settings_manager