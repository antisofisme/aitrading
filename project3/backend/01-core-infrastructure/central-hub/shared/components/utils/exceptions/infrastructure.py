"""
Infrastructure exceptions
"""

from typing import Optional
from .base import CentralHubError, ErrorCode, ErrorSeverity


class InfrastructureError(CentralHubError):
    """Base exception for infrastructure errors"""
    code = ErrorCode.INTERNAL_ERROR
    severity = ErrorSeverity.CRITICAL
    message = "Infrastructure error"


class DatabaseConnectionError(InfrastructureError):
    """Database connection failed"""
    code = ErrorCode.DATABASE_CONNECTION_ERROR
    severity = ErrorSeverity.CRITICAL
    message = "Database connection error"

    def __init__(self, database_name: str, host: str, port: int, **kwargs):
        super().__init__(
            message=f"Failed to connect to database '{database_name}' at {host}:{port}",
            details={
                "database_name": database_name,
                "host": host,
                "port": port
            },
            severity=ErrorSeverity.CRITICAL,
            **kwargs
        )


class CacheConnectionError(InfrastructureError):
    """Cache connection failed"""
    code = ErrorCode.CACHE_CONNECTION_ERROR
    severity = ErrorSeverity.HIGH
    message = "Cache connection error"

    def __init__(self, cache_backend: str, host: str, port: int, **kwargs):
        super().__init__(
            message=f"Failed to connect to cache '{cache_backend}' at {host}:{port}",
            details={
                "cache_backend": cache_backend,
                "host": host,
                "port": port
            },
            **kwargs
        )


class MessagingConnectionError(InfrastructureError):
    """Messaging system connection failed"""
    code = ErrorCode.MESSAGING_CONNECTION_ERROR
    severity = ErrorSeverity.HIGH
    message = "Messaging connection error"

    def __init__(self, messaging_system: str, connection_url: str, **kwargs):
        super().__init__(
            message=f"Failed to connect to messaging system '{messaging_system}' at {connection_url}",
            details={
                "messaging_system": messaging_system,
                "connection_url": connection_url
            },
            **kwargs
        )
