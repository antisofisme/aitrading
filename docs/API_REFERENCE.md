# API Reference - Dual Client Architecture

Complete API documentation for both PC Client and Web Dashboard architectures.

## API Overview

The AI Trading Platform provides different API endpoints optimized for specific client types:

- **PC Client APIs**: Optimized for high-frequency, low-latency trading operations
- **Web Dashboard APIs**: Optimized for analytics, user management, and monitoring
- **Shared APIs**: Common endpoints used by both client types

## Base URLs

```
PC Client API:    http://localhost:9000/api/v1
Web Dashboard API: https://api.yourdomain.com/api/v1
Development API:   http://localhost:8000/api/v1
```

## Authentication

### PC Client Authentication

PC clients use API key authentication for service-to-service communication:

```bash
# Header format
Authorization: Bearer pc_client_api_key_here
X-Client-Type: pc-client
X-Client-Version: 1.0.0
```

### Web Dashboard Authentication

Web dashboard uses JWT token authentication:

```bash
# Header format
Authorization: Bearer jwt_token_here
X-Client-Type: web-dashboard
Content-Type: application/json
```

### Authentication Endpoints

#### Login (Web Only)
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password",
  "remember": true
}

Response:
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "subscription": "pro",
      "permissions": ["trading", "analytics"]
    },
    "tokens": {
      "access_token": "jwt_token",
      "refresh_token": "refresh_token",
      "expires_in": 900
    }
  }
}
```

#### Refresh Token (Web Only)
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "refresh_token_here"
}

Response:
{
  "success": true,
  "data": {
    "access_token": "new_jwt_token",
    "expires_in": 900
  }
}
```

## PC Client APIs

### Trading Operations

#### Execute Trade
```http
POST /api/v1/pc/trading/execute
Authorization: Bearer pc_client_api_key
Content-Type: application/json

{
  "symbol": "EURUSD",
  "action": "BUY",
  "volume": 0.1,
  "price": 1.0850,
  "stop_loss": 1.0800,
  "take_profit": 1.0900,
  "confidence": 0.85,
  "strategy_id": "ml_ensemble_v1"
}

Response:
{
  "success": true,
  "data": {
    "trade_id": "trade_uuid",
    "order_id": "mt5_order_id",
    "status": "executed",
    "execution_price": 1.0851,
    "execution_time": "2024-01-15T10:30:00Z",
    "slippage": 0.0001
  }
}
```

#### Get Positions
```http
GET /api/v1/pc/trading/positions
Authorization: Bearer pc_client_api_key

Response:
{
  "success": true,
  "data": {
    "positions": [
      {
        "position_id": "pos_uuid",
        "symbol": "EURUSD",
        "action": "BUY",
        "volume": 0.1,
        "open_price": 1.0851,
        "current_price": 1.0865,
        "profit": 1.40,
        "profit_pips": 1.4,
        "open_time": "2024-01-15T10:30:00Z"
      }
    ],
    "total_positions": 1,
    "total_profit": 1.40
  }
}
```

#### Close Position
```http
DELETE /api/v1/pc/trading/positions/{position_id}
Authorization: Bearer pc_client_api_key

Response:
{
  "success": true,
  "data": {
    "position_id": "pos_uuid",
    "close_price": 1.0865,
    "close_time": "2024-01-15T11:00:00Z",
    "profit": 1.40,
    "status": "closed"
  }
}
```

### AI Predictions

#### Get Prediction
```http
GET /api/v1/pc/ai/predictions/{symbol}
Authorization: Bearer pc_client_api_key

Response:
{
  "success": true,
  "data": {
    "symbol": "EURUSD",
    "prediction": {
      "signal": "BUY",
      "confidence": 0.85,
      "probability": 0.78,
      "target_price": 1.0900,
      "stop_loss": 1.0800,
      "timeframe": "1H",
      "valid_until": "2024-01-15T12:00:00Z"
    },
    "models": {
      "ensemble": 0.85,
      "xgboost": 0.82,
      "lstm": 0.88,
      "transformer": 0.84
    },
    "market_regime": "trending",
    "correlation_score": 0.75
  }
}
```

#### Get Bulk Predictions
```http
POST /api/v1/pc/ai/predictions/bulk
Authorization: Bearer pc_client_api_key
Content-Type: application/json

{
  "symbols": ["EURUSD", "GBPUSD", "USDJPY"],
  "timeframes": ["15M", "1H"],
  "models": ["ensemble", "xgboost"]
}

Response:
{
  "success": true,
  "data": {
    "predictions": [
      {
        "symbol": "EURUSD",
        "timeframe": "1H",
        "signal": "BUY",
        "confidence": 0.85
      }
    ],
    "generated_at": "2024-01-15T10:30:00Z"
  }
}
```

### Market Data

#### Get Real-time Quotes
```http
GET /api/v1/pc/market/quotes?symbols=EURUSD,GBPUSD
Authorization: Bearer pc_client_api_key

Response:
{
  "success": true,
  "data": {
    "quotes": [
      {
        "symbol": "EURUSD",
        "bid": 1.0850,
        "ask": 1.0852,
        "spread": 0.0002,
        "timestamp": "2024-01-15T10:30:00Z"
      }
    ]
  }
}
```

#### WebSocket Market Data
```javascript
// WebSocket connection for real-time data
const ws = new WebSocket('ws://localhost:9001/ws/market');

ws.onopen = function() {
  // Subscribe to symbols
  ws.send(JSON.stringify({
    action: 'subscribe',
    symbols: ['EURUSD', 'GBPUSD'],
    types: ['quotes', 'predictions']
  }));
};

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Market update:', data);
};
```

### Account Information

#### Get Account Balance
```http
GET /api/v1/pc/account/balance
Authorization: Bearer pc_client_api_key

Response:
{
  "success": true,
  "data": {
    "balance": 10000.00,
    "equity": 10015.40,
    "margin": 325.20,
    "free_margin": 9690.20,
    "margin_level": 3081.25,
    "currency": "USD",
    "leverage": 100
  }
}
```

## Web Dashboard APIs

### User Management

#### Get User Profile
```http
GET /api/v1/web/users/profile
Authorization: Bearer jwt_token

Response:
{
  "success": true,
  "data": {
    "user": {
      "id": "user_uuid",
      "email": "user@example.com",
      "name": "John Doe",
      "subscription": {
        "tier": "pro",
        "expires_at": "2024-12-31T23:59:59Z",
        "features": ["real_time_data", "advanced_analytics"]
      },
      "created_at": "2024-01-01T00:00:00Z",
      "last_login": "2024-01-15T10:00:00Z"
    }
  }
}
```

#### Update User Profile
```http
PUT /api/v1/web/users/profile
Authorization: Bearer jwt_token
Content-Type: application/json

{
  "name": "John Smith",
  "timezone": "UTC",
  "notifications": {
    "email": true,
    "push": false,
    "sms": false
  }
}

Response:
{
  "success": true,
  "data": {
    "user": {
      "id": "user_uuid",
      "name": "John Smith",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  }
}
```

### Subscription Management

#### Get Subscription Plans
```http
GET /api/v1/web/subscriptions/plans
Authorization: Bearer jwt_token

Response:
{
  "success": true,
  "data": {
    "plans": [
      {
        "id": "free",
        "name": "Free Tier",
        "price": 0,
        "currency": "USD",
        "interval": "month",
        "features": ["basic_analytics", "demo_trading"],
        "limits": {
          "api_calls": 1000,
          "data_retention": "7d"
        }
      },
      {
        "id": "pro",
        "name": "Professional",
        "price": 299,
        "currency": "USD",
        "interval": "month",
        "features": ["real_time_data", "advanced_analytics", "api_access"],
        "limits": {
          "api_calls": 50000,
          "data_retention": "1y"
        }
      }
    ]
  }
}
```

#### Upgrade Subscription
```http
POST /api/v1/web/subscriptions/upgrade
Authorization: Bearer jwt_token
Content-Type: application/json

{
  "plan_id": "pro",
  "payment_method": "midtrans",
  "billing_cycle": "monthly"
}

Response:
{
  "success": true,
  "data": {
    "subscription": {
      "id": "sub_uuid",
      "plan": "pro",
      "status": "active",
      "next_billing": "2024-02-15T00:00:00Z"
    },
    "payment": {
      "payment_url": "https://midtrans.com/payment/...",
      "expires_at": "2024-01-15T11:00:00Z"
    }
  }
}
```

### Analytics and Reporting

#### Get Trading Performance
```http
GET /api/v1/web/analytics/performance?timeframe=30d&group_by=daily
Authorization: Bearer jwt_token

Response:
{
  "success": true,
  "data": {
    "performance": {
      "total_trades": 156,
      "winning_trades": 98,
      "losing_trades": 58,
      "win_rate": 0.628,
      "total_profit": 1250.75,
      "average_profit": 8.02,
      "max_drawdown": 0.05,
      "sharpe_ratio": 2.35,
      "roi": 0.125
    },
    "daily_performance": [
      {
        "date": "2024-01-15",
        "trades": 8,
        "profit": 45.20,
        "win_rate": 0.75
      }
    ]
  }
}
```

#### Get AI Model Performance
```http
GET /api/v1/web/analytics/ai-models?timeframe=7d
Authorization: Bearer jwt_token

Response:
{
  "success": true,
  "data": {
    "models": [
      {
        "name": "ensemble",
        "accuracy": 0.742,
        "precision": 0.756,
        "recall": 0.728,
        "f1_score": 0.742,
        "predictions": 342,
        "correct_predictions": 254
      },
      {
        "name": "xgboost",
        "accuracy": 0.718,
        "precision": 0.721,
        "recall": 0.715,
        "f1_score": 0.718,
        "predictions": 342,
        "correct_predictions": 246
      }
    ],
    "market_regimes": [
      {
        "regime": "trending",
        "accuracy": 0.812,
        "occurrences": 120
      },
      {
        "regime": "ranging",
        "accuracy": 0.686,
        "occurrences": 89
      }
    ]
  }
}
```

#### Export Performance Report
```http
POST /api/v1/web/analytics/export
Authorization: Bearer jwt_token
Content-Type: application/json

{
  "format": "pdf",
  "timeframe": "30d",
  "sections": ["performance", "ai_models", "risk_analysis"],
  "email_delivery": true
}

Response:
{
  "success": true,
  "data": {
    "export_id": "export_uuid",
    "status": "generating",
    "estimated_completion": "2024-01-15T10:35:00Z",
    "download_url": null
  }
}
```

### Multi-User Administration (Enterprise)

#### List Users (Admin Only)
```http
GET /api/v1/web/admin/users?page=1&limit=50&filter=active
Authorization: Bearer admin_jwt_token

Response:
{
  "success": true,
  "data": {
    "users": [
      {
        "id": "user_uuid",
        "email": "user@example.com",
        "name": "John Doe",
        "subscription": "pro",
        "status": "active",
        "last_login": "2024-01-15T09:00:00Z",
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 50,
      "total": 1250,
      "pages": 25
    }
  }
}
```

#### Create User (Admin Only)
```http
POST /api/v1/web/admin/users
Authorization: Bearer admin_jwt_token
Content-Type: application/json

{
  "email": "newuser@example.com",
  "name": "New User",
  "subscription": "basic",
  "permissions": ["trading", "analytics"],
  "send_welcome_email": true
}

Response:
{
  "success": true,
  "data": {
    "user": {
      "id": "new_user_uuid",
      "email": "newuser@example.com",
      "name": "New User",
      "subscription": "basic",
      "status": "pending_verification",
      "created_at": "2024-01-15T10:30:00Z"
    },
    "temporary_password": "temp_password_123"
  }
}
```

### Real-time WebSocket APIs

#### Web Dashboard WebSocket
```javascript
// Connect to WebSocket for real-time updates
const ws = new WebSocket('wss://api.yourdomain.com/ws');

// Send authentication
ws.onopen = function() {
  ws.send(JSON.stringify({
    action: 'authenticate',
    token: 'jwt_token_here'
  }));
};

// Subscribe to channels
ws.send(JSON.stringify({
  action: 'subscribe',
  channels: ['trading_updates', 'ai_predictions', 'market_alerts']
}));

// Handle messages
ws.onmessage = function(event) {
  const data = JSON.parse(event.data);

  switch(data.channel) {
    case 'trading_updates':
      handleTradingUpdate(data.payload);
      break;
    case 'ai_predictions':
      handleAIPrediction(data.payload);
      break;
    case 'market_alerts':
      handleMarketAlert(data.payload);
      break;
  }
};
```

## Shared APIs

### System Health

#### Health Check
```http
GET /api/v1/health

Response:
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00Z",
    "version": "1.0.0",
    "services": {
      "database": "healthy",
      "redis": "healthy",
      "ai_models": "healthy",
      "mt5_connector": "healthy"
    },
    "uptime": "72h 15m 32s"
  }
}
```

#### System Metrics
```http
GET /api/v1/metrics
Authorization: Bearer api_key

Response:
{
  "success": true,
  "data": {
    "metrics": {
      "api_requests_per_minute": 1250,
      "active_connections": 342,
      "database_connections": 15,
      "memory_usage": "2.1GB",
      "cpu_usage": "12%",
      "prediction_latency_ms": 45,
      "trading_latency_ms": 8
    }
  }
}
```

## Error Handling

### Error Response Format

All APIs use consistent error response format:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "field": "symbol",
      "reason": "Invalid trading symbol"
    },
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_uuid"
  }
}
```

### Common Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `AUTHENTICATION_REQUIRED` | Missing or invalid authentication | 401 |
| `AUTHORIZATION_FAILED` | Insufficient permissions | 403 |
| `VALIDATION_ERROR` | Request validation failed | 400 |
| `RESOURCE_NOT_FOUND` | Requested resource not found | 404 |
| `RATE_LIMIT_EXCEEDED` | API rate limit exceeded | 429 |
| `INTERNAL_SERVER_ERROR` | Server error occurred | 500 |
| `SERVICE_UNAVAILABLE` | Service temporarily unavailable | 503 |
| `TRADING_ERROR` | Trading operation failed | 422 |
| `INSUFFICIENT_FUNDS` | Not enough balance for trade | 422 |
| `MARKET_CLOSED` | Market is currently closed | 422 |
| `PREDICTION_UNAVAILABLE` | AI prediction not available | 503 |

## Rate Limiting

### Rate Limits by Client Type

#### PC Client
- **Trading APIs**: 1000 requests/minute
- **Market Data**: 5000 requests/minute
- **AI Predictions**: 500 requests/minute

#### Web Dashboard
- **Free Tier**: 100 requests/minute
- **Basic Tier**: 500 requests/minute
- **Pro Tier**: 2000 requests/minute
- **Enterprise Tier**: 10000 requests/minute

### Rate Limit Headers

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642248000
X-RateLimit-Type: pc-client
```

## SDK and Libraries

### JavaScript SDK

```javascript
import { AITradingClient } from '@aitrading/sdk';

// PC Client
const pcClient = new AITradingClient({
  type: 'pc-client',
  apiKey: 'your_api_key',
  baseURL: 'http://localhost:9000'
});

// Web Dashboard
const webClient = new AITradingClient({
  type: 'web-dashboard',
  token: 'jwt_token',
  baseURL: 'https://api.yourdomain.com'
});

// Execute trade
const trade = await pcClient.trading.execute({
  symbol: 'EURUSD',
  action: 'BUY',
  volume: 0.1
});
```

### Python SDK

```python
from aitrading import AITradingClient

# PC Client
pc_client = AITradingClient(
    client_type='pc-client',
    api_key='your_api_key',
    base_url='http://localhost:9000'
)

# Web Dashboard
web_client = AITradingClient(
    client_type='web-dashboard',
    token='jwt_token',
    base_url='https://api.yourdomain.com'
)

# Get predictions
prediction = pc_client.ai.get_prediction('EURUSD')
print(f"Signal: {prediction.signal}, Confidence: {prediction.confidence}")
```

## Testing

### API Testing with curl

```bash
# Test PC Client API
curl -X GET "http://localhost:9000/api/v1/pc/account/balance" \
  -H "Authorization: Bearer your_pc_api_key" \
  -H "X-Client-Type: pc-client"

# Test Web Dashboard API
curl -X GET "https://api.yourdomain.com/api/v1/web/users/profile" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "X-Client-Type: web-dashboard"
```

### Postman Collection

Import our Postman collection for comprehensive API testing:
- **PC Client Collection**: [Download](./postman/pc-client-api.json)
- **Web Dashboard Collection**: [Download](./postman/web-dashboard-api.json)

## Support

### API Documentation
- **Interactive Docs**: https://api.yourdomain.com/docs
- **OpenAPI Spec**: https://api.yourdomain.com/openapi.json

### Support Channels
- **Discord**: [discord.gg/aitrading](https://discord.gg/aitrading)
- **Email**: api-support@aitrading.com
- **GitHub Issues**: [Repository Issues](https://github.com/your-org/ai-trading-platform/issues)

---

**📝 This API reference covers both PC Client and Web Dashboard architectures. Choose the appropriate endpoints based on your client type and use case.**