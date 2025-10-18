# Skill: polygon-live-collector Service

## Purpose
Real-time tick data collector from Polygon.io WebSocket API. Streams live forex/gold ticks to TimescaleDB + NATS + Kafka.

## Key Facts
- **Phase**: Data Foundation (Phase 1)
- **Status**: ✅ Active, Production
- **Priority**: P0 (Critical - system won't work without it)
- **Symbols**: 14 trading pairs (EURUSD, XAUUSD, GBPUSD, etc.)

## Data Flow
```
Polygon.io WebSocket
  → polygon-live-collector (normalize/validate)
  → TimescaleDB.market_ticks (3-day retention)
  → NATS: ticks.{symbol} (real-time)
  → Kafka: tick_archive (persistence)
```

## Messaging
- **NATS Publish**: `ticks.EURUSD`, `ticks.XAUUSD`, etc. (real-time streaming)
- **Kafka Publish**: `tick_archive` topic (archival, replay capability)
- **Pattern**: Both NATS + Kafka (critical data needs real-time + archive)

## Dependencies
- **Upstream**: Polygon.io WebSocket API
- **Downstream**: data-bridge (consumes NATS + Kafka)
- **Infrastructure**: TimescaleDB, NATS cluster (3 nodes), Kafka

## Critical Rules
1. **NEVER** skip NATS publishing (data-bridge needs real-time stream)
2. **ALWAYS** publish to both NATS + Kafka (archive is mandatory)
3. **VERIFY** 3-day retention policy on TimescaleDB (prevent disk overflow)
4. **RESPECT** Polygon.io rate limits (5 req/sec)
5. **ENSURE** reconnection logic handles WebSocket disconnects

## Common Tasks
- **Add new pair**: Update `config/collector.yaml` → Test WebSocket subscription
- **Fix gaps**: Check polygon-historical-downloader for backfill
- **Debug**: Check logs for "Connected to Polygon.io", verify tick counts in DB

## Validation
When working on this service, ALWAYS verify:
- [ ] Ticks flowing to TimescaleDB (query `market_ticks` table)
- [ ] NATS publishing works (check data-bridge receives messages)
- [ ] Kafka archiving works (check `tick_archive` topic)
- [ ] All 14 pairs active (no missing symbols)

## Reference Docs
- Planning guide: `PLANNING_SKILL_GUIDE.md` (Service 1, lines 70-250)
- Architecture: `SERVICE_ARCHITECTURE_AND_FLOW.md` (lines 276-298)
- Flow + messaging: `SERVICE_FLOW_TREE_WITH_MESSAGING.md` (lines 35-80)
- Database schema: `table_database_input.md` (market_ticks table)
