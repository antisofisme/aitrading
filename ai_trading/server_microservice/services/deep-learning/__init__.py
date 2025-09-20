"""
Deep Learning Service - Advanced neural network processing
Complex pattern recognition and deep learning models
"""
__version__ = "2.0.0"
__service_type__ = "deep-learning"

from .src import api, business, config, infrastructure, models

__all__ = ['api', 'business', 'config', 'infrastructure', 'models']

__model_types__ = [
    'transformer_models',
    'cnn_patterns',
    'rnn_sequences',
    'custom_architectures'
]