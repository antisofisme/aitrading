---
name: dashboard
description: Web UI for real-time monitoring with live dashboards, KPI tracking, data visualization, and WebSocket updates for system status, trading performance, and ML metrics
license: MIT
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
metadata:
  type: Supporting Services (Web UI)
  phase: Supporting Services (Phase 4)
  status: To Implement
  priority: P3 (Medium - user interface)
  port: 8016
  dependencies:
    - central-hub
    - clickhouse
    - nats
  version: 1.0.0
---

# Dashboard Service

Web UI for real-time monitoring with interactive dashboards, KPI tracking, live data visualization via WebSocket, and comprehensive system status across all 18 microservices.

## When to Use This Skill

Use this skill when:
- Building web dashboards for monitoring
- Visualizing real-time trading data
- Implementing KPI tracking
- Creating system health dashboards
- Adding user authentication
- Developing real-time WebSocket updates

## Service Overview

**Type:** Supporting Services (Web Dashboard)
**Port:** 8016
**Stack:** FastAPI (backend) + React/Vue (frontend)
**Input:** NATS (all events `*.*`) + ClickHouse (all tables read-only)
**Output:** Web UI (dashboards, charts) + WebSocket (real-time updates)
**Access:** Authenticated users only

**Dependencies:**
- **Upstream**: All services (subscribes to all NATS events)
- **Downstream**: None (read-only, no writes)
- **Infrastructure**: NATS cluster, ClickHouse, Web server

## Key Capabilities

- Real-time system status monitoring
- Live trading dashboard (positions, P&L, equity curve)
- Performance metrics visualization
- Data quality monitoring
- ML model performance tracking
- Service health overview
- WebSocket real-time updates
- User authentication and authorization

## Architecture

### Data Flow

```
NATS: *.* (subscribe ALL events for real-time monitoring)
  +
ClickHouse.* (read all tables for historical data)
  ↓
dashboard-service (FastAPI backend)
  ├─→ Process events for real-time updates
  ├─→ Query ClickHouse for historical charts
  ├─→ Aggregate KPIs
  ↓
WebSocket (push to browser)
  ↓
Web UI (React/Vue frontend)
  ├─→ System status dashboard
  ├─→ Live trading dashboard
  ├─→ Performance charts
  ├─→ Data quality monitor
  └─→ ML model dashboard
```

### Dashboard Views

**1. System Status Dashboard:**
- Service health (17 microservices)
  - Green: Healthy
  - Yellow: Degraded
  - Red: Down
- Infrastructure health
  - PostgreSQL, ClickHouse status
  - NATS cluster (3 nodes)
  - Kafka broker
- Data flow metrics
  - Ticks/second
  - Candles/minute
  - Features/hour

**2. Live Trading Dashboard:**
- Open positions (symbol, size, entry, current P&L)
- Recent trades (last 20)
- Real-time P&L
- Portfolio equity curve
- Daily/weekly/monthly returns

**3. Performance Dashboard:**
- Sharpe ratio (30-day rolling)
- Max drawdown (current and historical)
- Win rate, profit factor
- Trade statistics (avg win/loss, R-multiples)
- Equity curve chart

**4. Data Quality Dashboard:**
- Tick counts by symbol
- Candle completeness (gaps detected)
- Feature availability (NULL percentage)
- Gap detection alerts
- Data latency metrics

**5. ML Models Dashboard:**
- Active models/agents
- Model performance metrics (accuracy, F1)
- Training status and progress
- Prediction accuracy over time
- Feature importance charts

### Configuration

**Operational Config (Central Hub):**
```json
{
  "operational": {
    "server_settings": {
      "host": "0.0.0.0",
      "port": 8016,
      "workers": 4,
      "reload": false
    },
    "websocket": {
      "enabled": true,
      "heartbeat_interval_seconds": 30,
      "max_connections": 100
    },
    "authentication": {
      "enabled": true,
      "session_timeout_minutes": 60,
      "require_2fa": false
    },
    "data_refresh": {
      "realtime_update_interval_ms": 1000,
      "chart_update_interval_seconds": 5,
      "clickhouse_query_interval_seconds": 10
    },
    "clickhouse_connection": {
      "read_only": true,
      "timeout_seconds": 30
    }
  }
}
```

**Environment Variables (Secrets):**
```bash
DASHBOARD_SECRET_KEY=your_secret_key  # Session encryption
ADMIN_PASSWORD=your_admin_password    # Admin login
```

## Examples

### Example 1: Fetch Config from Central Hub

```python
from shared.components.config import ConfigClient

# Initialize client
client = ConfigClient(
    service_name="dashboard",
    safe_defaults={
        "operational": {
            "server_settings": {"port": 8016},
            "websocket": {"enabled": True}
        }
    }
)
await client.init_async()

# Get config
config = await client.get_config()
port = config['operational']['server_settings']['port']
ws_enabled = config['operational']['websocket']['enabled']
print(f"Dashboard on port {port}, WebSocket: {ws_enabled}")
```

### Example 2: Subscribe to All NATS Events

```python
from nats.aio.client import Client as NATS
from dashboard import EventProcessor

nc = NATS()
await nc.connect(servers=["nats://nats-1:4222"])

processor = EventProcessor()

# Subscribe to ALL events (wildcard)
async def message_handler(msg):
    subject = msg.subject
    data = msg.data.decode()

    # Process event for real-time dashboard updates
    await processor.process_event(subject, data)

    # Push to connected WebSocket clients
    await websocket_manager.broadcast(subject, data)

# Subscribe to everything
await nc.subscribe("*.*", cb=message_handler)
```

### Example 3: Query ClickHouse for Equity Curve

```python
from dashboard import ClickHouseQuery

query = ClickHouseQuery()

# Get equity curve (last 30 days)
equity_data = await query.get_equity_curve(
    days=30,
    interval="1 hour"
)

# Result:
# [
#   {"timestamp": "2025-10-01 00:00", "equity": 10250.50},
#   {"timestamp": "2025-10-01 01:00", "equity": 10275.25},
#   ...
# ]

# Send to frontend
await send_chart_data("equity_curve", equity_data)
```

### Example 4: WebSocket Real-Time Updates

```python
from fastapi import WebSocket
from dashboard import WebSocketManager

ws_manager = WebSocketManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)

    try:
        while True:
            # Wait for messages from client (heartbeat)
            data = await websocket.receive_text()

            # Send real-time updates
            await websocket.send_json({
                "type": "status_update",
                "services": await get_service_status(),
                "trading": await get_trading_stats(),
                "timestamp": time.time()
            })

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
```

### Example 5: Query System Health

```python
# API endpoint for system health
@app.get("/api/health/system")
async def get_system_health():
    services = await query_service_registry()
    infrastructure = await query_infrastructure_health()

    return {
        "services": {
            "total": len(services),
            "healthy": len([s for s in services if s['status'] == 'healthy']),
            "degraded": len([s for s in services if s['status'] == 'degraded']),
            "down": len([s for s in services if s['status'] == 'down'])
        },
        "infrastructure": {
            "postgresql": infrastructure['postgresql']['status'],
            "clickhouse": infrastructure['clickhouse']['status'],
            "nats": infrastructure['nats']['status'],
            "kafka": infrastructure['kafka']['status']
        },
        "timestamp": time.time()
    }
```

## Guidelines

- **ALWAYS** use ConfigClient for operational settings (ports, intervals)
- **NEVER** publish to NATS (read-only service!)
- **ALWAYS** use read-only ClickHouse connection
- **VERIFY** dashboard updates in real-time (WebSocket)
- **ENSURE** authentication and authorization
- **VALIDATE** data refresh rates don't overload ClickHouse

## Critical Rules

1. **Config Hierarchy:**
   - Admin passwords, secret keys → ENV variables
   - Server settings, refresh intervals → Central Hub
   - Safe defaults → ConfigClient fallback

2. **Read-Only Operations:**
   - **NEVER** publish to NATS (subscriber only)
   - **NEVER** write to ClickHouse (read-only connection)
   - **VERIFY** no accidental data modifications

3. **Authentication (Mandatory):**
   - **REQUIRE** login for dashboard access
   - **IMPLEMENT** session management
   - **ENFORCE** role-based access control (RBAC)

4. **Performance Optimization:**
   - **LIMIT** ClickHouse query frequency
   - **CACHE** dashboard data (5-10 second refresh)
   - **PAGINATE** large result sets

5. **WebSocket Management:**
   - **HEARTBEAT** to detect disconnections
   - **LIMIT** max concurrent connections
   - **HANDLE** reconnection gracefully

## Common Tasks

### Add New Dashboard Widget
1. Design widget layout (chart type, KPIs)
2. Create API endpoint for data
3. Query ClickHouse or NATS for data
4. Add frontend component (React/Vue)
5. Enable WebSocket updates if real-time

### Implement User Authentication
1. Create user database table
2. Implement login endpoint (JWT tokens)
3. Add session management
4. Protect dashboard routes
5. Test login flow end-to-end

### Optimize Dashboard Performance
1. Profile slow queries (ClickHouse)
2. Add caching layer (Redis/DragonflyDB)
3. Reduce query frequency
4. Implement pagination
5. Monitor page load times

### Add Real-Time Chart
1. Subscribe to relevant NATS subjects
2. Process events for chart data
3. Push updates via WebSocket
4. Update frontend chart library
5. Test real-time responsiveness

## Troubleshooting

### Issue 1: Dashboard Loading Slowly (> 5 seconds)
**Symptoms:** Slow page load times
**Solution:**
- Profile ClickHouse queries (identify slow ones)
- Add caching for dashboard data
- Reduce initial data load (lazy loading)
- Optimize frontend bundle size
- Check network latency

### Issue 2: WebSocket Disconnecting Frequently
**Symptoms:** Real-time updates stop, reconnect messages
**Solution:**
- Increase heartbeat interval
- Check network stability
- Review WebSocket timeout settings
- Implement exponential backoff for reconnect
- Test with different browsers

### Issue 3: NATS Event Overload
**Symptoms:** Dashboard can't keep up with events
**Solution:**
- Filter events (subscribe to specific subjects)
- Throttle WebSocket updates (batch events)
- Aggregate before sending to client
- Use sampling for high-frequency data
- Consider event buffering

### Issue 4: ClickHouse Connection Timeout
**Symptoms:** Queries failing with timeout errors
**Solution:**
- Increase timeout setting
- Optimize slow queries (add indexes)
- Reduce query complexity
- Use materialized views
- Check ClickHouse server load

### Issue 5: Authentication Not Working
**Symptoms:** Users can't log in
**Solution:**
- Check DASHBOARD_SECRET_KEY set
- Verify ADMIN_PASSWORD correct
- Review JWT token expiration
- Test authentication endpoint manually
- Check session storage

## Validation Checklist

After making changes to this service:
- [ ] NATS subscribes to `*.*` (all events)
- [ ] ClickHouse connection read-only (verify no writes)
- [ ] WebSocket updates browser in real-time
- [ ] Authentication works (login required)
- [ ] Dashboard loads fast (< 2 seconds)
- [ ] All charts displaying correctly
- [ ] No data modification possible
- [ ] Session timeout working
- [ ] ConfigClient fetching from Central Hub
- [ ] Hot-reload responding to config updates

## Related Skills

- `central-hub` - Provides operational config and service registry
- `performance-monitoring` - Provides performance metrics
- `execution` - Provides trading data
- `notification-hub` - Can trigger from dashboard actions

## References

- Full Documentation: `docs/SERVICE_ARCHITECTURE_AND_FLOW.md` (lines 752-767)
- Planning Guide: `docs/PLANNING_SKILL_GUIDE.md` (Service 16, lines 2652-2850)
- Flow + Messaging: `docs/SERVICE_FLOW_TREE_WITH_MESSAGING.md` (lines 755-785)
- Database Schema: All tables (read-only access)
- Config Architecture: `docs/CONFIG_ARCHITECTURE.md`
- Central Hub Skill: `.claude/skills/central-hub/SKILL.md`
- Code: `05-supporting-services/dashboard-service/`

---

**Created:** 2025-10-19
**Version:** 1.0.0
**Status:** To Implement
