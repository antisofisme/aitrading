---
name: execution
description: Order management service that creates orders from approved signals, sends to broker via MT5 connector, and tracks fills and slippage with complete order lifecycle management
license: MIT
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
metadata:
  type: Trading (Execution)
  phase: Live Trading (Phase 3)
  status: To Implement
  priority: P2 (High - executes trading decisions)
  port: 8012
  dependencies:
    - central-hub
    - clickhouse
    - nats
    - kafka
  version: 1.0.0
---

# Execution Service

Order management service that creates orders from risk-approved signals, sends them to broker via MT5 connector, tracks complete order lifecycle (pending → submitted → filled/cancelled), and monitors fills and slippage.

## When to Use This Skill

Use this skill when:
- Implementing order creation and submission logic
- Tracking order lifecycle (pending, submitted, filled, cancelled)
- Debugging order execution issues
- Monitoring slippage and fill quality
- Reconciling positions with broker
- Implementing idempotency (prevent duplicate orders)

## Service Overview

**Type:** Trading (Order Execution)
**Port:** 8012
**Input:** NATS (`signals.approved.>` from risk-mgmt) + ClickHouse (signals)
**Output:** ClickHouse (`orders`, `executions`, `positions`) + NATS + Kafka
**Function:** Order creation, broker submission, fill tracking
**Order Types:** Market, Limit, Stop, Stop-Limit

**Dependencies:**
- **Upstream**: risk-management (approved signals via NATS)
- **Downstream**: mt5-connector (sends orders), performance-monitoring (receives fills)
- **Infrastructure**: ClickHouse, NATS cluster, Kafka

## Key Capabilities

- Order creation from approved signals
- Order state machine management
- Broker order submission (via MT5 connector)
- Fill tracking and slippage monitoring
- Position reconciliation
- Idempotency (prevent duplicates)
- Order lifecycle audit trail
- Real-time status broadcasting

## Architecture

### Data Flow

```
NATS: signals.approved.> (subscribe from risk-mgmt)
  ↓
execution-service
  ├─→ Create order (check idempotency)
  ├─→ Send to MT5 connector
  ├─→ Track order state
  ├─→ Monitor fills
  ├─→ Calculate slippage
  ↓
├─→ ClickHouse.orders (order metadata)
├─→ ClickHouse.executions (fill details)
├─→ ClickHouse.positions (current holdings)
├─→ NATS: orders.{status}.{symbol} (status updates)
└─→ Kafka: order_execution_archive (audit trail)
```

### Order Lifecycle State Machine

```
PENDING
  ↓ (submit to broker)
SUBMITTED
  ↓ (broker confirms)
  ├─→ PARTIALLY_FILLED
  │     ↓ (more fills)
  │     FILLED
  ├─→ FILLED
  ├─→ CANCELLED
  ├─→ REJECTED
  └─→ FAILED
```

**States:**
1. **PENDING**: Order created, not yet submitted
2. **SUBMITTED**: Sent to broker (mt5-connector)
3. **PARTIALLY_FILLED**: Partial execution
4. **FILLED**: Complete execution
5. **CANCELLED**: Order cancelled (user or system)
6. **REJECTED**: Broker rejected order
7. **FAILED**: System error

### Order Types

| Type | Description | Use Case |
|------|-------------|----------|
| **Market** | Execute at current market price | Immediate execution |
| **Limit** | Execute at specified price or better | Better price guarantee |
| **Stop** | Trigger order when price reaches level | Stop-loss protection |
| **Stop-Limit** | Combination of stop + limit | Price control after trigger |

### Configuration

**Operational Config (Central Hub):**
```json
{
  "operational": {
    "order_defaults": {
      "default_order_type": "market",
      "enable_limit_orders": true,
      "enable_stop_orders": true,
      "max_slippage_pips": 3
    },
    "idempotency": {
      "enabled": true,
      "check_window_hours": 24,
      "dedupe_by": "signal_id"
    },
    "fill_tracking": {
      "track_partial_fills": true,
      "update_interval_seconds": 1,
      "slippage_alert_threshold_pips": 5
    },
    "position_reconciliation": {
      "enabled": true,
      "reconcile_interval_minutes": 5,
      "auto_correct_discrepancies": false
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
    service_name="execution",
    safe_defaults={
        "operational": {
            "order_defaults": {"default_order_type": "market"},
            "idempotency": {"enabled": True}
        }
    }
)
await client.init_async()

# Get config
config = await client.get_config()
order_type = config['operational']['order_defaults']['default_order_type']
max_slippage = config['operational']['order_defaults']['max_slippage_pips']
print(f"Order type: {order_type}, Max slippage: {max_slippage} pips")
```

### Example 2: Create Order from Approved Signal

```python
from execution_service import OrderManager

order_mgr = OrderManager()

# Receive approved signal
signal = {
    "signal_id": "sig_12345",
    "symbol": "EURUSD",
    "signal_type": "buy",
    "entry_price": 1.08125,
    "stop_loss": 1.08000,
    "take_profit": 1.08500,
    "position_size": 0.01
}

# Check idempotency (prevent duplicate orders)
if await order_mgr.order_exists(signal_id="sig_12345"):
    logger.warning(f"Order already exists for signal {signal['signal_id']}")
    return

# Create order
order = await order_mgr.create_order(
    signal=signal,
    order_type="market"
)

# Submit to broker (via MT5 connector)
await order_mgr.submit_order(order)

# Result saved to ClickHouse.orders with state=SUBMITTED
```

### Example 3: Track Order Fills

```python
from execution_service import FillTracker

tracker = FillTracker()

# Monitor order status (callback from MT5 connector)
async def on_fill(fill_event):
    # Update order state
    await tracker.process_fill(
        order_id=fill_event['order_id'],
        fill_price=fill_event['fill_price'],
        fill_quantity=fill_event['fill_quantity'],
        fill_time=fill_event['timestamp']
    )

    # Calculate slippage
    slippage = await tracker.calculate_slippage(
        expected_price=fill_event['expected_price'],
        fill_price=fill_event['fill_price'],
        order_side=fill_event['side']
    )

    # Alert if excessive slippage
    if abs(slippage) > 5:  # 5 pips
        await send_alert(f"High slippage: {slippage} pips")

    # Update position
    await tracker.update_position(fill_event)

# Subscribe to fill events from MT5
await subscribe_fills("mt5.fills.*", callback=on_fill)
```

### Example 4: Query Orders and Executions

```sql
-- Check recent orders
SELECT
    order_id,
    signal_id,
    symbol,
    order_type,
    state,
    entry_price,
    fill_price,
    slippage_pips,
    created_at,
    filled_at
FROM orders
WHERE created_at > now() - INTERVAL 1 DAY
ORDER BY created_at DESC
LIMIT 20;

-- Calculate fill rate
SELECT
    COUNT(CASE WHEN state = 'FILLED' THEN 1 END) as filled,
    COUNT(CASE WHEN state = 'REJECTED' THEN 1 END) as rejected,
    COUNT(CASE WHEN state = 'CANCELLED' THEN 1 END) as cancelled,
    (COUNT(CASE WHEN state = 'FILLED' THEN 1 END) * 100.0 / COUNT(*)) as fill_rate_pct
FROM orders
WHERE created_at > now() - INTERVAL 7 DAY;

-- Average slippage analysis
SELECT
    symbol,
    AVG(slippage_pips) as avg_slippage,
    STDDEV(slippage_pips) as slippage_stddev,
    MAX(ABS(slippage_pips)) as max_slippage
FROM orders
WHERE state = 'FILLED'
  AND created_at > now() - INTERVAL 30 DAY
GROUP BY symbol
ORDER BY avg_slippage DESC;
```

### Example 5: Position Reconciliation

```python
from execution_service import PositionReconciler

reconciler = PositionReconciler()

# Reconcile positions (every 5 minutes)
async def reconcile_positions():
    # Get positions from database
    db_positions = await reconciler.get_db_positions()

    # Get positions from broker (MT5)
    mt5_positions = await reconciler.get_mt5_positions()

    # Compare
    discrepancies = await reconciler.compare_positions(db_positions, mt5_positions)

    if discrepancies:
        logger.error(f"Position discrepancies found: {discrepancies}")
        # Alert or auto-correct based on config
        if config['auto_correct_discrepancies']:
            await reconciler.correct_positions(discrepancies)
    else:
        logger.info("Positions reconciled successfully")
```

## Guidelines

- **ALWAYS** use ConfigClient for operational settings (order types, slippage limits)
- **NEVER** execute rejected signals (only approved signals!)
- **ALWAYS** track order state machine (prevent state corruption)
- **VERIFY** idempotency (prevent duplicate orders)
- **ENSURE** slippage tracking (monitor execution quality)
- **VALIDATE** position updates match fills

## Critical Rules

1. **Config Hierarchy:**
   - Order types, limits → Central Hub (operational config)
   - Safe defaults → ConfigClient fallback
   - No secrets needed

2. **Approved Signals Only:**
   - **NEVER** execute rejected signals
   - **ONLY** process `signals.approved.*`
   - **VERIFY** signal passed risk-management

3. **Idempotency (CRITICAL):**
   - **CHECK** order doesn't already exist (by signal_id)
   - **PREVENT** duplicate order creation
   - **USE** 24-hour window for deduplication

4. **Order State Management:**
   - **TRACK** complete lifecycle (pending → filled)
   - **UPDATE** state on broker callbacks
   - **NEVER** skip state transitions

5. **Position Reconciliation:**
   - **VERIFY** DB positions match broker
   - **RECONCILE** every 5 minutes
   - **ALERT** on discrepancies

## Common Tasks

### Create Market Order
1. Receive approved signal from risk-mgmt
2. Check idempotency (signal_id not exists)
3. Create order with current market price
4. Submit to MT5 connector
5. Track fill and slippage

### Implement Stop-Loss Order
1. Extract SL level from signal
2. Create stop order
3. Submit to broker
4. Monitor for trigger
5. Track execution when triggered

### Debug Failed Orders
1. Query orders table for state=FAILED
2. Review error logs for failure reason
3. Check MT5 connector connectivity
4. Verify broker rejections (margin, symbols)
5. Test with sample order

### Monitor Fill Quality
1. Query executions for slippage data
2. Calculate average slippage per symbol
3. Set slippage alert thresholds
4. Review high-slippage orders
5. Optimize order types (limit instead of market)

## Troubleshooting

### Issue 1: Orders Not Being Submitted
**Symptoms:** State stuck on PENDING
**Solution:**
- Check MT5 connector connectivity
- Verify NATS publishing to MT5 connector
- Review submission logs for errors
- Test MT5 connector health endpoint
- Check broker connectivity

### Issue 2: Duplicate Orders Created
**Symptoms:** Same signal_id appearing twice
**Solution:**
- Verify idempotency enabled in config
- Check deduplication window sufficient
- Review order creation logic for race conditions
- Test with known duplicate signals
- Add database unique constraint on signal_id

### Issue 3: High Slippage
**Symptoms:** Average slippage > 5 pips
**Solution:**
- Use limit orders instead of market
- Check market liquidity (avoid low-liquidity pairs)
- Reduce order size (large orders = more slippage)
- Review order timing (avoid news events)
- Test different brokers

### Issue 4: Position Discrepancies
**Symptoms:** DB positions don't match MT5
**Solution:**
- Check fill tracking logic (all fills recorded?)
- Verify MT5 position API working
- Review reconciliation interval (too infrequent?)
- Manually reconcile and investigate cause
- Enable auto-correct if safe

### Issue 5: Orders Stuck in SUBMITTED State
**Symptoms:** Never transition to FILLED or REJECTED
**Solution:**
- Check MT5 connector callbacks working
- Verify fill tracking subscriptions active
- Review broker order status
- Test callback processing manually
- Add timeout for stuck orders

## Validation Checklist

After making changes to this service:
- [ ] NATS subscribes to `signals.approved.>` (approved only)
- [ ] Orders created in ClickHouse.orders
- [ ] Order status published to NATS `orders.*.*`
- [ ] Fills tracked in ClickHouse.executions
- [ ] Positions updated in ClickHouse.positions
- [ ] Kafka archives complete order lifecycle
- [ ] Idempotency working (no duplicates)
- [ ] Slippage calculation correct
- [ ] Position reconciliation running
- [ ] ConfigClient fetching from Central Hub
- [ ] Hot-reload responding to config updates

## Related Skills

- `central-hub` - Provides operational config and service discovery
- `risk-management` - Provides approved signals
- `mt5-connector` - Sends orders to broker
- `performance-monitoring` - Receives fills for metrics

## References

- Full Documentation: `docs/SERVICE_ARCHITECTURE_AND_FLOW.md` (lines 579-617)
- Planning Guide: `docs/PLANNING_SKILL_GUIDE.md` (Service 11, lines 1852-2050)
- Flow + Messaging: `docs/SERVICE_FLOW_TREE_WITH_MESSAGING.md` (lines 579-633)
- Database Schema: `docs/table_database_trading.md` (orders, executions, positions tables)
- Config Architecture: `docs/CONFIG_ARCHITECTURE.md`
- Central Hub Skill: `.claude/skills/central-hub/SKILL.md`
- Code: `04-trading-execution/execution-service/`

---

**Created:** 2025-10-19
**Version:** 1.0.0
**Status:** To Implement
