"""
__init__.py - Shared Utilities Module Initializer

🎯 PURPOSE:
Business: Shared utilities and common functionality initialization
Technical: Cross-cutting concern exports and utility access
Domain: Shared Utilities/Common Functionality

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:28.261Z
Session: client-side-ai-brain-full-compliance
Confidence: 91%
Complexity: low

🧩 PATTERNS USED:
- AI_BRAIN_SHARED_INIT: Shared utilities initialization

📦 DEPENDENCIES:
Internal: config_manager, logger_manager
External: None

💡 AI DECISION REASONING:
Shared module initialization provides unified access to common utilities and cross-cutting functionality.

🚀 USAGE:
from src.shared import ClientSettings, Credentials

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

from .config import *
from .security import *
from .utils import *

__all__ = []