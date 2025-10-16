"""
Central Hub SDK - Database Module
Unified database connection management and smart routing

Features:
- DatabaseRouter: Multi-database connection management with smart routing
- DatabaseHealthChecker: Health monitoring for all databases
- SchemaMigrator: OPTIONAL - Schema version management (see note below)

⚠️ IMPORTANT: Schema Management
   Schema creation is handled by SQL files, not this SDK:
   - ClickHouse: central-hub/shared/schemas/clickhouse/*.sql
   - TimescaleDB: central-hub/shared/schemas/timescaledb/*.sql

   For development (frequent Docker restarts):
   → Use native database init scripts (/docker-entrypoint-initdb.d/)
   → SchemaMigrator is OPTIONAL and may be overkill

   Use SchemaMigrator ONLY when:
   - You need version tracking across deployments
   - You need programmatic schema management
   - Native init scripts are not sufficient

Recommended Usage:
    from central_hub_sdk.database import DatabaseRouter

    # Initialize router with config
    router = DatabaseRouter(config)
    await router.initialize()  # Connect to databases

    # Get database manager
    clickhouse = router.get_manager(db_type=DatabaseType.CLICKHOUSE)

    # Tables already created by native init scripts
    await clickhouse.execute("INSERT INTO ticks ...")

Version: 2.0.0
"""

from .router import DatabaseRouter
from .health import DatabaseHealthChecker
from .migrator import SchemaMigrator  # OPTIONAL - see docstring above

__all__ = [
    "DatabaseRouter",           # CORE: Connection management
    "DatabaseHealthChecker",    # CORE: Health monitoring
    "SchemaMigrator",          # OPTIONAL: Schema version management (prefer native init)
]

__version__ = "2.0.0"
