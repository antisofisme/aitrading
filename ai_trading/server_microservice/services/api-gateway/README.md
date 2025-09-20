# API Gateway Service

## Overview
Entry point for all client requests. Handles routing, authentication, and load balancing.

## Responsibilities
- HTTP request routing to appropriate services
- Authentication and authorization
- Rate limiting and CORS
- Health check aggregation
- Load balancing

## Dependencies
- FastAPI core
- Basic authentication libraries
- Request routing middleware

## Resources
- CPU: 1 core
- Memory: 1GB RAM
- Port: 8000

## API Endpoints
```
GET  /health        - Health check
POST /auth/login    - Authentication
GET  /auth/verify   - Token verification
GET  /services/*    - Route to other services
```

## Environment Variables
```
API_GATEWAY_PORT=8000
LOG_LEVEL=INFO
ENVIRONMENT=development
```