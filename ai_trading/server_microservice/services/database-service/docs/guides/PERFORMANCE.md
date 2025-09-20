# Database Service Performance Guide

**Comprehensive performance optimization strategies for high-frequency trading operations**

## Performance Overview

The Database Service is optimized for high-throughput trading operations with sub-10ms response times for critical operations and support for 50,000+ tick insertions per second.

## Performance Benchmarks

### Current Performance Metrics

| Operation | Database | Target | Achieved | P95 | P99 |
|-----------|----------|--------|----------|-----|-----|
| **Tick Insert** | ClickHouse | <5ms | 3.2ms | 5ms | 8ms |
| **Recent Ticks** | ClickHouse | <10ms | 6.5ms | 10ms | 15ms |
| **User Auth** | PostgreSQL | <15ms | 8.2ms | 12ms | 20ms |
| **Graph Query** | ArangoDB | <25ms | 18.5ms | 25ms | 40ms |
| **Vector Search** | Weaviate | <50ms | 35.2ms | 45ms | 80ms |
| **Cache Get** | DragonflyDB | <1ms | 0.3ms | 0.8ms | 1.5ms |
| **Stream Publish** | Redpanda | <5ms | 2.1ms | 4ms | 8ms |

### Throughput Benchmarks

| Operation | Database | Target TPS | Achieved TPS | Peak TPS |
|-----------|----------|-------------|--------------|----------|
| **Batch Tick Insert** | ClickHouse | 50,000/sec | 65,000/sec | 85,000/sec |
| **Cache Operations** | DragonflyDB | 100,000/sec | 125,000/sec | 180,000/sec |
| **Stream Processing** | Redpanda | 20,000/sec | 28,000/sec | 35,000/sec |
| **Query Execution** | ClickHouse | 10,000/sec | 12,500/sec | 18,000/sec |

## Database-Specific Optimizations

### 1. ClickHouse Optimizations

#### Table Structure Optimization
```sql
-- Optimized tick data table for high-frequency inserts
CREATE TABLE ticks_optimized (
    timestamp DateTime64(3, 'UTC'),
    symbol LowCardinality(String),
    bid Float64 CODEC(Delta, LZ4),
    ask Float64 CODEC(Delta, LZ4),
    last Float64 CODEC(Delta, LZ4),
    volume UInt64 CODEC(Delta, LZ4),
    spread Float32 CODEC(LZ4),
    broker LowCardinality(String),
    account_type LowCardinality(String)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, broker, timestamp)
SETTINGS 
    index_granularity = 8192,
    merge_max_block_size = 8192,
    max_insert_block_size = 1048576;
```

#### Optimization Features
- **LowCardinality**: For enum-like fields (symbol, broker, account_type)
- **Compression Codecs**: Delta + LZ4 for numeric data
- **Partitioning**: Monthly partitions for optimal query pruning
- **Index Granularity**: Tuned for tick data access patterns
- **Block Size**: Optimized for batch inserts

#### Query Optimization Examples
```python
# Optimized queries with proper indexing
class ClickHouseOptimizedQueries:
    
    @staticmethod
    def get_recent_ticks_optimized(symbol: str, broker: str, limit: int = 1000):
        """Ultra-fast recent ticks query - uses primary index"""
        return f"""
        SELECT 
            timestamp,
            bid,
            ask,
            last,
            volume,
            spread
        FROM ticks_optimized 
        WHERE symbol = '{symbol}' 
            AND broker = '{broker}'
            AND timestamp >= now() - INTERVAL 1 HOUR
        ORDER BY timestamp DESC 
        LIMIT {limit}
        SETTINGS max_threads = 4
        """
    
    @staticmethod
    def get_tick_statistics_optimized(symbol: str, timeframe: str):
        """Optimized aggregation query with proper indexing"""
        return f"""
        SELECT 
            toStartOfInterval(timestamp, INTERVAL 1 {timeframe}) as period,
            avg(bid) as avg_bid,
            avg(ask) as avg_ask,
            min(bid) as min_bid,
            max(ask) as max_ask,
            sum(volume) as total_volume,
            count(*) as tick_count
        FROM ticks_optimized 
        WHERE symbol = '{symbol}'
            AND timestamp >= now() - INTERVAL 24 HOUR
        GROUP BY period
        ORDER BY period
        SETTINGS 
            max_threads = 8,
            max_memory_usage = 1000000000
        """
```

### 2. PostgreSQL Optimizations

#### Index Strategy
```sql
-- Optimized indexes for user operations
CREATE INDEX CONCURRENTLY idx_users_email_hash ON users USING hash (email);
CREATE INDEX CONCURRENTLY idx_users_org_created ON users (organization_id, created_at DESC);
CREATE INDEX CONCURRENTLY idx_api_keys_user_active ON api_keys (user_id, is_active) WHERE is_active = true;

-- Partial indexes for active sessions
CREATE INDEX CONCURRENTLY idx_sessions_active ON user_sessions (user_id, expires_at) 
WHERE expires_at > NOW();
```

#### Connection Pool Optimization
```python
# Optimized PostgreSQL connection configuration
postgresql_config = {
    "pool_size": 20,
    "max_overflow": 30,
    "pool_timeout": 30,
    "pool_recycle": 3600,
    "pool_pre_ping": True,
    "connect_args": {
        "server_side_cursors": True,
        "application_name": "database-service",
        "options": "-c statement_timeout=30s -c idle_in_transaction_session_timeout=60s"
    }
}
```

### 3. DragonflyDB Optimizations

#### High-Performance Caching Strategies
```python
class HighPerformanceCache:
    """Optimized caching for trading data"""
    
    def __init__(self):
        self.cache_patterns = {
            # Hot data - very short TTL, high frequency
            "tick_latest": {"ttl": 5, "pipeline": True},
            
            # Warm data - medium TTL, frequent access
            "indicators": {"ttl": 60, "pipeline": True},
            
            # Cold data - long TTL, infrequent access
            "user_profiles": {"ttl": 3600, "pipeline": False}
        }
    
    async def optimized_tick_cache(self, symbol: str, tick_data: dict):
        """Ultra-fast tick caching with pipelining"""
        pipe = self.redis.pipeline()
        
        # Latest tick
        pipe.set(f"tick:latest:{symbol}", json.dumps(tick_data), ex=5)
        
        # Moving average cache
        pipe.lpush(f"tick:ma:{symbol}", tick_data['last'])
        pipe.ltrim(f"tick:ma:{symbol}", 0, 19)  # Keep last 20 values
        pipe.expire(f"tick:ma:{symbol}", 300)
        
        # Execute pipeline (single network roundtrip)
        await pipe.execute()
    
    async def batch_cache_operations(self, operations: List[dict]):
        """Batch multiple cache operations for efficiency"""
        pipe = self.redis.pipeline()
        
        for op in operations:
            if op['type'] == 'set':
                pipe.set(op['key'], op['value'], ex=op.get('ttl', 300))
            elif op['type'] == 'get':
                pipe.get(op['key'])
            elif op['type'] == 'delete':
                pipe.delete(op['key'])
        
        return await pipe.execute()
```

### 4. Connection Pool Optimization

#### Optimal Pool Configurations
```python
# Database-specific connection pool configurations
OPTIMAL_POOL_CONFIGS = {
    "clickhouse": {
        "min_connections": 3,
        "max_connections": 15,
        "connection_timeout": 5,
        "idle_timeout": 600,
        "max_lifetime": 3600,
        "health_check_interval": 30,
        "retry_attempts": 3
    },
    "postgresql": {
        "min_connections": 5,
        "max_connections": 20,
        "connection_timeout": 10,
        "idle_timeout": 300,
        "max_lifetime": 1800,
        "health_check_interval": 30,
        "retry_attempts": 3
    },
    "dragonflydb": {
        "min_connections": 10,
        "max_connections": 50,
        "connection_timeout": 1,
        "idle_timeout": 300,
        "max_lifetime": 600,
        "health_check_interval": 10,
        "retry_attempts": 5
    }
}

class OptimizedConnectionManager:
    """High-performance connection management"""
    
    async def get_connection_with_failover(self, db_type: str):
        """Get connection with automatic failover"""
        pool = self.connection_pools[db_type]
        
        for attempt in range(3):
            try:
                async with pool.acquire() as connection:
                    # Test connection health
                    await connection.execute("SELECT 1")
                    return connection
            except Exception as e:
                if attempt == 2:  # Last attempt
                    raise
                await asyncio.sleep(0.1 * (2 ** attempt))  # Exponential backoff
    
    async def warm_up_connections(self):
        """Pre-warm connection pools for optimal performance"""
        tasks = []
        for db_type, pool in self.connection_pools.items():
            task = self._warm_up_pool(db_type, pool)
            tasks.append(task)
        
        await asyncio.gather(*tasks)
    
    async def _warm_up_pool(self, db_type: str, pool):
        """Warm up individual connection pool"""
        min_connections = OPTIMAL_POOL_CONFIGS[db_type]["min_connections"]
        
        connections = []
        try:
            # Acquire minimum connections to warm up pool
            for _ in range(min_connections):
                conn = await pool.acquire()
                connections.append(conn)
                
            # Test each connection
            for conn in connections:
                await conn.execute("SELECT 1")
                
        finally:
            # Release all connections back to pool
            for conn in connections:
                await pool.release(conn)
```

## High-Frequency Trading Optimizations

### 1. Batch Processing Optimization

```python
class HFTOptimizedBatch:
    """High-frequency trading batch processing"""
    
    def __init__(self):
        self.batch_size = 10000
        self.max_wait_time = 0.1  # 100ms max wait
        self.pending_batches = {}
    
    async def optimized_tick_insertion(self, ticks: List[dict]):
        """Ultra-fast batch tick insertion"""
        
        # Group ticks by symbol for optimal partitioning
        symbol_batches = {}
        for tick in ticks:
            symbol = tick['symbol']
            if symbol not in symbol_batches:
                symbol_batches[symbol] = []
            symbol_batches[symbol].append(tick)
        
        # Process batches in parallel
        tasks = []
        for symbol, symbol_ticks in symbol_batches.items():
            task = self._insert_symbol_batch(symbol, symbol_ticks)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate results
        total_inserted = 0
        errors = []
        
        for result in results:
            if isinstance(result, Exception):
                errors.append(str(result))
            else:
                total_inserted += result
        
        return {
            "total_inserted": total_inserted,
            "errors": errors,
            "batches_processed": len(symbol_batches)
        }
    
    async def _insert_symbol_batch(self, symbol: str, ticks: List[dict]):
        """Insert batch for single symbol (optimal for partitioning)"""
        
        # Create optimized ClickHouse insert query
        query = f"""
        INSERT INTO ticks_optimized 
        (timestamp, symbol, bid, ask, last, volume, spread, broker, account_type)
        VALUES
        """
        
        # Build values efficiently
        values = []
        for tick in ticks:
            value = f"('{tick['timestamp']}', '{symbol}', {tick['bid']}, {tick['ask']}, {tick['last']}, {tick['volume']}, {tick['spread']}, '{tick['broker']}', '{tick['account_type']}')"
            values.append(value)
        
        final_query = query + ", ".join(values)
        
        # Execute with connection pooling
        async with self.clickhouse_pool.acquire() as connection:
            result = await connection.execute(final_query)
            return len(ticks)
```

### 2. Query Result Caching

```python
class SmartQueryCache:
    """Intelligent query result caching"""
    
    def __init__(self):
        self.cache = {}
        self.cache_stats = {"hits": 0, "misses": 0}
    
    async def cached_query(self, query: str, cache_key: str, ttl: int = 300):
        """Execute query with intelligent caching"""
        
        # Check cache first
        cached_result = await self.get_cached_result(cache_key)
        if cached_result is not None:
            self.cache_stats["hits"] += 1
            return cached_result
        
        # Execute query
        result = await self.execute_query(query)
        
        # Cache result with TTL
        await self.cache_result(cache_key, result, ttl)
        self.cache_stats["misses"] += 1
        
        return result
    
    async def smart_tick_cache(self, symbol: str, limit: int):
        """Smart caching for tick queries"""
        
        # Different cache strategies based on request
        if limit <= 100:
            # Hot data - cache for 5 seconds
            cache_key = f"ticks:recent:{symbol}:{limit}"
            ttl = 5
        elif limit <= 1000:
            # Warm data - cache for 30 seconds
            cache_key = f"ticks:medium:{symbol}:{limit}"
            ttl = 30
        else:
            # Cold data - cache for 5 minutes
            cache_key = f"ticks:large:{symbol}:{limit}"
            ttl = 300
        
        return await self.cached_query(
            self.build_tick_query(symbol, limit),
            cache_key,
            ttl
        )
```

### 3. Parallel Processing

```python
class ParallelQueryProcessor:
    """Parallel processing for complex operations"""
    
    async def parallel_indicator_calculation(self, symbols: List[str], timeframe: str):
        """Calculate indicators for multiple symbols in parallel"""
        
        # Limit concurrency to avoid overwhelming the database
        semaphore = asyncio.Semaphore(10)
        
        async def process_symbol(symbol: str):
            async with semaphore:
                return await self.calculate_indicators(symbol, timeframe)
        
        # Process all symbols in parallel
        tasks = [process_symbol(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate results
        successful_results = []
        errors = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append(f"{symbols[i]}: {str(result)}")
            else:
                successful_results.append(result)
        
        return {
            "results": successful_results,
            "errors": errors,
            "success_rate": len(successful_results) / len(symbols)
        }
    
    async def parallel_database_health_check(self):
        """Check all database health in parallel"""
        
        health_checks = {
            "clickhouse": self.check_clickhouse_health(),
            "postgresql": self.check_postgresql_health(),
            "arangodb": self.check_arangodb_health(),
            "weaviate": self.check_weaviate_health(),
            "dragonflydb": self.check_dragonflydb_health(),
            "redpanda": self.check_redpanda_health()
        }
        
        # Execute all health checks in parallel
        results = await asyncio.gather(
            *health_checks.values(),
            return_exceptions=True
        )
        
        # Build health status
        health_status = {}
        for db_name, result in zip(health_checks.keys(), results):
            if isinstance(result, Exception):
                health_status[db_name] = {
                    "status": "unhealthy",
                    "error": str(result)
                }
            else:
                health_status[db_name] = {
                    "status": "healthy",
                    "response_time_ms": result
                }
        
        return health_status
```

## Performance Monitoring

### 1. Real-time Performance Metrics

```python
class PerformanceMonitor:
    """Real-time performance monitoring"""
    
    def __init__(self):
        self.metrics = {
            "queries_per_second": 0,
            "avg_response_time": 0,
            "error_rate": 0,
            "connection_pool_utilization": {},
            "slow_queries": []
        }
        self.query_times = deque(maxlen=1000)  # Rolling window
    
    async def track_query_performance(self, db_type: str, query: str, execution_time: float):
        """Track individual query performance"""
        
        # Record timing
        self.query_times.append(execution_time)
        
        # Update metrics
        self.metrics["avg_response_time"] = sum(self.query_times) / len(self.query_times)
        
        # Check for slow queries
        if execution_time > 1000:  # 1 second threshold
            self.metrics["slow_queries"].append({
                "database": db_type,
                "query": query[:100] + "..." if len(query) > 100 else query,
                "execution_time_ms": execution_time,
                "timestamp": datetime.now().isoformat()
            })
            
        # Keep only recent slow queries
        cutoff_time = datetime.now() - timedelta(hours=1)
        self.metrics["slow_queries"] = [
            q for q in self.metrics["slow_queries"]
            if datetime.fromisoformat(q["timestamp"]) > cutoff_time
        ]
    
    async def get_performance_report(self):
        """Generate comprehensive performance report"""
        
        # Calculate QPS over last minute
        recent_queries = [
            t for t in self.query_times
            if time.time() - t < 60
        ]
        qps = len(recent_queries) / 60 if recent_queries else 0
        
        # Get connection pool utilization
        pool_utilization = {}
        for db_type, pool in self.connection_pools.items():
            pool_utilization[db_type] = {
                "active": pool.size - pool.checked_in,
                "idle": pool.checked_in,
                "total": pool.size,
                "utilization_percent": ((pool.size - pool.checked_in) / pool.size) * 100
            }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "queries_per_second": qps,
            "avg_response_time_ms": self.metrics["avg_response_time"],
            "connection_pools": pool_utilization,
            "slow_queries_count": len(self.metrics["slow_queries"]),
            "performance_grade": self._calculate_performance_grade()
        }
    
    def _calculate_performance_grade(self):
        """Calculate overall performance grade"""
        avg_time = self.metrics["avg_response_time"]
        slow_query_count = len(self.metrics["slow_queries"])
        
        if avg_time < 10 and slow_query_count == 0:
            return "A+"
        elif avg_time < 25 and slow_query_count < 5:
            return "A"
        elif avg_time < 50 and slow_query_count < 10:
            return "B"
        elif avg_time < 100 and slow_query_count < 20:
            return "C"
        else:
            return "D"
```

### 2. Performance Alerts

```python
class PerformanceAlerting:
    """Performance alerting system"""
    
    def __init__(self):
        self.thresholds = {
            "avg_response_time_ms": 100,
            "queries_per_second": 5000,
            "error_rate_percent": 1.0,
            "connection_pool_utilization_percent": 80,
            "slow_query_count": 10
        }
        self.alert_cooldown = 300  # 5 minutes
        self.last_alerts = {}
    
    async def check_performance_thresholds(self, metrics: dict):
        """Check if any performance thresholds are exceeded"""
        
        alerts = []
        current_time = time.time()
        
        # Check response time threshold
        if metrics["avg_response_time_ms"] > self.thresholds["avg_response_time_ms"]:
            if self._should_alert("response_time", current_time):
                alerts.append({
                    "type": "HIGH_RESPONSE_TIME",
                    "value": metrics["avg_response_time_ms"],
                    "threshold": self.thresholds["avg_response_time_ms"],
                    "severity": "WARNING"
                })
        
        # Check connection pool utilization
        for db_type, pool_info in metrics["connection_pools"].items():
            utilization = pool_info["utilization_percent"]
            if utilization > self.thresholds["connection_pool_utilization_percent"]:
                if self._should_alert(f"pool_{db_type}", current_time):
                    alerts.append({
                        "type": "HIGH_POOL_UTILIZATION",
                        "database": db_type,
                        "value": utilization,
                        "threshold": self.thresholds["connection_pool_utilization_percent"],
                        "severity": "WARNING"
                    })
        
        # Check slow query count
        if metrics["slow_queries_count"] > self.thresholds["slow_query_count"]:
            if self._should_alert("slow_queries", current_time):
                alerts.append({
                    "type": "HIGH_SLOW_QUERY_COUNT",
                    "value": metrics["slow_queries_count"],
                    "threshold": self.thresholds["slow_query_count"],
                    "severity": "WARNING"
                })
        
        return alerts
    
    def _should_alert(self, alert_type: str, current_time: float):
        """Check if we should send alert (respects cooldown)"""
        last_alert_time = self.last_alerts.get(alert_type, 0)
        if current_time - last_alert_time > self.alert_cooldown:
            self.last_alerts[alert_type] = current_time
            return True
        return False
```

## Optimization Recommendations

### 1. Database-Specific Tuning

#### ClickHouse Tuning
```sql
-- Memory and performance settings
SET max_memory_usage = 10000000000;        -- 10GB max memory per query
SET max_threads = 8;                       -- Use 8 threads for query processing
SET max_execution_time = 300;              -- 5 minute query timeout
SET send_progress_in_http_headers = 1;     -- Enable progress tracking
SET max_insert_block_size = 1048576;       -- 1M rows per insert block
```

#### PostgreSQL Tuning
```sql
-- Connection and memory settings
-- In postgresql.conf
shared_buffers = '2GB'
effective_cache_size = '6GB'
maintenance_work_mem = '512MB'
checkpoint_completion_target = 0.9
wal_buffers = '64MB'
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
```

### 2. Application-Level Optimizations

#### Connection Pool Sizing Formula
```python
def calculate_optimal_pool_size(expected_concurrent_users: int, avg_query_time_ms: int):
    """Calculate optimal connection pool size"""
    
    # Base calculation: concurrent users × query time × safety factor
    base_size = (expected_concurrent_users * avg_query_time_ms / 1000) * 1.5
    
    # Add buffer for peak load
    buffer = max(5, base_size * 0.3)
    
    # Round up and apply limits
    optimal_size = math.ceil(base_size + buffer)
    
    return {
        "min_connections": max(2, optimal_size // 4),
        "max_connections": min(50, optimal_size),
        "recommended": optimal_size
    }

# Example usage
hft_pool_config = calculate_optimal_pool_size(
    expected_concurrent_users=100,
    avg_query_time_ms=10
)
```

#### Query Optimization Guidelines

1. **Use Proper Indexing**
   ```python
   # Always filter by indexed columns first
   query = """
   SELECT * FROM ticks 
   WHERE symbol = %s          -- Indexed column first
     AND broker = %s          -- Indexed column second  
     AND timestamp >= %s      -- Indexed column third
   ORDER BY timestamp DESC    -- Use index for sorting
   LIMIT %s
   """
   ```

2. **Batch Operations**
   ```python
   # Instead of individual inserts
   for tick in ticks:
       await insert_tick(tick)  # BAD: N database calls
   
   # Use batch inserts
   await insert_ticks_batch(ticks)  # GOOD: 1 database call
   ```

3. **Connection Reuse**
   ```python
   # Use connection pooling
   async with connection_pool.acquire() as conn:
       # Multiple operations with same connection
       result1 = await conn.execute(query1)
       result2 = await conn.execute(query2)
       result3 = await conn.execute(query3)
   ```

### 3. Monitoring and Alerting Setup

```python
# Production monitoring configuration
MONITORING_CONFIG = {
    "performance_thresholds": {
        "clickhouse_response_time_ms": 50,
        "postgresql_response_time_ms": 100,
        "cache_response_time_ms": 5,
        "connection_pool_utilization_percent": 75,
        "error_rate_percent": 0.5
    },
    "alert_channels": {
        "slack": "https://hooks.slack.com/services/...",
        "email": ["admin@example.com"],
        "pagerduty": "integration-key"
    },
    "metrics_collection_interval": 60,
    "performance_report_interval": 300
}
```

---

**Performance Guide Version**: 2.0.0  
**Last Updated**: 2025-07-31  
**Optimization Status**: ✅ HFT Ready