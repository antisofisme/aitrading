"""
Configuration loader for Polygon.io Live Collector
Refactored to use environment variables (Central Hub pattern)
"""
import os
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PairConfig:
    symbol: str
    polygon_symbol: str
    description: str
    priority: int
    use_case: str = None
    volatility: str = None
    poll_interval: int = None

class Config:
    def __init__(self, config_path: str = "/app/config/pairs.yaml"):
        self.config_path = config_path
        self._config = self._load_config()

        # Environment variables
        self.polygon_api_key = os.getenv("POLYGON_API_KEY")
        if not self.polygon_api_key:
            raise ValueError("POLYGON_API_KEY environment variable not set")

        self.instance_id = os.getenv("INSTANCE_ID", "polygon-live-collector-1")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

        # Load messaging configs from environment variables
        self._load_env_configs()

    def _load_env_configs(self):
        """Load NATS and Kafka configs from environment variables"""
        logger.info("📡 Loading configuration from environment variables...")

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

    def _load_config(self) -> Dict:
        """Load YAML configuration"""
        config_file = Path(self.config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(config_file, 'r') as f:
            return yaml.safe_load(f)

    @property
    def websocket_trading_pairs(self) -> List[PairConfig]:
        """Get WebSocket trading pairs"""
        pairs = []
        for pair in self._config.get('websocket_trading_pairs', []):
            pairs.append(PairConfig(
                symbol=pair['symbol'],
                polygon_symbol=pair['polygon_symbol'],
                description=pair['description'],
                priority=pair['priority'],
                volatility=pair.get('volatility')
            ))
        return pairs

    @property
    def websocket_analysis_pairs(self) -> List[PairConfig]:
        """Get WebSocket analysis pairs"""
        pairs = []
        for pair in self._config.get('websocket_analysis_pairs', []):
            pairs.append(PairConfig(
                symbol=pair['symbol'],
                polygon_symbol=pair['polygon_symbol'],
                description=pair['description'],
                priority=pair['priority'],
                use_case=pair.get('use_case')
            ))
        return pairs

    @property
    def rest_confirmation_pairs(self) -> List[PairConfig]:
        """Get REST confirmation pairs"""
        pairs = []
        for pair in self._config.get('rest_confirmation_pairs', []):
            pairs.append(PairConfig(
                symbol=pair['symbol'],
                polygon_symbol=pair['polygon_symbol'],
                description=pair['description'],
                priority=pair.get('priority', 5),
                use_case=pair.get('use_case'),
                poll_interval=pair.get('poll_interval', 180)
            ))
        return pairs

    @property
    def all_websocket_pairs(self) -> List[PairConfig]:
        """Get all WebSocket pairs (trading + analysis)"""
        return self.websocket_trading_pairs + self.websocket_analysis_pairs

    @property
    def websocket_config(self) -> Dict:
        """Get WebSocket configuration"""
        return self._config.get('websocket_config', {})

    @property
    def rest_config(self) -> Dict:
        """Get REST API configuration"""
        return self._config.get('rest_config', {})

    @property
    def nats_config(self) -> Dict:
        """
        Get NATS configuration from environment variables

        Priority: 1. Environment variables, 2. YAML config
        """
        yaml_nats = self._config.get('nats_config', {})

        if len(self._nats_cluster_urls) > 1:
            # Cluster mode
            return {
                'url': ','.join(self._nats_cluster_urls),
                'max_reconnect_attempts': yaml_nats.get('max_reconnect_attempts', -1),
                'reconnect_time_wait': yaml_nats.get('reconnect_time_wait', 2)
            }
        else:
            # Single server
            return {
                'url': self._nats_cluster_urls[0],
                'max_reconnect_attempts': yaml_nats.get('max_reconnect_attempts', -1),
                'reconnect_time_wait': yaml_nats.get('reconnect_time_wait', 2)
            }

    @property
    def kafka_config(self) -> Dict:
        """
        Get Kafka configuration from environment variables

        Priority: 1. Environment variables, 2. YAML config
        """
        yaml_kafka = self._config.get('kafka_config', {})

        return {
            'brokers': self._kafka_brokers,
            'client_id': yaml_kafka.get('client_id', 'polygon-live-collector'),
            'group_id': yaml_kafka.get('group_id', 'polygon-collectors')
        }

    @property
    def monitoring_config(self) -> Dict:
        """Get monitoring configuration"""
        return self._config.get('monitoring', {})

    @property
    def timescaledb_config(self) -> Dict:
        """
        Get TimescaleDB configuration
        Priority: 1. Environment variables, 2. YAML config
        """
        yaml_config = self._config.get('timescaledb_config', {})

        return {
            'host': os.getenv('TIMESCALEDB_HOST', yaml_config.get('host', 'suho-timescaledb')),
            'port': int(os.getenv('TIMESCALEDB_PORT', yaml_config.get('port', 5432))),
            'database': os.getenv('TIMESCALEDB_DATABASE', yaml_config.get('database', 'suho_trading')),
            'user': os.getenv('TIMESCALEDB_USER', yaml_config.get('user', 'suho_service')),
            'password': os.getenv('TIMESCALEDB_PASSWORD', yaml_config.get('password', '')),
            'tenant_id': os.getenv('TENANT_ID', yaml_config.get('tenant_id', 'default_tenant')),
            'pool_min_size': yaml_config.get('pool_min_size', 2),
            'pool_max_size': yaml_config.get('pool_max_size', 10),
            'batch_size': yaml_config.get('batch_size', 100),
            'batch_timeout': yaml_config.get('batch_timeout', 5.0)
        }

    def get_websocket_subscriptions(self) -> List[str]:
        """
        Generate WebSocket subscription list
        Format: CA.C:EURUSD (Quotes for EUR/USD)
        """
        subscriptions = []
        prefix = self.websocket_config.get('subscription_prefix', 'CA')

        for pair in self.all_websocket_pairs:
            # Polygon uses format: CA.C:EURUSD
            subscription = f"{prefix}.{pair.polygon_symbol}"
            subscriptions.append(subscription)

        return subscriptions

    @property
    def aggregate_config(self) -> Dict:
        """Get aggregate configuration"""
        return self._config.get('aggregate_config', {})

    def get_aggregate_subscriptions(self) -> List[str]:
        """
        Generate aggregate WebSocket subscription list
        Format: CAS.C:EURUSD (Aggregates per second for EUR/USD)
        """
        agg_config = self.aggregate_config

        if not agg_config.get('enabled', False):
            return []

        subscriptions = []
        prefix = agg_config.get('websocket', {}).get('subscription_prefix', 'CAS')
        pairs = agg_config.get('websocket', {}).get('pairs', [])

        for pair_symbol in pairs:
            # Polygon uses format: CAS.C:EURUSD
            subscription = f"{prefix}.{pair_symbol}"
            subscriptions.append(subscription)

        return subscriptions
