"""
Base Configuration Interface - Abstract class for service-specific configuration
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
from enum import Enum

class Environment(Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

class BaseConfig(ABC):
    """Abstract base class for all service configurations"""
    
    def __init__(self, service_name: str, environment: Union[Environment, str] = Environment.DEVELOPMENT):
        self.service_name = service_name
        self.environment = Environment(environment) if isinstance(environment, str) else environment
        self._config_cache = {}
        self._is_loaded = False
    
    @abstractmethod
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from various sources"""
        pass
    
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any):
        """Set configuration value"""
        pass
    
    @abstractmethod
    def has(self, key: str) -> bool:
        """Check if configuration key exists"""
        pass
    
    @abstractmethod
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration for this service"""
        pass
    
    @abstractmethod
    def get_cache_config(self) -> Dict[str, Any]:
        """Get cache configuration for this service"""
        pass
    
    @abstractmethod
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration for this service"""
        pass
    
    @abstractmethod
    def get_service_endpoints(self) -> Dict[str, str]:
        """Get other service endpoints this service depends on"""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate configuration completeness and correctness"""
        pass
    
    def reload_config(self):
        """Reload configuration from sources"""
        self._config_cache.clear()
        self._is_loaded = False
        self.load_config()
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == Environment.DEVELOPMENT
    
    def get_environment(self) -> Environment:
        """Get current environment"""
        return self.environment
    
    def get_service_name(self) -> str:
        """Get service name"""
        return self.service_name
    
    @abstractmethod
    def setup_service_specific_config(self):
        """Setup service-specific configuration"""
        pass