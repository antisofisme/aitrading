# Skill: tick-aggregator Service

## Purpose
Aggregate raw ticks into OHLCV candles for 7 timeframes (5m, 15m, 30m, 1h, 4h, 1d, 1w). Runs on cron schedule.

## Key Facts
- **Phase**: Data Foundation (Phase 1)
- **Status**: ✅ Active, Production
- **Priority**: P0 (Critical - ML features depend on this)
- **Timeframes**: 7 (5m, 15m, 30m, 1h, 4h, 1d, 1w)
- **Schedule**: Cron-based (every 5min, 15min, hourly, etc.)

## Data Flow
```
TimescaleDB.live_ticks (read) + ClickHouse.historical_ticks (batch)
  → tick-aggregator (aggregate ticks → OHLCV)
  → ClickHouse.live_aggregates (7-day retention)
  → ClickHouse.historical_aggregates (unlimited)
  → NATS: bars.{symbol}.{timeframe} (real-time)
  → Kafka: aggregate_archive (persistence)
```

## Messaging
- **NATS Publish**: `bars.EURUSD.5m`, `bars.XAUUSD.1h`, etc. (real-time candles)
- **Kafka Publish**: `aggregate_archive` topic (archival for replay)
- **Pattern**: Both NATS + Kafka (critical data needs real-time + archive)

## Dependencies
- **Upstream**: polygon-live-collector (ticks via TimescaleDB)
- **Downstream**:
  - feature-engineering-service (subscribes to `bars.*` via NATS)
  - data-bridge (archives to ClickHouse via Kafka)
- **Infrastructure**: TimescaleDB, ClickHouse, NATS cluster, Kafka

## Critical Rules
1. **NEVER** skip aggregation windows (missing candles = incomplete ML features)
2. **ALWAYS** publish to NATS immediately (feature-engineering waits for this)
3. **ENSURE** lookback windows catch late-arriving ticks (buffer strategy)
4. **VERIFY** both live_aggregates (7-day) and historical_aggregates (unlimited)
5. **VALIDATE** OHLC integrity (open <= high, low <= close, no NULLs)

## Common Tasks
- **Add timeframe**: Update `config/aggregator.yaml` → Add cron schedule → Test
- **Fix missing candles**: Check late-arriving ticks, verify lookback window
- **Debug gaps**: Query ClickHouse for candle counts, check cron execution

## Validation
When working on this service, ALWAYS verify:
- [ ] Candles exist in ClickHouse (both live + historical tables)
- [ ] NATS publishes `bars.*.*` subjects (check feature-engineering receives)
- [ ] Kafka archives to `aggregate_archive` topic
- [ ] All 7 timeframes active (5m, 15m, 30m, 1h, 4h, 1d, 1w)
- [ ] No NULL values in OHLC (open, high, low, close all non-NULL)

## Reference Docs

**Service Documentation:**
- Planning guide: `PLANNING_SKILL_GUIDE.md` (Service 6, lines 810-1050)
- Architecture: `SERVICE_ARCHITECTURE_AND_FLOW.md` (lines 396-418)
- Flow + messaging: `SERVICE_FLOW_TREE_WITH_MESSAGING.md` (lines 251-308)
- Database schema: `table_database_input.md` (aggregates table)

**Operational Skills (Central-Hub Agent Tools):**
- 🔍 Debug issues: `.claude/skills/central-hub-debugger/`
- 🔧 Fix problems: `.claude/skills/central-hub-fixer/`
- ➕ Create new service: `.claude/skills/central-hub-service-creator/`
