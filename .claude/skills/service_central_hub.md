# Central Hub Service Skill

**Service Name:** central-hub
**Type:** Core Infrastructure
**Port:** 7000
**Purpose:** Centralized coordination, service discovery, health monitoring, and **operational configuration management**

---

## 📋 QUICK REFERENCE

**When to use this skill:**
- Working on Central Hub service
- Adding new API endpoints
- Implementing coordination features
- **Managing service configurations**
- Debugging service discovery
- Monitoring infrastructure health

**Key Capabilities:**
- ✅ Centralized configuration management (PostgreSQL storage)
- ✅ Service discovery and registry
- ✅ Health monitoring and aggregation
- ✅ Workflow orchestration
- ✅ Infrastructure monitoring (databases, messaging)
- ✅ NATS/Kafka message broadcasting

---

## 🏗️ ARCHITECTURE

### **Service Structure**

```
central-hub/
├── base/
│   ├── app.py                    # Main FastAPI application
│   ├── api/
│   │   ├── config.py            # ⭐ Config management API (NEW)
│   │   ├── discovery.py         # Service discovery
│   │   ├── health.py            # Health monitoring
│   │   ├── metrics.py           # Metrics collection
│   │   └── infrastructure.py    # Infrastructure monitoring
│   ├── managers/
│   │   ├── connection_manager.py    # DB, cache, messaging connections
│   │   ├── coordination_manager.py  # Service registry, workflows
│   │   └── monitoring_manager.py    # Health checks, alerts
│   └── config/
│       ├── infrastructure.yaml      # Infrastructure configs (DB, NATS, Kafka)
│       └── database/
│           └── init-scripts/
│               └── 03-create-service-configs.sql  # ⭐ Service config tables
└── shared/
    └── components/
        └── config/
            └── client.py        # ⭐ Config client for services
```

### **Manager-Based Architecture**

```python
CentralHubService (BaseService)
├── ConnectionManager
│   ├── db_manager (PostgreSQL connection pool)
│   ├── cache_manager (DragonflyDB client)
│   ├── nats_client (NATS cluster connection)
│   └── kafka_producer (Kafka producer)
│
├── CoordinationManager
│   ├── service_registry (Service discovery)
│   ├── config_manager (Configuration management)  # ⭐
│   ├── workflow_engine (Workflow orchestration)
│   └── task_scheduler (Background tasks)
│
└── MonitoringManager
    ├── health_aggregator (Service health)
    ├── infrastructure_monitor (DB, messaging health)
    └── alert_manager (Alert dispatching)
```

---

## ⚠️ CONFIGURATION SYSTEMS (CRITICAL - READ FIRST!)

**Central Hub manages TWO DIFFERENT configuration systems:**

### **System 1: Infrastructure Config (Internal Only)**

**Class:** `InfrastructureConfigManager`
**Location:** `shared/components/utils/patterns/config.py`
**Purpose:** Central Hub's INTERNAL infrastructure settings
**Scope:** Central Hub ONLY
**Data Source:** YAML files (`infrastructure.yaml`)

```python
# ✅ Used ONLY within Central Hub
from components.utils.patterns.config import InfrastructureConfigManager

config = InfrastructureConfigManager(service_name="central-hub")
await config.load_config()
db_config = await config.get_database_config()
```

**What it manages:**
- Database connection settings (PostgreSQL, ClickHouse, DragonflyDB)
- Messaging infrastructure (NATS cluster, Kafka, Zookeeper)
- Health check configurations
- Service dependencies mapping
- Alert configurations

**File:** `base/config/infrastructure.yaml`

---

### **System 2: Operational Config (Services)**

**Class:** `ConfigClient`
**Location:** `shared/components/config/client.py`
**Purpose:** Runtime operational settings for ALL services
**Scope:** All 18 microservices
**Data Source:** PostgreSQL via Central Hub API

```python
# ✅ Used by ALL services (not Central Hub itself)
from shared.components.config import ConfigClient

client = ConfigClient("polygon-historical-downloader")
await client.init_async()
config = await client.get_config()
batch_size = config['operational']['batch_size']
```

**What it manages:**
- Operational parameters (batch_size, intervals, retries)
- Feature flags (enable/disable features)
- Business logic thresholds
- Service-specific runtime settings

**Storage:** PostgreSQL `service_configs` table + NATS hot-reload

---

### **Decision Matrix - Which Config System?**

| Use Case | System to Use | Example |
|----------|---------------|---------|
| **Central Hub infrastructure** | InfrastructureConfigManager | Database hosts, NATS cluster config |
| **Service operational settings** | ConfigClient | batch_size, gap_check_interval |
| **API keys, secrets** | ENV variables | POLYGON_API_KEY, DB passwords |

**IMPORTANT:**
- ❌ **NEVER** use InfrastructureConfigManager in other services (Central Hub only!)
- ✅ **ALWAYS** use ConfigClient for service operational configs
- ✅ **ALWAYS** use ENV vars for secrets and credentials

**Full Documentation:** `docs/CONFIG_ARCHITECTURE.md`

---

## ⭐ CENTRALIZED CONFIGURATION MANAGEMENT

### **Database Schema**

```sql
-- Current operational configs for all services
CREATE TABLE service_configs (
    service_name VARCHAR(100) PRIMARY KEY,
    config_json JSONB NOT NULL,
    version VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(100) DEFAULT 'system',
    updated_by VARCHAR(100) DEFAULT 'system',
    description TEXT,
    tags TEXT[],
    active BOOLEAN DEFAULT true
);

-- Complete audit trail of all config changes
CREATE TABLE config_audit_log (
    id BIGSERIAL PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    config_json JSONB NOT NULL,
    version VARCHAR(20) NOT NULL,
    action VARCHAR(20) NOT NULL,  -- 'created', 'updated', 'deleted'
    changed_by VARCHAR(100) NOT NULL,
    changed_at TIMESTAMPTZ DEFAULT NOW(),
    change_reason TEXT
);
```

### **Config API Endpoints**

#### **GET /api/v1/config/:service_name**
Fetch operational configuration for a service

```bash
curl http://suho-central-hub:7000/api/v1/config/polygon-historical-downloader

# Response:
{
  "service_name": "polygon-historical-downloader",
  "config": {
    "operational": {
      "gap_check_interval_hours": 1,
      "batch_size": 100,
      "max_retries": 3
    },
    "download": {
      "start_date": "today-7days",
      "end_date": "today"
    },
    "features": {
      "enable_gap_verification": true
    }
  },
  "version": "1.0.0",
  "updated_at": 1729327200000
}
```

#### **POST /api/v1/config/:service_name**
Update service configuration (with NATS broadcast)

```bash
curl -X POST http://suho-central-hub:7000/api/v1/config/polygon-historical-downloader \
  -H "Content-Type: application/json" \
  -d '{
    "operational": {
      "gap_check_interval_hours": 2
    }
  }'

# Automatically:
# 1. Stores in PostgreSQL
# 2. Creates audit log entry
# 3. Broadcasts to NATS: config.update.polygon-historical-downloader
# 4. Services auto-reload (if subscribed)
```

#### **GET /api/v1/config/history/:service_name**
Get configuration change history

```bash
curl http://suho-central-hub:7000/api/v1/config/history/polygon-historical-downloader?limit=5

# Response:
{
  "service_name": "polygon-historical-downloader",
  "history": [
    {
      "version": "1.1.0",
      "action": "updated",
      "changed_by": "admin",
      "changed_at": 1729327200000,
      "config": {...}
    }
  ],
  "total": 15
}
```

---

## 🔧 CRITICAL RULES - CENTRALIZED CONFIG

### **Rule 1: Config Hierarchy (What Goes Where)**

```
❌ NEVER PUT IN CENTRAL HUB:
- Database credentials (CLICKHOUSE_PASSWORD, POSTGRES_PASSWORD)
- API keys and secrets (POLYGON_API_KEY, AWS_ACCESS_KEY)
- Infrastructure hostnames (CLICKHOUSE_HOST, NATS_URL)
→ These MUST be in ENV VARS

✅ ALWAYS PUT IN CENTRAL HUB:
- Operational settings (batch_size, retry_delay, intervals)
- Feature flags (enable_verification, enable_cache)
- Business logic (download_range, thresholds)
- Tuning parameters (max_concurrent, buffer_size)
→ These are safe to change at runtime
```

### **Rule 2: Config Storage Pattern**

```python
# Service config structure in PostgreSQL
{
  "operational": {
    "batch_size": 100,
    "max_retries": 3,
    "retry_delay_seconds": 10
  },
  "features": {
    "enable_feature_x": true,
    "enable_feature_y": false
  },
  "business_logic": {
    "threshold": 0.95,
    "interval_hours": 1
  }
}
```

### **Rule 3: NATS Broadcast Pattern**

```python
# When config updated, broadcast to:
Subject: config.update.{service_name}

Message:
{
  "service_name": "polygon-historical-downloader",
  "config": {...},
  "version": "1.1.0",
  "updated_at": 1729327200000,
  "updated_by": "admin"
}

# Services subscribe and auto-reload (optional)
```

### **Rule 4: Fallback Safety**

```
Services MUST work even if Central Hub is down:
1. Cache config locally (in-memory + optional disk)
2. Refresh every 5 minutes (default TTL)
3. Use safe defaults if Hub unavailable
4. Log warning but continue operation

✅ Non-critical dependency (graceful degradation)
❌ Never make Hub a hard dependency for service startup
```

---

## 📊 SERVICE DISCOVERY & HEALTH

### **Service Registry**

```python
# Services self-register on startup
POST /api/v1/discovery/register
{
  "service_name": "polygon-historical-downloader",
  "host": "suho-polygon-historical",
  "port": 8001,
  "health_endpoint": "/health",
  "metadata": {
    "version": "1.0.0",
    "instance_id": "polygon-historical-1"
  }
}
```

### **Health Aggregation**

```python
# Central Hub monitors all services
GET /api/v1/health/services

# Response:
{
  "total_services": 18,
  "healthy": 17,
  "unhealthy": 1,
  "services": {
    "polygon-historical-downloader": "healthy",
    "tick-aggregator": "healthy",
    "data-bridge": "degraded"
  }
}
```

---

## 🔄 TYPICAL WORKFLOWS

### **Workflow 1: Service Fetches Config on Startup**

```
Service Startup
    ↓
1. Load critical configs from ENV VARS
   (DB credentials, NATS_URL, etc.)
    ↓
2. Connect to Central Hub
   GET /api/v1/config/{service_name}
    ↓
3. Merge with local defaults
   (Operational configs override defaults)
    ↓
4. Subscribe to NATS config.update.{service_name}
   (For hot-reload)
    ↓
5. Start service with merged config
```

### **Workflow 2: Admin Updates Config**

```
Admin Action
    ↓
POST /api/v1/config/{service_name}
    ↓
Central Hub:
1. Validate config JSON
2. Store in PostgreSQL (UPSERT)
3. Create audit log entry (trigger)
4. Broadcast via NATS
    ↓
All Service Instances:
1. Receive NATS notification
2. Fetch updated config
3. Reload without restart
4. Log config change
```

### **Workflow 3: Rollback Config**

```sql
-- Rollback to previous version
SELECT rollback_config(
  'polygon-historical-downloader',
  '1.0.0',  -- target version
  'admin'   -- who rolled back
);

-- Automatically:
-- 1. Fetches config from audit log
-- 2. Updates current config
-- 3. Creates rollback audit entry
-- 4. Broadcasts update via NATS
```

---

## ✅ VALIDATION CHECKLIST

### **Adding New Service Config**

- [ ] Config follows hierarchy (operational/features/business_logic)
- [ ] No secrets or credentials in config JSON
- [ ] Safe defaults provided in service code
- [ ] Service handles Hub unavailability gracefully
- [ ] Config changes tested in staging first
- [ ] Audit trail reviewed after deployment

### **Updating Existing Config**

- [ ] Change reason documented
- [ ] Version incremented
- [ ] Tested with target service
- [ ] Rollback plan prepared
- [ ] NATS broadcast verified
- [ ] Service reloaded successfully (if hot-reload enabled)

### **Monitoring Config Health**

- [ ] Central Hub /health endpoint returns 200
- [ ] PostgreSQL connection healthy
- [ ] service_configs table accessible
- [ ] NATS cluster available for broadcasts
- [ ] Audit log growing (changes being tracked)

---

## 🚨 COMMON ISSUES & SOLUTIONS

### **Issue 1: Service Can't Fetch Config (500 Error)**

**Symptoms:**
- GET /api/v1/config/:service returns 500
- Service logs show connection errors

**Debug Steps:**
```bash
# 1. Check Central Hub health
curl http://suho-central-hub:7000/health

# 2. Verify PostgreSQL connection
docker exec suho-central-hub python3 -c "
import asyncio, asyncpg
async def test():
    conn = await asyncpg.connect('postgresql://suho_admin:...@suho-postgresql:5432/suho_trading')
    print(await conn.fetchval('SELECT COUNT(*) FROM service_configs'))
    await conn.close()
asyncio.run(test())
"

# 3. Check db_manager initialization
docker logs suho-central-hub | grep "db_manager\|Connection Manager"
```

**Common Causes:**
- db_manager not initialized in ConnectionManager
- PostgreSQL connection pool not created
- service_configs table doesn't exist

### **Issue 2: NATS Broadcast Not Received**

**Symptoms:**
- Config updated but services don't reload
- No NATS messages in logs

**Debug Steps:**
```bash
# 1. Check NATS connection
docker exec suho-central-hub python3 -c "
import asyncio, nats
async def test():
    nc = await nats.connect('nats://nats-1:4222')
    print('NATS connected:', nc.is_connected)
    await nc.close()
asyncio.run(test())
"

# 2. Subscribe to config updates
nats sub -s nats://localhost:4222 "config.update.*"

# 3. Trigger config update and watch
```

**Common Causes:**
- NATS client not initialized
- Wrong subject pattern
- Service not subscribed to config.update.{service_name}

### **Issue 3: Config Not Persisting**

**Symptoms:**
- POST returns success but config not in database
- Config reverts after Central Hub restart

**Debug Steps:**
```bash
# Check if config actually stored
docker exec suho-postgresql psql -U suho_admin -d suho_trading -c \
  "SELECT service_name, version, updated_at FROM service_configs"

# Check audit log
docker exec suho-postgresql psql -U suho_admin -d suho_trading -c \
  "SELECT * FROM config_audit_log ORDER BY changed_at DESC LIMIT 5"
```

**Common Causes:**
- Transaction not committed
- Trigger not firing
- Wrong database connection

---

## 📚 INTEGRATION EXAMPLES

### **Example 1: Add New Service Config**

```sql
-- Insert new service config
INSERT INTO service_configs (service_name, config_json, version, description, tags)
VALUES (
  'new-service-name',
  '{
    "operational": {
      "batch_size": 100,
      "max_retries": 3
    },
    "features": {
      "enable_feature_a": true
    }
  }'::jsonb,
  '1.0.0',
  'New service description',
  ARRAY['category', 'tag']
);
```

### **Example 2: Service Config Client (Python)**

```python
from shared.components.config.client import ConfigClient

class MyService:
    def __init__(self):
        # Critical configs from ENV
        self.db_host = os.getenv('CLICKHOUSE_HOST')
        self.db_password = os.getenv('CLICKHOUSE_PASSWORD')

        # Operational configs from Central Hub
        self.config_client = ConfigClient(
            service_name='my-service',
            central_hub_url='http://suho-central-hub:7000'
        )

    async def init_async(self):
        # Fetch operational configs
        config = await self.config_client.get_config()

        self.batch_size = config['operational']['batch_size']
        self.max_retries = config['operational']['max_retries']

        # Subscribe to updates (hot-reload)
        await self.config_client.subscribe_to_updates()
```

---

## 🎯 BEST PRACTICES

1. **Config Versioning**
   - Use semantic versioning (1.0.0, 1.1.0, 2.0.0)
   - Increment patch for minor tweaks
   - Increment minor for new features
   - Increment major for breaking changes

2. **Audit Trail**
   - Always include change_reason in updates
   - Review history before rollback
   - Monitor audit log size (archive old entries)

3. **NATS Broadcasting**
   - Best-effort delivery (non-blocking)
   - Services should poll if no NATS message
   - Use TTL-based cache refresh as backup

4. **Testing**
   - Test config changes in staging first
   - Verify service behavior with new config
   - Have rollback plan ready
   - Monitor metrics after deployment

5. **Security**
   - Never store secrets in service_configs
   - Use environment variables for credentials
   - Implement API key auth for config endpoints
   - Audit who changed what when

---

## 🔍 MONITORING & OBSERVABILITY

### **Key Metrics**

```python
# Config fetch metrics
config_fetch_total{service, status}  # success/failure
config_fetch_duration_seconds{service}
config_cache_hit_total{service}
config_fallback_to_defaults_total{service}

# Update metrics
config_update_total{service, action}
config_version{service, version}

# Health metrics
config_api_health{endpoint}
database_connection_health
nats_broadcast_success_rate
```

### **Alerts**

```yaml
# Alert if many services falling back to defaults
- alert: CentralHubConfigDown
  expr: sum(rate(config_fallback_to_defaults_total[5m])) > 5

# Alert if config API slow
- alert: ConfigAPISlowResponse
  expr: config_fetch_duration_seconds > 1.0

# Alert if database unavailable
- alert: ConfigDatabaseDown
  expr: database_connection_health == 0
```

---

## 📖 SUMMARY

**Central Hub = Configuration Provider for 18+ Services**

**Core Responsibilities:**
- ✅ Store operational configs in PostgreSQL
- ✅ Provide API for config CRUD operations
- ✅ Broadcast updates via NATS
- ✅ Maintain complete audit trail
- ✅ Enable zero-downtime config changes

**Critical Success Factors:**
1. Keep secrets in ENV VARS, not database
2. Ensure graceful degradation (Hub down → use defaults)
3. Test config changes before production
4. Monitor config fetch health
5. Use audit trail for debugging

**Use this skill when:**
- Adding new service configs
- Updating existing configs
- Debugging config-related issues
- Implementing config hot-reload
- Managing service coordination
