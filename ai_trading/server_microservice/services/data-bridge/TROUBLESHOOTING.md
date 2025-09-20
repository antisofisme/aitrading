# MT5 Bridge Troubleshooting & Error Handling Guide

## 🚨 Error Handling Overview

The MT5 Bridge Microservice implements comprehensive error handling patterns using centralized infrastructure. This guide provides systematic troubleshooting procedures, error code reference, and resolution strategies.

**Error Handling Architecture:**
- **Centralized Error Management**: All errors processed through shared infrastructure
- **Structured Error Responses**: Consistent error format across all endpoints
- **Automatic Error Recovery**: Built-in retry mechanisms and fallback procedures
- **Comprehensive Logging**: Detailed error context for debugging

## 📊 Error Classification System

### **Error Severity Levels**

| Level | Code Range | Description | Action Required |
|-------|------------|-------------|-----------------|
| **CRITICAL** | 5xx | Service failure, requires immediate attention | Immediate investigation |
| **HIGH** | 4xx | Client errors, trading operations affected | Review and fix within hours |
| **MEDIUM** | 3xx | Warnings, partial functionality impacted | Monitor and address |
| **LOW** | 2xx | Informational, no impact on operations | Log for analysis |

### **Error Categories**

```
┌─────────────────────────────────────────────────────────────┐
│                    Error Classification                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 🔗 Connection Errors                                       │
│    ├─ MT5_CONNECTION_FAILED                                │
│    ├─ WEBSOCKET_CONNECTION_ERROR                           │
│    └─ NETWORK_TIMEOUT                                      │
│                                                             │
│ 📝 Validation Errors                                       │
│    ├─ VALIDATION_ERROR                                     │
│    ├─ INVALID_SYMBOL                                       │
│    └─ INVALID_VOLUME                                       │
│                                                             │
│ 💰 Trading Errors                                          │
│    ├─ INSUFFICIENT_MARGIN                                  │
│    ├─ MARKET_CLOSED                                        │ 
│    └─ ORDER_EXECUTION_FAILED                               │
│                                                             │
│ 🔐 Security Errors                                         │
│    ├─ UNAUTHORIZED                                         │
│    ├─ RATE_LIMITED                                         │
│    └─ AUTHENTICATION_FAILED                                │
│                                                             │
│ ⚙️ System Errors                                           │
│    ├─ INTERNAL_SERVER_ERROR                                │
│    ├─ SERVICE_UNAVAILABLE                                  │
│    └─ CONFIGURATION_ERROR                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Common Issues & Solutions

### **1. Connection Issues**

#### **MT5 Connection Failed**
**Error Code**: `MT5_CONNECTION_FAILED`
**HTTP Status**: 503

**Symptoms**:
```json
{
  "success": false,
  "error": "Failed to connect to MT5: Invalid credentials",
  "error_code": "MT5_CONNECTION_FAILED",
  "details": {
    "server": "FBS-Real",
    "login": 12345,
    "suggestion": "Check credentials and server availability"
  }
}
```

**Diagnostic Steps**:
```bash
# 1. Check service health
curl http://localhost:8001/health

# 2. Verify MT5 configuration
curl http://localhost:8001/status | jq '.status.mt5_status'

# 3. Check container logs
docker logs mt5-bridge | grep "MT5_CONNECTION"

# 4. Test connection manually
curl -X POST http://localhost:8001/connect \
  -H "Content-Type: application/json" \
  -d '{"server":"FBS-Real","login":12345,"password":"test"}'
```

**Common Causes & Solutions**:

| Cause | Solution | Prevention |
|-------|----------|------------|
| **Invalid Credentials** | Verify MT5_LOGIN and MT5_PASSWORD environment variables | Use secure credential management |
| **Server Unavailable** | Check MT5 server status and network connectivity | Monitor server uptime |
| **MT5 Terminal Not Running** | Start MT5 terminal on Windows host | Implement MT5 health monitoring |
| **Firewall Blocking** | Configure firewall rules for MT5 ports | Document network requirements |

**Resolution Script**:
```bash
#!/bin/bash
# mt5_connection_fix.sh

# Check environment variables
echo "Checking MT5 configuration..."
if [ -z "$MT5_LOGIN" ]; then
    echo "❌ MT5_LOGIN not set"
    exit 1
fi

if [ -z "$MT5_PASSWORD" ]; then
    echo "❌ MT5_PASSWORD not set"
    exit 1
fi

echo "✅ Credentials configured"

# Test connection
echo "Testing MT5 connection..."
curl -f -X POST http://localhost:8001/connect || {
    echo "❌ Connection test failed"
    echo "Checking logs..."
    docker logs mt5-bridge --tail 50 | grep -i error
    exit 1
}

echo "✅ MT5 connection successful"
```

#### **WebSocket Connection Drops**
**Error Code**: `WEBSOCKET_CONNECTION_ERROR`

**Symptoms**:
- Frequent client disconnections
- WebSocket messages not delivered
- Connection timeouts

**Diagnostic Steps**:
```bash
# Check WebSocket status
curl http://localhost:8001/websocket/ws/status

# Monitor connection health
watch -n 5 'curl -s http://localhost:8001/websocket/ws/health | jq ".health.status"'

# Check active connections
curl http://localhost:8001/websocket/ws/status | jq '.websocket_status.active_connections'
```

**Solutions**:
```python
# Client-side reconnection logic
class MT5WebSocketClient:
    def __init__(self, url, max_retries=5):
        self.url = url
        self.max_retries = max_retries
        self.retry_count = 0
        
    async def connect_with_retry(self):
        while self.retry_count < self.max_retries:
            try:
                self.websocket = await websockets.connect(self.url)
                self.retry_count = 0  # Reset on successful connection
                return True
            except Exception as e:
                self.retry_count += 1
                wait_time = 2 ** self.retry_count  # Exponential backoff
                print(f"Connection failed, retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
        
        return False
```

### **2. Trading Operation Errors**

#### **Insufficient Margin**
**Error Code**: `INSUFFICIENT_MARGIN`
**HTTP Status**: 400

**Error Response**:
```json
{
  "success": false,
  "error": "Failed to place order: Insufficient margin",
  "details": {
    "error_code": "INSUFFICIENT_MARGIN",
    "required_margin": 108.46,
    "available_margin": 100.00,
    "symbol": "EURUSD",
    "volume": 0.1
  }
}
```

**Diagnostic Steps**:
```bash
# Check account information
curl http://localhost:8001/account | jq '.account'

# Verify margin requirements
curl -X POST http://localhost:8001/symbol \
  -H "Content-Type: application/json" \
  -d '{"symbol":"EURUSD"}' | jq '.symbol'
```

**Solutions**:
1. **Reduce Trade Volume**: Use smaller lot sizes
2. **Increase Account Balance**: Deposit more funds
3. **Close Existing Positions**: Free up margin
4. **Use Different Symbol**: Trade instruments with lower margin requirements

#### **Market Closed**
**Error Code**: `MARKET_CLOSED`
**HTTP Status**: 400

**Error Response**:
```json
{
  "success": false,
  "error": "Market is closed",
  "error_code": "MARKET_CLOSED",
  "details": {
    "symbol": "EURUSD",
    "current_time": "2025-01-27T22:00:00Z",
    "next_open": "2025-01-28T07:00:00Z"
  }
}
```

**Market Hours Check**:
```python
def is_market_open(symbol: str) -> bool:
    """Check if market is open for trading"""
    now = datetime.now(timezone.utc)
    weekday = now.weekday()
    
    # Forex market closed on weekends
    if weekday >= 5:  # Saturday, Sunday
        return False
    
    # Check trading session hours
    hour = now.hour
    if symbol.startswith("EUR") or symbol.startswith("GBP"):
        return 7 <= hour <= 21  # London session
    
    return True
```

### **3. Validation Errors**

#### **Invalid Trading Parameters**
**Error Code**: `VALIDATION_ERROR`
**HTTP Status**: 400

**Common Validation Errors**:

| Field | Error | Valid Range | Example |
|-------|-------|-------------|---------|
| `volume` | Volume too large | 0.01 - 10.0 | 0.1 |
| `symbol` | Invalid symbol format | 6-character pairs | EURUSD |
| `order_type` | Unknown order type | buy, sell, buy_limit, etc. | buy |
| `stop_loss` | Invalid SL price | > 0, logical price | 1.0800 |

**Validation Example**:
```python
from pydantic import BaseModel, Field, validator

class TradeOrderRequest(BaseModel):
    symbol: str = Field(..., regex=r'^[A-Z]{6}$')
    volume: float = Field(..., gt=0.01, le=10.0)
    order_type: str = Field(..., regex=r'^(buy|sell|buy_limit|sell_limit)$')
    
    @validator('symbol')
    def validate_symbol(cls, v):
        allowed_symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']
        if v not in allowed_symbols:
            raise ValueError(f'Symbol {v} not supported')
        return v
```

### **4. Performance Issues**

#### **High Latency**
**Symptoms**:
- Response times > 100ms
- WebSocket message delays
- Cache misses increasing

**Diagnostic Commands**:
```bash
# Check performance metrics
curl http://localhost:8001/performance/metrics | jq '.performance_score'

# Monitor cache performance
curl http://localhost:8001/performance/cache | jq '.cache_performance'

# Check connection pool
curl http://localhost:8001/performance/metrics | jq '.connection_pool'
```

**Performance Tuning**:
```yaml
# docker-compose.yml - Performance optimization
services:
  mt5-bridge:
    environment:
      - CACHE_SIZE=1000        # Increase cache size
      - CACHE_TTL=600          # Extend cache TTL
      - MAX_CONNECTIONS=100    # Increase connection limit
      - BATCH_SIZE=50          # Optimize batch processing
    resources:
      limits:
        memory: 1G
        cpus: '2.0'
```

#### **Memory Usage High**
**Symptoms**:
- Memory usage > 1GB
- Container OOM kills
- Slow response times

**Memory Diagnostic**:
```bash
# Check container memory usage
docker stats mt5-bridge

# Check application memory metrics
curl http://localhost:8001/performance/metrics | jq '.memory_usage'

# Monitor WebSocket connections
curl http://localhost:8001/websocket/ws/status | jq '.websocket_status.active_connections'
```

**Memory Optimization**:
```python
# Enable garbage collection
import gc

# Trigger cleanup every 100 disconnections
if len(self.active_connections) % 100 == 0:
    gc.collect()

# Use WeakKeyDictionary for temporary references
import weakref
self.connection_metadata = weakref.WeakKeyDictionary()
```

## 🔍 Systematic Troubleshooting Process

### **Step 1: Initial Assessment**
```bash
#!/bin/bash
# quick_health_check.sh

echo "🏥 MT5 Bridge Health Check"
echo "=========================="

# Service availability
if curl -f http://localhost:8001/health &>/dev/null; then
    echo "✅ Service is responding"
else
    echo "❌ Service not responding"
    exit 1
fi

# MT5 connection status
MT5_STATUS=$(curl -s http://localhost:8001/health | jq -r '.mt5_status.status')
echo "🔗 MT5 Status: $MT5_STATUS"

# WebSocket health
WS_STATUS=$(curl -s http://localhost:8001/websocket/ws/health | jq -r '.health.status')
echo "🌐 WebSocket Status: $WS_STATUS"

# Performance check
CACHE_HIT_RATE=$(curl -s http://localhost:8001/performance/cache | jq -r '.cache_performance.hit_rate.hit_rate_percent')
echo "💾 Cache Hit Rate: $CACHE_HIT_RATE%"
```

### **Step 2: Error Pattern Analysis**
```bash
# analyze_errors.sh
#!/bin/bash

echo "📊 Error Pattern Analysis"
echo "========================"

# Check recent errors in logs
echo "Recent errors:"
docker logs mt5-bridge --since 1h | grep -i error | tail -10

# Count error types
echo -e "\nError frequency:"
docker logs mt5-bridge --since 24h | grep -i error | \
  grep -o 'error_code":"[^"]*' | \
  sort | uniq -c | sort -nr

# Performance issues
echo -e "\nPerformance warnings:"
docker logs mt5-bridge --since 1h | grep -i "slow\|timeout\|memory" | tail -5
```

### **Step 3: Component-Specific Diagnosis**

#### **MT5 Connection Diagnosis**
```bash
# mt5_diagnosis.sh
#!/bin/bash

echo "🔧 MT5 Connection Diagnosis"
echo "=========================="

# Check MT5 status
curl -s http://localhost:8001/status | jq '.status.mt5_status'

# Test connection
echo -e "\nTesting connection:"
curl -X POST http://localhost:8001/connect \
  -H "Content-Type: application/json" \
  -d '{}' | jq

# Check account accessibility
echo -e "\nAccount information:"
curl -s http://localhost:8001/account | jq '.success'
```

#### **WebSocket Diagnosis**
```bash
# websocket_diagnosis.sh
#!/bin/bash

echo "🌐 WebSocket Diagnosis"
echo "====================="

# Connection statistics
curl -s http://localhost:8001/websocket/ws/status | jq '{
  active_connections: .websocket_status.active_connections,
  success_rate: .websocket_status.success_rate_percent,
  messages_processed: .websocket_status.messages_processed
}'

# Health status
curl -s http://localhost:8001/websocket/ws/health | jq '.health.status'
```

## 📝 Error Code Reference

### **Complete Error Code Table**

| Code | HTTP Status | Category | Description | Resolution |
|------|-------------|----------|-------------|------------|
| `VALIDATION_ERROR` | 400 | Validation | Request validation failed | Check request format and parameters |
| `UNAUTHORIZED` | 401 | Security | Authentication required | Provide valid API key or token |
| `FORBIDDEN` | 403 | Security | Insufficient permissions | Check user permissions and roles |
| `NOT_FOUND` | 404 | Client | Resource not found | Verify resource exists and path is correct |
| `METHOD_NOT_ALLOWED` | 405 | Client | HTTP method not allowed | Use correct HTTP method (GET, POST, etc.) |
| `RATE_LIMITED` | 429 | Security | Too many requests | Wait and retry with backoff |
| `INTERNAL_SERVER_ERROR` | 500 | System | Unexpected server error | Check logs and report to administrators |
| `SERVICE_UNAVAILABLE` | 503 | System | Service temporarily unavailable | Wait and retry, check service status |
| `MT5_CONNECTION_FAILED` | 503 | Connection | Cannot connect to MT5 | Check credentials and MT5 server status |
| `MT5_NOT_CONNECTED` | 503 | Connection | MT5 terminal not connected | Establish MT5 connection first |
| `INSUFFICIENT_MARGIN` | 400 | Trading | Not enough margin for trade | Reduce volume or increase balance |
| `INVALID_SYMBOL` | 400 | Trading | Trading symbol not found | Use valid symbol names |
| `MARKET_CLOSED` | 400 | Trading | Trading not available | Wait for market opening hours |
| `ORDER_EXECUTION_FAILED` | 400 | Trading | Order placement failed | Check order parameters and market conditions |
| `WEBSOCKET_ERROR` | 500 | Connection | WebSocket operation failed | Check connection and retry |
| `CONFIGURATION_ERROR` | 500 | System | Invalid configuration | Verify configuration files and environment variables |

### **Error Response Format**
```json
{
  "success": false,
  "error": "Human-readable error message",
  "error_code": "MACHINE_READABLE_CODE",
  "details": {
    "field": "specific_context",
    "value": "problematic_value",
    "suggestion": "how_to_fix",
    "retry_after": "optional_retry_delay"
  },
  "timestamp": "2025-01-27T10:00:00Z",
  "request_id": "uuid-for-tracking"
}
```

## 🛠️ Advanced Troubleshooting Tools

### **Debug Mode Activation**
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export WEBSOCKET_DEBUG=true
export ENABLE_PROFILING=true

# Restart service with debug mode
docker-compose restart mt5-bridge

# Monitor debug logs
docker logs -f mt5-bridge | grep DEBUG
```

### **Performance Profiling**
```python
# Enable performance profiling in code
import cProfile
import pstats

def profile_function(func):
    """Decorator for profiling function performance"""
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        result = func(*args, **kwargs)
        profiler.disable()
        
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        stats.print_stats(10)  # Top 10 time consumers
        
        return result
    return wrapper
```

### **Network Diagnostics**
```bash
# Check network connectivity
ping mt5-bridge-server.com

# Test WebSocket connection
wscat -c ws://localhost:8001/websocket/ws

# Monitor network traffic
netstat -tulpn | grep :8001

# Check DNS resolution
nslookup mt5-bridge-server.com
```

### **Container Diagnostics**
```bash
# Check container resource usage
docker stats mt5-bridge

# Inspect container configuration
docker inspect mt5-bridge

# Check container processes
docker exec mt5-bridge ps aux

# Access container shell for debugging
docker exec -it mt5-bridge /bin/bash
```

## 🚨 Emergency Procedures

### **Service Recovery Steps**
```bash
#!/bin/bash
# emergency_recovery.sh

echo "🚨 Emergency Recovery Procedure"
echo "==============================="

# Step 1: Stop service gracefully
echo "1. Stopping service..."
docker-compose stop mt5-bridge

# Step 2: Check for hung processes
echo "2. Checking for hung processes..."
docker ps -a | grep mt5-bridge

# Step 3: Force cleanup if needed
echo "3. Force cleanup..."
docker-compose down mt5-bridge
docker system prune -f

# Step 4: Restart with fresh state
echo "4. Restarting service..."
docker-compose up -d mt5-bridge

# Step 5: Verify recovery
sleep 10
if curl -f http://localhost:8001/health; then
    echo "✅ Service recovered successfully"
else
    echo "❌ Recovery failed - escalate to operations team"
fi
```

### **Data Backup Procedure**
```bash
# backup_service_state.sh
#!/bin/bash

BACKUP_DIR="/backup/mt5-bridge/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup configuration
cp -r ./config "$BACKUP_DIR/"

# Backup logs
docker logs mt5-bridge > "$BACKUP_DIR/service.log"

# Backup performance metrics
curl -s http://localhost:8001/performance/metrics > "$BACKUP_DIR/metrics.json"

# Backup cache state
curl -s http://localhost:8001/performance/cache > "$BACKUP_DIR/cache.json"

echo "Backup completed: $BACKUP_DIR"
```

### **Escalation Procedures**

#### **Level 1: Automatic Recovery**
- Service restart attempts (3 retries)
- Connection pool reset
- Cache cleanup

#### **Level 2: Manual Intervention**
- Configuration review
- Log analysis
- Performance tuning

#### **Level 3: Expert Support**
- Code-level debugging
- Infrastructure analysis
- Vendor support engagement

### **Contact Information**
```
Emergency Contacts:
├─ Level 1 Support: support@company.com
├─ Level 2 DevOps: devops@company.com  
├─ Level 3 Engineering: engineering@company.com
└─ Emergency Hotline: +1-800-EMERGENCY
```

## 📊 Monitoring & Alerting

### **Key Metrics to Monitor**
```yaml
# monitoring_alerts.yml
alerts:
  - name: service_down
    condition: service_health != "healthy"
    severity: critical
    
  - name: high_error_rate
    condition: error_rate > 5%
    severity: high
    
  - name: mt5_disconnected
    condition: mt5_status != "connected"
    severity: high
    
  - name: memory_usage_high
    condition: memory_usage > 80%
    severity: medium
    
  - name: cache_hit_rate_low
    condition: cache_hit_rate < 70%
    severity: medium
```

### **Health Check Endpoints**
```bash
# Primary health check
curl http://localhost:8001/health

# WebSocket health
curl http://localhost:8001/websocket/ws/health

# Performance health
curl http://localhost:8001/performance/metrics
```

---

**This comprehensive troubleshooting guide ensures rapid issue resolution and maintains high service availability for enterprise trading operations.**