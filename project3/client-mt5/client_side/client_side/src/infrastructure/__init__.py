"""
__init__.py - Infrastructure Module Initializer

🎯 PURPOSE:
Business: Infrastructure layer module initialization and exports
Technical: Centralized infrastructure access and dependency management
Domain: Infrastructure/Module Initialization

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:28.236Z
Session: client-side-ai-brain-full-compliance
Confidence: 94%
Complexity: low

🧩 PATTERNS USED:
- AI_BRAIN_INFRASTRUCTURE_INIT: Infrastructure layer initialization

📦 DEPENDENCIES:
Internal: central_hub
External: None

💡 AI DECISION REASONING:
Infrastructure module initialization provides unified access to all centralized services and components.

🚀 USAGE:
from src.infrastructure import CentralHub, CoreLogger

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

# Legacy imports (backward compatibility)
from .mt5 import *
from .websocket import *
from .streaming import *

# NEW: Centralized Infrastructure
from .central_hub import (
    ClientCentralHub,
    client_central_hub,
    get_system_status,
    get_health_summary,
    get_centralization_status,
    reload_all_configs,
    clear_all_caches
)

# Import centralized managers
from .imports import client_import_manager, get_module, get_class, get_function
from .errors import client_error_handler, handle_error, handle_mt5_error, handle_websocket_error, ErrorCategory, ErrorSeverity
from .logging import client_logger_manager, get_logger, setup_mt5_logger, setup_websocket_logger
from .config import client_config_manager, get_config, get_client_settings
from .performance import client_performance_manager, performance_tracked, track_performance, get_performance_report
from .validation import client_validator, validate_field, validate_dict, validate_mt5_connection, validate_trading_symbol, validate_tick_data

__all__ = [
    # Central Hub
    'ClientCentralHub',
    'client_central_hub',
    'get_system_status',
    'get_health_summary', 
    'get_centralization_status',
    'reload_all_configs',
    'clear_all_caches',
    
    # Import Manager
    'client_import_manager',
    'get_module',
    'get_class', 
    'get_function',
    
    # Error Handler
    'client_error_handler',
    'handle_error',
    'handle_mt5_error',
    'handle_websocket_error',
    'ErrorCategory',
    'ErrorSeverity',
    
    # Logger Manager
    'client_logger_manager',
    'get_logger',
    'setup_mt5_logger',
    'setup_websocket_logger',
    
    # Config Manager
    'client_config_manager',
    'get_config',
    'get_client_settings',
    
    # Performance Manager
    'client_performance_manager',
    'performance_tracked',
    'track_performance',
    'get_performance_report',
    
    # Validator
    'client_validator',
    'validate_field',
    'validate_dict',
    'validate_mt5_connection',
    'validate_trading_symbol',
    'validate_tick_data'
]

__version__ = "1.0.0"
__architecture__ = "Centralized Enterprise"