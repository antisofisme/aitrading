---
name: performance-monitoring
description: Tracks trading performance in real-time with industry-standard metrics (Sharpe, Sortino, drawdown, win rate) and generates alerts when thresholds are breached
license: MIT
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
metadata:
  type: Trading (Performance Monitoring)
  phase: Live Trading (Phase 3)
  status: To Build
  priority: P2 (High - monitor trading health)
  port: 8013
  dependencies:
    - central-hub
    - clickhouse
    - nats
  version: 1.0.0
---

# Performance Monitoring Service

Tracks trading performance in real-time using industry-standard metrics (Sharpe ratio, Sortino ratio, max drawdown, win rate, profit factor). Generates alerts when performance thresholds are breached and maintains equity curve for visualization.

## When to Use This Skill

Use this skill when:
- Calculating trading performance metrics
- Monitoring equity curve in real-time
- Setting up performance alerts (drawdown, daily loss)
- Analyzing trade statistics (win rate, profit factor)
- Debugging performance degradation
- Generating performance reports

## Service Overview

**Type:** Trading (Performance Monitoring)
**Port:** 8013
**Input:** NATS (`orders.filled.>` from execution) + ClickHouse (orders, positions)
**Output:** ClickHouse (`portfolio_value`, `performance_metrics`, `trade_analysis`) + NATS (alerts)
**Messaging:** NATS only (real-time monitoring)
**Metrics:** Sharpe, Sortino, Calmar, drawdown, win rate, profit factor

**Dependencies:**
- **Upstream**: execution (fills via NATS)
- **Downstream**: notification-hub (alert routing), dashboard (visualizations)
- **Infrastructure**: ClickHouse, NATS cluster

## Key Capabilities

- Real-time equity curve tracking
- Risk-adjusted return metrics (Sharpe, Sortino, Calmar)
- Drawdown monitoring and alerts
- Win rate and profit factor calculation
- Trade statistics analysis (avg win/loss, R-multiples)
- Performance alerts (drawdown, daily loss limits)
- Historical performance tracking

## Architecture

### Data Flow

```
NATS: orders.filled.> (subscribe from execution)
  ↓
performance-monitoring
  ├─→ Update equity curve
  ├─→ Calculate metrics (Sharpe, drawdown, win rate)
  ├─→ Check alert thresholds
  ├─→ Analyze trades
  ↓
├─→ ClickHouse.portfolio_value (equity curve)
├─→ ClickHouse.performance_metrics (Sharpe, Sortino, etc.)
├─→ ClickHouse.trade_analysis (statistics)
└─→ NATS: performance.alert.{type} (alerts)
```

### Performance Metrics

**1. Risk-Adjusted Returns:**

**Sharpe Ratio:**
```
Sharpe = (Portfolio Return - Risk-Free Rate) / StdDev(Returns)
```
- **Good**: > 1.0
- **Excellent**: > 2.0

**Sortino Ratio:**
```
Sortino = (Portfolio Return - Risk-Free Rate) / Downside StdDev
```
- Better than Sharpe (only penalizes downside volatility)

**Calmar Ratio:**
```
Calmar = CAGR / Max Drawdown
```
- **Good**: > 3.0

**2. Drawdown Metrics:**

**Max Drawdown:**
```
Max DD = (Peak Equity - Trough Equity) / Peak Equity
```

**Current Drawdown:**
```
Current DD = (Peak Equity - Current Equity) / Peak Equity
```

**Drawdown Duration:**
- Days since last equity peak

**3. Win Rate Metrics:**

**Win Rate:**
```
Win Rate % = (Winning Trades / Total Trades) * 100
```

**Profit Factor:**
```
Profit Factor = Gross Profit / Gross Loss
```
- **Good**: > 1.5
- **Excellent**: > 2.0

**4. Trade Statistics:**

**Average Win/Loss:**
```
Avg Win = Sum(Profitable Trades) / Count(Profitable Trades)
Avg Loss = Sum(Losing Trades) / Count(Losing Trades)
```

**Expectancy:**
```
Expectancy = (Win Rate * Avg Win) - (Loss Rate * Avg Loss)
```

**R-Multiple:**
```
R-Multiple = Profit / Initial Risk
```

### Configuration

**Operational Config (Central Hub):**
```json
{
  "operational": {
    "metrics_calculation": {
      "risk_free_rate": 0.04,
      "calculation_period_days": 30,
      "min_trades_for_metrics": 20
    },
    "alerts": {
      "enabled": true,
      "max_drawdown_pct": 0.15,
      "daily_loss_limit_pct": 0.05,
      "min_sharpe_ratio": 1.0,
      "min_win_rate_pct": 0.45
    },
    "equity_curve": {
      "update_interval_seconds": 60,
      "starting_capital": 10000
    },
    "trade_analysis": {
      "group_by_symbol": true,
      "group_by_timeframe": true,
      "calculate_r_multiples": true
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
    service_name="performance-monitoring",
    safe_defaults={
        "operational": {
            "alerts": {"max_drawdown_pct": 0.15},
            "metrics_calculation": {"risk_free_rate": 0.04}
        }
    }
)
await client.init_async()

# Get config
config = await client.get_config()
max_dd = config['operational']['alerts']['max_drawdown_pct']
risk_free = config['operational']['metrics_calculation']['risk_free_rate']
print(f"Max drawdown alert: {max_dd*100}%, Risk-free rate: {risk_free*100}%")
```

### Example 2: Calculate Sharpe Ratio

```python
from performance_monitor import MetricsCalculator

calculator = MetricsCalculator()

# Calculate Sharpe ratio (last 30 days)
sharpe = await calculator.calculate_sharpe(
    period_days=30,
    risk_free_rate=0.04
)

# Calculation:
# 1. Get daily returns from portfolio_value
# 2. Calculate average return
# 3. Calculate std dev of returns
# 4. Sharpe = (avg_return - risk_free) / std_dev

print(f"Sharpe Ratio (30d): {sharpe:.2f}")

# Alert if below threshold
if sharpe < 1.0:
    await send_alert("performance.alert.low_sharpe", sharpe)
```

### Example 3: Track Equity Curve

```python
from performance_monitor import EquityTracker

tracker = EquityTracker()

# Update equity on each fill
async def on_fill(fill_event):
    # Calculate new equity
    new_equity = await tracker.calculate_equity(
        cash=fill_event['cash_balance'],
        open_positions=fill_event['positions'],
        unrealized_pnl=fill_event['unrealized_pnl']
    )

    # Save to database
    await tracker.save_equity_snapshot(
        timestamp=fill_event['timestamp'],
        equity=new_equity,
        cash=fill_event['cash_balance'],
        unrealized_pnl=fill_event['unrealized_pnl']
    )

    # Check for new peak
    if new_equity > tracker.peak_equity:
        tracker.peak_equity = new_equity
        tracker.peak_timestamp = fill_event['timestamp']

    # Calculate current drawdown
    current_dd = (tracker.peak_equity - new_equity) / tracker.peak_equity

    # Alert if exceeds limit
    if current_dd > 0.15:  # 15% max drawdown
        await send_alert("performance.alert.drawdown_limit", current_dd)
```

### Example 4: Query Performance Metrics

```sql
-- Check recent performance metrics
SELECT
    date,
    sharpe_ratio,
    sortino_ratio,
    max_drawdown_pct,
    current_drawdown_pct,
    win_rate_pct,
    profit_factor,
    total_trades
FROM performance_metrics
WHERE date >= CURRENT_DATE - INTERVAL 30 DAY
ORDER BY date DESC;

-- Equity curve (last 7 days)
SELECT
    timestamp,
    equity,
    cash,
    unrealized_pnl,
    (equity - LAG(equity) OVER (ORDER BY timestamp)) / LAG(equity) OVER (ORDER BY timestamp) * 100 as daily_return_pct
FROM portfolio_value
WHERE timestamp >= now() - INTERVAL 7 DAY
ORDER BY timestamp;

-- Trade analysis by symbol
SELECT
    symbol,
    COUNT(*) as total_trades,
    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
    (SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as win_rate_pct,
    AVG(CASE WHEN pnl > 0 THEN pnl END) as avg_win,
    AVG(CASE WHEN pnl < 0 THEN pnl END) as avg_loss,
    SUM(CASE WHEN pnl > 0 THEN pnl ELSE 0 END) / ABS(SUM(CASE WHEN pnl < 0 THEN pnl ELSE 0 END)) as profit_factor
FROM trade_analysis
WHERE closed_at >= CURRENT_DATE - INTERVAL 30 DAY
GROUP BY symbol
ORDER BY profit_factor DESC;
```

### Example 5: Generate Performance Alert

```python
from performance_monitor import AlertManager

alert_mgr = AlertManager()

# Check all alert conditions
async def check_alerts():
    metrics = await calculator.get_current_metrics()

    # Drawdown alert
    if metrics['current_drawdown_pct'] > 0.15:
        await alert_mgr.send_alert(
            alert_type="drawdown_limit",
            severity="critical",
            message=f"Drawdown {metrics['current_drawdown_pct']*100:.1f}% exceeds 15% limit",
            data=metrics
        )

    # Daily loss alert
    if metrics['daily_pnl_pct'] < -0.05:
        await alert_mgr.send_alert(
            alert_type="daily_loss_limit",
            severity="high",
            message=f"Daily loss {metrics['daily_pnl_pct']*100:.1f}% exceeds 5% limit",
            data=metrics
        )

    # Low Sharpe alert
    if metrics['sharpe_ratio'] < 1.0:
        await alert_mgr.send_alert(
            alert_type="low_sharpe",
            severity="medium",
            message=f"Sharpe ratio {metrics['sharpe_ratio']:.2f} below 1.0 threshold",
            data=metrics
        )
```

## Guidelines

- **ALWAYS** use ConfigClient for operational settings (alert thresholds, metrics periods)
- **NEVER** use forward-looking data (prevent look-ahead bias)
- **ALWAYS** update equity curve in real-time
- **VERIFY** performance calculations match industry standards
- **ENSURE** alerts trigger before catastrophic loss
- **VALIDATE** trade analysis matches executed orders

## Critical Rules

1. **Config Hierarchy:**
   - Alert thresholds, metrics periods → Central Hub (operational config)
   - Safe defaults → ConfigClient fallback
   - No secrets needed

2. **No Look-Ahead Bias:**
   - **NEVER** use forward-looking data in metrics
   - **ONLY** use realized PnL for calculations
   - **VERIFY** timestamp ordering correct

3. **Equity Curve Accuracy:**
   - **UPDATE** in real-time (every fill)
   - **INCLUDE** unrealized PnL
   - **TRACK** peak equity for drawdown

4. **Alert Timing (Early Warning):**
   - **TRIGGER** before catastrophic loss
   - **SEND** to notification-hub immediately
   - **LOG** all alert events

5. **Metric Calculation Standards:**
   - **USE** industry-standard formulas
   - **VERIFY** calculations match benchmarks
   - **DOCUMENT** any deviations

## Common Tasks

### Set Up Performance Alerts
1. Define alert thresholds (drawdown, daily loss)
2. Update config via Central Hub API
3. Test with historical data
4. Verify alert delivery to notification-hub
5. Monitor alert frequency

### Calculate Win Rate
1. Query trade_analysis for closed trades
2. Count winning vs losing trades
3. Calculate percentage
4. Compare to target (> 45%)
5. Analyze losing trades for patterns

### Monitor Drawdown
1. Track equity curve daily
2. Calculate current drawdown from peak
3. Set max drawdown threshold
4. Alert when approaching limit
5. Implement stop-trading logic if breached

### Generate Performance Report
1. Query performance_metrics for period
2. Calculate all standard metrics
3. Include equity curve chart
4. Add trade statistics
5. Export to PDF or dashboard

## Troubleshooting

### Issue 1: Sharpe Ratio Calculation Incorrect
**Symptoms:** Unrealistic Sharpe values
**Solution:**
- Verify daily returns calculation
- Check risk-free rate (should be annual, not daily)
- Review std dev calculation (population vs sample)
- Test with known benchmark data
- Ensure sufficient trade history (min 20 trades)

### Issue 2: Equity Curve Not Updating
**Symptoms:** Stale equity values
**Solution:**
- Check NATS subscription to `orders.filled.>`
- Verify fill events being received
- Review equity calculation logic
- Test update interval (should be real-time)
- Check database write permissions

### Issue 3: Drawdown Alerts Not Firing
**Symptoms:** Exceeding threshold without alert
**Solution:**
- Verify alert enabled in config
- Check threshold settings (not too high?)
- Review peak equity tracking
- Test alert logic manually
- Check NATS publishing to notification-hub

### Issue 4: Metrics Don't Match Broker
**Symptoms:** Performance differs from broker reports
**Solution:**
- Check if including unrealized PnL (broker may not)
- Verify commission and spread calculations
- Review timestamp alignment (timezone issues?)
- Compare trade-by-trade
- Check for missing fills

### Issue 5: Win Rate Seems Too High/Low
**Symptoms:** Unrealistic win rate percentage
**Solution:**
- Verify trade counting logic (only closed trades?)
- Check PnL calculation (including costs?)
- Review trade classification (what's a "win"?)
- Compare to individual trade records
- Test with known sample data

## Validation Checklist

After making changes to this service:
- [ ] NATS subscribes to `orders.filled.>` (real-time fills)
- [ ] Equity curve updated (portfolio_value table)
- [ ] Metrics calculated correctly (verify formulas)
- [ ] Alerts published to NATS (performance.alert.*)
- [ ] Trade analysis matches executions (reconciliation)
- [ ] Sharpe ratio reasonable (0.5 - 3.0 range typical)
- [ ] Drawdown calculation accurate
- [ ] Win rate matches actual trades
- [ ] ConfigClient fetching from Central Hub
- [ ] Hot-reload responding to config updates

## Related Skills

- `central-hub` - Provides operational config and service discovery
- `execution` - Provides fills via NATS for metrics
- `risk-management` - Uses metrics for risk limits
- `notification-hub` - Receives performance alerts
- `dashboard` - Visualizes equity curve and metrics

## References

- Full Documentation: `docs/SERVICE_ARCHITECTURE_AND_FLOW.md` (lines 659-698)
- Planning Guide: `docs/PLANNING_SKILL_GUIDE.md` (Service 13, lines 2052-2250)
- Flow + Messaging: `docs/SERVICE_FLOW_TREE_WITH_MESSAGING.md` (lines 635-677)
- Database Schema: `docs/table_database_trading.md` (portfolio_value, performance_metrics tables)
- Config Architecture: `docs/CONFIG_ARCHITECTURE.md`
- Central Hub Skill: `.claude/skills/central-hub/SKILL.md`
- Code: `05-supporting-services/performance-monitoring/`

---

**Created:** 2025-10-19
**Version:** 1.0.0
**Status:** To Build
