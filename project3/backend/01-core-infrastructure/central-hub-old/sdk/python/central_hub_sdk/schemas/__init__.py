"""
Central Hub SDK - Schema Definitions Module
Type hints and validation helpers - NOT for schema creation

⚠️ IMPORTANT: Schema Creation
   This module provides TYPE HINTS and VALIDATION only.

   Schema creation (CREATE TABLE) is handled by SQL files:
   - ClickHouse: central-hub/shared/schemas/clickhouse/*.sql
   - TimescaleDB: central-hub/shared/schemas/timescaledb/*.sql
   - ArangoDB: central-hub/shared/schemas/arangodb/*.json
   - Weaviate: central-hub/shared/schemas/weaviate/*.json

   SQL files are automatically executed by:
   - ClickHouse: /docker-entrypoint-initdb.d/ (native init)
   - TimescaleDB: /docker-entrypoint-initdb.d/ (PostgreSQL init)
   - Others: Application-level initialization if needed

   Use this module for:
   - Type checking (mypy, pyright)
   - Runtime validation
   - Documentation

Version: 2.0.0
"""

# ClickHouse Type Hints (SIMPLIFIED - validation only)
from .clickhouse_schema import (
    TickData,
    AggregateData,
    EconomicCalendarData,
    FredEconomicData,
    validate_tick_data,
    validate_aggregate_data,
    TABLE_TICKS,
    TABLE_AGGREGATES,
    TABLE_ECONOMIC_CALENDAR,
    TABLE_FRED_ECONOMIC,
)

# DragonflyDB Cache Patterns
from .dragonfly_schema import (
    CacheKeyPattern,
    get_dragonfly_schemas,
)

# Legacy imports (for backward compatibility - deprecated)
# TODO: Remove in v3.0.0
try:
    from .timescale_schema import get_timescale_schemas
    from .arangodb_schema import get_arangodb_schemas
    from .weaviate_schema import get_weaviate_schemas
except ImportError:
    pass

__all__ = [
    # ClickHouse Type Hints
    "TickData",
    "AggregateData",
    "EconomicCalendarData",
    "FredEconomicData",
    "validate_tick_data",
    "validate_aggregate_data",
    "TABLE_TICKS",
    "TABLE_AGGREGATES",
    "TABLE_ECONOMIC_CALENDAR",
    "TABLE_FRED_ECONOMIC",
    # Cache Patterns
    "CacheKeyPattern",
    "get_dragonfly_schemas",
]

__version__ = "2.0.0"
