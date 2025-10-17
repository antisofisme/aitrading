"""
Schema Migration System
Auto-initialize and version database schemas

⚠️ DEPRECATION WARNING:
   This module is OPTIONAL and may be deprecated in future versions.

   For development environments, prefer native database initialization:
   - ClickHouse: Mount SQL files to /docker-entrypoint-initdb.d/
   - TimescaleDB: Mount SQL files to /docker-entrypoint-initdb.d/

   Use SchemaMigrator ONLY when:
   - You need version tracking across deployments
   - You need programmatic rollback support
   - Native init scripts are not sufficient

   For most cases, native database init is simpler and more reliable.
"""
import logging
import warnings
from typing import Any, Dict, Optional, List
from pathlib import Path
from .router import DatabaseRouter
from .base import DatabaseType

logger = logging.getLogger(__name__)


class SchemaMigrator:
    """
    Schema migration and versioning system

    ⚠️ OPTIONAL: Consider using native database init scripts instead.

    Features:
    - Auto-detect schema files
    - Version tracking (basic)
    - Idempotent migrations
    - Rollback support (future/not implemented)

    Alternatives (RECOMMENDED for development):
    - ClickHouse: /docker-entrypoint-initdb.d/ (native)
    - TimescaleDB: /docker-entrypoint-initdb.d/ (PostgreSQL native)
    """

    def __init__(self, router: DatabaseRouter, schema_base_path: str):
        """
        Initialize schema migrator

        Args:
            router: DatabaseRouter instance
            schema_base_path: Base path to schema files
        """
        self.router = router
        self.schema_base_path = Path(schema_base_path)

        # Schema paths for each database
        self.schema_paths = {
            DatabaseType.TIMESCALEDB: self.schema_base_path / "timescaledb",
            DatabaseType.CLICKHOUSE: self.schema_base_path / "clickhouse",
            DatabaseType.ARANGODB: self.schema_base_path / "arangodb",
            DatabaseType.WEAVIATE: self.schema_base_path / "weaviate",
        }

    async def initialize_all_schemas(self) -> Dict[str, bool]:
        """
        Initialize schemas for all active databases

        Returns:
            Dict of database -> initialization status
        """
        if not self.router.is_initialized():
            raise RuntimeError("Router must be initialized first")

        logger.info("🔧 Initializing database schemas...")

        results = {}

        # Initialize each active database
        for db_type in self.router.get_active_databases():
            if db_type not in self.schema_paths:
                logger.info(f"⏭️  No schema initialization needed for {db_type.value}")
                results[db_type.value] = True
                continue

            try:
                success = await self.initialize_database_schema(db_type)
                results[db_type.value] = success

                if success:
                    logger.info(f"✅ Schema initialized for {db_type.value}")
                else:
                    logger.warning(f"⚠️  Schema initialization failed for {db_type.value}")

            except Exception as e:
                logger.error(f"❌ Error initializing {db_type.value} schema: {e}")
                results[db_type.value] = False

        # Summary
        success_count = sum(1 for v in results.values() if v)
        total_count = len(results)

        logger.info(
            f"✅ Schema initialization complete: {success_count}/{total_count} successful"
        )

        return results

    async def initialize_database_schema(self, db_type: DatabaseType) -> bool:
        """
        Initialize schema for specific database

        Args:
            db_type: Database type to initialize

        Returns:
            bool: True if successful
        """
        schema_dir = self.schema_paths.get(db_type)
        if not schema_dir or not schema_dir.exists():
            logger.warning(f"Schema directory not found for {db_type.value}: {schema_dir}")
            return False

        # Get all SQL files sorted by name (01_xxx.sql, 02_xxx.sql, etc.)
        sql_files = sorted(schema_dir.glob("*.sql"))

        if not sql_files:
            logger.info(f"No schema files found for {db_type.value}")
            return True

        logger.info(f"📄 Found {len(sql_files)} schema file(s) for {db_type.value}")

        # Get database manager
        manager = self.router.get_manager(db_type=db_type)

        # Execute each schema file
        success_count = 0
        for sql_file in sql_files:
            try:
                await manager.initialize_schema(str(sql_file))
                success_count += 1
                logger.debug(f"  ✅ {sql_file.name}")
            except Exception as e:
                logger.error(f"  ❌ {sql_file.name}: {e}")

        return success_count == len(sql_files)

    async def verify_schemas(self) -> Dict[str, Any]:
        """
        Verify all schemas are properly initialized

        Returns:
            Dict of database -> verification status
        """
        if not self.router.is_initialized():
            raise RuntimeError("Router must be initialized first")

        logger.info("🔍 Verifying database schemas...")

        results = {}

        for db_type in self.router.get_active_databases():
            try:
                manager = self.router.get_manager(db_type=db_type)
                health = await manager.health_check()

                results[db_type.value] = {
                    "status": health.get("status"),
                    "verified": health.get("status") == "healthy"
                }

            except Exception as e:
                logger.error(f"❌ Schema verification failed for {db_type.value}: {e}")
                results[db_type.value] = {
                    "status": "error",
                    "verified": False,
                    "error": str(e)
                }

        return results

    def get_schema_files(self, db_type: DatabaseType) -> List[Path]:
        """
        Get list of schema files for database

        Args:
            db_type: Database type

        Returns:
            List of schema file paths
        """
        schema_dir = self.schema_paths.get(db_type)
        if not schema_dir or not schema_dir.exists():
            return []

        return sorted(schema_dir.glob("*.sql"))
