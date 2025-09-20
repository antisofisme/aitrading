"""
AI Brain Enhanced Core Cache Implementation - Confidence-based intelligent caching with DragonflyDB
Enhanced with AI Brain confidence-driven cache strategies and pattern recognition
"""
import json
import time
import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from collections import OrderedDict
import hashlib
import redis.asyncio as redis
from redis.asyncio import ConnectionPool
from ..base.base_cache import BaseCache, CacheLevel, CacheStrategy

# AI Brain Integration
try:
    import sys
    sys.path.append('/mnt/f/WINDSURF/concept_ai/projects/ai_trading/server_microservice/services')
    from shared.ai_brain_confidence_framework import AiBrainConfidenceFramework
    AI_BRAIN_AVAILABLE = True
except ImportError:
    AI_BRAIN_AVAILABLE = False

class CoreCache(BaseCache):
    """AI Brain Enhanced Core cache implementation with confidence-driven intelligent caching strategies"""
    
    def __init__(self, 
                 service_name: str,
                 default_ttl: int = 3600,
                 max_size: int = 1000,
                 strategy: CacheStrategy = CacheStrategy.LRU,
                 dragonflydb_url: Optional[str] = None):
        """
        Initialize AI Brain Enhanced CoreCache with confidence-based caching strategies.
        
        Args:
            service_name: Name of the service using this cache
            default_ttl: Default time-to-live for cache entries in seconds (default: 3600)
            max_size: Maximum number of entries in memory cache (default: 1000)
            strategy: Cache eviction strategy (LRU, LFU, FIFO) (default: LRU)
            dragonflydb_url: DragonflyDB connection URL, defaults to DRAGONFLYDB_URL env var
        """
        super().__init__(service_name, default_ttl, max_size)
        self.strategy = strategy
        
        # Memory cache (L1 - fastest)
        self.memory_cache = OrderedDict()
        self.memory_ttl = {}
        
        # DragonflyDB connection with pooling (L2 - distributed cache)
        self.dragonflydb_url = dragonflydb_url or os.getenv('DRAGONFLYDB_URL', 'redis://dragonflydb:6379')
        self.redis_pool = None
        self.redis_client = None
        
        # AI Brain Enhanced Caching
        self.confidence_cache_strategies = {}
        self.cache_pattern_analysis = {}
        self.confidence_ttl_adjustments = {}
        self.ai_brain_cache_decisions = []
        
        # AI Brain Integration
        self.ai_brain_confidence = None
        if AI_BRAIN_AVAILABLE:
            try:
                self.ai_brain_confidence = AiBrainConfidenceFramework(f"cache-{service_name}")
                print(f"✅ AI Brain confidence caching initialized for: {service_name}")
            except Exception as e:
                print(f"⚠️ AI Brain cache initialization failed: {e}")
        
        # Initialize cache
        self.setup_service_specific_caching()
        
        # Initialize DragonflyDB connection asynchronously
        self._connection_initialized = False
    
    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache using multi-tier lookup strategy.
        
        Lookup order:
        1. Memory cache (L1) - fastest access
        2. DragonflyDB (L2) - distributed cache
        3. Return default if not found
        
        Args:
            key: Cache key to lookup
            default: Value to return if key is not found (default: None)
            
        Returns:
            Cached value or default if not found
        """
        cache_key = self.generate_key(key)
        
        # L1: Check memory cache first
        memory_value = self._get_from_memory(cache_key)
        if memory_value is not None:
            self._record_hit()
            return memory_value
        
        # L2: Check Redis cache
        redis_value = await self._get_from_redis(cache_key)
        if redis_value is not None:
            # Store in memory cache for faster next access
            await self._set_in_memory(cache_key, redis_value)
            self._record_hit()
            return redis_value
        
        # Cache miss
        self._record_miss()
        return default
    
    async def set(self, 
                  key: str, 
                  value: Any, 
                  ttl: Optional[int] = None,
                  level: CacheLevel = CacheLevel.MEMORY) -> bool:
        """Set value in cache with optional TTL"""
        cache_key = self.generate_key(key)
        ttl = ttl or self.default_ttl
        
        try:
            if level == CacheLevel.MEMORY or level == CacheLevel.REDIS:
                # Always store in memory for fastest access
                await self._set_in_memory(cache_key, value, ttl)
            
            if level == CacheLevel.REDIS:
                # Also store in Redis for persistence and sharing
                await self._set_in_redis(cache_key, value, ttl)
            
            self._record_set()
            return True
            
        except Exception as cache_error:
            print(f"Cache set error for key {cache_key}: {cache_error}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        cache_key = self.generate_key(key)
        
        try:
            # Remove from memory cache
            deleted_memory = self._delete_from_memory(cache_key)
            
            # Remove from Redis cache
            deleted_redis = await self._delete_from_redis(cache_key)
            
            if deleted_memory or deleted_redis:
                self._record_delete()
                return True
            
            return False
            
        except Exception as cache_error:
            print(f"Cache delete error for key {cache_key}: {cache_error}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        cache_key = self.generate_key(key)
        
        # Check memory cache first
        if self._exists_in_memory(cache_key):
            return True
        
        # Check Redis cache
        return await self._exists_in_redis(cache_key)
    
    async def clear(self, pattern: Optional[str] = None):
        """Clear cache, optionally by pattern"""
        if pattern:
            # Clear by pattern
            pattern_key = self.generate_key(pattern)
            await self._clear_by_pattern(pattern_key)
        else:
            # Clear all cache for this service
            self.memory_cache.clear()
            self.memory_ttl.clear()
            await self._clear_redis_service_keys()
    
    async def get_multi(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache"""
        result = {}
        
        for key in keys:
            value = await self.get(key)
            if value is not None:
                result[key] = value
        
        return result
    
    async def set_multi(self, 
                        data: Dict[str, Any], 
                        ttl: Optional[int] = None,
                        level: CacheLevel = CacheLevel.MEMORY) -> bool:
        """Set multiple values in cache"""
        try:
            for key, value in data.items():
                await self.set(key, value, ttl, level)
            return True
        except Exception as cache_error:
            print(f"Cache set_multi error: {cache_error}")
            return False
    
    async def delete_multi(self, keys: List[str]) -> int:
        """Delete multiple keys from cache"""
        deleted_count = 0
        
        for key in keys:
            if await self.delete(key):
                deleted_count += 1
        
        return deleted_count
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment numeric value in cache"""
        cache_key = self.generate_key(key)
        current_value = await self.get(key, 0)
        
        if not isinstance(current_value, (int, float)):
            current_value = 0
        
        new_value = current_value + amount
        await self.set(key, new_value)
        
        return new_value
    
    async def decrement(self, key: str, amount: int = 1) -> int:
        """Decrement numeric value in cache"""
        return await self.increment(key, -amount)
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL for existing key"""
        cache_key = self.generate_key(key)
        
        # Update TTL in memory cache
        if cache_key in self.memory_cache:
            self.memory_ttl[cache_key] = time.time() + ttl
        
        # Update TTL in Redis cache
        return await self._expire_in_redis(cache_key, ttl)
    
    async def ttl(self, key: str) -> int:
        """Get remaining TTL for key"""
        cache_key = self.generate_key(key)
        
        # Check memory cache TTL first
        if cache_key in self.memory_ttl:
            remaining = self.memory_ttl[cache_key] - time.time()
            return max(0, int(remaining))
        
        # Check Redis TTL
        return await self._ttl_in_redis(cache_key)
    
    async def get_size(self) -> int:
        """Get current cache size"""
        memory_size = len(self.memory_cache)
        redis_size = await self._get_redis_size()
        
        return {
            "memory": memory_size,
            "redis": redis_size,
            "total": memory_size + redis_size
        }
    
    async def get_keys(self, pattern: Optional[str] = None) -> List[str]:
        """Get all keys, optionally matching pattern"""
        keys = set()
        
        # Get keys from memory cache
        memory_keys = list(self.memory_cache.keys())
        keys.update(memory_keys)
        
        # Get keys from Redis cache
        redis_keys = await self._get_redis_keys(pattern)
        keys.update(redis_keys)
        
        # Filter by pattern if provided
        if pattern:
            pattern_key = self.generate_key(pattern)
            keys = [cache_key for cache_key in keys if pattern_key in cache_key]
        
        return list(keys)
    
    def setup_service_specific_caching(self) -> None:
        """Setup service-specific caching configuration"""
        # Service-specific cache configurations
        
        if self.service_name == "api-gateway":
            # API Gateway needs fast response caching
            self.default_ttl = 300  # 5 minutes
            self.max_size = 2000
        
        elif self.service_name == "database-service":
            # Database service needs longer caching
            self.default_ttl = 3600  # 1 hour
            self.max_size = 5000
        
        elif self.service_name in ["trading-engine", "mt5-bridge"]:
            # Trading services need very short caching
            self.default_ttl = 60  # 1 minute
            self.max_size = 1000
    
    async def warm_up(self, data: Dict[str, Any]):
        """Warm up cache with initial data"""
        print(f"Warming up cache for {self.service_name} with {len(data)} items")
        await self.set_multi(data)
    
    # DragonflyDB connection management
    async def _ensure_dragonflydb_connection(self) -> None:
        """Ensure DragonflyDB connection is established with optimized connection pooling"""
        if not self._connection_initialized:
            try:
                # PERFORMANCE FIX: Optimized connection pool parameters for high-performance
                self.redis_pool = ConnectionPool.from_url(
                    self.dragonflydb_url,
                    max_connections=50,  # Increased pool size for high concurrency
                    retry_on_timeout=True,
                    socket_connect_timeout=3,  # Reduced timeout for faster failure detection
                    socket_timeout=5,  # Reduced socket timeout
                    socket_keepalive=True,  # Enable keepalive
                    socket_keepalive_options={},
                    health_check_interval=15,  # More frequent health checks
                    decode_responses=False,  # Keep as bytes for better performance
                    # PERFORMANCE FIX: Additional optimization parameters
                    connection_class=redis.Connection,
                    retry_on_error=[ConnectionError, TimeoutError],
                    retry=redis.Retry(backoff=redis.ExponentialBackoff(), retries=3)
                )
                
                # Create Redis client from pool
                self.redis_client = redis.Redis(connection_pool=self.redis_pool)
                
                # Test connection
                await self.redis_client.ping()
                self._connection_initialized = True
                
                # Use proper logging instead of print
                import logging
                logger = logging.getLogger(f"{self.service_name}-cache")
                logger.info(f"DragonflyDB connection established", 
                           extra={"context": {"url": self.dragonflydb_url, "pool_size": 20}})
                
            except Exception as connection_error:
                # Log connection error but don't fail completely (fallback to memory only)
                import logging
                logger = logging.getLogger(f"{self.service_name}-cache")
                logger.warning(f"DragonflyDB connection failed, using memory-only cache", 
                             extra={"context": {"error": str(connection_error), "url": self.dragonflydb_url}})
                self.redis_client = None
                self._connection_initialized = True  # Mark as attempted
    
    async def _close_dragonflydb_connection(self) -> None:
        """Close DragonflyDB connection and cleanup pool"""
        if self.redis_client:
            await self.redis_client.close()
        if self.redis_pool:
            await self.redis_pool.disconnect()
        self._connection_initialized = False
    
    # Memory cache operations
    def _get_from_memory(self, key: str) -> Any:
        """Get value from memory cache"""
        if key not in self.memory_cache:
            return None
        
        # Check TTL
        if key in self.memory_ttl:
            if time.time() > self.memory_ttl[key]:
                # Expired
                self._delete_from_memory(key)
                return None
        
        # Update access order for LRU
        if self.strategy == CacheStrategy.LRU:
            self.memory_cache.move_to_end(key)
        
        return self.memory_cache[key]
    
    async def _set_in_memory(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in memory cache"""
        # Check if we need to evict items
        if len(self.memory_cache) >= self.max_size and key not in self.memory_cache:
            self._evict_from_memory()
        
        # Store value
        self.memory_cache[key] = value
        
        # Set TTL if provided
        if ttl:
            self.memory_ttl[key] = time.time() + ttl
        
        # Move to end for LRU
        if self.strategy == CacheStrategy.LRU:
            self.memory_cache.move_to_end(key)
    
    def _delete_from_memory(self, key: str) -> bool:
        """Delete value from memory cache"""
        deleted = False
        
        if key in self.memory_cache:
            del self.memory_cache[key]
            deleted = True
        
        if key in self.memory_ttl:
            del self.memory_ttl[key]
        
        return deleted
    
    def _exists_in_memory(self, key: str) -> bool:
        """Check if key exists in memory cache"""
        if key not in self.memory_cache:
            return False
        
        # Check TTL
        if key in self.memory_ttl:
            if time.time() > self.memory_ttl[key]:
                self._delete_from_memory(key)
                return False
        
        return True
    
    def _evict_from_memory(self) -> None:
        """Evict items from memory cache based on strategy"""
        if not self.memory_cache:
            return
        
        if self.strategy == CacheStrategy.LRU:
            # Remove least recently used (first item)
            oldest_key = next(iter(self.memory_cache))
            self._delete_from_memory(oldest_key)
            self._record_eviction()
        
        elif self.strategy == CacheStrategy.FIFO:
            # Remove first in (first item)
            oldest_key = next(iter(self.memory_cache))
            self._delete_from_memory(oldest_key)
            self._record_eviction()
    
    # Redis cache operations (placeholder implementations)
    async def _get_from_redis(self, key: str) -> Any:
        """Get value from DragonflyDB cache"""
        await self._ensure_dragonflydb_connection()
        
        if not self.redis_client:
            return None
            
        try:
            value_bytes = await self.redis_client.get(key)
            if value_bytes is None:
                return None
                
            # Deserialize JSON data
            value_str = value_bytes.decode('utf-8')
            return json.loads(value_str)
            
        except Exception as cache_error:
            import logging
            logger = logging.getLogger(f"{self.service_name}-cache")
            logger.error(f"DragonflyDB get error for key {key}", 
                        extra={"context": {"error": str(cache_error)}})
            return None
    
    async def _set_in_redis(self, key: str, value: Any, ttl: int) -> bool:
        """Set value in DragonflyDB cache"""
        await self._ensure_dragonflydb_connection()
        
        if not self.redis_client:
            return False
            
        try:
            # Serialize to JSON
            value_str = json.dumps(value, default=str)
            
            # Set with TTL
            result = await self.redis_client.setex(key, ttl, value_str)
            return bool(result)
            
        except Exception as cache_error:
            import logging
            logger = logging.getLogger(f"{self.service_name}-cache")
            logger.error(f"DragonflyDB set error for key {key}", 
                        extra={"context": {"error": str(cache_error)}})
            return False
    
    async def _delete_from_redis(self, key: str) -> bool:
        """Delete value from DragonflyDB cache"""
        await self._ensure_dragonflydb_connection()
        
        if not self.redis_client:
            return False
            
        try:
            result = await self.redis_client.delete(key)
            return bool(result)
            
        except Exception as cache_error:
            import logging
            logger = logging.getLogger(f"{self.service_name}-cache")
            logger.error(f"DragonflyDB delete error for key {key}", 
                        extra={"context": {"error": str(cache_error)}})
            return False
    
    async def _exists_in_redis(self, key: str) -> bool:
        """Check if key exists in DragonflyDB cache"""
        await self._ensure_dragonflydb_connection()
        
        if not self.redis_client:
            return False
            
        try:
            result = await self.redis_client.exists(key)
            return bool(result)
            
        except Exception as cache_error:
            import logging
            logger = logging.getLogger(f"{self.service_name}-cache")
            logger.error(f"DragonflyDB exists error for key {key}", 
                        extra={"context": {"error": str(cache_error)}})
            return False
    
    async def _expire_in_redis(self, key: str, ttl: int) -> bool:
        """Set TTL in DragonflyDB cache"""
        await self._ensure_dragonflydb_connection()
        
        if not self.redis_client:
            return False
            
        try:
            result = await self.redis_client.expire(key, ttl)
            return bool(result)
            
        except Exception as cache_error:
            import logging
            logger = logging.getLogger(f"{self.service_name}-cache")
            logger.error(f"DragonflyDB expire error for key {key}", 
                        extra={"context": {"error": str(cache_error)}})
            return False
    
    async def _ttl_in_redis(self, key: str) -> int:
        """Get TTL from DragonflyDB cache"""
        await self._ensure_dragonflydb_connection()
        
        if not self.redis_client:
            return -1
            
        try:
            result = await self.redis_client.ttl(key)
            return int(result)
            
        except Exception as cache_error:
            import logging
            logger = logging.getLogger(f"{self.service_name}-cache")
            logger.error(f"DragonflyDB TTL error for key {key}", 
                        extra={"context": {"error": str(cache_error)}})
            return -1
    
    async def _get_redis_size(self) -> int:
        """Get DragonflyDB cache size for this service"""
        await self._ensure_dragonflydb_connection()
        
        if not self.redis_client:
            return 0
            
        try:
            # Count keys matching service pattern
            pattern = f"{self.service_name}:*"
            keys = await self.redis_client.keys(pattern)
            return len(keys)
            
        except Exception as cache_error:
            import logging
            logger = logging.getLogger(f"{self.service_name}-cache")
            logger.error(f"DragonflyDB size error", 
                        extra={"context": {"error": str(cache_error)}})
            return 0
    
    async def _get_redis_keys(self, pattern: Optional[str] = None) -> List[str]:
        """Get DragonflyDB cache keys"""
        await self._ensure_dragonflydb_connection()
        
        if not self.redis_client:
            return []
            
        try:
            # Use service-specific pattern if none provided
            search_pattern = pattern or f"{self.service_name}:*"
            keys_bytes = await self.redis_client.keys(search_pattern)
            # Convert bytes to strings
            return [key.decode('utf-8') for key in keys_bytes]
            
        except Exception as cache_error:
            import logging
            logger = logging.getLogger(f"{self.service_name}-cache")
            logger.error(f"DragonflyDB keys error", 
                        extra={"context": {"error": str(cache_error), "pattern": search_pattern}})
            return []
    
    async def _clear_by_pattern(self, pattern: str) -> None:
        """Clear cache by pattern"""
        # Clear memory cache by pattern
        keys_to_delete = [cache_key for cache_key in self.memory_cache.keys() if pattern in cache_key]
        for key in keys_to_delete:
            self._delete_from_memory(key)
    
    async def _clear_redis_service_keys(self) -> None:
        """Clear all DragonflyDB keys for this service"""
        await self._ensure_dragonflydb_connection()
        
        if not self.redis_client:
            return
            
        try:
            # Get all keys for this service
            pattern = f"{self.service_name}:*"
            keys = await self.redis_client.keys(pattern)
            
            if keys:
                # Delete all keys in batch for efficiency
                await self.redis_client.delete(*keys)
                
                import logging
                logger = logging.getLogger(f"{self.service_name}-cache")
                logger.info(f"Cleared {len(keys)} DragonflyDB keys for service", 
                           extra={"context": {"keys_cleared": len(keys), "pattern": pattern}})
            
        except Exception as cache_error:
            import logging
            logger = logging.getLogger(f"{self.service_name}-cache")
            logger.error(f"DragonflyDB clear error", 
                        extra={"context": {"error": str(cache_error)}})
    
    # AI Brain Enhanced Caching Methods
    
    async def set_with_confidence(self, key: str, value: Any, confidence_score: float, ttl: Optional[int] = None) -> bool:
        """AI Brain enhanced cache set with confidence-based TTL adjustment"""
        # Calculate AI Brain confidence-based TTL
        adjusted_ttl = self._calculate_confidence_based_ttl(key, confidence_score, ttl or self.default_ttl)
        
        # Record caching decision
        cache_decision = {
            "timestamp": datetime.now().isoformat(),
            "operation": "set_with_confidence",
            "key": key,
            "confidence_score": confidence_score,
            "original_ttl": ttl or self.default_ttl,
            "adjusted_ttl": adjusted_ttl,
            "ttl_adjustment_ratio": adjusted_ttl / (ttl or self.default_ttl)
        }
        
        self.ai_brain_cache_decisions.append(cache_decision)
        
        # Track confidence patterns for this key type
        key_pattern = self._extract_key_pattern(key)
        if key_pattern not in self.confidence_cache_strategies:
            self.confidence_cache_strategies[key_pattern] = []
        
        self.confidence_cache_strategies[key_pattern].append({
            "confidence": confidence_score,
            "ttl_adjustment": adjusted_ttl / (ttl or self.default_ttl),
            "timestamp": time.time()
        })
        
        # Keep last 50 entries per pattern
        if len(self.confidence_cache_strategies[key_pattern]) > 50:
            self.confidence_cache_strategies[key_pattern] = self.confidence_cache_strategies[key_pattern][-50:]
        
        # Perform the cache set with adjusted TTL
        result = await self.set(key, value, adjusted_ttl)
        
        # Log AI Brain caching decision
        import logging
        logger = logging.getLogger(f"{self.service_name}-ai-brain-cache")
        logger.info(f"🧠 AI Brain Cache: {key} stored with confidence {confidence_score:.3f}, TTL adjusted to {adjusted_ttl}s")
        
        return result
    
    async def get_with_confidence_analysis(self, key: str, default: Any = None) -> Dict[str, Any]:
        """AI Brain enhanced cache get with confidence analysis of cached data"""
        # Get cached value
        cached_value = await self.get(key, None)
        
        # Analyze cache hit/miss with confidence context
        result = {
            "value": cached_value if cached_value is not None else default,
            "cache_hit": cached_value is not None,
            "confidence_analysis": None,
            "ai_brain_recommendation": None
        }
        
        if self.ai_brain_confidence and AI_BRAIN_AVAILABLE:
            # Analyze confidence of cached data retrieval
            confidence_analysis = self.ai_brain_confidence.calculate_confidence(
                model_prediction={"cache_hit": result["cache_hit"]},
                data_inputs={"key_pattern": self._extract_key_pattern(key), "cache_level": "memory" if key in self.memory_cache else "redis"},
                market_context={"service": self.service_name, "operation": "cache_retrieve"},
                historical_data=self._get_key_pattern_history(key),
                risk_parameters={"cache_miss_impact": "medium" if not result["cache_hit"] else "low"}
            )
            
            result["confidence_analysis"] = {
                "composite_score": confidence_analysis.composite_score,
                "cache_reliability": confidence_analysis.composite_score,
                "recommended_action": "refresh_cache" if confidence_analysis.composite_score < 0.75 and not result["cache_hit"] else "use_cached"
            }
            
            # Generate AI Brain recommendation
            if confidence_analysis.composite_score < 0.70:
                result["ai_brain_recommendation"] = {
                    "priority": "medium",
                    "action": "consider_cache_refresh",
                    "reason": f"Cache reliability confidence low ({confidence_analysis.composite_score:.2f})",
                    "suggested_ttl_adjustment": 0.8  # Suggest shorter TTL for low confidence
                }
        
        return result
    
    def _calculate_confidence_based_ttl(self, key: str, confidence_score: float, base_ttl: int) -> int:
        """Calculate TTL based on AI Brain confidence score"""
        # High confidence = longer TTL, Low confidence = shorter TTL
        confidence_multiplier = 0.5 + (confidence_score * 1.0)  # Range: 0.5 to 1.5
        
        # Apply pattern-based adjustments
        key_pattern = self._extract_key_pattern(key)
        pattern_history = self.confidence_cache_strategies.get(key_pattern, [])
        
        if pattern_history:
            # Calculate average confidence for this pattern
            avg_pattern_confidence = sum([entry["confidence"] for entry in pattern_history[-10:]]) / min(len(pattern_history), 10)
            
            # Apply pattern learning adjustment
            pattern_multiplier = 0.8 + (avg_pattern_confidence * 0.4)  # Range: 0.8 to 1.2
            confidence_multiplier *= pattern_multiplier
        
        # Calculate final TTL
        adjusted_ttl = int(base_ttl * confidence_multiplier)
        
        # Ensure TTL is within reasonable bounds
        min_ttl = 60  # 1 minute minimum
        max_ttl = base_ttl * 2  # Max 2x original TTL
        
        return max(min_ttl, min(adjusted_ttl, max_ttl))
    
    def _extract_key_pattern(self, key: str) -> str:
        """Extract pattern from cache key for AI Brain analysis"""
        # Remove service prefix
        if key.startswith(f"{self.service_name}:"):
            key = key[len(self.service_name)+1:]
        
        # Extract pattern (first part before specific ID)
        parts = key.split(":")
        if len(parts) >= 2:
            return parts[0]  # e.g., "market_data", "user_session", "api_response"
        return "generic"
    
    def _get_key_pattern_history(self, key: str) -> Dict[str, Any]:
        """Get historical data for key pattern"""
        key_pattern = self._extract_key_pattern(key)
        pattern_data = self.confidence_cache_strategies.get(key_pattern, [])
        
        if not pattern_data:
            return {"avg_confidence": 0.5, "sample_count": 0}
        
        recent_data = pattern_data[-20:]  # Last 20 entries
        
        return {
            "avg_confidence": sum([entry["confidence"] for entry in recent_data]) / len(recent_data),
            "sample_count": len(recent_data),
            "avg_ttl_adjustment": sum([entry["ttl_adjustment"] for entry in recent_data]) / len(recent_data)
        }
    
    def get_ai_brain_cache_analysis(self) -> Dict[str, Any]:
        """Get comprehensive AI Brain cache analysis"""
        analysis = {
            "service": self.service_name,
            "analysis_timestamp": datetime.now().isoformat(),
            "ai_brain_enabled": AI_BRAIN_AVAILABLE and self.ai_brain_confidence is not None,
            "total_cache_decisions": len(self.ai_brain_cache_decisions),
            "pattern_strategies_count": len(self.confidence_cache_strategies),
            "cache_efficiency": None
        }
        
        # Analyze cache patterns
        pattern_analysis = {}
        for pattern, entries in self.confidence_cache_strategies.items():
            if entries:
                recent_entries = entries[-10:]  # Last 10 entries
                pattern_analysis[pattern] = {
                    "avg_confidence": sum([e["confidence"] for e in recent_entries]) / len(recent_entries),
                    "avg_ttl_adjustment": sum([e["ttl_adjustment"] for e in recent_entries]) / len(recent_entries),
                    "sample_count": len(entries),
                    "confidence_trend": self._calculate_confidence_trend(recent_entries)
                }
        
        analysis["pattern_analysis"] = pattern_analysis
        
        # Overall cache efficiency metrics
        if self.ai_brain_cache_decisions:
            recent_decisions = self.ai_brain_cache_decisions[-50:]  # Last 50 decisions
            avg_confidence = sum([d["confidence_score"] for d in recent_decisions]) / len(recent_decisions)
            avg_ttl_ratio = sum([d["ttl_adjustment_ratio"] for d in recent_decisions]) / len(recent_decisions)
            
            analysis["cache_efficiency"] = {
                "average_confidence": avg_confidence,
                "average_ttl_adjustment_ratio": avg_ttl_ratio,
                "efficiency_rating": "high" if avg_confidence >= 0.85 else "medium" if avg_confidence >= 0.70 else "low",
                "optimization_suggestions": self._generate_cache_optimization_suggestions(avg_confidence, avg_ttl_ratio)
            }
        
        return analysis
    
    def _calculate_confidence_trend(self, entries: List[Dict[str, Any]]) -> str:
        """Calculate confidence trend for pattern entries"""
        if len(entries) < 2:
            return "insufficient_data"
        
        # Compare first half with second half
        mid_point = len(entries) // 2
        first_half_avg = sum([e["confidence"] for e in entries[:mid_point]]) / mid_point
        second_half_avg = sum([e["confidence"] for e in entries[mid_point:]]) / (len(entries) - mid_point)
        
        if second_half_avg > first_half_avg + 0.05:
            return "improving"
        elif second_half_avg < first_half_avg - 0.05:
            return "declining"
        else:
            return "stable"
    
    def _generate_cache_optimization_suggestions(self, avg_confidence: float, avg_ttl_ratio: float) -> List[str]:
        """Generate AI Brain cache optimization suggestions"""
        suggestions = []
        
        if avg_confidence < 0.75:
            suggestions.append("🧠 Consider implementing cache warming strategies for low-confidence data")
            suggestions.append("📊 Review data quality feeding into cached operations")
        
        if avg_ttl_ratio < 0.8:
            suggestions.append("⏱️ TTL adjustments are consistently reducing cache duration - review confidence calculations")
        elif avg_ttl_ratio > 1.2:
            suggestions.append("🚀 High confidence patterns detected - consider increasing base TTL for similar patterns")
        
        if not suggestions:
            suggestions.append("✅ Cache performance is optimal with AI Brain confidence adjustments")
        
        return suggestions
    
    async def refresh_cache_with_confidence_check(self, key: str, refresh_function, confidence_threshold: float = 0.85) -> Dict[str, Any]:
        """Refresh cache entry with AI Brain confidence validation"""
        refresh_result = {
            "refreshed": False,
            "confidence_score": 0.0,
            "cached": False,
            "ai_brain_approval": False,
            "value": None
        }
        
        try:
            # Execute refresh function to get new data
            new_value = await refresh_function() if asyncio.iscoroutinefunction(refresh_function) else refresh_function()
            
            # Calculate confidence for new data if AI Brain is available
            if self.ai_brain_confidence and AI_BRAIN_AVAILABLE:
                confidence_analysis = self.ai_brain_confidence.calculate_confidence(
                    model_prediction={"data_freshness": 1.0, "refresh_success": True},
                    data_inputs={"data_size": len(str(new_value)), "data_type": type(new_value).__name__},
                    market_context={"service": self.service_name, "operation": "cache_refresh", "key_pattern": self._extract_key_pattern(key)},
                    historical_data=self._get_key_pattern_history(key),
                    risk_parameters={"refresh_frequency": "on_demand"}
                )
                
                refresh_result["confidence_score"] = confidence_analysis.composite_score
                refresh_result["ai_brain_approval"] = confidence_analysis.composite_score >= confidence_threshold
                
                # Only cache if confidence is sufficient
                if refresh_result["ai_brain_approval"]:
                    cached = await self.set_with_confidence(key, new_value, confidence_analysis.composite_score)
                    refresh_result["cached"] = cached
                    refresh_result["value"] = new_value
                else:
                    # Low confidence - don't cache, just return value
                    refresh_result["value"] = new_value
                    import logging
                    logger = logging.getLogger(f"{self.service_name}-ai-brain-cache")
                    logger.warning(f"🧠 AI Brain Cache: Refresh blocked for {key} - confidence {confidence_analysis.composite_score:.3f} below threshold {confidence_threshold}")
            else:
                # No AI Brain available - standard caching
                cached = await self.set(key, new_value)
                refresh_result["cached"] = cached
                refresh_result["value"] = new_value
                refresh_result["ai_brain_approval"] = True  # Assume approval without AI Brain
            
            refresh_result["refreshed"] = True
            
        except Exception as e:
            import logging
            logger = logging.getLogger(f"{self.service_name}-ai-brain-cache")
            logger.error(f"Cache refresh failed for {key}: {e}")
            refresh_result["error"] = str(e)
        
        return refresh_result