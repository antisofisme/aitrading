# 📊 Database Schemas - Central Hub (Single Source of Truth)

## Overview

Semua schema database disimpan di Central Hub sebagai **single source of truth**. Semua service menggunakan schema dari sini untuk consistency.

---

## 🗂️ Directory Structure

```
schemas/
├── clickhouse/           # ClickHouse OLAP schemas
│   ├── 01_ticks.sql             # Live Polygon: Real-time forex quotes (90 days)
│   ├── 02_aggregates.sql        # Historical Polygon: OHLCV bars (10 years)
│   └── 03_ml_features.sql       # ML Pipeline: Wide table (100+ columns)
│
└── timescaledb/          # TimescaleDB/PostgreSQL OLTP schemas
    ├── 01_market_ticks.sql      # Live Polygon: Primary real-time storage (90 days)
    ├── 02_market_candles.sql    # Live Polygon: OHLCV bars (90 days)
    ├── 03_market_context.sql    # External Data: Economic calendar (5 years)
    └── 04_ml_predictions.sql    # ML Pipeline: Prediction results (90 days)
```

---

## 📋 Schema Mapping by Service

### 1️⃣ Polygon Live Collector
**Data Flow**: WebSocket → NATS/Kafka → Data Bridge → Database

| Schema File | Database | Table | Purpose | Retention |
|-------------|----------|-------|---------|-----------|
| `timescaledb/01_market_ticks.sql` | TimescaleDB | `market_ticks` | Primary real-time storage | 90 days |
| `timescaledb/02_market_candles.sql` | TimescaleDB | `market_candles` | OHLCV bars | 90 days |
| `clickhouse/01_ticks.sql` | ClickHouse | `ticks` | Analytics backup | 90 days |

**Output Format** (from Live Collector):
```json
{
  "symbol": "EUR/USD",
  "bid": 1.0848,
  "ask": 1.0850,
  "mid": 1.0849,
  "spread": 2.0,
  "timestamp": 1706198400000,
  "timestamp_ms": 1706198400000,
  "exchange": 1,
  "source": "polygon_websocket",
  "event_type": "quote"
}
```

---

### 2️⃣ Polygon Historical Downloader
**Data Flow**: REST API → Direct Write → ClickHouse

| Schema File | Database | Table | Purpose | Retention |
|-------------|----------|-------|---------|-----------|
| `clickhouse/02_aggregates.sql` | ClickHouse | `aggregates` | Historical OHLCV for backtesting | 10 years |

**Output Format** (from Historical Downloader):
```json
{
  "symbol": "EUR/USD",
  "timeframe": "1m",
  "timestamp": "2024-01-26T13:30:00Z",
  "timestamp_ms": 1706198400000,
  "open": 1.0845,
  "high": 1.0855,
  "low": 1.0840,
  "close": 1.0850,
  "volume": 12345,
  "vwap": 1.0847,
  "range_pips": 15.0,
  "start_time": "2024-01-26T13:30:00Z",
  "end_time": "2024-01-26T13:31:00Z",
  "source": "polygon_historical",
  "event_type": "ohlcv"
}
```

---

### 3️⃣ External Data Collector
**Data Flow**: APIs/Scrapers → Transform → PostgreSQL/TimescaleDB

| Schema File | Database | Table | Purpose | Retention |
|-------------|----------|-------|---------|-----------|
| `timescaledb/03_market_context.sql` | TimescaleDB | `market_context` | Economic calendar & sentiment | 5 years |

**Output Format** (after transformation):
```json
{
  "event_id": "USD_nonfarm_payrolls_2024-01-26",
  "data_type": "economic_calendar",
  "symbol": "Non-Farm Payrolls",
  "timestamp": 1706198400000,
  "time_status": "historical",
  "actual_value": 353000,
  "forecast_value": 340000,
  "previous_value": 325000,
  "category": "employment",
  "importance": "high",
  "currency_impact": ["USD"],
  "market_impact_score": 0.76,
  "source": "mql5"
}
```

---

## 🔧 Usage Guidelines

### For Service Developers

**1. Initialize Database Schema**:
```bash
# ClickHouse
clickhouse-client --queries-file /schemas/clickhouse/01_ticks.sql

# TimescaleDB
psql -f /schemas/timescaledb/01_market_ticks.sql
```

**2. Schema Updates**:
- ✅ Update schema file in Central Hub
- ✅ Run migration script
- ✅ All services automatically use updated schema

**3. Schema Versioning**:
- Each schema file has version comment at top
- Migration files in `migrations/` directory
- Use semantic versioning (v1.0.0, v1.1.0, etc.)

---

## 📊 Database Stack Overview

### ClickHouse (OLAP - Analytics)
- **Purpose**: High-performance analytical queries, ML training data
- **Tables**: `ticks`, `aggregates`, `ml_features`
- **Strengths**: Columnar storage, compression, fast aggregations
- **Use Cases**: Historical backtesting, feature engineering, ML training

### TimescaleDB (OLTP - Transactional)
- **Purpose**: Fast read/write, real-time data, user data
- **Tables**: `market_ticks`, `market_candles`, `market_context`, `ml_predictions`
- **Strengths**: Time-series optimization, compression, continuous aggregates
- **Use Cases**: Real-time quotes, predictions, economic data

### DragonflyDB (Cache)
- **Purpose**: Ultra-fast cache layer
- **Keys**: `tick:latest:{symbol}`, `candle:latest:{symbol}`, `prediction:{symbol}`
- **TTL**: 15 min - 1 hour
- **Use Cases**: Real-time trading signals, latest data access

---

## 🔄 Schema Update Workflow

1. **Identify Change**: New field, index, or table needed
2. **Update Schema File**: Edit corresponding `.sql` file in Central Hub
3. **Create Migration**: Add migration script if needed
4. **Test**: Run on dev database first
5. **Deploy**: Apply to production via CI/CD
6. **Notify Services**: All services auto-detect schema changes

---

## 📚 References

- [Data Architecture Guide](/backend/DATA_ARCHITECTURE_GUIDE.md)
- [Data Routing Guide](/backend/00-data-ingestion/DATA_ROUTING_GUIDE.md)
- [ML Pipeline Schemas](/backend/03-ml-pipeline/schemas/)

---

**Last Updated**: 2025-10-06
**Maintained By**: Central Hub Team
**Version**: 1.0.0
