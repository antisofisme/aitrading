# Client-MT5 - Data Subscriber Client

## 🎯 Purpose
**Data subscriber client** yang menggunakan WebSocket connection ke server untuk menerima processed market data dan indicators dari server-side data ingestion system, menggantikan direct MT5 streaming untuk maximum efficiency.

---

## 📊 Architecture Revolution

### **Old Architecture (Inefficient)**:
```
1000 Clients × Direct MT5 Connections = 3000 broker connections
Each client processes raw tick data individually
Redundant calculations: 1000× indicator processing
Resource waste: 99.9% redundant processing
```

### **New Architecture (Optimal)**:
```
Server-Side Data Ingestion:
├── 00-data-ingestion: 3 broker connections → serve 1000+ clients
├── Server-side indicators: Process once, serve many
├── Client-MT5: Data subscriber + local display
└── 99.9% Resource Reduction: 3000 → 3 connections
```

---

## 🔄 Client Data Flow

### **Data Subscription Model**:
```
Client-MT5 → API Gateway → Data Bridge → Database Service → Processed Data
     ↓              ↓              ↓               ↓              ↓
WebSocket       JWT Auth      Subscription      Multi-DB     Real-time
Subscribe       User Context   Tier Filtering    Storage      Market Data
Real-time       Rate Limits    Data Access      Historical    + Indicators
Display         Multi-tenant   Validation       Analytics     Ready to Use
```

### **Client Responsibilities** (Simplified):
1. **Authentication**: JWT-based login dengan subscription tier
2. **WebSocket Subscription**: Connect to server data streams
3. **Data Reception**: Receive processed market data + indicators
4. **Local Display**: Show charts, indicators, trading interface
5. **Trade Execution**: Send orders via API Gateway to trading service

---

## 🚀 Protocol Buffer Integration

### **Schema Import** (from Server Registry):
```cpp
// Import from centralized server schemas
#include "central-hub/shared/proto/trading/market_data.proto"
#include "central-hub/shared/proto/common/user_context.proto"
#include "central-hub/shared/proto/indicators/technical_analysis.proto"
```

### **Data Reception Messages**:
```protobuf
message ClientMarketData {
  string symbol = 1;                    // Trading pair
  double bid = 2;                      // Current bid price
  double ask = 3;                      // Current ask price
  int64 timestamp = 4;                 // Server timestamp
  SubscriptionTier user_tier = 5;      // User access level
  TechnicalIndicators indicators = 6;   // Server-calculated indicators
  MarketSession session = 7;           // Market session info
}

message TechnicalIndicators {
  double sma_20 = 1;                   // Simple Moving Average 20
  double sma_50 = 2;                   // Simple Moving Average 50
  double ema_12 = 3;                   // Exponential Moving Average 12
  double ema_26 = 4;                   // Exponential Moving Average 26
  double macd_line = 5;                // MACD Line
  double macd_signal = 6;              // MACD Signal
  double rsi = 7;                      // Relative Strength Index
  double bollinger_upper = 8;          // Bollinger Band Upper
  double bollinger_middle = 9;         // Bollinger Band Middle
  double bollinger_lower = 10;         // Bollinger Band Lower
}
```

## 📱 Client Implementation

### **WebSocket Client (C++/MQL5)**:
```cpp
// WebSocket client for data subscription
class MarketDataSubscriber {
private:
    WebSocketClient ws_client;
    ProtocolBufferParser pb_parser;
    string jwt_token;
    string user_id;

public:
    bool ConnectToServer(string server_url, string auth_token) {
        // Connect via API Gateway WebSocket endpoint
        string ws_url = "wss://api.gateway.com/ws/market-data";

        // Add authentication headers
        map<string, string> headers;
        headers["Authorization"] = "Bearer " + auth_token;
        headers["x-user-id"] = user_id;

        return ws_client.Connect(ws_url, headers);
    }

    void SubscribeToSymbols(vector<string> symbols) {
        // Send subscription request
        for (string symbol : symbols) {
            SubscriptionRequest request;
            request.symbol = symbol;
            request.data_type = "real_time_with_indicators";

            string binary_data = request.SerializeAsString();
            ws_client.Send(binary_data);
        }
    }

    void OnDataReceived(string binary_data) {
        // Parse Protocol Buffer data
        ClientMarketData market_data;
        market_data.ParseFromString(binary_data);

        // Update local charts and displays
        UpdateChart(market_data);
        UpdateIndicators(market_data.indicators);
    }
};
```

### **MQL5 Expert Advisor Integration**:
```mql5
//+------------------------------------------------------------------+
//| Client-MT5 Data Subscriber EA                                    |
//+------------------------------------------------------------------+

#include "WebSocketClient.mqh"
#include "ProtocolBuffer.mqh"

input string ServerURL = "wss://api.gateway.com/ws/market-data";
input string AuthToken = "your_jwt_token_here";
input string SubscribeSymbols = "EURUSD,GBPUSD,USDJPY";

MarketDataSubscriber subscriber;

int OnInit() {
    // Initialize WebSocket connection
    if (!subscriber.ConnectToServer(ServerURL, AuthToken)) {
        Print("Failed to connect to market data server");
        return INIT_FAILED;
    }

    // Subscribe to symbols
    string symbols[];
    StringSplit(SubscribeSymbols, ',', symbols);
    subscriber.SubscribeToSymbols(symbols);

    Print("Client-MT5 Data Subscriber initialized");
    return INIT_SUCCEEDED;
}

void OnTick() {
    // Handle incoming WebSocket data
    subscriber.ProcessIncomingData();

    // Local trading logic using server-provided indicators
    ProcessTradingSignals();
}

void OnDeinit(const int reason) {
    subscriber.Disconnect();
    Print("Client-MT5 Data Subscriber stopped");
}

void ProcessTradingSignals() {
    // Use server-calculated indicators for trading decisions
    ClientMarketData current_data = subscriber.GetLatestData("EURUSD");

    if (current_data.indicators.rsi < 30) {
        // RSI oversold - potential buy signal
        // Send order via API Gateway
        PlaceOrder("EURUSD", ORDER_TYPE_BUY, 0.1);
    }
    else if (current_data.indicators.rsi > 70) {
        // RSI overbought - potential sell signal
        // Send order via API Gateway
        PlaceOrder("EURUSD", ORDER_TYPE_SELL, 0.1);
    }
}

void PlaceOrder(string symbol, int order_type, double volume) {
    // Send order via API Gateway to Trading Service
    OrderRequest request;
    request.symbol = symbol;
    request.order_type = order_type;
    request.volume = volume;
    request.user_id = subscriber.GetUserId();

    // Send via HTTP API
    HTTPClient http_client;
    http_client.Post("https://api.gateway.com/api/v1/orders", request);
}
```

---

## 🔗 Integration Points

### **Server Dependencies**:
- **API Gateway**: WebSocket authentication + data streaming
- **Data Bridge**: Real-time market data distribution
- **00-data-ingestion**: Server-side broker data collection
- **Indicators Service**: Server-calculated technical indicators
- **Trading Service**: Order placement and management

### **Client Features**:
- **Real-time Charts**: Display server-streamed data
- **Technical Indicators**: Show server-calculated indicators
- **Trading Interface**: Place orders via API Gateway
- **Subscription Management**: Handle different tier access
- **Offline Mode**: Cache data for temporary disconnections

---

## 📊 Performance Benefits

### **Client-Side Efficiency**:
```
Resource Savings per Client:
- No MT5 connection needed: 100% connection overhead eliminated
- No indicator calculations: 95% CPU usage reduction
- No data processing: 90% memory usage reduction
- Bandwidth optimized: 60% smaller Protocol Buffer data
```

### **Network Optimization**:
```
Data Transfer Comparison (1000 clients):
Traditional: 1000 × full tick streams = 1000× bandwidth
New Model: 1 processed stream → 1000 clients = 99.9% reduction
```

---

## 🚀 Protocol Buffers DLL Implementation

### **Custom C++ DLL Architecture**:

#### **DLL Structure**:
```cpp
// TradingProtobuf.dll - MT5 Integration Layer

// Core Functions (exported to MT5)
extern "C" {
    __declspec(dllexport) int InitializeProtobuf();
    __declspec(dllexport) int SendTickBatch(const char* symbols[],
                                           double bids[], double asks[],
                                           long timestamps[], int count);
    __declspec(dllexport) int ConnectWebSocket(const char* endpoint, const char* auth_token);
    __declspec(dllexport) int GetConnectionStatus();
    __declspec(dllexport) void CleanupProtobuf();
}

// Internal Implementation
class ProtobufManager {
public:
    bool SerializeMarketDataStream(const std::vector<trading::v1::TickData>& ticks, std::string& output);
    bool SendToWebSocket(const std::string& binary_data);
    bool ValidateConnection();
private:
    std::unique_ptr<WebSocketClient> ws_client_;
    trading::v1::MarketDataStream current_stream_;
    common::v1::UserContext user_context_;
};
```

#### **MT5 Expert Advisor Integration**:
```mql5
// MT5 Expert Advisor (MQL5 Code)
#property copyright "AI Trading Platform"
#property version   "1.00"

#import "TradingProtobuf.dll"
   int InitializeProtobuf();
   int SendTickBatch(string symbols[], double bids[], double asks[], long timestamps[], int count);
   int ConnectWebSocket(string endpoint, string auth_token);
   int GetConnectionStatus();
   void CleanupProtobuf();
#import

// Global variables
string SYMBOLS[] = {"EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD",
                   "USDCAD", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY"};
double tick_buffer_bids[10];
double tick_buffer_asks[10];
long tick_buffer_timestamps[10];
int buffer_count = 0;

// EA Initialization
int OnInit() {
    if(InitializeProtobuf() != 0) {
        Print("Failed to initialize Protocol Buffers");
        return INIT_FAILED;
    }

    // Connect to API Gateway WebSocket endpoint
    string endpoint = "wss://api.gateway.com/ws/mt5";
    string auth_token = "Bearer " + GetAuthToken();

    if(ConnectWebSocket(endpoint, auth_token) != 0) {
        Print("Failed to connect to WebSocket");
        return INIT_FAILED;
    }

    Print("MT5 Protocol Buffers integration initialized successfully");
    return INIT_SUCCEEDED;
}

// Tick processing
void OnTick() {
    // Collect tick data for all monitored symbols
    for(int i = 0; i < ArraySize(SYMBOLS); i++) {
        MqlTick tick;
        if(SymbolInfoTick(SYMBOLS[i], tick)) {
            // Add to batch buffer
            tick_buffer_bids[buffer_count] = tick.bid;
            tick_buffer_asks[buffer_count] = tick.ask;
            tick_buffer_timestamps[buffer_count] = tick.time_msc;
            buffer_count++;

            // Send batch when buffer is full (5 ticks) or timeout (100ms)
            if(buffer_count >= 5 || ShouldFlushBuffer()) {
                // Use server schema registry format
                SendTickBatch(SYMBOLS, tick_buffer_bids, tick_buffer_asks,
                             tick_buffer_timestamps, buffer_count);
                buffer_count = 0;
            }
        }
    }
}

// Cleanup
void OnDeinit(const int reason) {
    CleanupProtobuf();
    Print("Protocol Buffers integration cleaned up");
}
```

### **Performance Benefits**:
```
MT5 Integration Performance:
- Serialization: 1.5ms (vs 15ms JSON)
- Memory Usage: 60% less bandwidth
- CPU Usage: 10x less processing overhead
- Network Efficiency: Optimal untuk 50+ ticks/second
- Type Safety: Compile-time schema validation
```

### **DLL Dependencies**:
- **Protocol Buffers C++**: libprotobuf.lib
- **Generated Schema Files**:
  - trading/market_data.pb.h/.cc
  - common/base.pb.h/.cc
- **WebSocket Client**: websocketpp atau similar
- **MT5 Terminal API**: Compatible dengan MT5 build 3000+
- **Threading Support**: Multi-threaded tick processing
- **Schema Registry**: Sync dengan backend/central-hub/shared/proto/

### **Installation Process**:
1. **Generate Protocol Buffers Code**:
   ```bash
   # From backend schema registry
   cd backend/01-core-infrastructure/central-hub/shared/proto
   protoc --cpp_out=../../../../client-mt5/03-communication/protobuf/generated/ \
          trading/market_data.proto common/base.proto
   ```

2. **Compile TradingProtobuf.dll**:
   - Include generated .pb.h/.pb.cc files
   - Link dengan libprotobuf.lib
   - Build untuk MT5-compatible architecture

3. **Deploy to MT5**:
   - Place DLL di MT5 Terminal/MQL5/Libraries/ folder
   - Install Expert Advisor di MT5 Terminal/MQL5/Experts/
   - Configure WebSocket endpoint dan authentication dalam EA settings
   - Enable DLL imports dalam MT5 Terminal options

4. **Schema Sync Process**:
   - Monitor backend schema registry untuk updates
   - Regenerate client protobuf code saat schema changes
   - Rebuild dan redeploy DLL saat diperlukan

---

## 🔐 Centralized Configuration Management

### **User Configuration Flow**:
```
User Registration → Backend User Service → Configuration Database → Client-MT5 Config
       ↓                    ↓                      ↓                      ↓
Email/Password        User Profile            Encrypted Storage      Local Config Cache
Trading Preferences   MT5 Credentials         Symbol Selections     Real-time Updates
```

### **04-infrastructure/configuration/**
**Input Flow**: User settings dari backend user service
**Output Flow**: Localized config untuk client operations
**Function**:
- **Centralized Config Sync**: Pull user configuration dari backend
- **Secure Credential Storage**: Encrypted local storage untuk MT5 login
- **Trading Preferences**: User-selected trading pairs dan strategies
- **Real-time Updates**: Dynamic config updates tanpa restart

---

## 📊 Dynamic Pair Selection Strategy

### **User-Controlled Trading Pairs**:
```json
{
  "user_id": "user123",
  "trading_config": {
    "primary_pairs": ["EURUSD", "GBPUSD"],          // User selected trading pairs
    "correlation_pairs": ["USDCHF", "EURGBP"],      // Auto-selected for analysis
    "monitoring_pairs": ["USDJPY", "AUDUSD"],       // Market context pairs
    "max_simultaneous": 6,                          // User tier limit
    "correlation_threshold": 0.7                    // Auto-selection criteria
  }
}
```

### **Smart Correlation Selection**:
```python
# Auto-select correlation pairs based on user's primary trading pairs
def select_correlation_pairs(primary_pairs: List[str]) -> List[str]:
    CORRELATION_MATRIX = {
        "EURUSD": ["USDCHF", "EURGBP", "GBPUSD"],   # Negatively/positively correlated
        "GBPUSD": ["EURGBP", "USDCHF", "GBPJPY"],
        "USDJPY": ["EURJPY", "GBPJPY", "AUDJPY"]
    }

    correlation_pairs = []
    for primary in primary_pairs:
        correlation_pairs.extend(CORRELATION_MATRIX.get(primary, []))

    return list(set(correlation_pairs))  # Remove duplicates
```

### **Subscription Tier Limits**:
```json
{
  "free_tier": {
    "max_trading_pairs": 2,
    "max_monitoring_pairs": 4,
    "correlation_analysis": false
  },
  "pro_tier": {
    "max_trading_pairs": 5,
    "max_monitoring_pairs": 10,
    "correlation_analysis": true
  },
  "enterprise_tier": {
    "max_trading_pairs": "unlimited",
    "max_monitoring_pairs": "unlimited",
    "correlation_analysis": true,
    "custom_pairs": true
  }
}
```

---

## 🔐 Secure Credential Management

### **Centralized Authentication Flow**:
```
User Login (Web) → Backend Auth → Encrypted Credentials → Client-MT5 Download
      ↓               ↓                ↓                     ↓
Email/Password    JWT Token        Database Storage      Local Decryption
2FA Optional      Session Mgmt     AES-256 Encryption    Secure Memory
```

### **MT5 Credential Structure**:
```json
{
  "user_id": "user123",
  "email": "user@example.com",
  "mt5_accounts": [
    {
      "account_id": "mt5_001",
      "login": 1234567,
      "password": "encrypted_password",
      "server": "FBS-Demo",
      "broker": "FBS",
      "account_type": "demo",
      "is_active": true,
      "created_at": "2024-01-15T10:00:00Z"
    }
  ],
  "trading_permissions": {
    "can_trade": true,
    "max_position_size": 1.0,
    "allowed_symbols": ["EURUSD", "GBPUSD"],
    "risk_limits": {
      "max_daily_loss": 1000,
      "max_drawdown": 0.1
    }
  }
}
```

### **Configuration Sync Architecture**:
```python
class CentralizedConfigManager:
    def __init__(self, user_token: str):
        self.user_token = user_token
        self.backend_url = "https://api.aitrading.com"
        self.local_cache = SecureLocalStorage()

    async def sync_user_config(self) -> UserConfig:
        """Download user configuration dari backend"""
        headers = {"Authorization": f"Bearer {self.user_token}"}

        # Get user trading preferences
        user_config = await self.api_client.get(
            f"{self.backend_url}/api/v1/users/config",
            headers=headers
        )

        # Get MT5 credentials (encrypted)
        mt5_credentials = await self.api_client.get(
            f"{self.backend_url}/api/v1/users/mt5-accounts",
            headers=headers
        )

        # Cache locally dengan encryption
        await self.local_cache.store_encrypted(user_config, mt5_credentials)
        return UserConfig(user_config, mt5_credentials)
```

---

## 🎯 Dynamic Pair Monitoring Strategy

### **Real-time Pair Selection**:
```python
class DynamicPairManager:
    async def update_monitoring_pairs(self, user_config: UserConfig):
        """Update pairs based on user trading activity"""

        # 1. User selected trading pairs (always monitored)
        trading_pairs = user_config.primary_pairs

        # 2. Auto-select correlation pairs
        correlation_pairs = self.select_correlation_pairs(trading_pairs)

        # 3. Add market context pairs (major pairs for overall sentiment)
        context_pairs = ["EURUSD", "GBPUSD", "USDJPY"] if not in trading_pairs

        # 4. Apply subscription limits
        total_pairs = trading_pairs + correlation_pairs + context_pairs
        max_pairs = user_config.subscription_tier.max_monitoring_pairs

        final_pairs = total_pairs[:max_pairs]

        # 5. Update MT5 monitoring threads
        await self.mt5_manager.update_symbol_monitoring(final_pairs)
```

### **Intelligent Correlation Analysis**:
```python
# Real-time correlation calculation
correlation_data = {
    "EURUSD": {
        "correlated_pairs": ["USDCHF": -0.95, "EURGBP": 0.72],
        "impact_weight": 0.8,
        "monitoring_priority": "high"
    },
    "GBPUSD": {
        "correlated_pairs": ["EURGBP": 0.68, "GBPJPY": 0.85],
        "impact_weight": 0.7,
        "monitoring_priority": "medium"
    }
}
```

---

## 🚀 Hybrid Processing Benefits

### **Client-Side Processing (5ms)**:
✅ **Immediate validation** - Filter bad ticks before server
✅ **Fast indicators** - SMA/EMA calculated locally
✅ **Reduced bandwidth** - Send processed data, not raw ticks
✅ **Lower server load** - Preprocessing distributed to clients

### **Server-Side Processing (15ms)**:
✅ **Complex analysis** - MACD, Bollinger Bands, advanced indicators
✅ **AI predictions** - Machine learning model inference
✅ **Multi-agent coordination** - Consensus algorithms
✅ **Risk management** - Advanced position sizing dan stop-loss

### **Total Pipeline**: <20ms vs traditional 50-100ms

---

## 📊 Data Format Specification

### **Protocol Buffers Schema Integration**:

#### **Schema Source**:
```
Source: ../backend/01-core-infrastructure/central-hub/shared/proto/trading/market_data.proto
Common: ../backend/01-core-infrastructure/central-hub/shared/proto/common/base.proto
Generated: client-mt5/03-communication/protobuf/generated/
```

#### **MarketDataStream Protocol Buffers Message** (From Server Schema Registry):
```protobuf
// From: trading/market_data.proto
message MarketDataStream {
  repeated TickData ticks = 1;          // MT5-compatible tick data
  repeated OHLCVBar bars = 2;           // OHLCV bar data (optional)
  MarketDepth depth = 3;                // Market depth (optional)
  string source = 4;                    // Data source ("MT5")
  int64 batch_sequence = 5;             // Batch sequence number
  int64 batch_time = 6;                 // Unix timestamp
  int64 batch_time_msc = 7;             // Unix timestamp with milliseconds
  string tenant_id = 8;                 // Multi-tenant isolation
}

// MT5 API Compatible Structure
message TickData {
  string symbol = 1;                    // Trading symbol (EURUSD, etc)

  // Official MT5 API fields
  double bid = 2;                       // Bid price
  double ask = 3;                       // Ask price
  double last = 4;                      // Last trade price
  int64 volume = 5;                     // Tick volume (MT5 integer)
  int64 time = 6;                       // Unix timestamp
  int64 time_msc = 7;                   // Unix timestamp with milliseconds
  int32 flags = 8;                      // MT5 tick flags
  double volume_real = 9;               // Real volume

  // Additional system fields
  string tenant_id = 10;                // Multi-tenant isolation
  int64 sequence_number = 11;           // Gap detection
  string source = 12;                   // Data source ("MT5")
  double spread = 13;                   // Calculated spread
}

// From: common/base.proto
message UserContext {
  string user_id = 1;
  string tenant_id = 2;                 // Company/tenant identifier
  string session_id = 3;
  repeated string roles = 4;
  map<string, string> permissions = 5;
}

message BaseMessage {
  string tenant_id = 1;                 // Required for multi-tenant isolation
  Timestamp timestamp = 2;             // Message creation time
  string correlation_id = 3;           // Request tracing ID
  string source_service = 4;           // "client-mt5"
  string message_version = 5;          // Schema version
}
```

### **Binary Serialization Benefits**:
```
Performance Comparison (1000 ticks):
JSON Serialization:    ~15ms + ~150KB data
Protobuf Serialization: ~1.5ms + ~60KB data

Network Benefits:
- 60% smaller payload size
- 10x faster serialization/deserialization
- Lower CPU usage on MT5 client
- Reduced WebSocket bandwidth usage
- Type safety dan schema validation
```

### **Sample Binary Data Flow**:
```cpp
// MT5 Expert Advisor Integration
#include "BatchTickData.pb.h"

// Create protobuf message using server schema registry
#include "trading/market_data.pb.h"
#include "common/base.pb.h"

// Create market data stream
trading::v1::MarketDataStream stream;
stream.set_source("MT5");
stream.set_batch_sequence(456);
stream.set_batch_time(GetTickCount());
stream.set_batch_time_msc(GetTickCount64());
stream.set_tenant_id("company_abc");

// Add MT5-compatible tick data
trading::v1::TickData* tick = stream.add_ticks();
tick->set_symbol("EURUSD");
tick->set_bid(1.08945);
tick->set_ask(1.08948);
tick->set_last(1.08946);          // MT5 last price
tick->set_volume(150);             // MT5 tick volume
tick->set_time(GetTickCount());    // MT5 time field
tick->set_time_msc(GetTickCount64()); // MT5 time_msc field
tick->set_flags(0x06);             // MT5 flags (bid+ask)
tick->set_tenant_id("company_abc");
tick->set_sequence_number(sequence++);
tick->set_source("MT5");
tick->set_spread(tick->ask() - tick->bid());

// Serialize to binary
std::string binary_data;
stream.SerializeToString(&binary_data);

// Send via WebSocket
websocket_client->send_binary(binary_data);
```

### **Monitored Symbol Pairs**:
```python
MAJOR_PAIRS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF",  # Major currencies
    "AUDUSD", "USDCAD", "NZDUSD",             # Commodity currencies
    "EURGBP", "EURJPY", "GBPJPY"              # Cross pairs
]
# Total: 10 pairs for comprehensive market correlation analysis
```

---

## 🛡️ Failover & Recovery Strategy

### **Triple Redundancy System**:
1. **Primary WebSocket**: Main connection ke backend data-bridge
2. **Backup WebSocket**: Secondary connection untuk failover
3. **Local Buffer**: Emergency storage (1000 ticks ≈ 3 minutes data)

### **Recovery Mechanisms**:
```python
# Connection Recovery Flow
Connection Lost → Local Buffer Activated → Alert Generated → Auto-Reconnect
      ↓                    ↓                    ↓               ↓
Data preserved       Continue processing    Ops notification   5-second retry
Quality maintained   No data loss          System monitoring   Connection restored
```

### **Quality Assurance**:
- **Health Monitoring**: Connection status, tick rate, processing latency
- **Auto-cleanup**: Memory management setiap 10 seconds
- **Performance Alerts**: Degradation detection dan notification
- **Data Integrity**: Checksum validation dan duplicate detection

---

## 🔗 Integration Points

### **Backend Communication**:
- **Data Bridge (8001)**: Real-time tick data streaming
- **API Gateway (8000)**: Authentication dan routing
- **User Service (8009)**: User context dan permissions

### **Previous Flow**: MT5 Terminal → Client-MT5 (hybrid processing)
**Next Flow**: Client-MT5 → Backend Data Processing → AI Analysis

---

## 🎯 Business Value

### **Performance Advantage**:
- **5x faster processing** vs pure server processing
- **10x lower bandwidth** dengan preprocessed data
- **99.9% uptime** dengan triple failover system

### **Scalability Benefits**:
- **Distributed processing** - Client handles local computation
- **Server efficiency** - Focus on AI/ML heavy lifting
- **Multi-user support** - Isolated processing per client

### **Trading Advantage**:
- **Ultra-low latency** - <20ms decision pipeline
- **Multi-pair analysis** - Comprehensive market view
- **Reliable execution** - Mission-critical failover system

---

**Key Innovation**: Hybrid preprocessing architecture yang optimize latency dengan distributed local processing sambil maintain centralized AI intelligence di server.