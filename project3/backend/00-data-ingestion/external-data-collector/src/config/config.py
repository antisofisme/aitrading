"""
Configuration loader for External Data Collector (Economic Calendar)
Refactored to use environment variables (Central Hub v2.0 pattern)
"""
import os
import re
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass

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
        self._config = self._load_config()

        # Environment variables
        self.instance_id = os.getenv("INSTANCE_ID", "external-data-collector-1")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

        # API Keys from environment
        # Temporary disable Z.ai to test regex parser
        self.zai_api_key = ""  # os.getenv("ZAI_API_KEY", "")

        # Load messaging and database configs from environment variables
        self._load_env_configs()

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

    def _load_config(self) -> Dict:
        """Load YAML configuration with environment variable substitution"""
        config_file = Path(self.config_path)

        # If config doesn't exist, return default
        if not config_file.exists():
            return self._default_config()

        with open(config_file, 'r') as f:
            # Read YAML and substitute environment variables
            yaml_content = f.read()
            # Substitute ${VAR_NAME:-default} patterns with env var values
            yaml_content = self._substitute_env_vars(yaml_content)
            return yaml.safe_load(yaml_content)

    def _default_config(self) -> Dict:
        """Default configuration if YAML not found"""
        return {
            'scrapers': {
                'mql5_economic_calendar': {
                    'enabled': True,
                    'source': 'mql5.com',
                    'priority': 1,
                    'scrape_interval': 3600,  # 1 hour
                    'metadata': {
                        'data_type': 'economic_calendar',
                        'update_mode': 'incremental'
                    }
                }
            },
            'storage': {
                'type': 'json',  # json or postgresql
                'json_path': '/app/data',
                'postgresql': {
                    'host': os.getenv('DB_HOST', 'localhost'),
                    'port': int(os.getenv('DB_PORT', '5432')),
                    'database': os.getenv('DB_NAME', 'aitrading'),
                    'user': os.getenv('DB_USER', 'postgres'),
                    'password': os.getenv('DB_PASSWORD', '')
                }
            },
            'messaging': {
                'nats': {
                    'enabled': False,
                    'host': 'suho-nats',
                    'port': 4222
                },
                'kafka': {
                    'enabled': False,
                    'bootstrap_servers': 'suho-kafka:9092'
                }
            },
            'backfill': {
                'enabled': False,
                'months_back': 12,
                'batch_days': 30
            },
            'monitoring': {
                'metrics_enabled': True,
                'health_check_port': 8080
            }
        }

    @property
    def scrapers(self) -> List[ScraperConfig]:
        """Get enabled scrapers"""
        scrapers = []
        for name, config in self._config.get('scrapers', {}).items():
            if config.get('enabled', True):
                scrapers.append(ScraperConfig(
                    source=config.get('source', name),
                    enabled=True,
                    priority=config.get('priority', 5),
                    scrape_interval=config.get('scrape_interval', 3600),
                    metadata=config.get('metadata', {}),
                    api_key=config.get('api_key', ''),
                    indicators=config.get('indicators', []),
                    coins=config.get('coins', []),
                    symbols=config.get('symbols', []),
                    sessions=config.get('sessions', {})
                ))
        return sorted(scrapers, key=lambda x: x.priority)

    @property
    def storage_config(self) -> Dict:
        """Get storage configuration"""
        return self._config.get('storage', self._default_config()['storage'])

    @property
    def messaging_config(self) -> Dict:
        """Get messaging configuration"""
        return self._config.get('messaging', {})

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
        """Get backfill configuration"""
        return self._config.get('backfill', {})

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
