"""
Base Messaging Client Interface
Menyediakan abstract interface untuk semua messaging protocols
"""

import asyncio
import logging
from typing import Any, Dict, Optional, Callable, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class MessageType(Enum):
    """Message type enumeration"""
    PUBLISH = "publish"
    REQUEST = "request"
    REPLY = "reply"
    STREAM = "stream"


@dataclass
class Message:
    """Standard message format"""
    subject: str
    data: Any
    headers: Optional[Dict[str, str]] = None
    reply_to: Optional[str] = None
    message_type: MessageType = MessageType.PUBLISH
    correlation_id: Optional[str] = None


@dataclass
class MessagingConfig:
    """Messaging configuration"""
    protocol: str  # "nats", "kafka", "http"
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    timeout: int = 30
    retry_attempts: int = 3
    max_reconnect_attempts: int = 10


class MessagingClient(ABC):
    """
    Abstract messaging client interface
    Semua messaging protocols harus implement interface ini
    """

    def __init__(self, config: MessagingConfig, service_name: str):
        self.config = config
        self.service_name = service_name
        self.connected = False
        self.logger = logging.getLogger(f"{service_name}.messaging.{config.protocol}")

    @abstractmethod
    async def connect(self):
        """Connect to messaging server"""
        pass

    @abstractmethod
    async def disconnect(self):
        """Disconnect from messaging server"""
        pass

    @abstractmethod
    async def publish(self, subject: str, data: Any, headers: Optional[Dict[str, str]] = None):
        """
        Publish message (fire and forget)

        Args:
            subject: Topic/channel/subject
            data: Message data
            headers: Optional headers
        """
        pass

    @abstractmethod
    async def subscribe(self, subject: str, callback: Callable, queue_group: Optional[str] = None):
        """
        Subscribe to messages

        Args:
            subject: Topic/channel/subject
            callback: Callback function(message)
            queue_group: Optional queue group for load balancing
        """
        pass

    @abstractmethod
    async def request(self, subject: str, data: Any, timeout: Optional[int] = None) -> Any:
        """
        Request-reply pattern

        Args:
            subject: Request subject
            data: Request data
            timeout: Request timeout in seconds

        Returns:
            Response data
        """
        pass

    @abstractmethod
    async def reply(self, reply_to: str, data: Any):
        """
        Reply to request

        Args:
            reply_to: Reply subject
            data: Response data
        """
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Health check for messaging connection"""
        pass

    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self.connected


class MessagingError(Exception):
    """Base messaging error"""
    pass


class ConnectionError(MessagingError):
    """Connection error"""
    pass


class PublishError(MessagingError):
    """Publish error"""
    pass


class SubscriptionError(MessagingError):
    """Subscription error"""
    pass


class RequestTimeoutError(MessagingError):
    """Request timeout error"""
    pass
