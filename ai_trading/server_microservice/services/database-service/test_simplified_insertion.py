#!/usr/bin/env python3
"""
Test Simplified ClickHouse Insertion
Tests that the simplified 5-column table schema works with the fixed database service
"""

import asyncio
import httpx
import json
from datetime import datetime
import os
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Import database manager
from business.database_manager import DatabaseManager

# ClickHouse connection settings
CLICKHOUSE_HOST = os.getenv('CLICKHOUSE_HOST', 'localhost')
CLICKHOUSE_PORT = int(os.getenv('CLICKHOUSE_PORT', '8123'))
CLICKHOUSE_USER = os.getenv('CLICKHOUSE_USER', 'default')
CLICKHOUSE_PASSWORD = os.getenv('CLICKHOUSE_PASSWORD', 'clickhouse_password_2024')

async def test_direct_clickhouse_insertion():
    """Test direct ClickHouse insertion with simplified schema"""
    print("=" * 60)
    print("Testing Direct ClickHouse Insertion (Simplified Schema)")
    print("=" * 60)
    
    # Create HTTP client
    base_url = f"http://{CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}"
    auth = (CLICKHOUSE_USER, CLICKHOUSE_PASSWORD) if CLICKHOUSE_PASSWORD else None
    
    async with httpx.AsyncClient(base_url=base_url, auth=auth, timeout=30.0) as client:
        
        print("1. Testing simple tick insertion with 5 columns...")
        
        # Simplified test tick data (only 5 columns)
        test_tick = {
            "timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            "symbol": "EURUSD",
            "bid": 1.0950,
            "ask": 1.0952,
            "broker": "FBS-Demo"
        }
        
        # Convert to JSON for ClickHouse
        json_data = json.dumps(test_tick)
        
        # INSERT query for simplified table
        insert_query = "INSERT INTO trading_data.ticks FORMAT JSONEachRow"
        
        try:
            response = await client.post(
                "/",
                params={'query': insert_query},
                content=json_data,
                headers={'Content-Type': 'application/octet-stream'}
            )
            
            if response.status_code == 200:
                print("   ✓ Direct insertion successful")
                
                # Verify with SELECT
                select_query = "SELECT * FROM trading_data.ticks ORDER BY timestamp DESC LIMIT 1 FORMAT JSONEachRow"
                select_response = await client.post("/", params={'query': select_query})
                
                if select_response.status_code == 200 and select_response.text.strip():
                    inserted_data = json.loads(select_response.text.strip())
                    print(f"   ✓ Verified: {inserted_data}")
                    return True
                else:
                    print(f"   ! SELECT verification failed: {select_response.status_code}")
            else:
                print(f"   ✗ Direct insertion failed: {response.status_code}")
                print(f"     Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ✗ Direct insertion error: {e}")
            return False

async def test_database_service_insertion():
    """Test database service insertion with simplified schema"""
    print("\n2. Testing Database Service Insertion...")
    
    try:
        # Initialize database manager
        db_manager = DatabaseManager()
        await db_manager.initialize()
        print("   ✓ Database manager initialized")
        
        # Test simplified tick data insertion
        simplified_tick_data = [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "symbol": "GBPUSD",
                "bid": 1.2750,
                "ask": 1.2752,
                "broker": "FBS-Demo"
            },
            {
                "timestamp": datetime.utcnow().isoformat(),
                "symbol": "USDJPY",
                "bid": 149.50,
                "ask": 149.52,
                "broker": "FBS-Demo"
            }
        ]
        
        # Insert using database service
        result = await db_manager.insert_tick_data(simplified_tick_data, "FBS-Demo", "demo")
        
        if result.get("inserted"):
            print(f"   ✓ Database service insertion successful: {result['records_count']} ticks")
            print(f"     Throughput: {result.get('throughput_ticks_per_second', 0):.1f} ticks/sec")
            
            # Verify data exists
            recent_ticks = await db_manager.get_recent_ticks("GBPUSD", "FBS-Demo", 5)
            if recent_ticks:
                print(f"   ✓ Verification successful: {len(recent_ticks)} recent ticks found")
                return True
            else:
                print("   ! No recent ticks found in verification")
                return False
        else:
            print(f"   ✗ Database service insertion failed: {result}")
            return False
            
    except Exception as e:
        print(f"   ✗ Database service test error: {e}")
        return False
    finally:
        if 'db_manager' in locals():
            await db_manager.shutdown()

async def test_client_format_simulation():
    """Test with client-side data format simulation"""
    print("\n3. Testing Client Data Format Simulation...")
    
    try:
        # Simulate data from WebSocket client (uses 'time' not 'timestamp')
        client_tick_data = {
            "symbol": "EURJPY",
            "bid": 161.25,
            "ask": 161.27,
            "spread": 0.02,
            "time": datetime.utcnow().isoformat(),  # Client sends 'time'
            "volume": 100.0,
            "last": 161.26,
            "source": "mt5_bridge",
            "broker": "FBS-Demo"
        }
        
        # Initialize database manager
        db_manager = DatabaseManager()
        await db_manager.initialize()
        
        # Insert single tick (will be processed by _process_tick_data method)
        result = await db_manager.insert_tick_data(client_tick_data, "FBS-Demo", "demo")
        
        if result.get("inserted"):
            print(f"   ✓ Client format insertion successful: {result['records_count']} ticks")
            return True
        else:
            print(f"   ✗ Client format insertion failed: {result}")
            return False
            
    except Exception as e:
        print(f"   ✗ Client format test error: {e}")
        return False
    finally:
        if 'db_manager' in locals():
            await db_manager.shutdown()

async def main():
    """Run all simplified insertion tests"""
    print("🚀 Starting Simplified ClickHouse Insertion Tests")
    
    results = []
    
    # Test 1: Direct ClickHouse insertion
    results.append(await test_direct_clickhouse_insertion())
    
    # Test 2: Database service insertion
    results.append(await test_database_service_insertion())
    
    # Test 3: Client format simulation
    results.append(await test_client_format_simulation())
    
    # Summary
    print("\n" + "=" * 60)
    passed_tests = sum(results)
    total_tests = len(results)
    
    if passed_tests == total_tests:
        print(f"🎉 ALL TESTS PASSED ({passed_tests}/{total_tests})")
        print("✅ Direct ClickHouse insertion: SUCCESS")
        print("✅ Database service insertion: SUCCESS")
        print("✅ Client format compatibility: SUCCESS")
        print("\n🎯 RESULT: Simplified 5-column schema is working correctly!")
        return True
    else:
        print(f"❌ SOME TESTS FAILED ({passed_tests}/{total_tests})")
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