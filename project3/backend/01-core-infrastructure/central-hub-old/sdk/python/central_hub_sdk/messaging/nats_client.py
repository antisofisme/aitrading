"""
NATS Messaging Client
Implementasi NATS untuk high-frequency, low-latency messaging
"""

import asyncio
import json
import time
from typing import Any, Dict, Optional, Callable
import nats
from nats.aio.client import Client as NATSClient
from nats.errors import TimeoutError as NATSTimeout

from .base import (
    MessagingClient,
    MessagingConfig,
    Message,
    MessageType,
    ConnectionError,
    PublishError,
    SubscriptionError,
    RequestTimeoutError
)


class NATSMessagingClient(MessagingClient):
    """
    NATS messaging client
    Best for: High-frequency data, low-latency messaging, tick streaming
    """

    def __init__(self, config: MessagingConfig, service_name: str):
        super().__init__(config, service_name)
        self.nc: Optional[NATSClient] = None
        self.subscriptions = {}

    async def connect(self):
        """Connect to NATS server"""
        try:
            self.nc = await nats.connect(
                servers=[f"nats://{self.config.host}:{self.config.port}"],
                name=self.service_name,
                max_reconnect_attempts=self.config.max_reconnect_attempts,
                reconnect_time_wait=2,
                user=self.config.username,
                password=self.config.password
            )
            self.connected = True
            self.logger.info(f"Connected to NATS: {self.config.host}:{self.config.port}")

        except Exception as e:
            self.logger.error(f"Failed to connect to NATS: {str(e)}")
            raise ConnectionError(f"NATS connection failed: {str(e)}")

    async def disconnect(self):
        """Disconnect from NATS server"""
        if self.nc:
            await self.nc.close()
            self.connected = False
            self.logger.info("Disconnected from NATS")

    def _serialize(self, data: Any) -> bytes:
        """Serialize data to bytes"""
        if isinstance(data, bytes):
            return data
        elif isinstance(data, str):
            return data.encode()
        else:
            return json.dumps(data, default=str).encode()

    def _deserialize(self, data: bytes) -> Any:
        """Deserialize bytes to data"""
        try:
            return json.loads(data.decode())
        except json.JSONDecodeError:
            return data.decode()
        except Exception:
            return data

    async def publish(self, subject: str, data: Any, headers: Optional[Dict[str, str]] = None):
        """Publish message to NATS"""
        if not self.nc or not self.connected:
            raise PublishError("Not connected to NATS")

        try:
            payload = self._serialize(data)
            await self.nc.publish(subject, payload, headers=headers)
            self.logger.debug(f"Published to {subject}: {len(payload)} bytes")

        except Exception as e:
            self.logger.error(f"Publish error to {subject}: {str(e)}")
            raise PublishError(f"Failed to publish: {str(e)}")

    async def subscribe(self, subject: str, callback: Callable, queue_group: Optional[str] = None):
        """Subscribe to NATS subject"""
        if not self.nc or not self.connected:
            raise SubscriptionError("Not connected to NATS")

        try:
            async def message_handler(msg):
                """Internal message handler"""
                try:
                    data = self._deserialize(msg.data)
                    message = Message(
                        subject=msg.subject,
                        data=data,
                        headers=msg.headers if hasattr(msg, 'headers') else None,
                        reply_to=msg.reply if hasattr(msg, 'reply') else None,
                        message_type=MessageType.PUBLISH
                    )

                    # Call user callback
                    if asyncio.iscoroutinefunction(callback):
                        await callback(message)
                    else:
                        callback(message)

                except Exception as e:
                    self.logger.error(f"Error handling message from {subject}: {str(e)}")

            # Subscribe with optional queue group
            sub = await self.nc.subscribe(subject, queue=queue_group, cb=message_handler)
            self.subscriptions[subject] = sub

            self.logger.info(f"Subscribed to {subject}" + (f" [queue: {queue_group}]" if queue_group else ""))

        except Exception as e:
            self.logger.error(f"Subscription error for {subject}: {str(e)}")
            raise SubscriptionError(f"Failed to subscribe: {str(e)}")

    async def request(self, subject: str, data: Any, timeout: Optional[int] = None) -> Any:
        """Request-reply pattern with NATS"""
        if not self.nc or not self.connected:
            raise RequestTimeoutError("Not connected to NATS")

        try:
            payload = self._serialize(data)
            timeout = timeout or self.config.timeout

            response = await self.nc.request(subject, payload, timeout=timeout)
            return self._deserialize(response.data)

        except NATSTimeout:
            raise RequestTimeoutError(f"Request timeout for {subject}")
        except Exception as e:
            self.logger.error(f"Request error for {subject}: {str(e)}")
            raise RequestTimeoutError(f"Request failed: {str(e)}")

    async def reply(self, reply_to: str, data: Any):
        """Reply to request"""
        if not self.nc or not self.connected:
            raise PublishError("Not connected to NATS")

        try:
            payload = self._serialize(data)
            await self.nc.publish(reply_to, payload)
            self.logger.debug(f"Replied to {reply_to}")

        except Exception as e:
            self.logger.error(f"Reply error to {reply_to}: {str(e)}")
            raise PublishError(f"Failed to reply: {str(e)}")

    async def health_check(self) -> Dict[str, Any]:
        """NATS health check"""
        try:
            if not self.nc or not self.connected:
                return {
                    "protocol": "nats",
                    "status": "unhealthy",
                    "error": "Not connected"
                }

            start_time = time.time()
            await self.nc.flush()
            response_time = (time.time() - start_time) * 1000

            return {
                "protocol": "nats",
                "status": "healthy",
                "response_time_ms": response_time,
                "server": f"{self.config.host}:{self.config.port}",
                "subscriptions": len(self.subscriptions)
            }

        except Exception as e:
            return {
                "protocol": "nats",
                "status": "unhealthy",
                "error": str(e)
            }

    async def unsubscribe(self, subject: str):
        """Unsubscribe from subject"""
        if subject in self.subscriptions:
            await self.subscriptions[subject].unsubscribe()
            del self.subscriptions[subject]
            self.logger.info(f"Unsubscribed from {subject}")
