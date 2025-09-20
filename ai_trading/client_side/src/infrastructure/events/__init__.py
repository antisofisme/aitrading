"""
__init__.py - Event System Module Initializer

🎯 PURPOSE:
Business: Event management components initialization
Technical: Event core and related component exports
Domain: Event Management/Module Initialization

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:28.460Z
Session: client-side-ai-brain-full-compliance
Confidence: 89%
Complexity: low

🧩 PATTERNS USED:
- AI_BRAIN_EVENT_INIT: Event system module initialization

📦 DEPENDENCIES:
Internal: event_core
External: None

💡 AI DECISION REASONING:
Event module initialization provides unified access to event management system.

🚀 USAGE:
from src.infrastructure.events import EventCore

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

from .event_core import (
    EventCore,
    Event, 
    EventType,
    EventPriority,
    EventHandler,
    EventStats,
    get_event_core,
    publish_event,
    subscribe_to_events,
    publish_mt5_event,
    publish_websocket_event,
    publish_config_event,
    publish_performance_event
)

__all__ = [
    'EventCore',
    'Event',
    'EventType', 
    'EventPriority',
    'EventHandler',
    'EventStats',
    'get_event_core',
    'publish_event',
    'subscribe_to_events',
    'publish_mt5_event',
    'publish_websocket_event',
    'publish_config_event',
    'publish_performance_event'
]