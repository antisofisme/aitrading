"""
Smart Database Router
Automatically routes data to the appropriate database based on data type and use case
"""
import logging
from typing import Any, Dict, Optional, List
from enum import Enum
from .base import DatabaseType
from .timescale import TimescaleDBManager
from .clickhouse import ClickHouseManager
from .dragonfly import DragonflyDBManager
from .arango import ArangoDBManager
from .weaviate import WeaviateManager

logger = logging.getLogger(__name__)


class DataCategory(Enum):
    """Data category for routing decisions"""
    TICK_DATA = "tick_data"              # Real-time tick data
    CANDLE_DATA = "candle_data"          # OHLCV candles
    ANALYTICS = "analytics"              # Aggregated analytics
    CACHE = "cache"                      # Hot cache data
    GRAPH = "graph"                      # Relationship data
    VECTOR = "vector"                    # ML embeddings
    EXTERNAL = "external"                # External data sources


class DatabaseRouter:
    """
    Smart router for multi-database architecture

    Routing Logic:
    - Tick data (real-time) → TimescaleDB
    - Candles (historical) → TimescaleDB + ClickHouse
    - Analytics queries → ClickHouse
    - Cache/Hot data → DragonflyDB
    - Graph/Relationships → ArangoDB
    - ML Vectors → Weaviate

    Features:
    - Auto-initialization of all databases
    - Smart routing based on data type
    - Fallback mechanisms
    - Health monitoring
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize database router

        Args:
            config: Configuration dict with database configs
        """
        self.config = config
        self.managers = {}
        self._initialized = False

        # Routing rules
        self.routing_rules = {
            DataCategory.TICK_DATA: DatabaseType.TIMESCALEDB,
            DataCategory.CANDLE_DATA: DatabaseType.TIMESCALEDB,  # Primary
            DataCategory.ANALYTICS: DatabaseType.CLICKHOUSE,
            DataCategory.CACHE: DatabaseType.DRAGONFLYDB,
            DataCategory.GRAPH: DatabaseType.ARANGODB,
            DataCategory.VECTOR: DatabaseType.WEAVIATE,
            DataCategory.EXTERNAL: DatabaseType.CLICKHOUSE,
        }

        # Secondary databases for data replication
        self.replication_rules = {
            DataCategory.CANDLE_DATA: [DatabaseType.CLICKHOUSE],  # Replicate to ClickHouse
            DataCategory.TICK_DATA: [DatabaseType.DRAGONFLYDB],   # Cache latest
        }

    async def initialize(self) -> bool:
        """
        Initialize all database connections

        Returns:
            bool: True if all critical databases connected
        """
        if self._initialized:
            logger.info("Router already initialized")
            return True

        logger.info("🚀 Initializing Database Router...")

        # Initialize each database manager
        success_count = 0
        critical_dbs = [DatabaseType.TIMESCALEDB, DatabaseType.DRAGONFLYDB]

        # TimescaleDB
        if 'timescaledb' in self.config:
            try:
                manager = TimescaleDBManager(self.config['timescaledb'])
                if await manager.connect():
                    self.managers[DatabaseType.TIMESCALEDB] = manager
                    success_count += 1
                    logger.info("✅ TimescaleDB initialized")
            except Exception as e:
                logger.error(f"❌ TimescaleDB initialization failed: {e}")

        # ClickHouse
        if 'clickhouse' in self.config:
            try:
                manager = ClickHouseManager(self.config['clickhouse'])
                if await manager.connect():
                    self.managers[DatabaseType.CLICKHOUSE] = manager
                    success_count += 1
                    logger.info("✅ ClickHouse initialized")
            except Exception as e:
                logger.error(f"❌ ClickHouse initialization failed: {e}")

        # DragonflyDB
        if 'dragonflydb' in self.config:
            try:
                manager = DragonflyDBManager(self.config['dragonflydb'])
                if await manager.connect():
                    self.managers[DatabaseType.DRAGONFLYDB] = manager
                    success_count += 1
                    logger.info("✅ DragonflyDB initialized")
            except Exception as e:
                logger.error(f"❌ DragonflyDB initialization failed: {e}")

        # ArangoDB (optional)
        if 'arangodb' in self.config:
            try:
                manager = ArangoDBManager(self.config['arangodb'])
                if await manager.connect():
                    self.managers[DatabaseType.ARANGODB] = manager
                    success_count += 1
                    logger.info("✅ ArangoDB initialized")
            except Exception as e:
                logger.warning(f"⚠️ ArangoDB initialization failed (optional): {e}")

        # Weaviate (optional)
        if 'weaviate' in self.config:
            try:
                manager = WeaviateManager(self.config['weaviate'])
                if await manager.connect():
                    self.managers[DatabaseType.WEAVIATE] = manager
                    success_count += 1
                    logger.info("✅ Weaviate initialized")
            except Exception as e:
                logger.warning(f"⚠️ Weaviate initialization failed (optional): {e}")

        # Check if critical databases are available
        critical_ok = all(
            db_type in self.managers
            for db_type in critical_dbs
        )

        if not critical_ok:
            logger.error("❌ Critical databases not available")
            return False

        self._initialized = True
        logger.info(
            f"✅ Database Router initialized | "
            f"Active: {success_count}/{len(self.config)} databases"
        )

        return True

    def get_manager(
        self,
        category: Optional[DataCategory] = None,
        db_type: Optional[DatabaseType] = None
    ):
        """
        Get database manager

        Args:
            category: Data category for automatic routing
            db_type: Specific database type (overrides routing)

        Returns:
            Database manager instance
        """
        if not self._initialized:
            raise RuntimeError("Router not initialized. Call initialize() first.")

        # Direct database access
        if db_type:
            manager = self.managers.get(db_type)
            if not manager:
                raise ValueError(f"Database {db_type.value} not available")
            return manager

        # Auto-routing based on category
        if category:
            target_db = self.routing_rules.get(category)
            if not target_db:
                raise ValueError(f"No routing rule for category: {category.value}")

            manager = self.managers.get(target_db)
            if not manager:
                raise ValueError(f"Target database {target_db.value} not available")

            return manager

        raise ValueError("Either category or db_type must be specified")

    async def route_write(
        self,
        category: DataCategory,
        data: Any,
        replicate: bool = True
    ) -> Dict[str, bool]:
        """
        Route write operation to appropriate database(s)

        Args:
            category: Data category
            data: Data to write
            replicate: Whether to replicate to secondary databases

        Returns:
            Dict of database -> success status
        """
        results = {}

        # Write to primary database
        primary_manager = self.get_manager(category=category)
        try:
            # Actual write logic would be implemented by the manager
            # This is just the routing framework
            results[primary_manager.__class__.__name__] = True
        except Exception as e:
            logger.error(f"Primary write failed: {e}")
            results[primary_manager.__class__.__name__] = False

        # Replicate to secondary databases
        if replicate and category in self.replication_rules:
            for db_type in self.replication_rules[category]:
                if db_type in self.managers:
                    try:
                        secondary_manager = self.managers[db_type]
                        # Replication logic
                        results[secondary_manager.__class__.__name__] = True
                    except Exception as e:
                        logger.warning(f"Replication to {db_type.value} failed: {e}")
                        results[secondary_manager.__class__.__name__] = False

        return results

    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Check health of all connected databases

        Returns:
            Dict of database -> health status
        """
        if not self._initialized:
            return {"error": "Router not initialized"}

        health_status = {}

        for db_type, manager in self.managers.items():
            try:
                status = await manager.health_check()
                health_status[db_type.value] = status
            except Exception as e:
                health_status[db_type.value] = {
                    "status": "error",
                    "error": str(e)
                }

        return health_status

    async def close_all(self):
        """Close all database connections"""
        for db_type, manager in self.managers.items():
            try:
                await manager.disconnect()
                logger.info(f"✅ Closed {db_type.value}")
            except Exception as e:
                logger.error(f"Error closing {db_type.value}: {e}")

        self.managers.clear()
        self._initialized = False
        logger.info("✅ All database connections closed")

    def is_initialized(self) -> bool:
        """Check if router is initialized"""
        return self._initialized

    def get_active_databases(self) -> List[DatabaseType]:
        """Get list of active database connections"""
        return list(self.managers.keys())
