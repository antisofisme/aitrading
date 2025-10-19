---
name: polygon-historical-downloader
description: Gap filling service for recent historical data from Polygon.io REST API. Detects gaps in live_aggregates and backfills missing candles with scheduled batch processing.
license: MIT
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
metadata:
  type: Data Ingestion (Gap Filling)
  phase: Data Foundation (Phase 1)
  status: Active Production
  priority: P0 (Critical - prevents incomplete data)
  port: 8002
  dependencies:
    - central-hub
    - clickhouse
  version: 2.0.0
---

# Polygon Historical Downloader Service

Gap filling service for recent historical data from Polygon.io REST API. Detects gaps in live_aggregates and backfills missing candles through scheduled batch processing (hourly, daily, weekly).

## When to Use This Skill

Use this skill when:
- Fixing gaps in recent historical data (last 7 days)
- Implementing gap detection logic
- Debugging incomplete candle data
- Configuring gap detection thresholds
- Scheduling backfill jobs
- Verifying Polygon.io API integration

## Service Overview

**Type:** Data Ingestion (Gap Filling)
**Port:** 8002
**Data Source:** Polygon.io REST API
**Storage:** ClickHouse (`live_aggregates` table, 7-day retention)
**Messaging:** None (batch mode only)
**Mode:** Scheduled batch processing (hourly, daily, weekly checks)
**Range:** Last 7 days (matches live_aggregates retention)

**Dependencies:**
- **Upstream**: Polygon.io REST API
- **Downstream**: None (writes directly to ClickHouse)
- **Reads from**: ClickHouse.live_aggregates (gap detection)
- **Infrastructure**: ClickHouse only

## Key Capabilities

- Intelligent gap detection across date ranges
- Scheduled batch processing (hourly/daily/weekly)
- Recent historical data download (last 7 days)
- Direct ClickHouse writing (live_aggregates)
- Configurable completeness thresholds
- Rate limit handling (5 req/sec)

## Architecture

### Data Flow

```
ClickHouse.live_aggregates (read for gap detection)
  ↓ (Detect gaps)
Gap Detector (completeness analysis)
  ↓ (Identify missing candles)
Polygon.io REST API (download missing data)
  ↓ (Validate & normalize)
polygon-historical-downloader
  ↓ (Backfill)
ClickHouse.live_aggregates (write gaps)
```

**NO Messaging:**
- No NATS publishing (batch mode, not real-time)
- No Kafka archival (writes directly to ClickHouse)

### Gap Detection Strategy

**Completeness Thresholds:**

| Timeframe Type | Threshold | Rationale |
|----------------|-----------|-----------|
| **Intraday** (5m, 15m, 30m, 1h, 4h) | 100% | ANY missing candle = gap (trading hours continuous) |
| **Daily+** (1d, 1w) | 80% | Weekends/holidays tolerated (natural gaps) |

**Check Period:** Last 7 days (live_aggregates retention window)

**Gap Detection Algorithm:**
1. Query ClickHouse for existing candles per symbol/timeframe
2. Calculate expected candle count for date range
3. Compare actual vs expected
4. If completeness < threshold → GAP DETECTED
5. Identify specific missing date ranges
6. Download only gaps from Polygon.io

### Configuration

**Operational Config (Central Hub):**
```json
{
  "operational": {
    "symbols": ["EURUSD", "XAUUSD", "GBPUSD"],
    "timeframes": ["5m", "15m", "30m", "1h", "4h", "1d", "1w"],
    "check_period_days": 7,
    "completeness_threshold_intraday": 1.0,
    "completeness_threshold_daily": 0.8,
    "batch_size": 150,
    "schedule": {
      "hourly_check": "0 * * * *",
      "daily_check": "0 1 * * *",
      "weekly_check": "0 2 * * 0"
    }
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
    service_name="polygon-historical-downloader",
    safe_defaults={
        "operational": {
            "batch_size": 150,
            "check_period_days": 7,
            "completeness_threshold_intraday": 1.0
        }
    }
)
await client.init_async()

# Get config
config = await client.get_config()
symbols = config['operational']['symbols']
check_period = config['operational']['check_period_days']
print(f"Checking {symbols} for gaps in last {check_period} days")
```

### Example 2: Detect Gaps

```python
from gap_detector import GapDetector

detector = GapDetector()

# Detect gaps for EURUSD 5m
gaps = await detector.detect_gaps(
    symbol="EURUSD",
    timeframe="5m",
    check_period_days=7,
    completeness_threshold=1.0
)

# Result: List of gap periods
# [
#   {"start": "2025-10-15 10:00", "end": "2025-10-15 12:00"},
#   {"start": "2025-10-18 08:00", "end": "2025-10-18 09:00"}
# ]
```

### Example 3: Backfill Detected Gaps

```python
from polygon_downloader import PolygonHistoricalDownloader

downloader = PolygonHistoricalDownloader()

# Download and backfill gaps
for gap in gaps:
    await downloader.download_and_fill(
        symbol="EURUSD",
        timeframe="5m",
        start_date=gap["start"],
        end_date=gap["end"]
    )
    # Writes directly to ClickHouse.live_aggregates
```

### Example 4: Query Gap Detection Results

```sql
-- Check completeness for EURUSD 5m last 7 days
SELECT
    symbol,
    timeframe,
    toDate(timestamp) as date,
    COUNT(*) as actual_candles,
    288 as expected_candles,  -- 288 5m candles per day
    (COUNT(*) / 288.0) * 100 as completeness_pct
FROM live_aggregates
WHERE symbol = 'EURUSD'
  AND timeframe = '5m'
  AND timestamp >= now() - INTERVAL 7 DAY
GROUP BY symbol, timeframe, date
HAVING completeness_pct < 100
ORDER BY date DESC;
```

### Example 5: Update Gap Detection Config

```bash
# Adjust completeness threshold
curl -X POST http://suho-central-hub:7000/api/v1/config/polygon-historical-downloader \
  -H "Content-Type: application/json" \
  -d '{
    "operational": {
      "completeness_threshold_intraday": 0.95,
      "batch_size": 200
    }
  }'

# Hot-reload will apply new thresholds
```

## Guidelines

- **ALWAYS** use ConfigClient for operational settings (thresholds, batch sizes)
- **NEVER** overlap with dukascopy-historical (polygon = recent, dukascopy = old)
- **ALWAYS** check for gaps before downloading (avoid duplicates)
- **VERIFY** date range stays within 7 days (live_aggregates retention)
- **RESPECT** Polygon.io rate limits (5 req/sec)
- **ENSURE** gap detection uses correct completeness thresholds

## Critical Rules

1. **Config Hierarchy:**
   - API keys → ENV variables (`POLYGON_API_KEY`)
   - Thresholds, schedules → Central Hub (operational config)
   - Safe defaults → ConfigClient fallback

2. **Data Division (IMPORTANT):**
   - **Polygon-historical**: Recent gaps (last 7 days)
   - **Dukascopy-historical**: Old data (2+ years back)
   - **NEVER** overlap date ranges!

3. **Gap Detection Accuracy:**
   - **VERIFY** entire date range checked (not just between existing data)
   - **USE** correct threshold per timeframe type
   - **CHECK** market hours (avoid detecting natural gaps as issues)

4. **Deduplication:**
   - **CHECK** existing data before download
   - **USE** `ON CONFLICT` for upserts if needed
   - **AVOID** duplicate candle inserts

5. **Rate Limiting:**
   - **RESPECT** Polygon.io limits (5 req/sec)
   - **IMPLEMENT** exponential backoff on errors
   - **BATCH** requests efficiently

## Common Tasks

### Fix Detected Gaps
1. Review gap detector logs for identified gaps
2. Verify gaps are real (not weekends/holidays)
3. Run downloader for specific date ranges
4. Verify backfill success in ClickHouse
5. Check completeness improved

### Add New Timeframe
1. Update config via Central Hub API (add to `timeframes`)
2. Set appropriate completeness threshold
3. Add to gap detection schedule
4. Test gap detection logic
5. Verify backfill working

### Debug Gap Detection Issues
1. Query ClickHouse for actual vs expected candles
2. Check gap detector algorithm for logic errors
3. Verify completeness threshold appropriate
4. Review market hours handling
5. Test with known gap periods

### Optimize Download Performance
1. Increase batch size (test performance)
2. Parallelize gap fills (multiple symbols)
3. Cache API responses (avoid redundant calls)
4. Optimize ClickHouse write performance
5. Monitor API rate limit usage

## Troubleshooting

### Issue 1: Gaps Not Being Detected
**Symptoms:** Known missing candles not identified
**Solution:**
- Verify completeness threshold not too low
- Check gap detection date range correct (7 days)
- Review algorithm logic (entire range vs between data)
- Test with manual candle count query
- Check gap detector logs for errors

### Issue 2: False Positive Gap Detection
**Symptoms:** Weekends/holidays detected as gaps
**Solution:**
- Use 80% threshold for daily+ timeframes
- Implement market hours filtering
- Check calendar for holidays
- Review completeness calculation logic
- Test with known valid periods

### Issue 3: Polygon API Rate Limiting
**Symptoms:** 429 errors, downloads failing
**Solution:**
- Reduce batch size (fewer parallel requests)
- Implement exponential backoff
- Add delays between requests
- Monitor API usage (stay under 5 req/sec)
- Consider Polygon.io plan upgrade

### Issue 4: Duplicate Candles After Backfill
**Symptoms:** Same timestamps appearing multiple times
**Solution:**
- Check deduplication logic before insert
- Use `ON CONFLICT` in SQL
- Query existing data before download
- Review backfill logic for bugs
- Clear duplicates manually if needed

### Issue 5: Incomplete Backfills
**Symptoms:** Gaps still exist after backfill attempt
**Solution:**
- Check Polygon.io response for data availability
- Verify data exists for requested period
- Review backfill logs for errors
- Test API manually for date range
- Check ClickHouse insert success

## Validation Checklist

After making changes to this service:
- [ ] Gaps detected correctly (check gap_detector logs)
- [ ] Backfill completes successfully (no errors in logs)
- [ ] Data written to live_aggregates (query ClickHouse)
- [ ] No duplicate data (check deduplication logic)
- [ ] Schedule runs as expected (cron: hourly, daily, weekly)
- [ ] Completeness improved after backfill
- [ ] API rate limits respected
- [ ] ConfigClient fetching from Central Hub
- [ ] Hot-reload responding to config updates

## Related Skills

- `central-hub` - Provides operational config and service discovery
- `polygon-live-collector` - Provides real-time tick data
- `dukascopy-historical-downloader` - Handles old historical data (2+ years)
- `tick-aggregator` - Reads live_aggregates for feature calculation

## References

- Full Documentation: `docs/SERVICE_ARCHITECTURE_AND_FLOW.md` (lines 301-319)
- Planning Guide: `docs/PLANNING_SKILL_GUIDE.md` (Service 2, lines 252-450)
- Flow + Messaging: `docs/SERVICE_FLOW_TREE_WITH_MESSAGING.md` (lines 82-105)
- Database Schema: `docs/table_database_input.md` (live_aggregates table)
- Config Architecture: `docs/CONFIG_ARCHITECTURE.md`
- Central Hub Skill: `.claude/skills/central-hub/SKILL.md`
- Code: `00-data-ingestion/polygon-historical-downloader/`

---

**Created:** 2025-10-19
**Version:** 2.0.0
**Status:** Production Ready
