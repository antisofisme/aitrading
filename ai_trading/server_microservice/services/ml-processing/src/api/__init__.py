"""
ML Processing API - Microservice Implementation
Traditional machine learning endpoints for trading analytics
"""
__version__ = "2.0.0"

from .ml_endpoints import router as ml_router

__all__ = ['ml_router']