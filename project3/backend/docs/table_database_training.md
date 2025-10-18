# 🧠 Database Training Tables - ML Model Training & FinRL

> **Version**: 1.0.0  
> **Last Updated**: 2025-10-18  
> **Status**: Complete - Ready for Implementation  
> **Related Services**: supervised-training-service, finrl-training-service

---

## 📋 Overview

**Purpose**: Dokumentasi untuk tabel-tabel yang digunakan dalam **ML Model Training & Reinforcement Learning (FinRL)**

**Input**: `ml_features` table (dari table_database_process.md)  
**Output**: Trained models, agents, dan metrics untuk inference

**Database**: ClickHouse (suho_analytics)

---

## 🎯 Training Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    TRAINING PIPELINE                            │
└─────────────────────────────────────────────────────────────────┘

ml_features (historical + targets)
    │
    ├─→ SUPERVISED LEARNING PATH
    │   │
    │   ├─→ supervised-training-service
    │   │   ├─ Data preparation (train/val/test split)
    │   │   ├─ Feature selection
    │   │   ├─ Model training (XGBoost, LightGBM, CatBoost)
    │   │   ├─ Hyperparameter tuning (Optuna)
    │   │   └─ Cross-validation
    │   │
    │   └─→ TABLES:
    │       ├─ training_runs (experiment tracking)
    │       ├─ model_checkpoints (saved models)
    │       ├─ training_metrics (accuracy, loss, etc)
    │       └─ hyperparameters_log (tuning history)
    │
    └─→ REINFORCEMENT LEARNING PATH (FinRL)
        │
        ├─→ finrl-training-service
        │   ├─ Environment creation (FinRL gym)
        │   ├─ State/action space definition
        │   ├─ Reward function design
        │   ├─ Agent training (PPO, A2C, DDPG, SAC, TD3)
        │   └─ Episode evaluation
        │
        └─→ TABLES:
            ├─ agent_training_runs (RL experiment tracking)
            ├─ agent_checkpoints (saved agents)
            ├─ reward_history (episode rewards)
            └─ rl_hyperparameters (RL config)
```

---

## 📊 Complete Table List

| # | Table Name | Purpose | Service | Priority |
|---|-----------|---------|---------|----------|
| 1 | training_runs | Supervised ML experiment tracking | supervised-training | P1 |
| 2 | model_checkpoints | Saved model binaries | supervised-training | P1 |
| 3 | training_metrics | Training metrics per epoch | supervised-training | P1 |
| 4 | hyperparameters_log | Hyperparameter tuning history | supervised-training | P1 |
| 5 | agent_training_runs | RL experiment tracking | finrl-training | P1 |
| 6 | agent_checkpoints | Saved RL agent binaries | finrl-training | P1 |
| 7 | reward_history | RL reward per episode | finrl-training | P1 |
| 8 | rl_hyperparameters | RL hyperparameter tuning | finrl-training | P1 |

---

## 📁 Database: ClickHouse (suho_analytics)

**Why ClickHouse for Training Tables?**
- Fast writes untuk experiment logging
- Efficient storage untuk large checkpoint blobs  
- Fast queries untuk model comparison & analysis
- Time-series optimization untuk training metrics
- Column-oriented untuk analytic queries

---

## 🔧 SUPERVISED LEARNING TABLES

### **Table 1: training_runs**

**Purpose**: Track setiap training experiment

**Key Columns**:
- run_id (UUID primary key)
- model_type (xgboost, lightgbm, catboost, etc)
- training dates, split ratios
- features_used, target_variable
- final metrics (accuracy, loss, F1, AUC)
- training status, duration

**ClickHouse Schema**: See SERVICE_ARCHITECTURE_AND_FLOW.md line 886-902

---

### **Table 2: model_checkpoints**

**Purpose**: Store trained model binaries

**Key Columns**:
- checkpoint_id, run_id
- model_binary (base64 encoded)
- model_format (pickle, joblib, onnx)
- performance metrics at checkpoint
- deployment status

---

### **Table 3: training_metrics**

**Purpose**: Time-series metrics per epoch/iteration

**Key Columns**:
- run_id, iteration_number
- train/val loss and accuracy
- learning_rate, gradient_norm
- iteration_duration_ms

---

### **Table 4: hyperparameters_log**

**Purpose**: Hyperparameter tuning experiments

**Key Columns**:
- trial_id, run_id
- hyperparameters (JSON)
- objective_value, scores
- tuning_method (optuna, grid_search, etc)

---

## 🎮 REINFORCEMENT LEARNING TABLES (FinRL)

### **Table 5: agent_training_runs**

**Purpose**: Track RL agent training

**Key Columns**:
- run_id, agent_type (ppo, a2c, ddpg, sac, td3)
- state_dim (110 features), action_dim
- reward_function_type
- final metrics (mean_reward, sharpe_ratio, total_return)

---

### **Table 6: agent_checkpoints**

**Purpose**: Store trained RL agents

**Key Columns**:
- checkpoint_id, run_id
- agent_binary (policy + value networks)
- performance at checkpoint
- deployment status

---

### **Table 7: reward_history**

**Purpose**: Episode-by-episode reward tracking

**Key Columns**:
- run_id, episode_number, timestep_number
- step_reward, episode_cumulative_reward
- episode_final_reward, sharpe_ratio
- learning metrics (policy_loss, value_loss)

---

### **Table 8: rl_hyperparameters**

**Purpose**: RL hyperparameter tuning

**Key Columns**:
- trial_id, run_id
- hyperparameters (learning_rate, gamma, clip_range, etc)
- mean_reward, sharpe_ratio
- total_timesteps, total_episodes

---

## 🔄 Training Workflows

### **Supervised Learning Example**:
1. Create training_run
2. Log training_metrics per iteration
3. Run hyperparameter tuning (log to hyperparameters_log)
4. Save best model to model_checkpoints
5. Update training_run with final metrics

### **RL (FinRL) Example**:
1. Create agent_training_run
2. Log reward_history per episode
3. Save agent_checkpoints every N episodes
4. Run RL hyperparameter tuning
5. Deploy best agent

---

## 📊 Query Examples

### Compare Model Performance:
```sql
SELECT
    run_name,
    model_type,
    final_test_accuracy,
    final_f1_score
FROM training_runs
WHERE status = 'completed'
ORDER BY final_test_accuracy DESC
LIMIT 10;
```

### Best RL Agents:
```sql
SELECT
    run_name,
    agent_type,
    final_sharpe_ratio,
    final_total_return
FROM agent_training_runs  
WHERE status = 'completed'
ORDER BY final_sharpe_ratio DESC
LIMIT 10;
```

---

## 🎯 Implementation Notes

1. **Model Storage**: Store binaries as base64 in ClickHouse (< 100MB models)
2. **Large Models**: Consider S3/MinIO for models > 100MB
3. **Metrics Retention**: Keep detailed metrics for 6 months, summaries forever
4. **Checkpointing**: Save every 100 epochs/episodes for recovery
5. **Version Control**: Track git_commit_hash for reproducibility

---

## 📝 Next Steps

1. Implement supervised-training-service using these tables
2. Implement finrl-training-service using RL tables  
3. Setup experiment tracking (optional: MLflow/W&B integration)
4. Design table_database_trading.md for live trading

---

**Version History**:
- v1.0.0 (2025-10-18): Initial complete training tables documentation
