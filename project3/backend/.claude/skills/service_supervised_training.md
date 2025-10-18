# Skill: supervised-training-service Service

## Purpose
Train supervised ML models (XGBoost, LightGBM, CatBoost) on historical ml_features with targets for price prediction.

## Key Facts
- **Phase**: ML Training (Phase 2)
- **Status**: ⚠️ To Implement
- **Priority**: P1 (Important - core ML capability)
- **Models**: XGBoost, LightGBM, CatBoost, Random Forest
- **Training data**: ClickHouse.ml_features (historical + targets)

## Data Flow
```
ClickHouse.ml_features (historical + targets)
  → supervised-training-service (train ML models)
  → ClickHouse.training_runs
  → ClickHouse.model_checkpoints
  → ClickHouse.training_metrics
  → NATS: training.completed.{run_id} (status)
```

## Messaging
- **NATS Publish**: `training.started.{run_id}`, `training.completed.{run_id}`, `training.failed.{run_id}`
- **Pattern**: Status events only (batch training, no streaming)

## Dependencies
- **Upstream**: feature-engineering-service (provides ml_features with targets)
- **Downstream**: inference-service (loads trained models)
- **Infrastructure**: ClickHouse, NATS cluster, GPU (optional)

## Critical Rules
1. **NEVER** train on live data (live mode has NO targets!)
2. **ALWAYS** use time-series split (prevent look-ahead bias)
3. **VERIFY** targets exist in training data (check target columns)
4. **ENSURE** model versioning (save checkpoints with metadata)
5. **VALIDATE** model performance before deployment (min accuracy threshold)

## Training Strategy
- **Split**: Time-series split (not random) - train/val/test by date
- **Targets**: future_return_5m, future_return_15m, future_return_1h, future_return_4h, future_return_1d
- **Validation**: Walk-forward validation (mimics production)
- **Hyperparameters**: Optuna for tuning (automated search)

## Models to Train
1. **XGBoost**: Gradient boosting (fast, accurate)
2. **LightGBM**: Fast gradient boosting (large datasets)
3. **CatBoost**: Handles categorical features well
4. **Random Forest**: Ensemble baseline

## Validation
When working on this service, ALWAYS verify:
- [ ] ml_features has targets (historical mode only)
- [ ] Time-series split used (no look-ahead bias)
- [ ] Model checkpoints saved to ClickHouse
- [ ] Training metrics logged (accuracy, precision, recall)
- [ ] NATS publishes training status events

## Reference Docs
- Planning guide: `PLANNING_SKILL_GUIDE.md` (Service 8, lines 1052-1250)
- Architecture: `SERVICE_ARCHITECTURE_AND_FLOW.md` (lines 459-495)
- Flow + messaging: `SERVICE_FLOW_TREE_WITH_MESSAGING.md` (lines 379-419)
- Database schema: `table_database_training.md` (to be designed)
