# 🏗️ Service Architecture & Flow - Complete Reference

> **Version**: 1.0.0
> **Last Updated**: 2025-10-17
> **Status**: Complete - Master Reference Document
> **Purpose**: Definisi lengkap service architecture untuk mencegah development keluar jalur

---

## 📋 Table of Contents

1. [Service Tree Overview](#service-tree-overview)
2. [Complete Service List](#complete-service-list)
3. [Data Flow Pipeline](#data-flow-pipeline)
4. [Service Details by Phase](#service-details-by-phase)
5. [Service Dependencies](#service-dependencies)
6. [Table Database Mapping](#table-database-mapping)

---

## 🌳 Service Tree Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI TRADING SYSTEM                            │
│                    (Complete Service Tree)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  DATA PHASE   │   │ TRAINING PHASE│   │ TRADING PHASE │
│   (Phase 1)   │   │   (Phase 2)   │   │   (Phase 3)   │
└───────┬───────┘   └───────┬───────┘   └───────┬───────┘
        │                   │                   │
        ▼                   ▼                   ▼

┌─────────────────────────────────────────────────────────────────┐
│ 00-data-ingestion/                                              │
│   ├─ polygon-live-collector         (Live ticks streaming)     │
│   ├─ polygon-historical-downloader  (Historical data batch)    │
│   ├─ dukascopy-historical-downloader (Backup historical)       │
│   └─ external-data-collector        (Economic calendar, FRED)  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 01-core-infrastructure/                                         │
│   └─ central-hub                    (Service coordination)      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 02-data-processing/                                             │
│   ├─ tick-aggregator                (Ticks → Candles)          │
│   └─ feature-engineering-service    (Candles → ML Features)    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────┴─────────────────────┐
        │                                           │
        ▼                                           ▼
┌─────────────────────────────┐   ┌─────────────────────────────┐
│ 03-ml-training/             │   │ 04-trading-execution/       │
│   ├─ supervised-training    │   │   ├─ inference-service      │
│   └─ finrl-training         │   │   ├─ execution-service      │
└─────────────────────────────┘   │   ├─ risk-management        │
                                  │   └─ performance-monitoring │
                                  └─────────────────────────────┘
                                              ↓
                              ┌───────────────┴───────────────┐
                              │                               │
                              ▼                               ▼
                  ┌───────────────────┐       ┌───────────────────┐
                  │ 05-broker-        │       │ 06-backtesting/   │
                  │ integration/      │       │   └─ backtesting- │
                  │   └─ mt5-connector│       │     service       │
                  └───────────────────┘       └───────────────────┘
                              ↓
                  ┌───────────────────────────┐
                  │ 07-business-platform/     │
                  │   ├─ analytics-service    │
                  │   └─ notification-hub     │
                  └───────────────────────────┘
```

---

## 📊 Complete Service List

| # | Service Name | Folder | Status | Priority |
|---|-------------|--------|--------|----------|
| 1 | polygon-live-collector | 00-data-ingestion | ✅ Active | P0 |
| 2 | polygon-historical-downloader | 00-data-ingestion | ✅ Active | P0 |
| 3 | dukascopy-historical-downloader | 00-data-ingestion | ✅ Active | P1 |
| 4 | external-data-collector | 00-data-ingestion | ✅ Active | P1 |
| 5 | central-hub | 01-core-infrastructure | ✅ Active | P0 |
| 6 | tick-aggregator | 02-data-processing | ✅ Active | P0 |
| 7 | feature-engineering-service | 02-data-processing | ✅ Active | P0 |
| 8 | supervised-training-service | 03-ml-training | ⚠️ Placeholder | P1 |
| 9 | finrl-training-service | 03-ml-training | ⚠️ To Build | P1 |
| 10 | inference-service | 04-trading-execution | ⚠️ Placeholder | P2 |
| 11 | execution-service | 04-trading-execution | ⚠️ Placeholder | P2 |
| 12 | risk-management | 04-trading-execution | ⚠️ Placeholder | P2 |
| 13 | performance-monitoring | 04-trading-execution | ⚠️ To Build | P2 |
| 14 | mt5-connector | 05-broker-integration | ⚠️ Placeholder | P3 |
| 15 | backtesting-service | 06-backtesting | ⚠️ Placeholder | P2 |
| 16 | analytics-service | 07-business-platform | ⚠️ Placeholder | P3 |
| 17 | notification-hub | 07-business-platform | ⚠️ Placeholder | P3 |

**Legend:**
- ✅ Active: Service running in production
- ⚠️ Placeholder: Service exists but not implemented
- ⚠️ To Build: Service needs to be created

---

## 🔄 Data Flow Pipeline

### **Phase 1: Data Acquisition & Processing (✅ COMPLETE)**

```
┌─────────────────────────────────────────────────────────────────┐
│                    LIVE DATA FLOW                               │
└─────────────────────────────────────────────────────────────────┘

Polygon API (WebSocket)
    ↓ (Live ticks)
polygon-live-collector
    ↓ (Store ticks)
TimescaleDB.market_ticks
    ↓ (Real-time aggregation)
tick-aggregator
    ↓ (OHLCV candles)
ClickHouse.aggregates
    ↓ (Feature calculation)
feature-engineering-service
    ↓ (110 ML features)
ClickHouse.ml_features (live, no targets)
    ↓
READY FOR INFERENCE


┌─────────────────────────────────────────────────────────────────┐
│                 HISTORICAL DATA FLOW                            │
└─────────────────────────────────────────────────────────────────┘

Polygon API (REST) / Dukascopy
    ↓ (Historical ticks)
polygon-historical-downloader
    ↓ (Store ticks)
TimescaleDB.market_ticks
    ↓ (Batch aggregation)
tick-aggregator
    ↓ (OHLCV candles)
ClickHouse.aggregates
    ↓ (Feature calculation + targets)
feature-engineering-service
    ↓ (110 ML features + 5 targets)
ClickHouse.ml_features (historical, with targets)
    ↓
READY FOR TRAINING


┌─────────────────────────────────────────────────────────────────┐
│                EXTERNAL DATA FLOW                               │
└─────────────────────────────────────────────────────────────────┘

Economic Calendar API + FRED + Commodities
    ↓
external-data-collector
    ↓
ClickHouse.external_economic_calendar
ClickHouse.external_fred_indicators
ClickHouse.external_commodity_prices
    ↓
feature-engineering-service (JOIN for features)
```

---

### **Phase 2: Model Training (⚠️ TO IMPLEMENT)**

```
┌─────────────────────────────────────────────────────────────────┐
│              SUPERVISED LEARNING FLOW                           │
└─────────────────────────────────────────────────────────────────┘

ClickHouse.ml_features (historical + targets)
    ↓ (Query training data)
supervised-training-service
    ├─ Train ML models (XGBoost, LightGBM, CatBoost)
    ├─ Hyperparameter tuning
    ├─ Cross-validation
    └─ Model evaluation
    ↓ (Save models & metrics)
ClickHouse.training_runs
ClickHouse.model_checkpoints
ClickHouse.training_metrics
    ↓
TRAINED MODEL READY FOR INFERENCE


┌─────────────────────────────────────────────────────────────────┐
│           REINFORCEMENT LEARNING FLOW (FinRL)                   │
└─────────────────────────────────────────────────────────────────┘

ClickHouse.ml_features (historical, no targets needed)
    ↓ (Create RL environment)
finrl-training-service
    ├─ Define reward function (Sharpe, profit, risk)
    ├─ Train RL agent (PPO, A2C, DDPG, SAC, TD3)
    ├─ Episode training (explore → exploit)
    └─ Agent evaluation
    ↓ (Save agents & metrics)
ClickHouse.agent_training_runs
ClickHouse.agent_checkpoints
ClickHouse.reward_history
    ↓
TRAINED AGENT READY FOR TRADING
```

---

### **Phase 3: Live Trading (⚠️ TO IMPLEMENT)**

```
┌─────────────────────────────────────────────────────────────────┐
│                  TRADING EXECUTION FLOW                         │
└─────────────────────────────────────────────────────────────────┘

ClickHouse.ml_features (live, latest candle)
    ↓ (Load trained model/agent)
inference-service
    ├─ Model prediction (supervised)
    │  OR
    ├─ Agent decision (RL)
    └─ Generate signals (buy/sell/hold)
    ↓
ClickHouse.trading_signals
    ↓ (Risk checks)
risk-management
    ├─ Position sizing
    ├─ Stop-loss calculation
    ├─ Portfolio limits
    └─ Risk approval
    ↓
execution-service
    ├─ Order creation
    ├─ Send to broker
    └─ Execution tracking
    ↓
mt5-connector (via broker API)
    ↓ (Order fills)
execution-service
    ↓ (Update positions)
ClickHouse.positions
ClickHouse.orders
ClickHouse.executions
    ↓
performance-monitoring
    ├─ Calculate metrics (Sharpe, drawdown, win rate)
    ├─ Compare with benchmark
    └─ Generate alerts
    ↓
ClickHouse.performance_metrics
ClickHouse.risk_events
    ↓ (Optional: Continuous learning)
finrl-training-service (update agent with real results)
```

---

## 🎯 Service Details by Phase

### **PHASE 1: Data Acquisition & Processing** ✅ COMPLETE

#### **Service 1: polygon-live-collector**
**Folder**: `00-data-ingestion/polygon-live-collector`
**Status**: ✅ Active

**Purpose**: Real-time streaming of live market data dari Polygon WebSocket API

**Functions**:
- Connect to Polygon WebSocket (forex & crypto)
- Subscribe to tick data (bid/ask/spread)
- Stream live ticks ke TimescaleDB
- Handle reconnection & backfill gaps

**Input**: Polygon WebSocket API
**Output**: `TimescaleDB.market_ticks` (live ticks)

**Tables**: `table_database_input.md`

**Critical Features**:
- Sub-second latency
- Automatic reconnection
- Gap detection & backfill
- Multi-symbol support (14 pairs)

---

#### **Service 2: polygon-historical-downloader**
**Folder**: `00-data-ingestion/polygon-historical-downloader`
**Status**: ✅ Active

**Purpose**: Batch download historical tick data untuk training

**Functions**:
- Download historical ticks dari Polygon REST API
- Date range: 2023-01-01 sampai sekarang
- Store ke TimescaleDB
- Progress tracking & resume capability

**Input**: Polygon REST API
**Output**: `TimescaleDB.market_ticks` (historical ticks)

**Tables**: `table_database_input.md`

**Current Status**: 2.8 years of data (2023-2025), 14 pairs

---

#### **Service 3: dukascopy-historical-downloader**
**Folder**: `00-data-ingestion/dukascopy-historical-downloader`
**Status**: ✅ Active (Backup)

**Purpose**: Alternative historical data source (redundancy)

**Functions**:
- Download dari Dukascopy API
- Convert format ke compatible structure
- Fill gaps dari Polygon data

**Input**: Dukascopy API
**Output**: `TimescaleDB.market_ticks`

**Tables**: `table_database_input.md`

---

#### **Service 4: external-data-collector**
**Folder**: `00-data-ingestion/external-data-collector`
**Status**: ✅ Active

**Purpose**: Collect external data untuk ML features

**Functions**:
- Economic calendar (news events)
- FRED indicators (GDP, unemployment, CPI, interest rates)
- Commodity prices (gold, oil)
- Store ke ClickHouse

**Input**:
- Economic Calendar API
- FRED API
- Yahoo Finance (commodities)

**Output**:
- `ClickHouse.external_economic_calendar`
- `ClickHouse.external_fred_indicators`
- `ClickHouse.external_commodity_prices`

**Tables**: `table_database_input.md`

**Update Frequency**:
- Economic calendar: Daily
- FRED: Weekly
- Commodities: Real-time (with cache)

---

#### **Service 5: central-hub**
**Folder**: `01-core-infrastructure/central-hub`
**Status**: ✅ Active

**Purpose**: Service coordination, health monitoring, message routing

**Functions**:
- Service discovery & registration
- Health check aggregation
- Message routing (Kafka/NATS)
- Configuration management
- Metrics collection

**Input**: All services (health checks, events)
**Output**:
- Service registry
- Health metrics
- Coordination signals

**Tables**: Internal coordination tables (PostgreSQL)

**Critical Role**: Orchestration layer untuk semua services

---

#### **Service 6: tick-aggregator**
**Folder**: `02-data-processing/tick-aggregator`
**Status**: ✅ Active

**Purpose**: Aggregate ticks menjadi OHLCV candles

**Functions**:
- Real-time aggregation (live ticks → candles)
- Batch aggregation (historical ticks → candles)
- Multi-timeframe support (5m, 15m, 30m, 1h, 4h, 1d, 1w)
- Calculate spreads, volatility, tick counts

**Input**: `TimescaleDB.market_ticks`
**Output**: `ClickHouse.aggregates`

**Tables**: `table_database_input.md`

**Processing**:
- Live: Real-time streaming
- Historical: Batch processing (parallel)
- Performance: 10,000+ candles/second

---

#### **Service 7: feature-engineering-service**
**Folder**: `02-data-processing/feature-engineering-service`
**Status**: ✅ Active

**Purpose**: Calculate 110 ML features dari candles + external data

**Functions**:
- Technical indicators (RSI, MACD, Bollinger, Stochastic, etc)
- Fibonacci retracement levels
- Market session features (London, NY, Tokyo overlap)
- Calendar features (day of week, month boundaries)
- Lagged features (trend detection)
- Rolling statistics (support/resistance)
- Multi-timeframe features (higher TF context)
- External data join (economic events, FRED, commodities)
- Target calculation (for supervised learning - historical only)

**Input**:
- `ClickHouse.aggregates` (OHLCV)
- `ClickHouse.external_*` tables

**Output**: `ClickHouse.ml_features` (110 derived features)

**Tables**: `table_database_process.md` (v2.0.0)

**Feature Breakdown**:
- Phase 1 (MVP): 97 features
- Phase 2: +8 features (momentum + quality)
- Phase 3: +5 features (interactions)

**Critical Notes**:
- Historical: Calculate WITH targets
- Live: Calculate WITHOUT targets
- Performance: < 5 seconds per candle (110 features)

---

### **PHASE 2: Model Training** ⚠️ TO IMPLEMENT

#### **Service 8: supervised-training-service**
**Folder**: `03-ml-training/supervised-training-service`
**Status**: ⚠️ Placeholder (To Implement)

**Purpose**: Train supervised ML models (classification & regression)

**Functions**:
- Data preparation (train/validation/test split)
- Feature selection & engineering
- Model training:
  - XGBoost (gradient boosting)
  - LightGBM (fast gradient boosting)
  - CatBoost (categorical features)
  - Random Forest
  - Neural Networks (optional)
- Hyperparameter tuning (Optuna/GridSearch)
- Cross-validation
- Model evaluation (accuracy, precision, recall, F1, AUC)
- Model versioning & registry

**Input**: `ClickHouse.ml_features` (historical + targets)
**Output**:
- `ClickHouse.training_runs`
- `ClickHouse.model_checkpoints`
- `ClickHouse.training_metrics`
- `ClickHouse.hyperparameters_log`

**Tables**: `table_database_training.md` (To Design)

**Stack**: Python, Scikit-learn, XGBoost, LightGBM, CatBoost, Optuna

**Training Strategy**:
- Walk-forward validation
- Time-series split
- Look-ahead bias prevention
- Regularization to prevent overfitting

---

#### **Service 9: finrl-training-service**
**Folder**: `03-ml-training/finrl-training-service`
**Status**: ⚠️ To Build

**Purpose**: Train Reinforcement Learning agent dengan FinRL framework

**Functions**:
- Trading environment creation (FinRL)
- State space definition (110 features)
- Action space definition (buy/sell/hold + position size)
- Reward function design:
  - Sharpe ratio
  - Profit/loss
  - Risk-adjusted returns
  - Drawdown penalty
- RL algorithm training:
  - PPO (Proximal Policy Optimization)
  - A2C (Advantage Actor-Critic)
  - DDPG (Deep Deterministic Policy Gradient)
  - SAC (Soft Actor-Critic)
  - TD3 (Twin Delayed DDPG)
- Episode training (explore → exploit)
- Agent evaluation & comparison
- Continuous learning (update with live results)

**Input**: `ClickHouse.ml_features` (historical, NO targets needed)
**Output**:
- `ClickHouse.agent_training_runs`
- `ClickHouse.agent_checkpoints`
- `ClickHouse.reward_history`
- `ClickHouse.rl_hyperparameters`

**Tables**: `table_database_training.md` (To Design)

**Stack**: Python, FinRL, Stable-Baselines3, PyTorch, Gym

**Key Differences from Supervised**:
- NO target variables needed
- Learns from rewards (profit/loss)
- Sequential decision making
- Continuous learning capability

---

### **PHASE 3: Live Trading** ⚠️ TO IMPLEMENT

#### **Service 10: inference-service**
**Folder**: `04-trading-execution/inference-service`
**Status**: ⚠️ Placeholder (To Implement)

**Purpose**: Real-time prediction menggunakan trained models/agents

**Functions**:
- Model/agent loading & caching
- Real-time feature fetching (latest candle)
- Prediction generation:
  - Supervised model: Probability scores (buy/sell/hold)
  - RL agent: Action selection (policy output)
- Signal generation with confidence scores
- Multi-model ensemble (optional)
- Prediction logging & monitoring

**Input**:
- `ClickHouse.ml_features` (live, latest candle)
- Trained models/agents (from training phase)

**Output**:
- `ClickHouse.trading_signals`
- `ClickHouse.model_predictions`

**Tables**: `table_database_trading.md` (To Design)

**Stack**: Python, FastAPI, Model serving (ONNX/TorchServe optional)

**Performance Requirements**:
- Latency: < 100ms per prediction
- Real-time streaming
- Model hot-swapping (A/B testing)

---

#### **Service 11: execution-service**
**Folder**: `04-trading-execution/execution-service`
**Status**: ⚠️ Placeholder (To Implement)

**Purpose**: Execute trading orders ke broker

**Functions**:
- Order creation & validation
- Order routing to broker (MT5)
- Execution tracking (fills, partial fills)
- Slippage monitoring
- Commission tracking
- Position management (open/close)
- Order history & audit trail

**Input**:
- `ClickHouse.trading_signals` (approved by risk management)

**Output**:
- `ClickHouse.orders`
- `ClickHouse.executions`
- `ClickHouse.positions`

**Tables**: `table_database_trading.md` (To Design)

**Stack**: Python, MT5 API, asyncio

**Order Types**:
- Market orders
- Limit orders
- Stop-loss orders
- Take-profit orders

**Critical Features**:
- Idempotent order submission
- Duplicate detection
- Automatic retry on failures
- Order state machine

---

#### **Service 12: risk-management**
**Folder**: `04-trading-execution/risk-management`
**Status**: ⚠️ Placeholder (To Implement)

**Purpose**: Risk checks sebelum order execution

**Functions**:
- Position sizing (Kelly Criterion, Fixed Fractional)
- Stop-loss calculation (ATR-based, percentage-based)
- Take-profit calculation
- Portfolio limits:
  - Max position size per symbol
  - Max total exposure
  - Max daily loss
  - Max drawdown
- Risk approval/rejection
- Risk event logging

**Input**:
- `ClickHouse.trading_signals`
- `ClickHouse.positions` (current positions)
- `ClickHouse.portfolio_value`

**Output**:
- Approved/rejected signals
- `ClickHouse.risk_events`

**Tables**: `table_database_trading.md` (To Design)

**Stack**: Python

**Risk Metrics**:
- R-multiple (risk/reward ratio)
- Position correlation
- Portfolio heat
- Expectancy calculation

---

#### **Service 13: performance-monitoring**
**Folder**: `04-trading-execution/performance-monitoring`
**Status**: ⚠️ To Build

**Purpose**: Track trading performance & calculate metrics

**Functions**:
- Performance metrics calculation:
  - Sharpe ratio
  - Sortino ratio
  - Maximum drawdown
  - Win rate
  - Profit factor
  - Expectancy
  - Average R-multiple
- Benchmark comparison (buy & hold)
- Equity curve generation
- Trade analysis (winners/losers breakdown)
- Risk-adjusted returns
- Alert generation (performance degradation)

**Input**:
- `ClickHouse.positions`
- `ClickHouse.orders`
- `ClickHouse.executions`
- `ClickHouse.portfolio_value`

**Output**:
- `ClickHouse.performance_metrics`
- `ClickHouse.trade_analysis`

**Tables**: `table_database_trading.md` (To Design)

**Stack**: Python, Pandas, Matplotlib/Plotly

**Reporting Frequency**:
- Real-time: Equity curve
- Daily: Performance summary
- Weekly: Detailed analysis
- Monthly: Comprehensive report

---

### **PHASE 4: Supporting Services** ⚠️ FUTURE

#### **Service 14: mt5-connector**
**Folder**: `05-broker-integration/mt5-connector`
**Status**: ⚠️ Placeholder (To Implement)

**Purpose**: Integration dengan MetaTrader 5 broker

**Functions**:
- MT5 API connection
- Account authentication
- Order submission
- Position queries
- Balance/equity monitoring
- Trade history sync

**Input**: Orders from execution-service
**Output**: Fill confirmations

**Tables**: MT5-specific tables (to design)

**Stack**: Python, MetaTrader5 library

---

#### **Service 15: backtesting-service**
**Folder**: `06-backtesting/backtesting-service`
**Status**: ⚠️ Placeholder (To Implement)

**Purpose**: Historical backtesting untuk model/strategy validation

**Functions**:
- Historical simulation
- Walk-forward testing
- Monte Carlo simulation
- Performance analysis
- Parameter optimization

**Input**:
- `ClickHouse.ml_features` (historical)
- Trained models/agents

**Output**: Backtest reports & metrics

**Tables**: Separate backtest tables

**Stack**: Python, Backtrader/Zipline/VectorBT

---

#### **Service 16: analytics-service**
**Folder**: `07-business-platform/analytics-service`
**Status**: ⚠️ Placeholder (Future)

**Purpose**: Business analytics & dashboards

**Functions**:
- Dashboard generation
- KPI tracking
- Data visualization
- Report generation

**Input**: All database tables
**Output**: Dashboards & reports

**Stack**: Python, FastAPI, React/Vue

---

#### **Service 17: notification-hub**
**Folder**: `07-business-platform/notification-hub`
**Status**: ⚠️ Placeholder (Future)

**Purpose**: Alert & notification system

**Functions**:
- Email notifications
- Telegram/Discord alerts
- SMS alerts (critical only)
- Event-driven notifications

**Input**: Events from all services
**Output**: Notifications

**Stack**: Python, SMTP, Telegram Bot API

---

## 🔗 Service Dependencies

### **Dependency Graph**

```
Legend:
→ Data flow
⇢ Service dependency
⊗ Critical dependency (system won't work without it)

┌─────────────────────────────────────────────────────────────────┐
│                   DEPENDENCY CHAIN                              │
└─────────────────────────────────────────────────────────────────┘

External APIs
    ↓
Data Ingestion Services ⊗
    ↓
TimescaleDB (ticks) ⊗
    ↓
tick-aggregator ⊗
    ↓
ClickHouse (aggregates) ⊗
    ↓
feature-engineering-service ⊗
    ↓
ClickHouse (ml_features) ⊗
    ↓
    ├─→ supervised-training → model_checkpoints
    │                              ↓
    └─→ finrl-training → agent_checkpoints
                                   ↓
                            inference-service
                                   ↓
                            trading_signals
                                   ↓
                            risk-management
                                   ↓
                            execution-service
                                   ↓
                            mt5-connector
                                   ↓
                            broker (live trading)
```

### **Critical Path (Must Work)**

1. ⊗ **External APIs** (Polygon, Economic Calendar, FRED)
2. ⊗ **Data Collectors** (Live + Historical)
3. ⊗ **TimescaleDB** (Tick storage)
4. ⊗ **tick-aggregator** (Candle generation)
5. ⊗ **ClickHouse** (Aggregates storage)
6. ⊗ **feature-engineering-service** (Feature calculation)
7. ⊗ **ClickHouse** (ML features storage)

**Result**: Training data ready!

---

## 📊 Table Database Mapping

### **File 1: `table_database_input.md`**
**Status**: ✅ Complete (v1.8.0)

**Services**:
- polygon-live-collector
- polygon-historical-downloader
- dukascopy-historical-downloader
- external-data-collector
- tick-aggregator

**Tables**:
- `TimescaleDB.market_ticks` (raw ticks)
- `ClickHouse.aggregates` (OHLCV candles)
- `ClickHouse.external_economic_calendar`
- `ClickHouse.external_fred_indicators`
- `ClickHouse.external_commodity_prices`

---

### **File 2: `table_database_process.md`**
**Status**: ✅ Complete (v2.0.0)

**Services**:
- feature-engineering-service

**Tables**:
- `ClickHouse.ml_features` (110 derived features)

**Input**: aggregates + external_* tables
**Output**: ml_features (110 columns)

**Key Decision**: ml_features stores ONLY derived features (NO raw OHLC)

---

### **File 3: `table_database_training.md`**
**Status**: ⚠️ To Design

**Services**:
- supervised-training-service
- finrl-training-service

**Expected Tables**:
- `training_runs` (experiment tracking)
- `model_checkpoints` (saved models)
- `training_metrics` (accuracy, loss, etc)
- `hyperparameters_log` (tuning history)
- `agent_training_runs` (RL specific)
- `agent_checkpoints` (RL agents)
- `reward_history` (RL rewards per episode)
- `rl_hyperparameters` (RL config)

**Input**: ml_features (historical)
**Output**: Trained models/agents

---

### **File 4: `table_database_trading.md`**
**Status**: ⚠️ To Design

**Services**:
- inference-service
- execution-service
- risk-management
- performance-monitoring

**Expected Tables**:
- `trading_signals` (predictions)
- `model_predictions` (raw model outputs)
- `positions` (open/closed positions)
- `orders` (order history)
- `executions` (fills & slippage)
- `portfolio_value` (equity curve)
- `performance_metrics` (Sharpe, drawdown, etc)
- `risk_events` (risk triggers)
- `trade_analysis` (individual trade breakdown)

**Input**: ml_features (live), trained models
**Output**: Trading execution & performance

---

## 🚧 Implementation Roadmap

### **✅ Phase 1: Foundation (COMPLETE)**
- Week 1-4: Data ingestion (live + historical) ✅
- Week 5-8: Tick aggregation ✅
- Week 9-12: Feature engineering (110 features) ✅
- **Status**: 82% complete, 2.8 years of data ready

---

### **⚠️ Phase 2: Model Training (CURRENT)**
- Week 13-16: Design `table_database_training.md`
- Week 17-20: Implement supervised-training-service
- Week 21-24: Implement finrl-training-service
- Week 25-28: Model evaluation & selection

---

### **⚠️ Phase 3: Live Trading (FUTURE)**
- Week 29-32: Design `table_database_trading.md`
- Week 33-36: Implement inference-service
- Week 37-40: Implement execution-service + risk-management
- Week 41-44: Implement performance-monitoring
- Week 45-48: Paper trading & validation
- Week 49-52: Live trading (small capital)

---

### **⚠️ Phase 4: Optimization (FUTURE)**
- Continuous learning (FinRL online updates)
- Multi-model ensemble
- Advanced risk management
- Automated parameter optimization

---

## ✅ Validation Checklist

Before implementation, verify:

- [ ] **Service Purpose Clear**: Setiap service punya tujuan yang jelas
- [ ] **No Overlaps**: Tidak ada duplikasi fungsi antar services
- [ ] **Clear Boundaries**: Input/output tiap service well-defined
- [ ] **Table Mapping**: Setiap service tahu table mana yang dipakai
- [ ] **Dependencies Clear**: Service dependencies teridentifikasi
- [ ] **Critical Path**: Critical services teridentifikasi (marked with ⊗)
- [ ] **Phase Separation**: Data → Training → Trading phases jelas
- [ ] **Consistency**: Naming konsisten dengan folder structure

---

## 🎯 Next Steps

1. **Review Document**: Pastikan semua services & flows sudah benar
2. **Design Training Tables**: Complete `table_database_training.md`
3. **Design Trading Tables**: Complete `table_database_trading.md`
4. **Begin Implementation**: Start with supervised-training-service

---

**This document is the MASTER REFERENCE for all development.**
**Any changes to service architecture MUST update this document first.**

**Version History**:
- v1.0.0 (2025-10-17): Initial complete service architecture documentation
