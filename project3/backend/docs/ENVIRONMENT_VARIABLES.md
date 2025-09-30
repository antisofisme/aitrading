# 🌍 Environment Variables Reference

## Complete Reference Guide

Dokumen ini berisi **referensi lengkap** semua environment variables yang digunakan dalam sistem SUHO Trading.

## 📊 Categories Overview

| Category | Count | Description |
|----------|-------|-------------|
| Database Infrastructure | 12 | Database connections dan credentials |
| Messaging Infrastructure | 6 | Message brokers dan event streaming |
| Core Services | 8 | Main application services |
| Security & Authentication | 4 | JWT, API keys, secrets |
| Development Settings | 5 | Development dan debugging flags |

---

## 🗃️ Database Infrastructure

### PostgreSQL (Primary OLTP Database)
```bash
POSTGRES_HOST=suho-postgresql          # PostgreSQL container hostname
POSTGRES_PORT=5432                     # PostgreSQL port
POSTGRES_DB=suho_trading              # Primary database name
POSTGRES_USER=suho_admin              # Database user
POSTGRES_PASSWORD=suho_secure_password_2024  # Database password
DATABASE_URL=postgresql://suho_admin:${POSTGRES_PASSWORD}@suho-postgresql:5432/suho_trading
```

### ClickHouse (OLAP Analytics Database)
```bash
CLICKHOUSE_HOST=suho-clickhouse        # ClickHouse container hostname
CLICKHOUSE_PORT=8123                   # ClickHouse HTTP interface port
CLICKHOUSE_DB=suho_analytics          # Analytics database name
CLICKHOUSE_USER=suho_analytics        # ClickHouse user
CLICKHOUSE_PASSWORD=clickhouse_secure_2024  # ClickHouse password
```

### DragonflyDB (High-Performance Cache)
```bash
DRAGONFLY_HOST=suho-dragonflydb       # DragonflyDB container hostname
DRAGONFLY_PORT=6379                   # DragonflyDB port (Redis-compatible)
DRAGONFLY_PASSWORD=dragonfly_secure_2024  # DragonflyDB password
CACHE_URL=redis://:${DRAGONFLY_PASSWORD}@suho-dragonflydb:6379
```

### ArangoDB (Multi-Model Graph Database)
```bash
ARANGO_HOST=suho-arangodb             # ArangoDB container hostname
ARANGO_PORT=8529                      # ArangoDB web interface port
ARANGO_ROOT_PASSWORD=arango_secure_password_2024  # ArangoDB root password
ARANGO_JWT_SECRET=your-jwt-secret-change-in-production  # ArangoDB JWT secret
```

### Weaviate (Vector Database)
```bash
WEAVIATE_HOST=suho-weaviate           # Weaviate container hostname
WEAVIATE_PORT=8080                    # Weaviate HTTP API port
```

---

## 📨 Messaging Infrastructure

### Kafka (Event Streaming Platform)
```bash
KAFKA_BROKERS=suho-kafka:9092         # Kafka broker addresses (comma-separated)
KAFKA_CLIENT_ID=suho-trading-client   # Kafka client identifier
ZOOKEEPER_CONNECT=suho-zookeeper:2181 # Zookeeper connection string
KAFKAJS_NO_PARTITIONER_WARNING=1      # Suppress KafkaJS partitioner warnings
```

### NATS (Message Broker)
```bash
NATS_URL=nats://suho-nats-server:4222 # Complete NATS connection URL
NATS_HOST=suho-nats-server            # NATS server hostname
NATS_PORT=4222                        # NATS server port
```

---

## 🏢 Core Services

### Central Hub (Configuration & Coordination)
```bash
CENTRAL_HUB_URL=http://suho-central-hub:7000  # Central Hub service URL
CENTRAL_HUB_PORT=7000                         # Central Hub service port
```

### API Gateway (Main Entry Point)
```bash
API_GATEWAY_PORT=8000                 # API Gateway HTTP port
LOG_LEVEL=info                        # Logging level (debug|info|warn|error)
CORS_ENABLED=true                     # Enable CORS for browser requests
WEBSOCKET_ENABLED=true                # Enable WebSocket connections
```

### Application Settings
```bash
NODE_ENV=development                  # Application environment (development|production|staging)
HOT_RELOAD_ENABLED=false             # Enable hot reload for development
COMPONENT_WATCH_ENABLED=false        # Enable component file watching
PYTHONPATH=/app                      # Python path for Central Hub
```

---

## 🔐 Security & Authentication

### JWT Configuration
```bash
JWT_SECRET=your-super-secret-jwt-key-change-in-production  # JWT signing secret
JWT_EXPIRES_IN=24h                    # JWT token expiration time
JWT_ISSUER=suho-api-gateway          # JWT issuer identifier
JWT_AUDIENCE=suho-trading            # JWT audience identifier
```

### External Services
```bash
TELEGRAM_BOT_TOKEN=                   # Telegram bot token (optional)
```

---

## 🔧 Usage Patterns

### 1. Docker Compose Usage
```yaml
# docker-compose.yml
environment:
  - POSTGRES_HOST=${POSTGRES_HOST}
  - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
  - KAFKA_BROKERS=${KAFKA_BROKERS}
```

### 2. Central Hub Static Config Usage
```json
{
  "database": {
    "host": "ENV:POSTGRES_HOST",
    "port": "ENV:POSTGRES_PORT",
    "password": "ENV:POSTGRES_PASSWORD"
  }
}
```

### 3. Application Code Usage
```javascript
// Via Central Hub config resolution
const config = await centralHub.getConfig('database');

// Direct environment access (fallback only)
const fallbackHost = process.env.POSTGRES_HOST || 'localhost';
```

---

## 🛡️ Security Guidelines

### ✅ Secure Practices
```bash
# Use strong passwords
POSTGRES_PASSWORD=complex_secure_password_2024

# Use random JWT secrets
JWT_SECRET=$(openssl rand -base64 32)

# Use environment-specific values
NODE_ENV=production  # For production deployments
```

### ❌ Avoid These
```bash
# DON'T use simple passwords
POSTGRES_PASSWORD=123456

# DON'T use default secrets
JWT_SECRET=secret

# DON'T hardcode in code
const dbHost = 'localhost';  // BAD
```

---

## 🔄 Environment-Specific Configurations

### Development
```bash
NODE_ENV=development
LOG_LEVEL=debug
HOT_RELOAD_ENABLED=true
CORS_ENABLED=true
```

### Staging
```bash
NODE_ENV=staging
LOG_LEVEL=info
HOT_RELOAD_ENABLED=false
CORS_ENABLED=true
```

### Production
```bash
NODE_ENV=production
LOG_LEVEL=warn
HOT_RELOAD_ENABLED=false
CORS_ENABLED=false  # Configure specific origins
```

---

## 📝 Variable Validation

### Required Variables
These variables MUST be set for the system to function:
- `POSTGRES_PASSWORD`
- `CLICKHOUSE_PASSWORD`
- `DRAGONFLY_PASSWORD`
- `ARANGO_ROOT_PASSWORD`
- `JWT_SECRET`
- `KAFKA_BROKERS`
- `NATS_URL`

### Optional Variables
These variables have reasonable defaults:
- `TELEGRAM_BOT_TOKEN` (empty = disabled)
- `LOG_LEVEL` (default: info)
- `NODE_ENV` (default: development)

### Validation Script
```bash
#!/bin/bash
# validate-env.sh
REQUIRED_VARS="POSTGRES_PASSWORD CLICKHOUSE_PASSWORD DRAGONFLY_PASSWORD JWT_SECRET"

for var in $REQUIRED_VARS; do
    if [ -z "${!var}" ]; then
        echo "ERROR: $var is not set"
        exit 1
    fi
done
echo "✅ All required environment variables are set"
```

---

## 🔍 Debugging Environment Variables

### Check Variables in Container
```bash
# List all environment variables
docker exec suho-api-gateway env

# Check specific variable
docker exec suho-api-gateway env | grep POSTGRES_HOST

# Check variable from within container
docker exec suho-api-gateway printenv KAFKA_BROKERS
```

### Validate .env File
```bash
# Check .env syntax
cat .env | grep -E "^[A-Z].*=" | head -10

# Find missing equals signs
cat .env | grep -E "^[A-Z]" | grep -v "="
```

---

**Last Updated**: $(date)
**Version**: 1.0.0
**Total Variables**: 35+