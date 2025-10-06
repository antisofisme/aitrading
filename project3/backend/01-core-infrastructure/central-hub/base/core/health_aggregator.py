"""
Health Aggregator - Combines infrastructure and service health into unified view
"""

import logging
import time
from typing import Dict, List, Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

from models.infrastructure_model import SystemHealth, InfrastructureStatus

logger = logging.getLogger("central-hub.health-aggregator")


class HealthAggregator:
    """Aggregates health data from infrastructure and services"""

    def __init__(self, infrastructure_monitor, service_registry, dependency_graph):
        self.infrastructure_monitor = infrastructure_monitor
        self.service_registry = service_registry
        self.dependency_graph = dependency_graph

    async def get_system_health(self) -> SystemHealth:
        """
        Get complete system health status

        Returns:
            SystemHealth object with complete status
        """
        # Get infrastructure status
        infrastructure_status = self.infrastructure_monitor.get_all_status()

        # Get service status
        service_status = self.service_registry.get_registry()

        # Calculate summary
        infra_summary = self._calculate_infrastructure_summary(infrastructure_status)
        service_summary = self._calculate_service_summary(service_status)

        # Calculate overall status
        overall_status = self._calculate_overall_status(infra_summary, service_summary)

        # Get impact analysis for any failures
        impact_analysis = await self._get_impact_analysis(infrastructure_status, service_status)

        # Build complete system health
        system_health = SystemHealth(
            timestamp=int(time.time() * 1000),
            overall_status=overall_status,
            summary={
                'infrastructure': infra_summary,
                'services': service_summary
            },
            infrastructure=self._format_infrastructure_status(infrastructure_status),
            services=self._format_service_status(service_status),
            impact_analysis=impact_analysis,
            dependency_graph=self.dependency_graph.get_graph_data()
        )

        return system_health

    def _calculate_infrastructure_summary(self, infrastructure_status: Dict) -> Dict[str, int]:
        """Calculate infrastructure summary statistics"""
        total = len(infrastructure_status)
        healthy = sum(1 for h in infrastructure_status.values() if h.status == InfrastructureStatus.HEALTHY)
        unhealthy = sum(1 for h in infrastructure_status.values() if h.status == InfrastructureStatus.UNHEALTHY)
        critical_down = sum(
            1 for h in infrastructure_status.values()
            if h.status == InfrastructureStatus.UNHEALTHY and h.critical
        )

        return {
            'total': total,
            'healthy': healthy,
            'unhealthy': unhealthy,
            'critical_down': critical_down
        }

    def _calculate_service_summary(self, service_status: Dict) -> Dict[str, int]:
        """Calculate service summary statistics"""
        total = len(service_status)
        healthy = 0
        degraded = 0
        down = 0

        for service_name, service_info in service_status.items():
            status = service_info.get('status', 'unknown')
            if status == 'active':
                # Check if service is actually healthy based on dependencies
                if self._is_service_healthy(service_name):
                    healthy += 1
                else:
                    degraded += 1
            else:
                down += 1

        return {
            'total': total,
            'healthy': healthy,
            'degraded': degraded,
            'down': down
        }

    def _is_service_healthy(self, service_name: str) -> bool:
        """Check if service is healthy based on its dependencies"""
        # Get service dependency chain
        chain = self.dependency_graph.get_dependency_chain(service_name)
        if not chain:
            return True  # No dependencies = healthy

        # Check required dependencies
        infrastructure_status = self.infrastructure_monitor.get_all_status()

        for dep in chain.get('requires', []):
            infra_name = dep['name']
            if infra_name in infrastructure_status:
                if infrastructure_status[infra_name].status != InfrastructureStatus.HEALTHY:
                    return False  # Required dependency down = degraded

        return True

    def _calculate_overall_status(self, infra_summary: Dict, service_summary: Dict) -> str:
        """
        Calculate overall system status

        Returns:
            'healthy', 'degraded', or 'critical'
        """
        # Critical infrastructure down = CRITICAL
        if infra_summary.get('critical_down', 0) > 0:
            return 'critical'

        # Any infrastructure down = DEGRADED
        if infra_summary.get('unhealthy', 0) > 0:
            return 'degraded'

        # Any service degraded/down = DEGRADED
        if service_summary.get('degraded', 0) > 0 or service_summary.get('down', 0) > 0:
            return 'degraded'

        # All good = HEALTHY
        return 'healthy'

    def _format_infrastructure_status(self, infrastructure_status: Dict) -> List[Dict[str, Any]]:
        """Format infrastructure status for response"""
        formatted = []

        for name, health in infrastructure_status.items():
            formatted.append({
                'name': name,
                'type': health.type,
                'status': health.status.value if hasattr(health.status, 'value') else health.status,
                'last_check': health.last_check,
                'response_time_ms': health.response_time_ms,
                'error': health.error,
                'critical': health.critical,
                'dependents': self.dependency_graph.get_dependents(name)
            })

        # Sort by critical first, then by name
        formatted.sort(key=lambda x: (not x['critical'], x['name']))

        return formatted

    def _format_service_status(self, service_status: Dict) -> List[Dict[str, Any]]:
        """Format service status for response"""
        formatted = []
        infrastructure_status = self.infrastructure_monitor.get_all_status()

        for name, info in service_status.items():
            # Get dependency chain
            chain = self.dependency_graph.get_dependency_chain(name)

            # Check dependency status
            dependency_status = {}
            degraded_reason = None

            if chain:
                for dep in chain.get('requires', []):
                    infra_name = dep['name']
                    if infra_name in infrastructure_status:
                        status = infrastructure_status[infra_name].status
                        dependency_status[infra_name] = status.value if hasattr(status, 'value') else str(status)

                        if status != InfrastructureStatus.HEALTHY:
                            degraded_reason = f"Required infrastructure {infra_name} is {status.value}"

                for dep in chain.get('optional', []):
                    infra_name = dep['name']
                    if infra_name in infrastructure_status:
                        status = infrastructure_status[infra_name].status
                        dependency_status[infra_name] = status.value if hasattr(status, 'value') else str(status)

                        if status != InfrastructureStatus.HEALTHY and not degraded_reason:
                            degraded_reason = f"Optional infrastructure {infra_name} is {status.value}"

            # Determine service status
            service_status_str = info.get('status', 'unknown')
            if degraded_reason:
                service_status_str = 'degraded'

            formatted.append({
                'name': name,
                'type': 'application',
                'status': service_status_str,
                'reason': degraded_reason,
                'last_heartbeat': info.get('last_seen'),
                'version': info.get('version'),
                'metadata': info.get('metadata', {}),
                'dependencies': {
                    'required': [d['name'] for d in chain.get('requires', [])] if chain else [],
                    'optional': [d['name'] for d in chain.get('optional', [])] if chain else [],
                    'status': dependency_status
                }
            })

        return formatted

    async def _get_impact_analysis(self, infrastructure_status: Dict, service_status: Dict) -> List[Dict[str, Any]]:
        """Get impact analysis for any failures"""
        impact_list = []

        # Analyze each unhealthy infrastructure
        for name, health in infrastructure_status.items():
            if health.status == InfrastructureStatus.UNHEALTHY:
                impact = self.dependency_graph.analyze_impact(name, 'infrastructure')
                impact_list.append(impact.to_dict())

        # Analyze each down service (future: service-to-service dependencies)
        for name, info in service_status.items():
            if info.get('status') != 'active':
                impact = self.dependency_graph.analyze_impact(name, 'service')
                if impact.affected_services:  # Only add if there are affected services
                    impact_list.append(impact.to_dict())

        return impact_list

    async def get_infrastructure_health(self) -> List[Dict[str, Any]]:
        """Get infrastructure health only"""
        infrastructure_status = self.infrastructure_monitor.get_all_status()
        return self._format_infrastructure_status(infrastructure_status)

    async def get_service_health(self) -> List[Dict[str, Any]]:
        """Get service health only"""
        service_status = self.service_registry.get_registry()
        return self._format_service_status(service_status)

    async def get_summary(self) -> Dict[str, Any]:
        """Get quick summary"""
        infrastructure_status = self.infrastructure_monitor.get_all_status()
        service_status = self.service_registry.get_registry()

        infra_summary = self._calculate_infrastructure_summary(infrastructure_status)
        service_summary = self._calculate_service_summary(service_status)
        overall_status = self._calculate_overall_status(infra_summary, service_summary)

        return {
            'overall_status': overall_status,
            'infrastructure': infra_summary,
            'services': service_summary,
            'timestamp': int(time.time() * 1000)
        }
