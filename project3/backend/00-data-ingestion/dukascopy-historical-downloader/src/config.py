"""
Configuration loader for Dukascopy Historical Downloader
Fetches NATS config from Central Hub
"""
import os
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional
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
    """Trading pair configuration"""
    symbol: str  # Standard format: EUR/USD
    dukascopy_symbol: str  # Dukascopy format: EURUSD
    priority: int
    description: str = ""


class Config:
    """
    Configuration manager for Dukascopy downloader

    Priority:
    1. Central Hub (NATS config)
    2. YAML config (pairs, download settings)
    3. Environment variables
    """

    def __init__(self, config_path: str = "/app/config/pairs.yaml"):
        self.config_path = config_path
        self._config = self._load_config()

        # Environment variables
        self.instance_id = os.getenv("INSTANCE_ID", "dukascopy-historical-1")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

        # Central Hub client (will be initialized async)
        self.central_hub: Optional[CentralHubClient] = None
        self._nats_config_from_hub: Optional[Dict] = None

    async def fetch_nats_config_from_central_hub(self):
        """
        Fetch NATS configuration from Central Hub
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

            logger.info("📡 Fetching NATS config from Central Hub...")

            # Fetch NATS config
            self._nats_config_from_hub = await self.central_hub.get_messaging_config('nats')

            # Log cluster info
            conn = self._nats_config_from_hub['connection']
            cluster_urls = conn.get('cluster_urls')
            if cluster_urls:
                logger.info(f"✅ NATS config loaded from Central Hub: {len(cluster_urls)} nodes")
            else:
                logger.info(f"✅ NATS config loaded from Central Hub: {conn['host']}:{conn['port']}")

        except Exception as e:
            logger.warning(f"⚠️  Failed to fetch NATS config from Central Hub: {e}")
            logger.warning("⚠️  Falling back to YAML configuration")

    def _load_config(self) -> Dict:
        """Load YAML configuration"""
        config_file = Path(self.config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(config_file, 'r') as f:
            return yaml.safe_load(f)

    @property
    def trading_pairs(self) -> List[PairConfig]:
        """Get trading pairs configuration"""
        pairs = []
        for pair in self._config.get('trading_pairs', []):
            pairs.append(PairConfig(
                symbol=pair['symbol'],
                dukascopy_symbol=pair['dukascopy_symbol'],
                priority=pair.get('priority', 5),
                description=pair.get('description', '')
            ))
        return pairs

    @property
    def download_config(self) -> Dict:
        """Get download configuration"""
        return self._config.get('download', {})

    @property
    def aggregation_config(self) -> Dict:
        """Get aggregation configuration"""
        return self._config.get('aggregation', {})

    @property
    def schedule_config(self) -> Dict:
        """Get schedule configuration"""
        return self._config.get('schedule', {})

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
                    'reconnect_time_wait': 2,
                    'ping_interval': 120
                }
            else:
                # Fallback to single host/port (legacy mode)
                return {
                    'url': f"nats://{conn['host']}:{conn['port']}",
                    'max_reconnect_attempts': -1,
                    'reconnect_time_wait': 2,
                    'ping_interval': 120
                }

        # Fallback to YAML config
        return self._config.get('nats_config', {})

    @property
    def clickhouse_config(self) -> Dict:
        """
        Get ClickHouse configuration (for gap detection)
        Uses ticks table (ClickHouse tick table)
        """
        yaml_config = self._config.get('clickhouse_config', {})

        return {
            'host': os.getenv('CLICKHOUSE_HOST', yaml_config.get('host', 'suho-clickhouse')),
            'port': int(os.getenv('CLICKHOUSE_PORT', yaml_config.get('port', 9000))),
            'user': os.getenv('CLICKHOUSE_USER', yaml_config.get('user', 'suho_analytics')),
            'password': os.getenv('CLICKHOUSE_PASSWORD', yaml_config.get('password', '')),
            'database': yaml_config.get('database', 'suho_analytics'),
            'table': yaml_config.get('table', 'ticks')  # ClickHouse uses 'ticks' table name
        }
