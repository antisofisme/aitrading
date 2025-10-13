"""
Unit tests for Day of Week features
Tests day-based pattern detection features
"""

import pytest
import pandas as pd
from datetime import datetime
from src.features.market_context import MarketContextFeatures


@pytest.fixture
def market_context():
    """Initialize MarketContextFeatures with test config"""
    config = {
        'feature_groups': {
            'market_context': {}
        }
    }
    return MarketContextFeatures(config)


class TestDayOfWeekFeatures:
    """Test day-based trading pattern features"""

    def test_monday_morning_features(self, market_context):
        """Test Monday morning (week start, gap plays)"""
        # Monday 2025-01-06 08:00 UTC (London open)
        timestamp = pd.Timestamp('2025-01-06 08:00:00', tz='UTC')

        features = market_context.calculate(timestamp, {})

        # Check Monday indicator
        assert features['is_monday'] == 1
        assert features['is_tuesday'] == 0
        assert features['is_friday'] == 0

        # Check week position (Monday 08:00 = 8/120 = 0.0667)
        assert 0.06 < features['week_position'] < 0.07

        # Check day_of_week (0=Monday)
        assert features['day_of_week'] == 0

    def test_friday_afternoon_features(self, market_context):
        """Test Friday afternoon (profit taking, position squaring)"""
        # Friday 2025-01-10 18:00 UTC (near NY close)
        timestamp = pd.Timestamp('2025-01-10 18:00:00', tz='UTC')

        features = market_context.calculate(timestamp, {})

        # Check Friday indicator
        assert features['is_friday'] == 1
        assert features['is_monday'] == 0

        # Check week position (Friday 18:00 = (4*24 + 18)/120 = 0.9)
        assert 0.89 < features['week_position'] < 0.91

        # Check day_of_week (4=Friday)
        assert features['day_of_week'] == 4

    def test_wednesday_midday_features(self, market_context):
        """Test Wednesday midday (mid-week stability)"""
        # Wednesday 2025-01-08 12:00 UTC (mid-week, mid-day)
        timestamp = pd.Timestamp('2025-01-08 12:00:00', tz='UTC')

        features = market_context.calculate(timestamp, {})

        # Check Wednesday indicator
        assert features['is_wednesday'] == 1
        assert features['is_monday'] == 0
        assert features['is_friday'] == 0

        # Check week position (Wednesday 12:00 = (2*24 + 12)/120 = 0.5)
        assert 0.49 < features['week_position'] < 0.51

        # Check day_of_week (2=Wednesday)
        assert features['day_of_week'] == 2

    def test_weekend_handling(self, market_context):
        """Test weekend dates return Friday close position"""
        # Saturday 2025-01-11 10:00 UTC
        timestamp = pd.Timestamp('2025-01-11 10:00:00', tz='UTC')

        features = market_context.calculate(timestamp, {})

        # Weekend should map to Friday close (week_position = 1.0)
        assert features['week_position'] == 1.0

        # Day indicators should all be 0 (not Mon-Fri)
        assert features['is_monday'] == 0
        assert features['is_friday'] == 0

    def test_all_days_covered(self, market_context):
        """Test all weekdays have exactly one indicator = 1"""
        test_dates = [
            '2025-01-06',  # Monday
            '2025-01-07',  # Tuesday
            '2025-01-08',  # Wednesday
            '2025-01-09',  # Thursday
            '2025-01-10',  # Friday
        ]

        for date_str in test_dates:
            timestamp = pd.Timestamp(f'{date_str} 12:00:00', tz='UTC')
            features = market_context.calculate(timestamp, {})

            # Count day indicators
            day_indicators = [
                features['is_monday'],
                features['is_tuesday'],
                features['is_wednesday'],
                features['is_thursday'],
                features['is_friday']
            ]

            # Exactly one should be 1, rest should be 0
            assert sum(day_indicators) == 1

    def test_week_position_progression(self, market_context):
        """Test week_position increases monotonically through the week"""
        positions = []

        # Test Monday through Friday at same hour
        for day_offset in range(5):  # Mon-Fri
            date = pd.Timestamp('2025-01-06', tz='UTC') + pd.Timedelta(days=day_offset)
            timestamp = date.replace(hour=12)

            features = market_context.calculate(timestamp, {})
            positions.append(features['week_position'])

        # Check monotonic increase
        for i in range(len(positions) - 1):
            assert positions[i] < positions[i + 1], \
                f"Week position should increase: {positions}"

    def test_hour_progression_within_day(self, market_context):
        """Test week_position increases within a single day"""
        # Test Monday at different hours
        base_date = pd.Timestamp('2025-01-06', tz='UTC')
        positions = []

        for hour in [0, 6, 12, 18, 23]:
            timestamp = base_date.replace(hour=hour)
            features = market_context.calculate(timestamp, {})
            positions.append(features['week_position'])

        # Check monotonic increase
        for i in range(len(positions) - 1):
            assert positions[i] < positions[i + 1], \
                f"Week position should increase within day: {positions}"

    def test_feature_types(self, market_context):
        """Test all features return correct types"""
        timestamp = pd.Timestamp('2025-01-06 12:00:00', tz='UTC')
        features = market_context.calculate(timestamp, {})

        # Day indicators should be integers
        assert isinstance(features['is_monday'], int)
        assert isinstance(features['is_friday'], int)

        # week_position should be float
        assert isinstance(features['week_position'], float)

        # day_of_week should be integer
        assert isinstance(features['day_of_week'], int)

        # Check ranges
        assert 0 <= features['week_position'] <= 1.0
        assert 0 <= features['day_of_week'] <= 6
        assert features['is_monday'] in [0, 1]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
