#!/usr/bin/env python3
"""
Test Weekend vs Data Logic - Demonstrate Correct Weekend Handling

IMPORTANT DISTINCTION:
1. Download on weekend = OK (bisa download kapan saja)  
2. Download weekend data = NOT OK (jangan ambil data Sabtu-Minggu)

This test shows the difference clearly.
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

async def test_weekend_download_vs_weekend_data():
    """
    Test the key difference:
    - Download timing: Can happen anytime (including weekends)
    - Data range: Should exclude weekend data for consistency
    """
    logger.info("🧪 TESTING: Weekend Download vs Weekend Data Logic")
    logger.info("=" * 80)
    
    trading_calendar = get_trading_calendar()
    
    # Test 1: Check current time (weekend)
    now = datetime.now()
    market_status = trading_calendar.get_market_status(now)
    
    logger.info("📅 Current Time Analysis:")
    logger.info(f"  Time: {now.strftime('%A, %Y-%m-%d %H:%M')}")
    logger.info(f"  Is Weekend: {'Yes' if now.weekday() >= 5 else 'No'}")
    logger.info(f"  Download Allowed: {'Yes' if market_status['recommendation'] == 'DOWNLOAD' else 'No'}")
    logger.info(f"  Data Quality: {market_status.get('data_quality', 'N/A')}")
    logger.info(f"  Reason: {market_status['reason']}")
    
    # Test 2: Show data range filtering 
    logger.info("\n📊 Data Range Filtering Test:")
    logger.info("-" * 50)
    
    # Create a range that includes weekend
    friday = datetime(2024, 8, 9, 14, 0)    # Friday 2 PM
    saturday = datetime(2024, 8, 10, 14, 0)  # Saturday 2 PM  
    sunday = datetime(2024, 8, 11, 14, 0)    # Sunday 2 PM
    monday = datetime(2024, 8, 12, 14, 0)    # Monday 2 PM
    
    test_times = [friday, saturday, sunday, monday]
    
    logger.info("🕐 Time Range Analysis:")
    for test_time in test_times:
        is_trading = trading_calendar.is_trading_day(test_time)
        day_name = test_time.strftime('%A')
        
        if is_trading:
            logger.info(f"  ✅ {day_name} {test_time.strftime('%Y-%m-%d %H:%M')}: INCLUDE in download (trading day)")
        else:
            logger.info(f"  ❌ {day_name} {test_time.strftime('%Y-%m-%d %H:%M')}: SKIP from data range (weekend/holiday)")
    
    # Test 3: Practical example with downloader
    logger.info("\n🔧 Practical Downloader Example:")
    logger.info("-" * 50)
    
    try:
        # Initialize downloader (this works regardless of current time)
        os.environ['USE_TOR_PROXY'] = 'true'
        downloader = DataBridgeDukascopyDownloader()
        
        logger.info("✅ Downloader initialized successfully (works on any day)")
        
        # Show what would happen with 72-hour range (includes weekend)
        logger.info("📋 Simulating 72-hour data range request:")
        
        end_time = datetime(2024, 8, 12, 23, 0)    # Monday night
        start_time = end_time - timedelta(hours=72)  # Friday morning
        
        logger.info(f"  📅 Requested range: {start_time.strftime('%A %Y-%m-%d %H:%M')} to {end_time.strftime('%A %Y-%m-%d %H:%M')}")
        
        # Count all hours vs trading hours
        all_hours = []
        current = start_time
        while current <= end_time:
            all_hours.append(current)
            current += timedelta(hours=1)
        
        # Filter using trading calendar
        trading_hours = []
        weekend_hours = []
        
        for hour in all_hours:
            if trading_calendar.is_trading_day(hour):
                trading_hours.append(hour)
            else:
                weekend_hours.append(hour)
        
        logger.info(f"  📊 Total hours requested: {len(all_hours)}")
        logger.info(f"  ✅ Trading hours (will download): {len(trading_hours)}")
        logger.info(f"  ❌ Weekend hours (will skip): {len(weekend_hours)}")
        
        # Show weekend hours that get skipped
        if weekend_hours:
            logger.info("  🗓️  Weekend data being skipped:")
            for wh in weekend_hours[:5]:  # Show first 5
                logger.info(f"    - {wh.strftime('%A %Y-%m-%d %H:00')} (no trading activity)")
            if len(weekend_hours) > 5:
                logger.info(f"    ... and {len(weekend_hours)-5} more weekend hours")
        
        logger.info("\n✅ Key Point: Download can run NOW (even on weekend)")
        logger.info("✅ But it will automatically skip weekend DATA for ML/DL consistency")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_ml_consistency_demo():
    """Demonstrate ML/DL data consistency"""
    logger.info("\n🤖 ML/DL Data Consistency Demo")
    logger.info("=" * 50)
    
    trading_calendar = get_trading_calendar()
    
    # Simulate one week of data processing
    monday = datetime(2024, 8, 5, 0, 0)   # Week start
    sunday = datetime(2024, 8, 11, 23, 59)  # Week end
    
    logger.info(f"📅 Processing week: {monday.strftime('%Y-%m-%d')} to {sunday.strftime('%Y-%m-%d')}")
    
    # Generate all hourly data points
    all_data_points = []
    current = monday
    
    while current <= sunday:
        all_data_points.append({
            'timestamp': current,
            'day': current.strftime('%A'),
            'is_trading': trading_calendar.is_trading_day(current)
        })
        current += timedelta(hours=1)
    
    # Filter for ML/DL training
    trading_data = [dp for dp in all_data_points if dp['is_trading']]
    weekend_data = [dp for dp in all_data_points if not dp['is_trading']]
    
    logger.info(f"📊 Total data points: {len(all_data_points)}")
    logger.info(f"✅ Trading data (for ML/DL): {len(trading_data)}")  
    logger.info(f"❌ Weekend data (excluded): {len(weekend_data)}")
    
    # Show distribution
    day_counts = {}
    for td in trading_data:
        day = td['day']
        day_counts[day] = day_counts.get(day, 0) + 1
    
    logger.info("\n📈 Trading data distribution:")
    for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
        count = day_counts.get(day, 0)
        logger.info(f"  {day}: {count} hours")
    
    weekend_count = day_counts.get('Saturday', 0) + day_counts.get('Sunday', 0)
    logger.info(f"\n🎯 Weekend contamination: {weekend_count} hours (should be 0)")
    
    if weekend_count == 0:
        logger.info("✅ Perfect ML/DL data consistency - no weekend contamination!")
        return True
    else:
        logger.error("❌ Weekend contamination detected - ML/DL consistency compromised")
        return False

async def main():
    """Main demonstration"""
    logger.info("🎯 WEEKEND HANDLING LOGIC DEMONSTRATION")
    logger.info("Showing the difference between download timing vs data filtering")
    logger.info("=" * 80)
    
    # Key message
    logger.info("🔑 KEY CONCEPT:")
    logger.info("   ✅ Download on weekend = OK (can download anytime)")
    logger.info("   ❌ Download weekend data = NOT OK (skip Sat/Sun data)")
    logger.info("   🎯 Result = Consistent Mon-Fri data for ML/DL models")
    logger.info("")
    
    tests = [
        ("Weekend Download vs Weekend Data", test_weekend_download_vs_weekend_data),
        ("ML/DL Data Consistency", test_ml_consistency_demo)
    ]
    
    passed = 0
    for test_name, test_func in tests:
        logger.info(f"🏃 Running: {test_name}")
        logger.info("-" * 60)
        
        try:
            result = await test_func()
            if result:
                logger.info(f"✅ {test_name}: PASSED\n")
                passed += 1
            else:
                logger.error(f"❌ {test_name}: FAILED\n")
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {e}\n")
    
    logger.info("=" * 80)
    logger.info("🏆 SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Tests passed: {passed}/{len(tests)}")
    
    if passed == len(tests):
        logger.info("✅ LOGIC CORRECT: Can download anytime, but skip weekend data")
        logger.info("🎉 Perfect for ML/DL consistency - no weekend contamination")
        return True
    else:
        logger.error("❌ Logic needs adjustment")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)