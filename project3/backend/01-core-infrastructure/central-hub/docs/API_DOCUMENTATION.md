# Central Hub API Documentation

## 🔗 API Overview

Central Hub provides RESTful APIs for service discovery, configuration management, health monitoring, and system metrics. All endpoints follow standardized response formats and include comprehensive error handling.

**Base URL**: `http://localhost:7000`
**Content-Type**: `application/json`
**Authentication**: Service-based (via service registration)

## 📋 Table of Contents

- [Service Information](#-service-information)
- [Health Monitoring](#-health-monitoring)
- [Service Discovery](#-service-discovery)
- [Configuration Management](#-configuration-management)
- [System Metrics](#-system-metrics)
- [Error Handling](#-error-handling)
- [Rate Limiting](#-rate-limiting)

---

## 🏠 Service Information

### Get Service Info
**Endpoint**: `GET /`
**Description**: Retrieve Central Hub service information and status

**Response**:
```json
{
  "service": "central-hub",
  "version": "3.0.0-full",
  "status": "active",
  "implementation": "full",
  "features": [
    "real_database_integration",
    "real_cache_integration",
    "real_transport_methods",
    "contract_validation",
    "service_coordination",
    "workflow_orchestration",
    "task_scheduling",
    "health_monitoring"
  ],
  "transports": {
    "nats": true,
    "kafka": true,
    "redis": true,
    "grpc": true,
    "http": true
  },
  "database": true,
  "cache": true,
  "contracts": true,
  "registered_services": 5,
  "timestamp": 1759206478165
}
```

---

## 💚 Health Monitoring

### Health Check
**Endpoint**: `GET /health`
**Description**: Comprehensive health check including database and service connectivity

**Response**:
```json
{
  "status": "healthy",
  "version": "3.0.0-full",
  "timestamp": 1759206478165,
  "uptime_seconds": 3456,
  "checks": {
    "database": {
      "status": "healthy",
      "postgresql": "connected",
      "clickhouse": "connected",
      "dragonflydb": "connected",
      "arangodb": "connected",
      "weaviate": "connected"
    },
    "messaging": {
      "status": "healthy",
      "nats": "connected",
      "kafka": "connected"
    },
    "services": {
      "status": "healthy",
      "registered_count": 5,
      "active_count": 5
    }
  },
  "performance": {
    "memory_usage_mb": 156,
    "cpu_usage_percent": 12.3,
    "active_connections": 15
  }
}
```

**Status Codes**:
- `200 OK` - Service healthy
- `503 Service Unavailable` - Service unhealthy or degraded

---

## 🔍 Service Discovery

### Register Service
**Endpoint**: `POST /discovery/register`
**Description**: Register a new service with Central Hub

**Request Body**:
```json
{
  "service_name": "api-gateway",
  "host": "suho-api-gateway",
  "port": 8000,
  "protocol": "http",
  "version": "1.0.0",
  "environment": "development",
  "health_endpoint": "/health",
  "metadata": {
    "type": "api-gateway",
    "capabilities": ["http", "websocket", "trading"],
    "tenant_support": false,
    "max_connections": 1000,
    "load_balancing_weight": 10
  },
  "transport_config": {
    "preferred_inbound": ["http"],
    "preferred_outbound": ["http", "nats-kafka"],
    "supports_streaming": true,
    "max_message_size": 1048576
  }
}
```

**Response**:
```json
{
  "status": "registered",
  "service_id": "api-gateway-1642234567890",
  "registration_time": "2024-01-15T10:30:00Z",
  "service_url": "http://suho-api-gateway:8000",
  "health_check_url": "http://suho-api-gateway:8000/health",
  "assigned_routing_group": "gateway-services"
}
```

**Status Codes**:
- `201 Created` - Service successfully registered
- `400 Bad Request` - Invalid registration data
- `409 Conflict` - Service already registered with same name

### Get All Services
**Endpoint**: `GET /discovery/services`
**Description**: Retrieve all registered services

**Query Parameters**:
- `type` (optional): Filter by service type
- `environment` (optional): Filter by environment
- `status` (optional): Filter by status (active, inactive, maintenance)
- `capabilities` (optional): Filter by capabilities (comma-separated)

**Example**: `GET /discovery/services?type=trading-engine&status=active`

**Response**:
```json
{
  "services": [
    {
      "service_name": "trading-engine-1",
      "service_id": "trading-engine-1-1642234567890",
      "url": "http://trading-engine-1:8080",
      "status": "active",
      "type": "trading-engine",
      "version": "1.2.0",
      "capabilities": ["real-time", "backtesting", "order-management"],
      "health_status": "healthy",
      "last_seen": "2024-01-15T10:30:00Z",
      "registered_at": "2024-01-15T09:00:00Z",
      "metadata": {
        "max_connections": 500,
        "load_balancing_weight": 15
      }
    }
  ],
  "total_count": 1,
  "active_count": 1,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Get Specific Service
**Endpoint**: `GET /discovery/services/{service_name}`
**Description**: Get detailed information about a specific service

**Path Parameters**:
- `service_name`: Name of the service

**Response**:
```json
{
  "service_name": "api-gateway",
  "service_id": "api-gateway-1642234567890",
  "url": "http://suho-api-gateway:8000",
  "status": "active",
  "type": "api-gateway",
  "version": "1.0.0",
  "environment": "development",
  "capabilities": ["http", "websocket", "trading"],
  "health_status": "healthy",
  "last_health_check": "2024-01-15T10:29:45Z",
  "registered_at": "2024-01-15T09:00:00Z",
  "last_seen": "2024-01-15T10:30:00Z",
  "metadata": {
    "max_connections": 1000,
    "load_balancing_weight": 10,
    "tenant_support": false
  },
  "transport_config": {
    "preferred_inbound": ["http"],
    "preferred_outbound": ["http", "nats-kafka"],
    "supports_streaming": true
  },
  "statistics": {
    "total_requests": 15642,
    "requests_per_minute": 120,
    "average_response_time_ms": 45,
    "error_rate_percent": 0.2
  }
}
```

**Status Codes**:
- `200 OK` - Service found
- `404 Not Found` - Service not registered

### Unregister Service
**Endpoint**: `DELETE /discovery/services/{service_name}`
**Description**: Unregister a service from Central Hub

**Response**:
```json
{
  "status": "unregistered",
  "service_name": "api-gateway",
  "unregistered_at": "2024-01-15T10:30:00Z"
}
```

### Discovery Health Check
**Endpoint**: `GET /discovery/health`
**Description**: Health status of service discovery system

**Response**:
```json
{
  "status": "healthy",
  "registered_services": 5,
  "active_services": 4,
  "inactive_services": 1,
  "last_registration": "2024-01-15T10:25:00Z",
  "registry_size_mb": 2.3,
  "average_health_check_time_ms": 15
}
```

---

## ⚙️ Configuration Management

### Get Service Configuration
**Endpoint**: `GET /config/{service_name}`
**Description**: Retrieve configuration for a specific service

**Path Parameters**:
- `service_name`: Name of the service

**Query Parameters**:
- `section` (optional): Specific configuration section
- `format` (optional): Response format (json, yaml) - default: json

**Example**: `GET /config/api-gateway?section=business_rules`

**Response**:
```json
{
  "service_name": "api-gateway",
  "version": "2.0.0",
  "last_updated": "2024-01-15T10:00:00Z",
  "configuration": {
    "business_rules": {
      "rate_limiting": {
        "requests_per_minute": 1000,
        "burst_limit": 100,
        "enabled": true
      },
      "timeouts": {
        "request_timeout_ms": 30000,
        "connection_timeout_ms": 5000
      }
    },
    "features": {
      "enable_debug_logging": false,
      "enable_performance_metrics": true,
      "maintenance_mode": false
    }
  },
  "static_references": {
    "database_url": "ENV:DATABASE_URL",
    "cache_url": "ENV:CACHE_URL"
  }
}
```

### Validate Service Configuration
**Endpoint**: `POST /config/{service_name}/validate`
**Description**: Validate configuration for a service without applying

**Request Body**:
```json
{
  "configuration": {
    "business_rules": {
      "rate_limiting": {
        "requests_per_minute": 2000,
        "burst_limit": 150
      }
    }
  }
}
```

**Response**:
```json
{
  "valid": true,
  "validation_results": [
    {
      "level": "info",
      "field": "business_rules.rate_limiting.requests_per_minute",
      "message": "Value within acceptable range"
    }
  ],
  "warnings": [],
  "errors": []
}
```

### Reload Configurations
**Endpoint**: `POST /config/reload`
**Description**: Reload hot-reload configurations for all services

**Response**:
```json
{
  "status": "reloaded",
  "reloaded_services": ["api-gateway", "trading-engine"],
  "reload_time": "2024-01-15T10:30:00Z",
  "reload_duration_ms": 150,
  "errors": []
}
```

---

## 📊 System Metrics

### Get System Metrics
**Endpoint**: `GET /metrics`
**Description**: Comprehensive system metrics and performance data

**Response**:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "system": {
    "uptime_seconds": 3456,
    "memory_usage_mb": 156,
    "cpu_usage_percent": 12.3,
    "disk_usage_percent": 45.2,
    "network_io": {
      "bytes_in": 1048576,
      "bytes_out": 2097152
    }
  },
  "services": {
    "registered_count": 5,
    "active_count": 4,
    "total_requests_24h": 156420,
    "average_response_time_ms": 45,
    "error_rate_percent": 0.15
  },
  "database": {
    "postgresql": {
      "status": "connected",
      "active_connections": 8,
      "pool_size": 10,
      "query_time_p95_ms": 25
    },
    "clickhouse": {
      "status": "connected",
      "active_connections": 3,
      "disk_usage_gb": 12.5
    },
    "dragonflydb": {
      "status": "connected",
      "memory_usage_mb": 64,
      "hit_rate_percent": 94.2
    }
  },
  "messaging": {
    "nats": {
      "status": "connected",
      "messages_in": 8640,
      "messages_out": 8635,
      "subjects": 12
    },
    "kafka": {
      "status": "connected",
      "topics": 8,
      "partitions": 24,
      "messages_per_second": 150
    }
  }
}
```

### Get Service-Specific Metrics
**Endpoint**: `GET /metrics/services/{service_name}`
**Description**: Detailed metrics for a specific service

**Response**:
```json
{
  "service_name": "api-gateway",
  "timestamp": "2024-01-15T10:30:00Z",
  "health_status": "healthy",
  "performance": {
    "requests_per_minute": 120,
    "average_response_time_ms": 45,
    "p95_response_time_ms": 120,
    "p99_response_time_ms": 250,
    "error_rate_percent": 0.2,
    "active_connections": 25
  },
  "resources": {
    "cpu_usage_percent": 15.2,
    "memory_usage_mb": 128,
    "disk_usage_mb": 45
  },
  "endpoints": [
    {
      "path": "/health",
      "method": "GET",
      "requests_count": 1440,
      "average_response_time_ms": 5,
      "error_rate_percent": 0.0
    },
    {
      "path": "/api/orders",
      "method": "POST",
      "requests_count": 856,
      "average_response_time_ms": 125,
      "error_rate_percent": 0.5
    }
  ]
}
```

---

## 🚨 Error Handling

### Standard Error Response
All API endpoints return standardized error responses:

```json
{
  "error": {
    "code": "SERVICE_NOT_FOUND",
    "message": "Service 'unknown-service' not found in registry",
    "details": {
      "service_name": "unknown-service",
      "suggestion": "Check service name or register service first"
    },
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req-123456789"
  }
}
```

### Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `INVALID_REQUEST` | Request validation failed |
| 401 | `UNAUTHORIZED` | Service authentication required |
| 403 | `FORBIDDEN` | Service not authorized for operation |
| 404 | `SERVICE_NOT_FOUND` | Requested service not registered |
| 409 | `CONFLICT` | Service already registered or conflict |
| 422 | `VALIDATION_FAILED` | Configuration validation failed |
| 429 | `RATE_LIMITED` | Rate limit exceeded |
| 500 | `INTERNAL_ERROR` | Internal server error |
| 503 | `SERVICE_UNAVAILABLE` | Central Hub unhealthy |

---

## 🛡️ Rate Limiting

### Rate Limit Headers
All responses include rate limiting information:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1642234567
X-RateLimit-Window: 60
```

### Rate Limits by Endpoint

| Endpoint Group | Limit | Window |
|----------------|-------|---------|
| Service Discovery | 100 req/min | 60 seconds |
| Configuration | 50 req/min | 60 seconds |
| Health Checks | 200 req/min | 60 seconds |
| Metrics | 30 req/min | 60 seconds |

### Rate Limit Exceeded Response
```json
{
  "error": {
    "code": "RATE_LIMITED",
    "message": "Rate limit exceeded",
    "details": {
      "limit": 100,
      "window_seconds": 60,
      "retry_after_seconds": 45
    }
  }
}
```

---

## 🔧 Integration Examples

### Service Registration Flow
```bash
# 1. Register service
curl -X POST http://localhost:7000/discovery/register \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "my-service",
    "host": "my-service",
    "port": 8080,
    "metadata": {"type": "api"}
  }'

# 2. Verify registration
curl http://localhost:7000/discovery/services/my-service

# 3. Health check
curl http://localhost:7000/health
```

### Configuration Management Flow
```bash
# 1. Get current configuration
curl http://localhost:7000/config/api-gateway

# 2. Validate new configuration
curl -X POST http://localhost:7000/config/api-gateway/validate \
  -H "Content-Type: application/json" \
  -d '{"configuration": {"business_rules": {"rate_limiting": {"requests_per_minute": 2000}}}}'

# 3. Reload configurations
curl -X POST http://localhost:7000/config/reload
```

### Service Discovery Flow
```bash
# 1. Find trading services
curl "http://localhost:7000/discovery/services?type=trading-engine&status=active"

# 2. Get specific service details
curl http://localhost:7000/discovery/services/trading-engine-1

# 3. Call discovered service directly
curl http://trading-engine-1:8080/api/orders
```

---

**🔗 Central Hub API: Koordinasi dan Monitoring yang Comprehensive dan Type-Safe**