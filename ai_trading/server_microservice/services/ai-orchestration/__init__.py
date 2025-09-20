"""
AI Orchestration Service - Intelligent workflow coordination
Manages AI agent collaboration and task distribution
"""
__version__ = "2.0.0"
__service_type__ = "ai-orchestration"

from .src import api, business, infrastructure

__all__ = ['api', 'business', 'infrastructure']

__service_capabilities__ = [
    'agent_coordination',
    'workflow_orchestration', 
    'task_distribution',
    'ai_collaboration'
]