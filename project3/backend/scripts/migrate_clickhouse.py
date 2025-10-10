#!/usr/bin/env python3
"""
ClickHouse Migration Script: MergeTree → ReplacingMergeTree

This script migrates the aggregates table to use ReplacingMergeTree engine
to enable automatic deduplication and solve the 178x duplication issue.

Usage:
    python migrate_clickhouse.py --step 1  # Create new table
    python migrate_clickhouse.py --step 2  # Copy data
    python migrate_clickhouse.py --step 3  # Verify data
    python migrate_clickhouse.py --step 4  # Rename tables
    python migrate_clickhouse.py --step 5  # Optimize
    python migrate_clickhouse.py --step 6  # Final verification
    python migrate_clickhouse.py --all     # Run all steps (interactive)
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from clickhouse_driver import Client
except ImportError:
    print("ERROR: clickhouse-driver not installed")
    print("Install with: pip install clickhouse-driver")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class ClickHouseMigration:
    """ClickHouse schema migration manager"""

    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        self.client = Client(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        logger.info(f"✅ Connected to ClickHouse: {host}:{port}/{database}")

    def step1_create_new_table(self):
        """Step 1: Create aggregates_new with ReplacingMergeTree"""
        logger.info("=" * 80)
        logger.info("STEP 1: Creating aggregates_new table with ReplacingMergeTree engine")
        logger.info("=" * 80)

        # Check if table already exists
        result = self.client.execute(
            "SELECT COUNT(*) FROM system.tables WHERE database = currentDatabase() AND name = 'aggregates_new'"
        )

        if result[0][0] > 0:
            logger.warning("⚠️  Table aggregates_new already exists!")
            response = input("Drop and recreate? (yes/no): ")
            if response.lower() == 'yes':
                self.client.execute("DROP TABLE aggregates_new")
                logger.info("✅ Dropped existing aggregates_new table")
            else:
                logger.info("⏭️  Skipping table creation")
                return

        # Create new table
        create_query = """
        CREATE TABLE aggregates_new
        (
            symbol String,
            timeframe String,
            timestamp DateTime,
            timestamp_ms Int64,
            open Float64,
            high Float64,
            low Float64,
            close Float64,
            volume UInt64,
            vwap Float64,
            range_pips Float64,
            body_pips Float64,
            start_time DateTime,
            end_time DateTime,
            source String,
            event_type String,
            indicators String,
            ingested_at DateTime DEFAULT now()
        )
        ENGINE = ReplacingMergeTree(ingested_at)
        PARTITION BY (symbol, toYYYYMM(timestamp))
        ORDER BY (symbol, timeframe, timestamp)
        SETTINGS index_granularity = 8192
        """

        self.client.execute(create_query)
        logger.info("✅ Created aggregates_new table with ReplacingMergeTree engine")

    def step2_copy_data(self):
        """Step 2: Copy unique data from aggregates to aggregates_new"""
        logger.info("=" * 80)
        logger.info("STEP 2: Copying data from aggregates to aggregates_new")
        logger.info("=" * 80)

        # Check source row count
        result = self.client.execute("SELECT COUNT(*) FROM aggregates")
        total_rows = result[0][0]
        logger.info(f"📊 Source table has {total_rows:,} rows")

        # Check unique combinations
        result = self.client.execute(
            "SELECT COUNT(DISTINCT (symbol, timeframe, timestamp)) FROM aggregates"
        )
        unique_count = result[0][0]
        logger.info(f"📊 Source table has {unique_count:,} unique combinations")
        logger.info(f"📊 Duplication rate: {total_rows / unique_count:.2f}x")

        # Estimate time
        logger.info(f"⏱️  Estimated copy time: {total_rows / 1_000_000:.1f} minutes (1M rows/min)")

        response = input(f"\nProceed with copying {total_rows:,} rows? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("⏭️  Skipping data copy")
            return

        logger.info("🔄 Starting data copy...")
        start_time = datetime.now()

        # Copy data (deduplicating using ROW_NUMBER)
        copy_query = """
        INSERT INTO aggregates_new
        SELECT
            symbol, timeframe, timestamp, timestamp_ms,
            open, high, low, close, volume, vwap,
            range_pips, body_pips, start_time, end_time,
            source, event_type, indicators, ingested_at
        FROM (
            SELECT *,
                   ROW_NUMBER() OVER (
                       PARTITION BY symbol, timeframe, timestamp
                       ORDER BY ingested_at DESC
                   ) as rn
            FROM aggregates
        ) t
        WHERE rn = 1
        """

        self.client.execute(copy_query)

        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Data copy completed in {duration:.1f} seconds")

        # Check result
        result = self.client.execute("SELECT COUNT(*) FROM aggregates_new")
        new_rows = result[0][0]
        logger.info(f"📊 New table has {new_rows:,} rows")
        logger.info(f"📊 Removed {total_rows - new_rows:,} duplicates ({(total_rows - new_rows) / total_rows * 100:.1f}%)")

    def step3_verify_data(self):
        """Step 3: Verify data integrity"""
        logger.info("=" * 80)
        logger.info("STEP 3: Verifying data integrity")
        logger.info("=" * 80)

        # Compare row counts
        logger.info("\n📊 Row Count Comparison:")
        result = self.client.execute("""
            SELECT 'aggregates' as table, COUNT(*) as total_rows,
                   COUNT(DISTINCT (symbol, timeframe, timestamp)) as unique
            FROM aggregates
            UNION ALL
            SELECT 'aggregates_new' as table, COUNT(*) as total_rows,
                   COUNT(DISTINCT (symbol, timeframe, timestamp)) as unique
            FROM aggregates_new
        """)

        for row in result:
            logger.info(f"  {row[0]:20} | Total: {row[1]:>10,} | Unique: {row[2]:>10,}")

        # Compare data ranges by symbol
        logger.info("\n📊 Data Range Comparison:")
        result = self.client.execute("""
            SELECT 'aggregates' as table, symbol,
                   MIN(timestamp) as earliest, MAX(timestamp) as latest, COUNT(*) as rows
            FROM aggregates
            GROUP BY symbol
            UNION ALL
            SELECT 'aggregates_new' as table, symbol,
                   MIN(timestamp) as earliest, MAX(timestamp) as latest, COUNT(*) as rows
            FROM aggregates_new
            GROUP BY symbol
            ORDER BY symbol, table
        """)

        current_symbol = None
        for row in result:
            table, symbol, earliest, latest, rows = row
            if symbol != current_symbol:
                logger.info(f"\n  Symbol: {symbol}")
                current_symbol = symbol
            logger.info(f"    {table:20} | {earliest} to {latest} | {rows:>10,} rows")

        # Check for missing data
        logger.info("\n🔍 Checking for missing symbols...")
        result = self.client.execute("""
            SELECT symbol FROM aggregates
            GROUP BY symbol
            EXCEPT
            SELECT symbol FROM aggregates_new
            GROUP BY symbol
        """)

        if result:
            logger.error(f"❌ Missing symbols in new table: {[row[0] for row in result]}")
        else:
            logger.info("✅ All symbols present in new table")

        logger.info("\n✅ Data verification complete")

    def step4_rename_tables(self):
        """Step 4: Rename tables (swap old and new)"""
        logger.info("=" * 80)
        logger.info("STEP 4: Renaming tables (CRITICAL STEP!)")
        logger.info("=" * 80)

        logger.warning("⚠️  This will rename:")
        logger.warning("     aggregates → aggregates_old")
        logger.warning("     aggregates_new → aggregates")
        logger.warning("⚠️  Make sure data verification passed!")

        response = input("\nProceed with table rename? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("⏭️  Skipping table rename")
            return

        logger.info("🔄 Renaming tables...")

        # Rename old table to backup
        self.client.execute("RENAME TABLE aggregates TO aggregates_old")
        logger.info("✅ Renamed aggregates → aggregates_old")

        # Rename new table to active
        self.client.execute("RENAME TABLE aggregates_new TO aggregates")
        logger.info("✅ Renamed aggregates_new → aggregates")

        logger.info("✅ Table rename complete!")
        logger.info("⚠️  Old table preserved as aggregates_old (can be dropped after verification)")

    def step5_optimize(self):
        """Step 5: Run OPTIMIZE TABLE to apply deduplication"""
        logger.info("=" * 80)
        logger.info("STEP 5: Running OPTIMIZE TABLE FINAL")
        logger.info("=" * 80)

        logger.info("🔄 This will merge all parts and apply deduplication")
        logger.info("⏱️  This may take several minutes depending on data size")

        response = input("\nProceed with OPTIMIZE? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("⏭️  Skipping OPTIMIZE")
            return

        logger.info("🔄 Running OPTIMIZE TABLE aggregates FINAL...")
        start_time = datetime.now()

        self.client.execute("OPTIMIZE TABLE aggregates FINAL")

        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ OPTIMIZE completed in {duration:.1f} seconds")

    def step6_final_verification(self):
        """Step 6: Final verification and cleanup instructions"""
        logger.info("=" * 80)
        logger.info("STEP 6: Final Verification")
        logger.info("=" * 80)

        # Check for duplicates (should be 0)
        logger.info("\n🔍 Checking for remaining duplicates...")
        result = self.client.execute("""
            SELECT symbol, timeframe, timestamp, COUNT(*) as count
            FROM aggregates FINAL
            GROUP BY symbol, timeframe, timestamp
            HAVING count > 1
            LIMIT 10
        """)

        if result:
            logger.error(f"❌ Found {len(result)} duplicate combinations:")
            for row in result:
                logger.error(f"  {row[0]} {row[1]} @ {row[2]} ({row[3]} occurrences)")
        else:
            logger.info("✅ No duplicates found!")

        # Check storage size
        logger.info("\n📊 Storage Comparison:")
        result = self.client.execute("""
            SELECT
                table,
                formatReadableSize(sum(bytes)) as size,
                sum(rows) as rows,
                max(modification_time) as latest_modification
            FROM system.parts
            WHERE table IN ('aggregates', 'aggregates_old')
              AND active = 1
            GROUP BY table
        """)

        for row in result:
            logger.info(f"  {row[0]:20} | Size: {row[1]:>10} | Rows: {row[2]:>12,} | Modified: {row[3]}")

        # Query performance test
        logger.info("\n⚡ Query Performance Test:")
        test_query = """
            SELECT symbol, timeframe, COUNT(*) as bars
            FROM aggregates FINAL
            WHERE timestamp >= now() - INTERVAL 7 DAY
            GROUP BY symbol, timeframe
        """

        start_time = datetime.now()
        result = self.client.execute(test_query)
        duration = (datetime.now() - start_time).total_seconds()

        logger.info(f"  Query completed in {duration:.3f} seconds")
        logger.info(f"  Result: {len(result)} rows")

        # Cleanup instructions
        logger.info("\n" + "=" * 80)
        logger.info("✅ MIGRATION COMPLETE!")
        logger.info("=" * 80)
        logger.info("\nNext steps:")
        logger.info("1. Monitor application for 24-48 hours")
        logger.info("2. Verify no errors in logs")
        logger.info("3. If everything works correctly:")
        logger.info("   DROP TABLE aggregates_old;")
        logger.info("\n⚠️  Keep backup table for at least 7 days before dropping")

    def run_all_steps(self):
        """Run all migration steps interactively"""
        logger.info("=" * 80)
        logger.info("ClickHouse Migration: MergeTree → ReplacingMergeTree")
        logger.info("=" * 80)

        steps = [
            ("Create new table", self.step1_create_new_table),
            ("Copy data", self.step2_copy_data),
            ("Verify data", self.step3_verify_data),
            ("Rename tables", self.step4_rename_tables),
            ("Optimize table", self.step5_optimize),
            ("Final verification", self.step6_final_verification),
        ]

        for i, (name, func) in enumerate(steps, 1):
            logger.info(f"\n{'='*80}")
            logger.info(f"Step {i}/6: {name}")
            logger.info(f"{'='*80}")

            response = input(f"\nRun step {i}? (yes/no/quit): ")
            if response.lower() == 'quit':
                logger.info("Migration stopped by user")
                return
            elif response.lower() == 'yes':
                try:
                    func()
                except Exception as e:
                    logger.error(f"❌ Error in step {i}: {e}")
                    response = input("Continue to next step? (yes/no): ")
                    if response.lower() != 'yes':
                        return
            else:
                logger.info(f"⏭️  Skipped step {i}")


def main():
    parser = argparse.ArgumentParser(description="ClickHouse MergeTree → ReplacingMergeTree Migration")
    parser.add_argument('--host', default='suho-clickhouse', help='ClickHouse host')
    parser.add_argument('--port', type=int, default=9000, help='ClickHouse native port')
    parser.add_argument('--user', default='suho_analytics', help='ClickHouse user')
    parser.add_argument('--password', required=True, help='ClickHouse password')
    parser.add_argument('--database', default='suho_analytics', help='Database name')
    parser.add_argument('--step', type=int, choices=[1,2,3,4,5,6], help='Run specific step')
    parser.add_argument('--all', action='store_true', help='Run all steps interactively')

    args = parser.parse_args()

    try:
        migration = ClickHouseMigration(
            host=args.host,
            port=args.port,
            user=args.user,
            password=args.password,
            database=args.database
        )

        if args.all:
            migration.run_all_steps()
        elif args.step:
            steps = {
                1: migration.step1_create_new_table,
                2: migration.step2_copy_data,
                3: migration.step3_verify_data,
                4: migration.step4_rename_tables,
                5: migration.step5_optimize,
                6: migration.step6_final_verification,
            }
            steps[args.step]()
        else:
            parser.print_help()

    except KeyboardInterrupt:
        logger.info("\nMigration interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
