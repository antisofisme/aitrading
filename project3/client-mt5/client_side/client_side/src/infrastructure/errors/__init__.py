"""
__init__.py - Error Management Module Initializer

🎯 PURPOSE:
Business: Error handling components initialization
Technical: Error manager and related component exports
Domain: Error Handling/Module Initialization

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:28.405Z
Session: client-side-ai-brain-full-compliance
Confidence: 91%
Complexity: low

🧩 PATTERNS USED:
- AI_BRAIN_ERROR_INIT: Error handling module initialization

📦 DEPENDENCIES:
Internal: error_manager
External: None

💡 AI DECISION REASONING:
Error module initialization provides unified access to centralized error management.

🚀 USAGE:
from src.infrastructure.errors import ErrorManager

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

from .error_manager import (
    ClientErrorHandler,
    ErrorContext,
    ErrorSeverity,
    ErrorCategory,
    client_error_handler,
    handle_error,
    handle_mt5_error,
    handle_websocket_error,
    get_error_stats
)

__all__ = [
    'ClientErrorHandler',
    'ErrorContext',
    'ErrorSeverity',
    'ErrorCategory',
    'client_error_handler',
    'handle_error',
    'handle_mt5_error', 
    'handle_websocket_error',
    'get_error_stats'
]

__module_type__ = "centralized_infrastructure_client"
__version__ = "1.0.0"