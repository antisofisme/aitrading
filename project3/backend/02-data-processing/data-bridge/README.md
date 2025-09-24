# Data Bridge Service

## 🎯 Purpose
**WebSocket server dan data processing service** yang menerima pre-processed tick data dari client-mt5, melakukan advanced validation, dan stores directly ke database service menggunakan Protocol Buffers untuk optimal performance.

---

## 📊 ChainFlow Diagram

```
Client-MT5 → API Gateway (Auth Only) → Data Bridge → Database Service → Multi-Database Storage
    ↓           ↓                        ↓              ↓                 ↓
WebSocket   JWT Validation            Advanced      Protobuf Binary    PostgreSQL
Processed   User Context             Validation    Serialization      ClickHouse
Data        Rate Limits              Data Enrich   10x Faster        DragonflyDB
50+ ticks   Direct Forward           Quality Check  60% Smaller      Weaviate/Arango
```

---

## 🏗️ Service Architecture

### **Input Flow**: Pre-processed tick data dari Client-MT5 via API Gateway coordination
**Data Source**: Client-MT5 → Data Bridge (direct WebSocket after API Gateway auth)
**Format**: Protocol Buffers (BatchTickData) dengan authenticated user context
**Frequency**: 50+ ticks/second across 10 trading pairs
**Performance Target**: <3ms data validation dan routing (part of <30ms total system budget)

### **Output Flow**: Validated, enriched data ke Database Service
**Destination**: Database Service (direct connection)
**Format**: Protocol Buffers (EnrichedBatchData)
**Processing**: Advanced validation + data enrichment
**Performance Target**: <3ms processing per batch (within <30ms total system budget)

---

## 🚀 Transport Architecture & Contract Integration

### **Transport Decision Matrix Applied**:

#### **Kategori A: High Volume + Mission Critical**
- **Primary Transport**: WebSocket Binary + Protocol Buffers
- **Backup Transport**: HTTP/2 streaming for fallback (standardized across all services)
- **Failover**: Automatic connection recovery
- **Services**: API Gateway → Data Bridge (tick data streaming)
- **Performance**: <3ms data validation dan routing

#### **Kategori B: Medium Volume + Important**
- **Transport**: HTTP + Protocol Buffers
- **Connection**: Direct connection pooling
- **Services**: Data Bridge → Database Service (enriched data storage)

### **⚠️ Service Communication Pattern**

**Data Bridge uses DIRECT service calls:**

```
✅ CORRECT Flow:
1. Client-MT5 → API Gateway (authenticate & get WebSocket token)
2. Client-MT5 → Data Bridge (direct WebSocket with JWT token)
3. Data Bridge → Database Service (direct multi-database storage)
4. Data Bridge → Central Hub (register health & metrics)

✅ Service Discovery:
- Data Bridge queries Central Hub untuk Database Service endpoint
- Direct connection to Database Service (no proxy through Central Hub)
- Authentication token validated independently

❌ WRONG Flow:
1. Client-MT5 → API Gateway → Data Bridge
   (API Gateway should NOT proxy data streams)
2. Data Bridge → Central Hub → Database Service
   (Central Hub should NOT proxy database operations)
```

**Data Bridge Role:**
- ✅ **Data Processor**: Validate dan enrich tick data dari Client-MT5
- ✅ **Direct Database Client**: Store processed data directly ke Database Service
- ✅ **Service Discovery Client**: Query Central Hub untuk service endpoints
- ❌ **API Gateway Proxy**: TIDAK receive data through API Gateway proxy

### **Schema Dependencies & Contracts**:
```python
# Import from centralized schemas
import sys
sys.path.append('../../../01-core-infrastructure/central-hub/shared/generated/python')

from common.tick_data_pb2 import BatchTickData, TickData, QualityMetrics
from common.user_context_pb2 import UserContext, SubscriptionTier
from trading.enriched_data_pb2 import EnrichedBatchData, ValidationResults
from common.api_response_pb2 import APIResponse, ErrorInfo
```

---

## 🔄 Data Processing Pipeline

### **1. WebSocket Input Processing**:
```python
class DataBridgeProcessor:
    async def handle_websocket_data(self, binary_data: bytes, user_context: UserContext):
        """Process incoming protobuf data from API Gateway"""

        # Deserialize Protocol Buffers data
        batch_data = BatchTickData()
        batch_data.ParseFromString(binary_data)

        # Extract user context for processing
        user_id = batch_data.user_id
        ticks = batch_data.ticks

        # Performance tracking
        start_time = time.time()

        # Process batch
        enriched_data = await self.process_tick_batch(batch_data, user_context)

        # Send to Database Service
        await self.send_to_database(enriched_data)

        # Performance logging
        processing_time = (time.time() - start_time) * 1000
        self.logger.info(f"Batch processed in {processing_time:.2f}ms")
```

### **2. Advanced Validation Pipeline**:
```python
async def process_tick_batch(self, batch_data: BatchTickData, user_context: UserContext) -> EnrichedBatchData:
    """Advanced validation beyond client-side processing"""

    enriched = EnrichedBatchData()
    enriched.original_batch.CopyFrom(batch_data)
    enriched.user_context.CopyFrom(user_context)

    for tick in batch_data.ticks:
        # Advanced validation
        validation_result = await self.advanced_validation(tick)

        if validation_result.is_valid:
            # Data enrichment
            enriched_tick = await self.enrich_tick_data(tick, user_context)
            enriched.enriched_ticks.append(enriched_tick)
        else:
            # Log validation failures
            enriched.validation_failures.append(validation_result)

    # Calculate batch quality metrics
    enriched.quality_score = self.calculate_quality_score(enriched)
    enriched.processing_timestamp = int(time.time() * 1000)

    return enriched
```

### **3. Data Enrichment Process**:
```python
async def enrich_tick_data(self, tick: TickData, user_context: UserContext) -> EnrichedTickData:
    """Enrich tick data with additional context and validation"""

    enriched = EnrichedTickData()
    enriched.original_tick.CopyFrom(tick)

    # Market context enrichment
    enriched.market_session = await self.get_market_session(tick.symbol, tick.timestamp)
    enriched.liquidity_score = await self.calculate_liquidity_score(tick)
    enriched.volatility_context = await self.get_volatility_context(tick.symbol)

    # User-specific enrichment
    enriched.user_relevance_score = self.calculate_user_relevance(tick, user_context)
    enriched.subscription_tier = user_context.tier

    # Technical enrichment
    enriched.normalized_price = self.normalize_price(tick.bid, tick.ask)
    enriched.tick_quality_score = self.assess_tick_quality(tick)

    return enriched
```

---

## 📊 Contract Definitions

### **Input Contract (from API Gateway)**:
**File**: `contracts/inputs/from-api-gateway.md`
```markdown
# Input Contract: API Gateway → Data Bridge

## Protocol Buffer Schema
- **Source**: `central-hub/shared/proto/common/tick-data.proto`
- **Message Type**: `BatchTickData`
- **Transport**: WebSocket Binary

## Data Flow
1. Client-MT5 authenticates dengan API Gateway (JWT validation)
2. API Gateway provides authenticated WebSocket endpoint untuk Data Bridge
3. Client-MT5 connects directly to Data Bridge dengan authenticated context
4. Data Bridge receives BatchTickData protobuf message dengan validated user context

## Schema Reference
```protobuf
message BatchTickData {
  repeated TickData ticks = 1;     // Pre-processed tick data
  string user_id = 2;              // User identifier
  int32 batch_id = 3;              // Batch sequence number
  int64 batch_timestamp = 4;       // Batch creation time
  QualityMetrics quality = 5;      // Client-side quality metrics
}
```

## Performance Requirements
- **Input Rate**: 50+ ticks/second
- **Batch Size**: 5 ticks per batch (100ms timeout)
- **Processing Target**: <3ms per batch
```

### **Output Contract (to Database Service)**:
**File**: `contracts/outputs/to-database-service.md`
```markdown
# Output Contract: Data Bridge → Database Service

## Protocol Buffer Schema
- **Source**: `central-hub/shared/proto/trading/enriched-data.proto`
- **Message Type**: `EnrichedBatchData`
- **Transport**: HTTP Binary (direct service call)

## Data Flow
1. Data Bridge processes and enriches BatchTickData
2. Advanced validation and context enrichment
3. Serialize to EnrichedBatchData protobuf
4. Direct HTTP call to Database Service
5. Database Service handles multi-database storage

## Schema Reference
```protobuf
message EnrichedBatchData {
  BatchTickData original_batch = 1;           // Original data
  repeated EnrichedTickData enriched_ticks = 2; // Enriched tick data
  repeated ValidationFailure validation_failures = 3; // Failed validations
  UserContext user_context = 4;              // User context info
  double quality_score = 5;                  // Overall batch quality
  int64 processing_timestamp = 6;            // Processing completion time
  MarketContext market_context = 7;          // Market session info
}

message EnrichedTickData {
  TickData original_tick = 1;                // Original tick data
  MarketSession market_session = 2;          // Market session context
  double liquidity_score = 3;               // Liquidity assessment
  VolatilityContext volatility_context = 4; // Volatility metrics
  double user_relevance_score = 5;          // User-specific relevance
  SubscriptionTier subscription_tier = 6;   // User subscription level
  double normalized_price = 7;              // Normalized price data
  double tick_quality_score = 8;            // Individual tick quality
}
```

## Performance Requirements
- **Output Rate**: Matches input rate (50+ ticks/second)
- **Processing Time**: <3ms enrichment per batch
- **Data Size**: ~60% smaller than JSON equivalent
- **Serialization**: <0.5ms per batch
```

### **Internal Contract (service-specific)**:
**File**: `contracts/internal/validation-rules.md`
```markdown
# Internal Contract: Data Bridge Validation Rules

## Advanced Validation Schema
- **Source**: Service-specific validation logic
- **Purpose**: Beyond client-side validation
- **Performance**: <1ms per tick validation

## Validation Rules
1. **Cross-pair Correlation**: Detect unusual price movements
2. **Market Session Validation**: Verify trading hours compliance
3. **Liquidity Assessment**: Check market depth indicators
4. **Historical Context**: Compare with recent price history
5. **User Tier Validation**: Subscription-specific data access

## Quality Scoring
- **Tick Quality**: Individual tick assessment (0.0 - 1.0)
- **Batch Quality**: Overall batch health score
- **User Relevance**: Personalized relevance scoring
- **Market Context**: Session and volatility context
```

---

## ⚡ Performance Optimizations

### **Protocol Buffers Benefits**:
```
Performance Metrics (1000 ticks processing):
JSON Processing: ~15ms serialization + ~150KB data
Protobuf Processing: ~1.5ms serialization + ~60KB data

Network Transfer Savings:
- 60% smaller payload size
- 10x faster serialization/deserialization
- Reduced WebSocket bandwidth usage
- Lower CPU usage for data processing
```

### **Batch Processing Optimization**:
```python
class BatchProcessor:
    def __init__(self):
        self.batch_buffer = []
        self.batch_timeout = 0.1  # 100ms
        self.max_batch_size = 10

    async def process_with_batching(self, tick_data: TickData):
        """Optimize processing with intelligent batching"""
        self.batch_buffer.append(tick_data)

        # Process when batch is full or timeout reached
        if (len(self.batch_buffer) >= self.max_batch_size or
            self.should_timeout_batch()):

            await self.process_batch(self.batch_buffer)
            self.batch_buffer.clear()
```

### **Connection Pooling**:
```python
class DatabaseConnectionManager:
    def __init__(self):
        self.connection_pool = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(
                limit=100,  # Max connections
                ttl_dns_cache=300,
                use_dns_cache=True
            )
        )

    async def send_to_database(self, enriched_data: EnrichedBatchData):
        """Optimized database service communication"""
        binary_data = enriched_data.SerializeToString()

        async with self.connection_pool.post(
            'http://database-service:8006/api/v1/store-batch',
            data=binary_data,
            headers={'Content-Type': 'application/x-protobuf'}
        ) as response:
            return await response.read()
```

---

## 🔍 Monitoring & Observability

### **Performance Metrics**:
- **Processing Latency**: Per-batch processing time
- **Throughput**: Ticks processed per second
- **Quality Score**: Data quality assessment
- **Error Rate**: Validation failure percentage
- **Protocol Buffer Efficiency**: Serialization performance

### **Health Checks**:
```python
async def health_check():
    """Service health assessment (standardized format)"""
    return {
        "service_name": "data-bridge",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "performance_metrics": {
            "processing_latency_ms": await get_avg_latency(),
            "throughput_tps": await get_current_throughput(),
            "quality_score": await get_avg_quality_score(),
            "active_connections": get_active_websocket_count(),
            "protobuf_performance": await get_protobuf_metrics()
        },
        "system_resources": {
            "cpu_usage": await get_cpu_usage(),
            "memory_usage": await get_memory_usage()
        }
    }
```

### **Alerting Thresholds**:
- **Latency**: >5ms average processing time
- **Quality**: <0.8 average quality score
- **Throughput**: <40 ticks/second sustained
- **Error Rate**: >5% validation failures

---

## 🔗 Integration Points

### **Service Dependencies**:
- **API Gateway**: WebSocket data input + user authentication
- **Database Service**: Direct HTTP connection for data storage
- **Central Hub**: Service discovery dan health reporting
- **Shared Schemas**: Protocol Buffers schema imports

### **External Dependencies**:
- **Market Data Validation**: Real-time market session APIs
- **Historical Context**: Price history for validation
- **User Context**: Subscription tier verification
- **Performance Monitoring**: Metrics collection service

---

## 🎯 Business Value

### **Data Quality Assurance**:
- **Advanced Validation**: Beyond client-side processing
- **Market Context**: Real-time market session awareness
- **User Personalization**: Subscription-tier specific processing
- **Quality Scoring**: Measurable data quality metrics

### **Performance Leadership**:
- **Sub-3ms Processing**: Contributing to <30ms total latency
- **High Throughput**: 50+ ticks/second sustained processing
- **Efficient Serialization**: 60% bandwidth savings with protobuf
- **Scalable Architecture**: Handle multiple concurrent users

### **Operational Excellence**:
- **Real-time Monitoring**: Comprehensive performance tracking
- **Automated Quality Control**: Intelligent validation rules
- **Service Reliability**: Health checks dan automated recovery
- **Future-proof Design**: Protocol Buffers schema evolution

---

## 🔗 Service Contract Specifications

### **Data Bridge Contracts**:
- **Input Contract**: WebSocket Binary dari API Gateway dengan BatchTickData protobuf
- **Output Contract**: HTTP + Protocol Buffers ke Database Service dengan EnrichedBatchData
- **Validation Pipeline**: Advanced server-side validation beyond client processing

### **Critical Path Integration**:
- **API Gateway → Data Bridge**: WebSocket Binary untuk high-frequency data
- **Data Bridge → Database Service**: HTTP + Protocol Buffers untuk enriched storage
- **Performance Target**: <3ms total processing per batch

---

**Input Flow**: API Gateway (WebSocket) → Data Bridge (validation & enrichment)
**Output Flow**: Data Bridge → Database Service (multi-database storage)
**Key Innovation**: Advanced data validation dengan multi-transport architecture dan Protocol Buffers optimization untuk high-frequency trading data processing