"""
🧠 Letta Memory Integration - MICROSERVICE IMPLEMENTATION 
Enterprise-grade memory management for AI agents using Letta framework dengan microservice architecture

CENTRALIZED INFRASTRUCTURE:
- Performance tracking untuk memory operations
- Centralized error handling untuk memory management
- Event publishing untuk memory lifecycle monitoring
- Enhanced logging dengan memory-specific configuration
- Comprehensive validation untuk memory data
- Advanced metrics tracking untuk memory performance optimization
"""

import os
import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
import weakref

# CENTRALIZED INFRASTRUCTURE - VIA BASE MICROSERVICE
from .base_microservice import AIOrchestrationBaseMicroservice

# Enhanced logger with microservice infrastructure
from ....shared.infrastructure.core.logger_core import CoreLogger
memory_logger = CoreLogger("ai-orchestration", "letta_memory_microservice")

# Memory management performance metrics for microservice
ai_orchestration_letta_metrics = {
    "total_memory_operations": 0,
    "successful_operations": 0,
    "failed_operations": 0,
    "sessions_created": 0,
    "memories_added": 0,
    "memories_searched": 0,
    "memories_deleted": 0,
    "sessions_active": 0,
    "avg_operation_time_ms": 0,
    "events_published": 0,
    "microservice_uptime": time.time(),
    "total_api_calls": 0
}

try:
    # Future: Import actual Letta when available
    # import letta
    AI_ORCHESTRATION_LETTA_AVAILABLE = False
except ImportError:
    AI_ORCHESTRATION_LETTA_AVAILABLE = False
    memory_logger.warning("Letta not available for microservice. Using mock implementation.")


class MemoryType(Enum):
    """Types of memory for microservice"""
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    WORKING = "working"
    LONG_TERM = "long_term"


class MemoryPriority(Enum):
    """Memory priority levels for microservice"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AIOrchestrationMemoryEntry:
    """
    Individual memory entry untuk MICROSERVICE dengan FULL CENTRALIZATION
    Enterprise-grade memory entry with comprehensive tracking for microservice architecture
    """
    id: str
    content: str
    timestamp: datetime
    memory_type: MemoryType
    importance: float
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    # Enhanced tracking fields for microservice
    created_at: datetime = field(default_factory=datetime.now)
    processing_time_ms: Optional[float] = None
    validation_passed: bool = True
    microservice_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate memory entry with microservice centralized infrastructure"""
        try:
            self.microservice_metadata.update({
                "creation_method": "letta_memory_entry_microservice",
                "microservice": "ai-orchestration",
                "centralized_infrastructure": True,
                "creation_timestamp": time.time(),
                "environment": os.getenv("MICROSERVICE_ENVIRONMENT", "development")
            })
            
            # Enhanced validation for microservice
            from .base_microservice import Validator
            validation_result = Validator.validate_required_fields(
                {"content": self.content, "memory_type": self.memory_type.value},
                ["content", "memory_type"]
            )
            
            self.validation_passed = validation_result.is_valid if hasattr(validation_result, 'is_valid') else True
            
            if not self.validation_passed:
                ai_orchestration_letta_metrics["failed_operations"] += 1
                memory_logger.warning(f"Memory entry validation failed for microservice: {self.id}")
            
        except Exception as e:
            from .base_microservice import ErrorHandler
            error_response = ErrorHandler.handle_error(
                error=e,
                component="letta_memory_microservice",
                operation="validate_memory_entry",
                context={"memory_id": self.id}
            )
            memory_logger.error(f"Failed to validate memory entry in microservice: {error_response}")
    
    def access(self):
        """Access memory entry with microservice tracking"""
        try:
            self.access_count += 1
            self.last_accessed = datetime.now()
            
            # Publish access event for microservice
            from .base_microservice import EventManager
            EventManager.publish_event(
                event_type="memory_entry_accessed",
                component="letta_memory_microservice",
                message=f"Memory entry accessed in microservice: {self.memory_type.value}",
                data={
                    "memory_id": self.id,
                    "memory_type": self.memory_type.value,
                    "access_count": self.access_count,
                    "microservice": "ai-orchestration"
                }
            )
            ai_orchestration_letta_metrics["events_published"] += 1
            
        except Exception as e:
            from .base_microservice import ErrorHandler
            error_response = ErrorHandler.handle_error(
                error=e,
                component="letta_memory_microservice",
                operation="access_memory",
                context={"memory_id": self.id}
            )
            memory_logger.error(f"Failed to access memory entry in microservice: {error_response}")


@dataclass
class AIOrchestrationMemorySession:
    """
    Memory session for microservice dengan FULL CENTRALIZATION
    Enterprise-grade memory session management for microservice architecture
    """
    session_id: str
    agent_id: str
    created_at: datetime = field(default_factory=datetime.now)
    memories: Dict[str, AIOrchestrationMemoryEntry] = field(default_factory=dict)
    session_context: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    
    # Enhanced tracking for microservice
    last_activity: datetime = field(default_factory=datetime.now)
    total_operations: int = 0
    microservice_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize memory session with microservice centralization"""
        try:
            self.microservice_metadata.update({
                "creation_method": "letta_memory_session_microservice",
                "microservice": "ai-orchestration",
                "centralized_infrastructure": True,
                "session_start": time.time(),
                "environment": os.getenv("MICROSERVICE_ENVIRONMENT", "development")
            })
            
            # Update metrics
            ai_orchestration_letta_metrics["sessions_created"] += 1
            ai_orchestration_letta_metrics["sessions_active"] += 1
            
            # Publish session creation event for microservice
            from .base_microservice import EventManager
            EventManager.publish_event(
                event_type="memory_session_created",
                component="letta_memory_microservice",
                message=f"Memory session created in microservice: {self.agent_id}",
                data={
                    "session_id": self.session_id,
                    "agent_id": self.agent_id,
                    "microservice": "ai-orchestration",
                    "creation_timestamp": time.time()
                }
            )
            ai_orchestration_letta_metrics["events_published"] += 1
            
        except Exception as e:
            from .base_microservice import ErrorHandler
            error_response = ErrorHandler.handle_error(
                error=e,
                component="letta_memory_microservice",
                operation="initialize_session",
                context={"session_id": self.session_id}
            )
            memory_logger.error(f"Failed to initialize memory session in microservice: {error_response}")
    
    
    def add_memory(self, memory_entry: AIOrchestrationMemoryEntry) -> bool:
        """Add memory to session with microservice tracking"""
        start_time = time.perf_counter()
        
        try:
            self.memories[memory_entry.id] = memory_entry
            self.total_operations += 1
            self.last_activity = datetime.now()
            
            # Calculate processing time
            processing_time = (time.perf_counter() - start_time) * 1000
            memory_entry.processing_time_ms = processing_time
            
            # Update metrics
            ai_orchestration_letta_metrics["memories_added"] += 1
            ai_orchestration_letta_metrics["successful_operations"] += 1
            ai_orchestration_letta_metrics["total_memory_operations"] += 1
            
            # Publish memory added event for microservice
            from .base_microservice import EventManager
            EventManager.publish_event(
                event_type="memory_added_to_session",
                component="letta_memory_microservice",
                message=f"Memory added to session in microservice: {memory_entry.memory_type.value}",
                data={
                    "session_id": self.session_id,
                    "memory_id": memory_entry.id,
                    "memory_type": memory_entry.memory_type.value,
                    "processing_time_ms": processing_time,
                    "microservice": "ai-orchestration"
                }
            )
            ai_orchestration_letta_metrics["events_published"] += 1
            
            memory_logger.info(f"✅ Added memory to microservice session: {memory_entry.id} ({processing_time:.2f}ms)")
            return True
            
        except Exception as e:
            processing_time = (time.perf_counter() - start_time) * 1000
            ai_orchestration_letta_metrics["failed_operations"] += 1
            
            from .base_microservice import ErrorHandler
            error_response = ErrorHandler.handle_error(
                error=e,
                component="letta_memory_microservice",
                operation="add_memory",
                context={
                    "session_id": self.session_id,
                    "memory_id": memory_entry.id
                }
            )
            memory_logger.error(f"❌ Failed to add memory to microservice session: {error_response}")
            return False


class AIOrchestrationLettaMemory(AIOrchestrationBaseMicroservice):
    """
    Letta Memory Manager for Microservice - ENHANCED WITH FULL CENTRALIZATION
    Enterprise-grade memory management for AI agents using Letta framework in microservice architecture
    
    CENTRALIZED INFRASTRUCTURE:
    - Performance tracking untuk memory operations
    - Centralized error handling untuk memory management
    - Event publishing untuk memory lifecycle monitoring
    - Enhanced logging dengan memory-specific configuration
    - Comprehensive validation untuk memory data
    - Advanced metrics tracking untuk memory performance optimization
    """
    
    
    def __init__(self):
        """Initialize Letta Memory Microservice dengan FULL CENTRALIZATION"""
        try:
            # Initialize base microservice infrastructure
            super().__init__(service_name="ai-orchestration", component_name="letta_memory")
            
            # Component-specific initialization with memory optimization
            self.sessions: Dict[str, AIOrchestrationMemorySession] = {}
            
            # Memory-optimized store with weak references for automatic cleanup
            self.memory_store: Dict[str, AIOrchestrationMemoryEntry] = {}
            self._memory_index: Dict[str, Dict[str, List[weakref.ref]]] = defaultdict(lambda: defaultdict(list))  # Fast search index
            self._session_memory_count: Dict[str, int] = defaultdict(int)  # Track memory usage per session
            
            # Memory cleanup configuration
            self._max_memories_per_session = 1000
            self._max_total_memories = 10000
            self._cleanup_threshold = 0.9  # Cleanup when 90% full
            
            self.client = None
            
            # Component-specific monitoring
            self.performance_analytics: Dict[str, Any] = {}
            self.session_stats: Dict[str, int] = {
                "total_sessions": 0,
                "active_sessions": 0,
                "total_memories": 0,
                "successful_operations": 0,
                "failed_operations": 0
            }
            
            # Setup Letta client
            self._setup_microservice_client()
            
            # Publish component initialization event
            self.publish_event(
                event_type="letta_memory_initialized",
                message="Letta memory component initialized with full centralization",
                data={
                    "letta_available": AI_ORCHESTRATION_LETTA_AVAILABLE,
                    "microservice_version": "2.0.0"
                }
            )
            ai_orchestration_letta_metrics["events_published"] += 1
            
            if not AI_ORCHESTRATION_LETTA_AVAILABLE:
                self.logger.warning("Letta not available for microservice. Using mock implementation.")
            
            self.logger.info(f"✅ Letta memory microservice initialized with centralization infrastructure")
            
        except Exception as e:
            error_response = self.handle_error(e, "initialize", {"component": "letta_memory"})
            self.logger.error(f"Failed to initialize Letta memory microservice: {error_response}")
            raise
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for Letta memory component"""
        return {
            "enabled": os.getenv("LETTA_MEMORY_ENABLED", "true").lower() == "true",
            "max_memories_per_session": int(os.getenv("LETTA_MAX_MEMORIES", "1000")),
            "memory_retention_days": int(os.getenv("LETTA_RETENTION_DAYS", "30")),
            "health_check_interval": int(os.getenv("HEALTH_CHECK_INTERVAL", "30")),
            "debug": os.getenv("LETTA_DEBUG", "false").lower() == "true"
        }
    
    def _perform_health_checks(self) -> Dict[str, Any]:
        """Perform Letta memory specific health checks"""
        try:
            return {
                "healthy": True,
                "letta_available": AI_ORCHESTRATION_LETTA_AVAILABLE,
                "client_initialized": self.client is not None,
                "active_sessions": len(self.sessions),
                "total_memories": len(self.memory_store),
                "session_stats": self.session_stats
            }
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    
    def _setup_microservice_client(self):
        """Setup Letta memory client untuk microservice dengan FULL CENTRALIZATION"""
        try:
            if not AI_ORCHESTRATION_LETTA_AVAILABLE:
                self.logger.warning("⚠️ Letta not available for microservice, using mock implementation")
                return
            
            if not self.enabled:
                self.logger.info("🔅 Letta memory microservice disabled via configuration")
                return
            
            # Future: Initialize actual Letta client for microservice
            # self.client = LettaClient(
            #     config=self.config,
            #     service_name=self.service_name
            # )
            
            self.logger.info("✅ Letta memory microservice client setup complete (mock mode)")
            
        except Exception as e:
            error_response = self.handle_error(e, "setup_client", {})
            self.logger.error(f"❌ Failed to setup memory microservice client: {error_response}")
    
    
    async def create_session(self, agent_id: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Create new memory session untuk microservice dengan FULL CENTRALIZATION"""
        start_time = time.perf_counter()
        
        try:
            # Generate session ID for microservice
            session_id = f"letta_session_{agent_id}_{int(time.time() * 1000)}"
            
            # Enhanced validation for microservice
            if not self.validate_data(
                {"agent_id": agent_id}, ["agent_id"]
            ):
                ai_orchestration_letta_metrics["failed_operations"] += 1
                raise ValueError(f"Invalid agent_id for microservice session creation")
            
            # Create enhanced session for microservice
            session = AIOrchestrationMemorySession(
                session_id=session_id,
                agent_id=agent_id,
                session_context=context or {}
            )
            
            # Store session
            self.sessions[session_id] = session
            
            # Update microservice metrics
            self.session_stats["total_sessions"] += 1
            self.session_stats["active_sessions"] += 1
            self.track_operation("create_session", True, {"agent_id": agent_id})
            
            # Calculate creation time
            creation_time = (time.perf_counter() - start_time) * 1000
            
            self.logger.info(f"🧠 Created memory session for microservice: {session_id} - {agent_id}")
            return session_id
            
        except Exception as e:
            creation_time = (time.perf_counter() - start_time) * 1000
            ai_orchestration_letta_metrics["failed_operations"] += 1
            
            error_response = self.handle_error(
                e, "create_session", 
                {"agent_id": agent_id}
            )
            
            self.logger.error(f"❌ Failed to create memory session for microservice: {error_response}")
            raise
    
    def _cleanup_old_memories(self, session_id: str):
        """Clean up old memories when session reaches capacity"""
        session = self.sessions[session_id]
        if len(session.memories) > self._max_memories_per_session * self._cleanup_threshold:
            # Sort memories by importance and last access, remove least important
            sorted_memories = sorted(
                session.memories.items(),
                key=lambda x: (x[1].importance, x[1].last_accessed or datetime.min)
            )
            
            # Remove 20% of least important memories
            to_remove = int(len(sorted_memories) * 0.2)
            for memory_id, memory in sorted_memories[:to_remove]:
                # Remove from session
                session.memories.pop(memory_id, None)
                # Remove from global store
                self.memory_store.pop(memory_id, None)
                # Update session memory count
                self._session_memory_count[session_id] -= 1
    
    def _build_memory_index(self, memory_entry: AIOrchestrationMemoryEntry):
        """Build search index for fast memory retrieval"""
        # Index by memory type
        self._memory_index["type"][memory_entry.memory_type.value].append(weakref.ref(memory_entry))
        
        # Index by tags
        for tag in memory_entry.tags:
            self._memory_index["tag"][tag].append(weakref.ref(memory_entry))
    
    
    async def add_memory(
        self,
        session_id: str,
        content: str,
        memory_type: MemoryType,
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add memory to session untuk microservice dengan FULL CENTRALIZATION"""
        start_time = time.perf_counter()
        
        try:
            # Validate session exists
            if session_id not in self.sessions:
                ai_orchestration_letta_metrics["failed_operations"] += 1
                raise ValueError(f"Session {session_id} not found in microservice")
            
            # Check and cleanup if session is near capacity
            self._cleanup_old_memories(session_id)
            
            # Generate memory ID for microservice
            memory_id = f"memory_{session_id}_{len(self.sessions[session_id].memories)}_{int(time.time() * 1000)}"
            
            # Create enhanced memory entry for microservice
            memory_entry = AIOrchestrationMemoryEntry(
                id=memory_id,
                content=content,
                timestamp=datetime.now(),
                memory_type=memory_type,
                importance=importance,
                tags=tags or [],
                metadata=metadata or {}
            )
            
            # Add to session
            session = self.sessions[session_id]
            success = session.add_memory(memory_entry)
            
            if success:
                # Store in global memory store
                self.memory_store[memory_id] = memory_entry
                
                # Build search index for fast retrieval
                self._build_memory_index(memory_entry)
                
                # Update session memory count
                self._session_memory_count[session_id] += 1
                
                # Update microservice metrics
                self.session_stats["total_memories"] += 1
                self.session_stats["successful_operations"] += 1
                
                # Calculate processing time
                processing_time = (time.perf_counter() - start_time) * 1000
                
                self.logger.info(f"🧠 Added memory to microservice: {memory_id} - {memory_type.value}")
                return memory_id
            else:
                raise Exception("Failed to add memory to session")
            
        except Exception as e:
            processing_time = (time.perf_counter() - start_time) * 1000
            ai_orchestration_letta_metrics["failed_operations"] += 1
            self.session_stats["failed_operations"] += 1
            
            error_response = self.handle_error(
                e, "add_memory",
                {
                    "session_id": session_id,
                    "memory_type": memory_type.value
                }
            )
            
            self.logger.error(f"❌ Failed to add memory to microservice: {error_response}")
            raise
    
    
    async def search_memories(
        self,
        session_id: str,
        query: str,
        memory_types: Optional[List[MemoryType]] = None,
        limit: int = 10
    ) -> List[AIOrchestrationMemoryEntry]:
        """Search memories in session untuk microservice dengan FULL CENTRALIZATION and optimized search"""
        start_time = time.perf_counter()
        
        try:
            # Validate session exists
            if session_id not in self.sessions:
                ai_orchestration_letta_metrics["failed_operations"] += 1
                raise ValueError(f"Session {session_id} not found in microservice")
            
            session = self.sessions[session_id]
            results = []
            
            # Optimized search using index when possible
            if memory_types and len(memory_types) == 1:
                # Use index for single memory type searches (much faster)
                memory_type = memory_types[0]
                candidate_refs = self._memory_index["type"][memory_type.value]
                
                for memory_ref in candidate_refs:
                    memory = memory_ref()  # Get object from weak reference
                    if memory is None:  # Object was garbage collected
                        continue
                    
                    # Check if memory belongs to this session
                    if memory.id not in session.memories:
                        continue
                    
                    if query.lower() in memory.content.lower():
                        memory.access()  # Track access
                        results.append(memory)
                    
                    if len(results) >= limit:
                        break
            else:
                # Fallback to full search for complex queries
                for memory in session.memories.values():
                    if memory_types and memory.memory_type not in memory_types:
                        continue
                    
                    if query.lower() in memory.content.lower():
                        memory.access()  # Track access
                        results.append(memory)
                    
                    if len(results) >= limit:
                        break
            
            # Update metrics
            ai_orchestration_letta_metrics["memories_searched"] += 1
            ai_orchestration_letta_metrics["successful_operations"] += 1
            
            # Calculate search time
            search_time = (time.perf_counter() - start_time) * 1000
            
            # Publish search event for microservice
            self.publish_event(
                event_type="memories_searched",
                message=f"Memories searched: {len(results)} found",
                data={
                    "session_id": session_id,
                    "query": query,
                    "results_count": len(results),
                    "search_time_ms": search_time
                }
            )
            ai_orchestration_letta_metrics["events_published"] += 1
            
            self.logger.info(f"🔍 Searched memories in microservice: {len(results)} found ({search_time:.2f}ms)")
            return results
            
        except Exception as e:
            search_time = (time.perf_counter() - start_time) * 1000
            ai_orchestration_letta_metrics["failed_operations"] += 1
            
            error_response = self.handle_error(
                e, "search_memories",
                {
                    "session_id": session_id,
                    "query": query
                }
            )
            
            self.logger.error(f"❌ Failed to search memories in microservice: {error_response}")
            return []
    
    def get_enhanced_health_status(self) -> Dict[str, Any]:
        """Get enhanced health status with Letta memory specific metrics"""
        # Get base health status from parent
        base_health = super().get_health_status()
        
        # Calculate memory usage statistics
        total_session_memories = sum(self._session_memory_count.values())
        avg_memories_per_session = total_session_memories / len(self.sessions) if self.sessions else 0
        memory_usage_percentage = (len(self.memory_store) / self._max_total_memories) * 100
        
        # Add Letta memory specific metrics
        base_health.update({
            "letta_metrics": {
                "total_operations": ai_orchestration_letta_metrics["total_memory_operations"],
                "successful_operations": ai_orchestration_letta_metrics["successful_operations"],
                "failed_operations": ai_orchestration_letta_metrics["failed_operations"],
                "active_sessions": len(self.sessions),
                "total_memories": len(self.memory_store),
                "avg_operation_time_ms": ai_orchestration_letta_metrics["avg_operation_time_ms"],
                "avg_memories_per_session": avg_memories_per_session,
                "memory_usage_percentage": memory_usage_percentage
            },
            "session_stats": self.session_stats,
            "memory_config": {
                "max_memories_per_session": self.config.get("max_memories_per_session", 1000),
                "memory_retention_days": self.config.get("memory_retention_days", 30),
                "cleanup_threshold": self._cleanup_threshold
            },
            "memory_optimization": {
                "index_entries": sum(len(entries) for entries in self._memory_index["type"].values()),
                "session_memory_counts": dict(self._session_memory_count),
                "memory_pressure": "high" if memory_usage_percentage > 80 else "medium" if memory_usage_percentage > 60 else "low"
            },
            "microservice_version": "2.0.0"
        })
        
        return base_health


# Global microservice instance
ai_orchestration_letta_memory = AIOrchestrationLettaMemory()


def get_letta_memory_microservice() -> AIOrchestrationLettaMemory:
    """Get the global Letta memory microservice instance"""
    return ai_orchestration_letta_memory