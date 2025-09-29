"""
Central Hub - Transfer Manager Implementation
Self-contained implementation that PROVIDES TransferManager for other services
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Union
import logging
import json


class TransferManagerImplementation:
    """
    Self-contained TransferManager implementation for Central Hub
    This becomes the 'shared' component that other services import
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.logger = logging.getLogger("central-hub.transfer-manager")
        self.config = config or {}
        self.service_name = self.config.get("service_name", "central-hub")

        # Transport clients (initialized lazily)
        self._grpc_client = None
        self._http_client = None
        self._nats_client = None
        self._kafka_client = None

        # Metrics tracking
        self.metrics = {
            "total_transfers": 0,
            "successful_transfers": 0,
            "failed_transfers": 0,
            "transfers_by_method": {"grpc": 0, "http": 0, "nats-kafka": 0},
            "avg_latency_ms": 0,
            "total_latency_ms": 0
        }

    async def initialize(self):
        """Initialize transport clients"""
        self.logger.info("Initializing TransferManager for Central Hub")

        # Initialize HTTP client (always available)
        await self._initialize_http_client()

        # Initialize other clients based on configuration
        if self.config.get("enable_grpc", True):
            await self._initialize_grpc_client()

        if self.config.get("enable_nats_kafka", True):
            await self._initialize_nats_kafka_clients()

    async def send(self, data: Any, target_service: str, transport_method: str = "auto",
                  options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Send data to target service using specified transport method
        This is the main method that other services will use
        """
        start_time = time.time()
        options = options or {}

        try:
            self.metrics["total_transfers"] += 1

            # Auto-select transport method if needed
            if transport_method == "auto":
                transport_method = self._auto_select_transport(data, target_service, options)

            # Route to appropriate transport
            result = await self._route_transfer(data, target_service, transport_method, options)

            # Record success metrics
            latency_ms = int((time.time() - start_time) * 1000)
            self._record_success_metrics(transport_method, latency_ms)

            self.logger.debug(f"Transfer successful: {target_service} via {transport_method}")
            return result

        except Exception as error:
            # Record failure metrics
            latency_ms = int((time.time() - start_time) * 1000)
            self._record_failure_metrics(transport_method, latency_ms)

            self.logger.error(f"Transfer failed: {target_service} via {transport_method}: {error}")

            # Try fallback method if configured
            fallback_method = self._get_fallback_method(transport_method)
            if fallback_method and fallback_method != transport_method:
                self.logger.info(f"Trying fallback method: {fallback_method}")
                return await self.send(data, target_service, fallback_method, options)

            raise

    async def _route_transfer(self, data: Any, target_service: str,
                            transport_method: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Route transfer to appropriate transport implementation"""

        if transport_method == "grpc":
            return await self._send_via_grpc(data, target_service, options)
        elif transport_method == "nats-kafka":
            return await self._send_via_nats_kafka(data, target_service, options)
        elif transport_method == "http":
            return await self._send_via_http(data, target_service, options)
        else:
            raise ValueError(f"Unknown transport method: {transport_method}")

    async def _send_via_http(self, data: Any, target_service: str,
                           options: Dict[str, Any]) -> Dict[str, Any]:
        """Send data via HTTP REST"""
        endpoint = options.get("endpoint", "/api/receive")
        method = options.get("method", "POST")
        timeout = options.get("timeout", 10)

        # For Central Hub, we need service discovery to get target URL
        service_url = await self._resolve_service_url(target_service)

        # Simulate HTTP client (in real implementation, use aiohttp or httpx)
        self.logger.info(f"HTTP {method} to {service_url}{endpoint}")

        # Prepare payload
        payload = {
            "data": data,
            "metadata": {
                "source_service": self.service_name,
                "correlation_id": options.get("correlation_id"),
                "timestamp": int(time.time() * 1000)
            }
        }

        # Simulate HTTP call
        await asyncio.sleep(0.01)  # Simulate network latency

        return {
            "status": "success",
            "transport": "http",
            "target": target_service,
            "response_time_ms": 10
        }

    async def _send_via_grpc(self, data: Any, target_service: str,
                           options: Dict[str, Any]) -> Dict[str, Any]:
        """Send data via gRPC"""
        method_name = options.get("method", "ProcessMessage")
        timeout = options.get("timeout", 5)

        # Resolve service endpoint
        service_endpoint = await self._resolve_grpc_endpoint(target_service)

        self.logger.info(f"gRPC call to {service_endpoint}::{method_name}")

        # Prepare gRPC message
        grpc_message = {
            "data": data,
            "metadata": {
                "source_service": self.service_name,
                "correlation_id": options.get("correlation_id"),
                "timestamp": int(time.time() * 1000)
            }
        }

        # Simulate gRPC call
        await asyncio.sleep(0.005)  # Simulate network latency

        return {
            "status": "success",
            "transport": "grpc",
            "target": target_service,
            "response_time_ms": 5
        }

    async def _send_via_nats_kafka(self, data: Any, target_service: str,
                                 options: Dict[str, Any]) -> Dict[str, Any]:
        """Send data via NATS+Kafka hybrid"""
        topic = options.get("topic", f"{target_service}.messages")
        durability = options.get("durability", True)

        self.logger.info(f"NATS+Kafka publish to topic: {topic}")

        # Prepare message
        message = {
            "data": data,
            "metadata": {
                "source_service": self.service_name,
                "target_service": target_service,
                "correlation_id": options.get("correlation_id"),
                "timestamp": int(time.time() * 1000)
            }
        }

        # Send via NATS for real-time
        if self._nats_client:
            await self._publish_to_nats(topic, message)

        # Send via Kafka for durability
        if durability and self._kafka_client:
            await self._publish_to_kafka(topic, message)

        # Simulate publish latency
        await asyncio.sleep(0.002)

        return {
            "status": "success",
            "transport": "nats-kafka",
            "target": target_service,
            "topic": topic,
            "response_time_ms": 2
        }

    def _auto_select_transport(self, data: Any, target_service: str,
                             options: Dict[str, Any]) -> str:
        """Auto-select optimal transport method"""
        data_size = self._estimate_data_size(data)
        is_critical = options.get("critical_path", False)
        volume = options.get("volume", "medium")

        # Central Hub auto-selection logic
        if volume == "high" or data_size > 1024 * 1024:  # > 1MB
            return "nats-kafka"
        elif is_critical and volume == "medium":
            return "grpc"
        else:
            return "http"

    def _get_fallback_method(self, primary_method: str) -> Optional[str]:
        """Get fallback transport method"""
        fallbacks = {
            "grpc": "http",
            "nats-kafka": "grpc",
            "http": None  # HTTP is the final fallback
        }
        return fallbacks.get(primary_method)

    def _estimate_data_size(self, data: Any) -> int:
        """Estimate data size in bytes"""
        if isinstance(data, str):
            return len(data.encode('utf-8'))
        elif isinstance(data, bytes):
            return len(data)
        elif isinstance(data, dict):
            return len(json.dumps(data).encode('utf-8'))
        else:
            return len(str(data).encode('utf-8'))

    async def _resolve_service_url(self, service_name: str) -> str:
        """Resolve service URL via service discovery"""
        # In Central Hub, this would use the ServiceRegistry
        # For now, return a placeholder
        return f"http://{service_name}:8000"

    async def _resolve_grpc_endpoint(self, service_name: str) -> str:
        """Resolve gRPC endpoint via service discovery"""
        return f"{service_name}:50051"

    async def _publish_to_nats(self, topic: str, message: Dict[str, Any]):
        """Publish message to NATS"""
        # Simulate NATS publish
        self.logger.debug(f"NATS publish to {topic}")

    async def _publish_to_kafka(self, topic: str, message: Dict[str, Any]):
        """Publish message to Kafka for durability"""
        # Simulate Kafka publish
        self.logger.debug(f"Kafka publish to {topic}")

    async def _initialize_http_client(self):
        """Initialize HTTP client"""
        self.logger.info("HTTP client initialized")

    async def _initialize_grpc_client(self):
        """Initialize gRPC client"""
        self.logger.info("gRPC client initialized")

    async def _initialize_nats_kafka_clients(self):
        """Initialize NATS and Kafka clients"""
        self.logger.info("NATS+Kafka clients initialized")

    def _record_success_metrics(self, transport_method: str, latency_ms: int):
        """Record successful transfer metrics"""
        self.metrics["successful_transfers"] += 1
        self.metrics["transfers_by_method"][transport_method] += 1
        self.metrics["total_latency_ms"] += latency_ms

        # Update average latency
        total_transfers = self.metrics["total_transfers"]
        self.metrics["avg_latency_ms"] = self.metrics["total_latency_ms"] / total_transfers

    def _record_failure_metrics(self, transport_method: str, latency_ms: int):
        """Record failed transfer metrics"""
        self.metrics["failed_transfers"] += 1
        self.metrics["total_latency_ms"] += latency_ms

        # Update average latency
        total_transfers = self.metrics["total_transfers"]
        self.metrics["avg_latency_ms"] = self.metrics["total_latency_ms"] / total_transfers

    async def health_check(self) -> Dict[str, Any]:
        """Health check for transfer manager"""
        success_rate = (
            self.metrics["successful_transfers"] / self.metrics["total_transfers"]
            if self.metrics["total_transfers"] > 0 else 1.0
        )

        return {
            "status": "operational",
            "total_transfers": self.metrics["total_transfers"],
            "success_rate": success_rate,
            "avg_latency_ms": self.metrics["avg_latency_ms"],
            "transports_available": {
                "http": True,
                "grpc": self._grpc_client is not None,
                "nats_kafka": self._nats_client is not None and self._kafka_client is not None
            }
        }

    async def shutdown(self):
        """Graceful shutdown of transfer manager"""
        self.logger.info("Shutting down TransferManager")

        # Close connections
        if self._grpc_client:
            await self._close_grpc_client()
        if self._nats_client:
            await self._close_nats_client()
        if self._kafka_client:
            await self._close_kafka_client()

    async def _close_grpc_client(self):
        """Close gRPC client connections"""
        self.logger.info("Closing gRPC connections")

    async def _close_nats_client(self):
        """Close NATS client connections"""
        self.logger.info("Closing NATS connections")

    async def _close_kafka_client(self):
        """Close Kafka client connections"""
        self.logger.info("Closing Kafka connections")


# Export class for use by other services
TransferManager = TransferManagerImplementation