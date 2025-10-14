"""
Central Hub SDK - Database Module
Unified database access layer with auto-initialization and smart routing
"""

from .router import DatabaseRouter
from .health import DatabaseHealthChecker
from .migrator import SchemaMigrator

__all__ = [
    "DatabaseRouter",
    "DatabaseHealthChecker",
    "SchemaMigrator",
]

__version__ = "2.0.0"
