"""
__init__.py - Shared Config Module Initializer

🎯 PURPOSE:
Business: Shared configuration components initialization
Technical: Client settings and config utilities exports
Domain: Shared Configuration/Module Initialization

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:28.628Z
Session: client-side-ai-brain-full-compliance
Confidence: 91%
Complexity: low

🧩 PATTERNS USED:
- AI_BRAIN_SHARED_CONFIG_INIT: Shared config module initialization

📦 DEPENDENCIES:
Internal: client_settings
External: None

💡 AI DECISION REASONING:
Shared config module initialization provides unified access to configuration utilities.

🚀 USAGE:
from src.shared.config import ClientSettings

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

from .client_settings import (
    get_client_settings, 
    ClientSettings, 
    ClientConstants,
    MT5Config, 
    NetworkConfig, 
    StreamingConfig,
    ApplicationConfig
)

# Alias for backward compatibility
get_settings = get_client_settings
get_mt5_settings = get_client_settings

__all__ = [
    # New centralized configuration
    "get_client_settings",
    "ClientSettings", 
    "ClientConstants",
    "MT5Config",
    "NetworkConfig",
    "StreamingConfig", 
    "ApplicationConfig",
    # Backward compatibility aliases
    "get_settings",
    "get_mt5_settings"
]