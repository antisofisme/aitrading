"""
config_manager.py - Configuration Management System

🎯 PURPOSE:
Business: Centralized configuration for all trading client settings and parameters
Technical: Environment-aware configuration with validation and hot-reloading
Domain: Configuration/Environment Management/Settings

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:27.800Z
Session: client-side-ai-brain-full-compliance
Confidence: 93%
Complexity: medium

🧩 PATTERNS USED:
- AI_BRAIN_CONFIG_MANAGEMENT: Centralized configuration with environment awareness
- HOT_RELOAD_CONFIG: Dynamic configuration reloading without restart

📦 DEPENDENCIES:
Internal: logger_manager, error_manager
External: os, json, yaml, configparser, pathlib

💡 AI DECISION REASONING:
Centralized configuration management enables consistent settings across all components with environment-specific overrides for development and production.

🚀 USAGE:
config = ConfigManager.get_instance(); mt5_login = config.get("mt5.login")

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

import json
import yaml
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import threading
import os
from copy import deepcopy

@dataclass 
class ConfigSection:
    """Configuration section metadata"""
    name: str
    file_path: str
    format: str  # json, yaml, env
    last_modified: Optional[datetime] = None
    cached: bool = True
    environment_specific: bool = False
    validation_schema: Optional[Dict[str, Any]] = None

class ClientConfigManager:
    """
    Client-Side Centralized Configuration Manager
    Manages all configurations for MT5 Trading Client with validation and caching
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        self.config_cache: Dict[str, Any] = {}
        self.config_sections: Dict[str, ConfigSection] = {}
        self.file_watchers: Dict[str, datetime] = {}
        self.environment = os.getenv('CLIENT_ENV', 'development')
        self._setup_default_sections()
    
    @classmethod
    def get_instance(cls) -> 'ClientConfigManager':
        """Singleton pattern with thread safety"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def _setup_default_sections(self):
        """Setup default configuration sections"""
        self.config_sections.update({
            # Client settings
            'client': ConfigSection(
                name='client',
                file_path='src/shared/config/client_config.json',
                format='json',
                cached=True,
                environment_specific=True
            ),
            
            # MT5 connection settings  
            'mt5': ConfigSection(
                name='mt5',
                file_path='src/shared/config/mt5_config.json',
                format='json',
                cached=True,
                validation_schema={
                    'login': {'type': 'integer', 'required': True},
                    'server': {'type': 'string', 'required': True},
                    'path': {'type': 'string', 'required': False}
                }
            ),
            
            # WebSocket settings
            'websocket': ConfigSection(
                name='websocket',
                file_path='src/shared/config/websocket_config.json',
                format='json',
                cached=True,
                validation_schema={
                    'url': {'type': 'string', 'required': True},
                    'timeout': {'type': 'integer', 'required': False},
                    'reconnect_attempts': {'type': 'integer', 'required': False}
                }
            ),
            
            # Redpanda/Kafka settings
            'redpanda': ConfigSection(
                name='redpanda',
                file_path='src/shared/config/redpanda_config.json', 
                format='json',
                cached=True,
                validation_schema={
                    'bootstrap_servers': {'type': 'list', 'required': True},
                    'topics': {'type': 'dict', 'required': True}
                }
            ),
            
            # Logging settings
            'logging': ConfigSection(
                name='logging',
                file_path='src/shared/config/logging_config.yaml',
                format='yaml',
                cached=True
            ),
            
            # Trading settings
            'trading': ConfigSection(
                name='trading',
                file_path='src/shared/config/trading_config.json',
                format='json',
                cached=True,
                validation_schema={
                    'symbols': {'type': 'list', 'required': True},
                    'timeframes': {'type': 'list', 'required': True},
                    'risk_management': {'type': 'dict', 'required': True}
                }
            )
        })
    
    def get_config(self, section: str, use_cache: bool = True, 
                  validate: bool = True) -> Dict[str, Any]:
        """
        Get configuration section with caching and validation
        
        Args:
            section: Configuration section name
            use_cache: Whether to use cached version
            validate: Whether to validate against schema
            
        Returns:
            Configuration dictionary
        """
        # Check cache first
        if use_cache and section in self.config_cache:
            if not self._is_file_modified(section):
                return deepcopy(self.config_cache[section])
        
        # Load configuration
        config_data = self._load_config_section(section)
        
        # Apply environment-specific overrides
        if section in self.config_sections:
            section_info = self.config_sections[section]
            if section_info.environment_specific:
                config_data = self._apply_environment_overrides(section, config_data)
        
        # Validate if requested
        if validate and section in self.config_sections:
            section_info = self.config_sections[section]
            if section_info.validation_schema:
                self._validate_config(config_data, section_info.validation_schema)
        
        # Cache the result
        self.config_cache[section] = deepcopy(config_data)
        
        return config_data
    
    def set_config(self, section: str, config_data: Dict[str, Any], 
                  save_to_file: bool = True):
        """
        Set configuration section
        
        Args:
            section: Configuration section name
            config_data: Configuration data
            save_to_file: Whether to save to file
        """
        # Update cache
        self.config_cache[section] = deepcopy(config_data)
        
        # Save to file if requested
        if save_to_file:
            self._save_config_section(section, config_data)
    
    def get_client_settings(self) -> Dict[str, Any]:
        """Get client settings (backward compatibility)"""
        return self.get_config('client')
    
    def get_mt5_config(self) -> Dict[str, Any]:
        """Get MT5 configuration"""
        return self.get_config('mt5')
    
    def get_websocket_config(self) -> Dict[str, Any]:
        """Get WebSocket configuration"""  
        return self.get_config('websocket')
    
    def get_redpanda_config(self) -> Dict[str, Any]:
        """Get Redpanda configuration"""
        return self.get_config('redpanda')
    
    def update_config_value(self, section: str, key_path: str, value: Any):
        """
        Update specific configuration value using dot notation
        
        Args:
            section: Configuration section
            key_path: Dot-separated key path (e.g., 'mt5.login')
            value: New value
        """
        config = self.get_config(section)
        
        # Navigate to the key using dot notation
        keys = key_path.split('.')
        current = config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the value
        current[keys[-1]] = value
        
        # Save updated config
        self.set_config(section, config)
    
    def reload_config(self, section: Optional[str] = None):
        """Reload configuration from files"""
        if section:
            if section in self.config_cache:
                del self.config_cache[section]
            self.get_config(section, use_cache=False)
        else:
            self.config_cache.clear()
            for section_name in self.config_sections.keys():
                self.get_config(section_name, use_cache=False)
    
    def get_config_status(self) -> Dict[str, Any]:
        """Get configuration system status"""
        return {
            'environment': self.environment,
            'cached_sections': list(self.config_cache.keys()),
            'total_sections': len(self.config_sections),
            'file_watchers': len(self.file_watchers),
            'sections_info': {name: asdict(info) for name, info in self.config_sections.items()}
        }
    
    def validate_all_configs(self) -> Dict[str, Any]:
        """Validate all configurations"""
        results = {}
        
        for section_name, section_info in self.config_sections.items():
            try:
                config = self.get_config(section_name, validate=True)
                results[section_name] = {'valid': True, 'error': None}
            except Exception as e:
                results[section_name] = {'valid': False, 'error': str(e)}
        
        return results
    
    def export_config(self, section: str, filepath: str, format: str = 'json'):
        """Export configuration to file"""
        config = self.get_config(section)
        
        try:
            if format.lower() == 'json':
                with open(filepath, 'w') as f:
                    json.dump(config, f, indent=2, default=str)
            elif format.lower() == 'yaml':
                with open(filepath, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False)
            else:
                raise ValueError(f"Unsupported format: {format}")
        except Exception as e:
            raise Exception(f"Failed to export config: {e}")
    
    def _load_config_section(self, section: str) -> Dict[str, Any]:
        """Load configuration section from file"""
        if section not in self.config_sections:
            raise ValueError(f"Unknown configuration section: {section}")
        
        section_info = self.config_sections[section]
        file_path = Path(section_info.file_path)
        
        if not file_path.exists():
            # Return default configuration
            return self._get_default_config(section)
        
        try:
            if section_info.format == 'json':
                with open(file_path, 'r') as f:
                    return json.load(f)
            elif section_info.format == 'yaml':
                with open(file_path, 'r') as f:
                    return yaml.safe_load(f) or {}
            else:
                raise ValueError(f"Unsupported format: {section_info.format}")
                
        except Exception as e:
            print(f"Failed to load config {section}: {e}")
            return self._get_default_config(section)
    
    def _save_config_section(self, section: str, config_data: Dict[str, Any]):
        """Save configuration section to file"""
        if section not in self.config_sections:
            raise ValueError(f"Unknown configuration section: {section}")
        
        section_info = self.config_sections[section]
        file_path = Path(section_info.file_path)
        
        # Create directory if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            if section_info.format == 'json':
                with open(file_path, 'w') as f:
                    json.dump(config_data, f, indent=2, default=str)
            elif section_info.format == 'yaml':
                with open(file_path, 'w') as f:
                    yaml.dump(config_data, f, default_flow_style=False)
            
            # Update file modification time
            self.file_watchers[section] = datetime.fromtimestamp(file_path.stat().st_mtime)
            
        except Exception as e:
            raise Exception(f"Failed to save config {section}: {e}")
    
    def _is_file_modified(self, section: str) -> bool:
        """Check if configuration file was modified"""
        if section not in self.config_sections:
            return False
        
        section_info = self.config_sections[section]
        file_path = Path(section_info.file_path)
        
        if not file_path.exists():
            return False
        
        current_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
        cached_mtime = self.file_watchers.get(section)
        
        if cached_mtime is None or current_mtime > cached_mtime:
            self.file_watchers[section] = current_mtime
            return True
        
        return False
    
    def _apply_environment_overrides(self, section: str, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment-specific configuration overrides"""
        env_file = f"src/shared/config/{section}_{self.environment}.json"
        env_path = Path(env_file)
        
        if env_path.exists():
            try:
                with open(env_path, 'r') as f:
                    env_overrides = json.load(f)
                
                # Deep merge environment overrides
                config_data = self._deep_merge(config_data, env_overrides)
            except Exception as e:
                print(f"Failed to load environment overrides for {section}: {e}")
        
        return config_data
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        result = deepcopy(base)
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _validate_config(self, config_data: Dict[str, Any], schema: Dict[str, Any]):
        """Validate configuration against schema"""
        # Simple validation - can be extended with more sophisticated validation
        for field, rules in schema.items():
            if rules.get('required', False) and field not in config_data:
                raise ValueError(f"Required field '{field}' missing from configuration")
            
            if field in config_data:
                value = config_data[field]
                expected_type = rules.get('type')
                
                if expected_type == 'string' and not isinstance(value, str):
                    raise ValueError(f"Field '{field}' must be string")
                elif expected_type == 'integer' and not isinstance(value, int):
                    raise ValueError(f"Field '{field}' must be integer")
                elif expected_type == 'list' and not isinstance(value, list):
                    raise ValueError(f"Field '{field}' must be list")
                elif expected_type == 'dict' and not isinstance(value, dict):
                    raise ValueError(f"Field '{field}' must be dictionary")
    
    def _get_default_config(self, section: str) -> Dict[str, Any]:
        """Get default configuration for section"""
        defaults = {
            'client': {
                'app_name': 'MT5 Trading Client',
                'version': '1.0.0',
                'debug': False
            },
            'mt5': {
                'login': 0,
                'server': '',
                'path': ''
            },
            'websocket': {
                'url': os.getenv('WEBSOCKET_URL', 'ws://localhost:8000/api/v1/ws/mt5'),
                'timeout': int(os.getenv('WEBSOCKET_TIMEOUT', '30')),
                'reconnect_attempts': int(os.getenv('WEBSOCKET_RECONNECT_ATTEMPTS', '5'))
            },
            'redpanda': {
                'bootstrap_servers': os.getenv('REDPANDA_BOOTSTRAP_SERVERS', 'localhost:9092').split(','),
                'topics': {
                    'tick_data': os.getenv('REDPANDA_TICK_TOPIC', 'mt5_tick_data'),
                    'account_info': os.getenv('REDPANDA_ACCOUNT_TOPIC', 'mt5_account_info')
                }
            },
            'trading': {
                'symbols': ['EURUSD', 'GBPUSD'],
                'timeframes': ['M1', 'M5', 'H1'],
                'risk_management': {
                    'max_risk_percent': 2.0,
                    'max_trades': 10
                }
            }
        }
        
        return defaults.get(section, {})


# Global instance
client_config_manager = ClientConfigManager.get_instance()

# Convenience functions
def get_config(section: str, use_cache: bool = True) -> Dict[str, Any]:
    """Get configuration section"""
    return client_config_manager.get_config(section, use_cache)

def get_client_settings() -> Dict[str, Any]:
    """Get client settings (backward compatibility)"""
    return client_config_manager.get_client_settings()

def get_mt5_config() -> Dict[str, Any]:
    """Get MT5 configuration"""
    return client_config_manager.get_mt5_config()

def get_websocket_config() -> Dict[str, Any]:
    """Get WebSocket configuration"""
    return client_config_manager.get_websocket_config()

def get_config_status() -> Dict[str, Any]:
    """Get configuration status"""
    return client_config_manager.get_config_status()