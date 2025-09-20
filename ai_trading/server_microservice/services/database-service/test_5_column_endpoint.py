#!/usr/bin/env python3
"""
Test script to verify the database service endpoints work with 5-column data
"""

import requests
import json
from datetime import datetime

def test_database_service_endpoints():
    """Test database service endpoints with 5-column tick data"""
    
    base_url = "http://localhost:8008"  # Database service port
    
    print("=== Testing Database Service Endpoints (5-Column Fix) ===")
    
    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print(f"  ✓ Health check passed: {response.json()}")
        else:
            print(f"  ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Health check error: {e}")
        print("  (Service may not be running - start with: docker-compose up -d database-service)")
        return False
    
    # Test 2: Schema retrieval
    print("\n2. Testing schema retrieval...")
    try:
        response = requests.get(f"{base_url}/api/v1/schemas/clickhouse", timeout=5)
        if response.status_code == 200:
            schemas = response.json()
            if 'raw_data' in schemas and 'ticks' in schemas['raw_data']:
                print("  ✓ ClickHouse schemas retrieved successfully")
                print(f"    Available tables: {schemas['raw_data']}")
            else:
                print(f"  ❌ Unexpected schema structure: {schemas}")
                return False
        else:
            print(f"  ❌ Schema retrieval failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Schema retrieval error: {e}")
        return False
    
    # Test 3: Insert 5-column tick data
    print("\n3. Testing tick data insertion (5-column)...")
    
    # Sample 5-column tick data that matches actual table structure
    tick_data = [
        {
            "timestamp": datetime.utcnow().isoformat(),
            "symbol": "EURUSD",
            "bid": 1.0850,
            "ask": 1.0852,
            "broker": "test"
        },
        {
            "timestamp": datetime.utcnow().isoformat(),
            "symbol": "GBPUSD", 
            "bid": 1.2650,
            "ask": 1.2652,
            "broker": "test"
        }
    ]
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/clickhouse/ticks",
            json={
                "data": tick_data,
                "broker": "test"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✓ Tick data insertion successful: {result}")
            
            # Verify the response indicates successful insertion
            if result.get("inserted") and result.get("records_count") == 2:
                print("  ✓ Correct number of records inserted")
                return True
            else:
                print(f"  ⚠️  Unexpected insertion result: {result}")
                return False
        else:
            print(f"  ❌ Tick data insertion failed: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"    Error details: {error_detail}")
            except:
                print(f"    Raw response: {response.text}")
            return False
            
    except Exception as e:
        print(f"  ❌ Tick data insertion error: {e}")
        return False

def print_usage_instructions():
    """Print instructions for running the database service"""
    
    print("\n=== Usage Instructions ===")
    print("\nTo test the fixed database service:")
    print("1. Start the database service:")
    print("   cd server_microservice")
    print("   docker-compose up -d database-service")
    print("")
    print("2. Wait for service to initialize (check logs):")
    print("   docker logs -f server_microservice-database-service-1")
    print("")
    print("3. Run this test script:")
    print("   python3 test_5_column_endpoint.py")
    print("")
    print("4. Send test data with 5-column structure:")
    
    sample_curl = """
curl -X POST http://localhost:8008/api/v1/clickhouse/ticks \\
  -H "Content-Type: application/json" \\
  -d '{
    "data": [
      {
        "timestamp": "2024-01-09T15:30:45.123Z",
        "symbol": "EURUSD",
        "bid": 1.0850,
        "ask": 1.0852,
        "broker": "test"
      }
    ],
    "broker": "test"
  }'
"""
    print(sample_curl)

if __name__ == "__main__":
    print("Database Service 5-Column Endpoint Test")
    print("=" * 50)
    
    success = test_database_service_endpoints()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ENDPOINT TESTS PASSED!")
        print("✓ Database service is working with 5-column tick data")
        print("✓ No more validation errors for missing columns")
        print("✓ Service ready for production use with actual ClickHouse table")
    else:
        print("💥 ENDPOINT TESTS FAILED")
        print("❌ Issues found with database service")
    
    print_usage_instructions()
    
    exit(0 if success else 1)