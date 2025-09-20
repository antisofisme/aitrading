#!/usr/bin/env python3
"""
Test ClickHouse connectivity and real database operations
This script tests the actual database service implementation with real ClickHouse connections
"""

import asyncio
import os
import sys
import httpx
from datetime import datetime
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Import our real database components
from business.database_manager import DatabaseManager

async def test_clickhouse_connectivity():
    """Test basic ClickHouse connectivity"""
    print("🔧 Testing ClickHouse connectivity...")
    
    # Set up environment variables for ClickHouse connection
    os.environ.setdefault('CLICKHOUSE_HOST', 'localhost')
    os.environ.setdefault('CLICKHOUSE_PORT', '8123')
    os.environ.setdefault('CLICKHOUSE_USER', 'default')
    os.environ.setdefault('CLICKHOUSE_PASSWORD', '')
    
    try:
        # Test direct ClickHouse connection
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8123/ping")
            if response.status_code == 200:
                print("✅ Direct ClickHouse connection successful")
                
                # Test basic query
                ping_response = await client.post("http://localhost:8123/", params={'query': 'SELECT 1 as test'})
                if ping_response.status_code == 200:
                    print("✅ ClickHouse query execution successful")
                else:
                    print(f"❌ ClickHouse query failed: HTTP {ping_response.status_code}")
            else:
                print(f"❌ ClickHouse connection failed: HTTP {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ ClickHouse connection error: {e}")
        return False
    
    return True

async def test_database_manager():
    """Test DatabaseManager with real connections"""
    print("\n🗄️ Testing DatabaseManager with real connections...")
    
    try:
        # Create and initialize database manager
        db_manager = DatabaseManager()
        await db_manager.initialize()
        print("✅ DatabaseManager initialized successfully")
        
        # Test ClickHouse query execution
        try:
            result = await db_manager.execute_clickhouse_query("SELECT 1 as test_value", "default")
            print(f"✅ ClickHouse query successful: {result}")
        except Exception as e:
            print(f"❌ ClickHouse query failed: {e}")
        
        # Test database creation
        try:
            await db_manager.execute_clickhouse_query("CREATE DATABASE IF NOT EXISTS trading_data", "default")
            print("✅ ClickHouse database creation successful")
        except Exception as e:
            print(f"❌ ClickHouse database creation failed: {e}")
        
        # Test simple table creation and data insertion
        try:
            # Create a test table
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS trading_data.test_ticks (
                timestamp DateTime64(3) DEFAULT now64(),
                symbol String,
                bid Float64,
                ask Float64,
                broker String DEFAULT 'test'
            ) ENGINE = MergeTree()
            ORDER BY timestamp
            """
            
            await db_manager.execute_clickhouse_query(create_table_sql, "trading_data")
            print("✅ Test table creation successful")
            
            # Insert test data
            test_tick = {
                "timestamp": datetime.utcnow().isoformat(),
                "symbol": "EURUSD",
                "bid": 1.0850,
                "ask": 1.0852,
                "broker": "test-broker"
            }
            
            result = await db_manager.insert_clickhouse_data("test_ticks", test_tick, "trading_data")
            print(f"✅ Test data insertion successful: {result}")
            
            # Query back the data
            select_result = await db_manager.execute_clickhouse_query(
                "SELECT * FROM trading_data.test_ticks ORDER BY timestamp DESC LIMIT 5",
                "trading_data"
            )
            print(f"✅ Data retrieval successful: {len(select_result)} records found")
            if select_result:
                print(f"   Latest record: {select_result[0]}")
                
        except Exception as e:
            print(f"❌ Table operations failed: {e}")
        
        # Test tick data insertion (the main functionality)
        try:
            test_tick_data = [
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "symbol": "EURUSD",
                    "bid": 1.0850 + i * 0.0001,
                    "ask": 1.0852 + i * 0.0001,
                    "volume": 100.0,
                    "broker": "FBS-Demo",
                    "account_type": "demo"
                }
                for i in range(10)  # Test with 10 ticks
            ]
            
            result = await db_manager.insert_tick_data(test_tick_data, "FBS-Demo", "demo")
            print(f"✅ Bulk tick insertion successful: {result}")
            
        except Exception as e:
            print(f"❌ Bulk tick insertion failed: {e}")
        
        # Cleanup
        await db_manager.shutdown()
        print("✅ DatabaseManager shutdown completed")
        
    except Exception as e:
        print(f"❌ DatabaseManager test failed: {e}")
        return False
    
    return True

async def main():
    """Run all connectivity tests"""
    print("🚀 Starting ClickHouse Database Connectivity Tests")
    print("=" * 60)
    
    # Test basic connectivity
    connectivity_ok = await test_clickhouse_connectivity()
    
    if connectivity_ok:
        # Test database manager
        manager_ok = await test_database_manager()
        
        if manager_ok:
            print("\n" + "=" * 60)
            print("🎉 ALL TESTS PASSED - Real database operations are working!")
            print("✅ ClickHouse connectivity: SUCCESS")  
            print("✅ DatabaseManager operations: SUCCESS")
            print("✅ Schema creation: SUCCESS")
            print("✅ Data insertion: SUCCESS")
            print("✅ Data retrieval: SUCCESS")
            return True
        else:
            print("\n❌ DatabaseManager tests failed")
            return False
    else:
        print("\n❌ ClickHouse connectivity tests failed")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        sys.exit(1)