"""
AI Provider Service - Multi-provider AI interface
Unified access to multiple AI providers and models
"""
__version__ = "2.0.0"
__service_type__ = "ai-provider"

from .src import infrastructure, providers

__all__ = ['infrastructure', 'providers']

__supported_providers__ = [
    'openai',
    'anthropic',
    'google',
    'local_models'
]