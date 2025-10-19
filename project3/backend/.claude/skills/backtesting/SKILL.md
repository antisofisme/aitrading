---
name: backtesting
description: Historical simulation engine for testing trading strategies on past data with walk-forward validation, Monte Carlo simulation, and realistic transaction costs before live deployment
license: MIT
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
metadata:
  type: Supporting Services (Strategy Validation)
  phase: Supporting Services (Phase 4)
  status: To Implement
  priority: P2 (High - validate before live)
  port: 8015
  dependencies:
    - central-hub
    - clickhouse
    - nats
  version: 1.0.0
---

# Backtesting Engine Service

Historical simulation engine for testing trading strategies on historical data with walk-forward validation, Monte Carlo simulation, and realistic transaction costs to validate strategies before live deployment.

## When to Use This Skill

Use this skill when:
- Testing ML models on historical data
- Validating trading strategies before live deployment
- Implementing walk-forward analysis
- Running Monte Carlo simulations
- Calculating realistic performance metrics
- Debugging strategy logic with historical replay

## Service Overview

**Type:** Supporting Services (Strategy Backtesting)
**Port:** 8015
**Input:** ClickHouse (`historical_aggregates`, `ml_features`, `model_checkpoints`)
**Output:** ClickHouse (`backtest_results`) + NATS (status events)
**Methods:** Historical replay, walk-forward, Monte Carlo
**Data Range:** Full historical dataset (2+ years)

**Dependencies:**
- **Upstream**: feature-engineering (historical ml_features), training services (models)
- **Downstream**: None (writes results to ClickHouse)
- **Infrastructure**: ClickHouse, NATS cluster

## Key Capabilities

- Historical data replay simulation
- Walk-forward validation
- Monte Carlo simulation for risk assessment
- Realistic transaction cost modeling
- Slippage simulation
- Complete performance metrics
- Look-ahead bias prevention
- Strategy optimization

## Architecture

### Data Flow

```
ClickHouse.historical_aggregates (candles)
  +
ClickHouse.ml_features (features)
  +
ClickHouse.model_checkpoints (models/strategies to test)
  ↓
backtesting-engine
  ├─→ Load historical data (time-series order)
  ├─→ Replay strategy execution
  ├─→ Simulate fills with slippage
  ├─→ Calculate transaction costs
  ├─→ Track hypothetical P&L
  ↓
├─→ ClickHouse.backtest_results (performance metrics)
├─→ ClickHouse.backtest_trades (trade-by-trade log)
└─→ NATS: backtest.completed.{run_id} (status)
```

### Backtesting Methods

**1. Historical Simulation:**
- Replay historical data in chronological order
- Execute strategy rules at each time step
- Track hypothetical positions and P&L
- Prevent look-ahead bias (strict time ordering)

**2. Walk-Forward Testing:**
```
Train Period: 2020-01-01 to 2020-06-30 (6 months)
Test Period:  2020-07-01 to 2020-09-30 (3 months)
  ↓ (Roll forward)
Train Period: 2020-03-01 to 2020-08-31 (6 months)
Test Period:  2020-09-01 to 2020-11-30 (3 months)
  ↓ (Repeat)
...
```
- Mimics production deployment
- Prevents overfitting
- More realistic than static train/test split

**3. Monte Carlo Simulation:**
- Random resampling of historical trades
- Generate 1000+ alternate scenarios
- Calculate confidence intervals
- Estimate risk of ruin probability

### Transaction Cost Model

```python
# Realistic cost calculation
cost = (
    spread_cost +           # Bid-ask spread
    commission_cost +       # Broker commission
    slippage_cost +         # Market impact
    swap_cost               # Overnight financing
)

# Example for EURUSD 0.01 lots
spread = 2 pips = $2
commission = $0.50 per lot = $0.05 (0.01 lots)
slippage = 0.5 pips avg = $0.50
swap = $0.10 per day
Total = $3.15 per round-trip trade
```

### Configuration

**Operational Config (Central Hub):**
```json
{
  "operational": {
    "data_settings": {
      "start_date": "2020-01-01",
      "end_date": "2024-12-31",
      "symbols": ["EURUSD", "XAUUSD"],
      "timeframes": ["5m", "15m", "1h"]
    },
    "transaction_costs": {
      "spread_pips": 2.0,
      "commission_per_lot": 0.50,
      "slippage_pips": 0.5,
      "swap_per_day": 0.10
    },
    "walk_forward": {
      "enabled": true,
      "train_period_months": 6,
      "test_period_months": 3,
      "step_months": 3
    },
    "monte_carlo": {
      "enabled": false,
      "num_simulations": 1000,
      "confidence_level": 0.95
    },
    "initial_capital": 10000,
    "position_size_pct": 0.02
  }
}
```

## Examples

### Example 1: Fetch Config from Central Hub

```python
from shared.components.config import ConfigClient

# Initialize client
client = ConfigClient(
    service_name="backtesting",
    safe_defaults={
        "operational": {
            "initial_capital": 10000,
            "transaction_costs": {"spread_pips": 2.0}
        }
    }
)
await client.init_async()

# Get config
config = await client.get_config()
start_date = config['operational']['data_settings']['start_date']
capital = config['operational']['initial_capital']
print(f"Backtest from {start_date} with ${capital} capital")
```

### Example 2: Run Historical Backtest

```python
from backtesting_engine import Backtester

backtester = Backtester()

# Load model to test
model = await load_model_from_checkpoint("xgboost-eurusd-v1.2.3")

# Load historical data
historical_data = await load_historical_data(
    symbol="EURUSD",
    timeframe="5m",
    start_date="2020-01-01",
    end_date="2024-12-31"
)

# Run backtest
results = await backtester.run(
    model=model,
    data=historical_data,
    initial_capital=10000,
    transaction_costs=config['transaction_costs']
)

# Results:
# {
#   "total_return_pct": 45.2,
#   "sharpe_ratio": 1.85,
#   "max_drawdown_pct": -12.3,
#   "win_rate_pct": 58.5,
#   "total_trades": 523,
#   "profit_factor": 1.92
# }
```

### Example 3: Walk-Forward Validation

```python
from backtesting_engine import WalkForwardTester

wf_tester = WalkForwardTester()

# Run walk-forward
results = await wf_tester.run(
    model_class="xgboost",
    symbol="EURUSD",
    timeframe="5m",
    train_period_months=6,
    test_period_months=3,
    step_months=3,
    start_date="2020-01-01",
    end_date="2024-12-31"
)

# Results per fold:
# [
#   {"fold": 1, "test_sharpe": 1.82, "test_return": 8.5},
#   {"fold": 2, "test_sharpe": 1.65, "test_return": 6.2},
#   {"fold": 3, "test_sharpe": 2.01, "test_return": 11.3},
#   ...
# ]

print(f"Avg test Sharpe: {np.mean([r['test_sharpe'] for r in results]):.2f}")
```

### Example 4: Monte Carlo Simulation

```python
from backtesting_engine import MonteCarloSimulator

mc_sim = MonteCarloSimulator()

# Get trade history from backtest
trade_history = results['trades']

# Run Monte Carlo
mc_results = await mc_sim.run(
    trades=trade_history,
    num_simulations=1000,
    initial_capital=10000
)

# Results:
# {
#   "median_return": 42.5,
#   "confidence_95_lower": 18.2,  # 95% chance of at least 18.2% return
#   "confidence_95_upper": 68.9,  # 95% chance of at most 68.9% return
#   "risk_of_ruin_pct": 2.3       # 2.3% chance of losing 50%+ of capital
# }
```

### Example 5: Query Backtest Results

```sql
-- Check recent backtests
SELECT
    run_id,
    strategy_name,
    symbol,
    timeframe,
    start_date,
    end_date,
    total_return_pct,
    sharpe_ratio,
    max_drawdown_pct,
    win_rate_pct,
    total_trades
FROM backtest_results
ORDER BY created_at DESC
LIMIT 10;

-- Compare strategies
SELECT
    strategy_name,
    AVG(sharpe_ratio) as avg_sharpe,
    AVG(max_drawdown_pct) as avg_max_dd,
    AVG(win_rate_pct) as avg_win_rate
FROM backtest_results
GROUP BY strategy_name
ORDER BY avg_sharpe DESC;
```

## Guidelines

- **ALWAYS** use ConfigClient for operational settings (capital, costs)
- **NEVER** use live data for backtesting (historical only!)
- **ALWAYS** prevent look-ahead bias (strict time-series order)
- **VERIFY** transaction costs included (slippage, commission)
- **ENSURE** walk-forward validation (mimics production)
- **VALIDATE** results match expected performance

## Critical Rules

1. **Config Hierarchy:**
   - Transaction costs, capital → Central Hub (operational config)
   - Safe defaults → ConfigClient fallback
   - No secrets needed

2. **No Look-Ahead Bias (CRITICAL):**
   - **NEVER** use future data in past decisions
   - **ENFORCE** strict timestamp ordering
   - **VERIFY** features calculated with data available at time

3. **Realistic Costs (Mandatory):**
   - **INCLUDE** spread, commission, slippage
   - **MODEL** swap costs for overnight positions
   - **ACCOUNT** for market impact on large orders

4. **Walk-Forward Validation:**
   - **USE** rolling windows (train → test → roll)
   - **PREVENT** overfitting to single period
   - **MIMIC** production deployment process

5. **Result Validation:**
   - **CHECK** metrics reasonable (Sharpe 0.5-3.0 typical)
   - **VERIFY** trade count sufficient (>30 trades)
   - **COMPARE** to buy-and-hold benchmark

## Common Tasks

### Run Simple Backtest
1. Load model from checkpoint
2. Load historical data (candles + features)
3. Configure initial capital and costs
4. Run simulation in time-series order
5. Calculate performance metrics

### Optimize Strategy Parameters
1. Define parameter grid to search
2. Run backtest for each combination
3. Track performance metrics
4. Select best parameters by Sharpe ratio
5. Validate with walk-forward

### Compare Multiple Strategies
1. Define strategies to test (models, rules)
2. Run each on same historical period
3. Calculate standardized metrics
4. Compare risk-adjusted returns
5. Select best strategy for live deployment

### Estimate Risk of Ruin
1. Run backtest to get trade history
2. Monte Carlo simulation (1000+ runs)
3. Calculate probability of X% loss
4. Review confidence intervals
5. Adjust position sizing if needed

## Troubleshooting

### Issue 1: Unrealistic Backtest Performance
**Symptoms:** Sharpe ratio > 3.0, win rate > 70%
**Solution:**
- Check for look-ahead bias (using future data?)
- Verify transaction costs included
- Review feature calculation (leakage?)
- Test on out-of-sample period
- Compare to simpler baseline

### Issue 2: Backtest Too Slow
**Symptoms:** > 1 hour for 1 year of data
**Solution:**
- Reduce data granularity (use 15m instead of 1m)
- Optimize feature calculation (vectorize)
- Use sampling (test on subset first)
- Parallelize across symbols
- Cache intermediate results

### Issue 3: Walk-Forward Results Inconsistent
**Symptoms:** High variance across folds
**Solution:**
- Increase train period (more data)
- Check for regime changes (market conditions)
- Review parameter stability
- Test on multiple symbols
- Consider ensemble methods

### Issue 4: Monte Carlo Shows High Risk of Ruin
**Symptoms:** > 10% chance of losing 50%
**Solution:**
- Reduce position sizing (2% → 1% risk per trade)
- Tighten stop-losses
- Improve win rate or profit factor
- Add risk management rules
- Test different strategies

### Issue 5: Backtest Results Don't Match Live
**Symptoms:** Live performance much worse than backtest
**Solution:**
- Check slippage modeling (too optimistic?)
- Verify commission costs correct
- Review order fill assumptions
- Test during similar market conditions
- Add execution delay simulation

## Validation Checklist

After making changes to this service:
- [ ] Historical data loaded (aggregates + ml_features)
- [ ] Model/strategy defined correctly
- [ ] Backtest runs without look-ahead bias (timestamp ordering)
- [ ] Transaction costs included (spread + commission + slippage)
- [ ] Results saved to ClickHouse.backtest_results
- [ ] NATS publishes completion status
- [ ] Walk-forward validation working (if enabled)
- [ ] Monte Carlo simulation accurate (if enabled)
- [ ] ConfigClient fetching from Central Hub
- [ ] Hot-reload responding to config updates

## Related Skills

- `central-hub` - Provides operational config and service discovery
- `supervised-training` - Provides models to backtest
- `finrl-training` - Provides RL agents to backtest
- `feature-engineering` - Provides historical features
- `performance-monitoring` - Similar metrics calculation

## References

- Full Documentation: `docs/SERVICE_ARCHITECTURE_AND_FLOW.md` (lines 726-749)
- Planning Guide: `docs/PLANNING_SKILL_GUIDE.md` (Service 15, lines 2452-2650)
- Flow + Messaging: `docs/SERVICE_FLOW_TREE_WITH_MESSAGING.md` (lines 723-753)
- Database Schema: TBD (backtest_results table to be designed)
- Config Architecture: `docs/CONFIG_ARCHITECTURE.md`
- Central Hub Skill: `.claude/skills/central-hub/SKILL.md`
- Code: `05-supporting-services/backtesting-engine/`

---

**Created:** 2025-10-19
**Version:** 1.0.0
**Status:** To Implement
