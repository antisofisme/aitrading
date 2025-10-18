# Phase 2: Service Fixes Required

**Date**: 2025-10-18
**Status**: Phase 1 Database Migration ✅ Complete, Phase 2 In Progress

---

## ✅ Phase 1 Complete - Database Schema Migration

### TimescaleDB:
- ✅ Table renamed: `market_ticks` → `live_ticks`
- ✅ Dropped 8 columns: tick_id, tenant_id, mid, spread, exchange, source, event_type, use_case
- ✅ Final schema: 6 columns (time, symbol, bid, ask, timestamp_ms, ingested_at)
- ✅ Backup created: 4.5M rows preserved

### ClickHouse:
- ✅ Table recreated: `live_aggregates` with correct 15-column schema
- ✅ Created 5 missing tables:
  - historical_ticks
  - historical_aggregates
  - external_economic_calendar
  - external_fred_indicators
  - external_commodity_prices
- ✅ Old table preserved: `aggregates_old` (backup)

---

## 🔧 Phase 2: Service Updates Required

### **Service 1: central-hub (Database Manager)** ✅ DONE

**File**: `01-core-infrastructure/central-hub/shared/components/data_manager/router.py:75-92`

**Changes Made**:
- ✅ Changed table name in SELECT: `market_ticks` → `live_ticks`
- ✅ Changed table name in INSERT: `market_ticks` → `live_ticks`
- ✅ Updated INSERT columns from 10 to 5: removed tenant_id, mid, spread, source, event_type

**Result**: Central Hub now writes clean 6-column schema to live_ticks

---

### **Service 2: data-bridge** ✅ DONE

**File**: `02-data-processing/data-bridge/src/main.py:224,262,287`

**Changes Made**:
- ✅ Updated comments: `market_ticks` → `live_ticks`
- ✅ Updated logger messages: `aggregates` → `live_aggregates`
- ✅ Updated routing docstrings to reference correct table names

**Result**: Comments and logs now reflect correct table names

---

### **Service 3: tick-aggregator** 🔴 IN PROGRESS

**Files**:
- `02-data-processing/tick-aggregator/src/aggregator.py` (PRIMARY)
- `02-data-processing/data-bridge/src/clickhouse_writer.py` (SECONDARY)

#### **aggregator.py Changes Required**:

**Line 201**: Change table name
```python
# OLD:
FROM market_ticks
# NEW:
FROM live_ticks
```

**Lines 193-200**: Update query (mid and spread don't exist anymore)
```python
# OLD:
SELECT symbol, time as timestamp, bid, ask, mid, spread, ...
FROM market_ticks

# NEW:
SELECT
    symbol,
    time as timestamp,
    bid,
    ask,
    (bid + ask) / 2 as mid,
    ask - bid as spread,
    EXTRACT(EPOCH FROM time)::BIGINT * 1000 as timestamp_ms
FROM live_ticks
```

**Lines 241-247**: Update resampling to include spread metrics
```python
# OLD:
resampled = group.resample(resample_rule).agg({
    'mid': ['first', 'max', 'min', 'last', 'count'],
    'bid': 'mean',
    'ask': 'mean',
    'spread': 'mean',
    'timestamp_ms': 'first'
})

# NEW:
resampled = group.resample(resample_rule).agg({
    'mid': ['first', 'max', 'min', 'last', 'count'],
    'spread': ['mean', 'max', 'min'],  # NEW: avg, max, min spread
    'timestamp_ms': 'first'
})
```

**Lines 283-318**: Update candle output schema
```python
# REMOVE:
- vwap (not needed in aggregates, calculated on-the-fly if needed)
- range_pips → rename to price_range
- body_pips (not needed)
- start_time (not needed)
- end_time (not needed)
- source (not needed)
- event_type (not needed)

# ADD:
- avg_spread: float(resampled[('spread', 'mean')])
- max_spread: float(resampled[('spread', 'max')])
- min_spread: float(resampled[('spread', 'min')])
- pct_change: (close_price - open_price) / open_price * 100 if open_price != 0 else 0
- is_complete: 1 (or calculate based on tick_count threshold)

# RENAME:
- volume → tick_count (already named correctly in current code, just need to ensure consistency)

# NEW candle structure:
candle = {
    'symbol': symbol,
    'timeframe': timeframe,
    'timestamp_ms': timestamp_ms,
    'open': float(open_price),
    'high': float(high_price),
    'low': float(low_price),
    'close': float(close_price),
    'tick_count': tick_count,  # Was 'volume'
    'avg_spread': float(resampled[('spread', 'mean')]),  # NEW
    'max_spread': float(resampled[('spread', 'max')]),   # NEW
    'min_spread': float(resampled[('spread', 'min')]),   # NEW
    'price_range': float(range_pips),  # Was 'range_pips'
    'pct_change': float(pct_change),  # NEW
    'is_complete': 1  # NEW (could be dynamic based on tick_count)
}
```

#### **clickhouse_writer.py Changes Required**:

**Line 295**: Change table name in deduplication query
```python
# OLD:
FROM aggregates
# NEW:
FROM live_aggregates
```

**Line 398**: Change table name in INSERT
```python
# OLD:
self.client.insert('aggregates', data, ...)
# NEW:
self.client.insert('live_aggregates', data, ...)
```

**Lines 373-405**: Update column list and data preparation
```python
# OLD columns (19):
'symbol', 'timeframe', 'timestamp', 'timestamp_ms',
'open', 'high', 'low', 'close', 'volume',
'vwap', 'range_pips', 'body_pips', 'start_time', 'end_time',
'source', 'event_type', 'indicators', 'version', 'created_at'

# NEW columns (15):
'time',  # Was 'timestamp'
'symbol',
'timeframe',  # Keep as Enum8 mapping (handled by ClickHouse)
'open', 'high', 'low', 'close',
'tick_count',  # Was 'volume'
'avg_spread',  # NEW
'max_spread',  # NEW
'min_spread',  # NEW
'price_range',  # Was 'range_pips'
'pct_change',  # NEW
'is_complete',  # NEW
'created_at'
```

**Data preparation changes**:
```python
# Remove:
- timestamp → use timestamp_ms as 'time'
- vwap
- body_pips
- start_time
- end_time
- source
- event_type
- indicators (if not needed)
- version

# Add:
- avg_spread = float(agg.get('avg_spread', 0))
- max_spread = float(agg.get('max_spread', 0))
- min_spread = float(agg.get('min_spread', 0))
- pct_change = float(agg.get('pct_change', 0))
- is_complete = int(agg.get('is_complete', 1))

# Rename:
- volume → tick_count
- range_pips → price_range
```

---

### **Service 4: dukascopy-downloader** ⏳ PENDING

**Action**: Verify writes to ClickHouse.historical_ticks (not live_ticks)

**Required Changes**:
- Ensure writes to `historical_ticks` table (not `ticks`)
- Use correct 6-column schema: time, symbol, bid, ask, timestamp_ms, ingested_at
- If aggregating: write to `historical_aggregates` with 15-column schema

---

### **Service 5: external-data-collector** ⏳ PENDING

**Action**: Implement 3 data collectors for external data tables

**Required Tables**:
1. `external_economic_calendar` (MQL5 calendar data)
2. `external_fred_indicators` (FRED API)
3. `external_commodity_prices` (Yahoo Finance)

**Status**: Tables created, collectors not yet implemented

---

## 📋 Implementation Order

1. ✅ Phase 1: Database Migration (DONE)
2. ✅ central-hub router.py (DONE)
3. ✅ data-bridge main.py comments (DONE)
4. 🔄 tick-aggregator aggregator.py (IN PROGRESS)
5. 🔄 data-bridge clickhouse_writer.py (IN PROGRESS)
6. ⏳ Rebuild and restart services
7. ⏳ Test data flow end-to-end
8. ⏳ dukascopy-downloader verification
9. ⏳ external-data-collector implementation

---

## 🎯 Expected Outcome

After all fixes:
- ✅ Live ticks: Clean 6-column storage (no bloat)
- ✅ Live aggregates: 15 columns with all ML-required features
- ✅ Historical data: Separate tables with correct schemas
- ✅ External data: 3 sources ingested
- ✅ Feature engineering: All 110 features can be calculated

---

**Last Updated**: 2025-10-18 (after Phase 1 completion)
