---
name: risk-management
description: Risk validation gate that validates trading signals against position limits, portfolio constraints, and calculates optimal position sizing before execution approval
license: MIT
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
metadata:
  type: Trading (Risk Management)
  phase: Live Trading (Phase 3)
  status: To Implement
  priority: P2 (High - prevents catastrophic losses)
  port: 8011
  dependencies:
    - central-hub
    - clickhouse
    - nats
    - kafka
  version: 1.0.0
---

# Risk Management Service

Risk validation gate that validates all trading signals against position limits, portfolio constraints, and calculates optimal position sizing using Kelly Criterion or Fixed Fractional method before approving for execution.

## When to Use This Skill

Use this skill when:
- Implementing position sizing algorithms
- Setting up risk limits (position, portfolio, daily loss)
- Debugging signal rejections
- Calculating Kelly Criterion or Fixed Fractional sizing
- Monitoring portfolio heat and exposure
- Implementing drawdown protection

## Service Overview

**Type:** Trading (Risk Management)
**Port:** 8011
**Input:** NATS (`signals.>` from inference) + ClickHouse (portfolio state)
**Output:** ClickHouse (`risk_events`) + NATS (`signals.approved.*`, `signals.rejected.*`) + Kafka
**Function:** Position sizing, limit validation, approval/rejection
**Methods:** Kelly Criterion, Fixed Fractional, ATR-based stops

**Dependencies:**
- **Upstream**: inference (trading signals via NATS)
- **Downstream**: execution (consumes approved signals)
- **Infrastructure**: ClickHouse, NATS cluster, Kafka

## Key Capabilities

- Position limit validation
- Portfolio limit validation
- Position sizing (Kelly Criterion, Fixed Fractional)
- Risk/reward ratio validation
- Correlation checks (avoid overexposure)
- Drawdown protection
- Signal approval/rejection workflow
- Risk event logging and audit trail

## Architecture

### Data Flow

```
NATS: signals.> (subscribe from inference)
  ↓
risk-management
  ├─→ Load current portfolio from ClickHouse
  ├─→ Validate position limits
  ├─→ Validate portfolio limits
  ├─→ Calculate position size (Kelly/Fixed Fractional)
  ├─→ Check correlation exposure
  ├─→ Validate risk/reward ratio
  ↓
Decision: APPROVE or REJECT
  ↓
├─→ ClickHouse.trading_signals (update: approved/rejected)
├─→ ClickHouse.risk_events (log violations)
├─→ NATS: signals.approved.{symbol} (if approved)
├─→ NATS: signals.rejected.{symbol} (if rejected)
└─→ Kafka: risk_events_archive (audit trail)
```

### Risk Checks

**1. Position Limits:**
- Max position size per symbol (e.g., 2% of capital)
- Max concurrent positions (e.g., 5 positions)
- Max exposure per symbol (e.g., $1000)

**2. Portfolio Limits:**
- Max total exposure (e.g., 20% of capital)
- Max daily loss (e.g., 5% of capital)
- Max drawdown from peak (e.g., 15%)
- Portfolio heat (sum of all position risks)

**3. Correlation Limits:**
- Max correlated positions (e.g., EURUSD + GBPUSD = 2 max)
- Currency exposure limits

**4. Risk/Reward:**
- Min risk/reward ratio (e.g., 1:2)
- Stop-loss within acceptable range

### Position Sizing Methods

**1. Kelly Criterion:**
```
Kelly% = (Win% * AvgWin - Loss% * AvgLoss) / AvgWin
Position Size = Kelly% * Capital
```

**2. Fixed Fractional:**
```
Risk% = 1-2% of capital per trade
Position Size = (Capital * Risk%) / (Entry - StopLoss)
```

**3. ATR-based:**
```
Stop Distance = ATR * Multiplier
Position Size = (Capital * Risk%) / Stop Distance
```

### Configuration

**Operational Config (Central Hub):**
```json
{
  "operational": {
    "position_limits": {
      "max_position_size_pct": 0.02,
      "max_concurrent_positions": 5,
      "max_exposure_per_symbol": 1000
    },
    "portfolio_limits": {
      "max_total_exposure_pct": 0.20,
      "max_daily_loss_pct": 0.05,
      "max_drawdown_pct": 0.15,
      "max_portfolio_heat": 0.10
    },
    "correlation_limits": {
      "max_correlated_positions": 2,
      "correlation_threshold": 0.7
    },
    "position_sizing": {
      "method": "fixed_fractional",
      "risk_per_trade_pct": 0.01,
      "kelly_fraction": 0.25,
      "min_position_size": 0.01,
      "max_position_size": 1.0
    },
    "risk_reward": {
      "min_rr_ratio": 2.0,
      "require_sl_tp": true
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
    service_name="risk-management",
    safe_defaults={
        "operational": {
            "position_limits": {"max_position_size_pct": 0.02},
            "position_sizing": {"method": "fixed_fractional", "risk_per_trade_pct": 0.01}
        }
    }
)
await client.init_async()

# Get config
config = await client.get_config()
max_position_pct = config['operational']['position_limits']['max_position_size_pct']
risk_pct = config['operational']['position_sizing']['risk_per_trade_pct']
print(f"Max position: {max_position_pct*100}%, Risk per trade: {risk_pct*100}%")
```

### Example 2: Validate Signal Against Limits

```python
from risk_manager import RiskManager

risk_mgr = RiskManager()

# Receive signal from inference
signal = {
    "symbol": "EURUSD",
    "signal_type": "buy",
    "entry_price": 1.08125,
    "stop_loss": 1.08000,
    "take_profit": 1.08500,
    "confidence_score": 0.85
}

# Load current portfolio
portfolio = await risk_mgr.get_portfolio_state()

# Validate signal
validation_result = await risk_mgr.validate_signal(signal, portfolio)

# Result:
# {
#   "approved": True/False,
#   "reason": "..." if rejected,
#   "position_size": 0.01,  # Calculated size
#   "checks": {
#     "position_limit": "pass",
#     "portfolio_limit": "pass",
#     "correlation_limit": "pass",
#     "rr_ratio": "pass"
#   }
# }
```

### Example 3: Calculate Position Size (Fixed Fractional)

```python
from risk_manager import PositionSizer

sizer = PositionSizer(method="fixed_fractional")

# Calculate position size
position_size = await sizer.calculate_size(
    capital=10000,
    risk_pct=0.01,  # 1% risk
    entry_price=1.08125,
    stop_loss=1.08000,
    symbol="EURUSD"
)

# Result: 0.08 lots
# Calculation:
# Risk$ = 10000 * 0.01 = $100
# Stop distance = 1.08125 - 1.08000 = 0.00125 = 12.5 pips
# Position size = $100 / (12.5 pips * $10/pip) = 0.08 lots
```

### Example 4: Calculate Kelly Criterion

```python
from risk_manager import KellyCriterion

kelly = KellyCriterion()

# Calculate Kelly% based on backtest stats
kelly_pct = await kelly.calculate(
    win_rate=0.60,       # 60% winning trades
    avg_win=150,         # Average win $150
    avg_loss=75,         # Average loss $75
    kelly_fraction=0.25  # Conservative (25% of full Kelly)
)

# Result: Kelly% = ((0.60 * 150 - 0.40 * 75) / 150) * 0.25
#                = (90 - 30) / 150 * 0.25
#                = 0.40 * 0.25
#                = 0.10 (10% of capital per trade)
```

### Example 5: Query Risk Events

```sql
-- Check recent rejections
SELECT
    event_id,
    signal_id,
    symbol,
    rejection_reason,
    violated_limit,
    timestamp
FROM risk_events
WHERE event_type = 'rejected'
  AND timestamp > now() - INTERVAL 1 DAY
ORDER BY timestamp DESC
LIMIT 20;

-- Calculate rejection rate
SELECT
    COUNT(CASE WHEN event_type = 'approved' THEN 1 END) as approved,
    COUNT(CASE WHEN event_type = 'rejected' THEN 1 END) as rejected,
    (COUNT(CASE WHEN event_type = 'rejected' THEN 1 END) * 100.0 / COUNT(*)) as rejection_rate_pct
FROM risk_events
WHERE timestamp > now() - INTERVAL 7 DAY;
```

## Guidelines

- **ALWAYS** use ConfigClient for operational settings (limits, sizing methods)
- **NEVER** skip risk checks (all signals MUST pass validation)
- **ALWAYS** reject signals violating limits (safety first!)
- **VERIFY** current portfolio state before approval
- **ENSURE** position sizing follows configured method
- **VALIDATE** stop-loss and take-profit levels

## Critical Rules

1. **Config Hierarchy:**
   - Limits, sizing methods → Central Hub (operational config)
   - Safe defaults → ConfigClient fallback
   - No secrets needed

2. **All Signals Must Pass:**
   - **NEVER** skip risk-management (all signals go through)
   - **REJECT** violating signals immediately
   - **LOG** all rejections with reason

3. **Position Sizing (Mandatory):**
   - **CALCULATE** size based on configured method
   - **ENFORCE** min/max position size limits
   - **VALIDATE** size against capital

4. **Portfolio State Accuracy:**
   - **ALWAYS** load current portfolio before validation
   - **VERIFY** position counts accurate
   - **UPDATE** after signal approval

5. **Risk/Reward Validation:**
   - **CHECK** min RR ratio (e.g., 1:2)
   - **REQUIRE** SL and TP levels
   - **REJECT** poor RR ratios

## Common Tasks

### Set Position Limits
1. Determine risk tolerance (conservative, moderate, aggressive)
2. Calculate max position size (% of capital)
3. Update config via Central Hub API
4. Test with sample signals
5. Monitor rejection rate

### Implement Kelly Criterion
1. Gather backtest stats (win rate, avg win/loss)
2. Calculate full Kelly%
3. Apply Kelly fraction (25-50% for safety)
4. Update position sizing config
5. Monitor performance

### Debug High Rejection Rate
1. Query risk_events for rejection reasons
2. Review most common violations
3. Adjust limits if too conservative
4. Check portfolio state accuracy
5. Test edge cases

### Add Correlation Checks
1. Define correlated pairs (EURUSD/GBPUSD, etc.)
2. Set max correlated positions
3. Implement correlation matrix
4. Test with correlated signals
5. Monitor exposure by currency

## Troubleshooting

### Issue 1: All Signals Being Rejected
**Symptoms:** 100% rejection rate
**Solution:**
- Check limits not too strict (e.g., max_position_size_pct too low)
- Verify portfolio state loading correctly
- Review rejection reasons in logs
- Test with known-good signal
- Adjust limits if needed

### Issue 2: Position Sizing Always Min/Max
**Symptoms:** All positions same size
**Solution:**
- Check sizing calculation logic
- Verify ATR or volatility data available
- Review min/max size constraints
- Test calculation manually
- Check for division by zero

### Issue 3: Portfolio Heat Exceeding Limit
**Symptoms:** Valid signals rejected due to heat
**Solution:**
- Close losing positions first
- Reduce max_portfolio_heat limit
- Implement position exit logic
- Check heat calculation correct
- Monitor open positions count

### Issue 4: Correlation Checks Not Working
**Symptoms:** Over-exposed to correlated pairs
**Solution:**
- Verify correlation matrix populated
- Check correlation threshold appropriate
- Review correlation calculation period
- Test with known correlated pairs
- Update correlation data regularly

### Issue 5: Kelly Sizing Too Aggressive
**Symptoms:** Position sizes too large
**Solution:**
- Reduce kelly_fraction (50% → 25%)
- Add max_position_size cap
- Review backtest stats (win rate accurate?)
- Use Fixed Fractional instead
- Test in simulation first

## Validation Checklist

After making changes to this service:
- [ ] NATS subscribes to `signals.>` (all signals from inference)
- [ ] Risk checks applied (position, portfolio, correlation limits)
- [ ] Position size calculated correctly
- [ ] Approved signals published to `signals.approved.*`
- [ ] Rejected signals logged with reason in `risk_events`
- [ ] Kafka archives all risk decisions
- [ ] Portfolio state loading accurately
- [ ] RR ratio validation working
- [ ] ConfigClient fetching from Central Hub
- [ ] Hot-reload responding to config updates

## Related Skills

- `central-hub` - Provides operational config and service discovery
- `inference` - Provides trading signals for validation
- `execution` - Consumes approved signals for order creation
- `performance-monitoring` - Tracks risk metrics and drawdowns

## References

- Full Documentation: `docs/SERVICE_ARCHITECTURE_AND_FLOW.md` (lines 620-656)
- Planning Guide: `docs/PLANNING_SKILL_GUIDE.md` (Service 12, lines 1652-1850)
- Flow + Messaging: `docs/SERVICE_FLOW_TREE_WITH_MESSAGING.md` (lines 527-577)
- Database Schema: `docs/table_database_trading.md` (risk_events table)
- Config Architecture: `docs/CONFIG_ARCHITECTURE.md`
- Central Hub Skill: `.claude/skills/central-hub/SKILL.md`
- Code: `04-trading-execution/risk-management/`

---

**Created:** 2025-10-19
**Version:** 1.0.0
**Status:** To Implement
