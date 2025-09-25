"""
Standardized Market Data Classes
Based on real API output structures from Yahoo Finance, FRED, CoinGecko, etc.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MarketTick:
    """Market tick/price data - Yahoo Finance, Exchange Rate API format"""
    symbol: str = ""
    timestamp: int = 0  # Unix timestamp in milliseconds

    # OHLC Data (Yahoo Finance format)
    price_open: Optional[float] = None
    price_high: Optional[float] = None
    price_low: Optional[float] = None
    price_close: Optional[float] = None

    # Simplified price data
    bid: Optional[float] = None
    ask: Optional[float] = None
    last: Optional[float] = None  # Current/close price
    spread: Optional[float] = None

    # Volume and metadata
    volume: Optional[float] = None
    change_percent: Optional[float] = None

    # Source and quality
    source: str = ""
    data_type: str = "market_price"  # market_price, forex_rate
    session: Optional[str] = None

    # Raw data for debugging
    raw_metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp,
            'price_open': self.price_open,
            'price_high': self.price_high,
            'price_low': self.price_low,
            'price_close': self.price_close,
            'bid': self.bid,
            'ask': self.ask,
            'last': self.last,
            'spread': self.spread,
            'volume': self.volume,
            'change_percent': self.change_percent,
            'source': self.source,
            'data_type': self.data_type,
            'session': self.session,
            'raw_metadata': self.raw_metadata
        }


@dataclass
class EconomicIndicator:
    """Economic indicator data - FRED API format"""
    series_id: str = ""  # e.g., "CPIAUCSL"
    symbol: str = ""     # For consistency with other data types
    timestamp: int = 0   # Unix timestamp in milliseconds

    # FRED API actual structure
    date: str = ""       # "2025-08-01" from FRED
    value: Optional[float] = None  # Can be None/null in FRED

    # Metadata
    name: str = ""
    units: str = ""      # "Index 1982-84=100"
    frequency: str = ""  # "Monthly", "Quarterly"

    # Our enhancements
    source: str = "FRED"
    data_type: str = "economic_indicator"
    currency_impact: List[str] = field(default_factory=list)
    market_impact_score: float = 0.0
    session: Optional[str] = None

    # Raw FRED response
    raw_metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        return {
            'series_id': self.series_id,
            'symbol': self.symbol,
            'timestamp': self.timestamp,
            'date': self.date,
            'value': self.value,
            'name': self.name,
            'units': self.units,
            'frequency': self.frequency,
            'source': self.source,
            'data_type': self.data_type,
            'currency_impact': self.currency_impact,
            'market_impact_score': self.market_impact_score,
            'session': self.session,
            'raw_metadata': self.raw_metadata
        }


@dataclass
class CryptocurrencyData:
    """Cryptocurrency data - CoinGecko API format"""
    crypto_id: str = ""        # "bitcoin", "ethereum"
    symbol: str = ""           # "BTC", "ETH"
    timestamp: int = 0

    # CoinGecko actual structure
    price: float = 0.0         # Current price
    vs_currency: str = "USD"   # "usd", "eur"
    change_24h: Optional[float] = None    # 24h change percent
    market_cap: Optional[float] = None    # Market capitalization

    # Our enhancements
    source: str = "CoinGecko"
    data_type: str = "cryptocurrency"
    weight: float = 0.0        # For sentiment calculation
    risk_correlation: str = "medium"  # high, medium, low
    session: Optional[str] = None

    # Raw CoinGecko response
    raw_metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        return {
            'crypto_id': self.crypto_id,
            'symbol': self.symbol,
            'timestamp': self.timestamp,
            'price': self.price,
            'vs_currency': self.vs_currency,
            'change_24h': self.change_24h,
            'market_cap': self.market_cap,
            'source': self.source,
            'data_type': self.data_type,
            'weight': self.weight,
            'risk_correlation': self.risk_correlation,
            'session': self.session,
            'raw_metadata': self.raw_metadata
        }


@dataclass
class ExchangeRateData:
    """Exchange rate data - Exchange Rate API format"""
    base_currency: str = ""    # "USD"
    quote_currency: str = ""   # "EUR", "GBP"
    symbol: str = ""           # "EURUSD" for consistency
    timestamp: int = 0

    # Exchange Rate API actual structure
    rate: float = 0.0          # Exchange rate value

    # Our enhancements
    source: str = "ExchangeRateAPI"
    data_type: str = "exchange_rate"
    currency_type: str = "major"  # major, minor, exotic
    session: Optional[str] = None

    # Raw API response
    raw_metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        return {
            'base_currency': self.base_currency,
            'quote_currency': self.quote_currency,
            'symbol': self.symbol,
            'timestamp': self.timestamp,
            'rate': self.rate,
            'source': self.source,
            'data_type': self.data_type,
            'currency_type': self.currency_type,
            'session': self.session,
            'raw_metadata': self.raw_metadata
        }


@dataclass
class SentimentData:
    """Market sentiment data - Fear & Greed API format"""
    symbol: str = "FEAR_GREED_INDEX"  # For consistency
    timestamp: int = 0

    # Fear & Greed API actual structure
    index_value: int = 50              # 0-100
    value_classification: str = ""     # "Fear", "Greed", etc.

    # Our enhancements
    source: str = "Alternative.me"
    data_type: str = "market_sentiment"
    sentiment_level: str = "neutral"   # extreme_fear, fear, neutral, greed, extreme_greed
    contrarian_signal: str = "hold"    # buy, sell, hold
    signal_strength: float = 0.0       # 0-1
    market_phase: str = "trending"     # capitulation, accumulation, trending, distribution, euphoria
    session: Optional[str] = None

    # Raw API response
    raw_metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp,
            'index_value': self.index_value,
            'value_classification': self.value_classification,
            'source': self.source,
            'data_type': self.data_type,
            'sentiment_level': self.sentiment_level,
            'contrarian_signal': self.contrarian_signal,
            'signal_strength': self.signal_strength,
            'market_phase': self.market_phase,
            'session': self.session,
            'raw_metadata': self.raw_metadata
        }


@dataclass
class SessionData:
    """Market session data - Static config format"""
    symbol: str = "MARKET_SESSION"    # For consistency
    timestamp: int = 0

    # Session config actual structure
    current_sessions: List[str] = field(default_factory=list)  # ["London", "NewYork"]
    session_overlaps: List[str] = field(default_factory=list)  # ["London_NewYork"]
    volatility_multiplier: float = 1.0
    active_pairs: List[str] = field(default_factory=list)      # Most active pairs
    is_weekend: bool = False
    is_high_volatility: bool = False

    # Our enhancements
    source: str = "Static_Config"
    data_type: str = "market_session"

    def to_dict(self) -> dict:
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp,
            'current_sessions': self.current_sessions,
            'session_overlaps': self.session_overlaps,
            'volatility_multiplier': self.volatility_multiplier,
            'active_pairs': self.active_pairs,
            'is_weekend': self.is_weekend,
            'is_high_volatility': self.is_high_volatility,
            'source': self.source,
            'data_type': self.data_type
        }


# Unified Data Type for all collectors
@dataclass
class UnifiedMarketData:
    """
    Unified data structure for all external data sources
    Can represent any type of market data from any API
    """
    # Common fields (always present)
    symbol: str = ""           # EURUSD, CPI, BTC, FEAR_GREED_INDEX
    timestamp: int = 0         # Unix timestamp in milliseconds
    source: str = ""           # Yahoo, FRED, CoinGecko, etc.
    data_type: str = ""        # market_price, economic_indicator, cryptocurrency, etc.

    # Price data (for market ticks, forex, commodities)
    price_open: Optional[float] = None
    price_high: Optional[float] = None
    price_low: Optional[float] = None
    price_close: Optional[float] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    spread: Optional[float] = None
    volume: Optional[float] = None
    change_percent: Optional[float] = None

    # Economic data (for FRED indicators)
    date: Optional[str] = None          # "2025-08-01"
    value: Optional[float] = None       # Economic value
    units: Optional[str] = None         # "Index 1982-84=100"
    frequency: Optional[str] = None     # "Monthly"

    # Crypto data (for CoinGecko)
    crypto_id: Optional[str] = None     # "bitcoin"
    vs_currency: Optional[str] = None   # "USD"
    market_cap: Optional[float] = None

    # Exchange rate data
    base_currency: Optional[str] = None # "USD"
    quote_currency: Optional[str] = None # "EUR"
    rate: Optional[float] = None

    # Sentiment data (Fear & Greed)
    index_value: Optional[int] = None           # 0-100
    value_classification: Optional[str] = None  # "Fear", "Greed"
    sentiment_level: Optional[str] = None       # "extreme_fear"
    contrarian_signal: Optional[str] = None     # "buy", "sell"
    signal_strength: Optional[float] = None     # 0-1

    # Session data
    current_sessions: Optional[List[str]] = None
    volatility_multiplier: Optional[float] = None
    is_high_volatility: Optional[bool] = None

    # Metadata
    session: Optional[str] = None       # Current trading session
    currency_impact: Optional[List[str]] = None
    market_impact_score: Optional[float] = None

    # Event deduplication (NEW)
    event_id: Optional[str] = None      # External API event ID for UPSERT
    external_id: Optional[str] = None   # Alternative unique identifier

    # Raw data for debugging/future processing
    raw_metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        """Convert to dictionary, excluding None values"""
        data = {}
        for key, value in self.__dict__.items():
            if value is not None:
                data[key] = value
        return data

    def get_target_table(self) -> str:
        """Determine which table this data should go to based on usage patterns"""
        # HIGH FREQUENCY DATA → market_ticks (for pattern analysis)
        high_freq_types = {'market_price', 'forex_rate'}

        # LOW FREQUENCY DATA → market_context (for supporting context)
        low_freq_types = {
            'economic_indicator', 'cryptocurrency', 'exchange_rate',
            'market_sentiment', 'market_session'
        }

        if self.data_type in high_freq_types:
            return 'market_ticks'
        elif self.data_type in low_freq_types:
            return 'market_context'
        else:
            # Default to context for unknown types
            return 'market_context'

    def to_database_format(self) -> dict:
        """Convert to database-compatible format based on target table"""
        target_table = self.get_target_table()

        if target_table == 'market_ticks':
            return self._to_market_ticks_format()
        else:
            return self._to_market_context_format()

    def _to_market_ticks_format(self) -> dict:
        """Format for market_ticks table (pattern analysis)"""
        # Calculate change in pips for forex pairs
        change_pips = None
        if self.price_open and self.price_close:
            pip_multiplier = 10000 if 'JPY' not in self.symbol else 100
            change_pips = (self.price_close - self.price_open) * pip_multiplier

        db_data = {
            'symbol': self.symbol,
            'timeframe': 'M1',  # Default, should be determined by collector
            'timestamp': self.timestamp,
            'price_open': self.price_open or self.price_close,
            'price_high': self.price_high or self.price_close,
            'price_low': self.price_low or self.price_close,
            'price_close': self.price_close,
            'volume': int(self.volume or 0),
            'change_percent': self.change_percent,
            'change_pips': change_pips,
            'session': self.session,
            'is_high_volatility': self.is_high_volatility or False,
            'source': self.source,
            'data_quality': 'good'  # Default, should be determined by collector
        }

        # Remove None values
        return {k: v for k, v in db_data.items() if v is not None}

    def _to_market_context_format(self) -> dict:
        """Format for market_context table (supporting context)"""
        # Determine currency impact
        currency_impact = self.currency_impact or []
        if not currency_impact and self.base_currency:
            currency_impact = [self.base_currency]
            if self.quote_currency:
                currency_impact.append(self.quote_currency)

        # Determine forex impact
        forex_impact = None
        if self.data_type == 'economic_indicator' and 'USD' in currency_impact:
            forex_impact = 'usd_impact'
        elif self.data_type == 'market_sentiment':
            forex_impact = self.contrarian_signal or 'neutral'

        # Determine if this is forecast or actual data from metadata
        collection_phase = None
        if self.raw_metadata:
            collection_phase = self.raw_metadata.get("collection_phase")

        # Route values based on collection phase
        forecast_value = None
        actual_value = None
        if collection_phase == "forecast":
            forecast_value = self.value
        elif collection_phase == "actual":
            actual_value = self.value

        db_data = {
            'data_type': self.data_type,
            'symbol': self.symbol,
            'timestamp': self.timestamp,

            # Handle forecast vs actual values correctly
            'forecast_value': forecast_value,
            'actual_value': actual_value,
            'previous_value': self.raw_metadata.get("previous") if self.raw_metadata else None,

            # General value field (fallback)
            'value': self.value or self.index_value or self.rate or self.price_close,
            'value_text': self.value_classification or self.sentiment_level,

            'category': self._get_category(),
            'importance': self._get_importance(),
            'frequency': self.frequency or 'real-time',
            'units': self.units or self.vs_currency,
            'currency_impact': currency_impact,
            'forex_impact': forex_impact,
            'market_impact_score': self.market_impact_score or self.signal_strength or 0.5,
            'source': self.source,
            'reliability': 'high',  # Default

            # Event deduplication
            'event_id': self.event_id,           # For UPSERT deduplication
            'external_id': self.external_id,     # Alternative deduplication

            # Time status based on data completeness
            'time_status': 'historical' if actual_value is not None else 'scheduled',

            # Event timing
            'event_date': self.date,

            'metadata': self.to_dict()
        }

        # Remove None values
        return {k: v for k, v in db_data.items() if v is not None}

    def _get_category(self) -> str:
        """Get category based on data type and content"""
        if self.data_type == 'economic_indicator':
            if 'CPI' in self.symbol or 'inflation' in str(self.units).lower():
                return 'inflation'
            elif 'GDP' in self.symbol:
                return 'gdp'
            elif 'employment' in str(self.units).lower() or 'UNRATE' in self.symbol:
                return 'employment'
            else:
                return 'economic'
        elif self.data_type == 'cryptocurrency':
            return 'sentiment'
        elif self.data_type == 'market_sentiment':
            return 'sentiment'
        elif self.data_type == 'exchange_rate':
            return 'exchange_rate'
        elif self.data_type == 'market_session':
            return 'session'
        else:
            return 'general'

    def _get_importance(self) -> str:
        """Determine importance based on impact score and type"""
        if self.market_impact_score and self.market_impact_score >= 0.8:
            return 'high'
        elif self.market_impact_score and self.market_impact_score >= 0.5:
            return 'medium'
        elif self.data_type in ['economic_indicator', 'market_sentiment']:
            return 'high'  # Default high for these types
        else:
            return 'medium'