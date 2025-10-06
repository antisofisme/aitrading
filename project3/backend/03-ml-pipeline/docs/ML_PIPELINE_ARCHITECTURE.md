# Complete ML/DL Pipeline Architecture for AI Forex Trading Platform

## Executive Summary

This document defines the production-ready ML/DL pipeline architecture for the SUHO AI Trading Platform, integrating real-time forex data ingestion, feature engineering, model training/deployment, and continuous learning feedback loops.

---

## 1. System Overview

### 1.1 Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        CLIENT APPLICATIONS                               │
│                  (Web Dashboard, Mobile App, Trading Bots)               │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ REST/WebSocket
┌────────────────────────────────▼────────────────────────────────────────┐
│                          API GATEWAY                                     │
│              (Authentication, Rate Limiting, Routing)                    │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌────────▼────────┐   ┌──────────▼──────────┐   ┌──────▼───────────┐
│  DATA INGESTION │   │  ML/DL PIPELINE     │   │  TRADING ENGINE  │
│   (Polygon.io)  │   │  (This Document)    │   │  (Execution)     │
└────────┬────────┘   └──────────┬──────────┘   └──────┬───────────┘
         │                       │                       │
         │              ┌────────┴────────┐              │
         │              │                 │              │
┌────────▼──────────────▼─────┐   ┌──────▼──────────────▼──────┐
│   DATA LAYER (Storage)      │   │   MESSAGING LAYER           │
│  - TimescaleDB (90 days)    │   │   - NATS (real-time)        │
│  - ClickHouse (10 years)    │   │   - Kafka (durable)         │
│  - Weaviate (vectors)       │   │                             │
│  - DragonflyDB (cache)      │   │                             │
└─────────────────────────────┘   └─────────────────────────────┘
```

### 1.2 ML Pipeline Components

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          ML/DL PIPELINE                                   │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────┐      ┌──────────────────┐      ┌────────────────┐  │
│  │ 1. FEATURE      │─────▶│ 2. MODEL         │─────▶│ 3. INFERENCE   │  │
│  │    ENGINEERING  │      │    TRAINING      │      │    SERVICE     │  │
│  └─────────────────┘      └──────────────────┘      └────────────────┘  │
│         │                          │                          │          │
│         │                          │                          │          │
│         ▼                          ▼                          ▼          │
│  ┌─────────────────┐      ┌──────────────────┐      ┌────────────────┐  │
│  │ ClickHouse      │      │ Model Registry   │      │ Predictions    │  │
│  │ (ml_features)   │      │ (PostgreSQL)     │      │ (TimescaleDB)  │  │
│  └─────────────────┘      └──────────────────┘      └────────────────┘  │
│                                                               │          │
│         ┌─────────────────────────────────────────────────────┘          │
│         │                                                                │
│         ▼                                                                │
│  ┌─────────────────┐      ┌──────────────────┐      ┌────────────────┐  │
│  │ 4. PATTERN      │─────▶│ 5. SIGNAL        │─────▶│ 6. FEEDBACK    │  │
│  │    MATCHING     │      │    GENERATION    │      │    LOOP        │  │
│  └─────────────────┘      └──────────────────┘      └────────────────┘  │
│         │                          │                          │          │
│         ▼                          ▼                          ▼          │
│  ┌─────────────────┐      ┌──────────────────┐      ┌────────────────┐  │
│  │ Weaviate        │      │ Trading Signals  │      │ Trade Results  │  │
│  │ (vectors)       │      │ (NATS/Kafka)     │      │ (TimescaleDB)  │  │
│  └─────────────────┘      └──────────────────┘      └────────────────┘  │
│                                                               │          │
│                          ┌────────────────────────────────────┘          │
│                          │   (Continuous Learning)                       │
│                          └──────────────────────────────────┐            │
│                                                             ▼            │
│                                                  ┌──────────────────┐    │
│                                                  │ 7. MODEL         │    │
│                                                  │    RETRAINING    │    │
│                                                  └──────────────────┘    │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Data Flow Architecture

### 2.1 Training Data Pipeline

```
Raw OHLCV Data (ClickHouse: aggregates)
           │
           ▼
┌──────────────────────────────────┐
│  FEATURE ENGINEERING SERVICE     │
│                                  │
│  Input: Raw OHLCV + External     │
│  Output: ml_features table       │
│                                  │
│  Computes:                       │
│  - Technical Indicators          │
│  - Pattern Recognition           │
│  - Multi-horizon Labels          │
│  - External Data Enrichment      │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│  ClickHouse: ml_features         │
│                                  │
│  - 100+ feature columns          │
│  - Multi-horizon labels          │
│  - 10-year retention             │
│  - Multi-tenant partitioned      │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│  MODEL TRAINING SERVICE          │
│                                  │
│  1. Query ml_features            │
│  2. Feature selection            │
│  3. Train/validate/test split    │
│  4. Model training (GPU)         │
│  5. Hyperparameter tuning        │
│  6. Model evaluation             │
│  7. Model serialization          │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│  Model Storage (S3/MinIO)        │
│  + Model Registry (PostgreSQL)   │
│                                  │
│  - Model binary (.h5, .pt)       │
│  - Metadata & metrics            │
│  - Version tracking              │
└──────────────────────────────────┘
```

### 2.2 Real-Time Inference Pipeline

```
Live Market Data (NATS/Kafka)
           │
           ▼
┌──────────────────────────────────┐
│  FEATURE COMPUTATION             │
│  (Real-time feature engineering) │
│                                  │
│  - Sliding window indicators     │
│  - Pattern detection             │
│  - External data lookup          │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│  EMBEDDING GENERATION            │
│  (For pattern matching)          │
│                                  │
│  - Autoencoder inference         │
│  - Vector normalization          │
└──────────────┬───────────────────┘
               │
               ├──────────────────────────┐
               │                          │
               ▼                          ▼
┌──────────────────────────┐   ┌─────────────────────┐
│  ML INFERENCE SERVICE    │   │  WEAVIATE SEARCH    │
│                          │   │                     │
│  1. Load model           │   │  1. Similarity      │
│  2. Feature scaling      │   │     search          │
│  3. Prediction           │   │  2. Find top K      │
│  4. Confidence scoring   │   │     patterns        │
└──────────────┬───────────┘   └──────────┬──────────┘
               │                          │
               └──────────┬───────────────┘
                          │
                          ▼
               ┌──────────────────────────────┐
               │  SIGNAL AGGREGATION          │
               │                              │
               │  - Combine ML prediction     │
               │  - Pattern consensus voting  │
               │  - Risk assessment           │
               │  - Confidence threshold      │
               └──────────────┬───────────────┘
                              │
                              ▼
               ┌──────────────────────────────┐
               │  Store Prediction            │
               │  (TimescaleDB: ml_predictions)│
               └──────────────┬───────────────┘
                              │
                              ▼
               ┌──────────────────────────────┐
               │  Generate Trading Signal     │
               │  (if confidence > threshold) │
               └──────────────┬───────────────┘
                              │
                              ▼
                  Trading Engine (execution)
```

### 2.3 Feedback Loop (Continuous Learning)

```
Trade Execution
       │
       ▼
┌──────────────────────────────────┐
│  Trade Results Recorded          │
│  (TimescaleDB: trade_results)    │
│                                  │
│  - Entry/Exit prices             │
│  - PnL (pips, %, $)              │
│  - Trade duration                │
│  - Market conditions             │
└──────────────┬───────────────────┘
               │
               ├─────────────────────────────┐
               │                             │
               ▼                             ▼
┌──────────────────────────┐   ┌─────────────────────────┐
│  Update Predictions      │   │  Create Pattern Vector  │
│  (actual outcome)        │   │  (Weaviate)             │
│                          │   │                         │
│  - actual_direction      │   │  - Store embedding      │
│  - actual_return         │   │  - historicalOutcome    │
│  - direction_correct     │   │  - profitLossPips       │
└──────────────┬───────────┘   └──────────────┬──────────┘
               │                              │
               └──────────┬───────────────────┘
                          │
                          ▼
               ┌──────────────────────────────┐
               │  Performance Monitoring      │
               │                              │
               │  - Calculate accuracy        │
               │  - Win rate tracking         │
               │  - Drift detection           │
               │  - Alert generation          │
               └──────────────┬───────────────┘
                              │
                   If performance degrades
                              │
                              ▼
               ┌──────────────────────────────┐
               │  Trigger Retraining          │
               │                              │
               │  1. Query new data           │
               │  2. Retrain model            │
               │  3. A/B test new version     │
               │  4. Gradual rollout          │
               └──────────────────────────────┘
```

---

## 3. Database Schema Details

### 3.1 ClickHouse: Feature Store

**Table: `ml_features`**
- **Purpose**: Wide table storing all engineered features for model training
- **Retention**: 10 years (3650 days)
- **Partitioning**: By tenant_id, symbol, month
- **Key Columns**:
  - Primary: tenant_id, user_id, symbol, timeframe, timestamp
  - OHLCV: open, high, low, close, volume
  - Trend Indicators: SMA (10,20,50,100,200), EMA, MACD, ADX, Ichimoku
  - Momentum: RSI, Stochastic, CCI, Williams %R, ROC
  - Volatility: Bollinger Bands, ATR, Keltner, Donchian, Historical Vol
  - Volume: OBV, VWAP, MFI
  - Patterns: Candlestick patterns, support/resistance
  - Labels: direction (1h, 4h, 1d), returns, max gain/loss, trade outcomes

**Table: `feature_jobs`**
- Tracks feature engineering jobs for monitoring

**Table: `feature_importance`**
- Stores feature importance scores from trained models

**Materialized Views**:
- `latest_features`: Real-time feature vectors per symbol
- `feature_stats`: Statistical properties for normalization

### 3.2 PostgreSQL: Model Registry

**Schema: `ml_registry`**

**Table: `models`**
- **Purpose**: Central registry for all ML/DL models
- **Key Fields**:
  - model_id, tenant_id, user_id
  - model_name, model_type, task_type
  - architecture (JSONB), hyperparameters (JSONB)
  - features_used (TEXT[]), feature_version
  - training data range, sample counts
  - metrics (JSONB), storage path
  - deployment info, parent_model_id

**Table: `training_jobs`**
- Tracks all training attempts (success/failure)
- Progress monitoring (current_epoch, losses)
- Resource usage tracking

**Table: `model_evaluations`**
- Historical evaluation results
- A/B testing comparisons
- Statistical significance testing

**Table: `model_deployments`**
- Deployment history (blue/green, canary)
- Environment tracking (staging/production)
- Rollback capability

**Table: `model_alerts`**
- Performance degradation alerts
- Data drift warnings
- High latency notifications

**Table: `experiments`**
- Experiment tracking (alternative to MLflow)
- Hyperparameter tuning results

### 3.3 TimescaleDB: Real-Time Predictions

**Table: `ml_predictions`**
- **Purpose**: Store all real-time predictions
- **Hypertable**: Partitioned by time (1-day chunks) + tenant_id
- **Retention**: 90 days
- **Key Fields**:
  - time, prediction_id, tenant_id, user_id
  - model_id, model_name, model_version
  - symbol, timeframe
  - input_features (JSONB snapshot)
  - predicted_direction, direction_confidence
  - predicted_price, predicted_return
  - probabilities (JSONB), risk estimates
  - pattern matching results (from Weaviate)
  - signal generation info
  - actual outcomes (for feedback)
  - accuracy metrics, latency tracking

**Table: `trade_results`**
- **Purpose**: Store actual trade executions
- **Hypertable**: Partitioned by time + tenant_id
- **Retention**: 3 years
- **Key Fields**:
  - trade_id, prediction_id linkage
  - entry/exit prices and times
  - PnL (pips, %, amount)
  - risk management (SL, TP, R:R)
  - market conditions snapshot
  - slippage, commission tracking

**Table: `model_performance_timeseries`**
- Time-series performance metrics
- Aggregated by window (1h, 1d, 7d)
- Drift detection data

**Continuous Aggregates**:
- `ml_predictions_hourly`: Hourly prediction stats
- `trade_results_daily`: Daily trading performance

**Triggers**:
- Auto-update predictions when trade results recorded

### 3.4 Weaviate: Vector Pattern Store

**Class: `TradingPattern`**
- **Purpose**: Store vectorized trading patterns
- **Vector Dimension**: 128 or 256
- **Distance Metric**: Cosine similarity
- **Key Properties**:
  - tenantId, userId, patternId
  - symbol, timeframe, timestamp
  - patternType, sequenceLength
  - featureVector (raw features for reference)
  - technicalIndicators (object)
  - historicalOutcome, profitLossPips
  - winRate, occurrenceCount
  - modelId, embeddingVersion
  - marketConditions (object)
  - confidence, verified, tags

**Class: `LiveMarketState`**
- **Purpose**: Real-time market state embeddings
- **TTL**: Auto-delete after 24 hours
- **Key Properties**:
  - Current market features
  - matchedPatternIds (from similarity search)
  - topSimilarityScore
  - signalGenerated, predictionId

**Class: `AnomalyPattern`**
- **Purpose**: Detected anomalies and unusual patterns
- **Key Properties**:
  - anomalyType, severity, anomalyScore
  - marketImpact, eventCause
  - affectedModels

---

## 4. Feature Engineering Strategy

### 4.1 Feature Categories

| Category | Features | Storage |
|----------|----------|---------|
| **Price Action** | OHLCV, mid_price, spread, range_pips, body_pips | ClickHouse |
| **Trend** | SMA (5 periods), EMA (5), MACD, ADX, Ichimoku | ClickHouse |
| **Momentum** | RSI, Stochastic, CCI, Williams %R, ROC, Momentum | ClickHouse |
| **Volatility** | Bollinger Bands, ATR, Keltner, Donchian, Realized Vol | ClickHouse |
| **Volume** | Volume SMA, OBV, VWAP, MFI | ClickHouse |
| **Patterns** | Candlestick patterns, support/resistance levels | ClickHouse |
| **Higher Timeframe** | 1h/4h/1d trend context | ClickHouse |
| **External** | Economic calendar, sentiment, correlations | ClickHouse |
| **Labels** | Multi-horizon (1h, 4h, 1d) direction + returns | ClickHouse |

### 4.2 Feature Computation Workflow

```python
# Pseudocode for feature engineering

class FeatureEngineer:
    def compute_features(self, ohlcv_data, symbol, timeframe):
        """
        Compute all features from raw OHLCV data

        Args:
            ohlcv_data: DataFrame with OHLCV columns
            symbol: Trading pair (e.g., 'EUR/USD')
            timeframe: Base timeframe (e.g., '1h')

        Returns:
            DataFrame with 100+ feature columns
        """
        features = pd.DataFrame()

        # 1. Price derivatives
        features['mid_price'] = (ohlcv_data['bid'] + ohlcv_data['ask']) / 2
        features['spread'] = ohlcv_data['ask'] - ohlcv_data['bid']
        features['range_pips'] = ohlcv_data['high'] - ohlcv_data['low']

        # 2. Trend indicators
        for period in [10, 20, 50, 100, 200]:
            features[f'sma_{period}'] = talib.SMA(ohlcv_data['close'], period)
            features[f'ema_{period}'] = talib.EMA(ohlcv_data['close'], period)

        features['macd_line'], features['macd_signal'], features['macd_histogram'] = \
            talib.MACD(ohlcv_data['close'])

        # 3. Momentum indicators
        features['rsi_14'] = talib.RSI(ohlcv_data['close'], 14)
        features['stoch_k'], features['stoch_d'] = talib.STOCH(
            ohlcv_data['high'], ohlcv_data['low'], ohlcv_data['close']
        )

        # 4. Volatility indicators
        features['bb_upper'], features['bb_middle'], features['bb_lower'] = \
            talib.BBANDS(ohlcv_data['close'], 20, 2, 2)
        features['atr_14'] = talib.ATR(ohlcv_data['high'],
                                       ohlcv_data['low'],
                                       ohlcv_data['close'], 14)

        # 5. Volume indicators
        features['obv'] = talib.OBV(ohlcv_data['close'], ohlcv_data['volume'])
        features['mfi_14'] = talib.MFI(ohlcv_data['high'],
                                       ohlcv_data['low'],
                                       ohlcv_data['close'],
                                       ohlcv_data['volume'], 14)

        # 6. Pattern recognition
        features['pattern_doji'] = talib.CDLDOJI(ohlcv_data['open'],
                                                  ohlcv_data['high'],
                                                  ohlcv_data['low'],
                                                  ohlcv_data['close'])

        # 7. Higher timeframe context
        features['htf_trend_1h'] = self.get_htf_trend(symbol, '1h')
        features['htf_trend_4h'] = self.get_htf_trend(symbol, '4h')
        features['htf_trend_1d'] = self.get_htf_trend(symbol, '1d')

        # 8. External data enrichment
        features['upcoming_event_impact'] = self.get_economic_calendar(symbol)
        features['sentiment_score'] = self.get_sentiment(symbol)

        # 9. Multi-horizon labels
        features['label_direction_1h'] = self.compute_direction_label(
            ohlcv_data, horizon='1h'
        )
        features['label_return_1h'] = self.compute_return_label(
            ohlcv_data, horizon='1h'
        )

        # 10. Data quality scoring
        features['data_quality_score'] = self.assess_quality(features)

        return features
```

### 4.3 Feature Normalization

**Stored in ClickHouse `feature_stats` materialized view:**
- Mean, std, min, max per feature
- Updated daily
- Used for real-time scaling during inference

**Normalization methods:**
- StandardScaler: For indicators with normal distribution (RSI, Stochastic)
- MinMaxScaler: For bounded indicators (0-100)
- RobustScaler: For price-based features (resistant to outliers)

---

## 5. Model Training & Deployment

### 5.1 Model Types

| Model Type | Use Case | Framework | Input Shape |
|------------|----------|-----------|-------------|
| **LSTM** | Time-series sequence prediction | PyTorch/TensorFlow | (batch, seq_len, features) |
| **Transformer** | Multi-horizon attention-based | PyTorch | (batch, seq_len, features) |
| **XGBoost** | Tabular feature classification | XGBoost | (batch, features) |
| **Random Forest** | Baseline model | Scikit-learn | (batch, features) |
| **Ensemble** | Voting/stacking models | Custom | Multiple models |

### 5.2 Training Workflow

```python
# Training service pseudocode

class ModelTrainer:
    def train_model(self, config):
        """
        Train a new model

        Args:
            config: TrainingConfig with hyperparameters
        """
        # 1. Query training data from ClickHouse
        features_df = clickhouse.query(f"""
            SELECT * FROM ml_features
            WHERE tenant_id = '{config.tenant_id}'
              AND symbol = '{config.symbol}'
              AND timeframe = '{config.timeframe}'
              AND timestamp >= '{config.start_date}'
              AND timestamp <= '{config.end_date}'
              AND data_quality_score > 0.9
            ORDER BY timestamp
        """)

        # 2. Feature selection
        selected_features = self.select_features(
            features_df,
            config.feature_list
        )

        # 3. Train/val/test split (chronological)
        train, val, test = self.chronological_split(
            selected_features,
            ratios=[0.7, 0.15, 0.15]
        )

        # 4. Normalize features
        scaler = StandardScaler()
        train_scaled = scaler.fit_transform(train)
        val_scaled = scaler.transform(val)

        # 5. Build model
        model = self.build_model(config.architecture)

        # 6. Train with early stopping
        history = model.fit(
            train_scaled,
            epochs=config.epochs,
            validation_data=val_scaled,
            callbacks=[
                EarlyStopping(patience=10),
                ModelCheckpoint(save_best_only=True),
                TensorBoard(log_dir=config.log_dir)
            ]
        )

        # 7. Evaluate on test set
        metrics = self.evaluate(model, test)

        # 8. Save model
        model_path = self.save_model(model, config)

        # 9. Register in PostgreSQL
        self.register_model(
            model_path=model_path,
            config=config,
            metrics=metrics,
            feature_list=selected_features.columns.tolist()
        )

        return model, metrics
```

### 5.3 Model Versioning Strategy

**Semantic Versioning: `vMAJOR.MINOR.PATCH`**
- **MAJOR**: Breaking changes (architecture change, feature set change)
- **MINOR**: Feature additions, hyperparameter improvements
- **PATCH**: Bug fixes, retraining on new data (same config)

**Example:**
- `v1.0.0`: Initial LSTM model with 50 features
- `v1.1.0`: Added 10 new features (volume indicators)
- `v1.1.1`: Retrained on updated data
- `v2.0.0`: Switched to Transformer architecture

**Model Storage:**
```
s3://suho-models/
  ├── tenant_001/
  │   ├── eurusd_lstm_1h/
  │   │   ├── v1.0.0/
  │   │   │   ├── model.h5
  │   │   │   ├── scaler.pkl
  │   │   │   ├── config.json
  │   │   │   └── metadata.json
  │   │   ├── v1.1.0/
  │   │   └── v2.0.0/
  │   └── xauusd_transformer_4h/
  └── tenant_002/
```

### 5.4 Deployment Strategy

**Blue/Green Deployment:**
1. Deploy new model version to staging
2. A/B test: 10% traffic to new model, 90% to old
3. Monitor performance for 24-48 hours
4. If metrics improve: gradual rollout (50%, 100%)
5. If metrics degrade: instant rollback

**Canary Deployment:**
- Deploy to specific users first (beta testers)
- Monitor performance and feedback
- Gradual expansion to all users

**Model Registry Status:**
- `draft`: Model trained but not deployed
- `testing`: In A/B test
- `production`: Active in production
- `archived`: Deprecated model

---

## 6. Real-Time Inference Architecture

### 6.1 Inference Service

```python
# Inference service pseudocode

class InferenceService:
    def __init__(self):
        self.models = {}  # model_id -> loaded model
        self.scalers = {}  # model_id -> scaler
        self.embedding_model = None  # For Weaviate patterns

    def load_models(self):
        """Load all production models into memory"""
        active_models = postgresql.query("""
            SELECT model_id, model_storage_path, features_used
            FROM ml_registry.models
            WHERE status = 'production'
        """)

        for model in active_models:
            self.models[model.id] = load_model(model.path)
            self.scalers[model.id] = load_scaler(model.scaler_path)

    async def predict(self, market_data, tenant_id, user_id, symbol):
        """
        Generate prediction for current market state

        Args:
            market_data: Latest OHLCV + indicators
            tenant_id, user_id, symbol: Identifiers

        Returns:
            Prediction with confidence and similar patterns
        """
        start_time = time.time()

        # 1. Feature engineering (real-time)
        features = self.compute_features(market_data)

        # 2. Get active model for this symbol
        model_id = self.get_active_model(tenant_id, symbol)
        model = self.models[model_id]
        scaler = self.scalers[model_id]

        # 3. Feature scaling
        features_scaled = scaler.transform(features)

        # 4. ML Prediction
        prediction = model.predict(features_scaled)
        confidence = self.compute_confidence(prediction)

        # 5. Generate embedding for pattern matching
        embedding = self.embedding_model.encode(features)

        # 6. Find similar patterns in Weaviate
        similar_patterns = await weaviate.search(
            collection='TradingPattern',
            vector=embedding,
            filters={
                'tenantId': tenant_id,
                'symbol': symbol,
                'verified': True
            },
            limit=10
        )

        # 7. Pattern consensus voting
        pattern_votes = self.aggregate_pattern_outcomes(similar_patterns)

        # 8. Combined prediction (ML + Patterns)
        final_prediction = self.combine_predictions(
            ml_prediction=prediction,
            ml_confidence=confidence,
            pattern_votes=pattern_votes
        )

        # 9. Risk assessment
        risk_metrics = self.assess_risk(
            prediction=final_prediction,
            volatility=features['atr_14'],
            similar_patterns=similar_patterns
        )

        # 10. Store prediction in TimescaleDB
        prediction_id = await timescaledb.insert(
            table='ml_predictions',
            data={
                'tenant_id': tenant_id,
                'user_id': user_id,
                'model_id': model_id,
                'symbol': symbol,
                'predicted_direction': final_prediction['direction'],
                'direction_confidence': final_prediction['confidence'],
                'similar_pattern_count': len(similar_patterns),
                'pattern_similarity_score': similar_patterns[0].score,
                'inference_latency_ms': (time.time() - start_time) * 1000,
                # ... other fields
            }
        )

        # 11. Generate signal if confidence threshold met
        if final_prediction['confidence'] > 0.7:
            signal = self.generate_signal(
                prediction=final_prediction,
                risk_metrics=risk_metrics
            )
            await nats.publish('trading.signals', signal)

        return {
            'prediction_id': prediction_id,
            'prediction': final_prediction,
            'similar_patterns': similar_patterns,
            'signal_generated': final_prediction['confidence'] > 0.7
        }
```

### 6.2 Pattern Matching with Weaviate

```python
class PatternMatcher:
    def __init__(self):
        self.weaviate_client = weaviate.Client(url="http://weaviate:8080")
        self.embedding_model = AutoEncoder()  # Trained on ml_features

    async def find_similar_patterns(self, current_features, tenant_id, symbol):
        """
        Find historical patterns similar to current market state

        Returns:
            List of similar patterns with outcomes
        """
        # 1. Generate embedding
        embedding = self.embedding_model.encode(current_features)

        # 2. Weaviate similarity search
        results = self.weaviate_client.query.get(
            'TradingPattern',
            [
                'patternId', 'timestamp', 'historicalOutcome',
                'profitLossPips', 'returnPercent', 'winRate',
                'technicalIndicators { rsi14 macdHistogram }'
            ]
        ).with_near_vector({
            'vector': embedding.tolist(),
            'certainty': 0.7  # Minimum similarity threshold
        }).with_where({
            'operator': 'And',
            'operands': [
                {'path': ['tenantId'], 'operator': 'Equal', 'valueText': tenant_id},
                {'path': ['symbol'], 'operator': 'Equal', 'valueText': symbol},
                {'path': ['verified'], 'operator': 'Equal', 'valueBoolean': True}
            ]
        }).with_limit(20).do()

        patterns = results['data']['Get']['TradingPattern']

        # 3. Filter by market regime similarity
        filtered_patterns = [
            p for p in patterns
            if self.is_similar_regime(
                current_features,
                p['technicalIndicators']
            )
        ]

        return filtered_patterns[:10]  # Top 10

    def aggregate_pattern_outcomes(self, patterns):
        """
        Vote aggregation from similar patterns

        Returns:
            {'bullish': 0.6, 'bearish': 0.3, 'neutral': 0.1}
        """
        if not patterns:
            return {'bullish': 0.33, 'bearish': 0.33, 'neutral': 0.34}

        votes = {'bullish': 0, 'bearish': 0, 'neutral': 0}

        for pattern in patterns:
            similarity = pattern['_additional']['certainty']

            if pattern['historicalOutcome'] == 'profitable':
                if pattern['profitLossPips'] > 0:
                    votes['bullish'] += similarity
                else:
                    votes['bearish'] += similarity
            elif pattern['historicalOutcome'] == 'loss':
                # Inverse signal
                if pattern['profitLossPips'] < 0:
                    votes['bullish'] += similarity * 0.5  # Lower weight
            else:
                votes['neutral'] += similarity

        # Normalize
        total = sum(votes.values())
        return {k: v/total for k, v in votes.items()}
```

---

## 7. Feedback Loop & Continuous Learning

### 7.1 Trade Results → Model Improvement

```python
class FeedbackLoop:
    async def process_trade_result(self, trade_result):
        """
        Process completed trade and update models

        Args:
            trade_result: Trade execution result from trading engine
        """
        # 1. Update prediction with actual outcome
        if trade_result.prediction_id:
            await timescaledb.update(
                table='ml_predictions',
                where={'prediction_id': trade_result.prediction_id},
                data={
                    'actual_direction': self.compute_direction(
                        trade_result.pnl_pips
                    ),
                    'actual_return': trade_result.pnl_percent,
                    'direction_correct': self.is_direction_correct(
                        trade_result
                    ),
                    'outcome_recorded_at': trade_result.exit_time
                }
            )

        # 2. Create pattern vector in Weaviate
        if trade_result.pnl_pips != 0:  # Skip breakeven trades
            pattern_embedding = self.generate_pattern_embedding(
                trade_result.market_conditions
            )

            await weaviate.create(
                collection='TradingPattern',
                properties={
                    'tenantId': trade_result.tenant_id,
                    'symbol': trade_result.symbol,
                    'timestamp': trade_result.entry_time,
                    'historicalOutcome': 'profitable' if trade_result.pnl_pips > 0 else 'loss',
                    'profitLossPips': trade_result.pnl_pips,
                    'returnPercent': trade_result.pnl_percent,
                    'verified': True,
                    'technicalIndicators': trade_result.market_conditions,
                    # ... other fields
                },
                vector=pattern_embedding
            )

        # 3. Update performance metrics
        await self.update_model_performance(trade_result)

        # 4. Check for performance degradation
        await self.check_model_health(trade_result.model_id)

    async def check_model_health(self, model_id):
        """
        Detect model degradation and trigger retraining
        """
        # Query recent performance
        recent_performance = await timescaledb.query("""
            SELECT
                AVG(CASE WHEN direction_correct THEN 1.0 ELSE 0.0 END) as accuracy,
                COUNT(*) as prediction_count
            FROM ml_predictions
            WHERE model_id = $1
              AND outcome_recorded_at >= NOW() - INTERVAL '7 days'
              AND outcome_recorded_at IS NOT NULL
        """, model_id)

        # Get baseline performance
        baseline = await postgresql.query("""
            SELECT metrics->'accuracy' as baseline_accuracy
            FROM ml_registry.models
            WHERE model_id = $1
        """, model_id)

        # Degradation threshold: 10% drop in accuracy
        if recent_performance.accuracy < baseline.baseline_accuracy * 0.9:
            # Create alert
            await postgresql.insert(
                table='ml_registry.model_alerts',
                data={
                    'model_id': model_id,
                    'alert_type': 'performance_degradation',
                    'severity': 'critical',
                    'metric_name': 'accuracy',
                    'current_value': recent_performance.accuracy,
                    'threshold_value': baseline.baseline_accuracy * 0.9,
                    'message': f'Model accuracy dropped to {recent_performance.accuracy:.2%}'
                }
            )

            # Trigger retraining workflow
            await self.trigger_retraining(model_id)
```

### 7.2 Automated Retraining Pipeline

```python
class RetrainingPipeline:
    async def trigger_retraining(self, model_id):
        """
        Automatically retrain model with new data
        """
        # 1. Get model config
        model_config = await postgresql.query("""
            SELECT * FROM ml_registry.models WHERE model_id = $1
        """, model_id)

        # 2. Query new training data (last 2 years)
        new_data = await clickhouse.query(f"""
            SELECT * FROM ml_features
            WHERE tenant_id = '{model_config.tenant_id}'
              AND symbol = '{model_config.target_symbol}'
              AND timeframe = '{model_config.target_timeframe}'
              AND timestamp >= NOW() - INTERVAL 730 DAY
              AND data_quality_score > 0.9
            ORDER BY timestamp
        """)

        # 3. Train new model version
        new_version = self.increment_version(model_config.version)

        trainer = ModelTrainer()
        new_model, metrics = await trainer.train_model(
            config={
                'tenant_id': model_config.tenant_id,
                'symbol': model_config.target_symbol,
                'timeframe': model_config.target_timeframe,
                'architecture': model_config.architecture,
                'hyperparameters': model_config.hyperparameters,
                'features': model_config.features_used,
                'version': new_version
            }
        )

        # 4. A/B test: Deploy with 10% traffic
        await self.deploy_canary(
            model_id=new_model.model_id,
            traffic_percentage=10
        )

        # 5. Monitor for 48 hours
        await asyncio.sleep(48 * 3600)

        # 6. Compare performance
        comparison = await self.compare_models(
            old_model_id=model_id,
            new_model_id=new_model.model_id,
            time_window='48 hours'
        )

        # 7. Promote or rollback
        if comparison.new_model_better:
            await self.promote_to_production(new_model.model_id)
            await self.archive_model(model_id)
        else:
            await self.rollback_deployment(new_model.model_id)
```

---

## 8. Multi-Tenant Isolation Strategy

### 8.1 Data Isolation

**ClickHouse (ml_features):**
- Partitioned by `tenant_id`
- All queries MUST include `WHERE tenant_id = ?`
- Application-level enforcement

**PostgreSQL (ml_registry):**
- Row-Level Security (RLS) policies
- `SET app.current_tenant_id = 'tenant_001'` before queries
- Automatic filtering via RLS

**TimescaleDB (ml_predictions, trade_results):**
- Hypertable partitioning by `tenant_id`
- RLS policies enabled
- Multi-dimensional partitioning (time + tenant)

**Weaviate (patterns):**
- All searches include `tenantId` filter
- Application-level enforcement
- Optional: Use Weaviate multi-tenancy feature (separate shards)

### 8.2 Model Isolation

**Shared Models (Platform-provided):**
- `user_id = NULL` in models table
- Available to all users in tenant
- Example: EUR/USD baseline model

**User-Specific Models:**
- `user_id = 'user_123'`
- Private to individual user
- Fine-tuned on user's trading data

**Model Access Control:**
```sql
-- Can user access model?
SELECT * FROM ml_registry.models
WHERE (tenant_id = 'tenant_001' AND user_id IS NULL)  -- Shared
   OR (tenant_id = 'tenant_001' AND user_id = 'user_123')  -- Private
```

### 8.3 Resource Quotas

**Per-Tenant Limits:**
- Max models: 10 (free tier), 100 (premium)
- Max predictions per day: 10,000 (free), unlimited (premium)
- Training compute hours per month: 10h (free), 100h (premium)
- Storage quota: 10GB (free), 1TB (premium)

**Enforcement:**
- API Gateway rate limiting
- Database triggers for quota checks
- Background job for usage tracking

---

## 9. Performance Optimization

### 9.1 Latency Targets

| Operation | Target Latency | Strategy |
|-----------|----------------|----------|
| Feature computation | < 50ms | Optimized TA-Lib, vectorized ops |
| Embedding generation | < 20ms | GPU inference, batching |
| ML prediction | < 100ms | Model optimization (ONNX, TorchScript) |
| Weaviate similarity search | < 50ms | HNSW index, pre-filtered queries |
| **Total prediction latency** | **< 200ms** | End-to-end optimization |

### 9.2 Caching Strategy

**DragonflyDB (Redis-compatible cache):**

```python
# Cache hot features
cache_key = f"features:{tenant_id}:{symbol}:{timeframe}:latest"
cached_features = dragonfly.get(cache_key)

if not cached_features:
    features = compute_features(market_data)
    dragonfly.setex(cache_key, 60, features)  # 60 second TTL

# Cache model predictions
pred_cache_key = f"prediction:{tenant_id}:{symbol}:{model_id}:{timestamp_bucket}"
cached_prediction = dragonfly.get(pred_cache_key)

# Cache pattern embeddings
pattern_cache_key = f"patterns:{tenant_id}:{symbol}:top10"
cached_patterns = dragonfly.get(pattern_cache_key)
```

**Cache Invalidation:**
- Feature cache: 60 seconds (real-time data)
- Pattern cache: 5 minutes (patterns don't change frequently)
- Model metadata: 1 hour (models rarely updated)

### 9.3 Database Query Optimization

**ClickHouse:**
- Pre-compute materialized views (`latest_features`, `feature_stats`)
- Use `PREWHERE` for partition pruning
- Optimize `ORDER BY` for common query patterns

**TimescaleDB:**
- Continuous aggregates for hourly/daily rollups
- Hypertable compression for old data
- Parallel queries with multiple workers

**Weaviate:**
- Use `limit` parameter to reduce results
- Pre-filter with `where` before vector search
- Enable Product Quantization (PQ) for large datasets

### 9.4 Model Optimization

**Model Compression:**
- Quantization: FP32 → INT8 (4x smaller, minimal accuracy loss)
- Pruning: Remove low-importance weights
- Knowledge distillation: Train smaller model from larger

**Inference Optimization:**
- ONNX Runtime: 2-3x faster inference
- TorchScript: JIT compilation for PyTorch
- Batching: Process multiple predictions together

---

## 10. Monitoring & Observability

### 10.1 Key Metrics

**Model Performance:**
- Accuracy, Precision, Recall, F1-score
- Win rate, Sharpe ratio, Max drawdown
- Prediction latency (P50, P95, P99)
- Calibration error

**System Health:**
- Feature computation latency
- Database query latency
- Weaviate search latency
- Cache hit rate

**Business Metrics:**
- Total predictions per day
- Signals generated per day
- Trades executed
- Average PnL per trade

### 10.2 Alerting Rules

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| Model accuracy drop | < 10% baseline | Critical | Trigger retraining |
| High prediction latency | P95 > 500ms | Warning | Scale inference service |
| Data quality drop | < 80% quality score | Warning | Investigate data pipeline |
| Pattern match rate low | < 5% similarity | Info | Retrain embedding model |
| Cache hit rate low | < 70% | Info | Review cache strategy |

### 10.3 Dashboards

**Real-Time Dashboard:**
- Live predictions count
- Current model accuracy (rolling 1h)
- Active trading signals
- System latency graphs

**Analytics Dashboard:**
- Model leaderboard (accuracy, Sharpe ratio)
- Feature importance rankings
- Pattern matching effectiveness
- Trade performance by model

---

## 11. Security & Compliance

### 11.1 Data Security

**Encryption:**
- At rest: Database encryption (PostgreSQL, ClickHouse)
- In transit: TLS for all connections
- Model storage: S3 server-side encryption

**Access Control:**
- API authentication (JWT tokens)
- Database user roles (read-only, service, admin)
- Row-Level Security for multi-tenancy

### 11.2 Model Security

**Model Theft Prevention:**
- Models stored in private S3 buckets
- API rate limiting prevents model extraction
- Watermarking for proprietary models

**Adversarial Attack Prevention:**
- Input validation (feature range checks)
- Anomaly detection on prediction requests
- Rate limiting per user/tenant

### 11.3 Compliance

**Data Retention:**
- GDPR: Support user data deletion
- Feature data: 10 years (configurable)
- Predictions: 90 days (configurable)
- Trade results: 3 years (regulatory requirement)

**Audit Logs:**
- All model deployments logged
- Training jobs tracked with metadata
- Prediction requests logged (sampling)

---

## 12. Deployment Architecture

### 12.1 Service Components

```yaml
services:
  # Feature Engineering Service
  feature-engineer:
    image: suho/feature-engineer:latest
    replicas: 2
    resources:
      cpu: "2"
      memory: "4Gi"
    environment:
      - CLICKHOUSE_URL=clickhouse:8123
      - NATS_URL=nats:4222

  # ML Training Service (GPU)
  model-trainer:
    image: suho/model-trainer:latest
    replicas: 1
    resources:
      cpu: "4"
      memory: "16Gi"
      gpu: "1"  # NVIDIA GPU
    environment:
      - CLICKHOUSE_URL=clickhouse:8123
      - POSTGRES_URL=postgresql:5432
      - S3_BUCKET=suho-models

  # Inference Service (CPU)
  inference-service:
    image: suho/inference-service:latest
    replicas: 4
    resources:
      cpu: "2"
      memory: "8Gi"
    environment:
      - POSTGRES_URL=postgresql:5432
      - TIMESCALEDB_URL=postgresql:5432
      - WEAVIATE_URL=weaviate:8080
      - DRAGONFLY_URL=dragonflydb:6379
      - S3_BUCKET=suho-models

  # Pattern Matcher Service
  pattern-matcher:
    image: suho/pattern-matcher:latest
    replicas: 2
    resources:
      cpu: "1"
      memory: "4Gi"
    environment:
      - WEAVIATE_URL=weaviate:8080

  # Feedback Loop Service
  feedback-loop:
    image: suho/feedback-loop:latest
    replicas: 1
    resources:
      cpu: "1"
      memory: "2Gi"
    environment:
      - TIMESCALEDB_URL=postgresql:5432
      - WEAVIATE_URL=weaviate:8080
      - NATS_URL=nats:4222
```

### 12.2 Scaling Strategy

**Horizontal Scaling:**
- Inference Service: Auto-scale based on prediction queue depth
- Feature Engineer: Scale with data ingestion rate
- Pattern Matcher: Scale with Weaviate query load

**Vertical Scaling:**
- Training Service: GPU instances for model training
- ClickHouse: Scale storage for historical data
- Weaviate: Scale memory for vector index

---

## 13. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-4)
- ✅ Set up ClickHouse schema (ml_features)
- ✅ Set up PostgreSQL schema (ml_registry)
- ✅ Set up TimescaleDB schema (ml_predictions, trade_results)
- ✅ Set up Weaviate schema (TradingPattern)
- Implement feature engineering service
- Create baseline models (XGBoost, Random Forest)

### Phase 2: ML Pipeline (Weeks 5-8)
- Implement model training service
- Build inference service
- Create pattern matching service
- Deploy first models to production
- Set up monitoring dashboards

### Phase 3: Advanced Features (Weeks 9-12)
- Implement LSTM/Transformer models
- Build embedding model for patterns
- Create feedback loop service
- Implement automated retraining
- A/B testing framework

### Phase 4: Optimization (Weeks 13-16)
- Model optimization (ONNX, quantization)
- Caching strategy implementation
- Performance tuning
- Load testing and scaling
- Security hardening

---

## 14. Success Metrics

### Model Performance
- **Accuracy**: > 60% direction prediction
- **Sharpe Ratio**: > 1.5 (trading performance)
- **Win Rate**: > 55%
- **Max Drawdown**: < 15%

### System Performance
- **Prediction Latency**: P95 < 200ms
- **Feature Computation**: < 50ms
- **Uptime**: 99.9%
- **Data Quality**: > 95% high-quality features

### Business Metrics
- **User Satisfaction**: > 4.5/5 rating
- **Model Adoption**: > 70% users using ML predictions
- **Cost Efficiency**: < $0.001 per prediction

---

## 15. Appendix

### A. Technology Stack Summary

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
| **Model Storage** | S3 / MinIO | Model binaries |
| **Orchestration** | Docker Compose / Kubernetes | Service deployment |

### B. File Locations

- **Schemas**: `/mnt/g/khoirul/aitrading/project3/backend/03-ml-pipeline/schemas/`
  - `01_clickhouse_ml_features.sql`
  - `02_postgresql_model_registry.sql`
  - `03_timescaledb_predictions.sql`
  - `04_weaviate_pattern_vectors.json`

- **Source Code**: `/mnt/g/khoirul/aitrading/project3/backend/03-ml-pipeline/src/`
  - `feature_engineer.py`
  - `model_trainer.py`
  - `inference_service.py`
  - `pattern_matcher.py`
  - `feedback_loop.py`

---

**Document Version**: 1.0.0
**Last Updated**: 2025-10-05
**Author**: ML Engineering Team
**Status**: Production Ready
