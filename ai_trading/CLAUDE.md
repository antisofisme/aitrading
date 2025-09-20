# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🏗️ **PROJECT ARCHITECTURE OVERVIEW**

This is a **sophisticated AI-powered trading platform** with multiple applications and architectures:

### **🎯 APPLICATION STRUCTURE**

**CRITICAL: Understand which application you're working on before starting any task.**

1. **`server_microservice/`** - Modern microservices architecture (PRIMARY DEVELOPMENT TARGET)
   - 11 independent services with per-service infrastructure
   - Ports: 8000-8010 (api-gateway, data-bridge, performance-analytics, ai-orchestration, deep-learning, ai-provider, ml-processing, trading-engine, database-service, user-service, strategy-optimization)

2. **`server_side/`** - Legacy monolithic application 
   - Traditional centralized architecture 
   - **DO NOT modify when working on microservices**

3. **`client_side/`** - MT5 bridge client for real-time market data
   - WebSocket integration with server microservices
   - MetaTrader 5 connectivity

4. **`frontend/`** - Next.js 15 dashboard application
   - Real-time trading analytics and portfolio management

### **🔥 CRITICAL MICROSERVICE RULES**

**When working on microservices:**
- ✅ **ONLY WORK IN**: `server_microservice/services/[service-name]/`
- ✅ **PER-SERVICE INFRASTRUCTURE**: Each service has its own centralized infrastructure
- ✅ **SERVICE INDEPENDENCE**: No shared dependencies between services
- ❌ **NEVER REFERENCE**: server_side/ infrastructure from microservices

## 🚀 **COMMON COMMANDS**

### **Development Environment Setup**

```bash
# Quick development start (all microservices)
cd server_microservice
docker-compose up -d --build

# Production deployment
docker-compose -f docker-compose.prod.yml up -d --build

# Health check all services
for port in {8000..8009}; do
  curl -f http://localhost:$port/health || echo "Service on port $port not responding"
done
```

### **Individual Service Development**

```bash
# Work on specific service
cd server_microservice/services/data-bridge

# Local development (with hot reload)
pip install -r requirements.txt
export PYTHONPATH="./src"
python main.py

# Service-specific container build
docker-compose up -d --build data-bridge
```

### **Frontend Development**

```bash
cd frontend
npm install
npm run dev              # Development with Turbo
npm run build           # Production build
npm run lint           # Code linting
```

### **Client Bridge Testing**

```bash
cd client_side
# Ensure MetaTrader 5 is running on Windows
python src/presentation/cli/hybrid_bridge.py
```

### **Testing and Validation**

```bash
# Test all microservice infrastructure
python test_all_services_infra.py

# Comprehensive service health check
cd server_microservice
curl http://localhost:8008/api/v1/schemas/clickhouse  # Database schemas
curl http://localhost:8001/api/v1/ws/mt5/status      # MT5 WebSocket status
```

## 🏛️ **HIGH-LEVEL ARCHITECTURE**

### **Microservice Architecture Pattern**

Each of the 9 microservices follows a standardized structure:

```
services/[service-name]/
├── main.py                    # FastAPI application entry
├── Dockerfile                 # Multi-stage container build
├── requirements.txt           # Tiered dependencies
├── src/
│   ├── api/                  # REST endpoints
│   ├── business/             # Domain logic
│   ├── models/               # Data models
│   ├── infrastructure/       # Per-service centralized framework
│   │   ├── core/            # CoreLogger, CoreConfig, CoreErrorHandler
│   │   ├── base/            # Abstract interfaces
│   │   └── optional/        # EventCore, ValidationCore, CacheCore
│   └── [domain-specific]/    # Service business modules
```

### **Per-Service Centralization Pattern**

**CRITICAL**: Each service implements its own infrastructure layer to ensure independence:

- **CoreLogger**: Service-specific JSON logging with context
- **CoreConfig**: Environment-aware configuration management  
- **CoreErrorHandler**: Service-scoped error handling
- **CorePerformance**: Performance tracking and metrics
- **CoreCache**: Service-level caching with TTL
- **EventCore**: Service event publishing
- **ValidationCore**: Business rules validation

### **Data Flow Architecture**

1. **Real-time Pipeline**: MT5 Client → Data Bridge (8001) → WebSocket → Frontend
2. **AI Decision Engine**: Market Data → AI Orchestration (8003) → AI Provider (8005) → Trading Signals
3. **ML Processing**: Historical Data → ML Processing (8006) → Deep Learning (8004) → Model Training
4. **Data Persistence**: All Services → Database Service (8008) → Multi-DB Stack

### **Database Stack Architecture**

- **PostgreSQL**: User authentication, session management (14 tables)
- **ClickHouse**: High-frequency trading data, analytics (11 tables) 
- **DragonflyDB**: High-performance caching layer
- **Weaviate**: Vector database for AI/ML embeddings
- **ArangoDB**: Graph database for complex relationships

### **Service Communication**

- **HTTP/REST**: Synchronous service-to-service communication
- **WebSocket**: Real-time data streaming (MT5, frontend updates)
- **Event Publishing**: Asynchronous service notifications
- **Docker Network**: Service discovery via container networking

## 🔧 **DEVELOPMENT WORKFLOW**

### **Before Starting Any Task**

1. **Identify Target Application**: 
   - Check if path contains `server_microservice/` vs `server_side/`
   - Determine which specific service you're modifying

2. **Scan Project Structure**:
   ```bash
   # Understand service boundaries
   ls server_microservice/services/[service-name]/src/
   
   # Check existing infrastructure
   ls server_microservice/services/[service-name]/src/infrastructure/
   ```

3. **Verify Service Health**:
   ```bash
   curl http://localhost:800X/health  # Replace X with service port
   ```

### **Service Development Rules**

- ✅ **Edit existing files** - Never create duplicates (backup_, v2_, new_)
- ✅ **Use service infrastructure** - Always use CoreLogger, CoreConfig, etc.
- ✅ **Cache dependencies** - Use pre-downloaded wheels for Docker builds
- ❌ **No cross-service dependencies** - Services must be completely independent
- ❌ **No fallback patterns** - Service infrastructure must work, fail fast if not

### **Performance Optimization Principles**

- **Docker Layer Caching**: Dependencies → Application Code → Production
- **Tiered Requirements**: Core (50MB) → Database (200MB) → AI (500MB) → Advanced (2GB) → Heavy ML (4GB)
- **Offline-First**: Pre-download wheels for faster builds
- **Service-Specific Builds**: Only build changed services

## 🔍 **DEBUGGING PROTOCOL**

### **Systematic Debugging Approach**

1. **Health Checks First**:
   ```bash
   docker-compose ps                    # Check container status
   curl http://localhost:8000/health   # API Gateway health
   curl http://localhost:8008/health   # Database service health
   ```

2. **End-to-End Data Flow Verification**:
   ```bash
   # Check WebSocket connectivity
   curl -H "Connection: Upgrade" -H "Upgrade: websocket" \
     http://localhost:8000/api/v1/ws/mt5
   
   # Verify database schemas
   curl http://localhost:8008/api/v1/schemas/clickhouse
   curl http://localhost:8008/api/v1/schemas/postgresql
   ```

3. **Service Logs Analysis**:
   ```bash
   docker logs service-[service-name] --tail 50
   ```

4. **Never Assume - Always Verify**:
   - Check actual table schemas, not documentation
   - Verify environment variables are loaded
   - Confirm service-to-service connectivity

## 🚀 **DEPLOYMENT STRATEGIES**

### **Development (Fast Iteration)**
```bash
docker-compose up -d --build        # 30 seconds with cached wheels
```

### **Production (Zero Downtime)**
```bash
docker-compose -f docker-compose.prod.yml up -d --build --remove-orphans
timeout 60 bash -c 'until curl -f http://localhost:8000/health; do sleep 5; done'
```

### **Service-Specific Deployment**
```bash
docker-compose up -d --build data-bridge  # Deploy single service
```

## 📊 **PERFORMANCE BENCHMARKS**

- **Service Startup**: 6 seconds (90% improvement from optimization)
- **Container Builds**: 30 seconds to 15 minutes based on service complexity
- **WebSocket Throughput**: 5000+ messages/second
- **Database Operations**: 100x improvement via connection pooling
- **Memory Usage**: 95% reduction through optimization
- **Cache Hit Rates**: 85%+ across services

## 🎯 **SERVICE-SPECIFIC NOTES**

### **API Gateway (8000)**
- Entry point for all requests
- Authentication, rate limiting, CORS
- Routes to appropriate services

### **Data Bridge (8001)**  
- MT5 WebSocket integration
- Real-time tick data processing (18 ticks/second achieved)
- Market data normalization

### **AI Orchestration (8003) & AI Provider (8005)**
- OpenAI, DeepSeek, Google AI integration
- Langfuse for AI observability
- LangChain workflow orchestration

### **ML Processing (8006) & Deep Learning (8004)**
- Traditional ML and neural networks
- Model training and inference
- Feature engineering pipelines

### **Trading Engine (8007)**
- Core trading logic and strategy execution
- Risk management and order placement
- Performance-critical service

### **Database Service (8008)**
- Multi-database abstraction layer
- Schema management for all databases
- Connection pooling and optimization

### **User Service (8009)**
- User authentication and authorization
- Session management
- Enterprise user features

## 🔧 **CONFIGURATION MANAGEMENT**

### **Environment Variables**
- Service-specific `.env` files
- Docker Compose environment sections
- CoreConfig for runtime configuration management

### **Key Environment Categories**
- **AI APIs**: OpenAI, DeepSeek, Google AI keys
- **Database**: Connection strings and credentials
- **MT5**: Account login, password, server
- **Service**: Port configurations, debug flags
- **Security**: CORS, authentication settings

## 📁 **IMPORTANT FILES AND DIRECTORIES**

- **`docker-compose.yml`**: Development orchestration
- **`docker-compose.prod.yml`**: Production deployment
- **`.env.example`**: Environment variable template
- **`server_microservice/services/`**: All microservice implementations
- **`.claude/`**: Claude-specific configuration and MCP tools
- **`frontend/src/`**: Next.js dashboard application
- **`client_side/src/`**: MT5 bridge client

## ⚠️ **CRITICAL REMINDERS**

1. **Architecture Isolation**: Never mix server_side and server_microservice patterns
2. **Service Independence**: Each microservice must be completely self-contained
3. **Infrastructure Consistency**: Always use service-specific CoreLogger, CoreConfig, etc.
4. **Performance First**: Use cached dependencies, optimize Docker layers
5. **Real Testing**: Use actual MT5 connections and real data flows
6. **Fail Fast**: Service infrastructure must work - no fallback patterns

---

**Last Updated**: 2025-01-09
**Version**: 3.0 - Comprehensive Architecture Documentation
**Status**: ACTIVE - PRODUCTION READY MICROSERVICE PLATFORM