"""
Coordination Manager
Handles all service coordination, registry, routing, and workflow orchestration
"""

import logging
from typing import Optional, Dict, Any
from pathlib import Path
import sys

# Add shared to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

# Core coordination modules
from core.service_registry import ServiceRegistry
from core.coordination_router import CoordinationRouter

# ConfigManager moved to shared patterns after refactoring
from components.utils.patterns.config import ConfigManager

# Implementation modules
from impl.coordination.service_coordinator import ServiceCoordinator
from impl.workflow.workflow_engine import WorkflowEngine
from impl.scheduling.task_scheduler import TaskScheduler

logger = logging.getLogger("central-hub.coordination-manager")


class CoordinationManager:
    """
    Manages all service coordination and orchestration for Central Hub

    Responsibilities:
    - Service registry management
    - Service coordination and routing
    - Workflow orchestration
    - Task scheduling
    - Configuration management
    """

    def __init__(self, service_name: str, db_manager):
        self.service_name = service_name
        self.db_manager = db_manager

        # Core coordination components
        self.service_registry: Optional[ServiceRegistry] = None
        self.config_manager: Optional[ConfigManager] = None
        self.coordination_router: Optional[CoordinationRouter] = None

        # Implementation components
        self.service_coordinator: Optional[ServiceCoordinator] = None
        self.workflow_engine: Optional[WorkflowEngine] = None
        self.task_scheduler: Optional[TaskScheduler] = None

    async def initialize(self):
        """Initialize all coordination components"""
        try:
            logger.info("🎯 Initializing Coordination Manager...")

            # 1. Initialize service registry
            self.service_registry = ServiceRegistry()
            logger.info("✅ Service registry initialized")

            # 2. Initialize configuration manager
            self.config_manager = ConfigManager(service_name=self.service_name)
            logger.info("✅ Configuration manager initialized")

            # 3. Initialize coordination router
            self.coordination_router = CoordinationRouter()
            logger.info("✅ Coordination router initialized")

            # 4. Initialize service coordinator
            self.service_coordinator = ServiceCoordinator(
                service_registry=self.service_registry.get_registry(),
                db_manager=self.db_manager
            )
            logger.info("✅ Service coordinator initialized")

            # 5. Initialize workflow engine
            self.workflow_engine = WorkflowEngine(
                service_registry=self.service_registry.get_registry()
            )
            logger.info("✅ Workflow engine initialized")

            # 6. Initialize task scheduler
            self.task_scheduler = TaskScheduler(
                service_registry=self.service_registry.get_registry()
            )
            logger.info("✅ Task scheduler initialized")

            logger.info("✅ Coordination Manager initialized")

        except Exception as e:
            logger.error(f"❌ Coordination Manager initialization failed: {str(e)}")
            raise

    async def start_services(self):
        """Start background coordination services"""
        try:
            logger.info("▶️ Starting coordination services...")

            # Start task scheduler
            if self.task_scheduler:
                await self.task_scheduler.start_scheduler()
                logger.info("✅ Task scheduler started")

            logger.info("✅ Coordination services started")

        except Exception as e:
            logger.error(f"❌ Failed to start coordination services: {str(e)}")

    async def stop_services(self):
        """Stop background coordination services"""
        try:
            logger.info("🛑 Stopping coordination services...")

            # Stop task scheduler
            if self.task_scheduler:
                await self.task_scheduler.stop_scheduler()
                logger.info("✅ Task scheduler stopped")

            logger.info("✅ Coordination services stopped")

        except Exception as e:
            logger.error(f"❌ Failed to stop coordination services: {str(e)}")

    async def health_check(self):
        """Check health of all coordination components"""
        health = {
            "service_registry": "unknown",
            "config_manager": "unknown",
            "coordination_router": "unknown",
            "service_coordinator": "unknown",
            "workflow_engine": "unknown",
            "task_scheduler": "unknown",
            "overall_status": "unknown"
        }

        # Check each component
        for component_name in [
            "service_registry",
            "config_manager",
            "coordination_router",
            "service_coordinator",
            "workflow_engine",
            "task_scheduler"
        ]:
            component = getattr(self, component_name, None)
            if component and hasattr(component, "health_check"):
                try:
                    component_health = await component.health_check()
                    health[component_name] = component_health.get("status", "unknown")
                except Exception:
                    health[component_name] = "unhealthy"
            elif component:
                health[component_name] = "healthy"
            else:
                health[component_name] = "not_initialized"

        # Overall status
        if all(status in ["healthy", "not_initialized"] for status in health.values() if status != health["overall_status"]):
            health["overall_status"] = "healthy"
        else:
            health["overall_status"] = "degraded"

        return health

    def get_service_registry(self):
        """Get service registry instance"""
        return self.service_registry

    def get_registered_services(self) -> Dict[str, Any]:
        """Get all registered services"""
        if self.service_registry:
            return self.service_registry.get_registry()
        return {}

    def get_service_count(self) -> int:
        """Get count of registered services"""
        return len(self.get_registered_services())
