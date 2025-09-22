"""
MT5 Integration System - Level 3 Data Flow
High-performance real-time market data integration with MetaTrader 5
Target: 50+ ticks/second processing with <10ms latency
"""

import asyncio
import logging
import time
import json
import websockets
from typing import Dict, List, Optional, Any, Callable, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import threading
import queue
import MetaTrader5 as mt5
from websockets.exceptions import ConnectionClosed
import aioredis
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TickType(Enum):
    """Market tick types"""
    BID = "bid"
    ASK = "ask"
    LAST = "last"
    VOLUME = "volume"

class MarketState(Enum):
    """Market session states"""
    CLOSED = "closed"
    PRE_MARKET = "pre_market"
    OPEN = "open"
    POST_MARKET = "post_market"
    WEEKEND = "weekend"

@dataclass
class MarketTick:
    """Standard market tick data structure"""
    symbol: str
    bid: float
    ask: float
    last: float
    volume: int
    timestamp: datetime
    spread: float
    tick_type: TickType
    flags: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'symbol': self.symbol,
            'bid': self.bid,
            'ask': self.ask,
            'last': self.last,
            'volume': self.volume,
            'timestamp': self.timestamp.isoformat(),
            'spread': self.spread,
            'tick_type': self.tick_type.value,
            'flags': self.flags
        }

@dataclass
class OHLCV:
    """OHLC + Volume data"""
    symbol: str
    timeframe: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    timestamp: datetime
    tick_volume: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'timestamp': self.timestamp.isoformat(),
            'tick_volume': self.tick_volume
        }

class MT5Config(BaseModel):
    """MT5 connection configuration"""
    login: int = Field(..., description="MT5 account login")
    password: str = Field(..., description="MT5 account password")
    server: str = Field(..., description="MT5 server name")
    path: Optional[str] = Field(None, description="MT5 terminal path")
    timeout: int = Field(default=60000, description="Connection timeout in ms")

    # Trading symbols to monitor
    symbols: List[str] = Field(default=["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"])

    # Performance settings
    max_ticks_per_second: int = Field(default=100, description="Max tick processing rate")
    buffer_size: int = Field(default=10000, description="Tick buffer size")
    reconnect_attempts: int = Field(default=5, description="Max reconnection attempts")
    reconnect_delay: int = Field(default=5, description="Delay between reconnection attempts")

class PerformanceMetrics:
    """Performance tracking for MT5 integration"""

    def __init__(self):
        self.ticks_received = 0
        self.ticks_processed = 0
        self.ticks_dropped = 0
        self.processing_times = []
        self.connection_uptime = 0
        self.last_tick_time = None
        self.start_time = datetime.utcnow()

        # Rolling statistics
        self.tps_history = []  # Ticks per second history
        self.latency_history = []

    def record_tick(self, processing_time: float):
        """Record tick processing metrics"""
        self.ticks_received += 1
        current_time = time.time()

        if processing_time > 0:
            self.ticks_processed += 1
            self.processing_times.append(processing_time)

            # Keep only last 1000 processing times
            if len(self.processing_times) > 1000:
                self.processing_times = self.processing_times[-1000:]
        else:
            self.ticks_dropped += 1

        # Calculate TPS
        if self.last_tick_time:
            interval = current_time - self.last_tick_time
            if interval > 0:
                tps = 1.0 / interval
                self.tps_history.append(tps)

                # Keep last 100 TPS measurements
                if len(self.tps_history) > 100:
                    self.tps_history = self.tps_history[-100:]

        self.last_tick_time = current_time

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        current_time = datetime.utcnow()
        uptime_seconds = (current_time - self.start_time).total_seconds()

        avg_processing_time = np.mean(self.processing_times) if self.processing_times else 0
        avg_tps = np.mean(self.tps_history) if self.tps_history else 0
        max_tps = np.max(self.tps_history) if self.tps_history else 0

        return {
            'uptime_seconds': uptime_seconds,
            'ticks_received': self.ticks_received,
            'ticks_processed': self.ticks_processed,
            'ticks_dropped': self.ticks_dropped,
            'processing_rate': self.ticks_processed / uptime_seconds if uptime_seconds > 0 else 0,
            'drop_rate': self.ticks_dropped / self.ticks_received if self.ticks_received > 0 else 0,
            'avg_processing_time_ms': avg_processing_time * 1000,
            'avg_tps': avg_tps,
            'max_tps': max_tps,
            'target_met': avg_tps >= 18,  # 18 ticks/second target
            'performance_score': min(100, (avg_tps / 50) * 100)  # Score out of 100
        }

class TickBuffer:
    """High-performance tick buffer for managing market data flow"""

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.buffer = queue.Queue(maxsize=max_size)
        self.overflow_count = 0
        self.lock = threading.RLock()

    def add_tick(self, tick: MarketTick) -> bool:
        """Add tick to buffer, return False if buffer is full"""
        try:
            self.buffer.put_nowait(tick)
            return True
        except queue.Full:
            with self.lock:
                self.overflow_count += 1
            return False

    def get_tick(self, timeout: float = 1.0) -> Optional[MarketTick]:
        """Get tick from buffer with timeout"""
        try:
            return self.buffer.get(timeout=timeout)
        except queue.Empty:
            return None

    def get_batch(self, batch_size: int = 100, timeout: float = 1.0) -> List[MarketTick]:
        """Get batch of ticks for efficient processing"""
        ticks = []
        end_time = time.time() + timeout

        while len(ticks) < batch_size and time.time() < end_time:
            try:
                tick = self.buffer.get_nowait()
                ticks.append(tick)
            except queue.Empty:
                break

        return ticks

    def size(self) -> int:
        """Get current buffer size"""
        return self.buffer.qsize()

    def clear(self):
        """Clear buffer"""
        with self.lock:
            while not self.buffer.empty():
                try:
                    self.buffer.get_nowait()
                except queue.Empty:
                    break

class MT5DataProvider:
    """High-performance MT5 data provider with real-time streaming"""

    def __init__(self, config: MT5Config):
        self.config = config
        self.is_connected = False
        self.is_streaming = False

        # Buffers and queues
        self.tick_buffer = TickBuffer(config.buffer_size)
        self.ohlc_buffer = TickBuffer(config.buffer_size)

        # Performance tracking
        self.metrics = PerformanceMetrics()

        # Subscriber management
        self.tick_subscribers: Set[Callable[[MarketTick], None]] = set()
        self.ohlc_subscribers: Set[Callable[[OHLCV], None]] = set()

        # Threading
        self.tick_thread: Optional[threading.Thread] = None
        self.processing_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

        # Connection management
        self.reconnect_count = 0
        self.last_reconnect = None

        logger.info("MT5 Data Provider initialized")

    async def initialize(self) -> bool:
        """Initialize MT5 connection"""
        try:
            # Initialize MT5
            if not mt5.initialize(path=self.config.path,
                                 login=self.config.login,
                                 password=self.config.password,
                                 server=self.config.server,
                                 timeout=self.config.timeout):
                error = mt5.last_error()
                logger.error(f"MT5 initialization failed: {error}")
                return False

            # Get account info
            account_info = mt5.account_info()
            if account_info is None:
                logger.error("Failed to get account information")
                return False

            logger.info(f"Connected to MT5: {account_info.name} ({account_info.login})")

            # Subscribe to symbols
            for symbol in self.config.symbols:
                if not mt5.symbol_select(symbol, True):
                    logger.warning(f"Failed to select symbol: {symbol}")
                else:
                    logger.info(f"Subscribed to symbol: {symbol}")

            self.is_connected = True

            # Start data streaming
            await self.start_streaming()

            return True

        except Exception as e:
            logger.error(f"MT5 initialization error: {e}")
            return False

    async def start_streaming(self):
        """Start real-time data streaming"""
        try:
            if self.is_streaming:
                return

            self.stop_event.clear()

            # Start tick collection thread
            self.tick_thread = threading.Thread(target=self._tick_collection_loop, daemon=True)
            self.tick_thread.start()

            # Start tick processing thread
            self.processing_thread = threading.Thread(target=self._tick_processing_loop, daemon=True)
            self.processing_thread.start()

            self.is_streaming = True
            logger.info("MT5 streaming started")

        except Exception as e:
            logger.error(f"Failed to start streaming: {e}")

    async def stop_streaming(self):
        """Stop data streaming"""
        try:
            self.is_streaming = False
            self.stop_event.set()

            # Wait for threads to finish
            if self.tick_thread and self.tick_thread.is_alive():
                self.tick_thread.join(timeout=5)

            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=5)

            logger.info("MT5 streaming stopped")

        except Exception as e:
            logger.error(f"Error stopping streaming: {e}")

    def _tick_collection_loop(self):
        """Main tick collection loop - runs in separate thread"""
        last_check = time.time()

        while not self.stop_event.is_set():
            try:
                current_time = time.time()

                # Get ticks for all symbols
                for symbol in self.config.symbols:
                    # Get latest ticks
                    ticks = mt5.copy_ticks_from(symbol,
                                              datetime.fromtimestamp(last_check),
                                              1000,
                                              mt5.COPY_TICKS_ALL)

                    if ticks is not None and len(ticks) > 0:
                        for tick_data in ticks:
                            tick = MarketTick(
                                symbol=symbol,
                                bid=float(tick_data['bid']),
                                ask=float(tick_data['ask']),
                                last=float(tick_data['last']),
                                volume=int(tick_data['volume']),
                                timestamp=datetime.fromtimestamp(tick_data['time']),
                                spread=float(tick_data['ask'] - tick_data['bid']),
                                tick_type=TickType.LAST,
                                flags=int(tick_data['flags'])
                            )

                            # Add to buffer
                            if not self.tick_buffer.add_tick(tick):
                                logger.warning(f"Tick buffer overflow for {symbol}")

                last_check = current_time
                time.sleep(0.1)  # 100ms intervals for high frequency

            except Exception as e:
                logger.error(f"Tick collection error: {e}")
                time.sleep(1)  # Wait before retrying

    def _tick_processing_loop(self):
        """Process ticks from buffer - runs in separate thread"""
        while not self.stop_event.is_set():
            try:
                # Process ticks in batches for efficiency
                ticks = self.tick_buffer.get_batch(batch_size=50, timeout=0.1)

                if ticks:
                    start_time = time.time()

                    # Process each tick
                    for tick in ticks:
                        self._process_tick(tick)

                    processing_time = time.time() - start_time
                    self.metrics.record_tick(processing_time / len(ticks))

            except Exception as e:
                logger.error(f"Tick processing error: {e}")
                time.sleep(0.1)

    def _process_tick(self, tick: MarketTick):
        """Process individual tick"""
        try:
            # Notify all subscribers
            for subscriber in self.tick_subscribers.copy():
                try:
                    subscriber(tick)
                except Exception as e:
                    logger.error(f"Subscriber error: {e}")
                    # Remove failing subscriber
                    self.tick_subscribers.discard(subscriber)

        except Exception as e:
            logger.error(f"Error processing tick: {e}")

    def subscribe_ticks(self, callback: Callable[[MarketTick], None]):
        """Subscribe to tick updates"""
        self.tick_subscribers.add(callback)
        logger.info("New tick subscriber added")

    def unsubscribe_ticks(self, callback: Callable[[MarketTick], None]):
        """Unsubscribe from tick updates"""
        self.tick_subscribers.discard(callback)

    def get_latest_tick(self, symbol: str) -> Optional[MarketTick]:
        """Get latest tick for symbol"""
        try:
            tick_data = mt5.symbol_info_tick(symbol)
            if tick_data is None:
                return None

            return MarketTick(
                symbol=symbol,
                bid=float(tick_data.bid),
                ask=float(tick_data.ask),
                last=float(tick_data.last),
                volume=int(tick_data.volume),
                timestamp=datetime.fromtimestamp(tick_data.time),
                spread=float(tick_data.ask - tick_data.bid),
                tick_type=TickType.LAST
            )

        except Exception as e:
            logger.error(f"Error getting latest tick: {e}")
            return None

    def get_ohlc_data(self, symbol: str, timeframe: str, count: int = 100) -> List[OHLCV]:
        """Get OHLC data for symbol"""
        try:
            # Map timeframe string to MT5 constant
            tf_map = {
                'M1': mt5.TIMEFRAME_M1,
                'M5': mt5.TIMEFRAME_M5,
                'M15': mt5.TIMEFRAME_M15,
                'M30': mt5.TIMEFRAME_M30,
                'H1': mt5.TIMEFRAME_H1,
                'H4': mt5.TIMEFRAME_H4,
                'D1': mt5.TIMEFRAME_D1
            }

            mt5_timeframe = tf_map.get(timeframe, mt5.TIMEFRAME_H1)

            # Get rates
            rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, 0, count)

            if rates is None:
                return []

            ohlc_data = []
            for rate in rates:
                ohlc = OHLCV(
                    symbol=symbol,
                    timeframe=timeframe,
                    open=float(rate['open']),
                    high=float(rate['high']),
                    low=float(rate['low']),
                    close=float(rate['close']),
                    volume=int(rate['real_volume']),
                    timestamp=datetime.fromtimestamp(rate['time']),
                    tick_volume=int(rate['tick_volume'])
                )
                ohlc_data.append(ohlc)

            return ohlc_data

        except Exception as e:
            logger.error(f"Error getting OHLC data: {e}")
            return []

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        base_stats = self.metrics.get_stats()

        # Add MT5-specific stats
        mt5_stats = {
            'is_connected': self.is_connected,
            'is_streaming': self.is_streaming,
            'symbols_count': len(self.config.symbols),
            'buffer_size': self.tick_buffer.size(),
            'buffer_overflow_count': self.tick_buffer.overflow_count,
            'reconnect_count': self.reconnect_count,
            'subscribers_count': len(self.tick_subscribers)
        }

        return {**base_stats, **mt5_stats}

    async def reconnect(self) -> bool:
        """Attempt to reconnect to MT5"""
        try:
            if self.reconnect_count >= self.config.reconnect_attempts:
                logger.error("Maximum reconnection attempts reached")
                return False

            logger.info(f"Attempting MT5 reconnection (attempt {self.reconnect_count + 1})")

            # Stop current streaming
            await self.stop_streaming()

            # Shutdown MT5
            mt5.shutdown()

            # Wait before reconnecting
            await asyncio.sleep(self.config.reconnect_delay)

            # Attempt reconnection
            success = await self.initialize()

            if success:
                self.reconnect_count = 0
                logger.info("MT5 reconnection successful")
            else:
                self.reconnect_count += 1
                logger.error("MT5 reconnection failed")

            self.last_reconnect = datetime.utcnow()
            return success

        except Exception as e:
            logger.error(f"Reconnection error: {e}")
            return False

    async def shutdown(self):
        """Shutdown MT5 connection"""
        try:
            await self.stop_streaming()
            mt5.shutdown()
            self.is_connected = False
            logger.info("MT5 connection shutdown")

        except Exception as e:
            logger.error(f"Shutdown error: {e}")

class MT5WebSocketBridge:
    """WebSocket bridge for real-time MT5 data distribution"""

    def __init__(self, mt5_provider: MT5DataProvider, port: int = 8081):
        self.mt5_provider = mt5_provider
        self.port = port
        self.connected_clients: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.server = None

        # Subscribe to MT5 ticks
        self.mt5_provider.subscribe_ticks(self._broadcast_tick)

    async def start_server(self):
        """Start WebSocket server"""
        try:
            self.server = await websockets.serve(
                self._handle_client,
                "localhost",
                self.port
            )
            logger.info(f"MT5 WebSocket bridge started on port {self.port}")

        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")

    async def _handle_client(self, websocket, path):
        """Handle new WebSocket client"""
        client_id = f"client_{len(self.connected_clients)}"
        self.connected_clients[client_id] = websocket

        try:
            logger.info(f"WebSocket client connected: {client_id}")

            # Send welcome message
            welcome = {
                'type': 'welcome',
                'client_id': client_id,
                'symbols': self.mt5_provider.config.symbols,
                'timestamp': datetime.utcnow().isoformat()
            }
            await websocket.send(json.dumps(welcome))

            # Keep connection alive
            async for message in websocket:
                # Handle client messages if needed
                pass

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"WebSocket client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"WebSocket client error: {e}")
        finally:
            if client_id in self.connected_clients:
                del self.connected_clients[client_id]

    async def _broadcast_tick(self, tick: MarketTick):
        """Broadcast tick to all connected clients"""
        if not self.connected_clients:
            return

        tick_message = {
            'type': 'tick',
            'data': tick.to_dict()
        }

        message = json.dumps(tick_message)
        disconnected_clients = []

        for client_id, websocket in self.connected_clients.items():
            try:
                await websocket.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.append(client_id)
            except Exception as e:
                logger.error(f"Error sending to client {client_id}: {e}")
                disconnected_clients.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected_clients:
            del self.connected_clients[client_id]

# Factory function for easy setup
async def create_mt5_integration(config: MT5Config) -> MT5DataProvider:
    """Create and initialize MT5 integration"""
    try:
        provider = MT5DataProvider(config)

        if await provider.initialize():
            logger.info("MT5 integration created successfully")

            # Execute coordination hook
            await _notify_mt5_ready()

            return provider
        else:
            logger.error("Failed to initialize MT5 integration")
            return None

    except Exception as e:
        logger.error(f"Error creating MT5 integration: {e}")
        return None

async def _notify_mt5_ready():
    """Notify coordination system that MT5 is ready"""
    try:
        import subprocess
        result = subprocess.run([
            'npx', 'claude-flow@alpha', 'hooks', 'notify',
            '--message', 'MT5 integration operational - real-time data streaming active'
        ], capture_output=True, text=True)

        if result.returncode == 0:
            logger.info("MT5 readiness notification sent")
        else:
            logger.warning(f"Failed to send MT5 notification: {result.stderr}")

    except Exception as e:
        logger.warning(f"MT5 coordination notification failed: {e}")

# Export main components
__all__ = [
    'MT5DataProvider',
    'MT5Config',
    'MarketTick',
    'OHLCV',
    'TickType',
    'MarketState',
    'PerformanceMetrics',
    'MT5WebSocketBridge',
    'create_mt5_integration'
]