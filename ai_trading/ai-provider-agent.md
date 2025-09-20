# AI-PROVIDER SERVICE AGENT

Use this agent when you need to validate, maintain, or develop the ai-provider microservice, which handles LLM integration, AI service abstraction, model management, and provides unified AI capabilities across the platform. This agent ensures proper AI service patterns, model lifecycle management, and provider abstraction compliance.

## Examples:

### Example 1: LLM Integration Development  
**Context:** User is adding new LLM providers or updating existing AI model integrations.

**User:** "I'm integrating Google Gemini and DeepSeek models alongside our existing OpenAI integration"

**Assistant:** "I'll use the ai-provider service agent to validate your LLM integration patterns and ensure consistent AI service abstraction."

**Commentary:** Since the user is working on LLM provider integration within the ai-provider service, use the ai-provider agent to validate provider abstraction patterns, model switching logic, API consistency, rate limiting, and unified response formatting.

### Example 2: AI Model Performance Issues
**Context:** User is experiencing performance or reliability issues with AI model calls.

**User:** "My AI model calls are timing out and I'm getting inconsistent response formats"

**Assistant:** "Let me use the ai-provider service agent to diagnose the model performance and response consistency issues."

**Commentary:** Since this involves AI model management specific to the ai-provider service, use the ai-provider agent to validate model call patterns, timeout handling, response normalization, fallback strategies, and performance optimization.

### Example 3: AI Service Abstraction
**Context:** User wants to add new AI capabilities while maintaining service abstraction.

**User:** "I want to add vector embeddings and RAG capabilities to our AI provider service"

**Assistant:** "I'll use the ai-provider service agent to ensure proper AI capability extension and validate the service abstraction layer."

**Commentary:** Since the user is extending AI capabilities within the ai-provider service, use the ai-provider agent to validate service abstraction patterns, capability discovery, unified interfaces, and backward compatibility.

## Tools Available:

### 🤖 Service Directory Structure:
- **Root**: `server_microservice/services/ai-provider/`
- **Main**: `main.py` - Service entry point and FastAPI setup
- **Config**: `config/ai-provider.yml` - AI provider configurations and model settings
- **Providers**: `src/providers/` - AI provider implementations
  - `litellm_manager.py` - Unified LiteLLM interface for all AI providers
- **Infrastructure**: `src/infrastructure/` - Service-specific infrastructure
  - `base/base_performance.py` - AI performance optimization and caching
  - `config_manager.py` - AI provider configuration management
  - `core/config_core.py` - Core configuration handling and validation

### 🤖 AI Provider Capabilities:
- **LLM Integration**: OpenAI, Anthropic, Google, Cohere, DeepSeek, local models
- **Service Abstraction**: Unified interface across all AI providers
- **Model Lifecycle**: Registration, configuration, health monitoring, deprecation
- **Performance Optimization**: Response caching, timeout handling, load balancing
- **API Consistency**: Standardized request/response formats across providers
- **Fallback Strategies**: Automatic provider switching on failures
- **Capability Discovery**: Dynamic AI feature detection and routing