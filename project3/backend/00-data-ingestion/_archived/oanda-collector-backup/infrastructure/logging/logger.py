"""
Logging Setup - Structured logging configuration
"""
import logging
import sys
from typing import Dict, Any, Optional
from pathlib import Path
import json
from datetime import datetime


class JsonFormatter(logging.Formatter):
    """
    JSON formatter for structured logging
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON

        Args:
            record: Log record

        Returns:
            JSON formatted log string
        """
        log_data = {
            'timestamp': datetime.utcfromtimestamp(record.created).isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, 'extra'):
            log_data['extra'] = record.extra

        return json.dumps(log_data)


def setup_logging(config: Dict[str, Any]) -> None:
    """
    Setup logging configuration

    Args:
        config: Logging configuration from config.yaml
    """
    log_level = config.get('level', 'INFO').upper()
    log_format = config.get('format', 'json')
    outputs = config.get('outputs', [{'type': 'console'}])

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Setup formatters
    if log_format == 'json':
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    # Setup handlers based on outputs
    for output in outputs:
        output_type = output.get('type', 'console')

        if output_type == 'console':
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(formatter)
            root_logger.addHandler(handler)

        elif output_type == 'file':
            log_path = Path(output.get('path', '/var/log/oanda-collector/app.log'))

            # Create log directory if it doesn't exist
            log_path.parent.mkdir(parents=True, exist_ok=True)

            # Setup rotating file handler
            from logging.handlers import RotatingFileHandler

            max_bytes = output.get('max_size', 100) * 1024 * 1024  # Convert MB to bytes
            backup_count = output.get('max_files', 10)

            handler = RotatingFileHandler(
                log_path,
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            handler.setFormatter(formatter)
            root_logger.addHandler(handler)

    # Set third-party loggers to WARNING to reduce noise
    logging.getLogger('v20').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('nats').setLevel(logging.WARNING)

    root_logger.info(f"Logging configured: level={log_level}, format={log_format}")


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
