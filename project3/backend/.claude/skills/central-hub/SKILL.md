---
name: central-hub
description: Core orchestration service providing centralized configuration management, service discovery, health monitoring, and infrastructure coordination for all 18 microservices with hot-reload and failover support
license: MIT
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
metadata:
  type: Core Infrastructure (Orchestration)
  phase: Core Infrastructure (Phase 0)
  status: Implemented
  priority: P0 (Critical - system backbone)
  port: 8001
  dependencies:
    - postgresql
    - nats
  version: 2.0.0
---

# Central Hub Service

Core orchestration and coordination service that provides centralized configuration management, service discovery, health monitoring, and infrastructure coordination for all 18 microservices in the AI trading system. Acts as the single source of truth for operational configuration with hot-reload and failover capabilities.

## When to Use This Skill

Use this skill when:
- Implementing centralized configuration for any service
- Setting up service discovery and registration
- Monitoring infrastructure health (PostgreSQL, NATS, Kafka, ClickHouse)
- Debugging configuration issues
- Implementing hot-reload for config changes
- Managing service coordination and dependencies

## Service Overview

**Type:** Core Infrastructure (System Backbone)
**Port:** 8001
**Database:** PostgreSQL (central_hub)
**Input:** Service registration, config requests, health checks
**Output:** Config distribution, service discovery, health status
**Function:** Configuration management, service coordination, infrastructure monitoring
**Critical:** All services depend on Central Hub

**Dependencies:**
- **Upstream**: None (foundational service)
- **Downstream**: All 18 microservices
- **Infrastructure**: PostgreSQL, NATS cluster

## Key Capabilities

- Centralized configuration management
- Service discovery and registration
- Hot-reload configuration updates
- Health monitoring (services + infrastructure)
- Failover and high availability
- Configuration versioning and rollback
- Service dependency tracking
- Infrastructure status dashboard

## Architecture

### Data Flow

```
Services (18 microservices)
  ↓ (register on startup)
central-hub
  ├─→ Store in PostgreSQL.central_hub.service_registry
  ├─→ Provide config via ConfigClient
  ├─→ Monitor health via heartbeats
  ├─→ Track dependencies
  ↓
Services
  ├─→ Fetch config on startup
  ├─→ Hot-reload on config updates
  ├─→ Send health metrics
  └─→ Query service discovery
```

### Configuration Architecture

**3-Layer Hierarchy:**

```
Layer 1: Environment Variables (Secrets)
  - API keys, passwords, tokens
  - Never stored in database
  - Read from OS environment

Layer 2: Central Hub (Operational Config)
  - Service settings, thresholds, intervals
  - Stored in PostgreSQL
  - Hot-reload supported

Layer 3: Safe Defaults (Fallback)
  - Hardcoded in ConfigClient
  - Used if Central Hub unavailable
  - Ensures service can start
```

**Example:**
```python
# Layer 1: Secrets (ENV)
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

# Layer 2: Operational (Central Hub)
config = await client.get_config()
symbols = config['operational']['symbols']

# Layer 3: Safe Defaults (Fallback)
client = ConfigClient(
    service_name="polygon-live-collector",
    safe_defaults={
        "operational": {
            "symbols": ["EURUSD"],  # Fallback if Central Hub down
            "websocket_reconnect_delay": 5
        }
    }
)
```

### Service Registry Schema

**Table: service_registry**
```sql
CREATE TABLE service_registry (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,  -- healthy, degraded, down
    last_heartbeat TIMESTAMP NOT NULL,
    version VARCHAR(50),
    host VARCHAR(255),
    port INTEGER,
    dependencies JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Table: service_configs**
```sql
CREATE TABLE service_configs (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    config_data JSONB NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(service_name, version)
);
```

**Table: health_metrics**
```sql
CREATE TABLE health_metrics (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100),
    metric_type VARCHAR(100),  -- cpu, memory, latency, throughput
    metric_value FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Table: infrastructure_status**
```sql
CREATE TABLE infrastructure_status (
    id SERIAL PRIMARY KEY,
    component_name VARCHAR(100),  -- postgresql, nats, kafka, clickhouse
    status VARCHAR(50),
    response_time_ms FLOAT,
    error_message TEXT,
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Configuration

**Central Hub's Own Config:**
```json
{
  "operational": {
    "server_settings": {
      "host": "0.0.0.0",
      "port": 8001,
      "workers": 4
    },
    "service_discovery": {
      "heartbeat_interval_seconds": 30,
      "service_timeout_seconds": 90,
      "auto_deregister_dead_services": true
    },
    "health_monitoring": {
      "check_interval_seconds": 60,
      "infrastructure_components": [
        "postgresql",
        "nats",
        "kafka",
        "clickhouse"
      ]
    },
    "config_management": {
      "enable_versioning": true,
      "enable_hot_reload": true,
      "config_cache_ttl_seconds": 300
    }
  }
}
```

**Environment Variables (Secrets):**
```bash
CENTRAL_HUB_DB_HOST=localhost
CENTRAL_HUB_DB_PORT=5432
CENTRAL_HUB_DB_NAME=central_hub
CENTRAL_HUB_DB_USER=suho_admin
CENTRAL_HUB_DB_PASSWORD=your_secure_password
```

## Examples

### Example 1: Service Registration on Startup

```python
from central_hub.client import CentralHubClient

hub = CentralHubClient(base_url="http://central-hub:8001")

# Register service on startup
await hub.register_service(
    service_name="polygon-live-collector",
    version="1.2.3",
    host="polygon-live-collector",
    port=8002,
    dependencies=["central-hub", "timescaledb", "nats"],
    metadata={
        "type": "data-ingestion",
        "phase": "phase-1",
        "priority": "P0"
    }
)

# Start heartbeat loop
async def send_heartbeat():
    while True:
        await hub.heartbeat("polygon-live-collector", status="healthy")
        await asyncio.sleep(30)

asyncio.create_task(send_heartbeat())
```

### Example 2: Fetch Config via ConfigClient

```python
from shared.components.config import ConfigClient

# Initialize client with safe defaults
client = ConfigClient(
    service_name="tick-aggregator",
    safe_defaults={
        "operational": {
            "timeframes": ["5m", "15m", "1h"],
            "aggregation_interval_seconds": 60
        }
    }
)

# Initialize connection to Central Hub
await client.init_async()

# Fetch config (Layer 2: Central Hub)
config = await client.get_config()

# Use config
timeframes = config['operational']['timeframes']
interval = config['operational']['aggregation_interval_seconds']

print(f"Aggregating to: {timeframes}, Interval: {interval}s")
```

### Example 3: Hot-Reload Configuration

```python
from shared.components.config import ConfigClient

client = ConfigClient(service_name="risk-management")
await client.init_async()

# Enable hot-reload (watch for config updates)
async def on_config_update(new_config):
    logger.info("Config updated via Central Hub!")

    # Update runtime settings
    global MAX_POSITION_SIZE
    MAX_POSITION_SIZE = new_config['operational']['position_limits']['max_position_size']

    logger.info(f"Max position size updated to: {MAX_POSITION_SIZE}")

# Start hot-reload listener
await client.watch_config(callback=on_config_update)
```

### Example 4: Query Service Discovery

```python
from central_hub.client import CentralHubClient

hub = CentralHubClient(base_url="http://central-hub:8001")

# Get all healthy services
services = await hub.get_services(status="healthy")

for service in services:
    print(f"{service['service_name']}: {service['host']}:{service['port']}")

# Find specific service
feature_service = await hub.get_service("feature-engineering")
if feature_service:
    print(f"Feature service URL: http://{feature_service['host']}:{feature_service['port']}")
```

### Example 5: Update Service Configuration

```python
from central_hub.api import ConfigAPI

api = ConfigAPI()

# Update config for a service
new_config = {
    "operational": {
        "symbols": ["EURUSD", "XAUUSD", "GBPUSD"],  # Added GBPUSD
        "websocket_reconnect_delay": 10  # Increased delay
    }
}

# Update (creates new version)
version = await api.update_config(
    service_name="polygon-live-collector",
    config_data=new_config,
    created_by="admin"
)

print(f"Config updated to version {version}")

# All instances of polygon-live-collector will hot-reload automatically!
```

### Example 6: Monitor Infrastructure Health

```python
from central_hub.monitoring import InfrastructureMonitor

monitor = InfrastructureMonitor()

# Check all infrastructure components
async def check_infrastructure():
    results = await monitor.check_all()

    for component, status in results.items():
        if status['status'] == 'healthy':
            print(f"✅ {component}: {status['response_time_ms']:.2f}ms")
        else:
            print(f"❌ {component}: {status['error_message']}")

# Run checks every 60 seconds
while True:
    await check_infrastructure()
    await asyncio.sleep(60)
```

### Example 7: Query Health Metrics

```sql
-- Check service health status
SELECT
    service_name,
    status,
    last_heartbeat,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - last_heartbeat)) as seconds_since_heartbeat
FROM service_registry
ORDER BY last_heartbeat DESC;

-- Check infrastructure health
SELECT
    component_name,
    status,
    response_time_ms,
    checked_at
FROM infrastructure_status
WHERE checked_at > CURRENT_TIMESTAMP - INTERVAL '1 hour'
ORDER BY checked_at DESC;

-- Service uptime
SELECT
    service_name,
    COUNT(*) as total_heartbeats,
    COUNT(CASE WHEN status = 'healthy' THEN 1 END) as healthy_count,
    (COUNT(CASE WHEN status = 'healthy' THEN 1 END) * 100.0 / COUNT(*)) as uptime_pct
FROM health_metrics
WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '24 hours'
GROUP BY service_name
ORDER BY uptime_pct DESC;
```

## Guidelines

- **ALWAYS** register services on startup
- **NEVER** hardcode config in services (use ConfigClient)
- **ALWAYS** send heartbeats (every 30 seconds)
- **VERIFY** Central Hub accessible before service starts
- **ENSURE** hot-reload enabled for config changes
- **VALIDATE** service dependencies before registration

## Critical Rules

1. **Config Hierarchy (MANDATORY):**
   - Secrets → ENV variables (NEVER in Central Hub database)
   - Operational settings → Central Hub (hot-reload supported)
   - Safe defaults → ConfigClient fallback

2. **Service Registration:**
   - **REGISTER** on startup (before accepting traffic)
   - **HEARTBEAT** every 30 seconds
   - **DEREGISTER** on graceful shutdown

3. **High Availability:**
   - **CACHE** config locally (if Central Hub down, use cache)
   - **FALLBACK** to safe defaults if both fail
   - **RETRY** registration with exponential backoff

4. **Hot-Reload Support:**
   - **ENABLE** config watching
   - **VALIDATE** new config before applying
   - **LOG** all config changes

5. **Health Monitoring:**
   - **CHECK** infrastructure every 60 seconds
   - **ALERT** if critical component down
   - **TRACK** service uptime percentage

## Common Tasks

### Add New Service Config
1. Define operational config JSON
2. Create entry in service_configs table
3. Update service code to use ConfigClient
4. Test hot-reload (update config, verify service reloads)
5. Monitor config version changes

### Update Existing Service Config
1. Use Central Hub API to update config
2. New version created automatically
3. All service instances hot-reload
4. Verify changes applied (check logs)
5. Rollback if needed (activate previous version)

### Monitor Service Health
1. Query service_registry for recent heartbeats
2. Check status column (healthy/degraded/down)
3. Review health_metrics for trends
4. Set up alerts for missing heartbeats
5. Auto-deregister dead services if enabled

### Debug Config Issues
1. Check service logs for ConfigClient errors
2. Verify Central Hub accessible (curl http://central-hub:8001/health)
3. Query service_configs for active config
4. Test config JSON validity
5. Verify safe defaults correct

## Troubleshooting

### Issue 1: Service Can't Register
**Symptoms:** Registration failing on startup
**Solution:**
- Verify Central Hub running (docker ps | grep central-hub)
- Check Central Hub accessible (curl http://central-hub:8001/health)
- Review registration payload (valid JSON?)
- Check PostgreSQL connection
- Test with minimal registration first

### Issue 2: Config Not Hot-Reloading
**Symptoms:** Config updates not applied
**Solution:**
- Verify hot-reload enabled in ConfigClient
- Check watch_config callback registered
- Review Central Hub logs for update events
- Test config version incremented
- Restart service if needed

### Issue 3: Services Marked as Down
**Symptoms:** Healthy services showing as down
**Solution:**
- Check heartbeat interval (too infrequent?)
- Verify service_timeout_seconds not too short
- Review network connectivity (service → Central Hub)
- Check heartbeat function running
- Test manual heartbeat

### Issue 4: Infrastructure Health Checks Failing
**Symptoms:** PostgreSQL/NATS/Kafka showing as down
**Solution:**
- Verify components actually running
- Check connection credentials correct
- Review network connectivity
- Test manual connection
- Increase timeout settings

### Issue 5: Config Versions Accumulating
**Symptoms:** Too many config versions in database
**Solution:**
- Implement config cleanup job
- Archive old versions (keep last 10)
- Review config update frequency (too often?)
- Use rollback feature to restore if needed
- Set retention policy

## Validation Checklist

After making changes to Central Hub:
- [ ] PostgreSQL connection working (service_registry accessible)
- [ ] Service registration API working (POST /register)
- [ ] Config distribution working (GET /config/{service_name})
- [ ] Hot-reload notifications sent (config updates propagate)
- [ ] Health monitoring active (infrastructure checks running)
- [ ] Heartbeat tracking working (last_heartbeat updated)
- [ ] Service discovery working (GET /services)
- [ ] Config versioning active (new versions created)
- [ ] Safe defaults defined for all services
- [ ] Infrastructure status tracked

## Related Skills

**Central Hub is used by ALL services:**
- All 18 microservices use ConfigClient
- `polygon-live-collector`, `tick-aggregator`, etc. - Register and fetch config
- `dashboard` - Queries service registry and health metrics
- `notification-hub` - Receives alerts about service health

## References

- Full Documentation: `docs/SERVICE_ARCHITECTURE_AND_FLOW.md` (lines 140-200)
- Planning Guide: `docs/PLANNING_SKILL_GUIDE.md` (Service 0, lines 50-250)
- Config Architecture: `docs/CONFIG_ARCHITECTURE.md` (Complete centralized config design)
- Database Schema: `docs/table_database_trading.md` (service_registry, service_configs, health_metrics)
- Code: `00-core-infrastructure/central-hub/`

---

**Created:** 2025-10-19
**Version:** 2.0.0
**Status:** Implemented
**Note:** Central Hub is the foundational service. All other services depend on it for configuration and service discovery.
