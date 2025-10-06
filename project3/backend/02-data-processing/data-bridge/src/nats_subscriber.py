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
        """Subscribe to all subjects"""
        subjects = self.config.get('subjects', {})

        # Subscribe to tick data
        tick_subject = subjects.get('ticks', 'ticks.>')
        await self.nc.subscribe(tick_subject, cb=self._handle_tick_message)
        logger.info(f"📊 Subscribed to {tick_subject}")

        # Subscribe to aggregate data
        agg_subject = subjects.get('aggregates', 'bars.>')
        await self.nc.subscribe(agg_subject, cb=self._handle_aggregate_message)
        logger.info(f"📊 Subscribed to {agg_subject}")

        # Subscribe to confirmation data
        conf_subject = subjects.get('confirmation', 'confirmation.>')
        await self.nc.subscribe(conf_subject, cb=self._handle_tick_message)
        logger.info(f"📊 Subscribed to {conf_subject}")

        # Subscribe to external data (economic calendar, sentiment, etc.)
        external_subject = subjects.get('external', 'market.external.>')
        await self.nc.subscribe(external_subject, cb=self._handle_external_message)
        logger.info(f"📊 Subscribed to {external_subject}")

        self.is_running = True

    async def _handle_tick_message(self, msg):
        """Handle tick/confirmation message from NATS"""
        try:
            # Parse JSON
            data = orjson.loads(msg.data)

            # Add source metadata
            data['_source'] = 'nats'
            data['_subject'] = msg.subject

            # Send to message handler
            await self.message_handler(data, data_type='tick')

            # Update statistics
            self.total_messages += 1
            if 'confirmation' in msg.subject:
                self.confirmation_messages += 1
            else:
                self.tick_messages += 1

            if self.total_messages % 1000 == 0:
                logger.info(f"📈 NATS received {self.total_messages} messages")

        except Exception as e:
            logger.error(f"Error handling NATS tick message: {e}")
            logger.debug(f"Message data: {msg.data[:200]}")

    async def _handle_aggregate_message(self, msg):
        """Handle aggregate message from NATS"""
        try:
            # Parse JSON
            data = orjson.loads(msg.data)

            # Add source metadata
            data['_source'] = 'nats'
            data['_subject'] = msg.subject

            # Send to message handler
            await self.message_handler(data, data_type='aggregate')

            # Update statistics
            self.total_messages += 1
            self.aggregate_messages += 1

            if self.total_messages % 1000 == 0:
                logger.info(f"📈 NATS received {self.total_messages} messages")

        except Exception as e:
            logger.error(f"Error handling NATS aggregate message: {e}")
            logger.debug(f"Message data: {msg.data[:200]}")

    async def _handle_external_message(self, msg):
        """Handle external data message from NATS (economic calendar, sentiment, etc.)"""
        try:
            # Parse JSON
            data = orjson.loads(msg.data)

            # Add source metadata
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
            'total_messages': self.total_messages,
            'tick_messages': self.tick_messages,
            'aggregate_messages': self.aggregate_messages,
            'confirmation_messages': self.confirmation_messages,
            'external_messages': self.external_messages
        }
