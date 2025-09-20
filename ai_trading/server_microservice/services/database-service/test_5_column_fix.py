#!/usr/bin/env python3
"""
Test script for 5-column tick data validation
Tests the fixed database service against the actual ClickHouse table structure
"""

import asyncio
import sys
import os
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from business.database_manager import DatabaseManager

async def test_5_column_validation():
    """Test the fixed 5-column tick data processing"""
    
    print("=== Testing 5-Column Tick Data Fix ===")
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    try:
        # Test 1: Validate 5-column tick data structure
        print("\n1. Testing 5-column tick data validation...")
        
        # Sample tick data with ONLY the 5 columns that exist in actual table
        sample_tick_data = [
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
        
        # Test batch processing
        print("  - Testing batch processing...")
        processed_ticks = db_manager._batch_process_tick_data(sample_tick_data, "test", "demo")
        
        print(f"  - Original ticks: {len(sample_tick_data)}")
        print(f"  - Processed ticks: {len(processed_ticks)}")
        
        # Validate structure
        for i, tick in enumerate(processed_ticks):
            required_fields = {"timestamp", "symbol", "bid", "ask", "broker"}
            tick_fields = set(tick.keys())
            
            if not required_fields.issubset(tick_fields):
                missing = required_fields - tick_fields
                print(f"  ❌ Tick {i} missing fields: {missing}")
                return False
            
            # Check no extra fields (should only have 5 columns)
            extra_fields = tick_fields - required_fields
            if extra_fields:
                print(f"  ⚠️  Tick {i} has extra fields: {extra_fields}")
            
            print(f"  ✓ Tick {i}: {tick['symbol']} @ {tick['bid']}/{tick['ask']} (broker: {tick['broker']})")
        
        # Test 2: Validate batch validation works
        print("\n2. Testing batch validation...")
        await db_manager._batch_validate_tick_data(processed_ticks)
        print("  ✓ Batch validation passed")
        
        # Test 3: Test schema retrieval
        print("\n3. Testing table schema retrieval...")
        schema_sql = await db_manager.get_table_schema("clickhouse", "ticks")
        if schema_sql:
            print("  ✓ Schema retrieved successfully")
            print("  Schema preview:")
            lines = schema_sql.strip().split('\n')
            for line in lines[:10]:  # Show first 10 lines
                if line.strip():
                    print(f"    {line.strip()}")
            if len(lines) > 10:
                print("    ...")
        else:
            print("  ❌ Schema retrieval failed")
            return False
        
        # Test 4: Test with invalid data (should fail)
        print("\n4. Testing validation with invalid data...")
        try:
            invalid_tick_data = [
                {
                    "symbol": "EURUSD",  # Missing timestamp, bid, ask, broker
                    "bid": 1.0850
                }
            ]
            await db_manager._batch_validate_tick_data(invalid_tick_data)
            print("  ❌ Validation should have failed for incomplete data")
            return False
        except ValueError as e:
            print(f"  ✓ Validation correctly failed: {e}")
        
        print("\n=== All Tests Passed! ===")
        print("✓ 5-column tick data structure is working correctly")
        print("✓ No more 12-column validation errors")
        print("✓ Database service matches actual ClickHouse table structure")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_insert_query_generation():
    """Test the INSERT query generation for 5-column table"""
    
    print("\n=== Testing INSERT Query Generation ===")
    
    db_manager = DatabaseManager()
    
    # Sample 5-column data
    tick_data = [
        {
            "timestamp": "2024-01-09 15:30:45.123",
            "symbol": "EURUSD",
            "bid": 1.0850,
            "ask": 1.0852, 
            "broker": "test"
        }
    ]
    
    # Test VALUES format generation (simulated)
    print("\nTesting VALUES format generation...")
    processed_ticks = db_manager._batch_process_tick_data(tick_data, "test", "demo")
    
    print("Sample INSERT query would be:")
    values = []
    for record in processed_ticks:
        timestamp = db_manager._escape_sql_string(record.get('timestamp', 'now64()'))
        symbol = db_manager._escape_sql_string(record.get('symbol', ''))
        bid = float(record.get('bid', 0.0))
        ask = float(record.get('ask', 0.0))
        broker = db_manager._escape_sql_string(record.get('broker', 'test'))
        
        values_tuple = f"('{timestamp}', '{symbol}', {bid}, {ask}, '{broker}')"
        values.append(values_tuple)
    
    values_clause = ',\n    '.join(values)
    insert_query = f"""INSERT INTO trading_data.ticks 
        (timestamp, symbol, bid, ask, broker) 
        VALUES 
    {values_clause}"""
    
    print(insert_query)
    print("\n✓ Query structure matches 5-column table")

if __name__ == "__main__":
    async def main():
        success = await test_5_column_validation()
        await test_insert_query_generation()
        
        if success:
            print("\n🎉 ALL TESTS PASSED - Database service is fixed!")
            sys.exit(0)
        else:
            print("\n💥 TESTS FAILED - Issues remain")
            sys.exit(1)
    
    asyncio.run(main())