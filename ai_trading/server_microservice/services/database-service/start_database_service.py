#!/usr/bin/env python3
"""
Simple startup script for the database service
For testing and development purposes
"""

import asyncio
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from main import DatabaseServiceApp

async def main():
    """Start the database service"""
    print("🚀 Starting Database Service (port 8008)")
    print("=" * 50)
    
    # Create and initialize the app
    app_instance = DatabaseServiceApp()
    
    try:
        # Initialize the service
        await app_instance.initialize()
        print("✅ Database service initialized successfully")
        
        # Start the server (this would normally be done by uvicorn)
        print("🔧 Note: This script initializes the service components.")
        print("💡 To start the full HTTP server, run: python main.py")
        print("📊 Or use Docker: docker-compose up database-service")
        
        # Test basic functionality
        await test_basic_functionality(app_instance)
        
    except Exception as e:
        print(f"❌ Failed to initialize database service: {e}")
        raise
    finally:
        # Cleanup
        try:
            await app_instance.shutdown()
            print("✅ Database service shutdown completed")
        except Exception as e:
            print(f"⚠️  Error during shutdown: {e}")

async def test_basic_functionality(app_instance):
    """Test basic service functionality"""
    try:
        print("\n🔍 Testing basic functionality...")
        
        # Test database manager
        db_manager = app_instance.database_manager
        
        # Test health status
        health = await db_manager.get_health_status()
        print(f"   Database health: {health}")
        
        # Test schema retrieval
        schemas = await db_manager.get_all_schemas()
        clickhouse_tables = schemas.get('clickhouse', {})
        total_tables = sum(len(tables) for tables in clickhouse_tables.values())
        print(f"   Available ClickHouse tables: {total_tables}")
        
        # Test tick data processing (without actual insertion)
        sample_tick = {
            "symbol": "EURUSD",
            "timestamp": "2025-01-09T12:00:00.123Z",
            "bid": 1.04125,
            "ask": 1.04128,
            "volume": 1000.0
        }
        
        processed_tick = db_manager._process_tick_data(sample_tick, "FBS-Demo", "demo")
        print(f"   Tick processing test: {processed_tick['symbol']} @ {processed_tick['timestamp']}")
        
        print("✅ Basic functionality test completed")
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())