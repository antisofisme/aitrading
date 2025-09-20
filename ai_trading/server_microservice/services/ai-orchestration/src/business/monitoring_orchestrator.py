"""
Monitoring Orchestrator - Microservice Version with Per-Service Infrastructure
Central monitoring system for AI orchestration service with microservice infrastructure:
- Per-service monitoring and health checks
- Microservice-specific alerting and notifications
- Service-to-service monitoring coordination
- AI orchestration component monitoring
- Per-service performance analytics
"""

import asyncio
import time
import json
import uuid
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import threading
from concurrent.futures import ThreadPoolExecutor

# PER-SERVICE INFRASTRUCTURE INTEGRATION
from ....shared.infrastructure.base_error_handler import BaseErrorHandler, ErrorCategory
from ....shared.infrastructure.base_event_publisher import BaseEventPublisher
from ....shared.infrastructure.base_logger import BaseLogger
from ....shared.infrastructure.base.base_performance import BasePerformance
from ....shared.infrastructure.base_validator import BaseValidator
from ....shared.infrastructure.base_config import BaseConfig

# Initialize per-service infrastructure
error_handler = BaseErrorHandler("ai-orchestration")
event_publisher = BaseEventPublisher("ai-orchestration")
logger = BaseLogger("ai-orchestration", "monitoring_orchestrator")
performance_tracker = BasePerformance()
validator = BaseValidator("ai-orchestration")
config = BaseConfig("ai-orchestration")


@dataclass
class MonitoringState:
    """AI Orchestration service monitoring state"""
    health_monitor_status: str = "inactive"
    alerting_system_status: str = "inactive"
    performance_analytics_status: str = "inactive"
    service_monitor_status: str = "inactive"
    ai_orchestration_monitor_status: str = "inactive"
    overall_status: str = "inactive"
    started_at: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None
    error_count: int = 0
    warning_count: int = 0
    ai_coordinator_health: float = 1.0
    task_scheduler_health: float = 1.0
    handit_client_health: float = 1.0
    letta_integration_health: float = 1.0


@dataclass
class AIOrchestrationMetrics:
    """AI orchestration specific metrics"""
    active_ai_tasks: int = 0
    completed_ai_tasks: int = 0
    failed_ai_tasks: int = 0
    average_task_duration_ms: float = 0.0
    ai_coordinator_uptime: float = 100.0
    handit_api_response_time_ms: float = 0.0
    letta_integration_response_time_ms: float = 0.0
    scheduled_tasks_count: int = 0
    last_update: Optional[datetime] = None


class MonitoringOrchestrator:
    """
    AI Orchestration Monitoring Orchestrator
    Microservice monitoring control center for AI orchestration components
    """
    
    def __init__(self, monitoring_config: Optional[Dict[str, Any]] = None):
        self.monitoring_config = monitoring_config or {}
        self.is_running = False
        self.state = MonitoringState()
        self.metrics = AIOrchestrationMetrics()
        
        # Monitoring components
        self.health_checks: Dict[str, Callable] = {}
        self.performance_monitors: Dict[str, Any] = {}
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        
        # Orchestration components
        self.orchestration_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        # Integration settings
        self.auto_alert_on_health_issues = True
        self.auto_performance_analysis = True
        self.cross_component_monitoring = True
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        
        # Performance optimization
        self.component_health_cache: Dict[str, Dict[str, Any]] = {}
        self.last_cache_update = 0
        self.cache_ttl_seconds = 30
        
        # Monitoring intervals (in seconds)
        self.health_check_interval = 60
        self.performance_check_interval = 30
        self.alert_check_interval = 15
        
        logger.info("AI Orchestration Monitoring Orchestrator initialized")

    async def start_monitoring(self) -> bool:
        """Start the AI orchestration monitoring system"""
        start_time = time.time()
        
        try:
            if self.is_running:
                logger.warning("Monitoring system already running")
                return True
            
            logger.info("Starting AI orchestration monitoring system...")
            
            # Initialize monitoring components
            success_count = 0
            total_components = 5
            
            # Start health monitoring
            if await self._start_health_monitoring():
                self.state.health_monitor_status = "active"
                success_count += 1
                logger.info("✅ Health Monitor started")
            else:
                self.state.health_monitor_status = "failed"
                logger.error("❌ Health Monitor failed to start")
            
            # Start alerting system
            if await self._start_alerting_system():
                self.state.alerting_system_status = "active"
                success_count += 1
                logger.info("✅ Alerting System started")
            else:
                self.state.alerting_system_status = "failed"
                logger.error("❌ Alerting System failed to start")
            
            # Start performance analytics
            if await self._start_performance_analytics():
                self.state.performance_analytics_status = "active"
                success_count += 1
                logger.info("✅ Performance Analytics started")
            else:
                self.state.performance_analytics_status = "failed"
                logger.error("❌ Performance Analytics failed to start")
            
            # Start service monitor
            if await self._start_service_monitor():
                self.state.service_monitor_status = "active"
                success_count += 1
                logger.info("✅ Service Monitor started")
            else:
                self.state.service_monitor_status = "failed"
                logger.error("❌ Service Monitor failed to start")
            
            # Start AI orchestration specific monitoring
            if await self._start_ai_orchestration_monitoring():
                self.state.ai_orchestration_monitor_status = "active"
                success_count += 1
                logger.info("✅ AI Orchestration Monitor started")
            else:
                self.state.ai_orchestration_monitor_status = "failed"
                logger.error("❌ AI Orchestration Monitor failed to start")
            
            # Determine overall status
            if success_count == total_components:
                self.state.overall_status = "fully_active"
                self.is_running = True
            elif success_count > 0:
                self.state.overall_status = "partially_active"
                self.is_running = True
            else:
                self.state.overall_status = "failed"
                logger.error("❌ All monitoring components failed to start")
                return False
            
            # Set startup time
            self.state.started_at = datetime.now()
            self.state.last_heartbeat = datetime.now()
            
            # Start orchestration thread
            if self.is_running:
                self.orchestration_thread = threading.Thread(
                    target=self._orchestration_loop,
                    daemon=True
                )
                self.orchestration_thread.start()
                logger.info("🚀 Orchestration thread started")
            
            # Setup monitoring rules
            self._setup_monitoring_rules()
            
            # Record performance
            startup_time = (time.time() - start_time) * 1000
            performance_tracker.record_operation(
                operation_name="monitoring_system_startup",
                duration_ms=startup_time,
                success=True,
                metadata={
                    "components_started": success_count,
                    "total_components": total_components
                }
            )
            
            # Publish event
            event_publisher.publish_event(
                event_type="monitoring_system_started",
                data={
                    "startup_time_ms": startup_time,
                    "components_started": success_count,
                    "overall_status": self.state.overall_status,
                    "timestamp": datetime.now().isoformat()
                },
                context="monitoring_orchestrator"
            )
            
            logger.info(f"🎯 AI Orchestration monitoring started successfully ({success_count}/{total_components} components active)")
            return True
            
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                error_category=ErrorCategory.SYSTEM_ERROR,
                context={
                    "component": "monitoring_orchestrator",
                    "operation": "start_monitoring"
                }
            )
            logger.error(f"❌ Failed to start monitoring system: {error_response}")
            self.state.overall_status = "failed"
            return False

    async def stop_monitoring(self) -> bool:
        """Stop the AI orchestration monitoring system"""
        start_time = time.time()
        
        try:
            if not self.is_running:
                logger.warning("Monitoring system not running")
                return True
            
            logger.info("Stopping AI orchestration monitoring system...")
            self.is_running = False
            
            # Stop orchestration thread
            if self.orchestration_thread and self.orchestration_thread.is_alive():
                self.orchestration_thread.join(timeout=5)
            
            # Stop all monitoring components
            stop_results = []
            
            # Stop components
            components = [
                ("Health Monitor", self._stop_health_monitoring),
                ("Alerting System", self._stop_alerting_system),
                ("Performance Analytics", self._stop_performance_analytics),
                ("Service Monitor", self._stop_service_monitor),
                ("AI Orchestration Monitor", self._stop_ai_orchestration_monitoring)
            ]
            
            for component_name, stop_func in components:
                try:
                    result = await stop_func()
                    stop_results.append((component_name, result))
                except Exception as e:
                    logger.error(f"Error stopping {component_name}: {e}")
                    stop_results.append((component_name, False))
            
            # Shutdown executor
            self.executor.shutdown(wait=True)
            
            # Update state
            self.state.overall_status = "inactive"
            self.state.health_monitor_status = "inactive"
            self.state.alerting_system_status = "inactive"
            self.state.performance_analytics_status = "inactive"
            self.state.service_monitor_status = "inactive"
            self.state.ai_orchestration_monitor_status = "inactive"
            
            # Record performance
            shutdown_time = (time.time() - start_time) * 1000
            performance_tracker.record_operation(
                operation_name="monitoring_system_shutdown",
                duration_ms=shutdown_time,
                success=True,
                metadata={
                    "components_stopped": len([r for _, r in stop_results if r])
                }
            )
            
            # Log results
            successful_stops = sum(1 for _, success in stop_results if success)
            logger.info(f"🛑 AI Orchestration monitoring stopped ({successful_stops}/{len(stop_results)} components stopped cleanly)")
            
            return all(success for _, success in stop_results)
            
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                error_category=ErrorCategory.SYSTEM_ERROR,
                context={
                    "component": "monitoring_orchestrator",
                    "operation": "stop_monitoring"
                }
            )
            logger.error(f"❌ Error stopping monitoring system: {error_response}")
            return False

    def _orchestration_loop(self):
        """Main orchestration loop for AI orchestration monitoring"""
        while self.is_running:
            try:
                # Update heartbeat
                self.state.last_heartbeat = datetime.now()
                
                # Perform monitoring tasks
                self._perform_health_checks()
                self._perform_performance_checks()
                self._perform_alert_checks()
                self._monitor_ai_orchestration_components()
                
                # Update metrics and cache
                self._update_metrics()
                self._update_component_health_cache()
                
                # Trigger heartbeat events
                self._trigger_heartbeat_events()
                
                # Sleep until next cycle
                time.sleep(self.health_check_interval)
                
            except Exception as e:
                error_response = error_handler.handle_error(
                    error=e,
                    error_category=ErrorCategory.SYSTEM_ERROR,
                    context={
                        "component": "monitoring_orchestrator",
                        "operation": "orchestration_loop"
                    }
                )
                logger.error(f"Error in orchestration loop: {error_response}")
                self.state.error_count += 1
                time.sleep(10)

    async def _start_health_monitoring(self) -> bool:
        """Start health monitoring for AI orchestration service"""
        try:
            # Setup health checks for AI orchestration components
            self.health_checks = {
                "ai_coordinator": self._check_ai_coordinator_health,
                "task_scheduler": self._check_task_scheduler_health,
                "handit_client": self._check_handit_client_health,
                "letta_integration": self._check_letta_integration_health,
                "service_connectivity": self._check_service_connectivity_health
            }
            
            logger.debug("Health monitoring initialized with AI orchestration checks")
            return True
            
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                error_category=ErrorCategory.CONFIGURATION_ERROR,
                context={
                    "component": "health_monitoring",
                    "operation": "start_health_monitoring"
                }
            )
            logger.error(f"Failed to start health monitoring: {error_response}")
            return False

    async def _start_alerting_system(self) -> bool:
        """Start alerting system for AI orchestration service"""
        try:
            # Setup alert rules for AI orchestration
            self.alert_rules = {
                "ai_coordinator_failure": {
                    "threshold": 0.5,
                    "severity": "critical",
                    "description": "AI Coordinator health below threshold"
                },
                "task_scheduler_failure": {
                    "threshold": 0.5,
                    "severity": "critical",
                    "description": "Task Scheduler health below threshold"
                },
                "handit_api_failure": {
                    "threshold": 0.3,
                    "severity": "high",
                    "description": "Handit API response issues"
                },
                "letta_integration_failure": {
                    "threshold": 0.3,
                    "severity": "high",
                    "description": "Letta integration connectivity issues"
                },
                "high_error_rate": {
                    "threshold": 10,
                    "severity": "medium",
                    "description": "High error rate in AI orchestration"
                }
            }
            
            logger.debug("Alerting system initialized with AI orchestration rules")
            return True
            
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                error_category=ErrorCategory.CONFIGURATION_ERROR,
                context={
                    "component": "alerting_system",
                    "operation": "start_alerting_system"
                }
            )
            logger.error(f"Failed to start alerting system: {error_response}")
            return False

    async def _start_performance_analytics(self) -> bool:
        """Start performance analytics for AI orchestration service"""
        try:
            # Setup performance monitors
            self.performance_monitors = {
                "ai_task_duration": {"metric_type": "duration", "unit": "ms"},
                "api_response_times": {"metric_type": "duration", "unit": "ms"},
                "memory_usage": {"metric_type": "gauge", "unit": "bytes"},
                "cpu_usage": {"metric_type": "gauge", "unit": "percent"},
                "active_connections": {"metric_type": "gauge", "unit": "count"}
            }
            
            logger.debug("Performance analytics initialized for AI orchestration")
            return True
            
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                error_category=ErrorCategory.CONFIGURATION_ERROR,
                context={
                    "component": "performance_analytics",
                    "operation": "start_performance_analytics"
                }
            )
            logger.error(f"Failed to start performance analytics: {error_response}")
            return False

    async def _start_service_monitor(self) -> bool:
        """Start service monitor for external dependencies"""
        try:
            # Monitor external services that AI orchestration depends on
            logger.debug("Service monitor initialized for external dependencies")
            return True
            
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                error_category=ErrorCategory.CONFIGURATION_ERROR,
                context={
                    "component": "service_monitor",
                    "operation": "start_service_monitor"
                }
            )
            logger.error(f"Failed to start service monitor: {error_response}")
            return False

    async def _start_ai_orchestration_monitoring(self) -> bool:
        """Start AI orchestration specific monitoring"""
        try:
            # Initialize AI orchestration metrics
            self.metrics = AIOrchestrationMetrics()
            self.metrics.last_update = datetime.now()
            
            logger.debug("AI orchestration specific monitoring initialized")
            return True
            
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                error_category=ErrorCategory.CONFIGURATION_ERROR,
                context={
                    "component": "ai_orchestration_monitoring",
                    "operation": "start_ai_orchestration_monitoring"
                }
            )
            logger.error(f"Failed to start AI orchestration monitoring: {error_response}")
            return False

    # Stop methods
    async def _stop_health_monitoring(self) -> bool:
        """Stop health monitoring"""
        try:
            self.health_checks.clear()
            return True
        except Exception as e:
            logger.error(f"Error stopping health monitoring: {e}")
            return False

    async def _stop_alerting_system(self) -> bool:
        """Stop alerting system"""
        try:
            self.alert_rules.clear()
            return True
        except Exception as e:
            logger.error(f"Error stopping alerting system: {e}")
            return False

    async def _stop_performance_analytics(self) -> bool:
        """Stop performance analytics"""
        try:
            self.performance_monitors.clear()
            return True
        except Exception as e:
            logger.error(f"Error stopping performance analytics: {e}")
            return False

    async def _stop_service_monitor(self) -> bool:
        """Stop service monitor"""
        try:
            return True
        except Exception as e:
            logger.error(f"Error stopping service monitor: {e}")
            return False

    async def _stop_ai_orchestration_monitoring(self) -> bool:
        """Stop AI orchestration monitoring"""
        try:
            return True
        except Exception as e:
            logger.error(f"Error stopping AI orchestration monitoring: {e}")
            return False

    # Health check methods
    async def _check_ai_coordinator_health(self) -> float:
        """Check AI coordinator health"""
        try:
            # This would implement actual health checks for AI coordinator
            # For now, return a simple health score
            return 1.0
        except Exception as e:
            logger.error(f"Error checking AI coordinator health: {e}")
            return 0.0

    async def _check_task_scheduler_health(self) -> float:
        """Check task scheduler health"""
        try:
            # This would implement actual health checks for task scheduler
            # For now, return a simple health score
            return 1.0
        except Exception as e:
            logger.error(f"Error checking task scheduler health: {e}")
            return 0.0

    async def _check_handit_client_health(self) -> float:
        """Check Handit client health"""
        try:
            # This would implement actual health checks for Handit API
            # For now, return a simple health score
            return 1.0
        except Exception as e:
            logger.error(f"Error checking Handit client health: {e}")
            return 0.0

    async def _check_letta_integration_health(self) -> float:
        """Check Letta integration health"""
        try:
            # This would implement actual health checks for Letta integration
            # For now, return a simple health score
            return 1.0
        except Exception as e:
            logger.error(f"Error checking Letta integration health: {e}")
            return 0.0

    async def _check_service_connectivity_health(self) -> float:
        """Check service connectivity health"""
        try:
            # This would implement actual connectivity checks
            # For now, return a simple health score
            return 1.0
        except Exception as e:
            logger.error(f"Error checking service connectivity health: {e}")
            return 0.0

    def _perform_health_checks(self):
        """Perform all health checks"""
        try:
            for check_name, check_func in self.health_checks.items():
                try:
                    health_score = asyncio.run(check_func())
                    
                    # Update state based on check
                    if check_name == "ai_coordinator":
                        self.state.ai_coordinator_health = health_score
                    elif check_name == "task_scheduler":
                        self.state.task_scheduler_health = health_score
                    elif check_name == "handit_client":
                        self.state.handit_client_health = health_score
                    elif check_name == "letta_integration":
                        self.state.letta_integration_health = health_score
                    
                    # Check for alerts
                    if health_score < 0.5:
                        self._trigger_health_alert(check_name, health_score)
                        
                except Exception as e:
                    logger.error(f"Error in health check {check_name}: {e}")
                    self.state.error_count += 1
                    
        except Exception as e:
            logger.error(f"Error performing health checks: {e}")

    def _perform_performance_checks(self):
        """Perform performance monitoring checks"""
        try:
            # Record current performance metrics
            current_time = datetime.now()
            
            # Update AI orchestration metrics
            self.metrics.last_update = current_time
            
            # This would implement actual performance monitoring
            logger.debug("Performance checks completed")
            
        except Exception as e:
            logger.error(f"Error performing performance checks: {e}")

    def _perform_alert_checks(self):
        """Perform alert rule evaluations"""
        try:
            # Check alert rules
            for rule_name, rule_config in self.alert_rules.items():
                try:
                    should_alert = self._evaluate_alert_rule(rule_name, rule_config)
                    if should_alert:
                        self._trigger_alert(rule_name, rule_config)
                except Exception as e:
                    logger.error(f"Error evaluating alert rule {rule_name}: {e}")
                    
        except Exception as e:
            logger.error(f"Error performing alert checks: {e}")

    def _monitor_ai_orchestration_components(self):
        """Monitor AI orchestration specific components"""
        try:
            # This would implement AI orchestration specific monitoring
            logger.debug("AI orchestration component monitoring completed")
            
        except Exception as e:
            logger.error(f"Error monitoring AI orchestration components: {e}")

    def _evaluate_alert_rule(self, rule_name: str, rule_config: Dict[str, Any]) -> bool:
        """Evaluate if an alert rule should trigger"""
        try:
            # This would implement actual alert rule evaluation logic
            return False
        except Exception as e:
            logger.error(f"Error evaluating alert rule {rule_name}: {e}")
            return False

    def _trigger_health_alert(self, check_name: str, health_score: float):
        """Trigger health-related alert"""
        try:
            alert_data = {
                "alert_type": "health_check",
                "check_name": check_name,
                "health_score": health_score,
                "severity": "critical" if health_score < 0.3 else "high",
                "timestamp": datetime.now().isoformat()
            }
            
            event_publisher.publish_event(
                event_type="health_alert_triggered",
                data=alert_data,
                context="monitoring_orchestrator"
            )
            
            logger.warning(f"Health alert triggered for {check_name}: score={health_score}")
            
        except Exception as e:
            logger.error(f"Error triggering health alert: {e}")

    def _trigger_alert(self, rule_name: str, rule_config: Dict[str, Any]):
        """Trigger general alert"""
        try:
            alert_data = {
                "alert_type": "rule_based",
                "rule_name": rule_name,
                "severity": rule_config.get("severity", "medium"),
                "description": rule_config.get("description", "Alert triggered"),
                "timestamp": datetime.now().isoformat()
            }
            
            event_publisher.publish_event(
                event_type="alert_triggered",
                data=alert_data,
                context="monitoring_orchestrator"
            )
            
            logger.warning(f"Alert triggered: {rule_name}")
            
        except Exception as e:
            logger.error(f"Error triggering alert: {e}")

    def _setup_monitoring_rules(self):
        """Setup monitoring rules and thresholds"""
        try:
            # This would setup specific monitoring rules for AI orchestration
            logger.debug("Monitoring rules setup completed")
            
        except Exception as e:
            logger.error(f"Error setting up monitoring rules: {e}")

    def _update_metrics(self):
        """Update AI orchestration metrics"""
        try:
            self.metrics.last_update = datetime.now()
            
            # This would implement actual metrics collection and updates
            logger.debug("Metrics updated")
            
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")

    def _update_component_health_cache(self):
        """Update component health cache"""
        try:
            current_time = time.time()
            
            if current_time - self.last_cache_update > self.cache_ttl_seconds:
                self.component_health_cache = {
                    "ai_coordinator": {"health": self.state.ai_coordinator_health},
                    "task_scheduler": {"health": self.state.task_scheduler_health},
                    "handit_client": {"health": self.state.handit_client_health},
                    "letta_integration": {"health": self.state.letta_integration_health},
                    "system_status": {
                        "overall_status": self.state.overall_status,
                        "error_count": self.state.error_count,
                        "warning_count": self.state.warning_count
                    }
                }
                
                self.last_cache_update = current_time
                
        except Exception as e:
            logger.error(f"Error updating component health cache: {e}")

    def _trigger_heartbeat_events(self):
        """Trigger heartbeat events"""
        try:
            event_publisher.publish_event(
                event_type="monitoring_heartbeat",
                data={
                    "timestamp": datetime.now().isoformat(),
                    "state": {
                        "overall_status": self.state.overall_status,
                        "components_status": {
                            "health_monitor": self.state.health_monitor_status,
                            "alerting_system": self.state.alerting_system_status,
                            "performance_analytics": self.state.performance_analytics_status,
                            "service_monitor": self.state.service_monitor_status,
                            "ai_orchestration_monitor": self.state.ai_orchestration_monitor_status
                        }
                    },
                    "metrics": {
                        "active_ai_tasks": self.metrics.active_ai_tasks,
                        "completed_ai_tasks": self.metrics.completed_ai_tasks,
                        "failed_ai_tasks": self.metrics.failed_ai_tasks,
                        "scheduled_tasks_count": self.metrics.scheduled_tasks_count
                    }
                },
                context="monitoring_orchestrator"
            )
            
        except Exception as e:
            logger.error(f"Error triggering heartbeat events: {e}")

    # Public API methods
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get comprehensive monitoring system status for AI orchestration"""
        try:
            return {
                "service": "ai-orchestration",
                "overall_status": self.state.overall_status,
                "is_running": self.is_running,
                "started_at": self.state.started_at.isoformat() if self.state.started_at else None,
                "last_heartbeat": self.state.last_heartbeat.isoformat() if self.state.last_heartbeat else None,
                "uptime_seconds": (datetime.now() - self.state.started_at).total_seconds() if self.state.started_at else 0,
                "component_status": {
                    "health_monitor": self.state.health_monitor_status,
                    "alerting_system": self.state.alerting_system_status,
                    "performance_analytics": self.state.performance_analytics_status,
                    "service_monitor": self.state.service_monitor_status,
                    "ai_orchestration_monitor": self.state.ai_orchestration_monitor_status
                },
                "ai_orchestration_health": {
                    "ai_coordinator": self.state.ai_coordinator_health,
                    "task_scheduler": self.state.task_scheduler_health,
                    "handit_client": self.state.handit_client_health,
                    "letta_integration": self.state.letta_integration_health
                },
                "error_count": self.state.error_count,
                "warning_count": self.state.warning_count,
                "metrics": {
                    "active_ai_tasks": self.metrics.active_ai_tasks,
                    "completed_ai_tasks": self.metrics.completed_ai_tasks,
                    "failed_ai_tasks": self.metrics.failed_ai_tasks,
                    "scheduled_tasks_count": self.metrics.scheduled_tasks_count,
                    "last_update": self.metrics.last_update.isoformat() if self.metrics.last_update else None
                }
            }
            
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                error_category=ErrorCategory.SYSTEM_ERROR,
                context={
                    "component": "monitoring_orchestrator",
                    "operation": "get_monitoring_status"
                }
            )
            logger.error(f"Error getting monitoring status: {error_response}")
            return {"error": str(e)}

    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary for AI orchestration service"""
        try:
            overall_health = (
                self.state.ai_coordinator_health +
                self.state.task_scheduler_health +
                self.state.handit_client_health +
                self.state.letta_integration_health
            ) / 4.0
            
            return {
                "service": "ai-orchestration",
                "overall_health_score": overall_health,
                "component_health": {
                    "ai_coordinator": self.state.ai_coordinator_health,
                    "task_scheduler": self.state.task_scheduler_health,
                    "handit_client": self.state.handit_client_health,
                    "letta_integration": self.state.letta_integration_health
                },
                "health_status": "healthy" if overall_health > 0.8 else "degraded" if overall_health > 0.5 else "unhealthy",
                "active_issues": self.state.error_count + self.state.warning_count,
                "last_check": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting health summary: {e}")
            return {"error": str(e)}

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for AI orchestration service"""
        try:
            return {
                "service": "ai-orchestration",
                "ai_task_metrics": {
                    "active_tasks": self.metrics.active_ai_tasks,
                    "completed_tasks": self.metrics.completed_ai_tasks,
                    "failed_tasks": self.metrics.failed_ai_tasks,
                    "average_duration_ms": self.metrics.average_task_duration_ms,
                    "success_rate": (
                        self.metrics.completed_ai_tasks / 
                        max(1, self.metrics.completed_ai_tasks + self.metrics.failed_ai_tasks)
                    ) * 100
                },
                "api_response_times": {
                    "handit_api_ms": self.metrics.handit_api_response_time_ms,
                    "letta_integration_ms": self.metrics.letta_integration_response_time_ms
                },
                "scheduler_metrics": {
                    "scheduled_tasks": self.metrics.scheduled_tasks_count
                },
                "uptime_metrics": {
                    "ai_coordinator_uptime": self.metrics.ai_coordinator_uptime
                },
                "last_update": self.metrics.last_update.isoformat() if self.metrics.last_update else None
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {"error": str(e)}

    async def force_health_check(self) -> Dict[str, Any]:
        """Force immediate health check of all components"""
        try:
            logger.info("Force health check requested")
            
            results = {}
            for check_name, check_func in self.health_checks.items():
                try:
                    health_score = await check_func()
                    results[check_name] = {"health_score": health_score, "status": "completed"}
                except Exception as e:
                    results[check_name] = {"error": str(e), "status": "failed"}
            
            # Update state
            self._perform_health_checks()
            
            # Publish event
            event_publisher.publish_event(
                event_type="force_health_check_completed",
                data={
                    "results": results,
                    "timestamp": datetime.now().isoformat()
                },
                context="monitoring_orchestrator"
            )
            
            logger.info("Force health check completed")
            return results
            
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                error_category=ErrorCategory.SYSTEM_ERROR,
                context={
                    "component": "monitoring_orchestrator",
                    "operation": "force_health_check"
                }
            )
            logger.error(f"Force health check failed: {error_response}")
            return {"error": str(e)}