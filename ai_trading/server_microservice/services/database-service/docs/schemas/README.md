# Database Schemas Documentation

**Complete schema reference for all 6 database systems with 128+ schema definitions**

## Schema Overview

The Database Service manages comprehensive schemas across 6 different database systems, totaling 128 schema definitions optimized for high-frequency trading operations.

## Database Schema Summary

| Database | Type | Tables/Collections | Primary Use Case |
|----------|------|-------------------|------------------|
| **ClickHouse** | Time-Series | 98 tables | Trading data, ticks, indicators, ML/DL processing |
| **PostgreSQL** | Relational | 8 tables | User authentication, ML metadata |
| **ArangoDB** | Graph | 6 collections | Strategy relationships, dependencies |
| **Weaviate** | Vector | 4 classes | AI embeddings, pattern recognition |
| **DragonflyDB** | Cache | 7 patterns | High-performance caching |
| **Redpanda** | Streaming | 5 topics | Real-time data streams |

**Total**: 128 schema definitions

## Schema Architecture

### 1. ClickHouse Schemas (98 Tables)

#### Raw Data Schemas (9 tables)
```sql
-- Core tick data table
CREATE TABLE ticks (
    timestamp DateTime64(3, 'UTC'),
    symbol LowCardinality(String),
    bid Float64 CODEC(Delta, LZ4),
    ask Float64 CODEC(Delta, LZ4),
    last Float64 CODEC(Delta, LZ4),
    volume UInt64 CODEC(Delta, LZ4),
    spread Float32 CODEC(LZ4),
    primary_session Bool,
    broker LowCardinality(String),
    account_type LowCardinality(String)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, broker, timestamp)
SETTINGS index_granularity = 8192;

-- Account information
CREATE TABLE account_info (
    timestamp DateTime,
    account_id String,
    balance Float64,
    equity Float64,
    margin Float64,
    free_margin Float64,
    margin_level Float64,
    currency String,
    broker String,
    account_type String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (account_id, broker, timestamp);

-- Trading positions
CREATE TABLE positions (
    timestamp DateTime,
    position_id String,
    symbol String,
    position_type Enum8('BUY' = 1, 'SELL' = 2),
    volume Float64,
    open_price Float64,
    current_price Float64,
    profit Float64,
    swap Float64,
    commission Float64,
    broker String,
    account_type String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, broker, timestamp);
```

#### Technical Indicators (20 tables)
```sql
-- Simple Moving Average
CREATE TABLE sma_20 (
    timestamp DateTime,
    symbol String,
    timeframe String,
    sma_value Float64,
    period UInt16,
    broker String,
    account_type String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, timeframe, timestamp);

-- Exponential Moving Average
CREATE TABLE ema_50 (
    timestamp DateTime,
    symbol String,
    timeframe String,
    ema_value Float64,
    period UInt16,
    smoothing_factor Float64,
    broker String,
    account_type String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, timeframe, timestamp);

-- Relative Strength Index
CREATE TABLE rsi_14 (
    timestamp DateTime,
    symbol String,
    timeframe String,
    rsi_value Float64,
    period UInt16,
    overbought_level Float64,
    oversold_level Float64,
    broker String,
    account_type String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, timeframe, timestamp);
```

#### ML Processing Tables (31 tables)
```sql
-- ML feature store
CREATE TABLE ml_features_combined (
    timestamp DateTime,
    symbol String,
    timeframe String,
    feature_vector Array(Float64),
    feature_names Array(String),
    model_version String,
    broker String,
    account_type String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, timeframe, timestamp);

-- ML predictions
CREATE TABLE ml_tick_patterns (
    timestamp DateTime,
    symbol String,
    pattern_type String,
    confidence_score Float64,
    prediction_horizon_minutes UInt16,
    model_id String,
    feature_importance Array(Float64),
    broker String,
    account_type String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, timestamp);
```

### 2. PostgreSQL Schemas (8 Tables)

#### User Authentication
```sql
-- Organizations table
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255),
    subscription_tier VARCHAR(50) DEFAULT 'basic',
    api_rate_limit INTEGER DEFAULT 1000,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    organization_id UUID REFERENCES organizations(id),
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- API keys table
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100),
    permissions JSONB DEFAULT '{}',
    rate_limit INTEGER,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### ML Metadata
```sql
-- Model registry
CREATE TABLE model_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    model_type VARCHAR(100) NOT NULL,
    framework VARCHAR(50),
    performance_metrics JSONB,
    hyperparameters JSONB,
    training_data_hash VARCHAR(64),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(name, version)
);

-- Training runs
CREATE TABLE training_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID REFERENCES model_registry(id),
    status VARCHAR(50) DEFAULT 'pending',
    start_time TIMESTAMP DEFAULT NOW(),
    end_time TIMESTAMP,
    training_config JSONB,
    metrics JSONB,
    artifacts_path TEXT,
    error_message TEXT
);
```

### 3. ArangoDB Schemas (6 Collections)

#### Strategy Collections
```javascript
// Trading strategies collection
{
  "_key": "strategy_001",
  "name": "Mean Reversion EURUSD",
  "strategy_type": "mean_reversion",
  "instruments": ["EURUSD"],
  "timeframe": "H1",
  "parameters": {
    "lookback_period": 20,
    "deviation_threshold": 2.0,
    "position_size": 0.1
  },
  "performance_metrics": {
    "total_return": 15.6,
    "sharpe_ratio": 1.8,
    "max_drawdown": -5.2
  },
  "created_at": "2025-07-31T10:00:00Z",
  "updated_at": "2025-07-31T10:00:00Z"
}

// Strategy components
{
  "_key": "component_001",
  "strategy_id": "strategy_001",
  "component_type": "indicator",
  "name": "SMA_20",
  "parameters": {
    "period": 20,
    "source": "close"
  },
  "weight": 0.4
}

// Strategy backtests
{
  "_key": "backtest_001",
  "strategy_id": "strategy_001",
  "backtest_period": {
    "start": "2025-01-01",
    "end": "2025-07-31"
  },
  "results": {
    "total_trades": 156,
    "winning_trades": 98,
    "total_return": 18.5,
    "max_drawdown": -4.8
  }
}
```

#### Relationship Collections
```javascript
// Component relationships (edges)
{
  "_from": "strategies/strategy_001",
  "_to": "components/component_001",
  "relationship_type": "uses_component",
  "weight": 0.8,
  "created_at": "2025-07-31T10:00:00Z"
}

// Strategy dependencies
{
  "_from": "strategies/strategy_001",
  "_to": "strategies/strategy_002",
  "dependency_type": "requires_signal",
  "priority": 1
}
```

### 4. Weaviate Schemas (4 Classes)

#### Vector Classes
```python
# Market sentiment class
market_sentiment_class = {
    "class": "MarketSentiment",
    "description": "Market sentiment analysis from news and social media",
    "properties": [
        {
            "name": "symbol",
            "dataType": ["string"],
            "description": "Trading instrument symbol"
        },
        {
            "name": "sentiment_score",
            "dataType": ["number"],
            "description": "Sentiment score from -1 to 1"
        },
        {
            "name": "news_summary",
            "dataType": ["text"],
            "description": "Summary of relevant news"
        },
        {
            "name": "timestamp",
            "dataType": ["date"],
            "description": "Analysis timestamp"
        },
        {
            "name": "confidence",
            "dataType": ["number"],
            "description": "Analysis confidence level"
        }
    ],
    "vectorizer": "text2vec-openai",
    "moduleConfig": {
        "text2vec-openai": {
            "model": "ada-002",
            "dimensions": 1536
        }
    }
}

# Technical pattern class
technical_pattern_class = {
    "class": "TechnicalPattern",
    "description": "Technical analysis patterns detected in price data",
    "properties": [
        {
            "name": "pattern_name",
            "dataType": ["string"],
            "description": "Name of the detected pattern"
        },
        {
            "name": "symbol",
            "dataType": ["string"],
            "description": "Trading instrument symbol"
        },
        {
            "name": "timeframe",
            "dataType": ["string"],
            "description": "Chart timeframe"
        },
        {
            "name": "confidence_score",
            "dataType": ["number"],
            "description": "Pattern confidence score"
        },
        {
            "name": "price_levels",
            "dataType": ["number[]"],
            "description": "Key price levels of the pattern"
        }
    ],
    "vectorizer": "text2vec-openai"
}
```

### 5. DragonflyDB Cache Patterns (7 patterns)

```python
# Cache schema patterns
CACHE_PATTERNS = {
    # Real-time tick cache
    "tick_cache": {
        "pattern": "tick:{symbol}:{broker}",
        "ttl": 30,  # 30 seconds
        "data_structure": "hash",
        "fields": ["timestamp", "bid", "ask", "last", "volume", "spread"]
    },
    
    # Indicator cache
    "indicator_cache": {
        "pattern": "indicator:{symbol}:{timeframe}:{type}",
        "ttl": 300,  # 5 minutes
        "data_structure": "string",
        "compression": "gzip"
    },
    
    # ML predictions cache
    "ml_predictions_cache": {
        "pattern": "ml_pred:{model_id}:{symbol}:{timestamp}",
        "ttl": 600,  # 10 minutes
        "data_structure": "hash",
        "fields": ["prediction", "confidence", "features"]
    },
    
    # User session cache
    "session_cache": {
        "pattern": "session:{user_id}:{session_token}",
        "ttl": 3600,  # 1 hour
        "data_structure": "hash",
        "fields": ["user_data", "permissions", "last_activity"]
    },
    
    # Query result cache
    "query_result_cache": {
        "pattern": "query:{hash}",
        "ttl": 900,  # 15 minutes
        "data_structure": "string",
        "compression": "lz4"
    },
    
    # API response cache
    "api_response_cache": {
        "pattern": "api:{endpoint}:{params_hash}",
        "ttl": 60,  # 1 minute
        "data_structure": "string",
        "compression": "gzip"
    },
    
    # Rate limiting cache
    "rate_limit_cache": {
        "pattern": "rate_limit:{api_key}:{minute}",
        "ttl": 60,  # 1 minute
        "data_structure": "counter"
    }
}
```

### 6. Redpanda Streaming Topics (5 topics)

```python
# Streaming topic configurations
STREAMING_TOPICS = {
    # MT5 tick stream
    "mt5_tick_stream": {
        "partitions": 12,
        "replication_factor": 3,
        "retention_ms": 86400000,  # 24 hours
        "compression_type": "snappy",
        "schema": {
            "timestamp": "datetime",
            "symbol": "string",
            "bid": "float",
            "ask": "float",
            "last": "float",
            "volume": "int64",
            "broker": "string"
        }
    },
    
    # Trading signals
    "trading_signals": {
        "partitions": 6,
        "replication_factor": 3,
        "retention_ms": 604800000,  # 7 days
        "compression_type": "gzip",
        "schema": {
            "signal_id": "string",
            "symbol": "string",
            "signal_type": "enum[BUY,SELL,HOLD]",
            "confidence": "float",
            "strategy_id": "string",
            "timestamp": "datetime"
        }
    },
    
    # Market events
    "market_events": {
        "partitions": 4,
        "replication_factor": 3,
        "retention_ms": 259200000,  # 3 days
        "compression_type": "lz4",
        "schema": {
            "event_type": "string",
            "symbol": "string",
            "severity": "enum[LOW,MEDIUM,HIGH,CRITICAL]",
            "message": "string",
            "timestamp": "datetime"
        }
    },
    
    # System alerts
    "alerts_notifications": {
        "partitions": 2,
        "replication_factor": 3,
        "retention_ms": 604800000,  # 7 days
        "compression_type": "gzip",
        "schema": {
            "alert_id": "string",
            "alert_type": "string",
            "severity": "enum[INFO,WARNING,ERROR,CRITICAL]",
            "message": "string",
            "user_id": "string",
            "timestamp": "datetime"
        }
    },
    
    # System monitoring
    "system_monitoring": {
        "partitions": 3,
        "replication_factor": 3,
        "retention_ms": 172800000,  # 2 days
        "compression_type": "snappy",
        "schema": {
            "service_name": "string",
            "metric_name": "string",
            "metric_value": "float",
            "tags": "map[string,string]",
            "timestamp": "datetime"
        }
    }
}
```

## Schema Migration Management

### Migration Version Control
```python
class SchemaMigrationManager:
    """Manages database schema versions and migrations"""
    
    def __init__(self):
        self.current_versions = {
            "clickhouse": "2.1.0",
            "postgresql": "1.3.0", 
            "arangodb": "1.2.0",
            "weaviate": "1.1.0",
            "dragonflydb": "1.0.0",
            "redpanda": "1.0.0"
        }
        
    async def apply_migration(self, database: str, target_version: str):
        """Apply schema migration to target version"""
        current = self.current_versions[database]
        
        if current >= target_version:
            return {"status": "no_migration_needed", "current": current}
        
        migration_path = self._get_migration_path(database, current, target_version)
        
        results = []
        for migration in migration_path:
            result = await self._execute_migration(database, migration)
            results.append(result)
            
            if not result["success"]:
                # Rollback previous migrations
                await self._rollback_migrations(database, results[:-1])
                return {"status": "failed", "error": result["error"]}
        
        self.current_versions[database] = target_version
        return {"status": "success", "applied_migrations": len(results)}
    
    async def _execute_migration(self, database: str, migration: dict):
        """Execute individual migration"""
        try:
            if database == "clickhouse":
                return await self._execute_clickhouse_migration(migration)
            elif database == "postgresql":
                return await self._execute_postgresql_migration(migration)
            # ... other databases
        except Exception as e:
            return {"success": False, "error": str(e)}
```

### Schema Validation
```python
class SchemaValidator:
    """Validates schema integrity and consistency"""
    
    async def validate_all_schemas(self):
        """Validate all database schemas"""
        validation_results = {}
        
        # Validate each database
        for database in ["clickhouse", "postgresql", "arangodb", "weaviate"]:
            validation_results[database] = await self._validate_database_schema(database)
        
        return {
            "overall_status": all(r["valid"] for r in validation_results.values()),
            "results": validation_results
        }
    
    async def _validate_clickhouse_schema(self):
        """Validate ClickHouse schema structure"""
        errors = []
        warnings = []
        
        # Check required tables exist
        required_tables = ["ticks", "account_info", "positions", "sma_20", "ema_50", "rsi_14"]
        
        for table in required_tables:
            if not await self._table_exists("clickhouse", table):
                errors.append(f"Required table '{table}' does not exist")
        
        # Check table structures
        for table in required_tables:
            if await self._table_exists("clickhouse", table):
                structure_issues = await self._validate_table_structure("clickhouse", table)
                if structure_issues:
                    warnings.extend(structure_issues)
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
```

## Schema Documentation Files

### Individual Schema Documentation
- [ClickHouse Schemas](./CLICKHOUSE_SCHEMAS.md) - Complete ClickHouse table definitions
- [PostgreSQL Schemas](./POSTGRESQL_SCHEMAS.md) - PostgreSQL table structures  
- [ArangoDB Schemas](./ARANGODB_SCHEMAS.md) - Graph database collections
- [Weaviate Schemas](./WEAVIATE_SCHEMAS.md) - Vector database classes
- [Cache Schemas](./CACHE_SCHEMAS.md) - DragonflyDB cache patterns
- [Streaming Schemas](./STREAMING_SCHEMAS.md) - Redpanda topic configurations

### Migration Documentation
- [Migration Guide](../guides/MIGRATION.md) - Schema migration procedures
- [Version History](./VERSION_HISTORY.md) - Schema version changelog
- [Rollback Procedures](./ROLLBACK_PROCEDURES.md) - Schema rollback instructions

## Schema Statistics

### Storage Optimization
| Database | Tables | Estimated Size | Compression | Index Size |
|----------|--------|---------------|-------------|------------|
| ClickHouse | 98 | 2.8 TB | 75% | 280 GB |
| PostgreSQL | 8 | 50 GB | 25% | 12 GB |
| ArangoDB | 6 | 100 GB | 30% | 25 GB |
| Weaviate | 4 | 500 GB | 40% | 150 GB |

### Performance Metrics
| Database | Avg Query Time | Insert Throughput | Index Efficiency |
|----------|---------------|------------------|------------------|
| ClickHouse | 8.5ms | 65,000/sec | 95% |
| PostgreSQL | 15ms | 5,000/sec | 90% |
| ArangoDB | 25ms | 2,000/sec | 85% |
| Weaviate | 45ms | 1,000/sec | 80% |

---

**Schema Version**: 2.1.0  
**Last Updated**: 2025-07-31  
**Total Schemas**: 128 definitions across 6 databases  
**Status**: ✅ Production Ready