# Skill: backtesting-engine Service

## Purpose
Historical simulation engine. Test trading strategies on historical data before live deployment.

## Key Facts
- **Phase**: Supporting Services (Phase 4)
- **Status**: ⚠️ To Implement
- **Priority**: P2 (High - validate strategies before live trading)
- **Function**: Historical simulation, walk-forward testing, Monte Carlo
- **Data**: Uses historical_aggregates + ml_features

## Data Flow
```
ClickHouse.historical_aggregates (historical candles)
ClickHouse.ml_features (historical features)
ClickHouse.model_checkpoints (models to test)
  → backtesting-engine (simulate trading strategy)
  → ClickHouse.backtest_results
  → NATS: backtest.completed.{run_id} (status)
```

## Messaging
- **NATS Publish**: `backtest.started.*`, `backtest.progress.*`, `backtest.completed.*`
- **Pattern**: Status events only (batch processing, no streaming)

## Dependencies
- **Upstream**: feature-engineering-service (historical ml_features), training services (models to test)
- **Downstream**: None (writes results to ClickHouse)
- **Infrastructure**: ClickHouse, NATS cluster

## Critical Rules
1. **NEVER** use live data for backtesting (historical only!)
2. **ALWAYS** prevent look-ahead bias (strict time-series order)
3. **VERIFY** transaction costs included (slippage, commission)
4. **ENSURE** walk-forward validation (mimics production)
5. **VALIDATE** results match expected performance (sanity checks)

## Backtesting Methods
### Historical Simulation
- Replay historical data
- Execute strategy rules
- Track hypothetical P&L

### Walk-Forward Testing
- Train on period A, test on period B
- Rolling window (mimics production deployment)
- Prevents overfitting

### Monte Carlo Simulation
- Random resampling of trades
- Estimate risk of ruin
- Confidence intervals for returns

## Performance Metrics
- Sharpe ratio, Sortino ratio
- Max drawdown, avg drawdown
- Win rate, profit factor
- Total return, CAGR
- Number of trades
- Avg holding period

## Validation
When working on this service, ALWAYS verify:
- [ ] Historical data loaded (aggregates + ml_features)
- [ ] Model/strategy defined correctly
- [ ] Backtest runs without look-ahead bias (check timestamp ordering)
- [ ] Transaction costs included (slippage + commission)
- [ ] Results saved to ClickHouse.backtest_results
- [ ] NATS publishes completion status

## Reference Docs

**Service Documentation:**
- Planning guide: `PLANNING_SKILL_GUIDE.md` (Service 15, lines 2452-2650)
- Architecture: `SERVICE_ARCHITECTURE_AND_FLOW.md` (lines 726-749)
- Flow + messaging: `SERVICE_FLOW_TREE_WITH_MESSAGING.md` (lines 723-753)
- Database schema: TBD (backtest_results table to be designed)

**Operational Skills (Central-Hub Agent Tools):**
- 🔍 Debug issues: `.claude/skills/central-hub-debugger/`
- 🔧 Fix problems: `.claude/skills/central-hub-fixer/`
- ➕ Create new service: `.claude/skills/central-hub-service-creator/`
