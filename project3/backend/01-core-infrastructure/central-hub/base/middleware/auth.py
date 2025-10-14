"""
Authentication Middleware
Basic API key authentication for Central Hub
"""

import os
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger("central-hub.auth-middleware")


class BasicAuthMiddleware(BaseHTTPMiddleware):
    """
    Basic API key authentication middleware

    Validates X-API-Key header against configured API keys
    Allows unauthenticated access to:
    - /health (health check)
    - /docs, /redoc, /openapi.json (API documentation)

    Environment variables:
    - CENTRAL_HUB_API_KEYS: Comma-separated list of valid API keys
    - DISABLE_AUTH: Set to "true" to disable authentication (dev only)
    """

    def __init__(self, app):
        super().__init__(app)

        # Load API keys from environment
        api_keys_str = os.getenv("CENTRAL_HUB_API_KEYS", "")
        self.api_keys = set(key.strip() for key in api_keys_str.split(",") if key.strip())

        # Authentication can be disabled for development
        self.auth_enabled = os.getenv("DISABLE_AUTH", "false").lower() != "true"

        if not self.auth_enabled:
            logger.warning("⚠️ Authentication is DISABLED - DO NOT use in production!")
        elif not self.api_keys:
            logger.warning("⚠️ No API keys configured - authentication will reject all requests")

    async def dispatch(self, request: Request, call_next):
        # Skip authentication if disabled
        if not self.auth_enabled:
            return await call_next(request)

        # Public endpoints (no authentication required)
        public_paths = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]

        if request.url.path in public_paths or request.url.path.startswith("/docs"):
            return await call_next(request)

        # Extract API key from header
        api_key = request.headers.get("X-API-Key")

        if not api_key:
            logger.warning(f"Missing API key for path: {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing X-API-Key header",
                headers={"WWW-Authenticate": "ApiKey"}
            )

        # Validate API key
        if api_key not in self.api_keys:
            logger.warning(f"Invalid API key attempt for path: {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid API key"
            )

        # Add authenticated flag to request state
        request.state.authenticated = True

        return await call_next(request)


def require_auth(request: Request):
    """
    Dependency function to require authentication in endpoints

    Usage:
        from fastapi import Depends
        from middleware.auth import require_auth

        @app.get("/protected")
        async def protected_endpoint(authenticated: bool = Depends(require_auth)):
            return {"status": "authenticated"}
    """
    if not getattr(request.state, "authenticated", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return True
