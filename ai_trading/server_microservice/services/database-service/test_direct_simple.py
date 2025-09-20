#!/usr/bin/env python3
"""
Simple Direct ClickHouse Test - Simplified Schema
Tests the 5-column table insertion without database service dependencies
"""

import asyncio
import httpx
import json
import os
from datetime import datetime

# ClickHouse connection settings
CLICKHOUSE_HOST = os.getenv('CLICKHOUSE_HOST', 'localhost')
CLICKHOUSE_PORT = int(os.getenv('CLICKHOUSE_PORT', '8123'))
CLICKHOUSE_USER = os.getenv('CLICKHOUSE_USER', 'default')
CLICKHOUSE_PASSWORD = os.getenv('CLICKHOUSE_PASSWORD', 'clickhouse_password_2024')

async def test_simplified_insertion():
    """Test simplified 5-column ClickHouse insertion"""
    print("=" * 60)
    print("Direct ClickHouse Test - Simplified 5-Column Schema")
    print("=" * 60)
    
    # Create HTTP client
    base_url = f"http://{CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}"
    auth = (CLICKHOUSE_USER, CLICKHOUSE_PASSWORD) if CLICKHOUSE_PASSWORD else None
    
    async with httpx.AsyncClient(base_url=base_url, auth=auth, timeout=30.0) as client:
        
        print("1. Checking table structure...")
        try:
            desc_query = "DESCRIBE trading_data.ticks FORMAT JSONEachRow"
            response = await client.post("/", params={'query': desc_query})
            if response.status_code == 200:
                print("   ✓ Table structure:")
                for line in response.text.strip().split('\n'):
                    if line.strip():
                        col_info = json.loads(line)
                        print(f"     - {col_info['name']}: {col_info['type']}")
            else:
                print(f"   ✗ Failed to get table structure: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ✗ Error checking table: {e}")
            return False
        
        print("\n2. Testing simplified tick insertion...")
        
        # Create test data for SIMPLIFIED 5-column table
        test_ticks = [
            {
                "timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                "symbol": "EURUSD",
                "bid": 1.0950,
                "ask": 1.0952,
                "broker": "FBS-Demo"
            },
            {
                "timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                "symbol": "GBPUSD",
                "bid": 1.2750,
                "ask": 1.2752,
                "broker": "FBS-Demo"
            },
            {
                "timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                "symbol": "USDJPY",
                "bid": 149.50,
                "ask": 149.52,
                "broker": "FBS-Demo"
            }
        ]
        
        # Convert to JSON lines format
        json_lines = []
        for tick in test_ticks:
            json_lines.append(json.dumps(tick))
        
        insert_data = '\n'.join(json_lines)
        
        # INSERT query
        insert_query = "INSERT INTO trading_data.ticks FORMAT JSONEachRow"
        
        try:
            response = await client.post(
                "/",
                params={'query': insert_query},
                content=insert_data,
                headers={'Content-Type': 'application/octet-stream'}
            )
            
            if response.status_code == 200:
                print(f"   ✓ Successfully inserted {len(test_ticks)} simplified ticks")
                
                # Verify insertion
                print("\n3. Verifying insertion...")
                select_query = "SELECT * FROM trading_data.ticks ORDER BY timestamp DESC LIMIT 3 FORMAT JSONEachRow"
                select_response = await client.post("/", params={'query': select_query})
                
                if select_response.status_code == 200 and select_response.text.strip():
                    print("   ✓ Verification successful:")
                    for line in select_response.text.strip().split('\n'):
                        if line.strip():
                            row_data = json.loads(line)
                            print(f"     - {row_data['symbol']}: {row_data['bid']}/{row_data['ask']} @ {row_data['timestamp']}")
                    return True
                else:
                    print(f"   ! SELECT verification failed: {select_response.status_code}")
                    return False
            else:
                print(f"   ✗ Insertion failed: HTTP {response.status_code}")
                print(f"     Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ✗ Insertion error: {e}")
            return False

async def main():
    """Run simplified insertion test"""
    print("🚀 Starting Direct ClickHouse Simplified Schema Test")
    
    success = await test_simplified_insertion()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 SIMPLIFIED SCHEMA TEST PASSED")
        print("✅ Direct ClickHouse insertion with 5-column table: SUCCESS")
        print("🎯 RESULT: The simplified table schema is working correctly!")
    else:
        print("❌ SIMPLIFIED SCHEMA TEST FAILED")
        print("The issue is likely with the table structure or data format.")
    
    return success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        exit(1)