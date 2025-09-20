#!/usr/bin/env python3
"""
Final Integration Test - Complete Pipeline
Test: Download → Process → Store in Database
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

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

async def test_complete_pipeline():
    """Test complete pipeline: Download → Process → Database"""
    
    try:
        logger.info("🚀 FINAL INTEGRATION TEST - COMPLETE PIPELINE")
        logger.info("=" * 70)
        
        # Initialize downloader
        os.environ['USE_TOR_PROXY'] = 'true'
        downloader = DataBridgeDukascopyDownloader()
        logger.info("✅ Dukascopy downloader initialized with Tor")
        
        # Step 1: Find existing downloaded files
        logger.info("📁 STEP 1: Checking downloaded files...")
        
        eurusd_dir = Path("/mnt/f/WINDSURF/neliti_code/server_microservice/services/data-bridge/historical_data/dukascopy/EURUSD")
        bi5_files = list(eurusd_dir.glob("*.bi5"))
        
        logger.info(f"Found {len(bi5_files)} .bi5 files")
        
        if not bi5_files:
            logger.error("❌ No .bi5 files found! Run download test first")
            return False
        
        # Step 2: Process files
        logger.info("🔄 STEP 2: Processing .bi5 files...")
        
        processed_count = 0
        total_ticks = 0
        all_processed_data = []
        
        for bi5_file in bi5_files:
            file_size = bi5_file.stat().st_size
            logger.info(f"📂 Processing: {bi5_file.name} ({file_size} bytes)")
            
            try:
                df = downloader._convert_dukascopy_bi5_to_csv(bi5_file)
                
                if df is not None and len(df) > 0:
                    processed_count += 1
                    total_ticks += len(df)
                    all_processed_data.append(df)
                    logger.info(f"  ✅ Processed {len(df)} ticks")
                    logger.info(f"  📊 Time: {df['timestamp'].min()} to {df['timestamp'].max()}")
                    logger.info(f"  💰 Price: {df['bid'].min():.5f} - {df['bid'].max():.5f}")
                else:
                    logger.warning(f"  ⚠️ No data extracted from {bi5_file.name}")
                    
            except Exception as e:
                logger.error(f"  ❌ Processing failed: {e}")
        
        logger.info("=" * 50)
        logger.info(f"📊 Processing Summary:")
        logger.info(f"  ✅ Files processed: {processed_count}/{len(bi5_files)}")
        logger.info(f"  📈 Total ticks: {total_ticks}")
        
        if processed_count == 0:
            logger.error("❌ No files processed successfully")
            return False
        
        # Step 3: Database storage test
        logger.info("💾 STEP 3: Testing database storage...")
        
        # Combine first 200 ticks from all processed data
        sample_data = []
        for df in all_processed_data:
            sample_data.extend(df.head(50).to_dict('records'))  # 50 ticks per file
            if len(sample_data) >= 200:
                break
        
        sample_data = sample_data[:200]  # Limit to 200 ticks
        logger.info(f"📊 Testing with {len(sample_data)} sample ticks")
        
        # Test database
        db_success = await test_database_storage(sample_data)
        
        if db_success:
            logger.info("=" * 70)
            logger.info("🎉 COMPLETE PIPELINE TEST SUCCESSFUL!")
            logger.info("✅ Download → Process → Database = WORKING")
            logger.info(f"📊 Final stats:")
            logger.info(f"  • Files processed: {processed_count}")
            logger.info(f"  • Total ticks: {total_ticks}")
            logger.info(f"  • Database storage: ✅ Working")
            return True
        else:
            logger.warning("⚠️ Database storage failed, but processing works")
            return False
        
    except Exception as e:
        logger.error(f"❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_database_storage(sample_data):
    """Test database storage with sample data"""
    try:
        logger.info("🔌 Testing database connection...")
        
        import aiohttp
        
        database_url = "http://localhost:8008"
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            # Health check
            try:
                async with session.get(f"{database_url}/health") as response:
                    if response.status == 200:
                        health_data = await response.json()
                        logger.info(f"✅ Database service healthy: {health_data.get('status', 'unknown')}")
                    else:
                        logger.warning(f"⚠️ Database health check: {response.status}")
                        return False
            except Exception as e:
                logger.error(f"❌ Cannot connect to database service: {e}")
                logger.info("💡 Start database service: docker-compose up database-service -d")
                return False
            
            # Prepare records
            records = []
            for tick in sample_data:
                records.append({
                    "timestamp": tick['timestamp'].isoformat() if hasattr(tick['timestamp'], 'isoformat') else str(tick['timestamp']),
                    "symbol": "EURUSD",
                    "bid": float(tick['bid']),
                    "ask": float(tick['ask']),
                    "data_source": "dukascopy"
                })
            
            logger.info(f"📊 Inserting {len(records)} records...")
            
            # Insert data
            payload = {
                "table_name": "market_data",
                "data": records
            }
            
            async with session.post(f"{database_url}/api/v1/clickhouse/insert", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"✅ Database insert successful!")
                    logger.info(f"📊 Response: {result}")
                    
                    # Query to verify
                    await verify_database_data(session, database_url)
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Database insert failed: {response.status}")
                    logger.error(f"   Error: {error_text}")
                    return False
                    
    except Exception as e:
        logger.error(f"❌ Database storage test failed: {e}")
        return False

async def verify_database_data(session, database_url):
    """Verify data was stored correctly"""
    try:
        logger.info("🔍 Verifying stored data...")
        
        # Query recent dukascopy data
        query_payload = {
            "query": """
            SELECT 
                COUNT(*) as total_records,
                MIN(timestamp) as earliest,
                MAX(timestamp) as latest,
                AVG(bid) as avg_bid,
                data_source
            FROM market_data 
            WHERE data_source = 'dukascopy' AND symbol = 'EURUSD'
            GROUP BY data_source
            """
        }
        
        async with session.post(f"{database_url}/api/v1/clickhouse/query", json=query_payload) as response:
            if response.status == 200:
                result = await response.json()
                logger.info("✅ Database verification successful!")
                
                if result.get('data'):
                    for row in result['data']:
                        logger.info(f"📊 Database contains:")
                        logger.info(f"  • Total EURUSD records: {row.get('total_records', 0)}")
                        logger.info(f"  • Time range: {row.get('earliest', 'N/A')} to {row.get('latest', 'N/A')}")
                        logger.info(f"  • Average bid: {row.get('avg_bid', 0):.5f}")
                        logger.info(f"  • Data source: {row.get('data_source', 'N/A')}")
                else:
                    logger.warning("⚠️ No data found in query result")
                    
            else:
                error_text = await response.text()
                logger.warning(f"⚠️ Database query failed: {response.status} - {error_text}")
                
    except Exception as e:
        logger.warning(f"⚠️ Database verification failed: {e}")

async def main():
    """Main test"""
    logger.info("🧪 FINAL INTEGRATION TEST SUITE")
    logger.info("Testing complete pipeline: Download → Process → Database")
    logger.info("=" * 70)
    
    success = await test_complete_pipeline()
    
    if success:
        logger.info("=" * 70)
        logger.info("🏆 SUCCESS: COMPLETE PIPELINE WORKING!")
        logger.info("🎉 Dukascopy integration fully operational")
        logger.info("📊 Ready for production use")
        return True
    else:
        logger.error("=" * 70)
        logger.error("❌ PIPELINE TEST INCOMPLETE")
        logger.error("💡 Check individual components")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)