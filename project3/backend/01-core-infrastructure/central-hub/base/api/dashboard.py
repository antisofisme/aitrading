"""
Unified Dashboard API
Complete system health and monitoring for frontend dashboard
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional

dashboard_router = APIRouter()


@dashboard_router.get("/health")
async def get_system_health() -> Dict[str, Any]:
    """
    Get complete system health status
    Returns infrastructure + services + impact analysis + dependencies
    For frontend dashboard main view
    """
    from app import central_hub_service

    try:
        system_health = await central_hub_service.health_aggregator.get_system_health()
        return system_health.to_dict()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system health: {str(e)}")


@dashboard_router.get("/summary")
async def get_summary() -> Dict[str, Any]:
    """
    Get quick summary of system health
    Lightweight endpoint for polling/status checks
    """
    from app import central_hub_service

    try:
        summary = await central_hub_service.health_aggregator.get_summary()
        return summary

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")


@dashboard_router.get("/dependencies")
async def get_dependency_graph() -> Dict[str, Any]:
    """
    Get complete dependency graph
    For frontend visualization
    """
    from app import central_hub_service

    try:
        graph_data = central_hub_service.dependency_graph.get_graph_data()
        return graph_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dependency graph: {str(e)}")


@dashboard_router.get("/dependencies/{service}")
async def get_service_dependencies(service: str) -> Dict[str, Any]:
    """
    Get dependency chain for specific service
    Shows what service depends on and current status
    """
    from app import central_hub_service

    try:
        chain = central_hub_service.dependency_graph.get_dependency_chain(service)

        if not chain:
            raise HTTPException(status_code=404, detail=f"Service {service} not found")

        # Add current status for each dependency
        infrastructure_status = central_hub_service.infrastructure_monitor.get_all_status()

        for dep in chain.get('requires', []):
            infra_name = dep['name']
            if infra_name in infrastructure_status:
                dep['status'] = infrastructure_status[infra_name].status.value
                dep['last_check'] = infrastructure_status[infra_name].last_check

        for dep in chain.get('optional', []):
            infra_name = dep['name']
            if infra_name in infrastructure_status:
                dep['status'] = infrastructure_status[infra_name].status.value
                dep['last_check'] = infrastructure_status[infra_name].last_check

        return chain

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dependencies: {str(e)}")


@dashboard_router.get("/impact-analysis")
async def get_impact_analysis() -> Dict[str, Any]:
    """
    Get current impact analysis for all failures
    Shows what's affected and recommendations
    """
    from app import central_hub_service

    try:
        system_health = await central_hub_service.health_aggregator.get_system_health()

        return {
            "impact_analysis": system_health.impact_analysis,
            "count": len(system_health.impact_analysis)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get impact analysis: {str(e)}")


@dashboard_router.get("/metrics")
async def get_aggregated_metrics() -> Dict[str, Any]:
    """
    Get aggregated metrics from all components
    For frontend charts and statistics
    """
    from app import central_hub_service

    try:
        # Get infrastructure metrics
        infrastructure_status = central_hub_service.infrastructure_monitor.get_all_status()

        response_times = []
        for infra in infrastructure_status.values():
            if infra.response_time_ms is not None:
                response_times.append({
                    'name': infra.name,
                    'type': infra.type,
                    'response_time_ms': infra.response_time_ms,
                    'status': infra.status.value if hasattr(infra.status, 'value') else str(infra.status)
                })

        # Get service metrics
        service_registry = central_hub_service.service_registry.get_registry()
        service_metrics = []

        for name, info in service_registry.items():
            service_metrics.append({
                'name': name,
                'last_heartbeat': info.get('last_seen'),
                'uptime': info.get('metadata', {}).get('uptime'),
                'version': info.get('version')
            })

        # Get alert stats
        alert_stats = central_hub_service.alert_manager.get_alert_stats()

        return {
            'infrastructure': {
                'response_times': response_times,
                'average_response_time': sum(r['response_time_ms'] for r in response_times) / len(response_times) if response_times else 0
            },
            'services': service_metrics,
            'alerts': alert_stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@dashboard_router.get("/alerts")
async def get_alerts(
    active_only: bool = Query(False, description="Return only active alerts"),
    limit: int = Query(50, description="Maximum number of alerts to return")
) -> Dict[str, Any]:
    """
    Get system alerts
    """
    from app import central_hub_service

    try:
        if active_only:
            alerts = central_hub_service.alert_manager.get_active_alerts()
        else:
            alerts = central_hub_service.alert_manager.get_alert_history(limit=limit)

        return {
            "alerts": alerts,
            "count": len(alerts)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")


@dashboard_router.post("/alerts/{component}/acknowledge")
async def acknowledge_alert(component: str) -> Dict[str, Any]:
    """
    Acknowledge an alert
    """
    from app import central_hub_service

    try:
        success = central_hub_service.alert_manager.acknowledge_alert(component)

        if not success:
            raise HTTPException(status_code=404, detail=f"No active alert for {component}")

        return {
            "component": component,
            "acknowledged": True,
            "message": "Alert acknowledged successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge alert: {str(e)}")


@dashboard_router.get("/status")
async def get_dashboard_status() -> Dict[str, Any]:
    """
    Quick status endpoint for frontend health check
    """
    from app import central_hub_service

    try:
        summary = await central_hub_service.health_aggregator.get_summary()
        alert_stats = central_hub_service.alert_manager.get_alert_stats()

        return {
            "dashboard": "operational",
            "overall_status": summary['overall_status'],
            "active_alerts": alert_stats['active_alerts'],
            "timestamp": summary['timestamp']
        }

    except Exception as e:
        return {
            "dashboard": "error",
            "error": str(e)
        }
