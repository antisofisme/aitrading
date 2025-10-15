"""
bridge_app.py - Bridge Application Core

🎯 PURPOSE:
Business: Core bridge application logic for MT5-WebSocket data flow
Technical: Application orchestration with service lifecycle management
Domain: Application Core/Service Orchestration/Data Flow

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:27.903Z
Session: client-side-ai-brain-full-compliance
Confidence: 93%
Complexity: high

🧩 PATTERNS USED:
- AI_BRAIN_APPLICATION_CORE: Application orchestration with centralized infrastructure
- SERVICE_LIFECYCLE: Coordinated service startup and shutdown

📦 DEPENDENCIES:
Internal: central_hub, mt5_handler, websocket_client, data_source_monitor
External: asyncio, signal, threading, dataclasses

💡 AI DECISION REASONING:
Bridge application core provides centralized coordination of all services with proper lifecycle management and error handling.

🚀 USAGE:
bridge = BridgeApp(); await bridge.start()

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

from src.shared.config.client_settings import get_client_settings

import asyncio
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List
from loguru import logger
from dataclasses import asdict

from libs.config import get_client_settings
from mt5_handler import MT5Handler, MT5_ORDER_TYPES, MT5_TIMEFRAMES
from websocket_client import WebSocketClient, MessageTypes
from service_manager import service_manager, setup_graceful_shutdown


class MT5Bridge:
    """
    Main MT5 Bridge Application
    Orchestrates communication between MT5 and Docker Backend
    """
    
    def __init__(self):
        # Load configuration
        self.settings = get_client_settings()
        
        # Initialize components
        self.mt5_handler = None
        self.ws_client = None
        
        # Application state
        self.running = False
        self.last_heartbeat = None
        self.daily_trades_count = 0
        self.last_trade_date = None
        
        # Tasks
        self.data_streaming_task = None
        self.message_listening_task = None
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration - File + Database"""
        logger.remove()  # Remove default handler
        
        # Console logging
        logger.add(
            sys.stdout,
            level=self.settings.app.log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>bridge_app</cyan> | "
                   "<level>{message}</level>",
            colorize=True
        )
        
        # File logging - Max 5MB, overwrite old data
        logger.add(
            self.settings.app.log_file,
            level=self.settings.app.log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} | {message}",
            rotation="5 MB",  # Rotate after 5MB
            retention=1,  # Keep only 1 file (current)
            compression=None,  # No compression
            enqueue=True  # Prevent duplicate logs
        )
        
        # Initialize database logger
        # Database logging is handled by server side
        logger.info("📝 File logging configured")
        
        logger.info("📝 Bridge application logging configured (File + Database + Console)")
    
    async def start(self):
        """Start MT5 Bridge application"""
        try:
            logger.info("🚀 Starting MT5 Bridge Application")
            
            # Setup graceful shutdown
            setup_graceful_shutdown()
            
            # Register services with service manager
            service_manager.register_service("MT5_Bridge_Main")
            
            # Initialize MT5 connection
            await self._initialize_mt5()
            service_manager.register_service("MT5_Handler")
            
            # Initialize WebSocket connection
            await self._initialize_websocket()
            service_manager.register_service("WebSocket_Client")
            
            # Register signal handlers
            self._setup_signal_handlers()
            
            # Start background tasks
            await self._start_background_tasks()
            service_manager.register_service("Data_Streaming")
            service_manager.register_service("Message_Listening")
            
            self.running = True
            logger.success("✅ MT5 Bridge started successfully")
            
            # Start service monitor
            monitor_task = asyncio.create_task(service_manager.start_service_monitor())
            
            # Main application loop
            await self._main_loop()
            
            # Cancel monitor if main loop exits
            monitor_task.cancel()
            
        except Exception as e:
            logger.error(f"Start application error: {e}")
            await self.stop()
    
    async def stop(self):
        """Stop MT5 Bridge application"""
        try:
            logger.info("🛑 Stopping MT5 Bridge Application")
            
            self.running = False
            
            # Use service manager to stop all services
            await service_manager.shutdown_all_services()
            
            # Cancel background tasks
            if self.data_streaming_task:
                self.data_streaming_task.cancel()
            
            if self.message_listening_task:
                self.message_listening_task.cancel()
            
            # Disconnect from WebSocket
            if self.ws_client:
                await self.ws_client.disconnect()
            
            # Disconnect from MT5
            if self.mt5_handler:
                await self.mt5_handler.disconnect()
            
            logger.info("✅ MT5 Bridge stopped")
            
        except Exception as e:
            logger.error(f"Stop application error: {e}")
    
    async def _initialize_mt5(self):
        """Initialize MT5 connection"""
        try:
            mt5_config = self.settings.get_mt5_config()
            
            self.mt5_handler = MT5Handler(
                login=self.settings.mt5.login,
                password=self.settings.mt5.password,
                server=self.settings.mt5.server,
                path=self.settings.mt5.installation_path
            )
            
            success = await self.mt5_handler.connect()
            if not success:
                raise Exception("Failed to connect to MT5")
                
        except Exception as e:
            logger.error(f"MT5 initialization error: {e}")
            raise
    
    async def _initialize_websocket(self):
        """Initialize WebSocket connection"""
        try:
            backend_config = self.settings.network
            
            self.ws_client = WebSocketClient(
                ws_url=backend_config.websocket_url,
                auth_token=getattr(backend_config, 'auth_token', None)
            )
            
            # Register message handlers
            self._register_message_handlers()
            
            success = await self.ws_client.connect()
            if not success:
                raise Exception("Failed to connect to Backend WebSocket")
                
        except Exception as e:
            logger.error(f"WebSocket initialization error: {e}")
            raise
    
    def _register_message_handlers(self):
        """Register WebSocket message handlers"""
        # Original handlers
        self.ws_client.register_handler(MessageTypes.TRADING_SIGNAL, self._handle_trading_signal)
        self.ws_client.register_handler(MessageTypes.CLOSE_POSITION, self._handle_close_position)
        self.ws_client.register_handler(MessageTypes.MODIFY_ORDER, self._handle_modify_order)
        self.ws_client.register_handler(MessageTypes.GET_DATA, self._handle_get_data)
        self.ws_client.register_handler(MessageTypes.EMERGENCY_STOP, self._handle_emergency_stop)
        self.ws_client.register_handler(MessageTypes.CONFIG_UPDATE, self._handle_config_update)
        self.ws_client.register_handler(MessageTypes.DATA_PROCESSED, self._handle_data_processed)
        self.ws_client.register_handler(MessageTypes.CONNECTION_ESTABLISHED, self._handle_connection_established)
        
        # NEW: Enhanced server optimization handlers
        self.ws_client.register_handler(MessageTypes.LIVE_DATA_PROCESSED, self._handle_live_data_processed)
        self.ws_client.register_handler(MessageTypes.POSITIONS_PROCESSED, self._handle_positions_processed)
        self.ws_client.register_handler(MessageTypes.ORDER_RESULT_PROCESSED, self._handle_order_result_processed)
        self.ws_client.register_handler(MessageTypes.HEARTBEAT_RESPONSE, self._handle_heartbeat_response)
        self.ws_client.register_handler(MessageTypes.ERROR_ACKNOWLEDGED, self._handle_error_acknowledged)
        self.ws_client.register_handler(MessageTypes.PERFORMANCE_ALERT, self._handle_performance_alert)
    
    async def _start_background_tasks(self):
        """Start background tasks"""
        # Data streaming task
        self.data_streaming_task = asyncio.create_task(self._data_streaming_loop())
        
        # Message listening task
        self.message_listening_task = asyncio.create_task(self.ws_client.listen_for_messages())
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            asyncio.create_task(self.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def _main_loop(self):
        """Main application loop"""
        try:
            while self.running:
                # Check connections
                await self._check_connections()
                
                # Sleep
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Main loop error: {e}")
    
    async def _check_connections(self):
        """Check and maintain connections"""
        try:
            # Check MT5 connection
            if not await self.mt5_handler.is_connected():
                logger.warning("MT5 connection lost, attempting reconnect...")
                await self.mt5_handler.connect()
            
            # Check WebSocket connection
            if not self.ws_client.is_connected:
                logger.warning("WebSocket connection lost, attempting reconnect...")
                await self.ws_client.auto_reconnect()
                
        except Exception as e:
            logger.error(f"Check connections error: {e}")
    
    async def _data_streaming_loop(self):
        """Stream MT5 data to backend"""
        try:
            while self.running:
                # Send account info every 30 seconds
                account_info = await self.mt5_handler.get_account_info()
                if account_info:
                    await self.ws_client.send_account_info(account_info)
                
                # Send positions
                positions = await self.mt5_handler.get_positions()
                await self.ws_client.send_positions(positions)
                
                # Send orders
                orders = await self.mt5_handler.get_orders()
                await self.ws_client.send_orders(orders)
                
                # Stream tick data for major pairs
                major_pairs = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF"]
                for symbol in major_pairs:
                    tick = await self.mt5_handler.get_tick(symbol)
                    if tick:
                        await self.ws_client.send_tick_data(tick)
                
                # Wait before next update
                await asyncio.sleep(5)  # Update every 5 seconds
                
        except asyncio.CancelledError:
            logger.debug("Data streaming loop cancelled")
        except Exception as e:
            logger.error(f"Data streaming error: {e}")
    
    # Message Handlers
    
    async def _handle_trading_signal(self, data: Dict[str, Any]):
        """Handle trading signal from AI backend"""
        try:
            signal_data = data.get("data", {})
            
            logger.info(f"📈 Received trading signal: {signal_data}")
            
            # Check if trading is enabled
            if not self.settings.app.trading_enabled or self.settings.app.emergency_stop:
                logger.warning("Trading disabled, ignoring signal")
                return
            
            # Check daily trade limit
            if not self._check_daily_trade_limit():
                logger.warning("Daily trade limit exceeded, ignoring signal")
                return
            
            # Extract signal parameters
            symbol = signal_data.get("symbol")
            action = signal_data.get("action")  # "BUY" or "SELL"
            volume = signal_data.get("volume", 0.01)
            sl = signal_data.get("stop_loss")
            tp = signal_data.get("take_profit")
            comment = signal_data.get("comment", "AI Signal")
            
            if not symbol or not action:
                logger.error("Invalid signal: missing symbol or action")
                return
            
            # Place order
            order_type = MT5_ORDER_TYPES.get(action)
            if order_type is None:
                logger.error(f"Invalid order type: {action}")
                return
            
            ticket = await self.mt5_handler.place_order(
                symbol=symbol,
                order_type=order_type,
                volume=volume,
                sl=sl,
                tp=tp,
                comment=comment
            )
            
            # Send result back
            result = {
                "signal_id": signal_data.get("id"),
                "success": ticket is not None,
                "ticket": ticket,
                "message": "Order placed successfully" if ticket else "Order failed"
            }
            
            await self.ws_client.send_trade_result(result)
            
            if ticket:
                self.daily_trades_count += 1
                logger.success(f"✅ Signal executed: {symbol} {action} - Ticket: {ticket}")
            
        except Exception as e:
            logger.error(f"Handle trading signal error: {e}")
            await self.ws_client.send_error(f"Trading signal error: {e}")
    
    async def _handle_close_position(self, data: Dict[str, Any]):
        """Handle close position command"""
        try:
            position_data = data.get("data", {})
            ticket = position_data.get("ticket")
            
            if not ticket:
                logger.error("Close position: missing ticket")
                return
            
            success = await self.mt5_handler.close_position(ticket)
            
            result = {
                "ticket": ticket,
                "success": success,
                "message": "Position closed" if success else "Close failed"
            }
            
            await self.ws_client.send_trade_result(result)
            
        except Exception as e:
            logger.error(f"Handle close position error: {e}")
    
    async def _handle_modify_order(self, data: Dict[str, Any]):
        """Handle modify order command"""
        try:
            # Implementation for order modification
            logger.info("Order modification not implemented yet")
            
        except Exception as e:
            logger.error(f"Handle modify order error: {e}")
    
    async def _handle_get_data(self, data: Dict[str, Any]):
        """Handle data request from backend"""
        try:
            request_type = data.get("request_type")
            
            if request_type == "account_info":
                account_info = await self.mt5_handler.get_account_info()
                await self.ws_client.send_account_info(account_info)
            
            elif request_type == "positions":
                positions = await self.mt5_handler.get_positions()
                await self.ws_client.send_positions(positions)
            
            elif request_type == "orders":
                orders = await self.mt5_handler.get_orders()
                await self.ws_client.send_orders(orders)
            
        except Exception as e:
            logger.error(f"Handle get data error: {e}")
    
    async def _handle_emergency_stop(self, data: Dict[str, Any]):
        """Handle emergency stop command"""
        try:
            logger.critical("🚨 EMERGENCY STOP TRIGGERED")
            
            # Close all positions
            positions = await self.mt5_handler.get_positions()
            for position in positions:
                await self.mt5_handler.close_position(position.ticket)
            
            # Set emergency stop flag
            self.settings.app.emergency_stop = True
            
            logger.warning("All positions closed, trading stopped")
            
        except Exception as e:
            logger.error(f"Handle emergency stop error: {e}")
    
    async def _handle_config_update(self, data: Dict[str, Any]):
        """Handle configuration update"""
        try:
            config_data = data.get("data", {})
            logger.info(f"Configuration update: {config_data}")
            
            # Update settings (implementation depends on requirements)
            
        except Exception as e:
            logger.error(f"Handle config update error: {e}")
    
    async def _handle_data_processed(self, data: Dict[str, Any]):
        """Handle data processed confirmation from backend"""
        try:
            message_data = data.get("data", {})
            logger.debug(f"📊 Backend processed data: {message_data}")
            
            # This is just a confirmation that the backend processed our data
            # No specific action needed, just acknowledge receipt
            
        except Exception as e:
            logger.error(f"Handle data processed error: {e}")
    
    async def _handle_connection_established(self, data: Dict[str, Any]):
        """Handle connection established confirmation from backend"""
        try:
            connection_data = data.get("data", {})
            logger.success(f"✅ Backend connection established: {connection_data}")
            
            # This confirms the backend successfully received our connection
            # No specific action needed, just acknowledge receipt
            
        except Exception as e:
            logger.error(f"Handle connection established error: {e}")
    
    def _check_daily_trade_limit(self) -> bool:
        """Check if daily trade limit is reached"""
        today = datetime.now().date()
        
        # Reset counter if new day
        if self.last_trade_date != today:
            self.daily_trades_count = 0
            self.last_trade_date = today
        
        return self.daily_trades_count < self.settings.app.max_daily_trades
    
    # NEW: Enhanced server optimization message handlers
    
    async def _handle_live_data_processed(self, data: Dict[str, Any]):
        """Handle enhanced live data processed response from server"""
        try:
            response_data = data.get("data", data)
            logger.debug(f"✅ Server processed live data: {response_data.get('status', 'unknown')}")
            
            # Enhanced response includes account balance and processing stats
            if "account_balance" in response_data:
                logger.info(f"💰 Account Balance: {response_data['account_balance']}")
                
            if "equity" in response_data:
                logger.info(f"💎 Equity: {response_data['equity']}")
                
            if "positions_count" in response_data:
                logger.info(f"📊 Open Positions: {response_data['positions_count']}")
            
        except Exception as e:
            logger.error(f"Handle live data processed error: {e}")
    
    async def _handle_positions_processed(self, data: Dict[str, Any]):
        """Handle enhanced positions processed response from server"""
        try:
            response_data = data.get("data", data)
            logger.debug(f"📋 Server processed positions: {response_data.get('status', 'unknown')}")
            
            # Enhanced response includes position summary
            if "position_count" in response_data:
                logger.info(f"📊 Positions processed: {response_data['position_count']}")
                
            if "total_profit" in response_data:
                profit = response_data['total_profit']
                profit_emoji = "💰" if profit >= 0 else "📉"
                logger.info(f"{profit_emoji} Total Profit: {profit}")
            
        except Exception as e:
            logger.error(f"Handle positions processed error: {e}")
    
    async def _handle_order_result_processed(self, data: Dict[str, Any]):
        """Handle enhanced order result processed response from server"""
        try:
            response_data = data.get("data", data)
            logger.debug(f"📝 Server processed order result: {response_data.get('status', 'unknown')}")
            
            # Enhanced response includes order confirmation
            if "order_data" in response_data:
                order_info = response_data['order_data']
                logger.info(f"✅ Order result acknowledged by server: {order_info}")
            
        except Exception as e:
            logger.error(f"Handle order result processed error: {e}")
    
    async def _handle_heartbeat_response(self, data: Dict[str, Any]):
        """Handle enhanced heartbeat response with server stats"""
        try:
            response_data = data.get("data", data)
            logger.debug(f"💓 Enhanced heartbeat response: {response_data.get('server_status', 'unknown')}")
            
            # Enhanced heartbeat includes data flow statistics
            if "data_flow_stats" in response_data:
                stats = response_data['data_flow_stats']
                logger.debug(f"📊 Server Data Flow Stats:")
                logger.debug(f"   Live Updates: {stats.get('live_updates', 0)}")
                logger.debug(f"   Analytical Batches: {stats.get('analytical_batches', 0)}")
                logger.debug(f"   Buffer Size: {stats.get('buffer_size', 0)}")
                
                # Store stats for monitoring
                self.server_stats = stats
            
        except Exception as e:
            logger.error(f"Handle heartbeat response error: {e}")
    
    async def _handle_error_acknowledged(self, data: Dict[str, Any]):
        """Handle enhanced error acknowledgment from server"""
        try:
            response_data = data.get("data", data)
            logger.debug(f"🚨 Server acknowledged error: {response_data.get('handled_by', 'unknown')}")
            
            # Enhanced error handling with server feedback
            if "error_data" in response_data:
                error_info = response_data['error_data']
                logger.info(f"✅ Error handled by server: {error_info}")
            
        except Exception as e:
            logger.error(f"Handle error acknowledged error: {e}")
    
    async def _handle_performance_alert(self, data: Dict[str, Any]):
        """Handle performance monitoring alerts from server"""
        try:
            alert_data = data.get("data", data)
            alert_type = alert_data.get("alert_type", "unknown")
            message = alert_data.get("message", "Performance alert received")
            severity = alert_data.get("severity", "medium")
            
            # Log based on severity
            if severity == "critical":
                logger.critical(f"🚨 CRITICAL PERFORMANCE ALERT: {message}")
            elif severity == "high":
                logger.error(f"⚠️ HIGH PERFORMANCE ALERT: {message}")
            elif severity == "medium":
                logger.warning(f"⚠️ PERFORMANCE ALERT: {message}")
            else:
                logger.info(f"📊 Performance Info: {message}")
            
            # Take action based on alert type
            if alert_type == "high_latency":
                logger.info("🔄 Consider reducing message frequency")
            elif alert_type == "memory_usage":
                logger.info("💾 Consider clearing local buffers")
            elif alert_type == "connection_issues":
                logger.info("🔌 Connection monitoring activated")
            
            # Store performance alerts for trend analysis
            if not hasattr(self, 'performance_alerts'):
                self.performance_alerts = []
            self.performance_alerts.append({
                "timestamp": datetime.now(),
                "alert_type": alert_type,
                "severity": severity,
                "message": message
            })
            
            # Keep only last 50 alerts
            if len(self.performance_alerts) > 50:
                self.performance_alerts = self.performance_alerts[-50:]
            
        except Exception as e:
            logger.error(f"Handle performance alert error: {e}")


async def main():
    """Main entry point"""
    try:
        # Create default config if needed
        create_default_config()
        
        # Start MT5 Bridge
        bridge = MT5Bridge()
        await bridge.start()
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
    finally:
        logger.info("Application finished")


if __name__ == "__main__":
    asyncio.run(main())