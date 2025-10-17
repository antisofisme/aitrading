# Database Workflow & Data Flow Documentation

**Version:** 1.0.0
**Created:** 2025-10-16
**Purpose:** Comprehensive documentation of database tables, data flow, and synchronization from input to feature engineering
**Concern Addressed:** "Flow tidak sesuai atau tidak sinkron" (Potential flow misalignment or synchronization issues)

---

## 📋 EXECUTIVE SUMMARY

This document traces the complete data pipeline from raw input (live/historical) through to ML feature engineering. The system is designed with **clear separation of concerns** and **multiple verification points** to ensure data integrity and synchronization.

**Key Findings:**
- ✅ **Data flow is logically sound** - Clear progression from ticks → aggregates → features
- ✅ **Databases properly separated** - TimescaleDB for time-series, ClickHouse for analytics
- ✅ **Synchronization points identified** - Data Bridge ensures consistency between systems
- ⚠️ **Critical attention needed** - Tick aggregator timing and gap detection

---

## 🔄 DATA FLOW OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        INPUT SOURCES (Raw Data)                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          │                         │                         │
          ▼                         ▼                         ▼
  ┌───────────────┐        ┌───────────────┐        ┌───────────────┐
  │  LIVE TICKS   │        │  HISTORICAL   │        │   EXTERNAL    │
  │   (Polygon    │        │   DOWNLOAD    │        │  DATA SOURCES │
  │   WebSocket)  │        │  (REST API)   │        │  (6 sources)  │
  └───────┬───────┘        └───────┬───────┘        └───────┬───────┘
          │                        │                        │
          └────────────┬───────────┘                        │
                       ▼                                    │
          ┌─────────────────────────┐                       │
          │   MESSAGE QUEUE (NATS)  │                       │
          │  tick.{symbol}.quote    │                       │
          └────────────┬────────────┘                       │
                       ▼                                    │
          ┌─────────────────────────┐                       │
          │   DATA BRIDGE SERVICE   │◄──────────────────────┘
          │ (PostgreSQL + ClickHouse│
          │       Writer)           │
          └────────────┬────────────┘
                       │
         ┌─────────────┼─────────────┐
         ▼                           ▼
┌─────────────────┐         ┌─────────────────┐
│  TIMESCALEDB    │         │   CLICKHOUSE    │
│  (OLTP Layer)   │         │ (OLAP Layer)    │
│                 │         │                 │
│ • market_ticks  │         │ • external_*    │
└────────┬────────┘         └─────────────────┘
         │
         ▼
┌─────────────────┐
│ TICK AGGREGATOR │ ← Aggregates ticks into OHLCV candles
│   (Cron-based)  │   (5m, 15m, 30m, 1h, 4h, 1d, 1w)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   CLICKHOUSE    │
│  • aggregates   │ ← OHLCV bars + 26 technical indicators
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│ FEATURE ENGINEERING │ ← Combines aggregates + external data
│      SERVICE        │   Generates 72 ML features
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│    CLICKHOUSE       │
│ • ml_training_data  │ ← Final ML training dataset (72 features)
└─────────────────────┘
```

---

## 📊 DATABASE ARCHITECTURE

### **Two-Database Strategy:**

| Database | Type | Purpose | Data Volume | Retention |
|----------|------|---------|-------------|-----------|
| **TimescaleDB** (PostgreSQL) | OLTP | Real-time tick storage, fast writes | High frequency (100K+ ticks/sec) | 90 days |
| **ClickHouse** | OLAP | Analytical storage, aggregations, ML | Historical analysis | 10 years |

**Why Two Databases?**
- **TimescaleDB**: Optimized for high-frequency writes (live ticks), ACID compliance
- **ClickHouse**: Columnar storage for analytical queries, 10-100x compression, fast aggregations

---

## 🗂️ TABLE SCHEMAS & DATA FLOW

### **LAYER 1: RAW INPUT → TimescaleDB**

#### **Table: `market_ticks` (TimescaleDB)**

**Purpose:** Primary storage for real-time tick data
**Source:** Polygon Live WebSocket → NATS → Data Bridge
**Volume:** ~10,000-100,000 ticks/day per symbol
**Retention:** 90 days (compressed after 7 days)

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `time` | TIMESTAMPTZ | Tick timestamp (primary key) | 2025-10-16 14:23:45.123+00 |
| `tick_id` | UUID | Unique tick identifier | 550e8400-e29b-41d4-a716-... |
| `tenant_id` | VARCHAR(50) | Multi-tenant isolation | 'system' |
| `symbol` | VARCHAR(20) | Trading pair | 'XAU/USD', 'EUR/USD' |
| `bid` | DECIMAL(18,5) | Bid price | 2645.32000 |
| `ask` | DECIMAL(18,5) | Ask price | 2645.45000 |
| `mid` | DECIMAL(18,5) | Mid price = (bid+ask)/2 | 2645.38500 |
| `spread` | DECIMAL(10,5) | Spread in pips | 1.30000 |
| `source` | VARCHAR(50) | Data source | 'polygon_websocket' |
| `event_type` | VARCHAR(20) | Event type | 'quote' |
| `timestamp_ms` | BIGINT | Unix milliseconds | 1697461425123 |
| `ingested_at` | TIMESTAMPTZ | Ingestion time | 2025-10-16 14:23:45.456+00 |

**Key Features:**
- **Hypertable**: Automatic time-based partitioning (1-day chunks)
- **Compression**: Chunks older than 7 days compressed (10-20x reduction)
- **Retention**: Auto-delete after 90 days
- **RLS**: Row-level security for tenant isolation
- **Indexes**: Optimized for (tenant_id, symbol, time) queries

**Data Flow:**
```
Polygon WebSocket → NATS (tick.{symbol}.quote) → Data Bridge → market_ticks table
```

**Continuous Aggregates:**
- `market_ticks_1m`: 1-minute OHLCV pre-aggregation
- `latest_market_ticks`: Latest tick per symbol (dashboard)

---

### **LAYER 2: TICK AGGREGATION → ClickHouse**

#### **Table: `aggregates` (ClickHouse)**

**Purpose:** Historical OHLCV bars for backtesting and ML training
**Source:** Tick Aggregator queries `market_ticks` → Aggregates into candles → Writes to ClickHouse
**Timeframes:** 5m, 15m, 30m, 1h, 4h, 1d, 1w (7 timeframes)
**Retention:** 10 years

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `symbol` | String | Trading pair | 'XAU/USD' |
| `timeframe` | String | Candle timeframe | '1h', '5m', '1d' |
| `timestamp` | DateTime64(3) | Bar start time (UTC) | 2025-10-16 14:00:00.000 |
| `timestamp_ms` | UInt64 | Unix milliseconds | 1697461200000 |
| `open` | Decimal(18,5) | Open price | 2645.12000 |
| `high` | Decimal(18,5) | High price | 2647.85000 |
| `low` | Decimal(18,5) | Low price | 2644.20000 |
| `close` | Decimal(18,5) | Close price | 2646.50000 |
| `volume` | UInt64 | Tick count (proxy volume) | 1234 |
| `vwap` | Decimal(18,5) | Volume-weighted average price | 2645.95000 |
| `range_pips` | Decimal(10,5) | High - Low in pips | 36.50000 |
| `body_pips` | Decimal(10,5) | abs(close - open) in pips | 13.80000 |
| `start_time` | DateTime64(3) | Bar start time | 2025-10-16 14:00:00.000 |
| `end_time` | DateTime64(3) | Bar end time | 2025-10-16 14:59:59.999 |
| `source` | String | Data source | 'live_aggregated', 'polygon_historical' |
| `event_type` | String | Event type | 'ohlcv' |
| `indicators` | String (JSON) | 26 technical indicators | '{"sma_7": 2645.3, "rsi_14": 58.2, ...}' |
| `ingested_at` | DateTime64(3) | Ingestion timestamp | 2025-10-16 15:01:23.456 |

**Technical Indicators in JSON (26 indicators):**
```json
{
  "sma_7": 2645.30, "sma_14": 2643.50, "sma_21": 2641.20, "sma_50": 2638.10, "sma_200": 2620.50,
  "ema_7": 2646.10, "ema_14": 2644.20, "ema_21": 2642.30, "ema_50": 2639.50, "ema_200": 2622.30,
  "rsi_14": 58.23,
  "macd_line": 3.45, "macd_signal": 2.10, "macd_histogram": 1.35,
  "stochastic_k": 72.34, "stochastic_d": 68.12,
  "bollinger_upper": 2650.20, "bollinger_middle": 2645.30, "bollinger_lower": 2640.40, "bollinger_width": 9.80,
  "atr_14": 18.45,
  "mfi_14": 64.32,
  "obv": 1234567,
  "adl": 9876543,
  "cci_20": 112.34,
  "vwap": 2645.95
}
```

**Key Features:**
- **Partitioning**: By (symbol, month) for efficient pruning
- **Sorting**: By (symbol, timeframe, timestamp) for fast lookups
- **TTL**: 10-year retention (3650 days)
- **Compression**: Automatic ClickHouse compression (10-100x)
- **Materialized Views**: `daily_stats`, `monthly_stats` for pre-aggregated analytics

**Data Flow:**
```
market_ticks (TimescaleDB)
  → Tick Aggregator (Cron: every 5m, 15m, 1h, etc.)
  → Aggregates OHLCV + calculates 26 indicators
  → aggregates table (ClickHouse)
```

**Aggregation Logic:**
```sql
-- Example: 1-hour aggregation
SELECT
    time_bucket('1 hour', time) AS timestamp,
    symbol,
    FIRST(mid, time) AS open,
    MAX(mid) AS high,
    MIN(mid) AS low,
    LAST(mid, time) AS close,
    COUNT(*) AS volume,
    AVG(mid) AS vwap
FROM market_ticks
WHERE symbol = 'XAU/USD'
  AND time >= '2025-10-16 14:00:00'
  AND time < '2025-10-16 15:00:00'
GROUP BY timestamp, symbol;
```

---

### **LAYER 3: EXTERNAL DATA → ClickHouse**

#### **Table: `external_economic_calendar` (ClickHouse)**

**Purpose:** Economic events and news for fundamental analysis
**Source:** MQL5.com Economic Calendar → External Data Collector → ClickHouse
**Update Frequency:** Hourly
**Retention:** 2 years

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `date` | Date | Event date | 2025-10-16 |
| `time` | String | Event time | '14:30' |
| `currency` | String | Currency code | 'USD', 'EUR' |
| `event` | String | Event name | 'Non-Farm Payrolls', 'CPI' |
| `forecast` | Nullable(String) | Forecasted value | '200K', '3.2%' |
| `previous` | Nullable(String) | Previous value | '180K', '3.0%' |
| `actual` | Nullable(String) | Actual value (after release) | '225K', '3.6%' |
| `impact` | String | Impact level | 'low', 'medium', 'high' |
| `source` | String | Data source | 'mql5' |
| `collected_at` | DateTime | Collection timestamp | 2025-10-16 10:15:23 |

**Key Features:**
- **High Impact Index**: Fast filtering for high-impact events
- **TTL**: 2-year retention (730 days)

---

#### **Table: `external_fred_economic` (ClickHouse)**

**Purpose:** Economic indicators from Federal Reserve Economic Data
**Source:** FRED (St. Louis Federal Reserve) → External Data Collector → ClickHouse
**Update Frequency:** Every 4 hours
**Retention:** 5 years

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `series_id` | String | Indicator ID | 'GDP', 'UNRATE', 'CPIAUCSL', 'DFF' |
| `value` | Float64 | Indicator value | 3.2, 3.8, 304.7 |
| `observation_date` | Date | Observation date | 2025-10-01 |
| `source` | String | Data source | 'fred' |
| `collected_at` | DateTime | Collection timestamp | 2025-10-16 08:00:00 |

**Key Series IDs:**
- `GDP`: Gross Domestic Product
- `UNRATE`: Unemployment Rate
- `CPIAUCSL`: Consumer Price Index
- `DFF`: Federal Funds Rate
- `DGS10`: 10-Year Treasury Yield

**Key Features:**
- **Materialized View**: `fred_latest_values` for latest indicator values
- **TTL**: 5-year retention (1825 days)

---

#### **Additional External Tables:**

| Table | Purpose | Update Frequency | Retention |
|-------|---------|------------------|-----------|
| `external_crypto_sentiment` | Crypto market sentiment | Every 6 hours | 1 year |
| `external_fear_greed_index` | CNN Fear & Greed Index | Daily | 2 years |
| `external_commodity_prices` | Gold, Oil, Silver prices | Every 4 hours | 5 years |
| `external_market_sessions` | Trading session info (London, NY, Tokyo) | Static | Permanent |

---

### **LAYER 4: FEATURE ENGINEERING → ML Training Data**

#### **Table: `ml_training_data` (ClickHouse)**

**Purpose:** Final ML training dataset with 72 engineered features
**Source:** Feature Engineering Service queries `aggregates` + `external_*` tables → Calculates 72 features → Writes to ClickHouse
**Processing:** 6-month chunks (memory-efficient)
**Retention:** 10 years

**Feature Groups (72 features total):**

| Group | Features | Expected Importance | Description |
|-------|----------|---------------------|-------------|
| **News/Calendar** | 8 | ~20% | `upcoming_high_impact_events_4h`, `time_to_next_event_minutes`, `event_impact_score`, `is_pre_news_zone`, `is_post_news_zone`, `event_type_category`, `actual_vs_forecast_deviation`, `historical_event_volatility` |
| **Price Action** | 10 | ~18% | `support_resistance_distance`, `is_at_key_level`, `order_block_zone`, `swing_high_low_distance`, `price_rejection_wick`, `h4_trend_direction`, `h4_support_resistance_distance`, `d1_support_resistance_distance`, `w1_swing_high_low`, `multi_tf_alignment` |
| **Multi-Timeframe** | 9 | ~15% | `m5_momentum`, `m15_consolidation`, `h1_trend`, `h4_structure`, `d1_bias`, `w1_major_level`, `tf_alignment_score`, `h4_h1_divergence`, `d1_w1_alignment` |
| **Candlestick Patterns** | 9 | ~15% | `bullish_engulfing`, `bearish_engulfing`, `pin_bar_bullish`, `pin_bar_bearish`, `doji_indecision`, `hammer_reversal`, `shooting_star`, `morning_star`, `evening_star` |
| **Volume Analysis** | 8 | ~15% | `volume_spike`, `volume_profile`, `buying_pressure`, `selling_pressure`, `volume_momentum`, `volume_at_level`, `delta_volume`, `volume_divergence` |
| **Volatility/Regime** | 6 | ~12% | `atr_current`, `atr_expansion`, `true_range_pct`, `volatility_regime`, `adx_value`, `bb_width` |
| **Divergence** | 4 | ~10% | `rsi_price_divergence`, `macd_price_divergence`, `volume_price_divergence`, `divergence_strength` |
| **Market Context** | 6 | ~8% | `is_london_session`, `is_new_york_session`, `is_asian_session`, `liquidity_level`, `day_of_week`, `time_of_day_category` |
| **Fibonacci** | 9 | ~8% | `fib_retracement_0.236`, `fib_retracement_0.382`, `fib_retracement_0.5`, `fib_retracement_0.618`, `fib_retracement_0.786`, `fib_extension_1.272`, `fib_extension_1.618`, `is_in_golden_zone`, `distance_to_nearest_fib_level` |
| **Momentum** | 3 | ~5% | `rsi_value`, `macd_histogram`, `stochastic_k` |
| **Moving Averages** | 2 | ~2% | `sma_200`, `ema_50` |
| **Structure SL/TP** | 5 | ~5% | `nearest_support_distance`, `nearest_resistance_distance`, `structure_risk_reward`, `atr_based_sl_distance`, `structure_based_tp_distance` |

**Schema:**
```sql
CREATE TABLE ml_training_data (
    -- Metadata
    symbol String,
    timeframe String,
    timestamp DateTime64(3),
    timestamp_ms UInt64,

    -- Price data (reference)
    open Float64, high Float64, low Float64, close Float64, volume UInt64,

    -- 72 ML features (see above)
    ...

    -- Target variables
    target UInt8,                -- Binary: 0=not profitable, 1=profitable
    target_pips Float64,         -- Actual pips moved

    -- Metadata
    data_quality_score Float64,  -- 0-1 score for data completeness
    feature_version String,      -- Feature calculation version (e.g., "2.3")
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, timeframe, timestamp);
```

**Data Flow:**
```
aggregates table (OHLCV + 26 indicators)
  + external_economic_calendar
  + external_fred_economic
  + external_crypto_sentiment
  + external_fear_greed_index
  + external_commodity_prices
  → Feature Engineering Service
  → Calculates 72 features (v2.3)
  → ml_training_data table
```

**Processing Strategy:**
- **Memory-Efficient Chunking**: Processes 6-month chunks to prevent OOM
- **Historical Processing**: Processes ALL available data (up to 10 years)
- **Continuous Processing**: Processes new H1 candles every hour

---

## 🔄 DATA SYNCHRONIZATION POINTS

### **Critical Synchronization Areas:**

#### **1. Live Ticks → TimescaleDB Sync**

**Service:** Data Bridge
**Flow:** `NATS (tick.{symbol}.quote)` → Data Bridge → `market_ticks` table
**Frequency:** Real-time (as ticks arrive)
**Verification:**
```sql
-- Check latest tick age
SELECT
    symbol,
    MAX(time) AS latest_tick,
    NOW() - MAX(time) AS age
FROM market_ticks
WHERE tenant_id = 'system'
GROUP BY symbol
HAVING age > INTERVAL '5 minutes';  -- Alert if > 5 min old
```

**Failure Handling:**
- **Dead Letter Queue (DLQ)**: Failed writes go to `data_bridge_dlq` table (PostgreSQL)
- **Retry Logic**: 6 retries with exponential backoff
- **Manual Replay**: Operations team can replay DLQ messages

---

#### **2. Ticks → Aggregates Sync**

**Service:** Tick Aggregator
**Flow:** `market_ticks` → Tick Aggregator (Cron) → `aggregates` table
**Frequency:** Every 5m, 15m, 30m, 1h, 4h, daily, weekly
**Verification:**
```sql
-- Check for missing aggregates (gaps)
WITH expected_candles AS (
    SELECT generate_series(
        date_trunc('hour', NOW() - INTERVAL '24 hours'),
        date_trunc('hour', NOW()),
        INTERVAL '1 hour'
    ) AS expected_time
)
SELECT e.expected_time
FROM expected_candles e
LEFT JOIN aggregates a
    ON date_trunc('hour', a.timestamp) = e.expected_time
    AND a.symbol = 'XAU/USD'
    AND a.timeframe = '1h'
WHERE a.timestamp IS NULL;
```

**Gap Detection:**
- Tick Aggregator has **gap detection and backfill logic**
- Queries ClickHouse for missing candles and fills them from TimescaleDB

---

#### **3. External Data → ClickHouse Sync**

**Service:** External Data Collector
**Flow:** External APIs → External Data Collector → `external_*` tables
**Frequency:** Hourly (calendar), 4-hourly (FRED), 6-hourly (crypto)
**Verification:**
```sql
-- Check external data freshness
SELECT
    'economic_calendar' AS table_name,
    MAX(collected_at) AS last_update,
    NOW() - MAX(collected_at) AS age
FROM external_economic_calendar
UNION ALL
SELECT
    'fred_economic' AS table_name,
    MAX(collected_at) AS last_update,
    NOW() - MAX(collected_at) AS age
FROM external_fred_economic;
```

**Failure Handling:**
- External Data Collector logs failed API calls
- Retries with exponential backoff
- Alerts if data > 24 hours old

---

#### **4. Aggregates + External → ML Training Data Sync**

**Service:** Feature Engineering Service
**Flow:** `aggregates` + `external_*` → Feature Calculator → `ml_training_data`
**Frequency:** Historical (6-month chunks), Continuous (hourly for new candles)
**Verification:**
```sql
-- Check if ml_training_data is up-to-date
SELECT
    MAX(timestamp) AS latest_feature_timestamp,
    (SELECT MAX(timestamp) FROM aggregates WHERE symbol = 'XAU/USD' AND timeframe = '1h') AS latest_aggregate_timestamp,
    latest_aggregate_timestamp - latest_feature_timestamp AS lag
FROM ml_training_data
WHERE symbol = 'XAU/USD' AND timeframe = '1h';
```

**Data Quality:**
- `data_quality_score` column tracks feature completeness (0-1)
- Features with missing external data get lower quality scores
- ML training can filter by quality threshold

---

## ⚠️ POTENTIAL SYNCHRONIZATION ISSUES & SOLUTIONS

### **Issue 1: Tick Aggregator Timing Mismatch**

**Problem:** Cron runs at fixed intervals, but candles close at dynamic times
**Example:** 1-hour cron at 15:00:00, but last tick at 14:59:58 (2 seconds before close)

**Solution:**
```python
# Tick Aggregator waits for candle completion
lookback_minutes = 65  # Query last 65 minutes for 1h candle (safety margin)

# Query with safety margin
query = f"""
SELECT * FROM market_ticks
WHERE symbol = '{symbol}'
  AND time >= '{candle_start}' - INTERVAL '5 minutes'
  AND time < '{candle_end}' + INTERVAL '5 minutes'
"""
```

---

### **Issue 2: External Data Missing for Recent Candles**

**Problem:** Feature engineering runs before external data is collected
**Example:** H1 candle at 14:00, but economic calendar only collected at 14:30

**Solution:**
```python
# Feature calculator checks data availability
def calculate_features(aggregates_batch, timeframe):
    # Query external data with lookback window
    calendar_data = query_economic_calendar(
        start_time=batch_start - timedelta(hours=4),  # 4h lookback
        end_time=batch_end
    )

    # Set data_quality_score based on availability
    if calendar_data.empty:
        features['data_quality_score'] = 0.7  # Reduced quality
        features['upcoming_high_impact_events_4h'] = 0  # Default value
    else:
        features['data_quality_score'] = 1.0
        features['upcoming_high_impact_events_4h'] = len(calendar_data)
```

---

### **Issue 3: Historical Data Gaps in TimescaleDB**

**Problem:** market_ticks has 90-day retention, but aggregates need historical data
**Example:** Need to fill 6-month gap, but ticks only available for 90 days

**Solution:**
```python
# Hybrid approach: Use both sources
if gap_date > (now - 90 days):
    # Recent gap: Use TimescaleDB ticks
    aggregator.backfill_from_timescaledb(gap_date)
else:
    # Old gap: Use Polygon Historical API
    historical_downloader.download_bars(gap_date, timeframe='1h')
```

---

## ✅ DATA VERIFICATION CHECKLIST

### **Daily Health Checks:**

1. **Tick Data Freshness** (Live WebSocket)
```sql
SELECT symbol, MAX(time) as latest_tick, NOW() - MAX(time) as age
FROM market_ticks
WHERE tenant_id = 'system'
GROUP BY symbol
HAVING age > INTERVAL '5 minutes';
-- Expected: 0 rows (all ticks fresh)
```

2. **Aggregate Gaps** (1h timeframe)
```sql
SELECT
    symbol,
    COUNT(*) as candle_count,
    24 - COUNT(*) as missing_candles
FROM aggregates
WHERE timeframe = '1h'
  AND timestamp >= date_trunc('day', NOW())
  AND timestamp < date_trunc('day', NOW()) + INTERVAL '1 day'
GROUP BY symbol;
-- Expected: candle_count = 24 (no gaps)
```

3. **External Data Freshness**
```sql
SELECT
    'economic_calendar' as source,
    MAX(collected_at) as last_update,
    NOW() - MAX(collected_at) as age
FROM external_economic_calendar
UNION ALL
SELECT
    'fred_economic' as source,
    MAX(collected_at) as last_update,
    NOW() - MAX(collected_at) as age
FROM external_fred_economic;
-- Expected: age < 24 hours for all sources
```

4. **ML Training Data Quality**
```sql
SELECT
    symbol,
    timeframe,
    COUNT(*) as total_rows,
    AVG(data_quality_score) as avg_quality,
    SUM(CASE WHEN data_quality_score < 0.8 THEN 1 ELSE 0 END) as low_quality_count
FROM ml_training_data
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY symbol, timeframe;
-- Expected: avg_quality > 0.9, low_quality_count < 5%
```

5. **Data Bridge DLQ Check** (Failed writes)
```sql
SELECT
    message_type,
    COUNT(*) as failure_count,
    MAX(created_at) as latest_failure
FROM data_bridge_dlq
WHERE replayed = FALSE
GROUP BY message_type;
-- Expected: 0 rows (no failures)
```

---

## 📈 DATA VOLUMES & PERFORMANCE

### **Expected Data Volumes:**

| Table | Rows/Day | Storage/Day | Total Storage (Full Retention) |
|-------|----------|-------------|-------------------------------|
| `market_ticks` (14 pairs) | ~1.4M | ~200 MB | ~18 GB (90 days, compressed) |
| `aggregates` (7 timeframes) | ~2,400 | ~5 MB | ~18 GB (10 years, compressed) |
| `external_economic_calendar` | ~50 | ~10 KB | ~36 MB (2 years) |
| `external_fred_economic` | ~20 | ~5 KB | ~36 MB (5 years) |
| `ml_training_data` | ~24 | ~2 MB | ~7.3 GB (10 years) |

**Total Storage:** ~44 GB (with ClickHouse compression 10-100x)

---

## 🚀 PERFORMANCE OPTIMIZATION

### **Query Optimization Tips:**

1. **Use PREWHERE in ClickHouse**
```sql
-- Fast: PREWHERE filters before decompression
SELECT * FROM aggregates
PREWHERE symbol = 'XAU/USD' AND timeframe = '1h'
WHERE timestamp >= now() - INTERVAL 30 DAY;
```

2. **Leverage Materialized Views**
```sql
-- Instead of scanning full table
SELECT avgMerge(avg_close) FROM daily_stats
WHERE symbol = 'XAU/USD' AND day >= today() - INTERVAL 30 DAY;
```

3. **Use TimescaleDB Continuous Aggregates**
```sql
-- Pre-aggregated 1-minute candles
SELECT * FROM market_ticks_1m
WHERE symbol = 'EUR/USD'
  AND bucket >= NOW() - INTERVAL '1 hour';
```

---

## 🔍 TROUBLESHOOTING GUIDE

### **Symptom: ML features missing or stale**

**Check:**
1. Is `aggregates` table up-to-date?
```sql
SELECT MAX(timestamp) FROM aggregates WHERE symbol = 'XAU/USD' AND timeframe = '1h';
```

2. Is Feature Engineering Service running?
```bash
docker logs suho-feature-engineering --tail 100
```

3. Are external data tables up-to-date?
```sql
SELECT MAX(collected_at) FROM external_economic_calendar;
```

---

### **Symptom: Aggregate gaps (missing candles)**

**Check:**
1. Are ticks available in TimescaleDB?
```sql
SELECT COUNT(*) FROM market_ticks
WHERE symbol = 'XAU/USD'
  AND time >= '2025-10-16 14:00:00'
  AND time < '2025-10-16 15:00:00';
```

2. Did Tick Aggregator run?
```bash
docker logs suho-tick-aggregator --tail 100 | grep "Aggregation completed"
```

3. Manual backfill:
```bash
# Trigger manual aggregation
docker exec suho-tick-aggregator python -m src.backfill --symbol XAU/USD --timeframe 1h --start "2025-10-16 14:00"
```

---

### **Symptom: Data Bridge DLQ has failed messages**

**Check:**
1. View DLQ entries:
```sql
SELECT * FROM data_bridge_dlq WHERE replayed = FALSE ORDER BY created_at DESC LIMIT 50;
```

2. Inspect error messages:
```sql
SELECT message_type, last_error, COUNT(*) FROM data_bridge_dlq
WHERE replayed = FALSE
GROUP BY message_type, last_error;
```

3. Manual replay (after fixing root cause):
```sql
-- Mark as ready for replay
UPDATE data_bridge_dlq SET replayed = FALSE WHERE id IN (1, 2, 3);

-- Trigger replay script
docker exec suho-data-bridge python -m src.replay_dlq
```

---

## 📝 CONCLUSIONS & RECOMMENDATIONS

### **Current State Assessment:**

✅ **STRENGTHS:**
1. **Clear data flow architecture** - Well-separated layers (OLTP → OLAP → ML)
2. **Proper database selection** - TimescaleDB for writes, ClickHouse for analytics
3. **Comprehensive feature set** - 72 features from 11 categories
4. **Failure handling** - DLQ for failed writes, gap detection, retry logic
5. **Multi-timeframe analysis** - 7 timeframes for rich ML context

⚠️ **AREAS FOR ATTENTION:**

1. **External Data Timing**
   - **Issue**: External data collection may lag behind feature engineering
   - **Impact**: Features may have default/missing values for recent candles
   - **Mitigation**: `data_quality_score` tracks completeness; filter by quality threshold during ML training

2. **Tick Aggregator Timing**
   - **Issue**: Cron schedule may miss late-arriving ticks
   - **Impact**: OHLCV candles may be slightly incomplete
   - **Mitigation**: Lookback windows (e.g., 65 minutes for 1h candles) capture late ticks

3. **Historical Gap Handling**
   - **Issue**: TimescaleDB has 90-day retention, but may need older data for backfill
   - **Impact**: Cannot backfill gaps older than 90 days from ticks
   - **Mitigation**: Hybrid approach - use Polygon Historical API for old gaps

### **Recommendations:**

1. **Implement Daily Health Dashboard**
   - Automate verification queries above
   - Alert on: tick staleness, aggregate gaps, external data age, DLQ entries
   - Grafana + Prometheus for monitoring

2. **Add Data Quality Metrics to ML Pipeline**
   - Filter training data by `data_quality_score >= 0.9`
   - Track feature completeness per timeframe
   - Log features with frequent missing values

3. **Consider Real-Time Feature Engineering**
   - Current: Batch processing (historical chunks + hourly continuous)
   - Future: Stream processing with Apache Flink/Kafka Streams for sub-second features

4. **Add Data Lineage Tracking**
   - Track which ticks → aggregates → features
   - Useful for debugging ML predictions
   - Store `aggregate_id` and `tick_count` in `ml_training_data`

---

## 📚 RELATED DOCUMENTATION

- [TRADING_STRATEGY_AND_ML_DESIGN.md](./TRADING_STRATEGY_AND_ML_DESIGN.md) - 72 features specification (v2.3)
- [FOUNDATION_VERIFICATION_REPORT.md](./FOUNDATION_VERIFICATION_REPORT.md) - Phase 1 completion status
- [FIBONACCI_ANALYSIS_AND_INTEGRATION.md](./FIBONACCI_ANALYSIS_AND_INTEGRATION.md) - Fibonacci features (v2.3)

---

**Document Status:** ✅ COMPLETE
**Last Updated:** 2025-10-16
**Next Review:** After Phase 2 ML training completion
