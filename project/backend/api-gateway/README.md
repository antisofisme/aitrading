# API Gateway Service - Phase 1

The API Gateway service provides centralized routing, authentication, and rate limiting for the AI Trading Platform microservices architecture.

## Features

- **Service Routing**: Routes requests to appropriate microservices
- **Authentication Middleware**: JWT token validation with auth service integration
- **Rate Limiting**: Configurable request rate limiting per IP
- **CORS Support**: Cross-origin resource sharing configuration
- **Health Checks**: Comprehensive health monitoring endpoints
- **Service Discovery**: Integration with Central Hub registry
- **Error Handling**: Centralized error handling and logging
- **Security**: Helmet.js security headers and compression

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │────│   API Gateway   │────│   Auth Service  │
│   (Port 3000)   │    │   (Port 8000)   │    │   (Port 8001)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ├─────────────────────────────────────┐
                              │                                     │
                       ┌─────────────────┐                ┌─────────────────┐
                       │ Trading Service │                │  Central Hub    │
                       │   (Port 8002)   │                │   (Port 8003)   │
                       └─────────────────┘                └─────────────────┘
```

## Quick Start

1. **Install Dependencies**:
   ```bash
   npm install
   ```

2. **Environment Setup**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start in Development**:
   ```bash
   npm run dev
   ```

4. **Start in Production**:
   ```bash
   npm start
   ```

## API Routes

### Health Endpoints
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed health with service status
- `GET /health/ready` - Readiness probe
- `GET /health/live` - Liveness probe
- `GET /health/metrics` - Service metrics

### Service Proxying
- `POST /api/auth/*` - Authentication service routes
- `GET|POST|PUT|DELETE /api/trading/*` - Trading service routes
- `GET|POST /api/hub/*` - Central Hub routes

### Gateway Info
- `GET /` - Gateway information and status
- `GET /services` - Registered services list

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_GATEWAY_PORT` | 8000 | Gateway listen port |
| `AUTH_SERVICE_URL` | http://localhost:8001 | Auth service URL |
| `TRADING_SERVICE_URL` | http://localhost:8002 | Trading service URL |
| `HUB_SERVICE_URL` | http://localhost:8003 | Central Hub URL |
| `CORS_ORIGINS` | localhost:3000,localhost:3001 | Allowed CORS origins |
| `RATE_LIMIT_MAX` | 100 | Max requests per window |
| `JWT_SECRET` | - | JWT secret for token validation |

### Rate Limiting

Default: 100 requests per 15 minutes per IP address

```javascript
// Configure in config/config.js
rateLimit: {
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // limit each IP to 100 requests per windowMs
}
```

### CORS Configuration

```javascript
cors: {
  origins: ['http://localhost:3000', 'http://localhost:3001'],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS']
}
```

## Authentication

The gateway integrates with the Authentication Service for token validation:

1. **Local JWT Verification**: Fast local verification using shared secret
2. **Service Delegation**: Falls back to auth service for complex validation
3. **Role-Based Access**: Optional role and permission checking

```javascript
// Protected route example
app.use('/api/trading', authMiddleware, tradingProxy);

// Role-based protection
app.use('/api/admin', authMiddleware, requireRole('admin'), adminProxy);
```

## Service Registry Integration

The gateway automatically registers with the Central Hub:

```javascript
// Registration includes
{
  name: 'api-gateway',
  host: 'localhost',
  port: 8000,
  type: 'api-gateway',
  healthCheck: 'http://localhost:8000/health',
  capabilities: ['routing', 'authentication', 'rate-limiting']
}
```

## Monitoring & Observability

### Health Checks
- **Basic**: `/health` - Simple status check
- **Detailed**: `/health/detailed` - Includes downstream service status
- **Ready**: `/health/ready` - Kubernetes readiness probe
- **Live**: `/health/live` - Kubernetes liveness probe

### Metrics
- Request/response times
- Error rates
- Service availability
- Memory and CPU usage

### Logging
Structured JSON logging with Winston:
- Request/response logging
- Error tracking
- Service interaction logs
- Performance metrics

## Security Features

1. **Helmet.js**: Security headers
2. **Rate Limiting**: DDoS protection
3. **CORS**: Cross-origin protection
4. **JWT Validation**: Token authentication
5. **Input Validation**: Request sanitization
6. **Error Sanitization**: No sensitive data leakage

## Phase 1 Limitations

This is a Phase 1 implementation focusing on:
- Basic routing and proxying
- Simple authentication integration
- Essential middleware
- Health monitoring

Future phases will add:
- Advanced service discovery
- Circuit breakers
- Request/response transformation
- Advanced metrics and tracing
- Load balancing
- API versioning

## Development

```bash
# Development with auto-reload
npm run dev

# Run tests
npm test

# Lint code
npm run lint

# Health check
npm run health
```

## Docker Support

```dockerfile
FROM node:16-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 8000
CMD ["npm", "start"]
```

## Troubleshooting

### Common Issues

1. **Service Discovery Fails**: Check Central Hub connectivity
2. **Authentication Errors**: Verify JWT secret configuration
3. **CORS Issues**: Check allowed origins configuration
4. **Rate Limiting**: Adjust limits for your use case

### Debug Mode

```bash
LOG_LEVEL=debug npm run dev
```

This enables detailed request/response logging and service interaction traces.