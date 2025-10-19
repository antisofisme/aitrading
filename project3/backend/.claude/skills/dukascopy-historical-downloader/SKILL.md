---
name: dukascopy-historical-downloader
description: Bulk historical data downloader from Dukascopy API for 2+ years of tick data. Handles proprietary .bi5 format decompression and writes directly to ClickHouse for training data.
license: MIT
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
metadata:
  type: Data Ingestion (Batch Historical)
  phase: Data Foundation (Phase 1)
  status: Active Production
  priority: P1 (Important - training data source)
  port: 8003
  dependencies:
    - central-hub
    - clickhouse
  version: 2.0.0
---

# Dukascopy Historical Downloader Service

Bulk historical data downloader from Dukascopy API for 2+ years of tick data. Downloads proprietary .bi5 format files, decompresses them, validates data quality, and writes directly to ClickHouse historical storage for ML training.

## When to Use This Skill

Use this skill when:
- Downloading bulk historical data (2+ years)
- Backfilling old tick data for training
- Working with Dukascopy .bi5 format files
- Debugging decompression or format issues
- Verifying historical data quality
- Avoiding duplicate downloads

## Service Overview

**Type:** Data Ingestion (Batch Historical)
**Port:** 8003
**Data Source:** Dukascopy API (.bi5 binary format)
**Storage:** ClickHouse (`historical_ticks` table, unlimited retention)
**Messaging:** None (batch mode only)
**Mode:** Batch processing (one-time or periodic)
**Date Range:** 2+ years (typically 2023-01-01 to present)

**Dependencies:**
- **Upstream**: Dukascopy API
- **Downstream**: tick-aggregator (reads historical_ticks for batch aggregation)
- **Infrastructure**: ClickHouse only

## Key Capabilities

- Bulk download of historical tick data (2+ years)
- .bi5 proprietary format decompression
- Data quality validation (NULL checks, timestamp ordering)
- Direct ClickHouse writing (unlimited retention)
- Gap detection (avoid duplicate downloads)
- Configurable date ranges
- Price sanity validation

## Architecture

### Data Flow

```
Dukascopy API
  ↓ (Download .bi5 files)
.bi5 Files (proprietary binary format)
  ↓ (Decompress)
Raw tick records (timestamp, bid, ask, spread)
  ↓ (Validate)
Validated ticks (no NULLs, valid timestamps)
  ↓ (Batch write)
ClickHouse.historical_ticks (unlimited retention)
```

**NO Messaging:**
- No NATS publishing (batch mode, not real-time)
- No Kafka archival (writes directly to ClickHouse)

### Data Format

**.bi5 Format (Dukascopy Proprietary):**
- Binary compressed format
- Contains: timestamp, bid price, ask price, bid volume, ask volume
- Compression: LZMA-based
- File naming: `{symbol}/{year}/{month}/{day}/{hour}.bi5`

**Conversion Process:**
1. Download .bi5 file from Dukascopy API
2. Decompress using LZMA decoder
3. Parse binary structure:
   - Timestamp (milliseconds since epoch)
   - Bid price (compressed delta encoding)
   - Ask price (compressed delta encoding)
   - Bid volume, Ask volume
4. Convert to standard tick format
5. Validate data quality
6. Write to ClickHouse

### Configuration

**Operational Config (Central Hub):**
```json
{
  "operational": {
    "symbols": ["EURUSD", "XAUUSD", "GBPUSD"],
    "date_range": {
      "start": "2023-01-01",
      "end": "2025-01-01"
    },
    "batch_size": 100,
    "enable_gap_detection": true,
    "validate_data_quality": true,
    "max_price_deviation": 0.1,
    "skip_existing": true
  }
}
```

## Examples

### Example 1: Fetch Config from Central Hub

```python
from shared.components.config import ConfigClient

# Initialize client
client = ConfigClient(
    service_name="dukascopy-historical-downloader",
    safe_defaults={
        "operational": {
            "batch_size": 100,
            "validate_data_quality": True
        }
    }
)
await client.init_async()

# Get config
config = await client.get_config()
symbols = config['operational']['symbols']
date_range = config['operational']['date_range']
print(f"Downloading {symbols} from {date_range['start']} to {date_range['end']}")
```

### Example 2: Download Historical Data

```python
from dukascopy_downloader import DukascopyDownloader

downloader = DukascopyDownloader()

# Download ticks for date range
await downloader.download_range(
    symbol="EURUSD",
    start_date="2023-01-01",
    end_date="2023-12-31"
)

# Process:
# 1. Check ClickHouse for existing data (skip if exists)
# 2. Download .bi5 files for each hour
# 3. Decompress and parse
# 4. Validate data quality
# 5. Batch write to ClickHouse
```

### Example 3: Decompress .bi5 File

```python
from dukascopy_downloader import decompress_bi5

# Download .bi5 file
bi5_file = await downloader.download_bi5(
    symbol="EURUSD",
    year=2023,
    month=1,
    day=15,
    hour=10
)

# Decompress
ticks = decompress_bi5(bi5_file)

# Result: List of tick dictionaries
# [
#   {"timestamp_ms": 1673780400000, "bid": 1.08123, "ask": 1.08126, ...},
#   {"timestamp_ms": 1673780400100, "bid": 1.08124, "ask": 1.08127, ...},
#   ...
# ]
```

### Example 4: Verify Historical Data in ClickHouse

```sql
-- Check data availability for EURUSD
SELECT
    symbol,
    COUNT(*) as tick_count,
    MIN(timestamp_ms) as oldest_tick,
    MAX(timestamp_ms) as newest_tick,
    ROUND((MAX(timestamp_ms) - MIN(timestamp_ms)) / 1000.0 / 86400.0, 2) as days_span
FROM historical_ticks
WHERE symbol = 'EURUSD'
GROUP BY symbol;

-- Find gaps in data
SELECT
    symbol,
    toDate(timestamp_ms / 1000) as date,
    COUNT(*) as tick_count
FROM historical_ticks
WHERE symbol = 'EURUSD'
  AND timestamp_ms BETWEEN 1672531200000 AND 1704067200000  -- 2023
GROUP BY symbol, date
ORDER BY date;
```

### Example 5: Update Download Configuration

```bash
# Add new symbol for download
curl -X POST http://suho-central-hub:7000/api/v1/config/dukascopy-historical-downloader \
  -H "Content-Type: application/json" \
  -d '{
    "operational": {
      "symbols": ["EURUSD", "XAUUSD", "GBPUSD", "USDJPY"],
      "date_range": {
        "start": "2022-01-01",
        "end": "2025-01-01"
      }
    }
  }'

# Hot-reload will pick up new symbols
```

## Guidelines

- **ALWAYS** use ConfigClient for operational settings (symbols, date ranges)
- **NEVER** overlap with polygon-historical (dukascopy = old data, polygon = recent gaps)
- **ALWAYS** decompress .bi5 files correctly (proprietary format)
- **VERIFY** date range avoids duplicate downloads (check existing data first)
- **ENSURE** data quality validation (no NULL prices, valid timestamps)
- **RESPECT** download limits (avoid hammering Dukascopy servers)

## Critical Rules

1. **Config Hierarchy:**
   - Symbols, date ranges → Central Hub (operational config)
   - Safe defaults → ConfigClient fallback
   - No API key needed (Dukascopy is free)

2. **Data Division (IMPORTANT):**
   - **Dukascopy**: Old historical data (2+ years back)
   - **Polygon-historical**: Recent gaps (last few months)
   - **NEVER** overlap date ranges!

3. **.bi5 Decompression:**
   - **ALWAYS** use LZMA decoder
   - **VERIFY** binary structure parsing
   - **HANDLE** decompression errors gracefully

4. **Data Quality Validation:**
   - **CHECK** for NULL values (bid, ask, timestamp)
   - **VERIFY** timestamp ordering (ascending)
   - **VALIDATE** price sanity (no extreme deviations)
   - **REJECT** invalid ticks

5. **Gap Detection:**
   - **CHECK** ClickHouse for existing data before download
   - **SKIP** already downloaded date ranges
   - **LOG** gaps found during validation

## Common Tasks

### Download New Historical Period
1. Update config via Central Hub API (set date_range)
2. Run downloader (automatic gap detection)
3. Monitor logs for download progress
4. Verify data in ClickHouse (query historical_ticks)
5. Check for gaps or errors

### Fix Corrupted Data
1. Identify corrupted date range (NULL checks, timestamp gaps)
2. Delete corrupted data from ClickHouse
3. Re-download specific date range
4. Validate decompression successful
5. Verify data quality

### Debug Missing Ticks
1. Check Dukascopy API availability
2. Verify .bi5 file format hasn't changed
3. Review decompression logs for errors
4. Test with sample .bi5 file
5. Check ClickHouse insert logs

### Optimize Download Performance
1. Increase batch size (download multiple hours in parallel)
2. Use connection pooling for API requests
3. Cache .bi5 files locally before processing
4. Parallelize decompression
5. Batch ClickHouse inserts

## Troubleshooting

### Issue 1: .bi5 Decompression Failing
**Symptoms:** Decompression errors, invalid data
**Solution:**
- Verify LZMA decoder version compatible
- Check .bi5 file not corrupted (re-download)
- Review Dukascopy format changes
- Test with known-good .bi5 file
- Update decompression library

### Issue 2: NULL Values in Tick Data
**Symptoms:** Many ticks have NULL bid/ask
**Solution:**
- Enable data quality validation in config
- Review .bi5 parsing logic
- Check for delta encoding issues
- Verify base price correctly set
- Reject ticks with NULL values

### Issue 3: Duplicate Data in ClickHouse
**Symptoms:** Same timestamps appearing multiple times
**Solution:**
- Enable `skip_existing` in config
- Check gap detection logic
- Use `ON CONFLICT` for upserts
- Query existing data before download
- Clear duplicates manually if needed

### Issue 4: Download Taking Too Long
**Symptoms:** Downloading 1 year takes days
**Solution:**
- Increase batch size (parallel downloads)
- Cache .bi5 files locally
- Parallelize decompression
- Optimize ClickHouse batch inserts
- Check network bandwidth to Dukascopy

### Issue 5: API Rate Limiting
**Symptoms:** 429 errors, download throttled
**Solution:**
- Add delays between requests
- Respect Dukascopy rate limits
- Implement exponential backoff
- Download during off-peak hours
- Contact Dukascopy for higher limits

## Validation Checklist

After making changes to this service:
- [ ] .bi5 files downloaded successfully
- [ ] Decompression works (no format errors)
- [ ] Data written to historical_ticks (query ClickHouse)
- [ ] Tick counts match expected (no missing days)
- [ ] No duplicate data (check date range overlaps)
- [ ] NULL validation passing (no NULL bid/ask)
- [ ] Timestamp ordering correct (ascending)
- [ ] Price sanity checks passing
- [ ] ConfigClient fetching from Central Hub
- [ ] Hot-reload responding to config updates

## Related Skills

- `central-hub` - Provides operational config and service discovery
- `polygon-historical-downloader` - Handles recent historical gaps
- `tick-aggregator` - Reads historical_ticks for batch aggregation
- `data-bridge` - Archives live data to historical storage

## References

- Full Documentation: `docs/SERVICE_ARCHITECTURE_AND_FLOW.md` (lines 322-337)
- Planning Guide: `docs/PLANNING_SKILL_GUIDE.md` (Service 3, lines 452-650)
- Flow + Messaging: `docs/SERVICE_FLOW_TREE_WITH_MESSAGING.md` (lines 107-127)
- Database Schema: `docs/table_database_input.md` (historical_ticks table)
- Config Architecture: `docs/CONFIG_ARCHITECTURE.md`
- Central Hub Skill: `.claude/skills/central-hub/SKILL.md`
- Code: `00-data-ingestion/dukascopy-historical-downloader/`

---

**Created:** 2025-10-19
**Version:** 2.0.0
**Status:** Production Ready
