# Skill: mt5-connector Service

## Purpose
Broker API gateway. Sends orders to MetaTrader 5 broker and receives fill confirmations.

## Key Facts
- **Phase**: Supporting Services (Phase 4)
- **Status**: ⚠️ To Implement
- **Priority**: P3 (Medium - broker integration)
- **Function**: MT5 API communication, order routing
- **Broker**: MetaTrader 5 (forex/gold broker)

## Data Flow
```
NATS: orders.> (listen for orders from execution-service)
ClickHouse.orders (read order details)
  → mt5-connector (send to MT5 broker API)
  → MT5 Broker (order execution)
  → ClickHouse.executions (fill confirmations)
  → NATS: broker.fill.{symbol} (fill confirmations)
  → Kafka: broker_communication_log (audit)
```

## Messaging
- **NATS Subscribe**: `orders.submitted.>` (new orders from execution-service)
- **NATS Publish**: `broker.fill.*` (fill confirmations from broker), `broker.error.*` (broker errors)
- **Kafka Publish**: `broker_communication_log` (complete broker interaction log)
- **Pattern**: Both NATS + Kafka (critical broker communication needs real-time + audit)

## Dependencies
- **Upstream**: execution-service (orders via NATS)
- **Downstream**: execution-service (fill confirmations via NATS)
- **External**: MetaTrader 5 broker API
- **Infrastructure**: NATS cluster, Kafka, MT5 API

## Critical Rules
1. **NEVER** send duplicate orders (verify order_id not already submitted)
2. **ALWAYS** log broker responses (audit trail for compliance)
3. **VERIFY** broker connection before order submission
4. **ENSURE** error handling for broker rejections (notify execution-service)
5. **VALIDATE** fill confirmations match order requests (reconciliation)

## MT5 API Operations
### Order Submission
- Create market order
- Create limit order
- Create stop order
- Set stop-loss and take-profit

### Position Management
- Query open positions
- Modify position (SL/TP)
- Close position

### Account Info
- Balance and equity
- Margin used/free
- Account currency

## Error Handling
- **Connection errors**: Retry with exponential backoff
- **Order rejection**: Log reason, notify execution-service
- **Timeout**: Mark order as failed, investigate
- **Invalid parameters**: Validate before sending to broker

## Validation
When working on this service, ALWAYS verify:
- [ ] NATS subscribes to `orders.submitted.>` (order requests)
- [ ] MT5 connection established (check API status)
- [ ] Orders sent to broker successfully
- [ ] Fill confirmations published to NATS `broker.fill.*`
- [ ] Kafka archives all broker communication
- [ ] Error handling works (test with invalid orders)

## Reference Docs
- Planning guide: `PLANNING_SKILL_GUIDE.md` (Service 14, lines 2252-2450)
- Architecture: `SERVICE_ARCHITECTURE_AND_FLOW.md` (lines 706-723)
- Flow + messaging: `SERVICE_FLOW_TREE_WITH_MESSAGING.md` (lines 684-721)
- Database schema: `table_database_trading.md` (executions table)
