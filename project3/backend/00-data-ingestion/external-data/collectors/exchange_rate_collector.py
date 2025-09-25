"""
Exchange Rate API Collector - Real-time Currency Exchange Rates
Provides current exchange rates for 170+ currencies for cross-validation and arbitrage detection

FEATURES:
- 170+ currency exchange rates
- USD base with all major currencies
- Real-time rate updates
- Cross-validation for broker feeds
- Arbitrage opportunity detection
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
import logging

from .schemas.market_data_pb2 import MarketTick
from .session_market_config import MarketSessionsConfig

logger = logging.getLogger(__name__)


class ExchangeRateCollector:
    """
    Exchange Rate API collector for real-time currency rates
    Provides cross-validation data for forex trading
    """

    def __init__(self):
        self.base_url = "https://api.exchangerate-api.com/v4/latest"
        self.session = None
        self.market_sessions = MarketSessionsConfig()

        # Major currencies for forex trading
        self.major_currencies = [
            "EUR", "GBP", "JPY", "CHF", "AUD", "CAD", "NZD", "SEK",
            "NOK", "DKK", "PLN", "CZK", "HUF", "TRY", "ZAR", "MXN"
        ]

        # Cryptocurrency rates (if supported)
        self.crypto_currencies = [
            "BTC", "ETH", "LTC", "XRP", "ADA", "DOT"
        ]

        # Currency pair mapping for validation
        self.forex_pairs = {
            "EURUSD": {"base": "EUR", "quote": "USD"},
            "GBPUSD": {"base": "GBP", "quote": "USD"},
            "USDJPY": {"base": "USD", "quote": "JPY"},
            "USDCHF": {"base": "USD", "quote": "CHF"},
            "AUDUSD": {"base": "AUD", "quote": "USD"},
            "USDCAD": {"base": "USD", "quote": "CAD"},
            "NZDUSD": {"base": "NZD", "quote": "USD"},
            "EURGBP": {"base": "EUR", "quote": "GBP"},
            "EURJPY": {"base": "EUR", "quote": "JPY"},
            "GBPJPY": {"base": "GBP", "quote": "JPY"}
        }

        # Rate change thresholds for alerts
        self.change_thresholds = {
            "major": 0.005,      # 0.5% change
            "minor": 0.01,       # 1% change
            "exotic": 0.02       # 2% change
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

    async def exchange_rate_get_current_rates(
        self,
        base_currency: str = "USD"
    ) -> List[Dict]:
        """
        Get current exchange rates for all supported currencies

        Args:
            base_currency: Base currency for rates (default: USD)

        Returns:
            List of exchange rate dictionaries
        """
        try:
            url = f"{self.base_url}/{base_currency}"

            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return await self.exchange_rate_parse_response(base_currency, data)
                else:
                    logger.error(f"Exchange Rate API error: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Error fetching exchange rates: {e}")
            return []

    async def exchange_rate_parse_response(
        self,
        base_currency: str,
        data: Dict[str, Any]
    ) -> List[Dict]:
        """Parse Exchange Rate API response"""
        rates = []

        try:
            api_rates = data.get("rates", {})
            timestamp = data.get("time_last_updated", int(datetime.now().timestamp()))

            # Convert to milliseconds if needed
            if timestamp < 1e12:  # Assuming timestamp is in seconds
                timestamp = int(timestamp * 1000)

            # Current session info
            session_info = self.market_sessions.session_market_get_current_session(timestamp)
            current_session = session_info.get("current_sessions", ["Unknown"])[0] if session_info.get("current_sessions") else "Unknown"

            for currency, rate in api_rates.items():
                if rate and rate > 0:
                    rate_info = {
                        "base_currency": base_currency,
                        "quote_currency": currency,
                        "rate": float(rate),
                        "timestamp": timestamp,
                        "session": current_session,
                        "source": "ExchangeRateAPI",
                        "data_type": "exchange_rate",
                        "currency_type": self.exchange_rate_classify_currency(currency),
                        "pair_symbol": f"{base_currency}{currency}" if base_currency != currency else None
                    }
                    rates.append(rate_info)

        except Exception as e:
            logger.error(f"Error parsing exchange rate response: {e}")

        return rates

    def exchange_rate_classify_currency(self, currency: str) -> str:
        """Classify currency type for processing priority"""
        if currency in ["EUR", "GBP", "JPY", "CHF", "AUD", "CAD", "NZD"]:
            return "major"
        elif currency in ["SEK", "NOK", "DKK", "PLN", "CZK", "SGD", "HKD"]:
            return "minor"
        elif currency in self.crypto_currencies:
            return "crypto"
        else:
            return "exotic"

    async def exchange_rate_get_forex_pairs(self) -> List[MarketTick]:
        """
        Get exchange rates formatted as forex pairs (EURUSD, GBPUSD, etc.)

        Returns:
            List of MarketTick objects for major forex pairs
        """
        # Get USD-based rates
        usd_rates = await self.exchange_rate_get_current_rates("USD")

        # Get EUR-based rates for cross pairs
        eur_rates = await self.exchange_rate_get_current_rates("EUR")

        forex_ticks = []

        try:
            # Convert rates to forex pair format
            usd_rate_dict = {rate["quote_currency"]: rate for rate in usd_rates}
            eur_rate_dict = {rate["quote_currency"]: rate for rate in eur_rates}

            for pair_symbol, pair_config in self.forex_pairs.items():
                base = pair_config["base"]
                quote = pair_config["quote"]

                rate_value = None
                source_rates = None

                if base == "USD":
                    # USD base pairs (USDJPY, USDCHF, etc.)
                    if quote in usd_rate_dict:
                        rate_value = usd_rate_dict[quote]["rate"]
                        source_rates = usd_rates[0]  # Use timestamp from USD rates
                elif quote == "USD":
                    # USD quote pairs (EURUSD, GBPUSD, etc.)
                    if base in usd_rate_dict:
                        rate_value = 1.0 / usd_rate_dict[base]["rate"]  # Invert rate
                        source_rates = usd_rates[0]
                elif base == "EUR":
                    # EUR base pairs (EURGBP, EURJPY, etc.)
                    if quote in eur_rate_dict:
                        rate_value = eur_rate_dict[quote]["rate"]
                        source_rates = eur_rates[0] if eur_rates else None
                else:
                    # Cross pairs - calculate via USD
                    if base in usd_rate_dict and quote in usd_rate_dict:
                        base_usd = 1.0 / usd_rate_dict[base]["rate"]
                        quote_usd = 1.0 / usd_rate_dict[quote]["rate"]
                        rate_value = base_usd / quote_usd
                        source_rates = usd_rates[0]

                if rate_value and source_rates:
                    tick = MarketTick()
                    tick.symbol = pair_symbol
                    tick.timestamp = source_rates["timestamp"]
                    tick.last = rate_value
                    tick.bid = rate_value * 0.9999  # Approximate spread
                    tick.ask = rate_value * 1.0001
                    tick.spread = tick.ask - tick.bid
                    tick.volume = 0.0  # No volume data from exchange rates
                    tick.broker_source = "ExchangeRateAPI"
                    tick.data_quality = "Reference_Rate"

                    forex_ticks.append(tick)

        except Exception as e:
            logger.error(f"Error creating forex pairs: {e}")

        return forex_ticks

    async def exchange_rate_validate_broker_rates(
        self,
        broker_rates: List[MarketTick],
        tolerance: float = 0.001
    ) -> List[Dict]:
        """
        Validate broker rates against reference exchange rates

        Args:
            broker_rates: List of broker MarketTick objects
            tolerance: Acceptable difference (0.001 = 0.1%)

        Returns:
            List of validation results
        """
        reference_rates = await self.exchange_rate_get_forex_pairs()
        reference_dict = {tick.symbol: tick for tick in reference_rates}

        validation_results = []

        for broker_tick in broker_rates:
            symbol = broker_tick.symbol
            reference_tick = reference_dict.get(symbol)

            if not reference_tick:
                validation_results.append({
                    "symbol": symbol,
                    "status": "no_reference",
                    "broker_rate": broker_tick.last,
                    "reference_rate": None,
                    "difference": None,
                    "timestamp": broker_tick.timestamp
                })
                continue

            # Calculate difference
            broker_rate = broker_tick.last
            reference_rate = reference_tick.last
            difference = abs(broker_rate - reference_rate) / reference_rate

            status = "valid" if difference <= tolerance else "deviation"

            validation_results.append({
                "symbol": symbol,
                "status": status,
                "broker_rate": broker_rate,
                "reference_rate": reference_rate,
                "difference_percent": difference * 100,
                "tolerance_percent": tolerance * 100,
                "broker_source": broker_tick.broker_source,
                "timestamp": broker_tick.timestamp
            })

        return validation_results

    async def exchange_rate_detect_arbitrage(
        self,
        min_opportunity: float = 0.001
    ) -> List[Dict]:
        """
        Detect potential arbitrage opportunities between currency pairs

        Args:
            min_opportunity: Minimum arbitrage opportunity (0.001 = 0.1%)

        Returns:
            List of arbitrage opportunities
        """
        try:
            rates = await self.exchange_rate_get_current_rates("USD")
            rate_dict = {rate["quote_currency"]: rate["rate"] for rate in rates}

            arbitrage_opportunities = []

            # Check triangular arbitrage for major currencies
            triangular_sets = [
                ("EUR", "GBP", "USD"),
                ("EUR", "JPY", "USD"),
                ("GBP", "JPY", "USD"),
                ("AUD", "NZD", "USD"),
                ("EUR", "CHF", "USD")
            ]

            for base, intermediate, quote in triangular_sets:
                if base in rate_dict and intermediate in rate_dict and quote == "USD":
                    # Calculate direct rate vs cross rate
                    direct_rate = 1.0 / rate_dict[base]  # e.g., EURUSD
                    cross_rate = (1.0 / rate_dict[intermediate]) / (1.0 / rate_dict[base])  # via intermediate

                    difference = abs(direct_rate - cross_rate) / direct_rate

                    if difference >= min_opportunity:
                        arbitrage_opportunities.append({
                            "type": "triangular",
                            "currencies": [base, intermediate, quote],
                            "direct_rate": direct_rate,
                            "cross_rate": cross_rate,
                            "opportunity_percent": difference * 100,
                            "timestamp": rates[0]["timestamp"] if rates else int(datetime.now().timestamp() * 1000)
                        })

        except Exception as e:
            logger.error(f"Error detecting arbitrage: {e}")

        return arbitrage_opportunities

    async def exchange_rate_get_major_currencies(self) -> List[Dict]:
        """Get rates for major trading currencies only"""
        all_rates = await self.exchange_rate_get_current_rates("USD")
        major_rates = [
            rate for rate in all_rates
            if rate["currency_type"] == "major"
        ]
        return major_rates

    async def exchange_rate_monitor_changes(
        self,
        previous_rates: List[Dict],
        current_rates: List[Dict]
    ) -> List[Dict]:
        """
        Monitor significant rate changes between two rate sets

        Args:
            previous_rates: Previous rate data
            current_rates: Current rate data

        Returns:
            List of significant changes
        """
        changes = []

        if not previous_rates:
            return changes

        # Create lookup dictionaries
        prev_dict = {f"{r['base_currency']}{r['quote_currency']}": r for r in previous_rates}
        curr_dict = {f"{r['base_currency']}{r['quote_currency']}": r for r in current_rates}

        for pair_key, current_rate in curr_dict.items():
            previous_rate = prev_dict.get(pair_key)

            if not previous_rate:
                continue

            # Calculate percentage change
            prev_value = previous_rate["rate"]
            curr_value = current_rate["rate"]
            change_percent = abs(curr_value - prev_value) / prev_value

            # Check against thresholds
            currency_type = current_rate["currency_type"]
            threshold = self.change_thresholds.get(currency_type, 0.01)

            if change_percent >= threshold:
                changes.append({
                    "pair": pair_key,
                    "currency_type": currency_type,
                    "previous_rate": prev_value,
                    "current_rate": curr_value,
                    "change_percent": change_percent * 100,
                    "threshold_percent": threshold * 100,
                    "direction": "up" if curr_value > prev_value else "down",
                    "timestamp": current_rate["timestamp"]
                })

        return changes

    def exchange_rate_get_supported_currencies(self) -> Dict[str, List[str]]:
        """Get list of supported currencies by category"""
        return {
            "major": ["EUR", "GBP", "JPY", "CHF", "AUD", "CAD", "NZD"],
            "minor": ["SEK", "NOK", "DKK", "PLN", "CZK", "SGD", "HKD"],
            "crypto": self.crypto_currencies,
            "forex_pairs": list(self.forex_pairs.keys()),
            "total_supported": "170+"
        }


# Usage Example
async def main():
    """Example usage of Exchange Rate Collector"""
    async with ExchangeRateCollector() as collector:

        # Get current exchange rates
        print("Getting current exchange rates...")
        rates = await collector.exchange_rate_get_current_rates("USD")
        print(f"Retrieved {len(rates)} exchange rates")

        # Show major currency rates
        major_rates = [r for r in rates if r["currency_type"] == "major"]
        print("\nMajor currency rates:")
        for rate in major_rates[:5]:
            print(f"USD/{rate['quote_currency']}: {rate['rate']}")

        # Get forex pairs format
        print("\nGetting forex pairs...")
        forex_pairs = await collector.exchange_rate_get_forex_pairs()
        for pair in forex_pairs[:5]:
            print(f"{pair.symbol}: {pair.last} (spread: {pair.spread:.5f})")

        # Detect arbitrage opportunities
        print("\nChecking for arbitrage opportunities...")
        arbitrage = await collector.exchange_rate_detect_arbitrage()
        for opp in arbitrage:
            print(f"Arbitrage in {opp['currencies']}: {opp['opportunity_percent']:.3f}%")

        # Show supported currencies
        supported = collector.exchange_rate_get_supported_currencies()
        print(f"\nSupported currencies: {supported['total_supported']}")
        print(f"Major pairs: {len(supported['forex_pairs'])}")


if __name__ == "__main__":
    asyncio.run(main())