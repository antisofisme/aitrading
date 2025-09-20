#!/usr/bin/env python3
"""
Create Economic Calendar Table Script
Simple script to ensure the economic_calendar table exists with the full AI-enhanced schema
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# Configuration
DATABASE_SERVICE_URL = "http://localhost:8008"
DATABASE_TYPE = "clickhouse"
TABLE_NAME = "economic_calendar"

async def create_economic_calendar_table():
    """Create the economic calendar table with full AI-enhanced schema"""
    print("🔧 Creating Economic Calendar Table")
    print("=" * 50)
    print(f"Service: {DATABASE_SERVICE_URL}")
    print(f"Database: {DATABASE_TYPE}")
    print(f"Table: {TABLE_NAME}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        try:
            # Step 1: Check service health
            print("\n1️⃣ Checking database service health...")
            
            health_url = f"{DATABASE_SERVICE_URL}/health"
            async with session.get(health_url) as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"✅ Service status: {health_data.get('status', 'Unknown')}")
                    
                    database_status = health_data.get('database_status', {})
                    if 'clickhouse' in database_status:
                        print(f"✅ ClickHouse status: {database_status['clickhouse']}")
                    else:
                        print("⚠️ ClickHouse status not found")
                else:
                    print(f"❌ Health check failed: HTTP {response.status}")
                    return False
            
            # Step 2: Check if schema exists
            print(f"\n2️⃣ Checking existing schema for {TABLE_NAME}...")
            
            schema_url = f"{DATABASE_SERVICE_URL}/api/v1/schemas/{DATABASE_TYPE}/{TABLE_NAME}"
            async with session.get(schema_url) as response:
                if response.status == 200:
                    schema_data = await response.json()
                    if schema_data.get("success"):
                        print("✅ Schema definition found")
                        schema_sql = schema_data.get("schema_sql", "")
                        print(f"   📏 Schema length: {len(schema_sql)} characters")
                        
                        # Check for key AI columns
                        ai_columns = ["ai_predicted_value", "volatility_impact_score", "ai_sentiment_score"]
                        found_ai = sum(1 for col in ai_columns if col in schema_sql)
                        print(f"   🤖 AI columns found: {found_ai}/{len(ai_columns)}")
                    else:
                        print("❌ Schema definition not found")
                        return False
                else:
                    print(f"❌ Schema check failed: HTTP {response.status}")
                    return False
            
            # Step 3: Create the table (force recreate for clean state)
            print(f"\n3️⃣ Creating table {TABLE_NAME}...")
            
            create_url = f"{DATABASE_SERVICE_URL}/api/v1/schemas/tables/{DATABASE_TYPE}/{TABLE_NAME}/create"
            create_payload = {
                "force_recreate": True  # Ensure clean table creation
            }
            
            async with session.post(create_url, json=create_payload) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("success"):
                        print("✅ Table created successfully!")
                        print(f"   💬 Message: {result.get('message', 'N/A')}")
                        print(f"   ⏱️ Duration: {result.get('creation_duration_ms', 0):.2f}ms")
                        print(f"   📊 Schema applied: {result.get('schema_applied', False)}")
                    else:
                        print(f"❌ Table creation failed: {result.get('message', 'Unknown error')}")
                        return False
                else:
                    error_text = await response.text()
                    print(f"❌ Table creation request failed: HTTP {response.status}")
                    print(f"   Error: {error_text}")
                    return False
            
            # Step 4: Verify table creation with a simple query
            print(f"\n4️⃣ Verifying table creation...")
            
            verify_url = f"{DATABASE_SERVICE_URL}/api/v1/database/clickhouse/query"
            verify_params = {
                "query": f"DESCRIBE TABLE trading_data.{TABLE_NAME}",
                "database": "trading_data"
            }
            
            async with session.get(verify_url, params=verify_params) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("success"):
                        columns = result.get("result", [])
                        print(f"✅ Table verified! Found {len(columns)} columns")
                        
                        # Check for critical AI columns
                        column_names = [col.get('name', '') for col in columns if isinstance(col, dict)]
                        
                        critical_columns = [
                            "ai_predicted_value",
                            "ai_prediction_confidence", 
                            "volatility_impact_score",
                            "currency_pair_impacts",
                            "historical_pattern_match"
                        ]
                        
                        found_critical = []
                        for col in critical_columns:
                            if any(col in name for name in column_names):
                                found_critical.append(col)
                        
                        print(f"   🤖 Critical AI columns verified: {len(found_critical)}/{len(critical_columns)}")
                        
                        if len(found_critical) >= 3:  # At least 3 AI columns should be present
                            print("✅ AI-enhanced schema successfully applied!")
                        else:
                            print("⚠️ AI-enhanced columns may be missing")
                            
                    else:
                        print(f"⚠️ Table verification query failed")
                else:
                    print(f"⚠️ Table verification request failed: HTTP {response.status}")
            
            print(f"\n✅ Economic calendar table setup completed!")
            print("🎯 Table is ready for economic data insertion")
            return True
            
        except Exception as e:
            print(f"💥 Error during table creation: {e}")
            return False

async def main():
    """Main execution function"""
    success = await create_economic_calendar_table()
    
    if success:
        print("\n🎉 SUCCESS: Economic calendar table is ready!")
        print("\n📋 Next steps:")
        print("  1. Use the data insertion endpoints to add economic events")
        print("  2. Run the test suite: python test_economic_calendar_creation.py")
        print("  3. Check data with: curl 'http://localhost:8008/api/v1/database/clickhouse/query?query=SELECT COUNT(*) FROM trading_data.economic_calendar'")
    else:
        print("\n❌ FAILED: Economic calendar table creation failed")
        print("\n🔧 Troubleshooting:")
        print("  1. Check if the database service is running on port 8008")
        print("  2. Verify ClickHouse is accessible and configured correctly")
        print("  3. Check service logs for detailed error information")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)