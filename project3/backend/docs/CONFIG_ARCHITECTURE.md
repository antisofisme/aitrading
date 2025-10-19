# Configuration Architecture - Suho Trading Platform

**Last Updated:** 2025-10-19
**Status:** ✅ Production Ready

---

## 📖 Overview

Suho Trading Platform uses **TWO DISTINCT configuration systems**, each serving different purposes. Understanding when to use each system is **CRITICAL** for maintaining architectural consistency.

---

## 🎯 Two Configuration Systems

### **System 1: Infrastructure Configuration** (File-Based)

**Class:** `InfrastructureConfigManager`
**Location:** `central-hub/shared/components/utils/patterns/config.py`
**Purpose:** Central Hub's INTERNAL infrastructure settings
**Scope:** Central Hub ONLY
**Data Source:** YAML/JSON files (`infrastructure.yaml`)

```python
from components.utils.patterns.config import InfrastructureConfigManager

# Used by Central Hub internally
config = InfrastructureConfigManager(service_name="central-hub")
await config.load_config()
db_config = await config.get_database_config()
```

**What it manages:**
- ✅ Database connection settings (PostgreSQL, ClickHouse, DragonflyDB)
- ✅ Messaging infrastructure (NATS cluster, Kafka, Zookeeper)
- ✅ Health check configurations
- ✅ Service dependencies mapping
- ✅ Alert configurations

---

### **System 2: Operational Configuration** (Database-Based)

**Class:** `ConfigClient`
**Location:** `shared/components/config/client.py`
**Purpose:** Runtime operational settings for ALL services
**Scope:** All 18 microservices
**Data Source:** PostgreSQL via Central Hub API

```python
from shared.components.config import ConfigClient

# Used by ALL services
config_client = ConfigClient("polygon-historical-downloader")
await config_client.init_async()
config = await config_client.get_config()
batch_size = config['operational']['batch_size']
```

**What it manages:**
- ✅ Operational parameters (batch_size, intervals, retries)
- ✅ Feature flags (enable/disable features)
- ✅ Business logic thresholds
- ✅ Service-specific settings
- ✅ Runtime tunable parameters

---

## 📊 Decision Matrix - Which System to Use?

| Config Type | System to Use | Example | Storage |
|-------------|---------------|---------|---------|
| **API keys, secrets** | **ENV variables** | `POLYGON_API_KEY` | `.env` file |
| **Database host/port** | **InfrastructureConfigManager** | `suho-postgresql:5432` | `infrastructure.yaml` |
| **Batch sizes, intervals** | **ConfigClient** | `batch_size: 100` | PostgreSQL |
| **Feature flags** | **ConfigClient** | `enable_verification: true` | PostgreSQL |
| **Health check settings** | **InfrastructureConfigManager** | `timeout: 5` | `infrastructure.yaml` |
| **Service dependencies** | **InfrastructureConfigManager** | `requires: [postgresql, nats]` | `infrastructure.yaml` |
| **Retry counts** | **ConfigClient** | `max_retries: 3` | PostgreSQL |
| **Alert rules** | **InfrastructureConfigManager** | `severity: critical` | `infrastructure.yaml` |

---

## 🏗️ Configuration Hierarchy (All Services)

Every service follows this **3-layer hierarchy**:

```
┌─────────────────────────────────────────┐
│   Layer 1: Environment Variables        │  ← CRITICAL
│   ─────────────────────────────────────  │
│   - API keys (POLYGON_API_KEY)          │
│   - Secrets (DB passwords)              │
│   - Infrastructure (hostnames, ports)   │
│   → Source: .env file                   │
│   → Priority: HIGHEST                   │
│   → NEVER in Central Hub!               │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│   Layer 2: Operational Config           │  ← RUNTIME
│   ─────────────────────────────────────  │
│   - Batch sizes, intervals              │
│   - Feature flags                       │
│   - Business logic thresholds           │
│   → Source: PostgreSQL (ConfigClient)   │
│   → Priority: MEDIUM                    │
│   → Hot-reload capable                  │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│   Layer 3: Safe Defaults                │  ← FALLBACK
│   ─────────────────────────────────────  │
│   - Hardcoded in code                   │
│   → Source: ConfigClient safe_defaults  │
│   → Priority: LOWEST                    │
│   → Used ONLY when Hub unavailable      │
└─────────────────────────────────────────┘
```

**Golden Rule:**
- **Secrets** → ENV vars
- **Infrastructure** → InfrastructureConfigManager (Central Hub only)
- **Operational** → ConfigClient (all services)

---

## 🔍 Detailed System Comparison

### **InfrastructureConfigManager** (File-Based)

#### **Architecture:**
```
┌─────────────────────────────────────┐
│      Central Hub                    │
│                                     │
│  ┌──────────────────────────────┐  │
│  │ InfrastructureConfigManager  │  │
│  │                              │  │
│  │  1. Load infrastructure.yaml │  │
│  │  2. Merge with ENV vars      │  │
│  │  3. Priority system          │  │
│  │  4. Provide to managers      │  │
│  └──────────────────────────────┘  │
│           ↓                         │
│  Used by CoordinationManager,      │
│  MonitoringManager, etc.           │
└─────────────────────────────────────┘
```

#### **Priority System:**
1. **Environment Variables** (priority: 100) - Highest
2. **Environment-specific file** (`production.json`, priority: 50)
3. **Service-specific file** (`central-hub.json`, priority: 40)
4. **Default file** (`default.json`, priority: 10) - Lowest

#### **Example Usage:**
```python
from components.utils.patterns.config import InfrastructureConfigManager

# Initialize
config = InfrastructureConfigManager(service_name="central-hub")
await config.load_config()

# Get database config
db_config = await config.get_database_config()
print(db_config)
# {
#   "host": "suho-postgresql",
#   "port": 5432,
#   "database": "suho_trading",
#   "username": "suho_admin"
# }

# Get messaging config
nats_config = await config.get("messaging.nats-1")
print(nats_config)
# {
#   "host": "nats-1",
#   "port": 4222,
#   "management_port": 8222,
#   "health_check": {...}
# }
```

#### **Configuration File (infrastructure.yaml):**
```yaml
databases:
  postgresql:
    host: suho-postgresql
    port: 5432
    type: postgres
    health_check:
      method: tcp
      timeout: 5
      interval: 30
    critical: true

messaging:
  nats-1:
    host: nats-1
    port: 4222
    management_port: 8222
    health_check:
      method: http
      endpoint: /healthz
```

---

### **ConfigClient** (Database-Based)

#### **Architecture:**
```
┌─────────────────────────────────────────────┐
│           Central Hub API                   │
│                                             │
│   PostgreSQL: service_configs table         │
│   ┌──────────────────────────────────────┐  │
│   │ service_name | config_json | version │  │
│   │ polygon-hist | {...}       | 1.0.0   │  │
│   │ tick-aggr    | {...}       | 1.2.0   │  │
│   └──────────────────────────────────────┘  │
│                                             │
│   API Endpoints:                            │
│   - GET /api/v1/config/{service}            │
│   - POST /api/v1/config/{service}           │
│   - GET /api/v1/config/history/{service}    │
└──────────────┬──────────────────────────────┘
               │ HTTP + NATS
        ┌──────┼──────┬──────┬──────┐
        ↓      ↓      ↓      ↓      ↓
    Service1  Svc2  Svc3  ...  Svc18
    (ConfigClient instances)

Each Service:
├── 1. Fetch from API (GET)
├── 2. Cache locally (5 min TTL)
├── 3. Fallback to safe defaults
└── 4. Subscribe to NATS for hot-reload
```

#### **Workflow:**
1. **Service Startup:**
   - ConfigClient fetches initial config from Central Hub API
   - Caches config locally (default: 5 minutes)
   - Subscribes to NATS for updates

2. **Runtime Access:**
   - First access: Fetch from cache (if valid)
   - Cache expired: Fetch from API, update cache
   - API unavailable: Use safe defaults

3. **Config Update (Admin):**
   - Admin updates via `POST /api/v1/config/{service}`
   - Central Hub saves to PostgreSQL
   - NATS broadcast: `config.update.{service}`
   - ConfigClient receives update
   - Cache updated instantly
   - **Service continues running with new config!**

#### **Example Usage:**
```python
from shared.components.config import ConfigClient

# 1. Initialize with safe defaults
config_client = ConfigClient(
    service_name="polygon-historical-downloader",
    central_hub_url="http://suho-central-hub:7000",
    safe_defaults={
        "operational": {
            "batch_size": 100,
            "gap_check_interval_hours": 1
        }
    },
    enable_nats_updates=True  # Enable hot-reload
)

# 2. Async init (fetch initial config)
await config_client.init_async()

# 3. Get config (uses cache if valid)
config = await config_client.get_config()
batch_size = config['operational']['batch_size']

# 4. Force refresh (ignore cache)
config = await config_client.get_config(force_refresh=True)

# 5. Register callback for updates
def on_config_update(new_config):
    print(f"Config updated! New batch_size: {new_config['operational']['batch_size']}")

config_client.on_config_update(on_config_update)

# 6. Cleanup
await config_client.shutdown()
```

---

## 🚀 Integration Patterns

### **Pattern 1: Service Configuration Class**

**Recommended pattern for all 18 services:**

```python
import os
from shared.components.config import ConfigClient

class ServiceConfig:
    """
    Complete service configuration following 3-layer hierarchy
    """

    def __init__(self):
        # === LAYER 1: CRITICAL CONFIGS (ENV VARS) ===
        self.polygon_api_key = os.getenv("POLYGON_API_KEY")
        self.clickhouse_host = os.getenv("CLICKHOUSE_HOST")
        self.clickhouse_password = os.getenv("CLICKHOUSE_PASSWORD")

        # Validate critical configs
        if not self.polygon_api_key:
            raise ValueError("POLYGON_API_KEY not set")

        # === LAYER 2: OPERATIONAL CONFIGS (CENTRAL HUB) ===
        self._config_client = ConfigClient(
            service_name="polygon-historical-downloader",
            central_hub_url=os.getenv("CENTRAL_HUB_URL", "http://suho-central-hub:7000"),
            safe_defaults=self._get_safe_defaults(),
            cache_ttl_seconds=300,
            enable_nats_updates=True
        )

        self._operational_config = None

    def _get_safe_defaults(self) -> dict:
        """
        LAYER 3: Safe fallback configuration
        CRITICAL: Service MUST work with these defaults!
        """
        return {
            "operational": {
                "batch_size": 100,
                "max_retries": 3,
                "gap_check_interval_hours": 1
            },
            "features": {
                "enable_verification": True,
                "enable_auto_backfill": True
            }
        }

    async def init_async(self):
        """Async init - fetch operational config"""
        await self._config_client.init_async()
        self._operational_config = await self._config_client.get_config()

        # Register hot-reload callback
        def on_update(new_config):
            self._operational_config = new_config
            print("✅ Config hot-reloaded!")

        self._config_client.on_config_update(on_update)

    async def shutdown(self):
        """Cleanup"""
        await self._config_client.shutdown()

    # === CONFIG PROPERTIES ===

    @property
    def batch_size(self) -> int:
        """Get batch size from operational config"""
        return self._operational_config.get('operational', {}).get('batch_size', 100)

    @property
    def gap_check_interval_hours(self) -> int:
        """Get gap check interval from operational config"""
        return self._operational_config.get('operational', {}).get('gap_check_interval_hours', 1)
```

**Usage in Service:**
```python
async def main():
    # 1. Create config (loads ENV VARS)
    config = ServiceConfig()

    # 2. Async init (fetch from Central Hub)
    await config.init_async()

    # 3. Use config
    print(f"API Key: {config.polygon_api_key[:10]}...")
    print(f"Batch size: {config.batch_size}")
    print(f"Gap interval: {config.gap_check_interval_hours} hours")

    # 4. Start service with centralized config
    service = MyService(config)
    await service.start()

    # Config auto-reloads if admin updates in Central Hub!

    # 5. Cleanup
    await config.shutdown()
```

---

### **Pattern 2: Central Hub Infrastructure Config**

**For Central Hub internal use only:**

```python
from components.utils.patterns.config import InfrastructureConfigManager

class CentralHubConfig:
    """
    Central Hub's internal infrastructure configuration
    """

    def __init__(self):
        # Load infrastructure config from files
        self.infra_config = InfrastructureConfigManager(
            service_name="central-hub",
            environment="production"
        )

    async def init_async(self):
        """Load infrastructure configuration"""
        await self.infra_config.load_config()

    async def get_database_config(self, db_name: str) -> dict:
        """Get database configuration"""
        databases = await self.infra_config.get("databases", {})
        return databases.get(db_name, {})

    async def get_messaging_config(self, msg_name: str) -> dict:
        """Get messaging configuration"""
        messaging = await self.infra_config.get("messaging", {})
        return messaging.get(msg_name, {})
```

---

## 🔄 Hot-Reload Flow

### **How Hot-Reload Works:**

```
Admin Updates Config
    ↓
POST /api/v1/config/polygon-historical-downloader
    ↓
Central Hub API:
  1. Validates config
  2. Saves to PostgreSQL service_configs table
  3. Broadcasts NATS message: config.update.polygon-historical-downloader
    ↓
ConfigClient (in polygon-historical service):
  1. Receives NATS message
  2. Parses new config
  3. Updates local cache
  4. Triggers registered callbacks
    ↓
Service Continues Running
  ✓ No restart needed
  ✓ Zero downtime
  ✓ New config active immediately
```

### **Example Hot-Reload:**

```bash
# Admin updates batch_size from 100 to 200
curl -X POST http://suho-central-hub:7000/api/v1/config/polygon-historical-downloader \
  -H "Content-Type: application/json" \
  -d '{
    "operational": {
      "batch_size": 200,
      "gap_check_interval_hours": 1
    }
  }'

# Response:
# {
#   "status": "success",
#   "message": "Config updated and broadcasted",
#   "version": "1.1.0"
# }

# Service logs:
# [2025-10-19 10:30:45] 🔄 Config hot-reloaded for polygon-historical-downloader (version: 1.1.0)
# [2025-10-19 10:30:45] ✅ New batch_size: 200
```

---

## ❌ Common Mistakes

### **Mistake 1: Using InfrastructureConfigManager in Services**

```python
# ❌ WRONG - Don't use in services!
from components.utils.patterns.config import InfrastructureConfigManager

class PolygonService:
    def __init__(self):
        self.config = InfrastructureConfigManager("polygon-historical")
        # This won't work! InfrastructureConfigManager is for Central Hub only

# ✅ CORRECT - Use ConfigClient
from shared.components.config import ConfigClient

class PolygonService:
    def __init__(self):
        self.config_client = ConfigClient("polygon-historical-downloader")
```

---

### **Mistake 2: Putting Secrets in ConfigClient**

```python
# ❌ WRONG - Never put secrets in Central Hub!
config_client = ConfigClient(
    service_name="my-service",
    safe_defaults={
        "secrets": {
            "api_key": "abc123xyz"  # NEVER DO THIS!
        }
    }
)

# ✅ CORRECT - Secrets in ENV vars
import os

class Config:
    def __init__(self):
        # Secrets from ENV
        self.api_key = os.getenv("POLYGON_API_KEY")

        # Operational from ConfigClient
        self.config_client = ConfigClient(
            service_name="my-service",
            safe_defaults={"operational": {"batch_size": 100}}
        )
```

---

### **Mistake 3: Hardcoding Operational Configs**

```python
# ❌ WRONG - Hardcoded values
class Service:
    def __init__(self):
        self.batch_size = 100  # Hardcoded, can't change without rebuild
        self.gap_interval = 1

# ✅ CORRECT - Use ConfigClient
class Service:
    def __init__(self, config: ServiceConfig):
        self.config = config

    async def process(self):
        batch_size = self.config.batch_size  # From ConfigClient, hot-reload capable
        gap_interval = self.config.gap_check_interval_hours
```

---

## 📚 API Reference

### **ConfigClient Methods**

```python
# Initialize
client = ConfigClient(
    service_name: str,                    # Required
    central_hub_url: str = "...",         # Central Hub URL
    cache_ttl_seconds: int = 300,         # Cache TTL (5 min)
    enable_nats_updates: bool = False,    # Enable hot-reload
    safe_defaults: Optional[dict] = None  # Fallback config
)

# Async init
await client.init_async()

# Get config
config = await client.get_config(force_refresh=False)

# Get value by path
batch_size = client.get_value("operational.batch_size", default=100)

# Register callback
client.on_config_update(callback_function)

# Subscribe to updates
await client.subscribe_to_updates()

# Cleanup
await client.shutdown()
```

### **InfrastructureConfigManager Methods**

```python
# Initialize
config = InfrastructureConfigManager(
    service_name: str,
    environment: str = "development"
)

# Load config
await config.load_config()

# Get value
value = await config.get("database.host", default=None)

# Get section
db_config = await config.get_database_config()
cache_config = await config.get_cache_config()

# Get all
all_config = config.get_all()

# Reload
await config.reload()
```

---

## 🎯 Best Practices

### **1. Always Provide Safe Defaults**
```python
# ✅ Good - Service works even if Hub down
config_client = ConfigClient(
    service_name="my-service",
    safe_defaults={
        "operational": {
            "batch_size": 100,
            "max_retries": 3
        }
    }
)
```

### **2. Use Properties for Config Access**
```python
# ✅ Good - Clean, type-safe interface
class Config:
    @property
    def batch_size(self) -> int:
        return self._operational_config.get('operational', {}).get('batch_size', 100)
```

### **3. Separate Concerns**
```python
# ✅ Good - Clear separation
class Config:
    # ENV vars - Critical
    self.api_key = os.getenv("API_KEY")

    # ConfigClient - Operational
    self._config_client = ConfigClient(...)

    # Code - Safe defaults
    safe_defaults = {"batch_size": 100}
```

### **4. Test Fallback Scenarios**
```python
# ✅ Good - Test with Hub unavailable
async def test_fallback():
    client = ConfigClient(
        service_name="test-service",
        central_hub_url="http://invalid-url:9999",  # Hub down
        safe_defaults={"operational": {"batch_size": 100}}
    )

    config = await client.get_config()
    assert config['operational']['batch_size'] == 100  # Uses defaults
```

---

## 📖 Related Documentation

- **ConfigClient Documentation:** `shared/components/config/README.md`
- **Central Hub Skill:** `.claude/skills/service_central_hub.md`
- **Config Management Skill:** `.claude/skills/centralized_config_management.md`
- **Review Report:** `docs/CENTRAL_HUB_CONFIG_REVIEW_REPORT.md`
- **Implementation Summary:** `docs/SKILLS_CENTRALIZED_CONFIG_SUMMARY.md`

---

## 🆘 Troubleshooting

### **Issue: Config not found (404)**

**Symptom:**
```
ValueError: Config not found for service: my-service
```

**Solution:**
Add config in Central Hub database:
```bash
curl -X POST http://suho-central-hub:7000/api/v1/config/my-service \
  -H "Content-Type: application/json" \
  -d '{"operational": {"batch_size": 100}}'
```

---

### **Issue: Hot-reload not working**

**Debug:**
1. Check NATS connection:
   ```bash
   docker logs my-service | grep NATS
   ```

2. Verify `enable_nats_updates=True`

3. Check NATS broadcast:
   ```bash
   docker logs suho-central-hub | grep "Config updated and broadcasted"
   ```

---

## 🏁 Summary

**Two Systems, Different Purposes:**

| System | Purpose | Users | Source |
|--------|---------|-------|--------|
| **InfrastructureConfigManager** | Central Hub infrastructure | Central Hub only | YAML files |
| **ConfigClient** | Service operational configs | All 18 services | PostgreSQL API |

**When to Use What:**
- **Secrets** → ENV vars
- **Infrastructure** → InfrastructureConfigManager (Central Hub only)
- **Operational** → ConfigClient (all services)

**Key Benefits:**
- ✅ Clear separation of concerns
- ✅ Hot-reload for operational configs
- ✅ Audit trail for compliance
- ✅ Zero-downtime updates
- ✅ Graceful degradation (fallback to defaults)

---

**Version:** 1.0.0
**Last Updated:** 2025-10-19
**Status:** ✅ Production Ready
