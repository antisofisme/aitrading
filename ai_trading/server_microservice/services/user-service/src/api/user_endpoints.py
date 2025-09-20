"""
User Service - API Endpoints
REST API endpoints for user management operations
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from datetime import datetime

# PER-SERVICE INFRASTRUCTURE INTEGRATION
from ..business.user_service import UserService, UserCreateRequest, UserUpdateRequest, UserProfile
from ..business.project_service import ProjectService, ProjectCreateRequest, Project
from ..business.workflow_service import AIWorkflowService, WorkflowRequest, WorkflowExecution
from ..business.base_domain_service import ServiceContext

router = APIRouter(prefix="/api/v1", tags=["user-service"])

# Service instances
user_service = UserService()
project_service = ProjectService() 
workflow_service = AIWorkflowService()

async def get_service_context(
    user_id: str = None,
    tenant_id: Optional[str] = None,
    organization_id: Optional[str] = None
) -> ServiceContext:
    """Get service context for requests"""
    # Use environment-specific defaults for development
    import os
    environment = os.getenv('MICROSERVICE_ENVIRONMENT', 'development')
    
    # Only use demo values in development environment
    if environment == 'development':
        user_id = user_id or os.getenv('DEV_DEFAULT_USER_ID', 'demo_user')
        tenant_id = tenant_id or os.getenv('DEV_DEFAULT_TENANT_ID', 'demo_tenant')
        demo_permissions = os.getenv('DEV_DEFAULT_PERMISSIONS', 'user:read,project:read,workflow:read').split(',')
    else:
        # Production/staging should require explicit user context
        if not user_id:
            raise ValueError("user_id is required in non-development environment")
        demo_permissions = []
    
    return ServiceContext(
        user_id=user_id,
        tenant_id=tenant_id,
        organization_id=organization_id,
        permissions=demo_permissions
    )

# User Management Endpoints
@router.post("/users", response_model=Dict[str, Any])
async def create_user(
    request: Dict[str, Any],
    context: ServiceContext = Depends(get_service_context)
):
    """Create new user"""
    try:
        create_request = UserCreateRequest(
            email=request["email"],
            password=request["password"],
            full_name=request["full_name"],
            role=request.get("role", "user"),
            organization_id=request.get("organization_id"),
            profile_settings=request.get("profile_settings"),
            ai_preferences=request.get("ai_preferences")
        )
        
        result = await user_service.create_user(create_request, context)
        
        if result.success:
            return {
                "success": True,
                "data": {
                    "user_id": result.data.user_id,
                    "email": result.data.email,
                    "full_name": result.data.full_name,
                    "role": result.data.role,
                    "created_at": result.data.created_at.isoformat()
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result.error_message)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{user_id}", response_model=Dict[str, Any])
async def get_user(
    user_id: str,
    context: ServiceContext = Depends(get_service_context)
):
    """Get user profile"""
    try:
        result = await user_service.get_user_profile(user_id, context)
        
        if result.success:
            return {
                "success": True,
                "data": {
                    "user_id": result.data.user_id,
                    "email": result.data.email,
                    "full_name": result.data.full_name,
                    "role": result.data.role,
                    "organization_id": result.data.organization_id,
                    "is_active": result.data.is_active,
                    "created_at": result.data.created_at.isoformat(),
                    "profile_settings": result.data.profile_settings,
                    "ai_preferences": result.data.ai_preferences
                }
            }
        else:
            raise HTTPException(status_code=404, detail=result.error_message)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{user_id}/ai-preferences", response_model=Dict[str, Any])
async def get_user_ai_preferences(
    user_id: str,
    context: ServiceContext = Depends(get_service_context)
):
    """Get user AI preferences"""
    try:
        result = await user_service.get_ai_preferences(user_id, context)
        
        if result.success:
            return {
                "success": True,
                "data": result.data
            }
        else:
            raise HTTPException(status_code=404, detail=result.error_message)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/users/{user_id}/ai-preferences", response_model=Dict[str, Any])
async def update_user_ai_preferences(
    user_id: str,
    ai_preferences: Dict[str, Any],
    context: ServiceContext = Depends(get_service_context)
):
    """Update user AI preferences"""
    try:
        result = await user_service.update_ai_preferences(user_id, ai_preferences, context)
        
        if result.success:
            return {
                "success": True,
                "data": result.data
            }
        else:
            raise HTTPException(status_code=400, detail=result.error_message)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Project Management Endpoints
@router.post("/projects", response_model=Dict[str, Any])
async def create_project(
    request: Dict[str, Any],
    context: ServiceContext = Depends(get_service_context)
):
    """Create new project"""
    try:
        from ..business.project_service import ProjectPriority
        
        create_request = ProjectCreateRequest(
            name=request["name"],
            description=request["description"],
            priority=ProjectPriority(request.get("priority", "medium")),
            due_date=datetime.fromisoformat(request["due_date"]) if request.get("due_date") else None,
            tags=request.get("tags", []),
            metadata=request.get("metadata", {})
        )
        
        result = await project_service.create_project(create_request, context)
        
        if result.success:
            return {
                "success": True,
                "data": {
                    "project_id": result.data.project_id,
                    "name": result.data.name,
                    "description": result.data.description,
                    "status": result.data.status.value,
                    "priority": result.data.priority.value,
                    "created_at": result.data.created_at.isoformat()
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result.error_message)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}", response_model=Dict[str, Any])
async def get_project(
    project_id: str,
    context: ServiceContext = Depends(get_service_context)
):
    """Get project details"""
    try:
        result = await project_service.get_project(project_id, context)
        
        if result.success:
            return {
                "success": True,
                "data": {
                    "project_id": result.data.project_id,
                    "name": result.data.name,
                    "description": result.data.description,
                    "status": result.data.status.value,
                    "priority": result.data.priority.value,
                    "owner_id": result.data.owner_id,
                    "completion_percentage": result.data.completion_percentage,
                    "total_cost": result.data.total_cost,
                    "created_at": result.data.created_at.isoformat(),
                    "tags": result.data.tags
                }
            }
        else:
            raise HTTPException(status_code=404, detail=result.error_message)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}/analytics", response_model=Dict[str, Any])
async def get_project_analytics(
    project_id: str,
    context: ServiceContext = Depends(get_service_context)
):
    """Get project analytics"""
    try:
        result = await project_service.generate_project_analytics(project_id, context)
        
        if result.success:
            return {
                "success": True,
                "data": result.data
            }
        else:
            raise HTTPException(status_code=404, detail=result.error_message)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Workflow Management Endpoints  
@router.post("/workflows/templates", response_model=Dict[str, Any])
async def create_workflow_template(
    request: Dict[str, Any],
    context: ServiceContext = Depends(get_service_context)
):
    """Create workflow template"""
    try:
        result = await workflow_service.create_workflow_template(
            name=request["name"],
            description=request["description"],
            category=request["category"],
            ai_services=request["ai_services"],
            input_schema=request["input_schema"],
            output_schema=request["output_schema"],
            steps=request["steps"],
            estimated_cost=request["estimated_cost"],
            estimated_duration=request["estimated_duration"],
            tags=request.get("tags", []),
            context=context
        )
        
        if result.success:
            return {
                "success": True,
                "data": {
                    "template_id": result.data.template_id,
                    "name": result.data.name,
                    "category": result.data.category,
                    "estimated_cost": result.data.estimated_cost,
                    "created_at": result.data.created_at.isoformat()
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result.error_message)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workflows/execute", response_model=Dict[str, Any])
async def execute_workflow(
    request: Dict[str, Any],
    context: ServiceContext = Depends(get_service_context)
):
    """Execute workflow"""
    try:
        from ..business.workflow_service import WorkflowPriority
        
        workflow_request = WorkflowRequest(
            template_id=request["template_id"],
            input_data=request["input_data"],
            priority=WorkflowPriority(request.get("priority", "normal")),
            max_cost=request.get("max_cost"),
            metadata=request.get("metadata", {})
        )
        
        result = await workflow_service.execute_workflow(workflow_request, context)
        
        if result.success:
            return {
                "success": True,
                "data": {
                    "execution_id": result.data.execution_id,
                    "template_id": result.data.template_id,
                    "status": result.data.status.value,
                    "progress": result.data.progress,
                    "estimated_cost": result.data.cost_incurred
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result.error_message)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflows/executions/{execution_id}", response_model=Dict[str, Any])
async def get_workflow_execution(
    execution_id: str,
    context: ServiceContext = Depends(get_service_context)
):
    """Get workflow execution status"""
    try:
        result = await workflow_service.get_execution_status(execution_id, context)
        
        if result.success:
            return {
                "success": True,
                "data": {
                    "execution_id": result.data.execution_id,
                    "template_id": result.data.template_id,
                    "status": result.data.status.value,
                    "progress": result.data.progress,
                    "current_step": result.data.current_step,
                    "total_steps": result.data.total_steps,
                    "cost_incurred": result.data.cost_incurred,
                    "started_at": result.data.started_at.isoformat() if result.data.started_at else None,
                    "completed_at": result.data.completed_at.isoformat() if result.data.completed_at else None,
                    "error_message": result.data.error_message
                }
            }
        else:
            raise HTTPException(status_code=404, detail=result.error_message)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health Check
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "service": "user-service",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "user_service": "operational",
            "project_service": "operational", 
            "workflow_service": "operational"
        }
    }