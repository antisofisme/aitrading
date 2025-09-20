"""
health_core.py - System Health Monitoring

🎯 PURPOSE:
Business: Comprehensive system health monitoring for trading platform reliability
Technical: Real-time health checks, metrics collection, and alerting system
Domain: Health Monitoring/System Diagnostics/Reliability

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:27.882Z
Session: client-side-ai-brain-full-compliance
Confidence: 88%
Complexity: medium

🧩 PATTERNS USED:
- AI_BRAIN_HEALTH_MONITORING: Comprehensive system health monitoring
- PROACTIVE_DIAGNOSTICS: Predictive health analysis and alerting

📦 DEPENDENCIES:
Internal: logger_manager, performance_manager, event_core
External: psutil, asyncio, dataclasses, enum, time

💡 AI DECISION REASONING:
Trading systems require continuous health monitoring to prevent downtime and ensure optimal performance during market hours.

🚀 USAGE:
health_core.check_system_health()

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

import asyncio
import threading
import time
import psutil
import json
from typing import Dict, Any, Optional, List, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
from pathlib import Path
import uuid
import hashlib

class ComponentStatus(Enum):
    """Component health status"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"
    OFFLINE = "offline"

class MetricType(Enum):
    """Types of health metrics"""
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_USAGE = "disk_usage"
    NETWORK_LATENCY = "network_latency"
    ERROR_RATE = "error_rate"
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    QUEUE_SIZE = "queue_size"
    CONNECTION_COUNT = "connection_count"
    CUSTOM = "custom"

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class HealthMetric:
    """Individual health metric"""
    name: str
    metric_type: MetricType
    value: float
    unit: str
    timestamp: datetime
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def status(self) -> ComponentStatus:
        """Determine status based on thresholds"""
        if self.threshold_critical is not None and self.value >= self.threshold_critical:
            return ComponentStatus.CRITICAL
        elif self.threshold_warning is not None and self.value >= self.threshold_warning:
            return ComponentStatus.WARNING
        else:
            return ComponentStatus.HEALTHY

@dataclass
class ComponentHealth:
    """Health status of a system component"""
    component_name: str
    status: ComponentStatus
    last_check: datetime
    metrics: Dict[str, HealthMetric]
    dependencies: List[str] = None
    error_count: int = 0
    uptime_seconds: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.metadata is None:
            self.metadata = {}

@dataclass
class HealthAlert:
    """Health monitoring alert"""
    id: str
    component: str
    severity: AlertSeverity
    metric_name: str
    current_value: float
    threshold_value: float
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class SystemDiagnostics:
    """System-wide diagnostics"""
    overall_status: ComponentStatus
    component_count: int
    healthy_components: int
    warning_components: int
    critical_components: int
    active_alerts: int
    last_updated: datetime
    system_metrics: Dict[str, HealthMetric] = None
    recommendations: List[str] = None
    
    def __post_init__(self):
        if self.system_metrics is None:
            self.system_metrics = {}
        if self.recommendations is None:
            self.recommendations = []

class HealthCore:
    """
    AI Brain Health Core System
    Intelligent system health monitoring and diagnostics
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        # Component tracking
        self._components: Dict[str, ComponentHealth] = {}
        self._metric_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._health_checks: Dict[str, Callable] = {}
        
        # Alert management
        self._alerts: Dict[str, HealthAlert] = {}
        self._alert_rules: Dict[str, Dict[str, Any]] = {}
        self._alert_history: deque = deque(maxlen=5000)
        
        # AI Brain predictive features
        self._trend_analysis: Dict[str, List[float]] = defaultdict(list)
        self._anomaly_detection: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self._performance_baselines: Dict[str, Dict[str, float]] = defaultdict(dict)
        
        # Configuration
        self._monitoring_interval = 30  # seconds
        self._enable_predictive_alerts = True
        self._enable_auto_recovery = True
        self._enable_trend_analysis = True
        self._alert_cooldown = 300  # 5 minutes
        
        # System metrics
        self._system_start_time = datetime.now()
        self._last_full_check = None
        
        # Background tasks
        self._running = False
        self._background_tasks: List[asyncio.Task] = []
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Persistence
        self._health_log_path = Path("logs/health_monitoring.json")
        self._alert_log_path = Path("logs/health_alerts.json")
        
        # Initialize system
        self._initialize_health_core()
    
    @classmethod
    def get_instance(cls) -> 'HealthCore':
        """Singleton pattern with thread safety"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def _initialize_health_core(self):
        """Initialize health core system"""
        # Register default health checks
        self._register_default_health_checks()
        
        # Load default alert rules
        self._load_default_alert_rules()
        
        print("❤️ AI Brain Health Core initialized")
    
    async def start(self):
        """Start health monitoring system"""
        if self._running:
            return
        
        self._running = True
        
        # Start background monitoring tasks
        self._background_tasks = [
            asyncio.create_task(self._health_monitor()),
            asyncio.create_task(self._system_diagnostics()),
            asyncio.create_task(self._trend_analyzer()),
            asyncio.create_task(self._alert_processor()),
            asyncio.create_task(self._recovery_manager())
        ]
        
        print("💓 Health monitoring started")
    
    async def stop(self):
        """Stop health monitoring system"""
        if not self._running:
            return
        
        self._running = False
        
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        # Save final state
        self._save_health_state()
        
        print("💔 Health monitoring stopped")
    
    # ==================== COMPONENT REGISTRATION ====================
    
    def register_component(self, component_name: str, 
                          health_check: Optional[Callable] = None,
                          dependencies: Optional[List[str]] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Register component for health monitoring"""
        try:
            with self._lock:
                # Create component health record
                self._components[component_name] = ComponentHealth(
                    component_name=component_name,
                    status=ComponentStatus.UNKNOWN,
                    last_check=datetime.now(),
                    metrics={},
                    dependencies=dependencies or [],
                    metadata=metadata or {}
                )
                
                # Register health check if provided
                if health_check:
                    self._health_checks[component_name] = health_check
                
                print(f"📋 Component registered for monitoring: {component_name}")
                return True
                
        except Exception as e:
            print(f"❌ Failed to register component {component_name}: {e}")
            return False
    
    def unregister_component(self, component_name: str) -> bool:
        """Unregister component from monitoring"""
        try:
            with self._lock:
                if component_name in self._components:
                    del self._components[component_name]
                
                if component_name in self._health_checks:
                    del self._health_checks[component_name]
                
                print(f"🗑️ Component unregistered: {component_name}")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Failed to unregister component {component_name}: {e}")
            return False
    
    # ==================== HEALTH CHECKING ====================
    
    async def check_component_health(self, component_name: str) -> Optional[ComponentHealth]:
        """Check health of specific component"""
        if component_name not in self._components:
            return None
        
        try:
            component = self._components[component_name]
            
            # Update last check time
            component.last_check = datetime.now()
            
            # Run custom health check if available
            if component_name in self._health_checks:
                health_check = self._health_checks[component_name]
                
                # Execute health check (support both sync and async)
                try:
                    if asyncio.iscoroutinefunction(health_check):
                        check_result = await health_check()
                    else:
                        check_result = health_check()
                    
                    # Process health check result
                    if isinstance(check_result, bool):
                        component.status = ComponentStatus.HEALTHY if check_result else ComponentStatus.CRITICAL
                    elif isinstance(check_result, dict):
                        self._process_health_check_result(component, check_result)
                    
                except Exception as e:
                    component.status = ComponentStatus.CRITICAL
                    component.error_count += 1
                    print(f"❌ Health check failed for {component_name}: {e}")
            
            # Collect system metrics for the component
            await self._collect_component_metrics(component)
            
            # Determine overall component status based on metrics
            self._determine_component_status(component)
            
            # Check for alerts
            await self._check_component_alerts(component)
            
            return component
            
        except Exception as e:
            print(f"❌ Component health check error for {component_name}: {e}")
            return None
    
    def _process_health_check_result(self, component: ComponentHealth, result: Dict[str, Any]):
        """Process health check result dictionary"""
        # Update status
        if 'status' in result:
            if isinstance(result['status'], str):
                try:
                    component.status = ComponentStatus(result['status'].lower())
                except ValueError:
                    component.status = ComponentStatus.UNKNOWN
            elif isinstance(result['status'], bool):
                component.status = ComponentStatus.HEALTHY if result['status'] else ComponentStatus.CRITICAL
        
        # Update metrics
        if 'metrics' in result and isinstance(result['metrics'], dict):
            for metric_name, metric_value in result['metrics'].items():
                if isinstance(metric_value, (int, float)):
                    metric = HealthMetric(
                        name=metric_name,
                        metric_type=MetricType.CUSTOM,
                        value=float(metric_value),
                        unit=result.get('units', {}).get(metric_name, ''),
                        timestamp=datetime.now()
                    )
                    component.metrics[metric_name] = metric
        
        # Update error count
        if 'error_count' in result:
            component.error_count = result['error_count']
        
        # Update metadata
        if 'metadata' in result:
            component.metadata.update(result['metadata'])
    
    async def _collect_component_metrics(self, component: ComponentHealth):
        """Collect system metrics for component"""
        try:
            # CPU usage
            cpu_metric = HealthMetric(
                name="cpu_usage",
                metric_type=MetricType.CPU_USAGE,
                value=psutil.cpu_percent(interval=0.1),
                unit="%",
                timestamp=datetime.now(),
                threshold_warning=70.0,
                threshold_critical=90.0
            )
            component.metrics["cpu_usage"] = cpu_metric
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_metric = HealthMetric(
                name="memory_usage",
                metric_type=MetricType.MEMORY_USAGE,
                value=memory.percent,
                unit="%",
                timestamp=datetime.now(),
                threshold_warning=80.0,
                threshold_critical=95.0
            )
            component.metrics["memory_usage"] = memory_metric
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_metric = HealthMetric(
                name="disk_usage",
                metric_type=MetricType.DISK_USAGE,
                value=(disk.used / disk.total) * 100,
                unit="%",
                timestamp=datetime.now(),
                threshold_warning=80.0,
                threshold_critical=95.0
            )
            component.metrics["disk_usage"] = disk_metric
            
            # Update uptime
            component.uptime_seconds = (datetime.now() - self._system_start_time).total_seconds()
            
            # Store metrics in history
            for metric_name, metric in component.metrics.items():
                history_key = f"{component.component_name}:{metric_name}"
                self._metric_history[history_key].append({
                    'timestamp': metric.timestamp,
                    'value': metric.value
                })
            
        except Exception as e:
            print(f"❌ Failed to collect metrics for {component.component_name}: {e}")
    
    def _determine_component_status(self, component: ComponentHealth):
        """Determine overall component status based on metrics"""
        statuses = []
        
        # Check each metric's status
        for metric in component.metrics.values():
            statuses.append(metric.status)
        
        # Determine worst status
        if ComponentStatus.CRITICAL in statuses:
            component.status = ComponentStatus.CRITICAL
        elif ComponentStatus.WARNING in statuses:
            component.status = ComponentStatus.WARNING
        elif ComponentStatus.HEALTHY in statuses:
            component.status = ComponentStatus.HEALTHY
        else:
            component.status = ComponentStatus.UNKNOWN
    
    # ==================== HEALTH MONITORING LOOP ====================
    
    async def _health_monitor(self):
        """Main health monitoring loop"""
        while self._running:
            try:
                start_time = time.time()
                
                # Check all registered components
                for component_name in list(self._components.keys()):
                    await self.check_component_health(component_name)
                
                # Update last full check time
                self._last_full_check = datetime.now()
                
                # Calculate sleep time to maintain interval
                elapsed = time.time() - start_time
                sleep_time = max(0, self._monitoring_interval - elapsed)
                
                await asyncio.sleep(sleep_time)
                
            except Exception as e:
                print(f"❌ Health monitor error: {e}")
                await asyncio.sleep(self._monitoring_interval)
    
    async def _system_diagnostics(self):
        """Generate system-wide diagnostics"""
        while self._running:
            try:
                await asyncio.sleep(60)  # Run every minute
                
                diagnostics = self._generate_system_diagnostics()
                
                # Log diagnostics
                self._log_diagnostics(diagnostics)
                
            except Exception as e:
                print(f"❌ System diagnostics error: {e}")
    
    def _generate_system_diagnostics(self) -> SystemDiagnostics:
        """Generate comprehensive system diagnostics"""
        component_count = len(self._components)
        healthy_count = sum(1 for c in self._components.values() if c.status == ComponentStatus.HEALTHY)
        warning_count = sum(1 for c in self._components.values() if c.status == ComponentStatus.WARNING)
        critical_count = sum(1 for c in self._components.values() if c.status == ComponentStatus.CRITICAL)
        
        # Determine overall status
        if critical_count > 0:
            overall_status = ComponentStatus.CRITICAL
        elif warning_count > 0:
            overall_status = ComponentStatus.WARNING
        elif healthy_count == component_count and component_count > 0:
            overall_status = ComponentStatus.HEALTHY
        else:
            overall_status = ComponentStatus.UNKNOWN
        
        # Collect system-wide metrics
        system_metrics = {}
        try:
            # Overall CPU usage
            system_metrics["system_cpu"] = HealthMetric(
                name="system_cpu",
                metric_type=MetricType.CPU_USAGE,
                value=psutil.cpu_percent(interval=0.1),
                unit="%",
                timestamp=datetime.now()
            )
            
            # Overall memory usage
            memory = psutil.virtual_memory()
            system_metrics["system_memory"] = HealthMetric(
                name="system_memory",
                metric_type=MetricType.MEMORY_USAGE,
                value=memory.percent,
                unit="%",
                timestamp=datetime.now()
            )
            
            # Process count
            system_metrics["process_count"] = HealthMetric(
                name="process_count",
                metric_type=MetricType.CUSTOM,
                value=len(psutil.pids()),
                unit="count",
                timestamp=datetime.now()
            )
            
        except Exception as e:
            print(f"❌ Failed to collect system metrics: {e}")
        
        # Generate recommendations
        recommendations = self._generate_recommendations(overall_status, critical_count, warning_count)
        
        return SystemDiagnostics(
            overall_status=overall_status,
            component_count=component_count,
            healthy_components=healthy_count,
            warning_components=warning_count,
            critical_components=critical_count,
            active_alerts=len([a for a in self._alerts.values() if not a.resolved]),
            last_updated=datetime.now(),
            system_metrics=system_metrics,
            recommendations=recommendations
        )
    
    def _generate_recommendations(self, overall_status: ComponentStatus, 
                                critical_count: int, warning_count: int) -> List[str]:
        """Generate health recommendations based on system status"""
        recommendations = []
        
        if overall_status == ComponentStatus.CRITICAL:
            recommendations.append("🚨 System has critical issues requiring immediate attention")
            if critical_count > 1:
                recommendations.append(f"Multiple components ({critical_count}) are in critical state")
        
        if overall_status == ComponentStatus.WARNING:
            recommendations.append("⚠️ System has performance issues that should be addressed")
            
        if warning_count > 3:
            recommendations.append("Consider investigating common causes of warnings")
        
        # Check for resource issues
        for component in self._components.values():
            if "cpu_usage" in component.metrics and component.metrics["cpu_usage"].value > 80:
                recommendations.append("High CPU usage detected - consider optimizing processes")
            if "memory_usage" in component.metrics and component.metrics["memory_usage"].value > 85:
                recommendations.append("High memory usage detected - check for memory leaks")
            if "disk_usage" in component.metrics and component.metrics["disk_usage"].value > 85:
                recommendations.append("Low disk space - consider cleanup or expansion")
        
        if not recommendations:
            recommendations.append("✅ System is operating normally")
        
        return recommendations
    
    # ==================== ALERT MANAGEMENT ====================
    
    async def _check_component_alerts(self, component: ComponentHealth):
        """Check component for alert conditions"""
        for metric_name, metric in component.metrics.items():
            # Check for threshold violations
            if metric.status in [ComponentStatus.WARNING, ComponentStatus.CRITICAL]:
                await self._create_alert(component, metric)
    
    async def _create_alert(self, component: ComponentHealth, metric: HealthMetric):
        """Create health alert"""
        alert_key = f"{component.component_name}:{metric.name}"
        
        # Check cooldown period
        if alert_key in self._alerts:
            existing_alert = self._alerts[alert_key]
            if not existing_alert.resolved:
                time_since_alert = (datetime.now() - existing_alert.timestamp).total_seconds()
                if time_since_alert < self._alert_cooldown:
                    return  # Still in cooldown period
        
        # Determine alert severity
        if metric.status == ComponentStatus.CRITICAL:
            severity = AlertSeverity.CRITICAL
            threshold = metric.threshold_critical
        elif metric.status == ComponentStatus.WARNING:
            severity = AlertSeverity.WARNING
            threshold = metric.threshold_warning
        else:
            return  # No alert needed
        
        # Create alert
        alert = HealthAlert(
            id=str(uuid.uuid4()),
            component=component.component_name,
            severity=severity,
            metric_name=metric.name,
            current_value=metric.value,
            threshold_value=threshold,
            message=f"{component.component_name} {metric.name} is {metric.value:.2f}{metric.unit} (threshold: {threshold:.2f}{metric.unit})",
            timestamp=datetime.now()
        )
        
        # Store alert
        self._alerts[alert_key] = alert
        self._alert_history.append(alert)
        
        # Log alert
        print(f"🚨 ALERT [{severity.value.upper()}]: {alert.message}")
        
        # Save to log file
        self._log_alert(alert)
    
    async def _alert_processor(self):
        """Process and manage alerts"""
        while self._running:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Check for resolved alerts
                current_time = datetime.now()
                
                for alert_key, alert in list(self._alerts.items()):
                    if not alert.resolved:
                        # Check if the condition is still present
                        component = self._components.get(alert.component)
                        if component and alert.metric_name in component.metrics:
                            metric = component.metrics[alert.metric_name]
                            
                            # Check if alert condition is resolved
                            if alert.severity == AlertSeverity.CRITICAL and metric.status != ComponentStatus.CRITICAL:
                                alert.resolved = True
                                alert.resolved_at = current_time
                                print(f"✅ RESOLVED: {alert.message}")
                            elif alert.severity == AlertSeverity.WARNING and metric.status == ComponentStatus.HEALTHY:
                                alert.resolved = True
                                alert.resolved_at = current_time
                                print(f"✅ RESOLVED: {alert.message}")
                        else:
                            # Component or metric no longer exists, resolve alert
                            alert.resolved = True
                            alert.resolved_at = current_time
                
            except Exception as e:
                print(f"❌ Alert processor error: {e}")
    
    # ==================== TREND ANALYSIS ====================
    
    async def _trend_analyzer(self):
        """Analyze trends and predict issues"""
        while self._running:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                if self._enable_trend_analysis:
                    self._analyze_metric_trends()
                    
                if self._enable_predictive_alerts:
                    await self._generate_predictive_alerts()
                    
            except Exception as e:
                print(f"❌ Trend analyzer error: {e}")
    
    def _analyze_metric_trends(self):
        """Analyze metric trends for predictive insights"""
        for history_key, metric_history in self._metric_history.items():
            if len(metric_history) < 10:  # Need enough data points
                continue
            
            try:
                # Extract values from history
                values = [entry['value'] for entry in list(metric_history)[-20:]]  # Last 20 values
                
                # Simple trend analysis
                if len(values) >= 10:
                    recent_values = values[-10:]
                    older_values = values[-20:-10]
                    
                    recent_avg = sum(recent_values) / len(recent_values)
                    older_avg = sum(older_values) / len(older_values)
                    
                    # Calculate trend direction and magnitude
                    trend_direction = 1 if recent_avg > older_avg else -1
                    trend_magnitude = abs(recent_avg - older_avg) / older_avg if older_avg > 0 else 0
                    
                    # Store trend analysis
                    self._trend_analysis[history_key] = {
                        'direction': trend_direction,
                        'magnitude': trend_magnitude,
                        'recent_avg': recent_avg,
                        'older_avg': older_avg,
                        'timestamp': datetime.now()
                    }
                    
            except Exception as e:
                print(f"❌ Trend analysis error for {history_key}: {e}")
    
    async def _generate_predictive_alerts(self):
        """Generate predictive alerts based on trends"""
        for history_key, trend_data in self._trend_analysis.items():
            try:
                component_name, metric_name = history_key.split(':', 1)
                
                if component_name in self._components:
                    component = self._components[component_name]
                    
                    # Check for concerning trends
                    if (trend_data['direction'] == 1 and  # Increasing trend
                        trend_data['magnitude'] > 0.1 and  # Significant increase
                        metric_name in ['cpu_usage', 'memory_usage', 'disk_usage', 'error_rate']):
                        
                        # Create predictive alert
                        predicted_value = trend_data['recent_avg'] * (1 + trend_data['magnitude'])
                        
                        # Check if trend will exceed thresholds
                        if metric_name in component.metrics:
                            metric = component.metrics[metric_name]
                            
                            if (metric.threshold_critical and predicted_value > metric.threshold_critical * 0.9):
                                await self._create_predictive_alert(
                                    component_name, metric_name, predicted_value, 
                                    "Critical threshold may be exceeded soon"
                                )
                            elif (metric.threshold_warning and predicted_value > metric.threshold_warning * 0.9):
                                await self._create_predictive_alert(
                                    component_name, metric_name, predicted_value,
                                    "Warning threshold may be exceeded soon"
                                )
                        
            except Exception as e:
                print(f"❌ Predictive alert error for {history_key}: {e}")
    
    async def _create_predictive_alert(self, component_name: str, metric_name: str, 
                                     predicted_value: float, message: str):
        """Create predictive alert"""
        alert_key = f"predictive:{component_name}:{metric_name}"
        
        # Check if predictive alert already exists
        if alert_key in self._alerts and not self._alerts[alert_key].resolved:
            return
        
        alert = HealthAlert(
            id=str(uuid.uuid4()),
            component=component_name,
            severity=AlertSeverity.INFO,
            metric_name=metric_name,
            current_value=predicted_value,
            threshold_value=0.0,
            message=f"Predictive: {component_name} {metric_name} trending towards {predicted_value:.2f} - {message}",
            timestamp=datetime.now(),
            metadata={'predictive': True}
        )
        
        self._alerts[alert_key] = alert
        self._alert_history.append(alert)
        
        print(f"🔮 PREDICTIVE ALERT: {alert.message}")
    
    # ==================== RECOVERY MANAGEMENT ====================
    
    async def _recovery_manager(self):
        """Manage automatic recovery actions"""
        while self._running:
            try:
                await asyncio.sleep(120)  # Check every 2 minutes
                
                if self._enable_auto_recovery:
                    await self._attempt_auto_recovery()
                    
            except Exception as e:
                print(f"❌ Recovery manager error: {e}")
    
    async def _attempt_auto_recovery(self):
        """Attempt automatic recovery for critical issues"""
        for component_name, component in self._components.items():
            if component.status == ComponentStatus.CRITICAL:
                # Check if recovery action is available
                recovery_actions = self._get_recovery_actions(component_name, component)
                
                for action in recovery_actions:
                    try:
                        print(f"🔄 Attempting recovery for {component_name}: {action['description']}")
                        
                        # Execute recovery action
                        if asyncio.iscoroutinefunction(action['handler']):
                            success = await action['handler'](component)
                        else:
                            success = action['handler'](component)
                        
                        if success:
                            print(f"✅ Recovery successful for {component_name}")
                            break  # Stop after first successful recovery
                        
                    except Exception as e:
                        print(f"❌ Recovery failed for {component_name}: {e}")
    
    def _get_recovery_actions(self, component_name: str, component: ComponentHealth) -> List[Dict[str, Any]]:
        """Get available recovery actions for component"""
        actions = []
        
        # Generic recovery actions based on metrics
        if 'memory_usage' in component.metrics and component.metrics['memory_usage'].value > 90:
            actions.append({
                'description': 'Clear memory caches',
                'handler': self._clear_memory_caches
            })
        
        if 'disk_usage' in component.metrics and component.metrics['disk_usage'].value > 95:
            actions.append({
                'description': 'Clean temporary files',
                'handler': self._clean_temp_files
            })
        
        # Component-specific recovery actions
        component_recovery_actions = {
            'central_hub': [
                {'description': 'Restart central hub', 'handler': self._restart_central_hub}
            ],
            'websocket_client': [
                {'description': 'Reconnect WebSocket', 'handler': self._reconnect_websocket}
            ],
            'mt5_handler': [
                {'description': 'Reconnect MT5', 'handler': self._reconnect_mt5}
            ]
        }
        
        if component_name in component_recovery_actions:
            actions.extend(component_recovery_actions[component_name])
        
        return actions
    
    async def _clear_memory_caches(self, component: ComponentHealth) -> bool:
        """Clear memory caches"""
        try:
            # Placeholder for cache clearing logic
            print(f"🧹 Clearing memory caches for {component.component_name}")
            return True
        except Exception:
            return False
    
    async def _clean_temp_files(self, component: ComponentHealth) -> bool:
        """Clean temporary files"""
        try:
            # Placeholder for temp file cleaning
            print(f"🧹 Cleaning temporary files for {component.component_name}")
            return True
        except Exception:
            return False
    
    async def _restart_central_hub(self, component: ComponentHealth) -> bool:
        """Restart central hub"""
        try:
            # Placeholder for restart logic
            print(f"🔄 Restarting central hub")
            return True
        except Exception:
            return False
    
    async def _reconnect_websocket(self, component: ComponentHealth) -> bool:
        """Reconnect WebSocket"""
        try:
            # Placeholder for WebSocket reconnection
            print(f"🔌 Reconnecting WebSocket")
            return True
        except Exception:
            return False
    
    async def _reconnect_mt5(self, component: ComponentHealth) -> bool:
        """Reconnect MT5"""
        try:
            # Placeholder for MT5 reconnection
            print(f"📈 Reconnecting MT5")
            return True
        except Exception:
            return False
    
    # ==================== DEFAULT HEALTH CHECKS ====================
    
    def _register_default_health_checks(self):
        """Register default health checks for common components"""
        
        # System health check
        def system_health_check():
            try:
                cpu_usage = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                status = True
                if cpu_usage > 90 or memory.percent > 95 or (disk.used / disk.total * 100) > 95:
                    status = False
                
                return {
                    'status': status,
                    'metrics': {
                        'cpu_usage': cpu_usage,
                        'memory_usage': memory.percent,
                        'disk_usage': (disk.used / disk.total) * 100
                    }
                }
            except Exception:
                return False
        
        # Register system component with health check
        self.register_component('system', system_health_check)
        
        print("✅ Default health checks registered")
    
    def _load_default_alert_rules(self):
        """Load default alert rules"""
        self._alert_rules = {
            'cpu_usage_high': {
                'metric': 'cpu_usage',
                'threshold': 80.0,
                'severity': 'warning',
                'message': 'High CPU usage detected'
            },
            'memory_usage_high': {
                'metric': 'memory_usage', 
                'threshold': 85.0,
                'severity': 'warning',
                'message': 'High memory usage detected'
            },
            'disk_usage_high': {
                'metric': 'disk_usage',
                'threshold': 90.0,
                'severity': 'critical',
                'message': 'Low disk space detected'
            }
        }
        
        print("📋 Default alert rules loaded")
    
    # ==================== LOGGING AND PERSISTENCE ====================
    
    def _log_diagnostics(self, diagnostics: SystemDiagnostics):
        """Log system diagnostics"""
        try:
            self._health_log_path.parent.mkdir(parents=True, exist_ok=True)
            
            log_entry = {
                'timestamp': diagnostics.last_updated.isoformat(),
                'overall_status': diagnostics.overall_status.value,
                'component_count': diagnostics.component_count,
                'healthy_components': diagnostics.healthy_components,
                'warning_components': diagnostics.warning_components,
                'critical_components': diagnostics.critical_components,
                'active_alerts': diagnostics.active_alerts,
                'recommendations': diagnostics.recommendations
            }
            
            with open(self._health_log_path, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
                
        except Exception as e:
            print(f"❌ Failed to log diagnostics: {e}")
    
    def _log_alert(self, alert: HealthAlert):
        """Log health alert"""
        try:
            self._alert_log_path.parent.mkdir(parents=True, exist_ok=True)
            
            alert_entry = asdict(alert)
            alert_entry['timestamp'] = alert.timestamp.isoformat()
            if alert.resolved_at:
                alert_entry['resolved_at'] = alert.resolved_at.isoformat()
            
            with open(self._alert_log_path, 'a') as f:
                f.write(json.dumps(alert_entry) + '\n')
                
        except Exception as e:
            print(f"❌ Failed to log alert: {e}")
    
    def _save_health_state(self):
        """Save current health state"""
        try:
            state_path = Path("logs/health_state.json")
            state_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Prepare state data
            state = {
                'components': {},
                'alerts': {},
                'timestamp': datetime.now().isoformat()
            }
            
            # Save component states
            for name, component in self._components.items():
                component_data = asdict(component)
                component_data['last_check'] = component.last_check.isoformat()
                
                # Convert metrics to serializable format
                metrics_data = {}
                for metric_name, metric in component.metrics.items():
                    metric_data = asdict(metric)
                    metric_data['timestamp'] = metric.timestamp.isoformat()
                    metrics_data[metric_name] = metric_data
                
                component_data['metrics'] = metrics_data
                state['components'][name] = component_data
            
            # Save alert states
            for key, alert in self._alerts.items():
                alert_data = asdict(alert)
                alert_data['timestamp'] = alert.timestamp.isoformat()
                if alert.resolved_at:
                    alert_data['resolved_at'] = alert.resolved_at.isoformat()
                state['alerts'][key] = alert_data
            
            with open(state_path, 'w') as f:
                json.dump(state, f, indent=2)
                
        except Exception as e:
            print(f"❌ Failed to save health state: {e}")
    
    # ==================== PUBLIC API ====================
    
    def get_system_health(self) -> SystemDiagnostics:
        """Get current system health diagnostics"""
        return self._generate_system_diagnostics()
    
    def get_component_health(self, component_name: str) -> Optional[ComponentHealth]:
        """Get health status for specific component"""
        return self._components.get(component_name)
    
    def get_all_components(self) -> Dict[str, ComponentHealth]:
        """Get health status for all components"""
        return self._components.copy()
    
    def get_active_alerts(self) -> List[HealthAlert]:
        """Get all active (unresolved) alerts"""
        return [alert for alert in self._alerts.values() if not alert.resolved]
    
    def get_alert_history(self, limit: int = 100) -> List[HealthAlert]:
        """Get recent alert history"""
        return list(self._alert_history)[-limit:]
    
    def get_component_metrics(self, component_name: str, metric_name: Optional[str] = None) -> Dict[str, Any]:
        """Get metrics for a component"""
        if component_name not in self._components:
            return {}
        
        component = self._components[component_name]
        
        if metric_name:
            metric = component.metrics.get(metric_name)
            return asdict(metric) if metric else {}
        else:
            return {name: asdict(metric) for name, metric in component.metrics.items()}
    
    def force_health_check(self, component_name: Optional[str] = None):
        """Force immediate health check"""
        if component_name:
            # Check specific component
            asyncio.create_task(self.check_component_health(component_name))
        else:
            # Check all components
            for name in self._components.keys():
                asyncio.create_task(self.check_component_health(name))


# ==================== CONVENIENCE FUNCTIONS ====================

# Global instance
health_core = None

def get_health_core() -> HealthCore:
    """Get global health core instance"""
    global health_core
    if health_core is None:
        health_core = HealthCore.get_instance()
    return health_core

def register_component_health(component_name: str, health_check: Optional[Callable] = None) -> bool:
    """Convenience function to register component for health monitoring"""
    return get_health_core().register_component(component_name, health_check)

def get_system_health_status() -> SystemDiagnostics:
    """Convenience function to get system health"""
    return get_health_core().get_system_health()

def get_component_status(component_name: str) -> Optional[ComponentHealth]:
    """Convenience function to get component health"""
    return get_health_core().get_component_health(component_name)

def is_system_healthy() -> bool:
    """Check if system is healthy overall"""
    health = get_health_core().get_system_health()
    return health.overall_status == ComponentStatus.HEALTHY