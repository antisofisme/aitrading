"""
Health Monitor for Central Hub Service

Phase 1 Implementation: Basic health monitoring and status aggregation
Focus: Service health checks, system health, and basic monitoring
"""

import asyncio
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from ..core.logger import CentralHubLogger
from ..registry.service_registry import ServiceRegistry, ServiceStatus


class HealthStatus(Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthMetric:
    """Health metric model"""
    name: str
    value: float
    unit: str
    status: HealthStatus
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if isinstance(self.status, str):
            self.status = HealthStatus(self.status)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['status'] = self.status.value
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class SystemHealth:
    """System health model"""
    overall_status: HealthStatus
    cpu_usage: HealthMetric
    memory_usage: HealthMetric
    disk_usage: HealthMetric
    services_health: Dict[str, str]
    timestamp: datetime

    def __post_init__(self):
        if isinstance(self.overall_status, str):
            self.overall_status = HealthStatus(self.overall_status)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "overall_status": self.overall_status.value,
            "cpu_usage": self.cpu_usage.to_dict(),
            "memory_usage": self.memory_usage.to_dict(),
            "disk_usage": self.disk_usage.to_dict(),
            "services_health": self.services_health,
            "timestamp": self.timestamp.isoformat()
        }


class HealthMonitor:
    """
    Health Monitor for Central Hub

    Phase 1 Implementation:
    - System metrics monitoring
    - Service health aggregation
    - Basic alerting
    - Health status reporting
    """

    def __init__(
        self,
        service_registry: ServiceRegistry,
        logger: Optional[CentralHubLogger] = None
    ):
        self.service_registry = service_registry
        self.logger = logger
        self.monitoring_task: Optional[asyncio.Task] = None
        self.check_interval = 30  # seconds
        self.running = False

        # Health thresholds
        self.cpu_warning_threshold = 70.0  # %
        self.cpu_critical_threshold = 90.0  # %
        self.memory_warning_threshold = 80.0  # %
        self.memory_critical_threshold = 95.0  # %
        self.disk_warning_threshold = 85.0  # %
        self.disk_critical_threshold = 95.0  # %

        # Current system health
        self.current_health: Optional[SystemHealth] = None

    async def start(self) -> None:
        """Start health monitoring"""
        try:
            if self.logger:
                self.logger.info("🚀 Starting Health Monitor")

            self.running = True
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())

            # Perform initial health check
            await self._check_system_health()

            if self.logger:
                self.logger.info("✅ Health Monitor started successfully")

        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to start Health Monitor: {e}")
            raise

    async def stop(self) -> None:
        """Stop health monitoring"""
        try:
            if self.logger:
                self.logger.info("🛑 Stopping Health Monitor")

            self.running = False

            # Cancel monitoring task
            if self.monitoring_task and not self.monitoring_task.done():
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass

            if self.logger:
                self.logger.info("✅ Health Monitor stopped successfully")

        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Error stopping Health Monitor: {e}")

    async def _monitoring_loop(self) -> None:
        """Background monitoring loop"""
        while self.running:
            try:
                await self._check_system_health()
                await self._check_services_health()
                await asyncio.sleep(self.check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.logger:
                    self.logger.error(f"❌ Error in monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)

    async def _check_system_health(self) -> None:
        """Check system health metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_status = self._determine_status(
                cpu_percent,
                self.cpu_warning_threshold,
                self.cpu_critical_threshold
            )
            cpu_metric = HealthMetric(
                name="cpu_usage",
                value=cpu_percent,
                unit="%",
                status=cpu_status,
                threshold_warning=self.cpu_warning_threshold,
                threshold_critical=self.cpu_critical_threshold
            )

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_status = self._determine_status(
                memory_percent,
                self.memory_warning_threshold,
                self.memory_critical_threshold
            )
            memory_metric = HealthMetric(
                name="memory_usage",
                value=memory_percent,
                unit="%",
                status=memory_status,
                threshold_warning=self.memory_warning_threshold,
                threshold_critical=self.memory_critical_threshold
            )

            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            disk_status = self._determine_status(
                disk_percent,
                self.disk_warning_threshold,
                self.disk_critical_threshold
            )
            disk_metric = HealthMetric(
                name="disk_usage",
                value=disk_percent,
                unit="%",
                status=disk_status,
                threshold_warning=self.disk_warning_threshold,
                threshold_critical=self.disk_critical_threshold
            )

            # Services health summary
            services = await self.service_registry.get_all_services()
            services_health = {
                service["name"]: service["status"]
                for service in services
            }

            # Determine overall status
            overall_status = self._determine_overall_status([
                cpu_status,
                memory_status,
                disk_status
            ])

            # Update current health
            self.current_health = SystemHealth(
                overall_status=overall_status,
                cpu_usage=cpu_metric,
                memory_usage=memory_metric,
                disk_usage=disk_metric,
                services_health=services_health,
                timestamp=datetime.utcnow()
            )

            # Log health metrics
            if self.logger:
                self.logger.log_performance_metric("cpu_usage", cpu_percent, "%")
                self.logger.log_performance_metric("memory_usage", memory_percent, "%")
                self.logger.log_performance_metric("disk_usage", disk_percent, "%")

        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Error checking system health: {e}")

    async def _check_services_health(self) -> None:
        """Check health of all registered services"""
        try:
            services = await self.service_registry.get_all_services()

            for service in services:
                service_name = service["name"]

                # Perform health check
                status = await self.service_registry.health_check_service(service_name)

                if self.logger:
                    self.logger.log_health_check(
                        service_name,
                        status.value,
                        {"host": service["host"], "port": service["port"]}
                    )

        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Error checking services health: {e}")

    def _determine_status(
        self,
        value: float,
        warning_threshold: float,
        critical_threshold: float
    ) -> HealthStatus:
        """Determine health status based on thresholds"""
        if value >= critical_threshold:
            return HealthStatus.CRITICAL
        elif value >= warning_threshold:
            return HealthStatus.WARNING
        else:
            return HealthStatus.HEALTHY

    def _determine_overall_status(self, statuses: List[HealthStatus]) -> HealthStatus:
        """Determine overall status from multiple statuses"""
        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL
        elif HealthStatus.WARNING in statuses:
            return HealthStatus.WARNING
        elif HealthStatus.UNKNOWN in statuses:
            return HealthStatus.UNKNOWN
        else:
            return HealthStatus.HEALTHY

    async def get_system_health(self) -> Dict[str, Any]:
        """
        Get current system health

        Returns:
            System health dictionary
        """
        if self.current_health:
            return self.current_health.to_dict()
        else:
            return {
                "overall_status": HealthStatus.UNKNOWN.value,
                "message": "Health monitoring not available"
            }

    async def get_service_health(self, service_name: str) -> Dict[str, Any]:
        """
        Get specific service health

        Args:
            service_name: Name of the service

        Returns:
            Service health information
        """
        service = await self.service_registry.get_service(service_name)

        if service:
            return {
                "service_name": service_name,
                "status": service.status.value,
                "last_seen": service.last_seen.isoformat(),
                "host": service.host,
                "port": service.port
            }
        else:
            return {
                "service_name": service_name,
                "status": ServiceStatus.UNKNOWN.value,
                "message": "Service not found"
            }

    async def get_health_summary(self) -> Dict[str, Any]:
        """
        Get health summary

        Returns:
            Health summary dictionary
        """
        system_health = await self.get_system_health()
        services = await self.service_registry.get_all_services()

        # Count services by status
        service_status_counts = {}
        for status in ServiceStatus:
            service_status_counts[status.value] = sum(
                1 for service in services
                if service["status"] == status.value
            )

        return {
            "system_status": system_health.get("overall_status"),
            "total_services": len(services),
            "service_status_counts": service_status_counts,
            "system_metrics": {
                "cpu_usage": system_health.get("cpu_usage", {}),
                "memory_usage": system_health.get("memory_usage", {}),
                "disk_usage": system_health.get("disk_usage", {})
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    def set_thresholds(
        self,
        cpu_warning: float = None,
        cpu_critical: float = None,
        memory_warning: float = None,
        memory_critical: float = None,
        disk_warning: float = None,
        disk_critical: float = None
    ) -> None:
        """Set health monitoring thresholds"""
        if cpu_warning is not None:
            self.cpu_warning_threshold = cpu_warning
        if cpu_critical is not None:
            self.cpu_critical_threshold = cpu_critical
        if memory_warning is not None:
            self.memory_warning_threshold = memory_warning
        if memory_critical is not None:
            self.memory_critical_threshold = memory_critical
        if disk_warning is not None:
            self.disk_warning_threshold = disk_warning
        if disk_critical is not None:
            self.disk_critical_threshold = disk_critical

        if self.logger:
            self.logger.log_config_change(
                "health_thresholds",
                "updated",
                {
                    "cpu_warning": self.cpu_warning_threshold,
                    "cpu_critical": self.cpu_critical_threshold,
                    "memory_warning": self.memory_warning_threshold,
                    "memory_critical": self.memory_critical_threshold,
                    "disk_warning": self.disk_warning_threshold,
                    "disk_critical": self.disk_critical_threshold
                }
            )

    def get_current_timestamp(self) -> str:
        """Get current timestamp as ISO string"""
        return datetime.utcnow().isoformat() + "Z"

    def get_monitor_stats(self) -> Dict[str, Any]:
        """Get monitor statistics"""
        return {
            "running": self.running,
            "check_interval": self.check_interval,
            "thresholds": {
                "cpu_warning": self.cpu_warning_threshold,
                "cpu_critical": self.cpu_critical_threshold,
                "memory_warning": self.memory_warning_threshold,
                "memory_critical": self.memory_critical_threshold,
                "disk_warning": self.disk_warning_threshold,
                "disk_critical": self.disk_critical_threshold
            },
            "last_check": self.current_health.timestamp.isoformat() if self.current_health else None
        }
"