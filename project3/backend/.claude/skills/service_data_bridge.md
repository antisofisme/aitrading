# Skill: data-bridge Service

## Purpose
Data routing hub that consumes from NATS + Kafka and archives to ClickHouse. Handles deduplication and batch writes.

## Key Facts
- **Phase**: Data Foundation (Phase 1)
- **Status**: ✅ Active, Production
- **Priority**: P0 (Critical - archives live data to permanent storage)
- **Pattern**: Multi-source consumer (NATS + Kafka) → ClickHouse writer
- **Deduplication**: DragonflyDB cache (1-hour TTL)

## Data Flow
```
NATS: Subscribe ticks.>, bars.>, external.> (real-time)
Kafka: Consume tick_archive, aggregate_archive (backup)
TimescaleDB.live_ticks (read for archiving after 3 days)
  → data-bridge (route, deduplicate, batch write)
  → ClickHouse.historical_ticks (archive)
  → ClickHouse.historical_aggregates (archive)
  → DragonflyDB (deduplication cache)
```

## Messaging
- **NATS Subscribe**: `ticks.>`, `bars.>`, `market.external.>` (all streams)
- **Kafka Consume**: `tick_archive`, `aggregate_archive`, `external_data_archive`
- **Pattern**: Hub consumer (subscribes from multiple sources)
- **Consumer Group**: `data-bridge-group` (load balancing across instances)

## Dependencies
- **Upstream**:
  - polygon-live-collector (NATS ticks, Kafka tick_archive)
  - tick-aggregator (NATS bars, Kafka aggregate_archive)
  - external-data-collector (NATS external, Kafka external_archive)
- **Downstream**: ClickHouse (writes historical data)
- **Infrastructure**: NATS cluster, Kafka, ClickHouse, DragonflyDB

## Critical Rules
1. **NEVER** skip deduplication (check DragonflyDB cache before insert)
2. **ALWAYS** use batch writes to ClickHouse (performance optimization)
3. **VERIFY** both NATS + Kafka consumption (dual path redundancy)
4. **ENSURE** TimescaleDB archival before 3-day expiration
5. **VALIDATE** no data loss during archival (compare counts)

## Deduplication Strategy
- **Cache**: DragonflyDB (Redis-compatible)
- **Key format**: `{symbol}:{timestamp}:{data_type}`
- **TTL**: 1 hour (prevent duplicate inserts within window)
- **LRU size**: 10,000 entries max

## Validation
When working on this service, ALWAYS verify:
- [ ] NATS subscriptions active (check connection to nats-1, nats-2, nats-3)
- [ ] Kafka consumer group balanced (check partition assignment)
- [ ] Data archived to ClickHouse (query historical_* tables)
- [ ] DragonflyDB cache working (check deduplication logs)
- [ ] No data loss (compare live vs historical counts)

## Reference Docs
- Planning guide: `PLANNING_SKILL_GUIDE.md` (Service 5, lines 852-1050)
- Architecture: `SERVICE_ARCHITECTURE_AND_FLOW.md` (lines 371-393)
- Flow + messaging: `SERVICE_FLOW_TREE_WITH_MESSAGING.md` (lines 167-223)
- Database schema: `table_database_input.md` (historical_* tables)
