"""
Central Hub SDK for Python v2.0

Official client library for integrating services with Suho Central Hub.
Now with comprehensive multi-database support and auto-initialization!

Basic Usage:
    from central_hub_sdk import CentralHubClient, ProgressLogger

    # Service registration
    client = CentralHubClient(
        service_name="my-service",
        service_type="data-collector",
        version="1.0.0"
    )

    await client.register()
    await client.start_heartbeat_loop()

Database SDK Usage (v2.0):
    from central_hub_sdk import DatabaseRouter, SchemaMigrator, DatabaseHealthChecker

    # Initialize all databases with auto-schema creation
    config = {
        'timescaledb': {'host': 'localhost', 'port': 5432, ...},
        'clickhouse': {'host': 'localhost', 'port': 8123, ...},
        'dragonflydb': {'host': 'localhost', 'port': 6379, ...},
    }

    router = DatabaseRouter(config)
    await router.initialize()

    # Auto-initialize schemas from SQL files
    migrator = SchemaMigrator(router, schema_base_path="/path/to/schemas")
    await migrator.initialize_all_schemas()

    # Check health
    health_checker = DatabaseHealthChecker(router)
    report = await health_checker.check_all()
"""

__version__ = "2.0.0"
__author__ = "Suho Trading System"

# Legacy components (v1.x)
from .client import CentralHubClient
from .progress_logger import ProgressLogger
from .heartbeat_logger import HeartbeatLogger

# Database SDK components (v2.0)
from .database import (
    DatabaseRouter,
    DatabaseHealthChecker,
    SchemaMigrator,
)

__all__ = [
    # Legacy
    'CentralHubClient',
    'ProgressLogger',
    'HeartbeatLogger',
    # Database SDK
    'DatabaseRouter',
    'DatabaseHealthChecker',
    'SchemaMigrator',
]
