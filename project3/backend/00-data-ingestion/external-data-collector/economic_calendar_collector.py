"""
Economic Calendar Collector - Handles Forecast → Actual Data Flow
Supports APIs that provide events twice: once as forecast, once as actual result
"""

import asyncio
import aiohttp
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from schemas.market_data_pb2 import UnifiedMarketData


class EconomicCalendarCollector:
    """
    Collector for Economic Calendar APIs that provide forecast→actual flow
    Example APIs: Forex Factory, Economic Calendar API, Trading Economics
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://api.example-economic-calendar.com/v1"
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _generate_event_id(self, event_data: Dict[str, Any]) -> str:
        """Generate consistent event_id for UPSERT deduplication"""
        # Create unique ID based on symbol, date, and importance
        key_string = f"{event_data.get('symbol', '')}{event_data.get('event_date', '')}{event_data.get('title', '')}"
        return hashlib.md5(key_string.encode()).hexdigest()[:16]

    async def economic_calendar_get_events(
        self,
        days_ahead: int = 7,
        importance_levels: List[str] = ["high", "medium"]
    ) -> List[UnifiedMarketData]:
        """
        Get upcoming economic calendar events
        This will return forecast data that later gets updated with actual results
        """
        events = []

        try:
            # Get upcoming events (forecast phase)
            forecast_url = f"{self.base_url}/calendar/upcoming"
            params = {
                "days": days_ahead,
                "importance": ",".join(importance_levels),
                "api_key": self.api_key
            }

            async with self.session.get(forecast_url, params=params) as response:
                if response.status == 200:
                    api_data = await response.json()

                    for event in api_data.get("events", []):
                        # Generate consistent event_id for later UPSERT
                        event_id = self._generate_event_id(event)

                        unified_event = UnifiedMarketData(
                            # Core identification
                            symbol=event.get("symbol", "UNKNOWN"),
                            timestamp=int(datetime.fromisoformat(event["event_date"]).timestamp() * 1000),
                            source="EconomicCalendar",
                            data_type="economic_calendar",

                            # Event deduplication
                            event_id=event_id,
                            external_id=event.get("id"),  # API's own ID

                            # Time classification - this is FORECAST data
                            # time_status will be set in to_database_format based on actual_value

                            # Values - PRESERVE BOTH for AI learning
                            # Use 'value' field to carry the data, but specify which type in metadata
                            value=event.get("forecast"),  # Current value for this collection phase

                            # Event metadata
                            date=event.get("event_date"),
                            units=event.get("unit", ""),
                            frequency=event.get("frequency", "one-time"),

                            # Impact assessment
                            currency_impact=event.get("affected_currencies", []),
                            market_impact_score=self._parse_importance_to_score(event.get("importance")),

                            # Full API response for debugging
                            raw_metadata={
                                **event,
                                "collection_phase": "forecast",
                                "collected_at": datetime.now().isoformat(),
                                "data_completeness": {
                                    "has_forecast": event.get("forecast") is not None,
                                    "has_actual": False,
                                    "has_previous": event.get("previous") is not None
                                }
                            }
                        )

                        events.append(unified_event)

        except Exception as e:
            print(f"Error fetching calendar events: {e}")

        return events

    async def economic_calendar_get_recent_results(
        self,
        days_back: int = 1
    ) -> List[UnifiedMarketData]:
        """
        Get recent economic events with ACTUAL results
        This provides the second phase - actual data to update forecasts
        """
        events = []

        try:
            # Get recent results (actual phase)
            results_url = f"{self.base_url}/calendar/results"
            params = {
                "days_back": days_back,
                "api_key": self.api_key
            }

            async with self.session.get(results_url, params=params) as response:
                if response.status == 200:
                    api_data = await response.json()

                    for event in api_data.get("events", []):
                        # SAME event_id as forecast for UPSERT
                        event_id = self._generate_event_id(event)

                        unified_event = UnifiedMarketData(
                            # Same identification as forecast
                            symbol=event.get("symbol", "UNKNOWN"),
                            timestamp=int(datetime.fromisoformat(event["event_date"]).timestamp() * 1000),
                            source="EconomicCalendar",
                            data_type="economic_calendar",

                            # SAME event_id for UPSERT deduplication
                            event_id=event_id,
                            external_id=event.get("id"),

                            # Values - actual result (forecast will be preserved in UPSERT)
                            value=event.get("actual"),  # Current value for this collection phase

                            # Event metadata
                            date=event.get("event_date"),
                            units=event.get("unit", ""),
                            frequency=event.get("frequency", "one-time"),

                            # Impact assessment (may be updated based on surprise)
                            currency_impact=event.get("affected_currencies", []),
                            market_impact_score=self._calculate_actual_impact(
                                event.get("actual"),
                                event.get("forecast"),
                                event.get("previous")
                            ),

                            # Full API response
                            raw_metadata={
                                **event,
                                "collection_phase": "actual",
                                "collected_at": datetime.now().isoformat(),
                                "surprise_factor": self._calculate_surprise_factor(event),
                                "data_completeness": {
                                    "has_forecast": event.get("forecast") is not None,
                                    "has_actual": event.get("actual") is not None,
                                    "has_previous": event.get("previous") is not None
                                },
                                "learning_features": {
                                    "forecast_vs_actual": event.get("actual", 0) - event.get("forecast", 0),
                                    "actual_vs_previous": event.get("actual", 0) - event.get("previous", 0),
                                    "forecast_vs_previous": event.get("forecast", 0) - event.get("previous", 0)
                                }
                            }
                        )

                        events.append(unified_event)

        except Exception as e:
            print(f"Error fetching calendar results: {e}")

        return events

    def _parse_importance_to_score(self, importance: str) -> float:
        """Convert API importance string to numeric score"""
        importance_map = {
            "low": 0.3,
            "medium": 0.6,
            "high": 0.9,
            "very_high": 1.0
        }
        return importance_map.get(importance.lower(), 0.5)

    def _calculate_actual_impact(
        self,
        actual: Optional[float],
        forecast: Optional[float],
        previous: Optional[float]
    ) -> float:
        """Calculate actual market impact based on surprise factor"""
        if not all([actual, forecast, previous]):
            return 0.5  # Default if missing data

        # Calculate surprise magnitude vs forecast
        forecast_surprise = abs(actual - forecast) / abs(forecast) if forecast != 0 else 0

        # Calculate vs previous period
        previous_surprise = abs(actual - previous) / abs(previous) if previous != 0 else 0

        # Combine both factors
        impact_score = min((forecast_surprise + previous_surprise) / 2, 1.0)

        # Boost score for directional surprises
        if (actual > forecast and actual > previous) or (actual < forecast and actual < previous):
            impact_score = min(impact_score * 1.2, 1.0)

        return round(impact_score, 2)

    def _calculate_surprise_factor(self, event: Dict[str, Any]) -> str:
        """Determine surprise level for trading algorithms"""
        actual = event.get("actual")
        forecast = event.get("forecast")

        if not all([actual, forecast]):
            return "unknown"

        surprise_pct = abs(actual - forecast) / abs(forecast) if forecast != 0 else 0

        if surprise_pct > 0.1:  # >10% surprise
            return "major"
        elif surprise_pct > 0.05:  # 5-10% surprise
            return "moderate"
        elif surprise_pct > 0.02:  # 2-5% surprise
            return "minor"
        else:
            return "inline"

    async def get_all_economic_data(self) -> List[UnifiedMarketData]:
        """Get both upcoming forecasts and recent actual results"""
        all_data = []

        # Get forecasts for next 7 days
        forecasts = await self.economic_calendar_get_events(days_ahead=7)
        all_data.extend(forecasts)

        # Get actual results from last 2 days
        actuals = await self.economic_calendar_get_recent_results(days_back=2)
        all_data.extend(actuals)

        return all_data


# Example usage and database UPSERT
"""
Database insertion with UPSERT to handle forecast→actual flow:

INSERT INTO market_context (
    event_id, symbol, data_type, source, time_status,
    event_date, forecast_value, actual_value, importance, currency_impact
) VALUES (
    %(event_id)s, %(symbol)s, 'economic_calendar', 'EconomicCalendar',
    CASE WHEN %(actual_value)s IS NULL THEN 'scheduled' ELSE 'historical' END,
    %(event_date)s, %(forecast_value)s, %(actual_value)s, %(importance)s, %(currency_impact)s
)
ON CONFLICT (event_id, symbol, event_date)
DO UPDATE SET
    actual_value = COALESCE(EXCLUDED.actual_value, market_context.actual_value),
    forecast_value = COALESCE(market_context.forecast_value, EXCLUDED.forecast_value),
    time_status = CASE
        WHEN EXCLUDED.actual_value IS NOT NULL THEN 'historical'
        ELSE market_context.time_status
    END,
    market_impact_score = EXCLUDED.market_impact_score,
    metadata = EXCLUDED.metadata,
    updated_at = NOW();
"""