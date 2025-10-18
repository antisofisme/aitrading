# Skill: external-data-collector Service

## Purpose
Collect external market data (economic calendar, FRED indicators, commodity prices) for ML feature enrichment.

## Key Facts
- **Phase**: Data Foundation (Phase 1)
- **Status**: ✅ Active, Production
- **Priority**: P1 (Important - enriches ML features)
- **Data sources**: Economic Calendar API, FRED (Federal Reserve), Yahoo Finance (commodities)
- **Update frequency**: Daily (economic), Weekly (FRED), Real-time cached (commodities)

## Data Flow
```
Economic Calendar API + FRED + Yahoo Finance
  → external-data-collector (collect, normalize)
  → ClickHouse.external_economic_calendar
  → ClickHouse.external_fred_indicators
  → ClickHouse.external_commodity_prices
  → NATS: market.external.{type} (real-time)
  → Kafka: external_data_archive (optional)
```

## Messaging
- **NATS Publish**: `market.external.economic_calendar`, `market.external.fred_indicators`, `market.external.commodity_prices`
- **Kafka Publish**: `external_data_archive` (optional archival)
- **Pattern**: Both NATS + Kafka (external data needs real-time + archive)

## Dependencies
- **Upstream**: External APIs (Economic Calendar, FRED, Yahoo Finance)
- **Downstream**: feature-engineering-service (joins external data with candles)
- **Infrastructure**: ClickHouse, NATS cluster, Kafka (optional)

## Critical Rules
1. **NEVER** skip economic calendar updates (important for news-based features)
2. **ALWAYS** cache commodity prices (avoid hitting API limits)
3. **VERIFY** FRED data freshness (updates weekly, check last_updated field)
4. **ENSURE** timezone consistency (convert all timestamps to UTC)
5. **VALIDATE** data completeness (no missing critical indicators)

## Data Types
### Economic Calendar
- News events (NFP, FOMC, CPI, GDP releases)
- Impact level (high/medium/low)
- Actual vs forecast values

### FRED Indicators
- Interest rates (Fed Funds Rate)
- Inflation (CPI, PCE)
- Employment (Unemployment Rate)
- GDP growth

### Commodity Prices
- Gold (XAUUSD fundamental)
- Oil (WTI, Brent)
- Other metals (Silver, Copper)

## Validation
When working on this service, ALWAYS verify:
- [ ] Data written to ClickHouse external_* tables
- [ ] NATS publishes `market.external.*` subjects
- [ ] Economic calendar has upcoming events (not empty)
- [ ] FRED indicators updated (check last_updated timestamp)
- [ ] Commodity prices current (within last hour)

## Reference Docs

**Service Documentation:**
- Planning guide: `PLANNING_SKILL_GUIDE.md` (Service 4, lines 652-850)
- Architecture: `SERVICE_ARCHITECTURE_AND_FLOW.md` (lines 340-368)
- Flow + messaging: `SERVICE_FLOW_TREE_WITH_MESSAGING.md` (lines 129-165)
- Database schema: `table_database_input.md` (external_* tables)

**Operational Skills (Central-Hub Agent Tools):**
- 🔍 Debug issues: `.claude/skills/central-hub-debugger/`
- 🔧 Fix problems: `.claude/skills/central-hub-fixer/`
- ➕ Create new service: `.claude/skills/central-hub-service-creator/`
