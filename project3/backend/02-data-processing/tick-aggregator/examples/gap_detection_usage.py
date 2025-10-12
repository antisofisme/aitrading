"""
Gap Detection Usage Examples

Demonstrates how to use the optimized gap detection for various scenarios
"""
import sys
import os
from datetime import date, timedelta
import logging

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.gap_detector import GapDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_1_recent_gaps():
    """Example 1: Detect recent gaps (last 24 hours)"""
    logger.info("\n" + "="*60)
    logger.info("EXAMPLE 1: Detect Recent Gaps (24 hours)")
    logger.info("="*60)

    config = {
        'host': 'localhost',
        'port': 9000,
        'database': 'suho_analytics',
        'user': 'suho_analytics',
        'password': os.getenv('CLICKHOUSE_PASSWORD', '')
    }

    detector = GapDetector(config)
    detector.connect()

    # Detect gaps in last 24 hours
    gaps = detector.detect_recent_gaps(
        symbol='XAU/USD',
        timeframe='1d',
        interval_minutes=1440,  # 1 day
        lookback_hours=24
    )

    logger.info(f"Found {len(gaps)} recent gaps")
    for gap in gaps:
        logger.info(f"  - {gap}")

    detector.close()


def example_2_date_range_gaps():
    """Example 2: Detect gaps in specific date range (optimized)"""
    logger.info("\n" + "="*60)
    logger.info("EXAMPLE 2: Detect Date Range Gaps (Optimized)")
    logger.info("="*60)

    config = {
        'host': 'localhost',
        'port': 9000,
        'database': 'suho_analytics',
        'user': 'suho_analytics',
        'password': os.getenv('CLICKHOUSE_PASSWORD', '')
    }

    detector = GapDetector(config)
    detector.connect()

    # Detect gaps in 1-year range
    start = date(2024, 1, 1)
    end = date(2024, 12, 31)

    gaps = detector.get_date_range_gaps(
        symbol='XAU/USD',
        timeframe='1d',
        start_date=start,
        end_date=end
    )

    logger.info(f"Date range: {start} to {end}")
    logger.info(f"Found {len(gaps)} gaps in 1 year")

    # Show first 5 gaps
    for gap in gaps[:5]:
        logger.info(
            f"  - {gap['date']}: {gap['type']} "
            f"({gap['symbol']} {gap['timeframe']})"
        )

    if len(gaps) > 5:
        logger.info(f"  ... and {len(gaps) - 5} more")

    # Get performance stats
    stats = detector.get_stats()
    logger.info(f"\nPerformance Stats:")
    logger.info(f"  Method: {stats['gap_detection_method']}")
    logger.info(f"  Optimized queries: {stats['optimized_queries']}")
    logger.info(f"  Avg duration: {stats['avg_duration']:.2f}s")

    detector.close()


def example_3_multi_year_range():
    """Example 3: Detect gaps in large date range (10 years)"""
    logger.info("\n" + "="*60)
    logger.info("EXAMPLE 3: Large Date Range (10 Years)")
    logger.info("="*60)

    config = {
        'host': 'localhost',
        'port': 9000,
        'database': 'suho_analytics',
        'user': 'suho_analytics',
        'password': os.getenv('CLICKHOUSE_PASSWORD', '')
    }

    detector = GapDetector(config)
    detector.connect()

    # Detect gaps in 10-year range
    end = date.today()
    start = end - timedelta(days=365 * 10)

    logger.info(f"Date range: {start} to {end} (10 years)")
    logger.info("Using chunking for optimal performance...")

    gaps = detector.get_date_range_gaps(
        symbol='XAU/USD',
        timeframe='1d',
        start_date=start,
        end_date=end,
        chunk_days=365  # 1-year chunks
    )

    logger.info(f"Found {len(gaps)} total gaps in 10 years")

    # Group gaps by year
    gaps_by_year = {}
    for gap in gaps:
        year = gap['date'].year
        if year not in gaps_by_year:
            gaps_by_year[year] = 0
        gaps_by_year[year] += 1

    logger.info("\nGaps by year:")
    for year in sorted(gaps_by_year.keys()):
        logger.info(f"  {year}: {gaps_by_year[year]} gaps")

    # Performance stats
    stats = detector.get_stats()
    logger.info(f"\nPerformance:")
    logger.info(f"  Total duration: {stats['total_duration']:.2f}s")
    logger.info(f"  Avg per query: {stats['avg_duration']:.2f}s")

    detector.close()


def example_4_multiple_symbols():
    """Example 4: Detect gaps for multiple symbols"""
    logger.info("\n" + "="*60)
    logger.info("EXAMPLE 4: Multiple Symbols Gap Detection")
    logger.info("="*60)

    config = {
        'host': 'localhost',
        'port': 9000,
        'database': 'suho_analytics',
        'user': 'suho_analytics',
        'password': os.getenv('CLICKHOUSE_PASSWORD', '')
    }

    detector = GapDetector(config)
    detector.connect()

    symbols = ['XAU/USD', 'EUR/USD', 'GBP/USD']
    start = date(2024, 1, 1)
    end = date(2024, 12, 31)

    all_gaps = {}

    for symbol in symbols:
        gaps = detector.get_date_range_gaps(
            symbol=symbol,
            timeframe='1d',
            start_date=start,
            end_date=end
        )
        all_gaps[symbol] = gaps
        logger.info(f"{symbol}: {len(gaps)} gaps")

    # Summary
    total_gaps = sum(len(gaps) for gaps in all_gaps.values())
    logger.info(f"\nTotal gaps across all symbols: {total_gaps}")

    detector.close()


def example_5_compare_methods():
    """Example 5: Compare optimized vs legacy methods"""
    logger.info("\n" + "="*60)
    logger.info("EXAMPLE 5: Compare Optimized vs Legacy")
    logger.info("="*60)

    config = {
        'host': 'localhost',
        'port': 9000,
        'database': 'suho_analytics',
        'user': 'suho_analytics',
        'password': os.getenv('CLICKHOUSE_PASSWORD', '')
    }

    detector = GapDetector(config)
    detector.connect()

    start = date(2024, 1, 1)
    end = date(2024, 3, 31)  # 3 months

    import time

    # Test optimized
    logger.info("Testing OPTIMIZED method...")
    opt_start = time.time()
    opt_gaps = detector._get_date_range_gaps_optimized(
        'XAU/USD', '1d', start, end
    )
    opt_duration = time.time() - opt_start

    # Test legacy
    logger.info("Testing LEGACY method...")
    leg_start = time.time()
    leg_gaps = detector._get_date_range_gaps_legacy(
        'XAU/USD', '1d', start, end
    )
    leg_duration = time.time() - leg_start

    # Compare
    speedup = leg_duration / opt_duration if opt_duration > 0 else 0

    logger.info(f"\nResults:")
    logger.info(f"  Optimized: {opt_duration:.2f}s - {len(opt_gaps)} gaps")
    logger.info(f"  Legacy: {leg_duration:.2f}s - {len(leg_gaps)} gaps")
    logger.info(f"  Speedup: {speedup:.1f}x faster")

    # Verify same results
    opt_dates = {g['date'] for g in opt_gaps}
    leg_dates = {g['date'] for g in leg_gaps}

    if opt_dates == leg_dates:
        logger.info("  ✅ Both methods return IDENTICAL results")
    else:
        logger.info("  ⚠️ Results differ!")

    detector.close()


def main():
    """Run all examples"""
    logger.info("🚀 Gap Detection Usage Examples\n")

    examples = [
        ("Recent Gaps (24h)", example_1_recent_gaps),
        ("Date Range (1 year)", example_2_date_range_gaps),
        ("Large Range (10 years)", example_3_multi_year_range),
        ("Multiple Symbols", example_4_multiple_symbols),
        ("Compare Methods", example_5_compare_methods),
    ]

    logger.info("Available examples:")
    for i, (name, _) in enumerate(examples, 1):
        logger.info(f"  {i}. {name}")

    logger.info("\nRunning Example 2 (most common use case)...")

    try:
        example_2_date_range_gaps()
        logger.info("\n✅ Example completed successfully")
    except Exception as e:
        logger.error(f"\n❌ Example failed: {e}", exc_info=True)


if __name__ == "__main__":
    main()
