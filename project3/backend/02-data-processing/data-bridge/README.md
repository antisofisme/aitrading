# Data Bridge Service

## 🎯 Purpose
**Data distribution hub dan subscription management service** yang menerima aggregated market data dari 00-data-ingestion service, melakukan subscription-based filtering, dan distribusi real-time data ke client subscribers dengan advanced validation dan database storage.

---

## 📊 ChainFlow Diagram

```
00-Data-Ingestion → NATS → Data Bridge ← API Gateway ← Client-MT5 Subscribers
        ↓            ↓         ↓           ↓              ↓
3 Broker Data   Stream   Subscription  WebSocket      Real-time
Aggregation     Queue    Management    Proxy         Market Data
99.9% Efficient Message  Filter/Route  JWT Auth      + Indicators
Server-side     Bus      Quality Check Rate Limits   60% Smaller
        ↓            ↓         ↓           ↓              ↓
Database Service ← Enriched Data ← Data Bridge → Client Distribution
```

---

## 🏗️ Service Architecture

### **Input Flow**: Server-processed market data + client subscription requests
**Data Source 1**: 00-data-ingestion → NATS → Data Bridge (aggregated broker data)
**Data Source 2**: Client-MT5 → API Gateway → Data Bridge (subscription requests)
**Format**: Direct Objects (Python dict from ingestion), Protocol Buffers (SubscriptionRequest from clients)
**Frequency**: 50+ ticks/second dari server ingestion, subscription management dari clients
**Performance Target**: <3ms data distribution dan filtering (part of <30ms total system budget)

### **Output Flow**: Real-time market data distribution + database storage
**Destination 1**: Client-MT5 subscribers via API Gateway WebSocket proxy (real-time streaming)
**Destination 2**: Database Service (direct connection for storage)
**Format**: Protocol Buffers (ClientMarketData to clients), Direct Objects (Python dict to database)
**Processing**: Subscription filtering + data enrichment + real-time distribution
**Performance Target**: <3ms distribution per batch (within <30ms total system budget)

---

## 🚀 Transport Architecture & Contract Integration

### **Transport Decision Matrix Applied**:

#### **Kategori A: High Volume + Mission Critical**
- **Primary Transport**: NATS + Direct Objects (00-data-ingestion → Data Bridge)
- **Secondary Transport**: WebSocket Binary + Protocol Buffers (Data Bridge → Client subscribers)
- **Backup Transport**: HTTP/2 streaming for fallback
- **Services**: Data ingestion streaming + real-time client distribution
- **Performance**: <3ms data filtering dan distribution

#### **Kategori B: Medium Volume + Important**
- **Transport**: HTTP + Direct Objects
- **Connection**: Direct connection pooling
- **Services**: Data Bridge → Database Service (enriched data storage)

### **⚠️ Service Communication Pattern**

**Data Bridge service communication pattern:**

```
✅ CORRECT Flow (Client Connection):
1. Client-MT5 → API Gateway (authenticate & establish WebSocket)
2. API Gateway → Data Bridge (proxy WebSocket dengan authenticated context)
3. Data Bridge → Database Service (direct backend service call)
4. Data Bridge → Central Hub (register health & metrics)

✅ CORRECT Flow (Backend Service Discovery):
- Data Bridge queries Central Hub untuk Database Service endpoint
- Data Bridge makes direct connection to Database Service (no proxy through Central Hub)
- Backend services communicate directly after service discovery

❌ WRONG Flow:
1. Client-MT5 → Data Bridge (direct from internet - SECURITY RISK!)
2. Data Bridge → Central Hub → Database Service (Central Hub should NOT proxy data)
```

**Data Bridge Role:**
- ✅ **Data Processor**: Validate dan enrich tick data dari API Gateway
- ✅ **Backend Service**: Receive data via API Gateway WebSocket proxy
- ✅ **Direct Database Client**: Store processed data directly ke Database Service
- ✅ **Service Discovery Client**: Query Central Hub untuk service endpoints
- ❌ **Internet-Facing Service**: TIDAK receive direct connections dari internet

### **Schema Dependencies & Contracts**:
```python
# Internal services use direct Python objects
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

# Protocol Buffers only for client communication
from common.user_context_pb2 import UserContext, SubscriptionTier  # Client data
from common.api_response_pb2 import APIResponse, ErrorInfo  # Client responses
```

---

## 📊 **Technical Indicators Implementation Strategy**

### **Kategorisasi Indicator Berdasarkan Sumber Data**

#### **KATEGORI 1: Berdasarkan Tick/Raw Data (Hitungan dari OHLCV)**
```
✅ Data langsung dari tick OANDA v20 API
```

**Momentum & Trend Indicators:**
1. **RSI** - Hitung dari close price series
2. **MACD** - Hitung dari close price (EMA 12, EMA 26, Signal 9)
3. **Stochastic** - Hitung dari high/low/close
4. **MFI** - Hitung dari high/low/close/volume
5. **AO (Awesome Oscillator)** - Hitung dari high/low midpoint
6. **Bollinger Bands** - Hitung dari close price + standard deviation
7. **EMA/SMA** - Hitung dari close price series
8. **ATR** - Hitung dari high/low/close (true range)
9. **Williams %R** - Hitung dari high/low/close
10. **CCI** - Hitung dari typical price (high+low+close)/3
11. **Parabolic SAR** - Hitung dari high/low series
12. **Aroon** - Hitung dari high/low periods
13. **CMO** - Hitung dari close price momentum
14. **Donchian Channels** - Hitung dari high/low periods
15. **Keltner Channels** - Hitung dari EMA + ATR

#### **KATEGORI 2: Berdasarkan Output dari Kolektor (External Data)**
```
✅ Data dari external-data collectors (bukan tick langsung)
```

**Market Context Indicators:**
1. **Economic** - Dari FRED API, Yahoo Finance economic calendar
2. **Sessions** - Dari market_session collector (trading hours)
3. **Volume** - Dari broker volume data (bukan tick volume)
4. **Order Book** - Dari broker depth data (jika ada)
5. **Correlation** - Dari multiple asset price relationships
6. **ADL (Accumulation/Distribution)** - Perlu volume dari broker
7. **OBV (On-Balance Volume)** - Perlu volume dari broker

#### **KATEGORI 3: Berdasarkan Pattern/Group Calculation (Analisis Kelompok Data)**
```
✅ Analisis dari gabungan data tick + context
```

**Execution Analysis:**
1. **Slippage** - Analisis dari expected vs actual execution price
2. **Timesales** - Analisis dari trade execution patterns

**Advanced Pattern Recognition:**
1. **Harmonic Patterns** - Analisis geometric patterns dari price series
2. **Elliott Wave** - Analisis wave structure dari price movements
3. **Candlestick Patterns** - Pattern recognition dari OHLC combinations
4. **Chart Patterns** - Pattern detection (head & shoulders, triangles, dll)
5. **Fibonacci** - Level calculations dari swing high/low points
6. **Smart Money Concepts** - Analisis institutional flow patterns
7. **Ichimoku Cloud** - Complex calculation dari multiple timeframe analysis

---

## ⚙️ **Indicator Processing Implementation Plan**

### **Categories 1 & 2 Processing in Data-Bridge**

#### **KATEGORI 1: Real-time Tick Calculation (15 Indicators)**
```
✅ Mathematical formulas applied to live OHLCV data
✅ Processed in Data-Bridge for <3ms performance
✅ Cached for efficiency with TTL strategy
```

**Technical Implementation:**
1. **RSI (14 period)** - Momentum oscillator dari close price series
2. **MACD** - EMA(12) - EMA(26), Signal EMA(9)
3. **Stochastic** - %K dan %D dari high/low/close
4. **MFI (Money Flow Index)** - Volume-weighted RSI
5. **AO (Awesome Oscillator)** - Midpoint momentum
6. **Bollinger Bands** - SMA(20) ± 2*StdDev
7. **EMA/SMA Multiple Periods** - 12, 26, 20, 50, 200
8. **ATR (Average True Range)** - Volatility measurement
9. **Williams %R** - Momentum oscillator
10. **CCI (Commodity Channel Index)** - Typical price based
11. **Parabolic SAR** - Trend reversal system
12. **Aroon** - Trend strength measurement
13. **CMO (Chande Momentum)** - Price momentum
14. **Donchian Channels** - Breakout system
15. **Keltner Channels** - EMA + ATR bands

#### **KATEGORI 2: External Data Integration (7 Indicators)**
```
✅ Data from external-data collectors merged with tick data
✅ Context enrichment for market conditions
✅ Real-time session and correlation analysis
```

**Data Integration:**
1. **Economic Data** - FRED API, Yahoo Finance economic calendar integration
2. **Market Sessions** - Trading hours context from session collector
3. **Volume Data** - Broker volume (bukan tick volume)
4. **Order Book** - Market depth data (bila tersedia dari broker)
5. **Cross-Asset Correlation** - Multi-pair relationship analysis
6. **ADL (Accumulation/Distribution)** - Volume flow indicator
7. **OBV (On-Balance Volume)** - Volume-price relationship

### **Processing Architecture Design**

#### **Real-time Processing Flow:**
```python
# Data input from ingestion (Direct Objects)
ingestion_data = {
    'symbol': 'EURUSD',
    'timestamp': 1673000000000,
    'price_close': 1.0856,
    'price_open': 1.0855,
    'bid': 1.0855,
    'ask': 1.0857,
    'volume': 1000.0,
    'source': 'OANDA_API'
}

# Category 1: Calculate from OHLCV
category1_indicators = await calculate_tick_based_indicators(ingestion_data)

# Category 2: Merge external data
category2_context = await merge_external_data_context(ingestion_data)

# Combine results (Direct Objects)
enhanced_data = {
    'market_data': ingestion_data,
    'category1_indicators': category1_indicators,
    'category2_context': category2_context,
    'processing_timestamp': int(time.time() * 1000),
    'processing_time_ms': 2.1
}

# Dual output
await send_to_database(enhanced_data)           # Storage (Direct Objects)
await send_to_feature_engineering(enhanced_data) # ML Pipeline (Direct Objects)
```

#### **Performance Strategy:**
```
Caching Strategy:
- Price Series Cache: TTL 60s, max 1000 symbols
- Indicator Cache: TTL 30s, max 500 calculations
- External Data Cache: TTL 300s, max 100 contexts

Processing Priority:
- Category 1 (High Priority): <1ms per indicator
- Category 2 (Medium Priority): <2ms per context merge
- Total Target: <3ms per tick batch
```

#### **Direct Objects Schema (Python Dict):**
```python
# Internal data structures use Python dicts for performance
category1_indicators = {
    'rsi_14': 65.5,
    'macd': {'macd': 0.0023, 'signal': 0.0021, 'histogram': 0.0002},
    'stochastic': {'k': 75.2, 'd': 72.8},
    'mfi_14': 68.3,
    'ao': 0.0012,
    'bollinger': {'upper': 1.0870, 'middle': 1.0856, 'lower': 1.0842},
    'ema_values': [1.0854, 1.0856, 1.0851, 1.0858, 1.0850],  # 12,26,20,50,200
    'sma_values': [1.0855, 1.0857, 1.0852, 1.0859, 1.0851],
    'atr_14': 0.0015,
    'williams_r': -25.5,
    'cci_14': 85.2,
    'parabolic_sar': 1.0851,
    'aroon': {'up': 85.7, 'down': 14.3},
    'cmo_14': 15.8,
    'donchian': {'upper': 1.0875, 'lower': 1.0840},
    'keltner': {'upper': 1.0871, 'middle': 1.0856, 'lower': 1.0841}
}

category2_context = {
    'economic': {'cpi': 3.2, 'gdp': 2.1, 'unemployment': 3.7},
    'session': {'current': 'London', 'overlap': 'NY-London', 'volatility_multiplier': 1.2},
    'volume': {'current': 1250, 'average': 1100, 'ratio': 1.14},
    'order_book': {'bid_depth': 5000, 'ask_depth': 4800, 'imbalance': 0.04},
    'correlation': {'GBPUSD': 0.82, 'USDJPY': -0.65, 'AUDUSD': 0.71},
    'adl': 125000.5,
    'obv': 89500.2
}

enhanced_data = {
    'market_data': ingestion_data,
    'category1_indicators': category1_indicators,
    'category2_context': category2_context,
    'processing_timestamp': 1673000000000,
    'processing_time_ms': 2.1
}
```

#### **Error Handling & Fallback:**
```
Circuit Breaker Pattern:
- External API failures → Use cached context data
- Calculation errors → Log and continue with partial indicators
- Performance degradation → Reduce indicator frequency temporarily

Quality Assurance:
- Validate calculation results against expected ranges
- Monitor calculation accuracy vs historical patterns
- Alert on significant indicator deviation
```

### **Integration with ML Pipeline**

#### **Data Bridge → Feature-Engineering Flow:**
```
Real-time Enhanced Data → Feature-Engineering Service
              ↓                       ↓
    Category 1&2 Indicators    Convert to ML Features
    Direct Objects (Dict)      Normalize & Transform
    <3ms processing time      Prepare for CNN/LSTM input
```

#### **Categories NOT Processed (Delegated to ML):**
**KATEGORI 3: Advanced Pattern Recognition**
- Harmonic Patterns → ML-Processing (CNN-based detection)
- Elliott Wave → ML-Processing (Complex wave analysis)
- Candlestick Patterns → ML-Processing (Pattern recognition)
- Chart Patterns → ML-Processing (Computer vision)
- Fibonacci Levels → ML-Processing (Smart level detection)
- Smart Money Concepts → ML-Processing (Institutional flow analysis)
- Ichimoku Cloud → ML-Processing (Multi-timeframe analysis)

**Reasoning**: Category 3 requires sophisticated pattern recognition, machine learning models, and complex algorithms that exceed simple mathematical calculations.

---

## 🔄 Data Processing Pipeline

### **1. Dual Input Processing**:
```python
class DataBridgeProcessor:
    async def handle_websocket_data(self, binary_data: bytes, user_context: UserContext):
        """Process incoming protobuf data from clients via API Gateway"""

        # Deserialize Protocol Buffers data (Client-MT5 only)
        batch_data = BatchTickData()
        batch_data.ParseFromString(binary_data)

        # Extract user context for processing
        user_id = batch_data.user_id
        ticks = batch_data.ticks

        # Performance tracking
        start_time = time.time()

        # Process batch
        enriched_data = await self.process_tick_batch(batch_data, user_context)

        # Send to Database Service (Direct Objects)
        await self.send_to_database(enriched_data)

        # Performance logging
        processing_time = (time.time() - start_time) * 1000
        self.logger.info(f"Client batch processed in {processing_time:.2f}ms")

    async def handle_internal_data(self, market_data_dict: dict):
        """Process incoming direct objects from Data-Ingestion"""

        # Direct object processing (faster than protobuf)
        start_time = time.time()

        # Calculate indicators
        enhanced_data = await self.process_market_data(market_data_dict)

        # Dual output (Direct Objects)
        await self.send_to_database(enhanced_data)           # Storage
        await self.send_to_feature_engineering(enhanced_data) # ML Pipeline

        # Performance logging
        processing_time = (time.time() - start_time) * 1000
        self.logger.info(f"Internal data processed in {processing_time:.2f}ms")
```

### **2. Market Data Processing Pipeline**:
```python
async def process_market_data(self, market_data_dict: dict) -> dict:
    """Process market data with Categories 1&2 indicator calculation"""

    enhanced_data = {
        'market_data': market_data_dict,
        'category1_indicators': {},
        'category2_context': {},
        'processing_timestamp': int(time.time() * 1000),
        'processing_time_ms': 0.0
    }

    start_time = time.time()

    # Category 1: Technical Indicators from OHLCV
    enhanced_data['category1_indicators'] = await self.calculate_technical_indicators(market_data_dict)

    # Category 2: External Data Context Integration
    enhanced_data['category2_context'] = await self.merge_external_context(market_data_dict)

    # Performance tracking
    enhanced_data['processing_time_ms'] = (time.time() - start_time) * 1000

    return enhanced_data

async def calculate_technical_indicators(self, market_data: dict) -> dict:
    """Calculate all Category 1 indicators from OHLCV data"""

    # Extract price data
    close_price = market_data['price_close']
    open_price = market_data['price_open']
    high_price = market_data.get('price_high', close_price)
    low_price = market_data.get('price_low', close_price)
    volume = market_data.get('volume', 0)

    # Calculate indicators (simplified example)
    indicators = {}

    # RSI calculation
    indicators['rsi_14'] = await self.calculate_rsi(close_price, period=14)

    # MACD calculation
    indicators['macd'] = await self.calculate_macd(close_price)

    # Add other 13 indicators...

    return indicators
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

### **Dual Input Contracts**:

#### **Input Contract 1: Client Data (from API Gateway)**
**File**: `contracts/inputs/from-api-gateway.md`
```markdown
# Input Contract: API Gateway → Data Bridge (Client Data)

## Protocol Buffer Schema (Client-MT5 Only)
- **Source**: `central-hub/shared/proto/common/tick-data.proto`
- **Message Type**: `BatchTickData`
- **Transport**: WebSocket Binary

## Data Flow
1. Client-MT5 authenticates dengan API Gateway (JWT validation)
2. API Gateway provides authenticated WebSocket endpoint untuk Data Bridge
3. Client-MT5 sends BatchTickData protobuf message
4. Data Bridge deserializes and processes client-specific data

## Performance Requirements
- **Processing Target**: <2ms per client batch (Protocol Buffers overhead)
```

#### **Input Contract 2: Internal Data (from Data-Ingestion)**
**File**: `contracts/inputs/from-data-ingestion.md`
```markdown
# Input Contract: Data-Ingestion → Data Bridge (Internal)

## Direct Objects Schema (Performance Optimized)
- **Format**: Python dict objects
- **Transport**: NATS/direct function calls

## Schema Reference
```python
market_data_dict = {
    'symbol': 'EURUSD',
    'timestamp': 1673000000000,
    'price_close': 1.0856,
    'price_open': 1.0855,
    'bid': 1.0855,
    'ask': 1.0857,
    'volume': 1000.0,
    'source': 'OANDA_API'
}
```

## Performance Requirements
- **Processing Target**: <1ms per batch (Direct object access)
```

### **Output Contract (to Database Service)**:
**File**: `contracts/outputs/to-database-service.md`
```markdown
# Output Contract: Data Bridge → Database Service (Internal)

## Direct Objects Schema (Performance Optimized)
- **Format**: Python dict objects
- **Transport**: HTTP POST with JSON/direct function calls

## Data Flow
1. Data Bridge processes market data with Categories 1&2
2. Calculate technical indicators and merge context
3. Send enhanced_data dict to Database Service
4. Database Service handles multi-database storage

## Schema Reference
```python
enhanced_data = {
    'market_data': {
        'symbol': 'EURUSD',
        'timestamp': 1673000000000,
        'price_close': 1.0856,
        'bid': 1.0855,
        'ask': 1.0857,
        'volume': 1000.0,
        'source': 'OANDA_API'
    },
    'category1_indicators': {
        'rsi_14': 65.5,
        'macd': {'macd': 0.0023, 'signal': 0.0021},
        'bollinger': {'upper': 1.0870, 'lower': 1.0842},
        # ... 12 other indicators
    },
    'category2_context': {
        'economic': {'cpi': 3.2, 'gdp': 2.1},
        'session': {'current': 'London', 'volatility_multiplier': 1.2},
        'correlation': {'GBPUSD': 0.82, 'USDJPY': -0.65},
        # ... other context data
    },
    'processing_timestamp': 1673000000000,
    'processing_time_ms': 2.1
}
```

## Performance Requirements
- **Processing Time**: <2ms indicator calculation per batch
- **Transfer Time**: <0.1ms (direct objects, no serialization)
- **Total Target**: <2.1ms per batch (significant improvement from 3ms)
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
- **API Gateway**: WebSocket proxy untuk client connections + user authentication
- **Database Service**: Direct HTTP connection untuk backend data storage
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

**Input Flow**: Client-MT5 → API Gateway (WebSocket proxy) → Data Bridge (validation & enrichment)
**Output Flow**: Data Bridge → Database Service (multi-database storage)
**Key Innovation**: Advanced data validation dengan WebSocket proxy architecture dan Protocol Buffers optimization untuk high-frequency trading data processing