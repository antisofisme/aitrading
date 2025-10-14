"""
Central Hub Exception Hierarchy
Provides domain-specific exceptions with error codes
"""

from .base import (
    CentralHubError,
    ErrorCode,
    ErrorSeverity
)

from .service_registry import (
    ServiceRegistrationError,
    ServiceNotFoundError,
    ServiceAlreadyExistsError,
    InvalidServiceConfigError,
    ServiceHealthCheckFailedError
)

from .discovery import (
    ServiceDiscoveryError,
    DiscoveryTimeoutError,
    NoHealthyInstanceError
)

from .configuration import (
    ConfigurationError,
    ConfigNotFoundError,
    ConfigValidationError,
    ConfigReloadError
)

from .coordination import (
    CoordinationError,
    WorkflowExecutionError,
    ServiceCommunicationError,
    DeadlockDetectedError
)

from .infrastructure import (
    InfrastructureError,
    DatabaseConnectionError,
    CacheConnectionError,
    MessagingConnectionError
)

__all__ = [
    # Base
    "CentralHubError",
    "ErrorCode",
    "ErrorSeverity",

    # Service Registry
    "ServiceRegistrationError",
    "ServiceNotFoundError",
    "ServiceAlreadyExistsError",
    "InvalidServiceConfigError",
    "ServiceHealthCheckFailedError",

    # Discovery
    "ServiceDiscoveryError",
    "DiscoveryTimeoutError",
    "NoHealthyInstanceError",

    # Configuration
    "ConfigurationError",
    "ConfigNotFoundError",
    "ConfigValidationError",
    "ConfigReloadError",

    # Coordination
    "CoordinationError",
    "WorkflowExecutionError",
    "ServiceCommunicationError",
    "DeadlockDetectedError",

    # Infrastructure
    "InfrastructureError",
    "DatabaseConnectionError",
    "CacheConnectionError",
    "MessagingConnectionError",
]
