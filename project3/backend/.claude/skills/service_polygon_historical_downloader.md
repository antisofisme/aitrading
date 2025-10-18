# Skill: polygon-historical-downloader Service

## Purpose
Gap filling service for recent historical data from Polygon.io REST API. Detects gaps in live_aggregates and backfills missing candles.

## Key Facts
- **Phase**: Data Foundation (Phase 1)
- **Status**: ✅ Active, Production
- **Priority**: P0 (Critical - gap filling prevents incomplete data)
- **Mode**: Scheduled batch processing (hourly, daily, weekly checks)
- **Range**: Recent 7 days (matches live_aggregates retention)

## Data Flow
```
Polygon.io REST API (recent historical data)
  → polygon-historical-downloader (gap detection, download, backfill)
  → ClickHouse.live_aggregates (direct write, fill gaps)
  → NO messaging (batch mode only)
```

## Messaging
- **NATS**: None (batch processing, no real-time streaming)
- **Kafka**: None (writes directly to ClickHouse)
- **Pattern**: Batch-only service (scheduled gap filling)

## Dependencies
- **Upstream**: Polygon.io REST API
- **Downstream**: None (writes directly to ClickHouse)
- **Reads from**: ClickHouse.live_aggregates (gap detection)
- **Infrastructure**: ClickHouse only

## Critical Rules
1. **NEVER** overlap with dukascopy-historical (polygon = recent gaps, dukascopy = old data)
2. **ALWAYS** check for gaps before downloading (don't duplicate data)
3. **VERIFY** date range stays within 7 days (live_aggregates retention)
4. **RESPECT** Polygon.io rate limits (5 req/sec)
5. **ENSURE** gap detection uses completeness thresholds (100% for intraday)

## Common Tasks
- **Fix gaps**: Check logs for detected gaps → Verify backfill success
- **Add timeframe**: Update `config/schedule.yaml` → Add gap detection rules
- **Debug missing data**: Query ClickHouse for completeness, check Polygon API response

## Gap Detection Strategy
- **Intraday (5m, 15m, 30m, 1h, 4h)**: 100% threshold (ANY missing = gap)
- **Daily+ (1d, 1w)**: 80% threshold (weekends/holidays tolerated)
- **Check period**: Last 7 days (live_aggregates retention window)

## Validation
When working on this service, ALWAYS verify:
- [ ] Gaps detected correctly (check gap_detector.py logs)
- [ ] Backfill completes successfully (no errors in logs)
- [ ] Data written to live_aggregates (query ClickHouse)
- [ ] No duplicate data (check deduplication logic)
- [ ] Schedule runs as expected (cron: hourly, daily, weekly)

## Reference Docs
- Planning guide: `PLANNING_SKILL_GUIDE.md` (Service 2, lines 252-450)
- Architecture: `SERVICE_ARCHITECTURE_AND_FLOW.md` (lines 301-319)
- Flow + messaging: `SERVICE_FLOW_TREE_WITH_MESSAGING.md` (lines 82-105)
- Database schema: `table_database_input.md` (live_aggregates table)
