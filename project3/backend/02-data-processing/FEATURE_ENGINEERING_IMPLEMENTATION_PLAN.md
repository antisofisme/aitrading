# Feature Engineering Service - Implementation Plan

**Version:** 2.0.0 (Redirected to Main Strategy)
**Created:** 2025-10-06
**Updated:** 2025-10-08
**Purpose:** Phase 1 verification tasks, Phase 2+ see main strategy document

---

## 📢 IMPORTANT NOTICE

**For Phase 2 onwards (Feature Engineering Design, Implementation, ML Training, etc.):**

👉 **SEE MAIN STRATEGY DOCUMENT:**
📄 [TRADING_STRATEGY_AND_ML_DESIGN.md](./TRADING_STRATEGY_AND_ML_DESIGN.md)

**This document contains ONLY Phase 1 (Foundation Verification).**

All subsequent phases are documented in the main strategy document to avoid conflicting information.

---

## 📋 **PHASE 1: Foundation Verification** ⚠️

**Duration:** 1 day
**Status:** CURRENT PHASE
**Purpose:** Verify data pipeline working correctly before feature engineering

---

### **Task 1.1: Verify Tick Aggregator Data**

**Checklist:**
- [ ] Check `aggregates` table in ClickHouse exists
- [ ] Verify 6 timeframes present: **M5, M15, H1, H4, D1, W1**
- [ ] Verify 10 pairs data flowing (EURUSD, GBPUSD, XAUUSD, etc.)
- [ ] Confirm `indicators` JSON column populated
- [ ] Test parse indicators JSON: Extract RSI, MACD, SMA values

**SQL Test Query:**
```sql
-- Check table exists and timeframes
SELECT
    timeframe,
    COUNT(*) as count,
    MIN(timestamp) as first_candle,
    MAX(timestamp) as latest_candle
FROM aggregates
WHERE symbol = 'EUR/USD'
GROUP BY timeframe
ORDER BY timeframe;

-- Expected output: M5, M15, H1, H4, D1, W1

-- Test JSON indicators parsing
SELECT
    symbol,
    timeframe,
    timestamp,
    JSONExtractFloat(indicators, 'rsi') as rsi,
    JSONExtractFloat(indicators, 'macd') as macd,
    JSONExtractFloat(indicators, 'sma_14') as sma_14
FROM aggregates
WHERE symbol = 'EUR/USD'
  AND timeframe = '1h'
  AND timestamp >= now() - INTERVAL 1 DAY
LIMIT 10;

-- Expected: Non-zero values for indicators
```

**Validation Criteria:**
- ✅ All 6 timeframes present (M5, M15, H1, H4, D1, W1)
- ✅ Indicators column populated (not empty strings)
- ✅ JSON parsing works (no NULL values)
- ✅ Data freshness < 1 hour (for recent candles)

---

### **Task 1.2: Verify External Data Sources**

**Checklist:**
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

**SQL Test Queries:**
```sql
-- Check all external tables exist
SHOW TABLES LIKE 'external_%';

-- Expected: 6 tables

-- Check data freshness for each table
SELECT
    'economic_calendar' as table_name,
    COUNT(*) as count,
    MAX(collected_at) as latest
FROM external_economic_calendar
UNION ALL
SELECT
    'fred_economic',
    COUNT(*),
    MAX(collected_at)
FROM external_fred_economic
UNION ALL
SELECT
    'crypto_sentiment',
    COUNT(*),
    MAX(collected_at)
FROM external_crypto_sentiment
UNION ALL
SELECT
    'fear_greed_index',
    COUNT(*),
    MAX(collected_at)
FROM external_fear_greed_index
UNION ALL
SELECT
    'commodity_prices',
    COUNT(*),
    MAX(collected_at)
FROM external_commodity_prices
UNION ALL
SELECT
    'market_sessions',
    COUNT(*),
    MAX(collected_at)
FROM external_market_sessions
ORDER BY table_name;

-- Expected: Latest timestamp within last 24 hours for all tables
```

**Validation Criteria:**
- ✅ All 6 tables exist
- ✅ Data freshness < 24 hours
- ✅ No critical gaps in economic calendar
- ✅ Reasonable row counts (not empty)

---

### **Task 1.3: Verify Historical Data (5 Years)**

**NEW - Critical for Phase 2:**
- [ ] Verify historical data availability: 2020-2024 (5 years)
- [ ] Check XAUUSD (Gold) data completeness
- [ ] Estimate total rows for training

**SQL Test Query:**
```sql
-- Check historical data range for Gold (primary pair)
SELECT
    symbol,
    timeframe,
    COUNT(*) as total_candles,
    MIN(timestamp) as first_date,
    MAX(timestamp) as last_date,
    DATE_DIFF('day', MIN(timestamp), MAX(timestamp)) as days_coverage
FROM aggregates
WHERE symbol = 'XAU/USD'
GROUP BY symbol, timeframe
ORDER BY timeframe;

-- Expected for H1: ~43,800 candles (5 years × 365 × 24)
```

**Validation Criteria:**
- ✅ Gold (XAUUSD) data from 2020-01-01 minimum
- ✅ H1 timeframe: ~40,000+ candles (5 years)
- ✅ <5% data gaps (missing candles)
- ✅ All 6 timeframes have historical data

---

### **Task 1.4: Update ClickHouse Schema (if needed)**

**Checklist:**
- [ ] Verify `aggregates.indicators` column type is String/JSON
- [ ] Check indexes on (symbol, timeframe, timestamp)
- [ ] Document current schema structure
- [ ] Validate ReplacingMergeTree for external tables

**SQL Test Query:**
```sql
-- Show aggregates table schema
SHOW CREATE TABLE aggregates;

-- Show external_economic_calendar schema (should be ReplacingMergeTree)
SHOW CREATE TABLE external_economic_calendar;
```

**Expected Schema Features:**
- ✅ `indicators` column type: String (for JSON)
- ✅ Index on (symbol, timeframe, timestamp)
- ✅ TTL policy configured
- ✅ External tables use ReplacingMergeTree (for deduplication)

---

## 📊 **DELIVERABLE: Foundation Verification Report**

**Report Contents:**

### **1. Data Availability Summary**
```yaml
Aggregates Table:
  Total Symbols: 10
  Timeframes: [M5, M15, H1, H4, D1, W1]
  Historical Range: 2020-01-01 to 2024-10-08
  Total Candles (XAUUSD H1): 43,800
  Data Quality: 98.5% (1.5% gaps)

External Data:
  Economic Calendar: 1,200+ events (last 30 days)
  FRED Economic: 15 indicators updated
  Crypto Sentiment: 10 coins tracked
  Fear & Greed: Daily updates
  Commodity Prices: Gold, Oil tracked
  Market Sessions: 4 sessions defined
```

### **2. Data Quality Issues (if any)**
- Missing candles: [list dates/times]
- NULL indicators: [list symbols/timeframes]
- Stale external data: [list sources]
- Schema mismatches: [list issues]

### **3. Recommendations**
- ✅ Ready for Phase 2 (if all criteria met)
- ⚠️ Fix issues before proceeding (if critical gaps found)
- 📋 Backfill historical data (if needed)

---

## 🔗 **NEXT STEPS**

### **After Phase 1 Verification Passes:**

👉 **GO TO:** [TRADING_STRATEGY_AND_ML_DESIGN.md](./TRADING_STRATEGY_AND_ML_DESIGN.md)

**Sections to follow:**
- **Week 2: Feature Engineering Design** (63 features definition)
- **Week 3-4: Implementation** (Feature calculators)
- **Week 5: ML Training** (XGBoost with 5 years data)
- **Week 6-7: Backtesting** (Structure-based SL/TP)
- **Week 8-11: Paper Trading** (Real-time validation)
- **Week 12+: Live Trading** (Micro lot start)

---

## 📌 **DECISION LOG**

### **2025-10-08: Redirected to Main Strategy**
- Kept Phase 1 (Foundation Verification) in this document
- Phase 2+ redirected to TRADING_STRATEGY_AND_ML_DESIGN.md
- Reason: Avoid conflicting information across multiple docs
- Single source of truth for strategy and implementation

### **2025-10-06: Initial Creation**
- Original implementation plan created
- Target: 70-90 features
- Now superseded by revised strategy (63 features, multi-timeframe)

---

**STATUS:** Phase 1 Active - Foundation Verification

**SEE MAIN STRATEGY:** [TRADING_STRATEGY_AND_ML_DESIGN.md](./TRADING_STRATEGY_AND_ML_DESIGN.md)

---

*This document focuses on Phase 1 only. All subsequent phases are in the main strategy document.*
