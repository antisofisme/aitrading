"""
Fear & Greed Index Collector - Market Psychology Indicator
Provides alternative.me Fear & Greed Index for market sentiment analysis

FEATURES:
- Real-time Fear & Greed Index (0-100 scale)
- Historical sentiment data
- Market psychology classification
- Contrarian trading signals
- Forex sentiment correlation
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any
import logging

from .session_market_config import MarketSessionsConfig

logger = logging.getLogger(__name__)


class FearGreedCollector:
    """
    Fear & Greed Index collector for market sentiment analysis
    Provides contrarian signals and market psychology insights
    """

    def __init__(self):
        self.base_url = "https://api.alternative.me/fng"
        self.session = None
        self.market_sessions = MarketSessionsConfig()

        # Fear & Greed classification levels
        self.sentiment_levels = {
            "extreme_fear": {"min": 0, "max": 24, "signal": "buy", "strength": 0.9},
            "fear": {"min": 25, "max": 44, "signal": "buy", "strength": 0.6},
            "neutral": {"min": 45, "max": 55, "signal": "hold", "strength": 0.1},
            "greed": {"min": 56, "max": 75, "signal": "sell", "strength": 0.6},
            "extreme_greed": {"min": 76, "max": 100, "signal": "sell", "strength": 0.9}
        }

        # Forex correlation with Fear & Greed
        self.forex_correlations = {
            "risk_on_pairs": {
                # These pairs tend to rise during greed (risk-on)
                "AUDUSD": {"correlation": 0.65, "type": "positive"},
                "NZDUSD": {"correlation": 0.60, "type": "positive"},
                "EURAUD": {"correlation": 0.45, "type": "positive"},
                "GBPAUD": {"correlation": 0.40, "type": "positive"}
            },
            "safe_haven_pairs": {
                # These pairs tend to rise during fear (risk-off)
                "USDJPY": {"correlation": -0.55, "type": "negative"},  # JPY strength
                "USDCHF": {"correlation": -0.50, "type": "negative"},  # CHF strength
                "XAUUSD": {"correlation": -0.70, "type": "negative"}   # Gold rises on fear
            },
            "usd_strength": {
                # USD can be mixed - flight to safety vs risk appetite
                "DXY": {"correlation": -0.30, "type": "mixed"}  # Dollar index
            }
        }

        # Contrarian signal thresholds
        self.contrarian_thresholds = {
            "extreme_contrarian": {"fear_max": 20, "greed_min": 85},
            "strong_contrarian": {"fear_max": 30, "greed_min": 75},
            "moderate_contrarian": {"fear_max": 40, "greed_min": 65}
        }

        # Historical analysis periods
        self.analysis_periods = {
            "short_term": 7,    # 1 week
            "medium_term": 30,  # 1 month
            "long_term": 90     # 3 months
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

    async def sentiment_fear_greed_get_current_index(self) -> Dict:
        """
        Get current Fear & Greed Index

        Returns:
            Current Fear & Greed Index data
        """
        try:
            async with self.session.get(self.base_url) as response:
                if response.status == 200:
                    data = await response.json()
                    return await self.sentiment_fear_greed_parse_current_response(data)
                else:
                    logger.error(f"Fear & Greed API error: {response.status}")
                    return {}

        except Exception as e:
            logger.error(f"Error fetching Fear & Greed Index: {e}")
            return {}

    async def sentiment_fear_greed_parse_current_response(self, data: Dict[str, Any]) -> Dict:
        """Parse current Fear & Greed Index response"""
        try:
            if "data" not in data or not data["data"]:
                logger.warning("No data in Fear & Greed response")
                return {}

            current_data = data["data"][0]

            value = int(current_data.get("value", 50))
            classification = current_data.get("value_classification", "Neutral").lower()
            timestamp = int(current_data.get("timestamp", datetime.now().timestamp()))

            # Convert timestamp to milliseconds if needed
            if timestamp < 1e12:
                timestamp *= 1000

            # Current session info
            session_info = self.market_sessions.session_market_get_current_session(timestamp)
            current_session = session_info.get("current_sessions", ["Unknown"])[0] if session_info.get("current_sessions") else "Unknown"

            # Classify sentiment level
            sentiment_level = self.sentiment_fear_greed_classify_sentiment(value)

            # Generate contrarian signal
            contrarian_signal = self.sentiment_fear_greed_generate_contrarian_signal(value, sentiment_level)

            fear_greed_data = {
                "index_value": value,
                "classification": classification,
                "sentiment_level": sentiment_level,
                "timestamp": timestamp,
                "session": current_session,
                "source": "Alternative.me",
                "data_type": "fear_greed_index",
                "contrarian_signal": contrarian_signal["signal"],
                "signal_strength": contrarian_signal["strength"],
                "market_phase": self.sentiment_fear_greed_determine_market_phase(value)
            }

            return fear_greed_data

        except Exception as e:
            logger.error(f"Error parsing Fear & Greed data: {e}")
            return {}

    def sentiment_fear_greed_classify_sentiment(self, value: int) -> str:
        """Classify sentiment level based on Fear & Greed value"""
        for level, config in self.sentiment_levels.items():
            if config["min"] <= value <= config["max"]:
                return level
        return "neutral"

    def sentiment_fear_greed_generate_contrarian_signal(
        self,
        value: int,
        sentiment_level: str
    ) -> Dict:
        """Generate contrarian trading signal based on Fear & Greed Index"""

        signal_config = self.sentiment_levels.get(sentiment_level, {})
        base_signal = signal_config.get("signal", "hold")
        base_strength = signal_config.get("strength", 0.1)

        # Enhance signal based on extreme levels
        if sentiment_level == "extreme_fear":
            # Extreme fear = Strong buy signal (contrarian)
            return {
                "signal": "strong_buy",
                "strength": 0.9,
                "reasoning": "extreme_fear_contrarian",
                "forex_bias": "risk_on_reversal"
            }
        elif sentiment_level == "extreme_greed":
            # Extreme greed = Strong sell signal (contrarian)
            return {
                "signal": "strong_sell",
                "strength": 0.9,
                "reasoning": "extreme_greed_contrarian",
                "forex_bias": "risk_off_reversal"
            }
        elif sentiment_level == "fear":
            return {
                "signal": "buy",
                "strength": 0.6,
                "reasoning": "fear_contrarian",
                "forex_bias": "moderate_risk_on"
            }
        elif sentiment_level == "greed":
            return {
                "signal": "sell",
                "strength": 0.6,
                "reasoning": "greed_contrarian",
                "forex_bias": "moderate_risk_off"
            }
        else:
            return {
                "signal": "hold",
                "strength": 0.1,
                "reasoning": "neutral_market",
                "forex_bias": "no_bias"
            }

    def sentiment_fear_greed_determine_market_phase(self, value: int) -> str:
        """Determine current market phase based on sentiment"""
        if value <= 25:
            return "capitulation"      # Market bottom forming
        elif value <= 45:
            return "accumulation"      # Smart money buying
        elif value <= 55:
            return "trending"          # Healthy uptrend
        elif value <= 75:
            return "distribution"      # Smart money selling
        else:
            return "euphoria"          # Market top forming

    async def sentiment_fear_greed_get_historical_data(
        self,
        limit: int = 30
    ) -> List[Dict]:
        """
        Get historical Fear & Greed Index data

        Args:
            limit: Number of historical data points (max 100)

        Returns:
            List of historical Fear & Greed data
        """
        try:
            params = {"limit": min(limit, 100)}

            async with self.session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return await self.sentiment_fear_greed_parse_historical_response(data)
                else:
                    logger.error(f"Fear & Greed historical API error: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Error fetching historical Fear & Greed data: {e}")
            return []

    async def sentiment_fear_greed_parse_historical_response(
        self,
        data: Dict[str, Any]
    ) -> List[Dict]:
        """Parse historical Fear & Greed Index response"""
        historical_data = []

        try:
            data_points = data.get("data", [])

            for point in data_points:
                value = int(point.get("value", 50))
                timestamp = int(point.get("timestamp", 0))

                # Convert timestamp to milliseconds if needed
                if timestamp < 1e12:
                    timestamp *= 1000

                sentiment_level = self.sentiment_fear_greed_classify_sentiment(value)
                contrarian_signal = self.sentiment_fear_greed_generate_contrarian_signal(value, sentiment_level)

                historical_point = {
                    "index_value": value,
                    "classification": point.get("value_classification", "").lower(),
                    "sentiment_level": sentiment_level,
                    "timestamp": timestamp,
                    "source": "Alternative.me",
                    "data_type": "fear_greed_historical",
                    "contrarian_signal": contrarian_signal["signal"],
                    "signal_strength": contrarian_signal["strength"],
                    "market_phase": self.sentiment_fear_greed_determine_market_phase(value)
                }

                historical_data.append(historical_point)

        except Exception as e:
            logger.error(f"Error parsing historical Fear & Greed data: {e}")

        return historical_data

    async def sentiment_fear_greed_analyze_trends(
        self,
        period: str = "medium_term"
    ) -> Dict:
        """
        Analyze Fear & Greed trends over specified period

        Args:
            period: Analysis period ("short_term", "medium_term", "long_term")

        Returns:
            Trend analysis results
        """
        days = self.analysis_periods.get(period, 30)
        historical_data = await self.sentiment_fear_greed_get_historical_data(days)

        if not historical_data:
            return {}

        try:
            values = [point["index_value"] for point in historical_data]
            timestamps = [point["timestamp"] for point in historical_data]

            # Calculate trend metrics
            current_value = values[0] if values else 50
            avg_value = sum(values) / len(values)
            min_value = min(values)
            max_value = max(values)

            # Trend direction
            if len(values) >= 7:
                recent_avg = sum(values[:7]) / 7
                older_avg = sum(values[-7:]) / 7
                trend_direction = "up" if recent_avg > older_avg else "down"
                trend_strength = abs(recent_avg - older_avg) / avg_value
            else:
                trend_direction = "neutral"
                trend_strength = 0.0

            # Volatility
            volatility = (max_value - min_value) / avg_value if avg_value > 0 else 0

            # Extremes count
            extreme_fear_count = sum(1 for v in values if v <= 25)
            extreme_greed_count = sum(1 for v in values if v >= 75)

            # Market regime
            if avg_value <= 35:
                market_regime = "bearish_sentiment"
            elif avg_value >= 65:
                market_regime = "bullish_sentiment"
            else:
                market_regime = "neutral_sentiment"

            trend_analysis = {
                "period": period,
                "days_analyzed": days,
                "data_points": len(values),
                "current_value": current_value,
                "average_value": round(avg_value, 1),
                "min_value": min_value,
                "max_value": max_value,
                "trend_direction": trend_direction,
                "trend_strength": round(trend_strength, 3),
                "volatility": round(volatility, 3),
                "extreme_fear_count": extreme_fear_count,
                "extreme_greed_count": extreme_greed_count,
                "market_regime": market_regime,
                "contrarian_opportunities": extreme_fear_count + extreme_greed_count,
                "timestamp": int(datetime.now().timestamp() * 1000),
                "source": "Alternative.me"
            }

            return trend_analysis

        except Exception as e:
            logger.error(f"Error analyzing Fear & Greed trends: {e}")
            return {}

    async def sentiment_fear_greed_generate_forex_signals(
        self,
        current_sentiment: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Generate forex trading signals based on Fear & Greed sentiment

        Args:
            current_sentiment: Current sentiment data (optional, will fetch if not provided)

        Returns:
            List of forex signals
        """
        if not current_sentiment:
            current_sentiment = await self.sentiment_fear_greed_get_current_index()

        if not current_sentiment:
            return []

        signals = []
        timestamp = current_sentiment["timestamp"]
        sentiment_level = current_sentiment["sentiment_level"]
        signal_strength = current_sentiment["signal_strength"]
        forex_bias = current_sentiment.get("contrarian_signal", {}).get("forex_bias", "no_bias")

        try:
            # Generate signals based on sentiment and correlations
            for pair_group, pairs in self.forex_correlations.items():
                for symbol, correlation_data in pairs.items():
                    correlation = correlation_data["correlation"]
                    correlation_type = correlation_data["type"]

                    # Calculate signal based on correlation
                    if correlation_type == "positive":
                        # Positive correlation with risk sentiment
                        if sentiment_level in ["extreme_fear", "fear"]:
                            signal = "bullish"  # Contrarian: fear -> buy risk assets
                        elif sentiment_level in ["extreme_greed", "greed"]:
                            signal = "bearish"  # Contrarian: greed -> sell risk assets
                        else:
                            signal = "neutral"
                    elif correlation_type == "negative":
                        # Negative correlation (safe havens)
                        if sentiment_level in ["extreme_fear", "fear"]:
                            signal = "bullish"  # Fear -> safe haven demand
                        elif sentiment_level in ["extreme_greed", "greed"]:
                            signal = "bearish"  # Greed -> safe haven selling
                        else:
                            signal = "neutral"
                    else:
                        signal = "neutral"

                    if signal != "neutral":
                        # Adjust strength based on correlation strength
                        adjusted_strength = signal_strength * abs(correlation)

                        signals.append({
                            "symbol": symbol,
                            "signal": signal,
                            "strength": round(adjusted_strength, 3),
                            "correlation": correlation,
                            "sentiment_level": sentiment_level,
                            "reasoning": f"fear_greed_{sentiment_level}_contrarian",
                            "pair_group": pair_group,
                            "timestamp": timestamp,
                            "source": "Fear_Greed_Analysis"
                        })

        except Exception as e:
            logger.error(f"Error generating forex signals: {e}")

        return signals

    async def sentiment_fear_greed_get_contrarian_alerts(
        self,
        threshold_type: str = "moderate_contrarian"
    ) -> List[Dict]:
        """
        Get contrarian trading alerts based on extreme sentiment levels

        Args:
            threshold_type: Type of contrarian threshold to use

        Returns:
            List of contrarian alerts
        """
        current_sentiment = await self.sentiment_fear_greed_get_current_index()

        if not current_sentiment:
            return []

        alerts = []
        value = current_sentiment["index_value"]
        timestamp = current_sentiment["timestamp"]

        threshold_config = self.contrarian_thresholds.get(threshold_type, {})

        # Check for extreme fear (buy signal)
        if value <= threshold_config.get("fear_max", 30):
            alerts.append({
                "alert_type": "contrarian_buy",
                "index_value": value,
                "sentiment_level": current_sentiment["sentiment_level"],
                "signal_strength": current_sentiment["signal_strength"],
                "message": f"Extreme fear detected (Index: {value}). Potential buying opportunity.",
                "recommended_action": "Consider long positions in risk assets",
                "forex_bias": "bullish_risk_currencies",
                "timestamp": timestamp,
                "threshold_type": threshold_type
            })

        # Check for extreme greed (sell signal)
        elif value >= threshold_config.get("greed_min", 70):
            alerts.append({
                "alert_type": "contrarian_sell",
                "index_value": value,
                "sentiment_level": current_sentiment["sentiment_level"],
                "signal_strength": current_sentiment["signal_strength"],
                "message": f"Extreme greed detected (Index: {value}). Potential selling opportunity.",
                "recommended_action": "Consider short positions in risk assets",
                "forex_bias": "bearish_risk_currencies",
                "timestamp": timestamp,
                "threshold_type": threshold_type
            })

        return alerts

    def sentiment_fear_greed_get_sentiment_levels(self) -> Dict:
        """Get Fear & Greed sentiment level configurations"""
        return self.sentiment_levels

    def sentiment_fear_greed_get_forex_correlations(self) -> Dict:
        """Get forex correlation configurations"""
        return self.forex_correlations


# Usage Example
async def main():
    """Example usage of Fear & Greed Collector"""
    async with FearGreedCollector() as collector:

        # Get current Fear & Greed Index
        print("Getting current Fear & Greed Index...")
        current = await collector.sentiment_fear_greed_get_current_index()
        if current:
            print(f"Fear & Greed Index: {current['index_value']} ({current['classification']})")
            print(f"Sentiment Level: {current['sentiment_level']}")
            print(f"Contrarian Signal: {current['contrarian_signal']} (strength: {current['signal_strength']})")
            print(f"Market Phase: {current['market_phase']}")

        # Get historical data and analyze trends
        print("\nAnalyzing medium-term trends...")
        trends = await collector.sentiment_fear_greed_analyze_trends("medium_term")
        if trends:
            print(f"Average sentiment: {trends['average_value']} ({trends['market_regime']})")
            print(f"Trend direction: {trends['trend_direction']} (strength: {trends['trend_strength']})")
            print(f"Extreme readings: {trends['contrarian_opportunities']} contrarian opportunities")

        # Generate forex signals
        print("\nGenerating forex signals...")
        signals = await collector.sentiment_fear_greed_generate_forex_signals()
        for signal in signals[:5]:
            print(f"{signal['symbol']}: {signal['signal']} (strength: {signal['strength']:.2f})")

        # Check for contrarian alerts
        print("\nChecking for contrarian alerts...")
        alerts = await collector.sentiment_fear_greed_get_contrarian_alerts()
        for alert in alerts:
            print(f"ALERT: {alert['alert_type']} - {alert['message']}")

        # Show configuration
        levels = collector.sentiment_fear_greed_get_sentiment_levels()
        print(f"\nSentiment levels configured: {len(levels)}")


if __name__ == "__main__":
    asyncio.run(main())