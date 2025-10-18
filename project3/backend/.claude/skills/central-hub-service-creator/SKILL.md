---
name: central-hub-service-creator
description: Create new microservices compliant with Suho AI Trading central-hub architecture. Ensures consistent folder structure, connection patterns, Docker integration, and health checks across all services in the 00-data-ingestion, 02-data-processing, and 03-machine-learning layers.
---

# Central Hub Service Creator

This skill guides the creation of new microservices that integrate seamlessly with the Suho AI Trading central-hub architecture.

## Service Layer Types

Services are organized into three pipeline layers:

1. **00-data-ingestion** - Data collectors and downloaders
2. **02-data-processing** - Data transformation and aggregation
3. **03-machine-learning** - Feature engineering and ML inference

## Required Folder Structure

```
{layer}/{service-name}/
├── src/
│   ├── main.py              # Service entry point
│   ├── healthcheck.py       # Health check endpoint
│   └── [modules]/           # Service-specific modules
├── config/
│   └── infrastructure.yaml  # Service configuration
├── Dockerfile               # Docker build instructions
└── requirements.txt         # Python dependencies
```

## Standard Python Patterns

### 1. Imports Organization

```python
# Standard library
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Third-party
import yaml
import asyncio
from dotenv import load_dotenv

# Local modules
from .module_name import ClassName
```

### 2. Environment Variables Loading

```python
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Service identity
INSTANCE_ID = os.getenv('INSTANCE_ID', 'service-name-1')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
```

### 3. Configuration Loading

```python
import yaml
from pathlib import Path

def load_config(config_path: str = "config/infrastructure.yaml") -> dict:
    """Load service configuration from YAML file"""
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_file, 'r') as f:
        return yaml.safe_load(f)

# Usage
config = load_config()
```

### 4. Database Connection Patterns

**PostgreSQL/TimescaleDB:**
```python
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'suho-postgresql')
POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
POSTGRES_DB = os.getenv('POSTGRES_DB', 'suho_trading')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'suho_admin')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
```

**ClickHouse:**
```python
CLICKHOUSE_HOST = os.getenv('CLICKHOUSE_HOST', 'suho-clickhouse')
CLICKHOUSE_PORT = int(os.getenv('CLICKHOUSE_PORT', '9000'))  # Native: 9000, HTTP: 8123
CLICKHOUSE_DATABASE = os.getenv('CLICKHOUSE_DATABASE', 'suho_analytics')
CLICKHOUSE_USER = os.getenv('CLICKHOUSE_USER', 'suho_analytics')
CLICKHOUSE_PASSWORD = os.getenv('CLICKHOUSE_PASSWORD')
```

**DragonflyDB (Redis-compatible):**
```python
DRAGONFLY_HOST = os.getenv('DRAGONFLY_HOST', 'suho-dragonflydb')
DRAGONFLY_PORT = int(os.getenv('DRAGONFLY_PORT', '6379'))
DRAGONFLY_PASSWORD = os.getenv('DRAGONFLY_PASSWORD')
DRAGONFLY_DB = int(os.getenv('DRAGONFLY_DB', '0'))
```

**NATS Cluster (3 nodes):**
```python
NATS_URL = os.getenv('NATS_URL', 'nats://nats-1:4222,nats://nats-2:4222,nats://nats-3:4222')
```

**Kafka:**
```python
KAFKA_BROKERS = os.getenv('KAFKA_BROKERS', 'suho-kafka:9092')
```

### 5. Logging Pattern

```python
import logging

logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Usage
logger.info("Service started")
logger.error(f"Error occurred: {error}", exc_info=True)
```

### 6. Error Handling Pattern

```python
try:
    # Critical operation
    result = await perform_operation()
except ConnectionError as e:
    logger.error(f"Connection failed: {e}", exc_info=True)
    # Implement retry logic or graceful degradation
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise
```

### 7. Health Check Implementation

Create `src/healthcheck.py`:

```python
#!/usr/bin/env python3
"""
Health check endpoint for service monitoring
Exit code 0 = healthy, 1 = unhealthy
"""
import sys
import logging

logger = logging.getLogger(__name__)

def check_database_connection() -> bool:
    """Verify database connectivity"""
    try:
        # Test database connection
        # Example: execute simple query
        return True
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        return False

def check_message_broker() -> bool:
    """Verify message broker connectivity"""
    try:
        # Test NATS/Kafka connection
        return True
    except Exception as e:
        logger.error(f"Message broker check failed: {e}")
        return False

def check_health() -> bool:
    """Run all health checks"""
    checks = [
        ("Database", check_database_connection()),
        ("Message Broker", check_message_broker()),
    ]

    all_healthy = all(status for _, status in checks)

    for name, status in checks:
        logger.info(f"{name}: {'✓' if status else '✗'}")

    return all_healthy

if __name__ == "__main__":
    sys.exit(0 if check_health() else 1)
```

## Dockerfile Template

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install central-hub SDK (if service needs it)
COPY 01-core-infrastructure/central-hub/sdk/python/ /tmp/central-hub-sdk/
RUN pip install --no-cache-dir /tmp/central-hub-sdk/ && rm -rf /tmp/central-hub-sdk/

# Install Python dependencies
COPY {layer}/{service-name}/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY {layer}/{service-name}/src/ ./src/
COPY {layer}/{service-name}/config/ ./config/

# Set environment
ENV PYTHONUNBUFFERED=1

# Run the service
CMD ["python", "-u", "src/main.py"]
```

## requirements.txt Template

```txt
# Python version: 3.11+

# Core dependencies
python-dotenv==1.0.0
pyyaml==6.0.1

# Database clients (add as needed)
asyncpg==0.30.0              # PostgreSQL async
clickhouse-connect==0.6.8    # ClickHouse
redis==5.0.0                 # DragonflyDB/Redis

# Message brokers (add as needed)
nats-py==2.6.0              # NATS
aiokafka==0.10.0            # Kafka async

# Utilities
httpx>=0.27.0
aiohttp==3.9.0
python-json-logger==2.0.7
```

## config/infrastructure.yaml Template

```yaml
service:
  name: {service-name}
  version: "1.0.0"
  description: "{Service description}"

# Database configurations
postgresql:
  host: suho-postgresql
  port: 5432
  database: suho_trading
  user: suho_admin
  # Password from environment variable

clickhouse:
  host: suho-clickhouse
  port: 9000  # Native protocol (use 8123 for HTTP)
  database: suho_analytics
  user: suho_analytics
  # Password from environment variable

dragonflydb:
  host: suho-dragonflydb
  port: 6379
  db: 0
  # Password from environment variable

# Message broker configurations
nats:
  urls:
    - nats://nats-1:4222
    - nats://nats-2:4222
    - nats://nats-3:4222

kafka:
  brokers:
    - suho-kafka:9092

# Service-specific configurations
processing:
  batch_size: 1000
  poll_interval: 60
  # Add service-specific settings here
```

## docker-compose.yml Entry Template

```yaml
  {service-name}:
    build:
      context: .
      dockerfile: {layer}/{service-name}/Dockerfile
    container_name: suho-{service-name}
    hostname: suho-{service-name}
    restart: unless-stopped
    environment:
      # Service identity
      - INSTANCE_ID={service-name}-1
      - LOG_LEVEL=${LOG_LEVEL:-INFO}

      # PostgreSQL/TimescaleDB connection
      - POSTGRES_HOST=suho-postgresql
      - POSTGRES_PORT=5432
      - POSTGRES_DB=suho_trading
      - POSTGRES_USER=suho_admin
      - POSTGRES_PASSWORD=suho_secure_password_2024

      # ClickHouse connection
      - CLICKHOUSE_HOST=suho-clickhouse
      - CLICKHOUSE_PORT=9000  # Native: 9000, HTTP: 8123
      - CLICKHOUSE_DATABASE=suho_analytics
      - CLICKHOUSE_USER=suho_analytics
      - CLICKHOUSE_PASSWORD=clickhouse_secure_2024

      # DragonflyDB connection (if needed)
      - DRAGONFLY_HOST=suho-dragonflydb
      - DRAGONFLY_PORT=6379
      - DRAGONFLY_PASSWORD=dragonfly_secure_2024
      - DRAGONFLY_DB=0

      # NATS cluster connection
      - NATS_URL=nats://nats-1:4222,nats://nats-2:4222,nats://nats-3:4222

      # Kafka connection
      - KAFKA_BROKERS=suho-kafka:9092

      # Python
      - PYTHONUNBUFFERED=1
    volumes:
      - ./{layer}/{service-name}/config:/app/config:ro
      - {service-name}_logs:/app/logs
    networks:
      - suho-trading-network
    depends_on:
      postgresql:
        condition: service_healthy
      clickhouse:
        condition: service_healthy
      dragonflydb:
        condition: service_healthy
      nats-1:
        condition: service_healthy
      nats-2:
        condition: service_healthy
      nats-3:
        condition: service_healthy
      kafka:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python3", "/app/src/healthcheck.py"]
      interval: 20s
      timeout: 15s
      retries: 3
      start_period: 90s
    labels:
      - "com.suho.service={service-name}"
      - "com.suho.type={service-type}"  # data-collector, data-processor, ml-service
```

## Volume Entry in docker-compose.yml

Add to volumes section:

```yaml
volumes:
  {service-name}_logs:
    driver: local
    labels:
      - "com.suho.data={service-name}-logs"
```

## Naming Conventions

- **Service name**: lowercase-with-hyphens (e.g., `tick-aggregator`)
- **Container name**: `suho-{service-name}` (e.g., `suho-tick-aggregator`)
- **Hostname**: Same as container name
- **Volume name**: `{service-name}_logs` (e.g., `tick_aggregator_logs`)
- **Network**: Always `suho-trading-network`
- **Labels**: `com.suho.service`, `com.suho.type`

## Pre-Creation Checklist

Before creating a new service, verify:

- [ ] Service name follows naming convention
- [ ] Service layer determined (00, 02, or 03)
- [ ] Dependencies identified (which databases/brokers needed)
- [ ] Configuration requirements documented
- [ ] Health check strategy defined
- [ ] Logging requirements specified

## Post-Creation Checklist

After creating a new service, verify:

- [ ] All files created in correct locations
- [ ] Dockerfile builds successfully
- [ ] docker-compose.yml entry added
- [ ] Volume entry added to docker-compose.yml
- [ ] Environment variables configured
- [ ] Health check passes
- [ ] Service starts without errors
- [ ] Connections to dependencies work
- [ ] Logging outputs correctly
- [ ] README.md created (if needed)

## Common Pitfalls to Avoid

1. **Hardcoded values** - Always use environment variables with defaults
2. **Inconsistent naming** - Follow the naming conventions strictly
3. **Missing health checks** - Every service MUST have a health check
4. **Wrong port numbers** - ClickHouse native=9000, HTTP=8123
5. **Missing dependencies** - Declare all depends_on in docker-compose.yml
6. **Absolute paths** - Use relative paths from service root
7. **No error handling** - Wrap critical operations in try-except
8. **Missing logging** - Log all important events and errors

## Example Usage

"Create a new service called 'sentiment-analyzer' in the 03-machine-learning layer that reads from ClickHouse and publishes to Kafka"

This skill will ensure the service follows all central-hub patterns and integrates seamlessly with existing infrastructure.
