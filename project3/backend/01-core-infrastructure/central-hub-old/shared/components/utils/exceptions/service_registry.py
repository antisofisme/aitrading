"""
Service Registry exceptions
"""

from typing import Any, Dict, Optional
from .base import CentralHubError, ErrorCode, ErrorSeverity


class ServiceRegistrationError(CentralHubError):
    """Base exception for service registration errors"""
    code = ErrorCode.SERVICE_REGISTRATION_FAILED
    severity = ErrorSeverity.HIGH
    message = "Service registration failed"


class ServiceNotFoundError(CentralHubError):
    """Service not found in registry"""
    code = ErrorCode.SERVICE_NOT_FOUND
    severity = ErrorSeverity.MEDIUM
    message = "Service not found"

    def __init__(self, service_name: str, **kwargs):
        super().__init__(
            message=f"Service '{service_name}' not found in registry",
            details={"service_name": service_name},
            **kwargs
        )


class ServiceAlreadyExistsError(CentralHubError):
    """Service already registered"""
    code = ErrorCode.SERVICE_ALREADY_EXISTS
    severity = ErrorSeverity.LOW
    message = "Service already exists"

    def __init__(self, service_name: str, **kwargs):
        super().__init__(
            message=f"Service '{service_name}' is already registered",
            details={"service_name": service_name},
            **kwargs
        )


class InvalidServiceConfigError(CentralHubError):
    """Invalid service configuration"""
    code = ErrorCode.INVALID_SERVICE_CONFIG
    severity = ErrorSeverity.HIGH
    message = "Invalid service configuration"

    def __init__(self, validation_errors: Dict[str, Any], **kwargs):
        super().__init__(
            message="Service configuration validation failed",
            details={"validation_errors": validation_errors},
            **kwargs
        )


class ServiceHealthCheckFailedError(CentralHubError):
    """Service health check failed"""
    code = ErrorCode.SERVICE_HEALTH_CHECK_FAILED
    severity = ErrorSeverity.MEDIUM
    message = "Service health check failed"

    def __init__(self, service_name: str, health_endpoint: str, **kwargs):
        super().__init__(
            message=f"Health check failed for service '{service_name}' at {health_endpoint}",
            details={
                "service_name": service_name,
                "health_endpoint": health_endpoint
            },
            **kwargs
        )
