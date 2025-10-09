"""
News/Economic Calendar Features (8 features - 20% importance)

Features:
1. upcoming_high_impact_events_4h
2. time_to_next_event_minutes
3. event_impact_score
4. is_pre_news_zone
5. is_post_news_zone
6. event_type_category
7. actual_vs_forecast_deviation
8. historical_event_volatility
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class NewsCalendarFeatures:
    """Calculate news/economic calendar features"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config['feature_groups']['news_calendar']
        self.lookback_hours = self.config.get('lookback_hours', 4)
        self.blackout_minutes = self.config.get('news_blackout_minutes', 15)

    def calculate(self, timestamp: pd.Timestamp, external_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Calculate all news/calendar features"""
        features = {}

        calendar_data = external_data.get('economic_calendar', pd.DataFrame())

        # 1. Upcoming high-impact events in next 4 hours
        features['upcoming_high_impact_events_4h'] = self._count_upcoming_events(
            timestamp, calendar_data, hours=4, impact='high'
        )

        # 2. Time to next event (minutes)
        features['time_to_next_event_minutes'] = self._time_to_next_event(
            timestamp, calendar_data
        )

        # 3. Event impact score (1=low, 2=medium, 3=high)
        features['event_impact_score'] = self._get_next_event_impact(
            timestamp, calendar_data
        )

        # 4. Is pre-news zone (1-2 hours before high-impact)
        features['is_pre_news_zone'] = self._is_pre_news_zone(
            timestamp, calendar_data
        )

        # 5. Is post-news zone (30-60 min after release)
        features['is_post_news_zone'] = self._is_post_news_zone(
            timestamp, calendar_data
        )

        # 6. Event type category (NFP, CPI, Fed, etc)
        features['event_type_category'] = self._get_event_type(
            timestamp, calendar_data
        )

        # 7. Actual vs forecast deviation (%)
        features['actual_vs_forecast_deviation'] = self._calc_deviation(
            calendar_data
        )

        # 8. Historical event volatility (avg pips moved)
        features['historical_event_volatility'] = self._get_historical_volatility(
            calendar_data
        )

        return features

    def _count_upcoming_events(
        self,
        timestamp: pd.Timestamp,
        calendar_data: pd.DataFrame,
        hours: int = 4,
        impact: str = 'high'
    ) -> int:
        """Count upcoming high-impact events"""
        if calendar_data.empty:
            return 0

        try:
            future_window = timestamp + timedelta(hours=hours)

            # Filter events in time window
            upcoming = calendar_data[
                (calendar_data['date'] >= timestamp) &
                (calendar_data['date'] <= future_window) &
                (calendar_data['impact'] == impact)
            ]

            return len(upcoming)
        except:
            return 0

    def _time_to_next_event(self, timestamp: pd.Timestamp, calendar_data: pd.DataFrame) -> int:
        """Minutes until next economic event"""
        if calendar_data.empty:
            return 9999  # No events

        try:
            future_events = calendar_data[calendar_data['date'] > timestamp].sort_values('date')

            if not future_events.empty:
                next_event = future_events.iloc[0]
                time_diff = (next_event['date'] - timestamp).total_seconds() / 60
                return int(time_diff)
        except:
            pass

        return 9999

    def _get_next_event_impact(self, timestamp: pd.Timestamp, calendar_data: pd.DataFrame) -> int:
        """Get impact score of next event (1-3)"""
        if calendar_data.empty:
            return 0

        try:
            future_events = calendar_data[calendar_data['date'] > timestamp].sort_values('date')

            if not future_events.empty:
                impact = future_events.iloc[0]['impact']
                if impact == 'high':
                    return 3
                elif impact == 'medium':
                    return 2
                else:
                    return 1
        except:
            pass

        return 0

    def _is_pre_news_zone(self, timestamp: pd.Timestamp, calendar_data: pd.DataFrame) -> int:
        """Check if in pre-news zone (1-2h before high-impact)"""
        if calendar_data.empty:
            return 0

        try:
            # Look for high-impact events in next 1-2 hours
            window_start = timestamp + timedelta(hours=1)
            window_end = timestamp + timedelta(hours=2)

            pre_news = calendar_data[
                (calendar_data['date'] >= window_start) &
                (calendar_data['date'] <= window_end) &
                (calendar_data['impact'] == 'high')
            ]

            return 1 if not pre_news.empty else 0
        except:
            return 0

    def _is_post_news_zone(self, timestamp: pd.Timestamp, calendar_data: pd.DataFrame) -> int:
        """Check if in post-news zone (30-60 min after release)"""
        if calendar_data.empty:
            return 0

        try:
            # Look for events that happened 30-60 min ago
            window_start = timestamp - timedelta(minutes=60)
            window_end = timestamp - timedelta(minutes=30)

            post_news = calendar_data[
                (calendar_data['date'] >= window_start) &
                (calendar_data['date'] <= window_end) &
                (calendar_data['impact'] == 'high')
            ]

            return 1 if not post_news.empty else 0
        except:
            return 0

    def _get_event_type(self, timestamp: pd.Timestamp, calendar_data: pd.DataFrame) -> str:
        """Get event type category of nearest event"""
        if calendar_data.empty:
            return 'none'

        try:
            future_events = calendar_data[calendar_data['date'] > timestamp].sort_values('date')

            if not future_events.empty:
                event_name = str(future_events.iloc[0].get('event', '')).lower()

                # Categorize by keywords
                if 'nfp' in event_name or 'employment' in event_name:
                    return 'nfp'
                elif 'cpi' in event_name or 'inflation' in event_name:
                    return 'cpi'
                elif 'fed' in event_name or 'fomc' in event_name:
                    return 'fed'
                elif 'gdp' in event_name:
                    return 'gdp'
                elif 'ecb' in event_name:
                    return 'ecb'
                else:
                    return 'other'
        except:
            pass

        return 'none'

    def _calc_deviation(self, calendar_data: pd.DataFrame) -> float:
        """Calculate actual vs forecast deviation for latest event"""
        if calendar_data.empty:
            return 0.0

        try:
            # Get most recent event with actual data
            recent = calendar_data[
                (calendar_data['actual'].notna()) &
                (calendar_data['forecast'].notna())
            ].tail(1)

            if not recent.empty:
                actual = float(recent.iloc[0]['actual'])
                forecast = float(recent.iloc[0]['forecast'])

                if forecast != 0:
                    deviation = (actual - forecast) / abs(forecast)
                    return round(deviation, 3)
        except:
            pass

        return 0.0

    def _get_historical_volatility(self, calendar_data: pd.DataFrame) -> float:
        """Get average volatility for this event type"""
        # Simplified: Return fixed value based on event type
        # In production, this would query historical price moves
        return 150.0  # Average 150 pips for major events
