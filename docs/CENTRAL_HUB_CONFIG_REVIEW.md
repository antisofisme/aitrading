# Central Hub - Centralized Config Review & Implementation Plan

**Date:** 2025-10-19
**Purpose:** Review existing Central Hub architecture and propose best approach for implementing centralized configuration management

---

## 📊 CURRENT STATE ANALYSIS

### **Architecture Overview**

```
Central Hub (FastAPI @ port 7000)
├── Base Service (BaseService pattern)
├── 3 Focused Managers:
│   ├── ConnectionManager (DB, cache, messaging)
│   ├── MonitoringManager (health, infrastructure, alerts)
│   └── CoordinationManager (registry, routing, workflows)
├── ConfigManager (file + env vars)
└── API Endpoints (v1 + backward compat)
```

### **Existing Config Capabilities**

#### **✅ WHAT ALREADY WORKS**

1. **Infrastructure Configs** (`/api/v1/config/database/:name`, `/api/v1/config/messaging/:name`)
   - Location: `base/api/config.py:174-236`
   - Source: `base/config/infrastructure.yaml`
   - Provides: PostgreSQL, ClickHouse, DragonflyDB, NATS, Kafka configs
   - **Status:** ✅ FULLY FUNCTIONAL

2. **ConfigManager** (`shared/components/utils/patterns/config.py`)
   - Pattern: File-based + environment variable hierarchy
   - Priority: ENV VARS (100) > env.json (50) > service.json (40) > default.json (10)
   - Features: Deep merge, dot notation access, validation
   - **Status:** ✅ PRODUCTION-READY

3. **Config API Endpoints** (`base/api/config.py`)
   - `GET /api/v1/config/` - Global config
   - `GET /api/v1/config/:service_name` - Service-specific (⚠️ TODO)
   - `POST /api/v1/config/update` - Update config (⚠️ TODO)
   - `GET /api/v1/config/history/:service_name` - History (⚠️ TODO)
   - **Status:** ⚠️ SKELETON EXISTS, NOT IMPLEMENTED

#### **❌ WHAT'S MISSING**

1. **PostgreSQL Storage for Service Configs**
   - No `service_configs` table exists
   - No `config_audit_log` table
   - Configs currently hardcoded in code (lines 80-94)

2. **Service-Specific Config Storage/Retrieval**
   - Marked as TODO (line 83, 96-153)
   - No database integration
   - No NATS broadcast on updates

3. **Config Client Library**
   - No shared library for services to fetch configs
   - Services still use local config files

---

## 🏗️ EXISTING ARCHITECTURE - STRENGTHS

### **1. Manager-Based Architecture (God Object Refactored)**

```python
# base/app.py:66-95
class CentralHubService(BaseService):
    def __init__(self):
        self.connection_manager: ConnectionManager  # DB, cache, messaging
        self.monitoring_manager: MonitoringManager  # Health, alerts
        self.coordination_manager: CoordinationManager  # Registry, workflows
```

**✅ Benefits:**
- Clean separation of concerns
- Easy to extend
- Well-tested pattern

**📍 Integration Point:**
- Add service config management to **CoordinationManager**
- Already has `ConfigManager` instance (line 47, 65-66)

### **2. Existing ConfigManager Pattern**

```python
# shared/components/utils/patterns/config.py
class ConfigManager:
    - File + ENV VAR hierarchy
    - Deep merge support
    - Validation
    - Feature flags
    - Hot reload (async)
```

**✅ Perfect Foundation:**
- Already supports multiple config sources
- Has `add_source()` method for extensibility
- Can add `remote` source type (line 109-110, 154-158)

**📍 Integration Point:**
- Add `remote` config source pointing to Central Hub API
- Fallback to local files if Hub unavailable

### **3. Database Integration Ready**

```python
# base/managers/connection_manager.py
self.connection_manager.db_manager  # PostgreSQL connection pool
```

**✅ Database Already Available:**
- AsyncPG connection pool
- Used by other managers
- Transaction support

**📍 Integration Point:**
- Create `service_configs` and `config_audit_log` tables
- Integrate with existing `db_manager`

### **4. NATS Integration Ready**

```python
# base/managers/connection_manager.py
self.connection_manager.nats_client  # NATS connection
```

**✅ NATS Already Connected:**
- 3-node cluster support
- Publish/subscribe ready

**📍 Integration Point:**
- Publish config updates to `config.update.{service_name}`
- Services subscribe for hot-reload

---

## ⚠️ ARCHITECTURE CONCERNS

### **1. Config API TODOs Not Implemented**

**Current Code:**
```python
# base/api/config.py:80-94
@config_router.get("/{service_name}")
async def get_service_config(service_name: str):
    # TODO: Implement service-specific config retrieval
    return {
        "service": service_name,
        "config": {
            "database_pool_size": 10,  # HARDCODED!
            "cache_ttl": 300,
            "log_level": "INFO"
        }
    }
```

**Problem:**
- Hardcoded response
- No database integration
- No real config storage

**Solution:**
- Implement database storage (see plan below)

### **2. No Database Schema**

**Missing:**
```sql
CREATE TABLE service_configs (
    service_name VARCHAR(100) PRIMARY KEY,
    config_json JSONB NOT NULL,
    version VARCHAR(20),
    updated_at TIMESTAMP,
    ...
);
```

**Solution:**
- Create migration script
- Integrate with existing `db_manager`

### **3. Contract Validation Overhead**

**Current:**
```python
# base/api/config.py:45-50
contract_result = await contract_processor.process_inbound_message(
    'configuration_request', request_data
)
```

**Concern:**
- Contract validation for EVERY config request
- Adds latency
- May not be necessary for internal config API

**Solution:**
- Make contract validation optional for config endpoints
- Use simplified validation for internal services

---

## 🎯 RECOMMENDED APPROACH

### **Phase 1: Database Storage (1-2 hours)**

**What to do:**
1. Create PostgreSQL migration for `service_configs` table
2. Implement storage in existing config API endpoints
3. Integrate with `db_manager` from `ConnectionManager`

**Changes:**
```python
# base/api/config.py:80-94 - Replace TODO

@config_router.get("/{service_name}")
async def get_service_config(service_name: str, request: Request):
    """Get configuration for specific service"""
    db_manager = request.app.state.central_hub_service.connection_manager.db_manager

    # Fetch from PostgreSQL
    async with db_manager.pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT config_json, version FROM service_configs WHERE service_name = $1",
            service_name
        )

    if not row:
        raise HTTPException(status_code=404, detail=f"Config not found for {service_name}")

    return {
        "service": service_name,
        "config": row['config_json'],
        "version": row['version']
    }
```

**Files to Create:**
- `base/migrations/001_create_service_configs.sql`
- Update `base/api/config.py` (implement TODOs)

**Risk Level:** ⚠️ LOW (only adds storage, no breaking changes)

---

### **Phase 2: Shared Config Client Library (1-2 hours)**

**What to do:**
1. Create `shared/components/config/client.py`
2. Extend existing `ConfigManager` to support remote source
3. Add caching and fallback logic

**Changes:**
```python
# shared/components/config/client.py (NEW)

class ConfigClient:
    """Centralized config client - fetches from Central Hub"""

    def __init__(self, service_name: str, central_hub_url: str):
        self.service_name = service_name
        self.hub_url = central_hub_url
        self._cache = None
        self._cache_timestamp = None

    async def get_config(self, force_refresh=False):
        """Fetch config from Central Hub with caching"""
        if not force_refresh and self._is_cache_valid():
            return self._cache['config']

        try:
            # Fetch from Hub
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.hub_url}/api/v1/config/{self.service_name}") as resp:
                    data = await resp.json()
                    self._update_cache(data)
                    return data['config']
        except Exception as e:
            # Fallback to cached or defaults
            if self._cache:
                return self._cache['config']
            return self._get_safe_defaults()
```

**OR Extend Existing ConfigManager:**
```python
# shared/components/utils/patterns/config.py:154-158

async def _load_from_remote(self, url: str) -> Optional[Dict[str, Any]]:
    """Load configuration from Central Hub API"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data.get('config', {})
    except Exception as e:
        self.logger.error(f"Failed to load remote config: {e}")
        return None
```

**Files to Create/Update:**
- `shared/components/config/client.py` (NEW)
- OR Update `shared/components/utils/patterns/config.py` (extend existing)

**Risk Level:** ⚠️ LOW (additive only, no breaking changes)

---

### **Phase 3: NATS Hot-Reload (Optional - 1 hour)**

**What to do:**
1. Publish config updates to NATS on POST /config/update
2. Services subscribe to `config.update.{service_name}`
3. Auto-reload config without restart

**Changes:**
```python
# base/api/config.py:96-153

@config_router.post("/update")
async def update_config(update: ConfigUpdate, request: Request):
    """Update config + broadcast via NATS"""

    # 1. Store in database
    db_manager = request.app.state.db_manager
    async with db_manager.pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO service_configs (service_name, config_json, version)
            VALUES ($1, $2, $3)
            ON CONFLICT (service_name) DO UPDATE SET
                config_json = EXCLUDED.config_json,
                version = EXCLUDED.version,
                updated_at = NOW()
            """,
            update.service, update.config, update.version
        )

    # 2. Broadcast via NATS
    nats_client = request.app.state.central_hub_service.connection_manager.nats_client
    await nats_client.publish(
        f"config.update.{update.service}",
        json.dumps(update.dict()).encode()
    )

    return {"status": "updated", "service": update.service}
```

**Files to Update:**
- `base/api/config.py` (implement broadcast)
- Services subscribe on startup (optional)

**Risk Level:** ⚠️ MEDIUM (new messaging pattern)

---

## 📋 MIGRATION PLAN (Recommended)

### **Step 1: Database Migration (30 min)**

```sql
-- base/migrations/001_create_service_configs.sql

CREATE TABLE IF NOT EXISTS service_configs (
    service_name VARCHAR(100) PRIMARY KEY,
    config_json JSONB NOT NULL,
    version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100) DEFAULT 'system',
    updated_by VARCHAR(100) DEFAULT 'system'
);

CREATE INDEX idx_service_configs_updated_at ON service_configs(updated_at DESC);

CREATE TABLE IF NOT EXISTS config_audit_log (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    config_json JSONB NOT NULL,
    version VARCHAR(20) NOT NULL,
    action VARCHAR(20) NOT NULL,
    changed_by VARCHAR(100) NOT NULL,
    changed_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_config_audit_service ON config_audit_log(service_name, changed_at DESC);
```

### **Step 2: Implement Config Storage API (30 min)**

Update `base/api/config.py`:
- Lines 80-94: Implement GET from database
- Lines 96-153: Implement POST to database + NATS broadcast
- Lines 156-171: Implement history from audit log

### **Step 3: Create Config Client Library (30 min)**

Create `shared/components/config/client.py`:
- Fetch from Central Hub API
- Local caching (5 min TTL)
- Fallback to safe defaults

### **Step 4: Migrate 1 Pilot Service (30 min)**

Migrate `polygon-historical-downloader`:
- Use `ConfigClient` for operational configs
- Keep ENV VARS for critical configs (DB, credentials)
- Test hot-reload

---

## 🎯 FINAL RECOMMENDATION

### **Hybrid Approach - Extend Existing Architecture**

**Use What Already Works:**
1. ✅ Keep existing `ConfigManager` for file + env config
2. ✅ Keep infrastructure.yaml for database/messaging configs
3. ✅ Use existing ConnectionManager for DB access
4. ✅ Use existing NATS client for broadcasts

**Add What's Missing:**
1. ➕ Create PostgreSQL tables for service configs
2. ➕ Implement storage in existing config API
3. ➕ Extend `ConfigManager` to support "remote" source
4. ➕ (Optional) Add NATS hot-reload

**Implementation Timeline:**
- **Phase 1:** Database storage (1-2 hours) - **DO THIS FIRST**
- **Phase 2:** Config client library (1-2 hours) - **THEN THIS**
- **Phase 3:** NATS hot-reload (1 hour) - **OPTIONAL**

**Total Time:** 2-5 hours (depending on optional features)

**Risk Assessment:**
- ✅ **LOW RISK** - Builds on existing architecture
- ✅ **NON-BREAKING** - Additive changes only
- ✅ **INCREMENTAL** - Can deploy phase by phase

---

## 🚨 CRITICAL RULES (FROM SKILL FILE)

**✅ DO:**
- Store operational configs in Central Hub (batch sizes, intervals, retries)
- Keep critical configs in ENV VARS (DB credentials, hostnames, ports)
- Always have safe defaults (service works even if Hub down)
- Cache configs locally (don't hammer Hub)
- Validate configs on startup (fail fast if critical missing)

**❌ DON'T:**
- Store secrets in Central Hub (use ENV VARS + secrets manager)
- Skip fallback logic (service must work if Hub unavailable)
- Make Hub a critical dependency for startup (only for operational configs)

---

## 📊 COMPARISON: Current vs Proposed

| Aspect | Current State | After Implementation |
|--------|---------------|---------------------|
| **Service Configs** | Hardcoded in code | Stored in PostgreSQL |
| **Config Updates** | Restart service | Hot-reload via NATS (optional) |
| **Consistency** | Each service different | Single source of truth |
| **Audit Trail** | None | Complete history in DB |
| **Client Library** | None | `ConfigClient` in shared/ |
| **Fallback** | N/A | Safe defaults + local cache |
| **Critical Configs** | Mixed | ENV VARS only |
| **Operational Configs** | Mixed | Central Hub only |

---

## ✅ CONCLUSION

**Best Approach:**
- ✅ **Extend existing Central Hub architecture** (don't rebuild)
- ✅ **Implement the TODOs** in `base/api/config.py`
- ✅ **Add PostgreSQL storage** (already have db_manager)
- ✅ **Create config client library** (or extend ConfigManager)
- ✅ **Keep it simple** - no over-engineering

**Next Steps:**
1. Review this document
2. Decide on phase implementation (all at once or incremental)
3. Start with Phase 1 (database storage) - lowest risk
4. Test with polygon-historical as pilot
5. Roll out to other services gradually

**Key Success Factors:**
- Build on what already works
- Don't break existing services
- Keep critical configs in ENV VARS
- Always have fallback defaults
- Test incrementally
