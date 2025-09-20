"""
Deep Learning API - Microservice Implementation
Neural network endpoints for advanced trading analytics
"""
__version__ = "2.0.0"

from .dl_endpoints import router as dl_router

__all__ = ['dl_router']