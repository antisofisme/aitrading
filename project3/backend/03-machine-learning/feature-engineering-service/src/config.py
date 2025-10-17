"""
Configuration loader for Feature Engineering Service
Loads database configuration from environment variables
"""
import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager for Feature Engineering Service"""

    def __init__(self, config_path: str = "config/features.yaml"):
        self.config_path = config_path
        self._config = self._load_yaml_config()

        # Load ClickHouse config from environment variables
        self._clickhouse_config = self._load_clickhouse_config()

        logger.info(f"✅ Configuration loaded from {config_path}")
        logger.info("✅ ClickHouse config loaded from environment variables")

    def _load_yaml_config(self) -> Dict[str, Any]:
        """Load YAML configuration file"""
        config_file = Path(self.config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(config_file, 'r') as f:
            return yaml.safe_load(f)

    def _load_clickhouse_config(self) -> Dict[str, Any]:
        """Load ClickHouse configuration from environment variables"""
        return {
            'connection': {
                'host': os.getenv('CLICKHOUSE_HOST', 'localhost'),
                'port': int(os.getenv('CLICKHOUSE_PORT', '8123')),  # HTTP port
                'http_port': int(os.getenv('CLICKHOUSE_PORT', '8123')),
                'database': os.getenv('CLICKHOUSE_DATABASE', 'suho_analytics'),
                'username': os.getenv('CLICKHOUSE_USER', 'default'),
                'user': os.getenv('CLICKHOUSE_USER', 'default'),
                'password': os.getenv('CLICKHOUSE_PASSWORD', '')
            }
        }

    @property
    def clickhouse_config(self) -> Dict[str, Any]:
        """Get ClickHouse configuration"""
        return self._clickhouse_config

    @property
    def service_config(self) -> Dict[str, Any]:
        """Get service configuration"""
        return self._config.get('service', {})

    @property
    def primary_pair(self) -> str:
        """Get primary trading pair"""
        return self._config.get('primary_pair', 'XAU/USD')

    @property
    def timeframes(self) -> Dict[str, str]:
        """Get timeframes configuration"""
        return self._config.get('timeframes', {})

    @property
    def processing_config(self) -> Dict[str, Any]:
        """Get processing configuration"""
        return self._config.get('processing', {})

    @property
    def feature_groups(self) -> Dict[str, Any]:
        """Get feature groups configuration"""
        return self._config.get('feature_groups', {})

    def get_full_config(self) -> Dict[str, Any]:
        """Get full YAML configuration"""
        return self._config
