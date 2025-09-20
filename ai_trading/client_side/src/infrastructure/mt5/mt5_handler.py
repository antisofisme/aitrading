"""
mt5_handler.py - MT5 Integration System

🎯 PURPOSE:
Business: Core MT5 trading operations with real-time market data and order execution
Technical: Comprehensive MT5 client with centralized infrastructure integration
Domain: MT5/Trading/Market Data

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:27.726Z
Session: client-side-ai-brain-full-compliance
Confidence: 95%
Complexity: high

🧩 PATTERNS USED:
- AI_BRAIN_MT5_INTEGRATION: MT5 trading system integration with centralized infrastructure
- CENTRALIZED_INFRASTRUCTURE: Uses AI Brain centralized logging and error handling

📦 DEPENDENCIES:
Internal: centralized_logger, error_handler, config_manager, performance_tracker
External: MetaTrader5, pandas, numpy, psutil, asyncio

💡 AI DECISION REASONING:
MT5 integration selected for proven reliability, comprehensive API access, and strong community support. Centralized infrastructure ensures AI Brain pattern consistency.

🚀 USAGE:
handler = MT5Handler(); await handler.connect(); tick_data = await handler.get_tick("EURUSD")

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    # Create mock MT5 for development without MetaTrader5
    MT5_AVAILABLE = False
    class MockMT5:
        # Order types
        ORDER_TYPE_BUY = 0
        ORDER_TYPE_SELL = 1
        ORDER_TYPE_BUY_LIMIT = 2
        ORDER_TYPE_SELL_LIMIT = 3
        ORDER_TYPE_BUY_STOP = 4
        ORDER_TYPE_SELL_STOP = 5
        
        # Timeframes
        TIMEFRAME_M1 = 1
        TIMEFRAME_M5 = 5
        TIMEFRAME_M15 = 15
        TIMEFRAME_M30 = 30
        TIMEFRAME_H1 = 16385
        TIMEFRAME_H4 = 16388
        TIMEFRAME_D1 = 16408
        TIMEFRAME_W1 = 32769
        TIMEFRAME_MN1 = 49153
        
        @staticmethod
        def initialize(): 
            print("⚠️ Mock MT5: Simulated initialization (MetaTrader5 not available)")
            return False
        @staticmethod  
        def shutdown(): 
            print("⚠️ Mock MT5: Simulated shutdown")
            pass
        @staticmethod
        def terminal_info(): 
            return {"name": "Mock Terminal", "version": "5.00", "connected": False}
        @staticmethod
        def account_info(): 
            return {"login": 0, "balance": 0.0, "equity": 0.0}
        @staticmethod
        def copy_rates_from_pos(symbol, timeframe, start_pos, count):
            return []
        @staticmethod
        def symbol_info(symbol):
            return None
        @staticmethod
        def symbols_get():
            return []
    mt5 = MockMT5()
import pandas as pd
import numpy as np
import subprocess
import os
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import pytz

# CENTRALIZED INFRASTRUCTURE IMPORTS
from src.infrastructure import (
    # Centralized Logging
    get_logger,
    
    # Centralized Configuration  
    get_config,
    get_client_settings,
    
    # Centralized Error Handling
    handle_error,
    handle_mt5_error,
    ErrorCategory,
    ErrorSeverity,
    
    # Performance Tracking
    performance_tracked,
    track_performance,
    
    # Validation
    validate_field,
    validate_mt5_connection,
    validate_trading_symbol
)


@dataclass
class MT5AccountInfo:
    """MT5 Account Information"""
    login: int
    balance: float
    equity: float
    margin: float
    free_margin: float
    margin_level: float
    currency: str
    server: str
    company: str


@dataclass
class MT5Symbol:
    """MT5 Symbol Information"""
    name: str
    description: str
    currency_base: str
    currency_profit: str
    currency_margin: str
    point: float
    digits: int
    spread: int
    volume_min: float
    volume_max: float
    volume_step: float


@dataclass
class MT5Tick:
    """MT5 Tick Data"""
    symbol: str
    time: datetime
    bid: float
    ask: float
    last: float
    volume: int
    spread: float


@dataclass
class MT5Position:
    """MT5 Position Information"""
    ticket: int
    symbol: str
    type: int
    volume: float
    price_open: float
    price_current: float
    profit: float
    swap: float
    commission: float
    time: datetime
    comment: str


@dataclass
class MT5Order:
    """MT5 Order Information"""
    ticket: int
    symbol: str
    type: int
    volume: float
    price_open: float
    sl: float
    tp: float
    time_setup: datetime
    comment: str
    magic: int


@dataclass
class MT5Deal:
    """MT5 Deal/Trade History"""
    ticket: int
    order: int
    time: datetime
    symbol: str
    type: int
    entry: int
    volume: float
    price: float
    commission: float
    swap: float
    profit: float
    fee: float
    comment: str
    magic: int


class MT5Handler:
    """
    MT5 Handler Class with Centralized Infrastructure
    Manages all MetaTrader 5 operations with enhanced logging, error handling, and performance tracking
    """
    
    def __init__(self, login: int, password: str, server: str, path: str = None):
        # CENTRALIZED INFRASTRUCTURE INITIALIZATION
        # Initialize centralized logger first
        self.logger = get_logger('mt5_handler', context={
            'component': 'mt5_handler',
            'account': str(login),
            'server': server,
            'version': '2.0.0-centralized'
        })
        
        # CENTRALIZED VALIDATION - Validate MT5 connection parameters at initialization
        validation_result = validate_mt5_connection(login, server, password)
        if not validation_result.is_valid:
            error_messages = [error.message for error in validation_result.errors]
            raise ValueError(f"MT5Handler initialization failed - Invalid parameters: {'; '.join(error_messages)}")
        
        # Load centralized configuration
        try:
            self.mt5_config = get_config('mt5')
            self.trading_config = get_config('trading')
        except Exception as e:
            error_context = handle_error(
                error=e,
                category=ErrorCategory.CONFIG,
                severity=ErrorSeverity.HIGH,
                component='mt5_handler',
                operation='configuration_loading'
            )
            self.logger.error(f"Failed to load MT5 configuration: {error_context.message}")
            # Use default config as fallback
            self.mt5_config = {}
            self.trading_config = {}
        
        # Initialize MT5 connection parameters
        self.login = login
        self.password = password
        self.server = server
        self.path = path or self.mt5_config.get('installation_path', r"C:\Program Files\MetaTrader 5\terminal64.exe")
        self.connected = False
        self.account_info = None
        self.timezone = pytz.timezone('Etc/UTC')
        
        # Centralized system status logging
        self.logger.info(f"🚀 MT5Handler initialized with centralized infrastructure for account {login} on {server}")
        self.logger.info(f"📦 MT5 Terminal Path: {self.path}")
        self.logger.info(f"✅ Connection parameters validation passed")
        
    def is_mt5_running(self) -> bool:
        """Check if MT5 terminal is already running"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                if proc.info['name'] and 'terminal64.exe' in proc.info['name'].lower():
                    return True
            return False
        except Exception as e:
            self.logger.warning(f"Could not check MT5 process: {e}")
            return False
    
    def start_mt5_terminal(self) -> bool:
        """Start MT5 terminal if not running"""
        try:
            if self.is_mt5_running():
                self.logger.info("✅ MT5 terminal already running")
                return True
            
            self.logger.info("🚀 Starting MT5 terminal...")
            
            # Check if MT5 executable exists
            if not os.path.exists(self.path):
                self.logger.error(f"❌ MT5 executable not found at: {self.path}")
                return False
            
            # Start MT5 terminal
            subprocess.Popen([self.path], shell=True)
            
            # Wait for MT5 to start
            self.logger.info("⏳ Waiting for MT5 terminal to start...")
            for i in range(30):  # Wait up to 30 seconds
                time.sleep(1)
                if self.is_mt5_running():
                    self.logger.success(f"✅ MT5 terminal started successfully!")
                    time.sleep(3)  # Additional wait for full initialization
                    return True
                self.logger.info(f"   Waiting... ({i+1}/30)")
            
            self.logger.error("❌ MT5 terminal failed to start within 30 seconds")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error starting MT5 terminal: {e}")
            return False

    @performance_tracked("mt5_initialization", "mt5_handler")
    async def initialize(self) -> bool:
        """Initialize and connect to MT5 terminal with auto-start - Enhanced with centralized infrastructure"""
        try:
            with track_performance("mt5_terminal_startup", "mt5_handler"):
                # Step 1: Ensure MT5 terminal is running
                if not self.start_mt5_terminal():
                    error_context = handle_mt5_error(
                        Exception("Failed to start MT5 terminal"),
                        operation="terminal_startup"
                    )
                    self.logger.error(f"❌ Failed to start MT5 terminal: {error_context.message}")
                    return False
            
            with track_performance("mt5_connection_init", "mt5_handler"):
                # Step 2: Initialize MT5 connection
                self.logger.info("🔌 Initializing MT5 connection...")
                if not mt5.initialize(path=self.path):
                    error_context = handle_mt5_error(
                        Exception("MT5 initialize failed"),
                        operation="connection_initialization"
                    )
                    self.logger.error(f"❌ MT5 initialize failed with path: {self.path}")
                    # Display recovery suggestions from centralized error handler
                    for suggestion in error_context.recovery_suggestions:
                        self.logger.info(f"💡 Recovery: {suggestion}")
                    return False
            
            with track_performance("mt5_login", "mt5_handler"):
                # Step 3: Login to MT5 account
                self.logger.info(f"🔐 Logging in to account {self.login} on {self.server}...")
                if not mt5.login(self.login, password=self.password, server=self.server):
                    error_code = mt5.last_error()
                    login_error = Exception(f"MT5 login failed with error code: {error_code}")
                    error_context = handle_mt5_error(login_error, operation="account_login")
                    
                    self.logger.error(f"❌ MT5 login failed: {error_code}")
                    
                    # Display recovery suggestions from centralized error handler
                    for suggestion in error_context.recovery_suggestions:
                        self.logger.info(f"💡 Recovery: {suggestion}")
                    
                    # Provide specific error code guidance
                    if error_code == 10004:
                        self.logger.info("💡 Error 10004: Invalid account credentials")
                        self.logger.info("   - Check login, password, and server name")
                        self.logger.info("   - Make sure account is active")
                    elif error_code == 10016:
                        self.logger.info("💡 Error 10016: No connection to trade server")
                        self.logger.info("   - Check internet connection")
                        self.logger.info("   - Verify server name (e.g., 'FBS-Demo')")
                    elif error_code == 10017:
                        self.logger.info("💡 Error 10017: Wrong account credentials")
                        self.logger.info("   - Double-check login and password")
                    
                    mt5.shutdown()
                    return False
            
            with track_performance("account_info_retrieval", "mt5_handler"):
                # Step 4: Verify connection and get account info
                self.connected = True
                self.account_info = await self.get_account_info()
            
            # Log successful connection with comprehensive details
            self.logger.success(f"✅ Successfully connected to MT5!")
            self.logger.info(f"📊 Server: {self.server}")
            self.logger.info(f"👤 Account: {self.login}")
            self.logger.info(f"💰 Balance: {self.account_info.balance if self.account_info else 'N/A'} {self.account_info.currency if self.account_info else ''}")
            self.logger.info(f"🏢 Broker: {self.account_info.company if self.account_info else 'N/A'}")
            
            return True
            
        except Exception as e:
            # Use centralized error handling
            error_context = handle_mt5_error(e, operation="mt5_initialization")
            self.logger.error(f"MT5 connection error: {error_context.message}")
            
            # Log recovery suggestions
            for suggestion in error_context.recovery_suggestions:
                self.logger.info(f"💡 Recovery: {suggestion}")
            
            return False
    
    async def shutdown(self):
        """Shutdown and disconnect from MT5 terminal"""
        try:
            if self.connected:
                mt5.shutdown()
                self.connected = False
                self.logger.info("🔌 Disconnected from MT5")
        except Exception as e:
            self.logger.error(f"MT5 disconnect error: {e}")
    
    async def connect(self) -> bool:
        """Alias for initialize() method - backward compatibility"""
        return await self.initialize()
    
    async def disconnect(self):
        """Alias for shutdown() method - backward compatibility"""
        await self.shutdown()
    
    async def is_connected(self) -> bool:
        """Check if MT5 is connected"""
        try:
            if not self.connected:
                return False
            
            # Test connection by getting terminal info
            terminal_info = mt5.terminal_info()
            return terminal_info is not None
            
        except Exception as e:
            self.logger.error(f"MT5 connection check error: {e}")
            return False
    
    async def get_account_info(self) -> Optional[MT5AccountInfo]:
        """Get MT5 account information"""
        try:
            if not await self.is_connected():
                return None
            
            account_info = mt5.account_info()
            if account_info is None:
                return None
            
            return MT5AccountInfo(
                login=account_info.login,
                balance=account_info.balance,
                equity=account_info.equity,
                margin=account_info.margin,
                free_margin=account_info.margin_free,
                margin_level=account_info.margin_level,
                currency=account_info.currency,
                server=account_info.server,
                company=account_info.company
            )
            
        except Exception as e:
            self.logger.error(f"Get account info error: {e}")
            return None
    
    async def get_symbols(self) -> List[MT5Symbol]:
        """Get available symbols"""
        try:
            if not await self.is_connected():
                return []
            
            symbols = mt5.symbols_get()
            if symbols is None:
                return []
            
            result = []
            for symbol in symbols:
                result.append(MT5Symbol(
                    name=symbol.name,
                    description=symbol.description,
                    currency_base=symbol.currency_base,
                    currency_profit=symbol.currency_profit,
                    currency_margin=symbol.currency_margin,
                    point=symbol.point,
                    digits=symbol.digits,
                    spread=symbol.spread,
                    volume_min=symbol.volume_min,
                    volume_max=symbol.volume_max,
                    volume_step=symbol.volume_step
                ))
            
            return result
            
        except Exception as e:
            self.logger.error(f"Get symbols error: {e}")
            return []
    
    async def select_symbol(self, symbol: str) -> bool:
        """Select a symbol for trading and data streaming"""
        try:
            if not await self.is_connected():
                return False
            
            # Check if symbol exists
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                self.logger.error(f"Symbol {symbol} not found")
                return False
            
            # If symbol is not visible, select it
            if not symbol_info.visible:
                selected = mt5.symbol_select(symbol, True)
                if not selected:
                    self.logger.error(f"Failed to select symbol {symbol}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Select symbol error for {symbol}: {e}")
            return False
    
    async def get_tick(self, symbol: str) -> Optional[MT5Tick]:
        """Get latest tick for symbol"""
        try:
            if not await self.is_connected():
                return None
            
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return None
            
            return MT5Tick(
                symbol=symbol,
                time=datetime.fromtimestamp(tick.time, self.timezone),
                bid=tick.bid,
                ask=tick.ask,
                last=tick.last,
                volume=tick.volume,
                spread=(tick.ask - tick.bid)
            )
            
        except Exception as e:
            self.logger.error(f"Get tick error for {symbol}: {e}")
            return None
    
    async def get_rates(self, symbol: str, timeframe: int, count: int = 100) -> Optional[pd.DataFrame]:
        """Get historical rates for symbol"""
        try:
            if not await self.is_connected():
                return None
            
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            if rates is None:
                return None
            
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Get rates error for {symbol}: {e}")
            return None
    
    async def get_positions(self) -> List[MT5Position]:
        """Get all open positions"""
        try:
            if not await self.is_connected():
                return []
            
            positions = mt5.positions_get()
            if positions is None:
                return []
            
            result = []
            for pos in positions:
                result.append(MT5Position(
                    ticket=pos.ticket,
                    symbol=pos.symbol,
                    type=pos.type,
                    volume=pos.volume,
                    price_open=pos.price_open,
                    price_current=pos.price_current,
                    profit=pos.profit,
                    swap=pos.swap,
                    commission=getattr(pos, 'commission', 0.0),
                    time=datetime.fromtimestamp(pos.time, self.timezone),
                    comment=pos.comment
                ))
            
            return result
            
        except Exception as e:
            self.logger.error(f"Get positions error: {e}")
            return []
    
    async def get_orders(self) -> List[MT5Order]:
        """Get all pending orders"""
        try:
            if not await self.is_connected():
                return []
            
            orders = mt5.orders_get()
            if orders is None:
                return []
            
            result = []
            for order in orders:
                result.append(MT5Order(
                    ticket=order.ticket,
                    symbol=order.symbol,
                    type=order.type,
                    volume=getattr(order, 'volume', getattr(order, 'volume_initial', 0.0)),
                    price_open=getattr(order, 'price_open', 0.0),
                    sl=getattr(order, 'sl', 0.0),
                    tp=getattr(order, 'tp', 0.0),
                    time_setup=datetime.fromtimestamp(order.time_setup, self.timezone),
                    comment=getattr(order, 'comment', ''),
                    magic=getattr(order, 'magic', 0)
                ))
            
            return result
            
        except Exception as e:
            self.logger.error(f"Get orders error: {e}")
            return []
    
    async def get_deals_history(self, days: int = None) -> List[MT5Deal]:
        """Get historical deals/trades - ALL TIME if days=None"""
        try:
            if not await self.is_connected():
                return []
            
            # Calculate date range with smart fallback
            if days is None:
                self.logger.info("📜 Fetching ALL TIME deals history...")
                # Try progressively shorter periods if longer ones fail
                periods_to_try = [1095, 365, 180, 90, 30]  # 3 years, 1 year, 6 months, 3 months, 1 month
                deals = None
                
                for period in periods_to_try:
                    try:
                        from_date = datetime.now() - timedelta(days=period)
                        to_date = datetime.now()
                        deals = mt5.history_deals_get(from_date, to_date)
                        if deals is not None:
                            self.logger.debug(f"✅ Successfully retrieved deals for {period} days period ({len(deals)} deals)")
                            break
                        else:
                            self.logger.debug(f"⚠️ No deals found for {period} days period, trying shorter period...")
                    except Exception as e:
                        self.logger.warning(f"⚠️ Failed to get deals for {period} days: {e}, trying shorter period...")
                        continue
                
                if deals is None:
                    self.logger.warning("⚠️ No deals history found for any period - this might be a new demo account")
                    self.logger.info("💡 Recommendation: Try placing some test trades in MT5 terminal first")
                    return []
            else:
                from_date = datetime.now() - timedelta(days=days)
                to_date = datetime.now()
                deals = mt5.history_deals_get(from_date, to_date)
                if deals is None:
                    return []
            
            result = []
            for deal in deals:
                result.append(MT5Deal(
                    ticket=deal.ticket,
                    order=deal.order,
                    time=datetime.fromtimestamp(deal.time, self.timezone),
                    symbol=deal.symbol,
                    type=deal.type,
                    entry=deal.entry,
                    volume=deal.volume,
                    price=deal.price,
                    commission=deal.commission,
                    swap=deal.swap,
                    profit=deal.profit,
                    fee=getattr(deal, 'fee', 0.0),
                    comment=deal.comment,
                    magic=deal.magic
                ))
            
            return result
            
        except Exception as e:
            self.logger.error(f"Get deals history error: {e}")
            return []
    
    async def get_orders_history(self, days: int = None) -> List[MT5Order]:
        """Get historical orders - ALL TIME if days=None"""
        try:
            if not await self.is_connected():
                return []
            
            # Calculate date range with smart fallback
            if days is None:
                self.logger.info("📜 Fetching ALL TIME orders history...")
                # Try progressively shorter periods if longer ones fail
                periods_to_try = [1095, 365, 180, 90, 30]  # 3 years, 1 year, 6 months, 3 months, 1 month
                orders = None
                
                for period in periods_to_try:
                    try:
                        from_date = datetime.now() - timedelta(days=period)
                        to_date = datetime.now()
                        orders = mt5.history_orders_get(from_date, to_date)
                        if orders is not None:
                            self.logger.debug(f"✅ Successfully retrieved orders for {period} days period ({len(orders)} orders)")
                            break
                        else:
                            self.logger.debug(f"⚠️ No orders found for {period} days period, trying shorter period...")
                    except Exception as e:
                        self.logger.warning(f"⚠️ Failed to get orders for {period} days: {e}, trying shorter period...")
                        continue
                
                if orders is None:
                    self.logger.warning("⚠️ No orders history found for any period - this might be a new demo account")
                    self.logger.info("💡 Recommendation: Try placing some test orders in MT5 terminal first")
                    return []
            else:
                from_date = datetime.now() - timedelta(days=days)
                to_date = datetime.now()
                orders = mt5.history_orders_get(from_date, to_date)
                if orders is None:
                    return []
            
            result = []
            for order in orders:
                result.append(MT5Order(
                    ticket=order.ticket,
                    symbol=order.symbol,
                    type=order.type,
                    volume=getattr(order, 'volume', getattr(order, 'volume_initial', 0.0)),
                    price_open=getattr(order, 'price_open', 0.0),
                    sl=getattr(order, 'sl', 0.0),
                    tp=getattr(order, 'tp', 0.0),
                    time_setup=datetime.fromtimestamp(order.time_setup, self.timezone),
                    comment=getattr(order, 'comment', ''),
                    magic=getattr(order, 'magic', 0)
                ))
            
            return result
            
        except Exception as e:
            self.logger.error(f"Get orders history error: {e}")
            return []
    
    @performance_tracked("mt5_place_order", "mt5_handler")
    async def place_order(self, symbol: str, order_type: int, volume: float, 
                         price: float = None, sl: float = None, tp: float = None,
                         comment: str = "AI Trading", magic: int = 234000) -> Optional[int]:
        """Place a trading order - Enhanced with centralized validation and performance tracking"""
        try:
            # CENTRALIZED VALIDATION - Validate trading symbol
            symbol_validation = validate_trading_symbol(symbol)
            if not symbol_validation.is_valid:
                error_messages = [error.message for error in symbol_validation.errors]
                self.logger.error(f"Invalid trading symbol {symbol}: {'; '.join(error_messages)}")
                return None
            
            # CENTRALIZED VALIDATION - Validate trading volume
            volume_validation = validate_field('trading_volume', volume, 'trading_volume')
            if not volume_validation.is_valid:
                error_messages = [error.message for error in volume_validation.errors]
                self.logger.error(f"Invalid trading volume {volume}: {'; '.join(error_messages)}")
                return None
            
            if not await self.is_connected():
                self.logger.error("Not connected to MT5")
                return None
            
            with track_performance("symbol_info_retrieval", "mt5_handler"):
                # Get symbol info
                symbol_info = mt5.symbol_info(symbol)
                if symbol_info is None:
                    self.logger.error(f"Symbol {symbol} not found")
                    return None
            
            with track_performance("price_calculation", "mt5_handler"):
                # If no price specified, use current market price
                if price is None:
                    tick = mt5.symbol_info_tick(symbol)
                    if tick is None:
                        self.logger.error(f"Cannot get tick for {symbol}")
                        return None
                    
                    if order_type == mt5.ORDER_TYPE_BUY:
                        price = tick.ask
                    elif order_type == mt5.ORDER_TYPE_SELL:
                        price = tick.bid
            
            with track_performance("order_preparation", "mt5_handler"):
                # Prepare order request
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": symbol,
                    "volume": volume,
                    "type": order_type,
                    "price": price,
                    "sl": sl,
                    "tp": tp,
                    "deviation": 20,
                    "magic": magic,
                    "comment": comment,
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }
            
            with track_performance("order_execution", "mt5_handler"):
                # Send order
                result = mt5.order_send(request)
                
                if result.retcode != mt5.TRADE_RETCODE_DONE:
                    # Use centralized error handling for order failures
                    order_error = Exception(f"Order failed: {result.retcode} - {result.comment}")
                    error_context = handle_mt5_error(order_error, operation="order_placement")
                    self.logger.error(f"Order failed: {result.retcode} - {result.comment}")
                    
                    # Log recovery suggestions
                    for suggestion in error_context.recovery_suggestions:
                        self.logger.info(f"💡 Recovery: {suggestion}")
                    
                    return None
                
                self.logger.success(f"✅ Order placed: {result.order} - {symbol} {volume} lots")
                return result.order
            
        except Exception as e:
            # Use centralized error handling
            error_context = handle_mt5_error(e, operation="place_order")
            self.logger.error(f"Place order error: {error_context.message}")
            
            # Log recovery suggestions
            for suggestion in error_context.recovery_suggestions:
                self.logger.info(f"💡 Recovery: {suggestion}")
            
            return None
    
    @performance_tracked("mt5_close_position", "mt5_handler")
    async def close_position(self, ticket: int) -> bool:
        """Close a position by ticket - Enhanced with centralized validation and performance tracking"""
        try:
            # CENTRALIZED VALIDATION - Validate ticket number
            ticket_validation = validate_field('ticket', ticket, 'trading_ticket')
            if not ticket_validation.is_valid:
                error_messages = [error.message for error in ticket_validation.errors]
                self.logger.error(f"Invalid ticket number {ticket}: {'; '.join(error_messages)}")
                return False
            
            if not await self.is_connected():
                return False
            
            with track_performance("position_retrieval", "mt5_handler"):
                # Get position info
                positions = mt5.positions_get(ticket=ticket)
                if not positions:
                    self.logger.error(f"Position {ticket} not found")
                    return False
                
                position = positions[0]
            
            with track_performance("close_order_preparation", "mt5_handler"):
                # Determine opposite order type
                if position.type == mt5.POSITION_TYPE_BUY:
                    order_type = mt5.ORDER_TYPE_SELL
                else:
                    order_type = mt5.ORDER_TYPE_BUY
                
                # Get current price
                tick = mt5.symbol_info_tick(position.symbol)
                if tick is None:
                    self.logger.error(f"Cannot get tick for {position.symbol}")
                    return False
                
                price = tick.bid if order_type == mt5.ORDER_TYPE_SELL else tick.ask
                
                # Prepare close request
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": position.symbol,
                    "volume": position.volume,
                    "type": order_type,
                    "position": ticket,
                    "price": price,
                    "deviation": 20,
                    "magic": position.magic,
                    "comment": "Close by AI",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }
            
            with track_performance("close_order_execution", "mt5_handler"):
                # Send close request
                result = mt5.order_send(request)
                
                if result.retcode != mt5.TRADE_RETCODE_DONE:
                    # Use centralized error handling for close position failures
                    close_error = Exception(f"Close position failed: {result.retcode} - {result.comment}")
                    error_context = handle_mt5_error(close_error, operation="position_close")
                    self.logger.error(f"Close position failed: {result.retcode} - {result.comment}")
                    
                    # Log recovery suggestions
                    for suggestion in error_context.recovery_suggestions:
                        self.logger.info(f"💡 Recovery: {suggestion}")
                    
                    return False
                
                self.logger.success(f"✅ Position closed: {ticket}")
                return True
            
        except Exception as e:
            # Use centralized error handling
            error_context = handle_mt5_error(e, operation="close_position")
            self.logger.error(f"Close position error: {error_context.message}")
            
            # Log recovery suggestions
            for suggestion in error_context.recovery_suggestions:
                self.logger.info(f"💡 Recovery: {suggestion}")
            
            return False
    
    async def get_trading_hours(self, symbol: str) -> Dict[str, Any]:
        """Get trading hours for symbol"""
        try:
            if not await self.is_connected():
                return {}
            
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return {}
            
            return {
                "symbol": symbol,
                "trade_mode": symbol_info.trade_mode,
                "start_time": symbol_info.start_time,
                "expiration_time": symbol_info.expiration_time,
                "sessions_quotes": symbol_info.sessions_quotes,
                "sessions_trades": symbol_info.sessions_trades
            }
            
        except Exception as e:
            self.logger.error(f"Get trading hours error: {e}")
            return {}


# Constants for MT5 order types
MT5_ORDER_TYPES = {
    "BUY": mt5.ORDER_TYPE_BUY,
    "SELL": mt5.ORDER_TYPE_SELL,
    "BUY_LIMIT": mt5.ORDER_TYPE_BUY_LIMIT,
    "SELL_LIMIT": mt5.ORDER_TYPE_SELL_LIMIT,
    "BUY_STOP": mt5.ORDER_TYPE_BUY_STOP,
    "SELL_STOP": mt5.ORDER_TYPE_SELL_STOP
}

# Constants for MT5 timeframes
MT5_TIMEFRAMES = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
    "D1": mt5.TIMEFRAME_D1,
    "W1": mt5.TIMEFRAME_W1,
    "MN1": mt5.TIMEFRAME_MN1
}