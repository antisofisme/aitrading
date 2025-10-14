"""
Common Messaging Patterns
Menyediakan pattern-pattern messaging yang sering digunakan
"""

import asyncio
import uuid
from typing import Any, Dict, Optional, Callable, List
from dataclasses import dataclass
from datetime import datetime

from .base import MessagingClient, Message


@dataclass
class PublishConfig:
    """Publish configuration"""
    retry_count: int = 3
    retry_delay: float = 0.5
    timeout: Optional[int] = None


class PubSubPattern:
    """
    Publish-Subscribe Pattern
    Best for: Broadcasting messages to multiple subscribers
    """

    def __init__(self, client: MessagingClient):
        self.client = client

    async def publish(self, subject: str, data: Any, config: Optional[PublishConfig] = None):
        """
        Publish with retry logic

        Args:
            subject: Topic to publish to
            data: Message data
            config: Publish configuration
        """
        config = config or PublishConfig()

        for attempt in range(config.retry_count):
            try:
                await self.client.publish(subject, data)
                return

            except Exception as e:
                if attempt == config.retry_count - 1:
                    raise

                await asyncio.sleep(config.retry_delay * (attempt + 1))

    async def subscribe(self, subject: str, callback: Callable, queue_group: Optional[str] = None):
        """
        Subscribe to topic

        Args:
            subject: Topic to subscribe to
            callback: Message handler
            queue_group: Optional queue group for load balancing
        """
        await self.client.subscribe(subject, callback, queue_group)


class RequestReplyPattern:
    """
    Request-Reply Pattern
    Best for: Synchronous communication, RPC-style calls
    """

    def __init__(self, client: MessagingClient):
        self.client = client
        self.pending_requests: Dict[str, asyncio.Future] = {}

    async def request(self, subject: str, data: Any, timeout: int = 30) -> Any:
        """
        Send request and wait for reply

        Args:
            subject: Request topic
            data: Request data
            timeout: Timeout in seconds

        Returns:
            Reply data
        """
        correlation_id = str(uuid.uuid4())
        reply_subject = f"_REPLY.{correlation_id}"

        # Create future for response
        future = asyncio.Future()
        self.pending_requests[correlation_id] = future

        # Subscribe to reply
        async def reply_handler(message: Message):
            """Handle reply message"""
            if correlation_id in self.pending_requests:
                self.pending_requests[correlation_id].set_result(message.data)

        await self.client.subscribe(reply_subject, reply_handler)

        try:
            # Send request
            await self.client.publish(
                subject,
                data,
                headers={"reply_to": reply_subject, "correlation_id": correlation_id}
            )

            # Wait for reply with timeout
            response = await asyncio.wait_for(future, timeout=timeout)
            return response

        finally:
            # Cleanup
            del self.pending_requests[correlation_id]

    async def handle_request(self, subject: str, handler: Callable):
        """
        Handle requests on subject

        Args:
            subject: Request topic
            handler: Request handler function(data) -> response
        """
        async def request_handler(message: Message):
            """Internal request handler"""
            try:
                # Process request
                if asyncio.iscoroutinefunction(handler):
                    response_data = await handler(message.data)
                else:
                    response_data = handler(message.data)

                # Send reply
                if message.headers and "reply_to" in message.headers:
                    reply_to = message.headers["reply_to"]
                    await self.client.publish(reply_to, response_data)

            except Exception as e:
                # Send error response
                if message.headers and "reply_to" in message.headers:
                    reply_to = message.headers["reply_to"]
                    await self.client.publish(reply_to, {"error": str(e)})

        await self.client.subscribe(subject, request_handler)


class StreamPattern:
    """
    Streaming Pattern
    Best for: Real-time data streams, continuous updates
    """

    def __init__(self, client: MessagingClient):
        self.client = client
        self.active_streams: Dict[str, bool] = {}

    async def stream_publish(self, subject: str, data_generator, batch_size: int = 100):
        """
        Stream data from generator

        Args:
            subject: Stream topic
            data_generator: Async generator or iterable
            batch_size: Messages per batch
        """
        stream_id = str(uuid.uuid4())
        self.active_streams[stream_id] = True

        try:
            batch = []

            if hasattr(data_generator, '__aiter__'):
                # Async generator
                async for data in data_generator:
                    if not self.active_streams.get(stream_id):
                        break

                    batch.append(data)

                    if len(batch) >= batch_size:
                        await self.client.publish(subject, {"batch": batch, "stream_id": stream_id})
                        batch = []

            else:
                # Regular iterable
                for data in data_generator:
                    if not self.active_streams.get(stream_id):
                        break

                    batch.append(data)

                    if len(batch) >= batch_size:
                        await self.client.publish(subject, {"batch": batch, "stream_id": stream_id})
                        batch = []

            # Send remaining batch
            if batch:
                await self.client.publish(subject, {"batch": batch, "stream_id": stream_id})

            # Send end marker
            await self.client.publish(subject, {"stream_id": stream_id, "end_of_stream": True})

        finally:
            del self.active_streams[stream_id]

    async def stream_subscribe(self, subject: str, handler: Callable):
        """
        Subscribe to stream

        Args:
            subject: Stream topic
            handler: Handler function(batch_data)
        """
        async def stream_handler(message: Message):
            """Internal stream handler"""
            try:
                data = message.data

                if isinstance(data, dict):
                    # Check for end of stream
                    if data.get("end_of_stream"):
                        # Notify handler of stream end
                        if asyncio.iscoroutinefunction(handler):
                            await handler(None)
                        else:
                            handler(None)
                        return

                    # Process batch
                    batch = data.get("batch", [])
                    if batch:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(batch)
                        else:
                            handler(batch)

            except Exception as e:
                # Log error but don't crash stream
                pass

        await self.client.subscribe(subject, stream_handler)


class FanOutPattern:
    """
    Fan-Out Pattern
    Best for: Broadcasting to multiple services
    """

    def __init__(self, client: MessagingClient):
        self.client = client

    async def fan_out(self, subjects: List[str], data: Any):
        """
        Publish to multiple subjects in parallel

        Args:
            subjects: List of topics
            data: Message data
        """
        tasks = [self.client.publish(subject, data) for subject in subjects]
        await asyncio.gather(*tasks)


class WorkQueuePattern:
    """
    Work Queue Pattern
    Best for: Load balancing work across multiple workers
    """

    def __init__(self, client: MessagingClient):
        self.client = client

    async def add_work(self, queue: str, task_data: Any):
        """
        Add work to queue

        Args:
            queue: Queue name
            task_data: Task data
        """
        await self.client.publish(queue, {
            "task_id": str(uuid.uuid4()),
            "data": task_data,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def process_work(self, queue: str, worker_func: Callable, queue_group: Optional[str] = None):
        """
        Process work from queue

        Args:
            queue: Queue name
            worker_func: Worker function(task_data) -> result
            queue_group: Worker group for load balancing
        """
        async def work_handler(message: Message):
            """Internal work handler"""
            try:
                task = message.data
                task_id = task.get("task_id")
                data = task.get("data")

                # Process task
                if asyncio.iscoroutinefunction(worker_func):
                    result = await worker_func(data)
                else:
                    result = worker_func(data)

                # Optionally publish result
                # await self.client.publish(f"{queue}.results", {
                #     "task_id": task_id,
                #     "result": result
                # })

            except Exception as e:
                # Log error or publish to error queue
                pass

        await self.client.subscribe(queue, work_handler, queue_group=queue_group)
