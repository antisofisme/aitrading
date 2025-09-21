"""
Service Registry API endpoints for Central Hub Service

Phase 1 Implementation: Service registration and discovery endpoints
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter()


class ServiceRegistrationRequest(BaseModel):
    """Service registration request model"""
    name: str
    host: str
    port: int
    health_endpoint: str = "/health"
    metadata: Dict[str, Any] = {}


class ServiceResponse(BaseModel):
    """Service response model"""
    name: str
    host: str
    port: int
    status: str
    health_endpoint: str
    last_seen: str
    metadata: Dict[str, Any]


class ServiceRegistryStats(BaseModel):
    """Service registry statistics model"""
    total_services: int
    status_breakdown: Dict[str, int]
    cleanup_interval: int
    service_ttl: int
    running: bool


@router.post("/register")
async def register_service(service_request: ServiceRegistrationRequest, request: Request):
    """Register a new service"""
    try:
        service_registry = request.app.state.service_registry
        logger = request.app.state.logger

        if not service_registry:
            raise HTTPException(status_code=503, detail="Service registry not available")

        success = await service_registry.register_service(
            name=service_request.name,
            host=service_request.host,
            port=service_request.port,
            health_endpoint=service_request.health_endpoint,
            metadata=service_request.metadata
        )

        if success:
            if logger:
                logger.info(
                    f"✅ Service registered: {service_request.name}",
                    service_name=service_request.name,
                    host=service_request.host,
                    port=service_request.port
                )

            return {
                "message": f"Service '{service_request.name}' registered successfully",
                "service_name": service_request.name,
                "status": "registered"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to register service")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Service registration failed: {str(e)}")


@router.delete("/{service_name}")
async def unregister_service(service_name: str, request: Request):
    """Unregister a service"""
    try:
        service_registry = request.app.state.service_registry
        logger = request.app.state.logger

        if not service_registry:
            raise HTTPException(status_code=503, detail="Service registry not available")

        success = await service_registry.unregister_service(service_name)

        if success:
            if logger:
                logger.info(f"✅ Service unregistered: {service_name}")

            return {
                "message": f"Service '{service_name}' unregistered successfully",
                "service_name": service_name,
                "status": "unregistered"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Service unregistration failed: {str(e)}")


@router.get("/", response_model=List[ServiceResponse])
async def get_all_services(request: Request):
    """Get all registered services"""
    try:
        service_registry = request.app.state.service_registry

        if not service_registry:
            raise HTTPException(status_code=503, detail="Service registry not available")

        services = await service_registry.get_all_services()

        return [ServiceResponse(**service) for service in services]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve services: {str(e)}")


@router.get("/healthy", response_model=List[ServiceResponse])
async def get_healthy_services(request: Request):
    """Get all healthy services"""
    try:
        service_registry = request.app.state.service_registry

        if not service_registry:
            raise HTTPException(status_code=503, detail="Service registry not available")

        services = await service_registry.get_healthy_services()

        return [ServiceResponse(**service) for service in services]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve healthy services: {str(e)}")


@router.get("/{service_name}", response_model=ServiceResponse)
async def get_service(service_name: str, request: Request):
    """Get specific service information"""
    try:
        service_registry = request.app.state.service_registry

        if not service_registry:
            raise HTTPException(status_code=503, detail="Service registry not available")

        service = await service_registry.get_service(service_name)

        if service:
            return ServiceResponse(**service.to_dict())
        else:
            raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve service: {str(e)}")


@router.get("/discover/{service_type}")
async def discover_services(service_type: str, request: Request):
    """Discover services by type"""
    try:
        service_registry = request.app.state.service_registry

        if not service_registry:
            raise HTTPException(status_code=503, detail="Service registry not available")

        services = await service_registry.discover_services(service_type)

        return {
            "service_type": service_type,
            "services": services,
            "count": len(services)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Service discovery failed: {str(e)}")


@router.post("/{service_name}/health-check")
async def health_check_service(service_name: str, request: Request):
    """Trigger health check for a specific service"""
    try:
        service_registry = request.app.state.service_registry
        logger = request.app.state.logger

        if not service_registry:
            raise HTTPException(status_code=503, detail="Service registry not available")

        status = await service_registry.health_check_service(service_name)

        if logger:
            logger.info(
                f"🔍 Manual health check performed: {service_name} - {status.value}",
                service_name=service_name,
                health_status=status.value
            )

        return {
            "service_name": service_name,
            "status": status.value,
            "timestamp": request.app.state.health_monitor.get_current_timestamp()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/stats/registry", response_model=ServiceRegistryStats)
async def get_registry_stats(request: Request):
    """Get service registry statistics"""
    try:
        service_registry = request.app.state.service_registry

        if not service_registry:
            raise HTTPException(status_code=503, detail="Service registry not available")

        stats = service_registry.get_registry_stats()

        return ServiceRegistryStats(**stats)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve registry stats: {str(e)}")
"