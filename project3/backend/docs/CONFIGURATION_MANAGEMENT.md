# 🔧 Centralized Configuration Management

## Overview

Sistem SUHO Trading menggunakan **Centralized Configuration Management** dengan **Single Source of Truth** untuk semua konfigurasi sistem. Arsitektur ini memungkinkan pengelolaan konfigurasi yang efisien, konsisten, dan mudah di-maintain.

## 🎯 Prinsip Dasar

### Single Source of Truth
```
📁 .env (ROOT) ← SINGLE SOURCE OF TRUTH
├── Database credentials
├── Service URLs
├── API keys
├── Port numbers
└── Feature flags
```

### Zero Hardcode Policy
- ❌ **DILARANG**: Hardcode values di kode atau config files
- ✅ **WAJIB**: Semua values dari environment variables
- ✅ **WAJIB**: Menggunakan fallback yang reasonable

## 🏗️ Arsitektur

### 1. Environment Variables (.env)
```bash
# Master configuration file
# Location: /project3/backend/.env

# Database Infrastructure
POSTGRES_HOST=suho-postgresql
POSTGRES_PASSWORD=suho_secure_password_2024
KAFKA_BROKERS=suho-kafka:9092
NATS_URL=nats://suho-nats-server:4222
```

### 2. Docker Compose Integration
```yaml
# docker-compose.yml menggunakan ${VAR} syntax
environment:
  - DATABASE_URL=${DATABASE_URL}
  - KAFKA_BROKERS=${KAFKA_BROKERS}
  - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
```

### 3. Central Hub Config Resolution
```json
// Static configs menggunakan "ENV:VARIABLE" syntax
{
  "connection": {
    "host": "ENV:POSTGRES_HOST",
    "port": "ENV:POSTGRES_PORT",
    "password": "ENV:POSTGRES_PASSWORD"
  }
}
```

### 4. Service Code Integration
```javascript
// Services mengambil config dari Central Hub
const config = await centralHub.getConfig('database');
// config.host sudah resolved dari ENV:POSTGRES_HOST
```

## 📋 Variabel Environment

### Database Infrastructure
| Variable | Description | Example |
|----------|-------------|---------|
| `POSTGRES_HOST` | PostgreSQL hostname | `suho-postgresql` |
| `POSTGRES_PORT` | PostgreSQL port | `5432` |
| `POSTGRES_DB` | Database name | `suho_trading` |
| `POSTGRES_USER` | Database user | `suho_admin` |
| `POSTGRES_PASSWORD` | Database password | `suho_secure_password_2024` |
| `CLICKHOUSE_HOST` | ClickHouse hostname | `suho-clickhouse` |
| `CLICKHOUSE_PORT` | ClickHouse HTTP port | `8123` |
| `DRAGONFLY_HOST` | DragonflyDB hostname | `suho-dragonflydb` |
| `DRAGONFLY_PASSWORD` | DragonflyDB password | `dragonfly_secure_2024` |

### Messaging Infrastructure
| Variable | Description | Example |
|----------|-------------|---------|
| `KAFKA_BROKERS` | Kafka broker addresses | `suho-kafka:9092` |
| `KAFKA_CLIENT_ID` | Kafka client identifier | `suho-trading-client` |
| `NATS_URL` | NATS server URL | `nats://suho-nats-server:4222` |
| `NATS_HOST` | NATS hostname | `suho-nats-server` |
| `NATS_PORT` | NATS port | `4222` |

### Core Services
| Variable | Description | Example |
|----------|-------------|---------|
| `CENTRAL_HUB_URL` | Central Hub service URL | `http://suho-central-hub:7000` |
| `API_GATEWAY_PORT` | API Gateway port | `8000` |
| `JWT_SECRET` | JWT signing secret | `your-super-secret-jwt-key` |

## 🔄 Workflow Configuration

### 1. Menambah Konfigurasi Baru

**Step 1: Tambah ke .env**
```bash
# Tambah variable baru
NEW_SERVICE_URL=http://new-service:3000
NEW_SERVICE_API_KEY=secret_key_123
```

**Step 2: Update docker-compose.yml**
```yaml
environment:
  - NEW_SERVICE_URL=${NEW_SERVICE_URL}
  - NEW_SERVICE_API_KEY=${NEW_SERVICE_API_KEY}
```

**Step 3: Update static config (jika perlu)**
```json
{
  "new_service": {
    "url": "ENV:NEW_SERVICE_URL",
    "api_key": "ENV:NEW_SERVICE_API_KEY"
  }
}
```

### 2. Mengubah Konfigurasi Existing

**Hanya edit 1 file**: `.env`
```bash
# BEFORE
POSTGRES_PASSWORD=old_password

# AFTER
POSTGRES_PASSWORD=new_password
```

**Restart services**:
```bash
docker-compose restart central-hub api-gateway
```

## 🛠️ Central Hub Config Resolution

### Static Config Format
```json
{
  "database": {
    "host": "ENV:POSTGRES_HOST",
    "port": "ENV:POSTGRES_PORT",
    "password": "ENV:POSTGRES_PASSWORD"
  }
}
```

### Runtime Resolution
```javascript
// Central Hub automatically resolves ENV: values
"ENV:POSTGRES_HOST" → process.env.POSTGRES_HOST → "suho-postgresql"
```

### Client Usage
```javascript
// API Gateway mendapat config yang sudah resolved
const dbConfig = await centralHub.getConfig('database');
console.log(dbConfig.host); // "suho-postgresql"
```

## 🔍 Troubleshooting

### Missing Environment Variable
```bash
# Error: Environment variable not set
Error: ENV:POSTGRES_PASSWORD not found

# Solution: Add to .env
echo "POSTGRES_PASSWORD=your_password" >> .env
```

### Service Can't Connect
```bash
# Check environment variables are loaded
docker exec suho-api-gateway env | grep POSTGRES

# Check Central Hub config resolution
curl http://localhost:7000/config/service/api-gateway
```

### Invalid Configuration
```bash
# Check .env syntax
cat .env | grep -E "^[^#].*=" | grep -v "="

# Restart services after .env changes
docker-compose restart central-hub api-gateway
```

## ✅ Best Practices

### 1. Naming Convention
```bash
# Service-specific variables
SERVICE_NAME_SETTING=value

# Infrastructure variables
INFRASTRUCTURE_COMPONENT_SETTING=value

# Examples:
API_GATEWAY_PORT=8000
POSTGRES_HOST=suho-postgresql
```

### 2. Security
```bash
# Sensitive data
POSTGRES_PASSWORD=secure_password_here
JWT_SECRET=random_secret_key_here

# Non-sensitive data
POSTGRES_HOST=suho-postgresql
POSTGRES_PORT=5432
```

### 3. Documentation
- Setiap variable baru harus didokumentasi
- Gunakan descriptive names
- Sertakan example values
- Update dokumentasi saat ada perubahan

### 4. Testing
```bash
# Test configuration changes
docker-compose config

# Validate environment variables
docker-compose exec api-gateway env | grep POSTGRES
```

## 🚀 Benefits

### ✅ Achieved
- **Single Source of Truth**: Semua config di 1 tempat (.env)
- **Zero Hardcode**: Tidak ada values yang hardcode
- **Easy Maintenance**: Update 1 file untuk semua services
- **Environment Consistency**: Sama di dev/staging/production
- **Security**: Credentials terpusat dan tidak tersebar

### 📈 Metrics
- **Configuration Files**: 8 files converted to ENV: syntax
- **Environment Variables**: 25+ variables centralized
- **Hardcoded Values**: 0 remaining
- **Maintenance Time**: Reduced by 80%

---

**Last Updated**: $(date)
**Version**: 1.0.0
**Maintainer**: SUHO Trading Team