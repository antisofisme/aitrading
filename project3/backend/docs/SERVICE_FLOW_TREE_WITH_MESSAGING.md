# 🌊 Service Flow Tree with Messaging Layer

> **Version**: 1.0.0
> **Last Updated**: 2025-10-18
> **Status**: Complete - Master Flow Reference
> **Purpose**: Flow tree per-service dengan messaging layer (NATS vs Kafka) yang jelas

---

## 📋 Table of Contents

1. [Messaging Architecture Overview](#messaging-architecture-overview)
2. [Phase 1: Data Foundation](#phase-1-data-foundation)
3. [Phase 2: ML Training](#phase-2-ml-training)
4. [Phase 3: Live Trading](#phase-3-live-trading)
5. [Phase 4: Supporting Services](#phase-4-supporting-services)
6. [Messaging Summary Table](#messaging-summary-table)
7. [NATS Subject Naming Convention](#nats-subject-naming-convention)
8. [Kafka Topic Naming Convention](#kafka-topic-naming-convention)

---

## 🏗️ Messaging Architecture Overview

### **NATS (Real-time, Low-latency)**
- **Purpose**: Real-time streaming data antar services
- **Use case**: Live data flow, publish/subscribe, event notifications
- **Architecture**: NATS Cluster (3 nodes) untuk high availability
- **Pattern**: Fire-and-forget, at-most-once delivery
- **Latency**: Sub-millisecond
- **Best for**: Real-time trading signals, live ticks, immediate alerts

### **Kafka (Persistence, Replay)**
- **Purpose**: Data archiving, gap filling, replay capability
- **Use case**: Persistent storage, reprocessing, audit trail, compliance
- **Architecture**: Single broker (can scale to cluster)
- **Pattern**: At-least-once delivery, consumer groups, partitioning
- **Latency**: Low (milliseconds)
- **Best for**: Historical data, audit logs, replayable streams

### **When to Use What?**
- **Both (NATS + Kafka)**: Critical data that needs real-time + persistence
  - Live ticks (real-time trading + historical backfill)
  - Aggregated candles (real-time analysis + historical storage)
  - Trading signals (immediate execution + audit trail)

- **NATS Only**: Real-time events without persistence needs
  - Feature calculations (derived from persisted candles)
  - Performance alerts (real-time notifications)
  - Training status (ephemeral events)

- **Kafka Only**: Batch processing with replay needs
  - Rare (most batch processes write directly to ClickHouse)

- **Neither**: Batch services that write directly to database
  - Historical downloaders (polygon-historical, dukascopy-historical)
  - Backtesting engine (reads historical, writes results)

---

## 🔄 PHASE 1: Data Foundation

### **SERVICE 1: polygon-live-collector**

```
┌─────────────────────────────────────────────────────────────┐
│ SERVICE 1: polygon-live-collector                           │
├─────────────────────────────────────────────────────────────┤
│ INPUT:  Polygon.io WebSocket (real-time ticks)             │
│ PROCESS: Collect, normalize, validate ticks                │
│                                                             │
│ OUTPUT:                                                     │
│   ├─ TimescaleDB.live_ticks (3-day retention)             │
│   ├─ NATS: ticks.{symbol} (real-time streaming) ✅         │
│   └─ Kafka: tick_archive (persistence) ✅                  │
│                                                             │
│ MESSAGING:                                                  │
│   - NATS → Real-time subscribers (data-bridge)             │
│   - Kafka → Archive & gap filling                          │
│                                                             │
│ NATS SUBJECTS:                                              │
│   - ticks.EURUSD                                            │
│   - ticks.XAUUSD                                            │
│   - ticks.GBPUSD                                            │
│   (... for all 14 pairs)                                    │
│                                                             │
│ KAFKA TOPICS:                                               │
│   - tick_archive (all symbols)                             │
└─────────────────────────────────────────────────────────────┘
```

---

### **SERVICE 2: polygon-historical-downloader**

```
┌─────────────────────────────────────────────────────────────┐
│ SERVICE 2: polygon-historical-downloader                    │
├─────────────────────────────────────────────────────────────┤
│ INPUT:  Polygon.io REST API (gap filling)                  │
│ PROCESS: Detect gaps, download, backfill                   │
│                                                             │
│ OUTPUT:                                                     │
│   ├─ ClickHouse.live_aggregates (direct write)            │
│   └─ NO messaging (batch processing only)                 │
│                                                             │
│ MESSAGING: None (batch mode)                               │
│                                                             │
│ PATTERN: Batch gap-filling service                         │
│   - Runs on schedule (hourly, daily, weekly)               │
│   - Writes directly to ClickHouse                          │
│   - No real-time streaming needed                          │
└─────────────────────────────────────────────────────────────┘
```

---

### **SERVICE 3: dukascopy-historical-downloader**

```
┌─────────────────────────────────────────────────────────────┐
│ SERVICE 3: dukascopy-historical-downloader                  │
├─────────────────────────────────────────────────────────────┤
│ INPUT:  Dukascopy API (historical data)                    │
│ PROCESS: Download, decompress, convert                     │
│                                                             │
│ OUTPUT:                                                     │
│   ├─ ClickHouse.historical_ticks (direct write)           │
│   └─ NO messaging (batch processing only)                 │
│                                                             │
│ MESSAGING: None (batch mode)                               │
│                                                             │
│ PATTERN: One-time/periodic bulk downloader                 │
│   - Downloads years of historical data                     │
│   - Writes directly to ClickHouse                          │
│   - No streaming (batch insert)                            │
└─────────────────────────────────────────────────────────────┘
```

---

### **SERVICE 4: external-data-collector**

```
┌─────────────────────────────────────────────────────────────┐
│ SERVICE 4: external-data-collector                          │
├─────────────────────────────────────────────────────────────┤
│ INPUT:  Economic Calendar API, FRED, Commodities           │
│ PROCESS: Collect external market data                      │
│                                                             │
│ OUTPUT:                                                     │
│   ├─ ClickHouse.external_* tables (direct write)          │
│   ├─ NATS: market.external.{type} (real-time) ✅           │
│   └─ Kafka: external_data_archive (optional) ✅            │
│                                                             │
│ MESSAGING:                                                  │
│   - NATS → Real-time external data stream                  │
│   - Kafka → External data archive                          │
│                                                             │
│ NATS SUBJECTS:                                              │
│   - market.external.economic_calendar                       │
│   - market.external.fred_indicators                         │
│   - market.external.commodity_prices                        │
│                                                             │
│ KAFKA TOPICS:                                               │
│   - external_data_archive                                  │
└─────────────────────────────────────────────────────────────┘
```

---

### **SERVICE 5: data-bridge**

```
┌─────────────────────────────────────────────────────────────┐
│ SERVICE 5: data-bridge                                      │
├─────────────────────────────────────────────────────────────┤
│ INPUT:                                                      │
│   ├─ NATS: Subscribe to ticks.>, bars.>, external.> ✅     │
│   ├─ Kafka: tick_archive, aggregate_archive ✅             │
│   └─ TimescaleDB.live_ticks (read for archiving)          │
│                                                             │
│ PROCESS: Route data, deduplicate, batch write              │
│                                                             │
│ OUTPUT:                                                     │
│   ├─ ClickHouse.historical_ticks (archive)                │
│   ├─ ClickHouse.historical_aggregates (archive)           │
│   └─ DragonflyDB (cache, deduplication)                   │
│                                                             │
│ MESSAGING:                                                  │
│   - NATS subscriber (real-time path)                       │
│   - Kafka consumer (backup + gap filling)                  │
│                                                             │
│ NATS SUBSCRIPTIONS:                                         │
│   - ticks.> (all tick streams)                             │
│   - bars.> (all candle streams)                            │
│   - market.external.> (external data)                      │
│                                                             │
│ KAFKA CONSUMER GROUPS:                                      │
│   - data-bridge-group (load balanced across instances)     │
│                                                             │
│ PATTERN: Data routing hub                                  │
│   - Consumes from both NATS + Kafka                        │
│   - Deduplicates data (DragonflyDB cache)                  │
│   - Batches writes to ClickHouse                           │
└─────────────────────────────────────────────────────────────┘
```

---

### **SERVICE 6: tick-aggregator**

```
┌─────────────────────────────────────────────────────────────┐
│ SERVICE 6: tick-aggregator                                  │
├─────────────────────────────────────────────────────────────┤
│ INPUT:                                                      │
│   ├─ TimescaleDB.live_ticks (read for aggregation)        │
│   └─ ClickHouse.historical_ticks (batch mode)             │
│                                                             │
│ PROCESS: Aggregate ticks → OHLCV candles (7 timeframes)    │
│                                                             │
│ OUTPUT:                                                     │
│   ├─ ClickHouse.live_aggregates (7-day retention)         │
│   ├─ ClickHouse.historical_aggregates (unlimited)         │
│   ├─ NATS: bars.{symbol}.{timeframe} (real-time) ✅        │
│   └─ Kafka: aggregate_archive (persistence) ✅             │
│                                                             │
│ MESSAGING:                                                  │
│   - NATS → Publish candles for real-time subscribers       │
│   - Kafka → Archive candles for replay                     │
│                                                             │
│ NATS SUBJECTS:                                              │
│   - bars.EURUSD.5m                                          │
│   - bars.EURUSD.15m                                         │
│   - bars.EURUSD.1h                                          │
│   - bars.XAUUSD.5m                                          │
│   (... symbol x timeframe combinations)                     │
│                                                             │
│ KAFKA TOPICS:                                               │
│   - aggregate_archive (all symbols, all timeframes)        │
│                                                             │
│ PATTERN: Real-time aggregation + archiving                 │
│   - Runs on cron schedule (every 5m, 15m, 1h, etc)         │
│   - Publishes to NATS for immediate consumption            │
│   - Archives to Kafka for historical replay                │
└─────────────────────────────────────────────────────────────┘
```

---

### **SERVICE 7: feature-engineering-service**

```
┌─────────────────────────────────────────────────────────────┐
│ SERVICE 7: feature-engineering-service                      │
├─────────────────────────────────────────────────────────────┤
│ INPUT:                                                      │
│   ├─ NATS: bars.> (subscribe for real-time) ✅             │
│   ├─ ClickHouse.aggregates (read candles)                 │
│   └─ ClickHouse.external_* (join external data)           │
│                                                             │
│ PROCESS: Calculate 110 ML features                         │
│                                                             │
│ OUTPUT:                                                     │
│   ├─ ClickHouse.ml_features (110 derived features)        │
│   ├─ NATS: features.{symbol}.{timeframe} (real-time) ✅    │
│   └─ Kafka: ml_features_archive (optional) ✅              │
│                                                             │
│ MESSAGING:                                                  │
│   - NATS subscriber (bars) + publisher (features)          │
│   - Kafka → Archive features for training                  │
│                                                             │
│ NATS SUBSCRIPTIONS:                                         │
│   - bars.> (all candles from tick-aggregator)              │
│                                                             │
│ NATS PUBLISH:                                               │
│   - features.EURUSD.5m                                      │
│   - features.XAUUSD.1h                                      │
│   (... for all symbol x timeframe)                          │
│                                                             │
│ KAFKA TOPICS:                                               │
│   - ml_features_archive (optional, for training replay)    │
│                                                             │
│ PATTERN: Real-time feature calculation                     │
│   - Listens to new candles from NATS                       │
│   - Calculates features immediately                        │
│   - Publishes to NATS for inference service                │
│   - Optionally archives to Kafka                           │
└─────────────────────────────────────────────────────────────┘
```

**✅ CHECKPOINT 1**: ml_features table has data → Ready for Phase 2

---

## 🤖 PHASE 2: ML Training

### **SERVICE 8: supervised-training-service**

```
┌─────────────────────────────────────────────────────────────┐
│ SERVICE 8: supervised-training-service                      │
├─────────────────────────────────────────────────────────────┤
│ INPUT:                                                      │
│   ├─ ClickHouse.ml_features (historical + targets)        │
│   └─ NO real-time streaming needed (batch training)       │
│                                                             │
│ PROCESS: Train ML models (XGBoost, LightGBM, CatBoost)     │
│                                                             │
│ OUTPUT:                                                     │
│   ├─ ClickHouse.training_runs                             │
│   ├─ ClickHouse.model_checkpoints                         │
│   ├─ ClickHouse.training_metrics                          │
│   └─ NATS: training.completed.{run_id} (status only) ✅    │
│                                                             │
│ MESSAGING:                                                  │
│   - NATS → Publish training status/completion events       │
│   - NO Kafka (batch training, no streaming)                │
│                                                             │
│ NATS PUBLISH:                                               │
│   - training.started.{run_id}                              │
│   - training.progress.{run_id}                             │
│   - training.completed.{run_id}                            │
│   - training.failed.{run_id}                               │
│                                                             │
│ PATTERN: Batch training with status events                 │
│   - Reads historical features from ClickHouse              │
│   - Trains models (hours/days)                             │
│   - Publishes status to NATS for monitoring                │
│   - Saves checkpoints to ClickHouse                        │
└─────────────────────────────────────────────────────────────┘
```

---

### **SERVICE 9: finrl-training-service**

```
┌─────────────────────────────────────────────────────────────┐
│ SERVICE 9: finrl-training-service                           │
├─────────────────────────────────────────────────────────────┤
│ INPUT:                                                      │
│   ├─ ClickHouse.ml_features (historical, NO targets)      │
│   └─ NO real-time streaming (batch training)              │
│                                                             │
│ PROCESS: Train RL agents (PPO, A2C, SAC)                   │
│                                                             │
│ OUTPUT:                                                     │
│   ├─ ClickHouse.agent_checkpoints                         │
│   ├─ ClickHouse.training_episodes                         │
│   ├─ ClickHouse.reward_history                            │
│   └─ NATS: training.rl.completed.{run_id} (status) ✅      │
│                                                             │
│ MESSAGING:                                                  │
│   - NATS → Publish RL training progress/completion         │
│   - NO Kafka (batch training, episodic)                    │
│                                                             │
│ NATS PUBLISH:                                               │
│   - training.rl.started.{run_id}                           │
│   - training.rl.episode.{run_id}.{episode_num}             │
│   - training.rl.completed.{run_id}                         │
│   - training.rl.failed.{run_id}                            │
│                                                             │
│ PATTERN: Episodic RL training with progress tracking       │
│   - Reads features, creates trading environment            │
│   - Trains agent over episodes                             │
│   - Publishes episode rewards to NATS                      │
│   - Saves agent checkpoints to ClickHouse                  │
└─────────────────────────────────────────────────────────────┘
```

**✅ CHECKPOINT 2**: model_checkpoints/agent_checkpoints exist → Ready for Phase 3

---

## 💼 PHASE 3: Live Trading

### **SERVICE 10: inference-service**

```
┌─────────────────────────────────────────────────────────────┐
│ SERVICE 10: inference-service                               │
├─────────────────────────────────────────────────────────────┤
│ INPUT:                                                      │
│   ├─ NATS: features.> (subscribe real-time features) ✅    │
│   ├─ ClickHouse.ml_features (latest candle fallback)      │
│   └─ ClickHouse.model_checkpoints (load trained models)   │
│                                                             │
│ PROCESS: Generate predictions/actions from models          │
│                                                             │
│ OUTPUT:                                                     │
│   ├─ ClickHouse.trading_signals                           │
│   ├─ ClickHouse.model_predictions (debug)                 │
│   ├─ NATS: signals.{symbol} (real-time signals) ✅         │
│   └─ Kafka: trading_signals_archive (audit trail) ✅       │
│                                                             │
│ MESSAGING:                                                  │
│   - NATS → Subscribe features, publish signals (low latency)│
│   - Kafka → Archive all signals for compliance/audit       │
│                                                             │
│ NATS SUBSCRIPTIONS:                                         │
│   - features.> (all feature streams)                       │
│                                                             │
│ NATS PUBLISH:                                               │
│   - signals.EURUSD (buy/sell/hold signals)                 │
│   - signals.XAUUSD                                          │
│   (... for all symbols)                                     │
│                                                             │
│ KAFKA TOPICS:                                               │
│   - trading_signals_archive (compliance, audit trail)      │
│                                                             │
│ PATTERN: Real-time inference with audit                    │
│   - Listens to features via NATS                           │
│   - Generates signals immediately (< 100ms)                │
│   - Publishes to NATS for risk-management                  │
│   - Archives ALL signals to Kafka (audit)                  │
└─────────────────────────────────────────────────────────────┘
```

---

### **SERVICE 12: risk-management**

```
┌─────────────────────────────────────────────────────────────┐
│ SERVICE 12: risk-management                                 │
├─────────────────────────────────────────────────────────────┤
│ INPUT:                                                      │
│   ├─ NATS: signals.> (subscribe trading signals) ✅        │
│   ├─ ClickHouse.trading_signals (read if needed)          │
│   └─ ClickHouse.positions (current portfolio)             │
│                                                             │
│ PROCESS: Validate position sizing, limits, stop-loss       │
│                                                             │
│ OUTPUT:                                                     │
│   ├─ ClickHouse.trading_signals (update: approved/rejected)│
│   ├─ ClickHouse.risk_events (violations)                  │
│   ├─ NATS: signals.approved.{symbol} (approved only) ✅    │
│   └─ Kafka: risk_events_archive (compliance) ✅            │
│                                                             │
│ MESSAGING:                                                  │
│   - NATS → Real-time risk approval flow                    │
│   - Kafka → Archive risk decisions for audit               │
│                                                             │
│ NATS SUBSCRIPTIONS:                                         │
│   - signals.> (all signals from inference)                 │
│                                                             │
│ NATS PUBLISH:                                               │
│   - signals.approved.EURUSD (approved signals only)        │
│   - signals.rejected.EURUSD (rejected with reason)         │
│   - risk.alert.limit_exceeded                              │
│                                                             │
│ KAFKA TOPICS:                                               │
│   - risk_events_archive (audit log of risk decisions)      │
│                                                             │
│ PATTERN: Real-time risk gate                               │
│   - Receives signals via NATS                              │
│   - Validates against position limits, drawdown            │
│   - Publishes approved signals to execution-service        │
│   - Archives ALL risk decisions to Kafka                   │
└─────────────────────────────────────────────────────────────┘
```

---

### **SERVICE 11: execution-service**

```
┌─────────────────────────────────────────────────────────────┐
│ SERVICE 11: execution-service                               │
├─────────────────────────────────────────────────────────────┤
│ INPUT:                                                      │
│   ├─ NATS: signals.approved.> (approved signals) ✅        │
│   └─ ClickHouse.trading_signals (read approved)           │
│                                                             │
│ PROCESS: Create orders, send to broker, track fills        │
│                                                             │
│ OUTPUT:                                                     │
│   ├─ ClickHouse.orders                                    │
│   ├─ ClickHouse.executions                                │
│   ├─ ClickHouse.positions                                 │
│   ├─ NATS: orders.{status}.{symbol} (order status) ✅      │
│   └─ Kafka: order_execution_archive (audit) ✅             │
│                                                             │
│ MESSAGING:                                                  │
│   - NATS → Real-time order flow & status updates           │
│   - Kafka → Complete order audit trail                     │
│                                                             │
│ NATS SUBSCRIPTIONS:                                         │
│   - signals.approved.> (approved signals only)             │
│                                                             │
│ NATS PUBLISH:                                               │
│   - orders.pending.EURUSD                                   │
│   - orders.submitted.EURUSD                                 │
│   - orders.filled.EURUSD                                    │
│   - orders.cancelled.EURUSD                                 │
│   - orders.failed.EURUSD                                    │
│                                                             │
│ KAFKA TOPICS:                                               │
│   - order_execution_archive (complete order lifecycle)     │
│                                                             │
│ PATTERN: Real-time order management                        │
│   - Receives approved signals via NATS                     │
│   - Creates orders, sends to mt5-connector                 │
│   - Publishes order status to NATS                         │
│   - Archives complete execution log to Kafka               │
└─────────────────────────────────────────────────────────────┘
```

---

### **SERVICE 13: performance-monitoring**

```
┌─────────────────────────────────────────────────────────────┐
│ SERVICE 13: performance-monitoring                          │
├─────────────────────────────────────────────────────────────┤
│ INPUT:                                                      │
│   ├─ NATS: orders.filled.> (real-time fills) ✅            │
│   ├─ ClickHouse.positions (read positions)                │
│   ├─ ClickHouse.orders (read for analysis)                │
│   └─ ClickHouse.executions (read slippage)                │
│                                                             │
│ PROCESS: Calculate Sharpe, drawdown, win rate, P&L         │
│                                                             │
│ OUTPUT:                                                     │
│   ├─ ClickHouse.portfolio_value (equity curve)            │
│   ├─ ClickHouse.performance_metrics                       │
│   ├─ ClickHouse.trade_analysis                            │
│   ├─ NATS: performance.alert.{type} (alerts) ✅            │
│   └─ NO Kafka (periodic calculation, not streaming)        │
│                                                             │
│ MESSAGING:                                                  │
│   - NATS → Real-time performance alerts                    │
│   - NO Kafka (metrics calculated periodically)             │
│                                                             │
│ NATS SUBSCRIPTIONS:                                         │
│   - orders.filled.> (track all fills)                      │
│                                                             │
│ NATS PUBLISH:                                               │
│   - performance.alert.drawdown_limit                       │
│   - performance.alert.daily_loss_limit                     │
│   - performance.alert.low_sharpe                           │
│                                                             │
│ PATTERN: Real-time monitoring with periodic aggregation    │
│   - Listens to fills via NATS                              │
│   - Updates equity curve real-time                         │
│   - Calculates metrics periodically (daily)                │
│   - Publishes alerts to NATS                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔌 PHASE 4: Supporting Services

### **SERVICE 14: mt5-connector**

```
┌─────────────────────────────────────────────────────────────┐
│ SERVICE 14: mt5-connector                                   │
├─────────────────────────────────────────────────────────────┤
│ INPUT:                                                      │
│   ├─ NATS: orders.> (listen for orders) ✅                 │
│   └─ ClickHouse.orders (read order details)               │
│                                                             │
│ PROCESS: Send orders to MT5, receive fills                 │
│                                                             │
│ OUTPUT:                                                     │
│   ├─ ClickHouse.executions (broker fills)                 │
│   ├─ NATS: broker.fill.{symbol} (fill confirmations) ✅    │
│   └─ Kafka: broker_communication_log (audit) ✅            │
│                                                             │
│ MESSAGING:                                                  │
│   - NATS → Real-time broker communication                  │
│   - Kafka → Complete broker interaction log                │
│                                                             │
│ NATS SUBSCRIPTIONS:                                         │
│   - orders.submitted.> (new orders to send)                │
│                                                             │
│ NATS PUBLISH:                                               │
│   - broker.fill.EURUSD (fill confirmations from broker)    │
│   - broker.error.{symbol} (broker errors)                  │
│                                                             │
│ KAFKA TOPICS:                                               │
│   - broker_communication_log (compliance, audit)           │
│                                                             │
│ PATTERN: Broker API gateway                                │
│   - Receives order requests via NATS                       │
│   - Sends to MT5 broker API                                │
│   - Publishes fill confirmations to NATS                   │
│   - Archives all broker interactions to Kafka              │
└─────────────────────────────────────────────────────────────┘
```

---

### **SERVICE 15: backtesting-engine**

```
┌─────────────────────────────────────────────────────────────┐
│ SERVICE 15: backtesting-engine                              │
├─────────────────────────────────────────────────────────────┤
│ INPUT:                                                      │
│   ├─ ClickHouse.historical_aggregates                     │
│   ├─ ClickHouse.ml_features (historical)                  │
│   └─ ClickHouse.model_checkpoints (models to test)        │
│                                                             │
│ PROCESS: Historical simulation, walk-forward testing       │
│                                                             │
│ OUTPUT:                                                     │
│   ├─ ClickHouse.backtest_results                          │
│   └─ NATS: backtest.completed.{run_id} (status) ✅         │
│                                                             │
│ MESSAGING:                                                  │
│   - NATS → Publish backtest completion status              │
│   - NO Kafka (batch processing)                            │
│                                                             │
│ NATS PUBLISH:                                               │
│   - backtest.started.{run_id}                              │
│   - backtest.progress.{run_id}                             │
│   - backtest.completed.{run_id}                            │
│                                                             │
│ PATTERN: Batch simulation with status events               │
│   - Reads historical data from ClickHouse                  │
│   - Simulates trading strategy                             │
│   - Publishes progress to NATS                             │
│   - Saves results to ClickHouse                            │
└─────────────────────────────────────────────────────────────┘
```

---

### **SERVICE 16: dashboard-service**

```
┌─────────────────────────────────────────────────────────────┐
│ SERVICE 16: dashboard-service                               │
├─────────────────────────────────────────────────────────────┤
│ INPUT:                                                      │
│   ├─ NATS: *.> (subscribe ALL events for monitoring) ✅    │
│   └─ ClickHouse.* (read all tables)                       │
│                                                             │
│ PROCESS: Real-time dashboards, KPI tracking                │
│                                                             │
│ OUTPUT:                                                     │
│   └─ Web UI (dashboards, charts, alerts)                  │
│                                                             │
│ MESSAGING:                                                  │
│   - NATS subscriber (real-time dashboard updates)          │
│   - NO publishing (read-only service)                      │
│                                                             │
│ NATS SUBSCRIPTIONS:                                         │
│   - ticks.> (live tick data)                               │
│   - bars.> (live candles)                                  │
│   - signals.> (trading signals)                            │
│   - orders.> (order status)                                │
│   - performance.alert.> (alerts)                           │
│   - training.> (training progress)                         │
│                                                             │
│ PATTERN: Real-time monitoring dashboard                    │
│   - Subscribes to all NATS events                          │
│   - Updates UI in real-time (WebSocket to browser)         │
│   - Queries ClickHouse for historical data                 │
│   - Read-only (no publishing)                              │
└─────────────────────────────────────────────────────────────┘
```

---

### **SERVICE 17: notification-hub**

```
┌─────────────────────────────────────────────────────────────┐
│ SERVICE 17: notification-hub                                │
├─────────────────────────────────────────────────────────────┤
│ INPUT:                                                      │
│   ├─ NATS: performance.alert.>, risk.alert.> ✅            │
│   └─ ClickHouse.risk_events, performance_metrics          │
│                                                             │
│ PROCESS: Route alerts (Telegram, Email, SMS)               │
│                                                             │
│ OUTPUT:                                                     │
│   └─ Notifications (Telegram Bot, SMTP, SMS)              │
│                                                             │
│ MESSAGING:                                                  │
│   - NATS subscriber (alert events)                         │
│   - NO Kafka (fire-and-forget notifications)               │
│                                                             │
│ NATS SUBSCRIPTIONS:                                         │
│   - performance.alert.> (performance alerts)               │
│   - risk.alert.> (risk violations)                         │
│   - training.completed.> (training done notifications)     │
│   - orders.filled.> (trade notifications)                  │
│                                                             │
│ PATTERN: Event-driven notification router                  │
│   - Listens to alert events via NATS                       │
│   - Routes to appropriate channel (Telegram/Email/SMS)     │
│   - Fire-and-forget (no persistence needed)                │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Messaging Summary Table

| # | Service | NATS (Real-time) | Kafka (Archive) | Pattern |
|---|---------|------------------|-----------------|---------|
| 1 | polygon-live-collector | Publish: `ticks.*` | Publish: `tick_archive` | Both (real-time + archive) |
| 2 | polygon-historical-downloader | - | - | None (batch to ClickHouse) |
| 3 | dukascopy-historical-downloader | - | - | None (batch to ClickHouse) |
| 4 | external-data-collector | Publish: `market.external.*` | Publish: `external_archive` | Both (real-time + archive) |
| 5 | data-bridge | Subscribe: `ticks.>`, `bars.>`, `external.>` | Consumer: All archives | Both (subscriber + consumer) |
| 6 | tick-aggregator | Publish: `bars.*.*` | Publish: `aggregate_archive` | Both (real-time + archive) |
| 7 | feature-engineering-service | Sub: `bars.>`, Pub: `features.*.*` | Optional: `ml_features_archive` | NATS primary, Kafka optional |
| 8 | supervised-training-service | Publish: `training.completed.*` | - | NATS status only |
| 9 | finrl-training-service | Publish: `training.rl.*` | - | NATS status only |
| 10 | inference-service | Sub: `features.>`, Pub: `signals.*` | Publish: `signals_archive` | Both (real-time + audit) |
| 11 | execution-service | Sub: `signals.approved.>`, Pub: `orders.*.*` | Publish: `order_archive` | Both (real-time + audit) |
| 12 | risk-management | Sub: `signals.>`, Pub: `signals.approved.*` | Publish: `risk_archive` | Both (real-time + audit) |
| 13 | performance-monitoring | Sub: `orders.filled.>`, Pub: `performance.alert.*` | - | NATS only |
| 14 | mt5-connector | Sub: `orders.submitted.>`, Pub: `broker.fill.*` | Publish: `broker_log` | Both (real-time + audit) |
| 15 | backtesting-engine | Publish: `backtest.completed.*` | - | NATS status only |
| 16 | dashboard-service | Subscribe: `*.*` (all events) | - | NATS only (read-only) |
| 17 | notification-hub | Subscribe: `*.alert.*` | - | NATS only (fire-and-forget) |

---

## 📡 NATS Subject Naming Convention

### **Format**: `{domain}.{entity}.{detail}`

### **Domains**:
- `ticks` - Raw tick data
- `bars` - Aggregated candles
- `features` - ML features
- `signals` - Trading signals
- `orders` - Order lifecycle
- `broker` - Broker interactions
- `training` - Model/agent training
- `backtest` - Backtesting results
- `performance` - Performance metrics
- `risk` - Risk management
- `market.external` - External data

### **Examples**:
```
# Tick data
ticks.EURUSD
ticks.XAUUSD

# Candles (bars)
bars.EURUSD.5m
bars.EURUSD.1h
bars.XAUUSD.1d

# ML Features
features.EURUSD.5m
features.XAUUSD.1h

# Trading signals
signals.EURUSD
signals.approved.EURUSD
signals.rejected.XAUUSD

# Orders
orders.pending.EURUSD
orders.submitted.EURUSD
orders.filled.EURUSD
orders.cancelled.EURUSD
orders.failed.EURUSD

# Broker
broker.fill.EURUSD
broker.error.XAUUSD

# Training
training.started.run_123
training.completed.run_123
training.rl.episode.run_456.1000

# Performance
performance.alert.drawdown_limit
performance.alert.daily_loss_limit

# Risk
risk.alert.limit_exceeded
risk.alert.position_size

# External data
market.external.economic_calendar
market.external.fred_indicators
market.external.commodity_prices
```

### **Wildcards**:
- `ticks.>` - All tick streams
- `bars.>` - All candle streams
- `bars.EURUSD.*` - All EURUSD timeframes
- `orders.*.EURUSD` - All order statuses for EURUSD
- `*.alert.*` - All alerts from all domains

---

## 📦 Kafka Topic Naming Convention

### **Format**: `{purpose}_archive` or `{domain}_archive`

### **Topics**:
```
# Data archives (for replay & gap filling)
tick_archive                    # All raw ticks
aggregate_archive               # All candles (7 timeframes)
external_data_archive           # Economic calendar, FRED, commodities
ml_features_archive             # ML features (optional)

# Audit/compliance archives
trading_signals_archive         # All signals (approved + rejected)
order_execution_archive         # Complete order lifecycle
risk_events_archive             # Risk decisions & violations
broker_communication_log        # Broker API interactions
```

### **Partitioning Strategy**:
- **By symbol**: `EURUSD`, `XAUUSD`, `GBPUSD`, etc.
- **Purpose**: Parallel processing, load balancing
- **Consumer groups**: Multiple instances = automatic load distribution

### **Retention**:
- Critical archives (orders, signals): 7 years (compliance)
- Data archives (ticks, aggregates): 1 year (reprocessing)
- Logs (broker communication): 90 days (debugging)

---

## 🎯 Key Patterns

### **Pattern 1: Real-time + Archive (Critical Data)**
Services that need both immediate delivery AND historical replay:
- polygon-live-collector (ticks)
- tick-aggregator (candles)
- inference-service (signals)
- execution-service (orders)

**Flow**: Publish to NATS (real-time) + Kafka (archive)

---

### **Pattern 2: Real-time Only (Ephemeral Events)**
Services that only need immediate delivery:
- feature-engineering-service (derived from archived candles)
- performance-monitoring (alerts)
- training services (status notifications)

**Flow**: Publish to NATS only

---

### **Pattern 3: Batch Processing (No Streaming)**
Services that process historical data in batches:
- polygon-historical-downloader
- dukascopy-historical-downloader
- backtesting-engine

**Flow**: Direct database writes, optional status to NATS

---

### **Pattern 4: Hub Consumer (Multi-source)**
Services that consume from multiple sources:
- data-bridge (NATS + Kafka → ClickHouse)
- dashboard-service (NATS all events → WebSocket UI)

**Flow**: Subscribe to multiple NATS subjects/Kafka topics

---

## ✅ Validation Checklist

Before implementing messaging for a service:

- [ ] **Purpose Clear**: Why does this service need messaging?
- [ ] **NATS or Kafka?**: Real-time streaming or archive/replay?
- [ ] **Both?**: Do we need immediate delivery AND historical replay?
- [ ] **Subject/Topic Name**: Follows naming convention?
- [ ] **Wildcards Correct**: Subscribing to correct subject pattern?
- [ ] **Consumer Group**: Kafka consumer group configured (if applicable)?
- [ ] **Retention Policy**: Kafka topic retention configured?
- [ ] **Deduplication**: Is deduplication needed (data-bridge)?
- [ ] **Error Handling**: What happens if messaging fails?
- [ ] **Monitoring**: How to monitor message flow?

---

## 🎯 Quick Reference

**When to use NATS**:
- ✅ Real-time streaming (< 100ms latency)
- ✅ Fire-and-forget delivery
- ✅ Ephemeral events (alerts, status updates)
- ✅ High throughput (millions of messages/sec)

**When to use Kafka**:
- ✅ Audit trail & compliance
- ✅ Replay capability (gap filling)
- ✅ At-least-once delivery guarantee
- ✅ Multi-consumer scenarios (load balancing)

**When to use Both**:
- ✅ Critical data that needs BOTH real-time + archive
- ✅ Trading signals (immediate execution + audit)
- ✅ Ticks & candles (real-time analysis + historical backfill)

**When to use Neither**:
- ✅ Batch processing (historical downloaders)
- ✅ Direct database writes (no streaming needed)

---

**Version History**:
- v1.0.0 (2025-10-18): Initial complete service flow tree with messaging layer documentation
