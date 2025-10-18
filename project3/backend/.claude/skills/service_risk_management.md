# Skill: risk-management Service

## Purpose
Risk validation gate. Validates trading signals against position limits, portfolio constraints before execution.

## Key Facts
- **Phase**: Live Trading (Phase 3)
- **Status**: ⚠️ To Implement
- **Priority**: P2 (High - prevents catastrophic losses)
- **Function**: Position sizing, stop-loss calculation, limit checks
- **Approval**: Approve/reject signals before execution

## Data Flow
```
NATS: signals.> (subscribe from inference-service)
ClickHouse.trading_signals (read)
ClickHouse.positions (current portfolio)
  → risk-management (validate limits, position sizing)
  → ClickHouse.trading_signals (update: approved/rejected)
  → ClickHouse.risk_events (violations)
  → NATS: signals.approved.{symbol} (approved signals only)
  → Kafka: risk_events_archive (compliance)
```

## Messaging
- **NATS Subscribe**: `signals.>` (all signals from inference-service)
- **NATS Publish**: `signals.approved.*` (approved only), `signals.rejected.*` (rejected with reason)
- **Kafka Publish**: `risk_events_archive` (audit log of risk decisions)
- **Pattern**: Both NATS + Kafka (critical risk decisions need real-time + audit)

## Dependencies
- **Upstream**: inference-service (trading signals via NATS)
- **Downstream**: execution-service (consumes approved signals via NATS)
- **Infrastructure**: ClickHouse, NATS cluster, Kafka

## Critical Rules
1. **NEVER** skip risk checks (all signals MUST pass through risk-management)
2. **ALWAYS** reject signals that violate limits (safety first!)
3. **VERIFY** current portfolio state before approval (check existing positions)
4. **ENSURE** position sizing follows Kelly Criterion or Fixed Fractional
5. **VALIDATE** stop-loss and take-profit levels (risk/reward ratio)

## Risk Checks
### Position Limits
- Max position size per symbol (e.g., 2% of capital)
- Max total exposure (e.g., 20% of capital)
- Max correlated positions (e.g., EURUSD + GBPUSD)

### Portfolio Limits
- Max daily loss (e.g., 5% of capital)
- Max drawdown (e.g., 15% from peak)
- Portfolio heat (sum of all risks)

### Position Sizing
- Kelly Criterion (optimal fraction)
- Fixed Fractional (1-2% risk per trade)
- ATR-based stop-loss

## Validation
When working on this service, ALWAYS verify:
- [ ] NATS subscribes to `signals.>` (all signals from inference)
- [ ] Risk checks applied (position limits, portfolio limits)
- [ ] Approved signals published to `signals.approved.*`
- [ ] Rejected signals logged with reason
- [ ] Kafka archives all risk decisions

## Reference Docs

**Service Documentation:**
- Planning guide: `PLANNING_SKILL_GUIDE.md` (Service 12, lines 1652-1850)
- Architecture: `SERVICE_ARCHITECTURE_AND_FLOW.md` (lines 620-656)
- Flow + messaging: `SERVICE_FLOW_TREE_WITH_MESSAGING.md` (lines 527-577)
- Database schema: `table_database_trading.md` (risk_events table)

**Operational Skills (Central-Hub Agent Tools):**
- 🔍 Debug issues: `.claude/skills/central-hub-debugger/`
- 🔧 Fix problems: `.claude/skills/central-hub-fixer/`
- ➕ Create new service: `.claude/skills/central-hub-service-creator/`
