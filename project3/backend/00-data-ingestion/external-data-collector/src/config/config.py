"""
Configuration loader for External Data Collector (Economic Calendar)
Centralized config via Central Hub (ConfigClient pattern)
"""
import os
import re
import yaml
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Add shared components to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from shared.components.config import ConfigClient

logger = logging.getLogger(__name__)


@dataclass
class ScraperConfig:
    """Economic calendar scraper configuration"""
    source: str
    enabled: bool
    priority: int
    scrape_interval: int  # seconds
    metadata: Dict[str, Any] = None
    api_key: str = ""  # Optional API key

    def __post_init__(self):
        # Initialize optional fields with empty defaults if None
        if self.indicators is None:
            self.indicators = []
        if self.coins is None:
            self.coins = []
        if self.symbols is None:
            self.symbols = []
        if self.sessions is None:
            self.sessions = {}

    indicators: List[str] = None  # For FRED
    coins: List[str] = None  # For CoinGecko
    symbols: List[str] = None  # For Yahoo Finance
    sessions: Dict[str, Any] = None  # For Market Sessions


class Config:
    """Configuration for External Data Collector"""

    def __init__(self, config_path: str = "/app/config/scrapers.yaml"):
        self.config_path = config_path

        # Environment variables (SECRETS ONLY!)
        self.instance_id = os.getenv("INSTANCE_ID", "external-data-collector-1")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

        # API Keys from environment (SECRETS!)
        self.zai_api_key = os.getenv("ZAI_API_KEY", "")
        self.fred_api_key = os.getenv("FRED_API_KEY", "")
        self.economic_calendar_api_key = os.getenv("ECONOMIC_CALENDAR_API_KEY", "")

        # ConfigClient for operational settings from Central Hub
        self._config_client: Optional[ConfigClient] = None
        self._operational_config: Dict = {}

        # Safe defaults (fallback if Central Hub unavailable)
        self._safe_defaults = self._default_config()

        # Legacy YAML config (fallback only)
        self._yaml_config = self._load_yaml_config()

        # Load infrastructure configs from environment variables
        self._load_env_configs()

        logger.info("=" * 80)
        logger.info("EXTERNAL DATA COLLECTOR - CENTRALIZED CONFIG")
        logger.info("=" * 80)
        logger.info(f"Instance ID: {self.instance_id}")
        logger.info(f"Config Mode: Central Hub + Environment Variables")
        logger.info("=" * 80)

    def _load_env_configs(self):
        """Load NATS and Kafka configs from environment variables"""
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

    def _substitute_env_vars(self, content: str) -> str:
        """
        Substitute environment variables in content
        Supports both ${VAR} and ${VAR:-default} patterns
        """
        # Pattern: ${VAR_NAME:-default_value} or ${VAR_NAME}
        pattern = r'\$\{([^}:]+)(?::-([^}]*))?\}'

        def replacer(match):
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) is not None else ''
            return os.getenv(var_name, default_value)

        return re.sub(pattern, replacer, content)

    async def init_async(self):
        """Initialize ConfigClient connection to Central Hub"""
        logger.info("📡 Initializing ConfigClient for external-data-collector...")

        self._config_client = ConfigClient(
            service_name="external-data-collector",
            safe_defaults=self._safe_defaults
        )

        try:
            await self._config_client.init_async()
            self._operational_config = await self._config_client.get_config()

            logger.info("✅ ConfigClient initialized successfully")
            logger.info(f"✅ Loaded config from Central Hub:")
            logger.info(f"   - Economic Calendar: {self._operational_config['operational'].get('economic_calendar', {}).get('enabled', False)}")
            logger.info(f"   - FRED Indicators: {len(self._operational_config['operational'].get('fred_indicators', {}).get('indicators', []))}")
            logger.info(f"   - Commodity Prices: {len(self._operational_config['operational'].get('commodity_prices', {}).get('symbols', []))}")
        except Exception as e:
            logger.warning(f"⚠️  Failed to connect to Central Hub: {e}")
            logger.warning(f"⚠️  Using safe defaults")
            self._operational_config = self._safe_defaults

    def _load_yaml_config(self) -> Dict:
        """Load YAML configuration with environment variable substitution (fallback only)"""
        config_file = Path(self.config_path)

        # If config doesn't exist, return empty
        if not config_file.exists():
            return {}

        with open(config_file, 'r') as f:
            # Read YAML and substitute environment variables
            yaml_content = f.read()
            # Substitute ${VAR_NAME:-default} patterns with env var values
            yaml_content = self._substitute_env_vars(yaml_content)
            return yaml.safe_load(yaml_content)

    def _default_config(self) -> Dict:
        """
        Safe defaults (Central Hub structure)

        Only 3 external sources as per table_database_input.md:
        1. Economic Calendar (MQL5) ⭐⭐⭐⭐⭐
        2. FRED Indicators ⭐⭐⭐⭐⭐
        3. Commodity Prices ⭐⭐⭐⭐

        ARCHIVED (disabled):
        - Crypto Sentiment (not relevant for forex/gold)
        - Fear & Greed Index (subjective, low consistency)
        - Market Sessions (moved to calculated features)
        """
        return {
            'operational': {
                'economic_calendar': {
                    'enabled': True,
                    'source': 'mql5.com',
                    'priority': 1,
                    'scrape_interval': 3600,  # 1 hour
                    'lookforward_days': 30,
                    'impact_levels': ['high', 'medium'],
                    'metadata': {
                        'data_type': 'economic_calendar',
                        'update_mode': 'incremental',
                        'parser': 'regex'
                    }
                },
                'fred_indicators': {
                    'enabled': True,
                    'source': 'fred.stlouisfed.org',
                    'priority': 2,
                    'scrape_interval': 14400,  # 4 hours
                    'indicators': ['GDP', 'UNRATE', 'CPIAUCSL', 'DFF', 'DGS10', 'DEXUSEU', 'DEXJPUS'],
                    'metadata': {
                        'data_type': 'fred_economic'
                    }
                },
                'commodity_prices': {
                    'enabled': True,
                    'source': 'finance.yahoo.com',
                    'priority': 5,
                    'scrape_interval': 1800,  # 30 minutes
                    'cache_ttl_minutes': 15,
                    'symbols': ['GC=F', 'CL=F', 'SI=F', 'HG=F', 'NG=F'],
                    'metadata': {
                        'data_type': 'commodity_prices'
                    }
                },
                'crypto_sentiment': {
                    'enabled': False,
                    'reason': 'ARCHIVED - Not relevant for forex/gold pairs'
                },
                'fear_greed_index': {
                    'enabled': False,
                    'reason': 'ARCHIVED - Subjective, low consistency'
                },
                'market_sessions': {
                    'enabled': False,
                    'reason': 'MOVED TO CALCULATED FEATURES - Pure calculation from UTC time'
                },
                'storage': {
                    'type': 'json',
                    'json_path': '/app/data'
                },
                'messaging': {
                    'nats_enabled': False,
                    'kafka_enabled': True
                },
                'backfill': {
                    'enabled': False,
                    'months_back': 1,
                    'batch_days': 7
                }
            }
        }

    @property
    def scrapers(self) -> List[ScraperConfig]:
        """Get enabled scrapers from Central Hub config"""
        scrapers = []
        operational = self._operational_config.get('operational', {})

        # Map Central Hub config to ScraperConfig objects
        scraper_mappings = {
            'economic_calendar': ('mql5.com', 'mql5_economic_calendar'),
            'fred_indicators': ('fred.stlouisfed.org', 'fred_economic'),
            'commodity_prices': ('finance.yahoo.com', 'yahoo_finance_commodity'),
            'crypto_sentiment': ('coingecko.com', 'coingecko_sentiment'),
            'fear_greed_index': ('alternative.me', 'fear_greed_index'),
            'market_sessions': ('market_sessions', 'market_sessions')
        }

        for config_key, (source, name) in scraper_mappings.items():
            config = operational.get(config_key, {})

            if config.get('enabled', False):
                # Build ScraperConfig
                scraper = ScraperConfig(
                    source=config.get('source', source),
                    enabled=True,
                    priority=config.get('priority', 5),
                    scrape_interval=config.get('scrape_interval', 3600),
                    metadata=config.get('metadata', {}),
                    api_key=self.fred_api_key if config_key == 'fred_indicators' else '',
                    indicators=config.get('indicators', []),
                    coins=config.get('coins', []),
                    symbols=config.get('symbols', []),
                    sessions=config.get('sessions', {})
                )
                scrapers.append(scraper)

        return sorted(scrapers, key=lambda x: x.priority)

    @property
    def storage_config(self) -> Dict:
        """Get storage configuration from Central Hub"""
        storage = self._operational_config.get('operational', {}).get('storage', {})

        # Merge with defaults
        return {
            'type': storage.get('type', 'json'),
            'json_path': storage.get('json_path', '/app/data'),
            'postgresql': {
                'host': os.getenv('DB_HOST', 'suho-postgresql'),
                'port': int(os.getenv('DB_PORT', '5432')),
                'database': os.getenv('DB_NAME', 'suho_trading'),
                'user': os.getenv('DB_USER', 'suho_admin'),
                'password': os.getenv('DB_PASSWORD', 'suho_secure_2024')
            }
        }

    @property
    def messaging_config(self) -> Dict:
        """Get messaging configuration from Central Hub"""
        messaging = self._operational_config.get('operational', {}).get('messaging', {})

        return {
            'nats': {
                'enabled': messaging.get('nats_enabled', False)
            },
            'kafka': {
                'enabled': messaging.get('kafka_enabled', True)
            }
        }

    @property
    def nats_config(self) -> Dict:
        """
        Get NATS configuration from environment variables

        Returns:
            Dict with 'url' and connection parameters
        """
        yaml_nats = self.messaging_config.get('nats', {})

        if len(self._nats_cluster_urls) > 1:
            # Cluster mode
            return {
                'url': ','.join(self._nats_cluster_urls),
                'enabled': yaml_nats.get('enabled', False),
                'max_reconnect_attempts': -1,
                'reconnect_time_wait': 2
            }
        else:
            # Single server
            return {
                'url': self._nats_cluster_urls[0],
                'enabled': yaml_nats.get('enabled', False),
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
        yaml_kafka = self.messaging_config.get('kafka', {})

        return {
            'brokers': self._kafka_brokers,
            'enabled': yaml_kafka.get('enabled', False),
            'client_id': 'external-data-collector',
            'group_id': 'external-collectors'
        }

    @property
    def backfill_config(self) -> Dict:
        """Get backfill configuration from Central Hub"""
        return self._operational_config.get('operational', {}).get('backfill', {
            'enabled': False,
            'months_back': 1,
            'batch_days': 7
        })

    @property
    def monitoring_config(self) -> Dict:
        """Get monitoring configuration"""
        return self._config.get('monitoring', {})

    @property
    def use_database(self) -> bool:
        """Check if database storage is enabled"""
        return self.storage_config.get('type') == 'postgresql'

    def get_db_connection_string(self) -> str:
        """Get PostgreSQL connection string"""
        if not self.use_database:
            return None

        pg = self.storage_config['postgresql']
        return f"postgresql://{pg['user']}:{pg['password']}@{pg['host']}:{pg['port']}/{pg['database']}"
