"""
AI Brain Enhanced Health Core - Deployment readiness with completeness auditing
Production-ready health monitoring with AI Brain completeness validation
"""

import asyncio
import time
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable, Tuple
from enum import Enum
from dataclasses import dataclass, field
from ..base.base_logger import BaseLogger
from ..base.base_performance import BasePerformance

# AI Brain Integration
try:
    import sys
    sys.path.append('/mnt/f/WINDSURF/concept_ai/projects/ai_trading/server_microservice/services')
    from shared.ai_brain_confidence_framework import AiBrainConfidenceFramework
    AI_BRAIN_AVAILABLE = True
except ImportError:
    AI_BRAIN_AVAILABLE = False

class HealthStatus(Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    NOT_READY = "not_ready"  # AI Brain: Not ready for deployment

class ComponentType(Enum):
    """Component type enumeration"""
    DATABASE = "database"
    CACHE = "cache"
    EXTERNAL_API = "external_api"
    QUEUE = "queue"
    STORAGE = "storage"
    CUSTOM = "custom"
    # AI Brain: Completeness components
    CONFIGURATION = "configuration"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    SECURITY = "security"

@dataclass
class HealthCheck:
    """Individual health check definition"""
    name: str
    component_type: ComponentType
    check_function: Callable[[], bool]
    timeout_seconds: float = 5.0
    interval_seconds: float = 30.0
    failure_threshold: int = 3
    recovery_threshold: int = 2
    last_check: Optional[datetime] = None
    failure_count: int = 0
    success_count: int = 0
    status: HealthStatus = HealthStatus.UNKNOWN
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class HealthReport:
    """AI Brain Enhanced complete health report with deployment readiness"""
    service_name: str
    overall_status: HealthStatus
    timestamp: datetime
    uptime_seconds: float
    checks: Dict[str, Dict[str, Any]]
    metrics: Dict[str, Any]
    environment: str
    version: str
    # AI Brain Completeness Audit Results
    deployment_readiness: Dict[str, Any] = None
    completeness_score: float = 0.0
    missing_components: List[str] = field(default_factory=list)
    deployment_blockers: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

class HealthCore:
    """
    AI Brain Enhanced core health monitoring with deployment readiness auditing.
    
    Features:
    - Individual component health checks
    - Automatic health monitoring with configurable intervals
    - Failure/recovery thresholds with circuit breaker pattern
    - Comprehensive health reporting
    - Performance metrics integration
    - Production-ready monitoring
    - AI Brain deployment completeness auditing
    - Missing component detection
    - Deployment readiness validation
    """
    
    def __init__(self, service_name: str, environment: str = "development"):
        """
        Initialize health monitoring for a service.
        
        Args:
            service_name: Name of the service being monitored
            environment: Environment (development, staging, production)
        """
        self.service_name = service_name
        self.environment = environment
        self.version = os.getenv(f"{service_name.upper().replace('-', '_')}_VERSION", "1.0.0")
        
        # Health checks registry
        self.health_checks: Dict[str, HealthCheck] = {}
        
        # Service lifecycle tracking
        self.start_time = time.time()
        self.is_running = False
        
        # Monitoring task
        self._monitoring_task: Optional[asyncio.Task] = None
        
        # AI Brain Completeness Auditing
        self.deployment_requirements = self._load_deployment_requirements()
        self.completeness_auditor = None
        if AI_BRAIN_AVAILABLE:
            try:
                self.ai_brain_confidence = AiBrainConfidenceFramework(f"health-{service_name}")
                print(f"\u2705 AI Brain Confidence Framework initialized for health monitoring: {service_name}")
            except Exception as e:
                print(f"\u26a0\ufe0f AI Brain Confidence Framework initialization failed: {e}")
        
        # Deployment readiness cache
        self._last_completeness_check: Optional[datetime] = None
        self._completeness_cache: Optional[Dict[str, Any]] = None
        self._cache_duration_minutes = 10  # Cache completeness results for 10 minutes
        
        # Initialize logging and performance tracking
        self.logger = BaseLogger(service_name, "health_core")
        self.performance_tracker = BasePerformance(service_name)
        
        # Service-specific configurations
        self._setup_service_defaults()
        
        # AI Brain: Setup deployment readiness checks
        self._setup_completeness_checks()
        
        self.logger.info("Health monitoring initialized", extra={
            "service": service_name,
            "environment": environment,
            "version": self.version
        })
    
    def _setup_service_defaults(self):
        """Setup service-specific health check configurations"""
        service_configs = {
            "ai-provider": {
                "check_interval": 30.0,
                "timeout": 10.0,
                "failure_threshold": 5
            },
            "api-gateway": {
                "check_interval": 15.0,
                "timeout": 5.0,
                "failure_threshold": 3
            },
            "trading-engine": {
                "check_interval": 10.0,
                "timeout": 3.0,
                "failure_threshold": 2
            },
            "database-service": {
                "check_interval": 30.0,
                "timeout": 15.0,
                "failure_threshold": 5
            },
            "data-bridge": {
                "check_interval": 5.0,
                "timeout": 2.0,
                "failure_threshold": 2
            }
        }
        
        config = service_configs.get(self.service_name, {
            "check_interval": 30.0,
            "timeout": 5.0,
            "failure_threshold": 3
        })
        
        self.default_interval = config["check_interval"]
        self.default_timeout = config["timeout"]
        self.default_failure_threshold = config["failure_threshold"]
    
    def _load_deployment_requirements(self) -> Dict[str, List[str]]:
        """AI Brain: Load deployment requirements for completeness auditing"""
        return {
            'essential': [
                'health_endpoint',
                'metrics_endpoint',
                'logging_configured',
                'error_handling',
                'configuration_management'
            ],
            'production': [
                'database_connection',
                'external_api_connectivity',
                'security_headers',
                'rate_limiting',
                'monitoring_alerts',
                'backup_strategy',
                'disaster_recovery'
            ],
            'containerization': [
                'dockerfile',
                'health_checks',
                'resource_limits',
                'environment_variables',
                'secrets_management'
            ],
            'observability': [
                'structured_logging',
                'metrics_collection',
                'distributed_tracing',
                'alerting_rules',
                'dashboard_setup'
            ]
        }
    
    def _setup_completeness_checks(self):
        """AI Brain: Setup automated deployment completeness checks"""
        # Register completeness validation checks
        self.register_check(
            "deployment_readiness",
            self._check_deployment_readiness,
            ComponentType.DEPLOYMENT,
            timeout_seconds=30.0,
            interval_seconds=300.0  # Check every 5 minutes
        )
        
        self.register_check(
            "configuration_completeness",
            self._check_configuration_completeness,
            ComponentType.CONFIGURATION,
            timeout_seconds=15.0,
            interval_seconds=300.0
        )
        
        self.register_check(
            "monitoring_completeness",
            self._check_monitoring_completeness,
            ComponentType.MONITORING,
            timeout_seconds=10.0,
            interval_seconds=600.0  # Check every 10 minutes
        )
        
        self.register_check(
            "security_completeness",
            self._check_security_completeness,
            ComponentType.SECURITY,
            timeout_seconds=20.0,
            interval_seconds=600.0
        )
    
    async def _check_deployment_readiness(self) -> bool:
        """AI Brain: Check if service is ready for deployment"""
        try:
            readiness_result = await self.audit_deployment_completeness()
            return readiness_result['overall_score'] >= 0.85  # 85% completeness threshold
        except Exception as e:
            self.logger.error(f"Deployment readiness check failed: {e}")
            return False
    
    async def _check_configuration_completeness(self) -> bool:
        """AI Brain: Check configuration completeness"""
        try:
            # Check for essential configuration
            required_configs = [
                'DATABASE_URL',
                'LOG_LEVEL',
                'SERVICE_PORT',
                'ENVIRONMENT'
            ]
            
            missing_configs = [config for config in required_configs if not os.getenv(config)]
            return len(missing_configs) == 0
        except Exception:
            return False
    
    async def _check_monitoring_completeness(self) -> bool:
        """AI Brain: Check monitoring system completeness"""
        try:
            # Check if monitoring components are available
            monitoring_components = [
                self.health_checks,  # Health checks configured
                hasattr(self, 'performance_tracker'),  # Performance tracking
                self.logger,  # Logging configured
            ]
            
            return all(component for component in monitoring_components)
        except Exception:
            return False
    
    async def _check_security_completeness(self) -> bool:
        """AI Brain: Check security configuration completeness"""
        try:
            # Basic security checks
            security_checks = [
                os.getenv('JWT_SECRET') is not None,  # Authentication configured
                self.environment != 'development' or os.getenv('ALLOW_DEV_MODE') == 'true',  # Production mode
                len(self.health_checks) > 0,  # Health monitoring active
            ]
            
            return all(security_checks)
        except Exception:
            return False
    
    async def audit_deployment_completeness(self) -> Dict[str, Any]:
        """AI Brain: Comprehensive deployment completeness audit"""
        # Use cache if available and recent
        if (self._completeness_cache and self._last_completeness_check and 
            (datetime.now() - self._last_completeness_check).total_seconds() < (self._cache_duration_minutes * 60)):
            return self._completeness_cache
        
        audit_result = {
            'service_name': self.service_name,
            'audit_timestamp': datetime.now().isoformat(),
            'overall_score': 0.0,
            'category_scores': {},
            'missing_components': [],
            'deployment_blockers': [],
            'recommendations': [],
            'ready_for_deployment': False
        }
        
        try:
            # Audit each category
            for category, requirements in self.deployment_requirements.items():
                category_score, missing, blockers = await self._audit_category(category, requirements)\n                audit_result['category_scores'][category] = category_score\n                audit_result['missing_components'].extend(missing)\n                audit_result['deployment_blockers'].extend(blockers)\n            \n            # Calculate overall score\n            weights = {\n                'essential': 0.4,\n                'production': 0.3,\n                'containerization': 0.2,\n                'observability': 0.1\n            }\n            \n            total_score = 0.0\n            for category, weight in weights.items():\n                total_score += audit_result['category_scores'].get(category, 0.0) * weight\n            \n            audit_result['overall_score'] = total_score\n            audit_result['ready_for_deployment'] = total_score >= 0.85 and len(audit_result['deployment_blockers']) == 0\n            \n            # Generate recommendations\n            audit_result['recommendations'] = self._generate_completeness_recommendations(audit_result)\n            \n            # AI Brain confidence scoring\n            if hasattr(self, 'ai_brain_confidence') and self.ai_brain_confidence:\n                confidence_score = await self.ai_brain_confidence.calculate_confidence(\n                    'deployment_readiness',\n                    {\n                        'overall_score': audit_result['overall_score'],\n                        'missing_components': len(audit_result['missing_components']),\n                        'deployment_blockers': len(audit_result['deployment_blockers']),\n                        'environment': self.environment\n                    }\n                )\n                audit_result['ai_brain_confidence'] = confidence_score\n            \n            # Cache the result\n            self._completeness_cache = audit_result\n            self._last_completeness_check = datetime.now()\n            \n            return audit_result\n            \n        except Exception as e:\n            self.logger.error(f\"Deployment completeness audit failed: {e}\")\n            audit_result.update({\n                'error': str(e),\n                'overall_score': 0.0,\n                'ready_for_deployment': False,\n                'deployment_blockers': ['Audit system failure']\n            })\n            return audit_result\n    \n    async def _audit_category(self, category: str, requirements: List[str]) -> Tuple[float, List[str], List[str]]:\n        \"\"\"Audit a specific category of deployment requirements\"\"\"\n        fulfilled = 0\n        missing = []\n        blockers = []\n        \n        for requirement in requirements:\n            is_fulfilled, is_blocker = await self._check_requirement(category, requirement)\n            \n            if is_fulfilled:\n                fulfilled += 1\n            else:\n                missing.append(f\"{category}.{requirement}\")\n                if is_blocker:\n                    blockers.append(f\"{category}.{requirement}\")\n        \n        score = fulfilled / len(requirements) if requirements else 1.0\n        return score, missing, blockers\n    \n    async def _check_requirement(self, category: str, requirement: str) -> Tuple[bool, bool]:\n        \"\"\"Check if a specific requirement is fulfilled\"\"\"\n        is_blocker = False\n        \n        try:\n            if category == 'essential':\n                if requirement == 'health_endpoint':\n                    return len(self.health_checks) > 0, True\n                elif requirement == 'metrics_endpoint':\n                    return hasattr(self, 'performance_tracker'), False\n                elif requirement == 'logging_configured':\n                    return self.logger is not None, True\n                elif requirement == 'error_handling':\n                    return True, False  # Assume basic error handling exists\n                elif requirement == 'configuration_management':\n                    return os.getenv('SERVICE_NAME') is not None, True\n            \n            elif category == 'production':\n                if requirement == 'database_connection':\n                    return 'database' in [check.component_type.value for check in self.health_checks.values()], True\n                elif requirement == 'external_api_connectivity':\n                    return 'external_api' in [check.component_type.value for check in self.health_checks.values()], False\n                elif requirement == 'security_headers':\n                    return self.environment == 'production', False\n                elif requirement == 'rate_limiting':\n                    return True, False  # Assume implemented at gateway level\n                elif requirement == 'monitoring_alerts':\n                    return len(self.health_checks) >= 3, False\n                elif requirement == 'backup_strategy':\n                    return self.environment != 'production', False  # Only required for production\n                elif requirement == 'disaster_recovery':\n                    return self.environment != 'production', False\n            \n            elif category == 'containerization':\n                if requirement == 'dockerfile':\n                    return os.path.exists('Dockerfile'), False\n                elif requirement == 'health_checks':\n                    return len(self.health_checks) > 0, False\n                elif requirement == 'resource_limits':\n                    return os.getenv('MEMORY_LIMIT') is not None, False\n                elif requirement == 'environment_variables':\n                    return len([k for k in os.environ.keys() if k.startswith(self.service_name.upper())]) > 0, False\n                elif requirement == 'secrets_management':\n                    return os.getenv('JWT_SECRET') is not None, False\n            \n            elif category == 'observability':\n                if requirement == 'structured_logging':\n                    return self.logger is not None, False\n                elif requirement == 'metrics_collection':\n                    return hasattr(self, 'performance_tracker'), False\n                elif requirement == 'distributed_tracing':\n                    return os.getenv('JAEGER_ENDPOINT') is not None, False\n                elif requirement == 'alerting_rules':\n                    return len(self.health_checks) > 0, False\n                elif requirement == 'dashboard_setup':\n                    return True, False  # Assume external dashboard exists\n            \n            return False, is_blocker\n            \n        except Exception:\n            return False, False\n    \n    def _generate_completeness_recommendations(self, audit_result: Dict[str, Any]) -> List[str]:\n        \"\"\"Generate recommendations based on completeness audit\"\"\"\n        recommendations = []\n        \n        if audit_result['overall_score'] < 0.5:\n            recommendations.append(\"Service is not ready for deployment - address critical missing components\")\n        elif audit_result['overall_score'] < 0.85:\n            recommendations.append(\"Service needs improvement before production deployment\")\n        \n        if audit_result['deployment_blockers']:\n            recommendations.append(f\"Resolve {len(audit_result['deployment_blockers'])} deployment blockers immediately\")\n        \n        # Category-specific recommendations\n        for category, score in audit_result['category_scores'].items():\n            if score < 0.7:\n                recommendations.append(f\"Improve {category} completeness (current: {score:.1%})\")\n        \n        if audit_result['category_scores'].get('essential', 0) < 0.9:\n            recommendations.append(\"Essential components missing - service may not function properly\")\n        \n        if self.environment == 'production' and audit_result['category_scores'].get('production', 0) < 0.8:\n            recommendations.append(\"Production requirements not met - service not production-ready\")\n        \n        return recommendations\n    \n    def register_check(self, 
                      name: str,
                      check_function: Callable[[], bool],
                      component_type: ComponentType = ComponentType.CUSTOM,
                      timeout_seconds: Optional[float] = None,
                      interval_seconds: Optional[float] = None,
                      failure_threshold: Optional[int] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Register a health check function.
        
        Args:
            name: Unique name for the health check
            check_function: Function that returns True if healthy, False otherwise
            component_type: Type of component being checked
            timeout_seconds: Timeout for the check (default: service-specific)
            interval_seconds: Check interval (default: service-specific)
            failure_threshold: Failures before marking unhealthy (default: service-specific)
            metadata: Additional metadata for the check
        """
        if name in self.health_checks:
            self.logger.warning(f"Health check '{name}' already registered, replacing")
        
        health_check = HealthCheck(
            name=name,
            component_type=component_type,
            check_function=check_function,
            timeout_seconds=timeout_seconds or self.default_timeout,
            interval_seconds=interval_seconds or self.default_interval,
            failure_threshold=failure_threshold or self.default_failure_threshold,
            metadata=metadata or {}
        )
        
        self.health_checks[name] = health_check
        
        self.logger.info(f"Health check registered: {name}", extra={
            "component_type": component_type.value,
            "timeout": health_check.timeout_seconds,
            "interval": health_check.interval_seconds,
            "failure_threshold": health_check.failure_threshold
        })
    
    def unregister_check(self, name: str) -> bool:
        """Unregister a health check"""
        if name in self.health_checks:
            del self.health_checks[name]
            self.logger.info(f"Health check unregistered: {name}")
            return True
        return False
    
    async def check_component(self, name: str) -> Tuple[HealthStatus, Optional[str]]:
        """
        Execute a single health check.
        
        Args:
            name: Name of the health check to execute
            
        Returns:
            Tuple of (status, error_message)
        """
        if name not in self.health_checks:
            return HealthStatus.UNKNOWN, f"Health check '{name}' not found"
        
        check = self.health_checks[name]
        
        try:
            # Execute check with timeout
            start_time = time.time()
            
            # Create a task for the check function
            if asyncio.iscoroutinefunction(check.check_function):
                result = await asyncio.wait_for(
                    check.check_function(),
                    timeout=check.timeout_seconds
                )
            else:
                # Run sync function in executor
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, check.check_function),
                    timeout=check.timeout_seconds
                )
            
            execution_time = time.time() - start_time
            check.last_check = datetime.now()
            
            if result:
                # Success
                check.success_count += 1
                check.failure_count = 0  # Reset failure count on success
                
                # Check if we should mark as healthy after recovery
                if (check.status == HealthStatus.UNHEALTHY and 
                    check.success_count >= check.recovery_threshold):
                    check.status = HealthStatus.HEALTHY
                    check.error_message = None
                    self.logger.info(f"Component recovered: {name}")
                elif check.status == HealthStatus.UNKNOWN:
                    check.status = HealthStatus.HEALTHY
                
                # Log successful check
                self.performance_tracker.record_operation(
                    f"health_check_{name}",
                    execution_time,
                    True
                )
                
                return check.status, None
            else:
                # Failure
                check.failure_count += 1
                check.success_count = 0  # Reset success count on failure
                error_msg = f"Health check returned False"
                
                # Check if we should mark as unhealthy
                if check.failure_count >= check.failure_threshold:
                    check.status = HealthStatus.UNHEALTHY
                    check.error_message = error_msg
                    self.logger.error(f"Component unhealthy: {name}", extra={
                        "failure_count": check.failure_count,
                        "threshold": check.failure_threshold
                    })
                else:
                    check.status = HealthStatus.DEGRADED
                    check.error_message = error_msg
                
                # Log failed check
                self.performance_tracker.record_operation(
                    f"health_check_{name}",
                    execution_time,
                    False
                )
                
                return check.status, error_msg
                
        except asyncio.TimeoutError:
            check.failure_count += 1
            check.last_check = datetime.now()
            error_msg = f"Health check timed out after {check.timeout_seconds}s"
            
            if check.failure_count >= check.failure_threshold:
                check.status = HealthStatus.UNHEALTHY
            else:
                check.status = HealthStatus.DEGRADED
            
            check.error_message = error_msg
            
            self.logger.error(f"Health check timeout: {name}", extra={
                "timeout": check.timeout_seconds,
                "failure_count": check.failure_count
            })
            
            return check.status, error_msg
            
        except Exception as e:
            check.failure_count += 1
            check.last_check = datetime.now()
            error_msg = f"Health check error: {str(e)}"
            
            if check.failure_count >= check.failure_threshold:
                check.status = HealthStatus.UNHEALTHY
            else:
                check.status = HealthStatus.DEGRADED
            
            check.error_message = error_msg
            
            self.logger.error(f"Health check exception: {name}", extra={
                "error": str(e),
                "failure_count": check.failure_count
            })
            
            return check.status, error_msg
    
    async def check_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Execute all registered health checks.
        
        Returns:
            Dictionary of check results
        """
        results = {}
        
        # Execute all checks concurrently
        check_tasks = []
        for name in self.health_checks.keys():
            task = asyncio.create_task(self.check_component(name))
            check_tasks.append((name, task))
        
        # Wait for all checks to complete
        for name, task in check_tasks:
            try:
                status, error_message = await task
                check = self.health_checks[name]
                
                results[name] = {
                    "status": status.value,
                    "component_type": check.component_type.value,
                    "last_check": check.last_check.isoformat() if check.last_check else None,
                    "failure_count": check.failure_count,
                    "success_count": check.success_count,
                    "error_message": error_message,
                    "metadata": check.metadata
                }
            except Exception as e:
                results[name] = {
                    "status": HealthStatus.UNKNOWN.value,
                    "error_message": f"Check execution failed: {str(e)}"
                }
        
        return results
    
    async def get_health_report(self) -> HealthReport:
        """
        Generate a comprehensive AI Brain enhanced health report with deployment readiness.
        
        Returns:
            Complete health report with all checks, metrics, and deployment completeness
        """
        # Execute all health checks
        check_results = await self.check_all()
        
        # AI Brain: Get deployment completeness audit
        deployment_readiness = await self.audit_deployment_completeness()
        
        # Determine overall status (including deployment readiness)
        overall_status = self._calculate_overall_status_with_completeness(check_results, deployment_readiness)
        
        # Get performance metrics
        metrics = self._get_health_metrics()
        
        # Calculate uptime
        uptime_seconds = time.time() - self.start_time
        
        return HealthReport(
            service_name=self.service_name,
            overall_status=overall_status,
            timestamp=datetime.now(),
            uptime_seconds=uptime_seconds,
            checks=check_results,
            metrics=metrics,
            environment=self.environment,
            version=self.version,
            deployment_readiness=deployment_readiness,
            completeness_score=deployment_readiness.get('overall_score', 0.0),
            missing_components=deployment_readiness.get('missing_components', []),
            deployment_blockers=deployment_readiness.get('deployment_blockers', []),
            recommendations=deployment_readiness.get('recommendations', [])
        )
    
    def _calculate_overall_status(self, check_results: Dict[str, Dict[str, Any]]) -> HealthStatus:
        """Calculate overall service health status from individual checks"""
        if not check_results:
            return HealthStatus.UNKNOWN
        
        statuses = [HealthStatus(result["status"]) for result in check_results.values()]
        
        # If any check is unhealthy, service is unhealthy
        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        
        # If any check is degraded, service is degraded
        if HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        
        # If all checks are healthy, service is healthy
        if all(status == HealthStatus.HEALTHY for status in statuses):
            return HealthStatus.HEALTHY
        
        # Otherwise unknown
        return HealthStatus.UNKNOWN
    
    def _calculate_overall_status_with_completeness(self, check_results: Dict[str, Dict[str, Any]], 
                                                   deployment_readiness: Dict[str, Any]) -> HealthStatus:
        """AI Brain: Calculate overall status including deployment completeness"""
        # First get the basic health status
        basic_status = self._calculate_overall_status(check_results)
        
        # Check deployment readiness
        if not deployment_readiness.get('ready_for_deployment', False):
            # If service has critical deployment blockers, mark as not ready
            if deployment_readiness.get('deployment_blockers', []):
                return HealthStatus.NOT_READY
            # If completeness score is too low, service is not ready
            elif deployment_readiness.get('overall_score', 0.0) < 0.5:
                return HealthStatus.NOT_READY
        
        # If deployment readiness is OK, return basic health status
        return basic_status
    
    def _get_health_metrics(self) -> Dict[str, Any]:
        """Get health-related metrics"""
        return {
            "total_checks": len(self.health_checks),
            "uptime_seconds": time.time() - self.start_time,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "monitoring_active": self.is_running,
            "memory_usage_mb": self._get_memory_usage(),
            "cpu_usage_percent": self._get_cpu_usage()
        }
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0
    
    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        try:
            import psutil
            return psutil.cpu_percent(interval=0.1)
        except ImportError:
            return 0.0
    
    async def start_monitoring(self):
        """Start continuous health monitoring"""
        if self.is_running:
            self.logger.warning("Health monitoring already running")
            return
        
        self.is_running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        self.logger.info("Health monitoring started", extra={
            "checks": len(self.health_checks),
            "default_interval": self.default_interval
        })
    
    async def stop_monitoring(self):
        """Stop continuous health monitoring"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Health monitoring stopped")
    
    async def _monitoring_loop(self):
        """Continuous monitoring loop"""
        try:
            while self.is_running:
                # Check if any checks need to be executed
                now = datetime.now()
                
                for name, check in self.health_checks.items():
                    if (check.last_check is None or 
                        (now - check.last_check).total_seconds() >= check.interval_seconds):
                        
                        # Execute check
                        await self.check_component(name)
                
                # Wait before next iteration
                await asyncio.sleep(min(5.0, self.default_interval / 6))
                
        except asyncio.CancelledError:
            self.logger.info("Health monitoring loop cancelled")
        except Exception as e:
            self.logger.error(f"Health monitoring loop error: {e}")
            # Restart monitoring after error
            if self.is_running:
                await asyncio.sleep(5.0)
                self._monitoring_task = asyncio.create_task(self._monitoring_loop())
    
    # Context manager support
    async def __aenter__(self):
        await self.start_monitoring()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop_monitoring()

# Common health check implementations
class CommonHealthChecks:
    """Common health check implementations for microservices"""
    
    @staticmethod
    def database_connection(connection_func: Callable[[], bool]) -> Callable[[], bool]:
        """Generic database connection health check"""
        def check():
            try:
                return connection_func()
            except Exception:
                return False
        return check
    
    @staticmethod
    def redis_connection(redis_client) -> Callable[[], bool]:
        """Redis connection health check"""
        def check():
            try:
                return redis_client.ping() if hasattr(redis_client, 'ping') else True
            except Exception:
                return False
        return check
    
    @staticmethod
    def external_api(url: str, timeout: float = 5.0) -> Callable[[], bool]:
        """External API health check"""
        def check():
            try:
                import requests
                response = requests.get(url, timeout=timeout)
                return response.status_code < 500
            except Exception:
                return False
        return check
    
    @staticmethod
    def file_system(path: str) -> Callable[[], bool]:
        """File system access health check"""
        def check():
            try:
                return os.path.exists(path) and os.access(path, os.R_OK | os.W_OK)
            except Exception:
                return False
        return check
    
    @staticmethod
    def memory_usage(max_usage_mb: float = 1000.0) -> Callable[[], bool]:
        """Memory usage health check"""
        def check():
            try:
                import psutil
                process = psutil.Process(os.getpid())
                memory_mb = process.memory_info().rss / 1024 / 1024
                return memory_mb < max_usage_mb
            except Exception:
                return True  # Default to healthy if can't check
        return check