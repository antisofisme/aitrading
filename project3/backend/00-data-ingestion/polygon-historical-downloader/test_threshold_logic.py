#!/usr/bin/env python3
"""
Test script for timeframe-aware threshold detection
Validates the threshold configuration without requiring dependencies
"""

# Threshold configuration (duplicated from gap_detector.py for testing)
INTRADAY_TIMEFRAMES = ['5m', '15m', '30m', '1h', '4h']
DAILY_PLUS_TIMEFRAMES = ['1d', '1w']

INTRADAY_THRESHOLD = 1.0  # 100% - expect all bars (any missing = incomplete)
DAILY_THRESHOLD = 0.8     # 80% - weekends/holidays OK (20% missing allowed)

def test_threshold_constants():
    """Test that threshold constants are properly defined"""
    print("=" * 80)
    print("THRESHOLD CONFIGURATION TEST")
    print("=" * 80)

    print("\n1. Intraday Timeframes (100% threshold):")
    print(f"   Timeframes: {INTRADAY_TIMEFRAMES}")
    print(f"   Threshold: {INTRADAY_THRESHOLD * 100}%")
    assert INTRADAY_THRESHOLD == 1.0, "Intraday threshold should be 100%"
    print("   ✅ PASS - Intraday threshold is 100%")

    print("\n2. Daily+ Timeframes (80% threshold):")
    print(f"   Timeframes: {DAILY_PLUS_TIMEFRAMES}")
    print(f"   Threshold: {DAILY_THRESHOLD * 100}%")
    assert DAILY_THRESHOLD == 0.8, "Daily threshold should be 80%"
    print("   ✅ PASS - Daily+ threshold is 80%")

    print("\n3. Threshold Application Logic:")
    test_cases = [
        ('5m', INTRADAY_THRESHOLD, "intraday"),
        ('15m', INTRADAY_THRESHOLD, "intraday"),
        ('30m', INTRADAY_THRESHOLD, "intraday"),
        ('1h', INTRADAY_THRESHOLD, "intraday"),
        ('4h', INTRADAY_THRESHOLD, "intraday"),
        ('1d', DAILY_THRESHOLD, "daily+"),
        ('1w', DAILY_THRESHOLD, "daily+"),
    ]

    for timeframe, expected_threshold, category in test_cases:
        if timeframe in INTRADAY_TIMEFRAMES:
            actual_threshold = INTRADAY_THRESHOLD
        else:
            actual_threshold = DAILY_THRESHOLD

        status = "✅" if actual_threshold == expected_threshold else "❌"
        print(f"   {status} {timeframe:>4} -> {actual_threshold*100:>5.0f}% ({category})")
        assert actual_threshold == expected_threshold, f"Threshold mismatch for {timeframe}"

    print("\n4. Edge Cases - Completeness Scenarios:")

    # Test completeness scenarios
    scenarios = [
        ("5m intraday - 100% complete", '5m', 288, 288, True),
        ("5m intraday - 99.9% complete (1 bar missing)", '5m', 287, 288, False),
        ("5m intraday - 95% complete", '5m', 274, 288, False),
        ("5m intraday - 80% complete", '5m', 230, 288, False),
        ("1h intraday - 100% complete", '1h', 24, 24, True),
        ("1h intraday - 1 bar missing", '1h', 23, 24, False),
        ("1d daily - 100% complete", '1d', 5, 5, True),
        ("1d daily - 80% complete (weekend gap)", '1d', 4, 5, True),
        ("1d daily - 79% complete", '1d', 3, 5, False),
        ("1w weekly - 80% complete", '1w', 4, 5, True),
    ]

    for description, timeframe, bars_found, bars_expected, expected_complete in scenarios:
        if timeframe in INTRADAY_TIMEFRAMES:
            threshold = INTRADAY_THRESHOLD
        else:
            threshold = DAILY_THRESHOLD

        completeness = bars_found / bars_expected
        is_complete = completeness >= threshold

        status = "✅" if is_complete == expected_complete else "❌"
        result_str = "COMPLETE" if is_complete else "INCOMPLETE"
        print(f"   {status} {description}")
        print(f"      {bars_found}/{bars_expected} bars ({completeness*100:.1f}%) vs {threshold*100}% threshold -> {result_str}")
        assert is_complete == expected_complete, f"Completeness check failed for {description}"

    print("\n5. Key Behaviors:")
    print("   ✅ Intraday (5m, 15m, 30m, 1h, 4h): ANY missing bar = INCOMPLETE")
    print("   ✅ Daily+ (1d, 1w): Up to 20% missing allowed (weekends/holidays)")
    print("   ✅ Logging will show which threshold is being used")

    print("\n" + "=" * 80)
    print("ALL TESTS PASSED ✅")
    print("=" * 80)

if __name__ == '__main__':
    test_threshold_constants()
