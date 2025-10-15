"""
__init__.py - Network Module Initializer

🎯 PURPOSE:
Business: Network communication components initialization
Technical: Network core and related component exports
Domain: Network Communication/Module Initialization

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:28.559Z
Session: client-side-ai-brain-full-compliance
Confidence: 91%
Complexity: low

🧩 PATTERNS USED:
- AI_BRAIN_NETWORK_INIT: Network module initialization

📦 DEPENDENCIES:
Internal: network_core
External: None

💡 AI DECISION REASONING:
Network module initialization provides unified access to network communication.

🚀 USAGE:
from src.infrastructure.network import NetworkCore

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

from .network_core import (
    NetworkCore,
    ServiceEndpoint,
    NetworkRequest,
    NetworkResponse,
    ServiceHealth,
    NetworkStats,
    ConnectionType,
    RetryStrategy,
    HealthStatus,
    get_network_core,
    make_request,
    get_service_health,
    register_service_endpoint,
    api_gateway_request,
    data_bridge_request,
    database_request,
    ai_orchestration_request
)

__all__ = [
    'NetworkCore',
    'ServiceEndpoint',
    'NetworkRequest',
    'NetworkResponse', 
    'ServiceHealth',
    'NetworkStats',
    'ConnectionType',
    'RetryStrategy',
    'HealthStatus',
    'get_network_core',
    'make_request',
    'get_service_health',
    'register_service_endpoint',
    'api_gateway_request',
    'data_bridge_request',
    'database_request',
    'ai_orchestration_request'
]