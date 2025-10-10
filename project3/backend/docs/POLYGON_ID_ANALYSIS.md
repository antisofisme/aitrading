# POLYGON API ID ANALYSIS & DEDUPLICATION STRATEGY

## ❌ POLYGON TIDAK MEMBERIKAN UNIQUE ID

### Polygon API Response Structure:
```json
{
  "v": 77,          // volume
  "vw": 1.1727,     // volume weighted average price
  "o": 1.17253,     // open
  "c": 1.17266,     // close
  "h": 1.1727,      // high
  "l": 1.17253,     // low
  "t": 1757894400000, // timestamp (milliseconds) - ONLY IDENTIFIER!
  "n": 77           // number of items
}
```

**TIDAK ADA FIELD:**
- ❌ `id`
- ❌ `message_id`
- ❌ `uid`
- ❌ `bar_id`

## 🎯 COMPOSITE KEY (YANG BENAR)

**Yang membuat sebuah bar UNIQUE:**
```
Composite Key = Symbol + Timeframe + Timestamp

Example:
  EUR/USD + 1m + 1757894400000 = Unique bar
```

**Di Database ClickHouse:**
```sql
ORDER BY (symbol, timeframe, timestamp)
```

**Problem:** 
- MergeTree `ORDER BY` ≠ `UNIQUE` constraint
- MergeTree **ALLOWS** multiple rows dengan sama (symbol, timeframe, timestamp)
- Result: Duplikasi 178x!

---

## 🔧 3 SOLUSI AVAILABLE

### Option 1: ReplacingMergeTree (BEST)
**How it works:**
```sql
ENGINE = ReplacingMergeTree(ingested_at)
ORDER BY (symbol, timeframe, timestamp)
```

**Behavior:**
- Auto-deduplicate rows dengan sama `ORDER BY` key
- Keep row dengan `ingested_at` terbaru
- Happens during `OPTIMIZE TABLE FINAL` atau background merge

**Pros:**
- ✅ No code changes needed
- ✅ Automatic deduplication
- ✅ Query correct data: `SELECT ... FROM table FINAL`

**Cons:**
- ⚠️ Need `OPTIMIZE TABLE FINAL` to apply (or wait for background merge)
- ⚠️ Query needs `FINAL` keyword for guaranteed unique results

---

### Option 2: Application-Level Deduplication

**data-bridge: Check before INSERT**
```python
async def insert_aggregate(self, aggregate):
    # Check if exists
    existing = await clickhouse.query(f"""
        SELECT COUNT(*) 
        FROM aggregates 
        WHERE symbol = '{aggregate['symbol']}'
          AND timeframe = '{aggregate['timeframe']}'
          AND timestamp = '{aggregate['timestamp']}'
    """)
    
    if existing[0][0] == 0:
        # Not exists, safe to insert
        await clickhouse.insert('aggregates', aggregate)
    else:
        logger.debug(f"Skip duplicate: {aggregate['symbol']} {aggregate['timestamp']}")
```

**Pros:**
- ✅ Prevent duplicates at source
- ✅ No database schema change

**Cons:**
- ❌ Extra query per insert (performance hit)
- ❌ Race condition possible (concurrent inserts)
- ❌ More code to maintain

---

### Option 3: Historical Downloader - Smart Gap Detection

**Better gap detection:**
```python
# Instead of just MIN/MAX check:
existing_timestamps = clickhouse.query(f"""
    SELECT DISTINCT timestamp 
    FROM aggregates 
    WHERE symbol = '{symbol}'
      AND timeframe = '1m'
      AND timestamp BETWEEN '{start}' AND '{end}'
""")

# Download only MISSING timestamps
missing_timestamps = all_expected_timestamps - existing_timestamps
download(missing_timestamps)
```

**Pros:**
- ✅ Download only what's needed
- ✅ No re-download

**Cons:**
- ❌ Expensive for large time ranges
- ❌ Complex logic
- ❌ Still need database-level dedup (Option 1 or 2)

---

## 📊 COMPARISON

| Solution | Dedup Effectiveness | Performance | Complexity | Recommended |
|----------|-------------------|-------------|------------|-------------|
| ReplacingMergeTree | 🟢 Excellent | 🟢 Good | 🟢 Low | ✅ YES |
| App-level check | 🟡 Good | 🔴 Poor | 🟡 Medium | ⚠️ Optional |
| Smart gap detection | 🟡 Preventive | 🟡 Medium | 🔴 High | ⚠️ Optional |

---

## ✅ RECOMMENDED APPROACH

**Kombinasi Option 1 + Option 3 (Light Version):**

1. **ClickHouse: ReplacingMergeTree**
   ```sql
   ENGINE = ReplacingMergeTree(ingested_at)
   ORDER BY (symbol, timeframe, timestamp)
   ```
   - Auto-deduplicate duplicates
   - Keep latest data

2. **Historical Downloader: Track Downloaded Periods**
   ```python
   # Simple tracking file: downloaded_periods.json
   {
     "EUR/USD_1m": [
       {"start": "2015-01-01", "end": "2025-10-10", "downloaded_at": "2025-10-08"}
     ]
   }
   
   # Before download, check:
   if period_already_downloaded(symbol, timeframe, start, end):
       logger.info("Period already downloaded, SKIP")
       return
   ```
   - Prevent re-download of same periods
   - Simple file-based tracking

3. **Regular OPTIMIZE (Cron Job)**
   ```bash
   # Run daily
   clickhouse-client --query "OPTIMIZE TABLE aggregates FINAL"
   ```
   - Apply deduplication
   - Reclaim storage

---

## 🎯 IMPLEMENTATION SUMMARY

**Why Polygon doesn't provide ID:**
- They assume: (ticker + timestamp) = unique bar
- Up to consumer to deduplicate

**What we should do:**
1. ✅ Use composite key: (symbol, timeframe, timestamp)
2. ✅ Change to ReplacingMergeTree
3. ✅ Add simple period tracking in historical downloader
4. ✅ Run periodic OPTIMIZE

**Expected Results:**
- Storage: 91M rows → ~35M rows (60% reduction)
- Query speed: 2-3x faster
- No more duplicates in future

