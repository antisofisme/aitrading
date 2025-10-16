"""
MultiLevelCache - 2-Tier Caching System
L1: In-memory cache (fast, limited size)
L2: DragonflyDB/Redis cache (slower, larger capacity)

This is a specialized cache for data_manager, not the general-purpose CacheManager.
"""
import asyncio
import json
import time
from typing import Any, Optional, Dict
from collections import OrderedDict
import redis.asyncio as aioredis


class L1Cache:
    """L1 in-memory cache with TTL and LRU eviction (no external dependencies)"""

    def __init__(self, max_size: int = 1000, ttl: int = 60):
        self.max_size = max_size
        self.ttl = ttl
        self._cache = OrderedDict()  # Key -> (value, expire_time)

    def get(self, key: str) -> Optional[Any]:
        """Get value if exists and not expired"""
        if key in self._cache:
            value, expire_time = self._cache[key]
            if time.time() < expire_time:
                # Move to end (LRU)
                self._cache.move_to_end(key)
                return value
            else:
                # Expired - remove
                del self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value with TTL"""
        # Remove oldest if at capacity
        if key not in self._cache and len(self._cache) >= self.max_size:
            self._cache.popitem(last=False)  # Remove oldest

        ttl_to_use = ttl if ttl is not None else self.ttl
        expire_time = time.time() + ttl_to_use
        self._cache[key] = (value, expire_time)
        self._cache.move_to_end(key)

    def delete(self, key: str) -> bool:
        """Delete key"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def __contains__(self, key: str) -> bool:
        """Check if key exists and not expired"""
        return self.get(key) is not None

    def __len__(self) -> int:
        """Get cache size"""
        return len(self._cache)

    def clear(self):
        """Clear all entries"""
        self._cache.clear()


class L2Cache:
    """L2 Redis/DragonflyDB cache"""

    def __init__(self, redis_client: aioredis.Redis, namespace: str = "data_cache"):
        self.redis_client = redis_client
        self.namespace = namespace

    def _make_key(self, key: str) -> str:
        """Create namespaced key"""
        return f"{self.namespace}:{key}"

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        try:
            redis_key = self._make_key(key)
            value_str = await self.redis_client.get(redis_key)
            if value_str:
                return json.loads(value_str)
            return None
        except Exception:
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in Redis with TTL"""
        try:
            redis_key = self._make_key(key)
            value_str = json.dumps(value, default=str)
            await self.redis_client.setex(redis_key, ttl, value_str)
            return True
        except Exception:
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        try:
            redis_key = self._make_key(key)
            result = await self.redis_client.delete(redis_key)
            return result > 0
        except Exception:
            return False

    async def clear(self, pattern: str = "*") -> int:
        """Clear keys matching pattern"""
        try:
            redis_pattern = self._make_key(pattern)
            keys = await self.redis_client.keys(redis_pattern)
            if keys:
                await self.redis_client.delete(*keys)
                return len(keys)
            return 0
        except Exception:
            return 0


class MultiLevelCache:
    """
    2-tier caching system optimized for market data

    L1 (In-Memory):
    - Ultra-fast access (microseconds)
    - Limited size (configurable)
    - Short TTL (60 seconds default)
    - Pure Python LRU+TTL cache

    L2 (DragonflyDB/Redis):
    - Fast access (milliseconds)
    - Large capacity
    - Longer TTL (3600 seconds default)
    - Shared across service instances

    Read Strategy:
    1. Check L1 cache → if hit, return
    2. Check L2 cache → if hit, populate L1, return
    3. Cache miss → return None

    Write Strategy:
    - Write to both L1 and L2 simultaneously
    """

    def __init__(
        self,
        redis_client: aioredis.Redis,
        l1_max_size: int = 1000,
        l1_ttl: int = 60,
        namespace: str = "data_cache",
        l1_cache: Optional[L1Cache] = None,
        l2_cache: Optional[L2Cache] = None
    ):
        """
        Initialize multi-level cache

        Args:
            redis_client: Redis/DragonflyDB client (required)
            l1_max_size: Max items in L1 cache
            l1_ttl: Default TTL for L1 cache (seconds)
            namespace: Key prefix for L2 cache
            l1_cache: L1Cache instance (optional, will create if not provided)
            l2_cache: L2Cache instance (optional, will create if not provided)
        """
        # Initialize L1 cache
        self.l1_cache = l1_cache or L1Cache(max_size=l1_max_size, ttl=l1_ttl)

        # Initialize L2 cache
        self.l2_cache = l2_cache or L2Cache(redis_client=redis_client, namespace=namespace)

        # Statistics
        self.stats = {
            "l1_hits": 0,
            "l2_hits": 0,
            "misses": 0,
            "l1_writes": 0,
            "l2_writes": 0,
            "errors": 0
        }

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache (L1 → L2 → miss)

        Returns:
            Cached value or None if not found
        """
        try:
            # Try L1 cache first (fastest)
            value = self.l1_cache.get(key)
            if value is not None:
                self.stats["l1_hits"] += 1
                return value

            # Try L2 cache (Redis/DragonflyDB)
            value = await self.l2_cache.get(key)
            if value is not None:
                # L2 hit - populate L1 for next access
                self.l1_cache.set(key, value)
                self.stats["l2_hits"] += 1
                return value

            # Cache miss
            self.stats["misses"] += 1
            return None

        except Exception:
            self.stats["errors"] += 1
            return None

    async def set(
        self,
        key: str,
        value: Any,
        l1_ttl: Optional[int] = None,
        l2_ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache (write to both L1 and L2)

        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            l1_ttl: TTL for L1 cache (seconds, optional - uses default)
            l2_ttl: TTL for L2 cache (seconds, optional - uses 3600)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Write to L1 cache
            self.l1_cache.set(key, value, ttl=l1_ttl)
            self.stats["l1_writes"] += 1

            # Write to L2 cache
            l2_ttl = l2_ttl or 3600  # Default 1 hour
            await self.l2_cache.set(key, value, ttl=l2_ttl)
            self.stats["l2_writes"] += 1

            return True

        except Exception:
            self.stats["errors"] += 1
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete key from both L1 and L2 caches

        Returns:
            True if deleted from at least one cache
        """
        try:
            l1_deleted = self.l1_cache.delete(key)
            l2_deleted = await self.l2_cache.delete(key)
            return l1_deleted or l2_deleted

        except Exception:
            self.stats["errors"] += 1
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching pattern (L2 only)
        L1 will expire naturally via TTL

        Args:
            pattern: Key pattern (e.g., "tick:latest:EUR*")

        Returns:
            Number of keys deleted
        """
        try:
            return await self.l2_cache.clear(pattern)
        except Exception:
            self.stats["errors"] += 1
            return 0

    async def clear(self) -> bool:
        """
        Clear all cache entries (both L1 and L2)

        Returns:
            True if successful
        """
        try:
            self.l1_cache.clear()
            await self.l2_cache.clear()
            return True

        except Exception:
            self.stats["errors"] += 1
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache stats and hit rates
        """
        total_requests = (
            self.stats["l1_hits"] +
            self.stats["l2_hits"] +
            self.stats["misses"]
        )

        l1_hit_rate = (
            (self.stats["l1_hits"] / total_requests * 100)
            if total_requests > 0 else 0
        )

        l2_hit_rate = (
            (self.stats["l2_hits"] / total_requests * 100)
            if total_requests > 0 else 0
        )

        overall_hit_rate = (
            ((self.stats["l1_hits"] + self.stats["l2_hits"]) / total_requests * 100)
            if total_requests > 0 else 0
        )

        return {
            "l1_size": len(self.l1_cache),
            "l1_max_size": self.l1_cache.max_size,
            "l1_hits": self.stats["l1_hits"],
            "l1_hit_rate_pct": round(l1_hit_rate, 2),
            "l2_hits": self.stats["l2_hits"],
            "l2_hit_rate_pct": round(l2_hit_rate, 2),
            "total_misses": self.stats["misses"],
            "overall_hit_rate_pct": round(overall_hit_rate, 2),
            "total_requests": total_requests,
            "l1_writes": self.stats["l1_writes"],
            "l2_writes": self.stats["l2_writes"],
            "errors": self.stats["errors"]
        }

    def reset_stats(self):
        """Reset statistics counters"""
        self.stats = {
            "l1_hits": 0,
            "l2_hits": 0,
            "misses": 0,
            "l1_writes": 0,
            "l2_writes": 0,
            "errors": 0
        }
