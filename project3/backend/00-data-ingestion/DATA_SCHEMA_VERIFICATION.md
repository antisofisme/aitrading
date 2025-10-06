# 📊 Data Schema Verification Report

## Overview
Laporan verifikasi output data collectors dengan schema database

---

## 1️⃣ POLYGON LIVE COLLECTOR

### Output Format (Live Ticks)
```python
{
    'symbol': 'EUR/USD',          # String
    'bid': 1.0848,                # Float
    'ask': 1.0850,                # Float
    'mid': 1.0849,                # Float (calculated)
    'spread': 2.0,                # Float (in pips)
    'timestamp': 1706198400000,   # Int (Unix milliseconds)
    'timestamp_ms': 1706198400000,# Int (Unix milliseconds)
    'exchange': 1,                # Int (Exchange ID)
    'source': 'polygon_websocket',# String
    'event_type': 'quote'         # String
}
```

### Target Schema: ClickHouse `ticks` table
```sql
CREATE TABLE ticks (
    symbol String,                    -- ✅ MATCH
    timestamp DateTime64(3, 'UTC'),   -- ✅ Convert from timestamp_ms
    timestamp_ms UInt64,              -- ✅ MATCH
    bid Decimal(18, 5),               -- ✅ MATCH
    ask Decimal(18, 5),               -- ✅ MATCH
    mid Decimal(18, 5),               -- ✅ MATCH
    spread Decimal(10, 5),            -- ✅ MATCH
    exchange UInt16,                  -- ✅ MATCH
    source String,                    -- ✅ MATCH
    event_type String,                -- ✅ MATCH
    use_case String DEFAULT '',       -- ⚠️ OPTIONAL (for confirmation pairs)
    ingested_at DateTime64(3, 'UTC') DEFAULT now64(3)
)
```

### ✅ Verification Result: **PERFECT MATCH**
- All output fields map correctly to schema
- Type conversions handled properly
- No missing fields

---

## 2️⃣ POLYGON HISTORICAL DOWNLOADER

### Output Format (OHLCV Bars)
```python
{
    'symbol': 'EUR/USD',          # String
    'timestamp': datetime_object, # DateTime
    'timestamp_ms': 1706198400000,# Int (Unix milliseconds)
    'open': 1.0845,               # Float
    'high': 1.0855,               # Float
    'low': 1.0840,                # Float
    'close': 1.0850,              # Float
    'bid': 1.0848,                # Float
    'ask': 1.0850,                # Float
    'mid': 1.0849,                # Float
    'volume': 12345,              # Int
    'vwap': 1.0847,               # Float
    'num_trades': 100,            # Int
    'source': 'polygon_historical'# String
}
```

### Target Schema: ClickHouse `aggregates` table
```sql
CREATE TABLE aggregates (
    symbol String,                    -- ✅ MATCH
    timeframe String,                 -- ❌ MISSING IN OUTPUT
    timestamp DateTime64(3, 'UTC'),   -- ✅ MATCH
    timestamp_ms UInt64,              -- ✅ MATCH
    open Decimal(18, 5),              -- ✅ MATCH
    high Decimal(18, 5),              -- ✅ MATCH
    low Decimal(18, 5),               -- ✅ MATCH
    close Decimal(18, 5),             -- ✅ MATCH
    volume UInt64,                    -- ✅ MATCH
    vwap Decimal(18, 5) DEFAULT 0,   -- ✅ MATCH
    range_pips Decimal(10, 5),        -- ❌ MISSING IN OUTPUT
    start_time DateTime64(3, 'UTC'),  -- ❌ MISSING IN OUTPUT
    end_time DateTime64(3, 'UTC'),    -- ❌ MISSING IN OUTPUT
    source String,                    -- ✅ MATCH
    event_type String DEFAULT 'ohlcv',-- ⚠️ IMPLIED
    ingested_at DateTime64(3, 'UTC') DEFAULT now64(3)
)
```

### ⚠️ Verification Result: **NEEDS ENHANCEMENT**

**Missing Fields:**
1. ✅ `timeframe` - Harus ditambahkan (1m, 5m, 1h, dll)
2. ✅ `range_pips` - Bisa dihitung dari high-low
3. ✅ `start_time` - Sama dengan timestamp
4. ✅ `end_time` - Hitung dari timeframe

**Extra Fields (Not in Schema):**
- `bid`, `ask`, `mid` → Bisa disimpan, tapi tidak ada di schema aggregates
- `num_trades` → Tidak ada di schema

**Recommendation:**
```python
# Add these fields in clickhouse_writer.py:
{
    ...existing fields,
    'timeframe': '1m',  # From config/API parameter
    'range_pips': round((high - low) * 10000, 2),
    'start_time': timestamp,
    'end_time': timestamp + timeframe_ms,
    'event_type': 'ohlcv'
}
```

---

## 3️⃣ EXTERNAL DATA COLLECTOR (Economic Calendar)

### Output Format (Economic Events)
```python
{
    'date': '2024-01-26',         # String (YYYY-MM-DD)
    'time': '13:30',              # String (HH:MM)
    'currency': 'USD',            # String
    'event': 'Non-Farm Payrolls', # String
    'forecast': '340K',           # String or None
    'previous': '325K',           # String or None
    'actual': '353K',             # String or None
    'impact': 'high'              # String (high/medium/low) or None
}
```

### Target Schema: PostgreSQL/TimescaleDB `market_context` table
```sql
CREATE TABLE market_context (
    id BIGSERIAL PRIMARY KEY,
    event_id VARCHAR(100),                -- ❌ MISSING IN OUTPUT
    external_id VARCHAR(100),             -- ❌ MISSING IN OUTPUT
    data_type VARCHAR(30) NOT NULL,       -- ⚠️ MUST SET: 'economic_calendar'
    symbol VARCHAR(50) NOT NULL,          -- ✅ Map from 'event'
    timestamp BIGINT NOT NULL,            -- ⚠️ CONVERT from date+time
    time_status VARCHAR(20) NOT NULL DEFAULT 'historical',  -- ⚠️ LOGIC NEEDED

    -- Values
    value DECIMAL(20,8),                  -- ⚠️ PARSE from actual/forecast
    value_text VARCHAR(100),              -- ✅ Can use event name

    -- Context
    category VARCHAR(50),                 -- ⚠️ INFER from event name
    importance VARCHAR(20),               -- ✅ Map from 'impact'
    frequency VARCHAR(20),                -- ⚠️ INFER
    units VARCHAR(50),                    -- ⚠️ PARSE from value (K, M, %)

    -- Event fields
    actual_value DECIMAL(20,8),           -- ⚠️ PARSE from 'actual'
    forecast_value DECIMAL(20,8),         -- ⚠️ PARSE from 'forecast'
    previous_value DECIMAL(20,8),         -- ⚠️ PARSE from 'previous'
    event_date TIMESTAMP,                 -- ✅ CONVERT from date+time
    release_date TIMESTAMP,               -- ✅ Same as event_date (for now)

    -- Market impact
    currency_impact TEXT[],               -- ✅ Map from 'currency'
    forex_impact VARCHAR(30),             -- ⚠️ CALCULATE based on event
    market_impact_score DECIMAL(3,2),     -- ⚠️ CALCULATE from surprise

    -- Source
    source VARCHAR(50) NOT NULL,          -- ⚠️ MUST SET: 'mql5'
    reliability VARCHAR(20) DEFAULT 'high',
    metadata JSONB,                       -- ✅ Store original event
    created_at TIMESTAMP DEFAULT NOW()
)
```

### ⚠️ Verification Result: **MAJOR TRANSFORMATION NEEDED**

**Missing Critical Fields:**
1. ❌ `event_id` - Generate: `{currency}_{event_slug}_{date}`
2. ❌ `external_id` - Generate unique ID
3. ❌ `data_type` - Set to `'economic_calendar'`
4. ❌ `timestamp` - Convert `date + time` to Unix milliseconds
5. ❌ `time_status` - Logic:
   - If actual exists → 'historical'
   - If date > now → 'scheduled'
   - If date < now && !actual → 'missed_data'

**Value Parsing Needed:**
1. Parse numeric values: `'340K'` → `340000.0`
2. Handle percentages: `'2.5%'` → `2.5`
3. Handle decimals: `'1.8B'` → `1800000000.0`

**Market Impact Calculation:**
```python
# Calculate surprise magnitude
if actual and forecast:
    surprise = abs(actual - forecast) / abs(forecast)
    market_impact_score = min(surprise * 2.0, 1.0)
else:
    market_impact_score = None
```

**Recommendation:**
Create transformation pipeline in external-data-collector:
```python
def transform_to_market_context(event: dict) -> dict:
    """Transform scraped event to market_context format"""
    return {
        'event_id': generate_event_id(event),
        'external_id': generate_external_id(event),
        'data_type': 'economic_calendar',
        'symbol': event['event'],
        'timestamp': convert_to_unix_ms(event['date'], event['time']),
        'time_status': determine_time_status(event),
        'value': parse_numeric_value(event.get('actual') or event.get('forecast')),
        'value_text': event['event'],
        'category': infer_category(event['event']),
        'importance': event.get('impact', 'medium'),
        'actual_value': parse_numeric_value(event.get('actual')),
        'forecast_value': parse_numeric_value(event.get('forecast')),
        'previous_value': parse_numeric_value(event.get('previous')),
        'event_date': convert_to_timestamp(event['date'], event['time']),
        'release_date': convert_to_timestamp(event['date'], event['time']),
        'currency_impact': [event['currency']],
        'forex_impact': calculate_forex_impact(event),
        'market_impact_score': calculate_impact_score(event),
        'source': 'mql5',
        'reliability': 'high',
        'metadata': event,  # Store original
        'created_at': datetime.now()
    }
```

---

## 📋 SUMMARY & ACTION ITEMS

### ✅ Live Collector - READY
- Perfect match with ClickHouse `ticks` table
- No changes needed

### ⚠️ Historical Downloader - NEEDS FIX
**Required Changes in `/polygon-historical-downloader/src/clickhouse_writer.py`:**
```python
# Add missing fields:
1. timeframe (from config)
2. range_pips (calculate: (high-low)*10000)
3. start_time (= timestamp)
4. end_time (= timestamp + timeframe duration)
5. event_type ('ohlcv')
```

### ⚠️ External Collector - NEEDS MAJOR ENHANCEMENT
**Required Changes in `/external-data-collector/src/`:**
1. Create `transformers/economic_calendar.py`
2. Implement value parsing (K, M, B, %)
3. Generate event_id and external_id
4. Calculate market_impact_score
5. Add database writer for PostgreSQL/TimescaleDB

---

## 🗂️ Schema Files Location

### Active Schemas (Need to be created/updated):
```
backend/
├── 00-data-ingestion/
│   ├── schemas/
│   │   ├── clickhouse_forex.sql       # ✅ EXISTS (archived)
│   │   └── postgresql_market.sql      # ✅ EXISTS (archived)
│   └── DATA_SCHEMA_VERIFICATION.md    # ✅ THIS FILE
```

### Schema Files (Currently Archived):
1. `/00-data-ingestion/_archived/clickhouse-consumer/sql/schema.sql`
2. `/00-data-ingestion/_archived/external-data/database/database_schema_hybrid.sql`

**Recommendation:**
1. Move active schemas to `/00-data-ingestion/schemas/`
2. Update schemas based on this verification
3. Create migration scripts if needed

---

## 🔄 Next Steps

### Priority 1: Fix Historical Downloader
1. Update `clickhouse_writer.py` to include missing fields
2. Test with sample data
3. Verify ClickHouse insertion

### Priority 2: Enhance External Collector
1. Create transformation pipeline
2. Implement value parser
3. Add PostgreSQL writer
4. Test end-to-end flow

### Priority 3: Schema Management
1. Create active schema directory
2. Add schema version tracking
3. Document migration procedures

---

**Date**: 2025-10-06
**Status**: Verification Complete - Action Required
