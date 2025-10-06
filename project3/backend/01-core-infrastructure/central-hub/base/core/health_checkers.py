"""
Health Checkers - Infrastructure health check implementations
"""

import asyncio
import time
import logging
from typing import Tuple, Optional
import httpx
import redis.asyncio as redis

logger = logging.getLogger("central-hub.health-checkers")


class HealthCheckResult:
    """Health check result"""
    def __init__(self, healthy: bool, response_time_ms: float, error: Optional[str] = None):
        self.healthy = healthy
        self.response_time_ms = response_time_ms
        self.error = error


class HTTPHealthChecker:
    """HTTP-based health checker"""

    @staticmethod
    async def check(host: str, port: int, endpoint: str = "/health", timeout: int = 5) -> HealthCheckResult:
        """
        Perform HTTP health check

        Args:
            host: Target hostname
            port: Target port
            endpoint: Health check endpoint
            timeout: Request timeout in seconds

        Returns:
            HealthCheckResult with status and response time
        """
        start_time = time.time()
        url = f"http://{host}:{port}{endpoint}"

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url)
                response_time = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    logger.debug(f"✅ HTTP health check passed: {url} ({response_time:.2f}ms)")
                    return HealthCheckResult(True, response_time)
                else:
                    error_msg = f"HTTP {response.status_code}"
                    logger.warning(f"⚠️ HTTP health check failed: {url} - {error_msg}")
                    return HealthCheckResult(False, response_time, error_msg)

        except httpx.TimeoutException:
            response_time = (time.time() - start_time) * 1000
            error_msg = f"Timeout after {timeout}s"
            logger.warning(f"⚠️ HTTP health check timeout: {url}")
            return HealthCheckResult(False, response_time, error_msg)

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            error_msg = str(e)
            logger.warning(f"⚠️ HTTP health check error: {url} - {error_msg}")
            return HealthCheckResult(False, response_time, error_msg)


class RedisHealthChecker:
    """Redis/DragonflyDB health checker"""

    @staticmethod
    async def check(host: str, port: int, password: Optional[str] = None, timeout: int = 5) -> HealthCheckResult:
        """
        Perform Redis PING health check

        Args:
            host: Redis hostname
            port: Redis port
            password: Redis password (optional)
            timeout: Connection timeout in seconds

        Returns:
            HealthCheckResult with status and response time
        """
        start_time = time.time()

        try:
            client = redis.Redis(
                host=host,
                port=port,
                password=password,
                socket_connect_timeout=timeout,
                socket_timeout=timeout,
                decode_responses=True
            )

            # Send PING command
            pong = await client.ping()
            response_time = (time.time() - start_time) * 1000

            await client.close()

            if pong:
                logger.debug(f"✅ Redis health check passed: {host}:{port} ({response_time:.2f}ms)")
                return HealthCheckResult(True, response_time)
            else:
                logger.warning(f"⚠️ Redis health check failed: {host}:{port} - No PONG response")
                return HealthCheckResult(False, response_time, "No PONG response")

        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            error_msg = f"Timeout after {timeout}s"
            logger.warning(f"⚠️ Redis health check timeout: {host}:{port}")
            return HealthCheckResult(False, response_time, error_msg)

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            error_msg = str(e)
            logger.warning(f"⚠️ Redis health check error: {host}:{port} - {error_msg}")
            return HealthCheckResult(False, response_time, error_msg)


class KafkaHealthChecker:
    """Kafka health checker"""

    @staticmethod
    async def check(host: str, port: int, timeout: int = 10) -> HealthCheckResult:
        """
        Perform Kafka health check using admin client

        Args:
            host: Kafka hostname
            port: Kafka port
            timeout: Operation timeout in seconds

        Returns:
            HealthCheckResult with status and response time
        """
        start_time = time.time()

        try:
            from aiokafka.admin import AIOKafkaAdminClient

            admin_client = AIOKafkaAdminClient(
                bootstrap_servers=f"{host}:{port}",
                request_timeout_ms=timeout * 1000
            )

            await admin_client.start()

            # Try to list topics as health check
            topics = await admin_client.list_topics()
            response_time = (time.time() - start_time) * 1000

            await admin_client.close()

            logger.debug(f"✅ Kafka health check passed: {host}:{port} ({len(topics)} topics, {response_time:.2f}ms)")
            return HealthCheckResult(True, response_time)

        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            error_msg = f"Timeout after {timeout}s"
            logger.warning(f"⚠️ Kafka health check timeout: {host}:{port}")
            return HealthCheckResult(False, response_time, error_msg)

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            error_msg = str(e)
            logger.warning(f"⚠️ Kafka health check error: {host}:{port} - {error_msg}")
            return HealthCheckResult(False, response_time, error_msg)


class TCPHealthChecker:
    """TCP-based health checker (for Zookeeper, etc)"""

    @staticmethod
    async def check(host: str, port: int, command: Optional[str] = None, timeout: int = 5) -> HealthCheckResult:
        """
        Perform TCP health check with optional command

        Args:
            host: Target hostname
            port: Target port
            command: Command to send (e.g., "ruok" for Zookeeper)
            timeout: Connection timeout in seconds

        Returns:
            HealthCheckResult with status and response time
        """
        start_time = time.time()

        try:
            # Open connection
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=timeout
            )

            if command:
                # Send command
                writer.write(command.encode())
                await writer.drain()

                # Read response
                response = await asyncio.wait_for(
                    reader.read(100),
                    timeout=timeout
                )
                response_text = response.decode().strip()
            else:
                # Just connection test
                response_text = "connected"

            response_time = (time.time() - start_time) * 1000

            writer.close()
            await writer.wait_closed()

            logger.debug(f"✅ TCP health check passed: {host}:{port} - {response_text} ({response_time:.2f}ms)")
            return HealthCheckResult(True, response_time)

        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            error_msg = f"Timeout after {timeout}s"
            logger.warning(f"⚠️ TCP health check timeout: {host}:{port}")
            return HealthCheckResult(False, response_time, error_msg)

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            error_msg = str(e)
            logger.warning(f"⚠️ TCP health check error: {host}:{port} - {error_msg}")
            return HealthCheckResult(False, response_time, error_msg)


class HealthCheckerFactory:
    """Factory to create appropriate health checker"""

    @staticmethod
    def get_checker(method: str):
        """Get health checker by method name"""
        checkers = {
            "http": HTTPHealthChecker,
            "redis_ping": RedisHealthChecker,
            "kafka_admin": KafkaHealthChecker,
            "tcp": TCPHealthChecker
        }

        checker = checkers.get(method.lower())
        if not checker:
            raise ValueError(f"Unknown health check method: {method}")

        return checker
