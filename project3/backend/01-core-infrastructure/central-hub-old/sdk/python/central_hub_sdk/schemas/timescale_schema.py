"""
TimescaleDB Schema Definitions
PostgreSQL + TimescaleDB extensions for time-series data
"""
from typing import Dict, List, Any


# Reusable column definitions
COMMON_COLUMNS = {
    "timestamp_ms": "BIGINT NOT NULL",
    "ingested_at": "TIMESTAMPTZ DEFAULT NOW()",
    "tenant_id": "VARCHAR(50) NOT NULL",
}


def get_timescale_schemas() -> List[Dict[str, Any]]:
    """
    Get all TimescaleDB table schemas

    Returns:
        List of schema definitions with SQL generation
    """
    return [
        MARKET_TICKS_SCHEMA,
        MARKET_CANDLES_SCHEMA,
        MARKET_CONTEXT_SCHEMA,
    ]


# ============================================================================
# MARKET TICKS TABLE
# ============================================================================

MARKET_TICKS_SCHEMA = {
    "name": "market_ticks",
    "description": "Real-time market tick data (bid/ask/mid/spread)",
    "version": "1.0",
    "hypertable": {
        "time_column": "time",
        "chunk_interval": "1 day"
    },
    "columns": {
        "time": "TIMESTAMPTZ NOT NULL",
        "tick_id": "UUID DEFAULT gen_random_uuid()",
        "tenant_id": COMMON_COLUMNS["tenant_id"],
        "symbol": "VARCHAR(20) NOT NULL",
        "bid": "DECIMAL(18, 5) NOT NULL",
        "ask": "DECIMAL(18, 5) NOT NULL",
        "mid": "DECIMAL(18, 5) NOT NULL",
        "spread": "DECIMAL(10, 5) NOT NULL",
        "exchange": "VARCHAR(50)",
        "source": "VARCHAR(50) NOT NULL",
        "event_type": "VARCHAR(20) NOT NULL",
        "use_case": "VARCHAR(50) DEFAULT ''",
        "timestamp_ms": COMMON_COLUMNS["timestamp_ms"],
        "ingested_at": COMMON_COLUMNS["ingested_at"],
    },
    "primary_key": ["time", "tenant_id", "symbol", "tick_id"],
    "indexes": [
        {
            "name": "idx_market_ticks_symbol_time",
            "columns": ["symbol", "time DESC"],
            "method": "BTREE"
        },
        {
            "name": "idx_market_ticks_source",
            "columns": ["source"],
            "method": "BTREE"
        },
    ],
    "partition_by": "time",
}


# ============================================================================
# MARKET CANDLES TABLE
# ============================================================================

MARKET_CANDLES_SCHEMA = {
    "name": "candles",
    "description": "OHLCV candle data with technical indicators",
    "version": "1.0",
    "hypertable": {
        "time_column": "timestamp",
        "chunk_interval": "7 days"
    },
    "columns": {
        "symbol": "VARCHAR(20) NOT NULL",
        "timeframe": "VARCHAR(10) NOT NULL",
        "timestamp": "TIMESTAMPTZ NOT NULL",
        "timestamp_ms": COMMON_COLUMNS["timestamp_ms"],
        "open": "DECIMAL(18, 5) NOT NULL",
        "high": "DECIMAL(18, 5) NOT NULL",
        "low": "DECIMAL(18, 5) NOT NULL",
        "close": "DECIMAL(18, 5) NOT NULL",
        "volume": "BIGINT DEFAULT 0",
        "vwap": "DECIMAL(18, 5)",
        "range_pips": "DECIMAL(10, 5)",
        "body_pips": "DECIMAL(10, 5)",
        "num_trades": "INTEGER",
        "start_time": "TIMESTAMPTZ",
        "end_time": "TIMESTAMPTZ",
        "source": "VARCHAR(50) NOT NULL",
        "event_type": "VARCHAR(20) NOT NULL",
        "ingested_at": COMMON_COLUMNS["ingested_at"],
    },
    "primary_key": ["timestamp", "symbol", "timeframe"],
    "indexes": [
        {
            "name": "idx_candles_symbol_timeframe",
            "columns": ["symbol", "timeframe", "timestamp DESC"],
            "method": "BTREE"
        },
    ],
}


# ============================================================================
# MARKET CONTEXT TABLE
# ============================================================================

MARKET_CONTEXT_SCHEMA = {
    "name": "market_context",
    "description": "Market sentiment and context data",
    "version": "1.0",
    "hypertable": {
        "time_column": "timestamp",
        "chunk_interval": "30 days"
    },
    "columns": {
        "timestamp": "TIMESTAMPTZ NOT NULL",
        "context_type": "VARCHAR(50) NOT NULL",
        "symbol": "VARCHAR(20)",
        "sentiment_score": "DECIMAL(5, 2)",
        "volatility_index": "DECIMAL(10, 5)",
        "market_phase": "VARCHAR(20)",
        "metadata": "JSONB",
        "source": "VARCHAR(50) NOT NULL",
        "ingested_at": COMMON_COLUMNS["ingested_at"],
    },
    "primary_key": ["timestamp", "context_type"],
    "indexes": [
        {
            "name": "idx_market_context_type",
            "columns": ["context_type", "timestamp DESC"],
            "method": "BTREE"
        },
    ],
}


# ============================================================================
# SQL GENERATION FUNCTIONS
# ============================================================================

def generate_create_table_sql(schema: Dict[str, Any]) -> str:
    """
    Generate CREATE TABLE SQL from schema definition

    Args:
        schema: Table schema dictionary

    Returns:
        SQL CREATE TABLE statement
    """
    table_name = schema["name"]
    columns = schema["columns"]
    primary_key = schema.get("primary_key", [])

    # Generate column definitions
    col_defs = []
    for col_name, col_type in columns.items():
        col_defs.append(f"    {col_name} {col_type}")

    # Add primary key
    if primary_key:
        pk_cols = ", ".join(primary_key)
        col_defs.append(f"    PRIMARY KEY ({pk_cols})")

    # Build SQL
    sql = f"""
-- {schema.get('description', table_name)}
CREATE TABLE IF NOT EXISTS {table_name} (
{',\n'.join(col_defs)}
);
"""

    return sql


def generate_create_hypertable_sql(schema: Dict[str, Any]) -> str:
    """
    Generate TimescaleDB hypertable creation SQL

    Args:
        schema: Table schema dictionary

    Returns:
        SQL SELECT create_hypertable() statement
    """
    if "hypertable" not in schema:
        return ""

    table_name = schema["name"]
    time_column = schema["hypertable"]["time_column"]
    chunk_interval = schema["hypertable"]["chunk_interval"]

    sql = f"""
-- Convert {table_name} to hypertable
SELECT create_hypertable(
    '{table_name}',
    '{time_column}',
    chunk_time_interval => INTERVAL '{chunk_interval}',
    if_not_exists => TRUE
);
"""

    return sql


def generate_create_indexes_sql(schema: Dict[str, Any]) -> str:
    """
    Generate CREATE INDEX SQL statements

    Args:
        schema: Table schema dictionary

    Returns:
        SQL CREATE INDEX statements
    """
    if "indexes" not in schema:
        return ""

    table_name = schema["name"]
    indexes = schema["indexes"]

    sql_statements = []
    for index in indexes:
        index_name = index["name"]
        columns = ", ".join(index["columns"])
        method = index.get("method", "BTREE")

        sql = f"""
CREATE INDEX IF NOT EXISTS {index_name}
    ON {table_name} USING {method} ({columns});
"""
        sql_statements.append(sql)

    return "\n".join(sql_statements)


def generate_full_schema_sql(schema: Dict[str, Any]) -> str:
    """
    Generate complete schema SQL (table + hypertable + indexes)

    Args:
        schema: Table schema dictionary

    Returns:
        Complete SQL statements
    """
    sql_parts = [
        generate_create_table_sql(schema),
        generate_create_hypertable_sql(schema),
        generate_create_indexes_sql(schema),
    ]

    return "\n".join(part for part in sql_parts if part)


def get_all_timescale_sql() -> str:
    """
    Generate SQL for all TimescaleDB tables

    Returns:
        Complete SQL script
    """
    schemas = get_timescale_schemas()
    sql_parts = []

    # Add header
    sql_parts.append("""
-- ===========================================================================
-- TimescaleDB Schema - Auto-generated from Python definitions
-- Generated: 2025-10-14
-- Version: 2.0
-- ===========================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS timescaledb;

""")

    # Generate SQL for each table
    for schema in schemas:
        sql_parts.append(generate_full_schema_sql(schema))
        sql_parts.append("\n")

    return "\n".join(sql_parts)
