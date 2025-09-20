"""
AI Brain Enhanced Core Performance Implementation - Confidence-correlated performance tracking
Enhanced with AI Brain confidence correlation and systematic performance validation
"""
import time
import uuid
import json
import statistics
import aiofiles
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from contextlib import contextmanager, asynccontextmanager
from functools import wraps
from pathlib import Path
from ..base.base_performance import BasePerformance, PerformanceMetric

# AI Brain Integration
try:
    import sys
    sys.path.append('/mnt/f/WINDSURF/concept_ai/projects/ai_trading/server_microservice/services')
    from shared.ai_brain_confidence_framework import AiBrainConfidenceFramework
    AI_BRAIN_AVAILABLE = True
except ImportError:
    AI_BRAIN_AVAILABLE = False

class CorePerformance(BasePerformance):
    """AI Brain Enhanced Core performance tracker with confidence correlation analysis"""
    
    def __init__(self, 
                 service_name: str,
                 max_metrics: int = 10000,
                 slow_threshold_ms: float = 1000):
        """
        Initialize AI Brain Enhanced CorePerformance with confidence correlation tracking.
        
        Args:
            service_name: Name of the service to track performance for
            max_metrics: Maximum number of metrics to store in memory (default: 10000)
            slow_threshold_ms: Threshold in milliseconds to consider an operation slow (default: 1000)
        """
        super().__init__(service_name)
        self.max_metrics = max_metrics
        self.slow_threshold_ms = slow_threshold_ms
        
        # AI Brain Enhanced Performance Tracking
        self.confidence_performance_correlation = {}
        self.confidence_metrics = []
        self.performance_degradation_alerts = []
        
        # AI Brain Confidence Framework Integration (if available)
        self.ai_brain_confidence = None
        if AI_BRAIN_AVAILABLE:
            try:
                self.ai_brain_confidence = AiBrainConfidenceFramework(f"performance-{service_name}")
                print(f"✅ AI Brain Confidence Framework initialized for performance tracker: {service_name}")
            except Exception as e:
                print(f"⚠️ AI Brain Confidence Framework initialization failed: {e}")
        
        self.setup_service_specific_tracking()
    
    def start_tracking(self, operation_name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Start tracking a new operation.
        
        Args:
            operation_name: Name/identifier for the operation being tracked
            metadata: Optional metadata dictionary to associate with this operation
            
        Returns:
            Unique operation ID that can be used to end tracking
        """
        operation_id = str(uuid.uuid4())
        
        tracking_data = {
            "operation_name": operation_name,
            "start_time": time.time(),
            "metadata": metadata or {}
        }
        
        self.active_operations[operation_id] = tracking_data
        return operation_id
    
    def end_tracking(self, operation_id: str) -> PerformanceMetric:
        """End tracking an operation"""
        if operation_id not in self.active_operations:
            raise ValueError(f"Operation {operation_id} not found in active operations")
        
        tracking_data = self.active_operations.pop(operation_id)
        end_time = time.time()
        duration = (end_time - tracking_data["start_time"]) * 1000  # Convert to milliseconds
        
        # Create performance metric
        metric = PerformanceMetric(
            operation_name=tracking_data["operation_name"],
            duration=duration,
            timestamp=datetime.utcnow(),
            metadata=tracking_data["metadata"]
        )
        
        # Record the metric
        self.record_metric(metric)
        
        # Check for slow operations
        if duration > self.slow_threshold_ms:
            self.alert_on_slow_operation(metric)
        
        # Cleanup old metrics if we exceed max
        self._cleanup_old_metrics()
        
        return metric
    
    @asynccontextmanager
    async def track_operation(self, operation_name: str, metadata: Optional[Dict[str, Any]] = None):
        """Async context manager for tracking operations"""
        operation_id = self.start_tracking(operation_name, metadata)
        try:
            yield operation_id
        finally:
            self.end_tracking(operation_id)
    
    @contextmanager
    def track_operation_sync(self, operation_name: str, metadata: Optional[Dict[str, Any]] = None):
        """Sync context manager for tracking operations (for backwards compatibility)"""
        operation_id = self.start_tracking(operation_name, metadata)
        try:
            yield operation_id
        finally:
            self.end_tracking(operation_id)
    
    def performance_tracked(self, operation_name: str = None, metadata: Optional[Dict[str, Any]] = None):
        """Decorator for tracking function performance"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                op_name = operation_name or f"{func.__module__}.{func.__name__}"
                op_metadata = {
                    "function": func.__name__,
                    "module": func.__module__,
                    **(metadata or {})
                }
                
                with self.track_operation(op_name, op_metadata):
                    return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def get_metrics(self, 
                   operation_name: Optional[str] = None,
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None) -> List[PerformanceMetric]:
        """Get performance metrics with optional filtering"""
        filtered_metrics = self.metrics.copy()
        
        # Filter by operation name
        if operation_name:
            filtered_metrics = [m for m in filtered_metrics if m.operation_name == operation_name]
        
        # Filter by time range
        if start_time:
            filtered_metrics = [m for m in filtered_metrics if m.timestamp >= start_time]
        
        if end_time:
            filtered_metrics = [m for m in filtered_metrics if m.timestamp <= end_time]
        
        return filtered_metrics
    
    def get_statistics(self, operation_name: Optional[str] = None) -> Dict[str, Any]:
        """Get performance statistics"""
        metrics = self.get_metrics(operation_name)
        
        if not metrics:
            return {
                "operation_name": operation_name,
                "total_operations": 0,
                "statistics": None
            }
        
        durations = [m.duration for m in metrics]
        
        stats = {
            "operation_name": operation_name,
            "total_operations": len(metrics),
            "duration_ms": {
                "min": min(durations),
                "max": max(durations),
                "mean": statistics.mean(durations),
                "median": statistics.median(durations),
                "std_dev": statistics.stdev(durations) if len(durations) > 1 else 0
            },
            "time_range": {
                "start": min(m.timestamp for m in metrics).isoformat(),
                "end": max(m.timestamp for m in metrics).isoformat()
            },
            "slow_operations_count": len([m for m in metrics if m.duration > self.slow_threshold_ms]),
            "service": self.service_name
        }
        
        # Add percentiles if we have enough data
        if len(durations) >= 5:
            stats["duration_ms"]["percentiles"] = {
                "50th": statistics.median(durations),
                "90th": self._calculate_percentile(durations, 90),
                "95th": self._calculate_percentile(durations, 95),
                "99th": self._calculate_percentile(durations, 99)
            }
        
        return stats
    
    def get_slow_operations(self, threshold_ms: float = 1000) -> List[PerformanceMetric]:
        """Get operations slower than threshold"""
        return [m for m in self.metrics if m.duration > threshold_ms]
    
    def get_average_response_time(self, operation_name: Optional[str] = None) -> float:
        """Get average response time"""
        metrics = self.get_metrics(operation_name)
        
        if not metrics:
            return 0.0
        
        return statistics.mean(m.duration for m in metrics)
    
    def get_percentile(self, percentile: float, operation_name: Optional[str] = None) -> float:
        """Get percentile response time (e.g., 95th percentile)"""
        metrics = self.get_metrics(operation_name)
        
        if not metrics:
            return 0.0
        
        durations = [m.duration for m in metrics]
        return self._calculate_percentile(durations, percentile)
    
    def clear_metrics(self, older_than: Optional[datetime] = None):
        """Clear metrics, optionally only older than specified time"""
        if older_than:
            self.metrics = [m for m in self.metrics if m.timestamp > older_than]
        else:
            self.metrics.clear()
    
    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format"""
        if format == "json":
            metrics_data = []
            for metric in self.metrics:
                metrics_data.append({
                    "operation_name": metric.operation_name,
                    "duration_ms": metric.duration,
                    "timestamp": metric.timestamp.isoformat(),
                    "metadata": metric.metadata
                })
            
            export_data = {
                "service": self.service_name,
                "export_time": datetime.utcnow().isoformat(),
                "total_metrics": len(metrics_data),
                "metrics": metrics_data
            }
            
            return json.dumps(export_data, indent=2)
        
        elif format == "csv":
            import io
            output = io.StringIO()
            
            # Write CSV header
            output.write("operation_name,duration_ms,timestamp,service\n")
            
            # Write metrics
            for metric in self.metrics:
                output.write(f"{metric.operation_name},{metric.duration},{metric.timestamp.isoformat()},{self.service_name}\n")
            
            return output.getvalue()
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    async def export_metrics_to_file(self, file_path: Path, format: str = "json") -> None:
        """Export metrics to file asynchronously"""
        metrics_data = self.export_metrics(format)
        
        async with aiofiles.open(file_path, 'w') as f:
            await f.write(metrics_data)
    
    async def export_performance_report(self, report_dir: Path) -> Dict[str, str]:
        """Export comprehensive performance report to multiple files"""
        report_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate different report formats concurrently
        tasks = [
            self.export_metrics_to_file(report_dir / f"{self.service_name}_metrics.json", "json"),
            self.export_metrics_to_file(report_dir / f"{self.service_name}_metrics.csv", "csv"),
        ]
        
        # Add slow operations report
        slow_operations = self.get_slow_operations(threshold_ms=1000)
        if slow_operations:
            slow_ops_content = json.dumps({
                "service": self.service_name,
                "report_time": datetime.utcnow().isoformat(),
                "slow_operations": [
                    {
                        "operation": op.operation_name,
                        "duration_ms": op.duration,
                        "timestamp": op.timestamp.isoformat(),
                        "metadata": op.metadata
                    }
                    for op in slow_operations
                ]
            }, indent=2)
            
            async def write_slow_ops():
                async with aiofiles.open(report_dir / f"{self.service_name}_slow_ops.json", 'w') as f:
                    await f.write(slow_ops_content)
            
            tasks.append(write_slow_ops())
        
        # Execute all exports concurrently
        await asyncio.gather(*tasks)
        
        return {
            "metrics_json": str(report_dir / f"{self.service_name}_metrics.json"),
            "metrics_csv": str(report_dir / f"{self.service_name}_metrics.csv"),
            "slow_operations": str(report_dir / f"{self.service_name}_slow_ops.json") if slow_operations else None
        }
    
    def setup_service_specific_tracking(self) -> None:
        """Setup service-specific performance tracking"""
        # Service-specific performance configurations
        
        if self.service_name == "api-gateway":
            self._setup_api_gateway_tracking()
        elif self.service_name == "database-service":
            self._setup_database_tracking()
        elif self.service_name in ["mt5-bridge", "trading-engine"]:
            self._setup_trading_tracking()
    
    def _setup_api_gateway_tracking(self) -> None:
        """Setup API Gateway specific tracking"""
        # Lower threshold for API responses
        self.slow_threshold_ms = 500
    
    def _setup_database_tracking(self) -> None:
        """Setup Database Service specific tracking"""
        # Higher threshold for database operations
        self.slow_threshold_ms = 2000
    
    def _setup_trading_tracking(self) -> None:
        """Setup Trading specific tracking"""
        # Very low threshold for trading operations (real-time critical)
        self.slow_threshold_ms = 100
    
    def alert_on_slow_operation(self, metric: PerformanceMetric) -> None:
        """Handle alerts for slow operations"""
        alert_data = {
            "service": self.service_name,
            "operation": metric.operation_name,
            "duration_ms": metric.duration,
            "threshold_ms": self.slow_threshold_ms,
            "timestamp": metric.timestamp.isoformat(),
            "metadata": metric.metadata
        }
        
        # In production, this would send alerts to monitoring systems
        # Use proper logging instead of print for production code
        import logging
        logger = logging.getLogger(f"{self.service_name}-performance-alerts")
        logger.warning(f"SLOW OPERATION ALERT", extra={"context": alert_data})
    
    def _calculate_percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile from data"""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        k = (len(sorted_data) - 1) * (percentile / 100)
        f = int(k)
        c = k - f
        
        if f == len(sorted_data) - 1:
            return sorted_data[f]
        
        return sorted_data[f] * (1 - c) + sorted_data[f + 1] * c
    
    def _cleanup_old_metrics(self):
        """Clean up old metrics if we exceed maximum"""
        if len(self.metrics) > self.max_metrics:
            # Sort by timestamp and keep the most recent metrics
            self.metrics.sort(key=lambda m: m.timestamp, reverse=True)
            self.metrics = self.metrics[:self.max_metrics]
    
    def get_real_time_stats(self, window_minutes: int = 5) -> Dict[str, Any]:
        """Get real-time performance statistics for recent window"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=window_minutes)
        recent_metrics = self.get_metrics(start_time=cutoff_time)
        
        if not recent_metrics:
            return {
                "window_minutes": window_minutes,
                "operations_count": 0,
                "operations_per_minute": 0,
                "average_duration_ms": 0,
                "slow_operations_count": 0
            }
        
        durations = [m.duration for m in recent_metrics]
        
        return {
            "window_minutes": window_minutes,
            "operations_count": len(recent_metrics),
            "operations_per_minute": len(recent_metrics) / window_minutes,
            "average_duration_ms": statistics.mean(durations),
            "median_duration_ms": statistics.median(durations),
            "max_duration_ms": max(durations),
            "slow_operations_count": len([m for m in recent_metrics if m.duration > self.slow_threshold_ms]),
            "service": self.service_name,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_operation_breakdown(self) -> Dict[str, Dict[str, Any]]:
        """Get performance breakdown by operation type"""
        breakdown = {}
        
        # Group metrics by operation name
        operation_groups = {}
        for metric in self.metrics:
            if metric.operation_name not in operation_groups:
                operation_groups[metric.operation_name] = []
            operation_groups[metric.operation_name].append(metric)
        
        # Calculate statistics for each operation
        for operation_name, metrics in operation_groups.items():
            durations = [m.duration for m in metrics]
            
            breakdown[operation_name] = {
                "count": len(metrics),
                "average_duration_ms": statistics.mean(durations),
                "median_duration_ms": statistics.median(durations),
                "min_duration_ms": min(durations),
                "max_duration_ms": max(durations),
                "slow_operations_count": len([m for m in metrics if m.duration > self.slow_threshold_ms]),
                "percentage_of_total": round((len(metrics) / len(self.metrics)) * 100, 2) if self.metrics else 0
            }
        
        return breakdown
    
    # AI Brain Enhanced Performance Methods
    
    def record_confidence_metric(self, operation_name: str, confidence_score: float, performance_metric: PerformanceMetric):
        """Record confidence score with associated performance metric for AI Brain analysis"""
        confidence_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation_name": operation_name,
            "confidence_score": confidence_score,
            "performance_duration_ms": performance_metric.duration,
            "performance_metadata": performance_metric.metadata
        }
        
        self.confidence_metrics.append(confidence_entry)
        
        # Track confidence-performance correlation
        if operation_name not in self.confidence_performance_correlation:
            self.confidence_performance_correlation[operation_name] = {
                "confidence_scores": [],
                "performance_durations": [],
                "correlation_coefficient": 0.0,
                "sample_count": 0
            }
        
        correlation_data = self.confidence_performance_correlation[operation_name]
        correlation_data["confidence_scores"].append(confidence_score)
        correlation_data["performance_durations"].append(performance_metric.duration)
        correlation_data["sample_count"] += 1
        
        # Calculate correlation if we have enough samples (minimum 5)
        if correlation_data["sample_count"] >= 5:
            try:
                import numpy as np
                correlation_coef = np.corrcoef(
                    correlation_data["confidence_scores"],
                    correlation_data["performance_durations"]
                )[0, 1]
                
                # Handle NaN values (when all values are identical)
                correlation_data["correlation_coefficient"] = float(correlation_coef) if not np.isnan(correlation_coef) else 0.0
                
                # Detect performance degradation with low confidence
                self._detect_performance_degradation(operation_name, confidence_score, performance_metric.duration)
                
            except ImportError:
                # Fallback simple correlation calculation without numpy
                correlation_data["correlation_coefficient"] = self._calculate_simple_correlation(
                    correlation_data["confidence_scores"],
                    correlation_data["performance_durations"]
                )
    
    def _detect_performance_degradation(self, operation_name: str, confidence_score: float, duration_ms: float):
        """AI Brain: Detect performance degradation patterns with confidence correlation"""
        degradation_threshold = self.slow_threshold_ms * 0.8  # 80% of slow threshold
        confidence_threshold = 0.70  # Low confidence threshold
        
        # Alert if low confidence correlates with poor performance
        if confidence_score < confidence_threshold and duration_ms > degradation_threshold:
            alert = {
                "timestamp": datetime.now().isoformat(),
                "operation_name": operation_name,
                "confidence_score": confidence_score,
                "duration_ms": duration_ms,
                "degradation_type": "confidence_performance_correlation",
                "severity": "high" if duration_ms > self.slow_threshold_ms else "medium",
                "ai_brain_analysis": {
                    "pattern": "Low confidence correlating with poor performance",
                    "recommendation": "Review operation logic and data quality",
                    "urgency": "immediate" if duration_ms > self.slow_threshold_ms * 1.5 else "high"
                }
            }
            
            self.performance_degradation_alerts.append(alert)
            
            # Log alert with AI Brain context
            import logging
            logger = logging.getLogger(f"{self.service_name}-ai-brain-performance")
            logger.warning(f"🧠 AI Brain Performance Degradation: {operation_name} - Confidence: {confidence_score:.3f}, Duration: {duration_ms:.1f}ms", 
                         extra={"context": alert})
    
    def _calculate_simple_correlation(self, x_values: List[float], y_values: List[float]) -> float:
        """Simple correlation calculation without external dependencies"""
        if len(x_values) != len(y_values) or len(x_values) < 2:
            return 0.0
        
        n = len(x_values)
        mean_x = sum(x_values) / n
        mean_y = sum(y_values) / n
        
        numerator = sum((x_values[i] - mean_x) * (y_values[i] - mean_y) for i in range(n))
        
        sum_sq_x = sum((x - mean_x) ** 2 for x in x_values)
        sum_sq_y = sum((y - mean_y) ** 2 for y in y_values)
        
        denominator = (sum_sq_x * sum_sq_y) ** 0.5
        
        return numerator / denominator if denominator != 0 else 0.0
    
    def get_confidence_performance_analysis(self) -> Dict[str, Any]:
        """Get AI Brain confidence-performance correlation analysis"""
        analysis = {
            "service": self.service_name,
            "analysis_timestamp": datetime.now().isoformat(),
            "total_confidence_metrics": len(self.confidence_metrics),
            "operations_with_correlation": len(self.confidence_performance_correlation),
            "performance_degradation_alerts": len(self.performance_degradation_alerts),
            "correlations": {}
        }
        
        # Analyze each operation's confidence-performance relationship
        for operation_name, correlation_data in self.confidence_performance_correlation.items():
            if correlation_data["sample_count"] >= 5:
                correlation_coef = correlation_data["correlation_coefficient"]
                
                # Interpret correlation strength
                if abs(correlation_coef) >= 0.7:
                    strength = "strong"
                elif abs(correlation_coef) >= 0.4:
                    strength = "moderate"
                else:
                    strength = "weak"
                
                # Determine correlation direction and meaning
                if correlation_coef > 0:
                    direction = "positive"
                    meaning = "Higher confidence leads to longer duration (concerning)"
                else:
                    direction = "negative" 
                    meaning = "Higher confidence leads to shorter duration (expected)"
                
                analysis["correlations"][operation_name] = {
                    "correlation_coefficient": correlation_coef,
                    "strength": strength,
                    "direction": direction,
                    "interpretation": meaning,
                    "sample_count": correlation_data["sample_count"],
                    "average_confidence": sum(correlation_data["confidence_scores"]) / len(correlation_data["confidence_scores"]),
                    "average_duration_ms": sum(correlation_data["performance_durations"]) / len(correlation_data["performance_durations"]),
                    "ai_brain_recommendation": self._generate_correlation_recommendation(correlation_coef, operation_name)
                }
        
        # Recent performance degradation trends
        recent_alerts = [alert for alert in self.performance_degradation_alerts if 
                        datetime.fromisoformat(alert["timestamp"]) > datetime.now() - timedelta(hours=1)]
        
        analysis["recent_degradation_alerts"] = len(recent_alerts)
        analysis["ai_brain_health_status"] = self._assess_ai_brain_health_status()
        
        return analysis
    
    def _generate_correlation_recommendation(self, correlation_coef: float, operation_name: str) -> Dict[str, Any]:
        """Generate AI Brain recommendations based on confidence-performance correlation"""
        if correlation_coef > 0.5:
            return {
                "priority": "high",
                "action": "investigate_performance_bottleneck",
                "reason": "Positive correlation suggests high confidence operations are unexpectedly slow",
                "specific_recommendations": [
                    f"Review {operation_name} implementation for performance bottlenecks",
                    "Check if high confidence triggers more complex processing paths",
                    "Consider optimizing high-confidence operation workflows"
                ]
            }
        elif correlation_coef < -0.5:
            return {
                "priority": "low", 
                "action": "maintain_current_pattern",
                "reason": "Negative correlation is expected - high confidence correlates with good performance",
                "specific_recommendations": [
                    f"Maintain current {operation_name} implementation",
                    "Consider using this pattern as a template for other operations"
                ]
            }
        else:
            return {
                "priority": "medium",
                "action": "monitor_pattern_development", 
                "reason": "Weak correlation - pattern may emerge with more data",
                "specific_recommendations": [
                    f"Continue monitoring {operation_name} confidence-performance relationship",
                    "Ensure sufficient sample size for reliable correlation analysis"
                ]
            }
    
    def _assess_ai_brain_health_status(self) -> Dict[str, Any]:
        """Assess overall AI Brain performance health status"""
        recent_hour_alerts = len([alert for alert in self.performance_degradation_alerts if 
                                datetime.fromisoformat(alert["timestamp"]) > datetime.now() - timedelta(hours=1)])
        
        total_operations_tracked = len(self.confidence_metrics)
        
        if recent_hour_alerts == 0 and total_operations_tracked > 0:
            status = "healthy"
            message = "AI Brain confidence-performance correlation is optimal"
        elif recent_hour_alerts <= 2:
            status = "warning"
            message = "Minor performance degradation detected - monitoring required"
        else:
            status = "critical"
            message = "Significant performance degradation - immediate attention required"
        
        # Calculate overall confidence trend
        if total_operations_tracked >= 10:
            recent_confidences = [metric["confidence_score"] for metric in self.confidence_metrics[-10:]]
            avg_recent_confidence = sum(recent_confidences) / len(recent_confidences)
            
            if avg_recent_confidence >= 0.85:
                confidence_trend = "high"
            elif avg_recent_confidence >= 0.70:
                confidence_trend = "medium"
            else:
                confidence_trend = "low"
        else:
            confidence_trend = "insufficient_data"
        
        return {
            "overall_status": status,
            "message": message,
            "recent_alerts_count": recent_hour_alerts,
            "confidence_trend": confidence_trend,
            "tracked_operations": total_operations_tracked,
            "recommendations": self._generate_health_recommendations(status, confidence_trend)
        }
    
    def _generate_health_recommendations(self, status: str, confidence_trend: str) -> List[str]:
        """Generate health-based recommendations"""
        recommendations = []
        
        if status == "critical":
            recommendations.extend([
                "🚨 Immediate review of operations with low confidence scores required",
                "🔍 Investigate root causes of performance degradation",
                "⚡ Consider implementing circuit breakers for failing operations"
            ])
        elif status == "warning":
            recommendations.extend([
                "⚠️ Monitor operations closely for trend development", 
                "🧠 Review AI Brain confidence thresholds for accuracy"
            ])
        
        if confidence_trend == "low":
            recommendations.extend([
                "📊 Review data quality feeding into confidence calculations",
                "🎯 Consider retraining models or updating confidence algorithms"
            ])
        
        if not recommendations:
            recommendations.append("✅ Continue current monitoring and optimization practices")
        
        return recommendations
    
    def export_ai_brain_performance_report(self) -> Dict[str, Any]:
        """Export comprehensive AI Brain performance analysis report"""
        confidence_analysis = self.get_confidence_performance_analysis()
        performance_stats = self.get_statistics()
        operation_breakdown = self.get_operation_breakdown()
        real_time_stats = self.get_real_time_stats()
        
        report = {
            "report_metadata": {
                "service": self.service_name,
                "generated_at": datetime.now().isoformat(),
                "report_type": "ai_brain_performance_analysis",
                "data_window": "all_time"
            },
            "ai_brain_analysis": confidence_analysis,
            "performance_statistics": performance_stats,
            "operation_breakdown": operation_breakdown,
            "real_time_metrics": real_time_stats,
            "degradation_alerts": self.performance_degradation_alerts,
            "confidence_metrics": self.confidence_metrics[-100:] if len(self.confidence_metrics) > 100 else self.confidence_metrics  # Last 100 for report size management
        }
        
        return report


# CENTRALIZED PERFORMANCE MANAGER - Simple singleton for all microservices
import threading

class SharedInfraPerformanceManager:
    """Simple centralized performance management for microservices"""
    
    _trackers = {}
    _lock = threading.RLock()
    
    @classmethod
    def get_performance_tracker(cls, service_name: str) -> CorePerformance:
        """Get or create performance tracker for service"""
        with cls._lock:
            if service_name not in cls._trackers:
                cls._trackers[service_name] = CorePerformance(service_name)
            return cls._trackers[service_name]
    
    @classmethod
    def track_operation(cls, service_name: str, operation_name: str, **kwargs):
        """Track operation for service"""
        tracker = cls.get_performance_tracker(service_name)
        return tracker.track_operation(operation_name, **kwargs)
    
    @classmethod
    def get_all_trackers(cls):
        """Get all managed performance trackers"""
        return cls._trackers.copy()


# Simple convenience functions
def get_performance_tracker(service_name: str) -> CorePerformance:
    """Get performance tracker for service"""
    return SharedInfraPerformanceManager.get_performance_tracker(service_name)

def track_operation(service_name: str, operation_name: str, **kwargs):
    """Track operation for service"""
    return SharedInfraPerformanceManager.track_operation(service_name, operation_name, **kwargs)

# Decorator for automatic performance tracking
def performance_tracked(service_name: str, operation_name: str = ""):
    """Decorator for automatic performance tracking"""
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                tracker = get_performance_tracker(service_name)
                op_name = operation_name or f"{func.__name__}"
                
                operation_id = tracker.start_tracking(op_name)
                try:
                    result = await func(*args, **kwargs)
                    tracker.end_tracking(operation_id)
                    return result
                except Exception as e:
                    tracker.end_tracking(operation_id)
                    raise
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                tracker = get_performance_tracker(service_name)
                op_name = operation_name or f"{func.__name__}"
                
                operation_id = tracker.start_tracking(op_name)
                try:
                    result = func(*args, **kwargs)
                    tracker.end_tracking(operation_id)
                    return result
                except Exception as e:
                    tracker.end_tracking(operation_id)
                    raise
            return sync_wrapper
    return decorator

# Context manager for performance tracking
@contextmanager
def performance_context(service_name: str, operation_name: str, **metadata):
    """Context manager for performance tracking"""
    tracker = get_performance_tracker(service_name)
    operation_id = tracker.start_tracking(operation_name, metadata)
    try:
        yield tracker
    finally:
        tracker.end_tracking(operation_id)