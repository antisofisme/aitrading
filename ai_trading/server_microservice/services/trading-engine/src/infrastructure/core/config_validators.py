"""
Configuration Validators - Validation logic for configuration completeness and correctness
"""
import os
import logging
from typing import Dict, Any


class ConfigValidators:
    """Configuration validation utilities"""
    
    @staticmethod
    def validate_config(service_name: str, config: Dict[str, Any], environment: str) -> bool:
        """Validate configuration completeness and correctness"""
        try:
            # Required configuration checks
            required_keys = [
                'service.name',
                'service.port'
            ]
            
            for key in required_keys:
                if not ConfigValidators._has_nested_key(config, key):
                    # Use proper logging instead of print
                    logger = logging.getLogger(f"{service_name}-config")
                    logger.error(f"Missing required configuration: {key}", 
                               extra={"context": {"validation_error": key}})
                    return False
            
            # Validate port range
            port = ConfigValidators._get_nested_value(config, 'service.port')
            if not (1000 <= port <= 65535):
                logger = logging.getLogger(f"{service_name}-config")
                logger.error(f"Invalid port number: {port}")
                return False
            
            # Environment-specific validations
            if ConfigValidators._is_production(environment):
                # Production requires certain security settings
                if not ConfigValidators._get_nested_value(config, 'database.password'):
                    logger = logging.getLogger(f"{service_name}-config")
                    logger.error("Production environment requires database password")
                    return False
            
            return True
            
        except Exception as validation_error:
            logger = logging.getLogger(f"{service_name}-config")
            logger.error(f"Configuration validation error: {validation_error}")
            return False
    
    @staticmethod
    def remove_sensitive_data(data: Dict, sensitive_keys: list = None) -> None:
        """Remove sensitive data from configuration"""
        if sensitive_keys is None:
            sensitive_keys = ['password', 'secret', 'token', 'key']
            
        if isinstance(data, dict):
            for key, value in list(data.items()):
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    data[key] = "***HIDDEN***"
                elif isinstance(value, dict):
                    ConfigValidators.remove_sensitive_data(value, sensitive_keys)
    
    @staticmethod
    def _has_nested_key(config: Dict[str, Any], key: str) -> bool:
        """Check if nested key exists in configuration"""
        keys = key.split('.')
        value = config
        
        for config_key in keys:
            if isinstance(value, dict) and config_key in value:
                value = value[config_key]
            else:
                return False
        
        return True
    
    @staticmethod
    def _get_nested_value(config: Dict[str, Any], key: str) -> Any:
        """Get nested value from configuration"""
        keys = key.split('.')
        value = config
        
        for config_key in keys:
            if isinstance(value, dict) and config_key in value:
                value = value[config_key]
            else:
                return None
        
        return value
    
    @staticmethod
    def _is_production(environment: str) -> bool:
        """Check if environment is production"""
        return environment.lower() == 'production'