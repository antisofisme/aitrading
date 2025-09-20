"""
Configuration Management Package for ML Processing microservice

This package provides enterprise-grade configuration management:
- Multi-tiered settings (default, environment, service-specific)
- Environment variable support with validation
- Centralized configuration caching and management
- ML-specific configuration components
"""

from .settings import (
    MlProcessingSettings,
    MlProcessingSettingsManager,
    get_ml_processing_settings,
    get_enabled_models,
    get_model_parameters,
    get_feature_engineering_config,
    get_training_config,
    get_settings_manager_microservice
)

__all__ = [
    # Settings Classes
    'MlProcessingSettings',
    'MlProcessingSettingsManager',
    
    # Configuration Functions
    'get_ml_processing_settings',
    'get_enabled_models',
    'get_model_parameters',
    'get_feature_engineering_config',
    'get_training_config',
    'get_settings_manager_microservice'
]

__version__ = "2.0.0"
__microservice__ = "ml-processing"
__configuration_pattern__ = "Centralized Environment-Based Configuration"