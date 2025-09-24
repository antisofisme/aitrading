"""
Central Hub Health Check API
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
import time

health_router = APIRouter()


@health_router.get("/")
async def health_check() -> Dict[str, Any]:
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": int(time.time() * 1000),
        "service": "central-hub",
        "version": "3.0.0"
    }


@health_router.get("/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """Detailed health check dengan service-specific metrics"""
    # Import service instance (circular import avoidance)
    from ..app import central_hub_service

    custom_checks = await central_hub_service.custom_health_checks()

    return {
        "status": "healthy",
        "timestamp": int(time.time() * 1000),
        "service": "central-hub",
        "version": "3.0.0",
        "details": custom_checks,
        "uptime_seconds": time.time() - central_hub_service.start_time,
        "components": {
            "service_discovery": "active",
            "health_monitor": "active",
            "load_balancer": "active",
            "circuit_breaker": "active"
        }
    }


@health_router.get("/readiness")
async def readiness_check() -> Dict[str, Any]:
    """Kubernetes readiness probe"""
    return {
        "ready": True,
        "service": "central-hub"
    }


@health_router.get("/liveness")
async def liveness_check() -> Dict[str, Any]:
    """Kubernetes liveness probe"""
    return {
        "alive": True,
        "service": "central-hub"
    }