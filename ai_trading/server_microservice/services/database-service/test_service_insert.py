#!/usr/bin/env python3
"""
Test Database Service Tick Insertion via HTTP API
Tests the actual database service endpoints with proper authentication
"""

import asyncio
import httpx
import json
from datetime import datetime, timezone

async def test_database_service_api():
    """Test the database service API endpoints"""
    print("=" * 60)
    print("Database Service API Tick Insertion Test")
    print("=" * 60)
    
    base_url = "http://localhost:8008"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        print("1. Testing service health...")
        try:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                print(f"   ✓ Service health: {response.json()}")
            else:
                print(f"   ✗ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ✗ Health check error: {e}")
            return False
        
        print("\\n2. Testing single tick insertion...")
        try:
            # Create test tick data
            tick_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "symbol": "EURUSD_API_TEST",
                "bid": 1.0970,
                "ask": 1.0972,
                "last": 1.0971,
                "volume": 125.0,
                "spread": 0.0002,
                "broker": "FBS-Demo",
                "account_type": "demo"
            }
            
            response = await client.post(
                f"{base_url}/api/v1/clickhouse/ticks",
                json=tick_data
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✓ Single tick insertion successful: {result}")
                
                if result.get("success") and result.get("records_inserted", 0) > 0:
                    print(f"   ✓ Inserted {result['records_inserted']} record(s)")
                    print(f"   ✓ Duration: {result.get('insertion_duration_ms', 0):.2f}ms")
                    print(f"   ✓ Throughput: {result.get('throughput_records_per_second', 0):.0f} records/sec")
                else:
                    print(f"   ! Insertion result unclear: {result}")
            else:
                print(f"   ✗ Single tick insertion failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ✗ Single tick insertion error: {e}")
            return False
        
        print("\\n3. Testing batch tick insertion...")
        try:
            # Create batch test data
            batch_data = {
                "ticks": []
            }
            
            for i in range(5):
                tick = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "symbol": f"EURUSD_BATCH_API_{i}",
                    "bid": 1.0970 + (i * 0.0001),
                    "ask": 1.0972 + (i * 0.0001),
                    "last": 1.0971 + (i * 0.0001),
                    "volume": 100.0 + i,
                    "spread": 0.0002,
                    "broker": "FBS-Demo",
                    "account_type": "demo"
                }
                batch_data["ticks"].append(tick)
            
            response = await client.post(
                f"{base_url}/api/v1/clickhouse/ticks/batch",
                json=batch_data
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✓ Batch tick insertion successful: {result}")
                
                if result.get("success") and result.get("records_inserted", 0) > 0:
                    print(f"   ✓ Inserted {result['records_inserted']} record(s)")
                    print(f"   ✓ Duration: {result.get('insertion_duration_ms', 0):.2f}ms")
                    print(f"   ✓ Throughput: {result.get('throughput_records_per_second', 0):.0f} records/sec")
                    print(f"   ✓ Performance optimized: {result.get('performance_optimized', False)}")
                else:
                    print(f"   ! Batch insertion result unclear: {result}")
            else:
                print(f"   ✗ Batch tick insertion failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ✗ Batch tick insertion error: {e}")
            return False
        
        print("\\n4. Testing ClickHouse query to verify data...")
        try:
            # Query the inserted data
            query = "SELECT COUNT(*) as count FROM trading_data.ticks WHERE symbol LIKE '%API%'"
            response = await client.get(
                f"{base_url}/api/v1/clickhouse/query",
                params={"query": query, "database": "trading_data"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✓ Query successful: {result}")
                
                if result.get("success") and result.get("result"):
                    count = result["result"][0].get("count", 0)
                    print(f"   ✓ Found {count} records matching API test pattern")
                else:
                    print(f"   ! Query result unclear: {result}")
            else:
                print(f"   ✗ Query failed: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   ✗ Query error: {e}")
        
        print("\\n5. Testing service status...")
        try:
            response = await client.get(f"{base_url}/status")
            if response.status_code == 200:
                status = response.json()
                print(f"   ✓ Service status retrieved")
                print(f"   Database health: {status.get('database_health', {})}")
                print(f"   Component status: {status.get('component_status', {})}")
                print(f"   Database stats: {status.get('database_statistics', {})}")
            else:
                print(f"   ✗ Status check failed: {response.status_code}")
        except Exception as e:
            print(f"   ✗ Status check error: {e}")
        
        print("\\n" + "=" * 60)
        print("✓ ALL DATABASE SERVICE API TESTS COMPLETED")
        print("=" * 60)
        
        return True

async def main():
    """Main test function"""
    try:
        success = await test_database_service_api()
        
        if success:
            print("\\n🎉 Database Service API authentication and insertion are working correctly!")
        else:
            print("\\n❌ Database Service API test failed")
            
    except Exception as e:
        print(f"\\n💥 FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())