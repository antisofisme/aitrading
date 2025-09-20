# Data Bridge Service - OpenAPI Specification

## Overview
The Data Bridge service handles real-time market data streaming, MT5 integration, WebSocket connections, and external data source coordination.

## Base URL
- Development: `http://localhost:8001`
- Production: `http://data-bridge:8001` (internal)

## Endpoints

### Health Check
```yaml
/health:
  get:
    summary: Health check endpoint
    responses:
      200:
        description: Service is healthy
        content:
          application/json:
            schema:
              type: object
              properties:
                status:
                  type: string
                service:
                  type: string
                  example: "data-bridge"
                mt5_connected:
                  type: boolean
                websocket_active:
                  type: boolean
```

### MT5 Integration
```yaml
/api/v1/mt5/connect:
  post:
    summary: Connect to MT5 terminal
    requestBody:
      content:
        application/json:
          schema:
            type: object
            properties:
              login:
                type: string
              password:
                type: string
              server:
                type: string
    responses:
      200:
        description: Successfully connected
      400:
        description: Connection failed

/api/v1/mt5/symbols:
  get:
    summary: Get available trading symbols
    responses:
      200:
        description: List of symbols
        content:
          application/json:
            schema:
              type: object
              properties:
                symbols:
                  type: array
                  items:
                    type: object
                    properties:
                      symbol:
                        type: string
                      description:
                        type: string
                      digits:
                        type: integer

/api/v1/mt5/ticks/{symbol}:
  get:
    summary: Get real-time tick data for symbol
    parameters:
      - name: symbol
        in: path
        required: true
        schema:
          type: string
          example: "EURUSD"
    responses:
      200:
        description: Tick data stream
        content:
          application/json:
            schema:
              type: object
              properties:
                symbol:
                  type: string
                bid:
                  type: number
                ask:
                  type: number
                timestamp:
                  type: string
                  format: date-time
```

### WebSocket Endpoints
```yaml
/ws/mt5/ticks:
  websocket:
    summary: Real-time tick data stream
    description: WebSocket endpoint for streaming live market data
    parameters:
      - name: symbols
        in: query
        schema:
          type: array
          items:
            type: string
    responses:
      101:
        description: WebSocket connection established

/ws/mt5/orders:
  websocket:
    summary: Real-time order updates
    description: WebSocket endpoint for order status updates
```

## Event Streaming (NATS)
The service publishes events to NATS subjects:
- `market.ticks.{symbol}` - Real-time tick data
- `market.orders.{order_id}` - Order updates
- `market.news.economic` - Economic calendar events

## Configuration
- `MT5_LOGIN`, `MT5_PASSWORD`, `MT5_SERVER` - MT5 credentials
- `WEBSOCKET_ENABLED` - Enable/disable WebSocket functionality
- `RATE_LIMITING_REQUESTS_PER_MINUTE` - API rate limiting
- `NATS_URL` - Message broker connection