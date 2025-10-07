# Storage Calculation for 5 Years ML Training Data

**Date:** 2025-10-06
**Scope:** ClickHouse aggregates + external data + ML training data
**Duration:** 5 years (2020-2025)

---

## 📊 **DATA SOURCES BREAKDOWN**

### **1. AGGREGATES TABLE (with 26 indicators)**

**Configuration:**
- 10 pairs (EURUSD, GBPUSD, XAUUSD, etc.)
- 7 timeframes (5m, 15m, 30m, 1h, 4h, 1d, 1w)
- 26 technical indicators per candle (stored as JSON)

#### **Rows Calculation:**

**Per Pair, Per Timeframe, Per Year:**
```
5m  timeframe: 288 candles/day × 365 days = 105,120 rows/year
15m timeframe: 96 candles/day × 365 days = 35,040 rows/year
30m timeframe: 48 candles/day × 365 days = 17,520 rows/year
1h  timeframe: 24 candles/day × 365 days = 8,760 rows/year
4h  timeframe: 6 candles/day × 365 days = 2,190 rows/year
1d  timeframe: 1 candle/day × 365 days = 365 rows/year
1w  timeframe: 52 weeks/year = 52 rows/year
───────────────────────────────────────────────────────
Total per pair: 169,047 rows/year
```

**All Pairs:**
```
10 pairs × 169,047 rows/pair/year = 1,690,470 rows/year
```

**5 Years:**
```
1,690,470 rows/year × 5 years = 8,452,350 rows total
```

#### **Storage Size Calculation:**

**Per Row (Uncompressed):**
```
Column              Type            Size
─────────────────────────────────────────
symbol              String          8 bytes
timeframe           String          4 bytes
timestamp           DateTime64      8 bytes
timestamp_ms        UInt64          8 bytes
open                Decimal(18,5)   8 bytes
high                Decimal(18,5)   8 bytes
low                 Decimal(18,5)   8 bytes
close               Decimal(18,5)   8 bytes
volume              UInt64          8 bytes
vwap                Decimal(18,5)   8 bytes
range_pips          Decimal(10,5)   8 bytes
body_pips           Decimal(10,5)   8 bytes
start_time          DateTime64      8 bytes
end_time            DateTime64      8 bytes
source              String          20 bytes
event_type          String          8 bytes
indicators          String (JSON)   ~500 bytes ⚠️ LARGEST!
ingested_at         DateTime64      8 bytes
─────────────────────────────────────────
TOTAL PER ROW:                      ~644 bytes
```

**Total Uncompressed Size:**
```
8,452,350 rows × 644 bytes = 5.44 GB
```

**ClickHouse Compression:**
- **Best case (100x compression):** 54 MB
- **Realistic (20x compression):** 272 MB ✅ **MOST LIKELY**
- **Worst case (10x compression):** 544 MB

**Estimated Aggregates Storage (5 years): 272 MB - 544 MB**

---

### **2. EXTERNAL DATA TABLES (6 tables)**

#### **Table 1: Economic Calendar**

**Update Frequency:** Hourly
**Rows per year:**
```
~100 events/day × 365 days = 36,500 rows/year
5 years = 182,500 rows
```

**Size per row:** ~200 bytes (date, time, currency, event, forecast, previous, actual, impact)

**Storage:**
```
Uncompressed: 182,500 × 200 = 36.5 MB
Compressed (20x): 1.8 MB
```

#### **Table 2: FRED Economic Indicators**

**Update Frequency:** Every 4 hours
**Rows per year:**
```
7 indicators × 6 updates/day = 42 rows/day
42 × 365 = 15,330 rows/year
5 years = 76,650 rows
```

**Size per row:** ~100 bytes (series_id, value, observation_date)

**Storage:**
```
Uncompressed: 76,650 × 100 = 7.7 MB
Compressed (20x): 385 KB
```

#### **Table 3: Crypto Sentiment**

**Update Frequency:** Every 30 minutes
**Rows per year:**
```
5 coins × 48 updates/day = 240 rows/day
240 × 365 = 87,600 rows/year
5 years = 438,000 rows
```

**Size per row:** ~150 bytes (coin_id, price, sentiment, social metrics)

**Storage:**
```
Uncompressed: 438,000 × 150 = 65.7 MB
Compressed (20x): 3.3 MB
```

#### **Table 4: Fear & Greed Index**

**Update Frequency:** Hourly
**Rows per year:**
```
24 updates/day × 365 days = 8,760 rows/year
5 years = 43,800 rows
```

**Size per row:** ~100 bytes (value, classification, sentiment_score)

**Storage:**
```
Uncompressed: 43,800 × 100 = 4.4 MB
Compressed (20x): 220 KB
```

#### **Table 5: Commodity Prices**

**Update Frequency:** Every 30 minutes
**Rows per year:**
```
5 commodities × 48 updates/day = 240 rows/day
240 × 365 = 87,600 rows/year
5 years = 438,000 rows
```

**Size per row:** ~150 bytes (symbol, price, change, volume)

**Storage:**
```
Uncompressed: 438,000 × 150 = 65.7 MB
Compressed (20x): 3.3 MB
```

#### **Table 6: Market Sessions**

**Update Frequency:** Every 5 minutes
**Rows per year:**
```
288 updates/day × 365 days = 105,120 rows/year
5 years = 525,600 rows
```

**Size per row:** ~100 bytes (utc_time, active_sessions, liquidity_level)

**Storage:**
```
Uncompressed: 525,600 × 100 = 52.6 MB
Compressed (20x): 2.6 MB
```

**Estimated External Data Storage (5 years): ~11.5 MB**

---

### **3. ML_TRAINING_DATA TABLE (Feature Engineering Result)**

**Configuration:**
- 10 pairs
- 3 main timeframes for ML training (1h, 4h, 1d)
- 70-90 features per row (estimate: 80 features avg)

#### **Rows Calculation:**

**Per Pair, Per Year:**
```
1h timeframe: 24 × 365 = 8,760 rows/year
4h timeframe: 6 × 365 = 2,190 rows/year
1d timeframe: 1 × 365 = 365 rows/year
───────────────────────────────────────
Total: 11,315 rows/year per pair
```

**All Pairs:**
```
10 pairs × 11,315 = 113,150 rows/year
5 years = 565,750 rows
```

#### **Storage Size Calculation:**

**Per Row (Uncompressed):**
```
Component                   Size
───────────────────────────────────
Metadata (10 columns)       80 bytes
OHLCV (5 columns)          40 bytes
Technical indicators (26)   208 bytes
External features (10)      80 bytes
Lag features (20)          160 bytes
Cross-pair features (10)    80 bytes
Volatility features (8)     64 bytes
Volume features (5)         40 bytes
Target variables (3)        24 bytes
───────────────────────────────────
TOTAL PER ROW:             ~776 bytes
```

**Total Uncompressed Size:**
```
565,750 rows × 776 bytes = 439 MB
```

**ClickHouse Compression:**
```
Compressed (20x): 22 MB
```

**Estimated ML Training Data Storage (5 years): ~22 MB**

---

## 💾 **TOTAL STORAGE SUMMARY**

### **Per Data Source (5 Years):**

| Data Source | Rows | Uncompressed | Compressed (20x) |
|-------------|------|--------------|------------------|
| **Aggregates** (OHLCV + indicators) | 8,452,350 | 5.44 GB | **272-544 MB** |
| **Economic Calendar** | 182,500 | 36.5 MB | 1.8 MB |
| **FRED Economic** | 76,650 | 7.7 MB | 385 KB |
| **Crypto Sentiment** | 438,000 | 65.7 MB | 3.3 MB |
| **Fear & Greed Index** | 43,800 | 4.4 MB | 220 KB |
| **Commodity Prices** | 438,000 | 65.7 MB | 3.3 MB |
| **Market Sessions** | 525,600 | 52.6 MB | 2.6 MB |
| **ML Training Data** | 565,750 | 439 MB | 22 MB |

### **TOTAL (Compressed):**
```
Aggregates:        272-544 MB  (main storage)
External Data:     11.5 MB     (supporting data)
ML Training Data:  22 MB       (engineered features)
────────────────────────────────────────
SUBTOTAL:          305-577 MB

Indexes:           ~50-100 MB  (estimated)
Materialized Views: ~20-50 MB  (estimated)
Overhead:          ~50 MB      (metadata, logs)
────────────────────────────────────────
GRAND TOTAL:       425-777 MB
```

### **🎯 REALISTIC ESTIMATE: 500 MB - 1 GB for 5 Years**

---

## 📈 **GROWTH PROJECTIONS**

### **Per Year Growth:**
```
Year 1: ~100-155 MB
Year 2: ~200-310 MB
Year 3: ~300-465 MB
Year 4: ~400-620 MB
Year 5: ~500-775 MB
```

### **Storage by Retention Policy:**

**Option 1: Keep All 5 Years**
- Total: ~500 MB - 1 GB
- Good for: Long-term backtesting, model retraining

**Option 2: Keep 2 Years (TTL policy)**
- Total: ~200 - 400 MB
- Good for: Active trading, recent pattern analysis

**Option 3: Keep 1 Year (Aggressive TTL)**
- Total: ~100 - 200 MB
- Good for: Live trading only, minimal storage

---

## 💡 **OPTIMIZATION STRATEGIES**

### **1. Timeframe Selection (Storage Saver)**

**Current: 7 timeframes (5m, 15m, 30m, 1h, 4h, 1d, 1w)**
- Storage: 272-544 MB (5 years)

**Option A: Only trade timeframes (1h, 4h, 1d)**
- Rows reduction: 169,047 → 11,315 per pair/year (-93%)
- Storage: 18-36 MB (5 years) ✅ **95% savings!**

**Option B: Only intraday (5m, 15m, 1h)**
- Rows reduction: 169,047 → 148,920 per pair/year (-12%)
- Storage: 240-480 MB (5 years) ✅ **12% savings**

### **2. Pair Selection (Storage Saver)**

**Current: 10 pairs**
- Storage: 272-544 MB (5 years)

**Option A: Focus on 5 major pairs (EURUSD, GBPUSD, USDJPY, XAUUSD, AUDUSD)**
- Storage: 136-272 MB (5 years) ✅ **50% savings**

**Option B: Single pair strategy (EURUSD only)**
- Storage: 27-54 MB (5 years) ✅ **90% savings**

### **3. Indicator Reduction (Storage Saver)**

**Current: 26 indicators (~500 bytes JSON)**
- Row size: 644 bytes
- Storage: 272-544 MB (5 years)

**Option A: Essential 10 indicators only**
- Row size: ~300 bytes (-53%)
- Storage: 128-256 MB (5 years) ✅ **53% savings**

**Option B: No indicators (calculate on-demand)**
- Row size: 144 bytes (-78%)
- Storage: 60-120 MB (5 years) ✅ **78% savings**
- Trade-off: Slower queries (calculate indicators at query time)

---

## 🔍 **COMPARISON WITH OTHER SYSTEMS**

### **Storage Comparison:**

| System | 5 Years Storage | Technology |
|--------|-----------------|------------|
| **Our System** | **500 MB - 1 GB** | ClickHouse (20x compression) |
| Traditional SQL (PostgreSQL) | 5-10 GB | Minimal compression |
| Time-series DB (InfluxDB) | 2-4 GB | Moderate compression |
| NoSQL (MongoDB) | 8-15 GB | No/low compression |
| Parquet Files | 1-2 GB | Columnar compression |

**✅ Our system is VERY efficient!**

---

## 💾 **RECOMMENDED HARDWARE**

### **For 5 Years of Data:**

**Minimum:**
- Disk: 10 GB SSD (5 GB data + 5 GB overhead)
- RAM: 4 GB (ClickHouse recommended)
- CPU: 2 cores

**Recommended:**
- Disk: 20 GB SSD (plenty of headroom)
- RAM: 8 GB (for better query performance)
- CPU: 4 cores (parallel query execution)

**Optimal:**
- Disk: 50 GB NVMe SSD (fast I/O)
- RAM: 16 GB (cache hot data)
- CPU: 8 cores (max performance)

---

## ✅ **FINAL ANSWER**

### **Storage Requirement for 5 Years:**

**Pessimistic (worst case):** 1 GB
**Realistic (most likely):** 500-750 MB
**Optimistic (best case):** 300-500 MB

### **With Current Hardware (G:\khoirul\aitrading):**

**Assuming you have:**
- Windows WSL2 environment
- Minimum 50 GB free disk space
- ClickHouse in Docker

**Answer:** ✅ **SANGAT CUKUP!**

500 MB - 1 GB adalah **NOTHING** untuk disk modern (biasanya TB-scale).

### **Cost Analysis (if cloud):**

**AWS EBS (gp3):**
- $0.08/GB/month
- 1 GB storage = $0.08/month = **$1/year**
- 5 years total: **$5** 🤑

**Conclusion:** Storage cost is **negligible**. Focus on query performance & data quality instead!

---

**END OF STORAGE CALCULATION**

*Note: Calculations based on 10 pairs, 7 timeframes, 26 indicators, 6 external sources, 5 years retention. Actual storage may vary ±20% based on data characteristics.*
