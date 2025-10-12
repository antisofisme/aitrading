"""
Database Connection Pool Manager
Centralized connection management for all databases
Phase 1: PostgreSQL/TimescaleDB + DragonflyDB
"""
import os
import json
import asyncio
import asyncpg
import redis.asyncio as redis
from typing import Dict, Optional, Any
from pathlib import Path
from .exceptions import (
    DatabaseConnectionError,
    ConfigurationError,
    ConnectionPoolExhaustedError
)


class DatabasePoolManager:
    """
    Manage connection pools for all databases
    Phase 1: TimescaleDB + DragonflyDB
    Phase 2: ClickHouse (coming soon)
    Phase 3: Weaviate + ArangoDB (coming soon)
    """

    def __init__(self, configs: Optional[Dict[str, Any]] = None):
        self.pools: Dict[str, Any] = {}
        self.configs: Dict[str, Dict] = {}
        self._external_configs = configs  # Configs from Central Hub
        self._initialized = False

    async def initialize(self):
        """Initialize all database connection pools"""
        if self._initialized:
            return

        try:
            # Load configurations
            await self._load_configs()

            # Initialize connection pools
            await self._init_timescale_pool()
            await self._init_dragonfly_pool()

            self._initialized = True
            print("✅ Database pools initialized successfully")

        except Exception as e:
            print(f"❌ Failed to initialize database pools: {e}")
            raise ConfigurationError("database_pools", str(e))

    async def _load_configs(self):
        """
        Load database configurations
        Priority:
        1. External configs from Central Hub (already resolved env vars)
        2. Static files from shared/static/database/
        """
        # If external configs provided (from Central Hub), use them
        if self._external_configs:
            print("✅ Using database configs from Central Hub")

            # Map Central Hub config names to internal names
            if 'postgresql' in self._external_configs:
                self.configs['timescale'] = self._external_configs['postgresql']

            if 'dragonflydb' in self._external_configs:
                self.configs['dragonfly'] = self._external_configs['dragonflydb']

            return

        # Fallback: Load from static files
        print("⚠️  Loading database configs from static files (fallback)")
        config_dir = Path(__file__).parent.parent.parent / "static" / "database"

        # Load PostgreSQL config
        pg_config_file = config_dir / "postgresql.json"
        if pg_config_file.exists():
            with open(pg_config_file) as f:
                self.configs['timescale'] = json.load(f)
        else:
            raise ConfigurationError("postgresql", f"Config file not found: {pg_config_file}")

        # Load DragonflyDB config
        df_config_file = config_dir / "dragonflydb.json"
        if df_config_file.exists():
            with open(df_config_file) as f:
                self.configs['dragonfly'] = json.load(f)
        else:
            raise ConfigurationError("dragonflydb", f"Config file not found: {df_config_file}")

    def _resolve_env(self, value: str) -> str:
        """Resolve environment variable patterns: ENV:VAR_NAME or ${VAR_NAME}"""
        # If not a string, return as-is (already resolved)
        if not isinstance(value, str):
            return value

        # Pattern 1: ENV:VAR_NAME
        if value.startswith("ENV:"):
            env_var = value[4:]  # Remove "ENV:" prefix
            env_value = os.getenv(env_var)
            if env_value is None:
                raise ConfigurationError("environment", f"Environment variable {env_var} not set")
            return env_value

        # Pattern 2: ${VAR_NAME} or $VAR_NAME
        if "${" in value or value.startswith("$"):
            import re
            # Replace ${VAR_NAME} with actual value
            def replacer(match):
                var_name = match.group(1)
                env_value = os.getenv(var_name)
                if env_value is None:
                    raise ConfigurationError("environment", f"Environment variable {var_name} not set")
                return env_value

            # Handle ${VAR_NAME}
            value = re.sub(r'\$\{([^}]+)\}', replacer, value)
            # Handle $VAR_NAME (word boundary)
            value = re.sub(r'\$([A-Z_][A-Z0-9_]*)', replacer, value)

        return value

    async def _init_timescale_pool(self):
        """Initialize PostgreSQL/TimescaleDB connection pool"""
        try:
            config = self.configs['timescale']
            conn_config = config['connection']
            pool_config = config['pool']

            # Resolve environment variables
            host = self._resolve_env(conn_config['host'])
            port = int(self._resolve_env(conn_config['port']))
            database = self._resolve_env(conn_config['database'])
            user = self._resolve_env(conn_config['user'])
            password = self._resolve_env(conn_config['password'])

            # Create connection pool
            self.pools['timescale'] = await asyncpg.create_pool(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
                min_size=pool_config['min'],
                max_size=pool_config['max'],
                timeout=pool_config['acquire_timeout'] / 1000,  # Convert ms to seconds
                command_timeout=pool_config['idle_timeout'] / 1000
            )

            print(f"✅ TimescaleDB pool initialized ({pool_config['min']}-{pool_config['max']} connections)")

        except Exception as e:
            raise DatabaseConnectionError("timescale", str(e))

    async def _init_dragonfly_pool(self):
        """Initialize DragonflyDB (Redis-compatible) connection pool"""
        try:
            config = self.configs['dragonfly']
            conn_config = config['connection']
            pool_config = config['pool']

            # Resolve environment variables
            host = self._resolve_env(conn_config['host'])
            port = int(self._resolve_env(conn_config['port']))
            password = self._resolve_env(conn_config['password'])
            db = conn_config.get('database', 0)

            # Create Redis connection pool
            self.pools['dragonfly'] = redis.ConnectionPool(
                host=host,
                port=port,
                password=password,
                db=db,
                max_connections=pool_config['max_connections'],
                retry_on_timeout=pool_config.get('retry_on_timeout', True),
                socket_timeout=pool_config.get('connection_timeout', 5000) / 1000,
                socket_connect_timeout=pool_config.get('connection_timeout', 5000) / 1000
            )

            # Test connection
            client = redis.Redis(connection_pool=self.pools['dragonfly'])
            await client.ping()
            await client.close()

            print(f"✅ DragonflyDB pool initialized (max {pool_config['max_connections']} connections)")

        except Exception as e:
            raise DatabaseConnectionError("dragonfly", str(e))

    async def get_timescale_connection(self):
        """Get PostgreSQL/TimescaleDB connection from pool"""
        if 'timescale' not in self.pools:
            raise DatabaseConnectionError("timescale", "Pool not initialized")

        try:
            return await self.pools['timescale'].acquire()
        except asyncio.TimeoutError:
            pool_config = self.configs['timescale']['pool']
            raise ConnectionPoolExhaustedError(
                "timescale",
                pool_config['max'],
                pool_config['acquire_timeout'] // 1000
            )

    async def release_timescale_connection(self, conn):
        """Release PostgreSQL/TimescaleDB connection back to pool"""
        if 'timescale' in self.pools:
            await self.pools['timescale'].release(conn)

    def get_dragonfly_client(self) -> redis.Redis:
        """Get DragonflyDB client (Redis-compatible)"""
        if 'dragonfly' not in self.pools:
            raise DatabaseConnectionError("dragonfly", "Pool not initialized")

        return redis.Redis(connection_pool=self.pools['dragonfly'])

    async def health_check_all(self) -> Dict[str, str]:
        """Check health of all database connections"""
        health = {}

        # TimescaleDB health check
        try:
            conn = await self.get_timescale_connection()
            await conn.fetchval("SELECT 1")
            await self.release_timescale_connection(conn)
            health['timescale'] = "healthy"
        except Exception as e:
            health['timescale'] = f"unhealthy: {str(e)[:100]}"

        # DragonflyDB health check
        try:
            client = self.get_dragonfly_client()
            await client.ping()
            await client.close()
            health['dragonfly'] = "healthy"
        except Exception as e:
            health['dragonfly'] = f"unhealthy: {str(e)[:100]}"

        return health

    async def close_all(self):
        """Close all database connection pools gracefully"""
        # Close TimescaleDB pool
        if 'timescale' in self.pools:
            await self.pools['timescale'].close()
            print("✅ TimescaleDB pool closed")

        # Close DragonflyDB pool
        if 'dragonfly' in self.pools:
            await self.pools['dragonfly'].disconnect()
            print("✅ DragonflyDB pool closed")

        self._initialized = False


# Singleton instance
_pool_manager = None


async def get_pool_manager(configs: Optional[Dict[str, Any]] = None) -> DatabasePoolManager:
    """
    Get or create singleton pool manager instance

    Args:
        configs: Optional database configs from Central Hub
                 Format: {'postgresql': {...}, 'clickhouse': {...}, 'dragonflydb': {...}}
    """
    global _pool_manager
    if _pool_manager is None:
        _pool_manager = DatabasePoolManager(configs=configs)
        await _pool_manager.initialize()
    return _pool_manager
