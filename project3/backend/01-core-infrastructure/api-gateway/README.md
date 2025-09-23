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
  bytes payload = 3;          // Actual protobuf message (BatchTickData, etc)
  int64 timestamp = 4;        // For message ordering
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

### **User-Facing Monitoring:**
**Real-time Performance Dashboard:**
- **Connection Status**: Connected/Disconnected + connection quality indicator
- **Data Latency**: Real-time delay measurement ("Your data delay: 15ms")
- **Message Success Rate**: Data delivery success percentage ("99.8% delivered")
- **Current Usage**: Active trading pairs vs subscription limits ("2/5 pairs active")

**Business Transparency:**
- **Subscription Usage**: Data volume dan API calls vs monthly limits
- **Service Health**: System status dengan user-friendly indicators
- **Historical Performance**: Average latency trends last 24 hours
- **Upgrade Indicators**: Benefits dari higher subscription tiers

**User Value Proposition:**
- Performance confidence untuk trading decisions
- Usage awareness untuk subscription optimization
- Service reliability transparency
- Clear upgrade path visibility

### **Kafka Integration Benefits:**
- **Message Ordering**: Per-user tick sequence preserved via partitioning
- **Replay Capability**: Historical data replay for backtesting
- **Durability**: No data loss pada service restart
- **Scalability**: 1M+ messages/second, multiple consumers
- **Back-pressure**: Buffer traffic spikes dari multiple clients

---

## Dependencies
- **central-hub**: Service discovery dan health monitoring
- **user-management**: User authentication dan context validation
- **database-service**: Session storage dan rate limiting data

---

**Next Flow**: API Gateway → Data Bridge (WebSocket data) → Feature Engineering → ML Processing
**Key Innovation**: Native WebSocket untuk maximum trading performance dengan enterprise security