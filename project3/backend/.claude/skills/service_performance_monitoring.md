# Skill: performance-monitoring Service

## Purpose
Track trading performance in real-time. Calculate metrics (Sharpe, drawdown, win rate) and generate alerts.

## Key Facts
- **Phase**: Live Trading (Phase 3)
- **Status**: ⚠️ To Build
- **Priority**: P2 (High - monitor trading performance)
- **Function**: Performance calculation, equity curve, alerts
- **Metrics**: Sharpe ratio, Sortino, max drawdown, win rate, profit factor

## Data Flow
```
NATS: orders.filled.> (subscribe from execution-service)
ClickHouse.positions (read)
ClickHouse.orders (read)
ClickHouse.executions (read)
  → performance-monitoring (calculate metrics, generate alerts)
  → ClickHouse.portfolio_value (equity curve)
  → ClickHouse.performance_metrics
  → ClickHouse.trade_analysis
  → NATS: performance.alert.{type} (alerts)
```

## Messaging
- **NATS Subscribe**: `orders.filled.>` (real-time fills from execution-service)
- **NATS Publish**: `performance.alert.drawdown_limit`, `performance.alert.daily_loss_limit`, `performance.alert.low_sharpe`
- **Pattern**: NATS only (real-time monitoring, no Kafka archival needed)

## Dependencies
- **Upstream**: execution-service (fills via NATS)
- **Downstream**: notification-hub (alert routing), dashboard-service (visualizations)
- **Infrastructure**: ClickHouse, NATS cluster

## Critical Rules
1. **NEVER** use forward-looking data in metrics (prevent look-ahead bias)
2. **ALWAYS** update equity curve in real-time (track portfolio value)
3. **VERIFY** performance calculations match industry standards (Sharpe formula)
4. **ENSURE** alerts trigger before catastrophic loss (early warning system)
5. **VALIDATE** trade analysis matches executed orders (reconciliation)

## Performance Metrics
### Risk-Adjusted Returns
- **Sharpe Ratio**: (Return - RiskFree) / StdDev
- **Sortino Ratio**: (Return - RiskFree) / Downside StdDev
- **Calmar Ratio**: CAGR / Max Drawdown

### Drawdown
- **Max Drawdown**: Largest peak-to-trough decline
- **Current Drawdown**: Current decline from peak
- **Drawdown Duration**: Days in drawdown

### Win Rate
- **Total Trades**: Count of closed positions
- **Winning Trades**: Count of profitable trades
- **Win Rate %**: Winning / Total * 100
- **Profit Factor**: Gross Profit / Gross Loss

### Trade Statistics
- **Avg Win**: Average profitable trade
- **Avg Loss**: Average losing trade
- **Largest Win**: Biggest single win
- **Largest Loss**: Biggest single loss
- **Avg R-multiple**: Average reward/risk ratio
- **Expectancy**: (Win% * AvgWin) - (Loss% * AvgLoss)

## Validation
When working on this service, ALWAYS verify:
- [ ] NATS subscribes to `orders.filled.>` (real-time fills)
- [ ] Equity curve updated (portfolio_value table)
- [ ] Metrics calculated correctly (verify formulas)
- [ ] Alerts published to NATS (performance.alert.*)
- [ ] Trade analysis matches executions (reconciliation check)

## Reference Docs
- Planning guide: `PLANNING_SKILL_GUIDE.md` (Service 13, lines 2052-2250)
- Architecture: `SERVICE_ARCHITECTURE_AND_FLOW.md` (lines 659-698)
- Flow + messaging: `SERVICE_FLOW_TREE_WITH_MESSAGING.md` (lines 635-677)
- Database schema: `table_database_trading.md` (portfolio_value, performance_metrics tables)
