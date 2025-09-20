# AI Orchestration Service - Architecture Documentation

## Service Overview
The AI Orchestration Service is a unified microservice that coordinates multiple AI components for comprehensive workflow management. It serves as the central hub for AI operations within the Neliti trading platform.

## Architecture Principles

### 1. Microservice Architecture
- **Service Independence**: Each AI component is independently manageable
- **Service Isolation**: Per-service centralization with no cross-dependencies
- **Service Scalability**: Individual components can scale based on demand

### 2. Centralized Infrastructure Pattern
- **Per-Service Centralization**: Each service maintains its own infrastructure layer
- **Infrastructure Components**: Logging, configuration, performance tracking, error handling
- **Event-Driven Architecture**: All components publish lifecycle events

### 3. AI Component Integration
- **Unified Interface**: Single API for multiple AI services
- **Component Orchestration**: Coordinated execution across AI providers
- **Observability**: Comprehensive monitoring and tracing

## Core Components

### 1. Handit AI Client (`handit_client.py`)
**Purpose**: Specialized AI task execution with domain-specific models

**Capabilities:**
- 12+ specialized AI models (forex, crypto, stocks, etc.)
- Task priority management
- Performance optimization with caching
- Memory-bounded task history

**Key Features:**
- Task Types: Financial analysis, trading signals, risk assessment
- Model Specialties: Forex, commodities, crypto specialists
- Priority Queue: 5-level priority system (LOW to CRITICAL)
- Caching: LRU cache for duplicate request optimization

### 2. Letta Memory Integration (`letta_integration.py`)
**Purpose**: Advanced memory management for AI agents

**Capabilities:**
- Persistent agent memory
- Session management
- Memory type classification (semantic, episodic, procedural)
- Memory retention policies

**Key Features:**
- Multi-agent memory isolation
- Memory search and retrieval
- Context-aware memory updates
- Memory lifecycle management

### 3. LangGraph Workflows (`langgraph_workflows.py`)
**Purpose**: Complex multi-step AI workflow execution

**Capabilities:**
- Workflow template management
- Sequential and parallel execution
- Checkpoint and recovery
- Workflow state management

**Key Features:**
- Pre-defined templates for trading analysis
- Dynamic workflow construction
- Error recovery and retry logic
- Workflow performance tracking

### 4. Langfuse Observability (`langfuse_client.py`)
**Purpose**: Comprehensive AI performance monitoring and tracing

**Capabilities:**
- Distributed tracing
- Performance metrics collection
- User session tracking
- AI interaction logging

**Key Features:**
- Real-time trace creation
- Metric aggregation
- Performance analytics
- Observability dashboards

### 5. Agent Coordinator (`agent_coordinator.py`)
**Purpose**: Multi-agent coordination and communication management

**Capabilities:**
- Agent registration and lifecycle
- Message routing and priority
- Task coordination strategies
- Agent health monitoring

**Key Features:**
- Priority-based message queuing
- Sequential and parallel coordination
- Agent performance metrics
- Health score tracking

### 6. Task Scheduler (`task_scheduler.py`)
**Purpose**: Background task management and execution

**Capabilities:**
- Scheduled task execution
- Task retry logic
- Queue management
- Resource optimization

### 7. Monitoring Orchestrator (`monitoring_orchestrator.py`)
**Purpose**: Unified monitoring across all AI components

**Capabilities:**
- Health check aggregation
- Performance metric collection
- Alert management
- Dashboard data preparation

## Service Infrastructure

### 1. Centralized Infrastructure Layer

#### Base Infrastructure (`src/infrastructure/base/`)
- **BaseLogger**: Structured logging foundation
- **BaseConfig**: Configuration management base
- **BaseErrorHandler**: Error handling patterns
- **BasePerformance**: Performance tracking base
- **BaseCache**: Caching infrastructure base
- **BaseResponse**: Response standardization

#### Core Infrastructure (`src/infrastructure/core/`)
- **CoreLogger**: Production-ready logging with JSON formatting
- **CoreConfig**: Environment-aware configuration management
- **CoreErrorHandler**: Comprehensive error classification and handling
- **CorePerformance**: Advanced performance tracking and metrics
- **CoreCache**: Redis-compatible caching with TTL management
- **CoreResponse**: Standardized API response formatting

#### Optional Infrastructure (`src/infrastructure/optional/`)
- **EventCore**: Event publishing and subscription
- **ValidationCore**: Data validation and schema checking
- **ContainerCore**: Dependency injection container
- **FactoryCore**: Object creation and lifecycle management

### 2. Configuration Management

#### Centralized Configuration (`config/ai-orchestration.yml`)
- **Service Settings**: Port, debug, environment configuration
- **AI Services**: Configuration for all 4 AI components
- **Performance Settings**: Caching, concurrency, timeout configuration
- **Security Settings**: Authentication, rate limiting, IP restrictions
- **Monitoring Settings**: Health checks, metrics, observability levels

#### Environment Variables (`.env.example`)
- **Service Configuration**: 20+ environment variables
- **AI Provider Configuration**: API keys, endpoints, timeouts
- **Performance Tuning**: Concurrency limits, cache settings
- **Security Configuration**: JWT secrets, API keys

### 3. Performance Optimization

#### Memory Management
- **Bounded Collections**: Limited task history (500 entries)
- **LRU Caches**: Task results (100 entries), completed tasks (1000 entries)
- **Memory Cleanup**: Automatic cleanup of old data
- **Garbage Collection**: Periodic cleanup of expired entries

#### Caching Strategy
- **Multi-Level Caching**: Task cache, response cache, configuration cache
- **TTL Management**: Configurable time-to-live for different data types
- **Cache Keys**: Deterministic hashing for duplicate detection
- **Cache Metrics**: Hit/miss ratio tracking

#### Concurrency Management
- **Async/Await**: Non-blocking I/O operations
- **Task Queues**: Priority-based task scheduling
- **Connection Pools**: Optimized external service connections
- **Resource Limits**: Configurable concurrency limits

## API Architecture

### 1. REST API Design
- **RESTful Endpoints**: Standard HTTP methods and status codes
- **Consistent Response Format**: Standardized success/error responses
- **Request Validation**: Comprehensive input validation
- **Error Handling**: Centralized error response formatting

### 2. Endpoint Categories

#### Health & Monitoring
- `GET /health`: Basic health check
- `GET /status`: Detailed service status
- `GET /metrics`: Performance and usage metrics

#### AI Orchestration
- `POST /api/v1/orchestration/execute`: Unified AI operation execution
- `GET /api/v1/orchestration/workflows`: Active workflow management

#### Task Management
- `POST /api/v1/ai-orchestration/tasks`: Create AI tasks
- `GET /api/v1/ai-orchestration/tasks`: List and filter tasks
- `GET /api/v1/ai-orchestration/tasks/{id}`: Get task details
- `DELETE /api/v1/ai-orchestration/tasks/{id}`: Cancel tasks

#### System Information
- `GET /api/v1/ai-orchestration/models`: Available AI models
- `GET /api/v1/ai-orchestration/capabilities`: Service capabilities

## Data Flow Architecture

### 1. Request Processing Flow
```
Client Request → API Gateway → Validation → AI Component Router → Task Execution → Response Formatting → Client Response
```

### 2. AI Component Coordination Flow
```
Orchestration Request → Component Selection → Parallel/Sequential Execution → Result Aggregation → Response Delivery
```

### 3. Event Flow
```
Component Operation → Event Publishing → Event Manager → External Subscribers → Monitoring Systems
```

### 4. Error Handling Flow
```
Error Occurrence → Error Classification → Centralized Handler → Logging → Response Formatting → Client Notification
```

## Deployment Architecture

### 1. Container Strategy
- **Multi-Stage Dockerfile**: Optimized build process
- **Tiered Dependencies**: Progressive dependency loading
- **Production Optimization**: Security and performance hardening

### 2. Resource Requirements
- **CPU**: 4 cores (recommended)
- **Memory**: 8GB RAM (with AI models)
- **Port**: 8003 (configurable)
- **Dependencies**: Python 3.11+, Redis (optional)

### 3. Scaling Strategy
- **Horizontal Scaling**: Multiple service instances
- **Load Balancing**: Request distribution
- **Resource Isolation**: Per-instance resource limits
- **Health Checks**: Automated instance monitoring

## Security Architecture

### 1. Authentication & Authorization
- **API Key Authentication**: Optional API key validation
- **JWT Token Support**: Session-based authentication
- **Role-Based Access**: Future enhancement for user roles

### 2. Data Protection
- **Environment Variables**: Secure credential management
- **Configuration Encryption**: Sensitive data protection
- **Input Validation**: Comprehensive request validation
- **Output Sanitization**: Safe response formatting

### 3. Network Security
- **CORS Configuration**: Cross-origin request control
- **Rate Limiting**: Request frequency control
- **IP Restrictions**: Optional IP-based access control
- **HTTPS Support**: Secure communication protocols

## Monitoring & Observability

### 1. Metrics Collection
- **Performance Metrics**: Response times, throughput, error rates
- **Business Metrics**: Task completion rates, AI model usage
- **Resource Metrics**: Memory usage, CPU utilization
- **Custom Metrics**: Component-specific measurements

### 2. Logging Strategy
- **Structured Logging**: JSON-formatted log entries
- **Contextual Logging**: Request correlation and tracing
- **Log Levels**: Configurable verbosity (DEBUG to CRITICAL)
- **Log Aggregation**: Centralized log collection

### 3. Tracing & Observability
- **Distributed Tracing**: Cross-component request tracking
- **Performance Profiling**: Code-level performance analysis
- **Error Tracking**: Comprehensive error monitoring
- **Health Monitoring**: Automated health checks

## Future Architecture Enhancements

### 1. Planned Improvements
- **WebSocket Support**: Real-time workflow updates
- **GraphQL API**: Flexible query interface
- **Message Queue Integration**: Asynchronous processing
- **Circuit Breaker Pattern**: Fault tolerance enhancement

### 2. Scalability Enhancements
- **Database Integration**: Persistent state management
- **Caching Layer**: Redis/Memcached integration
- **Service Mesh**: Advanced microservice networking
- **Auto-Scaling**: Dynamic resource adjustment

### 3. AI Enhancements
- **Model Versioning**: AI model lifecycle management
- **A/B Testing**: Model performance comparison
- **Custom Models**: User-defined AI model integration
- **Federated Learning**: Distributed model training

This architecture provides a solid foundation for scalable, maintainable AI orchestration with comprehensive observability and performance optimization.