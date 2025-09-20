"""
Rate Limiting Middleware - Enterprise-grade brute force protection
Comprehensive rate limiting with multiple strategies and Redis backend
"""

import asyncio
import time
from typing import Dict, Any, Optional, Callable, Tuple
from datetime import datetime, timedelta
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
import redis.asyncio as aioredis

class RateLimitStrategy:
    """Base class for rate limiting strategies"""
    
    def __init__(self, name: str):
        self.name = name
    
    async def is_allowed(self, identifier: str, redis_client: aioredis.Redis) -> Tuple[bool, Dict[str, Any]]:
        """Check if request is allowed and return status info"""
        raise NotImplementedError
    
    async def record_request(self, identifier: str, redis_client: aioredis.Redis) -> None:
        """Record a request"""
        raise NotImplementedError

class FixedWindowStrategy(RateLimitStrategy):
    """Fixed window rate limiting strategy"""
    
    def __init__(self, requests_per_window: int, window_seconds: int):
        super().__init__("fixed_window")
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
    
    async def is_allowed(self, identifier: str, redis_client: aioredis.Redis) -> Tuple[bool, Dict[str, Any]]:
        """Check fixed window rate limit"""
        current_window = int(time.time()) // self.window_seconds
        key = f"rate_limit:fixed:{identifier}:{current_window}"
        
        current_count = await redis_client.get(key)
        current_count = int(current_count) if current_count else 0
        
        allowed = current_count < self.requests_per_window
        
        return allowed, {
            "strategy": self.name,
            "current_count": current_count,
            "limit": self.requests_per_window,
            "window_seconds": self.window_seconds,
            "reset_time": (current_window + 1) * self.window_seconds
        }
    
    async def record_request(self, identifier: str, redis_client: aioredis.Redis) -> None:
        """Record request in fixed window"""
        current_window = int(time.time()) // self.window_seconds
        key = f"rate_limit:fixed:{identifier}:{current_window}"
        
        pipe = redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, self.window_seconds * 2)  # Keep for cleanup
        await pipe.execute()

class SlidingWindowStrategy(RateLimitStrategy):
    """Sliding window rate limiting strategy (more accurate)"""
    
    def __init__(self, requests_per_window: int, window_seconds: int):
        super().__init__("sliding_window")
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
    
    async def is_allowed(self, identifier: str, redis_client: aioredis.Redis) -> Tuple[bool, Dict[str, Any]]:
        """Check sliding window rate limit"""
        now = time.time()
        window_start = now - self.window_seconds
        key = f"rate_limit:sliding:{identifier}"
        
        # Remove expired entries and count current requests
        pipe = redis_client.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        results = await pipe.execute()
        
        current_count = results[1]
        allowed = current_count < self.requests_per_window
        
        return allowed, {
            "strategy": self.name,
            "current_count": current_count,
            "limit": self.requests_per_window,
            "window_seconds": self.window_seconds,
            "reset_time": now + self.window_seconds
        }
    
    async def record_request(self, identifier: str, redis_client: aioredis.Redis) -> None:
        """Record request in sliding window"""
        now = time.time()
        key = f"rate_limit:sliding:{identifier}"
        
        pipe = redis_client.pipeline()
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, self.window_seconds * 2)
        await pipe.execute()

class TokenBucketStrategy(RateLimitStrategy):
    """Token bucket rate limiting strategy (burst-friendly)"""
    
    def __init__(self, bucket_size: int, refill_rate: float):
        super().__init__("token_bucket")
        self.bucket_size = bucket_size
        self.refill_rate = refill_rate  # tokens per second
    
    async def is_allowed(self, identifier: str, redis_client: aioredis.Redis) -> Tuple[bool, Dict[str, Any]]:
        """Check token bucket rate limit"""
        key = f"rate_limit:bucket:{identifier}"
        now = time.time()
        
        # Get current bucket state
        bucket_data = await redis_client.hmget(key, "tokens", "last_refill")
        
        current_tokens = float(bucket_data[0]) if bucket_data[0] else self.bucket_size
        last_refill = float(bucket_data[1]) if bucket_data[1] else now
        
        # Calculate tokens to add based on time elapsed
        time_elapsed = now - last_refill
        tokens_to_add = time_elapsed * self.refill_rate
        current_tokens = min(self.bucket_size, current_tokens + tokens_to_add)
        
        allowed = current_tokens >= 1.0
        
        return allowed, {
            "strategy": self.name,
            "current_tokens": current_tokens,
            "bucket_size": self.bucket_size,
            "refill_rate": self.refill_rate
        }
    
    async def record_request(self, identifier: str, redis_client: aioredis.Redis) -> None:
        """Consume token from bucket"""
        key = f"rate_limit:bucket:{identifier}"
        now = time.time()
        
        # Get current state and consume token
        bucket_data = await redis_client.hmget(key, "tokens", "last_refill")
        
        current_tokens = float(bucket_data[0]) if bucket_data[0] else self.bucket_size
        last_refill = float(bucket_data[1]) if bucket_data[1] else now
        
        # Refill tokens
        time_elapsed = now - last_refill
        tokens_to_add = time_elapsed * self.refill_rate
        current_tokens = min(self.bucket_size, current_tokens + tokens_to_add)
        
        # Consume one token
        new_tokens = max(0, current_tokens - 1)
        
        # Update bucket state
        pipe = redis_client.pipeline()
        pipe.hmset(key, {
            "tokens": new_tokens,
            "last_refill": now
        })
        pipe.expire(key, int(self.bucket_size / self.refill_rate) * 2)
        await pipe.execute()

class AdaptiveRateLimiter:
    """Adaptive rate limiter that adjusts based on user behavior"""
    
    def __init__(self, redis_client: aioredis.Redis):
        self.redis_client = redis_client
        self.strategies = {}
        self.penalties = {}  # User-specific penalties
        
    def add_strategy(self, name: str, strategy: RateLimitStrategy):
        """Add a rate limiting strategy"""
        self.strategies[name] = strategy
    
    async def is_allowed(
        self,
        identifier: str,
        strategy_name: str = "default",
        user_reputation: int = 100
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check if request is allowed with adaptive logic"""
        
        if strategy_name not in self.strategies:
            return True, {"error": "Strategy not found"}
        
        strategy = self.strategies[strategy_name]
        
        # Check for existing penalties
        penalty_key = f"penalty:{identifier}"
        penalty_data = await self.redis_client.hgetall(penalty_key)
        
        current_penalty = 1.0
        if penalty_data:
            penalty_level = int(penalty_data.get(b"level", 0))
            penalty_expires = float(penalty_data.get(b"expires", 0))
            
            if penalty_expires > time.time():
                current_penalty = 0.1 * (0.5 ** penalty_level)  # Exponential backoff
        
        # Adjust limits based on user reputation and penalties
        if hasattr(strategy, 'requests_per_window'):
            original_limit = strategy.requests_per_window
            strategy.requests_per_window = int(original_limit * current_penalty * (user_reputation / 100))
        
        allowed, info = await strategy.is_allowed(identifier, self.redis_client)
        
        # Restore original limit
        if hasattr(strategy, 'requests_per_window'):
            strategy.requests_per_window = original_limit
        
        info["adaptive_penalty"] = current_penalty
        info["user_reputation"] = user_reputation
        
        return allowed, info
    
    async def record_request(
        self,
        identifier: str,
        strategy_name: str = "default",
        success: bool = True
    ) -> None:
        """Record request and update penalties"""
        
        if strategy_name not in self.strategies:
            return
        
        strategy = self.strategies[strategy_name]
        await strategy.record_request(identifier, self.redis_client)
        
        # Update penalties based on behavior
        penalty_key = f"penalty:{identifier}"
        
        if not success:  # Failed request (e.g., authentication failure)
            penalty_data = await self.redis_client.hgetall(penalty_key)
            penalty_level = int(penalty_data.get(b"level", 0)) if penalty_data else 0
            penalty_level = min(10, penalty_level + 1)  # Max penalty level 10
            
            penalty_duration = 60 * (2 ** penalty_level)  # Exponential backoff
            expires_at = time.time() + penalty_duration
            
            await self.redis_client.hmset(penalty_key, {
                "level": penalty_level,
                "expires": expires_at,
                "last_violation": time.time()
            })
            await self.redis_client.expire(penalty_key, int(penalty_duration * 2))
        else:  # Successful request
            # Gradually reduce penalties for good behavior
            penalty_data = await self.redis_client.hgetall(penalty_key)
            if penalty_data:
                penalty_level = int(penalty_data.get(b"level", 0))
                if penalty_level > 0:
                    penalty_level = max(0, penalty_level - 1)
                    
                    if penalty_level == 0:
                        await self.redis_client.delete(penalty_key)
                    else:
                        penalty_duration = 60 * (2 ** penalty_level)
                        expires_at = time.time() + penalty_duration
                        
                        await self.redis_client.hmset(penalty_key, {
                            "level": penalty_level,
                            "expires": expires_at
                        })

class RateLimitMiddleware:
    """FastAPI middleware for comprehensive rate limiting"""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        global_requests_per_minute: int = 1000,
        auth_requests_per_minute: int = 10,
        user_requests_per_minute: int = 100,
        enable_adaptive: bool = True
    ):
        self.redis_url = redis_url
        self.redis_client = None
        self.rate_limiter = None
        self.enable_adaptive = enable_adaptive
        
        # Rate limiting rules
        self.rules = {
            "global": {"strategy": "sliding_window", "requests": global_requests_per_minute, "window": 60},
            "auth": {"strategy": "token_bucket", "requests": auth_requests_per_minute, "window": 60},
            "user": {"strategy": "fixed_window", "requests": user_requests_per_minute, "window": 60},
            "strict": {"strategy": "token_bucket", "requests": 5, "window": 60}  # For sensitive operations
        }
    
    async def __call__(self, request: Request, call_next: Callable):
        """Rate limiting middleware handler"""
        
        # Initialize Redis client if needed
        if not self.redis_client:
            await self._initialize_redis()
        
        # Determine rate limiting rule based on endpoint
        rule_name = self._get_rule_for_request(request)
        rule = self.rules.get(rule_name, self.rules["global"])
        
        # Get identifier (IP + optional user)
        identifier = self._get_identifier(request)
        
        # Check rate limit
        allowed, info = await self.rate_limiter.is_allowed(
            identifier, 
            rule_name,
            user_reputation=self._get_user_reputation(request)
        )
        
        if not allowed:
            # Rate limit exceeded
            await self._log_rate_limit_violation(identifier, rule_name, info, request)
            
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Try again later.",
                    "retry_after": info.get("reset_time", time.time() + 60) - time.time(),
                    "limit": info.get("limit"),
                    "remaining": info.get("limit", 0) - info.get("current_count", 0)
                },
                headers={
                    "X-RateLimit-Limit": str(info.get("limit", 0)),
                    "X-RateLimit-Remaining": str(max(0, info.get("limit", 0) - info.get("current_count", 0))),
                    "X-RateLimit-Reset": str(int(info.get("reset_time", time.time() + 60))),
                    "Retry-After": str(int(info.get("reset_time", time.time() + 60) - time.time()))
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Record successful request
        await self.rate_limiter.record_request(
            identifier, 
            rule_name, 
            success=response.status_code < 400
        )
        
        # Add rate limit headers to response
        if info:
            response.headers["X-RateLimit-Limit"] = str(info.get("limit", 0))
            response.headers["X-RateLimit-Remaining"] = str(max(0, info.get("limit", 0) - info.get("current_count", 0)))
            response.headers["X-RateLimit-Reset"] = str(int(info.get("reset_time", time.time() + 60)))
        
        return response
    
    async def _initialize_redis(self):
        """Initialize Redis client and rate limiter"""
        try:
            self.redis_client = aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30
            )
            
            # Test connection
            await self.redis_client.ping()
            
            # Initialize adaptive rate limiter
            self.rate_limiter = AdaptiveRateLimiter(self.redis_client)
            
            # Add strategies
            self.rate_limiter.add_strategy(
                "global", 
                SlidingWindowStrategy(self.rules["global"]["requests"], self.rules["global"]["window"])
            )
            self.rate_limiter.add_strategy(
                "auth", 
                TokenBucketStrategy(self.rules["auth"]["requests"], self.rules["auth"]["requests"] / 60.0)
            )
            self.rate_limiter.add_strategy(
                "user", 
                FixedWindowStrategy(self.rules["user"]["requests"], self.rules["user"]["window"])
            )
            self.rate_limiter.add_strategy(
                "strict", 
                TokenBucketStrategy(self.rules["strict"]["requests"], self.rules["strict"]["requests"] / 60.0)
            )
            
        except Exception as e:
            # Fallback to memory-based rate limiting if Redis fails
            print(f"Failed to initialize Redis for rate limiting: {e}")
            # In production, you might want to use a local memory cache as fallback
    
    def _get_rule_for_request(self, request: Request) -> str:
        """Determine rate limiting rule based on request"""
        path = request.url.path.lower()
        
        # Authentication endpoints get stricter limits
        if any(auth_path in path for auth_path in ["/auth/login", "/auth/refresh", "/auth/password-reset"]):
            return "auth"
        
        # Admin endpoints get strict limits
        if "/admin/" in path:
            return "strict"
        
        # User-specific endpoints
        if request.headers.get("Authorization"):
            return "user"
        
        return "global"
    
    def _get_identifier(self, request: Request) -> str:
        """Get unique identifier for rate limiting"""
        # Try to get real IP from headers (for load balancers)
        real_ip = (
            request.headers.get("X-Real-IP") or
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or
            request.client.host
        )
        
        # Include user ID if authenticated
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            # In production, you'd decode the JWT to get user ID
            # For now, we'll use a hash of the token
            import hashlib
            token_hash = hashlib.md5(auth_header.encode()).hexdigest()[:8]
            return f"{real_ip}:{token_hash}"
        
        return real_ip
    
    def _get_user_reputation(self, request: Request) -> int:
        """Get user reputation score (0-100) for adaptive rate limiting"""
        # This is a placeholder - in production, you'd look up actual user reputation
        # based on historical behavior, account age, verification status, etc.
        return 100  # Default reputation
    
    async def _log_rate_limit_violation(
        self, 
        identifier: str, 
        rule_name: str, 
        info: Dict[str, Any], 
        request: Request
    ):
        """Log rate limit violations for monitoring"""
        violation_data = {
            "identifier": identifier,
            "rule": rule_name,
            "path": request.url.path,
            "method": request.method,
            "user_agent": request.headers.get("User-Agent", ""),
            "timestamp": datetime.utcnow().isoformat(),
            "rate_limit_info": info
        }
        
        # Store in Redis for monitoring
        try:
            violation_key = f"violations:{identifier}:{int(time.time())}"
            await self.redis_client.setex(
                violation_key,
                3600,  # Keep for 1 hour
                str(violation_data)
            )
        except Exception as e:
            print(f"Failed to log rate limit violation: {e}")

# Helper function to create rate limit middleware
def create_rate_limit_middleware(**kwargs) -> RateLimitMiddleware:
    """Create and configure rate limiting middleware"""
    return RateLimitMiddleware(**kwargs)