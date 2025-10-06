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

        # Central Hub client (will be initialized async)
        self._central_hub_config: Dict[str, Any] = {}

    def _load_config(self) -> Dict:
        """Load YAML configuration"""
        config_file = Path(self.config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(config_file, 'r') as f:
            return yaml.safe_load(f)

    async def initialize_central_hub(self):
        """Initialize Central Hub client and fetch configs"""
        try:
            from central_hub_sdk import CentralHubClient

            logger.info("📡 Initializing Central Hub client...")

            # Initialize Central Hub client
            self.central_hub = CentralHubClient(
                service_name='tick-aggregator',
                service_type='data-processing',
                version='1.0.0',
                capabilities=['tick-aggregation', 'ohlcv-generation', 'timescaledb-query', 'nats-publishing']
            )

            # Fetch configs from Central Hub
            logger.info("⚙️  Fetching configs from Central Hub...")

            nats_config = await self.central_hub.get_messaging_config('nats')
            kafka_config = await self.central_hub.get_messaging_config('kafka')
            postgresql_config = await self.central_hub.get_database_config('postgresql')

            # Store Central Hub config
            self._central_hub_config = {
                'nats': nats_config,
                'kafka': kafka_config,
                'postgresql': postgresql_config
            }

            logger.info(f"✅ Central Hub configs loaded")

        except Exception as e:
            logger.warning(f"⚠️  Failed to get config from Central Hub: {e}")
            logger.warning("⚠️  Falling back to YAML configuration...")

    @property
    def database_config(self) -> Dict[str, Any]:
        """Get database configuration (TimescaleDB)"""
        yaml_db = self._config.get('database', {})

        # If Central Hub config available, use it
        if self._central_hub_config.get('postgresql'):
            hub_db = self._central_hub_config['postgresql']['connection']
            return {
                'host': hub_db['host'],
                'port': hub_db['port'],
                'database': hub_db['database'],
                'user': hub_db['username'],
                'password': hub_db['password'],
                'pool_size': yaml_db.get('pool_size', 5),
                'tenant_id': yaml_db.get('tenant_id', 'system')
            }

        # Fallback to YAML
        return yaml_db

    @property
    def nats_config(self) -> Dict[str, Any]:
        """Get NATS configuration"""
        yaml_nats = self._config.get('nats', {})

        # If Central Hub config available, merge it
        if self._central_hub_config.get('nats'):
            hub_nats = self._central_hub_config['nats']['connection']
            nats_url = f"nats://{hub_nats['host']}:{hub_nats['port']}"
            return {
                'url': nats_url,
                'max_reconnect_attempts': yaml_nats.get('max_reconnect_attempts', -1),
                'reconnect_time_wait': yaml_nats.get('reconnect_time_wait', 2),
                'ping_interval': yaml_nats.get('ping_interval', 120),
                'subjects': yaml_nats.get('subjects', {})
            }

        return yaml_nats

    @property
    def kafka_config(self) -> Dict[str, Any]:
        """Get Kafka configuration"""
        yaml_kafka = self._config.get('kafka', {})

        # If Central Hub config available, merge it
        if self._central_hub_config.get('kafka'):
            hub_kafka = self._central_hub_config['kafka']['connection']
            brokers = hub_kafka['bootstrap_servers']
            return {
                'brokers': brokers if isinstance(brokers, list) else [brokers],
                'topics': yaml_kafka.get('topics', {}),
                'compression_type': yaml_kafka.get('compression_type', 'lz4')
            }

        return yaml_kafka

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
