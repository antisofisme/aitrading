"""
Optional Infrastructure Patterns - Advanced features for complex scenarios
"""
from .event_core import CoreEventManager
from .validation_core import CoreValidator
from .container_core import CoreServiceContainer
from .factory_core import CoreFactory

__all__ = [
    'CoreEventManager',
    'CoreValidator',
    'CoreServiceContainer',
    'CoreFactory'
]

# Optional pattern metadata
__optional_patterns__ = [
    "events", "validation", "container", "factory"
]