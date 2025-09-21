"""
Configuration Manager for Central Hub Service

Phase 1 Implementation: Basic configuration management without complex features
Focus: Environment variables, file-based config, and basic validation
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path
import yaml
import json
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class CentralHubConfig(BaseSettings):
    """Central Hub configuration model"""

    # Service configuration
    service_name: str = Field(default="central-hub", description="Service name")
    service_port: int = Field(default=8010, description="Service port")
    service_host: str = Field(default="0.0.0.0", description="Service host")

    # Logging configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: str = Field(default="logs/central-hub.log", description="Log file path")
    log_format: str = Field(default="json", description="Log format (json|text)")

    # Service registry configuration
    registry_ttl: int = Field(default=300, description="Service TTL in seconds")
    registry_cleanup_interval: int = Field(default=60, description="Registry cleanup interval")

    # Health monitoring configuration
    health_check_interval: int = Field(default=30, description="Health check interval")
    health_timeout: int = Field(default=10, description="Health check timeout")

    # Environment
    environment: str = Field(default="development", description="Environment")
    debug: bool = Field(default=False, description="Debug mode")

    class Config:
        env_prefix = "CENTRAL_HUB_"
        env_file = ".env"
        case_sensitive = False


class ConfigManager:
    """
    Configuration Manager for Central Hub Service

    Phase 1 Implementation:
    - Environment variable support
    - File-based configuration
    - Basic validation
    - Simple caching
    """

    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir) if config_dir else Path("config")
        self.config_cache: Dict[str, Any] = {}
        self.config_model: Optional[CentralHubConfig] = None
        self.logger = logging.getLogger(self.__class__.__name__)

    async def initialize(self) -> None:
        """Initialize configuration manager"""
        try:
            # Load configuration model
            self.config_model = CentralHubConfig()

            # Load additional config files
            await self._load_config_files()

            # Cache commonly used values
            self._cache_common_configs()

            self.logger.info("✅ Configuration Manager initialized successfully")

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Configuration Manager: {e}")
            raise

    async def _load_config_files(self) -> None:
        """Load configuration from files"""
        try:
            # Load main config file
            main_config_path = self.config_dir / "main.yaml"
            if main_config_path.exists():
                with open(main_config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                    if config_data:
                        self.config_cache.update(config_data)

            # Load environment-specific config
            env_config_path = self.config_dir / f"{self.config_model.environment}.yaml"
            if env_config_path.exists():
                with open(env_config_path, 'r') as f:
                    env_config = yaml.safe_load(f)
                    if env_config:
                        self.config_cache.update(env_config)

        except Exception as e:
            self.logger.warning(f"⚠️ Failed to load config files: {e}")

    def _cache_common_configs(self) -> None:
        """Cache commonly used configuration values"""
        # Cache model values
        if self.config_model:
            self.config_cache.update({
                "service.name": self.config_model.service_name,
                "service.port": self.config_model.service_port,
                "service.host": self.config_model.service_host,
                "logging.level": self.config_model.log_level,
                "logging.file": self.config_model.log_file,
                "logging.format": self.config_model.log_format,
                "registry.ttl": self.config_model.registry_ttl,
                "registry.cleanup_interval": self.config_model.registry_cleanup_interval,
                "health.check_interval": self.config_model.health_check_interval,
                "health.timeout": self.config_model.health_timeout,
                "environment": self.config_model.environment,
                "debug": self.config_model.debug
            })

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key

        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        try:
            # Check cache first
            if key in self.config_cache:
                return self.config_cache[key]

            # Handle dot notation
            if '.' in key:
                keys = key.split('.')
                value = self.config_cache
                for k in keys:
                    if isinstance(value, dict) and k in value:
                        value = value[k]
                    else:
                        return default
                return value

            return default

        except Exception as e:
            self.logger.warning(f"⚠️ Failed to get config key '{key}': {e}")
            return default

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value

        Args:
            key: Configuration key
            value: Configuration value
        """
        try:
            self.config_cache[key] = value
            self.logger.debug(f"📝 Set config: {key} = {value}")

        except Exception as e:
            self.logger.error(f"❌ Failed to set config key '{key}': {e}")

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values"""
        return self.config_cache.copy()

    def get_service_config(self) -> Dict[str, Any]:
        """Get service-specific configuration"""
        return {
            "name": self.get("service.name"),
            "port": self.get("service.port"),
            "host": self.get("service.host"),
            "environment": self.get("environment"),
            "debug": self.get("debug")
        }

    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return {
            "level": self.get("logging.level"),
            "file": self.get("logging.file"),
            "format": self.get("logging.format")
        }

    def get_registry_config(self) -> Dict[str, Any]:
        """Get service registry configuration"""
        return {
            "ttl": self.get("registry.ttl"),
            "cleanup_interval": self.get("registry.cleanup_interval")
        }

    def get_health_config(self) -> Dict[str, Any]:
        """Get health monitoring configuration"""
        return {
            "check_interval": self.get("health.check_interval"),
            "timeout": self.get("health.timeout")
        }

    async def reload(self) -> None:
        """Reload configuration"""
        try:
            self.logger.info("🔄 Reloading configuration...")

            # Clear cache
            self.config_cache.clear()

            # Reload everything
            await self.initialize()

            self.logger.info("✅ Configuration reloaded successfully")

        except Exception as e:
            self.logger.error(f"❌ Failed to reload configuration: {e}")
            raise

    def validate_config(self) -> Dict[str, Any]:
        """
        Validate current configuration

        Returns:
            Validation results
        """
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }

        try:
            # Validate required configurations
            required_configs = [
                ("service.name", str),
                ("service.port", int),
                ("logging.level", str)
            ]

            for key, expected_type in required_configs:
                value = self.get(key)
                if value is None:
                    validation_results["errors"].append(f"Missing required config: {key}")
                    validation_results["valid"] = False
                elif not isinstance(value, expected_type):
                    validation_results["errors"].append(
                        f"Invalid type for {key}: expected {expected_type.__name__}, got {type(value).__name__}"
                    )
                    validation_results["valid"] = False

            # Validate port range
            port = self.get("service.port")
            if port and (port < 1024 or port > 65535):
                validation_results["warnings"].append(f"Port {port} is outside recommended range")

            # Validate log level
            log_level = self.get("logging.level")
            if log_level and log_level.upper() not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                validation_results["errors"].append(f"Invalid log level: {log_level}")
                validation_results["valid"] = False

        except Exception as e:
            validation_results["errors"].append(f"Validation error: {str(e)}")
            validation_results["valid"] = False

        return validation_results

    def get_status(self) -> Dict[str, Any]:
        """Get configuration manager status"""
        return {
            "initialized": self.config_model is not None,
            "cached_configs": len(self.config_cache),
            "environment": self.get("environment"),
            "debug_mode": self.get("debug"),
            "config_validation": self.validate_config()
        }