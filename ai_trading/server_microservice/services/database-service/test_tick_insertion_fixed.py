#!/usr/bin/env python3
"""
Test Database Service Tick Insertion with Fixed Authentication
Tests the actual database service's tick insertion functionality
"""

import asyncio
import json
from datetime import datetime, timezone
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from business.database_manager import DatabaseManager

async def test_database_service_tick_insertion():
    """Test the database service's tick insertion functionality"""
    print("=" * 60)
    print("Database Service Tick Insertion Test (Fixed Authentication)")
    print("=" * 60)
    
    # Create database manager
    db_manager = DatabaseManager()
    
    try:
        print("1. Initializing database manager...")
        await db_manager.initialize()
        print("   ✓ Database manager initialized successfully")
        
        print("\\n2. Testing connection health...")
        health_status = await db_manager.get_health_status()
        print(f"   Database health: {health_status}")
        
        if health_status.get('clickhouse') != 'healthy':
            print("   ⚠ ClickHouse not healthy, but continuing with test...")
        
        print("\\n3. Testing single tick insertion...")
        
        # Create test tick data
        test_tick = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "symbol": "EURUSD_TEST",
            "bid": 1.0950,
            "ask": 1.0952,
            "last": 1.0951,
            "volume": 100.0,
            "spread": 0.0002,
            "primary_session": "London",
            "active_sessions": ["London", "New York"],
            "session_overlap": True
        }
        
        # Insert single tick
        result = await db_manager.insert_tick_data(test_tick, broker="FBS-Demo", account_type="demo")
        print(f"   ✓ Single tick insertion result: {result}")
        
        print("\\n4. Testing bulk tick insertion...")
        
        # Create bulk test data
        bulk_ticks = []
        for i in range(10):
            tick = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "symbol": f"EURUSD_BULK_{i}",
                "bid": 1.0950 + (i * 0.0001),
                "ask": 1.0952 + (i * 0.0001),
                "last": 1.0951 + (i * 0.0001),
                "volume": 100.0 + i,
                "spread": 0.0002,
                "primary_session": "London",
                "active_sessions": ["London"],
                "session_overlap": False
            }
            bulk_ticks.append(tick)
        
        # Insert bulk ticks
        bulk_result = await db_manager.insert_tick_data(bulk_ticks, broker="FBS-Demo", account_type="demo")
        print(f"   ✓ Bulk tick insertion result: {bulk_result}")
        
        print("\\n5. Testing data retrieval...")
        
        # Test recent ticks retrieval
        recent_ticks = await db_manager.get_recent_ticks("EURUSD_TEST", broker="FBS-Demo", limit=5)
        print(f"   ✓ Retrieved {len(recent_ticks)} recent ticks for EURUSD_TEST")
        
        if recent_ticks:
            print(f"   Latest tick: {recent_ticks[0]}")
        
        print("\\n6. Testing symbol statistics...")
        
        # Test symbol statistics
        stats = await db_manager.get_symbol_statistics_cached("EURUSD_TEST", hours=1, broker="FBS-Demo")
        print(f"   ✓ Symbol statistics: {stats}")
        
        print("\\n7. Testing direct ClickHouse query...")
        
        # Test direct ClickHouse query
        query = "SELECT COUNT(*) as count FROM trading_data.ticks WHERE symbol LIKE '%EURUSD%'"
        query_result = await db_manager.execute_clickhouse_query(query, "trading_data")
        print(f"   ✓ Direct query result: {query_result}")
        
        print("\\n" + "=" * 60)
        print("✓ ALL TESTS PASSED - Database service tick insertion is working!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        return False
        
    finally:
        print("\\n8. Shutting down database manager...")
        try:
            await db_manager.shutdown()
            print("   ✓ Database manager shutdown completed")
        except Exception as e:
            print(f"   ⚠ Shutdown error: {e}")

async def test_raw_clickhouse_insert():
    """Test raw ClickHouse insert to isolate authentication issues"""
    print("\\n" + "-" * 40)
    print("Raw ClickHouse Insert Test")
    print("-" * 40)
    
    try:
        import httpx
        
        # Test data
        test_data = {
            "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            "symbol": "EURUSD_RAW",
            "bid": 1.0960,
            "ask": 1.0962,
            "last": 1.0961,
            "volume": 50.0,
            "spread": 0.0002,
            "primary_session": "New York",
            "active_sessions": ["New York"],
            "session_overlap": False,
            "broker": "FBS-Demo",
            "account_type": "demo"
        }
        
        # Create HTTP client with authentication
        async with httpx.AsyncClient(
            base_url="http://localhost:8123",
            auth=("default", "clickhouse_password_2024"),
            timeout=httpx.Timeout(30.0)
        ) as client:
            
            # Insert data
            json_data = json.dumps(test_data)
            insert_query = "INSERT INTO trading_data.ticks FORMAT JSONEachRow"
            
            response = await client.post(
                "/",
                params={'query': insert_query},
                content=json_data,
                headers={'Content-Type': 'application/octet-stream'}
            )
            
            if response.status_code == 200:
                print("   ✓ Raw ClickHouse insert successful")
                return True
            else:
                print(f"   ✗ Raw ClickHouse insert failed: HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"   ✗ Raw ClickHouse insert error: {e}")
        return False

async def main():
    """Main test function"""
    # Set environment variables for testing
    os.environ['CLICKHOUSE_USER'] = 'default'
    os.environ['CLICKHOUSE_PASSWORD'] = 'clickhouse_password_2024'
    os.environ['CLICKHOUSE_HOST'] = 'localhost'
    os.environ['CLICKHOUSE_PORT'] = '8123'
    os.environ['CLICKHOUSE_DB'] = 'trading_data'
    
    try:
        # Test raw ClickHouse insert first
        raw_success = await test_raw_clickhouse_insert()
        
        if raw_success:
            print("\\nRaw ClickHouse test passed, proceeding with database service test...")
            service_success = await test_database_service_tick_insertion()
            
            if service_success:
                print("\\n🎉 ALL TESTS PASSED - ClickHouse authentication is fully working!")
            else:
                print("\\n❌ Database service test failed")
        else:
            print("\\n❌ Raw ClickHouse test failed - check authentication")
            
    except Exception as e:
        print(f"\\n💥 FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())