"""
Central Hub Configuration Coordinator
====================================

This module provides configuration COORDINATION for Central Hub itself.
Service configs have been moved to shared/config/ where services can access them directly.

Central Hub Role:
- Manages its own configuration (central_hub_config.json)
- Distributes service configs to requesting services
- Validates configurations
- Handles hot reload notifications

Usage:
    # For Central Hub's own config
    from .validation import validate_central_hub_config

    # For service coordination
    from central_hub.core.config_manager import ConfigManager
"""

import os
import json
from typing import Dict, Any, Tuple, List, Optional
from pathlib import Path

# Central Hub's own configuration path
CONFIG_FILE = Path(__file__).parent / "central_hub_config.json"

def load_central_hub_config() -> Dict[str, Any]:
    """
    Load Central Hub's own configuration

    Returns:
        Central Hub configuration dictionary
    """
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Central Hub config file not found: {CONFIG_FILE}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in Central Hub config: {e}")

def validate_central_hub_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate Central Hub's own configuration

    Args:
        config: Configuration dictionary to validate

    Returns:
        Tuple of (is_valid: bool, errors: List[str])
    """
    errors = []

    # Required sections
    required_sections = ['service', 'transport_methods', 'service_registry']
    for section in required_sections:
        if section not in config:
            errors.append(f"Missing required section: {section}")

    # Service info validation
    if 'service' in config:
        service_info = config['service']
        if 'name' not in service_info or service_info['name'] != 'central-hub':
            errors.append("Service name must be 'central-hub'")
        if 'port' not in service_info:
            errors.append("Service port is required")

    return len(errors) == 0, errors

def get_service_configs_location() -> str:
    """
    Get the location where service configurations can be found

    Returns:
        Path to shared service configurations
    """
    return "../shared/config/services/"

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
    'load_central_hub_config',
    'validate_central_hub_config',
    'get_service_configs_location',
    'register_config_update',
    'get_hot_reload_status',
    'clear_hot_reload_status'
]