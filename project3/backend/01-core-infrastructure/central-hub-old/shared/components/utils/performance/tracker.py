"""
Performance Tracker utility untuk monitoring service performance
Menyediakan comprehensive performance monitoring dan metrics collection
"""

import time
import asyncio
import psutil
import logging as python_logging
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque, defaultdict
from contextlib import contextmanager
import threading
from statistics import mean, median, stdev


@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    operation: str
    duration_ms: float
    timestamp: float
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemMetrics:
    """System resource metrics"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    timestamp: float


@dataclass
class OperationStats:
    """Statistics for an operation"""
    operation: str
    total_calls: int
    successful_calls: int
    failed_calls: int
    avg_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    median_duration_ms: float
    p95_duration_ms: float
    p99_duration_ms: float
    success_rate: float
    error_rate: float
    calls_per_second: float
    recent_errors: List[str]


class PerformanceTracker:
    """
    Comprehensive performance tracker untuk service monitoring
    """

    def __init__(self, service_name: str, max_metrics: int = 10000):
        self.service_name = service_name
        self.max_metrics = max_metrics
        self.metrics: deque = deque(maxlen=max_metrics)
        self.system_metrics: deque = deque(maxlen=1000)
        self.start_time = time.time()
        self.logger = python_logging.getLogger(f"{service_name}.performance")

        # Thread-safe lock for metrics
        self._lock = threading.Lock()

        # Cached statistics (updated periodically)
        self._cached_stats: Dict[str, OperationStats] = {}
        self._last_stats_update = 0
        self._stats_cache_duration = 60  # Update every 60 seconds

        # System monitoring
        self._system_monitor_running = False
        self._system_monitor_task = None

    def start_system_monitoring(self, interval_seconds: int = 30):
        """Start system resource monitoring"""
        if not self._system_monitor_running:
            self._system_monitor_running = True
            self._system_monitor_task = asyncio.create_task(
                self._system_monitor_loop(interval_seconds)
            )
            self.logger.info("System monitoring started")

    def stop_system_monitoring(self):
        """Stop system resource monitoring"""
        if self._system_monitor_running:
            self._system_monitor_running = False
            if self._system_monitor_task:
                self._system_monitor_task.cancel()
            self.logger.info("System monitoring stopped")

    async def _system_monitor_loop(self, interval_seconds: int):
        """System monitoring loop"""
        while self._system_monitor_running:
            try:
                await self._collect_system_metrics()
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"System monitoring error: {str(e)}")
                await asyncio.sleep(interval_seconds)

    async def _collect_system_metrics(self):
        """Collect system resource metrics"""
        try:
            # CPU and Memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()

            # Disk usage for current directory
            disk = psutil.disk_usage('.')

            # Network stats
            network = psutil.net_io_counters()

            system_metric = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / (1024 * 1024),
                memory_available_mb=memory.available / (1024 * 1024),
                disk_usage_percent=disk.percent,
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv,
                timestamp=time.time()
            )

            with self._lock:
                self.system_metrics.append(system_metric)

        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {str(e)}")

    def record_operation(self,
                        operation: str,
                        duration_ms: float,
                        success: bool = True,
                        error: Optional[str] = None,
                        **metadata):
        """Record operation performance metric"""
        metric = PerformanceMetric(
            operation=operation,
            duration_ms=duration_ms,
            timestamp=time.time(),
            success=success,
            error=error,
            metadata=metadata
        )

        with self._lock:
            self.metrics.append(metric)

        self.logger.debug(f"Recorded {operation}: {duration_ms:.2f}ms (success: {success})")

    @contextmanager
    def measure(self, operation: str, **metadata):
        """Context manager for measuring operation duration"""
        start_time = time.time()
        error = None
        success = True

        try:
            yield
        except Exception as e:
            error = str(e)
            success = False
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.record_operation(operation, duration_ms, success, error, **metadata)

    async def measure_async(self, operation: str, func: Callable, *args, **kwargs):
        """Measure async function execution"""
        start_time = time.time()
        error = None
        success = True

        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            error = str(e)
            success = False
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.record_operation(operation, duration_ms, success, error)

    def get_operation_stats(self, operation: str, time_window_minutes: Optional[int] = None) -> Optional[OperationStats]:
        """Get statistics for a specific operation"""
        current_time = time.time()
        cutoff_time = current_time - (time_window_minutes * 60) if time_window_minutes else 0

        with self._lock:
            operation_metrics = [
                m for m in self.metrics
                if m.operation == operation and m.timestamp >= cutoff_time
            ]

        if not operation_metrics:
            return None

        durations = [m.duration_ms for m in operation_metrics]
        successful_metrics = [m for m in operation_metrics if m.success]
        failed_metrics = [m for m in operation_metrics if not m.success]

        # Calculate statistics
        total_calls = len(operation_metrics)
        successful_calls = len(successful_metrics)
        failed_calls = len(failed_metrics)

        avg_duration = mean(durations)
        min_duration = min(durations)
        max_duration = max(durations)
        median_duration = median(durations)

        # Percentiles
        sorted_durations = sorted(durations)
        p95_index = int(0.95 * len(sorted_durations))
        p99_index = int(0.99 * len(sorted_durations))

        p95_duration = sorted_durations[min(p95_index, len(sorted_durations) - 1)]
        p99_duration = sorted_durations[min(p99_index, len(sorted_durations) - 1)]

        # Rates
        success_rate = successful_calls / total_calls if total_calls > 0 else 0
        error_rate = failed_calls / total_calls if total_calls > 0 else 0

        # Calls per second
        time_span = max(1, current_time - operation_metrics[0].timestamp)
        calls_per_second = total_calls / time_span

        # Recent errors
        recent_errors = [m.error for m in failed_metrics if m.error][-10:]  # Last 10 errors

        return OperationStats(
            operation=operation,
            total_calls=total_calls,
            successful_calls=successful_calls,
            failed_calls=failed_calls,
            avg_duration_ms=avg_duration,
            min_duration_ms=min_duration,
            max_duration_ms=max_duration,
            median_duration_ms=median_duration,
            p95_duration_ms=p95_duration,
            p99_duration_ms=p99_duration,
            success_rate=success_rate,
            error_rate=error_rate,
            calls_per_second=calls_per_second,
            recent_errors=recent_errors
        )

    def get_all_operation_stats(self, time_window_minutes: Optional[int] = None) -> Dict[str, OperationStats]:
        """Get statistics for all operations"""
        current_time = time.time()

        # Use cached stats if available and not expired
        if (current_time - self._last_stats_update < self._stats_cache_duration and
            self._cached_stats and time_window_minutes is None):
            return self._cached_stats.copy()

        # Get unique operations
        with self._lock:
            operations = set(m.operation for m in self.metrics)

        stats = {}
        for operation in operations:
            operation_stats = self.get_operation_stats(operation, time_window_minutes)
            if operation_stats:
                stats[operation] = operation_stats

        # Cache results for default time window
        if time_window_minutes is None:
            self._cached_stats = stats.copy()
            self._last_stats_update = current_time

        return stats

    def get_system_stats(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get system resource statistics"""
        current_time = time.time()
        cutoff_time = current_time - (time_window_minutes * 60)

        with self._lock:
            recent_metrics = [
                m for m in self.system_metrics
                if m.timestamp >= cutoff_time
            ]

        if not recent_metrics:
            return {}

        # Calculate averages
        avg_cpu = mean([m.cpu_percent for m in recent_metrics])
        avg_memory = mean([m.memory_percent for m in recent_metrics])
        avg_memory_used = mean([m.memory_used_mb for m in recent_metrics])
        avg_disk = mean([m.disk_usage_percent for m in recent_metrics])

        # Get latest network stats
        latest_metric = recent_metrics[-1]

        return {
            "cpu_percent_avg": avg_cpu,
            "memory_percent_avg": avg_memory,
            "memory_used_mb_avg": avg_memory_used,
            "memory_available_mb": latest_metric.memory_available_mb,
            "disk_usage_percent_avg": avg_disk,
            "network_bytes_sent": latest_metric.network_bytes_sent,
            "network_bytes_recv": latest_metric.network_bytes_recv,
            "uptime_seconds": current_time - self.start_time,
            "metrics_collected": len(recent_metrics)
        }

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        operation_stats = self.get_all_operation_stats()
        system_stats = self.get_system_stats()

        # Overall service statistics
        with self._lock:
            total_operations = len(self.metrics)
            if self.metrics:
                total_successful = sum(1 for m in self.metrics if m.success)
                overall_success_rate = total_successful / total_operations
                avg_duration = mean([m.duration_ms for m in self.metrics])
            else:
                overall_success_rate = 0
                avg_duration = 0

        # Top slowest operations
        slowest_operations = sorted(
            operation_stats.items(),
            key=lambda x: x[1].avg_duration_ms,
            reverse=True
        )[:5]

        # Most error-prone operations
        error_prone_operations = sorted(
            operation_stats.items(),
            key=lambda x: x[1].error_rate,
            reverse=True
        )[:5]

        return {
            "service_name": self.service_name,
            "uptime_seconds": time.time() - self.start_time,
            "total_operations": total_operations,
            "overall_success_rate": overall_success_rate,
            "avg_operation_duration_ms": avg_duration,
            "unique_operations": len(operation_stats),
            "slowest_operations": [
                {"operation": op, "avg_duration_ms": stats.avg_duration_ms}
                for op, stats in slowest_operations
            ],
            "error_prone_operations": [
                {"operation": op, "error_rate": stats.error_rate}
                for op, stats in error_prone_operations
            ],
            "system_stats": system_stats,
            "operation_stats": {
                op: {
                    "total_calls": stats.total_calls,
                    "success_rate": stats.success_rate,
                    "avg_duration_ms": stats.avg_duration_ms,
                    "p95_duration_ms": stats.p95_duration_ms
                }
                for op, stats in operation_stats.items()
            }
        }

    def get_health_metrics(self) -> Dict[str, Any]:
        """Get health-related metrics for health checks"""
        operation_stats = self.get_all_operation_stats(time_window_minutes=5)  # Last 5 minutes
        system_stats = self.get_system_stats(time_window_minutes=5)

        # Determine health status
        health_status = "healthy"
        health_issues = []

        # Check system resources
        if system_stats.get("cpu_percent_avg", 0) > 80:
            health_issues.append("High CPU usage")
            health_status = "degraded"

        if system_stats.get("memory_percent_avg", 0) > 85:
            health_issues.append("High memory usage")
            health_status = "degraded"

        # Check operation error rates
        for operation, stats in operation_stats.items():
            if stats.error_rate > 0.1:  # 10% error rate
                health_issues.append(f"High error rate for {operation}")
                health_status = "degraded"

            if stats.avg_duration_ms > 10000:  # 10 seconds
                health_issues.append(f"Slow response time for {operation}")
                health_status = "degraded"

        if len(health_issues) > 5:
            health_status = "unhealthy"

        return {
            "status": health_status,
            "issues": health_issues,
            "metrics": {
                "total_operations_5min": sum(stats.total_calls for stats in operation_stats.values()),
                "avg_response_time_ms": mean([stats.avg_duration_ms for stats in operation_stats.values()]) if operation_stats else 0,
                "overall_success_rate": mean([stats.success_rate for stats in operation_stats.values()]) if operation_stats else 1.0,
                "cpu_usage": system_stats.get("cpu_percent_avg", 0),
                "memory_usage": system_stats.get("memory_percent_avg", 0)
            }
        }

    def clear_metrics(self, older_than_hours: Optional[int] = None):
        """Clear performance metrics"""
        if older_than_hours is None:
            with self._lock:
                self.metrics.clear()
                self.system_metrics.clear()
            self._cached_stats.clear()
            self.logger.info("All performance metrics cleared")
        else:
            cutoff_time = time.time() - (older_than_hours * 3600)
            with self._lock:
                # Keep only recent metrics
                self.metrics = deque([
                    m for m in self.metrics if m.timestamp >= cutoff_time
                ], maxlen=self.max_metrics)

                self.system_metrics = deque([
                    m for m in self.system_metrics if m.timestamp >= cutoff_time
                ], maxlen=1000)

            self._cached_stats.clear()
            self.logger.info(f"Cleared metrics older than {older_than_hours} hours")

    def export_metrics(self, format: str = "json") -> Any:
        """Export metrics for external monitoring systems"""
        if format.lower() == "json":
            return {
                "service_name": self.service_name,
                "export_timestamp": time.time(),
                "performance_summary": self.get_performance_summary(),
                "operation_stats": {op: stats.__dict__ for op, stats in self.get_all_operation_stats().items()},
                "system_stats": self.get_system_stats()
            }
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def __str__(self) -> str:
        """String representation"""
        return f"PerformanceTracker(service={self.service_name}, metrics={len(self.metrics)})"