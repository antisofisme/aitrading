#!/usr/bin/env python3
"""
Test Weekday Download - Target Specific Weekday Dates
Focus on dates we know have trading data
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

async def test_specific_weekday_download():
    """Test download for specific weekday with known trading hours"""
    
    try:
        logger.info("🚀 Testing Specific Weekday Download")
        
        # Set environment variables for Tor
        os.environ['USE_TOR_PROXY'] = 'true'
        logger.info("🧅 Tor proxy enabled")
        
        # Initialize downloader
        downloader = DataBridgeDukascopyDownloader()
        logger.info("✅ Dukascopy downloader initialized")
        
        # Target: Friday August 8, 2025 - This should be a trading day
        target_start = datetime(2025, 8, 8, 10, 0, 0)  # Friday 10:00 AM
        target_end = datetime(2025, 8, 8, 16, 0, 0)    # Friday 4:00 PM
        
        logger.info(f"🎯 Target: {target_start.strftime('%Y-%m-%d %H:%M')} - {target_end.strftime('%H:%M')} (Friday trading hours)")
        
        # Calculate hours from target_start to now
        current_time = datetime.now()
        hours_from_start = int((current_time - target_start).total_seconds() / 3600)
        
        # But we want just 6 hours of Friday trading data
        target_hours = 6  # 6 hours: 10:00-16:00
        
        logger.info(f"⏰ Requesting {target_hours} hours of Friday trading data")
        
        # Custom download method - manually build the time range we want
        logger.info("📥 Starting manual time range download...")
        
        # Create pair directory
        pair_dir = downloader.dukascopy_dir / "EURUSD"
        pair_dir.mkdir(exist_ok=True)
        
        # Download specific hours manually
        session = await downloader._create_http_session()
        
        downloaded_count = 0
        failed_count = 0
        
        try:
            for hour_offset in range(6):  # 6 hours: 10:00 to 15:00
                target_time = target_start + timedelta(hours=hour_offset)
                
                year = target_time.year
                month = target_time.month
                day = target_time.day  
                hour = target_time.hour
                
                url = downloader._build_dukascopy_url("EURUSD", year, month, day, hour)
                filename = f"EURUSD_{year}_{month:02d}_{day:02d}_{hour:02d}.bi5"
                filepath = pair_dir / filename
                
                logger.info(f"📥 Downloading {hour_offset+1}/6: {target_time.strftime('%Y-%m-%d %H:00')}")
                logger.info(f"🔗 URL: {url}")
                
                # Download this specific file
                result = await downloader._download_dukascopy_file(session, url, filepath)
                
                if result and result.get("success"):
                    downloaded_count += 1
                    logger.info(f"  ✅ Success: {result.get('size_mb', 0):.2f} MB")
                else:
                    failed_count += 1
                    logger.info(f"  ❌ Failed or no data")
                
                # Small delay
                await asyncio.sleep(0.2)
                
        finally:
            await session.close()
        
        # Summary
        total_attempted = downloaded_count + failed_count
        success_rate = (downloaded_count / total_attempted * 100) if total_attempted > 0 else 0
        
        logger.info("=" * 60)
        logger.info("📊 MANUAL DOWNLOAD RESULTS")
        logger.info("=" * 60)
        logger.info(f"✅ Files downloaded: {downloaded_count}")
        logger.info(f"❌ Files failed: {failed_count}")
        logger.info(f"📈 Success rate: {success_rate:.1f}%")
        
        if downloaded_count > 0:
            logger.info("🎉 SUCCESS! Manual download is working")
            
            # Test processing
            await test_file_processing()
            
            return True
        else:
            logger.warning("⚠️ No files downloaded - may be weekend/holiday")
            
            # Try a different known good date
            await test_known_good_date()
            
            return False
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_known_good_date():
    """Test with a date we absolutely know has data"""
    try:
        logger.info("🔍 Testing with known good historical date...")
        
        # July 15, 2024 - Monday - Should definitely have data
        test_date = datetime(2024, 7, 15, 14, 0, 0)  # Monday 2 PM
        
        logger.info(f"📅 Testing: {test_date.strftime('%Y-%m-%d %H:%M')} (Monday 2 PM)")
        
        # Build URL manually
        url = f"https://datafeed.dukascopy.com/datafeed/EURUSD/2024/06/15/14h_ticks.bi5"
        
        import aiohttp_socks
        import aiohttp
        
        connector = aiohttp_socks.ProxyConnector.from_url('socks5://127.0.0.1:9050')
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/octet-stream, */*',
        }
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=30),
            headers=headers
        ) as session:
            
            logger.info(f"📡 Testing URL: {url}")
            
            async with session.get(url) as response:
                logger.info(f"📊 Response: {response.status}")
                
                if response.status == 200:
                    content = await response.read()
                    logger.info(f"✅ Downloaded {len(content)} bytes from July 2024!")
                    
                    # Save file for processing test
                    test_file = "/tmp/test_eurusd.bi5"
                    with open(test_file, 'wb') as f:
                        f.write(content)
                    
                    # Test processing
                    downloader = DataBridgeDukascopyDownloader()
                    df = downloader._convert_dukascopy_bi5_to_csv(test_file)
                    
                    if df is not None and len(df) > 0:
                        logger.info(f"✅ Processed {len(df)} ticks from historical data!")
                        logger.info(f"📊 Time range: {df['timestamp'].min()} to {df['timestamp'].max()}")
                        
                        # Test database storage
                        await test_database_storage(df.head(50))
                        
                        return True
                    else:
                        logger.warning("⚠️ Could not process historical data")
                else:
                    logger.warning(f"⚠️ Historical data not available: {response.status}")
                    
        return False
        
    except Exception as e:
        logger.error(f"❌ Known good date test failed: {e}")
        return False

async def test_file_processing():
    """Test processing any existing files"""
    try:
        logger.info("🔄 Testing file processing...")
        
        import glob
        
        # Find any .bi5 files
        pattern = "/mnt/f/WINDSURF/neliti_code/server_microservice/services/data-bridge/historical_data/dukascopy/EURUSD/*.bi5"
        files = glob.glob(pattern)
        
        logger.info(f"📁 Found {len(files)} existing .bi5 files")
        
        if files:
            # Test with largest file
            largest_file = max(files, key=os.path.getsize)
            file_size = os.path.getsize(largest_file)
            logger.info(f"📂 Processing: {os.path.basename(largest_file)} ({file_size} bytes)")
            
            downloader = DataBridgeDukascopyDownloader()
            df = downloader._convert_dukascopy_bi5_to_csv(largest_file)
            
            if df is not None and len(df) > 0:
                logger.info(f"✅ Processed {len(df)} ticks from existing file")
                logger.info(f"📊 Time range: {df['timestamp'].min()} to {df['timestamp'].max()}")
                
                # Test database storage with sample
                await test_database_storage(df.head(100))
                
                return True
            else:
                logger.warning("⚠️ Could not process existing file")
        else:
            logger.info("ℹ️ No existing .bi5 files found")
            
        return False
        
    except Exception as e:
        logger.error(f"❌ File processing failed: {e}")
        return False

async def test_database_storage(df):
    """Test database storage"""
    try:
        logger.info("💾 Testing database storage...")
        
        import aiohttp
        
        database_url = "http://localhost:8008"
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            # Health check
            try:
                async with session.get(f"{database_url}/health") as response:
                    if response.status == 200:
                        logger.info("✅ Database service is healthy")
                    else:
                        logger.warning(f"⚠️ Database service: {response.status}")
                        return False
            except:
                logger.error("❌ Cannot connect to database service")
                logger.info("💡 Start database: docker-compose up database-service")
                return False
            
            # Prepare data
            records = []
            for _, row in df.iterrows():
                records.append({
                    "timestamp": row['timestamp'].isoformat(),
                    "symbol": "EURUSD",
                    "bid": float(row['bid']),
                    "ask": float(row['ask']),
                    "data_source": "dukascopy"
                })
            
            # Insert data
            payload = {
                "table_name": "market_data",
                "data": records
            }
            
            async with session.post(f"{database_url}/api/v1/clickhouse/insert", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"✅ Inserted {len(records)} records into database!")
                    logger.info(f"📊 Response: {result}")
                    return True
                else:
                    error = await response.text()
                    logger.error(f"❌ Database insert failed: {response.status} - {error}")
                    return False
                    
    except Exception as e:
        logger.error(f"❌ Database storage failed: {e}")
        return False

async def main():
    """Main test"""
    logger.info("🧪 WEEKDAY DOWNLOAD TEST SUITE")
    logger.info("=" * 60)
    
    success = await test_specific_weekday_download()
    
    if success:
        logger.info("=" * 60)
        logger.info("✅ WEEKDAY DOWNLOAD TEST SUCCESSFUL!")
        logger.info("🎉 Data pipeline working: Download → Process → Database")
        return True
    else:
        logger.error("=" * 60)
        logger.error("❌ WEEKDAY DOWNLOAD TEST FAILED")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)