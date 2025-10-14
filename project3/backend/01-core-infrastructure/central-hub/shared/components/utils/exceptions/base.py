"""
Base exception classes for Central Hub
"""

from enum import Enum
from typing import Any, Dict, Optional


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"           # Recoverable, log and continue
    MEDIUM = "medium"     # Recoverable with retry
    HIGH = "high"         # Service degradation
    CRITICAL = "critical" # Service failure


class ErrorCode:
    """Standard error codes for Central Hub"""

    # Base codes (1000-1999)
    UNKNOWN_ERROR = "CH-1000"
    INTERNAL_ERROR = "CH-1001"
    VALIDATION_ERROR = "CH-1002"
    NOT_FOUND = "CH-1003"
    ALREADY_EXISTS = "CH-1004"
    UNAUTHORIZED = "CH-1005"
    FORBIDDEN = "CH-1006"
    TIMEOUT = "CH-1007"

    # Service Registry codes (2000-2999)
    SERVICE_REGISTRATION_FAILED = "CH-2000"
    SERVICE_NOT_FOUND = "CH-2001"
    SERVICE_ALREADY_EXISTS = "CH-2002"
    INVALID_SERVICE_CONFIG = "CH-2003"
    SERVICE_HEALTH_CHECK_FAILED = "CH-2004"
    SERVICE_DEREGISTRATION_FAILED = "CH-2005"

    # Discovery codes (3000-3999)
    SERVICE_DISCOVERY_FAILED = "CH-3000"
    DISCOVERY_TIMEOUT = "CH-3001"
    NO_HEALTHY_INSTANCE = "CH-3002"
    LOAD_BALANCER_ERROR = "CH-3003"

    # Configuration codes (4000-4999)
    CONFIG_NOT_FOUND = "CH-4000"
    CONFIG_VALIDATION_FAILED = "CH-4001"
    CONFIG_RELOAD_FAILED = "CH-4002"
    CONFIG_PARSE_ERROR = "CH-4003"

    # Coordination codes (5000-5999)
    COORDINATION_FAILED = "CH-5000"
    WORKFLOW_EXECUTION_FAILED = "CH-5001"
    SERVICE_COMMUNICATION_ERROR = "CH-5002"
    DEADLOCK_DETECTED = "CH-5003"
    CIRCULAR_DEPENDENCY = "CH-5004"

    # Infrastructure codes (6000-6999)
    DATABASE_CONNECTION_ERROR = "CH-6000"
    CACHE_CONNECTION_ERROR = "CH-6001"
    MESSAGING_CONNECTION_ERROR = "CH-6002"
    HEALTH_CHECK_FAILED = "CH-6003"


class CentralHubError(Exception):
    """
    Base exception for all Central Hub errors

    All domain exceptions inherit from this class
    Provides structured error information with codes and context
    """

    code: str = ErrorCode.UNKNOWN_ERROR
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    message: str = "An error occurred in Central Hub"

    def __init__(
        self,
        message: Optional[str] = None,
        code: Optional[str] = None,
        severity: Optional[ErrorSeverity] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        """
        Initialize Central Hub error

        Args:
            message: Human-readable error message
            code: Error code for clients
            severity: Error severity level
            details: Additional context/details
            cause: Original exception (if wrapped)
        """
        self.message = message or self.__class__.message
        self.code = code or self.__class__.code
        self.severity = severity or self.__class__.severity
        self.details = details or {}
        self.cause = cause

        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "severity": self.severity.value,
                "details": self.details
            }
        }

    def __str__(self) -> str:
        """String representation"""
        return f"[{self.code}] {self.message}"

    def __repr__(self) -> str:
        """Detailed representation"""
        return f"{self.__class__.__name__}(code={self.code}, message={self.message}, severity={self.severity.value})"
