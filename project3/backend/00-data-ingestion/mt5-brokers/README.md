# MT5-Based Broker Collectors

## 🎯 Purpose
**MetaTrader5-based collector services** yang menggunakan direct MT5 terminal connections ke brokers yang menyediakan MT5 platform untuk data ingestion dengan maximum compatibility dan reliability.

---

## 🏗️ MT5 Collector Architecture

### **MT5-Compatible Brokers**:
```
mt5-brokers/
├── ic-markets/          # IC Markets MT5 collector
│   ├── collector.py     # MT5 Python API integration
│   ├── config.yaml      # IC Markets MT5 server config
│   └── health.py        # MT5 connection monitoring
├── pepperstone/         # Pepperstone MT5 collector
│   ├── collector.py     # MT5 Python API integration
│   ├── config.yaml      # Pepperstone MT5 server config
│   └── health.py        # MT5 connection monitoring
└── shared/             # Shared MT5 utilities
    ├── mt5_client.py   # MetaTrader5 Python wrapper
    ├── mt5_validator.py # MT5-specific validation
    └── mt5_monitor.py   # MT5 health monitoring
```

---

## 🔄 MT5 Collection Process

### **MT5 Connection Flow**:
1. **MT5 Terminal Init**: Initialize MetaTrader5 Python library
2. **Broker Login**: Authenticate with broker MT5 server
3. **Symbol Selection**: Subscribe to major trading pairs
4. **Tick Streaming**: Real-time tick data collection via MT5 API
5. **NATS Publishing**: Stream processed data to Market Aggregator

### **MT5-Specific Features**:
```python
import MetaTrader5 as mt5

class MT5BrokerCollector:
    def __init__(self, broker_config: MT5BrokerConfig):
        self.broker_name = broker_config.name
        self.server = broker_config.server
        self.login = broker_config.login
        self.password = broker_config.password

    async def initialize_mt5(self):
        """Initialize MT5 terminal connection"""
        if not mt5.initialize():
            raise Exception(f"MT5 initialization failed: {mt5.last_error()}")

        # Login to broker
        if not mt5.login(self.login, self.password, self.server):
            raise Exception(f"MT5 login failed: {mt5.last_error()}")

    async def collect_tick_data(self):
        """Collect real-time tick data via MT5 API"""
        for symbol in self.symbols:
            # Get latest tick
            tick = mt5.symbol_info_tick(symbol)
            if tick is not None:
                # Convert MT5 tick to standard format
                market_tick = self.convert_mt5_tick(tick, symbol)
                await self.stream_to_aggregator(market_tick)
```

---

## 📊 MT5 Broker Configurations

### **IC Markets MT5 Setup**:
```yaml
# ic-markets/config.yaml
broker:
  name: "IC Markets"
  type: "mt5"
  server: "ICMarkets-Demo01"
  login: 12345678
  password: "demo_password"

symbols:
  - "EURUSD"
  - "GBPUSD"
  - "USDJPY"
  - "USDCHF"
  - "AUDUSD"

mt5_settings:
  terminal_path: "/opt/mt5-icmarkets/"
  connection_timeout: 30
  reconnect_attempts: 5
  tick_buffer_size: 1000
```

### **Pepperstone MT5 Setup**:
```yaml
# pepperstone/config.yaml
broker:
  name: "Pepperstone"
  type: "mt5"
  server: "Pepperstone-Demo"
  login: 87654321
  password: "demo_password"

symbols:
  - "EURUSD"
  - "GBPUSD"
  - "USDJPY"
  - "EURGBP"
  - "EURJPY"

mt5_settings:
  terminal_path: "/opt/mt5-pepperstone/"
  connection_timeout: 30
  reconnect_attempts: 5
  tick_buffer_size: 1000
```

---

## ⚡ MT5 Performance Optimization

### **MT5 Connection Management**:
```python
class MT5ConnectionManager:
    def __init__(self, broker_configs: List[MT5BrokerConfig]):
        self.broker_configs = broker_configs
        self.active_connections = {}

    async def maintain_mt5_connections(self):
        """Monitor and maintain MT5 connections"""
        for config in self.broker_configs:
            try:
                # Check MT5 connection health
                if not mt5.terminal_info():
                    await self.reconnect_mt5(config)

                # Verify account connection
                if not mt5.account_info():
                    await self.relogin_mt5(config)

            except Exception as e:
                logger.error(f"MT5 connection error for {config.name}: {e}")
                await self.handle_mt5_failure(config)
```

### **MT5 Data Validation**:
```python
def validate_mt5_tick(self, tick_data, symbol: str) -> bool:
    """Validate MT5 tick data integrity"""

    # Check MT5 specific fields
    if not hasattr(tick_data, 'time') or not hasattr(tick_data, 'time_msc'):
        return False

    # Validate MT5 bid/ask
    if tick_data.bid <= 0 or tick_data.ask <= 0:
        return False

    # Check MT5 spread reasonableness
    spread = tick_data.ask - tick_data.bid
    if spread > 0.01:  # 100 pips maximum
        return False

    # Validate MT5 volume
    if tick_data.volume < 0:
        return False

    return True
```

---

## 🔗 Integration Benefits

### **MT5 Advantages**:
- **Standardized API**: Consistent MetaTrader5 Python integration
- **Broker Compatibility**: Works with any MT5-supporting broker
- **Rich Data**: Complete tick information including volume and flags
- **Established Protocol**: Mature and stable connection method

### **MT5 Performance**:
- **Connection Efficiency**: Single MT5 connection per broker
- **Data Completeness**: Full tick data with MT5 metadata
- **Reliability**: Proven MT5 terminal stability
- **Monitoring**: Built-in MT5 connection diagnostics

---

## 🎯 Business Value

### **MT5 Broker Coverage**:
- **IC Markets**: Premium forex broker with tight spreads
- **Pepperstone**: Popular retail forex broker
- **Scalable**: Easy addition of new MT5-compatible brokers
- **Standardized**: Consistent data format across MT5 brokers

### **Operational Benefits**:
- **Single Technology Stack**: MetaTrader5 Python API
- **Unified Monitoring**: Common MT5 health checks
- **Easy Maintenance**: Standardized MT5 configuration
- **Broker Flexibility**: Support any MT5-enabled broker