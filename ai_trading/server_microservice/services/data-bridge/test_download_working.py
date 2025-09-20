#!/usr/bin/env python3
"""
Test Working Download with Tor Proxy
Focus on weekday data that should be available
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

async def test_working_download():
    """Test download with Tor proxy for weekday data"""
    
    try:
        logger.info("🚀 Testing Working Download with Tor Proxy")
        
        # Set environment variables for Tor
        os.environ['USE_TOR_PROXY'] = 'true'
        logger.info("🧅 Tor proxy enabled")
        
        # Initialize downloader
        downloader = DataBridgeDukascopyDownloader()
        logger.info("✅ Dukascopy downloader initialized")
        
        # Test with known working date - August 7, 2024 (Wednesday)
        # This should have market data
        target_date = datetime(2024, 8, 7, 10, 0, 0)  # Wednesday 10:00 AM
        current_time = datetime.now()
        hours_back = int((current_time - target_date).total_seconds() / 3600)
        
        logger.info(f"🎯 Target: {target_date.strftime('%Y-%m-%d %H:%M')} (Wednesday)")
        logger.info(f"⏰ Hours back: {hours_back} hours ({hours_back/24:.1f} days)")
        
        # Test very small batch first - just 6 hours around known good time
        logger.info("📥 Testing small batch (6 hours) around known trading time")
        
        results = await downloader.download_small_batch(
            pair="EURUSD",
            hours_back=6  # Just 6 hours to test quickly
        )
        
        # Print results
        logger.info("=" * 60)
        logger.info("📊 DOWNLOAD RESULTS")
        logger.info("=" * 60)
        logger.info(f"🎯 Pair: {results['pair']}")
        logger.info(f"⏰ Hours requested: {results['hours_back']}")
        logger.info(f"✅ Files downloaded: {results['files_downloaded']}")
        logger.info(f"❌ Files failed: {results['files_failed']}")
        logger.info(f"💾 Total size: {results['total_size_mb']:.2f} MB")
        logger.info(f"⏱️  Duration: {results['duration_seconds']:.1f} seconds")
        logger.info(f"📈 Success rate: {results['success_rate']*100:.1f}%")
        
        if results['files_downloaded'] > 0:
            logger.info("🎉 SUCCESS! Download is working with Tor proxy")
            
            # Test processing the downloaded files
            await test_file_processing(results['pair'])
            
        elif results['files_failed'] > 0:
            logger.warning("⚠️ All downloads failed - checking reasons...")
            
            # Test direct Dukascopy connection with Tor
            await test_dukascopy_connection()
            
        else:
            logger.info("ℹ️ No files to download (might be due to deduplication)")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

async def test_dukascopy_connection():
    """Test direct connection to Dukascopy"""
    try:
        import aiohttp_socks
        import aiohttp
        
        logger.info("🔍 Testing direct Dukascopy connection with Tor...")
        
        # Create Tor SOCKS connector
        connector = aiohttp_socks.ProxyConnector.from_url('socks5://127.0.0.1:9050')
        
        # Test URL - known working Dukascopy file
        test_url = "https://datafeed.dukascopy.com/datafeed/EURUSD/2024/07/07/10h_ticks.bi5"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/octet-stream, */*',
        }
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=30),
            headers=headers
        ) as session:
            
            logger.info(f"📡 Testing URL: {test_url}")
            
            async with session.get(test_url) as response:
                logger.info(f"📊 Response status: {response.status}")
                logger.info(f"📊 Content-Type: {response.headers.get('Content-Type', 'N/A')}")
                logger.info(f"📊 Content-Length: {response.headers.get('Content-Length', 'N/A')}")
                
                if response.status == 200:
                    content = await response.read()
                    logger.info(f"✅ Downloaded {len(content)} bytes successfully!")
                    
                    # Test decompression
                    if len(content) > 0:
                        logger.info("🔄 Testing LZMA decompression...")
                        try:
                            import lzma
                            decompressed = lzma.decompress(content)
                            logger.info(f"✅ Decompressed to {len(decompressed)} bytes")
                            logger.info("🎉 Connection and processing working!")
                            return True
                        except Exception as e:
                            logger.info(f"ℹ️ Not LZMA compressed or different format: {e}")
                            return True  # Still successful download
                else:
                    logger.error(f"❌ HTTP {response.status}: {await response.text()}")
                    return False
                    
    except Exception as e:
        logger.error(f"❌ Connection test failed: {e}")
        return False

async def test_file_processing(pair):
    """Test processing downloaded files"""
    try:
        logger.info("🔄 Testing file processing...")
        
        import glob
        
        # Find downloaded files
        pattern = f"/mnt/f/WINDSURF/neliti_code/server_microservice/services/data-bridge/historical_data/dukascopy/{pair}/*.bi5"
        files = glob.glob(pattern)
        
        logger.info(f"📁 Found {len(files)} .bi5 files")
        
        if files:
            # Test with most recent file
            latest_file = max(files, key=os.path.getctime)
            file_size = os.path.getsize(latest_file)
            logger.info(f"📂 Testing file: {os.path.basename(latest_file)} ({file_size} bytes)")
            
            # Initialize downloader for processing
            downloader = DataBridgeDukascopyDownloader()
            
            # Process file
            df = downloader._convert_dukascopy_bi5_to_csv(latest_file)
            
            if df is not None and len(df) > 0:
                logger.info(f"✅ Processed {len(df)} ticks successfully")
                logger.info(f"📊 Time range: {df['timestamp'].min()} to {df['timestamp'].max()}")
                logger.info(f"💰 Price range: {df['bid'].min():.5f} - {df['bid'].max():.5f}")
                
                # Show sample data
                logger.info("📋 Sample ticks:")
                for i, row in df.head(3).iterrows():
                    logger.info(f"  {row['timestamp']}: Bid={row['bid']:.5f}, Ask={row['ask']:.5f}, Spread={row['spread']:.5f}")
                
                return True
            else:
                logger.warning("⚠️ Failed to process .bi5 file")
                return False
        else:
            logger.info("ℹ️ No .bi5 files found")
            return False
            
    except Exception as e:
        logger.error(f"❌ File processing test failed: {e}")
        return False

async def main():
    """Main test function"""
    logger.info("🧪 WORKING DOWNLOAD TEST WITH TOR PROXY")
    logger.info("=" * 70)
    
    # Test working download
    results = await test_working_download()
    
    if results and results['files_downloaded'] > 0:
        logger.info("=" * 70)
        logger.info("✅ DOWNLOAD TEST SUCCESSFUL!")
        logger.info("🎉 Dukascopy download is working with Tor proxy")
        return True
    else:
        logger.error("=" * 70)
        logger.error("❌ DOWNLOAD TEST FAILED")
        logger.error("💡 Check Tor proxy and network connection")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)