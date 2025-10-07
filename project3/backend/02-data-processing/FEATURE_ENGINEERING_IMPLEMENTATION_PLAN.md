# Feature Engineering Service - Implementation Plan

**Version:** 1.0.0
**Created:** 2025-10-06
**Purpose:** Transform raw aggregates + external data → ML-ready training dataset
**Target:** High-quality ML features with 70-80% accuracy potential

---

## 🎯 **OBJECTIVES**

### **Primary Goal:**
Create a Feature Engineering Service that combines:
- ✅ 26 technical indicators (from Tick Aggregator)
- ✅ 8-10 external market features (from External Data Collector)
- 🔄 20-30 engineered features (lag, cross-pair, volatility, volume)
- 🔄 3-5 target variables (for different ML models)

**Total: 70-90 features per candle for ML training**

### **Why Option 3 (Feature Engineering Service)?**

**Advantages over other options:**
1. ✅ **Prevents data leakage** - No future data in training
2. ✅ **Handles missing data properly** - Forward-fill with validation
3. ✅ **Enables lag features** - Historical context for ML
4. ✅ **Cross-pair correlation** - Market structure analysis
5. ✅ **Advanced target engineering** - Realistic trading targets
6. ✅ **Reproducible & versioned** - Track model improvements
7. ✅ **15-20% higher accuracy** - Better feature quality

---

## 📋 **IMPLEMENTATION PHASES**

### **PHASE 1: Foundation Verification (1 day)** ⚠️

#### **Task 1.1: Verify Tick Aggregator Data**
- [ ] Check `aggregates` table in ClickHouse exists
- [ ] Verify 7 timeframes present (5m, 15m, 30m, 1h, 4h, 1d, 1w)
- [ ] Verify 10 pairs data flowing (EURUSD, GBPUSD, XAUUSD, etc.)
- [ ] Confirm `indicators` JSON column populated
- [ ] Test parse indicators JSON: Extract RSI, MACD, SMA values

**SQL Test Query:**
```sql
SELECT
    symbol,
    timeframe,
    timestamp,
    JSONExtractFloat(indicators, 'rsi') as rsi,
    JSONExtractFloat(indicators, 'macd') as macd
FROM aggregates
WHERE symbol = 'EUR/USD'
  AND timeframe = '1h'
  AND timestamp >= now() - INTERVAL 1 DAY
LIMIT 10;
```

#### **Task 1.2: Verify External Data Sources**
- [ ] Check 6 external tables exist:
  - `external_economic_calendar`
  - `external_fred_economic`
  - `external_crypto_sentiment`
  - `external_fear_greed_index`
  - `external_commodity_prices`
  - `external_market_sessions`
- [ ] Verify update frequencies match config
- [ ] Check data freshness (last insert timestamp)
- [ ] Identify data gaps or missing periods

#### **Task 1.3: Update ClickHouse Schema (if needed)**
- [ ] Verify `aggregates.indicators` column type is String/JSON
- [ ] Add index on (symbol, timeframe, timestamp) if not exists
- [ ] Document current schema structure

**Deliverable:** Foundation Verification Report (data quality, coverage, gaps)

---

### **PHASE 2: Feature & Schema Design (2-3 days)** 🔄

#### **Task 2.1: Finalize Feature List**

**A. Technical Indicators (26 features) ✅ DONE**
```yaml
Moving Averages:
  - sma_7, sma_14, sma_21, sma_50, sma_200
  - ema_7, ema_14, ema_21, ema_50, ema_200

Momentum:
  - rsi
  - macd, macd_signal, macd_histogram
  - stoch_k, stoch_d
  - mfi, cci

Volume:
  - obv, adl, vwap

Volatility:
  - bb_middle, bb_upper, bb_lower, bb_width
  - atr
```

**B. External Features (8-10 features) 🔄 TO DESIGN**
- [ ] Define economic event feature: `upcoming_high_impact_events` (count in next 4h)
- [ ] Define FRED features: `gdp_value`, `unemployment_rate`, `cpi_value` (latest values)
- [ ] Define sentiment: `fear_greed_index` (0-100), `fear_greed_classification`
- [ ] Define commodities: `gold_price`, `oil_price`, `gold_oil_ratio`
- [ ] Define sessions: `active_sessions_count`, `liquidity_level_score` (1-5)

**C. Lag Features (15-20 features) 🔄 TO DESIGN**
```yaml
Price Lags:
  - close_lag_1, close_lag_3, close_lag_6, close_lag_12
  - pct_change_1, pct_change_3, pct_change_6

Indicator Lags:
  - rsi_lag_1, rsi_lag_3, rsi_change
  - macd_lag_1, macd_change
  - atr_lag_1, atr_change

External Lags:
  - fear_greed_change_1d
  - gold_price_change_3h
  - oil_price_change_6h
```

**D. Cross-Pair Features (10-15 features) 🔄 TO DESIGN**
```yaml
USD Strength:
  - usd_strength_index: avg(USDJPY, USDCAD) - avg(EURUSD, GBPUSD)

Pair Ratios:
  - eurusd_gbpusd_ratio
  - audjpy_risk_indicator (risk-on/risk-off proxy)

Cross-pair Indicators:
  - eurusd_rsi - gbpusd_rsi (divergence)
  - eurusd_macd - usdjpy_macd
```

**E. Volatility Features (5-10 features) 🔄 TO DESIGN**
```yaml
Rolling Volatility:
  - volatility_1h (std of returns)
  - volatility_4h, volatility_24h
  - volatility_ratio (current vs 24h avg)

Range Measures:
  - range_pct (high-low / close)
  - body_pct (abs(close-open) / close)
```

**F. Volume Features (3-5 features) 🔄 TO DESIGN**
```yaml
Volume Analysis:
  - volume_ma_20 (20-period MA)
  - volume_ratio (current / MA)
  - volume_surge (boolean: volume > 2x MA)
```

#### **Task 2.2: Define Target Variables**

- [ ] **Binary Classification:**
  - `target_up_down`: 0 = down, 1 = up (next candle)
  - `target_profitable`: 1 if next_close - current_close > spread

- [ ] **Multi-class Classification:**
  - `target_movement`: -2 (strong down), -1 (weak down), 0 (sideways), 1 (weak up), 2 (strong up)

- [ ] **Regression:**
  - `target_close_next`: Next candle close price
  - `target_pips_change`: Next candle change in pips

- [ ] **Time-based:**
  - `bars_to_10pips`: How many candles to reach 10 pips profit
  - `max_profit_next_6h`: Maximum achievable profit in next 6 hours

**Decision:** Start with 3 targets: `target_up_down`, `target_profitable`, `target_pips_change`

#### **Task 2.3: Design ClickHouse Table Schema**

**Table: `ml_training_data`**

- [ ] Define column list (70-90 columns)
- [ ] Choose partitioning: `PARTITION BY toYYYYMM(timestamp)`
- [ ] Define primary key: `ORDER BY (symbol, timeframe, timestamp)`
- [ ] Set TTL: `TTL timestamp + INTERVAL 2 YEAR`
- [ ] Choose column types:
  - DateTime for timestamps
  - Float64 for prices, indicators, ratios
  - UInt8 for categorical (0-5 range)
  - String for JSON (if needed for metadata)

**Schema Template:**
```sql
CREATE TABLE ml_training_data (
    -- Metadata
    timestamp DateTime,
    symbol String,
    timeframe String,

    -- OHLCV
    open Float64,
    high Float64,
    low Float64,
    close Float64,
    volume UInt64,

    -- Technical Indicators (26)
    rsi Float64,
    macd Float64,
    macd_signal Float64,
    -- ... 23 more indicators

    -- External Features (10)
    upcoming_high_impact_events UInt16,
    fear_greed_index Float64,
    gold_price Float64,
    -- ... 7 more external

    -- Lag Features (20)
    close_lag_1 Float64,
    rsi_lag_1 Float64,
    -- ... 18 more lags

    -- Cross-Pair Features (10)
    usd_strength_index Float64,
    eurusd_gbpusd_ratio Float64,
    -- ... 8 more cross-pair

    -- Volatility Features (8)
    volatility_1h Float64,
    volatility_24h Float64,
    -- ... 6 more volatility

    -- Volume Features (5)
    volume_ma_20 Float64,
    volume_ratio Float64,
    -- ... 3 more volume

    -- Target Variables (3-5)
    target_up_down UInt8,
    target_profitable UInt8,
    target_pips_change Float64,

    -- Quality Metadata
    data_quality_score Float32,
    missing_features_count UInt16,
    created_at DateTime DEFAULT now()

) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, timeframe, timestamp)
TTL timestamp + INTERVAL 2 YEAR;
```

**Deliverable:** Feature Specification Document + ClickHouse Schema DDL

---

### **PHASE 3: Service Architecture Design (2 days)** 🔄

#### **Task 3.1: Define Service Components**

**Component 1: Aggregates Fetcher**
- [ ] Design: Query ClickHouse `aggregates` table
- [ ] Input: date_range, symbols, timeframes
- [ ] Processing: Parse indicators JSON → separate columns
- [ ] Output: pandas DataFrame with OHLCV + 26 indicators

**Component 2: External Data Fetcher**
- [ ] Design: Query 6 external tables
- [ ] Processing:
  - Merge on timestamp (nearest match)
  - Forward-fill missing values
  - Handle timezone alignment
- [ ] Output: pandas DataFrame with 10 external features

**Component 3: Feature Engineer**
- [ ] Design: Merge aggregates + external
- [ ] Processing:
  - Calculate lag features (shift operations)
  - Calculate cross-pair features (multi-symbol merge)
  - Calculate volatility features (rolling std)
  - Calculate volume features (rolling MA)
  - Calculate target variables (shift future values)
  - Data quality validation (check NaN, outliers)
- [ ] Output: pandas DataFrame with 70-90 features

**Component 4: ClickHouse Writer**
- [ ] Design: Batch insert to `ml_training_data`
- [ ] Processing:
  - Batch size: 10,000 rows
  - Deduplication: ON CONFLICT (symbol, timeframe, timestamp) UPDATE
  - Error handling: Log failed batches
- [ ] Output: Insertion stats (rows inserted, errors)

**Component 5: Main Orchestrator**
- [ ] Design: Coordinate 4 workers
- [ ] Modes:
  - Historical Backfill (process months of data)
  - Incremental Update (process last 24h)
  - On-Demand (custom date range)
- [ ] Scheduling: APScheduler (hourly/daily cron)
- [ ] Error handling: Retry logic, alerts

#### **Task 3.2: Define Execution Modes**

**Mode 1: Historical Backfill**
- [ ] Purpose: Generate training data for past 6-12 months
- [ ] Parameters:
  - start_date: '2024-01-01'
  - end_date: '2025-10-06'
  - symbols: ['EURUSD', 'GBPUSD', ...]
  - timeframes: ['1h', '4h', '1d']
  - batch_size: 1 month chunks
- [ ] Process: Sequential batch processing with progress tracking

**Mode 2: Incremental Update**
- [ ] Purpose: Daily/hourly updates with fresh candles
- [ ] Parameters:
  - lookback: 24 hours (process recent data only)
  - symbols: ['EURUSD', 'GBPUSD', ...]
  - timeframes: ['1h', '4h']
  - schedule: Cron "0 */1 * * *" (every hour)
- [ ] Process: Scheduled job, idempotent (safe to re-run)

**Mode 3: On-Demand**
- [ ] Purpose: Custom dataset for experiments
- [ ] Interface: CLI command or HTTP API endpoint
- [ ] Parameters: Fully customizable
- [ ] Process: Synchronous execution with immediate response

#### **Task 3.3: Data Quality Checks**

**Check 1: Missing Data Detection**
- [ ] Logic: Calculate NULL percentage per feature
- [ ] Threshold: Warn if > 5% NULL
- [ ] Action: Log warning + continue (forward-fill handles it)

**Check 2: Data Leakage Prevention**
- [ ] Logic: Verify external data timestamp <= candle timestamp
- [ ] Threshold: Zero tolerance
- [ ] Action: Error + stop processing

**Check 3: Outlier Detection**
- [ ] Logic: Values beyond 3 standard deviations
- [ ] Threshold: Flag rows with >5 outlier features
- [ ] Action: Log for manual review

**Check 4: Feature Correlation**
- [ ] Logic: Pearson correlation > 0.95 between feature pairs
- [ ] Threshold: Warn if highly correlated features found
- [ ] Action: Document for feature selection phase

**Deliverable:** Architecture Design Document + Component Specifications

---

### **PHASE 4: Implementation (5-7 days)** 🔄

#### **Task 4.1: Setup Project Structure**
```
/project3/backend/02-data-processing/feature-engineering-service/
├── src/
│   ├── main.py                    # Main orchestrator
│   ├── aggregates_fetcher.py      # Component 1
│   ├── external_fetcher.py        # Component 2
│   ├── feature_engineer.py        # Component 3
│   ├── clickhouse_writer.py       # Component 4
│   └── utils/
│       ├── data_quality.py        # Quality checks
│       ├── timestamp_utils.py     # Timezone handling
│       └── config_loader.py       # Config management
├── config/
│   └── features.yaml              # Feature definitions
├── tests/
│   ├── test_lag_features.py
│   ├── test_cross_pair.py
│   ├── test_data_quality.py
│   └── test_integration.py
├── Dockerfile
├── requirements.txt
└── README.md
```

#### **Task 4.2: Implement Core Components**

- [ ] **Step 1:** Implement Aggregates Fetcher
  - Query ClickHouse with date range filter
  - Parse indicators JSON
  - Return clean DataFrame

- [ ] **Step 2:** Implement External Data Fetcher
  - Query 6 external tables
  - Merge on timestamp with pd.merge_asof
  - Forward-fill missing values

- [ ] **Step 3:** Implement Feature Engineer
  - Lag features: `df['close_lag_1'] = df['close'].shift(1)`
  - Cross-pair: Merge multiple symbols, calculate ratios
  - Volatility: `df['volatility_1h'] = df['close'].pct_change().rolling(60).std()`
  - Volume: `df['volume_ratio'] = df['volume'] / df['volume'].rolling(20).mean()`
  - Target: `df['target_next'] = df['close'].shift(-1)`

- [ ] **Step 4:** Implement ClickHouse Writer
  - Batch insert with clickhouse_connect
  - Handle duplicates with REPLACE INTO or ON CONFLICT

- [ ] **Step 5:** Implement Main Orchestrator
  - Coordinate execution flow
  - Add APScheduler for cron jobs
  - Add logging & error handling

#### **Task 4.3: Add Data Quality Module**

- [ ] Implement missing data detection
- [ ] Implement outlier detection
- [ ] Implement data leakage check
- [ ] Add quality score calculation

**Deliverable:** Working Feature Engineering Service

---

### **PHASE 5: Testing & Validation (2-3 days)** 🔄

#### **Task 5.1: Unit Tests**

- [ ] **Test Lag Features:**
  ```python
  def test_lag_features():
      df = pd.DataFrame({'close': [1, 2, 3, 4, 5]})
      df['close_lag_1'] = df['close'].shift(1)
      assert df['close_lag_1'].tolist() == [np.nan, 1, 2, 3, 4]
  ```

- [ ] **Test Forward-Fill:**
  ```python
  def test_forward_fill():
      df = pd.DataFrame({'value': [1, np.nan, np.nan, 2, np.nan]})
      df['value'].fillna(method='ffill', inplace=True)
      assert df['value'].tolist() == [1, 1, 1, 2, 2]
  ```

- [ ] **Test Target Variable:**
  ```python
  def test_target_variable():
      df = pd.DataFrame({'close': [1.0850, 1.0855, 1.0860]})
      df['target_next'] = df['close'].shift(-1)
      assert df['target_next'].tolist()[0] == 1.0855
  ```

#### **Task 5.2: Integration Tests**

- [ ] **End-to-End Test:**
  1. Run service for 1 day of data (EURUSD, 1h)
  2. Verify ml_training_data has 24 rows
  3. Check all 70-90 columns present
  4. Verify no NULL in critical features
  5. Check target variables aligned correctly

- [ ] **Data Quality Test:**
  1. Load 100 sample rows
  2. Check feature distributions
  3. Verify no extreme outliers
  4. Confirm timestamp ordering

#### **Task 5.3: Historical Backfill Test**

- [ ] Run backfill for 1 month (January 2024)
- [ ] Expected rows: 10 pairs x 720 hours = 7,200 rows (1h timeframe)
- [ ] Verify completion without errors
- [ ] Check data quality scores

**Deliverable:** Test Suite + Validation Report

---

### **PHASE 6: Deployment & Documentation (2-3 days)** 🔄

#### **Task 6.1: Containerization**

- [ ] Create Dockerfile
  ```dockerfile
  FROM python:3.11-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install -r requirements.txt
  COPY src/ ./src/
  CMD ["python", "src/main.py"]
  ```

- [ ] Build & test container locally
- [ ] Push to container registry (optional)

#### **Task 6.2: Deployment**

- [ ] Deploy container to server
- [ ] Configure environment variables (ClickHouse credentials)
- [ ] Setup cron job or systemd service for incremental updates
- [ ] Configure monitoring (logs, metrics)

#### **Task 6.3: Historical Backfill**

- [ ] Run historical backfill: January 2024 - October 2025
- [ ] Expected rows: ~150,000 (10 pairs x 12 months x 720 hours/month)
- [ ] Monitor progress & handle errors
- [ ] Validate final dataset quality

#### **Task 6.4: Documentation**

**Feature Documentation:**
- [ ] Document all 70-90 features (name, formula, source, range)
- [ ] Document target variables (formula, use case)
- [ ] Document data quality thresholds

**Operations Runbook:**
- [ ] How to run historical backfill
- [ ] How to run incremental update
- [ ] How to add new features
- [ ] How to troubleshoot failures
- [ ] How to query ml_training_data for ML training

**Schema Documentation:**
- [ ] Table DDL with comments
- [ ] Sample queries for ML frameworks (PyTorch, TensorFlow, scikit-learn)
- [ ] Performance optimization tips

**Deliverable:** Production-ready Feature Engineering Service + Complete Documentation

---

## 📊 **TIMELINE SUMMARY**

| Phase | Duration | Status |
|-------|----------|--------|
| Phase 1: Foundation Verification | 1 day | ⚠️ Pending |
| Phase 2: Feature & Schema Design | 2-3 days | 🔄 To Do |
| Phase 3: Architecture Design | 2 days | 🔄 To Do |
| Phase 4: Implementation | 5-7 days | 🔄 To Do |
| Phase 5: Testing & Validation | 2-3 days | 🔄 To Do |
| Phase 6: Deployment & Documentation | 2-3 days | 🔄 To Do |
| **TOTAL** | **14-19 days (2-3 weeks)** | 🔄 In Planning |

---

## ✅ **SUCCESS CRITERIA**

### **Technical Metrics:**
- ✅ 70-90 features generated per candle
- ✅ <5% missing data across all features
- ✅ Zero data leakage (no future data in training)
- ✅ <1% outlier rate
- ✅ 99.9% uptime for incremental updates

### **ML Performance Metrics:**
- 🎯 Model accuracy: 70-80% (target)
- 🎯 Precision: >65% (minimize false positives)
- 🎯 Recall: >65% (capture true signals)
- 🎯 F1-Score: >65%

### **Operational Metrics:**
- ✅ Historical backfill: <24 hours for 12 months
- ✅ Incremental update: <5 minutes per run
- ✅ Storage: <10GB per year of data
- ✅ Query performance: <1 second for 1 month data

---

## 🚨 **RISKS & MITIGATIONS**

### **Risk 1: Data Leakage**
- **Impact:** High - Model unusable in production
- **Mitigation:** Strict timestamp validation, unit tests for future data

### **Risk 2: Missing External Data**
- **Impact:** Medium - Features with NULL values
- **Mitigation:** Forward-fill strategy, data quality alerts

### **Risk 3: Cross-Pair Synchronization**
- **Impact:** Medium - Misaligned timestamps between pairs
- **Mitigation:** Use pd.merge_asof with tolerance parameter

### **Risk 4: Storage Growth**
- **Impact:** Low - Disk space issues
- **Mitigation:** TTL policy (2 years), compression (LZ4)

### **Risk 5: Performance Bottleneck**
- **Impact:** Medium - Slow feature engineering
- **Mitigation:** Batch processing, parallel execution for multiple symbols

---

## 📝 **NOTES & DECISIONS LOG**

### **2025-10-06: Initial Plan Created**
- Decision: Use Option 3 (Feature Engineering Service) for best ML quality
- Decision: Target 70-90 features (26 technical + 10 external + 30 engineered)
- Decision: Start with 3 target variables (up_down, profitable, pips_change)
- Decision: 1h, 4h, 1d timeframes for initial implementation (5m, 15m, 30m later)

### **Next Review:** After Phase 1 Completion
- Review data quality findings
- Adjust feature list based on NULL percentage
- Finalize target variables based on data distribution

---

## 🔗 **RELATED DOCUMENTS**

- [Technical Indicators Implementation](./tick-aggregator/src/technical_indicators.py)
- [External Data Types](../00-data-ingestion/external-data-collector/DATA_TYPES.md)
- [Data Flow Architecture](../00-data-ingestion/COMPLETE_DATA_FLOW.md)
- [Indicator Framework Analysis](../../docs/analysis/indicator-framework-analysis.md)

---

## 👥 **TEAM & RESPONSIBILITIES**

- **Data Engineer:** Phase 1-3 (Design & Architecture)
- **ML Engineer:** Phase 2 (Feature selection & target variables)
- **Backend Developer:** Phase 4 (Implementation)
- **QA Engineer:** Phase 5 (Testing & Validation)
- **DevOps:** Phase 6 (Deployment & Monitoring)

---

**END OF IMPLEMENTATION PLAN**

*This is a living document. Update as implementation progresses.*
