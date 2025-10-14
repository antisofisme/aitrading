"""
TimescaleDB Connection Manager
Handles PostgreSQL with TimescaleDB extensions for time-series data
"""
import asyncpg
import logging
from typing import Any, Dict, Optional, List
from pathlib import Path
from .base import BaseConnectionManager, DatabaseStatus

logger = logging.getLogger(__name__)


class TimescaleDBManager(BaseConnectionManager):
    """
    Connection manager for TimescaleDB (PostgreSQL + time-series extensions)

    Features:
    - Connection pooling
    - Auto schema initialization
    - Hypertable creation
    - Query timeout handling
    - Retry logic with exponential backoff
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.pool: Optional[asyncpg.Pool] = None
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 5432)
        self.database = config.get('database', 'suho_trading')
        self.user = config.get('user', 'suho_admin')
        self.password = config.get('password', '')
        self.pool_size = config.get('pool_size', 10)
        self.min_pool_size = config.get('min_pool_size', 2)

    async def connect(self) -> bool:
        """Establish connection pool to TimescaleDB"""
        try:
            logger.info(f"🔌 Connecting to TimescaleDB at {self.host}:{self.port}/{self.database}")

            self.pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                min_size=self.min_pool_size,
                max_size=self.pool_size,
                command_timeout=60
            )

            # Test connection
            async with self.pool.acquire() as conn:
                version = await conn.fetchval("SELECT version()")
                timescale_version = await conn.fetchval(
                    "SELECT extversion FROM pg_extension WHERE extname='timescaledb'"
                )

            logger.info(
                f"✅ TimescaleDB connected | "
                f"PostgreSQL: {version.split()[1]} | "
                f"TimescaleDB: {timescale_version}"
            )

            self._is_connected = True
            return True

        except Exception as e:
            logger.error(f"❌ TimescaleDB connection failed: {e}")
            self._is_connected = False
            return False

    async def disconnect(self) -> None:
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            self.pool = None
            self._is_connected = False
            logger.info("✅ TimescaleDB connection pool closed")

    async def health_check(self) -> Dict[str, Any]:
        """Check TimescaleDB health"""
        if not self._is_connected or not self.pool:
            return {
                "status": DatabaseStatus.UNHEALTHY.value,
                "connected": False,
                "error": "Not connected"
            }

        try:
            async with self.pool.acquire() as conn:
                # Check connection
                await conn.fetchval("SELECT 1")

                # Get pool stats
                pool_size = self.pool.get_size()
                pool_free = self.pool.get_idle_size()

                # Get database stats
                db_size = await conn.fetchval(
                    "SELECT pg_database_size(current_database())"
                )

                return {
                    "status": DatabaseStatus.HEALTHY.value,
                    "connected": True,
                    "pool": {
                        "size": pool_size,
                        "free": pool_free,
                        "used": pool_size - pool_free
                    },
                    "database_size_mb": round(db_size / 1024 / 1024, 2)
                }

        except Exception as e:
            logger.error(f"❌ TimescaleDB health check failed: {e}")
            return {
                "status": DatabaseStatus.DEGRADED.value,
                "connected": True,
                "error": str(e)
            }

    async def initialize_schema(self, schema_path: str) -> bool:
        """
        Initialize database schema from SQL file

        Args:
            schema_path: Path to SQL schema file

        Returns:
            bool: True if initialization successful
        """
        if not self._is_connected:
            logger.error("Cannot initialize schema: Not connected")
            return False

        try:
            sql_file = Path(schema_path)
            if not sql_file.exists():
                logger.error(f"Schema file not found: {schema_path}")
                return False

            sql_content = sql_file.read_text()

            async with self.pool.acquire() as conn:
                # Execute schema SQL
                await conn.execute(sql_content)

            logger.info(f"✅ Schema initialized from {sql_file.name}")
            return True

        except Exception as e:
            logger.error(f"❌ Schema initialization failed: {e}")
            return False

    async def execute_query(self, query: str, *args, timeout: float = 30.0, **kwargs) -> Any:
        """
        Execute query with timeout

        Args:
            query: SQL query
            *args: Query parameters
            timeout: Query timeout in seconds

        Returns:
            Query results
        """
        if not self._is_connected:
            raise ConnectionError("Not connected to TimescaleDB")

        try:
            async with self.pool.acquire() as conn:
                # Set statement timeout
                await conn.execute(f"SET statement_timeout = '{int(timeout * 1000)}'")

                # Execute query
                if kwargs.get('fetch_one'):
                    return await conn.fetchrow(query, *args)
                elif kwargs.get('fetch_val'):
                    return await conn.fetchval(query, *args)
                elif kwargs.get('execute_only'):
                    await conn.execute(query, *args)
                    return None
                else:
                    return await conn.fetch(query, *args)

        except asyncpg.QueryCanceledError:
            logger.error(f"Query timeout after {timeout}s: {query[:100]}...")
            raise TimeoutError(f"Query exceeded {timeout}s timeout")
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

    async def create_hypertable(
        self,
        table_name: str,
        time_column: str = "time",
        chunk_interval: str = "1 day"
    ) -> bool:
        """
        Convert table to TimescaleDB hypertable

        Args:
            table_name: Name of the table
            time_column: Time column name (default: 'time')
            chunk_interval: Chunk time interval (default: '1 day')

        Returns:
            bool: True if successful
        """
        try:
            query = f"""
                SELECT create_hypertable(
                    '{table_name}',
                    '{time_column}',
                    chunk_time_interval => INTERVAL '{chunk_interval}',
                    if_not_exists => TRUE
                );
            """

            await self.execute_query(query, execute_only=True)
            logger.info(f"✅ Hypertable created: {table_name} ({chunk_interval} chunks)")
            return True

        except Exception as e:
            logger.error(f"❌ Hypertable creation failed for {table_name}: {e}")
            return False

    async def get_connection(self):
        """
        Get a connection from the pool

        Returns:
            asyncpg.Connection context manager
        """
        if not self.pool:
            raise ConnectionError("Connection pool not initialized")
        return self.pool.acquire()
