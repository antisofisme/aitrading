# API Gateway Service

## 🎯 Purpose
**Central entry point dan traffic controller** yang handle authentication, routing, dan WebSocket connections untuk semua client requests dengan <5ms response time.

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

### **Output Flow**: Filtered data ke multiple Kafka topics untuk scalability
**Destination**: Multiple Kafka topics berdasarkan data type
**Topic Structure**:
- `tick-data` (5000 msg/sec) → Data-Bridge consumers
- `user-events` (2 msg/sec) → User-Management consumers
- `trading-signals` (1000 msg/sec) → Trading-Engine consumers
- `notifications` (50 msg/sec) → Notification-Hub consumers
**Multi-User Handling**: Each topic partitioned by user_id
**Performance Target**: <5ms routing + filtering + Kafka publish

---

## 🔧 WebSocket Implementation

### **Native WebSocket (WSS) - Chosen for Performance**

**Why Native WebSocket over Socket.IO:**
- **30% faster** - Minimal protocol overhead
- **Predictable latency** - Critical for <30ms total target
- **High throughput** - Optimal for 50+ ticks/second
- **Simple protocol** - Less failure points for mission-critical trading

**WebSocket Endpoints:**
```
WSS://api.gateway.com/ws/mt5        # MT5 client real-time data
WSS://api.gateway.com/ws/frontend   # Frontend real-time updates
WSS://api.gateway.com/ws/alerts     # Trading alerts and notifications
```

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

### **JWT + Protocol Buffers Authentication:**
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
- **60% smaller tokens** vs JSON payload
- **10x faster decode** (0.2ms vs 2ms)
- **Cache-friendly** limits lookup dengan 5min TTL
- **Real-time updates** via database + cache invalidation

### **Protocol Buffers Integration:**
```
Client-MT5 → MessageEnvelope → API Gateway → Header-based Route → Kafka Topics
    ↓              ↓                ↓               ↓                  ↓
JSON Batch    Protobuf Binary   Read Header    Route by Type      Specialized Topics
5 ticks/100ms  60% smaller      <0.1ms route   No full parsing    tick-data/user-events
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

**Routing Benefits:**
- **Header-only routing**: No full deserialization needed (0.1ms vs 2ms)
- **Fast topic determination**: Read message_type header only
- **Optimal for 5000+ msg/sec**: Minimal processing overhead

### **Multi-Topic Data Flow:**
```
Multiple Users → WebSocket → API Gateway → Route by Data Type → Kafka Topics
      ↓             ↓            ↓              ↓                    ↓
100+ Clients   Auth Once    Filter/Route   tick-data (high vol)   Specialized Consumers
50 ticks/sec   Per Client   By Data Type   user-events (low vol)  Independent Scaling
Real-time      JWT Token    Rate Limits    trading-signals        Parallel Processing
```

### **Error Handling & Protection:**
```
Normal Flow:    Valid Messages → Filtering → Kafka Topics → Processing
Error Flow:     Invalid Messages → Dead Letter Queue → Manual Review
Protection:     Spam Detection → Circuit Breaker → Block Connection
```

**Dead Letter Queue (DLQ):**
- **failed-messages** Kafka topic untuk invalid/corrupt messages
- **No data loss**: Error messages stored untuk investigation
- **Non-blocking**: Tidak ganggu normal processing flow

**Circuit Breaker Protection:**
- **Error threshold**: >50% error rate dalam 1 menit trigger circuit breaker
- **Auto-disconnect**: WebSocket connection terminated untuk spam clients
- **Temporary ban**: Block reconnection untuk protect server resources
- **Rate limiting**: Max 100 messages/sec per user, drop excess

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

### **Input Contracts (dari Central-Hub):**
- **Service Discovery**: Available service endpoints dan health status
- **Health Monitoring**: Real-time service health untuk load balancing
- **Dynamic Config**: Runtime configuration updates
- **Auth Cache**: User authentication data untuk fast lookup

### **Output Contracts (ke Central-Hub & Kafka):**
- **Service Registration**: Register API Gateway dengan Central-Hub
- **Performance Metrics**: Latency, throughput, error rates (async Kafka)
- **User Activity Events**: Login, data usage, subscription events (async Kafka)
- **Filtered Data**: Routed ke multiple Kafka topics (tick-data, user-events, trading-signals)

### **Internal Processing:**
- **Local Caching**: Service endpoints (30s TTL), user auth (5min TTL)
- **Sync/Async Routing**: Critical path sync, monitoring async
- **Fallback Mechanisms**: Cache-first when Central-Hub unavailable
- **Performance Optimization**: <1ms coordination overhead target

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

**Next Flow**: API Gateway → Data Bridge (WebSocket data) → Feature Engineering → ML Processing
**Key Innovation**: Native WebSocket untuk maximum trading performance dengan enterprise security