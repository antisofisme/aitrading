"""
Configuration Loaders - Specialized loading logic for different configuration sources
"""
import os
import json
import yaml
import aiofiles
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigLoaders:
    """Configuration loading utilities for different sources"""
    
    @staticmethod
    def load_default_config(service_name: str) -> Dict[str, Any]:
        """Load default configuration for any service"""
        return {
            # Service identification
            "service": {
                "name": service_name,
                "version": "1.0.0",
                "port": ConfigLoaders._get_default_port(service_name),
                "host": "0.0.0.0"
            },
            
            # Database configuration (will be overridden by service-specific)
            "database": {
                "max_connections": 10,
                "timeout": 30,
                "retry_attempts": 3
            },
            
            # Cache configuration
            "cache": {
                "ttl": 3600,
                "max_size": 1000,
                "enabled": True
            },
            
            # Logging configuration
            "logging": {
                "level": "INFO",
                "format": "json",
                "enable_request_logging": True,
                "enable_performance_logging": True
            },
            
            # Performance configuration
            "performance": {
                "enable_tracking": True,
                "slow_operation_threshold_ms": 1000,
                "metrics_retention_hours": 24
            },
            
            # Health check configuration
            "health": {
                "enabled": True,
                "endpoint": "/health",
                "check_interval_seconds": 30
            }
        }
    
    @staticmethod
    async def load_environment_config(config_dir: Path, environment: str) -> Dict[str, Any]:
        """Load environment-specific configuration"""
        env_file = config_dir / f"{environment}.yml"
        
        if env_file.exists():
            async with aiofiles.open(env_file, 'r') as f:
                content = await f.read()
                return yaml.safe_load(content) or {}
        return {}
    
    @staticmethod
    async def load_service_config(config_dir: Path, service_name: str) -> Dict[str, Any]:
        """Load service-specific configuration"""
        service_file = config_dir / f"{service_name}.yml"
        
        if service_file.exists():
            async with aiofiles.open(service_file, 'r') as f:
                content = await f.read()
                return yaml.safe_load(content) or {}
        return {}
    
    @staticmethod
    def load_environment_variables(service_name: str) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        config = {}
        
        # Service-specific environment variables
        env_prefix = f"{service_name.upper().replace('-', '_')}_"
        
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                config_key = key[len(env_prefix):].lower()
                config[config_key] = ConfigLoaders._parse_env_value(value)
        
        return config
    
    @staticmethod
    async def load_secrets() -> Dict[str, Any]:
        """Load secrets from secure storage (Docker secrets, etc.)"""
        secrets = {}
        secrets_dir = Path("/run/secrets")
        
        if secrets_dir.exists():
            tasks = []
            for secret_file in secrets_dir.glob("*"):
                tasks.append(ConfigLoaders._load_single_secret(secret_file))
            
            # Load all secrets concurrently
            secret_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in secret_results:
                if isinstance(result, dict):
                    secrets.update(result)
        
        return secrets
    
    @staticmethod
    async def _load_single_secret(secret_file: Path) -> Dict[str, str]:
        """Load a single secret file asynchronously"""
        try:
            async with aiofiles.open(secret_file, 'r') as f:
                secret_value = (await f.read()).strip()
                secret_name = secret_file.name.lower()
                
                # Map common secret names to config keys
                if secret_name in ['db_password', 'database_password']:
                    return {'database.password': secret_value}
                elif secret_name in ['redis_password']:
                    return {'cache.password': secret_value}
                elif secret_name.endswith('_api_key'):
                    service = secret_name.replace('_api_key', '')
                    return {f'external_services.{service}.api_key': secret_value}
                    
        except Exception:
            # Ignore unreadable secrets
            pass
        
        return {}
    
    @staticmethod
    def create_default_service_config(service_name: str) -> Dict[str, Any]:
        """Create default service configuration"""
        default_config = {
            "service": {
                "name": service_name,
                "description": f"{service_name.title()} microservice",
                "version": "1.0.0"
            }
        }
        
        # Service-specific defaults
        if service_name == "api-gateway":
            default_config.update({
                "rate_limiting": {
                    "enabled": True,
                    "requests_per_minute": 1000
                },
                "cors": {
                    "enabled": True,
                    "origins": ["*"]
                }
            })
        elif service_name == "database-service":
            default_config.update({
                "connection_pool": {
                    "min_connections": 5,
                    "max_connections": 20
                },
                "query_timeout": 30
            })
        
        return default_config
    
    @staticmethod
    async def create_service_config_file(config_dir: Path, service_name: str) -> None:
        """Create default service configuration file asynchronously"""
        service_config_file = config_dir / f"{service_name}.yml"
        if not service_config_file.exists():
            default_config = ConfigLoaders.create_default_service_config(service_name)
            config_content = yaml.dump(default_config, default_flow_style=False)
            
            async with aiofiles.open(service_config_file, 'w') as f:
                await f.write(config_content)
    
    @staticmethod
    def _get_default_port(service_name: str) -> int:
        """Get default port for service"""
        port_mapping = {
            "api-gateway": 8000,
            "mt5-bridge": 8001,
            "trading-engine": 8002,
            "ml-processing": 8003,
            "deep-learning": 8004,
            "ai-orchestration": 8006,
            "ai-provider": 8007,
            "database-service": 8008
        }
        
        return port_mapping.get(service_name, 8000)
    
    @staticmethod
    def _parse_env_value(value: str) -> Any:
        """Parse environment variable value to appropriate type"""
        # Try to parse as JSON first
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Parse boolean values
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Parse numeric values
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass
        
        # Return as string
        return value