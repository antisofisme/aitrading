"""
__init__.py - Shared Utils Module Initializer

🎯 PURPOSE:
Business: Shared utility components initialization
Technical: Utility functions and helper components exports
Domain: Shared Utilities/Module Initialization

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:28.689Z
Session: client-side-ai-brain-full-compliance
Confidence: 90%
Complexity: low

🧩 PATTERNS USED:
- AI_BRAIN_SHARED_UTILS_INIT: Shared utilities module initialization

📦 DEPENDENCIES:
Internal: manage_credentials, mt5_error_handling, debug_config
External: None

💡 AI DECISION REASONING:
Shared utils module initialization provides unified access to utility functions.

🚀 USAGE:
from src.shared.utils import manage_credentials, mt5_error_handling

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

from .mt5_error_handling import (
    retry_with_backoff,
    MT5ErrorContext,
    handle_mt5_connection_error,
    handle_websocket_error,
    handle_streaming_error
)

__all__ = [
    "retry_with_backoff",
    "MT5ErrorContext",
    "handle_mt5_connection_error",
    "handle_websocket_error", 
    "handle_streaming_error"
]