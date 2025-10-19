---
name: mt5-connector
description: Broker API gateway that sends orders to MetaTrader 5 broker and receives fill confirmations with complete order lifecycle tracking and error handling
license: MIT
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
metadata:
  type: Supporting Services (Broker Integration)
  phase: Supporting Services (Phase 4)
  status: To Implement
  priority: P3 (Medium - broker integration)
  port: 8014
  dependencies:
    - central-hub
    - clickhouse
    - nats
    - kafka
  version: 1.0.0
---

# MT5 Connector Service

Broker API gateway that communicates with MetaTrader 5 broker, sends orders from execution service, receives fill confirmations, and logs all broker communications for compliance and debugging.

## When to Use This Skill

Use this skill when:
- Integrating with MT5 broker API
- Sending orders to broker
- Receiving fill confirmations
- Debugging broker connectivity issues
- Implementing broker error handling
- Logging broker communications for audit

## Service Overview

**Type:** Supporting Services (Broker Gateway)
**Port:** 8014
**Input:** NATS (`orders.submitted.>` from execution)
**Output:** NATS (`broker.fill.*`, `broker.error.*`) + Kafka (audit log)
**External API:** MetaTrader 5 Python API
**Function:** Order routing, fill confirmation, broker communication

**Dependencies:**
- **Upstream**: execution (orders via NATS)
- **Downstream**: execution (fill confirmations via NATS)
- **External**: MetaTrader 5 broker API
- **Infrastructure**: NATS cluster, Kafka

## Key Capabilities

- MT5 API integration
- Order submission to broker
- Fill confirmation tracking
- Position query and management
- Account information retrieval
- Error handling and retry logic
- Complete broker communication logging

## Architecture

### Data Flow

```
NATS: orders.submitted.> (listen from execution)
  ↓
mt5-connector
  ├─→ Validate order parameters
  ├─→ Check broker connectivity
  ├─→ Send order to MT5 broker API
  ↓
MT5 Broker
  ├─→ Order execution
  ├─→ Fill confirmation
  ├─→ Position update
  ↓
mt5-connector
  ├─→ Receive fill confirmation
  ├─→ Validate fill data
  ↓
├─→ ClickHouse.executions (fill details)
├─→ NATS: broker.fill.{symbol} (execution)
├─→ NATS: broker.error.{symbol} (if rejected)
└─→ Kafka: broker_communication_log (audit trail)
```

### MT5 API Operations

**1. Order Management:**
- `order_send()` - Submit market/limit/stop order
- `order_check()` - Validate order before submission
- `positions_get()` - Query open positions
- `positions_close()` - Close specific position

**2. Position Modification:**
- Modify stop-loss level
- Modify take-profit level
- Partial close position

**3. Account Information:**
- `account_info()` - Balance, equity, margin
- `account_currency()` - Base currency
- `account_leverage()` - Trading leverage

**4. Symbol Information:**
- `symbol_info()` - Tick size, contract size
- `symbol_info_tick()` - Current bid/ask

### Configuration

**Operational Config (Central Hub):**
```json
{
  "operational": {
    "mt5_connection": {
      "terminal_path": "/path/to/terminal64.exe",
      "server": "broker-server",
      "login": 12345678,
      "timeout_seconds": 60
    },
    "order_settings": {
      "validate_before_send": true,
      "max_retries": 3,
      "retry_delay_seconds": 5
    },
    "error_handling": {
      "auto_reconnect": true,
      "reconnect_interval_seconds": 30,
      "log_all_communications": true
    },
    "position_sync": {
      "sync_interval_minutes": 5,
      "reconcile_on_disconnect": true
    }
  }
}
```

**Environment Variables (Secrets):**
```bash
MT5_PASSWORD=your_broker_password  # NEVER hardcode!
```

## Examples

### Example 1: Fetch Config from Central Hub

```python
from shared.components.config import ConfigClient

# Initialize client
client = ConfigClient(
    service_name="mt5-connector",
    safe_defaults={
        "operational": {
            "order_settings": {"validate_before_send": True},
            "error_handling": {"auto_reconnect": True}
        }
    }
)
await client.init_async()

# Get config
config = await client.get_config()
timeout = config['operational']['mt5_connection']['timeout_seconds']
max_retries = config['operational']['order_settings']['max_retries']
print(f"MT5 timeout: {timeout}s, Max retries: {max_retries}")
```

### Example 2: Initialize MT5 Connection

```python
import MetaTrader5 as mt5
from mt5_connector import MT5Manager

manager = MT5Manager()

# Initialize connection
success = await manager.initialize(
    terminal_path=config['terminal_path'],
    server=config['server'],
    login=config['login'],
    password=os.getenv("MT5_PASSWORD")
)

if success:
    account_info = mt5.account_info()
    print(f"Connected to MT5: {account_info.name}")
    print(f"Balance: ${account_info.balance:.2f}")
    print(f"Equity: ${account_info.equity:.2f}")
else:
    logger.error("Failed to connect to MT5")
```

### Example 3: Send Order to Broker

```python
from mt5_connector import OrderSubmitter

submitter = OrderSubmitter()

# Receive order from execution service
order = {
    "order_id": "ord_12345",
    "symbol": "EURUSD",
    "order_type": "buy",
    "volume": 0.01,  # lots
    "price": 1.08125,
    "sl": 1.08000,
    "tp": 1.08500
}

# Submit to MT5
result = await submitter.send_order(
    symbol=order['symbol'],
    order_type=mt5.ORDER_TYPE_BUY,
    volume=order['volume'],
    price=order['price'],
    sl=order['sl'],
    tp=order['tp'],
    comment=f"order_id:{order['order_id']}"
)

if result.retcode == mt5.TRADE_RETCODE_DONE:
    # Success - publish fill confirmation
    await publish_fill_confirmation(result)
else:
    # Error - publish broker error
    await publish_broker_error(result)
```

### Example 4: Handle Fill Confirmation

```python
from mt5_connector import FillHandler

handler = FillHandler()

# Process MT5 trade result
async def process_fill(trade_result):
    fill_data = {
        "order_id": extract_order_id(trade_result.comment),
        "ticket": trade_result.order,
        "symbol": trade_result.symbol,
        "volume": trade_result.volume,
        "price": trade_result.price,
        "timestamp": trade_result.time,
        "commission": trade_result.commission,
        "swap": trade_result.swap
    }

    # Save to ClickHouse
    await handler.save_execution(fill_data)

    # Publish to NATS
    await handler.publish_fill(
        subject=f"broker.fill.{fill_data['symbol']}",
        data=fill_data
    )

    # Archive to Kafka
    await handler.archive_to_kafka(fill_data)
```

### Example 5: Query Open Positions

```python
# Get all open positions from MT5
positions = mt5.positions_get()

if positions:
    for pos in positions:
        print(f"Ticket: {pos.ticket}")
        print(f"Symbol: {pos.symbol}")
        print(f"Type: {'BUY' if pos.type == mt5.POSITION_TYPE_BUY else 'SELL'}")
        print(f"Volume: {pos.volume}")
        print(f"Open Price: {pos.price_open}")
        print(f"Current Price: {pos.price_current}")
        print(f"Profit: ${pos.profit:.2f}")
        print("---")
```

## Guidelines

- **ALWAYS** use ConfigClient for operational settings (timeout, retries)
- **NEVER** send duplicate orders (verify order_id not already submitted)
- **ALWAYS** log broker responses (audit trail for compliance)
- **VERIFY** broker connection before order submission
- **ENSURE** error handling for broker rejections
- **VALIDATE** fill confirmations match order requests

## Critical Rules

1. **Config Hierarchy:**
   - MT5 password → ENV variables (`MT5_PASSWORD`)
   - Connection settings, retry logic → Central Hub
   - Safe defaults → ConfigClient fallback

2. **Order Idempotency:**
   - **CHECK** order_id not already submitted
   - **PREVENT** duplicate order submission
   - **USE** order comment field for tracking

3. **Connection Management:**
   - **VERIFY** connection before sending orders
   - **AUTO-RECONNECT** on disconnect
   - **RETRY** failed orders with exponential backoff

4. **Error Handling (Comprehensive):**
   - **LOG** all broker errors with retcode
   - **NOTIFY** execution service of rejections
   - **CATEGORIZE** errors (retriable vs fatal)

5. **Audit Trail (Mandatory):**
   - **LOG** every broker communication
   - **ARCHIVE** to Kafka for compliance
   - **INCLUDE** timestamps, order IDs, results

## Common Tasks

### Initialize MT5 Connection
1. Set MT5_PASSWORD environment variable
2. Configure terminal path and server in Central Hub
3. Initialize MT5 connection on service start
4. Verify account info retrieval
5. Monitor connection health

### Send Market Order
1. Receive order from execution service (NATS)
2. Validate order parameters (symbol, volume, SL/TP)
3. Check MT5 connection active
4. Submit order via `mt5.order_send()`
5. Process result and publish confirmation

### Handle Broker Rejection
1. Receive retcode != TRADE_RETCODE_DONE
2. Log error details (retcode, description)
3. Determine if retriable (e.g., TRADE_RETCODE_PRICE_OFF)
4. Retry if appropriate, or notify execution service
5. Archive rejection to Kafka

### Sync Positions with Broker
1. Query MT5 positions via `mt5.positions_get()`
2. Query database positions
3. Compare and identify discrepancies
4. Reconcile differences (alert or auto-correct)
5. Log reconciliation results

## Troubleshooting

### Issue 1: MT5 Connection Failing
**Symptoms:** `mt5.initialize()` returns False
**Solution:**
- Verify MT5 terminal running
- Check server name and login correct
- Verify MT5_PASSWORD environment variable set
- Review MT5 terminal logs
- Test connection manually in MT5 terminal

### Issue 2: Orders Being Rejected (TRADE_RETCODE_INVALID)
**Symptoms:** All orders rejected with retcode 10013
**Solution:**
- Validate symbol name (EURUSD not EUR/USD)
- Check volume (must be in broker's min/max range)
- Verify SL/TP levels within allowed distance
- Check market hours (can't trade when market closed)
- Review broker-specific restrictions

### Issue 3: Fill Confirmations Not Arriving
**Symptoms:** Orders sent but no fill messages
**Solution:**
- Check NATS publishing working
- Verify fill handler callback registered
- Review MT5 trade result processing
- Test NATS subscription manually
- Check for exceptions in callback

### Issue 4: Position Discrepancies
**Symptoms:** Database positions don't match MT5
**Solution:**
- Run position sync manually
- Check fill tracking logic (all fills recorded?)
- Verify MT5 positions API working
- Review reconciliation interval (too infrequent?)
- Investigate manual trades (outside system)

### Issue 5: High Latency to Broker
**Symptoms:** Order execution > 1 second
**Solution:**
- Check network latency to broker
- Verify MT5 terminal location (VPS near broker)
- Review broker API response times
- Test with limit orders instead of market
- Consider broker upgrade or change

## Validation Checklist

After making changes to this service:
- [ ] NATS subscribes to `orders.submitted.>` (order requests)
- [ ] MT5 connection established (check `account_info()`)
- [ ] Orders sent to broker successfully
- [ ] Fill confirmations published to NATS `broker.fill.*`
- [ ] Kafka archives all broker communication
- [ ] Error handling works (test with invalid orders)
- [ ] Position sync working (reconciliation accurate)
- [ ] Duplicate order prevention active
- [ ] ConfigClient fetching from Central Hub
- [ ] Hot-reload responding to config updates

## Related Skills

- `central-hub` - Provides operational config and service discovery
- `execution` - Sends orders to MT5 connector
- `risk-management` - Provides position limits
- `performance-monitoring` - Receives fill confirmations

## References

- Full Documentation: `docs/SERVICE_ARCHITECTURE_AND_FLOW.md` (lines 706-723)
- Planning Guide: `docs/PLANNING_SKILL_GUIDE.md` (Service 14, lines 2252-2450)
- Flow + Messaging: `docs/SERVICE_FLOW_TREE_WITH_MESSAGING.md` (lines 684-721)
- Database Schema: `docs/table_database_trading.md` (executions table)
- MT5 Python API: https://www.mql5.com/en/docs/python_metatrader5
- Config Architecture: `docs/CONFIG_ARCHITECTURE.md`
- Central Hub Skill: `.claude/skills/central-hub/SKILL.md`
- Code: `05-supporting-services/mt5-connector/`

---

**Created:** 2025-10-19
**Version:** 1.0.0
**Status:** To Implement
