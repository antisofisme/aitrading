# ML/DL Pipeline for AI Forex Trading Platform

Complete production-ready machine learning and deep learning pipeline architecture for the SUHO AI Trading Platform.

---

## 📋 Executive Summary

This ML/DL pipeline enables:
1. **Feature Engineering**: Transform raw OHLCV data into 100+ ML features
2. **Model Training**: Train LSTM, Transformer, XGBoost models with GPU acceleration
3. **Real-time Inference**: < 200ms prediction latency for live trading
4. **Pattern Matching**: Vector similarity search using Weaviate for historical pattern recognition
5. **Feedback Loop**: Continuous learning from trade results
6. **Multi-tenancy**: Isolated models per tenant/user

---

## 🏗️ Architecture Overview

### Data Flow

```
Polygon.io → NATS/Kafka → Data Bridge → TimescaleDB (90 days)
                                     ↓
                              ClickHouse (10 years)
                                     ↓
                         Feature Engineering
                                     ↓
                    ┌────────────────┴────────────────┐
                    ▼                                 ▼
            Model Training                    Real-time Inference
                    │                                 │
                    ▼                                 ▼
            Model Registry                    ML Predictions
            (PostgreSQL)                      (TimescaleDB)
                                                     │
                                    ┌────────────────┼────────────────┐
                                    ▼                ▼                ▼
                            Pattern Matching   Signal Gen    Feedback Loop
                             (Weaviate)        (NATS)       (Trade Results)
```

---

## 📊 Database Schemas

### 1. ClickHouse: ML Features (Training Data)

**Table: `ml_training.ml_features`**
- **Purpose**: Store engineered features for model training
- **Retention**: 10 years (3650 days)
- **Columns**: 100+ features including:
  - OHLCV data
  - Technical indicators (trend, momentum, volatility, volume)
  - Pattern recognition
  - Multi-horizon labels (1h, 4h, 1d)
  - Data quality scores

**Schema File**: `/schemas/01_clickhouse_ml_features.sql`

**Key Features:**
```sql
-- Trend Indicators
sma_10, sma_20, sma_50, sma_100, sma_200
ema_10, ema_20, ema_50, ema_100, ema_200
macd_line, macd_signal, macd_histogram
adx_14, plus_di_14, minus_di_14
tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b

-- Momentum Indicators
rsi_14, stoch_k, stoch_d, cci_20, williams_r_14
roc_10, roc_20, momentum_10

-- Volatility Indicators
bb_upper_20_2, bb_middle_20_2, bb_lower_20_2
atr_14, kc_upper, kc_middle, kc_lower
dc_upper_20, dc_lower_20, realized_vol_20

-- Volume Indicators
obv, vwap, mfi_14, volume_ratio

-- Multi-Horizon Labels
label_direction_1h, label_direction_4h, label_direction_1d
label_return_1h, label_return_4h, label_return_1d
label_max_gain_1h, label_max_loss_1h
```

### 2. PostgreSQL: Model Registry

**Schema: `ml_registry`**
- **Purpose**: Central registry for all ML/DL models
- **Tables**:
  - `models`: Model metadata, architecture, metrics
  - `training_jobs`: Training job tracking
  - `model_evaluations`: Evaluation history
  - `model_deployments`: Deployment tracking
  - `model_alerts`: Performance alerts
  - `experiments`: Experiment tracking

**Schema File**: `/schemas/02_postgresql_model_registry.sql`

**Key Model Metadata:**
```json
{
    "model_id": "uuid",
    "model_name": "eurusd_lstm_1h",
    "model_type": "lstm",
    "version": "v2.1.0",
    "status": "production",
    "architecture": { "layers": [...] },
    "hyperparameters": { "learning_rate": 0.001, ... },
    "features_used": ["close", "rsi_14", ...],
    "metrics": {
        "accuracy": 0.67,
        "sharpe_ratio": 1.8,
        "win_rate": 0.58
    },
    "model_storage_path": "s3://suho-models/..."
}
```

### 3. TimescaleDB: Real-Time Predictions

**Table: `ml_predictions`**
- **Purpose**: Store all real-time predictions
- **Hypertable**: Partitioned by time (1-day chunks) + tenant_id
- **Retention**: 90 days
- **Columns**:
  - Prediction outputs (direction, confidence, probabilities)
  - Pattern matching results (from Weaviate)
  - Signal generation info
  - Actual outcomes (for feedback loop)
  - Performance tracking

**Table: `trade_results`**
- **Purpose**: Store actual trade executions
- **Retention**: 3 years
- **Columns**:
  - Entry/exit prices and times
  - PnL (pips, %, amount)
  - Risk management (SL, TP, R:R)
  - Market conditions snapshot

**Schema File**: `/schemas/03_timescaledb_predictions.sql`

### 4. Weaviate: Vector Pattern Store

**Class: `TradingPattern`**
- **Purpose**: Store vectorized trading patterns for similarity matching
- **Vector Dimension**: 128 or 256
- **Distance Metric**: Cosine similarity
- **Key Properties**:
  - Pattern embeddings
  - Historical outcomes (profitable/loss/breakeven)
  - Technical indicator snapshots
  - Win rate, profit/loss statistics

**Class: `LiveMarketState`**
- **Purpose**: Real-time market state embeddings
- **TTL**: 24 hours (auto-cleanup)
- **Usage**: Match live data against historical patterns

**Schema File**: `/schemas/04_weaviate_pattern_vectors.json`

---

## 🔧 Components

### 1. Feature Engineering Service

**File**: `/src/feature_engineer.py`

**Responsibilities:**
- Query raw OHLCV from ClickHouse
- Compute 100+ technical indicators
- Calculate multi-horizon labels
- Store results in `ml_features` table

**Key Functions:**
```python
engineer = FeatureEngineer()

# Compute features for EUR/USD 1h
features_df = engineer.compute_features(
    ohlcv_df=ohlcv_data,
    tenant_id='tenant_001',
    user_id='user_123',
    symbol='EUR/USD',
    timeframe='1h'
)

# Save to ClickHouse
engineer.save_to_clickhouse(features_df)
```

**Features Computed:**
- ✅ 10 SMA/EMA periods
- ✅ MACD, ADX, Ichimoku
- ✅ RSI, Stochastic, CCI, Williams %R
- ✅ Bollinger Bands, ATR, Keltner, Donchian
- ✅ OBV, VWAP, MFI
- ✅ Candlestick patterns
- ✅ Support/Resistance, Pivot Points
- ✅ Multi-horizon labels (1h, 4h, 1d)

### 2. Model Training Service

**Responsibilities:**
- Query training data from ClickHouse
- Train ML/DL models (LSTM, Transformer, XGBoost)
- Hyperparameter tuning
- Model evaluation
- Save models to S3/MinIO
- Register in model registry

**Supported Models:**
- LSTM (time-series sequences)
- Transformer (multi-horizon attention)
- XGBoost (tabular features)
- Random Forest (baseline)
- Ensemble (voting/stacking)

**Training Configuration:**
```json
{
    "model_type": "lstm",
    "hyperparameters": {
        "sequence_length": 60,
        "lstm_units": [128, 64],
        "dropout": 0.2,
        "learning_rate": 0.001,
        "batch_size": 32,
        "epochs": 100
    },
    "features": ["close", "rsi_14", "macd_histogram", ...]
}
```

### 3. Inference Service

**Responsibilities:**
- Load production models from S3
- Real-time feature computation
- Generate predictions (< 200ms)
- Pattern matching via Weaviate
- Combine ML + Pattern signals
- Store predictions in TimescaleDB

**Prediction Flow:**
```
Market Data → Feature Computation → Embedding Generation
                     ↓                         ↓
            ML Prediction              Weaviate Search
                     ↓                         ↓
                Signal Aggregation (ML + Patterns)
                            ↓
                    Trading Signal
```

### 4. Pattern Matching Service

**Responsibilities:**
- Generate pattern embeddings (autoencoder)
- Store patterns in Weaviate
- Similarity search for live data
- Pattern consensus voting

**Usage:**
```python
# Find similar patterns
similar_patterns = pattern_matcher.find_similar_patterns(
    current_features=live_features,
    tenant_id='tenant_001',
    symbol='EUR/USD',
    limit=10
)

# Aggregate outcomes
votes = pattern_matcher.aggregate_pattern_outcomes(similar_patterns)
# Returns: {'bullish': 0.6, 'bearish': 0.3, 'neutral': 0.1}
```

### 5. Feedback Loop Service

**Responsibilities:**
- Monitor trade executions
- Update predictions with actual outcomes
- Create pattern vectors from successful trades
- Detect model performance degradation
- Trigger automated retraining

**Continuous Learning:**
```
Trade Result → Update Prediction (actual outcome)
            → Create Pattern Vector (Weaviate)
            → Monitor Performance
            → Trigger Retraining (if degraded)
```

---

## 📈 Multi-Horizon Predictions

### Supported Horizons

| Horizon | Use Case | Label Type |
|---------|----------|------------|
| **1h** | Scalping, short-term trades | Classification + Regression |
| **4h** | Swing trading | Classification + Regression |
| **1d** | Position trading | Classification + Regression |

### Label Types

1. **Classification**: Direction prediction
   - `1`: Bullish (price up > 0.1%)
   - `0`: Neutral (price unchanged)
   - `-1`: Bearish (price down > 0.1%)

2. **Regression**: Return prediction
   - `label_return_1h`: Expected return % in 1 hour
   - `label_max_gain_1h`: Max favorable movement
   - `label_max_loss_1h`: Max adverse movement

---

## 🔐 Multi-Tenant Isolation

### Data Isolation

**ClickHouse (ml_features):**
- Partitioned by `tenant_id`
- All queries include `WHERE tenant_id = ?`

**PostgreSQL (ml_registry):**
- Row-Level Security (RLS) policies
- `SET app.current_tenant_id = 'tenant_001'`

**TimescaleDB (predictions, trade_results):**
- Hypertable partitioning by `tenant_id`
- RLS enabled

**Weaviate (patterns):**
- Application-level filtering by `tenantId`

### Model Isolation

**Shared Models:**
- `user_id = NULL`
- Available to all users in tenant
- Example: EUR/USD baseline model

**User-Specific Models:**
- `user_id = 'user_123'`
- Private to individual user
- Fine-tuned on user's data

---

## 🚀 Deployment Workflow

### Model Lifecycle

```
DRAFT → TRAINING → TESTING → STAGING → CANARY → PRODUCTION → ARCHIVED
```

### Canary Deployment

1. Deploy new model to production
2. Route 10% traffic to new model
3. Monitor for 48 hours
4. Compare metrics (accuracy, latency, Sharpe ratio)
5. Promote to 100% or rollback

### Automated Retraining

**Triggers:**
- Performance degradation (accuracy < baseline * 0.9)
- Data drift (KS test p-value < 0.05)
- Scheduled (monthly)
- Manual (user-initiated)

**Workflow:**
1. Query new training data (last 2 years)
2. Train new model version
3. Evaluate on test set
4. A/B test (canary deployment)
5. Promote or rollback

---

## 📊 Performance Targets

### Latency

| Operation | Target | Strategy |
|-----------|--------|----------|
| Feature computation | < 50ms | Vectorized TA-Lib operations |
| Embedding generation | < 20ms | GPU inference, batching |
| ML prediction | < 100ms | ONNX Runtime, TorchScript |
| Weaviate search | < 50ms | HNSW index |
| **Total** | **< 200ms** | End-to-end optimization |

### Model Performance

- **Accuracy**: > 60% direction prediction
- **Sharpe Ratio**: > 1.5
- **Win Rate**: > 55%
- **Max Drawdown**: < 15%

### System Performance

- **Uptime**: 99.9%
- **Data Quality**: > 95% high-quality features
- **Cache Hit Rate**: > 70%

---

## 📁 File Structure

```
03-ml-pipeline/
├── README.md                          # This file
├── schemas/
│   ├── 01_clickhouse_ml_features.sql  # Feature store schema
│   ├── 02_postgresql_model_registry.sql  # Model registry schema
│   ├── 03_timescaledb_predictions.sql   # Predictions schema
│   └── 04_weaviate_pattern_vectors.json # Weaviate schema
├── docs/
│   ├── ML_PIPELINE_ARCHITECTURE.md    # Complete architecture guide
│   └── DEPLOYMENT_WORKFLOW.md         # Deployment procedures
├── src/
│   ├── feature_engineer.py            # Feature engineering service
│   ├── model_trainer.py               # Model training service
│   ├── inference_service.py           # Real-time inference
│   ├── pattern_matcher.py             # Weaviate pattern matching
│   └── feedback_loop.py               # Continuous learning
├── configs/
│   ├── eurusd_lstm_1h.json            # Model configs
│   └── feature_engineering.yaml       # Feature config
├── scripts/
│   ├── export_training_data.py        # Data export utilities
│   ├── train_model.py                 # Training scripts
│   ├── evaluate_model.py              # Evaluation scripts
│   └── deploy_model.py                # Deployment scripts
├── notebooks/
│   ├── model_development.ipynb        # Development notebooks
│   └── feature_analysis.ipynb         # Feature exploration
└── requirements.txt                    # Python dependencies
```

---

## 🔧 Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Feature Store** | ClickHouse | Historical training data (10 years) |
| **Model Registry** | PostgreSQL | Model metadata and versioning |
| **Real-time DB** | TimescaleDB | Predictions and trade results (90 days) |
| **Vector DB** | Weaviate | Pattern similarity search |
| **Cache** | DragonflyDB | Hot data caching |
| **Messaging** | NATS + Kafka | Real-time data streaming |
| **ML Framework** | PyTorch, TensorFlow | Deep learning models |
| **ML Toolkit** | Scikit-learn, XGBoost | Classical ML models |
| **Feature Engineering** | TA-Lib, Pandas | Technical indicators |
| **Model Storage** | S3 / MinIO | Model binaries |
| **Orchestration** | Kubernetes | Service deployment |

---

## 📖 Documentation

### Core Documents

1. **[ML_PIPELINE_ARCHITECTURE.md](docs/ML_PIPELINE_ARCHITECTURE.md)**
   - Complete system architecture
   - Data flow diagrams
   - Component details
   - Integration patterns
   - Performance optimization
   - Monitoring & alerts

2. **[DEPLOYMENT_WORKFLOW.md](docs/DEPLOYMENT_WORKFLOW.md)**
   - Model lifecycle management
   - Versioning strategy
   - Canary deployments
   - A/B testing
   - Automated retraining
   - Rollback procedures

### Schema Files

1. **[01_clickhouse_ml_features.sql](schemas/01_clickhouse_ml_features.sql)**
   - Feature store schema
   - 100+ feature columns
   - Multi-horizon labels
   - Materialized views

2. **[02_postgresql_model_registry.sql](schemas/02_postgresql_model_registry.sql)**
   - Model registry schema
   - Training jobs tracking
   - Deployment history
   - Alert management

3. **[03_timescaledb_predictions.sql](schemas/03_timescaledb_predictions.sql)**
   - Real-time predictions schema
   - Trade results tracking
   - Performance metrics
   - Continuous aggregates

4. **[04_weaviate_pattern_vectors.json](schemas/04_weaviate_pattern_vectors.json)**
   - Vector schema for patterns
   - Similarity search config
   - Integration examples

---

## 🚀 Quick Start

### 1. Initialize Databases

```bash
# ClickHouse
clickhouse-client < schemas/01_clickhouse_ml_features.sql

# PostgreSQL
psql -U suho_admin -d suho_trading < schemas/02_postgresql_model_registry.sql
psql -U suho_admin -d suho_trading < schemas/03_timescaledb_predictions.sql

# Weaviate
python scripts/init_weaviate_schema.py
```

### 2. Compute Features

```python
from src.feature_engineer import FeatureEngineer

engineer = FeatureEngineer()

# Compute features for last 30 days
engineer.compute_and_save(
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now(),
    tenant_id='tenant_001',
    user_id='user_123',
    symbol='EUR/USD',
    timeframe='1h'
)
```

### 3. Train Model

```bash
python scripts/train_model.py \
    --config configs/eurusd_lstm_1h.json \
    --tenant tenant_001 \
    --symbol EUR/USD \
    --timeframe 1h
```

### 4. Deploy Model

```bash
# Deploy to staging
python scripts/deploy_model.py \
    --model-id uuid-1234-5678 \
    --environment staging

# Canary deployment (10% traffic)
python scripts/deploy_model.py \
    --model-id uuid-1234-5678 \
    --environment production \
    --canary \
    --traffic-percentage 10
```

---

## 📊 Monitoring

### Dashboards

1. **Model Performance**
   - Real-time accuracy (rolling 1h)
   - Prediction latency (P50, P95, P99)
   - Signal generation rate
   - Model comparison

2. **Trading Performance**
   - Win rate by model
   - Sharpe ratio
   - Max drawdown
   - PnL by symbol

3. **System Health**
   - Feature computation latency
   - Database query latency
   - Weaviate search latency
   - Cache hit rate

### Alerts

- Model accuracy drop (< 10% baseline)
- High prediction latency (P95 > 500ms)
- Data quality degradation (< 80%)
- Pattern match rate low (< 5%)

---

## 🎯 Success Metrics

### Model Performance
- ✅ Accuracy > 60%
- ✅ Sharpe Ratio > 1.5
- ✅ Win Rate > 55%
- ✅ Max Drawdown < 15%

### System Performance
- ✅ Prediction Latency P95 < 200ms
- ✅ Uptime 99.9%
- ✅ Data Quality > 95%

### Business Metrics
- ✅ User Satisfaction > 4.5/5
- ✅ Model Adoption > 70%
- ✅ Cost < $0.001 per prediction

---

## 🛠️ Troubleshooting

### Common Issues

**Model accuracy drops:**
- Check for data drift
- Verify feature quality
- Trigger retraining

**High latency:**
- Enable model caching
- Convert to ONNX
- Scale inference service

**Training fails:**
- Check GPU availability
- Verify data quality
- Review hyperparameters

---

## 📞 Support

For questions or issues:
- **Documentation**: See `/docs` directory
- **Schemas**: See `/schemas` directory
- **Examples**: See `/notebooks` directory

---

**Version**: 1.0.0
**Last Updated**: 2025-10-05
**Status**: Production Ready
**Author**: ML Engineering Team
