#!/usr/bin/env python3
"""
Validation script for database service endpoints
Checks imports, validates endpoint definitions, and verifies data models
"""

import sys
import os
import asyncio
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def validate_imports():
    """Validate all required imports work"""
    print("🔍 Validating imports...")
    
    try:
        # Test main imports
        from ...shared.infrastructure.core.logger_core import CoreLogger
        from ...shared.infrastructure.core.config_core import CoreConfig
        from ...shared.infrastructure.core.error_core import CoreErrorHandler
        from ...shared.infrastructure.core.performance_core import CorePerformance
        from ...shared.infrastructure.optional.event_core import CoreEventManager
        from ...shared.infrastructure.optional.validation_core import CoreValidator
        print("✅ Core infrastructure imports: OK")
        
        # Test database manager import
        from src.business.database_manager import DatabaseManager
        print("✅ Database manager import: OK")
        
        # Test schema imports
        from src.schemas.clickhouse.raw_data_schemas import ClickhouseRawDataSchemas
        print("✅ ClickHouse schema imports: OK")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def validate_data_models():
    """Validate Pydantic data models"""
    print("\n🔍 Validating data models...")
    
    try:
        # Import the main module to get the models
        import main
        
        # Test TickData model
        tick_data = main.TickData(
            symbol="EURUSD",
            bid=1.1000,
            ask=1.1002
        )
        print("✅ TickData model: OK")
        
        # Test BatchTickRequest model
        batch_request = main.BatchTickRequest(
            ticks=[tick_data, tick_data]
        )
        print("✅ BatchTickRequest model: OK")
        
        # Test AccountInfoData model
        account_data = main.AccountInfoData(
            login=1016,
            balance=10000.0,
            equity=10000.0,
            margin=0.0,
            currency="USD",
            server="FBS-Real"
        )
        print("✅ AccountInfoData model: OK")
        
        # Test DataInsertionResponse model
        response_model = main.DataInsertionResponse(
            success=True,
            table="ticks",
            database="trading_data",
            records_inserted=1,
            insertion_duration_ms=10.0,
            message="Test successful"
        )
        print("✅ DataInsertionResponse model: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Data model validation failed: {e}")
        return False

def validate_app_creation():
    """Validate FastAPI app creation"""
    print("\n🔍 Validating FastAPI app creation...")
    
    try:
        # Import and create the app
        import main
        app = main.create_app()
        
        # Check that the app was created
        if app is None:
            print("❌ App creation failed: returned None")
            return False
        
        # Check that the app has the expected routes
        routes = [route.path for route in app.routes]
        
        expected_routes = [
            "/api/v1/clickhouse/ticks",
            "/api/v1/clickhouse/ticks/batch", 
            "/api/v1/clickhouse/account_info"
        ]
        
        missing_routes = [route for route in expected_routes if route not in routes]
        if missing_routes:
            print(f"❌ Missing routes: {missing_routes}")
            return False
        
        print("✅ FastAPI app creation: OK")
        print(f"✅ New endpoints registered: {len(expected_routes)}")
        
        return True
        
    except Exception as e:
        print(f"❌ App creation validation failed: {e}")
        return False

def validate_schemas():
    """Validate ClickHouse schemas"""
    print("\n🔍 Validating ClickHouse schemas...")
    
    try:
        from src.schemas.clickhouse.raw_data_schemas import ClickhouseRawDataSchemas
        
        # Test schema access
        schemas = ClickhouseRawDataSchemas.get_all_tables()
        
        required_tables = ["ticks", "account_info"]
        missing_tables = [table for table in required_tables if table not in schemas]
        
        if missing_tables:
            print(f"❌ Missing required tables: {missing_tables}")
            return False
        
        # Test individual schema access
        ticks_schema = ClickhouseRawDataSchemas.ticks()
        account_info_schema = ClickhouseRawDataSchemas.account_info()
        
        if not ticks_schema or not account_info_schema:
            print("❌ Schema SQL generation failed")
            return False
        
        print("✅ ClickHouse schemas: OK")
        print(f"✅ Available tables: {len(schemas)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Schema validation failed: {e}")
        return False

async def validate_database_manager():
    """Validate database manager functionality"""
    print("\n🔍 Validating database manager...")
    
    try:
        from src.business.database_manager import DatabaseManager
        
        # Create database manager instance
        db_manager = DatabaseManager()
        
        # Test basic methods exist
        if not hasattr(db_manager, 'insert_tick_data'):
            print("❌ Missing insert_tick_data method")
            return False
            
        if not hasattr(db_manager, 'insert_clickhouse_data'):
            print("❌ Missing insert_clickhouse_data method")
            return False
            
        print("✅ Database manager structure: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Database manager validation failed: {e}")
        return False

def main():
    """Run all validations"""
    print("🗄️ Database Service Endpoint Validation")
    print("=" * 50)
    
    validations = [
        ("Core Imports", validate_imports),
        ("Data Models", validate_data_models),
        ("FastAPI App", validate_app_creation),
        ("ClickHouse Schemas", validate_schemas),
        ("Database Manager", lambda: asyncio.run(validate_database_manager()))
    ]
    
    results = []
    
    for name, validation_func in validations:
        print(f"\n📋 {name} Validation")
        print("-" * 30)
        
        try:
            result = validation_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} validation crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for name, result in results:
        if result:
            print(f"✅ {name}: PASSED")
            passed += 1
        else:
            print(f"❌ {name}: FAILED")
            failed += 1
    
    print(f"\n🎯 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 ALL VALIDATIONS PASSED! The endpoints should work correctly.")
    else:
        print("⚠️  Some validations failed. Please fix the issues before testing.")
    
    return failed == 0

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Validation script failed: {e}")
        sys.exit(1)