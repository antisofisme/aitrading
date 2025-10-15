"""
Health Checkers Factory - Provides different health check implementations
"""

import logging
import httpx
import time
from typing import Dict, Any
import sys
from pathlib import Path

# Add shared to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

from models.infrastructure_model import HealthCheckResult


class HTTPHealthChecker:
    """HTTP-based health checker"""

    @staticmethod
    async def check(host: str, port: int, endpoint: str = "/health", timeout: int = 5) -> HealthCheckResult:
        """Check health via HTTP"""
        url = f"http://{host}:{port}{endpoint}"
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url)
                response_time_ms = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    return HealthCheckResult(
                        healthy=True,
                        response_time_ms=response_time_ms,
                        details={"code": 200}
                    )
                else:
                    return HealthCheckResult(
                        healthy=False,
                        response_time_ms=response_time_ms,
                        error=f"HTTP {response.status_code}",
                        details={"code": response.status_code}
                    )
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                healthy=False,
                response_time_ms=response_time_ms,
                error=str(e)
            )


class TCPHealthChecker:
    """TCP-based health checker"""

    @staticmethod
    async def check(host: str, port: int, timeout: int = 5, **kwargs) -> HealthCheckResult:
        """Check health via TCP connection"""
        import asyncio
        start_time = time.time()
        try:
            # Try to open TCP connection
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=timeout
            )
            writer.close()
            await writer.wait_closed()
            response_time_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                healthy=True,
                response_time_ms=response_time_ms
            )
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                healthy=False,
                response_time_ms=response_time_ms,
                error=str(e)
            )


class PingHealthChecker:
    """Ping-based health checker"""

    @staticmethod
    async def check(host: str, **kwargs) -> HealthCheckResult:
        """Check health via ping"""
        import asyncio
        start_time = time.time()
        try:
            # Use system ping command
            process = await asyncio.create_subprocess_exec(
                "ping", "-c", "1", "-W", "2", host,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            response_time_ms = (time.time() - start_time) * 1000

            if process.returncode == 0:
                return HealthCheckResult(
                    healthy=True,
                    response_time_ms=response_time_ms
                )
            else:
                return HealthCheckResult(
                    healthy=False,
                    response_time_ms=response_time_ms,
                    error="ping failed"
                )
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                healthy=False,
                response_time_ms=response_time_ms,
                error=str(e)
            )


class RedisHealthChecker:
    """Redis PING health checker"""

    @staticmethod
    async def check(host: str, port: int, password: str = None, timeout: int = 5, **kwargs) -> HealthCheckResult:
        """Check health via Redis PING"""
        import asyncio
        import redis.asyncio as redis
        start_time = time.time()
        try:
            # Create Redis client
            redis_url = f"redis://:{password}@{host}:{port}" if password else f"redis://{host}:{port}"
            client = redis.from_url(redis_url)

            # Send PING command
            await asyncio.wait_for(client.ping(), timeout=timeout)
            await client.close()

            response_time_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                healthy=True,
                response_time_ms=response_time_ms
            )
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                healthy=False,
                response_time_ms=response_time_ms,
                error=str(e)
            )


class KafkaHealthChecker:
    """Kafka Admin health checker"""

    @staticmethod
    async def check(host: str, port: int, timeout: int = 5, **kwargs) -> HealthCheckResult:
        """Check health via Kafka Admin API"""
        import asyncio
        start_time = time.time()
        try:
            # Use TCP check as simple health check for Kafka
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=timeout
            )
            writer.close()
            await writer.wait_closed()

            response_time_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                healthy=True,
                response_time_ms=response_time_ms
            )
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                healthy=False,
                response_time_ms=response_time_ms,
                error=str(e)
            )


class HealthCheckerFactory:
    """Factory for getting appropriate health checker"""

    _checkers = {
        "http": HTTPHealthChecker,
        "tcp": TCPHealthChecker,
        "ping": PingHealthChecker,
        "redis_ping": RedisHealthChecker,
        "kafka_admin": KafkaHealthChecker,
    }

    @classmethod
    def get_checker(cls, method: str):
        """Get health checker for specified method"""
        method_lower = method.lower()
        if method_lower in cls._checkers:
            return cls._checkers[method_lower]
        else:
            # Default to HTTP
            logging.warning(f"Unknown health check method: {method}, defaulting to HTTP")
            return cls._checkers["http"]
