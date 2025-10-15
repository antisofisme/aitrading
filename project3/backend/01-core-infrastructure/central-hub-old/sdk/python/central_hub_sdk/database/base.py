"""
Base Connection Manager Interface
All database managers must implement this interface
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DatabaseType(Enum):
    """Supported database types"""
    TIMESCALEDB = "timescaledb"
    CLICKHOUSE = "clickhouse"
    DRAGONFLYDB = "dragonflydb"
    ARANGODB = "arangodb"
    WEAVIATE = "weaviate"


class DatabaseStatus(Enum):
    """Database connection status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class BaseConnectionManager(ABC):
    """
    Base class for all database connection managers

    Each database manager must implement:
    - Connection lifecycle (connect, disconnect, reconnect)
    - Health checking
    - Schema initialization
    - Query execution with retry logic
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize connection manager

        Args:
            config: Database-specific configuration
        """
        self.config = config
        self.connection = None
        self._is_connected = False
        self._retry_count = 0
        self._max_retries = config.get('max_retries', 3)
        self._retry_delay = config.get('retry_delay', 5)

    @property
    def is_connected(self) -> bool:
        """Check if connection is active"""
        return self._is_connected

    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to database

        Returns:
            bool: True if connection successful
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close database connection"""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check database health

        Returns:
            dict: Health status information
        """
        pass

    @abstractmethod
    async def initialize_schema(self, schema_path: str) -> bool:
        """
        Initialize database schema from SQL/config file

        Args:
            schema_path: Path to schema definition file

        Returns:
            bool: True if initialization successful
        """
        pass

    @abstractmethod
    async def execute_query(self, query: str, *args, **kwargs) -> Any:
        """
        Execute database query with retry logic

        Args:
            query: Query string
            *args: Query parameters
            **kwargs: Additional options

        Returns:
            Query results
        """
        pass

    async def reconnect(self) -> bool:
        """
        Reconnect to database with retry logic

        Returns:
            bool: True if reconnection successful
        """
        logger.info(f"Attempting to reconnect to {self.__class__.__name__}...")

        await self.disconnect()

        for attempt in range(self._max_retries):
            try:
                if await self.connect():
                    logger.info(f"✅ Reconnection successful on attempt {attempt + 1}")
                    self._retry_count = 0
                    return True
            except Exception as e:
                logger.warning(
                    f"Reconnection attempt {attempt + 1}/{self._max_retries} failed: {e}"
                )
                if attempt < self._max_retries - 1:
                    import asyncio
                    await asyncio.sleep(self._retry_delay)

        logger.error(f"❌ Failed to reconnect after {self._max_retries} attempts")
        return False

    def get_status(self) -> DatabaseStatus:
        """
        Get current connection status

        Returns:
            DatabaseStatus: Current status
        """
        if not self._is_connected:
            return DatabaseStatus.UNHEALTHY

        if self._retry_count > 0:
            return DatabaseStatus.DEGRADED

        return DatabaseStatus.HEALTHY

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} connected={self._is_connected}>"
