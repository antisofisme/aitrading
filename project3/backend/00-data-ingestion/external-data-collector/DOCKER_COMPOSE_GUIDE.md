# Docker Compose Deployment Guide

## 📍 Ada 2 Docker Compose Files

### 1. **Main Production** (`/backend/docker-compose.yml`)

✅ **File ini yang utama untuk production deployment!**

Location: `/mnt/g/khoirul/aitrading/project3/backend/docker-compose.yml`

**Service Configuration:**
```yaml
external-data-collector:
  container_name: suho-external-collector
  depends_on:
    - nats (healthy)
    - postgresql (healthy)
    - central-hub (started)
  environment:
    - CENTRAL_HUB_URL=http://suho-central-hub:7000
    - DB_HOST=suho-postgresql
    - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
  volumes:
    - external_collector_data:/app/data
    - external_collector_logs:/app/logs
```

**Features:**
- ✅ Integrated dengan semua services (PostgreSQL, NATS, Kafka, Central Hub)
- ✅ Named volumes untuk data persistence
- ✅ Health checks untuk dependencies
- ✅ Production-ready configuration
- ✅ Consistent dengan polygon-live-collector dan polygon-historical-downloader

### 2. **Local Development** (`/00-data-ingestion/external-data-collector/docker-compose.yml`)

⚠️ **Hanya untuk testing lokal / development!**

Location: `/mnt/g/khoirul/aitrading/project3/backend/00-data-ingestion/external-data-collector/docker-compose.yml`

**Service Configuration:**
```yaml
external-data-collector:
  container_name: suho-external-collector-dev
  environment:
    - INSTANCE_ID=external-data-collector-dev-1
  volumes:
    - ./data:/app/data  # Local directory
    - ./logs:/app/logs  # Local directory
```

**Features:**
- ✅ Quick local testing
- ✅ Local file mounts untuk debugging
- ✅ Standalone service testing
- ⚠️ Requires external network: `suho-trading-network`

---

## 🚀 Deployment Options

### Option 1: Production Deployment (Recommended)

**Deploy semua services sekaligus:**

```bash
# Di backend root directory
cd /mnt/g/khoirul/aitrading/project3/backend

# Start all services
docker-compose up -d

# Check external-data-collector logs
docker logs -f suho-external-collector

# Expected output:
# ================================================================================
# EXTERNAL DATA COLLECTOR + CENTRAL HUB
# ================================================================================
# Instance ID: external-data-collector-1
# Central Hub: Enabled
# 🚀 Starting External Data Collector...
# ✅ Registered with Central Hub: external-data-collector
```

**Deploy hanya external-data-collector:**

```bash
cd /mnt/g/khoirul/aitrading/project3/backend

# Start dependencies first
docker-compose up -d postgresql nats central-hub

# Then start external-data-collector
docker-compose up -d external-data-collector

# Check logs
docker logs -f suho-external-collector
```

### Option 2: Local Development

**Testing lokal (requires network sudah exist):**

```bash
# Create network if not exists
docker network create suho-trading-network

# Di external-data-collector directory
cd /mnt/g/khoirul/aitrading/project3/backend/00-data-ingestion/external-data-collector

# Start service
docker-compose up -d

# Check logs
docker logs -f suho-external-collector-dev
```

---

## ⚙️ Environment Variables

### Production (Main docker-compose.yml)

Sudah di-set via docker-compose.yml:

```bash
# Service identity
INSTANCE_ID=external-data-collector-1
LOG_LEVEL=INFO

# Central Hub
CENTRAL_HUB_URL=http://suho-central-hub:7000

# Database (automatic from main compose)
DB_HOST=suho-postgresql
DB_PASSWORD=${POSTGRES_PASSWORD}

# Messaging (automatic)
NATS_URL=nats://suho-nats-server:4222
KAFKA_BROKERS=suho-kafka:9092
```

**Hanya perlu set via `.env` file:**

```bash
# API Keys (optional)
ZAI_API_KEY=your-key-here
FRED_API_KEY=your-key-here
COINGECKO_API_KEY=your-key-here

# Log level (optional)
LOG_LEVEL=INFO
```

### Development (Local docker-compose.yml)

Create `.env` file di `/00-data-ingestion/external-data-collector/`:

```bash
# Required if Central Hub not running
CENTRAL_HUB_URL=http://suho-central-hub:7000

# Optional API keys
ZAI_API_KEY=your-key-here

# Optional database (falls back to JSON)
DB_HOST=suho-postgresql
DB_PASSWORD=suho_secure_password_2024
```

---

## 🔍 Service Discovery

### Via Main Docker Compose

Service akan otomatis register ke Central Hub:

```bash
# Check service registration
curl http://suho-central-hub:7000/api/discovery/services

# Response:
{
  "services": [
    {
      "name": "external-data-collector",
      "status": "healthy",
      "type": "data-collector",
      "capabilities": [
        "economic-calendar",
        "historical-backfill",
        "mql5-data-source"
      ]
    }
  ]
}
```

---

## 📊 Volume Management

### Production Volumes (Named Volumes)

```bash
# List volumes
docker volume ls | grep external

# Output:
# suho-trading_external_collector_data
# suho-trading_external_collector_logs

# Inspect volume
docker volume inspect suho-trading_external_collector_data

# Backup volume
docker run --rm \
  -v suho-trading_external_collector_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/external-data-backup.tar.gz /data
```

### Development Volumes (Local Directories)

```bash
# Data stored in local directories
ls -la /mnt/g/khoirul/aitrading/project3/backend/00-data-ingestion/external-data-collector/data
ls -la /mnt/g/khoirul/aitrading/project3/backend/00-data-ingestion/external-data-collector/logs
```

---

## 🛠️ Common Commands

### Production

```bash
# Start
docker-compose up -d external-data-collector

# Stop
docker-compose stop external-data-collector

# Restart
docker-compose restart external-data-collector

# Logs
docker logs -f suho-external-collector

# Enter container
docker exec -it suho-external-collector bash

# Remove (keeps volumes)
docker-compose rm -f external-data-collector

# Remove with volumes
docker-compose down -v
```

### Development

```bash
# Start
cd 00-data-ingestion/external-data-collector
docker-compose up -d

# Logs
docker logs -f suho-external-collector-dev

# Stop
docker-compose down

# Rebuild
docker-compose build --no-cache
docker-compose up -d
```

---

## 🔧 Troubleshooting

### Service tidak start

```bash
# Check dependencies
docker-compose ps

# Ensure Central Hub running
docker logs suho-central-hub

# Check network
docker network inspect suho-trading-network

# Check health
docker inspect suho-external-collector | grep Health
```

### Cannot connect to Central Hub

```bash
# Test connection
docker exec suho-external-collector curl http://suho-central-hub:7000/health

# Check environment
docker exec suho-external-collector env | grep CENTRAL_HUB

# Fallback: Service will run in standalone mode
# Check logs for: "Central Hub SDK not available - running in standalone mode"
```

### Database connection failed

```bash
# Falls back to JSON automatically
# Check logs for: "Database: JSON fallback"

# Data stored in:
# Production: /var/lib/docker/volumes/suho-trading_external_collector_data/_data
# Development: ./data/date_tracking.json
```

---

## 📝 Best Practices

1. **Production**: Always use main `docker-compose.yml`
   ```bash
   cd /mnt/g/khoirul/aitrading/project3/backend
   docker-compose up -d
   ```

2. **Development**: Use local docker-compose for quick testing
   ```bash
   cd 00-data-ingestion/external-data-collector
   docker-compose up -d
   ```

3. **Environment Variables**: Set sensitive data via `.env` file
   ```bash
   # Create .env in backend root
   ZAI_API_KEY=your-key
   POSTGRES_PASSWORD=secure-password
   ```

4. **Data Persistence**: Production uses named volumes (survives container removal)
   ```bash
   # Volumes persist even after:
   docker-compose down

   # To remove volumes:
   docker-compose down -v
   ```

5. **Monitoring**: Check logs regularly
   ```bash
   # Production
   docker logs -f suho-external-collector

   # Follow metrics in Central Hub
   curl http://suho-central-hub:7000/api/discovery/services
   ```

---

## 🎯 Summary

| Aspect | Production (Main) | Development (Local) |
|--------|------------------|---------------------|
| **File Location** | `/backend/docker-compose.yml` | `/external-data-collector/docker-compose.yml` |
| **Container Name** | `suho-external-collector` | `suho-external-collector-dev` |
| **Network** | `suho-trading-network` (internal) | `suho-trading-network` (external) |
| **Volumes** | Named volumes | Local directories |
| **Dependencies** | Auto-managed | Manual setup |
| **Use Case** | Production deployment | Local testing |

**Recommendation**: ✅ Use production docker-compose.yml for all deployments!

---

**Last Updated**: 2025-10-05
**Status**: Production Ready ✅
