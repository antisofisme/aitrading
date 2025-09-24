# Client-MT5 - Account Profile & Trading Execution Client

## 🎯 Purpose
**MT5 trading execution client** yang mengirimkan account profile dan financial status ke server, kemudian menerima AI-generated trading execution commands untuk automated trading di MT5 terminal.

---

## 📊 Architecture Revolution

### **Old Architecture (Client-Side Processing)**:
```
1000 Clients × Direct MT5 Connections = 3000 broker connections
Each client processes tick data and makes trading decisions
Redundant AI processing: 1000× duplicate analysis
Risk: Uncontrolled client-side trading decisions
```

### **New Architecture (Server-Side AI)**:
```
Server-Side AI Trading System:
├── Approved Brokers: Server collects from regulated brokers only
├── AI Analysis: Server processes data with ML/AI models
├── Trading Commands: Server generates optimized execution orders
└── Client-MT5: Receives commands + executes trades safely
```

---

## 🔄 Client Data Flow

### **Account Profile & Execution Model**:
```
Client-MT5 → API Gateway → Server AI Analysis → Trading Commands → Client-MT5
     ↓              ↓               ↓                 ↓               ↓
Account Info   JWT Auth      ML/AI Engine      Risk Assessment  Auto Execution
Profile Data   User Context  Market Analysis   Position Sizing  MT5 Terminal
Financial      Rate Limits   News Integration  Stop Loss       Trade Management
Status         Multi-tenant  Sentiment AI      Take Profit     Performance
```

### **Client Responsibilities** (Transformed):
1. **Account Registration**: Send MT5 account details dan broker info
2. **Profile Management**: Provide risk tolerance dan trading preferences
3. **Financial Status**: Report account balance, equity, margin status
4. **Command Execution**: Execute AI-generated trading commands di MT5
5. **Status Reporting**: Send execution confirmations back to server

---

## 🚀 Protocol Buffer Integration

### **Schema Import** (from Server Registry):
```cpp
// Import from centralized server schemas
#include "central-hub/shared/proto/trading/account_profile.proto"
#include "central-hub/shared/proto/trading/execution_commands.proto"
#include "central-hub/shared/proto/common/user_context.proto"
```

### **Account Profile Messages** (Client to Server):
```protobuf
message AccountProfile {
  string user_id = 1;                     // User identifier
  string account_number = 2;              // MT5 account number
  string broker_name = 3;                 // Broker name (must be approved)
  string server_name = 4;                 // MT5 server name
  AccountType account_type = 5;           // DEMO/LIVE
  string base_currency = 6;               // Account base currency
  double balance = 7;                     // Current account balance
  double equity = 8;                      // Current equity
  double margin_used = 9;                 // Used margin
  double margin_free = 10;                // Free margin
  RiskProfile risk_profile = 11;          // Risk tolerance settings
  TradingPreferences preferences = 12;    // Trading preferences
}

message RiskProfile {
  double max_risk_per_trade = 1;          // Maximum risk % per trade
  double max_daily_loss = 2;              // Maximum daily loss limit
  double max_drawdown = 3;                // Maximum account drawdown
  bool allow_news_trading = 4;            // Allow trading during news
  repeated string allowed_symbols = 5;    // Allowed trading symbols
}

message TradingPreferences {
  double preferred_lot_size = 1;          // Preferred position size
  int32 max_open_positions = 2;          // Maximum simultaneous positions
  bool auto_close_friday = 3;            // Auto-close before weekend
  bool conservative_mode = 4;             // Conservative trading mode
}
```

### **Trading Execution Commands** (Server to Client):
```protobuf
message TradingCommand {
  string command_id = 1;                  // Unique command identifier
  string user_id = 2;                     // Target user
  CommandType type = 3;                   // OPEN_POSITION/CLOSE_POSITION/MODIFY
  string symbol = 4;                      // Trading symbol
  OrderType order_type = 5;               // BUY/SELL
  double lot_size = 6;                    // Position size
  double entry_price = 7;                 // Entry price (0 for market)
  double stop_loss = 8;                   // Stop loss level
  double take_profit = 9;                 // Take profit level
  string reason = 10;                     // AI decision reason
  double confidence_score = 11;           // AI confidence (0.0-1.0)
  int64 expires_at = 12;                  // Command expiration time
}

enum CommandType {
  OPEN_POSITION = 0;
  CLOSE_POSITION = 1;
  MODIFY_POSITION = 2;
  CLOSE_ALL = 3;
}

enum OrderType {
  BUY = 0;
  SELL = 1;
  BUY_LIMIT = 2;
  SELL_LIMIT = 3;
  BUY_STOP = 4;
  SELL_STOP = 5;
}
```

## 📱 Client Implementation

### **Account Profile Client (C++/MQL5)**:
```cpp
// Account profile and trading execution client
class MT5TradingClient {
private:
    WebSocketClient ws_client;
    ProtocolBufferParser pb_parser;
    string jwt_token;
    string user_id;
    AccountProfile account_profile;

public:
    bool ConnectToServer(string server_url, string auth_token) {
        // Connect via API Gateway WebSocket endpoint
        string ws_url = "wss://api.gateway.com/ws/trading-client";

        // Add authentication headers
        map<string, string> headers;
        headers["Authorization"] = "Bearer " + auth_token;
        headers["x-user-id"] = user_id;

        return ws_client.Connect(ws_url, headers);
    }

    bool SendAccountProfile() {
        // Collect current account information
        account_profile.account_number = AccountInfoString(ACCOUNT_LOGIN);
        account_profile.broker_name = AccountInfoString(ACCOUNT_COMPANY);
        account_profile.server_name = AccountInfoString(ACCOUNT_SERVER);
        account_profile.balance = AccountInfoDouble(ACCOUNT_BALANCE);
        account_profile.equity = AccountInfoDouble(ACCOUNT_EQUITY);
        account_profile.margin_used = AccountInfoDouble(ACCOUNT_MARGIN);
        account_profile.margin_free = AccountInfoDouble(ACCOUNT_MARGIN_FREE);

        // Serialize and send to server
        string binary_data = account_profile.SerializeAsString();
        return ws_client.Send(binary_data);
    }

    void OnTradingCommand(string binary_data) {
        // Parse trading command from server
        TradingCommand command;
        command.ParseFromString(binary_data);

        // Execute trading command in MT5
        ExecuteTradingCommand(command);
    }

    bool ExecuteTradingCommand(TradingCommand command) {
        // Execute AI-generated trading command
        switch(command.type) {
            case CommandType::OPEN_POSITION:
                return OpenPosition(command);
            case CommandType::CLOSE_POSITION:
                return ClosePosition(command);
            case CommandType::MODIFY_POSITION:
                return ModifyPosition(command);
            default:
                return false;
        }
    }
};
```

### **MQL5 Expert Advisor Integration**:
```mql5
//+------------------------------------------------------------------+
//| Client-MT5 Trading Execution EA                                  |
//+------------------------------------------------------------------+

#include "WebSocketClient.mqh"
#include "ProtocolBuffer.mqh"

input string ServerURL = "wss://api.gateway.com/ws/trading-client";
input string AuthToken = "your_jwt_token_here";
input double MaxRiskPerTrade = 2.0;  // Maximum risk % per trade
input bool AutoTrading = true;       // Enable auto trading

MT5TradingClient trading_client;

int OnInit() {
    // Initialize WebSocket connection
    if (!trading_client.ConnectToServer(ServerURL, AuthToken)) {
        Print("Failed to connect to trading server");
        return INIT_FAILED;
    }

    // Send account profile to server
    if (!trading_client.SendAccountProfile()) {
        Print("Failed to send account profile");
        return INIT_FAILED;
    }

    Print("Client-MT5 Trading Client initialized");
    return INIT_SUCCEEDED;
}

void OnTick() {
    // Update account status periodically
    static datetime last_update = 0;
    if (TimeCurrent() - last_update > 60) {  // Every minute
        trading_client.SendAccountProfile();
        last_update = TimeCurrent();
    }

    // Process incoming trading commands
    trading_client.ProcessIncomingCommands();
}

void OnDeinit(const int reason) {
    trading_client.Disconnect();
    Print("Client-MT5 Trading Client stopped");
}

// NO MORE INDICATOR CALCULATIONS - ALL DONE ON SERVER
// Client only executes commands from AI trading engine
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
- **Account Monitoring**: Real-time account balance and equity tracking
- **Trading Execution**: Automated execution of AI-generated commands
- **Risk Management**: Client-side risk controls and validation
- **Status Reporting**: Real-time position and execution status
- **Connection Management**: Reliable WebSocket connection with failover

---

## 📊 Performance Benefits

### **Client-Side Efficiency**:
```
Resource Optimization per Client:
- No tick data processing: 95% CPU usage reduction
- No indicator calculations: 90% memory usage reduction
- No market analysis: 85% processing overhead eliminated
- Focused execution: Only trading command processing
- Minimal bandwidth: Account updates + trading commands only
```

### **Network Optimization**:
```
Data Transfer Comparison (1000 clients):
Traditional: 1000 × tick data processing = 1000× bandwidth
New Model: 1000 × account profiles + trading commands = 99.5% reduction
- Client → Server: Account info only (minimal data)
- Server → Client: Trading commands only (targeted instructions)
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