# Skill: central-hub Service

## Purpose
Service coordination hub. Manages service registry, health monitoring, configuration management, and message routing across all services.

## Key Facts
- **Phase**: Core Infrastructure (Phase 1)
- **Status**: ✅ Active, Production
- **Priority**: P0 (Critical - orchestration layer for all services)
- **Function**: Service discovery, health checks, config management, coordination

## Data Flow
```
All Services (health checks, events, registration)
  → central-hub (aggregate, monitor, coordinate)
  → PostgreSQL (service_registry, health_metrics, coordination_history)
  → NATS/Kafka (coordination signals, config updates)
  → All Services (config updates, coordination commands)
```

## Messaging
- **NATS Subscribe**: Service health updates, registration events
- **NATS Publish**: Configuration updates, coordination signals
- **Pattern**: Hub pattern (receives from all, broadcasts to all)

## Dependencies
- **Upstream**: All 17 services (health checks, registration)
- **Downstream**: All 17 services (config distribution, coordination)
- **Infrastructure**: PostgreSQL, NATS cluster, Kafka, DragonflyDB

## Critical Rules
1. **NEVER** modify infrastructure.yaml without testing (breaks all services!)
2. **ALWAYS** validate service health checks before marking as healthy
3. **VERIFY** NATS/Kafka connectivity before starting (orchestration depends on it)
4. **ENSURE** PostgreSQL connection for registry (service discovery needs this)
5. **VALIDATE** all service dependencies before startup (prevent cascade failures)

## Core Responsibilities

### 1. Service Registry
- Track all running services (17 services)
- Service discovery (where is tick-aggregator?)
- Dependency validation (can inference-service start?)

### 2. Health Monitoring
- Aggregate health checks from all services
- Infrastructure health (NATS, Kafka, ClickHouse, PostgreSQL, etc.)
- Alert on service degradation
- Trigger recovery actions

### 3. Configuration Management
- Centralized config distribution
- Environment variable management
- Dynamic config updates (no restart needed)
- Config versioning

### 4. Message Routing
- NATS cluster coordination (3 nodes)
- Kafka consumer group management
- Message flow monitoring
- Dead letter queue handling

## Infrastructure Monitored

### Databases
- PostgreSQL (suho-postgresql)
- DragonflyDB (suho-dragonflydb) - Redis-compatible
- ArangoDB (suho-arangodb) - Graph database (optional)
- ClickHouse (suho-clickhouse)

### Messaging
- NATS cluster (nats-1, nats-2, nats-3)
- Kafka (suho-kafka)
- Zookeeper (suho-zookeeper)

### Search/Vector
- Weaviate (suho-weaviate) - Vector database (optional)

## Configuration Files

### infrastructure.yaml
Defines all infrastructure components and health checks:
```yaml
databases:
  postgresql: { host, port, health_check }
  clickhouse: { host, port, health_check }
  dragonflydb: { host, port, health_check }

messaging:
  nats-1: { host, port, health_check }
  nats-2: { host, port, health_check }
  nats-3: { host, port, health_check }
  kafka: { host, port, health_check }

service_dependencies:
  tick-aggregator:
    requires: [postgresql, nats, kafka, clickhouse]
  feature-engineering:
    requires: [clickhouse, nats]
```

## Common Tasks

### Task 1: Add New Service to Registry
1. Update `infrastructure.yaml` → Add service_dependencies entry
2. Define required infrastructure (databases, messaging)
3. Set health check method (HTTP, TCP, custom)
4. Restart central-hub
5. Verify service registers successfully

### Task 2: Debug Service Not Starting
1. Check central-hub logs for dependency validation errors
2. Verify required infrastructure is healthy (check health_metrics table)
3. Check NATS/Kafka connectivity
4. Verify PostgreSQL service_registry accessible
5. Look for missing configuration

### Task 3: Monitor System Health
Query health status:
```sql
-- PostgreSQL
SELECT service_name, status, last_check
FROM health_metrics
WHERE last_check > NOW() - INTERVAL '5 minutes'
ORDER BY service_name;
```

Check infrastructure health:
```bash
# Via central-hub API
curl http://central-hub:8000/health/infrastructure

# Check all services
curl http://central-hub:8000/health/services
```

## Health Check Methods

### HTTP
- Used for: Web services, APIs
- Check: GET /health or /healthz
- Expected: 200 OK

### TCP
- Used for: Databases, messaging
- Check: Socket connection
- Expected: Connection successful

### Redis Ping
- Used for: DragonflyDB
- Check: PING command
- Expected: PONG response

### Kafka Admin
- Used for: Kafka broker
- Check: List topics command
- Expected: Topic list returned

### Custom Scripts
- Used for: Complex health checks
- Check: Run Python script
- Expected: Exit code 0

## Validation
When working on this service, ALWAYS verify:
- [ ] PostgreSQL service_registry table accessible
- [ ] All infrastructure health checks pass
- [ ] NATS cluster (3 nodes) reachable
- [ ] Kafka broker reachable
- [ ] Service dependencies validated correctly
- [ ] Health metrics updated (< 1 minute old)
- [ ] No cascade failures (one service down doesn't break others)

## Database Schema

### service_registry
```sql
CREATE TABLE service_registry (
    service_name VARCHAR PRIMARY KEY,
    instance_id VARCHAR,
    status VARCHAR, -- healthy, degraded, down
    last_heartbeat TIMESTAMP,
    dependencies JSONB,
    metadata JSONB
);
```

### health_metrics
```sql
CREATE TABLE health_metrics (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR,
    check_type VARCHAR,
    status VARCHAR,
    latency_ms INT,
    last_check TIMESTAMP,
    error_message TEXT
);
```

### coordination_history
```sql
CREATE TABLE coordination_history (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR,
    service_name VARCHAR,
    action VARCHAR,
    result VARCHAR,
    timestamp TIMESTAMP,
    metadata JSONB
);
```

## Emergency Procedures

### All Services Down
1. Check central-hub logs for errors
2. Verify PostgreSQL accessible
3. Check NATS cluster status (all 3 nodes)
4. Restart central-hub: `docker-compose restart central-hub`
5. Services should auto-recover (dependency validation)

### Infrastructure Failure
1. Check which infrastructure failed (PostgreSQL, NATS, Kafka)
2. Restart failed infrastructure
3. Wait for central-hub health checks to pass
4. Services auto-reconnect via central-hub coordination

## Reference Docs
- Planning guide: `PLANNING_SKILL_GUIDE.md` (Service 5, central-hub section)
- Architecture: `SERVICE_ARCHITECTURE_AND_FLOW.md` (lines 371-393)
- Flow + messaging: `SERVICE_FLOW_TREE_WITH_MESSAGING.md` (central-hub coordination)
- Infrastructure config: `01-core-infrastructure/central-hub/base/config/infrastructure.yaml`
