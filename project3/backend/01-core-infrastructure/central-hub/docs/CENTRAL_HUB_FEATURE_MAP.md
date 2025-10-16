# 📊 CENTRAL HUB - COMPLETE FEATURE MAP & ARCHITECTURE

**Version:** 2.0 (Post-Refactoring)
**Last Updated:** 2025-10-16 (Updated after data-bridge refactoring)
**Architecture:** God Object → 3 Focused Managers

---

## 🏗️ STRUKTUR UTAMA

```
central-hub/
├── base/          → Central Hub Service (Core Application)
├── shared/        → Shared Components (Untuk semua services)
├── sdk/           → Legacy SDK (Backward compatibility)
├── contracts/     → Service Contracts & Validation
└── docs/          → Documentation
```

**Total:** 105 Python files, 55 directories

---

## 🎯 A. CENTRALIZED FEATURES (Hanya untuk Central Hub)

**Lokasi:** `/base/`

### **1. MANAGERS (3 Focused Managers - Post Refactoring)**

**Lokasi:** `/base/managers/`

#### **a. ConnectionManager**
**File:** `connection_manager.py`

**Konsep:** Mengelola semua koneksi infrastruktur untuk Central Hub

**Fitur:**
- PostgreSQL connection via `DatabaseManager`
- DragonflyDB cache via `CacheManager`
- NATS cluster client (3 nodes)
- Kafka producer
- Redis pub/sub client
- Schema migration (multi-tenant support)

**Environment Variables:**
```bash
POSTGRES_HOST=suho-postgresql
POSTGRES_PORT=5432
POSTGRES_DB=suho_trading
POSTGRES_USER=suho_admin
POSTGRES_PASSWORD=***

DRAGONFLY_HOST=suho-dragonflydb
DRAGONFLY_PORT=6379
DRAGONFLY_PASSWORD=***

NATS_URL=nats://nats-1:4222,nats://nats-2:4222,nats://nats-3:4222
KAFKA_BROKERS=suho-kafka:9092
```

**Dipakai oleh:** Central Hub internal only

---

#### **b. MonitoringManager**
**File:** `monitoring_manager.py`

**Konsep:** Monitoring kesehatan semua infrastruktur & services

**Fitur:**
- Infrastructure health monitoring (via InfrastructureMonitor)
- Service health aggregation (via HealthAggregator)
- Alert management (via AlertManager)
- Metrics collection & reporting
- Real-time status tracking

**Components:**
- `InfrastructureMonitor` - Monitor 11 infrastructure components
- `HealthAggregator` - Aggregate service health
- `AlertManager` - Multi-channel alerting

**Dipakai oleh:** Central Hub internal only

---

#### **c. CoordinationManager**
**File:** `coordination_manager.py`

**Konsep:** Service registry, routing, dan workflow orchestration

**Fitur:**
- Service registration & discovery (via ServiceRegistry)
- Dependency management (via DependencyGraph)
- Workflow coordination (via CoordinationRouter)
- Service routing & load balancing
- Contract validation

**Components:**
- `ServiceRegistry` - Database-backed service registry
- `DependencyGraph` - Dependency tracking & topological sorting
- `CoordinationRouter` - Workflow routing logic

**Dipakai oleh:** Central Hub internal only

---

### **2. CORE COMPONENTS**

**Lokasi:** `/base/core/`

#### **a. Service Registry**
**File:** `service_registry.py`

**Konsep:** PostgreSQL-backed registry untuk semua running services

**Fitur:**
- Register/unregister services
- Service heartbeat tracking (last_seen)
- Multi-tenant isolation (tenant_id column)
- Contract validation
- Transport preferences (NATS/Kafka/HTTP)
- Service metadata & versioning

**Database Table:**
```sql
service_registry (
    id, tenant_id, service_name, host, port,
    protocol, health_endpoint, version, metadata,
    status, registered_at, last_seen,
    transport_preferences, contract_validated
)
```

---

#### **b. Health Monitor & Checkers**
**Files:**
- `health_monitor.py` - Overall health monitoring coordinator
- `health_checkers.py` - Specific health check implementations
- `health_aggregator.py` - Aggregate health dari multiple services

**Konsep:** Comprehensive health check system

**Health Checkers Available:**
- `HTTPHealthChecker` - HTTP endpoint checks (status code, response time)
- `TCPHealthChecker` - TCP socket checks
- `RedisPingChecker` - Redis/DragonflyDB PING checks
- `KafkaAdminChecker` - Kafka broker checks (list_topics)

**Health Check Result:**
```python
@dataclass
class HealthCheckResult:
    healthy: bool
    response_time_ms: float
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

---

#### **c. Infrastructure Monitor**
**File:** `infrastructure_monitor.py`

**Konsep:** Monitor semua database, messaging, search infrastructure

**Fitur:**
- Load & parse `infrastructure.yaml`
- Monitor 11 infrastructure components:
  - **Databases:** PostgreSQL, DragonflyDB, ArangoDB, ClickHouse
  - **Messaging:** NATS-1, NATS-2, NATS-3, Kafka, Zookeeper
  - **Search:** Weaviate
- Auto-alert on failures/recovery
- Health check intervals: 30 seconds
- Status tracking (HEALTHY/UNHEALTHY/UNKNOWN)
- Response time tracking

**Configuration:** `/base/config/infrastructure.yaml`

**Status Enum:**
```python
class InfrastructureStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
```

---

#### **d. Alert Manager**
**File:** `alert_manager.py`

**Konsep:** Centralized alerting system untuk infrastructure & services

**Fitur:**
- Multi-channel alerts (log, console, webhook, email - future)
- Alert rules & severity levels (critical, warning, info)
- Alert history tracking
- Rate limiting & deduplication

**Alert Channels:**
- `LogAlertChannel` - Log to file/stdout ✅
- `ConsoleAlertChannel` - Console output ✅
- `WebhookAlertChannel` - HTTP webhooks (future)
- `EmailAlertChannel` - Email notifications (future)

---

#### **e. Dependency Graph**
**File:** `dependency_graph.py`

**Konsep:** Service dependency tracking & analysis

**Fitur:**
- Build dependency graph from service metadata
- Topological sorting untuk startup order
- Impact analysis (jika service A down, service B,C affected)
- Circular dependency detection
- Dependency visualization (ASCII/JSON)

---

#### **f. Coordination Router**
**File:** `coordination_router.py`

**Konsep:** Workflow coordination & service communication routing

**Fitur:**
- Route messages between services
- Workflow orchestration
- Multi-transport support (NATS, Kafka, HTTP)
- Request/response correlation
- Timeout handling

---

### **3. API ENDPOINTS**

**Lokasi:** `/base/api/`

**Framework:** FastAPI

#### **Available Endpoints:**

| Endpoint | File | Purpose |
|----------|------|---------|
| `GET /health` | `health.py` | Central Hub health check |
| `GET /api/v1/health/services` | `health.py` | All services health |
| `GET /api/v1/infrastructure/status` | `infrastructure.py` | Infrastructure status |
| `GET /api/v1/infrastructure/{name}` | `infrastructure.py` | Specific component health |
| `GET /api/v1/metrics` | `metrics.py` | System metrics |
| `GET /api/v1/services` | `discovery.py` | List registered services |
| `POST /api/v1/services/register` | `discovery.py` | Register new service |
| `GET /api/v1/config/{key}` | `config.py` | Get configuration |
| `GET /dashboard` | `dashboard.py` | Web UI dashboard |

**Example Response:**
```json
{
  "status": "healthy",
  "services": 5,
  "infrastructure": {
    "postgresql": "healthy",
    "nats-1": "healthy",
    "kafka": "healthy"
  }
}
```

---

### **4. CONFIGURATION**

**Lokasi:** `/base/config/`

#### **infrastructure.yaml**
**Purpose:** Define all infrastructure components with health check configs

**Structure:**
```yaml
databases:
  postgresql: {...}
  dragonflydb: {...}
  clickhouse: {...}
  arangodb: {...}

messaging:
  nats-1: {...}
  nats-2: {...}
  nats-3: {...}
  kafka: {...}
  zookeeper: {...}

search:
  weaviate: {...}

service_dependencies:
  data-bridge:
    requires: [nats, kafka, clickhouse, dragonflydb]

alerts:
  enabled: true
  channels: [log, console]
```

---

## 🔄 B. SHARED COMPONENTS (Untuk Semua Services)

**Lokasi:** `/shared/`

**Cara Pakai:** Mount ke service via Docker volume `/app/central-hub/shared:ro`

---

### **1. DATA MANAGER (✅ SUDAH DIPAKAI DATA-BRIDGE)**

**Lokasi:** `/shared/components/data_manager/`

#### **a. DataRouter**
**File:** `router.py`

**Konsep:** Smart routing untuk tick & candle data ke database yang tepat

**Fitur:**
- `save_tick(tick_data: TickData)` → TimescaleDB + DragonflyDB cache
- `save_candle(candle_data: CandleData)` → TimescaleDB
- Auto-caching layer (read-through, write-through)
- Connection pool management
- Error handling & retry logic

**Usage:**
```python
from components.data_manager import DataRouter, TickData

router = DataRouter()
await router.initialize()

tick = TickData(
    symbol="EURUSD",
    timestamp=1234567890,
    bid=1.0850,
    ask=1.0852
)
await router.save_tick(tick)
```

**Dipakai oleh:** ✅ data-bridge, tick-aggregator

---

#### **b. MultiLevelCache (L1 + L2)**
**File:** `cache.py`

**Konsep:** 2-tier caching system untuk data manager (specialized, not general CacheManager)

**Architecture:**
- **L1Cache**: In-memory LRU+TTL cache (pure Python OrderedDict)
  - Ultra-fast (microseconds)
  - Limited size (default 1000 items)
  - Short TTL (default 60 seconds)
  - No external dependencies

- **L2Cache**: Redis/DragonflyDB cache
  - Fast (milliseconds)
  - Large capacity
  - Long TTL (default 3600 seconds)
  - Shared across service instances

- **MultiLevelCache**: Orchestrates L1 + L2
  - Read: L1 → L2 → miss
  - Write: Both L1 and L2 simultaneously
  - Statistics tracking (hit rates, misses)

**Implementation Details:**
```python
class L1Cache:
    """Pure Python in-memory cache using OrderedDict"""
    def __init__(self, max_size: int = 1000, ttl: int = 60):
        self._cache = OrderedDict()  # (value, expire_time)

    def get(self, key: str) -> Optional[Any]:
        # LRU: move_to_end on access
        # TTL: delete if expired

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        # Evict oldest if at capacity (LRU)

class L2Cache:
    """Redis/DragonflyDB backend"""
    def __init__(self, redis_client, namespace="data_cache"):
        self.redis_client = redis_client

    async def get(self, key: str) -> Optional[Any]:
        # JSON deserialization

    async def set(self, key: str, value: Any, ttl: int = 3600):
        # JSON serialization + Redis SETEX

class MultiLevelCache:
    """Orchestrates L1 + L2"""
    def __init__(self, redis_client, l1_max_size=1000, l1_ttl=60):
        self.l1_cache = L1Cache(max_size=l1_max_size, ttl=l1_ttl)
        self.l2_cache = L2Cache(redis_client)

    async def get(self, key):
        # Try L1 → L2 → None
        if value := self.l1_cache.get(key):
            return value  # L1 hit
        if value := await self.l2_cache.get(key):
            self.l1_cache.set(key, value)  # Populate L1
            return value  # L2 hit
        return None  # Miss
```

**Key Design Decisions:**
- Zero external dependencies (uses stdlib `OrderedDict`)
- Backward compatible signature (router.py compatibility)
- Exports 3 classes: L1Cache, L2Cache, MultiLevelCache
- Statistics tracking for observability

**Usage:**
```python
# Simple initialization
cache = MultiLevelCache(redis_client, l1_max_size=1000, l1_ttl=60)

# Advanced initialization
l1 = L1Cache(max_size=2000, ttl=120)
l2 = L2Cache(redis_client, namespace="custom")
cache = MultiLevelCache(redis_client, l1_cache=l1, l2_cache=l2)

# Operations
await cache.set("key", value, l1_ttl=60, l2_ttl=3600)
value = await cache.get("key")
await cache.delete("key")
stats = await cache.get_stats()
```

**Statistics:**
```python
stats = await cache.get_stats()
# {
#     "l1_size": 250,
#     "l1_max_size": 1000,
#     "l1_hits": 15000,
#     "l1_hit_rate_pct": 75.0,
#     "l2_hits": 4000,
#     "l2_hit_rate_pct": 20.0,
#     "total_misses": 1000,
#     "overall_hit_rate_pct": 95.0
# }
```

**Dipakai oleh:** ✅ data-bridge (DataRouter), router.py

---

#### **c. DatabasePoolManager**
**File:** `pools.py`

**Konsep:** Centralized connection pooling untuk TimescaleDB & DragonflyDB

**Fitur:**
- Auto pool creation dengan configs dari Central Hub/env
- Connection lifecycle management (open, close, health check)
- Pool statistics & monitoring
- Singleton pattern via `get_pool_manager()`
- Support asyncpg (PostgreSQL) & redis.asyncio (DragonflyDB)

**Config Format:**
```python
configs = {
    'postgresql': {
        'connection': {
            'host': 'localhost',
            'port': 5432,
            'database': 'suho_trading',
            'user': 'admin',
            'password': '***',
            'min_size': 10,
            'max_size': 50
        }
    }
}
```

**Usage:**
```python
from components.data_manager.pools import get_pool_manager

pool_manager = await get_pool_manager(configs=db_configs)
# Pools auto-created, ready to use
```

**Dipakai oleh:** ✅ data-bridge, all services needing database

---

#### **c. Models**
**File:** `models.py`

**Konsep:** Standard data models untuk market data & events

**Available Models:**
```python
@dataclass
class TickData:
    symbol: str
    timestamp: int
    timestamp_ms: int
    bid: float
    ask: float
    volume: Optional[float]
    source: str
    exchange: Optional[str]
    event_type: str

@dataclass
class CandleData:
    symbol: str
    timeframe: str
    timestamp: int
    timestamp_ms: int
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float]
    vwap: Optional[float]
    num_trades: Optional[int]
    source: str
    event_type: str

@dataclass
class EconomicEvent:
    ...

@dataclass
class HealthCheckResponse:
    ...
```

**Dipakai oleh:** ✅ data-bridge, tick-aggregator, ML services

---

#### **d. Exceptions**
**File:** `exceptions.py`

**Konsep:** Custom exceptions untuk data manager operations

**Available Exceptions:**
```python
class DataManagerError(Exception): ...
class DatabaseConnectionError(DataManagerError): ...
class QueryTimeoutError(DataManagerError): ...
class QueryExecutionError(DataManagerError): ...
class CacheError(DataManagerError): ...
class ValidationError(DataManagerError): ...
```

---

### **2. STANDARD PATTERNS**

**Lokasi:** `/shared/components/utils/patterns/`

#### **a. DatabaseManager Pattern**
**File:** `database.py`

**Konsep:** Standard pattern untuk managing multiple database connections

**Fitur:**
- Multi-database support (PostgreSQL, ClickHouse, MongoDB, ArangoDB)
- Connection pooling & lifecycle management
- Query execution with error handling
- Transaction support
- Health checks per connection
- Retry logic

**Supported Databases:**
- `PostgreSQLConnection` - asyncpg-based
- `ClickHouseConnection` - clickhouse-connect
- `MongoDBConnection` - motor
- `ArangoDBConnection` - python-arango

**Usage:**
```python
from components.utils.patterns import DatabaseManager, DatabaseConfig

db = DatabaseManager(service_name="my-service", max_connections=20)

config = DatabaseConfig(
    host="localhost",
    port=5432,
    database="mydb",
    username="user",
    password="pass"
)

await db.add_connection("postgres", "postgresql", config)
result = await db.execute("SELECT * FROM users LIMIT 10")
```

**Dipakai oleh:** Central Hub (ConnectionManager)
**Bisa dipakai:** Services needing multiple database types

---

#### **b. CacheManager Pattern**
**File:** `cache.py`

**Konsep:** Standard caching layer dengan multi-backend support

**Fitur:**
- Multi-backend (Redis, Memcached, In-Memory)
- TTL management (per-key or default)
- Cache invalidation (single key, pattern, flush all)
- Multi-level caching (L1 memory + L2 Redis)
- Cache statistics (hits, misses, hit rate)
- Namespace isolation
- Serialization (JSON, Pickle, MessagePack)

**Cache Backends:**
- `RedisCache` - Redis/DragonflyDB backend
- `MemcachedCache` - Memcached backend
- `MemoryCache` - In-memory cache (LRU)

**Usage:**
```python
from components.utils.patterns import CacheManager, CacheConfig

cache = CacheManager(service_name="my-service", default_ttl=300)

config = CacheConfig(
    backend="redis",
    host="localhost",
    port=6379,
    password="***",
    db=0,
    default_ttl=300
)

await cache.add_backend("redis", config)
await cache.set("key", {"data": "value"}, ttl=600)
value = await cache.get("key")
```

**Multi-Level Cache:**
```python
from components.data_manager.cache import MultiLevelCache, L1Cache, L2Cache

# Option 1: Simple initialization (redis_client as first param)
cache = MultiLevelCache(redis_client, l1_max_size=1000, l1_ttl=60)
await cache.set("key", value)

# Option 2: Advanced initialization with custom L1/L2
l1 = L1Cache(max_size=1000, ttl=60)
l2 = L2Cache(redis_client, namespace="my_cache")
cache = MultiLevelCache(redis_client, l1_cache=l1, l2_cache=l2)

# Usage - checks L1 first, then L2, then returns None
value = await cache.get("key")  # L1 → L2 → miss
await cache.set("key", value, l1_ttl=60, l2_ttl=3600)  # Write to both
await cache.delete("key")  # Delete from both
stats = await cache.get_stats()  # Get hit rates
```

**Dipakai oleh:** ✅ data-bridge (DataRouter), Central Hub (ConnectionManager)
**Bisa dipakai:** All services needing caching

---

#### **c. CircuitBreaker Pattern**
**File:** `circuit_breaker.py`

**Konsep:** Circuit breaker untuk protecting against external service failures

**Fitur:**
- Auto-open circuit on failure threshold
- Auto-close after recovery timeout
- Half-open state for testing recovery
- Failure/success tracking
- Per-service circuit breakers
- Configurable thresholds

**States:**
- `CLOSED` - Normal operation
- `OPEN` - Circuit open, requests fail fast
- `HALF_OPEN` - Testing if service recovered

**Usage:**
```python
from components.utils.patterns import CircuitBreakerManager

cb = CircuitBreakerManager(service_name="my-service")
cb.add_circuit("external-api", failure_threshold=5, recovery_timeout=60)

if not cb.is_open("external-api"):
    try:
        result = await call_external_api()
        await cb.record_success("external-api")
    except Exception as e:
        await cb.record_failure("external-api")
        # Circuit will open after 5 failures
```

**Bisa dipakai:** Services calling external APIs (Polygon, economic data providers)

---

#### **d. ConfigManager Pattern**
**File:** `config.py`

**Konsep:** Dynamic configuration management dengan multiple sources

**Fitur:**
- Load from files (YAML, JSON, TOML)
- Load from environment variables
- Load from remote config service
- Hot reload (watch file changes)
- Config validation (schema validation)
- Environment-specific configs (dev, staging, prod)
- Config caching

**Usage:**
```python
from components.utils.patterns import ConfigManager

config = ConfigManager(
    service_name="my-service",
    environment="production"
)

await config.load_config()
database_url = await config.get("database.url")
timeout = await config.get("api.timeout", default=30)
```

**Bisa dipakai:** Services needing dynamic configuration

---

#### **e. Health Check Pattern**
**File:** `health.py`

**Konsep:** Standard health check interface & implementations

**Fitur:**
- Multiple check types (HTTP, TCP, Database, Custom)
- Dependency health aggregation
- Health status enum (HEALTHY, UNHEALTHY, DEGRADED)
- Response time tracking
- Health history

**Usage:**
```python
from components.utils.patterns import HealthChecker, HealthStatus

class MyServiceHealthChecker(HealthChecker):
    async def check(self) -> HealthStatus:
        # Check database
        db_ok = await self.check_database()
        # Check cache
        cache_ok = await self.check_cache()

        if db_ok and cache_ok:
            return HealthStatus.HEALTHY
        elif db_ok or cache_ok:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.UNHEALTHY
```

**Bisa dipakai:** All services

---

#### **f. Response Pattern**
**File:** `response.py`

**Konsep:** Standardized API response format

**Fitur:**
- Success/error indication
- Data payload
- Error messages & codes
- Processing time tracking
- Correlation ID tracking
- Metadata support

**StandardResponse:**
```python
@dataclass
class StandardResponse:
    success: bool
    data: Optional[Any] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    processing_time_ms: Optional[float] = None
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

**Usage:**
```python
from components.utils.patterns import StandardResponse

# Success response
return StandardResponse(
    success=True,
    data={"users": [...]},
    processing_time_ms=45.2,
    correlation_id="abc-123"
)

# Error response
return StandardResponse(
    success=False,
    error_message="Database connection failed",
    error_code="DB_CONNECTION_ERROR",
    processing_time_ms=12.5
)
```

**Bisa dipakai:** All services with API endpoints

---

#### **g. Tracing Pattern**
**File:** `tracing.py`

**Konsep:** Distributed tracing & request tracking

**Fitur:**
- Correlation ID generation & propagation
- Request span tracking
- Performance timing (start, end, duration)
- Error tracking per span
- Trace context propagation (headers, messages)
- Parent-child span relationships

**Usage:**
```python
from components.utils.patterns import RequestTracer

tracer = RequestTracer(service_name="my-service")

correlation_id = "req-12345"
with tracer.trace("process_order", correlation_id):
    # Do work
    await process_payment()

    # Add metadata
    tracer.add_metadata(correlation_id, {"order_id": "ORD-123"})

    # Record errors
    try:
        await send_email()
    except Exception as e:
        tracer.add_error(correlation_id, str(e))
```

**Bisa dipakai:** Services needing observability & debugging

---

#### **h. Repository Pattern**
**File:** `repository.py`

**Konsep:** Data access abstraction layer (DDD pattern)

**Fitur:**
- CRUD operations abstraction
- Query builder
- Transaction support
- Entity mapping
- Lazy loading

**Bisa dipakai:** Services with complex data access logic

---

#### **i. Hot Reload Pattern**
**File:** `hot_reload.py`

**Konsep:** Dynamic code reloading without service restart

**Fitur:**
- Watch file changes
- Reload modules dynamically
- Zero-downtime updates
- Rollback on errors

**Bisa dipakai:** Services needing continuous deployment

---

### **3. BASE SERVICE CLASS**

**Lokasi:** `/shared/components/utils/base_service.py`

**Konsep:** Base class untuk standardisasi semua services dengan built-in patterns

**Built-in Components:**
- `DatabaseManager` - Database access
- `CacheManager` - Caching layer
- `ConfigManager` - Configuration management
- `RequestTracer` - Distributed tracing
- `CircuitBreakerManager` - External service protection
- `StandardResponse` - Response formatting
- Structured logging (newline format)
- Health checks
- Process tracing

**Abstract Methods:**
```python
async def custom_health_checks(self) -> Dict[str, Any]
async def on_startup(self)
async def on_shutdown(self)
```

**Usage Example:**
```python
from components.utils.base_service import BaseService, ServiceConfig

config = ServiceConfig(
    service_name="my-service",
    version="1.0.0",
    port=8000,
    environment="production",
    enable_tracing=True,
    enable_circuit_breaker=True,
    health_check_interval=30,
    cache_ttl_default=300,
    max_connections=100
)

class MyService(BaseService):
    def __init__(self):
        super().__init__(config)

    async def custom_health_checks(self) -> Dict[str, Any]:
        # Service-specific health checks
        return {
            "queue_size": await self.get_queue_size(),
            "worker_count": self.active_workers
        }

    async def on_startup(self):
        # Custom startup logic
        await self.connect_to_external_api()

    async def on_shutdown(self):
        # Custom shutdown logic
        await self.flush_buffers()

# Use service
service = MyService()
await service.start()

# Built-in methods available:
await service.db_execute("SELECT * FROM users")
await service.cache_set("key", value, ttl=600)
config_value = await service.get_config("api.timeout")
```

**Benefits:**
- Consistent structure across all services
- Built-in observability (logging, tracing, health checks)
- Built-in resilience (circuit breaker, retry logic)
- Reduced boilerplate code
- Easy testing

**Bisa dipakai:** Recommended for all new services

---

### **4. UTILITY COMPONENTS**

**Lokasi:** `/shared/components/utils/`

#### **a. Data Validator**
**File:** `data_validator.py`

**Konsep:** Validate incoming market data (ticks, candles, economic events)

**Validations:**
- Field presence (required fields)
- Data types (int, float, str)
- Value ranges (price > 0, volume >= 0)
- Timestamp validity
- Symbol format

**Usage:**
```python
from components.utils.data_validator import DataValidator

validator = DataValidator()

tick_data = {...}
if validator.validate_tick(tick_data):
    await process_tick(tick_data)
else:
    logger.error(f"Invalid tick: {validator.errors}")
```

---

#### **b. Timezone Handler**
**File:** `timezone_handler.py`

**Konsep:** Timezone conversion & handling untuk market data

**Fitur:**
- Convert between timezones (UTC, NY, London, Tokyo)
- Market session detection (Asian, European, US)
- DST handling
- Timestamp formatting

---

#### **c. Gap Fill Verifier**
**File:** `gap_fill_verifier.py`

**Konsep:** Detect & report data gaps untuk quality assurance

**Fitur:**
- Detect missing ticks/candles
- Calculate gap duration
- Generate gap reports
- Alert on critical gaps

---

#### **d. Contract Bridge**
**File:** `contract_bridge.py`

**Konsep:** Service contract validation (schema validation)

**Fitur:**
- Validate request/response schemas
- API contract enforcement
- Version compatibility checks

---

#### **e. Error DNA Analyzer**
**Lokasi:** `/shared/components/utils/log_utils/error_dna/`

**Konsep:** Advanced error analysis & categorization

**Fitur:**
- Error pattern detection (connection errors, timeout errors, validation errors)
- Root cause analysis
- Error fingerprinting (unique error signature)
- Error clustering (group similar errors)
- Automatic categorization

**Usage:**
```python
from components.utils.log_utils.error_dna import ErrorDNA

analyzer = ErrorDNA()

try:
    await risky_operation()
except Exception as e:
    dna = analyzer.analyze(e)
    # dna.category: "CONNECTION_ERROR"
    # dna.fingerprint: "postgres_connection_refused_5432"
    # dna.suggested_fix: "Check PostgreSQL is running"
```

---

### **5. EXCEPTIONS**

**Lokasi:** `/shared/components/utils/exceptions/`

**Standard exceptions untuk semua services:**

| File | Purpose |
|------|---------|
| `base.py` | Base exception classes |
| `service_registry.py` | Service registry errors (ServiceNotFound, RegistrationFailed) |
| `discovery.py` | Service discovery errors (DiscoveryTimeout, NoHealthyInstances) |
| `configuration.py` | Config errors (ConfigNotFound, ConfigValidationError) |
| `coordination.py` | Coordination errors (WorkflowFailed, CircularDependency) |
| `infrastructure.py` | Infrastructure errors (InfrastructureUnavailable, HealthCheckFailed) |

**Exception Hierarchy:**
```python
BaseServiceError
├── ServiceRegistryError
│   ├── ServiceNotFound
│   ├── ServiceAlreadyRegistered
│   └── RegistrationFailed
├── DiscoveryError
│   ├── DiscoveryTimeout
│   ├── NoHealthyInstances
│   └── ServiceUnavailable
├── ConfigurationError
│   ├── ConfigNotFound
│   ├── ConfigValidationError
│   └── ConfigLoadError
├── CoordinationError
│   ├── WorkflowFailed
│   ├── CircularDependency
│   └── DependencyUnavailable
└── InfrastructureError
    ├── InfrastructureUnavailable
    ├── HealthCheckFailed
    └── ConnectionFailed
```

---

### **6. MODELS**

**Lokasi:** `/shared/models/`

#### **infrastructure_model.py**

**Data models untuk infrastructure monitoring:**

```python
class InfrastructureType(str, Enum):
    POSTGRES = "postgres"
    REDIS = "redis"
    NATS = "nats"
    KAFKA = "kafka"
    CLICKHOUSE = "clickhouse"
    ARANGO = "arango"
    WEAVIATE = "weaviate"
    ZOOKEEPER = "zookeeper"

class InfrastructureStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

class HealthCheckMethod(str, Enum):
    HTTP = "http"
    TCP = "tcp"
    REDIS_PING = "redis_ping"
    KAFKA_ADMIN = "kafka_admin"

@dataclass
class HealthCheckConfig:
    method: HealthCheckMethod
    endpoint: Optional[str]
    port: Optional[int]
    command: Optional[str]
    timeout: int
    interval: int

@dataclass
class InfrastructureConfig:
    name: str
    host: str
    port: int
    type: InfrastructureType
    health_check: HealthCheckConfig
    dependencies: List[str]
    critical: bool
    description: str
    management_port: Optional[int]

@dataclass
class InfrastructureHealth:
    name: str
    type: str
    status: InfrastructureStatus
    response_time_ms: Optional[float]
    error: Optional[str]
    last_check: int
    critical: bool
    dependents: List[str]
```

---

### **7. CONNECTION RETRY UTILITY**

**Lokasi:** `/shared/utils/connection_retry.py`

**Konsep:** Retry logic untuk resilient connection initialization

**Fitur:**
- Exponential backoff (1s → 2s → 4s → 8s → ...)
- Max retries configurable
- Custom error messages
- Async support

**Usage:**
```python
from utils.connection_retry import connect_with_retry

# Retry database connection
pool = await connect_with_retry(
    lambda: create_database_pool(),
    "PostgreSQL Database",
    max_retries=10
)

# Retry external API
api_client = await connect_with_retry(
    lambda: initialize_api_client(),
    "External API",
    max_retries=5
)
```

**Retry Strategy:**
- Attempt 1: immediate
- Attempt 2: wait 1s
- Attempt 3: wait 2s
- Attempt 4: wait 4s
- Attempt 5: wait 8s
- ...
- Max wait: 32s between attempts

**Dipakai oleh:** ✅ data-bridge, all services needing resilient connections

---

## 🔌 C. SDK - LEGACY vs ADVANCED

**Lokasi:** `/sdk/python/central_hub_sdk/`

**Important:** SDK memiliki 2 bagian - Legacy (deprecated) dan Advanced (masih berguna)

---

### **❌ PART 1: LEGACY SDK (v1.x) - DEPRECATED**

**Status:** DEPRECATED untuk semua services (Central Hub tidak pakai)

#### **1. CentralHubClient** ❌
**File:** `client.py`
**Status:** DEPRECATED

**Konsep:** Client untuk fetch config dari Central Hub API

**Masalah:**
- Network dependency on Central Hub API
- Slower than environment variables
- Extra complexity & failure points
- Not used by refactored Central Hub

**Migration:** Use environment variables directly (see Migration Guide section H)

---

#### **2. HeartbeatLogger** ❌
**File:** `heartbeat_logger.py`
**Status:** DEPRECATED

**Konsep:** Periodic heartbeat logging with metrics

**Migration:** Use standard Python logging + BaseService health checks

---

#### **3. ProgressLogger** ❌
**File:** `progress_logger.py`
**Status:** DEPRECATED

**Konsep:** Progress tracking logger

**Migration:** Use standard Python logging with progress indicators

---

### **✅ PART 2: ADVANCED SDK (v2.0) - MASIH BERGUNA**

**Status:** Production-ready, dapat dipakai untuk advanced use cases

---

#### **1. SDK Database (v2.0)** ✅

**Lokasi:** `/sdk/python/central_hub_sdk/database/`

**Konsep:** Multi-database router dengan auto schema migration

**Components:**
```python
from central_hub_sdk.database import (
    DatabaseRouter,          # Smart router untuk 6 databases
    DatabaseHealthChecker,   # Health check semua databases
    SchemaMigrator          # Auto-create schemas dari Python
)
```

**Supported Databases:**
- TimescaleDB (`timescale.py`) - PostgreSQL + time-series
- ClickHouse (`clickhouse.py`) - OLAP analytics
- DragonflyDB (`dragonfly.py`) - Redis-compatible cache
- ArangoDB (`arango.py`) - Graph + document database
- Weaviate (`weaviate.py`) - Vector search
- MongoDB (via base) - Document database

**Kelebihan vs Shared DataManager:**
| Feature | SDK Database v2.0 | Shared Data Manager |
|---------|------------------|-------------------|
| Databases | 6 types ✅ | 2 types (PostgreSQL, Dragonfly) |
| Auto Schema Migration | ✅ Yes | ❌ Manual |
| Health Checks | ✅ Built-in | ⚠️ Separate |
| Router | ✅ Advanced | ✅ Basic |
| Use Case | Multi-database apps | Simple tick/candle storage |

**Usage Example:**
```python
from central_hub_sdk.database import DatabaseRouter, SchemaMigrator

# Config untuk 6 databases
config = {
    'timescaledb': {
        'host': 'localhost',
        'port': 5432,
        'database': 'trading',
        'user': 'admin',
        'password': '***'
    },
    'clickhouse': {...},
    'dragonflydb': {...},
    'arangodb': {...},
    'weaviate': {...}
}

# Initialize router
router = DatabaseRouter(config)
await router.initialize()

# Auto-create schemas
migrator = SchemaMigrator(router, schema_base_path="/path/to/schemas")
await migrator.initialize_all_schemas()

# Health check all databases
health_checker = DatabaseHealthChecker(router)
report = await health_checker.check_all()
```

**Kapan Pakai:**
- ✅ Service butuh multiple database types (bukan hanya PostgreSQL)
- ✅ Service butuh auto schema migration
- ✅ Service butuh centralized database health checks
- ❌ Service hanya butuh TimescaleDB + DragonflyDB → pakai Shared DataManager

---

#### **2. SDK Messaging (v2.0)** ✅

**Lokasi:** `/sdk/python/central_hub_sdk/messaging/`

**Konsep:** Unified messaging interface untuk NATS, Kafka, dan HTTP

**⚠️ TIDAK ADA DI SHARED COMPONENTS!**

**Components:**
```python
from central_hub_sdk.messaging import (
    # Clients
    NATSMessagingClient,     # NATS wrapper
    KafkaMessagingClient,    # Kafka wrapper
    HTTPMessagingClient,     # HTTP wrapper

    # Router
    MessagingRouter,         # Use-case based routing
    UseCase,                 # Use case enum

    # Patterns
    PubSubPattern,           # Publish/Subscribe
    RequestReplyPattern,     # Request/Response (RPC)
    StreamPattern,           # Stream processing
    FanOutPattern,           # Broadcast to multiple
    WorkQueuePattern,        # Task distribution

    # Base
    MessagingClient,
    Message,
    MessageType
)
```

**5 Messaging Patterns:**

1. **PubSubPattern** - Publish/Subscribe
   ```python
   pub_sub = PubSubPattern(nats_client)
   await pub_sub.publish("topic", {"data": "value"})
   await pub_sub.subscribe("topic", handler_func)
   ```

2. **RequestReplyPattern** - Request/Response (RPC)
   ```python
   req_reply = RequestReplyPattern(nats_client)
   response = await req_reply.request("service.method", {"param": "value"})
   ```

3. **StreamPattern** - Stream processing
   ```python
   stream = StreamPattern(kafka_client)
   await stream.produce("stream_name", events)
   await stream.consume("stream_name", consumer_group)
   ```

4. **FanOutPattern** - Broadcast to multiple consumers
   ```python
   fanout = FanOutPattern(nats_client)
   await fanout.broadcast("event_name", data, ["consumer1", "consumer2"])
   ```

5. **WorkQueuePattern** - Task distribution
   ```python
   work_queue = WorkQueuePattern(nats_client)
   await work_queue.add_task("queue_name", task_data)
   worker_task = await work_queue.get_task("queue_name")
   ```

**Unified Interface:**
```python
# Auto-route based on use case
router = MessagingRouter()
router.register_client(UseCase.REAL_TIME_EVENTS, nats_client)
router.register_client(UseCase.BATCH_PROCESSING, kafka_client)
router.register_client(UseCase.RPC_CALLS, http_client)

# Send message - auto-routed
await router.send(UseCase.REAL_TIME_EVENTS, "topic", data)
```

**Kapan Pakai:**
- ✅ Service butuh advanced messaging patterns (RPC, FanOut, WorkQueue)
- ✅ Service butuh unified interface untuk NATS/Kafka/HTTP
- ✅ Service butuh multi-transport routing
- ❌ Service hanya butuh simple NATS pub/sub → pakai nats.py langsung

---

#### **3. SDK Schemas (v2.0)** ✅

**Lokasi:** `/sdk/python/central_hub_sdk/schemas/`

**Konsep:** Python-based schema definitions, auto-generate SQL!

**⚠️ TIDAK ADA DI SHARED COMPONENTS!**

**Files:**
```python
timescale_schema.py    # PostgreSQL/TimescaleDB schemas
clickhouse_schema.py   # ClickHouse OLAP schemas
dragonfly_schema.py    # DragonflyDB cache patterns
arangodb_schema.py     # ArangoDB graph schemas
weaviate_schema.py     # Weaviate vector schemas
```

**Kelebihan:**
- ✅ Single source of truth (1 Python file = all table schemas)
- ✅ Type safe (Python type hints + IDE autocomplete)
- ✅ Auto-generate SQL dari Python dicts
- ✅ Version control friendly (easy git diff)
- ✅ Reusable constants & functions
- ✅ Dynamic schema definition (loops, conditionals)

**Example - TimescaleDB Schema:**
```python
# Define schema in Python
MARKET_TICKS_SCHEMA = {
    "name": "market_ticks",
    "description": "Real-time market tick data",
    "version": "1.0",

    # TimescaleDB specific
    "hypertable": {
        "time_column": "timestamp",
        "chunk_interval": "1 day"
    },

    # Columns
    "columns": {
        "timestamp": "TIMESTAMPTZ NOT NULL",
        "symbol": "VARCHAR(20) NOT NULL",
        "bid": "DECIMAL(18, 5)",
        "ask": "DECIMAL(18, 5)",
        "volume": "BIGINT DEFAULT 0"
    },

    # Primary key
    "primary_key": ["timestamp", "symbol"],

    # Indexes
    "indexes": [
        {
            "name": "idx_symbol_time",
            "columns": ["symbol", "timestamp DESC"],
            "method": "BTREE"
        }
    ]
}

# Auto-generate SQL
from central_hub_sdk.schemas.timescale_schema import generate_full_schema_sql

sql = generate_full_schema_sql(MARKET_TICKS_SCHEMA)
print(sql)

# Output:
# CREATE TABLE IF NOT EXISTS market_ticks (
#     timestamp TIMESTAMPTZ NOT NULL,
#     symbol VARCHAR(20) NOT NULL,
#     bid DECIMAL(18, 5),
#     ask DECIMAL(18, 5),
#     volume BIGINT DEFAULT 0,
#     PRIMARY KEY (timestamp, symbol)
# );
# SELECT create_hypertable('market_ticks', 'timestamp', chunk_time_interval => INTERVAL '1 day');
# CREATE INDEX IF NOT EXISTS idx_symbol_time ON market_ticks (symbol, timestamp DESC) USING BTREE;
```

**Workflow:**
```python
# 1. Import schemas
from central_hub_sdk.schemas import (
    get_timescale_schemas,
    get_clickhouse_schemas,
    get_dragonfly_schemas
)

# 2. Get all schemas
all_timescale_schemas = get_timescale_schemas()
# Returns: [MARKET_TICKS_SCHEMA, MARKET_CANDLES_SCHEMA, ...]

# 3. Auto-migrate with SchemaMigrator
from central_hub_sdk import DatabaseRouter, SchemaMigrator

router = DatabaseRouter(config)
await router.initialize()

migrator = SchemaMigrator(router, use_python_schemas=True)
await migrator.initialize_all_schemas()
# All schemas auto-created!
```

**Kapan Pakai:**
- ✅ Service butuh complex database schemas
- ✅ Service butuh schema versioning
- ✅ Service butuh auto schema migration
- ✅ Team wants type-safe schema definitions
- ✅ Project needs centralized schema management

**Kapan TIDAK Pakai:**
- ❌ Service hanya butuh simple tables → tulis SQL manual
- ❌ Schema jarang berubah → static SQL files cukup

---

### **SDK v2.0 Summary:**

| SDK Component | Status | Use Case |
|--------------|--------|----------|
| **CentralHubClient** | ❌ DEPRECATED | Config fetching (use env vars) |
| **HeartbeatLogger** | ❌ DEPRECATED | Logging (use standard logging) |
| **ProgressLogger** | ❌ DEPRECATED | Progress tracking (use logging) |
| **Database v2.0** | ✅ PRODUCTION | Multi-database + auto migration |
| **Messaging v2.0** | ✅ PRODUCTION | Advanced messaging patterns |
| **Schemas v2.0** | ✅ PRODUCTION | Python-based schemas |

---

### **Decision Tree: Shared vs SDK?**

```
Need database access?
├─ Only PostgreSQL + DragonflyDB for ticks/candles?
│  └─ ✅ Use Shared DataManager (simpler)
├─ Multiple database types (ClickHouse, Arango, Weaviate)?
│  └─ ✅ Use SDK Database v2.0
└─ Need auto schema migration?
   └─ ✅ Use SDK Database v2.0 + Schemas v2.0

Need messaging?
├─ Simple NATS pub/sub?
│  └─ ✅ Use nats.py directly
├─ Advanced patterns (RPC, FanOut, WorkQueue)?
│  └─ ✅ Use SDK Messaging v2.0
└─ Multi-transport routing (NATS/Kafka/HTTP)?
   └─ ✅ Use SDK Messaging v2.0

Need schema management?
├─ Simple tables, static schemas?
│  └─ ✅ Write SQL manually
└─ Complex schemas, versioning, migrations?
   └─ ✅ Use SDK Schemas v2.0
```

---

## 📋 D. RECOMMENDATIONS UNTUK SERVICES LAIN

### **✅ YANG HARUS DIPAKAI:**

#### **1. Data Manager Components** (jika butuh database)
```python
# Import from shared components
from components.data_manager import DataRouter, TickData, CandleData
from components.data_manager.pools import get_pool_manager
from components.data_manager.cache import MultiLevelCache, L1Cache, L2Cache

# Example usage
router = DataRouter()
await router.initialize()

# Save tick data
tick = TickData(symbol="EURUSD", timestamp=1234567890, bid=1.0850, ask=1.0852)
await router.save_tick(tick)

# Cache usage (already integrated in DataRouter)
cache = MultiLevelCache(redis_client, l1_max_size=1000, l1_ttl=60)
await cache.set("key", value)
```

**Use Cases:**
- Saving market ticks → TimescaleDB
- Saving candles → TimescaleDB
- Caching frequently accessed data (L1 in-memory + L2 Redis)
- Database connection pooling
- ✅ **data-bridge refactored**: No longer uses CentralHubClient SDK

---

#### **2. Standard Patterns** (sesuai kebutuhan)
```python
from components.utils.patterns import (
    DatabaseManager,      # Multi-database connections
    CacheManager,         # Multi-backend caching
    CircuitBreaker,       # External API resilience
    ConfigManager,        # Dynamic configuration
    StandardResponse,     # API response format
    RequestTracer,        # Distributed tracing
    HealthChecker         # Health checks
)
```

**Use Cases:**
- Multi-database access → `DatabaseManager`
- Caching layer → `CacheManager`
- External API calls → `CircuitBreaker`
- Dynamic config → `ConfigManager`
- API responses → `StandardResponse`
- Request tracking → `RequestTracer`

---

#### **3. Base Service** (untuk new services)
```python
from components.utils.base_service import BaseService, ServiceConfig

class MyService(BaseService):
    async def custom_health_checks(self):
        return {"status": "ok"}

    async def on_startup(self):
        # Initialize
        pass

    async def on_shutdown(self):
        # Cleanup
        pass
```

**Benefits:**
- All patterns built-in
- Consistent structure
- Reduced boilerplate
- Better observability

---

#### **4. Connection Retry Utility**
```python
from utils.connection_retry import connect_with_retry

pool = await connect_with_retry(
    lambda: create_pool(),
    "Database Pool",
    max_retries=10
)
```

---

#### **5. Standard Exceptions**
```python
from components.utils.exceptions import (
    DatabaseConnectionError,
    QueryTimeoutError,
    ValidationError,
    ServiceNotFound,
    ConfigNotFound
)
```

---

#### **6. Utility Components**
```python
from components.utils import (
    DataValidator,
    TimezoneHandler,
    GapFillVerifier
)
```

---

### **❌ YANG JANGAN DIPAKAI:**

1. ❌ `CentralHubClient` SDK - Use environment variables
2. ❌ `HeartbeatLogger` SDK - Use standard logging
3. ❌ `ProgressLogger` SDK - Use standard logging
4. ❌ Hardcoded credentials - Use environment variables
5. ❌ Manual connection pooling - Use `DatabasePoolManager`

---

### **🎯 CONFIG PATTERN (Post-Refactoring):**

**❌ OLD WAY (SDK):**
```python
from central_hub_sdk import CentralHubClient

client = CentralHubClient(...)
await client.register()

# Fetch config via API
nats_config = await client.get_messaging_config('nats')
db_config = await client.get_database_config('postgresql')
```

**✅ NEW WAY (Environment Variables):**
```python
import os

# Direct environment variables
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
POSTGRES_DB = os.getenv("POSTGRES_DB", "suho_trading")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

NATS_URL = os.getenv("NATS_URL", "nats://nats-1:4222")
KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "kafka:9092")

DRAGONFLY_HOST = os.getenv("DRAGONFLY_HOST", "dragonflydb")
DRAGONFLY_PORT = int(os.getenv("DRAGONFLY_PORT", 6379))
DRAGONFLY_PASSWORD = os.getenv("DRAGONFLY_PASSWORD")

CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "clickhouse")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", 8123))
```

**Benefits:**
- No network dependency
- Faster startup
- Simpler code
- Better testability
- Standard 12-factor app pattern

---

## 📦 E. DOCKER VOLUME MOUNT PATTERN

**Cara mengakses shared components:**

### **docker-compose.yml**
```yaml
services:
  my-service:
    image: my-service:latest
    volumes:
      # Mount shared components (read-only)
      - ./central-hub/shared:/app/central-hub/shared:ro
    environment:
      # Database configs
      - POSTGRES_HOST=suho-postgresql
      - POSTGRES_PORT=5432
      - POSTGRES_DB=suho_trading
      - POSTGRES_USER=suho_admin
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

      # Cache configs
      - DRAGONFLY_HOST=suho-dragonflydb
      - DRAGONFLY_PORT=6379
      - DRAGONFLY_PASSWORD=${DRAGONFLY_PASSWORD}

      # Messaging configs
      - NATS_URL=nats://nats-1:4222,nats://nats-2:4222,nats://nats-3:4222
      - KAFKA_BROKERS=suho-kafka:9092

      # ClickHouse configs
      - CLICKHOUSE_HOST=suho-clickhouse
      - CLICKHOUSE_PORT=8123
      - CLICKHOUSE_USER=suho_analytics
      - CLICKHOUSE_PASSWORD=${CLICKHOUSE_PASSWORD}
      - CLICKHOUSE_DATABASE=suho_analytics
```

### **Python Import Path**
```python
import sys
sys.path.insert(0, '/app/central-hub/shared')

# Now can import shared components
from components.data_manager import DataRouter
from components.utils.patterns import CacheManager
```

---

## 🎯 F. SUMMARY

### **Central Hub Menyediakan:**

#### **1. Centralized Services** (hanya di Central Hub):
- ✅ Service registry & discovery (PostgreSQL-backed)
- ✅ Infrastructure monitoring (11 components, 30s intervals)
- ✅ Health aggregation & alerting (multi-channel)
- ✅ Workflow coordination & routing
- ✅ REST API untuk monitoring & management
- ✅ Web dashboard

#### **2. Shared Components** (bisa dipakai semua services):
- ✅ **DataRouter & DatabasePoolManager** (✅ sudah dipakai data-bridge)
- ✅ **Standard Patterns:**
  - DatabaseManager (multi-database)
  - CacheManager (multi-backend)
  - CircuitBreaker (resilience)
  - ConfigManager (dynamic config)
  - RequestTracer (observability)
  - HealthChecker (health checks)
- ✅ **BaseService class** (recommended untuk new services)
- ✅ **Exceptions & Models** (standardized errors & data structures)
- ✅ **Utilities:**
  - Connection retry
  - Data validator
  - Timezone handler
  - Gap fill verifier
  - Error DNA analyzer

#### **3. Configuration Method:**
- ✅ **Environment variables** (Central Hub pattern baru, recommended)
- ❌ **SDK API calls** (legacy, deprecated)

---

### **Architecture Statistics:**

- **Total Files:** 105 Python files
- **Total Directories:** 55 directories
- **Infrastructure Monitored:** 11 components (3 NATS, 4 databases, 2 messaging, 1 search, 1 coordination)
- **Health Check Methods:** 4 types (HTTP, TCP, Redis PING, Kafka Admin)
- **Standard Patterns:** 9 patterns (Database, Cache, CircuitBreaker, Config, Health, Response, Tracing, Repository, HotReload)
- **Managers:** 3 focused managers (Connection, Monitoring, Coordination)

---

## 📚 G. ADDITIONAL RESOURCES

### **Documentation:**
- `/docs/CENTRAL_HUB_FEATURE_MAP.md` - This document
- `/docs/README.md` - Central Hub overview
- `/shared/components/data_manager/README.md` - Data Manager guide
- `/shared/components/utils/patterns/README.md` - Pattern library guide (if exists)

### **Configuration Files:**
- `/base/config/infrastructure.yaml` - Infrastructure monitoring config

### **Testing:**
- `/tests/unit/` - Unit tests
- `/tests/integration/` - Integration tests
- `/tests/fixtures/` - Test fixtures

---

## 🔄 H. MIGRATION GUIDE (SDK → Environment Variables)

### **Step 1: Remove SDK Dependencies**
```python
# Remove these imports
# from central_hub_sdk import CentralHubClient  ❌
# from central_hub_sdk import HeartbeatLogger   ❌
```

### **Step 2: Add Environment Variable Config**
```python
import os

# Add environment variable loading
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
# ... add all configs
```

### **Step 3: Remove SDK Initialization**
```python
# Remove SDK client initialization
# self.central_hub = CentralHubClient(...)  ❌
# await self.central_hub.register()         ❌
```

### **Step 4: Update Docker Compose**
```yaml
# Add environment variables to service
environment:
  - POSTGRES_HOST=suho-postgresql
  - NATS_URL=nats://nats-1:4222,nats://nats-2:4222,nats://nats-3:4222
  # ... add all configs
```

### **Step 5: Remove SDK Config Fetching**
```python
# Remove API config fetching
# nats_config = await self.central_hub.get_messaging_config('nats')  ❌

# Use environment variables directly
nats_urls = os.getenv("NATS_URL").split(',')  ✅
```

### **Step 6: Update Health Checks**
```python
# Remove hardcoded credentials
# conn = await asyncpg.connect(
#     host='suho-postgresql',      ❌ Hardcoded
#     password='hardcoded_pass'    ❌ Hardcoded
# )

# Use environment variables
conn = await asyncpg.connect(
    host=os.getenv("POSTGRES_HOST"),         ✅
    password=os.getenv("POSTGRES_PASSWORD")  ✅
)
```

---

## 📖 I. REAL-WORLD EXAMPLE: DATA-BRIDGE REFACTORING

**Date Completed:** 2025-10-16

### **Before Refactoring:**

**Issues:**
- ❌ Used `CentralHubClient` SDK for config fetching
- ❌ Used `HeartbeatLogger` SDK for logging
- ❌ Hardcoded credentials in healthcheck.py
- ❌ Depended on Central Hub API availability
- ❌ Missing `cache.py` (was deleted during previous refactoring)

### **Refactoring Steps:**

#### **1. Refactored config.py**
```python
# REMOVED:
from central_hub_sdk import CentralHubClient

# ADDED:
import os

def _load_env_configs(self):
    """Load database and messaging configs from environment variables"""
    self._postgresql_config = {
        'connection': {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', 5432)),
            # ... all from env vars
        }
    }
```

#### **2. Refactored main.py**
```python
# REMOVED:
from central_hub_sdk import HeartbeatLogger

# REPLACED WITH:
# Standard logging every 30 seconds
if int((datetime.utcnow() - self.start_time).total_seconds()) % 30 == 0:
    logger.info(f"📊 Heartbeat | Ticks: {metrics['ticks']:,} ...")
```

#### **3. Refactored healthcheck.py**
```python
# REMOVED:
async def check_central_hub(): ...  # No longer needed

# ADDED:
async def check_dragonflydb():  # Was missing
    import redis.asyncio as redis
    client = redis.Redis(
        host=os.getenv('DRAGONFLY_HOST', 'localhost'),
        port=int(os.getenv('DRAGONFLY_PORT', 6379)),
        password=os.getenv('DRAGONFLY_PASSWORD', None),
        # ... from env vars
    )
```

#### **4. Created cache.py**
**Following Central Hub architecture pattern:**

```python
# /shared/components/data_manager/cache.py
from collections import OrderedDict
import redis.asyncio as aioredis

class L1Cache:
    """L1 in-memory cache with TTL and LRU eviction"""
    def __init__(self, max_size: int = 1000, ttl: int = 60):
        self.max_size = max_size
        self.ttl = ttl
        self._cache = OrderedDict()  # Pure Python, no dependencies

class L2Cache:
    """L2 Redis/DragonflyDB cache"""
    def __init__(self, redis_client: aioredis.Redis, namespace: str = "data_cache"):
        self.redis_client = redis_client
        self.namespace = namespace

class MultiLevelCache:
    """2-tier caching system (L1 in-memory + L2 Redis)"""
    def __init__(
        self,
        redis_client: aioredis.Redis,
        l1_max_size: int = 1000,
        l1_ttl: int = 60,
        namespace: str = "data_cache",
        l1_cache: Optional[L1Cache] = None,
        l2_cache: Optional[L2Cache] = None
    ):
        self.l1_cache = l1_cache or L1Cache(max_size=l1_max_size, ttl=l1_ttl)
        self.l2_cache = l2_cache or L2Cache(redis_client, namespace)
```

**Key Design Decisions:**
- ✅ Pure Python implementation (no external dependencies like `cachetools`)
- ✅ Backward compatible signature (router.py passes `redis_client` as first param)
- ✅ Supports both simple and advanced initialization
- ✅ Exports L1Cache, L2Cache, MultiLevelCache (required by `__init__.py`)

#### **5. Updated docker-compose.yml**
```yaml
# REMOVED:
- CENTRAL_HUB_URL=http://suho-central-hub:7000

depends_on:
  central-hub:  # REMOVED dependency
    condition: service_healthy

# ADDED:
- CLICKHOUSE_HOST=suho-clickhouse
- CLICKHOUSE_PORT=9000
- CLICKHOUSE_HTTP_PORT=8123
- CLICKHOUSE_DATABASE=suho_analytics
- CLICKHOUSE_USER=suho_analytics
- CLICKHOUSE_PASSWORD=clickhouse_secure_2024
- DRAGONFLY_DB=0  # Was missing
```

### **After Refactoring:**

**Results:**
- ✅ All 3 data-bridge replicas: HEALTHY
- ✅ No SDK dependencies
- ✅ 100% environment variables (12-factor app pattern)
- ✅ Faster startup (no API calls)
- ✅ Independent from Central Hub availability
- ✅ Pure Python cache implementation (no external deps)

**Status Check:**
```bash
$ docker compose ps | grep data-bridge
backend-data-bridge-1   (healthy)
backend-data-bridge-2   (healthy)
backend-data-bridge-3   (healthy)
```

### **Lessons Learned:**

1. **Missing cache.py issue**: File was deleted in previous refactoring
   - **Solution**: Created NEW file aligned with Central Hub architecture (not restored old version)
   - **Reference**: CENTRAL_HUB_FEATURE_MAP.md for correct pattern

2. **Import signature mismatch**: router.py calls `MultiLevelCache(redis_client, ...)`
   - **Solution**: Made `redis_client` first positional parameter for backward compatibility

3. **Missing classes**: `__init__.py` imports L1Cache, L2Cache, MultiLevelCache
   - **Solution**: Exported all three classes from cache.py

4. **External dependencies**: Initial version used `cachetools` library
   - **Solution**: Rewrote to use `collections.OrderedDict` (standard library)

### **Migration Time:**
- **Total time**: ~30 minutes
- **Files changed**: 5 files (config.py, main.py, healthcheck.py, cache.py, docker-compose.yml)
- **Lines changed**: ~150 lines

---

**End of Document**

---

**Maintained by:** Central Hub Team
**Contact:** See project README for contact information
**License:** Proprietary - Suho Trading System
