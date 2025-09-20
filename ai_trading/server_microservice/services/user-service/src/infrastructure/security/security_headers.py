"""
Security Headers Middleware - Enterprise security headers implementation
Comprehensive security headers for defense in depth
"""

from typing import Dict, Any, Optional, Callable
from fastapi import Request, Response
from fastapi.responses import Response as FastAPIResponse
import secrets
import hashlib

class SecurityHeadersMiddleware:
    """
    Comprehensive security headers middleware for enterprise applications
    Implements OWASP security header recommendations
    """
    
    def __init__(
        self,
        # Content Security Policy
        enable_csp: bool = True,
        csp_directives: Optional[Dict[str, str]] = None,
        csp_report_uri: Optional[str] = None,
        
        # HTTP Strict Transport Security
        enable_hsts: bool = True,
        hsts_max_age: int = 31536000,  # 1 year
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = False,
        
        # Frame Options
        frame_options: str = "DENY",  # DENY, SAMEORIGIN, or ALLOW-FROM
        
        # Content Type Options
        enable_nosniff: bool = True,
        
        # XSS Protection (Legacy, but still useful)
        xss_protection: str = "1; mode=block",
        
        # Referrer Policy
        referrer_policy: str = "strict-origin-when-cross-origin",
        
        # Permissions Policy (Feature Policy)
        enable_permissions_policy: bool = True,
        permissions_policy: Optional[Dict[str, str]] = None,
        
        # Cross-Origin Policies
        cross_origin_embedder_policy: str = "require-corp",
        cross_origin_opener_policy: str = "same-origin",
        cross_origin_resource_policy: str = "same-origin",
        
        # Custom headers
        custom_headers: Optional[Dict[str, str]] = None,
        
        # Environment-specific settings
        environment: str = "production"
    ):
        self.enable_csp = enable_csp
        self.csp_directives = csp_directives or self._get_default_csp_directives()
        self.csp_report_uri = csp_report_uri
        
        self.enable_hsts = enable_hsts
        self.hsts_max_age = hsts_max_age
        self.hsts_include_subdomains = hsts_include_subdomains
        self.hsts_preload = hsts_preload
        
        self.frame_options = frame_options
        self.enable_nosniff = enable_nosniff
        self.xss_protection = xss_protection
        self.referrer_policy = referrer_policy
        
        self.enable_permissions_policy = enable_permissions_policy
        self.permissions_policy = permissions_policy or self._get_default_permissions_policy()
        
        self.cross_origin_embedder_policy = cross_origin_embedder_policy
        self.cross_origin_opener_policy = cross_origin_opener_policy
        self.cross_origin_resource_policy = cross_origin_resource_policy
        
        self.custom_headers = custom_headers or {}
        self.environment = environment
        
        # Nonce tracking for CSP
        self.nonce_cache = {}
    
    def _get_default_csp_directives(self) -> Dict[str, str]:
        """Get default Content Security Policy directives"""
        return {
            "default-src": "'self'",
            "script-src": "'self' 'unsafe-inline' 'unsafe-eval'",  # Adjust based on needs
            "style-src": "'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src": "'self' https://fonts.gstatic.com",
            "img-src": "'self' data: https:",
            "connect-src": "'self' https:",
            "frame-src": "'none'",
            "object-src": "'none'",
            "media-src": "'self'",
            "form-action": "'self'",
            "base-uri": "'self'",
            "frame-ancestors": "'none'",
            "upgrade-insecure-requests": ""
        }
    
    def _get_default_permissions_policy(self) -> Dict[str, str]:
        """Get default Permissions Policy directives"""
        return {
            "accelerometer": "()",
            "ambient-light-sensor": "()",
            "autoplay": "()",
            "battery": "()",
            "camera": "()",
            "cross-origin-isolated": "()",
            "display-capture": "()",
            "document-domain": "()",
            "encrypted-media": "()",
            "execution-while-not-rendered": "()",
            "execution-while-out-of-viewport": "()",
            "fullscreen": "()",
            "geolocation": "()",
            "gyroscope": "()",
            "keyboard-map": "()",
            "magnetometer": "()",
            "microphone": "()",
            "midi": "()",
            "navigation-override": "()",
            "payment": "()",
            "picture-in-picture": "()",
            "publickey-credentials-get": "()",
            "screen-wake-lock": "()",
            "sync-xhr": "()",
            "usb": "()",
            "web-share": "()",
            "xr-spatial-tracking": "()"
        }
    
    async def __call__(self, request: Request, call_next: Callable):
        """Security headers middleware handler"""
        
        # Generate CSP nonce for this request
        nonce = self._generate_nonce() if self.enable_csp else None
        
        # Store nonce in request state for use in templates
        if nonce:
            request.state.csp_nonce = nonce
        
        # Process the request
        response = await call_next(request)
        
        # Add security headers to response
        self._add_security_headers(response, request, nonce)
        
        return response
    
    def _add_security_headers(self, response: Response, request: Request, nonce: Optional[str] = None):
        """Add comprehensive security headers to response"""
        
        # Content Security Policy
        if self.enable_csp:
            csp_header = self._build_csp_header(nonce)
            response.headers["Content-Security-Policy"] = csp_header
            
            if self.csp_report_uri:
                response.headers["Content-Security-Policy-Report-Only"] = f"{csp_header}; report-uri {self.csp_report_uri}"
        
        # HTTP Strict Transport Security (only for HTTPS)
        if self.enable_hsts and self._is_https_request(request):
            hsts_value = f"max-age={self.hsts_max_age}"
            if self.hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            if self.hsts_preload:
                hsts_value += "; preload"
            response.headers["Strict-Transport-Security"] = hsts_value
        
        # X-Frame-Options
        response.headers["X-Frame-Options"] = self.frame_options
        
        # X-Content-Type-Options
        if self.enable_nosniff:
            response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-XSS-Protection (legacy but still useful)
        response.headers["X-XSS-Protection"] = self.xss_protection
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = self.referrer_policy
        
        # Permissions Policy
        if self.enable_permissions_policy:
            permissions_header = self._build_permissions_policy_header()
            response.headers["Permissions-Policy"] = permissions_header
        
        # Cross-Origin Policies
        response.headers["Cross-Origin-Embedder-Policy"] = self.cross_origin_embedder_policy
        response.headers["Cross-Origin-Opener-Policy"] = self.cross_origin_opener_policy
        response.headers["Cross-Origin-Resource-Policy"] = self.cross_origin_resource_policy
        
        # Server identification (security through obscurity)
        response.headers["Server"] = "TradingPlatform/1.0"
        
        # Remove potentially sensitive headers
        response.headers.pop("X-Powered-By", None)
        
        # Cache control for sensitive endpoints
        if self._is_sensitive_endpoint(request):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        # Custom headers
        for header_name, header_value in self.custom_headers.items():
            response.headers[header_name] = header_value
        
        # Development-specific headers
        if self.environment == "development":
            response.headers["X-Development-Mode"] = "true"
            # Relax some policies for development
            if "Content-Security-Policy" in response.headers:
                csp = response.headers["Content-Security-Policy"]
                # Add localhost for development
                csp = csp.replace("'self'", "'self' localhost:* 127.0.0.1:*")
                response.headers["Content-Security-Policy"] = csp
    
    def _build_csp_header(self, nonce: Optional[str] = None) -> str:
        """Build Content Security Policy header"""
        directives = []
        
        for directive, value in self.csp_directives.items():
            if value:
                # Add nonce to script-src and style-src if provided
                if nonce and directive in ["script-src", "style-src"] and "'self'" in value:
                    value = f"{value} 'nonce-{nonce}'"
                directives.append(f"{directive} {value}")
            else:
                # Directive without value (like upgrade-insecure-requests)
                directives.append(directive)
        
        return "; ".join(directives)
    
    def _build_permissions_policy_header(self) -> str:
        """Build Permissions Policy header"""
        policies = []
        for feature, allowlist in self.permissions_policy.items():
            policies.append(f"{feature}={allowlist}")
        return ", ".join(policies)
    
    def _generate_nonce(self) -> str:
        """Generate cryptographically secure nonce for CSP"""
        nonce_bytes = secrets.token_bytes(16)
        return hashlib.sha256(nonce_bytes).hexdigest()[:16]
    
    def _is_https_request(self, request: Request) -> bool:
        """Check if request is over HTTPS"""
        return (
            request.url.scheme == "https" or
            request.headers.get("X-Forwarded-Proto") == "https" or
            request.headers.get("X-Forwarded-Ssl") == "on"
        )
    
    def _is_sensitive_endpoint(self, request: Request) -> bool:
        """Check if endpoint is sensitive and needs strict cache control"""
        sensitive_paths = [
            "/auth/",
            "/admin/",
            "/api/v1/users/",
            "/api/v1/trading/",
            "/api/v1/portfolio/"
        ]
        
        path = request.url.path.lower()
        return any(sensitive_path in path for sensitive_path in sensitive_paths)

class CSRFProtectionMiddleware:
    """
    CSRF Protection Middleware using double-submit cookie pattern
    """
    
    def __init__(
        self,
        secret_key: str,
        token_header_name: str = "X-CSRF-Token",
        cookie_name: str = "csrf_token",
        cookie_path: str = "/",
        cookie_domain: Optional[str] = None,
        cookie_secure: bool = True,
        cookie_httponly: bool = False,  # Client needs to read this cookie
        cookie_samesite: str = "Strict",
        exempt_methods: list = None,
        exempt_paths: list = None
    ):
        self.secret_key = secret_key
        self.token_header_name = token_header_name
        self.cookie_name = cookie_name
        self.cookie_path = cookie_path
        self.cookie_domain = cookie_domain
        self.cookie_secure = cookie_secure
        self.cookie_httponly = cookie_httponly
        self.cookie_samesite = cookie_samesite
        
        self.exempt_methods = exempt_methods or ["GET", "HEAD", "OPTIONS", "TRACE"]
        self.exempt_paths = exempt_paths or ["/health", "/docs", "/openapi.json"]
    
    async def __call__(self, request: Request, call_next: Callable):
        """CSRF protection middleware handler"""
        
        # Skip CSRF check for exempt methods and paths
        if (request.method in self.exempt_methods or 
            any(exempt_path in request.url.path for exempt_path in self.exempt_paths)):
            response = await call_next(request)
            self._set_csrf_cookie(response, request)
            return response
        
        # Verify CSRF token for state-changing requests
        if not self._verify_csrf_token(request):
            return FastAPIResponse(
                content="CSRF token missing or invalid",
                status_code=403,
                headers={"Content-Type": "text/plain"}
            )
        
        # Process request
        response = await call_next(request)
        
        # Set/refresh CSRF cookie
        self._set_csrf_cookie(response, request)
        
        return response
    
    def _verify_csrf_token(self, request: Request) -> bool:
        """Verify CSRF token using double-submit cookie pattern"""
        
        # Get token from header
        header_token = request.headers.get(self.token_header_name)
        if not header_token:
            return False
        
        # Get token from cookie
        cookie_token = request.cookies.get(self.cookie_name)
        if not cookie_token:
            return False
        
        # Verify tokens match and are valid
        return (
            header_token == cookie_token and
            self._verify_token_signature(header_token)
        )
    
    def _generate_csrf_token(self) -> str:
        """Generate cryptographically secure CSRF token"""
        token_data = secrets.token_urlsafe(32)
        signature = hashlib.hmac.new(
            self.secret_key.encode(),
            token_data.encode(),
            hashlib.sha256
        ).hexdigest()[:16]
        
        return f"{token_data}.{signature}"
    
    def _verify_token_signature(self, token: str) -> bool:
        """Verify CSRF token signature"""
        try:
            token_data, signature = token.rsplit(".", 1)
            expected_signature = hashlib.hmac.new(
                self.secret_key.encode(),
                token_data.encode(),
                hashlib.sha256
            ).hexdigest()[:16]
            
            return secrets.compare_digest(signature, expected_signature)
        except ValueError:
            return False
    
    def _set_csrf_cookie(self, response: Response, request: Request):
        """Set CSRF cookie in response"""
        
        # Generate new token if not present or invalid
        existing_token = request.cookies.get(self.cookie_name)
        if not existing_token or not self._verify_token_signature(existing_token):
            token = self._generate_csrf_token()
        else:
            token = existing_token
        
        # Set cookie
        response.set_cookie(
            key=self.cookie_name,
            value=token,
            path=self.cookie_path,
            domain=self.cookie_domain,
            secure=self.cookie_secure,
            httponly=self.cookie_httponly,
            samesite=self.cookie_samesite,
            max_age=3600  # 1 hour
        )

def create_security_middleware(
    environment: str = "production",
    csrf_secret_key: Optional[str] = None,
    **kwargs
) -> tuple:
    """Create and configure security middleware"""
    
    # Security headers middleware
    security_headers = SecurityHeadersMiddleware(
        environment=environment,
        **kwargs
    )
    
    # CSRF protection middleware (if secret key provided)
    csrf_middleware = None
    if csrf_secret_key:
        csrf_middleware = CSRFProtectionMiddleware(
            secret_key=csrf_secret_key,
            cookie_secure=environment == "production"
        )
    
    return security_headers, csrf_middleware