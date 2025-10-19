"""
Configuration loader for Polygon.io Historical Downloader
Centralized config via Central Hub (ConfigClient pattern)
"""
import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

# Add shared components to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from shared.components.config import ConfigClient

logger = logging.getLogger(__name__)

@dataclass
class PairConfig:
    symbol: str
    polygon_symbol: str
    priority: int

class Config:
    def __init__(self):
        # Environment variables (SECRETS ONLY!)
        self.polygon_api_key = os.getenv("POLYGON_API_KEY")
        if not self.polygon_api_key:
            raise ValueError("POLYGON_API_KEY environment variable not set")

        self.instance_id = os.getenv("INSTANCE_ID", "polygon-historical-downloader-1")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

        # ConfigClient for operational settings from Central Hub
        self._config_client: Optional[ConfigClient] = None
        self._operational_config: Dict = {}

        # Safe defaults (fallback if Central Hub unavailable)
        self._safe_defaults = {
            "operational": {
                "symbols": ["EURUSD", "XAUUSD"],
                "timeframes": ["5m", "15m", "30m", "1h", "4h", "1d", "1w"],
                "check_period_days": 7,
                "completeness_threshold_intraday": 1.0,
                "completeness_threshold_daily": 0.8,
                "batch_size": 150,
                "schedule": {
                    "hourly_check": "0 * * * *",
                    "daily_check": "0 1 * * *",
                    "weekly_check": "0 2 * * 0"
                },
                "gap_detection": {
                    "enabled": True,
                    "max_gap_days": 7
                },
                "download": {
                    "start_date": "today-7days",
                    "end_date": "today",
                    "rate_limit_per_sec": 5
                }
            }
        }

        # Load infrastructure configs from environment variables
        self._load_env_configs()

        logger.info("=" * 80)
        logger.info("POLYGON HISTORICAL DOWNLOADER - CENTRALIZED CONFIG")
        logger.info("=" * 80)
        logger.info(f"Instance ID: {self.instance_id}")
        logger.info(f"Config Mode: Central Hub + Environment Variables")
        logger.info("=" * 80)

    async def init_async(self):
        """Initialize ConfigClient connection to Central Hub"""
        logger.info("📡 Initializing ConfigClient for polygon-historical-downloader...")

        self._config_client = ConfigClient(
            service_name="polygon-historical-downloader",
            safe_defaults=self._safe_defaults
        )

        try:
            await self._config_client.init_async()
            self._operational_config = await self._config_client.get_config()

            logger.info("✅ ConfigClient initialized successfully")
            logger.info(f"✅ Loaded config from Central Hub:")
            logger.info(f"   - Symbols: {self._operational_config['operational']['symbols']}")
            logger.info(f"   - Timeframes: {self._operational_config['operational']['timeframes']}")
            logger.info(f"   - Check period: {self._operational_config['operational']['check_period_days']} days")
            logger.info(f"   - Batch size: {self._operational_config['operational']['batch_size']}")
        except Exception as e:
            logger.warning(f"⚠️  Failed to connect to Central Hub: {e}")
            logger.warning(f"⚠️  Using safe defaults")
            self._operational_config = self._safe_defaults

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

    @property
    def pairs(self) -> List[PairConfig]:
        """Get all pairs to download from Central Hub config"""
        pairs = []
        symbols = self._operational_config.get('operational', {}).get('symbols', ['EURUSD', 'XAUUSD'])

        # Map symbols to polygon symbols with priority
        symbol_mapping = {
            'EURUSD': ('C:EURUSD', 1),
            'XAUUSD': ('C:XAUUSD', 1),
            'GBPUSD': ('C:GBPUSD', 2),
            'USDJPY': ('C:USDJPY', 2),
            'AUDUSD': ('C:AUDUSD', 3),
            'USDCAD': ('C:USDCAD', 3),
        }

        for symbol in symbols:
            if symbol in symbol_mapping:
                polygon_symbol, priority = symbol_mapping[symbol]
                pairs.append(PairConfig(
                    symbol=symbol,
                    polygon_symbol=polygon_symbol,
                    priority=priority
                ))
            else:
                logger.warning(f"Unknown symbol {symbol}, skipping")

        return pairs

    @property
    def download_config(self) -> Dict:
        """Get download configuration from Central Hub"""
        download_cfg = self._operational_config.get('operational', {}).get('download', {})

        # Parse dates - ENV takes priority over Central Hub config
        start_date = os.getenv('HISTORICAL_START_DATE', download_cfg.get('start_date', 'today-7days'))
        end_date = os.getenv('HISTORICAL_END_DATE', download_cfg.get('end_date', 'today'))

        # Handle "today-Xdays" format
        if start_date.startswith('today'):
            days_back = 7  # default
            if '-' in start_date and 'days' in start_date:
                days_back = int(start_date.replace('today-', '').replace('days', ''))
            start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

        if end_date == 'today' or end_date == 'now':
            end_date = datetime.now().strftime('%Y-%m-%d')

        return {
            'start_date': start_date,
            'end_date': end_date,
            'batch_size': self._operational_config.get('operational', {}).get('batch_size', 150),
            'rate_limit_per_sec': download_cfg.get('rate_limit_per_sec', 5)
        }

    @property
    def gap_detection_config(self) -> Dict:
        """Get gap detection configuration from Central Hub"""
        return self._operational_config.get('operational', {}).get('gap_detection', {
            'enabled': True,
            'max_gap_days': 7
        })

    @property
    def schedules(self) -> Dict:
        """Get schedule configuration from Central Hub"""
        return self._operational_config.get('operational', {}).get('schedule', {
            'hourly_check': "0 * * * *",
            'daily_check': "0 1 * * *",
            'weekly_check': "0 2 * * 0"
        })

    @property
    def completeness_thresholds(self) -> Dict:
        """Get completeness thresholds from Central Hub"""
        return {
            'intraday': self._operational_config.get('operational', {}).get('completeness_threshold_intraday', 1.0),
            'daily': self._operational_config.get('operational', {}).get('completeness_threshold_daily', 0.8)
        }

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

        Note: Defaults to 5m (smallest granularity in ClickHouse live_aggregates)
        """
        download_cfg = self.download_config
        granularity = download_cfg.get('granularity', {})

        if pair.priority <= 2:
            # Trading pairs: 5-minute bars (ClickHouse default)
            cfg = granularity.get('trading_pairs', {})
        elif pair.priority == 3:
            # Analysis pairs: 5-minute bars
            cfg = granularity.get('analysis_pairs', {})
        else:
            # Confirmation pairs: 5-minute bars
            cfg = granularity.get('confirmation_pairs', {})

        # Default to '5m' which is the smallest timeframe in ClickHouse live_aggregates
        # ClickHouse schema only supports: 5m, 15m, 30m, 1h, 4h, 1d, 1w
        timeframe = cfg.get('timeframe', 'minute')  # Keep 'minute' for Polygon API compatibility
        multiplier = cfg.get('multiplier', 5)  # Changed from 1 to 5 (5-minute default)

        return timeframe, multiplier
