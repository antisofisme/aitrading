"""
Messaging Router
Smart routing untuk memilih protocol yang tepat berdasarkan use case
"""

import logging
from typing import Any, Dict, Optional, Callable, Union
from enum import Enum

from .base import MessagingClient, MessagingConfig, Message
from .nats_client import NATSMessagingClient
from .kafka_client import KafkaMessagingClient
from .http_client import HTTPMessagingClient


class UseCase(Enum):
    """Use case enumeration for smart routing"""
    HIGH_FREQUENCY = "high_frequency"      # Tick data, real-time updates → NATS
    USER_COMMAND = "user_command"          # User actions, events → Kafka
    SERVICE_COORD = "service_coord"        # Service coordination → HTTP
    REQUEST_REPLY = "request_reply"        # Request-reply pattern → NATS
    EVENT_SOURCING = "event_sourcing"      # Event logging → Kafka
    EXTERNAL_API = "external_api"          # External APIs → HTTP


class MessagingRouter:
    """
    Smart messaging router
    Otomatis memilih protocol yang tepat berdasarkan use case
    """

    # Default protocol mapping
    DEFAULT_ROUTING = {
        UseCase.HIGH_FREQUENCY: "nats",
        UseCase.USER_COMMAND: "kafka",
        UseCase.SERVICE_COORD: "http",
        UseCase.REQUEST_REPLY: "nats",
        UseCase.EVENT_SOURCING: "kafka",
        UseCase.EXTERNAL_API: "http"
    }

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.clients: Dict[str, MessagingClient] = {}
        self.routing_rules = self.DEFAULT_ROUTING.copy()
        self.logger = logging.getLogger(f"{service_name}.messaging_router")

    async def add_client(self, protocol: str, config: MessagingConfig):
        """
        Add messaging client

        Args:
            protocol: "nats", "kafka", "http"
            config: Messaging configuration
        """
        if protocol.lower() == "nats":
            client = NATSMessagingClient(config, self.service_name)
        elif protocol.lower() == "kafka":
            client = KafkaMessagingClient(config, self.service_name)
        elif protocol.lower() == "http":
            client = HTTPMessagingClient(config, self.service_name)
        else:
            raise ValueError(f"Unsupported protocol: {protocol}")

        await client.connect()
        self.clients[protocol.lower()] = client
        self.logger.info(f"Added {protocol} messaging client")

    def set_routing_rule(self, use_case: UseCase, protocol: str):
        """
        Override routing rule for specific use case

        Args:
            use_case: Use case enum
            protocol: Target protocol
        """
        self.routing_rules[use_case] = protocol.lower()
        self.logger.info(f"Set routing rule: {use_case.value} → {protocol}")

    def get_client(self, use_case: UseCase) -> MessagingClient:
        """
        Get appropriate client for use case

        Args:
            use_case: Use case enum

        Returns:
            MessagingClient instance
        """
        protocol = self.routing_rules.get(use_case)
        if not protocol:
            raise ValueError(f"No routing rule for {use_case}")

        client = self.clients.get(protocol)
        if not client:
            raise ValueError(f"No client configured for protocol: {protocol}")

        return client

    async def publish(self, subject: str, data: Any, use_case: UseCase = UseCase.HIGH_FREQUENCY,
                     headers: Optional[Dict[str, str]] = None):
        """
        Smart publish - routes to appropriate protocol

        Args:
            subject: Topic/channel/path
            data: Message data
            use_case: Use case for routing
            headers: Optional headers
        """
        client = self.get_client(use_case)
        await client.publish(subject, data, headers)
        self.logger.debug(f"Published via {client.config.protocol}: {subject}")

    async def subscribe(self, subject: str, callback: Callable, use_case: UseCase = UseCase.HIGH_FREQUENCY,
                       queue_group: Optional[str] = None):
        """
        Smart subscribe - routes to appropriate protocol

        Args:
            subject: Topic/channel
            callback: Message handler
            use_case: Use case for routing
            queue_group: Optional queue group
        """
        client = self.get_client(use_case)
        await client.subscribe(subject, callback, queue_group)
        self.logger.info(f"Subscribed via {client.config.protocol}: {subject}")

    async def request(self, subject: str, data: Any, use_case: UseCase = UseCase.REQUEST_REPLY,
                     timeout: Optional[int] = None) -> Any:
        """
        Smart request-reply - routes to appropriate protocol

        Args:
            subject: Request topic
            data: Request data
            use_case: Use case for routing
            timeout: Request timeout

        Returns:
            Response data
        """
        client = self.get_client(use_case)
        response = await client.request(subject, data, timeout)
        self.logger.debug(f"Request via {client.config.protocol}: {subject}")
        return response

    async def disconnect_all(self):
        """Disconnect all messaging clients"""
        for protocol, client in self.clients.items():
            try:
                await client.disconnect()
                self.logger.info(f"Disconnected from {protocol}")
            except Exception as e:
                self.logger.error(f"Error disconnecting from {protocol}: {str(e)}")

    async def health_check_all(self) -> Dict[str, Any]:
        """Health check for all messaging clients"""
        health_status = {
            "overall_status": "healthy",
            "protocols": {}
        }

        unhealthy_count = 0
        for protocol, client in self.clients.items():
            try:
                client_health = await client.health_check()
                health_status["protocols"][protocol] = client_health

                if client_health.get("status") != "healthy":
                    unhealthy_count += 1

            except Exception as e:
                health_status["protocols"][protocol] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                unhealthy_count += 1

        # Determine overall status
        if unhealthy_count == 0:
            health_status["overall_status"] = "healthy"
        elif unhealthy_count < len(self.clients):
            health_status["overall_status"] = "degraded"
        else:
            health_status["overall_status"] = "unhealthy"

        health_status["total_protocols"] = len(self.clients)
        health_status["unhealthy_protocols"] = unhealthy_count

        return health_status


# Convenience functions
async def create_default_router(service_name: str,
                               nats_config: Optional[MessagingConfig] = None,
                               kafka_config: Optional[MessagingConfig] = None,
                               http_config: Optional[MessagingConfig] = None) -> MessagingRouter:
    """
    Create router with default configuration

    Args:
        service_name: Service name
        nats_config: NATS configuration (optional)
        kafka_config: Kafka configuration (optional)
        http_config: HTTP configuration (optional)

    Returns:
        Configured MessagingRouter
    """
    router = MessagingRouter(service_name)

    # Add clients if config provided
    if nats_config:
        await router.add_client("nats", nats_config)

    if kafka_config:
        await router.add_client("kafka", kafka_config)

    if http_config:
        await router.add_client("http", http_config)

    return router
