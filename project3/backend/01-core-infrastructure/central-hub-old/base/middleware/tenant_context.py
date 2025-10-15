"""
Tenant Context Middleware
Extracts tenant_id from requests and adds to request state
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger("central-hub.tenant-middleware")


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Extract tenant_id from request headers and add to request state

    Supports multiple tenant identification methods:
    1. X-Tenant-ID header (primary)
    2. Authorization JWT token (future)
    3. API key mapping (future)

    For now, defaults to 'system' tenant if not provided
    """

    async def dispatch(self, request: Request, call_next):
        # Extract tenant_id from header
        tenant_id = request.headers.get("X-Tenant-ID", "system")

        # Validate tenant_id format (alphanumeric + dash/underscore)
        if not tenant_id.replace("-", "").replace("_", "").isalnum():
            logger.warning(f"Invalid tenant_id format: {tenant_id}")
            tenant_id = "system"

        # Add to request state for access in endpoints
        request.state.tenant_id = tenant_id

        # Log tenant context (for debugging)
        logger.debug(f"Request from tenant: {tenant_id}, path: {request.url.path}")

        response = await call_next(request)

        # Add tenant_id to response headers for client verification
        response.headers["X-Tenant-ID"] = tenant_id

        return response


def get_tenant_id(request: Request) -> str:
    """
    Helper function to get tenant_id from request state

    Usage in endpoints:
        from middleware.tenant_context import get_tenant_id

        @app.get("/services")
        async def get_services(request: Request):
            tenant_id = get_tenant_id(request)
            # Filter services by tenant_id
    """
    return getattr(request.state, "tenant_id", "system")
