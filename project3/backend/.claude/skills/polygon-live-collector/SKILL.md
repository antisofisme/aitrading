---
name: polygon-live-collector
description: Real-time tick data collector from Polygon.io WebSocket API. Streams live forex/gold ticks to TimescaleDB, NATS, and Kafka with 3-day retention.
license: MIT
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
metadata:
  type: Data Ingestion
  phase: Data Foundation (Phase 1)
  status: Active Production
  priority: P0 (Critical)
  port: 8000
  dependencies:
    - central-hub
    - timescaledb
    - nats
    - kafka
  version: 2.0.0
---

# Polygon Live Collector Service

Real-time tick data collector from Polygon.io WebSocket API. Streams live forex/gold ticks to TimescaleDB with 3-day retention, publishes to NATS for real-time streaming, and archives to Kafka for replay capability.

## When to Use This Skill

Use this skill when:
- Working on Polygon.io live data collection
- Adding new trading pairs to real-time stream
- Debugging WebSocket connection issues
- Fixing tick data gaps in real-time stream
- Configuring retention policies
- Verifying NATS/Kafka messaging integration

## Service Overview

**Type:** Data Ingestion (Real-time WebSocket)
**Port:** 8000
**Data Source:** Polygon.io WebSocket API
**Storage:** TimescaleDB (`market_ticks` table, 3-day retention)
**Messaging:** NATS (real-time) + Kafka (archival)
**Symbols:** 14 trading pairs (EURUSD, XAUUSD, GBPUSD, USDJPY, AUDUSD, etc.)

**Dependencies:**
- **Upstream**: Polygon.io WebSocket API
- **Downstream**: data-bridge (consumes NATS + Kafka)
- **Infrastructure**: TimescaleDB, NATS cluster (3 nodes), Kafka

## Key Capabilities

- Real-time WebSocket data collection from Polygon.io
- Tick normalization and validation
- 3-day rolling retention in TimescaleDB
- Real-time NATS publishing (`ticks.{symbol}`)
- Kafka archival (`tick_archive` topic)
- Automatic WebSocket reconnection
- Rate limit handling (5 req/sec)

## Architecture

### Data Flow

```
Polygon.io WebSocket
  ↓
polygon-live-collector (normalize/validate)
  ↓
├─→ TimescaleDB.market_ticks (3-day retention)
├─→ NATS: ticks.{symbol} (real-time streaming)
└─→ Kafka: tick_archive (persistence)
```

### Messaging Pattern

**NATS Publishing:**
- Topic: `ticks.EURUSD`, `ticks.XAUUSD`, etc.
- Purpose: Real-time streaming for downstream consumers
- Consumers: data-bridge, feature-engineering

**Kafka Publishing:**
- Topic: `tick_archive`
- Purpose: Archival and replay capability
- Retention: Indefinite (for historical analysis)

### Configuration

**Operational Config (Central Hub):**
```json
{
  "operational": {
    "symbols": [
      "EURUSD", "XAUUSD", "GBPUSD", "USDJPY",
      "AUDUSD", "USDCAD", "NZDUSD", "EURGBP",
      "EURJPY", "GBPJPY", "AUDJPY", "NZDJPY",
      "USDCHF", "XAGUSD"
    ],
    "websocket_reconnect_delay": 5,
    "rate_limit_per_second": 5
  }
}
```

**Environment Variables (Secrets):**
```bash
POLYGON_API_KEY=your_api_key_here  # NEVER hardcode!
```

## Examples

### Example 1: Fetch Config from Central Hub

```python
from shared.components.config import ConfigClient

# Initialize client
client = ConfigClient(
    service_name="polygon-live-collector",
    safe_defaults={
        "operational": {
            "symbols": ["EURUSD", "XAUUSD"],
            "websocket_reconnect_delay": 5,
            "rate_limit_per_second": 5
        }
    }
)
await client.init_async()

# Get config
config = await client.get_config()
symbols = config['operational']['symbols']
print(f"Collecting {len(symbols)} symbols: {symbols}")
```

### Example 2: Connect to Polygon.io WebSocket

```python
from polygon_collector import PolygonLiveCollector

collector = PolygonLiveCollector()
await collector.connect_websocket(symbols=["EURUSD", "XAUUSD"])

# Collector will automatically:
# 1. Normalize tick data
# 2. Insert to TimescaleDB
# 3. Publish to NATS (ticks.EURUSD)
# 4. Archive to Kafka (tick_archive)
```

### Example 3: Add New Trading Pair

```bash
# Update config via Central Hub API
curl -X POST http://suho-central-hub:7000/api/v1/config/polygon-live-collector \
  -H "Content-Type: application/json" \
  -d '{
    "operational": {
      "symbols": ["EURUSD", "XAUUSD", "GBPUSD", "EURAUD"]
    }
  }'

# Hot-reload will automatically pick up new symbol
```

### Example 4: Query Live Ticks from TimescaleDB

```sql
-- Check recent ticks
SELECT
    symbol,
    COUNT(*) as tick_count,
    MIN(timestamp_ms) as oldest_tick,
    MAX(timestamp_ms) as newest_tick
FROM market_ticks
WHERE timestamp_ms > (EXTRACT(EPOCH FROM NOW()) * 1000 - 3600000)  -- Last hour
GROUP BY symbol
ORDER BY tick_count DESC;
```

## Guidelines

- **ALWAYS** use ConfigClient for operational settings (symbols, reconnect delay)
- **NEVER** hardcode API keys (use ENV vars: `POLYGON_API_KEY`)
- **USE** safe defaults in ConfigClient (fallback when Hub unavailable)
- **ENABLE** hot-reload for zero-downtime config updates
- **MONITOR** 3-day retention policy (prevent disk overflow)
- **RESPECT** Polygon.io rate limits (5 req/sec)

## Critical Rules

1. **Config Hierarchy:**
   - API keys → ENV variables (`POLYGON_API_KEY`)
   - Symbols, intervals → Central Hub (operational config)
   - Safe defaults → ConfigClient fallback

2. **Messaging (BOTH NATS + Kafka):**
   - **NEVER** skip NATS publishing (data-bridge needs real-time stream)
   - **ALWAYS** publish to both NATS + Kafka (archive is mandatory)
   - **VERIFY** messages flowing to both systems

3. **Data Integrity:**
   - **VERIFY** 3-day retention policy active
   - **ENSURE** tick validation before insertion
   - **HANDLE** WebSocket disconnects gracefully (auto-reconnect)

4. **Rate Limits:**
   - **RESPECT** Polygon.io limits (5 req/sec)
   - **IMPLEMENT** exponential backoff on errors
   - **LOG** rate limit violations

## Common Tasks

### Add New Trading Pair
1. Update config via Central Hub API (add symbol to `symbols` array)
2. Hot-reload will automatically subscribe to new WebSocket stream
3. Verify ticks flowing to TimescaleDB and NATS

### Fix Data Gaps
1. Check WebSocket connection logs
2. Verify Polygon.io API key is valid
3. Use polygon-historical-downloader for backfill (gaps in historical data)
4. Check NATS/Kafka for dropped messages

### Debug Collection Issues
1. Check logs for "Connected to Polygon.io" message
2. Query TimescaleDB for recent tick counts per symbol
3. Verify NATS publishing: `nats sub "ticks.*"`
4. Check Kafka consumer for `tick_archive` topic

## Troubleshooting

### Issue 1: WebSocket Disconnects Frequently
**Symptoms:** Logs show repeated reconnection attempts
**Solution:**
- Check network connectivity to Polygon.io
- Verify API key is valid
- Increase `websocket_reconnect_delay` in config
- Check rate limit violations in logs

### Issue 2: Missing Ticks for Some Symbols
**Symptoms:** Some symbols have no recent ticks
**Solution:**
- Verify symbol is in config's `symbols` array
- Check Polygon.io subscription status
- Ensure symbol is actively traded (market hours)
- Use historical downloader to backfill gaps

### Issue 3: TimescaleDB Disk Full
**Symptoms:** Insert errors, disk space warnings
**Solution:**
- Verify 3-day retention policy is active
- Check compression settings
- Manually clean old data if needed
- Monitor disk usage (set alerts)

### Issue 4: NATS/Kafka Not Receiving Messages
**Symptoms:** Downstream services report missing data
**Solution:**
- Check NATS cluster health
- Verify Kafka broker connectivity
- Review publishing logs for errors
- Test with `nats sub` and `kafka-console-consumer`

## Validation Checklist

After making changes to this service:
- [ ] Ticks flowing to TimescaleDB (query `market_ticks` table)
- [ ] NATS publishing works (check data-bridge receives messages)
- [ ] Kafka archiving works (check `tick_archive` topic)
- [ ] All 14 pairs active (no missing symbols)
- [ ] WebSocket connection stable (no frequent disconnects)
- [ ] 3-day retention policy active
- [ ] No rate limit violations in logs
- [ ] ConfigClient fetching from Central Hub
- [ ] Hot-reload responding to config updates

## Related Skills

- `central-hub` - Provides operational config and service discovery
- `polygon-historical-downloader` - Backfills historical gaps
- `data-bridge` - Consumes NATS + Kafka messages
- `tick-aggregator` - Aggregates ticks into OHLCV candles
- `feature-engineering` - Consumes real-time tick stream

## References

- Full Documentation: `docs/SERVICE_ARCHITECTURE_AND_FLOW.md` (lines 276-298)
- Planning Guide: `docs/PLANNING_SKILL_GUIDE.md` (Service 1, lines 70-250)
- Database Schema: `docs/table_database_input.md` (market_ticks table)
- Flow + Messaging: `docs/SERVICE_FLOW_TREE_WITH_MESSAGING.md` (lines 35-80)
- Config Architecture: `docs/CONFIG_ARCHITECTURE.md`
- Central Hub Skill: `.claude/skills/central-hub/SKILL.md`
- Code: `00-data-ingestion/polygon-live-collector/`

---

**Created:** 2025-10-19
**Version:** 2.0.0
**Status:** Production Ready
