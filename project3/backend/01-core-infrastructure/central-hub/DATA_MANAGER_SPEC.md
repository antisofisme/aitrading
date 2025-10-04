# Data Manager - Database Abstraction Layer

## 📋 Overview

**Data Manager** adalah shared component yang menyediakan abstraction layer untuk akses ke 5 databases yang ada di Suho Trading Platform:

1. **TimescaleDB** (PostgreSQL) - Primary OLTP + time-series storage
2. **ClickHouse** - OLAP analytics database
3. **DragonflyDB** - High-performance cache (Redis-compatible)
4. **Weaviate** - Vector database untuk AI/ML
5. **ArangoDB** - Multi-model graph database

---

## 🎯 Goals

### Primary Goals
1. **Single Entry Point** - Services hanya perlu import Data Manager, tidak perlu tahu database mana yang dipakai
2. **Smart Routing** - Otomatis route operations ke database yang paling sesuai
3. **Connection Pooling** - Centralized connection management untuk efisiensi
4. **Multi-level Caching** - L1 (memory) → L2 (DragonflyDB) → L3 (Database)
5. **Hot-reload Strategy** - Bisa ubah routing/caching strategy tanpa restart

### Secondary Goals
- Type safety dengan proper data models
- Error handling & retry logic dengan circuit breaker
- Performance metrics & monitoring
- Query optimization & batch operations

---

## 🏗️ Architecture

### Component Structure

```
central-hub/shared/
├── components/
│   └── data-manager/                    # Core implementation
│       ├── __init__.py                  # Main exports
│       ├── router.py                    # Smart routing logic
│       ├── pools.py                     # Connection pool manager
│       ├── cache.py                     # Multi-level caching
│       ├── query_builder.py             # Query abstraction (optional)
│       ├── models.py                    # Data models (Tick, Candle, etc)
│       ├── exceptions.py                # Custom exceptions
│       └── README.md                    # Component documentation
│
├── hot-reload/
│   └── data_manager_strategy.py         # Dynamic routing & caching strategy
│
└── static/
    └── database/
        ├── postgresql.json              # Already exists
        ├── clickhouse.json              # Already exists
        ├── dragonflydb.json             # Already exists
        ├── weaviate.json                # Already exists
        └── arangodb.json                # Already exists
```

---

## 🔄 Smart Routing Strategy

### Operation Routing Map

| Operation | Primary | Secondary | Cache |
|-----------|---------|-----------|-------|
| `save_tick` | TimescaleDB | - | DragonflyDB |
| `save_candle` | TimescaleDB | ClickHouse | DragonflyDB |
| `save_candles_bulk` | TimescaleDB | ClickHouse | - |
| `get_latest_tick` | DragonflyDB | TimescaleDB | - |
| `get_candles` | DragonflyDB | ClickHouse → TimescaleDB | ✓ |
| `get_historical` | ClickHouse | TimescaleDB | ✗ |
| `compute_aggregates` | ClickHouse | - | DragonflyDB (5 min) |
| `find_patterns` | Weaviate | - | ✗ |
| `similarity_search` | Weaviate | - | ✗ |
| `get_correlations` | ArangoDB | - | DragonflyDB (1 hour) |
| `graph_analysis` | ArangoDB | - | ✗ |

### Routing Logic

**Write Operations** (Multi-target parallel):
- `save_tick(data)` → TimescaleDB (primary) + DragonflyDB (cache latest 1 hour)
- `save_candle(data)` → TimescaleDB + ClickHouse + DragonflyDB (cache latest candles)

**Read Operations** (Cascading fallback):
- `get_candles(...)` → Try DragonflyDB → If miss, try ClickHouse → If miss, TimescaleDB

**Specialized Operations** (Direct):
- `find_patterns(...)` → Weaviate only (vector search)
- `get_correlations(...)` → ArangoDB only (graph traversal)

---

## 📦 Data Models

### Core Data Types

```python
# Tick Data
class TickData:
    symbol: str              # "EUR/USD"
    timestamp: int           # Unix timestamp ms
    bid: float               # 1.09551
    ask: float               # 1.09553
    spread: float            # 0.00002
    volume: Optional[float]  # Trade volume
    source: str              # "twelve-data", "oanda"

# Candle Data
class CandleData:
    symbol: str              # "EUR/USD"
    timeframe: str           # "1m", "5m", "1h", "1d"
    timestamp: int           # Unix timestamp ms (candle open time)
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float]
    source: str

# Economic Event
class EconomicEvent:
    event_id: str
    timestamp: int
    country: str             # "US", "EU", "JP"
    event_name: str          # "CPI", "NFP", "GDP"
    actual: Optional[float]
    forecast: Optional[float]
    previous: Optional[float]
    impact: str              # "high", "medium", "low"
    currency_impact: List[str]  # ["USD", "EUR"]
```

---

## 🔌 API Design

### DataRouter Class

```python
from central_hub.shared.components.data_manager import DataRouter

# Initialize router
router = DataRouter()

# Write operations
await router.save_tick(tick_data: TickData)
await router.save_candle(candle_data: CandleData)
await router.save_candles_bulk(candles: List[CandleData])

# Read operations - Real-time
await router.get_latest_tick(symbol: str) -> TickData
await router.get_latest_candles(symbol: str, timeframe: str, limit: int = 100) -> List[CandleData]

# Read operations - Historical
await router.get_historical_candles(
    symbol: str,
    timeframe: str,
    start_date: str,  # "2015-01-01"
    end_date: str     # "2025-01-01"
) -> List[CandleData]

# Analytics operations
await router.compute_aggregates(
    symbol: str,
    timeframe: str,
    period: str  # "1d", "1w", "1mo"
) -> Dict

# AI/ML operations
await router.find_patterns(
    pattern_vector: List[float],
    limit: int = 10
) -> List[Dict]

await router.similarity_search(
    query_vector: List[float],
    threshold: float = 0.8
) -> List[Dict]

# Correlation operations
await router.get_correlations(
    symbol: str,
    threshold: float = 0.6
) -> List[Dict]

await router.graph_analysis(
    start_symbol: str,
    depth: int = 2
) -> Dict
```

---

## ⚙️ Hot-reload Strategy

### Strategy Configuration

Location: `shared/hot-reload/data_manager_strategy.py`

```python
DATA_MANAGER_STRATEGY = {
    # Routing rules
    "routing": {
        "save_tick": ["timescale", "dragonfly_cache"],
        "save_candle": ["timescale", "clickhouse", "dragonfly_cache"],
        "get_latest_tick": ["dragonfly_cache", "timescale"],
        "get_candles": ["dragonfly_cache", "clickhouse", "timescale"],
        "get_historical": ["clickhouse"],
        "find_patterns": ["weaviate"],
        "get_correlations": ["arangodb"]
    },

    # Cache TTL settings
    "cache": {
        "tick_ttl_seconds": 3600,         # 1 hour
        "candle_ttl_seconds": 3600,       # 1 hour
        "historical_ttl_seconds": 0,      # No cache (always fresh)
        "aggregates_ttl_seconds": 300,    # 5 minutes
        "patterns_ttl_seconds": 0,        # No cache
        "correlations_ttl_seconds": 3600  # 1 hour
    },

    # Connection pool settings
    "connection_pools": {
        "timescale": {
            "min_size": 5,
            "max_size": 20,
            "timeout": 30
        },
        "clickhouse": {
            "max_connections": 10,
            "timeout": 30
        },
        "dragonfly": {
            "min_connections": 5,
            "max_connections": 50,
            "timeout": 5
        },
        "weaviate": {
            "timeout": 30
        },
        "arangodb": {
            "max_connections": 10,
            "timeout": 30
        }
    },

    # Performance tuning
    "performance": {
        "batch_size": 1000,              # Bulk insert batch size
        "query_timeout_seconds": 30,
        "retry_max_attempts": 3,
        "retry_backoff_multiplier": 2,
        "circuit_breaker_threshold": 5,
        "circuit_breaker_timeout": 60
    },

    # Query optimization
    "optimization": {
        "enable_query_cache": true,
        "enable_prepared_statements": true,
        "enable_connection_pooling": true,
        "enable_batch_operations": true
    }
}
```

### Strategy dapat di-update tanpa restart:
- Central Hub detect file change di `hot-reload/data_manager_strategy.py`
- Auto-reload strategy
- Services yang sudah running otomatis apply strategy baru

---

## 🔧 Connection Management

### Database Connection Pools

```python
class DatabasePoolManager:
    """
    Manage connection pools untuk semua 5 databases
    """

    pools = {
        'timescale': AsyncPG Pool,      # asyncpg untuk PostgreSQL/TimescaleDB
        'clickhouse': ClickHouse Client, # clickhouse-connect
        'dragonfly': Redis Pool,         # redis-py async
        'weaviate': Weaviate Client,     # weaviate-client
        'arangodb': ArangoDB Database    # python-arango
    }

    async def initialize():
        """Initialize all pools from shared/static/database/ configs"""

    async def get_connection(db_name: str):
        """Get connection from pool"""

    async def health_check_all():
        """Check health of all database connections"""

    async def close_all():
        """Close all pools gracefully"""
```

### Connection Pool Limits

| Database | Min | Max | Timeout |
|----------|-----|-----|---------|
| TimescaleDB | 5 | 20 | 30s |
| ClickHouse | - | 10 | 30s |
| DragonflyDB | 5 | 50 | 5s |
| Weaviate | - | - | 30s |
| ArangoDB | - | 10 | 30s |

**Total max connections**: ~90 (vs 250 jika setiap service connect langsung ke 5 DBs)

---

## 💾 Multi-level Caching Strategy

### Cache Levels

**L1: In-Memory Cache** (Python dict)
- TTL: 1 minute
- Scope: Per-service instance
- Use case: Latest ticks, frequently accessed data
- Size: Limited (max 1000 entries per type)

**L2: DragonflyDB Cache** (Redis-compatible)
- TTL: Configurable (default 1 hour)
- Scope: Shared across all services
- Use case: Latest ticks, latest candles, aggregates
- Size: Memory-based (configured in docker-compose)

**L3: Database** (Persistent)
- TTL: Infinite
- Scope: TimescaleDB, ClickHouse
- Use case: All historical data
- Size: Disk-based

### Cache Key Patterns

```python
# Tick data
"tick:latest:{symbol}"                    # Latest tick for symbol
"tick:range:{symbol}:{start}:{end}"      # Tick range

# Candle data
"candle:latest:{symbol}:{timeframe}:{limit}"  # Latest N candles
"candle:range:{symbol}:{timeframe}:{start}:{end}"

# Aggregates
"agg:{symbol}:{timeframe}:{period}:{metric}"

# Correlations
"corr:{symbol}:{threshold}:{timestamp}"

# Patterns
# No cache (always fresh from Weaviate)
```

### Cache Invalidation

```python
# On new tick
invalidate("tick:latest:{symbol}")

# On new candle
invalidate("candle:latest:{symbol}:{timeframe}:*")

# On correlation update
invalidate("corr:{symbol}:*")
```

---

## 🚨 Error Handling & Resilience

### Exception Hierarchy

```python
class DataManagerError(Exception):
    """Base exception untuk Data Manager"""

class DatabaseConnectionError(DataManagerError):
    """Database connection failed"""

class QueryTimeoutError(DataManagerError):
    """Query execution timeout"""

class CacheError(DataManagerError):
    """Cache operation failed"""

class ValidationError(DataManagerError):
    """Data validation failed"""
```

### Retry Logic

```python
# Retry configuration
max_attempts = 3
backoff_multiplier = 2  # 1s, 2s, 4s

# Exponential backoff
for attempt in range(max_attempts):
    try:
        result = await execute_query()
        break
    except TransientError:
        if attempt < max_attempts - 1:
            await asyncio.sleep(backoff_multiplier ** attempt)
        else:
            raise
```

### Circuit Breaker Pattern

```python
# Circuit states: CLOSED → OPEN → HALF_OPEN → CLOSED
#
# CLOSED: Normal operation
# OPEN: Stop requests after 5 consecutive failures
# HALF_OPEN: Allow 1 test request after 60s timeout
# → If success → CLOSED
# → If fail → OPEN
```

---

## 📊 Monitoring & Metrics

### Performance Metrics

```python
metrics = {
    "operations": {
        "save_tick": {
            "count": 15420,
            "success_rate": 0.998,
            "avg_latency_ms": 2.5,
            "p95_latency_ms": 5.2,
            "p99_latency_ms": 12.1
        },
        "get_candles": {
            "count": 8640,
            "cache_hit_rate": 0.85,
            "avg_latency_ms": 1.2
        }
    },

    "databases": {
        "timescale": {
            "active_connections": 8,
            "idle_connections": 12,
            "total_queries": 24000,
            "failed_queries": 3
        },
        "clickhouse": { /* ... */ },
        "dragonfly": { /* ... */ }
    },

    "cache": {
        "l1_hit_rate": 0.45,
        "l2_hit_rate": 0.85,
        "total_hit_rate": 0.93
    }
}
```

### Health Check

```python
await router.health_check()

# Response
{
    "status": "healthy",
    "databases": {
        "timescale": "healthy",
        "clickhouse": "healthy",
        "dragonfly": "healthy",
        "weaviate": "healthy",
        "arangodb": "healthy"
    },
    "connection_pools": {
        "timescale": "8/20 connections",
        "clickhouse": "3/10 connections",
        "dragonfly": "15/50 connections"
    },
    "cache": {
        "l1_entries": 850,
        "l2_entries": 5420
    }
}
```

---

## 🔐 Security Considerations

### Credential Management
- All credentials dari `.env` file (single source of truth)
- Database configs use `ENV:*` pattern
- No hardcoded passwords

### Access Control
- Data Manager tidak implement authentication (rely on service-level auth)
- Input validation untuk prevent SQL injection
- Parameterized queries only

### Data Sanitization
- Validate all inputs before database operations
- Escape special characters
- Type checking via Pydantic models

---

## 📝 Usage Examples

### Twelve Data Collector

```python
# twelve-data-collector/src/publisher.py

from central_hub.shared.components.data_manager import DataRouter, TickData

class TwelveDataPublisher:
    def __init__(self):
        self.router = DataRouter()

    async def publish_tick(self, tick_raw: dict):
        """Save tick from Twelve Data API"""

        # Convert to TickData model
        tick = TickData(
            symbol=tick_raw['symbol'],
            timestamp=tick_raw['timestamp'],
            bid=tick_raw['bid'],
            ask=tick_raw['ask'],
            source='twelve-data'
        )

        # Save via Data Manager
        # → Automatically routes to TimescaleDB + DragonflyDB
        await self.router.save_tick(tick)

    async def publish_candles_bulk(self, candles_raw: list):
        """Bulk save historical candles"""

        candles = [
            CandleData(
                symbol=c['symbol'],
                timeframe='1h',
                timestamp=c['timestamp'],
                open=c['open'],
                high=c['high'],
                low=c['low'],
                close=c['close'],
                volume=c.get('volume'),
                source='twelve-data'
            )
            for c in candles_raw
        ]

        # Bulk save (optimized batch insert)
        await self.router.save_candles_bulk(candles)
```

### Trading Engine (Query)

```python
# trading-engine/src/data_access.py

from central_hub.shared.components.data_manager import DataRouter

class TradingDataAccess:
    def __init__(self):
        self.router = DataRouter()

    async def get_recent_candles(self, symbol: str, count: int = 100):
        """Get recent candles for strategy calculation"""

        # Data Manager auto-routes:
        # 1. Try DragonflyDB cache (fast)
        # 2. If miss → ClickHouse (analytics optimized)
        # 3. If miss → TimescaleDB (primary)
        candles = await self.router.get_latest_candles(
            symbol=symbol,
            timeframe='1h',
            limit=count
        )

        return candles

    async def get_training_data(self, symbol: str):
        """Get 10 years historical data for ML training"""

        # Direct to ClickHouse (optimized for large queries)
        candles = await self.router.get_historical_candles(
            symbol=symbol,
            timeframe='1h',
            start_date='2015-01-01',
            end_date='2025-01-01'
        )

        return candles
```

### Analytics Service (Aggregates)

```python
# analytics-service/src/analytics.py

from central_hub.shared.components.data_manager import DataRouter

class Analytics:
    def __init__(self):
        self.router = DataRouter()

    async def compute_daily_stats(self, symbol: str):
        """Compute daily statistics"""

        # Uses ClickHouse materialized views (pre-computed)
        # Cached in DragonflyDB for 5 minutes
        stats = await self.router.compute_aggregates(
            symbol=symbol,
            timeframe='1h',
            period='1d'
        )

        return stats
```

---

## 🚀 Implementation Phases

### Phase 1: Core Foundation (Priority 1)
- [ ] Create `router.py` with basic routing logic
- [ ] Create `pools.py` for TimescaleDB + DragonflyDB connection pooling
- [ ] Create `cache.py` for L1 (memory) + L2 (DragonflyDB) caching
- [ ] Create `models.py` with TickData, CandleData models
- [ ] Create `exceptions.py` with custom exception hierarchy
- [ ] Test with dummy data (save/retrieve ticks and candles)

### Phase 2: Additional Databases (Priority 2)
- [ ] Add ClickHouse support to `pools.py`
- [ ] Implement historical query optimization
- [ ] Add bulk operations for historical backfill
- [ ] Performance testing with large datasets

### Phase 3: AI/ML Databases (Priority 3)
- [ ] Add Weaviate support (vector search)
- [ ] Add ArangoDB support (graph queries)
- [ ] Implement pattern matching operations
- [ ] Implement correlation graph analysis

### Phase 4: Production Readiness (Priority 4)
- [ ] Add comprehensive error handling & retry logic
- [ ] Implement circuit breaker pattern
- [ ] Add performance metrics & monitoring
- [ ] Add health check endpoints
- [ ] Write comprehensive tests
- [ ] Documentation completion

### Phase 5: Hot-reload Strategy (Priority 5)
- [ ] Create `data_manager_strategy.py` in hot-reload
- [ ] Implement strategy loading & reloading
- [ ] Test hot-reload functionality
- [ ] Performance tuning based on production metrics

---

## 📚 Dependencies

### Python Libraries Required

Add to `central-hub/requirements.txt`:

```txt
# Database clients
asyncpg==0.29.0              # TimescaleDB (PostgreSQL async)
clickhouse-connect==0.7.0    # ClickHouse client
redis[hiredis]==5.0.1        # DragonflyDB (Redis-compatible)
weaviate-client==3.26.0      # Weaviate vector DB
python-arango==7.8.0         # ArangoDB multi-model

# Data validation
pydantic==2.5.0              # Data models & validation

# Utilities
orjson==3.9.12              # Fast JSON serialization
```

---

## 🎯 Success Criteria

### Performance Targets
- [ ] Tick save latency: < 5ms (p95)
- [ ] Candle query latency: < 10ms (p95) with cache
- [ ] Cache hit rate: > 85% for recent data
- [ ] Connection pool efficiency: > 80% utilization
- [ ] Query success rate: > 99.9%

### Reliability Targets
- [ ] Database connection uptime: > 99.9%
- [ ] Automatic reconnection on failures: < 5s
- [ ] Circuit breaker activation: < 1% of operations
- [ ] Data consistency: 100% (no lost writes)

### Scalability Targets
- [ ] Support 1000+ ticks/second
- [ ] Support 100+ concurrent services
- [ ] Bulk insert: 10,000 candles in < 1 second
- [ ] Historical query: 10 years data in < 2 seconds

---

## 📞 Integration Points

### Central Hub Integration
- **Service Discovery**: Data Manager tidak perlu register (shared component)
- **Configuration**: Load dari `shared/static/database/` configs
- **Hot-reload**: Support strategy updates via `shared/hot-reload/`

### Service Integration
- **Import Pattern**: `from central_hub.shared.components.data_manager import DataRouter`
- **Initialization**: Auto-load configs dari Central Hub
- **Usage**: Simple async API (`await router.save_tick(...)`)

### Protocol Buffers Integration
- Compatible dengan existing `market_data.proto`
- Data models dapat convert to/from protobuf
- Support for NATS/Kafka message publishing (optional)

---

## ✅ Testing Strategy

### Unit Tests
- Connection pool management
- Cache operations (set, get, invalidate)
- Routing logic (correct database selection)
- Data model validation
- Error handling & retries

### Integration Tests
- End-to-end save/retrieve operations
- Multi-database consistency
- Cache coherency across services
- Connection failure recovery
- Performance under load

### Performance Tests
- Throughput benchmarks (ticks/second, candles/second)
- Latency measurements (p50, p95, p99)
- Connection pool efficiency
- Cache hit rate optimization
- Bulk operation performance

---

## 📖 References

### Related Documentation
- [Central Hub README](./README.md)
- [Shared Architecture Guide](./docs/SHARED_ARCHITECTURE.md)
- [Contracts Guide](./docs/CONTRACTS_GUIDE.md)
- [Database Configs](./shared/static/database/)

### Database Documentation
- [TimescaleDB Documentation](https://docs.timescale.com/)
- [ClickHouse Documentation](https://clickhouse.com/docs)
- [DragonflyDB Documentation](https://www.dragonflydb.io/docs)
- [Weaviate Documentation](https://weaviate.io/developers/weaviate)
- [ArangoDB Documentation](https://www.arangodb.com/docs/)

---

**📅 Created**: 2025-10-02
**👤 Owner**: Backend Infrastructure Team
**🔄 Status**: Specification - Ready for Implementation
**📊 Priority**: High - Foundation for all data services

---

**Next Steps:**
1. Review & approve this specification
2. Create GitHub issue/task untuk implementation
3. Assign to developer
4. Start with Phase 1 implementation
5. Iterate based on feedback & testing
