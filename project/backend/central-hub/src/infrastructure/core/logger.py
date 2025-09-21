"""
Logging Infrastructure for Central Hub Service

Phase 1 Implementation: Basic logging without complex retention
Focus: JSON structured logging, file output, and simple configuration
"""

import logging
import logging.handlers
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import structlog


class JSONFormatter(logging.Formatter):
    """JSON formatter for log records"""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)

        return json.dumps(log_entry, ensure_ascii=False)


class CentralHubLogger:
    """
    Central Hub Logger

    Phase 1 Implementation:
    - JSON structured logging
    - File and console output
    - Basic configuration
    - Simple log management
    """

    def __init__(self, name: str, level: str = "INFO", log_file: Optional[str] = None):
        self.name = name
        self.level = level.upper()
        self.log_file = log_file
        self.logger = logging.getLogger(name)
        self._setup_logger()

    def _setup_logger(self) -> None:
        """Setup logger configuration"""
        # Clear existing handlers
        self.logger.handlers.clear()

        # Set level
        self.logger.setLevel(getattr(logging, self.level))

        # Prevent propagation to avoid duplicate logs
        self.logger.propagate = False

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, self.level))
        console_formatter = JSONFormatter()
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # File handler (if specified)
        if self.log_file:
            # Ensure log directory exists
            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            # Create rotating file handler
            file_handler = logging.handlers.RotatingFileHandler(
                self.log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5
            )\n            file_handler.setLevel(getattr(logging, self.level))\n            file_formatter = JSONFormatter()\n            file_handler.setFormatter(file_formatter)\n            self.logger.addHandler(file_handler)\n    \n    def _log_with_extra(self, level: str, message: str, **kwargs) -> None:\n        \"\"\"Log message with extra fields\"\"\"\n        extra_fields = {k: v for k, v in kwargs.items() if k != \"exc_info\"}\n        \n        # Create log record with extra fields\n        getattr(self.logger, level.lower())(\n            message,\n            extra={\"extra_fields\": extra_fields},\n            exc_info=kwargs.get(\"exc_info\", False)\n        )\n    \n    def debug(self, message: str, **kwargs) -> None:\n        \"\"\"Log debug message\"\"\"\n        self._log_with_extra(\"DEBUG\", message, **kwargs)\n    \n    def info(self, message: str, **kwargs) -> None:\n        \"\"\"Log info message\"\"\"\n        self._log_with_extra(\"INFO\", message, **kwargs)\n    \n    def warning(self, message: str, **kwargs) -> None:\n        \"\"\"Log warning message\"\"\"\n        self._log_with_extra(\"WARNING\", message, **kwargs)\n    \n    def error(self, message: str, **kwargs) -> None:\n        \"\"\"Log error message\"\"\"\n        self._log_with_extra(\"ERROR\", message, **kwargs)\n    \n    def critical(self, message: str, **kwargs) -> None:\n        \"\"\"Log critical message\"\"\"\n        self._log_with_extra(\"CRITICAL\", message, **kwargs)\n    \n    def exception(self, message: str, **kwargs) -> None:\n        \"\"\"Log exception with traceback\"\"\"\n        kwargs[\"exc_info\"] = True\n        self._log_with_extra(\"ERROR\", message, **kwargs)\n    \n    def log_service_event(self, event_type: str, service_name: str, details: Dict[str, Any]) -> None:\n        \"\"\"Log service-related event\"\"\"\n        self.info(\n            f\"Service event: {event_type}\",\n            event_type=event_type,\n            service_name=service_name,\n            **details\n        )\n    \n    def log_health_check(self, service_name: str, status: str, details: Dict[str, Any]) -> None:\n        \"\"\"Log health check result\"\"\"\n        log_method = self.info if status == \"healthy\" else self.warning\n        log_method(\n            f\"Health check: {service_name} - {status}\",\n            event_type=\"health_check\",\n            service_name=service_name,\n            health_status=status,\n            **details\n        )\n    \n    def log_config_change(self, key: str, old_value: Any, new_value: Any) -> None:\n        \"\"\"Log configuration change\"\"\"\n        self.info(\n            f\"Configuration changed: {key}\",\n            event_type=\"config_change\",\n            config_key=key,\n            old_value=str(old_value),\n            new_value=str(new_value)\n        )\n    \n    def log_performance_metric(self, metric_name: str, value: float, unit: str = \"ms\") -> None:\n        \"\"\"Log performance metric\"\"\"\n        self.info(\n            f\"Performance metric: {metric_name} = {value}{unit}\",\n            event_type=\"performance_metric\",\n            metric_name=metric_name,\n            value=value,\n            unit=unit\n        )\n    \n    def get_stats(self) -> Dict[str, Any]:\n        \"\"\"Get logger statistics\"\"\"\n        return {\n            \"name\": self.name,\n            \"level\": self.level,\n            \"log_file\": self.log_file,\n            \"handlers_count\": len(self.logger.handlers),\n            \"propagate\": self.logger.propagate\n        }\n\n\ndef setup_logger(name: str, level: str = \"INFO\", log_file: Optional[str] = None) -> CentralHubLogger:\n    \"\"\"\n    Setup and return a configured logger\n    \n    Args:\n        name: Logger name\n        level: Logging level\n        log_file: Optional log file path\n        \n    Returns:\n        Configured CentralHubLogger instance\n    \"\"\"\n    return CentralHubLogger(name=name, level=level, log_file=log_file)\n\n\n# Global logger registry\n_logger_registry: Dict[str, CentralHubLogger] = {}\n\n\ndef get_logger(name: str, level: str = \"INFO\", log_file: Optional[str] = None) -> CentralHubLogger:\n    \"\"\"\n    Get or create a logger instance\n    \n    Args:\n        name: Logger name\n        level: Logging level\n        log_file: Optional log file path\n        \n    Returns:\n        CentralHubLogger instance\n    \"\"\"\n    if name not in _logger_registry:\n        _logger_registry[name] = setup_logger(name, level, log_file)\n    \n    return _logger_registry[name]\n\n\ndef get_all_loggers() -> Dict[str, CentralHubLogger]:\n    \"\"\"Get all registered loggers\"\"\"\n    return _logger_registry.copy()\n\n\ndef clear_loggers() -> None:\n    \"\"\"Clear all registered loggers\"\"\"\n    _logger_registry.clear()\n"