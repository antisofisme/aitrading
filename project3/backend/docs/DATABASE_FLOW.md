# =� Database Flow - Data Storage Strategy

> **Version**: 1.5.0 (Draft - Bertahap)
> **Last Updated**: 2025-10-17
> **Status**: In Discussion - Konsep Awal

---

## <� Prinsip Utama: Pemisahan Storage Berdasarkan Use Case

### 1� **Live Data** � TimescaleDB (Fast Writes)
- **Purpose**: Real-time trading, operational data
- **Optimization**: Fast writes, time-series queries
- **Retention**: 90 hari (auto-cleanup)
- **Use Case**: Live monitoring, recent analysis

### 2� **Historical Data** � ClickHouse (Long-term Storage)
- **Purpose**: Analytics, backtesting, ML training
- **Optimization**: Compression, analytical queries
- **Retention**: Unlimited (cost-effective storage)
- **Use Case**: Historical analysis, model training

---

## =� Data Sources & Storage

**Final Architecture**: 2 Data Sources

| Source | Type | Storage | Retention | Cost | Status |
|--------|------|---------|-----------|------|--------|
| **Polygon Live** | Real-time tick | TimescaleDB | 90 days | Paid (subscription) | ✅ Active |
| **Dukascopy Historical** | Historical tick | ClickHouse | Unlimited | FREE | ✅ Active |
| ~~Polygon Historical~~ | Aggregated candles | - | - | Paid | ❌ Archived |

---

### **Source 1: Polygon.io Live WebSocket**

**Data Type**: Real-time tick data (bid/ask quotes)

**Storage**:
```
Polygon WebSocket � Live Collector � TimescaleDB.market_ticks
```

**Database**: TimescaleDB
**Table**: `market_ticks`
**Retention**: 90 hari

**Kolom Inti** (6 kolom):
- `time` - timestamp with time zone (primary key)
- `symbol` - varchar(20) (EUR/USD, XAU/USD, dll)
- `bid` - numeric(18,5)
- `ask` - numeric(18,5)
- `timestamp_ms` - bigint (unix timestamp untuk precision)
- `ingested_at` - timestamp with time zone

**Kolom Optional** (calculated on-the-fly):
- `mid` = (bid + ask) / 2
- `spread` = ask - bid

**Kolom Dihapus** (redundant):
- ~~`tick_id`~~ - tidak perlu, cukup composite key (time + symbol)
- ~~`tenant_id`~~ - single tenant
- ~~`exchange`~~ - jelas dari context (Polygon)
- ~~`source`~~ - jelas dari tabel
- ~~`event_type`~~ - semua tick
- ~~`use_case`~~ - jelas dari tabel

**Karakteristik**:
- Write speed: ~100-1,000 ticks/second per symbol
- Query pattern: Recent data (last minutes/hours/days)
- Auto-delete setelah 90 hari

---

### **Source 2: Dukascopy Historical Downloads**

**Data Type**: Historical tick data (bid/ask dari binary files)

**Storage**:
```
Dukascopy Binary Files � Historical Downloader � ClickHouse.historical_ticks
```

**Database**: ClickHouse
**Table**: `historical_ticks`
**Retention**: Unlimited

**Kolom Inti** (6 kolom - **sama dengan live**):
- `time` - DateTime64(3, 'UTC') (primary key)
- `symbol` - String (EUR/USD, XAU/USD, dll)
- `bid` - Decimal(18,5)
- `ask` - Decimal(18,5)
- `timestamp_ms` - UInt64 (unix timestamp untuk precision)
- `ingested_at` - DateTime64(3, 'UTC')

**Kolom Optional** (calculated on-the-fly):
- `mid` = (bid + ask) / 2
- `spread` = ask - bid

**Kolom Dihapus** (redundant):
- ~~`tick_id`~~ - tidak perlu, cukup composite key (time + symbol)
- ~~`tenant_id`~~ - single tenant
- ~~`exchange`~~ - jelas dari context (Dukascopy)
- ~~`source`~~ - jelas dari tabel
- ~~`event_type`~~ - semua tick
- ~~`use_case`~~ - jelas dari tabel

**Karakteristik**:
- Write speed: Batch processing (jutaan tick sekaligus)
- Query pattern: Historical analysis (backtest, ML training)
- Highly compressed (10:1 ratio)
- Long-term storage (tahun-tahun ke belakang)

**About Dukascopy**:
- **Provider**: Dukascopy Bank SA (Swiss regulated bank)
- **Data Quality**: High-quality, widely used by researchers/traders
- **Cost**: **FREE** (gratis untuk historical tick data)
- **Update Schedule**: Daily updates
- **Delay**: **1-2 hari** (T-1 atau T-2)
  - Contoh: Data 15 Oktober tersedia tanggal 16-17 Oktober
- **Coverage**: Multi-year historical data

---

### ~~**Source 3: Polygon Historical API**~~ ❌ **ARCHIVED**

**Status**: **TIDAK DIGUNAKAN** - Service akan diarsipkan

**Alasan**:
- Redundant dengan Dukascopy (sudah ada tick historical)
- Polygon historical = aggregated candles (bukan raw tick)
- Lebih mahal untuk bulk historical data
- Tidak perlu 2 sumber historical yang sama

**Action Items**:
- [ ] Stop `polygon-historical-downloader` service
- [ ] Archive service code ke `00-data-ingestion/_archived/`
- [ ] Remove from docker-compose.yml
- [ ] Update service documentation

---


## 📰 External Data Sources (ML Features)

**Purpose**: Menyediakan context data untuk ML model (economic events, market conditions)

**Total Sources**: 3 external data sources (scraped/fetched dari luar)

**Storage**: ClickHouse (analytics database)
**Flow**: `External Collector → NATS/Kafka → ClickHouse`

---

### **Source 4: Economic Calendar** ⭐⭐⭐⭐⭐

**Data Type**: Scheduled economic events & releases (NFP, GDP, Interest Rate, dll)

**Storage**:
```
MQL5 Scraper → External Collector → ClickHouse.external_economic_calendar
```

**Database**: ClickHouse
**Table**: `external_economic_calendar`
**Retention**: Unlimited

**Kolom Inti** (8 kolom):
- `event_time` - DateTime64(3, 'UTC') ⭐ **PRIMARY** (kapan event release)
- `currency` - String (USD, EUR, GBP, JPY)
- `event_name` - String (Non-Farm Payrolls, GDP, Interest Rate Decision)
- `impact` - Enum8('low', 'medium', 'high') (impact level untuk ML)
- `forecast` - Nullable(String) (predicted value)
- `previous` - Nullable(String) (previous value)
- `actual` - Nullable(String) (actual released value)
- `scraped_at` - DateTime64(3, 'UTC') (tracking only)

**Primary Index**: (event_time, currency)

**Timestamp Concept** (PENTING untuk ML):
```
event_time: 2025-10-06 14:30:00 UTC  ← NFP dirilis (ML pakai ini untuk join)
scraped_at: 2025-10-06 15:00:00 UTC  ← Kapan scraper ambil (tracking)
```

**ML Usage**:
```sql
-- Join dengan price data pada waktu event
SELECT
    e.event_time,
    e.event_name,
    e.impact,
    p.close AS price_before,
    LEAD(p.close) OVER (ORDER BY p.time) AS price_after
FROM external_economic_calendar e
LEFT JOIN aggregates p
    ON p.timestamp BETWEEN e.event_time - INTERVAL 5 MINUTE
                       AND e.event_time + INTERVAL 5 MINUTE
WHERE e.currency = 'USD' AND e.impact = 'high'
```

**Karakteristik**:
- Write frequency: Hourly scraping
- Data consistency: Very high (scheduled events)
- ML impact: ⭐⭐⭐⭐⭐ (highest impact untuk price movement)

---

### **Source 5: FRED Economic Indicators** ⭐⭐⭐⭐⭐

**Data Type**: Official US economic indicators (GDP, Unemployment, CPI, Interest Rates)

**Storage**:
```
FRED API → External Collector → ClickHouse.external_fred_indicators
```

**Database**: ClickHouse
**Table**: `external_fred_indicators`
**Retention**: Unlimited

**Kolom Inti** (6 kolom):
- `release_time` - DateTime64(3, 'UTC') ⭐ **PRIMARY** (kapan data dirilis)
- `series_id` - String (GDP, UNRATE, CPIAUCSL, DFF, DGS10, DEXUSEU, DEXJPUS)
- `series_name` - String (Gross Domestic Product, Unemployment Rate, dll)
- `value` - Float64 (indicator value)
- `unit` - String (Billions, Percent, Index)
- `scraped_at` - DateTime64(3, 'UTC') (tracking only)

**Primary Index**: (release_time, series_id)

**Timestamp Concept**:
```
release_time: 2025-10-06 08:30:00 UTC  ← GDP Q3 dirilis (ML pakai ini)
scraped_at: 2025-10-06 12:00:00 UTC    ← Kapan scraper ambil
```

**Karakteristik**:
- Write frequency: 4 hours (API polling)
- Data consistency: Very high (official government data)
- ML impact: ⭐⭐⭐⭐⭐ (macro trend prediction)

---

### **Source 6: Commodity Prices** ⭐⭐⭐⭐

**Data Type**: Commodity prices (Gold, Oil, Silver, Copper, Natural Gas)

**Storage**:
```
Yahoo Finance API → External Collector → ClickHouse.external_commodity_prices
```

**Database**: ClickHouse
**Table**: `external_commodity_prices`
**Retention**: Unlimited

**Kolom Inti** (8 kolom):
- `price_time` - DateTime64(3, 'UTC') ⭐ **PRIMARY** (waktu harga tercatat)
- `symbol` - String (GC=F, CL=F, SI=F, HG=F, NG=F)
- `commodity_name` - String (Gold, Crude Oil, Silver, Copper, Natural Gas)
- `price` - Decimal(18,5) (current price)
- `currency` - String (USD)
- `change_pct` - Float64 (perubahan % dari previous close)
- `volume` - UInt64 (trading volume)
- `scraped_at` - DateTime64(3, 'UTC') (tracking only)

**Primary Index**: (price_time, symbol)

**Timestamp Concept**:
```
price_time: 2025-10-06 14:30:00 UTC  ← Harga gold saat ini (ML pakai ini)
scraped_at: 2025-10-06 14:30:15 UTC  ← Kapan scraper ambil
```

**Karakteristik**:
- Write frequency: 30 minutes (API polling)
- Data consistency: High (Yahoo Finance API)
- ML impact: ⭐⭐⭐⭐ (correlation analysis dengan forex)

---

### ~~**Source 7: Crypto Sentiment**~~ ❌ **ARCHIVED**
### ~~**Source 8: Fear & Greed Index**~~ ❌ **ARCHIVED**
### ~~**Source 9: Market Sessions**~~ ⚠️ **MOVED TO CALCULATED FEATURES**

**Status**: **TIDAK DIGUNAKAN** - Relevance rendah atau sudah dipindahkan

**Alasan**:
- Crypto sentiment tidak relevan untuk forex/gold pairs
- Fear & Greed Index = subjective, konsistensi rendah
- **Market Sessions** = calculated feature (tidak perlu external source), pindah ke Feature Engineering

---

## 🧮 Calculated Features (Feature Engineering)

**Purpose**: Features yang di-calculate on-the-fly dari timestamp dan candle data (tidak perlu external source)

**Storage**: **TIDAK DISIMPAN** - calculated saat feature engineering
**Flow**: `Aggregates → Feature Engineering Service → ML Features`

---

### **Feature 1: Market Sessions** ⭐⭐⭐⭐⭐

**Data Type**: Trading session status (London, New York, Tokyo, Sydney)

**Calculation**:
```python
def calculate_market_session(timestamp_utc):
    """
    Pure calculation dari UTC time (tidak perlu scraping)
    """
    hour = timestamp_utc.hour
    
    sessions = {
        'sydney': (22, 7),    # 22:00 - 07:00 UTC
        'tokyo': (0, 9),      # 00:00 - 09:00 UTC
        'london': (8, 16),    # 08:00 - 16:00 UTC
        'newyork': (13, 22)   # 13:00 - 22:00 UTC
    }
    
    active = [name for name, (start, end) in sessions.items() 
              if is_time_in_range(hour, start, end)]
    
    return {
        'active_sessions': active,              # ['london', 'newyork']
        'active_count': len(active),            # 2
        'is_overlap': len(active) > 1,          # True
        'liquidity_level': get_liquidity(active) # 'high'
    }
```

**Features Generated** (5 features):
- `active_sessions` - List session aktif
- `active_count` - Jumlah session (0-4)
- `is_overlap` - Binary flag overlap
- `liquidity_level` - Enum(very_low, low, medium, high, very_high)
- `is_london_newyork_overlap` - Binary flag untuk overlap paling liquid

**ML Impact**: ⭐⭐⭐⭐⭐ (volatility & liquidity prediction)

**Why Calculated, Not Stored?**
- Session times = fixed schedule (tidak berubah)
- Calculation = instant (< 1ms)
- No external dependency (pure math dari UTC time)
- Lebih flexible (mudah adjust session times)

---

### **Feature 2: Calendar Features** ⭐⭐⭐⭐⭐

**Data Type**: Day of week, week of month, month boundaries, dst holidays

**Calculation**:
```python
def add_calendar_features(df, timestamp_col='time'):
    """
    Calendar features dari timestamp
    """
    # Day features
    df['day_of_week'] = df[timestamp_col].dt.dayofweek  # 0=Monday, 6=Sunday
    df['day_name'] = df[timestamp_col].dt.day_name()    # 'Monday', 'Tuesday'
    
    # Binary flags (important trading days)
    df['is_monday'] = (df['day_of_week'] == 0).astype(int)
    df['is_friday'] = (df['day_of_week'] == 4).astype(int)
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    
    # Week features
    df['week_of_month'] = (df[timestamp_col].dt.day - 1) // 7 + 1
    df['week_of_year'] = df[timestamp_col].dt.isocalendar().week
    
    # Month boundaries (impact trading behavior)
    df['is_month_start'] = (df[timestamp_col].dt.day <= 5).astype(int)
    df['is_month_end'] = (df[timestamp_col].dt.day >= 25).astype(int)
    df['day_of_month'] = df[timestamp_col].dt.day
    
    return df
```

**Features Generated** (10 features):
- `day_of_week` - 0-6 (Monday-Sunday)
- `day_name` - String name
- `is_monday`, `is_friday`, `is_weekend` - Binary flags
- `week_of_month` - 1-5
- `week_of_year` - 1-52
- `is_month_start`, `is_month_end` - Binary flags
- `day_of_month` - 1-31

**ML Impact**: ⭐⭐⭐⭐⭐ (behavioral patterns per hari)

**Why Important?**
- Monday = Opening volatility (gap dari weekend)
- Friday = Position closing (avoid weekend risk)
- Month-end = Institutional rebalancing
- Week 1 = NFP release (first Friday of month)

---

### **Feature 3: Time Features** ⭐⭐⭐⭐

**Data Type**: Hour, minute, quarter (intraday patterns)

**Calculation**:
```python
def add_time_features(df, timestamp_col='time'):
    """
    Intraday time features
    """
    df['hour_utc'] = df[timestamp_col].dt.hour           # 0-23
    df['minute'] = df[timestamp_col].dt.minute           # 0-59
    df['quarter_hour'] = df['minute'] // 15              # 0-3
    
    # Binary flags untuk key hours
    df['is_market_open'] = df['hour_utc'].between(0, 22).astype(int)  # Forex 24/5
    df['is_london_open'] = df['hour_utc'].between(8, 16).astype(int)
    df['is_ny_open'] = df['hour_utc'].between(13, 22).astype(int)
    
    return df
```

**Features Generated** (6 features):
- `hour_utc`, `minute`, `quarter_hour` - Time components
- `is_market_open`, `is_london_open`, `is_ny_open` - Binary flags

**ML Impact**: ⭐⭐⭐⭐ (intraday volatility patterns)

---

## 🔄 Feature Engineering Workflow

```
┌─────────────────────────────────────────────────────────┐
│         AGGREGATED CANDLES (live/historical)            │
│  time, symbol, timeframe, OHLC, tick_count, spreads     │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │  Feature Engineering Service  │
        └───────────┬───────────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
        ▼           ▼           ▼
   ┌─────────┐ ┌─────────┐ ┌──────────┐
   │Calculated│ │External │ │Technical │
   │ Features│ │  Data   │ │Indicators│
   └────┬────┘ └────┬────┘ └────┬─────┘
        │           │           │
        │  Market   │ Economic  │  RSI
        │  Sessions │ Calendar  │  MACD
        │  Calendar │ FRED      │  Bollinger
        │  Time     │ Commodity │  Fibonacci
        │           │           │
        └───────────┴───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  COMPLETE ML FEATURES │
        │   (72 features total) │
        └───────────────────────┘
```

---

### **Summary: Storage Strategy**

| Feature Type | Storage | Calculation | Example |
|-------------|---------|-------------|---------|
| **Raw Ticks** | TimescaleDB/ClickHouse | Streamed/Batch | bid, ask, spread |
| **Aggregates** | ClickHouse | Tick Aggregator | OHLC, tick_count |
| **External Data** | ClickHouse | Scraper/API | Economic events, FRED |
| **Calculated Features** | **NONE** | Feature Engineering | Market sessions, calendar |
| **Technical Indicators** | **NONE** | Feature Engineering | RSI, MACD, Bollinger |

**Principle**: Only store raw/external data. Calculate derived features on-the-fly untuk flexibility.

---

## 📊 Aggregated Candles (OHLC Data)

**Purpose**: Time-series candles untuk trading analysis dan ML training

**Storage**: ClickHouse (analytics database)
**Flow**: `Raw Ticks → Tick Aggregator → ClickHouse`

**Timeframes**: 7 levels - 5m, 15m, 30m, 1h, 4h, 1d, 1w

**Aggregation Strategy**: **Flat Aggregation** (semua timeframe di-aggregate langsung dari raw ticks untuk accuracy)

---

### **Table 1: live_aggregates** (dari Polygon Live Ticks)

**Data Flow**:
```
TimescaleDB.market_ticks → Tick Aggregator → ClickHouse.live_aggregates
```

**Database**: ClickHouse
**Retention**: 90-180 hari (operational data)
**Update**: Real-time streaming aggregation

**Schema** (15 kolom):
```sql
CREATE TABLE suho_analytics.live_aggregates
(
    -- Primary keys
    time DateTime64(3, 'UTC'),                          -- Candle open time (UTC aligned)
    symbol String,                                      -- C:EURUSD, C:XAUUSD, dll
    timeframe Enum8('5m'=1, '15m'=2, '30m'=3, '1h'=4, 
                    '4h'=5, '1d'=6, '1w'=7),           -- Timeframe identifier
    
    -- OHLC (mid prices: (bid+ask)/2)
    open Decimal(18,5),                                 -- First tick mid price
    high Decimal(18,5),                                 -- Highest mid price
    low Decimal(18,5),                                  -- Lowest mid price
    close Decimal(18,5),                                -- Last tick mid price
    
    -- Volume metrics
    tick_count UInt32,                                  -- Volume proxy (total ticks)
    
    -- Spread metrics
    avg_spread Decimal(18,5),                          -- Average bid-ask spread
    max_spread Decimal(18,5),                          -- Maximum spread (volatility)
    min_spread Decimal(18,5),                          -- Minimum spread
    
    -- Volatility metrics
    price_range Decimal(18,5),                         -- high - low (intrabar range)
    pct_change Decimal(10,5),                          -- (close - open) / open * 100
    
    -- Quality flags
    is_complete UInt8,                                 -- 1 = closed candle, 0 = partial
    
    -- Metadata
    created_at DateTime64(3, 'UTC')                    -- Aggregation timestamp
)
ENGINE = MergeTree()
PARTITION BY (toYYYYMM(time), timeframe)
ORDER BY (symbol, timeframe, time);
```

**Primary Index**: (symbol, timeframe, time)

**Partition Strategy**: 
- Partitioned by month AND timeframe (e.g., `202510_4` = October 2025, 1h candles)
- Enables fast queries per timeframe
- Easy retention management (drop old partitions)

**Aggregation Example** (EUR/USD 5m candle):
```
Raw Ticks (14:00:00 - 14:05:00): 847 ticks
  → 14:00:01: bid=1.10501, ask=1.10503 (mid=1.10502)
  → 14:00:45: bid=1.10510, ask=1.10512 (mid=1.10511)
  → 14:04:59: bid=1.10508, ask=1.10510 (mid=1.10509)

Result:
{
  time: "2025-10-17 14:00:00",
  symbol: "C:EURUSD",
  timeframe: "5m",
  open: 1.10502,           // First tick
  high: 1.10515,           // Highest
  low: 1.10498,            // Lowest
  close: 1.10509,          // Last tick
  tick_count: 847,         // Total ticks
  avg_spread: 0.00002,     // Average spread
  max_spread: 0.00004,     // Volatility spike
  min_spread: 0.00001,     // Tightest spread
  price_range: 0.00017,    // 1.10515 - 1.10498
  pct_change: 0.0063,      // (1.10509-1.10502)/1.10502*100
  is_complete: 1           // Closed candle
}
```

**Karakteristik**:
- Write frequency: Continuous (new candles every timeframe interval)
- Query pattern: Recent data (last hours/days/weeks)
- Use Case: Live monitoring, recent backtesting, operational alerts

---

### **Table 2: historical_aggregates** (dari Dukascopy Historical Ticks)

**Data Flow**:
```
ClickHouse.historical_ticks → Historical Aggregator → ClickHouse.historical_aggregates
```

**Database**: ClickHouse
**Retention**: Unlimited (long-term storage)
**Update**: Batch processing (backfill historical)

**Schema** (15 kolom - **identik dengan live_aggregates**):
```sql
CREATE TABLE suho_analytics.historical_aggregates
(
    -- Primary keys
    time DateTime64(3, 'UTC'),
    symbol String,
    timeframe Enum8('5m'=1, '15m'=2, '30m'=3, '1h'=4, 
                    '4h'=5, '1d'=6, '1w'=7),
    
    -- OHLC
    open Decimal(18,5),
    high Decimal(18,5),
    low Decimal(18,5),
    close Decimal(18,5),
    
    -- Volume metrics
    tick_count UInt32,
    
    -- Spread metrics
    avg_spread Decimal(18,5),
    max_spread Decimal(18,5),
    min_spread Decimal(18,5),
    
    -- Volatility metrics
    price_range Decimal(18,5),
    pct_change Decimal(10,5),
    
    -- Quality flags
    is_complete UInt8,
    
    -- Metadata
    created_at DateTime64(3, 'UTC')
)
ENGINE = MergeTree()
PARTITION BY (toYYYYMM(time), timeframe)
ORDER BY (symbol, timeframe, time);
```

**Karakteristik**:
- Write frequency: Batch (daily backfill dari Dukascopy)
- Query pattern: Historical analysis (any timeframe, multi-year)
- Data quality: Complete (no gaps)
- Use Case: ML training, historical backtesting, research
- Compression: High (ClickHouse compression ~10:1)

---

### **Timeframe Synchronization**

Semua timeframes aligned dengan UTC boundaries:

```
Timeline UTC:
14:00:00 ──────→ 14:05:00 ──────→ 14:10:00 ──────→ 14:15:00 ──────→ 14:30:00
   │                │                │                │                │
   5m #1            5m #2            5m #3            5m #4            5m #5 & 5m #6
   
   └────────────────────────────────────────────────────────────────────┘
                              15m candle (14:15:00)
   
   └────────────────────────────────────────────────────────────────────────────────┘
                                   30m candle (14:00:00)
```

**Data Example**:
```sql
time                symbol      timeframe   open      high      low       close     tick_count
2025-10-17 14:00:00 C:EURUSD   5m          1.10502   1.10515   1.10498   1.10509   847
2025-10-17 14:05:00 C:EURUSD   5m          1.10510   1.10520   1.10505   1.10518   923
2025-10-17 14:10:00 C:EURUSD   5m          1.10519   1.10525   1.10512   1.10520   891

2025-10-17 14:00:00 C:EURUSD   15m         1.10502   1.10525   1.10498   1.10520   2661

2025-10-17 14:00:00 C:EURUSD   1h          1.10502   1.10545   1.10498   1.10540   10234
```

---

### **Query Pattern: Union Live + Historical for ML**

Untuk ML training, gabungkan kedua tabel:

```sql
-- Complete dataset: historical + recent live data
SELECT * FROM (
    -- Historical data (complete, compressed)
    SELECT * FROM suho_analytics.historical_aggregates
    WHERE time < '2025-10-15'
      AND symbol = 'C:EURUSD'
      AND timeframe = '1h'
    
    UNION ALL
    
    -- Recent live data (operational)
    SELECT * FROM suho_analytics.live_aggregates
    WHERE time >= '2025-10-15'
      AND symbol = 'C:EURUSD'
      AND timeframe = '1h'
)
ORDER BY time;
```

**Benefits**:
- Complete historical coverage (unlimited retention)
- Fresh live data (real-time updates)
- Efficient storage (historical compressed, live hot)
- Optimal for ML training (all data in one query)

---

### **Why 15 Columns?**

| Column | Purpose | ML Impact |
|--------|---------|-----------|
| **time, symbol, timeframe** | Primary keys | Essential for indexing |
| **open, high, low, close** | Price action | ⭐⭐⭐⭐⭐ Core features |
| **tick_count** | Activity/volume proxy | ⭐⭐⭐⭐ Liquidity indicator |
| **avg_spread, max_spread, min_spread** | Market conditions | ⭐⭐⭐⭐ Volatility/liquidity |
| **price_range** | Volatility | ⭐⭐⭐⭐ Breakout detection |
| **pct_change** | Momentum | ⭐⭐⭐⭐⭐ Direction prediction |
| **is_complete** | Quality flag | ⭐⭐⭐ Filter incomplete data |
| **created_at** | Tracking | ⭐ Debugging only |

**Total**: 15 kolom (lean, focused, ML-optimized)

---

### **Aggregation Process Flow**

```
┌─────────────────────────────────────────────────────────────────┐
│                    RAW TICK DATA                                │
│  TimescaleDB.market_ticks (live) or ClickHouse.historical_ticks│
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
                  ┌─────────────────┐
                  │ Tick Aggregator │
                  │   (Flat Mode)   │
                  └────────┬────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐
    │  5m, 15m   │  │  30m, 1h   │  │  4h, 1d, 1w│
    └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
          │               │               │
          └───────────────┴───────────────┘
                          │
                          ▼
          ┌───────────────────────────────┐
          │  ClickHouse Aggregates Table  │
          │  (live or historical)         │
          └───────────────────────────────┘
```

**Flat Aggregation Logic**:
```python
def aggregate_ticks_to_all_timeframes(ticks, timestamp):
    """
    Aggregate raw ticks to ALL timeframes in parallel
    Each timeframe calculated directly from raw ticks (not cascading)
    """
    results = []
    
    for tf in ['5m', '15m', '30m', '1h', '4h', '1d', '1w']:
        candle_start = round_to_timeframe(timestamp, tf)
        candle_ticks = filter_ticks_for_timeframe(ticks, candle_start, tf)
        
        candle = {
            'time': candle_start,
            'timeframe': tf,
            'open': candle_ticks[0].mid_price,
            'high': max(t.mid_price for t in candle_ticks),
            'low': min(t.mid_price for t in candle_ticks),
            'close': candle_ticks[-1].mid_price,
            'tick_count': len(candle_ticks),
            'avg_spread': mean(t.spread for t in candle_ticks),
            'max_spread': max(t.spread for t in candle_ticks),
            'min_spread': min(t.spread for t in candle_ticks),
            'price_range': max_price - min_price,
            'pct_change': (close - open) / open * 100,
            'is_complete': 1 if candle_closed else 0,
        }
        results.append(candle)
    
    return results
```

**Why Flat vs Hierarchical?**
- ✅ Most accurate (no cascading errors)
- ✅ tick_count accurate (actual ticks, not summed)
- ✅ Spread metrics precise (calculated from raw data)
- ❌ More computation (7x aggregation per batch)

For ML training accuracy, flat aggregation is worth the computational cost.

---
## = Perbedaan Storage Strategy

| Aspek | TimescaleDB (Live) | ClickHouse (Historical) |
|-------|-------------------|------------------------|
| **Use Case** | Real-time trading | Historical analysis |
| **Write Pattern** | Streaming (real-time) | Batch (backfill) |
| **Write Speed** | Fast (optimized for inserts) | Very fast (batch inserts) |
| **Query Pattern** | Recent data (hot data) | Any timeframe (cold data) |
| **Retention** | 90 hari | Unlimited |
| **Compression** | Moderate | High (10:1) |
| **Storage Cost** | Higher (SSD) | Lower (compressed) |
| **Data Age** | 0-90 days | > 90 days or historical |

---

## =� Next Steps (Belum Dibahas)

- [x] Flow dari tick ke aggregates (candle generation) ✅ COMPLETED
- [ ] Flow dari aggregates ke ML features (feature engineering service)
- [ ] Query patterns untuk each use case
- [ ] Data lifecycle management
- [ ] Backup & recovery strategy

---

**Status**: Dokumentasi bertahap - akan dilanjutkan sesuai diskusi

**Version History**:
- v1.5.0 (2025-10-17): Separated External Data (3 sources) vs Calculated Features (Market Sessions, Calendar, Time) - Market Sessions moved to Feature Engineering
- v1.4.0 (2025-10-17): Added aggregates tables (live + historical) with 15 columns, flat aggregation strategy, 7 timeframes
- v1.3.0 (2025-10-17): Added 4 external data tables with timestamp concept for ML (Economic Calendar, FRED, Market Sessions, Commodity Prices)
- v1.2.0 (2025-10-17): Finalized 2-source architecture - Polygon Live + Dukascopy Historical only, archived Polygon Historical
- v1.1.0 (2025-10-17): Simplified schema - reduced from 14 to 6 core columns, removed redundant fields
- v1.0.0 (2025-10-17): Initial draft - Live vs Historical storage concept
