# Feature Engineering Service

**Status:** ✅ **PRODUCTION READY**

Generates 63 ML features from OHLCV data + 26 technical indicators + 6 external data sources.

---

## Overview

### Purpose
Transforms raw market data into 63 ML features for XGBoost model training and inference.

### Input
- **Aggregates table** (ClickHouse): OHLCV + 26 indicators (RSI, MACD, ATR, etc.)
- **External data tables** (ClickHouse): Economic calendar, market sessions, sentiment, etc.
- **Multi-timeframe context**: M5, M15, H1, H4, D1, W1

### Output
- **ml_training_data table** (ClickHouse): 63 features + metadata + target variable

---

## Architecture

### Service Components

```
┌─────────────────────────────────────────────────┐
│         Feature Engineering Service              │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │     main.py (Orchestrator)                │  │
│  │  • Historical processing (5 years)        │  │
│  │  • Continuous mode (real-time)            │  │
│  │  • Central Hub registration               │  │
│  └──────────────────────────────────────────┘  │
│                       │                          │
│  ┌──────────────────────────────────────────┐  │
│  │  feature_calculator.py (Coordinator)      │  │
│  │  Orchestrates 11 feature calculators      │  │
│  └──────────────────────────────────────────┘  │
│                       │                          │
│  ┌─────────────────────────────────────────┐   │
│  │       11 Feature Calculators             │   │
│  │  • NewsCalendarFeatures (8 features)     │   │
│  │  • PriceActionFeatures (10 features)     │   │
│  │  • MultiTimeframeFeatures (9 features)   │   │
│  │  • CandlestickPatternFeatures (9 feat.)  │   │
│  │  • VolumeFeatures (8 features)           │   │
│  │  • VolatilityRegimeFeatures (6 features) │   │
│  │  • DivergenceFeatures (4 features)       │   │
│  │  • MarketContextFeatures (6 features)    │   │
│  │  • MomentumFeatures (3 features)         │   │
│  │  • MovingAverageFeatures (2 features)    │   │
│  │  • StructureSLTPFeatures (5 features)    │   │
│  └─────────────────────────────────────────┘   │
│                       │                          │
│  ┌──────────────────────────────────────────┐  │
│  │  clickhouse_client.py                     │  │
│  │  • Read: aggregates, external_data        │  │
│  │  • Write: ml_training_data                │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

---

## 63 Features Breakdown

### Tier 1: Critical Features (50%+ Importance)

#### **News/Calendar (8 features - 20% importance)**
1. `upcoming_high_impact_events_4h` - Count of high-impact events in next 4h
2. `time_to_next_event_minutes` - Minutes until next economic event
3. `event_impact_score` - 1=low, 2=medium, 3=high
4. `is_pre_news_zone` - 1-2h before high-impact (entry window)
5. `is_post_news_zone` - 30-60min after release (re-entry opportunity)
6. `event_type_category` - NFP/CPI/Fed/GDP/ECB categorization
7. `actual_vs_forecast_deviation` - Surprise factor (%)
8. `historical_event_volatility` - Avg pips moved for this event type

#### **Price Action/Structure (10 features - 18% importance)**
1. `support_resistance_distance` - Distance to nearest S/R (pips)
2. `is_at_key_level` - Price within 20 pips of S/R
3. `order_block_zone` - Inside order block (institutional zone)
4. `swing_high_low_distance` - Distance to swing points (pips)
5. `price_rejection_wick` - Wick rejection (% of candle)
6. `h4_trend_direction` - H4 trend: 1=up, -1=down, 0=neutral
7. `h4_support_resistance_distance` - H4 S/R distance (pips)
8. `d1_support_resistance_distance` - D1 S/R distance (pips)
9. `w1_swing_high_low` - Weekly swing level (price)
10. `multi_tf_alignment` - TF alignment score (0-6)

### Tier 2: High Importance (15% each)

#### **Multi-Timeframe (9 features - 15% importance)**
1. `m5_momentum` - M5 Rate of Change (%)
2. `m15_consolidation` - M15 BB width < threshold (0/1)
3. `h1_trend` - H1 trend: 1=up, -1=down, 0=neutral
4. `h4_structure` - bullish_structure/bearish_structure/neutral
5. `d1_bias` - D1 bias: 1=bullish, -1=bearish, 0=neutral
6. `w1_major_level` - Weekly major level (price)
7. `tf_alignment_score` - All TFs alignment (0-6)
8. `h4_h1_divergence` - H4/H1 trend conflict (0/1)
9. `d1_w1_alignment` - D1/W1 agreement (0/1)

#### **Candlestick Patterns (9 features - 15% importance)**
1. `bullish_engulfing` - Bullish engulfing pattern (0/1)
2. `bearish_engulfing` - Bearish engulfing pattern (0/1)
3. `pin_bar_bullish` - Bullish pin bar (0/1)
4. `pin_bar_bearish` - Bearish pin bar (0/1)
5. `doji_indecision` - Doji pattern (0/1)
6. `hammer_reversal` - Hammer reversal (0/1)
7. `shooting_star` - Shooting star (0/1)
8. `morning_star` - Morning star (3-candle bullish) (0/1)
9. `evening_star` - Evening star (3-candle bearish) (0/1)

#### **Volume Analysis (8 features - 15% importance)**
1. `volume_spike` - Volume > 2x average (0/1)
2. `volume_profile` - Volume percentile rank (0-1)
3. `buying_pressure` - (Close-Low)/(High-Low)
4. `selling_pressure` - (High-Close)/(High-Low)
5. `volume_momentum` - Volume ROC over 3 candles (%)
6. `volume_at_level` - Cumulative volume at S/R level
7. `delta_volume` - Buy-Sell volume approximation
8. `volume_divergence` - Price/Volume divergence: 1=bullish, -1=bearish, 0=none

### Tier 3: Medium Importance

#### **Volatility/Regime (6 features - 12% importance)**
1. `atr_current` - Current ATR (pips)
2. `atr_expansion` - ATR increasing (0/1)
3. `true_range_pct` - True range as % of price
4. `volatility_regime` - 1=low, 2=medium, 3=high (Gold-specific)
5. `adx_value` - Trend strength (>25=trending)
6. `bb_width` - Bollinger Band width (%)

#### **Divergence (4 features - 10% importance)**
1. `rsi_price_divergence` - RSI/Price divergence: 1=bullish, -1=bearish, 0=none
2. `macd_price_divergence` - MACD/Price divergence: 1=bullish, -1=bearish, 0=none
3. `volume_price_divergence` - Volume/Price divergence: 1=bullish, -1=bearish, 0=none
4. `divergence_strength` - Combined divergence score (-3 to +3)

#### **Market Context (6 features - 8% importance)**
1. `is_london_session` - London session active (0/1)
2. `is_new_york_session` - NY session active (0/1)
3. `is_asian_session` - Asian session active (0/1)
4. `liquidity_level` - 1=low, 2=medium, 3=high (overlap=high)
5. `day_of_week` - 0=Monday, 4=Friday
6. `time_of_day_category` - asian_open/london_open/overlap/ny_open/after_hours

### Tier 4: Low Importance

#### **Momentum (3 features - 5% importance)**
1. `rsi_value` - RSI (0-100)
2. `macd_histogram` - MACD histogram value
3. `stochastic_k` - Stochastic %K (0-100)

#### **Moving Averages (2 features - 2% importance)**
1. `sma_200` - SMA 200 (dynamic S/R)
2. `ema_50` - EMA 50 (trend confirmation)

#### **Structure SL/TP (5 features - 5% importance)**
1. `nearest_support_distance` - Distance to support (pips)
2. `nearest_resistance_distance` - Distance to resistance (pips)
3. `structure_risk_reward` - Structure RR ratio
4. `atr_based_sl_distance` - ATR × 1.5 (pips)
5. `structure_based_tp_distance` - Structure-based TP (pips)

---

## Target Variable

### Binary Classification
- `target`: 0 = not profitable (< 15 pips), 1 = profitable (≥ 15 pips)
- `target_pips`: Actual pips moved (for regression models)

---

## Usage

### Build & Deploy
```bash
# Build Docker image
docker build -t suho-feature-engineering \
  -f 03-machine-learning/feature-engineering-service/Dockerfile .

# Deploy via docker-compose
docker-compose up -d feature-engineering-service

# View logs
docker logs -f suho-feature-engineering
```

### Environment Variables
```bash
CENTRAL_HUB_URL=http://suho-central-hub:7000
CLICKHOUSE_HOST=suho-clickhouse
CLICKHOUSE_PORT=8123
CLICKHOUSE_DATABASE=suho_analytics
CLICKHOUSE_USER=suho_analytics
CLICKHOUSE_PASSWORD=clickhouse_secure_2024
SERVICE_NAME=feature-engineering-service
SERVICE_TYPE=ml-feature-engineering
SERVICE_VERSION=1.0.0
LOG_LEVEL=INFO
```

### Processing Modes

#### 1. Historical Processing (5 years)
Processes 2020-2024 data for ML training:
```python
# Automatically runs on startup
# Queries: aggregates table (H1 timeframe)
# Generates: ~43,800 training samples (5 years × 365 days × 24 hours)
# Duration: ~30-60 minutes (depends on data size)
```

#### 2. Continuous Mode (Real-time)
Runs every hour to process new candles:
```python
# Runs continuously after historical processing
# Waits for next hour boundary
# Processes last hour candle
# Sends heartbeat to Central Hub
```

---

## Database Schema

### Input Tables

#### aggregates (ClickHouse)
- Columns: symbol, timeframe, timestamp, OHLCV, indicators (JSON with 26 indicators)
- Source: tick-aggregator service

#### external_economic_calendar
- Columns: date, event, impact, actual, forecast, country
- Source: external-data-collector

#### external_market_sessions
- Columns: session_name, start_time, end_time, timezone

#### external_fear_greed_index
- Columns: date, value, classification

#### external_commodity_prices
- Columns: date, gold_price, oil_price, etc.

#### external_crypto_sentiment
- Columns: date, btc_sentiment, eth_sentiment

#### external_fred_economic
- Columns: date, series_id, value

### Output Table

#### ml_training_data (ClickHouse)
- **84 columns**: metadata (9) + price (5) + 63 features + target (2) + quality (5)
- **Partitioning**: By month (toYYYYMM(timestamp))
- **Ordering**: (symbol, timeframe, timestamp)
- **Indexes**: target, volatility_regime, event_type_category

#### ml_training_stats (Materialized View)
- Daily statistics: total_samples, profitable_samples, avg_pips, avg_quality
- Auto-updates on INSERT to ml_training_data

---

## Configuration

### features.yaml
```yaml
# Primary trading pair
primary_pair: "XAU/USD"

# Multi-timeframe configuration
timeframes:
  m5: "5m"
  m15: "15m"
  h1: "1h"
  h4: "4h"
  d1: "1d"
  w1: "1w"

# Target variable
target:
  type: "binary"  # binary or regression
  prediction_horizon_candles: 1  # Next candle
  profit_threshold_pips: 15  # For binary labeling

# Feature groups (11 groups)
feature_groups:
  news_calendar:
    enabled: true
    importance: 0.20
    lookback_hours: 4
    news_blackout_minutes: 15

  price_action:
    enabled: true
    importance: 0.18
    support_resistance_threshold: 20  # pips
    order_block_threshold: 20  # pips

  # ... (10 more groups)
```

---

## Performance

### Historical Processing
- **Input**: ~43,800 H1 candles (5 years)
- **Output**: ~43,800 training samples (63 features each)
- **Duration**: 30-60 minutes (with multi-TF queries)
- **Memory**: ~2GB peak

### Real-time Processing
- **Frequency**: Every hour (on the hour)
- **Latency**: <5 seconds per candle
- **Memory**: ~500MB steady state

---

## Monitoring

### Health Checks
```bash
# Check service logs
docker logs suho-feature-engineering

# Check Central Hub registration
curl http://localhost:7000/api/discovery/services | jq '.[] | select(.service_name=="feature-engineering-service")'

# Query ml_training_data
docker exec suho-clickhouse clickhouse-client \
  --user suho_analytics \
  --password clickhouse_secure_2024 \
  --database suho_analytics \
  --query "SELECT count() FROM ml_training_data"
```

### Key Metrics
- **Processing rate**: Candles/second
- **Feature completeness**: % of features calculated
- **Data quality score**: 0-1 (average across all samples)
- **Target distribution**: Profitable vs unprofitable ratio

---

## Next Steps

1. ✅ **Feature Engineering Service** - COMPLETE
2. ⏳ **Model Training Service** - XGBoost training on ml_training_data
3. ⏳ **Prediction Service** - Real-time inference using trained model
4. ⏳ **Backtesting Service** - Validate model performance

---

## Files Structure

```
feature-engineering-service/
├── Dockerfile                  # Multi-stage build with TA-Lib
├── .dockerignore              # Exclude cache/logs
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── config/
│   └── features.yaml          # Feature configuration (63 features)
├── src/
│   ├── main.py               # Service entry point
│   ├── feature_calculator.py # Main orchestrator
│   ├── clickhouse_client.py  # Database client
│   ├── central_hub_sdk.py    # Central Hub integration
│   └── features/             # 11 feature calculators
│       ├── __init__.py
│       ├── news_calendar.py
│       ├── price_action.py
│       ├── multi_timeframe.py
│       ├── candlestick_patterns.py
│       ├── volume_analysis.py
│       ├── volatility_regime.py
│       ├── divergence.py
│       ├── market_context.py
│       ├── momentum.py
│       ├── moving_averages.py
│       └── structure_sl_tp.py
└── migrations/
    ├── README.md              # Migration instructions
    └── 001_create_ml_training_data.sql  # ClickHouse table schema
```

---

**Last Updated:** 2025-10-08
**Version:** 1.0.0
**Status:** ✅ Production Ready
