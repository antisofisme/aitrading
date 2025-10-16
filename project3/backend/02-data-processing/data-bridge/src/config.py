"""
Configuration loader for Data Bridge
Refactored to use environment variables (Central Hub pattern)
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class Config:
    def __init__(self, config_path: str = "/app/config/bridge.yaml"):
        self.config_path = config_path
        self._config = self._load_config()

        # Environment variables
        self.instance_id = os.getenv("INSTANCE_ID", "data-bridge-1")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

        # Load configs from environment variables
        self._load_env_configs()

    def _load_config(self) -> Dict:
        """Load YAML configuration with environment variable expansion"""
        config_file = Path(self.config_path)
        if not config_file.exists():
            logger.warning(f"Config file not found: {self.config_path}, using environment variables only")
            return {}

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
        logger.info("📡 Loading configuration from environment variables...")

        # PostgreSQL config
        self._postgresql_config = {
            'connection': {
                'host': os.getenv('POSTGRES_HOST', 'localhost'),
                'port': int(os.getenv('POSTGRES_PORT', 5432)),
                'database': os.getenv('POSTGRES_DB', 'suho_trading'),
                'user': os.getenv('POSTGRES_USER', 'postgres'),
                'password': os.getenv('POSTGRES_PASSWORD', ''),
                'min_size': int(os.getenv('POSTGRES_MIN_POOL', 10)),
                'max_size': int(os.getenv('POSTGRES_MAX_POOL', 50))
            }
        }

        # DragonflyDB config
        self._dragonflydb_config = {
            'connection': {
                'host': os.getenv('DRAGONFLY_HOST', 'localhost'),
                'port': int(os.getenv('DRAGONFLY_PORT', 6379)),
                'password': os.getenv('DRAGONFLY_PASSWORD', ''),
                'db': int(os.getenv('DRAGONFLY_DB', 0))
            }
        }

        # ClickHouse config
        self._clickhouse_config = {
            'connection': {
                'host': os.getenv('CLICKHOUSE_HOST', 'localhost'),
                'port': int(os.getenv('CLICKHOUSE_PORT', 8123)),
                'http_port': int(os.getenv('CLICKHOUSE_HTTP_PORT', 8123)),
                'database': os.getenv('CLICKHOUSE_DATABASE', 'suho_analytics'),
                'user': os.getenv('CLICKHOUSE_USER', 'default'),
                'password': os.getenv('CLICKHOUSE_PASSWORD', '')
            }
        }

        # NATS config
        nats_url = os.getenv('NATS_URL', 'nats://localhost:4222')
        if ',' in nats_url:
            # Cluster mode
            self._nats_cluster_urls = [url.strip() for url in nats_url.split(',')]
            logger.info(f"✅ NATS cluster: {len(self._nats_cluster_urls)} nodes")
        else:
            # Single server
            self._nats_cluster_urls = [nats_url]
            logger.info(f"✅ NATS single server: {nats_url}")

        # Kafka config
        kafka_brokers = os.getenv('KAFKA_BROKERS', 'localhost:9092')
        self._kafka_brokers = [b.strip() for b in kafka_brokers.split(',')]
        logger.info(f"✅ Kafka brokers: {self._kafka_brokers}")

        logger.info(f"✅ PostgreSQL: {self._postgresql_config['connection']['host']}:{self._postgresql_config['connection']['port']}")
        logger.info(f"✅ DragonflyDB: {self._dragonflydb_config['connection']['host']}:{self._dragonflydb_config['connection']['port']}")
        logger.info(f"✅ ClickHouse: {self._clickhouse_config['connection']['host']}:{self._clickhouse_config['connection']['http_port']}")

    async def initialize_central_hub(self):
        """
        Initialize method for backward compatibility
        No longer fetches from Central Hub API - uses environment variables
        """
        logger.info("✅ Configuration loaded from environment variables (no Central Hub API call)")
        pass

    @property
    def nats_config(self) -> Dict[str, Any]:
        """
        Get NATS configuration

        Priority:
        1. Environment variables (NATS_URL)
        2. YAML config (subjects, reconnection params)
        """
        yaml_nats = self._config.get('nats', {})

        if len(self._nats_cluster_urls) > 1:
            # Cluster mode
            return {
                'cluster_urls': self._nats_cluster_urls,
                'url': ','.join(self._nats_cluster_urls),
                'max_reconnect_attempts': yaml_nats.get('max_reconnect_attempts', -1),
                'reconnect_time_wait': yaml_nats.get('reconnect_time_wait', 2),
                'ping_interval': yaml_nats.get('ping_interval', 120),
                'subjects': yaml_nats.get('subjects', {})
            }
        else:
            # Single server
            return {
                'url': self._nats_cluster_urls[0],
                'max_reconnect_attempts': yaml_nats.get('max_reconnect_attempts', -1),
                'reconnect_time_wait': yaml_nats.get('reconnect_time_wait', 2),
                'ping_interval': yaml_nats.get('ping_interval', 120),
                'subjects': yaml_nats.get('subjects', {})
            }

    @property
    def kafka_config(self) -> Dict[str, Any]:
        """
        Get Kafka configuration

        Priority:
        1. Environment variables (KAFKA_BROKERS)
        2. YAML config (topics, consumer params)
        """
        yaml_kafka = self._config.get('kafka', {})

        return {
            'brokers': self._kafka_brokers,
            'group_id': yaml_kafka.get('group_id', 'data-bridge'),
            'auto_offset_reset': yaml_kafka.get('auto_offset_reset', 'latest'),
            'enable_auto_commit': yaml_kafka.get('enable_auto_commit', True),
            'auto_commit_interval_ms': yaml_kafka.get('auto_commit_interval_ms', 5000),
            'fetch_min_bytes': yaml_kafka.get('fetch_min_bytes', 1024),
            'fetch_max_wait_ms': yaml_kafka.get('fetch_max_wait_ms', 500),
            'max_poll_records': yaml_kafka.get('max_poll_records', 500),
            'topics': yaml_kafka.get('topics', {})
        }

    @property
    def batch_config(self) -> Dict[str, Any]:
        """Get batch processing configuration"""
        return self._config.get('batch', {
            'tick_batch_size': 1000,
            'aggregate_batch_size': 500,
            'flush_interval_seconds': 5
        })

    @property
    def dedup_config(self) -> Dict[str, Any]:
        """Get deduplication configuration"""
        return self._config.get('deduplication', {
            'enabled': True,
            'cache_size': 10000,
            'cache_ttl_seconds': 3600
        })

    @property
    def monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration"""
        return self._config.get('monitoring', {
            'report_interval_seconds': 60,
            'enable_metrics': True
        })

    @property
    def database_configs(self) -> Dict[str, Any]:
        """
        Get database configurations from environment variables

        Returns database configs in format expected by DatabasePoolManager:
        {'postgresql': {...}, 'dragonflydb': {...}, 'clickhouse': {...}}

        Note: DatabasePoolManager will map these to internal names:
        - postgresql -> timescale
        - dragonflydb -> dragonfly
        """
        return {
            'postgresql': self._postgresql_config,
            'dragonflydb': self._dragonflydb_config,
            'clickhouse': self._clickhouse_config
        }
