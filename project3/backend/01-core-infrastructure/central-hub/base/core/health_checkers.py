"""
Health Checkers Factory - Provides different health check implementations
"""

import logging
import httpx
from typing import Dict, Any


class HTTPHealthChecker:
    """HTTP-based health checker"""

    @staticmethod
    async def check(host: str, port: int, endpoint: str = "/health", timeout: int = 5) -> Dict[str, Any]:
        """Check health via HTTP"""
        url = f"http://{host}:{port}{endpoint}"
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    return {"status": "healthy", "code": 200}
                else:
                    return {"status": "unhealthy", "code": response.status_code}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


class TCPHealthChecker:
    """TCP-based health checker"""

    @staticmethod
    async def check(host: str, port: int, timeout: int = 5) -> Dict[str, Any]:
        """Check health via TCP connection"""
        import asyncio
        try:
            # Try to open TCP connection
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=timeout
            )
            writer.close()
            await writer.wait_closed()
            return {"status": "healthy"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


class PingHealthChecker:
    """Ping-based health checker"""

    @staticmethod
    async def check(host: str, **kwargs) -> Dict[str, Any]:
        """Check health via ping"""
        import asyncio
        try:
            # Use system ping command
            process = await asyncio.create_subprocess_exec(
                "ping", "-c", "1", "-W", "2", host,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            if process.returncode == 0:
                return {"status": "healthy"}
            else:
                return {"status": "unhealthy", "error": "ping failed"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


class HealthCheckerFactory:
    """Factory for getting appropriate health checker"""

    _checkers = {
        "http": HTTPHealthChecker,
        "tcp": TCPHealthChecker,
        "ping": PingHealthChecker,
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
