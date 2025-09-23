# Output Contract: API Gateway → Frontend WebSocket

## Purpose
API Gateway mengirim real-time updates ke Frontend dashboard untuk live trading status, analytics, dan system monitoring.

## Data Format
**Format**: JSON (untuk Frontend compatibility)
**Transport**: WebSocket Real-time
**Compression**: Optional gzip untuk large datasets

## Data Flow
1. Processing services → API Gateway → Analysis results
2. API Gateway transform ke JSON format
3. Send real-time updates ke Frontend via WebSocket
4. Frontend update UI components accordingly

## Message Types

### **1. Trading Status Updates**
```json
{
  "type": "trading_status",
  "user_id": "user123",
  "timestamp": "2024-01-20T10:30:15Z",
  "data": {
    "active_signals": [
      {
        "symbol": "EURUSD",
        "signal": "BUY",
        "confidence": 0.85,
        "entry_price": 1.0845,
        "stop_loss": 1.0820,
        "take_profit": 1.0880,
        "timestamp": "2024-01-20T10:30:10Z",
        "status": "active"
      }
    ],
    "open_positions": [
      {
        "ticket": "12345678",
        "symbol": "EURUSD",
        "type": "BUY",
        "volume": 0.1,
        "open_price": 1.0845,
        "current_price": 1.0850,
        "profit": 5.00,
        "status": "open"
      }
    ],
    "account_balance": 10000.00,
    "account_equity": 10005.00,
    "margin_used": 108.45,
    "margin_free": 9891.55
  }
}
```

### **2. System Performance Metrics**
```json
{
  "type": "system_metrics",
  "timestamp": "2024-01-20T10:30:15Z",
  "data": {
    "connection_status": {
      "mt5": "connected",
      "api_gateway": "healthy",
      "trading_engine": "healthy",
      "notification_hub": "healthy"
    },
    "performance": {
      "data_latency_ms": 15,
      "signal_generation_ms": 120,
      "execution_success_rate": 0.98,
      "uptime_percentage": 99.9
    },
    "usage": {
      "signals_today": 45,
      "executions_today": 12,
      "api_calls_remaining": 8500,
      "subscription_tier": "pro"
    }
  }
}
```

### **3. Real-time Market Data**
```json
{
  "type": "market_data",
  "timestamp": "2024-01-20T10:30:15Z",
  "data": {
    "symbols": [
      {
        "symbol": "EURUSD",
        "bid": 1.0845,
        "ask": 1.0847,
        "spread": 0.0002,
        "change": 0.0005,
        "change_percent": 0.046,
        "timestamp": "2024-01-20T10:30:14Z"
      }
    ],
    "market_session": "london_open",
    "volatility": "medium"
  }
}
```

### **4. Notifications & Alerts**
```json
{
  "type": "notification",
  "user_id": "user123",
  "timestamp": "2024-01-20T10:30:15Z",
  "data": {
    "id": "notif_456",
    "type": "trading_signal",
    "priority": "high",
    "title": "New Trading Signal",
    "message": "BUY EURUSD signal generated with 85% confidence",
    "action_required": true,
    "action_url": "/dashboard/signals/789",
    "expires_at": "2024-01-20T10:35:15Z"
  }
}
```

### **5. Analytics Data**
```json
{
  "type": "analytics",
  "user_id": "user123",
  "timestamp": "2024-01-20T10:30:15Z",
  "data": {
    "performance_summary": {
      "win_rate": 0.72,
      "profit_factor": 1.45,
      "total_trades": 156,
      "profitable_trades": 112,
      "average_profit": 25.50,
      "max_drawdown": 0.08
    },
    "recent_activity": [
      {
        "time": "10:25",
        "action": "Signal Generated",
        "symbol": "EURUSD",
        "result": "BUY"
      }
    ]
  }
}
```

## WebSocket Connection Management
- **Authentication**: JWT token validation saat connection
- **Subscription**: User subscribe ke specific data types
- **Rate Limiting**: Max 100 messages/second per user
- **Reconnection**: Auto-reconnect dengan exponential backoff
- **Heartbeat**: Ping/pong setiap 30 seconds

## Security Requirements
- **User Isolation**: Only send data untuk authenticated user
- **Data Filtering**: Filter berdasarkan subscription tier
- **Real-time Encryption**: WSS (WebSocket Secure)
- **Session Management**: Track dan validate active sessions