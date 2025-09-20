"""
__init__.py - Configuration Module Initializer

🎯 PURPOSE:
Business: Configuration management components initialization
Technical: Config manager and related component exports
Domain: Configuration/Module Initialization

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:28.381Z
Session: client-side-ai-brain-full-compliance
Confidence: 93%
Complexity: low

🧩 PATTERNS USED:
- AI_BRAIN_CONFIG_INIT: Configuration module initialization

📦 DEPENDENCIES:
Internal: config_manager
External: None

💡 AI DECISION REASONING:
Configuration module initialization provides unified access to configuration management.

🚀 USAGE:
from src.infrastructure.config import ConfigManager

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

from .config_manager import (
    ClientConfigManager,
    ConfigSection,
    client_config_manager,
    get_config,
    get_client_settings,
    get_mt5_config,
    get_websocket_config,
    get_config_status
)

__all__ = [
    'ClientConfigManager',
    'ConfigSection',
    'client_config_manager',
    'get_config',
    'get_client_settings',
    'get_mt5_config', 
    'get_websocket_config',
    'get_config_status'
]

__module_type__ = "centralized_infrastructure_client"
__version__ = "1.0.0"