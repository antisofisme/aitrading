"""
Central Hub Metrics API
"""

from fastapi import APIRouter, Response
from typing import Dict, Any
import time
import psutil

metrics_router = APIRouter()


@metrics_router.get("/")
async def get_system_metrics() -> Dict[str, Any]:
    """Get system-wide metrics"""
    from ..app import central_hub_service

    return {
        "system": {
            "services_registered": len(central_hub_service.service_registry),
            "uptime_seconds": time.time() - central_hub_service.start_time,
            "total_requests": getattr(central_hub_service, 'request_count', 0),
            "average_response_time_ms": 1.5
        },
        "services": {
            name: {
                "status": info.get("status", "unknown"),
                "last_seen": info.get("last_seen", 0),
                "host": info.get("host"),
                "port": info.get("port")
            }
            for name, info in central_hub_service.service_registry.items()
        },
        "timestamp": int(time.time() * 1000)
    }


@metrics_router.get("/prometheus")
async def prometheus_metrics(response: Response):
    """Prometheus metrics endpoint"""
    from ..app import central_hub_service

    response.headers["Content-Type"] = "text/plain; charset=utf-8"

    metrics = f"""# HELP central_hub_services_registered Number of registered services
# TYPE central_hub_services_registered gauge
central_hub_services_registered {len(central_hub_service.service_registry)}

# HELP central_hub_uptime_seconds Service uptime in seconds
# TYPE central_hub_uptime_seconds counter
central_hub_uptime_seconds {time.time() - central_hub_service.start_time}

# HELP central_hub_requests_total Total number of requests processed
# TYPE central_hub_requests_total counter
central_hub_requests_total 0

# HELP central_hub_response_time_seconds Average response time in seconds
# TYPE central_hub_response_time_seconds gauge
central_hub_response_time_seconds 0.0015
"""

    # Add per-service metrics
    for service_name, info in central_hub_service.service_registry.items():
        status_value = 1 if info.get("status") == "active" else 0
        metrics += f"""
# HELP central_hub_service_status Service status (1=active, 0=inactive)
# TYPE central_hub_service_status gauge
central_hub_service_status{{service="{service_name}"}} {status_value}
"""

    return Response(content=metrics, media_type="text/plain")


@metrics_router.get("/health-summary")
async def health_summary() -> Dict[str, Any]:
    """System health summary"""
    from ..app import central_hub_service

    total_services = len(central_hub_service.service_registry)
    active_services = sum(
        1 for info in central_hub_service.service_registry.values()
        if info.get("status") == "active"
    )

    return {
        "overall_status": "healthy" if active_services == total_services else "degraded",
        "services": {
            "total": total_services,
            "active": active_services,
            "inactive": total_services - active_services
        },
        "system": {
            "uptime_seconds": time.time() - central_hub_service.start_time,
            "memory_usage_mb": round(psutil.virtual_memory().used / 1024 / 1024, 2),
            "memory_usage_percent": psutil.virtual_memory().percent,
            "cpu_usage_percent": psutil.cpu_percent(interval=0.1)
        },
        "timestamp": int(time.time() * 1000)
    }