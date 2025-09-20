#!/usr/bin/env python3
"""
Test script to create economic_calendar table in ClickHouse directly
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src path to sys.path for proper imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.business.database_manager import DatabaseManager
from src.schemas.clickhouse.external_data_schemas import ClickhouseExternalDataSchemas


async def create_economic_calendar_table():
    """Create economic_calendar table directly using DatabaseManager"""
    print("🚀 Creating economic_calendar table...")
    
    try:
        # Initialize database manager
        db_manager = DatabaseManager()
        await db_manager.initialize()
        print("✅ Database manager initialized")
        
        # Get the economic calendar schema
        schema_sql = ClickhouseExternalDataSchemas.economic_calendar()
        print(f"📋 Schema SQL length: {len(schema_sql)} characters")
        
        # Execute table creation
        print("🔧 Executing CREATE TABLE query...")
        result = await db_manager.execute_clickhouse_query(
            query=schema_sql,
            database="trading_data"
        )
        
        print("✅ Economic calendar table created successfully!")
        print(f"📊 Result: {result}")
        
        # Test with a simple query to verify table exists
        print("\n🔍 Verifying table was created...")
        verify_query = "SHOW TABLES FROM trading_data LIKE 'economic_calendar'"
        verify_result = await db_manager.execute_clickhouse_query(
            query=verify_query,
            database="trading_data"  
        )
        
        if verify_result:
            print("✅ Table verification successful!")
            print(f"📋 Table found: {verify_result}")
        else:
            print("❌ Table verification failed - table not found")
        
        # Test table structure
        print("\n📋 Checking table structure...")
        structure_query = "DESCRIBE trading_data.economic_calendar"
        structure_result = await db_manager.execute_clickhouse_query(
            query=structure_query,
            database="trading_data"
        )
        
        print(f"📊 Table structure ({len(structure_result)} columns):")
        for i, column in enumerate(structure_result[:10]):  # Show first 10 columns
            print(f"  {i+1}. {column}")
            
        if len(structure_result) > 10:
            print(f"  ... and {len(structure_result) - 10} more columns")
        
        # Cleanup
        await db_manager.shutdown()
        print("\n🎉 Table creation test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error creating economic calendar table: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("📅 Economic Calendar Table Creation Test")
    print("=" * 50)
    asyncio.run(create_economic_calendar_table())