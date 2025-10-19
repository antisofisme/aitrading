---
name: feature-engineering
description: Calculates 110 ML features from candles and external data for both training (historical with targets) and inference (live without targets). Powers the entire ML pipeline.
license: MIT
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
metadata:
  type: Data Processing (ML Features)
  phase: Data Foundation (Phase 1)
  status: Active Production
  priority: P0 (Critical - ML depends on this)
  port: 8007
  dependencies:
    - central-hub
    - clickhouse
    - nats
    - kafka
  version: 2.0.0
---

# Feature Engineering Service

Calculates 110 derived ML features from OHLCV candles and external data. Operates in dual mode: historical (with future targets for training) and live (without targets for inference). **CRITICAL**: NO raw OHLC stored in ml_features table - only derived features.

## When to Use This Skill

Use this skill when:
- Adding new technical indicators or features
- Debugging missing or NULL features
- Implementing multi-timeframe feature calculations
- Integrating external data (economic calendar, FRED, commodities)
- Optimizing feature calculation performance
- Verifying historical vs live mode behavior
- Fixing feature data quality issues

## Service Overview

**Type:** Data Processing (ML Feature Computation)
**Port:** 8007
**Input:** NATS (`bars.>`) + ClickHouse (`aggregates`, `external_*`)
**Output:** ClickHouse (`ml_features` table) + NATS (`features.{symbol}.{timeframe}`)
**Features:** 110 derived features (NO raw OHLC!)
**Mode:** Dual (historical with targets + live without targets)

**Dependencies:**
- **Upstream**:
  - tick-aggregator (provides candles via NATS `bars.*`)
  - external-data-collector (economic data, FRED, commodities)
- **Downstream**:
  - supervised-training (reads historical ml_features)
  - finrl-training (reads historical ml_features)
  - inference (subscribes to `features.*` via NATS)
- **Infrastructure**: ClickHouse, NATS cluster, Kafka (optional)

## Key Capabilities

- 110 derived ML features (no raw OHLC)
- Dual mode: historical (with targets) + live (no targets)
- Real-time feature publishing via NATS
- Technical indicators (RSI, MACD, Bollinger, etc.)
- Fibonacci support/resistance levels
- Market session features (London/NY/Tokyo)
- Multi-timeframe context features
- External data integration (economic calendar, FRED)
- Feature validation (no NULL in critical features)

## Architecture

### Data Flow

```
NATS: bars.> (subscribe real-time candles)
  +
ClickHouse.aggregates (read historical candles)
  +
ClickHouse.external_* (economic calendar, FRED, commodities)
  ↓
feature-engineering-service
  ├─→ Calculate technical indicators (35 features)
  ├─→ Calculate Fibonacci levels (8 features)
  ├─→ Calculate market sessions (6 features)
  ├─→ Calculate calendar features (5 features)
  ├─→ Calculate lagged features (20 features)
  ├─→ Calculate rolling stats (15 features)
  ├─→ Calculate multi-timeframe (15 features)
  ├─→ Join external data (6 features)
  └─→ Calculate targets (5 targets - historical only!)
  ↓
├─→ ClickHouse.ml_features (110 features ONLY)
├─→ NATS: features.{symbol}.{timeframe} (real-time)
└─→ Kafka: ml_features_archive (optional)
```

### Feature Breakdown (110 Total)

**1. Technical Indicators (35 features)**
- RSI (7, 14, 21 periods)
- MACD (12, 26, 9)
- Bollinger Bands (upper, middle, lower)
- Stochastic (%K, %D)
- ATR (14)
- ADX (14)
- CCI (20)
- MFI (14)
- Williams %R
- ROC (Rate of Change)

**2. Fibonacci Levels (8 features)**
- Support levels (23.6%, 38.2%, 50%, 61.8%)
- Resistance levels (23.6%, 38.2%, 50%, 61.8%)

**3. Market Sessions (6 features)**
- London session open/close
- NY session open/close
- Tokyo session open/close
- Session overlap indicators

**4. Calendar Features (5 features)**
- Day of week
- Hour of day
- Month boundary
- Quarter boundary
- Is holiday

**5. Lagged Features (20 features)**
- Previous 1, 2, 3, 5, 10 candles (OHLC changes)

**6. Rolling Statistics (15 features)**
- 20-period rolling mean/std
- 50-period rolling mean/std
- Support/resistance zones

**7. Multi-Timeframe Features (15 features)**
- Higher timeframe context (e.g., 1h context for 5m)
- Trend alignment across timeframes

**8. External Data (6 features)**
- Economic event proximity
- FRED indicators (unemployment, GDP)
- Commodity correlations (oil, gold)

**9. Targets (5 targets - HISTORICAL MODE ONLY)**
- `future_return_5m` - 5-minute ahead return
- `future_return_15m` - 15-minute ahead return
- `future_return_1h` - 1-hour ahead return
- `future_return_direction` - Binary (up/down)
- `future_volatility` - Forward-looking volatility

**CRITICAL**: ml_features table has **110 columns** (features only, NO OHLC)
- Historical mode: 110 features + 5 targets = 115 columns
- Live mode: 110 features + 0 targets = 110 columns

### Configuration

**Operational Config (Central Hub):**
```json
{
  "operational": {
    "mode": "live",
    "enable_nats_publishing": true,
    "enable_kafka_archival": false,
    "feature_validation_enabled": true,
    "null_threshold": 0.05,
    "cache_window_size": 1000,
    "external_data_join_enabled": true
  }
}
```

## Examples

### Example 1: Fetch Config from Central Hub

```python
from shared.components.config import ConfigClient

# Initialize client
client = ConfigClient(
    service_name="feature-engineering",
    safe_defaults={
        "operational": {
            "mode": "live",
            "enable_nats_publishing": True,
            "null_threshold": 0.05
        }
    }
)
await client.init_async()

# Get config
config = await client.get_config()
mode = config['operational']['mode']
print(f"Feature engineering mode: {mode}")
```

### Example 2: Calculate Features for Candle

```python
from feature_engineering import FeatureCalculator

calculator = FeatureCalculator(mode="live")

# Calculate features from candle
features = await calculator.calculate_features(
    symbol="EURUSD",
    timeframe="5m",
    candle=candle_data,
    include_targets=False  # Live mode - no targets
)

# Result: 110 features (no OHLC, no targets)
print(f"Features calculated: {len(features)}")  # 110
```

### Example 3: Query ML Features from ClickHouse

```sql
-- Check feature table schema (should be 110 columns + metadata)
DESCRIBE ml_features;

-- Query recent features
SELECT
    symbol,
    timeframe,
    timestamp,
    rsi_14,
    macd_signal,
    bb_upper,
    fibonacci_support_382,
    session_london_active,
    future_return_5m  -- Only in historical mode!
FROM ml_features
WHERE symbol = 'EURUSD'
  AND timeframe = '5m'
  AND timestamp > now() - INTERVAL 1 HOUR
ORDER BY timestamp DESC
LIMIT 10;

-- Count NULL features (should be < 5%)
SELECT
    COUNT(*) as total_rows,
    SUM(CASE WHEN rsi_14 IS NULL THEN 1 ELSE 0 END) as null_rsi,
    SUM(CASE WHEN macd_signal IS NULL THEN 1 ELSE 0 END) as null_macd,
    (SUM(CASE WHEN rsi_14 IS NULL THEN 1 ELSE 0 END) / COUNT(*)) * 100 as null_percentage
FROM ml_features;
```

### Example 4: Subscribe to Real-time Features (NATS)

```bash
# Subscribe to all features for EURUSD
nats sub "features.EURUSD.*"

# Subscribe to all 5m features
nats sub "features.*.5m"

# Subscribe to all features
nats sub "features.*.*"
```

### Example 5: Switch Between Historical and Live Mode

```bash
# Set to historical mode (with targets)
curl -X POST http://suho-central-hub:7000/api/v1/config/feature-engineering \
  -H "Content-Type: application/json" \
  -d '{
    "operational": {
      "mode": "historical"
    }
  }'

# Set to live mode (no targets)
curl -X POST http://suho-central-hub:7000/api/v1/config/feature-engineering \
  -H "Content-Type: application/json" \
  -d '{
    "operational": {
      "mode": "live"
    }
  }'
```

## Guidelines

- **ALWAYS** use ConfigClient for operational settings (mode, validation thresholds)
- **NEVER** store raw OHLC in ml_features table (only derived features!)
- **ALWAYS** calculate targets for historical mode (training needs targets)
- **NEVER** calculate targets for live mode (no future data available)
- **VERIFY** all 110 features calculated (no missing features)
- **VALIDATE** NULL percentage < 5% (critical features must not be NULL)

## Critical Rules

1. **Config Hierarchy:**
   - Mode (historical/live) → Central Hub (operational config)
   - Safe defaults → ConfigClient fallback
   - No secrets needed

2. **NO Raw OHLC in ml_features:**
   - **NEVER** store open, high, low, close, volume in ml_features
   - **ONLY** derived features (RSI, MACD, Fibonacci, etc.)
   - **REASON**: Prevent data leakage, force feature engineering

3. **Historical vs Live Mode:**
   - **Historical**: Calculate targets (future_return_5m, etc.)
   - **Live**: NO targets (future data not available)
   - **VERIFY**: Mode set correctly in config

4. **Feature Validation:**
   - **CHECK** NULL percentage < 5%
   - **VALIDATE** critical features (RSI, MACD, Bollinger) not NULL
   - **REJECT** features if validation fails

5. **External Data Join:**
   - **ENABLE** in config (`external_data_join_enabled`)
   - **VERIFY** external data available before join
   - **HANDLE** missing external data gracefully

## Common Tasks

### Add New Technical Indicator
1. Update `src/features/technical_indicators.py` (add indicator function)
2. Add to feature list in `calculate_features()`
3. Update ml_features table schema (add column)
4. Test with historical data
5. Verify NULL percentage acceptable

### Add External Data Feature
1. Ensure external data available in ClickHouse (external_* tables)
2. Implement join logic in `join_external_data()`
3. Add to feature list (increment count to 111)
4. Update schema
5. Test join performance

### Debug Missing Features
1. Check candles exist in ClickHouse
2. Verify external data available (if using)
3. Review feature calculation logs for errors
4. Check NULL percentage
5. Test feature calculation with sample data

### Optimize Feature Calculation
1. Profile feature calculation time per feature
2. Cache intermediate results (rolling windows)
3. Use vectorized operations (NumPy/Pandas)
4. Parallelize feature groups
5. Monitor memory usage

## Troubleshooting

### Issue 1: High NULL Percentage (> 5%)
**Symptoms:** Many features NULL in ml_features table
**Solution:**
- Check source candles quality (sufficient history for indicators)
- Review indicator parameters (e.g., RSI needs 14+ candles)
- Verify external data join working
- Increase warmup period for rolling features

### Issue 2: Features Not Publishing to NATS
**Symptoms:** Inference service not receiving features
**Solution:**
- Check `enable_nats_publishing` in config
- Verify NATS cluster connectivity
- Review publishing logs for errors
- Test with `nats sub "features.*.*"`

### Issue 3: Historical Mode Has No Targets
**Symptoms:** Training fails due to missing targets
**Solution:**
- Verify mode set to "historical" in config
- Check future data available for target calculation
- Review target calculation logic
- Ensure sufficient candles after current timestamp

### Issue 4: Raw OHLC Found in ml_features
**Symptoms:** Data leakage in training
**Solution:**
- **CRITICAL**: Remove OHLC columns immediately
- Review feature list (only derived features)
- Update schema to exclude OHLC
- Verify feature extraction logic

### Issue 5: External Data Join Failing
**Symptoms:** External features always NULL
**Solution:**
- Check external_* tables populated
- Verify timestamp alignment logic
- Review join query performance
- Enable debug logging for joins
- Test with sample data

## Validation Checklist

After making changes to this service:
- [ ] ml_features table has 110 columns (NOT 115 with OHLC!)
- [ ] Features calculated for all symbols + timeframes
- [ ] Historical mode: targets exist (future_return_5m, etc.)
- [ ] Live mode: NO targets (only 110 features)
- [ ] NULL percentage < 5% for critical features
- [ ] NATS publishes `features.*.*` (inference subscribes)
- [ ] No raw OHLC in ml_features table
- [ ] External data join working (if enabled)
- [ ] ConfigClient fetching from Central Hub
- [ ] Hot-reload responding to config updates

## Related Skills

- `central-hub` - Provides operational config and service discovery
- `tick-aggregator` - Provides candles via NATS
- `external-data-collector` - Provides external data for features
- `supervised-training` - Consumes historical features
- `finrl-training` - Consumes historical features
- `inference` - Consumes live features via NATS

## References

- Full Documentation: `docs/SERVICE_ARCHITECTURE_AND_FLOW.md` (lines 420-454)
- Planning Guide: `docs/PLANNING_SKILL_GUIDE.md` (Service 7, lines 810-1050)
- Flow + Messaging: `docs/SERVICE_FLOW_TREE_WITH_MESSAGING.md` (lines 310-372)
- Database Schema: `docs/table_database_process.md` (ml_features table - v2.0.0)
- Config Architecture: `docs/CONFIG_ARCHITECTURE.md`
- Central Hub Skill: `.claude/skills/central-hub/SKILL.md`
- Code: `02-data-processing/feature-engineering-service/`

---

**Created:** 2025-10-19
**Version:** 2.0.0
**Status:** Production Ready
