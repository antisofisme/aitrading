"""
Authentication Service - Enterprise-grade security implementation
Handles password hashing, JWT tokens, session management, and 2FA
"""

import asyncio
import hashlib
import secrets
import uuid
import pyotp
import qrcode
import io
import base64
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from jose import jwt, JWTError
from passlib.context import CryptContext
from passlib.hash import bcrypt

# PER-SERVICE INFRASTRUCTURE INTEGRATION
from ...shared.infrastructure.base.base_error_handler import BaseErrorHandler, ErrorCategory
from ...shared.infrastructure.base.base_performance import BasePerformance
from .base_domain_service import BaseDomainService, ServiceResult, ServiceContext
from ..models.user_models import UserCredentials, UserSession, SessionStatus

# Password context with bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # Strong security with 12 rounds
    bcrypt__ident="2b"   # Latest bcrypt variant
)

@dataclass
class TokenPair:
    """JWT token pair"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600  # 1 hour
    refresh_expires_in: int = 2592000  # 30 days

@dataclass 
class LoginResult:
    """Login operation result"""
    success: bool
    user_id: Optional[str] = None
    tokens: Optional[TokenPair] = None
    session_id: Optional[str] = None
    requires_2fa: bool = False
    lockout_remaining: Optional[int] = None
    error_message: Optional[str] = None

@dataclass
class AuthContext:
    """Authentication context"""
    user_id: str
    session_id: str
    ip_address: str
    user_agent: str
    permissions: List[str]
    is_admin: bool = False
    expires_at: datetime = None

class AuthenticationService(BaseDomainService):
    """
    Enterprise Authentication Service with:
    - bcrypt password hashing with configurable rounds
    - JWT access/refresh token system
    - Session management with Redis
    - Account lockout protection
    - Two-factor authentication (TOTP)
    - Comprehensive audit logging
    - Rate limiting and brute force protection
    """
    
    def __init__(self):
        super().__init__("authentication")
        
        # Security configuration
        self.JWT_SECRET_KEY = None
        self.JWT_ALGORITHM = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES = 60
        self.REFRESH_TOKEN_EXPIRE_DAYS = 30
        self.MAX_LOGIN_ATTEMPTS = 5
        self.LOCKOUT_DURATION_MINUTES = 30
        self.SESSION_TIMEOUT_MINUTES = 480  # 8 hours
        self.PASSWORD_HISTORY_LENGTH = 5
        
        # Rate limiting
        self.login_attempt_window = 900  # 15 minutes
        self.max_attempts_per_window = 10
        
    async def _initialize_service(self):
        """Initialize authentication service"""
        try:
            # Load security configuration
            auth_config = self.config.get('authentication', {})
            self.JWT_SECRET_KEY = auth_config.get('jwt_secret') or secrets.token_urlsafe(32)
            self.ACCESS_TOKEN_EXPIRE_MINUTES = auth_config.get('jwt_expiry_hours', 1) * 60
            self.REFRESH_TOKEN_EXPIRE_DAYS = auth_config.get('refresh_token_expiry_days', 30)
            
            security_config = self.config.get('security', {})
            self.MAX_LOGIN_ATTEMPTS = security_config.get('max_failed_login_attempts', 5)
            self.LOCKOUT_DURATION_MINUTES = security_config.get('lockout_duration_minutes', 30)
            
            # Initialize Redis for session management
            await self._initialize_redis()
            
            self.logger.info("AuthenticationService initialized with enterprise security", context={
                "access_token_minutes": self.ACCESS_TOKEN_EXPIRE_MINUTES,
                "refresh_token_days": self.REFRESH_TOKEN_EXPIRE_DAYS,
                "max_login_attempts": self.MAX_LOGIN_ATTEMPTS,
                "lockout_duration": self.LOCKOUT_DURATION_MINUTES
            })
            
        except Exception as e:
            error_response = self.error_handler.handle_error(
                e,
                ErrorCategory.SERVICE_ERROR,
                {"operation": "initialize_auth_service"}
            )
            self.logger.error("Authentication service initialization failed", context={"error": error_response.to_dict()})
            raise
    
    async def _initialize_redis(self):
        """Initialize Redis connection for session management"""
        try:
            cache_config = self.config.get('cache', {})
            # Redis connection will be handled by the base cache infrastructure
            self.redis_prefix = "auth:"
            self.session_prefix = f"{self.redis_prefix}session:"
            self.rate_limit_prefix = f"{self.redis_prefix}rate_limit:"
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Redis: {str(e)}")
            raise
    
    # Password Security with bcrypt
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt with salt"""
        try:
            return pwd_context.hash(password)
        except Exception as e:
            self.logger.error(f"Password hashing failed: {str(e)}")
            raise ValueError("Password hashing failed")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against bcrypt hash"""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            self.logger.error(f"Password verification failed: {str(e)}")
            return False
    
    def needs_rehash(self, hashed_password: str) -> bool:
        """Check if password needs rehashing (for algorithm updates)"""
        return pwd_context.needs_update(hashed_password)
    
    # JWT Token Management
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.JWT_SECRET_KEY, algorithm=self.JWT_ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh",
            "jti": str(uuid.uuid4())  # JWT ID for token revocation
        })
        
        encoded_jwt = jwt.encode(to_encode, self.JWT_SECRET_KEY, algorithm=self.JWT_ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.JWT_SECRET_KEY, algorithms=[self.JWT_ALGORITHM])
            
            # Verify token type
            if payload.get("type") != token_type:
                return None
                
            return payload
            
        except JWTError as e:
            self.logger.warning(f"JWT verification failed: {str(e)}")
            return None
    
    async def create_token_pair(self, user_id: str, session_id: str, permissions: List[str]) -> TokenPair:
        """Create access and refresh token pair"""
        token_data = {
            "sub": user_id,
            "session_id": session_id,
            "permissions": permissions
        }
        
        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token(token_data)
        
        # Store refresh token in Redis for revocation capability
        await self.set_cached(
            f"{self.redis_prefix}refresh_token:{user_id}:{session_id}",
            {
                "token": refresh_token,
                "created_at": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "session_id": session_id
            },
            ttl=self.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600  # Convert to seconds
        )
        
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_expires_in=self.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
        )
    
    # Authentication Operations
    async def authenticate_user(
        self,
        email: str,
        password: str,
        ip_address: str,
        user_agent: str,
        totp_code: Optional[str] = None,
        context: Optional[ServiceContext] = None
    ) -> ServiceResult[LoginResult]:
        """Authenticate user with comprehensive security checks"""
        
        async def _authenticate_operation():
            # Rate limiting check
            rate_limit_key = f"{self.rate_limit_prefix}{ip_address}"
            current_attempts = await self.get_cached(rate_limit_key) or 0
            
            if current_attempts >= self.max_attempts_per_window:
                await self._log_security_event("rate_limit_exceeded", {
                    "ip_address": ip_address,
                    "attempts": current_attempts
                })
                return LoginResult(
                    success=False,
                    error_message="Rate limit exceeded. Please try again later."
                )
            
            # Get user credentials
            async with await self.get_db_connection() as conn:
                user_cred_record = await conn.fetchrow("""
                    SELECT uc.*, u.email, u.full_name, u.role, u.is_active
                    FROM user_credentials uc
                    JOIN users u ON uc.user_id = u.user_id
                    WHERE u.email = $1
                """, email)
                
                if not user_cred_record:
                    # Increment rate limiting counter
                    await self._increment_rate_limit(ip_address)
                    await self._log_security_event("login_failed_user_not_found", {
                        "email": email,
                        "ip_address": ip_address
                    })
                    return LoginResult(
                        success=False,
                        error_message="Invalid credentials"
                    )
                
                user_cred = UserCredentials(
                    user_id=user_cred_record["user_id"],
                    username=user_cred_record["username"],
                    password_hash=user_cred_record["password_hash"],
                    salt=user_cred_record["salt"],
                    last_password_change=user_cred_record["last_password_change"],
                    failed_login_attempts=user_cred_record["failed_login_attempts"],
                    locked_until=user_cred_record["locked_until"],
                    two_factor_enabled=user_cred_record["two_factor_enabled"],
                    two_factor_secret=user_cred_record["two_factor_secret"],
                    recovery_codes=user_cred_record["recovery_codes"] or []
                )
                
                # Check if account is locked
                if user_cred.is_locked:
                    lockout_remaining = int((user_cred.locked_until - datetime.utcnow()).total_seconds())
                    await self._log_security_event("login_failed_account_locked", {
                        "user_id": user_cred.user_id,
                        "email": email,
                        "ip_address": ip_address,
                        "lockout_remaining": lockout_remaining
                    })
                    return LoginResult(
                        success=False,
                        lockout_remaining=lockout_remaining,
                        error_message=f"Account locked. Try again in {lockout_remaining} seconds."
                    )
                
                # Verify password
                if not self.verify_password(password, user_cred.password_hash):
                    # Increment failed attempts
                    new_attempts = user_cred.failed_login_attempts + 1
                    
                    # Lock account if max attempts reached
                    locked_until = None
                    if new_attempts >= self.MAX_LOGIN_ATTEMPTS:
                        locked_until = datetime.utcnow() + timedelta(minutes=self.LOCKOUT_DURATION_MINUTES)
                    
                    await conn.execute("""
                        UPDATE user_credentials 
                        SET failed_login_attempts = $1, locked_until = $2
                        WHERE user_id = $3
                    """, new_attempts, locked_until, user_cred.user_id)
                    
                    await self._increment_rate_limit(ip_address)
                    await self._log_security_event("login_failed_invalid_password", {
                        "user_id": user_cred.user_id,
                        "email": email,
                        "ip_address": ip_address,
                        "failed_attempts": new_attempts
                    })
                    
                    return LoginResult(
                        success=False,
                        error_message="Invalid credentials"
                    )
                
                # Check if user account is active
                if not user_cred_record["is_active"]:
                    await self._log_security_event("login_failed_inactive_account", {
                        "user_id": user_cred.user_id,
                        "email": email,
                        "ip_address": ip_address
                    })
                    return LoginResult(
                        success=False,
                        error_message="Account is inactive"
                    )
                
                # Two-factor authentication check
                if user_cred.two_factor_enabled:
                    if not totp_code:
                        return LoginResult(
                            success=False,
                            requires_2fa=True,
                            error_message="Two-factor authentication required"
                        )
                    
                    if not self._verify_totp(user_cred.two_factor_secret, totp_code):
                        await self._increment_rate_limit(ip_address)
                        await self._log_security_event("login_failed_invalid_2fa", {
                            "user_id": user_cred.user_id,
                            "email": email,
                            "ip_address": ip_address
                        })
                        return LoginResult(
                            success=False,
                            error_message="Invalid two-factor authentication code"
                        )
                
                # Successful login - reset failed attempts
                await conn.execute("""
                    UPDATE user_credentials 
                    SET failed_login_attempts = 0, locked_until = NULL
                    WHERE user_id = $1
                """, user_cred.user_id)
                
                # Update last login
                await conn.execute("""
                    UPDATE users SET last_login = NOW()
                    WHERE user_id = $1
                """, user_cred.user_id)
                
                # Create session
                session_id = str(uuid.uuid4())
                session = UserSession(
                    session_id=session_id,
                    user_id=user_cred.user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    expires_at=datetime.utcnow() + timedelta(minutes=self.SESSION_TIMEOUT_MINUTES)
                )
                
                # Store session in Redis
                await self._store_session(session)
                
                # Get user permissions
                permissions = await self._get_user_permissions(user_cred.user_id)
                
                # Create token pair
                tokens = await self.create_token_pair(user_cred.user_id, session_id, permissions)
                
                # Reset rate limiting for successful login
                await self.invalidate_cache(rate_limit_key)
                
                await self._log_security_event("login_successful", {
                    "user_id": user_cred.user_id,
                    "email": email,
                    "ip_address": ip_address,
                    "session_id": session_id
                })
                
                return LoginResult(
                    success=True,
                    user_id=user_cred.user_id,
                    tokens=tokens,
                    session_id=session_id
                )
        
        return await self.execute_with_context(
            "authenticate_user",
            context or ServiceContext(user_id="system"),
            _authenticate_operation
        )
    
    async def refresh_access_token(
        self,
        refresh_token: str,
        context: Optional[ServiceContext] = None
    ) -> ServiceResult[TokenPair]:
        """Refresh access token using refresh token"""
        
        async def _refresh_token_operation():
            # Verify refresh token
            payload = self.verify_token(refresh_token, "refresh")
            if not payload:
                return None
            
            user_id = payload.get("sub")
            session_id = payload.get("session_id")
            jti = payload.get("jti")
            
            # Check if refresh token exists in Redis
            stored_token_data = await self.get_cached(f"{self.redis_prefix}refresh_token:{user_id}:{session_id}")
            if not stored_token_data or stored_token_data.get("token") != refresh_token:
                await self._log_security_event("refresh_token_invalid", {
                    "user_id": user_id,
                    "session_id": session_id
                })
                return None
            
            # Verify session is still valid
            session_data = await self.get_cached(f"{self.session_prefix}{session_id}")
            if not session_data:
                return None
            
            # Get fresh user permissions
            permissions = await self._get_user_permissions(user_id)
            
            # Create new token pair
            new_tokens = await self.create_token_pair(user_id, session_id, permissions)
            
            await self._log_security_event("token_refreshed", {
                "user_id": user_id,
                "session_id": session_id
            })
            
            return new_tokens
        
        return await self.execute_with_context(
            "refresh_token",
            context or ServiceContext(user_id="system"),
            _refresh_token_operation
        )
    
    # Session Management
    async def _store_session(self, session: UserSession):
        """Store session in Redis"""
        session_data = {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "ip_address": session.ip_address,
            "user_agent": session.user_agent,
            "created_at": session.created_at.isoformat(),
            "expires_at": session.expires_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "status": session.status.value
        }
        
        ttl = int((session.expires_at - datetime.utcnow()).total_seconds())
        await self.set_cached(f"{self.session_prefix}{session.session_id}", session_data, ttl=ttl)
    
    async def get_session(self, session_id: str) -> Optional[UserSession]:
        """Get session from Redis"""
        session_data = await self.get_cached(f"{self.session_prefix}{session_id}")
        if not session_data:
            return None
        
        return UserSession(
            session_id=session_data["session_id"],
            user_id=session_data["user_id"],
            ip_address=session_data["ip_address"],
            user_agent=session_data["user_agent"],
            created_at=datetime.fromisoformat(session_data["created_at"]),
            expires_at=datetime.fromisoformat(session_data["expires_at"]),
            last_activity=datetime.fromisoformat(session_data["last_activity"]),
            status=SessionStatus(session_data["status"])
        )
    
    async def invalidate_session(self, session_id: str):
        """Invalidate session"""
        await self.invalidate_cache(f"{self.session_prefix}{session_id}")
        
        await self._log_security_event("session_invalidated", {
            "session_id": session_id
        })
    
    async def extend_session(self, session_id: str, hours: int = 8):
        """Extend session expiration"""
        session = await self.get_session(session_id)
        if session and session.is_valid:
            session.extend_session(hours)
            await self._store_session(session)
    
    # Two-Factor Authentication
    def generate_2fa_secret(self) -> str:
        """Generate TOTP secret for 2FA"""
        return pyotp.random_base32()
    
    def generate_2fa_qr_code(self, user_email: str, secret: str, issuer: str = "Trading Platform") -> str:
        """Generate QR code for 2FA setup"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name=issuer
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        return base64.b64encode(img_buffer.getvalue()).decode()
    
    def _verify_totp(self, secret: str, token: str) -> bool:
        """Verify TOTP token"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)  # Allow 1 window tolerance
    
    async def enable_2fa(self, user_id: str, secret: str, token: str) -> bool:
        """Enable 2FA for user after verifying setup token"""
        if not self._verify_totp(secret, token):
            return False
        
        # Generate recovery codes
        recovery_codes = [secrets.token_urlsafe(8) for _ in range(8)]
        
        async with await self.get_db_connection() as conn:
            await conn.execute("""
                UPDATE user_credentials 
                SET two_factor_enabled = true, 
                    two_factor_secret = $1,
                    recovery_codes = $2
                WHERE user_id = $3
            """, secret, recovery_codes, user_id)
        
        await self._log_security_event("2fa_enabled", {
            "user_id": user_id
        })
        
        return True
    
    async def disable_2fa(self, user_id: str, password: str) -> bool:
        """Disable 2FA for user after password verification"""
        async with await self.get_db_connection() as conn:
            cred_record = await conn.fetchrow("""
                SELECT password_hash FROM user_credentials WHERE user_id = $1
            """, user_id)
            
            if not cred_record or not self.verify_password(password, cred_record["password_hash"]):
                return False
            
            await conn.execute("""
                UPDATE user_credentials 
                SET two_factor_enabled = false, 
                    two_factor_secret = NULL,
                    recovery_codes = NULL
                WHERE user_id = $1
            """, user_id)
        
        await self._log_security_event("2fa_disabled", {
            "user_id": user_id
        })
        
        return True
    
    # Helper Methods
    async def _get_user_permissions(self, user_id: str) -> List[str]:
        """Get user permissions from database"""
        async with await self.get_db_connection() as conn:
            result = await conn.fetchrow("""
                SELECT role FROM users WHERE user_id = $1
            """, user_id)
            
            if not result:
                return []
            
            # Map roles to permissions (this should be configurable)
            role_permissions = {
                "admin": ["*"],
                "trader": ["trade:*", "portfolio:*", "market:read"],
                "user": ["portfolio:read", "market:read"],
                "viewer": ["market:read"]
            }
            
            return role_permissions.get(result["role"], [])
    
    async def _increment_rate_limit(self, identifier: str):
        """Increment rate limiting counter"""
        key = f"{self.rate_limit_prefix}{identifier}"
        current = await self.get_cached(key) or 0
        await self.set_cached(key, current + 1, ttl=self.login_attempt_window)
    
    async def _log_security_event(self, event_type: str, data: Dict[str, Any]):
        """Log security events for audit trail"""
        security_event = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
            "service": "user-service-auth"
        }
        
        self.logger.info(f"Security Event: {event_type}", context=security_event)
        
        # Store in audit log
        try:
            async with await self.get_db_connection() as conn:
                await conn.execute("""
                    INSERT INTO security_audit_log (event_type, event_data, created_at)
                    VALUES ($1, $2, NOW())
                """, event_type, security_event)
        except Exception as e:
            self.logger.error(f"Failed to store security audit log: {str(e)}")
    
    # Additional Authentication Methods
    async def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str
    ) -> bool:
        """Change user password with security checks"""
        try:
            async with await self.get_db_connection() as conn:
                # Get current credentials
                cred_record = await conn.fetchrow("""
                    SELECT password_hash, password_history
                    FROM user_credentials WHERE user_id = $1
                """, user_id)
                
                if not cred_record:
                    return False
                
                # Verify current password
                if not self.verify_password(current_password, cred_record["password_hash"]):
                    await self._log_security_event("password_change_failed_invalid_current", {
                        "user_id": user_id
                    })
                    return False
                
                # Check password history to prevent reuse
                new_password_hash = self.hash_password(new_password)
                password_history = cred_record["password_history"] or []
                
                if new_password_hash in password_history:
                    await self._log_security_event("password_change_failed_reused", {
                        "user_id": user_id
                    })
                    return False
                
                # Add current password to history and update
                await conn.execute("""
                    SELECT add_to_password_history($1, $2, $3)
                """, user_id, cred_record["password_hash"], self.PASSWORD_HISTORY_LENGTH)
                
                # Update password
                await conn.execute("""
                    UPDATE user_credentials 
                    SET password_hash = $1, last_password_change = NOW()
                    WHERE user_id = $2
                """, new_password_hash, user_id)
                
                await self._log_security_event("password_changed", {
                    "user_id": user_id
                })
                
                return True
                
        except Exception as e:
            self.logger.error(f"Password change failed: {str(e)}")
            return False
    
    async def get_user_sessions(self, user_id: str) -> List[UserSession]:
        """Get all active sessions for a user"""
        try:
            # Get sessions from Redis first, fallback to database
            sessions = []
            
            # For now, we'll implement database lookup
            # In production, Redis would be primary storage
            async with await self.get_db_connection() as conn:
                session_records = await conn.fetch("""
                    SELECT * FROM user_sessions 
                    WHERE user_id = $1 AND status = 'active' AND expires_at > NOW()
                    ORDER BY last_activity DESC
                """, user_id)
                
                for record in session_records:
                    sessions.append(UserSession(
                        session_id=record["session_id"],
                        user_id=record["user_id"],
                        ip_address=record["ip_address"],
                        user_agent=record["user_agent"],
                        created_at=record["created_at"],
                        expires_at=record["expires_at"],
                        last_activity=record["last_activity"],
                        status=SessionStatus(record["status"])
                    ))
            
            return sessions
            
        except Exception as e:
            self.logger.error(f"Failed to get user sessions: {str(e)}")
            return []
    
    async def request_password_reset(self, email: str, ip_address: str) -> bool:
        """Request password reset token"""
        try:
            async with await self.get_db_connection() as conn:
                # Check if user exists
                user_record = await conn.fetchrow("""
                    SELECT user_id FROM users WHERE email = $1 AND is_active = true
                """, email)
                
                if not user_record:
                    # Log attempt but don't reveal if email exists
                    await self._log_security_event("password_reset_attempt_invalid_email", {
                        "email": email,
                        "ip_address": ip_address
                    })
                    return True  # Always return True to prevent enumeration
                
                # Generate reset token
                reset_token = secrets.token_urlsafe(32)
                token_hash = hashlib.sha256(reset_token.encode()).hexdigest()
                
                # Store reset token
                expires_at = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
                
                await conn.execute("""
                    INSERT INTO password_reset_tokens 
                    (user_id, token_hash, expires_at, ip_address)
                    VALUES ($1, $2, $3, $4)
                """, user_record["user_id"], token_hash, expires_at, ip_address)
                
                await self._log_security_event("password_reset_requested", {
                    "user_id": user_record["user_id"],
                    "email": email,
                    "ip_address": ip_address
                })
                
                # In production, send email with reset_token
                # For now, we'll just log it
                self.logger.info(f"Password reset token: {reset_token}")
                
                return True
                
        except Exception as e:
            self.logger.error(f"Password reset request failed: {str(e)}")
            return True  # Don't reveal errors
    
    async def confirm_password_reset(
        self,
        reset_token: str,
        new_password: str,
        ip_address: str
    ) -> bool:
        """Confirm password reset with token"""
        try:
            token_hash = hashlib.sha256(reset_token.encode()).hexdigest()
            
            async with await self.get_db_connection() as conn:
                # Get reset token
                token_record = await conn.fetchrow("""
                    SELECT prt.*, u.email
                    FROM password_reset_tokens prt
                    JOIN users u ON prt.user_id = u.user_id
                    WHERE prt.token_hash = $1 
                    AND prt.expires_at > NOW()
                    AND prt.is_used = false
                """, token_hash)
                
                if not token_record:
                    await self._log_security_event("password_reset_failed_invalid_token", {
                        "token_hash": token_hash,
                        "ip_address": ip_address
                    })
                    return False
                
                # Hash new password
                new_password_hash = self.hash_password(new_password)
                
                # Update password
                await conn.execute("""
                    UPDATE user_credentials 
                    SET password_hash = $1, 
                        last_password_change = NOW(),
                        failed_login_attempts = 0,
                        locked_until = NULL
                    WHERE user_id = $2
                """, new_password_hash, token_record["user_id"])
                
                # Mark token as used
                await conn.execute("""
                    UPDATE password_reset_tokens 
                    SET is_used = true, used_at = NOW()
                    WHERE token_hash = $1
                """, token_hash)
                
                await self._log_security_event("password_reset_completed", {
                    "user_id": token_record["user_id"],
                    "email": token_record["email"],
                    "ip_address": ip_address
                })
                
                return True
                
        except Exception as e:
            self.logger.error(f"Password reset confirmation failed: {str(e)}")
            return False