# ✅ Schema Alignment Verification Report

**Date**: 2025-10-18
**Purpose**: Verify all central-hub schema files match `table_database_input.md` v1.8.0
**Status**: ✅ **COMPLETE** - All schemas aligned

---

## 📋 Executive Summary

All schema definition files in `01-core-infrastructure/central-hub/shared/schemas/` have been updated to match the database migration specifications from `table_database_input.md` v1.8.0.

**Changes Made**:
- ✅ 3 schema files updated (TimescaleDB + ClickHouse)
- ✅ 4 new schema files created (external tables + historical_aggregates)
- ✅ Old schema files remain for reference (will be archived)
- ✅ All schemas match live database state

---

## 🗄️ TimescaleDB Schema Verification

### **Table: live_ticks** ✅ ALIGNED

**Schema File**: `timescaledb/01_live_ticks.sql`

**Specification (table_database_input.md)**:
```sql
time TIMESTAMPTZ NOT NULL,
symbol TEXT NOT NULL,
bid NUMERIC(18,5) NOT NULL,
ask NUMERIC(18,5) NOT NULL,
timestamp_ms BIGINT NOT NULL,
ingested_at TIMESTAMPTZ DEFAULT NOW()
```

**Schema File Columns**: ✅ **MATCHES**
- time (TIMESTAMPTZ, partition key)
- symbol (TEXT)
- bid (NUMERIC(18,5))
- ask (NUMERIC(18,5))
- timestamp_ms (BIGINT)
- ingested_at (TIMESTAMPTZ, default NOW())

**Key Features**:
- ✅ Hypertable with 1-day chunks
- ✅ Compression policy (7 days)
- ✅ Retention policy (90 days)
- ✅ Continuous aggregate (1-minute OHLC with spread metrics)
- ✅ Helper functions (get_mid_price, get_spread)
- ✅ Unique index for deduplication (symbol, time, timestamp_ms)

**Migration Notes**:
- Renamed from `market_ticks` to `live_ticks`
- Removed 8 unnecessary columns (tick_id, tenant_id, mid, spread, exchange, source, event_type, use_case)
- Storage reduction: ~57% per row

---

## 📊 ClickHouse Schema Verification

### **Table 1: live_aggregates** ✅ ALIGNED

**Schema File**: `clickhouse/02_live_aggregates.sql`

**Specification (table_database_input.md)**:
```sql
time DateTime64(3, 'UTC'),
symbol String,
timeframe Enum8('5m'=1, '15m'=2, '30m'=3, '1h'=4, '4h'=5, '1d'=6, '1w'=7),
open, high, low, close Decimal(18,5),
tick_count UInt32,
avg_spread, max_spread, min_spread Decimal(18,5),
price_range Decimal(18,5),
pct_change Float64,
is_complete UInt8,
created_at DateTime64(3, 'UTC')
```

**Schema File Columns**: ✅ **MATCHES** (15 columns)

**Key Features**:
- ✅ MergeTree engine
- ✅ Partition by (month, symbol)
- ✅ Order by (symbol, timeframe, time)
- ✅ TTL: 7 days
- ✅ Enum8 timeframe (8x storage efficiency)
- ✅ ML features: avg_spread, max_spread, min_spread, pct_change, is_complete
- ✅ Materialized views: hourly stats, daily stats
- ✅ Helper functions: get_ohlc_mid, get_body_size, get_upper_shadow, get_lower_shadow

**Migration Notes**:
- Renamed from `aggregates` to `live_aggregates`
- Added 5 ML features (spread metrics, pct_change, is_complete)
- Removed 8 unnecessary columns (vwap, body_pips, start_time, end_time, source, event_type, indicators, version)
- Changed timeframe from String to Enum8

---

### **Table 2: historical_ticks** ✅ ALIGNED

**Schema File**: `clickhouse/01_historical_ticks.sql`

**Specification (table_database_input.md)**:
```sql
time DateTime64(3, 'UTC'),
symbol String,
bid Decimal(18,5),
ask Decimal(18,5),
timestamp_ms UInt64,
ingested_at DateTime64(3, 'UTC')
```

**Schema File Columns**: ✅ **MATCHES** (6 columns)

**Key Features**:
- ✅ MergeTree engine
- ✅ Partition by (month, symbol)
- ✅ Order by (symbol, time)
- ✅ TTL: 10 years (long-term storage)
- ✅ Materialized views: daily stats, monthly stats
- ✅ Helper functions: get_tick_mid, get_tick_spread

**Data Sources**:
- Dukascopy historical data (.bi5 files)
- Collector: dukascopy-historical-downloader
- Transport: NATS (market.{symbol}.tick)
- Writer: data-bridge → clickhouse_writer.py

**Migration Notes**:
- Renamed from `ticks` to `historical_ticks`
- Aligned with live_ticks schema (6 columns)
- Removed: mid, spread, exchange, event_type, use_case

---

### **Table 3: historical_aggregates** ✅ ALIGNED

**Schema File**: `clickhouse/03_historical_aggregates.sql`

**Specification (table_database_input.md)**:
```sql
-- Same 15-column schema as live_aggregates
-- TTL: 10 years (vs 7 days for live)
```

**Schema File Columns**: ✅ **MATCHES** (15 columns, same as live_aggregates)

**Key Features**:
- ✅ MergeTree engine
- ✅ Partition by (year, symbol) - optimized for historical queries
- ✅ Order by (symbol, timeframe, time)
- ✅ TTL: 10 years
- ✅ Materialized view: yearly statistics
- ✅ Same ML features as live_aggregates

**Data Sources**:
- Historical tick aggregation from historical_ticks
- polygon-historical-downloader (OHLCV bars from Polygon API)

**Purpose**:
- Long-term ML training data
- Backtesting
- Feature engineering

---

### **Table 4: external_economic_calendar** ✅ ALIGNED

**Schema File**: `clickhouse/04_external_economic_calendar.sql`

**Specification (table_database_input.md)**:
```sql
event_time DateTime64(3, 'UTC'),
currency String,
event_name String,
impact Enum8('low'=1, 'medium'=2, 'high'=3),
forecast Nullable(String),
previous Nullable(String),
actual Nullable(String),
scraped_at DateTime64(3, 'UTC')
```

**Schema File Columns**: ✅ **MATCHES** (8 columns)

**Key Features**:
- ✅ MergeTree engine
- ✅ Partition by month
- ✅ Order by (event_time, currency, event_name)
- ✅ TTL: 5 years
- ✅ Indexes: currency, impact, event_time
- ✅ Materialized views: high-impact events (monthly), event types

**Data Sources**:
- MQL5 Economic Calendar
- Collector: external-data-collector → mql5_historical_scraper.py
- Update Frequency: Every 6 hours
- Backfill: 12 months

**ML Use Cases**:
- Pre-event volatility spike detection
- Post-event price movement correlation
- Currency strength index
- Risk-on/risk-off regime classification

---

### **Table 5: external_fred_indicators** ✅ ALIGNED

**Schema File**: `clickhouse/05_external_fred_indicators.sql`

**Specification (table_database_input.md)**:
```sql
release_time DateTime64(3, 'UTC'),
series_id String,
series_name String,
value Float64,
unit String,
scraped_at DateTime64(3, 'UTC')
```

**Schema File Columns**: ✅ **MATCHES** (6 columns)

**Key Features**:
- ✅ MergeTree engine
- ✅ Partition by year
- ✅ Order by (series_id, release_time)
- ✅ TTL: 10 years
- ✅ Indexes: series_id, release_time
- ✅ Materialized views: latest values, quarterly aggregates

**Data Sources**:
- FRED API (Federal Reserve Economic Data)
- Collector: external-data-collector → fred_economic.py
- Update Frequency: Every 6 hours

**Tracked Indicators**:
- GDP, UNRATE, CPIAUCSL, FEDFUNDS, DGS10, DEXUSEU

**ML Use Cases**:
- Macro regime classification
- USD strength prediction
- Risk-on/risk-off sentiment
- Inflation expectations
- Central bank policy prediction

---

### **Table 6: external_commodity_prices** ✅ ALIGNED

**Schema File**: `clickhouse/06_external_commodity_prices.sql`

**Specification (table_database_input.md)**:
```sql
price_time DateTime64(3, 'UTC'),
symbol String,
commodity_name String,
price Decimal(18,5),
currency String,
change_pct Float64,
volume UInt64,
scraped_at DateTime64(3, 'UTC')
```

**Schema File Columns**: ✅ **MATCHES** (8 columns)

**Key Features**:
- ✅ MergeTree engine
- ✅ Partition by month
- ✅ Order by (symbol, price_time)
- ✅ TTL: 5 years
- ✅ Indexes: symbol, price_time
- ✅ Materialized views: latest prices, daily OHLC

**Data Sources**:
- Yahoo Finance API
- Collector: external-data-collector → yahoo_finance_commodity.py
- Update Frequency: Every 1 hour

**Tracked Commodities**:
- GC=F (Gold), SI=F (Silver), CL=F (Crude Oil), NG=F (Natural Gas)

**ML Use Cases**:
- Risk-on/risk-off sentiment
- USD correlation analysis
- Energy sector exposure
- Inflation expectations
- Cross-asset correlation

---

## 📝 Schema Files Summary

### **TimescaleDB** (1 table)
| File | Table Name | Columns | Status |
|------|------------|---------|--------|
| `timescaledb/01_live_ticks.sql` | live_ticks | 6 | ✅ ALIGNED |

### **ClickHouse** (6 tables)
| File | Table Name | Columns | Status |
|------|------------|---------|--------|
| `clickhouse/01_historical_ticks.sql` | historical_ticks | 6 | ✅ ALIGNED |
| `clickhouse/02_live_aggregates.sql` | live_aggregates | 15 | ✅ ALIGNED |
| `clickhouse/03_historical_aggregates.sql` | historical_aggregates | 15 | ✅ ALIGNED |
| `clickhouse/04_external_economic_calendar.sql` | external_economic_calendar | 8 | ✅ ALIGNED |
| `clickhouse/05_external_fred_indicators.sql` | external_fred_indicators | 6 | ✅ ALIGNED |
| `clickhouse/06_external_commodity_prices.sql` | external_commodity_prices | 8 | ✅ ALIGNED |

### **Old Schema Files** (To Be Archived)
| File | Status | Replacement |
|------|--------|-------------|
| `timescaledb/01_market_ticks.sql` | ⚠️ OBSOLETE | 01_live_ticks.sql |
| `clickhouse/01_ticks.sql` | ⚠️ OBSOLETE | 01_historical_ticks.sql |
| `clickhouse/02_aggregates.sql` | ⚠️ OBSOLETE | 02_live_aggregates.sql |

---

## ✅ Verification Checklist

### **Schema Completeness**
- ✅ All 7 tables from `table_database_input.md` have schema files
- ✅ All column names match specifications
- ✅ All column types match specifications
- ✅ All column constraints match specifications

### **Schema Features**
- ✅ Correct partitioning strategies (time-based)
- ✅ Correct ordering keys (optimized for queries)
- ✅ Correct TTL policies (retention as specified)
- ✅ Indexes for query performance
- ✅ Materialized views for pre-aggregation
- ✅ Helper functions for derived values

### **Documentation**
- ✅ Column comments present
- ✅ Table comments present
- ✅ Data sources documented
- ✅ ML use cases documented
- ✅ Migration notes present
- ✅ Verification queries included

### **Migration Compatibility**
- ✅ Schema files match live database state
- ✅ Schema files match service code (router.py, clickhouse_writer.py, tick-aggregator)
- ✅ Backward compatibility maintained (old field names supported via .get())

---

## 🎯 Success Metrics

### **Before Schema Alignment**
- ❌ 3 schema files with OLD specifications (market_ticks, ticks, aggregates)
- ❌ 4 missing schema files (external tables + historical_aggregates)
- ❌ Schema files didn't match live database state
- ❌ Schema files didn't match service code

### **After Schema Alignment**
- ✅ 7 schema files with CORRECT specifications
- ✅ All schema files created (TimescaleDB + ClickHouse)
- ✅ Schema files match live database state
- ✅ Schema files match service code
- ✅ Documentation complete (column comments, migration notes, verification queries)
- ✅ Old schema files preserved for reference (not deleted)

---

## 🔄 Next Steps

### **Immediate**
1. ⏳ Archive old schema files:
   ```bash
   mkdir -p 01-core-infrastructure/central-hub/shared/schemas/archive
   mv timescaledb/01_market_ticks.sql schemas/archive/
   mv clickhouse/01_ticks.sql schemas/archive/
   mv clickhouse/02_aggregates.sql schemas/archive/
   ```

2. ⏳ Update schema initialization script (if exists) to use new schema files

3. ⏳ Test schema creation on clean database instance

### **Future**
1. Create schema versioning system (track schema changes over time)
2. Add schema migration scripts (automated upgrades)
3. Create schema validation tests (ensure schema files match live DB)

---

## 📚 Related Documentation

- `table_database_input.md` - Master database specification
- `MIGRATION_COMPLETE_2025-10-18.md` - Database migration summary
- `00_DATA_INGESTION_ALIGNMENT_STATUS.md` - Service alignment status
- `AUDIT_REPORT_2025-10-18.md` - Pre-migration audit
- `PHASE2_SERVICE_FIXES_REQUIRED.md` - Service fix specifications

---

**Verification Completed**: 2025-10-18
**Schema Files**: 7/7 aligned
**Status**: ✅ **SUCCESS**

All central-hub schema definition files now accurately reflect the migrated database schemas and match `table_database_input.md` v1.8.0 specifications.
