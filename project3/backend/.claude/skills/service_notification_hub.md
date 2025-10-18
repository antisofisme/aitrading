# Skill: notification-hub Service

## Purpose
Alert routing service. Sends notifications (Telegram, Email, SMS) based on events from other services.

## Key Facts
- **Phase**: Supporting Services (Phase 4)
- **Status**: ⚠️ To Implement
- **Priority**: P3 (Medium - user notifications)
- **Function**: Alert routing, notification delivery
- **Channels**: Telegram Bot, Email (SMTP), SMS (optional)

## Data Flow
```
NATS: performance.alert.>, risk.alert.> (subscribe alerts)
ClickHouse.risk_events, performance_metrics (read)
  → notification-hub (route to appropriate channel)
  → Telegram Bot / SMTP / SMS (deliver notifications)
```

## Messaging
- **NATS Subscribe**: `performance.alert.*`, `risk.alert.*`, `training.completed.*`, `orders.filled.*` (alert events)
- **Pattern**: NATS only, subscriber (no Kafka, fire-and-forget notifications)

## Dependencies
- **Upstream**: All services that publish alerts (performance-monitoring, risk-management, etc.)
- **Downstream**: None (notification endpoints)
- **External**: Telegram API, SMTP server, SMS provider
- **Infrastructure**: NATS cluster

## Critical Rules
1. **NEVER** spam users with notifications (rate limiting required)
2. **ALWAYS** include context in alerts (symbol, amount, reason)
3. **VERIFY** notification delivery (track sent/failed status)
4. **ENSURE** alert priority levels (critical vs warning)
5. **VALIDATE** user preferences (opt-in/opt-out per channel)

## Alert Types
### Performance Alerts
- Daily loss limit exceeded
- Max drawdown reached
- Low Sharpe ratio warning
- Large winning/losing trade

### Risk Alerts
- Position limit exceeded
- Portfolio exposure too high
- Stop-loss triggered
- Margin call warning

### System Alerts
- Service down
- Data gap detected
- Training completed
- Model deployment

### Trading Alerts
- Order filled
- Position opened/closed
- Take-profit hit
- Stop-loss hit

## Notification Channels
### Telegram
- Instant delivery
- Two-way communication (optional)
- Rich formatting (markdown)
- Low cost (free API)

### Email (SMTP)
- Detailed reports
- Daily/weekly summaries
- HTML formatting
- Attachments (charts, reports)

### SMS (Optional)
- Critical alerts only
- High cost (carrier fees)
- Plain text only
- Character limits

## Validation
When working on this service, ALWAYS verify:
- [ ] NATS subscribes to `*.alert.*` (all alert events)
- [ ] Telegram bot configured (bot token, chat ID)
- [ ] Email configured (SMTP server, credentials)
- [ ] Notifications delivered (check Telegram/email received)
- [ ] Rate limiting works (no spam)
- [ ] User preferences respected (opt-in/opt-out)

## Reference Docs
- Planning guide: `PLANNING_SKILL_GUIDE.md` (Service 17, lines 2852-3050)
- Architecture: `SERVICE_ARCHITECTURE_AND_FLOW.md` (lines 770-786)
- Flow + messaging: `SERVICE_FLOW_TREE_WITH_MESSAGING.md` (lines 787-820)
- Database schema: N/A (no database writes, event-driven only)
