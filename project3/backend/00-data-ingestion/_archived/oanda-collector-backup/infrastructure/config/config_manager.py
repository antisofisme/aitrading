"""
Configuration Manager - Handles configuration loading and hot-reload
"""
import logging
import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Manages service configuration with support for:
    - YAML file loading
    - Environment variable substitution
    - Central Hub config synchronization
    - Hot-reload support
    """

    def __init__(
        self,
        config_path: str,
        central_hub_client=None
    ):
        """
        Initialize Configuration Manager

        Args:
            config_path: Path to config.yaml file
            central_hub_client: Optional Central Hub client for remote config
        """
        self.config_path = Path(config_path)
        self.central_hub = central_hub_client

        self.config: Dict[str, Any] = {}
        self.config_version: Optional[str] = None

        logger.info(f"Configuration manager initialized: {config_path}")

    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file

        Returns:
            Dict containing configuration
        """
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Config file not found: {self.config_path}")

            with open(self.config_path, 'r') as f:
                config_raw = yaml.safe_load(f)

            # Substitute environment variables
            self.config = self._substitute_env_vars(config_raw)

            logger.info("Configuration loaded successfully")
            return self.config

        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise

    def _substitute_env_vars(self, config: Any) -> Any:
        """
        Recursively substitute environment variables in config

        Args:
            config: Configuration object (dict, list, or primitive)

        Returns:
            Configuration with substituted values
        """
        if isinstance(config, dict):
            return {
                key: self._substitute_env_vars(value)
                for key, value in config.items()
            }
        elif isinstance(config, list):
            return [self._substitute_env_vars(item) for item in config]
        elif isinstance(config, str):
            # Check for environment variable pattern ${VAR_NAME}
            if config.startswith('${') and config.endswith('}'):
                var_name = config[2:-1]

                # Support default values: ${VAR_NAME:-default}
                if ':-' in var_name:
                    var_name, default = var_name.split(':-', 1)
                    return os.getenv(var_name, default)
                else:
                    return os.getenv(var_name, config)
            return config
        else:
            return config

    async def sync_with_central_hub(self, service_name: str) -> bool:
        """
        Synchronize configuration with Central Hub

        Args:
            service_name: Service name to fetch config for

        Returns:
            bool: True if sync successful
        """
        if not self.central_hub:
            logger.warning("Central Hub client not configured, skipping sync")
            return False

        try:
            remote_config = await self.central_hub.get_configuration(service_name)

            if remote_config:
                # Merge remote config with local config
                # Remote config takes precedence for specific sections
                if 'configuration' in remote_config:
                    self._merge_config(remote_config['configuration'])

                self.config_version = remote_config.get('config_version')
                logger.info(f"Configuration synced with Central Hub (version: {self.config_version})")
                return True
            else:
                logger.warning("No remote configuration found")
                return False

        except Exception as e:
            logger.error(f"Error syncing with Central Hub: {e}")
            return False

    def _merge_config(self, remote_config: Dict[str, Any]) -> None:
        """
        Merge remote configuration with local config

        Args:
            remote_config: Remote configuration to merge
        """
        for section, values in remote_config.items():
            if section in self.config:
                if isinstance(values, dict) and isinstance(self.config[section], dict):
                    # Deep merge for dict sections
                    self.config[section].update(values)
                else:
                    # Replace for non-dict sections
                    self.config[section] = values
            else:
                # Add new section
                self.config[section] = values

        logger.info(f"Merged remote configuration: {list(remote_config.keys())}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key (supports dot notation)

        Args:
            key: Configuration key (e.g., "oanda.environment")
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get entire configuration section

        Args:
            section: Section name (e.g., "oanda", "nats")

        Returns:
            Dict containing section configuration
        """
        return self.config.get(section, {})

    def get_all(self) -> Dict[str, Any]:
        """
        Get entire configuration

        Returns:
            Complete configuration dict
        """
        return self.config

    def reload(self) -> Dict[str, Any]:
        """
        Reload configuration from file

        Returns:
            Reloaded configuration
        """
        logger.info("Reloading configuration")
        return self.load_config()

    async def watch_for_updates(self, interval: int = 60) -> None:
        """
        Watch for configuration updates from Central Hub

        Args:
            interval: Check interval in seconds
        """
        import asyncio

        logger.info(f"Starting configuration watch (interval: {interval}s)")

        while True:
            try:
                await asyncio.sleep(interval)

                # Check for updates from Central Hub
                if self.central_hub:
                    service_name = self.config.get('service', {}).get('name')
                    if service_name:
                        await self.sync_with_central_hub(service_name)

            except asyncio.CancelledError:
                logger.info("Configuration watch cancelled")
                break

            except Exception as e:
                logger.error(f"Error in configuration watch: {e}")

    def validate_config(self) -> bool:
        """
        Validate configuration completeness

        Returns:
            bool: True if configuration is valid
        """
        required_sections = ['service', 'oanda', 'central_hub', 'nats', 'streaming']

        for section in required_sections:
            if section not in self.config:
                logger.error(f"Missing required configuration section: {section}")
                return False

        # Validate OANDA accounts
        accounts = self.config.get('oanda', {}).get('accounts', [])
        valid_accounts = [
            acc for acc in accounts
            if acc.get('enabled') and acc.get('id') and acc.get('token')
        ]

        if not valid_accounts:
            logger.error("No valid OANDA accounts configured")
            return False

        logger.info(f"Configuration validated: {len(valid_accounts)} active accounts")
        return True
