#!/usr/bin/env python3
"""
Test ClickHouse Authentication Fix
Tests the corrected ClickHouse authentication and schema auto-creation
"""

import asyncio
import httpx
import os
import logging
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_clickhouse_connection():
    """Test ClickHouse connection with corrected authentication"""
    
    # Use the same hostname resolution logic as connection factory
    is_docker = os.path.exists('/.dockerenv') or os.getenv('DOCKER_ENV', 'false').lower() == 'true'
    
    if is_docker:
        host = 'database-clickhouse'  # Docker service name
    else:
        host = 'localhost'  # Development environment
    
    port = int(os.getenv('CLICKHOUSE_PORT', '8123'))
    user = os.getenv('CLICKHOUSE_USER', 'neliti_user')
    password = os.getenv('CLICKHOUSE_PASSWORD', 'clickhouse_password_2024')
    
    logger.info(f"Testing ClickHouse connection - Docker: {is_docker}, host: {host}, port: {port}, user: {user}")
    
    # Test basic connection
    auth_config = (user, password) if password and password.strip() else None
    
    client = httpx.AsyncClient(
        base_url=f"http://{host}:{port}",
        auth=auth_config,
        timeout=httpx.Timeout(30.0)
    )
    
    try:
        # Test 1: Ping endpoint
        logger.info("Test 1: Testing ping endpoint...")
        response = await client.get("/ping")
        logger.info(f"Ping response: HTTP {response.status_code}")
        if response.status_code != 200:
            logger.error(f"Ping failed: {response.text}")
            return False
        
        # Test 2: Basic query
        logger.info("Test 2: Testing basic query...")
        query = "SELECT 1 as test_value"
        params = {
            'query': query,
            'default_format': 'JSONEachRow'
        }
        
        response = await client.post("/", params=params)
        logger.info(f"Query response: HTTP {response.status_code}")
        if response.status_code != 200:
            logger.error(f"Query failed: {response.text}")
            return False
        
        result_text = response.text.strip()
        logger.info(f"Query result: {result_text}")
        
        # Test 3: Create database
        logger.info("Test 3: Testing database creation...")
        create_db_query = "CREATE DATABASE IF NOT EXISTS trading_data"
        params = {'query': create_db_query}
        
        response = await client.post("/", params=params)
        logger.info(f"Create database response: HTTP {response.status_code}")
        if response.status_code != 200:
            logger.error(f"Create database failed: {response.text}")
            return False
        
        # Test 4: Use database
        logger.info("Test 4: Testing database selection...")
        use_db_query = "USE trading_data"
        params = {'query': use_db_query}
        
        response = await client.post("/", params=params)
        logger.info(f"Use database response: HTTP {response.status_code}")
        if response.status_code != 200:
            logger.error(f"Use database failed: {response.text}")
            return False
        
        # Test 5: Create economic_calendar table
        logger.info("Test 5: Testing economic_calendar table creation...")
        
        create_table_query = """
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
        
        params = {'query': create_table_query}
        
        response = await client.post("/", params=params)
        logger.info(f"Create table response: HTTP {response.status_code}")
        if response.status_code != 200:
            logger.error(f"Create table failed: {response.text}")
            return False
        
        # Test 6: Verify table exists
        logger.info("Test 6: Verifying table exists...")
        check_table_query = "SHOW TABLES FROM trading_data"
        params = {
            'query': check_table_query,
            'default_format': 'JSONEachRow'
        }
        
        response = await client.post("/", params=params)
        logger.info(f"Show tables response: HTTP {response.status_code}")
        if response.status_code != 200:
            logger.error(f"Show tables failed: {response.text}")
            return False
        
        tables_text = response.text.strip()
        logger.info(f"Available tables: {tables_text}")
        
        # Check if economic_calendar is in the list
        if "economic_calendar" in tables_text:
            logger.info("✅ SUCCESS: economic_calendar table created successfully!")
        else:
            logger.error("❌ FAIL: economic_calendar table not found in table list")
            return False
        
        logger.info("🎉 All ClickHouse authentication and schema tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        return False
        
    finally:
        await client.aclose()

async def main():
    """Main test function"""
    logger.info("Starting ClickHouse authentication fix test...")
    
    success = await test_clickhouse_connection()
    
    if success:
        logger.info("🎉 ClickHouse authentication fix successful!")
        return 0
    else:
        logger.error("❌ ClickHouse authentication fix failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)