"""
🚀 AI Orchestration API Endpoints - Microservice Implementation
Enterprise-grade API endpoints for AI orchestration with Handit AI, Letta, LangGraph, and Langfuse integration

CENTRALIZED INFRASTRUCTURE:
- Performance tracking untuk API operations
- Centralized error handling untuk API responses
- Event publishing untuk API lifecycle monitoring
- Enhanced logging dengan API-specific configuration
- Comprehensive validation untuk API requests
- Advanced metrics tracking untuk API performance optimization
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query, Path, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

# SERVICE-SPECIFIC CENTRALIZED INFRASTRUCTURE
from ...shared.infrastructure.core.logger_core import CoreLogger
from ...shared.infrastructure.core.error_core import CoreErrorHandler
from ...shared.infrastructure.base.base_performance import BasePerformance
from ...shared.infrastructure.core.performance_core import performance_tracked, CorePerformance
from ...shared.infrastructure.core.config_core import CoreConfig
from ...shared.infrastructure.optional.event_core import CoreEventManager
from ...shared.infrastructure.optional.validation_core import SharedInfraValidationManager
from ...shared.infrastructure.core.response_core import CoreResponse

# AI ORCHESTRATION COMPONENTS
from ..business.handit_client import (
    AIOrchestrationHanditClient, get_handit_microservice,
    TaskType, ModelSpecialty, TaskPriority, TaskStatus
)

# Enhanced logger for API endpoints
api_logger = CoreLogger("ai-orchestration", "api_endpoints")

# API performance metrics
api_metrics = {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "avg_response_time_ms": 0,
    "total_response_time_ms": 0,
    "events_published": 0,
    "validation_errors": 0,
    "concurrent_requests_peak": 0,
    "health_checks": 0
}

# FastAPI router for AI orchestration
router = APIRouter(prefix="/api/v1/ai-orchestration", tags=["AI Orchestration"])


# PYDANTIC MODELS FOR API

class TaskRequest(BaseModel):
    """Request model for creating AI tasks"""
    task_type: str = Field(..., description="Type of AI task to perform")
    specialty: str = Field(..., description="Model specialty to use")
    input_data: Dict[str, Any] = Field(..., description="Input data for the task")
    priority: int = Field(default=2, ge=1, le=5, description="Task priority (1=LOW, 5=CRITICAL)")
    timeout: int = Field(default=30, ge=5, le=300, description="Task timeout in seconds")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    
    @validator('task_type')
    def validate_task_type(cls, v):
        try:
            TaskType(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid task_type. Must be one of: {[t.value for t in TaskType]}")
    
    @validator('specialty')
    def validate_specialty(cls, v):
        try:
            ModelSpecialty(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid specialty. Must be one of: {[s.value for s in ModelSpecialty]}")


class TaskResponse(BaseModel):
    """Response model for AI tasks"""
    task_id: str
    status: str
    task_type: str
    specialty: str
    priority: int
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    processing_time_ms: float = 0.0
    result: Optional[Dict[str, Any]] = None
    confidence: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}


class HealthResponse(BaseModel):
    """Response model for health check"""
    service: str
    status: str
    uptime_seconds: float
    microservice_version: str
    handit_available: bool
    client_initialized: bool
    metrics: Dict[str, Any]
    config: Dict[str, Any]
    models: Dict[str, Any]
    timestamp: str


class MetricsResponse(BaseModel):
    """Response model for metrics"""
    api_metrics: Dict[str, Any]
    ai_orchestration_handit_metrics: Dict[str, Any]
    microservice_stats: Dict[str, Any]
    timestamp: str


# DEPENDENCY FOR HANDIT AI MICROSERVICE

def get_handit_client() -> AIOrchestrationHanditClient:
    """Dependency to get Handit AI microservice client"""
    return get_handit_microservice()


# API ENDPOINTS

@router.post("/tasks", response_model=TaskResponse, status_code=201)
async def create_ai_task(
    task_request: TaskRequest,
    background_tasks: BackgroundTasks,
    handit_client: AIOrchestrationHanditClient = Depends(get_handit_client)
) -> TaskResponse:
    """
    Create a new AI task dengan FULL CENTRALIZATION
    Enterprise-grade task creation with comprehensive validation and monitoring
    """
    start_time = time.perf_counter()
    
    try:
        # Update API metrics
        api_metrics["total_requests"] += 1
        
        # Enhanced validation
        validator = SharedInfraValidationManager("ai-orchestration")
        required_fields = ["task_type", "specialty", "input_data"]
        request_data = task_request.dict()
        
        # Simple validation - check required fields exist
        validation_passed = all(field in request_data and request_data[field] is not None for field in required_fields)
        
        if not validation_passed:
            api_metrics["validation_errors"] += 1
            api_metrics["failed_requests"] += 1
            
            error_handler = CoreErrorHandler("ai-orchestration")
            error_response = error_handler.handle_service_error(
                error=ValueError(f"Invalid request: missing required fields"),
                operation="create_task",
                context={"request_data": request_data}
            )
            
            raise HTTPException(
                status_code=400,
                detail=f"Validation failed: missing required fields {required_fields}"
            )
        
        # Create AI task
        task_id = await handit_client.create_task(
            task_type=TaskType(task_request.task_type),
            specialty=ModelSpecialty(task_request.specialty),
            input_data=task_request.input_data,
            priority=TaskPriority(task_request.priority),
            timeout=task_request.timeout,
            metadata=task_request.metadata
        )
        
        # Get task details
        task = handit_client.active_tasks.get(task_id)
        if not task:
            raise HTTPException(status_code=500, detail="Failed to create task")
        
        # Calculate response time
        response_time = (time.perf_counter() - start_time) * 1000
        
        # Update API metrics
        api_metrics["successful_requests"] += 1
        api_metrics["total_response_time_ms"] += response_time
        if api_metrics["successful_requests"] > 0:
            api_metrics["avg_response_time_ms"] = (
                api_metrics["total_response_time_ms"] / api_metrics["successful_requests"]
            )
        
        # Record performance metrics
        performance_tracker = BasePerformance("ai-orchestration")
        performance_tracker.record_metric(
            operation="create_ai_task_endpoint",
            duration_ms=response_time,
            success=True,
            metadata={
                "task_type": task_request.task_type,
                "specialty": task_request.specialty,
                "priority": task_request.priority,
                "service": "ai-orchestration"
            }
        )
        
        # Publish API event
        event_manager = CoreEventManager("ai-orchestration")
        event_manager.publish_event(
            event_type="ai_task_created_via_api",
            component="api_endpoints",
            message=f"AI task created via API: {task_request.task_type}",
            data={
                "task_id": task_id,
                "task_type": task_request.task_type,
                "specialty": task_request.specialty,
                "response_time_ms": response_time,
                "api_endpoint": "/tasks"
            }
        )
        api_metrics["events_published"] += 1
        
        # Create response
        response = TaskResponse(
            task_id=task.id,
            status=task.status.value,
            task_type=task.task_type.value,
            specialty=task.specialty.value,
            priority=task.priority.value,
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            processing_time_ms=task.processing_time_ms,
            metadata=task.metadata
        )
        
        api_logger.info(f"✅ Created AI task via API: {task_id} ({response_time:.2f}ms)")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        # Handle task creation failure
        response_time = (time.perf_counter() - start_time) * 1000
        api_metrics["failed_requests"] += 1
        
        error_handler = CoreErrorHandler("ai-orchestration")
        error_response = error_handler.handle_service_error(
            error=e,
            operation="create_task",
            context={"request_data": task_request.dict()}
        )
        
        api_logger.error(f"❌ Failed to create AI task via API: {error_response}")
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_ai_task(
    task_id: str = Path(..., description="Task ID to retrieve"),
    handit_client: AIOrchestrationHanditClient = Depends(get_handit_client)
) -> TaskResponse:
    """
    Get AI task status and results dengan FULL CENTRALIZATION
    Enterprise-grade task retrieval with comprehensive monitoring
    """
    start_time = time.perf_counter()
    
    try:
        # Update API metrics
        api_metrics["total_requests"] += 1
        
        # Get task from active tasks
        task = handit_client.active_tasks.get(task_id)
        if not task:
            # Check completed tasks
            response = handit_client.completed_tasks.get(task_id)
            if response:
                # Calculate response time
                response_time = (time.perf_counter() - start_time) * 1000
                api_metrics["successful_requests"] += 1
                
                return TaskResponse(
                    task_id=response.task_id,
                    status=response.status.value,
                    task_type="unknown",  # Not stored in response
                    specialty="unknown",  # Not stored in response
                    priority=2,  # Default
                    created_at="",  # Not stored in response
                    result=response.result,
                    confidence=response.confidence,
                    processing_time_ms=response.processing_time_ms,
                    error=response.error,
                    metadata=response.metadata
                )
            
            api_metrics["failed_requests"] += 1
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        # Calculate response time
        response_time = (time.perf_counter() - start_time) * 1000
        api_metrics["successful_requests"] += 1
        
        # Create response
        response = TaskResponse(
            task_id=task.id,
            status=task.status.value,
            task_type=task.task_type.value,
            specialty=task.specialty.value,
            priority=task.priority.value,
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            processing_time_ms=task.processing_time_ms,
            metadata=task.metadata
        )
        
        api_logger.info(f"📋 Retrieved AI task via API: {task_id} ({response_time:.2f}ms)")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        response_time = (time.perf_counter() - start_time) * 1000
        api_metrics["failed_requests"] += 1
        
        error_handler = CoreErrorHandler("ai-orchestration")
        error_response = error_handler.handle_service_error(
            error=e,
            operation="get_task",
            context={"task_id": task_id}
        )
        
        api_logger.error(f"❌ Failed to get AI task via API: {error_response}")
        raise HTTPException(status_code=500, detail=f"Failed to get task: {str(e)}")


@router.get("/tasks", response_model=List[TaskResponse])
async def list_ai_tasks(
    status: Optional[str] = Query(None, description="Filter by task status"),
    task_type: Optional[str] = Query(None, description="Filter by task type"),
    limit: int = Query(default=50, ge=1, le=1000, description="Maximum number of tasks to return"),
    handit_client: AIOrchestrationHanditClient = Depends(get_handit_client)
) -> List[TaskResponse]:
    """
    List AI tasks with filtering dengan FULL CENTRALIZATION
    Enterprise-grade task listing with comprehensive filtering and monitoring
    """
    start_time = time.perf_counter()
    
    try:
        # Update API metrics
        api_metrics["total_requests"] += 1
        
        # Get all tasks (active + completed)
        all_tasks = []
        
        # Add active tasks
        for task in handit_client.active_tasks.values():
            if status and task.status.value != status:
                continue
            if task_type and task.task_type.value != task_type:
                continue
                
            all_tasks.append(TaskResponse(
                task_id=task.id,
                status=task.status.value,
                task_type=task.task_type.value,
                specialty=task.specialty.value,
                priority=task.priority.value,
                created_at=task.created_at,
                started_at=task.started_at,
                completed_at=task.completed_at,
                processing_time_ms=task.processing_time_ms,
                metadata=task.metadata
            ))
        
        # Limit results
        all_tasks = all_tasks[:limit]
        
        # Calculate response time
        response_time = (time.perf_counter() - start_time) * 1000
        api_metrics["successful_requests"] += 1
        
        api_logger.info(f"📋 Listed {len(all_tasks)} AI tasks via API ({response_time:.2f}ms)")
        return all_tasks
        
    except Exception as e:
        response_time = (time.perf_counter() - start_time) * 1000
        api_metrics["failed_requests"] += 1
        
        error_handler = CoreErrorHandler("ai-orchestration")
        error_response = error_handler.handle_service_error(
            error=e,
            operation="list_tasks",
            context={"status": status, "task_type": task_type, "limit": limit}
        )
        
        api_logger.error(f"❌ Failed to list AI tasks via API: {error_response}")
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {str(e)}")


@router.delete("/tasks/{task_id}", status_code=204)
async def cancel_ai_task(
    task_id: str = Path(..., description="Task ID to cancel"),
    handit_client: AIOrchestrationHanditClient = Depends(get_handit_client)
):
    """
    Cancel AI task dengan FULL CENTRALIZATION
    Enterprise-grade task cancellation with comprehensive monitoring
    """
    start_time = time.perf_counter()
    
    try:
        # Update API metrics
        api_metrics["total_requests"] += 1
        
        # Check if task exists and is active
        if task_id not in handit_client.active_tasks:
            api_metrics["failed_requests"] += 1
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found or not active")
        
        # Cancel task (remove from active tasks)
        task = handit_client.active_tasks.pop(task_id, None)
        if task:
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now().isoformat()
        
        # Remove from queue if present
        handit_client.task_queue = [t for t in handit_client.task_queue if t.id != task_id]
        
        # Calculate response time
        response_time = (time.perf_counter() - start_time) * 1000
        api_metrics["successful_requests"] += 1
        
        # Publish cancellation event
        event_manager = CoreEventManager("ai-orchestration")
        event_manager.publish_event(
            event_type="ai_task_cancelled_via_api",
            component="api_endpoints",
            message=f"AI task cancelled via API: {task_id}",
            data={
                "task_id": task_id,
                "response_time_ms": response_time,
                "api_endpoint": f"/tasks/{task_id}"
            }
        )
        api_metrics["events_published"] += 1
        
        api_logger.info(f"❌ Cancelled AI task via API: {task_id} ({response_time:.2f}ms)")
        
    except HTTPException:
        raise
    except Exception as e:
        response_time = (time.perf_counter() - start_time) * 1000
        api_metrics["failed_requests"] += 1
        
        error_handler = CoreErrorHandler("ai-orchestration")
        error_response = error_handler.handle_service_error(
            error=e,
            operation="cancel_task",
            context={"task_id": task_id}
        )
        
        api_logger.error(f"❌ Failed to cancel AI task via API: {error_response}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")


@router.get("/health", response_model=HealthResponse)
async def health_check(
    handit_client: AIOrchestrationHanditClient = Depends(get_handit_client)
) -> HealthResponse:
    """
    Health check for AI orchestration microservice dengan FULL CENTRALIZATION
    Enterprise-grade health monitoring with comprehensive metrics
    """
    start_time = time.perf_counter()
    
    try:
        # Update API metrics
        api_metrics["total_requests"] += 1
        api_metrics["health_checks"] += 1
        
        # Get health status from Handit client
        health_data = handit_client.get_enhanced_health_status()
        
        # Calculate response time
        response_time = (time.perf_counter() - start_time) * 1000
        api_metrics["successful_requests"] += 1
        
        # Create enhanced health response
        response = HealthResponse(
            service=health_data["service"],
            status=health_data["status"],
            uptime_seconds=health_data["uptime_seconds"],
            microservice_version=health_data.get("microservice_version", "2.0.0"),
            handit_available=health_data["handit_available"],
            client_initialized=health_data["client_initialized"],
            metrics=health_data["metrics"],
            config=health_data["config"],
            models=health_data["models"],
            timestamp=health_data["timestamp"]
        )
        
        api_logger.debug(f"✅ Health check completed ({response_time:.2f}ms)")
        return response
        
    except Exception as e:
        response_time = (time.perf_counter() - start_time) * 1000
        api_metrics["failed_requests"] += 1
        
        error_handler = CoreErrorHandler("ai-orchestration")
        error_response = error_handler.handle_service_error(
            error=e,
            operation="health_check",
            context={}
        )
        
        api_logger.error(f"❌ Health check failed: {error_response}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    handit_client: AIOrchestrationHanditClient = Depends(get_handit_client)
) -> MetricsResponse:
    """
    Get comprehensive metrics untuk AI orchestration microservice dengan CENTRALIZATION
    Enterprise-grade metrics collection with detailed performance data
    """
    start_time = time.perf_counter()
    
    try:
        # Update API metrics
        api_metrics["total_requests"] += 1
        
        # Get Handit metrics (import from handit_client module)
        from ..business.handit_client import ai_orchestration_handit_metrics
        
        # Calculate response time
        response_time = (time.perf_counter() - start_time) * 1000
        api_metrics["successful_requests"] += 1
        
        # Create metrics response
        response = MetricsResponse(
            api_metrics=api_metrics.copy(),
            ai_orchestration_handit_metrics=ai_orchestration_handit_metrics.copy(),
            microservice_stats=handit_client.microservice_stats.copy(),
            timestamp=datetime.now().isoformat()
        )
        
        api_logger.debug(f"📊 Metrics retrieved ({response_time:.2f}ms)")
        return response
        
    except Exception as e:
        response_time = (time.perf_counter() - start_time) * 1000
        api_metrics["failed_requests"] += 1
        
        error_handler = CoreErrorHandler("ai-orchestration")
        error_response = error_handler.handle_service_error(
            error=e,
            operation="get_metrics",
            context={}
        )
        
        api_logger.error(f"❌ Failed to get metrics: {error_response}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/models", response_model=Dict[str, List[str]])
async def get_available_models(
    handit_client: AIOrchestrationHanditClient = Depends(get_handit_client)
) -> Dict[str, List[str]]:
    """
    Get available AI models and specialties dengan FULL CENTRALIZATION
    Enterprise-grade model discovery with comprehensive information
    """
    start_time = time.perf_counter()
    
    try:
        # Update API metrics
        api_metrics["total_requests"] += 1
        
        # Calculate response time
        response_time = (time.perf_counter() - start_time) * 1000
        api_metrics["successful_requests"] += 1
        
        # Create models response
        response = {
            "task_types": [task_type.value for task_type in TaskType],
            "model_specialties": [specialty.value for specialty in ModelSpecialty],
            "available_models": list(handit_client.models.values()),
            "task_priorities": [priority.name for priority in TaskPriority],
            "task_statuses": [status.value for status in TaskStatus]
        }
        
        api_logger.debug(f"🤖 Models list retrieved ({response_time:.2f}ms)")
        return response
        
    except Exception as e:
        response_time = (time.perf_counter() - start_time) * 1000
        api_metrics["failed_requests"] += 1
        
        error_handler = CoreErrorHandler("ai-orchestration")
        error_response = error_handler.handle_service_error(
            error=e,
            operation="get_models",
            context={}
        )
        
        api_logger.error(f"❌ Failed to get models: {error_response}")
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")


# STARTUP EVENT

@router.on_event("startup")
async def startup_event():
    """Startup event for AI orchestration API"""
    try:
        # Publish API startup event
        event_manager = CoreEventManager("ai-orchestration")
        event_manager.publish_event(
            event_type="api_startup",
            component="api_endpoints",
            message="AI orchestration API microservice started",
            data={
                "api_version": "2.0.0",
                "service": "ai-orchestration",
                "startup_timestamp": time.time()
            }
        )
        api_metrics["events_published"] += 1
        
        api_logger.info("🚀 AI Orchestration API microservice started successfully")
        
    except Exception as e:
        error_handler = CoreErrorHandler("ai-orchestration")
        error_response = error_handler.handle_service_error(
            error=e,
            operation="startup",
            context={}
        )
        api_logger.error(f"❌ Failed to start API: {error_response}")


# SHUTDOWN EVENT

@router.on_event("shutdown")
async def shutdown_event():
    """Shutdown event for AI orchestration API"""
    try:
        # Publish API shutdown event
        event_manager = CoreEventManager("ai-orchestration")
        event_manager.publish_event(
            event_type="api_shutdown",
            component="api_endpoints",
            message="AI orchestration API microservice shutting down",
            data={
                "final_metrics": api_metrics.copy(),
                "shutdown_timestamp": time.time()
            }
        )
        
        api_logger.info("🛑 AI Orchestration API microservice shutdown complete")
        
    except Exception as e:
        api_logger.error(f"❌ Error during API shutdown: {str(e)}")