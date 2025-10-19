---
name: supervised-training
description: Trains supervised ML models (XGBoost, LightGBM, CatBoost) on historical ml_features with targets for price prediction using time-series split and walk-forward validation
license: MIT
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
metadata:
  type: Machine Learning (Training)
  phase: ML Training (Phase 2)
  status: To Implement
  priority: P1 (Important - core ML capability)
  port: 8008
  dependencies:
    - central-hub
    - clickhouse
    - nats
  version: 1.0.0
---

# Supervised Training Service

Trains supervised ML models (XGBoost, LightGBM, CatBoost, Random Forest) on historical ml_features with targets for price prediction. Uses time-series split to prevent look-ahead bias and walk-forward validation to mimic production.

## When to Use This Skill

Use this skill when:
- Training new ML models for price prediction
- Tuning hyperparameters with Optuna
- Evaluating model performance metrics
- Implementing time-series cross-validation
- Managing model versioning and checkpoints
- Debugging training data quality issues

## Service Overview

**Type:** Machine Learning (Training)
**Port:** 8008
**Input:** ClickHouse (`ml_features` table - historical mode with targets)
**Output:** ClickHouse (`training_runs`, `model_checkpoints`, `training_metrics`)
**Messaging:** NATS (training status events)
**Models:** XGBoost, LightGBM, CatBoost, Random Forest
**Validation:** Time-series split + walk-forward validation

**Dependencies:**
- **Upstream**: feature-engineering (provides ml_features with targets)
- **Downstream**: inference (loads trained models)
- **Infrastructure**: ClickHouse, NATS cluster, GPU (optional for deep learning)

## Key Capabilities

- Supervised ML model training (gradient boosting, ensembles)
- Time-series split (prevent look-ahead bias)
- Walk-forward validation (mimic production)
- Hyperparameter tuning with Optuna
- Model versioning and checkpoints
- Performance metrics logging
- Training status broadcasting (NATS)

## Architecture

### Data Flow

```
ClickHouse.ml_features (historical + targets)
  ↓ (Load training data)
supervised-training-service
  ├─→ Time-series split (train/val/test by date)
  ├─→ Train models (XGBoost, LightGBM, CatBoost, RF)
  ├─→ Hyperparameter tuning (Optuna)
  ├─→ Evaluate performance (accuracy, precision, recall, F1)
  ├─→ Save checkpoints
  ↓
├─→ ClickHouse.training_runs (metadata)
├─→ ClickHouse.model_checkpoints (serialized models)
├─→ ClickHouse.training_metrics (performance)
└─→ NATS: training.{status}.{run_id} (events)
```

### Training Strategy

**1. Data Split (Time-series):**
- **Train**: 70% oldest data
- **Validation**: 15% middle data
- **Test**: 15% newest data
- **CRITICAL**: Split by date, NOT random (prevent look-ahead bias)

**2. Targets:**
- `future_return_5m` - 5-minute ahead return
- `future_return_15m` - 15-minute ahead return
- `future_return_1h` - 1-hour ahead return
- `future_return_4h` - 4-hour ahead return
- `future_return_1d` - 1-day ahead return
- `future_return_direction` - Binary classification (up/down)

**3. Models:**
- **XGBoost**: Fast gradient boosting, good for tabular data
- **LightGBM**: Faster gradient boosting, handles large datasets
- **CatBoost**: Handles categorical features well, less tuning needed
- **Random Forest**: Ensemble baseline, robust to overfitting

**4. Hyperparameter Tuning:**
- Use Optuna for automated search
- Objective: Maximize F1 score (or custom metric)
- Search space: learning rate, max depth, n_estimators, etc.
- Trials: 100-500 (configurable)

**5. Walk-Forward Validation:**
- Train on window, predict next period
- Roll window forward, retrain
- Evaluate on multiple time periods
- Mimics production behavior

### Configuration

**Operational Config (Central Hub):**
```json
{
  "operational": {
    "models": ["xgboost", "lightgbm", "catboost", "random_forest"],
    "targets": ["future_return_direction", "future_return_1h"],
    "split_ratio": [0.7, 0.15, 0.15],
    "hyperparameter_tuning": {
      "enabled": true,
      "trials": 100,
      "metric": "f1_score"
    },
    "walk_forward_validation": {
      "enabled": true,
      "window_days": 90,
      "step_days": 30
    },
    "model_versioning": {
      "auto_increment": true,
      "save_checkpoints": true
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
    service_name="supervised-training",
    safe_defaults={
        "operational": {
            "models": ["xgboost", "lightgbm"],
            "targets": ["future_return_direction"],
            "split_ratio": [0.7, 0.15, 0.15]
        }
    }
)
await client.init_async()

# Get config
config = await client.get_config()
models = config['operational']['models']
targets = config['operational']['targets']
print(f"Training {models} for targets: {targets}")
```

### Example 2: Train XGBoost Model

```python
from supervised_trainer import SupervisedTrainer

trainer = SupervisedTrainer()

# Load training data (historical features with targets)
train_data, val_data, test_data = await trainer.load_data_timeseries_split(
    symbol="EURUSD",
    timeframe="5m",
    target="future_return_direction",
    split_ratio=[0.7, 0.15, 0.15]
)

# Train XGBoost
model, metrics = await trainer.train_xgboost(
    train_data=train_data,
    val_data=val_data,
    hyperparams={
        "max_depth": 6,
        "learning_rate": 0.1,
        "n_estimators": 100
    }
)

# Evaluate on test set
test_metrics = await trainer.evaluate(model, test_data)
print(f"Test Accuracy: {test_metrics['accuracy']:.4f}")
print(f"Test F1 Score: {test_metrics['f1_score']:.4f}")

# Save checkpoint
await trainer.save_checkpoint(model, metrics, version="1.0.0")
```

### Example 3: Hyperparameter Tuning with Optuna

```python
from supervised_trainer import HyperparameterTuner

tuner = HyperparameterTuner()

# Define search space
search_space = {
    "max_depth": (3, 10),
    "learning_rate": (0.001, 0.3),
    "n_estimators": (50, 500),
    "min_child_weight": (1, 10)
}

# Run Optuna search
best_params, best_score = await tuner.optimize(
    model_type="xgboost",
    train_data=train_data,
    val_data=val_data,
    search_space=search_space,
    n_trials=100,
    metric="f1_score"
)

print(f"Best hyperparameters: {best_params}")
print(f"Best F1 score: {best_score:.4f}")
```

### Example 4: Walk-Forward Validation

```python
from supervised_trainer import WalkForwardValidator

validator = WalkForwardValidator()

# Validate with walk-forward
results = await validator.validate(
    model_type="xgboost",
    symbol="EURUSD",
    timeframe="5m",
    target="future_return_direction",
    window_days=90,
    step_days=30
)

# Results: List of metrics per fold
# [
#   {"fold": 1, "accuracy": 0.62, "f1_score": 0.60, "precision": 0.58, ...},
#   {"fold": 2, "accuracy": 0.64, "f1_score": 0.61, "precision": 0.60, ...},
#   ...
# ]

print(f"Average Accuracy: {np.mean([r['accuracy'] for r in results]):.4f}")
```

### Example 5: Query Training Metrics from ClickHouse

```sql
-- Check recent training runs
SELECT
    run_id,
    model_type,
    symbol,
    timeframe,
    target,
    accuracy,
    f1_score,
    precision,
    recall,
    training_duration_minutes,
    created_at
FROM training_runs
ORDER BY created_at DESC
LIMIT 10;

-- Get best model by F1 score
SELECT
    run_id,
    model_type,
    f1_score,
    accuracy,
    version
FROM training_runs
WHERE symbol = 'EURUSD'
  AND timeframe = '5m'
  AND target = 'future_return_direction'
ORDER BY f1_score DESC
LIMIT 1;
```

## Guidelines

- **ALWAYS** use ConfigClient for operational settings (models, targets, split ratios)
- **NEVER** train on live data (live mode has NO targets!)
- **ALWAYS** use time-series split (prevent look-ahead bias)
- **VERIFY** targets exist in training data (check target columns)
- **ENSURE** model versioning (save checkpoints with metadata)
- **VALIDATE** model performance before deployment (min threshold)

## Critical Rules

1. **Config Hierarchy:**
   - Models, targets, split ratios → Central Hub (operational config)
   - Safe defaults → ConfigClient fallback
   - No secrets needed

2. **NO Training on Live Data:**
   - **NEVER** use live features (no targets available)
   - **ONLY** use historical features from feature-engineering
   - **VERIFY** targets exist before training

3. **Time-Series Split (CRITICAL):**
   - **ALWAYS** split by date (not random)
   - **PREVENT** look-ahead bias (no future data in training)
   - **ORDER**: train (oldest) → val (middle) → test (newest)

4. **Model Versioning:**
   - **SAVE** checkpoints with metadata (version, metrics, hyperparams)
   - **INCREMENT** version on each training run
   - **TRACK** best model by metric (F1, accuracy)

5. **Minimum Performance Threshold:**
   - **VALIDATE** accuracy > 55% (above random for binary)
   - **CHECK** F1 score > 0.50
   - **REJECT** models below threshold

## Common Tasks

### Train New Model
1. Verify historical features available with targets
2. Configure model type and target in Central Hub
3. Run training with hyperparameter tuning
4. Evaluate on test set
5. Save checkpoint if performance acceptable

### Tune Hyperparameters
1. Define search space for model type
2. Configure Optuna trials (100-500)
3. Run optimization
4. Review best params and score
5. Retrain with best params on full dataset

### Implement Walk-Forward Validation
1. Configure window and step size
2. Run validation across multiple periods
3. Analyze performance consistency
4. Identify overfitting or underfitting
5. Adjust model based on results

### Debug Poor Model Performance
1. Check training data quality (NULL features, target distribution)
2. Verify time-series split correct (no leakage)
3. Review feature importance (are features predictive?)
4. Test simpler model first (Random Forest baseline)
5. Check for class imbalance (adjust loss function)

## Troubleshooting

### Issue 1: Training Fails Due to Missing Targets
**Symptoms:** Error: target column not found
**Solution:**
- Verify feature-engineering in historical mode
- Check ml_features table has target columns
- Review feature generation logs
- Test with known historical data

### Issue 2: Model Overfits Badly
**Symptoms:** Train accuracy high, test accuracy low
**Solution:**
- Reduce model complexity (max_depth, n_estimators)
- Increase regularization (min_child_weight, lambda)
- Use walk-forward validation
- Add more training data
- Check for data leakage

### Issue 3: Hyperparameter Tuning Takes Forever
**Symptoms:** Optuna trials too slow
**Solution:**
- Reduce n_trials (100 → 50)
- Narrow search space
- Use faster model (LightGBM instead of XGBoost)
- Parallelize trials (multiple GPUs)
- Use early stopping

### Issue 4: Model Performance Below Random
**Symptoms:** Accuracy < 50% for binary classification
**Solution:**
- Check target distribution (class imbalance?)
- Verify features are predictive (feature importance)
- Review data preprocessing (normalization, scaling)
- Test with simpler baseline model
- Check for bugs in training code

### Issue 5: Checkpoint Saving Failing
**Symptoms:** Model trained but not saved
**Solution:**
- Check ClickHouse connectivity
- Verify checkpoint serialization (pickle/joblib)
- Review storage space availability
- Test checkpoint save/load manually
- Check permissions

## Validation Checklist

After making changes to this service:
- [ ] ml_features has targets (historical mode only)
- [ ] Time-series split used (no look-ahead bias)
- [ ] Model checkpoints saved to ClickHouse
- [ ] Training metrics logged (accuracy, precision, recall, F1)
- [ ] NATS publishes training status events
- [ ] Model performance above threshold (accuracy > 55%, F1 > 0.50)
- [ ] Hyperparameter tuning working (if enabled)
- [ ] Walk-forward validation results reasonable
- [ ] ConfigClient fetching from Central Hub
- [ ] Hot-reload responding to config updates

## Related Skills

- `central-hub` - Provides operational config and service discovery
- `feature-engineering` - Provides historical ml_features with targets
- `inference` - Loads trained models for real-time prediction
- `finrl-training` - Alternative RL-based training approach

## References

- Full Documentation: `docs/SERVICE_ARCHITECTURE_AND_FLOW.md` (lines 459-495)
- Planning Guide: `docs/PLANNING_SKILL_GUIDE.md` (Service 8, lines 1052-1250)
- Flow + Messaging: `docs/SERVICE_FLOW_TREE_WITH_MESSAGING.md` (lines 379-419)
- Database Schema: `docs/table_database_training.md` (to be designed)
- Config Architecture: `docs/CONFIG_ARCHITECTURE.md`
- Central Hub Skill: `.claude/skills/central-hub/SKILL.md`
- Code: `03-machine-learning/supervised-training-service/`

---

**Created:** 2025-10-19
**Version:** 1.0.0
**Status:** To Implement
