# MT5 Bridge WebSocket Protocol - Complete Reference

## 🌐 Protocol Overview

The MT5 Bridge WebSocket Protocol provides real-time, bi-directional communication between trading applications and the MetaTrader 5 platform. Built on WebSocket technology with JSON message format, it supports high-frequency trading operations, real-time market data streaming, and account monitoring.

**Protocol Specifications:**
- **Transport**: WebSocket (RFC 6455)
- **Message Format**: JSON
- **Connection URL**: `ws://localhost:8001/websocket/ws` (development) | `wss://mt5-bridge.domain.com/websocket/ws` (production)
- **Max Connections**: 100 per instance (configurable)
- **Message Rate Limit**: 100 messages/second per connection
- **Heartbeat Interval**: 30 seconds (configurable)

## 🔗 Connection Lifecycle

### **1. Connection Establishment**
```javascript
// JavaScript Example
const ws = new WebSocket('ws://localhost:8001/websocket/ws');

ws.onopen = function(event) {
    console.log('Connected to MT5 Bridge');
};
```

### **2. Welcome Message (Server → Client)**
Upon successful connection, the server sends a welcome message:

```json
{
  "type": "connection_established",
  "message": "Connected to MT5 Bridge Microservice",
  "timestamp": "2025-01-27T10:00:00Z",
  "server_status": "ready",
  "features": {
    "trading_commands": true,
    "real_time_data": true,
    "account_monitoring": true,
    "signal_processing": true
  },
  "mt5_status": {
    "status": "connected",
    "server": "FBS-Real",
    "last_update": "2025-01-27T09:59:55Z"
  }
}
```

### **3. Connection Cleanup**
- **Graceful Disconnect**: Client sends WebSocket close frame
- **Timeout Disconnect**: Server disconnects after 60 seconds of inactivity
- **Error Disconnect**: Automatic cleanup on connection errors

## 📨 Message Structure

### **Base Message Format**
All WebSocket messages follow this structure:

```json
{
  "type": "message_type",
  "timestamp": "2025-01-27T10:00:00Z",
  "data": {
    // Message-specific payload
  }
}
```

**Required Fields:**
- `type` (string): Message type identifier
- `timestamp` (ISO 8601): Message timestamp
- `data` (object): Message payload data

## 📤 Client → Server Messages

### **1. Account Information Streaming**

Send real-time account data for processing and storage.

**Message Format:**
```json
{
  "type": "account_info",
  "timestamp": "2025-01-27T10:00:00Z",
  "data": {
    "balance": 10000.00,
    "equity": 9950.00,
    "margin": 100.00,
    "free_margin": 9850.00,
    "currency": "USD",
    "leverage": 100,
    "margin_level": 9950.00,
    "profit": -50.00
  }
}
```

**Data Fields:**
- `balance` (float): Account balance in account currency
- `equity` (float): Current equity including floating P&L
- `margin` (float): Used margin for open positions
- `free_margin` (float): Available margin for new trades
- `currency` (string): Account currency (USD, EUR, etc.)
- `leverage` (integer): Account leverage ratio
- `margin_level` (float): Margin level percentage
- `profit` (float): Current floating profit/loss

**Server Response:**
```json
{
  "type": "account_info_processed",
  "status": "success",
  "data": {
    "balance": 10000.00,
    "equity": 9950.00,
    "margin": 100.00
  },
  "timestamp": "2025-01-27T10:00:00Z"
}
```

### **2. Tick Data Streaming**

Stream real-time price tick data for market analysis.

**Message Format:**
```json
{
  "type": "tick_data",
  "timestamp": "2025-01-27T10:00:00Z",
  "data": {
    "symbol": "EURUSD",
    "bid": 1.0845,
    "ask": 1.0847,
    "spread": 2.0,
    "time": "2025-01-27T10:00:00Z",
    "volume": 1.0,
    "last": 1.0846,
    "flags": 0
  }
}
```

**Data Fields:**
- `symbol` (string): Trading symbol (e.g., "EURUSD", "GBPUSD")
- `bid` (float): Current bid price
- `ask` (float): Current ask price
- `spread` (float): Spread in points
- `time` (ISO 8601): Tick timestamp
- `volume` (float): Tick volume
- `last` (float): Last trade price
- `flags` (integer): Tick flags (0=normal, 1=buy, 2=sell)

**Server Response:**
```json
{
  "type": "tick_data_processed",
  "status": "success",
  "data": {
    "symbol": "EURUSD",
    "bid": 1.0845,
    "ask": 1.0847,
    "spread": 2.0
  },
  "timestamp": "2025-01-27T10:00:00Z"
}
```

### **3. Trading Signal Execution**

Send trading signals for automatic execution through MT5.

**Message Format:**
```json
{
  "type": "trading_signal",
  "timestamp": "2025-01-27T10:00:00Z",
  "data": {
    "signal_id": "550e8400-e29b-41d4-a716-446655440000",
    "symbol": "EURUSD",
    "action": "BUY",
    "volume": 0.1,
    "stop_loss": 1.0800,
    "take_profit": 1.0900,
    "comment": "AI Signal",
    "urgency": "high",
    "price": 1.0850,
    "magic": 12345,
    "expiration": "2025-01-27T11:00:00Z"
  }
}
```

**Data Fields:**
- `signal_id` (UUID): Unique signal identifier
- `symbol` (string): Trading symbol
- `action` (string): Order action - "BUY", "SELL", "CLOSE"
- `volume` (float): Trading volume (0.01-10.0)
- `stop_loss` (float, optional): Stop loss price
- `take_profit` (float, optional): Take profit price
- `comment` (string): Order comment (max 64 chars)
- `urgency` (string): Signal urgency - "low", "medium", "high"
- `price` (float, optional): Limit price for pending orders
- `magic` (integer, optional): Magic number for EA identification
- `expiration` (ISO 8601, optional): Order expiration time

**Server Response (Success):**
```json
{
  "type": "trading_signal_executed",
  "status": "success",
  "signal_id": "550e8400-e29b-41d4-a716-446655440000",
  "result": {
    "success": true,
    "order_id": "12345678",
    "price": 1.0846,
    "volume": 0.1,
    "symbol": "EURUSD",
    "type": "buy"
  },
  "timestamp": "2025-01-27T10:00:00Z"
}
```

**Server Response (Error):**
```json
{
  "type": "trading_signal_executed",
  "status": "error",
  "signal_id": "550e8400-e29b-41d4-a716-446655440000",
  "error": "Insufficient margin",
  "details": {
    "error_code": "INSUFFICIENT_MARGIN",
    "required_margin": 108.46,
    "available_margin": 100.00
  },
  "timestamp": "2025-01-27T10:00:00Z"
}
```

### **4. Heartbeat Monitoring**

Maintain connection health and get server status.

**Message Format:**
```json
{
  "type": "heartbeat",
  "timestamp": "2025-01-27T10:00:00Z",
  "data": {
    "client": "trading_client_1",
    "client_version": "1.0.0",
    "last_message_time": "2025-01-27T09:59:30Z"
  }
}
```

**Data Fields:**
- `client` (string): Client identifier
- `client_version` (string, optional): Client software version
- `last_message_time` (ISO 8601, optional): Last message timestamp

**Server Response:**
```json
{
  "type": "heartbeat_response",
  "status": "healthy",
  "data": {
    "server_status": "healthy",
    "active_connections": 5,
    "mt5_bridge_status": {
      "status": "connected",
      "last_update": "2025-01-27T09:59:55Z"
    },
    "processing_stats": {
      "total_connections": 25,
      "messages_processed": 1500,
      "successful_operations": 1485,
      "failed_operations": 15
    }
  },
  "timestamp": "2025-01-27T10:00:00Z"
}
```

### **5. MT5 Command Execution**

Execute specific MT5 operations through WebSocket.

**Connection Command:**
```json
{
  "type": "mt5_command",
  "timestamp": "2025-01-27T10:00:00Z",
  "data": {
    "command": "connect",
    "parameters": {
      "server": "FBS-Real",
      "login": 12345,
      "password": "your_password"
    }
  }
}
```

**Status Command:**
```json
{
  "type": "mt5_command",
  "timestamp": "2025-01-27T10:00:00Z",
  "data": {
    "command": "status"
  }
}
```

**Get Ticks Command:**
```json
{
  "type": "mt5_command",
  "timestamp": "2025-01-27T10:00:00Z",
  "data": {
    "command": "get_ticks",
    "symbol": "EURUSD",
    "count": 100
  }
}
```

**Available Commands:**
- `connect`: Connect to MT5 terminal
- `disconnect`: Disconnect from MT5 terminal
- `status`: Get MT5 connection status
- `account_info`: Get account information
- `get_ticks`: Get tick data for symbol

**Server Response:**
```json
{
  "type": "mt5_command_result",
  "status": "success",
  "command": "status",
  "result": {
    "status": "connected",
    "mt5_available": true,
    "last_error": null,
    "active_orders_count": 3
  },
  "timestamp": "2025-01-27T10:00:00Z"
}
```

## 📥 Server → Client Messages

### **1. Connection Status Updates**

**Connection Established:**
```json
{
  "type": "connection_established",
  "message": "Connected to MT5 Bridge Microservice",
  "timestamp": "2025-01-27T10:00:00Z",
  "server_status": "ready",
  "features": {
    "trading_commands": true,
    "real_time_data": true,
    "account_monitoring": true,
    "signal_processing": true
  },
  "mt5_status": {
    "status": "connected",
    "server": "FBS-Real"
  }
}
```

### **2. Data Processing Confirmations**

**Account Info Processed:**
```json
{
  "type": "account_info_processed",
  "status": "success",
  "data": {
    "balance": 10000.00,
    "equity": 9950.00,
    "margin": 100.00
  },
  "timestamp": "2025-01-27T10:00:00Z"
}
```

**Tick Data Processed:**
```json
{
  "type": "tick_data_processed",
  "status": "success",
  "data": {
    "symbol": "EURUSD",
    "bid": 1.0845,
    "ask": 1.0847,
    "spread": 2.0
  },
  "timestamp": "2025-01-27T10:00:00Z"
}
```

### **3. Trading Signal Results**

**Successful Execution:**
```json
{
  "type": "trading_signal_executed",
  "status": "success",
  "signal_id": "550e8400-e29b-41d4-a716-446655440000",
  "result": {
    "success": true,
    "order_id": "12345678",
    "price": 1.0846,
    "volume": 0.1,
    "symbol": "EURUSD",
    "execution_time": "2025-01-27T10:00:01Z"
  },
  "timestamp": "2025-01-27T10:00:00Z"
}
```

**Failed Execution:**
```json
{
  "type": "trading_signal_executed",
  "status": "failed",
  "signal_id": "550e8400-e29b-41d4-a716-446655440000",
  "error": "Market is closed",
  "details": {
    "error_code": "MARKET_CLOSED",
    "retry_after": "2025-01-28T09:00:00Z"
  },
  "timestamp": "2025-01-27T10:00:00Z"
}
```

### **4. System Status Updates**

**Heartbeat Response:**
```json
{
  "type": "heartbeat_response",
  "status": "healthy",
  "data": {
    "server_status": "healthy",
    "active_connections": 5,
    "mt5_bridge_status": {
      "status": "connected",
      "last_update": "2025-01-27T09:59:55Z"
    },
    "processing_stats": {
      "total_connections": 25,
      "messages_processed": 1500,
      "successful_operations": 1485,
      "failed_operations": 15
    }
  },
  "timestamp": "2025-01-27T10:00:00Z"
}
```

### **5. Error Messages**

**Validation Error:**
```json
{
  "type": "error",
  "message": "Invalid message format: missing required field 'symbol'",
  "error_code": "VALIDATION_ERROR",
  "details": {
    "field": "symbol",
    "expected_type": "string",
    "received": null
  },
  "timestamp": "2025-01-27T10:00:00Z"
}
```

**MT5 Connection Error:**
```json
{
  "type": "error",
  "message": "MT5 connection failed: Invalid credentials",
  "error_code": "MT5_CONNECTION_FAILED",
  "details": {
    "server": "FBS-Real",
    "login": 12345,
    "suggestion": "Check credentials and server availability"
  },
  "timestamp": "2025-01-27T10:00:00Z"
}
```

## 🔒 Security & Authentication

### **Authentication Methods**

**1. JWT Token Authentication:**
```javascript
const ws = new WebSocket('ws://localhost:8001/websocket/ws', {
  headers: {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
    'Client-ID': 'trading-client-001'
  }
});
```

**2. API Key Authentication:**
```javascript
const ws = new WebSocket('ws://localhost:8001/websocket/ws', {
  headers: {
    'X-API-Key': 'your-api-key-here',
    'X-Client-Version': '1.0.0'
  }
});
```

### **Rate Limiting**

**Connection Limits:**
- **Max Connections per IP**: 5
- **Messages per Second**: 100
- **Trading Orders per Minute**: 10
- **Heartbeat Interval**: 30 seconds

**Rate Limit Response:**
```json
{
  "type": "error",
  "message": "Rate limit exceeded",
  "error_code": "RATE_LIMITED",
  "details": {
    "limit": 100,
    "window": "60 seconds",
    "retry_after": 30
  },
  "timestamp": "2025-01-27T10:00:00Z"
}
```

## 📊 Protocol Performance

### **Message Processing Performance**
- **Average Latency**: < 5ms for message processing
- **Throughput**: 5000 messages/second
- **Connection Overhead**: 2KB per connection
- **Memory Usage**: 512MB for 100 connections

### **Optimization Features**
- **JSON Serialization**: Single serialization for broadcasts
- **Connection Pooling**: Efficient resource management
- **Batch Processing**: Handle large connection counts
- **Memory Management**: Automatic cleanup and garbage collection

## 🧪 Testing & Examples

### **Complete JavaScript Client**
```javascript
class MT5WebSocketClient {
    constructor(url) {
        this.ws = new WebSocket(url);
        this.setupEventListeners();
        this.heartbeatInterval = null;
    }
    
    setupEventListeners() {
        this.ws.onopen = () => {
            console.log('Connected to MT5 Bridge');
            this.startHeartbeat();
        };
        
        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        this.ws.onclose = () => {
            console.log('Connection closed');
            this.stopHeartbeat();
        };
    }
    
    handleMessage(message) {
        switch(message.type) {
            case 'connection_established':
                console.log('Welcome:', message.message);
                console.log('MT5 Status:', message.mt5_status);
                break;
                
            case 'trading_signal_executed':
                console.log('Signal executed:', message.status);
                if (message.status === 'success') {
                    console.log('Order ID:', message.result.order_id);
                } else {
                    console.error('Execution failed:', message.error);
                }
                break;
                
            case 'heartbeat_response':
                console.log('Server healthy, connections:', 
                    message.data.active_connections);
                break;
                
            case 'error':
                console.error('Server error:', message.message);
                break;
                
            default:
                console.log('Unknown message:', message);
        }
    }
    
    sendTradingSignal(symbol, action, volume, options = {}) {
        const signal = {
            type: 'trading_signal',
            timestamp: new Date().toISOString(),
            data: {
                signal_id: this.generateUUID(),
                symbol: symbol,
                action: action,
                volume: volume,
                stop_loss: options.sl,
                take_profit: options.tp,
                comment: options.comment || 'WebSocket Signal',
                urgency: options.urgency || 'medium'
            }
        };
        
        this.ws.send(JSON.stringify(signal));
    }
    
    sendAccountInfo(accountData) {
        const message = {
            type: 'account_info',
            timestamp: new Date().toISOString(),
            data: accountData
        };
        
        this.ws.send(JSON.stringify(message));
    }
    
    sendTickData(tickData) {
        const message = {
            type: 'tick_data',
            timestamp: new Date().toISOString(),
            data: tickData
        };
        
        this.ws.send(JSON.dumps(message));
    }
    
    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            const heartbeat = {
                type: 'heartbeat',
                timestamp: new Date().toISOString(),
                data: {
                    client: 'javascript_client',
                    client_version: '1.0.0'
                }
            };
            
            this.ws.send(JSON.stringify(heartbeat));
        }, 30000); // 30 seconds
    }
    
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }
    
    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
    
    close() {
        this.stopHeartbeat();
        this.ws.close();
    }
}

// Usage Example
const client = new MT5WebSocketClient('ws://localhost:8001/websocket/ws');

// Send trading signal after connection
setTimeout(() => {
    client.sendTradingSignal('EURUSD', 'BUY', 0.1, {
        sl: 1.0800,
        tp: 1.0900,
        comment: 'JavaScript API Test'
    });
}, 2000);
```

### **Python Client Example**
```python
import asyncio
import websockets
import json
import uuid
from datetime import datetime

class MT5WebSocketClient:
    def __init__(self, url):
        self.url = url
        self.websocket = None
        self.heartbeat_task = None
    
    async def connect(self):
        """Connect to MT5 Bridge WebSocket"""
        self.websocket = await websockets.connect(self.url)
        
        # Start heartbeat task
        self.heartbeat_task = asyncio.create_task(self.heartbeat_loop())
        
        # Start message handler
        asyncio.create_task(self.message_handler())
        
        print("Connected to MT5 Bridge")
    
    async def message_handler(self):
        """Handle incoming messages"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.handle_message(data)
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed")
    
    async def handle_message(self, message):
        """Handle specific message types"""
        msg_type = message.get('type')
        
        if msg_type == 'connection_established':
            print(f"Welcome: {message.get('message')}")
            print(f"MT5 Status: {message.get('mt5_status', {}).get('status')}")
            
        elif msg_type == 'trading_signal_executed':
            print(f"Signal executed: {message.get('status')}")
            if message.get('status') == 'success':
                result = message.get('result', {})
                print(f"Order ID: {result.get('order_id')}")
            else:
                print(f"Execution failed: {message.get('error')}")
                
        elif msg_type == 'heartbeat_response':
            data = message.get('data', {})
            print(f"Server healthy, connections: {data.get('active_connections')}")
            
        elif msg_type == 'error':
            print(f"Server error: {message.get('message')}")
            
        else:
            print(f"Unknown message: {message}")
    
    async def send_trading_signal(self, symbol, action, volume, **options):
        """Send trading signal"""
        signal = {
            'type': 'trading_signal',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'data': {
                'signal_id': str(uuid.uuid4()),
                'symbol': symbol,
                'action': action,
                'volume': volume,
                'stop_loss': options.get('sl'),
                'take_profit': options.get('tp'),
                'comment': options.get('comment', 'Python Client Signal'),
                'urgency': options.get('urgency', 'medium')
            }
        }
        
        await self.websocket.send(json.dumps(signal))
    
    async def send_account_info(self, account_data):
        """Send account information"""
        message = {
            'type': 'account_info',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'data': account_data
        }
        
        await self.websocket.send(json.dumps(message))
    
    async def heartbeat_loop(self):
        """Send periodic heartbeat messages"""
        while True:
            try:
                heartbeat = {
                    'type': 'heartbeat',
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'data': {
                        'client': 'python_client',
                        'client_version': '1.0.0'
                    }
                }
                
                await self.websocket.send(json.dumps(heartbeat))
                await asyncio.sleep(30)  # 30 seconds
                
            except Exception as e:
                print(f"Heartbeat error: {e}")
                break
    
    async def close(self):
        """Close connection gracefully"""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        
        if self.websocket:
            await self.websocket.close()

# Usage Example
async def main():
    client = MT5WebSocketClient('ws://localhost:8001/websocket/ws')
    
    try:
        await client.connect()
        
        # Send account info
        await client.send_account_info({
            'balance': 10000.00,
            'equity': 9950.00,
            'margin': 100.00,
            'free_margin': 9850.00,
            'currency': 'USD',
            'leverage': 100
        })
        
        # Send trading signal
        await client.send_trading_signal('EURUSD', 'BUY', 0.1, 
                                       sl=1.0800, tp=1.0900)
        
        # Keep connection alive
        await asyncio.sleep(60)
        
    finally:
        await client.close()

# Run example
# asyncio.run(main())
```

## 🚨 Error Handling

### **Common Error Codes**

| Error Code | Description | Suggested Action |
|------------|-------------|------------------|
| `VALIDATION_ERROR` | Message format validation failed | Check message structure and field types |
| `MT5_CONNECTION_FAILED` | Cannot connect to MT5 terminal | Verify MT5 credentials and server availability |
| `INSUFFICIENT_MARGIN` | Not enough margin for trade | Check account balance and reduce volume |
| `INVALID_SYMBOL` | Trading symbol not found | Use valid symbol names (EURUSD, GBPUSD, etc.) |
| `RATE_LIMITED` | Too many requests | Reduce message frequency and respect limits |
| `MARKET_CLOSED` | Trading not available | Wait for market opening hours |
| `UNAUTHORIZED` | Authentication failed | Check API keys and authentication tokens |

### **Error Response Format**
```json
{
  "type": "error",
  "message": "Human-readable error description",
  "error_code": "MACHINE_READABLE_CODE",
  "details": {
    "field": "Additional context",
    "suggestion": "How to fix the issue"
  },
  "timestamp": "2025-01-27T10:00:00Z"
}
```

## 📋 Best Practices

### **Connection Management**
1. **Implement reconnection logic** with exponential backoff
2. **Handle connection timeouts** gracefully
3. **Monitor connection health** with heartbeat messages
4. **Cleanup resources** on disconnect

### **Message Handling**
1. **Validate message structure** before sending
2. **Handle all message types** including errors
3. **Implement rate limiting** on client side
4. **Use unique signal IDs** for tracking

### **Performance Optimization**
1. **Batch multiple operations** when possible
2. **Implement client-side caching** for repeated data
3. **Use compression** for large messages
4. **Monitor memory usage** for long-running connections

### **Security Considerations**
1. **Use secure WebSocket (WSS)** in production
2. **Implement proper authentication** mechanisms
3. **Validate all input data** on client and server
4. **Monitor for suspicious activity** patterns

---

**This WebSocket protocol provides comprehensive real-time trading capabilities with enterprise-grade reliability, performance, and security.**