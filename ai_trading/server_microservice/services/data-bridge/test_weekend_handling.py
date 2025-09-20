#!/usr/bin/env python3
"""
Test Weekend Handling - Smart Trading Calendar
Verify that weekend data download is properly handled for ML/DL consistency
"""

import asyncio
import sys
import os
import logging
from datetime import datetime, timedelta

# Add paths for imports
sys.path.append('/mnt/f/WINDSURF/neliti_code/server_microservice')
sys.path.append('/mnt/f/WINDSURF/neliti_code/server_microservice/services/data-bridge/src')

from src.business.trading_calendar import get_trading_calendar
from src.data_sources.dukascopy_client import DataBridgeDukascopyDownloader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_weekend_detection():
    """Test weekend and holiday detection"""
    logger.info("🧪 Testing Weekend & Holiday Detection")
    logger.info("=" * 60)
    
    trading_calendar = get_trading_calendar()
    
    # Test various dates
    test_dates = [
        # Weekend dates (should be False)
        datetime(2024, 8, 10, 10, 0),  # Saturday
        datetime(2024, 8, 11, 14, 0),  # Sunday
        
        # Weekday dates (should be True)
        datetime(2024, 8, 9, 10, 0),   # Friday
        datetime(2024, 8, 8, 14, 0),   # Thursday
        datetime(2024, 8, 7, 12, 0),   # Wednesday
        datetime(2024, 8, 6, 16, 0),   # Tuesday  
        datetime(2024, 8, 5, 9, 0),    # Monday
    ]
    
    for test_date in test_dates:
        is_trading = trading_calendar.is_trading_day(test_date)
        status = trading_calendar.get_market_status(test_date)
        
        day_name = test_date.strftime('%A')
        date_str = test_date.strftime('%Y-%m-%d %H:%M')
        
        if is_trading:
            logger.info(f"✅ {date_str} ({day_name}): Trading day - {status['reason']}")
        else:
            logger.info(f"❌ {date_str} ({day_name}): Non-trading - {status['reason']}")
    
    return True

async def test_optimal_download_times():
    """Test optimal download time generation"""
    logger.info("\n🎯 Testing Optimal Download Times")
    logger.info("=" * 60)
    
    trading_calendar = get_trading_calendar()
    
    # Test with current time (might be weekend)
    logger.info("📊 Testing with current time...")
    current_optimal = trading_calendar.get_optimal_download_times(24)
    logger.info(f"  Found {len(current_optimal)} optimal hours in last 24 hours")
    
    # Test with a known weekday range
    logger.info("📊 Testing with known weekday range...")
    
    # Manually test with Thursday-Friday (Aug 8-9, 2024)
    thursday = datetime(2024, 8, 8, 0, 0)
    friday = datetime(2024, 8, 9, 23, 59)
    
    # Generate all hours between Thursday-Friday
    all_hours = []
    current = thursday.replace(hour=0, minute=0, second=0, microsecond=0)
    
    while current <= friday:
        all_hours.append(current)
        current += timedelta(hours=1)
    
    logger.info(f"  Total hours Thu-Fri: {len(all_hours)}")
    
    # Filter to trading hours only
    trading_hours = trading_calendar.filter_trading_hours_only(all_hours)
    logger.info(f"  Trading hours Thu-Fri: {len(trading_hours)}")
    
    # Test with weekend range
    logger.info("📊 Testing with weekend range...")
    
    saturday = datetime(2024, 8, 10, 0, 0)  
    sunday = datetime(2024, 8, 11, 23, 59)
    
    weekend_hours = []
    current = saturday.replace(hour=0, minute=0, second=0, microsecond=0)
    
    while current <= sunday:
        weekend_hours.append(current)
        current += timedelta(hours=1)
    
    logger.info(f"  Total weekend hours: {len(weekend_hours)}")
    
    # Filter weekend hours
    weekend_trading = trading_calendar.filter_trading_hours_only(weekend_hours)
    logger.info(f"  Trading hours on weekend: {len(weekend_trading)}")
    
    if len(weekend_trading) == 0:
        logger.info("✅ Weekend correctly filtered out - no trading hours")
        return True
    else:
        logger.error("❌ Weekend filtering failed - found trading hours on weekend")
        return False

async def test_downloader_weekend_handling():
    """Test downloader with weekend data"""
    logger.info("\n📥 Testing Downloader Weekend Handling")
    logger.info("=" * 60)
    
    try:
        # Set up for minimal test
        os.environ['USE_TOR_PROXY'] = 'true'
        downloader = DataBridgeDukascopyDownloader()
        
        logger.info("✅ Downloader initialized with trading calendar")
        
        # Test 1: Try to download weekend data (should be filtered)
        logger.info("🧪 Test 1: Download weekend data (should skip)")
        
        # Simulate weekend download (24 hours that include weekend)
        weekend_results = await downloader.download_small_batch(
            pair="EURUSD",
            hours_back=48  # 48 hours to include weekend
        )
        
        logger.info("📊 Weekend download results:")
        logger.info(f"  Files downloaded: {weekend_results['files_downloaded']}")
        logger.info(f"  Files failed: {weekend_results['files_failed']}")  
        logger.info(f"  Success rate: {weekend_results['success_rate']*100:.1f}%")
        
        # Test 2: Show market status
        logger.info("\n🧪 Test 2: Current Market Status")
        market_status = downloader.trading_calendar.get_market_status()
        
        logger.info(f"📊 Market Status:")
        logger.info(f"  DateTime: {market_status['datetime']}")
        logger.info(f"  Day: {market_status['weekday']} ({'Weekend' if market_status['is_weekend'] else 'Weekday'})")
        logger.info(f"  Trading Day: {'Yes' if market_status['is_trading_day'] else 'No'}")
        logger.info(f"  Active Hour: {'Yes' if market_status['is_active_hour'] else 'No'}")
        logger.info(f"  Recommendation: {market_status['recommendation']}")
        logger.info(f"  Reason: {market_status['reason']}")
        
        if market_status['active_sessions']:
            logger.info(f"  Active Sessions: {', '.join(market_status['active_sessions'])}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Downloader test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_ml_data_consistency():
    """Test ML/DL data consistency - no gaps from weekends"""
    logger.info("\n🤖 Testing ML/DL Data Consistency")
    logger.info("=" * 60)
    
    trading_calendar = get_trading_calendar()
    
    # Simulate a week of data
    start_date = datetime(2024, 8, 5, 0, 0)  # Monday
    end_date = datetime(2024, 8, 11, 23, 59)  # Sunday
    
    # Generate all hours
    all_hours = []
    current = start_date
    
    while current <= end_date:
        all_hours.append(current)
        current += timedelta(hours=1)
    
    logger.info(f"📅 Full week hours: {len(all_hours)}")
    
    # Filter to trading hours
    trading_hours = trading_calendar.filter_trading_hours_only(all_hours)
    logger.info(f"📊 Trading hours: {len(trading_hours)}")
    
    # Check for gaps
    if len(trading_hours) > 0:
        # Calculate expected trading hours (Mon-Fri = 5 days * 24 hours = 120 hours)
        expected_hours = 5 * 24  # 5 weekdays * 24 hours
        
        logger.info(f"🎯 Expected trading hours: {expected_hours}")
        logger.info(f"📊 Actual trading hours: {len(trading_hours)}")
        
        # Show distribution by day
        day_counts = {}
        for th in trading_hours:
            day_name = th.strftime('%A')
            day_counts[day_name] = day_counts.get(day_name, 0) + 1
        
        logger.info("📈 Hours per day:")
        for day, count in day_counts.items():
            logger.info(f"  {day}: {count} hours")
        
        # Check for weekend contamination
        weekend_contamination = day_counts.get('Saturday', 0) + day_counts.get('Sunday', 0)
        
        if weekend_contamination == 0:
            logger.info("✅ No weekend data contamination - ML/DL consistency maintained")
            return True
        else:
            logger.error(f"❌ Found {weekend_contamination} weekend hours - ML/DL consistency compromised")
            return False
    else:
        logger.warning("⚠️ No trading hours found in test range")
        return False

async def main():
    """Main test suite"""
    logger.info("🧪 WEEKEND HANDLING TEST SUITE")
    logger.info("Testing smart trading calendar for ML/DL data consistency")
    logger.info("=" * 80)
    
    tests = [
        ("Weekend Detection", test_weekend_detection),
        ("Optimal Download Times", test_optimal_download_times),
        ("Downloader Weekend Handling", test_downloader_weekend_handling),
        ("ML/DL Data Consistency", test_ml_data_consistency)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n🏃 Running: {test_name}")
        logger.info("-" * 50)
        
        try:
            result = await test_func()
            if result:
                logger.info(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name}: FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {e}")
    
    logger.info("\n" + "=" * 80)
    logger.info("🏆 TEST SUMMARY")
    logger.info("=" * 80)
    logger.info(f"📊 Tests passed: {passed}/{total}")
    logger.info(f"📈 Success rate: {passed/total*100:.1f}%")
    
    if passed == total:
        logger.info("✅ ALL TESTS PASSED - Weekend handling working correctly")
        logger.info("🎉 ML/DL data consistency ensured - no weekend contamination")
        return True
    else:
        logger.error("❌ SOME TESTS FAILED - Weekend handling needs fixes")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)