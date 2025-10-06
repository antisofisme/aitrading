# ML/DL Model Deployment & Versioning Workflow

## Overview

This document defines the complete workflow for training, versioning, deploying, and managing ML/DL models in the SUHO AI Trading Platform.

---

## 1. Model Lifecycle Stages

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MODEL LIFECYCLE                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  DRAFT → TRAINING → TESTING → STAGING → CANARY → PRODUCTION → ARCHIVED │
│                                                                      │
│    │       │          │         │          │          │          │  │
│    ▼       ▼          ▼         ▼          ▼          ▼          ▼  │
│  Config  Train &   Evaluate  A/B Test  Limited  Full Prod  Replaced│
│  Created Metrics   on Test   Metrics   Traffic   Traffic   by New  │
│                      Set                (10%)    (100%)    Version │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Development Workflow

### 2.1 Model Development (LOCAL)

```bash
# Step 1: Setup development environment
cd /backend/03-ml-pipeline
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Step 2: Extract training data from ClickHouse
python scripts/export_training_data.py \
    --tenant tenant_001 \
    --symbol EUR/USD \
    --timeframe 1h \
    --start-date 2023-01-01 \
    --end-date 2025-01-01 \
    --output data/eurusd_1h_training.parquet

# Step 3: Develop and train model
jupyter notebook notebooks/model_development.ipynb

# Step 4: Evaluate model
python scripts/evaluate_model.py \
    --model-path models/eurusd_lstm_1h_v1.h5 \
    --test-data data/eurusd_1h_test.parquet

# Step 5: Register model in registry
python scripts/register_model.py \
    --model-path models/eurusd_lstm_1h_v1.h5 \
    --config configs/eurusd_lstm_1h.json \
    --metrics metrics/eurusd_lstm_1h_v1.json \
    --status draft
```

### 2.2 Model Training Service (PRODUCTION)

```python
# Training job configuration
{
    "job_name": "eurusd_lstm_1h_v2_training",
    "tenant_id": "tenant_001",
    "model_config": {
        "model_name": "eurusd_lstm_1h",
        "model_type": "lstm",
        "target_symbol": "EUR/USD",
        "target_timeframe": "1h",
        "prediction_horizon": "4h",
        "version": "v2.0.0"
    },
    "training_config": {
        "start_date": "2023-01-01",
        "end_date": "2025-01-01",
        "features": [
            "close", "rsi_14", "macd_histogram", "bb_percent_b",
            "atr_14", "volume_ratio", "adx_14", "stoch_k",
            # ... 50+ features
        ],
        "hyperparameters": {
            "sequence_length": 60,
            "lstm_units": [128, 64],
            "dropout": 0.2,
            "learning_rate": 0.001,
            "batch_size": 32,
            "epochs": 100,
            "early_stopping_patience": 10
        }
    },
    "compute": {
        "gpu": true,
        "instance_type": "g4dn.xlarge",  # AWS GPU instance
        "timeout_hours": 12
    }
}

# Submit training job
curl -X POST http://ml-training-service:8080/api/v1/training/submit \
    -H "Content-Type: application/json" \
    -d @configs/eurusd_lstm_1h_v2_training.json
```

**Training Service Actions:**
1. Creates `training_jobs` record with status='queued'
2. Provisions GPU instance (if using cloud)
3. Queries training data from ClickHouse
4. Trains model with progress tracking
5. Evaluates on validation/test sets
6. Saves model to S3/MinIO
7. Registers in `ml_registry.models` with status='draft'
8. Updates `training_jobs` with final metrics

---

## 3. Model Versioning Strategy

### 3.1 Version Numbering

**Semantic Versioning: `vMAJOR.MINOR.PATCH`**

- **MAJOR**: Breaking changes
  - Architecture change (LSTM → Transformer)
  - Feature set change (different features)
  - Target change (1h → 4h prediction)

- **MINOR**: Non-breaking improvements
  - Additional features (add volume indicators)
  - Hyperparameter tuning (better performance)
  - Training data expansion

- **PATCH**: Bug fixes & retraining
  - Fix in data preprocessing
  - Retraining on new data (same config)
  - Performance optimization

**Examples:**
```
v1.0.0  → Initial LSTM model with 50 features
v1.1.0  → Added 10 volume features (MINOR: new features)
v1.1.1  → Retrained with updated data (PATCH: same config)
v2.0.0  → Switched to Transformer (MAJOR: architecture change)
```

### 3.2 Model Metadata

**Stored in `ml_registry.models` table:**

```json
{
    "model_id": "uuid-1234-5678",
    "model_name": "eurusd_lstm_1h",
    "version": "v2.1.0",
    "status": "production",
    "architecture": {
        "type": "lstm",
        "layers": [
            {"type": "lstm", "units": 128, "dropout": 0.2},
            {"type": "lstm", "units": 64, "dropout": 0.2},
            {"type": "dense", "units": 32, "activation": "relu"},
            {"type": "output", "units": 3, "activation": "softmax"}
        ],
        "optimizer": "adam",
        "loss": "categorical_crossentropy"
    },
    "hyperparameters": {
        "sequence_length": 60,
        "learning_rate": 0.001,
        "batch_size": 32,
        "epochs": 100
    },
    "features_used": [
        "close", "rsi_14", "macd_histogram", "bb_percent_b",
        "atr_14", "volume_ratio", "adx_14"
    ],
    "feature_version": "1.0.0",
    "training_data": {
        "start": "2023-01-01T00:00:00Z",
        "end": "2025-01-01T00:00:00Z",
        "train_samples": 15000,
        "val_samples": 3000,
        "test_samples": 3000
    },
    "metrics": {
        "accuracy": 0.67,
        "precision": 0.65,
        "recall": 0.70,
        "f1_score": 0.675,
        "auc_roc": 0.72,
        "sharpe_ratio": 1.8,
        "win_rate": 0.58,
        "train_loss": 0.45,
        "val_loss": 0.52,
        "test_loss": 0.54
    },
    "model_storage_path": "s3://suho-models/tenant_001/eurusd_lstm_1h/v2.1.0/model.h5",
    "parent_model_id": "uuid-previous-version",
    "created_at": "2025-10-01T12:00:00Z",
    "trained_at": "2025-10-01T18:30:00Z",
    "deployed_at": "2025-10-02T10:00:00Z"
}
```

---

## 4. Deployment Pipeline

### 4.1 Testing Phase

```bash
# After training completes with status='draft'

# Step 1: Automated evaluation on test set
python scripts/evaluate_model.py \
    --model-id uuid-1234-5678 \
    --test-data-query "SELECT * FROM ml_features WHERE ..."

# Step 2: Backtesting on historical data
python scripts/backtest_model.py \
    --model-id uuid-1234-5678 \
    --start-date 2024-01-01 \
    --end-date 2025-01-01

# Step 3: Update status to 'testing'
UPDATE ml_registry.models
SET status = 'testing'
WHERE model_id = 'uuid-1234-5678';

# Step 4: Create evaluation record
INSERT INTO ml_registry.model_evaluations
(model_id, dataset_type, metrics, ...)
VALUES (...);
```

**Acceptance Criteria:**
- Test accuracy ≥ baseline accuracy - 5%
- Sharpe ratio > 1.0
- Max drawdown < 20%
- No data leakage detected
- Inference latency < 200ms (P95)

### 4.2 Staging Deployment

```bash
# Deploy to staging environment

# Step 1: Update status
UPDATE ml_registry.models
SET status = 'staging'
WHERE model_id = 'uuid-1234-5678';

# Step 2: Deploy to staging inference service
kubectl apply -f deployments/staging/inference-service-v2.1.0.yaml

# Step 3: Run integration tests
python tests/integration/test_inference_api.py \
    --environment staging \
    --model-id uuid-1234-5678

# Step 4: Monitor for 24 hours
# - Check error rates
# - Validate prediction latency
# - Compare with production predictions (shadow mode)
```

### 4.3 Canary Deployment (A/B Testing)

```python
# Canary deployment configuration
{
    "deployment_id": "deploy-uuid-9999",
    "model_id": "uuid-1234-5678",  # New model
    "baseline_model_id": "uuid-old-version",  # Current production
    "environment": "production",
    "deployment_type": "canary",
    "traffic_allocation": {
        "new_model": 0.10,  # 10% traffic
        "baseline": 0.90    # 90% traffic
    },
    "duration_hours": 48,
    "success_criteria": {
        "min_accuracy": 0.60,
        "max_latency_p95_ms": 250,
        "min_uptime": 0.999
    }
}

# Execute canary deployment
POST /api/v1/deployments/canary
{
    "model_id": "uuid-1234-5678",
    "traffic_percentage": 10,
    "duration_hours": 48
}
```

**Canary Workflow:**
1. Deploy new model to production inference service
2. Route 10% of prediction requests to new model
3. Monitor metrics in real-time:
   ```sql
   -- Compare performance
   SELECT
       model_id,
       COUNT(*) as predictions,
       AVG(confidence_score) as avg_confidence,
       AVG(CASE WHEN direction_correct THEN 1.0 ELSE 0.0 END) as accuracy,
       AVG(inference_latency_ms) as avg_latency
   FROM ml_predictions
   WHERE time >= NOW() - INTERVAL '1 hour'
   GROUP BY model_id;
   ```
4. Statistical significance testing
5. Decision: Promote or Rollback

### 4.4 Full Production Rollout

```bash
# If canary succeeds, promote to full production

# Step 1: Increase traffic gradually
# 10% → 25% → 50% → 100% over 24 hours

curl -X PATCH http://deployment-service/api/v1/deployments/deploy-uuid-9999 \
    -d '{"traffic_percentage": 25}'

# Wait 6 hours, monitor...

curl -X PATCH http://deployment-service/api/v1/deployments/deploy-uuid-9999 \
    -d '{"traffic_percentage": 50}'

# Wait 6 hours, monitor...

curl -X PATCH http://deployment-service/api/v1/deployments/deploy-uuid-9999 \
    -d '{"traffic_percentage": 100}'

# Step 2: Update model status
UPDATE ml_registry.models
SET status = 'production', deployed_at = NOW()
WHERE model_id = 'uuid-1234-5678';

# Step 3: Archive old model
UPDATE ml_registry.models
SET status = 'archived'
WHERE model_id = 'uuid-old-version';

# Step 4: Create deployment record
INSERT INTO ml_registry.model_deployments
(model_id, environment, status, traffic_percentage, deployed_at)
VALUES ('uuid-1234-5678', 'production', 'active', 100, NOW());
```

### 4.5 Rollback Procedure

```bash
# If canary or production deployment fails

# Step 1: Immediate rollback to baseline
curl -X POST http://deployment-service/api/v1/deployments/rollback \
    -d '{
        "deployment_id": "deploy-uuid-9999",
        "reason": "High error rate detected"
    }'

# Step 2: Update model status
UPDATE ml_registry.models
SET status = 'draft'
WHERE model_id = 'uuid-1234-5678';

# Step 3: Restore baseline to 100%
UPDATE ml_registry.model_deployments
SET traffic_percentage = 100
WHERE model_id = 'uuid-old-version';

# Step 4: Alert team
# - Send Slack/email notification
# - Create incident ticket
# - Log rollback event
```

---

## 5. Continuous Deployment (CI/CD)

### 5.1 GitHub Actions Workflow

```yaml
# .github/workflows/ml-deploy.yml

name: ML Model Deployment

on:
  push:
    paths:
      - 'ml-models/**'
      - 'configs/**'

jobs:
  train:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Extract training data
        run: python scripts/export_training_data.py

      - name: Train model
        run: python scripts/train_model.py --config configs/eurusd_lstm_1h.json

      - name: Evaluate model
        run: python scripts/evaluate_model.py

      - name: Register model
        run: python scripts/register_model.py --status draft

  test:
    needs: train
    runs-on: ubuntu-latest
    steps:
      - name: Backtesting
        run: python scripts/backtest_model.py

      - name: Integration tests
        run: pytest tests/integration/

  deploy-staging:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to staging
        run: kubectl apply -f deployments/staging/

      - name: Smoke tests
        run: python tests/smoke/test_inference.py

  deploy-canary:
    needs: deploy-staging
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Canary deployment
        run: |
          curl -X POST $DEPLOYMENT_API/canary \
            -d '{"model_id": "$MODEL_ID", "traffic_percentage": 10}'

      - name: Monitor canary (48h)
        run: python scripts/monitor_canary.py --duration 48

      - name: Promote to production
        run: python scripts/promote_to_production.py
```

---

## 6. Model Monitoring

### 6.1 Performance Metrics

**Real-time Dashboard (Grafana):**
- Prediction count (last 1h, 24h)
- Model accuracy (rolling window)
- Inference latency (P50, P95, P99)
- Error rate
- Cache hit rate

**Alert Rules:**
```yaml
alerts:
  - name: model_accuracy_drop
    condition: accuracy < baseline_accuracy * 0.9
    severity: critical
    action: trigger_retraining

  - name: high_latency
    condition: p95_latency_ms > 500
    severity: warning
    action: scale_inference_service

  - name: high_error_rate
    condition: error_rate > 0.05
    severity: critical
    action: rollback_deployment
```

### 6.2 Data Drift Detection

```python
# Scheduled job (daily)

from scipy.stats import ks_2samp

def detect_drift(model_id, feature_name):
    # Get feature distribution from training data
    training_dist = query_feature_stats(
        model_id, feature_name, source='training'
    )

    # Get feature distribution from recent predictions
    production_dist = query_feature_stats(
        model_id, feature_name, source='production', days=7
    )

    # Kolmogorov-Smirnov test
    statistic, p_value = ks_2samp(training_dist, production_dist)

    if p_value < 0.05:  # Significant drift
        create_alert(
            model_id=model_id,
            alert_type='data_drift',
            message=f'Data drift detected in {feature_name}',
            severity='warning'
        )
        trigger_retraining(model_id)
```

---

## 7. Model Retraining

### 7.1 Automated Retraining Triggers

```python
# Retraining conditions
retraining_triggers = {
    "performance_degradation": {
        "condition": "accuracy < baseline * 0.90",
        "action": "immediate_retrain"
    },
    "data_drift": {
        "condition": "p_value < 0.05 (KS test)",
        "action": "scheduled_retrain"
    },
    "scheduled": {
        "condition": "monthly (1st of month)",
        "action": "retrain_with_new_data"
    },
    "manual": {
        "condition": "user_initiated",
        "action": "custom_retrain"
    }
}
```

### 7.2 Retraining Workflow

```python
async def automated_retraining(model_id, trigger_reason):
    """
    Automated model retraining pipeline
    """
    # 1. Get model configuration
    model_config = get_model_config(model_id)

    # 2. Query new training data (last 2 years)
    training_data = query_training_data(
        tenant_id=model_config.tenant_id,
        symbol=model_config.target_symbol,
        start_date=datetime.now() - timedelta(days=730),
        end_date=datetime.now()
    )

    # 3. Increment version (PATCH)
    new_version = increment_patch_version(model_config.version)

    # 4. Submit training job
    job_id = submit_training_job(
        config=model_config,
        version=new_version,
        data=training_data,
        reason=trigger_reason
    )

    # 5. Wait for completion
    await wait_for_training(job_id, timeout_hours=12)

    # 6. Evaluate new model
    metrics = evaluate_model(new_model_id)

    # 7. Compare with baseline
    if metrics['accuracy'] > baseline_accuracy:
        # Deploy canary
        deploy_canary(new_model_id, traffic=10)
    else:
        # Archive failed model
        archive_model(new_model_id, reason='poor_performance')
```

---

## 8. Multi-Tenant Model Management

### 8.1 Model Sharing Strategy

**Platform Models (Shared):**
- Trained on aggregated data from multiple tenants
- Available to all users (user_id = NULL)
- Lower accuracy but good baseline
- Free tier users limited to platform models

**Tenant Models:**
- Trained on single tenant's data
- Available to all users in tenant
- Better performance (tenant-specific patterns)

**User Models:**
- Trained on individual user's trades
- Private to user
- Fine-tuned for user's strategy
- Premium tier feature

### 8.2 Model Access Control

```sql
-- Get available models for user
SELECT m.*
FROM ml_registry.models m
WHERE m.status = 'production'
  AND (
      -- Platform models (shared)
      (m.tenant_id IS NULL AND m.user_id IS NULL)
      OR
      -- Tenant models
      (m.tenant_id = 'tenant_001' AND m.user_id IS NULL)
      OR
      -- User models
      (m.tenant_id = 'tenant_001' AND m.user_id = 'user_123')
  )
ORDER BY m.created_at DESC;
```

---

## 9. Storage & Artifacts

### 9.1 Model Storage Structure

```
s3://suho-models/
├── platform/                          # Shared models
│   ├── eurusd_baseline_1h/
│   │   ├── v1.0.0/
│   │   │   ├── model.h5              # Keras model
│   │   │   ├── model.onnx            # Optimized ONNX
│   │   │   ├── scaler.pkl            # Feature scaler
│   │   │   ├── config.json           # Model config
│   │   │   ├── metadata.json         # Training metadata
│   │   │   └── tensorboard/          # Training logs
│   │   └── v1.1.0/
│   └── xauusd_baseline_4h/
├── tenant_001/                        # Tenant-specific
│   ├── eurusd_lstm_1h/
│   │   ├── v1.0.0/
│   │   └── v2.0.0/
│   └── user_123/                      # User-specific
│       └── eurusd_custom_1h/
└── tenant_002/
```

### 9.2 Artifact Versioning

**Model Binary:**
- Stored in S3/MinIO
- Immutable (never overwrite)
- Versioned by model version

**Feature Scaler:**
- Stored alongside model
- Critical for inference (must match training)

**Configuration Files:**
- `config.json`: Model architecture & hyperparameters
- `metadata.json`: Training details, metrics, lineage

---

## 10. Best Practices

### 10.1 Model Development

✅ **DO:**
- Use version control for configs and notebooks
- Track experiments (MLflow, Weights & Biases)
- Validate on out-of-sample data
- Document feature engineering logic
- Test inference latency before deployment

❌ **DON'T:**
- Train on all available data (risk overfitting)
- Skip validation set
- Ignore data quality issues
- Deploy without backtesting
- Hard-code feature names

### 10.2 Deployment

✅ **DO:**
- Always use canary deployments
- Monitor performance 24-48 hours
- Keep rollback capability ready
- Test inference endpoint before full rollout
- Version everything (code, data, models)

❌ **DON'T:**
- Deploy directly to 100% production
- Skip staging environment
- Ignore performance degradation alerts
- Delete old model versions immediately

### 10.3 Monitoring

✅ **DO:**
- Track model performance over time
- Set up automated alerts
- Monitor data distribution drift
- Log all predictions (sampling if needed)
- Regular model audits

❌ **DON'T:**
- Only monitor technical metrics (latency, errors)
- Ignore business metrics (accuracy, Sharpe ratio)
- Wait for users to report issues
- Disable alerts during high load

---

## 11. Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| **Model accuracy drops** | Data drift, market regime change | Trigger retraining, update features |
| **High inference latency** | Model too complex, not optimized | Convert to ONNX, enable batching |
| **Deployment fails** | Dependency mismatch | Pin dependencies, use containers |
| **Rollback needed** | Critical bug found | Immediate rollback, investigate offline |
| **Training timeout** | Too much data, inefficient code | Reduce data, optimize pipeline |

---

## 12. Summary Checklist

### Pre-Deployment
- [ ] Model trained and evaluated
- [ ] Backtesting completed
- [ ] Inference latency < 200ms
- [ ] Model registered in registry
- [ ] Artifacts uploaded to S3
- [ ] Integration tests passing

### Deployment
- [ ] Deployed to staging
- [ ] Canary deployment (10% traffic)
- [ ] Monitored for 48 hours
- [ ] Metrics meet acceptance criteria
- [ ] Gradual rollout to 100%
- [ ] Old model archived

### Post-Deployment
- [ ] Monitoring dashboards configured
- [ ] Alerts enabled
- [ ] Documentation updated
- [ ] Team notified
- [ ] Rollback procedure tested

---

**Document Version**: 1.0.0
**Last Updated**: 2025-10-05
**Status**: Production Ready
