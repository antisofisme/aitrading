"""
__init__.py - Health Module Initializer

🎯 PURPOSE:
Business: Health monitoring components initialization
Technical: Health core and related component exports
Domain: Health Monitoring/Module Initialization

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:28.587Z
Session: client-side-ai-brain-full-compliance
Confidence: 88%
Complexity: low

🧩 PATTERNS USED:
- AI_BRAIN_HEALTH_INIT: Health monitoring module initialization

📦 DEPENDENCIES:
Internal: health_core
External: None

💡 AI DECISION REASONING:
Health module initialization provides unified access to health monitoring.

🚀 USAGE:
from src.infrastructure.health import HealthCore

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

from .health_core import (
    HealthCore,
    ComponentHealth,
    HealthMetric,
    HealthAlert,
    SystemDiagnostics,
    ComponentStatus,
    MetricType,
    AlertSeverity,
    get_health_core,
    register_component_health,
    get_system_health_status,
    get_component_status,
    is_system_healthy
)

__all__ = [
    'HealthCore',
    'ComponentHealth',
    'HealthMetric',
    'HealthAlert',
    'SystemDiagnostics',
    'ComponentStatus',
    'MetricType',
    'AlertSeverity',
    'get_health_core',
    'register_component_health',
    'get_system_health_status', 
    'get_component_status',
    'is_system_healthy'
]