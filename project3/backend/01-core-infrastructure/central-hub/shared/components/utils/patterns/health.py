"""
Health Checker untuk semua services
Menyediakan consistent health check patterns dengan aggregation
"""

import asyncio
import time
import logging as python_logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class HealthStatus(Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Health status for a single component"""
    name: str
    status: HealthStatus
    message: Optional[str] = None
    response_time_ms: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[int] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = int(time.time() * 1000)
        if isinstance(self.status, str):
            self.status = HealthStatus(self.status)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "response_time_ms": self.response_time_ms,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


@dataclass
class AggregatedHealth:
    """Aggregated health status"""
    overall_status: HealthStatus
    components: List[ComponentHealth]
    total_components: int
    healthy_count: int
    degraded_count: int
    unhealthy_count: int
    timestamp: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "overall_status": self.overall_status.value,
            "components": [c.to_dict() for c in self.components],
            "total_components": self.total_components,
            "healthy_count": self.healthy_count,
            "degraded_count": self.degraded_count,
            "unhealthy_count": self.unhealthy_count,
            "timestamp": self.timestamp
        }


class HealthChecker:
    """
    Health checker untuk semua services
    Mendukung multiple components dengan aggregation logic
    """

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.components: Dict[str, Callable] = {}
        self.logger = python_logging.getLogger(f"{service_name}.health")

    def register_component(self, name: str, health_check_func: Callable):
        """
        Register a component with its health check function

        Args:
            name: Component name (e.g., "database", "cache", "messaging")
            health_check_func: Async function that returns ComponentHealth or dict
        """
        self.components[name] = health_check_func
        self.logger.info(f"Registered health check for component: {name}")

    def unregister_component(self, name: str):
        """Unregister a component"""
        if name in self.components:
            del self.components[name]
            self.logger.info(f"Unregistered health check for component: {name}")

    async def check_component(self, name: str) -> ComponentHealth:
        """
        Check health of a single component

        Args:
            name: Component name

        Returns:
            ComponentHealth object
        """
        if name not in self.components:
            return ComponentHealth(
                name=name,
                status=HealthStatus.UNKNOWN,
                message=f"Component '{name}' not registered"
            )

        start_time = time.time()

        try:
            health_check_func = self.components[name]

            # Call the health check function
            if asyncio.iscoroutinefunction(health_check_func):
                result = await health_check_func()
            else:
                result = health_check_func()

            response_time = (time.time() - start_time) * 1000

            # Convert dict to ComponentHealth if needed
            if isinstance(result, dict):
                result.setdefault("name", name)
                result.setdefault("response_time_ms", response_time)
                return ComponentHealth(**result)
            elif isinstance(result, ComponentHealth):
                if result.response_time_ms is None:
                    result.response_time_ms = response_time
                return result
            else:
                return ComponentHealth(
                    name=name,
                    status=HealthStatus.HEALTHY,
                    response_time_ms=response_time
                )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.logger.error(f"Health check failed for {name}: {str(e)}")

            return ComponentHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check error: {str(e)}",
                response_time_ms=response_time
            )

    async def check_all(self, parallel: bool = True) -> AggregatedHealth:
        """
        Check health of all registered components

        Args:
            parallel: Run health checks in parallel (default: True)

        Returns:
            AggregatedHealth object with overall status
        """
        if not self.components:
            return AggregatedHealth(
                overall_status=HealthStatus.UNKNOWN,
                components=[],
                total_components=0,
                healthy_count=0,
                degraded_count=0,
                unhealthy_count=0,
                timestamp=int(time.time() * 1000)
            )

        # Run health checks
        if parallel:
            # Parallel execution
            tasks = [
                self.check_component(name)
                for name in self.components.keys()
            ]
            component_results = await asyncio.gather(*tasks)
        else:
            # Sequential execution
            component_results = []
            for name in self.components.keys():
                result = await self.check_component(name)
                component_results.append(result)

        # Count status
        healthy_count = sum(1 for c in component_results if c.status == HealthStatus.HEALTHY)
        degraded_count = sum(1 for c in component_results if c.status == HealthStatus.DEGRADED)
        unhealthy_count = sum(1 for c in component_results if c.status == HealthStatus.UNHEALTHY)
        total = len(component_results)

        # Determine overall status
        if unhealthy_count > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            overall_status = HealthStatus.DEGRADED
        elif healthy_count == total:
            overall_status = HealthStatus.HEALTHY
        else:
            overall_status = HealthStatus.UNKNOWN

        return AggregatedHealth(
            overall_status=overall_status,
            components=component_results,
            total_components=total,
            healthy_count=healthy_count,
            degraded_count=degraded_count,
            unhealthy_count=unhealthy_count,
            timestamp=int(time.time() * 1000)
        )

    async def get_component_health(self, name: str) -> Optional[ComponentHealth]:
        """Get health status of specific component"""
        if name not in self.components:
            return None
        return await self.check_component(name)

    def get_registered_components(self) -> List[str]:
        """Get list of registered components"""
        return list(self.components.keys())

    async def is_healthy(self) -> bool:
        """Quick check if service is healthy"""
        health = await self.check_all(parallel=True)
        return health.overall_status == HealthStatus.HEALTHY

    async def is_ready(self) -> bool:
        """
        Check if service is ready (healthy or degraded)
        Used for Kubernetes readiness probes
        """
        health = await self.check_all(parallel=True)
        return health.overall_status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]

    async def is_alive(self) -> bool:
        """
        Check if service is alive (not unhealthy)
        Used for Kubernetes liveness probes
        """
        health = await self.check_all(parallel=True)
        return health.overall_status != HealthStatus.UNHEALTHY


# Common health check helpers
async def check_database_health(connection, query: str = "SELECT 1") -> ComponentHealth:
    """
    Generic database health check

    Args:
        connection: Database connection/pool
        query: Test query (default: SELECT 1)

    Returns:
        ComponentHealth object
    """
    start_time = time.time()

    try:
        # Try to execute test query
        if hasattr(connection, 'execute'):
            await connection.execute(query)
        elif hasattr(connection, 'fetchval'):
            await connection.fetchval(query)
        else:
            # For pool connections
            async with connection.acquire() as conn:
                await conn.fetchval(query)

        response_time = (time.time() - start_time) * 1000

        return ComponentHealth(
            name="database",
            status=HealthStatus.HEALTHY,
            message="Database connection OK",
            response_time_ms=response_time
        )

    except Exception as e:
        response_time = (time.time() - start_time) * 1000

        return ComponentHealth(
            name="database",
            status=HealthStatus.UNHEALTHY,
            message=f"Database error: {str(e)}",
            response_time_ms=response_time
        )


async def check_cache_health(cache_client) -> ComponentHealth:
    """
    Generic cache health check

    Args:
        cache_client: Redis/DragonflyDB client

    Returns:
        ComponentHealth object
    """
    start_time = time.time()

    try:
        # Try to ping cache
        if hasattr(cache_client, 'ping'):
            await cache_client.ping()
        elif hasattr(cache_client, 'health_check'):
            result = await cache_client.health_check()
            if isinstance(result, dict) and result.get("status") == "unhealthy":
                return ComponentHealth(
                    name="cache",
                    status=HealthStatus.UNHEALTHY,
                    message=result.get("error", "Cache unhealthy"),
                    response_time_ms=(time.time() - start_time) * 1000
                )

        response_time = (time.time() - start_time) * 1000

        return ComponentHealth(
            name="cache",
            status=HealthStatus.HEALTHY,
            message="Cache connection OK",
            response_time_ms=response_time
        )

    except Exception as e:
        response_time = (time.time() - start_time) * 1000

        return ComponentHealth(
            name="cache",
            status=HealthStatus.UNHEALTHY,
            message=f"Cache error: {str(e)}",
            response_time_ms=response_time
        )


async def check_messaging_health(messaging_client, client_type: str = "nats") -> ComponentHealth:
    """
    Generic messaging health check

    Args:
        messaging_client: NATS/Kafka client
        client_type: Type of messaging client ("nats" or "kafka")

    Returns:
        ComponentHealth object
    """
    start_time = time.time()

    try:
        # Check connection status
        if client_type.lower() == "nats":
            if hasattr(messaging_client, 'is_connected') and not messaging_client.is_connected:
                raise Exception("NATS not connected")
        elif client_type.lower() == "kafka":
            if hasattr(messaging_client, 'bootstrap_connected'):
                if not await messaging_client.bootstrap_connected():
                    raise Exception("Kafka not connected")

        response_time = (time.time() - start_time) * 1000

        return ComponentHealth(
            name=f"messaging_{client_type}",
            status=HealthStatus.HEALTHY,
            message=f"{client_type.upper()} connection OK",
            response_time_ms=response_time
        )

    except Exception as e:
        response_time = (time.time() - start_time) * 1000

        return ComponentHealth(
            name=f"messaging_{client_type}",
            status=HealthStatus.UNHEALTHY,
            message=f"{client_type.upper()} error: {str(e)}",
            response_time_ms=response_time
        )
