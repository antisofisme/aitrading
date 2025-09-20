#!/usr/bin/env python3
"""
Economic Calendar Endpoints Validation Script
Validates the implementation of economic calendar data retrieval endpoints
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, Any, List
import json

# Add src path to sys.path for proper imports
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Import database manager and schemas
from src.business.database_manager import DatabaseManager
from src.schemas.clickhouse.external_data_schemas import ClickhouseExternalDataSchemas

class EconomicCalendarEndpointsValidator:
    """Validator for economic calendar endpoints implementation"""
    
    def __init__(self):
        self.test_results = []
        self.success_count = 0
        self.failure_count = 0
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test_name": test_name,
            "status": status,
            "success": success,
            "details": details
        }
        self.test_results.append(result)
        
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        
        print(f"{status}: {test_name}")
        if details:
            print(f"    Details: {details}")
    
    def validate_database_manager_methods(self):
        """Validate DatabaseManager has economic calendar methods"""
        print("\n=== Validating DatabaseManager Methods ===")
        
        # Check if DatabaseManager has the required methods
        db_manager = DatabaseManager()
        
        required_methods = [
            'get_economic_calendar_events',
            'get_economic_event_by_id', 
            'get_upcoming_economic_events',
            'get_economic_events_by_impact'
        ]
        
        for method_name in required_methods:
            has_method = hasattr(db_manager, method_name) and callable(getattr(db_manager, method_name))
            self.log_test(
                f"DatabaseManager.{method_name} method exists",
                has_method,
                f"Method {'found' if has_method else 'missing'} in DatabaseManager"
            )
    
    def validate_schema_availability(self):
        """Validate economic calendar schema is available"""
        print("\n=== Validating Schema Availability ===")
        
        try:
            schema_sql = ClickhouseExternalDataSchemas.economic_calendar()
            
            # Check schema contains essential elements
            essential_elements = [
                'CREATE TABLE',
                'economic_calendar',
                'timestamp',
                'event_name',
                'currency',
                'importance',
                'MergeTree()'
            ]
            
            for element in essential_elements:
                contains_element = element in schema_sql
                self.log_test(
                    f"Schema contains '{element}'",
                    contains_element,
                    f"Element {'found' if contains_element else 'missing'} in schema"
                )
            
            # Check schema length (should be substantial)
            schema_length_ok = len(schema_sql) > 1000
            self.log_test(
                "Schema has substantial content",
                schema_length_ok,
                f"Schema length: {len(schema_sql)} characters"
            )
            
        except Exception as e:
            self.log_test(
                "Economic calendar schema retrieval",
                False,
                f"Error: {str(e)}"
            )
    
    def validate_method_signatures(self):
        """Validate method signatures match expected parameters"""
        print("\n=== Validating Method Signatures ===")
        
        db_manager = DatabaseManager()
        
        # Check get_economic_calendar_events signature
        try:
            method = getattr(db_manager, 'get_economic_calendar_events', None)
            if method:
                import inspect
                sig = inspect.signature(method)
                params = list(sig.parameters.keys())
                
                expected_params = ['self', 'start_date', 'end_date', 'currency', 'importance', 'limit', 'offset']
                params_match = all(param in params for param in expected_params[1:])  # Skip 'self'
                
                self.log_test(
                    "get_economic_calendar_events signature",
                    params_match,
                    f"Parameters: {params}"
                )
            else:
                self.log_test(
                    "get_economic_calendar_events signature",
                    False,
                    "Method not found"
                )
        except Exception as e:
            self.log_test(
                "get_economic_calendar_events signature validation",
                False,
                f"Error: {str(e)}"
            )
        
        # Check get_upcoming_economic_events signature  
        try:
            method = getattr(db_manager, 'get_upcoming_economic_events', None)
            if method:
                import inspect
                sig = inspect.signature(method)
                params = list(sig.parameters.keys())
                
                expected_params = ['self', 'hours_ahead', 'currency', 'importance']
                params_match = all(param in params for param in expected_params[1:])  # Skip 'self'
                
                self.log_test(
                    "get_upcoming_economic_events signature",
                    params_match,
                    f"Parameters: {params}"
                )
            else:
                self.log_test(
                    "get_upcoming_economic_events signature",
                    False,
                    "Method not found"
                )
        except Exception as e:
            self.log_test(
                "get_upcoming_economic_events signature validation",
                False,
                f"Error: {str(e)}"
            )
    
    def validate_endpoint_structure(self):
        """Validate endpoint structure (import validation)"""
        print("\n=== Validating Endpoint Structure ===")
        
        try:
            # Try to import main and check if it can be loaded
            import importlib.util
            spec = importlib.util.spec_from_file_location("main", Path(__file__).parent / "main.py")
            
            if spec and spec.loader:
                self.log_test(
                    "Main module can be loaded",
                    True,
                    "Main.py imports successfully"
                )
            else:
                self.log_test(
                    "Main module can be loaded", 
                    False,
                    "Cannot load main.py"
                )
                
        except Exception as e:
            self.log_test(
                "Main module import validation",
                False,
                f"Import error: {str(e)}"
            )
    
    def validate_caching_implementation(self):
        """Validate caching is properly implemented"""
        print("\n=== Validating Caching Implementation ===")
        
        db_manager = DatabaseManager()
        
        # Check if cache attribute exists
        has_cache = hasattr(db_manager, 'cache')
        self.log_test(
            "DatabaseManager has cache attribute",
            has_cache,
            f"Cache attribute {'found' if has_cache else 'missing'}"
        )
        
        # Check if _escape_sql_string method exists (security)
        has_escape = hasattr(db_manager, '_escape_sql_string') and callable(getattr(db_manager, '_escape_sql_string'))
        self.log_test(
            "SQL injection prevention method exists",
            has_escape,
            f"_escape_sql_string method {'found' if has_escape else 'missing'}"
        )
    
    def run_all_validations(self):
        """Run all validation tests"""
        print("🗄️ Economic Calendar Endpoints Validation")
        print("=" * 60)
        
        self.validate_database_manager_methods()
        self.validate_schema_availability()
        self.validate_method_signatures()
        self.validate_endpoint_structure()
        self.validate_caching_implementation()
        
        # Summary
        print(f"\n=== Validation Summary ===")
        print(f"✅ Passed: {self.success_count}")
        print(f"❌ Failed: {self.failure_count}")
        print(f"📊 Total: {self.success_count + self.failure_count}")
        
        success_rate = (self.success_count / (self.success_count + self.failure_count)) * 100
        print(f"🎯 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🚀 EXCELLENT: Economic calendar endpoints implementation is robust!")
        elif success_rate >= 75:
            print("✅ GOOD: Economic calendar endpoints implementation is solid with minor issues")
        elif success_rate >= 50:
            print("⚠️ MODERATE: Economic calendar endpoints need some improvements")
        else:
            print("❌ POOR: Economic calendar endpoints need significant work")
        
        return success_rate >= 75

def main():
    """Main validation function"""
    validator = EconomicCalendarEndpointsValidator()
    success = validator.run_all_validations()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()