"""
API Gateway with Microservice Routing
Routes client requests to appropriate microservices
"""

import uvicorn
import sys
import os
import time
import httpx
import asyncio
import websockets
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
from starlette.responses import StreamingResponse

# API Gateway with microservice routing
app = FastAPI(title="API Gateway", version="2.0.0-microservice")

# Service endpoints mapping
SERVICES = {
    "data-bridge": "http://data-bridge:8001",
    "ai-provider": "http://ai-provider:8005", 
    "user-service": "http://user-service:8009",
    "database-service": "http://database-service:8008",
    "ai-orchestration": "http://ai-orchestration:8003"
}

# Basic CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Simple state
start_time = time.time()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "api-gateway",
        "version": "2.0.0-simple",
        "status": "operational",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Simple health check"""
    uptime = time.time() - start_time
    
    return {
        "status": "healthy",
        "service": "api-gateway",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": uptime,
        "version": "2.0.0-simple",
        "environment": "development"
    }

@app.get("/status")
async def detailed_status():
    """Detailed status with microservice health"""
    uptime = time.time() - start_time
    
    # Check microservice health
    services_health = {}
    async with httpx.AsyncClient(timeout=5.0) as client:
        for service_name, service_url in SERVICES.items():
            try:
                response = await client.get(f"{service_url}/health")
                services_health[service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "url": service_url
                }
            except Exception as e:
                services_health[service_name] = {
                    "status": "unreachable",
                    "error": str(e)[:100],
                    "url": service_url
                }
    
    return {
        "service": "api-gateway",
        "status": "running",
        "uptime_seconds": uptime,
        "version": "2.0.0-microservice", 
        "environment": "development",
        "timestamp": datetime.now().isoformat(),
        "microservices": services_health
    }

# =============================================================================
# CLIENT-SIDE ROUTING FOR MICROSERVICES
# =============================================================================

# Simple test WebSocket endpoint at root level
@app.websocket("/ws/test")
async def websocket_test_simple(websocket: WebSocket):
    """Simple WebSocket test endpoint"""
    print(f"🔌 WebSocket connection attempt from {websocket.client}")
    try:
        await websocket.accept()
        print("✅ WebSocket accepted successfully")
        await websocket.send_text("Hello WebSocket!")
        
        # Simple echo loop
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")

# Test endpoint with different path 
@app.websocket("/api/v1/ws/test")
async def websocket_test(websocket: WebSocket):
    """Simple WebSocket test endpoint"""
    print(f"🔌 WebSocket /api/v1/ws/test connection from {websocket.client}")
    await websocket.accept()
    print("✅ WebSocket accepted")
    await websocket.send_json({
        "status": "connected", 
        "message": "API Gateway WebSocket test successful",
        "timestamp": time.time()
    })
    
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except:
        pass

# ================================================================================
# WEBSOCKET STREAMING ENDPOINTS - Resource-based routing
# ================================================================================

@app.websocket("/api/stream/market-data")
async def websocket_market_data_stream(websocket: WebSocket):
    """Real-time market data stream (ticks, prices, volume)"""
    await websocket.accept()
    
    try:
        # Send initial connection from API Gateway
        await websocket.send_json({
            "status": "connecting",
            "service": "api-gateway", 
            "message": "Establishing connection to data-bridge",
            "timestamp": time.time()
        })
        
        # Connect to data-bridge WebSocket directly with simpler approach
        data_bridge_ws_url = "ws://data-bridge:8001/api/v1/ws"
        
        try:
            async with websockets.connect(data_bridge_ws_url) as data_bridge_ws:
                # Send connection success
                await websocket.send_json({
                    "status": "connected",
                    "service": "api-gateway", 
                    "stream_type": "market-data",
                    "message": "Real-time market data stream established",
                    "timestamp": datetime.now().isoformat(),
                    "data_source": "data-bridge"
                })
                
                async def forward_to_data_bridge():
                    """Forward messages from client to data-bridge"""
                    try:
                        while True:
                            message = await websocket.receive_text()
                            await data_bridge_ws.send(message)
                    except Exception as e:
                        print(f"Forward to data-bridge error: {e}")
                
                async def forward_to_client():
                    """Forward messages from data-bridge to client"""
                    try:
                        async for message in data_bridge_ws:
                            await websocket.send_text(message)
                    except Exception as e:
                        print(f"Forward to client error: {e}")
                
                # Run both forwarding tasks concurrently
                await asyncio.gather(
                    forward_to_data_bridge(),
                    forward_to_client(),
                    return_exceptions=True
                )
                
        except Exception as conn_error:
            await websocket.send_json({
                "status": "error",
                "service": "api-gateway",
                "message": f"Could not connect to data-bridge: {str(conn_error)}",
                "fallback": "Direct connection to data-bridge:8001/websocket/ws required",
                "timestamp": time.time()
            })
            
    except Exception as e:
        try:
            await websocket.send_json({
                "status": "error",
                "service": "api-gateway",
                "message": f"WebSocket proxy failed: {str(e)}",
                "timestamp": time.time()
            })
        except:
            pass


@app.websocket("/api/stream/trading")
async def websocket_trading_stream(websocket: WebSocket):
    """Real-time trading signals and execution updates"""
    await websocket.accept()
    
    try:
        await websocket.send_json({
            "status": "connected",
            "stream_type": "trading",
            "message": "Trading stream established - signals and executions",
            "timestamp": datetime.now().isoformat(),
            "features": ["signals", "executions", "risk_alerts"]
        })
        
        # Echo mode for development
        while True:
            try:
                message = await websocket.receive_text()
                await websocket.send_json({
                    "stream_type": "trading",
                    "echo": message,
                    "timestamp": datetime.now().isoformat()
                })
            except:
                break
                
    except Exception as e:
        print(f"Trading stream error: {e}")


@app.websocket("/api/stream/account") 
async def websocket_account_stream(websocket: WebSocket):
    """Real-time account information and balance updates"""
    await websocket.accept()
    
    try:
        await websocket.send_json({
            "status": "connected",
            "stream_type": "account",
            "message": "Account stream established - balance and info updates",
            "timestamp": datetime.now().isoformat(),
            "features": ["balance", "equity", "margin", "positions"]
        })
        
        # Echo mode for development  
        while True:
            try:
                message = await websocket.receive_text()
                await websocket.send_json({
                    "stream_type": "account", 
                    "echo": message,
                    "timestamp": datetime.now().isoformat()
                })
            except:
                break
                
    except Exception as e:
        print(f"Account stream error: {e}")


@app.websocket("/api/stream/news")
async def websocket_news_stream(websocket: WebSocket):
    """Real-time economic news and market events"""
    await websocket.accept()
    
    try:
        await websocket.send_json({
            "status": "connected",
            "stream_type": "news",
            "message": "News stream established - economic calendar and market events",
            "timestamp": datetime.now().isoformat(),
            "features": ["economic_calendar", "market_news", "volatility_alerts"]
        })
        
        # Echo mode for development
        while True:
            try:
                message = await websocket.receive_text()
                await websocket.send_json({
                    "stream_type": "news",
                    "echo": message,
                    "timestamp": datetime.now().isoformat()
                })
            except:
                break
                
    except Exception as e:
        print(f"News stream error: {e}")


@app.websocket("/api/stream/system")
async def websocket_system_stream(websocket: WebSocket):
    """Real-time system status and service health updates"""
    await websocket.accept()
    
    try:
        await websocket.send_json({
            "status": "connected",
            "stream_type": "system",
            "message": "System stream established - service health and alerts",
            "timestamp": datetime.now().isoformat(),
            "features": ["health_checks", "alerts", "performance_metrics"]
        })
        
        # Echo mode for development
        while True:
            try:
                message = await websocket.receive_text()
                await websocket.send_json({
                    "stream_type": "system",
                    "echo": message, 
                    "timestamp": datetime.now().isoformat()
                })
            except:
                break
                
    except Exception as e:
        print(f"System stream error: {e}")


# ================================================================================
# HTTP API ROUTING
# ================================================================================

# API routing - route HTTP requests to appropriate microservices (excluding WebSocket paths)
@app.api_route("/api/v1/{service_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_service(service_path: str, request: Request):
    """Route API requests to appropriate microservice"""
    
    # Skip WebSocket paths - they are handled by dedicated WebSocket endpoints
    if service_path.startswith("ws/") or service_path.startswith("stream/"):
        raise HTTPException(status_code=404, detail="WebSocket endpoints handled separately")
    
    # Determine target service based on path
    if service_path.startswith("mt5/") or service_path.startswith("data/"):
        target_service = "data-bridge"
    elif service_path.startswith("ai/") or service_path.startswith("openai/"):
        target_service = "ai-provider"
    elif service_path.startswith("users/") or service_path.startswith("workflows/"):
        target_service = "user-service"
    elif service_path.startswith("database/") or service_path.startswith("db/"):
        target_service = "database-service"
    elif service_path.startswith("orchestration/") or service_path.startswith("workflows/"):
        target_service = "ai-orchestration"
    else:
        # Default to data-bridge for MT5-related requests
        target_service = "data-bridge"
    
    if target_service not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Service {target_service} not found")
    
    # Forward request to target service
    target_url = f"{SERVICES[target_service]}/api/v1/{service_path}"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Get request body if present
            body = await request.body()
            
            # Forward the request
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=dict(request.headers),
                content=body,
                params=request.query_params
            )
            
            # Return the response
            return StreamingResponse(
                response.aiter_bytes(),
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Service {target_service} unavailable: {str(e)}")

# Direct service health endpoints for client monitoring
@app.get("/api/services/{service_name}/health")
async def service_health(service_name: str):
    """Get health status of specific microservice"""
    if service_name not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(f"{SERVICES[service_name]}/health")
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Service {service_name} unavailable: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting Simple API Gateway on port 8000")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )