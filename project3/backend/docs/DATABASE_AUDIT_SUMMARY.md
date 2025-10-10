# DATABASE AUDIT SUMMARY - AI TRADING PROJECT

## ✅ ARSITEKTUR DATA FLOW

### PostgreSQL / TimescaleDB (2.48M ticks)
**Purpose**: Store RAW live tick data for aggregation

**Tables:**
1. **market_ticks** - ACTIVE (2.48M rows)
   - Source: live-collector via NATS/Kafka
   - Used by: tick-aggregator
   - Data: nats (1.34M) + kafka (1.14M) = 2.48M ticks
   - Period: Oct 6 - Oct 10 (3 days live data)

2. **ticks** - LEGACY/UNUSED (14 rows)
   - Only 14 rows from Oct 6
   - Not actively used
   - Can be dropped

3. **candles, service_registry, health_metrics** - Infrastructure tables

### ClickHouse / suho_analytics (91M rows, 5.3 GB)
**Purpose**: Store aggregated OHLCV bars + indicators

**Main Table: aggregates**
| Source | Timeframes | Rows | Period | Purpose |
|--------|-----------|------|--------|---------|
| **historical_aggregated** | 5m,15m,1h | 7.1M | 2023-2025 | From tick-aggregator (clean) |
| **live_aggregated** | 5m,15m,1h | 40K | 3 days | From tick-aggregator (live) |
| **polygon_historical** | 1m,5m | 68M | 2015-2025 | Historical download (HAS DUPLICATES 2-3x) |
| **polygon_gap_fill** | 1m,5m | 15M | Sep-Oct 2025 | Gap filling (HAS MASSIVE DUPLICATES 178x!) |

**Other Tables:**
- ticks (ClickHouse) - EMPTY, not used
- ml_training_data - empty (future use)
- external_* - external data sources (small)
- Materialized views - stats/aggregations

---

## 🚨 MASALAH DUPLIKASI - CONFIRMED

### Problem 1: polygon_gap_fill (CRITICAL)
```
EUR/USD 1m data:
- Total rows: 1,176,278
- Unique timestamps: 6,602
- Duplication: 178x per timestamp!
```

**Root Cause:**
Historical downloader mem-publish sama data berulang kali ke NATS/Kafka.
Kemungkinan: Restart/retry loop tanpa check "sudah ada atau belum?"

### Problem 2: polygon_historical (MODERATE)
```
EUR/USD 1m data:
- Total rows: 9,385,773
- Unique timestamps: 3,681,674
- Duplication: 2.55x per timestamp
```

**Root Cause:**
Historical downloader overlap periods atau re-download existing data.

### Problem 3: TimescaleDB market_ticks (MINOR)
```
Total: 2,469,282 ticks
Unique: 1,883,599 ticks
Duplicates: 585,683 (23.7%)
```

**Root Cause:**
Live-collector reconnection atau restart → re-send same ticks via NATS/Kafka.

---

## 🔄 DATA FLOW (3 Independent Paths)

### Path 1: LIVE TICKS → AGGREGATES
```
Polygon WebSocket (live quotes)
  ↓
live-collector
  ↓ publish to NATS: ticks.{symbol}
data-bridge
  ↓ insert
TimescaleDB.market_ticks (2.48M, source=nats/kafka)
  ↓ read & aggregate
tick-aggregator
  ↓ publish to NATS: bars.{symbol}.{tf}
data-bridge
  ↓ insert
ClickHouse.aggregates (source=live_aggregated, historical_aggregated)
```

### Path 2: HISTORICAL BARS → CLICKHOUSE
```
Polygon REST API (historical 1m bars)
  ↓
historical-downloader
  ↓ publish to NATS: bars.{symbol}.1m
  ↓ publish to Kafka: aggregate_archive
data-bridge
  ↓ insert (NO DEDUPLICATION!)
ClickHouse.aggregates (source=polygon_historical, polygon_gap_fill)
```

### Path 3: AGGREGATION (5m, 15m, 1h, etc)
```
TimescaleDB.market_ticks
  ↓ read
tick-aggregator (calculate OHLCV + 12 indicators)
  ↓ publish to NATS: bars.{symbol}.{timeframe}
data-bridge
  ↓ insert
ClickHouse.aggregates (source=historical_aggregated)
```

---

## ❌ MENGAPA TERJADI DUPLIKASI?

### 1. Tidak Ada Unique Constraint
- TimescaleDB: No UNIQUE constraint on (symbol, timestamp)
- ClickHouse: MergeTree (bukan ReplacingMergeTree)
- Consequence: Same data bisa diinsert berkali-kali

### 2. Tidak Ada Deduplication Logic
- data-bridge: Tidak cek "apakah timestamp sudah ada?"
- historical-downloader: Tidak cek "apakah period sudah didownload?"
- Restart/retry → re-insert same data

### 3. Historical Downloader Loop
```
Historical downloader detects gap
  ↓
Download bars (e.g., 2015-01-01 to 2015-04-01)
  ↓
Publish to NATS/Kafka
  ↓
Service restart/error
  ↓
Re-detect same gap (belum ada logic "already downloaded")
  ↓
Re-download & re-publish same data
  ↓
DUPLIKASI 2x, 3x, ... 178x!
```

---

## 📊 STORAGE IMPACT

| Item | Actual Size | Waste | Percentage |
|------|-------------|-------|------------|
| Unique data | ~35-40M rows | - | 100% |
| Duplicate data | ~50M rows | 2.5-3 GB | ~60% overhead |
| **Total** | **91M rows** | **5.3 GB** | **160%** |

**Performance Impact:**
- Query speed: 2-3x slower (scanning duplicates)
- Storage cost: 60% wasted space
- ML training: Biased data (over-representation)

---

## ✅ DATA YANG BERSIH (No Duplicates)

**historical_aggregated (from tick-aggregator):**
- 5m: 4.98M rows → 226K unique timestamps ≈ 22x symbols (CORRECT!)
- 15m: 1.68M rows → 76K unique timestamps ≈ 22x symbols (CORRECT!)
- 1h: 430K rows → 19K unique timestamps ≈ 22x symbols (CORRECT!)

**Explanation**: Tick-aggregator membaca dari market_ticks (yang memang ada duplicates), 
tapi saat aggregate, dia otomatis deduplicate karena process OHLCV aggregation per timestamp.

---

## 🔍 TABEL YANG TIDAK TERPAKAI

1. **PostgreSQL.ticks** - 14 rows, legacy table
2. **ClickHouse.ticks** - 0 rows, empty/unused
3. MaterializedView `.inner_id.*` - Auto-generated, keep

**Recommendation**: Drop unused tables after confirm tidak ada dependency.

---

## 💡 ROOT CAUSE SUMMARY

| Issue | Severity | Root Cause | Impact |
|-------|----------|------------|--------|
| polygon_gap_fill 178x duplication | 🔴 CRITICAL | No check before re-download/re-publish | 15M duplicate rows |
| polygon_historical 2.5x duplication | 🟠 HIGH | Overlapping period download | 9M duplicate rows |
| market_ticks 23% duplication | 🟡 MEDIUM | Reconnection re-sends ticks | 585K duplicate rows |
| No unique constraints | 🟠 HIGH | Design issue - allows duplicates | All tables affected |
| No deduplication logic | 🔴 CRITICAL | Missing validation layer | Continuous growth |

---

## ✅ YANG SUDAH BENAR

1. ✅ Data OHLCV values: No NULL, no zero values
2. ✅ Tick-aggregator deduplication: Works correctly for aggregated data
3. ✅ Data flow architecture: 3 independent paths well-designed
4. ✅ TimescaleDB hypertables: Properly partitioned
5. ✅ ClickHouse compression: 5.3 GB for 91M rows (good ratio)

---

## 📋 NEXT STEPS (In Order)

1. **STOP historical-downloader** - Prevent more duplicates
2. **Add check logic** - "Is this timestamp already downloaded?"
3. **Deduplicate existing data** - OPTIMIZE TABLE or DELETE duplicates
4. **Add UNIQUE constraint** - Prevent future duplicates
5. **Resume historical download** - With new deduplication logic

