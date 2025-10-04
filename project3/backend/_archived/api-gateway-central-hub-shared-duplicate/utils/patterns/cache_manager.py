"""
Standard Cache Manager untuk semua services
Menyediakan consistent caching patterns dengan multiple backends
"""

import asyncio
import json
import logging as python_logging
import time
from typing import Any, Dict, Optional, Union, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
try:
    import redis.asyncio as aioredis
    AIOREDIS_AVAILABLE = True
except ImportError:
    AIOREDIS_AVAILABLE = False
from cachetools import TTLCache
import pickle


@dataclass
class CacheConfig:
    """Cache configuration"""
    backend: str  # "redis", "memory", "hybrid"
    host: Optional[str] = None
    port: Optional[int] = None
    password: Optional[str] = None
    db: int = 0
    default_ttl: int = 300  # 5 minutes
    memory_max_size: int = 1000
    compression: bool = False
    serialization: str = "json"  # "json", "pickle"


class CacheBackend(ABC):
    """Abstract cache backend interface"""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cache entries"""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Cache backend health check"""
        pass


class RedisBackend(CacheBackend):
    """Redis cache backend implementation"""

    def __init__(self, config: CacheConfig, service_name: str):
        self.config = config
        self.service_name = service_name
        self.redis = None
        self.logger = python_logging.getLogger(f"{service_name}.cache.redis")

    async def connect(self):
        """Connect to Redis with fallback"""
        if not AIOREDIS_AVAILABLE:
            self.logger.warning("aioredis not available, Redis cache disabled")
            return

        try:
            # Connect to DragonflyDB (Redis-compatible)
            dragonfly_url = f"redis://{self.config.host}:{self.config.port}"
            if self.config.password:
                dragonfly_url = f"redis://:{self.config.password}@{self.config.host}:{self.config.port}"

            self.redis = aioredis.from_url(
                dragonfly_url,
                db=self.config.db,
                decode_responses=True
            )
            await self.redis.ping()
            self.logger.info("DragonflyDB cache connected")
        except Exception as e:
            self.logger.warning(f"DragonflyDB connection failed, cache disabled: {str(e)}")
            self.redis = None

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis and AIOREDIS_AVAILABLE:
            await self.redis.close()
            self.logger.info("Redis cache disconnected")

    def _serialize(self, value: Any) -> str:
        """Serialize value for storage"""
        if self.config.serialization == "pickle":
            return pickle.dumps(value).hex()
        else:
            return json.dumps(value, default=str)

    def _deserialize(self, value: str) -> Any:
        """Deserialize value from storage"""
        if self.config.serialization == "pickle":
            return pickle.loads(bytes.fromhex(value))
        else:
            return json.loads(value)

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        if not self.redis:
            return None

        try:
            value = await self.redis.get(key)
            if value is None:
                return None
            return self._deserialize(value)
        except Exception as e:
            self.logger.error(f"Redis get error for key {key}: {str(e)}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis"""
        if not self.redis:
            return False

        try:
            serialized_value = self._serialize(value)
            ttl = ttl or self.config.default_ttl

            await self.redis.setex(key, ttl, serialized_value)
            return True
        except Exception as e:
            self.logger.error(f"Redis set error for key {key}: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        if not self.redis:
            return False

        try:
            result = await self.redis.delete(key)
            return result > 0
        except Exception as e:
            self.logger.error(f"Redis delete error for key {key}: {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        if not self.redis:
            return False

        try:
            result = await self.redis.exists(key)
            return result > 0
        except Exception as e:
            self.logger.error(f"Redis exists error for key {key}: {str(e)}")
            return False

    async def clear(self) -> bool:
        """Clear all Redis entries for this service"""
        if not self.redis:
            return False

        try:
            # Only clear keys with service prefix
            pattern = f"{self.service_name}:*"
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
            return True
        except Exception as e:
            self.logger.error(f"Redis clear error: {str(e)}")
            return False

    async def health_check(self) -> Dict[str, Any]:
        """Redis health check"""
        try:
            start_time = time.time()
            await self.redis.ping()
            response_time = (time.time() - start_time) * 1000

            info = await self.redis.info()
            return {
                "type": "redis",
                "status": "healthy",
                "response_time_ms": response_time,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "unknown"),
                "keyspace": info.get(f"db{self.config.db}", {})
            }
        except Exception as e:
            return {
                "type": "redis",
                "status": "unhealthy",
                "error": str(e)
            }


class MemoryBackend(CacheBackend):
    """In-memory cache backend implementation"""

    def __init__(self, config: CacheConfig, service_name: str):
        self.config = config
        self.service_name = service_name
        self.cache = TTLCache(maxsize=config.memory_max_size, ttl=config.default_ttl)
        self.logger = python_logging.getLogger(f"{service_name}.cache.memory")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache"""
        try:
            return self.cache.get(key)
        except Exception as e:
            self.logger.error(f"Memory get error for key {key}: {str(e)}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in memory cache"""
        try:
            self.cache[key] = value
            return True
        except Exception as e:
            self.logger.error(f"Memory set error for key {key}: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from memory cache"""
        try:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
        except Exception as e:
            self.logger.error(f"Memory delete error for key {key}: {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in memory cache"""
        return key in self.cache

    async def clear(self) -> bool:
        """Clear all memory cache entries"""
        try:
            self.cache.clear()
            return True
        except Exception as e:
            self.logger.error(f"Memory clear error: {str(e)}")
            return False

    async def health_check(self) -> Dict[str, Any]:
        """Memory cache health check"""
        return {
            "type": "memory",
            "status": "healthy",
            "current_size": len(self.cache),
            "max_size": self.cache.maxsize,
            "usage_percent": (len(self.cache) / self.cache.maxsize) * 100 if self.cache.maxsize > 0 else 0
        }


class StandardCacheManager:
    """
    Standard cache manager untuk semua services
    Mendukung multiple cache backends dengan interface yang konsisten
    """

    def __init__(self, service_name: str, default_ttl: int = 300):
        self.service_name = service_name
        self.default_ttl = default_ttl
        self.backends: Dict[str, CacheBackend] = {}
        self.primary_backend = None
        self.logger = python_logging.getLogger(f"{service_name}.cache_manager")

    async def add_backend(self, name: str, config: CacheConfig) -> CacheBackend:
        """Add cache backend"""
        if config.backend.lower() == "redis":
            backend = RedisBackend(config, self.service_name)
            await backend.connect()
        elif config.backend.lower() == "memory":
            backend = MemoryBackend(config, self.service_name)
        else:
            raise ValueError(f"Unsupported cache backend: {config.backend}")

        self.backends[name] = backend
        if self.primary_backend is None:
            self.primary_backend = name

        self.logger.info(f"Added {config.backend} cache backend: {name}")
        return backend

    def get_backend(self, name: Optional[str] = None) -> CacheBackend:
        """Get cache backend by name"""
        backend_name = name or self.primary_backend
        if backend_name not in self.backends:
            raise ValueError(f"Cache backend '{backend_name}' not found")
        return self.backends[backend_name]

    async def connect(self):
        """Connect to cache backends"""
        # Default connection setup - can be overridden by services
        pass

    async def disconnect(self):
        """Disconnect all cache backends"""
        for name, backend in self.backends.items():
            try:
                if hasattr(backend, 'disconnect'):
                    await backend.disconnect()
                self.logger.info(f"Disconnected from cache backend: {name}")
            except Exception as e:
                self.logger.error(f"Error disconnecting from {name}: {str(e)}")

    def _make_key(self, key: str) -> str:
        """Create namespaced cache key"""
        return f"{self.service_name}:{key}"

    async def get(self, key: str, default: Any = None, backend: Optional[str] = None) -> Any:
        """Get value from cache"""
        namespaced_key = self._make_key(key)
        cache_backend = self.get_backend(backend)

        try:
            value = await cache_backend.get(namespaced_key)
            return value if value is not None else default
        except Exception as e:
            self.logger.error(f"Cache get error for key {key}: {str(e)}")
            return default

    async def set(self, key: str, value: Any, ttl: Optional[int] = None, backend: Optional[str] = None) -> bool:
        """Set value in cache"""
        namespaced_key = self._make_key(key)
        cache_backend = self.get_backend(backend)
        ttl = ttl or self.default_ttl

        try:
            return await cache_backend.set(namespaced_key, value, ttl)
        except Exception as e:
            self.logger.error(f"Cache set error for key {key}: {str(e)}")
            return False

    async def delete(self, key: str, backend: Optional[str] = None) -> bool:
        """Delete key from cache"""
        namespaced_key = self._make_key(key)
        cache_backend = self.get_backend(backend)

        try:
            return await cache_backend.delete(namespaced_key)
        except Exception as e:
            self.logger.error(f"Cache delete error for key {key}: {str(e)}")
            return False

    async def exists(self, key: str, backend: Optional[str] = None) -> bool:
        """Check if key exists in cache"""
        namespaced_key = self._make_key(key)
        cache_backend = self.get_backend(backend)

        try:
            return await cache_backend.exists(namespaced_key)
        except Exception as e:
            self.logger.error(f"Cache exists error for key {key}: {str(e)}")
            return False

    async def clear(self, backend: Optional[str] = None) -> bool:
        """Clear cache entries for this service"""
        cache_backend = self.get_backend(backend)

        try:
            return await cache_backend.clear()
        except Exception as e:
            self.logger.error(f"Cache clear error: {str(e)}")
            return False

    async def health_check(self) -> Dict[str, Any]:
        """Health check for all cache backends"""
        health_status = {
            "overall_status": "healthy",
            "backends": {}
        }

        unhealthy_count = 0
        for name, backend in self.backends.items():
            try:
                backend_health = await backend.health_check()
                health_status["backends"][name] = backend_health

                if backend_health.get("status") != "healthy":
                    unhealthy_count += 1
            except Exception as e:
                health_status["backends"][name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                unhealthy_count += 1

        # Determine overall status
        if unhealthy_count == 0:
            health_status["overall_status"] = "healthy"
        elif unhealthy_count < len(self.backends):
            health_status["overall_status"] = "degraded"
        else:
            health_status["overall_status"] = "unhealthy"

        health_status["total_backends"] = len(self.backends)
        health_status["unhealthy_backends"] = unhealthy_count

        return health_status

    # Common caching patterns
    async def get_or_set(self, key: str, func, ttl: Optional[int] = None, backend: Optional[str] = None) -> Any:
        """Get from cache or set by calling function"""
        value = await self.get(key, backend=backend)

        if value is None:
            # Value not in cache, compute it
            if asyncio.iscoroutinefunction(func):
                value = await func()
            else:
                value = func()

            # Store in cache
            await self.set(key, value, ttl, backend)

        return value

    async def mget(self, keys: List[str], backend: Optional[str] = None) -> Dict[str, Any]:
        """Get multiple keys from cache"""
        results = {}
        for key in keys:
            results[key] = await self.get(key, backend=backend)
        return results

    async def mset(self, data: Dict[str, Any], ttl: Optional[int] = None, backend: Optional[str] = None) -> bool:
        """Set multiple key-value pairs in cache"""
        success_count = 0
        for key, value in data.items():
            if await self.set(key, value, ttl, backend):
                success_count += 1

        return success_count == len(data)

    async def increment(self, key: str, delta: int = 1, backend: Optional[str] = None) -> Optional[int]:
        """Increment integer value in cache"""
        current_value = await self.get(key, default=0, backend=backend)

        if isinstance(current_value, (int, float)):
            new_value = current_value + delta
            await self.set(key, new_value, backend=backend)
            return new_value

        return None

    async def decrement(self, key: str, delta: int = 1, backend: Optional[str] = None) -> Optional[int]:
        """Decrement integer value in cache"""
        return await self.increment(key, -delta, backend)