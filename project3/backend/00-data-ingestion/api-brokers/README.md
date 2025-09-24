# Native API-Based Broker Collectors

## 🎯 Purpose
**Native API collector services** yang menggunakan direct broker REST/WebSocket APIs untuk data ingestion dengan maximum performance, lower latency, dan access ke advanced broker features yang tidak tersedia melalui MT5.

---

## 🏗️ Native API Collector Architecture

### **Native API Brokers**:
```
api-brokers/
├── fxcm/               # FXCM REST API collector
│   ├── collector.py    # FXCM API integration
│   ├── config.yaml     # FXCM API credentials
│   ├── rest_client.py  # FXCM REST client
│   └── websocket_client.py # FXCM streaming
├── oanda/              # OANDA v20 API collector
│   ├── collector.py    # OANDA API integration
│   ├── config.yaml     # OANDA API credentials
│   ├── v20_client.py   # OANDA v20 REST client
│   └── stream_client.py # OANDA streaming
└── shared/             # Shared API utilities
    ├── api_client.py   # Generic REST client base
    ├── websocket_base.py # WebSocket client base
    ├── rate_limiter.py # API rate limiting
    └── api_validator.py # API-specific validation
```

---

## 🔄 Native API Collection Process

### **API Connection Flow**:
1. **API Authentication**: OAuth/Token-based authentication
2. **WebSocket Connection**: Real-time streaming connection
3. **Subscription Management**: Subscribe to instrument streams
4. **Rate Limiting**: Respect broker API limits
5. **NATS Publishing**: Stream processed data to Market Aggregator

### **Native API Benefits**:
```python
class NativeAPICollector:
    def __init__(self, broker_config: APIBrokerConfig):
        self.broker_name = broker_config.name
        self.api_endpoint = broker_config.api_endpoint
        self.credentials = broker_config.credentials

    async def authenticate(self):
        """Authenticate with broker API"""
        # OAuth flow for modern brokers
        token_response = await self.rest_client.post('/oauth/token', {
            'grant_type': 'client_credentials',
            'client_id': self.credentials.client_id,
            'client_secret': self.credentials.client_secret
        })

        self.access_token = token_response['access_token']

    async def subscribe_to_prices(self):
        """Subscribe to real-time price streaming"""
        # WebSocket streaming for low latency
        await self.websocket_client.connect(
            f"{self.stream_endpoint}/prices/stream",
            headers={'Authorization': f'Bearer {self.access_token}'}
        )

        for instrument in self.instruments:
            await self.websocket_client.subscribe(f'price.{instrument}')
```

---

## 📊 Native API Broker Configurations

### **FXCM API Setup**:
```yaml
# fxcm/config.yaml
broker:
  name: "FXCM"
  type: "rest_api"
  api_endpoint: "https://api-demo.fxcm.com"
  stream_endpoint: "wss://api-demo.fxcm.com/socket.io/"

credentials:
  access_token: "your_fxcm_access_token"
  account_id: "demo_account_123"

instruments:
  - "EUR/USD"
  - "GBP/USD"
  - "USD/JPY"
  - "USD/CHF"
  - "AUD/USD"

api_settings:
  rate_limit_per_minute: 300
  connection_timeout: 30
  reconnect_attempts: 5
  stream_buffer_size: 1000

features:
  market_depth: true
  historical_data: true
  order_book: true
  tick_volume: true
```

### **OANDA v20 API Setup**:
```yaml
# oanda/config.yaml
broker:
  name: "OANDA"
  type: "rest_api"
  api_endpoint: "https://api-fxpractice.oanda.com"
  stream_endpoint: "https://stream-fxpractice.oanda.com"

credentials:
  api_token: "your_oanda_api_token"
  account_id: "101-001-123456-001"

instruments:
  - "EUR_USD"
  - "GBP_USD"
  - "USD_JPY"
  - "USD_CHF"
  - "AUD_USD"
  - "USD_CAD"
  - "NZD_USD"

api_settings:
  rate_limit_per_second: 120
  connection_timeout: 30
  reconnect_attempts: 5
  stream_buffer_size: 1000

features:
  fractional_pricing: true
  streaming_prices: true
  granular_data: true
  position_book: true
```

---

## ⚡ Native API Performance Optimization

### **FXCM API Integration**:
```python
class FXCMAPICollector:
    def __init__(self, config: FXCMConfig):
        self.config = config
        self.rest_client = FXCMRestClient(config.api_endpoint, config.access_token)
        self.socket_client = FXCMSocketClient(config.stream_endpoint)

    async def start_price_streaming(self):
        """Start FXCM real-time price streaming"""
        await self.socket_client.connect()

        # Subscribe to price updates
        for instrument in self.config.instruments:
            await self.socket_client.emit('subscribe', {
                'pairs': [instrument]
            })

    async def on_price_update(self, data):
        """Handle FXCM price update"""
        # Convert FXCM format to standard
        market_tick = MarketTick()
        market_tick.symbol = data['Symbol'].replace('/', '')
        market_tick.bid = float(data['Rates'][0])
        market_tick.ask = float(data['Rates'][1])
        market_tick.timestamp = int(data['Updated'] * 1000)
        market_tick.broker_source = 'fxcm'

        await self.stream_to_aggregator(market_tick)
```

### **OANDA v20 API Integration**:
```python
class OANDAAPICollector:
    def __init__(self, config: OANDAConfig):
        self.config = config
        self.v20_client = oandapyV20.API(
            access_token=config.api_token,
            environment=config.environment
        )

    async def stream_prices(self):
        """Stream real-time prices from OANDA v20 API"""
        instruments = ','.join(self.config.instruments)

        stream = PricingStream(
            accountID=self.config.account_id,
            params={'instruments': instruments}
        )

        async for response in self.v20_client.request_async(stream):
            if response['type'] == 'PRICE':
                await self.process_oanda_price(response)

    async def process_oanda_price(self, price_data):
        """Process OANDA price update"""
        # Convert OANDA format to standard
        market_tick = MarketTick()
        market_tick.symbol = price_data['instrument'].replace('_', '')
        market_tick.bid = float(price_data['bids'][0]['price'])
        market_tick.ask = float(price_data['asks'][0]['price'])
        market_tick.timestamp = int(datetime.fromisoformat(
            price_data['time'].replace('Z', '+00:00')
        ).timestamp() * 1000)
        market_tick.broker_source = 'oanda'

        await self.stream_to_aggregator(market_tick)
```

---

## 🔍 API-Specific Features

### **FXCM Advanced Features**:
```python
class FXCMAdvancedData:
    async def get_market_depth(self, instrument: str):
        """Get FXCM market depth/order book"""
        response = await self.rest_client.get(f'/trading/get_model', {
            'models': ['OrderBook'],
            'pairs': instrument
        })
        return response['data']['OrderBook']

    async def get_tick_volume(self, instrument: str):
        """Get FXCM tick volume data"""
        response = await self.rest_client.get(f'/candles/{instrument}/m1', {
            'num': 1
        })
        return response['data'][0]['tickqty']
```

### **OANDA Advanced Features**:
```python
class OANDAAdvancedData:
    async def get_position_book(self, instrument: str):
        """Get OANDA position book data"""
        request = InstrumentsPositionBook(instrument=instrument)
        response = await self.v20_client.request_async(request)
        return response['positionBook']

    async def get_order_book(self, instrument: str):
        """Get OANDA order book data"""
        request = InstrumentsOrderBook(instrument=instrument)
        response = await self.v20_client.request_async(request)
        return response['orderBook']
```

---

## 🎯 Native API Advantages

### **Performance Benefits**:
- **Lower Latency**: Direct API connections bypass MT5 overhead
- **Higher Frequency**: Better tick resolution and timing
- **Real-time Streaming**: WebSocket connections for instant updates
- **Rate Optimization**: Custom rate limiting and connection management

### **Advanced Data Access**:
- **Market Depth**: Order book and liquidity data
- **Position Books**: Retail trader positioning data
- **Historical Analytics**: Advanced historical data access
- **Fractional Pricing**: Sub-pip precision for major pairs

### **Integration Benefits**:
- **Modern APIs**: RESTful and WebSocket standards
- **Better Documentation**: Comprehensive API documentation
- **Developer Tools**: SDKs and testing environments
- **Flexibility**: Custom data formatting and filtering

---

## 🔗 Business Value

### **Competitive Advantage**:
- **Premium Data Quality**: Direct from broker systems
- **Advanced Analytics**: Market depth and positioning data
- **Lower Infrastructure Cost**: No MT5 licensing required
- **Faster Time-to-Market**: Modern API integration

### **Operational Excellence**:
- **Monitoring**: Built-in API health metrics
- **Scalability**: Cloud-native API connections
- **Reliability**: Professional-grade API SLAs
- **Innovation**: Access to latest broker features