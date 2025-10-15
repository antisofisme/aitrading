"""
Messaging SDK Package
Unified messaging interface untuk NATS, Kafka, dan HTTP
"""

from .base import (
    MessagingClient,
    MessagingConfig,
    Message,
    MessageType,
    MessagingError,
    ConnectionError,
    PublishError,
    SubscriptionError,
    RequestTimeoutError
)

from .nats_client import NATSMessagingClient
from .kafka_client import KafkaMessagingClient
from .http_client import HTTPMessagingClient

from .router import (
    MessagingRouter,
    UseCase,
    create_default_router
)

from .patterns import (
    PubSubPattern,
    RequestReplyPattern,
    StreamPattern,
    FanOutPattern,
    WorkQueuePattern,
    PublishConfig
)

__all__ = [
    # Base classes
    "MessagingClient",
    "MessagingConfig",
    "Message",
    "MessageType",

    # Errors
    "MessagingError",
    "ConnectionError",
    "PublishError",
    "SubscriptionError",
    "RequestTimeoutError",

    # Client implementations
    "NATSMessagingClient",
    "KafkaMessagingClient",
    "HTTPMessagingClient",

    # Router
    "MessagingRouter",
    "UseCase",
    "create_default_router",

    # Patterns
    "PubSubPattern",
    "RequestReplyPattern",
    "StreamPattern",
    "FanOutPattern",
    "WorkQueuePattern",
    "PublishConfig"
]
