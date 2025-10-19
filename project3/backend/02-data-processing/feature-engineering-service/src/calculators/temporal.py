"""
Temporal Feature Calculator - 21 features
Market sessions (5) + Calendar (10) + Time (6)
"""
import pandas as pd
from datetime import datetime
from typing import Dict, Optional

class TemporalFeatureCalculator:
    """Calculate 21 temporal features"""

    def calculate(self, timestamp: pd.Timestamp) -> Dict[str, Optional[int]]:
        """
        Calculate temporal features from timestamp

        Args:
            timestamp: Current candle timestamp

        Returns:
            Dictionary with 21 temporal features
        """
        dt = pd.to_datetime(timestamp)

        # === MARKET SESSIONS (5) ===
        hour_utc = dt.hour
        active_sessions = []

        # Tokyo: 00:00-09:00 UTC
        if 0 <= hour_utc < 9:
            active_sessions.append('tokyo')

        # London: 08:00-17:00 UTC
        if 8 <= hour_utc < 17:
            active_sessions.append('london')

        # New York: 13:00-22:00 UTC
        if 13 <= hour_utc < 22:
            active_sessions.append('newyork')

        # Sydney: 22:00-07:00 UTC (next day)
        if hour_utc >= 22 or hour_utc < 7:
            active_sessions.append('sydney')

        active_count = len(active_sessions)
        is_overlap = 1 if active_count > 1 else 0
        is_london_newyork_overlap = 1 if ('london' in active_sessions and 'newyork' in active_sessions) else 0

        # Liquidity level
        if active_count >= 3:
            liquidity_level = 'very_high'
        elif active_count == 2:
            liquidity_level = 'high'
        elif active_count == 1:
            liquidity_level = 'medium'
        else:
            liquidity_level = 'low'

        # === CALENDAR (10) ===
        day_of_week = dt.weekday()  # 0 = Monday
        day_name = dt.strftime('%A')
        is_monday = 1 if day_of_week == 0 else 0
        is_friday = 1 if day_of_week == 4 else 0
        is_weekend = 1 if day_of_week >= 5 else 0  # Saturday/Sunday
        week_of_month = (dt.day - 1) // 7 + 1
        week_of_year = dt.isocalendar()[1]
        is_month_start = 1 if dt.day <= 7 else 0
        is_month_end = 1 if dt.day >= 24 else 0
        day_of_month = dt.day

        # === TIME (6) ===
        minute = dt.minute
        quarter_hour = minute // 15  # 0, 1, 2, 3
        is_market_open = 1 if not is_weekend else 0
        is_london_open = 1 if 'london' in active_sessions else 0
        is_ny_open = 1 if 'newyork' in active_sessions else 0

        return {
            # Market Sessions (5)
            'active_sessions': active_sessions,
            'active_count': active_count,
            'is_overlap': is_overlap,
            'liquidity_level': liquidity_level,
            'is_london_newyork_overlap': is_london_newyork_overlap,

            # Calendar (10)
            'day_of_week': day_of_week,
            'day_name': day_name,
            'is_monday': is_monday,
            'is_friday': is_friday,
            'is_weekend': is_weekend,
            'week_of_month': week_of_month,
            'week_of_year': week_of_year,
            'is_month_start': is_month_start,
            'is_month_end': is_month_end,
            'day_of_month': day_of_month,

            # Time (6)
            'hour_utc': hour_utc,
            'minute': minute,
            'quarter_hour': quarter_hour,
            'is_market_open': is_market_open,
            'is_london_open': is_london_open,
            'is_ny_open': is_ny_open
        }
