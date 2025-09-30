# 🏗️ Suho Trading System - Core Infrastructure

**Version**: 3.0.0
**Status**: Production Ready
**Architecture**: Centralized Configuration Management + Offline Package System

## 📋 **Overview**

This is the core infrastructure layer of the Suho AI Trading System, implementing a **2-service optimized architecture** with centralized configuration management.

### **Architecture Principles**
- ✅ **Central Hub**: Single source of truth for all configurations
- ✅ **API Gateway**: Protocol handling and routing only
- ❌ **Component Manager**: Removed (redundant functionality)
- 🔄 **Hot Reload**: Handled by Central Hub
- 📊 **Monitoring**: Centralized health aggregation

## 🏭 **Services Overview**

### **1. Central Hub** `/central-hub/`
**Primary Role**: Configuration coordinator and service orchestration

**Responsibilities:**
- 🎛️ Configuration management (static + hot-reload)
- 🔍 Service discovery and registration
- 📈 Health monitoring aggregation
- 🧩 Component versioning and distribution
- 💾 Database connection management
- 📡 NATS/Kafka coordination

**Key APIs:**
```bash
GET  /health          # Health aggregation
POST /config          # Get service configuration
POST /discovery       # Service registration
GET  /metrics         # Performance metrics
```

### **2. API Gateway** `/api-gateway/`
**Primary Role**: Protocol gateway and request routing

**Responsibilities:**
- 🌐 HTTP/WebSocket protocol handling
- 🔀 Intelligent request routing
- 🔒 JWT authentication & authorization
- 📊 Suho Binary Protocol ↔ Protobuf conversion
- 🏷️ Multi-tenant request isolation
- ⚡ Rate limiting and CORS management

**Key Features:**
```bash
Port 8000: HTTP API Server
Port 8001: Trading WebSocket Channel
Port 8002: Price Stream WebSocket Channel
```

## 🔧 **Configuration Management**

### **Centralized Configuration Flow**
```
Central Hub (Master Config)
    ↓ HTTP API
API Gateway (Requests Config)
    ↓ Cache + Fallback
Service Operation
```

### **Configuration Types**

#### **Static Configuration** (Secure, DB credentials)
```python
# Central Hub manages
database_credentials = {
    "postgresql": "postgresql://...",
    "dragonflydb": "redis://...",
    "kafka": "kafka://..."
}
```

#### **Hot-Reload Configuration** (Business rules)
```python
# Central Hub distributes via NATS
business_rules = {
    "rate_limits": {"max_requests": 1000},
    "cors_origins": ["*.suho.io"],
    "jwt_settings": {"expires_in": "24h"}
}
```

## 🚀 **Deployment**

### **Development Environment**
```bash
# Start all infrastructure services
docker-compose up -d

# Services will be available:
# - Central Hub: http://localhost:7000
# - API Gateway: http://localhost:8000
# - WebSocket Trading: ws://localhost:8001/ws/trading
# - WebSocket Price Stream: ws://localhost:8002/ws/price-stream
```

### **Service Dependencies**
```
Databases (PostgreSQL, ClickHouse, DragonflyDB, Weaviate, ArangoDB)
    ↓
Message Brokers (NATS, Kafka + Zookeeper)
    ↓
Central Hub (Configuration coordination)
    ↓
API Gateway (Request handling)
```

## 📊 **Database Stack**

| Database | Purpose | Port | Use Case |
|----------|---------|------|----------|
| **PostgreSQL + TimescaleDB** | Primary OLTP + Time Series | 5432 | Trading data, user management |
| **ClickHouse** | OLAP Analytics | 8123 | Real-time analytics, reporting |
| **DragonflyDB** | High-performance Cache | 6379 | Session cache, rate limiting |
| **Weaviate** | Vector Database | 8080 | AI/ML feature storage |
| **ArangoDB** | Multi-model Graph | 8529 | Relationship mapping |

## 🌐 **Message Transport**

| Transport | Purpose | Port | Use Case |
|-----------|---------|------|----------|
| **NATS** | Real-time messaging | 4222 | Configuration updates, hot-reload |
| **Kafka** | Durable streaming | 9092 | Trading signals, audit logs |
| **WebSocket** | Client connections | 8001/8002 | MT5 client communication |

## 🔐 **Security Architecture**

### **Authentication Flow**
```
Client Request → API Gateway → JWT Validation → Service Routing
```

### **Multi-tenant Isolation**
```
tenant_id validation → Service boundary enforcement → Database isolation
```

## 📈 **Performance Targets**

- **API Gateway Response**: <5ms routing decision
- **Central Hub Config**: <3ms configuration lookup
- **Database Operations**: <10ms average query time
- **WebSocket Latency**: <1ms binary protocol handling

## 🔄 **Hot Reload Architecture**

### **Configuration Update Flow**
```
Admin Update → Central Hub → NATS Broadcast → API Gateway → Live Apply
```

**Supported Hot-Reload Changes:**
- ✅ Business rules (rate limits, CORS)
- ✅ JWT settings (expiry, audience)
- ✅ Component versions
- ❌ Database credentials (requires restart)
- ❌ Core infrastructure settings

## 🧪 **Testing**

### **Integration Testing**
```bash
# Test Central Hub configuration API
curl -X POST http://localhost:7000/config \
  -H "Content-Type: application/json" \
  -d '{"service_name": "api-gateway"}'

# Test API Gateway health
curl http://localhost:8000/health
```

### **Performance Testing**
```bash
# Load test API Gateway
ab -n 1000 -c 50 http://localhost:8000/health

# Test WebSocket connections
wscat -c ws://localhost:8001/ws/trading
```

## 📝 **Migration Notes**

### **Changes from v1.0**
- ❌ **Removed**: Component Manager service (redundant)
- ✅ **Enhanced**: Central Hub with component management
- 🔄 **Updated**: API Gateway to use centralized config
- 📁 **Reorganized**: Documentation structure

### **Breaking Changes**
- Component Manager URLs no longer available
- Configuration now fetched from Central Hub
- Hot-reload mechanism simplified

## 🚨 **Troubleshooting**

### **Common Issues**

#### **API Gateway Cannot Start**
```bash
# Check Central Hub connectivity
curl http://localhost:7000/health

# Verify configuration API
curl -X POST http://localhost:7000/config \
  -d '{"service_name": "api-gateway"}'
```

#### **Configuration Not Loading**
```bash
# Check Central Hub logs
docker logs suho-central-hub

# Verify NATS connectivity
docker logs suho-nats-server
```

#### **Database Connection Issues**
```bash
# Check database health
docker ps | grep suho-postgresql
docker logs suho-postgresql
```

## 📚 **Documentation Index**

- **System Architecture**: `SYSTEM_ARCHITECTURE.md`
- **Configuration Management**: `central-hub/config/CONFIG_SUMMARY.md`
- **API Specifications**: `_archived/old-docs/` (legacy)
- **Database Schemas**: `central-hub/config/database/`

## 🤝 **Contributing**

1. **Configuration Changes**: Update Central Hub configs
2. **Service Changes**: Follow centralized config patterns
3. **Testing**: Ensure integration tests pass
4. **Documentation**: Update relevant README sections

## 📄 **License**

Suho Trading System - Internal Use Only
© 2024 Suho Technologies