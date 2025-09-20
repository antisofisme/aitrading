"""
MT5 Bridge Configuration - Trading platform and connection settings
"""
from typing import Dict, Any, Optional, List
from ...infrastructure.core.config_core import CoreConfig

# MT5 Configuration Constants
MT5_CONFIG_DEFAULT_TIMEOUT = 60000
MT5_CONFIG_DEFAULT_RETRIES = 3
MT5_CONFIG_DEFAULT_RETRY_DELAY = 5.0
MT5_CONFIG_MAX_RECONNECT_ATTEMPTS = 10
MT5_CONFIG_DEFAULT_MAGIC_NUMBER = 12345
MT5_CONFIG_MAX_VOLUME = 10.0
MT5_CONFIG_MIN_VOLUME = 0.01
MT5_CONFIG_VOLUME_STEP = 0.01
MT5_CONFIG_MAX_POSITIONS = 100
MT5_CONFIG_MAX_ORDERS = 200
MT5_CONFIG_DEFAULT_SLIPPAGE = 10
MT5_CONFIG_MAX_RISK_PER_TRADE = 0.02
MT5_CONFIG_MAX_DAILY_LOSS = 0.05
MT5_CONFIG_MAX_DRAWDOWN = 0.10
MT5_CONFIG_MAX_BARS = 10000
MT5_CONFIG_TICK_BUFFER_SIZE = 1000
MT5_CONFIG_DATA_REFRESH_INTERVAL = 1.0
MT5_CONFIG_HISTORICAL_DATA_LIMIT = 100000
MT5_CONFIG_WEBSOCKET_PORT = 8001
MT5_CONFIG_MAX_CONNECTIONS = 100
MT5_CONFIG_PING_INTERVAL = 20
MT5_CONFIG_PING_TIMEOUT = 10
MT5_CONFIG_CLOSE_TIMEOUT = 10
MT5_CONFIG_MESSAGE_QUEUE_SIZE = 1000
MT5_CONFIG_HEARTBEAT_INTERVAL = 30
MT5_CONFIG_BATCH_SIZE = 100
MT5_CONFIG_MAX_CONCURRENT = 50
MT5_CONFIG_REQUEST_TIMEOUT = 30.0
MT5_CONFIG_CACHE_TTL = 300
MT5_CONFIG_MEMORY_LIMIT_MB = 512
MT5_CONFIG_GC_THRESHOLD = 1000
MT5_CONFIG_HEALTH_CHECK_INTERVAL = 30
MT5_CONFIG_METRICS_INTERVAL = 60
MT5_CONFIG_METRICS_PORT = 9001
MT5_CONFIG_LATENCY_THRESHOLD = 1000

class MT5BridgeConfig(CoreConfig):
    """MT5 Bridge specific configuration with trading platform settings"""
    
    def __init__(self):
        super().__init__("mt5-bridge")
        self.setup_mt5_defaults()
        self.load_mt5_configuration()
    
    def setup_mt5_defaults(self):
        """Setup MT5 Bridge specific default configurations"""
        mt5_defaults = {
            # MT5 Connection Settings
            "mt5": {
                "server": "MetaQuotes-Demo",
                "login": None,  # Must be provided via environment
                "password": None,  # Must be provided via environment
                "timeout": MT5_CONFIG_DEFAULT_TIMEOUT,  # Connection timeout in ms
                "path": None,  # MT5 installation path (auto-detect if None)
                "portable": False,  # Use portable mode
                "connection_retries": MT5_CONFIG_DEFAULT_RETRIES,
                "retry_delay": MT5_CONFIG_DEFAULT_RETRY_DELAY,
                "max_reconnect_attempts": MT5_CONFIG_MAX_RECONNECT_ATTEMPTS
            },
            
            # Trading Settings
            "trading": {
                "max_volume": MT5_CONFIG_MAX_VOLUME,  # Maximum lot size
                "min_volume": MT5_CONFIG_MIN_VOLUME,  # Minimum lot size
                "volume_step": MT5_CONFIG_VOLUME_STEP,  # Volume step
                "max_positions": MT5_CONFIG_MAX_POSITIONS,  # Maximum open positions
                "max_orders": MT5_CONFIG_MAX_ORDERS,  # Maximum pending orders
                "slippage": MT5_CONFIG_DEFAULT_SLIPPAGE,  # Slippage in points
                "magic_number": MT5_CONFIG_DEFAULT_MAGIC_NUMBER,  # EA magic number
                "comment": "MT5Bridge",  # Trade comment
                "enable_trading": True,  # Enable/disable trading
                "risk_management": {
                    "max_risk_per_trade": MT5_CONFIG_MAX_RISK_PER_TRADE,  # 2% per trade
                    "max_daily_loss": MT5_CONFIG_MAX_DAILY_LOSS,  # 5% daily loss limit
                    "max_drawdown": MT5_CONFIG_MAX_DRAWDOWN,  # 10% maximum drawdown
                    "enable_stop_loss": True,
                    "enable_take_profit": True
                }
            },
            
            # Data Settings
            "data": {
                "symbols": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"],
                "timeframes": ["M1", "M5", "M15", "M30", "H1", "H4", "D1"],
                "max_bars": MT5_CONFIG_MAX_BARS,  # Maximum bars to retrieve
                "tick_buffer_size": MT5_CONFIG_TICK_BUFFER_SIZE,  # Tick buffer size
                "enable_tick_streaming": True,
                "enable_bar_streaming": True,
                "data_refresh_interval": MT5_CONFIG_DATA_REFRESH_INTERVAL,  # seconds
                "historical_data_limit": MT5_CONFIG_HISTORICAL_DATA_LIMIT
            },
            
            # WebSocket Settings
            "websocket": {
                "host": "0.0.0.0",
                "port": MT5_CONFIG_WEBSOCKET_PORT,
                "max_connections": MT5_CONFIG_MAX_CONNECTIONS,
                "ping_interval": MT5_CONFIG_PING_INTERVAL,
                "ping_timeout": MT5_CONFIG_PING_TIMEOUT,
                "close_timeout": MT5_CONFIG_CLOSE_TIMEOUT,
                "enable_compression": True,
                "message_queue_size": MT5_CONFIG_MESSAGE_QUEUE_SIZE,
                "heartbeat_interval": MT5_CONFIG_HEARTBEAT_INTERVAL
            },
            
            # Performance Settings
            "performance": {
                "tick_processing_batch_size": MT5_CONFIG_BATCH_SIZE,
                "max_concurrent_requests": MT5_CONFIG_MAX_CONCURRENT,
                "request_timeout": MT5_CONFIG_REQUEST_TIMEOUT,
                "cache_ttl": MT5_CONFIG_CACHE_TTL,  # 5 minutes
                "enable_caching": True,
                "memory_limit_mb": MT5_CONFIG_MEMORY_LIMIT_MB,
                "gc_threshold": MT5_CONFIG_GC_THRESHOLD
            },
            
            # Monitoring Settings
            "monitoring": {
                "health_check_interval": MT5_CONFIG_HEALTH_CHECK_INTERVAL,
                "performance_metrics_interval": MT5_CONFIG_METRICS_INTERVAL,
                "log_level": "INFO",
                "enable_metrics": True,
                "metrics_port": MT5_CONFIG_METRICS_PORT,
                "alert_on_connection_loss": True,
                "alert_on_high_latency": True,
                "latency_threshold_ms": MT5_CONFIG_LATENCY_THRESHOLD
            }
        }
        
        self.defaults.update(mt5_defaults)
    
    def load_mt5_configuration(self):
        """Load MT5-specific configuration from various sources"""
        try:
            # Load from YAML configuration files
            self.load_from_yaml("mt5_bridge.yaml")
            
            # Load environment-specific overrides
            env = self.get_environment()
            if env != "development":
                self.load_from_yaml(f"mt5_bridge.{env}.yaml")
            
            # Load sensitive data from environment variables
            self._load_sensitive_config()
            
            # Validate critical configurations
            self._validate_mt5_config()
            
        except Exception as e:
            self.logger.error(f"Failed to load MT5 configuration: {e}")
            raise
    
    def _load_sensitive_config(self):
        """Load sensitive configuration from data-bridge configuration manager"""
        # Use data-bridge configuration manager instead of direct environment access
        from ...infrastructure.config_manager import get_config_manager
        
        config_manager = get_config_manager()
        
        # MT5 credentials - using data-bridge config management
        mt5_creds = config_manager.get_mt5_credentials()
        
        if mt5_creds['login']:
            try:
                self.set("mt5.login", int(mt5_creds['login']))
            except ValueError:
                raise ValueError(f"Invalid MT5 login: {mt5_creds['login']}. Must be numeric.")
        
        if mt5_creds['password']:
            self.set("mt5.password", mt5_creds['password'])
        
        if mt5_creds['server']:
            self.set("mt5.server", mt5_creds['server'])
        
        # Trading settings from configuration manager
        magic_number = config_manager.get('trading.magic_number')
        if magic_number:
            self.set("trading.magic_number", magic_number)
        
        # WebSocket settings from configuration manager
        ws_port = config_manager.get('websocket.port')
        if ws_port:
            self.set("websocket.port", ws_port)
    
    def _validate_mt5_config(self):
        """Validate critical MT5 configuration"""
        # Check required MT5 credentials
        if not self.get("mt5.login"):
            raise ValueError("MT5 login is required. Set MT5_LOGIN environment variable.")
        
        if not self.get("mt5.password"):
            raise ValueError("MT5 password is required. Set MT5_PASSWORD environment variable.")
        
        # Validate trading settings
        max_volume = self.get("trading.max_volume")
        min_volume = self.get("trading.min_volume")
        if max_volume <= min_volume:
            raise ValueError("Maximum volume must be greater than minimum volume")
        
        # Validate WebSocket settings
        port = self.get("websocket.port")
        if not (1024 <= port <= 65535):
            raise ValueError("WebSocket port must be between 1024 and 65535")
        
        # Validate symbols
        symbols = self.get("data.symbols")
        if not symbols or not isinstance(symbols, list):
            raise ValueError("At least one trading symbol must be configured")
    
    def get_mt5_connection_params(self) -> Dict[str, Any]:
        """Get MT5 connection parameters"""
        return {
            "login": self.get("mt5.login"),
            "password": self.get("mt5.password"),
            "server": self.get("mt5.server"),
            "timeout": self.get("mt5.timeout"),
            "path": self.get("mt5.path"),
            "portable": self.get("mt5.portable")
        }
    
    def get_trading_symbols(self) -> List[str]:
        """Get configured trading symbols"""
        return self.get("data.symbols", [])
    
    def get_timeframes(self) -> List[str]:
        """Get configured timeframes"""
        return self.get("data.timeframes", [])
    
    def get_websocket_config(self) -> Dict[str, Any]:
        """Get WebSocket server configuration"""
        return {
            "host": self.get("websocket.host"),
            "port": self.get("websocket.port"),
            "max_connections": self.get("websocket.max_connections"),
            "ping_interval": self.get("websocket.ping_interval"),
            "ping_timeout": self.get("websocket.ping_timeout"),
            "close_timeout": self.get("websocket.close_timeout")
        }
    
    def get_risk_settings(self) -> Dict[str, Any]:
        """Get risk management settings"""
        return self.get("trading.risk_management", {})
    
    def is_trading_enabled(self) -> bool:
        """Check if trading is enabled"""
        return self.get("trading.enable_trading", False)
    
    def get_magic_number(self) -> int:
        """Get EA magic number"""
        return self.get("trading.magic_number", MT5_CONFIG_DEFAULT_MAGIC_NUMBER)
    
    def update_symbol_config(self, symbol: str, config: Dict[str, Any]):
        """Update configuration for specific symbol"""
        symbol_config = self.get(f"symbols.{symbol}", {})
        symbol_config.update(config)
        self.set(f"symbols.{symbol}", symbol_config)
        
        self.logger.info(f"Updated configuration for symbol {symbol}", {
            "symbol": symbol,
            "config": config,
            "operation_type": "config_update"
        })