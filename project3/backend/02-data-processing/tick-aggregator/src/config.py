"""
Configuration loader for Tick Aggregator
Integrates with Central Hub for database and messaging configs
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class Config:
    def __init__(self, config_path: str = "/app/config/aggregator.yaml"):
        self.config_path = config_path
        self._config = self._load_config()

        # Environment variables
        self.instance_id = os.getenv("INSTANCE_ID", "aggregator-1")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

        # Load database and messaging configs from environment variables
        self._load_env_configs()

    def _load_config(self) -> Dict:
        """Load YAML configuration with environment variable expansion"""
        config_file = Path(self.config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(config_file, 'r') as f:
            content = f.read()
            # Expand environment variables in YAML
            content = self._expand_env_vars(content)
            return yaml.safe_load(content)

    def _expand_env_vars(self, content: str) -> str:
        """Expand ${VAR} environment variables in config"""
        import re
        pattern = r'\$\{([^}]+)\}'

        def replacer(match):
            var_name = match.group(1)
            return os.getenv(var_name, match.group(0))

        return re.sub(pattern, replacer, content)

    def _load_env_configs(self):
        """Load database and messaging configs from environment variables"""
        # PostgreSQL/TimescaleDB config
        self._postgresql_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', '5432')),
            'database': os.getenv('POSTGRES_DB', 'suho_trading'),
            'user': os.getenv('POSTGRES_USER', 'admin'),
            'password': os.getenv('POSTGRES_PASSWORD', ''),
            'pool_size': int(os.getenv('POSTGRES_POOL_SIZE', '5')),
            'tenant_id': os.getenv('TENANT_ID', 'system')
        }

        # ClickHouse config
        self._clickhouse_config = {
            'host': os.getenv('CLICKHOUSE_HOST', 'localhost'),
            'port': int(os.getenv('CLICKHOUSE_PORT', '9000')),
            'database': os.getenv('CLICKHOUSE_DATABASE', 'suho_analytics'),
            'user': os.getenv('CLICKHOUSE_USER', 'suho_analytics'),
            'password': os.getenv('CLICKHOUSE_PASSWORD', '')
        }

        # NATS config (cluster support)
        nats_urls = os.getenv('NATS_URL', 'nats://localhost:4222')
        cluster_urls = [url.strip() for url in nats_urls.split(',')]

        self._nats_config = {
            'cluster_urls': cluster_urls,
            'url': nats_urls,
            'max_reconnect_attempts': int(os.getenv('NATS_MAX_RECONNECT_ATTEMPTS', '-1')),
            'reconnect_time_wait': int(os.getenv('NATS_RECONNECT_TIME_WAIT', '2')),
            'ping_interval': int(os.getenv('NATS_PING_INTERVAL', '120')),
            'subjects': self._config.get('nats', {}).get('subjects', {})
        }

        # Kafka config
        kafka_brokers = os.getenv('KAFKA_BROKERS', 'localhost:9092')
        self._kafka_config = {
            'brokers': [broker.strip() for broker in kafka_brokers.split(',')],
            'topics': self._config.get('kafka', {}).get('topics', {}),
            'compression_type': os.getenv('KAFKA_COMPRESSION_TYPE', 'lz4')
        }

        logger.info("✅ Loaded configs from environment variables (PostgreSQL, ClickHouse, NATS, Kafka)")

    @property
    def database_config(self) -> Dict[str, Any]:
        """Get database configuration (TimescaleDB)"""
        return self._postgresql_config

    @property
    def nats_config(self) -> Dict[str, Any]:
        """Get NATS configuration with cluster support"""
        return self._nats_config

    @property
    def kafka_config(self) -> Dict[str, Any]:
        """Get Kafka configuration"""
        return self._kafka_config

    @property
    def aggregation_config(self) -> Dict[str, Any]:
        """Get aggregation configuration"""
        return self._config.get('aggregation', {})

    @property
    def timeframes(self) -> List[Dict[str, Any]]:
        """Get timeframe configurations"""
        return self.aggregation_config.get('timeframes', [])

    @property
    def monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration"""
        return self._config.get('monitoring', {})

    @property
    def state_config(self) -> Dict[str, Any]:
        """Get state management configuration"""
        return self._config.get('state', {})

    @property
    def clickhouse_config(self) -> Dict[str, Any]:
        """Get ClickHouse configuration for gap detection"""
        return self._clickhouse_config
