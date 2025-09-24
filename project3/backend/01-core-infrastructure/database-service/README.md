# Database Service

## 🎯 Purpose
**Centralized multi-tenant database coordination service** yang mengatur data persistence, query optimization, dan database health untuk semua backend services dengan high-performance time-series support dan tenant isolation.

---

## 📊 ChainFlow Diagram

```
Backend Services → Database Service → Database Clusters
       ↓               ↓                    ↓
Multi-tenant       Query Router         PostgreSQL
Service Calls     Tenant Isolation     TimescaleDB
Protocol Buffers  Performance Cache    Redis Cache
Direct Database   Schema Management    Multi-tenant
```

---

## 🏗️ Service Architecture

### **Input Flow**: Database queries dari backend services
**Data Source**: All backend services (Trading-Engine, Analytics, User-Management, etc.)
**Protocol**: Direct database connections + Central Hub coordination
**Data Format**: SQL queries + Protocol Buffers untuk complex operations
**Authentication**: Service-level authentication dengan tenant context
**Performance Target**: <2ms query routing dan tenant validation (part of <30ms total system budget)

### **Output Flow**: Database responses dengan tenant-aware data filtering
**Destinations**: Response langsung ke calling services
**Data Processing**: Multi-tenant filtering, performance optimization, caching
**Connection Management**: Pool connections per tenant untuk optimal performance
**Performance Target**: <5ms untuk simple queries, <50ms untuk complex analytics (within <30ms total system budget)

---

## 🚀 Database Architecture & Multi-Tenant Strategy

### **Multi-Tenant Isolation Strategy:**

#### **Hybrid Approach: Schema + Row-Level Security**
- **Company Level**: Separate schemas per company (tenant_abc, tenant_xyz)
- **User Level**: Row-level security dalam shared tables
- **Performance**: Optimal query performance dengan isolated data
- **Security**: Complete data isolation antar tenants

### **Multi-Database Technology Stack (Per Plan3):**

#### **Primary Database: PostgreSQL**
- **OLTP Workload**: User management, trading transactions, service coordination
- **Multi-tenancy**: Schema-based tenant isolation
- **ACID Compliance**: Critical untuk trading data consistency
- **Performance**: Optimized untuk transactional trading operations

#### **Analytics Database: ClickHouse**
- **OLAP Workload**: Complex analytics, reporting, business intelligence
- **Time-Series Analytics**: Historical trading performance analysis
- **Columnar Storage**: Optimized untuk aggregate queries
- **Performance**: Optimized untuk large-scale analytics queries

#### **High-Performance Cache: DragonflyDB**
- **Redis-Compatible**: Drop-in Redis replacement dengan better performance
- **Multi-threaded**: Superior performance untuk high-frequency trading
- **Memory Efficiency**: 25x more memory efficient than Redis
- **Hot Data**: Frequently accessed user data, configurations, session states

#### **Vector Database: Weaviate**
- **AI/ML Features**: Store dan query ML model embeddings
- **Vector Similarity**: AI pattern matching dan recommendations
- **Real-time**: Fast similarity searches untuk trading patterns
- **Integration**: Native integration dengan ML-Processing service

#### **Graph Database: ArangoDB**
- **Multi-Model**: Document, graph, dan key-value dalam satu database
- **Relationship Analytics**: Complex user relationship dan trading network analysis
- **Flexible Schema**: Dynamic schema untuk varied trading data structures
- **Performance**: Optimized untuk complex relationship queries

### **⚠️ Database Access Pattern**

**Services make DIRECT database connections:**

```
✅ CORRECT Flow:
1. Trading-Engine → Database Service (query: tenant context + SQL)
2. Database Service → PostgreSQL/TimescaleDB (tenant-filtered query)
3. Database Service → Trading-Engine (tenant-filtered results)

✅ Connection Management:
- Each service maintains connection pool to Database Service
- Database Service manages actual database connections
- Tenant context validated at Database Service level
- Query optimization and caching handled centrally

❌ WRONG Flow:
1. Services → Central Hub → Database Service
   (Central Hub should NOT proxy database requests)
```

---

## 🏢 Multi-Tenant Database Design

### **Tenant Isolation Levels:**

#### **Level 1: Company Schema Isolation**
```sql
-- Company-specific schemas
CREATE SCHEMA tenant_company_abc;
CREATE SCHEMA tenant_company_xyz;

-- Per-company tables
CREATE TABLE tenant_company_abc.users (...);
CREATE TABLE tenant_company_abc.mt5_accounts (...);
CREATE TABLE tenant_company_abc.trading_history (...);
```

#### **Level 2: User-Level Row Security**
```sql
-- Shared tables dengan row-level security
CREATE TABLE public.market_data (
    id BIGSERIAL PRIMARY KEY,
    company_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50),
    symbol VARCHAR(20) NOT NULL,
    tick_data JSONB,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Row-level security policy
CREATE POLICY company_isolation ON public.market_data
FOR ALL TO database_service_role
USING (company_id = current_setting('app.current_company_id'));
```

### **Time-Series Data Optimization:**

#### **Trading Data Tables (TimescaleDB Hypertables)**
```sql
-- Tick data untuk real-time trading
CREATE TABLE trading_ticks (
    time TIMESTAMPTZ NOT NULL,
    company_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    bid DECIMAL(10,5),
    ask DECIMAL(10,5),
    volume INTEGER,
    spread DECIMAL(6,2)
);

-- Convert to hypertable untuk time-series optimization
SELECT create_hypertable('trading_ticks', 'time', chunk_time_interval => INTERVAL '1 hour');

-- Company-based partitioning untuk multi-tenancy
SELECT add_dimension('trading_ticks', 'company_id', number_partitions => 4);
```

#### **AI Predictions Storage**
```sql
-- ML predictions dengan confidence scores
CREATE TABLE ai_predictions (
    time TIMESTAMPTZ NOT NULL,
    company_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    prediction_type VARCHAR(50) NOT NULL, -- "buy", "sell", "hold"
    confidence DECIMAL(3,2) NOT NULL, -- 0.00 to 1.00
    model_version VARCHAR(20),
    features JSONB,
    result JSONB
);

SELECT create_hypertable('ai_predictions', 'time', chunk_time_interval => INTERVAL '6 hours');
```

### **Business Data Management:**

#### **User & Subscription Management**
```sql
-- Per-tenant user management
CREATE TABLE tenant_company_abc.users (
    user_id VARCHAR(50) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    subscription_tier VARCHAR(20) NOT NULL, -- "free", "pro", "enterprise"
    subscription_limits JSONB, -- {"max_mt5_accounts": 5, "max_pairs": 10}
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- MT5 accounts per user
CREATE TABLE tenant_company_abc.mt5_accounts (
    account_id BIGINT PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES tenant_company_abc.users(user_id),
    account_number VARCHAR(50) NOT NULL,
    broker VARCHAR(100),
    account_type VARCHAR(20), -- "demo", "live"
    balance DECIMAL(15,2),
    equity DECIMAL(15,2),
    margin DECIMAL(15,2),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### **Configuration & Service Coordination:**
```sql
-- Tenant-specific configurations
CREATE TABLE tenant_configurations (
    company_id VARCHAR(50) NOT NULL,
    config_key VARCHAR(100) NOT NULL,
    config_value JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (company_id, config_key)
);

-- Service registry (shared across all tenants)
CREATE TABLE service_registry (
    service_name VARCHAR(50) PRIMARY KEY,
    service_host VARCHAR(255) NOT NULL,
    service_port INTEGER NOT NULL,
    health_endpoint VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active',
    last_heartbeat TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);
```

---

## 🚀 Transport Architecture & Service Integration

### **Multi-Database Query Categories:**

#### **Kategori A: High-Frequency Trading Operations (PostgreSQL + DragonflyDB)**
- **Query Type**: INSERT trading transactions, SELECT user positions
- **Database**: PostgreSQL dengan DragonflyDB caching
- **Performance**: <2ms transactional operations
- **Caching**: DragonflyDB untuk hot trading data (positions, balances)
- **Use Cases**: Order executions, real-time portfolio updates, user authentication

#### **Kategori B: Analytics & Reporting (ClickHouse)**
- **Query Type**: Complex aggregations, historical performance analysis
- **Database**: ClickHouse untuk OLAP workloads
- **Performance**: <100ms untuk complex analytics queries
- **Use Cases**: Trading performance reports, market trend analysis, business intelligence

#### **Kategori C: AI/ML Pattern Operations (Weaviate)**
- **Query Type**: Vector similarity searches, pattern matching
- **Database**: Weaviate untuk ML embeddings dan patterns
- **Performance**: <50ms untuk similarity queries
- **Use Cases**: Trading pattern recognition, AI recommendations, predictive analytics

#### **Kategori D: Relationship Analysis (ArangoDB)**
- **Query Type**: Graph traversals, multi-model queries
- **Database**: ArangoDB untuk complex relationships
- **Performance**: <200ms untuk graph queries
- **Use Cases**: User network analysis, trading influence patterns, risk correlation

### **Standardized Fallback Strategies:**

#### **Database Connection Fallback (Standardized)**
```python
# Consistent with other services
class DatabaseFallbackManager:
    def __init__(self):
        self.fallback_hierarchy = {
            "primary": "direct_connection",    # Direct database connection
            "secondary": "connection_pool",   # Connection pool fallback
            "tertiary": "cached_response"     # Cached data fallback
        }

    async def query_with_fallback(self, query, params, context):
        """Execute database query with automatic fallback"""
        for connection_type in self.fallback_hierarchy.values():
            try:
                return await self.execute_query(connection_type, query, params, context)
            except DatabaseException as e:
                await self.log_database_failure(connection_type, e)
                continue
        raise AllDatabasesFailedException()
```

### **Multi-Database Service Integration:**
```python
# Services integrate dengan Database Service for multi-database coordination
from database_service_client import MultiDatabaseClient

class TradingEngineService(BaseService):
    def __init__(self):
        super().__init__(config)
        self.db_client = MultiDatabaseClient(
            host="database-service:8080",
            tenant_context=self.tenant_context
        )

    async def save_trading_signal(self, signal_data, tenant_context):
        # Multi-database operation via Database Service
        results = await self.db_client.execute_multi_db_operation({
            # Primary transaction in PostgreSQL
            "postgresql": {
                "query": "INSERT INTO trading_signals (...) VALUES (...)",
                "params": signal_data,
                "company_id": tenant_context["company_id"]
            },
            # Cache update in DragonflyDB
            "dragonflydb": {
                "operation": "set",
                "key": f"signal:{tenant_context['company_id']}:{signal_data['signal_id']}",
                "value": signal_data,
                "ttl": 300  # 5 minutes cache
            },
            # Analytics insert in ClickHouse
            "clickhouse": {
                "query": "INSERT INTO signal_analytics (...) VALUES (...)",
                "params": signal_data
            }
        })
        return results

    async def find_similar_patterns(self, trading_pattern, tenant_context):
        # Vector similarity search via Weaviate
        result = await self.db_client.weaviate_query({
            "operation": "similarity_search",
            "class": "TradingPatterns",
            "vector": trading_pattern["embedding"],
            "tenant_filter": tenant_context["company_id"],
            "limit": 10,
            "certainty": 0.8
        })
        return result
```

---

## Dependencies & Communication Patterns

### **Hybrid Communication Strategy:**
**Database Connections**: Direct connections untuk performance
**Service Coordination**: Query Central Hub untuk service discovery
**Health Monitoring**: Register database health dengan Central Hub
**Configuration**: Receive tenant config updates dari Central Hub

### **Input Contracts:**

**From Backend Services:**
- **from-trading-engine**: Trading signals, execution results, P&L data
- **from-ml-processing**: AI predictions, model results, feature data
- **from-analytics-service**: User analytics, performance metrics queries
- **from-user-management**: User CRUD, subscription updates, MT5 account management
- **from-risk-management**: Risk calculations, portfolio positions, limits
- **from-notification-hub**: Notification logs, delivery status, user preferences

**From External Sources:**
- **from-central-hub-config**: Tenant configuration updates, service coordination
- **from-payment-webhook**: Subscription status changes, billing updates

### **Output Contracts:**

**To Backend Services:**
- **to-all-services**: Query results dengan tenant-filtered data
- **to-central-hub-metrics**: Database performance metrics, health status
- **to-analytics-service**: Aggregated data untuk reporting dan insights

### **Internal Processing:**
- **multi-tenant-isolation**: Automatic tenant context validation
- **query-optimization**: Query planning dan performance analysis
- **connection-pooling**: Efficient database connection management
- **caching-strategy**: Multi-layer caching (Redis + application cache)
- **backup-strategy**: Automated backups dengan point-in-time recovery
- **monitoring-alerting**: Performance monitoring, slow query detection

### **Standardized Health Check (Multi-Database):**
```python
# Database Service health check compliant with standard format
@app.get("/health")
async def multi_database_health():
    return {
        "service_name": "database-service",
        "status": await calculate_overall_status(),
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "uptime_seconds": await get_uptime_seconds(),
        "performance_metrics": {
            "response_time_ms": await get_avg_response_time(),
            "throughput_rps": await get_current_throughput(),
            "error_rate_percent": await get_error_rate()
        },
        "system_resources": {
            "cpu_usage_percent": await get_cpu_usage(),
            "memory_usage_mb": await get_memory_usage(),
            "disk_usage_percent": await get_disk_usage()
        },
        "dependencies": {
            "postgresql": await check_postgresql_health(),
            "clickhouse": await check_clickhouse_health(),
            "dragonflydb": await check_dragonflydb_health(),
            "weaviate": await check_weaviate_health(),
            "arangodb": await check_arangodb_health()
        },
        "tenant_context": {
            "active_tenants": await count_active_tenants(),
            "tenant_isolation_status": "healthy"
        },
        # Service-specific multi-database details
        "database_details": {
            "postgresql": {
                "active_connections": await get_pg_connection_count(),
                "tenant_schemas": await count_pg_tenant_schemas()
            },
            "clickhouse": {
                "active_queries": await get_ch_active_queries(),
                "disk_usage_gb": await get_ch_disk_usage()
            },
            "dragonflydb": {
                "memory_usage_mb": await get_df_memory_usage(),
                "cache_hit_rate_percent": await get_df_cache_stats()
            },
            "weaviate": {
                "objects_count": await get_weaviate_object_count(),
                "vector_dimensions": await get_weaviate_schema_info()
            },
            "arangodb": {
                "collections_count": await get_arango_collections(),
                "graph_performance_ms": await get_arango_graph_stats()
            }
        },
        "multi_db_performance": {
            "cross_database_queries": await get_cross_db_query_stats(),
            "transaction_consistency": await check_multi_db_consistency()
        }
    }
```

---

## 🎯 Multi-Tenant Business Value

### **Data Isolation & Security:**
- **Complete Tenant Separation**: Schema-level isolation untuk companies
- **Row-Level Security**: User-level data filtering dalam shared tables
- **Audit Trails**: Complete database activity logging per tenant
- **Compliance Ready**: Support untuk financial data regulations

### **Performance Optimization:**
- **Time-Series Optimization**: TimescaleDB untuk high-frequency trading data
- **Multi-Layer Caching**: Redis + application cache untuk hot data
- **Connection Pooling**: Optimized connections per tenant
- **Query Optimization**: Tenant-aware query planning

### **Scalability & Reliability:**
- **Horizontal Scaling**: Support untuk read replicas dan sharding
- **High Availability**: Automated failover dan backup strategies
- **Load Distribution**: Query routing berdasarkan workload type
- **Resource Isolation**: Per-tenant resource limits dan monitoring

### **Development Efficiency:**
- **Shared Database Patterns**: StandardDatabaseManager untuk all services
- **Schema Management**: Automated migration dan versioning
- **Integration Simplicity**: Consistent database client patterns
- **Monitoring & Alerting**: Comprehensive database observability

---

**Key Innovation**: Multi-tenant database coordination yang optimized untuk high-frequency trading data dengan complete tenant isolation dan real-time performance monitoring.