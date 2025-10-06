#!/usr/bin/env python3
"""
Run Historical Backfill
1-year economic calendar data collection
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from scrapers.mql5_historical_scraper import MQL5HistoricalScraper


async def run_backfill(
    months_back: int = 12,
    use_zai: bool = False,
    db_connection: str = None
):
    """
    Run historical backfill

    Args:
        months_back: Months to backfill (default: 12)
        use_zai: Use Z.ai parser (requires ZAI_API_KEY env var)
        db_connection: PostgreSQL connection string (optional)
    """
    print("=" * 80)
    print("🚀 MQL5 HISTORICAL BACKFILL")
    print("=" * 80)
    print()
    print(f"Configuration:")
    print(f"  Months back: {months_back}")
    print(f"  Z.ai parser: {'Enabled' if use_zai else 'Disabled (regex fallback)'}")
    print(f"  Database: {'PostgreSQL' if db_connection else 'JSON file (fallback)'}")
    print()

    # Get Z.ai API key if needed
    zai_key = os.getenv('ZAI_API_KEY', 'test')

    if use_zai and zai_key == 'test':
        print("⚠️  WARNING: ZAI_API_KEY not set!")
        print("   Set environment variable to use Z.ai parser:")
        print("   export ZAI_API_KEY='your-key'")
        print()
        print("   Falling back to regex parser...")
        use_zai = False

    # Initialize scraper
    scraper = MQL5HistoricalScraper(
        zai_api_key=zai_key,
        db_connection_string=db_connection,
        use_zai=use_zai
    )

    # Run backfill
    start_time = datetime.now()

    await scraper.backfill_historical_data(months_back=months_back)

    duration = (datetime.now() - start_time).total_seconds()

    print()
    print("=" * 80)
    print("✅ BACKFILL COMPLETED")
    print("=" * 80)
    print()
    print(f"Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    print()


async def run_daily_update(days_back: int = 7):
    """
    Update recent actual values

    Args:
        days_back: Days to check for updates (default: 7)
    """
    print("=" * 80)
    print("🔄 DAILY UPDATE - Actual Values")
    print("=" * 80)
    print()

    zai_key = os.getenv('ZAI_API_KEY', 'test')

    scraper = MQL5HistoricalScraper(
        zai_api_key=zai_key,
        use_zai=False  # Regex is fine for updates
    )

    await scraper.update_recent_actuals(days_back=days_back)

    print("✅ Daily update completed")
    print()


async def run_coverage_report():
    """Print coverage statistics"""
    from utils.date_tracker import print_coverage_report

    await print_coverage_report()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='MQL5 Historical Data Backfill')
    parser.add_argument(
        'command',
        choices=['backfill', 'update', 'report'],
        help='Command to run'
    )
    parser.add_argument(
        '--months',
        type=int,
        default=12,
        help='Months to backfill (default: 12)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Days back for update (default: 7)'
    )
    parser.add_argument(
        '--zai',
        action='store_true',
        help='Use Z.ai parser (requires ZAI_API_KEY)'
    )
    parser.add_argument(
        '--db',
        type=str,
        default=None,
        help='PostgreSQL connection string'
    )

    args = parser.parse_args()

    if args.command == 'backfill':
        asyncio.run(run_backfill(
            months_back=args.months,
            use_zai=args.zai,
            db_connection=args.db
        ))
    elif args.command == 'update':
        asyncio.run(run_daily_update(days_back=args.days))
    elif args.command == 'report':
        asyncio.run(run_coverage_report())


if __name__ == '__main__':
    main()
