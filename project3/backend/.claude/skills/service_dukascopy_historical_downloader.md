# Skill: dukascopy-historical-downloader Service

## Purpose
Bulk historical data downloader from Dukascopy API for 2+ years of tick data. One-time/periodic downloads for training data.

## Key Facts
- **Phase**: Data Foundation (Phase 1)
- **Status**: ✅ Active, Production
- **Priority**: P1 (Important - training data source)
- **Mode**: Batch processing (one-time or periodic)
- **Range**: 2+ years (2023-01-01 to present)

## Data Flow
```
Dukascopy API (2+ years historical ticks)
  → dukascopy-historical-downloader (download, decompress, convert)
  → ClickHouse.historical_ticks (direct write, unlimited retention)
  → NO messaging (batch mode only)
```

## Messaging
- **NATS**: None (batch processing, no streaming)
- **Kafka**: None (writes directly to ClickHouse)
- **Pattern**: Batch-only service (bulk downloads)

## Dependencies
- **Upstream**: Dukascopy API
- **Downstream**: tick-aggregator (reads historical_ticks for batch aggregation)
- **Infrastructure**: ClickHouse only

## Critical Rules
1. **NEVER** overlap with polygon-historical (dukascopy = old data, polygon = recent gaps)
2. **ALWAYS** decompress .bi5 files correctly (Dukascopy proprietary format)
3. **VERIFY** date range avoids duplicate downloads (check existing data first)
4. **ENSURE** data quality validation (no NULL prices, valid timestamps)
5. **RESPECT** download limits (avoid hammering Dukascopy servers)

## Common Tasks
- **Download new period**: Update date range → Run downloader → Verify data in ClickHouse
- **Fix corrupted data**: Re-download specific date range → Validate decompression
- **Debug missing ticks**: Check Dukascopy availability, verify .bi5 file format

## Data Format
- **Source format**: .bi5 (Dukascopy binary format)
- **Conversion**: .bi5 → tick records (timestamp, bid, ask, spread)
- **Validation**: Check for NULL values, timestamp ordering, price sanity

## Validation
When working on this service, ALWAYS verify:
- [ ] .bi5 files downloaded successfully
- [ ] Decompression works (no format errors)
- [ ] Data written to historical_ticks (query ClickHouse)
- [ ] Tick counts match expected (no missing days)
- [ ] No duplicate data (check date range overlaps)

## Reference Docs
- Planning guide: `PLANNING_SKILL_GUIDE.md` (Service 3, lines 452-650)
- Architecture: `SERVICE_ARCHITECTURE_AND_FLOW.md` (lines 322-337)
- Flow + messaging: `SERVICE_FLOW_TREE_WITH_MESSAGING.md` (lines 107-127)
- Database schema: `table_database_input.md` (historical_ticks table)
