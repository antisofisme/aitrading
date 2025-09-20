"""
websocket_client.py - WebSocket Communication Client

🎯 PURPOSE:
Business: Real-time WebSocket communication with microservices backend
Technical: Robust WebSocket client with reconnection and message handling
Domain: WebSocket/Real-time Communication/Service Integration

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:27.742Z
Session: client-side-ai-brain-full-compliance
Confidence: 92%
Complexity: medium

🧩 PATTERNS USED:
- AI_BRAIN_WEBSOCKET_CLIENT: Real-time communication with AI Brain patterns
- RECONNECTION_STRATEGY: Intelligent reconnection with exponential backoff

📦 DEPENDENCIES:
Internal: centralized_logger, error_handler, config_manager
External: websockets, asyncio, json, ssl

💡 AI DECISION REASONING:
WebSocket chosen for low-latency bidirectional communication. Robust error handling ensures reliability in production trading environment.

🚀 USAGE:
client = WebSocketClient(url); await client.connect(); await client.send(data)

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

import asyncio
import json
import websockets
from websockets.exceptions import ConnectionClosed
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from dataclasses import asdict
import ssl
from tenacity import retry, stop_after_attempt, wait_exponential

# CENTRALIZED INFRASTRUCTURE IMPORTS
from src.infrastructure import (
    # Centralized Logging
    get_logger,
    
    # Centralized Configuration  
    get_config,
    get_client_settings,
    
    # Centralized Error Handling
    handle_error,
    handle_websocket_error,
    ErrorCategory,
    ErrorSeverity,
    
    # Performance Tracking
    performance_tracked,
    track_performance,
    
    # Validation
    validate_field,
    validate_dict,
    validate_tick_data
)


class WebSocketClient:
    """
    WebSocket client for communication with Docker Backend - Enhanced with Centralized Infrastructure
    Provides centralized logging, error handling, performance tracking, and validation
    """
    
    def __init__(self, ws_url: str, auth_token: Optional[str] = None):
        # CENTRALIZED INFRASTRUCTURE INITIALIZATION
        # Initialize centralized logger first
        self.logger = get_logger('websocket_client', context={
            'component': 'websocket_client',
            'url': ws_url,
            'version': '2.0.0-centralized'
        })
        
        # CENTRALIZED VALIDATION - Validate WebSocket URL
        url_validation = validate_field('websocket_url', ws_url, 'websocket_url')
        if not url_validation.is_valid:
            error_messages = [error.message for error in url_validation.errors]
            raise ValueError(f"WebSocketClient initialization failed - Invalid URL: {'; '.join(error_messages)}")
        
        # Load centralized configuration
        try:
            self.websocket_config = get_config('websocket')
            self.network_config = get_config('client')
        except Exception as e:
            error_context = handle_error(
                error=e,
                category=ErrorCategory.CONFIG,
                severity=ErrorSeverity.HIGH,
                component='websocket_client',
                operation='configuration_loading'
            )
            self.logger.error(f"Failed to load WebSocket configuration: {error_context.message}")
            # Use default config as fallback
            self.websocket_config = {}
            self.network_config = {}
        
        # Initialize WebSocket connection parameters
        self.ws_url = ws_url
        self.auth_token = auth_token
        self.websocket = None
        self.connected = False
        self.message_handlers = {}
        self.heartbeat_task = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = self._safe_get_config(self.websocket_config, 'max_reconnect_attempts', 5)
        
        # Centralized system status logging
        self.logger.info(f"🚀 WebSocketClient initialized with centralized infrastructure")
        self.logger.info(f"🔌 Target URL: {ws_url}")
        self.logger.info(f"🔄 Max reconnect attempts: {self.max_reconnect_attempts}")
        self.logger.info(f"✅ URL validation passed")
    
    def _safe_get_config(self, obj, key: str, default=None):
        """
        Safely get configuration value supporting both dict and object access
        
        Args:
            obj: Configuration object or dictionary
            key: Configuration key
            default: Default value if not found
        
        Returns:
            Configuration value or default
        """
        try:
            if hasattr(obj, key):
                # Object access (e.g., config.max_reconnect_attempts)
                return getattr(obj, key)
            elif isinstance(obj, dict) and key in obj:
                # Dictionary access (e.g., config['max_reconnect_attempts'])
                return obj[key]
            elif hasattr(obj, 'get') and callable(getattr(obj, 'get')):
                # Dictionary-like object with get method
                return obj.get(key, default)
            else:
                return default
        except Exception as e:
            self.logger.debug(f"Error accessing config key '{key}': {e}")
            return default
        
    @performance_tracked("websocket_connection", "websocket_client")
    async def connect(self) -> bool:
        """Connect to WebSocket server - Enhanced with centralized performance tracking"""
        try:
            with track_performance("websocket_setup", "websocket_client"):
                # Prepare headers
                headers = {}
                if self.auth_token:
                    headers["Authorization"] = f"Bearer {self.auth_token}"
                
                # Connect to WebSocket
                self.logger.info(f"🔌 Connecting to: {self.ws_url}")
                
                # Handle SSL context for secure connections
                ssl_context = None
                if self.ws_url.startswith("wss://"):
                    ssl_context = ssl.create_default_context()
                    # For development, you might want to disable SSL verification
                    # ssl_context.check_hostname = False
                    # ssl_context.verify_mode = ssl.CERT_NONE
            
            with track_performance("websocket_handshake", "websocket_client"):
                # Simple connection without extra headers for now
                self.websocket = await websockets.connect(
                    self.ws_url,
                    ssl=ssl_context,
                    ping_interval=20,
                    ping_timeout=10,
                    close_timeout=10
                )
            
            with track_performance("websocket_initialization", "websocket_client"):
                self.connected = True
                self.reconnect_attempts = 0
                
                self.logger.success(f"✅ Connected to Backend WebSocket")
                
                # Start heartbeat
                self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
                
                # Send initial connection message
                await self.send_message({
                    "type": "connection",
                    "client": "mt5_bridge",
                    "timestamp": datetime.now().isoformat(),
                    "status": "connected"
                })
            
            return True
            
        except Exception as e:
            # Use centralized error handling
            error_context = handle_websocket_error(e, operation="websocket_connection")
            self.logger.error(f"WebSocket connection failed: {error_context.message}")
            
            # Log recovery suggestions
            for suggestion in error_context.recovery_suggestions:
                self.logger.info(f"💡 Recovery: {suggestion}")
            
            self.connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from WebSocket server"""
        try:
            self.connected = False
            
            # Cancel heartbeat
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
                try:
                    await self.heartbeat_task
                except asyncio.CancelledError:
                    pass
            
            # Close WebSocket
            if self.websocket:
                await self.websocket.close()
                self.websocket = None
            
            self.logger.info("🔌 Disconnected from Backend WebSocket")
            
        except Exception as e:
            self.logger.error(f"WebSocket disconnect error: {e}")
    
    @performance_tracked("websocket_send_message", "websocket_client")
    async def send_message(self, message: Dict[str, Any]) -> bool:
        """Send message to backend - Enhanced with centralized validation and performance tracking"""
        try:
            # CENTRALIZED VALIDATION - Validate basic message structure only
            # Skip field-level validation here since it's done in specific methods like send_tick_data
            msg_type = message.get('type')
            if not msg_type or not isinstance(msg_type, str):
                self.logger.error("Invalid message structure: Missing or invalid 'type' field")
                return False
            
            if not self.connected or not self.websocket:
                self.logger.warning("WebSocket not connected, cannot send message")
                return False
            
            with track_performance("message_preparation", "websocket_client"):
                # Add timestamp if not present
                if "timestamp" not in message:
                    message["timestamp"] = datetime.now().isoformat()
            
            with track_performance("message_transmission", "websocket_client"):
                # Send message with datetime serialization
                await self.websocket.send(json.dumps(message, default=str))
            
            # Only log important messages, not routine data
            msg_type = message.get('type', 'unknown')
            if msg_type not in ['tick_data', 'heartbeat', 'account_info', 'positions', 'orders']:
                self.logger.debug(f"📤 Sent: {msg_type}")
            return True
            
        except ConnectionClosed:
            self.logger.warning("WebSocket connection closed")
            self.connected = False
            return False
        except Exception as e:
            # Use centralized error handling
            error_context = handle_websocket_error(e, operation="send_message")
            self.logger.error(f"Send message error: {error_context.message}")
            
            # Log recovery suggestions for connection-related errors
            if "connection" in str(e).lower():
                for suggestion in error_context.recovery_suggestions:
                    self.logger.info(f"💡 Recovery: {suggestion}")
            
            return False
    
    async def listen_for_messages(self):
        """Listen for incoming messages from backend"""
        try:
            while self.connected and self.websocket:
                try:
                    message = await asyncio.wait_for(
                        self.websocket.recv(), 
                        timeout=30.0
                    )
                    
                    # Parse message
                    try:
                        data = json.loads(message)
                        await self._handle_message(data)
                    except json.JSONDecodeError as e:
                        self.logger.error(f"Invalid JSON received: {e}")
                        
                except asyncio.TimeoutError:
                    self.logger.debug("WebSocket receive timeout")
                    continue
                except ConnectionClosed:
                    self.logger.warning("WebSocket connection closed by server")
                    self.connected = False
                    break
                    
        except Exception as e:
            self.logger.error(f"Listen for messages error: {e}")
            self.connected = False
    
    async def _handle_message(self, data: Dict[str, Any]):
        """Handle incoming message"""
        try:
            message_type = data.get("type", "unknown")
            
            # Only log important messages, not routine responses
            if message_type not in ['data_processed', 'heartbeat_response']:
                self.logger.debug(f"📥 Received: {message_type}")
            
            # Call registered handler
            if message_type in self.message_handlers:
                handler = self.message_handlers[message_type]
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            else:
                self.logger.warning(f"No handler for message type: {message_type}")
                
        except Exception as e:
            self.logger.error(f"Handle message error: {e}")
    
    def register_handler(self, message_type: str, handler: Callable):
        """Register message handler"""
        self.message_handlers[message_type] = handler
        self.logger.info(f"📝 Registered handler for: {message_type}")
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeat messages"""
        try:
            while self.connected:
                await asyncio.sleep(30)  # Heartbeat every 30 seconds
                
                if self.connected:
                    await self.send_message({
                        "type": "heartbeat",
                        "client": "mt5_bridge",
                        "status": "alive"
                    })
                    
        except asyncio.CancelledError:
            self.logger.debug("Heartbeat loop cancelled")
        except Exception as e:
            self.logger.error(f"Heartbeat error: {e}")
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def auto_reconnect(self) -> bool:
        """Auto-reconnect with exponential backoff"""
        try:
            self.reconnect_attempts += 1
            self.logger.info(f"🔄 Reconnection attempt {self.reconnect_attempts}")
            
            if self.reconnect_attempts > self.max_reconnect_attempts:
                self.logger.error("Max reconnection attempts reached")
                return False
            
            # Disconnect first
            await self.disconnect()
            
            # Wait before reconnecting
            await asyncio.sleep(2 ** self.reconnect_attempts)
            
            # Try to reconnect
            return await self.connect()
            
        except Exception as e:
            self.logger.error(f"Auto-reconnect error: {e}")
            return False
    
    async def send_account_info(self, account_info):
        """Send MT5 account information"""
        message = {
            "type": "account_info",
            "data": asdict(account_info) if hasattr(account_info, '__dict__') else account_info
        }
        return await self.send_message(message)
    
    async def send_tick_data(self, tick):
        """Send tick data using flat format for better performance - Enhanced with tick-specific validation"""
        if hasattr(tick, '__dict__'):
            tick_dict = asdict(tick)
        else:
            tick_dict = tick
        
        # Extract tick data components
        symbol = tick_dict.get('symbol')
        bid = tick_dict.get('bid')
        ask = tick_dict.get('ask')
        last = tick_dict.get('last')
        volume = tick_dict.get('volume', 0)
        
        # CENTRALIZED VALIDATION - Validate tick data with proper rules
        tick_validation = validate_tick_data(
            symbol=symbol,
            bid=bid,
            ask=ask,
            last=last,
            volume=volume,
            context={'data_type': 'tick_data', 'source': 'mt5_bridge'}
        )
        
        if not tick_validation.is_valid:
            error_messages = [error.message for error in tick_validation.errors]
            self.logger.error(f"Invalid tick data: {'; '.join(error_messages)}")
            # Log the actual tick data for debugging
            self.logger.debug(f"Rejected tick data: symbol={symbol}, bid={bid}, ask={ask}, volume={volume}")
            return False
            
        # Use server-expected format with data wrapper and correct field names
        message = {
            "type": "tick_data",
            "data": {
                "symbol": symbol,
                "bid": bid,
                "ask": ask,
                "spread": tick_dict.get('spread', 0),
                "time": datetime.now().isoformat(),  # Server expects 'time' not 'timestamp'
                "volume": volume,
                "last": last,  # Keep additional fields for compatibility
                "source": "mt5_bridge"
            }
        }
        return await self.send_message(message)
    
    async def send_positions(self, positions):
        """Send positions data"""
        positions_list = [asdict(pos) if hasattr(pos, '__dict__') else pos for pos in positions]
        message = {
            "type": "positions",
            "data": {"positions": positions_list, "count": len(positions_list)}
        }
        return await self.send_message(message)
    
    async def send_orders(self, orders):
        """Send orders data"""
        orders_list = [asdict(order) if hasattr(order, '__dict__') else order for order in orders]
        message = {
            "type": "orders",
            "data": {"orders": orders_list, "count": len(orders_list)}
        }
        return await self.send_message(message)
    
    async def send_deals_history(self, deals):
        """Send historical deals/trades data"""
        deals_list = [asdict(deal) if hasattr(deal, '__dict__') else deal for deal in deals]
        message = {
            "type": "deals_history",
            "data": {"deals": deals_list, "count": len(deals_list)}
        }
        return await self.send_message(message)
    
    async def send_orders_history(self, orders):
        """Send historical orders data"""
        orders_list = [asdict(order) if hasattr(order, '__dict__') else order for order in orders]
        message = {
            "type": "orders_history", 
            "data": {"orders": orders_list, "count": len(orders_list)}
        }
        return await self.send_message(message)
    
    async def send_trade_result(self, trade_result):
        """Send trade execution result"""
        message = {
            "type": "trade_result",
            "data": trade_result
        }
        return await self.send_message(message)
    
    async def send_error(self, error_msg: str, error_code: str = None):
        """Send error message"""
        message = {
            "type": "error",
            "data": {
                "message": error_msg,
                "code": error_code,
                "timestamp": datetime.now().isoformat()
            }
        }
        return await self.send_message(message)
    
    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is connected"""
        return self.connected and self.websocket is not None


class MessageTypes:
    """WebSocket message types constants"""
    
    # Outgoing (MT5 Bridge → Backend)
    CONNECTION = "connection"
    HEARTBEAT = "heartbeat"
    ACCOUNT_INFO = "account_info"
    TICK_DATA = "tick_data"
    POSITIONS = "positions"
    ORDERS = "orders"
    TRADE_RESULT = "trade_result"
    ERROR = "error"
    
    # Incoming (Backend → MT5 Bridge) - Original
    TRADING_SIGNAL = "trading_signal"
    CLOSE_POSITION = "close_position"
    MODIFY_ORDER = "modify_order"
    GET_DATA = "get_data"
    EMERGENCY_STOP = "emergency_stop"
    CONFIG_UPDATE = "config_update"
    DATA_PROCESSED = "data_processed"
    CONNECTION_ESTABLISHED = "connection_established"
    
    # NEW: Server Optimization Response Messages
    LIVE_DATA_PROCESSED = "live_data_processed"        # Enhanced account data response
    POSITIONS_PROCESSED = "positions_processed"        # Enhanced positions response
    ORDER_RESULT_PROCESSED = "order_result_processed"  # Enhanced order result response
    HEARTBEAT_RESPONSE = "heartbeat_response"          # Enhanced heartbeat with stats
    ERROR_ACKNOWLEDGED = "error_acknowledged"          # Enhanced error response
    PERFORMANCE_ALERT = "performance_alert"            # New performance monitoring alerts