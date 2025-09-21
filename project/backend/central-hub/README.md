# Central Hub Service

**Phase 1 Infrastructure Migration - Port 8010**

## 🎯 Purpose

Central service orchestration and coordination hub for the AI Trading Platform Phase 1 infrastructure migration.

## 🏗️ Architecture

The Central Hub service provides:

1. **Service Orchestration & Coordination** - Central coordination point for all services
2. **Service Registry & Discovery** - Registration and discovery of microservices
3. **Health Monitoring** - System and service health monitoring
4. **Configuration Management** - Centralized configuration management
5. **Basic Logging** - Structured JSON logging without complex retention

## 🚀 Features

### Phase 1 Implementation
- ✅ Service registration and discovery
- ✅ Health monitoring and status aggregation
- ✅ Configuration management with environment support
- ✅ JSON structured logging
- ✅ RESTful API endpoints
- ✅ Docker containerization
- ✅ System metrics monitoring (CPU, Memory, Disk)

### Excluded from Phase 1
- ❌ AI/ML features
- ❌ Complex log retention
- ❌ Advanced analytics
- ❌ Telegram integration

## 📦 Installation

### Local Development

```bash
# Clone and navigate
cd project/backend/central-hub

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env

# Run locally
python main.py
```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d --build

# Check health
curl http://localhost:8010/health

# View logs
docker-compose logs -f central-hub
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CENTRAL_HUB_SERVICE_PORT` | 8010 | Service port |
| `CENTRAL_HUB_LOG_LEVEL` | INFO | Logging level |
| `CENTRAL_HUB_ENVIRONMENT` | development | Environment |
| `CENTRAL_HUB_REGISTRY_TTL` | 300 | Service TTL (seconds) |
| `CENTRAL_HUB_HEALTH_CHECK_INTERVAL` | 30 | Health check interval |

### Configuration Files

- `config/main.yaml` - Main configuration
- `config/development.yaml` - Development overrides
- `config/production.yaml` - Production overrides

## 📡 API Endpoints

### Health Endpoints
- `GET /` - Service information
- `GET /health` - Basic health check
- `GET /status` - Comprehensive status
- `GET /api/v1/health/` - Detailed health
- `GET /api/v1/health/summary` - Health summary
- `GET /api/v1/health/system` - System health
- `GET /api/v1/health/service/{name}` - Service health

### Service Registry Endpoints
- `POST /api/v1/services/register` - Register service
- `DELETE /api/v1/services/{name}` - Unregister service
- `GET /api/v1/services/` - List all services
- `GET /api/v1/services/healthy` - List healthy services
- `GET /api/v1/services/{name}` - Get service info
- `GET /api/v1/services/discover/{type}` - Discover by type
- `POST /api/v1/services/{name}/health-check` - Manual health check

### Configuration Endpoints
- `GET /api/v1/config/` - All configurations
- `GET /api/v1/config/{key}` - Get configuration
- `PUT /api/v1/config/{key}` - Update configuration
- `POST /api/v1/config/reload` - Reload configurations
- `GET /api/v1/config/status/validation` - Validate config

## 🧪 Testing

### Manual Testing

```bash
# Health check
curl http://localhost:8010/health

# Register a test service
curl -X POST http://localhost:8010/api/v1/services/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-service",
    "host": "localhost",
    "port": 8001,
    "health_endpoint": "/health",
    "metadata": {"type": "test"}
  }'

# List services
curl http://localhost:8010/api/v1/services/

# System health
curl http://localhost:8010/api/v1/health/system
```

### Health Check

```bash
# Service health
curl -f http://localhost:8010/health || echo "Service unhealthy"

# Comprehensive status
curl http://localhost:8010/status
```

## 🔍 Monitoring

### Health Metrics
- CPU usage monitoring with thresholds
- Memory usage monitoring with thresholds
- Disk usage monitoring with thresholds
- Service status aggregation
- System health scoring

### Log Structure

```json
{
  "timestamp": "2025-01-21T03:42:00.000Z",
  "level": "INFO",
  "logger": "central-hub",
  "message": "Service registered: test-service",
  "service_name": "test-service",
  "host": "localhost",
  "port": 8001
}
```

## 🐳 Docker

### Building

```bash
# Build image
docker build -t central-hub:latest .

# Run container
docker run -d \
  --name central-hub \
  -p 8010:8010 \
  -e CENTRAL_HUB_LOG_LEVEL=INFO \
  central-hub:latest
```

### Health Check

```bash
# Docker health check
docker exec central-hub curl -f http://localhost:8010/health
```

## 📊 Service Integration

### Registering Your Service

```python
import httpx

async def register_with_central_hub():
    registration_data = {
        "name": "my-service",
        "host": "localhost",
        "port": 8001,
        "health_endpoint": "/health",
        "metadata": {
            "type": "data-processor",
            "version": "1.0.0"
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8010/api/v1/services/register",
            json=registration_data
        )
        return response.status_code == 200
```

### Service Discovery

```python
async def discover_services(service_type: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://localhost:8010/api/v1/services/discover/{service_type}"
        )
        if response.status_code == 200:
            return response.json()["services"]
        return []
```

## 🔗 Phase 1 Integration

This Central Hub service is designed to integrate with other Phase 1 services:

- **API Gateway (8000)** - Routes requests through Central Hub registry
- **Database Service (8008)** - Registers with Central Hub for discovery
- **Data Bridge (8001)** - Registers for MT5 data service discovery
- **Trading Engine (8007)** - Registers for trading service coordination

## 🚦 Status

**Phase 1**: ✅ **COMPLETE**

- [x] Service orchestration and coordination
- [x] Service registry and health monitoring
- [x] Configuration management
- [x] Basic logging without complex retention
- [x] Port 8010 service setup
- [x] Docker containerization
- [x] API endpoints
- [x] Health monitoring

**Next Phase**: Phase 2 - AI Pipeline Integration

## 📚 Implementation Decisions

Stored implementation decisions:
- Hybrid architecture combining existing patterns with new Phase 1 requirements
- In-memory service registry with TTL-based cleanup for Phase 1 simplicity
- JSON structured logging without complex retention policies
- RESTful API design for service communication
- Health monitoring with configurable thresholds
- Environment-based configuration management
- Docker containerization for deployment consistency

## 🔧 Troubleshooting

### Common Issues

1. **Port 8010 already in use**
   ```bash
   # Check what's using port 8010
   lsof -i :8010

   # Change port in environment
   export CENTRAL_HUB_SERVICE_PORT=8011
   ```

2. **Service registration failing**
   ```bash
   # Check logs
   docker-compose logs central-hub

   # Verify health endpoint is accessible
   curl http://your-service-host:port/health
   ```

3. **Health checks failing**
   ```bash
   # Check system resources
   curl http://localhost:8010/api/v1/health/system

   # Verify thresholds
   curl http://localhost:8010/api/v1/config/health/info
   ```

## 📝 License

Part of AI Trading Platform - Phase 1 Infrastructure Migration