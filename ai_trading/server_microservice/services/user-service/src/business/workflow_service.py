"""
User Service - AI Workflow Management
Enterprise-grade AI workflow orchestration dengan LangGraph, Letta, LiteLLM, Handit AI, dan Langfuse
Migrated from server_side with per-service infrastructure patterns
"""

import os
import uuid
import json
import hashlib
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

# PER-SERVICE INFRASTRUCTURE INTEGRATION
from ....shared.infrastructure.base.base_error_handler import BaseErrorHandler, ErrorCategory
from ....shared.infrastructure.base.base_performance import BasePerformance
from .base_domain_service import BaseDomainService, ServiceResult, ServiceContext

class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class WorkflowPriority(Enum):
    """Workflow execution priority"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class WorkflowTemplate:
    """AI workflow template definition"""
    template_id: str
    name: str
    description: str
    category: str
    ai_services: List[str]  # LangGraph, Letta, LiteLLM, etc.
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    steps: List[Dict[str, Any]]
    estimated_cost: float
    estimated_duration: int  # seconds
    tags: List[str]
    created_by: str
    created_at: datetime
    is_active: bool

@dataclass
class WorkflowExecution:
    """AI workflow execution instance"""
    execution_id: str
    template_id: str
    user_id: str
    tenant_id: Optional[str]
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    status: WorkflowStatus
    priority: WorkflowPriority
    progress: float  # 0.0 to 1.0
    current_step: int
    total_steps: int
    execution_log: List[Dict[str, Any]]
    ai_service_calls: List[Dict[str, Any]]
    cost_incurred: float
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    metadata: Dict[str, Any]

@dataclass
class WorkflowRequest:
    """Workflow execution request"""
    template_id: str
    input_data: Dict[str, Any]
    priority: WorkflowPriority = WorkflowPriority.NORMAL
    max_cost: Optional[float] = None
    timeout_seconds: Optional[int] = None
    callback_url: Optional[str] = None
    metadata: Dict[str, Any] = None

# Mock AI Service Types - in production these would be separate service clients
class ServiceType(Enum):
    LANGGRAPH = "langgraph"
    LETTA = "letta" 
    HANDIT_AI = "handit_ai"
    LITELLM = "litellm"
    LANGFUSE = "langfuse"
    ORCHESTRATION = "orchestration"
    MEMORY_SYSTEM = "memory_system"
    QUALITY_ANALYZER = "quality_analyzer"
    MODEL_ROUTER = "model_router"
    OBSERVABILITY = "observability"

@dataclass
class ServiceConfig:
    """AI service configuration"""
    service_type: ServiceType
    service_name: str
    enabled: bool = True
    api_key: Optional[str] = None
    cost_optimization_enabled: bool = False
    memory_manager_enabled: bool = False
    provider_management_enabled: bool = False

@dataclass 
class ServiceRequest:
    """AI service request"""
    request_id: str
    service_type: ServiceType
    action: str
    payload: Dict[str, Any]

@dataclass
class ServiceResponse:
    """AI service response"""
    status: str
    result: Dict[str, Any]
    error: Optional[str] = None
    cost_estimate: float = 0.0
    tokens_used: int = 0
    provider_used: Optional[str] = None

class AIWorkflowService(BaseDomainService):
    """
    Enterprise AI Workflow Service dengan:
    - Multi-AI service orchestration (LangGraph, Letta, LiteLLM, Handit AI, Langfuse)
    - Workflow templates dan versioning
    - Cost tracking dan optimization
    - Real-time execution monitoring
    - Multi-tenant isolation
    - Event streaming untuk workflow events
    
    MIGRATED TO MICROSERVICE ARCHITECTURE with per-service infrastructure
    """
    
    def __init__(self):
        super().__init__("ai_workflow_orchestration")
    
    async def _initialize_service(self):
        """Initialize AI workflow service with per-service infrastructure"""
        try:
            # Cache configurations for AI workflow service
            self.template_cache_ttl = 7200  # 2 hours
            self.execution_cache_ttl = 3600  # 1 hour
            self.ai_service_cache_ttl = 1800  # 30 minutes
            
            # AI service instances - mock implementations for demonstration
            self.ai_services = {}
            
            # Initialize AI services
            await self._initialize_ai_services()
            
            # Workflow execution queue
            self.execution_queue = {}  # execution_id -> WorkflowExecution
            
            # Publish service initialization event using per-service event publisher
            self.event_publisher.publish(
                "ai_workflow_service_initialized",
                {
                    "service": "user-service",
                    "component": "ai_workflow_service",
                    "cache_ttl_config": {
                        "template": self.template_cache_ttl,
                        "execution": self.execution_cache_ttl,
                        "ai_service": self.ai_service_cache_ttl
                    },
                    "ai_services_count": len(self.ai_services)
                }
            )
            
            self.logger.info("AIWorkflowService initialized with full AI stack integration", extra={
                "ai_services_count": len(self.ai_services),
                "cache_configs": {
                    "template_ttl": self.template_cache_ttl,
                    "execution_ttl": self.execution_cache_ttl,
                    "ai_service_ttl": self.ai_service_cache_ttl
                }
            })
        except Exception as e:
            error_response = self.error_handler.handle_error(
                e,
                ErrorCategory.SERVICE_ERROR,
                {"operation": "initialize_ai_workflow_service", "service": "user-service"}
            )
            self.logger.error(f"Failed to initialize AI workflow service: {e}", extra={"error_response": error_response.to_dict()})
            raise
    
    async def _initialize_ai_services(self):
        """Initialize all AI service adapters - mock implementations"""
        try:
            # Service configurations for AI workflow orchestration
            service_configs = {
                "langgraph_orchestrator": ServiceConfig(
                    service_type=ServiceType.LANGGRAPH,
                    service_name="langgraph_orchestrator",
                    enabled=True,
                    cost_optimization_enabled=True,
                    memory_manager_enabled=True,
                    provider_management_enabled=True
                ),
                "letta_memory": ServiceConfig(
                    service_type=ServiceType.LETTA,
                    service_name="letta_memory",
                    enabled=True,
                    memory_manager_enabled=True
                ),
                "handit_quality_analyzer": ServiceConfig(
                    service_type=ServiceType.HANDIT_AI,
                    service_name="handit_quality_analyzer",
                    api_key=os.getenv("HANDIT_API_KEY", ""),
                    enabled=True,
                    cost_optimization_enabled=True
                ),
                "litellm_router": ServiceConfig(
                    service_type=ServiceType.LITELLM,
                    service_name="litellm_router",
                    enabled=True,
                    cost_optimization_enabled=True,
                    provider_management_enabled=True
                ),
                "langfuse_observability": ServiceConfig(
                    service_type=ServiceType.LANGFUSE,
                    service_name="langfuse_observability",
                    api_key=os.getenv("LANGFUSE_SECRET_KEY", ""),
                    enabled=True
                )
            }
            
            # Initialize each service (mock implementations)
            for service_name, config in service_configs.items():
                try:
                    service = await self._create_ai_service(service_name, config)
                    self.ai_services[service_name] = service
                    self.logger.info(f"✅ AI service {service_name} initialized")
                except Exception as e:
                    self.logger.error(f"❌ Failed to initialize {service_name}: {e}")
            
            self.logger.info(f"Initialized {len(self.ai_services)} AI services")
            
        except Exception as e:
            self.logger.error(f"AI services initialization failed: {e}")
    
    async def _create_ai_service(self, service_name: str, config: ServiceConfig):
        """Create AI service client - mock implementation"""
        # Mock service implementation
        class MockAIService:
            def __init__(self, name: str, config: ServiceConfig):
                self.name = name
                self.config = config
            
            async def process_request(self, request: ServiceRequest) -> ServiceResponse:
                # Mock AI service response
                return ServiceResponse(
                    status="success",
                    result={
                        "service": self.name,
                        "action": request.action,
                        "processed_data": f"Mock AI processing result for {request.action}",
                        "timestamp": datetime.now().isoformat()
                    },
                    cost_estimate=0.01,  # Mock cost
                    tokens_used=100,     # Mock tokens
                    provider_used="mock_provider"
                )
        
        return MockAIService(service_name, config)
    
    def _get_required_permission(self, operation: str) -> Optional[str]:
        """Get required permission untuk workflow operations"""
        permission_map = {
            "create_template": "ai:workflow:create",
            "update_template": "ai:workflow:update",
            "delete_template": "ai:workflow:delete",
            "execute_workflow": "ai:workflow:execute",
            "view_execution": "ai:workflow:read",
            "cancel_execution": "ai:workflow:cancel",
            "list_templates": "ai:workflow:read",
            "list_executions": "ai:workflow:read"
        }
        return permission_map.get(operation)
    
    # Workflow Template Management
    async def create_workflow_template(
        self, 
        name: str,
        description: str,
        category: str,
        ai_services: List[str],
        input_schema: Dict[str, Any],
        output_schema: Dict[str, Any],
        steps: List[Dict[str, Any]],
        estimated_cost: float,
        estimated_duration: int,
        tags: List[str],
        context: ServiceContext
    ) -> ServiceResult[WorkflowTemplate]:
        """Create new workflow template with centralized validation and event publishing"""
        
        # User service specific validation
        if not name or len(name.strip()) == 0:
            error_response = self.error_handler.handle_validation_error(
                "name", name, "Template name is required and cannot be empty"
            )
            return ServiceResult.failure("Invalid template name", error_response.to_dict())
        
        if estimated_cost < 0 or estimated_duration < 0:
            error_response = self.error_handler.handle_validation_error(
                "cost_duration", f"cost:{estimated_cost}, duration:{estimated_duration}", "Cost and duration must be positive"
            )
            return ServiceResult.failure("Invalid cost or duration values", error_response.to_dict())
        
        async def _create_template_operation():
            template_id = str(uuid.uuid4())
            
            # Validate AI services
            invalid_services = [s for s in ai_services if s not in self.ai_services]
            if invalid_services:
                raise ValueError(f"Invalid AI services: {invalid_services}")
            
            # Validate steps
            if not steps or not isinstance(steps, list):
                raise ValueError("Steps must be a non-empty list")
            
            template = WorkflowTemplate(
                template_id=template_id,
                name=name,
                description=description,
                category=category,
                ai_services=ai_services,
                input_schema=input_schema,
                output_schema=output_schema,
                steps=steps,
                estimated_cost=estimated_cost,
                estimated_duration=estimated_duration,
                tags=tags,
                created_by=context.user_id,
                created_at=datetime.now(),
                is_active=True
            )
            
            # Store in database using per-service database connection
            async with await self.get_db_connection() as conn:
                await conn.execute("""
                    INSERT INTO workflow_templates (
                        template_id, name, description, category, ai_services,
                        input_schema, output_schema, steps, estimated_cost,
                        estimated_duration, tags, created_by, created_at, is_active,
                        tenant_id
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                """, 
                template_id, name, description, category, ai_services,
                input_schema, output_schema, steps, estimated_cost,
                estimated_duration, tags, context.user_id, datetime.now(), True,
                context.tenant_id)
            
            # Cache template using per-service cache
            await self.set_cached(
                f"template:{template_id}",
                template,
                self.template_cache_ttl,
                context.tenant_id
            )
            
            # Store template embedding untuk search (if vector DB enabled)
            if self._vector_db:
                template_embedding = await self._generate_template_embedding(template)
                await self.store_embedding(
                    "workflow_templates",
                    template_id,
                    template_embedding,
                    {
                        "name": name,
                        "description": description,
                        "category": category,
                        "ai_services": ai_services,
                        "tags": tags,
                        "tenant_id": context.tenant_id
                    }
                )
            
            # Store template relationships (if graph DB enabled)
            if self._graph_db:
                # Template -> User relationship
                await self.store_relationship(
                    template_id,
                    context.user_id,
                    "CREATED_BY",
                    {"created_at": datetime.now().isoformat()}
                )
                
                # Template -> AI Services relationships
                for service in ai_services:
                    await self.store_relationship(
                        template_id,
                        service,
                        "USES_SERVICE",
                        {"service_type": service}
                    )
            
            # Publish template created event using per-service event publisher
            self.event_publisher.publish_workflow_event(
                "workflow_template_created",
                template_id,
                {
                    "name": name,
                    "category": category,
                    "ai_services": ai_services,
                    "estimated_cost": estimated_cost,
                    "created_at": datetime.now().isoformat()
                },
                context.user_id,
                {"operation": "create_workflow_template", "service": "user-service"}
            )
            
            # Also publish to service event system for inter-service communication
            await self.publish(
                "template_created",
                {
                    "template_id": template_id,
                    "name": name,
                    "category": category,
                    "ai_services": ai_services,
                    "estimated_cost": estimated_cost
                },
                context
            )
            
            return template
        
        return await self.execute_with_context(
            "create_template",
            context,
            _create_template_operation
        )
    
    async def get_workflow_template(
        self, 
        template_id: str, 
        context: ServiceContext
    ) -> ServiceResult[WorkflowTemplate]:
        """Get workflow template dengan caching and validation"""
        
        # User service specific validation
        if not self._validate_uuid(template_id):
            error_response = self.error_handler.handle_validation_error(
                "template_id", template_id, "Invalid template ID format"
            )
            return ServiceResult.failure("Invalid template ID", error_response.to_dict())
        
        async def _get_template_operation():
            # Try cache first
            cached_template = await self.get_cached(
                f"template:{template_id}",
                context.tenant_id
            )
            if cached_template:
                return cached_template
            
            # Get from database
            async with await self.get_db_connection() as conn:
                record = await conn.fetchrow("""
                    SELECT template_id, name, description, category, ai_services,
                           input_schema, output_schema, steps, estimated_cost,
                           estimated_duration, tags, created_by, created_at, is_active
                    FROM workflow_templates 
                    WHERE template_id = $1 AND is_active = true
                """, template_id)
                
                if not record:
                    raise ValueError("Template not found")
                
                template = WorkflowTemplate(
                    template_id=record["template_id"],
                    name=record["name"],
                    description=record["description"],
                    category=record["category"],
                    ai_services=record["ai_services"],
                    input_schema=record["input_schema"],
                    output_schema=record["output_schema"],
                    steps=record["steps"],
                    estimated_cost=record["estimated_cost"],
                    estimated_duration=record["estimated_duration"],
                    tags=record["tags"],
                    created_by=record["created_by"],
                    created_at=record["created_at"],
                    is_active=record["is_active"]
                )
                
                # Cache template
                await self.set_cached(
                    f"template:{template_id}",
                    template,
                    self.template_cache_ttl,
                    context.tenant_id
                )
                
                return template
        
        return await self.execute_with_context(
            "list_templates",
            context,
            _get_template_operation
        )
    
    # Workflow Execution
    async def execute_workflow(
        self, 
        request: WorkflowRequest, 
        context: ServiceContext
    ) -> ServiceResult[WorkflowExecution]:
        """Execute AI workflow dengan full orchestration and validation"""
        
        # User service specific validation
        if not self._validate_uuid(request.template_id):
            error_response = self.error_handler.handle_validation_error(
                "template_id", request.template_id, "Invalid template ID format"
            )
            return ServiceResult.failure("Invalid template ID", error_response.to_dict())
        
        if not request.input_data:
            error_response = self.error_handler.handle_validation_error(
                "input_data", "empty", "Input data is required for workflow execution"
            )
            return ServiceResult.failure("Input data required", error_response.to_dict())
        
        async def _execute_workflow_operation():
            # Get workflow template
            template_result = await self.get_workflow_template(request.template_id, context)
            if not template_result.success:
                raise ValueError(f"Template not found: {request.template_id}")
            
            template = template_result.data
            
            # Check cost limits
            if request.max_cost and template.estimated_cost > request.max_cost:
                raise ValueError(f"Estimated cost {template.estimated_cost} exceeds limit {request.max_cost}")
            
            # Create execution instance
            execution_id = str(uuid.uuid4())
            execution = WorkflowExecution(
                execution_id=execution_id,
                template_id=request.template_id,
                user_id=context.user_id,
                tenant_id=context.tenant_id,
                input_data=request.input_data,
                output_data=None,
                status=WorkflowStatus.PENDING,
                priority=request.priority,
                progress=0.0,
                current_step=0,
                total_steps=len(template.steps),
                execution_log=[],
                ai_service_calls=[],
                cost_incurred=0.0,
                started_at=None,
                completed_at=None,
                error_message=None,
                metadata=request.metadata or {}
            )
            
            # Store execution in database
            async with await self.get_db_connection() as conn:
                await conn.execute("""
                    INSERT INTO workflow_executions (
                        execution_id, template_id, user_id, tenant_id, input_data,
                        status, priority, progress, current_step, total_steps,
                        execution_log, ai_service_calls, cost_incurred, metadata,
                        created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, NOW())
                """, 
                execution_id, request.template_id, context.user_id, context.tenant_id,
                request.input_data, execution.status.value, execution.priority.value,
                execution.progress, execution.current_step, execution.total_steps,
                execution.execution_log, execution.ai_service_calls, execution.cost_incurred,
                execution.metadata)
            
            # Cache execution
            await self.set_cached(
                f"execution:{execution_id}",
                execution,
                self.execution_cache_ttl,
                context.tenant_id
            )
            
            # Add to execution queue
            self.execution_queue[execution_id] = execution
            
            # Start workflow execution asynchronously
            await self._start_workflow_execution(execution, template, context)
            
            # Publish execution started event using per-service event publisher
            self.event_publisher.publish_workflow_event(
                "workflow_execution_started",
                execution_id,
                {
                    "template_id": request.template_id,
                    "estimated_cost": template.estimated_cost,
                    "priority": request.priority.value,
                    "started_at": datetime.now().isoformat()
                },
                context.user_id,
                {"operation": "execute_workflow", "service": "user-service"}
            )
            
            # Also publish to service event system for inter-service communication
            await self.publish(
                "workflow_started",
                {
                    "execution_id": execution_id,
                    "template_id": request.template_id,
                    "user_id": context.user_id,
                    "estimated_cost": template.estimated_cost,
                    "priority": request.priority.value
                },
                context
            )
            
            return execution
        
        return await self.execute_with_context(
            "execute_workflow",
            context,
            _execute_workflow_operation
        )
    
    async def _start_workflow_execution(
        self, 
        execution: WorkflowExecution, 
        template: WorkflowTemplate, 
        context: ServiceContext
    ):
        """Start actual workflow execution"""
        try:
            # Update execution status
            execution.status = WorkflowStatus.RUNNING
            execution.started_at = datetime.now()
            
            await self._update_execution_status(execution, context)
            
            # Execute workflow steps
            current_data = execution.input_data.copy()
            
            for step_index, step in enumerate(template.steps):
                execution.current_step = step_index + 1
                execution.progress = step_index / len(template.steps)
                
                # Log step start
                execution.execution_log.append({
                    "step": step_index + 1,
                    "action": "step_started",
                    "step_config": step,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Execute step
                step_result = await self._execute_workflow_step(step, current_data, execution, context)
                
                if not step_result["success"]:
                    execution.status = WorkflowStatus.FAILED
                    execution.error_message = step_result["error"]
                    execution.completed_at = datetime.now()
                    await self._update_execution_status(execution, context)
                    return
                
                # Update current data with step output
                current_data.update(step_result["output"])
                execution.cost_incurred += step_result.get("cost", 0.0)
                
                # Log step completion
                execution.execution_log.append({
                    "step": step_index + 1,
                    "action": "step_completed",
                    "output": step_result["output"],
                    "cost": step_result.get("cost", 0.0),
                    "timestamp": datetime.now().isoformat()
                })
                
                await self._update_execution_status(execution, context)
            
            # Workflow completed successfully
            execution.status = WorkflowStatus.COMPLETED
            execution.progress = 1.0
            execution.output_data = current_data
            execution.completed_at = datetime.now()
            
            await self._update_execution_status(execution, context)
            
            # Publish completion event using per-service event publisher
            self.event_publisher.publish_workflow_event(
                "workflow_execution_completed",
                execution.execution_id,
                {
                    "template_id": execution.template_id,
                    "cost_incurred": execution.cost_incurred,
                    "duration_seconds": (execution.completed_at - execution.started_at).total_seconds(),
                    "completed_at": datetime.now().isoformat()
                },
                execution.user_id,
                {"operation": "workflow_completed", "service": "user-service"}
            )
            
            # Also publish to service event system for inter-service communication
            await self.publish(
                "workflow_completed",
                {
                    "execution_id": execution.execution_id,
                    "template_id": execution.template_id,
                    "cost_incurred": execution.cost_incurred,
                    "duration_seconds": (execution.completed_at - execution.started_at).total_seconds()
                },
                context
            )
            
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.now()
            await self._update_execution_status(execution, context)
            
            self.logger.error(f"Workflow execution failed: {e}")
    
    async def _execute_workflow_step(
        self, 
        step: Dict[str, Any], 
        input_data: Dict[str, Any], 
        execution: WorkflowExecution,
        context: ServiceContext
    ) -> Dict[str, Any]:
        """Execute individual workflow step"""
        try:
            step_type = step.get("type")
            service_name = step.get("service")
            action = step.get("action")
            parameters = step.get("parameters", {})
            
            # Get AI service
            if service_name not in self.ai_services:
                return {
                    "success": False,
                    "error": f"AI service {service_name} not available"
                }
            
            service = self.ai_services[service_name]
            
            # Prepare service request
            service_request = ServiceRequest(
                request_id=str(uuid.uuid4()),
                service_type=self._get_service_type(service_name),
                action=action,
                payload={
                    **parameters,
                    **input_data,
                    "execution_id": execution.execution_id,
                    "user_id": context.user_id,
                    "tenant_id": context.tenant_id
                }
            )
            
            # Execute service call
            start_time = datetime.now()
            service_response = await service.process_request(service_request)
            end_time = datetime.now()
            
            # Log service call
            service_call = {
                "service": service_name,
                "action": action,
                "request_id": service_request.request_id,
                "status": service_response.status,
                "cost": service_response.cost_estimate,
                "tokens_used": service_response.tokens_used,
                "provider_used": service_response.provider_used,
                "duration_seconds": (end_time - start_time).total_seconds(),
                "timestamp": start_time.isoformat()
            }
            
            execution.ai_service_calls.append(service_call)
            
            if service_response.status == "success":
                return {
                    "success": True,
                    "output": service_response.result,
                    "cost": service_response.cost_estimate,
                    "service_call": service_call
                }
            else:
                return {
                    "success": False,
                    "error": service_response.error,
                    "service_call": service_call
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _update_execution_status(self, execution: WorkflowExecution, context: ServiceContext):
        """Update execution status in database and cache"""
        try:
            # Update database
            async with await self.get_db_connection() as conn:
                await conn.execute("""
                    UPDATE workflow_executions 
                    SET status = $1, progress = $2, current_step = $3, 
                        execution_log = $4, ai_service_calls = $5, cost_incurred = $6,
                        output_data = $7, started_at = $8, completed_at = $9,
                        error_message = $10, updated_at = NOW()
                    WHERE execution_id = $11
                """, 
                execution.status.value, execution.progress, execution.current_step,
                execution.execution_log, execution.ai_service_calls, execution.cost_incurred,
                execution.output_data, execution.started_at, execution.completed_at,
                execution.error_message, execution.execution_id)
            
            # Update cache
            await self.set_cached(
                f"execution:{execution.execution_id}",
                execution,
                self.execution_cache_ttl,
                context.tenant_id
            )
            
        except Exception as e:
            self.logger.error(f"Failed to update execution status: {e}")
    
    def _get_service_type(self, service_name: str) -> ServiceType:
        """Get service type enum untuk service name"""
        service_type_map = {
            "langgraph_orchestrator": ServiceType.ORCHESTRATION,
            "letta_memory": ServiceType.MEMORY_SYSTEM,
            "handit_quality_analyzer": ServiceType.QUALITY_ANALYZER,
            "litellm_router": ServiceType.MODEL_ROUTER,
            "langfuse_observability": ServiceType.OBSERVABILITY
        }
        return service_type_map.get(service_name, ServiceType.ORCHESTRATION)
    
    # Workflow Monitoring
    async def get_execution_status(
        self, 
        execution_id: str, 
        context: ServiceContext
    ) -> ServiceResult[WorkflowExecution]:
        """Get workflow execution status with validation"""
        
        # User service specific validation
        if not self._validate_uuid(execution_id):
            error_response = self.error_handler.handle_validation_error(
                "execution_id", execution_id, "Invalid execution ID format"
            )
            return ServiceResult.failure("Invalid execution ID", error_response.to_dict())
        
        async def _get_execution_operation():
            # Try cache first
            cached_execution = await self.get_cached(
                f"execution:{execution_id}",
                context.tenant_id
            )
            if cached_execution:
                return cached_execution
            
            # Get from database
            async with await self.get_db_connection() as conn:
                record = await conn.fetchrow("""
                    SELECT execution_id, template_id, user_id, tenant_id, input_data,
                           output_data, status, priority, progress, current_step,
                           total_steps, execution_log, ai_service_calls, cost_incurred,
                           started_at, completed_at, error_message, metadata, created_at
                    FROM workflow_executions 
                    WHERE execution_id = $1
                """, execution_id)
                
                if not record:
                    raise ValueError("Execution not found")
                
                execution = WorkflowExecution(
                    execution_id=record["execution_id"],
                    template_id=record["template_id"],
                    user_id=record["user_id"],
                    tenant_id=record["tenant_id"],
                    input_data=record["input_data"],
                    output_data=record["output_data"],
                    status=WorkflowStatus(record["status"]),
                    priority=WorkflowPriority(record["priority"]),
                    progress=record["progress"],
                    current_step=record["current_step"],
                    total_steps=record["total_steps"],
                    execution_log=record["execution_log"],
                    ai_service_calls=record["ai_service_calls"],
                    cost_incurred=record["cost_incurred"],
                    started_at=record["started_at"],
                    completed_at=record["completed_at"],
                    error_message=record["error_message"],
                    metadata=record["metadata"]
                )
                
                # Cache execution
                await self.set_cached(
                    f"execution:{execution_id}",
                    execution,
                    self.execution_cache_ttl,
                    context.tenant_id
                )
                
                return execution
        
        return await self.execute_with_context(
            "view_execution",
            context,
            _get_execution_operation
        )
    
    # Helper Methods
    async def _generate_template_embedding(self, template: WorkflowTemplate) -> List[float]:
        """Generate embedding untuk workflow template"""
        text = f"{template.name} {template.description} {' '.join(template.tags)} {template.category}"
        
        # Mock embedding (dalam production gunakan model seperti sentence-transformers)
        hash_object = hashlib.md5(text.encode())
        hash_hex = hash_object.hexdigest()
        
        # Convert hash to embedding vector (784 dimensions)
        embedding = []
        for i in range(0, len(hash_hex), 2):
            val = int(hash_hex[i:i+2], 16) / 255.0
            embedding.append(val)
        
        # Pad to 784 dimensions
        while len(embedding) < 784:
            embedding.append(0.0)
        
        return embedding[:784]
    
    def _validate_uuid(self, uuid_string: str) -> bool:
        """Validate UUID format - user service specific"""
        try:
            uuid.UUID(uuid_string)
            return True
        except ValueError:
            return False