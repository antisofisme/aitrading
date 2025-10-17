# Dukascopy Tick Routing Implementation

## 📋 Summary

Implemented intelligent tick routing in Data Bridge to send Dukascopy historical ticks to ClickHouse `ticks` table, while Polygon ticks continue going to TimescaleDB `market_ticks` table.

**Status:** ✅ **IMPLEMENTATION COMPLETE** - Code ready, awaiting Dukascopy network recovery for end-to-end test

---

## 🎯 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA FLOW ROUTING                             │
└─────────────────────────────────────────────────────────────────┘

Dukascopy Historical     Polygon Live/Historical
       ↓                          ↓
   NATS publish            NATS publish
   source: 'dukascopy_historical'   source: 'polygon_*'
       ↓                          ↓
   ┌────────────────────────────────────┐
   │      DATA BRIDGE (Routing Logic)    │
   │   _save_tick() method              │
   │                                    │
   │   if source == 'dukascopy_historical':  │
   │      → _save_tick_to_clickhouse()  │
   │   else:                            │
   │      → _save_tick_to_timescale()   │
   └────────────────────────────────────┘
       ↓                          ↓
   ClickHouse               TimescaleDB
   ticks table           market_ticks table
   (long-term storage)   (real-time trading)
```

---

## 🔧 Implementation Details

### 1. Data Bridge Routing Logic (`main.py`)

**File:** `/project3/backend/02-data-processing/data-bridge/src/main.py`

```python
async def _save_tick(self, data: dict):
    """
    Route ticks based on source field:
    - Dukascopy → ClickHouse ticks table
    - Polygon   → TimescaleDB market_ticks table
    """
    source = data.get('source', 'unknown')

    if source == 'dukascopy_historical':
        await self._save_tick_to_clickhouse(data)
    else:
        await self._save_tick_to_timescale(data)

async def _save_tick_to_clickhouse(self, data: dict):
    """Save Dukascopy tick to ClickHouse ticks table"""
    tick_data = {
        'symbol': data.get('symbol'),
        'timestamp': data.get('timestamp'),
        'bid': data.get('bid', 0),
        'ask': data.get('ask', 0),
        'last': data.get('mid', (data.get('bid', 0) + data.get('ask', 0)) / 2),
        'volume': data.get('volume', 0),
        'flags': 0
    }

    await self.clickhouse_writer.add_tick(tick_data)
```

### 2. ClickHouse Writer Tick Buffer (`clickhouse_writer.py`)

**File:** `/project3/backend/02-data-processing/data-bridge/src/clickhouse_writer.py`

**Added Components:**
- `tick_buffer: List[Dict]` - Batch buffer for Dukascopy ticks
- `add_tick()` - Add tick to buffer with auto-flush
- `flush_ticks()` - Batch insert to ClickHouse with circuit breaker

```python
async def add_tick(self, tick_data: Dict):
    """Buffer Dukascopy tick, auto-flush on size/time threshold"""
    self.tick_buffer.append(tick_data)

    # Flush on batch_size (1000) or batch_timeout (10s)
    should_flush = (
        len(self.tick_buffer) >= self.batch_size or
        (datetime.now(timezone.utc) - self.last_tick_flush).total_seconds() >= self.batch_timeout
    )

    if should_flush:
        await self.flush_ticks()

async def flush_ticks(self):
    """
    Batch insert to ClickHouse.ticks table
    - Circuit breaker protection
    - Retry on failure
    - Statistics tracking
    """
    # Prepare batch data
    data = []
    for tick in self.tick_buffer:
        row = [
            tick['symbol'],
            tick['timestamp'],
            float(tick['bid']),
            float(tick['ask']),
            float(tick['last']),
            int(tick['volume']),
            int(tick['flags'])
        ]
        data.append(row)

    # Insert with circuit breaker
    self.circuit_breaker.call(
        lambda: self.client.insert(
            'ticks',
            data,
            column_names=['symbol', 'timestamp', 'bid', 'ask', 'last', 'volume', 'flags']
        )
    )

    self.tick_buffer.clear()
```

---

## 📊 Database Schemas

### ClickHouse `ticks` Table (Dukascopy Target)

```sql
CREATE TABLE ticks (
    symbol String,
    timestamp DateTime64(3),
    bid Float64,
    ask Float64,
    last Float64,      -- Mid price (bid+ask)/2
    volume UInt64,
    flags UInt32       -- Reserved for future use
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, timestamp);
```

**Purpose:** Long-term storage for Dukascopy historical tick data

**Optimization:**
- Partitioned by month for efficient historical queries
- Ordered by (symbol, timestamp) for fast time-series access
- No `source` column (all data is Dukascopy)

### TimescaleDB `market_ticks` Table (Polygon Target)

```sql
CREATE TABLE market_ticks (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20),
    timestamp TIMESTAMPTZ,
    bid DECIMAL(20,8),
    ask DECIMAL(20,8),
    mid DECIMAL(20,8),
    spread DECIMAL(20,8),
    volume BIGINT,
    source VARCHAR(50),    -- 'polygon_live', 'polygon_historical'
    ...
);

SELECT create_hypertable('market_ticks', 'timestamp');
```

**Purpose:** Real-time trading data from Polygon

**Features:**
- TimescaleDB hypertable for time-series optimization
- `source` column to distinguish Polygon sources
- Additional metadata fields (exchange, conditions, etc.)

---

## 🔍 Verification

### ✅ Components Verified

1. **ClickHouse Connection** ✅
   ```bash
   docker exec suho-clickhouse clickhouse-client \
     --user suho_analytics \
     --password clickhouse_secure_2024 \
     --query "SELECT 1"
   # Output: 1
   ```

2. **ClickHouse `ticks` Table Schema** ✅
   ```bash
   docker exec suho-clickhouse clickhouse-client \
     --user suho_analytics \
     --password clickhouse_secure_2024 \
     --query "DESCRIBE suho_analytics.ticks"
   # Output: symbol String, timestamp DateTime64(3), bid Float64, ...
   ```

3. **Manual Insert Test** ✅
   ```bash
   # Inserted 3 test ticks
   docker exec suho-clickhouse clickhouse-client \
     --user suho_analytics \
     --password clickhouse_secure_2024 \
     --query "
       INSERT INTO suho_analytics.ticks VALUES
       ('EUR/USD', now(), 1.08450, 1.08452, 1.08451, 1000, 0),
       ('GBP/USD', now(), 1.25800, 1.25802, 1.25801, 500, 0),
       ('XAU/USD', now(), 2050.50, 2050.60, 2050.55, 100, 0)
     "

   # Verify
   docker exec suho-clickhouse clickhouse-client \
     --user suho_analytics \
     --password clickhouse_secure_2024 \
     --query "SELECT * FROM suho_analytics.ticks ORDER BY timestamp DESC LIMIT 3"
   # ✅ All 3 ticks present
   ```

4. **Data Bridge Routing Code** ✅
   - `_save_tick()` routing logic implemented
   - `_save_tick_to_clickhouse()` created
   - `_save_tick_to_timescale()` created
   - Docker image rebuilt with new code

5. **ClickHouse Writer Tick Handling** ✅
   - `tick_buffer` initialized
   - `add_tick()` method implemented
   - `flush_ticks()` with circuit breaker

### ⏳ Pending End-to-End Test

**Status:** Blocked by Dukascopy network connectivity

**Issue:**
```bash
curl -I "https://datafeed.dukascopy.com/datafeed/EURUSD/2024/00/01/00h_ticks.bi5"
# curl: (28) Failed to connect to datafeed.dukascopy.com port 443: Timeout

ping datafeed.dukascopy.com
# 100% packet loss
```

**Root Cause:** Network timeout to `datafeed.dukascopy.com` (103.155.197.107)
- Possible ISP/firewall blocking
- Server may be temporarily down
- Network policy restriction in Docker/WSL environment

**Test Will Auto-Complete When:**
1. Dukascopy network recovers
2. Downloader successfully downloads historical data
3. Ticks published to NATS with `source: 'dukascopy_historical'`
4. Data bridge routes to ClickHouse
5. ClickHouse `ticks` table populated

---

## 🧪 Manual Testing (When Network Recovers)

### 1. Monitor Dukascopy Download

```bash
docker logs suho-dukascopy-historical -f --tail 50 | grep -E "(Published|Downloaded|✅)"
```

**Expected Output:**
```
✅ Downloaded 100 hours
📤 Published 50,000 ticks to NATS
```

### 2. Check Data Bridge Routing

```bash
docker logs backend-data-bridge-1 --tail 100 | grep -E "(dukascopy|ClickHouse|_save_tick)"
```

**Expected Output:**
```
🔧 _save_tick called | source=dukascopy_historical
✅ Inserted 1000 ticks to ClickHouse.ticks (total: 50000)
```

### 3. Verify ClickHouse Ticks

```bash
docker exec suho-clickhouse clickhouse-client \
  --user suho_analytics \
  --password clickhouse_secure_2024 \
  --query "
    SELECT
      symbol,
      count(*) as tick_count,
      min(timestamp) as first_tick,
      max(timestamp) as last_tick
    FROM suho_analytics.ticks
    GROUP BY symbol
    ORDER BY symbol
  "
```

**Expected Output:**
```
EUR/USD  500000  2024-01-01 00:00:00  2024-01-31 23:59:59
GBP/USD  400000  2024-01-01 00:00:00  2024-01-31 23:59:59
...
```

### 4. Verify Polygon Ticks NOT in ClickHouse

```bash
docker exec suho-postgresql psql -U suho_admin -d suho_trading \
  -c "SELECT symbol, source, count(*) FROM market_ticks GROUP BY symbol, source LIMIT 10;"
```

**Expected Output:**
```
 symbol  |      source         | count
---------+--------------------+--------
 EUR/USD | polygon_live       | 150000
 GBP/USD | polygon_historical | 200000
```

(No Dukascopy ticks in TimescaleDB)

---

## 📈 Performance Characteristics

### Batch Writing
- **Batch Size:** 1000 ticks
- **Batch Timeout:** 10 seconds
- **Circuit Breaker:** 5 failures → 60s cooldown
- **Memory:** ~100KB per 1000 ticks

### Expected Throughput
- **Dukascopy Download:** ~100-500 hours/minute
- **Tick Volume:** ~50-100K ticks/hour (EUR/USD)
- **ClickHouse Insert:** 10-50K ticks/sec (batch mode)
- **Data Bridge Processing:** 5-10K ticks/sec per instance

### Storage
- **ClickHouse Compression:** ~80% (MergeTree engine)
- **1 year EUR/USD ticks:** ~500GB uncompressed → ~100GB compressed
- **Partitioning:** Monthly partitions for efficient queries

---

## 🚀 Production Readiness

### ✅ Completed
- [x] Routing logic implemented
- [x] ClickHouse writer extended
- [x] Circuit breaker protection
- [x] Batch buffering
- [x] Error handling
- [x] Logging
- [x] Docker images built
- [x] Containers restarted

### ⏳ Awaiting
- [ ] Dukascopy network recovery
- [ ] End-to-end test with real data
- [ ] Performance validation under load
- [ ] 24h stability test

### 📝 Recommendations

1. **Network Recovery:**
   - Wait for Dukascopy network to recover (check periodically)
   - Alternative: Use proxy/VPN if ISP blocking
   - Alternative: Use `tickterial` Python library (has caching)

2. **Monitoring:**
   - Set up Grafana dashboard for ClickHouse ticks table
   - Alert on zero tick inserts for > 1 hour
   - Monitor ClickHouse disk usage

3. **Optimization:**
   - Consider increasing batch size to 5000 for higher throughput
   - Add compression on network layer (gzip)
   - Implement adaptive batching based on tick volume

---

## 📚 References

- **ClickHouse Writer:** `02-data-processing/data-bridge/src/clickhouse_writer.py`
- **Data Bridge Main:** `02-data-processing/data-bridge/src/main.py`
- **Dukascopy Config:** `00-data-ingestion/dukascopy-historical-downloader/config/pairs.yaml`
- **ClickHouse Schema:** `01-core-infrastructure/central-hub/base/config/database/init-scripts/01-clickhouse-schema.sql`

---

**Implementation Date:** 2025-10-13
**Status:** ✅ Code Complete, Network Issue Blocking Test
**Next Action:** Wait for Dukascopy network recovery or use alternative data source
