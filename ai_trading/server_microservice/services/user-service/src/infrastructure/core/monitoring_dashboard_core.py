"""
Service Monitoring Dashboard Core - Standardized monitoring integration across microservices
"""
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from .service_identity_core import get_service_identity, get_service_context, get_service_tags

@dataclass
class ServiceMetric:
    """Standardized service metric structure"""
    metric_name: str
    value: float
    unit: str
    timestamp: datetime
    tags: Dict[str, str]
    service_context: Dict[str, Any]

@dataclass
class ServiceHealthStatus:
    """Standardized service health status"""
    service_name: str
    status: str  # healthy, degraded, unhealthy
    uptime_seconds: float
    last_check: datetime
    checks: Dict[str, bool]
    performance_metrics: Dict[str, float]
    error_count: int
    warning_count: int

class ServiceMonitoringDashboardCore:
    """
    Standardized service monitoring dashboard integration.
    Provides consistent monitoring patterns across all microservices.
    """
    
    def __init__(self, service_name: str = None):
        """Initialize monitoring dashboard integration"""
        self.service_identity = get_service_identity(service_name)
        self.service_name = self.service_identity.service_name
        
        # Metrics storage
        self.metrics_history: List[ServiceMetric] = []
        self.current_metrics: Dict[str, float] = {}
        
        # Health tracking
        self.last_health_check = datetime.utcnow()
        self.health_checks: Dict[str, bool] = {}
        self.error_count = 0
        self.warning_count = 0
        
        # Performance tracking
        self.request_count = 0
        self.request_durations: List[float] = []
        self.database_query_count = 0
        self.database_query_durations: List[float] = []
        
        self._setup_default_monitoring()
    
    def _setup_default_monitoring(self):
        """Setup default monitoring patterns for service"""
        # Default health checks for all services
        self.health_checks = {
            "service_identity": True,
            "infrastructure_core": True,
            "memory_usage": True,
            "disk_space": True,
            "network_connectivity": True
        }
        
        # Service-specific health checks
        if self.service_name == "database-service":
            self.health_checks.update({
                "database_connection": True,
                "query_performance": True,
                "connection_pool": True
            })
        elif self.service_name == "ml-processing":
            self.health_checks.update({
                "model_availability": True,
                "gpu_memory": True,
                "inference_performance": True
            })
        elif self.service_name == "data-bridge":
            self.health_checks.update({
                "websocket_connection": True,
                "data_streaming": True,
                "message_queue": True
            })
        elif self.service_name == "ai-provider":
            self.health_checks.update({
                "api_connectivity": True,
                "token_validity": True,
                "rate_limits": True
            })
        elif self.service_name == "trading-engine":
            self.health_checks.update({
                "market_data_feed": True,
                "order_execution": True,
                "risk_management": True
            })
    
    def record_metric(self, 
                     metric_name: str, 
                     value: float, 
                     unit: str = "count",
                     additional_tags: Dict[str, str] = None) -> None:
        """Record a service metric with standardized format"""
        tags = get_service_tags()
        if additional_tags:
            tags.update(additional_tags)
        
        metric = ServiceMetric(
            metric_name=metric_name,
            value=value,
            unit=unit,
            timestamp=datetime.utcnow(),
            tags=tags,
            service_context=get_service_context()
        )
        
        # Store metric
        self.metrics_history.append(metric)
        self.current_metrics[metric_name] = value
        
        # Keep only last 1000 metrics to avoid memory bloat
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
    
    def record_request_metric(self, 
                            endpoint: str,
                            method: str,
                            status_code: int,
                            duration_ms: float,
                            user_id: str = None) -> None:
        """Record HTTP request metrics"""
        self.request_count += 1
        self.request_durations.append(duration_ms)
        
        # Record individual request metric
        tags = {
            "endpoint": endpoint,
            "method": method,
            "status_code": str(status_code),
            "status_class": f"{status_code // 100}xx"
        }
        if user_id:
            tags["user_id"] = user_id
        
        self.record_metric(f"http_request_duration", duration_ms, "milliseconds", tags)
        self.record_metric(f"http_request_count", 1, "count", tags)
        
        # Update aggregated metrics
        self._update_request_aggregates()
    
    def record_database_metric(self,
                             query_type: str,
                             table: str,
                             duration_ms: float,
                             rows_affected: int = None) -> None:
        """Record database operation metrics"""
        self.database_query_count += 1
        self.database_query_durations.append(duration_ms)
        
        tags = {
            "query_type": query_type,
            "table": table
        }
        if rows_affected is not None:
            tags["rows_affected"] = str(rows_affected)
        
        self.record_metric(f"database_query_duration", duration_ms, "milliseconds", tags)
        self.record_metric(f"database_query_count", 1, "count", tags)
        
        # Update aggregated metrics
        self._update_database_aggregates()
    
    def record_business_metric(self,
                             metric_name: str,
                             value: float,
                             business_context: Dict[str, str] = None) -> None:
        """Record business-specific metrics"""
        tags = {"metric_type": "business"}
        if business_context:
            tags.update(business_context)
        
        self.record_metric(f"business_{metric_name}", value, "count", tags)
    
    def record_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None) -> None:
        """Record service error for monitoring"""
        self.error_count += 1
        
        tags = {
            "error_type": error_type,
            "severity": "error"
        }
        
        self.record_metric("service_error_count", 1, "count", tags)
        
        # Update health status
        self._update_health_after_error(error_type)
    
    def record_warning(self, warning_type: str, warning_message: str, context: Dict[str, Any] = None) -> None:
        """Record service warning for monitoring"""
        self.warning_count += 1
        
        tags = {
            "warning_type": warning_type,
            "severity": "warning"
        }
        
        self.record_metric("service_warning_count", 1, "count", tags)
    
    def _update_request_aggregates(self) -> None:
        """Update aggregated request metrics"""
        if self.request_durations:
            avg_duration = sum(self.request_durations) / len(self.request_durations)
            max_duration = max(self.request_durations)
            min_duration = min(self.request_durations)
            
            self.record_metric("http_request_avg_duration", avg_duration, "milliseconds")
            self.record_metric("http_request_max_duration", max_duration, "milliseconds")
            self.record_metric("http_request_min_duration", min_duration, "milliseconds")
            self.record_metric("http_request_total_count", self.request_count, "count")
    
    def _update_database_aggregates(self) -> None:
        """Update aggregated database metrics"""
        if self.database_query_durations:
            avg_duration = sum(self.database_query_durations) / len(self.database_query_durations)
            max_duration = max(self.database_query_durations)
            
            self.record_metric("database_query_avg_duration", avg_duration, "milliseconds")
            self.record_metric("database_query_max_duration", max_duration, "milliseconds")
            self.record_metric("database_query_total_count", self.database_query_count, "count")
    
    def _update_health_after_error(self, error_type: str) -> None:
        """Update health checks after error"""
        # Mark specific health checks as failed based on error type
        if "database" in error_type.lower():
            self.health_checks["database_connection"] = False
        elif "network" in error_type.lower():
            self.health_checks["network_connectivity"] = False
        elif "memory" in error_type.lower():
            self.health_checks["memory_usage"] = False
    
    def get_health_status(self) -> ServiceHealthStatus:
        """Get current service health status"""
        # Calculate uptime
        uptime_seconds = (datetime.utcnow() - self.service_identity.startup_time).total_seconds()
        
        # Determine overall status
        failed_checks = sum(1 for check in self.health_checks.values() if not check)
        if failed_checks == 0:
            status = "healthy"
        elif failed_checks <= 2:
            status = "degraded"
        else:
            status = "unhealthy"
        
        # Get performance metrics
        performance_metrics = {
            "avg_request_duration": sum(self.request_durations) / len(self.request_durations) if self.request_durations else 0,
            "request_rate": self.request_count / max(uptime_seconds, 1),
            "error_rate": self.error_count / max(self.request_count, 1) if self.request_count > 0 else 0,
            "database_query_rate": self.database_query_count / max(uptime_seconds, 1)
        }
        
        return ServiceHealthStatus(
            service_name=self.service_name,
            status=status,
            uptime_seconds=uptime_seconds,
            last_check=datetime.utcnow(),
            checks=self.health_checks.copy(),
            performance_metrics=performance_metrics,
            error_count=self.error_count,
            warning_count=self.warning_count
        )
    
    def get_metrics_summary(self, duration_minutes: int = 60) -> Dict[str, Any]:
        """Get metrics summary for specified duration"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=duration_minutes)
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]
        
        # Group metrics by name
        metrics_by_name = {}
        for metric in recent_metrics:
            if metric.metric_name not in metrics_by_name:
                metrics_by_name[metric.metric_name] = []
            metrics_by_name[metric.metric_name].append(metric.value)
        
        # Calculate aggregates
        summary = {}
        for name, values in metrics_by_name.items():
            summary[name] = {
                "count": len(values),
                "sum": sum(values),
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "last": values[-1] if values else 0
            }
        
        return {
            "service_name": self.service_name,
            "duration_minutes": duration_minutes,
            "metrics_count": len(recent_metrics),
            "metrics": summary,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get complete dashboard data for service monitoring"""
        health_status = self.get_health_status()
        metrics_summary = self.get_metrics_summary()
        service_info = self.service_identity.get_service_info()
        
        return {
            "service_info": asdict(service_info),
            "health_status": asdict(health_status),
            "metrics_summary": metrics_summary,
            "current_metrics": self.current_metrics.copy(),
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def export_metrics_for_prometheus(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        service_tags = get_service_tags()
        
        # Convert tags to Prometheus label format
        tag_string = ",".join([f'{k}="{v}"' for k, v in service_tags.items()])
        
        for metric_name, value in self.current_metrics.items():
            # Convert metric name to Prometheus format
            prom_metric_name = metric_name.replace("-", "_").replace(".", "_")
            lines.append(f'{prom_metric_name}{{{tag_string}}} {value}')
        
        return "\n".join(lines)
    
    def reset_metrics(self) -> None:
        """Reset metrics (useful for testing or maintenance)"""
        self.metrics_history.clear()
        self.current_metrics.clear()
        self.request_durations.clear()
        self.database_query_durations.clear()
        self.request_count = 0
        self.database_query_count = 0
        self.error_count = 0
        self.warning_count = 0


# Service Monitoring Singleton for consistent usage across service
_service_monitoring = None

def get_service_monitoring(service_name: str = None) -> ServiceMonitoringDashboardCore:
    """Get or create service monitoring singleton"""
    global _service_monitoring
    
    if _service_monitoring is None:
        _service_monitoring = ServiceMonitoringDashboardCore(service_name)
    
    return _service_monitoring

def record_metric(metric_name: str, value: float, unit: str = "count", tags: Dict[str, str] = None) -> None:
    """Convenience function to record metrics"""
    monitoring = get_service_monitoring()
    monitoring.record_metric(metric_name, value, unit, tags)

def record_request(endpoint: str, method: str, status_code: int, duration_ms: float, user_id: str = None) -> None:
    """Convenience function to record HTTP requests"""
    monitoring = get_service_monitoring()
    monitoring.record_request_metric(endpoint, method, status_code, duration_ms, user_id)

def record_database_query(query_type: str, table: str, duration_ms: float, rows_affected: int = None) -> None:
    """Convenience function to record database queries"""
    monitoring = get_service_monitoring()
    monitoring.record_database_metric(query_type, table, duration_ms, rows_affected)

def get_health_status() -> ServiceHealthStatus:
    """Convenience function to get health status"""
    monitoring = get_service_monitoring()
    return monitoring.get_health_status()

def get_dashboard_data() -> Dict[str, Any]:
    """Convenience function to get dashboard data"""
    monitoring = get_service_monitoring()
    return monitoring.get_dashboard_data()