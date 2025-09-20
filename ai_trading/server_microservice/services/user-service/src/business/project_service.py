"""
User Service - Project Management
Enterprise-grade project management dengan AI integration, collaboration, dan analytics
Migrated from server_side with per-service infrastructure patterns
"""

import uuid
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

# PER-SERVICE INFRASTRUCTURE INTEGRATION
from ....shared.infrastructure.base.base_error_handler import BaseErrorHandler, ErrorCategory
from ....shared.infrastructure.base.base_performance import BasePerformance
from .base_domain_service import BaseDomainService, ServiceResult, ServiceContext

class ProjectStatus(Enum):
    """Project status"""
    DRAFT = "draft"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class ProjectPriority(Enum):
    """Project priority"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class CollaboratorRole(Enum):
    """Project collaborator roles"""
    OWNER = "owner"
    ADMIN = "admin"
    CONTRIBUTOR = "contributor"
    VIEWER = "viewer"

@dataclass
class ProjectSettings:
    """Project configuration settings"""
    ai_features_enabled: bool = True
    auto_analysis_enabled: bool = True
    collaboration_enabled: bool = True
    version_control_enabled: bool = True
    cost_tracking_enabled: bool = True
    analytics_enabled: bool = True
    notification_settings: Dict[str, bool] = None
    ai_model_preferences: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.notification_settings is None:
            self.notification_settings = {
                "task_updates": True,
                "ai_insights": True,
                "cost_alerts": True,
                "collaboration": True
            }
        if self.ai_model_preferences is None:
            self.ai_model_preferences = {
                "default_model": "gpt-4",
                "cost_preference": "balanced",
                "quality_threshold": 0.8
            }

@dataclass
class Project:
    """Project data model"""
    project_id: str
    name: str
    description: str
    status: ProjectStatus
    priority: ProjectPriority
    owner_id: str
    organization_id: Optional[str]
    tenant_id: Optional[str]
    settings: ProjectSettings
    created_at: datetime
    updated_at: datetime
    due_date: Optional[datetime]
    completion_percentage: float
    total_cost: float
    ai_insights: Dict[str, Any]
    tags: List[str]
    metadata: Dict[str, Any]

@dataclass
class ProjectCollaborator:
    """Project collaborator"""
    user_id: str
    project_id: str
    role: CollaboratorRole
    permissions: List[str]
    added_by: str
    added_at: datetime
    last_active: Optional[datetime]

@dataclass
class ProjectActivity:
    """Project activity log"""
    activity_id: str
    project_id: str
    user_id: str
    action: str
    description: str
    entity_type: str  # project, task, ai_workflow, etc
    entity_id: Optional[str]
    changes: Dict[str, Any]
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class ProjectCreateRequest:
    """Project creation request"""
    name: str
    description: str
    priority: ProjectPriority = ProjectPriority.MEDIUM
    due_date: Optional[datetime] = None
    settings: Optional[ProjectSettings] = None
    tags: List[str] = None
    metadata: Dict[str, Any] = None

@dataclass
class ProjectUpdateRequest:
    """Project update request"""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    priority: Optional[ProjectPriority] = None
    due_date: Optional[datetime] = None
    settings: Optional[ProjectSettings] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class ProjectService(BaseDomainService):
    """
    Enterprise Project Service dengan:
    - Multi-tenant project management
    - AI-powered project analytics
    - Collaboration dan permission management
    - Cost tracking dan optimization
    - Activity logging dan audit trail
    - Integration dengan AI workflows
    
    MIGRATED TO MICROSERVICE ARCHITECTURE with per-service infrastructure
    """
    
    def __init__(self):
        super().__init__("project_management")
    
    async def _initialize_service(self):
        """Initialize project service with per-service infrastructure"""
        self.logger.info("ProjectService initializing with AI integration")
        
        # Cache configurations for project service
        self.project_cache_ttl = 3600  # 1 hour
        self.collaborator_cache_ttl = 1800  # 30 minutes
        self.activity_cache_ttl = 900  # 15 minutes
        self.analytics_cache_ttl = 7200  # 2 hours
        
        self.logger.info("ProjectService initialized successfully", extra={
            "cache_ttl_config": {
                "project": self.project_cache_ttl,
                "collaborator": self.collaborator_cache_ttl,
                "activity": self.activity_cache_ttl,
                "analytics": self.analytics_cache_ttl
            }
        })
    
    def _get_required_permission(self, operation: str) -> Optional[str]:
        """Get required permission untuk project operations"""
        permission_map = {
            "create_project": "project:create",
            "update_project": "project:update",
            "delete_project": "project:delete",
            "view_project": "project:read",
            "list_projects": "project:read",
            "add_collaborator": "project:update",
            "remove_collaborator": "project:update",
            "update_collaborator": "project:update",
            "view_analytics": "project:read",
            "export_project": "project:read"
        }
        return permission_map.get(operation)
    
    # Core Project Management
    async def create_project(
        self, 
        request: ProjectCreateRequest, 
        context: ServiceContext
    ) -> ServiceResult[Project]:
        """Create new project dengan AI integration"""
        
        async def _create_project_operation():
            project_id = str(uuid.uuid4())
            
            # Default settings
            settings = request.settings or ProjectSettings()
            
            # Create project
            project = Project(
                project_id=project_id,
                name=request.name,
                description=request.description,
                status=ProjectStatus.DRAFT,
                priority=request.priority,
                owner_id=context.user_id,
                organization_id=context.organization_id,
                tenant_id=context.tenant_id,
                settings=settings,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                due_date=request.due_date,
                completion_percentage=0.0,
                total_cost=0.0,
                ai_insights={},
                tags=request.tags or [],
                metadata=request.metadata or {}
            )
            
            # Store in database using per-service database connection
            async with await self.get_db_connection() as conn:
                await conn.execute("""
                    INSERT INTO projects (
                        project_id, name, description, status, priority, owner_id,
                        organization_id, tenant_id, settings, created_at, updated_at,
                        due_date, completion_percentage, total_cost, ai_insights,
                        tags, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
                """, 
                project_id, request.name, request.description, project.status.value,
                project.priority.value, context.user_id, context.organization_id,
                context.tenant_id, settings.__dict__, datetime.now(), datetime.now(),
                request.due_date, 0.0, 0.0, {}, request.tags or [], request.metadata or {})
                
                # Add owner as collaborator
                await conn.execute("""
                    INSERT INTO project_collaborators (
                        user_id, project_id, role, permissions, added_by, added_at
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                """, 
                context.user_id, project_id, CollaboratorRole.OWNER.value,
                ["project:*"], context.user_id, datetime.now())
            
            # Cache project using per-service cache
            await self.set_cached(
                f"project:{project_id}",
                project,
                self.project_cache_ttl,
                context.tenant_id
            )
            
            # Store project embedding untuk search (if vector DB enabled)
            if self._vector_db:
                project_embedding = await self._generate_project_embedding(project)
                await self.store_embedding(
                    "projects",
                    project_id,
                    project_embedding,
                    {
                        "name": request.name,
                        "description": request.description,
                        "priority": request.priority.value,
                        "tags": request.tags or [],
                        "owner_id": context.user_id,
                        "tenant_id": context.tenant_id
                    }
                )
            
            # Store project relationships (if graph DB enabled)
            if self._graph_db:
                # Project -> Owner relationship
                await self.store_relationship(
                    project_id,
                    context.user_id,
                    "OWNED_BY",
                    {"created_at": datetime.now().isoformat()}
                )
                
                # Project -> Organization relationship
                if context.organization_id:
                    await self.store_relationship(
                        project_id,
                        context.organization_id,
                        "BELONGS_TO_ORG",
                        {"created_at": datetime.now().isoformat()}
                    )
            
            # Log activity
            await self._log_activity(
                project_id,
                context.user_id,
                "project_created",
                f"Project '{request.name}' created",
                "project",
                project_id,
                {"project_data": project.__dict__},
                context
            )
            
            # Publish project created event using per-service event publisher
            self.event_publisher.publish_project_event(
                "project_created",
                project_id,
                {
                    "name": request.name,
                    "priority": request.priority.value,
                    "organization_id": context.organization_id
                },
                context.user_id,
                {"operation": "create_project", "service": "user-service"}
            )
            
            # Also publish to service event system for inter-service communication
            await self.publish(
                "project_created",
                {
                    "project_id": project_id,
                    "name": request.name,
                    "owner_id": context.user_id,
                    "organization_id": context.organization_id,
                    "priority": request.priority.value
                },
                context
            )
            
            # Generate initial AI insights jika enabled
            if settings.ai_features_enabled:
                await self._generate_project_insights(project, context)
            
            return project
        
        return await self.execute_with_context(
            "create_project",
            context,
            _create_project_operation
        )
    
    async def get_project(
        self, 
        project_id: str, 
        context: ServiceContext
    ) -> ServiceResult[Project]:
        """Get project dengan access control"""
        
        async def _get_project_operation():
            # Check access permission
            has_access = await self._check_project_access(project_id, context.user_id, "read")
            if not has_access:
                raise PermissionError("Access denied to project")
            
            # Try cache first
            cached_project = await self.get_cached(
                f"project:{project_id}",
                context.tenant_id
            )
            if cached_project:
                return cached_project
            
            # Get from database
            async with await self.get_db_connection() as conn:
                record = await conn.fetchrow("""
                    SELECT project_id, name, description, status, priority, owner_id,
                           organization_id, tenant_id, settings, created_at, updated_at,
                           due_date, completion_percentage, total_cost, ai_insights,
                           tags, metadata
                    FROM projects 
                    WHERE project_id = $1
                """, project_id)
                
                if not record:
                    raise ValueError("Project not found")
                
                project = Project(
                    project_id=record["project_id"],
                    name=record["name"],
                    description=record["description"],
                    status=ProjectStatus(record["status"]),
                    priority=ProjectPriority(record["priority"]),
                    owner_id=record["owner_id"],
                    organization_id=record["organization_id"],
                    tenant_id=record["tenant_id"],
                    settings=ProjectSettings(**record["settings"]),
                    created_at=record["created_at"],
                    updated_at=record["updated_at"],
                    due_date=record["due_date"],
                    completion_percentage=record["completion_percentage"],
                    total_cost=record["total_cost"],
                    ai_insights=record["ai_insights"],
                    tags=record["tags"],
                    metadata=record["metadata"]
                )
                
                # Cache project
                await self.set_cached(
                    f"project:{project_id}",
                    project,
                    self.project_cache_ttl,
                    context.tenant_id
                )
                
                return project
        
        return await self.execute_with_context(
            "view_project",
            context,
            _get_project_operation
        )
    
    async def update_project(
        self, 
        project_id: str, 
        request: ProjectUpdateRequest, 
        context: ServiceContext
    ) -> ServiceResult[Project]:
        """Update project dengan change tracking"""
        
        async def _update_project_operation():
            # Check access permission
            has_access = await self._check_project_access(project_id, context.user_id, "write")
            if not has_access:
                raise PermissionError("Access denied to project")
            
            # Get current project
            current_project_result = await self.get_project(project_id, context)
            if not current_project_result.success:
                raise ValueError("Project not found")
            
            current_project = current_project_result.data
            
            # Build update query
            update_fields = []
            update_values = []
            param_index = 1
            changes = {}
            
            if request.name is not None and request.name != current_project.name:
                update_fields.append(f"name = ${param_index}")
                update_values.append(request.name)
                changes["name"] = {"old": current_project.name, "new": request.name}
                param_index += 1
            
            if request.description is not None and request.description != current_project.description:
                update_fields.append(f"description = ${param_index}")
                update_values.append(request.description)
                changes["description"] = {"old": current_project.description, "new": request.description}
                param_index += 1
            
            if request.status is not None and request.status != current_project.status:
                update_fields.append(f"status = ${param_index}")
                update_values.append(request.status.value)
                changes["status"] = {"old": current_project.status.value, "new": request.status.value}
                param_index += 1
            
            if request.priority is not None and request.priority != current_project.priority:
                update_fields.append(f"priority = ${param_index}")
                update_values.append(request.priority.value)
                changes["priority"] = {"old": current_project.priority.value, "new": request.priority.value}
                param_index += 1
            
            if request.due_date is not None and request.due_date != current_project.due_date:
                update_fields.append(f"due_date = ${param_index}")
                update_values.append(request.due_date)
                changes["due_date"] = {"old": current_project.due_date, "new": request.due_date}
                param_index += 1
            
            if request.settings is not None:
                update_fields.append(f"settings = ${param_index}")
                update_values.append(request.settings.__dict__)
                changes["settings"] = {"old": current_project.settings.__dict__, "new": request.settings.__dict__}
                param_index += 1
            
            if request.tags is not None and request.tags != current_project.tags:
                update_fields.append(f"tags = ${param_index}")
                update_values.append(request.tags)
                changes["tags"] = {"old": current_project.tags, "new": request.tags}
                param_index += 1
            
            if request.metadata is not None:
                merged_metadata = {**current_project.metadata, **request.metadata}
                update_fields.append(f"metadata = ${param_index}")
                update_values.append(merged_metadata)
                changes["metadata"] = {"old": current_project.metadata, "new": merged_metadata}
                param_index += 1
            
            if not update_fields:
                return current_project  # No changes
            
            # Add updated_at
            update_fields.append("updated_at = NOW()")
            update_values.append(project_id)
            
            query = f"""
                UPDATE projects 
                SET {', '.join(update_fields)}
                WHERE project_id = ${param_index}
                RETURNING project_id, name, description, status, priority, owner_id,
                         organization_id, tenant_id, settings, created_at, updated_at,
                         due_date, completion_percentage, total_cost, ai_insights,
                         tags, metadata
            """
            
            async with await self.get_db_connection() as conn:
                record = await conn.fetchrow(query, *update_values)
                
                updated_project = Project(
                    project_id=record["project_id"],
                    name=record["name"],
                    description=record["description"],
                    status=ProjectStatus(record["status"]),
                    priority=ProjectPriority(record["priority"]),
                    owner_id=record["owner_id"],
                    organization_id=record["organization_id"],
                    tenant_id=record["tenant_id"],
                    settings=ProjectSettings(**record["settings"]),
                    created_at=record["created_at"],
                    updated_at=record["updated_at"],
                    due_date=record["due_date"],
                    completion_percentage=record["completion_percentage"],
                    total_cost=record["total_cost"],
                    ai_insights=record["ai_insights"],
                    tags=record["tags"],
                    metadata=record["metadata"]
                )
                
                # Update cache
                await self.set_cached(
                    f"project:{project_id}",
                    updated_project,
                    self.project_cache_ttl,
                    context.tenant_id
                )
                
                # Update vector embedding jika ada perubahan relevan
                if self._vector_db and any(field in changes for field in ["name", "description", "tags"]):
                    project_embedding = await self._generate_project_embedding(updated_project)
                    await self.store_embedding(
                        "projects",
                        project_id,
                        project_embedding,
                        {
                            "name": updated_project.name,
                            "description": updated_project.description,
                            "priority": updated_project.priority.value,
                            "tags": updated_project.tags,
                            "owner_id": updated_project.owner_id,
                            "tenant_id": context.tenant_id
                        }
                    )
                
                # Log activity
                await self._log_activity(
                    project_id,
                    context.user_id,
                    "project_updated",
                    f"Project '{updated_project.name}' updated",
                    "project",
                    project_id,
                    {"changes": changes},
                    context
                )
                
                # Publish project updated event
                self.event_publisher.publish_project_event(
                    "project_updated",
                    project_id,
                    {"changes": changes},
                    context.user_id,
                    {"operation": "update_project", "service": "user-service"}
                )
                
                await self.publish(
                    "project_updated",
                    {
                        "project_id": project_id,
                        "changes": changes,
                        "updated_by": context.user_id
                    },
                    context
                )
                
                return updated_project
        
        return await self.execute_with_context(
            "update_project",
            context,
            _update_project_operation
        )
    
    # Collaboration Management
    async def add_collaborator(
        self, 
        project_id: str, 
        user_id: str, 
        role: CollaboratorRole,
        permissions: List[str],
        context: ServiceContext
    ) -> ServiceResult[ProjectCollaborator]:
        """Add collaborator to project"""
        
        async def _add_collaborator_operation():
            # Check access permission
            has_access = await self._check_project_access(project_id, context.user_id, "admin")
            if not has_access:
                raise PermissionError("Access denied to manage collaborators")
            
            # Check if user already collaborator
            existing = await self._get_collaborator(project_id, user_id)
            if existing:
                raise ValueError("User is already a collaborator")
            
            collaborator = ProjectCollaborator(
                user_id=user_id,
                project_id=project_id,
                role=role,
                permissions=permissions,
                added_by=context.user_id,
                added_at=datetime.now(),
                last_active=None
            )
            
            # Store in database
            async with await self.get_db_connection() as conn:
                await conn.execute("""
                    INSERT INTO project_collaborators (
                        user_id, project_id, role, permissions, added_by, added_at
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                """, 
                user_id, project_id, role.value, permissions, context.user_id, datetime.now())
            
            # Cache collaborator
            await self.set_cached(
                f"collaborator:{project_id}:{user_id}",
                collaborator,
                self.collaborator_cache_ttl,
                context.tenant_id
            )
            
            # Store relationship in graph
            if self._graph_db:
                await self.store_relationship(
                    user_id,
                    project_id,
                    "COLLABORATES_ON",
                    {
                        "role": role.value,
                        "permissions": permissions,
                        "added_at": datetime.now().isoformat()
                    }
                )
            
            # Log activity
            await self._log_activity(
                project_id,
                context.user_id,
                "collaborator_added",
                f"User {user_id} added as {role.value}",
                "collaborator",
                user_id,
                {"role": role.value, "permissions": permissions},
                context
            )
            
            # Publish event
            self.event_publisher.publish_project_event(
                "collaborator_added",
                project_id,
                {
                    "user_id": user_id,
                    "role": role.value,
                    "added_by": context.user_id
                },
                context.user_id,
                {"operation": "add_collaborator", "service": "user-service"}
            )
            
            await self.publish(
                "collaborator_added",
                {
                    "project_id": project_id,
                    "user_id": user_id,
                    "role": role.value,
                    "added_by": context.user_id
                },
                context
            )
            
            return collaborator
        
        return await self.execute_with_context(
            "add_collaborator",
            context,
            _add_collaborator_operation
        )
    
    # AI Analytics dan Insights
    async def generate_project_analytics(
        self, 
        project_id: str, 
        context: ServiceContext
    ) -> ServiceResult[Dict[str, Any]]:
        """Generate comprehensive project analytics dengan AI insights"""
        
        async def _generate_analytics_operation():
            # Check access
            has_access = await self._check_project_access(project_id, context.user_id, "read")
            if not has_access:
                raise PermissionError("Access denied to project analytics")
            
            # Try cache first
            cached_analytics = await self.get_cached(
                f"analytics:{project_id}",
                context.tenant_id
            )
            if cached_analytics:
                return cached_analytics
            
            # Get project
            project_result = await self.get_project(project_id, context)
            if not project_result.success:
                raise ValueError("Project not found")
            
            project = project_result.data
            
            # Calculate basic metrics
            analytics = {
                "project_id": project_id,
                "basic_metrics": {
                    "completion_percentage": project.completion_percentage,
                    "total_cost": project.total_cost,
                    "days_since_creation": (datetime.now() - project.created_at).days,
                    "status": project.status.value,
                    "priority": project.priority.value
                },
                "collaboration_metrics": await self._calculate_collaboration_metrics(project_id),
                "activity_metrics": await self._calculate_activity_metrics(project_id),
                "ai_insights": await self._generate_ai_insights(project, context),
                "generated_at": datetime.now().isoformat()
            }
            
            # Cache analytics
            await self.set_cached(
                f"analytics:{project_id}",
                analytics,
                self.analytics_cache_ttl,
                context.tenant_id
            )
            
            return analytics
        
        return await self.execute_with_context(
            "view_analytics",
            context,
            _generate_analytics_operation
        )
    
    # Helper Methods
    async def _check_project_access(self, project_id: str, user_id: str, access_type: str) -> bool:
        """Check if user has access to project"""
        try:
            collaborator = await self._get_collaborator(project_id, user_id)
            if not collaborator:
                return False
            
            # Role-based access control
            role_permissions = {
                "owner": ["read", "write", "admin", "delete"],
                "admin": ["read", "write", "admin"],
                "contributor": ["read", "write"],
                "viewer": ["read"]
            }
            
            allowed_access = role_permissions.get(collaborator.role.value, [])
            return access_type in allowed_access
            
        except Exception:
            return False
    
    async def _get_collaborator(self, project_id: str, user_id: str) -> Optional[ProjectCollaborator]:
        """Get project collaborator"""
        try:
            # Try cache first
            cached = await self.get_cached(f"collaborator:{project_id}:{user_id}")
            if cached:
                return cached
            
            # Get from database
            async with await self.get_db_connection() as conn:
                record = await conn.fetchrow("""
                    SELECT user_id, project_id, role, permissions, added_by, added_at, last_active
                    FROM project_collaborators 
                    WHERE project_id = $1 AND user_id = $2
                """, project_id, user_id)
                
                if record:
                    return ProjectCollaborator(
                        user_id=record["user_id"],
                        project_id=record["project_id"],
                        role=CollaboratorRole(record["role"]),
                        permissions=record["permissions"],
                        added_by=record["added_by"],
                        added_at=record["added_at"],
                        last_active=record["last_active"]
                    )
            
            return None
            
        except Exception:
            return None
    
    async def _log_activity(
        self, 
        project_id: str, 
        user_id: str, 
        action: str, 
        description: str,
        entity_type: str, 
        entity_id: Optional[str], 
        changes: Dict[str, Any], 
        context: ServiceContext
    ):
        """Log project activity"""
        try:
            activity_id = str(uuid.uuid4())
            
            activity = ProjectActivity(
                activity_id=activity_id,
                project_id=project_id,
                user_id=user_id,
                action=action,
                description=description,
                entity_type=entity_type,
                entity_id=entity_id,
                changes=changes,
                timestamp=datetime.now(),
                metadata={}
            )
            
            # Store in database
            async with await self.get_db_connection() as conn:
                await conn.execute("""
                    INSERT INTO project_activities (
                        activity_id, project_id, user_id, action, description,
                        entity_type, entity_id, changes, timestamp, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """, 
                activity_id, project_id, user_id, action, description,
                entity_type, entity_id, changes, datetime.now(), {})
            
            # Cache recent activity
            await self.set_cached(
                f"activity:{activity_id}",
                activity,
                self.activity_cache_ttl,
                context.tenant_id
            )
            
        except Exception as e:
            self.logger.error(f"Failed to log activity: {e}")
    
    async def _generate_project_embedding(self, project: Project) -> List[float]:
        """Generate embedding untuk project"""
        text = f"{project.name} {project.description} {' '.join(project.tags)} {project.priority.value}"
        
        # Mock embedding implementation
        import hashlib
        hash_object = hashlib.md5(text.encode())
        hash_hex = hash_object.hexdigest()
        
        embedding = []
        for i in range(0, len(hash_hex), 2):
            val = int(hash_hex[i:i+2], 16) / 255.0
            embedding.append(val)
        
        while len(embedding) < 784:
            embedding.append(0.0)
        
        return embedding[:784]
    
    async def _generate_project_insights(self, project: Project, context: ServiceContext):
        """Generate AI insights untuk project"""
        try:
            if not project.settings.ai_features_enabled:
                return
            
            # Generate insights menggunakan AI services (mock implementation)
            insights = {
                "completion_prediction": {
                    "estimated_completion_date": (datetime.now() + timedelta(days=30)).isoformat(),
                    "confidence": 0.75,
                    "factors": ["current_progress", "team_size", "complexity"]
                },
                "risk_assessment": {
                    "risk_level": "medium",
                    "potential_issues": ["timeline_pressure", "resource_constraints"],
                    "recommendations": ["increase_team_size", "adjust_timeline"]
                },
                "optimization_suggestions": [
                    "Consider using AI automation for repetitive tasks",
                    "Implement better collaboration workflows",
                    "Schedule regular progress reviews"
                ],
                "generated_at": datetime.now().isoformat()
            }
            
            # Update project dengan insights
            async with await self.get_db_connection() as conn:
                await conn.execute("""
                    UPDATE projects 
                    SET ai_insights = $1, updated_at = NOW()
                    WHERE project_id = $2
                """, insights, project.project_id)
            
            # Invalidate project cache
            await self.invalidate_cache(f"project:{project.project_id}", context.tenant_id)
            
        except Exception as e:
            self.logger.error(f"Failed to generate project insights: {e}")
    
    async def _calculate_collaboration_metrics(self, project_id: str) -> Dict[str, Any]:
        """Calculate collaboration metrics"""
        try:
            async with await self.get_db_connection() as conn:
                # Count collaborators
                collaborator_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM project_collaborators WHERE project_id = $1
                """, project_id)
                
                # Get role distribution
                role_distribution = await conn.fetch("""
                    SELECT role, COUNT(*) as count 
                    FROM project_collaborators 
                    WHERE project_id = $1 
                    GROUP BY role
                """, project_id)
                
                return {
                    "total_collaborators": collaborator_count,
                    "role_distribution": {row["role"]: row["count"] for row in role_distribution},
                    "active_collaborators_last_week": 0  # Would implement based on activity
                }
                
        except Exception as e:
            self.logger.error(f"Failed to calculate collaboration metrics: {e}")
            return {}
    
    async def _calculate_activity_metrics(self, project_id: str) -> Dict[str, Any]:
        """Calculate activity metrics"""
        try:
            async with await self.get_db_connection() as conn:
                # Activity counts
                total_activities = await conn.fetchval("""
                    SELECT COUNT(*) FROM project_activities WHERE project_id = $1
                """, project_id)
                
                recent_activities = await conn.fetchval("""
                    SELECT COUNT(*) FROM project_activities 
                    WHERE project_id = $1 AND timestamp > NOW() - INTERVAL '7 days'
                """, project_id)
                
                return {
                    "total_activities": total_activities,
                    "activities_last_week": recent_activities,
                    "activity_trend": "increasing" if recent_activities > 10 else "stable"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to calculate activity metrics: {e}")
            return {}
    
    async def _generate_ai_insights(self, project: Project, context: ServiceContext) -> Dict[str, Any]:
        """Generate AI-powered insights"""
        try:
            # Mock AI insights implementation
            return {
                "completion_forecast": {
                    "predicted_date": (datetime.now() + timedelta(days=45)).isoformat(),
                    "confidence": 0.82,
                    "methodology": "ml_regression_model"
                },
                "performance_score": 7.5,
                "bottlenecks": ["resource_allocation", "dependencies"],
                "recommendations": [
                    "Implement automated testing to reduce manual QA time",
                    "Consider parallel development tracks for independent features"
                ],
                "cost_optimization": {
                    "potential_savings": 250.0,
                    "suggestions": ["optimize_ai_model_usage", "batch_processing"]
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate AI insights: {e}")
            return {}