"""
Standalone Unit Tests for Forex Weekend Detection Logic
Tests the is_forex_market_open() function without external dependencies
"""
from datetime import datetime
import pytz

# Inline the function to test without dependencies
FOREX_OPEN_DAY = 6       # Sunday
FOREX_OPEN_HOUR = 17     # 5 PM EST
FOREX_CLOSE_DAY = 4      # Friday
FOREX_CLOSE_HOUR = 17    # 5 PM EST
EST = pytz.timezone('America/New_York')  # US Eastern Time (handles EDT/EST automatically)


def is_forex_market_open(dt: datetime) -> bool:
    """
    Check if forex market is open at given time

    Forex Market Hours:
    - Opens: Sunday 17:00 EST (5 PM Eastern)
    - Closes: Friday 17:00 EST (5 PM Eastern)
    - Market CLOSED: Friday 17:00 - Sunday 17:00 EST
    - Market OPEN: Sunday 17:00 - Friday 17:00 EST

    Args:
        dt: Timezone-aware datetime (preferably UTC or EST)

    Returns:
        True if market is open, False if closed
    """
    # Convert to EST for consistency
    if dt.tzinfo is None:
        # Assume UTC if naive
        dt = pytz.UTC.localize(dt)

    dt_est = dt.astimezone(EST)

    weekday = dt_est.weekday()  # Monday=0, Sunday=6
    hour = dt_est.hour

    # Monday-Thursday: Always open
    if 0 <= weekday <= 3:
        return True

    # Friday: Open until 17:00 EST
    if weekday == FOREX_CLOSE_DAY:
        return hour < FOREX_CLOSE_HOUR

    # Sunday: Open from 17:00 EST onwards
    if weekday == FOREX_OPEN_DAY:
        return hour >= FOREX_OPEN_HOUR

    # Saturday: Always closed
    return False


def test_friday_before_close():
    """Friday 16:59 EST - Market should be OPEN"""
    dt = EST.localize(datetime(2025, 10, 10, 16, 59))
    assert is_forex_market_open(dt) is True
    print("✅ Friday 16:59 EST - Market OPEN")


def test_friday_at_close():
    """Friday 17:00 EST - Market should be CLOSED"""
    dt = EST.localize(datetime(2025, 10, 10, 17, 0))
    assert is_forex_market_open(dt) is False
    print("✅ Friday 17:00 EST - Market CLOSED")


def test_friday_after_close():
    """Friday 17:01 EST - Market should be CLOSED"""
    dt = EST.localize(datetime(2025, 10, 10, 17, 1))
    assert is_forex_market_open(dt) is False
    print("✅ Friday 17:01 EST - Market CLOSED")


def test_sunday_before_open():
    """Sunday 16:59 EST - Market should be CLOSED"""
    dt = EST.localize(datetime(2025, 10, 12, 16, 59))
    assert is_forex_market_open(dt) is False
    print("✅ Sunday 16:59 EST - Market CLOSED")


def test_sunday_at_open():
    """Sunday 17:00 EST - Market should be OPEN"""
    dt = EST.localize(datetime(2025, 10, 12, 17, 0))
    assert is_forex_market_open(dt) is True
    print("✅ Sunday 17:00 EST - Market OPEN")


def test_sunday_after_open():
    """Sunday 17:01 EST - Market should be OPEN"""
    dt = EST.localize(datetime(2025, 10, 12, 17, 1))
    assert is_forex_market_open(dt) is True
    print("✅ Sunday 17:01 EST - Market OPEN")


def test_monday_midnight():
    """Monday 00:00 EST - Market should be OPEN"""
    dt = EST.localize(datetime(2025, 10, 13, 0, 0))
    assert is_forex_market_open(dt) is True
    print("✅ Monday 00:00 EST - Market OPEN")


def test_saturday_always_closed():
    """Saturday any time - Market should be CLOSED"""
    dt = EST.localize(datetime(2025, 10, 11, 12, 0))
    assert is_forex_market_open(dt) is False
    print("✅ Saturday 12:00 EST - Market CLOSED")


def test_tuesday_midday():
    """Tuesday midday - Market should be OPEN"""
    dt = EST.localize(datetime(2025, 10, 14, 12, 0))
    assert is_forex_market_open(dt) is True
    print("✅ Tuesday 12:00 EST - Market OPEN")


def test_utc_to_est_conversion():
    """Test UTC datetime converts correctly to EST"""
    # Friday 17:00 EST = Friday 21:00 UTC (during EDT)
    dt_utc = pytz.UTC.localize(datetime(2025, 10, 10, 21, 0))
    assert is_forex_market_open(dt_utc) is False
    print("✅ UTC to EST conversion - Friday 21:00 UTC = 17:00 EST (Market CLOSED)")


def test_naive_datetime_assumes_utc():
    """Test naive datetime is treated as UTC"""
    dt_naive = datetime(2025, 10, 13, 12, 0)  # Monday 12:00
    assert is_forex_market_open(dt_naive) is True
    print("✅ Naive datetime assumes UTC - Monday 12:00 UTC (Market OPEN)")


def test_dst_spring_forward():
    """Test DST spring forward (March)"""
    # March 9, 2025 - DST begins
    dt = EST.localize(datetime(2025, 3, 9, 17, 0))
    assert is_forex_market_open(dt) is True
    print("✅ DST spring forward - Sunday 17:00 EST (Market OPEN)")


def test_dst_fall_back():
    """Test DST fall back (November)"""
    # November 2, 2025 - DST ends
    dt = EST.localize(datetime(2025, 11, 2, 17, 0))
    assert is_forex_market_open(dt) is True
    print("✅ DST fall back - Sunday 17:00 EST (Market OPEN)")


def test_full_week_sequence():
    """Test market status for every day at noon"""
    week_tests = [
        (datetime(2025, 10, 6, 12, 0), True, "Monday"),
        (datetime(2025, 10, 7, 12, 0), True, "Tuesday"),
        (datetime(2025, 10, 8, 12, 0), True, "Wednesday"),
        (datetime(2025, 10, 9, 12, 0), True, "Thursday"),
        (datetime(2025, 10, 10, 12, 0), True, "Friday"),
        (datetime(2025, 10, 11, 12, 0), False, "Saturday"),
        (datetime(2025, 10, 12, 12, 0), False, "Sunday before 17:00"),
    ]

    for dt_naive, expected_open, day_name in week_tests:
        dt = EST.localize(dt_naive)
        result = is_forex_market_open(dt)
        assert result == expected_open, f"Failed for {day_name}"
    print("✅ Full week sequence - All days verified correctly")


def test_weekend_transition():
    """Test transition from Friday close to Sunday open"""
    transitions = [
        (datetime(2025, 10, 10, 16, 59), True, "Friday 16:59"),
        (datetime(2025, 10, 10, 17, 0), False, "Friday 17:00"),
        (datetime(2025, 10, 11, 12, 0), False, "Saturday 12:00"),
        (datetime(2025, 10, 12, 16, 59), False, "Sunday 16:59"),
        (datetime(2025, 10, 12, 17, 0), True, "Sunday 17:00"),
        (datetime(2025, 10, 13, 0, 0), True, "Monday 00:00"),
    ]

    for dt_naive, expected_open, label in transitions:
        dt = EST.localize(dt_naive)
        result = is_forex_market_open(dt)
        assert result == expected_open, f"Failed for {label}"
    print("✅ Weekend transition - Friday close to Sunday open verified")


def test_multiple_timezones():
    """Test with different timezone inputs"""
    # Friday 17:00 EST = Friday 21:00 UTC (EDT)
    dt_utc = pytz.UTC.localize(datetime(2025, 10, 10, 21, 0))
    assert is_forex_market_open(dt_utc) is False

    # Friday 17:00 EST = Saturday 05:00 WIB (EDT)
    wib = pytz.timezone('Asia/Jakarta')
    dt_wib = wib.localize(datetime(2025, 10, 11, 5, 0))
    assert is_forex_market_open(dt_wib) is False

    # Monday 12:00 EST = Tuesday 01:00 JST
    jst = pytz.timezone('Asia/Tokyo')
    dt_jst = jst.localize(datetime(2025, 10, 14, 1, 0))
    assert is_forex_market_open(dt_jst) is True

    print("✅ Multiple timezones - UTC, WIB, JST conversions verified")


if __name__ == "__main__":
    print("=" * 80)
    print("FOREX WEEKEND DETECTION - COMPREHENSIVE TESTS")
    print("=" * 80)
    print()

    # Critical edge cases
    print("📋 Critical Edge Cases:")
    test_friday_before_close()
    test_friday_at_close()
    test_friday_after_close()
    test_sunday_before_open()
    test_sunday_at_open()
    test_sunday_after_open()
    test_monday_midnight()
    test_saturday_always_closed()
    print()

    # Weekday tests
    print("📋 Weekday Tests:")
    test_tuesday_midday()
    print()

    # Timezone conversion tests
    print("📋 Timezone Conversion Tests:")
    test_utc_to_est_conversion()
    test_naive_datetime_assumes_utc()
    test_multiple_timezones()
    print()

    # DST tests
    print("📋 DST Transition Tests:")
    test_dst_spring_forward()
    test_dst_fall_back()
    print()

    # Sequence tests
    print("📋 Sequence Tests:")
    test_full_week_sequence()
    test_weekend_transition()
    print()

    print("=" * 80)
    print("✅ ALL TESTS PASSED - Weekend detection logic is correct!")
    print("=" * 80)
    print()
    print("Summary:")
    print("- Friday 16:59 EST → Market OPEN ✅")
    print("- Friday 17:00 EST → Market CLOSED ✅")
    print("- Friday 17:01 EST → Market CLOSED ✅")
    print("- Sunday 16:59 EST → Market CLOSED ✅")
    print("- Sunday 17:00 EST → Market OPEN ✅")
    print("- Sunday 17:01 EST → Market OPEN ✅")
    print("- Monday 00:00 EST → Market OPEN ✅")
    print("- Saturday any time → Market CLOSED ✅")
    print("- DST transitions handled automatically ✅")
    print("- Multiple timezone inputs supported ✅")
