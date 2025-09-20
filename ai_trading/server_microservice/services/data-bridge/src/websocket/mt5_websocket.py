"""
MT5 Bridge WebSocket - Real-time WebSocket server for MT5 microservice
Migrated from server_side with shared infrastructure integration
"""

import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
from pydantic import BaseModel, Field

# Service-specific infrastructure - use absolute imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))

try:
    from shared.infrastructure.core.logger_core import get_logger
    from shared.infrastructure.core.error_core import handle_error
    from shared.infrastructure.core.performance_core import performance_tracked, performance_context
    from shared.infrastructure.optional.validation_core import validate_trading_data
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
    
    def performance_context(service_name):
        class MockContext:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        return MockContext()
    
    def validate_trading_data(service_name, data):
        class MockValidationResult:
            def __init__(self):
                self.is_valid = True
                self.errors = []
        return MockValidationResult()

# Core MT5 functionality
from ..business.mt5_bridge import MT5Bridge, TickData, TradeOrder, OrderType, ConnectionStatus

# Database integration
from ..business.database_client import get_database_client, DatabaseServiceClient
from ..business.batch_processor import get_batch_processor, TickDataBatchProcessor

# Pydantic models for WebSocket communication
class WebSocketMessage(BaseModel):
    """Base WebSocket message structure"""
    type: str = Field(..., description="Message type")
    timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    data: Optional[Dict[str, Any]] = Field(default=None, description="Message payload")
    # Support direct fields for backward compatibility
    connection_id: Optional[str] = None
    client_id: Optional[str] = None
    status: Optional[str] = None

class AccountInfoMessage(BaseModel):
    """Account information message"""
    login: int
    balance: float
    equity: float
    margin: float
    free_margin: float
    margin_level: Optional[float] = None
    currency: str
    server: str
    company: str
    leverage: Optional[int] = Field(default=100)  # Default leverage if not provided

class TickDataMessage(BaseModel):
    """Tick data message"""
    symbol: str
    bid: float
    ask: float
    spread: float
    time: datetime
    volume: Optional[float] = None

class TradingSignalMessage(BaseModel):
    """Trading signal message"""
    signal_id: str = Field(default_factory=lambda: str(uuid4()))
    symbol: str
    action: str  # BUY, SELL, CLOSE
    volume: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    comment: str = "MT5 Bridge Signal"
    urgency: str = "medium"

class MT5WebSocketManager:
    """
    WebSocket Manager for MT5 Bridge Microservice
    
    Features:
    - Real-time bi-directional communication
    - Shared infrastructure integration
    - Connection management with health monitoring
    - Message validation and error handling
    """
    
    def __init__(self, service_name: str = "mt5-bridge"):
        self.service_name = service_name
        self.logger = get_logger(f"{service_name}-websocket", "001")
        
        # PERFORMANCE FIX: Use memory-efficient data structures
        self.active_connections: List[WebSocket] = []
        # Use WeakKeyDictionary to prevent memory leaks from connection metadata
        import weakref
        self.connection_metadata: weakref.WeakKeyDictionary = weakref.WeakKeyDictionary()
        
        # MT5 Bridge integration
        self.mt5_bridge: Optional[MT5Bridge] = None
        
        # Database integration
        self.db_client: Optional[DatabaseServiceClient] = None
        self.batch_processor: Optional[TickDataBatchProcessor] = None
        
        # Processing metrics
        self.processing_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_processed": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "last_update": datetime.now(timezone.utc)
        }
        
        self.logger.info("MT5 WebSocket Manager initialized")
    
    async def set_mt5_bridge(self, bridge: MT5Bridge):
        """Set MT5 bridge instance"""
        self.mt5_bridge = bridge
        self.logger.info("MT5 Bridge connected to WebSocket manager")
    
    async def initialize_database_integration(self):
        """Initialize database client and batch processor"""
        try:
            self.logger.info("Starting database integration initialization...")
            
            # Initialize database client
            self.logger.info("Initializing database client...")
            self.db_client = await get_database_client()
            self.logger.info("Database client initialized successfully")
            
            # Initialize batch processor
            self.logger.info("Initializing batch processor...")
            self.batch_processor = await get_batch_processor()
            self.logger.info("Batch processor initialized successfully")
            
            self.logger.info("Database integration initialization completed successfully")
            return True
        except Exception as e:
            self.logger.error(f"Database integration initialization failed: {type(e).__name__}: {str(e)}")
            error_context = {"operation": "initialize_database_integration", "error_type": type(e).__name__, "error_details": str(e)}
            handle_error("mt5-websocket", e, context=error_context)
            return False
    
    @performance_tracked("mt5-websocket", "connect_client")
    async def connect(self, websocket: WebSocket, client_info: Dict[str, Any] = None):
        """Accept WebSocket connection with validation"""
        try:
            await websocket.accept()
            self.active_connections.append(websocket)
            
            # Store connection metadata
            connection_id = str(uuid4())
            connection_metadata = {
                "connected_at": datetime.now(timezone.utc),
                "client_info": client_info or {},
                "last_heartbeat": datetime.now(timezone.utc),
                "status": "connected",
                "messages_processed": 0,
                "connection_id": connection_id
            }
            
            self.connection_metadata[websocket] = connection_metadata
            
            # Update metrics
            self.processing_stats["total_connections"] += 1
            self.processing_stats["active_connections"] = len(self.active_connections)
            self.processing_stats["successful_operations"] += 1
            
            self.logger.info(f"WebSocket connected: {len(self.active_connections)} active connections (ID: {connection_id})")
            
        except Exception as e:
            error_context = {
                "operation": "websocket_connect",
                "client_info": client_info or {}
            }
            handle_error("mt5-websocket", e, context=error_context)
            self.processing_stats["failed_operations"] += 1
    
    @performance_tracked("mt5-websocket", "disconnect_client")
    async def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection with comprehensive cleanup"""
        try:
            connection_metadata = self.connection_metadata.get(websocket, {})
            connection_id = connection_metadata.get("connection_id", "unknown")
            messages_processed = connection_metadata.get("messages_processed", 0)
            
            # PERFORMANCE FIX: Comprehensive cleanup to prevent memory leaks
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
                
            if websocket in self.connection_metadata:
                del self.connection_metadata[websocket]
            
            # PERFORMANCE FIX: Close WebSocket connection properly to free resources
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.close()
            except Exception:
                pass  # Connection might already be closed
            
            # PERFORMANCE FIX: Explicit garbage collection hint for large connection counts
            if len(self.active_connections) % 100 == 0:  # Every 100 disconnections
                import gc
                gc.collect()
            
            # Update metrics
            self.processing_stats["active_connections"] = len(self.active_connections)
            
            self.logger.info(f"WebSocket disconnected: {len(self.active_connections)} active connections")
            self.logger.info(f"Connection stats - ID: {connection_id}, Messages: {messages_processed}")
            
        except Exception as e:
            error_context = {"operation": "websocket_disconnect"}
            handle_error("mt5-websocket", e, context=error_context)
    
    @performance_tracked("mt5-websocket", "send_message")
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific WebSocket with error handling"""
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_text(json.dumps(message, default=str))
                
                # Update connection metadata
                if websocket in self.connection_metadata:
                    self.connection_metadata[websocket]["messages_processed"] += 1
                    
            else:
                self.logger.warning("Attempted to send message to disconnected WebSocket")
                
        except Exception as e:
            error_context = {
                "operation": "send_personal_message",
                "websocket_id": str(id(websocket))
            }
            handle_error("mt5-websocket", e, context=error_context)
            await self.disconnect(websocket)
    
    @performance_tracked("mt5-websocket", "broadcast_message")
    async def broadcast(self, message: dict):
        """Broadcast message to all connected WebSockets with optimized parallel sending"""
        if not self.active_connections:
            return {"successful_sends": 0, "failed_sends": 0}
        
        # PERFORMANCE FIX: Single JSON serialization instead of per-connection
        message_json = json.dumps(message, default=str)
        
        # PERFORMANCE FIX: Pre-filter healthy connections to avoid wasted tasks
        healthy_connections = [
            conn for conn in self.active_connections 
            if conn.client_state == WebSocketState.CONNECTED
        ]
        
        if not healthy_connections:
            return {"successful_sends": 0, "failed_sends": len(self.active_connections)}
        
        # PERFORMANCE FIX: Optimized send function with reduced error handling overhead
        async def send_to_connection(connection):
            try:
                await connection.send_text(message_json)
                return True, connection
            except Exception as e:
                # Simplified error handling to reduce overhead
                return False, connection
        
        # PERFORMANCE FIX: Batch processing for large connection counts (>100)
        if len(healthy_connections) > 100:
            # Process in batches of 50 to prevent overwhelming the event loop
            batch_size = 50
            successful_sends = 0
            failed_sends = 0
            
            for i in range(0, len(healthy_connections), batch_size):
                batch = healthy_connections[i:i + batch_size]
                tasks = [send_to_connection(conn) for conn in batch]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in batch_results:
                    if isinstance(result, Exception):
                        failed_sends += 1
                    else:
                        success, _ = result
                        if success:
                            successful_sends += 1
                        else:
                            failed_sends += 1
            
            return {"successful_sends": successful_sends, "failed_sends": failed_sends}
        else:
            # Execute all sends in parallel for smaller connection counts
            tasks = [send_to_connection(conn) for conn in healthy_connections]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
            # Process results for smaller connection counts
            successful_sends = 0
            disconnected = []
            
            for result in results:
                if isinstance(result, Exception):
                    continue
                success, connection = result
                if success:
                    successful_sends += 1
                else:
                    disconnected.append(connection)
            
            # PERFORMANCE FIX: Async cleanup without blocking broadcast response 
            if disconnected:
                asyncio.create_task(self._cleanup_disconnected_connections(disconnected))
            
            self.logger.debug(f"Optimized broadcast: {successful_sends} success, {len(disconnected)} failed")
            return {"successful_sends": successful_sends, "failed_sends": len(disconnected)}
    
    async def _cleanup_disconnected_connections(self, connections):
        """Background cleanup of disconnected connections"""
        cleanup_tasks = [self.disconnect(conn) for conn in connections]
        await asyncio.gather(*cleanup_tasks, return_exceptions=True)
    
    @performance_tracked("mt5-websocket", "handle_message")
    async def handle_message(self, message: WebSocketMessage, websocket: WebSocket):
        """Handle incoming WebSocket message with validation"""
        try:
            message_type = message.type
            data = message.data
            
            # Update processing metrics
            self.processing_stats["messages_processed"] += 1
            self.processing_stats["last_update"] = datetime.now(timezone.utc)
            
            # Route message based on type
            if message_type == "connection":
                await self._handle_connection_status(message, websocket)
                
            elif message_type == "account_info":
                await self._handle_account_info(data or message.dict(), websocket)
                
            elif message_type == "tick_data":
                await self._handle_tick_data(data, websocket)
                
            elif message_type == "positions":
                await self._handle_positions(data, websocket)
                
            elif message_type == "orders":
                await self._handle_orders(data, websocket)
                
            elif message_type == "deals_history":
                await self._handle_deals_history(data, websocket)
                
            elif message_type == "orders_history":
                await self._handle_orders_history(data, websocket)
                
            elif message_type == "trading_signal":
                await self._handle_trading_signal(data, websocket)
                
            elif message_type == "heartbeat":
                await self._handle_heartbeat(data, websocket)
                
            elif message_type == "mt5_command":
                await self._handle_mt5_command(data, websocket)
                
            else:
                self.logger.warning(f"Unknown message type: {message_type}")
                await self.send_personal_message({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                }, websocket)
            
            # Update successful operations
            self.processing_stats["successful_operations"] += 1
            
        except Exception as e:
            error_context = {
                "operation": "handle_websocket_message",
                "message_type": message.type if hasattr(message, 'type') else 'unknown'
            }
            handle_error("mt5-websocket", e, context=error_context)
            self.processing_stats["failed_operations"] += 1
            
            # Send error response
            await self.send_personal_message({
                "type": "error",
                "message": f"Error processing message: {str(e)}"
            }, websocket)
    
    async def _handle_account_info(self, data: Dict[str, Any], websocket: WebSocket):
        """Handle account information message with database storage"""
        try:
            account_info = AccountInfoMessage(**data)
            self.logger.info(f"Account info received: Balance={account_info.balance}, Equity={account_info.equity}")
            
            # CRITICAL: Store account info in database
            if self.db_client:
                try:
                    # Convert AccountInfoMessage to dict for database storage
                    account_dict = {
                        "login": account_info.login,
                        "balance": account_info.balance,
                        "equity": account_info.equity,
                        "margin": account_info.margin,
                        "free_margin": account_info.free_margin,
                        "margin_level": account_info.margin_level,
                        "currency": account_info.currency,
                        "server": account_info.server,
                        "company": account_info.company,
                        "leverage": account_info.leverage,
                        "broker": data.get("broker", "FBS-Demo"),
                        "account_type": data.get("account_type", "demo")
                    }
                    
                    # Store directly (account info is not high frequency)
                    stored = await self.db_client.store_account_info(account_dict)
                    
                    self.logger.info(f"Account info stored in database: {stored}")
                    
                except Exception as db_error:
                    self.logger.error(f"Failed to store account info in database: {db_error}")
                    # Continue processing even if database storage fails
            else:
                self.logger.warning("Database client not initialized - account info not stored")
            
            # Send acknowledgment
            await self.send_personal_message({
                "type": "account_info_processed",
                "status": "success",
                "data": {
                    "balance": account_info.balance,
                    "equity": account_info.equity,
                    "margin": account_info.margin,
                    "database_stored": self.db_client is not None
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, websocket)
            
        except Exception as e:
            self.logger.error(f"Error handling account info: {e}")
            await self.send_personal_message({
                "type": "error",
                "message": f"Invalid account info format: {str(e)}"
            }, websocket)
    
    async def _handle_tick_data(self, data: Dict[str, Any], websocket: WebSocket):
        """Handle tick data message with database storage"""
        try:
            tick_data = TickDataMessage(**data)
            
            # Validate tick data using shared infrastructure
            validation_data = {
                "symbol": tick_data.symbol,
                "price": tick_data.bid,
                "volume": tick_data.volume or 1.0
            }
            
            validation_result = validate_trading_data("mt5-websocket", validation_data)
            if not validation_result.is_valid:
                self.logger.warning(f"Invalid tick data: {validation_result.errors}")
                await self.send_personal_message({
                    "type": "error",
                    "message": f"Invalid tick data: {validation_result.errors}"
                }, websocket)
                return
            
            self.logger.debug(f"Tick data received: {tick_data.symbol} @ {tick_data.bid}/{tick_data.ask}")
            
            # CRITICAL: Store tick data in database via batch processor
            if self.batch_processor:
                try:
                    # Convert TickDataMessage to dict for database storage
                    tick_dict = {
                        "symbol": tick_data.symbol,
                        "bid": tick_data.bid,
                        "ask": tick_data.ask,
                        "spread": tick_data.spread,
                        "time": tick_data.time,
                        "volume": tick_data.volume,
                        "broker": data.get("broker", "FBS-Demo"),
                        "account_type": data.get("account_type", "demo")
                    }
                    
                    # Add to batch processor for efficient database storage
                    await self.batch_processor.add_tick(tick_dict)
                    
                    self.logger.debug(f"Tick data queued for database storage: {tick_data.symbol}")
                    
                except Exception as db_error:
                    self.logger.error(f"Failed to queue tick for database storage: {db_error}")
                    # Continue processing even if database storage fails
            else:
                self.logger.warning("Batch processor not initialized - tick data not stored in database")
            
            # Send tick processing confirmation
            await self.send_personal_message({
                "type": "tick_data_processed",
                "status": "success",
                "data": {
                    "symbol": tick_data.symbol,
                    "bid": tick_data.bid,
                    "ask": tick_data.ask,
                    "spread": tick_data.spread,
                    "database_queued": self.batch_processor is not None
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, websocket)
            
        except Exception as e:
            self.logger.error(f"Error handling tick data: {e}")
            await self.send_personal_message({
                "type": "error",
                "message": f"Invalid tick data format: {str(e)}"
            }, websocket)
    
    async def _handle_trading_signal(self, data: Dict[str, Any], websocket: WebSocket):
        """Handle trading signal message"""
        try:
            signal = TradingSignalMessage(**data)
            
            # Validate trading signal
            validation_data = {
                "symbol": signal.symbol,
                "volume": signal.volume,
                "operation": signal.action
            }
            
            validation_result = validate_trading_data("mt5-websocket", validation_data)
            if not validation_result.is_valid:
                self.logger.warning(f"Invalid trading signal: {validation_result.errors}")
                await self.send_personal_message({
                    "type": "error",
                    "message": f"Invalid trading signal: {validation_result.errors}"
                }, websocket)
                return
            
            self.logger.info(f"Trading signal received: {signal.symbol} {signal.action} {signal.volume}")
            
            # Execute signal through MT5 Bridge if available
            if self.mt5_bridge:
                try:
                    # Convert to TradeOrder and execute
                    order_type = OrderType.BUY if signal.action.upper() == "BUY" else OrderType.SELL
                    trade_order = TradeOrder(
                        symbol=signal.symbol,
                        order_type=order_type,
                        volume=signal.volume,
                        sl=signal.stop_loss,
                        tp=signal.take_profit,
                        comment=signal.comment
                    )
                    
                    result = await self.mt5_bridge.place_order(trade_order)
                    
                    await self.send_personal_message({
                        "type": "trading_signal_executed",
                        "status": "success" if result["success"] else "failed",
                        "signal_id": signal.signal_id,
                        "result": result,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }, websocket)
                    
                except Exception as e:
                    self.logger.error(f"Error executing trading signal: {e}")
                    await self.send_personal_message({
                        "type": "trading_signal_executed",
                        "status": "error",
                        "signal_id": signal.signal_id,
                        "error": str(e),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }, websocket)
            else:
                # No MT5 bridge available - just acknowledge
                await self.send_personal_message({
                    "type": "trading_signal_received",
                    "status": "acknowledged",
                    "signal_id": signal.signal_id,
                    "message": "Signal received but MT5 bridge not available",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }, websocket)
            
        except Exception as e:
            self.logger.error(f"Error handling trading signal: {e}")
            await self.send_personal_message({
                "type": "error",
                "message": f"Invalid trading signal format: {str(e)}"
            }, websocket)
    
    async def _handle_heartbeat(self, data: Dict[str, Any], websocket: WebSocket):
        """Handle heartbeat message"""
        try:
            # Update last heartbeat time
            if websocket in self.connection_metadata:
                self.connection_metadata[websocket]["last_heartbeat"] = datetime.now(timezone.utc)
            
            # Get system status
            status_data = {
                "server_status": "healthy",
                "active_connections": len(self.active_connections),
                "mt5_bridge_status": self.mt5_bridge.get_status() if self.mt5_bridge else {"status": "disconnected"},
                "processing_stats": self.processing_stats
            }
            
            await self.send_personal_message({
                "type": "heartbeat_response",
                "status": "healthy",
                "data": status_data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, websocket)
            
        except Exception as e:
            self.logger.error(f"Error handling heartbeat: {e}")
            await self.send_personal_message({
                "type": "error",
                "message": f"Error processing heartbeat: {str(e)}"
            }, websocket)
    
    async def _handle_mt5_command(self, data: Dict[str, Any], websocket: WebSocket):
        """Handle MT5 command message"""
        try:
            command = data.get("command")
            
            if not self.mt5_bridge:
                await self.send_personal_message({
                    "type": "mt5_command_result",
                    "status": "error",
                    "message": "MT5 bridge not available",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }, websocket)
                return
            
            result = None
            
            if command == "connect":
                result = await self.mt5_bridge.initialize()
                
            elif command == "disconnect":
                await self.mt5_bridge.disconnect()
                result = True
                
            elif command == "status":
                result = self.mt5_bridge.get_status()
                
            elif command == "account_info":
                result = await self.mt5_bridge.get_account_info()
                
            elif command == "get_ticks":
                symbol = data.get("symbol", "EURUSD")
                count = data.get("count", 100)
                tick_data = await self.mt5_bridge.get_tick_data(symbol, count)
                result = [tick.to_dict() for tick in tick_data]
                
            else:
                await self.send_personal_message({
                    "type": "error",
                    "message": f"Unknown MT5 command: {command}"
                }, websocket)
                return
            
            await self.send_personal_message({
                "type": "mt5_command_result",
                "status": "success",
                "command": command,
                "result": result,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, websocket)
            
        except Exception as e:
            self.logger.error(f"Error handling MT5 command: {e}")
            await self.send_personal_message({
                "type": "mt5_command_result",
                "status": "error",
                "command": data.get("command", "unknown"),
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, websocket)
    
    async def _handle_connection_status(self, message: WebSocketMessage, websocket: WebSocket):
        """Handle connection status messages"""
        self.logger.info(f"Connection status: {message.status}")
        await self.send_personal_message({
            "type": "connection_acknowledged",
            "status": "received",
            "client_id": message.client_id
        }, websocket)
    
    async def _handle_positions(self, data: Dict[str, Any], websocket: WebSocket):
        """Handle positions data"""
        self.logger.info(f"Received positions data: {len(data) if data else 0} positions")
        await self.send_personal_message({
            "type": "positions_processed",
            "count": len(data) if data else 0
        }, websocket)
    
    async def _handle_orders(self, data: Dict[str, Any], websocket: WebSocket):
        """Handle orders data"""
        self.logger.info(f"Received orders data: {len(data) if data else 0} orders")
        await self.send_personal_message({
            "type": "orders_processed",
            "count": len(data) if data else 0
        }, websocket)
    
    async def _handle_deals_history(self, data: Dict[str, Any], websocket: WebSocket):
        """Handle deals history data"""
        self.logger.info(f"Received deals history: {len(data) if data else 0} deals")
        await self.send_personal_message({
            "type": "deals_history_processed",
            "count": len(data) if data else 0
        }, websocket)
    
    async def _handle_orders_history(self, data: Dict[str, Any], websocket: WebSocket):
        """Handle orders history data"""
        self.logger.info(f"Received orders history: {len(data) if data else 0} orders")
        await self.send_personal_message({
            "type": "orders_history_processed", 
            "count": len(data) if data else 0
        }, websocket)
    
    def get_status(self) -> Dict[str, Any]:
        """Get WebSocket manager status with performance metrics"""
        total_operations = self.processing_stats["successful_operations"] + self.processing_stats["failed_operations"]
        success_rate = (self.processing_stats["successful_operations"] / total_operations * 100) if total_operations > 0 else 0
        
        # Connection health metrics
        healthy_connections = 0
        for ws, metadata in self.connection_metadata.items():
            if ws.client_state == WebSocketState.CONNECTED:
                healthy_connections += 1
        
        status = {
            "active_connections": len(self.active_connections),
            "healthy_connections": healthy_connections,
            "total_connections": self.processing_stats["total_connections"],
            "messages_processed": self.processing_stats["messages_processed"],
            "successful_operations": self.processing_stats["successful_operations"],
            "failed_operations": self.processing_stats["failed_operations"],
            "success_rate_percent": round(success_rate, 2),
            "mt5_bridge_available": self.mt5_bridge is not None,
            "last_update": self.processing_stats["last_update"].isoformat()
        }
        
        # Add MT5 bridge performance metrics if available
        if self.mt5_bridge:
            mt5_status = self.mt5_bridge.get_status()
            status["mt5_bridge_status"] = mt5_status
            status["cache_performance"] = mt5_status.get("cache_performance", {})
        else:
            status["mt5_bridge_status"] = None
        
        # Add database integration metrics
        if self.db_client:
            status["database_client"] = self.db_client.get_metrics()
        else:
            status["database_client"] = None
        
        if self.batch_processor:
            status["batch_processor"] = self.batch_processor.get_status()
        else:
            status["batch_processor"] = None
            
        return status
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics"""
        connection_details = []
        for ws, metadata in self.connection_metadata.items():
            connection_details.append({
                "connection_id": metadata.get("connection_id", "unknown"),
                "connected_at": metadata.get("connected_at", datetime.now(timezone.utc)).isoformat(),
                "messages_processed": metadata.get("messages_processed", 0),
                "last_heartbeat": metadata.get("last_heartbeat", datetime.now(timezone.utc)).isoformat(),
                "status": metadata.get("status", "unknown"),
                "client_state": ws.client_state.name if hasattr(ws.client_state, 'name') else str(ws.client_state)
            })
        
        return {
            "overall_stats": self.processing_stats,
            "connection_details": connection_details,
            "broadcast_performance": {
                "parallel_processing": True,
                "connection_pooling": True,
                "error_handling": "automatic_cleanup"
            }
        }

# Global WebSocket manager instance
websocket_manager = MT5WebSocketManager()

# Export main classes and functions
__all__ = [
    "MT5WebSocketManager",
    "WebSocketMessage",
    "AccountInfoMessage", 
    "TickDataMessage",
    "TradingSignalMessage",
    "websocket_manager"
]