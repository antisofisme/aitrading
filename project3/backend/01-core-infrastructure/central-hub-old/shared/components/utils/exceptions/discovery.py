"""
Service Discovery exceptions
"""

from typing import List, Optional
from .base import CentralHubError, ErrorCode, ErrorSeverity


class ServiceDiscoveryError(CentralHubError):
    """Base exception for service discovery errors"""
    code = ErrorCode.SERVICE_DISCOVERY_FAILED
    severity = ErrorSeverity.HIGH
    message = "Service discovery failed"


class DiscoveryTimeoutError(ServiceDiscoveryError):
    """Service discovery timed out"""
    code = ErrorCode.DISCOVERY_TIMEOUT
    severity = ErrorSeverity.MEDIUM
    message = "Service discovery timed out"

    def __init__(self, service_name: str, timeout_seconds: float, **kwargs):
        super().__init__(
            message=f"Discovery timeout for service '{service_name}' after {timeout_seconds}s",
            details={
                "service_name": service_name,
                "timeout_seconds": timeout_seconds
            },
            **kwargs
        )


class NoHealthyInstanceError(ServiceDiscoveryError):
    """No healthy service instances available"""
    code = ErrorCode.NO_HEALTHY_INSTANCE
    severity = ErrorSeverity.HIGH
    message = "No healthy service instances available"

    def __init__(self, service_name: str, total_instances: int = 0, **kwargs):
        super().__init__(
            message=f"No healthy instances found for service '{service_name}' (total: {total_instances})",
            details={
                "service_name": service_name,
                "total_instances": total_instances,
                "healthy_instances": 0
            },
            **kwargs
        )
