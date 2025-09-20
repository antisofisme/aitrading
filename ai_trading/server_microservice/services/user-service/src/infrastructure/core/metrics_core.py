"""
AI Brain Enhanced Metrics Core - Completeness Auditor Implementation
Production-ready metrics collection with AI Brain completeness validation and observability auditing
Enhanced with systematic monitoring completeness analysis and confidence-based validation
"""

import asyncio
import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable, Union
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, deque
import threading
from ..base.base_logger import BaseLogger
from ..base.base_performance import BasePerformance

# AI Brain Integration
try:
    import sys
    sys.path.append('/mnt/f/WINDSURF/concept_ai/projects/ai_trading/server_microservice/services')
    from shared.ai_brain_confidence_framework import AiBrainConfidenceFramework, ConfidenceThreshold
    from shared.ai_brain_trading_error_dna import AiBrainTradingErrorDNA
    AI_BRAIN_AVAILABLE = True
except ImportError:
    AI_BRAIN_AVAILABLE = False

class MetricType(Enum):
    """Metric type enumeration"""
    COUNTER = "counter"           # Incrementing values (requests, errors)
    GAUGE = "gauge"              # Current values (memory, connections)
    HISTOGRAM = "histogram"       # Distribution of values (response times)
    SUMMARY = "summary"          # Statistical summaries (percentiles)
    TIMER = "timer"              # Duration measurements

class MetricScope(Enum):
    """Metric scope enumeration"""
    SERVICE = "service"          # Service-level metrics
    ENDPOINT = "endpoint"        # API endpoint metrics
    BUSINESS = "business"        # Business logic metrics
    INFRASTRUCTURE = "infrastructure"  # Infrastructure metrics
    EXTERNAL = "external"        # External service metrics

class CompletenessCategory(Enum):
    """Monitoring completeness category enumeration"""
    CORE_METRICS = "core_metrics"              # Essential business/service metrics
    PERFORMANCE_METRICS = "performance_metrics" # Performance and latency metrics
    ERROR_METRICS = "error_metrics"            # Error tracking and handling metrics
    BUSINESS_METRICS = "business_metrics"      # Domain-specific business metrics
    OBSERVABILITY_STACK = "observability_stack" # Logs, metrics, traces coverage
    ALERTING_COVERAGE = "alerting_coverage"    # Alerting and notification coverage

class CompletenessGap(Enum):
    """Completeness gap types"""
    MISSING_METRIC = "missing_metric"
    STALE_DATA = "stale_data"
    INSUFFICIENT_COVERAGE = "insufficient_coverage"
    POOR_DATA_QUALITY = "poor_data_quality"
    MISSING_LABELS = "missing_labels"
    INCOMPLETE_OBSERVABILITY = "incomplete_observability"

@dataclass
class Metric:
    """Individual metric definition"""
    name: str
    metric_type: MetricType
    scope: MetricScope
    value: Union[int, float]
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    description: str = ""
    unit: str = ""

@dataclass
class MetricSnapshot:
    """AI Brain Enhanced snapshot of metric values with completeness analysis"""
    timestamp: datetime
    service_name: str
    environment: str
    metrics: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    # AI Brain Completeness Analysis
    completeness_score: float = 1.0
    completeness_gaps: List[Dict[str, Any]] = field(default_factory=list)
    observability_coverage: float = 1.0
    production_readiness_score: float = 1.0

@dataclass
class CompletenessRequirement:
    """Monitoring completeness requirement definition"""
    category: CompletenessCategory
    required_metrics: List[str]
    min_data_points: int = 10
    max_staleness_minutes: int = 5
    required_labels: List[str] = field(default_factory=list)
    business_criticality: str = "medium"  # low, medium, high, critical

class MetricsCore:
    """
    AI Brain Enhanced Core metrics collection implementation for microservices with Completeness Auditor.
    
    Features:
    - Real-time metrics collection and aggregation with completeness validation
    - Multiple metric types (counter, gauge, histogram, timer) with quality assessment
    - Service-specific metric scopes with observability coverage analysis
    - Historical data retention with completeness monitoring
    - Business and technical metric separation with gap detection
    - Performance optimized with minimal overhead and confidence scoring
    - Export capabilities for monitoring systems with production readiness assessment
    - AI Brain completeness auditing and observability validation
    """
    
    def __init__(self, 
                 service_name: str,
                 environment: str = "development",
                 retention_hours: int = 24,
                 flush_interval: float = 60.0):
        """
        Initialize AI Brain Enhanced metrics collection with completeness auditing.
        
        Args:
            service_name: Name of the service
            environment: Environment (development, staging, production)
            retention_hours: Hours to retain metric data
            flush_interval: Interval to flush metrics to storage
        """
        self.service_name = service_name
        self.environment = environment
        self.retention_hours = retention_hours
        self.flush_interval = flush_interval
        
        # AI Brain Completeness Auditor Integration
        self.ai_brain_confidence = None
        self.ai_brain_error_dna = None
        if AI_BRAIN_AVAILABLE:
            try:
                self.ai_brain_confidence = AiBrainConfidenceFramework(f"metrics-{service_name}")
                self.ai_brain_error_dna = AiBrainTradingErrorDNA(f"metrics-{service_name}")
                self.logger.info("✅ AI Brain Completeness Auditor initialized for metrics")
            except Exception as e:
                self.logger.warning(f"⚠️ AI Brain Completeness Auditor initialization failed: {e}")
        
        # Metric storage
        self._metrics: Dict[str, List[Metric]] = defaultdict(list)
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = defaultdict(float)
        self._histograms: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._timers: Dict[str, List[float]] = defaultdict(list)
        
        # Completeness tracking
        self.completeness_requirements: Dict[str, CompletenessRequirement] = {}
        self.completeness_gaps: List[Dict[str, Any]] = []
        self.last_completeness_audit: Optional[datetime] = None
        self.production_readiness_score: float = 0.0
        
        # Aggregated metrics cache
        self._aggregated_cache: Dict[str, Dict[str, Any]] = {}
        self._last_aggregation: Optional[datetime] = None
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Background tasks
        self.is_running = False
        self._flush_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._completeness_audit_task: Optional[asyncio.Task] = None
        
        # Initialize logging and performance tracking
        self.logger = BaseLogger(service_name, "metrics_core")
        self.performance_tracker = BasePerformance(service_name)
        
        # Service-specific configurations and completeness requirements
        self._setup_service_defaults()
        self._setup_completeness_requirements()
        
        self.logger.info("AI Brain Enhanced Metrics Core initialized", extra={
            "service": service_name,
            "environment": environment,
            "retention_hours": retention_hours,
            "flush_interval": flush_interval,
            "ai_brain_completeness_enabled": AI_BRAIN_AVAILABLE
        })
    
    def _setup_service_defaults(self):
        """Setup service-specific metric configurations"""
        service_configs = {
            "api-gateway": {
                "retention_hours": 48,
                "flush_interval": 30.0,
                "key_metrics": ["request_count", "response_time", "error_rate"]
            },
            "ai-provider": {
                "retention_hours": 72,
                "flush_interval": 60.0,
                "key_metrics": ["completion_requests", "provider_success_rate", "cost_estimate"]
            },
            "trading-engine": {
                "retention_hours": 168,  # 7 days
                "flush_interval": 10.0,
                "key_metrics": ["orders_executed", "pnl", "risk_metrics"]
            },
            "database-service": {
                "retention_hours": 168,
                "flush_interval": 120.0,
                "key_metrics": ["query_count", "connection_pool", "cache_hit_rate"]
            },
            "data-bridge": {
                "retention_hours": 24,
                "flush_interval": 5.0,
                "key_metrics": ["tick_count", "latency", "throughput"]
            }
        }
        
        if self.service_name in service_configs:
            config = service_configs[self.service_name]
            self.retention_hours = config["retention_hours"]
            self.flush_interval = config["flush_interval"]
            self.key_metrics = config["key_metrics"]
        else:
            self.key_metrics = ["request_count", "response_time", "error_count"]
    
    def _setup_completeness_requirements(self):
        """Setup AI Brain completeness requirements for service monitoring"""
        # Core service requirements (all services need these)
        core_requirements = [
            CompletenessRequirement(
                category=CompletenessCategory.CORE_METRICS,
                required_metrics=["request_count", "response_time", "error_count", "uptime"],
                min_data_points=50,
                max_staleness_minutes=2,
                required_labels=["service", "environment"],
                business_criticality="critical"
            ),
            CompletenessRequirement(
                category=CompletenessCategory.PERFORMANCE_METRICS,
                required_metrics=["cpu_usage", "memory_usage", "latency_p95"],
                min_data_points=30,
                max_staleness_minutes=5,
                required_labels=["service", "instance"],
                business_criticality="high"
            ),
            CompletenessRequirement(
                category=CompletenessCategory.ERROR_METRICS,
                required_metrics=["error_rate", "exception_count"],
                min_data_points=10,
                max_staleness_minutes=5,
                required_labels=["service", "error_type"],
                business_criticality="high"
            )
        ]
        
        # Service-specific requirements
        service_specific = {
            "api-gateway": [
                CompletenessRequirement(
                    category=CompletenessCategory.BUSINESS_METRICS,
                    required_metrics=["api_requests_total", "auth_success_rate", "rate_limit_hits"],
                    min_data_points=100,
                    max_staleness_minutes=1,
                    required_labels=["endpoint", "method", "status_code"],
                    business_criticality="critical"
                )
            ],
            "trading-engine": [
                CompletenessRequirement(
                    category=CompletenessCategory.BUSINESS_METRICS,
                    required_metrics=["orders_executed", "pnl_total", "risk_exposure", "slippage"],
                    min_data_points=20,
                    max_staleness_minutes=1,
                    required_labels=["symbol", "strategy", "order_type"],
                    business_criticality="critical"
                )
            ],
            "data-bridge": [
                CompletenessRequirement(
                    category=CompletenessCategory.BUSINESS_METRICS,
                    required_metrics=["tick_count", "stream_throughput", "data_lag"],
                    min_data_points=1000,
                    max_staleness_minutes=1,
                    required_labels=["source", "symbol", "stream_type"],
                    business_criticality="critical"
                )
            ],
            "ai-provider": [
                CompletenessRequirement(
                    category=CompletenessCategory.BUSINESS_METRICS,
                    required_metrics=["completion_requests", "provider_success_rate", "cost_estimate"],
                    min_data_points=50,
                    max_staleness_minutes=5,
                    required_labels=["provider", "model", "request_type"],
                    business_criticality="high"
                )
            ]
        }
        
        # Add core requirements
        for req in core_requirements:
            self.completeness_requirements[f"core_{req.category.value}"] = req
        
        # Add service-specific requirements
        if self.service_name in service_specific:
            for i, req in enumerate(service_specific[self.service_name]):
                self.completeness_requirements[f"{self.service_name}_{req.category.value}_{i}"] = req
        
        # Observability stack requirement
        self.completeness_requirements["observability_stack"] = CompletenessRequirement(
            category=CompletenessCategory.OBSERVABILITY_STACK,
            required_metrics=["log_entries", "trace_spans", "metric_data_points"],
            min_data_points=100,
            max_staleness_minutes=5,
            required_labels=["service", "environment", "source"],
            business_criticality="high"
        )
    
    def increment_counter(self, 
                         name: str,
                         value: float = 1.0,
                         labels: Optional[Dict[str, str]] = None,
                         scope: MetricScope = MetricScope.SERVICE) -> None:
        """
        Increment a counter metric.
        
        Args:
            name: Metric name
            value: Value to increment by
            labels: Metric labels for grouping
            scope: Metric scope
        """
        with self._lock:
            metric_key = self._build_metric_key(name, labels, scope)
            self._counters[metric_key] += value
            
            # Store detailed metric
            metric = Metric(
                name=name,
                metric_type=MetricType.COUNTER,
                scope=scope,
                value=self._counters[metric_key],
                timestamp=datetime.now(),
                labels=labels or {}
            )
            
            self._metrics[metric_key].append(metric)
            self._cleanup_old_metrics(metric_key)
    
    def set_gauge(self, 
                  name: str,
                  value: float,
                  labels: Optional[Dict[str, str]] = None,
                  scope: MetricScope = MetricScope.SERVICE) -> None:
        """
        Set a gauge metric value.
        
        Args:
            name: Metric name
            value: Current value
            labels: Metric labels
            scope: Metric scope
        """
        with self._lock:
            metric_key = self._build_metric_key(name, labels, scope)
            self._gauges[metric_key] = value
            
            # Store detailed metric
            metric = Metric(
                name=name,
                metric_type=MetricType.GAUGE,
                scope=scope,
                value=value,
                timestamp=datetime.now(),
                labels=labels or {}
            )
            
            self._metrics[metric_key].append(metric)
            self._cleanup_old_metrics(metric_key)
    
    def record_histogram(self, 
                        name: str,
                        value: float,
                        labels: Optional[Dict[str, str]] = None,
                        scope: MetricScope = MetricScope.SERVICE) -> None:
        """
        Record a value in a histogram metric.
        
        Args:
            name: Metric name
            value: Value to record
            labels: Metric labels
            scope: Metric scope
        """
        with self._lock:
            metric_key = self._build_metric_key(name, labels, scope)
            self._histograms[metric_key].append(value)
            
            # Store detailed metric
            metric = Metric(
                name=name,
                metric_type=MetricType.HISTOGRAM,
                scope=scope,
                value=value,
                timestamp=datetime.now(),
                labels=labels or {}
            )
            
            self._metrics[metric_key].append(metric)
            self._cleanup_old_metrics(metric_key)
    
    def start_timer(self, 
                   name: str,
                   labels: Optional[Dict[str, str]] = None,
                   scope: MetricScope = MetricScope.SERVICE) -> Callable[[], None]:
        """
        Start a timer metric and return a function to stop it.
        
        Args:
            name: Metric name
            labels: Metric labels
            scope: Metric scope
            
        Returns:
            Function to call when timer should stop
        """
        start_time = time.time()
        
        def stop_timer():
            duration = time.time() - start_time
            self.record_timer(name, duration, labels, scope)
        
        return stop_timer
    
    def record_timer(self, 
                    name: str,
                    duration: float,
                    labels: Optional[Dict[str, str]] = None,
                    scope: MetricScope = MetricScope.SERVICE) -> None:
        """
        Record a timer duration.
        
        Args:
            name: Metric name
            duration: Duration in seconds
            labels: Metric labels
            scope: Metric scope
        """
        with self._lock:
            metric_key = self._build_metric_key(name, labels, scope)
            self._timers[metric_key].append(duration)
            
            # Keep only recent timer values
            if len(self._timers[metric_key]) > 1000:
                self._timers[metric_key] = self._timers[metric_key][-1000:]
            
            # Store detailed metric
            metric = Metric(
                name=name,
                metric_type=MetricType.TIMER,
                scope=scope,
                value=duration,
                timestamp=datetime.now(),
                labels=labels or {}
            )
            
            self._metrics[metric_key].append(metric)
            self._cleanup_old_metrics(metric_key)
    
    def timer_context(self, 
                     name: str,
                     labels: Optional[Dict[str, str]] = None,
                     scope: MetricScope = MetricScope.SERVICE):
        """
        Context manager for timing operations.
        
        Usage:
            with metrics.timer_context("operation_name"):
                # Operation to time
                pass
        """
        return TimerContext(self, name, labels, scope)
    
    def get_counter(self, 
                   name: str,
                   labels: Optional[Dict[str, str]] = None,
                   scope: MetricScope = MetricScope.SERVICE) -> float:
        """Get current counter value"""
        with self._lock:
            metric_key = self._build_metric_key(name, labels, scope)
            return self._counters.get(metric_key, 0.0)
    
    def get_gauge(self, 
                 name: str,
                 labels: Optional[Dict[str, str]] = None,
                 scope: MetricScope = MetricScope.SERVICE) -> Optional[float]:
        """Get current gauge value"""
        with self._lock:
            metric_key = self._build_metric_key(name, labels, scope)
            return self._gauges.get(metric_key)
    
    def get_histogram_stats(self, 
                           name: str,
                           labels: Optional[Dict[str, str]] = None,
                           scope: MetricScope = MetricScope.SERVICE) -> Dict[str, float]:
        """Get histogram statistics"""
        with self._lock:
            metric_key = self._build_metric_key(name, labels, scope)
            values = list(self._histograms.get(metric_key, []))
            
            if not values:
                return {}
            
            values.sort()
            count = len(values)
            
            return {
                "count": count,
                "min": min(values),
                "max": max(values),
                "mean": sum(values) / count,
                "p50": values[int(count * 0.5)] if count > 0 else 0,
                "p90": values[int(count * 0.9)] if count > 0 else 0,
                "p95": values[int(count * 0.95)] if count > 0 else 0,
                "p99": values[int(count * 0.99)] if count > 0 else 0
            }
    
    def get_timer_stats(self, 
                       name: str,
                       labels: Optional[Dict[str, str]] = None,
                       scope: MetricScope = MetricScope.SERVICE) -> Dict[str, float]:
        """Get timer statistics"""
        with self._lock:
            metric_key = self._build_metric_key(name, labels, scope)
            values = list(self._timers.get(metric_key, []))
            
            if not values:
                return {}
            
            values.sort()
            count = len(values)
            
            return {
                "count": count,
                "min_ms": min(values) * 1000,
                "max_ms": max(values) * 1000,
                "mean_ms": (sum(values) / count) * 1000,
                "p50_ms": values[int(count * 0.5)] * 1000 if count > 0 else 0,
                "p90_ms": values[int(count * 0.9)] * 1000 if count > 0 else 0,
                "p95_ms": values[int(count * 0.95)] * 1000 if count > 0 else 0,
                "p99_ms": values[int(count * 0.99)] * 1000 if count > 0 else 0
            }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metric values"""
        with self._lock:
            # Check if we need to regenerate aggregated cache
            now = datetime.now()
            if (self._last_aggregation is None or 
                (now - self._last_aggregation).total_seconds() > 30):
                self._aggregate_metrics()
                self._last_aggregation = now
            
            return dict(self._aggregated_cache)
    
    def audit_completeness(self) -> Dict[str, Any]:
        """
        AI Brain Completeness Auditor - Comprehensive monitoring completeness validation
        
        Returns:
            Detailed completeness audit results with confidence scores
        """
        try:
            audit_timestamp = datetime.now()
            self.completeness_gaps.clear()
            
            overall_completeness_score = 1.0
            category_scores = {}
            
            with self._lock:
                current_metrics = self.get_all_metrics()
                
                # Audit each completeness requirement
                for req_id, requirement in self.completeness_requirements.items():
                    category_score, gaps = self._audit_requirement(requirement, current_metrics)
                    category_scores[req_id] = category_score
                    self.completeness_gaps.extend(gaps)
                    
                    # Weight critical requirements more heavily
                    weight = {
                        "critical": 1.0,
                        "high": 0.8,
                        "medium": 0.6,
                        "low": 0.4
                    }.get(requirement.business_criticality, 0.5)
                    
                    overall_completeness_score *= (category_score ** weight)
            
            # Calculate observability coverage
            observability_coverage = self._calculate_observability_coverage(current_metrics)
            
            # Calculate production readiness score
            production_readiness = self._calculate_production_readiness_score(
                overall_completeness_score, observability_coverage, len(self.completeness_gaps)
            )
            
            self.production_readiness_score = production_readiness
            self.last_completeness_audit = audit_timestamp
            
            # AI Brain confidence assessment
            ai_brain_confidence = 1.0
            if self.ai_brain_confidence and overall_completeness_score < 0.85:
                ai_brain_confidence = self.ai_brain_confidence.calculate_completeness_confidence(
                    current_metrics, category_scores, overall_completeness_score
                )
            
            audit_result = {
                "timestamp": audit_timestamp.isoformat(),
                "service": self.service_name,
                "environment": self.environment,
                "overall_completeness_score": overall_completeness_score,
                "observability_coverage": observability_coverage,
                "production_readiness_score": production_readiness,
                "ai_brain_confidence": ai_brain_confidence,
                "category_scores": category_scores,
                "completeness_gaps": self.completeness_gaps[-20:],  # Last 20 gaps
                "total_requirements": len(self.completeness_requirements),
                "requirements_met": len([s for s in category_scores.values() if s >= 0.85]),
                "critical_gaps": len([g for g in self.completeness_gaps if g.get("criticality") == "critical"]),
                "production_ready": production_readiness >= 0.85
            }
            
            self.logger.info("Completeness audit completed", extra={
                "completeness_score": overall_completeness_score,
                "production_readiness": production_readiness,
                "total_gaps": len(self.completeness_gaps),
                "ai_brain_confidence": ai_brain_confidence
            })
            
            return audit_result
            
        except Exception as e:
            if self.ai_brain_error_dna:
                self.ai_brain_error_dna.log_error(e, {
                    "context": "completeness_audit",
                    "service": self.service_name,
                    "requirements_count": len(self.completeness_requirements)
                })
            
            self.logger.error(f"Completeness audit error: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "service": self.service_name,
                "error": str(e),
                "overall_completeness_score": 0.0,
                "production_ready": False
            }
    
    def _audit_requirement(self, requirement: CompletenessRequirement, current_metrics: Dict[str, Any]) -> Tuple[float, List[Dict[str, Any]]]:
        """Audit individual completeness requirement"""
        gaps = []
        requirement_score = 1.0
        
        # Check each required metric
        missing_metrics = 0
        stale_metrics = 0
        poor_quality_metrics = 0
        
        for metric_name in requirement.required_metrics:
            # Check if metric exists
            metric_found = False
            for metric_key in current_metrics.keys():
                if metric_name in metric_key:
                    metric_found = True
                    
                    # Check data quality (simplified assessment)
                    metric_data = current_metrics[metric_key]
                    if isinstance(metric_data, dict):
                        data_points = metric_data.get("count", 0)
                        if data_points < requirement.min_data_points:
                            poor_quality_metrics += 1
                            gaps.append({
                                "type": CompletenessGap.POOR_DATA_QUALITY.value,
                                "metric": metric_name,
                                "requirement": requirement.category.value,
                                "details": f"Only {data_points} data points, need {requirement.min_data_points}",
                                "criticality": requirement.business_criticality,
                                "timestamp": datetime.now().isoformat()
                            })
                    break
            
            if not metric_found:
                missing_metrics += 1
                gaps.append({
                    "type": CompletenessGap.MISSING_METRIC.value,
                    "metric": metric_name,
                    "requirement": requirement.category.value,
                    "details": f"Required metric '{metric_name}' is missing",
                    "criticality": requirement.business_criticality,
                    "timestamp": datetime.now().isoformat()
                })
        
        # Calculate requirement score based on gaps
        total_metrics = len(requirement.required_metrics)
        if total_metrics > 0:
            completeness_ratio = 1.0 - ((missing_metrics + stale_metrics + poor_quality_metrics) / total_metrics)
            requirement_score = max(0.0, completeness_ratio)
        
        return requirement_score, gaps
    
    def _calculate_observability_coverage(self, current_metrics: Dict[str, Any]) -> float:
        """Calculate observability stack coverage"""
        observability_components = {
            "metrics": len([k for k in current_metrics.keys() if "metric" in k or "counter" in k or "gauge" in k]),
            "logs": len([k for k in current_metrics.keys() if "log" in k]),
            "traces": len([k for k in current_metrics.keys() if "trace" in k or "span" in k])
        }
        
        # Calculate coverage based on presence of observability data
        coverage_score = 0.0
        
        if observability_components["metrics"] > 0:
            coverage_score += 0.5  # Metrics are most important
        if observability_components["logs"] > 0:
            coverage_score += 0.3
        if observability_components["traces"] > 0:
            coverage_score += 0.2
        
        return min(1.0, coverage_score)
    
    def _calculate_production_readiness_score(self, completeness: float, observability: float, gap_count: int) -> float:
        """Calculate production readiness score"""
        # Base score from completeness and observability
        base_score = (completeness * 0.7) + (observability * 0.3)
        
        # Penalize for gaps (each gap reduces score)
        gap_penalty = min(0.5, gap_count * 0.02)  # Max 50% penalty
        
        # Production environment has higher standards
        if self.environment == "production":
            base_score *= 1.1  # Slight bonus for production monitoring
        
        return max(0.0, min(1.0, base_score - gap_penalty))
    
    def get_completeness_status(self) -> Dict[str, Any]:
        """Get current completeness status summary"""
        # Run fresh audit if none exists or is stale
        if (self.last_completeness_audit is None or 
            (datetime.now() - self.last_completeness_audit).total_seconds() > 300):  # 5 minutes
            return self.audit_completeness()
        
        return {
            "timestamp": self.last_completeness_audit.isoformat() if self.last_completeness_audit else None,
            "service": self.service_name,
            "production_readiness_score": self.production_readiness_score,
            "recent_gaps": len(self.completeness_gaps),
            "requirements_configured": len(self.completeness_requirements),
            "last_audit_age_seconds": (datetime.now() - self.last_completeness_audit).total_seconds() if self.last_completeness_audit else None,
            "ai_brain_completeness_enabled": AI_BRAIN_AVAILABLE
        }
    
    def get_service_metrics(self) -> Dict[str, Any]:
        """Get service-specific metrics summary"""
        metrics = self.get_all_metrics()
        
        return {
            "service": self.service_name,
            "environment": self.environment,
            "timestamp": datetime.now().isoformat(),
            "counters": {k: v for k, v in metrics.items() if "counter" in k},
            "gauges": {k: v for k, v in metrics.items() if "gauge" in k},
            "histograms": {k: v for k, v in metrics.items() if "histogram" in k},
            "timers": {k: v for k, v in metrics.items() if "timer" in k},
            "key_metrics": {metric: metrics.get(metric, 0) for metric in self.key_metrics}
        }
    
    def create_snapshot(self) -> MetricSnapshot:
        """Create a snapshot of current metrics"""
        return MetricSnapshot(
            timestamp=datetime.now(),
            service_name=self.service_name,
            environment=self.environment,
            metrics=self.get_all_metrics(),
            metadata={
                "retention_hours": self.retention_hours,
                "flush_interval": self.flush_interval,
                "total_metrics": len(self._metrics)
            }
        )
    
    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        
        with self._lock:
            # Export counters
            for key, value in self._counters.items():
                name, labels = self._parse_metric_key(key)
                label_str = self._format_prometheus_labels(labels)
                lines.append(f"{self.service_name}_{name}_total{label_str} {value}")
            
            # Export gauges
            for key, value in self._gauges.items():
                name, labels = self._parse_metric_key(key)
                label_str = self._format_prometheus_labels(labels)
                lines.append(f"{self.service_name}_{name}{label_str} {value}")
            
            # Export histogram percentiles
            for key, values in self._histograms.items():
                if values:
                    name, labels = self._parse_metric_key(key)
                    sorted_values = sorted(values)
                    count = len(sorted_values)
                    
                    label_str = self._format_prometheus_labels(labels)
                    
                    # Add percentiles
                    if count > 0:
                        lines.append(f"{self.service_name}_{name}_p50{label_str} {sorted_values[int(count * 0.5)]}")
                        lines.append(f"{self.service_name}_{name}_p90{label_str} {sorted_values[int(count * 0.9)]}")
                        lines.append(f"{self.service_name}_{name}_p95{label_str} {sorted_values[int(count * 0.95)]}")
        
        return "\n".join(lines)
    
    def _build_metric_key(self, 
                         name: str,
                         labels: Optional[Dict[str, str]],
                         scope: MetricScope) -> str:
        """Build a unique metric key"""
        label_str = ""
        if labels:
            sorted_labels = sorted(labels.items())
            label_str = "|".join(f"{k}={v}" for k, v in sorted_labels)
        
        return f"{scope.value}:{name}:{label_str}"
    
    def _parse_metric_key(self, key: str) -> tuple[str, Dict[str, str]]:
        """Parse metric key back to name and labels"""
        parts = key.split(":", 2)
        if len(parts) != 3:
            return key, {}
        
        scope, name, label_str = parts
        labels = {}
        
        if label_str:
            for pair in label_str.split("|"):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    labels[k] = v
        
        return name, labels
    
    def _format_prometheus_labels(self, labels: Dict[str, str]) -> str:
        """Format labels for Prometheus export"""
        if not labels:
            return ""
        
        label_pairs = [f'{k}="{v}"' for k, v in sorted(labels.items())]
        return "{" + ",".join(label_pairs) + "}"
    
    def _aggregate_metrics(self):
        """Aggregate metrics for cache"""
        self._aggregated_cache.clear()
        
        # Aggregate counters
        for key, value in self._counters.items():
            self._aggregated_cache[f"counter:{key}"] = value
        
        # Aggregate gauges
        for key, value in self._gauges.items():
            self._aggregated_cache[f"gauge:{key}"] = value
        
        # Aggregate histograms
        for key, values in self._histograms.items():
            if values:
                stats = self.get_histogram_stats(*self._parse_metric_key(key))
                self._aggregated_cache[f"histogram:{key}"] = stats
        
        # Aggregate timers
        for key, values in self._timers.items():
            if values:
                stats = self.get_timer_stats(*self._parse_metric_key(key))
                self._aggregated_cache[f"timer:{key}"] = stats
    
    def _cleanup_old_metrics(self, metric_key: str):
        """Clean up old metric data to maintain retention window"""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
        
        if metric_key in self._metrics:
            self._metrics[metric_key] = [
                m for m in self._metrics[metric_key]
                if m.timestamp > cutoff_time
            ]
    
    async def start_background_tasks(self):
        """Start background tasks for metrics processing"""
        if self.is_running:
            return
        
        self.is_running = True
        self._flush_task = asyncio.create_task(self._flush_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._completeness_audit_task = asyncio.create_task(self._completeness_audit_loop())
        
        self.logger.info("AI Brain Enhanced Metrics background tasks started")
    
    async def stop_background_tasks(self):
        """Stop background tasks"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self._flush_task:
            self._flush_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()
        if self._completeness_audit_task:
            self._completeness_audit_task.cancel()
        
        self.logger.info("AI Brain Enhanced Metrics background tasks stopped")
    
    async def _flush_loop(self):
        """Background task to flush metrics"""
        try:
            while self.is_running:
                # In production, this would flush to external systems
                snapshot = self.create_snapshot()
                
                # Log metrics summary
                metrics_summary = {
                    "counters": len(self._counters),
                    "gauges": len(self._gauges),
                    "histograms": len(self._histograms),
                    "timers": len(self._timers)
                }
                
                self.logger.info("Metrics flushed", extra={
                    "snapshot_timestamp": snapshot.timestamp.isoformat(),
                    "metrics_summary": metrics_summary
                })
                
                await asyncio.sleep(self.flush_interval)
        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Metrics flush loop error: {e}")
    
    async def _cleanup_loop(self):
        """Background task to cleanup old metrics"""
        try:
            while self.is_running:
                with self._lock:
                    for metric_key in list(self._metrics.keys()):
                        self._cleanup_old_metrics(metric_key)
                
                await asyncio.sleep(300)  # Cleanup every 5 minutes
        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Metrics cleanup loop error: {e}")
    
    async def _completeness_audit_loop(self):
        """Background task for AI Brain completeness auditing"""
        try:
            while self.is_running:
                # Run completeness audit
                audit_result = self.audit_completeness()
                
                # Log audit summary
                self.logger.info("Completeness audit completed", extra={
                    "production_readiness": audit_result.get("production_readiness_score", 0.0),
                    "completeness_score": audit_result.get("overall_completeness_score", 0.0),
                    "gaps_found": len(audit_result.get("completeness_gaps", [])),
                    "production_ready": audit_result.get("production_ready", False)
                })
                
                # Alert on low production readiness in production environment
                if (self.environment == "production" and 
                    audit_result.get("production_readiness_score", 0.0) < 0.85):
                    self.logger.warning("Production readiness below threshold", extra={
                        "current_score": audit_result.get("production_readiness_score", 0.0),
                        "threshold": 0.85,
                        "critical_gaps": audit_result.get("critical_gaps", 0)
                    })
                
                # Wait before next audit (more frequent in production)
                audit_interval = 300 if self.environment == "production" else 600  # 5 or 10 minutes
                await asyncio.sleep(audit_interval)
        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            if self.ai_brain_error_dna:
                self.ai_brain_error_dna.log_error(e, {
                    "context": "completeness_audit_loop",
                    "service": self.service_name
                })
            self.logger.error(f"Completeness audit loop error: {e}")

class TimerContext:
    """Context manager for timing operations"""
    
    def __init__(self, 
                 metrics_core: MetricsCore,
                 name: str,
                 labels: Optional[Dict[str, str]] = None,
                 scope: MetricScope = MetricScope.SERVICE):
        self.metrics_core = metrics_core
        self.name = name
        self.labels = labels
        self.scope = scope
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.metrics_core.record_timer(self.name, duration, self.labels, self.scope)

# Global metrics core instances
_metrics_cores: Dict[str, MetricsCore] = {}

def get_metrics_core(service_name: str, environment: str = "development") -> MetricsCore:
    """Get or create metrics core for a service"""
    key = f"{service_name}:{environment}"
    if key not in _metrics_cores:
        _metrics_cores[key] = MetricsCore(service_name, environment)
    return _metrics_cores[key]

# Convenience decorators
def track_counter(name: str, 
                 labels: Optional[Dict[str, str]] = None,
                 scope: MetricScope = MetricScope.SERVICE):
    """Decorator to track function calls as counter"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            service_name = getattr(func, '__module__', 'unknown').split('.')[0]
            metrics = get_metrics_core(service_name)
            metrics.increment_counter(name, 1.0, labels, scope)
            return func(*args, **kwargs)
        return wrapper
    return decorator

def track_timer(name: str, 
               labels: Optional[Dict[str, str]] = None,
               scope: MetricScope = MetricScope.SERVICE):
    """Decorator to track function execution time"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            service_name = getattr(func, '__module__', 'unknown').split('.')[0]
            metrics = get_metrics_core(service_name)
            
            with metrics.timer_context(name, labels, scope):
                return func(*args, **kwargs)
        return wrapper
    return decorator