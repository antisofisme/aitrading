#!/usr/bin/env python3
"""
Debug script to replicate the exact router registration process from main.py
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from fastapi import FastAPI

# Import routers exactly like main.py
print("=== IMPORTING ROUTERS ===")
try:
    from src.api.mt5_websocket_endpoints import router as mt5_websocket_router
    print("✅ mt5_websocket_router imported")
    
    from src.api.deduplication_endpoints import router as deduplication_router
    print("✅ deduplication_router imported")
    
    from src.api.economic_calendar_endpoints import router as economic_calendar_router
    print("✅ economic_calendar_router imported")
    
except Exception as e:
    print(f"❌ Import error: {e}")

# Create FastAPI app exactly like main.py
print("\n=== CREATING FASTAPI APP ===")
app = FastAPI(
    title="Data Bridge Microservice",
    description="Real-time market data ingestion and MT5 bridge service", 
    version="2.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

print("=== BEFORE ROUTER INCLUSION ===")
print(f"Initial routes count: {len(app.routes)}")

# Include routers exactly like main.py
print("\n=== INCLUDING ROUTERS ===")
try:
    print("Including mt5_websocket_router...")
    app.include_router(mt5_websocket_router, prefix="/api/v1", tags=["MT5 WebSocket"])
    print(f"Routes after MT5 WebSocket: {len(app.routes)}")
    
    print("Including deduplication_router...")
    app.include_router(deduplication_router, prefix="/api/v1", tags=["Deduplication Management"])
    print(f"Routes after Deduplication: {len(app.routes)}")
    
    print("Including economic_calendar_router...")
    app.include_router(economic_calendar_router, prefix="/api/v1/economic_calendar", tags=["Economic Calendar"])
    print(f"Routes after Economic Calendar: {len(app.routes)}")
    
except Exception as e:
    print(f"❌ Router inclusion error: {e}")
    import traceback
    traceback.print_exc()

print("\n=== FINAL ROUTE ANALYSIS ===")
economic_calendar_routes = []
mt5_routes = []
dedup_routes = []
other_routes = []

for route in app.routes:
    if hasattr(route, 'path'):
        path = route.path
        methods = getattr(route, 'methods', set())
        tags = getattr(route, 'tags', [])
        
        route_info = {
            'path': path,
            'methods': list(methods) if methods else [],
            'tags': tags
        }
        
        if '/economic_calendar' in path:
            economic_calendar_routes.append(route_info)
        elif '/ws/' in path:
            mt5_routes.append(route_info)
        elif '/deduplication' in path:
            dedup_routes.append(route_info)
        else:
            other_routes.append(route_info)

print(f"\n📊 ECONOMIC CALENDAR ROUTES ({len(economic_calendar_routes)}):")
for route in economic_calendar_routes:
    print(f"  {route['methods']} {route['path']} [tags: {route['tags']}]")

print(f"\n📊 MT5 WEBSOCKET ROUTES ({len(mt5_routes)}):")
for route in mt5_routes:
    print(f"  {route['methods']} {route['path']} [tags: {route['tags']}]")

print(f"\n📊 DEDUPLICATION ROUTES ({len(dedup_routes)}):")
for route in dedup_routes:
    print(f"  {route['methods']} {route['path']} [tags: {route['tags']}]")

print(f"\n📊 OTHER ROUTES ({len(other_routes)}):")
for route in other_routes:
    print(f"  {route['methods']} {route['path']} [tags: {route['tags']}]")

# Check specific target routes
target_routes = ["/api/v1/economic_calendar/health", "/api/v1/economic_calendar/sources/health"]
print(f"\n=== TARGET ROUTE CHECK ===")
for target in target_routes:
    found = any(route.path == target for route in app.routes if hasattr(route, 'path'))
    matching_routes = [r for r in app.routes if hasattr(r, 'path') and r.path == target]
    if found and matching_routes:
        route = matching_routes[0]
        tags = getattr(route, 'tags', [])
        print(f"{target}: ✅ FOUND [tags: {tags}]")
    else:
        print(f"{target}: ❌ MISSING")

# Generate OpenAPI spec
print(f"\n=== OPENAPI SPEC GENERATION ===")
try:
    openapi_spec = app.openapi()
    paths = openapi_spec.get('paths', {})
    
    print(f"Paths in OpenAPI spec: {len(paths)}")
    for path in target_routes:
        if path in paths:
            print(f"  {path}: ✅ IN OPENAPI SPEC")
        else:
            print(f"  {path}: ❌ NOT IN OPENAPI SPEC")
            
except Exception as e:
    print(f"❌ OpenAPI generation error: {e}")
    import traceback
    traceback.print_exc()