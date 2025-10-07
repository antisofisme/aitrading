# 🚀 DEPLOYMENT PLAN: Schema Updates & Service Rebuilds

**Date:** 2025-10-06
**Scope:** Add technical indicators + external data tables + deploy tick-aggregator
**Estimated Downtime:** ~5-10 minutes (data-bridge restart only)
**Data Loss Risk:** CRITICAL (currently losing indicator + external data)

---

## 📊 AUDIT RESULTS

### ❌ **CRITICAL ISSUES FOUND**

#### 1. ClickHouse Schema Missing Columns/Tables
- **Missing Column:** `aggregates.indicators` (26 technical indicator values)
- **Missing Tables:** 6 external data tables (economic calendar, FRED, crypto sentiment, fear & greed, commodities, market sessions)
- **Impact:** Data Bridge writing indicators but they're not persisted → **DATA LOSS**
- **Impact:** External Data Collector publishing data but no tables → **DATA LOSS**

#### 2. Service Code/Image Mismatch

| Service | Image Build Time | Code Modified | Status | Action |
|---------|------------------|---------------|--------|--------|
| **data-bridge** | Oct 6 01:13 | Oct 6 22:05 | ❌ Code 16h newer | REBUILD |
| **external-data-collector** | Oct 5 18:35 | Oct 6 21:05 | ❌ Code 28h newer | REBUILD |
| **tick-aggregator** | N/A | Oct 6 22:03 | ❌ Not deployed | BUILD + DEPLOY |
| polygon-historical-downloader | Oct 6 09:00 | Oct 4 21:14 | ✅ Image newer | OK |

#### 3. Tick Aggregator NOT Deployed
- **Status:** Code exists but:
  - No Docker image built
  - Not in `docker-compose.yml`
  - Never deployed
- **Impact:** No tick → aggregate conversion with indicators happening

---

## 🎯 DEPLOYMENT PLAN

### **Phase 1: Pre-Deployment Checks** (5 min)
1. ✅ Verify all schema files exist
2. ✅ Verify docker-compose.yml has data-bridge and external-data-collector
3. ❌ Add tick-aggregator to docker-compose.yml
4. Backup current ClickHouse schema
5. Check disk space (need ~1 GB for images)

### **Phase 2: ClickHouse Schema Updates** (2 min)
**NO DOWNTIME** - Can execute while services running

```bash
# 1. Add indicators column to aggregates table
docker exec suho-clickhouse clickhouse-client --multiquery < \
  shared/schemas/clickhouse/02_aggregates.sql

# 2. Create 6 external data tables
docker exec suho-clickhouse clickhouse-client --multiquery < \
  shared/schemas/clickhouse/03_external_economic_calendar.sql

docker exec suho-clickhouse clickhouse-client --multiquery < \
  shared/schemas/clickhouse/04_external_fred_economic.sql

docker exec suho-clickhouse clickhouse-client --multiquery < \
  shared/schemas/clickhouse/05_external_crypto_sentiment.sql

docker exec suho-clickhouse clickhouse-client --multiquery < \
  shared/schemas/clickhouse/06_external_fear_greed_index.sql

docker exec suho-clickhouse clickhouse-client --multiquery < \
  shared/schemas/clickhouse/07_external_commodity_prices.sql

docker exec suho-clickhouse clickhouse-client --multiquery < \
  shared/schemas/clickhouse/08_external_market_sessions.sql
```

**Expected Results:**
- `aggregates` table now has `indicators` column
- 6 new external data tables created with indexes

### **Phase 3: Rebuild Services** (5 min)
**PARTIAL DOWNTIME** - Data Bridge will be down during rebuild

```bash
# Navigate to backend directory
cd project3/backend

# 1. Rebuild data-bridge (CRITICAL - has indicators support)
docker-compose build data-bridge

# 2. Rebuild external-data-collector (updated code)
docker-compose build external-data-collector

# 3. Build tick-aggregator (NEW service - needs docker-compose entry first)
# Will be added in Phase 4
```

**Expected Results:**
- `backend-data-bridge:latest` built with new code (indicators support)
- `backend-external-data-collector:latest` built with new code
- Both images have Oct 6 22:00+ timestamp

### **Phase 4: Deploy Tick Aggregator** (3 min)
**NO DOWNTIME** - New service deployment

**Step 1: Add to docker-compose.yml** (insert after data-bridge section)

```yaml
  tick-aggregator:
    build:
      context: .
      dockerfile: 02-data-processing/tick-aggregator/Dockerfile
    container_name: suho-tick-aggregator
    hostname: suho-tick-aggregator
    environment:
      - INSTANCE_ID=tick-aggregator-1
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - TIMESCALEDB_HOST=timescaledb
      - TIMESCALEDB_PORT=5432
      - TIMESCALEDB_DB=${TIMESCALEDB_DB:-market_data}
      - TIMESCALEDB_USER=${TIMESCALEDB_USER:-suho_user}
      - TIMESCALEDB_PASSWORD=${TIMESCALEDB_PASSWORD:-your_secure_password}
      - NATS_URL=nats://nats:4222
      - CLICKHOUSE_HOST=clickhouse
      - CLICKHOUSE_PORT=9000
    volumes:
      - ./02-data-processing/tick-aggregator/config:/app/config:ro
      - ./01-core-infrastructure/central-hub/shared:/app/shared:ro
    networks:
      - suho-network
    depends_on:
      - timescaledb
      - nats
      - clickhouse
    restart: unless-stopped
    labels:
      - "com.suho.service=tick-aggregator"
      - "com.suho.layer=data-processing"
```

**Step 2: Build and Deploy**

```bash
# Build tick-aggregator
docker-compose build tick-aggregator

# Start tick-aggregator
docker-compose up -d tick-aggregator
```

**Expected Results:**
- `backend-tick-aggregator:latest` image created
- Container `suho-tick-aggregator` running
- Subscribing to TimescaleDB ticks
- Publishing aggregates with 26 indicators to NATS

### **Phase 5: Restart Services** (2 min)
**5-10 MIN DOWNTIME** - Data Bridge and External Collector restart

```bash
# Restart data-bridge with new image
docker-compose up -d data-bridge

# Restart external-data-collector with new image
docker-compose up -d external-data-collector
```

**Expected Results:**
- `suho-data-bridge` running with new code (writes indicators to ClickHouse)
- `suho-external-collector` running with new code
- Both containers have "Up X seconds" status

### **Phase 6: Verification** (5 min)
**NO DOWNTIME** - Read-only checks

```bash
# 1. Check all services running
docker ps | grep -E "data-bridge|external|tick-aggregator"

# 2. Check data-bridge logs for indicator writes
docker logs --tail 100 suho-data-bridge | grep -i "indicator"

# 3. Check tick-aggregator logs
docker logs --tail 100 suho-tick-aggregator

# 4. Verify indicators column populated
docker exec suho-clickhouse clickhouse-client --query \
  "SELECT symbol, timeframe, timestamp, length(indicators) as indicator_size
   FROM suho_analytics.aggregates
   WHERE timestamp >= now() - INTERVAL 1 HOUR
   ORDER BY timestamp DESC LIMIT 10"

# 5. Verify external tables populated
docker exec suho-clickhouse clickhouse-client --query \
  "SELECT 'economic_calendar' as table, count() as rows FROM suho_analytics.external_economic_calendar
   UNION ALL
   SELECT 'fred_economic', count() FROM suho_analytics.external_fred_economic
   UNION ALL
   SELECT 'crypto_sentiment', count() FROM suho_analytics.external_crypto_sentiment
   UNION ALL
   SELECT 'fear_greed_index', count() FROM suho_analytics.external_fear_greed_index
   UNION ALL
   SELECT 'commodity_prices', count() FROM suho_analytics.external_commodity_prices
   UNION ALL
   SELECT 'market_sessions', count() FROM suho_analytics.external_market_sessions"

# 6. Parse and verify indicator values
docker exec suho-clickhouse clickhouse-client --query \
  "SELECT symbol, timeframe, timestamp,
   JSONExtractString(indicators, 'rsi') as rsi,
   JSONExtractString(indicators, 'ema_14') as ema_14,
   JSONExtractString(indicators, 'macd') as macd
   FROM suho_analytics.aggregates
   WHERE indicators != ''
   ORDER BY timestamp DESC LIMIT 5"
```

**Expected Results:**
- ✅ 3 services running (data-bridge, external-collector, tick-aggregator)
- ✅ Data-bridge logs show "Writing X aggregates with indicators"
- ✅ Tick-aggregator logs show "Publishing aggregate with 26 indicators"
- ✅ `aggregates.indicators` column populated (non-empty JSON strings)
- ✅ 6 external tables have row counts > 0
- ✅ Parsed indicator values (RSI, EMA, MACD) are valid numbers

### **Phase 7: Monitor for 1 Hour** (60 min)
**NO DOWNTIME** - Passive monitoring

Monitor for:
1. No error logs in data-bridge
2. No error logs in tick-aggregator
3. No error logs in external-data-collector
4. Indicator data continuously written (check every 15 min)
5. External data continuously written (check every 15 min)

```bash
# Watch data-bridge logs
docker logs -f --tail 50 suho-data-bridge

# Watch tick-aggregator logs
docker logs -f --tail 50 suho-tick-aggregator

# Watch external-collector logs
docker logs -f --tail 50 suho-external-collector
```

---

## ⚠️ ROLLBACK PLAN

### If Schema Changes Fail:
```bash
# Drop newly added column
docker exec suho-clickhouse clickhouse-client --query \
  "ALTER TABLE suho_analytics.aggregates DROP COLUMN IF EXISTS indicators"

# Drop external tables
docker exec suho-clickhouse clickhouse-client --query \
  "DROP TABLE IF EXISTS suho_analytics.external_economic_calendar"
# ... repeat for other 5 tables
```

### If Service Rebuild Fails:
```bash
# Revert to old images
docker tag backend-data-bridge:latest backend-data-bridge:backup
docker pull <old-image-id>  # Use old image ID from audit

# Restart with old image
docker-compose up -d data-bridge external-data-collector
```

### If Tick Aggregator Fails:
```bash
# Stop and remove
docker-compose stop tick-aggregator
docker-compose rm -f tick-aggregator

# Comment out in docker-compose.yml
# No impact on existing services
```

---

## 📋 PRE-DEPLOYMENT CHECKLIST

- [ ] Backup docker-compose.yml
- [ ] Backup ClickHouse schema (pg_dump or export)
- [ ] Verify disk space (at least 2 GB free)
- [ ] Verify all 7 schema files exist
- [ ] Verify data-bridge/external-collector code changes committed
- [ ] Verify tick-aggregator code exists
- [ ] User approval to proceed

---

## 🎯 SUCCESS CRITERIA

1. ✅ `aggregates` table has `indicators` column with JSON data
2. ✅ 6 external data tables created and populated
3. ✅ Tick-aggregator service running and publishing aggregates
4. ✅ Data-bridge writing 26 indicator values per aggregate
5. ✅ External-collector writing to 6 external tables
6. ✅ No data loss (all indicators + external data persisted)
7. ✅ Services stable for 1 hour (no errors)

---

## 📊 DATA FLOW AFTER DEPLOYMENT

```
┌─────────────────────────────────────────────────────────────────┐
│                     COMPLETE DATA PIPELINE                       │
└─────────────────────────────────────────────────────────────────┘

[Polygon API] → [Live Collector] → [TimescaleDB Ticks]
                                          ↓
                                  [Tick Aggregator] ← NEW!
                                   (Calculates 26 indicators)
                                          ↓
                                    [NATS/Kafka]
                                   (aggregates topic)
                                          ↓
[External APIs] → [External Collector] → [NATS/Kafka] ← 6 sources
                                   (external_* topics)
                                          ↓
                                    [Data Bridge]
                                          ↓
                               ┌──────[ClickHouse]──────┐
                               │                         │
                         [aggregates]            [6 external tables]
                      (with indicators)       (economic, crypto, etc)
                               │                         │
                               └─────────┬───────────────┘
                                         ↓
                              [Feature Engineering Service] ← Phase 2
                                         ↓
                               [ml_training_data]
                              (70-90 features ready)
```

---

## 📝 NOTES

- **Current Status:** Data being LOST due to missing schema
- **Urgency:** HIGH - Every minute = lost indicator + external data
- **Risk Level:** LOW - Schema changes are additive (no data modification)
- **Downtime:** Only 5-10 minutes for service restarts
- **Reversible:** All changes can be rolled back
- **Next Phase:** After this deployment → Phase 2: Feature Engineering Service

---

**END OF DEPLOYMENT PLAN**

*Ready for execution pending user approval.*
