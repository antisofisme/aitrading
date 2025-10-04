"""
Data Models for Database Manager
Pydantic models for type safety and validation
"""
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime


class TickData(BaseModel):
    """
    Tick/Quote data model
    Real-time bid/ask prices for forex pairs
    """
    symbol: str = Field(..., description="Trading pair symbol (e.g., 'EUR/USD', 'XAU/USD')")
    timestamp: int = Field(..., description="Unix timestamp in milliseconds")
    timestamp_ms: int = Field(..., description="Unix timestamp in milliseconds (alias)")

    # Price data
    bid: float = Field(..., description="Bid price")
    ask: float = Field(..., description="Ask price")
    mid: Optional[float] = Field(None, description="Mid price (calculated)")
    spread: Optional[float] = Field(None, description="Spread in pips")

    # Metadata
    volume: Optional[float] = Field(None, description="Trade volume (if available)")
    source: str = Field(..., description="Data source (e.g., 'polygon', 'twelve-data', 'oanda')")
    exchange: Optional[int] = Field(None, description="Exchange ID (if applicable)")
    event_type: str = Field(default="quote", description="Event type")
    use_case: str = Field(default="", description="Use case category")

    @validator('timestamp_ms', always=True)
    def set_timestamp_ms(cls, v, values):
        """Ensure timestamp_ms is set from timestamp if not provided"""
        return v or values.get('timestamp')

    @validator('mid', always=True)
    def calculate_mid(cls, v, values):
        """Calculate mid price if not provided"""
        if v is None and 'bid' in values and 'ask' in values:
            return (values['bid'] + values['ask']) / 2
        return v

    @validator('spread', always=True)
    def calculate_spread(cls, v, values):
        """Calculate spread if not provided"""
        if v is None and 'bid' in values and 'ask' in values:
            return values['ask'] - values['bid']
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "EUR/USD",
                "timestamp": 1727996400000,
                "timestamp_ms": 1727996400000,
                "bid": 1.09551,
                "ask": 1.09553,
                "mid": 1.09552,
                "spread": 0.00002,
                "source": "polygon"
            }
        }


class CandleData(BaseModel):
    """
    OHLCV Candle data model
    Aggregated price bars for technical analysis
    """
    symbol: str = Field(..., description="Trading pair symbol")
    timeframe: str = Field(..., description="Timeframe (e.g., '1m', '5m', '1h', '1d')")
    timestamp: int = Field(..., description="Candle open time (Unix milliseconds)")
    timestamp_ms: int = Field(..., description="Candle open time (Unix milliseconds, alias)")

    # OHLCV data
    open: float = Field(..., description="Open price")
    high: float = Field(..., description="High price")
    low: float = Field(..., description="Low price")
    close: float = Field(..., description="Close price")
    volume: Optional[float] = Field(None, description="Volume (tick volume for forex)")

    # Additional metrics
    vwap: Optional[float] = Field(None, description="Volume Weighted Average Price")
    range_pips: Optional[float] = Field(None, description="High-Low range in pips")
    num_trades: Optional[int] = Field(None, description="Number of trades")

    # Time range
    start_time: Optional[int] = Field(None, description="Bar start time")
    end_time: Optional[int] = Field(None, description="Bar end time")

    # Metadata
    source: str = Field(..., description="Data source")
    event_type: str = Field(default="ohlcv", description="Event type")

    @validator('timestamp_ms', always=True)
    def set_timestamp_ms(cls, v, values):
        """Ensure timestamp_ms is set"""
        return v or values.get('timestamp')

    @validator('range_pips', always=True)
    def calculate_range_pips(cls, v, values):
        """Calculate range in pips if not provided"""
        if v is None and 'high' in values and 'low' in values:
            return (values['high'] - values['low']) * 10000  # Convert to pips
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "EUR/USD",
                "timeframe": "1m",
                "timestamp": 1727996400000,
                "timestamp_ms": 1727996400000,
                "open": 1.0850,
                "high": 1.0855,
                "low": 1.0848,
                "close": 1.0852,
                "volume": 15234,
                "vwap": 1.0851,
                "source": "polygon"
            }
        }


class EconomicEvent(BaseModel):
    """
    Economic event data model
    Fundamental data for news-based trading
    """
    event_id: str = Field(..., description="Unique event identifier")
    timestamp: int = Field(..., description="Event time (Unix milliseconds)")

    # Event details
    country: str = Field(..., description="Country code (e.g., 'US', 'EU', 'JP')")
    event_name: str = Field(..., description="Event name (e.g., 'CPI', 'NFP', 'GDP')")

    # Impact data
    actual: Optional[float] = Field(None, description="Actual value")
    forecast: Optional[float] = Field(None, description="Forecasted value")
    previous: Optional[float] = Field(None, description="Previous value")

    # Classification
    impact: str = Field(..., description="Impact level: 'high', 'medium', 'low'")
    currency_impact: List[str] = Field(default_factory=list, description="Affected currencies")

    # Metadata
    source: str = Field(..., description="Data source")

    @validator('impact')
    def validate_impact(cls, v):
        """Validate impact level"""
        if v not in ['high', 'medium', 'low']:
            raise ValueError("Impact must be 'high', 'medium', or 'low'")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "us_cpi_2024_01",
                "timestamp": 1727996400000,
                "country": "US",
                "event_name": "Consumer Price Index (CPI)",
                "actual": 3.2,
                "forecast": 3.1,
                "previous": 3.0,
                "impact": "high",
                "currency_impact": ["USD", "EUR"],
                "source": "economic_calendar"
            }
        }


class HealthCheckResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Overall status: 'healthy', 'degraded', 'unhealthy'")
    databases: dict = Field(default_factory=dict, description="Database health status")
    connection_pools: dict = Field(default_factory=dict, description="Connection pool status")
    cache: dict = Field(default_factory=dict, description="Cache status")
    timestamp: int = Field(..., description="Check timestamp")
