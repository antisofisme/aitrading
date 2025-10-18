"""
Configuration loader for Dukascopy Historical Downloader
Refactored to use environment variables (Central Hub v2.0 pattern)
"""
import os
import yaml
import logging
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass

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

    Uses environment variables following Central Hub v2.0 pattern
    """

    def __init__(self, config_path: str = "/app/config/pairs.yaml"):
        self.config_path = config_path
        self._config = self._load_config()

        # Environment variables
        self.instance_id = os.getenv("INSTANCE_ID", "dukascopy-historical-1")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

        # Load messaging configs from environment variables
        self._load_env_configs()

    def _load_env_configs(self):
        """Load NATS configuration from environment variables"""
        logger.info("📡 Loading configuration from environment variables...")

        # NATS config - Use cluster by default (Central Hub v2.0 pattern)
        nats_url = os.getenv('NATS_URL', 'nats://nats-1:4222,nats://nats-2:4222,nats://nats-3:4222')
        if ',' in nats_url:
            # Cluster mode
            self._nats_cluster_urls = [url.strip() for url in nats_url.split(',')]
            logger.info(f"✅ NATS cluster: {len(self._nats_cluster_urls)} nodes")
        else:
            # Single server
            self._nats_cluster_urls = [nats_url]
            logger.info(f"✅ NATS single server: {nats_url}")

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
        Get NATS configuration from environment variables

        Returns:
            Dict with 'url' and connection parameters
        """
        if len(self._nats_cluster_urls) > 1:
            # Cluster mode
            return {
                'url': ','.join(self._nats_cluster_urls),
                'max_reconnect_attempts': -1,
                'reconnect_time_wait': 2,
                'ping_interval': 120
            }
        else:
            # Single server
            return {
                'url': self._nats_cluster_urls[0],
                'max_reconnect_attempts': -1,
                'reconnect_time_wait': 2,
                'ping_interval': 120
            }

    @property
    def clickhouse_config(self) -> Dict:
        """
        Get ClickHouse configuration (for gap detection)
        Uses historical_ticks table (ClickHouse tick table)
        """
        yaml_config = self._config.get('clickhouse_config', {})

        return {
            'host': os.getenv('CLICKHOUSE_HOST', yaml_config.get('host', 'suho-clickhouse')),
            'port': int(os.getenv('CLICKHOUSE_PORT', yaml_config.get('port', 9000))),
            'user': os.getenv('CLICKHOUSE_USER', yaml_config.get('user', 'suho_analytics')),
            'password': os.getenv('CLICKHOUSE_PASSWORD', yaml_config.get('password', '')),
            'database': yaml_config.get('database', 'suho_analytics'),
            'table': yaml_config.get('table', 'historical_ticks')  # ClickHouse historical ticks table
        }
