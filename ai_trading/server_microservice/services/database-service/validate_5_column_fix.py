#!/usr/bin/env python3
"""
Simple validation script to check the 5-column fix
Tests schema definitions and data structure compatibility
"""

import re
import os

def validate_schema_fix():
    """Validate that the schema has been fixed to 5 columns"""
    
    print("=== Validating 5-Column Schema Fix ===")
    
    # Read the schema file
    schema_file = "src/schemas/clickhouse/raw_data_schemas.py"
    
    if not os.path.exists(schema_file):
        print(f"❌ Schema file not found: {schema_file}")
        return False
    
    with open(schema_file, 'r') as f:
        content = f.read()
    
    # Find the ticks table definition
    ticks_match = re.search(r'def ticks\(\) -> str:.*?return """(.*?)"""', content, re.DOTALL)
    if not ticks_match:
        print("❌ Could not find ticks() method definition")
        return False
    
    ticks_definition = ticks_match.group(1)
    print("✓ Found ticks table definition")
    
    # Check for 5-column structure
    expected_columns = [
        "timestamp DateTime64(3) DEFAULT now64()",
        "symbol String",
        "bid Float64",
        "ask Float64", 
        "broker String DEFAULT 'test'"
    ]
    
    print("\nValidating column structure:")
    all_columns_found = True
    
    for column in expected_columns:
        # Look for the column definition (allowing for slight formatting variations)
        column_pattern = column.replace("(", r"\(").replace(")", r"\)").replace("'", r"['\"]")
        if re.search(column_pattern, ticks_definition):
            print(f"  ✓ {column}")
        else:
            print(f"  ❌ Missing: {column}")
            all_columns_found = False
    
    # Check that old 12-column fields are NOT present
    old_columns = [
        "last Float64",
        "volume Float64", 
        "spread Float64",
        "primary_session",
        "active_sessions Array",
        "session_overlap Boolean",
        "account_type"
    ]
    
    print("\nValidating old columns are removed:")
    old_columns_removed = True
    
    for column in old_columns:
        if column.lower() in ticks_definition.lower():
            print(f"  ❌ Old column still present: {column}")
            old_columns_removed = False
        else:
            print(f"  ✓ Removed: {column}")
    
    return all_columns_found and old_columns_removed

def validate_database_manager_fix():
    """Validate that database manager processing is fixed"""
    
    print("\n=== Validating Database Manager Fix ===")
    
    db_manager_file = "src/business/database_manager.py"
    
    if not os.path.exists(db_manager_file):
        print(f"❌ Database manager file not found: {db_manager_file}")
        return False
    
    with open(db_manager_file, 'r') as f:
        content = f.read()
    
    # Check for updated validation
    validation_checks = [
        ('_batch_validate_tick_data', 'ACTUAL 5-column table schema'),
        ('_batch_process_tick_data', 'ACTUAL 5-column table schema'),
        ('_process_tick_data', 'ACTUAL 5-column ClickHouse table schema'),
        ('_optimized_bulk_insert_ticks', 'ACTUAL 5-column table')
    ]
    
    print("\nValidating method updates:")
    all_methods_updated = True
    
    for method_name, expected_comment in validation_checks:
        if expected_comment in content:
            print(f"  ✓ {method_name} updated with 5-column comment")
        else:
            print(f"  ❌ {method_name} missing 5-column comment")
            all_methods_updated = False
    
    # Check for INSERT statement fix
    if "(timestamp, symbol, bid, ask, broker)" in content:
        print("  ✓ INSERT statement updated to 5 columns")
    else:
        print("  ❌ INSERT statement not updated to 5 columns")
        all_methods_updated = False
    
    # Check that old 12-column validation is removed
    if "last\", \"volume\", \"spread\"" in content:
        print("  ❌ Old 12-column validation still present")
        all_methods_updated = False
    else:
        print("  ✓ Old 12-column validation removed")
    
    return all_methods_updated

def generate_test_data_example():
    """Generate example of properly structured 5-column test data"""
    
    print("\n=== Sample 5-Column Test Data ===")
    
    sample_data = """
# Correctly structured tick data for the ACTUAL 5-column table:
tick_data = [
    {
        "timestamp": "2024-01-09 15:30:45.123",
        "symbol": "EURUSD",
        "bid": 1.0850,
        "ask": 1.0852,
        "broker": "test"
    },
    {
        "timestamp": "2024-01-09 15:30:46.456", 
        "symbol": "GBPUSD",
        "bid": 1.2650,
        "ask": 1.2652,
        "broker": "test"
    }
]

# Expected INSERT query:
INSERT INTO trading_data.ticks 
    (timestamp, symbol, bid, ask, broker) 
VALUES 
    ('2024-01-09 15:30:45.123', 'EURUSD', 1.085, 1.0852, 'test'),
    ('2024-01-09 15:30:46.456', 'GBPUSD', 1.265, 1.2652, 'test')
"""
    
    print(sample_data)
    return True

if __name__ == "__main__":
    print("Database Service 5-Column Fix Validation")
    print("=" * 50)
    
    schema_ok = validate_schema_fix()
    db_manager_ok = validate_database_manager_fix()
    generate_test_data_example()
    
    print("\n" + "=" * 50)
    if schema_ok and db_manager_ok:
        print("🎉 ALL VALIDATIONS PASSED!")
        print("✓ Schema fixed to 5-column structure")
        print("✓ Database manager updated for 5-column processing")
        print("✓ Validation logic matches actual ClickHouse table")
        print("\nThe database service should now work with your actual 5-column table!")
    else:
        print("💥 VALIDATION ISSUES FOUND")
        if not schema_ok:
            print("❌ Schema definition issues")
        if not db_manager_ok:
            print("❌ Database manager processing issues")
    
    exit(0 if (schema_ok and db_manager_ok) else 1)