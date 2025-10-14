"""
Monitoring Manager
Handles all health monitoring, infrastructure monitoring, and alerting
"""

import logging
from typing import Optional
from pathlib import Path
import sys
import traceback

# Add shared to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

# Core monitoring modules
from core.health_monitor import HealthMonitor
from core.infrastructure_monitor import InfrastructureMonitor
from core.dependency_graph import DependencyGraph
from core.health_aggregator import HealthAggregator
from core.alert_manager import AlertManager

logger = logging.getLogger("central-hub.monitoring-manager")


class MonitoringManager:
    """
    Manages all monitoring and alerting for Central Hub

    Responsibilities:
    - Health monitoring of services
    - Infrastructure monitoring (CPU, memory, disk, network)
    - Dependency graph tracking
    - Alert management and notifications
    - Health aggregation and reporting
    """

    def __init__(self, service_registry, db_manager, cache_manager):
        self.service_registry = service_registry
        self.db_manager = db_manager
        self.cache_manager = cache_manager

        # Monitoring components
        self.health_monitor: Optional[HealthMonitor] = None
        self.infrastructure_monitor: Optional[InfrastructureMonitor] = None
        self.dependency_graph: Optional[DependencyGraph] = None
        self.health_aggregator: Optional[HealthAggregator] = None
        self.alert_manager: Optional[AlertManager] = None

    async def initialize(self):
        """Initialize all monitoring components"""
        try:
            logger.info("🔍 Initializing Monitoring Manager...")

            # 1. Initialize health monitor
            self.health_monitor = HealthMonitor(
                service_registry=self.service_registry,
                db_manager=self.db_manager,
                cache_manager=self.cache_manager
            )

            # 2. Initialize infrastructure monitor
            self.infrastructure_monitor = InfrastructureMonitor()
            await self.infrastructure_monitor.initialize()

            # 3. Initialize dependency graph
            self.dependency_graph = DependencyGraph()
            await self.dependency_graph.initialize()

            # 4. Initialize alert manager
            self.alert_manager = AlertManager()
            await self.alert_manager.initialize()

            # 5. Initialize health aggregator
            self.health_aggregator = HealthAggregator(
                self.infrastructure_monitor,
                self.service_registry,
                self.dependency_graph
            )

            # 6. Connect alert callback
            self.infrastructure_monitor.set_alert_callback(
                self.alert_manager.trigger_alert
            )

            logger.info("✅ Monitoring Manager initialized")

        except Exception as e:
            logger.error(f"❌ Monitoring Manager initialization failed: {str(e)}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            # Non-critical - can continue without full monitoring
            logger.warning("⚠️ Continuing with partial monitoring")

    async def start_monitoring(self):
        """Start all monitoring services"""
        try:
            logger.info("▶️ Starting monitoring services...")

            # Start health monitoring
            if self.health_monitor:
                await self.health_monitor.start_monitoring()
                logger.info("✅ Health monitoring started")

            # Start infrastructure monitoring
            if self.infrastructure_monitor:
                await self.infrastructure_monitor.start_monitoring()
                logger.info("✅ Infrastructure monitoring started")

            logger.info("✅ All monitoring services started")

        except Exception as e:
            logger.error(f"❌ Failed to start monitoring services: {str(e)}")

    async def stop_monitoring(self):
        """Stop all monitoring services"""
        try:
            logger.info("🛑 Stopping monitoring services...")

            # Stop health monitoring
            if self.health_monitor:
                await self.health_monitor.stop_monitoring()
                logger.info("✅ Health monitoring stopped")

            # Stop infrastructure monitoring
            if self.infrastructure_monitor:
                await self.infrastructure_monitor.stop_monitoring()
                logger.info("✅ Infrastructure monitoring stopped")

            logger.info("✅ All monitoring services stopped")

        except Exception as e:
            logger.error(f"❌ Failed to stop monitoring services: {str(e)}")

    async def health_check(self):
        """Aggregate health status from all monitoring components"""
        health = {
            "health_monitor": "unknown",
            "infrastructure_monitor": "unknown",
            "alert_manager": "unknown",
            "overall_status": "unknown"
        }

        # Health monitor status
        if self.health_monitor and hasattr(self.health_monitor, "health_check"):
            try:
                health_status = await self.health_monitor.health_check()
                health["health_monitor"] = health_status.get("status", "unknown")
            except Exception:
                health["health_monitor"] = "unhealthy"
        else:
            health["health_monitor"] = "not_initialized"

        # Infrastructure monitor status
        if self.infrastructure_monitor:
            health["infrastructure_monitor"] = "healthy"
        else:
            health["infrastructure_monitor"] = "not_initialized"

        # Alert manager status
        if self.alert_manager:
            health["alert_manager"] = "healthy"
        else:
            health["alert_manager"] = "not_initialized"

        # Overall status
        if all(status in ["healthy", "not_initialized"] for status in [
            health["health_monitor"],
            health["infrastructure_monitor"],
            health["alert_manager"]
        ]):
            health["overall_status"] = "healthy"
        else:
            health["overall_status"] = "degraded"

        return health

    async def get_aggregated_health(self):
        """Get aggregated health report from all services"""
        if self.health_aggregator:
            return await self.health_aggregator.get_aggregated_health()
        return {"status": "not_available", "message": "Health aggregator not initialized"}

    async def get_infrastructure_metrics(self):
        """Get infrastructure metrics"""
        if self.infrastructure_monitor:
            return await self.infrastructure_monitor.get_metrics()
        return {"status": "not_available", "message": "Infrastructure monitor not initialized"}
