# 🌳 Database Flow Tree - Complete Data Flow Architecture

> **Last Updated**: 2025-10-17
> **Version**: 1.0.0
> **Purpose**: Complete mapping of services to database tables with full column specifications

---

## 📊 Overview

```
┌─────────────────────┐
│  Data Sources       │
│  (Polygon, Dukascopy)│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Data Collectors    │ ───────► TimescaleDB: market_ticks (raw tick data)
│  (4 services)       │          - 90-day retention
└──────────┬──────────┘          - Hypertable partitioned by time
           │
           │ (via NATS/Kafka)
           │
           ▼
┌─────────────────────┐
│  Data Bridge        │ ───────► ClickHouse: aggregates (candle data)
│  (3 instances)      │          - Long-term analytics storage
└──────────┬──────────┘          - Aggregated OHLCV data
           │
           ▼
┌─────────────────────┐
│  Tick Aggregator    │ ───────► ClickHouse: aggregates (computed candles)
│  (1 service)        │          - Multiple timeframes (M1-W1)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Feature Service    │ ───────► ClickHouse: ml_features (TODO)
│  (ML features)      │          - 72 ML features per candle
└─────────────────────┘

┌─────────────────────┐
│  Central Hub        │ ───────► TimescaleDB: health_metrics
│  (Monitoring)       │          - Service health tracking
└─────────────────────┘
```

---

## 🗄️ Database Architecture

### TimescaleDB (Operational Database)
- **Purpose**: Real-time tick data storage
- **Retention**: 90 days (auto-cleanup via retention policy)
- **Optimization**: Hypertable with time-based partitioning
- **Tables**: `market_ticks`, `health_metrics`

### ClickHouse (Analytics Database)
- **Purpose**: Long-term analytics and aggregated data
- **Retention**: Unlimited (or configurable TTL)
- **Optimization**: Column-oriented, highly compressed
- **Tables**: `aggregates`, `ml_features` (planned)

---

## 📋 Complete Service → Table Flow

---

## 🔴 **1. Polygon Live Collector**

**Service**: `polygon-live-collector`
**Container**: `suho-live-collector`
**Purpose**: Collect real-time tick data from Polygon.io WebSocket API

### ✍️ Writes To: **TimescaleDB → `market_ticks`**

| Column | Type | Description | Example Value |
|--------|------|-------------|---------------|
| `time` | timestamp with time zone | Tick timestamp | `2025-10-17 10:30:45.123+00` |
| `tick_id` | uuid | Unique tick identifier | `550e8400-e29b-41d4-a716-446655440000` |
| `tenant_id` | varchar(50) | Multi-tenant isolation | `default` |
| `symbol` | varchar(20) | Trading pair symbol | `EUR/USD`, `XAU/USD` |
| `bid` | numeric(18,5) | Bid price | `1.08550` |
| `ask` | numeric(18,5) | Ask price | `1.08552` |
| `mid` | numeric(18,5) | Mid price (bid+ask)/2 | `1.08551` |
| `spread` | numeric(10,5) | Spread in pips | `0.00002` |
| `exchange` | varchar(50) | Exchange name | `polygon` |
| `source` | varchar(50) | Data source | `polygon-live` |
| `event_type` | varchar(20) | Event type | `tick`, `quote` |
| `use_case` | varchar(50) | Use case identifier | `real-time-trading` |
| `timestamp_ms` | bigint | Unix timestamp (ms) | `1729161045123` |
| `ingested_at` | timestamp with time zone | Ingestion timestamp | `2025-10-17 10:30:45.150+00` |

**Data Flow**:
```
Polygon WebSocket → Live Collector → NATS/Kafka → TimescaleDB.market_ticks
```

**Frequency**: Real-time (as ticks arrive, ~100-1000 ticks/second)

---

## 🟢 **2. Polygon Historical Downloader**

**Service**: `polygon-historical-downloader`
**Container**: `suho-historical-downloader`
**Purpose**: Download historical tick data from Polygon.io REST API

### ✍️ Writes To: **TimescaleDB → `market_ticks`**

| Column | Type | Description | Example Value |
|--------|------|-------------|---------------|
| *(Same schema as Live Collector)* |
| `source` | varchar(50) | Data source | `polygon-historical` |
| `use_case` | varchar(50) | Use case | `backfill`, `historical-analysis` |

**Data Flow**:
```
Polygon REST API → Historical Downloader → NATS/Kafka → TimescaleDB.market_ticks
```

**Frequency**: Batch processing (daily backfill, historical data)

---

## 🟡 **3. Dukascopy Historical Downloader**

**Service**: `dukascopy-historical-downloader`
**Container**: `suho-external-collector` (combined service)
**Purpose**: Download historical tick data from Dukascopy binary files

### ✍️ Writes To: **TimescaleDB → `market_ticks`**

| Column | Type | Description | Example Value |
|--------|------|-------------|---------------|
| *(Same schema as Live Collector)* |
| `source` | varchar(50) | Data source | `dukascopy` |
| `exchange` | varchar(50) | Exchange | `dukascopy` |

**Data Flow**:
```
Dukascopy Binary Files → External Collector → NATS/Kafka → TimescaleDB.market_ticks
```

**Frequency**: Batch processing (historical backfill)

---

## 🟠 **4. External Data Collector**

**Service**: `external-data-collector`
**Container**: `suho-external-collector`
**Purpose**: Collect data from external sources (generic collector)

### ✍️ Writes To: **TimescaleDB → `market_ticks`**

| Column | Type | Description | Example Value |
|--------|------|-------------|---------------|
| *(Same schema as Live Collector)* |
| `source` | varchar(50) | Data source | `external`, `custom` |

**Data Flow**:
```
External Source → External Collector → NATS/Kafka → TimescaleDB.market_ticks
```

---

## 🔵 **5. Data Bridge (3 Instances)**

**Service**: `data-bridge`
**Containers**: `backend-data-bridge-1`, `backend-data-bridge-2`, `backend-data-bridge-3`
**Purpose**: Stream data from TimescaleDB to ClickHouse with deduplication

### 📥 Reads From: **TimescaleDB → `market_ticks`**

### ✍️ Writes To: **ClickHouse → `aggregates`**

**Note**: Data Bridge currently **does NOT write directly** to ClickHouse. It forwards tick data via NATS/Kafka to Tick Aggregator, which then writes aggregated candles to ClickHouse.

**Actual Flow**:
```
TimescaleDB.market_ticks → Data Bridge → NATS/Kafka → Tick Aggregator → ClickHouse.aggregates
```

**Frequency**: Real-time streaming (100-1000 messages/second)

---

## 🟣 **6. Tick Aggregator**

**Service**: `tick-aggregator`
**Container**: `suho-tick-aggregator`
**Purpose**: Aggregate tick data into OHLCV candles for multiple timeframes

### 📥 Reads From:
- **NATS/Kafka** (tick stream from Data Bridge)
- **TimescaleDB → `market_ticks`** (backfill only)

### ✍️ Writes To: **ClickHouse → `aggregates`**

| Column | Type | Description | Example Value |
|--------|------|-------------|---------------|
| `symbol` | String | Trading pair | `EUR/USD`, `XAU/USD` |
| `timeframe` | String | Candle timeframe | `M1`, `M5`, `M15`, `M30`, `H1`, `H4`, `D1`, `W1` |
| `timestamp` | DateTime64(3, 'UTC') | Candle timestamp | `2025-10-17 10:30:00.000` |
| `timestamp_ms` | UInt64 | Unix timestamp (ms) | `1729161000000` |
| `open` | Decimal(18,5) | Open price | `1.08550` |
| `high` | Decimal(18,5) | High price | `1.08565` |
| `low` | Decimal(18,5) | Low price | `1.08545` |
| `close` | Decimal(18,5) | Close price | `1.08560` |
| `volume` | UInt64 | Volume (tick count) | `150` |
| `vwap` | Decimal(18,5) | Volume-weighted average price | `1.08555` |
| `range_pips` | Decimal(10,5) | High-Low range in pips | `0.00020` |
| `body_pips` | Decimal(10,5) | |Close-Open| in pips | `0.00010` |
| `start_time` | DateTime64(3, 'UTC') | Candle start time | `2025-10-17 10:30:00.000` |
| `end_time` | DateTime64(3, 'UTC') | Candle end time | `2025-10-17 10:30:59.999` |
| `source` | String | Data source | `polygon-live`, `polygon-historical` |
| `event_type` | String | Event type | `ohlcv` |
| `indicators` | String | Technical indicators (JSON) | `{}` (empty for now) |
| `ingested_at` | DateTime64(3, 'UTC') | Ingestion timestamp | `2025-10-17 10:31:00.050` |

**Data Flow**:
```
NATS/Kafka → Tick Aggregator → ClickHouse.aggregates
```

**Timeframes Supported**:
- M1 (1 minute)
- M5 (5 minutes)
- M15 (15 minutes)
- M30 (30 minutes)
- H1 (1 hour)
- H4 (4 hours)
- D1 (1 day)
- W1 (1 week)

**Frequency**:
- M1: Every 1 minute
- M5: Every 5 minutes
- ... (depends on timeframe)

---

## 🟤 **7. Feature Engineering Service**

**Service**: `feature-engineering-service`
**Container**: `suho-feature-service` (planned)
**Purpose**: Calculate 72 ML features from candle data

### 📥 Reads From: **ClickHouse → `aggregates`**

### ✍️ Writes To: **ClickHouse → `ml_features`** (TODO - table not yet created)

**Planned Schema for `ml_features`**:

| Column | Type | Description | Example Value |
|--------|------|-------------|---------------|
| `symbol` | String | Trading pair | `EUR/USD` |
| `timeframe` | String | Candle timeframe | `H1` |
| `timestamp` | DateTime64(3, 'UTC') | Feature timestamp | `2025-10-17 10:00:00.000` |
| `timestamp_ms` | UInt64 | Unix timestamp (ms) | `1729159200000` |
| **Price Features (18)** |
| `price_change_pct` | Float64 | Price change % | `0.05` |
| `price_momentum_3` | Float64 | 3-period momentum | `0.00015` |
| `price_momentum_5` | Float64 | 5-period momentum | `0.00023` |
| ... | ... | ... | ... |
| **Volatility Features (12)** |
| `atr_14` | Float64 | Average True Range (14) | `0.00045` |
| `volatility_std_20` | Float64 | 20-period std dev | `0.00032` |
| ... | ... | ... | ... |
| **Fibonacci Features (12)** |
| `fib_0_236` | Float64 | Fibonacci 23.6% level | `1.08545` |
| `fib_0_382` | Float64 | Fibonacci 38.2% level | `1.08550` |
| ... | ... | ... | ... |
| **Volume Features (6)** |
| `volume_ma_20` | Float64 | Volume MA (20) | `125.5` |
| ... | ... | ... | ... |
| **Trend Features (12)** |
| `ema_12` | Float64 | EMA (12) | `1.08555` |
| `sma_50` | Float64 | SMA (50) | `1.08560` |
| ... | ... | ... | ... |
| **Pattern Features (12)** |
| `is_doji` | UInt8 | Is Doji pattern | `0` (false) |
| `is_hammer` | UInt8 | Is Hammer pattern | `1` (true) |
| ... | ... | ... | ... |
| `ingested_at` | DateTime64(3, 'UTC') | Ingestion timestamp | `2025-10-17 10:05:00.000` |

**Total ML Features**: 72 features

**Data Flow**:
```
ClickHouse.aggregates → Feature Service → ClickHouse.ml_features
```

**Status**: ⚠️ **IN DEVELOPMENT** - Table schema not yet created

---

## ⚪ **8. Central Hub**

**Service**: `central-hub`
**Container**: `suho-central-hub`
**Purpose**: Service coordination and health monitoring

### ✍️ Writes To: **TimescaleDB → `health_metrics`**

| Column | Type | Description | Example Value |
|--------|------|-------------|---------------|
| `id` | integer | Primary key | `12345` |
| `tenant_id` | varchar(100) | Multi-tenant isolation | `system` |
| `service_name` | varchar(255) | Service name | `polygon-live-collector` |
| `timestamp` | timestamp | Metric timestamp | `2025-10-17 10:30:00` |
| `status` | varchar(50) | Health status | `healthy`, `unhealthy`, `degraded` |
| `response_time_ms` | double precision | Response time | `25.5` |
| `cpu_usage` | double precision | CPU usage (%) | `15.2` |
| `memory_usage` | double precision | Memory usage (MB) | `256.8` |
| `error_rate` | double precision | Error rate (%) | `0.05` |
| `metadata` | jsonb | Additional metadata | `{"version": "1.0", "uptime": 3600}` |

**Data Flow**:
```
All Services → Central Hub (health endpoint) → TimescaleDB.health_metrics
```

**Frequency**: Every 30 seconds (health check interval)

---

## 🔄 Complete Data Flow Summary

### **Real-time Flow** (Live Trading):
```
1. Polygon WebSocket
   ↓
2. Live Collector → market_ticks (TimescaleDB)
   ↓
3. Data Bridge (subscribe NATS/Kafka) → forward to Tick Aggregator
   ↓
4. Tick Aggregator → aggregates (ClickHouse)
   ↓
5. Feature Service (planned) → ml_features (ClickHouse)
   ↓
6. ML Model (future) → predictions
```

### **Historical Flow** (Backfill):
```
1. Polygon/Dukascopy API
   ↓
2. Historical Downloader → market_ticks (TimescaleDB)
   ↓
3. Tick Aggregator (backfill mode) → aggregates (ClickHouse)
   ↓
4. Feature Service (planned) → ml_features (ClickHouse)
```

### **Monitoring Flow**:
```
All Services → Central Hub → health_metrics (TimescaleDB)
```

---

## 📊 Data Volume Estimates

### TimescaleDB (market_ticks)
- **Per Symbol**: ~100-1000 ticks/second
- **14 Symbols**: ~1,400-14,000 ticks/second
- **Daily Volume**: ~120M - 1.2B ticks/day
- **90-Day Retention**: ~10B - 100B ticks total
- **Storage**: ~500GB - 5TB (with compression)

### ClickHouse (aggregates)
- **Per Symbol**: 8 timeframes
- **14 Symbols**: 112 total series
- **M1 Candles/Day**: 1,440 candles/symbol × 14 = 20,160 candles/day
- **All Timeframes**: ~30,000-40,000 candles/day
- **Storage**: ~10GB per year (highly compressed)

---

## 🚀 Next Steps

1. ✅ **Complete**: TimescaleDB `market_ticks` schema
2. ✅ **Complete**: ClickHouse `aggregates` schema
3. ⚠️ **TODO**: Create ClickHouse `ml_features` table
4. ⚠️ **TODO**: Implement Feature Engineering Service write logic
5. ⚠️ **TODO**: Add ML predictions table
6. ⚠️ **TODO**: Add trading signals table

---

## 📝 Notes

- **Deduplication**: Data Bridge handles duplicate detection using DragonflyDB cache
- **Multi-tenancy**: All tables support `tenant_id` for isolation
- **Retention**: TimescaleDB auto-deletes data older than 90 days
- **Scalability**: Data Bridge runs 3 instances for load balancing
- **Monitoring**: Central Hub tracks all service health metrics

---

**Generated**: 2025-10-17
**Author**: Claude Code
**Version**: 1.0.0
