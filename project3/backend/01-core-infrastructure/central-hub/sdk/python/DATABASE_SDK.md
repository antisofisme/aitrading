# Central Hub Database SDK v2.0

Comprehensive multi-database integration layer with auto-initialization and smart routing.

## 🎯 Features

### Supported Databases

1. **TimescaleDB** (PostgreSQL + time-series) - Real-time tick data
2. **ClickHouse** - Analytics and OLAP queries
3. **DragonflyDB** (Redis-compatible) - Ultra-fast caching
4. **ArangoDB** - Graph and document database
5. **Weaviate** - Vector database for ML embeddings

### Key Capabilities

✅ **Auto Schema Initialization** - SQL files executed automatically on startup
✅ **Smart Routing** - Data automatically routed to optimal database
✅ **Connection Pooling** - Efficient resource management
✅ **Health Monitoring** - Real-time health checks for all databases
✅ **Retry Logic** - Automatic reconnection with exponential backoff
✅ **Fallback Mechanisms** - Graceful degradation when databases unavailable

---

## 📦 Installation

```bash
pip install central-hub-sdk==2.0.0
```

Dependencies automatically installed:
- `asyncpg` - TimescaleDB/PostgreSQL
- `clickhouse-connect` - ClickHouse
- `redis[hiredis]` - DragonflyDB
- `python-arango` - ArangoDB
- `weaviate-client` - Weaviate

---

## 🚀 Quick Start

### 1. Basic Setup

```python
from central_hub_sdk import DatabaseRouter, SchemaMigrator, DatabaseHealthChecker

# Configuration for all databases
config = {
    'timescaledb': {
        'host': 'localhost',
        'port': 5432,
        'database': 'suho_trading',
        'user': 'suho_admin',
        'password': 'your_password',
        'pool_size': 10
    },
    'clickhouse': {
        'host': 'localhost',
        'port': 8123,
        'database': 'suho_analytics',
        'user': 'default',
        'password': '',
        'compress': True
    },
    'dragonflydb': {
        'host': 'localhost',
        'port': 6379,
        'db': 0,
        'max_connections': 50
    },
    # Optional: ArangoDB and Weaviate
    'arangodb': {
        'host': 'localhost',
        'port': 8529,
        'database': '_system',
        'username': 'root',
        'password': ''
    },
    'weaviate': {
        'host': 'localhost',
        'port': 8080,
        'use_grpc': True
    }
}

# Initialize router
router = DatabaseRouter(config)
await router.initialize()
```

### 2. Auto-Initialize Schemas

```python
# Schema files should be organized as:
# /schemas/
#   ├── timescaledb/
#   │   ├── 01_market_ticks.sql
#   │   ├── 02_market_candles.sql
#   │   └── 03_market_context.sql
#   ├── clickhouse/
#   │   ├── 01_ticks.sql
#   │   └── 02_aggregates.sql
#   └── ...

migrator = SchemaMigrator(router, schema_base_path="/app/shared/schemas")
results = await migrator.initialize_all_schemas()

# Results: {'timescaledb': True, 'clickhouse': True, 'dragonflydb': True}
```

### 3. Health Monitoring

```python
health_checker = DatabaseHealthChecker(router)

# Check all databases
report = await health_checker.check_all()

print(report)
# {
#   "status": "healthy",
#   "timestamp": "2025-10-14T14:30:00Z",
#   "databases": {
#     "timescaledb": {"status": "healthy", "pool": {"size": 10, "free": 8}},
#     "clickhouse": {"status": "healthy", "tables": 8},
#     "dragonflydb": {"status": "healthy", "keys": 1234}
#   },
#   "summary": {"total": 3, "healthy": 3, "degraded": 0, "unhealthy": 0}
# }

# Wait for all databases to be healthy
await health_checker.wait_for_healthy(timeout=60)
```

---

## 💡 Usage Examples

### Example 1: Smart Routing

```python
from central_hub_sdk.database import DataCategory

# Get database manager for tick data (auto-routed to TimescaleDB)
tick_manager = router.get_manager(category=DataCategory.TICK_DATA)

# Direct database access
clickhouse = router.get_manager(db_type=DatabaseType.CLICKHOUSE)
```

### Example 2: TimescaleDB Operations

```python
# Get TimescaleDB manager
timescale = router.get_manager(db_type=DatabaseType.TIMESCALEDB)

# Query with timeout
rows = await timescale.execute_query(
    "SELECT * FROM market_ticks WHERE symbol = $1 LIMIT 100",
    'EUR/USD',
    timeout=30.0
)

# Create hypertable
await timescale.create_hypertable(
    'market_ticks',
    time_column='time',
    chunk_interval='1 day'
)

# Get connection for complex operations
async with timescale.get_connection() as conn:
    # Use asyncpg connection directly
    await conn.execute("...")
```

### Example 3: ClickHouse Analytics

```python
clickhouse = router.get_manager(db_type=DatabaseType.CLICKHOUSE)

# Bulk insert
data = [
    ['EUR/USD', '5m', 1697123400000, 1.0850, ...],
    ['GBP/USD', '5m', 1697123400000, 1.2150, ...],
]

await clickhouse.insert_bulk(
    table='aggregates',
    data=data,
    column_names=['symbol', 'timeframe', 'timestamp_ms', 'close', ...]
)

# Analytics query
results = await clickhouse.execute_query(
    """
    SELECT symbol, AVG(close) as avg_price
    FROM aggregates
    WHERE timestamp >= now() - INTERVAL 1 DAY
    GROUP BY symbol
    """
)
```

### Example 4: DragonflyDB Caching

```python
dragonfly = router.get_manager(db_type=DatabaseType.DRAGONFLYDB)

# Set with TTL
await dragonfly.set('tick:latest:EURUSD', tick_data, ttl=60)

# Get
tick = await dragonfly.get('tick:latest:EURUSD')

# Check existence
exists = await dragonfly.exists('tick:latest:EURUSD')

# Delete
await dragonfly.delete('tick:latest:EURUSD')
```

### Example 5: ArangoDB Graph Operations

```python
arango = router.get_manager(db_type=DatabaseType.ARANGODB)

# Get collection
trades_coll = arango.get_collection('trades')

# AQL query
results = await arango.execute_query(
    """
    FOR trade IN trades
        FILTER trade.symbol == @symbol
        SORT trade.timestamp DESC
        LIMIT @limit
        RETURN trade
    """,
    bind_vars={'symbol': 'EUR/USD', 'limit': 100}
)

# Get graph
graph = arango.get_graph('trading_relationships')
```

### Example 6: Weaviate Vector Search

```python
weaviate = router.get_manager(db_type=DatabaseType.WEAVIATE)

# Semantic search
results = weaviate.semantic_search(
    class_name='TradingSignals',
    query='bullish EUR/USD pattern',
    properties=['symbol', 'signal_type', 'confidence'],
    limit=10
)

# Batch insert
objects = [
    {'symbol': 'EUR/USD', 'embedding': [0.1, 0.2, ...], ...},
    {'symbol': 'GBP/USD', 'embedding': [0.3, 0.4, ...], ...},
]

weaviate.batch_insert('TradingSignals', objects)
```

---

## 🏗️ Architecture

### Connection Managers

Each database has a dedicated manager implementing `BaseConnectionManager`:

- `TimescaleDBManager` - PostgreSQL + TimescaleDB extensions
- `ClickHouseManager` - HTTP/Native protocol support
- `DragonflyDBManager` - Redis-compatible async client
- `ArangoDBManager` - Multi-model (graph/document)
- `WeaviateManager` - Vector similarity search

### Smart Router

`DatabaseRouter` handles:
- Auto-routing based on data category
- Data replication to secondary databases
- Health monitoring
- Connection lifecycle management

### Schema Migrator

`SchemaMigrator` handles:
- SQL file discovery and execution
- Version tracking (future)
- Idempotent migrations
- Rollback support (future)

---

## 🔧 Configuration

### Environment Variables (Recommended)

```bash
# TimescaleDB
TIMESCALE_HOST=localhost
TIMESCALE_PORT=5432
TIMESCALE_DB=suho_trading
TIMESCALE_USER=suho_admin
TIMESCALE_PASSWORD=secret

# ClickHouse
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
CLICKHOUSE_DB=suho_analytics

# DragonflyDB
DRAGONFLY_HOST=localhost
DRAGONFLY_PORT=6379
```

### Docker Compose Integration

```yaml
services:
  my-service:
    build: .
    depends_on:
      postgresql:
        condition: service_healthy
      clickhouse:
        condition: service_healthy
      dragonflydb:
        condition: service_healthy
    environment:
      TIMESCALE_HOST: postgresql
      CLICKHOUSE_HOST: clickhouse
      DRAGONFLY_HOST: dragonflydb
```

---

## 🧪 Testing

```python
import pytest
from central_hub_sdk import DatabaseRouter, DatabaseHealthChecker

@pytest.mark.asyncio
async def test_database_connectivity():
    router = DatabaseRouter(test_config)
    assert await router.initialize()

    health_checker = DatabaseHealthChecker(router)
    report = await health_checker.check_all()

    assert report['status'] == 'healthy'
    assert report['summary']['healthy'] == 3

    await router.close_all()
```

---

## 📝 Best Practices

1. **Always use the router** - Don't create managers directly
2. **Initialize schemas on startup** - Use SchemaMigrator in service init
3. **Monitor health regularly** - Implement periodic health checks
4. **Use connection pooling** - Let managers handle connections
5. **Handle failures gracefully** - Implement fallbacks for non-critical databases

---

## 🔄 Migration from v1.x

```python
# Old way (v1.x) - manual connection management
import asyncpg
pool = await asyncpg.create_pool(host='localhost', ...)
conn = await pool.acquire()
await conn.fetch("SELECT ...")
await pool.release(conn)

# New way (v2.0) - SDK handles everything
from central_hub_sdk import DatabaseRouter
router = DatabaseRouter(config)
await router.initialize()

timescale = router.get_manager(db_type=DatabaseType.TIMESCALEDB)
rows = await timescale.execute_query("SELECT ...")
```

---

## 🚨 Troubleshooting

### Schema Files Not Found

```python
# Check schema path
migrator = SchemaMigrator(router, schema_base_path="/correct/path")
files = migrator.get_schema_files(DatabaseType.TIMESCALEDB)
print(f"Found {len(files)} schema files")
```

### Connection Timeouts

```python
# Increase timeout in config
config['timescaledb']['command_timeout'] = 120

# Or per-query
rows = await timescale.execute_query(query, timeout=60.0)
```

### Health Check Failures

```python
# Wait for databases to be ready
health_checker = DatabaseHealthChecker(router)
is_healthy = await health_checker.wait_for_healthy(timeout=120)

if not is_healthy:
    # Check individual databases
    report = await health_checker.check_all()
    print(report['databases'])
```

---

## 📚 API Reference

See inline documentation in source code:
- `database/base.py` - Base connection manager interface
- `database/router.py` - Smart routing logic
- `database/migrator.py` - Schema migration system
- `database/health.py` - Health monitoring

---

## 🤝 Contributing

This SDK is part of the Suho Trading System. For bugs or feature requests, contact the development team.

**Version:** 2.0.0
**Last Updated:** 2025-10-14
**Status:** Production Ready ✅
