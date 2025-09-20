"""
🚀 AI Orchestration API Module - Microservice Implementation
Enterprise-grade API endpoints for AI orchestration microservice
"""

__version__ = "2.0.0"
__microservice__ = "ai-orchestration"

from .orchestration_endpoints import router as orchestration_router

__all__ = ['orchestration_router']