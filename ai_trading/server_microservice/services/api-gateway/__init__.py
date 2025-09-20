"""
API Gateway Service - Unified service interface
Central routing and authentication for all microservices
"""
__version__ = "2.0.0"
__service_type__ = "api-gateway"

from .src import api, business, infrastructure

__all__ = ['api', 'business', 'infrastructure']

__gateway_features__ = [
    'request_routing',
    'authentication',
    'rate_limiting',
    'service_discovery'
]