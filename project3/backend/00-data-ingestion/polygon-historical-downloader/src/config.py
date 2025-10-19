"""
Configuration loader for Polygon.io Historical Downloader
Refactored to use environment variables (Central Hub v2.0 pattern)
"""
import os
import yaml
import logging
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class PairConfig:
    symbol: str
    polygon_symbol: str
    priority: int

class Config:
    def __init__(self, config_path: str = "/app/config/schedule.yaml"):
        self.config_path = config_path
        self._config = self._load_config()

        # Environment variables
        self.polygon_api_key = os.getenv("POLYGON_API_KEY")
        if not self.polygon_api_key:
            raise ValueError("POLYGON_API_KEY environment variable not set")

        self.instance_id = os.getenv("INSTANCE_ID", "polygon-historical-downloader-1")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

        # Load messaging and database configs from environment variables
        self._load_env_configs()

    def _load_env_configs(self):
        """Load NATS, Kafka, and ClickHouse configs from environment variables"""
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

        # Kafka config
        kafka_brokers = os.getenv('KAFKA_BROKERS', 'suho-kafka:9092')
        self._kafka_brokers = [b.strip() for b in kafka_brokers.split(',')]
        logger.info(f"✅ Kafka brokers: {self._kafka_brokers}")

        # ClickHouse config
        self._clickhouse_host = os.getenv('CLICKHOUSE_HOST', 'suho-clickhouse')
        self._clickhouse_port = int(os.getenv('CLICKHOUSE_PORT', '9000'))
        self._clickhouse_user = os.getenv('CLICKHOUSE_USER', 'suho_analytics')
        self._clickhouse_password = os.getenv('CLICKHOUSE_PASSWORD', 'clickhouse_secure_2024')
        self._clickhouse_database = os.getenv('CLICKHOUSE_DATABASE', 'suho_analytics')
        logger.info(f"✅ ClickHouse: {self._clickhouse_host}:{self._clickhouse_port}/{self._clickhouse_database} (user: {self._clickhouse_user})")

    def _load_config(self) -> Dict:
        """Load YAML configuration"""
        config_file = Path(self.config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(config_file, 'r') as f:
            return yaml.safe_load(f)

    @property
    def pairs(self) -> List[PairConfig]:
        """Get all pairs to download"""
        pairs = []
        for pair in self._config.get('pairs', []):
            pairs.append(PairConfig(
                symbol=pair['symbol'],
                polygon_symbol=pair['polygon_symbol'],
                priority=pair['priority']
            ))
        return pairs

    @property
    def download_config(self) -> Dict:
        """Get download configuration"""
        config = self._config.get('download', {})

        # Parse dates - ENV takes priority over YAML config
        start_date = os.getenv('HISTORICAL_START_DATE',
                               config.get('start_date', '2023-01-01'))
        end_date = os.getenv('HISTORICAL_END_DATE',
                             config.get('end_date', 'today'))

        if end_date == 'today' or end_date == 'now':
            end_date = datetime.now().strftime('%Y-%m-%d')

        config['start_date'] = start_date
        config['end_date'] = end_date

        return config

    @property
    def gap_detection_config(self) -> Dict:
        """Get gap detection configuration"""
        return self._config.get('gap_detection', {})

    @property
    def schedules(self) -> Dict:
        """Get schedule configuration"""
        return self._config.get('schedules', {})

    @property
    def monitoring_config(self) -> Dict:
        """Get monitoring configuration"""
        return self._config.get('monitoring', {})

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
                'reconnect_time_wait': 2
            }
        else:
            # Single server
            return {
                'url': self._nats_cluster_urls[0],
                'max_reconnect_attempts': -1,
                'reconnect_time_wait': 2
            }

    @property
    def kafka_config(self) -> Dict:
        """
        Get Kafka configuration from environment variables

        Returns:
            Dict with 'brokers' list
        """
        return {
            'brokers': self._kafka_brokers,
            'client_id': 'polygon-historical-downloader',
            'group_id': 'polygon-downloaders'
        }

    @property
    def clickhouse_config(self) -> Dict:
        """
        Get ClickHouse configuration from environment variables

        Returns:
            Dict with connection parameters
        """
        return {
            'host': self._clickhouse_host,
            'port': self._clickhouse_port,
            'user': self._clickhouse_user,
            'password': self._clickhouse_password,
            'database': self._clickhouse_database,
            'table': 'live_aggregates'  # Gap filling for live operational data
        }

    def get_timeframe_for_pair(self, pair: PairConfig) -> tuple:
        """
        Get timeframe and multiplier for a pair based on priority

        Returns: (timeframe, multiplier)
        """
        download_cfg = self.download_config
        granularity = download_cfg.get('granularity', {})

        if pair.priority <= 2:
            # Trading pairs: 1-minute bars
            cfg = granularity.get('trading_pairs', {})
        elif pair.priority == 3:
            # Analysis pairs: 1-minute bars
            cfg = granularity.get('analysis_pairs', {})
        else:
            # Confirmation pairs: 5-minute bars
            cfg = granularity.get('confirmation_pairs', {})

        timeframe = cfg.get('timeframe', 'minute')
        multiplier = cfg.get('multiplier', 1)

        return timeframe, multiplier
