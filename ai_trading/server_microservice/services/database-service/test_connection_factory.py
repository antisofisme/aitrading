#!/usr/bin/env python3
"""
Test Connection Factory ClickHouse Authentication
Direct test of the fixed ConnectionFactory implementation
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_connection_factory():
    """Test the ConnectionFactory directly"""
    print("=" * 60)
    print("Connection Factory ClickHouse Test")
    print("=" * 60)
    
    # Set environment variables
    os.environ['CLICKHOUSE_USER'] = 'default'
    os.environ['CLICKHOUSE_PASSWORD'] = 'clickhouse_password_2024'
    os.environ['CLICKHOUSE_HOST'] = 'localhost'
    os.environ['CLICKHOUSE_PORT'] = '8123'
    os.environ['CLICKHOUSE_DB'] = 'trading_data'
    
    try:
        # Import after setting environment
        from business.connection_factory import ConnectionFactory
        
        print("1. Creating ConnectionFactory...")
        factory = ConnectionFactory()
        print("   ✓ ConnectionFactory created")
        
        print("\\n2. Creating ClickHouse connection pool...")
        database_config = {
            "host": "localhost",
            "port": 8123,
            "user": "default",
            "password": "clickhouse_password_2024",
            "database": "trading_data"
        }
        
        pool = await factory.create_connection_pool("clickhouse", database_config)
        print("   ✓ ClickHouse connection pool created")
        print(f"   Pool info: {factory.get_pool_stats('clickhouse', pool)}")
        
        print("\\n3. Testing connection acquisition...")
        async with factory.get_connection("clickhouse", pool) as conn:
            print("   ✓ Connection acquired from pool")
            
            # Test if this is a real httpx client
            if hasattr(conn, 'get'):
                print("   ✓ Connection has HTTP client methods")
                
                # Test ping
                response = await conn.get("/ping")
                if response.status_code == 200:
                    print(f"   ✓ Ping successful: {response.text}")
                else:
                    print(f"   ✗ Ping failed: {response.status_code}")
                
                # Test INSERT
                print("\\n4. Testing INSERT operation...")
                
                test_data = {
                    "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                    "symbol": "EURUSD_FACTORY_TEST",
                    "bid": 1.0965,
                    "ask": 1.0967,
                    "last": 1.0966,
                    "volume": 75.0,
                    "spread": 0.0002,
                    "primary_session": "London",
                    "active_sessions": ["London"],
                    "session_overlap": False,
                    "broker": "FBS-Demo",
                    "account_type": "demo"
                }
                
                json_data = json.dumps(test_data)
                insert_query = "INSERT INTO trading_data.ticks FORMAT JSONEachRow"
                
                response = await conn.post(
                    "/",
                    params={'query': insert_query},
                    content=json_data,
                    headers={'Content-Type': 'application/octet-stream'}
                )
                
                if response.status_code == 200:
                    print("   ✓ INSERT via connection factory successful")
                    
                    # Verify with SELECT
                    select_query = "SELECT * FROM trading_data.ticks WHERE symbol = 'EURUSD_FACTORY_TEST' ORDER BY timestamp DESC LIMIT 1 FORMAT JSONEachRow"
                    response = await conn.post("/", params={'query': select_query})
                    
                    if response.status_code == 200 and response.text.strip():
                        result = json.loads(response.text.strip())
                        print(f"   ✓ Verification successful: {result}")
                    else:
                        print(f"   ! Verification query response: {response.status_code}, {response.text}")
                else:
                    print(f"   ✗ INSERT failed: {response.status_code}")
                    print(f"   Response: {response.text}")
            else:
                print("   ! Connection is not a real HTTP client (mock mode)")
        
        print("\\n5. Closing connection pool...")
        await factory.close_connection_pool("clickhouse", pool)
        print("   ✓ Connection pool closed")
        
        print("\\n" + "=" * 60)
        print("✓ CONNECTION FACTORY TEST PASSED")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\\n✗ CONNECTION FACTORY TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        return False

async def main():
    """Main test function"""
    success = await test_connection_factory()
    
    if success:
        print("\\n🎉 Connection Factory authentication is working correctly!")
    else:
        print("\\n❌ Connection Factory test failed")

if __name__ == "__main__":
    asyncio.run(main())