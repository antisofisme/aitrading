"""
client_settings.py - Client Settings Management

🎯 PURPOSE:
Business: Client-specific settings and configuration management
Technical: Structured settings with validation and environment overrides
Domain: Configuration/Client Settings/Environment Management

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:27.986Z
Session: client-side-ai-brain-full-compliance
Confidence: 91%
Complexity: medium

🧩 PATTERNS USED:
- AI_BRAIN_CLIENT_SETTINGS: Structured client settings management

📦 DEPENDENCIES:
Internal: config_manager, validation_core
External: dataclasses, typing, pathlib

💡 AI DECISION REASONING:
Client settings provide structured configuration with validation for reliable operation across different environments.

🚀 USAGE:
settings = ClientSettings.load(); mt5_server = settings.mt5.server

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

import os
import platform
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ClientEnvironment(str, Enum):
    """Client environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class LogLevel(str, Enum):
    """Logging levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class NetworkConfig(BaseSettings):
    """Network configuration for client connections"""
    
    # Server endpoints - TEMPORARILY: Direct to Data-Bridge (port 8001)
    server_host: str = Field(default="localhost", description="Server host")
    server_port: int = Field(default=8001, description="Data-Bridge port (temporary until API Gateway fixed)")
    server_protocol: str = Field(default="http", description="Server protocol")
    websocket_protocol: str = Field(default="ws", description="WebSocket protocol")
    
    # API endpoints - TEMPORARILY: Using working Data-Bridge endpoint
    api_base_path: str = Field(default="/api", description="API base path")
    websocket_path: str = Field(default="/api/v1/ws", description="WebSocket path - working Data-Bridge endpoint")
    health_path: str = Field(default="/health", description="Health check path")
    
    # Connection timeouts (seconds)
    connection_timeout: float = Field(default=10.0, description="Connection timeout")
    request_timeout: float = Field(default=30.0, description="Request timeout")
    websocket_timeout: float = Field(default=60.0, description="WebSocket timeout")
    websocket_ping_interval: float = Field(default=20.0, description="WebSocket ping interval")
    websocket_ping_timeout: float = Field(default=10.0, description="WebSocket ping timeout")
    
    # Retry settings
    max_reconnect_attempts: int = Field(default=5, description="Max reconnection attempts")
    reconnect_backoff_base: float = Field(default=2.0, description="Reconnection backoff base")
    reconnect_max_delay: float = Field(default=60.0, description="Max reconnection delay")
    
    # Heartbeat settings
    heartbeat_interval: float = Field(default=30.0, description="Heartbeat interval")
    heartbeat_timeout: float = Field(default=10.0, description="Heartbeat timeout")
    
    model_config = SettingsConfigDict(
        env_file=".env.client",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="",
        env_nested_delimiter="__"
    )
    
    # Computed properties
    @property
    def websocket_url(self) -> str:
        """Complete WebSocket URL"""
        return f"{self.websocket_protocol}://{self.server_host}:{self.server_port}{self.websocket_path}"
    
    @property
    def api_url(self) -> str:
        """Complete API URL"""
        return f"{self.server_protocol}://{self.server_host}:{self.server_port}{self.api_base_path}"
    
    @property
    def health_url(self) -> str:
        """Complete health check URL"""
        return f"{self.server_protocol}://{self.server_host}:{self.server_port}{self.health_path}"
    
    # Validation
    @field_validator('server_port')
    @classmethod
    def validate_port(cls, v):
        """Validate port number"""
        if not 1024 <= v <= 65535:
            raise ValueError('Port must be between 1024 and 65535')
        return v


class MT5Config(BaseSettings):
    """MT5 platform configuration"""
    
    # MT5 Connection credentials
    login: int = Field(default=0, description="MT5 login number", alias="MT5_LOGIN")
    password: str = Field(default="your_mt5_password", description="MT5 password", alias="MT5_PASSWORD") 
    server: str = Field(default="your_broker_server_name", description="MT5 broker server", alias="MT5_SERVER")
    
    # Installation paths
    windows_path: str = Field(default=r"C:\Program Files\MetaTrader 5\terminal64.exe", description="Windows MT5 path", alias="MT5_WINDOWS_PATH")
    linux_path: str = Field(default="/opt/mt5/terminal64", description="Linux MT5 path", alias="MT5_LINUX_PATH")
    custom_path: Optional[str] = Field(default=None, description="Custom MT5 path", alias="MT5_CUSTOM_PATH")
    
    # Process settings
    process_names: List[str] = Field(default=["terminal64.exe", "terminal64", "metatrader5.exe"], description="Process names")
    process_check_timeout: float = Field(default=30.0, description="Process check timeout")
    
    # Connection settings
    login_timeout: float = Field(default=30.0, description="Login timeout", alias="MT5_LOGIN_TIMEOUT")
    connection_retry_attempts: int = Field(default=3, description="Connection retry attempts", alias="MT5_CONNECTION_RETRY_ATTEMPTS")
    connection_retry_delay: float = Field(default=5.0, description="Connection retry delay", alias="MT5_CONNECTION_RETRY_DELAY")
    initialization_timeout: float = Field(default=60.0, description="Initialization timeout", alias="MT5_INITIALIZATION_TIMEOUT")
    startup_wait_time: float = Field(default=3.0, description="Startup wait time", alias="MT5_STARTUP_WAIT_TIME")
    
    # Trading symbols (will be parsed from comma-separated string in environment)
    major_pairs_raw: str = Field(default="EURUSD,GBPUSD,USDJPY,AUDUSD,USDCAD,USDCHF", description="Major currency pairs as string", alias="MAJOR_PAIRS")
    
    # Symbol settings
    symbol_selection_timeout: float = Field(default=10.0, description="Symbol selection timeout", alias="SYMBOL_SELECTION_TIMEOUT")
    tick_request_timeout: float = Field(default=5.0, description="Tick request timeout", alias="TICK_REQUEST_TIMEOUT")
    
    # Order execution
    default_magic_number: int = Field(default=234000, description="Default magic number", alias="MT5_DEFAULT_MAGIC_NUMBER")
    default_deviation_points: int = Field(default=20, description="Default deviation points", alias="MT5_DEFAULT_DEVIATION_POINTS")
    default_order_timeout: float = Field(default=30.0, description="Default order timeout", alias="MT5_DEFAULT_ORDER_TIMEOUT")
    order_fill_type: str = Field(default="IOC", description="Order fill type", alias="MT5_ORDER_FILL_TYPE")
    
    model_config = SettingsConfigDict(
        env_file=".env.client",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="",
        env_nested_delimiter="__"
    )
    
    @property
    def installation_path(self) -> str:
        """Get MT5 installation path for current platform"""
        if self.custom_path:
            return self.custom_path
        
        if platform.system() == "Windows":
            return self.windows_path
        else:
            return self.linux_path
    
    @property
    def major_pairs(self) -> List[str]:
        """Get major pairs as list from comma-separated string"""
        if not self.major_pairs_raw:
            return ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF"]
        return [pair.strip() for pair in self.major_pairs_raw.split(',') if pair.strip()]


class StreamingConfig(BaseSettings):
    """Redpanda/Kafka streaming configuration"""
    
    # Bootstrap servers (will be parsed from comma-separated strings)
    primary_servers_raw: str = Field(default="127.0.0.1:19092,localhost:19092", description="Primary bootstrap servers as string", alias="STREAMING_PRIMARY_SERVERS")
    fallback_servers_raw: str = Field(default="127.0.0.1:9092,localhost:9092", description="Fallback bootstrap servers as string", alias="STREAMING_FALLBACK_SERVERS")
    
    # Connection settings
    client_id: str = Field(default="mt5_bridge", description="Kafka client ID", alias="STREAMING_CLIENT_ID")
    group_id: str = Field(default="mt5_bridge_group", description="Kafka consumer group ID", alias="STREAMING_GROUP_ID")
    security_protocol: str = Field(default="PLAINTEXT", description="Security protocol", alias="STREAMING_SECURITY_PROTOCOL")
    
    # Producer settings
    batch_size: int = Field(default=16384, description="Producer batch size", alias="STREAMING_BATCH_SIZE")
    linger_ms: int = Field(default=5, description="Producer linger time", alias="STREAMING_LINGER_MS")
    compression_type: str = Field(default="gzip", description="Compression type", alias="STREAMING_COMPRESSION_TYPE")
    acks: int = Field(default=1, description="Producer acknowledgments", alias="STREAMING_ACKS")
    retries: int = Field(default=3, description="Producer retries", alias="STREAMING_RETRIES")
    retry_backoff_ms: int = Field(default=100, description="Retry backoff time", alias="STREAMING_RETRY_BACKOFF_MS")
    request_timeout_ms: int = Field(default=30000, description="Request timeout", alias="STREAMING_REQUEST_TIMEOUT_MS")
    
    # Consumer settings
    auto_offset_reset: str = Field(default="latest", description="Auto offset reset", alias="STREAMING_AUTO_OFFSET_RESET")
    enable_auto_commit: bool = Field(default=True, description="Enable auto commit", alias="STREAMING_ENABLE_AUTO_COMMIT")
    auto_commit_interval_ms: int = Field(default=5000, description="Auto commit interval", alias="STREAMING_AUTO_COMMIT_INTERVAL_MS")
    session_timeout_ms: int = Field(default=30000, description="Session timeout", alias="STREAMING_SESSION_TIMEOUT_MS")
    heartbeat_interval_ms: int = Field(default=3000, description="Heartbeat interval", alias="STREAMING_HEARTBEAT_INTERVAL_MS")
    
    # Topics
    tick_data_topic: str = Field(default="tick_data", description="Tick data topic", alias="TICK_DATA_TOPIC")
    events_topic: str = Field(default="mt5_events", description="Events topic", alias="EVENTS_TOPIC")
    responses_topic: str = Field(default="mt5_responses", description="Responses topic", alias="RESPONSES_TOPIC")
    signals_topic: str = Field(default="trading_signals", description="Trading signals topic", alias="SIGNALS_TOPIC")
    analytics_topic: str = Field(default="market_analytics", description="Analytics topic", alias="ANALYTICS_TOPIC")
    
    # Fallback settings
    enable_fallback_websocket: bool = Field(default=True, description="Enable WebSocket fallback")
    max_connection_attempts: int = Field(default=3, description="Max connection attempts")
    connection_retry_delay: float = Field(default=2.0, description="Connection retry delay")
    
    model_config = SettingsConfigDict(
        env_file=".env.client",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="",
        env_nested_delimiter="__"
    )
    
    @property
    def primary_servers(self) -> List[str]:
        """Get primary servers as list from comma-separated string"""
        if not self.primary_servers_raw:
            return ["127.0.0.1:19092", "localhost:19092"]
        return [server.strip() for server in self.primary_servers_raw.split(',') if server.strip()]
    
    @property
    def fallback_servers(self) -> List[str]:
        """Get fallback servers as list from comma-separated string"""
        if not self.fallback_servers_raw:
            return ["127.0.0.1:9092", "localhost:9092"]
        return [server.strip() for server in self.fallback_servers_raw.split(',') if server.strip()]
    
    @property
    def bootstrap_servers(self) -> str:
        """Get bootstrap servers as comma-separated string"""
        return ",".join(self.primary_servers)


class ApplicationConfig(BaseSettings):
    """Main application configuration"""
    
    # Basic settings
    app_name: str = Field(default="MT5 Bridge Client", description="Application name", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", description="Application version", alias="APP_VERSION")
    environment: ClientEnvironment = Field(default=ClientEnvironment.DEVELOPMENT, description="Environment", alias="ENVIRONMENT")
    debug: bool = Field(default=False, description="Debug mode", alias="DEBUG")
    
    # Logging configuration
    log_level: LogLevel = Field(default=LogLevel.INFO, description="Log level", alias="LOG_LEVEL")
    log_format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="Log format", alias="LOG_FORMAT")
    log_file: str = Field(default="mt5_bridge.log", description="Log file", alias="LOG_FILE")
    log_max_size: int = Field(default=10485760, description="Max log size (bytes)", alias="LOG_MAX_SIZE")
    log_retention: int = Field(default=7, description="Log retention (days)", alias="LOG_RETENTION")
    log_rotation: bool = Field(default=True, description="Enable log rotation", alias="LOG_ROTATION")
    
    # Performance settings
    data_processing_enabled: bool = Field(default=True, description="Enable data processing", alias="DATA_PROCESSING_ENABLED")
    data_batch_size: int = Field(default=100, description="Data batch size", alias="DATA_BATCH_SIZE")
    data_batch_timeout: float = Field(default=5.0, description="Data batch timeout", alias="DATA_BATCH_TIMEOUT")
    
    # Trading settings
    trading_enabled: bool = Field(default=False, description="Enable trading", alias="TRADING_ENABLED")
    paper_trading: bool = Field(default=True, description="Paper trading mode", alias="PAPER_TRADING")
    max_risk_per_trade: float = Field(default=2.0, description="Max risk per trade (%)", alias="MAX_RISK_PER_TRADE")
    max_daily_trades: int = Field(default=10, description="Max daily trades", alias="MAX_DAILY_TRADES")
    
    # File paths
    config_dir: str = Field(default="config", description="Configuration directory")
    logs_dir: str = Field(default="logs", description="Logs directory")
    data_dir: str = Field(default="data", description="Data directory")
    
    model_config = SettingsConfigDict(
        env_file=".env.client",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="",
        env_nested_delimiter="__"
    )
    
    # Validation
    @field_validator('environment', mode='before')
    @classmethod
    def validate_environment(cls, v):
        """Validate environment value"""
        if isinstance(v, str):
            return ClientEnvironment(v.lower())
        return v
    
    @field_validator('log_level', mode='before')
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level"""
        if isinstance(v, str):
            return LogLevel(v.upper())
        return v
    
    @field_validator('max_risk_per_trade')
    @classmethod
    def validate_risk_per_trade(cls, v):
        """Validate risk per trade"""
        if not 0.1 <= v <= 10.0:
            raise ValueError('Risk per trade must be between 0.1% and 10.0%')
        return v


class ClientConstants:
    """Centralized constants to replace magic numbers throughout client codebase"""
    
    # Timeout Constants (seconds)
    FAST_TIMEOUT = 5.0
    STANDARD_TIMEOUT = 30.0
    LONG_TIMEOUT = 300.0
    MT5_TIMEOUT = 60.0
    WEBSOCKET_TIMEOUT = 60.0
    
    # Cache TTL Constants (seconds)
    SHORT_TTL = 60      # 1 minute
    MEDIUM_TTL = 300    # 5 minutes
    LONG_TTL = 3600     # 1 hour
    
    # Retry Constants
    MAX_RETRIES = 3
    RETRY_BACKOFF = 2.0
    RETRY_DELAY = 1.0
    MT5_MAX_RETRIES = 5
    WEBSOCKET_MAX_RETRIES = 3
    
    # Batch Size Constants
    SMALL_BATCH = 10
    MEDIUM_BATCH = 100
    LARGE_BATCH = 1000
    TICK_BATCH_SIZE = 100
    
    # Memory Constants (MB)
    LOW_MEMORY = 32
    MEDIUM_MEMORY = 128
    HIGH_MEMORY = 256
    
    # MT5 Constants
    MT5_LOGIN_TIMEOUT = 30.0
    MT5_TICK_TIMEOUT = 5.0
    MT5_ORDER_TIMEOUT = 30.0
    MT5_MAGIC_NUMBER = 234000
    
    # WebSocket Constants
    WS_PING_INTERVAL = 20.0
    WS_PING_TIMEOUT = 10.0
    WS_CLOSE_TIMEOUT = 10.0
    
    # Trading Constants
    MIN_TRADE_SIZE = 0.01
    MAX_TRADE_SIZE = 100.0
    DEFAULT_SLIPPAGE = 20
    
    # File Constants
    LOG_FILE_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_RETENTION_DAYS = 7
    CONFIG_FILE_ENCODING = "utf-8"


class ClientSettings:
    """Main client settings that combines all configuration sections"""
    
    def __init__(self, **kwargs):
        # Initialize all configuration sections
        self.app = ApplicationConfig()
        self.network = NetworkConfig()
        self.mt5 = MT5Config()
        self.streaming = StreamingConfig()
        
        # Expose constants
        self.constants = ClientConstants()
        
        # Adjust settings based on environment
        self._adjust_for_environment()
        
        # Validate all configurations
        self._validate_all()
    
    def _adjust_for_environment(self):
        """Adjust settings based on environment"""
        if self.app.environment == ClientEnvironment.PRODUCTION:
            # Production optimizations
            self.app.debug = False
            self.app.log_level = LogLevel.WARNING
            self.app.trading_enabled = False  # Safer default
            self.app.paper_trading = True
            self.network.server_protocol = "https"
            self.network.websocket_protocol = "wss"
            
        elif self.app.environment == ClientEnvironment.STAGING:
            # Staging optimizations
            self.app.debug = False
            self.app.log_level = LogLevel.INFO
            self.app.trading_enabled = False
            self.app.paper_trading = True
            
        elif self.app.environment == ClientEnvironment.TESTING:
            # Testing optimizations
            self.app.debug = True
            self.app.log_level = LogLevel.DEBUG
            self.app.trading_enabled = False
            self.app.paper_trading = True
            
        elif self.app.environment == ClientEnvironment.DEVELOPMENT:
            # Development optimizations
            self.app.debug = True
            self.app.log_level = LogLevel.DEBUG
            self.app.trading_enabled = False
            self.app.paper_trading = True
    
    def _validate_all(self):
        """Validate all configuration sections"""
        try:
            # Validate each configuration section
            self.app.model_dump()
            self.network.model_dump()
            self.mt5.model_dump()
            self.streaming.model_dump()
            return True
        except Exception as e:
            raise ValueError(f"Configuration validation failed: {e}")
    
    def get_connection_urls(self) -> Dict[str, str]:
        """Get all connection URLs"""
        return {
            "websocket": self.network.websocket_url,
            "api": self.network.api_url,
            "health": self.network.health_url,
            "streaming": self.streaming.bootstrap_servers
        }
    
    def get_mt5_config(self) -> Dict[str, Any]:
        """Get MT5 configuration"""
        return {
            "path": self.mt5.installation_path,
            "timeout": self.mt5.login_timeout,
            "retries": self.mt5.connection_retry_attempts,
            "symbols": self.mt5.major_pairs,
            "magic_number": self.mt5.default_magic_number
        }
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.app.environment == ClientEnvironment.PRODUCTION
    
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.app.environment == ClientEnvironment.DEVELOPMENT
    
    def reload_config(self):
        """Reload configuration"""
        self.__init__()


# Global client settings instance
client_settings = None


def get_client_settings() -> ClientSettings:
    """Get global client settings instance"""
    global client_settings
    if client_settings is None:
        client_settings = ClientSettings()
    return client_settings


def reload_client_settings():
    """Reload client settings"""
    global client_settings
    client_settings = None
    return get_client_settings()


# Export for convenience
__all__ = [
    "ClientSettings",
    "get_client_settings",
    "reload_client_settings",
    "NetworkConfig",
    "MT5Config", 
    "StreamingConfig",
    "ApplicationConfig",
    "ClientConstants",
    "ClientEnvironment",
    "LogLevel"
]