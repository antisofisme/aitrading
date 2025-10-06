"""
Dependency Graph - Tracks dependencies between infrastructure and services
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, List, Set, Optional
from collections import defaultdict

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

from models.infrastructure_model import DependencyNode, ImpactAnalysis

logger = logging.getLogger("central-hub.dependency-graph")


class DependencyGraph:
    """Manages dependency relationships and impact analysis"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or str(Path(__file__).parent.parent / "config" / "infrastructure.yaml")
        self.graph: Dict[str, DependencyNode] = {}
        self.service_dependencies: Dict[str, dict] = {}

    async def initialize(self):
        """Load dependency configuration and build graph"""
        logger.info("🔧 Initializing Dependency Graph...")

        # Load service dependencies from config
        await self._load_service_dependencies()

        # Build the graph
        self._build_graph()

        logger.info(f"✅ Dependency graph built with {len(self.graph)} nodes")

    async def _load_service_dependencies(self):
        """Load service dependencies from YAML config"""
        try:
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)

            self.service_dependencies = config_data.get('service_dependencies', {})

            logger.info(f"✅ Loaded dependencies for {len(self.service_dependencies)} services")

        except Exception as e:
            logger.error(f"❌ Failed to load service dependencies: {e}", exc_info=True)
            raise

    def _build_graph(self):
        """Build bidirectional dependency graph"""
        # First, create nodes for all infrastructure (from config)
        try:
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)

            # Add infrastructure nodes
            for category in ['databases', 'messaging', 'search']:
                for name in config_data.get(category, {}).keys():
                    if name not in self.graph:
                        self.graph[name] = DependencyNode(
                            name=name,
                            type='infrastructure'
                        )

        except Exception as e:
            logger.error(f"❌ Error building infrastructure nodes: {e}")

        # Add service nodes and connect dependencies
        for service_name, deps in self.service_dependencies.items():
            # Create service node if not exists
            if service_name not in self.graph:
                self.graph[service_name] = DependencyNode(
                    name=service_name,
                    type='service'
                )

            service_node = self.graph[service_name]

            # Process required dependencies
            for infra_name in deps.get('requires', []):
                # Add to service's depends_on
                service_node.depends_on.append(infra_name)

                # Add to infrastructure's dependents (reverse link)
                if infra_name in self.graph:
                    if service_name not in self.graph[infra_name].required_by:
                        self.graph[infra_name].required_by.append(service_name)
                    if service_name not in self.graph[infra_name].dependents:
                        self.graph[infra_name].dependents.append(service_name)

            # Process optional dependencies
            for infra_name in deps.get('optional', []):
                # Add to service's depends_on (but mark as optional elsewhere)
                if infra_name not in service_node.depends_on:
                    service_node.depends_on.append(infra_name)

                # Add to infrastructure's optional_for (reverse link)
                if infra_name in self.graph:
                    if service_name not in self.graph[infra_name].optional_for:
                        self.graph[infra_name].optional_for.append(service_name)
                    if service_name not in self.graph[infra_name].dependents:
                        self.graph[infra_name].dependents.append(service_name)

        logger.info(f"✅ Built dependency graph with {len(self.graph)} nodes")

    def analyze_impact(self, failed_component: str, component_type: str = 'infrastructure') -> ImpactAnalysis:
        """
        Analyze impact of component failure

        Args:
            failed_component: Name of failed component
            component_type: 'infrastructure' or 'service'

        Returns:
            ImpactAnalysis with affected services and recommendations
        """
        if failed_component not in self.graph:
            logger.warning(f"⚠️ Component not in graph: {failed_component}")
            return ImpactAnalysis(
                failed_component=failed_component,
                component_type=component_type,
                impact_level='none',
                affected_services=[],
                recommendations=[f"Component {failed_component} not found in dependency graph"]
            )

        node = self.graph[failed_component]
        affected_services = []
        impact_level = 'none'

        # Get services that depend on this component
        if component_type == 'infrastructure':
            # Check required dependencies (critical impact)
            for service_name in node.required_by:
                affected_services.append({
                    'service': service_name,
                    'impact': 'degraded',
                    'reason': f'Required infrastructure {failed_component} is down'
                })
                impact_level = 'critical'

            # Check optional dependencies (warning impact)
            for service_name in node.optional_for:
                if service_name not in [s['service'] for s in affected_services]:
                    affected_services.append({
                        'service': service_name,
                        'impact': 'warning',
                        'reason': f'Optional infrastructure {failed_component} is down'
                    })
                    if impact_level == 'none':
                        impact_level = 'warning'

        elif component_type == 'service':
            # Service failure - check downstream services
            # (Currently no service-to-service dependencies, but prepared for future)
            pass

        # Generate recommendations
        recommendations = self._generate_recommendations(
            failed_component,
            component_type,
            affected_services
        )

        return ImpactAnalysis(
            failed_component=failed_component,
            component_type=component_type,
            impact_level=impact_level,
            affected_services=affected_services,
            recommendations=recommendations
        )

    def _generate_recommendations(self, component: str, component_type: str, affected_services: List[dict]) -> List[str]:
        """Generate recommendations for handling failure"""
        recommendations = []

        if component_type == 'infrastructure':
            recommendations.append(f"Check {component} container logs: docker logs suho-{component}")
            recommendations.append(f"Restart {component}: docker-compose restart {component}")

            if affected_services:
                service_names = [s['service'] for s in affected_services if s['impact'] == 'degraded']
                if service_names:
                    recommendations.append(f"Affected services may need restart after {component} recovery: {', '.join(service_names)}")

        return recommendations

    def get_dependency_chain(self, service_name: str) -> Dict:
        """
        Get complete dependency chain for a service

        Args:
            service_name: Service name

        Returns:
            Dictionary with complete dependency tree
        """
        if service_name not in self.graph:
            return {}

        node = self.graph[service_name]
        if node.type != 'service':
            return {}

        # Get service dependencies
        service_deps = self.service_dependencies.get(service_name, {})

        chain = {
            'service': service_name,
            'type': 'service',
            'requires': [],
            'optional': []
        }

        # Add required dependencies with their status
        for infra_name in service_deps.get('requires', []):
            if infra_name in self.graph:
                chain['requires'].append({
                    'name': infra_name,
                    'type': 'infrastructure',
                    # Status will be added by aggregator
                })

        # Add optional dependencies
        for infra_name in service_deps.get('optional', []):
            if infra_name in self.graph:
                chain['optional'].append({
                    'name': infra_name,
                    'type': 'infrastructure',
                })

        return chain

    def get_dependents(self, component_name: str) -> List[str]:
        """Get list of services that depend on this component"""
        if component_name not in self.graph:
            return []

        return self.graph[component_name].dependents

    def get_graph_data(self) -> Dict:
        """Get complete graph data for visualization"""
        nodes = []
        edges = []

        for name, node in self.graph.items():
            nodes.append({
                'id': name,
                'name': name,
                'type': node.type
            })

            # Add edges for dependencies
            for dep in node.depends_on:
                edges.append({
                    'source': name,
                    'target': dep,
                    'type': 'depends_on'
                })

        return {
            'nodes': nodes,
            'edges': edges
        }

    def is_service_affected_by(self, service_name: str, infrastructure_name: str) -> Optional[str]:
        """
        Check if service is affected by infrastructure failure

        Args:
            service_name: Service to check
            infrastructure_name: Failed infrastructure

        Returns:
            'critical' if required, 'warning' if optional, None if not affected
        """
        if service_name not in self.service_dependencies:
            return None

        deps = self.service_dependencies[service_name]

        if infrastructure_name in deps.get('requires', []):
            return 'critical'
        elif infrastructure_name in deps.get('optional', []):
            return 'warning'

        return None

    def add_service_dynamically(self, service_name: str, requires: List[str], optional: List[str]):
        """
        Add service to graph dynamically (when service registers)

        Args:
            service_name: Service name
            requires: List of required infrastructure
            optional: List of optional infrastructure
        """
        # Add to service dependencies
        self.service_dependencies[service_name] = {
            'requires': requires,
            'optional': optional
        }

        # Rebuild graph
        self._build_graph()

        logger.info(f"✅ Added service to dependency graph: {service_name}")
