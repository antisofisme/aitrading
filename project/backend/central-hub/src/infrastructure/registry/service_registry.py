"""
Service Registry for Central Hub Service

Phase 1 Implementation: Basic service registry and discovery
Focus: Service registration, health tracking, and basic discovery
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import httpx

from ..core.logger import CentralHubLogger


class ServiceStatus(Enum):
    """Service status enumeration"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    STARTING = "starting"
    STOPPING = "stopping"


@dataclass
class ServiceInfo:
    """Service information model"""
    name: str
    host: str
    port: int
    status: ServiceStatus
    health_endpoint: str
    last_seen: datetime
    metadata: Dict[str, Any]

    def __post_init__(self):
        if isinstance(self.status, str):
            self.status = ServiceStatus(self.status)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['status'] = self.status.value
        data['last_seen'] = self.last_seen.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServiceInfo':
        """Create from dictionary"""
        data_copy = data.copy()
        data_copy['status'] = ServiceStatus(data_copy['status'])
        data_copy['last_seen'] = datetime.fromisoformat(data_copy['last_seen'])
        return cls(**data_copy)


class ServiceRegistry:
    """
    Service Registry for Central Hub

    Phase 1 Implementation:
    - In-memory service storage
    - Basic health tracking
    - Service discovery
    - TTL-based cleanup
    """

    def __init__(self, logger: Optional[CentralHubLogger] = None):
        self.logger = logger
        self.services: Dict[str, ServiceInfo] = {}
        self.cleanup_task: Optional[asyncio.Task] = None
        self.cleanup_interval = 60  # seconds
        self.service_ttl = 300  # seconds (5 minutes)
        self.running = False

    async def initialize(self) -> None:
        """Initialize service registry"""
        try:
            if self.logger:
                self.logger.info("🚀 Initializing Service Registry")

            # Start cleanup task
            self.running = True
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())

            if self.logger:
                self.logger.info("✅ Service Registry initialized successfully")

        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to initialize Service Registry: {e}")
            raise

    async def shutdown(self) -> None:
        """Shutdown service registry"""
        try:
            if self.logger:
                self.logger.info("🛑 Shutting down Service Registry")

            self.running = False

            # Cancel cleanup task
            if self.cleanup_task and not self.cleanup_task.done():
                self.cleanup_task.cancel()
                try:
                    await self.cleanup_task
                except asyncio.CancelledError:
                    pass

            # Clear services
            self.services.clear()

            if self.logger:
                self.logger.info("✅ Service Registry shutdown complete")

        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Error shutting down Service Registry: {e}")

    async def register_service(
        self,
        name: str,
        host: str,
        port: int,
        health_endpoint: str = "/health",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Register a service

        Args:
            name: Service name
            host: Service host
            port: Service port
            health_endpoint: Health check endpoint
            metadata: Additional service metadata

        Returns:
            True if registration successful
        """
        try:
            service_info = ServiceInfo(
                name=name,
                host=host,
                port=port,
                status=ServiceStatus.STARTING,
                health_endpoint=health_endpoint,
                last_seen=datetime.utcnow(),
                metadata=metadata or {}
            )

            self.services[name] = service_info

            if self.logger:
                self.logger.log_service_event(
                    "service_registered",
                    name,
                    {
                        "host": host,
                        "port": port,
                        "health_endpoint": health_endpoint
                    }
                )

            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to register service '{name}': {e}")
            return False

    async def unregister_service(self, name: str) -> bool:
        """
        Unregister a service

        Args:
            name: Service name

        Returns:
            True if unregistration successful
        """
        try:
            if name in self.services:
                service_info = self.services[name]
                service_info.status = ServiceStatus.STOPPING

                # Remove from registry
                del self.services[name]

                if self.logger:
                    self.logger.log_service_event(
                        "service_unregistered",
                        name,
                        {"status": "removed"}
                    )

                return True
            else:
                if self.logger:
                    self.logger.warning(f"⚠️ Service '{name}' not found for unregistration")
                return False

        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to unregister service '{name}': {e}")
            return False

    async def update_service_status(self, name: str, status: ServiceStatus) -> bool:
        """
        Update service status

        Args:
            name: Service name
            status: New status

        Returns:
            True if update successful
        """
        try:
            if name in self.services:
                old_status = self.services[name].status
                self.services[name].status = status
                self.services[name].last_seen = datetime.utcnow()

                if self.logger:
                    self.logger.log_service_event(
                        "status_updated",
                        name,
                        {
                            "old_status": old_status.value,
                            "new_status": status.value
                        }
                    )

                return True
            else:
                if self.logger:
                    self.logger.warning(f"⚠️ Service '{name}' not found for status update")
                return False

        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to update service status '{name}': {e}")
            return False

    async def get_service(self, name: str) -> Optional[ServiceInfo]:
        """
        Get service information

        Args:
            name: Service name

        Returns:
            ServiceInfo if found, None otherwise
        """
        return self.services.get(name)

    async def get_all_services(self) -> List[Dict[str, Any]]:
        """
        Get all registered services

        Returns:
            List of service information dictionaries
        """
        return [service.to_dict() for service in self.services.values()]

    async def get_healthy_services(self) -> List[Dict[str, Any]]:
        """
        Get all healthy services

        Returns:
            List of healthy service information dictionaries
        """
        return [
            service.to_dict()
            for service in self.services.values()
            if service.status == ServiceStatus.HEALTHY
        ]

    async def discover_services(self, service_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Discover services by type

        Args:
            service_type: Optional service type filter

        Returns:
            List of matching services
        """
        services = await self.get_healthy_services()

        if service_type:
            services = [
                service for service in services
                if service.get("metadata", {}).get("type") == service_type
            ]

        return services

    async def health_check_service(self, name: str) -> ServiceStatus:
        """
        Perform health check on a service

        Args:
            name: Service name

        Returns:
            Service status
        """
        if name not in self.services:
            return ServiceStatus.UNKNOWN

        service = self.services[name]

        try:
            # Build health check URL
            health_url = f"http://{service.host}:{service.port}{service.health_endpoint}"

            # Perform health check
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(health_url)

                if response.status_code == 200:
                    new_status = ServiceStatus.HEALTHY
                else:
                    new_status = ServiceStatus.UNHEALTHY

                # Update service status
                await self.update_service_status(name, new_status)

                return new_status

        except Exception as e:
            if self.logger:
                self.logger.warning(
                    f"⚠️ Health check failed for service '{name}': {e}",
                    service_name=name,
                    error=str(e)
                )

            # Update service status to unhealthy
            await self.update_service_status(name, ServiceStatus.UNHEALTHY)
            return ServiceStatus.UNHEALTHY

    async def _cleanup_loop(self) -> None:
        """Background task to cleanup stale services"""
        while self.running:
            try:
                await self._cleanup_stale_services()
                await asyncio.sleep(self.cleanup_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.logger:
                    self.logger.error(f"❌ Error in cleanup loop: {e}")
                await asyncio.sleep(self.cleanup_interval)

    async def _cleanup_stale_services(self) -> None:
        """Remove stale services based on TTL"""
        try:
            current_time = datetime.utcnow()
            stale_services = []

            for name, service in self.services.items():
                time_since_last_seen = (current_time - service.last_seen).total_seconds()

                if time_since_last_seen > self.service_ttl:
                    stale_services.append(name)

            # Remove stale services
            for name in stale_services:
                if self.logger:
                    self.logger.log_service_event(
                        "service_expired",
                        name,
                        {"ttl_exceeded": True}
                    )
                del self.services[name]

            if stale_services and self.logger:
                self.logger.info(f"🧹 Cleaned up {len(stale_services)} stale services")

        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Error cleaning up stale services: {e}")

    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        status_counts = {}
        for status in ServiceStatus:
            status_counts[status.value] = sum(
                1 for service in self.services.values()
                if service.status == status
            )

        return {
            "total_services": len(self.services),
            "status_breakdown": status_counts,
            "cleanup_interval": self.cleanup_interval,
            "service_ttl": self.service_ttl,
            "running": self.running
        }

    def set_cleanup_config(self, cleanup_interval: int, service_ttl: int) -> None:
        """
        Set cleanup configuration

        Args:
            cleanup_interval: Cleanup interval in seconds
            service_ttl: Service TTL in seconds
        """
        self.cleanup_interval = cleanup_interval
        self.service_ttl = service_ttl

        if self.logger:
            self.logger.log_config_change(
                "registry_cleanup_config",
                f"interval={self.cleanup_interval}, ttl={self.service_ttl}",
                f"interval={cleanup_interval}, ttl={service_ttl}"
            )
"