"""
__init__.py - Shared Security Module Initializer

🎯 PURPOSE:
Business: Shared security components initialization
Technical: Credentials management and security utilities exports
Domain: Shared Security/Module Initialization

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:28.665Z
Session: client-side-ai-brain-full-compliance
Confidence: 94%
Complexity: low

🧩 PATTERNS USED:
- AI_BRAIN_SHARED_SECURITY_INIT: Shared security module initialization

📦 DEPENDENCIES:
Internal: credentials
External: None

💡 AI DECISION REASONING:
Shared security module initialization provides unified access to security utilities.

🚀 USAGE:
from src.shared.security import Credentials

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

from .credentials import (
    CredentialManager,
    SecureConfig,
    get_credential_manager,
    encrypt_env_file,
    decrypt_env_file
)

__all__ = [
    'CredentialManager',
    'SecureConfig', 
    'get_credential_manager',
    'encrypt_env_file',
    'decrypt_env_file'
]