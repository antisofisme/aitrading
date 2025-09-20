"""
🏗️ Base Microservice - CENTRALIZED INFRASTRUCTURE FOUNDATION
Enterprise-grade base class for all AI Orchestration microservice components

CENTRALIZED INFRASTRUCTURE:
- Standardized configuration management
- Centralized logging with service context
- Performance tracking with metrics collection
- Error handling with classification and recovery
- Event publishing with standardized patterns
- Health monitoring with comprehensive checks
"""

import os
import sys
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

# SERVICE-SPECIFIC INFRASTRUCTURE - MICROSERVICE COMPLIANCE
# Each microservice uses its OWN infrastructure components - NO external dependencies

from ...shared.infrastructure.core.logger_core import CoreLogger
from ...shared.infrastructure.core.error_core import CoreErrorHandler
from ...shared.infrastructure.core.performance_core import CorePerformance
from ...shared.infrastructure.core.config_core import CoreConfig
from ...shared.infrastructure.optional.event_core import CoreEventManager
from ...shared.infrastructure.optional.validation_core import SharedInfraValidationManager


class AIOrchestrationBaseMicroservice(ABC):
    """
    🏗️ Base Microservice Class for AI Orchestration Components
    
    Enterprise-grade foundation providing:
    - Centralized configuration management
    - Standardized logging with service context
    - Performance tracking and metrics collection
    - Error handling with classification
    - Event publishing with patterns
    - Health monitoring and checks
    """
    
    def __init__(self, service_name: str, component_name: str):
        """Initialize base microservice with centralized infrastructure"""
        try:
            # Core service identification
            self.service_name = service_name
            self.component_name = component_name
            self.microservice_id = f"{service_name}_{component_name}"
            
            # Initialize centralized infrastructure
            self._setup_centralized_logging()
            self._setup_centralized_configuration()
            self._setup_centralized_metrics()
            self._setup_centralized_health_monitoring()
            
            # Publish initialization event
            self._publish_initialization_event()
            
            self.logger.info(f"✅ {self.microservice_id} base microservice initialized with centralized infrastructure")
            
        except Exception as e:
            error_handler = CoreErrorHandler(service_name)
            error_response = error_handler.handle_service_error(
                error=e,
                operation="initialize_base_microservice",
                context={"service_name": service_name, "component_name": component_name}
            )
            raise RuntimeError(f"Failed to initialize base microservice: {error_response}")
    
    def _setup_centralized_logging(self):
        """Setup service-specific logging with service context"""
        self.logger = CoreLogger(f"{self.microservice_id}_microservice", f"{self.service_name}_{self.component_name}")
    
    def _setup_centralized_configuration(self):
        """Setup centralized configuration management"""
        try:
            # Load service-specific configuration through CoreConfig
            self.config_manager = CoreConfig(self.service_name)
            self.config = self.config_manager.get_service_config(self._get_default_config())
            
            # Load environment-specific settings
            self.environment = self.config.get("environment", "development")
            self.debug_mode = self.config.get("debug", False)
            self.enabled = self.config.get("enabled", True)
            
        except Exception as e:
            self.logger.error(f"Failed to setup service configuration: {str(e)}")
            # Fallback to default configuration
            self.config = self._get_default_config()
            self.environment = "development"
            self.debug_mode = False
            self.enabled = True
    
    def _setup_centralized_metrics(self):
        """Setup centralized metrics collection"""
        self.metrics = {
            "startup_time": time.time(),
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "health_checks": 0,
            "events_published": 0,
            "errors_handled": 0,
            "uptime_seconds": 0,
            "last_activity": time.time()
        }
        
        # Register metrics with service performance tracker
        self.performance_tracker = CorePerformance(self.service_name)
        self.performance_tracker.record_metric_batch = getattr(
            self.performance_tracker, 'record_metric_batch', lambda **kwargs: None
        )
    
    def _setup_centralized_health_monitoring(self):
        """Setup centralized health monitoring"""
        self.health_status = {
            "status": "healthy",
            "service": self.microservice_id,
            "component": self.component_name,
            "initialized": True,
            "last_check": datetime.now().isoformat()
        }
    
    def _publish_initialization_event(self):
        """Publish standardized initialization event"""
        try:
            self.event_manager = CoreEventManager(self.service_name)
            self.event_manager.publish_service_event(
                event_type=f"{self.microservice_id}_initialized",
                message=f"{self.microservice_id} microservice initialized with service infrastructure",
                data={
                    "service_name": self.service_name,
                    "component_name": self.component_name,
                    "microservice_id": self.microservice_id,
                    "environment": self.environment,
                    "enabled": self.enabled,
                    "initialization_timestamp": time.time(),
                    "service_infrastructure": True
                },
                priority="high"
            )
            self.metrics["events_published"] += 1
            
        except Exception as e:
            self.logger.error(f"Failed to publish initialization event: {str(e)}")
    
    @abstractmethod
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for the specific microservice component"""
        pass
    
    @abstractmethod
    def _perform_health_checks(self) -> Dict[str, Any]:
        """Perform component-specific health checks"""
        pass
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status with centralized patterns"""
        try:
            # Update uptime
            uptime = time.time() - self.metrics["startup_time"]
            self.metrics["uptime_seconds"] = uptime
            self.metrics["health_checks"] += 1
            
            # Perform component-specific health checks
            component_health = self._perform_health_checks()
            
            # Create standardized health response
            health_data = {
                "status": "healthy" if component_health.get("healthy", True) else "unhealthy",
                "service": self.microservice_id,
                "component": self.component_name,
                "uptime_seconds": uptime,
                "environment": self.environment,
                "enabled": self.enabled,
                "metrics": self.metrics.copy(),
                "component_health": component_health,
                "configuration": {
                    "debug_mode": self.debug_mode,
                    "environment": self.environment,
                    "enabled": self.enabled
                },
                "timestamp": datetime.now().isoformat(),
                "centralized_infrastructure": True
            }
            
            # Update last check time
            self.health_status["last_check"] = datetime.now().isoformat()
            
            return health_data
            
        except Exception as e:
            self.error_handler = CoreErrorHandler(self.service_name)
            error_response = self.error_handler.handle_service_error(
                error=e,
                operation="health_check",
                context={"service_name": self.service_name, "component": self.component_name}
            )
            self.logger.error(f"Health check failed: {error_response}")
            
            return {
                "status": "error",
                "service": self.microservice_id,
                "component": self.component_name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def track_operation(self, operation_name: str, success: bool = True, metadata: Optional[Dict[str, Any]] = None):
        """Track operations with centralized performance management"""
        try:
            # Update metrics
            self.metrics["total_operations"] += 1
            if success:
                self.metrics["successful_operations"] += 1
            else:
                self.metrics["failed_operations"] += 1
            
            self.metrics["last_activity"] = time.time()
            
            # Record with service performance tracker (simplified)
            if hasattr(self.performance_tracker, 'record_metric'):
                from ...shared.infrastructure.base.base_performance import PerformanceMetric
                from datetime import datetime
                metric = PerformanceMetric(
                    operation_name=f"{self.microservice_id}_{operation_name}",
                    duration=0.0,  # Will be calculated by performance_tracked decorator
                    timestamp=datetime.now(),
                    metadata={
                        "service_name": self.service_name,
                        "component_name": self.component_name,
                        "microservice_id": self.microservice_id,
                        "success": success,
                        **(metadata or {})
                    }
                )
                self.performance_tracker.record_metric(metric)
            
        except Exception as e:
            self.logger.error(f"Failed to track operation {operation_name}: {str(e)}")
    
    def handle_error(self, error: Exception, operation: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle errors with centralized error management"""
        try:
            self.metrics["errors_handled"] += 1
            self.metrics["failed_operations"] += 1
            
            if not hasattr(self, 'error_handler'):
                self.error_handler = CoreErrorHandler(self.service_name)
            
            error_response = self.error_handler.handle_service_error(
                error=error,
                operation=operation,
                context={
                    "service_name": self.service_name,
                    "component_name": self.component_name,
                    "microservice_id": self.microservice_id,
                    **(context or {})
                }
            )
            
            self.logger.error(f"Error in {operation}: {error_response}")
            return error_response
            
        except Exception as e:
            self.logger.critical(f"Critical error in service error handling: {str(e)}")
            return {"error": "Critical service error handling failure", "details": str(e)}
    
    def publish_event(self, event_type: str, message: str, data: Optional[Dict[str, Any]] = None):
        """Publish events with centralized patterns"""
        try:
            if not hasattr(self, 'event_manager'):
                self.event_manager = CoreEventManager(self.service_name)
            
            self.event_manager.publish_service_event(
                event_type=f"{self.microservice_id}_{event_type}",
                message=f"[{self.microservice_id}] {message}",
                data={
                    "service_name": self.service_name,
                    "component_name": self.component_name,
                    "microservice_id": self.microservice_id,
                    "environment": self.environment,
                    "timestamp": time.time(),
                    **(data or {})
                },
                priority="normal"
            )
            self.metrics["events_published"] += 1
            
        except Exception as e:
            self.logger.error(f"Failed to publish service event {event_type}: {str(e)}")
    
    def validate_data(self, data: Dict[str, Any], required_fields: List[str]) -> bool:
        """Validate data with service validation"""
        try:
            if not hasattr(self, 'validator'):
                self.validator = SharedInfraValidationManager(self.service_name)
            
            # Simple validation - check required fields exist and are not None
            return all(field in data and data[field] is not None for field in required_fields)
                
        except Exception as e:
            self.logger.error(f"Service validation failed: {str(e)}")
            return False


class AIOrchestrationMicroserviceFactory:
    """Factory for creating AI Orchestration microservice instances with centralized infrastructure"""
    
    @staticmethod
    def create_microservice(component_type: str, service_name: str = "ai-orchestration") -> AIOrchestrationBaseMicroservice:
        """Create microservice instance with proper centralization"""
        
        # Import specific microservice implementations
        if component_type == "handit_client":
            from .handit_client import AIOrchestrationHanditClient
            return AIOrchestrationHanditClient()
        elif component_type == "langfuse_observability":
            from .langfuse_client import AIOrchestrationLangfuseObservability
            return AIOrchestrationLangfuseObservability()
        elif component_type == "langgraph_workflows":
            from .langgraph_workflows import AIOrchestrationLangGraphWorkflows
            return AIOrchestrationLangGraphWorkflows()
        elif component_type == "letta_memory":
            from .letta_integration import AIOrchestrationLettaMemory
            return AIOrchestrationLettaMemory()
        elif component_type == "agent_coordinator":
            from .agent_coordinator import AIOrchestrationAgentCoordinator
            return AIOrchestrationAgentCoordinator()
        else:
            raise ValueError(f"Unknown microservice component type: {component_type}")