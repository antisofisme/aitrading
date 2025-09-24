# Output Contract: Data Bridge → Database Service

## 🎯 Contract Overview
Direct HTTP connection ke Database Service untuk multi-database storage dengan enriched Protocol Buffers data dan tenant-aware processing.

---

## 🔄 Service Communication Flow

### **Direct Service Call Pattern (Consistent with Central Hub)**
```
✅ CORRECT Flow:
1. Data Bridge processes and enriches BatchTickData
2. Data Bridge queries Central Hub for Database Service endpoint
3. Data Bridge makes direct HTTP call to Database Service
4. Database Service handles multi-database storage operations
5. Database Service returns operation status to Data Bridge

❌ WRONG Flow:
- Data Bridge → Central Hub → Database Service (NO proxy through Central Hub)
- Central Hub should provide discovery only, not route data
```

### **Service Discovery Integration**
```python
# Data Bridge discovers Database Service via Central Hub
database_endpoint = await central_hub.get_service_endpoint(
    service_name="database-service",
    tenant_context={"company_id": "company_abc"}
)
# Direct call to discovered endpoint
response = await http_client.post(f"{database_endpoint}/api/v1/store-batch", ...)
```

---

## 📡 Transport Specification

### **Transport Type**: HTTP + Protocol Buffers
- **Kategori**: Medium Volume + Important (Category B)
- **Primary**: HTTP + Protocol Buffers untuk optimal performance
- **Backup**: HTTP + JSON for fallback compatibility
- **Connection**: Direct connection pooling

### **HTTP Endpoint Details**
```
Method: POST
URL: http://database-service:8006/api/v1/store-batch
Content-Type: application/x-protobuf
Headers:
  - x-company-id: "company_abc"
  - x-user-id: "user_123"
  - x-subscription-tier: "pro"
  - Content-Length: <binary_size>
```

---

## 📋 Protocol Buffer Schema

### **Source Schema Location**
- **Schema Path**: `central-hub/shared/proto/trading/enriched-data.proto`
- **Import Path**: `../../../01-core-infrastructure/central-hub/shared/generated/python`

### **Message Type**: `EnrichedBatchData`
```protobuf
message EnrichedBatchData {
  BatchTickData original_batch = 1;           // Original data from API Gateway
  repeated EnrichedTickData enriched_ticks = 2; // Processed and enriched tick data
  repeated ValidationFailure validation_failures = 3; // Failed validations
  UserContext user_context = 4;              // Multi-tenant user context
  double quality_score = 5;                  // Overall batch quality (0.0-1.0)
  int64 processing_timestamp = 6;            // Processing completion time
  MarketContext market_context = 7;          // Market session information
  BusinessMetrics business_metrics = 8;      // Subscription and usage metrics
}

message EnrichedTickData {
  TickData original_tick = 1;                // Original tick from Client-MT5
  MarketSession market_session = 2;          // Market session context (open/close)
  double liquidity_score = 3;               // Liquidity assessment (0.0-1.0)
  VolatilityContext volatility_context = 4; // Volatility metrics and indicators
  double user_relevance_score = 5;          // User-specific relevance (0.0-1.0)
  SubscriptionTier subscription_tier = 6;   // User subscription level
  double normalized_price = 7;              // Normalized price data
  double tick_quality_score = 8;            // Individual tick quality (0.0-1.0)
}

message ValidationFailure {
  string tick_id = 1;                       // Failed tick identifier
  string failure_reason = 2;               // Validation failure description
  double confidence = 3;                   // Failure confidence level
  string validation_rule = 4;              // Which validation rule failed
}

message UserContext {
  string user_id = 1;                      // Individual user identifier
  string company_id = 2;                   // Company/tenant identifier
  SubscriptionTier tier = 3;               // Subscription tier
  repeated string allowed_symbols = 4;      // Tier-based symbol access
  int32 daily_tick_quota = 5;             // Daily processing quota
  bool premium_features = 6;               // Premium feature access
}

message MarketContext {
  MarketSession session = 1;               // Current market session
  double volatility_index = 2;            // Market volatility indicator
  string trading_hours = 3;               // Active trading hours
}

message BusinessMetrics {
  int32 ticks_processed = 1;              // Number of ticks in this batch
  double processing_cost = 2;             // Processing cost for billing
  int32 daily_usage_count = 3;           // Running daily usage count
  string subscription_status = 4;         // Current subscription status
}
```

---

## 🗄️ Multi-Database Storage Strategy

### **Database Routing Logic** (Consistent with Database Service README)
```python
# Data Bridge sends enriched data for multi-DB storage
multi_db_request = {
    # Primary OLTP storage (PostgreSQL)
    "postgresql": {
        "operation": "insert_trading_data",
        "schema": f"tenant_{user_context.company_id}",
        "table": "real_time_ticks",
        "data": enriched_batch_data
    },

    # Analytics storage (ClickHouse)
    "clickhouse": {
        "operation": "insert_analytics",
        "table": "tick_analytics",
        "data": analytics_metrics
    },

    # High-speed cache (DragonflyDB)
    "dragonflydb": {
        "operation": "cache_recent_data",
        "key": f"recent_ticks:{company_id}:{symbol}",
        "ttl": 300,  # 5 minutes
        "data": latest_ticks
    }
}
```

### **Multi-Tenant Data Isolation** (Schema-based)
- **Company Level**: Separate PostgreSQL schemas (`tenant_company_abc`)
- **User Level**: Row-level security dengan user_id filtering
- **Analytics**: ClickHouse with company_id partitioning

---

## 🚀 Performance Requirements

### **Processing Performance**
- **Output Rate**: Matches input rate (50+ ticks/second)
- **Processing Time**: <3ms enrichment per batch
- **Serialization**: <0.5ms per batch Protocol Buffers
- **HTTP Latency**: <2ms per database service call

### **Data Efficiency**
- **Protocol Buffers vs JSON**: 60% smaller payloads
- **Compression**: Built-in Protocol Buffers compression
- **Network Transfer**: Optimized binary serialization

### **Database Performance Targets** (Per Database Service README)
- **PostgreSQL**: <2ms transactional operations
- **ClickHouse**: <100ms analytics queries
- **DragonflyDB**: <1ms cache operations

---

## 🔒 Multi-Tenant Security

### **Tenant Context Propagation** (Consistent with Central Hub)
```
Request Headers:
x-company-id: "company_abc"         # Company/tenant identifier (standardized)
x-user-id: "user_123"               # Individual user identifier
x-subscription-tier: "pro"          # Subscription level
```

### **Data Isolation Validation**
- **Schema Validation**: Ensure data routes to correct tenant schema
- **Access Control**: Verify user permissions for data access
- **Audit Trail**: Log all tenant data operations for compliance

---

## 🎯 Business Logic Integration

### **Subscription-Aware Data Storage**
```python
# Storage based on subscription tier (from BUSINESS_FEATURES.md)
async def store_enriched_data(self, enriched_data, user_context):
    storage_config = {
        'free': {
            'retention_days': 1,
            'storage_priority': 'standard',
            'analytics_enabled': False
        },
        'pro': {
            'retention_days': 30,
            'storage_priority': 'high',
            'analytics_enabled': True
        },
        'enterprise': {
            'retention_days': 365,
            'storage_priority': 'premium',
            'analytics_enabled': True,
            'real_time_alerts': True
        }
    }

    config = storage_config[user_context.subscription_tier]
    return await self.database_service.store_with_config(enriched_data, config)
```

### **Usage Tracking & Billing** (ClickHouse Analytics)
```sql
-- Usage tracking for billing (stored in ClickHouse)
INSERT INTO usage_analytics (
    company_id, user_id, service_name, ticks_processed,
    processing_time_ms, data_size_bytes, timestamp, billing_period
) VALUES (
    ?, ?, 'data-bridge', ?, ?, ?, NOW(), ?
)
```

---

## 📊 Response Format

### **Success Response** (HTTP 200)
```json
{
    "status": "success",
    "batch_id": "batch_12345",
    "processed_ticks": 5,
    "processing_time_ms": 2.3,
    "storage_results": {
        "postgresql": {"status": "stored", "rows": 5},
        "clickhouse": {"status": "stored", "rows": 5},
        "dragonflydb": {"status": "cached", "keys": 3}
    },
    "quality_metrics": {
        "batch_quality_score": 0.95,
        "validation_success_rate": 1.0,
        "enrichment_completeness": 0.98
    }
}
```

### **Error Response** (HTTP 4xx/5xx)
```json
{
    "status": "error",
    "error_code": "VALIDATION_FAILED",
    "message": "Tick data validation failed for 2 ticks",
    "failed_ticks": ["tick_001", "tick_003"],
    "retry_recommended": true,
    "fallback_storage": "cache_only"
}
```

---

## 🔧 Error Handling & Fallback

### **Database Service Failures**
- **Primary Failure**: Store in DragonflyDB cache + retry queue
- **Partial Failure**: Continue with successful databases, log failures
- **Complete Failure**: Store in local buffer + alert monitoring

### **Data Quality Issues**
- **Validation Failures**: Store failed ticks for manual review
- **Incomplete Enrichment**: Store with partial enrichment flags
- **Schema Mismatches**: Graceful degradation to basic storage

---

## 🔍 Monitoring & Observability

### **Performance Metrics**
- **Storage Latency**: Per-database operation timing
- **Data Quality**: Enrichment success rates
- **Multi-DB Consistency**: Cross-database synchronization status

### **Business Metrics**
- **Subscription Usage**: Per-tier storage utilization
- **Revenue Impact**: Processing cost dan billing data
- **Customer Health**: Data quality scores per customer

---

## 📈 Integration Testing

### **End-to-End Validation**
```python
# Test enriched data storage across multiple databases
async def test_multi_database_storage():
    enriched_data = create_test_batch()
    response = await data_bridge.send_to_database(enriched_data)

    # Verify PostgreSQL storage
    pg_data = await database_service.query_postgresql(tenant_schema, batch_id)
    assert pg_data.ticks_count == enriched_data.ticks_count

    # Verify ClickHouse analytics
    ch_data = await database_service.query_clickhouse(analytics_query)
    assert ch_data.processing_metrics is not None

    # Verify DragonflyDB cache
    cached_data = await database_service.get_cached_data(cache_key)
    assert cached_data.latest_tick.timestamp == enriched_data.latest_timestamp
```

---

**Key Innovation**: Direct multi-database storage dengan tenant-aware enriched data processing dan comprehensive business metrics integration untuk optimal trading platform performance.