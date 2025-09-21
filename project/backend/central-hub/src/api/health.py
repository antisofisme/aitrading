"""
Health API endpoints for Central Hub Service

Phase 1 Implementation: Basic health check and monitoring endpoints
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """Health response model"""
    status: str
    service: str
    timestamp: str
    details: Dict[str, Any] = {}


class ServiceHealthResponse(BaseModel):
    """Service health response model"""
    service_name: str
    status: str
    last_seen: str
    host: str
    port: int


@router.get("/", response_model=HealthResponse)
async def get_health(request: Request):
    """Get overall health status"""
    try:
        health_monitor = request.app.state.health_monitor

        if not health_monitor:
            raise HTTPException(status_code=503, detail="Health monitor not available")

        system_health = await health_monitor.get_system_health()

        return HealthResponse(
            status=system_health.get("overall_status", "unknown"),
            service="central-hub",
            timestamp=health_monitor.get_current_timestamp(),
            details=system_health
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/summary")
async def get_health_summary(request: Request):
    """Get health summary"""
    try:
        health_monitor = request.app.state.health_monitor

        if not health_monitor:
            raise HTTPException(status_code=503, detail="Health monitor not available")

        summary = await health_monitor.get_health_summary()
        return summary

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health summary failed: {str(e)}")


@router.get("/system")
async def get_system_health(request: Request):
    """Get detailed system health"""
    try:
        health_monitor = request.app.state.health_monitor

        if not health_monitor:
            raise HTTPException(status_code=503, detail="Health monitor not available")

        system_health = await health_monitor.get_system_health()
        return system_health

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"System health check failed: {str(e)}")


@router.get("/service/{service_name}", response_model=ServiceHealthResponse)
async def get_service_health(service_name: str, request: Request):
    """Get specific service health"""
    try:
        health_monitor = request.app.state.health_monitor

        if not health_monitor:
            raise HTTPException(status_code=503, detail="Health monitor not available")

        service_health = await health_monitor.get_service_health(service_name)

        if service_health.get("status") == "unknown":
            raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")

        return ServiceHealthResponse(**service_health)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Service health check failed: {str(e)}")


@router.get("/metrics")
async def get_health_metrics(request: Request):
    """Get health monitoring metrics"""
    try:
        health_monitor = request.app.state.health_monitor

        if not health_monitor:
            raise HTTPException(status_code=503, detail="Health monitor not available")

        metrics = health_monitor.get_monitor_stats()
        return metrics

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metrics retrieval failed: {str(e)}")
"