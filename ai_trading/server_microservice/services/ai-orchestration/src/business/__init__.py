"""
AI Orchestration Business Logic - Microservice Implementation

Lazy-loading module for comprehensive AI orchestration components:
- Handit AI Client: Task orchestration and AI model coordination
- Letta Memory Integration: Advanced memory management for AI agents
- LangGraph Workflows: Complex multi-step AI workflow execution
- Langfuse Observability: Comprehensive AI performance monitoring
- Agent Coordinator: Multi-agent coordination and communication management
- Unified AI Orchestrator: Complete orchestration coordination
"""

__version__ = "2.0.0"
__microservice__ = "ai-orchestration"

# Lazy loading for AI orchestration components
def __getattr__(name):
    if name == "get_handit_microservice":
        from .handit_client import get_handit_microservice
        return get_handit_microservice
    elif name == "get_letta_memory_microservice":
        from .letta_integration import get_letta_memory_microservice
        return get_letta_memory_microservice
    elif name == "get_langgraph_workflow_microservice":
        from .langgraph_workflows import get_langgraph_workflow_microservice
        return get_langgraph_workflow_microservice
    elif name == "get_langfuse_observability_microservice":
        from .langfuse_client import get_langfuse_observability_microservice
        return get_langfuse_observability_microservice
    elif name == "AIOrchestrationHanditClient":
        from .handit_client import AIOrchestrationHanditClient
        return AIOrchestrationHanditClient
    elif name == "AIOrchestrationLettaIntegration":
        from .letta_integration import AIOrchestrationLettaIntegration
        return AIOrchestrationLettaIntegration
    elif name == "AIOrchestrationLangGraphWorkflows":
        from .langgraph_workflows import AIOrchestrationLangGraphWorkflows
        return AIOrchestrationLangGraphWorkflows
    elif name == "AIOrchestrationLangfuseClient":
        from .langfuse_client import AIOrchestrationLangfuseClient
        return AIOrchestrationLangfuseClient
    elif name == "AIOrchestrationAgentCoordinator":
        from .agent_coordinator import AIOrchestrationAgentCoordinator
        return AIOrchestrationAgentCoordinator
    elif name == "MLPipelineOrchestrator":
        from .ml_pipeline_orchestrator import MLPipelineOrchestrator
        return MLPipelineOrchestrator
    elif name == "MonitoringOrchestrator":
        from .monitoring_orchestrator import MonitoringOrchestrator
        return MonitoringOrchestrator
    elif name == "ScheduledTasksManager":
        from .task_scheduler import ScheduledTasksManager
        return ScheduledTasksManager
    else:
        raise AttributeError(f"module {__name__} has no attribute {name}")

__all__ = [
    "get_handit_microservice",
    "get_letta_memory_microservice", 
    "get_langgraph_workflow_microservice",
    "get_langfuse_observability_microservice",
    "AIOrchestrationHanditClient",
    "AIOrchestrationLettaIntegration",
    "AIOrchestrationLangGraphWorkflows",
    "AIOrchestrationLangfuseClient",
    "AIOrchestrationAgentCoordinator",
    "MLPipelineOrchestrator",
    "MonitoringOrchestrator",
    "ScheduledTasksManager"
]