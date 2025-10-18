# Skill: execution-service Service

## Purpose
Order management service. Creates orders from approved signals, sends to broker, tracks fills and slippage.

## Key Facts
- **Phase**: Live Trading (Phase 3)
- **Status**: ⚠️ To Implement
- **Priority**: P2 (High - executes trading decisions)
- **Function**: Order creation, broker submission, fill tracking
- **Order types**: Market, Limit, Stop-loss, Take-profit

## Data Flow
```
NATS: signals.approved.> (subscribe from risk-management)
ClickHouse.trading_signals (read approved)
  → execution-service (create orders, send to broker)
  → ClickHouse.orders
  → ClickHouse.executions
  → ClickHouse.positions
  → NATS: orders.{status}.{symbol} (order status updates)
  → Kafka: order_execution_archive (audit trail)
```

## Messaging
- **NATS Subscribe**: `signals.approved.>` (approved signals only from risk-management)
- **NATS Publish**: `orders.pending.*`, `orders.submitted.*`, `orders.filled.*`, `orders.cancelled.*`, `orders.failed.*`
- **Kafka Publish**: `order_execution_archive` (complete order lifecycle)
- **Pattern**: Both NATS + Kafka (critical execution data needs real-time + audit)

## Dependencies
- **Upstream**: risk-management (approved signals via NATS)
- **Downstream**: mt5-connector (sends orders to broker), performance-monitoring (receives fills)
- **Infrastructure**: ClickHouse, NATS cluster, Kafka

## Critical Rules
1. **NEVER** execute rejected signals (only process approved signals!)
2. **ALWAYS** track order state machine (pending → submitted → filled/cancelled)
3. **VERIFY** idempotency (prevent duplicate orders with same signal_id)
4. **ENSURE** slippage tracking (compare fill price vs expected price)
5. **VALIDATE** position updates match order fills (reconciliation)

## Order Lifecycle
1. **Pending**: Order created, not yet submitted
2. **Submitted**: Sent to broker (mt5-connector)
3. **Partially Filled**: Partial execution
4. **Filled**: Complete execution
5. **Cancelled**: Order cancelled (user or system)
6. **Rejected**: Broker rejected order
7. **Failed**: System error

## Order Types
- **Market**: Execute at current market price
- **Limit**: Execute at specified price or better
- **Stop**: Trigger order when price reaches stop level
- **Stop-limit**: Combination of stop + limit

## Validation
When working on this service, ALWAYS verify:
- [ ] NATS subscribes to `signals.approved.>` (approved signals only)
- [ ] Orders created in ClickHouse.orders
- [ ] Order status published to NATS `orders.*.*`
- [ ] Fills tracked in ClickHouse.executions
- [ ] Positions updated in ClickHouse.positions
- [ ] Kafka archives complete order lifecycle

## Reference Docs

**Service Documentation:**
- Planning guide: `PLANNING_SKILL_GUIDE.md` (Service 11, lines 1852-2050)
- Architecture: `SERVICE_ARCHITECTURE_AND_FLOW.md` (lines 579-617)
- Flow + messaging: `SERVICE_FLOW_TREE_WITH_MESSAGING.md` (lines 579-633)
- Database schema: `table_database_trading.md` (orders, executions, positions tables)

**Operational Skills (Central-Hub Agent Tools):**
- 🔍 Debug issues: `.claude/skills/central-hub-debugger/`
- 🔧 Fix problems: `.claude/skills/central-hub-fixer/`
- ➕ Create new service: `.claude/skills/central-hub-service-creator/`
