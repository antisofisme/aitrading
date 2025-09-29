"""
Central Hub - Logger Implementation
Self-contained implementation that PROVIDES structured logging for other services
"""

import logging
import json
import time
from typing import Dict, Any, Optional
import sys
from datetime import datetime


class CentralHubLogger:
    """
    Self-contained logger implementation for Central Hub
    This becomes the 'shared' component that other services import
    """

    def __init__(self, service_name: str = "central-hub"):
        self.service_name = service_name
        self.logger = logging.getLogger(service_name)

        # Configure logger if not already configured
        if not self.logger.handlers:
            self._configure_logger()

        # Metrics tracking
        self.log_metrics = {
            "total_logs": 0,
            "logs_by_level": {"debug": 0, "info": 0, "warn": 0, "error": 0},
            "errors_last_hour": 0,
            "last_error_time": None
        }

    def _configure_logger(self):
        """Configure structured JSON logging"""
        # Set log level
        self.logger.setLevel(python_logging.INFO)

        # Create console handler with JSON formatter
        console_handler = python_logging.StreamHandler(sys.stdout)
        console_handler.setLevel(python_logging.INFO)

        # Create custom JSON formatter
        json_formatter = StructuredJSONFormatter()
        console_handler.setFormatter(json_formatter)

        self.logger.addHandler(console_handler)

        # Prevent duplicate logs
        self.logger.propagate = False

    def info(self, message: str, extra: Dict[str, Any] = None):
        """Log info message with structured format"""
        self._log("info", message, extra)

    def warn(self, message: str, extra: Dict[str, Any] = None):
        """Log warning message with structured format"""
        self._log("warn", message, extra)

    def error(self, message: str, extra: Dict[str, Any] = None):
        """Log error message with structured format"""
        self._log("error", message, extra)
        self._update_error_metrics()

    def debug(self, message: str, extra: Dict[str, Any] = None):
        """Log debug message with structured format"""
        self._log("debug", message, extra)

    def _log(self, level: str, message: str, extra: Dict[str, Any] = None):
        """Internal logging method with metrics tracking"""
        extra = extra or {}

        # Add standard metadata
        log_data = {
            "service": self.service_name,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level.upper(),
            "message": message,
            **extra
        }

        # Track metrics
        self.log_metrics["total_logs"] += 1
        self.log_metrics["logs_by_level"][level] += 1

        # Log using appropriate level
        getattr(self.logger, level)(json.dumps(log_data))

    def _update_error_metrics(self):
        """Update error-specific metrics"""
        current_time = time.time()
        self.log_metrics["last_error_time"] = current_time

        # Count errors in last hour (simplified)
        self.log_metrics["errors_last_hour"] += 1

    def create_service_logger(self, service_name: str) -> 'ServiceLogger':
        """Create a logger for another service (factory method)"""
        return ServiceLogger(service_name, parent_logger=self)

    def get_metrics(self) -> Dict[str, Any]:
        """Get logging metrics"""
        return {
            "total_logs": self.log_metrics["total_logs"],
            "logs_by_level": self.log_metrics["logs_by_level"],
            "errors_last_hour": self.log_metrics["errors_last_hour"],
            "last_error_time": self.log_metrics["last_error_time"],
            "error_rate": (
                self.log_metrics["logs_by_level"]["error"] / self.log_metrics["total_logs"]
                if self.log_metrics["total_logs"] > 0 else 0
            )
        }

    async def health_check(self) -> Dict[str, Any]:
        """Health check for logger"""
        metrics = self.get_metrics()

        # Determine health status based on error rate
        error_rate = metrics["error_rate"]
        if error_rate > 0.1:  # > 10% error rate
            status = "degraded"
        elif error_rate > 0.05:  # > 5% error rate
            status = "warning"
        else:
            status = "healthy"

        return {
            "status": status,
            "total_logs": metrics["total_logs"],
            "error_rate": error_rate,
            "logs_by_level": metrics["logs_by_level"]
        }


class ServiceLogger:
    """Logger instance for individual services"""

    def __init__(self, service_name: str, parent_logger: CentralHubLogger = None):
        self.service_name = service_name
        self.parent_logger = parent_logger
        self.logger = logging.getLogger(service_name)

        # Configure if not already configured
        if not self.logger.handlers:
            self._configure_service_logger()

    def _configure_service_logger(self):
        """Configure service-specific logger"""
        self.logger.setLevel(python_logging.INFO)

        # Create console handler with JSON formatter
        console_handler = python_logging.StreamHandler(sys.stdout)
        console_handler.setLevel(python_logging.INFO)

        # Create custom JSON formatter
        json_formatter = StructuredJSONFormatter()
        console_handler.setFormatter(json_formatter)

        self.logger.addHandler(console_handler)
        self.logger.propagate = False

    def info(self, message: str, extra: Dict[str, Any] = None):
        """Log info message"""
        self._log("info", message, extra)

    def warn(self, message: str, extra: Dict[str, Any] = None):
        """Log warning message"""
        self._log("warn", message, extra)

    def error(self, message: str, extra: Dict[str, Any] = None):
        """Log error message"""
        self._log("error", message, extra)

    def debug(self, message: str, extra: Dict[str, Any] = None):
        """Log debug message"""
        self._log("debug", message, extra)

    def _log(self, level: str, message: str, extra: Dict[str, Any] = None):
        """Internal logging method"""
        extra = extra or {}

        # Add service-specific metadata
        log_data = {
            "service": self.service_name,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level.upper(),
            "message": message,
            **extra
        }

        # Update parent logger metrics if available
        if self.parent_logger:
            self.parent_logger.log_metrics["total_logs"] += 1
            self.parent_logger.log_metrics["logs_by_level"][level] += 1

        # Log using appropriate level
        getattr(self.logger, level)(json.dumps(log_data))


class StructuredJSONFormatter(python_logging.Formatter):
    """Custom JSON formatter for structured logging"""

    def format(self, record):
        """Format log record as JSON"""
        try:
            # Parse JSON from message if it's already JSON
            log_data = json.loads(record.getMessage())
            return json.dumps(log_data, separators=(',', ':'))
        except (json.JSONDecodeError, ValueError):
            # Fallback for non-JSON messages
            log_data = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": record.levelname,
                "message": record.getMessage(),
                "logger": record.name
            }

            # Add exception info if present
            if record.exc_info:
                log_data["exception"] = self.formatException(record.exc_info)

            return json.dumps(log_data, separators=(',', ':'))


# Factory function for creating service loggers (used by other services)
def create_service_logger(service_name: str) -> ServiceLogger:
    """Factory function to create service loggers"""
    return ServiceLogger(service_name)


# Export for use by other services
__all__ = ['CentralHubLogger', 'ServiceLogger', 'create_service_logger']