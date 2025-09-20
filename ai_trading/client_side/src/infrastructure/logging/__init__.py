"""
__init__.py - Logging Module Initializer

🎯 PURPOSE:
Business: Logging infrastructure components initialization
Technical: Logger manager and related component exports
Domain: Logging/Module Initialization

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:28.358Z
Session: client-side-ai-brain-full-compliance
Confidence: 94%
Complexity: low

🧩 PATTERNS USED:
- AI_BRAIN_LOGGING_INIT: Logging module initialization

📦 DEPENDENCIES:
Internal: logger_manager
External: None

💡 AI DECISION REASONING:
Logging module initialization provides unified access to centralized logging.

🚀 USAGE:
from src.infrastructure.logging import LoggerManager

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

from .logger_manager import (
    ClientLoggerManager,
    LoggerConfig,
    client_logger_manager,
    get_logger,
    setup_mt5_logger,
    setup_websocket_logger,
    get_log_stats,
    log_with_context
)

__all__ = [
    'ClientLoggerManager',
    'LoggerConfig',
    'client_logger_manager', 
    'get_logger',
    'setup_mt5_logger',
    'setup_websocket_logger',
    'get_log_stats',
    'log_with_context'
]

__module_type__ = "centralized_infrastructure_client"
__version__ = "1.0.0"