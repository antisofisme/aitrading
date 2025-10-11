# Tick Aggregator V2 - Deployment Guide

## Overview

Complete redesign of tick aggregator with 4 parallel components for continuous gap monitoring and priority-based data handling.

## Architecture Changes

### Before (V1)
```
Single Processor
├─ Cron-based (every 5m, 15m, 30m, 1h, 4h, 1d, 1w)
├─ Gap detection only before scheduled job
└─ No deduplication priority
```

### After (V2)
```
4 Parallel Components
├─ [1] LiveProcessor (CRITICAL) - Every 1 minute
├─ [2] LiveGapMonitor (HIGH) - Every 5 minutes
├─ [3] HistoricalProcessor (MEDIUM) - Every 6 hours
└─ [4] HistoricalGapMonitor (LOW) - Daily 02:00 UTC
```

## What Changed

### 1. ClickHouse Schema (✅ COMPLETED)
**Added 2 columns to `aggregates` table:**
- `version UInt64` - Deduplication priority
- `created_at DateTime` - Insert timestamp

**Migrated** 35.4M rows to new schema with calculated versions:
- `live_aggregated`: version = timestamp_ms (highest)
- `live_gap_filled`: version = timestamp_ms - 1
- `historical_aggregated`: version = 1
- `polygon_historical`: version = 0

### 2. New Components (✅ COMPLETED)

#### LiveProcessor (`live_processor.py`)
- **Priority**: CRITICAL
- **Trigger**: Every 1 minute
- **Purpose**: Aggregate recent ticks from TimescaleDB
- **Flow**:
  1. Check gaps (last 24h)
  2. Fill gaps if found
  3. Aggregate recent ticks
  4. Publish to ClickHouse (source='live_aggregated')

#### LiveGapMonitor (`live_gap_monitor.py`)
- **Priority**: HIGH
- **Trigger**: Every 5 minutes
- **Purpose**: Scan and fill gaps in live data (last 7 days)
- **Flow**:
  1. Scan ClickHouse for gaps
  2. Re-aggregate from TimescaleDB ticks
  3. Mark as source='live_gap_filled'
  4. Track oldest gap age

#### HistoricalProcessor (`historical_processor.py`)
- **Priority**: MEDIUM
- **Trigger**: Every 6 hours
- **Purpose**: Aggregate 1m bars → higher timeframes
- **Flow**:
  1. Check for new 1m data
  2. Aggregate to 5m, 15m, 30m, 1h, 4h, 1d, 1w
  3. Calculate technical indicators
  4. Mark as source='historical_aggregated'

#### HistoricalGapMonitor (`historical_gap_monitor.py`)
- **Priority**: LOW
- **Trigger**: Daily at 02:00 UTC
- **Purpose**: Fill old gaps (>7 days)
- **Flow**:
  1. Scan for gaps >7 days old
  2. Re-aggregate from 1m bars
  3. Skip recent data (live owns it)

### 3. Updated Writers (✅ COMPLETED)

#### clickhouse_writer.py (data-bridge)
- Added version calculation based on source
- Added created_at timestamp
- Updated insert column list

#### historical_aggregator.py (tick-aggregator)
- Added version calculation
- Added created_at timestamp
- Updated insert column list

### 4. Main Orchestrator (✅ COMPLETED)

Created `main_v2.py` with:
- Parallel initialization of 4 components
- APScheduler with 4 cron jobs
- Comprehensive metrics collection
- Heartbeat with all component stats

## Deployment Steps

### Step 1: Backup Current Service
```bash
cd /mnt/g/khoirul/aitrading/project3/backend

# Backup current tick-aggregator
docker stop suho-tick-aggregator
docker commit suho-tick-aggregator tick-aggregator-backup:v1
```

### Step 2: Replace main.py
```bash
cd 02-data-processing/tick-aggregator/src

# Backup old main
mv main.py main_v1_backup.py

# Activate new version
mv main_v2.py main.py
```

### Step 3: Rebuild Data-Bridge (Updated Writer)
```bash
cd /mnt/g/khoirul/aitrading/project3/backend

# Rebuild data-bridge with new version logic
docker build -t backend-data-bridge:latest \
  -f 02-data-processing/data-bridge/Dockerfile .

# Restart data-bridge
docker restart suho-data-bridge
```

### Step 4: Rebuild Tick-Aggregator (New V2)
```bash
cd /mnt/g/khoirul/aitrading/project3/backend

# Rebuild tick-aggregator with V2 components
docker build -t backend-tick-aggregator:latest \
  -f 02-data-processing/tick-aggregator/Dockerfile .

# Restart tick-aggregator
docker restart suho-tick-aggregator
```

### Step 5: Verify Deployment
```bash
# Check tick-aggregator logs
docker logs suho-tick-aggregator --tail 100

# Should see:
# ✅ SERVICE STARTED - ALL 4 COMPONENTS ACTIVE
# 📋 Scheduled Jobs:
#    - LiveProcessor (1min): cron[minute='*']
#    - LiveGapMonitor (5min): cron[minute='*/5']
#    - HistoricalProcessor (6h): cron[hour='*/6', minute='30']
#    - HistoricalGapMonitor (daily): cron[hour='2', minute='0']

# Check data-bridge logs
docker logs suho-data-bridge --tail 50

# Check ClickHouse for new data
docker exec suho-clickhouse clickhouse-client --query "
SELECT
    source,
    COUNT(*) as count,
    MIN(version) as min_version,
    MAX(version) as max_version
FROM suho_analytics.aggregates
WHERE created_at >= now() - INTERVAL 1 HOUR
GROUP BY source
ORDER BY source
FORMAT Pretty
"
```

## Monitoring

### Key Metrics to Track

1. **LiveProcessor**
   - `total_runs` - Should increment every minute
   - `total_candles_generated` - Live candles created
   - `total_gaps_filled` - Gaps recovered
   - `last_run_status` - Should be "success"

2. **LiveGapMonitor**
   - `total_gaps_found` - Gaps detected
   - `total_gaps_filled` - Gaps recovered
   - `oldest_gap_hours` - Should be < 24h

3. **HistoricalProcessor**
   - `total_symbols_processed` - Symbols with data
   - `total_candles_generated` - Historical candles

4. **HistoricalGapMonitor**
   - `total_gaps_filled` - Old gaps recovered

### Alerting Thresholds

```yaml
alerts:
  live_processor:
    - metric: last_run_status
      condition: != "success"
      threshold: 3 consecutive failures
      action: Alert DevOps

    - metric: oldest_gap_hours
      condition: > 24
      action: Investigate gap filling

  data_quality:
    - metric: coverage_24h
      condition: < 99%
      action: Check TimescaleDB connectivity

    - metric: coverage_7d
      condition: < 98%
      action: Review gap monitor logs
```

## Rollback Plan

If issues occur:

```bash
# Stop current service
docker stop suho-tick-aggregator

# Restore V1
cd /mnt/g/khoirul/aitrading/project3/backend/02-data-processing/tick-aggregator/src
mv main.py main_v2_failed.py
mv main_v1_backup.py main.py

# Rebuild
cd /mnt/g/khoirul/aitrading/project3/backend
docker build -t backend-tick-aggregator:latest \
  -f 02-data-processing/tick-aggregator/Dockerfile .

# Restart
docker start suho-tick-aggregator
```

**Note:** ClickHouse schema changes are backward compatible. V1 code will work with new schema (extra columns are ignored).

## Expected Benefits

1. **No Data Loss**: Continuous gap monitoring prevents data loss from service restarts
2. **Priority Handling**: Live data always takes precedence over historical
3. **Auto Recovery**: Gaps automatically detected and filled
4. **Better Visibility**: 4 components report separate metrics
5. **Scalability**: Each component can be optimized independently

## Testing Checklist

- [ ] ClickHouse schema has version + created_at columns
- [ ] Data-bridge inserts with version priority
- [ ] Tick-aggregator V2 starts successfully
- [ ] All 4 cron jobs scheduled
- [ ] LiveProcessor runs every minute
- [ ] LiveGapMonitor runs every 5 minutes
- [ ] New data has correct version values
- [ ] Gap detection works
- [ ] Deduplication prioritizes live data
- [ ] Metrics endpoint returns all component stats

## Next Steps

After successful deployment:

1. Monitor for 24 hours
2. Verify gap detection accuracy
3. Check deduplication behavior
4. Review metrics and logs
5. Fine-tune cron schedules if needed
6. Remove V1 backup if stable

---

**Deployment Date**: [To be filled]
**Deployed By**: [To be filled]
**Status**: Ready for deployment
