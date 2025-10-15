"""
__init__.py - Import Management Module Initializer

🎯 PURPOSE:
Business: Import management components initialization
Technical: Import manager and related component exports
Domain: Import Management/Module Initialization

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:28.419Z
Session: client-side-ai-brain-full-compliance
Confidence: 88%
Complexity: low

🧩 PATTERNS USED:
- AI_BRAIN_IMPORT_INIT: Import management module initialization

📦 DEPENDENCIES:
Internal: import_manager
External: None

💡 AI DECISION REASONING:
Import module initialization provides unified access to safe module importing.

🚀 USAGE:
from src.infrastructure.imports import ImportManager

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

from .import_manager import (
    ClientImportManager,
    ImportMapping,
    client_import_manager,
    get_module,
    get_class,
    get_function,
    get_import_status
)

__all__ = [
    'ClientImportManager',
    'ImportMapping', 
    'client_import_manager',
    'get_module',
    'get_class',
    'get_function',
    'get_import_status'
]

__module_type__ = "centralized_infrastructure_client"
__version__ = "1.0.0"