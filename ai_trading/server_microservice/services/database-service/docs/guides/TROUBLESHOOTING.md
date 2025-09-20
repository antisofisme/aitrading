# Database Service Troubleshooting Guide

**Comprehensive troubleshooting guide for Database Service issues and diagnostics**

## Quick Diagnostics

### Health Check Commands
```bash
# Basic service health
curl http://localhost:8003/api/v1/database/health

# Detailed health check
curl http://localhost:8003/api/v1/database/health/detailed

# Individual database health
curl http://localhost:8003/api/v1/database/health/clickhouse
curl http://localhost:8003/api/v1/database/health/postgresql
curl http://localhost:8003/api/v1/database/health/arangodb
```

### Service Status Check
```bash
# Check if service is running
ps aux | grep database-service

# Check port availability
netstat -tulpn | grep :8003

# Check resource usage
top -p $(pgrep -f database-service)
```

## Common Issues and Solutions

### 1. Connection Issues

#### Issue: Database Connection Timeout
**Symptoms:**
- API returns `DATABASE_CONNECTION_ERROR`
- Long response times (>30 seconds)
- Connection pool exhaustion warnings

**Diagnosis:**
```bash
# Check database connectivity
telnet clickhouse-host 8123
telnet postgresql-host 5432
telnet arangodb-host 8529

# Check connection pool status
curl http://localhost:8003/api/v1/database/metrics/connections
```

**Solutions:**

1. **Increase Connection Timeout**
```bash
# Environment variables
export CLICKHOUSE_CONNECTION_TIMEOUT=15
export POSTGRESQL_CONNECTION_TIMEOUT=20
export ARANGODB_CONNECTION_TIMEOUT=15
```

2. **Adjust Connection Pool Size**
```bash
# Reduce max connections if overwhelmed
export CLICKHOUSE_MAX_CONNECTIONS=10
export POSTGRESQL_MAX_CONNECTIONS=15

# Increase if insufficient
export CLICKHOUSE_MAX_CONNECTIONS=25
export POSTGRESQL_MAX_CONNECTIONS=30
```

3. **Check Database Server Status**
```bash
# ClickHouse
curl -u default:password http://clickhouse-host:8123/ping

# PostgreSQL
pg_isready -h postgresql-host -p 5432

# ArangoDB
curl http://arangodb-host:8529/_api/version
```

#### Issue: SSL/TLS Connection Errors
**Symptoms:**
- Certificate verification errors
- SSL handshake failures
- Connection refused with SSL enabled

**Solutions:**

1. **Disable SSL for Development**
```bash
export CLICKHOUSE_SECURE=false
export CLICKHOUSE_VERIFY_SSL=false
export POSTGRESQL_SSL_MODE=disable
export ARANGODB_USE_SSL=false
```

2. **Fix SSL Configuration**
```bash
# For production - proper SSL setup
export CLICKHOUSE_SECURE=true
export CLICKHOUSE_VERIFY_SSL=true
export POSTGRESQL_SSL_MODE=require
export ARANGODB_USE_SSL=true

# Add certificate paths if needed
export SSL_CERT_PATH=/path/to/cert.pem
export SSL_KEY_PATH=/path/to/key.pem
export SSL_CA_CERT_PATH=/path/to/ca.pem
```

### 2. Performance Issues

#### Issue: High Query Response Times
**Symptoms:**
- P95 response times > 100ms
- Slow query alerts
- High CPU usage

**Diagnosis:**
```python
# Performance diagnostic script
import asyncio
import time
import httpx

async def diagnose_performance():
    """Diagnose performance issues"""
    
    # Test basic query performance
    start_time = time.time()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8003/api/v1/database/clickhouse/query",
            params={"query": "SELECT COUNT(*) FROM ticks", "database": "trading_data"}
        )
    
    response_time = (time.time() - start_time) * 1000
    print(f"Basic query response time: {response_time:.2f}ms")
    
    if response_time > 100:
        print("❌ Performance issue detected")
        
        # Check connection pool utilization
        pool_response = await client.get("http://localhost:8003/api/v1/database/metrics/connections")
        pool_data = pool_response.json()
        
        for db, stats in pool_data["connection_pools"].items():
            utilization = stats["utilization_percent"]
            if utilization > 80:
                print(f"⚠️  High pool utilization for {db}: {utilization}%")
    
    return response_time

# Run diagnosis
asyncio.run(diagnose_performance())
```

**Solutions:**

1. **Optimize Connection Pools**
```python
# Increase pool size for high-load databases
OPTIMIZED_POOL_CONFIG = {
    "clickhouse": {
        "min_connections": 5,
        "max_connections": 25,  # Increased from 15
        "connection_timeout": 3,  # Reduced from 5
        "idle_timeout": 300     # Reduced from 600
    },
    "postgresql": {
        "min_connections": 8,   # Increased from 5
        "max_connections": 30,  # Increased from 20
        "connection_timeout": 8, # Reduced from 10
        "idle_timeout": 300
    }
}
```

2. **Enable Query Caching**
```bash
# Enable aggressive caching
export QUERY_RESULT_CACHE_ENABLED=true
export QUERY_RESULT_CACHE_TTL=300
export CONNECTION_CACHE_ENABLED=true
```

3. **Database-Specific Optimizations**
```sql
-- ClickHouse query optimization
SET max_threads = 8;
SET max_memory_usage = 4000000000;  -- 4GB
SET use_uncompressed_cache = 1;

-- PostgreSQL optimization
SET work_mem = '256MB';
SET shared_buffers = '2GB';
SET effective_cache_size = '6GB';
```

#### Issue: Memory Usage High
**Symptoms:**
- Out of memory errors
- Service crashes
- Swap usage increasing

**Diagnosis:**
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head -20

# Check service memory usage
pmap -d $(pgrep -f database-service)

# Monitor memory over time
while true; do
    echo "$(date): $(ps -p $(pgrep -f database-service) -o rss=) KB"
    sleep 60
done
```

**Solutions:**

1. **Reduce Connection Pool Sizes**
```bash
export CLICKHOUSE_MAX_CONNECTIONS=10
export POSTGRESQL_MAX_CONNECTIONS=15
export ARANGODB_MAX_CONNECTIONS=8
```

2. **Limit Query Memory Usage**
```bash
export MAX_MEMORY_PER_QUERY_MB=512
export MAX_RESULT_SIZE_MB=100
export CONNECTION_POOL_MEMORY_MB=256
```

3. **Optimize Garbage Collection**
```python
# For Python applications
import gc
gc.set_threshold(700, 10, 10)  # More aggressive GC
```

### 3. Data Issues

#### Issue: Data Insertion Failures
**Symptoms:**
- Insert operations timing out
- Data validation errors
- Duplicate key violations

**Diagnosis:**
```python
# Test data insertion
async def diagnose_insertion():
    test_data = {
        "table": "ticks",
        "database": "trading_data",
        "data": [{
            "timestamp": "2025-07-31T10:30:00.000Z",
            "symbol": "EURUSD",
            "bid": 1.08505,
            "ask": 1.08507,
            "last": 1.08506,
            "volume": 1000000,
            "broker": "TEST-BROKER",
            "account_type": "demo"
        }]
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8003/api/v1/database/clickhouse/insert",
                json=test_data
            )
            
        if response.status_code != 200:
            print(f"❌ Insert failed: {response.status_code} - {response.text}")
        else:
            print("✅ Insert successful")
            
    except Exception as e:
        print(f"❌ Insert error: {e}")

asyncio.run(diagnose_insertion())
```

**Solutions:**

1. **Increase Batch Size and Timeouts**
```bash
export CLICKHOUSE_INSERT_BATCH_SIZE=5000  # Reduced from 10000
export CLICKHOUSE_QUERY_TIMEOUT=60000     # Increased to 60 seconds
export INSERT_RETRY_ATTEMPTS=3
```

2. **Validate Data Format**
```python
def validate_tick_data(tick_data):
    """Validate tick data before insertion"""
    required_fields = ["timestamp", "symbol", "bid", "ask", "last", "volume", "broker"]
    
    for field in required_fields:
        if field not in tick_data:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate data types
    if not isinstance(tick_data["bid"], (int, float)):
        raise ValueError("Bid must be numeric")
    
    if not isinstance(tick_data["volume"], int):
        raise ValueError("Volume must be integer")
    
    # Validate ranges
    if tick_data["bid"] <= 0:
        raise ValueError("Bid must be positive")
    
    return True
```

3. **Handle Duplicate Data**
```sql
-- ClickHouse: Use REPLACE syntax for deduplication
ALTER TABLE ticks 
ADD CONSTRAINT unique_tick UNIQUE (timestamp, symbol, broker);

-- Or use ReplacingMergeTree engine
CREATE TABLE ticks_deduplicated (
    -- same columns as ticks
) ENGINE = ReplacingMergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, broker, timestamp);
```

### 4. Authentication Issues

#### Issue: API Key Authentication Failures
**Symptoms:**
- 401 Unauthorized responses
- "Invalid API key" errors
- Authentication bypassed unexpectedly

**Diagnosis:**
```bash
# Test API key authentication
curl -H "X-API-Key: test-key" http://localhost:8003/api/v1/database/health

# Check API key in database
# PostgreSQL query to check API keys
curl -X POST http://localhost:8003/api/v1/database/postgresql/query \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT id, name, is_active FROM api_keys WHERE key_hash = $1", "params": ["hashed-key"]}'
```

**Solutions:**

1. **Verify API Key Configuration**
```bash
# Check if API key requirement is properly configured
export API_KEY_REQUIRED=true
export JWT_SECRET_KEY=your-secret-key

# For development, temporarily disable authentication
export API_KEY_REQUIRED=false  # Development only!
```

2. **Regenerate API Keys**
```python
import hashlib
import secrets

def generate_api_key():
    """Generate new API key"""
    key = secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    
    return {
        "key": key,
        "hash": key_hash
    }

# Generate new key
new_key = generate_api_key()
print(f"New API Key: {new_key['key']}")
print(f"Hash (store in DB): {new_key['hash']}")
```

3. **Debug Authentication Flow**
```python
# Add authentication debugging
import logging

logger = logging.getLogger("auth")
logger.setLevel(logging.DEBUG)

def debug_api_key_auth(api_key: str):
    """Debug API key authentication"""
    
    logger.debug(f"Received API key: {api_key[:8]}...")
    
    # Hash the key
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    logger.debug(f"Generated hash: {key_hash[:16]}...")
    
    # Check in database
    # ... database query logic
    
    logger.debug("Authentication result: SUCCESS/FAILURE")
```

### 5. Service Startup Issues

#### Issue: Service Won't Start
**Symptoms:**
- Service exits immediately
- Port binding errors
- Database initialization failures

**Diagnosis:**
```bash
# Check service logs
tail -f /var/log/database-service.log

# Run service in foreground for debugging
python main_refactored.py

# Check port conflicts
lsof -i :8003

# Check environment variables
env | grep -E "(CLICKHOUSE|POSTGRESQL|ARANGODB|WEAVIATE|DRAGONFLY|REDPANDA)"
```

**Solutions:**

1. **Fix Port Conflicts**
```bash
# Find process using port 8003
lsof -ti:8003 | xargs kill -9

# Or use different port
export SERVICE_PORT=8004
```

2. **Fix Environment Variables**
```bash
# Create comprehensive .env file
cat > .env << EOF
# Service Configuration
SERVICE_NAME=database-service
SERVICE_PORT=8003
SERVICE_HOST=0.0.0.0

# Database Hosts
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
POSTGRESQL_HOST=localhost
POSTGRESQL_PORT=5432
ARANGODB_HOST=localhost
ARANGODB_PORT=8529
WEAVIATE_HOST=localhost
WEAVIATE_PORT=8080
DRAGONFLYDB_HOST=localhost
DRAGONFLYDB_PORT=6379
REDPANDA_BOOTSTRAP_SERVERS=localhost:9092

# Authentication
API_KEY_REQUIRED=false  # For debugging
EOF

# Load environment
source .env
```

3. **Database Connectivity Check**
```python
# Startup connectivity checker
import asyncio
import aiohttp

async def check_all_databases():
    """Check connectivity to all databases"""
    
    checks = {
        "clickhouse": check_clickhouse_connectivity(),
        "postgresql": check_postgresql_connectivity(),
        "arangodb": check_arangodb_connectivity(),
        "weaviate": check_weaviate_connectivity(),
        "dragonflydb": check_dragonflydb_connectivity()
    }
    
    results = await asyncio.gather(*checks.values(), return_exceptions=True)
    
    for db_name, result in zip(checks.keys(), results):
        if isinstance(result, Exception):
            print(f"❌ {db_name}: {result}")
        else:
            print(f"✅ {db_name}: Connected")

asyncio.run(check_all_databases())
```

## Error Code Reference

### Database Error Codes

| Error Code | Description | Common Causes | Solution |
|------------|-------------|---------------|----------|
| `DB_CONNECTION_TIMEOUT` | Connection timeout | Network issues, database overload | Increase timeout, check network |
| `DB_QUERY_TIMEOUT` | Query execution timeout | Complex query, database load | Optimize query, increase timeout |
| `DB_AUTHENTICATION_FAILED` | Database auth failed | Wrong credentials | Check username/password |
| `DB_PERMISSION_DENIED` | Insufficient permissions | User lacks permissions | Grant proper database permissions |
| `DB_TABLE_NOT_EXISTS` | Table doesn't exist | Missing schema migration | Run schema migration |
| `DB_CONSTRAINT_VIOLATION` | Data constraint violation | Invalid data, duplicates | Validate data before insert |

### Service Error Codes

| Error Code | Description | Common Causes | Solution |
|------------|-------------|---------------|----------|
| `SERVICE_STARTUP_FAILED` | Service startup failure | Config errors, port conflicts | Check config, kill conflicting processes |
| `CONNECTION_POOL_EXHAUSTED` | No available connections | High load, small pool | Increase pool size, reduce load |
| `RATE_LIMIT_EXCEEDED` | Too many requests | Client exceeding limits | Implement backoff, increase limits |
| `INVALID_API_KEY` | Authentication failed | Wrong/expired API key | Generate new API key |
| `CONFIGURATION_ERROR` | Invalid configuration | Missing/wrong config values | Validate configuration |

## Monitoring and Alerting

### Setting Up Monitoring
```python
# Performance monitoring script
import time
import asyncio
import httpx
from datetime import datetime

class DatabaseServiceMonitor:
    def __init__(self):
        self.base_url = "http://localhost:8003"
        self.alert_thresholds = {
            "response_time_ms": 100,
            "error_rate_percent": 1.0,
            "connection_utilization_percent": 80
        }
    
    async def monitor_performance(self):
        """Continuous performance monitoring"""
        while True:
            try:
                # Check health
                health_status = await self.check_health()
                
                # Check performance metrics
                metrics = await self.get_metrics()
                
                # Check for alerts
                alerts = self.check_alerts(metrics)
                
                if alerts:
                    await self.send_alerts(alerts)
                
                # Log status
                print(f"{datetime.now()}: Health={health_status}, Metrics={metrics}")
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                print(f"Monitoring error: {e}")
                await asyncio.sleep(10)
    
    async def check_health(self):
        """Check service health"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/v1/database/health")
                return response.status_code == 200
        except:
            return False
    
    def check_alerts(self, metrics):
        """Check for alert conditions"""
        alerts = []
        
        if metrics.get("avg_response_time_ms", 0) > self.alert_thresholds["response_time_ms"]:
            alerts.append({
                "type": "HIGH_RESPONSE_TIME",
                "value": metrics["avg_response_time_ms"],
                "threshold": self.alert_thresholds["response_time_ms"]
            })
        
        return alerts

# Run monitoring
monitor = DatabaseServiceMonitor()
asyncio.run(monitor.monitor_performance())
```

### Log Analysis
```bash
# Common log analysis commands

# Find connection errors
grep -i "connection" /var/log/database-service.log | tail -20

# Find slow queries
grep -i "slow" /var/log/database-service.log | tail -10

# Find authentication failures  
grep -i "auth" /var/log/database-service.log | grep -i "fail"

# Monitor real-time logs
tail -f /var/log/database-service.log | grep -E "(ERROR|WARN|CRITICAL)"

# Analyze error patterns
awk '/ERROR/ {print $0}' /var/log/database-service.log | sort | uniq -c | sort -nr
```

## Performance Debugging

### Database Query Analysis
```python
# Query performance analyzer
class QueryAnalyzer:
    def __init__(self):
        self.slow_queries = []
        self.query_stats = {}
    
    async def analyze_query_performance(self, query: str, database: str):
        """Analyze individual query performance"""
        
        start_time = time.time()
        
        # Execute query with EXPLAIN
        explain_query = f"EXPLAIN {query}"
        explain_result = await self.execute_query(explain_query, database)
        
        # Execute actual query
        result = await self.execute_query(query, database)
        
        execution_time = (time.time() - start_time) * 1000
        
        # Analyze results
        analysis = {
            "query": query[:100] + "..." if len(query) > 100 else query,
            "database": database,
            "execution_time_ms": execution_time,
            "rows_returned": len(result) if result else 0,
            "explain_plan": explain_result,
            "optimization_suggestions": self.get_optimization_suggestions(explain_result)
        }
        
        if execution_time > 1000:  # Slow query threshold
            self.slow_queries.append(analysis)
        
        return analysis
    
    def get_optimization_suggestions(self, explain_plan):
        """Generate optimization suggestions based on explain plan"""
        suggestions = []
        
        if "Full Table Scan" in str(explain_plan):
            suggestions.append("Consider adding an index to avoid full table scan")
        
        if "Sort" in str(explain_plan):
            suggestions.append("Consider adding an ORDER BY index to avoid sorting")
        
        return suggestions
```

### Connection Pool Debugging
```python
# Connection pool debugger
class ConnectionPoolDebugger:
    def __init__(self, connection_pools):
        self.connection_pools = connection_pools
    
    def debug_pool_status(self):
        """Debug connection pool status"""
        for db_type, pool in self.connection_pools.items():
            print(f"\n{db_type.upper()} Connection Pool:")
            print(f"  Size: {pool.size}")
            print(f"  Checked in: {pool.checked_in}")
            print(f"  Checked out: {pool.checked_out}")
            print(f"  Overflow: {pool.overflow}")
            print(f"  Invalid: {pool.invalid}")
            
            utilization = (pool.checked_out / pool.size) * 100
            print(f"  Utilization: {utilization:.1f}%")
            
            if utilization > 80:
                print(f"  ⚠️  HIGH UTILIZATION WARNING")
            
            if pool.overflow > 0:
                print(f"  ⚠️  OVERFLOW CONNECTIONS ACTIVE")
    
    async def test_pool_performance(self, db_type: str, test_duration: int = 60):
        """Test connection pool performance"""
        pool = self.connection_pools[db_type]
        
        start_time = time.time()
        connection_times = []
        
        while time.time() - start_time < test_duration:
            conn_start = time.time()
            
            try:
                async with pool.acquire() as connection:
                    await connection.execute("SELECT 1")
                
                connection_time = (time.time() - conn_start) * 1000
                connection_times.append(connection_time)
                
            except Exception as e:
                print(f"Connection test failed: {e}")
            
            await asyncio.sleep(0.1)
        
        # Calculate statistics
        if connection_times:
            avg_time = sum(connection_times) / len(connection_times)
            max_time = max(connection_times)
            min_time = min(connection_times)
            
            print(f"\n{db_type} Pool Performance Test ({test_duration}s):")
            print(f"  Total tests: {len(connection_times)}")
            print(f"  Average time: {avg_time:.2f}ms")
            print(f"  Min time: {min_time:.2f}ms")
            print(f"  Max time: {max_time:.2f}ms")
```

## Recovery Procedures

### Service Recovery
```bash
#!/bin/bash
# Service recovery script

echo "🔄 Starting Database Service Recovery..."

# 1. Stop service
echo "Stopping service..."
pkill -f database-service

# 2. Check for port conflicts
echo "Checking for port conflicts..."
lsof -ti:8003 | xargs kill -9 2>/dev/null || true

# 3. Clear temporary files
echo "Clearing temporary files..."
rm -rf /tmp/database-service-*

# 4. Check database connectivity
echo "Testing database connectivity..."
python3 -c "
import asyncio
import sys
sys.path.append('.')
from src.core.connection_factory import ConnectionFactory

async def test_connections():
    factory = ConnectionFactory()
    try:
        # Test each database
        await factory.test_all_connections()
        print('✅ All databases accessible')
    except Exception as e:
        print(f'❌ Database connectivity issue: {e}')
        return False
    return True

if not asyncio.run(test_connections()):
    exit(1)
"

# 5. Restart service
echo "Restarting service..."
python3 main_refactored.py &

# 6. Wait for startup
sleep 10

# 7. Verify service health
echo "Verifying service health..."
curl -f http://localhost:8003/api/v1/database/health || {
    echo "❌ Service health check failed"
    exit 1
}

echo "✅ Database Service recovery completed successfully"
```

### Database Recovery
```python
# Database recovery script
class DatabaseRecovery:
    async def recover_database_connections(self):
        """Recover all database connections"""
        
        recovery_results = {}
        
        for db_type in ["clickhouse", "postgresql", "arangodb", "weaviate", "dragonflydb", "redpanda"]:
            try:
                result = await self.recover_single_database(db_type)
                recovery_results[db_type] = result
            except Exception as e:
                recovery_results[db_type] = {"success": False, "error": str(e)}
        
        return recovery_results
    
    async def recover_single_database(self, db_type: str):
        """Recover single database connection"""
        
        # Close existing connections
        await self.close_database_connections(db_type)
        
        # Wait for connections to close
        await asyncio.sleep(2)
        
        # Reinitialize connection pool
        await self.initialize_database_connection(db_type)
        
        # Test connectivity
        await self.test_database_connectivity(db_type)
        
        return {"success": True, "message": f"{db_type} recovery completed"}
```

---

**Troubleshooting Guide Version**: 2.0.0  
**Last Updated**: 2025-07-31  
**Coverage**: ✅ All major issue categories  
**Status**: ✅ Production Ready