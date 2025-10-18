# 🎯 AI Trading System - Service Planning Skill Guide

> **Version**: 2.0.0 (Service-Centric Redesign)
> **Last Updated**: 2025-10-18
> **Purpose**: Per-service planning guide untuk AI Trading System development
> **Format**: 1 Skill = 1 Service (17 services total)

---

## 📋 Overview

**Skill Purpose**: Guide Claude Code dalam planning tasks BERDASARKAN SERVICE yang terlibat.

**Core Principle**: **"Know Your Service → Understand Dependencies → Plan Correctly"**

**Format**: Setiap service punya dedicated section dengan:
- **Purpose**: Fungsi service apa
- **Input**: Baca dari mana (tables/APIs)
- **Output**: Tulis ke mana (tables)
- **Requirements**: Database, messaging, infrastructure yang dibutuhkan
- **Common Tasks**: Typical tasks untuk service ini
- **Planning Examples**: Contoh planning scenario

---

## 🏗️ System Architecture Overview

### **3-Phase Structure**

```
Phase 1: DATA (✅ Active - 7 services)
├─ 00-data-ingestion/          (4 services)
├─ 01-core-infrastructure/     (1 service - central-hub)
└─ 02-data-processing/         (2 services)

Phase 2: TRAINING (⚠️ To Implement - 2 services)
└─ 03-ml-training/

Phase 3: TRADING (⚠️ Future - 8 services)
├─ 04-trading-execution/       (4 services)
├─ 05-broker-integration/      (1 service)
├─ 06-backtesting/             (1 service)
└─ 07-business-platform/       (2 services)
```

### **Service Index**

| # | Service | Phase | Status | Priority |
|---|---------|-------|--------|----------|
| 1 | [polygon-live-collector](#service-1-polygon-live-collector) | Data | ✅ Active | P0 |
| 2 | [polygon-historical-downloader](#service-2-polygon-historical-downloader) | Data | ✅ Active | P0 |
| 3 | [dukascopy-historical-downloader](#service-3-dukascopy-historical-downloader) | Data | ✅ Active | P1 |
| 4 | [external-data-collector](#service-4-external-data-collector) | Data | ✅ Active | P1 |
| 5 | [central-hub](#service-5-central-hub) | Infrastructure | ✅ Active | P0 |
| 6 | [tick-aggregator](#service-6-tick-aggregator) | Processing | ✅ Active | P0 |
| 7 | [feature-engineering-service](#service-7-feature-engineering-service) | Processing | ✅ Active | P0 |
| 8 | [supervised-training-service](#service-8-supervised-training-service) | Training | ⚠️ Placeholder | P1 |
| 9 | [finrl-training-service](#service-9-finrl-training-service) | Training | ⚠️ To Build | P1 |
| 10 | [inference-service](#service-10-inference-service) | Trading | ⚠️ Placeholder | P2 |
| 11 | [execution-service](#service-11-execution-service) | Trading | ⚠️ Placeholder | P2 |
| 12 | [risk-management](#service-12-risk-management) | Trading | ⚠️ Placeholder | P2 |
| 13 | [performance-monitoring](#service-13-performance-monitoring) | Trading | ⚠️ To Build | P2 |
| 14 | [mt5-connector](#service-14-mt5-connector) | Broker | ⚠️ Placeholder | P3 |
| 15 | [backtesting-service](#service-15-backtesting-service) | Backtesting | ⚠️ Placeholder | P2 |
| 16 | [analytics-service](#service-16-analytics-service) | Business | ⚠️ Placeholder | P3 |
| 17 | [notification-hub](#service-17-notification-hub) | Business | ⚠️ Placeholder | P3 |

---

## 📊 PHASE 1: DATA SERVICES (✅ Active)

---

### **Service 1: polygon-live-collector**

**Folder**: `00-data-ingestion/polygon-live-collector`
**Status**: ✅ Active (Production)
**Priority**: P0 (Critical)

#### **Purpose**
Real-time streaming live market data dari Polygon.io WebSocket API untuk forex & crypto pairs.

#### **Input Sources**
- **External API**: Polygon.io WebSocket API
  - Forex pairs: C:EURUSD, C:XAUUSD, dll (14 pairs)
  - Real-time bid/ask/spread data
  - Sub-second latency

#### **Output Targets**
- **TimescaleDB.live_ticks** (table)
  - Columns: timestamp_ms, symbol, bid, ask, spread
  - Retention: 3 days (TimescaleDB auto-delete)
  - Volume: ~100K ticks/day per symbol

#### **Requirements**

**Infrastructure Dependencies**:
- ✅ PostgreSQL/TimescaleDB (suho-postgresql)
- ✅ NATS cluster (nats-1, nats-2, nats-3) - for event streaming
- ✅ Kafka (suho-kafka) - for tick distribution
- ⚠️ DragonflyDB (optional caching)

**Configuration**:
```yaml
# Environment variables
POLYGON_API_KEY: <secret>
TIMESCALEDB_HOST: suho-postgresql
NATS_URL: nats://nats-1:4222,nats://nats-2:4222,nats://nats-3:4222
KAFKA_BROKERS: suho-kafka:9092
```

**Tech Stack**:
- Python 3.11+
- websockets library
- asyncio for concurrent connections
- NATS.py, aiokafka

#### **Common Tasks**

**Task 1: Adding New Trading Pairs**
```markdown
## Plan: Add NZD/USD to live collector

**Current State**:
- 14 pairs currently streaming ✅
- Polygon supports NZD/USD ✅

**Steps**:
1. Update config/pairs.yaml
   - Add: symbol: "NZD/USD", polygon_symbol: "C:NZDUSD"
2. No code changes needed (dynamic pair loading)
3. Restart service: docker-compose restart polygon-live-collector
4. Verify logs: "Subscribed to C:NZDUSD"
5. Check TimescaleDB: SELECT COUNT(*) FROM live_ticks WHERE symbol = 'C:NZDUSD'

**Testing**:
- Wait 5 minutes for data
- Verify tick count > 0
- Check bid/ask values reasonable
```

**Task 2: Fixing Connection Issues**
```markdown
## Debug: WebSocket disconnections

**Symptoms**:
- Logs show "Connection closed"
- Gap in tick data

**Investigation**:
1. Check Polygon API status (api.polygon.io)
2. Check network connectivity
3. Check POLYGON_API_KEY validity
4. Review error logs

**Common Fixes**:
- Reconnection logic already implemented (auto-retry)
- Check rate limits (5 req/sec for free tier)
- Verify API key has forex entitlement
```

**Task 3: Gap Backfilling**
```markdown
## Plan: Backfill missing ticks

**Scenario**: Service was down for 2 hours

**Strategy**:
1. Identify gap period (check logs)
2. Use polygon-historical-downloader for backfill
3. Validate no duplicates (timestamp_ms unique constraint)

**Note**: For gaps < 7 days, use polygon-historical
       For older data, use dukascopy-historical
```

#### **Monitoring & Health Checks**

**Health Endpoint**: `/health`
**Metrics**:
- Ticks received per second
- WebSocket connection status
- Last successful write timestamp
- Gap detection alerts

#### **Documentation References**
- Architecture: `SERVICE_ARCHITECTURE_AND_FLOW.md` line 276-298
- Tables: `table_database_input.md` (TimescaleDB.live_ticks)

---

### **Service 2: polygon-historical-downloader**

**Folder**: `00-data-ingestion/polygon-historical-downloader`
**Status**: ✅ Active (Gap Filling Only)
**Priority**: P0 (Critical for gaps)

#### **Purpose**
**Gap filling ONLY** untuk live_aggregates table (bukan untuk historical download!). Service ini mengisi data yang hilang dalam 7 hari terakhir.

⚠️ **IMPORTANT**: Polygon-historical adalah untuk **GAP FILLING**, bukan initial historical download. Dukascopy handles historical data.

#### **Input Sources**
- **Polygon REST API**: `/v2/aggs/ticker/{symbol}/range/{multiplier}/{timespan}/{from}/{to}`
  - Rate limit: 5 requests/second
  - Aggregates API (5-minute bars minimum)

#### **Output Targets**
- **ClickHouse.live_aggregates** (GAP FILLING TABLE)
  - Columns: time, symbol, timeframe, open, high, low, close, volume, tick_count
  - Retention: 7 days
  - Purpose: Fill gaps dari live polygon collector

#### **Requirements**

**Infrastructure Dependencies**:
- ✅ ClickHouse (suho-clickhouse) - target table
- ✅ NATS cluster - gap detection events
- ⚠️ Kafka (optional)

**Configuration**:
```yaml
# config/schedule.yaml
download:
  start_date: "today-7days"  # ONLY last 7 days!
  end_date: "today"
  timeframe: "minute"
  multiplier: 5  # 5-minute bars (ClickHouse schema requirement)

schedules:
  initial_download:
    enabled: false  # DISABLED - gap filling only!
  gap_check:
    interval_hours: 1  # Check every hour
```

**Environment Variables**:
```env
POLYGON_API_KEY=<secret>
CLICKHOUSE_HOST=suho-clickhouse
CLICKHOUSE_DATABASE=suho_analytics
CLICKHOUSE_PASSWORD=<secret>
```

#### **Common Tasks**

**Task 1: Verify Gap Filling Configuration**
```markdown
## Check: Is polygon-historical configured correctly?

**Verify**:
1. Check target table:
   - config.py line 171: table = 'live_aggregates' ✅
   - NOT 'historical_aggregates' ❌

2. Check timeframe:
   - schedule.yaml multiplier: 5 (NOT 1) ✅
   - ClickHouse enum only supports: 5m, 15m, 30m, 1h, 4h, 1d, 1w

3. Check date range:
   - start_date: "today-7days" (NOT "2023-01-01") ✅
   - end_date: "today"

4. Check initial_download:
   - enabled: false ✅

**If misconfigured**: Update config files, rebuild container
```

**Task 2: Manual Gap Filling**
```markdown
## Plan: Fill gap from 2025-10-15 to 2025-10-17

**Steps**:
1. Check gap exists:
   ```sql
   SELECT toDate(time) as date, COUNT(*) as bars
   FROM live_aggregates
   WHERE symbol = 'C:EURUSD' AND timeframe = '5m'
     AND toDate(time) BETWEEN '2025-10-15' AND '2025-10-17'
   GROUP BY date
   ORDER BY date;
   ```

2. Trigger download:
   - Set HISTORICAL_START_DATE='2025-10-15'
   - Set HISTORICAL_END_DATE='2025-10-17'
   - Run: docker-compose restart polygon-historical-downloader

3. Verify fill:
   - Check logs: "Downloaded X bars for C:EURUSD"
   - Re-run query above, verify COUNT increased
```

**Task 3: Fix Table Name Error**
```markdown
## Bug Fix: Service writing to wrong table

**Symptoms**:
- Logs: "Unknown table 'historical_aggregates'"
- OR: "Unknown table 'ticks'"

**Root Cause**: Config file wrong table name

**Fix**:
1. src/config.py line 171:
   - Change: 'historical_aggregates' → 'live_aggregates'

2. src/gap_detector.py (4 locations):
   - Change: 'historical_aggregates' → 'live_aggregates'
   - Change: 'timestamp' → 'time'
   - Remove: "AND source = 'polygon'" (column doesn't exist)

3. Rebuild: docker-compose build polygon-historical-downloader
4. Test: docker-compose up -d polygon-historical-downloader
```

#### **Monitoring & Health Checks**

**Health Endpoint**: `/health`
**Metrics**:
- Gap detection runs per hour
- Bars downloaded per gap
- Last successful gap fill

**Alerts**:
- Gap > 1 hour detected
- Download failures

#### **Documentation References**
- Architecture: `SERVICE_ARCHITECTURE_AND_FLOW.md` line 301-320
- Tables: `table_database_input.md` (ClickHouse.live_aggregates)
- Config: `config/schedule.yaml`

---

### **Service 3: dukascopy-historical-downloader**

**Folder**: `00-data-ingestion/dukascopy-historical-downloader`
**Status**: ✅ Active (Historical Data Source)
**Priority**: P1 (Backup/Historical)

#### **Purpose**
Download **historical tick data** dari Dukascopy untuk long-term storage. Ini adalah sumber utama untuk training data (2023-2025).

#### **Input Sources**
- **Dukascopy API**: Historical tick data
  - Date range: 2023-01-01 to present
  - Format: Bi5 files (binary tick data)
  - Free tier available

#### **Output Targets**
- **ClickHouse.historical_ticks** (unlimited retention)
  - Columns: timestamp_ms, symbol, bid, ask, bid_volume, ask_volume
  - Purpose: Long-term storage untuk ML training
  - Volume: ~2.8 years (2023-2025), 14 pairs

#### **Requirements**

**Infrastructure Dependencies**:
- ✅ ClickHouse (suho-clickhouse)
- ✅ NATS cluster (optional for progress events)

**Configuration**:
```yaml
# config/pairs.yaml
clickhouse:
  host: suho-clickhouse
  database: suho_analytics
  table: "historical_ticks"  # NOT 'ticks'!

download:
  start_date: "2023-01-01"
  end_date: "today"
  batch_size: 10000
```

#### **Common Tasks**

**Task 1: Download Historical Data for New Pair**
```markdown
## Plan: Download GBP/JPY historical data (2023-2025)

**Steps**:
1. Add to config/pairs.yaml:
   ```yaml
   - symbol: "GBP/JPY"
     dukascopy_symbol: "GBPJPY"
     priority: 3
   ```

2. Run download:
   ```bash
   docker-compose exec dukascopy-historical python src/downloader.py \
     --symbol GBPJPY \
     --start-date 2023-01-01 \
     --end-date today
   ```

3. Monitor progress:
   - Logs: "Downloaded 2023-01: 125,000 ticks"
   - Check ClickHouse:
     ```sql
     SELECT COUNT(*) FROM historical_ticks
     WHERE symbol = 'GBPJPY'
       AND timestamp_ms >= 1672531200000;
     ```

**Estimated Time**: 2-3 hours for 2.8 years
```

**Task 2: Fix Table Name Error**
```markdown
## Bug Fix: Unknown table 'ticks'

**Symptoms**:
- Error: "Unknown table 'suho_analytics.ticks'"

**Root Cause**:
- config.py line 133: default = 'ticks' (wrong!)
- pairs.yaml line 131: table: "ticks" (wrong!)

**Fix**:
1. config.py: Change 'ticks' → 'historical_ticks'
2. pairs.yaml: Change "ticks" → "historical_ticks"
3. Rebuild + restart
```

**Task 3: Gap Detection in Historical Data**
```markdown
## Plan: Find missing dates in 2023-2025 data

**Query**:
```sql
SELECT
    symbol,
    toDate(FROM_UNIXTIME(timestamp_ms / 1000)) as date,
    COUNT(*) as tick_count
FROM historical_ticks
WHERE timestamp_ms >= 1672531200000  -- 2023-01-01
GROUP BY symbol, date
HAVING tick_count < 10000  -- Suspiciously low
ORDER BY symbol, date;
```

**If gaps found**: Re-run downloader for those specific dates
```

#### **Documentation References**
- Architecture: `SERVICE_ARCHITECTURE_AND_FLOW.md` line 322-338
- Tables: `table_database_input.md` (ClickHouse.historical_ticks)

---

### **Service 4: external-data-collector**

**Folder**: `00-data-ingestion/external-data-collector`
**Status**: ✅ Active
**Priority**: P1 (ML Features)

#### **Purpose**
Collect **external data** untuk ML feature enrichment (economic calendar, FRED indicators, commodity prices).

#### **Input Sources**
1. **Economic Calendar API** (news events)
   - High-impact events (NFP, FOMC, CPI, etc)
2. **FRED API** (Federal Reserve Economic Data)
   - GDP, unemployment, CPI, interest rates
3. **Yahoo Finance** (commodities)
   - Gold (GC=F), Oil (CL=F)

#### **Output Targets**
- **ClickHouse.external_economic_calendar**
- **ClickHouse.external_fred_indicators**
- **ClickHouse.external_commodity_prices**

#### **Requirements**

**Infrastructure**:
- ✅ ClickHouse (suho-clickhouse)
- ✅ NATS cluster

**API Keys**:
```env
ECONOMIC_CALENDAR_API_KEY=<secret>
FRED_API_KEY=<secret>
# Yahoo Finance: No key needed (public)
```

#### **Common Tasks**

**Task 1: Add New FRED Indicator**
```markdown
## Plan: Add Consumer Sentiment Index (UMCSENT)

**Steps**:
1. Verify indicator exists: https://fred.stlouisfed.org/series/UMCSENT
2. Update config/fred_indicators.yaml:
   ```yaml
   - series_id: "UMCSENT"
     name: "consumer_sentiment"
     frequency: "monthly"
   ```
3. Test API call
4. Backfill historical data
5. Join in feature-engineering-service
```

**Task 2: Monitor Economic Events**
```markdown
## Check: Upcoming high-impact events this week

**Query**:
```sql
SELECT
    event_time,
    currency,
    event_name,
    impact
FROM external_economic_calendar
WHERE event_time >= now()
  AND event_time <= now() + INTERVAL 7 DAY
  AND impact = 'high'
ORDER BY event_time;
```
```

#### **Documentation References**
- Architecture: `SERVICE_ARCHITECTURE_AND_FLOW.md` line 340-368
- Tables: `table_database_input.md` (external_* tables)

---

### **Service 5: central-hub**

**Folder**: `01-core-infrastructure/central-hub`
**Status**: ✅ Active (Orchestration)
**Priority**: P0 (Critical Infrastructure)

#### **Purpose**
**Service coordination, health monitoring, dan message routing** untuk seluruh sistem. Central Hub adalah orchestration layer yang memastikan semua services bekerja correctly.

#### **Input Sources**
- **All Services**: Health check endpoints
- **NATS/Kafka**: Events dari semua services
- **PostgreSQL**: Service registry

#### **Output Targets**
- **PostgreSQL.service_registry** (service status)
- **PostgreSQL.health_metrics** (health aggregation)
- **PostgreSQL.coordination_history** (events log)

#### **Requirements**

**Infrastructure Dependencies** (monitors ALL of these):
- ✅ PostgreSQL (suho-postgresql) - service registry
- ✅ DragonflyDB (suho-dragonflydb) - caching
- ✅ ClickHouse (suho-clickhouse) - analytics
- ✅ NATS cluster (nats-1, nats-2, nats-3) - messaging
- ✅ Kafka (suho-kafka) + Zookeeper - streaming
- ⚠️ ArangoDB (suho-arangodb) - optional
- ⚠️ Weaviate (suho-weaviate) - optional

**Configuration**:
```yaml
# base/config/infrastructure.yaml
databases:
  postgresql: { host: suho-postgresql, port: 5432, critical: true }
  clickhouse: { host: suho-clickhouse, port: 8123, critical: true }
  dragonflydb: { host: suho-dragonflydb, port: 6379, critical: true }

messaging:
  nats-1: { host: nats-1, port: 4222, critical: true }
  nats-2: { host: nats-2, port: 4222, critical: true }
  nats-3: { host: nats-3, port: 4222, critical: true }
  kafka: { host: suho-kafka, port: 9092, critical: true }

service_dependencies:
  polygon-live-collector:
    requires: [nats, kafka, clickhouse]
  tick-aggregator:
    requires: [clickhouse, nats]
  feature-engineering-service:
    requires: [clickhouse]
```

#### **Common Tasks**

**Task 1: Check System Health**
```markdown
## Query: Overall system status

**Via API**:
```bash
curl http://central-hub:8000/health/system
```

**Response**:
```json
{
  "status": "healthy",
  "services": {
    "polygon-live-collector": "healthy",
    "tick-aggregator": "healthy",
    "feature-engineering-service": "degraded"
  },
  "infrastructure": {
    "postgresql": "healthy",
    "clickhouse": "healthy",
    "nats-cluster": "healthy",
    "kafka": "warning"
  }
}
```

**Task 2: Register New Service**
```markdown
## Plan: Register supervised-training-service

**Steps**:
1. Add to infrastructure.yaml:
   ```yaml
   service_dependencies:
     supervised-training-service:
       requires: [clickhouse, nats]
       optional: [postgresql]
   ```

2. Service implements /health endpoint
3. Central Hub auto-discovers via NATS announce
4. Verify registration:
   ```bash
   curl http://central-hub:8000/services/supervised-training-service
   ```
```

**Task 3: Debug Service Dependency Issues**
```markdown
## Investigate: Why is tick-aggregator failing?

**Steps**:
1. Check Central Hub logs:
   ```bash
   docker logs central-hub | grep "tick-aggregator"
   ```

2. Check dependencies:
   ```bash
   curl http://central-hub:8000/services/tick-aggregator/dependencies
   ```

3. Output shows:
   - clickhouse: ❌ DOWN
   - nats: ✅ HEALTHY

4. Root cause: ClickHouse down
5. Action: Restart ClickHouse
```

#### **Monitoring & Alerts**

**Health Aggregation**:
- Aggregates health from all services every 30 seconds
- Stores in PostgreSQL.health_metrics
- Exposes /health/system API

**Alerting**:
- Critical infrastructure down → immediate alert
- Service degraded → warning
- Dependency missing → error

#### **Documentation References**
- Architecture: `SERVICE_ARCHITECTURE_AND_FLOW.md` line 371-393
- Config: `01-core-infrastructure/central-hub/base/config/infrastructure.yaml`

---

### **Service 6: tick-aggregator**

**Folder**: `02-data-processing/tick-aggregator`
**Status**: ✅ Active
**Priority**: P0 (Critical Pipeline)

#### **Purpose**
Aggregate raw tick data menjadi **OHLCV candles** untuk multiple timeframes (5m, 15m, 30m, 1h, 4h, 1d, 1w).

#### **Input Sources**
- **TimescaleDB.live_ticks** (real-time aggregation)
- **ClickHouse.historical_ticks** (batch aggregation)

#### **Output Targets**
- **ClickHouse.live_aggregates** (7-day retention)
  - Real-time candles dari live ticks
- **ClickHouse.historical_aggregates** (unlimited retention)
  - Historical candles untuk training

#### **Requirements**

**Infrastructure**:
- ✅ TimescaleDB (suho-postgresql) - read ticks
- ✅ ClickHouse (suho-clickhouse) - write candles
- ✅ NATS cluster - candle completion events

**Configuration**:
```yaml
# config/aggregator.yaml
timeframes:
  - "5m"   # 5-minute bars
  - "15m"  # 15-minute bars
  - "30m"
  - "1h"
  - "4h"
  - "1d"
  - "1w"

realtime:
  window_seconds: 300  # 5 minutes
  flush_on_window_end: true

batch:
  chunk_size: 10000  # Process 10k ticks at a time
  parallel_workers: 4
```

#### **Common Tasks**

**Task 1: Add New Timeframe**
```markdown
## Plan: Add 2-hour timeframe (2h)

**Steps**:
1. Check if ClickHouse supports '2h':
   - Schema definition: Enum8(...)
   - Current: '5m', '15m', '30m', '1h', '4h', '1d', '1w'
   - **Issue**: '2h' NOT in enum!

2. Add to ClickHouse enum:
   ```sql
   ALTER TABLE aggregates
   MODIFY COLUMN timeframe Enum8(
     '5m'=1, '15m'=2, '30m'=3, '1h'=4,
     '2h'=5, '4h'=6, '1d'=7, '1w'=8
   );
   ```

3. Update aggregator config:
   ```yaml
   timeframes:
     - "2h"
   ```

4. Restart service
5. Backfill historical 2h candles
```

**Task 2: Backfill Historical Candles**
```markdown
## Plan: Backfill EUR/USD 1h candles (2023-2025)

**Query** (check current state):
```sql
SELECT
    toDate(time) as date,
    COUNT(*) as bar_count
FROM historical_aggregates
WHERE symbol = 'C:EURUSD'
  AND timeframe = '1h'
  AND time >= '2023-01-01'
GROUP BY date
ORDER BY date;
```

**If gaps found**:
```bash
docker-compose exec tick-aggregator python src/backfill.py \
  --symbol "C:EURUSD" \
  --timeframe "1h" \
  --start "2023-01-01" \
  --end "2025-01-01"
```

**Performance**: 10,000+ candles/second
```

**Task 3: Fix Aggregation Logic Bug**
```markdown
## Bug: OHLC values incorrect

**Symptoms**:
- close > high (impossible!)
- low > open (impossible!)

**Investigation**:
1. Check tick order (must be sorted by timestamp)
2. Check aggregation window boundaries
3. Check NULL handling

**Common causes**:
- Ticks not sorted before aggregation
- Window boundaries off-by-one
- Mixed timezones (UTC vs local)
```

#### **Documentation References**
- Architecture: `SERVICE_ARCHITECTURE_AND_FLOW.md` line 396-418
- Tables: `table_database_input.md` (aggregates table)

---

### **Service 7: feature-engineering-service**

**Folder**: `02-data-processing/feature-engineering-service`
**Status**: ✅ Active
**Priority**: P0 (ML Pipeline)

#### **Purpose**
Calculate **110 ML features** dari candles + external data untuk training dan inference.

⚠️ **CRITICAL DESIGN**: ml_features table stores ONLY **derived features** (NOT raw OHLC). ML training/inference JOINS aggregates + ml_features.

#### **Input Sources**
- **ClickHouse.aggregates** (OHLCV candles)
- **ClickHouse.external_economic_calendar**
- **ClickHouse.external_fred_indicators**
- **ClickHouse.external_commodity_prices**

#### **Output Targets**
- **ClickHouse.ml_features** (110 derived features)
  - **Does NOT include**: open, high, low, close, volume
  - **Only includes**: RSI, MACD, lagged, rolling, multi-TF, etc

#### **Requirements**

**Infrastructure**:
- ✅ ClickHouse (suho-clickhouse)
- ⚠️ NATS (optional for real-time triggers)

**Tech Stack**:
- Python 3.11+
- Pandas, NumPy (vectorized operations)
- TA-Lib (technical indicators)
- ClickHouse driver

**Configuration**:
```yaml
# config/features.yaml
features:
  phase1_mvp: 97  # Must-have
  phase2_enhanced: 8  # Should-have
  phase3_advanced: 5  # Nice-to-have

technical_indicators:
  rsi_period: 14
  macd_fast: 12
  macd_slow: 26
  macd_signal: 9
  bollinger_period: 20
  stochastic_k: 14
  stochastic_d: 3

lookback:
  lagged_features: [1, 2, 3, 5, 10]
  rolling_windows: [10, 20, 50]
```

#### **Feature Breakdown** (110 Total)

**Primary Keys** (5):
- time, symbol, timeframe, feature_version, created_at

**Market Sessions** (5):
- active_sessions, active_count, is_overlap, liquidity_level, is_london_newyork_overlap

**Calendar** (10):
- day_of_week, day_name, is_monday, is_friday, is_weekend, week_of_month, week_of_year, is_month_start, is_month_end, day_of_month

**Time** (6):
- hour_utc, minute, quarter_hour, is_market_open, is_london_open, is_ny_open

**Technical Indicators** (14):
- rsi_14, macd, macd_signal, macd_histogram, bb_upper, bb_middle, bb_lower, stoch_k, stoch_d, sma_50, sma_200, ema_12, cci, mfi

**Fibonacci** (7):
- fib_0, fib_236, fib_382, fib_50, fib_618, fib_786, fib_100

**External Data** (12):
- upcoming_event_minutes, upcoming_event_impact, recent_event_minutes, gdp_latest, unemployment_latest, cpi_latest, interest_rate_latest, gold_price, oil_price, gold_change_pct, oil_change_pct

**Lagged Features** (15):
- close_lag_1-10, rsi_lag_1-2, macd_lag_1, return_lag_1-3, volume_lag_1-2, spread_lag_1-2

**Rolling Statistics** (8):
- price_rolling_mean_10/20/50, price_rolling_std_10/20, price_rolling_max/min_20, dist_from_rolling_mean_20

**Multi-Timeframe** (10):
- htf_trend_direction, htf_rsi, htf_macd, htf_sma_50, ltf_volatility, ltf_volume, is_all_tf_aligned, tf_alignment_score, htf_support_level, htf_resistance_level

**Target Variables** (5) - Historical Only:
- target_return_5min, target_return_15min, target_return_1h, target_direction, target_is_profitable

**Phase 2 - Momentum** (5):
- roc_5, roc_10, price_acceleration, adx, adx_trend

**Phase 2 - Quality** (3):
- quality_score, missing_feature_count, calculation_duration_ms

**Phase 3 - Interactions** (5):
- rsi_volume_interaction, macd_session_interaction, price_deviation_volume, trend_strength_momentum, volatility_spread_ratio

#### **Common Tasks**

**Task 1: Add New Technical Indicator (ADX)**
```markdown
## Plan: Add Average Directional Index (ADX)

**Current State**:
- ml_features table: 110 features ✅
- TA-Lib integrated ✅
- Phase 2 momentum category exists ✅

**Implementation**:
1. Update schema:
   ```sql
   ALTER TABLE ml_features ADD COLUMN
       adx Nullable(Float64),
       adx_trend Enum8('weak'=1, 'moderate'=2, 'strong'=3, 'very_strong'=4);
   ```

2. Add calculation (src/technical_indicators.py):
   ```python
   def calculate_adx(high, low, close, period=14):
       adx = talib.ADX(high, low, close, timeperiod=period)
       adx_trend = classify_adx_trend(adx)  # 0-25=weak, 25-50=moderate, etc
       return adx, adx_trend
   ```

3. Test with sample data (1000 candles)
4. Backfill historical (2023-2025)
5. Enable for live pipeline

**Success Criteria**:
- ADX values 0-100
- NULL for first 14 candles
- adx_trend classification correct
- No performance degradation (< 5s per candle)

**Estimated Time**: 2-3 days
```

**Task 2: Fix Missing Features Issue**
```markdown
## Bug: Many features NULL for recent data

**Symptoms**:
- rsi_14: NULL
- macd: NULL
- lagged features: NULL

**Investigation**:
1. Check lookback windows:
   - RSI needs 14 candles minimum
   - MACD needs 26 candles minimum
   - Lagged features need N candles

2. Query for data availability:
   ```sql
   SELECT
       symbol,
       timeframe,
       COUNT(*) as candle_count
   FROM aggregates
   WHERE time >= now() - INTERVAL 1 DAY
   GROUP BY symbol, timeframe;
   ```

3. **Root cause**: Insufficient historical data

**Fix**:
- Backfill more historical candles
- OR: Accept NULL for first N candles (expected behavior)
```

**Task 3: Add Multi-Timeframe Features**
```markdown
## Plan: Implement higher timeframe context

**Concept**:
- Current: 5m timeframe
- Higher TF: 15m timeframe
- Get trend, RSI, support/resistance from 15m

**Implementation**:
1. Query higher TF data:
   ```sql
   SELECT
       time,
       calculate_trend(close, sma_50) as trend,
       rsi_14,
       find_support_resistance(low, high)
   FROM aggregates
   WHERE symbol = %(symbol)s
     AND timeframe = '15m'  -- Higher TF
     AND time = %(current_time)s
   ```

2. Join to ml_features:
   - htf_trend_direction
   - htf_rsi
   - htf_support_level
   - htf_resistance_level

**Benefit**: Avoid trading against higher TF trend
```

**Task 4: Verify NO Data Duplication**
```markdown
## Check: Is ml_features duplicating OHLC?

**Query**:
```sql
DESCRIBE ml_features;
```

**Expected**: NO columns named 'open', 'high', 'low', 'close', 'volume'
**If found**: ❌ WRONG DESIGN! Remove those columns.

**Correct Usage**:
```sql
-- ML Training Query
SELECT
    a.time,
    a.symbol,
    a.timeframe,
    a.open, a.high, a.low, a.close,  -- From aggregates
    a.tick_count, a.avg_spread,       -- From aggregates
    f.*                                -- From ml_features (110 features)
FROM aggregates a
LEFT JOIN ml_features f
    ON a.time = f.time
    AND a.symbol = f.symbol
    AND a.timeframe = f.timeframe
WHERE a.time >= '2023-01-01';
```
```

#### **Documentation References**
- Architecture: `SERVICE_ARCHITECTURE_AND_FLOW.md` line 420-455
- Tables: `table_database_process.md` (complete 110-feature spec)
- Design Decision: ml_features NO raw data (table_database_process.md line 38-76)

---

## 📊 PHASE 2: TRAINING SERVICES (⚠️ To Implement)

---

### **Service 8: supervised-training-service**

**Folder**: `03-ml-training/supervised-training-service`
**Status**: ⚠️ Placeholder (To Implement)
**Priority**: P1

#### **Purpose**
Train **supervised ML models** (classification & regression) menggunakan historical data dengan targets.

#### **Input Sources**
- **ClickHouse.ml_features** (historical + targets)
  - Requires: target_return_5min, target_return_1h, target_direction
  - Date range: 2023-01-01 to 2025-09-01 (training period)
- **ClickHouse.aggregates** (for JOIN - raw OHLC)

#### **Output Targets**
- **ClickHouse.training_runs** (experiment tracking)
- **ClickHouse.model_checkpoints** (saved models)
- **ClickHouse.training_metrics** (per-epoch metrics)
- **ClickHouse.hyperparameters_log** (tuning history)

#### **Requirements**

**Prerequisites**:
- ✅ Phase 1 complete (ml_features has data)
- ✅ Targets calculated (target_* columns)
- ⚠️ Training tables created (to implement)

**Infrastructure**:
- ✅ ClickHouse (query training data)
- ⚠️ GPU (optional for neural networks)

**Tech Stack**:
- Python 3.11+
- Scikit-learn (Random Forest, baseline)
- XGBoost (gradient boosting)
- LightGBM (fast gradient boosting)
- CatBoost (categorical features)
- Optuna (hyperparameter tuning)
- MLflow (optional experiment tracking)

#### **Common Tasks**

**Task 1: Initial Setup**
```markdown
## Plan: Setup supervised-training-service from scratch

**Week 1: Tables & Data**
- [ ] Create training tables:
  ```sql
  CREATE TABLE training_runs (...);
  CREATE TABLE model_checkpoints (...);
  CREATE TABLE training_metrics (...);
  CREATE TABLE hyperparameters_log (...);
  ```

- [ ] Test data query:
  ```sql
  SELECT
      a.*, f.*
  FROM aggregates a
  LEFT JOIN ml_features f USING (time, symbol, timeframe)
  WHERE a.time BETWEEN '2023-01-01' AND '2025-09-01'
    AND f.target_return_1h IS NOT NULL
  LIMIT 1000;  -- Test query
  ```

**Week 2: Basic Training**
- [ ] Implement data loader (query → pandas DataFrame)
- [ ] Train/val/test split (time-series aware)
- [ ] Basic XGBoost model
- [ ] Model evaluation (accuracy, F1, AUC)

**Week 3: Multiple Models**
- [ ] Add LightGBM
- [ ] Add CatBoost
- [ ] Model comparison framework

**Week 4: Hyperparameter Tuning**
- [ ] Integrate Optuna
- [ ] Define search space
- [ ] Run tuning experiments (100 trials)
- [ ] Save best model

**Success Criteria**:
- [ ] Model achieves >60% accuracy on test set
- [ ] Hyperparameter tuning improves performance
- [ ] Model saved and loadable
```

**Task 2: Feature Selection**
```markdown
## Plan: Select best features from 110 candidates

**Method 1: Feature Importance (XGBoost)**
```python
model = xgb.XGBClassifier()
model.fit(X_train, y_train)
importance = model.feature_importances_
top_50 = select_top_features(importance, n=50)
```

**Method 2: Recursive Feature Elimination**
```python
from sklearn.feature_selection import RFE
rfe = RFE(estimator=model, n_features_to_select=50)
rfe.fit(X_train, y_train)
selected_features = rfe.support_
```

**Result**: Reduced feature set (50-70 features) for faster training
```

**Task 3: Cross-Validation**
```markdown
## Plan: Implement time-series cross-validation

**Issue**: Standard K-Fold violates time-series assumption

**Solution**: TimeSeriesSplit (walk-forward)
```python
from sklearn.model_selection import TimeSeriesSplit

tscv = TimeSeriesSplit(n_splits=5)
for train_idx, val_idx in tscv.split(X):
    X_train, X_val = X[train_idx], X[val_idx]
    # Train model on X_train
    # Validate on X_val (future data)
```

**Benefit**: Prevents look-ahead bias
```

#### **Documentation References**
- Architecture: `SERVICE_ARCHITECTURE_AND_FLOW.md` line 458-495
- Tables: `table_database_training.md`

---

### **Service 9: finrl-training-service**

**Folder**: `03-ml-training/finrl-training-service`
**Status**: ⚠️ To Build
**Priority**: P1

#### **Purpose**
Train **Reinforcement Learning agents** dengan FinRL framework untuk trading decisions. NO targets needed (learns from rewards).

#### **Input Sources**
- **ClickHouse.ml_features** (historical, NO targets needed)
- **ClickHouse.aggregates** (for environment rewards)

#### **Output Targets**
- **ClickHouse.agent_training_runs**
- **ClickHouse.agent_checkpoints** (saved agents)
- **ClickHouse.reward_history** (episode rewards)
- **ClickHouse.rl_hyperparameters**

#### **Requirements**

**Prerequisites**:
- ✅ ml_features has data
- ⚠️ RL training tables created

**Tech Stack**:
- Python 3.11+
- FinRL framework
- Stable-Baselines3 (RL algorithms)
- PyTorch (neural networks)
- Gym (environment interface)

**RL Algorithms**:
- PPO (Proximal Policy Optimization) - recommended
- A2C (Advantage Actor-Critic)
- DDPG (Deep Deterministic Policy Gradient)
- SAC (Soft Actor-Critic)
- TD3 (Twin Delayed DDPG)

#### **Common Tasks**

**Task 1: Environment Setup**
```markdown
## Plan: Create FinRL trading environment

**State Space**: 110 features dari ml_features
**Action Space**:
- buy/sell/hold (discrete)
- OR: continuous position sizing (-1 to +1)

**Reward Function**:
```python
def calculate_reward(action, current_price, next_price, position):
    pnl = (next_price - current_price) * position
    sharpe_penalty = calculate_sharpe_ratio_penalty()
    drawdown_penalty = calculate_drawdown_penalty()

    reward = pnl - sharpe_penalty - drawdown_penalty
    return reward
```

**Implementation**:
```python
from finrl.env import StockTradingEnv

env = StockTradingEnv(
    df=training_data,  # From ml_features
    state_space=110,   # 110 features
    action_space=3,    # Buy/Sell/Hold
    reward_scaling=1.0
)
```
```

**Task 2: Agent Training**
```markdown
## Plan: Train PPO agent

**Hyperparameters**:
```python
from stable_baselines3 import PPO

model = PPO(
    "MlpPolicy",
    env,
    learning_rate=3e-4,
    n_steps=2048,
    batch_size=64,
    gamma=0.99,  # Discount factor
    clip_range=0.2,
    verbose=1
)

# Train for 1M timesteps
model.learn(total_timesteps=1_000_000)

# Save agent
model.save("ppo_eurusd_1h")
```

**Training Time**: 2-4 hours on GPU
```

**Task 3: Continuous Learning**
```markdown
## Plan: Update agent with live trading results

**Workflow**:
1. Agent makes predictions → trading_signals
2. Signals executed → positions
3. Calculate actual rewards from positions
4. Feed back to agent → improve policy

**Implementation**:
```python
# After each trading day
real_rewards = query_today_positions_pnl()
agent.update_from_experience(
    states=today_states,
    actions=today_actions,
    rewards=real_rewards
)
agent.save_checkpoint()
```

**Benefit**: Agent learns from real market, not just backtest
```

#### **Documentation References**
- Architecture: `SERVICE_ARCHITECTURE_AND_FLOW.md` line 498-540
- Tables: `table_database_training.md` (RL tables)

---

## 📈 PHASE 3: TRADING SERVICES (⚠️ Future)

---

### **Service 10: inference-service**

**Folder**: `04-trading-execution/inference-service`
**Status**: ⚠️ Placeholder
**Priority**: P2

#### **Purpose**
Real-time prediction menggunakan trained models/agents untuk generate trading signals.

#### **Input Sources**
- **ClickHouse.ml_features** (live, latest candle)
- **Trained models** (dari model_checkpoints)
- **Trained agents** (dari agent_checkpoints)

#### **Output Targets**
- **ClickHouse.trading_signals**
- **ClickHouse.model_predictions** (raw outputs)

#### **Requirements**

**Prerequisites**:
- ✅ Phase 2 complete (models trained)
- ✅ model_checkpoints has models
- ✅ ml_features has live data

**Tech Stack**:
- Python 3.11+
- FastAPI (API server)
- Model serving (ONNX/TorchServe optional)

#### **Common Tasks**

**Task 1: Load Trained Model**
```markdown
## Plan: Deploy best XGBoost model

**Steps**:
1. Query best model:
   ```sql
   SELECT checkpoint_id, model_binary
   FROM model_checkpoints
   WHERE run_id = (
       SELECT run_id FROM training_runs
       WHERE model_type = 'xgboost'
       ORDER BY final_test_accuracy DESC
       LIMIT 1
   );
   ```

2. Load model:
   ```python
   import pickle
   import base64

   model_binary = query_result['model_binary']
   model_bytes = base64.b64decode(model_binary)
   model = pickle.loads(model_bytes)
   ```

3. Cache in memory for fast inference
```

**Task 2: Real-Time Inference**
```markdown
## Plan: Generate signal for latest candle

**Query latest features**:
```sql
SELECT a.*, f.*
FROM aggregates a
LEFT JOIN ml_features f USING (time, symbol, timeframe)
WHERE a.symbol = 'C:EURUSD'
  AND a.timeframe = '1h'
ORDER BY a.time DESC
LIMIT 1;
```

**Generate prediction**:
```python
features = query_latest_features()
prediction = model.predict_proba(features)  # [prob_buy, prob_sell, prob_hold]

if prediction[0] > 0.7:  # 70% confidence
    create_trading_signal(
        symbol='C:EURUSD',
        signal_type='buy',
        confidence=prediction[0],
        entry_price=current_price
    )
```
```

#### **Documentation References**
- Architecture: `SERVICE_ARCHITECTURE_AND_FLOW.md` line 544-576
- Tables: `table_database_trading.md` (trading_signals)

---

### **Service 11: execution-service**

**Folder**: `04-trading-execution/execution-service`
**Status**: ⚠️ Placeholder
**Priority**: P2

#### **Purpose**
Execute trading orders ke broker (MT5) dan track order lifecycle.

#### **Input Sources**
- **ClickHouse.trading_signals** (approved signals)

#### **Output Targets**
- **ClickHouse.orders**
- **ClickHouse.executions**
- **ClickHouse.positions**

#### **Requirements**

**Prerequisites**:
- ✅ trading_signals table has data
- ✅ MT5 connector working
- ✅ Risk management approved signal

**Tech Stack**:
- Python 3.11+
- MT5 API
- asyncio (async order submission)

#### **Common Tasks**

**Task 1: Submit Market Order**
```markdown
## Plan: Execute buy signal for EUR/USD

**Steps**:
1. Get approved signal:
   ```sql
   SELECT * FROM trading_signals
   WHERE signal_id = %(signal_id)s
     AND risk_approval_status = 'approved'
     AND execution_status = 'pending';
   ```

2. Create order:
   ```python
   order = {
       'symbol': 'EURUSD',
       'order_type': 'market',
       'side': 'buy',
       'quantity': 0.1,  # From risk management
       'stop_loss': signal['stop_loss'],
       'take_profit': signal['take_profit']
   }

   broker_order_id = mt5_connector.submit_order(order)
   ```

3. Track execution:
   ```sql
   INSERT INTO orders (order_id, signal_id, broker_order_id, ...)
   VALUES (...);
   ```
```

**Task 2: Handle Partial Fills**
```markdown
## Plan: Track order fills

**Scenario**: Order for 1.0 lot filled in 2 parts (0.6 + 0.4)

**Track executions**:
```sql
INSERT INTO executions (order_id, fill_price, fill_quantity, ...)
VALUES
    (order_id, 1.0850, 0.6, ...),
    (order_id, 1.0852, 0.4, ...);
```

**Update order**:
```sql
UPDATE orders
SET order_status = 'filled',
    filled_quantity = 1.0,
    average_fill_price = 1.0851  -- Weighted average
WHERE order_id = %(order_id)s;
```
```

#### **Documentation References**
- Architecture: `SERVICE_ARCHITECTURE_AND_FLOW.md` line 579-617
- Tables: `table_database_trading.md` (orders, executions, positions)

---

### **Service 12: risk-management**

**Folder**: `04-trading-execution/risk-management`
**Status**: ⚠️ Placeholder
**Priority**: P2

#### **Purpose**
Risk checks, position sizing, portfolio limits sebelum order execution.

#### **Input Sources**
- **ClickHouse.trading_signals** (pending approval)
- **ClickHouse.positions** (current positions)

#### **Output Targets**
- **Approved/rejected signals** (update trading_signals)
- **ClickHouse.risk_events** (violations log)

#### **Requirements**

**Tech Stack**:
- Python 3.11+
- Risk calculation libraries

#### **Common Tasks**

**Task 1: Position Sizing**
```markdown
## Plan: Calculate position size using Kelly Criterion

**Formula**:
```
f = (p * b - q) / b
where:
  p = win probability
  f = fraction of capital to risk
  b = win/loss ratio
  q = 1 - p (loss probability)
```

**Implementation**:
```python
def calculate_position_size(signal, account_balance):
    win_prob = signal['confidence_score']  # From model
    win_loss_ratio = abs(signal['take_profit'] - signal['entry_price']) / \
                     abs(signal['entry_price'] - signal['stop_loss'])

    kelly_fraction = (win_prob * win_loss_ratio - (1 - win_prob)) / win_loss_ratio
    kelly_fraction = min(kelly_fraction, 0.02)  # Max 2% per trade

    position_size = account_balance * kelly_fraction / signal['entry_price']
    return position_size
```
```

**Task 2: Portfolio Limits**
```markdown
## Plan: Enforce portfolio risk limits

**Rules**:
1. Max 10 open positions
2. Max 30% total exposure
3. Max 5% daily loss
4. Max 20% drawdown

**Check**:
```python
def check_portfolio_limits(new_signal):
    current_positions = query_open_positions()

    if len(current_positions) >= 10:
        reject_signal(new_signal, reason="Max positions reached")
        return False

    total_exposure = sum(p.value for p in current_positions) + new_signal.size
    if total_exposure / account_balance > 0.30:
        reject_signal(new_signal, reason="Max exposure exceeded")
        return False

    today_pnl = query_today_pnl()
    if today_pnl < -0.05 * account_balance:
        reject_signal(new_signal, reason="Daily loss limit")
        return False

    return True  # Approved
```
```

#### **Documentation References**
- Architecture: `SERVICE_ARCHITECTURE_AND_FLOW.md` line 620-657
- Tables: `table_database_trading.md` (risk_events)

---

### **Service 13: performance-monitoring**

**Folder**: `04-trading-execution/performance-monitoring`
**Status**: ⚠️ To Build
**Priority**: P2

#### **Purpose**
Track trading performance, calculate metrics (Sharpe, drawdown, win rate), generate alerts.

#### **Input Sources**
- **ClickHouse.positions** (trade history)
- **ClickHouse.orders**
- **ClickHouse.executions**

#### **Output Targets**
- **ClickHouse.portfolio_value** (equity curve)
- **ClickHouse.performance_metrics**
- **ClickHouse.trade_analysis**

#### **Requirements**

**Tech Stack**:
- Python 3.11+
- Pandas (data analysis)
- Matplotlib/Plotly (visualization)

#### **Common Tasks**

**Task 1: Calculate Sharpe Ratio**
```markdown
## Plan: Daily Sharpe ratio calculation

**Formula**:
```
Sharpe = (Mean Return - Risk-Free Rate) / Std Dev of Returns
```

**Implementation**:
```python
def calculate_sharpe_ratio(returns, risk_free_rate=0.02):
    excess_returns = returns - risk_free_rate / 252  # Daily
    sharpe = excess_returns.mean() / excess_returns.std()
    sharpe_annualized = sharpe * np.sqrt(252)
    return sharpe_annualized
```

**Query returns**:
```sql
SELECT
    toDate(closed_at) as date,
    SUM(realized_pnl) as daily_pnl
FROM positions
WHERE position_status = 'closed'
GROUP BY date
ORDER BY date;
```
```

**Task 2: Track Max Drawdown**
```markdown
## Plan: Real-time drawdown monitoring

**Formula**:
```
Drawdown = (Peak Value - Current Value) / Peak Value
Max Drawdown = Largest drawdown in period
```

**Implementation**:
```python
def calculate_drawdown(equity_curve):
    peak = equity_curve.cummax()
    drawdown = (equity_curve - peak) / peak
    max_drawdown = drawdown.min()
    return drawdown, max_drawdown
```

**Alert**:
```python
if max_drawdown < -0.20:  # 20% drawdown
    send_alert("CRITICAL: 20% drawdown reached!")
    # Consider stopping trading
```
```

#### **Documentation References**
- Architecture: `SERVICE_ARCHITECTURE_AND_FLOW.md` line 659-699
- Tables: `table_database_trading.md` (performance_metrics)

---

## 🔗 PHASE 4: SUPPORTING SERVICES (⚠️ Future)

---

### **Service 14: mt5-connector**

**Folder**: `05-broker-integration/mt5-connector`
**Status**: ⚠️ Placeholder
**Priority**: P3

#### **Purpose**
Integration dengan MetaTrader 5 broker untuk order execution.

#### **Requirements**

**Tech Stack**:
- Python MetaTrader5 library
- MT5 account credentials

#### **Documentation References**
- Architecture: `SERVICE_ARCHITECTURE_AND_FLOW.md` line 704-724

---

### **Service 15: backtesting-service**

**Folder**: `06-backtesting/backtesting-service`
**Status**: ⚠️ Placeholder
**Priority**: P2

#### **Purpose**
Historical simulation untuk model/strategy validation sebelum live trading.

#### **Tech Stack**:
- Python
- Backtrader/Zipline/VectorBT

#### **Documentation References**
- Architecture: `SERVICE_ARCHITECTURE_AND_FLOW.md` line 727-750

---

### **Service 16: analytics-service**

**Folder**: `07-business-platform/analytics-service`
**Status**: ⚠️ Placeholder
**Priority**: P3

#### **Purpose**
Business analytics dashboards & reporting.

#### **Documentation References**
- Architecture: `SERVICE_ARCHITECTURE_AND_FLOW.md` line 752-768

---

### **Service 17: notification-hub**

**Folder**: `07-business-platform/notification-hub`
**Status**: ⚠️ Placeholder
**Priority**: P3

#### **Purpose**
Alert & notification system (email, Telegram, SMS).

#### **Documentation References**
- Architecture: `SERVICE_ARCHITECTURE_AND_FLOW.md` line 771-787

---

## 🔀 Service Flow & Dependencies

### **⚠️ CRITICAL: Service Execution Order**

**Golden Rule**: **NEVER** skip dependencies or jump phases!

```
Phase 1 MUST complete → Phase 2 MUST complete → Phase 3 can start
     ↓                      ↓                         ↓
   Services 1-7         Services 8-9            Services 10-13
```

---

### **🔗 Complete Service Dependency Chain**

```
┌─────────────────────────────────────────────────────────────────┐
│                  DATA FLOW PIPELINE                             │
│                  (Follow This Sequence!)                         │
└─────────────────────────────────────────────────────────────────┘

External APIs (Polygon, Dukascopy, Economic Calendar)
    ↓
┌─────────────────────────────────────────────────────────────────┐
│ Service 1: polygon-live-collector                               │
│ Service 2: polygon-historical-downloader (gap filling)          │
│ Service 3: dukascopy-historical-downloader                      │
│ Service 4: external-data-collector                              │
└─────────────────┬───────────────────────────────────────────────┘
                  ↓
          ✅ CHECKPOINT 1: Raw data collected
                  ↓
┌─────────────────────────────────────────────────────────────────┐
│ Service 6: tick-aggregator                                      │
│   Input:  TimescaleDB.live_ticks                                │
│           ClickHouse.historical_ticks                           │
│   Output: ClickHouse.aggregates (OHLCV candles)                │
└─────────────────┬───────────────────────────────────────────────┘
                  ↓
          ✅ CHECKPOINT 2: Candles ready
                  ↓
┌─────────────────────────────────────────────────────────────────┐
│ Service 7: feature-engineering-service                          │
│   Input:  ClickHouse.aggregates                                 │
│           ClickHouse.external_* tables                          │
│   Output: ClickHouse.ml_features (110 derived features)        │
└─────────────────┬───────────────────────────────────────────────┘
                  ↓
    ✅ CHECKPOINT 3: Phase 1 Complete (Features ready)
                  ↓
    ┌─────────────┴─────────────┐
    │                           │
    ▼                           ▼
┌────────────────────┐  ┌────────────────────┐
│ Service 8:         │  │ Service 9:         │
│ supervised-        │  │ finrl-training-    │
│ training-service   │  │ service            │
│                    │  │                    │
│ Input: ml_features │  │ Input: ml_features │
│ Output: models     │  │ Output: RL agents  │
└─────────┬──────────┘  └─────────┬──────────┘
          │                       │
          └───────────┬───────────┘
                      ↓
        ✅ CHECKPOINT 4: Phase 2 Complete (Models trained)
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│ Service 10: inference-service                                   │
│   Input:  ClickHouse.ml_features (live)                         │
│           model_checkpoints / agent_checkpoints                 │
│   Output: ClickHouse.trading_signals                            │
└─────────────────┬───────────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────────┐
│ Service 12: risk-management                                     │
│   Input:  trading_signals (pending)                             │
│           positions (current)                                   │
│   Output: trading_signals (approved/rejected)                   │
└─────────────────┬───────────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────────┐
│ Service 11: execution-service                                   │
│   Input:  trading_signals (approved)                            │
│   Output: orders, executions, positions                         │
└─────────────────┬───────────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────────┐
│ Service 14: mt5-connector                                       │
│   Input:  orders                                                │
│   Output: fill confirmations                                    │
└─────────────────┬───────────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────────┐
│ Service 13: performance-monitoring                              │
│   Input:  positions, orders, executions                         │
│   Output: portfolio_value, performance_metrics                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### **🚨 Dependency Validation Rules**

**Rule 1: Phase Sequence**
```
❌ WRONG: User asks "implement inference-service"
          → Phase 2 not complete!

✅ RIGHT: Check Phase 2 status first
          → If training tables empty → Implement Phase 2 first
          → If models exist → Safe to implement inference
```

**Rule 2: Table Existence**
```
❌ WRONG: Start feature-engineering without aggregates table

✅ RIGHT: Verify aggregates table has data
          → Query: SELECT COUNT(*) FROM aggregates
          → If count = 0 → Run tick-aggregator first
          → If count > 0 → Safe to proceed
```

**Rule 3: Service Health**
```
❌ WRONG: Implement Service B while Service A is failing

✅ RIGHT: Check Service A health via central-hub
          → If Service A down → Fix Service A first
          → If Service A healthy → Safe to implement Service B
```

---

### **🎯 User Request → Service Mapping**

**Use this decision tree untuk setiap user request:**

#### **Request Type: Data Collection**
```
User: "Add new trading pair"
  → Service 1: polygon-live-collector (live data)
  → Service 3: dukascopy-historical-downloader (historical)
  → Service 6: tick-aggregator (aggregate to candles)
  → Service 7: feature-engineering-service (calculate features)
```

#### **Request Type: Add Indicator/Feature**
```
User: "Add RSI indicator"
  → Service 7: feature-engineering-service ONLY
  ✅ Check: aggregates table has data
  ✅ Check: feature-engineering-service is running
```

#### **Request Type: Training**
```
User: "Train ML model"
  ✅ Check: Phase 1 complete (ml_features populated)
  ✅ Check: targets calculated
  → Service 8: supervised-training-service
  OR
  → Service 9: finrl-training-service
```

#### **Request Type: Trading**
```
User: "Deploy trading system"
  ✅ Check: Phase 2 complete (models exist)
  ✅ Check: model_checkpoints has data
  → Service 10: inference-service (first!)
  → Service 12: risk-management (second!)
  → Service 11: execution-service (third!)
  → Service 13: performance-monitoring (fourth!)
```

#### **Request Type: Fix Bug**
```
User: "Service X is failing"
  1. Check central-hub health status
  2. Identify which service is affected
  3. Check that service's dependencies
  4. Fix dependencies first (bottom-up)
  5. Then fix service itself
```

---

### **🔄 Data Flow by Table**

**Critical Tables & Their Flow**:

1. **live_ticks** (TimescaleDB)
   ```
   Source: polygon-live-collector (Service 1)
   Consumer: tick-aggregator (Service 6)
   Retention: 3 days
   ```

2. **historical_ticks** (ClickHouse)
   ```
   Source: dukascopy-historical-downloader (Service 3)
   Consumer: tick-aggregator (Service 6)
   Retention: Unlimited
   ```

3. **live_aggregates** (ClickHouse)
   ```
   Source: tick-aggregator (Service 6)
   Gap-filler: polygon-historical-downloader (Service 2)
   Consumer: feature-engineering-service (Service 7)
   Retention: 7 days
   ```

4. **historical_aggregates** (ClickHouse)
   ```
   Source: tick-aggregator (Service 6)
   Consumer: feature-engineering-service (Service 7)
   Retention: Unlimited
   ```

5. **ml_features** (ClickHouse)
   ```
   Source: feature-engineering-service (Service 7)
   Consumers:
     - supervised-training-service (Service 8)
     - finrl-training-service (Service 9)
     - inference-service (Service 10)
   ```

6. **model_checkpoints** (ClickHouse)
   ```
   Source: supervised-training-service (Service 8)
   Consumer: inference-service (Service 10)
   ```

7. **trading_signals** (ClickHouse)
   ```
   Source: inference-service (Service 10)
   Validator: risk-management (Service 12)
   Executor: execution-service (Service 11)
   ```

---

### **⚠️ Common Mistakes to Avoid**

**Mistake 1: Skipping Checkpoints**
```
❌ BAD: User wants training → Start implementing supervised-training
✅ GOOD: Check ml_features has data → Check targets exist → Then implement
```

**Mistake 2: Circular Dependencies**
```
❌ BAD: Service A reads from Service B, Service B reads from Service A
✅ GOOD: Follow unidirectional flow (Service A → Service B → Service C)
```

**Mistake 3: Missing Infrastructure**
```
❌ BAD: Implement service without checking ClickHouse is running
✅ GOOD: Check central-hub health first → Verify infrastructure → Then implement
```

**Mistake 4: Phase Jumping**
```
❌ BAD: "Let's implement inference-service now" (Phase 2 incomplete)
✅ GOOD: "Phase 2 training not complete. Must train models first before inference."
```

---

### **✅ Pre-Implementation Checklist**

Before implementing ANYTHING, ask these questions:

```markdown
[ ] 1. Which PHASE does this task belong to?
    - Phase 1 (Data): Services 1-7
    - Phase 2 (Training): Services 8-9
    - Phase 3 (Trading): Services 10-13

[ ] 2. Is previous phase COMPLETE?
    - Phase 1 → Check ml_features has data
    - Phase 2 → Check model_checkpoints has models
    - Phase 3 → Check trading_signals working

[ ] 3. Which SERVICE handles this task?
    - Read service Purpose section
    - Verify service status (Active/Placeholder)

[ ] 4. What are INPUT requirements?
    - Check "Input Sources" section
    - Verify tables exist and have data
    - Query: SELECT COUNT(*) FROM <input_table>

[ ] 5. What are INFRASTRUCTURE requirements?
    - Check "Requirements" section
    - Verify via central-hub health check
    - Fix any DOWN infrastructure first

[ ] 6. Are there DEPENDENCY services?
    - Check flow diagram above
    - Verify all upstream services running
    - Bottom-up fix (fix dependencies first)

[ ] 7. Is this the CORRECT sequence?
    - Can't do Service 8 before Service 7
    - Can't do Service 10 before Service 8
    - Can't do Service 11 before Service 10
```

---

## 🎯 How to Use This Guide

### **When Planning ANY Task**

```markdown
**Step 1**: Identify which SERVICE is involved
- Read service title (e.g., "Service 7: feature-engineering-service")
- Check status (Active/Placeholder/To Build)

**Step 2**: Understand service function
- Read "Purpose" section
- Check "Input Sources" (what it reads)
- Check "Output Targets" (what it writes)

**Step 3**: Verify requirements
- Check "Requirements" section
- Verify infrastructure is running
- Verify prerequisites are met

**Step 4**: Find similar task
- Read "Common Tasks" section
- Find example closest to your task
- Adapt example to your specific needs

**Step 5**: Execute
- Follow step-by-step plan from example
- Test incrementally
- Monitor results
```

### **Example Usage**

**User asks**: "Add Bollinger Bands to ml_features"

**Planning Process**:
1. **Identify service**: Feature-engineering-service (Service 7)
2. **Check status**: ✅ Active
3. **Understand purpose**: Calculates 110 ML features
4. **Check Common Tasks**: Find "Task 1: Add New Technical Indicator (ADX)"
5. **Adapt example**:
   - Replace ADX → Bollinger Bands
   - Use TA-Lib BBANDS function
   - Same workflow: schema → code → test → backfill

---

## 📚 Quick Reference

### **By Phase**

**Phase 1 (Active)**: Services 1-7
**Phase 2 (To Implement)**: Services 8-9
**Phase 3 (Future)**: Services 10-13
**Phase 4 (Supporting)**: Services 14-17

### **By Priority**

**P0 (Critical)**: 1, 2, 5, 6, 7
**P1 (High)**: 3, 4, 8, 9
**P2 (Medium)**: 10, 11, 12, 13, 15
**P3 (Low)**: 14, 16, 17

### **By Database**

**TimescaleDB**: 1 (live_ticks)
**ClickHouse**: 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13
**PostgreSQL**: 5 (central-hub registry)

---

## ✅ Validation Checklist

Before planning ANY task:

- [ ] Read relevant service section
- [ ] Verify service status (Active/Placeholder)
- [ ] Check prerequisites (Phase N-1 complete?)
- [ ] Verify infrastructure running
- [ ] Understand input/output tables
- [ ] Find similar task in "Common Tasks"
- [ ] Adapt example to your needs
- [ ] Get user approval before executing

---

**Version History**:
- v2.0.0 (2025-10-18): **Complete redesign** - Service-centric structure (17 services)
- v1.0.0 (2025-10-18): Initial task-centric planning guide
