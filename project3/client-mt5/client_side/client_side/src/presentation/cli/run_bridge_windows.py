"""
run_bridge_windows.py - Windows-Specific Bridge Runner

🎯 PURPOSE:
Business: Windows-optimized bridge runner with platform-specific features
Technical: Windows platform integration with MT5 terminal management
Domain: Platform Integration/Windows/MT5 Management

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:27.977Z
Session: client-side-ai-brain-full-compliance
Confidence: 89%
Complexity: medium

🧩 PATTERNS USED:
- AI_BRAIN_PLATFORM_INTEGRATION: Platform-specific integration and optimization

📦 DEPENDENCIES:
Internal: bridge_app, mt5_handler
External: sys, os, subprocess, winreg

💡 AI DECISION REASONING:
Windows-specific runner provides optimal integration with Windows MT5 terminal and platform-specific features.

🚀 USAGE:
python run_bridge_windows.py --mt5-path="C:\Program Files\MetaTrader 5"

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

import asyncio
import sys
import os
import time
from pathlib import Path
from datetime import datetime
from typing import Optional
import psutil
import signal

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from src.shared.config.mt5_config import get_mt5_settings, validate_mt5_path


class WindowsCompatibleBridge:
    """
    Windows-compatible MT5 Bridge with no unicode/emoji
    Simplified version for Windows console
    """
    
    def __init__(self):
        # Load configuration
        self.settings = get_mt5_settings()
        
        # Application state
        self.running = False
        self.start_time = None
        
        # Setup basic logging to file only
        self._setup_file_logging()
    
    def _setup_file_logging(self):
        """Setup console-only logging for Windows compatibility"""
        import logging
        
        # Configure console-only logging to avoid file conflicts
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)  # Console only
            ]
        )
        
        self.logger = logging.getLogger('MT5Bridge')
        self.logger.info("Windows-compatible console logging configured")
    
    async def start(self):
        """Start MT5 Bridge application"""
        try:
            self.logger.info("Starting MT5 Bridge Application (Windows Compatible)")
            
            # Validate setup
            if not await self._validate_setup():
                self.logger.error("Setup validation failed")
                return False
            
            # Initialize components
            await self._initialize_components()
            
            # Start background tasks
            await self._start_background_tasks()
            
            self.running = True
            self.start_time = datetime.now()
            
            self.logger.info("MT5 Bridge started successfully")
            self._display_status()
            
            # Main application loop
            await self._main_loop()
            
        except Exception as e:
            self.logger.error(f"Start application error: {e}")
            await self.stop()
    
    async def stop(self):
        """Stop MT5 Bridge application"""
        try:
            self.logger.info("Stopping MT5 Bridge Application")
            self.running = False
            
            # Cleanup components
            if hasattr(self, 'mt5_handler') and self.mt5_handler:
                await self.mt5_handler.disconnect()
            
            if hasattr(self, 'ws_client') and self.ws_client:
                await self.ws_client.disconnect()
            
            self.logger.info("MT5 Bridge stopped")
            
        except Exception as e:
            self.logger.error(f"Stop application error: {e}")
    
    async def _validate_setup(self):
        """Validate MT5 Bridge setup"""
        try:
            # Check MT5 installation
            if not validate_mt5_path(self.settings.mt5_path):
                self.logger.error(f"MT5 not found at: {self.settings.mt5_path}")
                return False
            
            # Check configuration
            if not self.settings.mt5_login or not self.settings.mt5_password:
                self.logger.error("MT5 credentials not configured")
                return False
            
            self.logger.info("Setup validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Setup validation error: {e}")
            return False
    
    async def _initialize_components(self):
        """Initialize MT5 and WebSocket components"""
        try:
            # Initialize MT5
            await self._initialize_mt5()
            
            # Initialize WebSocket
            await self._initialize_websocket()
            
        except Exception as e:
            self.logger.error(f"Component initialization error: {e}")
            raise
    
    async def _initialize_mt5(self):
        """Initialize MT5 connection"""
        try:
            from mt5_handler import MT5Handler
            
            mt5_config = self.settings.mt5_config
            
            self.mt5_handler = MT5Handler(
                login=mt5_config.login,
                password=mt5_config.password,
                server=mt5_config.server,
                path=mt5_config.path
            )
            
            success = await self.mt5_handler.connect()
            if not success:
                raise Exception("Failed to connect to MT5")
            
            self.logger.info("MT5 connection initialized")
                
        except Exception as e:
            self.logger.error(f"MT5 initialization error: {e}")
            raise
    
    async def _initialize_websocket(self):
        """Initialize WebSocket connection"""
        try:
            from websocket_client import WebSocketClient
            
            backend_config = self.settings.backend_config
            
            self.ws_client = WebSocketClient(
                ws_url=backend_config.ws_url,
                auth_token=backend_config.auth_token
            )
            
            # Register basic handlers
            self._register_message_handlers()
            
            success = await self.ws_client.connect()
            if success:
                self.logger.info("WebSocket connection initialized")
            else:
                self.logger.warning("WebSocket connection failed, will retry later")
                
        except Exception as e:
            self.logger.error(f"WebSocket initialization error: {e}")
            # Don't raise - can work without WebSocket
    
    def _register_message_handlers(self):
        """Register WebSocket message handlers"""
        try:
            from websocket_client import MessageTypes
            
            self.ws_client.register_handler(MessageTypes.TRADING_SIGNAL, self._handle_trading_signal)
            self.ws_client.register_handler(MessageTypes.GET_DATA, self._handle_get_data)
            self.ws_client.register_handler(MessageTypes.EMERGENCY_STOP, self._handle_emergency_stop)
            
        except Exception as e:
            self.logger.error(f"Handler registration error: {e}")
    
    def _display_status(self):
        """Display current status"""
        print("\n" + "="*60)
        print("MT5 BRIDGE - WINDOWS COMPATIBLE VERSION")
        print("="*60)
        print(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S') if self.start_time else 'Unknown'}")
        print(f"MT5: {'Connected' if hasattr(self, 'mt5_handler') and self.mt5_handler else 'Disconnected'}")
        print(f"WebSocket: {'Connected' if hasattr(self, 'ws_client') and self.ws_client and self.ws_client.is_connected else 'Disconnected'}")
        print(f"Trading: {'ENABLED' if self.settings.trading_enabled else 'DISABLED'}")
        print(f"Simulation: {'YES' if self.settings.simulation_mode else 'NO'}")
        print("="*60 + "\n")
    
    async def _main_loop(self):
        """Main application loop"""
        try:
            while self.running:
                # Basic health check
                await self._health_check()
                
                # Sleep
                await asyncio.sleep(5)
                
        except Exception as e:
            self.logger.error(f"Main loop error: {e}")
    
    async def _start_background_tasks(self):
        """Start background tasks for data streaming"""
        try:
            # Start data streaming task
            self.data_streaming_task = asyncio.create_task(self._data_streaming_loop())
            
            # Start WebSocket message listening task
            if hasattr(self, 'ws_client') and self.ws_client and self.ws_client.is_connected:
                self.ws_listening_task = asyncio.create_task(self.ws_client.listen_for_messages())
                
            self.logger.info("Background tasks started")
            
        except Exception as e:
            self.logger.error(f"Background tasks start error: {e}")
    
    async def _data_streaming_loop(self):
        """Stream MT5 data to backend"""
        try:
            self.logger.info("Starting data streaming loop")
            
            while self.running:
                try:
                    # Send account info every 30 seconds
                    if hasattr(self, 'mt5_handler') and self.mt5_handler:
                        account_info = await self.mt5_handler.get_account_info()
                        if account_info and hasattr(self, 'ws_client') and self.ws_client:
                            await self.ws_client.send_account_info(account_info)
                    
                    # Send positions
                    if hasattr(self, 'mt5_handler') and self.mt5_handler:
                        positions = await self.mt5_handler.get_positions()
                        if hasattr(self, 'ws_client') and self.ws_client:
                            await self.ws_client.send_positions(positions)
                    
                    # Send orders
                    if hasattr(self, 'mt5_handler') and self.mt5_handler:
                        orders = await self.mt5_handler.get_orders()
                        if hasattr(self, 'ws_client') and self.ws_client:
                            await self.ws_client.send_orders(orders)
                    
                    # Stream tick data for major pairs
                    major_pairs = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF"]
                    if hasattr(self, 'mt5_handler') and self.mt5_handler:
                        for symbol in major_pairs:
                            tick = await self.mt5_handler.get_tick(symbol)
                            if tick and hasattr(self, 'ws_client') and self.ws_client:
                                await self.ws_client.send_tick_data(tick)
                    
                    # Wait before next update
                    await asyncio.sleep(5)  # Update every 5 seconds
                    
                except Exception as e:
                    self.logger.error(f"Data streaming error: {e}")
                    await asyncio.sleep(1)
                    
        except asyncio.CancelledError:
            self.logger.info("Data streaming loop cancelled")
        except Exception as e:
            self.logger.error(f"Data streaming loop error: {e}")
    
    async def _health_check(self):
        """Basic health check"""
        try:
            # Check MT5 connection
            if hasattr(self, 'mt5_handler') and self.mt5_handler:
                if not await self.mt5_handler.is_connected():
                    self.logger.warning("MT5 connection lost, attempting reconnect...")
                    await self.mt5_handler.connect()
            
            # Check WebSocket connection
            if hasattr(self, 'ws_client') and self.ws_client and not self.ws_client.is_connected:
                self.logger.warning("WebSocket connection lost, attempting reconnect...")
                await self.ws_client.auto_reconnect()
                
        except Exception as e:
            self.logger.error(f"Health check error: {e}")
    
    # Message Handlers
    
    async def _handle_trading_signal(self, data):
        """Handle trading signal"""
        try:
            self.logger.info(f"Received trading signal: {data}")
            
            if not self.settings.trading_enabled:
                self.logger.warning("Trading disabled, ignoring signal")
                return
            
            # Process signal (simplified)
            signal_data = data.get("data", {})
            symbol = signal_data.get("symbol")
            action = signal_data.get("action")
            
            if symbol and action:
                self.logger.info(f"Processing signal: {symbol} {action}")
                # Add actual trading logic here
            
        except Exception as e:
            self.logger.error(f"Handle trading signal error: {e}")
    
    async def _handle_get_data(self, data):
        """Handle data request"""
        try:
            request_type = data.get("request_type")
            self.logger.info(f"Data request: {request_type}")
            
            if request_type == "account_info" and hasattr(self, 'mt5_handler'):
                account_info = await self.mt5_handler.get_account_info()
                if account_info and hasattr(self, 'ws_client'):
                    await self.ws_client.send_account_info(account_info)
            
        except Exception as e:
            self.logger.error(f"Handle get data error: {e}")
    
    async def _handle_emergency_stop(self, data):
        """Handle emergency stop"""
        try:
            self.logger.critical("EMERGENCY STOP TRIGGERED")
            
            # Close all positions if MT5 is available
            if hasattr(self, 'mt5_handler') and self.mt5_handler:
                positions = await self.mt5_handler.get_positions()
                for position in positions:
                    await self.mt5_handler.close_position(position.ticket)
            
            # Set emergency stop flag
            self.settings.emergency_stop = True
            
            self.logger.warning("Emergency stop completed")
            
        except Exception as e:
            self.logger.error(f"Handle emergency stop error: {e}")


async def main():
    """Main entry point"""
    try:
        print("MT5 Bridge - Windows Compatible Version")
        print("Starting application...")
        
        # Start bridge
        bridge = WindowsCompatibleBridge()
        await bridge.start()
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
    except Exception as e:
        print(f"Application error: {e}")
    finally:
        print("Application finished")


if __name__ == "__main__":
    # Set up proper signal handling for Windows
    if sys.platform == "win32":
        # Windows signal handling
        def signal_handler(signum, frame):
            print(f"Received signal {signum}, shutting down...")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    asyncio.run(main())