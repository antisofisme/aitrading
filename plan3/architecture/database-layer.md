# Database Layer Architecture (Level 1.2 dari Plan2)

## 🗄️ Multi-Database Architecture Overview

**Basis**: AI Trading heritage dengan **5 database stack** yang sudah proven + business enhancement

```yaml
Database_Heritage_Benefits (dari Plan2):
  Production_Tested: "Multi-database stack proven dalam ai_trading production"
  Performance_Optimized: "Connection pooling dan 100x improvement"
  Enterprise_Ready: "PostgreSQL, ClickHouse, Weaviate, ArangoDB, DragonflyDB"
  Business_Enhanced: "Multi-tenant isolation dan subscription billing data"
```

## 🏗️ Database Service Architecture

### **Dedicated Database Service (Port 8008)**:
```python
# Database Service Implementation dari Plan2
class DatabaseService:
    def __init__(self):
        self.ai_trading_heritage = {
            'performance': '100x improvement via connection pooling',
            'reliability': 'Production-tested multi-DB coordination',
            'scalability': 'Enterprise data management capabilities'
        }

        self.database_connections = self.initialize_connections()
        self.multi_tenant_manager = MultiTenantManager()

    def initialize_connections(self):
        """Initialize all database connections dengan AI Trading heritage"""
        return {
            'postgresql': self.setup_postgresql_connection(),
            'clickhouse': self.setup_clickhouse_connection(),
            'dragonflydb': self.setup_dragonfly_connection(),
            'weaviate': self.setup_weaviate_connection(),
            'arangodb': self.setup_arango_connection()
        }
```

### **ML Processing + Database Service (Port 8006)**:
```python
# Combined service dari Plan2 - Traditional ML + Database coordination
class MLDatabaseService:
    def __init__(self):
        self.database_component = DatabaseService()  # Shared database functionality
        self.ml_component = TraditionalMLProcessor()

    async def process_ml_with_data(self, features: Features, user_context: UserContext):
        """ML processing dengan direct database access"""
        # Get historical data untuk ML training
        historical_data = await self.database_component.get_historical_data(
            user_context, features.timeframe
        )

        # Process dengan traditional ML
        ml_result = await self.ml_component.process(features, historical_data)

        # Store results back ke database
        await self.database_component.store_ml_results(ml_result, user_context)

        return ml_result
```

---

## 🐘 PostgreSQL - Core Relational Data

### **Purpose**: User data, configurations, subscription data

#### **AI Trading Heritage Tables**:
```sql
-- User management (enhanced dari ai_trading)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Business enhancement
    tenant_id UUID NOT NULL,
    subscription_tier VARCHAR(20) DEFAULT 'free',
    subscription_start_date TIMESTAMP,
    subscription_end_date TIMESTAMP,
    billing_customer_id VARCHAR(100)
);

-- Trading accounts (dari ai_trading + business context)
CREATE TABLE trading_accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    account_number VARCHAR(50) NOT NULL,
    broker VARCHAR(100) NOT NULL,
    account_type VARCHAR(20) NOT NULL, -- demo/live
    balance DECIMAL(15,2),
    equity DECIMAL(15,2),
    margin DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Business enhancement
    tenant_id UUID NOT NULL,
    subscription_limits JSONB,
    usage_stats JSONB
);
```

#### **Business Enhancement Tables**:
```sql
-- Subscription management (new untuk business)
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    tier VARCHAR(20) NOT NULL, -- free, pro, enterprise
    status VARCHAR(20) NOT NULL, -- active, cancelled, expired
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP,
    billing_cycle VARCHAR(20), -- monthly, yearly
    price DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Usage tracking (new untuk billing)
CREATE TABLE usage_tracking (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    service_name VARCHAR(50) NOT NULL,
    usage_type VARCHAR(50) NOT NULL, -- api_calls, ticks_processed, ai_decisions
    usage_count INTEGER NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    billing_period DATE NOT NULL
);

-- API keys dan access (new untuk enterprise)
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    key_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100),
    permissions JSONB,
    rate_limit INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    last_used_at TIMESTAMP
);
```

#### **Multi-Tenant Isolation**:
```sql
-- Tenant isolation function
CREATE OR REPLACE FUNCTION apply_tenant_filter()
RETURNS TRIGGER AS $$
BEGIN
    -- Auto-apply tenant_id untuk all multi-tenant tables
    IF TG_OP = 'INSERT' THEN
        NEW.tenant_id = current_setting('app.current_tenant_id');
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Apply ke all multi-tenant tables
CREATE TRIGGER users_tenant_trigger
    BEFORE INSERT ON users
    FOR EACH ROW EXECUTE FUNCTION apply_tenant_filter();
```

### **Performance Optimization** (AI Trading Heritage):
```sql
-- Indexes untuk performance (dari ai_trading experience)
CREATE INDEX idx_users_tenant_email ON users(tenant_id, email);
CREATE INDEX idx_trading_accounts_user ON trading_accounts(user_id);
CREATE INDEX idx_subscriptions_user_status ON subscriptions(user_id, status);
CREATE INDEX idx_usage_tracking_user_period ON usage_tracking(user_id, billing_period);

-- Connection pooling configuration
-- (maintained dari ai_trading proven setup)
```

---

## ⚡ ClickHouse - Time Series Data

### **Purpose**: High-frequency trading data, analytics

#### **Market Data Tables** (AI Trading Heritage):
```sql
-- Market ticks (enhanced dari ai_trading)
CREATE TABLE market_ticks (
    tenant_id String,
    user_id String,
    symbol String,
    timestamp DateTime64(3),
    bid Float64,
    ask Float64,
    volume Float64,
    spread Float64,

    -- Business enhancement
    subscription_tier String,
    data_source String
) ENGINE = MergeTree()
PARTITION BY (tenant_id, toYYYYMM(timestamp))
ORDER BY (tenant_id, user_id, symbol, timestamp);

-- OHLCV data dengan multi-tenant support
CREATE TABLE ohlcv_data (
    tenant_id String,
    user_id String,
    symbol String,
    timeframe String, -- 1m, 5m, 1h, 1d
    timestamp DateTime,
    open Float64,
    high Float64,
    low Float64,
    close Float64,
    volume Float64,

    -- AI Trading heritage
    technical_indicators Map(String, Float64)
) ENGINE = MergeTree()
PARTITION BY (tenant_id, symbol, timeframe, toYYYYMM(timestamp))
ORDER BY (tenant_id, user_id, symbol, timeframe, timestamp);
```

#### **Trading Performance Data**:
```sql
-- Trade executions dengan tenant isolation
CREATE TABLE trades (
    tenant_id String,
    user_id String,
    trade_id String,
    account_id String,
    symbol String,
    type String, -- buy/sell
    volume Float64,
    open_price Float64,
    close_price Float64,
    open_time DateTime64(3),
    close_time DateTime64(3),
    profit Float64,
    commission Float64,
    swap Float64,
    strategy_id String,

    -- Business context
    subscription_tier String,
    ai_agents_used Array(String)
) ENGINE = MergeTree()
PARTITION BY (tenant_id, toYYYYMM(open_time))
ORDER BY (tenant_id, user_id, open_time);

-- AI decision tracking
CREATE TABLE ai_decisions (
    tenant_id String,
    user_id String,
    decision_id String,
    symbol String,
    timestamp DateTime64(3),
    agent_name String,
    decision_type String, -- buy/sell/hold
    confidence Float64,
    reasoning String,
    market_conditions Map(String, Float64),

    -- Performance tracking
    outcome String, -- profitable/loss/pending
    outcome_timestamp DateTime64(3)
) ENGINE = MergeTree()
PARTITION BY (tenant_id, toYYYYMM(timestamp))
ORDER BY (tenant_id, user_id, timestamp);
```

### **Performance Targets** (dari Plan2):
```sql
-- Query performance optimization
-- Target: <100ms analytics query
CREATE MATERIALIZED VIEW user_performance_summary
ENGINE = SummingMergeTree()
PARTITION BY (tenant_id, toYYYYMM(date))
ORDER BY (tenant_id, user_id, date)
AS SELECT
    tenant_id,
    user_id,
    toDate(timestamp) as date,
    count() as total_trades,
    sum(profit) as total_profit,
    avg(confidence) as avg_confidence
FROM trades t
JOIN ai_decisions d ON t.trade_id = d.decision_id
GROUP BY tenant_id, user_id, date;
```

---

## 🚀 DragonflyDB - Caching Layer

### **Purpose**: High-performance caching

#### **Cache Structure dengan Multi-Tenant Support**:
```python
class MultiTenantCache:
    def __init__(self):
        self.dragonfly_client = DragonflyClient()

    def get_tenant_key(self, tenant_id: str, user_id: str, key: str) -> str:
        """Generate tenant-isolated cache key"""
        return f"{tenant_id}:{user_id}:{key}"

    async def cache_market_data(self, tenant_id: str, user_id: str, symbol: str, data: MarketData):
        """Cache market data dengan tenant isolation"""
        cache_key = self.get_tenant_key(tenant_id, user_id, f"market:{symbol}")
        await self.dragonfly_client.setex(
            cache_key,
            ttl=5,  # 5 seconds TTL untuk real-time data
            value=data.json()
        )

    async def cache_ai_prediction(self, tenant_id: str, user_id: str, symbol: str, prediction: AIPrediction):
        """Cache AI predictions dengan subscription-aware TTL"""
        tier_ttl = {
            'free': 300,      # 5 minutes
            'pro': 60,        # 1 minute
            'enterprise': 30  # 30 seconds
        }

        user_tier = await self.get_user_tier(user_id)
        ttl = tier_ttl.get(user_tier, 300)

        cache_key = self.get_tenant_key(tenant_id, user_id, f"ai:prediction:{symbol}")
        await self.dragonfly_client.setex(cache_key, ttl, prediction.json())
```

#### **Session Management**:
```python
class SessionCache:
    async def store_user_session(self, user_context: UserContext, session_data: SessionData):
        """Store user session dengan tenant context"""
        session_key = f"session:{user_context.tenant_id}:{user_context.user_id}"
        await self.dragonfly_client.setex(
            session_key,
            ttl=3600,  # 1 hour
            value=session_data.json()
        )

    async def get_user_session(self, user_context: UserContext) -> Optional[SessionData]:
        """Get user session dengan tenant isolation"""
        session_key = f"session:{user_context.tenant_id}:{user_context.user_id}"
        cached_data = await self.dragonfly_client.get(session_key)
        return SessionData.parse_raw(cached_data) if cached_data else None
```

### **Performance Target**: <1ms cache access (dari Plan2)

---

## 🧠 Weaviate - Vector Database

### **Purpose**: Vector embeddings untuk AI

#### **Schema Structure** (AI Trading + Business Enhancement):
```json
{
  "class": "MarketPattern",
  "properties": [
    {"name": "tenantId", "dataType": ["string"]},
    {"name": "userId", "dataType": ["string"]},
    {"name": "symbol", "dataType": ["string"]},
    {"name": "patternType", "dataType": ["string"]},
    {"name": "timeframe", "dataType": ["string"]},
    {"name": "features", "dataType": ["number[]"]},
    {"name": "outcome", "dataType": ["string"]},
    {"name": "confidence", "dataType": ["number"]},
    {"name": "timestamp", "dataType": ["date"]},
    {"name": "subscriptionTier", "dataType": ["string"]}
  ],
  "vectorizer": "text2vec-openai",
  "multiTenancy": {
    "enabled": true
  }
}
```

#### **AI Pattern Storage**:
```python
class VectorPatternStorage:
    def __init__(self):
        self.weaviate_client = WeaviateClient()

    async def store_trading_pattern(self, pattern: TradingPattern, user_context: UserContext):
        """Store trading pattern dengan tenant isolation"""
        vector_object = {
            "tenantId": user_context.tenant_id,
            "userId": user_context.user_id,
            "symbol": pattern.symbol,
            "patternType": pattern.type,
            "features": pattern.features.tolist(),
            "outcome": pattern.outcome,
            "confidence": pattern.confidence,
            "subscriptionTier": user_context.subscription_tier
        }

        await self.weaviate_client.data_object.create(
            data_object=vector_object,
            class_name="MarketPattern",
            tenant=user_context.tenant_id
        )

    async def find_similar_patterns(self, query_pattern: TradingPattern, user_context: UserContext):
        """Find similar patterns dalam tenant scope"""
        result = await self.weaviate_client.query.get("MarketPattern") \
            .with_near_vector({"vector": query_pattern.features.tolist()}) \
            .with_tenant(user_context.tenant_id) \
            .with_where({
                "path": ["subscriptionTier"],
                "operator": "Equal",
                "valueString": user_context.subscription_tier
            }) \
            .with_limit(10) \
            .do()

        return result
```

---

## 🕸️ ArangoDB - Graph Database

### **Purpose**: Complex relationships

#### **Collections Structure**:
```javascript
// Document Collections dengan tenant support
db._create("symbols");
db._create("strategies");
db._create("users");
db._create("agents");

// Edge Collections untuk relationships
db._createEdgeCollection("symbol_correlations");
db._createEdgeCollection("strategy_dependencies");
db._createEdgeCollection("user_strategies");
db._createEdgeCollection("agent_interactions");
```

#### **Multi-Tenant Graph Queries**:
```javascript
// Symbol correlation analysis dalam tenant scope
function getSymbolCorrelations(tenantId, userId, symbol) {
    return db._query(`
        FOR v, e, p IN 1..2 OUTBOUND
            CONCAT('symbols/', @symbol)
            symbol_correlations
            FILTER e.tenantId == @tenantId
            AND (e.userId == @userId OR e.scope == 'global')
            RETURN {
                symbol: v.symbol,
                correlation: e.correlation,
                timeframe: e.timeframe,
                path: p
            }
    `, {
        tenantId: tenantId,
        userId: userId,
        symbol: symbol
    });
}

// Agent interaction analysis
function getAgentCollaboration(tenantId, userId) {
    return db._query(`
        FOR v, e IN 1..3 ANY
            CONCAT('users/', @userId)
            agent_interactions
            FILTER e.tenantId == @tenantId
            COLLECT agent = v.agentType
            AGGREGATE interactions = SUM(e.interactionScore)
            RETURN {
                agent: agent,
                totalInteractions: interactions
            }
    `, {
        tenantId: tenantId,
        userId: userId
    });
}
```

---

## 🔄 Database Layer Integration

### **Multi-Database Coordination**:
```python
class DatabaseCoordinator:
    def __init__(self):
        self.postgresql = PostgreSQLConnection()
        self.clickhouse = ClickHouseConnection()
        self.dragonflydb = DragonflyConnection()
        self.weaviate = WeaviateConnection()
        self.arangodb = ArangoConnection()

    async def execute_multi_db_transaction(self, operations: List[DatabaseOperation], user_context: UserContext):
        """Execute operations across multiple databases dengan consistency"""
        transaction_id = self.generate_transaction_id()

        try:
            # Execute pada each database
            for operation in operations:
                db_connection = self.get_connection(operation.database)
                await db_connection.execute(operation, user_context)

            # Commit all
            await self.commit_all_databases(transaction_id)

        except Exception as e:
            # Rollback all
            await self.rollback_all_databases(transaction_id)
            raise DatabaseTransactionError(f"Multi-DB transaction failed: {e}")
```

### **Performance Monitoring** (dari Plan2):
```python
class DatabasePerformanceMonitor:
    def __init__(self):
        self.metrics = {
            'postgresql_query_time': Histogram('postgresql_query_seconds'),
            'clickhouse_query_time': Histogram('clickhouse_query_seconds'),
            'dragonflydb_access_time': Histogram('cache_access_ms'),
            'weaviate_vector_search_time': Histogram('vector_search_seconds'),
            'arangodb_graph_traversal_time': Histogram('graph_traversal_seconds')
        }

    async def monitor_query_performance(self, db_type: str, query: str, execution_time: float):
        """Monitor database performance across all databases"""
        self.metrics[f'{db_type}_query_time'].observe(execution_time)

        # Alert jika performance degradation
        if execution_time > self.get_performance_threshold(db_type):
            await self.send_performance_alert(db_type, query, execution_time)
```

**Database Layer Status**: PLANNED - Foundation proven dari ai_trading dengan business enhancements
**Performance Foundation**: 100x improvement via connection pooling, <100ms query targets