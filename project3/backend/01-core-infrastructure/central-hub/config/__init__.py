"""
Centralized Configuration System - Suho AI Trading Platform
==========================================================

This module provides centralized configuration management for all services
in the Suho AI Trading Platform. Configurations are split into:

- STATIC: Infrastructure configs (environment variables)
- HOT RELOAD: Business logic configs (Central Hub)

Usage:
    from central_hub.config import get_service_config, validate_config

    # Get service configuration
    config = get_service_config('api-gateway')

    # Validate configuration
    is_valid, errors = validate_config('api-gateway', config)
"""

import os
import importlib
from typing import Dict, Any, Tuple, List, Optional

# Available service configurations
AVAILABLE_CONFIGS = {
    'api-gateway': 'config_api_gateway',
    'component-manager': 'config_component_manager',
    'trading-engine': 'config_trading_engine',
    'market-analyzer': 'config_market_analyzer',
}

def get_service_config(service_name: str) -> Optional[Dict[str, Any]]:
    """
    Get configuration for a specific service

    Args:
        service_name: Name of the service (e.g., 'api-gateway')

    Returns:
        Configuration dictionary or None if not found
    """
    if service_name not in AVAILABLE_CONFIGS:
        raise ValueError(f"Unknown service: {service_name}. Available: {list(AVAILABLE_CONFIGS.keys())}")

    config_module_name = AVAILABLE_CONFIGS[service_name]

    try:
        # Dynamic import of service config
        config_module = importlib.import_module(f".{config_module_name}", package=__name__)

        # Get config constant (naming convention: CONFIG_{SERVICE_NAME_UPPER})
        config_const_name = f"CONFIG_{service_name.upper().replace('-', '_')}"

        if hasattr(config_module, config_const_name):
            return getattr(config_module, config_const_name)
        else:
            raise AttributeError(f"Config constant {config_const_name} not found in {config_module_name}")

    except ImportError as e:
        raise ImportError(f"Failed to import config module {config_module_name}: {e}")

def validate_config(service_name: str, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate configuration for a specific service

    Args:
        service_name: Name of the service
        config: Configuration dictionary to validate

    Returns:
        Tuple of (is_valid: bool, errors: List[str])
    """
    if service_name not in AVAILABLE_CONFIGS:
        return False, [f"Unknown service: {service_name}"]

    config_module_name = AVAILABLE_CONFIGS[service_name]

    try:
        # Dynamic import of service config
        config_module = importlib.import_module(f".{config_module_name}", package=__name__)

        # Get validation function (naming convention: validate_{service_name}_config)
        validate_func_name = f"validate_{service_name.replace('-', '_')}_config"

        if hasattr(config_module, validate_func_name):
            validate_func = getattr(config_module, validate_func_name)
            return validate_func(config)
        else:
            # Fallback to generic validation
            from .templates.service_config_template import validate_config as generic_validate
            return generic_validate(config)

    except ImportError as e:
        return False, [f"Failed to import validation for {service_name}: {e}"]

def list_available_services() -> List[str]:
    """
    Get list of all available service configurations

    Returns:
        List of service names
    """
    return list(AVAILABLE_CONFIGS.keys())

def get_config_version(service_name: str) -> Optional[str]:
    """
    Get configuration version for a service

    Args:
        service_name: Name of the service

    Returns:
        Configuration version or None if not found
    """
    config = get_service_config(service_name)
    if config and 'config_meta' in config:
        return config['config_meta'].get('version')
    return None

def get_config_metadata(service_name: str) -> Optional[Dict[str, Any]]:
    """
    Get configuration metadata for a service

    Args:
        service_name: Name of the service

    Returns:
        Configuration metadata or None if not found
    """
    config = get_service_config(service_name)
    if config and 'config_meta' in config:
        return config['config_meta']
    return None

# Hot reload registry - tracks which configs have been updated
_hot_reload_registry = {}

def register_config_update(service_name: str, timestamp: str, version: str):
    """
    Register a configuration update for hot reload tracking

    Args:
        service_name: Name of the service
        timestamp: Update timestamp
        version: New configuration version
    """
    _hot_reload_registry[service_name] = {
        'timestamp': timestamp,
        'version': version,
        'status': 'updated'
    }

def get_hot_reload_status(service_name: str) -> Optional[Dict[str, Any]]:
    """
    Get hot reload status for a service

    Args:
        service_name: Name of the service

    Returns:
        Hot reload status or None if not tracked
    """
    return _hot_reload_registry.get(service_name)

def clear_hot_reload_status(service_name: str):
    """
    Clear hot reload status for a service

    Args:
        service_name: Name of the service
    """
    if service_name in _hot_reload_registry:
        del _hot_reload_registry[service_name]

# Export main functions
__all__ = [
    'get_service_config',
    'validate_config',
    'list_available_services',
    'get_config_version',
    'get_config_metadata',
    'register_config_update',
    'get_hot_reload_status',
    'clear_hot_reload_status',
    'AVAILABLE_CONFIGS'
]