# 🔧 Database Process Tables - Feature Engineering Service

> **Version**: 1.0.0 (Draft - Bertahap)
> **Last Updated**: 2025-10-17
> **Status**: In Discussion - Konsep Awal

---

## 📋 Overview

**Purpose**: Dokumentasi untuk tabel-tabel yang dihasilkan oleh **Feature Engineering Service**

**Input**: Data dari `table_database_input.md` (ticks, aggregates, external data)
**Output**: ML-ready features untuk training dan inference

---

## 🎯 Feature Engineering Service

**Service Name**: `feature-engineering-service`
**Function**: Transform raw/aggregated data → ML features (72 features)
**Flow**:
```
Input Tables (ClickHouse)
    ↓
Feature Engineering Service
    ↓
Output Tables (ClickHouse) - ML Ready
```

---

## 📊 Output Tables Structure

Feature Engineering Service menghasilkan **1 main table** dengan 72+ kolom (features):

### **Table: ml_features** (Main ML Training Table)

**Purpose**: Complete dataset dengan semua 72 ML features untuk training/inference

**Storage**: ClickHouse
**Update Frequency**: Real-time (saat candle baru) + Batch (historical backfill)
**Retention**:
- Live features: Sesuai dengan live_aggregates (7 days)
- Historical features: Unlimited

**Schema Structure** (72+ kolom):

#### **1. Primary Keys & Metadata** (5 kolom)
```sql
CREATE TABLE suho_analytics.ml_features
(
    -- Primary identifiers
    time DateTime64(3, 'UTC'),           -- Feature timestamp (same as candle time)
    symbol String,                        -- C:EURUSD, C:XAUUSD, dll
    timeframe Enum8('5m'=1, '15m'=2, '30m'=3, '1h'=4,
                    '4h'=5, '1d'=6, '1w'=7),

    -- Metadata
    feature_version String,               -- Version tracking (e.g., "v2.3")
    created_at DateTime64(3, 'UTC'),      -- When features were calculated
```

#### **2. Price Features** (4 kolom) - dari aggregates
```sql
    -- OHLC (from aggregates)
    open Decimal(18,5),
    high Decimal(18,5),
    low Decimal(18,5),
    close Decimal(18,5),
```

#### **3. Volume Features** (1 kolom) - dari aggregates
```sql
    -- Volume proxy
    tick_count UInt32,
```

#### **4. Spread Features** (3 kolom) - dari aggregates
```sql
    -- Spread metrics
    avg_spread Decimal(18,5),
    max_spread Decimal(18,5),
    min_spread Decimal(18,5),
```

#### **5. Volatility Features** (2 kolom) - dari aggregates
```sql
    -- Volatility
    price_range Decimal(18,5),
    pct_change Decimal(10,5),
```

#### **6. Market Session Features** (5 kolom) - calculated
```sql
    -- Market sessions (calculated from timestamp)
    active_sessions Array(String),        -- ['london', 'newyork']
    active_count UInt8,                   -- 0-4
    is_overlap UInt8,                     -- 0 or 1
    liquidity_level Enum8('very_low'=1, 'low'=2, 'medium'=3,
                           'high'=4, 'very_high'=5),
    is_london_newyork_overlap UInt8,      -- 0 or 1
```

#### **7. Calendar Features** (10 kolom) - calculated
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

#### **8. Time Features** (6 kolom) - calculated
```sql
    -- Intraday time
    hour_utc UInt8,                       -- 0-23
    minute UInt8,                         -- 0-59
    quarter_hour UInt8,                   -- 0-3
    is_market_open UInt8,                 -- 0 or 1
    is_london_open UInt8,                 -- 0 or 1
    is_ny_open UInt8,                     -- 0 or 1
```

#### **9. Technical Indicators** (14 kolom) - ⚠️ TO BE ADDED
```sql
    -- Technical indicators (dari TA-Lib atau manual calculation)
    rsi_14 Nullable(Float64),             -- RSI (14 periods)
    macd Nullable(Float64),               -- MACD line
    macd_signal Nullable(Float64),        -- MACD signal line
    macd_histogram Nullable(Float64),     -- MACD histogram
    bb_upper Nullable(Float64),           -- Bollinger Bands upper
    bb_middle Nullable(Float64),          -- Bollinger Bands middle (SMA)
    bb_lower Nullable(Float64),           -- Bollinger Bands lower
    stoch_k Nullable(Float64),            -- Stochastic %K
    stoch_d Nullable(Float64),            -- Stochastic %D
    sma_50 Nullable(Float64),             -- Simple Moving Average 50
    sma_200 Nullable(Float64),            -- Simple Moving Average 200
    ema_12 Nullable(Float64),             -- Exponential Moving Average 12
    cci Nullable(Float64),                -- Commodity Channel Index
    mfi Nullable(Float64),                -- Money Flow Index
```

#### **10. Fibonacci Features** (7 kolom) - calculated
```sql
    -- Fibonacci retracement levels
    fib_0 Nullable(Float64),              -- 0.0 (swing low)
    fib_236 Nullable(Float64),            -- 23.6% retracement
    fib_382 Nullable(Float64),            -- 38.2% retracement
    fib_50 Nullable(Float64),             -- 50.0% retracement
    fib_618 Nullable(Float64),            -- 61.8% retracement
    fib_786 Nullable(Float64),            -- 78.6% retracement
    fib_100 Nullable(Float64),            -- 100.0 (swing high)
```

#### **11. External Data Features** (15 kolom) - ⚠️ TO BE DESIGNED
```sql
    -- Economic Calendar (time-based join)
    upcoming_event_minutes Nullable(Int32),     -- Minutes until next high-impact event
    upcoming_event_impact Nullable(String),     -- 'low', 'medium', 'high'
    recent_event_minutes Nullable(Int32),       -- Minutes since last high-impact event

    -- FRED Indicators (latest values)
    gdp_latest Nullable(Float64),               -- Latest GDP value
    unemployment_latest Nullable(Float64),      -- Latest unemployment rate
    cpi_latest Nullable(Float64),               -- Latest CPI
    interest_rate_latest Nullable(Float64),     -- Latest interest rate

    -- Commodity Prices (latest values)
    gold_price Nullable(Float64),               -- Latest gold price
    oil_price Nullable(Float64),                -- Latest oil price
    gold_change_pct Nullable(Float64),          -- Gold % change
    oil_change_pct Nullable(Float64),           -- Oil % change

    -- Reserved for future external data
    ext_reserved_1 Nullable(Float64),
    ext_reserved_2 Nullable(Float64),
    ext_reserved_3 Nullable(Float64),
)
ENGINE = MergeTree()
PARTITION BY (toYYYYMM(time), timeframe)
ORDER BY (symbol, timeframe, time);
```

---

## 🔄 Feature Engineering Process Flow

```
┌────────────────────────────────────────────────────────────┐
│                    INPUT TABLES                            │
│                                                            │
│  • live_aggregates / historical_aggregates (OHLC)         │
│  • external_economic_calendar (events)                     │
│  • external_fred_indicators (macro indicators)             │
│  • external_commodity_prices (gold, oil)                   │
└───────────────────────────┬────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │  Feature Engineering Service      │
        │  (Python + Pandas + TA-Lib)       │
        └───────────┬───────────────────────┘
                    │
        ┌───────────┼────────────┐
        │           │            │
        ▼           ▼            ▼
   ┌─────────┐ ┌──────────┐ ┌──────────┐
   │Calculate│ │Technical │ │Join Ext  │
   │Features │ │Indicators│ │Data      │
   └────┬────┘ └────┬─────┘ └────┬─────┘
        │           │            │
        │ Sessions  │ RSI, MACD  │ Economic
        │ Calendar  │ Bollinger  │ FRED
        │ Time      │ Fibonacci  │ Commodity
        │           │            │
        └───────────┴────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │   ml_features table   │
        │   (72 features)       │
        └───────────────────────┘
```

---

## 📝 Feature Calculation Methods

### **1. Direct Copy** (dari aggregates)
- OHLC, tick_count, spreads, volatility → langsung copy dari aggregates

### **2. Calculated** (dari timestamp)
- Market sessions, calendar, time features → pure calculation

### **3. Technical Indicators** (dari price series)
```python
# Butuh historical candles (lookback window)
def calculate_rsi(close_prices, period=14):
    # Calculate RSI from last N candles
    ...

def calculate_macd(close_prices):
    # Calculate MACD from price series
    ...
```

### **4. Fibonacci** (dari swing high/low)
```python
# Butuh window untuk detect swing points
def calculate_fibonacci_levels(candles, lookback=20):
    # Find swing high/low in last N candles
    # Calculate fib retracement levels
    ...
```

### **5. External Data Join** (time-based)
```python
# Join dengan external tables berdasarkan timestamp proximity
def join_economic_events(feature_time):
    # Find upcoming/recent high-impact events
    ...

def join_fred_indicators(feature_time):
    # Get latest FRED values before feature_time
    ...
```

---

## ⚙️ Implementation Considerations

### **Lookback Windows**
Technical indicators membutuhkan historical data:
- RSI: 14 candles
- MACD: 26 candles (longest EMA)
- SMA 200: 200 candles
- Fibonacci: 20-50 candles (for swing detection)

**Strategy**: Query N candles before current candle untuk calculation

### **Nullable Fields**
Indicators yang butuh lookback akan NULL untuk awal-awal candles:
```sql
-- First 14 candles
rsi_14: NULL

-- After 14th candle
rsi_14: 67.3
```

### **Real-time vs Batch**
- **Real-time**: Calculate features untuk new candles (live_aggregates)
- **Batch**: Backfill historical features (historical_aggregates)

### **Performance Optimization**
- Use vectorized operations (Pandas/NumPy)
- Batch processing untuk historical
- Cache external data queries
- Parallel processing per symbol

---

## 🎯 Next Steps (To Be Discussed)

1. **External Data Join Strategy**
   - [ ] How to join economic events (time proximity?)
   - [ ] FRED indicators caching strategy
   - [ ] Commodity prices alignment

2. **Technical Indicators Implementation**
   - [ ] TA-Lib vs manual implementation
   - [ ] Lookback window optimization
   - [ ] Missing data handling (NULL strategy)

3. **Fibonacci Calculation**
   - [ ] Swing detection algorithm
   - [ ] Dynamic vs fixed lookback window
   - [ ] Multiple timeframe fibonacci?

4. **Table Partitioning & Performance**
   - [ ] Partition strategy (same as aggregates?)
   - [ ] Index optimization
   - [ ] Query patterns untuk training vs inference

5. **Feature Versioning**
   - [ ] How to handle feature changes?
   - [ ] Backward compatibility
   - [ ] A/B testing new features

---

## 📊 Feature Count Summary

| Category | Count | Status |
|----------|-------|--------|
| Primary Keys & Metadata | 5 | ✅ Defined |
| Price Features | 4 | ✅ Defined |
| Volume Features | 1 | ✅ Defined |
| Spread Features | 3 | ✅ Defined |
| Volatility Features | 2 | ✅ Defined |
| Market Session Features | 5 | ✅ Defined |
| Calendar Features | 10 | ✅ Defined |
| Time Features | 6 | ✅ Defined |
| Technical Indicators | 14 | ⚠️ To Be Implemented |
| Fibonacci Features | 7 | ⚠️ To Be Implemented |
| External Data Features | 15 | ⚠️ To Be Designed |
| **TOTAL** | **72** | **In Progress** |

---

**Status**: Dokumentasi bertahap - siap untuk diskusi implementation details

**Version History**:
- v1.0.0 (2025-10-17): Initial draft - ML features table structure, 72 features breakdown
