---
name: external-data-collector
description: Collects external market data (economic calendar, FRED indicators, commodity prices) for ML feature enrichment with daily/weekly update schedules and real-time caching
license: MIT
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
metadata:
  type: Data Ingestion (External Data)
  phase: Data Foundation (Phase 1)
  status: Active Production
  priority: P1 (Important - enriches ML features)
  port: 8004
  dependencies:
    - central-hub
    - clickhouse
    - nats
    - kafka
  version: 2.0.0
---

# External Data Collector Service

Collects external market data from multiple sources (Economic Calendar API, FRED, Yahoo Finance) for ML feature enrichment. Provides economic events, macroeconomic indicators, and commodity price correlations.

## When to Use This Skill

Use this skill when:
- Adding new economic indicators
- Debugging missing external data
- Integrating new external data sources (APIs)
- Configuring update schedules (daily/weekly)
- Verifying timezone conversions (all UTC)
- Optimizing commodity price caching

## Service Overview

**Type:** Data Ingestion (External Data)
**Port:** 8004
**Data Sources:**
- Economic Calendar API (news events, NFP, FOMC)
- FRED API (Federal Reserve indicators)
- Yahoo Finance API (commodity prices)
**Storage:** ClickHouse (`external_*` tables)
**Messaging:** NATS (real-time) + Kafka (archival)
**Update Frequency:**
- Economic Calendar: Daily
- FRED Indicators: Weekly
- Commodity Prices: Real-time cached (15-min TTL)

**Dependencies:**
- **Upstream**: External APIs (Economic Calendar, FRED, Yahoo Finance)
- **Downstream**: feature-engineering (joins external data with candles)
- **Infrastructure**: ClickHouse, NATS cluster, Kafka (optional)

## Key Capabilities

- Economic calendar collection (news events, impact levels)
- FRED macroeconomic indicators (interest rates, inflation, employment, GDP)
- Commodity price tracking (gold, oil, silver, copper)
- Timezone normalization (all timestamps UTC)
- Real-time NATS publishing
- Kafka archival (optional)
- Data freshness validation

## Architecture

### Data Flow

```
Economic Calendar API + FRED API + Yahoo Finance API
  ↓ (Collect & normalize)
external-data-collector
  ├─→ Validate & convert to UTC
  ├─→ ClickHouse.external_economic_calendar
  ├─→ ClickHouse.external_fred_indicators
  ├─→ ClickHouse.external_commodity_prices
  ├─→ NATS: market.external.{type} (real-time)
  └─→ Kafka: external_data_archive (optional)
```

### Data Types

**1. Economic Calendar**
- **Events**: NFP, FOMC meetings, CPI, GDP releases, PMI, retail sales
- **Impact Level**: High/Medium/Low
- **Values**: Actual vs Forecast vs Previous
- **Timezone**: Converted to UTC
- **Example**: NFP (Non-Farm Payrolls) - High impact, monthly

**2. FRED Indicators**
- **Interest Rates**: Fed Funds Rate, 10-Year Treasury Yield
- **Inflation**: CPI, PCE, Core Inflation
- **Employment**: Unemployment Rate, Labor Force Participation
- **GDP**: Real GDP Growth, GDP Deflator
- **Update**: Weekly (FRED publishes weekly)

**3. Commodity Prices**
- **Gold** (XAUUSD): Fundamental driver for gold trading
- **Oil**: WTI, Brent (energy correlation)
- **Silver** (XAGUSD): Precious metals correlation
- **Copper**: Economic health indicator
- **Update**: Real-time cached (15-min TTL to avoid API limits)

### Configuration

**Operational Config (Central Hub):**
```json
{
  "operational": {
    "economic_calendar": {
      "enabled": true,
      "update_schedule": "0 2 * * *",
      "lookforward_days": 30,
      "impact_levels": ["high", "medium"]
    },
    "fred_indicators": {
      "enabled": true,
      "update_schedule": "0 3 * * 1",
      "indicators": [
        "FEDFUNDS",
        "DGS10",
        "CPIAUCSL",
        "UNRATE",
        "GDP"
      ]
    },
    "commodity_prices": {
      "enabled": true,
      "cache_ttl_minutes": 15,
      "symbols": ["XAUUSD", "CL=F", "SI=F", "HG=F"]
    }
  }
}
```

**Environment Variables (Secrets):**
```bash
ECONOMIC_CALENDAR_API_KEY=your_key  # Economic Calendar API
FRED_API_KEY=your_key               # Federal Reserve API
# Yahoo Finance requires no API key (free)
```

## Examples

### Example 1: Fetch Config from Central Hub

```python
from shared.components.config import ConfigClient

# Initialize client
client = ConfigClient(
    service_name="external-data-collector",
    safe_defaults={
        "operational": {
            "economic_calendar": {"enabled": True},
            "fred_indicators": {"enabled": True},
            "commodity_prices": {"cache_ttl_minutes": 15}
        }
    }
)
await client.init_async()

# Get config
config = await client.get_config()
fred_indicators = config['operational']['fred_indicators']['indicators']
print(f"Collecting {len(fred_indicators)} FRED indicators: {fred_indicators}")
```

### Example 2: Collect Economic Calendar Events

```python
from external_collector import EconomicCalendarCollector

collector = EconomicCalendarCollector()

# Fetch upcoming events (next 30 days)
events = await collector.fetch_events(lookforward_days=30, impact_levels=["high"])

# Result: List of high-impact events
# [
#   {
#     "event_name": "Non-Farm Payrolls",
#     "timestamp": "2025-10-01 12:30:00 UTC",
#     "impact": "high",
#     "currency": "USD",
#     "actual": None,  # Not published yet
#     "forecast": 200000,
#     "previous": 180000
#   },
#   ...
# ]

# Write to ClickHouse
await collector.save_to_clickhouse(events)
```

### Example 3: Collect FRED Indicators

```python
from external_collector import FREDCollector

collector = FREDCollector()

# Fetch Fed Funds Rate
fed_funds = await collector.fetch_indicator(
    indicator_id="FEDFUNDS",
    start_date="2024-01-01"
)

# Result:
# [
#   {"date": "2024-01-01", "value": 5.33},
#   {"date": "2024-02-01", "value": 5.33},
#   ...
# ]

# Write to ClickHouse
await collector.save_fred_data(fed_funds, indicator_name="fed_funds_rate")
```

### Example 4: Query External Data from ClickHouse

```sql
-- Check upcoming economic events
SELECT
    event_name,
    timestamp,
    impact,
    currency,
    actual,
    forecast,
    previous
FROM external_economic_calendar
WHERE timestamp >= now()
  AND timestamp <= now() + INTERVAL 7 DAY
  AND impact = 'high'
ORDER BY timestamp ASC;

-- Check latest FRED indicators
SELECT
    indicator_name,
    date,
    value,
    last_updated
FROM external_fred_indicators
WHERE indicator_name = 'fed_funds_rate'
ORDER BY date DESC
LIMIT 10;

-- Check commodity prices (last hour)
SELECT
    symbol,
    timestamp,
    price,
    volume
FROM external_commodity_prices
WHERE timestamp >= now() - INTERVAL 1 HOUR
ORDER BY timestamp DESC;
```

### Example 5: Subscribe to Real-time External Data (NATS)

```bash
# Subscribe to all external data
nats sub "market.external.*"

# Subscribe to economic calendar only
nats sub "market.external.economic_calendar"

# Subscribe to FRED indicators
nats sub "market.external.fred_indicators"

# Subscribe to commodity prices
nats sub "market.external.commodity_prices"
```

## Guidelines

- **ALWAYS** use ConfigClient for operational settings (update schedules, indicators)
- **NEVER** skip timezone conversion (all timestamps must be UTC)
- **ALWAYS** cache commodity prices (avoid hitting API rate limits)
- **VERIFY** FRED data freshness (check `last_updated` field)
- **ENSURE** economic calendar has upcoming events (not stale)
- **VALIDATE** data completeness (no missing critical indicators)

## Critical Rules

1. **Config Hierarchy:**
   - API keys → ENV variables (`ECONOMIC_CALENDAR_API_KEY`, `FRED_API_KEY`)
   - Update schedules, indicators → Central Hub (operational config)
   - Safe defaults → ConfigClient fallback

2. **Timezone Consistency (CRITICAL):**
   - **ALWAYS** convert all timestamps to UTC
   - **NEVER** store local timezones
   - **VERIFY** timezone conversion correct

3. **Data Freshness:**
   - **Economic Calendar**: Daily updates (check upcoming events)
   - **FRED**: Weekly updates (check `last_updated` timestamp)
   - **Commodities**: 15-min cache TTL (real-time with rate limiting)

4. **API Rate Limiting:**
   - **Economic Calendar**: Respect API limits (usually 1000 calls/month)
   - **FRED**: No strict limits, but cache results
   - **Yahoo Finance**: Cache for 15 min (avoid excessive calls)

5. **Data Validation:**
   - **CHECK** for NULL values in critical fields
   - **VALIDATE** impact levels (high/medium/low only)
   - **ENSURE** forecast/actual/previous values reasonable

## Common Tasks

### Add New Economic Indicator
1. Find indicator ID in FRED database
2. Update config via Central Hub API (add to `indicators` list)
3. Test collection with sample date range
4. Verify data written to ClickHouse
5. Check NATS publishing working

### Debug Missing External Data
1. Check API credentials valid (ENV vars)
2. Verify update schedules running (cron jobs)
3. Query ClickHouse for last update timestamp
4. Review collector logs for errors
5. Test API manually to verify data availability

### Optimize Commodity Price Caching
1. Monitor API call frequency
2. Adjust `cache_ttl_minutes` based on usage
3. Implement in-memory caching layer
4. Check cache hit rate
5. Balance freshness vs API limits

### Add New External Data Source
1. Research API documentation
2. Implement collector class
3. Add configuration to Central Hub
4. Create ClickHouse table schema
5. Add NATS publishing
6. Test integration end-to-end

## Troubleshooting

### Issue 1: Economic Calendar Empty
**Symptoms:** No upcoming events in database
**Solution:**
- Check `ECONOMIC_CALENDAR_API_KEY` valid
- Verify API endpoint accessible
- Review `lookforward_days` config (should be 30+)
- Check API response for data availability
- Test API manually

### Issue 2: FRED Data Not Updating
**Symptoms:** `last_updated` timestamp stale
**Solution:**
- Verify weekly cron schedule running
- Check `FRED_API_KEY` valid
- Review collector logs for errors
- Test FRED API manually
- Check network connectivity

### Issue 3: Commodity Prices Stale
**Symptoms:** Prices not updating in real-time
**Solution:**
- Check cache TTL (should be 15 min or less)
- Verify Yahoo Finance API accessible
- Review cache invalidation logic
- Test API response manually
- Check for API rate limiting

### Issue 4: Timezone Conversion Errors
**Symptoms:** Events at wrong times
**Solution:**
- Review timezone conversion logic
- Ensure using UTC everywhere
- Check source API timezone format
- Test with known event times
- Validate stored timestamps

### Issue 5: NATS Publishing Failing
**Symptoms:** feature-engineering not receiving external data
**Solution:**
- Check NATS cluster connectivity
- Verify publishing enabled in config
- Review NATS subject names correct
- Test with `nats sub`
- Check for publishing errors in logs

## Validation Checklist

After making changes to this service:
- [ ] Data written to ClickHouse external_* tables
- [ ] NATS publishes `market.external.*` subjects
- [ ] Economic calendar has upcoming events (not empty)
- [ ] FRED indicators updated (check `last_updated` timestamp)
- [ ] Commodity prices current (within cache TTL)
- [ ] All timestamps in UTC
- [ ] No NULL values in critical fields
- [ ] API rate limits respected
- [ ] ConfigClient fetching from Central Hub
- [ ] Hot-reload responding to config updates

## Related Skills

- `central-hub` - Provides operational config and service discovery
- `feature-engineering` - Joins external data with candles for ML features
- `data-bridge` - Archives external data to ClickHouse

## References

- Full Documentation: `docs/SERVICE_ARCHITECTURE_AND_FLOW.md` (lines 340-368)
- Planning Guide: `docs/PLANNING_SKILL_GUIDE.md` (Service 4, lines 652-850)
- Flow + Messaging: `docs/SERVICE_FLOW_TREE_WITH_MESSAGING.md` (lines 129-165)
- Database Schema: `docs/table_database_input.md` (external_* tables)
- Config Architecture: `docs/CONFIG_ARCHITECTURE.md`
- Central Hub Skill: `.claude/skills/central-hub/SKILL.md`
- Code: `00-data-ingestion/external-data-collector/`

---

**Created:** 2025-10-19
**Version:** 2.0.0
**Status:** Production Ready
