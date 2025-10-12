"""
Configuration loader for Polygon.io Live Collector
Enhanced to fetch NATS/Kafka config from Central Hub
"""
import os
import yaml
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Import Central Hub SDK
try:
    from central_hub_sdk import CentralHubClient
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    logging.warning("Central Hub SDK not available, using fallback config")

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

        # Central Hub client (will be initialized async)
        self.central_hub: Optional[CentralHubClient] = None
        self._nats_config_from_hub: Optional[Dict] = None
        self._kafka_config_from_hub: Optional[Dict] = None

    async def fetch_messaging_configs_from_central_hub(self):
        """
        Fetch NATS and Kafka configurations from Central Hub
        This method should be called async after instantiation
        """
        if not SDK_AVAILABLE:
            logger.warning("⚠️  Central Hub SDK not available, using YAML config")
            return

        try:
            # Note: central_hub is already initialized in main.py
            if not self.central_hub:
                logger.warning("⚠️  Central Hub client not initialized")
                return

            logger.info("📡 Fetching messaging configs from Central Hub...")

            # Fetch NATS config
            self._nats_config_from_hub = await self.central_hub.get_messaging_config('nats')
            logger.info(f"✅ NATS config loaded from Central Hub: {self._nats_config_from_hub['connection']['host']}:{self._nats_config_from_hub['connection']['port']}")

            # Fetch Kafka config
            self._kafka_config_from_hub = await self.central_hub.get_messaging_config('kafka')
            logger.info(f"✅ Kafka config loaded from Central Hub: {self._kafka_config_from_hub['connection']['bootstrap_servers']}")

        except Exception as e:
            logger.warning(f"⚠️  Failed to fetch messaging configs from Central Hub: {e}")
            logger.warning("⚠️  Falling back to YAML configuration")

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
        Get NATS configuration
        Priority: 1. Central Hub, 2. YAML config
        """
        # If config fetched from Central Hub, use it
        if self._nats_config_from_hub:
            conn = self._nats_config_from_hub['connection']

            # Use cluster_urls if available (preferred for HA)
            cluster_urls = conn.get('cluster_urls')
            if cluster_urls:
                # Return comma-separated cluster URLs for high availability
                return {
                    'url': ','.join(cluster_urls),
                    'max_reconnect_attempts': -1,
                    'reconnect_time_wait': 2
                }
            else:
                # Fallback to single host/port (legacy mode)
                return {
                    'url': f"nats://{conn['host']}:{conn['port']}",
                    'max_reconnect_attempts': -1,
                    'reconnect_time_wait': 2
                }

        # Fallback to YAML config
        return self._config.get('nats_config', {})

    @property
    def kafka_config(self) -> Dict:
        """
        Get Kafka configuration
        Priority: 1. Central Hub, 2. YAML config
        """
        # If config fetched from Central Hub, use it
        if self._kafka_config_from_hub:
            conn = self._kafka_config_from_hub['connection']
            brokers = conn['bootstrap_servers']
            return {
                'brokers': brokers if isinstance(brokers, list) else [brokers],
                'client_id': 'polygon-live-collector',
                'group_id': 'polygon-collectors'
            }

        # Fallback to YAML config
        return self._config.get('kafka_config', {})

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
