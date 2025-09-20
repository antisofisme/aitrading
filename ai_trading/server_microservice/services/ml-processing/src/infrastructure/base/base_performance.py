"""
Base Performance Interface - Abstract class for service-specific performance tracking
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from functools import wraps
import time

class PerformanceMetric:
    """Single performance metric data"""
    
    def __init__(self, 
                 operation_name: str,
                 duration: float,
                 timestamp: datetime,
                 metadata: Optional[Dict[str, Any]] = None):
        self.operation_name = operation_name
        self.duration = duration
        self.timestamp = timestamp
        self.metadata = metadata or {}

class BasePerformance(ABC):
    """Abstract base class for all service performance trackers"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.metrics = []
        self.active_operations = {}
        
    @abstractmethod
    def start_tracking(self, operation_name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Start tracking an operation"""
        pass
    
    @abstractmethod
    def end_tracking(self, operation_id: str) -> PerformanceMetric:
        """End tracking an operation"""
        pass
    
    @abstractmethod
    def track_operation(self, operation_name: str, metadata: Optional[Dict[str, Any]] = None):
        """Context manager for tracking operations"""
        pass
    
    @abstractmethod
    def performance_tracked(self, operation_name: str = None, metadata: Optional[Dict[str, Any]] = None):
        """Decorator for tracking function performance"""
        pass
    
    @abstractmethod
    def get_metrics(self, 
                   operation_name: Optional[str] = None,
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None) -> List[PerformanceMetric]:
        """Get performance metrics with optional filtering"""
        pass
    
    @abstractmethod
    def get_statistics(self, operation_name: Optional[str] = None) -> Dict[str, Any]:
        """Get performance statistics"""
        pass
    
    @abstractmethod
    def get_slow_operations(self, threshold_ms: float = 1000) -> List[PerformanceMetric]:
        """Get operations slower than threshold"""
        pass
    
    @abstractmethod
    def get_average_response_time(self, operation_name: Optional[str] = None) -> float:
        """Get average response time"""
        pass
    
    @abstractmethod
    def get_percentile(self, percentile: float, operation_name: Optional[str] = None) -> float:
        """Get percentile response time (e.g., 95th percentile)"""
        pass
    
    @abstractmethod
    def clear_metrics(self, older_than: Optional[datetime] = None):
        """Clear metrics, optionally only older than specified time"""
        pass
    
    def record_metric(self, metric: PerformanceMetric):
        """Record a performance metric"""
        self.metrics.append(metric)
    
    def get_total_operations(self) -> int:
        """Get total number of tracked operations"""
        return len(self.metrics)
    
    def get_operations_per_second(self, window_seconds: int = 60) -> float:
        """Get operations per second in the last window"""
        cutoff = datetime.utcnow().timestamp() - window_seconds
        recent_ops = [m for m in self.metrics if m.timestamp.timestamp() > cutoff]
        return len(recent_ops) / window_seconds if window_seconds > 0 else 0
    
    @abstractmethod
    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format"""
        pass
    
    @abstractmethod
    def setup_service_specific_tracking(self):
        """Setup service-specific performance tracking"""
        pass
    
    @abstractmethod
    def alert_on_slow_operation(self, metric: PerformanceMetric):
        """Handle alerts for slow operations"""
        pass