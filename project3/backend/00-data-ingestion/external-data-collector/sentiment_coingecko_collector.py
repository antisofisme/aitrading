"""
CoinGecko Cryptocurrency Collector - Crypto Market Sentiment
Provides Bitcoin, Ethereum and other cryptocurrency prices for risk-on/risk-off sentiment analysis

FEATURES:
- Major cryptocurrency prices (BTC, ETH, ADA, DOT, SOL)
- Multiple fiat currencies (USD, EUR, BTC dominance)
- Market sentiment indicators via crypto correlation
- Risk-on/Risk-off signals for forex trading
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
import logging

from .session_market_config import MarketSessionsConfig

logger = logging.getLogger(__name__)


class CoinGeckoCollector:
    """
    CoinGecko collector for cryptocurrency prices
    Used for market sentiment analysis in forex trading
    """

    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.session = None
        self.market_sessions = MarketSessionsConfig()

        # Major cryptocurrencies for sentiment analysis
        self.crypto_symbols = {
            "bitcoin": {
                "symbol": "BTC",
                "weight": 0.6,        # Highest weight for market sentiment
                "risk_correlation": "high"
            },
            "ethereum": {
                "symbol": "ETH",
                "weight": 0.25,
                "risk_correlation": "high"
            },
            "cardano": {
                "symbol": "ADA",
                "weight": 0.05,
                "risk_correlation": "medium"
            },
            "polkadot": {
                "symbol": "DOT",
                "weight": 0.05,
                "risk_correlation": "medium"
            },
            "solana": {
                "symbol": "SOL",
                "weight": 0.05,
                "risk_correlation": "medium"
            }
        }

        # Supported fiat currencies
        self.fiat_currencies = ["usd", "eur", "gbp", "jpy", "cad", "aud"]

        # Sentiment thresholds based on Bitcoin price levels
        self.sentiment_thresholds = {
            "extreme_greed": 100000,    # BTC > $100k
            "greed": 80000,             # BTC > $80k
            "neutral": 50000,           # BTC $30k-$50k
            "fear": 30000,              # BTC < $30k
            "extreme_fear": 20000       # BTC < $20k
        }

        # Risk correlation with traditional markets
        self.risk_correlations = {
            "high_risk_on": ["bitcoin", "ethereum"],
            "medium_risk_on": ["cardano", "polkadot", "solana"],
            "safe_haven": []  # Generally no crypto safe havens
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

    async def sentiment_coingecko_get_current_prices(
        self,
        vs_currencies: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Get current cryptocurrency prices

        Args:
            vs_currencies: List of fiat currencies (default: ["usd", "eur"])

        Returns:
            List of cryptocurrency price dictionaries
        """
        if vs_currencies is None:
            vs_currencies = ["usd", "eur"]

        try:
            # Prepare API parameters
            crypto_ids = ",".join(self.crypto_symbols.keys())
            currencies = ",".join(vs_currencies)

            params = {
                "ids": crypto_ids,
                "vs_currencies": currencies,
                "include_market_cap": "true",
                "include_24hr_change": "true"
            }

            url = f"{self.base_url}/simple/price"

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return await self.sentiment_coingecko_parse_price_response(data, vs_currencies)
                else:
                    logger.error(f"CoinGecko API error: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Error fetching CoinGecko prices: {e}")
            return []

    async def sentiment_coingecko_parse_price_response(
        self,
        data: Dict[str, Any],
        vs_currencies: List[str]
    ) -> List[Dict]:
        """Parse CoinGecko price response"""
        crypto_data = []
        timestamp = int(datetime.now().timestamp() * 1000)

        # Current session info
        session_info = self.market_sessions.session_market_get_current_session(timestamp)
        current_session = session_info.get("current_sessions", ["Unknown"])[0] if session_info.get("current_sessions") else "Unknown"

        try:
            for crypto_id, price_data in data.items():
                crypto_config = self.crypto_symbols.get(crypto_id, {})
                symbol = crypto_config.get("symbol", crypto_id.upper())

                for currency in vs_currencies:
                    price_key = currency
                    change_key = f"{currency}_24h_change"
                    market_cap_key = f"{currency}_market_cap"

                    if price_key in price_data:
                        crypto_point = {
                            "crypto_id": crypto_id,
                            "symbol": symbol,
                            "price": float(price_data[price_key]),
                            "vs_currency": currency.upper(),
                            "change_24h": price_data.get(change_key, 0.0),
                            "market_cap": price_data.get(market_cap_key, 0),
                            "timestamp": timestamp,
                            "session": current_session,
                            "source": "CoinGecko",
                            "data_type": "cryptocurrency",
                            "weight": crypto_config.get("weight", 0.01),
                            "risk_correlation": crypto_config.get("risk_correlation", "low")
                        }
                        crypto_data.append(crypto_point)

        except Exception as e:
            logger.error(f"Error parsing CoinGecko data: {e}")

        return crypto_data

    async def sentiment_coingecko_calculate_market_sentiment(
        self,
        crypto_prices: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Calculate overall market sentiment based on crypto prices

        Args:
            crypto_prices: List of crypto price data (optional, will fetch if not provided)

        Returns:
            Market sentiment analysis
        """
        if not crypto_prices:
            crypto_prices = await self.sentiment_coingecko_get_current_prices(["usd"])

        sentiment_analysis = {
            "timestamp": int(datetime.now().timestamp() * 1000),
            "overall_sentiment": "neutral",
            "sentiment_score": 0.0,  # -1 (extreme fear) to 1 (extreme greed)
            "btc_price": 0.0,
            "btc_sentiment": "neutral",
            "risk_sentiment": "neutral",
            "forex_impact": "neutral",
            "source": "CoinGecko"
        }

        try:
            # Find Bitcoin price in USD
            btc_usd_data = next(
                (item for item in crypto_prices
                 if item["crypto_id"] == "bitcoin" and item["vs_currency"] == "USD"),
                None
            )

            if not btc_usd_data:
                logger.warning("Bitcoin USD price not found")
                return sentiment_analysis

            btc_price = btc_usd_data["price"]
            btc_change_24h = btc_usd_data.get("change_24h", 0.0)

            sentiment_analysis["btc_price"] = btc_price

            # Determine BTC sentiment based on price levels
            if btc_price >= self.sentiment_thresholds["extreme_greed"]:
                btc_sentiment = "extreme_greed"
                sentiment_score = 0.8
            elif btc_price >= self.sentiment_thresholds["greed"]:
                btc_sentiment = "greed"
                sentiment_score = 0.5
            elif btc_price >= self.sentiment_thresholds["neutral"]:
                btc_sentiment = "neutral"
                sentiment_score = 0.0
            elif btc_price >= self.sentiment_thresholds["fear"]:
                btc_sentiment = "fear"
                sentiment_score = -0.5
            else:
                btc_sentiment = "extreme_fear"
                sentiment_score = -0.8

            # Adjust sentiment based on 24h change
            if btc_change_24h > 5:  # Strong positive move
                sentiment_score += 0.2
            elif btc_change_24h > 2:  # Moderate positive
                sentiment_score += 0.1
            elif btc_change_24h < -5:  # Strong negative
                sentiment_score -= 0.2
            elif btc_change_24h < -2:  # Moderate negative
                sentiment_score -= 0.1

            # Cap sentiment score
            sentiment_score = max(-1.0, min(1.0, sentiment_score))

            # Calculate weighted sentiment from all cryptos
            total_weighted_sentiment = 0.0
            total_weight = 0.0

            for crypto_data in crypto_prices:
                if crypto_data["vs_currency"] == "USD":
                    weight = crypto_data["weight"]
                    change_24h = crypto_data.get("change_24h", 0.0)

                    # Convert change to sentiment score
                    crypto_sentiment = max(-0.5, min(0.5, change_24h / 10))

                    total_weighted_sentiment += crypto_sentiment * weight
                    total_weight += weight

            if total_weight > 0:
                weighted_sentiment = total_weighted_sentiment / total_weight
                # Combine BTC sentiment with weighted sentiment
                final_sentiment = (sentiment_score * 0.7) + (weighted_sentiment * 0.3)
            else:
                final_sentiment = sentiment_score

            # Determine overall sentiment
            if final_sentiment >= 0.6:
                overall_sentiment = "extreme_greed"
                risk_sentiment = "risk_on"
                forex_impact = "risk_currencies_up"  # AUD, NZD, CAD up
            elif final_sentiment >= 0.3:
                overall_sentiment = "greed"
                risk_sentiment = "risk_on"
                forex_impact = "risk_currencies_up"
            elif final_sentiment >= -0.3:
                overall_sentiment = "neutral"
                risk_sentiment = "neutral"
                forex_impact = "neutral"
            elif final_sentiment >= -0.6:
                overall_sentiment = "fear"
                risk_sentiment = "risk_off"
                forex_impact = "safe_havens_up"  # JPY, CHF, USD up
            else:
                overall_sentiment = "extreme_fear"
                risk_sentiment = "risk_off"
                forex_impact = "safe_havens_up"

            sentiment_analysis.update({
                "overall_sentiment": overall_sentiment,
                "sentiment_score": round(final_sentiment, 3),
                "btc_sentiment": btc_sentiment,
                "btc_change_24h": btc_change_24h,
                "risk_sentiment": risk_sentiment,
                "forex_impact": forex_impact
            })

        except Exception as e:
            logger.error(f"Error calculating sentiment: {e}")

        return sentiment_analysis

    async def sentiment_coingecko_get_dominance_data(self) -> Dict:
        """
        Get Bitcoin dominance and market cap data

        Returns:
            Market dominance information
        """
        try:
            url = f"{self.base_url}/global"

            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return await self.sentiment_coingecko_parse_dominance_response(data)
                else:
                    logger.error(f"CoinGecko global API error: {response.status}")
                    return {}

        except Exception as e:
            logger.error(f"Error fetching dominance data: {e}")
            return {}

    async def sentiment_coingecko_parse_dominance_response(self, data: Dict[str, Any]) -> Dict:
        """Parse global market dominance data"""
        try:
            global_data = data.get("data", {})

            dominance_info = {
                "timestamp": int(datetime.now().timestamp() * 1000),
                "btc_dominance": global_data.get("market_cap_percentage", {}).get("btc", 0.0),
                "eth_dominance": global_data.get("market_cap_percentage", {}).get("eth", 0.0),
                "total_market_cap": global_data.get("total_market_cap", {}).get("usd", 0),
                "total_volume_24h": global_data.get("total_volume", {}).get("usd", 0),
                "active_cryptocurrencies": global_data.get("active_cryptocurrencies", 0),
                "source": "CoinGecko",
                "data_type": "crypto_dominance"
            }

            # Interpret dominance for sentiment
            btc_dominance = dominance_info["btc_dominance"]
            if btc_dominance > 50:
                dominance_sentiment = "btc_flight_to_safety"  # Money flowing to BTC
            elif btc_dominance > 40:
                dominance_sentiment = "balanced_market"
            else:
                dominance_sentiment = "altcoin_season"  # Risk-on for alts

            dominance_info["dominance_sentiment"] = dominance_sentiment

            return dominance_info

        except Exception as e:
            logger.error(f"Error parsing dominance data: {e}")
            return {}

    async def sentiment_coingecko_get_forex_signals(self) -> List[Dict]:
        """
        Generate forex trading signals based on crypto sentiment

        Returns:
            List of forex signals based on crypto analysis
        """
        # Get sentiment analysis
        sentiment_data = await self.sentiment_coingecko_calculate_market_sentiment()

        if not sentiment_data:
            return []

        signals = []
        timestamp = sentiment_data["timestamp"]
        risk_sentiment = sentiment_data["risk_sentiment"]
        sentiment_score = sentiment_data["sentiment_score"]

        # Generate forex signals based on risk sentiment
        if risk_sentiment == "risk_on":
            # Risk-on: Favor commodity currencies, risk currencies
            signals.extend([
                {
                    "symbol": "AUDUSD",
                    "signal": "bullish",
                    "strength": abs(sentiment_score),
                    "reason": "crypto_risk_on_sentiment",
                    "timestamp": timestamp
                },
                {
                    "symbol": "NZDUSD",
                    "signal": "bullish",
                    "strength": abs(sentiment_score),
                    "reason": "crypto_risk_on_sentiment",
                    "timestamp": timestamp
                },
                {
                    "symbol": "USDJPY",
                    "signal": "bearish",
                    "strength": abs(sentiment_score) * 0.7,  # Less correlation
                    "reason": "risk_on_yen_weakness",
                    "timestamp": timestamp
                }
            ])

        elif risk_sentiment == "risk_off":
            # Risk-off: Favor safe havens
            signals.extend([
                {
                    "symbol": "USDJPY",
                    "signal": "bearish",
                    "strength": abs(sentiment_score),
                    "reason": "crypto_risk_off_yen_strength",
                    "timestamp": timestamp
                },
                {
                    "symbol": "USDCHF",
                    "signal": "bearish",
                    "strength": abs(sentiment_score) * 0.8,
                    "reason": "crypto_risk_off_chf_strength",
                    "timestamp": timestamp
                },
                {
                    "symbol": "AUDUSD",
                    "signal": "bearish",
                    "strength": abs(sentiment_score),
                    "reason": "risk_off_commodity_weakness",
                    "timestamp": timestamp
                }
            ])

        # Add Gold correlation signal
        if sentiment_data["overall_sentiment"] in ["fear", "extreme_fear"]:
            signals.append({
                "symbol": "XAUUSD",
                "signal": "bullish",
                "strength": abs(sentiment_score),
                "reason": "crypto_fear_gold_safe_haven",
                "timestamp": timestamp
            })

        return signals

    def sentiment_coingecko_get_supported_cryptos(self) -> Dict[str, Dict]:
        """Get list of supported cryptocurrencies"""
        return self.crypto_symbols

    async def sentiment_coingecko_get_historical_data(
        self,
        crypto_id: str,
        days: int = 7
    ) -> List[Dict]:
        """
        Get historical price data for sentiment trend analysis

        Args:
            crypto_id: Cryptocurrency ID (e.g., "bitcoin")
            days: Number of days (max 365 for free tier)

        Returns:
            List of historical price data
        """
        try:
            params = {
                "vs_currency": "usd",
                "days": days
            }

            url = f"{self.base_url}/coins/{crypto_id}/market_chart"

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self.sentiment_coingecko_parse_historical_data(crypto_id, data)
                else:
                    logger.error(f"CoinGecko historical API error: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Error fetching historical data for {crypto_id}: {e}")
            return []

    def sentiment_coingecko_parse_historical_data(
        self,
        crypto_id: str,
        data: Dict[str, Any]
    ) -> List[Dict]:
        """Parse historical chart data"""
        historical_data = []

        try:
            prices = data.get("prices", [])
            volumes = data.get("total_volumes", [])

            for i, price_point in enumerate(prices):
                timestamp_ms, price = price_point
                volume = volumes[i][1] if i < len(volumes) else 0

                historical_data.append({
                    "crypto_id": crypto_id,
                    "symbol": self.crypto_symbols.get(crypto_id, {}).get("symbol", crypto_id.upper()),
                    "price": price,
                    "volume": volume,
                    "timestamp": int(timestamp_ms),
                    "vs_currency": "USD",
                    "source": "CoinGecko",
                    "data_type": "crypto_historical"
                })

        except Exception as e:
            logger.error(f"Error parsing historical data: {e}")

        return historical_data


# Usage Example
async def main():
    """Example usage of CoinGecko Collector"""
    async with CoinGeckoCollector() as collector:

        # Get current crypto prices
        print("Getting current crypto prices...")
        prices = await collector.sentiment_coingecko_get_current_prices(["usd", "eur"])
        print(f"Retrieved {len(prices)} crypto prices")

        for price in prices[:3]:
            print(f"{price['symbol']}: ${price['price']} ({price['change_24h']:+.2f}%)")

        # Calculate market sentiment
        print("\nCalculating market sentiment...")
        sentiment = await collector.sentiment_coingecko_calculate_market_sentiment()
        print(f"Overall sentiment: {sentiment['overall_sentiment']}")
        print(f"Sentiment score: {sentiment['sentiment_score']}")
        print(f"BTC price: ${sentiment['btc_price']:,.0f}")
        print(f"Forex impact: {sentiment['forex_impact']}")

        # Get forex signals
        print("\nGenerating forex signals...")
        signals = await collector.sentiment_coingecko_get_forex_signals()
        for signal in signals:
            print(f"{signal['symbol']}: {signal['signal']} (strength: {signal['strength']:.2f})")

        # Get dominance data
        print("\nGetting market dominance...")
        dominance = await collector.sentiment_coingecko_get_dominance_data()
        if dominance:
            print(f"BTC dominance: {dominance['btc_dominance']:.1f}%")
            print(f"Market sentiment: {dominance['dominance_sentiment']}")

        # Show supported cryptos
        supported = collector.sentiment_coingecko_get_supported_cryptos()
        print(f"\nSupported cryptocurrencies: {len(supported)}")


if __name__ == "__main__":
    asyncio.run(main())