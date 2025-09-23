# AI Trading Platform - Plan2 Deployment Guide

## 🚀 Overview

This deployment guide covers the comprehensive Plan2 architecture with the complete database stack and all 20+ microservices integrated into a single, orchestrated Docker Compose environment.

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Database Stack](#database-stack)
3. [Service Architecture](#service-architecture)
4. [Prerequisites](#prerequisites)
5. [Quick Start](#quick-start)
6. [Configuration](#configuration)
7. [Service URLs](#service-urls)
8. [Monitoring](#monitoring)
9. [Troubleshooting](#troubleshooting)
10. [Production Considerations](#production-considerations)

## 🏗️ Architecture Overview

Plan2 implements a comprehensive microservices architecture with:

- **6 Database Systems** for different data patterns
- **20+ Microservices** for complete trading functionality
- **Streaming Platform** for real-time data processing
- **Monitoring Stack** for observability
- **Load Balancer** for service distribution

### Service Layers

```
┌─────────────────────────────────────────────────────────────┐
│                     NGINX Load Balancer                     │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                       │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Core Services │ Trading Services│    Support Services     │
│   - API Gateway │ - AI Orchestr.  │ - User Management       │
│   - Config Svc  │ - Trading Eng.  │ - Billing Service       │
│   - Database    │ - ML Predictor  │ - Notification          │
│                 │ - Risk Analyzer │ - Analytics             │
└─────────────────┴─────────────────┴─────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                      Database Layer                         │
├──────────┬──────────┬──────────┬──────────┬──────────┬──────┤
│PostgreSQL│DragonflyDB│ClickHouse│ Weaviate │ ArangoDB │Redpanda│
│  (OLTP)  │ (Cache)  │(Analytics)│(Vectors) │ (Graph)  │(Stream)│
└──────────┴──────────┴──────────┴──────────┴──────────┴──────┘
```

## 💾 Database Stack

### Primary Databases

| Database | Purpose | Port | Use Cases |
|----------|---------|------|-----------|
| **PostgreSQL** | OLTP/Primary | 5432 | User data, transactions, configurations |
| **DragonflyDB** | High-perf cache | 6379 | Session storage, real-time caching |
| **ClickHouse** | OLAP/Analytics | 8123, 9000 | Time-series data, analytics queries |
| **Weaviate** | Vector database | 8080 | AI embeddings, semantic search |
| **ArangoDB** | Graph database | 8529 | Relationship mapping, social graphs |
| **Redpanda** | Streaming platform | 19092 | Event streaming, message queues |

### Legacy Support

| Database | Purpose | Port | Notes |
|----------|---------|------|-------|
| **Redis** | Legacy cache | 6380 | Backward compatibility only |

## 🎯 Service Architecture

### Core Services (Tier 1)
- **Configuration Service** (8012) - Central configuration management
- **API Gateway** (3001) - Request routing and authentication
- **Database Service** (8008) - Data abstraction layer

### Trading Services (Tier 2)
- **AI Orchestrator** (8020) - Level 4 AI coordination
- **Trading Engine** (9000) - Core trading logic
- **ML Predictor** (8021) - Machine learning predictions
- **Risk Analyzer** (8022) - Risk management
- **Portfolio Manager** (9001) - Portfolio optimization
- **Order Management** (9002) - Order processing

### Support Services (Tier 3)
- **Data Bridge** (5001) - External data integration
- **Central Hub** (7000) - Service coordination
- **Notification Service** (9003) - Alerts and notifications
- **User Management** (8010) - User authentication/authorization
- **Billing Service** (8011) - Subscription and billing
- **Payment Service** (8013) - Payment processing
- **Compliance Monitor** (8014) - Regulatory compliance
- **Backtesting Engine** (8015) - Strategy backtesting

### Analytics Services (Tier 4)
- **Performance Analytics** (9100) - Performance metrics
- **Usage Monitoring** (9101) - Usage analytics
- **Revenue Analytics** (9102) - Revenue tracking
- **Chain Debug System** (8030) - Error tracking
- **AI Chain Analytics** (8031) - AI performance analysis

### Monitoring Services (Tier 5)
- **Prometheus** (9090) - Metrics collection
- **Grafana** (3000) - Visualization dashboards
- **Nginx** (80/443) - Load balancing and SSL termination

## 📋 Prerequisites

### System Requirements

```bash
# Minimum system requirements
- CPU: 8+ cores
- RAM: 16GB+ (32GB recommended)
- Storage: 100GB+ SSD
- Network: 1Gbps+ connection
```

### Software Dependencies

```bash
# Required software
- Docker Engine 20.10+
- Docker Compose 2.0+
- Git
- curl/wget
- jq (for testing scripts)
```

### Installation

```bash
# Install Docker (Ubuntu/Debian)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install jq
sudo apt-get install jq
```

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <your-repo>
cd aitrading/project

# Copy environment file
cp .env.plan2 .env

# Make scripts executable
chmod +x scripts/test-plan2-startup.sh
```

### 2. Configure Environment

```bash
# Edit environment variables
nano .env

# Key variables to set:
# - Database passwords
# - API keys for trading exchanges
# - Notification credentials
# - JWT secrets
```

### 3. Start Services

```bash
# Option 1: Use the test script (recommended)
./scripts/test-plan2-startup.sh

# Option 2: Manual startup
docker-compose -f docker-compose-plan2.yml --env-file .env up -d

# Option 3: Gradual startup (for debugging)
# Start databases first
docker-compose -f docker-compose-plan2.yml up -d postgres dragonflydb clickhouse weaviate arangodb redpanda

# Wait for health checks, then start core services
docker-compose -f docker-compose-plan2.yml up -d configuration-service api-gateway database-service

# Continue with remaining services...
```

### 4. Verify Deployment

```bash
# Check all services are running
docker-compose -f docker-compose-plan2.yml ps

# Check health status
docker-compose -f docker-compose-plan2.yml ps --format table

# Test API endpoints
curl http://localhost:3001/health
curl http://localhost:8012/health
```

## ⚙️ Configuration

### Environment Variables

The `.env.plan2` file contains all configuration options. Key sections:

#### Database Configuration
```bash
# PostgreSQL
POSTGRES_PASSWORD=ai_trading_secure_pass_2024
POSTGRES_URL=postgresql://ai_trading_user:${POSTGRES_PASSWORD}@postgres:5432/ai_trading

# DragonflyDB
DRAGONFLY_PASSWORD=dragonfly_secure_pass_2024
DRAGONFLY_URL=redis://dragonflydb:6379

# ClickHouse
CLICKHOUSE_PASSWORD=clickhouse_secure_pass_2024
CLICKHOUSE_URL=http://clickhouse:8123

# Weaviate
WEAVIATE_URL=http://weaviate:8080

# ArangoDB
ARANGO_PASSWORD=ai_trading_graph_pass_2024
ARANGO_URL=http://arangodb:8529

# Redpanda
REDPANDA_BROKERS=redpanda:9092
```

#### Security Configuration
```bash
# JWT Configuration
JWT_SECRET=ai_trading_jwt_super_secret_key_change_in_production_2024

# Rate Limiting
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=100
```

#### External APIs
```bash
# Trading APIs
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET_KEY=your_binance_secret_key_here

# Notifications
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
SMTP_USER=your_email@gmail.com
```

### Service-Specific Configuration

Each service can be configured via environment variables. See the docker-compose file for complete variable lists.

## 🌐 Service URLs

### Public Endpoints (via Nginx)

| Service | URL | Description |
|---------|-----|-------------|
| API Gateway | http://localhost/api/ | Main API entry point |
| Configuration | http://localhost/config/ | Configuration management |
| Trading Engine | http://localhost/trading/ | Trading operations |
| AI Orchestrator | http://localhost/ai/ | AI coordination |
| ML Predictor | http://localhost/ml/ | Machine learning |
| Risk Analyzer | http://localhost/risk/ | Risk management |
| Portfolio | http://localhost/portfolio/ | Portfolio management |
| Orders | http://localhost/orders/ | Order management |
| Analytics | http://localhost/analytics/ | Performance analytics |
| Debug | http://localhost/debug/ | Debug interface |

### Direct Service Access

| Service | Direct URL | Port |
|---------|------------|------|
| API Gateway | http://localhost:3001 | 3001 |
| Configuration | http://localhost:8012 | 8012 |
| Database Service | http://localhost:8008 | 8008 |
| AI Orchestrator | http://localhost:8020 | 8020 |
| Trading Engine | http://localhost:9000 | 9000 |
| ML Predictor | http://localhost:8021 | 8021 |
| Risk Analyzer | http://localhost:8022 | 8022 |

### Monitoring & Admin

| Service | URL | Credentials |
|---------|-----|-------------|
| Grafana | http://localhost:3000 | admin/admin123 |
| Prometheus | http://localhost:9090 | - |

### Database Connections

| Database | Connection String | Port |
|----------|-------------------|------|
| PostgreSQL | postgresql://ai_trading_user:pass@localhost:5432/ai_trading | 5432 |
| DragonflyDB | redis://localhost:6379 | 6379 |
| ClickHouse | http://localhost:8123 | 8123 |
| Weaviate | http://localhost:8080 | 8080 |
| ArangoDB | http://localhost:8529 | 8529 |
| Redpanda | localhost:19092 | 19092 |

## 📊 Monitoring

### Prometheus Metrics

All services expose metrics at `/metrics` endpoint:

```bash
# Example metrics endpoints
curl http://localhost:3001/metrics  # API Gateway
curl http://localhost:8012/metrics  # Configuration Service
curl http://localhost:9000/metrics  # Trading Engine
```

### Grafana Dashboards

Access Grafana at http://localhost:3000 (admin/admin123) for:

- **System Overview** - Overall system health
- **Trading Metrics** - Trading performance
- **Database Performance** - Database metrics
- **Service Health** - Individual service status
- **Error Tracking** - Error rates and patterns

### Health Checks

```bash
# Check all service health
for port in 3001 8012 8008 8020 9000 8021 8022; do
  echo "Checking port $port:"
  curl -s http://localhost:$port/health | jq .
done

# Database health checks
docker exec ai-trading-postgres pg_isready -U ai_trading_user
docker exec ai-trading-dragonflydb redis-cli ping
docker exec ai-trading-clickhouse wget -q --spider http://localhost:8123/ping
```

## 🔧 Troubleshooting

### Common Issues

#### Services Won't Start

```bash
# Check Docker daemon
sudo systemctl status docker

# Check available resources
docker system df
docker system prune  # Clean up if needed

# Check logs
docker-compose -f docker-compose-plan2.yml logs [service-name]
```

#### Database Connection Issues

```bash
# Check database health
docker-compose -f docker-compose-plan2.yml ps

# Test connections manually
docker exec -it ai-trading-postgres psql -U ai_trading_user -d ai_trading
docker exec -it ai-trading-dragonflydb redis-cli
```

#### Memory Issues

```bash
# Check memory usage
docker stats

# Increase Docker memory limits in Docker Desktop
# Or add swap space on Linux:
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### Service Discovery Issues

```bash
# Check network connectivity
docker network ls
docker network inspect ai-trading-network

# Test service-to-service communication
docker exec ai-trading-api-gateway curl http://configuration-service:8012/health
```

### Debug Commands

```bash
# View all container logs
docker-compose -f docker-compose-plan2.yml logs

# Follow logs for specific service
docker-compose -f docker-compose-plan2.yml logs -f trading-engine

# Execute commands in containers
docker exec -it ai-trading-postgres bash
docker exec -it ai-trading-dragonflydb redis-cli

# Check resource usage
docker stats --no-stream

# Inspect container configuration
docker inspect ai-trading-postgres
```

### Performance Optimization

```bash
# Restart specific services
docker-compose -f docker-compose-plan2.yml restart trading-engine

# Scale services (if needed)
docker-compose -f docker-compose-plan2.yml up -d --scale ml-predictor=2

# Clean up unused resources
docker system prune -a
docker volume prune
```

## 🚀 Production Considerations

### Security Hardening

1. **Change Default Passwords**
   ```bash
   # Generate strong passwords
   openssl rand -base64 32  # For database passwords
   openssl rand -hex 64     # For JWT secrets
   ```

2. **SSL/TLS Configuration**
   ```bash
   # Generate SSL certificates
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout config/nginx/ssl/key.pem \
     -out config/nginx/ssl/cert.pem
   ```

3. **Network Security**
   - Use Docker secrets for sensitive data
   - Implement network policies
   - Enable firewall rules
   - Use VPN for admin access

### Scaling Considerations

1. **Horizontal Scaling**
   ```bash
   # Scale stateless services
   docker-compose -f docker-compose-plan2.yml up -d --scale ml-predictor=3
   docker-compose -f docker-compose-plan2.yml up -d --scale risk-analyzer=2
   ```

2. **Database Scaling**
   - PostgreSQL: Read replicas
   - ClickHouse: Cluster setup
   - DragonflyDB: Redis Cluster
   - Weaviate: Multi-node cluster

3. **Load Balancing**
   - Configure Nginx upstream pools
   - Implement health checks
   - Use external load balancers

### Backup Strategy

```bash
# Database backups
# PostgreSQL
docker exec ai-trading-postgres pg_dump -U ai_trading_user ai_trading > backup_postgres.sql

# ClickHouse
docker exec ai-trading-clickhouse clickhouse-backup create

# Configuration backup
docker exec ai-trading-configuration-service tar -czf /tmp/config-backup.tar.gz /app/config
```

### Monitoring & Alerting

1. **Set up alerts in Prometheus**
2. **Configure Grafana notifications**
3. **Implement log aggregation (ELK stack)**
4. **Set up external monitoring (DataDog, New Relic)**

## 📄 Additional Resources

- [Docker Compose Reference](https://docs.docker.com/compose/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [DragonflyDB Documentation](https://www.dragonflydb.io/docs)
- [ClickHouse Documentation](https://clickhouse.com/docs)
- [Weaviate Documentation](https://weaviate.io/developers/weaviate)
- [ArangoDB Documentation](https://www.arangodb.com/docs/)
- [Redpanda Documentation](https://docs.redpanda.com/)

## 📞 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review service logs: `docker-compose logs [service-name]`
3. Open an issue in the project repository
4. Consult the monitoring dashboards for system health

---

**Note**: This deployment is configured for development/testing. For production use, implement additional security measures, monitoring, and backup strategies.