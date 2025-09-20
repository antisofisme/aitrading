"""
Database Service - Enterprise Multi-Database Management
Centralized data persistence and operations for all 6 database types
"""
__version__ = "2.0.0"
__service_name__ = "database-service"

# Core business logic - temporarily disabled for startup
# from .business.database_manager import DatabaseManager  # Temporarily disabled
# from .business.connection_factory import ConnectionFactory
# from .business.query_builder import QueryBuilder
# from .business.migration_manager import MigrationManager

# API layer - temporarily disabled
# from .api.database_endpoints import (
#     ClickHouseEndpoints,
#     PostgreSQLEndpoints,
#     ArangoDBEndpoints,
#     WeaviateEndpoints,
#     CacheEndpoints,
#     SchemaEndpoints,
#     HealthEndpoints
# )

# Infrastructure (shared components) - temporarily disabled for startup
# from .infrastructure.core.logger_core import get_logger
# from .infrastructure.core.config_core import get_config
# from .infrastructure.core.error_core import get_error_handler
# from .infrastructure.core.performance_core import get_performance_tracker
# from .infrastructure.core.cache_core import CoreCache

__all__ = [
    # Core business logic - temporarily disabled for startup
    # 'DatabaseManager',
    # 'ConnectionFactory',
    # 'QueryBuilder', 
    # 'MigrationManager',
    
    # API endpoints - temporarily disabled
    # 'ClickHouseEndpoints',
    # 'PostgreSQLEndpoints',
    # 'ArangoDBEndpoints',
    # 'WeaviateEndpoints',
    # 'CacheEndpoints',
    # 'SchemaEndpoints',
    # 'HealthEndpoints',
    
    # Infrastructure utilities - temporarily disabled
    # 'get_logger',
    # 'get_config',
    # 'get_error_handler', 
    # 'get_performance_tracker',
    # 'CoreCache'
]

# Service metadata
__databases__ = [
    "postgresql", "clickhouse", "arangodb", 
    "weaviate", "dragonflydb", "redpanda"
]

__capabilities__ = [
    "multi_database_operations",
    "connection_pooling", 
    "query_optimization",
    "schema_migration",
    "mt5_bridge_integration",
    "high_frequency_tick_processing"
]
