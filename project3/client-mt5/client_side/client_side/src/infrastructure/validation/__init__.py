"""
__init__.py - Validation Module Initializer

🎯 PURPOSE:
Business: Data validation components initialization
Technical: Validation core and validator component exports
Domain: Data Validation/Module Initialization

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:28.502Z
Session: client-side-ai-brain-full-compliance
Confidence: 92%
Complexity: low

🧩 PATTERNS USED:
- AI_BRAIN_VALIDATION_INIT: Validation module initialization

📦 DEPENDENCIES:
Internal: validator, validation_core
External: None

💡 AI DECISION REASONING:
Validation module initialization provides unified access to data validation systems.

🚀 USAGE:
from src.infrastructure.validation import Validator, ValidationCore

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

# Existing validation system
from .validator import (
    ClientValidator,
    ValidationLevel,
    ValidationError,
    ValidationReport,
    client_validator,
    validate_field,
    validate_dict,
    validate_mt5_connection,
    validate_trading_symbol,
    validate_tick_data,
    get_validation_stats
)

# AI Brain ValidationCore system
from .validation_core import (
    ValidationCore,
    ValidationRule,
    ValidationResult,
    ValidationContext,
    ValidationSeverity,
    ValidationCategory,
    RuleType,
    ValidationStats,
    get_validation_core,
    validate_data,
    validate_field_value,
    add_custom_rule
)

__all__ = [
    # Existing validation system
    'ClientValidator',
    'ValidationLevel',
    'ValidationError',
    'ValidationReport',
    'client_validator',
    'validate_field',
    'validate_dict',
    'validate_mt5_connection',
    'validate_trading_symbol',
    'validate_tick_data',
    'get_validation_stats',
    # AI Brain ValidationCore system
    'ValidationCore',
    'ValidationRule',
    'ValidationResult',
    'ValidationContext',
    'ValidationSeverity',
    'ValidationCategory',
    'RuleType',
    'ValidationStats',
    'get_validation_core',
    'validate_data',
    'validate_field_value',
    'add_custom_rule'
]

__module_type__ = "centralized_infrastructure_client"
__version__ = "1.0.0"