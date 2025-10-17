# 🔧 Database Process Tables - Feature Engineering Service

> **Version**: 2.0.0 (Complete Redesign)
> **Last Updated**: 2025-10-17
> **Status**: Complete - Ready for Implementation

---

## 📋 Overview

**Purpose**: Dokumentasi untuk tabel-tabel yang dihasilkan oleh **Feature Engineering Service**

**Input**: Data dari `table_database_input.md` (aggregates, external data)
**Output**: ML-ready features untuk training dan inference (110 features)

---

## 🎯 Feature Engineering Service

**Service Name**: `feature-engineering-service`
**Function**: Transform aggregated data → ML features (110 features untuk MVP)
**Flow**:
```
Input Tables (ClickHouse)
    ↓
Feature Engineering Service
    ↓
ml_features Table (110 derived features) ← NOT including raw OHLC
    ↓
ML Training/Inference (JOIN dengan aggregates untuk raw data)
```

---

## ⚠️ CRITICAL ARCHITECTURE DECISION

### **ml_features Table TIDAK Menyimpan Raw Data**

**Rationale**: Avoid duplication & maintain single source of truth

```
❌ OLD DESIGN (v1.0):
ml_features table stores:
├── OHLC (open, high, low, close)     ← DUPLICATE!
├── tick_count                        ← DUPLICATE!
├── Derived features (RSI, MACD, etc) ← OK

✅ NEW DESIGN (v2.0):
ml_features table stores:
└── ONLY derived features (RSI, MACD, lagged, rolling, etc)

aggregates table (source of truth):
├── OHLC
├── tick_count
└── spreads, volatility

ML Training/Inference:
SELECT
    a.time, a.symbol, a.timeframe,
    a.open, a.high, a.low, a.close,    ← From aggregates
    a.tick_count, a.avg_spread,         ← From aggregates
    f.*                                  ← From ml_features (110 columns)
FROM aggregates a
LEFT JOIN ml_features f
    ON a.time = f.time
    AND a.symbol = f.symbol
    AND a.timeframe = f.timeframe
WHERE a.time >= '2023-01-01'
```

**Benefits**:
- ✅ No data duplication
- ✅ Single source of truth (aggregates)
- ✅ Aggregates can be used independently
- ✅ Easier to maintain (update OHLC once)

---

## 📊 Output Table Structure

### **Table: ml_features** (110 Derived Features)

**Purpose**: Store ONLY derived/calculated features (not raw data)

**Storage**: ClickHouse
**Update Frequency**: Real-time (new candles) + Batch (historical backfill)
**Retention**:
- Historical: Unlimited (for training)
- Live: 30 days (for inference)

---

## 📐 Schema Structure (110 Features)

### **1. Primary Keys & Metadata** (5 columns)
```sql
CREATE TABLE suho_analytics.ml_features
(
    -- Primary identifiers
    time DateTime64(3, 'UTC'),           -- Feature timestamp (same as candle time)
    symbol String,                        -- C:EURUSD, C:XAUUSD, dll
    timeframe Enum8('5m'=1, '15m'=2, '30m'=3, '1h'=4,
                    '4h'=5, '1d'=6, '1w'=7),

    -- Metadata
    feature_version String,               -- Version tracking (e.g., "v2.0")
    created_at DateTime64(3, 'UTC'),      -- When features were calculated
```

---

### **2. Market Session Features** (5 columns) - Phase 1
```sql
    -- Market sessions (calculated from timestamp)
    active_sessions Array(String),        -- ['london', 'newyork']
    active_count UInt8,                   -- 0-4
    is_overlap UInt8,                     -- 0 or 1
    liquidity_level Enum8('very_low'=1, 'low'=2, 'medium'=3,
                           'high'=4, 'very_high'=5),
    is_london_newyork_overlap UInt8,      -- 0 or 1
```

---

### **3. Calendar Features** (10 columns) - Phase 1
```sql
    -- Calendar (calculated from timestamp)
    day_of_week UInt8,                    -- 0-6 (Monday-Sunday)
    day_name String,                      -- 'Monday', 'Tuesday'
    is_monday UInt8,                      -- 0 or 1
    is_friday UInt8,                      -- 0 or 1
    is_weekend UInt8,                     -- 0 or 1
    week_of_month UInt8,                  -- 1-5
    week_of_year UInt8,                   -- 1-52
    is_month_start UInt8,                 -- 0 or 1
    is_month_end UInt8,                   -- 0 or 1
    day_of_month UInt8,                   -- 1-31
```

---

### **4. Time Features** (6 columns) - Phase 1
```sql
    -- Intraday time
    hour_utc UInt8,                       -- 0-23
    minute UInt8,                         -- 0-59
    quarter_hour UInt8,                   -- 0-3
    is_market_open UInt8,                 -- 0 or 1
    is_london_open UInt8,                 -- 0 or 1
    is_ny_open UInt8,                     -- 0 or 1
```

---

### **5. Technical Indicators** (14 columns) - Phase 1
```sql
    -- Technical indicators (dari TA-Lib)
    rsi_14 Nullable(Float64),             -- RSI (14 periods)
    macd Nullable(Float64),               -- MACD line
    macd_signal Nullable(Float64),        -- MACD signal line
    macd_histogram Nullable(Float64),     -- MACD histogram
    bb_upper Nullable(Float64),           -- Bollinger Bands upper
    bb_middle Nullable(Float64),          -- Bollinger Bands middle (SMA 20)
    bb_lower Nullable(Float64),           -- Bollinger Bands lower
    stoch_k Nullable(Float64),            -- Stochastic %K
    stoch_d Nullable(Float64),            -- Stochastic %D
    sma_50 Nullable(Float64),             -- Simple Moving Average 50
    sma_200 Nullable(Float64),            -- Simple Moving Average 200
    ema_12 Nullable(Float64),             -- Exponential Moving Average 12
    cci Nullable(Float64),                -- Commodity Channel Index
    mfi Nullable(Float64),                -- Money Flow Index
```

---

### **6. Fibonacci Features** (7 columns) - Phase 1
```sql
    -- Fibonacci retracement levels
    fib_0 Nullable(Float64),              -- 0.0 (swing low)
    fib_236 Nullable(Float64),            -- 23.6% retracement
    fib_382 Nullable(Float64),            -- 38.2% retracement
    fib_50 Nullable(Float64),             -- 50.0% retracement
    fib_618 Nullable(Float64),            -- 61.8% retracement (golden ratio)
    fib_786 Nullable(Float64),            -- 78.6% retracement
    fib_100 Nullable(Float64),            -- 100.0 (swing high)
```

---

### **7. External Data Features** (12 columns) - Phase 1
```sql
    -- Economic Calendar (time-based join)
    upcoming_event_minutes Nullable(Int32),     -- Minutes until next high-impact event
    upcoming_event_impact Nullable(String),     -- 'low', 'medium', 'high'
    recent_event_minutes Nullable(Int32),       -- Minutes since last high-impact event

    -- FRED Indicators (latest values before feature time)
    gdp_latest Nullable(Float64),               -- Latest GDP value
    unemployment_latest Nullable(Float64),      -- Latest unemployment rate
    cpi_latest Nullable(Float64),               -- Latest CPI
    interest_rate_latest Nullable(Float64),     -- Latest interest rate (DFF)

    -- Commodity Prices (latest values)
    gold_price Nullable(Float64),               -- Latest gold price (GC=F)
    oil_price Nullable(Float64),                -- Latest oil price (CL=F)
    gold_change_pct Nullable(Float64),          -- Gold % change (24h)
    oil_change_pct Nullable(Float64),           -- Oil % change (24h)
```

---

### **8. Lagged Features** (15 columns) - Phase 1 🆕 CRITICAL
```sql
    -- Lagged Price (from aggregates.close)
    close_lag_1 Nullable(Float64),        -- Close price 1 candle ago
    close_lag_2 Nullable(Float64),        -- Close price 2 candles ago
    close_lag_3 Nullable(Float64),        -- Close price 3 candles ago
    close_lag_5 Nullable(Float64),        -- Close price 5 candles ago
    close_lag_10 Nullable(Float64),       -- Close price 10 candles ago

    -- Lagged Indicators
    rsi_lag_1 Nullable(Float64),          -- RSI 1 candle ago
    rsi_lag_2 Nullable(Float64),          -- RSI 2 candles ago
    macd_lag_1 Nullable(Float64),         -- MACD 1 candle ago

    -- Lagged Returns (% change)
    return_lag_1 Nullable(Float64),       -- % change 1 candle ago
    return_lag_2 Nullable(Float64),       -- % change 2 candles ago
    return_lag_3 Nullable(Float64),       -- % change 3 candles ago

    -- Lagged Volume (from aggregates.tick_count)
    volume_lag_1 Nullable(UInt32),        -- Tick count 1 candle ago
    volume_lag_2 Nullable(UInt32),        -- Tick count 2 candles ago

    -- Lagged Spread (from aggregates.avg_spread)
    spread_lag_1 Nullable(Float64),       -- Avg spread 1 candle ago
    spread_lag_2 Nullable(Float64),       -- Avg spread 2 candles ago
```

**Purpose**: Detect trends, momentum, dan patterns dari historical behavior

---

### **9. Rolling Statistics** (8 columns) - Phase 1 🆕 CRITICAL
```sql
    -- Rolling Mean (from close prices)
    price_rolling_mean_10 Nullable(Float64),    -- Mean of last 10 closes
    price_rolling_mean_20 Nullable(Float64),    -- Mean of last 20 closes
    price_rolling_mean_50 Nullable(Float64),    -- Mean of last 50 closes

    -- Rolling Std Dev (volatility measure)
    price_rolling_std_10 Nullable(Float64),     -- Std dev of last 10 closes
    price_rolling_std_20 Nullable(Float64),     -- Std dev of last 20 closes

    -- Rolling Min/Max (support/resistance)
    price_rolling_max_20 Nullable(Float64),     -- Highest high in 20 candles
    price_rolling_min_20 Nullable(Float64),     -- Lowest low in 20 candles

    -- Distance from Rolling Mean (Z-score)
    dist_from_rolling_mean_20 Nullable(Float64), -- (close - rolling_mean_20) / rolling_std_20
```

**Purpose**: Support/resistance detection, overbought/oversold, mean reversion signals

---

### **10. Momentum Features** (5 columns) - Phase 2 🆕
```sql
    -- Rate of Change (ROC)
    roc_5 Nullable(Float64),                -- (close - close_lag_5) / close_lag_5 * 100
    roc_10 Nullable(Float64),               -- (close - close_lag_10) / close_lag_10 * 100

    -- Price Acceleration (2nd derivative)
    price_acceleration Nullable(Float64),   -- Change in ROC (momentum of momentum)

    -- Directional Movement (trend strength)
    adx Nullable(Float64),                  -- Average Directional Index
    adx_trend Enum8('weak'=1, 'moderate'=2, 'strong'=3, 'very_strong'=4), -- ADX classification
```

**Purpose**: Trend strength, breakout detection, acceleration/deceleration signals

---

### **11. Multi-Timeframe Features** (10 columns) - Phase 1 🆕 CRITICAL FOR FOREX
```sql
    -- Higher Timeframe Context (1 level up)
    htf_trend_direction Enum8('up'=1, 'down'=2, 'sideways'=3), -- Higher TF trend
    htf_rsi Nullable(Float64),              -- RSI from higher timeframe
    htf_macd Nullable(Float64),             -- MACD from higher timeframe
    htf_sma_50 Nullable(Float64),           -- SMA 50 from higher TF

    -- Lower Timeframe Context (1 level down)
    ltf_volatility Nullable(Float64),       -- Volatility from lower TF
    ltf_volume Nullable(Float64),           -- Average volume from lower TF

    -- Multi-TF Alignment
    is_all_tf_aligned UInt8,                -- All TFs same direction? (0 or 1)
    tf_alignment_score Float64,             -- Alignment score (0-1)

    -- Higher TF Support/Resistance
    htf_support_level Nullable(Float64),    -- Support from daily/4h
    htf_resistance_level Nullable(Float64), -- Resistance from daily/4h
```

**Purpose**: Avoid trading against higher TF trend, identify key levels

**Timeframe Mapping**:
```
Current TF → Higher TF → Lower TF
5m        → 15m       → 1m (if available)
15m       → 1h        → 5m
30m       → 1h        → 15m
1h        → 4h        → 15m
4h        → 1d        → 1h
1d        → 1w        → 4h
```

---

### **12. Target Variables** (5 columns) - Phase 1 🆕 CRITICAL FOR SUPERVISED LEARNING
```sql
    -- Future Returns (for regression models)
    target_return_5min Nullable(Float64),   -- Return after 5 minutes (% change)
    target_return_15min Nullable(Float64),  -- Return after 15 minutes
    target_return_1h Nullable(Float64),     -- Return after 1 hour

    -- Direction (for classification models)
    target_direction Enum8('up'=1, 'down'=2, 'neutral'=3), -- Future direction

    -- Binary Classification (simplified)
    target_is_profitable UInt8,             -- Will this trade be profitable? (0 or 1)
```

**Calculation Logic** (with look-ahead bias prevention):
```sql
-- Example for 5min target on 5m timeframe:
target_return_5min = (close_at_t+1 - close_at_t) / close_at_t * 100

-- Example for 15min target on 5m timeframe:
target_return_15min = (close_at_t+3 - close_at_t) / close_at_t * 100

-- Direction (with threshold to avoid noise):
target_direction =
    CASE
        WHEN target_return_1h > 0.15 THEN 'up'      -- Significant move up
        WHEN target_return_1h < -0.15 THEN 'down'   -- Significant move down
        ELSE 'neutral'                               -- Range-bound
    END
```

---

### **13. Data Quality Metrics** (3 columns) - Phase 2 🆕
```sql
    -- Data Quality
    quality_score Float64,                  -- Overall quality (0-1)
    missing_feature_count UInt8,            -- How many features are NULL?
    calculation_duration_ms UInt32,         -- How long to calculate all features?
```

**Purpose**: Monitor feature health, detect data issues, performance tracking

---

### **14. Feature Interactions** (5 columns) - Phase 3 🆕
```sql
    -- Cross Features (interaction between 2+ features)
    rsi_volume_interaction Float64,         -- RSI * (volume / volume_avg)
    macd_session_interaction Float64,       -- MACD * liquidity_level
    price_deviation_volume Float64,         -- dist_from_mean * volume
    trend_strength_momentum Float64,        -- ADX * ROC
    volatility_spread_ratio Float64,        -- price_rolling_std / avg_spread
)
ENGINE = MergeTree()
PARTITION BY (toYYYYMM(time), timeframe)
ORDER BY (symbol, timeframe, time);
```

**Purpose**: Capture non-linear relationships (model dapat learn sendiri untuk tree-based, tapi explicit better untuk linear models)

---

## 🔄 Feature Engineering Process Flow

```
┌────────────────────────────────────────────────────────────┐
│                    INPUT TABLES                            │
│                                                            │
│  • aggregates (OHLC, volume, spreads)                     │  ← Source of Truth
│  • external_economic_calendar                             │
│  • external_fred_indicators                               │
│  • external_commodity_prices                              │
└───────────────────────────┬────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │  Feature Engineering Service      │
        │  (Python + Pandas + TA-Lib)       │
        └───────────┬───────────────────────┘
                    │
        ┌───────────┼──────────────────┬────────────────┐
        │           │                  │                │
        ▼           ▼                  ▼                ▼
   ┌─────────┐ ┌──────────┐  ┌───────────────┐  ┌─────────┐
   │Calculate│ │Technical │  │Multi-Timeframe│  │Join Ext │
   │Features │ │Indicators│  │Features       │  │Data     │
   └────┬────┘ └────┬─────┘  └───────┬───────┘  └────┬────┘
        │           │                │                │
        │ Sessions  │ RSI, MACD      │ HTF trend      │ Economic
        │ Calendar  │ Bollinger      │ Support/Res    │ FRED
        │ Time      │ Fibonacci      │ Alignment      │ Commodity
        │ Lagged    │ Rolling        │                │
        │ Momentum  │                │                │
        │           │                │                │
        └───────────┴────────────────┴────────────────┘
                    │
                    ▼
        ┌───────────────────────────┐
        │   ml_features table       │
        │   (110 derived features)  │
        │   ← NO RAW DATA           │
        └───────────────────────────┘
                    │
                    ▼
        ┌───────────────────────────┐
        │   ML Training/Inference   │
        │   JOIN aggregates         │  ← Get raw OHLC here
        │   + ml_features           │
        └───────────────────────────┘
```

---

## 📊 Complete Feature Count Summary

### **Phase 1 - MVP (MUST HAVE)**: 110 Features

| Category | Count | Priority | Status |
|----------|-------|----------|--------|
| Primary Keys & Metadata | 5 | ⭐⭐⭐⭐⭐ | ✅ Defined |
| Market Session Features | 5 | ⭐⭐⭐⭐⭐ | ✅ Defined |
| Calendar Features | 10 | ⭐⭐⭐⭐⭐ | ✅ Defined |
| Time Features | 6 | ⭐⭐⭐⭐ | ✅ Defined |
| Technical Indicators | 14 | ⭐⭐⭐⭐ | ⚠️ To Implement |
| Fibonacci Features | 7 | ⭐⭐⭐⭐ | ⚠️ To Implement |
| External Data Features | 12 | ⭐⭐⭐⭐ | ⚠️ To Implement |
| **🆕 Lagged Features** | 15 | ⭐⭐⭐⭐⭐ | ⚠️ To Implement |
| **🆕 Rolling Statistics** | 8 | ⭐⭐⭐⭐⭐ | ⚠️ To Implement |
| **🆕 Multi-Timeframe** | 10 | ⭐⭐⭐⭐⭐ | ⚠️ To Implement |
| **🆕 Target Variables** | 5 | ⭐⭐⭐⭐⭐ | ⚠️ To Implement |
| **Phase 1 TOTAL** | **97** | - | **MVP** |

### **Phase 2 - Enhancement (SHOULD HAVE)**: +8 Features

| Category | Count | Priority | Status |
|----------|-------|----------|--------|
| **🆕 Momentum Features** | 5 | ⭐⭐⭐⭐ | ⚠️ Phase 2 |
| **🆕 Data Quality** | 3 | ⭐⭐⭐ | ⚠️ Phase 2 |
| **Phase 2 TOTAL** | **+8** | - | **105 features** |

### **Phase 3 - Advanced (NICE TO HAVE)**: +5 Features

| Category | Count | Priority | Status |
|----------|-------|----------|--------|
| **🆕 Feature Interactions** | 5 | ⭐⭐⭐ | ⚠️ Phase 3 |
| **Phase 3 TOTAL** | **+5** | - | **110 features** |

---

## 🎯 Implementation Priority

### **Sprint 1** (Week 1-2): Core Infrastructure
- [ ] Setup ml_features table schema
- [ ] Implement JOIN logic (aggregates + ml_features)
- [ ] Test data flow (aggregates → ml_features)

### **Sprint 2** (Week 3-4): Basic Features
- [ ] Market sessions, calendar, time features
- [ ] Technical indicators (TA-Lib integration)
- [ ] Fibonacci calculation
- [ ] External data joins

### **Sprint 3** (Week 5-6): Critical Additions ⭐
- [ ] **Lagged features** (15 columns)
- [ ] **Rolling statistics** (8 columns)
- [ ] **Target variables** (5 columns) ← CRITICAL!

### **Sprint 4** (Week 7-8): Multi-Timeframe ⭐⭐⭐
- [ ] **Multi-timeframe features** (10 columns)
- [ ] Higher TF trend detection
- [ ] Support/resistance from higher TFs
- [ ] TF alignment scoring

### **Sprint 5** (Week 9-10): Enhancements
- [ ] Momentum features (5 columns)
- [ ] Data quality metrics (3 columns)
- [ ] Performance optimization

### **Sprint 6** (Week 11-12): Advanced & Testing
- [ ] Feature interactions (optional)
- [ ] Full backtest (2023-2025 data)
- [ ] Quality validation
- [ ] Production deployment

---

## ⚙️ Implementation Considerations

### **1. Lookback Windows**

| Feature | Lookback Required | Strategy |
|---------|-------------------|----------|
| RSI | 14 candles | NULL for first 14 |
| MACD | 26 candles | NULL for first 26 |
| SMA 200 | 200 candles | NULL for first 200 |
| Lagged (lag_10) | 10 candles | NULL for first 10 |
| Rolling (mean_50) | 50 candles | NULL for first 50 |
| Fibonacci | 20-50 candles | NULL if insufficient data |

### **2. NULL Handling Strategy**

```sql
-- Example for training query
SELECT * FROM ml_features
WHERE
    rsi_14 IS NOT NULL              -- At least 14 candles available
    AND close_lag_10 IS NOT NULL    -- At least 10 candles available
    AND target_return_1h IS NOT NULL -- Target available
    AND quality_score > 0.9          -- Good quality data
```

### **3. Multi-Timeframe Calculation**

```python
# Pseudo-code for multi-TF features
def calculate_multi_tf_features(current_symbol, current_tf, current_time):
    """
    Calculate higher & lower timeframe features
    """
    # Map to higher timeframe
    higher_tf = TF_MAP[current_tf]['higher']  # e.g., 5m → 15m

    # Query higher TF data at same time
    htf_data = query_aggregates(
        symbol=current_symbol,
        timeframe=higher_tf,
        time=current_time
    )

    # Calculate HTF features
    htf_trend = detect_trend(htf_data)
    htf_rsi = calculate_rsi(htf_data)
    htf_support, htf_resistance = find_levels(htf_data)

    return {
        'htf_trend_direction': htf_trend,
        'htf_rsi': htf_rsi,
        'htf_support_level': htf_support,
        'htf_resistance_level': htf_resistance
    }
```

### **4. Target Calculation (Look-Ahead Bias Prevention)**

```python
def calculate_targets(symbol, timeframe, time):
    """
    Calculate future returns WITHOUT look-ahead bias
    """
    # Get FUTURE candles (strict time boundary)
    future_candles = query_aggregates(
        symbol=symbol,
        timeframe=timeframe,
        time_start=time,  # Exclusive (not including current)
        time_end=time + timedelta(hours=1)  # 1 hour ahead
    )

    if len(future_candles) == 0:
        return None  # Cannot calculate target (at edge of dataset)

    # Calculate returns
    current_close = get_close_at(time)
    future_close_5m = future_candles[0].close  # 1st candle ahead
    future_close_1h = future_candles[-1].close  # Last candle in 1h

    return {
        'target_return_5min': (future_close_5m - current_close) / current_close * 100,
        'target_return_1h': (future_close_1h - current_close) / current_close * 100
    }
```

**CRITICAL**: Targets only calculated for historical data (NOT live data during inference)

### **5. Real-time vs Batch Processing**

**Real-time** (Live candles):
```python
# When new candle arrives
new_candle = {time: '2025-10-17 14:05:00', symbol: 'C:EURUSD', ...}

# Calculate features (NO targets for live)
features = calculate_features(new_candle, include_targets=False)

# Insert to ml_features
clickhouse.insert('ml_features', features)

# For inference: JOIN with aggregates
query = """
    SELECT a.*, f.*
    FROM aggregates a
    LEFT JOIN ml_features f USING (time, symbol, timeframe)
    WHERE a.time >= NOW() - INTERVAL 1 HOUR
"""
```

**Batch** (Historical backfill):
```python
# For training data (can calculate targets)
for candle in historical_candles:
    features = calculate_features(candle, include_targets=True)
    clickhouse.insert('ml_features', features)
```

### **6. Performance Optimization**

- **Vectorized Operations**: Use Pandas/NumPy for bulk calculations
- **Caching**: Cache external data queries (economic calendar doesn't change)
- **Parallel Processing**: Process multiple symbols in parallel
- **Batch Inserts**: Insert 1000+ rows at once (not row-by-row)
- **Incremental Updates**: Only calculate features for new candles

---

## 🚧 Known Limitations & Future Improvements

### **Current Limitations**:
1. **Multi-TF features**: Requires all timeframes to be populated (dependency)
2. **External data**: May have NULL if API fails (graceful degradation needed)
3. **Lookback windows**: First N candles will have many NULLs
4. **Computation cost**: 110 features per candle (optimize with caching)

### **Future Improvements** (Post-MVP):
1. **Feature Store Pattern**: Separate tables per feature category
2. **Feature Caching**: Cache expensive calculations (external data)
3. **Auto Feature Selection**: Remove low-importance features
4. **Online Learning Features**: Update features from live trading results
5. **Feature Importance Tracking**: Monitor which features actually used by model

---

## 📋 SQL Query Examples

### **Training Query** (Historical + Targets):
```sql
-- Get complete dataset for ML training
SELECT
    -- Raw data from aggregates
    a.time,
    a.symbol,
    a.timeframe,
    a.open,
    a.high,
    a.low,
    a.close,
    a.tick_count,
    a.avg_spread,
    a.max_spread,
    a.min_spread,
    a.price_range,
    a.pct_change,

    -- Derived features from ml_features (110 columns)
    f.*
FROM aggregates a
LEFT JOIN ml_features f
    ON a.time = f.time
    AND a.symbol = f.symbol
    AND a.timeframe = f.timeframe
WHERE
    a.time BETWEEN '2023-01-01' AND '2025-09-01'  -- Training period
    AND a.symbol = 'C:EURUSD'
    AND a.timeframe = '1h'
    AND f.rsi_14 IS NOT NULL           -- Filter incomplete features
    AND f.target_return_1h IS NOT NULL -- Must have target
    AND f.quality_score > 0.9          -- Good quality only
ORDER BY a.time;
```

### **Inference Query** (Live, No Targets):
```sql
-- Get latest data for prediction
SELECT
    a.time,
    a.symbol,
    a.timeframe,
    a.open,
    a.high,
    a.low,
    a.close,
    a.tick_count,
    a.avg_spread,

    -- Derived features (NO targets)
    f.rsi_14,
    f.macd,
    f.close_lag_1,
    f.close_lag_2,
    f.close_lag_3,
    f.price_rolling_mean_20,
    f.htf_trend_direction,
    -- ... (all other features except targets)
FROM aggregates a
LEFT JOIN ml_features f
    ON a.time = f.time
    AND a.symbol = f.symbol
    AND a.timeframe = f.timeframe
WHERE
    a.time >= NOW() - INTERVAL 2 HOUR  -- Recent data only
    AND a.symbol = 'C:EURUSD'
    AND a.timeframe = '1h'
ORDER BY a.time DESC
LIMIT 1;  -- Latest candle for prediction
```

---

## ✅ Validation Checklist

Before deployment, validate:

- [ ] **Schema Created**: ml_features table exists in ClickHouse
- [ ] **No Duplicates**: Raw OHLC NOT in ml_features (only in aggregates)
- [ ] **JOIN Works**: Can successfully join aggregates + ml_features
- [ ] **Targets Calculated**: Future returns computed correctly (no look-ahead bias)
- [ ] **Multi-TF Working**: Higher/lower TF features populated
- [ ] **NULL Handling**: Proper NULL for insufficient lookback windows
- [ ] **Quality Metrics**: quality_score calculated for all rows
- [ ] **Performance**: < 5 seconds to calculate 110 features per candle
- [ ] **Backtest Complete**: 2023-2025 data fully populated
- [ ] **Live Integration**: Real-time features calculated on new candles

---

**Status**: Complete redesign with 110 features for MVP

**Next Steps**:
1. Review & approve new design
2. Implement Phase 1 features (97 columns)
3. Add Phase 2 enhancements (+8 columns)
4. Test with ML training pipeline

**Version History**:
- v2.0.0 (2025-10-17): **Major redesign** - Removed raw data duplication, added 38 critical features (lagged, rolling, multi-TF, targets), total 110 features untuk MVP
- v1.0.0 (2025-10-17): Initial draft - 72 features with raw data duplication
