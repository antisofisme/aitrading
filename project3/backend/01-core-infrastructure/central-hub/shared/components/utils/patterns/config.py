"""
Infrastructure Configuration Manager for Central Hub
====================================================

IMPORTANT - SCOPE:
This module is for Central Hub's INTERNAL infrastructure configuration ONLY.
It loads configs from YAML/JSON files (infrastructure.yaml) for Central Hub's own use.

DO NOT USE THIS FOR SERVICE OPERATIONAL CONFIGS!
For service operational configs, use ConfigClient from shared/components/config/

Purpose:
- Load Central Hub's infrastructure settings (databases, messaging, health checks)
- Manage internal configuration from files
- Support environment variable overrides

NOT for:
- Service operational configurations (batch_size, intervals, etc.) → Use ConfigClient
- Runtime config updates → Use centralized config API (GET/POST /api/v1/config/{service})
- Multi-service configuration management → Use ConfigClient

Usage:
    # For Central Hub infrastructure config only
    from components.utils.patterns.config import InfrastructureConfigManager

    config = InfrastructureConfigManager(service_name="central-hub")
    await config.load_config()
    db_config = await config.get_database_config()
"""

import json
import os
import logging as python_logging
from typing import Any, Dict, Optional, Union, List
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import yaml
import aiofiles


@dataclass
class ConfigSource:
    """Configuration source definition"""
    type: str  # "file", "env", "remote"
    path: Optional[str] = None
    priority: int = 0
    watch: bool = False
    format: str = "json"  # "json", "yaml", "env"


class InfrastructureConfigManager:
    """
    Infrastructure Configuration Manager for Central Hub's INTERNAL use only.

    ⚠️ WARNING - SCOPE LIMITATION:
    This class is designed EXCLUSIVELY for Central Hub's infrastructure configuration.
    It loads configs from YAML/JSON files for Central Hub's internal operations.

    DO NOT USE THIS IN OTHER SERVICES!
    For service operational configs, use ConfigClient from shared/components/config/

    Purpose:
    - Load infrastructure configuration from files (infrastructure.yaml)
    - Manage Central Hub's database/messaging/health check settings
    - Support environment variable overrides with priority system

    Configuration Sources (Priority Order):
    1. Environment variables (priority: 100) - Highest
    2. Environment-specific file (production.json, priority: 50)
    3. Service-specific file (central-hub.json, priority: 40)
    4. Default file (default.json, priority: 10) - Lowest

    Example:
        >>> config = InfrastructureConfigManager(service_name="central-hub")
        >>> await config.load_config()
        >>> db_config = await config.get_database_config()
        >>> print(db_config['host'])
        'suho-postgresql'

    For Service Operational Configs:
        >>> # DON'T USE THIS! Use ConfigClient instead:
        >>> from shared.components.config import ConfigClient
        >>> client = ConfigClient("polygon-historical-downloader")
        >>> await client.init_async()
        >>> config = await client.get_config()
    """

    def __init__(self, service_name: str, environment: str = "development"):
        self.service_name = service_name
        self.environment = environment
        self.config_data: Dict[str, Any] = {}
        self.sources: List[ConfigSource] = []
        self.logger = python_logging.getLogger(f"{service_name}.config")

        # Default configuration sources
        self._add_default_sources()

    def _add_default_sources(self):
        """Add default configuration sources"""
        base_path = Path(__file__).parent.parent.parent / "config"

        # Environment variables (highest priority)
        self.sources.append(ConfigSource(
            type="env",
            priority=100
        ))

        # Environment-specific config file
        env_config_path = base_path / f"{self.environment}.json"
        if env_config_path.exists():
            self.sources.append(ConfigSource(
                type="file",
                path=str(env_config_path),
                priority=50,
                format="json"
            ))

        # Service-specific config file
        service_config_path = base_path / f"{self.service_name}.json"
        if service_config_path.exists():
            self.sources.append(ConfigSource(
                type="file",
                path=str(service_config_path),
                priority=40,
                format="json"
            ))

        # Default config file (lowest priority)
        default_config_path = base_path / "default.json"
        if default_config_path.exists():
            self.sources.append(ConfigSource(
                type="file",
                path=str(default_config_path),
                priority=10,
                format="json"
            ))

        # Sort by priority (highest first)
        self.sources.sort(key=lambda x: x.priority, reverse=True)

    async def load_config(self):
        """Load configuration from all sources"""
        merged_config = {}

        # Load from sources in reverse priority order (lowest to highest)
        for source in reversed(self.sources):
            try:
                source_config = await self._load_from_source(source)
                if source_config:
                    merged_config = self._deep_merge(merged_config, source_config)
                    self.logger.debug(f"Loaded config from {source.type}: {source.path}")
            except Exception as e:
                self.logger.error(f"Failed to load config from {source.type} {source.path}: {str(e)}")

        self.config_data = merged_config
        self.logger.info(f"Configuration loaded for {self.service_name}")

    async def _load_from_source(self, source: ConfigSource) -> Optional[Dict[str, Any]]:
        """Load configuration from a specific source"""
        if source.type == "file":
            return await self._load_from_file(source.path, source.format)
        elif source.type == "env":
            return self._load_from_env()
        elif source.type == "remote":
            return await self._load_from_remote(source.path)
        else:
            self.logger.warning(f"Unknown config source type: {source.type}")
            return None

    async def _load_from_file(self, file_path: str, file_format: str) -> Optional[Dict[str, Any]]:
        """Load configuration from file"""
        try:
            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()

            if file_format.lower() == "json":
                return json.loads(content)
            elif file_format.lower() in ["yaml", "yml"]:
                return yaml.safe_load(content)
            else:
                self.logger.error(f"Unsupported config format: {file_format}")
                return None

        except FileNotFoundError:
            self.logger.debug(f"Config file not found: {file_path}")
            return None
        except Exception as e:
            self.logger.error(f"Error loading config file {file_path}: {str(e)}")
            return None

    def _load_from_env(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        config = {}
        service_prefix = f"{self.service_name.upper().replace('-', '_')}_"

        for key, value in os.environ.items():
            if key.startswith(service_prefix):
                # Remove service prefix
                config_key = key[len(service_prefix):].lower()

                # Convert to nested structure if key contains double underscores
                if "__" in config_key:
                    self._set_nested_value(config, config_key.split("__"), self._convert_env_value(value))
                else:
                    config[config_key] = self._convert_env_value(value)

        return config

    async def _load_from_remote(self, url: str) -> Optional[Dict[str, Any]]:
        """Load configuration from remote source"""
        # TODO: Implement remote config loading (HTTP, etcd, consul, etc.)
        self.logger.warning("Remote config loading not implemented yet")
        return None

    def _convert_env_value(self, value: str) -> Union[str, int, float, bool]:
        """Convert environment variable string to appropriate type"""
        # Boolean values
        if value.lower() in ("true", "false"):
            return value.lower() == "true"

        # Numeric values
        try:
            if "." in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass

        # String value
        return value

    def _set_nested_value(self, config: Dict[str, Any], keys: List[str], value: Any):
        """Set nested dictionary value from key path"""
        current = config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value

    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        result = base.copy()

        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    async def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports dot notation)"""
        keys = key.split('.')
        current = self.config_data

        try:
            for k in keys:
                current = current[k]
            return current
        except (KeyError, TypeError):
            return default

    async def set(self, key: str, value: Any):
        """Set configuration value by key (supports dot notation)"""
        keys = key.split('.')
        current = self.config_data

        # Navigate to parent of target key
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        # Set the value
        current[keys[-1]] = value

    async def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section"""
        return await self.get(section, {})

    async def has_key(self, key: str) -> bool:
        """Check if configuration key exists"""
        value = await self.get(key, object())
        return value is not object()

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration data"""
        return self.config_data.copy()

    async def reload(self):
        """Reload configuration from all sources"""
        self.logger.info("Reloading configuration")
        await self.load_config()

    def add_source(self, source: ConfigSource):
        """Add new configuration source"""
        self.sources.append(source)
        self.sources.sort(key=lambda x: x.priority, reverse=True)

    # Common configuration patterns
    async def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return await self.get_section("database")

    async def get_cache_config(self) -> Dict[str, Any]:
        """Get cache configuration"""
        return await self.get_section("cache")

    async def get_service_config(self) -> Dict[str, Any]:
        """Get service-specific configuration"""
        return {
            "name": self.service_name,
            "environment": self.environment,
            "port": await self.get("port", 8000),
            "host": await self.get("host", "0.0.0.0"),
            "debug": await self.get("debug", False),
            "log_level": await self.get("log_level", "INFO")
        }

    async def get_external_services(self) -> Dict[str, Any]:
        """Get external service configurations"""
        return await self.get_section("external_services")

    async def get_feature_flags(self) -> Dict[str, bool]:
        """Get feature flags"""
        return await self.get_section("features")

    async def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if feature flag is enabled"""
        features = await self.get_feature_flags()
        return features.get(feature_name, False)

    async def get_rate_limits(self) -> Dict[str, Any]:
        """Get rate limiting configuration"""
        return await self.get_section("rate_limits")

    async def get_circuit_breaker_config(self) -> Dict[str, Any]:
        """Get circuit breaker configuration"""
        return await self.get_section("circuit_breaker")

    async def validate_config(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []

        # Check required service config
        service_config = await self.get_service_config()
        if not service_config.get("name"):
            errors.append("Service name is required")

        if not isinstance(service_config.get("port"), int):
            errors.append("Service port must be an integer")

        # Check database config if present
        db_config = await self.get_database_config()
        if db_config:
            required_db_fields = ["host", "port", "database", "username"]
            for field in required_db_fields:
                if not db_config.get(field):
                    errors.append(f"Database {field} is required")

        return errors

    def __str__(self) -> str:
        """String representation of configuration"""
        return f"InfrastructureConfigManager(service={self.service_name}, env={self.environment}, sources={len(self.sources)})"

    def __repr__(self) -> str:
        """Detailed string representation"""
        return f"InfrastructureConfigManager(service_name='{self.service_name}', environment='{self.environment}', config_keys={list(self.config_data.keys())})"


# Backward compatibility alias (DEPRECATED)
# TODO: Remove after all references updated
ConfigManager = InfrastructureConfigManager