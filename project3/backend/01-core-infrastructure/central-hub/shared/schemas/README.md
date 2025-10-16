# Database Schema Management

**Version:** 2.0.0
**Last Updated:** 2025-10-16

## Overview

This directory contains the **single source of truth** for all database schemas.

## Architecture

```
Source of Truth: SQL Files
central-hub/shared/schemas/
  ├── clickhouse/*.sql
  └── timescaledb/*.sql
          ↓
  Automatic Initialization
          ↓
Database Containers
- ClickHouse: /docker-entrypoint-initdb.d/
- TimescaleDB: /docker-entrypoint-initdb.d/
  → Execute .sql files on first start
          ↓
      Ready to Use!
```

## Key Principles

1. **SQL Files = Source of Truth**
   - Complete table definitions
   - Indexes, views, TTL policies
   - Documentation and sample queries

2. **Python SDK = Type Hints Only**
   - For validation (optional)
   - NOT for schema creation

3. **Native Init = Schema Creation**
   - Docker mounts SQL files
   - Auto-execute on first start
   - Simple and reliable

## Development Workflow

**Fresh Start:**
```bash
docker-compose down -v
docker-compose up
# → Schemas auto-created!
```

**Normal Restart:**
```bash
docker-compose restart clickhouse
# → Data retained
```

## Python Usage (Validation Only)

```python
from central_hub_sdk.schemas import TickData, validate_tick_data

# Type hints
tick: TickData = {...}

# Validation (optional)
validate_tick_data(tick)
```

## Connection Management

```python
from central_hub_sdk.database import DatabaseRouter

router = DatabaseRouter(config)
await router.initialize()

clickhouse = router.get_manager(db_type=DatabaseType.CLICKHOUSE)
# Tables already exist!
await clickhouse.execute("INSERT INTO ticks ...")
```

## Files

### ClickHouse
- `01_ticks.sql` - Tick data (90 days TTL)
- `02_aggregates.sql` - OHLCV bars (10 years)
- `03-08_external_*.sql` - External data

### TimescaleDB
- `01_market_ticks.sql` - Real-time ticks
- `02_market_candles.sql` - Candles
- `03_market_context.sql` - Context metadata

## Troubleshooting

**Tables not created?**
1. Check `docker logs suho-clickhouse`
2. Verify volume mount in docker-compose.yml
3. Force re-init: `docker-compose down -v`

**Schema out of sync?**
- SQL files are the truth
- Update Python hints to match (optional)

---

**Golden Rule:** SQL files are the single source of truth.
