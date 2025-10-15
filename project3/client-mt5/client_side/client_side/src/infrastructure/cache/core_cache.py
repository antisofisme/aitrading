"""
core_cache.py - Centralized Caching System

🎯 PURPOSE:
Business: High-performance caching for trading data and operations
Technical: Multi-level caching with TTL, LRU eviction, and performance optimization
Domain: Caching/Performance/Data Storage

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:27.833Z
Session: client-side-ai-brain-full-compliance
Confidence: 90%
Complexity: medium

🧩 PATTERNS USED:
- AI_BRAIN_CACHING_SYSTEM: Multi-level caching with intelligent eviction
- PERFORMANCE_OPTIMIZATION: Cache-based performance optimization

📦 DEPENDENCIES:
Internal: logger_manager, performance_manager
External: threading, time, collections, typing

💡 AI DECISION REASONING:
High-frequency trading requires sub-millisecond data access. Multi-level caching with intelligent eviction provides optimal performance.

🚀 USAGE:
cache = CoreCache.get_instance(); price = cache.get("EURUSD_tick")

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

import threading
import time
import hashlib
import json
import pickle
import weakref
from typing import Dict, Any, Optional, List, Union, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from collections import defaultdict
import asyncio
import sys

class CacheStrategy(Enum):
    """Cache strategy types"""
    LRU = "lru"              # Least Recently Used
    LFU = "lfu"              # Least Frequently Used
    TTL = "ttl"              # Time To Live
    ADAPTIVE = "adaptive"     # AI Brain Adaptive Strategy
    PREDICTIVE = "predictive" # Predictive caching based on patterns

class CachePriority(Enum):
    """Cache priority levels"""
    CRITICAL = 1    # Never evict unless expired
    HIGH = 2        # Evict only under memory pressure
    MEDIUM = 3      # Standard eviction rules
    LOW = 4         # First to evict

@dataclass
class CacheEntry:
    """Cache entry with AI Brain metadata"""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int
    ttl: Optional[int] = None
    priority: CachePriority = CachePriority.MEDIUM
    size_bytes: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.size_bytes == 0:
            self.size_bytes = self._calculate_size()
    
    def _calculate_size(self) -> int:
        """Calculate entry size in bytes"""
        try:
            return sys.getsizeof(pickle.dumps(self.value))
        except:
            return sys.getsizeof(str(self.value))
    
    @property
    def is_expired(self) -> bool:
        """Check if entry is expired"""
        if self.ttl is None:
            return False
        return (datetime.now() - self.created_at).seconds > self.ttl
    
    @property
    def age_seconds(self) -> int:
        """Get entry age in seconds"""
        return int((datetime.now() - self.created_at).total_seconds())
    
    @property
    def idle_seconds(self) -> int:
        """Get idle time since last access"""
        return int((datetime.now() - self.last_accessed).total_seconds())

@dataclass
class CacheStats:
    """Cache statistics for AI Brain learning"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_requests: int = 0
    average_response_time: float = 0.0
    memory_usage_bytes: int = 0
    hit_rate: float = 0.0
    
    def update_hit_rate(self):
        """Update hit rate calculation"""
        if self.total_requests > 0:
            self.hit_rate = self.hits / self.total_requests
        else:
            self.hit_rate = 0.0

@dataclass
class AccessPattern:
    """Access pattern for predictive caching"""
    key: str
    access_times: List[datetime]
    frequency: float
    predictive_weight: float = 1.0
    next_predicted_access: Optional[datetime] = None

class CoreCache:
    """
    AI Brain Core Cache System
    Intelligent caching with adaptive strategies and pattern learning
    """
    
    def __init__(self, 
                 name: str,
                 max_size: int = 1000,
                 max_memory_mb: int = 100,
                 default_ttl: int = 3600,
                 strategy: CacheStrategy = CacheStrategy.ADAPTIVE,
                 enable_persistence: bool = False,
                 persistence_path: Optional[str] = None):
        
        self.name = name
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.default_ttl = default_ttl
        self.strategy = strategy
        self.enable_persistence = enable_persistence
        
        # Cache storage
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: List[str] = []  # For LRU
        self._frequency_counter: Dict[str, int] = defaultdict(int)  # For LFU
        self._lock = threading.RLock()
        
        # AI Brain features
        self._access_patterns: Dict[str, AccessPattern] = {}
        self._usage_statistics: Dict[str, CacheStats] = {}
        self._global_stats = CacheStats()
        self._adaptive_weights: Dict[str, float] = {
            'recency': 0.4,
            'frequency': 0.3,
            'size': 0.2,
            'priority': 0.1
        }
        
        # Persistence
        if persistence_path:
            self.persistence_path = Path(persistence_path)
        else:
            self.persistence_path = Path(f"logs/cache_{name}.pkl")
        
        # Performance monitoring
        self._performance_history: List[Tuple[datetime, float]] = []
        self._last_cleanup = datetime.now()
        
        # Initialize cache
        self._initialize_cache()
    
    def _initialize_cache(self):
        """Initialize cache system"""
        if self.enable_persistence:
            self._load_from_persistence()
        
        # Start background tasks
        if hasattr(asyncio, 'create_task'):
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(self._background_maintenance())
                loop.create_task(self._pattern_analysis())
            except RuntimeError:
                # No event loop available, skip async tasks
                pass
    
    async def _background_maintenance(self):
        """Background maintenance tasks"""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                self._cleanup_expired()
                self._adaptive_strategy_update()
                
                if self.enable_persistence and (datetime.now() - self._last_cleanup).seconds > 300:
                    self._save_to_persistence()
                    self._last_cleanup = datetime.now()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Cache background maintenance error: {e}")
    
    async def _pattern_analysis(self):
        """Analyze access patterns for predictive caching"""
        while True:
            try:
                await asyncio.sleep(120)  # Run every 2 minutes
                self._analyze_access_patterns()
                self._predict_future_access()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Pattern analysis error: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache with AI Brain optimization"""
        start_time = time.time()
        
        with self._lock:
            # Update statistics
            self._global_stats.total_requests += 1
            
            # Check if key exists and is valid
            if key in self._cache:
                entry = self._cache[key]
                
                # Check expiration
                if entry.is_expired:
                    self._remove_entry(key)
                    self._global_stats.misses += 1
                    self._record_performance(start_time)
                    return default
                
                # Update access metadata
                entry.last_accessed = datetime.now()
                entry.access_count += 1
                self._frequency_counter[key] += 1
                
                # Update LRU order
                if key in self._access_order:
                    self._access_order.remove(key)
                self._access_order.append(key)
                
                # Record access pattern
                self._record_access_pattern(key)
                
                # Update statistics
                self._global_stats.hits += 1
                self._global_stats.update_hit_rate()
                
                self._record_performance(start_time)
                return entry.value
            
            # Cache miss
            self._global_stats.misses += 1
            self._global_stats.update_hit_rate()
            self._record_performance(start_time)
            return default
    
    def set(self, key: str, value: Any, 
            ttl: Optional[int] = None,
            priority: CachePriority = CachePriority.MEDIUM,
            metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Set value in cache with AI Brain optimization"""
        
        with self._lock:
            # Use default TTL if not specified
            if ttl is None:
                ttl = self._determine_optimal_ttl(key, value)
            
            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                access_count=1,
                ttl=ttl,
                priority=priority,
                metadata=metadata or {}
            )
            
            # Check if we need to evict entries
            if not self._ensure_capacity(entry.size_bytes):
                return False  # Could not make space
            
            # Store entry
            self._cache[key] = entry
            
            # Update tracking structures
            if key not in self._access_order:
                self._access_order.append(key)
            self._frequency_counter[key] = 1
            
            # Update global memory usage
            self._update_memory_stats()
            
            return True
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        with self._lock:
            if key in self._cache:
                self._remove_entry(key)
                return True
            return False
    
    def clear(self):
        """Clear entire cache"""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()
            self._frequency_counter.clear()
            self._access_patterns.clear()
            self._global_stats = CacheStats()
    
    def exists(self, key: str) -> bool:
        """Check if key exists and is valid"""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                return not entry.is_expired
            return False
    
    def keys(self) -> List[str]:
        """Get all valid keys"""
        with self._lock:
            valid_keys = []
            for key, entry in self._cache.items():
                if not entry.is_expired:
                    valid_keys.append(key)
            return valid_keys
    
    def size(self) -> int:
        """Get current cache size"""
        return len(self._cache)
    
    def memory_usage(self) -> int:
        """Get current memory usage in bytes"""
        with self._lock:
            return sum(entry.size_bytes for entry in self._cache.values())
    
    # ==================== AI BRAIN OPTIMIZATION METHODS ====================
    
    def _determine_optimal_ttl(self, key: str, value: Any) -> int:
        """Determine optimal TTL based on AI Brain patterns"""
        # Check access patterns for this key
        if key in self._access_patterns:
            pattern = self._access_patterns[key]
            
            # Adjust TTL based on access frequency
            if pattern.frequency > 10:  # High frequency access
                return self.default_ttl * 2  # Keep longer
            elif pattern.frequency > 1:   # Medium frequency
                return self.default_ttl
            else:                         # Low frequency
                return self.default_ttl // 2  # Shorter TTL
        
        # Default TTL for new keys
        return self.default_ttl
    
    def _ensure_capacity(self, needed_bytes: int) -> bool:
        """Ensure cache has capacity using AI Brain strategies"""
        current_memory = self.memory_usage()
        current_size = len(self._cache)
        
        # Check size limit
        if current_size >= self.max_size:
            if not self._evict_entries(size_based=True):
                return False
        
        # Check memory limit
        if current_memory + needed_bytes > self.max_memory_bytes:
            if not self._evict_entries(memory_based=True, needed_bytes=needed_bytes):
                return False
        
        return True
    
    def _evict_entries(self, size_based: bool = False, memory_based: bool = False, 
                      needed_bytes: int = 0) -> bool:
        """Evict entries using AI Brain strategies"""
        
        if self.strategy == CacheStrategy.ADAPTIVE:
            return self._adaptive_eviction(needed_bytes)
        elif self.strategy == CacheStrategy.LRU:
            return self._lru_eviction(needed_bytes)
        elif self.strategy == CacheStrategy.LFU:
            return self._lfu_eviction(needed_bytes)
        elif self.strategy == CacheStrategy.PREDICTIVE:
            return self._predictive_eviction(needed_bytes)
        else:
            return self._lru_eviction(needed_bytes)  # Fallback
    
    def _adaptive_eviction(self, needed_bytes: int) -> bool:
        """AI Brain adaptive eviction strategy"""
        # Score all entries for eviction
        eviction_scores = {}
        
        for key, entry in self._cache.items():
            if entry.priority == CachePriority.CRITICAL:
                continue  # Never evict critical entries
            
            score = self._calculate_eviction_score(entry)
            eviction_scores[key] = score
        
        # Sort by eviction score (higher score = more likely to evict)
        sorted_entries = sorted(eviction_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Evict entries until we have enough space
        freed_bytes = 0
        evicted = 0
        
        for key, score in sorted_entries:
            entry = self._cache[key]
            
            # Stop if we've freed enough memory and entries
            if (needed_bytes > 0 and freed_bytes >= needed_bytes) or evicted >= 10:
                break
            
            # Evict entry
            freed_bytes += entry.size_bytes
            evicted += 1
            self._remove_entry(key)
            self._global_stats.evictions += 1
        
        return evicted > 0
    
    def _calculate_eviction_score(self, entry: CacheEntry) -> float:
        """Calculate eviction score using AI Brain weighted factors"""
        
        # Recency factor (higher = more recently accessed = lower eviction score)
        recency_score = 1.0 / (1.0 + entry.idle_seconds / 3600.0)  # Normalize by hours
        
        # Frequency factor (higher = more frequently accessed = lower eviction score)  
        frequency_score = 1.0 / (1.0 + entry.access_count)
        
        # Size factor (larger = higher eviction score)
        size_score = entry.size_bytes / (1024 * 1024)  # Normalize by MB
        
        # Priority factor (higher priority = lower eviction score)
        priority_score = entry.priority.value / 4.0  # Normalize by max priority
        
        # Combine factors with AI Brain adaptive weights
        eviction_score = (
            self._adaptive_weights['recency'] * (1.0 - recency_score) +
            self._adaptive_weights['frequency'] * (1.0 - frequency_score) +
            self._adaptive_weights['size'] * size_score +
            self._adaptive_weights['priority'] * priority_score
        )
        
        return eviction_score
    
    def _lru_eviction(self, needed_bytes: int) -> bool:
        """Least Recently Used eviction"""
        evicted = 0
        freed_bytes = 0
        
        # Evict oldest entries first
        for key in self._access_order[:]:
            if key in self._cache:
                entry = self._cache[key]
                
                if entry.priority == CachePriority.CRITICAL:
                    continue
                
                freed_bytes += entry.size_bytes
                evicted += 1
                self._remove_entry(key)
                
                if (needed_bytes > 0 and freed_bytes >= needed_bytes) or evicted >= 10:
                    break
        
        return evicted > 0
    
    def _lfu_eviction(self, needed_bytes: int) -> bool:
        """Least Frequently Used eviction"""
        # Sort by frequency (ascending)
        sorted_by_freq = sorted(self._frequency_counter.items(), key=lambda x: x[1])
        
        evicted = 0
        freed_bytes = 0
        
        for key, freq in sorted_by_freq:
            if key in self._cache:
                entry = self._cache[key]
                
                if entry.priority == CachePriority.CRITICAL:
                    continue
                
                freed_bytes += entry.size_bytes
                evicted += 1
                self._remove_entry(key)
                
                if (needed_bytes > 0 and freed_bytes >= needed_bytes) or evicted >= 10:
                    break
        
        return evicted > 0
    
    def _predictive_eviction(self, needed_bytes: int) -> bool:
        """Predictive eviction based on access patterns"""
        # Score entries based on predicted future access
        prediction_scores = {}
        
        for key, entry in self._cache.items():
            if entry.priority == CachePriority.CRITICAL:
                continue
                
            # Get access pattern
            if key in self._access_patterns:
                pattern = self._access_patterns[key]
                if pattern.next_predicted_access:
                    time_to_next = (pattern.next_predicted_access - datetime.now()).total_seconds()
                    # Higher score = less likely to be accessed soon
                    prediction_scores[key] = max(0, time_to_next / 3600.0)  # Normalize by hours
                else:
                    prediction_scores[key] = 24.0  # Assume 24 hours if no prediction
            else:
                prediction_scores[key] = 12.0  # Default 12 hours for unknown patterns
        
        # Sort by prediction score (higher = evict first)
        sorted_entries = sorted(prediction_scores.items(), key=lambda x: x[1], reverse=True)
        
        evicted = 0
        freed_bytes = 0
        
        for key, score in sorted_entries:
            if key in self._cache:
                entry = self._cache[key]
                freed_bytes += entry.size_bytes
                evicted += 1
                self._remove_entry(key)
                
                if (needed_bytes > 0 and freed_bytes >= needed_bytes) or evicted >= 10:
                    break
        
        return evicted > 0
    
    def _remove_entry(self, key: str):
        """Remove entry and clean up tracking structures"""
        if key in self._cache:
            del self._cache[key]
        
        if key in self._access_order:
            self._access_order.remove(key)
        
        if key in self._frequency_counter:
            del self._frequency_counter[key]
        
        self._update_memory_stats()
    
    def _record_access_pattern(self, key: str):
        """Record access pattern for predictive caching"""
        now = datetime.now()
        
        if key not in self._access_patterns:
            self._access_patterns[key] = AccessPattern(
                key=key,
                access_times=[now],
                frequency=1.0
            )
        else:
            pattern = self._access_patterns[key]
            pattern.access_times.append(now)
            
            # Keep only last 100 access times
            if len(pattern.access_times) > 100:
                pattern.access_times = pattern.access_times[-100:]
            
            # Update frequency
            pattern.frequency = len(pattern.access_times)
    
    def _analyze_access_patterns(self):
        """Analyze access patterns for optimization"""
        for key, pattern in self._access_patterns.items():
            if len(pattern.access_times) >= 3:
                # Calculate average interval between accesses
                intervals = []
                for i in range(1, len(pattern.access_times)):
                    interval = (pattern.access_times[i] - pattern.access_times[i-1]).total_seconds()
                    intervals.append(interval)
                
                if intervals:
                    avg_interval = sum(intervals) / len(intervals)
                    # Predict next access
                    last_access = pattern.access_times[-1]
                    pattern.next_predicted_access = last_access + timedelta(seconds=avg_interval)
    
    def _predict_future_access(self):
        """Predict future cache access and preload if needed"""
        # This is a placeholder for more advanced predictive logic
        # In a full implementation, you might use machine learning models
        pass
    
    def _adaptive_strategy_update(self):
        """Update adaptive strategy weights based on performance"""
        # Analyze recent performance and adjust weights
        if len(self._performance_history) >= 10:
            recent_performance = self._performance_history[-10:]
            avg_response_time = sum(perf[1] for perf in recent_performance) / len(recent_performance)
            
            # Adjust weights based on hit rate and response time
            if self._global_stats.hit_rate < 0.7:  # Low hit rate
                # Increase recency and frequency weights
                self._adaptive_weights['recency'] = min(0.5, self._adaptive_weights['recency'] + 0.05)
                self._adaptive_weights['frequency'] = min(0.4, self._adaptive_weights['frequency'] + 0.05)
            
            if avg_response_time > 0.01:  # High response time
                # Increase size weight to evict larger items
                self._adaptive_weights['size'] = min(0.3, self._adaptive_weights['size'] + 0.05)
    
    def _record_performance(self, start_time: float):
        """Record performance metrics"""
        duration = time.time() - start_time
        self._performance_history.append((datetime.now(), duration))
        
        # Keep only last 1000 measurements
        if len(self._performance_history) > 1000:
            self._performance_history = self._performance_history[-1000:]
        
        # Update global average
        if len(self._performance_history) > 0:
            total_time = sum(perf[1] for perf in self._performance_history)
            self._global_stats.average_response_time = total_time / len(self._performance_history)
    
    def _update_memory_stats(self):
        """Update memory usage statistics"""
        self._global_stats.memory_usage_bytes = self.memory_usage()
    
    def _cleanup_expired(self):
        """Clean up expired entries"""
        with self._lock:
            expired_keys = []
            
            for key, entry in self._cache.items():
                if entry.is_expired:
                    expired_keys.append(key)
            
            for key in expired_keys:
                self._remove_entry(key)
    
    # ==================== PERSISTENCE METHODS ====================
    
    def _save_to_persistence(self):
        """Save cache to persistent storage"""
        if not self.enable_persistence:
            return
        
        try:
            # Ensure directory exists
            self.persistence_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Prepare data for serialization
            cache_data = {
                'entries': {},
                'access_patterns': {},
                'stats': asdict(self._global_stats),
                'adaptive_weights': self._adaptive_weights,
                'timestamp': datetime.now().isoformat()
            }
            
            # Serialize cache entries (excluding expired ones)
            for key, entry in self._cache.items():
                if not entry.is_expired:
                    cache_data['entries'][key] = {
                        'value': entry.value,
                        'created_at': entry.created_at.isoformat(),
                        'last_accessed': entry.last_accessed.isoformat(),
                        'access_count': entry.access_count,
                        'ttl': entry.ttl,
                        'priority': entry.priority.value,
                        'metadata': entry.metadata
                    }
            
            # Serialize access patterns
            for key, pattern in self._access_patterns.items():
                cache_data['access_patterns'][key] = {
                    'access_times': [t.isoformat() for t in pattern.access_times[-10:]],  # Keep last 10
                    'frequency': pattern.frequency,
                    'predictive_weight': pattern.predictive_weight
                }
            
            with open(self.persistence_path, 'wb') as f:
                pickle.dump(cache_data, f)
                
        except Exception as e:
            print(f"Failed to save cache to persistence: {e}")
    
    def _load_from_persistence(self):
        """Load cache from persistent storage"""
        if not self.persistence_path.exists():
            return
        
        try:
            with open(self.persistence_path, 'rb') as f:
                cache_data = pickle.load(f)
            
            # Restore cache entries
            for key, entry_data in cache_data.get('entries', {}).items():
                try:
                    entry = CacheEntry(
                        key=key,
                        value=entry_data['value'],
                        created_at=datetime.fromisoformat(entry_data['created_at']),
                        last_accessed=datetime.fromisoformat(entry_data['last_accessed']),
                        access_count=entry_data['access_count'],
                        ttl=entry_data['ttl'],
                        priority=CachePriority(entry_data['priority']),
                        metadata=entry_data.get('metadata', {})
                    )
                    
                    # Only restore non-expired entries
                    if not entry.is_expired:
                        self._cache[key] = entry
                        self._access_order.append(key)
                        self._frequency_counter[key] = entry.access_count
                        
                except Exception as e:
                    print(f"Failed to restore cache entry {key}: {e}")
            
            # Restore access patterns
            for key, pattern_data in cache_data.get('access_patterns', {}).items():
                try:
                    access_times = [datetime.fromisoformat(t) for t in pattern_data['access_times']]
                    self._access_patterns[key] = AccessPattern(
                        key=key,
                        access_times=access_times,
                        frequency=pattern_data['frequency'],
                        predictive_weight=pattern_data.get('predictive_weight', 1.0)
                    )
                except Exception as e:
                    print(f"Failed to restore access pattern {key}: {e}")
            
            # Restore adaptive weights
            if 'adaptive_weights' in cache_data:
                self._adaptive_weights.update(cache_data['adaptive_weights'])
            
            print(f"Cache {self.name} loaded from persistence: {len(self._cache)} entries")
            
        except Exception as e:
            print(f"Failed to load cache from persistence: {e}")
    
    # ==================== STATISTICS AND MONITORING ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        self._update_memory_stats()
        
        return {
            'name': self.name,
            'size': len(self._cache),
            'max_size': self.max_size,
            'memory_usage_mb': self._global_stats.memory_usage_bytes / (1024 * 1024),
            'max_memory_mb': self.max_memory_bytes / (1024 * 1024),
            'hit_rate': self._global_stats.hit_rate,
            'hits': self._global_stats.hits,
            'misses': self._global_stats.misses,
            'evictions': self._global_stats.evictions,
            'total_requests': self._global_stats.total_requests,
            'average_response_time_ms': self._global_stats.average_response_time * 1000,
            'strategy': self.strategy.value,
            'adaptive_weights': self._adaptive_weights.copy(),
            'access_patterns': len(self._access_patterns),
            'expired_entries': sum(1 for entry in self._cache.values() if entry.is_expired)
        }
    
    def get_top_accessed_keys(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most accessed keys"""
        with self._lock:
            sorted_entries = sorted(
                self._cache.items(),
                key=lambda x: x[1].access_count,
                reverse=True
            )
            
            return [
                {
                    'key': key,
                    'access_count': entry.access_count,
                    'age_seconds': entry.age_seconds,
                    'idle_seconds': entry.idle_seconds,
                    'size_bytes': entry.size_bytes
                }
                for key, entry in sorted_entries[:limit]
            ]
    
    def optimize_cache(self):
        """Trigger cache optimization"""
        self._cleanup_expired()
        self._adaptive_strategy_update()
        self._analyze_access_patterns()
        
        if self.enable_persistence:
            self._save_to_persistence()