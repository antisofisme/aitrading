#!/usr/bin/env python3
"""
Basic Usage Examples for Import Manager

Demonstrates common import scenarios for Phase 1 infrastructure migration.
"""

import asyncio
import json
import tempfile
from datetime import datetime
from pathlib import Path

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from import_manager import (
    ImportManager,
    ImportConfig,
    ImportType,
    create_import_manager,
    create_central_hub_integration,
    quick_import
)


def create_sample_data():
    """Create sample data files for demonstration"""
    temp_dir = Path(tempfile.gettempdir()) / "import_manager_examples"
    temp_dir.mkdir(exist_ok=True)
    
    # Sample JSON market data
    market_data = {
        "timestamp": "2025-01-09T10:00:00Z",
        "data_type": "market_tick",
        "records": [
            {"symbol": "EURUSD", "bid": 1.1234, "ask": 1.1236, "volume": 1000000},
            {"symbol": "GBPUSD", "bid": 1.3454, "ask": 1.3458, "volume": 750000},
            {"symbol": "USDJPY", "bid": 110.25, "ask": 110.28, "volume": 500000},
            {"symbol": "USDCHF", "bid": 0.9123, "ask": 0.9126, "volume": 300000}
        ]
    }
    
    json_file = temp_dir / "market_data.json"
    with open(json_file, 'w') as f:
        json.dump(market_data, f, indent=2)
    
    # Sample CSV trading signals
    csv_content = """timestamp,symbol,signal,confidence,price_target
2025-01-09T10:00:00Z,EURUSD,BUY,0.85,1.1250
2025-01-09T10:01:00Z,GBPUSD,SELL,0.78,1.3400
2025-01-09T10:02:00Z,USDJPY,HOLD,0.60,110.00
2025-01-09T10:03:00Z,USDCHF,BUY,0.90,0.9150
"""
    
    csv_file = temp_dir / "trading_signals.csv"
    with open(csv_file, 'w') as f:
        f.write(csv_content)
    
    # Sample configuration file
    config_data = {
        "trading_parameters": {
            "max_position_size": 100000,
            "risk_level": 0.02,
            "stop_loss_percent": 0.05,
            "take_profit_percent": 0.10
        },
        "api_settings": {
            "timeout": 30,
            "retries": 3,
            "rate_limit": 100
        },
        "data_sources": {
            "primary": "mt5",
            "backup": "yahoo_finance",
            "stream_enabled": True
        }
    }
    
    config_file = temp_dir / "trading_config.json"
    with open(config_file, 'w') as f:
        json.dump(config_data, f, indent=2)
    
    return {
        "market_data": str(json_file),
        "trading_signals": str(csv_file),
        "config": str(config_file),
        "temp_dir": str(temp_dir)
    }


async def example_basic_file_import():
    """Example: Basic file import"""
    print("\n=== Basic File Import Example ===")
    
    # Create sample data
    files = create_sample_data()
    
    # Create import manager
    manager = create_import_manager(files["temp_dir"])
    
    try:
        # Configure JSON import
        config = ImportConfig(
            import_id=f"market_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            import_type=ImportType.FILE,
            source_path=files["market_data"],
            format_type="json",
            validation_enabled=True
        )
        
        print(f"Starting import: {config.import_id}")
        
        # Execute import
        result = await manager.import_data(config)
        
        # Display results
        print(f"Import Status: {result.status.value}")
        print(f"Records Processed: {result.records_processed}")
        print(f"Records Failed: {result.records_failed}")
        print(f"Success Rate: {result.success_rate:.1f}%")
        print(f"Duration: {result.duration_seconds:.2f} seconds")
        print(f"File Format: {result.metadata.get('file_format', 'unknown')}")
        print(f"File Size: {result.metadata.get('file_size', 0)} bytes")
        
    except Exception as e:
        print(f"Error during import: {e}")


async def example_csv_import():
    """Example: CSV file import with validation"""
    print("\n=== CSV Import with Validation Example ===")
    
    files = create_sample_data()
    manager = create_import_manager(files["temp_dir"])
    
    try:
        # Configure CSV import with validation rules
        config = ImportConfig(
            import_id=f"trading_signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            import_type=ImportType.FILE,
            source_path=files["trading_signals"],
            format_type="csv",
            validation_enabled=True,
            metadata={"min_columns": 5}  # Require at least 5 columns
        )
        
        print(f"Starting CSV import: {config.import_id}")
        
        result = await manager.import_data(config)
        
        print(f"Import Status: {result.status.value}")
        print(f"Records Processed: {result.records_processed}")
        print(f"Columns: {result.metadata.get('columns', 0)}")
        print(f"Validation Passed: {result.metadata.get('validation_passed', False)}")
        
    except Exception as e:
        print(f"Error during CSV import: {e}")


async def example_stream_import():
    """Example: Stream import simulation"""
    print("\n=== Stream Import Example ===")
    
    files = create_sample_data()
    manager = create_import_manager(files["temp_dir"])
    
    try:
        # Configure stream import
        config = ImportConfig(
            import_id=f"stream_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            import_type=ImportType.STREAM,
            source_path="stream://market/live_data",
            format_type="json",
            batch_size=1000
        )
        
        print(f"Starting stream import: {config.import_id}")
        print("Processing streaming data...")
        
        result = await manager.import_data(config)
        
        print(f"Stream Import Status: {result.status.value}")
        print(f"Records Processed: {result.records_processed}")
        print(f"Batch Size: {config.batch_size}")
        
    except Exception as e:
        print(f"Error during stream import: {e}")


async def example_central_hub_integration():
    """Example: Central Hub integration"""
    print("\n=== Central Hub Integration Example ===")
    
    files = create_sample_data()
    
    # Create Central Hub integration
    integration = create_central_hub_integration(files["temp_dir"])
    
    try:
        # Import market data
        print("Importing market data via Central Hub...")
        market_result = await integration.import_market_data(
            source_path=files["market_data"],
            format_type="json"
        )
        
        print(f"Market Data Import: {market_result.status.value}")
        print(f"Records: {market_result.records_processed}")
        print(f"Data Type: {market_result.metadata.get('data_type')}")
        print(f"Source: {market_result.metadata.get('source')}")
        
        # Import configuration
        print("\nImporting configuration via Central Hub...")
        config_result = await integration.import_configuration(
            config_path=files["config"]
        )
        
        print(f"Configuration Import: {config_result.status.value}")
        print(f"Records: {config_result.records_processed}")
        
        # Import trading signals (streaming)
        print("\nImporting trading signals stream...")
        signals_result = await integration.import_trading_signals(
            stream_source="stream://trading/signals/live"
        )
        
        print(f"Trading Signals Import: {signals_result.status.value}")
        print(f"Records: {signals_result.records_processed}")
        
    except Exception as e:
        print(f"Error during Central Hub integration: {e}")


async def example_quick_import():
    """Example: Quick import convenience function"""
    print("\n=== Quick Import Example ===")
    
    files = create_sample_data()
    
    try:
        # Quick import - simplest way to import a file
        print("Using quick import function...")
        
        result = await quick_import(
            source_path=files["market_data"],
            import_type=ImportType.FILE,
            format_type="json"
        )
        
        print(f"Quick Import Status: {result.status.value}")
        print(f"Records Processed: {result.records_processed}")
        print(f"Import ID: {result.import_id}")
        
    except Exception as e:
        print(f"Error during quick import: {e}")


async def example_monitoring_and_statistics():
    """Example: Monitoring imports and getting statistics"""
    print("\n=== Monitoring and Statistics Example ===")
    
    files = create_sample_data()
    manager = create_import_manager(files["temp_dir"])
    
    try:
        # Start multiple imports
        import_ids = []
        
        for i in range(3):
            config = ImportConfig(
                import_id=f"monitor_test_{i}_{datetime.now().strftime('%H%M%S')}",
                import_type=ImportType.FILE,
                source_path=files["market_data"],
                format_type="json"
            )
            
            # Start import (don't await yet)
            import_task = asyncio.create_task(manager.import_data(config))
            import_ids.append((config.import_id, import_task))
        
        # Monitor active imports
        print("Active imports:")
        active_imports = manager.list_active_imports()
        for import_result in active_imports:
            print(f"  {import_result.import_id}: {import_result.status.value}")
        
        # Wait for imports to complete
        for import_id, task in import_ids:
            result = await task
            print(f"Completed {import_id}: {result.status.value}")
        
        # Get statistics
        print("\nImport Manager Statistics:")
        stats = manager.get_statistics()
        print(f"  Total imports: {stats['total_imports']}")
        print(f"  Completed: {stats['completed']}")
        print(f"  Failed: {stats['failed']}")
        print(f"  Success rate: {stats['success_rate']:.1f}%")
        
        # Health check
        print("\nHealth Check:")
        health = await manager.health_check()
        print(f"  Status: {health['status']}")
        print(f"  Active imports: {health['active_imports']}")
        print(f"  Configuration loaded: {health['configuration_loaded']}")
        
    except Exception as e:
        print(f"Error during monitoring: {e}")


async def example_error_handling():
    """Example: Error handling and recovery"""
    print("\n=== Error Handling Example ===")
    
    files = create_sample_data()
    manager = create_import_manager(files["temp_dir"])
    
    # Test file not found error
    try:
        config = ImportConfig(
            import_id="error_test_file_not_found",
            import_type=ImportType.FILE,
            source_path="/nonexistent/file.json",
            format_type="json"
        )
        
        print("Testing file not found error...")
        result = await manager.import_data(config)
        
        print(f"Result status: {result.status.value}")
        print(f"Error message: {result.error_message}")
        
    except Exception as e:
        print(f"Caught exception: {e}")
    
    # Test invalid JSON error
    try:
        # Create invalid JSON file
        invalid_file = Path(files["temp_dir"]) / "invalid.json"
        with open(invalid_file, 'w') as f:
            f.write('{"invalid": json}')
        
        config = ImportConfig(
            import_id="error_test_invalid_json",
            import_type=ImportType.FILE,
            source_path=str(invalid_file),
            format_type="json"
        )
        
        print("\nTesting invalid JSON error...")
        result = await manager.import_data(config)
        
        print(f"Result status: {result.status.value}")
        print(f"Error message: {result.error_message}")
        
    except Exception as e:
        print(f"Caught exception: {e}")


async def main():
    """Run all examples"""
    print("Import Manager Examples - Phase 1 Infrastructure Migration")
    print("=" * 60)
    
    try:
        await example_basic_file_import()
        await example_csv_import()
        await example_stream_import()
        await example_central_hub_integration()
        await example_quick_import()
        await example_monitoring_and_statistics()
        await example_error_handling()
        
        print("\n=== All Examples Completed ===")
        
    except Exception as e:
        print(f"Error running examples: {e}")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())