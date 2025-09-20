#!/usr/bin/env python3
"""
Test Economic Calendar Table Creation and Data Insertion
Verifies the complete AI-enhanced schema is applied correctly
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timezone
import time

# Test configuration
DATABASE_SERVICE_URL = "http://localhost:8008"
TEST_DATABASE_TYPE = "clickhouse"
TEST_TABLE_NAME = "economic_calendar"

async def test_table_creation():
    """Test the economic calendar table creation endpoint"""
    print("🔧 Testing Economic Calendar Table Creation")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        try:
            # Test 1: Create the economic_calendar table
            print(f"1️⃣ Creating table: {TEST_TABLE_NAME}")
            
            create_url = f"{DATABASE_SERVICE_URL}/api/v1/schemas/tables/{TEST_DATABASE_TYPE}/{TEST_TABLE_NAME}/create"
            create_payload = {
                "force_recreate": True  # Force recreation to ensure clean state
            }
            
            async with session.post(create_url, json=create_payload) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Table creation successful: {result}")
                    
                    if result.get("success"):
                        print(f"   ✅ Schema applied: {result.get('schema_applied', False)}")
                        print(f"   ⏱️ Duration: {result.get('creation_duration_ms', 0):.2f}ms")
                        print(f"   💬 Message: {result.get('message', 'No message')}")
                    else:
                        print(f"   ❌ Table creation failed: {result.get('message', 'Unknown error')}")
                        return False
                else:
                    error_text = await response.text()
                    print(f"❌ HTTP Error {response.status}: {error_text}")
                    return False
            
            # Test 2: Verify table schema
            print(f"\n2️⃣ Verifying table schema")
            
            schema_url = f"{DATABASE_SERVICE_URL}/api/v1/schemas/{TEST_DATABASE_TYPE}/{TEST_TABLE_NAME}"
            
            async with session.get(schema_url) as response:
                if response.status == 200:
                    schema_result = await response.json()
                    print(f"✅ Schema retrieved successfully")
                    
                    schema_sql = schema_result.get("schema_sql", "")
                    
                    # Verify AI-enhanced columns are present
                    ai_columns = [
                        "ai_predicted_value",
                        "ai_prediction_confidence",
                        "ai_sentiment_score",
                        "volatility_impact_score",
                        "currency_pair_impacts",
                        "sector_rotation_prediction",
                        "central_bank_reaction_probability",
                        "historical_pattern_match",
                        "seasonal_adjustment",
                        "surprise_index",
                        "consensus_accuracy"
                    ]
                    
                    missing_columns = []
                    for column in ai_columns:
                        if column not in schema_sql:
                            missing_columns.append(column)
                    
                    if not missing_columns:
                        print(f"   ✅ All AI-enhanced columns found in schema")
                    else:
                        print(f"   ⚠️ Missing AI columns: {missing_columns}")
                    
                    print(f"   📏 Schema SQL length: {len(schema_sql)} characters")
                else:
                    error_text = await response.text()
                    print(f"❌ Schema retrieval failed: {response.status} - {error_text}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Test error: {e}")
            return False

async def test_data_insertion():
    """Test inserting economic calendar data with AI-enhanced fields"""
    print("\n🔬 Testing Economic Calendar Data Insertion")
    print("=" * 60)
    
    # Sample economic calendar data with AI-enhanced fields
    sample_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_name": "US Non-Farm Payrolls",
        "country": "US",
        "currency": "USD",
        "importance": "High",
        "scheduled_time": datetime.now(timezone.utc).isoformat(),
        "actual_release_time": None,
        "timezone": "EST",
        "actual": "180K",
        "forecast": "170K",
        "previous": "160K",
        "unit": "jobs",
        "deviation_from_forecast": 10000.0,
        "market_impact": "High",
        "volatility_expected": "High",
        "currency_impact": "Bullish",
        "affected_sectors": "Banking,Manufacturing,Services",
        
        # AI-Enhanced fields
        "ai_predicted_value": 175000.0,
        "ai_prediction_confidence": 0.85,
        "ai_prediction_model": "ensemble_v2",
        "ai_sentiment_score": 0.65,
        "volatility_impact_score": 8.5,
        "currency_pair_impacts": "EURUSD:-0.3,GBPUSD:-0.2,USDJPY:+0.4",
        "sector_rotation_prediction": "Tech->Financials,Energy->Healthcare",
        "central_bank_reaction_probability": 0.25,
        "historical_pattern_match": 0.78,
        "seasonal_adjustment": 1.05,
        "surprise_index": 2.3,
        "consensus_accuracy": 0.82,
        
        # Cross-Asset Impact Analysis
        "bond_impact_prediction": "10Y_Treasury:-5bp,30Y_Treasury:-3bp",
        "equity_impact_prediction": "S&P500:+0.5%,NASDAQ:+0.3%,Russell2000:+0.7%",
        "commodity_impact_prediction": "Gold:-0.2%,Oil:+0.1%,Copper:+0.3%",
        
        # Time-based Impact Analysis
        "immediate_impact_window": "0-15min:High,15-30min:Medium",
        "delayed_impact_window": "1-4h:Medium,4-24h:Low",
        "impact_duration_minutes": 120,
        
        # Market Conditions Context
        "market_conditions_at_release": "Neutral,Low_VIX,High_Liquidity",
        "liquidity_conditions": "Normal",
        "concurrent_events": "ECB_Speech,UK_Inflation_Data",
        
        # Metadata
        "event_id": "NFP_2025_01_10",
        "source": "MQL5",
        "widget_url": "https://example.com/widget/nfp",
        "scraped_at": datetime.now(timezone.utc).isoformat()
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            # Insert data into ClickHouse
            print(f"1️⃣ Inserting sample economic calendar data")
            
            insert_url = f"{DATABASE_SERVICE_URL}/api/v1/database/clickhouse/insert"
            insert_payload = {
                "table": TEST_TABLE_NAME,
                "data": [sample_data],  # ClickHouse expects array of records
                "database": "trading_data"
            }
            
            async with session.post(insert_url, json=insert_payload) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Data insertion successful: {result}")
                    
                    if result.get("success"):
                        print(f"   📊 Records inserted: {result.get('records_inserted', 0)}")
                        print(f"   ⏱️ Duration: {result.get('query_duration_ms', 0):.2f}ms")
                        print(f"   🗃️ Database: {result.get('database', 'N/A')}")
                    else:
                        print(f"   ❌ Data insertion failed")
                        return False
                else:
                    error_text = await response.text()
                    print(f"❌ HTTP Error {response.status}: {error_text}")
                    return False
            
            # Test 2: Query the inserted data
            print(f"\n2️⃣ Querying inserted economic calendar data")
            
            query_url = f"{DATABASE_SERVICE_URL}/api/v1/database/clickhouse/query"
            query_params = {
                "query": f"SELECT * FROM trading_data.{TEST_TABLE_NAME} WHERE event_id = 'NFP_2025_01_10' ORDER BY timestamp DESC LIMIT 1",
                "database": "trading_data"
            }
            
            async with session.get(query_url, params=query_params) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Data query successful")
                    
                    if result.get("success") and result.get("result"):
                        records = result.get("result", [])
                        print(f"   📊 Records found: {len(records)}")
                        print(f"   ⏱️ Query duration: {result.get('query_duration_ms', 0):.2f}ms")
                        
                        if records:
                            record = records[0]
                            print(f"   📈 Event: {record.get('event_name', 'N/A')}")
                            print(f"   🤖 AI Confidence: {record.get('ai_prediction_confidence', 'N/A')}")
                            print(f"   📊 Volatility Score: {record.get('volatility_impact_score', 'N/A')}")
                            print(f"   💹 Currency Impact: {record.get('currency_impact', 'N/A')}")
                    else:
                        print(f"   ⚠️ No records found or query failed")
                        return False
                else:
                    error_text = await response.text()
                    print(f"❌ Query failed: {response.status} - {error_text}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Data insertion test error: {e}")
            return False

async def test_service_health():
    """Test database service health"""
    print("\n❤️ Testing Database Service Health")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        try:
            # General health check
            health_url = f"{DATABASE_SERVICE_URL}/health"
            
            async with session.get(health_url) as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"✅ Service health: {health_data.get('status', 'Unknown')}")
                    print(f"   🔗 Active connections: {health_data.get('active_connections', 0)}")
                    
                    database_status = health_data.get('database_status', {})
                    for db_type, status in database_status.items():
                        print(f"   🗃️ {db_type}: {status}")
                    
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Health check failed: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False

async def main():
    """Run all tests"""
    print("🚀 Economic Calendar Database Schema Test Suite")
    print("=" * 80)
    print(f"🎯 Target Service: {DATABASE_SERVICE_URL}")
    print(f"🗃️ Database Type: {TEST_DATABASE_TYPE}")
    print(f"📋 Table Name: {TEST_TABLE_NAME}")
    print(f"🕒 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Run tests
    tests = [
        ("Service Health Check", test_service_health),
        ("Table Creation", test_table_creation),
        ("Data Insertion", test_data_insertion)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"💥 {test_name}: CRASHED - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 80)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name:<30} {status}")
    
    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests PASSED! Economic calendar schema is working correctly.")
        return True
    else:
        print("⚠️ Some tests FAILED. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)