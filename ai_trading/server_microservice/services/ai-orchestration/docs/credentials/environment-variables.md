# AI Orchestration Service - Credentials and Configuration Management

## ✅ Status: Credentials Properly Externalized

All hardcoded credentials and configuration values have been moved to the centralized configuration system.

## 🎯 Configuration File Location

```
F:\WINDSURF\neliti_code\server_microservice\config\ai-orchestration\ai-orchestration.yml
```

## 🔒 Sensitive Data Management

### Environment Variables with Defaults
The configuration uses the pattern `${ENVIRONMENT_VARIABLE:default_value}` to allow:
- ✅ **Environment Variable Override**: Production secrets via environment variables
- ✅ **Default Values**: Safe defaults for development
- ✅ **No Hardcoded Secrets**: All sensitive data externalized

### Required Environment Variables for Production

#### Service Configuration
```bash
MICROSERVICE_ENVIRONMENT=production
AI_ORCHESTRATION_PORT=8003
AI_ORCHESTRATION_DEBUG=false
HEALTH_CHECK_INTERVAL=30
```

#### Handit AI Service
```bash
HANDIT_AI_ENABLED=true
HANDIT_AI_API_KEY=your_actual_api_key_here
HANDIT_AI_BASE_URL=https://api.handit.ai
HANDIT_AI_TIMEOUT=30
HANDIT_AI_MAX_CONCURRENT=10
```

#### Letta Memory Service
```bash
LETTA_MEMORY_ENABLED=true
LETTA_MAX_MEMORIES=1000
LETTA_RETENTION_DAYS=30
LETTA_DEBUG=false
```

#### LangGraph Workflows
```bash
LANGGRAPH_ENABLED=true
LANGGRAPH_MAX_CONCURRENT=10
LANGGRAPH_TIMEOUT=300
LANGGRAPH_RETRIES=3
LANGGRAPH_DEBUG=false
```

#### Langfuse Observability
```bash
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-lf-your_public_key_here
LANGFUSE_SECRET_KEY=sk-lf-your_secret_key_here
LANGFUSE_HOST=https://cloud.langfuse.com
LANGFUSE_FLUSH_AT=15
LANGFUSE_FLUSH_INTERVAL=0.5
LANGFUSE_DEBUG=false
OBSERVABILITY_LEVEL=detailed
```

#### Agent Coordinator
```bash
AGENT_COORDINATOR_MAX_AGENTS=100
AGENT_COORDINATOR_MAX_QUEUE=1000
AGENT_MESSAGE_TIMEOUT=30
```

#### Security (Optional)
```bash
ENABLE_AUTHENTICATION=true
JWT_SECRET=your_jwt_secret_minimum_32_characters
SESSION_TIMEOUT=3600
```

## 📁 File Structure

```
ai-orchestration/
├── .env.example                    # Template with all environment variables
├── main.py                         # Updated to use config manager
├── src/
│   └── infrastructure/
│       └── config_manager.py       # Configuration manager with env expansion
└── config/
    └── ai-orchestration.yml        # Centralized configuration with ${VAR:default}
```

## 🔧 How It Works

### 1. Configuration Loading
```python
# Automatically loads and expands environment variables
config_manager = get_config_manager()
service_config = get_service_config()

# Example: Gets HANDIT_AI_API_KEY or empty string
api_key = config_manager.get('ai_services.handit.api_key')
```

### 2. Environment Variable Expansion
The configuration file uses YAML with environment variable substitution:
```yaml
ai_services:
  handit:
    api_key: ${HANDIT_AI_API_KEY:}           # Required credential
    base_url: ${HANDIT_AI_BASE_URL:https://api.handit.ai}  # Optional with default
    enabled: ${HANDIT_AI_ENABLED:true}       # Boolean with default
```

### 3. Validation
```python
# Check if required credentials are provided
validation = config_manager.validate_required_credentials()
# Returns: {'handit_api_key': True, 'langfuse_public_key': False, ...}
```

## 🚀 Deployment Instructions

### Development Environment
1. Copy `.env.example` to `.env`
2. Fill in actual API keys and credentials
3. The service will load from environment variables

### Production Environment
1. Set environment variables in your deployment system:
   - Docker: Use environment variables or secrets
   - Kubernetes: Use ConfigMaps and Secrets
   - Cloud: Use cloud-specific secret management

### Docker Deployment
```bash
# Using environment variables
docker run -e HANDIT_AI_API_KEY=your_key \
           -e LANGFUSE_SECRET_KEY=your_secret \
           ai-orchestration:latest

# Using environment file
docker run --env-file .env ai-orchestration:latest
```

### Kubernetes Deployment
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: ai-orchestration-secrets
data:
  HANDIT_AI_API_KEY: <base64-encoded-key>
  LANGFUSE_SECRET_KEY: <base64-encoded-secret>
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-orchestration
spec:
  template:
    spec:
      containers:
      - name: ai-orchestration
        envFrom:
        - secretRef:
            name: ai-orchestration-secrets
```

## ✅ Security Benefits

1. **No Hardcoded Secrets**: All sensitive data moved to environment variables
2. **Environment-Specific Configuration**: Different settings per environment
3. **Safe Defaults**: Development can run without production credentials
4. **Credential Validation**: Runtime validation of required credentials
5. **Configuration Isolation**: Each service manages its own configuration

## 🔍 Verification

To verify that credentials are properly externalized:

```bash
# Check configuration without secrets
curl http://localhost:8003/status

# The response will show masked credentials:
{
  "configuration": {
    "handit_api_key": "***provided***",  # Indicates key is set
    "langfuse_public_key": "***provided***"
  }
}
```

## 📋 Migration Summary

### ✅ Completed Changes

1. **Created centralized configuration file**: `ai-orchestration.yml`
2. **Environment variable expansion**: `${VAR:default}` pattern
3. **Configuration manager**: Handles loading and validation
4. **Updated main.py**: Removed hardcoded `os.getenv()` calls
5. **Created .env.example**: Template for all required variables
6. **Added validation**: Check for required credentials

### 🔒 Security Improvements

- **Before**: Hardcoded defaults in Python code
- **After**: Environment variables with safe defaults in YAML
- **Benefit**: Production secrets never in code, easy to rotate

The AI orchestration service now follows security best practices with no hardcoded credentials or configuration values.