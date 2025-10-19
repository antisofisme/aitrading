# Centralized Config Management - System Skill

**Purpose:** Single source of truth for operational configurations across all microservices via Central Hub API

**Pattern:** Hybrid approach - Critical infrastructure configs from environment variables, operational configs from Central Hub

**Version:** 1.0.0 (Initial Implementation)

---

## 📋 QUICK REFERENCE

**When to use this pattern:**
- ✅ Operational settings that change frequently (batch sizes, intervals, retries)
- ✅ Feature flags and toggles
- ✅ Service-specific configurations
- ✅ Cross-service consistency required

**When NOT to use:**
- ❌ Critical infrastructure configs (DB credentials, hostnames, ports) → Use ENV VARS
- ❌ Secrets and passwords → Use ENV VARS + secrets management
- ❌ Bootstrap configs needed before Central Hub available → Use ENV VARS

---

## 🏗️ ARCHITECTURE

### **System Overview**

```
┌─────────────────────────────────────────────────────┐
│           Central Hub (Config Provider)             │
│                                                     │
│  ┌───────────────────────────────────────────────┐ │
│  │  PostgreSQL: service_configs table            │ │
│  │  - service_name (PK)                          │ │
│  │  - config_json (JSONB)                        │ │
│  │  - version                                    │ │
│  │  - updated_at                                 │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
│  API Endpoints:                                     │
│  GET  /api/v1/config/:service_name                 │
│  POST /api/v1/config/:service_name (admin only)    │
│                                                     │
└──────────────┬──────────────────────────────────────┘
               │ HTTP/JSON + NATS (for updates)
               │
    ┌──────────┼──────────┬──────────────┐
    ↓          ↓          ↓              ↓
┌─────────┐ ┌─────────┐ ┌─────────┐  ┌─────────┐
│Service A│ │Service B│ │Service C│  │Service N│
│         │ │         │ │         │  │         │
│ 1. Env  │ │ 1. Env  │ │ 1. Env  │  │ 1. Env  │
│ 2. Hub  │ │ 2. Hub  │ │ 2. Hub  │  │ 2. Hub  │
│ 3. Cache│ │ 3. Cache│ │ 3. Cache│  │ 3. Cache│
└─────────┘ └─────────┘ └─────────┘  └─────────┘
```

### **Data Flow**

```
Service Startup:
1. Load CRITICAL configs from ENV VARS (DB, NATS, etc.)
   └─ MUST succeed or service fails

2. Fetch OPERATIONAL configs from Central Hub
   └─ Fallback to safe defaults if Hub unavailable

3. Cache configs locally (in-memory + optional disk)
   └─ For faster access and Hub downtime resilience

4. Subscribe to NATS config updates (optional)
   └─ Real-time updates without restart

Runtime:
1. Use cached config for operations
2. Refresh periodically (default: 5 minutes)
3. React to NATS update notifications
```

---

## 📦 CONFIG STRUCTURE

### **Config Hierarchy**

```
Environment Variables (.env)
  └─ Critical Infrastructure Only
     ├─ CLICKHOUSE_HOST, CLICKHOUSE_PORT, CLICKHOUSE_USER, CLICKHOUSE_PASSWORD
     ├─ POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD
     ├─ NATS_URL, KAFKA_BROKERS
     └─ SERVICE_NAME, INSTANCE_ID, LOG_LEVEL

Central Hub (API)
  └─ Operational Configurations
     ├─ Service-specific settings
     ├─ Feature flags
     ├─ Runtime parameters
     └─ Cross-service consistency configs

Local Defaults (code)
  └─ Safe fallback values
     └─ Used ONLY when Central Hub unavailable
```

### **Example Config Structure**

```json
{
  "service_name": "polygon-historical-downloader",
  "version": "1.2.0",
  "updated_at": "2025-10-19T07:30:00Z",
  "config": {
    "operational": {
      "gap_check_interval_hours": 1,
      "batch_size": 100,
      "max_retries": 3,
      "retry_delay_seconds": 10,
      "verification_enabled": true
    },
    "download": {
      "start_date": "today-7days",
      "end_date": "today",
      "granularity": {
        "trading_pairs": {"timeframe": "minute", "multiplier": 5},
        "analysis_pairs": {"timeframe": "minute", "multiplier": 5}
      }
    },
    "features": {
      "enable_gap_verification": true,
      "enable_period_tracker": true,
      "enable_auto_backfill": true
    }
  }
}
```

---

## 🔧 IMPLEMENTATION GUIDE

### **Step 1: Central Hub - Config API (FastAPI)**

```python
# central-hub/src/api/config.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import asyncpg

router = APIRouter(prefix="/api/v1/config", tags=["config"])

class ServiceConfig(BaseModel):
    service_name: str
    config: Dict[str, Any]
    version: str = "1.0.0"

@router.get("/{service_name}")
async def get_service_config(service_name: str):
    """
    Get configuration for a service

    Returns:
        - 200: Config found
        - 404: Service not found
        - 500: Database error
    """
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT config_json, version, updated_at
            FROM service_configs
            WHERE service_name = $1
            """,
            service_name
        )

        if not row:
            raise HTTPException(status_code=404, detail=f"Config not found for {service_name}")

        return {
            "service_name": service_name,
            "config": row['config_json'],
            "version": row['version'],
            "updated_at": row['updated_at'].isoformat()
        }

@router.post("/{service_name}")
async def update_service_config(service_name: str, config: ServiceConfig):
    """
    Update service configuration (admin only)

    Also publishes update notification to NATS
    """
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO service_configs (service_name, config_json, version, updated_at)
            VALUES ($1, $2, $3, NOW())
            ON CONFLICT (service_name)
            DO UPDATE SET
                config_json = EXCLUDED.config_json,
                version = EXCLUDED.version,
                updated_at = NOW()
            """,
            service_name,
            config.config,
            config.version
        )

    # Publish update notification to NATS
    await nats_client.publish(
        f"config.update.{service_name}",
        json.dumps(config.dict()).encode()
    )

    return {"status": "updated", "service_name": service_name}
```

### **Step 2: Database Schema**

```sql
-- central-hub/migrations/001_create_service_configs.sql

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

-- Audit trail
CREATE TABLE IF NOT EXISTS config_audit_log (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    config_json JSONB NOT NULL,
    version VARCHAR(20) NOT NULL,
    action VARCHAR(20) NOT NULL, -- 'created', 'updated', 'deleted'
    changed_by VARCHAR(100) NOT NULL,
    changed_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_config_audit_service ON config_audit_log(service_name, changed_at DESC);
```

### **Step 3: Shared Config Client Library**

```python
# shared/components/config/client.py

import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import aiohttp
from nats.aio.client import Client as NATS

logger = logging.getLogger(__name__)

class ConfigClient:
    """
    Centralized configuration client for microservices

    Features:
    - Fetch configs from Central Hub
    - Local caching (in-memory + optional disk)
    - Auto-refresh
    - NATS-based real-time updates
    - Fallback to safe defaults
    """

    def __init__(
        self,
        service_name: str,
        central_hub_url: str = None,
        nats_url: str = None,
        cache_ttl_seconds: int = 300,  # 5 minutes
        enable_nats_updates: bool = True
    ):
        self.service_name = service_name
        self.central_hub_url = central_hub_url or os.getenv('CENTRAL_HUB_URL', 'http://suho-central-hub:7000')
        self.nats_url = nats_url or os.getenv('NATS_URL')
        self.cache_ttl = timedelta(seconds=cache_ttl_seconds)
        self.enable_nats_updates = enable_nats_updates

        # Cache
        self._config_cache: Optional[Dict[str, Any]] = None
        self._cache_timestamp: Optional[datetime] = None
        self._nats_client: Optional[NATS] = None

        logger.info(f"ConfigClient initialized for {service_name}")
        logger.info(f"Central Hub URL: {self.central_hub_url}")

    async def get_config(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get configuration from cache or Central Hub

        Args:
            force_refresh: Force fetch from Hub even if cache valid

        Returns:
            Configuration dictionary
        """
        # Check cache validity
        if not force_refresh and self._is_cache_valid():
            logger.debug(f"Using cached config for {self.service_name}")
            return self._config_cache['config']

        # Fetch from Central Hub
        try:
            config = await self._fetch_from_hub()
            self._update_cache(config)
            return config['config']

        except Exception as e:
            logger.error(f"Failed to fetch config from Central Hub: {e}")

            # Fallback to cached config if available
            if self._config_cache:
                logger.warning("Using stale cached config as fallback")
                return self._config_cache['config']

            # No cache available - use safe defaults
            logger.warning("No cache available, using safe defaults")
            return self._get_safe_defaults()

    async def _fetch_from_hub(self) -> Dict[str, Any]:
        """Fetch config from Central Hub API"""
        url = f"{self.central_hub_url}/api/v1/config/{self.service_name}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 404:
                    logger.warning(f"Config not found for {self.service_name}, using defaults")
                    return {'config': self._get_safe_defaults()}

                resp.raise_for_status()
                data = await resp.json()

                logger.info(f"Fetched config for {self.service_name} (version: {data.get('version', 'unknown')})")
                return data

    def _update_cache(self, config: Dict[str, Any]):
        """Update in-memory cache"""
        self._config_cache = config
        self._cache_timestamp = datetime.now()
        logger.debug(f"Config cache updated for {self.service_name}")

    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        if not self._config_cache or not self._cache_timestamp:
            return False

        age = datetime.now() - self._cache_timestamp
        return age < self.cache_ttl

    def _get_safe_defaults(self) -> Dict[str, Any]:
        """
        Safe default configuration

        Override this method in service-specific implementations
        """
        return {
            "operational": {
                "batch_size": 100,
                "max_retries": 3,
                "retry_delay_seconds": 10
            }
        }

    async def subscribe_to_updates(self):
        """
        Subscribe to NATS config update notifications

        Call this after service startup to receive real-time updates
        """
        if not self.enable_nats_updates or not self.nats_url:
            logger.info("NATS config updates disabled")
            return

        try:
            self._nats_client = NATS()
            await self._nats_client.connect(self.nats_url)

            subject = f"config.update.{self.service_name}"
            await self._nats_client.subscribe(subject, cb=self._handle_config_update)

            logger.info(f"Subscribed to config updates: {subject}")

        except Exception as e:
            logger.error(f"Failed to subscribe to NATS updates: {e}")

    async def _handle_config_update(self, msg):
        """Handle NATS config update notification"""
        try:
            data = json.loads(msg.data.decode())
            logger.info(f"Received config update notification (version: {data.get('version', 'unknown')})")

            # Force refresh from Hub
            await self.get_config(force_refresh=True)

        except Exception as e:
            logger.error(f"Failed to process config update: {e}")

    async def close(self):
        """Close NATS connection"""
        if self._nats_client:
            await self._nats_client.close()
            logger.info("ConfigClient closed")


# Service-specific implementations

class PolygonHistoricalConfigClient(ConfigClient):
    """Config client for Polygon Historical Downloader"""

    def _get_safe_defaults(self) -> Dict[str, Any]:
        """Safe defaults for Polygon Historical service"""
        return {
            "operational": {
                "gap_check_interval_hours": 1,
                "batch_size": 100,
                "max_retries": 3,
                "retry_delay_seconds": 10,
                "verification_enabled": True
            },
            "download": {
                "start_date": "today-7days",
                "end_date": "today"
            },
            "features": {
                "enable_gap_verification": True,
                "enable_period_tracker": True
            }
        }
```

### **Step 4: Service Integration Pattern**

```python
# polygon-historical-downloader/src/config.py

import os
from shared.components.config.client import PolygonHistoricalConfigClient

class Config:
    def __init__(self):
        # ===== CRITICAL INFRASTRUCTURE CONFIGS (ENV VARS ONLY) =====
        # These MUST exist or service fails
        self.polygon_api_key = os.getenv("POLYGON_API_KEY")
        if not self.polygon_api_key:
            raise ValueError("POLYGON_API_KEY environment variable not set")

        # Database credentials
        self._clickhouse_host = os.getenv('CLICKHOUSE_HOST')
        self._clickhouse_port = int(os.getenv('CLICKHOUSE_PORT', '9000'))
        self._clickhouse_user = os.getenv('CLICKHOUSE_USER')
        self._clickhouse_password = os.getenv('CLICKHOUSE_PASSWORD')
        self._clickhouse_database = os.getenv('CLICKHOUSE_DATABASE')

        if not all([self._clickhouse_host, self._clickhouse_user,
                    self._clickhouse_password, self._clickhouse_database]):
            raise ValueError("Missing required ClickHouse environment variables")

        # Messaging
        self.nats_url = os.getenv('NATS_URL')
        self.kafka_brokers = os.getenv('KAFKA_BROKERS', 'suho-kafka:9092')

        # Service identity
        self.instance_id = os.getenv("INSTANCE_ID", "polygon-historical-downloader-1")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

        # ===== OPERATIONAL CONFIGS (CENTRALIZED) =====
        # Fetch from Central Hub
        self._config_client = PolygonHistoricalConfigClient(
            service_name="polygon-historical-downloader",
            central_hub_url=os.getenv('CENTRAL_HUB_URL', 'http://suho-central-hub:7000'),
            nats_url=self.nats_url
        )

        # Will be populated after async init
        self._operational_config = None

    async def init_async(self):
        """
        Async initialization - call this after creating Config

        Fetches operational configs from Central Hub
        """
        self._operational_config = await self._config_client.get_config()
        await self._config_client.subscribe_to_updates()

        logger.info("✅ Operational config loaded from Central Hub")

    @property
    def gap_check_interval_hours(self) -> int:
        """Get gap check interval from centralized config"""
        return self._operational_config.get('operational', {}).get('gap_check_interval_hours', 1)

    @property
    def download_config(self) -> dict:
        """Get download configuration from centralized config"""
        return self._operational_config.get('download', {
            'start_date': 'today-7days',
            'end_date': 'today'
        })

    # ... other properties ...
```

### **Step 5: Service Main - Async Init Pattern**

```python
# polygon-historical-downloader/src/main.py

async def main():
    # 1. Create config (loads ENV VARS)
    config = Config()

    # 2. Async init (fetch from Central Hub)
    await config.init_async()

    # 3. Start service with centralized config
    service = PolygonHistoricalService(config)
    await service.start()

if __name__ == '__main__':
    asyncio.run(main())
```

---

## ⚠️ CRITICAL RULES

### **Rule 1: Never Put Secrets in Centralized Config**
```
❌ WRONG: Store passwords in Central Hub
✅ RIGHT: Store passwords in ENV VARS only
```

### **Rule 2: Always Have Safe Defaults**
```python
# Service MUST work even if Central Hub is down
def _get_safe_defaults(self):
    return {
        "batch_size": 100,  # Conservative default
        "max_retries": 3
    }
```

### **Rule 3: Critical Configs from ENV VARS Only**
```python
# Database, messaging, credentials → ENV VARS
# Operational settings → Central Hub
# Secrets → ENV VARS + secrets manager

✅ ENV VAR: CLICKHOUSE_HOST, CLICKHOUSE_PASSWORD
✅ Hub: batch_size, retry_delay
❌ Hub: database_password
```

### **Rule 4: Validate Configs on Startup**
```python
# Fail fast if critical configs missing
if not os.getenv('CLICKHOUSE_HOST'):
    raise ValueError("CLICKHOUSE_HOST required")

# Warn if operational configs unavailable
if not operational_config:
    logger.warning("Using safe defaults")
```

### **Rule 5: Cache Configs Locally**
```python
# Don't hammer Central Hub on every request
# Cache for 5 minutes (configurable)
# Refresh on NATS notification
```

---

## ✅ VALIDATION CHECKLIST

After implementing centralized config:

### **Infrastructure Level**
- [ ] Central Hub has `/api/v1/config/:service_name` endpoint
- [ ] PostgreSQL `service_configs` table exists
- [ ] NATS cluster available for update notifications
- [ ] All services can reach Central Hub URL

### **Service Level**
- [ ] Service loads critical configs from ENV VARS (DB, NATS, etc.)
- [ ] Service fetches operational configs from Central Hub
- [ ] Service has safe fallback defaults
- [ ] Service caches configs locally
- [ ] Service subscribes to NATS config updates (optional)

### **Functionality**
- [ ] Service starts successfully when Hub available
- [ ] Service starts successfully when Hub DOWN (uses defaults)
- [ ] Config updates via Central Hub API work
- [ ] NATS notifications trigger config refresh
- [ ] Cache TTL works correctly
- [ ] Logs show config source (ENV/Hub/Defaults)

### **Testing Scenarios**
- [ ] **Happy path:** Hub available → configs loaded
- [ ] **Hub down:** Service uses safe defaults
- [ ] **Hub returns 404:** Service uses safe defaults
- [ ] **Hub timeout:** Service falls back to cache or defaults
- [ ] **Config update:** NATS notification triggers refresh
- [ ] **Cache expiry:** Auto-refresh from Hub

---

## 📊 MONITORING

### **Metrics to Track**

```python
# Config fetch metrics
config_fetch_total{service, status}  # success/failure
config_fetch_duration_seconds{service}
config_cache_hit_total{service}
config_cache_miss_total{service}
config_fallback_to_defaults_total{service}

# Update metrics
config_update_received_total{service}
config_version{service, version}
```

### **Alerts**

```yaml
# Alert if service using stale config for > 1 hour
- alert: StaleConfigCache
  expr: time() - config_last_updated_timestamp > 3600

# Alert if many services falling back to defaults
- alert: CentralHubConfigDown
  expr: sum(rate(config_fallback_to_defaults_total[5m])) > 5
```

---

## 🔄 MIGRATION STRATEGY

### **Phase 1: Shared Defaults (No Breaking Change)**
1. Create `shared/config/defaults.py`
2. All services import from shared
3. Keep ENV VARS as primary source
4. **Benefit:** Consistency without architecture change

### **Phase 2: Central Hub API (Gradual Rollout)**
1. Implement Central Hub config API
2. Migrate 1-2 pilot services first
3. Monitor for 1 week
4. Migrate remaining services
5. **Benefit:** Gradual, low-risk

### **Phase 3: Real-time Updates (Optional)**
1. Add NATS subscription to services
2. Enable hot-reload of configs
3. **Benefit:** Zero-downtime config updates

---

## 📚 EXAMPLES

### **Example 1: Update Gap Check Interval**

```bash
# Before: Edit .env + restart all services
# After: One API call, no restart

curl -X POST http://suho-central-hub:7000/api/v1/config/polygon-historical-downloader \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "polygon-historical-downloader",
    "version": "1.1.0",
    "config": {
      "operational": {
        "gap_check_interval_hours": 2  # Changed from 1 to 2
      }
    }
  }'

# All instances receive NATS notification → auto-update
```

### **Example 2: Enable Feature Flag**

```bash
# Enable verification feature across all services
curl -X POST http://suho-central-hub:7000/api/v1/config/polygon-historical-downloader \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "features": {
        "enable_gap_verification": true  # Feature flag
      }
    }
  }'
```

---

## 🎯 SUMMARY

**Centralized Config Management provides:**
- ✅ Single source of truth for operational configs
- ✅ Consistency across all services
- ✅ Zero-downtime config updates
- ✅ Fallback resilience (service works even if Hub down)
- ✅ Audit trail (who changed what when)
- ✅ Easy monitoring and debugging

**Critical Success Factors:**
1. Keep secrets in ENV VARS, not Central Hub
2. Always have safe fallback defaults
3. Cache configs locally for resilience
4. Validate on startup, fail fast if critical configs missing
5. Use NATS for real-time updates (optional but recommended)

**Use this skill when:**
- Setting up new microservices
- Migrating existing services to centralized config
- Implementing config API in Central Hub
- Debugging config-related issues
- Ensuring cross-service consistency
