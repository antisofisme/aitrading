# Central Hub Service

## 🎯 Purpose
**Centralized coordination and database service integration hub** yang handle service discovery, health monitoring, database connections, dan system-wide coordination untuk semua backend services dalam Docker ecosystem.

---

## 📊 ChainFlow Diagram

```
Service A ──query──→ Central Hub ──response──→ Service A
    ↓                     ↓                        ↓
Direct Call          Discovery Only           Direct Call
    ↓                     ↓                        ↓
Service B ←─────────────────────────────────────────┘

Database Integration Flow:
Services ──discover──→ Central Hub ──connections──→ Database Cluster
    ↓                       ↓                          ↓
PostgreSQL             Service Registry         TimescaleDB
DragonflyDB           Health Monitor           ClickHouse
Kafka/NATS            Connection Pool          Weaviate

✅ COORDINATION PATTERN (NOT PROXY):
1. Service A queries Central Hub: "Where is Service B?"
2. Central Hub responds: "Service B is at http://service-b:8080"
3. Service A calls Service B directly
4. Central Hub manages database connections for all services

Shared Resources: Schemas, Utils, ErrorDNA, Circuit Breakers
```

---

## 🏗️ Central Hub Architecture

### **Database Service Integration** (Core Function)
**Function**: Centralized database connection management and service registry
**Usage**: All services connect through Central Hub for database access
**Performance**: <2ms service discovery, <5ms database connection routing

### **Runtime Coordination** (Service-based)
**Function**: Real-time service coordination dan monitoring
**Usage**: Runtime service discovery, health checks, load balancing
**Performance**: <2ms coordination response time (part of <30ms total system budget)

### **Static Resources** (Import/Library-based)
**Function**: Shared components yang di-import oleh services
**Usage**: Compile-time dependencies, static schema generation
**Performance**: No runtime overhead, optimal untuk high-frequency trading

---

## 📁 Service Structure

```
central-hub/
├── shared/                   # ✅ SHARED LIBRARY COMPONENTS (Import-based)
│   ├── config/              # Configuration management
│   ├── logging/             # Centralized logging utilities
│   ├── monitoring/          # Performance monitoring
│   ├── proto/               # Protocol Buffer definitions
│   ├── security/            # Security and authentication
│   ├── transfer/            # Data transfer protocols
│   └── utils/               # Shared utilities and patterns
├── service/                  # ✅ CENTRAL HUB SERVICE (Docker Container)
│   ├── api/                 # REST API endpoints
│   │   ├── discovery.py     # Service discovery endpoints
│   │   ├── health.py        # Health check endpoints
│   │   └── metrics.py       # Metrics and monitoring
│   ├── core/                # Core service functionality
│   ├── config/              # Service configuration
│   ├── app.py               # Main FastAPI application
│   └── app_minimal.py       # Minimal startup for development
├── Dockerfile               # Docker container configuration
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

---

## 🐳 Docker Deployment

### **Production Deployment**

Central Hub runs as a **separate Docker container** that connects to database services:

```bash
# Build Central Hub image
cd central-hub
docker build -t central-hub:latest .

# Deploy Central Hub with database connections
docker run -d \
  --name suho-central-hub \
  --network suho-trading-network \
  -p 7000:7000 \
  -e POSTGRES_HOST=suho-postgresql \
  -e POSTGRES_PORT=5432 \
  -e POSTGRES_DB=suho_trading \
  -e POSTGRES_USER=suho_admin \
  -e POSTGRES_PASSWORD=suho_secure_password_2024 \
  -e DRAGONFLY_HOST=suho-dragonflydb \
  -e DRAGONFLY_PORT=6379 \
  -e DRAGONFLY_PASSWORD=dragonfly_secure_2024 \
  -e KAFKA_BROKERS=suho-kafka:9092 \
  -e NATS_URL=nats://suho-nats-server:4222 \
  central-hub:latest
```

### **Connected Database Services**

Central Hub integrates with the following services (deployed via database-service docker-compose):

- **PostgreSQL** (TimescaleDB): Primary transactional database
- **DragonflyDB**: High-performance Redis-compatible cache
- **ClickHouse**: OLAP analytics database
- **Weaviate**: Vector database for AI/ML
- **ArangoDB**: Multi-model graph database
- **NATS**: Lightweight message broker
- **Kafka**: High-throughput message streaming

---

## 🚀 3 Transport Methods for Backend Communication

### **🚀 Transport Decision Matrix for Central Hub**

Central Hub coordinates all 3 transport methods and provides service discovery:

#### **Method 1: NATS+Kafka Hybrid (High Volume + Mission Critical)**
**Usage**: Service coordination for high-frequency trading data
**Services**: All services ← Central Hub coordination → Database cluster
**Architecture**: Central Hub manages dual transport routing

**NATS Transport**:
- **Subject**: `central-hub.discovery`, `central-hub.health`
- **Purpose**: Real-time service discovery (speed priority)
- **Latency**: <1ms

**Kafka Transport**:
- **Topic**: `central-hub-events`, `service-lifecycle`
- **Purpose**: Reliable service lifecycle events
- **Retention**: 3 days (critical for audit trail)

#### **Method 2: HTTP/REST (Standard Operations)**
**Usage**: Service discovery, health checks, configuration
**Services**: All backend services → Central Hub HTTP API
**Performance**: <2ms response time

**Endpoints**:
- `GET /api/discovery/{service_name}` - Service discovery
- `GET /health` - Health check
- `GET /metrics` - Service metrics
- `POST /api/discovery/register` - Service registration

#### **Method 3: gRPC (High-Performance Service Calls)**
**Usage**: Direct service communication after discovery
**Performance**: <1ms for local network calls
**Implementation**: Central Hub provides service addresses, services communicate directly

---

## 📊 Database Integration Features

### **Multi-Database Support**
- **PostgreSQL/TimescaleDB**: Primary OLTP + time-series data
- **ClickHouse**: High-performance analytics (OLAP)
- **DragonflyDB**: Redis-compatible caching layer
- **Weaviate**: Vector embeddings for AI features
- **ArangoDB**: Graph relationships and multi-model data

### **Connection Management**
- **Pool Management**: Optimized connection pooling per database
- **Health Monitoring**: Real-time database health checks
- **Failover Support**: Automatic failover for high availability
- **Performance Metrics**: Database query performance monitoring

### **Service Registry**
- **Automatic Discovery**: Services auto-register with Central Hub
- **Health Tracking**: Continuous health monitoring of all services
- **Load Balancing**: Intelligent routing based on service load
- **Circuit Breaker**: Fault tolerance for failed services

---

## 🚀 Performance & Monitoring

### **Key Metrics**
- **Service Discovery**: <2ms average response time
- **Database Connections**: <5ms connection establishment
- **Health Checks**: 30-second intervals
- **Memory Usage**: ~100MB baseline per container

### **Health Endpoints**
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed system health
- `GET /metrics` - Prometheus-compatible metrics
- `GET /metrics/health-summary` - System health summary

### **Logging & Monitoring**
- **Structured Logging**: JSON-formatted logs for all operations
- **Error Tracking**: Comprehensive error DNA for debugging
- **Performance Metrics**: Real-time performance monitoring
- **Database Metrics**: Connection pool and query performance

---

## 🔧 Development Setup

### **Local Development**
```bash
# Create virtual environment
cd central-hub
python -m venv venv_central
source venv_central/bin/activate  # Linux/Mac
# or venv_central\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run with auto-reload
cd service
PYTHONPATH=../shared:. uvicorn app:app --host 0.0.0.0 --port 7000 --reload
```

### **Docker Development**
```bash
# Build and run locally
docker build -t central-hub:dev .
docker run -p 7000:7000 central-hub:dev
```

---

## 🌐 Network Architecture

Central Hub operates in the `suho-trading-network` Docker network:

```
suho-trading-network (Docker Bridge)
├── suho-central-hub:7000        # Central Hub service
├── suho-postgresql:5432         # Primary database
├── suho-dragonflydb:6379        # Cache layer
├── suho-kafka:9092              # Message broker
├── suho-nats-server:4222        # Lightweight messaging
├── suho-clickhouse:8123         # Analytics database
├── suho-weaviate:8080           # Vector database
└── [other services...]          # Additional services
```

**External Access**: Central Hub is accessible at `http://localhost:7000` for development and monitoring.

---

## 📝 Configuration

Central Hub uses environment variables for database connections:

```env
# Database Configuration
POSTGRES_HOST=suho-postgresql
POSTGRES_PORT=5432
POSTGRES_DB=suho_trading
POSTGRES_USER=suho_admin
POSTGRES_PASSWORD=suho_secure_password_2024

# Cache Configuration
DRAGONFLY_HOST=suho-dragonflydb
DRAGONFLY_PORT=6379
DRAGONFLY_PASSWORD=dragonfly_secure_2024

# Message Broker Configuration
KAFKA_BROKERS=suho-kafka:9092
NATS_URL=nats://suho-nats-server:4222

# Additional Databases
CLICKHOUSE_HOST=suho-clickhouse
CLICKHOUSE_PORT=8123
WEAVIATE_HOST=suho-weaviate
WEAVIATE_PORT=8080
```

This configuration allows Central Hub to act as the central coordination point for all database and service interactions in the trading system.