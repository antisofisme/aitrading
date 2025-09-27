# Input Contract: Client-MT5 → API Gateway

## Purpose
Client-MT5 mengirim trading data, price streams, dan account information ke API Gateway menggunakan Suho Binary Protocol via dual WebSocket channels.

## Protocol
**Format**: Suho Binary Protocol (144-byte fixed packets)
**Transport**: Dual WebSocket channels
**Authentication**: JWT token saat connection establishment

## Data Flow
1. Client-MT5 → Dual WebSocket connection → API Gateway
2. API Gateway receives Suho Binary Protocol (no conversion)
3. Route raw binary data to Data Bridge for processing

## Current Architecture
- **Primary Route**: All Client-MT5 data → Data Bridge (binary passthrough)
- **Future Route**: Flexible routing to multiple backend services when needed

## WebSocket Channels

### **Channel 1: Trading Commands** (ws://localhost:8001/ws/trading)
Handle trading operations, account data, dan execution confirmations.

### **Channel 2: Price Streaming** (ws://localhost:8002/ws/price-stream)
Handle real-time market data streaming dan symbol subscriptions.

## Suho Binary Protocol Schema

### **Packet Header (16 bytes)**
```cpp
struct SuhoBinaryHeader {
    uint32  magic;        // 4 bytes - 0x53554854 "SUHO"
    uint16  version;      // 2 bytes - 0x0001
    uint8   msg_type;     // 1 byte  - Message type enum
    uint8   data_count;   // 1 byte  - Number of data items
    uint64  timestamp;    // 8 bytes - Microsecond precision
};
```

### **Message Types**
```cpp
enum MessageTypes {
    PRICE_STREAM = 0x01,      // Real-time price data
    ACCOUNT_PROFILE = 0x02,   // Account information
    TRADING_COMMAND = 0x03,   // Trading execution requests
    EXECUTION_CONFIRM = 0x04, // Trade confirmation
    SYSTEM_STATUS = 0x05,     // System health data
    HEARTBEAT = 0x06          // Connection keepalive
};
```

## Message Structures

### **1. Price Stream Data (Channel 2)**
```cpp
// Price Packet (16 bytes per symbol)
struct PricePacket {
    uint32  symbol_id;    // 4 bytes - EURUSD=1, GBPUSD=2, etc.
    uint32  bid_price;    // 4 bytes - Fixed point (*100000)
    uint32  ask_price;    // 4 bytes - Fixed point (*100000)
    uint32  meta_flags;   // 4 bytes - Spread + server_id + quality
};
```

**Example Binary Data Flow:**
```
Client-MT5 → Binary packet (144 bytes) → API Gateway → Parse → Protocol Buffer
EURUSD: 1.09551/1.09553 → 109551/109553 (fixed point) → MarketData protobuf
```

### **2. Account Profile Data (Channel 1)**
```cpp
// Account Snapshot (64 bytes)
struct AccountSnapshot {
    char    user_id[16];     // 16 bytes - User identifier
    char    broker[16];      // 16 bytes - Broker name
    uint32  account_num;     // 4 bytes  - MT5 account number
    uint32  balance_fp;      // 4 bytes  - Balance * 100
    uint32  equity_fp;       // 4 bytes  - Equity * 100
    uint32  margin_fp;       // 4 bytes  - Used margin * 100
    uint32  free_margin_fp;  // 4 bytes  - Free margin * 100
    uint16  leverage;        // 2 bytes  - Leverage ratio
    char    currency[3];     // 3 bytes  - Account currency
    uint8   reserved;        // 1 byte   - Alignment padding
    uint64  snapshot_time;   // 8 bytes  - Snapshot timestamp
};
```

### **3. Trading Command Data (Channel 1)**
```cpp
// Trading Command (32 bytes)
struct TradingCommand {
    uint32  command_id;      // 4 bytes - Unique command ID
    uint32  symbol_id;       // 4 bytes - Trading symbol
    uint8   action;          // 1 byte  - BUY=0, SELL=1, CLOSE=2
    uint32  volume_fp;       // 4 bytes - Lot size * 100
    uint32  price_fp;        // 4 bytes - Entry price * 100000
    uint32  stop_loss_fp;    // 4 bytes - Stop loss * 100000
    uint32  take_profit_fp;  // 4 bytes - Take profit * 100000
    uint32  magic_number;    // 4 bytes - EA magic number
    uint8   reserved[3];     // 3 bytes - Alignment padding
};
```

### **4. Execution Confirmation (Channel 1)**
```cpp
// Execution Confirmation (32 bytes)
struct ExecutionConfirm {
    uint32  ticket;          // 4 bytes - MT5 ticket number
    uint32  command_id;      // 4 bytes - Original command ID
    uint8   result;          // 1 byte  - SUCCESS=0, ERROR=1
    uint32  executed_price;  // 4 bytes - Actual execution price
    uint32  executed_volume; // 4 bytes - Actual volume executed
    uint16  error_code;      // 2 bytes - MT5 error code if failed
    uint64  execution_time;  // 8 bytes - Execution timestamp
    uint8   reserved[9];     // 9 bytes - Alignment padding
};
```

## Symbol Enumeration
```cpp
enum TradingSymbols {
    EURUSD = 1,    // EUR/USD
    GBPUSD = 2,    // GBP/USD
    USDJPY = 3,    // USD/JPY
    USDCHF = 4,    // USD/CHF
    AUDUSD = 5,    // AUD/USD
    USDCAD = 6,    // USD/CAD
    NZDUSD = 7,    // NZD/USD
    XAUUSD = 8,    // Gold
    XAGUSD = 9,    // Silver
    UNKNOWN = 255   // Invalid/unsupported symbol
};
```

## Processing Requirements

### **Validation Rules**
- **Magic Number**: Must be 0x53554854 ("SUHO")
- **Protocol Version**: Must be 0x0001
- **Timestamp**: Within 60 seconds of current time (prevent replay)
- **Message Size**: Fixed size validation per message type
- **Symbol Range**: Valid symbol ID (1-9, 255 for unknown)

### **Performance Targets**
- **Parsing Time**: <0.5ms per packet
- **Validation Time**: <0.1ms per packet
- **Protocol Conversion**: <0.3ms binary → protobuf
- **Total Processing**: <1ms end-to-end per message

### **Error Handling**
- **Invalid Magic**: Immediate connection termination
- **Protocol Mismatch**: Send error response, maintain connection
- **Timestamp Old**: Drop packet, log warning
- **Parse Error**: Send error response, maintain connection
- **Unknown Symbol**: Map to UNKNOWN, continue processing

## Output Routing

### **Price Stream Data Routes To:**
- **ML Processing Service**: Real-time analysis
- **Analytics Service**: Performance tracking
- **Data Bridge**: Historical storage

### **Account Profile Routes To:**
- **Analytics Service**: Account monitoring
- **User Management**: Account validation
- **Central Hub**: User context updates

### **Trading Commands Route To:**
- **Trading Engine**: Signal processing
- **Analytics Service**: Trading statistics
- **Notification Hub**: Trade alerts

### **Execution Confirmations Route To:**
- **Trading Engine**: Execution tracking
- **Analytics Service**: Performance metrics
- **Frontend Dashboard**: Real-time updates

## Security Requirements

### **Connection Security**
- **WSS Protocol**: TLS encryption for all WebSocket connections
- **JWT Authentication**: Valid token required for connection
- **Rate Limiting**: Max 100 messages/second per user
- **Connection Limits**: Max 2 concurrent connections per user

### **Data Security**
- **User Isolation**: Strict per-user data separation
- **Audit Trail**: Log all trading commands and confirmations
- **Data Sanitization**: Remove sensitive info from logs
- **Access Control**: Validate user permissions per symbol

### **Protocol Security**
- **Packet Validation**: Comprehensive binary validation
- **Replay Protection**: Timestamp-based duplicate detection
- **Buffer Overflow**: Fixed-size structures prevent overflows
- **Magic Number**: Instant invalid protocol detection

## Performance Optimization

### **Binary Protocol Benefits**
- **Bandwidth**: 75.8% reduction vs JSON (144 vs 596 bytes)
- **Processing**: 63.2% faster parsing vs JSON
- **Memory**: Fixed allocation, zero fragmentation
- **Network**: Single TCP packet for most messages

### **WebSocket Optimization**
- **Dual Channels**: Separate trading/price streams for performance
- **Connection Pooling**: Efficient WebSocket management
- **Auto-Reconnection**: Intelligent failover and recovery
- **Heartbeat**: 30-second keepalive for connection health

### **Caching Strategy**
- **User Authentication**: 5-minute cache for JWT validation
- **Symbol Mapping**: Permanent cache for symbol ID lookups
- **Rate Limits**: In-memory counters for performance
- **Connection State**: Efficient connection metadata storage

## Monitoring & Metrics

### **Connection Metrics**
- **Active Connections**: Real-time connection count
- **Protocol Distribution**: Binary vs JSON usage
- **Channel Usage**: Trading vs price stream activity
- **Authentication Success**: Login success/failure rates

### **Performance Metrics**
- **Message Throughput**: Messages per second per channel
- **Processing Latency**: Parse time percentiles
- **Error Rates**: Invalid packet percentage
- **Memory Usage**: Connection overhead tracking

### **Business Metrics**
- **Trading Volume**: Orders per user per day
- **Price Data Volume**: Ticks processed per symbol
- **User Activity**: Active trading sessions
- **Symbol Popularity**: Most traded pairs

## Example Data Flows

### **Price Stream Flow**
```
1. Client-MT5 → WebSocket Channel 2 → API Gateway
   Data: EURUSD 1.09551/1.09553 (144 bytes binary)

2. API Gateway → Parse Binary → Validate
   Header: magic=SUHO, type=PRICE_STREAM, count=1

3. API Gateway → Convert to Protocol Buffer
   MarketData: symbol="EURUSD", bid=1.09551, ask=1.09553

4. API Gateway → Route to Backend Services:
   ├── ML Processing (real-time analysis)
   ├── Analytics Service (performance tracking)
   └── Data Bridge (historical storage)
```

### **Trading Command Flow**
```
1. Client-MT5 → WebSocket Channel 1 → API Gateway
   Data: BUY EURUSD 0.1 lot @ 1.09551 (32 bytes binary)

2. API Gateway → Parse Binary → Validate
   Command: symbol=EURUSD, action=BUY, volume=0.1

3. API Gateway → Convert to Protocol Buffer
   TradingCommand: symbol="EURUSD", action="BUY", volume=0.1

4. API Gateway → Route to Backend Services:
   ├── Trading Engine (signal processing)
   ├── Analytics Service (trade tracking)
   └── Notification Hub (user alerts)
```

## Error Response Format

### **Binary Error Response**
```cpp
struct ErrorResponse {
    uint32  magic;           // 4 bytes - 0x53554854 "SUHO"
    uint16  version;         // 2 bytes - 0x0001
    uint8   msg_type;        // 1 byte  - ERROR_MESSAGE
    uint8   error_count;     // 1 byte  - Number of errors
    uint64  timestamp;       // 8 bytes - Response timestamp
    uint16  error_code;      // 2 bytes - Error classification
    char    error_msg[32];   // 32 bytes - Error description
    uint8   reserved[14];    // 14 bytes - Padding to 64 bytes
};
```

### **Error Codes**
```cpp
enum ErrorCodes {
    INVALID_MAGIC = 1001,      // Wrong magic number
    PROTOCOL_VERSION = 1002,   // Unsupported version
    TIMESTAMP_OLD = 1003,      // Packet too old
    PARSE_ERROR = 1004,        // Binary parse failure
    UNKNOWN_SYMBOL = 1005,     // Invalid symbol ID
    RATE_LIMITED = 1006,       // Too many messages
    AUTH_FAILED = 1007,        // Authentication error
    SYSTEM_ERROR = 1008        // Internal server error
};
```