"""
__init__.py - Performance Module Initializer

🎯 PURPOSE:
Business: Performance monitoring and optimization components initialization
Technical: Performance manager and related component exports
Domain: Performance/Module Initialization

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:28.335Z
Session: client-side-ai-brain-full-compliance
Confidence: 90%
Complexity: low

🧩 PATTERNS USED:
- AI_BRAIN_PERFORMANCE_INIT: Performance module initialization

📦 DEPENDENCIES:
Internal: performance_manager
External: None

💡 AI DECISION REASONING:
Performance module initialization provides unified access to performance monitoring.

🚀 USAGE:
from src.infrastructure.performance import ClientPerformanceManager

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

from .performance_manager import (
    ClientPerformanceManager,
    PerformanceMetric,
    ComponentStats,
    PerformanceCache,
    client_performance_manager,
    performance_tracked,
    track_performance,
    get_performance_cache,
    get_performance_report,
    optimize_memory
)

__all__ = [
    'ClientPerformanceManager',
    'PerformanceMetric',
    'ComponentStats', 
    'PerformanceCache',
    'client_performance_manager',
    'performance_tracked',
    'track_performance',
    'get_performance_cache',
    'get_performance_report',
    'optimize_memory'
]

__module_type__ = "centralized_infrastructure_client"
__version__ = "1.0.0"