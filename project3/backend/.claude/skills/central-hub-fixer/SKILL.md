---
name: central-hub-fixer
description: Fix and upgrade existing microservices to comply with Suho AI Trading central-hub architecture. Diagnose issues, standardize patterns, and ensure Docker, database connections, and health checks follow best practices.
---

# Central Hub Service Fixer

This skill guides the diagnosis and fixing of existing microservices to ensure they comply with the Suho AI Trading central-hub architecture standards.

## When to Use This Skill

Use this skill when:
- Existing service has connection issues
- Service doesn't follow naming conventions
- Health checks are failing or missing
- Docker configuration is incorrect
- Environment variables are hardcoded
- Service doesn't integrate with central-hub SDK
- Logging is insufficient or incorrect

## Diagnosis Checklist

Before fixing, diagnose the current state:

### 1. Service Identity Check
```bash
# Check container name and hostname
docker ps --filter "name=SERVICE_NAME" --format "table {{.Names}}\t{{.Status}}"

# Verify naming convention
# Expected: suho-{service-name}
# Actual: _______________
```

**Issues to check:**
- [ ] Container name follows `suho-{service-name}` pattern
- [ ] Hostname matches container name
- [ ] Service name uses lowercase-with-hyphens

### 2. File Structure Check
```bash
# Expected structure
{layer}/{service-name}/
├── src/
│   ├── main.py
│   ├── healthcheck.py
│   └── [modules]/
├── config/
│   └── infrastructure.yaml
├── Dockerfile
└── requirements.txt
```

**Issues to check:**
- [ ] All required files exist
- [ ] Files in correct locations
- [ ] No hardcoded paths
- [ ] config/infrastructure.yaml present

### 3. Environment Variables Check

**Common issues:**
```python
# ❌ WRONG - Hardcoded values
POSTGRES_HOST = "localhost"
POSTGRES_PASSWORD = "password123"
API_KEY = "abc123xyz"

# ✅ CORRECT - Environment variables with defaults
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'suho-postgresql')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
API_KEY = os.getenv('API_KEY')
```

**Check for:**
- [ ] All credentials use environment variables
- [ ] Proper defaults for hostnames
- [ ] No secrets in code
- [ ] `.env` file in `.gitignore`

### 4. Database Connection Check

**PostgreSQL/TimescaleDB:**
```python
# Standard pattern
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'suho-postgresql')
POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
POSTGRES_DB = os.getenv('POSTGRES_DB', 'suho_trading')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'suho_admin')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
```

**ClickHouse:**
```python
# Standard pattern - check port number!
CLICKHOUSE_HOST = os.getenv('CLICKHOUSE_HOST', 'suho-clickhouse')
CLICKHOUSE_PORT = int(os.getenv('CLICKHOUSE_PORT', '9000'))  # Native: 9000, HTTP: 8123
CLICKHOUSE_DATABASE = os.getenv('CLICKHOUSE_DATABASE', 'suho_analytics')
CLICKHOUSE_USER = os.getenv('CLICKHOUSE_USER', 'suho_analytics')
CLICKHOUSE_PASSWORD = os.getenv('CLICKHOUSE_PASSWORD')
```

**Common mistakes:**
- [ ] Wrong ClickHouse port (8123 instead of 9000 for native client)
- [ ] Wrong hostname (localhost instead of suho-clickhouse)
- [ ] Hardcoded passwords
- [ ] Missing connection pooling
- [ ] No retry logic

### 5. Health Check Verification

```bash
# Test health check
docker exec suho-{service-name} python3 /app/src/healthcheck.py
echo $?  # Should be 0 if healthy
```

**Required health check pattern:**
```python
#!/usr/bin/env python3
import sys
import logging

logger = logging.getLogger(__name__)

def check_database_connection() -> bool:
    """Verify database connectivity"""
    try:
        # Test connection here
        return True
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        return False

def check_health() -> bool:
    """Run all health checks"""
    checks = [
        ("Database", check_database_connection()),
        # Add other checks
    ]

    all_healthy = all(status for _, status in checks)

    for name, status in checks:
        logger.info(f"{name}: {'✓' if status else '✗'}")

    return all_healthy

if __name__ == "__main__":
    sys.exit(0 if check_health() else 1)
```

**Issues to check:**
- [ ] Health check file exists at `src/healthcheck.py`
- [ ] Exit code 0 for healthy, 1 for unhealthy
- [ ] Tests actual connections (not just returns True)
- [ ] Logs meaningful error messages

### 6. Docker Configuration Check

**Dockerfile issues:**
```dockerfile
# ❌ WRONG - Missing central-hub SDK
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install -r requirements.txt

# ✅ CORRECT - Installs SDK first
FROM python:3.11-slim
WORKDIR /app

# Install central-hub SDK
COPY 01-core-infrastructure/central-hub/sdk/python/ /tmp/central-hub-sdk/
RUN pip install --no-cache-dir /tmp/central-hub-sdk/ && rm -rf /tmp/central-hub-sdk/

# Install dependencies
COPY {layer}/{service-name}/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY {layer}/{service-name}/src/ ./src/
COPY {layer}/{service-name}/config/ ./config/

ENV PYTHONUNBUFFERED=1
CMD ["python", "-u", "src/main.py"]
```

**Check for:**
- [ ] Central-hub SDK installed
- [ ] Correct COPY paths from repository root
- [ ] PYTHONUNBUFFERED=1 set
- [ ] WORKDIR /app
- [ ] No hardcoded paths

### 7. docker-compose.yml Check

**Standard entry pattern:**
```yaml
  {service-name}:
    build:
      context: .
      dockerfile: {layer}/{service-name}/Dockerfile
    container_name: suho-{service-name}
    hostname: suho-{service-name}
    restart: unless-stopped
    environment:
      - INSTANCE_ID={service-name}-1
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - POSTGRES_HOST=suho-postgresql
      - POSTGRES_PORT=5432
      - POSTGRES_DB=suho_trading
      - POSTGRES_USER=suho_admin
      - POSTGRES_PASSWORD=suho_secure_password_2024
      - CLICKHOUSE_HOST=suho-clickhouse
      - CLICKHOUSE_PORT=9000
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
    healthcheck:
      test: ["CMD", "python3", "/app/src/healthcheck.py"]
      interval: 20s
      timeout: 15s
      retries: 3
      start_period: 90s
    labels:
      - "com.suho.service={service-name}"
      - "com.suho.type={service-type}"
```

**Issues to check:**
- [ ] Container name: `suho-{service-name}`
- [ ] Hostname matches container name
- [ ] Restart policy: `unless-stopped`
- [ ] All required environment variables present
- [ ] Volume paths use `./{layer}/{service-name}/`
- [ ] Network: `suho-trading-network`
- [ ] Proper `depends_on` with conditions
- [ ] Health check configured
- [ ] Labels present

### 8. Logging Check

**Standard logging pattern:**
```python
import logging
import os

logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Usage
logger.info("Service started")
logger.error(f"Error occurred: {error}", exc_info=True)
```

**Issues to check:**
- [ ] Logging configured in main.py
- [ ] LOG_LEVEL from environment
- [ ] Proper format string
- [ ] Named logger used
- [ ] exc_info=True for errors

## Common Fix Patterns

### Fix 1: Standardize Database Connections

**Before:**
```python
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="trading",
    user="admin",
    password="password123"
)
```

**After:**
```python
import os
from dotenv import load_dotenv

load_dotenv()

POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'suho-postgresql')
POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
POSTGRES_DB = os.getenv('POSTGRES_DB', 'suho_trading')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'suho_admin')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')

conn = psycopg2.connect(
    host=POSTGRES_HOST,
    port=POSTGRES_PORT,
    database=POSTGRES_DB,
    user=POSTGRES_USER,
    password=POSTGRES_PASSWORD
)
```

### Fix 2: Add Missing Health Check

1. Create `src/healthcheck.py` with proper pattern
2. Update Dockerfile to include health check file
3. Update docker-compose.yml with healthcheck section
4. Test: `docker exec suho-{service-name} python3 /app/src/healthcheck.py`

### Fix 3: Fix ClickHouse Port Issue

**Common mistake:**
```python
# ❌ Using HTTP port for native client
CLICKHOUSE_PORT = 8123
client = clickhouse_connect.get_client(host=host, port=8123)
```

**Fix:**
```python
# ✅ Use native port 9000
CLICKHOUSE_PORT = int(os.getenv('CLICKHOUSE_PORT', '9000'))
client = clickhouse_connect.get_client(host=host, port=CLICKHOUSE_PORT)
```

### Fix 4: Add Central-Hub SDK

**Update Dockerfile:**
```dockerfile
# Add before installing requirements
COPY 01-core-infrastructure/central-hub/sdk/python/ /tmp/central-hub-sdk/
RUN pip install --no-cache-dir /tmp/central-hub-sdk/ && rm -rf /tmp/central-hub-sdk/
```

**Update code to use SDK:**
```python
from central_hub.health import HealthChecker
from central_hub.config import ConfigManager
```

### Fix 5: Standardize Naming

1. Rename service folder: `old-name` → `correct-name`
2. Update docker-compose.yml:
   - Service name
   - Container name: `suho-{service-name}`
   - Hostname
   - Volume paths
   - Volume name
3. Update labels
4. Rebuild: `docker-compose build {service-name}`

### Fix 6: Fix Hardcoded Values

**Search for hardcoded values:**
```bash
# In service folder
grep -r "localhost" src/
grep -r "password" src/
grep -r "api_key" src/
grep -r "5432" src/
```

**Replace with environment variables:**
```python
# Add to .env
POSTGRES_HOST=suho-postgresql
API_KEY=your_key_here

# Update code
host = os.getenv('POSTGRES_HOST', 'suho-postgresql')
api_key = os.getenv('API_KEY')
```

## Verification After Fix

After applying fixes, verify:

### 1. Build Test
```bash
docker-compose build {service-name}
# Should complete without errors
```

### 2. Start Test
```bash
docker-compose up -d {service-name}
docker logs suho-{service-name} --tail 50
# Check for errors
```

### 3. Health Check Test
```bash
docker exec suho-{service-name} python3 /app/src/healthcheck.py
echo $?
# Should return 0
```

### 4. Connection Test
```bash
# Check database connection
docker exec suho-{service-name} python3 -c "
import os
os.environ['POSTGRES_HOST'] = 'suho-postgresql'
# Test connection code
print('Connection OK')
"
```

### 5. Environment Test
```bash
docker exec suho-{service-name} env | grep -E '(POSTGRES|CLICKHOUSE|NATS|KAFKA)'
# Verify all env vars present
```

## Fix Priority Order

When fixing multiple issues, follow this order:

1. **Critical (Fix immediately):**
   - Hardcoded secrets/passwords
   - Wrong database connections
   - Missing health checks
   - Security vulnerabilities

2. **High (Fix soon):**
   - Naming convention violations
   - Missing central-hub SDK
   - Incorrect Dockerfile patterns
   - Missing error handling

3. **Medium (Fix when convenient):**
   - Logging improvements
   - Configuration file standardization
   - Volume mount optimizations
   - Label additions

4. **Low (Nice to have):**
   - Code style improvements
   - Comment additions
   - Documentation updates

## Common Error Messages and Fixes

### Error: "Connection refused to localhost"
**Cause:** Service using localhost instead of Docker service names
**Fix:** Change to `suho-postgresql`, `suho-clickhouse`, etc.

### Error: "Authentication failed for user"
**Cause:** Wrong credentials or missing environment variables
**Fix:** Check docker-compose.yml environment section

### Error: "Health check failing"
**Cause:** Health check script not working or missing dependencies
**Fix:** Test health check manually, add error logging

### Error: "Permission denied"
**Cause:** File permissions or volume mount issues
**Fix:** Check volume mount paths and file permissions

### Error: "Module not found: central_hub"
**Cause:** Central-hub SDK not installed
**Fix:** Update Dockerfile to install SDK

## Rollback Plan

If fixes cause issues:

1. **Stop service:**
   ```bash
   docker-compose stop {service-name}
   ```

2. **Restore from git:**
   ```bash
   git checkout HEAD -- {layer}/{service-name}/
   git checkout HEAD -- docker-compose.yml
   ```

3. **Rebuild with old config:**
   ```bash
   docker-compose build {service-name}
   docker-compose up -d {service-name}
   ```

4. **Verify old version working:**
   ```bash
   docker logs suho-{service-name} --tail 50
   ```

## Example Usage

"Fix the data-bridge service - it's using localhost instead of suho-postgresql and the health check is failing"

This skill will systematically diagnose connection issues, update environment variables, fix health check, and verify the service is working correctly.
