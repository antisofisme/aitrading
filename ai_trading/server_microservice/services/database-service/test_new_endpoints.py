#!/usr/bin/env python3
"""
Test script for the new database service endpoints
Tests the 3 new ClickHouse data insertion endpoints
"""

import asyncio
import json
import aiohttp
from datetime import datetime

# Test data
SINGLE_TICK = {
    "timestamp": datetime.utcnow().isoformat(),
    "symbol": "EURUSD",
    "bid": 1.1000,
    "ask": 1.1002,
    "spread": 0.0002,
    "volume": 1.0,
    "broker": "FBS-Demo",
    "account_type": "demo"
}

BATCH_TICKS = {
    "ticks": [
        {
            "timestamp": datetime.utcnow().isoformat(),
            "symbol": "EURUSD",
            "bid": 1.1000,
            "ask": 1.1002,
            "volume": 1.0
        },
        {
            "timestamp": datetime.utcnow().isoformat(),
            "symbol": "GBPUSD",
            "bid": 1.2500,
            "ask": 1.2502,
            "volume": 1.5
        }
    ],
    "batch_size": 2
}

ACCOUNT_INFO = {
    "login": 1016,
    "balance": 10000.0,
    "equity": 10000.0,
    "margin": 0.0,
    "currency": "USD",
    "server": "FBS-Real",
    "broker": "FBS-Demo"
}

BASE_URL = "http://localhost:8008"

async def test_endpoint(session, endpoint, data, method="POST"):
    """Test a specific endpoint"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        print(f"\n🧪 Testing {method} {endpoint}")
        print(f"📤 Data: {json.dumps(data, indent=2)}")
        
        if method == "POST":
            async with session.post(url, json=data) as response:
                response_text = await response.text()
                print(f"📊 Status: {response.status}")
                print(f"📥 Response: {response_text}")
                return response.status, response_text
        else:
            async with session.get(url) as response:
                response_text = await response.text()
                print(f"📊 Status: {response.status}")
                print(f"📥 Response: {response_text}")
                return response.status, response_text
                
    except Exception as e:
        print(f"❌ Error testing {endpoint}: {e}")
        return 500, str(e)

async def test_service_health():
    """Test service health first"""
    async with aiohttp.ClientSession() as session:
        print("🏥 Testing service health...")
        
        # Test basic health
        status, response = await test_endpoint(session, "/health", {}, "GET")
        if status != 200:
            print("❌ Service health check failed!")
            return False
            
        # Test detailed status
        status, response = await test_endpoint(session, "/status", {}, "GET")
        print(f"✅ Service is healthy and running")
        return True

async def test_new_endpoints():
    """Test all new endpoints"""
    print("🚀 Testing New Database Service Endpoints")
    print("=" * 50)
    
    # Check service health first
    if not await test_service_health():
        print("❌ Service is not healthy, aborting tests")
        return
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Single tick insertion
        print("\n" + "=" * 50)
        print("📍 Test 1: Single Tick Insertion")
        status, response = await test_endpoint(
            session, 
            "/api/v1/clickhouse/ticks", 
            SINGLE_TICK
        )
        
        if status == 200:
            print("✅ Single tick insertion: PASSED")
        else:
            print("❌ Single tick insertion: FAILED")
        
        # Test 2: Batch tick insertion
        print("\n" + "=" * 50)
        print("📊 Test 2: Batch Tick Insertion")
        status, response = await test_endpoint(
            session,
            "/api/v1/clickhouse/ticks/batch",
            BATCH_TICKS
        )
        
        if status == 200:
            print("✅ Batch tick insertion: PASSED")
        else:
            print("❌ Batch tick insertion: FAILED")
        
        # Test 3: Account info insertion
        print("\n" + "=" * 50)
        print("💰 Test 3: Account Info Insertion")
        status, response = await test_endpoint(
            session,
            "/api/v1/clickhouse/account_info",
            ACCOUNT_INFO
        )
        
        if status == 200:
            print("✅ Account info insertion: PASSED")
        else:
            print("❌ Account info insertion: FAILED")
        
        # Test 4: Check service endpoints
        print("\n" + "=" * 50)
        print("🔍 Test 4: Service Discovery")
        status, response = await test_endpoint(session, "/", {}, "GET")
        
        if status == 200:
            try:
                service_info = json.loads(response)
                endpoints = service_info.get("endpoints", {})
                
                required_endpoints = [
                    "clickhouse_ticks_single",
                    "clickhouse_ticks_batch", 
                    "clickhouse_account_info"
                ]
                
                all_found = all(endpoint in endpoints for endpoint in required_endpoints)
                if all_found:
                    print("✅ All new endpoints discovered in service info: PASSED")
                else:
                    print("❌ Some endpoints missing from service info: FAILED")
                    
            except json.JSONDecodeError:
                print("❌ Service info response not valid JSON: FAILED")
        else:
            print("❌ Service discovery: FAILED")

if __name__ == "__main__":
    print("🗄️ Database Service Endpoint Test Suite")
    print("Testing the 3 new ClickHouse data insertion endpoints")
    print("Service URL:", BASE_URL)
    print("=" * 60)
    
    try:
        asyncio.run(test_new_endpoints())
        print("\n" + "=" * 60)
        print("🎯 Testing completed!")
        print("\nNote: Make sure the database service is running on port 8008")
        print("Start it with: python main.py")
        
    except KeyboardInterrupt:
        print("\n❌ Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Testing failed with error: {e}")