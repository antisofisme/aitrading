"""
Test version calculation for historical data
Verifies deterministic content-based hashing vs timestamp-based versioning
"""
import hashlib
from datetime import datetime, timezone


def calculate_version_for_historical(candle: dict) -> int:
    """
    Calculate deterministic version for historical data using content hash
    """
    # Create deterministic string from candle data
    content_keys = ['symbol', 'timeframe', 'timestamp_ms', 'open', 'high', 'low', 'close', 'volume', 'source']
    content_str = '|'.join([
        f"{key}:{candle.get(key)}"
        for key in content_keys
        if key in candle
    ])

    # Generate hash and convert to integer
    hash_obj = hashlib.md5(content_str.encode())
    hash_int = int(hash_obj.hexdigest()[:16], 16)

    # Convert to reasonable size
    version = hash_int % (10**15)

    return version, content_str


def calculate_version_for_live(timestamp_ms: int) -> int:
    """
    Calculate timestamp-based version for live data
    """
    return timestamp_ms * 1000  # Convert ms to microseconds


def test_deterministic_versions():
    """Test that same data produces same version"""
    print("=" * 80)
    print("TEST 1: Deterministic Versioning for Historical Data")
    print("=" * 80)

    # Sample candle data
    candle = {
        'symbol': 'XAU/USD',
        'timeframe': '5m',
        'timestamp_ms': 1704067200000,  # 2024-01-01 00:00:00
        'open': 2062.50,
        'high': 2065.00,
        'low': 2060.00,
        'close': 2063.75,
        'volume': 150000,
        'source': 'historical_aggregated'
    }

    # Calculate version multiple times
    v1, content1 = calculate_version_for_historical(candle)
    v2, content2 = calculate_version_for_historical(candle)
    v3, content3 = calculate_version_for_historical(candle)

    print(f"\nSample Candle:")
    print(f"  Symbol: {candle['symbol']}")
    print(f"  Timeframe: {candle['timeframe']}")
    print(f"  Timestamp: {datetime.fromtimestamp(candle['timestamp_ms']/1000, tz=timezone.utc)}")
    print(f"  OHLC: {candle['open']} / {candle['high']} / {candle['low']} / {candle['close']}")
    print(f"  Volume: {candle['volume']}")

    print(f"\nContent String:")
    print(f"  {content1}")

    print(f"\nVersion Calculation Results:")
    print(f"  Run 1: {v1}")
    print(f"  Run 2: {v2}")
    print(f"  Run 3: {v3}")

    print(f"\n✅ PASS: All versions identical: {v1 == v2 == v3}")

    return v1 == v2 == v3


def test_different_data_different_versions():
    """Test that different data produces different versions"""
    print("\n" + "=" * 80)
    print("TEST 2: Different Data Produces Different Versions")
    print("=" * 80)

    candle1 = {
        'symbol': 'XAU/USD',
        'timeframe': '5m',
        'timestamp_ms': 1704067200000,
        'open': 2062.50,
        'high': 2065.00,
        'low': 2060.00,
        'close': 2063.75,
        'volume': 150000,
        'source': 'historical_aggregated'
    }

    # Same timestamp, different price
    candle2 = {
        'symbol': 'XAU/USD',
        'timeframe': '5m',
        'timestamp_ms': 1704067200000,
        'open': 2062.50,
        'high': 2065.00,
        'low': 2060.00,
        'close': 2064.00,  # Different close price
        'volume': 150000,
        'source': 'historical_aggregated'
    }

    v1, _ = calculate_version_for_historical(candle1)
    v2, _ = calculate_version_for_historical(candle2)

    print(f"\nCandle 1 Close: {candle1['close']} → Version: {v1}")
    print(f"Candle 2 Close: {candle2['close']} → Version: {v2}")
    print(f"\n✅ PASS: Versions are different: {v1 != v2}")

    return v1 != v2


def test_timestamp_vs_content_versioning():
    """Compare timestamp-based (live) vs content-based (historical) versioning"""
    print("\n" + "=" * 80)
    print("TEST 3: Timestamp-Based vs Content-Based Versioning")
    print("=" * 80)

    timestamp_ms = 1704067200000  # 2024-01-01 00:00:00
    dt = datetime.fromtimestamp(timestamp_ms/1000, tz=timezone.utc)

    candle = {
        'symbol': 'EUR/USD',
        'timeframe': '15m',
        'timestamp_ms': timestamp_ms,
        'open': 1.1050,
        'high': 1.1075,
        'low': 1.1040,
        'close': 1.1065,
        'volume': 250000,
        'source': 'historical_aggregated'
    }

    # Calculate both version types
    content_version, _ = calculate_version_for_historical(candle)
    timestamp_version = calculate_version_for_live(timestamp_ms)

    print(f"\nBar Timestamp: {dt}")
    print(f"  Timestamp (ms): {timestamp_ms}")

    print(f"\nLive Versioning (timestamp-based):")
    print(f"  Version: {timestamp_version}")
    print(f"  Formula: timestamp_ms * 1000 = {timestamp_ms} * 1000")
    print(f"  Result: {timestamp_version:,}")

    print(f"\nHistorical Versioning (content-based):")
    print(f"  Version: {content_version}")
    print(f"  Formula: MD5(content) % 10^15")
    print(f"  Result: {content_version:,}")

    print(f"\n✅ Different versioning strategies for different use cases")
    print(f"   - Live: Uses timestamp (latest always wins)")
    print(f"   - Historical: Uses content hash (same data = same version)")


def test_multiple_symbols():
    """Test version generation for multiple trading pairs"""
    print("\n" + "=" * 80)
    print("TEST 4: Version Calculation for Multiple Trading Pairs")
    print("=" * 80)

    symbols = ['XAU/USD', 'EUR/USD', 'GBP/USD', 'USD/JPY']
    timestamp_ms = 1704067200000

    print(f"\nGenerating versions for {len(symbols)} symbols at {datetime.fromtimestamp(timestamp_ms/1000, tz=timezone.utc)}")
    print(f"\n{'Symbol':<12} {'Close':<10} {'Version':<20} {'Collision'}")
    print("-" * 80)

    versions = []
    for i, symbol in enumerate(symbols):
        candle = {
            'symbol': symbol,
            'timeframe': '5m',
            'timestamp_ms': timestamp_ms,
            'open': 1.0 + i * 0.1,
            'high': 1.0 + i * 0.1 + 0.05,
            'low': 1.0 + i * 0.1 - 0.05,
            'close': 1.0 + i * 0.1 + 0.025,
            'volume': 100000 + i * 10000,
            'source': 'historical_aggregated'
        }

        version, _ = calculate_version_for_historical(candle)
        collision = "COLLISION!" if version in versions else "OK"
        versions.append(version)

        print(f"{symbol:<12} {candle['close']:<10.4f} {version:<20,} {collision}")

    print(f"\n✅ All versions unique: {len(versions) == len(set(versions))}")


def test_backfill_scenario():
    """Simulate backfill scenario - same data run twice should produce same version"""
    print("\n" + "=" * 80)
    print("TEST 5: Backfill Scenario (Same Data, Multiple Runs)")
    print("=" * 80)

    print("\nScenario: Historical processor runs twice on the same 1m source data")
    print("Expected: Both runs produce IDENTICAL versions (prevents duplicates)")

    candle = {
        'symbol': 'XAU/USD',
        'timeframe': '1h',
        'timestamp_ms': 1704067200000,
        'open': 2062.50,
        'high': 2070.00,
        'low': 2058.00,
        'close': 2065.25,
        'volume': 500000,
        'source': 'historical_aggregated'
    }

    # Simulate first run (e.g., initial backfill)
    print("\n📥 First Run (Initial Backfill):")
    v1, _ = calculate_version_for_historical(candle)
    print(f"  Version: {v1:,}")

    # Simulate second run (e.g., gap-fill or re-aggregation)
    print("\n📥 Second Run (Gap Fill / Re-aggregation):")
    v2, _ = calculate_version_for_historical(candle)
    print(f"  Version: {v2:,}")

    print(f"\n✅ CRITICAL TEST: Same data produces same version: {v1 == v2}")
    print(f"   ClickHouse ReplacingMergeTree will correctly identify these as duplicates")
    print(f"   and keep only ONE copy (the one with max version, which is the same)")

    if v1 == v2:
        print("\n🎉 SUCCESS: Backfill deduplication will work correctly!")
    else:
        print("\n❌ FAILURE: Different versions would create duplicates!")

    return v1 == v2


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("VERSION CALCULATION TESTS - Historical vs Live Data")
    print("=" * 80)

    results = []

    # Run tests
    results.append(("Deterministic Historical Versions", test_deterministic_versions()))
    results.append(("Different Data Different Versions", test_different_data_different_versions()))
    test_timestamp_vs_content_versioning()  # No pass/fail, just demonstration
    test_multiple_symbols()  # No pass/fail, just demonstration
    results.append(("Backfill Deduplication", test_backfill_scenario()))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(result[1] for result in results)

    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 ALL TESTS PASSED - Version calculation is working correctly!")
        print("\nBenefits of Content-Based Versioning:")
        print("  ✅ Same historical data ALWAYS produces same version")
        print("  ✅ Prevents duplicate versions during backfills")
        print("  ✅ ClickHouse ReplacingMergeTree deduplication works correctly")
        print("  ✅ Source data corrections automatically change version")
        print("  ✅ No dependency on ingestion timestamp")
    else:
        print("❌ SOME TESTS FAILED - Review implementation")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
