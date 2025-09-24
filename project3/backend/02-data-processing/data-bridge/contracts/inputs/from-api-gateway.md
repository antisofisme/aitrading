# Input Contract: API Gateway → Data Bridge

## 🎯 Contract Overview
WebSocket connection proxied through API Gateway dengan authenticated user context untuk real-time tick data processing.

---

## 🔄 Connection Flow

### **Authentication & Connection Setup**
```
1. Client-MT5 → API Gateway: JWT Authentication
2. API Gateway validates JWT + subscription tier
3. API Gateway establishes WebSocket connection to Data Bridge
4. Client-MT5 → API Gateway → Data Bridge: WebSocket proxied dengan authenticated context
5. Data Bridge receives data via API Gateway proxy dengan validated context
```

### **Service Communication Pattern (Consistent with API Gateway)**
```
✅ CORRECT Flow:
- Client-MT5 authenticates with API Gateway (JWT validation)
- API Gateway establishes WebSocket connection dan proxies to Data Bridge
- Client-MT5 sends data to API Gateway which forwards to Data Bridge
- Data Bridge processes data received via API Gateway proxy

❌ WRONG Flow:
- Client-MT5 → Data Bridge (direct connection dari internet - SECURITY RISK!)
- Client tidak boleh bypass API Gateway untuk security dan monitoring
```

---

## 📡 Transport Specification

### **Transport Type**: WebSocket Binary + Protocol Buffers
- **Kategori**: High Volume + Mission Critical (Category A)
- **Primary**: WebSocket Binary + Protocol Buffers
- **Backup**: HTTP/2 streaming for fallback
- **Performance Target**: <3ms data validation dan routing

### **Connection Details**
```
Client Endpoint: WSS://api.gateway.com/ws/mt5
Internal Proxy: API Gateway → Data Bridge (ws://data-bridge:8003/ws/stream)
Protocol: WebSocket Secure (WSS) to API Gateway
Headers:
  - Authorization: Bearer <jwt_token>
  - x-company-id: "company_abc"
  - x-user-id: "user_123"
  - x-subscription-tier: "pro"
```

---

## 📋 Protocol Buffer Schema

### **Source Schema Location**
- **Schema Path**: `central-hub/shared/proto/common/tick-data.proto`
- **Import Path**: `../../../01-core-infrastructure/central-hub/shared/generated/python`

### **Message Type**: `BatchTickData`
```protobuf
message BatchTickData {
  repeated TickData ticks = 1;     // Pre-processed tick data from Client-MT5
  string user_id = 2;              // User identifier
  int32 batch_id = 3;              // Batch sequence number for ordering
  int64 batch_timestamp = 4;       // Batch creation time (Unix timestamp ms)
  QualityMetrics quality = 5;      // Client-side quality metrics
  string company_id = 6;           // Company/tenant identifier
  SubscriptionTier tier = 7;       // User subscription tier context
}

message TickData {
  string symbol = 1;               // Trading pair (e.g., "EURUSD")
  double bid = 2;                  // Bid price
  double ask = 3;                  // Ask price
  int64 timestamp = 4;             // Tick timestamp (Unix ms)
  int32 volume = 5;                // Tick volume
  double spread = 6;               // Bid-ask spread
}

message QualityMetrics {
  double latency_ms = 1;           // Client-side processing latency
  int32 missed_ticks = 2;          // Number of missed ticks
  double confidence = 3;           // Data quality confidence (0.0-1.0)
}
```

---

## 🚀 Performance Requirements

### **Input Rate & Volume**
- **Target Rate**: 50+ ticks/second across 10 trading pairs
- **Batch Size**: 5 ticks per batch (100ms timeout)
- **Peak Load**: 100 ticks/second durante market volatility

### **Processing Targets**
- **Per Batch**: <3ms processing time
- **WebSocket Latency**: <1ms connection overhead
- **Protocol Buffers**: 10x faster than JSON serialization

### **Subscription Tier Performance**
```
Free Tier:     1-10 ticks/second   (best effort)
Pro Tier:      10-50 ticks/second  (<100ms processing)
Enterprise:    50+ ticks/second    (<30ms processing)
```

---

## 🔍 Data Quality & Validation

### **Client-Side Quality Metrics** (Included in BatchTickData)
- **Latency Tracking**: Client-side processing time
- **Missed Ticks**: Count of missed data points
- **Confidence Score**: Data reliability assessment (0.0-1.0)

### **Data Bridge Validation** (Beyond Client Processing)
1. **Tick Data Integrity**: Bid/ask spread validation
2. **Timestamp Consistency**: Chronological ordering checks
3. **Market Session**: Trading hours compliance verification
4. **User Context**: Subscription tier data access validation

---

## 🔒 Security & Authentication

### **JWT Token Structure** (Consistent with API Gateway)
```json
{
  "sub": "user123",
  "iss": "api-gateway",
  "exp": 1640995200,
  "company_id": "company_abc",
  "subscription_tier": "pro",
  "data_access": ["EURUSD", "GBPUSD", "USDJPY"]
}
```

### **Multi-Tenant Context Headers**
```
x-company-id: "company_abc"         # Company/Tenant identifier (standardized)
x-user-id: "user_123"               # Individual user identifier
x-subscription-tier: "pro"          # Subscription level for data filtering
```

---

## 📊 Integration Points

### **API Gateway Dependencies**
- **Authentication Service**: JWT validation dan user context
- **Subscription Service**: Tier-based access control
- **Rate Limiting**: Per-user request throttling

### **Data Bridge Processing** (via API Gateway)
- **Input Reception**: Receive data dari API Gateway WebSocket proxy
- **Input Validation**: Advanced tick data validation
- **Data Enrichment**: Market context dan user-specific processing
- **Quality Assessment**: Comprehensive data quality scoring

---

## 🎯 Business Logic Integration

### **Subscription-Based Data Filtering**
```python
# Tier-based symbol access (from BUSINESS_FEATURES.md)
TIER_LIMITS = {
    'free': {
        'symbols': ['EURUSD', 'GBPUSD'],
        'max_ticks_per_second': 10,
        'data_retention_days': 1
    },
    'pro': {
        'symbols': ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD'],
        'max_ticks_per_second': 50,
        'data_retention_days': 30
    },
    'enterprise': {
        'symbols': 'all',
        'max_ticks_per_second': 'unlimited',
        'data_retention_days': 365
    }
}
```

### **Usage Tracking Integration**
- **Tick Count**: Per-user tick processing metrics
- **Bandwidth Usage**: Data transfer tracking for billing
- **Quality Metrics**: Data quality scores untuk service improvement

---

## 🔧 Error Handling & Fallback

### **Connection Errors**
- **Network Issues**: Automatic WebSocket reconnection
- **Authentication Failures**: JWT refresh mechanism
- **Rate Limiting**: Graceful degradation untuk subscription limits

### **Data Quality Issues**
- **Invalid Ticks**: Validation failure logging and filtering
- **Missing Data**: Gap detection dan interpolation
- **Timestamp Errors**: Chronological reordering

---

## 📈 Monitoring & Observability

### **Performance Metrics**
- **Connection Health**: Active WebSocket connections per user
- **Processing Latency**: Per-batch validation dan enrichment time
- **Data Quality**: Average quality scores dan validation success rate

### **Business Metrics**
- **Subscription Usage**: Tier-based feature utilization
- **Revenue Attribution**: Usage tracking untuk billing optimization
- **Customer Health**: User engagement dan subscription value

---

**Key Innovation**: API Gateway WebSocket proxy dengan multi-tenant context validation untuk secure real-time trading data processing dengan subscription-aware business logic integration.