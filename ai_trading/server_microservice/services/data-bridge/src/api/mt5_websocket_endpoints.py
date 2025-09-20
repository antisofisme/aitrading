"""
MT5 Bridge WebSocket Endpoints - FastAPI WebSocket routes
Real-time WebSocket endpoints for the MT5 microservice
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from pydantic import ValidationError

# Shared infrastructure - use absolute imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))

try:
    from shared.infrastructure.core.logger_core import get_logger
    from shared.infrastructure.core.error_core import handle_error
    from shared.infrastructure.core.performance_core import performance_tracked
except ImportError as e:
    print(f"⚠️ Infrastructure import issue: {e}")
    # Fallback implementations
    import logging
    def get_logger(name, version=None):
        return logging.getLogger(name)
    
    def handle_error(service_name, error, context=None):
        print(f"Error in {service_name}: {error}")
        if context:
            print(f"Context: {context}")
    
    def performance_tracked(service_name, operation_name):
        def decorator(func):
            return func
        return decorator

# WebSocket functionality
from ..websocket.mt5_websocket import websocket_manager, WebSocketMessage
from ..business.mt5_bridge import create_mt5_bridge

# Initialize logger
logger = get_logger("mt5-websocket-endpoints", "001")

# Create router
router = APIRouter()

# Dependency to ensure MT5 bridge is available
async def get_mt5_bridge_dependency():
    """Dependency to get MT5 bridge for WebSocket"""
    if websocket_manager.mt5_bridge is None:
        bridge = await create_mt5_bridge("mt5-bridge-websocket")
        await websocket_manager.set_mt5_bridge(bridge)
    
    # CRITICAL FIX: Database integration should be initialized at service startup, not per-client
    # Just verify it's available and log if missing
    if websocket_manager.db_client is None or websocket_manager.batch_processor is None:
        logger.warning("⚠️ Database integration not available - should have been initialized at service startup!")
        logger.warning(f"DB Client: {websocket_manager.db_client is not None}, Batch Processor: {websocket_manager.batch_processor is not None}")
    
    return websocket_manager.mt5_bridge

@router.websocket("/ws")
async def mt5_websocket_endpoint(
    websocket: WebSocket,
    mt5_bridge = Depends(get_mt5_bridge_dependency)
):
    """
    Main WebSocket endpoint for MT5 Bridge communication
    
    Handles:
    - Real-time trading data
    - Account information
    - Trading signals
    - MT5 commands
    - Health monitoring
    """
    
    # Extract client information
    client_info = {
        "user_agent": websocket.headers.get("user-agent", "Unknown"),
        "client_host": websocket.client.host if websocket.client else "Unknown",
        "connection_time": datetime.now(timezone.utc).isoformat()
    }
    
    # Connect WebSocket
    await websocket_manager.connect(websocket, client_info)
    
    try:
        # Send welcome message
        welcome_message = {
            "type": "connection_established",
            "message": "Connected to MT5 Bridge Microservice",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "server_status": "ready",
            "features": {
                "trading_commands": True,
                "real_time_data": True,
                "account_monitoring": True,
                "signal_processing": True
            },
            "mt5_status": mt5_bridge.get_status() if mt5_bridge else {"status": "unavailable"}
        }
        await websocket_manager.send_personal_message(welcome_message, websocket)
        
        # Main message handling loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Validate message structure
                try:
                    message = WebSocketMessage(**message_data)
                except ValidationError as validation_error:
                    logger.warning(f"Invalid message format: {validation_error}")
                    await websocket_manager.send_personal_message({
                        "type": "error",
                        "message": f"Invalid message format: {validation_error}",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }, websocket)
                    continue
                
                # Handle message through WebSocket manager
                await websocket_manager.handle_message(message, websocket)
                
            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected normally")
                break
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON received: {e}")
                await websocket_manager.send_personal_message({
                    "type": "error",
                    "message": f"Invalid JSON format: {str(e)}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }, websocket)
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await websocket_manager.send_personal_message({
                    "type": "error", 
                    "message": f"Server error: {str(e)}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }, websocket)
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        error_context = {
            "operation": "websocket_connection",
            "client_info": client_info
        }
        handle_error("mt5-websocket-endpoints", e, context=error_context)
    finally:
        await websocket_manager.disconnect(websocket)

@router.get("/ws/status")
@performance_tracked("mt5-websocket-endpoints", "get_websocket_status")
async def get_websocket_status():
    """Get WebSocket connection status"""
    try:
        status = websocket_manager.get_status()
        
        return {
            "success": True,
            "websocket_status": status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting WebSocket status: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@router.post("/ws/broadcast")
@performance_tracked("mt5-websocket-endpoints", "broadcast_message")
async def broadcast_message(message: Dict[str, Any]):
    """Broadcast message to all connected WebSocket clients"""
    try:
        # Add timestamp to message
        message["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        # Broadcast through WebSocket manager
        result = await websocket_manager.broadcast(message)
        
        return {
            "success": True,
            "message": "Message broadcasted successfully",
            "broadcast_result": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error broadcasting message: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@router.get("/ws/health")
@performance_tracked("mt5-websocket-endpoints", "websocket_health_check")
async def websocket_health_check():
    """Health check for WebSocket service"""
    try:
        status = websocket_manager.get_status()
        
        # Determine health status
        health_status = "healthy"
        if status["active_connections"] == 0:
            health_status = "no_connections"
        elif status["failed_operations"] > status["successful_operations"]:
            health_status = "degraded"
        
        health_data = {
            "status": health_status,
            "websocket_metrics": status,
            "service_info": {
                "service_name": "mt5-bridge-websocket",
                "version": "1.0.0",
                "uptime": "running"
            }
        }
        
        return {
            "success": True,
            "health": health_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error during WebSocket health check: {e}")
        return {
            "success": False,
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# ================================================================================
# INTERNAL WEBSOCKET ENDPOINTS FOR API GATEWAY PROXY
# ================================================================================

@router.websocket("/api/internal/market-data")
async def internal_market_data_websocket(
    websocket: WebSocket,
    mt5_bridge = Depends(get_mt5_bridge_dependency)
):
    """Internal WebSocket endpoint for market data streaming (used by API Gateway)"""
    
    client_info = {
        "source": "api-gateway",
        "stream_type": "market-data",
        "connection_time": datetime.now(timezone.utc).isoformat()
    }
    
    await websocket_manager.connect(websocket, client_info)
    
    try:
        # Send internal connection confirmation
        await websocket_manager.send_personal_message({
            "type": "internal_connection_established",
            "stream_type": "market-data",
            "message": "Data-Bridge market data stream ready",
            "features": ["tick_data", "price_updates", "volume_data"],
            "mt5_status": mt5_bridge.get_status() if mt5_bridge else {"status": "unavailable"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, websocket)
        
        # Handle internal WebSocket communication
        while True:
            try:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Handle internal message types
                if message_data.get("type") == "subscribe_symbol":
                    symbol = message_data.get("symbol", "EURUSD")
                    logger.info(f"Internal subscription to {symbol} market data")
                    
                    # Send mock tick data for development
                    await websocket_manager.send_personal_message({
                        "type": "tick_data",
                        "symbol": symbol,
                        "bid": 1.0850,
                        "ask": 1.0852,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }, websocket)
                
                elif message_data.get("type") == "heartbeat":
                    await websocket_manager.send_personal_message({
                        "type": "heartbeat_response",
                        "status": "healthy",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }, websocket)
                
                else:
                    # Forward to main message handler
                    message = WebSocketMessage(**message_data)
                    await websocket_manager.handle_message(message, websocket)
                    
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket_manager.send_personal_message({
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }, websocket)
            
    except Exception as e:
        logger.error(f"Internal market-data WebSocket error: {e}")
    finally:
        await websocket_manager.disconnect(websocket)


@router.websocket("/api/internal/trading")
async def internal_trading_websocket(
    websocket: WebSocket,
    mt5_bridge = Depends(get_mt5_bridge_dependency)
):
    """Internal WebSocket endpoint for trading signals (used by API Gateway)"""
    
    client_info = {
        "source": "api-gateway", 
        "stream_type": "trading",
        "connection_time": datetime.now(timezone.utc).isoformat()
    }
    
    await websocket_manager.connect(websocket, client_info)
    
    try:
        await websocket_manager.send_personal_message({
            "type": "internal_connection_established",
            "stream_type": "trading", 
            "message": "Data-Bridge trading stream ready",
            "features": ["trading_signals", "order_updates", "execution_reports"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, websocket)
        
        while True:
            try:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Handle trading-specific messages
                message = WebSocketMessage(**message_data)
                await websocket_manager.handle_message(message, websocket)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Internal trading WebSocket message error: {e}")
                break
                
    except Exception as e:
        logger.error(f"Internal trading WebSocket error: {e}")
    finally:
        await websocket_manager.disconnect(websocket)


@router.websocket("/api/internal/account")
async def internal_account_websocket(
    websocket: WebSocket,
    mt5_bridge = Depends(get_mt5_bridge_dependency)
):
    """Internal WebSocket endpoint for account information (used by API Gateway)"""
    
    client_info = {
        "source": "api-gateway",
        "stream_type": "account",
        "connection_time": datetime.now(timezone.utc).isoformat()
    }
    
    await websocket_manager.connect(websocket, client_info)
    
    try:
        await websocket_manager.send_personal_message({
            "type": "internal_connection_established",
            "stream_type": "account",
            "message": "Data-Bridge account stream ready", 
            "features": ["account_info", "balance_updates", "margin_info"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, websocket)
        
        while True:
            try:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                message = WebSocketMessage(**message_data)
                await websocket_manager.handle_message(message, websocket)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Internal account WebSocket message error: {e}")
                break
                
    except Exception as e:
        logger.error(f"Internal account WebSocket error: {e}")
    finally:
        await websocket_manager.disconnect(websocket)


# Economic calendar endpoints have been moved to dedicated economic_calendar_endpoints.py
# This keeps the WebSocket endpoints focused on their primary function


# Export router
__all__ = ["router"]