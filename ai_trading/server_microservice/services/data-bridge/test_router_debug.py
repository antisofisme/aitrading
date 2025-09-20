#!/usr/bin/env python3
"""
Debug script to test economic calendar router registration
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from fastapi import FastAPI
from src.api.economic_calendar_endpoints import router as economic_calendar_router

# Create test app
app = FastAPI(title="Test App")

# Include the router
app.include_router(economic_calendar_router, prefix="/api/v1/economic_calendar", tags=["Economic Calendar"])

# Print all routes
print("=== REGISTERED ROUTES ===")
for route in app.routes:
    if hasattr(route, 'path'):
        methods = getattr(route, 'methods', ['N/A'])
        print(f"{methods} {route.path}")

# Check specific routes we need
target_routes = ["/api/v1/economic_calendar/health", "/api/v1/economic_calendar/sources/health"]
print(f"\n=== CHECKING TARGET ROUTES ===")
for target in target_routes:
    found = any(route.path == target for route in app.routes if hasattr(route, 'path'))
    print(f"{target}: {'✅ FOUND' if found else '❌ MISSING'}")

# Run a quick test server
if __name__ == "__main__":
    import uvicorn
    print(f"\n=== TESTING SERVER ===")
    print("Starting test server on port 8888...")
    print("Test endpoints:")
    print("- http://localhost:8888/api/v1/economic_calendar/health")
    print("- http://localhost:8888/api/v1/economic_calendar/sources/health")
    
    uvicorn.run(app, host="127.0.0.1", port=8888, log_level="info")