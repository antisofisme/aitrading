"""
HTTP Messaging Client
Implementasi HTTP untuk service coordination dan external API calls
"""

import asyncio
import json
import time
from typing import Any, Dict, Optional, Callable
import aiohttp

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


class HTTPMessagingClient(MessagingClient):
    """
    HTTP messaging client
    Best for: Service coordination, external APIs, webhooks
    """

    def __init__(self, config: MessagingConfig, service_name: str):
        super().__init__(config, service_name)
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = f"http://{config.host}:{config.port}"

    async def connect(self):
        """Create HTTP session"""
        try:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)

            # Setup authentication if provided
            auth = None
            if self.config.username and self.config.password:
                auth = aiohttp.BasicAuth(self.config.username, self.config.password)

            self.session = aiohttp.ClientSession(
                timeout=timeout,
                auth=auth,
                headers={"User-Agent": self.service_name}
            )

            self.connected = True
            self.logger.info(f"HTTP client initialized: {self.base_url}")

        except Exception as e:
            self.logger.error(f"Failed to initialize HTTP client: {str(e)}")
            raise ConnectionError(f"HTTP client initialization failed: {str(e)}")

    async def disconnect(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.connected = False
            self.logger.info("HTTP client closed")

    async def publish(self, subject: str, data: Any, headers: Optional[Dict[str, str]] = None):
        """
        HTTP POST (publish)

        Args:
            subject: URL path (e.g., "/api/events/tick")
            data: Request body
            headers: Request headers
        """
        if not self.session or not self.connected:
            raise PublishError("HTTP client not initialized")

        try:
            url = f"{self.base_url}{subject}"

            # Prepare headers
            request_headers = {"Content-Type": "application/json"}
            if headers:
                request_headers.update(headers)

            # Serialize data
            if isinstance(data, (dict, list)):
                payload = json.dumps(data, default=str)
            elif isinstance(data, str):
                payload = data
            else:
                payload = json.dumps(data, default=str)

            async with self.session.post(url, data=payload, headers=request_headers) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    raise PublishError(f"HTTP {response.status}: {error_text}")

                self.logger.debug(f"Published to {url}: {response.status}")

        except aiohttp.ClientError as e:
            self.logger.error(f"HTTP publish error to {subject}: {str(e)}")
            raise PublishError(f"Failed to publish: {str(e)}")

    async def subscribe(self, subject: str, callback: Callable, queue_group: Optional[str] = None):
        """
        HTTP subscribe (not recommended - use webhooks instead)

        This is a polling-based implementation for compatibility
        Real-world usage should use webhooks
        """
        raise NotImplementedError("HTTP doesn't support native subscriptions, use webhooks or switch to NATS/Kafka")

    async def request(self, subject: str, data: Any, timeout: Optional[int] = None) -> Any:
        """
        HTTP GET/POST request

        Args:
            subject: URL path
            data: Request body (if POST) or query params (if dict)
            timeout: Request timeout

        Returns:
            Response data
        """
        if not self.session or not self.connected:
            raise RequestTimeoutError("HTTP client not initialized")

        try:
            url = f"{self.base_url}{subject}"
            request_timeout = timeout or self.config.timeout

            # Determine method based on data
            if data is None or (isinstance(data, dict) and not data):
                # GET request
                async with self.session.get(url, timeout=request_timeout) as response:
                    response.raise_for_status()

                    content_type = response.headers.get('Content-Type', '')
                    if 'application/json' in content_type:
                        return await response.json()
                    else:
                        return await response.text()

            else:
                # POST request
                payload = json.dumps(data, default=str) if isinstance(data, dict) else data
                headers = {"Content-Type": "application/json"}

                async with self.session.post(url, data=payload, headers=headers, timeout=request_timeout) as response:
                    response.raise_for_status()

                    content_type = response.headers.get('Content-Type', '')
                    if 'application/json' in content_type:
                        return await response.json()
                    else:
                        return await response.text()

        except asyncio.TimeoutError:
            raise RequestTimeoutError(f"HTTP request timeout for {subject}")
        except aiohttp.ClientError as e:
            self.logger.error(f"HTTP request error for {subject}: {str(e)}")
            raise RequestTimeoutError(f"Request failed: {str(e)}")

    async def reply(self, reply_to: str, data: Any):
        """
        HTTP reply (typically handled by web framework)
        This is a helper for webhook responses
        """
        await self.publish(reply_to, data)

    async def health_check(self) -> Dict[str, Any]:
        """HTTP health check"""
        try:
            if not self.session or not self.connected:
                return {
                    "protocol": "http",
                    "status": "unhealthy",
                    "error": "Not initialized"
                }

            # Try to ping the base URL or health endpoint
            start_time = time.time()

            try:
                async with self.session.get(f"{self.base_url}/health", timeout=5) as response:
                    response_time = (time.time() - start_time) * 1000

                    return {
                        "protocol": "http",
                        "status": "healthy" if response.status < 500 else "degraded",
                        "response_time_ms": response_time,
                        "base_url": self.base_url,
                        "http_status": response.status
                    }
            except Exception:
                # If /health doesn't exist, just check if we can connect
                response_time = (time.time() - start_time) * 1000
                return {
                    "protocol": "http",
                    "status": "healthy",
                    "response_time_ms": response_time,
                    "base_url": self.base_url,
                    "note": "No /health endpoint available"
                }

        except Exception as e:
            return {
                "protocol": "http",
                "status": "unhealthy",
                "error": str(e)
            }
