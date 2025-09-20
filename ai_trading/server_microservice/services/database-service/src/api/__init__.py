"""
Database Service API Layer
Centralized API management for all database operations
"""
__version__ = "2.0.0"

from .database_endpoints import (
    ClickHouseEndpoints,
    PostgreSQLEndpoints,
    ArangoDBEndpoints,
    WeaviateEndpoints,
    CacheEndpoints,
    SchemaEndpoints,
    HealthEndpoints
)

__all__ = [
    'ClickHouseEndpoints',
    'PostgreSQLEndpoints', 
    'ArangoDBEndpoints',
    'WeaviateEndpoints',
    'CacheEndpoints',
    'SchemaEndpoints',
    'HealthEndpoints'
]