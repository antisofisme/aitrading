"""
DragonflyDB Connection Manager
Redis-compatible in-memory cache with enhanced performance
"""
import redis.asyncio as redis
import logging
from typing import Any, Dict, Optional, List
from .base import BaseConnectionManager, DatabaseStatus

logger = logging.getLogger(__name__)


class DragonflyDBManager(BaseConnectionManager):
    """
    Connection manager for DragonflyDB (Redis-compatible)

    Features:
    - Async Redis protocol
    - Connection pooling
    - Pub/Sub support
    - TTL management
    - Multi-level caching
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client: Optional[redis.Redis] = None
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 6379)
        self.db = config.get('db', 0)
        self.password = config.get('password', None)
        self.max_connections = config.get('max_connections', 50)

    async def connect(self) -> bool:
        """Establish connection to DragonflyDB"""
        try:
            logger.info(f"🔌 Connecting to DragonflyDB at {self.host}:{self.port}/{self.db}")

            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
                max_connections=self.max_connections
            )

            # Test connection
            await self.client.ping()

            # Get server info
            info = await self.client.info('server')
            version = info.get('redis_version', 'unknown')

            logger.info(f"✅ DragonflyDB connected | Version: {version}")
            self._is_connected = True
            return True

        except Exception as e:
            logger.error(f"❌ DragonflyDB connection failed: {e}")
            self._is_connected = False
            return False

    async def disconnect(self) -> None:
        """Close DragonflyDB connection"""
        if self.client:
            await self.client.close()
            self.client = None
            self._is_connected = False
            logger.info("✅ DragonflyDB connection closed")

    async def health_check(self) -> Dict[str, Any]:
        """Check DragonflyDB health"""
        if not self._is_connected or not self.client:
            return {
                "status": DatabaseStatus.UNHEALTHY.value,
                "connected": False,
                "error": "Not connected"
            }

        try:
            # Ping
            await self.client.ping()

            # Get memory stats
            info = await self.client.info('memory')
            memory_used = info.get('used_memory_human', '0')
            memory_peak = info.get('used_memory_peak_human', '0')

            # Get key stats
            dbsize = await self.client.dbsize()

            return {
                "status": DatabaseStatus.HEALTHY.value,
                "connected": True,
                "keys": dbsize,
                "memory": {
                    "used": memory_used,
                    "peak": memory_peak
                }
            }

        except Exception as e:
            logger.error(f"❌ DragonflyDB health check failed: {e}")
            return {
                "status": DatabaseStatus.DEGRADED.value,
                "connected": True,
                "error": str(e)
            }

    async def initialize_schema(self, schema_path: str) -> bool:
        """
        Initialize cache schema (DragonflyDB doesn't need schema initialization)

        Returns:
            True (always successful for Redis-like databases)
        """
        logger.info("✅ DragonflyDB schema initialization not required (key-value store)")
        return True

    async def execute_query(self, query: str, *args, **kwargs) -> Any:
        """
        Execute Redis command

        Args:
            query: Redis command
            *args: Command arguments

        Returns:
            Command result
        """
        if not self._is_connected:
            raise ConnectionError("Not connected to DragonflyDB")

        try:
            # Split command into parts
            parts = query.split()
            command = parts[0].lower()

            # Execute based on command type
            if command == 'get':
                return await self.client.get(parts[1])
            elif command == 'set':
                return await self.client.set(parts[1], parts[2])
            elif command == 'del':
                return await self.client.delete(*parts[1:])
            else:
                # Generic command execution
                return await self.client.execute_command(*parts)

        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            raise

    # Convenience methods for common operations

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set key-value with optional TTL"""
        try:
            return await self.client.set(key, value, ex=ttl)
        except Exception as e:
            logger.error(f"Set failed for key {key}: {e}")
            return False

    async def get(self, key: str) -> Optional[Any]:
        """Get value by key"""
        try:
            return await self.client.get(key)
        except Exception as e:
            logger.error(f"Get failed for key {key}: {e}")
            return None

    async def delete(self, *keys: str) -> int:
        """Delete keys"""
        try:
            return await self.client.delete(*keys)
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Exists check failed for key {key}: {e}")
            return False

    async def expire(self, key: str, seconds: int) -> bool:
        """Set key expiration"""
        try:
            return await self.client.expire(key, seconds)
        except Exception as e:
            logger.error(f"Expire failed for key {key}: {e}")
            return False
