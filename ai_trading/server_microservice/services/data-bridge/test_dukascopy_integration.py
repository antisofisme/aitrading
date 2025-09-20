#!/usr/bin/env python3
"""
Test Dukascopy Integration with Database Storage
Tests the complete flow: Download -> Process -> Store in Database
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

async def test_dukascopy_download_and_storage():
    """Test complete Dukascopy download and database storage"""
    
    try:
        logger.info("🚀 Starting Dukascopy Integration Test")
        
        # Initialize downloader
        downloader = DataBridgeDukascopyDownloader()
        logger.info("✅ Dukascopy downloader initialized")
        
        # Test small batch download (last 24 hours)
        logger.info("📥 Testing small batch download (24 hours)")
        results = await downloader.download_small_batch(
            pair="EURUSD",
            hours_back=24  # Last 24 hours
        )
        
        # Print results
        logger.info("📊 Download Results:")
        logger.info(f"  Pair: {results['pair']}")
        logger.info(f"  Hours back: {results['hours_back']}")
        logger.info(f"  Files downloaded: {results['files_downloaded']}")
        logger.info(f"  Files failed: {results['files_failed']}")
        logger.info(f"  Files skipped (dedup): {results['files_skipped_dedup']}")
        logger.info(f"  Total size: {results['total_size_mb']:.2f} MB")
        logger.info(f"  Duration: {results['duration_seconds']:.1f} seconds")
        logger.info(f"  Success rate: {results['success_rate']*100:.1f}%")
        
        # Check deduplication stats
        if 'deduplication_stats' in results:
            logger.info("🔍 Deduplication Stats:")
            dedup = results['deduplication_stats']
            logger.info(f"  Download needed: {dedup.get('download_needed', 'N/A')}")
            logger.info(f"  Coverage: {dedup.get('coverage_percent', 0):.1f}%")
            logger.info(f"  Reason: {dedup.get('reason', 'N/A')}")
        
        # Process and store data if files were downloaded
        if results['files_downloaded'] > 0:
            logger.info("🔄 Processing downloaded files...")
            
            # Check if there are .bi5 files to process
            import glob
            bi5_files = glob.glob("/mnt/f/WINDSURF/neliti_code/server_microservice/services/data-bridge/historical_data/dukascopy/EURUSD/*.bi5")
            logger.info(f"📁 Found {len(bi5_files)} .bi5 files")
            
            if bi5_files:
                # Process the most recent file
                latest_file = max(bi5_files, key=os.path.getctime)
                logger.info(f"🔄 Processing latest file: {os.path.basename(latest_file)}")
                
                # Convert and process
                df = downloader._convert_dukascopy_bi5_to_csv(latest_file)
                if df is not None and len(df) > 0:
                    logger.info(f"✅ Successfully processed {len(df)} ticks")
                    logger.info(f"📊 Time range: {df['timestamp'].min()} to {df['timestamp'].max()}")
                    
                    # Try to store in database
                    try:
                        await test_database_storage(df.head(10))  # Test with first 10 records
                    except Exception as e:
                        logger.error(f"❌ Database storage failed: {e}")
                else:
                    logger.warning("⚠️ No data processed from .bi5 file")
            else:
                logger.info("ℹ️ No .bi5 files found to process")
        else:
            logger.info("ℹ️ No files downloaded - might be due to deduplication")
        
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
        
        async with aiohttp.ClientSession() as session:
            # Test health check
            try:
                async with session.get(f"{database_service_url}/health") as response:
                    if response.status == 200:
                        logger.info("✅ Database service is healthy")
                    else:
                        logger.warning(f"⚠️ Database service health check returned {response.status}")
            except Exception as e:
                logger.error(f"❌ Cannot connect to database service: {e}")
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

async def main():
    """Main test function"""
    logger.info("🧪 Starting Dukascopy Integration Test Suite")
    logger.info("=" * 60)
    
    # Test 1: Download and process data
    results = await test_dukascopy_download_and_storage()
    
    if results:
        logger.info("✅ Dukascopy integration test completed successfully")
        return True
    else:
        logger.error("❌ Dukascopy integration test failed")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)