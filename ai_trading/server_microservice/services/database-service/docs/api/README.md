# Database Service API Reference

**Complete API documentation for all database endpoints with practical examples**

## API Overview

The Database Service provides RESTful APIs for 6 different database systems with high-performance, enterprise-grade endpoints optimized for trading applications.

**Base URL**: `http://localhost:8003/api/v1/database`

## API Categories

### 🗂️ **Database Endpoints**
- [ClickHouse API](./CLICKHOUSE_API.md) - Time-series data, ticks, indicators
- [PostgreSQL API](./POSTGRESQL_API.md) - User authentication, metadata
- [ArangoDB API](./ARANGODB_API.md) - Graph queries, strategy relationships
- [Weaviate API](./WEAVIATE_API.md) - Vector search, AI embeddings
- [Cache API](./CACHE_API.md) - High-speed caching operations
- [Streaming API](./STREAMING_API.md) - Real-time data streams

### 🔧 **Service Endpoints**
- [Schema API](./SCHEMA_API.md) - Database schema management
- [Health API](./HEALTH_API.md) - Service and database health monitoring

## Authentication

All API endpoints require authentication using API keys or JWT tokens.

### API Key Authentication
```bash
curl -H "X-API-Key: your-api-key" \
     http://localhost:8003/api/v1/database/health
```

### JWT Token Authentication
```bash
curl -H "Authorization: Bearer your-jwt-token" \
     http://localhost:8003/api/v1/database/clickhouse/query
```

## Common Response Format

All API responses follow a consistent format:

### Success Response
```json
{
  "success": true,
  "timestamp": "2025-07-31T10:30:00Z",
  "duration_ms": 15.5,
  "result": {
    "data": "...",
    "metadata": "..."
  }
}
```

### Error Response
```json
{
  "success": false,
  "timestamp": "2025-07-31T10:30:00Z",
  "duration_ms": 8.2,
  "error": {
    "code": "DATABASE_ERROR",
    "message": "Connection timeout",
    "details": {
      "database": "clickhouse",
      "operation": "query_execution"
    }
  }
}
```

## Rate Limiting

API endpoints have different rate limits based on their computational cost:

| Endpoint Category | Rate Limit | Burst Limit |
|------------------|------------|-------------|
| ClickHouse Queries | 1000/min | 100/sec |
| ClickHouse Inserts | 500/min | 50/sec |
| PostgreSQL Operations | 2000/min | 200/sec |
| ArangoDB Queries | 1000/min | 100/sec |
| Weaviate Searches | 500/min | 50/sec |
| Cache Operations | 10000/min | 1000/sec |
| Health Checks | Unlimited | Unlimited |

## Performance Guidelines

### High-Frequency Trading Optimizations

1. **Batch Operations**: Use batch endpoints for bulk operations
2. **Connection Reuse**: Keep connections alive for repeated requests
3. **Query Optimization**: Use indexed fields in WHERE clauses
4. **Caching**: Leverage cache endpoints for frequently accessed data

### Example: Optimized Tick Data Retrieval
```python
import httpx
import asyncio

async def get_recent_ticks_optimized(symbol: str, limit: int = 1000):
    """Optimized tick data retrieval with connection reuse"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8003/api/v1/database/clickhouse/ticks/recent",
            params={
                "symbol": symbol,
                "limit": limit,
                "broker": "FBS-Demo"
            },
            headers={"X-API-Key": "your-api-key"}
        )
        return response.json()

# Usage
ticks = await get_recent_ticks_optimized("EURUSD", 1000)
```

## Error Handling

### Common Error Codes

| Code | Description | Common Causes |
|------|-------------|---------------|
| `DATABASE_CONNECTION_ERROR` | Database connection failed | Network issues, credentials |
| `QUERY_TIMEOUT` | Query execution timeout | Complex queries, database load |
| `INVALID_PARAMETERS` | Invalid request parameters | Missing required fields |
| `RATE_LIMIT_EXCEEDED` | Too many requests | Exceeding rate limits |
| `AUTHENTICATION_FAILED` | Invalid credentials | Wrong API key or token |
| `PERMISSION_DENIED` | Insufficient permissions | User lacks required permissions |

### Error Handling Example
```python
import httpx

async def handle_database_request(url: str, params: dict):
    """Robust error handling for database requests"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if not data.get("success"):
                error = data.get("error", {})
                if error.get("code") == "RATE_LIMIT_EXCEEDED":
                    await asyncio.sleep(60)  # Wait before retrying
                    return await handle_database_request(url, params)
                else:
                    raise DatabaseError(f"Database error: {error.get('message')}")
            
            return data.get("result")
            
    except httpx.TimeoutException:
        raise DatabaseTimeoutError("Request timeout")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            await asyncio.sleep(60)
            return await handle_database_request(url, params)
        raise DatabaseError(f"HTTP {e.response.status_code}: {e.response.text}")
```

## API Versioning

The API uses URL-based versioning:
- Current version: `v1`
- Base path: `/api/v1/database/`

### Version Compatibility

| Version | Status | Support End |
|---------|--------|-------------|
| v1 | Current | TBD |

## WebSocket Support

For real-time data streaming, use WebSocket endpoints:

```javascript
// Real-time tick data stream
const ws = new WebSocket('ws://localhost:8003/ws/ticks/EURUSD');

ws.onmessage = function(event) {
    const tick = JSON.parse(event.data);
    console.log('New tick:', tick);
};

ws.onopen = function() {
    console.log('Connected to tick stream');
};
```

## SDK and Client Libraries

### Python SDK Example
```python
from neliti_database_client import DatabaseClient

# Initialize client
client = DatabaseClient(
    base_url="http://localhost:8003",
    api_key="your-api-key"
)

# ClickHouse operations
ticks = await client.clickhouse.get_recent_ticks("EURUSD", limit=1000)
await client.clickhouse.insert_ticks(tick_data)

# PostgreSQL operations
user = await client.postgresql.get_user("user@example.com")
await client.postgresql.create_user(user_data)

# Cache operations
await client.cache.set("key", "value", ttl=300)
value = await client.cache.get("key")
```

## API Testing

### Health Check
```bash
curl http://localhost:8003/api/v1/database/health
```

### Authentication Test
```bash
curl -H "X-API-Key: test-key" \
     http://localhost:8003/api/v1/database/health/authenticated
```

### Performance Test
```bash
# Test ClickHouse query performance
time curl -H "X-API-Key: your-key" \
     "http://localhost:8003/api/v1/database/clickhouse/query?query=SELECT%20COUNT(*)%20FROM%20ticks&database=trading_data"
```

## Monitoring and Observability

### API Metrics Endpoint
```bash
curl http://localhost:8003/api/v1/database/metrics
```

Response:
```json
{
  "queries_per_second": 1250,
  "average_response_time_ms": 8.5,
  "error_rate_percent": 0.02,
  "active_connections": {
    "clickhouse": 8,
    "postgresql": 12,
    "arangodb": 4,
    "weaviate": 3,
    "dragonflydb": 25,
    "redpanda": 6
  }
}
```

### Request Tracing

Add tracing headers for debugging:
```bash
curl -H "X-Trace-ID: unique-trace-id" \
     -H "X-API-Key: your-key" \
     http://localhost:8003/api/v1/database/clickhouse/query
```

## Best Practices

### 1. Connection Management
- Use connection pooling in client applications
- Implement proper connection timeout handling
- Monitor connection pool utilization

### 2. Query Optimization
- Use appropriate indexes in database queries
- Implement query result caching
- Use batch operations for bulk data

### 3. Error Handling
- Implement exponential backoff for retries
- Handle rate limiting gracefully
- Log errors with sufficient context

### 4. Security
- Use HTTPS in production environments
- Rotate API keys regularly
- Implement proper access controls

---

**API Version**: v1  
**Last Updated**: 2025-07-31  
**Documentation Status**: ✅ Complete