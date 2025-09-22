"""
Enhanced API Gateway with Multi-Tenant Routing and Rate Limiting
Level 2 Connectivity - API Gateway Implementation
"""

import asyncio
import logging
import time
from typing import Dict, Optional, List
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import redis.asyncio as redis
import httpx
from contextlib import asynccontextmanager
import uvicorn
from pydantic import BaseModel, Field
import jwt
from datetime import datetime, timedelta
import os
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import hashlib

# Performance Metrics
REQUEST_COUNT = Counter('api_gateway_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('api_gateway_request_duration_seconds', 'Request duration')
ACTIVE_CONNECTIONS = Gauge('api_gateway_active_connections', 'Active connections')
RATE_LIMIT_HITS = Counter('api_gateway_rate_limit_hits_total', 'Rate limit violations', ['user_id', 'tier'])

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
JWT_SECRET = os.getenv("JWT_SECRET", "your-super-secret-jwt-key-change-in-production")
JWT_ALGORITHM = "HS256"

# Service Registry
SERVICE_REGISTRY = {
    "database": "http://localhost:8001",
    "market-data": "http://localhost:8002",
    "trading-engine": "http://localhost:8003",
    "risk-management": "http://localhost:8004",
    "business-api": "http://localhost:8050",
    "auth-service": "http://localhost:8051",
    "subscription-service": "http://localhost:8022",
    "user-management": "http://localhost:8021",
    "notification-service": "http://localhost:8024",
    "billing-service": "http://localhost:8025"
}

# Rate Limiting Configuration by Subscription Tier
RATE_LIMITS = {
    "free": {"requests_per_minute": 60, "requests_per_hour": 1000},
    "pro": {"requests_per_minute": 300, "requests_per_hour": 10000},
    "enterprise": {"requests_per_minute": 1000, "requests_per_hour": 50000}
}

logger = logging.getLogger(__name__)

class RateLimitInfo(BaseModel):
    limit: int
    remaining: int
    reset_time: int

class GatewayResponse(BaseModel):
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None
    metadata: Optional[Dict] = None

class GatewayState:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.http_client: Optional[httpx.AsyncClient] = None
        self.service_health: Dict[str, bool] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    state = GatewayState()

    # Initialize Redis connection
    try:
        state.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        await state.redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        raise

    # Initialize HTTP client for service communication
    state.http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(10.0),
        limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
    )

    # Initial service health check
    await update_service_health(state)

    app.state.gateway = state

    try:
        yield
    finally:
        # Cleanup
        if state.redis_client:
            await state.redis_client.close()
        if state.http_client:
            await state.http_client.aclose()

app = FastAPI(
    title="AI Trading System - Enhanced API Gateway",
    description="Multi-tenant API Gateway with rate limiting and service discovery",
    version="2.0.0",
    lifespan=lifespan
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.aitrading.local"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication utilities
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[Dict]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None

async def get_current_user(request: Request) -> Optional[Dict]:
    """Extract user from JWT token"""
    authorization: str = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization.split(" ")[1]
    user_data = verify_token(token)
    return user_data

async def check_rate_limit(
    redis_client: redis.Redis,
    user_id: str,
    tier: str = "free"
) -> RateLimitInfo:
    """Check and enforce rate limiting"""
    current_time = int(time.time())
    minute_key = f"rate_limit:minute:{user_id}:{current_time // 60}"
    hour_key = f"rate_limit:hour:{user_id}:{current_time // 3600}"

    # Get current counts
    pipe = redis_client.pipeline()
    pipe.incr(minute_key)
    pipe.expire(minute_key, 60)
    pipe.incr(hour_key)
    pipe.expire(hour_key, 3600)
    results = await pipe.execute()

    minute_count = results[0]
    hour_count = results[2]

    limits = RATE_LIMITS.get(tier, RATE_LIMITS["free"])

    if minute_count > limits["requests_per_minute"]:
        RATE_LIMIT_HITS.labels(user_id=user_id, tier=tier).inc()
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {limits['requests_per_minute']} requests per minute"
        )

    if hour_count > limits["requests_per_hour"]:
        RATE_LIMIT_HITS.labels(user_id=user_id, tier=tier).inc()
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {limits['requests_per_hour']} requests per hour"
        )

    return RateLimitInfo(
        limit=limits["requests_per_minute"],
        remaining=limits["requests_per_minute"] - minute_count,
        reset_time=((current_time // 60) + 1) * 60
    )

async def update_service_health(state: GatewayState):
    """Update service health status"""
    for service_name, service_url in SERVICE_REGISTRY.items():
        try:
            response = await state.http_client.get(f"{service_url}/health", timeout=5.0)
            state.service_health[service_name] = response.status_code == 200
        except Exception:
            state.service_health[service_name] = False

async def route_request(
    service_name: str,
    path: str,
    method: str,
    request: Request,
    state: GatewayState
) -> Response:
    """Route request to appropriate service"""
    service_url = SERVICE_REGISTRY.get(service_name)
    if not service_url:
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")

    if not state.service_health.get(service_name, False):
        raise HTTPException(status_code=503, detail=f"Service {service_name} unavailable")

    # Prepare request
    url = f"{service_url}{path}"
    headers = dict(request.headers)
    headers.pop("host", None)  # Remove host header

    try:
        # Forward request
        if method.upper() == "GET":
            response = await state.http_client.get(url, headers=headers, params=request.query_params)
        elif method.upper() == "POST":
            body = await request.body()
            response = await state.http_client.post(url, headers=headers, content=body)
        elif method.upper() == "PUT":
            body = await request.body()
            response = await state.http_client.put(url, headers=headers, content=body)
        elif method.upper() == "DELETE":
            response = await state.http_client.delete(url, headers=headers)
        else:
            raise HTTPException(status_code=405, detail="Method not allowed")

        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Service timeout")
    except Exception as e:
        logger.error(f"Error routing to {service_name}: {e}")
        raise HTTPException(status_code=502, detail="Bad gateway")

# Middleware for request tracking and rate limiting
@app.middleware("http")
async def gateway_middleware(request: Request, call_next):
    start_time = time.time()

    # Skip internal endpoints
    if request.url.path.startswith(("/health", "/metrics", "/docs")):
        response = await call_next(request)
        return response

    ACTIVE_CONNECTIONS.inc()

    try:
        # User authentication and rate limiting
        user = await get_current_user(request)
        if user:
            user_id = user.get("user_id", "anonymous")
            tier = user.get("subscription_tier", "free")

            # Rate limiting
            rate_limit_info = await check_rate_limit(
                app.state.gateway.redis_client,
                user_id,
                tier
            )

            # Add rate limit headers
            request.state.rate_limit = rate_limit_info
            request.state.user = user

        response = await call_next(request)

        # Add rate limit headers to response
        if hasattr(request.state, "rate_limit"):
            rl = request.state.rate_limit
            response.headers["X-RateLimit-Limit"] = str(rl.limit)
            response.headers["X-RateLimit-Remaining"] = str(rl.remaining)
            response.headers["X-RateLimit-Reset"] = str(rl.reset_time)

        # Record metrics
        duration = time.time() - start_time
        REQUEST_DURATION.observe(duration)
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()

        return response

    except HTTPException as e:
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=e.status_code
        ).inc()
        raise

    finally:
        ACTIVE_CONNECTIONS.dec()

# Health check endpoint
@app.get("/health")
async def health_check():
    """Gateway health check"""
    redis_healthy = False
    try:
        await app.state.gateway.redis_client.ping()
        redis_healthy = True
    except Exception:
        pass

    return {
        "status": "healthy" if redis_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "redis": redis_healthy,
        "services": app.state.gateway.service_health
    }

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics"""
    return Response(generate_latest(), media_type="text/plain")

# Service discovery endpoint
@app.get("/api/v1/services")
async def list_services():
    """List available services and their health"""
    await update_service_health(app.state.gateway)
    return {
        "services": {
            name: {
                "url": url,
                "healthy": app.state.gateway.service_health.get(name, False)
            }
            for name, url in SERVICE_REGISTRY.items()
        }
    }

# Authentication endpoint
@app.post("/api/v1/auth/login")
async def login(credentials: Dict):
    """Authenticate user and return JWT token"""
    # This should validate against user-management service
    # For now, mock authentication
    username = credentials.get("username")
    password = credentials.get("password")

    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password required")

    # Mock user validation - replace with actual authentication
    user_data = {
        "user_id": hashlib.md5(username.encode()).hexdigest()[:8],
        "username": username,
        "subscription_tier": "free",  # Default tier
        "permissions": ["read", "write"]
    }

    token = create_access_token(data=user_data)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_data
    }

# Generic service routing
@app.api_route("/api/v1/{service_name:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def route_to_service(service_name: str, request: Request):
    """Route requests to appropriate microservice"""
    # Extract service name and path
    path_parts = service_name.split("/", 1)
    service = path_parts[0]
    service_path = "/" + path_parts[1] if len(path_parts) > 1 else "/"

    # Add API prefix for service routing
    if not service_path.startswith("/api"):
        service_path = f"/api/v1{service_path}"

    return await route_request(
        service,
        service_path,
        request.method,
        request,
        app.state.gateway
    )

# Business API specific routing (higher performance requirements)
@app.api_route("/api/v1/business/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def route_business_api(path: str, request: Request):
    """Route to business API with optimized performance"""
    # Business API has <15ms performance requirement
    start_time = time.time()

    try:
        response = await route_request(
            "business-api",
            f"/api/v1/business/{path}",
            request.method,
            request,
            app.state.gateway
        )

        # Check performance requirement
        duration = (time.time() - start_time) * 1000  # Convert to ms
        if duration > 15:
            logger.warning(f"Business API response time {duration:.2f}ms exceeded 15ms target")

        return response

    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.error(f"Business API error after {duration:.2f}ms: {e}")
        raise

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )