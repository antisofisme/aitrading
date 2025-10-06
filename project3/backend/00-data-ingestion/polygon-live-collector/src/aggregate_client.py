"""
Polygon.io Aggregate WebSocket Client
OHLCV bars with tick volume (like MT5)
"""
import asyncio
import json
import logging
from typing import Callable, List, Optional
from datetime import datetime
from polygon import WebSocketClient
from polygon.websocket.models import WebSocketMessage

logger = logging.getLogger(__name__)

class PolygonAggregateClient:
    """
    Collects OHLCV aggregate bars from Polygon.io

    Event Type: CAS (Currency Aggregate Second)
    Provides: Open, High, Low, Close, Volume (tick volume like MT5)
    """

    def __init__(
        self,
        api_key: str,
        subscriptions: List[str],
        message_handler: Callable,
        config: dict
    ):
        self.api_key = api_key
        self.subscriptions = subscriptions
        self.message_handler = message_handler
        self.config = config

        self.client: Optional[WebSocketClient] = None
        self.is_running = False
        self.reconnect_count = 0
        self.aggregate_count = 0

        logger.info(f"Initialized Aggregate client with {len(subscriptions)} subscriptions")

    async def connect(self):
        """Connect to Polygon.io WebSocket for aggregates"""
        try:
            logger.info("Connecting to Polygon.io Aggregate WebSocket...")

            # Create WebSocket client for forex aggregates
            self.client = WebSocketClient(
                api_key=self.api_key,
                subscriptions=self.subscriptions,
                market="forex"  # Forex market
            )

            self.is_running = True
            logger.info(f"✅ Connected to Polygon.io Aggregate WebSocket")
            logger.info(f"📊 Subscribed to {len(self.subscriptions)} pairs for OHLCV data")

            # Run the client with message handler
            await self._run_client()

        except Exception as e:
            logger.error(f"Aggregate WebSocket connection error: {e}")
            await self._handle_reconnect()

    async def _run_client(self):
        """Run WebSocket client with message handling"""
        def handle_messages(msgs: List[WebSocketMessage]):
            """Process incoming aggregate messages"""
            try:
                for msg in msgs:
                    # Parse message
                    aggregate_data = self._parse_message(msg)
                    if aggregate_data:
                        # Send to message handler (NATS publisher)
                        asyncio.create_task(self.message_handler(aggregate_data))
                        self.aggregate_count += 1

                        if self.aggregate_count % 100 == 0:
                            logger.info(f"📊 Processed {self.aggregate_count} aggregate bars")

            except Exception as e:
                logger.error(f"Error handling aggregate message: {e}")

        try:
            # Run WebSocket client in executor (blocking call from polygon client)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,  # Use default ThreadPoolExecutor
                self.client.run,
                handle_messages
            )

        except Exception as e:
            logger.error(f"Aggregate WebSocket run error: {e}")
            if self.is_running:
                await self._handle_reconnect()

    def _parse_message(self, msg: WebSocketMessage) -> Optional[dict]:
        """
        Parse Polygon.io Aggregate WebSocket message

        Message format (CAS - Currency Aggregate Second):
        {
            "ev": "CAS",           // Event type (Currency Aggregate Second)
            "pair": "EUR/USD",     // Currency pair
            "o": 1.0850,           // Open price
            "h": 1.0855,           // High price
            "l": 1.0848,           // Low price
            "c": 1.0852,           // Close price
            "v": 15234,            // Tick volume (like MT5!)
            "s": 1706198400000,    // Start timestamp (Unix MS)
            "e": 1706198401000     // End timestamp (Unix MS)
        }
        """
        try:
            # Convert message to dict
            if hasattr(msg, '__dict__'):
                data = msg.__dict__
            else:
                data = msg

            # Extract fields
            event_type = data.get('ev', data.get('event_type'))

            # Only process aggregate messages (CAS = Currency Aggregate Second)
            if event_type != 'CAS':
                return None

            # Parse pair
            pair = data.get('pair', data.get('p', ''))

            # Format pair if needed (EURUSD → EUR/USD)
            if '/' not in pair and len(pair) == 6:
                pair = f"{pair[:3]}/{pair[3:]}"

            # Extract OHLCV data
            open_price = float(data.get('o', data.get('open', 0)))
            high_price = float(data.get('h', data.get('high', 0)))
            low_price = float(data.get('l', data.get('low', 0)))
            close_price = float(data.get('c', data.get('close', 0)))
            volume = int(data.get('v', data.get('volume', 0)))  # Tick volume (like MT5!)

            # Timestamps
            start_time_ms = int(data.get('s', data.get('start', 0)))
            end_time_ms = int(data.get('e', data.get('end', 0)))

            # Convert to datetime (ISO string format - matching Historical)
            start_time_dt = datetime.fromtimestamp(start_time_ms / 1000.0)
            end_time_dt = datetime.fromtimestamp(end_time_ms / 1000.0)

            start_time = start_time_dt.isoformat()
            end_time = end_time_dt.isoformat()

            # Calculate additional metrics
            range_pips = round((high_price - low_price) * 10000, 2)  # Range in pips
            vwap = data.get('vw', data.get('vwap', 0))  # Volume weighted average price

            # Output format matching TimescaleDB schema + Historical format
            return {
                'symbol': pair,
                'timeframe': '1s',  # 1-second bars
                'timestamp_ms': start_time_ms,  # Unix MS for TimescaleDB
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume,  # Tick volume (same as MT5!)
                'vwap': vwap,
                'range_pips': range_pips,
                'start_time': start_time,  # ISO string
                'end_time': end_time,  # ISO string
                'source': 'polygon_aggregate',
                'event_type': 'ohlcv'
            }

        except Exception as e:
            logger.error(f"Error parsing aggregate message: {e}")
            logger.debug(f"Raw message: {msg}")
            return None

    async def _handle_reconnect(self):
        """Handle WebSocket reconnection"""
        max_attempts = self.config.get('reconnect_attempts', 10)
        delay = self.config.get('reconnect_delay', 5)

        if self.reconnect_count >= max_attempts:
            logger.error(f"❌ Max reconnect attempts ({max_attempts}) reached. Stopping.")
            self.is_running = False
            return

        self.reconnect_count += 1
        logger.warning(f"🔄 Reconnecting... Attempt {self.reconnect_count}/{max_attempts}")

        await asyncio.sleep(delay)

        if self.is_running:
            await self.connect()

    async def close(self):
        """Close WebSocket connection"""
        logger.info("Closing Aggregate WebSocket connection...")
        self.is_running = False

        if self.client:
            try:
                # Polygon client doesn't have explicit close
                pass
            except Exception as e:
                logger.error(f"Error closing Aggregate WebSocket: {e}")

        logger.info("✅ Aggregate WebSocket closed")

    def get_stats(self) -> dict:
        """Get WebSocket statistics"""
        return {
            'is_running': self.is_running,
            'aggregate_count': self.aggregate_count,
            'reconnect_count': self.reconnect_count,
            'subscriptions': len(self.subscriptions)
        }
