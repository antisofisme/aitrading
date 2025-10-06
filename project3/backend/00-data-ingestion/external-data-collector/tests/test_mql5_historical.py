#!/usr/bin/env python3
"""
Test MQL5 Historical Scraper
Test with 1-week date range before full 1-year backfill
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from scrapers.mql5_historical_scraper import MQL5HistoricalScraper


async def test_single_date():
    """Test scraping a single date"""
    print("=" * 80)
    print("🧪 TEST 1: Single Date Scraping")
    print("=" * 80)
    print()

    # Use regex parser (no Z.ai key needed for testing)
    scraper = MQL5HistoricalScraper(
        zai_api_key="test",
        use_zai=False  # Use regex fallback
    )

    # Test with a recent date
    target_date = datetime.now().date() - timedelta(days=1)

    events = await scraper.scrape_date(target_date)

    print()
    print(f"📊 Results:")
    print(f"   Total events: {len(events)}")

    if events:
        # Show first 5 events
        print(f"\n   First 5 events:")
        for i, event in enumerate(events[:5], 1):
            print(f"   {i}. [{event['time']}] {event['currency']} - {event['event']}")
            if event['forecast'] or event['previous'] or event['actual']:
                parts = []
                if event['forecast']:
                    parts.append(f"F:{event['forecast']}")
                if event['previous']:
                    parts.append(f"P:{event['previous']}")
                if event['actual']:
                    parts.append(f"A:{event['actual']}")
                print(f"      {' | '.join(parts)}")

    print()
    return len(events) > 0


async def test_date_range():
    """Test scraping 1-week date range"""
    print("=" * 80)
    print("🧪 TEST 2: 1-Week Date Range")
    print("=" * 80)
    print()

    scraper = MQL5HistoricalScraper(
        zai_api_key="test",
        use_zai=False
    )

    # Last 7 days
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)

    print(f"Scraping from {start_date} to {end_date}")
    print()

    results = await scraper.scrape_date_range(start_date, end_date)

    print()
    print("=" * 80)
    print("📊 RESULTS SUMMARY")
    print("=" * 80)
    print()

    total_events = 0
    for date_str, events in sorted(results.items()):
        total_events += len(events)
        print(f"{date_str}: {len(events)} events")

    print()
    print(f"Total days: {len(results)}")
    print(f"Total events: {total_events}")
    print(f"Average events/day: {total_events/len(results) if results else 0:.1f}")

    # Data quality
    all_events = [e for events in results.values() for e in events]
    with_forecast = sum(1 for e in all_events if e.get('forecast'))
    with_previous = sum(1 for e in all_events if e.get('previous'))
    with_actual = sum(1 for e in all_events if e.get('actual'))

    print()
    print("Data Quality:")
    print(f"  With Forecast: {with_forecast}/{total_events} ({with_forecast/total_events*100 if total_events else 0:.1f}%)")
    print(f"  With Previous: {with_previous}/{total_events} ({with_previous/total_events*100 if total_events else 0:.1f}%)")
    print(f"  With Actual: {with_actual}/{total_events} ({with_actual/total_events*100 if total_events else 0:.1f}%)")

    print()
    return len(results) > 0


async def test_with_tracker():
    """Test scraping with DateTracker"""
    print("=" * 80)
    print("🧪 TEST 3: Scraping with DateTracker")
    print("=" * 80)
    print()

    scraper = MQL5HistoricalScraper(
        zai_api_key="test",
        use_zai=False,
        db_connection_string=None  # Use JSON file fallback
    )

    # Scrape 3 days
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=3)

    print(f"Scraping {start_date} to {end_date}")
    print()

    results = await scraper.scrape_date_range(start_date, end_date)

    # Check tracker stats
    stats = await scraper.tracker.get_coverage_stats()

    print()
    print("=" * 80)
    print("📊 TRACKER STATS")
    print("=" * 80)
    print()
    print(f"Total dates tracked: {stats.get('total_dates', 0)}")
    print(f"Total events: {stats.get('total_events', 0)}")
    print(f"Dates with forecast: {stats.get('dates_with_forecast', 0)}")
    print(f"Dates with actual: {stats.get('dates_with_actual', 0)}")

    if stats.get('earliest_date'):
        print(f"Earliest date: {stats['earliest_date']}")
        print(f"Latest date: {stats['latest_date']}")

    print()

    # Check missing dates
    missing = await scraper.tracker.get_missing_dates(start_date, end_date)
    print(f"Missing dates: {len(missing)}")
    if missing:
        print(f"  {[d.strftime('%Y-%m-%d') for d in missing]}")

    print()
    return True


async def test_zai_parser():
    """Test with Z.ai parser (requires API key)"""
    print("=" * 80)
    print("🧪 TEST 4: Z.ai Parser (Optional)")
    print("=" * 80)
    print()

    # Check if Z.ai API key available
    import os
    zai_key = os.getenv('ZAI_API_KEY')

    if not zai_key:
        print("⚠️  ZAI_API_KEY not set - skipping Z.ai test")
        print("   Set environment variable to test Z.ai parser:")
        print("   export ZAI_API_KEY='your-key'")
        print()
        return False

    scraper = MQL5HistoricalScraper(
        zai_api_key=zai_key,
        use_zai=True  # Use Z.ai parser
    )

    target_date = datetime.now().date() - timedelta(days=1)

    print(f"Testing Z.ai parser with date: {target_date}")
    print()

    events = await scraper.scrape_date(target_date)

    print()
    print(f"📊 Z.ai Results:")
    print(f"   Events found: {len(events)}")

    if events:
        # Show first 3 events
        for i, event in enumerate(events[:3], 1):
            print(f"\n   {i}. {event['currency']} - {event['event']}")
            print(f"      Date: {event['date']}, Time: {event['time']}")
            if event.get('impact'):
                print(f"      Impact: {event['impact']}")
            if event['forecast']:
                print(f"      Forecast: {event['forecast']}")
            if event['previous']:
                print(f"      Previous: {event['previous']}")
            if event['actual']:
                print(f"      Actual: {event['actual']}")

    print()
    return len(events) > 0


async def main():
    """Run all tests"""
    print("=" * 80)
    print("🧪 MQL5 HISTORICAL SCRAPER TESTS")
    print("=" * 80)
    print()

    tests = [
        ("Single Date", test_single_date),
        ("Date Range (1 week)", test_date_range),
        ("With Tracker", test_with_tracker),
        ("Z.ai Parser", test_zai_parser),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

        await asyncio.sleep(1)

    # Summary
    print("=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    print()

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")

    passed = sum(1 for _, s in results if s)
    total = len(results)

    print()
    print(f"Passed: {passed}/{total}")
    print("=" * 80)


if __name__ == '__main__':
    asyncio.run(main())
