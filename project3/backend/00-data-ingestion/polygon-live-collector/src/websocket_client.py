"""
Polygon.io WebSocket Client
Real-time forex quotes streaming
"""
import asyncio
import json
import logging
from typing import Callable, List, Optional
from datetime import datetime
from polygon import WebSocketClient
from polygon.websocket.models import WebSocketMessage

logger = logging.getLogger(__name__)

class PolygonWebSocketClient:
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
        self.message_count = 0

        logger.info(f"Initialized WebSocket client with {len(subscriptions)} subscriptions")

    async def connect(self):
        """Connect to Polygon.io WebSocket"""
        try:
            logger.info("Connecting to Polygon.io WebSocket...")

            # Create WebSocket client with subscriptions
            self.client = WebSocketClient(
                api_key=self.api_key,
                subscriptions=self.subscriptions,
                market="forex"  # Forex market
            )

            self.is_running = True
            logger.info(f"✅ Connected to Polygon.io WebSocket")
            logger.info(f"📊 Subscribed to {len(self.subscriptions)} pairs")

            # Run the client with message handler
            await self._run_client()

        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            await self._handle_reconnect()

    async def _run_client(self):
        """Run WebSocket client with message handling"""
        def handle_messages(msgs: List[WebSocketMessage]):
            """Process incoming messages"""
            try:
                for msg in msgs:
                    # Parse message
                    tick_data = self._parse_message(msg)
                    if tick_data:
                        # Send to message handler (NATS publisher)
                        asyncio.create_task(self.message_handler(tick_data))
                        self.message_count += 1

                        if self.message_count % 1000 == 0:
                            logger.info(f"📈 Processed {self.message_count} messages")

            except Exception as e:
                logger.error(f"Error handling message: {e}")

        try:
            # Run WebSocket client in executor (blocking call from polygon client)
            # This prevents "asyncio.run() cannot be called from running event loop" error
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,  # Use default ThreadPoolExecutor
                self.client.run,
                handle_messages
            )

        except Exception as e:
            logger.error(f"WebSocket run error: {e}")
            if self.is_running:
                await self._handle_reconnect()

    def _parse_message(self, msg: WebSocketMessage) -> Optional[dict]:
        """
        Parse Polygon.io WebSocket message

        Message format (Quote):
        {
            "ev": "C",           # Event type (C = Currency quote)
            "p": "EUR/USD",      # Pair
            "x": 1,              # Exchange ID
            "a": 1.0850,         # Ask price
            "b": 1.0848,         # Bid price
            "t": 1706198400000   # Timestamp (Unix MS)
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

            # Only process quote messages (C = Currency)
            if event_type != 'C':
                return None

            # Parse pair (format: C:EURUSD → EUR/USD)
            pair_raw = data.get('p', data.get('pair', ''))
            if pair_raw.startswith('C:'):
                pair = pair_raw[2:]  # Remove C: prefix
                # Format: EURUSD → EUR/USD
                if len(pair) == 6:
                    pair = f"{pair[:3]}/{pair[3:]}"
            else:
                pair = pair_raw

            # Extract prices
            ask = float(data.get('a', data.get('ask', 0)))
            bid = float(data.get('b', data.get('bid', 0)))

            # Calculate spread
            spread = round((ask - bid) * 10000, 2)  # in pips (4 decimal places)

            # Calculate mid price
            mid = round((ask + bid) / 2, 5)

            # Timestamp
            timestamp_ms = int(data.get('t', data.get('timestamp', 0)))
            timestamp = datetime.fromtimestamp(timestamp_ms / 1000.0).isoformat()

            # Exchange ID
            exchange = data.get('x', data.get('exchange', 0))

            return {
                'symbol': pair,
                'bid': bid,
                'ask': ask,
                'mid': mid,
                'spread': spread,
                'timestamp': timestamp,
                'timestamp_ms': timestamp_ms,
                'exchange': exchange,
                'source': 'polygon_websocket',
                'event_type': 'quote'
            }

        except Exception as e:
            logger.error(f"Error parsing message: {e}")
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
        logger.info("Closing WebSocket connection...")
        self.is_running = False

        if self.client:
            try:
                # Polygon client doesn't have explicit close
                # Just stop the running flag
                pass
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}")

        logger.info("✅ WebSocket closed")

    def get_stats(self) -> dict:
        """Get WebSocket statistics"""
        return {
            'is_running': self.is_running,
            'message_count': self.message_count,
            'reconnect_count': self.reconnect_count,
            'subscriptions': len(self.subscriptions)
        }
