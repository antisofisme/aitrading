---
name: data-bridge
description: Data routing hub that consumes from NATS and Kafka, deduplicates using DragonflyDB, and archives to ClickHouse with batch writes for optimal performance
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
  priority: P0 (Critical - archives to permanent storage)
  port: 8005
  dependencies:
    - central-hub
    - timescaledb
    - clickhouse
    - dragonflydb
    - nats
    - kafka
  version: 2.0.0
---

# Data Bridge Service

Data routing hub that consumes from multiple sources (NATS real-time + Kafka backup), performs deduplication using DragonflyDB cache, and archives to ClickHouse historical tables with batch writes for optimal performance.

## When to Use This Skill

Use this skill when:
- Working on data archival from live to historical storage
- Implementing deduplication logic
- Debugging data loss between TimescaleDB → ClickHouse
- Optimizing batch write performance
- Configuring NATS/Kafka consumption patterns
- Verifying dual-path redundancy (NATS + Kafka)

## Service Overview

**Type:** Data Processing (Router + Archival)
**Port:** 8005
**Input:** NATS (`ticks.>`, `bars.>`, `market.external.>`) + Kafka (`*_archive` topics)
**Output:** ClickHouse (`historical_ticks`, `historical_aggregates`, `external_*`)
**Deduplication:** DragonflyDB (1-hour TTL cache)
**Pattern:** Multi-source consumer → Deduplicate → Batch write

**Dependencies:**
- **Upstream**:
  - polygon-live-collector (NATS ticks, Kafka tick_archive)
  - tick-aggregator (NATS bars, Kafka aggregate_archive)
  - external-data-collector (NATS external, Kafka external_archive)
- **Downstream**: ClickHouse (writes historical data)
- **Infrastructure**: NATS cluster (3 nodes), Kafka, ClickHouse, DragonflyDB

## Key Capabilities

- Multi-source consumption (NATS + Kafka)
- DragonflyDB-based deduplication (1-hour TTL)
- Batch writes to ClickHouse (configurable batch size)
- Dual-path redundancy (NATS primary, Kafka backup)
- TimescaleDB archival before 3-day expiration
- Consumer group load balancing (`data-bridge-group`)
- Data loss prevention with count validation

## Architecture

### Data Flow

```
NATS Subscriptions:
  - ticks.> (real-time tick stream)
  - bars.> (real-time candle stream)
  - market.external.> (external data stream)
    ↓
Kafka Consumption:
  - tick_archive (backup tick stream)
  - aggregate_archive (backup candle stream)
  - external_data_archive (backup external stream)
    ↓
TimescaleDB.live_ticks (read for archiving after 3 days)
    ↓
data-bridge
  ├─→ DragonflyDB (check for duplicates)
  ├─→ Batch accumulation (configurable size)
  └─→ ClickHouse (batch write)
        ├─→ historical_ticks
        ├─→ historical_aggregates
        └─→ external_* tables
```

### Deduplication Strategy

**DragonflyDB Cache:**
- **Key Format**: `{symbol}:{timestamp_ms}:{data_type}`
  - Example: `EURUSD:1760867890000:tick`
  - Example: `XAUUSD:1760867900000:bar_5m`
- **TTL**: 1 hour (3600 seconds)
- **LRU Size**: 10,000 entries max
- **Purpose**: Prevent duplicate inserts from dual paths (NATS + Kafka)

**How It Works:**
1. Message received from NATS or Kafka
2. Generate cache key from message data
3. Check DragonflyDB: `EXISTS {key}`
4. If exists → Skip (duplicate)
5. If not exists → Add to batch, set cache key with 1-hour TTL
6. When batch full → Write to ClickHouse

### Batch Write Strategy

**Configuration:**
```json
{
  "operational": {
    "batch_size_ticks": 1000,
    "batch_size_candles": 500,
    "batch_size_external": 100,
    "batch_timeout_seconds": 30,
    "enable_deduplication": true,
    "dual_path_enabled": true
  }
}
```

**Batch Logic:**
- Accumulate messages until batch size reached
- OR timeout expires (whichever comes first)
- Write entire batch to ClickHouse in single query
- Clear batch, continue accumulating

### Configuration

**Operational Config (Central Hub):**
```json
{
  "operational": {
    "batch_size_ticks": 1000,
    "batch_size_candles": 500,
    "batch_size_external": 100,
    "batch_timeout_seconds": 30,
    "enable_deduplication": true,
    "dual_path_enabled": true,
    "nats_subscriptions": [
      "ticks.>",
      "bars.>",
      "market.external.>"
    ],
    "kafka_topics": [
      "tick_archive",
      "aggregate_archive",
      "external_data_archive"
    ],
    "consumer_group": "data-bridge-group"
  }
}
```

## Examples

### Example 1: Fetch Config from Central Hub

```python
from shared.components.config import ConfigClient

# Initialize client
client = ConfigClient(
    service_name="data-bridge",
    safe_defaults={
        "operational": {
            "batch_size_ticks": 1000,
            "batch_timeout_seconds": 30,
            "enable_deduplication": True
        }
    }
)
await client.init_async()

# Get config
config = await client.get_config()
batch_size = config['operational']['batch_size_ticks']
print(f"Using batch size: {batch_size}")
```

### Example 2: Subscribe to NATS Streams

```python
from data_bridge import DataBridge

bridge = DataBridge()

# Subscribe to all tick streams
await bridge.subscribe_nats("ticks.>", callback=handle_ticks)

# Subscribe to all candle streams
await bridge.subscribe_nats("bars.>", callback=handle_candles)

# Callbacks will:
# 1. Check DragonflyDB for duplicates
# 2. Add to batch if not duplicate
# 3. Write batch when size reached
```

### Example 3: Check Deduplication Cache

```bash
# Connect to DragonflyDB
redis-cli -h suho-dragonflydb -p 6379

# Check if key exists
EXISTS EURUSD:1760867890000:tick

# Get TTL
TTL EURUSD:1760867890000:tick

# Count cached keys
DBSIZE
```

### Example 4: Verify Data Archived to ClickHouse

```sql
-- Check tick counts in historical storage
SELECT
    symbol,
    COUNT(*) as tick_count,
    MIN(timestamp_ms) as oldest,
    MAX(timestamp_ms) as newest,
    ROUND((MAX(timestamp_ms) - MIN(timestamp_ms)) / 1000.0 / 86400.0, 2) as days_span
FROM historical_ticks
GROUP BY symbol
ORDER BY tick_count DESC;

-- Compare live vs historical (verify archival)
-- Live (TimescaleDB)
SELECT symbol, COUNT(*) as live_count
FROM market_ticks
WHERE timestamp_ms > (EXTRACT(EPOCH FROM NOW() - INTERVAL '3 days') * 1000)
GROUP BY symbol;

-- Historical (ClickHouse) - should have data older than 3 days
SELECT symbol, COUNT(*) as historical_count
FROM historical_ticks
WHERE timestamp_ms < (now() - INTERVAL 3 DAY) * 1000
GROUP BY symbol;
```

### Example 5: Update Batch Configuration

```bash
# Optimize batch size via Central Hub API
curl -X POST http://suho-central-hub:7000/api/v1/config/data-bridge \
  -H "Content-Type: application/json" \
  -d '{
    "operational": {
      "batch_size_ticks": 2000,
      "batch_timeout_seconds": 60
    }
  }'

# Hot-reload will automatically apply new batch settings
```

## Guidelines

- **ALWAYS** use ConfigClient for operational settings (batch sizes, timeouts)
- **NEVER** skip deduplication (check DragonflyDB before insert)
- **ALWAYS** use batch writes (never single inserts to ClickHouse)
- **VERIFY** both NATS + Kafka paths working (dual redundancy)
- **ENSURE** TimescaleDB archival happens before 3-day expiration
- **MONITOR** batch write latency (should complete before next batch)

## Critical Rules

1. **Config Hierarchy:**
   - Batch sizes, timeouts → Central Hub (operational config)
   - Safe defaults → ConfigClient fallback
   - No secrets needed

2. **Deduplication (MANDATORY):**
   - **NEVER** skip DragonflyDB check (prevents duplicates)
   - **ALWAYS** set 1-hour TTL on cache keys
   - **VERIFY** cache working (check DBSIZE)

3. **Dual-Path Consumption:**
   - **VERIFY** both NATS + Kafka active
   - **PRIMARY** path: NATS (real-time)
   - **BACKUP** path: Kafka (redundancy + replay)
   - **CHECK** consumer group balance

4. **Batch Writing:**
   - **ALWAYS** use batch writes (performance critical)
   - **NEVER** write single records to ClickHouse
   - **CONFIGURE** batch size based on throughput
   - **TIMEOUT** batch write if size not reached

5. **Data Integrity:**
   - **VALIDATE** no data loss (compare live vs historical counts)
   - **ENSURE** TimescaleDB archival before expiration
   - **MONITOR** write latency and throughput

## Common Tasks

### Increase Batch Size for Performance
1. Update config via Central Hub API (increase `batch_size_ticks`)
2. Monitor write latency and throughput
3. Test with different batch sizes (1000 → 2000 → 5000)
4. Find optimal balance between latency and performance
5. Verify no memory issues with larger batches

### Debug Missing Data in ClickHouse
1. Check NATS subscriptions active (`nats sub "ticks.>"`)
2. Verify Kafka consumer group balanced
3. Check DragonflyDB cache (might be filtering as duplicates)
4. Query TimescaleDB for source data
5. Review batch write logs for errors

### Fix Deduplication Issues
1. Check DragonflyDB connectivity
2. Verify TTL settings (should be 1 hour)
3. Review cache key generation logic
4. Monitor cache size (should not exceed LRU limit)
5. Clear cache if needed: `FLUSHDB`

### Optimize Archival Performance
1. Increase batch sizes (test different values)
2. Adjust timeout settings
3. Add ClickHouse partitioning by date
4. Monitor network latency to ClickHouse
5. Consider parallel batch writers

## Troubleshooting

### Issue 1: Duplicate Data in ClickHouse
**Symptoms:** Same timestamps appearing multiple times
**Solution:**
- Verify deduplication enabled in config
- Check DragonflyDB connectivity
- Review cache key generation (ensure unique keys)
- Clear cache and re-process if needed

### Issue 2: Data Not Appearing in Historical Tables
**Symptoms:** ClickHouse historical tables empty or stale
**Solution:**
- Check NATS subscriptions active
- Verify Kafka consumer running
- Review batch accumulation logs
- Check ClickHouse connectivity and credentials
- Test batch write manually

### Issue 3: High Memory Usage
**Symptoms:** Container using excessive memory
**Solution:**
- Reduce batch sizes in config
- Decrease batch timeout (force more frequent writes)
- Check for memory leaks in batch accumulation
- Monitor DragonflyDB cache size
- Restart service to clear accumulated batches

### Issue 4: Slow Archival (Lagging Behind)
**Symptoms:** Historical data missing recent entries
**Solution:**
- Increase batch sizes (write more efficiently)
- Reduce batch timeout (write more frequently)
- Add parallel batch writers
- Optimize ClickHouse indexes
- Check network latency

### Issue 5: Consumer Group Imbalance
**Symptoms:** Some Kafka partitions not being consumed
**Solution:**
- Check Kafka consumer group status
- Verify partition assignment
- Restart consumer to trigger rebalance
- Review consumer group configuration
- Scale consumers if needed

## Validation Checklist

After making changes to this service:
- [ ] NATS subscriptions active (check connection to nats-1, nats-2, nats-3)
- [ ] Kafka consumer group balanced (check partition assignment)
- [ ] Data archived to ClickHouse (query historical_* tables)
- [ ] DragonflyDB cache working (check deduplication logs, DBSIZE)
- [ ] No data loss (compare live vs historical counts)
- [ ] Batch writes completing successfully (check logs)
- [ ] No duplicates in ClickHouse (verify deduplication)
- [ ] ConfigClient fetching from Central Hub
- [ ] Hot-reload responding to config updates

## Related Skills

- `central-hub` - Provides operational config and service discovery
- `polygon-live-collector` - Provides NATS ticks and Kafka archives
- `tick-aggregator` - Provides NATS candles and Kafka archives
- `external-data-collector` - Provides external data streams
- `feature-engineering` - Reads historical data from ClickHouse

## References

- Full Documentation: `docs/SERVICE_ARCHITECTURE_AND_FLOW.md` (lines 371-393)
- Planning Guide: `docs/PLANNING_SKILL_GUIDE.md` (Service 5, lines 852-1050)
- Flow + Messaging: `docs/SERVICE_FLOW_TREE_WITH_MESSAGING.md` (lines 167-223)
- Database Schema: `docs/table_database_input.md` (historical_* tables)
- Config Architecture: `docs/CONFIG_ARCHITECTURE.md`
- Central Hub Skill: `.claude/skills/central-hub/SKILL.md`
- Code: `02-data-processing/data-bridge/`

---

**Created:** 2025-10-19
**Version:** 2.0.0
**Status:** Production Ready
