"""
Kafka Messaging Client
Implementasi Kafka untuk user commands dan high-throughput messaging
"""

import asyncio
import json
import time
from typing import Any, Dict, Optional, Callable
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.errors import KafkaError

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


class KafkaMessagingClient(MessagingClient):
    """
    Kafka messaging client
    Best for: User commands, event sourcing, high-throughput messaging
    """

    def __init__(self, config: MessagingConfig, service_name: str):
        super().__init__(config, service_name)
        self.producer: Optional[AIOKafkaProducer] = None
        self.consumers: Dict[str, AIOKafkaConsumer] = {}
        self.consumer_tasks: Dict[str, asyncio.Task] = {}

    async def connect(self):
        """Connect to Kafka broker"""
        try:
            # Create producer
            self.producer = AIOKafkaProducer(
                bootstrap_servers=f"{self.config.host}:{self.config.port}",
                client_id=self.service_name,
                compression_type='gzip',
                request_timeout_ms=self.config.timeout * 1000
            )
            await self.producer.start()

            self.connected = True
            self.logger.info(f"Connected to Kafka: {self.config.host}:{self.config.port}")

        except Exception as e:
            self.logger.error(f"Failed to connect to Kafka: {str(e)}")
            raise ConnectionError(f"Kafka connection failed: {str(e)}")

    async def disconnect(self):
        """Disconnect from Kafka broker"""
        # Stop all consumers
        for topic, task in self.consumer_tasks.items():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        for consumer in self.consumers.values():
            await consumer.stop()

        # Stop producer
        if self.producer:
            await self.producer.stop()

        self.connected = False
        self.logger.info("Disconnected from Kafka")

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
        """Publish message to Kafka topic"""
        if not self.producer or not self.connected:
            raise PublishError("Not connected to Kafka")

        try:
            payload = self._serialize(data)

            # Convert headers to list of tuples
            kafka_headers = None
            if headers:
                kafka_headers = [(k, v.encode() if isinstance(v, str) else v) for k, v in headers.items()]

            await self.producer.send_and_wait(
                subject,
                value=payload,
                headers=kafka_headers
            )
            self.logger.debug(f"Published to Kafka topic {subject}: {len(payload)} bytes")

        except Exception as e:
            self.logger.error(f"Publish error to {subject}: {str(e)}")
            raise PublishError(f"Failed to publish: {str(e)}")

    async def subscribe(self, subject: str, callback: Callable, queue_group: Optional[str] = None):
        """Subscribe to Kafka topic"""
        if not self.connected:
            raise SubscriptionError("Not connected to Kafka")

        try:
            # Create consumer
            consumer = AIOKafkaConsumer(
                subject,
                bootstrap_servers=f"{self.config.host}:{self.config.port}",
                group_id=queue_group or f"{self.service_name}_default",
                auto_offset_reset='latest',
                enable_auto_commit=True
            )
            await consumer.start()
            self.consumers[subject] = consumer

            # Create consumer task
            async def consume_messages():
                """Consumer loop"""
                try:
                    async for msg in consumer:
                        try:
                            data = self._deserialize(msg.value)

                            # Convert headers
                            headers = None
                            if msg.headers:
                                headers = {k: v.decode() if isinstance(v, bytes) else v for k, v in msg.headers}

                            message = Message(
                                subject=msg.topic,
                                data=data,
                                headers=headers,
                                message_type=MessageType.PUBLISH
                            )

                            # Call user callback
                            if asyncio.iscoroutinefunction(callback):
                                await callback(message)
                            else:
                                callback(message)

                        except Exception as e:
                            self.logger.error(f"Error handling Kafka message from {subject}: {str(e)}")

                except asyncio.CancelledError:
                    self.logger.info(f"Consumer for {subject} cancelled")
                except Exception as e:
                    self.logger.error(f"Consumer error for {subject}: {str(e)}")

            # Start consumer task
            task = asyncio.create_task(consume_messages())
            self.consumer_tasks[subject] = task

            self.logger.info(f"Subscribed to Kafka topic {subject}" + (f" [group: {queue_group}]" if queue_group else ""))

        except Exception as e:
            self.logger.error(f"Subscription error for {subject}: {str(e)}")
            raise SubscriptionError(f"Failed to subscribe: {str(e)}")

    async def request(self, subject: str, data: Any, timeout: Optional[int] = None) -> Any:
        """
        Request-reply pattern with Kafka (not recommended, use NATS for this)
        This is a simplified implementation
        """
        # Kafka is not designed for request-reply
        # This would require implementing reply topics and correlation IDs
        raise NotImplementedError("Request-reply not recommended with Kafka, use NATS instead")

    async def reply(self, reply_to: str, data: Any):
        """Reply to request (not recommended with Kafka)"""
        raise NotImplementedError("Request-reply not recommended with Kafka, use NATS instead")

    async def health_check(self) -> Dict[str, Any]:
        """Kafka health check"""
        try:
            if not self.producer or not self.connected:
                return {
                    "protocol": "kafka",
                    "status": "unhealthy",
                    "error": "Not connected"
                }

            # Check if producer is ready
            start_time = time.time()
            await self.producer.send_and_wait(
                "_health_check",
                value=b"ping",
                timeout=5
            )
            response_time = (time.time() - start_time) * 1000

            return {
                "protocol": "kafka",
                "status": "healthy",
                "response_time_ms": response_time,
                "broker": f"{self.config.host}:{self.config.port}",
                "active_consumers": len(self.consumers)
            }

        except Exception as e:
            return {
                "protocol": "kafka",
                "status": "unhealthy",
                "error": str(e)
            }

    async def unsubscribe(self, subject: str):
        """Unsubscribe from Kafka topic"""
        if subject in self.consumer_tasks:
            # Cancel consumer task
            self.consumer_tasks[subject].cancel()
            try:
                await self.consumer_tasks[subject]
            except asyncio.CancelledError:
                pass
            del self.consumer_tasks[subject]

        if subject in self.consumers:
            await self.consumers[subject].stop()
            del self.consumers[subject]

        self.logger.info(f"Unsubscribed from Kafka topic {subject}")
