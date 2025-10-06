# 📊 Data Routing & Schema Management Guide

## Overview
Dokumentasi lengkap tentang **dari mana ke mana** data disimpan di sistem.

---

## 🗂️ SCHEMA ARCHITECTURE - Hybrid Database Approach

### Database Distribution Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                     DATA ROUTING ARCHITECTURE                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  DATA COLLECTORS (Sources)                              │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  1. Polygon Live Collector       (Real-time ticks)      │   │
│  │  2. Polygon Historical Downloader (Historical OHLCV)    │   │
│  │  3. External Data Collector      (Economic calendar)    │   │
│  └────────┬────────────────────────┬─────────────┬─────────┘   │
│           │                        │             │             │
│           ↓                        ↓             ↓             │
│  ┌─────────────────┐   ┌─────────────────┐   ┌──────────────┐ │
│  │  ClickHouse     │   │  ClickHouse     │   │ PostgreSQL/  │ │
│  │  ticks          │   │  aggregates     │   │ TimescaleDB  │ │
│  │  (Forex data)   │   │  (OHLCV bars)   │   │ market_context│ │
│  └─────────────────┘   └─────────────────┘   └──────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 DATA ROUTING TABLE

| Collector | Data Type | Target Database | Table Name | Purpose |
|-----------|-----------|-----------------|------------|---------|
| **Polygon Live** | Forex Ticks (Real-time) | ClickHouse | `ticks` | High-frequency quote data |
| **Polygon Live** | Aggregate Bars (OHLCV) | ClickHouse | `aggregates` | Time-series OHLCV candles |
| **Polygon Historical** | Historical OHLCV | ClickHouse | `aggregates` | Backtesting data |
| **External Collector** | Economic Calendar | PostgreSQL/TimescaleDB | `market_context` | Low-frequency context data |
| **External Collector** | Sentiment Data | PostgreSQL/TimescaleDB | `market_context` | Market sentiment |
| **External Collector** | Economic Indicators | PostgreSQL/TimescaleDB | `market_context` | FRED, CoinGecko data |

---

## 🎯 ROUTING LOGIC - HIGH vs LOW FREQUENCY

### **From Schema SQL (Lines 457-475):**

```sql
-- =========================================================================
-- DATA ROUTING LOGIC (for collectors)
-- =========================================================================

-- HIGH FREQUENCY → market_ticks table:
-- - Yahoo Finance OHLCV data
-- - Dukascopy historical ticks
-- - Broker MT5/API real-time feeds
-- - All price/volume time series data

-- LOW FREQUENCY → market_context table:
-- - FRED economic indicators
-- - CoinGecko crypto prices/sentiment
-- - Fear & Greed Index
-- - Exchange rates (for reference)
-- - Market session data
-- - News events
-- - Economic calendar events
```

### Decision Tree:

```
Data Type?
    │
    ├─ Price/Volume/Tick? ──→ HIGH FREQUENCY
    │                         ├─ Real-time? → ClickHouse `ticks`
    │                         └─ Historical? → ClickHouse `aggregates`
    │
    └─ Economic/Sentiment? ──→ LOW FREQUENCY
                              └─ PostgreSQL `market_context`
```

---

## 🗃️ DETAILED SCHEMA MAPPING

### 1️⃣ ClickHouse `ticks` Table

**Source**: Polygon Live Collector (WebSocket + REST)

**Purpose**: Real-time forex quotes for pattern analysis

**Schema**:
```sql
CREATE TABLE ticks (
    symbol String,                    -- "EUR/USD", "XAU/USD"
    timestamp DateTime64(3, 'UTC'),   -- Millisecond precision
    timestamp_ms UInt64,              -- Unix timestamp
    bid Decimal(18, 5),               -- Bid price
    ask Decimal(18, 5),               -- Ask price
    mid Decimal(18, 5),               -- Mid price
    spread Decimal(10, 5),            -- Spread in pips
    exchange UInt16,                  -- Exchange ID
    source String,                    -- "polygon_websocket"
    event_type String,                -- "quote"
    ingested_at DateTime64(3, 'UTC')
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, timestamp)
TTL toDateTime(timestamp) + INTERVAL 90 DAY;  -- 90 days retention
```

**Data Flow**:
```
Polygon.io WebSocket
    → Live Collector (websocket_client.py)
    → NATS Publisher (nats_publisher.py)
    → Data Bridge (kafka_subscriber.py)
    → ClickHouse Writer
    → ticks table
```

---

### 2️⃣ ClickHouse `aggregates` Table

**Source**:
- Polygon Live Collector (Aggregate WebSocket)
- Polygon Historical Downloader (REST API)

**Purpose**: OHLCV bars for technical analysis & backtesting

**Schema**:
```sql
CREATE TABLE aggregates (
    symbol String,                    -- "EUR/USD"
    timeframe String,                 -- "1m", "5m", "1h", "1d"
    timestamp DateTime64(3, 'UTC'),   -- Bar start time
    timestamp_ms UInt64,
    open Decimal(18, 5),              -- OHLCV
    high Decimal(18, 5),
    low Decimal(18, 5),
    close Decimal(18, 5),
    volume UInt64,                    -- Tick volume
    vwap Decimal(18, 5),              -- Volume-weighted average
    range_pips Decimal(10, 5),        -- High-low range
    start_time DateTime64(3, 'UTC'),  -- Bar start
    end_time DateTime64(3, 'UTC'),    -- Bar end
    source String,                    -- "polygon_aggregate" / "polygon_historical"
    ingested_at DateTime64(3, 'UTC')
)
ENGINE = MergeTree()
PARTITION BY (symbol, toYYYYMM(timestamp))
ORDER BY (symbol, timeframe, timestamp)
TTL toDateTime(timestamp) + INTERVAL 365 DAY;  -- 1 year retention
```

**Data Flow (Live)**:
```
Polygon.io Aggregate WebSocket (CAS stream)
    → Live Collector (aggregate_client.py)
    → NATS Publisher
    → Data Bridge
    → ClickHouse Writer
    → aggregates table
```

**Data Flow (Historical)**:
```
Polygon.io REST API
    → Historical Downloader (main.py)
    → ClickHouse Writer (clickhouse_writer.py)
    → aggregates table
```

---

### 3️⃣ PostgreSQL/TimescaleDB `market_context` Table

**Source**: External Data Collector (Scrapers + APIs)

**Purpose**: Low-frequency economic/sentiment data for ML context

**Schema**:
```sql
CREATE TABLE market_context (
    id BIGSERIAL PRIMARY KEY,

    -- Identification
    event_id VARCHAR(100),            -- Unique event ID
    external_id VARCHAR(100),         -- External system ID

    -- Classification
    data_type VARCHAR(30) NOT NULL,   -- 'economic_calendar', 'sentiment', etc.
    symbol VARCHAR(50) NOT NULL,      -- Event name or indicator
    timestamp BIGINT NOT NULL,        -- Unix milliseconds
    time_status VARCHAR(20),          -- 'historical', 'scheduled', 'future'

    -- Values
    value DECIMAL(20,8),              -- Numeric value
    value_text VARCHAR(100),          -- Text value

    -- Event-specific
    actual_value DECIMAL(20,8),       -- Actual result
    forecast_value DECIMAL(20,8),     -- Forecast
    previous_value DECIMAL(20,8),     -- Previous value
    event_date TIMESTAMP,             -- Scheduled date
    release_date TIMESTAMP,           -- Release date

    -- Context
    category VARCHAR(50),             -- 'inflation', 'gdp', etc.
    importance VARCHAR(20),           -- 'high', 'medium', 'low'

    -- Market impact
    currency_impact TEXT[],           -- Affected currencies
    forex_impact VARCHAR(30),         -- Impact direction
    market_impact_score DECIMAL(3,2), -- 0.0-1.0

    -- Source
    source VARCHAR(50) NOT NULL,      -- 'mql5', 'fred', 'coingecko'
    reliability VARCHAR(20),          -- 'high', 'medium', 'low'
    metadata JSONB,                   -- Full API response

    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_context_type_time ON market_context (data_type, timestamp DESC);
CREATE INDEX idx_context_symbol_time ON market_context (symbol, timestamp DESC);
CREATE UNIQUE INDEX idx_context_event_dedup ON market_context (event_id, symbol, event_date);
```

**Data Flow**:
```
External APIs (MQL5, FRED, CoinGecko)
    → External Collector (scrapers/*.py)
    → Transformation Pipeline (NEW - needs to be built)
    → PostgreSQL Writer (NEW - needs to be built)
    → market_context table
```

---

## 🔄 COMPLETE DATA FLOW DIAGRAM

```
┌──────────────────────────────────────────────────────────────────┐
│                    DATA INGESTION SOURCES                        │
└──────────────────────────────────────────────────────────────────┘
         │                      │                      │
         ↓                      ↓                      ↓
    Polygon.io            Polygon.io           External APIs
    WebSocket             REST API             (MQL5, FRED)
    (Real-time)           (Historical)         (Economic)
         │                      │                      │
         ↓                      ↓                      ↓
┌─────────────────┐   ┌─────────────────┐   ┌──────────────────┐
│ Live Collector  │   │ Historical      │   │ External         │
│                 │   │ Downloader      │   │ Collector        │
│ Output:         │   │                 │   │                  │
│ - Tick quotes   │   │ Output:         │   │ Output:          │
│ - Aggregates    │   │ - OHLCV bars    │   │ - Calendar events│
└────────┬────────┘   └────────┬────────┘   └────────┬─────────┘
         │                      │                      │
         ↓                      ↓                      ↓
    NATS/Kafka             Direct Write          Transform
    Message Queue           to DB                Pipeline
         │                      │                      │
         ↓                      ↓                      ↓
┌─────────────────┐   ┌─────────────────┐   ┌──────────────────┐
│ Data Bridge     │   │ ClickHouse      │   │ PostgreSQL       │
│ (Subscriber)    │   │ Writer          │   │ Writer           │
└────────┬────────┘   └────────┬────────┘   └────────┬─────────┘
         │                      │                      │
         ↓                      ↓                      ↓
┌─────────────────────────────────────────────────────────────────┐
│                    DATABASE LAYER                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ ClickHouse (OLAP - Analytics Database)                 │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │ • ticks (90 days TTL)        - Real-time quotes        │    │
│  │ • aggregates (365 days TTL)  - OHLCV bars              │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ PostgreSQL/TimescaleDB (OLTP - Transactional DB)       │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │ • market_context (5 years)   - Economic/Sentiment data │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ DragonflyDB (Cache Layer)                              │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │ • tick:latest:{symbol} (1h TTL)  - Latest ticks        │    │
│  │ • candle:latest:{symbol} (1h)    - Latest candles      │    │
│  │ • indicator:{symbol} (5m)        - Calculated values   │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Schema File Locations

### Active Schemas (To be created):
```
backend/00-data-ingestion/schemas/
├── clickhouse_forex.sql           # ClickHouse ticks + aggregates
└── postgresql_market_context.sql  # PostgreSQL market_context
```

### Archived Schemas (Reference):
```
backend/00-data-ingestion/_archived/
├── clickhouse-consumer/sql/schema.sql           # Old ClickHouse schema
└── external-data/database/database_schema_hybrid.sql  # Hybrid schema (BEST REFERENCE)
```

### Architecture Documentation:
```
backend/docs/architecture/
└── END_TO_END_ARCHITECTURE.md    # Complete system architecture
```

---

## 🔧 Implementation Status

| Component | Schema Ready | Writer Ready | Integration Complete |
|-----------|--------------|--------------|---------------------|
| **Polygon Live → ClickHouse ticks** | ✅ Yes | ✅ Via Data Bridge | ✅ Production Ready |
| **Polygon Live → ClickHouse aggregates** | ⚠️ Missing fields | ⚠️ Needs update | ⚠️ Needs fix |
| **Polygon Historical → ClickHouse** | ⚠️ Missing fields | ⚠️ Needs update | ⚠️ Needs fix |
| **External → PostgreSQL context** | ✅ Yes | ❌ Not built | ❌ Major work needed |

---

## 🎯 Next Steps

### Priority 1: Fix Historical Downloader Output
```python
# File: polygon-historical-downloader/src/clickhouse_writer.py
# Add missing fields to match aggregates schema:
{
    ...existing fields,
    'timeframe': '1m',  # From config
    'range_pips': (high - low) * 10000,
    'start_time': timestamp,
    'end_time': timestamp + timeframe_duration,
    'event_type': 'ohlcv'
}
```

### Priority 2: Build External Collector Writer
```python
# New file: external-data-collector/src/writers/postgresql_writer.py
class PostgreSQLWriter:
    async def write_market_context(self, event: dict):
        # Transform scraped data to market_context format
        transformed = transform_to_market_context(event)
        # Insert to PostgreSQL
        await self.pg_pool.execute(INSERT_SQL, transformed)
```

### Priority 3: Create Active Schema Directory
```bash
mkdir -p backend/00-data-ingestion/schemas
# Move and update schemas from archived
```

---

## 📊 Performance Considerations

### Data Retention

| Database | Table | Retention | Reason |
|----------|-------|-----------|--------|
| ClickHouse | `ticks` | 90 days | High volume, recent data analysis |
| ClickHouse | `aggregates` | 365 days | Backtesting, lower volume |
| PostgreSQL | `market_context` | 5 years | Low volume, historical context |
| DragonflyDB | Cache | 1 hour - 15 min | Real-time only |

### Storage Estimates

- **ticks**: ~100 MB/day (compressed)
- **aggregates**: ~20 MB/day
- **market_context**: ~1 MB/day
- **Total**: ~4-5 GB/month

---

## 📚 References

1. **Schema SQL**: `/00-data-ingestion/_archived/external-data/database/database_schema_hybrid.sql` (Lines 457-475)
2. **Architecture**: `/docs/architecture/END_TO_END_ARCHITECTURE.md`
3. **Verification**: `/00-data-ingestion/DATA_SCHEMA_VERIFICATION.md`
4. **Data Manager**: `/01-core-infrastructure/central-hub/DATA_MANAGER_SPEC.md`

---

**Last Updated**: 2025-10-06
**Status**: Documentation Complete - Implementation In Progress
