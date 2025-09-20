"""
Authentication Middleware - Microservice Version with Per-Service Infrastructure
Enterprise-grade request validation, rate limiting, and security middleware for API Gateway:
- Per-service rate limiting and security controls
- Microservice authentication and authorization
- Gateway-level request validation and filtering
- Service-to-service authentication coordination
- Per-service security headers and policies
"""

import time
import json
import uuid
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# PER-SERVICE INFRASTRUCTURE INTEGRATION
from ...shared.infrastructure.base.base_error_handler import BaseErrorHandler
from ...shared.infrastructure.optional.event_core import EventCore as BaseEventPublisher
from ...shared.infrastructure.base.base_logger import BaseLogger
from ...shared.infrastructure.base.base_performance import BasePerformance as BasePerformanceTracker
from ...shared.infrastructure.optional.validation_core import ValidationCore as BaseValidator
from ...shared.infrastructure.base.base_config import BaseConfig

# Initialize per-service infrastructure
error_handler = BaseErrorHandler("api-gateway")
event_publisher = BaseEventPublisher("api-gateway")
logger = BaseLogger("api-gateway", "auth_middleware")
performance_tracker = BasePerformanceTracker("api-gateway")
validator = BaseValidator("api-gateway")
config = BaseConfig("api-gateway")


class GatewayRateLimitMiddleware(BaseHTTPMiddleware):
    """
    API Gateway rate limiting middleware with per-service and global limits
    """
    
    def __init__(self, app, requests_per_minute: int = 120, requests_per_hour: int = 2000):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        
        # PERFORMANCE OPTIMIZATION: Use deque for O(1) append and automatic size management
        from collections import deque
        self.request_counts = defaultdict(lambda: {"minute": deque(maxlen=requests_per_minute), "hour": deque(maxlen=requests_per_hour)})
        self.service_counts = defaultdict(lambda: {"minute": deque(maxlen=requests_per_minute), "hour": deque(maxlen=requests_per_hour)})
        
        # Service-specific rate limits
        self.service_limits = {
            "ai-orchestration": {"minute": 60, "hour": 1000},
            "data-bridge": {"minute": 100, "hour": 1500},
            "ml-processing": {"minute": 80, "hour": 1200},
            "trading-engine": {"minute": 50, "hour": 800},
            "database-service": {"minute": 200, "hour": 3000}
        }
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with gateway-level rate limiting"""
        start_time = time.time()
        
        try:
            # Get client and service identifiers
            client_id = await self._get_client_identifier(request)
            service_id = await self._get_target_service(request)
            
            # Check global rate limits
            if await self._is_globally_rate_limited(client_id):
                return await self._rate_limit_response("global")
            
            # Check service-specific rate limits
            if service_id and await self._is_service_rate_limited(client_id, service_id):
                return await self._rate_limit_response(service_id)
            
            # Record request
            await self._record_request(client_id, service_id)
            
            # Process request
            response = await call_next(request)
            processing_time = time.time() - start_time
            
            # Add gateway headers
            await self._add_gateway_headers(response, client_id, service_id, processing_time)
            
            # Record performance metrics
            performance_tracker.record_operation(
                operation_name="gateway_request_processing",
                duration_ms=processing_time * 1000,
                success=response.status_code < 400,
                metadata={
                    "client_id": client_id,
                    "service_id": service_id,
                    "status_code": response.status_code,
                    "path": str(request.url.path)
                }
            )
            
            return response
            
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                error_category=ErrorCategory.SYSTEM_ERROR,
                context={
                    "component": "gateway_rate_limit_middleware",
                    "operation": "process_request",
                    "client_id": client_id if 'client_id' in locals() else "unknown"
                }
            )
            logger.error(f"Gateway rate limit middleware error: {error_response}")
            
            # Continue processing on middleware error
            return await call_next(request)
    
    async def _get_client_identifier(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        try:
            # Try to get user from auth header
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                # In production, this would validate the token and get user ID
                return f"user:{hash(token) % 10000}"
            
            # Fallback to IP address
            client_ip = request.client.host
            forwarded_for = request.headers.get("x-forwarded-for")
            if forwarded_for:
                client_ip = forwarded_for.split(",")[0].strip()
            
            return f"ip:{client_ip}"
            
        except Exception as e:
            logger.warning(f"Client identifier error: {e}")
            return f"ip:{request.client.host}"
    
    async def _get_target_service(self, request: Request) -> Optional[str]:
        """Determine target service from request path"""
        try:
            path = request.url.path
            
            # Map API paths to services
            if path.startswith("/api/v1/ai/"):
                return "ai-orchestration"
            elif path.startswith("/api/v1/data/"):
                return "data-bridge"
            elif path.startswith("/api/v1/ml/"):
                return "ml-processing"
            elif path.startswith("/api/v1/trading/"):
                return "trading-engine"
            elif path.startswith("/api/v1/database/"):
                return "database-service"
            
            return None
            
        except Exception as e:
            logger.warning(f"Service identifier error: {e}")
            return None
    
    async def _is_globally_rate_limited(self, client_id: str) -> bool:
        """PERFORMANCE OPTIMIZED: Check if client is globally rate limited with O(1) complexity"""
        try:
            current_time = time.time()
            
            # PERFORMANCE OPTIMIZATION: Use deque automatic expiration, no manual cleanup needed
            client_data = self.request_counts[client_id]
            
            # PERFORMANCE OPTIMIZATION: Efficient cleanup using deque popleft for expired entries
            minute_cutoff = current_time - 60
            hour_cutoff = current_time - 3600
            
            # Clean minute deque - O(k) where k is expired entries
            while client_data["minute"] and client_data["minute"][0] <= minute_cutoff:
                client_data["minute"].popleft()
            
            # Clean hour deque - O(k) where k is expired entries  
            while client_data["hour"] and client_data["hour"][0] <= hour_cutoff:
                client_data["hour"].popleft()
            
            # Check global limits - O(1) length check instead of O(n) filtering
            return (len(client_data["minute"]) >= self.requests_per_minute or 
                    len(client_data["hour"]) >= self.requests_per_hour)
            
        except Exception as e:
            logger.error(f"Global rate limit check error: {e}")
            return False
    
    async def _is_service_rate_limited(self, client_id: str, service_id: str) -> bool:
        """Check if client is rate limited for specific service"""
        try:
            if service_id not in self.service_limits:
                return False
            
            current_time = time.time()
            service_key = f"{client_id}:{service_id}"
            
            # Clean old entries
            minute_cutoff = current_time - 60
            hour_cutoff = current_time - 3600
            
            service_data = self.service_counts[service_key]
            service_data["minute"] = [t for t in service_data["minute"] if t > minute_cutoff]
            service_data["hour"] = [t for t in service_data["hour"] if t > hour_cutoff]
            
            # Check service-specific limits
            limits = self.service_limits[service_id]
            return (len(service_data["minute"]) >= limits["minute"] or 
                    len(service_data["hour"]) >= limits["hour"])
            
        except Exception as e:
            logger.error(f"Service rate limit check error: {e}")
            return False
    
    async def _record_request(self, client_id: str, service_id: Optional[str]):
        """Record request for rate limiting"""
        try:
            current_time = time.time()
            
            # Record global request
            client_data = self.request_counts[client_id]
            client_data["minute"].append(current_time)
            client_data["hour"].append(current_time)
            
            # Record service-specific request
            if service_id:
                service_key = f"{client_id}:{service_id}"
                service_data = self.service_counts[service_key]
                service_data["minute"].append(current_time)
                service_data["hour"].append(current_time)
            
        except Exception as e:
            logger.error(f"Rate limit recording error: {e}")
    
    async def _rate_limit_response(self, limit_type: str) -> JSONResponse:
        """Generate rate limit exceeded response"""
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "Rate limit exceeded",
                "message": f"Too many requests for {limit_type}",
                "limit_type": limit_type,
                "retry_after": 60
            },
            headers={"Retry-After": "60"}
        )
    
    async def _add_gateway_headers(self, response: Response, client_id: str, service_id: Optional[str], processing_time: float):
        """Add gateway-specific headers to response"""
        try:
            # Rate limit headers
            global_remaining = await self._get_remaining_requests(client_id, "global")
            response.headers["X-RateLimit-Global-Remaining"] = str(global_remaining)
            
            if service_id:
                service_remaining = await self._get_remaining_requests(client_id, service_id)
                response.headers[f"X-RateLimit-{service_id}-Remaining"] = str(service_remaining)
            
            # Gateway identification
            response.headers["X-Gateway"] = "api-gateway"
            response.headers["X-Gateway-Processing-Time"] = f"{processing_time:.3f}s"
            response.headers["X-Request-ID"] = str(uuid.uuid4())
            
        except Exception as e:
            logger.warning(f"Error adding gateway headers: {e}")
    
    async def _get_remaining_requests(self, client_id: str, limit_type: str) -> int:
        """Get remaining requests for client and limit type"""
        try:
            if limit_type == "global":
                client_data = self.request_counts[client_id]
                minute_count = len(client_data["minute"])
                return max(0, self.requests_per_minute - minute_count)
            elif limit_type in self.service_limits:
                service_key = f"{client_id}:{limit_type}"
                service_data = self.service_counts[service_key]
                minute_count = len(service_data["minute"])
                return max(0, self.service_limits[limit_type]["minute"] - minute_count)
            
            return 0
            
        except Exception as e:
            logger.warning(f"Error getting remaining requests: {e}")
            return 0


class GatewaySecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Security headers middleware for API Gateway
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add gateway security headers to response"""
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Gateway identification
        response.headers["X-API-Gateway"] = "neliti-microservices-gateway"
        response.headers["X-Gateway-Version"] = "v1.0"
        
        return response


class GatewayRequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Request logging middleware for API Gateway monitoring
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.sensitive_fields = {"password", "token", "api_key", "secret", "authorization"}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log gateway requests and responses"""
        start_time = time.time()
        request_id = f"gw_req_{int(start_time * 1000000)}"
        
        # Log request
        await self._log_request(request, request_id)
        
        try:
            response = await call_next(request)
            processing_time = time.time() - start_time
            
            # Log response
            await self._log_response(request, response, request_id, processing_time)
            
            # Add request ID to response
            response.headers["X-Gateway-Request-ID"] = request_id
            
            # Publish gateway event
            event_publisher.publish_event(
                event_type="gateway_request_processed",
                data={
                    "request_id": request_id,
                    "method": request.method,
                    "path": str(request.url.path),
                    "status_code": response.status_code,
                    "processing_time_ms": processing_time * 1000,
                    "timestamp": datetime.now().isoformat()
                },
                context="gateway_request_logging"
            )
            
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Gateway request {request_id} failed: {str(e)[:200]} (took {processing_time:.3f}s)")
            
            # Publish gateway error event
            event_publisher.publish_event(
                event_type="gateway_request_failed",
                data={
                    "request_id": request_id,
                    "method": request.method,
                    "path": str(request.url.path),
                    "error": str(e)[:200],
                    "processing_time_ms": processing_time * 1000,
                    "timestamp": datetime.now().isoformat()
                },
                context="gateway_request_logging"
            )
            
            raise
    
    async def _log_request(self, request: Request, request_id: str):
        """Log incoming gateway request"""
        try:
            # Get client info
            client_ip = request.client.host
            user_agent = request.headers.get("user-agent", "Unknown")
            
            # Get target service
            target_service = "unknown"
            path = request.url.path
            if path.startswith("/api/v1/ai/"):
                target_service = "ai-orchestration"
            elif path.startswith("/api/v1/data/"):
                target_service = "data-bridge"
            elif path.startswith("/api/v1/ml/"):
                target_service = "ml-processing"
            elif path.startswith("/api/v1/trading/"):
                target_service = "trading-engine"
            elif path.startswith("/api/v1/database/"):
                target_service = "database-service"
            
            # Get auth status
            auth_status = "unauthenticated"
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                auth_status = "authenticated"
            
            # Log request
            logger.info(
                f"Gateway Request {request_id}: {request.method} {request.url.path} "
                f"-> {target_service} from {client_ip} auth:{auth_status} UA:{user_agent[:50]}"
            )
            
            # Log query params (filtered)
            if request.query_params:
                filtered_params = self._filter_sensitive_data(dict(request.query_params))
                logger.debug(f"Gateway Request {request_id} params: {filtered_params}")
            
        except Exception as e:
            logger.warning(f"Gateway request logging error: {e}")
    
    async def _log_response(self, request: Request, response: Response, request_id: str, processing_time: float):
        """Log gateway response details"""
        try:
            # Determine log level based on status code
            if response.status_code >= 500:
                log_level = logger.error
            elif response.status_code >= 400:
                log_level = logger.warning
            else:
                log_level = logger.info
            
            log_level(
                f"Gateway Response {request_id}: {response.status_code} "
                f"for {request.method} {request.url.path} "
                f"(took {processing_time:.3f}s)"
            )
            
        except Exception as e:
            logger.warning(f"Gateway response logging error: {e}")
    
    def _filter_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter sensitive data from logs"""
        filtered = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in self.sensitive_fields):
                filtered[key] = "***REDACTED***"
            else:
                filtered[key] = str(value)[:100]  # Truncate long values
        return filtered


class GatewayRequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Request validation middleware for API Gateway
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.max_request_size = 50 * 1024 * 1024  # 50MB for gateway
        self.blocked_patterns = [
            "<script", "javascript:", "data:text/html",
            "eval(", "function(", "setTimeout(", "setInterval(",
            "../", "..\\", "%2e%2e", "%2E%2E"
        ]
        
        # Service-specific validation rules
        self.service_rules = {
            "ai-orchestration": {"max_size": 10 * 1024 * 1024},  # 10MB for AI requests
            "data-bridge": {"max_size": 100 * 1024 * 1024},       # 100MB for data uploads
            "ml-processing": {"max_size": 20 * 1024 * 1024},      # 20MB for ML data
            "trading-engine": {"max_size": 5 * 1024 * 1024},     # 5MB for trading
            "database-service": {"max_size": 1 * 1024 * 1024}    # 1MB for DB queries
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate and sanitize gateway requests"""
        try:
            # Get target service
            target_service = await self._get_target_service(request)
            
            # Check request size (service-specific)
            max_size = self.max_request_size
            if target_service and target_service in self.service_rules:
                max_size = self.service_rules[target_service]["max_size"]
            
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > max_size:
                logger.warning(f"Request too large for {target_service}: {content_length} bytes")
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={
                        "error": "Request too large",
                        "max_size": max_size,
                        "service": target_service
                    }
                )
            
            # Check for suspicious patterns in URL
            url_str = str(request.url).lower()
            for pattern in self.blocked_patterns:
                if pattern in url_str:
                    logger.warning(f"Blocked suspicious gateway request: {url_str[:100]}")
                    
                    # Publish security event
                    event_publisher.publish_event(
                        event_type="gateway_security_violation",
                        data={
                            "violation_type": "suspicious_pattern",
                            "pattern": pattern,
                            "url": url_str[:100],
                            "client_ip": request.client.host,
                            "timestamp": datetime.now().isoformat()
                        },
                        context="gateway_security"
                    )
                    
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={"error": "Invalid request format"}
                    )
            
            # Validate content type for POST/PUT requests
            if request.method in ["POST", "PUT", "PATCH"]:
                content_type = request.headers.get("content-type", "")
                valid_types = ["application/json", "multipart/form-data", "application/x-www-form-urlencoded"]
                
                if not any(ct in content_type for ct in valid_types):
                    return JSONResponse(
                        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                        content={"error": "Unsupported content type", "valid_types": valid_types}
                    )
            
            # Validate authentication for protected endpoints
            if await self._requires_authentication(request):
                auth_header = request.headers.get("authorization")
                if not auth_header or not auth_header.startswith("Bearer "):
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"error": "Authentication required"},
                        headers={"WWW-Authenticate": "Bearer"}
                    )
            
            return await call_next(request)
            
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                error_category=ErrorCategory.VALIDATION_ERROR,
                context={
                    "component": "gateway_validation_middleware",
                    "operation": "validate_request",
                    "path": str(request.url.path)
                }
            )
            logger.error(f"Gateway request validation error: {error_response}")
            return await call_next(request)
    
    async def _get_target_service(self, request: Request) -> Optional[str]:
        """Get target service from request path"""
        try:
            path = request.url.path
            
            if path.startswith("/api/v1/ai/"):
                return "ai-orchestration"
            elif path.startswith("/api/v1/data/"):
                return "data-bridge"
            elif path.startswith("/api/v1/ml/"):
                return "ml-processing"
            elif path.startswith("/api/v1/trading/"):
                return "trading-engine"
            elif path.startswith("/api/v1/database/"):
                return "database-service"
            
            return None
            
        except Exception:
            return None
    
    async def _requires_authentication(self, request: Request) -> bool:
        """Check if request path requires authentication"""
        try:
            path = request.url.path
            
            # Public endpoints that don't require auth
            public_endpoints = [
                "/api/v1/auth/login",
                "/api/v1/auth/register",
                "/api/v1/health",
                "/api/v1/status",
                "/docs",
                "/redoc",
                "/openapi.json"
            ]
            
            return path not in public_endpoints
            
        except Exception:
            return True  # Default to requiring auth if uncertain


# Middleware factory functions
def create_gateway_rate_limit_middleware(requests_per_minute: int = 120, requests_per_hour: int = 2000):
    """Create gateway rate limiting middleware with custom limits"""
    def middleware_factory(app):
        return GatewayRateLimitMiddleware(app, requests_per_minute, requests_per_hour)
    return middleware_factory


def create_gateway_middleware_stack():
    """Create complete API Gateway middleware stack"""
    return [
        GatewayRequestValidationMiddleware,
        GatewaySecurityHeadersMiddleware, 
        GatewayRequestLoggingMiddleware,
        create_gateway_rate_limit_middleware(120, 2000)  # Higher limits for gateway
    ]


def create_development_middleware_stack():
    """Create development-friendly middleware stack"""
    return [
        GatewaySecurityHeadersMiddleware,
        GatewayRequestLoggingMiddleware,
        create_gateway_rate_limit_middleware(300, 5000)  # More lenient for development
    ]


def create_production_middleware_stack():
    """Create production-hardened middleware stack"""
    return [
        GatewayRequestValidationMiddleware,
        GatewaySecurityHeadersMiddleware,
        GatewayRequestLoggingMiddleware,
        create_gateway_rate_limit_middleware(100, 1500)  # Stricter for production
    ]