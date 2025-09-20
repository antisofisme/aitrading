"""
User Service - User management and authentication
User profiles, permissions, and session management
"""
__version__ = "2.0.0"
__service_type__ = "user-service"

from .src import api, business, infrastructure

__all__ = ['api', 'business', 'infrastructure']

__user_features__ = [
    'authentication',
    'user_profiles',
    'permissions',
    'session_management'
]