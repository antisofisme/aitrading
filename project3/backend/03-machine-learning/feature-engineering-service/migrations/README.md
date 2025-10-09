# ClickHouse Database Migrations

## Migration Files

### 001_create_ml_training_data.sql
Creates the main `ml_training_data` table with 63 features + metadata + target variable.

**Features:**
- 63 ML features organized by importance (20% news → 2% moving averages)
- Partitioned by month for efficient querying
- Indexed by symbol, timeframe, timestamp
- Includes data quality metadata
- Materialized view for training statistics

## Running Migrations

### Method 1: Manual (via clickhouse-client)
```bash
# Connect to ClickHouse
docker exec -it suho-clickhouse clickhouse-client \
  --user suho_analytics \
  --password clickhouse_secure_2024 \
  --database suho_analytics

# Run migration
cat 001_create_ml_training_data.sql | docker exec -i suho-clickhouse \
  clickhouse-client \
  --user suho_analytics \
  --password clickhouse_secure_2024 \
  --database suho_analytics
```

### Method 2: Docker Volume Mount
```bash
# Copy migration to container
docker cp 001_create_ml_training_data.sql suho-clickhouse:/tmp/

# Execute
docker exec suho-clickhouse clickhouse-client \
  --user suho_analytics \
  --password clickhouse_secure_2024 \
  --database suho_analytics \
  --queries-file /tmp/001_create_ml_training_data.sql
```

### Method 3: HTTP Interface
```bash
# Using curl
curl -X POST "http://localhost:8123/?user=suho_analytics&password=clickhouse_secure_2024&database=suho_analytics" \
  --data-binary @001_create_ml_training_data.sql
```

## Verifying Installation

```sql
-- Check table exists
SHOW TABLES FROM suho_analytics LIKE 'ml_training_data';

-- Check table structure
DESCRIBE TABLE suho_analytics.ml_training_data;

-- Check materialized view
SHOW TABLES FROM suho_analytics LIKE 'ml_training_stats';

-- Verify permissions
SHOW GRANTS FOR suho_analytics;
```

## Table Statistics

```sql
-- Count total rows
SELECT count() FROM suho_analytics.ml_training_data;

-- Count by symbol and timeframe
SELECT symbol, timeframe, count() AS samples
FROM suho_analytics.ml_training_data
GROUP BY symbol, timeframe
ORDER BY samples DESC;

-- Check target distribution
SELECT
    target,
    count() AS count,
    count() / sum(count()) OVER () AS percentage
FROM suho_analytics.ml_training_data
GROUP BY target;

-- View training statistics
SELECT *
FROM suho_analytics.ml_training_stats
ORDER BY date DESC
LIMIT 10;
```

## Dropping Tables (Caution!)

```sql
-- Drop materialized view first
DROP VIEW IF EXISTS suho_analytics.ml_training_stats;

-- Drop main table
DROP TABLE IF EXISTS suho_analytics.ml_training_data;
```
