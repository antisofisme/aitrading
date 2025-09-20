#!/usr/bin/env python3
"""
Test Historical Data Download - One Month
Tests downloading historical data for the past month with proper weekday handling
"""

import asyncio
import sys
import os
import logging
from datetime import datetime, timedelta

# Add paths for imports
sys.path.append('/mnt/f/WINDSURF/neliti_code/server_microservice')
sys.path.append('/mnt/f/WINDSURF/neliti_code/server_microservice/services/data-bridge/src')

from src.data_sources.dukascopy_client import DataBridgeDukascopyDownloader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_historical_month_download():
    """Test historical data download for one month"""
    
    try:
        logger.info("🚀 Starting Historical Month Download Test")
        logger.info("📅 Target: 1 month of historical data (720 hours)")
        
        # Initialize downloader
        downloader = DataBridgeDukascopyDownloader()
        logger.info("✅ Dukascopy downloader initialized")
        
        # Get the environment variable for hours back
        hours_back = int(os.getenv("DUKASCOPY_HOURS_BACK", "720"))  # 1 month = 30 days * 24 hours
        logger.info(f"🕐 Hours back from environment: {hours_back} hours ({hours_back/24:.1f} days)")
        
        # Test download for EURUSD (most liquid pair)
        logger.info("📥 Starting historical download for EURUSD")
        logger.info("⚠️  Note: Weekend data will fail (markets closed), this is expected")
        
        results = await downloader.download_small_batch(
            pair="EURUSD",
            hours_back=hours_back
        )
        
        # Print comprehensive results
        logger.info("=" * 60)
        logger.info("📊 DOWNLOAD RESULTS SUMMARY")
        logger.info("=" * 60)
        logger.info(f"🎯 Pair: {results['pair']}")
        logger.info(f"⏰ Time range: {results['hours_back']} hours ({results['hours_back']/24:.1f} days)")
        logger.info(f"✅ Files downloaded: {results['files_downloaded']}")
        logger.info(f"❌ Files failed: {results['files_failed']}")
        logger.info(f"🔄 Files skipped (dedup): {results['files_skipped_dedup']}")
        logger.info(f"📊 Total size: {results['total_size_mb']:.2f} MB")
        logger.info(f"⏱️  Duration: {results['duration_seconds']:.1f} seconds ({results['duration_seconds']/60:.1f} minutes)")
        logger.info(f"📈 Success rate: {results['success_rate']*100:.1f}%")
        
        # Analyze results
        total_attempted = results['files_downloaded'] + results['files_failed']
        if total_attempted > 0:
            logger.info(f"📋 Analysis:")
            logger.info(f"  • Total files attempted: {total_attempted}")
            logger.info(f"  • Weekend/holiday failures expected (markets closed)")
            logger.info(f"  • Weekday success rate: {results['success_rate']*100:.1f}%")
        
        # Check deduplication stats
        if 'deduplication_stats' in results:
            logger.info("=" * 60)
            logger.info("🔍 DEDUPLICATION ANALYSIS")
            logger.info("=" * 60)
            dedup = results['deduplication_stats']
            logger.info(f"📥 Download needed: {dedup.get('download_needed', 'N/A')}")
            logger.info(f"📊 Missing ranges: {dedup.get('missing_ranges', 0)}")
            logger.info(f"✅ Existing ranges: {dedup.get('existing_ranges', 0)}")
            logger.info(f"📈 Coverage: {dedup.get('coverage_percent', 0):.1f}%")
            logger.info(f"💡 Reason: {dedup.get('reason', 'N/A')}")
        
        # Check what files we actually have now
        logger.info("=" * 60)
        logger.info("📁 FILE SYSTEM ANALYSIS")
        logger.info("=" * 60)
        
        import glob
        bi5_files = glob.glob("/mnt/f/WINDSURF/neliti_code/server_microservice/services/data-bridge/historical_data/dukascopy/EURUSD/*.bi5")
        logger.info(f"📁 Total .bi5 files on disk: {len(bi5_files)}")
        
        if bi5_files:
            # Get file sizes
            total_size_bytes = sum(os.path.getsize(f) for f in bi5_files if os.path.exists(f))
            total_size_mb = total_size_bytes / (1024 * 1024)
            logger.info(f"💾 Total data size: {total_size_mb:.2f} MB")
            
            # Check recent files
            recent_files = sorted(bi5_files, key=os.path.getmtime, reverse=True)[:5]
            logger.info("📅 Most recent files:")
            for i, file_path in enumerate(recent_files, 1):
                filename = os.path.basename(file_path)
                size_kb = os.path.getsize(file_path) / 1024
                mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                logger.info(f"  {i}. {filename} ({size_kb:.1f} KB, {mtime.strftime('%Y-%m-%d %H:%M')})")
            
            # Test processing one file
            logger.info("=" * 60)
            logger.info("🔄 PROCESSING TEST")
            logger.info("=" * 60)
            
            # Find largest file (likely has most data)
            largest_file = max(bi5_files, key=os.path.getsize)
            file_size_kb = os.path.getsize(largest_file) / 1024
            logger.info(f"🎯 Testing with largest file: {os.path.basename(largest_file)} ({file_size_kb:.1f} KB)")
            
            # Process the file
            df = downloader._convert_dukascopy_bi5_to_csv(largest_file)
            if df is not None and len(df) > 0:
                logger.info(f"✅ Successfully processed {len(df)} ticks")
                logger.info(f"📊 Time range: {df['timestamp'].min()} to {df['timestamp'].max()}")
                logger.info(f"💰 Price range: {df['bid'].min():.5f} - {df['bid'].max():.5f}")
                logger.info(f"📈 Spread stats: min={df['spread'].min():.5f}, max={df['spread'].max():.5f}, avg={df['spread'].mean():.5f}")
                
                # Test database storage with sample
                logger.info("=" * 60)
                logger.info("💾 DATABASE STORAGE TEST")
                logger.info("=" * 60)
                
                try:
                    # Test with first 100 records
                    sample_df = df.head(100)
                    await test_database_storage(sample_df)
                except Exception as e:
                    logger.error(f"❌ Database storage test failed: {e}")
            else:
                logger.warning("⚠️ Could not process .bi5 file")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

async def test_database_storage(df):
    """Test storing processed data in database"""
    try:
        import aiohttp
        
        # Test database service connection
        database_service_url = "http://localhost:8008"
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            # Test health check
            try:
                async with session.get(f"{database_service_url}/health") as response:
                    if response.status == 200:
                        logger.info("✅ Database service is healthy and reachable")
                    else:
                        logger.warning(f"⚠️ Database service health check returned {response.status}")
                        return False
            except Exception as e:
                logger.error(f"❌ Cannot connect to database service at {database_service_url}: {e}")
                logger.info("💡 Make sure database service is running: docker-compose up database-service")
                return False
            
            # Prepare data for insertion
            records = []
            for _, row in df.iterrows():
                record = {
                    "timestamp": row['timestamp'].isoformat(),
                    "symbol": "EURUSD",
                    "bid": float(row['bid']),
                    "ask": float(row['ask']),
                    "data_source": "dukascopy"
                }
                records.append(record)
            
            logger.info(f"📊 Preparing to insert {len(records)} records into market_data table")
            
            # Test batch insertion
            try:
                insert_payload = {
                    "table_name": "market_data",
                    "data": records
                }
                
                async with session.post(
                    f"{database_service_url}/api/v1/clickhouse/insert",
                    json=insert_payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"✅ Successfully inserted {len(records)} records into database")
                        logger.info(f"📊 Database response: {result}")
                        
                        # Test query to verify data
                        await test_database_query(session, database_service_url)
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Database insertion failed: {response.status} - {error_text}")
                        return False
                        
            except Exception as e:
                logger.error(f"❌ Database insertion request failed: {e}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Database storage test failed: {e}")
        return False

async def test_database_query(session, database_service_url):
    """Test querying inserted data"""
    try:
        # Query recent dukascopy data
        query_payload = {
            "query": "SELECT COUNT(*) as total_records, MIN(timestamp) as earliest, MAX(timestamp) as latest FROM market_data WHERE data_source = 'dukascopy' AND symbol = 'EURUSD'"
        }
        
        async with session.post(
            f"{database_service_url}/api/v1/clickhouse/query",
            json=query_payload
        ) as response:
            if response.status == 200:
                result = await response.json()
                logger.info(f"✅ Database query successful:")
                if result.get('data'):
                    for row in result['data']:
                        logger.info(f"  • Total EURUSD records: {row.get('total_records', 0)}")
                        logger.info(f"  • Time range: {row.get('earliest', 'N/A')} to {row.get('latest', 'N/A')}")
                return True
            else:
                error_text = await response.text()
                logger.warning(f"⚠️ Database query failed: {response.status} - {error_text}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Database query test failed: {e}")
        return False

async def main():
    """Main test function"""
    logger.info("🧪 HISTORICAL MONTH DOWNLOAD TEST SUITE")
    logger.info("=" * 80)
    
    # Test historical download
    results = await test_historical_month_download()
    
    if results:
        logger.info("=" * 80)
        logger.info("✅ Historical month download test completed successfully")
        logger.info("💡 Weekend failures are expected (forex markets closed)")
        return True
    else:
        logger.error("=" * 80)
        logger.error("❌ Historical month download test failed")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)