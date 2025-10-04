"""
Configuration loader for ClickHouse Consumer
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any

class Config:
    def __init__(self, config_path: str = "/app/config/consumer.yaml"):
        self.config_path = config_path
        self._config = self._load_config()

        # Environment variables
        self.clickhouse_password = os.getenv("CLICKHOUSE_PASSWORD", "")
        self.instance_id = os.getenv("INSTANCE_ID", "clickhouse-consumer-1")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

    def _load_config(self) -> Dict:
        """Load YAML configuration"""
        config_file = Path(self.config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(config_file, 'r') as f:
            return yaml.safe_load(f)

    @property
    def clickhouse_config(self) -> Dict[str, Any]:
        """Get ClickHouse configuration"""
        config = self._config.get('clickhouse', {})
        # Replace password from environment
        config['password'] = self.clickhouse_password
        return config

    @property
    def nats_config(self) -> Dict[str, Any]:
        """Get NATS configuration"""
        return self._config.get('nats', {})

    @property
    def kafka_config(self) -> Dict[str, Any]:
        """Get Kafka configuration"""
        return self._config.get('kafka', {})

    @property
    def batch_config(self) -> Dict[str, Any]:
        """Get batch insertion configuration"""
        return self._config.get('batch', {})

    @property
    def dedup_config(self) -> Dict[str, Any]:
        """Get deduplication configuration"""
        return self._config.get('deduplication', {})

    @property
    def monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration"""
        return self._config.get('monitoring', {})
