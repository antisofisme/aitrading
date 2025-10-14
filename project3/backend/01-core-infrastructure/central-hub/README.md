# Central Hub Service - Suho AI Trading Platform

[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)](http://localhost:7000/health) [![Version](https://img.shields.io/badge/Version-3.0.0--full-blue)](#) [![Architecture](https://img.shields.io/badge/Architecture-Centralized%20Coordination-orange)](#)

## 🎯 Overview

**Central Hub** adalah jantung koordinasi dari Suho AI Trading Platform yang menyediakan:
- **Service Discovery & Registration** - Koordinasi antar semua backend services
- **Configuration Management** - Static & hot-reload configurations
- **Database Integration Hub** - Centralized database connection management
- **Health Monitoring** - Real-time monitoring semua services dan infrastructure
- **Messaging SDK** - Unified messaging layer (NATS, Kafka, HTTP)
- **Multi-protocol Communication** - Service coordination via REST API

## 🏗️ Architecture

### ChainFlow Pattern
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ API Gateway │────│ Central Hub │────│ Trading Eng │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       └────── Direct ──────┴────── Calls ─────┘

Database Integration Flow:
Services ──discover──→ Central Hub ──connections──→ Database Cluster
```

**✅ COORDINATION PATTERN (NOT PROXY):**
1. Service A queries Central Hub: "Where is Service B?"
2. Central Hub responds: "Service B is at http://service-b:8080"
3. Service A calls Service B directly
4. Central Hub manages database connections for all services

## 📂 Project Structure

```
central-hub/
├── README.md                    # 📖 This documentation
├── Dockerfile                   # 🐳 Container configuration
├── requirements.txt             # 📦 Python dependencies
├── SYSTEM_ARCHITECTURE.md       # 🏛️ Detailed architecture docs
├── SHARED_ARCHITECTURE_GUIDE.md # 🔗 Shared components guide
│
├── docs/                        # 📚 Comprehensive documentation
│   ├── SHARED_ARCHITECTURE.md   #    Shared folder detailed guide
│   ├── REFACTORING_2025_10.md   #    October 2025 refactoring guide
│   └── API_DOCUMENTATION.md     #    Complete API reference
│
├── base/                        # 🔧 Core implementation
│   ├── app.py                   #    FastAPI application entry point
│   ├── api/                     #    REST API endpoints
│   │   ├── discovery.py         #      Service registration & discovery
│   │   ├── health.py            #      Health monitoring endpoints
│   │   ├── config.py            #      Configuration management API
│   │   └── metrics.py           #      System metrics endpoints
│   ├── core/                    #    Core business logic
│   │   ├── service_registry.py  #      Service registry implementation
│   │   ├── health_monitor.py    #      Health monitoring system
│   │   ├── config_manager.py    #      Configuration management
│   │   └── coordination_router.py #    Inter-service routing
│   ├── impl/                    #    Infrastructure implementations
│   └── middleware/              #    HTTP middleware
│
├── shared/                      # 🔄 Shared configurations & components
│   ├── static/                  #    Infrastructure configs (stable)
│   │   ├── database/            #      Database connection configs
│   │   └── messaging/           #      Message broker configs
│   ├── hot-reload/              #    Business configs (dynamic)
│   │   ├── api_gateway.py       #      API Gateway business rules
│   │   └── service_config_template.py # Service config templates
│   └── components/              #    Shared utility components
│
├── sdk/                         # 📦 Client SDKs
│   └── python/                  #    Python SDK
│       └── central_hub_sdk/     #    Central Hub SDK
│           ├── client.py        #      Service registration client
│           ├── database/        #      Multi-database SDK
│           ├── messaging/       #      Unified messaging SDK
│           └── schemas/         #      Database schemas
│
└── logs/                        # 📊 Application logs
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for development)
- PostgreSQL, DragonflyDB, NATS, Kafka (via docker-compose)

### 1. Start with Docker Compose
```bash
# Start all infrastructure services
cd /path/to/project3/backend
docker-compose up -d

# Check Central Hub status
curl http://localhost:7000/health
```

### 2. Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (requires running databases)
cd base/
python app.py
```

### 3. Verify Installation
```bash
# Health check
curl http://localhost:7000/health

# Service info
curl http://localhost:7000/

# Service registry
curl http://localhost:7000/discovery/services
```

## 🔗 API Endpoints

### Core Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service information & status |
| `/health` | GET | Health check with database connectivity |
| `/metrics` | GET | System metrics & performance data |

### Service Discovery
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/discovery/register` | POST | Register a new service |
| `/discovery/services` | GET | Get all registered services |
| `/discovery/services/{name}` | GET | Get specific service info |
| `/discovery/health` | GET | Discovery system health |

### Configuration Management
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/config/{service_name}` | GET | Get service configuration |
| `/config/{service_name}/validate` | POST | Validate service config |
| `/config/reload` | POST | Reload hot-reload configurations |

## 🔧 Configuration

### Environment Variables
```bash
# Database connections
DATABASE_URL=postgresql://suho_admin:password@suho-postgresql:5432/suho_trading
CACHE_URL=redis://:password@suho-dragonflydb:6379

# Message brokers
NATS_URL=nats://suho-nats-server:4222
KAFKA_BROKERS=suho-kafka:9092

# Service settings
NODE_ENV=development
HOT_RELOAD_ENABLED=false
COMPONENT_WATCH_ENABLED=false
```

### Static vs Hot-reload Configs

**Static Configs** (`shared/static/`):
- Database connection details
- Message broker settings
- Infrastructure settings
- **Requires restart** to apply changes

**Hot-reload Configs** (`shared/hot-reload/`):
- Business rules & logic
- Feature flags
- Performance tuning
- **Applied immediately** without restart

## 🏃‍♂️ Service Registration Example

```javascript
// Register API Gateway
POST /discovery/register
{
  "name": "api-gateway",
  "host": "suho-api-gateway",
  "port": 8000,
  "protocol": "http",
  "health_endpoint": "/health",
  "metadata": {
    "type": "api-gateway",
    "capabilities": ["http", "websocket", "trading"],
    "max_connections": 1000
  }
}
```

## 📊 Monitoring & Health

### Health Monitoring Features
- **Database connectivity** check for all databases
- **Cache connectivity** check (DragonflyDB/Redis)
- **Message broker** connectivity (NATS, Kafka)
- **Service registry** health status
- **Background tasks** monitoring

### Metrics Collection
- Service registration count
- Request/response times
- Database connection pool status
- Cache hit/miss ratios
- Message queue depths

### Health Check Response
```json
{
  "status": "healthy",
  "version": "3.0.0-full",
  "timestamp": 1759206478165,
  "checks": {
    "database": "healthy",
    "cache": "healthy",
    "nats": "healthy",
    "kafka": "healthy"
  },
  "registered_services": 3
}
```

## 🔄 Integration Patterns

### Service-to-Service Communication
1. **Service Discovery**: Query Central Hub for service locations
2. **Direct Communication**: Call services directly using discovered endpoints
3. **Health Reporting**: Services report health status to Central Hub
4. **Configuration Updates**: Hot-reload configs pushed to services

### Database Integration
- **Connection Pooling**: Centralized database connection management
- **Multi-database Support**: PostgreSQL, ClickHouse, DragonflyDB, ArangoDB, Weaviate
- **Health Monitoring**: Continuous database connectivity checks
- **Connection Sharing**: Shared connection details via service discovery

## 🐳 Docker Integration

### Container Information
- **Base Image**: `python:3.11-slim`
- **Port**: `7000`
- **Health Check**: `curl -f http://localhost:7000/health`
- **Restart Policy**: `unless-stopped`

### Volume Mounts
```yaml
volumes:
  # Hot-reload support
  - ./shared:/app/shared:rw
  - ./base:/app/base:rw
  - ./sdk:/app/sdk:rw
  # Component cache
  - central-hub-components:/app/shared/.component_cache
```

### Dependencies
- `postgresql` - Primary database
- `dragonflydb` - Cache layer
- `nats` - Message streaming
- `kafka` - Event streaming

## 🛠️ Development

### Running Tests
```bash
# Unit tests
python -m pytest tests/

# Integration tests
python -m pytest tests/integration/

# Health check test
curl http://localhost:7000/health | jq .
```

### Hot-reload Development
```bash
# Enable hot-reload mode
export HOT_RELOAD_ENABLED=true
export COMPONENT_WATCH_ENABLED=true

# Changes to shared/hot-reload/ automatically applied
```

### Adding New Services
1. Install Central Hub SDK: `pip install -e sdk/python`
2. Use CentralHubClient for registration:
   ```python
   from central_hub_sdk import CentralHubClient
   client = CentralHubClient("my-service", "data-collector")
   await client.register()
   ```
3. Verify via `/discovery/services`

## 📈 Performance

### Specifications
- **Startup Time**: ~10-15 seconds (full integration)
- **Response Time**: <50ms for discovery queries
- **Concurrent Connections**: 1000+ supported
- **Memory Usage**: ~128-256MB base
- **Database Connections**: Pooled (10-20 per database)

### Optimization Features
- Connection pooling for all databases
- In-memory service registry caching
- Async/await for non-blocking operations
- Background health monitoring
- Circuit breaker patterns

## 🔒 Security

### Authentication & Authorization
- JWT-based service authentication
- API key validation for external services
- Rate limiting per service
- CORS protection

### Network Security
- Internal service communication only
- Health endpoints publicly accessible
- Admin endpoints require authentication
- SSL/TLS support for production

## 🚨 Troubleshooting

### Common Issues

**Service Not Registering**
```bash
# Check Central Hub connectivity
curl http://localhost:7000/health

# Verify service endpoint
curl http://service-host:port/health

# Check logs
docker logs suho-central-hub
```

**Database Connection Issues**
```bash
# Check database health
curl http://localhost:7000/health | jq .checks.database

# Test direct connection
psql postgresql://suho_admin:password@localhost:5432/suho_trading
```

**Configuration Not Loading**
```bash
# Reload configurations
curl -X POST http://localhost:7000/config/reload

# Check config status
curl http://localhost:7000/config/api-gateway
```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Enable performance metrics
export ENABLE_PERFORMANCE_METRICS=true
```

## 📞 Support

- **Health Endpoint**: http://localhost:7000/health
- **Metrics Dashboard**: http://localhost:7000/metrics
- **Service Registry**: http://localhost:7000/discovery/services
- **Docker Logs**: `docker logs suho-central-hub`

## 🎯 Next Steps

1. **Monitor** service health via `/health` endpoint
2. **Register** your services via `/discovery/register`
3. **Configure** business rules in `shared/hot-reload/`
4. **Scale** by adding more service instances
5. **Optimize** using `/metrics` performance data

---

**🚀 Central Hub: Koordinasi Cerdas untuk Ekosistem Trading AI yang Scalable**