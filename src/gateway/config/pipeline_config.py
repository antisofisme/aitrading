"""
Trading Pipeline Configuration
Centralized configuration for high-performance trading data pipeline
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class Environment(Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class DatabaseConfig:
    """Database connection configuration"""
    host: str
    port: int
    database: str
    username: str
    password: str
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600


@dataclass
class RedisConfig:
    """Redis configuration"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    max_connections: int = 20
    socket_timeout: int = 5
    socket_connect_timeout: int = 5


@dataclass
class WebSocketConfig:
    """WebSocket server configuration"""
    host: str = "localhost"
    port: int = 8765
    ping_interval: int = 20
    ping_timeout: int = 10
    max_size: int = 1024 * 1024  # 1MB
    compression: Optional[str] = None
    max_connections: int = 100


@dataclass
class PerformanceConfig:
    """Performance tuning configuration"""
    max_latency_ms: float = 500.0
    min_throughput_tps: int = 18
    processing_workers: int = 4
    queue_size: int = 10000
    batch_size: int = 100
    flush_interval_ms: int = 100
    memory_limit_mb: int = 1024


@dataclass
class MonitoringConfig:
    """Monitoring and metrics configuration"""
    enable_prometheus: bool = True
    prometheus_port: int = 9090
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    metrics_retention_seconds: int = 3600
    alert_latency_threshold_ms: float = 300.0
    alert_throughput_threshold_tps: int = 15


class PipelineConfig:
    """Main pipeline configuration class"""

    def __init__(self, environment: Environment = Environment.DEVELOPMENT):
        self.environment = environment
        self._load_config()

    def _load_config(self):
        """Load configuration based on environment"""
        if self.environment == Environment.PRODUCTION:
            self._load_production_config()
        elif self.environment == Environment.STAGING:
            self._load_staging_config()
        elif self.environment == Environment.TESTING:
            self._load_testing_config()
        else:
            self._load_development_config()

    def _load_development_config(self):
        """Development environment configuration"""
        self.databases = {
            'clickhouse': DatabaseConfig(
                host=os.getenv('CLICKHOUSE_HOST', 'localhost'),
                port=int(os.getenv('CLICKHOUSE_PORT', 9000)),
                database=os.getenv('CLICKHOUSE_DB', 'trading_data_dev'),
                username=os.getenv('CLICKHOUSE_USER', 'default'),
                password=os.getenv('CLICKHOUSE_PASS', ''),
                pool_size=5
            ),
            'postgresql': DatabaseConfig(
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                port=int(os.getenv('POSTGRES_PORT', 5432)),
                database=os.getenv('POSTGRES_DB', 'trading_db_dev'),
                username=os.getenv('POSTGRES_USER', 'trading_user'),
                password=os.getenv('POSTGRES_PASS', 'trading_pass'),
                pool_size=5
            )
        }

        self.redis = RedisConfig(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=int(os.getenv('REDIS_DB', 0)),
            max_connections=10
        )

        self.websocket = WebSocketConfig(
            host='localhost',
            port=8765,
            max_connections=50
        )

        self.performance = PerformanceConfig(
            processing_workers=2,
            queue_size=5000,
            memory_limit_mb=512
        )

        self.monitoring = MonitoringConfig(
            log_level="DEBUG",
            enable_prometheus=True
        )

    def _load_testing_config(self):
        """Testing environment configuration"""
        self.databases = {
            'clickhouse': DatabaseConfig(
                host='localhost',
                port=9000,
                database='trading_data_test',
                username='default',
                password='',
                pool_size=2
            ),
            'postgresql': DatabaseConfig(
                host='localhost',
                port=5432,
                database='trading_db_test',
                username='test_user',
                password='test_pass',
                pool_size=2
            )
        }

        self.redis = RedisConfig(
            host='localhost',
            port=6379,
            db=1,  # Use different DB for testing
            max_connections=5
        )

        self.websocket = WebSocketConfig(
            host='localhost',
            port=8766,  # Different port for testing
            max_connections=10
        )

        self.performance = PerformanceConfig(
            processing_workers=1,
            queue_size=1000,
            memory_limit_mb=256
        )

        self.monitoring = MonitoringConfig(
            log_level="WARNING",
            enable_prometheus=False
        )

    def _load_staging_config(self):
        """Staging environment configuration"""
        self.databases = {
            'clickhouse': DatabaseConfig(
                host=os.getenv('CLICKHOUSE_HOST', 'staging-clickhouse'),
                port=int(os.getenv('CLICKHOUSE_PORT', 9000)),
                database=os.getenv('CLICKHOUSE_DB', 'trading_data_staging'),
                username=os.getenv('CLICKHOUSE_USER', 'staging_user'),
                password=os.getenv('CLICKHOUSE_PASS', ''),
                pool_size=10
            ),
            'postgresql': DatabaseConfig(
                host=os.getenv('POSTGRES_HOST', 'staging-postgres'),
                port=int(os.getenv('POSTGRES_PORT', 5432)),
                database=os.getenv('POSTGRES_DB', 'trading_db_staging'),
                username=os.getenv('POSTGRES_USER', 'staging_user'),
                password=os.getenv('POSTGRES_PASS', ''),
                pool_size=10
            )
        }

        self.redis = RedisConfig(
            host=os.getenv('REDIS_HOST', 'staging-redis'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            password=os.getenv('REDIS_PASS'),
            max_connections=15
        )

        self.websocket = WebSocketConfig(
            host='0.0.0.0',
            port=8765,
            max_connections=75
        )

        self.performance = PerformanceConfig(
            processing_workers=3,
            queue_size=7500,
            memory_limit_mb=768
        )

        self.monitoring = MonitoringConfig(
            log_level="INFO",
            enable_prometheus=True
        )

    def _load_production_config(self):
        """Production environment configuration"""
        self.databases = {
            'clickhouse': DatabaseConfig(
                host=os.getenv('CLICKHOUSE_HOST', 'prod-clickhouse'),
                port=int(os.getenv('CLICKHOUSE_PORT', 9000)),
                database=os.getenv('CLICKHOUSE_DB', 'trading_data'),
                username=os.getenv('CLICKHOUSE_USER'),
                password=os.getenv('CLICKHOUSE_PASS'),
                pool_size=20,
                max_overflow=30
            ),
            'postgresql': DatabaseConfig(
                host=os.getenv('POSTGRES_HOST', 'prod-postgres'),
                port=int(os.getenv('POSTGRES_PORT', 5432)),
                database=os.getenv('POSTGRES_DB', 'trading_db'),
                username=os.getenv('POSTGRES_USER'),
                password=os.getenv('POSTGRES_PASS'),
                pool_size=20,
                max_overflow=30
            )
        }

        self.redis = RedisConfig(
            host=os.getenv('REDIS_HOST', 'prod-redis'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            password=os.getenv('REDIS_PASS'),
            max_connections=50,
            socket_timeout=10
        )

        self.websocket = WebSocketConfig(
            host='0.0.0.0',
            port=8765,
            max_connections=200,
            ping_interval=30,
            ping_timeout=15
        )

        self.performance = PerformanceConfig(
            max_latency_ms=200.0,  # Stricter in production
            min_throughput_tps=50,  # Higher requirement
            processing_workers=8,
            queue_size=20000,
            memory_limit_mb=2048
        )

        self.monitoring = MonitoringConfig(
            log_level="INFO",
            enable_prometheus=True,
            alert_latency_threshold_ms=200.0,
            alert_throughput_threshold_tps=45
        )

    def get_database_url(self, db_name: str) -> str:
        """Get database connection URL"""
        db_config = self.databases.get(db_name)
        if not db_config:
            raise ValueError(f"Database {db_name} not configured")

        if db_name == 'postgresql':
            return (f"postgresql://{db_config.username}:{db_config.password}@"
                   f"{db_config.host}:{db_config.port}/{db_config.database}")
        elif db_name == 'clickhouse':
            return (f"clickhouse://{db_config.username}:{db_config.password}@"
                   f"{db_config.host}:{db_config.port}/{db_config.database}")
        else:
            return f"{db_name}://{db_config.host}:{db_config.port}"

    def get_redis_url(self) -> str:
        """Get Redis connection URL"""
        auth = f":{self.redis.password}@" if self.redis.password else ""
        return f"redis://{auth}{self.redis.host}:{self.redis.port}/{self.redis.db}"

    def validate_config(self) -> List[str]:
        """Validate configuration and return any errors"""
        errors = []

        # Check required environment variables for production
        if self.environment == Environment.PRODUCTION:
            required_vars = [
                'CLICKHOUSE_HOST', 'CLICKHOUSE_USER', 'CLICKHOUSE_PASS',
                'POSTGRES_HOST', 'POSTGRES_USER', 'POSTGRES_PASS',
                'REDIS_HOST', 'REDIS_PASS'
            ]

            for var in required_vars:
                if not os.getenv(var):
                    errors.append(f"Missing required environment variable: {var}")

        # Validate performance requirements
        if self.performance.processing_workers < 1:
            errors.append("Processing workers must be at least 1")

        if self.performance.queue_size < 1000:
            errors.append("Queue size should be at least 1000 for good performance")

        # Validate database connections
        for db_name, db_config in self.databases.items():
            if not db_config.host:
                errors.append(f"Database {db_name} host not configured")
            if not db_config.username:
                errors.append(f"Database {db_name} username not configured")

        return errors


# Global configuration instance
_config_instance = None


def get_config(environment: Optional[Environment] = None) -> PipelineConfig:
    """Get global configuration instance"""
    global _config_instance

    if _config_instance is None:
        env = environment or Environment(os.getenv('ENVIRONMENT', 'development'))
        _config_instance = PipelineConfig(env)

        # Validate configuration
        errors = _config_instance.validate_config()
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")

    return _config_instance


def reset_config():
    """Reset global configuration (mainly for testing)"""
    global _config_instance
    _config_instance = None


# Configuration constants
DEFAULT_SYMBOLS = [
    'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD',
    'EURGBP', 'EURJPY', 'GBPJPY', 'XAUUSD', 'XAGUSD', 'BTCUSD', 'ETHUSD'
]

DATA_RETENTION_DAYS = {
    'tick_data': 30,        # 30 days for tick data
    'minute_data': 365,     # 1 year for minute data
    'hourly_data': 1825,    # 5 years for hourly data
    'daily_data': 3650      # 10 years for daily data
}

PERFORMANCE_THRESHOLDS = {
    'max_latency_p99_ms': 500,
    'max_latency_p95_ms': 200,
    'max_latency_p50_ms': 50,
    'min_throughput_tps': 18,
    'max_memory_usage_mb': 2048,
    'max_cpu_usage_percent': 80
}