"""
Configuration loader for Data Bridge
Refactored to use Database Manager instead of direct ClickHouse
Fetches messaging config from Central Hub
"""
import os
import yaml
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Import Central Hub SDK
try:
    from central_hub_sdk import CentralHubClient
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    logging.warning("Central Hub SDK not available, using fallback config")

logger = logging.getLogger(__name__)

class Config:
    def __init__(self, config_path: str = "/app/config/bridge.yaml"):
        self.config_path = config_path
        self._config = self._load_config()

        # Environment variables
        self.instance_id = os.getenv("INSTANCE_ID", "data-bridge-1")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

        # Central Hub client (will be initialized async)
        self.central_hub: Optional[CentralHubClient] = None
        self._central_hub_config: Dict[str, Any] = {}

        # Database Manager will handle database connections
        # No need for separate ClickHouse credentials here

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

    async def initialize_central_hub(self):
        """Initialize Central Hub client and fetch configs"""
        if not SDK_AVAILABLE:
            logger.warning("⚠️  Central Hub SDK not available, using YAML config only")
            return

        try:
            logger.info("📡 Initializing Central Hub client...")

            # Initialize Central Hub client
            self.central_hub = CentralHubClient(
                service_name='data-bridge',
                service_type='data-processing',
                version='1.0.0',
                capabilities=['nats-consumer', 'kafka-consumer', 'database-writer']
            )

            # Register with Central Hub service registry
            logger.info("📝 Registering with Central Hub...")
            await self.central_hub.register()
            logger.info("✅ Registered with Central Hub")

            # Fetch messaging configs from Central Hub
            logger.info("⚙️  Fetching messaging configs from Central Hub...")

            nats_config = await self.central_hub.get_messaging_config('nats')
            kafka_config = await self.central_hub.get_messaging_config('kafka')

            # Fetch database configs from Central Hub
            logger.info("⚙️  Fetching database configs from Central Hub...")

            postgresql_config = await self.central_hub.get_database_config('postgresql')
            clickhouse_config = await self.central_hub.get_database_config('clickhouse')
            dragonflydb_config = await self.central_hub.get_database_config('dragonflydb')

            # Store Central Hub config
            self._central_hub_config = {
                'nats': nats_config,
                'kafka': kafka_config,
                'postgresql': postgresql_config,
                'clickhouse': clickhouse_config,
                'dragonflydb': dragonflydb_config
            }

            logger.info(f"🔍 DEBUG: _central_hub_config keys: {list(self._central_hub_config.keys())}")
            logger.info(f"🔍 DEBUG: postgresql config type: {type(postgresql_config)}")
            logger.info(f"✅ Using NATS from Central Hub: {nats_config['connection']['host']}:{nats_config['connection']['port']}")
            logger.info(f"✅ Using Kafka from Central Hub: {kafka_config['connection']['bootstrap_servers']}")
            logger.info(f"✅ Using PostgreSQL from Central Hub: {postgresql_config['connection']['host']}:{postgresql_config['connection']['port']}")
            logger.info(f"✅ Using ClickHouse from Central Hub: {clickhouse_config['connection']['host']}:{clickhouse_config['connection'].get('http_port', clickhouse_config['connection'].get('port', '8123'))}")

        except Exception as e:
            logger.warning(f"⚠️  Failed to get config from Central Hub: {e}")
            logger.warning("⚠️  Falling back to YAML configuration...")

    @property
    def nats_config(self) -> Dict[str, Any]:
        """
        Get NATS configuration (merged from Central Hub + YAML)

        Priority:
        1. Central Hub config (connection details + cluster URLs)
        2. YAML config (subjects, reconnection params)
        """
        yaml_nats = self._config.get('nats', {})

        # If Central Hub config available, merge it
        if self._central_hub_config.get('nats'):
            hub_nats = self._central_hub_config['nats']['connection']

            # Use cluster_urls if available (preferred for HA)
            cluster_urls = hub_nats.get('cluster_urls')

            if cluster_urls:
                # Use cluster URLs for high availability
                return {
                    'cluster_urls': cluster_urls,  # From Central Hub (array)
                    'url': ','.join(cluster_urls),  # Fallback comma-separated format
                    'max_reconnect_attempts': yaml_nats.get('max_reconnect_attempts', -1),
                    'reconnect_time_wait': yaml_nats.get('reconnect_time_wait', 2),
                    'ping_interval': yaml_nats.get('ping_interval', 120),
                    'subjects': yaml_nats.get('subjects', {})
                }
            else:
                # Fallback to single host/port (legacy mode)
                nats_url = f"nats://{hub_nats['host']}:{hub_nats['port']}"
                return {
                    'url': nats_url,  # From Central Hub
                    'max_reconnect_attempts': yaml_nats.get('max_reconnect_attempts', -1),
                    'reconnect_time_wait': yaml_nats.get('reconnect_time_wait', 2),
                    'ping_interval': yaml_nats.get('ping_interval', 120),
                    'subjects': yaml_nats.get('subjects', {})
                }

        # Fallback to YAML only
        return yaml_nats

    @property
    def kafka_config(self) -> Dict[str, Any]:
        """
        Get Kafka configuration (merged from Central Hub + YAML)

        Priority:
        1. Central Hub config (brokers)
        2. YAML config (topics, consumer params)
        """
        yaml_kafka = self._config.get('kafka', {})

        # If Central Hub config available, merge it
        if self._central_hub_config.get('kafka'):
            hub_kafka = self._central_hub_config['kafka']['connection']

            # Get brokers from Central Hub
            brokers = hub_kafka['bootstrap_servers']

            # Merge: Central Hub brokers + YAML topics/params
            return {
                'brokers': brokers if isinstance(brokers, list) else [brokers],  # From Central Hub
                'group_id': yaml_kafka.get('group_id', 'data-bridge'),
                'auto_offset_reset': yaml_kafka.get('auto_offset_reset', 'latest'),
                'enable_auto_commit': yaml_kafka.get('enable_auto_commit', True),
                'auto_commit_interval_ms': yaml_kafka.get('auto_commit_interval_ms', 5000),
                'fetch_min_bytes': yaml_kafka.get('fetch_min_bytes', 1024),
                'fetch_max_wait_ms': yaml_kafka.get('fetch_max_wait_ms', 500),
                'max_poll_records': yaml_kafka.get('max_poll_records', 500),
                'topics': yaml_kafka.get('topics', {})
            }

        # Fallback to YAML only
        return yaml_kafka

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
        Get database configurations from Central Hub

        Returns database configs in format expected by DatabasePoolManager:
        {'postgresql': {...}, 'dragonflydb': {...}, 'clickhouse': {...}}

        Note: DatabasePoolManager will map these to internal names:
        - postgresql -> timescale
        - dragonflydb -> dragonfly
        """
        return {
            'postgresql': self._central_hub_config.get('postgresql', {}) if self._central_hub_config else {},
            'dragonflydb': self._central_hub_config.get('dragonflydb', {}) if self._central_hub_config else {},
            'clickhouse': self._central_hub_config.get('clickhouse', {}) if self._central_hub_config else {}
        }
