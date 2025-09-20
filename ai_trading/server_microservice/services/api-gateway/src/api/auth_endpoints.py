"""
Authentication API Endpoints - Microservice Version with Per-Service Infrastructure
Enterprise-grade JWT authentication with role-based access control (RBAC) for API Gateway:
- Per-service authentication and authorization
- Gateway-level JWT token management
- Service-to-service authentication coordination
- Microservice user session management
- Per-service security validation and monitoring
"""

import uuid
import hashlib
import time
import jwt
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, EmailStr

# SHARED INFRASTRUCTURE INTEGRATION
from ....shared.infrastructure.base.base_error_handler import BaseErrorHandler
from ....shared.infrastructure.optional.event_core import EventCore as BaseEventPublisher
from ....shared.infrastructure.base.base_logger import BaseLogger
from ....shared.infrastructure.base.base_performance import BasePerformance as BasePerformanceTracker
from ....shared.infrastructure.optional.validation_core import ValidationCore as BaseValidator
from ....shared.infrastructure.base.base_config import BaseConfig

# Initialize per-service infrastructure
error_handler = BaseErrorHandler("api-gateway")
event_publisher = BaseEventPublisher("api-gateway")
logger = BaseLogger("api-gateway", "auth_endpoints")
performance_tracker = BasePerformanceTracker("api-gateway")
validator = BaseValidator("api-gateway")
config = BaseConfig("api-gateway")

# Import passlib with fallback
try:
    from passlib.context import CryptContext
    PASSLIB_AVAILABLE = True
except ImportError:
    PASSLIB_AVAILABLE = False
    CryptContext = None

router = APIRouter()
security = HTTPBearer()

# Authentication performance metrics
auth_metrics = {
    "total_auth_requests": 0,
    "successful_logins": 0,
    "failed_logins": 0,
    "successful_registrations": 0,
    "failed_registrations": 0,
    "token_validations": 0,
    "avg_auth_response_time_ms": 0,
    "events_published": 0,
    "security_violations": 0,
    "gateway_auth_requests": 0
}

# JWT Configuration
# Import configuration manager
from ...shared.infrastructure.config_manager import get_config_manager

config_manager = get_config_manager()
auth_config = config_manager.get_authentication_config()

# JWT Configuration - SECURE: No hardcoded fallback
JWT_SECRET_KEY = auth_config.get('jwt_secret', '')
if not JWT_SECRET_KEY.strip():
    raise RuntimeError(
        "CRITICAL: JWT_SECRET_KEY not configured. "
        "Set JWT_SECRET_KEY environment variable for secure authentication."
    )

JWT_ALGORITHM = auth_config.get('jwt_algorithm', 'HS256')
JWT_EXPIRATION_HOURS = auth_config.get('token_expire_minutes', 30) // 60  # Convert minutes to hours

# Password hashing
if PASSLIB_AVAILABLE:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
else:
    pwd_context = None

# User roles and permissions for microservices
MICROSERVICE_ROLE_PERMISSIONS = {
    "admin": [
        "user:create", "user:read", "user:update", "user:delete",
        "project:create", "project:read", "project:update", "project:delete",
        "ai:chat", "ai:analyze", "ai:workflow", "ai:admin",
        "analytics:read", "analytics:admin",
        "system:monitor", "system:admin",
        "gateway:admin", "service:access:all"
    ],
    "project_manager": [
        "user:read", "user:update",
        "project:create", "project:read", "project:update",
        "ai:chat", "ai:analyze", "ai:workflow",
        "analytics:read",
        "service:access:ai-orchestration", "service:access:data-bridge", 
        "service:access:ml-processing", "service:access:trading-engine"
    ],
    "developer": [
        "user:read", "user:update",
        "project:read", "project:update",
        "ai:chat", "ai:analyze", "ai:workflow",
        "service:access:ai-orchestration", "service:access:data-bridge", 
        "service:access:ml-processing"
    ],
    "user": [
        "user:read", "user:update",
        "project:read",
        "ai:chat", "ai:analyze",
        "service:access:ai-orchestration"
    ],
    "service": [
        "service:internal", "service:communicate"
    ]
}

# Service access mapping
SERVICE_ACCESS_PERMISSIONS = {
    "ai-orchestration": "service:access:ai-orchestration",
    "data-bridge": "service:access:data-bridge",
    "ml-processing": "service:access:ml-processing",
    "trading-engine": "service:access:trading-engine",
    "database-service": "service:access:database-service"
}

# In-memory user store (in production, this would be a database service call)
USERS_STORE = {}
SESSION_STORE = {}


# Request/Response Models
class UserRegister(BaseModel):
    """User registration request"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    full_name: str = Field(..., min_length=2, description="Full name")
    organization_id: Optional[str] = Field(None, description="Organization ID")
    role: str = Field("user", description="User role")


class UserLogin(BaseModel):
    """User login request"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="Password")
    remember_me: bool = Field(False, description="Extended session")


class ServiceAuthRequest(BaseModel):
    """Service-to-service authentication request"""
    service_id: str = Field(..., description="Service identifier")
    service_secret: str = Field(..., description="Service secret")
    requested_permissions: list = Field(default_factory=list, description="Requested permissions")


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    email: str
    full_name: str
    role: str
    permissions: list
    organization_id: Optional[str] = None
    gateway_session_id: str


class UserProfile(BaseModel):
    """User profile response"""
    user_id: str
    email: str
    full_name: str
    role: str
    organization_id: Optional[str]
    is_active: bool
    created_at: str
    last_login: Optional[str]
    permissions: list
    gateway_session_id: str


class PasswordChange(BaseModel):
    """Password change request"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")


# Utility Functions
def hash_password(password: str) -> str:
    """Hash password using bcrypt or fallback"""
    if PASSLIB_AVAILABLE and pwd_context:
        return pwd_context.hash(password)
    else:
        # Fallback to simple hashing (NOT for production)
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    if PASSLIB_AVAILABLE and pwd_context:
        return pwd_context.verify(plain_password, hashed_password)
    else:
        # Fallback to simple verification (NOT for production)
        import hashlib
        return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password


def create_access_token(user_data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = user_data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated user"""
    token = credentials.credentials
    
    # Check cached session first
    if token in SESSION_STORE:
        cached_user = SESSION_STORE[token]
        cached_user["token"] = token
        return cached_user
    
    # Decode token and get user
    payload = decode_access_token(token)
    user_id = payload.get("user_id")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Get user from store (in production, this would be a database service call)
    if user_id not in USERS_STORE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    user_data = USERS_STORE[user_id].copy()
    user_data["permissions"] = MICROSERVICE_ROLE_PERMISSIONS.get(user_data["role"], [])
    user_data["token"] = token
    
    # Cache user session
    SESSION_STORE[token] = user_data
    
    return user_data


def require_permission(permission: str):
    """Dependency to require specific permission"""
    def permission_checker(current_user: Dict = Depends(get_current_user)):
        if permission not in current_user.get("permissions", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required for gateway access"
            )
        return current_user
    return permission_checker


def require_service_access(service_name: str):
    """Dependency to require access to specific service"""
    def service_access_checker(current_user: Dict = Depends(get_current_user)):
        required_permission = SERVICE_ACCESS_PERMISSIONS.get(service_name, f"service:access:{service_name}")
        all_access = "service:access:all"
        
        user_permissions = current_user.get("permissions", [])
        if required_permission not in user_permissions and all_access not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access to service '{service_name}' not permitted"
            )
        return current_user
    return service_access_checker


# Authentication Endpoints
@router.post("/register", response_model=TokenResponse)
async def register_user(user_data: UserRegister):
    """
    Register new user with role-based permissions for microservices architecture
    """
    start_time = time.perf_counter()
    
    try:
        # Update metrics
        auth_metrics["total_auth_requests"] += 1
        auth_metrics["gateway_auth_requests"] += 1
        
        # Validate registration data
        validation_result = validator.validate_dict(
            data={
                "email": user_data.email,
                "password": user_data.password,
                "full_name": user_data.full_name,
                "role": user_data.role
            },
            schema={
                "email": {"type": "email", "required": True},
                "password": {"type": "string", "required": True, "min_length": 8},
                "full_name": {"type": "string", "required": True, "min_length": 2},
                "role": {"type": "string", "required": True}
            },
            context="user_registration"
        )
        
        if not validation_result['valid']:
            error_response = error_handler.handle_error(
                error=ValueError(f"User registration validation failed: {validation_result['errors']}"),
                error_category=ErrorCategory.VALIDATION_ERROR,
                context={
                    "component": "gateway_auth",
                    "operation": "user_registration",
                    "email": user_data.email,
                    "role": user_data.role
                }
            )
            logger.warning(f"Registration validation failed: {error_response}")
            
            auth_metrics["failed_registrations"] += 1
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Validation failed: {validation_result['errors']}"
            )
        
        # Publish registration attempt event
        event_publisher.publish_event(
            event_type="gateway_user_registration_attempted",
            data={
                "email": user_data.email,
                "role": user_data.role,
                "organization_id": user_data.organization_id,
                "timestamp": datetime.now().isoformat()
            },
            context="gateway_auth"
        )
        auth_metrics["events_published"] += 1
        
        # Validate role
        if user_data.role not in MICROSERVICE_ROLE_PERMISSIONS:
            error_response = error_handler.handle_error(
                error=ValueError(f"Invalid role: {user_data.role}"),
                error_category=ErrorCategory.VALIDATION_ERROR,
                context={
                    "component": "gateway_auth",
                    "operation": "validate_user_role",
                    "role": user_data.role,
                    "valid_roles": list(MICROSERVICE_ROLE_PERMISSIONS.keys())
                }
            )
            logger.warning(f"Invalid role provided: {error_response}")
            
            auth_metrics["failed_registrations"] += 1
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Available roles: {list(MICROSERVICE_ROLE_PERMISSIONS.keys())}"
            )
        
        # Check if user already exists
        for existing_user in USERS_STORE.values():
            if existing_user["email"] == user_data.email:
                error_response = error_handler.handle_error(
                    error=ValueError(f"Email already registered: {user_data.email}"),
                    error_category=ErrorCategory.VALIDATION_ERROR,
                    context={
                        "component": "gateway_auth",
                        "operation": "check_existing_user",
                        "email": user_data.email
                    }
                )
                logger.warning(f"Registration attempt with existing email: {error_response}")
                
                # Publish security event
                event_publisher.publish_event(
                    event_type="gateway_duplicate_registration_attempt",
                    data={
                        "email": user_data.email,
                        "timestamp": datetime.now().isoformat()
                    },
                    context="gateway_security"
                )
                auth_metrics["security_violations"] += 1
                
                auth_metrics["failed_registrations"] += 1
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already registered"
                )
        
        # Hash password and create user
        try:
            hashed_password = hash_password(user_data.password)
            user_id = str(uuid.uuid4())
            gateway_session_id = str(uuid.uuid4())
            
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                error_category=ErrorCategory.SYSTEM_ERROR,
                context={
                    "component": "password_hashing",
                    "operation": "hash_user_password"
                }
            )
            logger.error(f"Password hashing failed: {error_response}")
            
            auth_metrics["failed_registrations"] += 1
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration failed due to internal error"
            )
        
        # Store user (in production, this would be a database service call)
        USERS_STORE[user_id] = {
            "user_id": user_id,
            "email": user_data.email,
            "password_hash": hashed_password,
            "full_name": user_data.full_name,
            "role": user_data.role,
            "organization_id": user_data.organization_id,
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "gateway_session_id": gateway_session_id
        }
        
        # Create JWT token
        try:
            token_data = {
                "user_id": user_id,
                "email": user_data.email,
                "role": user_data.role,
                "gateway_session_id": gateway_session_id
            }
            
            expires_delta = timedelta(hours=JWT_EXPIRATION_HOURS)
            access_token = create_access_token(token_data, expires_delta)
            
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                error_category=ErrorCategory.SYSTEM_ERROR,
                context={
                    "component": "jwt_token_creation",
                    "operation": "create_registration_token"
                }
            )
            logger.error(f"Token creation failed: {error_response}")
            
            auth_metrics["failed_registrations"] += 1
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration completed but login token generation failed"
            )
        
        # Cache user session
        user_session = {
            "user_id": user_id,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "role": user_data.role,
            "organization_id": user_data.organization_id,
            "permissions": MICROSERVICE_ROLE_PERMISSIONS.get(user_data.role, []),
            "gateway_session_id": gateway_session_id,
            "created_at": datetime.now().isoformat()
        }
        SESSION_STORE[access_token] = user_session
        
        # Record registration performance
        processing_time = (time.perf_counter() - start_time) * 1000
        performance_tracker.record_operation(
            operation_name="gateway_user_registration",
            duration_ms=processing_time,
            success=True,
            metadata={
                "email": user_data.email,
                "role": user_data.role,
                "organization_id": user_data.organization_id
            }
        )
        
        # Update success metrics
        auth_metrics["successful_registrations"] += 1
        current_avg = auth_metrics["avg_auth_response_time_ms"]
        total_requests = auth_metrics["total_auth_requests"]
        auth_metrics["avg_auth_response_time_ms"] = (
            (current_avg * (total_requests - 1) + processing_time) / total_requests
        )
        
        # Publish successful registration event
        event_publisher.publish_event(
            event_type="gateway_user_registration_completed",
            data={
                "user_id": user_id,
                "email": user_data.email,
                "role": user_data.role,
                "processing_time_ms": processing_time,
                "gateway_session_id": gateway_session_id,
                "timestamp": datetime.now().isoformat()
            },
            context="gateway_auth"
        )
        
        logger.info(
            f"Gateway user registered successfully: {user_data.email} with role {user_data.role} in {processing_time:.2f}ms"
        )
        
        return TokenResponse(
            access_token=access_token,
            expires_in=int(expires_delta.total_seconds()),
            user_id=user_id,
            email=user_data.email,
            full_name=user_data.full_name,
            role=user_data.role,
            permissions=MICROSERVICE_ROLE_PERMISSIONS.get(user_data.role, []),
            organization_id=user_data.organization_id,
            gateway_session_id=gateway_session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Handle unexpected errors
        processing_time = (time.perf_counter() - start_time) * 1000
        auth_metrics["failed_registrations"] += 1
        
        error_response = error_handler.handle_error(
            error=e,
            error_category=ErrorCategory.SYSTEM_ERROR,
            context={
                "component": "gateway_auth",
                "operation": "user_registration",
                "email": user_data.email if 'user_data' in locals() else "unknown"
            }
        )
        
        logger.error(f"Gateway registration failed with unexpected error: {error_response}")
        
        # Publish registration failure event
        event_publisher.publish_event(
            event_type="gateway_user_registration_failed",
            data={
                "error": str(e),
                "processing_time_ms": processing_time,
                "email": user_data.email if 'user_data' in locals() else "unknown"
            },
            context="gateway_auth"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed due to internal server error"
        )


@router.post("/login", response_model=TokenResponse)
async def login_user(login_data: UserLogin):
    """
    User login with JWT token generation for microservices gateway
    """
    start_time = time.perf_counter()
    
    try:
        # Update metrics
        auth_metrics["total_auth_requests"] += 1
        auth_metrics["gateway_auth_requests"] += 1
        
        # Validate login data
        validation_result = validator.validate_dict(
            data={
                "email": login_data.email,
                "password": login_data.password
            },
            schema={
                "email": {"type": "email", "required": True},
                "password": {"type": "string", "required": True}
            },
            context="user_login"
        )
        
        if not validation_result['valid']:
            error_response = error_handler.handle_error(
                error=ValueError(f"User login validation failed: {validation_result['errors']}"),
                error_category=ErrorCategory.VALIDATION_ERROR,
                context={
                    "component": "gateway_auth",
                    "operation": "user_login",
                    "email": login_data.email
                }
            )
            logger.warning(f"Login validation failed: {error_response}")
            
            auth_metrics["failed_logins"] += 1
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Validation failed: {validation_result['errors']}"
            )
        
        # Publish login attempt event
        event_publisher.publish_event(
            event_type="gateway_user_login_attempted",
            data={
                "email": login_data.email,
                "remember_me": login_data.remember_me,
                "timestamp": datetime.now().isoformat()
            },
            context="gateway_auth"
        )
        auth_metrics["events_published"] += 1
        
        # Find user by email
        user_record = None
        for user in USERS_STORE.values():
            if user["email"] == login_data.email and user["is_active"]:
                user_record = user
                break
        
        if not user_record:
            error_response = error_handler.handle_error(
                error=ValueError(f"Invalid login credentials for: {login_data.email}"),
                error_category=ErrorCategory.VALIDATION_ERROR,
                context={
                    "component": "gateway_auth",
                    "operation": "authenticate_user",
                    "email": login_data.email
                }
            )
            logger.warning(f"Login attempt with invalid credentials: {error_response}")
            
            # Publish security event
            event_publisher.publish_event(
                event_type="gateway_failed_login_attempt",
                data={
                    "email": login_data.email,
                    "timestamp": datetime.now().isoformat()
                },
                context="gateway_security"
            )
            auth_metrics["security_violations"] += 1
            
            auth_metrics["failed_logins"] += 1
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        try:
            password_valid = verify_password(login_data.password, user_record["password_hash"])
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                error_category=ErrorCategory.SYSTEM_ERROR,
                context={
                    "component": "password_verification",
                    "operation": "verify_user_password"
                }
            )
            logger.error(f"Password verification failed: {error_response}")
            
            auth_metrics["failed_logins"] += 1
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Login failed due to internal error"
            )
        
        if not password_valid:
            error_response = error_handler.handle_error(
                error=ValueError(f"Invalid password for user: {login_data.email}"),
                error_category=ErrorCategory.VALIDATION_ERROR,
                context={
                    "component": "gateway_auth",
                    "operation": "verify_user_password",
                    "email": login_data.email
                }
            )
            logger.warning(f"Login attempt with wrong password: {error_response}")
            
            # Publish security event
            event_publisher.publish_event(
                event_type="gateway_wrong_password_attempt",
                data={
                    "email": login_data.email,
                    "timestamp": datetime.now().isoformat()
                },
                context="gateway_security"
            )
            auth_metrics["security_violations"] += 1
            
            auth_metrics["failed_logins"] += 1
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Update last login
        user_record["last_login"] = datetime.now().isoformat()
        
        # Create JWT token
        try:
            gateway_session_id = str(uuid.uuid4())
            user_record["gateway_session_id"] = gateway_session_id
            
            token_data = {
                "user_id": user_record["user_id"],
                "email": user_record["email"],
                "role": user_record["role"],
                "gateway_session_id": gateway_session_id
            }
            
            expires_hours = 168 if login_data.remember_me else JWT_EXPIRATION_HOURS  # 7 days vs 24 hours
            expires_delta = timedelta(hours=expires_hours)
            access_token = create_access_token(token_data, expires_delta)
            
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                error_category=ErrorCategory.SYSTEM_ERROR,
                context={
                    "component": "jwt_token_creation",
                    "operation": "create_login_token"
                }
            )
            logger.error(f"Login token creation failed: {error_response}")
            
            auth_metrics["failed_logins"] += 1
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Login authentication succeeded but token generation failed"
            )
        
        # Cache user session
        user_session = {
            "user_id": user_record["user_id"],
            "email": user_record["email"],
            "full_name": user_record["full_name"],
            "role": user_record["role"],
            "organization_id": user_record["organization_id"],
            "permissions": MICROSERVICE_ROLE_PERMISSIONS.get(user_record["role"], []),
            "gateway_session_id": gateway_session_id,
            "last_login": user_record["last_login"]
        }
        SESSION_STORE[access_token] = user_session
        
        # Record login performance
        processing_time = (time.perf_counter() - start_time) * 1000
        performance_tracker.record_operation(
            operation_name="gateway_user_login",
            duration_ms=processing_time,
            success=True,
            metadata={
                "email": user_record["email"],
                "role": user_record["role"],
                "remember_me": login_data.remember_me,
                "expires_hours": expires_hours
            }
        )
        
        # Update success metrics
        auth_metrics["successful_logins"] += 1
        current_avg = auth_metrics["avg_auth_response_time_ms"]
        total_requests = auth_metrics["total_auth_requests"]
        auth_metrics["avg_auth_response_time_ms"] = (
            (current_avg * (total_requests - 1) + processing_time) / total_requests
        )
        
        # Publish successful login event
        event_publisher.publish_event(
            event_type="gateway_user_login_completed",
            data={
                "user_id": user_record["user_id"],
                "email": user_record["email"],
                "role": user_record["role"],
                "remember_me": login_data.remember_me,
                "processing_time_ms": processing_time,
                "gateway_session_id": gateway_session_id,
                "timestamp": datetime.now().isoformat()
            },
            context="gateway_auth"
        )
        
        logger.info(
            f"Gateway user logged in successfully: {user_record['email']} with role {user_record['role']} in {processing_time:.2f}ms"
        )
        
        return TokenResponse(
            access_token=access_token,
            expires_in=int(expires_delta.total_seconds()),
            user_id=user_record["user_id"],
            email=user_record["email"],
            full_name=user_record["full_name"],
            role=user_record["role"],
            permissions=MICROSERVICE_ROLE_PERMISSIONS.get(user_record["role"], []),
            organization_id=user_record["organization_id"],
            gateway_session_id=gateway_session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Handle unexpected errors
        processing_time = (time.perf_counter() - start_time) * 1000
        auth_metrics["failed_logins"] += 1
        
        error_response = error_handler.handle_error(
            error=e,
            error_category=ErrorCategory.SYSTEM_ERROR,
            context={
                "component": "gateway_auth",
                "operation": "user_login",
                "email": login_data.email if 'login_data' in locals() else "unknown"
            }
        )
        
        logger.error(f"Gateway login failed with unexpected error: {error_response}")
        
        # Publish login failure event
        event_publisher.publish_event(
            event_type="gateway_user_login_failed",
            data={
                "error": str(e),
                "processing_time_ms": processing_time,
                "email": login_data.email if 'login_data' in locals() else "unknown"
            },
            context="gateway_auth"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed due to internal server error"
        )


@router.post("/logout")
async def logout_user(current_user: Dict = Depends(get_current_user)):
    """
    User logout with token invalidation for gateway
    """
    start_time = time.perf_counter()
    
    try:
        # Publish logout attempt event
        event_publisher.publish_event(
            event_type="gateway_user_logout_attempted",
            data={
                "user_id": current_user["user_id"],
                "email": current_user["email"],
                "gateway_session_id": current_user.get("gateway_session_id"),
                "timestamp": datetime.now().isoformat()
            },
            context="gateway_auth"
        )
        auth_metrics["events_published"] += 1
        
        # Invalidate user session
        token = current_user.get("token")
        if token and token in SESSION_STORE:
            del SESSION_STORE[token]
            logger.debug(f"Gateway session invalidated for: {current_user['email']}")
        
        # Record logout performance
        processing_time = (time.perf_counter() - start_time) * 1000
        performance_tracker.record_operation(
            operation_name="gateway_user_logout",
            duration_ms=processing_time,
            success=True,
            metadata={
                "user_id": current_user["user_id"],
                "email": current_user["email"],
                "gateway_session_id": current_user.get("gateway_session_id")
            }
        )
        
        # Publish successful logout event
        event_publisher.publish_event(
            event_type="gateway_user_logout_completed",
            data={
                "user_id": current_user["user_id"],
                "email": current_user["email"],
                "processing_time_ms": processing_time,
                "gateway_session_id": current_user.get("gateway_session_id"),
                "timestamp": datetime.now().isoformat()
            },
            context="gateway_auth"
        )
        
        logger.info(f"Gateway user logged out successfully: {current_user['email']} in {processing_time:.2f}ms")
        
        return {
            "message": "Successfully logged out from gateway",
            "logout_time": datetime.now().isoformat(),
            "processing_time_ms": processing_time
        }
        
    except Exception as e:
        # Handle logout failure
        processing_time = (time.perf_counter() - start_time) * 1000
        
        error_response = error_handler.handle_error(
            error=e,
            error_category=ErrorCategory.SYSTEM_ERROR,
            context={
                "component": "gateway_auth",
                "operation": "user_logout",
                "user_id": current_user.get("user_id", "unknown") if 'current_user' in locals() else "unknown"
            }
        )
        
        logger.error(f"Gateway logout failed: {error_response}")
        
        # Publish logout failure event
        event_publisher.publish_event(
            event_type="gateway_user_logout_failed",
            data={
                "error": str(e),
                "processing_time_ms": processing_time,
                "user_id": current_user.get("user_id", "unknown") if 'current_user' in locals() else "unknown"
            },
            context="gateway_auth"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed due to internal error"
        )


@router.get("/profile", response_model=UserProfile)
async def get_user_profile(current_user: Dict = Depends(get_current_user)):
    """
    Get current user profile from gateway
    """
    return UserProfile(
        user_id=current_user["user_id"],
        email=current_user["email"],
        full_name=current_user["full_name"],
        role=current_user["role"],
        organization_id=current_user.get("organization_id"),
        is_active=True,
        created_at=current_user.get("created_at", ""),
        last_login=current_user.get("last_login"),
        permissions=current_user.get("permissions", []),
        gateway_session_id=current_user.get("gateway_session_id", "")
    )


@router.get("/verify-token")
async def verify_token(current_user: Dict = Depends(get_current_user)):
    """
    Verify JWT token validity for gateway
    """
    start_time = time.perf_counter()
    
    try:
        # Update metrics
        auth_metrics["token_validations"] += 1
        
        # Record token verification performance
        processing_time = (time.perf_counter() - start_time) * 1000
        performance_tracker.record_operation(
            operation_name="gateway_token_verification",
            duration_ms=processing_time,
            success=True,
            metadata={
                "user_id": current_user["user_id"],
                "role": current_user["role"],
                "permissions_count": len(current_user.get("permissions", []))
            }
        )
        
        # Publish token verification event
        event_publisher.publish_event(
            event_type="gateway_token_verification_completed",
            data={
                "user_id": current_user["user_id"],
                "email": current_user["email"],
                "role": current_user["role"],
                "processing_time_ms": processing_time,
                "gateway_session_id": current_user.get("gateway_session_id")
            },
            context="gateway_auth"
        )
        auth_metrics["events_published"] += 1
        
        logger.debug(f"Gateway token verified successfully for user: {current_user['email']} in {processing_time:.2f}ms")
        
        return {
            "valid": True,
            "user_id": current_user["user_id"],
            "email": current_user["email"],
            "role": current_user["role"],
            "permissions": current_user.get("permissions", []),
            "gateway_session_id": current_user.get("gateway_session_id"),
            "verification_time": datetime.now().isoformat(),
            "processing_time_ms": processing_time
        }
        
    except Exception as e:
        # Handle token verification failure
        processing_time = (time.perf_counter() - start_time) * 1000
        
        error_response = error_handler.handle_error(
            error=e,
            error_category=ErrorCategory.SYSTEM_ERROR,
            context={
                "component": "gateway_auth",
                "operation": "verify_token",
                "user_id": current_user.get("user_id", "unknown") if 'current_user' in locals() else "unknown"
            }
        )
        
        logger.error(f"Gateway token verification failed: {error_response}")
        
        # Publish token verification failure event
        event_publisher.publish_event(
            event_type="gateway_token_verification_failed",
            data={
                "error": str(e),
                "processing_time_ms": processing_time
            },
            context="gateway_auth"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token verification failed"
        )


@router.get("/permissions")
async def get_user_permissions(current_user: Dict = Depends(get_current_user)):
    """
    Get current user permissions for microservices
    """
    return {
        "user_id": current_user["user_id"],
        "role": current_user["role"],
        "permissions": current_user.get("permissions", []),
        "service_access": {
            "ai-orchestration": "service:access:ai-orchestration" in current_user.get("permissions", []),
            "data-bridge": "service:access:data-bridge" in current_user.get("permissions", []),
            "ml-processing": "service:access:ml-processing" in current_user.get("permissions", []),
            "trading-engine": "service:access:trading-engine" in current_user.get("permissions", []),
            "database-service": "service:access:database-service" in current_user.get("permissions", [])
        },
        "all_roles": list(MICROSERVICE_ROLE_PERMISSIONS.keys()),
        "gateway_session_id": current_user.get("gateway_session_id")
    }


@router.get("/roles")
async def get_available_roles(current_user: Dict = Depends(require_permission("system:admin"))):
    """
    Get all available roles and their permissions (admin only)
    """
    return {
        "roles": MICROSERVICE_ROLE_PERMISSIONS,
        "service_access_permissions": SERVICE_ACCESS_PERMISSIONS,
        "total_roles": len(MICROSERVICE_ROLE_PERMISSIONS)
    }


@router.post("/service-auth")
async def authenticate_service(auth_request: ServiceAuthRequest):
    """
    Service-to-service authentication endpoint
    """
    try:
        # Get service secrets from configuration (no hardcoded secrets)
        valid_services = config_manager.get('authentication.service_secrets', {})
        
        if not valid_services:
            logger.error("CRITICAL: Service secrets not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Service authentication not properly configured"
            )
        
        if auth_request.service_id not in valid_services:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid service ID"
            )
        
        if valid_services[auth_request.service_id] != auth_request.service_secret:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid service secret"
            )
        
        # Create service token
        service_token_data = {
            "service_id": auth_request.service_id,
            "permissions": ["service:internal", "service:communicate"],
            "type": "service"
        }
        
        access_token = create_access_token(service_token_data, timedelta(hours=1))
        
        logger.info(f"Service authenticated: {auth_request.service_id}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 3600,
            "service_id": auth_request.service_id,
            "permissions": ["service:internal", "service:communicate"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Service authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Service authentication failed"
        )


@router.get("/gateway-status")
async def get_gateway_auth_status():
    """
    Get authentication system status for gateway
    """
    return {
        "service": "api-gateway",
        "component": "authentication",
        "status": "active",
        "metrics": auth_metrics,
        "active_sessions": len(SESSION_STORE),
        "registered_users": len(USERS_STORE),
        "supported_roles": list(MICROSERVICE_ROLE_PERMISSIONS.keys()),
        "service_access_permissions": SERVICE_ACCESS_PERMISSIONS,
        "timestamp": datetime.now().isoformat()
    }