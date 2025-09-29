# Database Infrastructure Services

## 🎯 Purpose
**Centralized multi-database infrastructure cluster** yang menyediakan komprehensif database dan messaging services untuk semua backend services dengan high-performance time-series support, caching, analytics, dan message streaming dalam satu koordinasi deployment.

---

## 📊 ChainFlow Diagram

```
Backend Services → Central Hub → Database Infrastructure Cluster
       ↓               ↓                    ↓
Service Discovery  Coordination        PostgreSQL/TimescaleDB
Service Registry   Connection Pool     DragonflyDB (Cache)
Health Monitor     Load Balancing      ClickHouse (Analytics)
Circuit Breaker    Failover Support    Weaviate (Vector DB)
                                      ArangoDB (Graph DB)
                                      NATS (Messaging)
                                      Kafka (Streaming)

Integration Flow:
Services → Central Hub (Discovery) → Direct Database Connections
```

---

## 🏗️ Infrastructure Architecture

### **Database Cluster Components**
**Deployment**: Single docker-compose deployment for all database services
**Coordination**: Central Hub provides service discovery and connection management
**Network**: All services in `suho-trading-network` for internal communication

### **Primary Databases**
- **PostgreSQL + TimescaleDB**: Primary OLTP and time-series data
- **DragonflyDB**: High-performance Redis-compatible cache
- **ClickHouse**: OLAP analytics and reporting database

### **Specialized Databases**
- **Weaviate**: Vector database for AI/ML embeddings
- **ArangoDB**: Multi-model graph database

### **Message Infrastructure**
- **NATS**: Lightweight, fast messaging for real-time coordination
- **Kafka + Zookeeper**: High-throughput message streaming with persistence

---

## 🐳 Docker Deployment Architecture

### **Single Infrastructure Deployment**

All database and messaging services are deployed as one coordinated group:

```bash
# Deploy entire database infrastructure
cd database-service
docker-compose up -d

# Services deployed:
# - PostgreSQL (suho-postgresql:5432)
# - DragonflyDB (suho-dragonflydb:6379)
# - ClickHouse (suho-clickhouse:8123)
# - Weaviate (suho-weaviate:8080)
# - ArangoDB (suho-arangodb:8529)
# - NATS (suho-nats-server:4222)
# - Kafka (suho-kafka:9092)
# - Zookeeper (suho-zookeeper:2181)
```

### **Central Hub Integration**

Central Hub deploys **separately** but connects to all database services:

```bash
# Central Hub connects to database infrastructure
docker run -d \
  --name suho-central-hub \
  --network suho-trading-network \
  -p 7000:7000 \
  -e POSTGRES_HOST=suho-postgresql \
  -e DRAGONFLY_HOST=suho-dragonflydb \
  -e KAFKA_BROKERS=suho-kafka:9092 \
  -e NATS_URL=nats://suho-nats-server:4222 \
  # ... other database connections
  central-hub:latest
```

---

## 📊 Database Service Specifications

### **📍 PostgreSQL + TimescaleDB**
**Container**: `suho-postgresql:5432`
**Purpose**: Primary transactional database with time-series extensions
**Configuration**:
- Database: `suho_trading`
- User: `suho_admin` / Password: `suho_secure_password_2024`
- Max Connections: 200
- Shared Buffers: 1GB
- Effective Cache: 3GB

**Usage**:
- Trading orders and transactions
- User accounts and profiles
- Time-series price data
- System audit logs

### **📍 DragonflyDB (Redis-compatible)**
**Container**: `suho-dragonflydb:6379`
**Purpose**: High-performance caching and session storage
**Configuration**:
- Password: `dragonfly_secure_2024`
- Memory optimized for caching
- Redis protocol compatibility

**Usage**:
- Session management
- Real-time price caching
- Application performance cache
- Rate limiting data

### **📍 ClickHouse**
**Container**: `suho-clickhouse:8123` (HTTP) / `9000` (Native)
**Purpose**: OLAP analytics and reporting database
**Configuration**:
- Database: `suho_analytics`
- User: `suho_analytics` / Password: `clickhouse_secure_2024`
- Optimized for analytical queries

**Usage**:
- Trading performance analytics
- Historical data analysis
- Business intelligence reports
- Large-scale data aggregation

### **📍 Weaviate**
**Container**: `suho-weaviate:8080`
**Purpose**: Vector database for AI/ML features
**Configuration**:
- Anonymous access enabled for development
- Vector storage for embeddings
- GraphQL query interface

**Usage**:
- AI-powered trading insights
- Document similarity search
- Recommendation systems
- Machine learning feature storage

### **📍 ArangoDB**
**Container**: `suho-arangodb:8529`
**Purpose**: Multi-model graph database
**Configuration**:
- Root password: `arango_secure_password_2024`
- Document, graph, and key-value models
- Web interface available

**Usage**:
- User relationship graphs
- Trading network analysis
- Complex data relationships
- Multi-model data requirements

---

## 🚀 Message Infrastructure

### **📍 NATS Server**
**Container**: `suho-nats-server:4222`
**Purpose**: Lightweight, fast messaging for real-time coordination
**Configuration**:
- JetStream enabled for persistence
- HTTP monitoring on port 8222
- High-performance message delivery

**Usage**:
- Real-time service coordination
- Fast inter-service communication
- Event-driven architecture
- Live trading signals

### **📍 Kafka + Zookeeper**
**Container**: `suho-kafka:9092` + `suho-zookeeper:2181`
**Purpose**: High-throughput message streaming with persistence
**Configuration**:
- Broker ID: 1
- Partitions: 6 (default)
- Retention: 3 days
- Replication Factor: 1 (single broker setup)

**Usage**:
- High-volume trading data streams
- Audit log streaming
- Event sourcing
- System integration events

**⚠️ Fixed Configuration**: Removed problematic Confluent metrics reporter to ensure stable operation.

---

## 🌐 Network Architecture

All services operate in the `suho-trading-network` Docker bridge network:

```
suho-trading-network (Docker Bridge)
├── Database Cluster (docker-compose group):
│   ├── suho-postgresql:5432         # Primary database
│   ├── suho-dragonflydb:6379        # Cache layer
│   ├── suho-clickhouse:8123/9000    # Analytics database
│   ├── suho-weaviate:8080           # Vector database
│   ├── suho-arangodb:8529           # Graph database
│   ├── suho-nats-server:4222        # Fast messaging
│   ├── suho-kafka:9092              # Message streaming
│   └── suho-zookeeper:2181          # Kafka coordinator
└── External Services:
    ├── suho-central-hub:7000        # Service coordination
    └── [other backend services...]   # Application services
```

**External Ports**: Only Central Hub (7000) and database ports are exposed for development access.

---

## 📊 Performance & Monitoring

### **Database Health Checks**
Each service includes comprehensive health monitoring:

- **PostgreSQL**: `pg_isready` checks every 30s
- **ClickHouse**: HTTP ping endpoint monitoring
- **DragonflyDB**: Redis `ping` command checks
- **Weaviate**: HTTP readiness endpoint
- **ArangoDB**: API version endpoint checks
- **NATS**: HTTP health endpoint monitoring
- **Kafka**: Broker API version checks

### **Performance Targets**
- **PostgreSQL**: <5ms for simple queries, <50ms for complex transactions
- **DragonflyDB**: <1ms cache access
- **ClickHouse**: <100ms for analytical queries
- **NATS**: <1ms message delivery
- **Kafka**: <10ms message throughput

### **Storage Management**
All services use Docker volumes for data persistence:
- `postgresql_data` - PostgreSQL database files
- `clickhouse_data` - ClickHouse data and logs
- `dragonflydb_data` - DragonflyDB persistence
- `weaviate_data` - Vector database storage
- `arangodb_data` - Graph database storage
- `nats_data` - NATS JetStream persistence
- `kafka_data` - Kafka topic data
- `zookeeper_data` - Zookeeper coordination data

---

## 🚀 3 Transport Methods Integration

The database infrastructure supports all transport methods through Central Hub coordination:

### **Method 1: NATS+Kafka Hybrid (High Volume + Mission Critical)**
**Database Usage**: Real-time trading data persistence and analytics
- **NATS**: Fast writes to PostgreSQL for trading orders
- **Kafka**: Reliable streaming to ClickHouse for analytics

### **Method 2: HTTP/REST (Standard Operations)**
**Database Usage**: Standard CRUD operations and queries
- **Central Hub API**: Service discovery and database routing
- **Direct Connections**: HTTP connections to individual databases

### **Method 3: gRPC (High-Performance)**
**Database Usage**: High-frequency trading data access
- **Connection Pooling**: Optimized gRPC connections through Central Hub
- **Load Balancing**: Intelligent routing based on database load

---

## 🔧 Development & Operations

### **Deployment Commands**
```bash
# Deploy entire database infrastructure
cd database-service
docker-compose up -d

# Check all service status
docker-compose ps

# View logs for specific service
docker-compose logs postgresql
docker-compose logs kafka

# Scale specific services (if needed)
docker-compose up -d --scale kafka=1

# Backup and restore (example for PostgreSQL)
docker exec suho-postgresql pg_dump -U suho_admin suho_trading > backup.sql
```

### **Service Dependencies**
Services start in dependency order:
1. **Zookeeper** (required for Kafka)
2. **Core Databases** (PostgreSQL, DragonflyDB, ClickHouse)
3. **Specialized Databases** (Weaviate, ArangoDB)
4. **Messaging** (NATS, Kafka)
5. **Central Hub** (separate deployment, connects to all)

### **Environment Configuration**
Key environment variables for database connections are managed through docker-compose and passed to Central Hub for unified access.

---

## 📝 Integration Notes

### **Central Hub Role**
Central Hub acts as the **database service coordinator** by:
- Providing service discovery for all database endpoints
- Managing connection pooling and load balancing
- Monitoring health of all database services
- Implementing circuit breakers for database failures
- Coordinating failover and recovery procedures

### **Service Communication Pattern**
1. **Backend services** register with **Central Hub**
2. **Central Hub** provides database connection information
3. **Services** make direct connections to appropriate databases
4. **Central Hub** monitors and coordinates all database health

This architecture provides a robust, scalable database infrastructure that supports high-frequency trading requirements while maintaining data integrity and system reliability.