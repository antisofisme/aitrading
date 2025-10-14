# Database Schema Definitions - Python

Schema definitions for all databases using Python dictionaries. Update schema dengan edit file Python, SQL auto-generated!

## 🎯 Kenapa Python Schema?

### ✅ **Advantages:**

1. **Single Source of Truth** - 1 file untuk 1 database
2. **Type Safe** - Python type hints + IDE support
3. **Dynamic** - Bisa pakai logic, loops, conditionals
4. **Reusable** - Constants dan functions
5. **Version Control** - Git-friendly, easy diff
6. **Auto-Generate** - SQL/JSON otomatis di-generate

### ❌ **Dibanding SQL files:**

| Aspect | Python Schema | Raw SQL Files |
|--------|--------------|---------------|
| Update | Edit 1 dict | Edit SQL manually |
| Reuse | Functions/constants | Copy-paste |
| Validation | Python type hints | None |
| Generation | Auto-generate SQL | Write by hand |
| Versioning | Clear in code | Comments only |

---

## 📁 File Structure

```
schemas/
├── __init__.py                # Exports
├── README.md                  # This file
├── timescale_schema.py        # PostgreSQL + TimescaleDB
├── clickhouse_schema.py       # ClickHouse OLAP
├── dragonfly_schema.py        # Redis-compatible cache patterns
├── arangodb_schema.py         # Graph + Document
└── weaviate_schema.py         # Vector database
```

---

## 🚀 Quick Start

### 1. Import Schema

```python
from central_hub_sdk.schemas import (
    get_timescale_schemas,
    get_clickhouse_schemas,
    get_dragonfly_schemas,
)

# Get all TimescaleDB table schemas
timescale_schemas = get_timescale_schemas()

# Each schema is a Python dict
for schema in timescale_schemas:
    print(f"Table: {schema['name']}")
    print(f"Columns: {list(schema['columns'].keys())}")
```

### 2. Generate SQL

```python
from central_hub_sdk.schemas.timescale_schema import (
    get_all_timescale_sql,
    generate_full_schema_sql,
    MARKET_TICKS_SCHEMA
)

# Generate SQL for all tables
full_sql = get_all_timescale_sql()
print(full_sql)

# Generate SQL for single table
tick_sql = generate_full_schema_sql(MARKET_TICKS_SCHEMA)
print(tick_sql)
```

### 3. Use in Database Manager

```python
from central_hub_sdk.schemas.timescale_schema import get_all_timescale_sql

# In TimescaleDB manager
async def initialize_schema(self):
    sql = get_all_timescale_sql()
    await self.client.execute(sql)
```

---

## 📝 Schema Structure

### TimescaleDB (PostgreSQL)

```python
TABLE_SCHEMA = {
    "name": "table_name",
    "description": "What this table stores",
    "version": "1.0",

    # TimescaleDB specific
    "hypertable": {
        "time_column": "time",
        "chunk_interval": "1 day"
    },

    # Columns
    "columns": {
        "time": "TIMESTAMPTZ NOT NULL",
        "symbol": "VARCHAR(20) NOT NULL",
        "price": "DECIMAL(18, 5)",
    },

    # Primary key
    "primary_key": ["time", "symbol"],

    # Indexes
    "indexes": [
        {
            "name": "idx_symbol",
            "columns": ["symbol", "time DESC"],
            "method": "BTREE"
        }
    ],
}
```

### ClickHouse (OLAP)

```python
TABLE_SCHEMA = {
    "name": "table_name",
    "description": "Analytics table",
    "version": "1.0",

    # ClickHouse specific
    "engine": "MergeTree",
    "partition_by": "(symbol, toYYYYMM(timestamp))",
    "order_by": "(symbol, timestamp)",
    "ttl": "toDateTime(timestamp) + INTERVAL 90 DAY",

    # Columns
    "columns": {
        "symbol": "String",
        "timestamp": "DateTime64(3, 'UTC')",
        "price": "Decimal(18, 5)",
    },

    # Settings
    "settings": {
        "index_granularity": 8192
    }
}
```

### DragonflyDB (Cache Patterns)

```python
CACHE_PATTERN = {
    "pattern": "key:pattern:{placeholder}",
    "description": "What this cache stores",
    "ttl": 60,  # seconds
    "type": "hash",  # hash, list, string, set

    # Data structure
    "fields": {
        "field1": "string",
        "field2": "int",
        "field3": "float",
    },

    # Example data
    "example": {
        "key": "tick:latest:EURUSD",
        "value": {"field1": "val", ...}
    }
}
```

### ArangoDB (Graph)

```python
COLLECTION_SCHEMA = {
    "name": "collection_name",
    "type": "document",  # or "edge"
    "description": "What this stores",

    "schema": {
        "field1": "string",
        "field2": "number",
    },

    "indexes": [...]
}

GRAPH_SCHEMA = {
    "name": "graph_name",
    "edge_definitions": [
        {
            "edge_collection": "edge_name",
            "from_vertex_collections": ["coll1"],
            "to_vertex_collections": ["coll2"]
        }
    ]
}
```

### Weaviate (Vector)

```python
CLASS_SCHEMA = {
    "class": "ClassName",
    "description": "Vector class description",
    "vectorizer": "text2vec-transformers",

    "properties": [
        {
            "name": "field1",
            "dataType": ["string"],
            "description": "Field description",
            "indexFilterable": True
        }
    ]
}
```

---

## 🔧 How to Add/Update Schema

### Add New Table (TimescaleDB)

**1. Define schema in `timescale_schema.py`:**

```python
NEW_TABLE_SCHEMA = {
    "name": "my_new_table",
    "description": "My new table description",
    "version": "1.0",
    "hypertable": {
        "time_column": "timestamp",
        "chunk_interval": "1 day"
    },
    "columns": {
        "timestamp": "TIMESTAMPTZ NOT NULL",
        "data": "JSONB",
    },
    "primary_key": ["timestamp"],
}
```

**2. Add to schema list:**

```python
def get_timescale_schemas() -> List[Dict[str, Any]]:
    return [
        MARKET_TICKS_SCHEMA,
        MARKET_CANDLES_SCHEMA,
        NEW_TABLE_SCHEMA,  # ← Add here
    ]
```

**3. That's it!** SQL auto-generated on next deployment.

### Modify Existing Table

**Before:**
```python
"columns": {
    "time": "TIMESTAMPTZ NOT NULL",
    "symbol": "VARCHAR(20) NOT NULL",
}
```

**After:**
```python
"columns": {
    "time": "TIMESTAMPTZ NOT NULL",
    "symbol": "VARCHAR(20) NOT NULL",
    "new_field": "DECIMAL(10, 5)",  # ← Added
}
```

**Note:** Untuk production, butuh migration script untuk ALTER TABLE.

---

## 🎯 Best Practices

### 1. Use Reusable Constants

```python
# Define once
COMMON_COLUMNS = {
    "timestamp_ms": "BIGINT NOT NULL",
    "ingested_at": "TIMESTAMPTZ DEFAULT NOW()",
}

# Reuse everywhere
TABLE1 = {
    "columns": {
        "id": "UUID",
        "timestamp_ms": COMMON_COLUMNS["timestamp_ms"],  # ← Reuse
        "ingested_at": COMMON_COLUMNS["ingested_at"],    # ← Reuse
    }
}
```

### 2. Add Clear Descriptions

```python
SCHEMA = {
    "name": "market_ticks",
    "description": "Real-time market tick data (bid/ask/mid/spread)",  # ← Clear!
    "version": "1.0",
    ...
}
```

### 3. Version Your Schemas

```python
SCHEMA_V1 = {...}
SCHEMA_V2 = {...}

# Use active version
ACTIVE_SCHEMA = SCHEMA_V2
```

### 4. Document with Comments

```python
"columns": {
    "price": "DECIMAL(18, 5)",  # 18 total digits, 5 after decimal
    "volume": "BIGINT DEFAULT 0",  # Tick volume (number of ticks)
}
```

---

## 🔄 Integration with Migrator

Schema Python ini otomatis dipakai oleh `SchemaMigrator`:

```python
from central_hub_sdk import DatabaseRouter, SchemaMigrator
from central_hub_sdk.schemas import get_timescale_schemas

router = DatabaseRouter(config)
await router.initialize()

# Migrator akan call get_timescale_schemas() automatically
migrator = SchemaMigrator(router, use_python_schemas=True)
await migrator.initialize_all_schemas()
```

---

## 📊 Example: Complete Workflow

### Step 1: Define New Table

```python
# In timescale_schema.py
MY_ANALYTICS_TABLE = {
    "name": "analytics_results",
    "description": "Computed analytics and metrics",
    "version": "1.0",
    "hypertable": {
        "time_column": "computed_at",
        "chunk_interval": "7 days"
    },
    "columns": {
        "computed_at": "TIMESTAMPTZ NOT NULL",
        "metric_name": "VARCHAR(50) NOT NULL",
        "metric_value": "DECIMAL(18, 5)",
        "metadata": "JSONB",
    },
    "primary_key": ["computed_at", "metric_name"],
}
```

### Step 2: Add to Schema List

```python
def get_timescale_schemas():
    return [
        MARKET_TICKS_SCHEMA,
        MARKET_CANDLES_SCHEMA,
        MY_ANALYTICS_TABLE,  # ← New
    ]
```

### Step 3: Test SQL Generation

```python
from central_hub_sdk.schemas.timescale_schema import generate_full_schema_sql

sql = generate_full_schema_sql(MY_ANALYTICS_TABLE)
print(sql)

# Output:
# CREATE TABLE IF NOT EXISTS analytics_results (...)
# SELECT create_hypertable('analytics_results', ...)
```

### Step 4: Deploy

```bash
# Rebuild services with updated SDK
docker compose build data-bridge tick-aggregator
docker compose restart data-bridge tick-aggregator

# Schema auto-created on service startup!
```

---

## 🐛 Troubleshooting

### Schema Not Applied

**Check:**
1. Schema added to `get_xxx_schemas()` function?
2. SDK rebuilt in Docker? (`docker compose build`)
3. Service restarted? (`docker compose restart`)

### SQL Syntax Error

**Check:**
1. Column types correct for database?
2. Reserved keywords escaped?
3. Generated SQL with `get_all_xxx_sql()` first

### Type Mismatch

**Fix:**
```python
# Wrong
"price": "DECIMAL",  # ❌ Missing precision

# Correct
"price": "DECIMAL(18, 5)",  # ✅ With precision
```

---

## 📚 References

- **TimescaleDB Types**: https://docs.timescale.com/api/latest/hypertable/
- **ClickHouse Types**: https://clickhouse.com/docs/en/sql-reference/data-types/
- **ArangoDB Schema**: https://www.arangodb.com/docs/stable/data-modeling.html
- **Weaviate Schema**: https://weaviate.io/developers/weaviate/manage-data/collections

---

**Version:** 2.0
**Last Updated:** 2025-10-14
**Status:** ✅ Production Ready
