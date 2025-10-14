"""
ClickHouse Connection Manager
Handles ClickHouse for analytics and OLAP queries
"""
import clickhouse_connect
import logging
from typing import Any, Dict, Optional, List
from pathlib import Path
from .base import BaseConnectionManager, DatabaseStatus

logger = logging.getLogger(__name__)


class ClickHouseManager(BaseConnectionManager):
    """
    Connection manager for ClickHouse analytics database

    Features:
    - HTTP/Native protocol support
    - Bulk insert optimization
    - Query caching
    - Compression support
    - Schema auto-initialization
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = None
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 8123)
        self.database = config.get('database', 'suho_analytics')
        self.user = config.get('user', 'default')
        self.password = config.get('password', '')
        self.secure = config.get('secure', False)
        self.compress = config.get('compress', True)

    async def connect(self) -> bool:
        """Establish connection to ClickHouse"""
        try:
            logger.info(f"🔌 Connecting to ClickHouse at {self.host}:{self.port}/{self.database}")

            # ClickHouse client is synchronous, wrap in executor for async
            import asyncio
            loop = asyncio.get_event_loop()

            self.client = await loop.run_in_executor(
                None,
                lambda: clickhouse_connect.get_client(
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    username=self.user,
                    password=self.password,
                    secure=self.secure,
                    compress=self.compress
                )
            )

            # Test connection
            result = await loop.run_in_executor(
                None,
                lambda: self.client.command("SELECT version()")
            )

            logger.info(f"✅ ClickHouse connected | Version: {result}")
            self._is_connected = True
            return True

        except Exception as e:
            logger.error(f"❌ ClickHouse connection failed: {e}")
            self._is_connected = False
            return False

    async def disconnect(self) -> None:
        """Close ClickHouse connection"""
        if self.client:
            self.client.close()
            self.client = None
            self._is_connected = False
            logger.info("✅ ClickHouse connection closed")

    async def health_check(self) -> Dict[str, Any]:
        """Check ClickHouse health"""
        if not self._is_connected or not self.client:
            return {
                "status": DatabaseStatus.UNHEALTHY.value,
                "connected": False,
                "error": "Not connected"
            }

        try:
            import asyncio
            loop = asyncio.get_event_loop()

            # Ping server
            await loop.run_in_executor(None, lambda: self.client.ping())

            # Get server stats
            result = await loop.run_in_executor(
                None,
                lambda: self.client.query(
                    """
                    SELECT
                        count() as total_databases,
                        formatReadableSize(sum(bytes)) as total_size
                    FROM system.tables
                    WHERE database = currentDatabase()
                    """
                )
            )

            row = result.first_row

            return {
                "status": DatabaseStatus.HEALTHY.value,
                "connected": True,
                "tables": row[0] if row else 0,
                "database_size": row[1] if row else "0 B"
            }

        except Exception as e:
            logger.error(f"❌ ClickHouse health check failed: {e}")
            return {
                "status": DatabaseStatus.DEGRADED.value,
                "connected": True,
                "error": str(e)
            }

    async def initialize_schema(self, schema_path: str) -> bool:
        """Initialize database schema from SQL file"""
        if not self._is_connected:
            logger.error("Cannot initialize schema: Not connected")
            return False

        try:
            sql_file = Path(schema_path)
            if not sql_file.exists():
                logger.error(f"Schema file not found: {schema_path}")
                return False

            sql_content = sql_file.read_text()

            import asyncio
            loop = asyncio.get_event_loop()

            # Execute schema SQL
            await loop.run_in_executor(
                None,
                lambda: self.client.command(sql_content)
            )

            logger.info(f"✅ Schema initialized from {sql_file.name}")
            return True

        except Exception as e:
            logger.error(f"❌ Schema initialization failed: {e}")
            return False

    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict] = None,
        settings: Optional[Dict] = None,
        **kwargs
    ) -> Any:
        """
        Execute ClickHouse query

        Args:
            query: SQL query
            parameters: Query parameters
            settings: ClickHouse-specific settings

        Returns:
            Query results
        """
        if not self._is_connected:
            raise ConnectionError("Not connected to ClickHouse")

        try:
            import asyncio
            loop = asyncio.get_event_loop()

            if kwargs.get('execute_only'):
                await loop.run_in_executor(
                    None,
                    lambda: self.client.command(query, parameters=parameters, settings=settings)
                )
                return None
            else:
                result = await loop.run_in_executor(
                    None,
                    lambda: self.client.query(query, parameters=parameters, settings=settings)
                )
                return result.result_rows

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

    async def insert_bulk(
        self,
        table: str,
        data: List[List[Any]],
        column_names: Optional[List[str]] = None
    ) -> int:
        """
        Bulk insert data into ClickHouse table

        Args:
            table: Table name
            data: List of rows to insert
            column_names: Optional column names

        Returns:
            Number of rows inserted
        """
        if not self._is_connected:
            raise ConnectionError("Not connected to ClickHouse")

        try:
            import asyncio
            loop = asyncio.get_event_loop()

            await loop.run_in_executor(
                None,
                lambda: self.client.insert(table, data, column_names=column_names)
            )

            logger.debug(f"✅ Inserted {len(data)} rows into {table}")
            return len(data)

        except Exception as e:
            logger.error(f"Bulk insert failed: {e}")
            raise
