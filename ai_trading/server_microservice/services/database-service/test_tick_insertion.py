#!/usr/bin/env python3
"""
Test script for ClickHouse tick data insertion
Tests the complete flow from data formatting to database insertion
"""

import asyncio
import json
import httpx
from datetime import datetime, timezone
from typing import Dict, Any, List

# Test data that mimics MT5 tick data
SAMPLE_TICK_DATA = [
    {
        "symbol": "EURUSD",
        "timestamp": "2025-01-09T12:00:00.123Z",
        "bid": 1.04125,
        "ask": 1.04128,
        "last": 1.04127,
        "volume": 1000.0,
        "session": "London"
    },
    {
        "symbol": "GBPUSD", 
        "timestamp": "2025-01-09T12:00:01.456Z",
        "bid": 1.24567,
        "ask": 1.24571,
        "last": 1.24569,
        "volume": 1500.0,
        "session": "London"
    },
    {
        "symbol": "USDJPY",
        "timestamp": "2025-01-09T12:00:02.789Z", 
        "bid": 158.123,
        "ask": 158.127,
        "last": 158.125,
        "volume": 2000.0,
        "session": "London"
    }
]

async def test_database_service_health():
    """Test if the database service is running and healthy"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8008/health", timeout=5.0)
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Database service is healthy: {health_data}")
                return True
            else:
                print(f"❌ Database service health check failed: HTTP {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Cannot connect to database service: {e}")
        return False

async def test_clickhouse_schemas():
    """Test ClickHouse schema retrieval"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8008/api/v1/schemas/clickhouse/ticks", timeout=10.0)
            if response.status_code == 200:
                schema_data = response.json()
                print(f"✅ ClickHouse ticks table schema available:")
                print(f"   Database: {schema_data.get('database_type')}")
                print(f"   Table: {schema_data.get('table_name')}")
                return True
            else:
                print(f"❌ Schema retrieval failed: HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Schema test failed: {e}")
        return False

async def test_single_tick_insertion():
    """Test inserting a single tick"""
    try:
        single_tick = SAMPLE_TICK_DATA[0]
        
        request_data = {
            "tick_data": single_tick,
            "broker": "FBS-Demo", 
            "account_type": "demo"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8008/api/v1/database/clickhouse/ticks",
                json=request_data,
                timeout=15.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Single tick insertion successful:")
                print(f"   Records inserted: {result.get('records_inserted')}")
                print(f"   Duration: {result.get('query_duration_ms')}ms")
                return True
            else:
                print(f"❌ Single tick insertion failed: HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Single tick insertion test failed: {e}")
        return False

async def test_batch_tick_insertion():
    """Test inserting multiple ticks in batch"""
    try:
        request_data = {
            "tick_data": SAMPLE_TICK_DATA,
            "broker": "FBS-Demo",
            "account_type": "demo"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8008/api/v1/database/clickhouse/ticks",
                json=request_data,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Batch tick insertion successful:")
                print(f"   Records inserted: {result.get('records_inserted')}")
                print(f"   Duration: {result.get('query_duration_ms')}ms")
                print(f"   Throughput: {result.get('records_inserted', 0) / (result.get('query_duration_ms', 1) / 1000):.0f} ticks/sec")
                return True
            else:
                print(f"❌ Batch tick insertion failed: HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Batch tick insertion test failed: {e}")
        return False

async def test_tick_retrieval():
    """Test retrieving recent ticks"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://localhost:8008/api/v1/database/clickhouse/ticks/recent?symbol=EURUSD&broker=FBS-Demo&limit=10",
                timeout=10.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Tick retrieval successful:")
                print(f"   Ticks found: {result.get('ticks_count')}")
                print(f"   Duration: {result.get('query_duration_ms')}ms")
                if result.get('ticks'):
                    latest_tick = result['ticks'][0] if result['ticks'] else {}
                    print(f"   Latest tick: {latest_tick.get('symbol')} @ {latest_tick.get('timestamp')}")
                return True
            else:
                print(f"❌ Tick retrieval failed: HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Tick retrieval test failed: {e}")
        return False

async def test_direct_clickhouse_query():
    """Test direct ClickHouse query execution"""
    try:
        query = "SELECT COUNT(*) as total_ticks, symbol, MAX(timestamp) as latest FROM trading_data.ticks WHERE broker = 'FBS-Demo' GROUP BY symbol ORDER BY total_ticks DESC"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://localhost:8008/api/v1/database/clickhouse/query?query={query}&database=trading_data",
                timeout=15.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Direct ClickHouse query successful:")
                print(f"   Records returned: {result.get('records_count')}")
                print(f"   Duration: {result.get('query_duration_ms')}ms")
                if result.get('result'):
                    for row in result['result'][:3]:  # Show first 3 rows
                        print(f"   {row}")
                return True
            else:
                print(f"❌ Direct query failed: HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Direct query test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting ClickHouse Tick Data Insertion Tests")
    print("=" * 60)
    
    tests = [
        ("Database Service Health", test_database_service_health),
        ("ClickHouse Schema Retrieval", test_clickhouse_schemas),
        ("Single Tick Insertion", test_single_tick_insertion),
        ("Batch Tick Insertion", test_batch_tick_insertion),
        ("Tick Data Retrieval", test_tick_retrieval),
        ("Direct ClickHouse Query", test_direct_clickhouse_query)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📝 Running: {test_name}")
        print("-" * 40)
        
        try:
            success = await test_func()
            if success:
                passed += 1
                print(f"   Status: PASSED ✅")
            else:
                failed += 1
                print(f"   Status: FAILED ❌")
        except Exception as e:
            failed += 1
            print(f"   Status: ERROR ❌ - {e}")
        
        await asyncio.sleep(1)  # Brief pause between tests
    
    print("\n" + "=" * 60)
    print(f"🏁 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! ClickHouse tick insertion is working correctly.")
    else:
        print(f"⚠️  {failed} test(s) failed. Check the logs above for details.")
    
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)