"""
NATS Publisher - Publish market data to NATS streaming
"""
import logging
import asyncio
from typing import Dict, Any, Optional
import json
from nats.aio.client import Client as NATS
from nats.js import JetStreamContext

logger = logging.getLogger(__name__)


class NatsPublisher:
    """
    Publisher for NATS streaming
    Handles connection, publishing, and error recovery
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize NATS publisher

        Args:
            config: NATS configuration
        """
        self.config = config
        self.nats_url = config['nats']['url']
        self.client_id = config['nats']['client_id']

        self.nc: Optional[NATS] = None
        self.js: Optional[JetStreamContext] = None
        self.connected = False

        # Subjects
        self.subjects = config['nats']['subjects']

        # Statistics
        self.published_count = 0
        self.error_count = 0

        logger.info(f"NATS publisher initialized: {self.nats_url}")

    async def connect(self) -> bool:
        """
        Connect to NATS server

        Returns:
            bool: True if connection successful
        """
        try:
            self.nc = NATS()

            await self.nc.connect(
                servers=[self.nats_url],
                name=self.client_id,
                max_reconnect_attempts=self.config['nats']['connection'].get('max_reconnect_attempts', -1),
                reconnect_time_wait=self.config['nats']['connection'].get('reconnect_wait', 2)
            )

            # Get JetStream context for enhanced features
            self.js = self.nc.jetstream()

            self.connected = True
            logger.info("Connected to NATS server")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}")
            self.connected = False
            return False

    async def disconnect(self) -> None:
        """Disconnect from NATS server"""
        if self.nc and self.connected:
            await self.nc.drain()
            await self.nc.close()
            self.connected = False
            logger.info("Disconnected from NATS server")

    async def publish(
        self,
        subject: str,
        data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Publish message to NATS

        Args:
            subject: NATS subject
            data: Message data (will be JSON encoded)
            headers: Optional message headers

        Returns:
            bool: True if published successfully
        """
        if not self.connected:
            logger.error("Cannot publish: Not connected to NATS")
            return False

        try:
            # Encode data as JSON
            payload = json.dumps(data).encode('utf-8')

            # Publish message
            await self.nc.publish(subject, payload, headers=headers)

            self.published_count += 1
            logger.debug(f"Published to {subject}: {len(payload)} bytes")
            return True

        except Exception as e:
            self.error_count += 1
            logger.error(f"Error publishing to {subject}: {e}")
            return False

    async def publish_pricing(
        self,
        instrument: str,
        tick_data: Dict[str, Any]
    ) -> bool:
        """
        Publish pricing tick to data bridge

        Args:
            instrument: Instrument symbol
            tick_data: Pricing tick data

        Returns:
            bool: True if published successfully
        """
        # Generate subject
        subject = f"{self.subjects['pricing']}.{instrument}"

        # Add metadata
        message = {
            'subject': subject,
            'message_id': f"{instrument}_{tick_data.get('time', '')}",
            'timestamp': asyncio.get_event_loop().time(),
            'source': {
                'collector': 'oanda-collector',
                'instance_id': self.config['service']['instance_id'],
                'account_id': tick_data.get('account_id'),
                'environment': self.config.get('environment', 'development')
            },
            'data': tick_data,
            'metadata': {
                'collector_timestamp': tick_data.get('collector_timestamp'),
                'latency_ms': None  # Can be calculated if needed
            }
        }

        return await self.publish(subject, message)

    async def publish_candles(
        self,
        instrument: str,
        granularity: str,
        candles_data: Dict[str, Any]
    ) -> bool:
        """
        Publish candles data to data bridge

        Args:
            instrument: Instrument symbol
            granularity: Candle granularity (M1, H1, etc.)
            candles_data: Candles data

        Returns:
            bool: True if published successfully
        """
        # Generate subject
        subject = f"{self.subjects['candles']}.{instrument}.{granularity}"

        # Add metadata
        message = {
            'subject': subject,
            'message_id': f"{instrument}_{granularity}_{asyncio.get_event_loop().time()}",
            'timestamp': asyncio.get_event_loop().time(),
            'source': {
                'collector': 'oanda-collector',
                'instance_id': self.config['service']['instance_id'],
                'account_id': candles_data.get('account_id'),
                'environment': self.config.get('environment', 'development')
            },
            'data': candles_data,
            'metadata': {
                'collector_timestamp': candles_data.get('collector_timestamp'),
                'total_candles': len(candles_data.get('candles', [])),
                'complete_candles': sum(
                    1 for c in candles_data.get('candles', [])
                    if c.get('complete', False)
                )
            }
        }

        return await self.publish(subject, message)

    async def publish_heartbeat(self, health_data: Dict[str, Any]) -> bool:
        """
        Publish service heartbeat to Central Hub

        Args:
            health_data: Service health and status data

        Returns:
            bool: True if published successfully
        """
        # Generate subject
        instance_id = self.config['service']['instance_id']
        subject = f"{self.subjects['heartbeat']}.{instance_id}"

        # Build heartbeat message
        message = {
            'subject': subject,
            'message_id': f"heartbeat_{asyncio.get_event_loop().time()}",
            'timestamp': asyncio.get_event_loop().time(),
            'service': {
                'name': self.config['service']['name'],
                'instance_id': instance_id,
                'version': self.config['service']['version'],
                'uptime_seconds': health_data.get('uptime_seconds', 0)
            },
            'health': health_data.get('health', {}),
            'state': health_data.get('state', {}),
            'resources': health_data.get('resources', {})
        }

        return await self.publish(subject, message)

    async def request(
        self,
        subject: str,
        data: Dict[str, Any],
        timeout: float = 5.0
    ) -> Optional[Dict[str, Any]]:
        """
        Send request and wait for response

        Args:
            subject: NATS subject
            data: Request data
            timeout: Timeout in seconds

        Returns:
            Response data or None
        """
        if not self.connected:
            logger.error("Cannot request: Not connected to NATS")
            return None

        try:
            payload = json.dumps(data).encode('utf-8')

            response = await self.nc.request(
                subject,
                payload,
                timeout=timeout
            )

            return json.loads(response.data.decode('utf-8'))

        except asyncio.TimeoutError:
            logger.error(f"Request timeout for subject {subject}")
            return None

        except Exception as e:
            logger.error(f"Error in request to {subject}: {e}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        """
        Get publisher statistics

        Returns:
            Dict containing statistics
        """
        return {
            'connected': self.connected,
            'nats_url': self.nats_url,
            'client_id': self.client_id,
            'published_count': self.published_count,
            'error_count': self.error_count,
            'subjects': self.subjects
        }

    async def ensure_connected(self) -> bool:
        """
        Ensure connection to NATS, reconnect if needed

        Returns:
            bool: True if connected
        """
        if not self.connected:
            return await self.connect()
        return True
