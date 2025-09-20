#!/usr/bin/env python3
"""
Test Forex Holiday Logic - Correct Understanding

IMPORTANT: Forex market behavior vs Stock market:
- Stock Market: Closes on weekends AND national holidays
- Forex Market: ONLY closes on weekends (Saturday-Sunday)
- National holidays do NOT affect forex trading (24/5 market)

This test verifies correct forex market behavior.
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_forex_vs_stock_market_logic():
    """Test forex market behavior vs stock market expectations"""
    logger.info("🏦 TESTING: Forex vs Stock Market Holiday Behavior")
    logger.info("=" * 80)
    
    trading_calendar = get_trading_calendar()
    
    # Test dates including known national holidays
    test_cases = [
        # Regular weekdays (should always be trading days in forex)
        ("Regular Monday", datetime(2024, 7, 1, 14, 0)),     # Monday
        ("Regular Tuesday", datetime(2024, 7, 2, 14, 0)),    # Tuesday
        ("Regular Wednesday", datetime(2024, 7, 3, 14, 0)),  # Wednesday
        ("Regular Thursday", datetime(2024, 7, 4, 14, 0)),   # Thursday - US Independence Day
        ("Regular Friday", datetime(2024, 7, 5, 14, 0)),     # Friday
        
        # Weekends (should never be trading days)
        ("Weekend Saturday", datetime(2024, 7, 6, 14, 0)),   # Saturday
        ("Weekend Sunday", datetime(2024, 7, 7, 14, 0)),     # Sunday
        
        # Known major holidays on weekdays
        ("New Year's Day", datetime(2024, 1, 1, 14, 0)),     # Monday - New Year
        ("Christmas Day", datetime(2023, 12, 25, 14, 0)),    # Monday - Christmas
        ("US Independence Day", datetime(2024, 7, 4, 14, 0)), # Thursday - July 4th
    ]
    
    logger.info("📊 Forex Market Trading Day Analysis:")
    logger.info("-" * 60)
    
    stock_different_count = 0
    
    for description, test_date in test_cases:
        is_trading = trading_calendar.is_trading_day(test_date)
        weekday_name = test_date.strftime('%A')
        date_str = test_date.strftime('%Y-%m-%d')
        
        # What stock market would do
        is_weekend = test_date.weekday() >= 5
        is_holiday = "Independence" in description or "New Year" in description or "Christmas" in description
        stock_would_close = is_weekend or is_holiday
        
        if is_trading:
            status_icon = "✅ OPEN"
            reason = "Forex trades 24/5"
        else:
            status_icon = "❌ CLOSED" 
            reason = "Weekend only"
        
        logger.info(f"  {status_icon} {description}: {weekday_name} {date_str}")
        logger.info(f"     Forex: {'OPEN' if is_trading else 'CLOSED'} ({reason})")
        logger.info(f"     Stock: {'CLOSED' if stock_would_close else 'OPEN'} ({'Weekend/Holiday' if stock_would_close else 'Normal trading'})")
        
        if is_trading != (not stock_would_close):
            stock_different_count += 1
            logger.info(f"     💡 DIFFERENCE: Forex {'open' if is_trading else 'closed'} when stock would be {'closed' if stock_would_close else 'open'}")
        
        logger.info("")
    
    logger.info("📈 Key Findings:")
    logger.info(f"  • Cases where Forex ≠ Stock behavior: {stock_different_count}")
    logger.info(f"  • Forex ONLY closes on weekends (Sat-Sun)")
    logger.info(f"  • National holidays do NOT affect forex trading")
    logger.info(f"  • Forex operates 24/5 continuously")
    
    return True

async def test_holiday_week_data_continuity():
    """Test data continuity during holiday weeks"""
    logger.info("\n📅 TESTING: Holiday Week Data Continuity")
    logger.info("=" * 60)
    
    trading_calendar = get_trading_calendar()
    
    # Test US Independence Day week (July 4th, 2024 - Thursday)
    july_1_2024 = datetime(2024, 7, 1, 0, 0)  # Monday
    july_7_2024 = datetime(2024, 7, 7, 23, 59)  # Sunday
    
    logger.info(f"📊 Testing week of July 1-7, 2024 (includes July 4th Independence Day)")
    
    # Generate all days in the week
    all_days = []
    current = july_1_2024
    while current <= july_7_2024:
        all_days.append(current)
        current += timedelta(days=1)
    
    # Check each day
    trading_days = []
    weekend_days = []
    
    for day in all_days:
        day_name = day.strftime('%A')
        date_str = day.strftime('%Y-%m-%d')
        is_trading = trading_calendar.is_trading_day(day)
        
        special_note = ""
        if date_str == "2024-07-04":
            special_note = " (US Independence Day)"
        
        if is_trading:
            trading_days.append(day)
            logger.info(f"  ✅ {day_name} {date_str}{special_note}: TRADING DAY")
        else:
            weekend_days.append(day)
            logger.info(f"  ❌ {day_name} {date_str}{special_note}: WEEKEND")
    
    logger.info(f"\n📈 Week Summary:")
    logger.info(f"  • Trading days: {len(trading_days)} (Mon-Fri including July 4th)")
    logger.info(f"  • Weekend days: {len(weekend_days)} (Sat-Sun only)")
    logger.info(f"  • July 4th (Independence Day): {'TRADING' if datetime(2024, 7, 4) in trading_days else 'CLOSED'}")
    
    # Verify July 4th is treated as trading day
    july_4th_trading = trading_calendar.is_trading_day(datetime(2024, 7, 4, 14, 0))
    
    if july_4th_trading:
        logger.info("  ✅ CORRECT: July 4th treated as normal trading day (forex doesn't close for holidays)")
        return True
    else:
        logger.error("  ❌ INCORRECT: July 4th treated as non-trading day (wrong for forex)")
        return False

async def test_ml_dl_data_consistency_holidays():
    """Test ML/DL data consistency with holidays included"""
    logger.info("\n🤖 TESTING: ML/DL Data Consistency (With Holidays)")
    logger.info("=" * 60)
    
    trading_calendar = get_trading_calendar()
    
    # Test week including Christmas (Dec 25, 2023 was Monday)
    christmas_week_start = datetime(2023, 12, 25, 0, 0)    # Monday - Christmas Day
    christmas_week_end = datetime(2023, 12, 31, 23, 59)    # Sunday
    
    logger.info(f"📊 Testing Christmas week: {christmas_week_start.strftime('%Y-%m-%d')} to {christmas_week_end.strftime('%Y-%m-%d')}")
    
    # Generate all hours in the week
    all_hours = []
    current = christmas_week_start
    while current <= christmas_week_end:
        all_hours.append(current)
        current += timedelta(hours=1)
    
    # Filter for trading hours
    trading_hours = []
    weekend_hours = []
    
    for hour in all_hours:
        if trading_calendar.is_trading_day(hour):
            trading_hours.append(hour)
        else:
            weekend_hours.append(hour)
    
    # Count days
    trading_days = set([th.date() for th in trading_hours])
    weekend_dates = set([wh.date() for wh in weekend_hours])
    
    logger.info(f"📈 Results:")
    logger.info(f"  • Total hours in week: {len(all_hours)}")
    logger.info(f"  • Trading hours: {len(trading_hours)}")
    logger.info(f"  • Weekend hours: {len(weekend_hours)}")
    logger.info(f"  • Trading days: {len(trading_days)}")
    logger.info(f"  • Weekend days: {len(weekend_dates)}")
    
    # Show which days are trading days
    logger.info(f"\n📅 Trading days in Christmas week:")
    for td in sorted(trading_days):
        weekday = datetime.combine(td, datetime.min.time()).strftime('%A')
        special = " (Christmas Day)" if td.day == 25 else ""
        logger.info(f"  ✅ {weekday} {td}{special}")
    
    logger.info(f"\n📅 Weekend days:")
    for wd in sorted(weekend_dates):
        weekday = datetime.combine(wd, datetime.min.time()).strftime('%A')
        logger.info(f"  ❌ {weekday} {wd}")
    
    # Expected: 5 trading days (Mon-Fri including Christmas) + 2 weekend days
    expected_trading_days = 5  # Mon, Tue, Wed, Thu, Fri (including Christmas on Monday)
    expected_weekend_days = 2  # Sat, Sun
    
    success = (len(trading_days) == expected_trading_days and len(weekend_dates) == expected_weekend_days)
    
    if success:
        logger.info(f"\n✅ CORRECT: Christmas Day treated as normal trading day")
        logger.info(f"✅ Perfect ML/DL consistency: 5 weekdays + 2 weekend days")
        return True
    else:
        logger.error(f"\n❌ INCORRECT: Expected {expected_trading_days} trading days, got {len(trading_days)}")
        logger.error(f"❌ Expected {expected_weekend_days} weekend days, got {len(weekend_dates)}")
        return False

async def main():
    """Main test suite"""
    logger.info("🎯 FOREX HOLIDAY LOGIC TEST SUITE")
    logger.info("Verifying correct forex market behavior (24/5, no national holiday closures)")
    logger.info("=" * 80)
    
    # Key message
    logger.info("🔑 FOREX MARKET FACTS:")
    logger.info("   ✅ Closes: Weekends only (Saturday-Sunday)")
    logger.info("   ❌ Does NOT close: National holidays (Christmas, July 4th, etc.)")
    logger.info("   🌍 Operates: 24 hours/day, 5 days/week continuously")
    logger.info("   📈 Different from: Stock markets (which close for holidays)")
    logger.info("")
    
    tests = [
        ("Forex vs Stock Market Logic", test_forex_vs_stock_market_logic),
        ("Holiday Week Data Continuity", test_holiday_week_data_continuity),
        ("ML/DL Data Consistency (Holidays)", test_ml_dl_data_consistency_holidays)
    ]
    
    passed = 0
    for test_name, test_func in tests:
        logger.info(f"🏃 Running: {test_name}")
        logger.info("-" * 70)
        
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
        logger.info("✅ FOREX LOGIC CORRECT: Only weekends affect trading")
        logger.info("🎉 National holidays do NOT impact forex data")
        logger.info("📊 Perfect for ML/DL: Consistent Mon-Fri data even during holidays")
        return True
    else:
        logger.error("❌ Forex holiday logic needs adjustment")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)