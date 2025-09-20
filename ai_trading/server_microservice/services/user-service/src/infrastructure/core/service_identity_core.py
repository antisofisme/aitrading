"""
AI Brain Enhanced Service Identity Core - Architecture standards compliance and microservice patterns
Standardized service identification with AI Brain architecture validation
"""
import os
import uuid
import socket
import re
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

# AI Brain Integration
try:
    import sys
    sys.path.append('/mnt/f/WINDSURF/concept_ai/projects/ai_trading/server_microservice/services')
    from shared.ai_brain_confidence_framework import AiBrainConfidenceFramework
    AI_BRAIN_AVAILABLE = True
except ImportError:
    AI_BRAIN_AVAILABLE = False

@dataclass
class ServiceInfo:
    """AI Brain Enhanced standardized service information structure"""
    service_name: str
    service_id: str
    instance_id: str
    version: str
    deployment_env: str
    host_info: Dict[str, str]
    startup_time: datetime
    health_endpoint: str
    metrics_endpoint: str
    # AI Brain Architecture Compliance
    architecture_compliance: Dict[str, float] = None
    naming_standards_compliance: float = 0.0
    microservice_patterns_compliance: float = 0.0

class ServiceIdentityCore:
    """
    AI Brain Enhanced standardized service identity management for microservices.
    Ensures consistent service identification patterns and architecture compliance.
    
    Features:
    - Architecture standards validation
    - Microservice naming pattern enforcement  
    - Service boundary compliance checking
    - Pattern-based communication validation
    """
    
    def __init__(self, service_name: str, version: str = "1.0.0"):
        """
        Initialize AI Brain Enhanced service identity with architecture standards.
        
        Args:
            service_name: Name of the service (e.g., 'ml-processing')
            version: Service version (semantic versioning)
        """
        self.service_name = service_name
        self.version = version
        
        # AI Brain Architecture Standards
        self.architecture_violations: List[Dict[str, Any]] = []
        self.naming_compliance_score: float = 0.0
        self.microservice_patterns: Dict[str, bool] = {}
        
        # AI Brain Confidence Framework Integration
        self.ai_brain_confidence = None
        if AI_BRAIN_AVAILABLE:
            try:
                self.ai_brain_confidence = AiBrainConfidenceFramework(f"service-identity-{service_name}")
                print(f"\u2705 AI Brain Confidence Framework initialized for service identity: {service_name}")
            except Exception as e:
                print(f"\u26a0\ufe0f AI Brain Confidence Framework initialization failed: {e}")
        
        self._setup_service_identity()
        self._validate_architecture_standards()
    
    def _setup_service_identity(self):
        """Setup standardized service identity components"""
        # Standardized instance ID pattern
        self.instance_id = os.getenv('INSTANCE_ID', self._generate_instance_id())
        
        # Standardized service ID pattern: service-name-instance
        self.service_id = f"{self.service_name}-{self.instance_id}"
        
        # Deployment environment with fallback
        self.deployment_env = os.getenv('DEPLOYMENT_ENV', 'development')
        
        # Host information for service discovery
        self.host_info = self._get_host_info()
        
        # Service startup time
        self.startup_time = datetime.utcnow()
        
        # AI Brain: Standardized endpoint patterns with validation
        self.health_endpoint = f"/health/{self.service_name}"
        self.metrics_endpoint = f"/metrics/{self.service_name}"
        
        # Validate endpoint patterns against AI Brain standards
        self._validate_endpoint_patterns()
    
    def _validate_architecture_standards(self):
        """AI Brain: Validate service against architecture standards"""
        try:
            # Validate naming conventions
            self.naming_compliance_score = self._validate_naming_conventions()
            
            # Validate microservice patterns
            self.microservice_patterns = self._validate_microservice_patterns()
            
            # Validate service boundary compliance
            self._validate_service_boundaries()
            
            # Log compliance results
            if self.naming_compliance_score < 0.85:  # 85% compliance threshold
                self.architecture_violations.append({
                    'type': 'NAMING_STANDARDS',
                    'severity': 'HIGH',
                    'score': self.naming_compliance_score,
                    'message': 'Service naming does not meet architecture standards'
                })
            
            print(f\"AI Brain Architecture Standards validation completed for {self.service_name}:\")\n            print(f\"  - Naming compliance: {self.naming_compliance_score:.2f}\")\n            print(f\"  - Microservice patterns: {len([p for p in self.microservice_patterns.values() if p])}/{len(self.microservice_patterns)} compliant\")\n            print(f\"  - Architecture violations: {len(self.architecture_violations)}\")\n            \n        except Exception as e:\n            print(f\"Architecture standards validation failed: {e}\")\n    \n    def _validate_naming_conventions(self) -> float:\n        \"\"\"AI Brain: Validate service naming against standards\"\"\"\n        compliance_score = 1.0\n        \n        # Standard 1: kebab-case naming\n        if not re.match(r'^[a-z]+(-[a-z]+)*$', self.service_name):\n            compliance_score -= 0.3\n            self.architecture_violations.append({\n                'type': 'NAMING_CONVENTION',\n                'severity': 'MEDIUM',\n                'message': f\"Service name '{self.service_name}' should use kebab-case (e.g., 'data-bridge')\"\n            })\n        \n        # Standard 2: Descriptive naming\n        if len(self.service_name) < 5:\n            compliance_score -= 0.2\n            self.architecture_violations.append({\n                'type': 'NAMING_DESCRIPTIVENESS',\n                'severity': 'LOW',\n                'message': f\"Service name '{self.service_name}' is too short, should be descriptive\"\n            })\n        \n        # Standard 3: No generic names\n        generic_names = ['service', 'app', 'system', 'server', 'api']\n        if any(generic in self.service_name.lower() for generic in generic_names):\n            if self.service_name.lower() in generic_names:  # Only penalize if it's purely generic\n                compliance_score -= 0.4\n                self.architecture_violations.append({\n                    'type': 'GENERIC_NAMING',\n                    'severity': 'HIGH',\n                    'message': f\"Service name '{self.service_name}' is too generic, should be domain-specific\"\n                })\n        \n        # Standard 4: Version format validation\n        if not re.match(r'^\\d+\\.\\d+\\.\\d+$', self.version):\n            compliance_score -= 0.1\n            self.architecture_violations.append({\n                'type': 'VERSION_FORMAT',\n                'severity': 'LOW',\n                'message': f\"Version '{self.version}' should follow semantic versioning (x.y.z)\"\n            })\n        \n        return max(0.0, compliance_score)\n    \n    def _validate_microservice_patterns(self) -> Dict[str, bool]:\n        \"\"\"AI Brain: Validate microservice architecture patterns\"\"\"\n        patterns = {\n            'single_responsibility': self._check_single_responsibility(),\n            'bounded_context': self._check_bounded_context(),\n            'stateless_design': self._check_stateless_design(),\n            'api_gateway_ready': self._check_api_gateway_compatibility(),\n            'health_check_endpoint': self._check_health_endpoint(),\n            'metrics_endpoint': self._check_metrics_endpoint(),\n            'containerization_ready': self._check_containerization_readiness()\n        }\n        \n        # Record violations for failed patterns\n        for pattern, compliant in patterns.items():\n            if not compliant:\n                self.architecture_violations.append({\n                    'type': 'MICROSERVICE_PATTERN',\n                    'severity': 'MEDIUM',\n                    'pattern': pattern,\n                    'message': f\"Service does not comply with {pattern.replace('_', ' ')} pattern\"\n                })\n        \n        return patterns\n    \n    def _validate_service_boundaries(self):\n        \"\"\"AI Brain: Validate service boundary definitions\"\"\"\n        # Check if service has well-defined boundaries\n        if not hasattr(self, '_service_capabilities'):\n            self.architecture_violations.append({\n                'type': 'SERVICE_BOUNDARIES',\n                'severity': 'MEDIUM',\n                'message': 'Service capabilities and boundaries are not clearly defined'\n            })\n    \n    def _validate_endpoint_patterns(self):\n        \"\"\"AI Brain: Validate endpoint naming patterns\"\"\"\n        endpoint_patterns = {\n            'health': r'^/health/[a-z-]+$',\n            'metrics': r'^/metrics/[a-z-]+$'\n        }\n        \n        if not re.match(endpoint_patterns['health'], self.health_endpoint):\n            self.architecture_violations.append({\n                'type': 'ENDPOINT_PATTERN',\n                'severity': 'LOW',\n                'message': f\"Health endpoint '{self.health_endpoint}' does not follow standard pattern\"\n            })\n        \n        if not re.match(endpoint_patterns['metrics'], self.metrics_endpoint):\n            self.architecture_violations.append({\n                'type': 'ENDPOINT_PATTERN', \n                'severity': 'LOW',\n                'message': f\"Metrics endpoint '{self.metrics_endpoint}' does not follow standard pattern\"\n            })\n    \n    def _check_single_responsibility(self) -> bool:\n        \"\"\"Check if service follows single responsibility principle\"\"\"\n        # Heuristic: service name suggests single domain\n        domain_indicators = ['bridge', 'processor', 'manager', 'handler', 'service']\n        return any(indicator in self.service_name.lower() for indicator in domain_indicators)\n    \n    def _check_bounded_context(self) -> bool:\n        \"\"\"Check if service represents a bounded context\"\"\"\n        # Service should be domain-specific, not generic\n        return not any(generic in self.service_name.lower() for generic in ['generic', 'common', 'shared', 'util'])\n    \n    def _check_stateless_design(self) -> bool:\n        \"\"\"Check if service follows stateless design patterns\"\"\"\n        # Assume stateless unless service name suggests state management\n        stateful_indicators = ['session', 'state', 'cache']\n        return not any(indicator in self.service_name.lower() for indicator in stateful_indicators)\n    \n    def _check_api_gateway_ready(self) -> bool:\n        \"\"\"Check if service is ready for API gateway integration\"\"\"\n        # Service should have standard endpoints\n        return self.health_endpoint is not None and self.metrics_endpoint is not None\n    \n    def _check_health_endpoint(self) -> bool:\n        \"\"\"Check if service has proper health endpoint\"\"\"\n        return self.health_endpoint is not None and '/health/' in self.health_endpoint\n    \n    def _check_metrics_endpoint(self) -> bool:\n        \"\"\"Check if service has proper metrics endpoint\"\"\"\n        return self.metrics_endpoint is not None and '/metrics/' in self.metrics_endpoint\n    \n    def _check_containerization_readiness(self) -> bool:\n        \"\"\"Check if service is ready for containerization\"\"\"\n        # Check for container-related environment variables\n        container_indicators = ['HOSTNAME', 'INSTANCE_ID', 'SERVICE_PORT']\n        return any(os.getenv(indicator) for indicator in container_indicators)\n    \n    def _generate_instance_id(self) -> str:
        """Generate standardized instance ID"""
        # Use container ID if available, otherwise generate UUID
        container_id = os.getenv('HOSTNAME', str(uuid.uuid4())[:8])
        return container_id[:8]  # Keep it short but unique
    
    def _get_host_info(self) -> Dict[str, str]:
        """Get standardized host information"""
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
        except:
            hostname = "unknown"
            local_ip = "0.0.0.0"
        
        return {
            "hostname": hostname,
            "local_ip": local_ip,
            "port": os.getenv('SERVICE_PORT', '8000'),
            "container_id": os.getenv('HOSTNAME', 'local'),
        }
    
    def get_service_info(self) -> ServiceInfo:
        """Get complete AI Brain enhanced service information"""
        # Calculate overall architecture compliance
        architecture_compliance = self._calculate_architecture_compliance()
        
        return ServiceInfo(
            service_name=self.service_name,
            service_id=self.service_id,
            instance_id=self.instance_id,
            version=self.version,
            deployment_env=self.deployment_env,
            host_info=self.host_info,
            startup_time=self.startup_time,
            health_endpoint=self.health_endpoint,
            metrics_endpoint=self.metrics_endpoint,
            architecture_compliance=architecture_compliance,
            naming_standards_compliance=self.naming_compliance_score,
            microservice_patterns_compliance=self._calculate_microservice_compliance()
        )
    
    def get_service_context(self) -> Dict[str, Any]:
        """Get AI Brain enhanced service context for logging and monitoring"""
        return {
            "service_name": self.service_name,
            "service_id": self.service_id,
            "instance_id": self.instance_id,
            "version": self.version,
            "deployment_env": self.deployment_env,
            "hostname": self.host_info["hostname"],
            "local_ip": self.host_info["local_ip"],
            "port": self.host_info["port"],
            "uptime_seconds": (datetime.utcnow() - self.startup_time).total_seconds(),
            # AI Brain Architecture Context
            "architecture_compliance": self._calculate_architecture_compliance(),
            "naming_compliance": self.naming_compliance_score,
            "microservice_patterns_compliance": self._calculate_microservice_compliance(),
            "architecture_violations": len(self.architecture_violations)
        }
    
    def get_service_tags(self) -> Dict[str, str]:
        """Get standardized service tags for monitoring systems"""
        return {
            "service": self.service_name,
            "instance": self.instance_id,
            "version": self.version,
            "environment": self.deployment_env,
            "host": self.host_info["hostname"]
        }
    
    def _calculate_architecture_compliance(self) -> Dict[str, float]:
        \"\"\"AI Brain: Calculate overall architecture compliance scores\"\"\"
        return {
            'naming_standards': self.naming_compliance_score,\n            'microservice_patterns': self._calculate_microservice_compliance(),\n            'endpoint_patterns': self._calculate_endpoint_compliance(),\n            'overall': self._calculate_overall_compliance()\n        }\n    \n    def _calculate_microservice_compliance(self) -> float:\n        \"\"\"Calculate microservice pattern compliance score\"\"\"\n        if not hasattr(self, 'microservice_patterns') or not self.microservice_patterns:\n            return 0.0\n        \n        compliant_patterns = sum(1 for compliant in self.microservice_patterns.values() if compliant)\n        total_patterns = len(self.microservice_patterns)\n        \n        return compliant_patterns / total_patterns if total_patterns > 0 else 0.0\n    \n    def _calculate_endpoint_compliance(self) -> float:\n        \"\"\"Calculate endpoint pattern compliance score\"\"\"\n        endpoint_violations = [v for v in self.architecture_violations if v['type'] == 'ENDPOINT_PATTERN']\n        # Start with perfect score, deduct for violations\n        return max(0.0, 1.0 - (len(endpoint_violations) * 0.2))\n    \n    def _calculate_overall_compliance(self) -> float:\n        \"\"\"Calculate overall architecture compliance score\"\"\"\n        # Weighted average of all compliance scores\n        weights = {\n            'naming_standards': 0.3,\n            'microservice_patterns': 0.5,\n            'endpoint_patterns': 0.2\n        }\n        \n        total_score = 0.0\n        for category, weight in weights.items():\n            if category == 'naming_standards':\n                total_score += self.naming_compliance_score * weight\n            elif category == 'microservice_patterns':\n                total_score += self._calculate_microservice_compliance() * weight\n            elif category == 'endpoint_patterns':\n                total_score += self._calculate_endpoint_compliance() * weight\n        \n        return total_score\n    \n    def get_architecture_report(self) -> Dict[str, Any]:\n        \"\"\"AI Brain: Get detailed architecture compliance report\"\"\"\n        compliance = self._calculate_architecture_compliance()\n        \n        # Categorize violations by severity\n        violations_by_severity = {\n            'CRITICAL': [],\n            'HIGH': [],\n            'MEDIUM': [],\n            'LOW': []\n        }\n        \n        for violation in self.architecture_violations:\n            severity = violation.get('severity', 'MEDIUM')\n            violations_by_severity[severity].append(violation)\n        \n        return {\n            'service_name': self.service_name,\n            'overall_compliance': compliance['overall'],\n            'compliance_details': compliance,\n            'total_violations': len(self.architecture_violations),\n            'violations_by_severity': violations_by_severity,\n            'microservice_patterns': self.microservice_patterns,\n            'recommendations': self._generate_architecture_recommendations(),\n            'timestamp': datetime.utcnow().isoformat()\n        }\n    \n    def _generate_architecture_recommendations(self) -> List[str]:\n        \"\"\"Generate architecture improvement recommendations\"\"\"\n        recommendations = []\n        \n        if self.naming_compliance_score < 0.8:\n            recommendations.append(\"Improve service naming to follow kebab-case and domain-specific patterns\")\n        \n        if self._calculate_microservice_compliance() < 0.7:\n            recommendations.append(\"Review microservice patterns compliance, especially single responsibility and bounded context\")\n        \n        if any(v['type'] == 'ENDPOINT_PATTERN' for v in self.architecture_violations):\n            recommendations.append(\"Update endpoint patterns to follow standard /health/{service} and /metrics/{service} format\")\n        \n        critical_violations = [v for v in self.architecture_violations if v.get('severity') == 'CRITICAL']\n        if critical_violations:\n            recommendations.append(\"Address critical architecture violations immediately\")\n        \n        if not self.microservice_patterns.get('containerization_ready', True):\n            recommendations.append(\"Prepare service for containerization with proper environment variable handling\")\n        \n        return recommendations\n    \n    def validate_service_boundary(self, target_service: str) -> Tuple[bool, Dict[str, Any]]:
        """
        AI Brain Enhanced: Validate if this service should communicate with target service.
        Implements service boundary validation patterns with detailed analysis.
        
        Returns:
            Tuple of (is_allowed, validation_details)
        """
        # Define allowed service communication patterns with AI Brain architecture standards
        ALLOWED_COMMUNICATIONS = {
            "ml-processing": ["data-bridge", "database-service", "ai-provider"],
            "ai-orchestration": ["ai-provider", "ml-processing", "deep-learning"],
            "trading-engine": ["data-bridge", "ml-processing", "database-service"],
            "api-gateway": ["*"],  # API gateway can communicate with all services
            "data-bridge": ["database-service", "trading-engine", "ml-processing"],
            "database-service": ["*"],  # Database service can be accessed by all
            "deep-learning": ["ai-provider", "database-service"],
            "ai-provider": ["*"],  # AI provider can be accessed by all AI services
            "user-service": ["database-service", "api-gateway"]
        }
        
        allowed = ALLOWED_COMMUNICATIONS.get(self.service_name, [])
        is_allowed = "*" in allowed or target_service in allowed
        
        # Calculate confidence score for this communication
        confidence_score = self._calculate_communication_confidence(target_service, allowed)
        
        validation_details = {
            'source_service': self.service_name,
            'target_service': target_service,
            'is_allowed': is_allowed,
            'confidence_score': confidence_score,
            'allowed_targets': allowed,
            'communication_pattern': self._analyze_communication_pattern(target_service),
            'architecture_compliance': is_allowed,
            'recommendations': self._generate_communication_recommendations(target_service, is_allowed)
        }
        
        return is_allowed, validation_details
    
    def _calculate_communication_confidence(self, target_service: str, allowed: List[str]) -> float:
        """Calculate confidence score for service communication"""
        if "*" in allowed:
            return 1.0  # Universal access allowed
        elif target_service in allowed:
            return 0.95  # Explicitly allowed
        elif self._is_infrastructure_service(target_service):
            return 0.7  # Infrastructure services often needed
        else:
            return 0.1  # Not allowed, very low confidence
    
    def _analyze_communication_pattern(self, target_service: str) -> str:
        """Analyze the type of communication pattern"""
        patterns = {
            'database-service': 'DATA_PERSISTENCE',
            'api-gateway': 'EXTERNAL_INTERFACE',
            'ai-provider': 'AI_COMPUTATION',
            'ml-processing': 'MACHINE_LEARNING',
            'user-service': 'USER_MANAGEMENT',
            'trading-engine': 'BUSINESS_LOGIC'
        }
        
        return patterns.get(target_service, 'PEER_SERVICE')
    
    def _generate_communication_recommendations(self, target_service: str, is_allowed: bool) -> List[str]:
        """Generate recommendations for service communication"""
        recommendations = []
        
        if not is_allowed:
            recommendations.append(f"Communication with {target_service} violates service boundary architecture")
            recommendations.append("Consider using an intermediary service or API gateway")
            recommendations.append("Review if this communication indicates a missing service boundary")
        
        if self._is_potential_circular_dependency(target_service):
            recommendations.append("Potential circular dependency detected - review architecture")
        
        if not self._follows_layered_architecture(target_service):
            recommendations.append("Communication pattern may violate layered architecture principles")
        
        return recommendations
    
    def _is_infrastructure_service(self, service_name: str) -> bool:
        """Check if service is an infrastructure service"""
        infrastructure_services = ['database-service', 'cache-service', 'message-queue', 'logging-service']
        return service_name in infrastructure_services
    
    def _is_potential_circular_dependency(self, target_service: str) -> bool:
        """Detect potential circular dependencies"""
        # Simplified circular dependency detection
        if target_service == self.service_name:
            return True
        
        # Check for known circular patterns
        circular_patterns = [
            ('ml-processing', 'ai-orchestration'),
            ('trading-engine', 'data-bridge')
        ]
        
        for service1, service2 in circular_patterns:
            if (self.service_name == service1 and target_service == service2) or \
               (self.service_name == service2 and target_service == service1):
                return True
        
        return False
    
    def _follows_layered_architecture(self, target_service: str) -> bool:
        """Check if communication follows layered architecture principles"""
        # Define service layers (higher numbers = higher layer)
        service_layers = {
            'api-gateway': 4,
            'user-service': 3,
            'trading-engine': 3,
            'ai-orchestration': 3,
            'ml-processing': 2,
            'data-bridge': 2,
            'ai-provider': 1,
            'database-service': 1,
            'deep-learning': 1
        }
        
        source_layer = service_layers.get(self.service_name, 2)
        target_layer = service_layers.get(target_service, 2)
        
        # Services should generally communicate with same level or lower levels
        return target_layer <= source_layer or target_service in ['database-service', 'ai-provider']
    
    def generate_request_id(self, prefix: str = "req") -> str:
        """Generate standardized request ID for tracing"""
        timestamp = int(datetime.utcnow().timestamp() * 1000)
        return f"{prefix}-{self.service_name}-{self.instance_id}-{timestamp}"
    
    def is_production(self) -> bool:
        """Check if service is running in production environment"""
        return self.deployment_env.lower() in ['production', 'prod']
    
    def is_development(self) -> bool:
        """Check if service is running in development environment"""
        return self.deployment_env.lower() in ['development', 'dev', 'local']


# Service Identity Singleton for consistent usage across service
_service_identity = None

def get_service_identity(service_name: str = None, version: str = "1.0.0") -> ServiceIdentityCore:
    """
    Get or create service identity singleton.
    Service name is auto-detected from environment or provided explicitly.
    """
    global _service_identity
    
    if _service_identity is None:
        if service_name is None:
            # Auto-detect service name from environment or working directory
            service_name = os.getenv('SERVICE_NAME', os.path.basename(os.getcwd()))
        
        _service_identity = ServiceIdentityCore(service_name, version)
    
    return _service_identity

def get_service_context() -> Dict[str, Any]:
    """Get current service context for logging"""
    identity = get_service_identity()
    return identity.get_service_context()

def get_service_tags() -> Dict[str, str]:
    """Get current service tags for monitoring"""
    identity = get_service_identity()
    return identity.get_service_tags()