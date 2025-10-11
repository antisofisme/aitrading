# Timezone Standardization Guide - Multi-Tenant Trading System

**Document Version:** 1.0
**Last Updated:** 2025-10-11
**Status:** ✅ IMPLEMENTED

---

## 🎯 Executive Summary

This guide defines the timezone standardization strategy for our multi-tenant AI trading platform. All timestamps across the system follow a **3-layer architecture** ensuring consistency, flexibility, and compliance with global trading standards.

### Key Principles

1. **ALWAYS store in UTC** (Storage Layer)
2. **ALWAYS return both UTC + localized timestamps** (API Layer)
3. **Client chooses display timezone** (Presentation Layer)
4. **Use Unix epoch (ms) for comparisons** (System Layer)

---

## 🌍 Problem Statement

### Multi-Timezone Challenges

Our trading system faces unique timestamp challenges:

| Component | Timezone Challenge |
|-----------|-------------------|
| **Data APIs** | Polygon.io returns UTC timestamps |
| **System Internal** | Services run in UTC containers |
| **Multi-Tenant Clients** | Indonesia (WIB/WITA/WIT), Singapore (SGT), NY (EST), etc. |
| **Trading Platforms** | MT4/MT5 brokers use GMT+2 or GMT+3 |
| **Compliance** | Financial regulations require accurate timestamping |

### Impact of Poor Timestamp Management

- ❌ Client confusion ("Why does my order show wrong time?")
- ❌ Audit failures (timestamps don't match)
- ❌ Trading errors (orders executed at wrong time)
- ❌ Data inconsistency across databases

---

## 🏗️ Solution Architecture

### 3-Layer Timestamp Strategy

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 3: Client Display (Localized)                   │
│  ┌───────────────────────────────────────────────────┐ │
│  │ WIB: 2025-10-11 12:00:00+07:00                   │ │
│  │ EST: 2025-10-11 01:00:00-04:00                   │ │
│  │ GMT+2: 2025-10-11 07:00:00+02:00                 │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                         ↑
┌─────────────────────────────────────────────────────────┐
│  LAYER 2: API Response (UTC + Unix Epoch)              │
│  ┌───────────────────────────────────────────────────┐ │
│  │ timestamp_utc: "2025-10-11T05:00:00.000Z"        │ │
│  │ timestamp_ms: 1760155200000                       │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                         ↑
┌─────────────────────────────────────────────────────────┐
│  LAYER 1: Storage (ALWAYS UTC)                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ PostgreSQL: TIMESTAMPTZ '2025-10-11 05:00:00+00' │ │
│  │ ClickHouse: DateTime('UTC') 2025-10-11 05:00:00  │ │
│  │ Unix Epoch: 1760155200000                         │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## 📚 Implementation Details

### Layer 1: Storage (Database)

**Rule:** ALL timestamps MUST be stored in UTC with timezone awareness.

#### PostgreSQL/TimescaleDB

```sql
-- ✅ CORRECT: Use TIMESTAMPTZ (timestamp with timezone)
CREATE TABLE market_ticks (
    symbol VARCHAR(20),
    timestamp_utc TIMESTAMPTZ NOT NULL,  -- Stores UTC, displays in client TZ
    price DECIMAL(18, 5),
    volume INT,
    created_at TIMESTAMPTZ DEFAULT NOW()  -- Automatically UTC
);

-- ❌ WRONG: Don't use TIMESTAMP (naive, no timezone)
CREATE TABLE market_ticks (
    timestamp TIMESTAMP  -- ❌ Ambiguous! What timezone?
);
```

#### ClickHouse

```sql
-- ✅ CORRECT: Use DateTime('UTC') with explicit timezone
CREATE TABLE aggregates (
    symbol String,
    timeframe String,
    timestamp DateTime('UTC'),  -- Explicit UTC timezone
    timestamp_ms Int64,         -- Unix epoch milliseconds
    open Float64,
    high Float64,
    low Float64,
    close Float64,
    volume UInt64
) ENGINE = ReplacingMergeTree(timestamp_ms)
ORDER BY (symbol, timeframe, timestamp);

-- ❌ WRONG: Don't use DateTime without timezone
CREATE TABLE aggregates (
    timestamp DateTime  -- ❌ Uses server timezone (ambiguous!)
);
```

#### Python Code

```python
from datetime import datetime, timezone

# ✅ CORRECT: Timezone-aware UTC datetime
utc_now = datetime.now(timezone.utc)
print(utc_now)  # 2025-10-11 05:00:00+00:00

# ✅ CORRECT: Convert Unix timestamp to UTC
timestamp_ms = 1760155200000
dt = datetime.fromtimestamp(timestamp_ms / 1000.0, tz=timezone.utc)
print(dt)  # 2025-10-11 05:00:00+00:00

# ❌ WRONG: Naive datetime (no timezone)
naive_now = datetime.now()  # ❌ Ambiguous timezone!
naive_ts = datetime.fromtimestamp(timestamp_ms / 1000.0)  # ❌ Uses local TZ!
```

---

### Layer 2: API Response

**Rule:** ALWAYS return BOTH UTC and Unix epoch. Client can localize if needed.

#### REST API Response Format

```json
{
    "symbol": "EUR/USD",
    "timeframe": "5m",
    "timestamp_utc": "2025-10-11T05:00:00.000Z",  // ISO 8601 with 'Z' suffix
    "timestamp_ms": 1760155200000,                // Unix epoch milliseconds
    "open": 1.0850,
    "high": 1.0855,
    "low": 1.0848,
    "close": 1.0852,
    "volume": 1250
}
```

#### Multi-Timezone API Response (Optional)

For tenant-specific APIs, return pre-localized timestamps:

```json
{
    "symbol": "EUR/USD",
    "timestamp_utc": "2025-10-11T05:00:00.000Z",
    "timestamp_wib": "2025-10-11T12:00:00.000+07:00",  // Indonesia
    "timestamp_est": "2025-10-11T01:00:00.000-04:00",  // New York
    "timestamp_gmtp2": "2025-10-11T07:00:00.000+02:00", // MT4 Broker
    "timestamp_ms": 1760155200000,
    "price": 1.0850
}
```

#### FastAPI Implementation

```python
from datetime import datetime, timezone
from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter()

@router.get("/candles/{symbol}")
async def get_candles(
    symbol: str,
    timeframe: str,
    client_timezone: str = Query("UTC", alias="tz"),
    start: Optional[int] = None,  # Unix timestamp
    end: Optional[int] = None
):
    """
    Get candlestick data with optional timezone localization

    Args:
        symbol: Trading pair (e.g., EUR/USD)
        timeframe: Candle timeframe (e.g., 5m, 1h)
        client_timezone: Client's preferred timezone (default: UTC)
            Examples: "UTC", "WIB", "EST", "Asia/Jakarta", "America/New_York"
        start: Start time (Unix timestamp ms)
        end: End time (Unix timestamp ms)

    Returns:
        JSON with timestamps in UTC + client timezone
    """
    # Fetch data from database (all stored in UTC)
    candles = await fetch_candles_from_db(symbol, timeframe, start, end)

    # Format response with multi-timezone support
    response = []
    for candle in candles:
        candle_data = {
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp_utc": TimezoneHandler.format_iso(candle['timestamp_utc']),
            "timestamp_ms": TimezoneHandler.to_unix_ms(candle['timestamp_utc']),
            "open": candle['open'],
            "high": candle['high'],
            "low": candle['low'],
            "close": candle['close'],
            "volume": candle['volume']
        }

        # Add localized timestamp if client specified
        if client_timezone != "UTC":
            localized_dt = TimezoneHandler.to_timezone(
                candle['timestamp_utc'],
                client_timezone
            )
            candle_data['timestamp_local'] = TimezoneHandler.format_iso(localized_dt)
            candle_data['timezone'] = client_timezone

        response.append(candle_data)

    return {
        "status": "success",
        "symbol": symbol,
        "timeframe": timeframe,
        "timezone": client_timezone,
        "count": len(response),
        "candles": response
    }
```

---

### Layer 3: Client Display

**Rule:** Client chooses display timezone. Never assume client's timezone on backend.

#### Frontend Example (React/TypeScript)

```typescript
// Utility function for timezone conversion
import { format, utcToZonedTime } from 'date-fns-tz';

interface Candle {
    timestamp_utc: string;  // ISO 8601
    timestamp_ms: number;   // Unix epoch
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
}

// User's timezone (from browser or profile settings)
const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;  // e.g., "Asia/Jakarta"

function displayCandleTime(candle: Candle): string {
    // Convert UTC timestamp to user's local timezone
    const utcDate = new Date(candle.timestamp_utc);
    const zonedDate = utcToZonedTime(utcDate, userTimezone);

    // Format for display
    return format(zonedDate, 'yyyy-MM-dd HH:mm:ss zzz', { timeZone: userTimezone });
    // Output: "2025-10-11 12:00:00 WIB"
}

// Chart display
function TradingChart({ candles }: { candles: Candle[] }) {
    return (
        <div>
            {candles.map(candle => (
                <div key={candle.timestamp_ms}>
                    <span>Time: {displayCandleTime(candle)}</span>
                    <span>Price: {candle.close}</span>
                </div>
            ))}
        </div>
    );
}
```

---

## 🛠️ TimezoneHandler Utility

We've created a comprehensive `TimezoneHandler` class to standardize all timezone operations:

**Location:** `/project3/backend/01-core-infrastructure/central-hub/shared/components/utils/timezone_handler.py`

### Key Methods

```python
from timezone_handler import TimezoneHandler

# Get current UTC time (timezone-aware)
now_utc = TimezoneHandler.now_utc()
# Output: datetime(2025, 10, 11, 5, 0, 0, tzinfo=timezone.utc)

# Convert any datetime to UTC
dt_utc = TimezoneHandler.to_utc("2025-10-11T12:00:00+07:00")
# Output: datetime(2025, 10, 11, 5, 0, 0, tzinfo=timezone.utc)

# Convert to specific timezone
dt_wib = TimezoneHandler.to_timezone(now_utc, "WIB")
# Output: datetime(2025, 10, 11, 12, 0, 0, tzinfo=ZoneInfo('Asia/Jakarta'))

# Get Unix timestamp (ms)
unix_ms = TimezoneHandler.to_unix_ms(now_utc)
# Output: 1760155200000

# Format to ISO 8601
iso_string = TimezoneHandler.format_iso(now_utc)
# Output: "2025-10-11T05:00:00.000Z"

# Multi-timezone API response
response = TimezoneHandler.create_multi_tz_response(
    now_utc,
    timezones=["UTC", "WIB", "EST", "GMT+2"]
)
# Output: {
#     "timestamp_ms": 1760155200000,
#     "timestamp_utc": "2025-10-11T05:00:00.000Z",
#     "timestamp_wib": "2025-10-11T12:00:00.000+07:00",
#     "timestamp_est": "2025-10-11T01:00:00.000-04:00",
#     "timestamp_gmtp2": "2025-10-11T07:00:00.000+02:00"
# }

# Trading hours conversion
open_utc, close_utc = TimezoneHandler.get_trading_hours_utc(
    "09:00", "16:00", "WIB"
)
# Indonesian market hours in UTC
# Output: (datetime(...02:00:00...), datetime(...09:00:00...))
```

### Supported Timezones

| Code | Timezone | UTC Offset | Usage |
|------|----------|------------|-------|
| **UTC** | UTC | +0:00 | Universal standard |
| **WIB** | Asia/Jakarta | +7:00 | Indonesia Western Time |
| **WITA** | Asia/Makassar | +8:00 | Indonesia Central Time |
| **WIT** | Asia/Jayapura | +9:00 | Indonesia Eastern Time |
| **SGT** | Asia/Singapore | +8:00 | Singapore |
| **HKT** | Asia/Hong_Kong | +8:00 | Hong Kong |
| **JST** | Asia/Tokyo | +9:00 | Japan |
| **GMT** | Europe/London | +0:00/+1:00 | UK (DST aware) |
| **CET** | Europe/Paris | +1:00/+2:00 | Central Europe |
| **EST** | America/New_York | -5:00/-4:00 | Eastern US (DST aware) |
| **GMT+2** | Etc/GMT-2 | +2:00 | Most MT4 brokers |
| **GMT+3** | Etc/GMT-3 | +3:00 | Some MT5 brokers |

---

## 📋 Best Practices

### ✅ DO's

1. **ALWAYS store timestamps in UTC**
   ```python
   # ✅ Correct
   timestamp_utc = datetime.now(timezone.utc)
   ```

2. **ALWAYS use timezone-aware datetime objects**
   ```python
   # ✅ Correct
   dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
   ```

3. **ALWAYS return both UTC and Unix epoch in API responses**
   ```json
   {
       "timestamp_utc": "2025-10-11T05:00:00.000Z",
       "timestamp_ms": 1760155200000
   }
   ```

4. **Use ISO 8601 format for string timestamps**
   ```
   2025-10-11T05:00:00.000Z  ✅ Correct (Z = UTC)
   2025-10-11T12:00:00+07:00 ✅ Correct (with timezone offset)
   ```

5. **Use Unix epoch (ms) for date calculations**
   ```python
   # ✅ Correct - timezone-agnostic
   time_diff_ms = end_timestamp_ms - start_timestamp_ms
   ```

### ❌ DON'Ts

1. **Never use naive datetime objects**
   ```python
   # ❌ WRONG - ambiguous timezone
   dt = datetime.now()
   dt = datetime.fromtimestamp(ts_ms / 1000.0)
   ```

2. **Never assume client's timezone**
   ```python
   # ❌ WRONG - server might be in different timezone
   local_time = datetime.now()
   ```

3. **Never use deprecated datetime.utcnow()**
   ```python
   # ❌ WRONG - returns naive datetime
   dt = datetime.utcnow()

   # ✅ CORRECT
   dt = datetime.now(timezone.utc)
   ```

4. **Never store timestamps without timezone**
   ```sql
   -- ❌ WRONG
   CREATE TABLE events (timestamp TIMESTAMP);

   -- ✅ CORRECT
   CREATE TABLE events (timestamp_utc TIMESTAMPTZ);
   ```

5. **Never hardcode timezone conversions**
   ```python
   # ❌ WRONG - breaks during DST transitions
   jakarta_time = utc_time + timedelta(hours=7)

   # ✅ CORRECT - handles DST automatically
   jakarta_time = TimezoneHandler.to_timezone(utc_time, "WIB")
   ```

---

## 🧪 Testing Strategy

### Unit Tests

```python
import pytest
from datetime import datetime, timezone
from timezone_handler import TimezoneHandler

def test_utc_conversion():
    """Test UTC conversion from various inputs"""
    # From ISO string
    dt = TimezoneHandler.to_utc("2025-10-11T12:00:00+07:00")
    assert dt.hour == 5  # 12:00 WIB = 05:00 UTC

    # From Unix timestamp
    dt = TimezoneHandler.to_utc(1760155200000)
    assert dt.year == 2025
    assert dt.month == 10
    assert dt.day == 11

    # From naive datetime
    naive_dt = datetime(2025, 10, 11, 12, 0, 0)
    dt = TimezoneHandler.to_utc(naive_dt, from_tz="WIB")
    assert dt.hour == 5

def test_timezone_localization():
    """Test timezone conversion"""
    utc_dt = datetime(2025, 10, 11, 5, 0, 0, tzinfo=timezone.utc)

    # Convert to WIB
    wib_dt = TimezoneHandler.to_timezone(utc_dt, "WIB")
    assert wib_dt.hour == 12

    # Convert to EST
    est_dt = TimezoneHandler.to_timezone(utc_dt, "EST")
    assert est_dt.hour == 1  # 05:00 UTC = 01:00 EST (standard time)

def test_multi_tz_response():
    """Test multi-timezone API response"""
    utc_dt = datetime(2025, 10, 11, 5, 0, 0, tzinfo=timezone.utc)
    response = TimezoneHandler.create_multi_tz_response(
        utc_dt,
        timezones=["UTC", "WIB", "EST"]
    )

    assert response['timestamp_ms'] == 1760155200000
    assert 'timestamp_utc' in response
    assert 'timestamp_wib' in response
    assert 'timestamp_est' in response
```

### Integration Tests

```python
async def test_candle_api_timezone():
    """Test candle API with timezone parameter"""
    response = await client.get(
        "/api/candles/EURUSD?timeframe=5m&tz=WIB"
    )

    assert response.status_code == 200
    data = response.json()

    # Verify UTC timestamp present
    assert 'timestamp_utc' in data['candles'][0]

    # Verify localized timestamp present
    assert 'timestamp_local' in data['candles'][0]
    assert data['timezone'] == 'WIB'

    # Verify Unix epoch present
    assert 'timestamp_ms' in data['candles'][0]
```

---

## 📊 Database Verification

### PostgreSQL/TimescaleDB

```sql
-- Check if timestamps are timezone-aware
SELECT
    column_name,
    data_type,
    datetime_precision
FROM information_schema.columns
WHERE table_name = 'market_ticks'
AND column_name LIKE '%time%';

-- Should show: timestamp with time zone

-- Verify data
SELECT
    symbol,
    timestamp_utc,
    timestamp_utc AT TIME ZONE 'Asia/Jakarta' as timestamp_wib,
    timestamp_utc AT TIME ZONE 'America/New_York' as timestamp_est
FROM market_ticks
LIMIT 5;
```

### ClickHouse

```sql
-- Check timezone setting
SELECT timezone(), now();

-- Should show: UTC

-- Check DateTime columns
DESCRIBE TABLE aggregates;

-- timestamp should be: DateTime('UTC')

-- Verify data
SELECT
    symbol,
    timestamp,
    toUnixTimestamp(timestamp) * 1000 as timestamp_ms,
    formatDateTime(timestamp, '%Y-%m-%d %H:%M:%S', 'UTC') as utc,
    formatDateTime(timestamp, '%Y-%m-%d %H:%M:%S', 'Asia/Jakarta') as wib
FROM aggregates
LIMIT 5;
```

---

## 🚀 Migration Guide

If you have existing data with naive timestamps:

### PostgreSQL Migration

```sql
-- Step 1: Add new timezone-aware column
ALTER TABLE market_ticks
ADD COLUMN timestamp_utc_new TIMESTAMPTZ;

-- Step 2: Migrate data (assuming old data was UTC)
UPDATE market_ticks
SET timestamp_utc_new = timestamp_utc AT TIME ZONE 'UTC';

-- Step 3: Drop old column
ALTER TABLE market_ticks
DROP COLUMN timestamp_utc;

-- Step 4: Rename new column
ALTER TABLE market_ticks
RENAME COLUMN timestamp_utc_new TO timestamp_utc;
```

### ClickHouse Migration

```sql
-- Step 1: Create new table with correct schema
CREATE TABLE aggregates_new (
    symbol String,
    timeframe String,
    timestamp DateTime('UTC'),  -- Explicit UTC
    timestamp_ms Int64,
    ...
) ENGINE = ReplacingMergeTree(timestamp_ms)
ORDER BY (symbol, timeframe, timestamp);

-- Step 2: Migrate data
INSERT INTO aggregates_new
SELECT * FROM aggregates;

-- Step 3: Swap tables
RENAME TABLE aggregates TO aggregates_old;
RENAME TABLE aggregates_new TO aggregates;

-- Step 4: Drop old table (after verification)
DROP TABLE aggregates_old;
```

---

## 📞 Support & Contact

For questions or issues related to timezone handling:

- **Documentation:** This guide
- **Code Reference:** `timezone_handler.py`
- **Database Schema:** See DDL files in `/scripts/migrations/`
- **API Examples:** See `/docs/API_EXAMPLES.md`

---

## 📝 Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-11 | Initial timezone standardization implementation |
|     |            | - Created TimezoneHandler utility class |
|     |            | - Fixed ClickHouse DateTime columns to UTC |
|     |            | - Updated clickhouse_writer.py to use timezone-aware datetimes |
|     |            | - Documented 3-layer timezone strategy |

---

**Document Status:** ✅ ACTIVE
**Review Date:** 2025-11-11
**Next Review:** Quarterly
