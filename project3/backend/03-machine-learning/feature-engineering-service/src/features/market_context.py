"""
Market Context & Session Features (12 features - 8% importance)

Features:
1. is_london_session
2. is_new_york_session
3. is_asian_session
4. liquidity_level
5. day_of_week (0=Monday, 6=Sunday)
6. time_of_day_category

Day of Week Indicators (for pattern analysis):
7. is_monday (week start - gap plays)
8. is_tuesday
9. is_wednesday
10. is_thursday
11. is_friday (week end - profit taking)
12. week_position (0.0=start, 1.0=end)
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class MarketContextFeatures:
    """Calculate market context and session features"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config['feature_groups']['market_context']

        # Trading session times (UTC)
        self.sessions = {
            'asian': {'start': 0, 'end': 9},      # 00:00 - 09:00 UTC
            'london': {'start': 8, 'end': 16},     # 08:00 - 16:00 UTC
            'new_york': {'start': 13, 'end': 22}   # 13:00 - 22:00 UTC
        }

    def calculate(self, timestamp: pd.Timestamp, external_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Calculate all market context features"""
        features = {}

        # Convert timestamp to UTC if needed
        if timestamp.tzinfo is None:
            timestamp = timestamp.tz_localize('UTC')
        else:
            timestamp = timestamp.tz_convert('UTC')

        hour_utc = timestamp.hour
        day_of_week = timestamp.dayofweek  # 0=Monday, 6=Sunday

        # 1. Is London session
        features['is_london_session'] = self._is_session_active('london', hour_utc)

        # 2. Is New York session
        features['is_new_york_session'] = self._is_session_active('new_york', hour_utc)

        # 3. Is Asian session
        features['is_asian_session'] = self._is_session_active('asian', hour_utc)

        # 4. Liquidity level (1=low, 2=medium, 3=high)
        features['liquidity_level'] = self._calc_liquidity_level(hour_utc, day_of_week)

        # 5. Day of week (0=Monday, 4=Friday)
        features['day_of_week'] = int(day_of_week)

        # 6. Time of day category
        features['time_of_day_category'] = self._categorize_time_of_day(hour_utc)

        # 7-11. Day of week indicators (one-hot encoding)
        features['is_monday'] = 1 if day_of_week == 0 else 0
        features['is_tuesday'] = 1 if day_of_week == 1 else 0
        features['is_wednesday'] = 1 if day_of_week == 2 else 0
        features['is_thursday'] = 1 if day_of_week == 3 else 0
        features['is_friday'] = 1 if day_of_week == 4 else 0

        # 12. Week position (0.0 = Monday start, 1.0 = Friday end)
        # Useful for detecting end-of-week profit taking or start-of-week gap plays
        features['week_position'] = self._calculate_week_position(day_of_week, hour_utc)

        return features

    def _is_session_active(self, session_name: str, hour_utc: int) -> int:
        """Check if trading session is active"""
        session = self.sessions.get(session_name, {})
        start = session.get('start', 0)
        end = session.get('end', 24)

        if start <= hour_utc < end:
            return 1
        return 0

    def _calc_liquidity_level(self, hour_utc: int, day_of_week: int) -> int:
        """
        Calculate liquidity level
        1 = Low liquidity (Asian session, Friday close)
        2 = Medium liquidity (single session)
        3 = High liquidity (session overlap: London + NY)
        """
        # Friday after 16:00 UTC = low liquidity
        if day_of_week == 4 and hour_utc >= 16:
            return 1

        # Sunday open (Asian session) = low liquidity
        if day_of_week == 6:
            return 1

        # London + NY overlap (13:00 - 16:00 UTC) = high liquidity
        london_active = self._is_session_active('london', hour_utc)
        ny_active = self._is_session_active('new_york', hour_utc)

        if london_active and ny_active:
            return 3  # High liquidity (overlap)

        # Single major session = medium liquidity
        if london_active or ny_active:
            return 2

        # Asian session only = low liquidity
        return 1

    def _categorize_time_of_day(self, hour_utc: int) -> str:
        """
        Categorize time of day for Gold trading
        Returns: 'asian_open', 'london_open', 'ny_open', 'overlap', 'after_hours'
        """
        if 0 <= hour_utc < 3:
            return 'asian_open'
        elif 8 <= hour_utc < 10:
            return 'london_open'
        elif 13 <= hour_utc < 15:
            return 'overlap'  # London + NY overlap (highest liquidity)
        elif 15 <= hour_utc < 17:
            return 'ny_open'
        else:
            return 'after_hours'

    def _calculate_week_position(self, day_of_week: int, hour_utc: int) -> float:
        """
        Calculate position within the trading week (0.0 to 1.0)

        Args:
            day_of_week: 0=Monday, 4=Friday, 5-6=Weekend
            hour_utc: Hour of day (0-23)

        Returns:
            float: 0.0 = Monday 00:00, 1.0 = Friday 21:00 (NY close)

        Use cases:
        - Detect end-of-week profit taking (week_position > 0.8)
        - Detect start-of-week gap plays (week_position < 0.2)
        - Midweek stability patterns (0.4 < week_position < 0.6)
        """
        # Weekend = Friday close position
        if day_of_week >= 5:
            return 1.0

        # Calculate normalized position within work week (Mon-Fri)
        # Total trading hours in week: 5 days × 24 hours = 120 hours
        total_hours_in_week = 120.0

        # Hours elapsed since Monday 00:00
        hours_elapsed = (day_of_week * 24) + hour_utc

        # Normalize to 0.0 - 1.0
        week_position = hours_elapsed / total_hours_in_week

        return round(week_position, 4)
