"""
User Service - Core Microservice
Enterprise user management dengan project collaboration dan AI workflow orchestration
"""

__version__ = "1.0.0"
__service__ = "user-service"

# Service exports
from .business.user_service import UserService
from .business.project_service import ProjectService
from .business.workflow_service import AIWorkflowService
from .api.user_endpoints import router

__all__ = [
    "UserService",
    "ProjectService", 
    "AIWorkflowService",
    "router"
]