"""
News/Economic Calendar Features (8 features, ~18% expected importance)

Based on TRADING_STRATEGY_AND_ML_DESIGN.md v2.3
Fundamental analysis as primary support for trading decisions

Features:
1. upcoming_high_impact_events_4h - COUNT of high-impact events in next 4 hours
2. time_to_next_event_minutes - Minutes until next economic event
3. event_impact_score - 1=low, 2=medium, 3=high impact
4. is_pre_news_zone - Boolean, within 15 min before high-impact event
5. is_post_news_zone - Boolean, within 60 min after high-impact event
6. event_type_category - Categorical integer (NFP=10, CPI=9, GDP=8, etc.)
7. actual_vs_forecast_deviation - % deviation from forecast
8. historical_event_volatility - ATR multiplier (NFP=2.5x, High=2.0x, Medium=1.5x)
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class NewsCalendarFeatures:
    """
    Calculate news/economic calendar features

    Reads from external_economic_calendar table with columns:
    - event_date, event_time, currency, event_name
    - impact (low/medium/high), actual, forecast, previous
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config.get('feature_groups', {}).get('news_calendar', {})
        self.lookback_hours = self.config.get('lookback_hours', 4)
        self.news_blackout_minutes = self.config.get('news_blackout_minutes', 15)

        # High-impact event categories (NFP = highest volatility)
        self.high_impact_categories = {
            'NFP': 10, 'NON-FARM': 10, 'PAYROLLS': 10,  # Non-Farm Payrolls (highest)
            'CPI': 9, 'CONSUMER PRICE': 9,              # Consumer Price Index
            'FOMC': 9, 'FED': 9, 'INTEREST RATE': 9,   # Federal Open Market Committee
            'GDP': 8, 'GROSS DOMESTIC': 8,              # Gross Domestic Product
            'RETAIL SALES': 7,
            'UNEMPLOYMENT': 7, 'JOBLESS': 7,
            'PMI': 6, 'MANUFACTURING': 6,
            'PPI': 6, 'PRODUCER PRICE': 6,
            'TRADE BALANCE': 5
        }

        logger.info("📰 NewsCalendarFeatures initialized")

    def calculate(
        self,
        timestamp: pd.Timestamp,
        external_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        """
        Calculate all 8 news/calendar features

        Args:
            timestamp: Current candle timestamp
            external_data: Dict with 'economic_calendar' DataFrame

        Returns:
            Dict with 8 news features
        """
        try:
            calendar_df = external_data.get('economic_calendar', pd.DataFrame())

            if calendar_df.empty:
                logger.debug("⚠️ No economic calendar data available")
                return self._default_features()

            # Parse and filter events
            upcoming_events = self._filter_upcoming_events(calendar_df, timestamp)
            past_events = self._filter_past_events(calendar_df, timestamp)

            features = {}

            # 1. Count high-impact events in next 4 hours
            features['upcoming_high_impact_events_4h'] = self._count_high_impact_events(
                upcoming_events, hours=self.lookback_hours
            )

            # 2. Time to next event (any impact)
            features['time_to_next_event_minutes'] = self._time_to_next_event(
                upcoming_events, timestamp
            )

            # 3. Next event impact score (1-3)
            next_event = self._get_next_event(upcoming_events)
            features['event_impact_score'] = self._get_impact_score(next_event)

            # 4. Is in pre-news blackout zone? (15 min before high-impact)
            features['is_pre_news_zone'] = self._is_pre_news_zone(
                upcoming_events, timestamp, minutes=self.news_blackout_minutes
            )

            # 5. Is in post-news window? (60 min after high-impact)
            features['is_post_news_zone'] = self._is_post_news_zone(
                past_events, timestamp, minutes=60
            )

            # 6. Event type category (encoded as integer)
            features['event_type_category'] = self._get_event_category(next_event)

            # 7. Actual vs Forecast deviation (%)
            features['actual_vs_forecast_deviation'] = self._calculate_deviation(
                past_events, timestamp
            )

            # 8. Historical event volatility (ATR multiplier)
            features['historical_event_volatility'] = self._get_historical_volatility(
                next_event
            )

            return features

        except Exception as e:
            logger.error(f"❌ News calendar calculation failed: {e}")
            return self._default_features()

    def _filter_upcoming_events(
        self,
        calendar_df: pd.DataFrame,
        timestamp: pd.Timestamp
    ) -> pd.DataFrame:
        """Filter events that are upcoming (future events within 24h)"""
        try:
            # Combine event_date and event_time to full timestamp
            if 'event_timestamp' not in calendar_df.columns:
                calendar_df['event_timestamp'] = pd.to_datetime(
                    calendar_df['event_date'].astype(str) + ' ' +
                    calendar_df['event_time'].astype(str),
                    errors='coerce'
                )

            # Filter future events within next 24 hours
            future_events = calendar_df[
                (calendar_df['event_timestamp'] > timestamp) &
                (calendar_df['event_timestamp'] <= timestamp + timedelta(hours=24))
            ].copy()

            return future_events.sort_values('event_timestamp')

        except Exception as e:
            logger.warning(f"⚠️ Failed to filter upcoming events: {e}")
            return pd.DataFrame()

    def _filter_past_events(
        self,
        calendar_df: pd.DataFrame,
        timestamp: pd.Timestamp
    ) -> pd.DataFrame:
        """Filter events that happened recently (past 2 hours)"""
        try:
            if 'event_timestamp' not in calendar_df.columns:
                calendar_df['event_timestamp'] = pd.to_datetime(
                    calendar_df['event_date'].astype(str) + ' ' +
                    calendar_df['event_time'].astype(str),
                    errors='coerce'
                )

            # Filter past events within last 2 hours
            past_events = calendar_df[
                (calendar_df['event_timestamp'] <= timestamp) &
                (calendar_df['event_timestamp'] >= timestamp - timedelta(hours=2))
            ].copy()

            return past_events.sort_values('event_timestamp', ascending=False)

        except Exception:
            return pd.DataFrame()

    def _count_high_impact_events(
        self,
        events_df: pd.DataFrame,
        hours: int = 4
    ) -> int:
        """Count high-impact events in next N hours"""
        if events_df.empty:
            return 0

        try:
            high_impact = events_df[
                events_df['impact'].str.lower() == 'high'
            ]
            return len(high_impact)
        except Exception:
            return 0

    def _time_to_next_event(
        self,
        events_df: pd.DataFrame,
        timestamp: pd.Timestamp
    ) -> int:
        """Minutes until next event (any impact level)"""
        if events_df.empty:
            return 9999  # No upcoming events

        try:
            next_event = events_df.iloc[0]
            next_time = next_event['event_timestamp']
            delta = (next_time - timestamp).total_seconds() / 60
            return int(delta)
        except Exception:
            return 9999

    def _get_next_event(
        self,
        events_df: pd.DataFrame
    ) -> Optional[pd.Series]:
        """Get next upcoming event"""
        if events_df.empty:
            return None
        return events_df.iloc[0]

    def _get_impact_score(self, event: Optional[pd.Series]) -> int:
        """Convert impact string to score: 1=low, 2=medium, 3=high"""
        if event is None:
            return 0

        try:
            impact = str(event['impact']).lower()
            if impact == 'high':
                return 3
            elif impact == 'medium':
                return 2
            elif impact == 'low':
                return 1
            else:
                return 0
        except Exception:
            return 0

    def _is_pre_news_zone(
        self,
        events_df: pd.DataFrame,
        timestamp: pd.Timestamp,
        minutes: int = 15
    ) -> int:
        """Check if within blackout period before high-impact event (1=yes, 0=no)"""
        if events_df.empty:
            return 0

        try:
            high_impact = events_df[events_df['impact'].str.lower() == 'high']

            if high_impact.empty:
                return 0

            next_high_impact = high_impact.iloc[0]
            next_time = next_high_impact['event_timestamp']
            delta_minutes = (next_time - timestamp).total_seconds() / 60

            # Within blackout window?
            if 0 < delta_minutes <= minutes:
                return 1

            return 0
        except Exception:
            return 0

    def _is_post_news_zone(
        self,
        events_df: pd.DataFrame,
        timestamp: pd.Timestamp,
        minutes: int = 60
    ) -> int:
        """Check if within window after high-impact event (1=yes, 0=no)"""
        if events_df.empty:
            return 0

        try:
            high_impact = events_df[events_df['impact'].str.lower() == 'high']

            if high_impact.empty:
                return 0

            last_high_impact = high_impact.iloc[0]
            last_time = last_high_impact['event_timestamp']
            delta_minutes = (timestamp - last_time).total_seconds() / 60

            # Within post-news window?
            if 0 <= delta_minutes <= minutes:
                return 1

            return 0
        except Exception:
            return 0

    def _get_event_category(self, event: Optional[pd.Series]) -> int:
        """
        Get event category as integer (for ML encoding)

        Returns category importance score (0-10)
        NFP=10 (highest), CPI/FOMC=9, GDP=8, etc.
        """
        if event is None:
            return 0

        try:
            event_name = str(event['event_name']).upper()

            # Match against high-impact categories
            for category, score in self.high_impact_categories.items():
                if category in event_name:
                    return score

            # Default: unknown category
            return 1

        except Exception:
            return 0

    def _calculate_deviation(
        self,
        past_events_df: pd.DataFrame,
        timestamp: pd.Timestamp
    ) -> float:
        """
        Calculate % deviation between actual vs forecast for most recent event

        Returns: (actual - forecast) / forecast * 100
        """
        if past_events_df.empty:
            return 0.0

        try:
            # Get most recent event with actual & forecast data
            recent = past_events_df[
                (past_events_df['actual'].notna()) &
                (past_events_df['forecast'].notna())
            ]

            if recent.empty:
                return 0.0

            last_event = recent.iloc[0]
            actual = float(last_event['actual'])
            forecast = float(last_event['forecast'])

            if forecast == 0:
                return 0.0

            deviation = ((actual - forecast) / abs(forecast)) * 100

            return round(deviation, 2)

        except Exception:
            return 0.0

    def _get_historical_volatility(self, event: Optional[pd.Series]) -> float:
        """
        Get historical volatility multiplier for event type

        Based on typical ATR expansion after event
        Returns ATR multiplier (1.0 = normal, 2.5 = high volatility)
        """
        if event is None:
            return 1.0

        try:
            event_name = str(event['event_name']).upper()
            impact = str(event['impact']).lower()

            # High-volatility events (NFP, FOMC, CPI)
            for key in ['NFP', 'NON-FARM', 'FOMC', 'CPI', 'FED']:
                if key in event_name:
                    return 2.5

            # Medium-volatility by impact level
            if impact == 'high':
                return 2.0
            elif impact == 'medium':
                return 1.5
            elif impact == 'low':
                return 1.2

            return 1.0

        except Exception:
            return 1.0

    def _default_features(self) -> Dict[str, Any]:
        """Return default feature values when calculation fails"""
        return {
            'upcoming_high_impact_events_4h': 0,
            'time_to_next_event_minutes': 9999,
            'event_impact_score': 0,
            'is_pre_news_zone': 0,
            'is_post_news_zone': 0,
            'event_type_category': 0,
            'actual_vs_forecast_deviation': 0.0,
            'historical_event_volatility': 1.0
        }
