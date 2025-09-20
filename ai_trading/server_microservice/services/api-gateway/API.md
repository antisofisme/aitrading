# API Gateway Service - OpenAPI Specification

## Overview
The API Gateway serves as the single entry point for all client requests, providing routing, authentication, rate limiting, and CORS management.

## Base URL
- Development: `http://localhost:8000`
- Production: `https://api.neliti-trading.com`

## Authentication
- Bearer Token: `Authorization: Bearer <jwt_token>`
- Service Token: `X-Service-Token: <service_token>` (inter-service)

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
                  example: "healthy"
                timestamp:
                  type: string
                  format: date-time
                version:
                  type: string
                  example: "2.0.0-microservice"
```

### Service Proxy Routes
```yaml
/api/v1/data-bridge/{path}:
  get/post/put/delete:
    summary: Proxy to data-bridge service
    parameters:
      - name: path
        in: path
        required: true
        schema:
          type: string
    security:
      - BearerAuth: []
    responses:
      200:
        description: Successful proxy response
      401:
        description: Unauthorized
      429:
        description: Rate limit exceeded

/api/v1/ai-provider/{path}:
  get/post/put/delete:
    summary: Proxy to ai-provider service
    security:
      - BearerAuth: []

/api/v1/database-service/{path}:
  get/post/put/delete:
    summary: Proxy to database-service
    security:
      - BearerAuth: []

/api/v1/user-service/{path}:
  get/post/put/delete:
    summary: Proxy to user-service
    security:
      - BearerAuth: []

/api/v1/ai-orchestration/{path}:
  get/post/put/delete:
    summary: Proxy to ai-orchestration service
    security:
      - BearerAuth: []
```

### WebSocket Routes
```yaml
/ws/mt5:
  get:
    summary: WebSocket connection for MT5 real-time data
    parameters:
      - name: Connection
        in: header
        required: true
        schema:
          type: string
          example: "Upgrade"
      - name: Upgrade
        in: header
        required: true
        schema:
          type: string
          example: "websocket"
    responses:
      101:
        description: Switching protocols to WebSocket
```

## Rate Limiting
- Default: 1000 requests per minute per IP
- Configurable via `RATE_LIMITING_REQUESTS_PER_MINUTE`
- Responses include rate limit headers:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`

## CORS Configuration
- Production: Specific origins only
- Development: Configurable via `CORS_ORIGINS`

## Error Responses
```yaml
components:
  schemas:
    Error:
      type: object
      properties:
        error:
          type: string
        message:
          type: string
        timestamp:
          type: string
          format: date-time
        path:
          type: string
```