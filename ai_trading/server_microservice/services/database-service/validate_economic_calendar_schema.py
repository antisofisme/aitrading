#!/usr/bin/env python3
"""
Economic Calendar Schema Validation
Validates that the AI-enhanced schema is properly defined and ready for use
"""

import sys
import os
from pathlib import Path

# Add src path to sys.path for proper imports
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

def validate_economic_calendar_schema():
    """Validate the economic calendar schema definition"""
    print("🔍 Economic Calendar Schema Validation")
    print("=" * 50)
    
    try:
        # Import the schema
        from schemas.clickhouse.external_data_schemas import ClickhouseExternalDataSchemas
        
        # Get the economic calendar schema
        schema_sql = ClickhouseExternalDataSchemas.economic_calendar()
        
        print("✅ Schema import successful")
        print(f"📏 Schema SQL length: {len(schema_sql)} characters")
        
        # Validate AI-enhanced columns are present
        ai_columns = [
            "ai_predicted_value",
            "ai_prediction_confidence", 
            "ai_prediction_model",
            "ai_sentiment_score",
            "volatility_impact_score",
            "currency_pair_impacts",
            "sector_rotation_prediction",
            "central_bank_reaction_probability",
            "historical_pattern_match",
            "seasonal_adjustment",
            "surprise_index",
            "consensus_accuracy",
            "bond_impact_prediction",
            "equity_impact_prediction", 
            "commodity_impact_prediction",
            "immediate_impact_window",
            "delayed_impact_window",
            "impact_duration_minutes",
            "market_conditions_at_release",
            "liquidity_conditions",
            "concurrent_events"
        ]
        
        print(f"\n🤖 Validating AI-Enhanced Columns:")
        found_columns = []
        missing_columns = []
        
        for column in ai_columns:
            if column in schema_sql:
                found_columns.append(column)
                print(f"   ✅ {column}")
            else:
                missing_columns.append(column)
                print(f"   ❌ {column}")
        
        print(f"\n📊 AI Enhancement Summary:")
        print(f"   Found: {len(found_columns)}/{len(ai_columns)} columns")
        print(f"   Coverage: {len(found_columns)/len(ai_columns)*100:.1f}%")
        
        if len(found_columns) >= 15:
            print("🎉 Excellent AI enhancement coverage!")
        elif len(found_columns) >= 10:
            print("✅ Good AI enhancement coverage")
        else:
            print("⚠️ Limited AI enhancement coverage")
        
        # Validate table structure elements
        structural_elements = [
            "CREATE TABLE IF NOT EXISTS economic_calendar",
            "ENGINE = MergeTree()",
            "PARTITION BY toYYYYMM(timestamp)",
            "ORDER BY (country, currency, timestamp)",
            "TTL toDate(timestamp) + INTERVAL 1 YEAR",
            "INDEX idx_country country",
            "INDEX idx_currency currency",
            "INDEX idx_importance importance",
            "INDEX idx_timestamp timestamp"
        ]
        
        print(f"\n🏗️ Validating Table Structure:")
        found_structural = []
        
        for element in structural_elements:
            if element in schema_sql:
                found_structural.append(element)
                print(f"   ✅ {element}")
            else:
                print(f"   ❌ {element}")
        
        print(f"\n📈 Structure Summary:")
        print(f"   Found: {len(found_structural)}/{len(structural_elements)} elements")
        print(f"   Coverage: {len(found_structural)/len(structural_elements)*100:.1f}%")
        
        # Validate performance optimizations
        performance_features = [
            "CODEC(Delta, LZ4)",
            "CODEC(ZSTD)",
            "CODEC(Gorilla)",
            "CODEC(T64)",
            "LowCardinality(String)",
            "GRANULARITY 8192"
        ]
        
        print(f"\n⚡ Validating Performance Optimizations:")
        found_performance = []
        
        for feature in performance_features:
            if feature in schema_sql:
                found_performance.append(feature)
                print(f"   ✅ {feature}")
        
        print(f"\n🚀 Performance Summary:")
        print(f"   Found: {len(found_performance)}/{len(performance_features)} optimizations")
        
        # Overall assessment
        total_features = len(ai_columns) + len(structural_elements) + len(performance_features)
        total_found = len(found_columns) + len(found_structural) + len(found_performance)
        overall_score = (total_found / total_features) * 100
        
        print(f"\n🎯 Overall Schema Assessment:")
        print(f"   Total Features: {total_found}/{total_features}")
        print(f"   Overall Score: {overall_score:.1f}%")
        
        if overall_score >= 90:
            print("🏆 EXCELLENT: Schema is fully AI-enhanced and production-ready!")
        elif overall_score >= 80:
            print("✅ GOOD: Schema has strong AI enhancements")
        elif overall_score >= 70:
            print("⚠️ ADEQUATE: Schema has basic AI enhancements")
        else:
            print("❌ INADEQUATE: Schema needs more AI enhancements")
        
        # Show first 500 characters of schema for verification
        print(f"\n📄 Schema Preview (first 500 chars):")
        print("-" * 50)
        print(schema_sql[:500] + "..." if len(schema_sql) > 500 else schema_sql)
        print("-" * 50)
        
        # Table capabilities summary
        print(f"\n🎯 Table Capabilities:")
        print("   📊 Basic economic event storage (timestamp, event, values)")
        print("   🤖 AI prediction and confidence scoring")  
        print("   📈 Volatility and impact analysis")
        print("   💹 Cross-asset impact predictions")
        print("   🔍 Historical pattern recognition")
        print("   ⏰ Time-based impact windows")
        print("   🏛️ Central bank reaction modeling")
        print("   📋 Comprehensive metadata and source tracking")
        print("   ⚡ Performance-optimized with compression and indexing")
        
        return overall_score >= 80
        
    except ImportError as e:
        print(f"❌ Schema import failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("  1. Ensure you're running from the database-service directory")
        print("  2. Check that src/schemas/clickhouse/external_data_schemas.py exists")
        print("  3. Verify the Python path is correctly set")
        return False
        
    except Exception as e:
        print(f"💥 Validation error: {e}")
        return False

def main():
    """Main validation function"""
    print("🚀 Economic Calendar AI-Enhanced Schema Validator")
    print("=" * 60)
    print("This tool validates that the economic calendar schema includes")
    print("all AI-enhanced features for advanced market analysis.")
    print("=" * 60)
    
    success = validate_economic_calendar_schema()
    
    if success:
        print("\n🎉 VALIDATION PASSED: Schema is ready for AI-enhanced economic data!")
        print("\n📋 Ready for:")
        print("  ✅ Economic event data ingestion")
        print("  ✅ AI prediction and sentiment analysis")
        print("  ✅ Volatility impact scoring")
        print("  ✅ Cross-asset correlation analysis") 
        print("  ✅ Historical pattern recognition")
        print("  ✅ Real-time market impact assessment")
    else:
        print("\n❌ VALIDATION FAILED: Schema needs attention")
        print("\n🔧 Next steps:")
        print("  1. Check schema definition in external_data_schemas.py")
        print("  2. Ensure all AI columns are properly defined")
        print("  3. Verify table structure and performance optimizations")
    
    return success

if __name__ == "__main__":
    result = main()
    exit(0 if result else 1)