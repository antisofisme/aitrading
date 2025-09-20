"""
Configuration Managers - Centralized management and convenience functions
"""
import threading
from typing import Dict, Any, Optional
from .config_core import CoreConfig


# CENTRALIZED CONFIG MANAGER - Simple singleton for all microservices
class SharedInfraConfigManager:
    """Simple centralized config management for microservices"""
    
    _configs = {}
    _lock = threading.RLock()
    
    @classmethod
    def get_config(cls, service_name: str, environment: str = None) -> CoreConfig:
        """Get or create config for service"""
        with cls._lock:
            key = f"{service_name}-{environment or 'default'}"
            if key not in cls._configs:
                cls._configs[key] = CoreConfig(service_name, environment)
            return cls._configs[key]
    
    @classmethod
    def get_database_config(cls, service_name: str) -> Dict[str, Any]:
        """Get database config for service"""
        config = cls.get_config(service_name)
        return config.get_database_config()
    
    @classmethod
    def get_api_config(cls, service_name: str, key: str, default=None) -> Any:
        """Get API config value for service"""
        config = cls.get_config(service_name)
        return config.get(key, default)
    
    @classmethod
    def get_all_configs(cls) -> Dict[str, CoreConfig]:
        """Get all managed configs"""
        return cls._configs.copy()


# Simple convenience functions
def get_config(service_name: str, environment: str = None) -> CoreConfig:
    """Get config for service"""
    return SharedInfraConfigManager.get_config(service_name, environment)


def get_database_config(service_name: str) -> Dict[str, Any]:
    """Get database config"""
    return SharedInfraConfigManager.get_database_config(service_name)


def get_api_config(service_name: str, key: str, default=None) -> Any:
    """Get API config value"""
    return SharedInfraConfigManager.get_api_config(service_name, key, default)