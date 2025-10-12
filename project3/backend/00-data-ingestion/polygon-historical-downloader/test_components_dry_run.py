#!/usr/bin/env python3
"""
Dry-Run Test for Historical Downloader Components
Tests each component WITHOUT writing to database
"""
import sys
import os
import logging
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def test_1_config_loading():
    """Test 1: Verify config loading"""
    logger.info("=" * 80)
    logger.info("TEST 1: Config Loading")
    logger.info("=" * 80)

    try:
        from config import load_configs

        config = load_configs()

        # Verify required keys
        assert 'polygon' in config, "Missing 'polygon' config"
        assert 'clickhouse' in config, "Missing 'clickhouse' config"
        assert 'nats' in config, "Missing 'nats' config"
        assert 'symbols' in config, "Missing 'symbols' config"

        logger.info(f"✅ Config loaded successfully")
        logger.info(f"   - Polygon API: {config['polygon']['base_url']}")
        logger.info(f"   - ClickHouse: {config['clickhouse']['host']}:{config['clickhouse']['port']}")
        logger.info(f"   - NATS: {config['nats']['servers']}")
        logger.info(f"   - Symbols: {len(config['symbols'])} symbols")
        logger.info(f"   - Symbols list: {', '.join(config['symbols'][:5])}...")

        return True, config
    except Exception as e:
        logger.error(f"❌ Config loading failed: {e}", exc_info=True)
        return False, None


def test_2_gap_detector(config):
    """Test 2: Verify gap detection WITHOUT database write"""
    logger.info("=" * 80)
    logger.info("TEST 2: Gap Detector (Read-Only)")
    logger.info("=" * 80)

    try:
        from gap_detector import GapDetector

        # Create gap detector
        gap_detector = GapDetector(config['clickhouse'])

        logger.info(f"✅ GapDetector initialized")
        logger.info(f"   - Max gap check: {gap_detector.max_gap_check_hours} hours")

        # Test gap detection for one symbol (read-only)
        test_symbol = config['symbols'][0]
        start_date = '2025-10-01'
        end_date = '2025-10-10'
        test_timeframe = '1m'  # Test with 1-minute timeframe

        logger.info(f"📊 Testing gap detection for {test_symbol} ({start_date} to {end_date}) @ {test_timeframe}")

        gaps = gap_detector.get_date_range_gaps(test_symbol, start_date, end_date, timeframe=test_timeframe)

        logger.info(f"✅ Gap detection complete")
        logger.info(f"   - Symbol: {test_symbol}")
        logger.info(f"   - Date range: {start_date} to {end_date}")
        logger.info(f"   - Missing dates found: {len(gaps)}")
        if gaps:
            logger.info(f"   - Sample gaps: {gaps[:5]}...")

        gap_detector.client.disconnect()

        return True
    except Exception as e:
        logger.error(f"❌ Gap detector test failed: {e}", exc_info=True)
        return False


def test_3_downloader_dry_run(config):
    """Test 3: Verify Polygon API downloader (DRY RUN - no publish)"""
    logger.info("=" * 80)
    logger.info("TEST 3: Polygon API Downloader (Dry Run)")
    logger.info("=" * 80)

    try:
        from downloader import PolygonDownloader

        # Create downloader WITHOUT publisher (dry run)
        downloader = PolygonDownloader(
            polygon_config=config['polygon'],
            publisher=None  # No publisher = no write to NATS
        )

        logger.info(f"✅ PolygonDownloader initialized (dry-run mode)")
        logger.info(f"   - API Key: {config['polygon']['api_key'][:10]}...")
        logger.info(f"   - Base URL: {config['polygon']['base_url']}")

        # Test download for 1 day
        test_symbol = "XAU/USD"
        test_date = datetime.now() - timedelta(days=3)  # 3 days ago
        from_date = test_date.strftime('%Y-%m-%d')
        to_date = from_date

        logger.info(f"📥 Testing download for {test_symbol} on {from_date}")
        logger.info(f"   (This will FETCH from API but NOT publish to NATS)")

        # Download data (will fetch but not publish since publisher=None)
        bars = downloader.download_bars(
            symbol=test_symbol,
            from_date=from_date,
            to_date=to_date,
            timeframe='minute'
        )

        logger.info(f"✅ Download test complete")
        logger.info(f"   - Symbol: {test_symbol}")
        logger.info(f"   - Date: {from_date}")
        logger.info(f"   - Bars fetched: {len(bars) if bars else 0}")

        if bars:
            sample_bar = bars[0]
            logger.info(f"   - Sample bar: {sample_bar}")
            logger.info(f"   - Bar fields: {list(sample_bar.keys())}")

        return True
    except Exception as e:
        logger.error(f"❌ Downloader test failed: {e}", exc_info=True)
        return False


def test_4_period_tracker_dry_run(config):
    """Test 4: Verify period tracker (Read-Only)"""
    logger.info("=" * 80)
    logger.info("TEST 4: Period Tracker (Read-Only)")
    logger.info("=" * 80)

    try:
        from period_tracker import PeriodTracker

        # Create period tracker
        tracker = PeriodTracker(config['clickhouse'])

        logger.info(f"✅ PeriodTracker initialized")

        # Test checking downloaded periods (read-only)
        test_symbol = config['symbols'][0]
        test_date = '2025-10-01'

        logger.info(f"📊 Checking if {test_symbol} {test_date} is downloaded")

        is_downloaded = tracker.is_period_downloaded(
            symbol=test_symbol,
            timeframe='1m',
            start_date=test_date,
            end_date=test_date
        )

        logger.info(f"✅ Period check complete")
        logger.info(f"   - Symbol: {test_symbol}")
        logger.info(f"   - Date: {test_date}")
        logger.info(f"   - Is downloaded: {is_downloaded}")

        tracker.close()

        return True
    except Exception as e:
        logger.error(f"❌ Period tracker test failed: {e}", exc_info=True)
        return False


def test_5_publisher_dry_run(config):
    """Test 5: Verify NATS publisher can connect (but not publish)"""
    logger.info("=" * 80)
    logger.info("TEST 5: NATS Publisher (Connection Only)")
    logger.info("=" * 80)

    try:
        from publisher import NATSPublisher

        # Create publisher
        publisher = NATSPublisher(config['nats'])

        logger.info(f"✅ NATSPublisher initialized")
        logger.info(f"   - NATS servers: {config['nats']['servers']}")
        logger.info(f"   - Subject: {config['nats']['subject']}")

        # Test connection
        logger.info(f"🔌 Testing NATS connection...")
        publisher.connect()

        logger.info(f"✅ NATS connection successful")
        logger.info(f"   - Connected to: {config['nats']['servers']}")

        # Disconnect without publishing anything
        publisher.disconnect()
        logger.info(f"✅ Disconnected from NATS (no data published)")

        return True
    except Exception as e:
        logger.error(f"❌ NATS publisher test failed: {e}", exc_info=True)
        return False


def main():
    """Run all dry-run tests"""
    logger.info("")
    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + " " * 15 + "HISTORICAL DOWNLOADER - DRY RUN TESTS" + " " * 24 + "║")
    logger.info("║" + " " * 78 + "║")
    logger.info("║" + " " * 10 + "Testing all components WITHOUT writing to database" + " " * 17 + "║")
    logger.info("╚" + "=" * 78 + "╝")
    logger.info("")

    results = {}

    # Test 1: Config
    success, config = test_1_config_loading()
    results['Config Loading'] = success

    if not success or not config:
        logger.error("❌ Cannot proceed without config. Stopping tests.")
        return

    logger.info("")

    # Test 2: Gap Detector
    success = test_2_gap_detector(config)
    results['Gap Detector'] = success
    logger.info("")

    # Test 3: Downloader
    success = test_3_downloader_dry_run(config)
    results['API Downloader'] = success
    logger.info("")

    # Test 4: Period Tracker
    success = test_4_period_tracker_dry_run(config)
    results['Period Tracker'] = success
    logger.info("")

    # Test 5: NATS Publisher
    success = test_5_publisher_dry_run(config)
    results['NATS Publisher'] = success
    logger.info("")

    # Summary
    logger.info("=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status:<10} {test_name}")

    logger.info("=" * 80)

    total = len(results)
    passed = sum(results.values())

    logger.info(f"Total: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 ALL TESTS PASSED! Components are working correctly.")
    else:
        logger.warning(f"⚠️ {total - passed} test(s) failed. Check errors above.")

    logger.info("")
    logger.info("✅ No data was written to database during these tests.")
    logger.info("")


if __name__ == "__main__":
    main()
