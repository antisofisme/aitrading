# 🔄 Complete Data Flow Architecture

**Last Updated**: 2025-10-06
**Version**: 3.0.0

## 📊 Overview

This document describes the **complete end-to-end data flow** from Polygon.io to databases, ensuring data persistence and proper storage.

**Key Architecture Change (v3.0.0)**:
- Live data now flows through **tick data + Aggregator Service** (not direct 1s bars)
- Aggregator queries TimescaleDB and creates 7 timeframes (M5-W1)
- This provides **FASTEST** historical data updates vs REST API

---

## 🟢 LIVE DATA FLOW (Tick Data → Aggregated)

### **Source**: Polygon WebSocket Tick/Quote Stream

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Data Collection (Tick Data)                        │
├─────────────────────────────────────────────────────────────┤
│ Polygon WebSocket (Tick/Quote Stream)                      │
│ - Real-time bid/ask quotes (raw ticks)                     │
│ - Delay: <100ms                                            │
│ - Symbols: EUR/USD, GBP/USD, XAU/USD, etc.                │
└────────────┬────────────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Live Collector (Tick Publisher)                    │
├─────────────────────────────────────────────────────────────┤
│ Service: polygon-live-collector                             │
│ Location: /00-data-ingestion/polygon-live-collector/       │
│                                                              │
│ Function:                                                    │
│ - Parse tick data (bid/ask) from WebSocket                 │
│ - Calculate mid price and spread                            │
│ - Publish to NATS/Kafka (NO direct DB write)              │
│                                                              │
│ Output Format (Tick Data):                                   │
│ {                                                            │
│   'symbol': 'EUR/USD',                                      │
│   'bid': 1.0848,                                            │
│   'ask': 1.0850,                                            │
│   'mid': 1.0849,                                            │
│   'spread': 0.20,  (pips)                                   │
│   'timestamp_ms': 1706198400123,                            │
│   'exchange': 1,                                             │
│   'source': 'polygon_websocket',                            │
│   'event_type': 'quote'                                     │
│ }                                                            │
│                                                              │
│ NOTE: CAS (1s aggregates) DISABLED - using tick data       │
└────────────┬────────────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Message Queue (NATS/Kafka)                         │
├─────────────────────────────────────────────────────────────┤
│ NATS Subject: ticks.EURUSD                                  │
│ Kafka Topic: tick_archive                                   │
│                                                              │
│ Message Metadata:                                            │
│ - _source: 'polygon_websocket'                             │
│ - ingested_at: timestamp                                    │
└────────────┬────────────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Data Bridge (Tick Routing)                         │
├─────────────────────────────────────────────────────────────┤
│ Service: data-bridge                                        │
│ Location: /02-data-processing/data-bridge/                 │
│                                                              │
│ Function:                                                    │
│ - Subscribe from NATS subject: ticks.>                      │
│ - Filter: source = 'polygon_websocket' → TimescaleDB       │
│ - Batch write via Database Manager (1000 ticks/batch)      │
│ - Add tenant_id: 'system' (application-level)              │
│                                                              │
│ Configuration:                                               │
│ - Batch size: 1000 ticks                                    │
│ - Batch timeout: 5 seconds                                  │
│ - Tenant: 'system' (shared across all user tenants)        │
└────────────┬────────────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: TimescaleDB Storage (Tick Data)                    │
├─────────────────────────────────────────────────────────────┤
│ Database: suho_trading                                      │
│ Table: market_ticks                                         │
│ Schema Location: /central-hub/shared/schemas/timescaledb/  │
│                  01_market_ticks.sql                        │
│                                                              │
│ Data Stored:                                                 │
│ - time: TIMESTAMPTZ (tick timestamp)                       │
│ - tenant_id: 'system'                                       │
│ - symbol: 'EUR/USD'                                         │
│ - bid, ask, mid, spread                                     │
│ - timestamp_ms, exchange                                     │
│ - source: 'polygon_websocket'                               │
│                                                              │
│ Retention: 90 days (auto-delete via retention policy)      │
│ Compression: After 7 days (10-20x space savings)           │
│                                                              │
│ ✅ TICK DATA PERSISTED IN TIMESCALEDB                       │
└────────────┬────────────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 6: Tick Aggregator Service (NEW!)                     │
├─────────────────────────────────────────────────────────────┤
│ Service: tick-aggregator                                    │
│ Location: /02-data-processing/tick-aggregator/             │
│                                                              │
│ Function:                                                    │
│ - Query ticks from TimescaleDB (batch, scheduled)          │
│ - Aggregate to OHLCV for 7 timeframes                      │
│ - Calculate VWAP, range_pips, body_pips                    │
│ - Publish aggregates to NATS/Kafka                         │
│                                                              │
│ Schedule:                                                    │
│ - M5: Every 5 minutes                                       │
│ - M15: Every 15 minutes                                     │
│ - M30: Every 30 minutes                                     │
│ - H1: Every hour                                            │
│ - H4: Every 4 hours                                         │
│ - D1: Daily at 00:00 UTC                                    │
│ - W1: Weekly on Monday 00:00 UTC                           │
│                                                              │
│ Output Format (Aggregated):                                  │
│ {                                                            │
│   'symbol': 'EUR/USD',                                      │
│   'timeframe': '5m',                                        │
│   'timestamp_ms': 1706198400000,                            │
│   'open': 1.0850, 'high': 1.0855,                          │
│   'low': 1.0848, 'close': 1.0852,                          │
│   'volume': 1234,  (tick count)                            │
│   'vwap': 1.0851,                                           │
│   'range_pips': 0.70, 'body_pips': 0.20,                   │
│   'start_time': '2024-01-25T10:00:00+00:00',               │
│   'end_time': '2024-01-25T10:05:00+00:00',                 │
│   'source': 'live_aggregated',                              │
│   'event_type': 'ohlcv'                                     │
│ }                                                            │
└────────────┬────────────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 7: Message Queue (NATS/Kafka)                         │
├─────────────────────────────────────────────────────────────┤
│ NATS Subject: bars.EURUSD.5m                                │
│ Kafka Topic: aggregate_archive                              │
│                                                              │
│ Message Metadata:                                            │
│ - _source: 'live_aggregated' (from Aggregator)             │
│ - ingested_at: timestamp                                    │
└────────────┬────────────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 8: Data Bridge (Aggregate Routing)                    │
├─────────────────────────────────────────────────────────────┤
│ Service: data-bridge                                        │
│ Location: /02-data-processing/data-bridge/                 │
│                                                              │
│ Function:                                                    │
│ - Subscribe from NATS subject: bars.>                       │
│ - Filter: source = 'live_aggregated' → ClickHouse          │
│ - Batch write via ClickHouse Writer (1000 candles/batch)   │
│ - Validate timeframes: M5, M15, M30, H1, H4, D1, W1       │
│                                                              │
│ Configuration:                                               │
│ - Batch size: 1000 candles                                  │
│ - Batch timeout: 10 seconds                                 │
│ - Tenant: 'system' (shared across all user tenants)        │
└────────────┬────────────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 9: ClickHouse Storage (FASTEST Historical Data!)      │
├─────────────────────────────────────────────────────────────┤
│ Database: suho_analytics                                    │
│ Table: aggregates                                           │
│ Schema Location: /central-hub/shared/schemas/clickhouse/   │
│                  02_aggregates.sql                          │
│                                                              │
│ Data Stored:                                                 │
│ - symbol: 'EUR/USD'                                         │
│ - timeframe: '5m' (one of 7: M5-W1)                        │
│ - timestamp: DateTime64                                     │
│ - OHLCV + volume, vwap, range_pips, body_pips             │
│ - source: 'live_aggregated'                                 │
│                                                              │
│ Retention: 10 years (3650 days via TTL)                    │
│ Compression: 10-100x (automatic)                            │
│                                                              │
│ ✅ AGGREGATED DATA IN CLICKHOUSE (FASTEST UPDATE!)         │
└─────────────────────────────────────────────────────────────┘
```

**Key Benefit**: Live aggregated data arrives in ClickHouse within **minutes** (e.g., M5 arrives 5 minutes after bar close), much faster than REST API historical data which has 15-30 minute delay!

---

## 🔵 HISTORICAL DATA FLOW (Gap Filling Only)

### **Source**: Polygon REST API (Only for Missing Data)

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Gap Detection & Download (Only Missing Data)      │
├─────────────────────────────────────────────────────────────┤
│ Gap Detector → Check missing data in ClickHouse           │
│ Polygon REST API (/v2/aggs)                                │
│ - Download ONLY missing/gap data                           │
│ - Delay: ~15-30 minutes from real-time                     │
│ - Timeframes: M5, M15, M30, H1, H4, D1, W1 (7 total)      │
│ - Symbols: EUR/USD, GBP/USD, XAU/USD, etc.                │
│                                                              │
│ Note: Most data comes from live_aggregated (faster!)       │
└────────────┬────────────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Historical Downloader (Gap Filling Only)           │
├─────────────────────────────────────────────────────────────┤
│ Service: polygon-historical-downloader                      │
│ Location: /00-data-ingestion/polygon-historical-downloader/│
│                                                              │
│ Function:                                                    │
│ - Download ONLY gap/missing bars via REST API              │
│ - Transform to standard format                              │
│ - Publish to NATS/Kafka (NO direct DB write)              │
│                                                              │
│ Use Case:                                                    │
│ - Backfill old data (before live collection started)       │
│ - Fill gaps during downtime/network issues                  │
│ - Initial historical download (e.g., last 2 years)         │
│                                                              │
│ Output Format:                                               │
│ {                                                            │
│   'symbol': 'EUR/USD',                                      │
│   'timeframe': '15m',  (configurable: 5m, 15m, 30m, etc.) │
│   'timestamp_ms': 1706198400000,                            │
│   'open': 1.0850, 'high': 1.0855,                          │
│   'low': 1.0848, 'close': 1.0852,                          │
│   'volume': 15234, 'vwap': 1.0851,                         │
│   'range_pips': 0.70,                                       │
│   'start_time': '2024-01-25T10:00:00+00:00', (ISO string)  │
│   'end_time': '2024-01-25T10:15:00+00:00',                 │
│   'source': 'polygon_historical',                           │
│   'event_type': 'ohlcv'                                     │
│ }                                                            │
│                                                              │
│ Timeframes Downloaded:                                       │
│ - M5  (5 minutes)  - Entry timing & micro patterns         │
│ - M15 (15 minutes) - Intraday signals                       │
│ - M30 (30 minutes) - Confirmation                           │
│ - H1  (1 hour)     - Short-term trend                       │
│ - H4  (4 hours)    - Medium-term trend                      │
│ - D1  (1 day)      - Long-term trend                        │
│ - W1  (1 week)     - Major market structure                 │
└────────────┬────────────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Message Queue (NATS/Kafka)                         │
├─────────────────────────────────────────────────────────────┤
│ NATS Subject: bars.EURUSD.{5m|15m|30m|1h|4h|1d|1w}         │
│ Kafka Topic: aggregate_archive                              │
│                                                              │
│ Message Metadata:                                            │
│ - _source: 'polygon_historical' (gap filling)              │
│ - ingested_at: timestamp                                    │
└────────────┬────────────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Data Bridge (Routing Service)                      │
├─────────────────────────────────────────────────────────────┤
│ Service: data-bridge                                        │
│ Location: /02-data-processing/data-bridge/                 │
│                                                              │
│ Function:                                                    │
│ - Subscribe from NATS subject: bars.>                       │
│ - Filter: _source == 'polygon_historical' → ClickHouse     │
│ - Batch write via ClickHouse Writer (1000 candles/batch)   │
│ - Auto-convert: ISO strings → DateTime64                    │
│ - Validate timeframes: 5m, 15m, 30m, 1h, 4h, 1d, 1w       │
│                                                              │
│ Configuration:                                               │
│ - Batch size: 1000 candles                                  │
│ - Batch timeout: 10 seconds                                 │
│ - Tenant: 'system' (shared across all user tenants)        │
│ - Supported timeframes: [5m, 15m, 30m, 1h, 4h, 1d, 1w]    │
└────────────┬────────────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: ClickHouse Storage (Gap Data)                      │
├─────────────────────────────────────────────────────────────┤
│ Database: suho_analytics                                    │
│ Table: aggregates                                           │
│ Schema Location: /central-hub/shared/schemas/clickhouse/   │
│                  02_aggregates.sql                          │
│                                                              │
│ Data Stored (Gap Filling):                                   │
│ - symbol: 'EUR/USD'                                         │
│ - timeframe: '15m' (one of 7 supported)                    │
│ - timestamp: DateTime64 (bar start time)                    │
│ - source: 'polygon_historical'                              │
│ - timestamp_ms: UInt64                                      │
│ - OHLCV + volume, vwap, range_pips, body_pips             │
│ - start_time, end_time (DateTime64)                         │
│ - source: 'polygon_historical'                              │
│                                                              │
│ Retention: 10 years (3650 days via TTL)                    │
│ Partitioning: By symbol and month                           │
│ Compression: 10-100x (automatic ClickHouse compression)     │
│                                                              │
│ Materialized Views:                                          │
│ - daily_stats: Pre-aggregated daily statistics             │
│ - monthly_stats: Pre-aggregated monthly statistics         │
│                                                              │
│ ✅ DATA PERSISTED IN CLICKHOUSE                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Schema Locations (Central Hub)

All schemas are centralized in Central Hub for **single source of truth**:

### **TimescaleDB Schemas**:
```
/01-core-infrastructure/central-hub/shared/schemas/timescaledb/
├── 01_market_ticks.sql       (Tick data - optional)
├── 02_market_candles.sql     (✅ LIVE 1s bars)
└── 03_market_context.sql     (Economic calendar)
```

### **ClickHouse Schemas**:
```
/01-core-infrastructure/central-hub/shared/schemas/clickhouse/
├── 01_ticks.sql              (Tick data - optional, research only)
└── 02_aggregates.sql         (✅ HISTORICAL 7 timeframes)
```

---

## ✅ Verification Checklist

### **Live Data Flow (Complete)**:
- [x] Polygon WebSocket → Live Collector
- [x] Live Collector → NATS/Kafka (publish only)
- [x] NATS/Kafka → Data Bridge (source filter: NOT 'historical')
- [x] Data Bridge → TimescaleDB.market_candles (via Database Manager)
- [x] Schema in Central Hub: `timescaledb/02_market_candles.sql`
- [x] tenant_id = 'system' (application-level)
- [x] Retention: 90 days

### **Historical Data Flow (Complete)**:
- [x] Polygon REST API → Historical Downloader
- [x] Historical Downloader → NATS/Kafka (publish only)
- [x] NATS/Kafka → Data Bridge (source filter: 'historical')
- [x] Data Bridge → ClickHouse.aggregates (via ClickHouse Writer)
- [x] Schema in Central Hub: `clickhouse/02_aggregates.sql`
- [x] tenant_id = 'system' (application-level)
- [x] 7 timeframes: M5, M15, M30, H1, H4, D1, W1
- [x] Retention: 10 years

---

## 🔧 Environment Variables

### **Data Bridge Service**:
```bash
# Message Queues (from Central Hub)
CENTRAL_HUB_URL=http://suho-central-hub:8080
NATS_URL=nats://suho-nats-server:4222
KAFKA_BROKERS=suho-kafka:9092

# Databases (from Central Hub)
# TimescaleDB (for Live data)
TIMESCALEDB_HOST=suho-timescaledb
TIMESCALEDB_PORT=5432
TIMESCALEDB_DATABASE=suho_trading
TIMESCALEDB_USER=suho_service
TIMESCALEDB_PASSWORD=***

# ClickHouse (for Historical data)
CLICKHOUSE_HOST=suho-clickhouse
CLICKHOUSE_PORT=8123
CLICKHOUSE_DATABASE=suho_analytics
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=***

# DragonflyDB (cache layer)
DRAGONFLYDB_HOST=suho-dragonfly
DRAGONFLYDB_PORT=6379

# Batch Configuration
LIVE_BATCH_SIZE=100
LIVE_BATCH_TIMEOUT=5.0
HISTORICAL_BATCH_SIZE=1000
HISTORICAL_BATCH_TIMEOUT=10.0
```

---

## 📊 Data Storage Summary

| Data Type | Source | Timeframes | Database | Table | Retention | Tenant |
|-----------|--------|------------|----------|-------|-----------|--------|
| **Live** | WebSocket CAS | 1s | TimescaleDB | market_candles | 90 days | system |
| **Historical** | REST API | M5, M15, M30, H1, H4, D1, W1 | ClickHouse | aggregates | 10 years | system |

---

## 🎯 Key Design Principles

1. **Separation of Concerns**: Collectors ONLY publish, Data Bridge handles routing & writes
2. **Intelligent Routing**: Single service (Data Bridge) routes based on data source
3. **Message Queue First**: All data goes through NATS/Kafka (no direct DB writes)
4. **Single Source of Truth**: All schemas centralized in Central Hub
5. **System-Level Tenant**: Data is application-level ('system'), not per-user
6. **Data Persistence**: Both flows guaranteed to persist data to databases
7. **Scalability**: Data Bridge can be scaled horizontally for high throughput

---

**Status**: ✅ **COMPLETE** - All data flows verified and documented.
