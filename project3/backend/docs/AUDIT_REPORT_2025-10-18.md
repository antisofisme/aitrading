# 🔍 DATABASE & SERVICES AUDIT REPORT
> **Date**: 2025-10-18
> **Status**: Gap Analysis Complete
> **Severity**: 🔴 HIGH - Major Schema Misalignment

---

## 📊 EXECUTIVE SUMMARY

**Overall Status**: 🔴 **MAJOR GAPS FOUND**

| Component | Current State | Target State | Status |
|-----------|---------------|--------------|--------|
| **TimescaleDB Tables** | 1 table (market_ticks) | 1 table (live_ticks) | 🔴 Schema mismatch |
| **ClickHouse Tables** | 1 table (aggregates) | 6+ tables | 🔴 5 tables missing |
| **Table Schemas** | 14-18 columns | 6-15 columns | 🔴 Incorrect schemas |
| **External Data** | 0 tables | 3 tables | 🔴 Not implemented |

**Impact**: Services are writing incorrect schemas, data incompatible with feature engineering

---

## 🗄️ DATABASE SCHEMA AUDIT

### **1. TimescaleDB (PostgreSQL) - market_ticks**

**Current Schema** (14 columns):
```
✅ time (timestamp with time zone)
❌ tick_id (uuid) - NOT NEEDED
❌ tenant_id (varchar) - NOT NEEDED  
✅ symbol (varchar)
✅ bid (numeric)
✅ ask (numeric)
❌ mid (numeric) - SHOULD NOT BE STORED
❌ spread (numeric) - SHOULD NOT BE STORED
❌ exchange (varchar) - NOT NEEDED
❌ source (varchar) - NOT NEEDED
❌ event_type (varchar) - NOT NEEDED
❌ use_case (varchar) - NOT NEEDED
✅ timestamp_ms (bigint)
✅ ingested_at (timestamp)
```

**Target Schema** (6 columns):
```sql
CREATE TABLE live_ticks
(
    time timestamp with time zone NOT NULL,
    symbol varchar(20) NOT NULL,
    bid numeric(18,5) NOT NULL,
    ask numeric(18,5) NOT NULL,
    timestamp_ms bigint NOT NULL,
    ingested_at timestamp with time zone DEFAULT now()
);
```

**Issues**:
- ❌ Table name: `market_ticks` should be `live_ticks`
- ❌ 8 extra columns that bloat storage
- ❌ `mid` and `spread` should be calculated on-the-fly, not stored
- ❌ Redundant metadata columns (tick_id, tenant_id, exchange, source, etc)

**Migration Required**: 🔴 YES - Drop 8 columns, rename table

---

### **2. ClickHouse - aggregates**

**Current Schema** (18 columns):
```
✅ symbol (String)
❌ timeframe (String) - Should be Enum8
❌ timestamp (DateTime64) - Should be "time"
✅ timestamp_ms (UInt64)
✅ open, high, low, close (Decimal)
❌ volume (UInt64) - Should be "tick_count"
❌ vwap (Decimal) - NOT NEEDED
❌ range_pips (Decimal) - Should be "price_range"
❌ body_pips (Decimal) - NOT NEEDED
❌ start_time (DateTime64) - NOT NEEDED
❌ end_time (DateTime64) - NOT NEEDED
❌ source (String) - NOT NEEDED
❌ event_type (String) - NOT NEEDED
❌ indicators (String) - NOT NEEDED
✅ ingested_at (DateTime64) - Should be "created_at"
```

**MISSING Columns**:
- ❌ avg_spread, max_spread, min_spread (CRITICAL for ML)
- ❌ pct_change (momentum feature)
- ❌ is_complete (quality flag)

**Target Schema** (15 columns):
```sql
CREATE TABLE live_aggregates
(
    time DateTime64(3, 'UTC'),
    symbol String,
    timeframe Enum8('5m'=1, '15m'=2, '30m'=3, '1h'=4, '4h'=5, '1d'=6, '1w'=7),
    open Decimal(18,5),
    high Decimal(18,5),
    low Decimal(18,5),
    close Decimal(18,5),
    tick_count UInt32,  -- NOT "volume"
    avg_spread Decimal(18,5),  -- MISSING
    max_spread Decimal(18,5),  -- MISSING
    min_spread Decimal(18,5),  -- MISSING
    price_range Decimal(18,5),  -- NOT "range_pips"
    pct_change Decimal(10,5),  -- MISSING
    is_complete UInt8,  -- MISSING
    created_at DateTime64(3, 'UTC')
)
ENGINE = MergeTree()
PARTITION BY (toYYYYMM(time), timeframe)
ORDER BY (symbol, timeframe, time);
```

**Issues**:
- ❌ Table name: `aggregates` should be `live_aggregates` + `historical_aggregates`
- ❌ Missing 5 critical columns (spread metrics, pct_change, is_complete)
- ❌ Has 7 unnecessary columns (vwap, body_pips, start_time, etc)
- ❌ timeframe is String, should be Enum8
- ❌ Missing historical_aggregates table (separate from live)

**Migration Required**: 🔴 YES - Major schema restructure

---

### **3. ClickHouse - Missing Tables**

**Tables That Should Exist**:

#### ❌ **historical_ticks** (Dukascopy data)
```sql
CREATE TABLE historical_ticks
(
    time DateTime64(3, 'UTC'),
    symbol String,
    bid Decimal(18,5),
    ask Decimal(18,5),
    timestamp_ms UInt64,
    ingested_at DateTime64(3, 'UTC')
)
ENGINE = MergeTree()
PARTITION BY (toYYYYMM(time), symbol)
ORDER BY (symbol, time);
```
**Status**: 🔴 NOT CREATED

---

#### ❌ **historical_aggregates**
```sql
-- Same schema as live_aggregates, different data source
```
**Status**: 🔴 NOT CREATED

---

#### ❌ **external_economic_calendar**
```sql
CREATE TABLE external_economic_calendar
(
    event_time DateTime64(3, 'UTC'),
    currency String,
    event_name String,
    impact Enum8('low'=1, 'medium'=2, 'high'=3),
    forecast Nullable(String),
    previous Nullable(String),
    actual Nullable(String),
    scraped_at DateTime64(3, 'UTC')
)
ENGINE = MergeTree()
ORDER BY (event_time, currency);
```
**Status**: 🔴 NOT CREATED

---

#### ❌ **external_fred_indicators**
```sql
CREATE TABLE external_fred_indicators
(
    release_time DateTime64(3, 'UTC'),
    series_id String,
    series_name String,
    value Float64,
    unit String,
    scraped_at DateTime64(3, 'UTC')
)
ENGINE = MergeTree()
ORDER BY (release_time, series_id);
```
**Status**: 🔴 NOT CREATED

---

#### ❌ **external_commodity_prices**
```sql
CREATE TABLE external_commodity_prices
(
    price_time DateTime64(3, 'UTC'),
    symbol String,
    commodity_name String,
    price Decimal(18,5),
    currency String,
    change_pct Float64,
    volume UInt64,
    scraped_at DateTime64(3, 'UTC')
)
ENGINE = MergeTree()
ORDER BY (price_time, symbol);
```
**Status**: 🔴 NOT CREATED

---

## 🔧 SERVICES AUDIT

### **Service 1: polygon-live-collector**
**Status**: ⚠️ Partially Working - Writing to wrong schema

**Current Behavior**:
- ✅ Collecting live ticks from Polygon WebSocket
- ❌ Writing to TimescaleDB.market_ticks (should be live_ticks)
- ❌ Writing 14 columns (should be 6 columns)
- ❌ Calculating & storing mid/spread (should calculate on-the-fly)

**Fix Required**: Update schema alignment

---

### **Service 2: dukascopy-historical-downloader**
**Status**: ⚠️ Unknown - Need to check where it writes

**Expected Behavior**:
- ✅ Download historical ticks from Dukascopy
- ❌ Should write to ClickHouse.historical_ticks (table doesn't exist!)

**Fix Required**: 
1. Create historical_ticks table
2. Update service to write to ClickHouse

---

### **Service 3: tick-aggregator**
**Status**: ⚠️ Partially Working - Writing incomplete schema

**Current Behavior**:
- ✅ Aggregating ticks to candles
- ❌ Writing to ClickHouse.aggregates (should be live_aggregates + historical_aggregates)
- ❌ Writing 18 columns (should be 15, different columns)
- ❌ Missing critical columns: avg_spread, max_spread, min_spread, pct_change, is_complete

**Fix Required**: Major schema update

---

### **Service 4: external-data-collector**
**Status**: 🔴 NOT FUNCTIONAL - No target tables

**Current Behavior**:
- Status unknown (need to check implementation)
- ❌ Target tables don't exist (external_economic_calendar, external_fred_indicators, external_commodity_prices)

**Fix Required**:
1. Create 3 external data tables
2. Implement 3 data collectors

---

## 📋 MIGRATION PLAN

### **Phase 1: Database Schema Fix** (CRITICAL)

**1.1 TimescaleDB Migration**:
```sql
-- Rename table
ALTER TABLE market_ticks RENAME TO live_ticks;

-- Drop unnecessary columns
ALTER TABLE live_ticks 
  DROP COLUMN tick_id,
  DROP COLUMN tenant_id,
  DROP COLUMN mid,
  DROP COLUMN spread,
  DROP COLUMN exchange,
  DROP COLUMN source,
  DROP COLUMN event_type,
  DROP COLUMN use_case;

-- Verify: Should have 6 columns only
SELECT * FROM live_ticks LIMIT 1;
```

**1.2 ClickHouse Migration**:
```sql
-- Rename existing table
RENAME TABLE suho_analytics.aggregates TO suho_analytics.live_aggregates_old;

-- Create new live_aggregates with correct schema
CREATE TABLE suho_analytics.live_aggregates
(
    time DateTime64(3, 'UTC'),
    symbol String,
    timeframe Enum8('5m'=1, '15m'=2, '30m'=3, '1h'=4, '4h'=5, '1d'=6, '1w'=7),
    open Decimal(18,5),
    high Decimal(18,5),
    low Decimal(18,5),
    close Decimal(18,5),
    tick_count UInt32,
    avg_spread Decimal(18,5),
    max_spread Decimal(18,5),
    min_spread Decimal(18,5),
    price_range Decimal(18,5),
    pct_change Decimal(10,5),
    is_complete UInt8,
    created_at DateTime64(3, 'UTC')
)
ENGINE = MergeTree()
PARTITION BY (toYYYYMM(time), timeframe)
ORDER BY (symbol, timeframe, time)
TTL time + INTERVAL 7 DAY;

-- Migrate data (with column mapping)
INSERT INTO suho_analytics.live_aggregates
SELECT
    timestamp as time,
    symbol,
    CASE timeframe
        WHEN '5m' THEN 1
        WHEN '15m' THEN 2
        WHEN '30m' THEN 3
        WHEN '1h' THEN 4
        WHEN '4h' THEN 5
        WHEN '1d' THEN 6
        WHEN '1w' THEN 7
    END as timeframe,
    open,
    high,
    low,
    close,
    volume as tick_count,  -- Rename
    0 as avg_spread,  -- Default (missing data)
    0 as max_spread,  -- Default (missing data)
    0 as min_spread,  -- Default (missing data)
    range_pips as price_range,  -- Rename
    0 as pct_change,  -- Default (missing data)
    1 as is_complete,  -- Assume complete
    ingested_at as created_at
FROM suho_analytics.live_aggregates_old;

-- Verify migration
SELECT COUNT(*) FROM suho_analytics.live_aggregates;
SELECT COUNT(*) FROM suho_analytics.live_aggregates_old;

-- Drop old table after verification
-- DROP TABLE suho_analytics.live_aggregates_old;
```

**1.3 Create Missing Tables**:
```sql
-- Create historical_ticks
CREATE TABLE suho_analytics.historical_ticks (...);

-- Create historical_aggregates  
CREATE TABLE suho_analytics.historical_aggregates (...);

-- Create external tables
CREATE TABLE suho_analytics.external_economic_calendar (...);
CREATE TABLE suho_analytics.external_fred_indicators (...);
CREATE TABLE suho_analytics.external_commodity_prices (...);
```

---

### **Phase 2: Services Fix**

**2.1 polygon-live-collector**:
- Update table name: market_ticks → live_ticks
- Remove columns: tick_id, tenant_id, mid, spread, exchange, source, event_type, use_case
- Update INSERT statements to 6 columns only

**2.2 tick-aggregator**:
- Update table name: aggregates → live_aggregates
- Add spread calculation logic (avg, max, min from ticks)
- Add pct_change calculation
- Add is_complete flag
- Update column names: volume → tick_count, range_pips → price_range
- Remove unnecessary columns: vwap, body_pips, start_time, end_time, source, event_type, indicators

**2.3 dukascopy-historical-downloader**:
- Verify writes to ClickHouse.historical_ticks
- Aggregate to ClickHouse.historical_aggregates

**2.4 external-data-collector**:
- Implement Economic Calendar collector (MQL5)
- Implement FRED API collector
- Implement Commodity Prices collector (Yahoo Finance)

---

## 🎯 PRIORITY ACTIONS

### **IMMEDIATE (This Week)**:
1. ✅ Create audit report (DONE)
2. 🔴 Database schema migration (TimescaleDB + ClickHouse)
3. 🔴 Create missing ClickHouse tables

### **SHORT-TERM (Next Week)**:
4. ⚠️ Update polygon-live-collector schema
5. ⚠️ Update tick-aggregator schema
6. ⚠️ Verify dukascopy-downloader

### **MEDIUM-TERM (Week 3)**:
7. ⚠️ Implement external-data-collector (3 sources)
8. ✅ Validate complete data pipeline

---

## ❗ RISKS & IMPACTS

**If NOT Fixed**:
- ❌ Feature engineering service WILL FAIL (missing columns)
- ❌ ML training WILL FAIL (missing external data)
- ❌ Data quality issues (spread metrics missing)
- ❌ Storage waste (unnecessary columns)

**Migration Complexity**:
- 🟡 Medium - Requires downtime for schema changes
- 🟡 Data migration needed for ClickHouse
- ✅ Can keep old tables as backup during migration

---

## ✅ NEXT STEPS

**Decision Required**:
1. Approve migration plan
2. Schedule downtime window (2-4 hours for migration)
3. Backup current data before migration
4. Execute Phase 1 (Database Schema Fix)
5. Execute Phase 2 (Services Fix)

**Estimated Time**:
- Phase 1 (DB Migration): 2-3 hours
- Phase 2 (Services Fix): 1-2 days
- Testing & Validation: 1 day

**Total**: ~3-4 days untuk complete alignment

---

**Report Generated**: 2025-10-18
**Next Review**: After Phase 1 completion
