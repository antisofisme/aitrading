"""
Central Hub - Service Registry Coordinator
Handles service registration, discovery, and management
"""

import time
from typing import Dict, List, Optional, Any
import logging


class ServiceRegistry:
    """Manages service registration and discovery for Central Hub"""

    def __init__(self):
        self.logger = logging.getLogger("central-hub.service-registry")
        self.services: Dict[str, Dict[str, Any]] = {}
        self.service_health: Dict[str, Dict[str, Any]] = {}

    async def register(self, registration_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new service with Central Hub"""
        service_name = registration_data.get("name")
        if not service_name:
            raise ValueError("Service name is required for registration")

        service_info = {
            "name": service_name,
            "host": registration_data.get("host"),
            "port": registration_data.get("port"),
            "protocol": registration_data.get("protocol", "http"),
            "health_endpoint": registration_data.get("health_endpoint", "/health"),
            "version": registration_data.get("version"),
            "metadata": registration_data.get("metadata", {}),
            "capabilities": registration_data.get("capabilities", []),
            "tenant_id": registration_data.get("tenant_id"),
            "registered_at": int(time.time() * 1000),
            "last_seen": int(time.time() * 1000),
            "status": "active",
            "url": f"{registration_data.get('protocol', 'http')}://{registration_data.get('host')}:{registration_data.get('port')}"
        }

        # Store service registration
        self.services[service_name] = service_info

        # Initialize health tracking
        self.service_health[service_name] = {
            "status": "healthy",
            "last_check": int(time.time() * 1000),
            "response_time_ms": 0,
            "consecutive_failures": 0
        }

        self.logger.info(f"✅ Service registered: {service_name} at {service_info['url']}")

        return {
            "direct_response": {
                "type": "service_registration_response",
                "data": {
                    "status": "registered",
                    "service": service_name,
                    "url": service_info["url"],
                    "registered_at": service_info["registered_at"]
                }
            }
        }

    async def discover(self, discovery_data: Dict[str, Any]) -> Dict[str, Any]:
        """Discover services based on criteria"""
        service_name = discovery_data.get("service_name")
        tenant_id = discovery_data.get("tenant_id")
        required_capabilities = discovery_data.get("required_capabilities", [])

        if service_name:
            # Specific service discovery
            service = self.services.get(service_name)
            if not service:
                raise ValueError(f"Service {service_name} not found")

            # Update last accessed
            service["last_accessed"] = int(time.time() * 1000)

            return {
                "direct_response": {
                    "type": "service_discovery_response",
                    "data": {
                        "service": service,
                        "url": service["url"],
                        "status": service["status"],
                        "health": self.service_health.get(service_name, {})
                    }
                }
            }
        else:
            # List all services with filtering
            filtered_services = {}
            for name, service in self.services.items():
                # Filter by tenant if specified
                if tenant_id and service.get("tenant_id") != tenant_id:
                    continue

                # Filter by capabilities if specified
                if required_capabilities:
                    service_caps = service.get("capabilities", [])
                    if not all(cap in service_caps for cap in required_capabilities):
                        continue

                filtered_services[name] = service

            return {
                "direct_response": {
                    "type": "service_list_response",
                    "data": {
                        "services": filtered_services,
                        "count": len(filtered_services),
                        "timestamp": int(time.time() * 1000)
                    }
                }
            }

    async def update_service_health(self, service_name: str, health_data: Dict[str, Any]):
        """Update service health status"""
        if service_name not in self.services:
            self.logger.warning(f"Health update for unknown service: {service_name}")
            return

        self.service_health[service_name] = {
            "status": health_data.get("status", "unknown"),
            "last_check": int(time.time() * 1000),
            "response_time_ms": health_data.get("response_time_ms", 0),
            "consecutive_failures": health_data.get("consecutive_failures", 0),
            "metrics": health_data.get("metrics", {})
        }

        # Update service status based on health
        if health_data.get("status") == "unhealthy":
            self.services[service_name]["status"] = "unhealthy"
        elif health_data.get("status") == "healthy":
            self.services[service_name]["status"] = "active"

        self.services[service_name]["last_seen"] = int(time.time() * 1000)

    async def unregister(self, service_name: str) -> Dict[str, Any]:
        """Unregister a service"""
        if service_name not in self.services:
            raise ValueError(f"Service {service_name} not found")

        del self.services[service_name]
        if service_name in self.service_health:
            del self.service_health[service_name]

        self.logger.info(f"❌ Service unregistered: {service_name}")

        return {
            "direct_response": {
                "type": "service_unregistration_response",
                "data": {
                    "status": "unregistered",
                    "service": service_name
                }
            }
        }

    def get_healthy_services(self) -> List[str]:
        """Get list of healthy service names"""
        return [
            name for name, health in self.service_health.items()
            if health.get("status") == "healthy"
        ]

    def get_service_endpoints(self, service_name: str) -> List[Dict[str, Any]]:
        """Get available endpoints for a service (for load balancing)"""
        service = self.services.get(service_name)
        if not service:
            return []

        health = self.service_health.get(service_name, {})

        return [{
            "url": service["url"],
            "healthy": health.get("status") == "healthy",
            "response_time_ms": health.get("response_time_ms", 0),
            "metadata": service.get("metadata", {})
        }]

    async def health_check(self) -> Dict[str, Any]:
        """Health check for service registry coordinator"""
        return {
            "status": "operational",
            "registered_services": len(self.services),
            "healthy_services": len(self.get_healthy_services()),
            "unhealthy_services": len(self.services) - len(self.get_healthy_services()),
            "last_registration": max([s.get("registered_at", 0) for s in self.services.values()] + [0])
        }
    def get_registry(self) -> Dict[str, Dict[str, Any]]:
        """Get the service registry dictionary"""
        return self.services.copy()
