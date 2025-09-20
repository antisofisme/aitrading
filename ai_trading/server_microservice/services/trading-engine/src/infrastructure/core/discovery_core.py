"""
AI Brain Enhanced Service Discovery Core - Architecture-validated service discovery
Enhanced with AI Brain Architecture Standards for systematic service validation
"""

import asyncio
import time
import json
import hashlib
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable, Set
from enum import Enum
from dataclasses import dataclass, field
from ..base.base_logger import BaseLogger
from ..base.base_performance import BasePerformance

# AI Brain Integration
try:
    import sys
    sys.path.append('/mnt/f/WINDSURF/concept_ai/projects/ai_trading/server_microservice/services')
    from shared.ai_brain_confidence_framework import AiBrainConfidenceFramework
    from shared.ai_brain_trading_error_dna import AiBrainTradingErrorDNA
    AI_BRAIN_AVAILABLE = True
except ImportError:
    AI_BRAIN_AVAILABLE = False

class ServiceStatus(Enum):
    """Service status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    STARTING = "starting"
    STOPPING = "stopping"

class ServiceType(Enum):
    """Service type enumeration"""
    API_GATEWAY = "api-gateway"
    AI_PROVIDER = "ai-provider"
    AI_ORCHESTRATION = "ai-orchestration"
    DATABASE_SERVICE = "database-service"
    DATA_BRIDGE = "data-bridge"
    DEEP_LEARNING = "deep-learning"
    ML_PROCESSING = "ml-processing"
    TRADING_ENGINE = "trading-engine"
    USER_SERVICE = "user-service"
    EXTERNAL = "external"

@dataclass
class ServiceInstance:
    """Service instance definition"""
    instance_id: str
    service_name: str
    service_type: ServiceType
    host: str
    port: int
    protocol: str = "http"
    version: str = "1.0.0"
    environment: str = "development"
    status: ServiceStatus = ServiceStatus.UNKNOWN
    health_check_url: str = "/health"
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    last_heartbeat: Optional[datetime] = None
    registration_time: Optional[datetime] = None
    capabilities: List[str] = field(default_factory=list)
    load_factor: float = 0.0
    response_time_ms: float = 0.0
    
    # AI Brain Architecture Validation
    architecture_validation: Optional[ArchitectureValidationResult] = None
    service_contract_url: Optional[str] = None
    api_version: str = "v1"

    @property
    def base_url(self) -> str:
        """Get base URL for this service instance"""
        return f"{self.protocol}://{self.host}:{self.port}"
    
    @property
    def health_url(self) -> str:
        """Get health check URL for this service instance"""
        return f"{self.base_url}{self.health_check_url}"
    
    @property
    def is_healthy(self) -> bool:
        """Check if service instance is healthy"""
        return self.status == ServiceStatus.HEALTHY
    
    @property
    def is_available(self) -> bool:
        """Check if service instance is available for requests"""
        return self.status in [ServiceStatus.HEALTHY, ServiceStatus.DEGRADED]
    
    @property
    def is_architecture_compliant(self) -> bool:
        """Check if service instance is architecture compliant"""
        if not self.architecture_validation:
            return False  # Default to non-compliant if not validated
        return self.architecture_validation.is_compliant

@dataclass
class ArchitectureValidationResult:
    """Result of AI Brain architecture validation for services"""
    is_compliant: bool
    architecture_score: float
    violations: List[Dict[str, Any]]
    recommendations: List[str]
    ai_brain_confidence: float
    naming_violations: List[Dict[str, Any]]
    endpoint_consistency_issues: List[Dict[str, Any]]
    validation_timestamp: str
    service_pattern_compliance: float

@dataclass
class ServiceDiscoveryConfig:
    """Service discovery configuration"""
    heartbeat_interval: float = 30.0
    health_check_timeout: float = 5.0
    instance_ttl: float = 180.0  # 3 minutes
    cleanup_interval: float = 60.0
    max_health_check_failures: int = 3
    service_mesh_enabled: bool = False
    load_balancing_strategy: str = "round_robin"  # round_robin, least_connections, weighted
    
    # AI Brain Architecture Standards
    architecture_validation_enabled: bool = True
    enforce_naming_conventions: bool = True
    validate_endpoint_consistency: bool = True
    require_service_contracts: bool = True

class DiscoveryCore:
    """
    AI Brain Enhanced service discovery implementation for microservices.
    
    Features:
    - Service registration and deregistration
    - Health-aware service discovery
    - Load balancing with multiple strategies
    - Service mesh integration support
    - Automatic cleanup of stale instances
    - Circuit breaker pattern for failed services
    - Real-time service monitoring
    - AI Brain Architecture Standards validation
    - Service naming convention enforcement
    - Endpoint consistency checking
    - API contract validation
    """
    
    def __init__(self, service_name: str, config: Optional[ServiceDiscoveryConfig] = None):
        """
        Initialize service discovery for a service.
        
        Args:
            service_name: Name of the current service
            config: Service discovery configuration
        """
        self.service_name = service_name
        self.config = config or ServiceDiscoveryConfig()
        
        # Service registry (in production, this would be Redis/etcd/Consul)
        self.service_registry: Dict[str, Dict[str, ServiceInstance]] = {}
        self.instance_health_history: Dict[str, List[bool]] = {}
        
        # Load balancing state
        self.round_robin_indices: Dict[str, int] = {}
        
        # Monitoring state
        self.is_running = False
        self._monitoring_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Initialize logging and performance tracking
        self.logger = BaseLogger(service_name, "discovery_core")
        self.performance_tracker = BasePerformance(service_name)
        
        # AI Brain Architecture Standards Integration
        self.ai_brain_confidence = None
        self.ai_brain_error_dna = None
        if AI_BRAIN_AVAILABLE:
            try:
                self.ai_brain_confidence = AiBrainConfidenceFramework(f"discovery-architecture-{service_name}")
                self.ai_brain_error_dna = AiBrainTradingErrorDNA(f"discovery-validator-{service_name}")
                print(f"✅ AI Brain Architecture Standards initialized for discovery: {service_name}")
            except Exception as e:
                print(f"⚠️ AI Brain Architecture Standards initialization failed: {e}")
        
        # Architecture validation patterns (from AI Brain architecture-standards.js)
        self._init_architecture_patterns()
        
        # Service-specific configurations
        self._setup_service_defaults()
        
        self.logger.info("Service discovery initialized", extra={
            "service": service_name,
            "heartbeat_interval": self.config.heartbeat_interval,
            "health_check_timeout": self.config.health_check_timeout
        })
    
    def _setup_service_defaults(self):
        """Setup service-specific discovery configurations"""
        service_configs = {
            "api-gateway": {
                "heartbeat_interval": 15.0,
                "health_check_timeout": 3.0,
                "max_failures": 2
            },
            "ai-provider": {
                "heartbeat_interval": 30.0,
                "health_check_timeout": 10.0,
                "max_failures": 3
            },
            "trading-engine": {
                "heartbeat_interval": 10.0,
                "health_check_timeout": 2.0,
                "max_failures": 2
            },
            "database-service": {
                "heartbeat_interval": 60.0,
                "health_check_timeout": 15.0,
                "max_failures": 5
            },
            "data-bridge": {
                "heartbeat_interval": 5.0,
                "health_check_timeout": 1.0,
                "max_failures": 1
            }
        }
        
        if self.service_name in service_configs:
            config = service_configs[self.service_name]
            self.config.heartbeat_interval = config["heartbeat_interval"]
            self.config.health_check_timeout = config["health_check_timeout"]
            self.config.max_health_check_failures = config["max_failures"]
    
    def _init_architecture_patterns(self):
        """Initialize AI Brain architecture validation patterns"""
        # Naming convention patterns (from AI Brain architecture-standards.js)
        self.naming_conventions = {
            'services': r'^[a-z][a-z0-9]*(-[a-z0-9]+)*$',  # kebab-case
            'endpoints': r'^/api/v\d+/[a-z][a-z0-9]*(-[a-z0-9]+)*(/[a-z][a-z0-9]*(-[a-z0-9]+)*)*$',
            'parameters': r'^[a-zA-Z][a-zA-Z0-9]*$',  # camelCase
            'headers': r'^[a-z][a-z0-9]*(-[a-z0-9]+)*$',  # kebab-case
        }
        
        # Required service capabilities by type
        self.service_capability_requirements = {
            ServiceType.API_GATEWAY: ['routing', 'authentication', 'rate-limiting'],
            ServiceType.AI_PROVIDER: ['model-inference', 'response-streaming'],
            ServiceType.TRADING_ENGINE: ['order-execution', 'risk-management'],
            ServiceType.DATABASE_SERVICE: ['data-persistence', 'query-optimization'],
            ServiceType.DATA_BRIDGE: ['real-time-streaming', 'data-transformation']
        }
        
        # Standard endpoint patterns
        self.standard_endpoints = {
            'health': '/health',
            'metrics': '/metrics',
            'info': '/info',
            'ready': '/ready',
            'swagger': '/swagger',
        }
        
        # Service mesh naming patterns
        self.service_mesh_patterns = {
            'service_name': r'^[a-z][a-z0-9]*(-[a-z0-9]+)*$',
            'namespace': r'^[a-z][a-z0-9]*(-[a-z0-9]+)*$',
            'version': r'^v\d+(\.\d+)*$',
        }
    
    async def register_service(self, 
                              host: str,
                              port: int,
                              service_type: Optional[ServiceType] = None,
                              version: str = "1.0.0",
                              environment: str = "development",
                              capabilities: Optional[List[str]] = None,
                              metadata: Optional[Dict[str, Any]] = None,
                              tags: Optional[List[str]] = None) -> str:
        """
        Register this service instance in the discovery system.
        
        Args:
            host: Service host address
            port: Service port
            service_type: Type of service (auto-detected if None)
            version: Service version
            environment: Environment (development, staging, production)
            capabilities: List of service capabilities
            metadata: Additional service metadata
            tags: Service tags for filtering
            
        Returns:
            instance_id: Unique instance identifier
        """
        # Auto-detect service type if not provided
        if service_type is None:
            service_type = self._detect_service_type()
        
        # Generate unique instance ID
        instance_id = self._generate_instance_id(host, port)
        
        # Create service instance
        instance = ServiceInstance(
            instance_id=instance_id,
            service_name=self.service_name,
            service_type=service_type,
            host=host,
            port=port,
            version=version,
            environment=environment,
            status=ServiceStatus.STARTING,
            metadata=metadata or {},
            tags=tags or [],
            capabilities=capabilities or [],
            registration_time=datetime.now()
        )
        
        # Perform AI Brain Architecture Validation
        if self.config.architecture_validation_enabled:
            print(f"🏢 AI Brain: Performing architecture validation for service registration: {instance_id}")
            architecture_validation = await self._validate_service_architecture(instance)
            instance.architecture_validation = architecture_validation
            
            if not architecture_validation.is_compliant:
                self.logger.warning(f"Service {instance_id} registered with architecture violations", extra={
                    "violations": len(architecture_validation.violations),
                    "score": architecture_validation.architecture_score
                })
        
        # Register in service registry
        if self.service_name not in self.service_registry:
            self.service_registry[self.service_name] = {}
        
        self.service_registry[self.service_name][instance_id] = instance
        
        # Initialize health history
        self.instance_health_history[instance_id] = []
        
        self.logger.info(f"Service registered: {instance_id}", extra={
            "service_type": service_type.value,
            "host": host,
            "port": port,
            "version": version,
            "environment": environment,
            "capabilities": capabilities
        })
        
        return instance_id
    
    async def deregister_service(self, instance_id: str) -> bool:
        """
        Deregister a service instance.
        
        Args:
            instance_id: Instance ID to deregister
            
        Returns:
            bool: True if deregistered successfully
        """
        for service_name, instances in self.service_registry.items():
            if instance_id in instances:
                # Mark as stopping
                instances[instance_id].status = ServiceStatus.STOPPING
                
                # Remove after a grace period
                await asyncio.sleep(1.0)
                del instances[instance_id]
                
                # Cleanup health history
                if instance_id in self.instance_health_history:
                    del self.instance_health_history[instance_id]
                
                self.logger.info(f"Service deregistered: {instance_id}")
                return True
        
        return False
    
    async def discover_services(self, 
                               service_name: str,
                               environment: Optional[str] = None,
                               tags: Optional[List[str]] = None,
                               capabilities: Optional[List[str]] = None,
                               healthy_only: bool = True) -> List[ServiceInstance]:
        """
        Discover available service instances.
        
        Args:
            service_name: Name of service to discover
            environment: Filter by environment
            tags: Filter by tags
            capabilities: Filter by capabilities
            healthy_only: Return only healthy instances
            
        Returns:
            List of matching service instances
        """
        if service_name not in self.service_registry:
            return []
        
        instances = list(self.service_registry[service_name].values())
        
        # Apply filters
        if environment:
            instances = [i for i in instances if i.environment == environment]
        
        if tags:
            instances = [i for i in instances if any(tag in i.tags for tag in tags)]
        
        if capabilities:
            instances = [i for i in instances if 
                        any(cap in i.capabilities for cap in capabilities)]
        
        if healthy_only:
            instances = [i for i in instances if i.is_available]
        
        return instances
    
    async def get_service_instance(self, 
                                  service_name: str,
                                  strategy: str = "round_robin",
                                  **filters) -> Optional[ServiceInstance]:
        """
        Get a service instance using load balancing strategy.
        
        Args:
            service_name: Name of service
            strategy: Load balancing strategy
            **filters: Additional filters
            
        Returns:
            Selected service instance or None
        """
        instances = await self.discover_services(service_name, **filters)
        
        if not instances:
            return None
        
        if strategy == "round_robin":
            return self._round_robin_select(service_name, instances)
        elif strategy == "least_connections":
            return self._least_connections_select(instances)
        elif strategy == "weighted":
            return self._weighted_select(instances)
        else:
            # Default to first available
            return instances[0]
    
    def _round_robin_select(self, service_name: str, instances: List[ServiceInstance]) -> ServiceInstance:
        """Round robin selection"""
        if service_name not in self.round_robin_indices:
            self.round_robin_indices[service_name] = 0
        
        index = self.round_robin_indices[service_name] % len(instances)
        self.round_robin_indices[service_name] = (index + 1) % len(instances)
        
        return instances[index]
    
    def _least_connections_select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Least connections selection (based on load factor)"""
        return min(instances, key=lambda i: i.load_factor)
    
    def _weighted_select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Weighted selection based on performance"""
        # Select based on inverse of response time (faster = higher weight)
        if all(i.response_time_ms <= 0 for i in instances):
            return instances[0]
        
        return min(instances, key=lambda i: i.response_time_ms if i.response_time_ms > 0 else float('inf'))
    
    async def health_check_instance(self, instance: ServiceInstance) -> bool:
        """
        Perform health check on a service instance.
        
        Args:
            instance: Service instance to check
            
        Returns:
            bool: True if healthy
        """
        try:
            import aiohttp
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(
                total=self.config.health_check_timeout
            )) as session:
                start_time = time.time()
                
                async with session.get(instance.health_url) as response:
                    response_time = (time.time() - start_time) * 1000
                    instance.response_time_ms = response_time
                    
                    is_healthy = response.status < 500
                    
                    # Update instance status
                    if is_healthy:
                        instance.status = ServiceStatus.HEALTHY
                        instance.last_heartbeat = datetime.now()
                    else:
                        instance.status = ServiceStatus.DEGRADED
                    
                    # Update health history
                    history = self.instance_health_history.get(instance.instance_id, [])
                    history.append(is_healthy)
                    
                    # Keep only recent history
                    if len(history) > 10:
                        history = history[-10:]
                    
                    self.instance_health_history[instance.instance_id] = history
                    
                    # Check if instance should be marked unhealthy
                    recent_failures = history[-self.config.max_health_check_failures:]
                    if len(recent_failures) >= self.config.max_health_check_failures:
                        if not any(recent_failures):
                            instance.status = ServiceStatus.UNHEALTHY
                    
                    return is_healthy
                    
        except Exception as e:
            self.logger.error(f"Health check failed for {instance.instance_id}: {e}")
            
            # Update health history with failure
            history = self.instance_health_history.get(instance.instance_id, [])
            history.append(False)
            if len(history) > 10:
                history = history[-10:]
            self.instance_health_history[instance.instance_id] = history
            
            # Mark as unhealthy after consecutive failures
            recent_failures = history[-self.config.max_health_check_failures:]
            if len(recent_failures) >= self.config.max_health_check_failures:
                if not any(recent_failures):
                    instance.status = ServiceStatus.UNHEALTHY
            
            return False
    
    async def _validate_service_architecture(self, instance: ServiceInstance) -> ArchitectureValidationResult:
        """Perform comprehensive AI Brain architecture validation on service instance"""
        violations = []
        naming_violations = []
        endpoint_consistency_issues = []
        recommendations = []
        ai_brain_confidence = 0.85  # Default confidence
        
        try:
            print(f"🔍 AI Brain: Validating architecture standards for {instance.service_name}")
            
            # 1. Service naming convention validation
            naming_score = self._validate_service_naming(instance, naming_violations)
            
            # 2. Service capability validation
            capability_score = self._validate_service_capabilities(instance, violations)
            
            # 3. Endpoint consistency validation
            endpoint_score = await self._validate_endpoint_consistency(instance, endpoint_consistency_issues)
            
            # 4. Service contract validation
            contract_score = await self._validate_service_contract(instance, violations)
            
            # 5. Service mesh compliance validation
            mesh_score = self._validate_service_mesh_compliance(instance, violations)
            
            # 6. AI Brain confidence analysis
            if self.ai_brain_confidence and AI_BRAIN_AVAILABLE:
                try:
                    confidence_result = self.ai_brain_confidence.assess_decision_confidence(
                        decision_type="service_architecture",
                        factors={
                            "naming_score": naming_score,
                            "capability_score": capability_score,
                            "endpoint_score": endpoint_score,
                            "contract_score": contract_score,
                            "mesh_score": mesh_score,
                            "service_type": instance.service_type.value
                        },
                        context={
                            "service_name": instance.service_name,
                            "environment": instance.environment,
                            "validation_type": "architecture_compliance"
                        }
                    )
                    ai_brain_confidence = confidence_result.get("confidence_score", 0.85)
                    
                    if confidence_result.get("recommendations"):
                        recommendations.extend(confidence_result["recommendations"])
                        
                except Exception as e:
                    print(f"⚠️ AI Brain confidence analysis failed: {e}")
            
            # 7. Calculate overall architecture score
            architecture_score = self._calculate_architecture_score(
                naming_score, capability_score, endpoint_score, contract_score, mesh_score, ai_brain_confidence
            )
            
            # 8. Generate architecture recommendations
            if not recommendations:  # Only if AI Brain didn't provide recommendations
                recommendations = self._generate_architecture_recommendations(
                    violations, naming_violations, endpoint_consistency_issues
                )
            
            # 9. Determine compliance status
            is_compliant = (architecture_score >= 0.8 and 
                          len([v for v in violations if v.get('severity') == 'CRITICAL']) == 0)
            
            # Calculate service pattern compliance
            service_pattern_compliance = (naming_score + capability_score) / 2
            
            print(f"🏢 AI Brain Architecture Validation Complete: Score {architecture_score:.2f}, Compliant: {is_compliant}")
            
            return ArchitectureValidationResult(
                is_compliant=is_compliant,
                architecture_score=architecture_score,
                violations=violations,
                recommendations=recommendations,
                ai_brain_confidence=ai_brain_confidence,
                naming_violations=naming_violations,
                endpoint_consistency_issues=endpoint_consistency_issues,
                validation_timestamp=datetime.utcnow().isoformat(),
                service_pattern_compliance=service_pattern_compliance
            )
            
        except Exception as e:
            # Graceful degradation when architecture validation fails
            print(f"⚠️ AI Brain Architecture validation failed: {e}")
            if self.ai_brain_error_dna:
                try:
                    self.ai_brain_error_dna.analyze_error(e, {
                        "service_name": instance.service_name,
                        "operation": "architecture_validation"
                    })
                except:
                    pass  # Silent fallback if error DNA also fails
                    
            return ArchitectureValidationResult(
                is_compliant=False,
                architecture_score=0.0,
                violations=[{
                    'type': 'ARCHITECTURE_VALIDATION_ERROR',
                    'severity': 'HIGH',
                    'message': f'Architecture validation failed: {str(e)}',
                    'recommendation': 'Review architecture validation configuration'
                }],
                recommendations=['Manual architecture review required'],
                ai_brain_confidence=0.0,
                naming_violations=[],
                endpoint_consistency_issues=[],
                validation_timestamp=datetime.utcnow().isoformat(),
                service_pattern_compliance=0.0
            )
    
    async def start_monitoring(self):
        """Start service discovery monitoring"""
        if self.is_running:
            self.logger.warning("Service discovery monitoring already running")
            return
        
        self.is_running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        self.logger.info("Service discovery monitoring started")
    
    async def stop_monitoring(self):
        """Stop service discovery monitoring"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Service discovery monitoring stopped")
    
    async def _monitoring_loop(self):
        """Continuous health monitoring loop"""
        try:
            while self.is_running:
                # Health check all registered instances
                health_check_tasks = []
                
                for service_name, instances in self.service_registry.items():
                    for instance in instances.values():
                        if instance.status != ServiceStatus.STOPPING:
                            task = asyncio.create_task(self.health_check_instance(instance))
                            health_check_tasks.append((instance.instance_id, task))
                
                # Wait for all health checks
                for instance_id, task in health_check_tasks:
                    try:
                        await task
                    except Exception as e:
                        self.logger.error(f"Health check task failed for {instance_id}: {e}")
                
                # Wait before next iteration
                await asyncio.sleep(self.config.heartbeat_interval)
                
        except asyncio.CancelledError:
            self.logger.info("Service discovery monitoring loop cancelled")
        except Exception as e:
            self.logger.error(f"Service discovery monitoring loop error: {e}")
    
    async def _cleanup_loop(self):
        """Cleanup stale service instances"""
        try:
            while self.is_running:
                now = datetime.now()
                stale_instances = []
                
                for service_name, instances in self.service_registry.items():
                    for instance_id, instance in instances.items():
                        if (instance.last_heartbeat and 
                            (now - instance.last_heartbeat).total_seconds() > self.config.instance_ttl):
                            stale_instances.append((service_name, instance_id))
                
                # Remove stale instances
                for service_name, instance_id in stale_instances:
                    if service_name in self.service_registry:
                        if instance_id in self.service_registry[service_name]:
                            del self.service_registry[service_name][instance_id]
                            self.logger.info(f"Removed stale instance: {instance_id}")
                        
                        if instance_id in self.instance_health_history:
                            del self.instance_health_history[instance_id]
                
                # Wait before next cleanup
                await asyncio.sleep(self.config.cleanup_interval)
                
        except asyncio.CancelledError:
            self.logger.info("Service discovery cleanup loop cancelled")
        except Exception as e:
            self.logger.error(f"Service discovery cleanup loop error: {e}")
    
    def _detect_service_type(self) -> ServiceType:
        """Auto-detect service type from service name"""
        service_type_map = {
            "api-gateway": ServiceType.API_GATEWAY,
            "ai-provider": ServiceType.AI_PROVIDER,
            "ai-orchestration": ServiceType.AI_ORCHESTRATION,
            "database-service": ServiceType.DATABASE_SERVICE,
            "data-bridge": ServiceType.DATA_BRIDGE,
            "deep-learning": ServiceType.DEEP_LEARNING,
            "ml-processing": ServiceType.ML_PROCESSING,
            "trading-engine": ServiceType.TRADING_ENGINE,
            "user-service": ServiceType.USER_SERVICE
        }
        
        return service_type_map.get(self.service_name, ServiceType.EXTERNAL)
    
    def _generate_instance_id(self, host: str, port: int) -> str:
        """Generate unique instance ID"""
        base_str = f"{self.service_name}-{host}-{port}-{time.time()}"
        return hashlib.md5(base_str.encode()).hexdigest()[:16]
    
    def _validate_service_naming(self, instance: ServiceInstance, naming_violations: List[Dict[str, Any]]) -> float:
        """Validate service naming conventions"""
        import re
        score = 1.0
        
        # Check service name convention (kebab-case)
        service_pattern = re.compile(self.naming_conventions['services'])
        if not service_pattern.match(instance.service_name):
            naming_violations.append({
                'type': 'SERVICE_NAMING_VIOLATION',
                'field': 'service_name',
                'value': instance.service_name,
                'expected_pattern': 'kebab-case (e.g., user-service)',
                'recommendation': 'Use kebab-case naming convention'
            })
            score -= 0.3
            
        # Check version format
        version_pattern = re.compile(self.naming_conventions.get('version', r'^v\d+(\.\d+)*$'))
        if not version_pattern.match(f"v{instance.version}"):
            naming_violations.append({
                'type': 'VERSION_FORMAT_VIOLATION',
                'field': 'version',
                'value': instance.version,
                'expected_pattern': 'semantic versioning (e.g., 1.0.0)',
                'recommendation': 'Use semantic versioning'
            })
            score -= 0.2
            
        return max(0.0, score)
    
    def _validate_service_capabilities(self, instance: ServiceInstance, violations: List[Dict[str, Any]]) -> float:
        """Validate service capabilities against type requirements"""
        required_capabilities = self.service_capability_requirements.get(instance.service_type, [])
        
        if not required_capabilities:
            return 1.0  # No requirements defined
            
        missing_capabilities = []
        for required_cap in required_capabilities:
            if required_cap not in instance.capabilities:
                missing_capabilities.append(required_cap)
                
        if missing_capabilities:
            violations.append({
                'type': 'MISSING_CAPABILITIES',
                'severity': 'HIGH',
                'service_type': instance.service_type.value,
                'missing_capabilities': missing_capabilities,
                'recommendation': f'Implement required capabilities: {missing_capabilities}'
            })
            
        # Calculate score based on capability coverage
        if not required_capabilities:
            return 1.0
            
        coverage = 1.0 - (len(missing_capabilities) / len(required_capabilities))
        return max(0.0, coverage)
    
    async def _validate_endpoint_consistency(self, instance: ServiceInstance, issues: List[Dict[str, Any]]) -> float:
        """Validate endpoint consistency and patterns"""
        score = 1.0
        
        try:
            # Check if standard endpoints exist
            missing_standard_endpoints = []
            for endpoint_name, endpoint_path in self.standard_endpoints.items():
                # In a real implementation, this would make HTTP requests to check endpoint existence
                # For now, we'll check basic requirements
                if endpoint_name == 'health' and not instance.health_check_url:
                    missing_standard_endpoints.append(endpoint_name)
                    
            if missing_standard_endpoints:
                issues.append({
                    'type': 'MISSING_STANDARD_ENDPOINTS',
                    'missing_endpoints': missing_standard_endpoints,
                    'recommendation': 'Implement standard endpoints for service observability'
                })
                score -= len(missing_standard_endpoints) * 0.1
                
            # Validate API versioning in endpoints (if service contract URL exists)
            if instance.service_contract_url:
                # In a real implementation, this would fetch and validate the service contract
                pass
                
        except Exception as e:
            self.logger.error(f"Endpoint consistency validation failed: {e}")
            score = 0.5  # Partial score if validation fails
            
        return max(0.0, score)
    
    async def _validate_service_contract(self, instance: ServiceInstance, violations: List[Dict[str, Any]]) -> float:
        """Validate service contract availability and format"""
        if not self.config.require_service_contracts:
            return 1.0
            
        if not instance.service_contract_url:
            violations.append({
                'type': 'MISSING_SERVICE_CONTRACT',
                'severity': 'MEDIUM',
                'recommendation': 'Provide service contract URL (OpenAPI/Swagger specification)'
            })
            return 0.5
            
        # In a real implementation, this would fetch and validate the contract
        # For now, just check if URL is provided
        return 1.0
    
    def _validate_service_mesh_compliance(self, instance: ServiceInstance, violations: List[Dict[str, Any]]) -> float:
        """Validate service mesh naming and metadata compliance"""
        if not self.config.service_mesh_enabled:
            return 1.0
            
        score = 1.0
        
        # Check service mesh metadata
        required_mesh_metadata = ['namespace', 'cluster', 'region']
        missing_metadata = []
        
        for meta_key in required_mesh_metadata:
            if meta_key not in instance.metadata:
                missing_metadata.append(meta_key)
                
        if missing_metadata:
            violations.append({
                'type': 'MISSING_SERVICE_MESH_METADATA',
                'severity': 'MEDIUM',
                'missing_metadata': missing_metadata,
                'recommendation': 'Provide required service mesh metadata'
            })
            score -= len(missing_metadata) * 0.2
            
        return max(0.0, score)
    
    def _calculate_architecture_score(self, naming_score: float, capability_score: float, 
                                    endpoint_score: float, contract_score: float, 
                                    mesh_score: float, ai_brain_confidence: float) -> float:
        """Calculate overall architecture compliance score"""
        # Weighted scoring based on importance
        weights = {
            'naming': 0.2,
            'capability': 0.25,
            'endpoint': 0.2,
            'contract': 0.15,
            'mesh': 0.1,
            'confidence': 0.1
        }
        
        weighted_score = (
            naming_score * weights['naming'] +
            capability_score * weights['capability'] +
            endpoint_score * weights['endpoint'] +
            contract_score * weights['contract'] +
            mesh_score * weights['mesh'] +
            ai_brain_confidence * weights['confidence']
        )
        
        return max(0.0, min(1.0, weighted_score))
    
    def _generate_architecture_recommendations(self, violations: List[Dict[str, Any]], 
                                             naming_violations: List[Dict[str, Any]], 
                                             endpoint_issues: List[Dict[str, Any]]) -> List[str]:
        """Generate architecture improvement recommendations"""
        recommendations = []
        
        if naming_violations:
            recommendations.append("Adopt consistent naming conventions (kebab-case for services)")
            recommendations.append("Use semantic versioning for service versions")
            
        if any(v.get('type') == 'MISSING_CAPABILITIES' for v in violations):
            recommendations.append("Implement all required capabilities for service type")
            recommendations.append("Document service capabilities in registration metadata")
            
        if endpoint_issues:
            recommendations.append("Implement standard endpoints (/health, /metrics, /info)")
            recommendations.append("Use consistent API versioning in endpoint paths")
            
        if any(v.get('type') == 'MISSING_SERVICE_CONTRACT' for v in violations):
            recommendations.append("Provide OpenAPI/Swagger service contract specification")
            recommendations.append("Implement API documentation endpoints")
            
        # Add general architecture best practices
        recommendations.extend([
            "Follow microservices architecture patterns",
            "Implement proper service discovery registration",
            "Use consistent error handling and response formats",
            "Implement comprehensive observability (logging, metrics, tracing)"
        ])
        
        return list(set(recommendations))  # Remove duplicates
    
    def get_architecture_validation_summary(self) -> Dict[str, Any]:
        """Get summary of architecture validation across all services"""
        total_instances = 0
        compliant_instances = 0
        validation_scores = []
        violation_types = {}
        
        for instances in self.service_registry.values():
            for instance in instances.values():
                total_instances += 1
                
                if instance.architecture_validation:
                    validation_scores.append(instance.architecture_validation.architecture_score)
                    
                    if instance.architecture_validation.is_compliant:
                        compliant_instances += 1
                        
                    # Count violation types
                    for violation in instance.architecture_validation.violations:
                        violation_type = violation.get('type', 'UNKNOWN')
                        violation_types[violation_type] = violation_types.get(violation_type, 0) + 1
                        
        avg_score = sum(validation_scores) / len(validation_scores) if validation_scores else 0.0
        compliance_rate = compliant_instances / total_instances if total_instances > 0 else 0.0
        
        return {
            "total_instances": total_instances,
            "compliant_instances": compliant_instances,
            "compliance_rate": compliance_rate,
            "average_architecture_score": avg_score,
            "violation_types": violation_types,
            "architecture_validation_enabled": self.config.architecture_validation_enabled
        }
    
    def get_registry_status(self) -> Dict[str, Any]:
        """Get current registry status"""
        total_instances = sum(len(instances) for instances in self.service_registry.values())
        healthy_instances = 0
        
        for instances in self.service_registry.values():
            healthy_instances += sum(1 for i in instances.values() if i.is_healthy)
        
        # Include architecture validation summary
        architecture_summary = self.get_architecture_validation_summary()
        
        return {
            "total_services": len(self.service_registry),
            "total_instances": total_instances,
            "healthy_instances": healthy_instances,
            "monitoring_active": self.is_running,
            "architecture_validation": architecture_summary,
            "services": {
                name: {
                    "instance_count": len(instances),
                    "healthy_count": sum(1 for i in instances.values() if i.is_healthy),
                    "compliant_count": sum(1 for i in instances.values() if i.is_architecture_compliant),
                    "instances": [
                        {
                            "id": i.instance_id,
                            "host": i.host,
                            "port": i.port,
                            "status": i.status.value,
                            "architecture_compliant": i.is_architecture_compliant,
                            "architecture_score": i.architecture_validation.architecture_score if i.architecture_validation else 0.0,
                            "last_heartbeat": i.last_heartbeat.isoformat() if i.last_heartbeat else None
                        }
                        for i in instances.values()
                    ]
                }
                for name, instances in self.service_registry.items()
            }
        }
    
    # Context manager support
    async def __aenter__(self):
        await self.start_monitoring()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop_monitoring()

# Service discovery utilities
class ServiceClient:
    """Client for communicating with discovered services"""
    
    def __init__(self, discovery_core: DiscoveryCore):
        self.discovery = discovery_core
        self.logger = BaseLogger(discovery_core.service_name, "service_client")
    
    async def call_service(self, 
                          service_name: str,
                          endpoint: str,
                          method: str = "GET",
                          data: Optional[Dict[str, Any]] = None,
                          timeout: float = 30.0,
                          retries: int = 3) -> Dict[str, Any]:
        """
        Call another service with automatic discovery and failover.
        
        Args:
            service_name: Name of target service
            endpoint: API endpoint path
            method: HTTP method
            data: Request data
            timeout: Request timeout
            retries: Number of retries with different instances
            
        Returns:
            Response data
        """
        import aiohttp
        
        for attempt in range(retries):
            # Discover service instance
            instance = await self.discovery.get_service_instance(service_name)
            
            if not instance:
                if attempt == retries - 1:
                    raise ValueError(f"No available instances for service: {service_name}")
                await asyncio.sleep(0.5)
                continue
            
            try:
                url = f"{instance.base_url}{endpoint}"
                
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(
                    total=timeout
                )) as session:
                    if method.upper() == "GET":
                        async with session.get(url) as response:
                            response.raise_for_status()
                            return await response.json()
                    elif method.upper() == "POST":
                        async with session.post(url, json=data) as response:
                            response.raise_for_status()
                            return await response.json()
                    elif method.upper() == "PUT":
                        async with session.put(url, json=data) as response:
                            response.raise_for_status()
                            return await response.json()
                    elif method.upper() == "DELETE":
                        async with session.delete(url) as response:
                            response.raise_for_status()
                            return await response.json()
                    else:
                        raise ValueError(f"Unsupported HTTP method: {method}")
            
            except Exception as e:
                self.logger.error(f"Service call failed to {instance.instance_id}: {e}")
                
                # Mark instance as degraded
                instance.status = ServiceStatus.DEGRADED
                
                if attempt == retries - 1:
                    raise
                
                await asyncio.sleep(0.5)
        
        raise RuntimeError(f"All retries failed for service: {service_name}")

# Global discovery core instances
_discovery_cores: Dict[str, DiscoveryCore] = {}

def get_discovery_core(service_name: str, config: Optional[ServiceDiscoveryConfig] = None) -> DiscoveryCore:
    """Get or create AI Brain Enhanced discovery core for a service with architecture validation"""
    if service_name not in _discovery_cores:
        _discovery_cores[service_name] = DiscoveryCore(service_name, config)
    return _discovery_cores[service_name]

def get_architecture_validation_summary() -> Dict[str, Any]:
    """Get architecture validation summary across all discovery cores"""
    total_summary = {
        "total_instances": 0,
        "compliant_instances": 0,
        "compliance_rate": 0.0,
        "average_architecture_score": 0.0,
        "violation_types": {},
        "services": {}
    }
    
    all_scores = []
    
    for service_name, discovery_core in _discovery_cores.items():
        service_summary = discovery_core.get_architecture_validation_summary()
        total_summary["services"][service_name] = service_summary
        
        total_summary["total_instances"] += service_summary["total_instances"]
        total_summary["compliant_instances"] += service_summary["compliant_instances"]
        
        # Aggregate violation types
        for violation_type, count in service_summary["violation_types"].items():
            total_summary["violation_types"][violation_type] = total_summary["violation_types"].get(violation_type, 0) + count
            
    # Calculate overall rates
    if total_summary["total_instances"] > 0:
        total_summary["compliance_rate"] = total_summary["compliant_instances"] / total_summary["total_instances"]
        
    return total_summary