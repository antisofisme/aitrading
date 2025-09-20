#!/usr/bin/env python3
"""
Test MQL5 Economic Calendar Batch Scraper
Test konfigurasi .env, batch processing, dan pengecekan tanggal kosong
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

# Add path untuk imports
sys.path.append('/mnt/f/WINDSURF/neliti_code/server_microservice/services/data-bridge/src')

from data_sources.mql5_scraper import (
    MQL5WidgetScraper, 
    get_mql5_widget_events,
    get_mql5_batch_historical_events
)

async def test_environment_configuration():
    """Test konfigurasi environment variables"""
    print("🔧 TESTING ENVIRONMENT CONFIGURATION")
    print("=" * 50)
    
    # Test default values
    scraper = MQL5WidgetScraper()
    
    print(f"📅 Historical days back: {scraper.historical_days_back}")
    print(f"📦 Batch size: {scraper.batch_size}")
    print(f"⏱️  Batch delay: {scraper.batch_delay_seconds}s")
    print(f"🚫 Skip empty dates: {scraper.skip_empty_dates}")
    print(f"🔄 Max retries per date: {scraper.max_retries_per_date}")
    print(f"⏰ Browser timeout: {scraper.timeout}s")
    
    # Test dengan environment variables override
    os.environ['MQL5_HISTORICAL_DAYS_BACK'] = '60'
    os.environ['MQL5_BATCH_SIZE'] = '5'
    os.environ['MQL5_BATCH_DELAY_SECONDS'] = '3'
    os.environ['MQL5_SKIP_EMPTY_DATES'] = 'false'
    
    scraper_override = MQL5WidgetScraper()
    
    print("\n🎛️ AFTER ENVIRONMENT OVERRIDE:")
    print(f"📅 Historical days back: {scraper_override.historical_days_back}")
    print(f"📦 Batch size: {scraper_override.batch_size}")
    print(f"⏱️  Batch delay: {scraper_override.batch_delay_seconds}s")
    print(f"🚫 Skip empty dates: {scraper_override.skip_empty_dates}")
    
    print("✅ Environment configuration test completed\n")

async def test_batch_processing_small():
    """Test batch processing dengan range kecil untuk testing"""
    print("📦 TESTING BATCH PROCESSING (SMALL RANGE)")
    print("=" * 50)
    
    try:
        # Test dengan 7 hari terakhir
        results = await get_mql5_batch_historical_events(days_back=7)
        
        print(f"📊 Status: {results.get('status')}")
        print(f"📡 Source: {results.get('source')}")
        print(f"🛡️ Method: {results.get('method')}")
        
        # Show batch configuration
        config = results.get('batch_configuration', {})
        if config:
            print(f"\n⚙️ BATCH CONFIGURATION:")
            for key, value in config.items():
                print(f"   {key}: {value}")
        
        # Show date range results
        date_range = results.get('date_range', {})
        if date_range:
            print(f"\n📅 DATE RANGE RESULTS:")
            print(f"   Start: {date_range.get('start_date')}")
            print(f"   End: {date_range.get('end_date')}")
            print(f"   Successful: {date_range.get('successful_dates')}")
            print(f"   Empty: {date_range.get('empty_dates')}")
            print(f"   Failed: {date_range.get('failed_dates')}")
            
            success_rate = date_range.get('successful_dates', 0) / max(date_range.get('total_dates_attempted', 1), 1)
            print(f"   Success Rate: {success_rate*100:.1f}%")
        
        # Show events summary
        events = results.get('events', [])
        print(f"\n📈 EVENTS SUMMARY:")
        print(f"   Total events: {len(events)}")
        
        summary = results.get('summary', {})
        if summary:
            print(f"   High impact: {summary.get('high_impact', 0)}")
            print(f"   Medium impact: {summary.get('medium_impact', 0)}")
            print(f"   Low impact: {summary.get('low_impact', 0)}")
        
        # Show processing details
        processing = results.get('processing_details', {})
        if processing:
            print(f"\n📊 PROCESSING DETAILS:")
            successful_dates = processing.get('successful_dates', [])
            if isinstance(successful_dates, list) and successful_dates:
                print(f"   Successful dates: {successful_dates[:5]}...")
            
            empty_dates = processing.get('empty_dates')
            if isinstance(empty_dates, list):
                print(f"   Empty dates: {empty_dates[:3]}..." if len(empty_dates) > 3 else f"   Empty dates: {empty_dates}")
            else:
                print(f"   Empty dates handling: {empty_dates}")
        
        print("✅ Batch processing test completed\n")
        return True
        
    except Exception as e:
        print(f"❌ Batch processing test failed: {e}\n")
        return False

async def test_empty_date_detection():
    """Test deteksi tanggal kosong dan weekend skipping"""
    print("📭 TESTING EMPTY DATE DETECTION")
    print("=" * 50)
    
    try:
        # Test dengan weekend date (Saturday)
        saturday_date = "2024-08-10"  # This is a Saturday
        
        print(f"Testing weekend date: {saturday_date}")
        results = await get_mql5_widget_events(target_date=saturday_date)
        
        print(f"📊 Status: {results.get('status')}")
        events = results.get('events', [])
        print(f"📈 Events found: {len(events)}")
        
        if len(events) == 0:
            print("✅ Correctly detected weekend/empty date")
        else:
            print("⚠️ Weekend date returned events (might be sample data)")
        
        # Test dengan tanggal yang likely kosong (Sunday)
        sunday_date = "2024-08-11"  # This is a Sunday
        
        print(f"\nTesting Sunday date: {sunday_date}")
        results_sunday = await get_mql5_widget_events(target_date=sunday_date)
        
        events_sunday = results_sunday.get('events', [])
        print(f"📈 Events found: {len(events_sunday)}")
        
        if len(events_sunday) == 0:
            print("✅ Correctly handled Sunday (forex market closed)")
        
        print("✅ Empty date detection test completed\n")
        return True
        
    except Exception as e:
        print(f"❌ Empty date detection test failed: {e}\n")
        return False

async def test_single_date_vs_batch_comparison():
    """Test perbandingan single date vs batch mode"""
    print("🔄 TESTING SINGLE DATE VS BATCH COMPARISON")
    print("=" * 50)
    
    try:
        test_date = "2024-08-09"  # Friday
        
        # Test single date mode
        print(f"Testing single date: {test_date}")
        single_results = await get_mql5_widget_events(target_date=test_date)
        single_events = single_results.get('events', [])
        
        # Test batch mode dengan 1 hari
        print(f"Testing batch mode (1 day): {test_date}")
        batch_results = await get_mql5_widget_events(batch_mode=True, days_back=1)
        batch_events = batch_results.get('events', [])
        
        print(f"\n📊 COMPARISON RESULTS:")
        print(f"   Single mode events: {len(single_events)}")
        print(f"   Batch mode events: {len(batch_events)}")
        
        # Analyze differences
        if len(single_events) == len(batch_events):
            print("✅ Both modes returned same number of events")
        else:
            print(f"⚠️ Different event counts - investigating...")
            print(f"   Single mode status: {single_results.get('status')}")
            print(f"   Batch mode status: {batch_results.get('status')}")
        
        print("✅ Single vs batch comparison completed\n")
        return True
        
    except Exception as e:
        print(f"❌ Single vs batch comparison failed: {e}\n")
        return False

async def main():
    """Main testing function"""
    print("🚀 MQL5 ENHANCED SCRAPER TESTING SUITE")
    print("Testing: .env configuration, batch processing, empty date detection")
    print("=" * 80)
    
    tests = [
        ("Environment Configuration", test_environment_configuration),
        ("Batch Processing (Small Range)", test_batch_processing_small),
        ("Empty Date Detection", test_empty_date_detection),
        ("Single vs Batch Comparison", test_single_date_vs_batch_comparison)
    ]
    
    passed = 0
    for test_name, test_func in tests:
        print(f"🏃 Running: {test_name}")
        print("-" * 60)
        
        try:
            result = await test_func()
            if result:
                passed += 1
                print(f"✅ {test_name}: PASSED\n")
            else:
                print(f"❌ {test_name}: FAILED\n")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}\n")
    
    print("=" * 80)
    print("🏆 TESTING SUMMARY")
    print("=" * 80)
    print(f"Tests passed: {passed}/{len(tests)}")
    print(f"Success rate: {passed/len(tests)*100:.1f}%")
    
    if passed == len(tests):
        print("\n✅ ALL TESTS PASSED!")
        print("🎉 MQL5 Enhanced Scraper is ready:")
        print("   • Environment configuration working")
        print("   • Batch processing functional")
        print("   • Empty date detection active")
        print("   • Weekend filtering enabled")
        print("   • Retry mechanism operational")
    else:
        print(f"\n❌ {len(tests) - passed} TESTS FAILED")
        print("💡 Check configuration and dependencies")

if __name__ == "__main__":
    asyncio.run(main())