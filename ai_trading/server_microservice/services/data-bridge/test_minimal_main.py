#!/usr/bin/env python3
"""
Minimal test main.py to isolate router registration issue
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from fastapi import FastAPI

# Import routers exactly like main.py
from src.api.mt5_websocket_endpoints import router as mt5_websocket_router
from src.api.deduplication_endpoints import router as deduplication_router  
from src.api.economic_calendar_endpoints import router as economic_calendar_router

def create_minimal_app() -> FastAPI:
    """Create minimal FastAPI application to test router registration"""
    
    app = FastAPI(
        title="Data Bridge Microservice - Test",
        description="Test app for route registration debugging",
        version="2.0.0"
    )
    
    # Include routers in exact same order as main.py
    print("Including mt5_websocket_router...")
    app.include_router(mt5_websocket_router, prefix="/api/v1", tags=["MT5 WebSocket"])
    
    print("Including deduplication_router...")
    app.include_router(deduplication_router, prefix="/api/v1", tags=["Deduplication Management"])
    
    print("Including economic_calendar_router...")
    app.include_router(economic_calendar_router, prefix="/api/v1/economic_calendar", tags=["Economic Calendar"])
    
    return app

if __name__ == "__main__":
    import uvicorn
    
    app = create_minimal_app()
    
    # Print route analysis
    print("\n=== ROUTE ANALYSIS ===")
    economic_routes = []
    all_routes = []
    
    for route in app.routes:
        if hasattr(route, 'path'):
            route_info = {
                'path': route.path,
                'methods': list(getattr(route, 'methods', [])),
                'tags': getattr(route, 'tags', [])
            }
            all_routes.append(route_info)
            
            if '/economic_calendar' in route.path:
                economic_routes.append(route_info)
    
    print(f"\n📊 TOTAL ROUTES: {len(all_routes)}")
    print(f"📊 ECONOMIC CALENDAR ROUTES: {len(economic_routes)}")
    
    # Check target routes
    target_routes = ["/api/v1/economic_calendar/health", "/api/v1/economic_calendar/sources/health"]
    for target in target_routes:
        found_routes = [r for r in economic_routes if r['path'] == target]
        if found_routes:
            route = found_routes[0]
            print(f"✅ {target} - tags: {route['tags']}")
        else:
            print(f"❌ {target} - NOT FOUND")
    
    # Run test server
    print(f"\n🚀 Starting test server on port 8889...")
    uvicorn.run(app, host="127.0.0.1", port=8889, log_level="info")