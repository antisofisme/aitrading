"""
Configuration exceptions
"""

from typing import Any, Dict, Optional
from .base import CentralHubError, ErrorCode, ErrorSeverity


class ConfigurationError(CentralHubError):
    """Base exception for configuration errors"""
    code = ErrorCode.CONFIG_VALIDATION_FAILED
    severity = ErrorSeverity.HIGH
    message = "Configuration error"


class ConfigNotFoundError(ConfigurationError):
    """Configuration not found"""
    code = ErrorCode.CONFIG_NOT_FOUND
    severity = ErrorSeverity.MEDIUM
    message = "Configuration not found"

    def __init__(self, config_key: str, **kwargs):
        super().__init__(
            message=f"Configuration key '{config_key}' not found",
            details={"config_key": config_key},
            **kwargs
        )


class ConfigValidationError(ConfigurationError):
    """Configuration validation failed"""
    code = ErrorCode.CONFIG_VALIDATION_FAILED
    severity = ErrorSeverity.HIGH
    message = "Configuration validation failed"

    def __init__(self, validation_errors: Dict[str, Any], **kwargs):
        super().__init__(
            message="Configuration validation failed",
            details={"validation_errors": validation_errors},
            **kwargs
        )


class ConfigReloadError(ConfigurationError):
    """Configuration reload failed"""
    code = ErrorCode.CONFIG_RELOAD_FAILED
    severity = ErrorSeverity.MEDIUM
    message = "Configuration reload failed"

    def __init__(self, config_source: str, reason: str, **kwargs):
        super().__init__(
            message=f"Failed to reload configuration from '{config_source}': {reason}",
            details={
                "config_source": config_source,
                "reason": reason
            },
            **kwargs
        )
