"""
Infrastructure Monitoring API
Endpoints for infrastructure health monitoring
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

infrastructure_router = APIRouter()


@infrastructure_router.get("/")
async def list_infrastructure() -> Dict[str, Any]:
    """List all infrastructure with health status"""
    from app import central_hub_service

    try:
        infrastructure_health = await central_hub_service.health_aggregator.get_infrastructure_health()

        return {
            "infrastructure": infrastructure_health,
            "count": len(infrastructure_health)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get infrastructure status: {str(e)}")


@infrastructure_router.get("/{name}")
async def get_infrastructure(name: str) -> Dict[str, Any]:
    """Get specific infrastructure status"""
    from app import central_hub_service

    infrastructure_status = central_hub_service.infrastructure_monitor.get_infrastructure_status(name)

    if not infrastructure_status:
        raise HTTPException(status_code=404, detail=f"Infrastructure {name} not found")

    return {
        "infrastructure": infrastructure_status.to_dict(),
        "dependents": central_hub_service.dependency_graph.get_dependents(name)
    }


@infrastructure_router.get("/{name}/dependents")
async def get_infrastructure_dependents(name: str) -> Dict[str, Any]:
    """Get services that depend on this infrastructure"""
    from app import central_hub_service

    dependents = central_hub_service.dependency_graph.get_dependents(name)

    if dependents is None:
        raise HTTPException(status_code=404, detail=f"Infrastructure {name} not found")

    return {
        "infrastructure": name,
        "dependents": dependents,
        "count": len(dependents)
    }


@infrastructure_router.post("/{name}/check")
async def manual_health_check(name: str) -> Dict[str, Any]:
    """Manually trigger health check for infrastructure"""
    from app import central_hub_service

    try:
        result = await central_hub_service.infrastructure_monitor.manual_check(name)

        return {
            "infrastructure": name,
            "status": result.to_dict(),
            "message": "Manual health check completed"
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@infrastructure_router.get("/{name}/impact")
async def get_infrastructure_impact(name: str) -> Dict[str, Any]:
    """Get impact analysis if this infrastructure fails"""
    from app import central_hub_service

    try:
        impact = central_hub_service.dependency_graph.analyze_impact(name, 'infrastructure')

        return impact.to_dict()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Impact analysis failed: {str(e)}")
