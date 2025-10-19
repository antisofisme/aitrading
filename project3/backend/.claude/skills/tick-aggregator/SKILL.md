---
name: tick-aggregator
description: Aggregates raw ticks into OHLCV candles for 7 timeframes (5m, 15m, 30m, 1h, 4h, 1d, 1w) on cron schedule, publishes to NATS for real-time consumption and Kafka for archival
license: MIT
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
metadata:
  type: Data Processing
  phase: Data Foundation (Phase 1)
  status: Active Production
  priority: P0 (Critical - ML depends on this)
  port: 8006
  dependencies:
    - central-hub
    - timescaledb
    - clickhouse
    - nats
    - kafka
  version: 2.0.0
---

# Tick Aggregator Service

Aggregates raw tick data into OHLCV (Open, High, Low, Close, Volume) candles across 7 timeframes (5m, 15m, 30m, 1h, 4h, 1d, 1w). Runs on cron schedules, publishes to NATS for real-time streaming, and archives to Kafka.

## When to Use This Skill

Use this skill when:
- Working on tick-to-candle aggregation logic
- Adding new timeframes for aggregation
- Debugging missing or incomplete candles
- Fixing late-arriving tick handling
- Optimizing aggregation performance
- Verifying OHLCV integrity (no NULL values)
- Configuring cron schedules for aggregation

## Service Overview

**Type:** Data Processing (Aggregation)
**Port:** 8006
**Input:** TimescaleDB (`market_ticks`) + ClickHouse (`historical_ticks`)
**Output:** ClickHouse (`live_aggregates` 7-day, `historical_aggregates` unlimited)
**Messaging:** NATS (real-time candles) + Kafka (archival)
**Timeframes:** 7 (5m, 15m, 30m, 1h, 4h, 1d, 1w)
**Schedule:** Cron-based (every 5min, 15min, hourly, etc.)

**Dependencies:**
- **Upstream**: polygon-live-collector (provides ticks via TimescaleDB)
- **Downstream**:
  - feature-engineering (subscribes to `bars.*.*` via NATS)
  - data-bridge (archives to ClickHouse via Kafka)
- **Infrastructure**: TimescaleDB, ClickHouse, NATS cluster, Kafka

## Key Capabilities

- Multi-timeframe OHLCV aggregation (7 timeframes)
- Cron-based scheduling for each timeframe
- Late-arriving tick handling (lookback windows)
- Dual storage: live (7-day retention) + historical (unlimited)
- Real-time NATS publishing (`bars.{symbol}.{timeframe}`)
- Kafka archival (`aggregate_archive` topic)
- OHLCV integrity validation (no NULL values)

## Architecture

### Data Flow

```
TimescaleDB.market_ticks (live, 3-day)
  +
ClickHouse.historical_ticks (batch)
  ↓
tick-aggregator (aggregate ticks → OHLCV)
  ↓
├─→ ClickHouse.live_aggregates (7-day retention)
├─→ ClickHouse.historical_aggregates (unlimited)
├─→ NATS: bars.{symbol}.{timeframe} (real-time)
└─→ Kafka: aggregate_archive (persistence)
```

### Aggregation Logic

**For Each Timeframe:**
1. Query ticks from TimescaleDB/ClickHouse for current window
2. Calculate OHLC:
   - **Open**: First tick price in window
   - **High**: Maximum tick price in window
   - **Low**: Minimum tick price in window
   - **Close**: Last tick price in window
   - **Volume**: Sum of tick volumes in window
3. Validate integrity (open <= high, low <= close, no NULLs)
4. Insert to ClickHouse (both live + historical)
5. Publish to NATS immediately
6. Archive to Kafka

### Cron Schedules

| Timeframe | Schedule | Description |
|-----------|----------|-------------|
| 5m | `*/5 * * * *` | Every 5 minutes |
| 15m | `*/15 * * * *` | Every 15 minutes |
| 30m | `0,30 * * * *` | Every 30 minutes |
| 1h | `0 * * * *` | Every hour |
| 4h | `0 */4 * * *` | Every 4 hours |
| 1d | `0 0 * * *` | Daily at midnight |
| 1w | `0 0 * * 0` | Weekly on Sunday |

### Configuration

**Operational Config (Central Hub):**
```json
{
  "operational": {
    "timeframes": ["5m", "15m", "30m", "1h", "4h", "1d", "1w"],
    "lookback_minutes": {
      "5m": 10,
      "15m": 30,
      "30m": 60,
      "1h": 120,
      "4h": 300,
      "1d": 1440,
      "1w": 10080
    },
    "enable_late_tick_handling": true,
    "batch_size": 1000
  }
}
```

## Examples

### Example 1: Fetch Config from Central Hub

```python
from shared.components.config import ConfigClient

# Initialize client
client = ConfigClient(
    service_name="tick-aggregator",
    safe_defaults={
        "operational": {
            "timeframes": ["5m", "15m", "1h"],
            "batch_size": 1000
        }
    }
)
await client.init_async()

# Get config
config = await client.get_config()
timeframes = config['operational']['timeframes']
print(f"Aggregating {len(timeframes)} timeframes: {timeframes}")
```

### Example 2: Aggregate Ticks for 5m Timeframe

```python
from tick_aggregator import TickAggregator

aggregator = TickAggregator()

# Aggregate last 5 minutes
candles = await aggregator.aggregate_timeframe(
    symbol="EURUSD",
    timeframe="5m",
    lookback_minutes=10  # Buffer for late-arriving ticks
)

# Results:
# - Inserted to ClickHouse (live_aggregates + historical_aggregates)
# - Published to NATS (bars.EURUSD.5m)
# - Archived to Kafka (aggregate_archive)
```

### Example 3: Query Aggregated Candles from ClickHouse

```sql
-- Check recent candles for EURUSD 5m
SELECT
    symbol,
    timestamp,
    open,
    high,
    low,
    close,
    volume,
    timeframe
FROM live_aggregates
WHERE symbol = 'EURUSD'
  AND timeframe = '5m'
  AND timestamp > now() - INTERVAL 1 HOUR
ORDER BY timestamp DESC
LIMIT 20;
```

### Example 4: Subscribe to NATS Real-time Candles

```bash
# Subscribe to all 5m candles
nats sub "bars.*.5m"

# Subscribe to EURUSD all timeframes
nats sub "bars.EURUSD.*"

# Subscribe to all candles
nats sub "bars.*.*"
```

### Example 5: Update Aggregation Config

```bash
# Add new timeframe via Central Hub API
curl -X POST http://suho-central-hub:7000/api/v1/config/tick-aggregator \
  -H "Content-Type: application/json" \
  -d '{
    "operational": {
      "timeframes": ["5m", "15m", "30m", "1h", "4h", "1d", "1w", "2h"],
      "batch_size": 1500
    }
  }'

# Hot-reload will automatically pick up new timeframe
```

## Guidelines

- **ALWAYS** use ConfigClient for operational settings (timeframes, lookback windows)
- **NEVER** skip aggregation windows (missing candles = incomplete ML features)
- **ALWAYS** publish to NATS immediately (feature-engineering depends on this)
- **USE** lookback windows to catch late-arriving ticks
- **ENABLE** hot-reload for zero-downtime config updates
- **VALIDATE** OHLCV integrity before publishing (no NULL values)

## Critical Rules

1. **Config Hierarchy:**
   - Timeframes, schedules → Central Hub (operational config)
   - Safe defaults → ConfigClient fallback
   - Secrets → Not applicable (no API keys needed)

2. **Aggregation Windows:**
   - **NEVER** skip windows (missing candles break ML pipeline)
   - **ALWAYS** use lookback buffers for late-arriving ticks
   - **VERIFY** both live_aggregates and historical_aggregates written

3. **Messaging (BOTH NATS + Kafka):**
   - **ALWAYS** publish to NATS immediately (real-time requirement)
   - **NEVER** skip Kafka archival (needed for replay)
   - **VERIFY** messages flowing to both systems

4. **Data Integrity:**
   - **VALIDATE** OHLC relationships: open <= high, low <= close
   - **ENSURE** no NULL values in OHLC fields
   - **CHECK** volume > 0 for all candles

5. **Performance:**
   - **BATCH** tick queries (use `batch_size` from config)
   - **INDEX** timestamp columns for fast range queries
   - **MONITOR** aggregation latency (should complete before next window)

## Common Tasks

### Add New Timeframe
1. Update config via Central Hub API (add to `timeframes` array)
2. Define lookback window in `lookback_minutes`
3. Add cron schedule entry
4. Hot-reload will automatically start aggregating new timeframe
5. Verify candles appearing in ClickHouse

### Fix Missing Candles
1. Check cron execution logs (verify schedule fired)
2. Query TimescaleDB for source ticks in missing time range
3. Verify lookback window is sufficient for late ticks
4. Manually trigger aggregation for missing window if needed
5. Check ClickHouse for candle insertion

### Debug Gaps in Candles
1. Query ClickHouse for candle counts per timeframe/symbol
2. Check cron execution history
3. Verify tick data exists in TimescaleDB for gap period
4. Review late-arriving tick handling
5. Check NATS/Kafka publishing logs

### Optimize Aggregation Performance
1. Increase `batch_size` in config (test with different values)
2. Add indexes on timestamp columns
3. Partition ClickHouse tables by date
4. Monitor query execution times
5. Consider parallel processing for multiple symbols

## Troubleshooting

### Issue 1: Missing Candles for Specific Timeframe
**Symptoms:** Some timeframes have gaps in candle data
**Solution:**
- Check cron schedule is correct and firing
- Verify source ticks exist in TimescaleDB
- Increase lookback window for that timeframe
- Manually trigger aggregation to backfill gaps
- Check logs for aggregation errors

### Issue 2: NULL Values in OHLC
**Symptoms:** Candles have NULL in open/high/low/close
**Solution:**
- Verify tick data quality in TimescaleDB
- Check aggregation logic for edge cases (empty windows)
- Ensure sufficient ticks in window for aggregation
- Review late-arriving tick handling
- Add validation to reject NULL candles

### Issue 3: NATS Publishing Delayed
**Symptoms:** Feature-engineering reports stale candles
**Solution:**
- Check NATS cluster health
- Verify publishing happens immediately after aggregation
- Review aggregation latency (should complete before next window)
- Optimize query performance (add indexes)
- Monitor network latency to NATS cluster

### Issue 4: Kafka Archive Missing Messages
**Symptoms:** Historical replay missing candles
**Solution:**
- Check Kafka broker connectivity
- Verify Kafka producer configuration
- Review Kafka topic retention policy
- Check for Kafka publish errors in logs
- Test with `kafka-console-consumer` on `aggregate_archive` topic

### Issue 5: Late-Arriving Ticks Not Captured
**Symptoms:** Candles don't update when late ticks arrive
**Solution:**
- Increase lookback window in config
- Verify late tick handling is enabled
- Check buffer strategy implementation
- Review tick arrival timestamps
- Consider re-aggregating affected windows

## Validation Checklist

After making changes to this service:
- [ ] Candles exist in ClickHouse (both `live_aggregates` + `historical_aggregates`)
- [ ] NATS publishes `bars.*.*` subjects (check feature-engineering receives)
- [ ] Kafka archives to `aggregate_archive` topic
- [ ] All 7 timeframes active (5m, 15m, 30m, 1h, 4h, 1d, 1w)
- [ ] No NULL values in OHLC (open, high, low, close all non-NULL)
- [ ] OHLC relationships valid (open <= high, low <= close)
- [ ] Volume > 0 for all candles
- [ ] Cron schedules firing correctly
- [ ] ConfigClient fetching from Central Hub
- [ ] Hot-reload responding to config updates

## Related Skills

- `central-hub` - Provides operational config and service discovery
- `polygon-live-collector` - Provides source tick data
- `data-bridge` - Consumes Kafka archives and writes to ClickHouse
- `feature-engineering` - Consumes NATS real-time candles
- `supervised-training` - Uses historical candles for training

## References

- Full Documentation: `docs/SERVICE_ARCHITECTURE_AND_FLOW.md` (lines 396-418)
- Planning Guide: `docs/PLANNING_SKILL_GUIDE.md` (Service 6, lines 810-1050)
- Flow + Messaging: `docs/SERVICE_FLOW_TREE_WITH_MESSAGING.md` (lines 251-308)
- Database Schema: `docs/table_database_input.md` (aggregates table)
- Config Architecture: `docs/CONFIG_ARCHITECTURE.md`
- Central Hub Skill: `.claude/skills/central-hub/SKILL.md`
- Code: `02-data-processing/tick-aggregator/`

---

**Created:** 2025-10-19
**Version:** 2.0.0
**Status:** Production Ready
