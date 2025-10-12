"""
NATS Subscriber - Primary real-time data path
"""
import asyncio
import logging
import orjson
from typing import Callable
from nats.aio.client import Client as NATS

logger = logging.getLogger(__name__)

class NATSSubscriber:
    """
    NATS subscriber for real-time tick and aggregate data

    Subscription Pattern:
    - ticks.> (all tick data: ticks.EURUSD, ticks.XAUUSD, etc)
    - bars.> (all aggregate bars: bars.EURUSD.1s, etc)
    - confirmation.> (confirmation pairs)

    This is the PRIMARY data path (fast, <1ms latency)
    """

    def __init__(self, config: dict, message_handler: Callable):
        self.config = config
        self.message_handler = message_handler

        self.nc = None
        self.is_running = False

        # Statistics
        self.total_messages = 0
        self.tick_messages = 0
        self.aggregate_messages = 0
        self.confirmation_messages = 0
        self.external_messages = 0

        logger.info("NATS subscriber initialized")

    async def connect(self):
        """Connect to NATS server"""
        try:
            self.nc = NATS()

            await self.nc.connect(
                servers=[self.config.get('url', 'nats://localhost:4222')],
                max_reconnect_attempts=self.config.get('max_reconnect_attempts', -1),
                reconnect_time_wait=self.config.get('reconnect_time_wait', 2),
                ping_interval=self.config.get('ping_interval', 120)
            )

            logger.info(f"✅ Connected to NATS: {self.config.get('url')}")

        except Exception as e:
            logger.error(f"❌ NATS connection failed: {e}")
            raise

    async def subscribe_all(self):
        """
        Subscribe to all market data subjects

        Subject Patterns (from nats.json):
        - market.> (all market data: ticks, candles, all symbols)
        - signals.> (AI signals)
        - indicators.> (technical indicators)
        - system.> (system events)
        """
        # Subscribe to ALL market data (wildcard pattern from nats.json)
        # This includes:
        # - market.EURUSD.tick (ticks)
        # - market.EURUSD.5m (candles)
        # - market.XAUUSD.1h (candles)
        # etc.
        await self.nc.subscribe("market.>", cb=self._handle_market_message)
        logger.info(f"📊 Subscribed to market.> (all ticks + candles)")

        # Subscribe to signals (AI trading signals)
        await self.nc.subscribe("signals.>", cb=self._handle_signal_message)
        logger.info(f"📊 Subscribed to signals.> (AI signals)")

        # Subscribe to external data (economic calendar, sentiment, etc.)
        await self.nc.subscribe("market.external.>", cb=self._handle_external_message)
        logger.info(f"📊 Subscribed to market.external.> (external data)")

        # Subscribe to system events
        await self.nc.subscribe("system.>", cb=self._handle_system_message)
        logger.info(f"📊 Subscribed to system.> (system events)")

        self.is_running = True

    async def _handle_market_message(self, msg):
        """
        Handle market data messages (ticks + candles)

        Subject examples:
        - market.EURUSD.tick → tick data
        - market.EURUSD.5m → 5-minute candle
        - market.XAUUSD.1h → 1-hour candle
        """
        try:
            # Check if paused (backpressure)
            if self.is_paused():
                logger.debug(f"⏸️  Message dropped (backpressure active): {msg.subject}")
                return  # Drop message during backpressure

            # Parse JSON
            data = orjson.loads(msg.data)

            # Add source metadata (preserve existing _source if present)
            if '_source' not in data:
                data['_source'] = 'nats'
            data['_subject'] = msg.subject

            # Determine data type from subject
            # market.{symbol}.tick → tick
            # market.{symbol}.{timeframe} → aggregate
            parts = msg.subject.split('.')
            if len(parts) >= 3:
                data_type_indicator = parts[2]  # 'tick' or timeframe like '5m'

                if data_type_indicator == 'tick':
                    data_type = 'tick'
                    self.tick_messages += 1
                else:
                    data_type = 'aggregate'
                    self.aggregate_messages += 1
            else:
                # Fallback
                data_type = 'tick' if 'tick' in msg.subject else 'aggregate'

            # Send to message handler
            await self.message_handler(data, data_type=data_type)

            # Update statistics
            self.total_messages += 1

            if self.total_messages % 10000 == 0:
                logger.info(f"📈 NATS received {self.total_messages} messages")

        except Exception as e:
            logger.error(f"Error handling NATS market message: {e}")
            logger.debug(f"Subject: {msg.subject}")
            logger.debug(f"Message data: {msg.data[:200]}")

    async def _handle_signal_message(self, msg):
        """Handle AI signal messages (future use)"""
        try:
            # Check if paused (backpressure)
            if self.is_paused():
                return  # Drop message during backpressure

            data = orjson.loads(msg.data)

            if '_source' not in data:
                data['_source'] = 'nats'
            data['_subject'] = msg.subject

            # For now, just log (will be used when AI trading is implemented)
            logger.debug(f"📊 Received signal: {msg.subject}")

        except Exception as e:
            logger.error(f"Error handling signal message: {e}")

    async def _handle_system_message(self, msg):
        """Handle system events (health, logs, etc.)"""
        try:
            # Check if paused (backpressure) - system messages always processed
            # System messages are critical and should not be dropped

            data = orjson.loads(msg.data)

            # System messages are for monitoring, not data processing
            logger.debug(f"🔧 System event: {msg.subject}")

        except Exception as e:
            logger.error(f"Error handling system message: {e}")

    async def _handle_external_message(self, msg):
        """Handle external data message from NATS (economic calendar, sentiment, etc.)"""
        try:
            # Check if paused (backpressure)
            if self.is_paused():
                logger.debug(f"⏸️  External message dropped (backpressure active): {msg.subject}")
                return  # Drop message during backpressure

            # Parse JSON
            data = orjson.loads(msg.data)

            # Add source metadata (preserve existing _source if present)
            if '_source' not in data:
                data['_source'] = 'nats'
            data['_subject'] = msg.subject

            # Extract data type from subject (market.external.economic_calendar → economic_calendar)
            subject_parts = msg.subject.split('.')
            if len(subject_parts) >= 3:
                data_type = subject_parts[2]  # economic_calendar, fred_economic, etc.
            else:
                data_type = 'unknown'

            data['_external_type'] = data_type

            # Send to message handler
            await self.message_handler(data, data_type='external')

            # Update statistics
            self.total_messages += 1
            self.external_messages += 1

            if self.external_messages % 100 == 0:
                logger.info(f"📊 NATS received {self.external_messages} external data messages")

        except Exception as e:
            logger.error(f"Error handling NATS external message: {e}")
            logger.debug(f"Message subject: {msg.subject}")
            logger.debug(f"Message data: {msg.data[:200]}")

    async def pause(self):
        """
        Pause message consumption from NATS (backpressure mechanism)

        Note: NATS doesn't have native pause/resume like Kafka.
        We implement this by setting a flag to drop messages.
        Messages will still be received but will be acknowledged and dropped.
        """
        if not self.is_running:
            logger.warning("Cannot pause - NATS subscriber not running")
            return

        # Set internal flag to pause processing
        if not hasattr(self, '_paused'):
            self._paused = False

        if not self._paused:
            self._paused = True
            logger.info("⏸️  NATS subscriber paused (messages will be acknowledged and dropped)")
        else:
            logger.debug("NATS subscriber already paused")

    async def resume(self):
        """
        Resume message consumption from NATS (backpressure mechanism)

        Resumes normal message processing after a pause.
        """
        if not self.is_running:
            logger.warning("Cannot resume - NATS subscriber not running")
            return

        # Clear internal pause flag
        if not hasattr(self, '_paused'):
            self._paused = False

        if self._paused:
            self._paused = False
            logger.info("▶️  NATS subscriber resumed (normal message processing)")
        else:
            logger.debug("NATS subscriber already running")

    def is_paused(self) -> bool:
        """Check if subscriber is currently paused"""
        return hasattr(self, '_paused') and self._paused

    async def close(self):
        """Close NATS connection"""
        logger.info("Closing NATS connection...")
        self.is_running = False

        if self.nc:
            await self.nc.close()
            logger.info("✅ NATS connection closed")

    def get_stats(self) -> dict:
        """Get subscriber statistics"""
        return {
            'is_running': self.is_running,
            'is_paused': self.is_paused(),
            'total_messages': self.total_messages,
            'tick_messages': self.tick_messages,
            'aggregate_messages': self.aggregate_messages,
            'confirmation_messages': self.confirmation_messages,
            'external_messages': self.external_messages
        }
