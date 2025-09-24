"""
Central Hub Service Discovery API
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import time

discovery_router = APIRouter()


class ServiceRegistration(BaseModel):
    """Service registration model"""
    name: str
    host: str
    port: int
    protocol: str = "http"
    health_endpoint: str = "/health"
    version: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ServiceUpdate(BaseModel):
    """Service update model"""
    host: Optional[str] = None
    port: Optional[int] = None
    health_endpoint: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@discovery_router.post("/register")
async def register_service(registration: ServiceRegistration) -> Dict[str, Any]:
    """Register a service dengan Central Hub"""
    # Import service instance
    from ..app import central_hub_service

    service_info = {
        "name": registration.name,
        "host": registration.host,
        "port": registration.port,
        "protocol": registration.protocol,
        "health_endpoint": registration.health_endpoint,
        "version": registration.version,
        "metadata": registration.metadata or {},
        "registered_at": int(time.time() * 1000),
        "last_seen": int(time.time() * 1000),
        "status": "active"
    }

    # Store in service registry
    central_hub_service.service_registry[registration.name] = service_info

    central_hub_service.logger.info(
        f"Service registered: {registration.name} at {registration.host}:{registration.port}"
    )

    return {
        "status": "registered",
        "service": registration.name,
        "registered_at": service_info["registered_at"]
    }


@discovery_router.get("/{service_name}")
async def get_service(service_name: str) -> Dict[str, Any]:
    """Get service information by name"""
    from ..app import central_hub_service

    if service_name not in central_hub_service.service_registry:
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")

    service_info = central_hub_service.service_registry[service_name]

    return {
        "service": service_name,
        "info": service_info,
        "url": f"{service_info['protocol']}://{service_info['host']}:{service_info['port']}"
    }


@discovery_router.get("/")
async def list_services() -> Dict[str, Any]:
    """List all registered services"""
    from ..app import central_hub_service

    services = {}
    for name, info in central_hub_service.service_registry.items():
        services[name] = {
            "host": info["host"],
            "port": info["port"],
            "protocol": info["protocol"],
            "status": info["status"],
            "last_seen": info["last_seen"],
            "url": f"{info['protocol']}://{info['host']}:{info['port']}"
        }

    return {
        "services": services,
        "count": len(services)
    }


@discovery_router.put("/{service_name}")
async def update_service(service_name: str, update: ServiceUpdate) -> Dict[str, Any]:
    """Update service information"""
    from ..app import central_hub_service

    if service_name not in central_hub_service.service_registry:
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")

    service_info = central_hub_service.service_registry[service_name]

    # Update provided fields
    if update.host is not None:
        service_info["host"] = update.host
    if update.port is not None:
        service_info["port"] = update.port
    if update.health_endpoint is not None:
        service_info["health_endpoint"] = update.health_endpoint
    if update.metadata is not None:
        service_info["metadata"].update(update.metadata)

    service_info["last_seen"] = int(time.time() * 1000)

    central_hub_service.logger.info(f"Service updated: {service_name}")

    return {
        "status": "updated",
        "service": service_name,
        "updated_at": service_info["last_seen"]
    }


@discovery_router.delete("/{service_name}")
async def deregister_service(service_name: str) -> Dict[str, Any]:
    """Deregister service from Central Hub"""
    from ..app import central_hub_service

    if service_name not in central_hub_service.service_registry:
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")

    del central_hub_service.service_registry[service_name]

    central_hub_service.logger.info(f"Service deregistered: {service_name}")

    return {
        "status": "deregistered",
        "service": service_name,
        "deregistered_at": int(time.time() * 1000)
    }


@discovery_router.post("/{service_name}/heartbeat")
async def service_heartbeat(service_name: str) -> Dict[str, Any]:
    """Update service heartbeat"""
    from ..app import central_hub_service

    if service_name not in central_hub_service.service_registry:
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")

    central_hub_service.service_registry[service_name]["last_seen"] = int(time.time() * 1000)
    central_hub_service.service_registry[service_name]["status"] = "active"

    return {
        "status": "heartbeat_received",
        "service": service_name,
        "last_seen": central_hub_service.service_registry[service_name]["last_seen"]
    }