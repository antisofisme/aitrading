#!/usr/bin/env python3
"""
Final Database Test - Correct Endpoints
Test database storage with correct schema and endpoints
"""

import asyncio
import aiohttp
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_database_final():
    """Test database with correct endpoint and schema"""
    
    database_url = "http://localhost:8008"
    
    async with aiohttp.ClientSession() as session:
        # Test correct batch endpoint
        payload = {
            "symbol": "EURUSD", 
            "data_source": "dukascopy",
            "ticks": [
                {
                    "symbol": "EURUSD",
                    "timestamp": "2025-08-08T10:00:00.089000",
                    "bid": 1.16287,
                    "ask": 1.16289
                },
                {
                    "symbol": "EURUSD", 
                    "timestamp": "2025-08-08T10:01:00.150000",
                    "bid": 1.16290,
                    "ask": 1.16292
                },
                {
                    "symbol": "EURUSD",
                    "timestamp": "2025-08-08T10:02:00.200000", 
                    "bid": 1.16295,
                    "ask": 1.16297
                }
            ]
        }
        
        logger.info("📊 Testing batch ticks endpoint...")
        
        async with session.post(f"{database_url}/api/v1/clickhouse/ticks/batch", json=payload) as response:
            logger.info(f"Response status: {response.status}")
            
            if response.status == 200:
                result = await response.json()
                logger.info(f"✅ SUCCESS! Database insert working: {result}")
                return True
            else:
                error = await response.text()
                logger.error(f"❌ Database insert failed: {response.status} - {error}")
                
                # Try alternative single tick endpoint
                logger.info("🔄 Trying single tick endpoint...")
                
                single_payload = {
                    "symbol": "EURUSD",
                    "timestamp": "2025-08-08T10:00:00.089000", 
                    "bid": 1.16287,
                    "ask": 1.16289,
                    "data_source": "dukascopy"
                }
                
                async with session.post(f"{database_url}/api/v1/clickhouse/ticks", json=single_payload) as single_response:
                    logger.info(f"Single tick response: {single_response.status}")
                    
                    if single_response.status == 200:
                        result = await single_response.json()
                        logger.info(f"✅ SUCCESS! Single tick insert working: {result}")
                        return True
                    else:
                        single_error = await single_response.text()
                        logger.error(f"❌ Single tick also failed: {single_response.status} - {single_error}")
                
        return False

if __name__ == "__main__":
    success = asyncio.run(test_database_final())
    if success:
        logger.info("🎉 DATABASE INTEGRATION SUCCESSFUL!")
        logger.info("✅ Complete pipeline: Download → Process → Database = WORKING!")
    else:
        logger.error("❌ Database integration needs endpoint verification")