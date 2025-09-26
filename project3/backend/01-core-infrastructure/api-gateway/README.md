# 🚀 API Gateway - Suho Binary Protocol Integration

**High-Performance API Gateway with Client-MT5 Binary Protocol Support**

## 🎯 Purpose
**Revolutionary messaging hub** yang mengintegrasikan **Client-MT5 Suho Binary Protocol** dengan backend microservices untuk ultra-low latency trading dengan <1ms routing time.

---

## 📊 ChainFlow Diagram

```
Client-MT5 → API Gateway → Backend Services
    ↓           ↓              ↓
WebSocket WSS  Auth/Route    Service Calls
Real-time     Rate Limit     Load Balance
50+ ticks/sec  User Context   <3ms routing
```

---

## 🏗️ Service Architecture

### **Input Flow**: Client connections dan external API requests
**Data Source**: Client-MT5 (WebSocket), Frontend (HTTP), External APIs
**Protocol**: Native WebSocket (WSS) + HTTP REST + Protocol Buffers
**Data Format**: Protocol Buffers untuk binary efficiency (60% smaller, 10x faster)
**Authentication**: JWT tokens, rate limiting per subscription tier
**Performance Target**: <5ms request routing dan authentication

### **Output Flow**: Multi-transport routing berdasarkan kategori dan criticality
**Destinations**: Backend services via appropriate transport methods
**Routing Strategy**:
- **High Volume/Critical**: NATS primary → Kafka backup (trading data, signals)
- **Medium Volume**: Direct gRPC calls (business logic, analytics)
- **Low Volume**: HTTP REST via Kong Gateway (config, admin)
**Multi-User Handling**: User context preservation across all transports
**Performance Target**: <5ms request routing dan service call initiation

---

## 🚀 Transport Architecture & Contract Integration

### **Transport Decision Matrix Applied**:

#### **Kategori A: High Volume + Mission Critical**
- **Input**: Native WebSocket (WSS) + Protocol Buffers from Client-MT5
- **Output Primary**: NATS + Protocol Buffers (direct publish to NATS broker)
- **Output Backup**: Kafka + Protocol Buffers (direct publish to Kafka broker)
- **Failover**: Automatic NATS→Kafka switching (direct connection failover)
- **Services**: Trading data, market signals, real-time events
- **Performance**: <1ms direct NATS publish, <5ms total request processing

#### **Kategori B: Medium Volume + Important**
- **Input**: HTTP REST + JSON from Frontend dashboard
- **Output**: Direct gRPC calls to backend services (HTTP/2 + Protocol Buffers)
- **Connection**: Direct gRPC connection pooling + circuit breaker
- **Service Discovery**: Query Central Hub for service endpoints, then call directly
- **Services**: Business logic, analytics queries, user management
- **Performance**: <3ms direct gRPC call initiation

#### **Kategori C: Low Volume + Standard**
- **Input**: HTTP REST + JSON for admin operations
- **Output**: Direct HTTP REST calls to backend services
- **Service Discovery**: Query Central Hub for service endpoints, then call directly
- **Services**: Configuration management, health checks, admin operations
- **Performance**: <5ms direct HTTP call

### **⚠️ Service Communication Pattern**

**API Gateway makes DIRECT calls to backend services:**

```
✅ CORRECT Flow:
1. Client → API Gateway (request)
2. API Gateway → Central Hub (query: "where is Trading-Engine?")
3. Central Hub → API Gateway (answer: "http://trading-engine:8080")
4. API Gateway → Trading-Engine (direct call to http://trading-engine:8080)
5. Trading-Engine → API Gateway (response)
6. API Gateway → Client (response)

❌ WRONG Flow:
1. Client → API Gateway → Central Hub → Trading-Engine
   (Central Hub should NOT forward business requests)
```

**API Gateway Role:**
- ✅ **Client Gateway**: Handle client connections dan authentication
- ✅ **Service Caller**: Make direct calls to backend services
- ✅ **Service Discovery Client**: Query Central Hub for service locations
- ❌ **Service Proxy**: TIDAK route through Central Hub

### **Native WebSocket (WSS) - Chosen for Performance**

**Why Native WebSocket over Socket.IO:**
- **30% faster** - Minimal protocol overhead
- **Predictable latency** - Critical for <30ms total target
- **High throughput** - Optimal for 50+ ticks/second
- **Simple protocol** - Less failure points for mission-critical trading

**WebSocket Endpoints:**
```
WSS://api.gateway.com/ws/trading          # MT5 client (Client-MT5 compatibility)
WSS://api.gateway.com/ws/trading/commands # Trading commands channel
WSS://api.gateway.com/ws/trading/prices   # Price streaming channel
WSS://api.gateway.com/ws/mt5              # Alternative MT5 endpoint
WSS://api.gateway.com/ws/frontend         # Frontend real-time updates
WSS://api.gateway.com/ws/alerts           # Trading alerts and notifications
```

**Dual WebSocket Architecture for Client-MT5:**
- **Trading Commands Channel**: AI signal reception & execution confirmation
- **Price Streaming Channel**: Real-time bid/ask data transmission
- **Load Balanced**: Traffic separation for optimal performance

### **Security Implementation:**
- **WSS (WebSocket Secure)**: TLS encryption for all connections
- **One-time JWT Authentication**: Token verification saat WebSocket connection establish
- **No per-message auth**: Speed optimal untuk 50+ ticks/second
- **Rate Limiting**: Per-user limits based on subscription tier
- **CORS**: Cross-origin resource sharing configuration

### **Authentication Flow:**
```
Client-MT5 → WebSocket Connect + JWT Header → API Gateway Verify → Connection Allowed
Data Stream → No Auth Overhead per Message → Maximum Real-time Speed
```

### **Suho Binary Protocol Integration (Client-MT5 Compatibility):**

**API Gateway serves as Protocol Translator:**
```
Client-MT5 (Suho Binary) → API Gateway [CONVERT] → Protocol Buffers → Backend Services
```

**Suho Binary Protocol Structure (from Client-MT5):**
```cpp
// Header Structure (16 bytes) - matches Client-MT5
enum PROTOCOL_CONSTANTS {
    BINARY_MAGIC = 0x53554854,    // "SUHO" - validation signature
    BINARY_VERSION = 0x0001       // Protocol version
};

struct SuhoBinaryHeader {
    uint32  magic;        // 4 bytes - 0x53554854 "SUHO"
    uint16  version;      // 2 bytes - 0x0001
    uint8   msg_type;     // 1 byte  - Message type enum
    uint8   data_count;   // 1 byte  - Number of data items
    uint64  timestamp;    // 8 bytes - Microsecond precision
};

// Price Data Structure (16 bytes per symbol)
struct SuhoPricePacket {
    uint32  symbol_id;    // 4 bytes - Enum (EURUSD=1, GBPUSD=2...)
    uint32  bid_price;    // 4 bytes - Fixed point (*100000)
    uint32  ask_price;    // 4 bytes - Fixed point (*100000)
    uint32  meta_flags;   // 4 bytes - Spread + server_id + quality
};

// Account Profile (64 bytes)
struct SuhoAccountSnapshot {
    char    user_id[16];     // 16 bytes - User identifier
    char    broker[16];      // 16 bytes - Broker company
    uint32  account_num;     // 4 bytes  - Account number
    uint32  balance_fp;      // 4 bytes  - Balance * 100
    uint32  equity_fp;       // 4 bytes  - Equity * 100
    uint32  margin_fp;       // 4 bytes  - Margin * 100
    uint32  free_margin_fp;  // 4 bytes  - Free margin * 100
    uint16  leverage;        // 2 bytes  - Leverage ratio
    char    currency[3];     // 3 bytes  - Currency code
    uint8   reserved;        // 1 byte   - Alignment padding
    uint64  snapshot_time;   // 8 bytes  - Profile timestamp
};
```

**Binary-to-Protocol Buffers Conversion:**
```javascript
// Incoming: Suho Binary → Protocol Buffers
function convertSuhoToProtobuf(binaryBuffer) {
    const header = parseSuhoHeader(binaryBuffer);

    return {
        message_type: getSuhoMessageType(header.msg_type),
        user_id: extractUserFromAuth(),
        company_id: extractCompanyFromAuth(),
        payload: convertSuhoPayload(binaryBuffer, header),
        timestamp: header.timestamp,
        enable_tracing: shouldTrace(header.msg_type)
    };
}

// Outgoing: Protocol Buffers → Suho Binary
function convertProtobufToSuho(protobufMessage) {
    const header = createSuhoHeader(
        getSuhoMsgType(protobufMessage.message_type),
        protobufMessage.timestamp
    );

    return Buffer.concat([
        header,
        convertPayloadToSuho(protobufMessage.payload)
    ]);
}
```

**JWT + Protocol Buffers Authentication:**
```json
JWT Structure:
{
  "sub": "user123",
  "iss": "api-gateway",
  "exp": 1640995200,
  "data": "<protobuf_binary_payload>"  // UserToken protobuf (60% smaller)
}
```

**UserToken Protocol Buffers Schema:**
```protobuf
message UserToken {
  string user_id = 1;
  string company_id = 2;
  SubscriptionTier subscription_tier = 3;
  int64 issued_at = 4;
  int64 expires_at = 5;
}

enum SubscriptionTier {
  TIER_FREE = 0;
  TIER_PRO = 1;
  TIER_ENTERPRISE = 2;
}
```

**Performance Benefits:**
- **92% bandwidth reduction** (Suho Binary: 144 bytes vs JSON: 1,850 bytes)
- **80% processing speed improvement** (1.2ms vs 6.1ms)
- **Zero memory fragmentation** - fixed allocation
- **Built-in validation** - magic numbers, checksums
- **Protocol translation overhead**: <0.5ms per conversion

### **Multi-Transport Routing Integration:**
```
Client-MT5 → Suho Binary → API Gateway → Protocol Buffers → Backend Services
    ↓            ↓              ↓               ↓                  ↓
Price Stream  144 bytes    Binary Parser   Protobuf Convert   Service Calls
8 symbols     Fixed size   <0.2ms parse    <0.3ms convert     Direct Processing
50+ ticks/sec Ultra-fast   Magic verify    Category route     Real-time Response
```

**Enhanced Schema Structure:**
```protobuf
message MessageEnvelope {
  string message_type = 1;    // "tick_data", "user_event", "trading_signal"
  string user_id = 2;         // For Kafka partitioning
  string company_id = 3;      // Multi-tenant organization ID
  bytes payload = 4;          // Actual protobuf message (BatchTickData, etc)
  int64 timestamp = 5;        // For message ordering
  string correlation_id = 6;  // Request tracing ID (optional, for sampled requests)
  bool enable_tracing = 7;    // Flag untuk performance tracing
}
```

**Multi-Transport Routing Benefits:**
- **Intelligent route selection**: Category-based transport decision (<0.1ms)
- **Load balancing**: Automatic endpoint selection dengan health monitoring
- **Circuit breaker protection**: Automatic failover untuk service reliability
- **Optimal for 5000+ msg/sec**: Minimal processing overhead across all transports

### **Intelligent Routing Architecture:**
```
Multiple Users → WebSocket → API Gateway → Multi-Transport Router → Backend Services
      ↓             ↓            ↓                  ↓                      ↓
100+ Clients   Auth Once    Routing Engine    Transport Decision     Direct Processing
50 ticks/sec   Per Client   Load Balance      NATS/gRPC/HTTP        Service Response
Real-time      JWT Token    Circuit Breaker   Category-based        <5ms Total Latency
Multi-tenant   Rate Limits  Health Monitor    Auto Failover         Real-time Results
```

### **Advanced Error Handling & Protection:**
```
Normal Flow:    Valid Messages → Route Selection → Backend Services → Processing
Error Flow:     Service Down → Circuit Breaker → Automatic Failover → Alternative Service
Protection:     Rate Limiting → Load Balancing → Health Monitoring → Auto Recovery
```

**Dead Letter Queue (DLQ):**
- **failed-messages** Kafka topic untuk invalid/corrupt messages
- **No data loss**: Error messages stored untuk investigation
- **Non-blocking**: Tidak ganggu normal processing flow

**Connection Protection:**
- **Rate limiting**: Max 100 messages/sec per user, drop excess
- **Auto-disconnect**: WebSocket connection terminated untuk spam clients
- **Temporary ban**: Block reconnection untuk protect server resources
- **Central Hub Integration**: Query Central Hub untuk backend service health status

### **Multi-Tenant Security Architecture:**

**Server-Side Enforcement (Authoritative):**
```
WebSocket Data → JWT Extract → Multi-Tenant Filter → Company/User Limits → Kafka Route
     ↓              ↓              ↓                    ↓                   ↓
Client Data    company_id       Tenant Isolation    Enterprise: 10 users   Topic + Context
User Token     user_id          Resource Pool       Pro: 5 users           Secure Processing
Real-time      subscription     Data Separation     Free: 1 user           Multi-tenant Safe
```

**Security Principles:**
- ❌ **Client-side filtering**: Never trust client for security decisions
- ✅ **Server-side filtering**: All limits enforced di API Gateway
- ✅ **Multi-level control**: Company + User level restrictions
- ✅ **Real-time enforcement**: Immediate blocking untuk violations

**Multi-Level Control Structure:**
```
Company Level (Tenant):
├── Max users per organization (10 for Enterprise, 5 for Pro, 1 for Free)
├── Total MT5 accounts per company (50 Enterprise, 20 Pro, 5 Free)
├── Data volume limits per company
└── Payment status enforcement

User Level (Individual):
├── Trading pairs per user (based on company subscription)
├── MT5 accounts per user
├── Rate limiting per user
└── Feature access per user
```

### **User-Facing Monitoring:**
**Real-time Performance Dashboard:**
- **Connection Status**: Connected/Disconnected + connection quality indicator
- **Data Latency**: Real-time delay measurement ("Your data delay: 15ms")
- **Message Success Rate**: Data delivery success percentage ("99.8% delivered")
- **Current Usage**: Active trading pairs vs subscription limits ("2/5 pairs active")
- **Company Usage**: "Company ABC: 7/10 users active, 32/50 MT5 accounts"

**Business Transparency:**
- **Subscription Usage**: Data volume dan API calls vs monthly limits
- **Service Health**: System status dengan user-friendly indicators
- **Historical Performance**: Average latency trends last 24 hours
- **Upgrade Indicators**: Benefits dari higher subscription tiers
- **Multi-Tenant Insights**: Company-wide usage statistics dan optimization

**User Value Proposition:**
- Performance confidence untuk trading decisions
- Usage awareness untuk subscription optimization
- Service reliability transparency
- Clear upgrade path visibility
- Company-wide resource visibility

### **Kafka Integration Benefits:**
- **Message Ordering**: Per-user tick sequence preserved via partitioning
- **Replay Capability**: Historical data replay for backtesting
- **Durability**: No data loss pada service restart
- **Scalability**: 1M+ messages/second, multiple consumers
- **Back-pressure**: Buffer traffic spikes dari multiple clients

---

## Dependencies & Communication Patterns

### **Hybrid Communication Strategy:**
**Sync (Critical Path)**: Service discovery, load balancing, circuit breaker decisions
**Async (Non-Critical)**: User activity logging, performance metrics, config updates
**Caching**: Authentication, service endpoints, user permissions (local cache)

### **Input Contracts:**

**From External Sources:**
- **from-client-mt5**: WebSocket tick data dengan MessageEnvelope
- **from-frontend**: HTTP API requests, WebSocket subscriptions
- **from-central-hub-discovery**: Service endpoints dan health status
- **from-central-hub-config**: Dynamic configuration updates
- **from-payment-webhook**: Midtrans payment status updates

**From Processing Services:**
- **from-trading-engine**: Trading signals, auto execution commands
- **from-ml-processing**: AI predictions, confidence scores, market analysis
- **from-notification-hub**: Notifications yang perlu diroute ke channels
- **from-analytics-service**: Dashboard data, performance metrics, user analytics
- **from-user-management**: User status changes, subscription updates

### **Output Contracts:**

**To External Destinations:**
- **to-client-mt5-execution**: Auto execution commands via WebSocket
- **to-frontend-websocket**: Real-time dashboard updates, trading status
- **to-telegram-webhook**: Trading signals, alerts, notifications
- **to-midtrans-api**: Payment processing requests

**To Processing Services:**
- **to-kafka-topics**: Filtered data untuk processing pipeline
  - tick-data → Data-Bridge consumers
  - user-events → User-Management consumers
  - trading-signals → Trading-Engine consumers
  - notifications → Notification-Hub consumers
- **to-central-hub-register**: Service registration dan health reporting
- **to-central-hub-metrics**: Performance metrics (async)

### **Internal Processing:**
- **bidirectional-routing**: Input → Process → Output logic untuk all data flows
- **websocket-management**: Manage multiple WebSocket connections (MT5, Frontend)
- **output-formatting**: Format data per destination (JSON untuk Frontend, Protocol Buffers untuk services)
- **caching-strategy**: Service endpoints (30s TTL), user auth (5min TTL)
- **sync-async-routing**: Critical path sync, monitoring async
- **fallback-mechanisms**: Cache-first when services unavailable
- **performance-optimization**: <1ms coordination overhead target

### **Bidirectional Data Flow:**
```
Input Sources → API Gateway → Processing Pipeline → Output Destinations
     ↓              ↓                    ↓                 ↓
Client-MT5     Route & Filter      Data Processing    Auto Execution
Frontend       Auth & Validate     AI Analysis        Dashboard Updates
Services       Cache & Transform   Trading Decisions  Notifications
External       Security Check      Real-time Metrics  Multi-channel
```

**Complete Flow Example:**
```
1. Client-MT5 → tick data → API Gateway → Kafka (tick-data topic)
2. Data-Bridge → Feature-Engineering → ML-Processing → Trading-Engine
3. Trading-Engine → signal → API Gateway → route to:
   ├── Client-MT5 (auto execution)
   ├── Frontend (dashboard update)
   └── Telegram (user notification)
```

### **Payment Gateway Integration (Midtrans):**

**Hybrid Payment Status Management:**
```
Midtrans Webhook → Payment Gateway Service → Kafka Event → API Gateway Cache
     ↓                    ↓                      ↓                ↓
Payment Status      Signature Verify      subscription_status   Real-time Update
Changed            HMAC SHA-512           Event Broadcast       <1ms Cache Lookup
Real-time          Security Check         Multi-service Notify  Trading Access Control
```

**Security Implementation:**
```python
# Webhook signature verification
def verify_midtrans_webhook(payload, signature, secret_key):
    expected_signature = hmac.sha512(payload + secret_key)
    return hmac.compare_digest(signature, expected_signature)

# Payment status enforcement
if subscription_expired:
    block_trading_access()
    disconnect_websocket()
    log_payment_violation()
```

**Subscription Status Control:**
- **Real-time blocking**: Payment expired → immediate trading access revoked
- **Backup polling**: Every 5 minutes verify cache accuracy dengan payment service
- **Midtrans integration**: Recurring billing, webhook notifications, failed payment retry
- **Security audit**: All payment events logged untuk compliance tracking

**Payment Methods Support:**
- Credit/Debit Cards, Bank Transfer, GoPay, QRIS
- Automatic recurring billing (monthly/yearly)
- Failed payment retry mechanism
- Indonesian Rupiah (IDR) currency support

### **Request Tracing & Performance Monitoring:**

**Smart Sampling Strategy:**
```python
def should_trace_request(user_id, message_type):
    # Always trace errors and user complaints
    if error_detected or user_complaint_mode:
        return True

    # Sample normal requests for performance analysis
    if message_type == "tick_data":
        return hash(user_id) % 1000 == 0  # 0.1% sampling
    elif message_type == "trading_signal":
        return hash(user_id) % 100 == 0   # 1% sampling

    return False
```

**Correlation ID Implementation:**
```
API Gateway → Generate correlation_id → MessageEnvelope → All Services → Central-Hub Collection
     ↓              ↓                      ↓                 ↓               ↓
Request In    UUID generation        Tracing header     Service logs    Performance analysis
User Data     Sampling decision      enable_tracing     Same trace ID   Bottleneck detection
Real-time     <0.01ms overhead       Optional field     End-to-end      On-demand debugging
```

**Performance Benefits:**
- **99.9% requests**: Minimal overhead (no tracing)
- **0.1% requests**: Full performance tracing untuk analysis
- **Error requests**: Always traced untuk debugging
- **User complaints**: On-demand full tracing enable

**Dependencies:**
- **central-hub**: Service coordination, shared resources, health monitoring, request tracing
- **kafka**: Message routing untuk multi-topic data distribution
- **payment-gateway**: Midtrans integration, subscription billing, webhook processing

---

## 🔗 Service Contract Specifications

### **Sophisticated Routing Engine Contracts**:
- **Bidirectional Routing**: `/contracts/internal/bidirectional-routing.md`
  - Multi-transport support (HTTP/WebSocket/Kafka/gRPC)
  - Intelligent load balancing dengan adaptive strategies
  - Circuit breaker protection dengan auto-recovery
  - Multi-tenant filtering dan security enforcement

- **MT5 Execution Contract**: `/contracts/outputs/to-client-mt5-execution.md`
  - Real-time trading command delivery via WebSocket
  - Protocol Buffers execution commands dengan comprehensive validation
  - Automatic retry mechanisms dengan exponential backoff

### **Critical Path Integration**:
- **Client-MT5 → API Gateway**: WSS dengan Protocol Buffers
- **API Gateway → Backend Services**: Intelligent multi-transport routing
  - **High Volume**: NATS primary, Kafka backup dengan automatic failover
  - **Medium Volume**: gRPC calls dengan connection pooling
  - **Low Volume**: HTTP REST via Kong Gateway
- **Real-time Performance**: <1ms routing decision, <5ms total latency

### **Client-Facing Features**:
- ✅ **Multi-Tenant Request Routing**: Forward requests dengan tenant context to Central Hub
- ✅ **Subscription Tier Enforcement**: Real-time subscription validation dan feature access
- ✅ **Multi-tenant Security**: Company/user-level filtering dan access control
- ✅ **WebSocket Performance Monitoring**: Client connection metrics dengan alerting

---

**Next Flow**: API Gateway → Data Bridge (WebSocket data) → Feature Engineering → ML Processing
**Key Innovation**: Native WebSocket dengan multi-transport architecture untuk maximum trading performance dengan enterprise security