#!/usr/bin/env python3
"""
Startup script for database service with the new endpoints
"""

import asyncio
import uvicorn
import signal
import sys
from pathlib import Path

# Add src path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def start_database_service():
    """Start the database service"""
    print("🗄️ Starting Database Service with New Endpoints")
    print("=" * 60)
    print("🎯 Available Endpoints:")
    print("  📍 POST /api/v1/clickhouse/ticks - Insert single tick")
    print("  📊 POST /api/v1/clickhouse/ticks/batch - Insert batch ticks")
    print("  💰 POST /api/v1/clickhouse/account_info - Insert account info")
    print("  🏥 GET /health - Health check")
    print("  📋 GET /status - Detailed status")
    print("  📖 GET /docs - API documentation")
    print("=" * 60)
    
    try:
        # Import the app from main
        from main import database_service_app
        
        # Configure uvicorn
        config = uvicorn.Config(
            app=database_service_app,
            host="0.0.0.0",
            port=8008,
            log_level="info",
            reload=False,
            workers=1
        )
        
        # Create server
        server = uvicorn.Server(config)
        
        print("🚀 Database service starting on http://localhost:8008")
        print("📖 API documentation available at http://localhost:8008/docs")
        print("\n💡 Test the endpoints with:")
        print("  python test_new_endpoints.py")
        print("\n❌ Press Ctrl+C to stop")
        print("=" * 60)
        
        # Run the server
        server.run()
        
    except KeyboardInterrupt:
        print("\n\n👋 Database service stopped by user")
    except Exception as e:
        print(f"\n❌ Database service failed to start: {e}")
        print("\n🔧 Try running the validation script first:")
        print("  python validate_endpoints.py")
        sys.exit(1)

if __name__ == "__main__":
    start_database_service()