# Data Bridge Scaling Validation Guide

## Overview

This document provides validation steps for the data-bridge multi-instance scaling implementation (Issue #26).

**Implementation Date:** 2025-10-12
**Instances:** 3 replicas for load balancing
**Throughput Goal:** Support 50k+ msg/sec with automatic failover

---

## Pre-Deployment Checklist

### 1. Verify Kafka Topic Partitions

Kafka topics must have sufficient partitions for load distribution:

```bash
# Check partition count for each topic
docker exec suho-kafka kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic tick_archive
docker exec suho-kafka kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic aggregate_archive
docker exec suho-kafka kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic confirmation_archive
```

**Expected:** Each topic should have **6 partitions** (configured in docker-compose.yml: `KAFKA_NUM_PARTITIONS: 6`)

**Why 6 partitions?**
- 3 instances × 2 partitions = balanced load
- Allows scaling to 6 instances if needed
- Better than 3 (no room for growth) or 12 (over-partitioned)

### 2. Verify ClickHouse Idempotency

Data-bridge uses ClickHouse ReplacingMergeTree which deduplicates based on primary key:

```sql
-- Check table engine for aggregates table
SELECT
    database,
    name,
    engine,
    engine_full
FROM system.tables
WHERE database = 'suho_analytics' AND name = 'aggregates';

-- Expected: ReplacingMergeTree engine
```

**Result:** Should show `ReplacingMergeTree` engine with ORDER BY clause.

---

## Deployment Steps

### 1. Scale to 3 Instances

```bash
cd /mnt/g/khoirul/aitrading/project3/backend/02-data-processing/data-bridge
./scripts/scale_instances.sh 3
```

**Expected Output:**
```
⚡ Scaling data-bridge to 3 instances...
✓ suho-data-bridge-1: Up 10 seconds (healthy)
✓ suho-data-bridge-2: Up 10 seconds (healthy)
✓ suho-data-bridge-3: Up 10 seconds (healthy)
```

### 2. Verify Instances are Running

```bash
# Check all instances
docker ps --filter "name=data-bridge" --format "{{.Names}}: {{.Status}}"

# Check health status
docker-compose ps data-bridge
```

**Expected:** All 3 instances should show "Up" and "healthy" status.

### 3. Verify Instance Identification

Check logs to confirm each instance has unique ID:

```bash
# Check instance 1
docker logs suho-data-bridge-1 2>&1 | grep "Instance ID"

# Check instance 2
docker logs suho-data-bridge-2 2>&1 | grep "Instance ID"

# Check instance 3
docker logs suho-data-bridge-3 2>&1 | grep "Instance ID"
```

**Expected Output:**
```
🆔 Instance ID: suho-data-bridge-1 (#1)
🆔 Instance ID: suho-data-bridge-2 (#2)
🆔 Instance ID: suho-data-bridge-3 (#3)
```

---

## Validation Tests

### Test 1: Kafka Partition Assignment

Verify Kafka distributes partitions across all 3 instances:

```bash
# Check consumer group assignment
docker exec suho-kafka kafka-consumer-groups.sh \
    --bootstrap-server localhost:9092 \
    --describe \
    --group data-bridge-group
```

**Expected Output:**
```
GROUP             TOPIC           PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG  CONSUMER-ID                    HOST
data-bridge-group tick_archive    0          1234            1234            0    consumer-1-abc123              /172.20.0.5
data-bridge-group tick_archive    1          5678            5678            0    consumer-1-abc123              /172.20.0.5
data-bridge-group tick_archive    2          9012            9012            0    consumer-2-def456              /172.20.0.6
data-bridge-group tick_archive    3          3456            3456            0    consumer-2-def456              /172.20.0.6
data-bridge-group tick_archive    4          7890            7890            0    consumer-3-ghi789              /172.20.0.7
data-bridge-group tick_archive    5          1234            1234            0    consumer-3-ghi789              /172.20.0.7
```

**Validation:**
- ✅ Each instance gets **2 partitions** (6 partitions ÷ 3 instances)
- ✅ LAG is 0 or low (< 1000 messages)
- ✅ All partitions have assigned consumers

### Test 2: Message Distribution

Monitor message counts per instance:

```bash
# Watch logs for all instances (30 seconds)
docker-compose logs -f data-bridge | grep "messages received"
```

**Expected Behavior:**
- Each instance receives **~33%** of total messages
- Message rate is roughly equal across instances
- No instance is idle or overloaded

**Example:**
```
data-bridge-1 | 📈 Kafka received 10000 messages (ticks: 8000, agg: 2000, ext: 0)
data-bridge-2 | 📈 Kafka received 10500 messages (ticks: 8200, agg: 2300, ext: 0)
data-bridge-3 | 📈 Kafka received 9800 messages (ticks: 7900, agg: 1900, ext: 0)
```

### Test 3: Heartbeat Metrics

Check Central Hub for per-instance metrics:

```bash
# Check Central Hub logs for heartbeat reports
docker logs suho-central-hub 2>&1 | grep "data-bridge" | tail -20
```

**Expected Output:**
```
[INFO] Heartbeat from data-bridge-1: ticks=5000, ch_candles=2000, nats_msgs=7000
[INFO] Heartbeat from data-bridge-2: ticks=5200, ch_candles=2100, nats_msgs=7300
[INFO] Heartbeat from data-bridge-3: ticks=4900, ch_candles=1950, nats_msgs=6850
```

**Validation:**
- ✅ All 3 instances report metrics independently
- ✅ Metrics show balanced load distribution
- ✅ No instance is significantly behind

### Test 4: Failover Test

Test automatic rebalancing when one instance fails:

```bash
# 1. Check initial state
docker exec suho-kafka kafka-consumer-groups.sh \
    --bootstrap-server localhost:9092 \
    --describe \
    --group data-bridge-group

# 2. Stop instance 2
docker stop suho-data-bridge-2

# 3. Wait 30 seconds for rebalance
sleep 30

# 4. Check partition reassignment
docker exec suho-kafka kafka-consumer-groups.sh \
    --bootstrap-server localhost:9092 \
    --describe \
    --group data-bridge-group
```

**Expected Behavior:**
- ✅ Kafka detects instance 2 is down (after session_timeout_ms: 30s)
- ✅ Partitions 2 and 3 are **redistributed** to instances 1 and 3
- ✅ Instance 1 and 3 now handle **3 partitions each** (instead of 2)
- ✅ No message loss (LAG increases temporarily, then recovers)

**Recovery Test:**
```bash
# Restart instance 2
docker start suho-data-bridge-2

# Wait for rejoin
sleep 30

# Verify rebalance back to 2 partitions per instance
docker exec suho-kafka kafka-consumer-groups.sh \
    --bootstrap-server localhost:9092 \
    --describe \
    --group data-bridge-group
```

**Expected:** Partitions redistribute back to 2 per instance.

### Test 5: Duplicate Prevention

Verify ClickHouse ReplacingMergeTree prevents duplicates:

```sql
-- Insert test data twice with same timestamp/symbol (simulate duplicate from 2 instances)
INSERT INTO suho_analytics.aggregates
(symbol, timeframe, timestamp_ms, open, high, low, close, volume) VALUES
('EURUSD', '5m', 1697000000000, 1.0500, 1.0520, 1.0490, 1.0510, 1000);

INSERT INTO suho_analytics.aggregates
(symbol, timeframe, timestamp_ms, open, high, low, close, volume) VALUES
('EURUSD', '5m', 1697000000000, 1.0500, 1.0520, 1.0490, 1.0510, 1000);

-- Wait for merge (5-10 seconds)
SELECT sleep(10);

-- Query should return ONLY 1 row (duplicate removed)
SELECT * FROM suho_analytics.aggregates
WHERE symbol = 'EURUSD'
  AND timeframe = '5m'
  AND timestamp_ms = 1697000000000;
```

**Expected Result:** Only **1 row** returned (not 2).

### Test 6: Backpressure Coordination

Verify backpressure mechanism works across all instances:

```bash
# Simulate high load (send 100k messages)
# Then monitor pause/resume behavior

docker-compose logs -f data-bridge | grep -E "BACKPRESSURE|paused|resumed"
```

**Expected Behavior:**
- ✅ When buffer reaches **40k (80%)**, all instances pause consumption
- ✅ When buffer drops to **20k (40%)**, instances resume
- ✅ Logs show coordinated pause/resume across instances

---

## Performance Benchmarks

### Target Metrics

| Metric | Target | Method |
|--------|--------|--------|
| Total Throughput | 50,000 msg/sec | 3 instances × ~17k msg/sec each |
| Per-Instance Load | 17,000 msg/sec | Kafka partition distribution |
| Latency (p99) | < 100ms | NATS → ClickHouse write time |
| Failover Time | < 30 seconds | Kafka session timeout |
| Zero Data Loss | 100% | ReplacingMergeTree + Kafka retention |

### Load Test Command

```bash
# Send 100k test messages to NATS
python3 /mnt/g/khoirul/aitrading/project3/backend/00-data-ingestion/polygon-live-collector/tests/load_test.py \
    --messages 100000 \
    --rate 50000

# Monitor processing rate
docker-compose logs -f data-bridge | grep "messages received"
```

**Expected:** All 100k messages processed within **2-3 seconds** (50k msg/sec).

---

## Monitoring Dashboard Queries

### Query 1: Per-Instance Message Count

```bash
# Get message counts from logs
docker-compose logs data-bridge | grep "Kafka received" | \
    awk -F'|' '{print $3}' | \
    awk '{s[$1]+=$3} END {for (i in s) print i, s[i]}'
```

### Query 2: Consumer Lag by Partition

```bash
docker exec suho-kafka kafka-consumer-groups.sh \
    --bootstrap-server localhost:9092 \
    --describe \
    --group data-bridge-group | \
    awk '{if (NR>1) sum+=$6; print} END {print "Total LAG:", sum}'
```

### Query 3: Backpressure Events

```bash
# Count pause/resume events
docker-compose logs data-bridge | grep -c "BACKPRESSURE ACTIVE"
docker-compose logs data-bridge | grep -c "BACKPRESSURE RELEASED"
```

---

## Rollback Plan

If issues occur, rollback to single instance:

```bash
# Scale back to 1 instance
docker-compose up -d --scale data-bridge=1 --no-recreate

# Or revert to single container mode
docker-compose stop data-bridge
docker-compose rm -f data-bridge

# Restore original docker-compose.yml (before replicas config)
git checkout docker-compose.yml

# Restart
docker-compose up -d data-bridge
```

---

## Common Issues and Solutions

### Issue 1: Uneven Partition Distribution

**Symptom:** One instance gets 4+ partitions, others get 1-2

**Solution:**
```bash
# Force rebalance by restarting all instances
docker-compose restart data-bridge
```

### Issue 2: Consumer Group Stuck in "Dead" State

**Symptom:** `kafka-consumer-groups.sh` shows no active consumers

**Solution:**
```bash
# Reset consumer group offsets
docker exec suho-kafka kafka-consumer-groups.sh \
    --bootstrap-server localhost:9092 \
    --group data-bridge-group \
    --reset-offsets \
    --to-latest \
    --all-topics \
    --execute

# Restart instances
docker-compose restart data-bridge
```

### Issue 3: High LAG Across All Instances

**Symptom:** LAG > 10,000 messages per partition

**Root Cause:** ClickHouse write bottleneck (slow writes)

**Solution:**
```bash
# Check ClickHouse performance
docker exec suho-clickhouse clickhouse-client --query "
    SELECT
        event_time,
        query_duration_ms,
        query
    FROM system.query_log
    WHERE query LIKE '%INSERT INTO%'
    ORDER BY event_time DESC
    LIMIT 10"

# If writes are slow (> 500ms), increase batch size
# Edit: /mnt/g/khoirul/aitrading/project3/backend/02-data-processing/data-bridge/src/main.py
# Change: batch_size=1000 → batch_size=5000
```

---

## Success Criteria

The scaling implementation is successful if ALL criteria are met:

- ✅ **3 instances running** with unique IDs
- ✅ **Kafka partitions balanced** (2 per instance)
- ✅ **Load distribution ~33%** per instance
- ✅ **Failover time < 30 seconds** (automatic rebalancing)
- ✅ **Zero data loss** (ClickHouse ReplacingMergeTree)
- ✅ **No duplicate data** in ClickHouse
- ✅ **Backpressure coordinated** across instances
- ✅ **Heartbeat metrics** show per-instance stats
- ✅ **Total throughput ≥ 50k msg/sec**

---

## Next Steps

After successful validation:

1. **Monitor for 24 hours** - Watch for memory leaks, crashes, lag buildup
2. **Load test with production data** - Replay historical data at 100k msg/sec
3. **Document learnings** - Update runbook with observed behaviors
4. **Plan Phase 2** - Scale to 5 instances if throughput needs increase

---

**Document Version:** 1.0
**Last Updated:** 2025-10-12
**Author:** Claude Code (Backend API Developer)
