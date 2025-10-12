# Data Ingestion & Processing - System Architecture Diagrams

**Version:** 1.0
**Date:** 2025-10-12
**Purpose:** Visual representation of system architecture, data flows, and bottlenecks

---

## 1. High-Level Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         DATA INGESTION PIPELINE                              │
│                         Phase 1: NATS-only Market Data                       │
└──────────────────────────────────────────────────────────────────────────────┘

                        ┌─────────────────────┐
                        │   Polygon.io API    │
                        │   (External SaaS)   │
                        └──────────┬──────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
        ┌──────────────────────┐     ┌───────────────────────┐
        │  Live Collector      │     │ Historical Downloader │
        │  ────────────────    │     │ ─────────────────────│
        │  • WebSocket stream  │     │  • REST API batches   │
        │  • 40 msg/sec        │     │  • 3-month chunks     │
        │  • 14 symbols        │     │  • Gap detection      │
        │  • Continuous        │     │  • Period tracker     │
        │  • Real-time ticks   │     │  • 50k msg/sec burst  │
        └──────────┬───────────┘     └───────────┬───────────┘
                   │                             │
                   └─────────────┬───────────────┘
                                 │
                                 ▼
                 ┌───────────────────────────────┐
                 │   NATS JetStream Server       │
                 │   ──────────────────────      │
                 │   Subject: market.{symbol}.{tf}│
                 │   • In-memory (ephemeral)     │
                 │   • <1ms latency              │
                 │   • 11M msg/sec capacity      │
                 │   • Broadcast pattern (1→N)   │
                 │                               │
                 │   ⚠️  ISSUE: "Slow Consumer"   │
                 │      warnings during bursts   │
                 └───────────┬───────────────────┘
                             │
                             ▼
                 ┌───────────────────────────────┐
                 │   Data Bridge (Consumer)      │
                 │   ────────────────────        │
                 │   • NATS subscriber           │
                 │   • Batch consumer (1000)     │
                 │   • Deduplication cache       │
                 │   • Multi-DB writer           │
                 │                               │
                 │   ⚠️  BOTTLENECK: Single       │
                 │      consumer instance        │
                 └─────┬─────────────┬───────────┘
                       │             │
                ┌──────┘             └──────┐
                │                            │
                ▼                            ▼
    ┌─────────────────────┐      ┌──────────────────────┐
    │   TimescaleDB       │      │    ClickHouse        │
    │   (Live Ticks)      │      │    (Analytics)       │
    │   ───────────       │      │    ──────────        │
    │   • 2-3 day         │      │    • Unlimited       │
    │     retention       │      │      retention       │
    │   • Tick storage    │      │    • Aggregates      │
    │   • OLTP queries    │      │    • OLAP queries    │
    │                     │      │    • Gap detection   │
    │   ⚠️  ISSUE: 2-day   │      │      source          │
    │      retention vs    │      │                      │
    │      30-day gap      │      │                      │
    │      lookback        │      │                      │
    └──────────┬──────────┘      └──────────────────────┘
               │
               ▼
    ┌─────────────────────────────┐
    │  Tick Aggregator V2         │
    │  ─────────────────          │
    │  • Query TimescaleDB        │
    │  • Generate OHLCV candles   │
    │  • Calculate indicators     │
    │  • Multi-timeframe support  │
    │  • Publish back to NATS     │
    │                             │
    │  Components:                │
    │  1. Gap-fill aggregator     │
    │  2. Live aggregator         │
    │  3. Multi-TF aggregator     │
    │  4. Indicator calculator    │
    └─────────────────────────────┘
```

---

## 2. Data Flow Sequence Diagrams

### 2.1 Live Data Flow (Real-time Ticks)

```
┌─────────┐  ┌──────────┐  ┌──────┐  ┌────────┐  ┌─────────┐  ┌──────────┐
│Polygon  │  │  Live    │  │ NATS │  │ Data   │  │Timescale│  │ Click    │
│WebSocket│  │Collector │  │      │  │ Bridge │  │   DB    │  │ House    │
└────┬────┘  └────┬─────┘  └───┬──┘  └───┬────┘  └────┬────┘  └────┬─────┘
     │            │             │         │            │            │
     │ Tick event │             │         │            │            │
     │───────────>│             │         │            │            │
     │            │             │         │            │            │
     │            │ Normalize   │         │            │            │
     │            │ + Enrich    │         │            │            │
     │            │             │         │            │            │
     │            │ Publish     │         │            │            │
     │            │─────────────>│         │            │            │
     │            │ market.     │         │            │            │
     │            │ EURUSD.tick │         │            │            │
     │            │             │         │            │            │
     │            │             │Broadcast│            │            │
     │            │             │─────────>            │            │
     │            │             │         │            │            │
     │            │             │         │ Batch (1000│            │
     │            │             │         │ ticks wait)│            │
     │            │             │         │            │            │
     │            │             │         │ INSERT     │            │
     │            │             │         │────────────>│            │
     │            │             │         │            │            │
     │            │             │         │ INSERT     │            │
     │            │             │         │────────────────────────>│
     │            │             │         │            │            │
     │            │             │         │ ACK        │            │
     │            │             │         │<───────────│            │
     │            │             │         │            │            │
     │            │             │         │ ACK        │            │
     │            │             │         │<───────────────────────│

Latency Breakdown:
─────────────────
Polygon → Collector:    50ms (network)
Collector → NATS:       <1ms (publish)
NATS → Data-bridge:     <1ms (subscribe)
Batch wait:             2400ms ⚠️ BOTTLENECK
DB inserts:             30ms
─────────────────
TOTAL:                  ~2500ms (2.5 seconds)
```

### 2.2 Historical Download Flow (Backfill)

```
┌─────────┐  ┌──────────┐  ┌──────┐  ┌────────┐  ┌──────────┐
│Polygon  │  │Historical│  │ NATS │  │ Data   │  │ Click    │
│REST API │  │Downloader│  │      │  │ Bridge │  │ House    │
└────┬────┘  └────┬─────┘  └───┬──┘  └───┬────┘  └────┬─────┘
     │            │             │         │            │
     │ 1. Check gaps in ClickHouse        │            │
     │            │<───────────────────────────────────│
     │            │             │         │            │
     │ 2. Download 3-month chunk          │            │
     │<───────────│             │         │            │
     │            │             │         │            │
     │ 3-month    │             │         │            │
     │ bars       │             │         │            │
     │───────────>│             │         │            │
     │            │             │         │            │
     │            │ 3. Publish batches (100 bars/batch)│
     │            │─────────────>         │            │
     │            │ (50k/sec)   │         │            │
     │            │             │         │            │
     │            │             │ Broadcast            │
     │            │             │─────────>            │
     │            │             │ (1k/sec)│            │
     │            │             │         │ ⚠️ QUEUE   │
     │            │             │         │ BUILDUP    │
     │            │             │         │            │
     │            │             │         │ INSERT     │
     │            │             │         │────────────>│
     │            │             │         │            │
     │            │ 4. Verify (wait 5s)   │            │
     │            │<───────────────────────────────────│
     │            │ 95% check  │         │            │
     │            │             │         │            │
     │            │ 5. Mark period downloaded          │
     │            │             │         │            │

Issue: 50x throughput mismatch
────────────────────────────────
Publisher:      50,000 msg/sec (burst)
Data-bridge:     1,000 msg/sec (sustained)
Result:         Queue buildup → "Slow Consumer" warning
```

### 2.3 Gap Detection & Backfill Flow

```
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│  Cron    │  │   Gap    │  │ Click    │  │Historical│
│Scheduler │  │ Detector │  │  House   │  │Downloader│
└────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │              │             │
     │ Every 1hr   │              │             │
     │────────────>│              │             │
     │             │              │             │
     │             │ Query gaps   │             │
     │             │──────────────>             │
     │             │ (last 30 days)             │
     │             │              │             │
     │             │ Missing dates│             │
     │             │<─────────────│             │
     │             │              │             │
     │             │ Group into ranges          │
     │             │ (START/MIDDLE/END gaps)    │
     │             │              │             │
     │             │ Trigger backfill           │
     │             │────────────────────────────>│
     │             │              │             │
     │             │              │ Download    │
     │             │              │ missing     │
     │             │              │ data        │
     │             │              │             │

Gap Types:
──────────
START gap:   Missing first 7 days of range
MIDDLE gap:  Missing days 15-20 (data bridge crash)
END gap:     Missing last 7 days (ongoing collection issue)

⚠️  ISSUE: 30-day lookback vs 2-day TimescaleDB retention
─────────────────────────────────────────────────────────
Gap detector checks 30 days back
TimescaleDB only retains 2 days
Can't backfill gaps older than 2 days from TimescaleDB
Must rely on ClickHouse (but ClickHouse is gap source!)
```

---

## 3. Bottleneck Analysis Diagrams

### 3.1 Current Architecture - Single Consumer Bottleneck

```
                    Historical Download (50k msg/sec)
                              ↓
                    ┌─────────────────┐
                    │  NATS Server    │
                    │  ─────────────  │
                    │  Queue depth:   │
                    │  50,000 msgs    │ ⚠️ BUILDUP
                    │  ─────────────  │
                    │  Capacity:      │
                    │  11M msg/sec    │ ✅ NOT bottleneck
                    └────────┬────────┘
                             │
                             ▼ 1,000 msg/sec
                    ┌─────────────────┐
                    │  Data Bridge    │
                    │  ─────────────  │
                    │  Instance: 1    │ ⚠️ BOTTLENECK
                    │  Batch: 1000    │
                    │  ─────────────  │
                    │  Throughput:    │
                    │  1,000 msg/sec  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  ClickHouse     │
                    │  ─────────────  │
                    │  Capacity:      │
                    │  1M insert/sec  │ ✅ NOT bottleneck
                    └─────────────────┘

Problem: 50x throughput mismatch
Publisher sends 50,000 msg/sec
Consumer processes 1,000 msg/sec
Result: Queue buildup, "Slow Consumer" warning
```

### 3.2 Proposed Architecture - Multi-Consumer with Queue Groups

```
                    Historical Download (50k msg/sec)
                              ↓
                    ┌─────────────────┐
                    │  NATS Server    │
                    │  ─────────────  │
                    │  Queue group:   │
                    │  "data-bridge-  │
                    │   workers"      │
                    │  ─────────────  │
                    │  Load balance:  │
                    │  Round-robin    │
                    └────────┬────────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
                ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ Bridge-1 │ │ Bridge-2 │ │ Bridge-3 │
        │ ──────── │ │ ──────── │ │ ──────── │
        │ EUR*, GBP│ │ USD*, AUD│ │ XAU*, NZD│
        │ symbols  │ │ symbols  │ │ symbols  │
        │          │ │          │ │          │
        │ 17k/sec  │ │ 17k/sec  │ │ 17k/sec  │
        └────┬─────┘ └────┬─────┘ └────┬─────┘
             │            │            │
             └────────────┼────────────┘
                          │
                          ▼
                ┌─────────────────┐
                │  ClickHouse     │
                │  ─────────────  │
                │  Total:         │
                │  51k insert/sec │ ✅ RESOLVED
                └─────────────────┘

Solution: 3x parallel consumers
Each handles 17k msg/sec (within capacity)
Total throughput: 51k msg/sec
Result: No queue buildup, no slow consumer warnings
```

### 3.3 Latency Comparison - Current vs Optimized

```
CURRENT (Batch size: 1000, Flush: 5s)
─────────────────────────────────────
┌──────────────────────────────────────────────────────────┐
│ Polygon → Collector → NATS → Data-bridge → Database     │
│  50ms       <1ms      <1ms      2400ms       30ms        │
│                              ↑                           │
│                         BOTTLENECK                       │
│                         (batch wait)                     │
└──────────────────────────────────────────────────────────┘
TOTAL: ~2500ms (2.5 seconds)


OPTIMIZED (Dynamic batch: 10 live, 500 historical, Flush: 1s)
──────────────────────────────────────────────────────────────
LIVE DATA:
┌──────────────────────────────────────────────────────────┐
│ Polygon → Collector → NATS → Data-bridge → Database     │
│  50ms       <1ms      <1ms      100ms        30ms        │
│                              ↑                           │
│                         OPTIMIZED                        │
│                         (smaller batch)                  │
└──────────────────────────────────────────────────────────┘
TOTAL: ~182ms (0.18 seconds) ✅ 13x faster

HISTORICAL DATA:
┌──────────────────────────────────────────────────────────┐
│ Polygon → Downloader → NATS → Data-bridge → Database    │
│  API rate   chunk      <1ms      1000ms       30ms       │
│  limited    optimized           ↑                        │
│                              ACCEPTABLE                   │
│                              (high throughput)            │
└──────────────────────────────────────────────────────────┘
TOTAL: ~1031ms (1 second) - acceptable for batch processing
```

---

## 4. Message Flow Patterns

### 4.1 NATS Subject Hierarchy

```
market.*
├── market.EURUSD.*
│   ├── market.EURUSD.tick        (Live ticks, ~30/sec)
│   ├── market.EURUSD.5m          (5-min candles)
│   ├── market.EURUSD.15m         (15-min candles)
│   ├── market.EURUSD.30m         (30-min candles)
│   ├── market.EURUSD.1h          (1-hour candles)
│   ├── market.EURUSD.4h          (4-hour candles)
│   ├── market.EURUSD.1d          (Daily candles)
│   └── market.EURUSD.1w          (Weekly candles)
│
├── market.GBPUSD.*
│   └── (same timeframes)
│
├── market.XAUUSD.*
│   └── (same timeframes)
│
└── (12 more symbols)

Proposed Priority Subjects:
──────────────────────────
market.live.*                     (High priority)
├── market.live.EURUSD.tick
└── (real-time data)

market.historical.*               (Low priority)
├── market.historical.EURUSD.1m
└── (backfill data)
```

### 4.2 Database Write Patterns

```
┌────────────────────────────────────────────────────────────────┐
│                    DATA PERSISTENCE STRATEGY                   │
└────────────────────────────────────────────────────────────────┘

TimescaleDB (Live Ticks - 2-3 day retention)
───────────────────────────────────────────
┌─────────────────────────────────────────────┐
│ Table: market_ticks                         │
│ ───────────────                             │
│ Columns:                                    │
│   • timestamp (primary key)                 │
│   • symbol                                  │
│   • bid, ask, mid                           │
│   • spread                                  │
│   • tenant_id (multi-tenant)                │
│                                             │
│ Hypertable: Partitioned by timestamp (1hr) │
│ Retention: 2-3 days (auto-drop old chunks) │
│ Indexes: (symbol, timestamp), (tenant_id)  │
│                                             │
│ Write pattern: Batch insert (1000 rows)    │
│ Throughput: 100-1000 inserts/sec           │
└─────────────────────────────────────────────┘
              │
              ▼ (Read by Tick Aggregator)
┌─────────────────────────────────────────────┐
│ OHLCV Candle Generation                     │
│ ───────────────────────                     │
│ SELECT                                      │
│   symbol,                                   │
│   time_bucket('5 minutes', timestamp),      │
│   first(mid, timestamp) as open,            │
│   max(mid) as high,                         │
│   min(mid) as low,                          │
│   last(mid, timestamp) as close,            │
│   count(*) as volume                        │
│ FROM market_ticks                           │
│ GROUP BY symbol, time_bucket               │
└─────────────────────────────────────────────┘
              │
              ▼ (Publish to NATS)

ClickHouse (Analytics - Unlimited retention)
──────────────────────────────────────────
┌─────────────────────────────────────────────┐
│ Table: aggregates                           │
│ ────────────                                │
│ Columns:                                    │
│   • timestamp (DateTime64)                  │
│   • symbol (String)                         │
│   • timeframe (String)                      │
│   • open, high, low, close (Float64)        │
│   • volume (UInt64)                         │
│   • source (String: 'polygon_historical',   │
│             'polygon_live', 'polygon_gap')  │
│   • event_type (String)                     │
│                                             │
│ Engine: MergeTree()                         │
│ ORDER BY (symbol, timeframe, timestamp)     │
│ PARTITION BY toYYYYMM(timestamp)            │
│                                             │
│ Write pattern: Batch insert (500-1000 rows)│
│ Throughput: 500-50,000 inserts/sec         │
└─────────────────────────────────────────────┘
              │
              ▼ (Used by Gap Detector)
┌─────────────────────────────────────────────┐
│ Gap Detection Query                         │
│ ──────────────────                          │
│ WITH expected_dates AS (                    │
│   SELECT                                    │
│     toDate(timestamp) as date               │
│   FROM aggregates                           │
│   WHERE symbol = 'EUR/USD'                  │
│     AND timeframe = '1m'                    │
│     AND timestamp >= now() - INTERVAL 30 DAY│
│ )                                           │
│ SELECT missing_dates                        │
│ FROM generate_series(...)                   │
│ WHERE date NOT IN (SELECT date FROM...)    │
└─────────────────────────────────────────────┘
```

---

## 5. Scaling Strategies

### 5.1 Horizontal Scaling - Data Bridge

```
BEFORE (Single Instance):
─────────────────────────
              ┌──────────┐
              │  NATS    │
              └────┬─────┘
                   │
                   ▼
              ┌──────────┐
              │ Bridge-1 │ ⚠️ Bottleneck
              │ (solo)   │    All messages
              └────┬─────┘    go here
                   │
                   ▼
              ┌──────────┐
              │ Database │
              └──────────┘


AFTER (3 Instances with Queue Group):
──────────────────────────────────────
              ┌──────────┐
              │  NATS    │
              │ Queue:   │
              │ "workers"│
              └────┬─────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
        ▼          ▼          ▼
   ┌────────┐ ┌────────┐ ┌────────┐
   │Bridge-1│ │Bridge-2│ │Bridge-3│ ✅ Load balanced
   │EUR,GBP │ │USD,AUD │ │XAU,NZD │    3x throughput
   │symbols │ │symbols │ │symbols │
   └───┬────┘ └───┬────┘ └───┬────┘
       │          │          │
       └──────────┼──────────┘
                  │
                  ▼
              ┌──────────┐
              │ Database │
              └──────────┘

Configuration:
─────────────
# docker-compose.yml
data-bridge:
  deploy:
    replicas: 3

# data-bridge/main.py
await nats.subscribe(
    subject="market.>",
    queue="data-bridge-workers",  # Enable queue group
    cb=message_handler
)

Load Balancing:
──────────────
Message 1 → Bridge-1 (round-robin)
Message 2 → Bridge-2
Message 3 → Bridge-3
Message 4 → Bridge-1 (cycle repeats)
```

### 5.2 Vertical Scaling - Resource Allocation

```
┌────────────────────────────────────────────────────────────────┐
│                    RESOURCE ALLOCATION                         │
└────────────────────────────────────────────────────────────────┘

CURRENT (Development):
─────────────────────
┌─────────────────┐
│ Data Bridge     │
│ ─────────────   │
│ CPU: 1 core     │
│ RAM: 512 MB     │
│ Disk: Minimal   │
└─────────────────┘

PROPOSED (Production):
─────────────────────
┌─────────────────┐
│ Data Bridge     │
│ ─────────────   │
│ CPU: 2 cores    │ ✅ Handle parallel processing
│ RAM: 2 GB       │ ✅ Larger batch buffers
│ Disk: 1 GB      │ ✅ Disk buffer (fallback)
│                 │
│ Limits:         │
│ CPU: 4 cores    │ (max burst)
│ RAM: 4 GB       │ (max burst)
└─────────────────┘

docker-compose.yml:
──────────────────
data-bridge:
  deploy:
    resources:
      reservations:
        cpus: '2'
        memory: 2G
      limits:
        cpus: '4'
        memory: 4G
```

### 5.3 Database Scaling Strategy

```
┌────────────────────────────────────────────────────────────────┐
│                    TIMESCALEDB SCALING                         │
└────────────────────────────────────────────────────────────────┘

CURRENT (Single Node):
─────────────────────
┌────────────────────┐
│  TimescaleDB       │
│  ──────────────    │
│  • Single instance │
│  • 2-3 day retain  │
│  • 100 ins/sec     │
└────────────────────┘


FUTURE (Read Replicas):
──────────────────────
┌────────────────────┐
│ TimescaleDB        │
│ (Primary - Write)  │
│ ──────────────     │
│ • All writes       │
│ • Replication      │
└─────────┬──────────┘
          │ (async replication)
          ├─────────────────────┐
          │                     │
          ▼                     ▼
┌──────────────────┐  ┌──────────────────┐
│ Replica 1        │  │ Replica 2        │
│ (Read-only)      │  │ (Read-only)      │
│ ────────────     │  │ ────────────     │
│ • Aggregator     │  │ • API queries    │
│   queries        │  │                  │
└──────────────────┘  └──────────────────┘

Benefits:
────────
✅ Writes: 1x primary (no change)
✅ Reads: 3x capacity (1 primary + 2 replicas)
✅ Failover: Replicas can promote to primary
```

```
┌────────────────────────────────────────────────────────────────┐
│                    CLICKHOUSE SCALING                          │
└────────────────────────────────────────────────────────────────┘

CURRENT (Single Node):
─────────────────────
┌────────────────────┐
│  ClickHouse        │
│  ──────────────    │
│  • Single shard    │
│  • No replication  │
│  • 500k ins/sec    │
└────────────────────┘


FUTURE (Sharded + Replicated):
──────────────────────────────
Shard 1:                    Shard 2:
┌─────────────┐            ┌─────────────┐
│ CH Node 1   │◄───────────┤ CH Node 3   │
│ (Primary)   │ Replication│ (Primary)   │
│ EUR*, GBP*  │            │ USD*, AUD*  │
└──────┬──────┘            └──────┬──────┘
       │                          │
       ▼                          ▼
┌─────────────┐            ┌─────────────┐
│ CH Node 2   │            │ CH Node 4   │
│ (Replica)   │            │ (Replica)   │
│ EUR*, GBP*  │            │ USD*, AUD*  │
└─────────────┘            └─────────────┘

Benefits:
────────
✅ Horizontal scaling: 2x write capacity (2 shards)
✅ High availability: 2x redundancy (2 replicas)
✅ Query parallelism: Distributed queries across shards
```

---

## 6. Error Recovery Flows

### 6.1 NATS Downtime - Disk Buffer Fallback

```
┌──────────┐  ┌──────────┐  ┌──────┐  ┌──────────────┐
│Publisher │  │   NATS   │  │ Disk │  │ Data Bridge  │
└────┬─────┘  └────┬─────┘  │Buffer│  └──────────────┘
     │             │         └───┬──┘
     │             │             │
     │ Publish     │             │
     │────────────>│             │
     │             │ ✅ Success  │
     │             │             │
     │ Publish     │             │
     │────────────>│             │
     │             │ ❌ Failure  │
     │             │ (down)      │
     │             │             │
     │ Retry #1    │             │
     │────────────>│             │
     │             │ ❌ Failure  │
     │             │             │
     │ Retry #2    │             │
     │────────────>│             │
     │             │ ❌ Failure  │
     │             │             │
     │ Retry #3    │             │
     │────────────>│             │
     │             │ ❌ Failure  │
     │             │             │
     │ Circuit     │             │
     │ breaker     │             │
     │ triggered   │             │
     │             │             │
     │ Write to    │             │
     │ disk buffer │────────────>│
     │             │             │ ✅ Saved
     │             │             │ /data/buffer/
     │             │             │ buffer_<uuid>.json

     (Later, when NATS recovers)

     │ Flush       │             │
     │ buffer      │             │
     │ (periodic)  │             │
     │             │             │
     │ Read buffer │<────────────│
     │<────────────│             │
     │             │             │
     │ Publish     │             │
     │────────────>│             │
     │             │ ✅ Success  │
     │             │             │
     │ Delete      │             │
     │ buffer file │────────────>│
     │             │             │ ✅ Deleted
```

### 6.2 Data-bridge Crash - Gap Detection Recovery

```
┌──────────┐  ┌────────┐  ┌──────────┐  ┌──────────┐
│Publisher │  │  NATS  │  │  Data    │  │ Click    │
│          │  │        │  │  Bridge  │  │ House    │
└────┬─────┘  └───┬────┘  └────┬─────┘  └────┬─────┘
     │            │             │             │
     │ Publish    │             │             │
     │───────────>│             │             │
     │            │             │             │
     │            │ Deliver     │             │
     │            │────────────>│             │
     │            │             │ ✅ Healthy  │
     │            │             │             │
     │            │             │ INSERT      │
     │            │             │────────────>│
     │            │             │             │
     │            │             │ ❌ CRASH    │
     │            │             │ (OOM/bug)   │
     │            │             │             │
     │ Publish    │             │             │
     │───────────>│             │             │
     │            │             │             │
     │            │ Buffer      │             │
     │            │ messages    │             │ ⚠️ Data not
     │            │ (in memory) │             │   persisted
     │            │             │             │

     (10 minutes later - NATS drops messages)

     │            │ ⚠️ Queue    │             │
     │            │ too full    │             │
     │            │ Drop msgs   │             │
     │            │             │             │

     (1 hour later - Gap detector runs)

     │            │             │             │
┌────┴─────┐      │             │             │
│   Gap    │      │             │             │
│ Detector │      │             │             │
└────┬─────┘      │             │             │
     │            │             │             │
     │ Query gaps │             │             │
     │────────────────────────────────────────>│
     │            │             │             │
     │ Missing:   │             │             │
     │ 10:00-11:00│             │             │
     │<───────────────────────────────────────│
     │            │             │             │
     │ Trigger    │             │             │
     │ backfill   │             │             │
     │───────────>│             │             │
     │            │             │             │

     Result: Data loss prevented (but delayed by 1 hour)
```

---

## 7. Recommended Architecture - After Fixes

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    OPTIMIZED ARCHITECTURE (PHASE 2)                          │
└──────────────────────────────────────────────────────────────────────────────┘

                        ┌─────────────────────┐
                        │   Polygon.io API    │
                        └──────────┬──────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
        ┌──────────────────────┐     ┌───────────────────────┐
        │  Live Collector      │     │ Historical Downloader │
        │  • 40 msg/sec        │     │  • 50k msg/sec burst  │
        │  • Priority: HIGH    │     │  • Priority: LOW      │
        └──────────┬───────────┘     └───────────┬───────────┘
                   │                             │
                   │ Separate subjects           │
                   │ for prioritization          │
                   │                             │
                   ▼                             ▼
         market.live.*               market.historical.*
                   │                             │
                   └─────────────┬───────────────┘
                                 │
                                 ▼
                 ┌───────────────────────────────┐
                 │   NATS JetStream Server       │
                 │   ──────────────────────      │
                 │   Queue Group: "workers"      │
                 │   Load Balancing: Round-robin │
                 │   ✅ No slow consumer warnings │
                 └───────────┬───────────────────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
                ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ Bridge-1 │ │ Bridge-2 │ │ Bridge-3 │
        │ ──────── │ │ ──────── │ │ ──────── │
        │ 2 cores  │ │ 2 cores  │ │ 2 cores  │
        │ 2GB RAM  │ │ 2GB RAM  │ │ 2GB RAM  │
        │          │ │          │ │          │
        │ Batch:   │ │ Batch:   │ │ Batch:   │
        │ Live:10  │ │ Live:10  │ │ Live:10  │
        │ Hist:500 │ │ Hist:500 │ │ Hist:500 │
        │ ──────── │ │ ──────── │ │ ──────── │
        │ ✅ 17k/s  │ │ ✅ 17k/s  │ │ ✅ 17k/s  │
        └────┬─────┘ └────┬─────┘ └────┬─────┘
             │            │            │
             └────────────┼────────────┘
                          │
               ┌──────────┴──────────┐
               │                     │
               ▼                     ▼
    ┌─────────────────────┐  ┌──────────────────────┐
    │   TimescaleDB       │  │    ClickHouse        │
    │   ─────────────     │  │    ──────────        │
    │   Retention: 7 days │  │    Retention: ∞      │
    │   ✅ Increased from  │  │    Partitioned by    │
    │      2-3 days       │  │    year-month        │
    │                     │  │                      │
    │   Write: 500/sec    │  │    Write: 50k/sec    │
    │   Read replicas: 2  │  │    Shards: 2         │
    └──────────┬──────────┘  └──────────────────────┘
               │
               ▼
    ┌─────────────────────────────┐
    │  Tick Aggregator V2         │
    │  ─────────────────          │
    │  • Query TimescaleDB        │
    │  • Parallel processing      │
    │  • Multi-timeframe          │
    │  • 13 technical indicators  │
    │  • Publish to NATS          │
    └─────────────────────────────┘

KEY IMPROVEMENTS:
────────────────
✅ 3x data-bridge instances (queue group)
✅ Priority subjects (live vs historical)
✅ Dynamic batch sizing (10 live, 500 historical)
✅ 7-day TimescaleDB retention (was 2-3 days)
✅ 15-minute gap checks (was 1 hour)
✅ Resource limits (2 cores, 2GB RAM each)
✅ Prometheus metrics + Grafana dashboards
✅ Circuit breakers + disk buffer fallback

EXPECTED PERFORMANCE:
────────────────────
Live data latency: <200ms (was 2500ms)
Historical throughput: 51k msg/sec (was 1k msg/sec)
No slow consumer warnings
No live data starvation during backfills
Zero data loss during NATS/bridge failures
```

---

**Document Version:** 1.0
**Last Updated:** 2025-10-12
**Maintained by:** System Architecture Team

