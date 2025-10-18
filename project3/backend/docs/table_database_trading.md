# 📈 Database Trading Tables - Live Trading & Performance Tracking

> **Version**: 1.0.0  
> **Last Updated**: 2025-10-18  
> **Status**: Complete - Ready for Implementation  
> **Related Services**: inference-service, execution-service, risk-management, performance-monitoring

---

## 📋 Overview

**Purpose**: Dokumentasi untuk tabel-tabel yang digunakan dalam **Live Trading & Continuous Learning**

**Input**: Trained models/agents (dari table_database_training.md)  
**Output**: Trading signals, executions, positions, performance metrics

**Database**: ClickHouse (suho_analytics)

---

## 🎯 Trading Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                  TRADING EXECUTION PIPELINE                     │
└─────────────────────────────────────────────────────────────────┘

ml_features (live, latest candle)
    ↓
inference-service
    ├─ Load trained model/agent
    ├─ Generate predictions/actions
    └─ Create trading signals
    ↓
TABLES: trading_signals, model_predictions
    ↓
risk-management
    ├─ Position sizing
    ├─ Stop-loss/take-profit calculation
    ├─ Portfolio limit checks
    └─ Risk approval/rejection
    ↓
TABLES: risk_events
    ↓
execution-service
    ├─ Create orders
    ├─ Send to broker (MT5)
    ├─ Track execution
    └─ Update positions
    ↓
TABLES: orders, executions, positions
    ↓
performance-monitoring
    ├─ Calculate metrics (Sharpe, drawdown, win rate)
    ├─ Compare vs benchmark
    └─ Generate alerts
    ↓
TABLES: portfolio_value, performance_metrics, trade_analysis
    ↓
(Optional) finrl-training-service
    └─ Continuous learning dengan real trading results
```

---

## 📊 Complete Table List

| # | Table Name | Purpose | Service | Priority |
|---|-----------|---------|---------|----------|
| 1 | trading_signals | ML/RL generated trading signals | inference-service | P0 |
| 2 | model_predictions | Raw model outputs for debugging | inference-service | P1 |
| 3 | orders | Order creation & submission | execution-service | P0 |
| 4 | executions | Order fills & slippage tracking | execution-service | P0 |
| 5 | positions | Open & closed positions | execution-service | P0 |
| 6 | portfolio_value | Equity curve over time | performance-monitoring | P0 |
| 7 | performance_metrics | Sharpe, drawdown, win rate, etc | performance-monitoring | P1 |
| 8 | risk_events | Risk triggers & violations | risk-management | P1 |
| 9 | trade_analysis | Individual trade breakdown | performance-monitoring | P1 |

---

## 📁 Database: ClickHouse (suho_analytics)

**Why ClickHouse for Trading Tables?**
- Fast writes untuk real-time trading data
- Time-series optimization untuk price/equity tracking
- Fast aggregations untuk performance calculations
- Efficient storage dengan compression
- Real-time queries untuk monitoring dashboards

---

## 🔔 SIGNAL GENERATION TABLES

### **Table 1: trading_signals**

**Purpose**: ML/RL predictions yang sudah di-approve oleh risk management

**Key Columns**:
- signal_id (UUID)
- model_id/agent_id (which model generated this)
- symbol, timeframe, timestamp
- signal_type (buy/sell/hold/close)
- confidence_score (0-1)
- position_size_recommended
- stop_loss, take_profit levels
- risk_approval_status
- execution_status

**ClickHouse Schema**:
```sql
CREATE TABLE suho_analytics.trading_signals
(
    signal_id UUID DEFAULT generateUUIDv4(),
    created_at DateTime64(3, 'UTC') DEFAULT now64(),
    
    -- Model/Agent Info
    model_checkpoint_id Nullable(UUID),  -- From model_checkpoints
    agent_checkpoint_id Nullable(UUID),  -- From agent_checkpoints
    model_version String,
    
    -- Market Info
    symbol String,
    timeframe Enum8('5m'=1, '15m'=2, '30m'=3, '1h'=4, '4h'=5, '1d'=6, '1w'=7),
    signal_timestamp DateTime64(3, 'UTC'),
    
    -- Signal Details
    signal_type Enum8('buy'=1, 'sell'=2, 'hold'=3, 'close_long'=4, 'close_short'=5),
    confidence_score Float64,              -- 0-1
    position_size_recommended Float64,      -- Lot size or % of capital
    
    -- Price Levels
    entry_price Float64,
    stop_loss Float64,
    take_profit Float64,
    
    -- Risk Management
    risk_approval_status Enum8('pending'=1, 'approved'=2, 'rejected'=3),
    risk_rejection_reason Nullable(String),
    risk_reviewed_at Nullable(DateTime64(3, 'UTC')),
    
    -- Execution Status
    execution_status Enum8('pending'=1, 'submitted'=2, 'filled'=3, 'cancelled'=4, 'failed'=5),
    order_id Nullable(UUID),               -- FK to orders table
    
    -- Metadata
    features_snapshot String,              -- JSON: feature values at signal time
    model_raw_output String                -- JSON: raw model prediction probabilities
)
ENGINE = MergeTree()
PARTITION BY (symbol, toYYYYMM(created_at))
ORDER BY (symbol, created_at, signal_id)
TTL created_at + INTERVAL 1 YEAR;
```

---

### **Table 2: model_predictions**

**Purpose**: Raw model outputs untuk debugging & analysis

**Key Columns**:
- prediction_id, model_checkpoint_id
- symbol, timestamp
- raw_predictions (JSON: probabilities for buy/sell/hold)
- feature_values_used (snapshot)
- inference_latency_ms

---

## 💼 ORDER & EXECUTION TABLES

### **Table 3: orders**

**Purpose**: Order lifecycle tracking

**Key Columns**:
- order_id (UUID)
- signal_id (FK to trading_signals)
- symbol, order_type (market/limit/stop)
- side (buy/sell), quantity
- price, stop_price
- order_status (pending/submitted/filled/cancelled)
- broker_order_id
- submission/fill timestamps

**ClickHouse Schema**:
```sql
CREATE TABLE suho_analytics.orders
(
    order_id UUID DEFAULT generateUUIDv4(),
    created_at DateTime64(3, 'UTC') DEFAULT now64(),
    
    -- Related Signal
    signal_id UUID,                        -- FK to trading_signals
    
    -- Market Info
    symbol String,
    timeframe String,
    
    -- Order Details
    order_type Enum8('market'=1, 'limit'=2, 'stop'=3, 'stop_limit'=4),
    side Enum8('buy'=1, 'sell'=2),
    quantity Float64,                      -- Lot size
    
    -- Price Details
    price Nullable(Float64),               -- For limit orders
    stop_price Nullable(Float64),          -- For stop orders
    
    -- Execution
    order_status Enum8(
        'pending'=1, 
        'submitted'=2, 
        'partially_filled'=3,
        'filled'=4, 
        'cancelled'=5, 
        'rejected'=6,
        'failed'=7
    ),
    
    -- Broker Integration
    broker_order_id Nullable(String),      -- MT5 order ID
    broker String DEFAULT 'MT5',
    
    -- Timestamps
    submitted_at Nullable(DateTime64(3, 'UTC')),
    filled_at Nullable(DateTime64(3, 'UTC')),
    cancelled_at Nullable(DateTime64(3, 'UTC')),
    
    -- Fill Details
    filled_quantity Nullable(Float64),
    average_fill_price Nullable(Float64),
    commission Nullable(Float64),
    
    -- Failure Info
    rejection_reason Nullable(String),
    error_message Nullable(String)
)
ENGINE = MergeTree()
PARTITION BY (symbol, toYYYYMM(created_at))
ORDER BY (symbol, created_at, order_id);
```

---

### **Table 4: executions**

**Purpose**: Granular fill tracking (partial fills, slippage)

**Key Columns**:
- execution_id, order_id
- fill_price, fill_quantity
- slippage (difference from expected price)
- commission
- execution_timestamp

---

### **Table 5: positions**

**Purpose**: Open & closed position tracking

**Key Columns**:
- position_id, symbol
- side (long/short), quantity
- entry_price, current_price
- stop_loss, take_profit
- unrealized_pnl, realized_pnl
- position_status (open/closed)
- entry/exit timestamps

**ClickHouse Schema**:
```sql
CREATE TABLE suho_analytics.positions
(
    position_id UUID DEFAULT generateUUIDv4(),
    opened_at DateTime64(3, 'UTC'),
    
    -- Market Info
    symbol String,
    
    -- Position Details
    side Enum8('long'=1, 'short'=2),
    quantity Float64,
    entry_price Float64,
    
    -- Risk Management
    stop_loss Float64,
    take_profit Float64,
    
    -- Current State
    position_status Enum8('open'=1, 'closed'=2),
    current_price Nullable(Float64),
    
    -- P&L
    unrealized_pnl Nullable(Float64),      -- For open positions
    realized_pnl Nullable(Float64),        -- For closed positions
    commission_total Float64,
    
    -- Closing Info
    exit_price Nullable(Float64),
    exit_reason Nullable(Enum8('take_profit'=1, 'stop_loss'=2, 'manual'=3, 'signal'=4)),
    closed_at Nullable(DateTime64(3, 'UTC')),
    
    -- Performance Metrics
    r_multiple Nullable(Float64),          -- Reward/Risk ratio
    holding_period_hours Nullable(Float64),
    
    -- Related Orders
    entry_order_id UUID,
    exit_order_id Nullable(UUID)
)
ENGINE = MergeTree()
PARTITION BY (symbol, toYYYYMM(opened_at))
ORDER BY (symbol, opened_at, position_id);
```

---

## 📊 PERFORMANCE TRACKING TABLES

### **Table 6: portfolio_value**

**Purpose**: Equity curve tracking (time-series)

**Key Columns**:
- timestamp
- total_equity
- cash_balance
- positions_value
- unrealized_pnl
- realized_pnl_today
- total_pnl_cumulative

**ClickHouse Schema**:
```sql
CREATE TABLE suho_analytics.portfolio_value
(
    timestamp DateTime64(3, 'UTC'),
    
    -- Portfolio Components
    total_equity Float64,                  -- Cash + Positions
    cash_balance Float64,
    positions_value Float64,               -- Sum of all open positions
    
    -- P&L Breakdown
    unrealized_pnl Float64,                -- From open positions
    realized_pnl_today Float64,
    realized_pnl_total Float64,            -- Cumulative
    
    -- Performance
    daily_return_pct Float64,
    total_return_pct Float64,              -- From starting capital
    
    -- Risk Metrics
    max_drawdown_pct Float64,
    current_drawdown_pct Float64,
    
    -- Positions Count
    open_positions_count UInt16,
    
    -- Metadata
    starting_capital Float64
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY timestamp
TTL timestamp + INTERVAL 2 YEAR;
```

---

### **Table 7: performance_metrics**

**Purpose**: Calculated performance metrics (daily/weekly/monthly)

**Key Columns**:
- period_start, period_end
- period_type (daily/weekly/monthly)
- sharpe_ratio, sortino_ratio
- max_drawdown, win_rate
- profit_factor, expectancy
- total_trades, winning_trades

**ClickHouse Schema**:
```sql
CREATE TABLE suho_analytics.performance_metrics
(
    metric_id UUID DEFAULT generateUUIDv4(),
    calculated_at DateTime64(3, 'UTC') DEFAULT now64(),
    
    -- Period Info
    period_start DateTime,
    period_end DateTime,
    period_type Enum8('daily'=1, 'weekly'=2, 'monthly'=3, 'yearly'=4, 'all_time'=5),
    
    -- Return Metrics
    total_return_pct Float64,
    cagr Nullable(Float64),                -- Compound Annual Growth Rate
    
    -- Risk-Adjusted Returns
    sharpe_ratio Float64,
    sortino_ratio Nullable(Float64),
    calmar_ratio Nullable(Float64),
    
    -- Drawdown
    max_drawdown_pct Float64,
    avg_drawdown_pct Float64,
    max_drawdown_duration_days Nullable(UInt32),
    
    -- Win Rate
    total_trades UInt32,
    winning_trades UInt32,
    losing_trades UInt32,
    win_rate_pct Float64,
    
    -- Profit Metrics
    gross_profit Float64,
    gross_loss Float64,
    net_profit Float64,
    profit_factor Float64,                 -- Gross profit / Gross loss
    
    -- Trade Statistics
    avg_win Float64,
    avg_loss Float64,
    largest_win Float64,
    largest_loss Float64,
    avg_r_multiple Float64,
    expectancy Float64,                    -- (Win% * Avg Win) - (Loss% * Avg Loss)
    
    -- Holding Period
    avg_holding_period_hours Float64,
    
    -- Benchmark Comparison
    benchmark_return_pct Nullable(Float64),  -- Buy & hold
    alpha Nullable(Float64),               -- Excess return vs benchmark
    beta Nullable(Float64)                 -- Correlation with benchmark
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(period_start)
ORDER BY (period_type, period_start);
```

---

### **Table 8: risk_events**

**Purpose**: Risk violations & triggers

**Key Columns**:
- event_id, timestamp
- event_type (max_position_exceeded, daily_loss_limit, etc)
- severity (warning/critical)
- action_taken (signal_rejected/position_closed)

---

### **Table 9: trade_analysis**

**Purpose**: Individual trade detailed breakdown

**Key Columns**:
- trade_id, position_id
- entry/exit details
- pnl, r_multiple
- holding_period
- entry/exit_reason
- trade_quality_score

---

## 🔄 Trading Workflows

### **Real-Time Trading Flow**:
1. **Inference**: Generate trading_signal from ml_features
2. **Risk Check**: Validate signal, create risk_event if rejected
3. **Order Creation**: Create order in orders table
4. **Execution**: Track fills in executions table
5. **Position Update**: Update/create position in positions table
6. **Portfolio Update**: Update portfolio_value (real-time)
7. **Performance Calc**: Calculate performance_metrics (periodic)

### **Continuous Learning (FinRL)**:
1. Monitor trading_signals → executions → positions
2. Calculate actual rewards from real trades
3. Feed back to finrl-training-service
4. Retrain agent with real-world results
5. Deploy improved agent

---

## 📊 Query Examples

### Active Positions:
```sql
SELECT
    symbol,
    side,
    quantity,
    entry_price,
    current_price,
    unrealized_pnl,
    ROUND((current_price - entry_price) / (entry_price - stop_loss), 2) as r_multiple
FROM positions
WHERE position_status = 'open'
ORDER BY unrealized_pnl DESC;
```

### Today's Performance:
```sql
SELECT
    total_return_pct,
    sharpe_ratio,
    win_rate_pct,
    total_trades,
    profit_factor
FROM performance_metrics
WHERE period_type = 'daily'
  AND period_start = today()
LIMIT 1;
```

### Recent Trades:
```sql
SELECT
    p.symbol,
    p.side,
    p.entry_price,
    p.exit_price,
    p.realized_pnl,
    p.r_multiple,
    p.exit_reason
FROM positions p
WHERE p.position_status = 'closed'
  AND p.closed_at >= now() - INTERVAL 7 DAY
ORDER BY p.closed_at DESC
LIMIT 20;
```

---

## 🎯 Implementation Notes

1. **Real-Time Updates**: Update portfolio_value every 1 minute for equity curve
2. **Risk Checks**: Validate BEFORE order submission (prevent violations)
3. **Idempotency**: Use UUIDs for orders to prevent duplicates
4. **Audit Trail**: Never delete trading data (use TTL for old data only)
5. **Performance Calculation**: Run daily after market close, weekly on weekends
6. **Continuous Learning**: Optional FinRL updates with real trading feedback

---

## 📝 Next Steps

1. Implement inference-service (load models, generate signals)
2. Implement execution-service (order management, broker integration)
3. Implement risk-management (position sizing, limit checks)
4. Implement performance-monitoring (metrics calculation, alerts)
5. Setup dashboards untuk real-time monitoring
6. Paper trading validation (dry-run with real signals)
7. Live trading dengan small capital

---

**Version History**:
- v1.0.0 (2025-10-18): Initial complete trading tables documentation
