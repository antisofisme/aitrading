# Skill: dashboard-service Service

## Purpose
Web UI for real-time monitoring. Visualizes data, metrics, performance, and system status.

## Key Facts
- **Phase**: Supporting Services (Phase 4)
- **Status**: ⚠️ To Implement
- **Priority**: P3 (Medium - user interface)
- **Function**: Real-time dashboards, KPI tracking, data visualization
- **Stack**: FastAPI (backend) + React/Vue (frontend)

## Data Flow
```
NATS: *.> (subscribe ALL events for monitoring)
ClickHouse.* (read all tables)
  → dashboard-service (process, visualize)
  → Web UI (dashboards, charts, alerts)
  → WebSocket (real-time updates to browser)
```

## Messaging
- **NATS Subscribe**: `*.*` (all events from all services) - wildcard subscription
- **Pattern**: NATS only, read-only (no publishing, subscriber only)

## Dependencies
- **Upstream**: All services (subscribes to all NATS events)
- **Downstream**: None (read-only, no writes)
- **Infrastructure**: NATS cluster, ClickHouse, Web server

## Critical Rules
1. **NEVER** publish to NATS (read-only service!)
2. **ALWAYS** use read-only ClickHouse connection (no writes)
3. **VERIFY** dashboard updates in real-time (WebSocket to browser)
4. **ENSURE** authentication and authorization (secure access)
5. **VALIDATE** data refresh rates (avoid overloading ClickHouse)

## Dashboard Views
### System Status
- Service health (all 17 services)
- Infrastructure health (NATS, Kafka, ClickHouse, etc.)
- Data flow metrics (ticks/sec, candles/min)

### Live Trading
- Open positions
- Recent trades
- P&L (real-time)
- Portfolio equity curve

### Performance
- Sharpe ratio, max drawdown
- Win rate, profit factor
- Daily/weekly/monthly returns
- Trade statistics

### Data Quality
- Tick counts by symbol
- Candle completeness
- Feature availability
- Gap detection alerts

### ML Models
- Active models/agents
- Model performance metrics
- Training status
- Prediction accuracy

## Validation
When working on this service, ALWAYS verify:
- [ ] NATS subscribes to `*.*` (all events)
- [ ] ClickHouse connection read-only (no accidental writes)
- [ ] WebSocket updates browser in real-time
- [ ] Authentication works (login required)
- [ ] Dashboard loads fast (< 2 seconds)

## Reference Docs
- Planning guide: `PLANNING_SKILL_GUIDE.md` (Service 16, lines 2652-2850)
- Architecture: `SERVICE_ARCHITECTURE_AND_FLOW.md` (lines 752-767)
- Flow + messaging: `SERVICE_FLOW_TREE_WITH_MESSAGING.md` (lines 755-785)
- Database schema: All tables (read-only access)
