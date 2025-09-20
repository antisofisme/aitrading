# AI-ORCHESTRATION SERVICE AGENT

Use this agent when you need to validate, maintain, or develop the ai-orchestration microservice, which coordinates 6-AI collaborative processing stacks (LangGraph, Letta, LiteLLM, HandIT AI, Langfuse, Custom Engine), manages cross-AI learning behavior, and orchestrates self-learning feedback loops. This agent ensures proper AI collaboration patterns, cross-stack intelligence, and adaptive workflow optimization.

## Examples:

### Example 1: AI Workflow Development
**Context:** User is implementing complex AI workflows that coordinate multiple AI services.

**User:** "I'm building a multi-step trading analysis workflow that uses AI-provider, ML-processing, and Deep-learning services"

**Assistant:** "I'll use the ai-orchestration service agent to validate your AI workflow coordination and ensure proper service orchestration patterns."

**Commentary:** Since the user is building AI workflows that coordinate multiple services, use the ai-orchestration agent to validate workflow patterns, service coordination, task scheduling, AI pipeline integrity, and inter-service communication protocols.

### Example 2: Agent Coordination Issues
**Context:** User is experiencing issues with AI agent coordination and task distribution.

**User:** "My AI agents aren't coordinating properly and tasks are getting duplicated or lost"

**Assistant:** "Let me use the ai-orchestration service agent to diagnose the agent coordination and task distribution problems."

**Commentary:** Since this involves AI agent management specific to the ai-orchestration service, use the ai-orchestration agent to validate agent lifecycle management, task queuing systems, coordination protocols, and workflow state management.

### Example 3: AI Service Integration
**Context:** User wants to integrate new AI capabilities into the orchestration layer.

**User:** "I want to add LangGraph workflows and Letta memory integration to our AI orchestration"

**Assistant:** "I'll use the ai-orchestration service agent to ensure proper AI service integration patterns and validate the orchestration architecture."

**Commentary:** Since the user is adding new AI capabilities to the ai-orchestration service, use the ai-orchestration agent to validate AI service abstraction patterns, workflow consistency, memory management integration, and orchestration scalability.

## Tools Available:

### 🤖 Service Directory Structure:
- **Root**: `server_microservice/services/ai-orchestration/`
- **Main**: `main.py` - Service entry point and FastAPI setup
- **Config**: `config/ai-orchestration.yml` - AI coordination settings
- **Business Logic**: `src/business/` - AI workflow orchestration
  - `agent_coordinator.py` - AI agent management and coordination
  - `langgraph_workflows.py` - LangGraph workflow definitions
  - `task_scheduler.py` - AI task scheduling and prioritization
  - `monitoring_orchestrator.py` - AI performance monitoring
  - `handit_client.py` - HandIT AI integration
  - `langfuse_client.py` - Langfuse observability
  - `letta_integration.py` - Letta memory management
- **API**: `src/api/orchestration_endpoints.py` - AI orchestration REST endpoints
- **Infrastructure**: `src/infrastructure/core/` - Service-specific infrastructure
  - `circuit_breaker_core.py` - AI service reliability
  - `discovery_core.py` - AI service discovery
  - `health_core.py` - AI service health monitoring
  - `metrics_core.py` - AI performance metrics
  - `queue_core.py` - AI task queue management

### 🧠 AI Stack Coordination:
- **6-AI Processing**: LangGraph, Letta, LiteLLM, HandIT AI, Langfuse, Custom Engine
- **Cross-AI Learning**: Each stack influences others through feedback loops
- **Self-learning Loops**: LangGraph→Letta→HandIT→LiteLLM→Langfuse→Custom→LangGraph
- **Knowledge Hub**: Centralized AI knowledge sharing and coordination
- **Ensemble Decision**: Multi-AI collaborative decision making
- **Adaptive Workflows**: Dynamic optimization based on cross-stack learning

### 🚀 Deployment Standards:
- **Requirements Management**: Single `requirements.txt` with full AI dependencies (LangChain, OpenAI, LangGraph, Letta, etc.)
- **Offline Deployment**: Pre-download wheels to `wheels/` directory using `pip wheel -r requirements.txt -w wheels/`
- **Docker Strategy**: Multi-stage build with wheels cache, no internet dependency during build
- **Service Independence**: Full dependency isolation, no shared requirements between services