"""
Service Registry and Discovery System
Level 2 Connectivity - Service Registry Implementation
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import aioredis
import aiohttp
from pydantic import BaseModel, Field
import hashlib
import secrets
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    """Service health status"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"

class ServiceType(Enum):
    """Service types in the trading platform"""
    API_GATEWAY = "api-gateway"
    AUTH_SERVICE = "auth-service"
    TRADING_ENGINE = "trading-engine"
    DATA_BRIDGE = "data-bridge"
    AI_ENSEMBLE = "ai-ensemble"
    STRATEGY_ENGINE = "strategy-engine"
    RISK_MANAGER = "risk-manager"
    DATABASE_SERVICE = "database-service"
    NOTIFICATION_SERVICE = "notification-service"
    MONITORING_SERVICE = "monitoring-service"

@dataclass
class ServiceInstance:
    """Service instance information"""
    service_id: str
    service_name: str
    service_type: ServiceType
    host: str
    port: int
    version: str
    status: ServiceStatus
    health_check_url: str
    metadata: Dict[str, Any]
    tags: Set[str]
    registered_at: datetime
    last_heartbeat: datetime
    capabilities: List[str]
    dependencies: List[str]
    load_metrics: Dict[str, float]

@dataclass
class ServiceHealth:
    """Service health information"""
    service_id: str
    status: ServiceStatus
    response_time_ms: float
    error_rate: float
    uptime_seconds: int
    last_check: datetime
    details: Dict[str, Any]

class ServiceRegistration(BaseModel):
    """Service registration request"""
    service_name: str = Field(..., min_length=1, max_length=100)
    service_type: ServiceType
    host: str = Field(..., regex=r'^[a-zA-Z0-9.-]+$')
    port: int = Field(..., ge=1, le=65535)
    version: str = Field(default="1.0.0")
    health_check_url: str
    metadata: Dict[str, Any] = {}
    tags: Set[str] = set()
    capabilities: List[str] = []
    dependencies: List[str] = []

class ServiceQuery(BaseModel):
    """Service query parameters"""
    service_type: Optional[ServiceType] = None
    service_name: Optional[str] = None
    tags: Set[str] = set()
    status: Optional[ServiceStatus] = None
    capabilities: List[str] = []

class LoadBalancingStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    HEALTH_BASED = "health_based"
    GEOGRAPHIC = "geographic"

class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

@dataclass
class CircuitBreaker:
    """Circuit breaker for service calls"""
    service_id: str
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    half_open_max_calls: int = 3

class ServiceRegistry:
    """Distributed service registry with health monitoring"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None
        self.services: Dict[str, ServiceInstance] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.health_check_interval = 30  # seconds
        self.heartbeat_timeout = 90  # seconds
        self.cleanup_interval = 300  # seconds

        # Monitoring
        self.health_check_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None

        # Load balancing
        self.round_robin_counters: Dict[str, int] = {}

        logger.info("Service Registry initialized")

    async def initialize(self):
        """Initialize the service registry"""
        try:
            self.redis = aioredis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()

            # Start background tasks
            self.health_check_task = asyncio.create_task(self._health_check_loop())
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())

            logger.info("Service Registry fully initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Service Registry: {e}")
            raise

    async def shutdown(self):
        """Shutdown the service registry"""
        if self.health_check_task:
            self.health_check_task.cancel()
        if self.cleanup_task:
            self.cleanup_task.cancel()

        if self.redis:
            await self.redis.close()

        logger.info("Service Registry shutdown complete")

    async def register_service(self, registration: ServiceRegistration) -> str:
        """Register a new service instance"""
        try:
            # Generate unique service ID
            service_id = self._generate_service_id(registration)

            # Create service instance
            service_instance = ServiceInstance(
                service_id=service_id,
                service_name=registration.service_name,
                service_type=registration.service_type,
                host=registration.host,
                port=registration.port,
                version=registration.version,
                status=ServiceStatus.UNKNOWN,
                health_check_url=registration.health_check_url,
                metadata=registration.metadata,
                tags=registration.tags,
                registered_at=datetime.utcnow(),
                last_heartbeat=datetime.utcnow(),
                capabilities=registration.capabilities,
                dependencies=registration.dependencies,
                load_metrics={}
            )

            # Store in local cache
            self.services[service_id] = service_instance

            # Store in Redis
            await self._store_service_in_redis(service_instance)

            # Initialize circuit breaker
            self.circuit_breakers[service_id] = CircuitBreaker(service_id=service_id)

            # Perform initial health check
            await self._check_service_health(service_instance)

            logger.info(f"Service registered: {service_id} ({registration.service_name})")
            return service_id

        except Exception as e:
            logger.error(f"Failed to register service: {e}")
            raise

    async def deregister_service(self, service_id: str):
        """Deregister a service instance"""
        try:
            # Remove from local cache
            if service_id in self.services:
                del self.services[service_id]

            # Remove from Redis
            await self.redis.delete(f"service:{service_id}")
            await self.redis.srem("services:all", service_id)

            # Remove circuit breaker
            if service_id in self.circuit_breakers:
                del self.circuit_breakers[service_id]

            logger.info(f"Service deregistered: {service_id}")

        except Exception as e:
            logger.error(f"Failed to deregister service {service_id}: {e}")

    async def discover_services(self, query: ServiceQuery) -> List[ServiceInstance]:
        """Discover services based on query criteria"""
        try:
            # Get all services
            matching_services = []

            for service in self.services.values():
                if self._matches_query(service, query):
                    matching_services.append(service)

            # Sort by health and load
            matching_services.sort(key=lambda s: (
                s.status == ServiceStatus.HEALTHY,
                -s.load_metrics.get('cpu_usage', 0),
                -s.load_metrics.get('response_time', 0)
            ), reverse=True)

            logger.debug(f"Discovered {len(matching_services)} services for query")
            return matching_services

        except Exception as e:
            logger.error(f"Service discovery failed: {e}")
            return []

    async def get_service_instance(self, service_id: str) -> Optional[ServiceInstance]:
        """Get specific service instance"""
        return self.services.get(service_id)

    async def get_healthy_instance(self, service_type: ServiceType,
                                 strategy: LoadBalancingStrategy = LoadBalancingStrategy.HEALTH_BASED) -> Optional[ServiceInstance]:
        """Get a healthy service instance using load balancing"""
        try:
            # Find healthy services of the requested type
            healthy_services = [
                service for service in self.services.values()
                if service.service_type == service_type and service.status == ServiceStatus.HEALTHY
            ]

            if not healthy_services:
                logger.warning(f"No healthy services found for type: {service_type}")
                return None

            # Apply load balancing strategy
            return await self._apply_load_balancing(healthy_services, strategy)

        except Exception as e:
            logger.error(f"Failed to get healthy instance: {e}")
            return None

    async def update_service_health(self, service_id: str, health: ServiceHealth):
        """Update service health information"""
        try:
            if service_id in self.services:
                service = self.services[service_id]
                service.status = health.status
                service.last_heartbeat = datetime.utcnow()
                service.load_metrics.update({
                    'response_time': health.response_time_ms,
                    'error_rate': health.error_rate,
                    'uptime': health.uptime_seconds
                })

                # Update in Redis
                await self._store_service_in_redis(service)

                logger.debug(f"Health updated for service: {service_id}")

        except Exception as e:
            logger.error(f"Failed to update service health: {e}")

    async def heartbeat(self, service_id: str, load_metrics: Dict[str, float] = None):
        """Service heartbeat to maintain registration"""
        try:
            if service_id in self.services:
                service = self.services[service_id]
                service.last_heartbeat = datetime.utcnow()

                if load_metrics:
                    service.load_metrics.update(load_metrics)

                # Update in Redis
                await self._store_service_in_redis(service)

                logger.debug(f"Heartbeat received from service: {service_id}")

        except Exception as e:
            logger.error(f"Failed to process heartbeat: {e}")

    async def get_service_dependencies(self, service_id: str) -> List[ServiceInstance]:
        """Get dependencies for a service"""
        try:
            service = self.services.get(service_id)
            if not service:
                return []

            dependencies = []
            for dep_name in service.dependencies:
                dep_services = await self.discover_services(
                    ServiceQuery(service_name=dep_name, status=ServiceStatus.HEALTHY)
                )
                dependencies.extend(dep_services)

            return dependencies

        except Exception as e:
            logger.error(f"Failed to get dependencies: {e}")
            return []

    async def call_service(self, service_id: str, endpoint: str, method: str = "GET",
                          data: Any = None, timeout: int = 30) -> Any:
        """Make a call to a service with circuit breaker protection"""
        try:
            circuit_breaker = self.circuit_breakers.get(service_id)
            if not circuit_breaker:
                raise Exception(f"No circuit breaker found for service: {service_id}")

            # Check circuit breaker state
            if not await self._can_make_call(circuit_breaker):
                raise Exception(f"Circuit breaker is OPEN for service: {service_id}")

            service = self.services.get(service_id)
            if not service:
                raise Exception(f"Service not found: {service_id}")

            # Make the call
            url = f"http://{service.host}:{service.port}{endpoint}"

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                start_time = time.time()

                if method.upper() == "GET":
                    async with session.get(url) as response:
                        result = await response.json()
                elif method.upper() == "POST":
                    async with session.post(url, json=data) as response:
                        result = await response.json()
                else:
                    raise Exception(f"Unsupported HTTP method: {method}")

                response_time = (time.time() - start_time) * 1000

                # Record success
                await self._record_call_success(circuit_breaker, response_time)

                return result

        except Exception as e:
            # Record failure
            if circuit_breaker:
                await self._record_call_failure(circuit_breaker)

            logger.error(f"Service call failed: {e}")
            raise

    def _generate_service_id(self, registration: ServiceRegistration) -> str:
        """Generate unique service ID"""
        timestamp = str(int(time.time()))
        unique_str = f"{registration.service_name}:{registration.host}:{registration.port}:{timestamp}"
        return hashlib.md5(unique_str.encode()).hexdigest()[:16]

    async def _store_service_in_redis(self, service: ServiceInstance):
        """Store service instance in Redis"""
        service_data = {
            'service_id': service.service_id,
            'service_name': service.service_name,
            'service_type': service.service_type.value,
            'host': service.host,
            'port': service.port,
            'version': service.version,
            'status': service.status.value,
            'health_check_url': service.health_check_url,
            'metadata': json.dumps(service.metadata),
            'tags': json.dumps(list(service.tags)),
            'registered_at': service.registered_at.isoformat(),
            'last_heartbeat': service.last_heartbeat.isoformat(),
            'capabilities': json.dumps(service.capabilities),
            'dependencies': json.dumps(service.dependencies),
            'load_metrics': json.dumps(service.load_metrics)
        }

        await self.redis.hset(f"service:{service.service_id}", mapping=service_data)
        await self.redis.sadd("services:all", service.service_id)
        await self.redis.expire(f"service:{service.service_id}", self.heartbeat_timeout)

    def _matches_query(self, service: ServiceInstance, query: ServiceQuery) -> bool:
        """Check if service matches query criteria"""
        if query.service_type and service.service_type != query.service_type:
            return False

        if query.service_name and service.service_name != query.service_name:
            return False

        if query.status and service.status != query.status:
            return False

        if query.tags and not query.tags.issubset(service.tags):
            return False

        if query.capabilities:
            if not all(cap in service.capabilities for cap in query.capabilities):
                return False

        return True

    async def _apply_load_balancing(self, services: List[ServiceInstance],
                                  strategy: LoadBalancingStrategy) -> ServiceInstance:
        """Apply load balancing strategy"""
        if not services:
            return None

        if strategy == LoadBalancingStrategy.ROUND_ROBIN:
            service_type = services[0].service_type.value
            counter = self.round_robin_counters.get(service_type, 0)
            selected = services[counter % len(services)]
            self.round_robin_counters[service_type] = counter + 1
            return selected

        elif strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            # Simplified: use service with lowest CPU usage
            return min(services, key=lambda s: s.load_metrics.get('cpu_usage', 0))

        elif strategy == LoadBalancingStrategy.HEALTH_BASED:
            # Weight by response time and error rate
            def health_score(service):
                response_time = service.load_metrics.get('response_time', 100)
                error_rate = service.load_metrics.get('error_rate', 0)
                return response_time + (error_rate * 1000)

            return min(services, key=health_score)

        else:
            # Default to first healthy service
            return services[0]

    async def _check_service_health(self, service: ServiceInstance):
        """Check individual service health"""
        try:
            url = f"http://{service.host}:{service.port}{service.health_check_url}"

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                start_time = time.time()
                async with session.get(url) as response:
                    response_time = (time.time() - start_time) * 1000

                    if response.status == 200:
                        service.status = ServiceStatus.HEALTHY
                        service.load_metrics['response_time'] = response_time
                    else:
                        service.status = ServiceStatus.UNHEALTHY

                    service.last_heartbeat = datetime.utcnow()

        except Exception as e:
            service.status = ServiceStatus.UNHEALTHY
            logger.warning(f"Health check failed for {service.service_id}: {e}")

    async def _health_check_loop(self):
        """Background health check loop"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)

                # Check all registered services
                for service in list(self.services.values()):
                    await self._check_service_health(service)
                    await self._store_service_in_redis(service)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")

    async def _cleanup_loop(self):
        """Background cleanup of stale services"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)

                current_time = datetime.utcnow()
                stale_services = []

                for service_id, service in self.services.items():
                    time_since_heartbeat = (current_time - service.last_heartbeat).total_seconds()
                    if time_since_heartbeat > self.heartbeat_timeout:
                        stale_services.append(service_id)

                # Remove stale services
                for service_id in stale_services:
                    await self.deregister_service(service_id)
                    logger.info(f"Removed stale service: {service_id}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")

    async def _can_make_call(self, circuit_breaker: CircuitBreaker) -> bool:
        """Check if circuit breaker allows calls"""
        if circuit_breaker.state == CircuitBreakerState.CLOSED:
            return True

        if circuit_breaker.state == CircuitBreakerState.OPEN:
            if circuit_breaker.last_failure_time:
                time_since_failure = (datetime.utcnow() - circuit_breaker.last_failure_time).total_seconds()
                if time_since_failure > circuit_breaker.recovery_timeout:
                    circuit_breaker.state = CircuitBreakerState.HALF_OPEN
                    circuit_breaker.success_count = 0
                    return True
            return False

        if circuit_breaker.state == CircuitBreakerState.HALF_OPEN:
            return circuit_breaker.success_count < circuit_breaker.half_open_max_calls

        return False

    async def _record_call_success(self, circuit_breaker: CircuitBreaker, response_time: float):
        """Record successful service call"""
        if circuit_breaker.state == CircuitBreakerState.HALF_OPEN:
            circuit_breaker.success_count += 1
            if circuit_breaker.success_count >= circuit_breaker.half_open_max_calls:
                circuit_breaker.state = CircuitBreakerState.CLOSED
                circuit_breaker.failure_count = 0

        elif circuit_breaker.state == CircuitBreakerState.CLOSED:
            circuit_breaker.failure_count = max(0, circuit_breaker.failure_count - 1)

    async def _record_call_failure(self, circuit_breaker: CircuitBreaker):
        """Record failed service call"""
        circuit_breaker.failure_count += 1
        circuit_breaker.last_failure_time = datetime.utcnow()

        if circuit_breaker.state == CircuitBreakerState.HALF_OPEN:
            circuit_breaker.state = CircuitBreakerState.OPEN

        elif circuit_breaker.state == CircuitBreakerState.CLOSED:
            if circuit_breaker.failure_count >= circuit_breaker.failure_threshold:
                circuit_breaker.state = CircuitBreakerState.OPEN

    async def get_registry_stats(self) -> Dict[str, Any]:
        """Get service registry statistics"""
        total_services = len(self.services)
        healthy_services = sum(1 for s in self.services.values() if s.status == ServiceStatus.HEALTHY)
        unhealthy_services = sum(1 for s in self.services.values() if s.status == ServiceStatus.UNHEALTHY)

        service_types = {}
        for service in self.services.values():
            service_type = service.service_type.value
            service_types[service_type] = service_types.get(service_type, 0) + 1

        return {
            'total_services': total_services,
            'healthy_services': healthy_services,
            'unhealthy_services': unhealthy_services,
            'service_types': service_types,
            'registry_uptime': time.time(),
            'last_cleanup': datetime.utcnow().isoformat()
        }

# Global service registry instance
service_registry = None

async def get_service_registry() -> ServiceRegistry:
    """Get service registry instance"""
    global service_registry
    if service_registry is None:
        service_registry = ServiceRegistry()
        await service_registry.initialize()
    return service_registry

# Context manager for service registration
@asynccontextmanager
async def register_service_context(registration: ServiceRegistration):
    """Context manager for automatic service registration/deregistration"""
    registry = await get_service_registry()
    service_id = await registry.register_service(registration)

    try:
        yield service_id
    finally:
        await registry.deregister_service(service_id)

# Export main components
__all__ = [
    'ServiceRegistry',
    'ServiceRegistration',
    'ServiceQuery',
    'ServiceInstance',
    'ServiceHealth',
    'ServiceStatus',
    'ServiceType',
    'LoadBalancingStrategy',
    'get_service_registry',
    'register_service_context'
]