"""
ClickHouse Schema Definitions
OLAP database for analytics and aggregations
"""
from typing import Dict, List, Any


def get_clickhouse_schemas() -> List[Dict[str, Any]]:
    """Get all ClickHouse table schemas"""
    return [
        TICKS_SCHEMA,
        AGGREGATES_SCHEMA,
        EXTERNAL_ECONOMIC_CALENDAR_SCHEMA,
        EXTERNAL_FRED_ECONOMIC_SCHEMA,
    ]


# ============================================================================
# TICKS TABLE (Replicated from TimescaleDB for fast analytics)
# ============================================================================

TICKS_SCHEMA = {
    "name": "ticks",
    "description": "Replicated tick data for analytics",
    "version": "1.0",
    "engine": "MergeTree",
    "partition_by": "(symbol, toYYYYMM(timestamp))",
    "order_by": "(symbol, timestamp)",
    "ttl": "toDateTime(timestamp) + INTERVAL 90 DAY",
    "columns": {
        "symbol": "String",
        "timestamp": "DateTime64(3, 'UTC')",
        "timestamp_ms": "UInt64",
        "bid": "Decimal(18, 5)",
        "ask": "Decimal(18, 5)",
        "mid": "Decimal(18, 5)",
        "spread": "Decimal(10, 5)",
        "source": "String",
        "event_type": "String DEFAULT 'quote'",
        "ingested_at": "DateTime64(3, 'UTC') DEFAULT now64(3)",
    },
    "settings": {
        "index_granularity": 8192
    }
}


# ============================================================================
# AGGREGATES TABLE (OHLCV Candles)
# ============================================================================

AGGREGATES_SCHEMA = {
    "name": "aggregates",
    "description": "OHLCV candles with indicators",
    "version": "1.0",
    "engine": "MergeTree",
    "partition_by": "(symbol, toYYYYMM(timestamp))",
    "order_by": "(symbol, timeframe, timestamp)",
    "ttl": "toDateTime(timestamp) + INTERVAL 3650 DAY",  # 10 years
    "columns": {
        "symbol": "String",
        "timeframe": "String",
        "timestamp": "DateTime64(3, 'UTC')",
        "timestamp_ms": "UInt64",
        "open": "Decimal(18, 5)",
        "high": "Decimal(18, 5)",
        "low": "Decimal(18, 5)",
        "close": "Decimal(18, 5)",
        "volume": "UInt64",
        "vwap": "Decimal(18, 5) DEFAULT 0",
        "range_pips": "Decimal(10, 5)",
        "body_pips": "Decimal(10, 5)",
        "start_time": "DateTime64(3, 'UTC')",
        "end_time": "DateTime64(3, 'UTC')",
        "source": "String",
        "event_type": "String DEFAULT 'ohlcv'",
        "indicators": "String DEFAULT ''",  # JSON string
        "ingested_at": "DateTime64(3, 'UTC') DEFAULT now64(3)",
    },
    "settings": {
        "index_granularity": 8192
    }
}


# ============================================================================
# EXTERNAL ECONOMIC CALENDAR
# ============================================================================

EXTERNAL_ECONOMIC_CALENDAR_SCHEMA = {
    "name": "external_economic_calendar",
    "description": "Economic events and calendar",
    "version": "1.0",
    "engine": "MergeTree",
    "partition_by": "toYYYYMM(event_time)",
    "order_by": "(event_time, currency, event_name)",
    "ttl": "event_time + INTERVAL 1825 DAY",  # 5 years
    "columns": {
        "event_time": "DateTime64(3, 'UTC')",
        "currency": "String",
        "event_name": "String",
        "impact": "String",
        "forecast": "Nullable(Decimal(18, 5))",
        "actual": "Nullable(Decimal(18, 5))",
        "previous": "Nullable(Decimal(18, 5))",
        "source": "String",
        "ingested_at": "DateTime64(3, 'UTC') DEFAULT now64(3)",
    },
    "settings": {
        "index_granularity": 8192
    }
}


# ============================================================================
# EXTERNAL FRED ECONOMIC DATA
# ============================================================================

EXTERNAL_FRED_ECONOMIC_SCHEMA = {
    "name": "external_fred_economic",
    "description": "Federal Reserve economic data",
    "version": "1.0",
    "engine": "MergeTree",
    "partition_by": "toYYYYMM(observation_date)",
    "order_by": "(series_id, observation_date)",
    "ttl": "observation_date + INTERVAL 3650 DAY",  # 10 years
    "columns": {
        "series_id": "String",
        "observation_date": "Date",
        "value": "Decimal(18, 5)",
        "series_title": "String",
        "series_category": "String",
        "source": "String DEFAULT 'FRED'",
        "ingested_at": "DateTime64(3, 'UTC') DEFAULT now64(3)",
    },
    "settings": {
        "index_granularity": 8192
    }
}


# ============================================================================
# SQL GENERATION FUNCTIONS
# ============================================================================

def generate_create_table_sql(schema: Dict[str, Any]) -> str:
    """Generate ClickHouse CREATE TABLE SQL"""
    table_name = schema["name"]
    columns = schema["columns"]
    engine = schema.get("engine", "MergeTree")
    partition_by = schema.get("partition_by", "")
    order_by = schema.get("order_by", "")
    ttl = schema.get("ttl", "")
    settings = schema.get("settings", {})

    # Generate column definitions
    col_defs = []
    for col_name, col_type in columns.items():
        col_defs.append(f"    {col_name} {col_type}")

    # Build SQL
    sql = f"""
-- {schema.get('description', table_name)}
CREATE TABLE IF NOT EXISTS {table_name} (
{',\n'.join(col_defs)}
)
ENGINE = {engine}()
"""

    # Add partitioning
    if partition_by:
        sql += f"PARTITION BY {partition_by}\n"

    # Add ordering
    if order_by:
        sql += f"ORDER BY {order_by}\n"

    # Add TTL
    if ttl:
        sql += f"TTL {ttl}\n"

    # Add settings
    if settings:
        settings_str = ", ".join(f"{k} = {v}" for k, v in settings.items())
        sql += f"SETTINGS {settings_str}"

    sql += ";\n"

    return sql


def get_all_clickhouse_sql() -> str:
    """Generate SQL for all ClickHouse tables"""
    schemas = get_clickhouse_schemas()
    sql_parts = []

    # Add header
    sql_parts.append("""
-- ===========================================================================
-- ClickHouse Schema - Auto-generated from Python definitions
-- Generated: 2025-10-14
-- Version: 2.0
-- ===========================================================================

""")

    # Generate SQL for each table
    for schema in schemas:
        sql_parts.append(generate_create_table_sql(schema))
        sql_parts.append("\n")

    return "\n".join(sql_parts)
