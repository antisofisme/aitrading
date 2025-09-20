"""
🔍 Langfuse Observability Management - MICROSERVICE IMPLEMENTATION
Enterprise-grade AI observability, tracing, and performance monitoring with microservice architecture

CENTRALIZED INFRASTRUCTURE:
- Performance tracking untuk AI observability operations
- Centralized error handling untuk tracing and monitoring
- Event publishing untuk observability lifecycle monitoring
- Enhanced logging dengan observability-specific configuration
- Comprehensive validation untuk trace and span data
- Advanced metrics tracking untuk AI performance optimization

This module provides:
- AI observability dengan Langfuse integration for microservices
- Comprehensive tracing and monitoring dengan performance tracking
- AI cost tracking and usage analytics dengan centralized monitoring
- Real-time performance metrics dengan event publishing
- Enterprise-grade observability dengan error recovery
"""

import os
import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import threading

# SERVICE-SPECIFIC CENTRALIZED INFRASTRUCTURE
from .base_microservice import AIOrchestrationBaseMicroservice
from ....shared.infrastructure.core.logger_core import CoreLogger

# Enhanced logger with service-specific infrastructure
observability_logger = CoreLogger("ai-orchestration", "langfuse_observability")

try:
    from langfuse import Langfuse
    AI_ORCHESTRATION_LANGFUSE_AVAILABLE = True
except ImportError:
    AI_ORCHESTRATION_LANGFUSE_AVAILABLE = False


if not AI_ORCHESTRATION_LANGFUSE_AVAILABLE:
    observability_logger.warning("Langfuse not available for microservice. Install with: pip install langfuse")

# Langfuse observability performance metrics for microservice
ai_orchestration_langfuse_metrics = {
    "total_traces_created": 0,
    "successful_traces": 0,
    "failed_traces": 0,
    "total_spans_created": 0,
    "total_generations": 0,
    "total_events": 0,
    "total_observations": 0,
    "total_tokens_tracked": 0,
    "total_cost_tracked": 0.0,
    "avg_trace_duration_ms": 0,
    "events_published": 0,
    "validation_errors": 0,
    "langfuse_errors": 0,
    "microservice_uptime": time.time(),
    "total_api_calls": 0
}


class TraceStatus(Enum):
    """Status of traces for microservice"""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ObservabilityLevel(Enum):
    """Observability tracking levels for microservice"""
    BASIC = "basic"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"
    DEBUG = "debug"


@dataclass
class AIOrchestrationTraceMetrics:
    """
    Metrics for a specific trace - MICROSERVICE ENHANCED WITH CENTRALIZATION
    Enterprise-grade trace metrics with comprehensive tracking for microservice architecture
    """
    trace_id: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    token_count: int = 0
    cost_estimate: float = 0.0
    status: TraceStatus = TraceStatus.PENDING
    spans_count: int = 0
    observations_count: int = 0
    
    # Enhanced tracking for microservice
    microservice_metadata: Dict[str, Any] = field(default_factory=dict)
    performance_data: Dict[str, float] = field(default_factory=dict)
    error_count: int = 0
    
    def __post_init__(self):
        """Initialize trace metrics with microservice centralization"""
        try:
            self.microservice_metadata.update({
                "creation_method": "trace_metrics_microservice",
                "microservice": "ai-orchestration",
                "centralized_infrastructure": True,
                "creation_timestamp": time.time(),
                "environment": os.getenv("MICROSERVICE_ENVIRONMENT", "development")
            })
            
        except Exception as e:
            from ....shared.infrastructure.core.error_core import CoreErrorHandler
            error_handler = CoreErrorHandler("ai-orchestration")
            error_response = error_handler.handle_error(
                error=e,
                component="langfuse_observability",
                operation="initialize_trace_metrics",
                context={"trace_id": self.trace_id}
            )
            observability_logger.error(f"Failed to initialize trace metrics: {error_response}")
    
    @performance_tracked(operation_name="complete_trace_microservice")
    def complete_trace(self):
        """Complete trace with microservice tracking"""
        try:
            if self.end_time is None:
                self.end_time = time.time()
            
            self.duration_ms = (self.end_time - self.start_time) * 1000
            self.status = TraceStatus.COMPLETED
            
            # Update global metrics
            ai_orchestration_langfuse_metrics["successful_traces"] += 1
            ai_orchestration_langfuse_metrics["avg_trace_duration_ms"] = (
                (ai_orchestration_langfuse_metrics["avg_trace_duration_ms"] * (ai_orchestration_langfuse_metrics["successful_traces"] - 1) + 
                 self.duration_ms) / ai_orchestration_langfuse_metrics["successful_traces"]
            )
            
            # Publish trace completion event
            from ....shared.infrastructure.core.event_core import CoreEventManager
            event_manager = CoreEventManager("ai-orchestration")
            event_manager.publish_event(
                event_type="trace_completed",
                component="langfuse_observability",
                message=f"Trace completed: {self.trace_id}",
                data={
                    "trace_id": self.trace_id,
                    "duration_ms": self.duration_ms,
                    "spans_count": self.spans_count,
                    "token_count": self.token_count,
                    "cost_estimate": self.cost_estimate,
                    "service": "ai-orchestration"
                }
            )
            ai_orchestration_langfuse_metrics["events_published"] += 1
            
        except Exception as e:
            from ....shared.infrastructure.core.error_core import CoreErrorHandler
            error_handler = CoreErrorHandler("ai-orchestration")
            error_response = error_handler.handle_error(
                error=e,
                component="langfuse_observability",
                operation="complete_trace",
                context={"trace_id": self.trace_id}
            )
            observability_logger.error(f"Failed to complete trace: {error_response}")


@dataclass
class AIOrchestrationObservabilitySession:
    """
    Observability session for microservice - ENHANCED WITH CENTRALIZATION
    Enterprise-grade observability session management for microservice architecture
    """
    session_id: str
    service_name: str = "ai-orchestration"
    created_at: datetime = field(default_factory=datetime.now)
    traces: Dict[str, AIOrchestrationTraceMetrics] = field(default_factory=dict)
    session_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Enhanced tracking for microservice
    total_cost: float = 0.0
    total_tokens: int = 0
    total_observations: int = 0
    microservice_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize observability session with microservice centralization"""
        try:
            self.microservice_metadata.update({
                "creation_method": "observability_session_microservice",
                "microservice": "ai-orchestration",
                "centralized_infrastructure": True,
                "session_start": time.time(),
                "environment": os.getenv("MICROSERVICE_ENVIRONMENT", "development")
            })
            
        except Exception as e:
            from ....shared.infrastructure.core.error_core import CoreErrorHandler
            error_handler = CoreErrorHandler("ai-orchestration")
            error_response = error_handler.handle_error(
                error=e,
                component="langfuse_observability",
                operation="initialize_session",
                context={"session_id": self.session_id}
            )
            observability_logger.error(f"Failed to initialize observability session: {error_response}")
    
    @performance_tracked(operation_name="add_trace_to_session_microservice")
    def add_trace(self, trace_metrics: AIOrchestrationTraceMetrics):
        """Add trace to session with microservice tracking"""
        try:
            self.traces[trace_metrics.trace_id] = trace_metrics
            
            # Update session totals
            self.total_cost += trace_metrics.cost_estimate
            self.total_tokens += trace_metrics.token_count
            self.total_observations += trace_metrics.observations_count
            
            # Update global metrics
            ai_orchestration_langfuse_metrics["total_cost_tracked"] += trace_metrics.cost_estimate
            ai_orchestration_langfuse_metrics["total_tokens_tracked"] += trace_metrics.token_count
            
        except Exception as e:
            from ....shared.infrastructure.core.error_core import CoreErrorHandler
            error_handler = CoreErrorHandler("ai-orchestration")
            error_response = error_handler.handle_error(
                error=e,
                component="langfuse_observability",
                operation="add_trace_to_session",
                context={"session_id": self.session_id, "trace_id": trace_metrics.trace_id}
            )
            observability_logger.error(f"Failed to add trace to session: {error_response}")


class AIOrchestrationLangfuseObservability(AIOrchestrationBaseMicroservice):
    """
    Langfuse Observability Manager for Microservice - ENHANCED WITH FULL CENTRALIZATION
    Enterprise-grade AI observability, tracing, and performance monitoring for microservice architecture
    
    CENTRALIZED INFRASTRUCTURE:
    - Performance tracking untuk AI observability operations
    - Centralized error handling untuk tracing and monitoring
    - Event publishing untuk observability lifecycle monitoring
    - Enhanced logging dengan observability-specific configuration
    - Comprehensive validation untuk trace and span data
    - Advanced metrics tracking untuk AI performance optimization
    """
    
    @performance_tracked(operation_name="initialize_langfuse_microservice")
    def __init__(self):
        """Initialize Langfuse Observability Microservice dengan FULL CENTRALIZATION"""
        try:
            # Initialize base microservice infrastructure
            super().__init__(service_name="ai-orchestration", component_name="langfuse_observability")
            
            # Component-specific initialization
            self.client: Optional[Langfuse] = None
            self.active_traces: Dict[str, AIOrchestrationTraceMetrics] = {}
            self.sessions: Dict[str, AIOrchestrationObservabilitySession] = {}
            
            # Concurrency optimization
            self._trace_lock = threading.RLock()  # Thread-safe trace operations
            self._batch_operations_queue = asyncio.Queue(maxsize=1000)
            self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="langfuse")
            self._background_tasks: set = set()  # Track background tasks
            
            # Component-specific monitoring
            self.performance_analytics: Dict[str, Any] = {}
            self.trace_stats: Dict[str, int] = {
                "total_traces": 0,
                "active_traces": 0,
                "completed_traces": 0,
                "failed_traces": 0
            }
            
            # Setup Langfuse client
            self._setup_microservice_client()
            
            # Publish component initialization event
            self.publish_event(
                event_type="langfuse_observability_initialized",
                message="Langfuse observability component initialized with full centralization",
                data={
                    "langfuse_available": AI_ORCHESTRATION_LANGFUSE_AVAILABLE,
                    "microservice_version": "2.0.0"
                }
            )
            ai_orchestration_langfuse_metrics["events_published"] += 1
            
            if not AI_ORCHESTRATION_LANGFUSE_AVAILABLE:
                observability_logger.warning("Langfuse not available for microservice. Install with: pip install langfuse")
            
            self.logger.info(f"✅ Langfuse observability microservice initialized with centralization infrastructure")
            
        except Exception as e:
            error_response = self.handle_error(e, "initialize", {"component": "langfuse_observability"})
            self.logger.error(f"Failed to initialize Langfuse observability microservice: {error_response}")
            raise
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for Langfuse observability component"""
        # Use service-specific centralized configuration
        langfuse_config = self.config_manager.get('langfuse', {})
        
        return {
            "public_key": langfuse_config.get("public_key", ""),
            "secret_key": langfuse_config.get("secret_key", ""),
            "host": langfuse_config.get("host", "https://cloud.langfuse.com"),
            "enabled": langfuse_config.get("enabled", True),
            "flush_at": langfuse_config.get("flush_at", 15),
            "flush_interval": langfuse_config.get("flush_interval", 0.5),
            "health_check_interval": self.config_manager.get('monitoring.health_check_interval_seconds', 30),
            "debug": langfuse_config.get("debug", False),
            "observability_level": self.config_manager.get("observability.level", "detailed")
        }
    
    def _perform_health_checks(self) -> Dict[str, Any]:
        """Perform Langfuse observability specific health checks"""
        try:
            return {
                "healthy": True,
                "langfuse_available": AI_ORCHESTRATION_LANGFUSE_AVAILABLE,
                "client_initialized": self.client is not None,
                "active_traces": len(self.active_traces),
                "active_sessions": len(self.sessions),
                "trace_stats": self.trace_stats
            }
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    @performance_tracked(operation_name="setup_observability_microservice_client")
    def _setup_microservice_client(self):
        """Setup Langfuse observability client untuk microservice dengan FULL CENTRALIZATION"""
        try:
            if not AI_ORCHESTRATION_LANGFUSE_AVAILABLE:
                self.logger.warning("⚠️ Langfuse not available for microservice, using mock implementation")
                return
            
            if not self.enabled:
                self.logger.info("🔅 Langfuse observability microservice disabled via configuration")
                return
            
            # Validate configuration
            public_key = self.config.get("public_key", "")
            secret_key = self.config.get("secret_key", "")
            
            if not public_key or not secret_key:
                self.logger.warning("⚠️ Langfuse keys not provided for microservice")
                return
            
            # Initialize Langfuse client for microservice
            self.client = Langfuse(
                public_key=public_key,
                secret_key=secret_key,
                host=self.config.get("host", "https://cloud.langfuse.com"),
                flush_at=self.config.get("flush_at", 15),
                flush_interval=self.config.get("flush_interval", 0.5),
                debug=self.config.get("debug", False)
            )
            
            # Publish client initialization event for microservice
            self.publish_event(
                event_type="langfuse_client_initialized",
                message="Langfuse client initialized",
                data={
                    "host": self.config.get("host"),
                    "observability_level": self.config.get("observability_level")
                }
            )
            ai_orchestration_langfuse_metrics["events_published"] += 1
            
            self.logger.info("✅ Langfuse observability microservice client setup complete")
            
        except Exception as e:
            ai_orchestration_langfuse_metrics["langfuse_errors"] += 1
            
            error_response = self.handle_error(e, "setup_client", {})
            self.logger.error(f"❌ Failed to setup observability microservice client: {error_response}")
    
    @performance_tracked(operation_name="create_trace_microservice")
    async def create_trace(
        self,
        name: str,
        input_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> str:
        """Create new trace untuk microservice dengan FULL CENTRALIZATION"""
        start_time = time.perf_counter()
        
        try:
            # Generate trace ID for microservice
            trace_id = f"trace_ms_{name}_{int(time.time() * 1000)}"
            
            # Enhanced validation for microservice
            if not self.validate_data(
                {"name": name}, ["name"]
            ):
                ai_orchestration_langfuse_metrics["validation_errors"] += 1
                raise ValueError(f"Invalid trace name for microservice")
            
            # Create trace metrics for microservice
            trace_metrics = AIOrchestrationTraceMetrics(
                trace_id=trace_id,
                start_time=time.time()
            )
            
            # Store trace
            self.active_traces[trace_id] = trace_metrics
            
            # Create actual Langfuse trace if client available (async with background execution)
            if self.client and AI_ORCHESTRATION_LANGFUSE_AVAILABLE:
                # Execute Langfuse API call in background to avoid blocking
                task = asyncio.create_task(self._create_langfuse_trace_async(
                    trace_metrics, name, input_data, metadata, session_id, user_id
                ))
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)
            
            # Update microservice metrics
            ai_orchestration_langfuse_metrics["total_traces_created"] += 1
            self.trace_stats["total_traces"] += 1
            self.trace_stats["active_traces"] += 1
            self.track_operation("create_trace", True, {"trace_name": name})
            
            # Calculate creation time
            creation_time = (time.perf_counter() - start_time) * 1000
            
            self.logger.info(f"🔍 Created trace in microservice: {trace_id} - {name}")
            return trace_id
            
        except Exception as e:
            creation_time = (time.perf_counter() - start_time) * 1000
            ai_orchestration_langfuse_metrics["failed_traces"] += 1
            
            error_response = self.handle_error(
                e, "create_trace",
                {"trace_name": name}
            )
            
            self.logger.error(f"❌ Failed to create trace in microservice: {error_response}")
            raise
    
    @performance_tracked(operation_name="create_span_microservice")
    async def create_span(
        self,
        trace_id: str,
        name: str,
        input_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create span within trace untuk microservice dengan FULL CENTRALIZATION"""
        start_time = time.perf_counter()
        
        try:
            # Validate trace exists
            if trace_id not in self.active_traces:
                ai_orchestration_langfuse_metrics["validation_errors"] += 1
                raise ValueError(f"Trace {trace_id} not found in microservice")
            
            # Generate span ID for microservice
            span_id = f"span_ms_{trace_id}_{name}_{int(time.time() * 1000)}"
            
            # Update trace metrics
            trace_metrics = self.active_traces[trace_id]
            trace_metrics.spans_count += 1
            
            # Create actual Langfuse span if client available
            if self.client and AI_ORCHESTRATION_LANGFUSE_AVAILABLE:
                langfuse_trace_id = trace_metrics.microservice_metadata.get("langfuse_trace_id")
                if langfuse_trace_id:
                    langfuse_span = self.client.span(
                        trace_id=langfuse_trace_id,
                        name=name,
                        input=input_data,
                        metadata=metadata or {}
                    )
            
            # Update metrics
            ai_orchestration_langfuse_metrics["total_spans_created"] += 1
            
            # Calculate creation time
            creation_time = (time.perf_counter() - start_time) * 1000
            
            observability_logger.info(f"📊 Created span in microservice: {span_id} - {name}")
            return span_id
            
        except Exception as e:
            creation_time = (time.perf_counter() - start_time) * 1000
            
            from ....shared.infrastructure.core.error_core import CoreErrorHandler
            error_handler = CoreErrorHandler("ai-orchestration")
            error_response = error_handler.handle_error(
                error=e,
                component="langfuse_observability",
                operation="create_span",
                context={
                    "trace_id": trace_id,
                    "span_name": name,
                    "service_name": self.service_name
                }
            )
            
            observability_logger.error(f"❌ Failed to create span in microservice: {error_response}")
            raise
    
    @performance_tracked(operation_name="complete_trace_microservice")
    async def complete_trace(
        self,
        trace_id: str,
        output_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Complete trace untuk microservice dengan FULL CENTRALIZATION"""
        start_time = time.perf_counter()
        
        try:
            # Validate trace exists
            if trace_id not in self.active_traces:
                ai_orchestration_langfuse_metrics["validation_errors"] += 1
                raise ValueError(f"Trace {trace_id} not found in microservice")
            
            # Get trace metrics
            trace_metrics = self.active_traces[trace_id]
            
            # Complete trace metrics
            trace_metrics.complete_trace()
            
            # Update actual Langfuse trace if client available
            if self.client and AI_ORCHESTRATION_LANGFUSE_AVAILABLE:
                langfuse_trace_id = trace_metrics.microservice_metadata.get("langfuse_trace_id")
                if langfuse_trace_id:
                    self.client.trace(
                        id=langfuse_trace_id,
                        output=output_data,
                        metadata=metadata or {}
                    )
            
            # Move to completed and remove from active
            self.trace_stats["active_traces"] -= 1
            self.trace_stats["completed_traces"] += 1
            self.active_traces.pop(trace_id)
            
            # Calculate completion time
            completion_time = (time.perf_counter() - start_time) * 1000
            
            observability_logger.info(f"✅ Completed trace in microservice: {trace_id} ({completion_time:.2f}ms)")
            return True
            
        except Exception as e:
            completion_time = (time.perf_counter() - start_time) * 1000
            ai_orchestration_langfuse_metrics["failed_traces"] += 1
            
            from ....shared.infrastructure.core.error_core import CoreErrorHandler
            error_handler = CoreErrorHandler("ai-orchestration")
            error_response = error_handler.handle_error(
                error=e,
                component="langfuse_observability",
                operation="complete_trace",
                context={
                    "trace_id": trace_id,
                    "service_name": self.service_name
                }
            )
            
            observability_logger.error(f"❌ Failed to complete trace in microservice: {error_response}")
            return False
    
    @performance_tracked(operation_name="get_observability_microservice_health")
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status untuk observability microservice dengan CENTRALIZATION"""
        try:
            uptime = time.time() - self.microservice_stats["startup_time"]
            
            health_data = {
                "service": self.service_name,
                "component": "langfuse_observability",
                "status": "healthy",
                "uptime_seconds": uptime,
                "langfuse_available": AI_ORCHESTRATION_LANGFUSE_AVAILABLE,
                "client_initialized": self.client is not None,
                "microservice_stats": self.microservice_stats,
                "trace_stats": self.trace_stats,
                "metrics": {
                    "total_traces": ai_orchestration_langfuse_metrics["total_traces_created"],
                    "successful_traces": ai_orchestration_langfuse_metrics["successful_traces"],
                    "failed_traces": ai_orchestration_langfuse_metrics["failed_traces"],
                    "active_traces": len(self.active_traces),
                    "total_spans": ai_orchestration_langfuse_metrics["total_spans_created"],
                    "total_observations": ai_orchestration_langfuse_metrics["total_observations"],
                    "total_tokens_tracked": ai_orchestration_langfuse_metrics["total_tokens_tracked"],
                    "total_cost_tracked": ai_orchestration_langfuse_metrics["total_cost_tracked"],
                    "avg_trace_duration_ms": ai_orchestration_langfuse_metrics["avg_trace_duration_ms"],
                    "events_published": ai_orchestration_langfuse_metrics["events_published"]
                },
                "config": {
                    "enabled": self.config.get("enabled", True),
                    "host": self.config.get("host", "unknown"),
                    "observability_level": self.config.get("observability_level", "basic"),
                    "environment": self.config.get("environment", "development"),
                    "debug": self.config.get("debug", False)
                },
                "sessions": {
                    "active_sessions": len(self.sessions),
                    "session_stats": {
                        session_id: {
                            "total_traces": len(session.traces),
                            "total_cost": session.total_cost,
                            "total_tokens": session.total_tokens
                        }
                        for session_id, session in self.sessions.items()
                    }
                },
                "timestamp": datetime.now().isoformat(),
                "microservice_version": "2.0.0"
            }
            
            # Update health check counter
            self.microservice_stats["health_checks"] += 1
            
            return health_data
            
        except Exception as e:
            from ....shared.infrastructure.core.error_core import CoreErrorHandler
            error_handler = CoreErrorHandler("ai-orchestration")
            error_response = error_handler.handle_error(
                error=e,
                component="langfuse_observability",
                operation="health_check",
                context={"service_name": self.service_name}
            )
            observability_logger.error(f"Failed observability microservice health check: {error_response}")
            
            return {
                "service": self.service_name,
                "component": "langfuse_observability",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _create_langfuse_trace_async(self, trace_metrics, name, input_data, metadata, session_id, user_id):
        """Create Langfuse trace asynchronously in background"""
        try:
            # Run Langfuse API call in thread pool to avoid blocking
            langfuse_trace = await asyncio.get_event_loop().run_in_executor(
                self._executor,
                lambda: self.client.trace(
                    name=name,
                    input=input_data,
                    metadata=metadata or {},
                    session_id=session_id,
                    user_id=user_id
                )
            )
            
            # Thread-safe update of trace metadata
            with self._trace_lock:
                trace_metrics.microservice_metadata["langfuse_trace_id"] = langfuse_trace.id
                
        except Exception as e:
            self.logger.warning(f"Background Langfuse trace creation failed: {str(e)}")
    
    @performance_tracked(operation_name="batch_create_traces_microservice")
    async def batch_create_traces(self, trace_requests: List[Dict[str, Any]]) -> List[str]:
        """Create multiple traces concurrently for better throughput"""
        start_time = time.perf_counter()
        
        try:
            # Create all traces concurrently
            tasks = []
            for request in trace_requests:
                task = self.create_trace(
                    name=request.get("name", "batch_trace"),
                    input_data=request.get("input_data"),
                    metadata=request.get("metadata"),
                    session_id=request.get("session_id"),
                    user_id=request.get("user_id")
                )
                tasks.append(task)
            
            # Wait for all traces to be created
            trace_ids = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and return successful trace IDs
            successful_traces = [tid for tid in trace_ids if isinstance(tid, str)]
            
            creation_time = (time.perf_counter() - start_time) * 1000
            
            self.logger.info(f"🔍 Batch created {len(successful_traces)}/{len(trace_requests)} traces ({creation_time:.2f}ms)")
            return successful_traces
            
        except Exception as e:
            error_response = self.handle_error(e, "batch_create_traces", {"batch_size": len(trace_requests)})
            self.logger.error(f"❌ Failed to batch create traces: {error_response}")
            return []
    
    @performance_tracked(operation_name="flush_observations_microservice")
    async def flush_observations(self) -> bool:
        """Flush pending observations untuk microservice with background execution"""
        try:
            if self.client and AI_ORCHESTRATION_LANGFUSE_AVAILABLE:
                # Execute flush in background to avoid blocking
                await asyncio.get_event_loop().run_in_executor(
                    self._executor,
                    self.client.flush
                )
                
                # Publish flush event
                from ....shared.infrastructure.core.event_core import CoreEventManager
                event_manager = CoreEventManager("ai-orchestration")
                event_manager.publish_event(
                    event_type="observations_flushed",
                    component="langfuse_observability",
                    message="Flushed pending observations",
                    data={
                        "service_name": self.service_name,
                        "active_traces": len(self.active_traces),
                        "flush_timestamp": time.time()
                    }
                )
                ai_orchestration_langfuse_metrics["events_published"] += 1
                
                return True
            
            return False
            
        except Exception as e:
            from ....shared.infrastructure.core.error_core import CoreErrorHandler
            error_handler = CoreErrorHandler("ai-orchestration")
            error_response = error_handler.handle_error(
                error=e,
                component="langfuse_observability",
                operation="flush_observations",
                context={"service_name": self.service_name}
            )
            observability_logger.error(f"Failed to flush observations in microservice: {error_response}")
            return False


# Global microservice instance
ai_orchestration_langfuse_observability = AIOrchestrationLangfuseObservability()


def get_langfuse_observability_microservice() -> AIOrchestrationLangfuseObservability:
    """Get the global Langfuse observability microservice instance"""
    return ai_orchestration_langfuse_observability