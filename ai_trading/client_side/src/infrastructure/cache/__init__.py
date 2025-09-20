"""
__init__.py - Cache Module Initializer

🎯 PURPOSE:
Business: Caching system components initialization
Technical: Cache core and related component exports
Domain: Caching/Module Initialization

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:28.437Z
Session: client-side-ai-brain-full-compliance
Confidence: 90%
Complexity: low

🧩 PATTERNS USED:
- AI_BRAIN_CACHE_INIT: Caching module initialization

📦 DEPENDENCIES:
Internal: core_cache
External: None

💡 AI DECISION REASONING:
Cache module initialization provides unified access to caching infrastructure.

🚀 USAGE:
from src.infrastructure.cache import CoreCache

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

from .core_cache import CoreCache, CacheStrategy, CachePriority, CacheStats, CacheEntry

__all__ = [
    'CoreCache',
    'CacheStrategy', 
    'CachePriority',
    'CacheStats',
    'CacheEntry'
]