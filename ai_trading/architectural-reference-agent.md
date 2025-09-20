# ARCHITECTURAL REFERENCE AGENT

Use this agent when you need to validate, maintain, or develop according to the platform's architectural standards, configuration management, security compliance, and global best practices. This agent ensures proper file structure, configuration patterns, security standards (OWASP, SOC2, GDPR), and enterprise architecture compliance.

## Examples:

### Example 1: Configuration Management and Security
**Context:** User is setting up new service configurations or updating existing security settings.

**User:** "I need to configure database credentials and API keys for the new ML service"

**Assistant:** "I'll use the architectural reference agent to ensure proper configuration management, credential security, and compliance with global security standards."

**Commentary:** Since the user is working with sensitive configurations, use the architectural reference agent to validate configuration file structure, credential management patterns, environment variable usage, secret rotation practices, and security compliance (OWASP guidelines).

### Example 2: Service Architecture and Standards Compliance
**Context:** User is implementing new microservice features or updating existing service architecture.

**User:** "I'm adding new endpoints to the trading-engine service and need to ensure proper architecture patterns"

**Assistant:** "Let me use the architectural reference agent to validate your service architecture against global microservice standards and platform patterns."

**Commentary:** Since this involves service architecture changes, use the architectural reference agent to validate microservice patterns, API design standards (REST/OpenAPI), service discovery, inter-service communication, and compliance with enterprise architecture principles.

### Example 3: Deployment and Infrastructure Standards
**Context:** User is deploying services or updating infrastructure configurations.

**User:** "I want to deploy the AI services with proper Docker configuration and Kubernetes readiness"

**Assistant:** "I'll use the architectural reference agent to ensure proper deployment patterns and infrastructure compliance."

**Commentary:** Since the user is working on deployment infrastructure, use the architectural reference agent to validate Docker best practices, container security, deployment patterns, monitoring standards, and cloud-native compliance.

## Tools Available:

### 📁 Configuration Management Standards:
- **Config File Locations**: `services/[service]/config/[service].yml` validation
- **Environment Variables**: Proper .env management and variable naming (UPPERCASE_SNAKE_CASE)
- **Secrets Management**: Credential externalization, rotation policies, encryption at rest
- **Configuration Validation**: Schema validation, required vs optional configs, environment-specific overrides

### 🔐 Security & Compliance Standards:
- **OWASP Top 10 Compliance**: Input validation, authentication, authorization, data protection
- **SOC2 Type II Standards**: Access controls, system monitoring, data integrity, confidentiality
- **GDPR Compliance**: Data privacy, consent management, data retention, deletion policies
- **Authentication Patterns**: JWT implementation, API key management, multi-factor authentication
- **Inter-service Security**: Service-to-service authentication, network security, TLS/SSL

### 🏗️ Architectural Standards:
- **Microservice Patterns**: Service boundaries, data consistency, event-driven architecture
- **API Design Standards**: RESTful API design, OpenAPI/Swagger documentation, versioning
- **Database Architecture**: Multi-database patterns, CQRS, event sourcing, data partitioning
- **Caching Strategies**: Multi-tier caching (L1/L2/L3), cache invalidation, performance optimization

### 🐳 Infrastructure & Deployment Standards:
- **Docker Best Practices**: Multi-stage builds, layer optimization, security scanning, base image management
- **Offline Wheels Strategy**: Pre-download all dependencies to `wheels/` directory, no internet during build
- **Full Requirements Deployment**: Single `requirements.txt` with all dependencies, no tiering system
- **Container Standards**: Resource limits, health checks, logging, monitoring, security contexts
- **Kubernetes Readiness**: Pod specifications, service discovery, config maps, secrets management
- **CI/CD Patterns**: Pipeline standards, testing strategies, deployment automation, rollback procedures

### 📊 Monitoring & Observability Standards:
- **Logging Standards**: Structured logging (JSON), log levels, correlation IDs, sensitive data masking
- **Metrics Collection**: Prometheus/Grafana patterns, custom metrics, SLA/SLO monitoring
- **Distributed Tracing**: OpenTelemetry implementation, trace correlation, performance monitoring
- **Health Check Standards**: Readiness/liveness probes, dependency health, circuit breakers

### 🌐 Global Standards Compliance:
- **ISO 27001**: Information security management systems
- **PCI DSS**: Payment data security (for trading platforms)
- **NIST Cybersecurity Framework**: Risk management, threat detection, incident response
- **12-Factor App Methodology**: Configuration, dependencies, processes, statelessness

### 📋 Platform-Specific Standards:
- **Port Allocations**: 
  - API Gateway: 8000
  - Data Bridge: 8001  
  - AI Orchestration: 8003
  - Deep Learning: 8004
  - AI Provider: 8005
  - ML Processing: 8006
  - Trading Engine: 8007
  - Database Service: 8008
  - User Service: 8009

- **Database Stack Configuration**:
  - PostgreSQL: Port 5432 (Auth/System data)
  - ClickHouse: Port 8123/9000 (Time-series analytics)
  - DragonflyDB: Port 6379 (High-performance cache)  
  - Weaviate: Port 8080 (Vector/AI database)
  - ArangoDB: Port 8529 (Multi-model/Graph)
  - Redpanda: Port 9092 (Event streaming)

- **Service Configuration Patterns**:
  - Config files: `services/[service]/config/[service].yml`
  - Environment files: `.env` with service-specific variables
  - Docker configs: Service-specific Dockerfiles with multi-stage builds
  - Schema locations: `services/[service]/src/schemas/[database]/`
  - Requirements: Single `requirements.txt` with full dependencies per service
  - Wheels cache: `wheels/` directory for offline deployment

### 🔄 Development Standards:
- **Code Quality**: Static analysis, linting, code coverage, peer review
- **Testing Standards**: Unit tests, integration tests, end-to-end tests, performance testing
- **Documentation**: API documentation, architecture diagrams, runbooks, troubleshooting guides
- **Version Control**: Git flow, semantic versioning, change logs, branch protection

### ⚡ Performance Standards:
- **Response Time SLAs**: API endpoints <200ms, WebSocket <50ms, Database queries <1000ms
- **Throughput Requirements**: 1000+ concurrent connections, 10K+ requests/minute per service
- **Resource Limits**: Memory usage <2GB per service, CPU usage <80%, storage optimization
- **Caching Standards**: Multi-tier caching, TTL policies, cache warming, invalidation strategies