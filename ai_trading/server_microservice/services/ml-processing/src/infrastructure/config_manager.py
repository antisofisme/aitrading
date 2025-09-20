"""
Data Bridge Service Configuration Manager
Handles loading and parsing of configuration with environment variable expansion
"""
import os
import yaml
import re
from pathlib import Path
from typing import Dict, Any, Optional, Union


class DataBridgeConfigManager:
    """Configuration manager for Data Bridge service with environment variable expansion"""
    
    def __init__(self, config_path: str = None):
        """
        Initialize configuration manager
        
        Args:
            config_path: Path to configuration file, defaults to auto-detection
        """
        if config_path is None:
            # Auto-detect configuration path
            current_dir = Path(__file__).parent
            service_root = current_dir.parent.parent
            config_path = service_root / "config" / "data-bridge.yml"
        
        self.config_path = Path(config_path)
        self._config = None
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file with environment variable expansion"""
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            
            with open(self.config_path, 'r') as f:
                config_content = f.read()
            
            # Expand environment variables in the configuration
            expanded_content = self._expand_environment_variables(config_content)
            
            # Parse YAML
            self._config = yaml.safe_load(expanded_content) or {}
            
        except Exception as e:
            raise RuntimeError(f"Failed to load configuration from {self.config_path}: {e}")
    
    def _expand_environment_variables(self, content: str) -> str:
        """
        Expand environment variables in configuration content
        Supports format: ${VAR_NAME:default_value}
        """
        # Pattern to match ${VAR_NAME:default_value} or ${VAR_NAME}
        pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'
        
        def replacer(match):
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) is not None else ""
            return os.getenv(var_name, default_value)
        
        return re.sub(pattern, replacer, content)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key path (supports dot notation)
        
        Args:
            key: Configuration key path (e.g., 'data_sources.mt5.enabled')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_service_config(self) -> Dict[str, Any]:
        """Get main service configuration"""
        return self.get('service', {})
    
    def get_cors_config(self) -> Dict[str, Any]:
        """Get CORS configuration"""
        return self.get('cors', {})
    
    def get_rate_limiting_config(self) -> Dict[str, Any]:
        """Get rate limiting configuration"""
        return self.get('rate_limiting', {})
    
    def get_data_sources_config(self) -> Dict[str, Any]:
        """Get data sources configuration"""
        return self.get('data_sources', {})
    
    def get_mt5_bridge_config(self) -> Dict[str, Any]:
        """Get MT5 bridge configuration"""
        return self.get('mt5_bridge', {})
    
    def get_trading_config(self) -> Dict[str, Any]:
        """Get trading configuration"""
        return self.get('trading', {})
    
    def get_websocket_config(self) -> Dict[str, Any]:
        """Get WebSocket configuration"""
        return self.get('websocket', {})
    
    def get_real_time_data_config(self) -> Dict[str, Any]:
        """Get real-time data configuration"""
        return self.get('real_time_data', {})
    
    def get_caching_config(self) -> Dict[str, Any]:
        """Get caching configuration"""
        return self.get('caching', {})
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance configuration"""
        return self.get('performance', {})
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration"""
        return self.get('monitoring', {})
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return self.get('database', {})
    
    def get_cache_config(self) -> Dict[str, Any]:
        """Get cache configuration"""
        return self.get('cache', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return self.get('logging', {})
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration"""
        return self.get('security', {})
    
    def get_environment_config(self) -> Dict[str, Any]:
        """Get environment-specific configuration"""
        environment = self.get('service.environment', 'development')
        return self.get(f'environments.{environment}', {})
    
    def get_mt5_credentials(self) -> Dict[str, str]:
        """Get MT5 credentials safely"""
        return {
            'login': os.getenv('MT5_LOGIN', ''),
            'password': os.getenv('MT5_PASSWORD', ''),
            'server': os.getenv('MT5_SERVER', 'MetaQuotes-Demo')
        }
    
    def get_api_keys(self) -> Dict[str, str]:
        """Get API keys for data sources"""
        return {
            'dukascopy': os.getenv('DUKASCOPY_API_KEY', ''),
            'tradingview': os.getenv('TRADINGVIEW_API_KEY', ''),
            'mql5': os.getenv('MQL5_API_KEY', '')
        }
    
    def validate_required_configuration(self) -> Dict[str, bool]:
        """Validate that required configuration is provided"""
        validation_results = {}
        
        # Check database password
        db_password = self.get('database.password', '')
        validation_results['database_password'] = bool(db_password.strip())
        
        # Check cache password (optional)
        cache_password = self.get('cache.password', '')
        validation_results['cache_password'] = True  # Optional
        
        # Check MT5 credentials if MT5 is enabled
        if self.get('data_sources.mt5.enabled', True):
            mt5_creds = self.get_mt5_credentials()
            validation_results['mt5_login'] = bool(mt5_creds['login'].strip())
            validation_results['mt5_password'] = bool(mt5_creds['password'].strip())
        else:
            validation_results['mt5_login'] = True  # Not required if disabled
            validation_results['mt5_password'] = True  # Not required if disabled
        
        return validation_results
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get configuration summary without sensitive data"""
        summary = {
            'service': self.get_service_config(),
            'cors': self.get_cors_config(),
            'rate_limiting': self.get_rate_limiting_config(),
            'data_sources': {
                source: {'enabled': config.get('enabled', True)}
                for source, config in self.get_data_sources_config().items()
            },
            'websocket': {
                'enabled': self.get('websocket.enabled', True),
                'max_connections': self.get('websocket.max_connections', 1000)
            },
            'monitoring': self.get_monitoring_config(),
            'environment': self.get('service.environment', 'development')
        }
        
        # Remove sensitive data
        database_config = self.get_database_config().copy()
        if 'password' in database_config:
            database_config['password'] = '***masked***' if database_config['password'] else '***not_set***'
        summary['database'] = database_config
        
        cache_config = self.get_cache_config().copy()
        if 'password' in cache_config:
            cache_config['password'] = '***masked***' if cache_config['password'] else '***not_set***'
        summary['cache'] = cache_config
        
        return summary
    
    def reload_config(self) -> None:
        """Reload configuration from file"""
        self._load_config()
    
    def get_full_config(self) -> Dict[str, Any]:
        """Get full configuration (for debugging purposes only)"""
        return self._config.copy()


# Global configuration instance
_config_manager = None


def get_config_manager() -> DataBridgeConfigManager:
    """Get global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = DataBridgeConfigManager()
    return _config_manager


def get_service_config() -> Dict[str, Any]:
    """Get service configuration"""
    return get_config_manager().get_service_config()


def get_mt5_config() -> Dict[str, Any]:
    """Get MT5 bridge configuration"""
    return get_config_manager().get_mt5_bridge_config()


def get_websocket_config() -> Dict[str, Any]:
    """Get WebSocket configuration"""
    return get_config_manager().get_websocket_config()


def get_database_config() -> Dict[str, Any]:
    """Get database configuration"""
    return get_config_manager().get_database_config()


def get_mt5_credentials() -> Dict[str, str]:
    """Get MT5 credentials safely"""
    return get_config_manager().get_mt5_credentials()


def get_api_keys() -> Dict[str, str]:
    """Get API keys for data sources"""
    return get_config_manager().get_api_keys()