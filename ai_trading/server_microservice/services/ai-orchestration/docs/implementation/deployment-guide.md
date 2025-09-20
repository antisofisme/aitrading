# AI Orchestration Service - Deployment Guide

## Overview
Complete deployment guide for the AI Orchestration microservice with Docker containerization, environment configuration, and production best practices.

## Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+ recommended), macOS, or Windows with WSL2
- **CPU**: 4+ cores (8+ cores recommended for production)
- **Memory**: 8GB RAM minimum (16GB+ recommended for production)
- **Storage**: 20GB+ available disk space
- **Network**: Stable internet connection for AI service integrations

### Software Dependencies
- **Docker**: 20.10+ with Docker Compose 2.0+
- **Python**: 3.11+ (for local development)
- **Git**: Latest version
- **Redis**: 6.0+ (optional, for caching)

### Required API Keys
Before deployment, obtain the following API keys:
- **Handit AI API Key**: Contact Handit AI for access
- **Langfuse API Keys**: Register at https://cloud.langfuse.com
- **Letta API Key**: If using hosted Letta service
- **OpenAI API Key**: For LLM integrations (optional)

## Environment Configuration

### 1. Clone Repository and Navigate
```bash
git clone <repository-url>
cd server_microservice/services/ai-orchestration
```

### 2. Environment Variables Setup
Copy the environment template and configure:

```bash
cp .env.example .env
```

### 3. Essential Environment Variables

**Service Configuration:**
```bash
# Core service settings
MICROSERVICE_ENVIRONMENT=production
AI_ORCHESTRATION_PORT=8003
AI_ORCHESTRATION_DEBUG=false
AI_ORCHESTRATION_HOST=0.0.0.0

# Performance settings
RATE_LIMITING_REQUESTS_PER_MINUTE=1000
PERFORMANCE_MEMORY_LIMIT_MB=2048
```

**AI Services Configuration:**
```bash
# Handit AI (Required)
HANDIT_AI_ENABLED=true
HANDIT_AI_API_KEY=your_handit_ai_api_key_here
HANDIT_AI_BASE_URL=https://api.handit.ai
HANDIT_AI_TIMEOUT=30

# Langfuse Observability (Recommended)
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-lf-your_public_key_here
LANGFUSE_SECRET_KEY=sk-lf-your_secret_key_here
LANGFUSE_HOST=https://cloud.langfuse.com

# Letta Memory (Optional)
LETTA_MEMORY_ENABLED=true
LETTA_API_KEY=your_letta_api_key_here
LETTA_BASE_URL=http://localhost:8283

# LangGraph Workflows (Enabled by default)
LANGGRAPH_ENABLED=true
LANGGRAPH_MAX_CONCURRENT=10
LANGGRAPH_TIMEOUT=300
```

**Database & Cache (Optional):**
```bash
# PostgreSQL (if persistent storage needed)
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=ai_orchestration_db
DATABASE_USER=postgres
DATABASE_PASSWORD=your_secure_password

# Redis Cache (recommended for production)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=7
REDIS_PASSWORD=your_redis_password
```

**Security Configuration:**
```bash
# Security settings (recommended for production)
ENABLE_AUTHENTICATION=true
JWT_SECRET=your_very_secure_jwt_secret_minimum_32_chars
SESSION_TIMEOUT=3600
API_KEY_HEADER=X-API-Key
```

## Deployment Methods

### Method 1: Docker Compose (Recommended)

#### Development Deployment
Quick setup for development and testing:

```bash
# Build and start services
docker-compose up -d --build

# View logs
docker-compose logs -f ai-orchestration

# Health check
curl http://localhost:8003/health
```

#### Production Deployment
Optimized production deployment:

```bash
# Create production environment file
cp .env.example .env.production
# Edit .env.production with production values

# Build with production settings
docker-compose -f docker-compose.prod.yml up -d --build

# Verify deployment
docker-compose -f docker-compose.prod.yml ps
```

**Production docker-compose.prod.yml:**
```yaml
version: '3.8'

services:
  ai-orchestration:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    ports:
      - "8003:8003"
    env_file:
      - .env.production
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8003/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    depends_on:
      - redis
      - postgres
    networks:
      - ai-orchestration-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: unless-stopped
    networks:
      - ai-orchestration-network

  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: ${DATABASE_NAME}
      POSTGRES_USER: ${DATABASE_USER}
      POSTGRES_PASSWORD: ${DATABASE_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    networks:
      - ai-orchestration-network

volumes:
  redis_data:
  postgres_data:

networks:
  ai-orchestration-network:
    driver: bridge
```

### Method 2: Docker Single Container

#### Build Container
```bash
# Build optimized production image
docker build -t ai-orchestration:latest .

# Run with environment file
docker run -d \
  --name ai-orchestration \
  --env-file .env \
  -p 8003:8003 \
  --restart unless-stopped \
  ai-orchestration:latest
```

### Method 3: Local Python Development

#### Setup Virtual Environment
```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run development server
python main.py
```

## Tiered Dependency Management

The service supports tiered dependency installation for optimized deployment:

### Tier 1: Core Service (< 50MB)
Essential framework components only:
```bash
pip install -r requirements/tier1-core.txt
```

### Tier 2: Service + Database (< 200MB)
Core + database connections:
```bash
pip install -r requirements/tier2-service.txt
```

### Tier 3: AI Basic (< 500MB)
Core + basic AI capabilities:
```bash
pip install -r requirements/tier3-ai-basic.txt
```

### Tier 4: AI Advanced (< 2GB)
Full AI orchestration capabilities:
```bash
pip install -r requirements/tier4-ai-advanced.txt
```

### Use in Dockerfile
The Dockerfile supports building different tiers:
```bash
# Build with specific tier
docker build --target tier3 -t ai-orchestration:ai-basic .

# Production build (uses appropriate tier automatically)
docker build --target production -t ai-orchestration:production .
```

## Configuration Validation

### Pre-Deployment Checklist
```bash
# 1. Validate environment variables
python -c "
import os
from dotenv import load_dotenv
load_dotenv()

required_vars = [
    'AI_ORCHESTRATION_PORT',
    'HANDIT_AI_API_KEY',
    'LANGFUSE_PUBLIC_KEY',
    'LANGFUSE_SECRET_KEY'
]

missing = [var for var in required_vars if not os.getenv(var)]
if missing:
    print(f'Missing required environment variables: {missing}')
    exit(1)
else:
    print('✅ All required environment variables are set')
"

# 2. Test configuration loading
python -c "
import sys
sys.path.append('src')
from infrastructure.core.config_core import CoreConfig
config = CoreConfig('ai-orchestration')
print('✅ Configuration loaded successfully')
print(f'Service enabled: {config.get(\"enabled\", True)}')
"
```

### Configuration Testing
```bash
# Test with development configuration
MICROSERVICE_ENVIRONMENT=development python main.py --validate-config

# Test with production configuration
MICROSERVICE_ENVIRONMENT=production python main.py --validate-config
```

## Health Checks & Monitoring

### Basic Health Check
```bash
# Service health
curl http://localhost:8003/health

# Detailed status
curl http://localhost:8003/status

# Component metrics
curl http://localhost:8003/api/v1/ai-orchestration/metrics
```

### Expected Healthy Response
```json
{
  "status": "healthy",
  "service": "ai-orchestration-unified",
  "uptime_seconds": 3600,
  "microservice_version": "2.0.0",
  "component_status": {
    "handit_ai": true,
    "letta_memory": true,
    "langgraph_workflows": true,
    "langfuse_observability": true
  },
  "active_workflows": 5,
  "active_tasks": 12
}
```

### Monitoring Setup

#### Prometheus Metrics (Future)
```bash
# Add to docker-compose.yml
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
```

## Production Optimization

### Performance Tuning
```bash
# Environment variables for production
PERFORMANCE_ENABLE_CACHING=true
PERFORMANCE_CACHE_TTL_SECONDS=300
PERFORMANCE_PARALLEL_EXECUTION=true
PERFORMANCE_MEMORY_LIMIT_MB=4096

# Concurrency settings
HANDIT_AI_MAX_CONCURRENT=20
LANGGRAPH_MAX_CONCURRENT=20
AGENT_COORDINATOR_MAX_AGENTS=200
```

### Resource Limits
```bash
# Docker resource limits
docker run -d \
  --name ai-orchestration \
  --memory="4g" \
  --cpus="4.0" \
  --env-file .env \
  ai-orchestration:latest
```

### Log Management
```bash
# Configure log levels
LOG_LEVEL=INFO
LOG_FORMAT=json
ENABLE_AI_LOGGING=true
ENABLE_WORKFLOW_LOGGING=true

# Log rotation (add to docker-compose.yml)
logging:
  driver: "json-file"
  options:
    max-size: "100m"
    max-file: "10"
```

## Security Hardening

### Container Security
```bash
# Run as non-root user (already configured in Dockerfile)
USER aiorchestration

# Read-only root filesystem (add to docker-compose.yml)
read_only: true
tmpfs:
  - /tmp
  - /app/cache
```

### Network Security
```bash
# Firewall configuration
ufw allow 8003/tcp  # AI Orchestration service
ufw allow 6379/tcp  # Redis (if external)
ufw allow 5432/tcp  # PostgreSQL (if external)

# HTTPS termination (use reverse proxy)
# Example nginx configuration in production
```

### Secrets Management
```bash
# Use Docker secrets in production
echo "your_api_key" | docker secret create handit_api_key -
echo "your_jwt_secret" | docker secret create jwt_secret -

# Reference in docker-compose.yml
secrets:
  - handit_api_key
  - jwt_secret
```

## Backup & Recovery

### Data Backup
```bash
# Database backup
docker exec postgres pg_dump -U postgres ai_orchestration_db > backup.sql

# Redis backup
docker exec redis redis-cli --rdb /data/backup.rdb
```

### Service Recovery
```bash
# Quick restart
docker-compose restart ai-orchestration

# Full rebuild
docker-compose down
docker-compose up -d --build

# Rollback to previous version
docker tag ai-orchestration:latest ai-orchestration:backup
docker pull ai-orchestration:stable
docker tag ai-orchestration:stable ai-orchestration:latest
docker-compose up -d
```

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check logs
docker-compose logs ai-orchestration

# Common causes:
# 1. Missing environment variables
# 2. Port conflicts
# 3. Insufficient memory
# 4. Invalid API keys
```

#### Performance Issues
```bash
# Check resource usage
docker stats

# Monitor service metrics
curl http://localhost:8003/api/v1/ai-orchestration/metrics

# Check component health
curl http://localhost:8003/status
```

#### AI Component Failures
```bash
# Check individual component status
curl http://localhost:8003/status | jq '.component_status'

# Test AI services individually
curl -X POST http://localhost:8003/api/v1/orchestration/execute \
  -H "Content-Type: application/json" \
  -d '{"operation_type": "handit_task", "parameters": {"task_type": "analysis"}}'
```

### Debug Mode
```bash
# Enable debug mode
AI_ORCHESTRATION_DEBUG=true
LOG_LEVEL=DEBUG

# Run with debug logging
docker-compose up ai-orchestration
```

## Scaling & Load Balancing

### Horizontal Scaling
```bash
# Scale AI orchestration instances
docker-compose up -d --scale ai-orchestration=3

# Use load balancer (nginx example)
upstream ai_orchestration {
    server localhost:8003;
    server localhost:8004;
    server localhost:8005;
}
```

### Performance Monitoring
```bash
# Monitor performance metrics
watch -n 5 'curl -s http://localhost:8003/api/v1/ai-orchestration/metrics | jq ".api_metrics"'

# Load testing
ab -n 1000 -c 10 http://localhost:8003/health
```

## Maintenance

### Updates
```bash
# Update service
git pull
docker-compose build --no-cache
docker-compose up -d

# Update dependencies
pip freeze > requirements.txt
docker-compose build --no-cache
```

### Regular Maintenance
```bash
# Weekly tasks
docker system prune -f  # Clean unused containers
docker volume prune -f  # Clean unused volumes

# Monthly tasks
# Update base images
# Review and update API keys
# Check security patches
```

This deployment guide provides comprehensive instructions for setting up the AI Orchestration service in various environments with proper configuration, monitoring, and maintenance procedures.