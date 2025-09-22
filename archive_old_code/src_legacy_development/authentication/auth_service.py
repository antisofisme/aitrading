"""
Enhanced Authentication Service for AI Trading Platform
Level 2 Connectivity - Authentication Implementation
"""

import asyncio
import logging
import time
import jwt
import bcrypt
import redis.asyncio as redis
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import secrets
import hashlib
from dataclasses import dataclass
from enum import Enum
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserTier(Enum):
    """User subscription tiers"""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class UserRole(Enum):
    """User roles and permissions"""
    USER = "user"
    ADMIN = "admin"
    TRADER = "trader"
    ANALYST = "analyst"

@dataclass
class TokenData:
    """JWT token data structure"""
    user_id: str
    username: str
    email: str
    tier: UserTier
    role: UserRole
    permissions: List[str]
    expires_at: datetime

@dataclass
class RateLimitInfo:
    """Rate limiting information"""
    requests_per_minute: int
    requests_per_hour: int
    current_usage: int
    reset_time: datetime

# Database Models
Base = declarative_base()

class User(Base):
    """User database model"""
    __tablename__ = "users"

    id = sa.Column(sa.String, primary_key=True)
    username = sa.Column(sa.String(50), unique=True, nullable=False)
    email = sa.Column(sa.String(255), unique=True, nullable=False)
    password_hash = sa.Column(sa.String(255), nullable=False)
    tier = sa.Column(sa.Enum(UserTier), default=UserTier.FREE)
    role = sa.Column(sa.Enum(UserRole), default=UserRole.USER)
    is_active = sa.Column(sa.Boolean, default=True)
    is_verified = sa.Column(sa.Boolean, default=False)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    last_login = sa.Column(sa.DateTime)
    api_key = sa.Column(sa.String(255), unique=True)
    metadata = sa.Column(sa.JSON, default=dict)

class UserSession(Base):
    """User session tracking"""
    __tablename__ = "user_sessions"

    id = sa.Column(sa.String, primary_key=True)
    user_id = sa.Column(sa.String, sa.ForeignKey("users.id"))
    token_jti = sa.Column(sa.String(255), unique=True)  # JWT ID
    device_info = sa.Column(sa.String(500))
    ip_address = sa.Column(sa.String(45))
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    expires_at = sa.Column(sa.DateTime)
    is_revoked = sa.Column(sa.Boolean, default=False)

# Pydantic Models
class UserRegistration(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(..., min_length=8)
    tier: UserTier = UserTier.FREE
    metadata: Dict[str, Any] = {}

class UserLogin(BaseModel):
    username_or_email: str
    password: str
    device_info: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_info: Dict[str, Any]

class UserProfile(BaseModel):
    id: str
    username: str
    email: str
    tier: UserTier
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]
    metadata: Dict[str, Any]

class AuthConfig:
    """Authentication configuration"""
    JWT_SECRET_KEY = "your-super-secret-jwt-key-change-in-production"
    JWT_ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60
    REFRESH_TOKEN_EXPIRE_DAYS = 30

    # Rate limiting per tier
    RATE_LIMITS = {
        UserTier.FREE: {"requests_per_minute": 10, "requests_per_hour": 100},
        UserTier.PRO: {"requests_per_minute": 100, "requests_per_hour": 2000},
        UserTier.ENTERPRISE: {"requests_per_minute": 1000, "requests_per_hour": 50000}
    }

    # Permissions per role
    ROLE_PERMISSIONS = {
        UserRole.USER: ["read_predictions", "basic_trading"],
        UserRole.TRADER: ["read_predictions", "basic_trading", "advanced_trading", "create_strategies"],
        UserRole.ANALYST: ["read_predictions", "basic_trading", "view_analytics", "export_data"],
        UserRole.ADMIN: ["*"]  # All permissions
    }

class PasswordManager:
    """Secure password management"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

    @staticmethod
    def generate_api_key() -> str:
        """Generate secure API key"""
        return f"at_{secrets.token_urlsafe(32)}"

class JWTManager:
    """JWT token management"""

    def __init__(self, config: AuthConfig):
        self.config = config

    def create_access_token(self, user: User) -> str:
        """Create JWT access token"""
        now = datetime.utcnow()
        expires = now + timedelta(minutes=self.config.ACCESS_TOKEN_EXPIRE_MINUTES)

        payload = {
            "sub": user.id,
            "username": user.username,
            "email": user.email,
            "tier": user.tier.value,
            "role": user.role.value,
            "permissions": self.config.ROLE_PERMISSIONS[user.role],
            "iat": now,
            "exp": expires,
            "jti": secrets.token_urlsafe(16)  # JWT ID for revocation
        }

        return jwt.encode(payload, self.config.JWT_SECRET_KEY, algorithm=self.config.JWT_ALGORITHM)

    def create_refresh_token(self, user: User) -> str:
        """Create JWT refresh token"""
        now = datetime.utcnow()
        expires = now + timedelta(days=self.config.REFRESH_TOKEN_EXPIRE_DAYS)

        payload = {
            "sub": user.id,
            "type": "refresh",
            "iat": now,
            "exp": expires,
            "jti": secrets.token_urlsafe(16)
        }

        return jwt.encode(payload, self.config.JWT_SECRET_KEY, algorithm=self.config.JWT_ALGORITHM)

    def decode_token(self, token: str) -> TokenData:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(token, self.config.JWT_SECRET_KEY, algorithms=[self.config.JWT_ALGORITHM])

            return TokenData(
                user_id=payload["sub"],
                username=payload.get("username", ""),
                email=payload.get("email", ""),
                tier=UserTier(payload.get("tier", "free")),
                role=UserRole(payload.get("role", "user")),
                permissions=payload.get("permissions", []),
                expires_at=datetime.fromtimestamp(payload["exp"])
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

class RateLimiter:
    """Redis-based rate limiting"""

    def __init__(self, redis_client: redis.Redis, config: AuthConfig):
        self.redis = redis_client
        self.config = config

    async def check_rate_limit(self, user_id: str, tier: UserTier) -> RateLimitInfo:
        """Check and enforce rate limiting"""
        limits = self.config.RATE_LIMITS[tier]
        current_time = int(time.time())

        # Check minute limit
        minute_key = f"rate_limit:minute:{user_id}:{current_time // 60}"
        hour_key = f"rate_limit:hour:{user_id}:{current_time // 3600}"

        pipe = self.redis.pipeline()
        pipe.incr(minute_key)
        pipe.expire(minute_key, 60)
        pipe.incr(hour_key)
        pipe.expire(hour_key, 3600)
        results = await pipe.execute()

        minute_count = results[0]
        hour_count = results[2]

        # Check limits
        if minute_count > limits["requests_per_minute"]:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {limits['requests_per_minute']} requests per minute"
            )

        if hour_count > limits["requests_per_hour"]:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {limits['requests_per_hour']} requests per hour"
            )

        return RateLimitInfo(
            requests_per_minute=limits["requests_per_minute"],
            requests_per_hour=limits["requests_per_hour"],
            current_usage=minute_count,
            reset_time=datetime.fromtimestamp(((current_time // 60) + 1) * 60)
        )

class AuthenticationService:
    """Main authentication service"""

    def __init__(self, database_url: str, redis_url: str):
        self.config = AuthConfig()
        self.password_manager = PasswordManager()
        self.jwt_manager = JWTManager(self.config)

        # Database setup
        self.engine = create_async_engine(database_url)
        self.SessionLocal = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

        # Redis setup
        self.redis_client = None
        self.redis_url = redis_url

        # Rate limiter
        self.rate_limiter = None

        logger.info("Authentication service initialized")

    async def initialize(self):
        """Initialize async components"""
        try:
            # Initialize Redis
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()

            # Initialize rate limiter
            self.rate_limiter = RateLimiter(self.redis_client, self.config)

            # Create tables
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            logger.info("Authentication service fully initialized")

        except Exception as e:
            logger.error(f"Failed to initialize authentication service: {e}")
            raise

    async def register_user(self, registration: UserRegistration) -> UserProfile:
        """Register new user"""
        async with self.SessionLocal() as session:
            try:
                # Check if user exists
                existing_user = await session.execute(
                    sa.select(User).where(
                        (User.username == registration.username) |
                        (User.email == registration.email)
                    )
                )
                if existing_user.scalar_one_or_none():
                    raise HTTPException(status_code=400, detail="Username or email already exists")

                # Create new user
                user_id = hashlib.md5(f"{registration.username}{time.time()}".encode()).hexdigest()[:16]
                password_hash = self.password_manager.hash_password(registration.password)
                api_key = self.password_manager.generate_api_key()

                new_user = User(
                    id=user_id,
                    username=registration.username,
                    email=registration.email,
                    password_hash=password_hash,
                    tier=registration.tier,
                    api_key=api_key,
                    metadata=registration.metadata
                )

                session.add(new_user)
                await session.commit()
                await session.refresh(new_user)

                logger.info(f"User registered: {registration.username}")

                return UserProfile(
                    id=new_user.id,
                    username=new_user.username,
                    email=new_user.email,
                    tier=new_user.tier,
                    role=new_user.role,
                    is_active=new_user.is_active,
                    is_verified=new_user.is_verified,
                    created_at=new_user.created_at,
                    last_login=new_user.last_login,
                    metadata=new_user.metadata
                )

            except Exception as e:
                await session.rollback()
                logger.error(f"User registration failed: {e}")
                raise

    async def authenticate_user(self, login: UserLogin, ip_address: str = None) -> TokenResponse:
        """Authenticate user and create session"""
        async with self.SessionLocal() as session:
            try:
                # Find user
                user = await session.execute(
                    sa.select(User).where(
                        (User.username == login.username_or_email) |
                        (User.email == login.username_or_email)
                    )
                )
                user = user.scalar_one_or_none()

                if not user or not self.password_manager.verify_password(login.password, user.password_hash):
                    raise HTTPException(status_code=401, detail="Invalid credentials")

                if not user.is_active:
                    raise HTTPException(status_code=401, detail="Account is disabled")

                # Create tokens
                access_token = self.jwt_manager.create_access_token(user)
                refresh_token = self.jwt_manager.create_refresh_token(user)

                # Create session record
                token_data = self.jwt_manager.decode_token(access_token)
                session_id = secrets.token_urlsafe(16)

                user_session = UserSession(
                    id=session_id,
                    user_id=user.id,
                    token_jti=token_data.user_id,  # Use decoded data
                    device_info=login.device_info,
                    ip_address=ip_address,
                    expires_at=token_data.expires_at
                )

                session.add(user_session)

                # Update last login
                user.last_login = datetime.utcnow()
                await session.commit()

                logger.info(f"User authenticated: {user.username}")

                return TokenResponse(
                    access_token=access_token,
                    refresh_token=refresh_token,
                    expires_in=self.config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                    user_info={
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "tier": user.tier.value,
                        "role": user.role.value
                    }
                )

            except Exception as e:
                await session.rollback()
                logger.error(f"Authentication failed: {e}")
                raise

    async def validate_token(self, token: str) -> TokenData:
        """Validate JWT token"""
        token_data = self.jwt_manager.decode_token(token)

        # Check if session is still valid
        async with self.SessionLocal() as session:
            user_session = await session.execute(
                sa.select(UserSession).where(
                    (UserSession.user_id == token_data.user_id) &
                    (UserSession.expires_at > datetime.utcnow()) &
                    (UserSession.is_revoked == False)
                )
            )
            if not user_session.scalar_one_or_none():
                raise HTTPException(status_code=401, detail="Session invalid or expired")

        return token_data

    async def check_permission(self, token_data: TokenData, required_permission: str) -> bool:
        """Check if user has required permission"""
        if "*" in token_data.permissions:  # Admin has all permissions
            return True

        return required_permission in token_data.permissions

    async def revoke_token(self, user_id: str, token_jti: str = None):
        """Revoke user token(s)"""
        async with self.SessionLocal() as session:
            if token_jti:
                # Revoke specific token
                await session.execute(
                    sa.update(UserSession)
                    .where((UserSession.user_id == user_id) & (UserSession.token_jti == token_jti))
                    .values(is_revoked=True)
                )
            else:
                # Revoke all user tokens
                await session.execute(
                    sa.update(UserSession)
                    .where(UserSession.user_id == user_id)
                    .values(is_revoked=True)
                )

            await session.commit()
            logger.info(f"Tokens revoked for user: {user_id}")

    async def get_user_profile(self, user_id: str) -> UserProfile:
        """Get user profile"""
        async with self.SessionLocal() as session:
            user = await session.execute(sa.select(User).where(User.id == user_id))
            user = user.scalar_one_or_none()

            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            return UserProfile(
                id=user.id,
                username=user.username,
                email=user.email,
                tier=user.tier,
                role=user.role,
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=user.created_at,
                last_login=user.last_login,
                metadata=user.metadata
            )

    async def update_user_tier(self, user_id: str, new_tier: UserTier):
        """Update user subscription tier"""
        async with self.SessionLocal() as session:
            await session.execute(
                sa.update(User)
                .where(User.id == user_id)
                .values(tier=new_tier)
            )
            await session.commit()
            logger.info(f"User tier updated: {user_id} -> {new_tier.value}")

# FastAPI Dependencies
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthenticationService = Depends()
) -> TokenData:
    """FastAPI dependency to get current authenticated user"""
    token = credentials.credentials
    return await auth_service.validate_token(token)

async def require_permission(required_permission: str):
    """FastAPI dependency factory for permission checking"""
    def permission_checker(
        current_user: TokenData = Depends(get_current_user),
        auth_service: AuthenticationService = Depends()
    ):
        if not await auth_service.check_permission(current_user, required_permission):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user

    return permission_checker

async def check_rate_limit_dependency(
    current_user: TokenData = Depends(get_current_user),
    auth_service: AuthenticationService = Depends()
) -> RateLimitInfo:
    """FastAPI dependency for rate limiting"""
    if auth_service.rate_limiter:
        return await auth_service.rate_limiter.check_rate_limit(
            current_user.user_id,
            current_user.tier
        )
    return RateLimitInfo(
        requests_per_minute=1000,
        requests_per_hour=10000,
        current_usage=0,
        reset_time=datetime.utcnow() + timedelta(minutes=1)
    )

# Global auth service instance
auth_service = None

async def get_auth_service() -> AuthenticationService:
    """Get authentication service instance"""
    global auth_service
    if auth_service is None:
        auth_service = AuthenticationService(
            database_url="postgresql+asyncpg://trading_user:trading_pass@localhost/trading_db",
            redis_url="redis://localhost:6379"
        )
        await auth_service.initialize()
    return auth_service

# Export main components
__all__ = [
    'AuthenticationService',
    'UserRegistration',
    'UserLogin',
    'TokenResponse',
    'UserProfile',
    'TokenData',
    'RateLimitInfo',
    'UserTier',
    'UserRole',
    'get_current_user',
    'require_permission',
    'check_rate_limit_dependency',
    'get_auth_service'
]