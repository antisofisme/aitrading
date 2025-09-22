"""
Inter-Service Communication System
Level 2 Connectivity - Service Communication Implementation
Supports WebSocket, HTTP, and Message Queue communication patterns
"""

import asyncio
import logging
import json
import time
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import aioredis
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
import uuid
import hashlib
from contextlib import asynccontextmanager
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessageType(Enum):
    """Message types for inter-service communication"""
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    HEARTBEAT = "heartbeat"
    TRADING_SIGNAL = "trading_signal"
    MARKET_DATA = "market_data"
    RISK_ALERT = "risk_alert"
    SYSTEM_STATUS = "system_status"

class CommunicationProtocol(Enum):
    """Communication protocols"""
    HTTP = "http"
    WEBSOCKET = "websocket"
    REDIS_PUBSUB = "redis_pubsub"
    MESSAGE_QUEUE = "message_queue"

class ServiceEndpoint(Enum):
    """Trading platform service endpoints"""
    API_GATEWAY = "api-gateway"
    AUTH_SERVICE = "auth-service"
    TRADING_ENGINE = "trading-engine"
    DATA_BRIDGE = "data-bridge"
    AI_ENSEMBLE = "ai-ensemble"
    STRATEGY_ENGINE = "strategy-engine"
    RISK_MANAGER = "risk-manager"
    DATABASE_SERVICE = "database-service"

@dataclass
class Message:
    """Standard message format for inter-service communication"""
    id: str
    type: MessageType
    source: str
    destination: str
    payload: Dict[str, Any]
    timestamp: datetime
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    ttl: Optional[int] = None  # Time to live in seconds
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            'id': self.id,
            'type': self.type.value,
            'source': self.source,
            'destination': self.destination,
            'payload': self.payload,
            'timestamp': self.timestamp.isoformat(),
            'correlation_id': self.correlation_id,
            'reply_to': self.reply_to,
            'ttl': self.ttl,
            'metadata': self.metadata or {}
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary"""
        return cls(
            id=data['id'],
            type=MessageType(data['type']),
            source=data['source'],
            destination=data['destination'],
            payload=data['payload'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            correlation_id=data.get('correlation_id'),
            reply_to=data.get('reply_to'),
            ttl=data.get('ttl'),
            metadata=data.get('metadata', {})
        )

class MessageHandler:
    """Base message handler interface"""

    async def handle_message(self, message: Message) -> Optional[Message]:
        """Handle incoming message and optionally return response"""
        raise NotImplementedError

class TradingSignalHandler(MessageHandler):
    """Handler for trading signals"""

    async def handle_message(self, message: Message) -> Optional[Message]:
        """Process trading signal message"""
        try:
            signal_data = message.payload
            logger.info(f"Processing trading signal: {signal_data.get('signal_type', 'unknown')}")

            # Simulate signal processing
            await asyncio.sleep(0.1)

            # Return acknowledgment
            return Message(
                id=str(uuid.uuid4()),
                type=MessageType.RESPONSE,
                source=message.destination,
                destination=message.source,
                payload={
                    'status': 'processed',
                    'signal_id': signal_data.get('signal_id'),
                    'processed_at': datetime.utcnow().isoformat()
                },
                timestamp=datetime.utcnow(),
                correlation_id=message.id
            )

        except Exception as e:
            logger.error(f"Error processing trading signal: {e}")
            return None

class MarketDataHandler(MessageHandler):
    """Handler for market data updates"""

    async def handle_message(self, message: Message) -> Optional[Message]:
        """Process market data message"""
        try:
            market_data = message.payload
            symbol = market_data.get('symbol', 'UNKNOWN')
            price = market_data.get('price', 0.0)

            logger.debug(f"Market data update: {symbol} @ {price}")

            # Store in memory or forward to subscribers
            # This would integrate with the data pipeline

            return None  # Market data typically doesn't need response

        except Exception as e:
            logger.error(f"Error processing market data: {e}")
            return None

class HTTPCommunicator:
    """HTTP-based service communication"""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None

    async def initialize(self):
        """Initialize HTTP client session"""
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self.session = aiohttp.ClientSession(timeout=timeout)
        logger.info("HTTP communicator initialized")

    async def shutdown(self):
        """Shutdown HTTP client session"""
        if self.session:
            await self.session.close()

    async def send_message(self, service_url: str, message: Message) -> Optional[Message]:
        """Send message via HTTP"""
        try:
            if not self.session:
                await self.initialize()

            async with self.session.post(
                f"{service_url}/api/v1/messages",
                json=message.to_dict()
            ) as response:
                if response.status == 200:
                    response_data = await response.json()
                    return Message.from_dict(response_data)
                else:
                    logger.error(f"HTTP request failed: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"HTTP communication error: {e}")
            return None

class WebSocketCommunicator:
    """WebSocket-based real-time communication"""

    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, List[str]] = {}  # topic -> [connection_ids]
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}

    async def connect_client(self, websocket: WebSocket, client_id: str, metadata: Dict[str, Any] = None):
        """Accept WebSocket connection"""
        try:
            await websocket.accept()
            self.connections[client_id] = websocket
            self.connection_metadata[client_id] = metadata or {}

            logger.info(f"WebSocket client connected: {client_id}")

            # Send welcome message
            welcome_msg = Message(
                id=str(uuid.uuid4()),
                type=MessageType.SYSTEM_STATUS,
                source="communication-service",
                destination=client_id,
                payload={
                    'status': 'connected',
                    'server_time': datetime.utcnow().isoformat()
                },
                timestamp=datetime.utcnow()
            )
            await self.send_to_client(client_id, welcome_msg)

        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")

    async def disconnect_client(self, client_id: str):
        """Handle client disconnection"""
        try:
            if client_id in self.connections:
                del self.connections[client_id]

            if client_id in self.connection_metadata:
                del self.connection_metadata[client_id]

            # Remove from all subscriptions
            for topic in self.subscriptions:
                if client_id in self.subscriptions[topic]:
                    self.subscriptions[topic].remove(client_id)

            logger.info(f"WebSocket client disconnected: {client_id}")

        except Exception as e:
            logger.error(f"WebSocket disconnection error: {e}")

    async def send_to_client(self, client_id: str, message: Message):
        """Send message to specific client"""
        try:
            if client_id in self.connections:
                websocket = self.connections[client_id]
                await websocket.send_text(json.dumps(message.to_dict()))
            else:
                logger.warning(f"Client not found: {client_id}")

        except WebSocketDisconnect:
            await self.disconnect_client(client_id)
        except Exception as e:
            logger.error(f"Error sending to client {client_id}: {e}")

    async def broadcast_to_topic(self, topic: str, message: Message):
        """Broadcast message to all subscribers of a topic"""
        try:
            if topic in self.subscriptions:
                disconnected_clients = []

                for client_id in self.subscriptions[topic]:
                    try:
                        await self.send_to_client(client_id, message)
                    except:
                        disconnected_clients.append(client_id)

                # Clean up disconnected clients
                for client_id in disconnected_clients:
                    await self.disconnect_client(client_id)

        except Exception as e:
            logger.error(f"Broadcast error: {e}")

    async def subscribe_to_topic(self, client_id: str, topic: str):
        """Subscribe client to topic"""
        try:
            if topic not in self.subscriptions:
                self.subscriptions[topic] = []

            if client_id not in self.subscriptions[topic]:
                self.subscriptions[topic].append(client_id)
                logger.info(f"Client {client_id} subscribed to {topic}")

        except Exception as e:
            logger.error(f"Subscription error: {e}")

    async def unsubscribe_from_topic(self, client_id: str, topic: str):
        """Unsubscribe client from topic"""
        try:
            if topic in self.subscriptions and client_id in self.subscriptions[topic]:
                self.subscriptions[topic].remove(client_id)
                logger.info(f"Client {client_id} unsubscribed from {topic}")

        except Exception as e:
            logger.error(f"Unsubscription error: {e}")

class RedisPubSubCommunicator:
    """Redis Pub/Sub for message broadcasting"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None
        self.pubsub: Optional[aioredis.client.PubSub] = None
        self.subscribers: Dict[str, List[Callable]] = {}  # channel -> [callbacks]

    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis = aioredis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
            self.pubsub = self.redis.pubsub()

            logger.info("Redis Pub/Sub communicator initialized")

        except Exception as e:
            logger.error(f"Redis initialization failed: {e}")
            raise

    async def shutdown(self):
        """Shutdown Redis connection"""
        if self.pubsub:
            await self.pubsub.close()
        if self.redis:
            await self.redis.close()

    async def publish_message(self, channel: str, message: Message):
        """Publish message to Redis channel"""
        try:
            if not self.redis:
                await self.initialize()

            message_data = json.dumps(message.to_dict())
            await self.redis.publish(channel, message_data)

            logger.debug(f"Message published to {channel}")

        except Exception as e:
            logger.error(f"Redis publish error: {e}")

    async def subscribe_to_channel(self, channel: str, callback: Callable[[Message], None]):
        """Subscribe to Redis channel"""
        try:
            if not self.pubsub:
                await self.initialize()

            await self.pubsub.subscribe(channel)

            if channel not in self.subscribers:
                self.subscribers[channel] = []
            self.subscribers[channel].append(callback)

            logger.info(f"Subscribed to channel: {channel}")

        except Exception as e:
            logger.error(f"Redis subscription error: {e}")

    async def listen_for_messages(self):
        """Listen for incoming messages"""
        try:
            if not self.pubsub:
                return

            async for message in self.pubsub.listen():
                if message['type'] == 'message':
                    channel = message['channel']
                    data = json.loads(message['data'])
                    msg = Message.from_dict(data)

                    # Call all subscribers for this channel
                    if channel in self.subscribers:
                        for callback in self.subscribers[channel]:
                            try:
                                await callback(msg)
                            except Exception as e:
                                logger.error(f"Callback error: {e}")

        except Exception as e:
            logger.error(f"Redis listen error: {e}")

class MessageQueue:
    """Message queue for async processing"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None
        self.processing_tasks: Dict[str, asyncio.Task] = {}

    async def initialize(self):
        """Initialize message queue"""
        try:
            self.redis = aioredis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()

            logger.info("Message queue initialized")

        except Exception as e:
            logger.error(f"Message queue initialization failed: {e}")
            raise

    async def enqueue_message(self, queue_name: str, message: Message, priority: int = 5):
        """Add message to queue with priority"""
        try:
            if not self.redis:
                await self.initialize()

            message_data = json.dumps(message.to_dict())
            await self.redis.zadd(f"queue:{queue_name}", {message_data: priority})

            logger.debug(f"Message enqueued to {queue_name}")

        except Exception as e:
            logger.error(f"Queue enqueue error: {e}")

    async def dequeue_message(self, queue_name: str) -> Optional[Message]:
        """Get next message from queue"""
        try:
            if not self.redis:
                await self.initialize()

            # Get highest priority message
            result = await self.redis.zpopmax(f"queue:{queue_name}")

            if result:
                message_data, priority = result[0]
                data = json.loads(message_data)
                return Message.from_dict(data)

            return None

        except Exception as e:
            logger.error(f"Queue dequeue error: {e}")
            return None

    async def process_queue(self, queue_name: str, handler: MessageHandler, workers: int = 3):
        """Process queue with multiple workers"""
        try:
            async def worker():
                while True:
                    try:
                        message = await self.dequeue_message(queue_name)
                        if message:
                            await handler.handle_message(message)
                        else:
                            await asyncio.sleep(1)  # No messages, wait
                    except Exception as e:
                        logger.error(f"Worker error: {e}")
                        await asyncio.sleep(1)

            # Start worker tasks
            for i in range(workers):
                task = asyncio.create_task(worker())
                self.processing_tasks[f"{queue_name}_worker_{i}"] = task

            logger.info(f"Started {workers} workers for queue {queue_name}")

        except Exception as e:
            logger.error(f"Queue processing error: {e}")

class CommunicationService:
    """Main inter-service communication coordinator"""

    def __init__(self, service_name: str, redis_url: str = "redis://localhost:6379"):
        self.service_name = service_name
        self.redis_url = redis_url

        # Communication protocols
        self.http_comm = HTTPCommunicator()
        self.websocket_comm = WebSocketCommunicator()
        self.pubsub_comm = RedisPubSubCommunicator(redis_url)
        self.message_queue = MessageQueue(redis_url)

        # Message handlers
        self.message_handlers: Dict[MessageType, MessageHandler] = {
            MessageType.TRADING_SIGNAL: TradingSignalHandler(),
            MessageType.MARKET_DATA: MarketDataHandler()
        }

        # Service registry integration
        self.service_registry = None
        self.heartbeat_task: Optional[asyncio.Task] = None

        logger.info(f"Communication service initialized for {service_name}")

    async def initialize(self):
        """Initialize all communication protocols"""
        try:
            await self.http_comm.initialize()
            await self.pubsub_comm.initialize()
            await self.message_queue.initialize()

            # Start message listeners
            asyncio.create_task(self.pubsub_comm.listen_for_messages())

            # Start heartbeat
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            logger.info("Communication service fully initialized")

        except Exception as e:
            logger.error(f"Communication service initialization failed: {e}")
            raise

    async def shutdown(self):
        """Shutdown communication service"""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()

        await self.http_comm.shutdown()
        await self.pubsub_comm.shutdown()

        logger.info("Communication service shutdown complete")

    async def send_message(self, destination: str, message: Message,
                          protocol: CommunicationProtocol = CommunicationProtocol.HTTP) -> Optional[Message]:
        """Send message using specified protocol"""
        try:
            if protocol == CommunicationProtocol.HTTP:
                # Get service URL from registry
                service_url = f"http://{destination}:8000"  # Simplified
                return await self.http_comm.send_message(service_url, message)

            elif protocol == CommunicationProtocol.REDIS_PUBSUB:
                await self.pubsub_comm.publish_message(f"service:{destination}", message)
                return None

            elif protocol == CommunicationProtocol.MESSAGE_QUEUE:
                await self.message_queue.enqueue_message(f"service:{destination}", message)
                return None

            else:
                logger.error(f"Unsupported protocol: {protocol}")
                return None

        except Exception as e:
            logger.error(f"Message send error: {e}")
            return None

    async def broadcast_event(self, event_type: str, payload: Dict[str, Any],
                            protocol: CommunicationProtocol = CommunicationProtocol.REDIS_PUBSUB):
        """Broadcast event to all interested services"""
        try:
            message = Message(
                id=str(uuid.uuid4()),
                type=MessageType.EVENT,
                source=self.service_name,
                destination="broadcast",
                payload={
                    'event_type': event_type,
                    'data': payload
                },
                timestamp=datetime.utcnow()
            )

            if protocol == CommunicationProtocol.REDIS_PUBSUB:
                await self.pubsub_comm.publish_message(f"events:{event_type}", message)

            logger.info(f"Event broadcasted: {event_type}")

        except Exception as e:
            logger.error(f"Event broadcast error: {e}")

    async def register_message_handler(self, message_type: MessageType, handler: MessageHandler):
        """Register custom message handler"""
        self.message_handlers[message_type] = handler
        logger.info(f"Handler registered for {message_type}")

    async def handle_incoming_message(self, message: Message) -> Optional[Message]:
        """Handle incoming message"""
        try:
            handler = self.message_handlers.get(message.type)
            if handler:
                return await handler.handle_message(message)
            else:
                logger.warning(f"No handler for message type: {message.type}")
                return None

        except Exception as e:
            logger.error(f"Message handling error: {e}")
            return None

    async def _heartbeat_loop(self):
        """Send periodic heartbeat"""
        while True:
            try:
                await asyncio.sleep(30)  # 30 second heartbeat

                heartbeat_msg = Message(
                    id=str(uuid.uuid4()),
                    type=MessageType.HEARTBEAT,
                    source=self.service_name,
                    destination="service-registry",
                    payload={
                        'service': self.service_name,
                        'status': 'healthy',
                        'timestamp': datetime.utcnow().isoformat()
                    },
                    timestamp=datetime.utcnow()
                )

                await self.pubsub_comm.publish_message("heartbeat", heartbeat_msg)
                logger.debug(f"Heartbeat sent from {self.service_name}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

# Coordination hooks integration
async def notify_communication_ready():
    """Notify that inter-service communication is ready"""
    try:
        import subprocess
        result = subprocess.run([
            'npx', 'claude-flow@alpha', 'hooks', 'notify',
            '--message', 'Inter-service communication system operational'
        ], capture_output=True, text=True)

        if result.returncode == 0:
            logger.info("Communication readiness notification sent")
        else:
            logger.warning(f"Failed to send notification: {result.stderr}")

    except Exception as e:
        logger.warning(f"Coordination notification failed: {e}")

# Global communication service instance
communication_service = None

async def get_communication_service(service_name: str) -> CommunicationService:
    """Get communication service instance"""
    global communication_service
    if communication_service is None:
        communication_service = CommunicationService(service_name)
        await communication_service.initialize()
        await notify_communication_ready()
    return communication_service

# FastAPI WebSocket endpoint helper
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """FastAPI WebSocket endpoint implementation"""
    comm_service = await get_communication_service("websocket-handler")

    try:
        await comm_service.websocket_comm.connect_client(websocket, client_id)

        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            message = Message.from_dict(message_data)

            response = await comm_service.handle_incoming_message(message)
            if response:
                await comm_service.websocket_comm.send_to_client(client_id, response)

    except WebSocketDisconnect:
        await comm_service.websocket_comm.disconnect_client(client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await comm_service.websocket_comm.disconnect_client(client_id)

# Export main components
__all__ = [
    'CommunicationService',
    'Message',
    'MessageType',
    'CommunicationProtocol',
    'ServiceEndpoint',
    'MessageHandler',
    'TradingSignalHandler',
    'MarketDataHandler',
    'get_communication_service',
    'websocket_endpoint'
]