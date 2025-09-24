# Client-MT5 - Hybrid Local Processing

## 🎯 Purpose
**Hybrid preprocessing layer** yang handle MT5 integration dengan local processing untuk optimal <5ms latency, lalu streaming Protocol Buffers optimized data ke backend untuk AI analysis.

---

## 📊 ChainFlow Diagram

```
MT5 (10 Pairs) → Local Processing → Micro-batch → WebSocket → Backend Data Bridge
     ↓               ↓                ↓              ↓              ↓
Multi-threaded    Validation      5 ticks/100ms   Primary/Backup   Server AI
Symbol Monitor    Basic Indicators  Protobuf Binary Triple Failover   Decision Engine
50+ ticks/sec     SMA/EMA/RSI      Memory Buffer   Connection Pool   <15ms Response
                  Quality Metrics   60% Smaller    10x Faster       Optimized I/O
```

---

## 🏗️ Service Structure Overview

### **01-mt5-integration/ (2 modules)**

#### **api-connector/**
**Input Flow**: MT5 Terminal connection parameters
**Output Flow**: Raw tick streams untuk 10 major pairs
**Function**:
- MT5Handler initialization dengan login, password, server
- Multi-threaded symbol monitoring (10 pairs simultaneously)
- Connection management dan auto-reconnection
- Performance: 50+ ticks/second total (5 ticks/sec per pair)

#### **data-normalizer/**
**Input Flow**: Raw MT5 tick data dari multiple pairs
**Output Flow**: Normalized, validated tick data
**Function**:
- Tick validation (bid > 0, ask > bid, reasonable spread, volume > 0)
- Data normalization (timestamp UTC, decimal precision)
- Quality control dan error detection
- Performance: <1ms per tick processing

---

### **02-local-processing/ (3 modules)**

#### **data-validator/**
**Input Flow**: Normalized tick data dari data-normalizer
**Output Flow**: Validated ticks dengan quality metrics
**Function**:
- Real-time validation rules enforcement
- Spread validation (<100 points for major pairs)
- Timestamp validation (max 5 second delay)
- Volume validation dan outlier detection
- Quality scoring per tick dan symbol

#### **technical-indicators/**
**Input Flow**: Validated ticks dari data-validator
**Output Flow**: Basic indicators calculated locally
**Function**:
- **Local Indicators**: SMA(20,50), EMA(20,50), RSI(14)
- **Memory Management**: Keep 200 recent ticks per pair (40 minutes M1 data)
- **Multi-timeframe**: Real-time calculation untuk fast response
- **Performance**: <2ms indicator calculation per tick

#### **error-handler/**
**Input Flow**: Errors dari semua local processing modules
**Output Flow**: Handled errors, recovery actions, alerts
**Function**:
- ErrorDNA client implementation (dari ai_trading pattern)
- Connection lost recovery dan reconnection logic
- Data quality error handling dan alerting
- Performance degradation detection

---

### **03-communication/ (2 modules)**

#### **websocket-client/**
**Input Flow**: Processed tick data dengan indicators
**Output Flow**: WebSocket connection ke backend data-bridge
**Function**:
- **Primary Connection**: ws://backend:8001/api/v1/ws/mt5
- **Backup Connection**: ws://backup:8001/api/v1/ws/mt5
- JWT authentication untuk multi-user support
- Connection pooling dan load balancing

#### **data-streamer/**
**Input Flow**: Validated ticks dengan indicators dari local processing
**Output Flow**: Micro-batched Protocol Buffers binary data streams
**Function**:
- **Micro-batching**: 5 ticks per batch, max 100ms timeout
- **Protocol Buffers Format**: Binary structured data dengan type safety
- **Quality Metrics**: Processing time, validation stats
- **Performance**: 10 batches/second (50 ticks/second total)

---

## 🔄 Data Flow Chains

### **Chain 1: Real-time Multi-Pair Monitoring**
```
MT5 Terminal → API Connector (threaded) → Data Normalizer → Validator
    ↓              ↓                         ↓               ↓
10 Symbols     Async monitoring          UTC timestamps    Quality check
Live ticks     50+ ticks/second          Decimal norm      Error detection
```

### **Chain 2: Local Processing Pipeline**
```
Validated Ticks → Technical Indicators → Local Memory → Data Streamer
       ↓                ↓                    ↓              ↓
Quality scored    SMA/EMA/RSI calc     200 ticks buffer   Micro-batching
Error flagged     <2ms processing      Per-pair storage   Protobuf binary
```

### **Chain 3: WebSocket Streaming dengan Failover**
```
Micro-batches → WebSocket Client → Primary Connection → Backend Data Bridge
      ↓               ↓                ↓                      ↓
5 ticks/batch    JWT auth         Connection pool         Server processing
100ms timeout    Load balancing   Health monitoring       AI analysis
      ↓               ↓                ↓                      ↓
Local Buffer ← Backup Connection ← Connection Lost ← Failover Detection
```

---

## ⚡ Performance Targets & Achievements

### **Real-time Processing Performance**
- **Multi-pair Monitoring**: 50+ ticks/second (10 pairs × 5 ticks/sec)
- **Local Processing**: <5ms total (validation + indicators + batching)
- **WebSocket Streaming**: <100ms batch delivery
- **Memory Usage**: <50MB total client footprint

### **Reliability Targets**
- **Connection Uptime**: 99.9% dengan triple failover
- **Data Quality**: >99.5% valid ticks processed
- **Processing Success**: >99.8% successful local processing
- **Recovery Time**: <5 seconds untuk connection restoration

---

## 🔧 Key Technologies

### **MT5 Integration**
- **MetaTrader5 Python API**: Direct terminal integration
- **Custom C++ DLL**: Protocol Buffers serialization wrapper
- **Threading**: Async symbol monitoring untuk performance
- **Connection Pool**: Multiple MT5 connections untuk stability

### **Local Processing**
- **NumPy/Pandas**: Fast numerical computation
- **TA-Lib**: Technical analysis indicators
- **Asyncio**: Concurrent processing pipeline

### **Communication**
- **WebSocket**: Real-time bidirectional communication
- **Protocol Buffers**: Binary optimized data format (60% smaller, 10x faster)
- **Custom DLL Integration**: C++ wrapper untuk MT5 → Protobuf serialization
- **Schema Consistency**: Shared proto definitions dengan backend services
- **JWT**: Secure authentication dengan backend

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
    bool SerializeBatchData(const std::vector<TickData>& ticks, std::string& output);
    bool SendToWebSocket(const std::string& binary_data);
    bool ValidateConnection();
private:
    std::unique_ptr<WebSocketClient> ws_client_;
    BatchTickData current_batch_;
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
- **WebSocket Client**: websocketpp atau similar
- **MT5 Terminal API**: Compatible dengan MT5 build 3000+
- **Threading Support**: Multi-threaded tick processing

### **Installation Process**:
1. Compile TradingProtobuf.dll dengan Protocol Buffers support
2. Place DLL di MT5 Terminal/MQL5/Libraries/ folder
3. Install Expert Advisor di MT5 Terminal/MQL5/Experts/
4. Configure WebSocket endpoint dan authentication dalam EA settings
5. Enable DLL imports dalam MT5 Terminal options

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
Source: ../backend/01-core-infrastructure/central-hub/shared/proto/common/tick-data.proto
Generated: client-mt5/03-communication/protobuf/generated/
```

#### **BatchTickData Protocol Buffers Message**:
```protobuf
message BatchTickData {
  repeated TickData ticks = 1;         // Pre-processed tick data
  string user_id = 2;                  // User identifier
  int32 batch_id = 3;                  // Batch sequence number
  int64 batch_timestamp = 4;           // Batch creation time (Unix ms)
  QualityMetrics quality = 5;          // Client-side quality metrics
  string company_id = 6;               // Multi-tenant company ID
  SubscriptionTier tier = 7;           // User subscription tier
}

message TickData {
  string symbol = 1;                   // Trading pair ("EURUSD")
  double bid = 2;                      // Bid price
  double ask = 3;                      // Ask price
  int64 timestamp = 4;                 // Tick timestamp (Unix ms)
  int32 volume = 5;                    // Tick volume
  double spread = 6;                   // Calculated spread
  TechnicalIndicators indicators = 7;  // Local-computed indicators
}

message TechnicalIndicators {
  double sma_20 = 1;                   // Simple Moving Average
  double ema_20 = 2;                   // Exponential Moving Average
  double rsi_14 = 3;                   // Relative Strength Index
  double bb_upper = 4;                 // Bollinger Band Upper
  double bb_lower = 5;                 // Bollinger Band Lower
}

message QualityMetrics {
  int32 validation_passed = 1;         // Successfully validated ticks
  int32 validation_failed = 2;         // Failed validation ticks
  double processing_time_ms = 3;       // Local processing time
  double confidence_score = 4;         // Overall data confidence (0.0-1.0)
  int32 missed_ticks = 5;              // Number of missed ticks
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

// Create protobuf message
BatchTickData batch;
batch.set_user_id("user123");
batch.set_batch_id(456);
batch.set_batch_timestamp(GetTickCount64());

// Add tick data
TickData* tick = batch.add_ticks();
tick->set_symbol("EURUSD");
tick->set_bid(1.08945);
tick->set_ask(1.08948);
tick->set_volume(150);
tick->set_timestamp(GetTickCount64());

// Add technical indicators
TechnicalIndicators* indicators = tick->mutable_indicators();
indicators->set_sma_20(1.08950);
indicators->set_ema_20(1.08947);
indicators->set_rsi_14(65.4);

// Serialize to binary
std::string binary_data;
batch.SerializeToString(&binary_data);

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