# Polygon Historical Downloader Service Skill

**Service Name:** polygon-historical-downloader
**Type:** Data Ingestion
**Port:** 8002
**Purpose:** Download historical forex/gold data from Polygon.io and fill data gaps in ClickHouse

---

## 📋 QUICK REFERENCE

**When to use this skill:**
- Working on polygon-historical-downloader service
- Fixing gap filling logic
- Updating download configurations
- Debugging ClickHouse data issues
- Optimizing download performance

**Key Responsibilities:**
- ✅ Download historical OHLCV data from Polygon.io (5min timeframe)
- ✅ Detect and fill gaps in ClickHouse live_aggregates table
- ✅ Publish downloaded data to NATS/Kafka
- ✅ Track downloaded periods to avoid duplicates
- ✅ Verify data propagation through pipeline

**Data Flow:**
```
Polygon.io API (5min OHLCV)
    ↓ Download in batches
Gap Detector (ClickHouse query)
    ↓ Identify missing dates
Downloader (fetch missing ranges)
    ↓ Batch download
NATS Publisher (market.{symbol}.5m)
    ↓ Real-time streaming
Kafka Archive (aggregate_archive)
    ↓ Long-term storage
ClickHouse Verification
    ✓ Confirm data exists
```

---

## ⭐ CENTRALIZED CONFIGURATION (MANDATORY)

### **Configuration Hierarchy**

```python
# ===== CRITICAL CONFIGS → Environment Variables (.env) =====
# NEVER put these in Central Hub!

POLYGON_API_KEY=vSEvGAQ9YV0JVyue9ldon7rVqBPsfGnZ  # SECRET!
CLICKHOUSE_HOST=suho-clickhouse
CLICKHOUSE_PORT=9000
CLICKHOUSE_USER=suho_analytics
CLICKHOUSE_PASSWORD=clickhouse_secure_2024  # SECRET!
CLICKHOUSE_DATABASE=suho_analytics
NATS_URL=nats://nats-1:4222,nats://nats-2:4222,nats://nats-3:4222
KAFKA_BROKERS=suho-kafka:9092

# ===== OPERATIONAL CONFIGS → Central Hub =====
# Safe to change at runtime via ConfigClient

{
  "operational": {
    "gap_check_interval_hours": 1,
    "batch_size": 100,
    "max_retries": 3,
    "retry_delay_seconds": 10,
    "verification_enabled": true
  },
  "download": {
    "start_date": "today-7days",  # Gap filling range
    "end_date": "today",
    "granularity": {
      "trading_pairs": {"timeframe": "minute", "multiplier": 5},
      "analysis_pairs": {"timeframe": "minute", "multiplier": 5},
      "confirmation_pairs": {"timeframe": "minute", "multiplier": 5}
    }
  },
  "features": {
    "enable_gap_verification": true,
    "enable_period_tracker": true,
    "enable_auto_backfill": true
  }
}
```

### **Implementation Pattern**

```python
# polygon-historical-downloader/src/config.py

import os
from shared.components.config.client import ConfigClient

class Config:
    def __init__(self):
        # ===== CRITICAL INFRASTRUCTURE (ENV VARS ONLY) =====
        self.polygon_api_key = os.getenv("POLYGON_API_KEY")
        if not self.polygon_api_key:
            raise ValueError("POLYGON_API_KEY environment variable not set")

        # ClickHouse credentials
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
        self._config_client = ConfigClient(
            service_name="polygon-historical-downloader",
            central_hub_url=os.getenv('CENTRAL_HUB_URL', 'http://suho-central-hub:7000'),
            cache_ttl_seconds=300,
            enable_nats_updates=True
        )

        self._operational_config = None

    async def init_async(self):
        """
        Async initialization - call this after creating Config
        Fetches operational configs from Central Hub
        """
        try:
            self._operational_config = await self._config_client.get_config()
            await self._config_client.subscribe_to_updates()
            logger.info("✅ Operational config loaded from Central Hub")
        except Exception as e:
            logger.warning(f"Central Hub unavailable, using safe defaults: {e}")
            self._operational_config = self._get_safe_defaults()

    def _get_safe_defaults(self) -> dict:
        """Safe fallback configuration if Central Hub unavailable"""
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
                "enable_period_tracker": True,
                "enable_auto_backfill": True
            }
        }

    # ===== CONFIG PROPERTIES =====

    @property
    def gap_check_interval_hours(self) -> int:
        return self._operational_config.get('operational', {}).get('gap_check_interval_hours', 1)

    @property
    def batch_size(self) -> int:
        return self._operational_config.get('operational', {}).get('batch_size', 100)

    @property
    def max_retries(self) -> int:
        return self._operational_config.get('operational', {}).get('max_retries', 3)

    @property
    def download_range(self) -> dict:
        return self._operational_config.get('download', {
            'start_date': 'today-7days',
            'end_date': 'today'
        })

    @property
    def enable_gap_verification(self) -> bool:
        return self._operational_config.get('features', {}).get('enable_gap_verification', True)
```

### **Main Service - Async Init**

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

## 🔧 CRITICAL RULES

### **Rule 1: Gap Filling Range = 7 Days ONLY**

```python
# ❌ WRONG - Don't download 10 years of historical data
HISTORICAL_START_DATE=2015-01-01  # This is for Dukascopy initial download!

# ✅ CORRECT - Only fill gaps in last 7 days
POLYGON_GAP_START_DATE=today-7days
POLYGON_GAP_END_DATE=today
```

**Why?**
- Polygon-historical is for **GAP FILLING**, not initial historical download
- Dukascopy handles full 10-year historical data
- live_aggregates retention is 7 days
- Filling gaps beyond 7 days is wasteful (data already in historical_aggregates)

### **Rule 2: ALWAYS Verify Data Propagation**

```python
# Download → Publish → Verify pipeline
download_bars = await downloader.download(symbol, start, end)
await publisher.publish(download_bars)
await asyncio.sleep(30)  # Wait for pipeline propagation

# CRITICAL: Verify data actually reached ClickHouse
verified = await gap_verifier.verify(symbol, start, end)
if not verified:
    logger.error(f"Verification failed: {symbol} {start} {end}")
```

**Why?**
- NATS → Aggregator → Data-Bridge → ClickHouse takes ~30 seconds
- Download success ≠ data in ClickHouse
- Verification prevents false "gap filled" status

### **Rule 3: Use ClickHouse for Gap Detection (NOT historical_aggregates)**

```python
# ✅ CORRECT - Query live_aggregates
SELECT DISTINCT DATE(FROM_UNIXTIME(time/1000)) as date
FROM live_aggregates
WHERE symbol = 'XAU/USD'
  AND timeframe = '5m'
  AND time >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 7 DAY)) * 1000

# ❌ WRONG - Query historical_aggregates (for 10-year data)
```

**Why?**
- live_aggregates = last 7 days (gap filling target)
- historical_aggregates = 10+ years (read-only, already complete)
- Gap detector must check live_aggregates table only

### **Rule 4: Config Hierarchy (ALWAYS FOLLOW)**

```
❌ NEVER IN CENTRAL HUB:
- POLYGON_API_KEY (secret!)
- ClickHouse credentials
- NATS/Kafka URLs

✅ ALWAYS IN CENTRAL HUB:
- gap_check_interval_hours
- batch_size
- download range (start_date, end_date)
- Feature flags
```

---

## 🏗️ ARCHITECTURE

### **Startup Flow with Centralized Config**

```
Service Startup
    ↓
1. Load critical configs from ENV VARS
   (POLYGON_API_KEY, CLICKHOUSE_*, NATS_URL)
    ↓
2. Fetch operational configs from Central Hub
   GET /api/v1/config/polygon-historical-downloader
    ↓
3. Merge with safe defaults
   (gap_check_interval, batch_size, download_range)
    ↓
4. Subscribe to NATS config.update.polygon-historical-downloader
   (For hot-reload)
    ↓
5. Initialize components:
   - GapDetector (ClickHouse client)
   - Downloader (Polygon.io client)
   - Publisher (NATS/Kafka)
   - GapVerifier
    ↓
6. Start gap check loop:
   - Check for gaps (every gap_check_interval_hours)
   - Download missing data
   - Publish to NATS/Kafka
   - Verify in ClickHouse
```

### **Dependencies**

**Upstream (depends on):**
- Central Hub (for operational configs)
- Polygon.io API (data source)
- ClickHouse (gap detection)

**Downstream (provides data to):**
- NATS cluster (real-time streaming)
- Kafka (archival)
- ClickHouse (via Data-Bridge)

**Infrastructure:**
- PostgreSQL/TimescaleDB (period tracker)
- ClickHouse (gap detection + storage)
- NATS cluster (messaging)
- Kafka (archival)

---

## 📊 MESSAGE PATTERNS

### **NATS Publishing**

```python
# Subject pattern: market.{symbol}.{timeframe}
# Symbol normalized: XAU/USD → XAUUSD, GBP/JPY → GBPJPY

await nats_client.publish(
    subject="market.XAUUSD.5m",
    data={
        "symbol": "XAU/USD",
        "timeframe": "5m",
        "time": 1729327200000,  # Unix timestamp (ms)
        "open": 2650.25,
        "high": 2652.00,
        "low": 2649.50,
        "close": 2651.75,
        "volume": 12500,
        "source": "polygon-historical"
    }
)
```

### **Kafka Archiving**

```python
# Topic: aggregate_archive
# Key: {symbol}:{timeframe}

kafka_producer.produce(
    topic="aggregate_archive",
    key="XAU/USD:5m",
    value={...}  # Same as NATS message
)
```

---

## ✅ VALIDATION CHECKLIST

### **After Config Changes**

- [ ] Config follows hierarchy (critical in ENV, operational in Hub)
- [ ] Safe defaults in `_get_safe_defaults()` match production values
- [ ] Service starts with defaults (Hub down scenario tested)
- [ ] Service fetches config from Hub (Hub up scenario tested)
- [ ] Download range = 7 days (not 10 years!)
- [ ] Gap check interval reasonable (1-24 hours)

### **After Code Changes**

- [ ] POLYGON_API_KEY from ENV VAR (never hardcoded)
- [ ] ClickHouse credentials from ENV VARS
- [ ] Operational configs from ConfigClient
- [ ] Gap detection queries live_aggregates (not historical_aggregates)
- [ ] Verification enabled after downloads
- [ ] NATS subject pattern correct (market.{SYMBOL}.5m)

### **After Deployment**

- [ ] Service starts successfully
- [ ] Operational config loaded from Central Hub
- [ ] Gap detection finds correct missing dates
- [ ] Downloads succeed (check Polygon.io API limits)
- [ ] NATS publish working (check subscribers)
- [ ] Verification passes (data in ClickHouse)

---

## 🚨 COMMON ISSUES

### **Issue 1: Wrong Date Range (10 Years Instead of 7 Days)**

**Symptoms:**
```
📅 Checking date range: 2015-01-01 to 2025-10-19
Found 2810 missing dates  # ❌ WAY TOO MANY!
```

**Root Cause:**
- Using `HISTORICAL_START_DATE=2015-01-01` from .env
- This is for Dukascopy initial download, not Polygon gap filling!

**Fix:**
```bash
# In .env, add separate variables:
POLYGON_GAP_START_DATE=today-7days
POLYGON_GAP_END_DATE=today

# In docker-compose.yml:
environment:
  - HISTORICAL_START_DATE=${POLYGON_GAP_START_DATE:-today-7days}
  - HISTORICAL_END_DATE=${POLYGON_GAP_END_DATE:-today}
```

**Verification:**
```bash
docker logs suho-polygon-historical | grep "Checking date range"
# Should show: 2025-10-12 to 2025-10-19 (7 days)
```

---

### **Issue 2: ClickHouse Connection Refused**

**Symptoms:**
```
ConnectionRefusedError: [Errno 111] Connection refused
Code: 210. Connection refused (suho-clickhouse:9000)
```

**Root Cause:**
- Default ClickHouse credentials in code don't match actual ENV VARS
- `user='default'` but should be `user='suho_analytics'`

**Fix:**
```python
# config.py - Use correct defaults matching ENV VARS
self._clickhouse_user = os.getenv('CLICKHOUSE_USER', 'suho_analytics')  # ✅
self._clickhouse_database = os.getenv('CLICKHOUSE_DATABASE', 'suho_analytics')  # ✅

# NOT:
self._clickhouse_user = os.getenv('CLICKHOUSE_USER', 'default')  # ❌
```

**Verification:**
```bash
docker exec suho-polygon-historical env | grep CLICKHOUSE
# Should show: user=suho_analytics, database=suho_analytics
```

---

### **Issue 3: Config Not Loading from Central Hub**

**Symptoms:**
```
WARNING: Central Hub unavailable, using safe defaults
```

**Debug:**
```bash
# Test Central Hub API directly
curl http://suho-central-hub:7000/api/v1/config/polygon-historical-downloader

# Check service can reach Central Hub
docker exec suho-polygon-historical curl http://suho-central-hub:7000/health

# Check service logs
docker logs suho-polygon-historical | grep "Central Hub\|config"
```

**Common Causes:**
- Central Hub not running
- Network connectivity issue
- Service name mismatch in config
- Auth middleware blocking request

---

## 📖 SUMMARY

**Polygon Historical Downloader = Gap Filling for Last 7 Days**

**Configuration Pattern:**
- ✅ Critical configs (API key, DB creds) from ENV VARS
- ✅ Operational configs (intervals, batch size) from Central Hub
- ✅ Safe defaults for graceful degradation
- ✅ Hot-reload support via NATS

**Key Success Factors:**
1. Download range = 7 days ONLY (not 10 years!)
2. Always verify data propagation to ClickHouse
3. Query live_aggregates for gap detection
4. Follow config hierarchy strictly
5. Monitor Polygon.io API rate limits

**Use this skill when:**
- Implementing polygon-historical-downloader
- Fixing gap filling logic
- Updating download configurations
- Debugging data pipeline issues
- Migrating to centralized config
