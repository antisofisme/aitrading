# [SERVICE NAME] Service Skill - TEMPLATE

**INSTRUCTIONS:** Copy this template to create new service skills.
Replace [SERVICE_NAME], [SERVICE_TYPE], [PORT], etc. with actual values.

---

**Service Name:** [service-name]
**Type:** [Data Ingestion | Data Processing | ML | Trading | Infrastructure]
**Port:** [8001-8018]
**Purpose:** [One-line description]

---

## 📋 QUICK REFERENCE

**When to use this skill:**
- Working on [service-name] service
- [Add specific use cases]
- Debugging [service-name] issues

**Key Responsibilities:**
- ✅ [Responsibility 1]
- ✅ [Responsibility 2]
- ✅ [Responsibility 3]

**Data Flow:**
```
Input: [Source] → [Format]
Processing: [What it does]
Output: [Destination] → [Format]
```

---

## ⭐ CENTRALIZED CONFIGURATION (MANDATORY)

### **Configuration Hierarchy**

```python
# CRITICAL CONFIGS → Environment Variables (.env)
# NEVER put these in Central Hub!
CLICKHOUSE_HOST=suho-clickhouse
CLICKHOUSE_PORT=9000
CLICKHOUSE_USER=suho_analytics
CLICKHOUSE_PASSWORD=clickhouse_secure_2024  # SECRET!
NATS_URL=nats://nats-1:4222,nats://nats-2:4222,nats://nats-3:4222
KAFKA_BROKERS=suho-kafka:9092
[API_KEY]=[your_api_key]  # SECRET!

# OPERATIONAL CONFIGS → Central Hub (via ConfigClient)
# Safe to change at runtime
{
  "operational": {
    "batch_size": 100,
    "max_retries": 3,
    "retry_delay_seconds": 10,
    "[service_specific_param]": value
  },
  "features": {
    "enable_[feature_x]": true,
    "enable_[feature_y]": false
  },
  "[business_logic]": {
    "threshold": 0.95,
    "interval_hours": 1
  }
}
```

### **Implementation Pattern (MANDATORY)**

```python
# [service-name]/config.py

import os
from shared.components.config.client import ConfigClient

class Config:
    def __init__(self):
        # ===== CRITICAL INFRASTRUCTURE (ENV VARS ONLY) =====
        # Database credentials
        self.clickhouse_host = os.getenv('CLICKHOUSE_HOST')
        self.clickhouse_port = int(os.getenv('CLICKHOUSE_PORT', '9000'))
        self.clickhouse_user = os.getenv('CLICKHOUSE_USER')
        self.clickhouse_password = os.getenv('CLICKHOUSE_PASSWORD')
        self.clickhouse_database = os.getenv('CLICKHOUSE_DATABASE')

        # Validate critical configs
        if not all([self.clickhouse_host, self.clickhouse_user,
                    self.clickhouse_password, self.clickhouse_database]):
            raise ValueError("Missing required ClickHouse environment variables")

        # Messaging
        self.nats_url = os.getenv('NATS_URL')
        self.kafka_brokers = os.getenv('KAFKA_BROKERS')

        # [Add other critical configs from ENV VARS]

        # ===== OPERATIONAL CONFIGS (CENTRALIZED) =====
        self.config_client = ConfigClient(
            service_name='[service-name]',
            central_hub_url=os.getenv('CENTRAL_HUB_URL', 'http://suho-central-hub:7000'),
            cache_ttl_seconds=300,  # 5 minutes
            enable_nats_updates=True
        )

        self._operational_config = None

    async def init_async(self):
        """
        Async initialization - MUST call this after creating Config

        Fetches operational configs from Central Hub
        Falls back to safe defaults if Hub unavailable
        """
        try:
            self._operational_config = await self.config_client.get_config()
            await self.config_client.subscribe_to_updates()
            logger.info("✅ Operational config loaded from Central Hub")
        except Exception as e:
            logger.warning(f"Central Hub unavailable, using safe defaults: {e}")
            self._operational_config = self._get_safe_defaults()

    def _get_safe_defaults(self) -> dict:
        """
        Safe fallback configuration

        CRITICAL: Service MUST work with these defaults even if Hub is down
        """
        return {
            "operational": {
                "batch_size": 100,
                "max_retries": 3,
                "retry_delay_seconds": 10
            },
            "features": {
                "enable_[feature_x]": True  # Safe default
            }
        }

    # ===== CONFIG PROPERTIES =====
    # Expose config values via properties for clean access

    @property
    def batch_size(self) -> int:
        """Get batch size from centralized config"""
        return self._operational_config.get('operational', {}).get('batch_size', 100)

    @property
    def max_retries(self) -> int:
        """Get max retries from centralized config"""
        return self._operational_config.get('operational', {}).get('max_retries', 3)

    @property
    def enable_feature_x(self) -> bool:
        """Check if feature X is enabled"""
        return self._operational_config.get('features', {}).get('enable_feature_x', True)

    # [Add more properties as needed]
```

### **Service Main - Async Init Pattern**

```python
# [service-name]/main.py

import asyncio
from config import Config

async def main():
    # 1. Create config (loads ENV VARS)
    config = Config()

    # 2. Async init (fetch from Central Hub)
    await config.init_async()

    # 3. Start service with centralized config
    service = [ServiceName](config)
    await service.start()

if __name__ == '__main__':
    asyncio.run(main())
```

---

## 🔧 CRITICAL RULES

### **Rule 1: Config Hierarchy (ALWAYS FOLLOW)**

```
❌ NEVER IN CENTRAL HUB:
- Database credentials (passwords, users)
- API keys and secrets
- Infrastructure hostnames/ports
→ Use ENV VARS

✅ ALWAYS IN CENTRAL HUB:
- Operational settings (batch_size, intervals, retries)
- Feature flags (enable/disable features)
- Business logic (thresholds, ranges)
- Tuning parameters
→ Use ConfigClient
```

### **Rule 2: Graceful Degradation (MANDATORY)**

```python
# Service MUST work even if Central Hub is down
try:
    config = await config_client.get_config()
except Exception:
    logger.warning("Using safe defaults")
    config = self._get_safe_defaults()  # MUST HAVE DEFAULTS!
```

### **Rule 3: Hot-Reload (OPTIONAL)**

```python
# Subscribe to config updates for zero-downtime changes
await config_client.subscribe_to_updates()

# When update received via NATS:
# 1. Fetch new config
# 2. Validate
# 3. Apply without restart
# 4. Log change
```

### **Rule 4: [Add Service-Specific Critical Rules]**

---

## 🏗️ ARCHITECTURE

### **Data Flow**

```
[Describe data flow with centralized config]

Startup:
1. Load critical configs from ENV VARS
2. Fetch operational configs from Central Hub
3. Merge with defaults
4. Subscribe to NATS updates
5. Start processing

Runtime:
1. Use cached operational configs
2. Auto-refresh every 5 minutes
3. React to NATS config.update notifications
4. Log config changes
```

### **Dependencies**

```
Upstream (depends on):
- Central Hub (for operational configs)
- [List other dependencies]

Downstream (provides data to):
- [List consumers]

Infrastructure:
- PostgreSQL/TimescaleDB/ClickHouse
- NATS cluster
- Kafka (optional)
```

---

## ✅ VALIDATION CHECKLIST

### **After Config Changes**

- [ ] Config follows hierarchy (critical in ENV, operational in Hub)
- [ ] Safe defaults provided in `_get_safe_defaults()`
- [ ] Service starts successfully with defaults (Hub down scenario)
- [ ] Service fetches config from Hub (Hub up scenario)
- [ ] Config hot-reload works (if enabled)
- [ ] Logs show config source (ENV/Hub/Defaults)

### **After Code Changes**

- [ ] Critical configs from ENV VARS (never hardcoded)
- [ ] Operational configs from ConfigClient
- [ ] ConfigClient initialization in `init_async()`
- [ ] Safe defaults comprehensive
- [ ] Properties expose config values cleanly
- [ ] Error handling for Hub unavailability

---

## 🚨 COMMON ISSUES

### **Issue 1: Config Not Loading from Central Hub**

**Symptoms:**
- Service uses defaults even when Hub is up
- Logs show "Using safe defaults"

**Debug:**
```bash
# Test Central Hub API directly
curl http://suho-central-hub:7000/api/v1/config/[service-name]

# Check service logs
docker logs suho-[service-name] | grep "config\|Central Hub"
```

**Common Causes:**
- Central Hub not running
- Service name mismatch
- Network connectivity issue
- Auth middleware blocking request

### **Issue 2: Service Crashes on Startup (Missing ENV VAR)**

**Symptoms:**
- Service exits immediately
- Error: "Missing required ... environment variables"

**Fix:**
```bash
# Check .env file has all critical configs
grep -E "CLICKHOUSE_|NATS_|KAFKA_" .env

# Add missing vars to .env
echo "CLICKHOUSE_PASSWORD=..." >> .env
```

### **Issue 3: Config Changes Not Applied**

**Symptoms:**
- Updated config in Central Hub
- Service still using old values

**Debug:**
```bash
# Check if NATS broadcast sent
docker logs suho-central-hub | grep "Config updated and broadcasted"

# Check if service received NATS message
docker logs suho-[service-name] | grep "config.update"

# Manually refresh (restart service)
docker restart suho-[service-name]
```

---

## [Add Service-Specific Sections]

### **Processing Logic**

[Describe what this service does]

### **Message Patterns**

[NATS subjects, Kafka topics]

### **Database Schema**

[Tables used/created]

### **Performance Tuning**

[Optimization tips]

---

## 📖 SUMMARY

**[Service Name] = [One-line purpose]**

**Configuration Pattern:**
- ✅ Critical configs from ENV VARS
- ✅ Operational configs from Central Hub
- ✅ Safe defaults for graceful degradation
- ✅ Hot-reload support (optional)

**Key Success Factors:**
1. Follow config hierarchy strictly
2. Test with Hub down (ensure defaults work)
3. Monitor config fetch metrics
4. Document config changes in audit trail

**Use this skill when:**
- Implementing [service-name]
- Debugging [service-name] issues
- Updating [service-name] configuration
- Migrating to centralized config
