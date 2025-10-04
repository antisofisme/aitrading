"""
Multi-level Caching System
L1: In-memory cache (fast, per-instance)
L2: DragonflyDB cache (shared across services)
"""
import json
import asyncio
from typing import Optional, Any, Dict
from collections import OrderedDict
from datetime import datetime, timedelta
from .exceptions import CacheError


class L1Cache:
    """
    L1 In-Memory Cache
    Fast, local cache with LRU eviction
    """

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 60):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, tuple[Any, datetime]] = OrderedDict()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Get value from L1 cache"""
        if key in self._cache:
            value, expires_at = self._cache[key]

            # Check if expired
            if datetime.utcnow() < expires_at:
                # Move to end (LRU)
                self._cache.move_to_end(key)
                self._hits += 1
                return value
            else:
                # Expired, remove
                del self._cache[key]

        self._misses += 1
        return None

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        """Set value in L1 cache"""
        ttl = ttl_seconds or self.ttl_seconds
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)

        # Add to cache
        self._cache[key] = (value, expires_at)
        self._cache.move_to_end(key)

        # Evict oldest if size exceeded (LRU)
        if len(self._cache) > self.max_size:
            self._cache.popitem(last=False)

    def delete(self, key: str):
        """Delete key from L1 cache"""
        if key in self._cache:
            del self._cache[key]

    def clear(self):
        """Clear all L1 cache"""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def get_stats(self) -> Dict:
        """Get L1 cache statistics"""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0

        return {
            "entries": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 3)
        }


class L2Cache:
    """
    L2 DragonflyDB Cache
    Shared cache across all service instances
    """

    def __init__(self, redis_client):
        self.client = redis_client
        self._hits = 0
        self._misses = 0

    async def get(self, key: str) -> Optional[Any]:
        """Get value from L2 cache (DragonflyDB)"""
        try:
            value = await self.client.get(key)
            if value:
                self._hits += 1
                # Deserialize JSON
                return json.loads(value)
            else:
                self._misses += 1
                return None
        except Exception as e:
            raise CacheError("get", key, str(e))

    async def set(self, key: str, value: Any, ttl_seconds: int = 3600):
        """Set value in L2 cache (DragonflyDB)"""
        try:
            # Serialize to JSON
            serialized = json.dumps(value)
            await self.client.setex(key, ttl_seconds, serialized)
        except Exception as e:
            raise CacheError("set", key, str(e))

    async def delete(self, key: str):
        """Delete key from L2 cache"""
        try:
            await self.client.delete(key)
        except Exception as e:
            raise CacheError("delete", key, str(e))

    async def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern"""
        try:
            keys = await self.client.keys(pattern)
            if keys:
                await self.client.delete(*keys)
        except Exception as e:
            raise CacheError("delete_pattern", pattern, str(e))

    async def clear(self):
        """Clear all L2 cache (DANGEROUS!)"""
        try:
            await self.client.flushdb()
        except Exception as e:
            raise CacheError("clear", "all", str(e))

    async def get_stats(self) -> Dict:
        """Get L2 cache statistics"""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0

        try:
            info = await self.client.info("stats")
            return {
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 3),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0)
            }
        except:
            return {
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 3)
            }


class MultiLevelCache:
    """
    Multi-level caching system
    Cascade: L1 (memory) → L2 (DragonflyDB) → Database
    """

    def __init__(self, redis_client, l1_max_size: int = 1000, l1_ttl: int = 60):
        self.l1 = L1Cache(max_size=l1_max_size, ttl_seconds=l1_ttl)
        self.l2 = L2Cache(redis_client)

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache (cascade check)
        1. Check L1 (fast)
        2. If miss, check L2
        3. If found in L2, promote to L1
        """
        # Try L1
        value = self.l1.get(key)
        if value is not None:
            return value

        # Try L2
        value = await self.l2.get(key)
        if value is not None:
            # Promote to L1
            self.l1.set(key, value)
            return value

        return None

    async def set(self, key: str, value: Any, l1_ttl: int = 60, l2_ttl: int = 3600):
        """
        Set value in cache
        Write to both L1 and L2
        """
        # Write to L1
        self.l1.set(key, value, ttl_seconds=l1_ttl)

        # Write to L2
        await self.l2.set(key, value, ttl_seconds=l2_ttl)

    async def delete(self, key: str):
        """Delete from both L1 and L2"""
        self.l1.delete(key)
        await self.l2.delete(key)

    async def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        # L1: Can't pattern delete (would need to iterate all keys)
        # For now, just clear L1 entirely if pattern matches anything
        self.l1.clear()

        # L2: Delete pattern
        await self.l2.delete_pattern(pattern)

    async def get_stats(self) -> Dict:
        """Get combined cache statistics"""
        l1_stats = self.l1.get_stats()
        l2_stats = await self.l2.get_stats()

        total_hits = l1_stats['hits'] + l2_stats['hits']
        total_misses = l1_stats['misses'] + l2_stats['misses']
        total = total_hits + total_misses
        total_hit_rate = total_hits / total if total > 0 else 0

        return {
            "l1": l1_stats,
            "l2": l2_stats,
            "total_hit_rate": round(total_hit_rate, 3)
        }
