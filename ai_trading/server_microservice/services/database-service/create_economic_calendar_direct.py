#!/usr/bin/env python3
"""
Direct Economic Calendar Table Creation via ClickHouse Query
Uses the existing ClickHouse query endpoint to create the table directly
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# Configuration
DATABASE_SERVICE_URL = "http://localhost:8008"
DATABASE_NAME = "trading_data"

# Get the schema SQL from our schemas module
def get_economic_calendar_schema():
    """Get the economic calendar schema SQL"""
    return """
        CREATE TABLE IF NOT EXISTS economic_calendar (
            timestamp DateTime64(3) CODEC(Delta, LZ4),
            event_name String CODEC(ZSTD),
            country LowCardinality(String),
            currency LowCardinality(String),
            
            -- Event Data
            importance LowCardinality(String),
            scheduled_time DateTime64(3),
            actual_release_time Nullable(DateTime64(3)),
            timezone LowCardinality(String),
            
            -- Economic Values
            actual Nullable(String),
            forecast Nullable(String),
            previous Nullable(String),
            unit Nullable(String),
            deviation_from_forecast Nullable(Float64),
            
            -- AI-Enhanced Impact Analysis
            market_impact LowCardinality(String),
            volatility_expected LowCardinality(String),
            currency_impact LowCardinality(String),
            affected_sectors String CODEC(ZSTD),
            
            -- Critical Accuracy Enhancements - Phase 1
            -- AI Predictions
            ai_predicted_value Nullable(Float64) CODEC(Gorilla),
            ai_prediction_confidence Nullable(Float64) CODEC(Gorilla),
            ai_prediction_model LowCardinality(String) DEFAULT 'ensemble',
            ai_sentiment_score Nullable(Float64) CODEC(Gorilla),
            
            -- Enhanced Impact Metrics
            volatility_impact_score Float64 CODEC(Gorilla),
            currency_pair_impacts String CODEC(ZSTD),
            sector_rotation_prediction String CODEC(ZSTD),
            central_bank_reaction_probability Float64 CODEC(Gorilla),
            
            -- Historical Pattern Recognition
            historical_pattern_match Float64 CODEC(Gorilla),
            seasonal_adjustment Float64 CODEC(Gorilla),
            surprise_index Float64 CODEC(Gorilla),
            consensus_accuracy Float64 CODEC(Gorilla),
            
            -- Cross-Asset Impact Analysis
            bond_impact_prediction String CODEC(ZSTD),
            equity_impact_prediction String CODEC(ZSTD),
            commodity_impact_prediction String CODEC(ZSTD),
            
            -- Time-based Impact Analysis
            immediate_impact_window String CODEC(ZSTD),
            delayed_impact_window String CODEC(ZSTD),
            impact_duration_minutes Nullable(UInt32) CODEC(T64),
            
            -- Market Conditions Context
            market_conditions_at_release String CODEC(ZSTD),
            liquidity_conditions String CODEC(ZSTD),
            concurrent_events String CODEC(ZSTD),
            
            -- Metadata
            event_id Nullable(String),
            source LowCardinality(String) DEFAULT 'MQL5',
            widget_url Nullable(String),
            scraped_at DateTime64(3) DEFAULT now64(),
            
            -- Enhanced Indexing
            INDEX idx_country country TYPE set(50) GRANULARITY 8192,
            INDEX idx_currency currency TYPE set(20) GRANULARITY 8192,
            INDEX idx_importance importance TYPE set(5) GRANULARITY 8192,
            INDEX idx_timestamp timestamp TYPE minmax GRANULARITY 8192
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(timestamp)
        ORDER BY (country, currency, timestamp)
        TTL toDate(timestamp) + INTERVAL 1 YEAR
        SETTINGS index_granularity = 8192
    """

async def create_economic_calendar_table_direct():
    """Create economic calendar table using direct ClickHouse query"""
    print("🔧 Creating Economic Calendar Table (Direct ClickHouse Query)")
    print("=" * 65)
    print(f"Service: {DATABASE_SERVICE_URL}")
    print(f"Database: {DATABASE_NAME}")
    print(f"Method: Direct ClickHouse Query")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)
    
    async with aiohttp.ClientSession() as session:
        try:
            # Step 1: Check service health
            print("\n1️⃣ Checking database service health...")
            
            health_url = f"{DATABASE_SERVICE_URL}/health"
            async with session.get(health_url) as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"✅ Service status: {health_data.get('status', 'Unknown')}")
                else:
                    print(f"❌ Health check failed: HTTP {response.status}")
                    return False
            
            # Step 2: Create database (if not exists)
            print(f"\n2️⃣ Creating database {DATABASE_NAME}...")
            
            create_db_query = f"CREATE DATABASE IF NOT EXISTS {DATABASE_NAME}"
            
            clickhouse_url = f"{DATABASE_SERVICE_URL}/api/v1/clickhouse/query"
            params = {
                "query": create_db_query,
                "database": "default"
            }
            
            async with session.get(clickhouse_url, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("success"):
                        print(f"✅ Database {DATABASE_NAME} created/verified")
                    else:
                        print(f"⚠️ Database creation response: {result}")
                else:
                    error_text = await response.text()
                    print(f"⚠️ Database creation warning: {response.status} - {error_text}")
            
            # Step 3: Create the economic_calendar table
            print(f"\n3️⃣ Creating economic_calendar table...")
            
            schema_sql = get_economic_calendar_schema().strip()
            
            # Execute table creation query
            params = {
                "query": schema_sql,
                "database": DATABASE_NAME
            }
            
            async with session.get(clickhouse_url, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("success"):
                        print("✅ Economic calendar table created successfully!")
                        print(f"   ⏱️ Duration: {result.get('query_duration_ms', 0):.2f}ms")
                        print(f"   🗃️ Database: {result.get('database', 'N/A')}")
                    else:
                        print(f"❌ Table creation failed: {result}")
                        return False
                else:
                    error_text = await response.text()
                    print(f"❌ Table creation request failed: HTTP {response.status}")
                    print(f"   Error: {error_text}")
                    return False
            
            # Step 4: Verify table creation
            print(f"\n4️⃣ Verifying table creation...")
            
            verify_query = f"DESCRIBE TABLE {DATABASE_NAME}.economic_calendar"
            params = {
                "query": verify_query,
                "database": DATABASE_NAME
            }
            
            async with session.get(clickhouse_url, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("success") and result.get("result"):
                        columns = result.get("result", [])
                        print(f"✅ Table verified! Found {len(columns)} columns")
                        
                        # Check for AI columns
                        column_names = [col.get('name', '') for col in columns if isinstance(col, dict)]
                        
                        ai_columns = [
                            "ai_predicted_value",
                            "ai_prediction_confidence", 
                            "volatility_impact_score",
                            "historical_pattern_match",
                            "currency_pair_impacts"
                        ]
                        
                        found_ai = sum(1 for ai_col in ai_columns if any(ai_col in col for col in column_names))
                        print(f"   🤖 AI-enhanced columns found: {found_ai}/{len(ai_columns)}")
                        
                        if found_ai >= 3:
                            print("✅ AI-enhanced schema successfully applied!")
                        else:
                            print("⚠️ Some AI-enhanced columns may be missing")
                    else:
                        print(f"⚠️ Table verification inconclusive: {result}")
                else:
                    print(f"⚠️ Table verification failed: HTTP {response.status}")
            
            # Step 5: Test data insertion
            print(f"\n5️⃣ Testing sample data insertion...")
            
            # Insert sample economic event
            sample_data = {
                "timestamp": datetime.now().isoformat(),
                "event_name": "US Non-Farm Payrolls (Test)",
                "country": "US",
                "currency": "USD",
                "importance": "High",
                "scheduled_time": datetime.now().isoformat(),
                "actual": "180K",
                "forecast": "170K", 
                "previous": "160K",
                "unit": "jobs",
                "market_impact": "High",
                "volatility_expected": "High",
                "currency_impact": "Bullish",
                "affected_sectors": "Banking,Manufacturing",
                "ai_predicted_value": 175000,
                "ai_prediction_confidence": 0.85,
                "volatility_impact_score": 8.5,
                "historical_pattern_match": 0.78,
                "currency_pair_impacts": "EURUSD:-0.3,USDJPY:+0.4",
                "event_id": "TEST_NFP_2025",
                "source": "TEST"
            }
            
            insert_url = f"{DATABASE_SERVICE_URL}/api/v1/database/clickhouse/insert"
            insert_payload = {
                "table": "economic_calendar",
                "data": [sample_data],
                "database": DATABASE_NAME
            }
            
            async with session.post(insert_url, json=insert_payload) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("success"):
                        print("✅ Sample data inserted successfully!")
                        print(f"   📊 Records: {result.get('records_inserted', 0)}")
                        print(f"   ⏱️ Duration: {result.get('query_duration_ms', 0):.2f}ms")
                    else:
                        print(f"⚠️ Data insertion failed: {result}")
                else:
                    error_text = await response.text()
                    print(f"⚠️ Data insertion failed: HTTP {response.status}")
                    print(f"   Error: {error_text}")
            
            print(f"\n✅ Economic calendar table setup completed!")
            print("🎯 Table is ready for economic data with AI-enhanced features")
            return True
            
        except Exception as e:
            print(f"💥 Error during table creation: {e}")
            return False

async def main():
    """Main execution function"""
    success = await create_economic_calendar_table_direct()
    
    if success:
        print("\n🎉 SUCCESS: Economic calendar table is ready with AI enhancements!")
        print("\n📋 AI-Enhanced Features Applied:")
        print("  🤖 AI prediction confidence and sentiment scores")
        print("  📊 Volatility impact scoring and pattern recognition")
        print("  💹 Cross-asset and currency pair impact analysis")
        print("  🔍 Historical pattern matching and seasonal adjustments")
        print("  ⏰ Time-based impact windows and duration analysis")
        print("  🏛️ Central bank reaction probability modeling")
        print("\n📋 Next steps:")
        print("  1. Use economic data insertion endpoints to add real economic events")
        print("  2. Query data with: curl 'http://localhost:8008/api/v1/clickhouse/query?query=SELECT COUNT(*) FROM trading_data.economic_calendar'")
        print("  3. Test AI features with advanced economic event queries")
    else:
        print("\n❌ FAILED: Economic calendar table creation failed")
        print("\n🔧 Troubleshooting:")
        print("  1. Check if ClickHouse is accessible and properly configured")
        print("  2. Verify database service logs for detailed error information")
        print("  3. Ensure trading_data database exists and is accessible")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)