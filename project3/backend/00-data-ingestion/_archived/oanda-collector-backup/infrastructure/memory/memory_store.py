"""
Memory Store - Interface to Central Hub shared memory
"""
import logging
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)


class MemoryStore:
    """
    Interface to Central Hub memory store for shared state
    Allows coordination between multiple collector instances
    """

    def __init__(
        self,
        central_hub_client,
        namespace: str = "oanda-collector"
    ):
        """
        Initialize Memory Store

        Args:
            central_hub_client: Central Hub client instance
            namespace: Namespace prefix for keys
        """
        self.central_hub = central_hub_client
        self.namespace = namespace
        self.cache: Dict[str, Any] = {}

        logger.info(f"Memory store initialized with namespace: {namespace}")

    def _make_key(self, key: str) -> str:
        """
        Create namespaced key

        Args:
            key: Original key

        Returns:
            Namespaced key
        """
        return f"{self.namespace}:{key}"

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Store value in shared memory

        Args:
            key: Storage key
            value: Value to store (will be JSON encoded)
            ttl: Time to live in seconds (optional)

        Returns:
            bool: True if stored successfully
        """
        namespaced_key = self._make_key(key)

        try:
            # Store in local cache
            self.cache[namespaced_key] = value

            # TODO: Implement actual Central Hub memory API call
            # For now, we'll just use local cache
            # In production, this would call:
            # await self.central_hub.memory_set(namespaced_key, value, ttl)

            logger.debug(f"Stored in memory: {namespaced_key}")
            return True

        except Exception as e:
            logger.error(f"Error storing in memory: {e}")
            return False

    async def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve value from shared memory

        Args:
            key: Storage key
            default: Default value if key not found

        Returns:
            Stored value or default
        """
        namespaced_key = self._make_key(key)

        try:
            # Check local cache first
            if namespaced_key in self.cache:
                return self.cache[namespaced_key]

            # TODO: Implement actual Central Hub memory API call
            # For now, return default
            # In production, this would call:
            # value = await self.central_hub.memory_get(namespaced_key)

            return default

        except Exception as e:
            logger.error(f"Error retrieving from memory: {e}")
            return default

    async def delete(self, key: str) -> bool:
        """
        Delete value from shared memory

        Args:
            key: Storage key

        Returns:
            bool: True if deleted successfully
        """
        namespaced_key = self._make_key(key)

        try:
            # Remove from local cache
            if namespaced_key in self.cache:
                del self.cache[namespaced_key]

            # TODO: Implement actual Central Hub memory API call
            # await self.central_hub.memory_delete(namespaced_key)

            logger.debug(f"Deleted from memory: {namespaced_key}")
            return True

        except Exception as e:
            logger.error(f"Error deleting from memory: {e}")
            return False

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment counter in shared memory

        Args:
            key: Counter key
            amount: Increment amount

        Returns:
            New counter value or None on error
        """
        namespaced_key = self._make_key(key)

        try:
            current = await self.get(key, 0)
            new_value = current + amount
            await self.set(key, new_value)
            return new_value

        except Exception as e:
            logger.error(f"Error incrementing counter: {e}")
            return None

    async def acquire_lock(
        self,
        lock_key: str,
        ttl: int = 30,
        retry_count: int = 3
    ) -> bool:
        """
        Acquire distributed lock

        Args:
            lock_key: Lock identifier
            ttl: Lock time-to-live in seconds
            retry_count: Number of retry attempts

        Returns:
            bool: True if lock acquired
        """
        namespaced_key = self._make_key(f"lock:{lock_key}")

        for attempt in range(retry_count):
            try:
                # Check if lock exists
                existing = await self.get(f"lock:{lock_key}")

                if existing is None:
                    # Lock is available
                    await self.set(f"lock:{lock_key}", True, ttl=ttl)
                    logger.debug(f"Lock acquired: {lock_key}")
                    return True

                # Lock exists, wait and retry
                import asyncio
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error acquiring lock: {e}")

        logger.warning(f"Failed to acquire lock after {retry_count} attempts: {lock_key}")
        return False

    async def release_lock(self, lock_key: str) -> bool:
        """
        Release distributed lock

        Args:
            lock_key: Lock identifier

        Returns:
            bool: True if lock released
        """
        try:
            await self.delete(f"lock:{lock_key}")
            logger.debug(f"Lock released: {lock_key}")
            return True

        except Exception as e:
            logger.error(f"Error releasing lock: {e}")
            return False

    async def store_metrics(self, metrics: Dict[str, Any]) -> bool:
        """
        Store performance metrics

        Args:
            metrics: Metrics dictionary

        Returns:
            bool: True if stored successfully
        """
        import time
        timestamp = int(time.time())

        return await self.set(
            f"metrics:{timestamp}",
            metrics,
            ttl=3600  # Keep for 1 hour
        )

    async def get_recent_metrics(self, count: int = 10) -> list:
        """
        Get recent metrics entries

        Args:
            count: Number of recent entries to retrieve

        Returns:
            List of metrics dictionaries
        """
        # TODO: Implement range query when Central Hub API is available
        # For now, return empty list
        return []

    def clear_cache(self) -> None:
        """Clear local cache"""
        self.cache.clear()
        logger.info("Local cache cleared")
