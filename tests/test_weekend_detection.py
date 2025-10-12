"""
Unit Tests for Forex Weekend Detection Logic

Tests timezone-aware weekend detection for forex market hours:
- Opens: Sunday 17:00 EST
- Closes: Friday 17:00 EST
- Handles DST transitions automatically via pytz
"""
import pytest
from datetime import datetime
import pytz
import sys
from pathlib import Path

# Add source path
sys.path.insert(0, str(Path(__file__).parent.parent / 'project3' / 'backend' / '00-data-ingestion' / 'polygon-historical-downloader' / 'src'))

from gap_detector import is_forex_market_open, EST, FOREX_OPEN_HOUR, FOREX_CLOSE_HOUR


class TestForexMarketHours:
    """Test forex market open/close detection"""

    def test_friday_before_close_market_open(self):
        """Friday 16:59 EST - Market should be OPEN"""
        # October 10, 2025 is a Friday
        dt = EST.localize(datetime(2025, 10, 10, 16, 59))
        assert is_forex_market_open(dt) is True, "Market should be OPEN at Friday 16:59 EST"

    def test_friday_at_close_market_closed(self):
        """Friday 17:00 EST - Market should be CLOSED"""
        dt = EST.localize(datetime(2025, 10, 10, 17, 0))
        assert is_forex_market_open(dt) is False, "Market should be CLOSED at Friday 17:00 EST"

    def test_friday_after_close_market_closed(self):
        """Friday 17:01 EST - Market should be CLOSED"""
        dt = EST.localize(datetime(2025, 10, 10, 17, 1))
        assert is_forex_market_open(dt) is False, "Market should be CLOSED at Friday 17:01 EST"

    def test_sunday_before_open_market_closed(self):
        """Sunday 16:59 EST - Market should be CLOSED"""
        # October 12, 2025 is a Sunday
        dt = EST.localize(datetime(2025, 10, 12, 16, 59))
        assert is_forex_market_open(dt) is False, "Market should be CLOSED at Sunday 16:59 EST"

    def test_sunday_at_open_market_open(self):
        """Sunday 17:00 EST - Market should be OPEN"""
        dt = EST.localize(datetime(2025, 10, 12, 17, 0))
        assert is_forex_market_open(dt) is True, "Market should be OPEN at Sunday 17:00 EST"

    def test_sunday_after_open_market_open(self):
        """Sunday 17:01 EST - Market should be OPEN"""
        dt = EST.localize(datetime(2025, 10, 12, 17, 1))
        assert is_forex_market_open(dt) is True, "Market should be OPEN at Sunday 17:01 EST"

    def test_monday_midnight_market_open(self):
        """Monday 00:00 EST - Market should be OPEN"""
        # October 13, 2025 is a Monday
        dt = EST.localize(datetime(2025, 10, 13, 0, 0))
        assert is_forex_market_open(dt) is True, "Market should be OPEN at Monday 00:00 EST"

    def test_saturday_always_closed(self):
        """Saturday any time - Market should be CLOSED"""
        # October 11, 2025 is a Saturday
        dt = EST.localize(datetime(2025, 10, 11, 12, 0))
        assert is_forex_market_open(dt) is False, "Market should be CLOSED on Saturday"

    def test_tuesday_midday_market_open(self):
        """Tuesday midday - Market should be OPEN"""
        # October 14, 2025 is a Tuesday
        dt = EST.localize(datetime(2025, 10, 14, 12, 0))
        assert is_forex_market_open(dt) is True, "Market should be OPEN on Tuesday"

    def test_wednesday_market_open(self):
        """Wednesday - Market should be OPEN"""
        # October 15, 2025 is a Wednesday
        dt = EST.localize(datetime(2025, 10, 15, 12, 0))
        assert is_forex_market_open(dt) is True, "Market should be OPEN on Wednesday"

    def test_thursday_market_open(self):
        """Thursday - Market should be OPEN"""
        # October 16, 2025 is a Thursday
        dt = EST.localize(datetime(2025, 10, 16, 12, 0))
        assert is_forex_market_open(dt) is True, "Market should be OPEN on Thursday"


class TestTimezoneConversion:
    """Test timezone conversion (UTC to EST)"""

    def test_utc_to_est_conversion(self):
        """Test UTC datetime converts correctly to EST"""
        # Friday 17:00 EST = Friday 21:00 UTC (during EDT - daylight saving)
        # Friday 17:00 EST = Friday 22:00 UTC (during EST - standard time)
        dt_utc = pytz.UTC.localize(datetime(2025, 10, 10, 21, 0))  # October is EDT
        assert is_forex_market_open(dt_utc) is False, "Market should be CLOSED at Friday 17:00 EST"

    def test_naive_datetime_assumes_utc(self):
        """Test naive datetime is treated as UTC"""
        # Naive datetime (no timezone)
        dt_naive = datetime(2025, 10, 13, 12, 0)  # Monday 12:00 (assumed UTC)
        assert is_forex_market_open(dt_naive) is True, "Market should be OPEN on Monday"


class TestDSTTransitions:
    """Test Daylight Saving Time transitions"""

    def test_dst_spring_forward(self):
        """Test DST spring forward (March) - 2nd Sunday"""
        # March 9, 2025 - DST begins (2:00 AM -> 3:00 AM)
        # Sunday 17:00 EST should still work correctly
        dt = EST.localize(datetime(2025, 3, 9, 17, 0))
        assert is_forex_market_open(dt) is True, "Market should be OPEN at Sunday 17:00 EST (DST starts)"

    def test_dst_fall_back(self):
        """Test DST fall back (November) - 1st Sunday"""
        # November 2, 2025 - DST ends (2:00 AM -> 1:00 AM)
        # Sunday 17:00 EST should still work correctly
        dt = EST.localize(datetime(2025, 11, 2, 17, 0))
        assert is_forex_market_open(dt) is True, "Market should be OPEN at Sunday 17:00 EST (DST ends)"

    def test_edt_summer_time(self):
        """Test during EDT (Eastern Daylight Time - summer)"""
        # July is EDT (UTC-4)
        dt = EST.localize(datetime(2025, 7, 21, 12, 0))  # Monday in July
        assert is_forex_market_open(dt) is True, "Market should be OPEN during EDT"

    def test_est_winter_time(self):
        """Test during EST (Eastern Standard Time - winter)"""
        # January is EST (UTC-5)
        dt = EST.localize(datetime(2025, 1, 20, 12, 0))  # Monday in January
        assert is_forex_market_open(dt) is True, "Market should be OPEN during EST"


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_friday_late_evening(self):
        """Friday 23:59 EST - Market should be CLOSED"""
        dt = EST.localize(datetime(2025, 10, 10, 23, 59))
        assert is_forex_market_open(dt) is False, "Market should be CLOSED at Friday 23:59 EST"

    def test_sunday_early_morning(self):
        """Sunday 00:00 EST - Market should be CLOSED"""
        dt = EST.localize(datetime(2025, 10, 12, 0, 0))
        assert is_forex_market_open(dt) is False, "Market should be CLOSED at Sunday 00:00 EST"

    def test_sunday_late_evening(self):
        """Sunday 23:59 EST - Market should be OPEN"""
        dt = EST.localize(datetime(2025, 10, 12, 23, 59))
        assert is_forex_market_open(dt) is True, "Market should be OPEN at Sunday 23:59 EST"

    def test_saturday_midnight(self):
        """Saturday 00:00 EST - Market should be CLOSED"""
        dt = EST.localize(datetime(2025, 10, 11, 0, 0))
        assert is_forex_market_open(dt) is False, "Market should be CLOSED at Saturday 00:00 EST"

    def test_saturday_late_evening(self):
        """Saturday 23:59 EST - Market should be CLOSED"""
        dt = EST.localize(datetime(2025, 10, 11, 23, 59))
        assert is_forex_market_open(dt) is False, "Market should be CLOSED at Saturday 23:59 EST"


class TestWeekdaySequence:
    """Test full week sequence"""

    def test_full_week_sequence(self):
        """Test market status for every day of the week at noon"""
        # Week of October 6-12, 2025
        week = [
            (datetime(2025, 10, 6, 12, 0), True),   # Monday - OPEN
            (datetime(2025, 10, 7, 12, 0), True),   # Tuesday - OPEN
            (datetime(2025, 10, 8, 12, 0), True),   # Wednesday - OPEN
            (datetime(2025, 10, 9, 12, 0), True),   # Thursday - OPEN
            (datetime(2025, 10, 10, 12, 0), True),  # Friday - OPEN
            (datetime(2025, 10, 11, 12, 0), False), # Saturday - CLOSED
            (datetime(2025, 10, 12, 12, 0), False), # Sunday - CLOSED (before 17:00)
        ]

        for dt_naive, expected_open in week:
            dt = EST.localize(dt_naive)
            result = is_forex_market_open(dt)
            assert result == expected_open, f"Market status incorrect for {dt.strftime('%A')}"

    def test_weekend_close_to_open_transition(self):
        """Test transition from Friday close to Sunday open"""
        times = [
            (datetime(2025, 10, 10, 16, 59), True),   # Friday 16:59 - OPEN
            (datetime(2025, 10, 10, 17, 0), False),   # Friday 17:00 - CLOSED
            (datetime(2025, 10, 11, 12, 0), False),   # Saturday 12:00 - CLOSED
            (datetime(2025, 10, 12, 16, 59), False),  # Sunday 16:59 - CLOSED
            (datetime(2025, 10, 12, 17, 0), True),    # Sunday 17:00 - OPEN
            (datetime(2025, 10, 13, 0, 0), True),     # Monday 00:00 - OPEN
        ]

        for dt_naive, expected_open in times:
            dt = EST.localize(dt_naive)
            result = is_forex_market_open(dt)
            assert result == expected_open, f"Market status incorrect for {dt}"


class TestMultipleTimezones:
    """Test with multiple timezone inputs"""

    def test_utc_input(self):
        """Test with UTC timezone input"""
        # Friday 17:00 EST = Friday 21:00 UTC (EDT)
        dt_utc = pytz.UTC.localize(datetime(2025, 10, 10, 21, 0))
        assert is_forex_market_open(dt_utc) is False, "Market should be CLOSED"

    def test_asia_jakarta_input(self):
        """Test with Asia/Jakarta (WIB) timezone input"""
        # Friday 17:00 EST = Saturday 05:00 WIB (EDT)
        wib = pytz.timezone('Asia/Jakarta')
        dt_wib = wib.localize(datetime(2025, 10, 11, 5, 0))
        assert is_forex_market_open(dt_wib) is False, "Market should be CLOSED"

    def test_asia_tokyo_input(self):
        """Test with Asia/Tokyo (JST) timezone input"""
        # Monday 12:00 EST = Tuesday 01:00 JST
        jst = pytz.timezone('Asia/Tokyo')
        dt_jst = jst.localize(datetime(2025, 10, 14, 1, 0))
        assert is_forex_market_open(dt_jst) is True, "Market should be OPEN"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
