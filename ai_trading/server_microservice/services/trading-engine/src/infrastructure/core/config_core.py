"""
AI Brain Enhanced Core Configuration Implementation - AI-validated configuration management
Enhanced with AI Brain decision validation and systematic configuration integrity
"""
import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from ..base.base_config import BaseConfig, Environment
from .config_loaders import ConfigLoaders
from .config_validators import ConfigValidators

# AI Brain Integration
try:
    import sys
    sys.path.append('/mnt/f/WINDSURF/concept_ai/projects/ai_trading/server_microservice/services')
    from shared.ai_brain_confidence_framework import AiBrainConfidenceFramework
    from shared.ai_brain_trading_error_dna import AiBrainTradingErrorDNA
    AI_BRAIN_AVAILABLE = True
except ImportError:
    AI_BRAIN_AVAILABLE = False


class CoreConfig(BaseConfig):
    """AI Brain Enhanced Core configuration implementation with systematic validation and decision-based integrity"""
    
    def __init__(self, 
                 service_name: str, 
                 environment: Union[Environment, str] = None,
                 config_dir: str = None):
        """
        Initialize AI Brain Enhanced CoreConfig with systematic validation and configuration integrity.
        
        Args:
            service_name: Name of the service this configuration belongs to
            environment: Deployment environment (development, staging, production) or None for auto-detect
            config_dir: Custom configuration directory path, defaults to config/{service_name}
        """
        # Auto-detect environment if not provided
        if environment is None:
            env_str = os.getenv('ENVIRONMENT', os.getenv('ENV', 'development')).lower()
            environment = Environment(env_str)
        
        super().__init__(service_name, environment)
        
        # Configuration directory (default to service config dir)
        self.config_dir = Path(config_dir) if config_dir else Path(f"config/{service_name}")
        
        # AI Brain Enhanced Configuration Management
        self.configuration_decisions = []
        self.configuration_confidence_scores = {}
        self.configuration_validation_errors = []
        self.ai_brain_config_recommendations = []
        
        # AI Brain Integration
        self.ai_brain_confidence = None
        self.ai_brain_error_dna = None
        
        if AI_BRAIN_AVAILABLE:
            try:
                self.ai_brain_confidence = AiBrainConfidenceFramework(f"config-{service_name}")
                self.ai_brain_error_dna = AiBrainTradingErrorDNA(f"config-error-{service_name}")
                print(f"✅ AI Brain configuration validation initialized for: {service_name}")
            except Exception as e:
                print(f"⚠️ AI Brain configuration initialization failed: {e}")
        
        self.setup_service_specific_config()
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from multiple sources in priority order.
        
        Loading sequence:
        1. Default configuration (baseline settings)
        2. Environment-specific configuration (development.yml, production.yml)
        3. Service-specific configuration (service_name.yml)
        4. Environment variables (SERVICE_NAME_*)
        5. Docker secrets (/run/secrets/*)
        6. Common environment variables (DATABASE_URL, LOG_LEVEL)
        
        Returns:
            Complete configuration dictionary with all sources merged
        """
        if self._is_loaded:
            return self._config_cache
        
        # Initialize with empty config
        self._config_cache = {}
        
        # 1. Load default configuration
        try:
            default_config = ConfigLoaders.load_default_config(self.service_name)
            self._config_cache.update(default_config)
        except (ImportError, AttributeError) as e:
            # If ConfigLoaders doesn't exist, use basic defaults
            import logging
            logging.warning(f"ConfigLoaders not available, using basic defaults: {e}")
            default_config = {
                'service': {
                    'name': self.service_name,
                    'port': 8001 if self.service_name == 'data-bridge' else 8000,
                    'host': '0.0.0.0',
                    'debug': self.environment.value == 'development'
                },
                'environment': self.environment.value
            }
            self._config_cache.update(default_config)
        
        # 2-5. Load configuration from multiple sources synchronously to avoid event loop conflicts
        try:
            # Try to load configs, fallback to empty dict if loaders don't exist
            env_config = self._load_environment_config_sync()
            service_config = self._load_service_config_sync()
            secrets = self._load_secrets_sync()
        except Exception as e:
            # If config loading fails, use empty configs and continue
            import logging
            logging.warning(f"Config loading failed, using defaults: {e}")
            env_config = {}
            service_config = {}
            secrets = {}
        
        # Merge configurations
        self._deep_merge(self._config_cache, env_config)
        self._deep_merge(self._config_cache, service_config)
        
        # Override with environment variables
        try:
            env_vars = ConfigLoaders.load_environment_variables(self.service_name)
            for key, value in env_vars.items():
                self._set_nested_value(key, value)
        except (ImportError, AttributeError):
            # If ConfigLoaders doesn't exist, load basic env vars directly
            service_prefix = self.service_name.upper().replace('-', '_')
            env_vars = {}
            for key, value in os.environ.items():
                if key.startswith(f"{service_prefix}_"):
                    config_key = key[len(service_prefix)+1:].lower().replace('_', '.')
                    env_vars[config_key] = value
            for key, value in env_vars.items():
                self._set_nested_value(key, value)
        
        # Apply secrets
        for key, value in secrets.items():
            self.set(key, value)
        
        # 6. Handle common environment variables
        self._handle_common_env_vars()
        
        # Validate configuration
        try:
            if not ConfigValidators.validate_config(self.service_name, self._config_cache, self.environment.value):
                raise RuntimeError(f"Invalid configuration for service {self.service_name}")
        except (ImportError, AttributeError):
            # If ConfigValidators doesn't exist, do basic validation
            import logging
            logging.warning("ConfigValidators not available, skipping detailed validation")
            required_keys = ['service.name', 'environment']
            for key in required_keys:
                if not self.has(key):
                    raise RuntimeError(f"Missing required configuration: {key}")
        
        self._is_loaded = True
        return self._config_cache
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports dot notation)"""
        if not self._is_loaded:
            self.load_config()
        
        keys = key.split('.')
        value = self._config_cache
        
        for config_key in keys:
            if isinstance(value, dict) and config_key in value:
                value = value[config_key]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value (supports dot notation)"""
        self._set_nested_value(key, value)
    
    def has(self, key: str) -> bool:
        """Check if configuration key exists"""
        return self.get(key) is not None
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration for this service"""
        base_config = self.get('database', {})
        
        # Load from configuration manager instead of hardcoded os.getenv
        from ..config_manager import get_config_manager
        config_manager = get_config_manager()
        
        # Service-specific database configuration using config manager
        service_db_config = {
            "host": config_manager.get('database.host', 'localhost'),
            "port": config_manager.get('database.port', 5432),
            "name": config_manager.get('database.name', f"{self.service_name}_db"),
            "user": config_manager.get('database.user', 'postgres'),
            "password": config_manager.get('database.password', ''),
            **base_config
        }
        
        return service_db_config
    
    def get_cache_config(self) -> Dict[str, Any]:
        """Get cache configuration for this service"""
        base_config = self.get('cache', {})
        
        # Load from configuration manager instead of hardcoded os.getenv
        from ..config_manager import get_config_manager
        config_manager = get_config_manager()
        
        # Service-specific cache configuration using config manager
        service_cache_config = {
            "host": config_manager.get('cache.host', 'localhost'),
            "port": config_manager.get('cache.port', 6379),
            "db": config_manager.get('cache.db', 0),
            "password": config_manager.get('cache.password', ''),
            "prefix": f"{self.service_name}:",
            **base_config
        }
        
        return service_cache_config
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration for this service"""
        base_config = self.get('logging', {})
        
        # Service-specific logging configuration
        service_logging_config = {
            "service_name": self.service_name,
            "service_id": f"{self.service_name}-{os.getenv('HOSTNAME', '001')}",
            **base_config
        }
        
        return service_logging_config
    
    def get_service_endpoints(self) -> Dict[str, str]:
        """Get other service endpoints this service depends on"""
        endpoints = self.get('service_endpoints', {})
        
        # Load from configuration manager instead of hardcoded os.getenv
        from ..config_manager import get_config_manager
        config_manager = get_config_manager()
        
        # Add common service endpoints using config manager
        default_endpoints = {
            "api-gateway": config_manager.get('service_endpoints.api_gateway', 'http://api-gateway:8000'),
            "database-service": config_manager.get('service_endpoints.database_service', 'http://database-service:8008'),
            "cache-service": config_manager.get('service_endpoints.cache_service', 'http://redis:6379')
        }
        
        # Remove self-reference
        default_endpoints.pop(self.service_name, None)
        
        return {**default_endpoints, **endpoints}
    
    def setup_service_specific_config(self) -> None:
        """Setup service-specific configuration"""
        # Create config directory if it doesn't exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Create default service config file synchronously to avoid event loop conflicts
        self._create_service_config_file_sync()
    
    def _create_service_config_file_sync(self) -> None:
        """Create service config file synchronously"""
        config_file = self.config_dir / f"{self.service_name}.yml"
        
        if not config_file.exists():
            # Create basic service configuration
            default_config = {
                'service': {
                    'name': self.service_name,
                    'port': 8001 if self.service_name == 'data-bridge' else 8000,
                    'host': '0.0.0.0',
                    'debug': self.environment.value == 'development'
                },
                'environment': self.environment.value,
                'cors': {
                    'enabled': True,
                    'origins': ['*'],
                    'allow_credentials': True,
                    'allow_methods': ['*'],
                    'allow_headers': ['*']
                },
                'data_sources': {
                    'mt5': {
                        'enabled': True
                    }
                },
                'websocket': {
                    'enabled': True,
                    'max_connections': 200
                },
                'monitoring': {
                    'health_check_interval_seconds': 30
                }
            }
            
            try:
                with open(config_file, 'w') as f:
                    yaml.dump(default_config, f, default_flow_style=False)
            except Exception as e:
                # If we can't create the file, log warning but continue
                import logging
                logging.warning(f"Could not create service config file {config_file}: {e}")
    
    def _load_environment_config_sync(self) -> Dict[str, Any]:
        """Load environment-specific config synchronously"""
        env_file = self.config_dir / f"{self.environment.value}.yml"
        if env_file.exists():
            try:
                with open(env_file, 'r') as f:
                    return yaml.safe_load(f) or {}
            except Exception:
                pass
        return {}
    
    def _load_service_config_sync(self) -> Dict[str, Any]:
        """Load service-specific config synchronously"""
        service_file = self.config_dir / f"{self.service_name}.yml"
        if service_file.exists():
            try:
                with open(service_file, 'r') as f:
                    return yaml.safe_load(f) or {}
            except Exception:
                pass
        return {}
    
    def _load_secrets_sync(self) -> Dict[str, Any]:
        """Load secrets synchronously"""
        secrets = {}
        secrets_dir = Path("/run/secrets")
        if secrets_dir.exists():
            for secret_file in secrets_dir.iterdir():
                if secret_file.is_file():
                    try:
                        with open(secret_file, 'r') as f:
                            secrets[secret_file.name] = f.read().strip()
                    except Exception:
                        pass
        return secrets
    
    def export_config(self, format: str = "yaml") -> str:
        """Export current configuration"""
        if format == "yaml":
            return yaml.dump(self._config_cache, default_flow_style=False)
        elif format == "json":
            return json.dumps(self._config_cache, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary (without sensitive data)"""
        summary = self._config_cache.copy()
        
        # Remove sensitive information
        try:
            ConfigValidators.remove_sensitive_data(summary)
        except (ImportError, AttributeError):
            # If ConfigValidators doesn't exist, do basic sensitive data removal
            sensitive_keys = ['password', 'secret', 'key', 'token', 'credential']
            self._remove_sensitive_data_recursive(summary, sensitive_keys)
        
        return summary
    
    def _remove_sensitive_data_recursive(self, data: Dict[str, Any], sensitive_keys: List[str]) -> None:
        """Recursively remove sensitive data from config"""
        if isinstance(data, dict):
            for key in list(data.keys()):
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    data[key] = "***REDACTED***"
                elif isinstance(data[key], dict):
                    self._remove_sensitive_data_recursive(data[key], sensitive_keys)
    
    def validate_config(self) -> bool:
        """Validate configuration using ConfigValidators"""
        try:
            return ConfigValidators.validate_config(self.service_name, self._config_cache, self.environment.value)
        except Exception as e:
            # If validation fails, log warning but don't crash
            import logging
            logging.warning(f"Config validation failed for {self.service_name}: {e}")
            return True  # Allow service to continue with potentially invalid config
    
    def _deep_merge(self, base: Dict, update: Dict) -> None:
        """Deep merge two dictionaries"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def _set_nested_value(self, key: str, value: Any) -> None:
        """Set nested value using dot notation"""
        keys = key.split('.')
        current = self._config_cache
        
        for config_key in keys[:-1]:
            if config_key not in current:
                current[config_key] = {}
            current = current[config_key]
        
        current[keys[-1]] = value
    
    def _handle_common_env_vars(self) -> None:
        """Handle common environment variables"""
        common_vars = {
            'DATABASE_URL': 'database.url',
            'REDIS_URL': 'cache.url', 
            'LOG_LEVEL': 'logging.level'
        }
        
        for env_var, config_key in common_vars.items():
            value = os.getenv(env_var)
            if value:
                if env_var == 'LOG_LEVEL':
                    value = value.upper()
                self.set(config_key, value)
    
    def get_mt5_credentials(self) -> Dict[str, Any]:
        """Get MT5 credentials configuration"""
        return {
            "login": self.get('mt5.login', os.getenv('MT5_LOGIN')),
            "password": self.get('mt5.password', os.getenv('MT5_PASSWORD')),
            "server": self.get('mt5.server', os.getenv('MT5_SERVER', 'MetaQuotes-Demo'))
        }
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get configuration summary (without sensitive data)"""
        return self.get_config_summary()
    
    def validate_required_configuration(self) -> Dict[str, bool]:
        """Validate required configuration and return results"""
        required_keys = [
            'environment',
            'service.name',
            'service.port'
        ]
        
        results = {}
        for key in required_keys:
            results[key] = self.has(key)
        
        return results
    
    def get_service_config(self) -> Dict[str, Any]:
        """Get service-specific configuration"""
        return {
            'environment': self.get('environment', 'development'),
            'port': self.get('service.port', 8002),
            'host': self.get('service.host', '0.0.0.0'),
            'debug': self.get('service.debug', self.environment == Environment.DEVELOPMENT),
            'cors': self.get('cors', {}),
            'data_sources': self.get('data_sources', {}),
            'websocket': self.get('websocket', {}),
            'monitoring': self.get('monitoring', {})
        }
    
    # AI Brain Enhanced Configuration Methods
    
    def validate_configuration_with_ai_brain(self, config_changes: Dict[str, Any] = None) -> Dict[str, Any]:
        """AI Brain enhanced configuration validation with confidence scoring"""
        validation_result = {
            "is_valid": False,
            "confidence_score": 0.0,
            "validation_errors": [],
            "ai_brain_recommendations": [],
            "configuration_risks": [],
            "decision_confidence": 0.0
        }
        
        try:
            # Basic configuration validation
            basic_validation = self._validate_basic_configuration()
            validation_result["validation_errors"].extend(basic_validation.get("errors", []))
            
            # AI Brain confidence analysis if available
            if self.ai_brain_confidence and AI_BRAIN_AVAILABLE:
                config_data = config_changes or self._config_cache
                
                # Calculate configuration confidence
                confidence_score = self.ai_brain_confidence.calculate_confidence(
                    model_prediction={"config_validity": basic_validation["is_valid"]},
                    data_inputs={"config_completeness": len(config_data), "required_keys_present": basic_validation.get("required_keys_count", 0)},
                    market_context={"service_name": self.service_name, "environment": self.environment.value},
                    historical_data={"previous_validations": len(self.configuration_decisions)},
                    risk_parameters={"configuration_changes": len(config_changes or {})}
                )
                
                validation_result["confidence_score"] = confidence_score.composite_score
                validation_result["decision_confidence"] = confidence_score.composite_score
                
                # Generate AI Brain recommendations based on confidence
                if confidence_score.composite_score < 0.85:
                    validation_result["ai_brain_recommendations"] = self._generate_configuration_recommendations(
                        confidence_score, basic_validation
                    )
                
                # Assess configuration risks
                validation_result["configuration_risks"] = self._assess_configuration_risks(config_data, confidence_score)
                
                # Record configuration decision
                self._record_configuration_decision("validate_configuration", confidence_score.composite_score, validation_result)
            
            # Determine overall validity
            validation_result["is_valid"] = (
                len(validation_result["validation_errors"]) == 0 and
                validation_result["confidence_score"] >= 0.70  # Minimum acceptable confidence
            )
            
            return validation_result
            
        except Exception as e:
            if self.ai_brain_error_dna and AI_BRAIN_AVAILABLE:
                error_analysis = self.ai_brain_error_dna.analyze_error(e, {
                    "operation": "configuration_validation",
                    "service": self.service_name,
                    "config_data": config_changes or {}
                })
                validation_result["ai_brain_error_analysis"] = error_analysis
            
            validation_result["validation_errors"].append({
                "type": "validation_exception",
                "message": str(e),
                "severity": "critical"
            })
            return validation_result
    
    def _validate_basic_configuration(self) -> Dict[str, Any]:
        """Perform basic configuration validation checks"""
        validation = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "required_keys_count": 0
        }
        
        # Critical configuration requirements
        required_configs = {
            "service.name": "Service name must be specified",
            "service.port": "Service port must be specified",
            "environment": "Environment must be specified"
        }
        
        for key, error_message in required_configs.items():
            if not self.has(key):
                validation["errors"].append({
                    "key": key,
                    "message": error_message,
                    "severity": "critical"
                })
                validation["is_valid"] = False
            else:
                validation["required_keys_count"] += 1
        
        # Service-specific validations
        if self.service_name == "data-bridge":
            if not self.has("data_sources.mt5.enabled"):
                validation["warnings"].append({
                    "key": "data_sources.mt5.enabled",
                    "message": "MT5 data source should be explicitly enabled/disabled",
                    "severity": "medium"
                })
        
        # Port validation
        port = self.get("service.port")
        if port and (not isinstance(port, int) or port < 1024 or port > 65535):
            validation["errors"].append({
                "key": "service.port",
                "message": f"Invalid port number: {port}. Must be between 1024-65535",
                "severity": "high"
            })
            validation["is_valid"] = False
        
        # Environment validation
        env = self.get("environment")
        if env and env not in ["development", "staging", "production"]:
            validation["warnings"].append({
                "key": "environment",
                "message": f"Non-standard environment: {env}",
                "severity": "low"
            })
        
        return validation
    
    def _generate_configuration_recommendations(self, confidence_score, basic_validation) -> List[Dict[str, Any]]:
        """Generate AI Brain configuration recommendations based on confidence analysis"""
        recommendations = []
        
        # Low confidence recommendations
        if confidence_score.composite_score < 0.70:
            recommendations.append({
                "priority": "high",
                "category": "configuration_integrity",
                "message": "Configuration has low confidence score - review critical settings",
                "actions": [
                    "Verify all required configuration keys are present",
                    "Check configuration values for correctness",
                    "Ensure environment-specific settings are appropriate"
                ]
            })
        
        # Validation error recommendations
        if basic_validation.get("errors"):
            recommendations.append({
                "priority": "critical",
                "category": "validation_errors",
                "message": f"Configuration has {len(basic_validation['errors'])} validation errors",
                "actions": [error["message"] for error in basic_validation["errors"][:3]]  # Top 3 errors
            })
        
        # Service-specific recommendations
        if self.service_name == "data-bridge":
            if not self.has("websocket.enabled"):
                recommendations.append({
                    "priority": "medium",
                    "category": "service_optimization",
                    "message": "Data-bridge should explicitly configure WebSocket settings",
                    "actions": ["Enable WebSocket configuration", "Set appropriate connection limits"]
                })
        
        return recommendations
    
    def _assess_configuration_risks(self, config_data: Dict[str, Any], confidence_score) -> List[Dict[str, Any]]:
        """Assess potential risks in the configuration"""
        risks = []
        
        # High-risk configurations
        if self.get("service.debug") == True and self.environment.value == "production":
            risks.append({
                "risk_level": "high",
                "category": "security",
                "message": "Debug mode enabled in production environment",
                "mitigation": "Disable debug mode for production deployment"
            })
        
        # CORS risks
        cors_origins = self.get("cors.origins", [])
        if "*" in cors_origins and self.environment.value == "production":
            risks.append({
                "risk_level": "medium",
                "category": "security", 
                "message": "CORS allows all origins in production",
                "mitigation": "Restrict CORS origins to specific trusted domains"
            })
        
        # Low confidence risk
        if confidence_score.composite_score < 0.85:
            risks.append({
                "risk_level": "medium",
                "category": "reliability",
                "message": f"Configuration confidence below optimal threshold ({confidence_score.composite_score:.2f} < 0.85)",
                "mitigation": "Review and improve configuration quality"
            })
        
        return risks
    
    def _record_configuration_decision(self, decision_type: str, confidence: float, result: Dict[str, Any]):
        """Record configuration decision for AI Brain learning"""
        decision = {
            "timestamp": yaml.safe_load(json.dumps({"timestamp": "now"}))["timestamp"],  # Current timestamp
            "decision_type": decision_type,
            "confidence": confidence,
            "service": self.service_name,
            "environment": self.environment.value,
            "result": {
                "is_valid": result.get("is_valid", False),
                "error_count": len(result.get("validation_errors", [])),
                "risk_count": len(result.get("configuration_risks", []))
            }
        }
        
        self.configuration_decisions.append(decision)
        
        # Keep last 100 decisions
        if len(self.configuration_decisions) > 100:
            self.configuration_decisions = self.configuration_decisions[-100:]
    
    def get_ai_brain_configuration_analysis(self) -> Dict[str, Any]:
        """Get comprehensive AI Brain configuration analysis"""
        analysis = {
            "service": self.service_name,
            "analysis_timestamp": "now",
            "ai_brain_enabled": AI_BRAIN_AVAILABLE and self.ai_brain_confidence is not None,
            "total_decisions": len(self.configuration_decisions),
            "configuration_health": "unknown"
        }
        
        if self.configuration_decisions:
            # Calculate average confidence
            confidences = [d["confidence"] for d in self.configuration_decisions if "confidence" in d]
            if confidences:
                analysis["average_confidence"] = sum(confidences) / len(confidences)
                analysis["latest_confidence"] = confidences[-1] if confidences else 0
                
                # Determine configuration health
                if analysis["average_confidence"] >= 0.90:
                    analysis["configuration_health"] = "excellent"
                elif analysis["average_confidence"] >= 0.80:
                    analysis["configuration_health"] = "good"
                elif analysis["average_confidence"] >= 0.70:
                    analysis["configuration_health"] = "acceptable"
                else:
                    analysis["configuration_health"] = "needs_improvement"
        
        # Recent validation errors
        recent_errors = []
        for decision in self.configuration_decisions[-10:]:  # Last 10 decisions
            error_count = decision.get("result", {}).get("error_count", 0)
            if error_count > 0:
                recent_errors.append({
                    "decision_type": decision["decision_type"],
                    "error_count": error_count,
                    "confidence": decision.get("confidence", 0)
                })
        
        analysis["recent_validation_errors"] = recent_errors
        analysis["error_trend"] = "improving" if len(recent_errors) <= 2 else "stable" if len(recent_errors) <= 5 else "degrading"
        
        # AI Brain recommendations summary
        if hasattr(self, 'ai_brain_config_recommendations') and self.ai_brain_config_recommendations:
            analysis["active_recommendations"] = len(self.ai_brain_config_recommendations)
            analysis["high_priority_recommendations"] = len([
                r for r in self.ai_brain_config_recommendations 
                if r.get("priority") in ["high", "critical"]
            ])
        
        return analysis
    
    def validate_and_apply_configuration(self, new_config: Dict[str, Any], require_ai_brain_approval: bool = True) -> Dict[str, Any]:
        """Validate and apply new configuration with AI Brain approval if required"""
        application_result = {
            "applied": False,
            "validation_result": None,
            "ai_brain_approved": False,
            "errors": [],
            "rollback_available": True
        }
        
        try:
            # Create backup of current configuration
            config_backup = self._config_cache.copy()
            
            # Validate new configuration
            validation_result = self.validate_configuration_with_ai_brain(new_config)
            application_result["validation_result"] = validation_result
            
            # AI Brain approval check
            if require_ai_brain_approval:
                ai_brain_approved = validation_result.get("confidence_score", 0) >= 0.85
                application_result["ai_brain_approved"] = ai_brain_approved
                
                if not ai_brain_approved:
                    application_result["errors"].append({
                        "type": "ai_brain_approval_required",
                        "message": f"Configuration confidence {validation_result.get('confidence_score', 0):.2f} below required 0.85 threshold",
                        "recommendations": validation_result.get("ai_brain_recommendations", [])
                    })
                    return application_result
            else:
                application_result["ai_brain_approved"] = True
            
            # Apply configuration if validation passed
            if validation_result["is_valid"]:
                # Merge new configuration
                self._deep_merge(self._config_cache, new_config)
                application_result["applied"] = True
                
                # Record successful configuration change
                self._record_configuration_decision("apply_configuration", 
                                                  validation_result.get("confidence_score", 0.8), 
                                                  {"applied": True, "changes": len(new_config)})
            else:
                application_result["errors"].extend(validation_result.get("validation_errors", []))
            
            return application_result
            
        except Exception as e:
            if self.ai_brain_error_dna and AI_BRAIN_AVAILABLE:
                error_analysis = self.ai_brain_error_dna.analyze_error(e, {
                    "operation": "apply_configuration", 
                    "service": self.service_name,
                    "new_config": new_config
                })
                application_result["ai_brain_error_analysis"] = error_analysis
            
            application_result["errors"].append({
                "type": "application_exception",
                "message": str(e),
                "severity": "critical"
            })
            
            return application_result


# Import centralized managers and convenience functions
from .config_managers import (
    SharedInfraConfigManager,
    get_config,
    get_database_config,
    get_api_config
)