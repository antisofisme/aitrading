"""
__init__.py - Streaming Module Initializer

🎯 PURPOSE:
Business: Streaming infrastructure components initialization
Technical: Streaming client and related component exports
Domain: Streaming/Module Initialization

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:28.299Z
Session: client-side-ai-brain-full-compliance
Confidence: 91%
Complexity: low

🧩 PATTERNS USED:
- AI_BRAIN_STREAMING_INIT: Streaming module initialization

📦 DEPENDENCIES:
Internal: mt5_redpanda
External: None

💡 AI DECISION REASONING:
Streaming module initialization provides unified access to streaming infrastructure.

🚀 USAGE:
from src.infrastructure.streaming import MT5RedpandaStreamer

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

from .mt5_redpanda import MT5RedpandaProducer, MT5RedpandaConsumer, MT5RedpandaManager, MT5RedpandaConfig, MT5Event

__all__ = [
    "MT5RedpandaProducer",
    "MT5RedpandaConsumer", 
    "MT5RedpandaManager",
    "MT5RedpandaConfig",
    "MT5Event"
]