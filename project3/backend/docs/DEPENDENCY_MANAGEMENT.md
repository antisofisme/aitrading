# Service Dependency Management

## Overview

Comprehensive dependency management system with health checks and startup ordering for the AI Trading distributed system.

## Architecture

### Health Check System

```
┌─────────────────────────────────────────────────────────────┐
│                     Health Check Flow                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Service Start → Dependencies Ready? → Health Check Pass     │
│       ↓                    ↓                      ↓          │
│   Wait/Retry          Verify Connections      Report Healthy │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Components

1. **Bash Health Check Scripts** (`healthcheck.sh`)
   - Lightweight shell scripts
   - Call Python health check scripts
   - Fast execution (< 1s)

2. **Python Health Check Scripts** (`healthcheck.py`)
   - Verify all service dependencies
   - Test actual connections
   - Report success/failure

3. **Docker Health Checks**
   - Configured in Dockerfiles
   - Execute every 10-15 seconds
   - Start period: 30-60 seconds
   - Auto-restart unhealthy services

4. **Startup Retry Logic**
   - Exponential backoff (1s → 2s → 4s → 8s → 16s → 30s)
   - Max 10 retries per connection
   - Graceful degradation
   - Clear error messages

## Dependency Graph

```
Infrastructure Services (No Dependencies)
├── PostgreSQL (TimescaleDB)
├── ClickHouse
├── DragonflyDB
├── NATS
├── Kafka
└── Zookeeper

Core Services (Infrastructure Dependencies)
└── Central Hub
    ├── Depends: PostgreSQL, DragonflyDB, NATS, Kafka
    └── Health: HTTP API check

Application Services (Core + Infrastructure Dependencies)
├── Tick Aggregator
│   ├── Depends: PostgreSQL, ClickHouse, NATS, Central Hub
│   └── Health: Multi-dependency check
│
├── Data Bridge
│   ├── Depends: PostgreSQL, ClickHouse, NATS, Kafka, Central Hub
│   └── Health: Multi-dependency check
│
└── Historical Downloader
    ├── Depends: ClickHouse, NATS, Central Hub
    └── Health: Multi-dependency check
```

## Health Check Configuration

### Infrastructure Services

**PostgreSQL:**
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U suho_admin -d suho_trading"]
  interval: 30s
  timeout: 10s
  retries: 5
```

**ClickHouse:**
```yaml
healthcheck:
  test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:8123/ping"]
  interval: 30s
  timeout: 10s
  retries: 5
```

**NATS:**
```yaml
healthcheck:
  test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:8222/healthz"]
  interval: 15s
  timeout: 5s
  retries: 3
```

**Kafka:**
```yaml
healthcheck:
  test: ["CMD", "kafka-broker-api-versions", "--bootstrap-server", "suho-kafka:9092"]
  interval: 30s
  timeout: 10s
  retries: 5
```

### Application Services

**Central Hub:**
```yaml
healthcheck:
  test: ["CMD", "/app/healthcheck.sh"]
  interval: 10s
  timeout: 5s
  start_period: 30s
  retries: 5
depends_on:
  postgresql: {condition: service_healthy}
  dragonflydb: {condition: service_healthy}
  nats: {condition: service_healthy}
  kafka: {condition: service_healthy}
```

**Tick Aggregator:**
```yaml
healthcheck:
  test: ["CMD", "/app/healthcheck.sh"]
  interval: 15s
  timeout: 10s
  start_period: 60s
  retries: 3
depends_on:
  postgresql: {condition: service_healthy}
  clickhouse: {condition: service_healthy}
  nats: {condition: service_healthy}
  central-hub: {condition: service_healthy}
```

**Data Bridge:**
```yaml
healthcheck:
  test: ["CMD", "/app/healthcheck.sh"]
  interval: 15s
  timeout: 10s
  start_period: 60s
  retries: 3
depends_on:
  postgresql: {condition: service_healthy}
  clickhouse: {condition: service_healthy}
  nats: {condition: service_healthy}
  kafka: {condition: service_healthy}
  central-hub: {condition: service_healthy}
```

## Startup Retry Logic

### Python Implementation

```python
from shared.utils.connection_retry import connect_with_retry

# Async connections
await connect_with_retry(
    service.connect,
    "Service Name",
    max_retries=10
)

# Sync connections
from shared.utils.connection_retry import sync_connect_with_retry

sync_connect_with_retry(
    service.connect,
    "Service Name",
    max_retries=10
)
```

### Retry Behavior

- **Initial backoff:** 1 second
- **Max backoff:** 30 seconds
- **Multiplier:** 2x (exponential)
- **Max retries:** 10 attempts
- **Total max wait:** ~8 minutes

**Retry sequence:**
```
Attempt 1: Wait 1s
Attempt 2: Wait 2s
Attempt 3: Wait 4s
Attempt 4: Wait 8s
Attempt 5: Wait 16s
Attempt 6: Wait 30s (capped)
Attempt 7-10: Wait 30s each
```

## Testing

### Automated Test Script

```bash
cd /mnt/g/khoirul/aitrading/project3/backend
chmod +x scripts/test-health-checks.sh
./scripts/test-health-checks.sh
```

### Manual Testing

**Test 1: Clean Start**
```bash
docker-compose down -v
docker-compose up -d
sleep 60
docker ps --format "table {{.Names}}\t{{.Status}}"
# All should show "(healthy)"
```

**Test 2: Dependency Failure**
```bash
docker-compose stop suho-clickhouse
sleep 20
docker ps --format "table {{.Names}}\t{{.Status}}"
# tick-aggregator, data-bridge should show "(unhealthy)"
```

**Test 3: Recovery**
```bash
docker-compose start suho-clickhouse
sleep 60
docker ps --format "table {{.Names}}\t{{.Status}}"
# All should recover to "(healthy)"
```

**Test 4: Check Logs**
```bash
docker logs suho-tick-aggregator | grep -i error
docker logs suho-data-bridge | grep -i error
# Should show retry attempts, minimal connection errors
```

## Validation Criteria

✅ **Startup Order:**
- Services start in correct dependency order
- No premature connection attempts

✅ **Health Checks:**
- All services report "(healthy)" within 2 minutes
- Unhealthy services restart automatically

✅ **Dependency Recovery:**
- Services detect dependency failures within 30s
- Services recover within 60s of dependency restoration

✅ **Retry Logic:**
- Services show exponential backoff in logs
- Clear error messages for troubleshooting
- No crashes, only health check failures

## Troubleshooting

### Service Stuck in "Starting"

```bash
# Check logs
docker logs <service-name> --tail 100

# Check health check script
docker exec <service-name> /app/healthcheck.sh
```

### Service Perpetually Unhealthy

```bash
# Test individual dependencies
docker exec <service-name> python3 /app/src/healthcheck.py

# Check dependency service
docker ps --filter name=<dependency>
```

### Services Not Waiting for Dependencies

```bash
# Verify docker-compose.yml has depends_on with condition
docker-compose config | grep -A 5 "depends_on"
```

## Best Practices

1. **Health Check Timeout:** Keep < 5s for responsive detection
2. **Start Period:** Allow 2-3x normal startup time
3. **Retry Intervals:** Use exponential backoff to prevent overwhelming failed services
4. **Logging:** Log all retry attempts with backoff timing
5. **Graceful Degradation:** Continue running with degraded functionality when possible

## Files Modified

### Health Check Scripts
- `/01-core-infrastructure/central-hub/healthcheck.sh`
- `/02-data-processing/tick-aggregator/healthcheck.sh`
- `/02-data-processing/tick-aggregator/src/healthcheck.py`
- `/02-data-processing/data-bridge/healthcheck.sh`
- `/02-data-processing/data-bridge/src/healthcheck.py`
- `/00-data-ingestion/polygon-historical-downloader/healthcheck.sh`
- `/00-data-ingestion/polygon-historical-downloader/src/healthcheck.py`

### Dockerfiles
- `/01-core-infrastructure/central-hub/Dockerfile`
- `/02-data-processing/tick-aggregator/Dockerfile`
- `/02-data-processing/data-bridge/Dockerfile`
- `/00-data-ingestion/polygon-historical-downloader/Dockerfile`

### Docker Compose
- `/docker-compose.yml` - Added depends_on conditions and healthchecks

### Application Code
- `/shared/utils/connection_retry.py` - Retry utility module
- `/02-data-processing/tick-aggregator/src/main.py` - Added retry logic
- `/02-data-processing/data-bridge/src/main.py` - Added retry logic

### Documentation
- `/docs/DEPENDENCY_MANAGEMENT.md` - This file
- `/scripts/test-health-checks.sh` - Automated test script

## Impact

### Before Implementation
- ❌ Services start in random order
- ❌ Connection failures during startup
- ❌ No health status visibility
- ❌ Manual intervention required for recovery

### After Implementation
- ✅ Deterministic startup order
- ✅ Automatic retry with backoff
- ✅ Real-time health monitoring
- ✅ Automatic failure recovery
- ✅ Production-ready reliability
