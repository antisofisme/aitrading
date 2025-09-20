"""
AI Brain Enhanced Environment Core - Security-validated environment management
Enhanced with AI Brain Security Validator for systematic credential security
"""
import os
import re
import hashlib
from typing import Dict, Any, Optional, Union, List, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from .service_identity_core import get_service_identity

# AI Brain Integration
try:
    import sys
    sys.path.append('/mnt/f/WINDSURF/concept_ai/projects/ai_trading/server_microservice/services')
    from shared.ai_brain_confidence_framework import AiBrainConfidenceFramework
    from shared.ai_brain_trading_error_dna import AiBrainTradingErrorDNA
    AI_BRAIN_AVAILABLE = True
except ImportError:
    AI_BRAIN_AVAILABLE = False

class SecurityValidationLevel(Enum):
    """Security validation levels for environment variables"""
    MINIMAL = "minimal"  # Basic validation only
    STANDARD = "standard"  # Standard security checks
    STRICT = "strict"  # Comprehensive security validation
    PARANOID = "paranoid"  # Maximum security with all patterns

class EnvironmentType(Enum):
    """Standardized environment types"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

@dataclass
class SecurityValidationResult:
    """Result of security validation for environment variables"""
    is_secure: bool
    security_score: float
    violations: List[Dict[str, Any]]
    recommendations: List[str]
    ai_brain_confidence: float
    hardcoded_secrets: List[Dict[str, Any]]
    credential_exposure: List[Dict[str, Any]]
    validation_timestamp: str

@dataclass
class EnvironmentConfig:
    """Standardized environment configuration structure"""
    environment: EnvironmentType
    service_name: str
    service_port: int
    debug_mode: bool
    log_level: str
    
    # Database configuration
    database_url: Optional[str]
    redis_url: Optional[str]
    
    # External service URLs
    ai_provider_urls: Dict[str, str]
    monitoring_urls: Dict[str, str]
    
    # Security configuration
    jwt_secret: Optional[str]
    api_keys: Dict[str, str]
    
    # AI Brain Security Validation
    security_validation: Optional[SecurityValidationResult]
    
    # Service-specific configuration
    service_config: Dict[str, Any]

class EnvironmentCore:
    """
    AI Brain Enhanced environment variable management for microservices.
    Provides consistent environment variable patterns with comprehensive security validation.
    
    Features:
    - Hardcoded secrets detection and prevention
    - Credential management validation
    - Security best practices enforcement
    - AI Brain confidence-based validation
    - Surgical precision error prevention
    """
    
    def __init__(self, service_name: str = None, security_level: SecurityValidationLevel = SecurityValidationLevel.STANDARD):
        """Initialize AI Brain Enhanced environment management with security validation"""
        self.service_identity = get_service_identity(service_name)
        self.service_name = self.service_identity.service_name
        self.security_level = security_level
        
        # Standard environment variable prefixes
        self.service_prefix = f"{self.service_name.upper().replace('-', '_')}_"
        self.global_prefix = "NELITI_"
        
        # AI Brain Security Validator Integration
        self.ai_brain_confidence = None
        self.ai_brain_error_dna = None
        if AI_BRAIN_AVAILABLE:
            try:
                self.ai_brain_confidence = AiBrainConfidenceFramework(f"env-security-{self.service_name}")
                self.ai_brain_error_dna = AiBrainTradingErrorDNA(f"env-validator-{self.service_name}")
                print(f"✅ AI Brain Security Validator initialized for environment: {self.service_name}")
            except Exception as e:
                print(f"⚠️ AI Brain Security Validator initialization failed: {e}")
        
        # Security patterns for hardcoded secret detection
        self._init_security_patterns()
        
        # Load environment configuration with security validation
        self.config = self._load_environment_config()
        
    def _load_environment_config(self) -> EnvironmentConfig:
        """Load standardized environment configuration"""
        # Determine environment type
        env_str = self.get_env("DEPLOYMENT_ENV", "development")
        try:
            environment = EnvironmentType(env_str.lower())
        except ValueError:
            environment = EnvironmentType.DEVELOPMENT
        
        # Load core configuration
        service_port = self.get_env_int(f"{self.service_prefix}PORT", 8000)
        debug_mode = self.get_env_bool(f"{self.global_prefix}DEBUG", environment == EnvironmentType.DEVELOPMENT)
        log_level = self.get_env(f"{self.global_prefix}LOG_LEVEL", "INFO" if environment == EnvironmentType.PRODUCTION else "DEBUG")
        
        # Database configuration
        database_url = self.get_env(f"{self.global_prefix}DATABASE_URL")
        redis_url = self.get_env(f"{self.global_prefix}REDIS_URL")
        
        # AI Provider URLs
        ai_provider_urls = {
            "openai": self.get_env(f"{self.global_prefix}OPENAI_BASE_URL", "https://api.openai.com/v1"),
            "anthropic": self.get_env(f"{self.global_prefix}ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
            "langfuse": self.get_env(f"{self.global_prefix}LANGFUSE_HOST", "https://cloud.langfuse.com"),
            "handit": self.get_env(f"{self.global_prefix}HANDIT_BASE_URL", "https://api.handit.ai")
        }
        
        # Monitoring URLs
        monitoring_urls = {
            "prometheus": self.get_env(f"{self.global_prefix}PROMETHEUS_URL", "http://localhost:9090"),
            "grafana": self.get_env(f"{self.global_prefix}GRAFANA_URL", "http://localhost:3000"),
            "jaeger": self.get_env(f"{self.global_prefix}JAEGER_URL", "http://localhost:14268")
        }
        
        # Security configuration
        jwt_secret = self.get_env(f"{self.global_prefix}JWT_SECRET")
        api_keys = {
            "openai": self.get_env(f"{self.global_prefix}OPENAI_API_KEY"),
            "anthropic": self.get_env(f"{self.global_prefix}ANTHROPIC_API_KEY"),
            "langfuse_public": self.get_env(f"{self.global_prefix}LANGFUSE_PUBLIC_KEY"),
            "langfuse_secret": self.get_env(f"{self.global_prefix}LANGFUSE_SECRET_KEY"),
            "handit": self.get_env(f"{self.global_prefix}HANDIT_API_KEY")
        }
        
        # Service-specific configuration
        service_config = self._load_service_specific_config()
        
        # Perform AI Brain Security Validation
        security_validation = self._perform_security_validation({
            'database_url': database_url,
            'jwt_secret': jwt_secret,
            'api_keys': api_keys,
            'ai_provider_urls': ai_provider_urls,
            'monitoring_urls': monitoring_urls,
            'service_config': service_config
        })
        
        return EnvironmentConfig(
            environment=environment,
            service_name=self.service_name,
            service_port=service_port,
            debug_mode=debug_mode,
            log_level=log_level,
            database_url=database_url,
            redis_url=redis_url,
            ai_provider_urls=ai_provider_urls,
            monitoring_urls=monitoring_urls,
            jwt_secret=jwt_secret,
            api_keys=api_keys,
            service_config=service_config,
            security_validation=security_validation
        )
    
    def _load_service_specific_config(self) -> Dict[str, Any]:
        """Load service-specific environment configuration"""
        config = {}
        
        if self.service_name == "ml-processing":
            config.update({
                "model_path": self.get_env(f"{self.service_prefix}MODEL_PATH", "/models"),
                "gpu_enabled": self.get_env_bool(f"{self.service_prefix}GPU_ENABLED", False),
                "batch_size": self.get_env_int(f"{self.service_prefix}BATCH_SIZE", 32),
                "max_sequence_length": self.get_env_int(f"{self.service_prefix}MAX_SEQUENCE_LENGTH", 512),
                "inference_timeout": self.get_env_int(f"{self.service_prefix}INFERENCE_TIMEOUT", 30)
            })
        
        elif self.service_name == "trading-engine":
            config.update({
                "mt5_server": self.get_env(f"{self.service_prefix}MT5_SERVER"),
                "mt5_login": self.get_env_int(f"{self.service_prefix}MT5_LOGIN"),
                "mt5_password": self.get_env(f"{self.service_prefix}MT5_PASSWORD"),
                "risk_limit": self.get_env_float(f"{self.service_prefix}RISK_LIMIT", 0.02),
                "max_positions": self.get_env_int(f"{self.service_prefix}MAX_POSITIONS", 10),
                "trading_enabled": self.get_env_bool(f"{self.service_prefix}TRADING_ENABLED", False)
            })
        
        elif self.service_name == "data-bridge":
            config.update({
                "websocket_host": self.get_env(f"{self.service_prefix}WEBSOCKET_HOST", "localhost"),
                "websocket_port": self.get_env_int(f"{self.service_prefix}WEBSOCKET_PORT", 8765),
                "data_retention_days": self.get_env_int(f"{self.service_prefix}DATA_RETENTION_DAYS", 30),
                "batch_size": self.get_env_int(f"{self.service_prefix}BATCH_SIZE", 1000),
                "streaming_enabled": self.get_env_bool(f"{self.service_prefix}STREAMING_ENABLED", True)
            })
        
        elif self.service_name == "database-service":
            config.update({
                "connection_pool_size": self.get_env_int(f"{self.service_prefix}CONNECTION_POOL_SIZE", 20),
                "connection_timeout": self.get_env_int(f"{self.service_prefix}CONNECTION_TIMEOUT", 30),
                "query_timeout": self.get_env_int(f"{self.service_prefix}QUERY_TIMEOUT", 60),
                "backup_enabled": self.get_env_bool(f"{self.service_prefix}BACKUP_ENABLED", True),
                "backup_interval_hours": self.get_env_int(f"{self.service_prefix}BACKUP_INTERVAL_HOURS", 24)
            })
        
        elif self.service_name == "ai-provider":
            config.update({
                "provider_timeout": self.get_env_int(f"{self.service_prefix}PROVIDER_TIMEOUT", 30),
                "max_retries": self.get_env_int(f"{self.service_prefix}MAX_RETRIES", 3),
                "rate_limit_enabled": self.get_env_bool(f"{self.service_prefix}RATE_LIMIT_ENABLED", True),
                "cache_responses": self.get_env_bool(f"{self.service_prefix}CACHE_RESPONSES", True),
                "cache_ttl_seconds": self.get_env_int(f"{self.service_prefix}CACHE_TTL_SECONDS", 3600)
            })
        
        elif self.service_name == "api-gateway":
            config.update({
                "cors_origins": self.get_env_list(f"{self.service_prefix}CORS_ORIGINS", ["*"]),
                "rate_limit_requests": self.get_env_int(f"{self.service_prefix}RATE_LIMIT_REQUESTS", 1000),
                "rate_limit_window": self.get_env_int(f"{self.service_prefix}RATE_LIMIT_WINDOW", 3600),
                "auth_required": self.get_env_bool(f"{self.service_prefix}AUTH_REQUIRED", True),
                "request_timeout": self.get_env_int(f"{self.service_prefix}REQUEST_TIMEOUT", 30)
            })
        
        elif self.service_name == "deep-learning":
            config.update({
                "model_cache_size": self.get_env_int(f"{self.service_prefix}MODEL_CACHE_SIZE", 5),
                "training_enabled": self.get_env_bool(f"{self.service_prefix}TRAINING_ENABLED", False),
                "gpu_memory_fraction": self.get_env_float(f"{self.service_prefix}GPU_MEMORY_FRACTION", 0.8),
                "mixed_precision": self.get_env_bool(f"{self.service_prefix}MIXED_PRECISION", True),
                "checkpoint_interval": self.get_env_int(f"{self.service_prefix}CHECKPOINT_INTERVAL", 1000)
            })
        
        elif self.service_name == "user-service":
            config.update({
                "session_timeout": self.get_env_int(f"{self.service_prefix}SESSION_TIMEOUT", 3600),
                "password_min_length": self.get_env_int(f"{self.service_prefix}PASSWORD_MIN_LENGTH", 8),
                "max_login_attempts": self.get_env_int(f"{self.service_prefix}MAX_LOGIN_ATTEMPTS", 5),
                "email_verification": self.get_env_bool(f"{self.service_prefix}EMAIL_VERIFICATION", True),
                "two_factor_auth": self.get_env_bool(f"{self.service_prefix}TWO_FACTOR_AUTH", False)
            })
        
        elif self.service_name == "ai-orchestration":
            config.update({
                "workflow_timeout": self.get_env_int(f"{self.service_prefix}WORKFLOW_TIMEOUT", 300),
                "max_concurrent_workflows": self.get_env_int(f"{self.service_prefix}MAX_CONCURRENT_WORKFLOWS", 10),
                "retry_failed_tasks": self.get_env_bool(f"{self.service_prefix}RETRY_FAILED_TASKS", True),
                "task_queue_size": self.get_env_int(f"{self.service_prefix}TASK_QUEUE_SIZE", 1000),
                "enable_workflow_monitoring": self.get_env_bool(f"{self.service_prefix}ENABLE_WORKFLOW_MONITORING", True)
            })
        
        return config
    
    def _init_security_patterns(self):
        """Initialize security patterns for hardcoded secrets detection"""
        self.security_patterns = {
            # Hardcoded secrets patterns (from AI Brain security-validator.js)
            'secrets': [
                re.compile(r'password\s*[:=]\s*["\'][^"\']+["\']', re.IGNORECASE),
                re.compile(r'api[_-]?key\s*[:=]\s*["\'][^"\']+["\']', re.IGNORECASE),
                re.compile(r'secret\s*[:=]\s*["\'][^"\']+["\']', re.IGNORECASE),
                re.compile(r'token\s*[:=]\s*["\'][^"\']+["\']', re.IGNORECASE),
                re.compile(r'access[_-]?key\s*[:=]\s*["\'][^"\']+["\']', re.IGNORECASE),
                re.compile(r'private[_-]?key\s*[:=]\s*["\'][^"\']+["\']', re.IGNORECASE),
                re.compile(r'database[_-]?url\s*[:=]\s*["\'][^"\']+["\']', re.IGNORECASE),
                re.compile(r'connection[_-]?string\s*[:=]\s*["\'][^"\']+["\']', re.IGNORECASE),
                re.compile(r'jwt[_-]?secret\s*[:=]\s*["\'][^"\']+["\']', re.IGNORECASE),
                re.compile(r'encryption[_-]?key\s*[:=]\s*["\'][^"\']+["\']', re.IGNORECASE),
            ],
            
            # Credential exposure patterns
            'credentials': [
                re.compile(r'username\s*[:=]\s*["\'][^"\']+["\']', re.IGNORECASE),
                re.compile(r'email\s*[:=]\s*["\'][^"\'@]+@[^"\']+["\']', re.IGNORECASE),
                re.compile(r'auth\s*[:=]\s*["\'][^"\']+["\']', re.IGNORECASE),
                re.compile(r'bearer\s+[a-zA-Z0-9._-]+', re.IGNORECASE),
                re.compile(r'basic\s+[a-zA-Z0-9+/=]+', re.IGNORECASE),
            ],
            
            # Hardcoded configuration values
            'hardcoded': [
                re.compile(r'https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', re.IGNORECASE),  # URLs
                re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'),  # IP addresses
                re.compile(r'localhost:\d+', re.IGNORECASE),  # localhost with port
                re.compile(r'port\s*[:=]\s*\d+', re.IGNORECASE),  # Port numbers
            ]
        }
        
        # Allowed patterns (exemptions for false positives)
        self.allowed_patterns = [
            'process.env.',
            'os.getenv(',
            'os.environ.get(',
            'config.get(',
            'getSecret(',
            'fromEnv(',
            'vault.get(',
            'credentials.load(',
            'self.get_env(',
        ]
        
        # Security best practices for environment variables
        self.required_env_vars = {
            'production': [
                'DATABASE_URL',
                'JWT_SECRET',
                'API_KEY',
                'ENCRYPTION_KEY'
            ],
            'all_environments': [
                'DEPLOYMENT_ENV',
                'LOG_LEVEL'
            ]
        }
    
    def _perform_security_validation(self, config_data: Dict[str, Any]) -> SecurityValidationResult:
        """Perform comprehensive AI Brain security validation on configuration data"""
        violations = []
        hardcoded_secrets = []
        credential_exposure = []
        recommendations = []
        ai_brain_confidence = 0.85  # Default confidence
        
        try:
            # Convert configuration data to string for pattern matching
            config_str = str(config_data)
            
            # 1. Scan for hardcoded secrets
            print(f"🔍 AI Brain: Scanning for hardcoded secrets in {self.service_name}")
            secrets_found = self._detect_hardcoded_secrets(config_str)
            if secrets_found:
                hardcoded_secrets.extend(secrets_found)
                violations.extend([{
                    'type': 'HARDCODED_SECRET',
                    'severity': 'CRITICAL',
                    'message': f'Hardcoded secret detected: {secret["type"]}',
                    'location': secret['location'],
                    'recommendation': 'Use environment variables or secure vault'
                } for secret in secrets_found])
                
            # 2. Scan for credential exposure
            print(f"🔍 AI Brain: Scanning for credential exposure in {self.service_name}")
            creds_found = self._detect_credential_exposure(config_str)
            if creds_found:
                credential_exposure.extend(creds_found)
                violations.extend([{
                    'type': 'CREDENTIAL_EXPOSURE',
                    'severity': 'HIGH',
                    'message': f'Credential exposure detected: {cred["type"]}',
                    'location': cred['location'],
                    'recommendation': 'Use secure credential management system'
                } for cred in creds_found])
                
            # 3. Check required environment variables
            print(f"🔍 AI Brain: Validating required environment variables for {self.service_name}")
            missing_env_vars = self._check_required_env_vars()
            if missing_env_vars:
                violations.extend([{
                    'type': 'MISSING_REQUIRED_ENV_VAR',
                    'severity': 'HIGH',
                    'message': f'Required environment variable missing: {env_var}',
                    'location': 'environment',
                    'recommendation': f'Set {env_var} in environment or configuration'
                } for env_var in missing_env_vars])
                
            # 4. AI Brain confidence analysis
            if self.ai_brain_confidence and AI_BRAIN_AVAILABLE:
                try:
                    confidence_result = self.ai_brain_confidence.assess_decision_confidence(
                        decision_type="environment_security",
                        factors={
                            "secrets_found": len(hardcoded_secrets),
                            "credentials_exposed": len(credential_exposure),
                            "missing_env_vars": len(missing_env_vars),
                            "security_level": self.security_level.value
                        },
                        context={
                            "service_name": self.service_name,
                            "validation_type": "security_scan"
                        }
                    )
                    ai_brain_confidence = confidence_result.get("confidence_score", 0.85)
                    
                    if confidence_result.get("recommendations"):
                        recommendations.extend(confidence_result["recommendations"])
                        
                except Exception as e:
                    print(f"⚠️ AI Brain confidence analysis failed: {e}")
                    
            # 5. Calculate security score
            security_score = self._calculate_security_score(violations, ai_brain_confidence)
            
            # 6. Generate security recommendations
            if not recommendations:  # Only if AI Brain didn't provide recommendations
                recommendations = self._generate_security_recommendations(violations)
                
            # 7. Determine if configuration is secure
            is_secure = (security_score >= 0.8 and 
                        len([v for v in violations if v['severity'] == 'CRITICAL']) == 0)
                        
            print(f"🛡️ AI Brain Security Validation Complete: Score {security_score:.2f}, Secure: {is_secure}")
            
            return SecurityValidationResult(
                is_secure=is_secure,
                security_score=security_score,
                violations=violations,
                recommendations=recommendations,
                ai_brain_confidence=ai_brain_confidence,
                hardcoded_secrets=hardcoded_secrets,
                credential_exposure=credential_exposure,
                validation_timestamp=datetime.utcnow().isoformat()
            )
            
        except Exception as e:
            # Graceful degradation when security validation fails
            print(f"⚠️ AI Brain Security validation failed: {e}")
            if self.ai_brain_error_dna:
                try:
                    self.ai_brain_error_dna.analyze_error(e, {
                        "service_name": self.service_name,
                        "operation": "security_validation"
                    })
                except:
                    pass  # Silent fallback if error DNA also fails
                    
            return SecurityValidationResult(
                is_secure=False,
                security_score=0.0,
                violations=[{
                    'type': 'SECURITY_VALIDATION_ERROR',
                    'severity': 'HIGH',
                    'message': f'Security validation failed: {str(e)}',
                    'location': 'security_validator',
                    'recommendation': 'Review security validation configuration'
                }],
                recommendations=['Manual security review required'],
                ai_brain_confidence=0.0,
                hardcoded_secrets=[],
                credential_exposure=[],
                validation_timestamp=datetime.utcnow().isoformat()
            )
    
    def get_env(self, key: str, default: str = None) -> Optional[str]:
        """Get environment variable with optional default"""
        return os.getenv(key, default)
    
    def get_env_int(self, key: str, default: int = None) -> Optional[int]:
        """Get environment variable as integer"""
        value = os.getenv(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default
    
    def get_env_float(self, key: str, default: float = None) -> Optional[float]:
        """Get environment variable as float"""
        value = os.getenv(key)
        if value is None:
            return default
        try:
            return float(value)
        except ValueError:
            return default
    
    def get_env_bool(self, key: str, default: bool = False) -> bool:
        """Get environment variable as boolean"""
        value = os.getenv(key)
        if value is None:
            return default
        return value.lower() in ('true', '1', 'yes', 'on', 'enabled')
    
    def get_env_list(self, key: str, default: List[str] = None) -> List[str]:
        """Get environment variable as list (comma-separated)"""
        value = os.getenv(key)
        if value is None:
            return default or []
        return [item.strip() for item in value.split(',') if item.strip()]
    
    def get_required_env(self, key: str) -> str:
        """Get required environment variable (raises error if missing)"""
        value = os.getenv(key)
        if value is None:
            raise ValueError(f"Required environment variable {key} is not set")
        return value
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.config.environment == EnvironmentType.PRODUCTION
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.config.environment == EnvironmentType.DEVELOPMENT
    
    def is_testing(self) -> bool:
        """Check if running in testing environment"""
        return self.config.environment == EnvironmentType.TESTING
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration for service"""
        if not self.config.database_url:
            raise ValueError("Database URL not configured")
        
        return {
            "database_url": self.config.database_url,
            "pool_size": self.config.service_config.get("connection_pool_size", 10),
            "timeout": self.config.service_config.get("connection_timeout", 30),
            "ssl_mode": "require" if self.is_production() else "prefer"
        }
    
    def get_ai_provider_config(self, provider: str) -> Dict[str, Any]:
        """Get AI provider configuration"""
        base_url = self.config.ai_provider_urls.get(provider)
        api_key = self.config.api_keys.get(provider)
        
        if not base_url:
            raise ValueError(f"AI provider {provider} not configured")
        
        config = {
            "base_url": base_url,
            "timeout": self.config.service_config.get("provider_timeout", 30),
            "max_retries": self.config.service_config.get("max_retries", 3)
        }
        
        if api_key:
            config["api_key"] = api_key
        
        return config
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration"""
        return {
            "prometheus_url": self.config.monitoring_urls.get("prometheus"),
            "grafana_url": self.config.monitoring_urls.get("grafana"),
            "jaeger_url": self.config.monitoring_urls.get("jaeger"),
            "service_name": self.service_name,
            "environment": self.config.environment.value
        }
    
    def validate_required_config(self) -> List[str]:
        """Validate that all required configuration is present"""
        missing = []
        
        # Check required global configuration
        if self.is_production():
            if not self.config.database_url:
                missing.append("DATABASE_URL")
            if not self.config.jwt_secret:
                missing.append("JWT_SECRET")
        
        # Check service-specific required configuration
        if self.service_name == "trading-engine":
            for key in ["mt5_server", "mt5_login", "mt5_password"]:
                if not self.config.service_config.get(key):
                    missing.append(f"{self.service_prefix}{key.upper()}")
        
        elif self.service_name == "ai-provider":
            # At least one AI provider API key should be configured
            ai_keys = [k for k, v in self.config.api_keys.items() if v and k in ["openai", "anthropic"]]
            if not ai_keys:
                missing.append("At least one AI provider API key (OPENAI_API_KEY or ANTHROPIC_API_KEY)")
        
        return missing
    
    def _detect_hardcoded_secrets(self, config_str: str) -> List[Dict[str, Any]]:
        """Detect hardcoded secrets in configuration string"""
        secrets_found = []
        
        for pattern in self.security_patterns['secrets']:
            matches = pattern.finditer(config_str)
            for match in matches:
                # Check if it's an allowed pattern (false positive)
                is_allowed = any(allowed in match.group() for allowed in self.allowed_patterns)
                
                if not is_allowed:
                    secrets_found.append({
                        'type': 'hardcoded_secret',
                        'pattern': pattern.pattern,
                        'match': self._obfuscate_secret(match.group()),
                        'location': f'position_{match.start()}'
                    })
                    
        return secrets_found
    
    def _detect_credential_exposure(self, config_str: str) -> List[Dict[str, Any]]:
        """Detect credential exposure in configuration string"""
        credentials_found = []
        
        for pattern in self.security_patterns['credentials']:
            matches = pattern.finditer(config_str)
            for match in matches:
                is_allowed = any(allowed in match.group() for allowed in self.allowed_patterns)
                
                if not is_allowed:
                    credentials_found.append({
                        'type': 'credential_exposure',
                        'pattern': pattern.pattern,
                        'match': self._obfuscate_secret(match.group()),
                        'location': f'position_{match.start()}'
                    })
                    
        return credentials_found
    
    def _check_required_env_vars(self) -> List[str]:
        """Check for missing required environment variables"""
        missing = []
        
        # Check environment-specific required variables
        if self.is_production():
            for env_var in self.required_env_vars['production']:
                if not os.getenv(f"{self.global_prefix}{env_var}"):
                    missing.append(f"{self.global_prefix}{env_var}")
                    
        # Check variables required in all environments
        for env_var in self.required_env_vars['all_environments']:
            if not os.getenv(env_var):
                missing.append(env_var)
                
        return missing
    
    def _calculate_security_score(self, violations: List[Dict[str, Any]], ai_brain_confidence: float) -> float:
        """Calculate security score based on violations and AI Brain confidence"""
        base_score = 1.0
        
        # Deduct points for violations based on severity
        for violation in violations:
            if violation['severity'] == 'CRITICAL':
                base_score -= 0.3
            elif violation['severity'] == 'HIGH':
                base_score -= 0.2
            elif violation['severity'] == 'MEDIUM':
                base_score -= 0.1
                
        # Factor in AI Brain confidence
        adjusted_score = base_score * ai_brain_confidence
        
        return max(0.0, min(1.0, adjusted_score))
    
    def _generate_security_recommendations(self, violations: List[Dict[str, Any]]) -> List[str]:
        """Generate security recommendations based on violations"""
        recommendations = []
        
        if any(v['type'] == 'HARDCODED_SECRET' for v in violations):
            recommendations.append("Remove hardcoded secrets and use environment variables")
            recommendations.append("Implement secure credential management system")
            
        if any(v['type'] == 'CREDENTIAL_EXPOSURE' for v in violations):
            recommendations.append("Implement proper authentication and authorization")
            recommendations.append("Use secure token-based authentication")
            
        if any(v['type'] == 'MISSING_REQUIRED_ENV_VAR' for v in violations):
            recommendations.append("Set all required environment variables")
            recommendations.append("Create comprehensive .env.example file")
            
        # Add general security best practices
        recommendations.extend([
            "Use HTTPS for all communications",
            "Implement proper input validation",
            "Use security headers (CORS, CSP, etc.)",
            "Implement comprehensive logging and monitoring"
        ])
        
        return list(set(recommendations))  # Remove duplicates
    
    def _obfuscate_secret(self, secret: str) -> str:
        """Obfuscate secret for safe logging"""
        if len(secret) <= 6:
            return '***'
        return secret[:3] + '*' * (len(secret) - 6) + secret[-3:]
    
    def get_security_validation_result(self) -> Optional[SecurityValidationResult]:
        """Get the security validation result from configuration"""
        return self.config.security_validation if self.config else None
    
    def is_security_validated(self) -> bool:
        """Check if configuration has passed security validation"""
        validation = self.get_security_validation_result()
        return validation.is_secure if validation else False
    
    def get_security_violations(self) -> List[Dict[str, Any]]:
        """Get list of security violations found during validation"""
        validation = self.get_security_validation_result()
        return validation.violations if validation else []
    
    def get_security_recommendations(self) -> List[str]:
        """Get security recommendations from validation"""
        validation = self.get_security_validation_result()
        return validation.recommendations if validation else []
    
    def get_environment_summary(self) -> Dict[str, Any]:
        """Get summary of current environment configuration with security status"""
        security_validation = self.get_security_validation_result()
        
        summary = {
            "service_name": self.service_name,
            "environment": self.config.environment.value,
            "service_port": self.config.service_port,
            "debug_mode": self.config.debug_mode,
            "log_level": self.config.log_level,
            "database_configured": bool(self.config.database_url),
            "redis_configured": bool(self.config.redis_url),
            "ai_providers_configured": [k for k, v in self.config.api_keys.items() if v],
            "service_specific_config_count": len(self.config.service_config),
            "validation_errors": self.validate_required_config()
        }
        
        # Add security validation information
        if security_validation:
            summary.update({
                "security_validated": True,
                "security_score": security_validation.security_score,
                "is_secure": security_validation.is_secure,
                "security_violations_count": len(security_validation.violations),
                "critical_security_issues": len([v for v in security_validation.violations if v['severity'] == 'CRITICAL']),
                "ai_brain_confidence": security_validation.ai_brain_confidence,
                "last_security_validation": security_validation.validation_timestamp
            })
        else:
            summary.update({
                "security_validated": False,
                "security_score": 0.0,
                "is_secure": False
            })
            
        return summary


# Service Environment Singleton
_environment_core = None

def get_environment_core(service_name: str = None, security_level: SecurityValidationLevel = SecurityValidationLevel.STANDARD) -> EnvironmentCore:
    """Get or create AI Brain Enhanced environment core singleton with security validation"""
    global _environment_core
    
    if _environment_core is None:
        _environment_core = EnvironmentCore(service_name, security_level)
    
    return _environment_core

def get_security_validation() -> Optional[SecurityValidationResult]:
    """Convenience function to get security validation result"""
    env_core = get_environment_core()
    return env_core.get_security_validation_result()

def is_environment_secure() -> bool:
    """Convenience function to check if environment is secure"""
    env_core = get_environment_core()
    return env_core.is_security_validated()

def get_config() -> EnvironmentConfig:
    """Convenience function to get environment configuration"""
    env_core = get_environment_core()
    return env_core.config

def get_service_config() -> Dict[str, Any]:
    """Convenience function to get service-specific configuration"""
    env_core = get_environment_core()
    return env_core.config.service_config

def is_production() -> bool:
    """Convenience function to check if running in production"""
    env_core = get_environment_core()
    return env_core.is_production()

def is_development() -> bool:
    """Convenience function to check if running in development"""
    env_core = get_environment_core()
    return env_core.is_development()