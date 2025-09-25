"""
Yahoo Finance Commodity & Forex Collector
Collects real-time and historical data for 24 instruments (Major/Minor pairs + Gold + Oil)

FEATURES:
- 22 forex pairs (Major + Minor)
- 2 commodities (Gold XAUUSD, Oil USOIL)
- Real-time prices with OHLC data
- Volume and volatility metrics
- Batch processing for multiple instruments
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import logging

from .schemas.market_data_pb2 import MarketTick
from .session_market_config import MarketSessionsConfig

logger = logging.getLogger(__name__)


class YahooFinanceCollector:
    """
    Yahoo Finance collector for forex pairs and commodities
    Handles 24 instruments with batch processing capabilities
    """

    def __init__(self):
        self.base_url = "https://query1.finance.yahoo.com/v8/finance/chart"
        self.session = None
        self.market_sessions = MarketSessionsConfig()

        # 24 instruments mapping: Internal symbol -> Yahoo symbol
        self.instruments = {
            # Major Pairs (8)
            "EURUSD": "EURUSD=X",
            "GBPUSD": "GBPUSD=X",
            "USDJPY": "USDJPY=X",
            "USDCHF": "USDCHF=X",
            "AUDUSD": "AUDUSD=X",
            "USDCAD": "USDCAD=X",
            "NZDUSD": "NZDUSD=X",
            "EURGBP": "EURGBP=X",

            # Minor Pairs (14)
            "EURJPY": "EURJPY=X",
            "GBPJPY": "GBPJPY=X",
            "EURAUD": "EURAUD=X",
            "EURCAD": "EURCAD=X",
            "EURNZD": "EURNZD=X",
            "GBPAUD": "GBPAUD=X",
            "GBPCAD": "GBPCAD=X",
            "AUDCAD": "AUDCAD=X",
            "AUDJPY": "AUDJPY=X",
            "CADJPY": "CADJPY=X",
            "CHFJPY": "CHFJPY=X",
            "NZDJPY": "NZDJPY=X",
            "AUDNZD": "AUDNZD=X",
            "CADCHF": "CADCHF=X",

            # Commodities (2)
            "XAUUSD": "GC=F",      # Gold Futures
            "USOIL": "CL=F"        # Crude Oil Futures
        }

        # Instrument categories for processing
        self.categories = {
            "major_pairs": ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD", "EURGBP"],
            "minor_pairs": ["EURJPY", "GBPJPY", "EURAUD", "EURCAD", "EURNZD", "GBPAUD", "GBPCAD", "AUDCAD", "AUDJPY", "CADJPY", "CHFJPY", "NZDJPY", "AUDNZD", "CADCHF"],
            "commodities": ["XAUUSD", "USOIL"]
        }

        # Data validation ranges
        self.validation_ranges = {
            # Forex pairs (reasonable price ranges)
            "EURUSD": {"min": 0.5000, "max": 2.0000},
            "GBPUSD": {"min": 0.5000, "max": 2.5000},
            "USDJPY": {"min": 50.00, "max": 200.00},
            "USDCHF": {"min": 0.5000, "max": 2.0000},
            "AUDUSD": {"min": 0.3000, "max": 1.5000},
            "USDCAD": {"min": 0.8000, "max": 2.0000},

            # Commodities
            "XAUUSD": {"min": 1000.0, "max": 5000.0},    # Gold
            "USOIL": {"min": 10.0, "max": 200.0}         # Oil
        }

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def commodity_yahoo_get_current_prices(
        self,
        symbols: Optional[List[str]] = None,
        interval: str = "1m"
    ) -> List[MarketTick]:
        """
        Get current prices for specified instruments

        Args:
            symbols: List of internal symbols (e.g., ["EURUSD", "XAUUSD"])
            interval: Data interval (1m, 5m, 1h, 1d)

        Returns:
            List of MarketTick objects with current prices
        """
        if symbols is None:
            symbols = list(self.instruments.keys())

        all_ticks = []

        # Process instruments in batches to avoid rate limits
        batch_size = 5
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            batch_ticks = await self.commodity_yahoo_process_batch(batch, interval)
            all_ticks.extend(batch_ticks)

            # Rate limiting
            await asyncio.sleep(0.1)

        return all_ticks

    async def commodity_yahoo_process_batch(
        self,
        symbols: List[str],
        interval: str
    ) -> List[MarketTick]:
        """Process a batch of symbols concurrently"""
        tasks = []

        for symbol in symbols:
            task = self.commodity_yahoo_get_instrument_data(symbol, interval)
            tasks.append(task)

        # Execute batch concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten results and filter out exceptions
        all_ticks = []
        for result in results:
            if isinstance(result, list):
                all_ticks.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Batch processing error: {result}")

        return all_ticks

    async def commodity_yahoo_get_instrument_data(
        self,
        symbol: str,
        interval: str = "1m",
        range_period: str = "1d"
    ) -> List[MarketTick]:
        """
        Get data for a single instrument

        Args:
            symbol: Internal symbol (e.g., "EURUSD")
            interval: Data interval
            range_period: Time range

        Returns:
            List of MarketTick objects
        """
        try:
            yahoo_symbol = self.instruments.get(symbol)
            if not yahoo_symbol:
                logger.warning(f"Unknown symbol: {symbol}")
                return []

            params = {
                "interval": interval,
                "range": range_period,
                "includePrePost": "false"
            }

            url = f"{self.base_url}/{yahoo_symbol}"

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return await self.commodity_yahoo_parse_response(symbol, data)
                else:
                    logger.error(f"Yahoo Finance API error for {symbol}: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Error fetching {symbol} data: {e}")
            return []

    async def commodity_yahoo_parse_response(
        self,
        symbol: str,
        data: Dict[str, Any]
    ) -> List[MarketTick]:
        """Parse Yahoo Finance API response to MarketTick objects"""
        ticks = []

        try:
            chart = data.get("chart", {})
            result = chart.get("result", [])

            if not result:
                logger.warning(f"No data in Yahoo response for {symbol}")
                return []

            result_data = result[0]

            # Extract metadata
            meta = result_data.get("meta", {})
            currency = meta.get("currency", "USD")
            regular_market_price = meta.get("regularMarketPrice")

            # Extract timestamps and OHLC data
            timestamps = result_data.get("timestamp", [])
            indicators = result_data.get("indicators", {})
            quote = indicators.get("quote", [{}])[0]

            opens = quote.get("open", [])
            highs = quote.get("high", [])
            lows = quote.get("low", [])
            closes = quote.get("close", [])
            volumes = quote.get("volume", [])

            # Current session info
            session_info = self.market_sessions.session_market_get_current_session()
            current_session = session_info.get("current_sessions", ["Unknown"])[0] if session_info.get("current_sessions") else "Unknown"

            # Process each data point
            for i in range(len(timestamps)):
                if i >= len(closes) or closes[i] is None:
                    continue

                # Validate price data
                close_price = float(closes[i])
                if not self.commodity_yahoo_validate_price(symbol, close_price):
                    continue

                tick = MarketTick()
                tick.symbol = symbol
                tick.timestamp = int(timestamps[i] * 1000)  # Convert to milliseconds

                # OHLC data
                tick.last = close_price  # Use close as 'last' price
                tick.bid = close_price * 0.9999  # Approximate bid (close - small spread)
                tick.ask = close_price * 1.0001  # Approximate ask (close + small spread)
                tick.spread = tick.ask - tick.bid

                # Volume (if available)
                if i < len(volumes) and volumes[i] is not None:
                    tick.volume = float(volumes[i])
                else:
                    tick.volume = 0.0

                # Additional metadata
                tick.broker_source = "Yahoo_Finance"
                tick.data_quality = "Market_Data"

                ticks.append(tick)

        except Exception as e:
            logger.error(f"Error parsing Yahoo data for {symbol}: {e}")

        return ticks

    def commodity_yahoo_validate_price(self, symbol: str, price: float) -> bool:
        """Validate price is within reasonable ranges"""
        if price <= 0:
            return False

        # Check specific symbol ranges
        ranges = self.validation_ranges.get(symbol)
        if ranges:
            return ranges["min"] <= price <= ranges["max"]

        # Default validation for unknown symbols
        return 0.0001 <= price <= 10000.0

    async def commodity_yahoo_get_historical_data(
        self,
        symbol: str,
        period: str = "1mo",
        interval: str = "1d"
    ) -> List[MarketTick]:
        """
        Get historical data for a single instrument

        Args:
            symbol: Internal symbol
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)

        Returns:
            List of historical MarketTick objects
        """
        return await self.commodity_yahoo_get_instrument_data(symbol, interval, period)

    async def commodity_yahoo_get_major_pairs(self) -> List[MarketTick]:
        """Get current prices for major currency pairs only"""
        return await self.commodity_yahoo_get_current_prices(self.categories["major_pairs"])

    async def commodity_yahoo_get_commodities(self) -> List[MarketTick]:
        """Get current prices for commodities (Gold, Oil) only"""
        return await self.commodity_yahoo_get_current_prices(self.categories["commodities"])

    async def commodity_yahoo_get_volatility_data(self) -> List[Dict]:
        """
        Get VIX and other volatility indicators

        Returns:
            List of volatility data dictionaries
        """
        volatility_symbols = {
            "VIX": "^VIX",      # CBOE Volatility Index
            "VXN": "^VXN",      # NASDAQ-100 Volatility Index
            "RVX": "^RVX"       # Russell 2000 Volatility Index
        }

        volatility_data = []

        try:
            for symbol, yahoo_symbol in volatility_symbols.items():
                params = {
                    "interval": "1d",
                    "range": "5d"
                }

                url = f"{self.base_url}/{yahoo_symbol}"

                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        parsed_data = await self.commodity_yahoo_parse_volatility_response(symbol, data)
                        volatility_data.extend(parsed_data)

        except Exception as e:
            logger.error(f"Error fetching volatility data: {e}")

        return volatility_data

    async def commodity_yahoo_parse_volatility_response(
        self,
        symbol: str,
        data: Dict[str, Any]
    ) -> List[Dict]:
        """Parse volatility index data"""
        volatility_points = []

        try:
            result = data.get("chart", {}).get("result", [])
            if not result:
                return []

            result_data = result[0]
            timestamps = result_data.get("timestamp", [])
            quote = result_data.get("indicators", {}).get("quote", [{}])[0]
            closes = quote.get("close", [])

            for i in range(len(timestamps)):
                if i < len(closes) and closes[i] is not None:
                    volatility_points.append({
                        "symbol": symbol,
                        "value": float(closes[i]),
                        "timestamp": int(timestamps[i] * 1000),
                        "data_type": "volatility_index",
                        "source": "Yahoo_Finance"
                    })

        except Exception as e:
            logger.error(f"Error parsing volatility data for {symbol}: {e}")

        return volatility_points

    def commodity_yahoo_get_supported_instruments(self) -> Dict[str, List[str]]:
        """Get list of all supported instruments by category"""
        return {
            "all_symbols": list(self.instruments.keys()),
            "major_pairs": self.categories["major_pairs"],
            "minor_pairs": self.categories["minor_pairs"],
            "commodities": self.categories["commodities"],
            "total_count": len(self.instruments)
        }


# Usage Example
async def main():
    """Example usage of Yahoo Finance Collector"""
    async with YahooFinanceCollector() as collector:

        # Get current prices for all 24 instruments
        print("Getting all 24 instruments...")
        all_data = await collector.commodity_yahoo_get_current_prices()
        print(f"Retrieved {len(all_data)} data points")

        # Show sample data
        for tick in all_data[:5]:
            print(f"{tick.symbol}: {tick.last} (spread: {tick.spread:.5f})")

        # Get major pairs only
        print("\nGetting major pairs...")
        major_pairs = await collector.commodity_yahoo_get_major_pairs()
        print(f"Major pairs: {len(major_pairs)} data points")

        # Get commodities
        print("\nGetting commodities...")
        commodities = await collector.commodity_yahoo_get_commodities()
        for tick in commodities:
            print(f"{tick.symbol}: ${tick.last}")

        # Get volatility data
        print("\nGetting volatility data...")
        volatility = await collector.commodity_yahoo_get_volatility_data()
        for vol in volatility:
            print(f"{vol['symbol']}: {vol['value']}")

        # Show supported instruments
        supported = collector.commodity_yahoo_get_supported_instruments()
        print(f"\nTotal supported instruments: {supported['total_count']}")


if __name__ == "__main__":
    asyncio.run(main())