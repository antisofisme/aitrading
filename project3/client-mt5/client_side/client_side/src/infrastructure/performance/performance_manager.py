"""
performance_manager.py - Performance Monitoring & Optimization

🎯 PURPOSE:
Business: Comprehensive performance monitoring and optimization for trading operations
Technical: Real-time performance tracking with adaptive optimization and intelligent caching
Domain: Performance/Optimization/System Monitoring

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:27.751Z
Session: client-side-ai-brain-full-compliance
Confidence: 93%
Complexity: high

🧩 PATTERNS USED:
- AI_BRAIN_PERFORMANCE_OPTIMIZATION: Adaptive performance management with AI insights
- INTELLIGENT_CACHING: Smart caching based on usage patterns

📦 DEPENDENCIES:
Internal: centralized_logger, config_manager
External: psutil, threading, asyncio, gc, weakref

💡 AI DECISION REASONING:
Performance manager designed for high-frequency trading requirements with sub-millisecond latency targets and memory optimization.

🚀 USAGE:
manager = ClientPerformanceManager.get_instance(); with manager.track_operation("trade"): execute_trade()

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

import time
import threading
import asyncio
import psutil
import gc
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from functools import wraps
from contextlib import contextmanager
import weakref
from collections import defaultdict, deque
import json

@dataclass
class PerformanceMetric:
    """Performance metric data"""
    operation: str
    component: str
    start_time: datetime
    end_time: datetime
    duration_ms: float
    memory_before_mb: float
    memory_after_mb: float
    cpu_percent: float
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ComponentStats:
    """Component performance statistics"""
    component: str
    total_operations: int
    total_time_ms: float
    avg_time_ms: float
    min_time_ms: float
    max_time_ms: float
    success_rate: float
    memory_avg_mb: float
    last_operation: datetime
    
class PerformanceCache:
    """Performance-optimized caching system"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, datetime] = {}
        self.access_counts: Dict[str, int] = defaultdict(int)
        self.max_size = max_size
        self.ttl = timedelta(seconds=ttl_seconds)
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value with TTL check"""
        with self.lock:
            if key not in self.cache:
                return None
            
            # Check TTL
            if datetime.now() - self.access_times[key] > self.ttl:
                self._remove(key)
                return None
            
            # Update access stats
            self.access_times[key] = datetime.now()
            self.access_counts[key] += 1
            
            return self.cache[key]['value']
    
    def set(self, key: str, value: Any, ttl_override: Optional[int] = None) -> bool:
        """Set cached value with optional TTL override"""
        with self.lock:
            # Manage cache size
            if len(self.cache) >= self.max_size:
                self._evict_lru()
            
            # Store value
            self.cache[key] = {
                'value': value,
                'created': datetime.now(),
                'ttl': ttl_override or self.ttl.total_seconds()
            }
            self.access_times[key] = datetime.now()
            self.access_counts[key] = 1
            
            return True
    
    def _remove(self, key: str):
        """Remove key from cache"""
        self.cache.pop(key, None)
        self.access_times.pop(key, None)
        self.access_counts.pop(key, None)
    
    def _evict_lru(self):
        """Evict least recently used items"""
        if not self.access_times:
            return
        
        # Find oldest access time
        oldest_key = min(self.access_times.keys(), 
                        key=lambda k: self.access_times[k])
        self._remove(oldest_key)
    
    def clear(self):
        """Clear all cached items"""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
            self.access_counts.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_accesses = sum(self.access_counts.values())
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'total_accesses': total_accesses,
                'hit_rate': len(self.cache) / max(total_accesses, 1) * 100,
                'ttl_seconds': self.ttl.total_seconds()
            }

class ClientPerformanceManager:
    """
    Client-Side Centralized Performance Manager
    Manages performance optimization and monitoring for MT5 Trading Client
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        self.metrics_history: deque = deque(maxlen=10000)
        self.component_stats: Dict[str, ComponentStats] = {}
        self.active_operations: Dict[str, datetime] = {}
        
        # Performance caches for different components
        self.caches: Dict[str, PerformanceCache] = {
            'import_cache': PerformanceCache(max_size=500, ttl_seconds=3600),
            'config_cache': PerformanceCache(max_size=200, ttl_seconds=1800),
            'logger_cache': PerformanceCache(max_size=100, ttl_seconds=600),
            'data_cache': PerformanceCache(max_size=1000, ttl_seconds=300)
        }
        
        # System monitoring
        self.system_stats_history: deque = deque(maxlen=1000)
        self.monitoring_enabled = True
        self.monitoring_task = None
        
        # Memory pool for object reuse
        self.object_pools: Dict[str, List[Any]] = defaultdict(list)
        
        # Start background monitoring
        self._start_monitoring()
    
    @classmethod
    def get_instance(cls) -> 'ClientPerformanceManager':
        """Singleton pattern with thread safety"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def _start_monitoring(self):
        """Start background system monitoring"""
        if not self.monitoring_enabled:
            return
        
        def monitor_system():
            while self.monitoring_enabled:
                try:
                    # Collect system stats
                    cpu_percent = psutil.cpu_percent(interval=1)
                    memory = psutil.virtual_memory()
                    
                    self.system_stats_history.append({
                        'timestamp': datetime.now(),
                        'cpu_percent': cpu_percent,
                        'memory_percent': memory.percent,
                        'memory_used_mb': memory.used / 1024 / 1024,
                        'active_operations': len(self.active_operations)
                    })
                    
                    time.sleep(5)  # Monitor every 5 seconds
                    
                except Exception:
                    pass  # Silent monitoring
        
        monitor_thread = threading.Thread(target=monitor_system, daemon=True)
        monitor_thread.start()
    
    @contextmanager
    def track_operation(self, operation: str, component: str, 
                       metadata: Optional[Dict[str, Any]] = None):
        """Context manager for tracking operation performance"""
        operation_id = f"{component}:{operation}:{datetime.now().timestamp()}"
        
        # Start tracking
        start_time = datetime.now()
        memory_before = psutil.Process().memory_info().rss / 1024 / 1024
        cpu_before = psutil.cpu_percent()
        
        self.active_operations[operation_id] = start_time
        
        success = True
        error = None
        
        try:
            yield operation_id
        except Exception as e:
            success = False
            error = str(e)
            raise
        finally:
            # End tracking
            end_time = datetime.now()
            memory_after = psutil.Process().memory_info().rss / 1024 / 1024
            cpu_after = psutil.cpu_percent()
            
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            # Create metric
            metric = PerformanceMetric(
                operation=operation,
                component=component,
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                memory_before_mb=memory_before,
                memory_after_mb=memory_after,
                cpu_percent=(cpu_before + cpu_after) / 2,
                success=success,
                error=error,
                metadata=metadata or {}
            )
            
            # Store metric
            self.metrics_history.append(metric)
            self._update_component_stats(metric)
            
            # Cleanup
            self.active_operations.pop(operation_id, None)
    
    def _update_component_stats(self, metric: PerformanceMetric):
        """Update component statistics"""
        component = metric.component
        
        if component not in self.component_stats:
            self.component_stats[component] = ComponentStats(
                component=component,
                total_operations=0,
                total_time_ms=0.0,
                avg_time_ms=0.0,
                min_time_ms=float('inf'),
                max_time_ms=0.0,
                success_rate=0.0,
                memory_avg_mb=0.0,
                last_operation=metric.end_time
            )
        
        stats = self.component_stats[component]
        
        # Update counters
        stats.total_operations += 1
        stats.total_time_ms += metric.duration_ms
        stats.avg_time_ms = stats.total_time_ms / stats.total_operations
        stats.min_time_ms = min(stats.min_time_ms, metric.duration_ms)
        stats.max_time_ms = max(stats.max_time_ms, metric.duration_ms)
        stats.last_operation = metric.end_time
        
        # Calculate success rate
        recent_metrics = [m for m in self.metrics_history 
                         if m.component == component]
        successful = sum(1 for m in recent_metrics if m.success)
        stats.success_rate = (successful / len(recent_metrics)) * 100 if recent_metrics else 0
        
        # Update memory average
        memory_values = [m.memory_after_mb for m in recent_metrics]
        stats.memory_avg_mb = sum(memory_values) / len(memory_values) if memory_values else 0
    
    def get_cache(self, cache_name: str) -> PerformanceCache:
        """Get performance cache by name"""
        if cache_name not in self.caches:
            self.caches[cache_name] = PerformanceCache()
        return self.caches[cache_name]
    
    def cached_operation(self, cache_name: str, key: str, 
                        operation: Callable, ttl: Optional[int] = None) -> Any:
        """Execute operation with caching"""
        cache = self.get_cache(cache_name)
        
        # Try cache first
        cached_result = cache.get(key)
        if cached_result is not None:
            return cached_result
        
        # Execute operation and cache result
        result = operation()
        cache.set(key, result, ttl)
        
        return result
    
    def get_object_from_pool(self, object_type: str, factory: Callable) -> Any:
        """Get object from pool or create new one"""
        pool = self.object_pools[object_type]
        
        if pool:
            return pool.pop()
        else:
            return factory()
    
    def return_to_pool(self, object_type: str, obj: Any):
        """Return object to pool for reuse"""
        pool = self.object_pools[object_type]
        
        # Limit pool size
        if len(pool) < 50:
            # Reset object if it has a reset method
            if hasattr(obj, 'reset'):
                obj.reset()
            pool.append(obj)
    
    def optimize_memory(self):
        """Optimize memory usage"""
        # Force garbage collection
        gc.collect()
        
        # Clear old metrics
        if len(self.metrics_history) > 5000:
            # Keep only recent 2000 metrics
            recent_metrics = list(self.metrics_history)[-2000:]
            self.metrics_history.clear()
            self.metrics_history.extend(recent_metrics)
        
        # Clear cache if memory usage is high
        memory = psutil.virtual_memory()
        if memory.percent > 80:
            for cache in self.caches.values():
                cache.clear()
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        # Component statistics
        component_data = {name: asdict(stats) 
                         for name, stats in self.component_stats.items()}
        
        # Cache statistics
        cache_data = {name: cache.get_stats() 
                     for name, cache in self.caches.items()}
        
        # System statistics
        recent_system_stats = list(self.system_stats_history)[-100:]
        if recent_system_stats:
            avg_cpu = sum(s['cpu_percent'] for s in recent_system_stats) / len(recent_system_stats)
            avg_memory = sum(s['memory_percent'] for s in recent_system_stats) / len(recent_system_stats)
        else:
            avg_cpu = avg_memory = 0
        
        # Recent performance metrics
        recent_metrics = list(self.metrics_history)[-100:]
        avg_duration = sum(m.duration_ms for m in recent_metrics) / len(recent_metrics) if recent_metrics else 0
        
        return {
            'summary': {
                'total_operations': len(self.metrics_history),
                'active_operations': len(self.active_operations),
                'avg_cpu_percent': avg_cpu,
                'avg_memory_percent': avg_memory,
                'avg_operation_duration_ms': avg_duration
            },
            'components': component_data,
            'caches': cache_data,
            'system_health': {
                'memory_optimized': len(self.metrics_history) < 8000,
                'cache_efficiency': sum(c['hit_rate'] for c in cache_data.values()) / len(cache_data) if cache_data else 0,
                'monitoring_active': self.monitoring_enabled
            }
        }
    
    def get_slowest_operations(self, limit: int = 10) -> List[PerformanceMetric]:
        """Get slowest operations"""
        return sorted(self.metrics_history, 
                     key=lambda m: m.duration_ms, 
                     reverse=True)[:limit]
    
    def get_component_performance(self, component: str) -> Optional[ComponentStats]:
        """Get performance stats for specific component"""
        return self.component_stats.get(component)
    
    def clear_metrics(self, older_than_hours: Optional[int] = None):
        """Clear performance metrics"""
        if older_than_hours:
            cutoff = datetime.now() - timedelta(hours=older_than_hours)
            filtered_metrics = [m for m in self.metrics_history 
                              if m.end_time > cutoff]
            self.metrics_history.clear()
            self.metrics_history.extend(filtered_metrics)
        else:
            self.metrics_history.clear()
            self.component_stats.clear()
    
    def shutdown(self):
        """Shutdown performance manager"""
        self.monitoring_enabled = False
        for cache in self.caches.values():
            cache.clear()


# Performance tracking decorator
def performance_tracked(operation_name: str, component: str = "unknown", 
                       metadata: Optional[Dict[str, Any]] = None):
    """Decorator for tracking function performance"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            manager = ClientPerformanceManager.get_instance()
            with manager.track_operation(operation_name, component, metadata):
                return func(*args, **kwargs)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            manager = ClientPerformanceManager.get_instance()
            with manager.track_operation(operation_name, component, metadata):
                return await func(*args, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper
    return decorator


# Global instance
client_performance_manager = ClientPerformanceManager.get_instance()

# Convenience functions
def track_performance(operation: str, component: str, metadata: Optional[Dict[str, Any]] = None):
    """Track operation performance"""
    return client_performance_manager.track_operation(operation, component, metadata)

def get_performance_cache(cache_name: str) -> PerformanceCache:
    """Get performance cache"""
    return client_performance_manager.get_cache(cache_name)

def get_performance_report() -> Dict[str, Any]:
    """Get performance report"""
    return client_performance_manager.get_performance_report()

def optimize_memory():
    """Optimize memory usage"""
    return client_performance_manager.optimize_memory()