"""
ClickHouse Schema Type Hints
Type definitions for validation only - NOT for schema creation

⚠️ IMPORTANT: Schema Definition Source of Truth
   Full schema definitions are in SQL files:
   central-hub/shared/schemas/clickhouse/*.sql

   Those SQL files include:
   - Complete table definitions
   - Indexes and materialized views
   - TTL policies
   - Comments and documentation

   This Python module ONLY provides:
   - Type hints for validation
   - Column definitions for type checking
   - NOT for CREATE TABLE statements

   Schema creation is handled by:
   - ClickHouse Docker init scripts (/docker-entrypoint-initdb.d/)
   - SQL files are automatically executed on first start
"""
from typing import TypedDict, Literal, Optional
from datetime import datetime
from decimal import Decimal


# ============================================================================
# TYPE DEFINITIONS FOR VALIDATION
# ============================================================================

class TickData(TypedDict):
    """
    Type hints for ticks table - for validation only

    Full schema: central-hub/shared/schemas/clickhouse/01_ticks.sql
    """
    symbol: str
    timestamp: datetime
    timestamp_ms: int
    bid: Decimal
    ask: Decimal
    mid: Decimal
    spread: Decimal
    exchange: int
    source: Literal["polygon_websocket", "polygon_historical", "dukascopy_historical", "live_websocket"]
    event_type: str
    use_case: Optional[str]
    ingested_at: datetime


class AggregateData(TypedDict):
    """
    Type hints for aggregates table - for validation only

    Full schema: central-hub/shared/schemas/clickhouse/02_aggregates.sql
    """
    symbol: str
    timeframe: str
    timestamp: datetime
    timestamp_ms: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    vwap: Decimal
    range_pips: Decimal
    body_pips: Decimal
    start_time: datetime
    end_time: datetime
    source: str
    event_type: str
    indicators: str
    ingested_at: datetime


class EconomicCalendarData(TypedDict):
    """
    Type hints for external_economic_calendar table

    Full schema: central-hub/shared/schemas/clickhouse/03_external_economic_calendar.sql
    """
    event_time: datetime
    currency: str
    event_name: str
    impact: str
    forecast: Optional[Decimal]
    actual: Optional[Decimal]
    previous: Optional[Decimal]
    source: str
    ingested_at: datetime


class FredEconomicData(TypedDict):
    """
    Type hints for external_fred_economic table

    Full schema: central-hub/shared/schemas/clickhouse/04_external_fred_economic.sql
    """
    series_id: str
    observation_date: datetime
    value: Decimal
    series_title: str
    series_category: str
    source: str
    ingested_at: datetime


# ============================================================================
# VALIDATION HELPERS
# ============================================================================

def validate_tick_data(data: dict) -> bool:
    """
    Validate tick data structure before insert

    Args:
        data: Dictionary with tick data

    Returns:
        bool: True if valid

    Raises:
        ValueError: If validation fails
    """
    required_fields = ["symbol", "timestamp", "bid", "ask", "source"]

    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    return True


def validate_aggregate_data(data: dict) -> bool:
    """
    Validate aggregate data structure before insert

    Args:
        data: Dictionary with aggregate data

    Returns:
        bool: True if valid

    Raises:
        ValueError: If validation fails
    """
    required_fields = ["symbol", "timeframe", "timestamp", "open", "high", "low", "close", "volume", "source"]

    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    # Validate OHLC logic
    if not (data["low"] <= data["open"] <= data["high"] and
            data["low"] <= data["close"] <= data["high"]):
        raise ValueError(f"Invalid OHLC: H={data['high']}, L={data['low']}, O={data['open']}, C={data['close']}")

    return True


# ============================================================================
# TABLE NAMES (Constants)
# ============================================================================

TABLE_TICKS = "ticks"
TABLE_AGGREGATES = "aggregates"
TABLE_ECONOMIC_CALENDAR = "external_economic_calendar"
TABLE_FRED_ECONOMIC = "external_fred_economic"
TABLE_CRYPTO_SENTIMENT = "external_crypto_sentiment"
TABLE_FEAR_GREED_INDEX = "external_fear_greed_index"
TABLE_COMMODITY_PRICES = "external_commodity_prices"
TABLE_MARKET_SESSIONS = "external_market_sessions"


__all__ = [
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
]
