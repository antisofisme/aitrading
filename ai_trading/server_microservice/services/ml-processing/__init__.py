"""
ML Processing Service - Machine learning pipeline
Feature engineering, model training, and inference
"""
__version__ = "2.0.0"
__service_type__ = "ml-processing"

from .src import api, business, config, data_processing, infrastructure, models, technical_analysis

__all__ = ['api', 'business', 'config', 'data_processing', 'infrastructure', 'models', 'technical_analysis']

__ml_capabilities__ = [
    'feature_engineering',
    'model_training',
    'real_time_inference',
    'technical_analysis'
]