# API-GATEWAY SERVICE AGENT

Use this agent when you need to validate, maintain, or develop the api-gateway microservice, which handles request routing, authentication middleware, rate limiting, API orchestration, and service proxy management. This agent ensures proper gateway patterns, routing efficiency, and API security compliance.

## Examples:

### Example 1: API Routing and Service Integration
**Context:** User is implementing new API routes or updating service routing logic in the gateway.

**User:** "I'm adding new trading API endpoints and need to route them to the appropriate microservices with load balancing"

**Assistant:** "I'll use the api-gateway service agent to validate your routing configuration and ensure proper service integration patterns."

**Commentary:** Since the user is working on API routing within the api-gateway service, use the api-gateway agent to validate routing rules, service discovery patterns, load balancing strategies, failover mechanisms, and service health checking.

### Example 2: Authentication and Rate Limiting Issues
**Context:** User is experiencing problems with authentication middleware or rate limiting functionality.

**User:** "My API rate limiting is blocking legitimate users and authentication tokens aren't being validated correctly"

**Assistant:** "Let me use the api-gateway service agent to diagnose your authentication and rate limiting configuration issues."

**Commentary:** Since this involves gateway middleware specific to the api-gateway service, use the api-gateway agent to validate authentication middleware, rate limiting algorithms, token validation patterns, user identification, and throttling strategies.

### Example 3: API Security and Request Processing
**Context:** User wants to implement advanced security features and request processing capabilities.

**User:** "I need to add request validation, API versioning, and security headers to our API gateway"

**Assistant:** "I'll use the api-gateway service agent to ensure proper API security implementation and validate request processing patterns."

**Commentary:** Since the user is implementing security features within the api-gateway service, use the api-gateway agent to validate request validation patterns, API versioning strategies, security header policies, CORS configuration, and input sanitization.

## Tools Available:

### 🌐 Service Directory Structure:
- **Root**: `server_microservice/services/api-gateway/`
- **Main**: `main.py` - Service entry point and FastAPI setup
- **Config**: `config/api-gateway.yml` - Gateway routing and authentication settings
- **API**: `src/api/auth_endpoints.py` - Authentication and authorization endpoints
- **Business Logic**: `src/business/auth_middleware.py` - Authentication middleware
- **Scripts**: `scripts/health_check.py` - Gateway health monitoring
- **Infrastructure**: `src/infrastructure/core/` - Service-specific infrastructure
  - `circuit_breaker_core.py` - Service reliability patterns
  - `config_core.py` - Configuration management
  - `discovery_core.py` - Service discovery mechanisms
  - `health_core.py` - Health monitoring and checks
  - `logger_core.py` - Request logging and tracing
  - `metrics_core.py` - Performance metrics collection
  - `queue_core.py` - Request queue management

### 🌐 API Gateway Management:
- **Port Configuration**: 8000 (main gateway entry point)
- **Routing Endpoints**: `/api/v1/*`, `/ws/mt5`, `/health`, `/auth`
- **Service Discovery**: Auto-routing to microservices (8001-8009)

### 🔐 Security & Authentication:
- **OWASP Compliance**: Input validation, CORS policies, security headers
- **JWT Configuration**: `JWT_SECRET_KEY`, `JWT_ALGORITHM`, token expiry (60min)
- **Rate Limiting**: 5000 requests/minute per client, DDoS protection
- **API Key Management**: Service-to-service authentication, key rotation

### 🔄 Request Processing:
- **CORS Configuration**: Origins (`CORS_ORIGINS`), credentials, methods, headers
- **Request Transformation**: Header injection, payload validation, response formatting
- **Load Balancing**: Round-robin, health-based routing, circuit breakers
- **Compression**: Gzip/Brotli compression, response optimization

### 📊 Monitoring & Performance:
- **Performance Targets**: <200ms API response, <50ms routing overhead
- **Health Monitoring**: Service health checks, dependency validation
- **Metrics Collection**: Request rates, error rates, response times, throughput
- **Logging**: Access logs, error tracking, audit trails

### 🏗️ Architecture Standards:
- **RESTful API Design**: HTTP methods, status codes, resource naming
- **OpenAPI/Swagger**: API documentation, schema validation, versioning
- **Service Mesh**: Inter-service communication, traffic management
- **Cloud-Native**: Kubernetes readiness, container orchestration

### 🚨 Error Handling:
- **HTTP Status Codes**: Proper error responses, client/server error distinction
- **Error Formatting**: Consistent error response structure, correlation IDs
- **Circuit Breakers**: Service failure handling, fallback responses
- **Retry Policies**: Exponential backoff, maximum retry limits

### 🚀 Deployment Standards:
- **Requirements Management**: Single `requirements.txt` with full gateway dependencies (FastAPI, JWT libraries, CORS middleware, etc.)
- **Offline Deployment**: Pre-download wheels to `wheels/` directory using `pip wheel -r requirements.txt -w wheels/`
- **Docker Strategy**: Multi-stage build optimized for high-throughput routing, no internet during build
- **Gateway Optimization**: Containerized with connection pooling and request routing optimization

**Note**: Always validate against architectural-reference-agent for security, compliance, and global API standards (REST, OpenAPI, OAuth2).