---
name: inference
description: Real-time prediction service that loads trained ML models/RL agents and generates trading signals from live ml_features with sub-100ms latency requirement
license: MIT
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
metadata:
  type: Machine Learning (Inference)
  phase: Live Trading (Phase 3)
  status: To Implement
  priority: P2 (High - core trading capability)
  port: 8010
  dependencies:
    - central-hub
    - clickhouse
    - nats
    - kafka
  version: 1.0.0
---

# Inference Service

Real-time prediction service that loads trained models (supervised ML) or agents (reinforcement learning) and generates trading signals from live ml_features with sub-100ms latency requirement for high-frequency trading.

## When to Use This Skill

Use this skill when:
- Deploying trained models to production
- Generating real-time trading signals
- Debugging inference latency issues
- Implementing model versioning and hot-swapping
- Monitoring model performance drift
- Optimizing prediction throughput

## Service Overview

**Type:** Machine Learning (Real-time Inference)
**Port:** 8010
**Input:** NATS (`features.>`) + ClickHouse (`ml_features` latest candle fallback)
**Output:** ClickHouse (`trading_signals`, `model_predictions`) + NATS + Kafka
**Models:** Loads from `model_checkpoints` (supervised) or `agent_checkpoints` (RL)
**Latency Requirement:** < 100ms per prediction
**Throughput:** Handle 100+ predictions/second

**Dependencies:**
- **Upstream**:
  - feature-engineering (provides live features via NATS)
  - supervised-training OR finrl-training (trained models/agents)
- **Downstream**: risk-management (consumes signals via NATS)
- **Infrastructure**: ClickHouse, NATS cluster, Kafka

## Key Capabilities

- Real-time model inference (< 100ms latency)
- Load trained models from checkpoints
- Subscribe to live features via NATS
- Generate trading signals (buy/sell/hold/close)
- Model versioning and hot-swapping
- Performance monitoring and drift detection
- Signal validation and formatting
- Dual publishing (NATS + Kafka for audit)

## Architecture

### Data Flow

```
NATS: features.> (subscribe real-time features)
  ↓ (Feature stream)
inference-service
  ├─→ Load model from ClickHouse.model_checkpoints
  ├─→ Predict signal (buy/sell/hold/close)
  ├─→ Calculate confidence score
  ├─→ Determine entry/SL/TP levels
  ↓
├─→ ClickHouse.trading_signals (persist)
├─→ ClickHouse.model_predictions (debug/monitoring)
├─→ NATS: signals.{symbol} (real-time to risk-mgmt)
└─→ Kafka: trading_signals_archive (audit trail)
```

### Signal Types

| Type | Description | Risk Level |
|------|-------------|------------|
| **buy** | Open long position | High |
| **sell** | Open short position | High |
| **hold** | Do nothing | Low |
| **close_long** | Close existing long | Medium |
| **close_short** | Close existing short | Medium |

### Signal Format

```json
{
  "signal_id": "uuid-here",
  "symbol": "EURUSD",
  "timeframe": "5m",
  "timestamp_ms": 1760867890000,
  "signal_type": "buy",
  "confidence_score": 0.85,
  "entry_price": 1.08125,
  "stop_loss": 1.08000,
  "take_profit": 1.08500,
  "position_size_recommended": 0.01,
  "model_version": "xgboost-v1.2.3",
  "metadata": {
    "features_used": 110,
    "prediction_latency_ms": 45,
    "model_type": "xgboost"
  }
}
```

### Configuration

**Operational Config (Central Hub):**
```json
{
  "operational": {
    "model_config": {
      "model_type": "xgboost",
      "model_version": "1.2.3",
      "checkpoint_path": "models/xgboost_eurusd_5m_v1.2.3.pkl",
      "auto_reload": true
    },
    "inference_settings": {
      "confidence_threshold": 0.7,
      "max_latency_ms": 100,
      "fallback_to_hold": true
    },
    "signal_generation": {
      "calculate_entry_price": true,
      "calculate_sl_tp": true,
      "atr_multiplier_sl": 2.0,
      "atr_multiplier_tp": 3.0
    },
    "monitoring": {
      "track_latency": true,
      "track_predictions": true,
      "alert_on_drift": true
    }
  }
}
```

## Examples

### Example 1: Fetch Config from Central Hub

```python
from shared.components.config import ConfigClient

# Initialize client
client = ConfigClient(
    service_name="inference",
    safe_defaults={
        "operational": {
            "model_config": {"model_type": "xgboost"},
            "inference_settings": {"confidence_threshold": 0.7},
            "signal_generation": {"calculate_sl_tp": True}
        }
    }
)
await client.init_async()

# Get config
config = await client.get_config()
model_version = config['operational']['model_config']['model_version']
confidence_threshold = config['operational']['inference_settings']['confidence_threshold']
print(f"Using model version {model_version}, confidence threshold {confidence_threshold}")
```

### Example 2: Load Model and Run Inference

```python
from inference_service import InferenceEngine

engine = InferenceEngine()

# Load model from checkpoint
model = await engine.load_model(
    model_type="xgboost",
    version="1.2.3",
    symbol="EURUSD",
    timeframe="5m"
)

# Subscribe to live features
await engine.subscribe_features("features.EURUSD.5m", callback=generate_signal)

async def generate_signal(features):
    # Predict
    start_time = time.time()
    prediction = model.predict(features)
    latency = (time.time() - start_time) * 1000

    # Generate signal
    signal = await engine.create_signal(
        prediction=prediction,
        features=features,
        latency_ms=latency
    )

    # Publish to NATS + Kafka
    await engine.publish_signal(signal)
```

### Example 3: Calculate Entry/SL/TP Levels

```python
from signal_generator import SignalGenerator

generator = SignalGenerator()

# Calculate levels using ATR
signal = await generator.calculate_levels(
    symbol="EURUSD",
    signal_type="buy",
    current_price=1.08125,
    atr=0.00125,  # From features
    atr_multiplier_sl=2.0,
    atr_multiplier_tp=3.0
)

# Result:
# {
#   "entry_price": 1.08125,
#   "stop_loss": 1.08000,    # entry - (ATR * 2.0)
#   "take_profit": 1.08500   # entry + (ATR * 3.0)
# }
```

### Example 4: Query Trading Signals from ClickHouse

```sql
-- Check recent signals
SELECT
    signal_id,
    symbol,
    timeframe,
    timestamp_ms,
    signal_type,
    confidence_score,
    entry_price,
    stop_loss,
    take_profit,
    model_version
FROM trading_signals
WHERE symbol = 'EURUSD'
  AND timestamp_ms > (now() - INTERVAL 1 HOUR) * 1000
ORDER BY timestamp_ms DESC
LIMIT 20;

-- Calculate signal distribution
SELECT
    signal_type,
    COUNT(*) as count,
    AVG(confidence_score) as avg_confidence
FROM trading_signals
WHERE timestamp_ms > (now() - INTERVAL 1 DAY) * 1000
GROUP BY signal_type
ORDER BY count DESC;

-- Monitor prediction latency
SELECT
    symbol,
    AVG(JSONExtractFloat(metadata, 'prediction_latency_ms')) as avg_latency_ms,
    MAX(JSONExtractFloat(metadata, 'prediction_latency_ms')) as max_latency_ms
FROM trading_signals
WHERE timestamp_ms > (now() - INTERVAL 1 HOUR) * 1000
GROUP BY symbol;
```

### Example 5: Subscribe to Real-time Signals (NATS)

```bash
# Subscribe to all signals
nats sub "signals.*"

# Subscribe to EURUSD signals only
nats sub "signals.EURUSD"

# Subscribe to specific timeframe
nats sub "signals.EURUSD.5m"
```

## Guidelines

- **ALWAYS** use ConfigClient for operational settings (model version, thresholds)
- **NEVER** use historical features (inference needs live data only!)
- **ALWAYS** publish to both NATS + Kafka (audit trail mandatory)
- **VERIFY** model loaded correctly (check checkpoint metadata)
- **ENSURE** latency < 100ms (trading window is critical)
- **VALIDATE** signal format before publishing

## Critical Rules

1. **Config Hierarchy:**
   - Model version, thresholds → Central Hub (operational config)
   - Safe defaults → ConfigClient fallback
   - No secrets needed

2. **Live Data Only:**
   - **NEVER** use historical features (no targets in live mode)
   - **ONLY** use live features from feature-engineering NATS stream
   - **FALLBACK** to latest ClickHouse candle if NATS unavailable

3. **Latency Requirement:**
   - **ENSURE** prediction < 100ms
   - **OPTIMIZE** model loading (in-memory cache)
   - **PROFILE** bottlenecks (feature processing, model predict)
   - **REJECT** slow predictions (timeout)

4. **Signal Validation:**
   - **CHECK** confidence score > threshold
   - **VERIFY** entry/SL/TP levels reasonable
   - **VALIDATE** signal type valid (buy/sell/hold/close)
   - **REJECT** invalid signals

5. **Dual Publishing (Mandatory):**
   - **ALWAYS** publish to NATS (real-time to risk-mgmt)
   - **ALWAYS** archive to Kafka (audit trail, compliance)
   - **VERIFY** both paths working

## Common Tasks

### Deploy New Model Version
1. Train model using supervised-training
2. Save checkpoint to ClickHouse
3. Update config via Central Hub (set new model_version)
4. Hot-reload will automatically load new model
5. Monitor performance (latency, signal quality)

### Monitor Model Performance
1. Track prediction latency (should be < 100ms)
2. Monitor signal distribution (buy/sell/hold ratio)
3. Check confidence scores (average > threshold)
4. Review model predictions vs actual outcomes
5. Detect model drift (performance degradation)

### Debug High Latency
1. Profile feature processing time
2. Check model prediction time
3. Review network latency (NATS, ClickHouse)
4. Optimize model (reduce complexity)
5. Consider model quantization or pruning

### Implement Model Hot-Swapping
1. Configure `auto_reload: true` in config
2. Update model_version via Central Hub API
3. Inference service detects config change
4. Loads new model checkpoint
5. Swaps models without downtime

## Troubleshooting

### Issue 1: High Prediction Latency (> 100ms)
**Symptoms:** Signals delayed, trading opportunities missed
**Solution:**
- Profile each step (feature processing, model predict)
- Optimize model (reduce tree depth, fewer estimators)
- Cache model in memory (avoid reload)
- Use faster model type (LightGBM instead of XGBoost)
- Consider GPU acceleration

### Issue 2: Model Not Loading from Checkpoint
**Symptoms:** Inference fails to start
**Solution:**
- Verify checkpoint exists in ClickHouse
- Check model serialization format (pickle, joblib)
- Review model version in config
- Test checkpoint load manually
- Check ClickHouse connectivity

### Issue 3: No Signals Being Generated
**Symptoms:** NATS/Kafka streams empty
**Solution:**
- Check confidence threshold (may be too high)
- Verify features arriving via NATS
- Review model predictions (all "hold"?)
- Check signal generation logic
- Test with lower threshold

### Issue 4: Signal Format Invalid
**Symptoms:** Risk-management rejects signals
**Solution:**
- Verify signal schema matches expected format
- Check all required fields present
- Validate entry/SL/TP calculations
- Review confidence score range (0-1)
- Test signal validation logic

### Issue 5: Model Performance Drift
**Symptoms:** Signal quality degrading over time
**Solution:**
- Compare recent metrics vs training metrics
- Check for market regime changes
- Retrain model with recent data
- Implement online learning
- Add drift detection alerts

## Validation Checklist

After making changes to this service:
- [ ] NATS subscribes to `features.>` (real-time features)
- [ ] Model/agent loaded successfully (check logs)
- [ ] Signals published to NATS `signals.*` (risk-mgmt receives)
- [ ] Kafka archives to `trading_signals_archive`
- [ ] Latency < 100ms (measure time from feature → signal)
- [ ] Confidence threshold enforced
- [ ] Entry/SL/TP calculated correctly
- [ ] Signal validation passing
- [ ] ConfigClient fetching from Central Hub
- [ ] Hot-reload responding to config updates

## Related Skills

- `central-hub` - Provides operational config and service discovery
- `feature-engineering` - Provides live features via NATS
- `supervised-training` - Trains models for inference
- `finrl-training` - Trains RL agents for inference
- `risk-management` - Consumes signals for position sizing

## References

- Full Documentation: `docs/SERVICE_ARCHITECTURE_AND_FLOW.md` (lines 544-576)
- Planning Guide: `docs/PLANNING_SKILL_GUIDE.md` (Service 10, lines 1452-1650)
- Flow + Messaging: `docs/SERVICE_FLOW_TREE_WITH_MESSAGING.md` (lines 472-525)
- Database Schema: `docs/table_database_trading.md` (trading_signals table)
- Config Architecture: `docs/CONFIG_ARCHITECTURE.md`
- Central Hub Skill: `.claude/skills/central-hub/SKILL.md`
- Code: `03-machine-learning/inference-service/`

---

**Created:** 2025-10-19
**Version:** 1.0.0
**Status:** To Implement
