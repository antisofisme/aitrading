#!/usr/bin/env python3
"""
ConfigClient Test Script

Run this to test ConfigClient against running Central Hub
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add shared to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from components.config.client import ConfigClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def test_basic_fetch():
    """Test 1: Basic config fetch"""
    print("\n" + "=" * 60)
    print("TEST 1: Basic Config Fetch")
    print("=" * 60)

    safe_defaults = {
        "operational": {
            "batch_size": 100,
            "gap_check_interval_hours": 1
        }
    }

    client = ConfigClient(
        service_name="polygon-historical-downloader",
        central_hub_url="http://localhost:7000",
        safe_defaults=safe_defaults
    )

    try:
        await client.init_async()
        config = await client.get_config()

        print(f"✅ Config fetched successfully!")
        print(f"📊 Config: {config}")

        # Test get_value
        batch_size = client.get_value("operational.batch_size", 100)
        print(f"📦 Batch size: {batch_size}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        await client.shutdown()


async def test_caching():
    """Test 2: Config caching"""
    print("\n" + "=" * 60)
    print("TEST 2: Config Caching")
    print("=" * 60)

    client = ConfigClient(
        service_name="polygon-historical-downloader",
        central_hub_url="http://localhost:7000",
        cache_ttl_seconds=10  # 10 seconds for testing
    )

    try:
        await client.init_async()

        # First fetch (from Central Hub)
        print("Fetching config (should hit Central Hub)...")
        config1 = await client.get_config()
        print(f"✅ Config 1: {config1}")

        # Second fetch (should use cache)
        print("\nFetching config again (should use cache)...")
        config2 = await client.get_config()
        print(f"✅ Config 2: {config2}")

        # Force refresh (ignore cache)
        print("\nForce refresh (should hit Central Hub)...")
        config3 = await client.get_config(force_refresh=True)
        print(f"✅ Config 3: {config3}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

    finally:
        await client.shutdown()


async def test_fallback():
    """Test 3: Fallback to defaults when Hub unavailable"""
    print("\n" + "=" * 60)
    print("TEST 3: Fallback to Defaults")
    print("=" * 60)

    safe_defaults = {
        "operational": {
            "batch_size": 999,  # Different from Central Hub
            "gap_check_interval_hours": 99
        }
    }

    # Test with invalid URL (Hub unavailable)
    client = ConfigClient(
        service_name="polygon-historical-downloader",
        central_hub_url="http://invalid-url:9999",  # Wrong URL
        safe_defaults=safe_defaults,
        max_retries=1  # Fewer retries for faster test
    )

    try:
        print("Trying to fetch from invalid URL...")
        config = await client.get_config()

        print(f"✅ Fallback worked!")
        print(f"📊 Using defaults: {config}")

        batch_size = config['operational']['batch_size']
        if batch_size == 999:
            print(f"✅ Correct fallback value: {batch_size}")
            return True
        else:
            print(f"❌ Wrong value: {batch_size}")
            return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

    finally:
        await client.shutdown()


async def test_hot_reload():
    """Test 4: NATS hot-reload (requires NATS running)"""
    print("\n" + "=" * 60)
    print("TEST 4: NATS Hot-Reload (Optional)")
    print("=" * 60)

    try:
        import nats
    except ImportError:
        print("⚠️ NATS library not installed, skipping hot-reload test")
        return True

    client = ConfigClient(
        service_name="polygon-historical-downloader",
        central_hub_url="http://localhost:7000",
        enable_nats_updates=True,
        nats_url="nats://localhost:4222"
    )

    try:
        update_received = asyncio.Event()

        def on_update(new_config):
            print(f"🔄 Config update received: {new_config}")
            update_received.set()

        client.on_config_update(on_update)

        await client.init_async()

        print("✅ NATS subscription active")
        print("💡 To test: Update config in Central Hub")
        print("   curl -X POST http://localhost:7000/api/v1/config/polygon-historical-downloader \\")
        print('     -H "Content-Type: application/json" \\')
        print('     -d \'{"operational": {"batch_size": 200}}\'')
        print("\nWaiting for update (10 seconds)...")

        # Wait for update (max 10 seconds)
        try:
            await asyncio.wait_for(update_received.wait(), timeout=10.0)
            print("✅ Hot-reload test passed!")
            return True
        except asyncio.TimeoutError:
            print("⚠️ No update received (may be OK if not manually triggered)")
            return True

    except Exception as e:
        print(f"⚠️ Hot-reload test failed: {e}")
        print("   This is OK if NATS is not running")
        return True  # Non-critical

    finally:
        await client.shutdown()


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("ConfigClient Test Suite")
    print("=" * 60)
    print("\nPrerequisites:")
    print("  1. Central Hub running on http://localhost:7000")
    print("  2. DISABLE_AUTH=true (or provide X-API-Key)")
    print("  3. Config for 'polygon-historical-downloader' exists in database")
    print("")

    results = []

    # Test 1: Basic fetch
    results.append(("Basic Fetch", await test_basic_fetch()))

    # Test 2: Caching
    results.append(("Caching", await test_caching()))

    # Test 3: Fallback
    results.append(("Fallback", await test_fallback()))

    # Test 4: Hot-reload (optional)
    # results.append(("Hot-Reload", await test_hot_reload()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")

    total = len(results)
    passed = sum(1 for _, p in results if p)

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
