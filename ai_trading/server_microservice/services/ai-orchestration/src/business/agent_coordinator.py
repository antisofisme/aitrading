"""
🤖 Agent Coordinator - Microservice Implementation
Multi-agent coordination and communication management with full centralization

CENTRALIZED INFRASTRUCTURE INTEGRATION:
- Performance tracking for comprehensive agent coordination operations
- Centralized error handling for agent management and communication
- Event publishing for complete agent lifecycle monitoring
- Enhanced logging with agent-specific configuration and context
- Comprehensive validation for agent data and coordination parameters
- Advanced metrics tracking for agent performance optimization
"""

import os
import asyncio
import heapq
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import time

# SERVICE-SPECIFIC CENTRALIZED INFRASTRUCTURE
from .base_microservice import AIOrchestrationBaseMicroservice
from ....shared.infrastructure.core.logger_core import CoreLogger
from ....shared.infrastructure.base.base_performance import performance_tracked

# Enhanced logger with service-specific infrastructure
agent_coordinator_logger = CoreLogger("ai-orchestration", "agent_coordinator")

class AIOrchestrationAgentRole(Enum):
    """AI Orchestration Service - Enhanced agent roles for microservice orchestration"""
    ANALYZER = "analyzer"
    TRADER = "trader"
    RISK_MANAGER = "risk_manager"
    MARKET_MONITOR = "market_monitor"
    STRATEGY_PLANNER = "strategy_planner"
    AI_COORDINATOR = "ai_coordinator"
    MEMORY_MANAGER = "memory_manager"
    WORKFLOW_EXECUTOR = "workflow_executor"
    OBSERVABILITY_TRACKER = "observability_tracker"

class AgentStatus(Enum):
    """Enhanced agent status states"""
    IDLE = "idle"
    BUSY = "busy"
    PROCESSING = "processing"
    WAITING = "waiting"
    ERROR = "error"
    OFFLINE = "offline"
    INITIALIZING = "initializing"
    SHUTTING_DOWN = "shutting_down"

class MessagePriority(Enum):
    """Message priority levels"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5

@dataclass
class AIOrchestrationAgentMessage:
    """Enhanced message between agents with microservice features"""
    id: str
    sender_id: str
    receiver_id: str
    message_type: str
    content: Dict[str, Any]
    timestamp: datetime
    priority: int = MessagePriority.NORMAL.value
    metadata: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    sequence_number: int = field(default_factory=lambda: int(time.time() * 1000000))
    
    def __lt__(self, other):
        """Enable priority queue ordering (lower priority number = higher priority)"""
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.sequence_number < other.sequence_number

@dataclass
class AIOrchestrationAgent:
    """Enhanced agent definition for microservice orchestration"""
    id: str
    name: str
    role: AIOrchestrationAgentRole
    status: AgentStatus
    capabilities: List[str]
    handler: Optional[Callable] = None
    last_activity: Optional[datetime] = None
    health_score: float = 1.0
    performance_metrics: Optional[Dict[str, Any]] = None
    configuration: Optional[Dict[str, Any]] = None

class AIOrchestrationAgentCoordinator(AIOrchestrationBaseMicroservice):
    """
    🤖 Multi-agent coordination system with full microservice centralization
    
    Enterprise-grade agent coordination with:
    - Comprehensive performance tracking
    - Centralized error handling and validation
    - Event publishing for all agent operations
    - Advanced message routing and priority management
    - Health monitoring and metrics collection
    """
    
    @performance_tracked(operation_name="initialize_agent_coordinator_microservice")
    def __init__(self):
        try:
            # Initialize base microservice infrastructure
            super().__init__(service_name="ai-orchestration", component_name="agent_coordinator")
            
            # Component-specific initialization
            self.agents: Dict[str, AIOrchestrationAgent] = {}
            self.message_queue: List[AIOrchestrationAgentMessage] = []  # Priority heap
            self.agent_lookup_cache: Dict[str, AIOrchestrationAgent] = {}  # O(1) agent lookup
            self.running = False
            self.coordination_tasks: List[asyncio.Task] = []
            self._message_sequence = 0
            
            # Enhanced microservice state
            self.coordination_stats = {
                "total_agents_registered": 0,
                "total_messages_sent": 0,
                "total_messages_processed": 0,
                "total_tasks_coordinated": 0,
                "successful_coordinations": 0,
                "failed_coordinations": 0,
                "average_response_time": 0.0,
                "health_checks_performed": 0,
                "uptime_start": datetime.now()
            }
            
            # Publish component initialization event
            self.publish_event(
                event_type="agent_coordinator_initialized",
                message="Agent coordinator component initialized with full centralization",
                data={
                    "agents_count": 0,
                    "message_queue_size": 0,
                    "coordination_stats": self.coordination_stats,
                    "microservice_version": "2.0.0"
                }
            )
            
            self.logger.info("🤖 Agent Coordinator component initialized with centralization infrastructure")
            
        except Exception as e:
            error_response = self.handle_error(e, "initialize", {"component": "agent_coordinator"})
            self.logger.error(f"Failed to initialize Agent Coordinator microservice: {error_response}")
            raise
    
    @performance_tracked(operation_name="register_agent_microservice")
    def register_agent(self, agent: AIOrchestrationAgent) -> Dict[str, Any]:
        """Register a new agent with comprehensive validation and tracking"""
        try:
            # Enhanced validation
            validation_result = self.validate_data(
                {"agent_id": agent.id, "agent_name": agent.name},
                ["agent_id", "agent_name"]
            )
            
            if not validation_result:
                error_response = self.handle_error(
                    ValueError("Agent validation failed"),
                    "register_agent",
                    {"agent_id": agent.id, "agent_name": agent.name}
                )
                self.logger.error(f"❌ Agent validation failed: {agent.id}")
                return {"success": False, "error": "Agent validation failed"}
            
            # Check for duplicate registration
            if agent.id in self.agents:
                agent_coordinator_logger.warning(f"⚠️ Agent already registered: {agent.id}")
                return {"success": False, "error": "Agent already registered", "agent_id": agent.id}
            
            # Initialize agent performance metrics
            agent.performance_metrics = {
                "messages_received": 0,
                "messages_sent": 0,
                "tasks_completed": 0,
                "errors_encountered": 0,
                "average_response_time": 0.0,
                "last_health_check": datetime.now().isoformat(),
                "registration_time": datetime.now().isoformat()
            }
            
            # Set initial status
            agent.status = AgentStatus.INITIALIZING
            agent.last_activity = datetime.now()
            
            # Register agent
            self.agents[agent.id] = agent
            self.agent_lookup_cache[agent.id] = agent  # Cache for O(1) lookup
            self.coordination_stats["total_agents_registered"] += 1
            
            # Event publishing for agent registration
            self.publish_event(
                event_type="agent_registered",
                message=f"Agent registered: {agent.name} ({agent.role.value})",
                data={
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "agent_role": agent.role.value,
                    "capabilities": agent.capabilities,
                    "total_agents": len(self.agents),
                    "registered_at": datetime.now().isoformat()
                }
            )
            
            # Set agent to idle after successful registration
            agent.status = AgentStatus.IDLE
            
            self.logger.info(f"✅ Agent registered successfully: {agent.name} ({agent.role.value})")
            
            return {
                "success": True,
                "agent_id": agent.id,
                "agent_name": agent.name,
                "role": agent.role.value,
                "status": agent.status.value,
                "total_agents": len(self.agents),
                "registration_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_response = self.handle_error(
                e, "register_agent",
                {"agent_id": agent.id, "agent_name": agent.name}
            )
            self.logger.error(f"❌ Failed to register agent {agent.name}: {error_response}")
            return {"success": False, "error": str(e), "error_response": error_response}
    
    @performance_tracked(operation_name="send_agent_message_microservice")
    async def send_message(self, sender_id: str, receiver_id: str, 
                          message_type: str, content: Dict[str, Any], 
                          priority: int = MessagePriority.NORMAL.value,
                          correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """Send message between agents with enhanced routing and tracking"""
        try:
            # Enhanced validation
            validation_result = self.validate_data(
                {"sender_id": sender_id, "receiver_id": receiver_id, "message_type": message_type},
                ["sender_id", "receiver_id", "message_type"]
            )
            
            if not validation_result:
                error_response = self.handle_error(
                    ValueError("Message validation failed"),
                    "send_message",
                    {"sender_id": sender_id, "receiver_id": receiver_id}
                )
                self.logger.error(f"❌ Message validation failed: {sender_id} → {receiver_id}")
                return {"success": False, "error": "Message validation failed"}
            
            # Verify agents exist (O(1) lookup via cache)
            if sender_id not in self.agent_lookup_cache and sender_id != "coordinator":
                return {"success": False, "error": f"Sender agent not found: {sender_id}"}
            
            if receiver_id not in self.agent_lookup_cache:
                return {"success": False, "error": f"Receiver agent not found: {receiver_id}"}
            
            # Create enhanced message with optimized metadata
            self._message_sequence += 1
            now = datetime.now()
            
            message = AIOrchestrationAgentMessage(
                id=str(uuid.uuid4()),
                sender_id=sender_id,
                receiver_id=receiver_id,
                message_type=message_type,
                content=content,
                timestamp=now,
                priority=priority,
                correlation_id=correlation_id or str(uuid.uuid4()),
                sequence_number=self._message_sequence,
                metadata={
                    "sender_role": self.agent_lookup_cache.get(sender_id, {}).get("role", "coordinator") if hasattr(self.agent_lookup_cache.get(sender_id, {}), 'get') else "coordinator",
                    "receiver_role": self.agent_lookup_cache[receiver_id].role.value,
                    "created_at": now.isoformat()
                }
            )
            
            # Add to priority heap (O(log n) instead of O(n log n))
            heapq.heappush(self.message_queue, message)
            
            # Update statistics
            self.coordination_stats["total_messages_sent"] += 1
            if sender_id in self.agents:
                self.agents[sender_id].performance_metrics["messages_sent"] += 1
            
            # Event publishing for message sending
            self.publish_event(
                event_type="agent_message_sent",
                message=f"Message sent: {sender_id} → {receiver_id} ({message_type})",
                data={
                    "message_id": message.id,
                    "sender_id": sender_id,
                    "receiver_id": receiver_id,
                    "message_type": message_type,
                    "priority": priority,
                    "correlation_id": message.correlation_id,
                    "queue_size": len(self.message_queue),
                    "sent_at": datetime.now().isoformat()
                }
            )
            
            self.logger.debug(f"📨 Message queued: {sender_id} → {receiver_id} ({message_type})")
            
            return {
                "success": True,
                "message_id": message.id,
                "correlation_id": message.correlation_id,
                "queue_position": len(self.message_queue),
                "estimated_delivery": "immediate" if priority <= 2 else "normal",
                "sent_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_response = self.handle_error(
                e, "send_message",
                {"sender_id": sender_id, "receiver_id": receiver_id, "message_type": message_type}
            )
            self.logger.error(f"❌ Failed to send message: {error_response}")
            return {"success": False, "error": str(e), "error_response": error_response}
    
    @performance_tracked(operation_name="coordinate_multi_agent_task_microservice")
    async def coordinate_task(self, task_name: str, participants: List[str], 
                            task_data: Dict[str, Any], 
                            coordination_strategy: str = "sequential") -> Dict[str, Any]:
        """Coordinate a multi-agent task with enhanced strategy and tracking"""
        try:
            # Enhanced validation
            validation_result = self.validate_data(
                {"task_name": task_name, "participants": participants},
                ["task_name", "participants"]
            )
            
            if not validation_result:
                error_response = self.handle_error(
                    ValueError("Task coordination validation failed"),
                    "coordinate_task",
                    {"task_name": task_name}
                )
                self.logger.error(f"❌ Task validation failed: {task_name}")
                return {"success": False, "error": "Task validation failed"}
            
            # Validate participants (optimized with set operations)
            participants_set = set(participants)
            agents_set = set(self.agent_lookup_cache.keys())
            valid_participants = list(participants_set & agents_set)
            invalid_participants = list(participants_set - agents_set)
            
            if not valid_participants:
                return {"success": False, "error": "No valid participants found", "invalid_participants": invalid_participants}
            
            if invalid_participants:
                self.logger.warning(f"⚠️ Some participants not found: {invalid_participants}")
            
            # Generate coordination ID
            coordination_id = f"coord_{int(datetime.now().timestamp() * 1000)}"
            
            # Update statistics
            self.coordination_stats["total_tasks_coordinated"] += 1
            
            # Create coordination context
            coordination_context = {
                "coordination_id": coordination_id,
                "task_name": task_name,
                "strategy": coordination_strategy,
                "participants": valid_participants,
                "task_data": task_data,
                "created_at": datetime.now().isoformat(),
                "status": "initiated"
            }
            
            # Send task assignments based on strategy
            message_results = []
            
            if coordination_strategy == "sequential":
                # Send messages sequentially
                for i, agent_id in enumerate(valid_participants):
                    result = await self.send_message(
                        sender_id="coordinator",
                        receiver_id=agent_id,
                        message_type="task_assignment",
                        content={
                            **coordination_context,
                            "sequence_position": i + 1,
                            "total_participants": len(valid_participants),
                            "previous_agent": valid_participants[i-1] if i > 0 else None,
                            "next_agent": valid_participants[i+1] if i < len(valid_participants)-1 else None
                        },
                        priority=MessagePriority.HIGH.value,
                        correlation_id=coordination_id
                    )
                    message_results.append(result)
            
            elif coordination_strategy == "parallel":
                # Send messages in parallel
                tasks = []
                for agent_id in valid_participants:
                    task = self.send_message(
                        sender_id="coordinator",
                        receiver_id=agent_id,
                        message_type="task_assignment",
                        content={
                            **coordination_context,
                            "execution_mode": "parallel",
                            "synchronization_required": True
                        },
                        priority=MessagePriority.HIGH.value,
                        correlation_id=coordination_id
                    )
                    tasks.append(task)
                
                message_results = await asyncio.gather(*tasks)
            
            # Count successful message deliveries
            successful_deliveries = sum(1 for result in message_results if result.get("success", False))
            
            # Update success/failure statistics
            if successful_deliveries == len(valid_participants):
                self.coordination_stats["successful_coordinations"] += 1
                coordination_status = "success"
            else:
                self.coordination_stats["failed_coordinations"] += 1
                coordination_status = "partial_success"
            
            # Event publishing for task coordination
            self.publish_event(
                event_type="multi_agent_task_coordinated",
                message=f"Multi-agent task coordinated: {task_name} ({coordination_strategy})",
                data={
                    "coordination_id": coordination_id,
                    "task_name": task_name,
                    "coordination_strategy": coordination_strategy,
                    "participants": valid_participants,
                    "participants_count": len(valid_participants),
                    "successful_deliveries": successful_deliveries,
                    "status": coordination_status,
                    "initiated_at": datetime.now().isoformat()
                }
            )
            
            self.logger.info(f"🎯 Multi-agent task coordinated: {task_name} ({coordination_id})")
            
            return {
                "success": True,
                "coordination_id": coordination_id,
                "task_name": task_name,
                "coordination_strategy": coordination_strategy,
                "participants": valid_participants,
                "invalid_participants": invalid_participants,
                "successful_deliveries": successful_deliveries,
                "message_results": message_results,
                "status": coordination_status,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.coordination_stats["failed_coordinations"] += 1
            error_response = self.handle_error(
                e, "coordinate_task",
                {"task_name": task_name, "participants": participants, "coordination_strategy": coordination_strategy}
            )
            self.logger.error(f"❌ Failed to coordinate task {task_name}: {error_response}")
            return {"success": False, "error": str(e), "error_response": error_response}
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for agent coordinator component"""
        return {
            "enabled": True,
            "max_agents": int(os.getenv("AGENT_COORDINATOR_MAX_AGENTS", "100")),
            "max_queue_size": int(os.getenv("AGENT_COORDINATOR_MAX_QUEUE", "1000")),
            "health_check_interval": int(os.getenv("HEALTH_CHECK_INTERVAL", "30")),
            "message_timeout": int(os.getenv("AGENT_MESSAGE_TIMEOUT", "30"))
        }
    
    def _perform_health_checks(self) -> Dict[str, Any]:
        """Perform agent coordinator specific health checks"""
        try:
            # Calculate agent health metrics
            healthy_agents = sum(1 for agent in self.agents.values() if agent.status not in [AgentStatus.ERROR, AgentStatus.OFFLINE])
            agent_health_percentage = (healthy_agents / len(self.agents) * 100) if self.agents else 100
            
            return {
                "healthy": agent_health_percentage >= 80,
                "total_agents": len(self.agents),
                "healthy_agents": healthy_agents,
                "agent_health_percentage": agent_health_percentage,
                "message_queue_size": len(self.message_queue),
                "running": self.running,
                "active_coordination_tasks": len(self.coordination_tasks)
            }
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    def get_enhanced_health_status(self) -> Dict[str, Any]:
        """Get enhanced health status with agent coordinator specific metrics"""
        # Get base health status from parent
        base_health = super().get_health_status()
        
        # Add agent coordinator specific metrics
        uptime = datetime.now() - self.coordination_stats["uptime_start"]
        base_health.update({
            "coordination_metrics": {
                "total_agents": len(self.agents),
                "total_messages_sent": self.coordination_stats["total_messages_sent"],
                "total_tasks_coordinated": self.coordination_stats["total_tasks_coordinated"],
                "successful_coordinations": self.coordination_stats["successful_coordinations"],
                "failed_coordinations": self.coordination_stats["failed_coordinations"],
                "message_queue_size": len(self.message_queue)
            },
            "coordination_config": {
                "max_agents": self.config.get("max_agents", 100),
                "max_queue_size": self.config.get("max_queue_size", 1000)
            },
            "microservice_version": "2.0.0"
        })
        
        # Update health check count
        self.coordination_stats["health_checks_performed"] += 1
        
        return base_health

def get_agent_coordinator_microservice() -> AIOrchestrationAgentCoordinator:
    """Factory function to get Agent Coordinator Microservice instance"""
    return AIOrchestrationAgentCoordinator()