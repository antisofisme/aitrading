# 🏗️ AI Trading System - Complete Data Architecture Guide

## 📋 Overview

Panduan lengkap arsitektur data untuk sistem AI Trading - **dari mana ke mana** semua data disimpan dan diproses.

**Konsep Utama**: Hybrid Database Strategy dengan 5 layer storage untuk performa optimal ML/DL.

---

## 🎯 CRITICAL: System Use Case Understanding

### **System Flow: Analysis → Execution**

```
┌────────────────────────────────────────────────────────────────┐
│ PHASE 1: ANALYSIS (System AI/ML)                              │
├────────────────────────────────────────────────────────────────┤
│ Data Source: Polygon Aggregates (OHLCV Candles)               │
│ Timeframes:  M1, M5, M15, H1, H4, D1                          │
│ Process:     ML/DL analyze candle patterns                    │
│ Output:      SIGNAL: "BUY EUR/USD on M15 timeframe"           │
└────────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────────┐
│ PHASE 2: EXECUTION (User's Broker)                            │
├────────────────────────────────────────────────────────────────┤
│ Data Source: User's MT5 Real-time Bid/Ask                     │
│ Process:     System reads user's current broker prices        │
│ Execution:   Open position at user's broker price             │
│ Example:     BUY at ask=1.08485 (user's broker, not Polygon)  │
└────────────────────────────────────────────────────────────────┘
```

### **KEY PRINCIPLES:**

1. **Analysis Uses CANDLE DATA (Aggregates)** ✅
   - ML/DL models analyze based on timeframe candles (M1, M5, M15, etc.)
   - NOT per-second ticks
   - NOT individual bid/ask movements

2. **Execution Uses USER'S BROKER PRICES** ✅
   - Each broker has different bid/ask prices
   - Execution MUST use user's actual broker price
   - NOT Polygon ticks (reference only)

3. **Polygon Ticks = Research Only** ⚠️
   - Spread analysis, liquidity research
   - NOT for ML prediction
   - NOT for execution

---

## 📊 Data Type Classification

### **Type 1: Aggregates (OHLCV Candles)**

**Purpose**: ML/DL Analysis & Technical Analysis

**Sources**:
- ✅ Polygon Live (CAS Stream) - Real-time aggregates
- ✅ Polygon Historical (REST API) - Backfill & gap filling

**Timeframes**: M1, M5, M15, H1, H4, D1

**Format**:
```python
{
    'symbol': 'EUR/USD',
    'timeframe': 'M15',      # Analysis timeframe
    'timestamp': ...,
    'open': 1.0845,
    'high': 1.0855,
    'low': 1.0840,
    'close': 1.0850,
    'volume': 12345,
    'vwap': 1.0847,
    'source': 'polygon_aggregate' or 'polygon_historical'
}
```

**Storage**: ClickHouse `aggregates` table (Live + Historical MERGED)

**Why Merged?**
- Same data structure
- Same use case (ML training, charting)
- Gap filling: Historical fills missing live data
- Continuous time-series for queries

---

### **Type 2: Ticks (Bid/Ask Quotes)**

**Purpose**: Research, Spread Analysis (Optional)

**Sources**:
- ✅ Polygon Live (C Stream) - Reference bid/ask
- ❌ Polygon Historical - NOT available

**Format**:
```python
{
    'symbol': 'EUR/USD',
    'bid': 1.08480,
    'ask': 1.08490,
    'spread': 1.0,
    'timestamp': ...,
    'source': 'polygon_websocket'
}
```

**Storage**: ClickHouse `ticks` table (Optional)

**NOT Used For**:
- ❌ ML/DL prediction (use aggregates instead)
- ❌ Execution (use user's broker prices instead)

---

### **Type 3: User's Broker Quotes**

**Purpose**: Actual Trade Execution + Data Enrichment

**Sources**:
- ✅ MT5 API from user's broker

**Format**:
```python
{
    'symbol': 'EUR/USD',
    'bid': 1.08475,          # Real broker price
    'ask': 1.08485,          # Real broker price
    'spread': 1.0,
    'user_id': 'user123',
    'broker_metadata': {      # Flexible JSONB - from user
        'broker_name': 'IC Markets',
        'account_type': 'Raw Spread',
        'server': 'ICMarkets-Demo01',
        'platform': 'MT5',
        # ... any other user-defined metadata
    },
    'timestamp': ...
}
```

**Storage Strategy**: **HYBRID** (2-Tier)

```
┌─────────────────────────────────────────────────────────┐
│ HOT TIER: DragonflyDB (Last 1 Hour)                    │
├─────────────────────────────────────────────────────────┤
│ Key: user_quotes:{user_id}:{symbol}:{timestamp_ms}     │
│ TTL: 3600 seconds (1 hour)                             │
│ Purpose: Ultra-fast execution reads                     │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│ WARM TIER: TimescaleDB (Last 24 Hours)                 │
├─────────────────────────────────────────────────────────┤
│ Table: user_broker_quotes                               │
│ Retention: 24 hours                                     │
│ Cleanup: Batch delete every 48 hours                    │
│ Purpose: Spread analysis & broker comparison            │
└─────────────────────────────────────────────────────────┘
```

**Retention & Cleanup**:
- ✅ **24-hour rolling window** (data older than 24h not needed)
- ✅ **Batch cleanup every 48 hours** (not per-second DELETE)
- ✅ Efficient: Single DELETE query removes old data

**Multi-Tenant Architecture**:
- ✅ Row-level separation by `user_id`
- ✅ Each user can have different broker
- ✅ Flexible `broker_metadata` JSONB field (user-defined)

**Critical**:
- ✅ **Execution**: Read latest bid/ask from DragonflyDB (sub-ms latency)
- ✅ **Data Enrichment**: Analyze spread differences across brokers
- ✅ **Broker Comparison**: Which broker has best spread? (research)
- ✅ Different from Polygon (each broker has different prices)

---

## 🎯 Quick Reference - Data Flow Summary

```
┌─────────────────────────────────────────────────────────────────────┐
│                    COMPLETE DATA FLOW ARCHITECTURE                  │
└─────────────────────────────────────────────────────────────────────┘

1️⃣ POLYGON AGGREGATES (For ML/DL Analysis)

   Real-time:
   Polygon CAS Stream (M1, M5, M15) → NATS/Kafka → Data Bridge
                                                   ↓
                                        ClickHouse.aggregates
                                        (Live + Historical MERGED)

   Backfill/Gap Filling:
   Polygon REST API (Historical) → Direct Write → ClickHouse.aggregates
                                                   (SAME TABLE!)

   Purpose: ML/DL Training & Technical Analysis
   Retention: 10 years

2️⃣ POLYGON TICKS (Optional - Research Only)

   Polygon C Stream (bid/ask) → NATS/Kafka → Data Bridge
                                            ↓
                                 ClickHouse.ticks

   Purpose: Spread analysis, liquidity research
   NOT for: ML prediction, execution
   Retention: 90 days

3️⃣ INDICATOR CALCULATION (100+ Technical Indicators)

   ClickHouse.aggregates → Feature Engineer Service
                         ↓
                   ClickHouse.ml_features
                   (WIDE TABLE - 100+ columns)
                   10 years retention

4️⃣ ML/DL ANALYSIS & PREDICTIONS

   ml_features → Model Training → S3 (model binaries)
               ↓
          ML Inference
               ↓
   Signal: "BUY EUR/USD on M15"
               ↓
   TimescaleDB.ml_predictions + DragonflyDB (cache)

5️⃣ USER'S MT5 BROKER DATA (For Execution + Data Enrichment)

   MT5 API → Data Collector
           ↓
      HYBRID STORAGE:

      A. DragonflyDB (Hot - 1h TTL):
         - user_quotes:{user_id}:{symbol}:{ts}
         - Purpose: Ultra-fast execution (sub-ms read)

      B. TimescaleDB (Warm - 24h retention):
         - user_broker_quotes (bid/ask + flexible broker_metadata JSONB)
         - mt5_user_profiles (balance, equity, margin)
         - mt5_trade_results (actual trading outcomes)
         - Cleanup: Batch DELETE every 48 hours

      USE CASES:
      1. Execution: Read from DragonflyDB for trade execution
      2. Data Enrichment: Analyze spread across brokers (TimescaleDB)
      3. Broker Comparison: Which broker has best execution quality?

   Critical: Execution uses USER'S broker price, NOT Polygon

6️⃣ EXECUTION FLOW

   ML Signal → Read user's current broker bid/ask
            ↓
   Execute at user's broker price (mt5_broker_quotes)
            ↓
   Record result (mt5_trade_results)

7️⃣ COMPARISON & ANALYTICS

   System Predictions ⟷ User Trade Results
   SQL JOINs + Materialized Views
   Pattern Similarity → Weaviate (vector search)
```

---

## 📊 Storage Architecture - 5 Database Strategy

### 1. TimescaleDB (Primary OLTP Database)
**Purpose**: Fast read/write for real-time data + user data
**Retention**: 90 days (hot data)
**Tables**:
- `market_ticks` - Real-time forex quotes
- `market_candles` - OHLCV bars (1m, 5m, 1h, 1d)
- `ml_predictions` - ML/DL prediction results
- `mt5_user_profiles` - User account data
- `mt5_broker_quotes` - User broker prices
- `mt5_trade_results` - User trading outcomes

📖 **Detail Schema**: [/03-ml-pipeline/schemas/03_timescaledb_predictions.sql](./03-ml-pipeline/schemas/03_timescaledb_predictions.sql)
📖 **MT5 Schema**: [/docs/architecture/END_TO_END_ARCHITECTURE.md](./docs/architecture/END_TO_END_ARCHITECTURE.md#L1511-L1570)

---

### 2. ClickHouse (Analytics OLAP Database)
**Purpose**: ML training data dengan 100+ columns denormalized
**Retention**: 10 years (backtesting data)
**Tables**:
- `aggregates` - Historical OHLCV bars
- `ml_features` - **WIDE TABLE** (100+ technical indicators)

#### Wide Table Structure (ml_features):
```sql
-- Identifiers
tenant_id, user_id, symbol, timeframe, timestamp

-- Raw OHLCV (5 columns)
open, high, low, close, volume

-- Trend Indicators (40+ columns)
sma_10, sma_20, sma_50, ema_10, ema_20, macd_line, adx_14, ...

-- Momentum Indicators (15+ columns)
rsi_14, stoch_k, cci_20, williams_r_14, ...

-- Volatility Indicators (20+ columns)
bb_upper_20_2, atr_14, kc_upper, dc_upper_20, ...

-- Volume Indicators (10+ columns)
obv, vwap, mfi_14, ...

-- Multi-horizon Labels (6 columns)
label_direction_1h, label_return_1h,
label_direction_4h, label_return_4h,
label_direction_1d, label_return_1d
```

📖 **Detail Schema**: [/03-ml-pipeline/schemas/01_clickhouse_ml_features.sql](./03-ml-pipeline/schemas/01_clickhouse_ml_features.sql)
📖 **ML Pipeline**: [/03-ml-pipeline/IMPLEMENTATION_SUMMARY.md](./03-ml-pipeline/IMPLEMENTATION_SUMMARY.md)

---

### 3. DragonflyDB (Cache Layer + User Broker Quotes)
**Purpose**: Ultra-fast cache untuk real-time queries + execution data
**Retention**: 1 hour - 15 minutes TTL
**Keys**:

**A. System Data (Cache)**:
- `tick:latest:{symbol}` - Latest tick data (1h TTL)
- `candle:latest:{symbol}:{timeframe}` - Latest candles (1h TTL)
- `indicator:{symbol}:{indicator}` - Calculated indicators (5m TTL)
- `prediction:{symbol}:{timeframe}` - Latest predictions (15m TTL)

**B. User Broker Quotes (Execution)**:
- `user_quotes:{user_id}:{symbol}:{timestamp_ms}` - User's broker bid/ask (1h TTL)
- Purpose: Sub-millisecond read for trade execution
- Format: `{"bid": 1.08475, "ask": 1.08485, "spread": 1.0, "broker_metadata": {...}}`

📖 **Cache Strategy**: [/01-core-infrastructure/central-hub/DATA_MANAGER_SPEC.md](./01-core-infrastructure/central-hub/DATA_MANAGER_SPEC.md)

---

### 4. Weaviate (Vector Database)
**Purpose**: Pattern similarity search
**Collections**:
- `price_patterns` - Autoencoder embeddings dari candlestick patterns
- `prediction_history` - Stored predictions untuk similarity matching

📖 **Vector Search**: [/03-ml-pipeline/IMPLEMENTATION_SUMMARY.md](./03-ml-pipeline/IMPLEMENTATION_SUMMARY.md#L200-L250)

---

### 5. PostgreSQL (Metadata Database)
**Purpose**: Model metadata, service configs
**Tables**:
- `ml_models` - Model versions, performance metrics
- `training_jobs` - Training job history
- `feature_definitions` - Feature engineering metadata

📖 **Metadata Schema**: [/03-ml-pipeline/schemas/04_postgresql_metadata.sql](./03-ml-pipeline/schemas/04_postgresql_metadata.sql)

---

## 🔄 Complete Data Flow - Step by Step

### 🟢 Phase 1: Data Ingestion

#### A. Polygon Live Collector (Real-time)
```
Polygon.io WebSocket (Quotes)
→ Live Collector (websocket_client.py)
→ NATS Publisher (market.forex.quotes)
→ Data Bridge (Kafka Subscriber)
→ TimescaleDB.market_ticks
→ DragonflyDB (cache)
```

📖 **Implementation**: [/00-data-ingestion/polygon-live-collector/src/main.py](./00-data-ingestion/polygon-live-collector/src/main.py)
📖 **Config**: [/00-data-ingestion/polygon-live-collector/src/config.py](./00-data-ingestion/polygon-live-collector/src/config.py)

#### B. Polygon Historical Downloader
```
Polygon.io REST API (Aggregates)
→ Historical Downloader (main.py)
→ ClickHouse.aggregates (Direct Write)
```

📖 **Implementation**: [/00-data-ingestion/polygon-historical-downloader/](./00-data-ingestion/polygon-historical-downloader/)

#### C. External Data Collector (Economic Calendar)
```
External APIs (MQL5, FRED, CoinGecko)
→ Scrapers (calendar_mql5_scraper.py)
→ Transform Pipeline
→ PostgreSQL.market_context
```

📖 **Schema**: [/00-data-ingestion/_archived/external-data/database/database_schema_hybrid.sql](./00-data-ingestion/_archived/external-data/database/database_schema_hybrid.sql)

---

### 🟡 Phase 2: Feature Engineering (Indicator Calculation)

```
┌─────────────────────────────────────────┐
│   Raw OHLCV Data (TimescaleDB/ClickHouse) │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│   Feature Engineer Service              │
│   - 40+ Trend Indicators                │
│   - 15+ Momentum Indicators             │
│   - 20+ Volatility Indicators           │
│   - 10+ Volume Indicators               │
│   - Multi-horizon Labels (1h, 4h, 1d)   │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│   ClickHouse.ml_features                │
│   WIDE TABLE (100+ columns)             │
│   Retention: 10 years                   │
└─────────────────────────────────────────┘
```

**Kenapa Wide Table?**
- ✅ Denormalized untuk performa ML training
- ✅ Semua features dalam 1 row → fast batch loading
- ✅ ClickHouse optimized untuk OLAP queries
- ✅ Partisi by (tenant_id, symbol, month) → efficient filtering

📖 **Feature Engineering**: [/03-ml-pipeline/02-feature-engineering/](./03-ml-pipeline/02-feature-engineering/)

---

### 🔵 Phase 3: ML/DL Training & Predictions

#### Training Pipeline:
```
ClickHouse.ml_features (historical data)
→ Model Training Service (LSTM, Transformer, XGBoost)
→ S3 (trained model binaries)
→ PostgreSQL.ml_models (metadata)
```

#### Inference Pipeline:
```
Live Market Data (NATS/Kafka)
→ Feature Computation (real-time)
→ ML Inference Service
→ Weaviate (pattern similarity search)
→ TimescaleDB.ml_predictions
→ DragonflyDB (cache 15 min)
```

**Prediction Schema** (`ml_predictions`):
```sql
CREATE TABLE ml_predictions (
    time TIMESTAMPTZ NOT NULL,
    prediction_id UUID,
    tenant_id VARCHAR(50),
    symbol VARCHAR(20),
    timeframe VARCHAR(10),

    -- Predictions
    predicted_direction INT,        -- 1 (buy), -1 (sell), 0 (hold)
    predicted_price DECIMAL(18,5),
    confidence_score DECIMAL(5,4),

    -- Pattern Matching
    similar_pattern_count INT,
    pattern_similarity_score DECIMAL(5,4),

    -- Signal Generation
    signal_type VARCHAR(20),
    entry_price DECIMAL(18,5),
    stop_loss DECIMAL(18,5),
    take_profit DECIMAL(18,5),

    -- Actual Results (updated later)
    actual_direction INT,
    actual_price DECIMAL(18,5),
    direction_correct BOOLEAN,

    PRIMARY KEY (time, prediction_id)
);

SELECT create_hypertable('ml_predictions', 'time');
CREATE INDEX idx_predictions_tenant ON ml_predictions (tenant_id, time DESC);
```

📖 **ML Pipeline**: [/03-ml-pipeline/IMPLEMENTATION_SUMMARY.md](./03-ml-pipeline/IMPLEMENTATION_SUMMARY.md)
📖 **Prediction Schema**: [/03-ml-pipeline/schemas/03_timescaledb_predictions.sql](./03-ml-pipeline/schemas/03_timescaledb_predictions.sql)

---

### 🟣 Phase 4: MT5 User Data Integration

```
MT5 Platform (User Trading)
→ MT5 API Collector
→ TimescaleDB:
   - mt5_user_profiles
   - mt5_broker_quotes
   - mt5_trade_results
```

#### Schema Details:

**A. User Profiles** (`mt5_user_profiles`):
```sql
CREATE TABLE mt5_user_profiles (
    time TIMESTAMPTZ NOT NULL,
    tenant_id VARCHAR(50),
    user_id VARCHAR(50),
    broker VARCHAR(100),
    balance DECIMAL(18,2),
    equity DECIMAL(18,2),
    margin DECIMAL(18,2),
    free_margin DECIMAL(18,2),
    margin_level DECIMAL(10,2),
    PRIMARY KEY (time, tenant_id, user_id)
);
```

**B. User Broker Quotes** (`user_broker_quotes`):
```sql
CREATE TABLE user_broker_quotes (
    time TIMESTAMPTZ NOT NULL,
    user_id VARCHAR(50),
    symbol VARCHAR(20),
    bid DECIMAL(18,5),
    ask DECIMAL(18,5),
    spread DECIMAL(10,5),
    broker_metadata JSONB,              -- Flexible: broker_name, account_type, server, etc.
    PRIMARY KEY (time, user_id, symbol)
);

-- Hypertable for time-series optimization
SELECT create_hypertable('user_broker_quotes', 'time');

-- Index for fast user queries
CREATE INDEX idx_user_quotes_user ON user_broker_quotes (user_id, symbol, time DESC);

-- Retention policy: Delete data older than 24 hours
SELECT add_retention_policy('user_broker_quotes', INTERVAL '24 hours');

-- Compression after 1 hour (save storage)
ALTER TABLE user_broker_quotes SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'user_id,symbol'
);
SELECT add_compression_policy('user_broker_quotes', INTERVAL '1 hour');
```

**Batch Cleanup Job** (Runs every 48 hours):
```sql
-- Cleanup script (cron job)
DELETE FROM user_broker_quotes
WHERE time < NOW() - INTERVAL '24 hours';
```

**C. Trade Results** (`mt5_trade_results`):
```sql
CREATE TABLE mt5_trade_results (
    time TIMESTAMPTZ NOT NULL,
    trade_id UUID,
    tenant_id VARCHAR(50),
    user_id VARCHAR(50),
    symbol VARCHAR(20),
    trade_type VARCHAR(10),         -- 'buy', 'sell'
    entry_time TIMESTAMPTZ,
    entry_price DECIMAL(18,5),
    exit_time TIMESTAMPTZ,
    exit_price DECIMAL(18,5),
    volume DECIMAL(10,2),
    pnl DECIMAL(18,2),
    pnl_pips DECIMAL(10,4),
    outcome VARCHAR(20),             -- 'win', 'loss', 'breakeven'
    PRIMARY KEY (time, trade_id)
);
```

📖 **MT5 Integration**: [/docs/architecture/END_TO_END_ARCHITECTURE.md](./docs/architecture/END_TO_END_ARCHITECTURE.md#L1511-L1570)

---

### 🔴 Phase 5: Comparison & Analytics (System vs User)

#### Use Case 1: Prediction Accuracy vs User Trades
```sql
-- Compare system predictions with user trade results
SELECT
    p.symbol,
    p.predicted_direction,
    p.confidence_score,
    t.trade_type,
    t.pnl_pips,
    t.outcome,
    CASE
        WHEN p.predicted_direction = 1 AND t.trade_type = 'buy' THEN 'aligned'
        WHEN p.predicted_direction = -1 AND t.trade_type = 'sell' THEN 'aligned'
        ELSE 'divergent'
    END AS alignment
FROM ml_predictions p
INNER JOIN mt5_trade_results t
    ON p.symbol = t.symbol
    AND p.time BETWEEN t.entry_time - INTERVAL '5 minutes'
                   AND t.entry_time + INTERVAL '5 minutes'
WHERE p.tenant_id = t.tenant_id;
```

#### Use Case 2: Broker Price vs System Price
```sql
-- Detect broker spread differences
SELECT
    b.symbol,
    b.broker,
    b.bid AS broker_bid,
    b.ask AS broker_ask,
    (b.ask - b.bid) * 10000 AS broker_spread_pips,
    m.bid AS system_bid,
    m.ask AS system_ask,
    (m.ask - m.bid) * 10000 AS system_spread_pips,
    ABS((b.ask - b.bid) - (m.ask - m.bid)) * 10000 AS spread_difference
FROM mt5_broker_quotes b
INNER JOIN market_ticks m
    ON b.symbol = m.symbol
    AND b.time = m.timestamp
WHERE b.tenant_id = 'tenant_123';
```

#### Use Case 3: Performance Dashboard (Materialized View)
```sql
CREATE MATERIALIZED VIEW user_vs_system_performance AS
SELECT
    t.tenant_id,
    t.user_id,
    t.symbol,
    DATE_TRUNC('day', t.time) AS trade_date,

    -- User Performance
    COUNT(*) AS total_trades,
    SUM(CASE WHEN t.outcome = 'win' THEN 1 ELSE 0 END) AS wins,
    SUM(CASE WHEN t.outcome = 'loss' THEN 1 ELSE 0 END) AS losses,
    SUM(t.pnl_pips) AS total_pnl_pips,

    -- System Prediction Accuracy
    AVG(p.confidence_score) AS avg_prediction_confidence,
    SUM(CASE WHEN p.direction_correct THEN 1 ELSE 0 END) AS correct_predictions,

    -- Alignment Score
    SUM(CASE
        WHEN (p.predicted_direction = 1 AND t.trade_type = 'buy')
          OR (p.predicted_direction = -1 AND t.trade_type = 'sell')
        THEN 1 ELSE 0
    END) AS aligned_trades

FROM mt5_trade_results t
LEFT JOIN ml_predictions p
    ON t.symbol = p.symbol
    AND p.time BETWEEN t.entry_time - INTERVAL '5 minutes'
                   AND t.entry_time + INTERVAL '5 minutes'
GROUP BY t.tenant_id, t.user_id, t.symbol, DATE_TRUNC('day', t.time);
```

📖 **Analytics Queries**: [/docs/architecture/END_TO_END_ARCHITECTURE.md](./docs/architecture/END_TO_END_ARCHITECTURE.md)

---

### 🔬 Data Enrichment Use Case: Broker Spread Comparison

**Purpose**: Analyze spread differences across brokers for research & user insights

#### Use Case 1: Real-time Spread Comparison
```sql
-- Compare spread across different brokers for same symbol (last 1 hour)
SELECT
    symbol,
    broker_metadata->>'broker_name' AS broker_name,
    broker_metadata->>'account_type' AS account_type,
    AVG(spread) * 10000 AS avg_spread_pips,
    MIN(spread) * 10000 AS min_spread_pips,
    MAX(spread) * 10000 AS max_spread_pips,
    STDDEV(spread) * 10000 AS spread_volatility_pips,
    COUNT(*) AS quote_count
FROM user_broker_quotes
WHERE time > NOW() - INTERVAL '1 hour'
    AND symbol = 'EUR/USD'
GROUP BY symbol, broker_metadata->>'broker_name', broker_metadata->>'account_type'
ORDER BY avg_spread_pips ASC;
```

**Output Example**:
```
symbol   | broker_name  | account_type | avg_spread_pips | min | max | volatility | quotes
---------|--------------|--------------|-----------------|-----|-----|------------|-------
EUR/USD  | IC Markets   | Raw Spread   | 0.12            | 0.1 | 0.3 | 0.05       | 3600
EUR/USD  | FXCM         | ECN          | 0.28            | 0.2 | 0.5 | 0.08       | 3600
EUR/USD  | XM           | Standard     | 1.85            | 1.5 | 2.5 | 0.25       | 3600
```

**Insight**: IC Markets Raw Spread has best execution cost (0.12 pips avg)

#### Use Case 2: Spread Stability Analysis
```sql
-- Which broker has most stable spread? (less volatility = better)
WITH spread_stats AS (
    SELECT
        broker_metadata->>'broker_name' AS broker_name,
        symbol,
        time_bucket('5 minutes', time) AS bucket,
        AVG(spread) * 10000 AS avg_spread_pips,
        STDDEV(spread) * 10000 AS spread_volatility
    FROM user_broker_quotes
    WHERE time > NOW() - INTERVAL '24 hours'
    GROUP BY broker_name, symbol, bucket
)
SELECT
    broker_name,
    symbol,
    AVG(avg_spread_pips) AS overall_avg_spread,
    AVG(spread_volatility) AS avg_volatility,
    MAX(spread_volatility) AS max_volatility_spike
FROM spread_stats
GROUP BY broker_name, symbol
ORDER BY avg_volatility ASC;
```

**Insight**: Lower volatility = more predictable execution cost

#### Use Case 3: Best Execution Time Analysis
```sql
-- When is spread tightest for each broker? (best time to trade)
SELECT
    broker_metadata->>'broker_name' AS broker_name,
    symbol,
    EXTRACT(HOUR FROM time) AS hour_of_day,
    AVG(spread) * 10000 AS avg_spread_pips,
    COUNT(*) AS quote_count
FROM user_broker_quotes
WHERE time > NOW() - INTERVAL '24 hours'
    AND symbol IN ('EUR/USD', 'GBP/USD', 'USD/JPY')
GROUP BY broker_name, symbol, hour_of_day
ORDER BY broker_name, symbol, avg_spread_pips ASC;
```

**Insight**: Identify best trading hours for each broker (lowest spread windows)

#### Use Case 4: Broker vs Polygon Price Difference
```sql
-- How different is broker price from Polygon reference?
WITH polygon_ref AS (
    SELECT
        symbol,
        time_bucket('1 minute', timestamp) AS bucket,
        AVG((bid + ask) / 2) AS polygon_mid_price
    FROM market_ticks
    WHERE timestamp > NOW() - INTERVAL '1 hour'
    GROUP BY symbol, bucket
),
broker_prices AS (
    SELECT
        user_id,
        broker_metadata->>'broker_name' AS broker_name,
        symbol,
        time_bucket('1 minute', time) AS bucket,
        AVG((bid + ask) / 2) AS broker_mid_price
    FROM user_broker_quotes
    WHERE time > NOW() - INTERVAL '1 hour'
    GROUP BY user_id, broker_name, symbol, bucket
)
SELECT
    b.broker_name,
    b.symbol,
    AVG(ABS(b.broker_mid_price - p.polygon_mid_price)) * 10000 AS avg_price_diff_pips,
    MAX(ABS(b.broker_mid_price - p.polygon_mid_price)) * 10000 AS max_price_diff_pips
FROM broker_prices b
INNER JOIN polygon_ref p
    ON b.symbol = p.symbol
    AND b.bucket = p.bucket
GROUP BY b.broker_name, b.symbol
ORDER BY avg_price_diff_pips ASC;
```

**Insight**: Quantify broker price deviation from market reference (slippage risk)

#### Materialized View: Broker Performance Dashboard
```sql
CREATE MATERIALIZED VIEW broker_performance_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS bucket,
    broker_metadata->>'broker_name' AS broker_name,
    broker_metadata->>'account_type' AS account_type,
    symbol,
    AVG(spread) * 10000 AS avg_spread_pips,
    STDDEV(spread) * 10000 AS spread_volatility_pips,
    COUNT(*) AS quote_count,
    AVG((bid + ask) / 2) AS avg_mid_price
FROM user_broker_quotes
GROUP BY bucket, broker_name, account_type, symbol;

-- Refresh policy: Update every 30 minutes
SELECT add_continuous_aggregate_policy('broker_performance_hourly',
    start_offset => INTERVAL '2 hours',
    end_offset => INTERVAL '30 minutes',
    schedule_interval => INTERVAL '30 minutes');
```

**Business Value**:
1. **User Insights**: Show users which broker offers best execution
2. **Research**: Understand broker behavior patterns
3. **Execution Quality**: Track and improve trade execution
4. **Broker Selection**: Help users choose optimal broker for their strategy

---

## 🎯 Data Routing Logic - HIGH vs LOW Frequency

### Decision Tree:

```
Data Type?
    │
    ├─ Price/Volume/Tick Data? ──→ HIGH FREQUENCY
    │                              ├─ Real-time? → TimescaleDB.market_ticks
    │                              └─ Historical? → ClickHouse.aggregates
    │
    ├─ Technical Indicators? ──→ MEDIUM FREQUENCY
    │                           └─ ClickHouse.ml_features (Wide Table)
    │
    ├─ ML Predictions? ──→ MEDIUM FREQUENCY
    │                     ├─ TimescaleDB.ml_predictions (90 days)
    │                     └─ DragonflyDB (cache 15 min)
    │
    ├─ User MT5 Data? ──→ MEDIUM FREQUENCY
    │                    └─ TimescaleDB (mt5_* tables)
    │
    └─ Economic/Sentiment Data? ──→ LOW FREQUENCY
                                   └─ PostgreSQL.market_context
```

📖 **Routing Guide**: [/00-data-ingestion/DATA_ROUTING_GUIDE.md](./00-data-ingestion/DATA_ROUTING_GUIDE.md)

---

## 📦 Performance & Retention Strategy

| Database | Purpose | Retention | Data Volume | Query Type |
|----------|---------|-----------|-------------|------------|
| **TimescaleDB** | Real-time data + user data | 90 days (market data)<br>24 hours (user quotes) | ~100 MB/day | OLTP (fast reads/writes) |
| **ClickHouse** | ML training data (wide table) | 10 years | ~50 MB/day | OLAP (analytical queries) |
| **DragonflyDB** | Cache layer + user execution | 15 min - 1h | In-memory | Key-Value (ultra fast) |
| **Weaviate** | Pattern similarity | Permanent | ~10 MB/day | Vector search |
| **PostgreSQL** | Metadata | Permanent | ~1 MB/day | OLTP (transactional) |

### Why This Strategy?

✅ **TimescaleDB (Primary)**: Fast ingestion untuk real-time + user data
   - Market data: 90 days retention (sufficient for ML training)
   - User broker quotes: 24 hours retention (execution + spread analysis)
   - Batch cleanup every 48 hours (efficient DELETE)

✅ **ClickHouse (Analytics)**: Denormalized wide table → 8x faster ML training
   - 10 years historical data for backtesting
   - Partitioned by month for efficient queries

✅ **DragonflyDB (Cache + Execution)**: Sub-millisecond response
   - System cache: Predictions, indicators (15 min - 1h TTL)
   - User broker quotes: Latest bid/ask for execution (1h TTL)
   - Purpose: Ultra-fast read for trade execution

✅ **Weaviate (Patterns)**: Find similar market patterns untuk better predictions

✅ **PostgreSQL (Metadata)**: Reliable storage untuk model versions & configs

📖 **Performance Analysis**: [/00-data-ingestion/_archived/external-data/COMPREHENSIVE_ARCHITECTURE_SUMMARY.md](./00-data-ingestion/_archived/external-data/COMPREHENSIVE_ARCHITECTURE_SUMMARY.md)

---

## 🔗 Documentation Shortcuts (Detailed Specs)

### 📘 Data Ingestion
- [Data Routing Guide](./00-data-ingestion/DATA_ROUTING_GUIDE.md) - Complete routing logic
- [Schema Verification](./00-data-ingestion/DATA_SCHEMA_VERIFICATION.md) - Collector output validation
- [Polygon Live Collector](./00-data-ingestion/polygon-live-collector/) - Real-time implementation
- [Historical Downloader](./00-data-ingestion/polygon-historical-downloader/) - Backfill implementation
- [Hybrid Schema (Archived)](./00-data-ingestion/_archived/external-data/database/database_schema_hybrid.sql) - Original 2-table design

### 📗 ML/DL Pipeline
- [ML Pipeline Summary](./03-ml-pipeline/IMPLEMENTATION_SUMMARY.md) - Complete ML architecture
- [ClickHouse ml_features Schema](./03-ml-pipeline/schemas/01_clickhouse_ml_features.sql) - Wide table (100+ columns)
- [TimescaleDB Predictions Schema](./03-ml-pipeline/schemas/03_timescaledb_predictions.sql) - Prediction results
- [PostgreSQL Metadata Schema](./03-ml-pipeline/schemas/04_postgresql_metadata.sql) - Model metadata
- [Feature Engineering](./03-ml-pipeline/02-feature-engineering/) - Indicator calculation

### 📙 Core Infrastructure
- [End-to-End Architecture](./docs/architecture/END_TO_END_ARCHITECTURE.md) - Complete system design
- [Data Manager Spec](./01-core-infrastructure/central-hub/DATA_MANAGER_SPEC.md) - Smart routing layer
- [Central Hub SDK](./01-core-infrastructure/central-hub/sdk/) - Service coordination
- [API Gateway](./01-core-infrastructure/api-gateway/) - Entry point

### 📕 MT5 Integration
- [MT5 User Schemas](./docs/architecture/END_TO_END_ARCHITECTURE.md#L1511-L1570) - User data tables
- [Comparison Analytics](./docs/architecture/END_TO_END_ARCHITECTURE.md) - System vs User queries

---

## ✅ Implementation Status

| Component | Status | Database | Schema Ready | Writer Ready |
|-----------|--------|----------|--------------|--------------|
| **Polygon Live → Ticks** | ✅ Production | TimescaleDB | ✅ | ✅ |
| **Polygon Historical → Aggregates** | ✅ Production | ClickHouse | ✅ | ✅ |
| **User Broker Quotes (Hybrid)** | ⚠️ Schema Ready | DragonflyDB + TimescaleDB | ✅ | ❌ |
| **Feature Engineering → ml_features** | ⚠️ In Progress | ClickHouse | ✅ | ⚠️ |
| **ML Training → Models** | ⚠️ In Progress | S3 + PostgreSQL | ✅ | ⚠️ |
| **ML Inference → Predictions** | ⚠️ In Progress | TimescaleDB | ✅ | ⚠️ |
| **MT5 User Data → TimescaleDB** | ❌ Planned | TimescaleDB | ✅ | ❌ |
| **External Collector → Context** | ❌ Planned | PostgreSQL | ✅ | ❌ |

---

## 🎯 Next Steps - Implementation Priority

### Priority 1: Complete Feature Engineering
- [ ] Build Feature Engineer Service
- [ ] Connect to ClickHouse.ml_features
- [ ] Implement 100+ indicator calculations
- [ ] Add multi-horizon label generation

### Priority 2: ML/DL Training Pipeline
- [ ] Build Model Training Service
- [ ] Integrate with ClickHouse.ml_features
- [ ] Save models to S3
- [ ] Track metadata in PostgreSQL

### Priority 3: ML Inference Pipeline
- [ ] Build Inference Service
- [ ] Real-time feature computation
- [ ] Weaviate pattern matching
- [ ] Save predictions to TimescaleDB

### Priority 4: MT5 User Integration
- [ ] Build MT5 API Collector
- [ ] Implement user data ingestion
- [ ] Create comparison analytics
- [ ] Build performance dashboards

---

**Last Updated**: 2025-10-06
**Status**: Documentation Complete - Core Implementation In Progress
**Architecture Version**: 2.1 (Hybrid 5-Database Strategy + User Broker Quotes)
**Latest Addition**: User's Broker Quotes (Hybrid Storage: DragonflyDB + TimescaleDB) with Data Enrichment (Spread Comparison Analysis)
