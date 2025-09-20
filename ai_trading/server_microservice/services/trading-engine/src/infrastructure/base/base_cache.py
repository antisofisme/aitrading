"""
Base Cache Interface - Abstract class for service-specific caching
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from enum import Enum

class CacheLevel(Enum):
    MEMORY = "memory"
    REDIS = "redis"
    DATABASE = "database"

class CacheStrategy(Enum):
    LRU = "lru"           # Least Recently Used
    LFU = "lfu"           # Least Frequently Used
    TTL = "ttl"           # Time To Live
    FIFO = "fifo"         # First In First Out

class BaseCache(ABC):
    """Abstract base class for all service cache implementations"""
    
    def __init__(self, 
                 service_name: str,
                 default_ttl: int = 3600,  # 1 hour default
                 max_size: int = 1000):
        self.service_name = service_name
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "evictions": 0
        }
    
    @abstractmethod
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache"""
        pass
    
    @abstractmethod
    async def set(self, 
                  key: str, 
                  value: Any, 
                  ttl: Optional[int] = None,
                  level: CacheLevel = CacheLevel.MEMORY) -> bool:
        """Set value in cache with optional TTL"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        pass
    
    @abstractmethod
    async def clear(self, pattern: Optional[str] = None):
        """Clear cache, optionally by pattern"""
        pass
    
    @abstractmethod
    async def get_multi(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache"""
        pass
    
    @abstractmethod
    async def set_multi(self, 
                        data: Dict[str, Any], 
                        ttl: Optional[int] = None,
                        level: CacheLevel = CacheLevel.MEMORY) -> bool:
        """Set multiple values in cache"""
        pass
    
    @abstractmethod
    async def delete_multi(self, keys: List[str]) -> int:
        """Delete multiple keys from cache"""
        pass
    
    @abstractmethod
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment numeric value in cache"""
        pass
    
    @abstractmethod
    async def decrement(self, key: str, amount: int = 1) -> int:
        """Decrement numeric value in cache"""
        pass
    
    @abstractmethod
    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL for existing key"""
        pass
    
    @abstractmethod
    async def ttl(self, key: str) -> int:
        """Get remaining TTL for key"""
        pass
    
    def generate_key(self, *parts: str) -> str:
        """Generate cache key from parts"""
        return f"{self.service_name}:{':'.join(str(part) for part in parts)}"
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_operations = sum(self.cache_stats.values())
        hit_rate = (self.cache_stats["hits"] / max(self.cache_stats["hits"] + self.cache_stats["misses"], 1)) * 100
        
        return {
            **self.cache_stats,
            "total_operations": total_operations,
            "hit_rate_percent": round(hit_rate, 2),
            "service": self.service_name
        }
    
    def reset_stats(self):
        """Reset cache statistics"""
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "evictions": 0
        }
    
    def _record_hit(self):
        """Record cache hit"""
        self.cache_stats["hits"] += 1
    
    def _record_miss(self):
        """Record cache miss"""
        self.cache_stats["misses"] += 1
    
    def _record_set(self):
        """Record cache set"""
        self.cache_stats["sets"] += 1
    
    def _record_delete(self):
        """Record cache delete"""
        self.cache_stats["deletes"] += 1
    
    def _record_eviction(self):
        """Record cache eviction"""
        self.cache_stats["evictions"] += 1
    
    @abstractmethod
    async def get_size(self) -> int:
        """Get current cache size"""
        pass
    
    @abstractmethod
    async def get_keys(self, pattern: Optional[str] = None) -> List[str]:
        """Get all keys, optionally matching pattern"""
        pass
    
    @abstractmethod
    def setup_service_specific_caching(self):
        """Setup service-specific caching configuration"""
        pass
    
    @abstractmethod
    async def warm_up(self, data: Dict[str, Any]):
        """Warm up cache with initial data"""
        pass