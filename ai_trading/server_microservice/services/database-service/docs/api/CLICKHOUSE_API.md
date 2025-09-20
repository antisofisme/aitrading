# ClickHouse API Reference

**High-performance time-series database operations optimized for trading data**

## Overview

ClickHouse endpoints provide ultra-fast access to trading data including ticks, indicators, and analytics with sub-10ms response times for most operations.

**Base URL**: `/api/v1/database/clickhouse`

## Authentication

All endpoints require authentication:
```bash
curl -H "X-API-Key: your-api-key" \
     http://localhost:8003/api/v1/database/clickhouse/health
```

## Endpoints

### 1. Query Execution

#### Execute Custom Query
```http
GET /api/v1/database/clickhouse/query
```

**Parameters:**
- `query` (required): ClickHouse SQL query
- `database` (optional): Database name (default: "trading_data")

**Example Request:**
```bash
curl -G \
  -H "X-API-Key: your-api-key" \
  --data-urlencode "query=SELECT symbol, COUNT(*) as tick_count FROM ticks WHERE timestamp > now() - INTERVAL 1 HOUR GROUP BY symbol ORDER BY tick_count DESC LIMIT 10" \
  --data-urlencode "database=trading_data" \
  http://localhost:8003/api/v1/database/clickhouse/query
```

**Example Response:**
```json
{
  "success": true,
  "timestamp": "2025-07-31T10:30:00Z",
  "query_duration_ms": 8.5,
  "records_count": 10,
  "result": [
    {"symbol": "EURUSD", "tick_count": 15420},
    {"symbol": "GBPUSD", "tick_count": 12380},
    {"symbol": "USDJPY", "tick_count": 11250}
  ]
}
```

### 2. Tick Data Operations

#### Get Recent Ticks (Optimized)
```http
GET /api/v1/database/clickhouse/ticks/recent
```

**Parameters:**
- `symbol` (required): Trading symbol (e.g., "EURUSD")
- `broker` (optional): Broker name (default: "FBS-Demo")
- `limit` (optional): Number of records (default: 100, max: 10000)
- `timeframe` (optional): Time range (1m, 5m, 1h, 1d)

**Example Request:**
```bash
curl -G \
  -H "X-API-Key: your-api-key" \
  --data-urlencode "symbol=EURUSD" \
  --data-urlencode "broker=FBS-Demo" \
  --data-urlencode "limit=1000" \
  http://localhost:8003/api/v1/database/clickhouse/ticks/recent
```

**Example Response:**
```json
{
  "success": true,
  "symbol": "EURUSD",
  "broker": "FBS-Demo",
  "query_duration_ms": 3.2,
  "records_count": 1000,
  "result": [
    {
      "timestamp": "2025-07-31T10:29:59.850Z",
      "symbol": "EURUSD",
      "bid": 1.08501,
      "ask": 1.08503,
      "last": 1.08502,
      "volume": 1250000,
      "spread": 0.00002,
      "primary_session": true,
      "broker": "FBS-Demo",
      "account_type": "demo"
    }
  ]
}
```

#### Insert Tick Data (Batch)
```http
POST /api/v1/database/clickhouse/ticks/batch
```

**Request Body:**
```json
{
  "table": "ticks",
  "database": "trading_data",
  "data": [
    {
      "timestamp": "2025-07-31T10:30:00.000Z",
      "symbol": "EURUSD",
      "bid": 1.08505,
      "ask": 1.08507,
      "last": 1.08506,
      "volume": 1000000,
      "broker": "FBS-Demo",
      "account_type": "demo"
    }
  ]
}
```

**Example Request:**
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d @tick_data.json \
  http://localhost:8003/api/v1/database/clickhouse/ticks/batch
```

**Example Response:**
```json
{
  "success": true,
  "table": "ticks",
  "database": "trading_data",
  "insert_duration_ms": 5.8,
  "records_inserted": 1,
  "result": {
    "inserted_rows": 1,
    "server_response": "Ok."
  }
}
```

### 3. Indicator Data Operations

#### Get Latest Indicators
```http
GET /api/v1/database/clickhouse/indicators/{symbol}
```

**Path Parameters:**
- `symbol` (required): Trading symbol

**Query Parameters:**
- `indicators` (optional): Comma-separated list of indicators (sma_20, ema_50, rsi_14, etc.)
- `timeframe` (optional): Chart timeframe (M1, M5, M15, M30, H1, H4, D1)
- `limit` (optional): Number of records (default: 100)

**Example Request:**
```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8003/api/v1/database/clickhouse/indicators/EURUSD?indicators=sma_20,ema_50,rsi_14&timeframe=H1&limit=50"
```

**Example Response:**
```json
{
  "success": true,
  "symbol": "EURUSD",
  "timeframe": "H1",
  "query_duration_ms": 6.2,
  "records_count": 50,
  "result": [
    {
      "timestamp": "2025-07-31T10:00:00Z",
      "symbol": "EURUSD",
      "timeframe": "H1",
      "sma_20": 1.08495,
      "ema_50": 1.08487,
      "rsi_14": 65.8,
      "broker": "FBS-Demo"
    }
  ]
}
```

#### Insert Indicator Data
```http
POST /api/v1/database/clickhouse/indicators
```

**Request Body:**
```json
{
  "table": "sma_20",
  "database": "trading_data",
  "data": [
    {
      "timestamp": "2025-07-31T10:00:00Z",
      "symbol": "EURUSD",
      "timeframe": "H1",
      "sma_value": 1.08495,
      "period": 20,
      "broker": "FBS-Demo",
      "account_type": "demo"
    }
  ]
}
```

### 4. Analytics Operations

#### Market Summary
```http
GET /api/v1/database/clickhouse/analytics/market-summary
```

**Parameters:**
- `timeframe` (optional): Analysis period (1h, 4h, 1d, 1w)
- `symbols` (optional): Comma-separated symbols

**Example Request:**
```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8003/api/v1/database/clickhouse/analytics/market-summary?timeframe=1h&symbols=EURUSD,GBPUSD,USDJPY"
```

**Example Response:**
```json
{
  "success": true,
  "timeframe": "1h",
  "query_duration_ms": 12.5,
  "result": {
    "total_symbols": 3,
    "total_ticks": 45280,
    "avg_spread": 0.000018,
    "most_active": "EURUSD",
    "symbols": [
      {
        "symbol": "EURUSD",
        "tick_count": 18750,
        "avg_spread": 0.000015,
        "price_change": 0.00025,
        "price_change_percent": 0.023,
        "volume": 2850000000
      }
    ]
  }
}
```

#### Volume Analysis
```http
GET /api/v1/database/clickhouse/analytics/volume
```

**Parameters:**
- `symbol` (required): Trading symbol
- `timeframe` (required): Analysis timeframe
- `periods` (optional): Number of periods (default: 24)

**Example Request:**
```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8003/api/v1/database/clickhouse/analytics/volume?symbol=EURUSD&timeframe=H1&periods=24"
```

### 5. Performance Operations

#### Database Statistics
```http
GET /api/v1/database/clickhouse/stats
```

**Example Response:**
```json
{
  "success": true,
  "query_duration_ms": 2.1,
  "result": {
    "database": "trading_data",
    "total_tables": 98,
    "total_rows": 15420875,
    "total_size_bytes": 2847593472,
    "tables": [
      {
        "table": "ticks",
        "rows": 12485920,
        "size_bytes": 1847592847,
        "avg_row_size": 148
      }
    ]
  }
}
```

#### Query Performance Analysis
```http
GET /api/v1/database/clickhouse/performance/queries
```

**Example Response:**
```json
{
  "success": true,
  "result": {
    "slow_queries": [
      {
        "query": "SELECT * FROM ticks WHERE timestamp > ...",
        "duration_ms": 1250,
        "rows_examined": 5000000,
        "optimization_suggestion": "Add index on (timestamp, symbol)"
      }
    ],
    "top_queries": [
      {
        "query_pattern": "SELECT ... FROM ticks WHERE symbol = ?",
        "execution_count": 15420,
        "avg_duration_ms": 3.2,
        "total_time_ms": 49344
      }
    ]
  }
}
```

## High-Frequency Trading Optimizations

### 1. Batch Insert for Tick Data
```python
import httpx
import asyncio
from typing import List, Dict

async def insert_ticks_optimized(ticks: List[Dict]) -> Dict:
    """Optimized batch tick insertion for HFT"""
    
    # Split into batches of 1000 for optimal performance
    batch_size = 1000
    batches = [ticks[i:i + batch_size] for i in range(0, len(ticks), batch_size)]
    
    async with httpx.AsyncClient() as client:
        tasks = []
        for batch in batches:
            task = client.post(
                "http://localhost:8003/api/v1/database/clickhouse/ticks/batch",
                json={
                    "table": "ticks",
                    "database": "trading_data",
                    "data": batch
                },
                headers={"X-API-Key": "your-api-key"}
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        return {
            "total_batches": len(batches),
            "total_records": len(ticks),
            "success_rate": sum(1 for r in responses if r.json().get("success")) / len(responses)
        }

# Usage example
tick_data = [
    {
        "timestamp": "2025-07-31T10:30:00.000Z",
        "symbol": "EURUSD",
        "bid": 1.08505,
        "ask": 1.08507,
        "last": 1.08506,
        "volume": 1000000,
        "broker": "FBS-Demo",
        "account_type": "demo"
    }
    # ... more tick data
]

result = await insert_ticks_optimized(tick_data)
```

### 2. Real-time Tick Streaming
```python
async def stream_recent_ticks(symbol: str, callback):
    """Stream recent ticks with minimal latency"""
    while True:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://localhost:8003/api/v1/database/clickhouse/ticks/recent",
                    params={
                        "symbol": symbol,
                        "limit": 1,
                        "broker": "FBS-Demo"
                    },
                    headers={"X-API-Key": "your-api-key"}
                )
                
                data = response.json()
                if data.get("success") and data.get("result"):
                    latest_tick = data["result"][0]
                    await callback(latest_tick)
                
                await asyncio.sleep(0.1)  # 100ms polling
                
        except Exception as e:
            print(f"Streaming error: {e}")
            await asyncio.sleep(1)

# Usage
async def handle_tick(tick):
    print(f"New tick: {tick['symbol']} - {tick['last']}")

await stream_recent_ticks("EURUSD", handle_tick)
```

## Error Handling

### Common ClickHouse Errors

| Error Code | Description | Solution |
|------------|-------------|----------|
| `CLICKHOUSE_CONNECTION_ERROR` | Connection failed | Check ClickHouse server status |
| `QUERY_SYNTAX_ERROR` | Invalid SQL syntax | Validate query syntax |
| `TABLE_NOT_EXISTS` | Table doesn't exist | Create table or check name |
| `MEMORY_LIMIT_EXCEEDED` | Query uses too much memory | Optimize query or increase limits |
| `TIMEOUT_EXCEEDED` | Query execution timeout | Optimize query or increase timeout |

### Error Handling Example
```python
async def safe_clickhouse_query(query: str, database: str = "trading_data"):
    """Safe ClickHouse query with error handling"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "http://localhost:8003/api/v1/database/clickhouse/query",
                params={"query": query, "database": database},
                headers={"X-API-Key": "your-api-key"}
            )
            
            data = response.json()
            if not data.get("success"):
                error = data.get("error", {})
                if error.get("code") == "MEMORY_LIMIT_EXCEEDED":
                    # Retry with LIMIT clause
                    limited_query = f"{query} LIMIT 10000"
                    return await safe_clickhouse_query(limited_query, database)
                else:
                    raise ClickHouseError(f"Query failed: {error.get('message')}")
            
            return data.get("result")
            
    except httpx.TimeoutException:
        raise ClickHouseTimeoutError("Query timeout exceeded")
```

## Performance Benchmarks

### Typical Response Times

| Operation | Records | P50 | P95 | P99 |
|-----------|---------|-----|-----|-----|
| Recent Ticks | 100 | 2ms | 5ms | 8ms |
| Recent Ticks | 1,000 | 3ms | 8ms | 15ms |
| Recent Ticks | 10,000 | 8ms | 20ms | 35ms |
| Batch Insert | 100 | 3ms | 8ms | 12ms |
| Batch Insert | 1,000 | 5ms | 12ms | 25ms |
| Analytics Query | - | 10ms | 25ms | 50ms |

### Optimization Tips

1. **Use Indexes**: Always filter by indexed columns (symbol, timestamp, broker)
2. **Limit Results**: Use LIMIT clause for large result sets
3. **Batch Operations**: Group multiple operations into batches
4. **Connection Reuse**: Use persistent connections for multiple requests
5. **Query Optimization**: Use appropriate WHERE clauses and avoid SELECT *

---

**API Version**: v1  
**Last Updated**: 2025-07-31  
**Performance**: ✅ Optimized for HFT