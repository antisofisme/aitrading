# Data Manager - Database Abstraction Layer

**Version:** 1.0.0 (Phase 1)
**Status:** Production Ready
**Phase:** TimescaleDB + DragonflyDB

---

## 🎯 Overview

**Data Manager** adalah shared component yang menyediakan **single entry point** untuk akses ke semua databases di Suho Trading Platform. Services tidak perlu tahu database mana yang digunakan - Data Manager secara otomatis route ke database yang paling optimal.

### Databases Supported

| Database | Status | Purpose |
|----------|--------|---------|
| **TimescaleDB** (PostgreSQL) | ✅ Phase 1 | Primary OLTP + time-series |
| **DragonflyDB** (Redis) | ✅ Phase 1 | High-performance cache |
| **ClickHouse** | 🔜 Phase 2 | OLAP analytics |
| **Weaviate** | 🔜 Phase 3 | Vector database (AI/ML) |
| **ArangoDB** | 🔜 Phase 3 | Graph database |

---

## 🚀 Quick Start

### 1. Import Data Manager

```python
from central_hub.shared.components.data_manager import DataRouter, TickData, CandleData

# Initialize router
router = DataRouter()
await router.initialize()
```

### 2. Save Tick Data

```python
# Create tick data
tick = TickData(
    symbol="EUR/USD",
    timestamp=1727996400000,
    timestamp_ms=1727996400000,
    bid=1.09551,
    ask=1.09553,
    source="polygon"
)

# Save to database
# → Automatically routes to TimescaleDB + DragonflyDB cache
await router.save_tick(tick)
```

### 3. Query Latest Tick

```python
# Get latest tick for symbol
# → Tries DragonflyDB cache first (fast)
# → Falls back to TimescaleDB if cache miss
latest_tick = await router.get_latest_tick("EUR/USD")

print(f"Bid: {latest_tick.bid}, Ask: {latest_tick.ask}")
```

### 4. Save Candle Data

```python
candle = CandleData(
    symbol="EUR/USD",
    timeframe="1m",
    timestamp=1727996400000,
    timestamp_ms=1727996400000,
    open=1.0850,
    high=1.0855,
    low=1.0848,
    close=1.0852,
    volume=15234,
    source="polygon"
)

await router.save_candle(candle)
```

### 5. Query Latest Candles

```python
# Get last 100 candles
candles = await router.get_latest_candles(
    symbol="EUR/USD",
    timeframe="1m",
    limit=100
)

for candle in candles:
    print(f"Close: {candle.close}, Volume: {candle.volume}")
```

---

## 🏗️ Architecture

### Smart Routing Strategy

```
┌─────────────────────────────────────────────────────┐
│                   Data Router                       │
│                 (Smart Routing)                     │
└─────────────────────────────────────────────────────┘
                        │
         ┌──────────────┼──────────────┐
         │              │              │
         ▼              ▼              ▼
  ┌──────────┐   ┌──────────┐   ┌──────────┐
  │TimescaleDB│   │DragonflyDB│   │ClickHouse│
  │  (OLTP)   │   │  (Cache)  │   │ (Phase 2)│
  └──────────┘   └──────────┘   └──────────┘
```

### Multi-level Caching

```
Request → L1 (Memory) → L2 (DragonflyDB) → Database
           ~1ms            ~2-5ms           ~10-50ms
```

---

## 📦 Data Models

### TickData

```python
class TickData(BaseModel):
    symbol: str              # "EUR/USD"
    timestamp: int           # Unix timestamp ms
    timestamp_ms: int        # Alias for timestamp
    bid: float               # Bid price
    ask: float               # Ask price
    mid: Optional[float]     # Mid price (auto-calculated)
    spread: Optional[float]  # Spread (auto-calculated)
    volume: Optional[float]  # Trade volume
    source: str              # "polygon", "twelve-data", etc.
    exchange: Optional[int]  # Exchange ID
    event_type: str          # Default: "quote"
    use_case: str            # Use case category
```

### CandleData

```python
class CandleData(BaseModel):
    symbol: str              # "EUR/USD"
    timeframe: str           # "1m", "5m", "1h", "1d"
    timestamp: int           # Candle open time (Unix ms)
    timestamp_ms: int        # Alias
    open: float              # Open price
    high: float              # High price
    low: float               # Low price
    close: float             # Close price
    volume: Optional[float]  # Volume
    vwap: Optional[float]    # VWAP
    range_pips: Optional[float]  # High-Low range in pips
    num_trades: Optional[int]    # Number of trades
    start_time: Optional[int]    # Bar start time
    end_time: Optional[int]      # Bar end time
    source: str              # Data source
    event_type: str          # Default: "ohlcv"
```

---

## 🔧 Configuration

### Static Configuration

Location: `shared/static/database/`

- `postgresql.json` - TimescaleDB connection settings
- `dragonflydb.json` - DragonflyDB cache settings

**Example:**
```json
{
  "connection": {
    "host": "ENV:POSTGRES_HOST",
    "port": "ENV:POSTGRES_PORT",
    "database": "ENV:POSTGRES_DB"
  },
  "pool": {
    "min": 5,
    "max": 20
  }
}
```

### Hot-reload Strategy

Location: `shared/hot-reload/data_manager_strategy.py`

Update tanpa restart:

```python
DATA_MANAGER_STRATEGY = {
    "routing": {
        "save_tick": ["timescale", "dragonfly_cache"],
        "get_latest_tick": ["dragonfly_cache", "timescale"]
    },
    "cache": {
        "tick_ttl_seconds": 3600,
        "candle_ttl_seconds": 3600
    }
}
```

---

## 🔍 API Reference

### Write Operations

#### `save_tick(tick_data: TickData)`
Save tick data to TimescaleDB + cache to DragonflyDB

#### `save_candle(candle_data: CandleData)`
Save candle data to TimescaleDB + cache to DragonflyDB

#### `save_candles_bulk(candles: List[CandleData])`
Bulk save candles (optimized for historical data import)

### Read Operations

#### `get_latest_tick(symbol: str) -> Optional[TickData]`
Get latest tick for symbol (cache-first)

#### `get_latest_candles(symbol: str, timeframe: str, limit: int = 100) -> List[CandleData]`
Get latest N candles (cache-first)

### Health & Monitoring

#### `health_check() -> HealthCheckResponse`
Check health of all databases and cache

---

## 🚨 Error Handling

### Exception Hierarchy

```python
DataManagerError
├── DatabaseConnectionError
├── QueryTimeoutError
├── QueryExecutionError
├── CacheError
├── ValidationError
├── ConfigurationError
├── ConnectionPoolExhaustedError
├── RoutingError
├── CircuitBreakerOpenError
└── RetryExhaustedError
```

### Usage

```python
from central_hub.shared.components.data_manager import (
    DataRouter,
    DatabaseConnectionError,
    QueryTimeoutError
)

try:
    await router.save_tick(tick_data)
except DatabaseConnectionError as e:
    print(f"Database connection failed: {e}")
except QueryTimeoutError as e:
    print(f"Query timeout: {e.timeout_seconds}s")
```

---

## 📊 Performance

### Phase 1 Targets (Current)

- ✅ Tick save latency: < 5ms (p95)
- ✅ Candle query latency: < 10ms (p95) with cache
- ✅ Cache hit rate: > 85% for recent data
- ✅ Connection pool efficiency: > 80%

### Metrics

```python
health = await router.health_check()

print(health.databases)  # Database health status
print(health.cache)      # Cache hit rates
print(health.connection_pools)  # Pool usage
```

---

## 🔄 Usage Examples

### Example 1: Polygon Collector Integration

```python
from central_hub.shared.components.data_manager import DataRouter, TickData

class PolygonCollector:
    def __init__(self):
        self.router = DataRouter()

    async def start(self):
        await self.router.initialize()

    async def handle_tick(self, polygon_data: dict):
        # Convert Polygon data to TickData
        tick = TickData(
            symbol=polygon_data['pair'],
            timestamp=polygon_data['t'],
            timestamp_ms=polygon_data['t'],
            bid=polygon_data['b'],
            ask=polygon_data['a'],
            source='polygon'
        )

        # Save via Data Manager
        # → Auto-routes to TimescaleDB + DragonflyDB
        await self.router.save_tick(tick)
```

### Example 2: Trading Engine Query

```python
from central_hub.shared.components.data_manager import DataRouter

class TradingEngine:
    def __init__(self):
        self.router = DataRouter()

    async def get_market_data(self, symbol: str):
        # Get latest tick (cached)
        current_tick = await self.router.get_latest_tick(symbol)

        # Get recent candles for strategy
        candles = await self.router.get_latest_candles(
            symbol=symbol,
            timeframe="1h",
            limit=100
        )

        return current_tick, candles
```

### Example 3: Bulk Historical Import

```python
async def import_historical_data(symbol: str, candles_raw: list):
    router = DataRouter()
    await router.initialize()

    # Convert to CandleData objects
    candles = [
        CandleData(
            symbol=symbol,
            timeframe="1h",
            timestamp=c['timestamp'],
            timestamp_ms=c['timestamp'],
            open=c['open'],
            high=c['high'],
            low=c['low'],
            close=c['close'],
            volume=c['volume'],
            source='polygon_historical'
        )
        for c in candles_raw
    ]

    # Bulk save (optimized)
    await router.save_candles_bulk(candles)
    print(f"✅ Imported {len(candles)} candles")
```

---

## 🚧 Roadmap

### Phase 1 (Current) ✅
- TimescaleDB (OLTP + time-series)
- DragonflyDB (cache)
- Multi-level caching
- Smart routing
- Connection pooling

### Phase 2 (Next) 🔜
- ClickHouse integration (OLAP analytics)
- Historical query optimization
- Materialized views
- Bulk operations enhancement

### Phase 3 (Future) 🔮
- Weaviate (vector search for AI/ML)
- ArangoDB (graph analysis)
- Pattern matching
- Correlation analysis

---

## 📞 Support

- **Health Check**: `await router.health_check()`
- **Cache Stats**: `await router.cache.get_stats()`
- **Pool Status**: `await router.pool_manager.health_check_all()`

---

**🎯 Data Manager: Single Entry Point untuk Multi-Database Architecture**
