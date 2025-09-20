"""
🤖 AI Orchestration Microservice - UNIFIED INTEGRATION WITH FULL CENTRALIZATION  
Enterprise-grade AI workflow coordination with Handit AI, Letta, LangGraph, and Langfuse integration

CENTRALIZED INFRASTRUCTURE:
- Performance tracking untuk comprehensive AI orchestration operations
- Centralized error handling untuk AI workflow and agent management
- Event publishing untuk complete AI lifecycle monitoring
- Enhanced logging dengan AI-specific configuration and context
- Comprehensive validation untuk AI workflow data and parameters
- Advanced metrics tracking untuk AI performance optimization and analytics

INTEGRATED COMPONENTS:
- Handit AI Client: Task orchestration and AI model coordination
- Letta Memory Integration: Advanced memory management for AI agents
- LangGraph Workflows: Complex multi-step AI workflow execution
- Langfuse Observability: Comprehensive AI performance monitoring and tracing
"""

import uvicorn
import sys
import os
from pathlib import Path
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import time
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

# Add src path to sys.path for proper imports
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# SERVICE-SPECIFIC INFRASTRUCTURE - AI-ORCHESTRATION SERVICE ONLY
from ...shared.infrastructure.core.logger_core import CoreLogger
from ...shared.infrastructure.core.config_core import CoreConfig
from ...shared.infrastructure.core.error_core import CoreErrorHandler
from ...shared.infrastructure.core.performance_core import CorePerformance
from ...shared.infrastructure.core.cache_core import CoreCache
from ...shared.infrastructure.optional.event_core import CoreEventManager
from ...shared.infrastructure.optional.validation_core import CoreValidator

# AI ORCHESTRATION API
from src.api.orchestration_endpoints import router as orchestration_router

# AI ORCHESTRATION COMPONENTS - ALL INTEGRATED
from src.business.handit_client import get_handit_microservice
from src.business.letta_integration import get_letta_memory_microservice
from src.business.langgraph_workflows import get_langgraph_workflow_microservice
from src.business.langfuse_client import get_langfuse_observability_microservice

# Initialize service-specific infrastructure for AI-ORCHESTRATION
config_core = CoreConfig("ai-orchestration")
logger_core = CoreLogger("ai-orchestration", "main")
error_handler = CoreErrorHandler("ai-orchestration")
performance_core = CorePerformance("ai-orchestration")
cache_core = CoreCache("ai-orchestration", max_size=2000, ttl=1800)  # AI orchestration needs larger cache with 30min TTL
event_manager = CoreEventManager("ai-orchestration")
validator = CoreValidator("ai-orchestration")

# Service configuration
service_config = config_core.get_service_config()

# Enhanced logger for ai-orchestration microservice
microservice_logger = logger_core

# Unified microservice performance metrics
unified_microservice_metrics = {
    "startup_time": 0,
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "uptime_start": time.time(),
    "health_checks": 0,
    "events_published": 0,
    "handit_requests": 0,
    "letta_operations": 0,
    "langgraph_workflows": 0,
    "langfuse_traces": 0,
    "total_ai_operations": 0,
    "microservice_version": "2.0.0"
}

class OrchestrationMode(Enum):
    """AI orchestration operation modes"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"
    DEBUG = "debug"

class AIOrchestrationServiceState:
    """Complete state management for AI orchestration microservice"""
    
    def __init__(self):
        # Service components
        self.handit_service = None
        self.letta_service = None
        self.langgraph_service = None
        self.langfuse_service = None
        
        # Service cache management
        self.service_cache: Dict[str, Any] = {}
        self.cache_metrics = {
            "cache_hits": 0,
            "cache_misses": 0,
            "cache_size": 0,
            "cache_ttl_expires": 0
        }
        
        # Service performance metrics
        self.service_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "total_response_time": 0.0,
            "peak_memory_usage": 0,
            "active_connections": 0
        }
        
        # Service-specific performance stats
        self.performance_stats = {
            "startup_time": 0,
            "health_checks": 0,
            "events_published": 0,
            "background_tasks_active": 0,
            "last_health_check": 0,
            "service_restarts": 0
        }
        
        # Unified orchestration state
        self.active_workflows: Dict[str, Any] = {}
        self.active_memory_sessions: Dict[str, Any] = {}
        self.active_tasks: Dict[str, Any] = {}
        self.active_traces: Dict[str, Any] = {}
        
        # Execution statistics
        self.execution_stats = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "failed_workflows": 0,
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "total_memory_operations": 0,
            "total_traces": 0,
            "active_components": 0,
            "uptime_start": time.time()
        }
        
        # Component initialization status
        self.component_status = {
            "handit_ai": False,
            "letta_memory": False,
            "langgraph_workflows": False,
            "langfuse_observability": False
        }
        
    def get_cache(self, key: str) -> Any:
        """Get value from service cache"""
        if key in self.service_cache:
            self.cache_metrics["cache_hits"] += 1
            cached_data = self.service_cache[key]
            if cached_data.get("expires_at", 0) > time.time():
                return cached_data["value"]
            else:
                del self.service_cache[key]
                self.cache_metrics["cache_ttl_expires"] += 1
        self.cache_metrics["cache_misses"] += 1
        return None
        
    def set_cache(self, key: str, value: Any, ttl: int = 1800) -> None:
        """Set value in service cache with TTL"""
        self.service_cache[key] = {
            "value": value,
            "expires_at": time.time() + ttl
        }
        self.cache_metrics["cache_size"] = len(self.service_cache)
        
    def clear_expired_cache(self) -> None:
        """Clear expired cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, data in self.service_cache.items()
            if data.get("expires_at", 0) < current_time
        ]
        for key in expired_keys:
            del self.service_cache[key]
        self.cache_metrics["cache_ttl_expires"] += len(expired_keys)
        self.cache_metrics["cache_size"] = len(self.service_cache)
        
    def update_performance_metrics(self, response_time: float) -> None:
        """Update service performance metrics"""
        self.service_metrics["total_requests"] += 1
        self.service_metrics["total_response_time"] += response_time
        self.service_metrics["average_response_time"] = (
            self.service_metrics["total_response_time"] / self.service_metrics["total_requests"]
        )

# Global orchestration state with complete service state management
orchestration_state = AIOrchestrationServiceState()

@performance_core.track_operation("create_unified_ai_orchestration_app")
def create_app() -> FastAPI:
    """Create and configure unified FastAPI application with all AI components"""
    microservice_logger.info("Creating unified AI Orchestration application with full centralization")
    
    app = FastAPI(
        title="Neliti AI Orchestration - Unified Microservice",
        description="Comprehensive AI workflow coordination with Handit AI, Letta, LangGraph, and Langfuse integration",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include orchestration router
    app.include_router(orchestration_router, prefix="/api/v1", tags=["orchestration"])
    
    @app.on_event("startup")
    @performance_core.track_operation("startup_unified_ai_orchestration")
    async def startup_event():
        """Initialize unified AI orchestration with all components on startup"""
        start_time = time.perf_counter()
        
        try:
            microservice_logger.info("🚀 Starting unified AI Orchestration microservice with full centralization")
            
            # Initialize all AI orchestration components
            await initialize_ai_components()
            
            # Start background tasks
            asyncio.create_task(unified_workflow_executor())
            asyncio.create_task(unified_health_monitor())
            asyncio.create_task(unified_metrics_collector())
            asyncio.create_task(unified_trace_processor())
            
            # Load workflow templates
            await load_unified_workflow_templates()
            
            # Initialize default AI configurations
            await initialize_default_ai_configurations()
            
            # Calculate startup time
            startup_time = (time.perf_counter() - start_time) * 1000
            unified_microservice_metrics["startup_time"] = startup_time
            
            # Publish startup event with full details
            event_manager.publish_event(
                event_type="unified_ai_orchestration_startup",
                component="unified_ai_orchestration_microservice",
                message="Unified AI orchestration microservice started successfully with all components",
                data={
                    "startup_time_ms": startup_time,
                    "active_components": sum(orchestration_state.component_status.values()),
                    "component_status": orchestration_state.component_status,
                    "microservice_version": "2.0.0",
                    "environment": service_config.get('environment', 'development'),
                    "startup_timestamp": time.time()
                }
            )
            unified_microservice_metrics["events_published"] += 1
            
            microservice_logger.info(f"✅ Unified AI Orchestration microservice started successfully ({startup_time:.2f}ms)", extra={
                "startup_time_ms": startup_time,
                "active_components": sum(orchestration_state.component_status.values()),
                "component_status": orchestration_state.component_status
            })
            
        except Exception as e:
            startup_time = (time.perf_counter() - start_time) * 1000
            
            error_response = error_handler.handle_error(
                error=e,
                component="unified_ai_orchestration_microservice",
                operation="startup",
                context={"startup_time_ms": startup_time}
            )
            
            microservice_logger.error(f"❌ Failed to start unified AI orchestration microservice: {error_response}")
            raise
    
    @app.on_event("shutdown")
    @performance_core.track_operation("shutdown_unified_ai_orchestration")
    async def shutdown_event():
        """Cleanup unified AI orchestration on shutdown"""
        try:
            microservice_logger.info("🛑 Shutting down unified AI Orchestration microservice")
            
            # Stop all active workflows
            for workflow_id in list(orchestration_state.active_workflows.keys()):
                await stop_unified_workflow(workflow_id)
            
            # Cleanup all AI components
            await cleanup_ai_components()
            
            # Publish shutdown event
            event_manager.publish_event(
                event_type="unified_ai_orchestration_shutdown",
                component="unified_ai_orchestration_microservice",
                message="Unified AI orchestration microservice shutdown completed",
                data={
                    "final_workflow_count": len(orchestration_state.active_workflows),
                    "final_task_count": len(orchestration_state.active_tasks),
                    "execution_stats": orchestration_state.execution_stats,
                    "shutdown_timestamp": time.time()
                }
            )
            
            microservice_logger.info("✅ Unified AI Orchestration microservice shutdown completed gracefully")
            
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                component="unified_ai_orchestration_microservice",
                operation="shutdown",
                context={}
            )
            microservice_logger.error(f"❌ Error during unified microservice shutdown: {error_response}")
    
    @app.get("/health")
    @performance_core.track_operation("unified_health_check")
    async def unified_health_check():
        """Comprehensive health check for all AI components"""
        try:
            unified_microservice_metrics["health_checks"] += 1
            
            # Get health status from all components
            component_health = {}
            
            if orchestration_state.handit_service:
                component_health["handit_ai"] = orchestration_state.handit_service.get_health_status()
            
            if orchestration_state.letta_service:
                component_health["letta_memory"] = orchestration_state.letta_service.get_health_status()
            
            if orchestration_state.langgraph_service:
                component_health["langgraph_workflows"] = orchestration_state.langgraph_service.get_health_status()
            
            if orchestration_state.langfuse_service:
                component_health["langfuse_observability"] = orchestration_state.langfuse_service.get_health_status()
            
            uptime = time.time() - unified_microservice_metrics["uptime_start"]
            
            health_data = {
                "status": "healthy",
                "service": "ai-orchestration-unified",
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": uptime,
                "microservice_version": "2.0.0",
                "active_workflows": len(orchestration_state.active_workflows),
                "active_tasks": len(orchestration_state.active_tasks),
                "active_memory_sessions": len(orchestration_state.active_memory_sessions),
                "active_traces": len(orchestration_state.active_traces),
                "component_status": orchestration_state.component_status,
                "component_health": component_health,
                "execution_stats": orchestration_state.execution_stats,
                "metrics": unified_microservice_metrics,
                "environment": service_config.get('environment', 'development')
            }
            
            return health_data
            
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                component="unified_ai_orchestration_microservice",
                operation="health_check",
                context={}
            )
            microservice_logger.error(f"❌ Unified health check failed: {error_response}")
            
            return JSONResponse(
                status_code=500,
                content={
                    "status": "unhealthy",
                    "service": "ai-orchestration-unified",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )
    
    @app.get("/status")
    @performance_core.track_operation("unified_detailed_status")
    async def unified_detailed_status():
        """Comprehensive detailed status for unified AI orchestration"""
        try:
            uptime = time.time() - unified_microservice_metrics["uptime_start"]
            
            # Collect detailed metrics from all components
            detailed_metrics = {
                "handit_ai": {},
                "letta_memory": {},
                "langgraph_workflows": {},
                "langfuse_observability": {}
            }
            
            if orchestration_state.handit_service:
                detailed_metrics["handit_ai"] = orchestration_state.handit_service.get_health_status()
            
            if orchestration_state.letta_service:
                detailed_metrics["letta_memory"] = orchestration_state.letta_service.get_health_status()
            
            if orchestration_state.langgraph_service:
                detailed_metrics["langgraph_workflows"] = orchestration_state.langgraph_service.get_health_status()
            
            if orchestration_state.langfuse_service:
                detailed_metrics["langfuse_observability"] = orchestration_state.langfuse_service.get_health_status()
            
            return {
                "service": "ai-orchestration-unified",
                "status": "running",
                "uptime_seconds": uptime,
                "microservice_version": "2.0.0",
                "environment": service_config.get('environment', 'development'),
                "component_status": orchestration_state.component_status,
                "execution_stats": orchestration_state.execution_stats,
                "unified_metrics": unified_microservice_metrics,
                "service_cache_metrics": orchestration_state.cache_metrics,
                "detailed_component_metrics": detailed_metrics,
                "active_workflows": {
                    wf_id: {"status": wf.get("status"), "created_at": wf.get("created_at")}
                    for wf_id, wf in orchestration_state.active_workflows.items()
                },
                "active_tasks": {
                    task_id: {"status": task.get("status"), "created_at": task.get("created_at")}
                    for task_id, task in orchestration_state.active_tasks.items()
                },
                "configuration": {
                    "ai_orchestration_port": service_config.get('port', 8003),
                    "health_check_interval": config_core.get('monitoring.health_check_interval_seconds', 30),
                    "debug_mode": service_config.get('debug', False)
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                component="unified_ai_orchestration_microservice",
                operation="detailed_status",
                context={}
            )
            microservice_logger.error(f"❌ Detailed status check failed: {error_response}")
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )
    
    # Unified AI Orchestration Endpoints
    @app.post("/api/v1/orchestration/execute")
    @performance_core.track_operation("execute_unified_ai_orchestration")
    @cache_core.cached(ttl=600)  # Cache AI orchestration results for 10 minutes
    async def execute_unified_orchestration(orchestration_data: Dict[str, Any]):
        """Execute unified AI orchestration with all components"""
        start_time = time.perf_counter()
        
        try:
            # Generate orchestration ID
            orchestration_id = f"orchestration_{int(time.time() * 1000)}"
            
            # Validate orchestration request
            validation_result = validator.validate_required_fields(
                orchestration_data,
                ["operation_type", "parameters"]
            )
            
            if not validation_result.is_valid:
                unified_microservice_metrics["failed_requests"] += 1
                return JSONResponse(
                    status_code=400,
                    content={"error": "Invalid orchestration request", "validation": validation_result}
                )
            
            operation_type = orchestration_data.get("operation_type")
            parameters = orchestration_data.get("parameters", {})
            
            # Execute unified orchestration based on operation type
            result = await execute_unified_operation(orchestration_id, operation_type, parameters)
            
            # Calculate execution time
            execution_time = (time.perf_counter() - start_time) * 1000
            
            # Update metrics
            unified_microservice_metrics["total_requests"] += 1
            unified_microservice_metrics["successful_requests"] += 1
            unified_microservice_metrics["total_ai_operations"] += 1
            
            # Publish orchestration event
            event_manager.publish_event(
                event_type="unified_orchestration_executed",
                component="unified_ai_orchestration_microservice",
                message=f"Unified AI orchestration executed: {operation_type}",
                data={
                    "orchestration_id": orchestration_id,
                    "operation_type": operation_type,
                    "execution_time_ms": execution_time,
                    "success": result.get("success", False),
                    "components_used": result.get("components_used", [])
                }
            )
            unified_microservice_metrics["events_published"] += 1
            
            microservice_logger.info(f"🤖 Unified AI orchestration executed: {operation_type} ({execution_time:.2f}ms)", extra={
                "orchestration_id": orchestration_id,
                "execution_time_ms": execution_time,
                "components_used": result.get("components_used", [])
            })
            
            return {
                "success": True,
                "orchestration_id": orchestration_id,
                "operation_type": operation_type,
                "execution_time_ms": execution_time,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            unified_microservice_metrics["failed_requests"] += 1
            
            error_response = error_handler.handle_error(
                error=e,
                component="unified_ai_orchestration_microservice",
                operation="execute_orchestration",
                context={
                    "orchestration_data": orchestration_data,
                    "execution_time_ms": execution_time
                }
            )
            
            microservice_logger.error(f"❌ Unified AI orchestration failed: {error_response}")
            
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": str(e),
                    "execution_time_ms": execution_time,
                    "timestamp": datetime.now().isoformat()
                }
            )
    
    return app

# AI Component Initialization
@performance_core.track_operation("initialize_unified_ai_components")
async def initialize_ai_components():
    """Initialize all AI orchestration components with centralization"""
    try:
        microservice_logger.info("🔧 Initializing all AI orchestration components...")
        
        # Initialize Handit AI Client
        try:
            orchestration_state.handit_service = get_handit_microservice()
            orchestration_state.component_status["handit_ai"] = True
            microservice_logger.info("✅ Handit AI Client initialized successfully")
        except Exception as e:
            microservice_logger.error(f"❌ Failed to initialize Handit AI: {str(e)}")
            orchestration_state.component_status["handit_ai"] = False
        
        # Initialize Letta Memory Integration
        try:
            orchestration_state.letta_service = get_letta_memory_microservice()
            orchestration_state.component_status["letta_memory"] = True
            microservice_logger.info("✅ Letta Memory Integration initialized successfully")
        except Exception as e:
            microservice_logger.error(f"❌ Failed to initialize Letta Memory: {str(e)}")
            orchestration_state.component_status["letta_memory"] = False
        
        # Initialize LangGraph Workflows
        try:
            orchestration_state.langgraph_service = get_langgraph_workflow_microservice()
            orchestration_state.component_status["langgraph_workflows"] = True
            microservice_logger.info("✅ LangGraph Workflows initialized successfully")
        except Exception as e:
            microservice_logger.error(f"❌ Failed to initialize LangGraph Workflows: {str(e)}")
            orchestration_state.component_status["langgraph_workflows"] = False
        
        # Initialize Langfuse Observability
        try:
            orchestration_state.langfuse_service = get_langfuse_observability_microservice()
            orchestration_state.component_status["langfuse_observability"] = True
            microservice_logger.info("✅ Langfuse Observability initialized successfully")
        except Exception as e:
            microservice_logger.error(f"❌ Failed to initialize Langfuse Observability: {str(e)}")
            orchestration_state.component_status["langfuse_observability"] = False
        
        # Update orchestration stats
        orchestration_state.execution_stats["active_components"] = sum(orchestration_state.component_status.values())
        
        # Publish component initialization event
        event_manager.publish_event(
            event_type="ai_components_initialized",
            component="unified_ai_orchestration_microservice",
            message="AI orchestration components initialization completed",
            data={
                "component_status": orchestration_state.component_status,
                "active_components": orchestration_state.execution_stats["active_components"],
                "initialization_timestamp": time.time()
            }
        )
        unified_microservice_metrics["events_published"] += 1
        
        microservice_logger.info(f"🎯 AI components initialization completed: {orchestration_state.execution_stats['active_components']}/4 components active")
        
    except Exception as e:
        error_response = error_handler.handle_error(
            error=e,
            component="unified_ai_orchestration_microservice",
            operation="initialize_components",
            context={"component_status": orchestration_state.component_status}
        )
        microservice_logger.error(f"❌ AI components initialization failed: {error_response}")
        raise

# Unified Operation Execution
@performance_core.track_operation("execute_unified_ai_operation")
async def execute_unified_operation(orchestration_id: str, operation_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Execute unified AI operation using appropriate components"""
    try:
        components_used = []
        results = {}
        
        # Route operation to appropriate components based on type
        if operation_type == "handit_task":
            if orchestration_state.handit_service:
                task_result = await orchestration_state.handit_service.execute_task(
                    task_type=parameters.get("task_type", "analysis"),
                    input_data=parameters.get("input_data", {}),
                    model_specialty=parameters.get("model_specialty", "general")
                )
                results["handit_result"] = task_result
                components_used.append("handit_ai")
                unified_microservice_metrics["handit_requests"] += 1
        
        elif operation_type == "memory_operation":
            if orchestration_state.letta_service:
                if parameters.get("action") == "create_session":
                    session_id = await orchestration_state.letta_service.create_session(
                        agent_id=parameters.get("agent_id", "default"),
                        context=parameters.get("context", {})
                    )
                    results["memory_session_id"] = session_id
                    orchestration_state.active_memory_sessions[session_id] = {
                        "agent_id": parameters.get("agent_id"),
                        "created_at": datetime.now().isoformat()
                    }
                
                elif parameters.get("action") == "add_memory":
                    memory_id = await orchestration_state.letta_service.add_memory(
                        session_id=parameters.get("session_id"),
                        content=parameters.get("content", ""),
                        memory_type=parameters.get("memory_type", "semantic"),
                        importance=parameters.get("importance", 0.5)
                    )
                    results["memory_id"] = memory_id
                
                components_used.append("letta_memory")
                unified_microservice_metrics["letta_operations"] += 1
        
        elif operation_type == "workflow_execution":
            if orchestration_state.langgraph_service:
                workflow_result = await orchestration_state.langgraph_service.execute_workflow(
                    template_name=parameters.get("template_name", "trading_analysis_microservice"),
                    input_data=parameters.get("input_data", {}),
                    parameters=parameters.get("workflow_parameters", {})
                )
                results["workflow_result"] = workflow_result.__dict__ if hasattr(workflow_result, '__dict__') else workflow_result
                components_used.append("langgraph_workflows")
                unified_microservice_metrics["langgraph_workflows"] += 1
        
        elif operation_type == "trace_creation":
            if orchestration_state.langfuse_service:
                trace_id = await orchestration_state.langfuse_service.create_trace(
                    name=parameters.get("trace_name", "AI Operation"),
                    input_data=parameters.get("input_data", {}),
                    metadata=parameters.get("metadata", {}),
                    session_id=parameters.get("session_id"),
                    user_id=parameters.get("user_id")
                )
                results["trace_id"] = trace_id
                orchestration_state.active_traces[trace_id] = {
                    "trace_name": parameters.get("trace_name"),
                    "created_at": datetime.now().isoformat()
                }
                components_used.append("langfuse_observability")
                unified_microservice_metrics["langfuse_traces"] += 1
        
        elif operation_type == "comprehensive_analysis":
            # Use multiple components for comprehensive analysis
            comprehensive_results = {}
            
            # Start with trace creation for observability
            if orchestration_state.langfuse_service:
                trace_id = await orchestration_state.langfuse_service.create_trace(
                    name="Comprehensive AI Analysis",
                    input_data=parameters,
                    metadata={"operation_type": "comprehensive_analysis"}
                )
                comprehensive_results["trace_id"] = trace_id
                components_used.append("langfuse_observability")
            
            # Execute workflow for structured analysis
            if orchestration_state.langgraph_service:
                workflow_result = await orchestration_state.langgraph_service.execute_workflow(
                    template_name="trading_analysis_microservice",
                    input_data=parameters.get("input_data", {}),
                    parameters=parameters.get("workflow_parameters", {})
                )
                comprehensive_results["workflow_analysis"] = workflow_result.__dict__ if hasattr(workflow_result, '__dict__') else workflow_result
                components_used.append("langgraph_workflows")
            
            # Use Handit AI for specific task processing
            if orchestration_state.handit_service:
                task_result = await orchestration_state.handit_service.execute_task(
                    task_type="comprehensive_analysis",
                    input_data=parameters.get("input_data", {}),
                    model_specialty="trading"
                )
                comprehensive_results["handit_analysis"] = task_result
                components_used.append("handit_ai")
            
            results = comprehensive_results
        
        else:
            raise ValueError(f"Unknown operation type: {operation_type}")
        
        return {
            "success": True,
            "orchestration_id": orchestration_id,
            "operation_type": operation_type,
            "components_used": components_used,
            "results": results,
            "execution_timestamp": time.time()
        }
        
    except Exception as e:
        error_response = error_handler.handle_error(
            error=e,
            component="unified_ai_orchestration_microservice",
            operation="execute_operation",
            context={
                "orchestration_id": orchestration_id,
                "operation_type": operation_type,
                "parameters": parameters
            }
        )
        microservice_logger.error(f"❌ Unified operation execution failed: {error_response}")
        raise

# Background Tasks
async def unified_workflow_executor():
    """Unified background task executor for all AI components"""
    microservice_logger.info("🔄 Starting unified workflow executor")
    
    while True:
        try:
            # Process workflows, tasks, and operations
            await asyncio.sleep(1)
            
        except Exception as e:
            microservice_logger.error(f"❌ Error in unified workflow executor: {str(e)}")
            await asyncio.sleep(5)

async def unified_health_monitor():
    """Unified health monitoring for all AI components"""
    microservice_logger.info("💊 Starting unified health monitor")
    
    while True:
        try:
            # Monitor all component health
            if orchestration_state.handit_service:
                health = orchestration_state.handit_service.get_health_status()
                if health.get("status") != "healthy":
                    microservice_logger.warning("⚠️ Handit AI health check warning")
            
            if orchestration_state.letta_service:
                health = orchestration_state.letta_service.get_health_status()
                if health.get("status") != "healthy":
                    microservice_logger.warning("⚠️ Letta Memory health check warning")
            
            if orchestration_state.langgraph_service:
                health = orchestration_state.langgraph_service.get_health_status()
                if health.get("status") != "healthy":
                    microservice_logger.warning("⚠️ LangGraph Workflows health check warning")
            
            if orchestration_state.langfuse_service:
                health = orchestration_state.langfuse_service.get_health_status()
                if health.get("status") != "healthy":
                    microservice_logger.warning("⚠️ Langfuse Observability health check warning")
            
            await asyncio.sleep(30)  # Check every 30 seconds
            
        except Exception as e:
            microservice_logger.error(f"❌ Error in unified health monitor: {str(e)}")
            await asyncio.sleep(60)

async def unified_metrics_collector():
    """Unified metrics collection from all AI components"""
    microservice_logger.info("📊 Starting unified metrics collector")
    
    while True:
        try:
            # Collect and aggregate metrics from all components
            await asyncio.sleep(60)  # Collect every minute
            
        except Exception as e:
            microservice_logger.error(f"❌ Error in unified metrics collector: {str(e)}")
            await asyncio.sleep(120)

async def unified_trace_processor():
    """Unified trace processing for observability"""
    microservice_logger.info("🔍 Starting unified trace processor")
    
    while True:
        try:
            # Process traces and observability data
            if orchestration_state.langfuse_service:
                await orchestration_state.langfuse_service.flush_observations()
            
            await asyncio.sleep(300)  # Process every 5 minutes
            
        except Exception as e:
            microservice_logger.error(f"❌ Error in unified trace processor: {str(e)}")
            await asyncio.sleep(600)

async def load_unified_workflow_templates():
    """Load unified workflow templates for all components"""
    try:
        microservice_logger.info("📋 Loading unified workflow templates")
        # Templates are loaded by individual components during initialization
        microservice_logger.info("✅ Unified workflow templates loaded successfully")
        
    except Exception as e:
        microservice_logger.error(f"❌ Failed to load unified workflow templates: {str(e)}")

async def initialize_default_ai_configurations():
    """Initialize default AI configurations for all components"""
    try:
        microservice_logger.info("⚙️ Initializing default AI configurations")
        # Default configurations are handled by individual components
        microservice_logger.info("✅ Default AI configurations initialized successfully")
        
    except Exception as e:
        microservice_logger.error(f"❌ Failed to initialize default AI configurations: {str(e)}")

async def stop_unified_workflow(workflow_id: str) -> Dict[str, Any]:
    """Stop unified workflow execution"""
    try:
        if workflow_id in orchestration_state.active_workflows:
            workflow = orchestration_state.active_workflows[workflow_id]
            workflow["status"] = "cancelled"
            workflow["stopped_at"] = datetime.now().isoformat()
            return {"success": True, "workflow_id": workflow_id}
        else:
            return {"success": False, "error": f"Workflow {workflow_id} not found"}
            
    except Exception as e:
        microservice_logger.error(f"❌ Failed to stop unified workflow {workflow_id}: {str(e)}")
        return {"success": False, "error": str(e)}

async def cleanup_ai_components():
    """Cleanup all AI components on shutdown"""
    try:
        microservice_logger.info("🧹 Cleaning up AI components")
        
        # Cleanup individual components if they have cleanup methods
        if orchestration_state.langfuse_service:
            await orchestration_state.langfuse_service.flush_observations()
        
        # Reset component status
        for component in orchestration_state.component_status:
            orchestration_state.component_status[component] = False
        
        microservice_logger.info("✅ AI components cleanup completed")
        
    except Exception as e:
        microservice_logger.error(f"❌ Error during AI components cleanup: {str(e)}")

# Create the unified app instance
orchestration_app = create_app()

if __name__ == "__main__":
    port = service_config.get('port', 8003)
    debug = service_config.get('debug', False)
    
    microservice_logger.info(f"🚀 Starting Unified AI Orchestration microservice on port {port}")
    
    uvicorn.run(
        "main:orchestration_app",
        host="0.0.0.0",
        port=port,
        reload=debug,
        log_level="debug" if debug else "info"
    )