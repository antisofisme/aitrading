---
name: central-hub-debugger
description: Debug and troubleshoot Suho AI Trading microservices. Diagnose container issues, analyze logs, check database connections, verify message broker integration, and resolve common runtime errors.
---

# Central Hub Service Debugger

This skill guides systematic debugging of microservices in the Suho AI Trading central-hub architecture.

## Quick Diagnostic Commands

### Service Status Check
```bash
# Check all Suho services
docker ps --filter "name=suho" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Check specific service
docker ps --filter "name=suho-{service-name}" --format "table {{.Names}}\t{{.Status}}"

# Check service health
docker inspect --format='{{.State.Health.Status}}' suho-{service-name}
```

### Log Analysis
```bash
# View recent logs
docker logs suho-{service-name} --tail 100

# Follow logs in real-time
docker logs suho-{service-name} --follow

# Filter logs by error level
docker logs suho-{service-name} 2>&1 | grep -i error

# View logs with timestamps
docker logs suho-{service-name} --timestamps --tail 200
```

### Resource Check
```bash
# Check container resource usage
docker stats suho-{service-name} --no-stream

# Check disk usage
docker system df

# Check specific service disk usage
docker exec suho-{service-name} df -h
```

## Common Issue Patterns

### Issue 1: Service Won't Start

**Symptoms:**
- Container exits immediately
- Status shows "Exited (1)"
- Health check never runs

**Diagnosis:**
```bash
# Check exit code and error
docker ps -a --filter "name=suho-{service-name}" --format "{{.Status}}"

# View full logs
docker logs suho-{service-name}

# Check last command that ran
docker inspect suho-{service-name} --format='{{.Config.Cmd}}'
```

**Common Causes:**

1. **Missing environment variable:**
   ```python
   # Error in logs: KeyError: 'POSTGRES_PASSWORD'
   # Fix: Add to docker-compose.yml
   environment:
     - POSTGRES_PASSWORD=suho_secure_password_2024
   ```

2. **Import error:**
   ```python
   # Error in logs: ModuleNotFoundError: No module named 'clickhouse_connect'
   # Fix: Add to requirements.txt
   clickhouse-connect==0.6.8
   ```

3. **File not found:**
   ```python
   # Error in logs: FileNotFoundError: config/infrastructure.yaml
   # Fix: Check volume mount in docker-compose.yml
   volumes:
     - ./{layer}/{service-name}/config:/app/config:ro
   ```

### Issue 2: Database Connection Failures

**Symptoms:**
- "Connection refused" errors
- "Could not connect to server" messages
- Timeout errors

**Diagnosis:**
```bash
# Check database container is running
docker ps --filter "name=suho-postgresql"
docker ps --filter "name=suho-clickhouse"

# Test connection from service container
docker exec suho-{service-name} nc -zv suho-postgresql 5432
docker exec suho-{service-name} nc -zv suho-clickhouse 9000

# Check database logs
docker logs suho-postgresql --tail 100
docker logs suho-clickhouse --tail 100

# Verify environment variables
docker exec suho-{service-name} env | grep -E '(POSTGRES|CLICKHOUSE)'
```

**Common Causes:**

1. **Wrong hostname:**
   ```python
   # ❌ Using localhost
   POSTGRES_HOST = "localhost"

   # ✅ Use Docker service name
   POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'suho-postgresql')
   ```

2. **Wrong port:**
   ```python
   # ❌ Common mistake for ClickHouse
   CLICKHOUSE_PORT = 8123  # This is HTTP port

   # ✅ Use native protocol port
   CLICKHOUSE_PORT = int(os.getenv('CLICKHOUSE_PORT', '9000'))
   ```

3. **Database not ready:**
   ```yaml
   # Fix: Add proper depends_on
   depends_on:
     postgresql:
       condition: service_healthy  # Wait for health check
     clickhouse:
       condition: service_healthy
   ```

4. **Wrong credentials:**
   ```bash
   # Test PostgreSQL connection manually
   docker exec suho-postgresql psql -U suho_admin -d suho_trading -c "SELECT 1"

   # Test ClickHouse connection manually
   docker exec suho-clickhouse clickhouse-client --user suho_analytics --password clickhouse_secure_2024 --query "SELECT 1"
   ```

### Issue 3: Health Check Failing

**Symptoms:**
- Container status shows "unhealthy"
- Service restarts repeatedly
- `docker inspect` shows health check failures

**Diagnosis:**
```bash
# Check health status
docker inspect suho-{service-name} --format='{{.State.Health.Status}}'

# View health check history
docker inspect suho-{service-name} --format='{{range .State.Health.Log}}{{.Output}}{{end}}'

# Run health check manually
docker exec suho-{service-name} python3 /app/src/healthcheck.py
echo $?  # Should be 0 if healthy

# Check health check configuration
docker inspect suho-{service-name} --format='{{.Config.Healthcheck}}'
```

**Common Causes:**

1. **Health check file missing:**
   ```bash
   # Verify file exists
   docker exec suho-{service-name} ls -la /app/src/healthcheck.py

   # Fix: Create healthcheck.py in src/ folder
   ```

2. **Health check not testing actual connections:**
   ```python
   # ❌ Fake health check
   def check_health():
       return True  # Always returns healthy!

   # ✅ Real health check
   def check_database_connection():
       try:
           conn = psycopg2.connect(...)
           conn.execute("SELECT 1")
           conn.close()
           return True
       except Exception as e:
           logger.error(f"Database check failed: {e}")
           return False
   ```

3. **Timeout too short:**
   ```yaml
   # ❌ Not enough time
   healthcheck:
     timeout: 5s
     start_period: 10s

   # ✅ Adequate time for startup
   healthcheck:
     timeout: 15s
     start_period: 90s  # Give service time to initialize
   ```

### Issue 4: Message Broker Connection Issues

**Symptoms:**
- "NATS connection failed" errors
- "Kafka broker not available" messages
- Message publishing/consuming not working

**Diagnosis:**
```bash
# Check NATS cluster
docker ps --filter "name=nats" --format "table {{.Names}}\t{{.Status}}"

# Check Kafka
docker ps --filter "name=suho-kafka"

# Test NATS connection from service
docker exec suho-{service-name} nc -zv nats-1 4222
docker exec suho-{service-name} nc -zv nats-2 4222
docker exec suho-{service-name} nc -zv nats-3 4222

# Check NATS logs
docker logs nats-1 --tail 50

# Check Kafka logs
docker logs suho-kafka --tail 50

# Verify NATS environment variable
docker exec suho-{service-name} env | grep NATS_URL
```

**Common Causes:**

1. **Single NATS server instead of cluster:**
   ```python
   # ❌ Single server
   NATS_URL = "nats://nats-1:4222"

   # ✅ Full cluster for high availability
   NATS_URL = os.getenv('NATS_URL', 'nats://nats-1:4222,nats://nats-2:4222,nats://nats-3:4222')
   ```

2. **Missing depends_on for message brokers:**
   ```yaml
   # Add to docker-compose.yml
   depends_on:
     nats-1:
       condition: service_healthy
     nats-2:
       condition: service_healthy
     nats-3:
       condition: service_healthy
     kafka:
       condition: service_healthy
   ```

### Issue 5: High Memory/CPU Usage

**Symptoms:**
- Container using excessive resources
- System slowing down
- Out of memory errors

**Diagnosis:**
```bash
# Monitor resource usage
docker stats suho-{service-name}

# Check process inside container
docker exec suho-{service-name} ps aux

# Check memory usage details
docker exec suho-{service-name} cat /proc/meminfo

# View container limits
docker inspect suho-{service-name} --format='{{.HostConfig.Memory}} {{.HostConfig.CpuShares}}'
```

**Common Causes:**

1. **Memory leak:**
   ```python
   # Check for growing data structures
   # Common culprits: unclosed connections, cached data

   # ❌ Connections not closed
   conn = psycopg2.connect(...)
   # ... use connection ...
   # Never closed!

   # ✅ Proper cleanup
   try:
       conn = psycopg2.connect(...)
       # ... use connection ...
   finally:
       conn.close()
   ```

2. **Large data processing:**
   ```python
   # ❌ Loading entire dataset
   df = pd.read_sql("SELECT * FROM large_table", conn)

   # ✅ Process in batches
   for chunk in pd.read_sql("SELECT * FROM large_table", conn, chunksize=1000):
       process(chunk)
   ```

3. **Infinite loops or tight loops:**
   ```python
   # ❌ No sleep in polling loop
   while True:
       check_messages()  # CPU at 100%!

   # ✅ Add sleep interval
   while True:
       check_messages()
       time.sleep(1)  # Let CPU breathe
   ```

### Issue 6: Data Not Processing

**Symptoms:**
- Service running but no data output
- Tables empty when they should have data
- No error messages in logs

**Diagnosis:**
```bash
# Check if service is actually running
docker exec suho-{service-name} ps aux

# Verify database connections
docker exec suho-postgresql psql -U suho_admin -d suho_trading -c "
SELECT * FROM {table_name} ORDER BY timestamp DESC LIMIT 5;
"

docker exec suho-clickhouse clickhouse-client --query "
SELECT * FROM suho_analytics.{table_name} ORDER BY timestamp DESC LIMIT 5;
"

# Check service logs for processing messages
docker logs suho-{service-name} | grep -i "processing\|inserted\|saved"

# Verify input data exists
docker exec suho-clickhouse clickhouse-client --query "
SELECT COUNT(*) FROM suho_analytics.raw_ticks;
"
```

**Common Causes:**

1. **Silent failures:**
   ```python
   # ❌ Catching exceptions without logging
   try:
       process_data()
   except:
       pass  # Silent failure!

   # ✅ Log all errors
   try:
       process_data()
   except Exception as e:
       logger.error(f"Processing failed: {e}", exc_info=True)
       raise
   ```

2. **No input data:**
   ```bash
   # Check upstream service is producing data
   docker logs suho-data-bridge | grep "Published"
   docker logs suho-dukascopy-historical-downloader | grep "Downloaded"
   ```

3. **Wrong table/database:**
   ```python
   # Verify table names match
   # Check config/infrastructure.yaml
   # Verify environment variables
   ```

## Debugging Workflow

### Step 1: Identify the Scope
```bash
# Is it a single service or multiple?
docker ps --filter "name=suho" --format "table {{.Names}}\t{{.Status}}"

# Check infrastructure services
docker ps --filter "name=suho-postgresql"
docker ps --filter "name=suho-clickhouse"
docker ps --filter "name=suho-dragonflydb"
docker ps --filter "name=nats"
docker ps --filter "name=suho-kafka"
```

### Step 2: Check Service Logs
```bash
# View recent logs
docker logs suho-{service-name} --tail 200 --timestamps

# Look for patterns:
# - Error messages
# - Stack traces
# - Connection messages
# - Last successful operation
```

### Step 3: Verify Dependencies
```bash
# Check all dependencies are healthy
docker inspect suho-{service-name} --format='{{range .Config.Env}}{{println .}}{{end}}' | grep -E '(POSTGRES|CLICKHOUSE|NATS|KAFKA)'

# Test each dependency
docker exec suho-{service-name} nc -zv suho-postgresql 5432
docker exec suho-{service-name} nc -zv suho-clickhouse 9000
docker exec suho-{service-name} nc -zv nats-1 4222
```

### Step 4: Check Configuration
```bash
# View service configuration
docker exec suho-{service-name} cat /app/config/infrastructure.yaml

# Verify environment variables
docker exec suho-{service-name} env | sort

# Check file structure
docker exec suho-{service-name} ls -la /app/
docker exec suho-{service-name} ls -la /app/src/
docker exec suho-{service-name} ls -la /app/config/
```

### Step 5: Test Health Check
```bash
# Run health check manually
docker exec suho-{service-name} python3 /app/src/healthcheck.py
echo $?

# View health check history
docker inspect suho-{service-name} --format='{{json .State.Health}}' | jq
```

### Step 6: Interactive Debugging
```bash
# Get shell access
docker exec -it suho-{service-name} /bin/bash

# Inside container, test Python imports
python3 -c "import clickhouse_connect; print('OK')"
python3 -c "import psycopg2; print('OK')"
python3 -c "import nats; print('OK')"

# Test database connection manually
python3 -c "
import os
import clickhouse_connect
client = clickhouse_connect.get_client(
    host=os.getenv('CLICKHOUSE_HOST'),
    port=int(os.getenv('CLICKHOUSE_PORT')),
    username=os.getenv('CLICKHOUSE_USER'),
    password=os.getenv('CLICKHOUSE_PASSWORD')
)
print(client.query('SELECT 1').result_rows)
"
```

## Log Analysis Patterns

### Error Pattern Recognition
```bash
# Python exceptions
docker logs suho-{service-name} 2>&1 | grep "Traceback"

# Connection errors
docker logs suho-{service-name} 2>&1 | grep -i "connection\|refused\|timeout"

# Authentication errors
docker logs suho-{service-name} 2>&1 | grep -i "auth\|password\|permission"

# Module errors
docker logs suho-{service-name} 2>&1 | grep -i "modulenotfound\|importerror"

# Database errors
docker logs suho-{service-name} 2>&1 | grep -i "database\|query\|table"
```

### Success Pattern Recognition
```bash
# Service started
docker logs suho-{service-name} 2>&1 | grep -i "started\|running\|ready"

# Data processing
docker logs suho-{service-name} 2>&1 | grep -i "processing\|processed\|inserted"

# Connections established
docker logs suho-{service-name} 2>&1 | grep -i "connected\|connection established"
```

## Network Debugging

### Check Container Network
```bash
# View network configuration
docker inspect suho-{service-name} --format='{{json .NetworkSettings.Networks}}' | jq

# Should be on suho-trading-network
docker network inspect suho-trading-network | jq '.[] | .Containers'

# Test inter-container connectivity
docker exec suho-{service-name} ping -c 3 suho-postgresql
docker exec suho-{service-name} ping -c 3 suho-clickhouse

# Check DNS resolution
docker exec suho-{service-name} nslookup suho-postgresql
docker exec suho-{service-name} nslookup suho-clickhouse
```

## Performance Debugging

### Identify Bottlenecks
```bash
# Check CPU usage over time
docker stats suho-{service-name} --no-stream

# Monitor I/O
docker exec suho-{service-name} iostat 1 5

# Check query performance (PostgreSQL)
docker exec suho-postgresql psql -U suho_admin -d suho_trading -c "
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;
"

# Check query performance (ClickHouse)
docker exec suho-clickhouse clickhouse-client --query "
SELECT query, elapsed, read_rows, read_bytes
FROM system.query_log
WHERE type = 'QueryFinish'
ORDER BY event_time DESC
LIMIT 10
FORMAT Vertical
"
```

## Quick Fixes Reference

### Restart Service
```bash
docker-compose restart {service-name}
```

### Rebuild Service
```bash
docker-compose build {service-name}
docker-compose up -d {service-name}
```

### View Service Build Logs
```bash
docker-compose build {service-name} --no-cache --progress=plain
```

### Reset Service Completely
```bash
docker-compose stop {service-name}
docker-compose rm -f {service-name}
docker-compose build --no-cache {service-name}
docker-compose up -d {service-name}
```

### Check Recent Changes
```bash
# Git changes
git log --oneline --all -10

# Recently modified files
find {layer}/{service-name}/ -type f -mtime -1 -ls

# Docker image history
docker history suho-{service-name}
```

## Preventive Debugging

### Add Comprehensive Logging
```python
# At service startup
logger.info(f"Service starting - Instance ID: {INSTANCE_ID}")
logger.info(f"Database host: {POSTGRES_HOST}:{POSTGRES_PORT}")
logger.info(f"ClickHouse host: {CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}")

# Before critical operations
logger.info("Connecting to database...")
logger.info("Fetching data from ClickHouse...")
logger.info("Publishing message to NATS...")

# After operations
logger.info(f"Processed {count} records")
logger.info(f"Inserted {rows} rows into {table}")
```

### Add Error Context
```python
try:
    result = perform_operation()
except Exception as e:
    logger.error(
        f"Operation failed: {e}",
        exc_info=True,
        extra={
            'operation': 'data_processing',
            'timestamp': datetime.now(),
            'input_data': data_summary
        }
    )
    raise
```

## Example Usage

"The tick-aggregator service is showing as unhealthy and the logs show connection refused errors to ClickHouse"

This skill will systematically check ClickHouse container status, test network connectivity, verify environment variables, check port configuration, and identify the root cause.
