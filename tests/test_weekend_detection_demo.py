"""
Demonstration of Timezone-Aware Weekend Detection Fix

Shows the difference between old (day-of-week only) vs new (timezone-aware) logic
"""
from datetime import datetime, timedelta
import pytz

EST = pytz.timezone('America/New_York')


def old_logic_is_market_open(dt: datetime) -> bool:
    """OLD LOGIC: Only checks day of week (INCORRECT)"""
    return dt.weekday() < 5  # Monday=0, Friday=4


def new_logic_is_market_open(dt: datetime) -> bool:
    """NEW LOGIC: Timezone-aware forex market hours (CORRECT)"""
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)

    dt_est = dt.astimezone(EST)
    weekday = dt_est.weekday()
    hour = dt_est.hour

    # Monday-Thursday: Always open
    if 0 <= weekday <= 3:
        return True

    # Friday: Open until 17:00 EST
    if weekday == 4:  # Friday
        return hour < 17

    # Sunday: Open from 17:00 EST onwards
    if weekday == 6:  # Sunday
        return hour >= 17

    # Saturday: Always closed
    return False


def demonstrate_fix():
    """Demonstrate the fix with specific examples"""
    print("=" * 80)
    print("WEEKEND DETECTION FIX DEMONSTRATION")
    print("=" * 80)
    print()

    # Test cases that show the bug
    test_cases = [
        # Friday late afternoon/evening (CRITICAL BUG FIX)
        EST.localize(datetime(2025, 10, 10, 16, 59)),  # Friday 16:59 EST
        EST.localize(datetime(2025, 10, 10, 17, 0)),   # Friday 17:00 EST (MARKET CLOSES)
        EST.localize(datetime(2025, 10, 10, 18, 0)),   # Friday 18:00 EST
        EST.localize(datetime(2025, 10, 10, 23, 59)),  # Friday 23:59 EST

        # Saturday (should always be closed)
        EST.localize(datetime(2025, 10, 11, 12, 0)),   # Saturday 12:00 EST

        # Sunday afternoon/evening (CRITICAL BUG FIX)
        EST.localize(datetime(2025, 10, 12, 16, 59)),  # Sunday 16:59 EST
        EST.localize(datetime(2025, 10, 12, 17, 0)),   # Sunday 17:00 EST (MARKET OPENS)
        EST.localize(datetime(2025, 10, 12, 18, 0)),   # Sunday 18:00 EST
        EST.localize(datetime(2025, 10, 12, 23, 59)),  # Sunday 23:59 EST

        # Monday (should always be open)
        EST.localize(datetime(2025, 10, 13, 0, 0)),    # Monday 00:00 EST
        EST.localize(datetime(2025, 10, 13, 12, 0)),   # Monday 12:00 EST
    ]

    print("Testing edge cases around market open/close times:")
    print("-" * 80)
    print(f"{'Timestamp (EST)':<30} {'Old Logic':<15} {'New Logic':<15} {'Status'}")
    print("-" * 80)

    for dt in test_cases:
        old_result = old_logic_is_market_open(dt)
        new_result = new_logic_is_market_open(dt)

        # Determine expected result
        weekday = dt.weekday()
        hour = dt.hour
        if weekday == 4 and hour >= 17:  # Friday after 17:00
            expected = False
        elif weekday == 5:  # Saturday
            expected = False
        elif weekday == 6 and hour < 17:  # Sunday before 17:00
            expected = False
        else:
            expected = True

        status = ""
        if old_result != expected:
            status = "🐛 OLD BUG"
        if new_result == expected and old_result != expected:
            status = "✅ FIXED"
        elif new_result == expected:
            status = "✅ OK"

        old_str = "OPEN" if old_result else "CLOSED"
        new_str = "OPEN" if new_result else "CLOSED"

        dt_str = dt.strftime("%a %Y-%m-%d %H:%M %Z")
        print(f"{dt_str:<30} {old_str:<15} {new_str:<15} {status}")

    print("-" * 80)
    print()

    # Show specific problems fixed
    print("CRITICAL BUGS FIXED:")
    print("-" * 80)

    # Bug 1: Friday evening after market close
    friday_evening = EST.localize(datetime(2025, 10, 10, 20, 0))
    print(f"1. Friday 20:00 EST (5 PM close + 3 hours):")
    print(f"   OLD: {'OPEN' if old_logic_is_market_open(friday_evening) else 'CLOSED'} "
          f"← WRONG! Includes Friday evening trading")
    print(f"   NEW: {'OPEN' if new_logic_is_market_open(friday_evening) else 'CLOSED'} "
          f"← CORRECT! Market closed after 17:00 EST")
    print()

    # Bug 2: Sunday evening before market open
    sunday_afternoon = EST.localize(datetime(2025, 10, 12, 15, 0))
    print(f"2. Sunday 15:00 EST (2 hours before 5 PM open):")
    print(f"   OLD: {'OPEN' if old_logic_is_market_open(sunday_afternoon) else 'CLOSED'} "
          f"← WRONG! Market still closed")
    print(f"   NEW: {'OPEN' if new_logic_is_market_open(sunday_afternoon) else 'CLOSED'} "
          f"← CORRECT! Market opens at 17:00 EST")
    print()

    # Bug 3: Sunday evening after market open
    sunday_evening = EST.localize(datetime(2025, 10, 12, 20, 0))
    print(f"3. Sunday 20:00 EST (5 PM open + 3 hours):")
    print(f"   OLD: {'OPEN' if old_logic_is_market_open(sunday_evening) else 'CLOSED'} "
          f"← WRONG! Excludes Sunday evening trading")
    print(f"   NEW: {'OPEN' if new_logic_is_market_open(sunday_evening) else 'CLOSED'} "
          f"← CORRECT! Market open after 17:00 EST")
    print()

    print("=" * 80)
    print()

    # Show impact on gap detection
    print("IMPACT ON GAP DETECTION:")
    print("-" * 80)

    # Simulate a week of dates
    start_date = datetime(2025, 10, 6, 0, 0)  # Monday
    dates = [start_date + timedelta(days=i) for i in range(7)]

    print("Dates that would be included in gap detection:")
    print()
    print(f"{'Date':<20} {'Old Logic':<15} {'New Logic':<15} {'Impact'}")
    print("-" * 80)

    for dt in dates:
        dt_utc = pytz.UTC.localize(dt)
        old_included = old_logic_is_market_open(dt_utc)
        new_included = new_logic_is_market_open(dt_utc)

        old_str = "Include" if old_included else "Skip"
        new_str = "Include" if new_included else "Skip"

        impact = ""
        if old_included and not new_included:
            impact = "⚠️  False positive removed"
        elif not old_included and new_included:
            impact = "⚠️  False negative fixed"

        dt_str = dt.strftime("%a %Y-%m-%d")
        print(f"{dt_str:<20} {old_str:<15} {new_str:<15} {impact}")

    print("-" * 80)
    print()

    print("TIMEZONE HANDLING:")
    print("-" * 80)
    print("The new logic automatically handles:")
    print("  - DST transitions (Spring forward, Fall back)")
    print("  - Multiple timezone inputs (UTC, WIB, JST, etc.)")
    print("  - Naive datetimes (assumed UTC)")
    print()

    # DST demonstration
    print("DST Transition Examples:")
    print()

    # March DST (spring forward)
    march_dst = EST.localize(datetime(2025, 3, 9, 3, 0))  # After DST change
    print(f"  March 9, 2025 03:00 EST (after DST spring forward):")
    print(f"    UTC offset: {march_dst.strftime('%z')}")
    print(f"    Market status: {'OPEN' if new_logic_is_market_open(march_dst) else 'CLOSED'}")
    print()

    # November DST (fall back)
    nov_dst = EST.localize(datetime(2025, 11, 2, 3, 0), is_dst=False)  # After DST change
    print(f"  November 2, 2025 03:00 EST (after DST fall back):")
    print(f"    UTC offset: {nov_dst.strftime('%z')}")
    print(f"    Market status: {'OPEN' if new_logic_is_market_open(nov_dst) else 'CLOSED'}")
    print()

    print("=" * 80)


if __name__ == "__main__":
    demonstrate_fix()
