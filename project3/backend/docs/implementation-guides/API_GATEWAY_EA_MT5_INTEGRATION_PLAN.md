# API Gateway & EA MT5 Integration - Planning & Implementation

**Date:** 2025-10-13
**Status:** In Progress
**Priority:** High

---

## 📋 Overview

Integrasi EA MetaTrader 5 (SuhoTickStreamer) dengan backend system untuk streaming tick data real-time dari 14 forex pairs ke database.

---

## 🎯 Objectives

1. ✅ **EA MT5**: Stream tick data dari 14 pairs ke API Gateway - **READY**
2. ✅ **API Gateway**: Terima tick batch dan route ke NATS - **WORKING**
3. ✅ **Central Hub**: Update integration untuk multi-instance + auto re-registration - **IMPLEMENTED**
4. ⏳ **Data Bridge**: Route tick EA ke TimescaleDB - **UNHEALTHY (Investigating)**
5. ⚠️ **Testing**: End-to-end testing EA → Database - **PARTIAL (API Gateway verified, DB pending)**

---

## 🏗️ Architecture

```
┌─────────────────┐
│   EA MT5        │  14 pairs (EURUSD, GBPUSD, USDJPY, etc.)
│ (ICMarkets)     │  Batch interval: 1000ms
└────────┬────────┘
         │ HTTP POST /api/v1/ticks/batch
         │ JSON: {broker, account, source, ticks[]}
         ▼
┌─────────────────┐
│  API Gateway    │  Port 8000
│  (Node.js)      │  Central Hub integration ✅
└────────┬────────┘
         │ NATS Publish
         │ Subject: market.ticks.{symbol}
         │ source: 'mt5_ea'
         ▼
┌─────────────────┐
│  NATS Cluster   │  3 nodes (suho-nats-1,2,3)
│  (Messaging)    │  Real-time routing
└────────┬────────┘
         │ Subscribe: market.ticks.*
         ▼
┌─────────────────┐
│  Data Bridge    │  3 replicas
│  (Python)       │  Routing logic by source
└────────┬────────┘
         │ INSERT
         ▼
┌─────────────────┐
│  TimescaleDB    │  Table: market_ticks
│  (PostgreSQL)   │  source = 'mt5_ea'
└─────────────────┘
```

---

## ✅ Completed Tasks

### 1. **EA MT5 - SuhoTickStreamer.mq5** ✅
**Location:** `/mnt/g/khoirul/aitrading/project3/client-mt5/SuhoTickStreamer.mq5`

**Features:**
- Monitors 14 trading pairs:
  - Major: EURUSD, GBPUSD, USDJPY, USDCHF
  - Minor: AUDUSD, USDCAD, NZDUSD, EURGBP
  - Cross: EURJPY, GBPJPY, AUDJPY, NZDJPY, CHFJPY
  - Gold: XAUUSD
- Batch collection (1000ms interval, configurable)
- HTTP POST to API Gateway
- Statistics tracking (ticks sent, errors, success rate)
- Error handling with retry logic

**Configuration:**
```mql5
input string InpApiUrl = "http://localhost:8000/api/v1/ticks/batch";
input string InpApiKey = "your-api-key";
input int    InpBatchInterval = 1000;  // ms
input string InpBrokerName = "ICMarkets";
input string InpAccountId = "12345678";
input bool   InpEnableLogs = true;
```

**JSON Payload:**
```json
{
  "broker": "ICMarkets",
  "account": "12345678",
  "source": "mt5_ea",
  "timestamp": 1728825600000,
  "ticks": [
    {
      "symbol": "EURUSD",
      "timestamp": 1728825599500,
      "bid": 1.09551,
      "ask": 1.09553,
      "last": 1.09552,
      "volume": 100
    }
  ]
}
```

---

### 2. **API Gateway - Central Hub Integration** ✅
**Location:** `/mnt/g/khoirul/aitrading/project3/backend/01-core-infrastructure/api-gateway/`

#### A. New Central Hub Client (Node.js)
**File:** `src/config/central-hub-client.js`

**Features:**
- Service registration with multi-instance support
- Auto-detect instance_id from hostname (consistent with Python SDK)
- Periodic heartbeat (default: 30s)
- **Auto re-registration on 404** (consistent with Python SDK)
- Graceful deregistration

**Key Implementation:**
```javascript
// Auto-detect instance ID
const envInstanceId = process.env.INSTANCE_ID?.trim() || '';
this.instanceId = envInstanceId || os.hostname();

// Auto re-registration on 404
if (response.status === 404) {
  console.warn(`⚠️  Service not found (404) - re-registering...`);
  this.registered = false;
  const success = await this.register();
  // ...
}
```

#### B. Updated Config Loader
**File:** `src/config/central-hub-config.js`

**Changes:**
- Uses new CentralHubClient
- Supports NATS cluster (cluster_urls array)
- Automatic heartbeat start on initialize
- Metrics callback for heartbeat

---

### 3. **API Gateway - Tick Ingestion Endpoint** ✅
**File:** `src/index.js`

**Endpoint:** `POST /api/v1/ticks/batch`

**Request Validation:**
```javascript
// Required fields
if (!ticks || !Array.isArray(ticks) || ticks.length === 0) {
  return 400 - ticks array required
}
if (!broker || !account) {
  return 400 - broker and account required
}
```

**NATS Publishing Logic:**
```javascript
for (const tick of ticks) {
  const subject = `market.ticks.${tick.symbol}`;
  const tickData = {
    symbol: tick.symbol,
    timestamp: tick.timestamp,
    bid: tick.bid,
    ask: tick.ask,
    last: tick.last || 0,
    volume: tick.volume || 0,
    broker: broker,           // Metadata
    account: account,         // Metadata
    source: source || 'mt5_ea'  // Source identifier
  };

  await natsClient.publishViaNATS(subject, { data: tickData });
}
```

**Response:**
```json
{
  "status": "ok",
  "ticks_received": 14,
  "ticks_published": 14,
  "processing_time_ms": 45,
  "timestamp": 1728825600000,
  "correlationId": "req_123456"
}
```

---

### 4. **NATS Transport - Cluster Support** ✅
**File:** `src/transport/nats-kafka-client.js`

**Changes:**
```javascript
// Parse NATS servers (supports cluster)
let natsServers = ['nats://suho-nats-server:4222'];  // Fallback
if (config.nats?.servers) {
  natsServers = Array.isArray(config.nats.servers)
    ? config.nats.servers
    : [config.nats.servers];
}
```

**Benefits:**
- Supports NATS cluster (3 nodes)
- Automatic failover
- Load balancing across nodes

---

## 🔄 Data Flow Details

### 1. **Tick Collection (EA → API Gateway)**
```
EA collects ticks every OnTick() event
  → Buffers in TickBuffer[] array
  → Every 1000ms, sends HTTP POST batch
  → Includes broker + account metadata
```

### 2. **API Gateway Processing**
```
Receive JSON batch
  → Validate structure
  → Extract broker/account metadata
  → Loop through ticks array
  → Publish each tick to NATS:
      Subject: market.ticks.{symbol}
      Payload: {tick + broker + account + source}
```

### 3. **NATS Routing**
```
NATS receives on market.ticks.*
  → Data Bridge subscribes to market.ticks.*
  → Routes based on source field
```

### 4. **Data Bridge Routing Logic**
**File:** `data-bridge/src/main.py:296-323`

```python
async def _save_tick(self, data: dict):
    source = data.get('source', 'unknown')

    # ROUTING DECISION
    if source == 'dukascopy_historical':
        # → ClickHouse ticks table (historical)
        await self._save_tick_to_clickhouse(data)
    else:
        # → TimescaleDB market_ticks (ALL LIVE SOURCES)
        await self._save_tick_to_timescale(data)
        # Includes: polygon, mt5_ea, oanda, etc.
```

**Result:** EA ticks (`source='mt5_ea'`) → **TimescaleDB.market_ticks** ✅

### 5. **TimescaleDB Storage**
**Table:** `market_ticks`
**Schema:** (from TickData model)
```sql
CREATE TABLE market_ticks (
  symbol TEXT NOT NULL,
  timestamp_ms BIGINT NOT NULL,
  bid DOUBLE PRECISION NOT NULL,
  ask DOUBLE PRECISION NOT NULL,
  mid DOUBLE PRECISION,
  spread DOUBLE PRECISION,
  volume DOUBLE PRECISION,
  source TEXT NOT NULL,          -- 'mt5_ea', 'polygon', etc.
  exchange INTEGER,
  event_type TEXT DEFAULT 'quote',
  use_case TEXT,                 -- Can store JSON metadata
  PRIMARY KEY (symbol, timestamp_ms)
);
```

**Benefits of Shared Table:**
- ✅ Unified query interface
- ✅ Easy source comparison
- ✅ Scalable for future sources
- ✅ Consistent with existing architecture

---

## ✅ Resolved Issues

### 1. **API Gateway NATS Connection** ✅ FIXED
**Issue:** API Gateway failed to connect to NATS cluster

**Root Cause:** Environment variable `NATS_URL` was set to wrong hostname in container

**Solution:**
1. Fixed environment variable in `.env` file (correct cluster URLs)
2. Recreated container to pick up new environment
3. NATS now connects successfully to cluster: `nats-1:4222`, `nats-2:4222`, `nats-3:4222`

**Status:** ✅ VERIFIED WORKING
```
[TRANSPORT-INFO] NATS client connected successfully
[TRANSPORT-INFO] Kafka producer connected successfully
```

### 2. **Tick Endpoint NATS Publishing** ✅ FIXED
**Issue:** Tick endpoint received ticks but published 0 to NATS

**Root Cause:** Code referenced wrong property path `this.bidirectionalRouter.transport` instead of `this.bidirectionalRouter.natsKafkaClient`

**Solution:**
- Fixed reference in `src/index.js:517`
- Tested with curl: `ticks_published: 2` ✅

**Status:** ✅ VERIFIED WORKING

---

## ⏳ Pending Tasks

### 1. **Data Bridge Health Issue** ⏳ INVESTIGATING
**Issue:** Data Bridge containers showing as unhealthy

**Impact:** Tick messages published to NATS but not consumed/stored in database

**Action Required:**
1. Investigate Data Bridge health check failures
2. Check Data Bridge NATS subscription
3. Verify Data Bridge logs (currently too large)
4. Restart Data Bridge instances if needed

---

### 2. **Verify NATS Cluster Config** ⏳

**Check Central Hub Config:**
```bash
curl http://localhost:7000/api/config/messaging/nats
```

**Expected Response:**
```json
{
  "config": {
    "connection": {
      "host": "suho-nats-1",
      "port": 4222,
      "cluster_urls": [
        "nats://suho-nats-1:4222",
        "nats://suho-nats-2:4222",
        "nats://suho-nats-3:4222"
      ]
    }
  }
}
```

**Action:**
- Ensure `cluster_urls` is properly set in Central Hub
- API Gateway should fetch and use cluster URLs

---

### 3. **Test Tick Endpoint** ⏳

**Manual Test:**
```bash
curl -X POST http://localhost:8000/api/v1/ticks/batch \
  -H "Content-Type: application/json" \
  -d '{
    "broker": "ICMarkets",
    "account": "test123",
    "source": "mt5_ea",
    "ticks": [
      {
        "symbol": "EURUSD",
        "timestamp": 1728825599500,
        "bid": 1.09551,
        "ask": 1.09553,
        "last": 1.09552,
        "volume": 100
      }
    ]
  }'
```

**Expected Response:**
```json
{
  "status": "ok",
  "ticks_received": 1,
  "ticks_published": 1,
  "processing_time_ms": 15,
  "timestamp": 1728825600000
}
```

**Verify in NATS:**
```bash
# Subscribe to test
docker exec suho-nats-1 nats sub "market.ticks.EURUSD"
```

---

### 4. **Test EA in MT5** ⏳

**Installation Steps:**
1. Copy `SuhoTickStreamer.mq5` to MT5 folder:
   ```
   C:\Users\{User}\AppData\Roaming\MetaQuotes\Terminal\{GUID}\MQL5\Experts\
   ```

2. Configure settings:
   - API URL: `http://localhost:8000/api/v1/ticks/batch`
   - API Key: (optional for testing)
   - Broker: Your broker name
   - Account: Your account number
   - Batch Interval: 1000ms (default)

3. Enable WebRequest in MT5:
   - Tools → Options → Expert Advisors
   - Check "Allow WebRequest for listed URL"
   - Add: `http://localhost:8000`

4. Attach EA to any chart (symbol doesn't matter)

5. Monitor Expert tab for logs:
   ```
   ✅ Symbol available: EURUSD
   ✅ Symbol available: GBPUSD
   ...
   ✅ Batch sent: 14 ticks | Total: 14
   ```

---

### 5. **Verify Data in TimescaleDB** ⏳

**Query:**
```sql
-- Check MT5 EA ticks
SELECT
  symbol,
  timestamp_ms,
  bid,
  ask,
  source,
  use_case
FROM market_ticks
WHERE source = 'mt5_ea'
ORDER BY timestamp_ms DESC
LIMIT 10;
```

**Expected Result:**
```
symbol  | timestamp_ms  | bid     | ask     | source  | use_case
--------|---------------|---------|---------|---------|----------
EURUSD  | 1728825599500 | 1.09551 | 1.09553 | mt5_ea  | {"broker":"ICMarkets","account":"12345678"}
GBPUSD  | 1728825599510 | 1.28334 | 1.28336 | mt5_ea  | {"broker":"ICMarkets","account":"12345678"}
```

---

## 🔍 Troubleshooting Guide

### Issue 1: API Gateway Can't Connect to NATS

**Symptoms:**
```
Error: getaddrinfo ENOTFOUND suho-nats-server
```

**Solutions:**
1. Check NATS container status:
   ```bash
   docker ps | grep nats
   ```

2. Check docker network:
   ```bash
   docker network inspect backend_default
   ```

3. Test DNS resolution inside API Gateway:
   ```bash
   docker exec suho-api-gateway ping suho-nats-1
   ```

4. Check Central Hub config:
   ```bash
   curl http://localhost:7000/api/config/messaging/nats
   ```

---

### Issue 2: EA WebRequest Blocked

**Symptoms:**
```
❌ ERROR: WebRequest not allowed. Add URL to allowed list
```

**Solution:**
1. Open MT5
2. Tools → Options → Expert Advisors
3. Check "Allow WebRequest for listed URL"
4. Add: `http://localhost:8000`
5. Restart MT5

---

### Issue 3: Tick Data Not in Database

**Debug Steps:**

1. **Check API Gateway logs:**
   ```bash
   docker logs suho-api-gateway --tail 100 | grep "tick"
   ```

2. **Check NATS messages:**
   ```bash
   docker exec suho-nats-1 nats sub "market.ticks.*"
   ```

3. **Check Data Bridge logs:**
   ```bash
   docker logs suho-data-bridge --tail 100 | grep "tick"
   ```

4. **Check TimescaleDB:**
   ```bash
   docker exec suho-timescaledb psql -U postgres -d suho_analytics \
     -c "SELECT COUNT(*) FROM market_ticks WHERE source='mt5_ea';"
   ```

---

## 📊 Monitoring & Metrics

### API Gateway Metrics
- Endpoint: `GET http://localhost:8000/stats`
- Metrics:
  - `ticks_received`: Total ticks ingested
  - `ticks_published`: Total ticks sent to NATS
  - `error_count`: Failed requests
  - `processing_time_ms`: Average latency

### Data Bridge Metrics
- Logs: `docker logs suho-data-bridge`
- Metrics:
  - `ticks_saved`: Total ticks in TimescaleDB
  - `candles_saved_clickhouse`: Aggregates count
  - `buffer_size`: Current buffer size

### EA Metrics
- MT5 Expert Tab:
  - Total ticks sent
  - Total batches sent
  - Error count
  - Success rate %
  - Average ticks per batch

---

## 🚀 Deployment Checklist

### Pre-Deployment
- [ ] API Gateway passes health check
- [ ] NATS cluster is healthy (3/3 nodes)
- [ ] Data Bridge connected to TimescaleDB
- [ ] Central Hub configs are correct
- [ ] Manual tick test successful

### EA Deployment
- [ ] EA compiled without errors
- [ ] WebRequest URL whitelisted in MT5
- [ ] Broker and account configured
- [ ] API endpoint reachable from trading PC
- [ ] All 14 symbols available in MT5

### Post-Deployment
- [ ] Monitor API Gateway logs (first 10 minutes)
- [ ] Verify NATS message flow
- [ ] Check TimescaleDB inserts
- [ ] Monitor EA statistics in MT5
- [ ] Set up alerts for errors

---

## 📝 Next Steps

1. **Fix API Gateway NATS Connection** (Priority: HIGH)
   - Debug DNS resolution
   - Update NATS config in Central Hub
   - Test connection

2. **End-to-End Testing** (Priority: HIGH)
   - Manual curl test → API Gateway
   - Verify NATS routing
   - Check TimescaleDB data

3. **EA Production Testing** (Priority: MEDIUM)
   - Install in demo account
   - Monitor for 1 hour
   - Verify data quality

4. **Production Deployment** (Priority: LOW)
   - Deploy to production MT5
   - Monitor real ticks
   - Set up alerting

---

## 📚 References

- EA Source: `/mnt/g/khoirul/aitrading/project3/client-mt5/SuhoTickStreamer.mq5`
- API Gateway: `/mnt/g/khoirul/aitrading/project3/backend/01-core-infrastructure/api-gateway/`
- Data Bridge: `/mnt/g/khoirul/aitrading/project3/backend/02-data-processing/data-bridge/`
- Central Hub SDK: `/mnt/g/khoirul/aitrading/project3/backend/01-core-infrastructure/central-hub/sdk/python/`

---

**Last Updated:** 2025-10-13
**Next Review:** After NATS connection fix
