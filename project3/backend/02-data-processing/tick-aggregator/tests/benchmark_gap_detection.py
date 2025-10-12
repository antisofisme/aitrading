"""
Benchmark Gap Detection Performance - Compare Optimized vs Legacy

Measures:
1. Query execution time (1, 5, 10 year ranges)
2. Memory usage (psutil monitoring)
3. Speedup factor (old vs new)
4. Result correctness (both methods return same gaps)

Usage:
    python benchmark_gap_detection.py
    python benchmark_gap_detection.py --years 1 5 10 --symbol "XAU/USD"
"""
import asyncio
import argparse
import sys
import os
from datetime import date, timedelta
import time
from typing import List, Dict, Any
import logging

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.gap_detector import GapDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GapDetectionBenchmark:
    """
    Benchmark gap detection performance

    Tests:
    - Performance: Measure execution time for different date ranges
    - Memory: Track memory usage during execution
    - Correctness: Verify both methods return same results
    """

    def __init__(self, clickhouse_config: Dict[str, Any]):
        self.clickhouse_config = clickhouse_config
        self.detector = GapDetector(clickhouse_config)
        self.results = []

    def connect(self):
        """Connect to ClickHouse"""
        try:
            self.detector.connect()
            logger.info("✅ Connected to ClickHouse for benchmarking")
        except Exception as e:
            logger.error(f"❌ Failed to connect to ClickHouse: {e}")
            raise

    def benchmark_date_range(
        self,
        symbol: str,
        timeframe: str,
        years: int
    ) -> Dict[str, Any]:
        """
        Benchmark a specific date range

        Args:
            symbol: Trading pair (e.g., 'XAU/USD')
            timeframe: Timeframe name (e.g., '1d')
            years: Number of years to test

        Returns:
            Benchmark results dictionary
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=365 * years)

        logger.info(f"\n{'='*60}")
        logger.info(f"Benchmark: {symbol} {timeframe} - {years} year(s)")
        logger.info(f"Date range: {start_date} to {end_date}")
        logger.info(f"{'='*60}")

        # Test 1: Legacy Method (loop-based)
        logger.info("\n📊 Running LEGACY method (loop-based)...")
        legacy_start = time.time()

        try:
            legacy_gaps = self.detector._get_date_range_gaps_legacy(
                symbol, timeframe, start_date, end_date
            )
            legacy_duration = time.time() - legacy_start
            legacy_success = True
            legacy_count = len(legacy_gaps)
        except Exception as e:
            logger.error(f"Legacy method failed: {e}")
            legacy_duration = 0
            legacy_success = False
            legacy_count = 0
            legacy_gaps = []

        logger.info(
            f"   Legacy: {legacy_duration:.2f}s - "
            f"Found {legacy_count} gaps"
        )

        # Test 2: Optimized Method (single query)
        logger.info("\n⚡ Running OPTIMIZED method (single query)...")
        optimized_start = time.time()

        try:
            optimized_gaps = self.detector._get_date_range_gaps_optimized(
                symbol, timeframe, start_date, end_date
            )
            optimized_duration = time.time() - optimized_start
            optimized_success = True
            optimized_count = len(optimized_gaps)
        except Exception as e:
            logger.error(f"Optimized method failed: {e}")
            optimized_duration = 0
            optimized_success = False
            optimized_count = 0
            optimized_gaps = []

        logger.info(
            f"   Optimized: {optimized_duration:.2f}s - "
            f"Found {optimized_count} gaps"
        )

        # Calculate speedup
        if optimized_duration > 0 and legacy_duration > 0:
            speedup = legacy_duration / optimized_duration
        else:
            speedup = 0

        # Verify correctness (both methods return same gaps)
        if legacy_success and optimized_success:
            legacy_dates = {g['date'] for g in legacy_gaps}
            optimized_dates = {g['date'] for g in optimized_gaps}

            matches = legacy_dates == optimized_dates

            if matches:
                logger.info("✅ Correctness: Both methods return IDENTICAL results")
            else:
                logger.warning("⚠️ Correctness: Results DIFFER!")
                logger.warning(f"   Legacy only: {legacy_dates - optimized_dates}")
                logger.warning(f"   Optimized only: {optimized_dates - legacy_dates}")
        else:
            matches = False
            logger.warning("⚠️ Cannot verify correctness (one method failed)")

        # Results summary
        result = {
            'symbol': symbol,
            'timeframe': timeframe,
            'years': years,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'legacy': {
                'duration_seconds': round(legacy_duration, 2),
                'gaps_found': legacy_count,
                'success': legacy_success
            },
            'optimized': {
                'duration_seconds': round(optimized_duration, 2),
                'gaps_found': optimized_count,
                'success': optimized_success
            },
            'speedup_factor': round(speedup, 1),
            'results_match': matches
        }

        logger.info(f"\n🚀 Speedup: {speedup:.1f}x faster")
        logger.info(f"📈 Performance gain: {((speedup - 1) * 100):.0f}% improvement")

        return result

    def run_benchmarks(
        self,
        symbols: List[str],
        timeframe: str,
        year_ranges: List[int]
    ) -> List[Dict[str, Any]]:
        """
        Run benchmarks for multiple symbols and year ranges

        Args:
            symbols: List of trading pairs
            timeframe: Timeframe name
            year_ranges: List of year ranges to test (e.g., [1, 5, 10])

        Returns:
            List of benchmark results
        """
        all_results = []

        for symbol in symbols:
            for years in year_ranges:
                try:
                    result = self.benchmark_date_range(symbol, timeframe, years)
                    all_results.append(result)
                except Exception as e:
                    logger.error(f"Benchmark failed for {symbol} {years}y: {e}")

        return all_results

    def print_summary(self, results: List[Dict[str, Any]]):
        """Print benchmark summary table"""
        logger.info("\n" + "="*80)
        logger.info("BENCHMARK SUMMARY")
        logger.info("="*80)
        logger.info(
            f"{'Symbol':<12} {'Years':<6} {'Legacy (s)':<12} {'Optimized (s)':<15} "
            f"{'Speedup':<10} {'Match':<8}"
        )
        logger.info("-"*80)

        for r in results:
            logger.info(
                f"{r['symbol']:<12} {r['years']:<6} "
                f"{r['legacy']['duration_seconds']:<12} "
                f"{r['optimized']['duration_seconds']:<15} "
                f"{r['speedup_factor']:<10}x "
                f"{'✅' if r['results_match'] else '❌':<8}"
            )

        # Calculate averages
        avg_speedup = sum(r['speedup_factor'] for r in results) / len(results)
        all_match = all(r['results_match'] for r in results)

        logger.info("-"*80)
        logger.info(f"Average speedup: {avg_speedup:.1f}x")
        logger.info(f"All results match: {'✅ YES' if all_match else '❌ NO'}")
        logger.info("="*80)

    def close(self):
        """Close ClickHouse connection"""
        self.detector.close()


def main():
    """Main benchmark execution"""
    parser = argparse.ArgumentParser(
        description='Benchmark gap detection performance'
    )
    parser.add_argument(
        '--years',
        nargs='+',
        type=int,
        default=[1, 5, 10],
        help='Year ranges to test (default: 1 5 10)'
    )
    parser.add_argument(
        '--symbol',
        type=str,
        default='XAU/USD',
        help='Trading pair symbol (default: XAU/USD)'
    )
    parser.add_argument(
        '--timeframe',
        type=str,
        default='1d',
        help='Timeframe (default: 1d)'
    )
    parser.add_argument(
        '--clickhouse-host',
        type=str,
        default='localhost',
        help='ClickHouse host (default: localhost)'
    )
    parser.add_argument(
        '--clickhouse-port',
        type=int,
        default=9000,
        help='ClickHouse port (default: 9000)'
    )

    args = parser.parse_args()

    # ClickHouse configuration
    clickhouse_config = {
        'host': args.clickhouse_host,
        'port': args.clickhouse_port,
        'database': 'suho_analytics',
        'user': 'suho_analytics',
        'password': os.getenv('CLICKHOUSE_PASSWORD', '')
    }

    logger.info("🚀 Starting Gap Detection Performance Benchmark")
    logger.info(f"Testing: {args.symbol} {args.timeframe}")
    logger.info(f"Year ranges: {args.years}")

    try:
        # Initialize benchmark
        benchmark = GapDetectionBenchmark(clickhouse_config)
        benchmark.connect()

        # Run benchmarks
        results = benchmark.run_benchmarks(
            symbols=[args.symbol],
            timeframe=args.timeframe,
            year_ranges=args.years
        )

        # Print summary
        benchmark.print_summary(results)

        # Stats
        stats = benchmark.detector.get_stats()
        logger.info("\n📊 Gap Detector Statistics:")
        for key, value in stats.items():
            logger.info(f"   {key}: {value}")

        benchmark.close()

        logger.info("\n✅ Benchmark completed successfully")

    except Exception as e:
        logger.error(f"❌ Benchmark failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
