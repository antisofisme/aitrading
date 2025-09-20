#!/usr/bin/env python3
"""
ClickHouse Authentication Test Script
Tests ClickHouse connectivity with the correct credentials from docker-compose.yml
"""

import asyncio
import httpx
import os
import json
from datetime import datetime

# ClickHouse credentials from docker-compose.yml
CLICKHOUSE_HOST = os.getenv('CLICKHOUSE_HOST', 'localhost')
CLICKHOUSE_PORT = int(os.getenv('CLICKHOUSE_PORT', '8123'))
CLICKHOUSE_USER = os.getenv('CLICKHOUSE_USER', 'default')
CLICKHOUSE_PASSWORD = os.getenv('CLICKHOUSE_PASSWORD', 'clickhouse_password_2024')

async def test_clickhouse_connection():
    """Test ClickHouse connection and authentication"""
    print("=" * 60)
    print("ClickHouse Authentication Test")
    print("=" * 60)
    
    # Display configuration
    print(f"Host: {CLICKHOUSE_HOST}")
    print(f"Port: {CLICKHOUSE_PORT}")
    print(f"User: {CLICKHOUSE_USER}")
    print(f"Password: {'***' if CLICKHOUSE_PASSWORD else 'None'}")
    print("-" * 60)
    
    # Create HTTP client with authentication
    base_url = f"http://{CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}"
    auth = (CLICKHOUSE_USER, CLICKHOUSE_PASSWORD) if CLICKHOUSE_PASSWORD else None
    
    async with httpx.AsyncClient(
        base_url=base_url,
        auth=auth,
        timeout=httpx.Timeout(30.0)
    ) as client:
        
        print("1. Testing /ping endpoint...")
        try:
            response = await client.get("/ping")
            if response.status_code == 200:
                print(f"   ✓ PING successful: {response.text}")
            else:
                print(f"   ✗ PING failed: HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"   ✗ PING error: {e}")
            return False
        
        print("\n2. Testing database existence...")
        try:
            query = "SHOW DATABASES"
            response = await client.post("/", params={'query': query})
            if response.status_code == 200:
                databases = response.text.strip().split('\\n')
                print(f"   ✓ Available databases: {databases}")
                if 'trading_data' in databases:
                    print("   ✓ trading_data database exists")
                else:
                    print("   ! trading_data database not found, creating...")
                    await create_database(client)
            else:
                print(f"   ✗ SHOW DATABASES failed: HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"   ✗ SHOW DATABASES error: {e}")
            return False
        
        print("\\n3. Testing table existence...")
        try:
            query = "SHOW TABLES FROM trading_data"
            response = await client.post("/", params={'query': query})
            if response.status_code == 200:
                tables = response.text.strip().split('\\n') if response.text.strip() else []
                print(f"   ✓ Available tables in trading_data: {tables}")
                if 'ticks' in tables:
                    print("   ✓ ticks table exists")
                else:
                    print("   ! ticks table not found, creating...")
                    await create_ticks_table(client)
            else:
                print(f"   ✗ SHOW TABLES failed: HTTP {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   ✗ SHOW TABLES error: {e}")
        
        print("\\n4. Testing INSERT operation...")
        try:
            # Test data for insertion
            test_tick = {
                "timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                "symbol": "EURUSD",
                "bid": 1.0950,
                "ask": 1.0952,
                "last": 1.0951,
                "volume": 100.0,
                "spread": 0.0002,
                "primary_session": "London",
                "active_sessions": ["London", "New York"],
                "session_overlap": True,
                "broker": "FBS-Demo",
                "account_type": "demo"
            }
            
            # Convert to JSON for ClickHouse
            json_data = json.dumps(test_tick)
            
            # INSERT query
            insert_query = "INSERT INTO trading_data.ticks FORMAT JSONEachRow"
            
            response = await client.post(
                "/",
                params={'query': insert_query},
                content=json_data,
                headers={'Content-Type': 'application/octet-stream'}
            )
            
            if response.status_code == 200:
                print("   ✓ INSERT successful")
                
                # Test SELECT to verify
                select_query = "SELECT * FROM trading_data.ticks ORDER BY timestamp DESC LIMIT 1 FORMAT JSONEachRow"
                response = await client.post("/", params={'query': select_query})
                
                if response.status_code == 200 and response.text.strip():
                    inserted_data = json.loads(response.text.strip())
                    print(f"   ✓ Verified insertion: {inserted_data}")
                    return True
                else:
                    print(f"   ! SELECT verification failed: {response.status_code}")
            else:
                print(f"   ✗ INSERT failed: HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ✗ INSERT error: {e}")
            return False

async def create_database(client):
    """Create trading_data database"""
    try:
        query = "CREATE DATABASE IF NOT EXISTS trading_data"
        response = await client.post("/", params={'query': query})
        if response.status_code == 200:
            print("   ✓ trading_data database created")
        else:
            print(f"   ✗ Failed to create database: HTTP {response.status_code}")
    except Exception as e:
        print(f"   ✗ Database creation error: {e}")

async def create_ticks_table(client):
    """Create ticks table with proper schema"""
    try:
        # Use the existing schema from the database service
        schema_sql = """
        CREATE TABLE IF NOT EXISTS trading_data.ticks (
            timestamp DateTime64(3),
            symbol String,
            bid Float64,
            ask Float64,
            last Float64,
            volume Float64,
            spread Float64,
            primary_session String,
            active_sessions Array(String),
            session_overlap UInt8,
            broker String,
            account_type String
        ) ENGINE = MergeTree()
        ORDER BY (timestamp, symbol)
        PARTITION BY toYYYYMM(timestamp)
        """
        
        response = await client.post("/", params={'query': schema_sql})
        if response.status_code == 200:
            print("   ✓ ticks table created")
        else:
            print(f"   ✗ Failed to create table: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ✗ Table creation error: {e}")

async def main():
    """Main test function"""
    try:
        success = await test_clickhouse_connection()
        
        print("\\n" + "=" * 60)
        if success:
            print("✓ ALL TESTS PASSED - ClickHouse authentication is working!")
        else:
            print("✗ TESTS FAILED - ClickHouse authentication issues detected")
        print("=" * 60)
        
    except Exception as e:
        print(f"\\n✗ FATAL ERROR: {e}")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())