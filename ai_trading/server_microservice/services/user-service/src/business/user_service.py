"""
User Service - Core User Management
Enterprise-grade user management dengan multi-tenant support, caching, dan event streaming
Migrated from server_side with per-service infrastructure patterns
"""

import uuid
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass

# PER-SERVICE INFRASTRUCTURE INTEGRATION
from ...shared.infrastructure.base.base_error_handler import BaseErrorHandler, ErrorCategory
from ...shared.infrastructure.base.base_performance import BasePerformance
from .base_domain_service import BaseDomainService, ServiceResult, ServiceContext

@dataclass
class UserProfile:
    """User profile data class"""
    user_id: str
    email: str
    full_name: str
    role: str
    organization_id: Optional[str]
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    profile_settings: Dict[str, Any]
    ai_preferences: Dict[str, Any]

@dataclass
class UserCreateRequest:
    """User creation request"""
    email: str
    password: str
    full_name: str
    role: str = "user"
    organization_id: Optional[str] = None
    profile_settings: Dict[str, Any] = None
    ai_preferences: Dict[str, Any] = None

@dataclass
class UserUpdateRequest:
    """User update request"""
    full_name: Optional[str] = None
    role: Optional[str] = None
    profile_settings: Optional[Dict[str, Any]] = None
    ai_preferences: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class UserService(BaseDomainService):
    """
    Enterprise User Service dengan:
    - Multi-tenant user management
    - AI preferences management
    - Profile caching
    - User activity tracking
    - Event streaming untuk user actions
    
    MIGRATED TO MICROSERVICE ARCHITECTURE with per-service infrastructure
    """
    
    def __init__(self):
        super().__init__("user_management")
        
        # Role permissions mapping for user service
        self.ROLE_PERMISSIONS = {
            "admin": ["user:*", "project:*", "workflow:*"],
            "manager": ["user:read", "user:update", "project:*", "workflow:*"],
            "user": ["user:read", "user:update_own", "project:read", "project:create", "workflow:execute"],
            "viewer": ["user:read", "project:read", "workflow:read"]
        }
    
    async def _initialize_service(self):
        """Initialize user service with per-service infrastructure"""
        try:
            # User service cache configurations - service-specific TTL
            cache_config = self.config.get_cache_config()
            self.user_cache_ttl = cache_config.get("ttl_user_profile", 3600)  # 1 hour
            self.profile_cache_ttl = cache_config.get("ttl_user_profile", 3600)  # 1 hour  
            self.ai_preferences_cache_ttl = cache_config.get("ttl_ai_preferences", 7200)  # 2 hours
            
            # Publish service initialization event using per-service event publisher
            self.event_publisher.publish(
                "user_service_initialized",
                {
                    "service": "user-service",
                    "cache_ttl_config": {
                        "user": self.user_cache_ttl,
                        "profile": self.profile_cache_ttl,
                        "ai_preferences": self.ai_preferences_cache_ttl
                    }
                }
            )
            
            self.logger.info("UserService initialized with multi-tenant support", context={
                "cache_configs": {
                    "user_ttl": self.user_cache_ttl,
                    "profile_ttl": self.profile_cache_ttl,
                    "ai_preferences_ttl": self.ai_preferences_cache_ttl
                },
                "max_users_per_tenant": self.config.get("max_users_per_tenant", 1000)
            })
        except Exception as e:
            error_response = self.error_handler.handle_error(
                e,
                ErrorCategory.SERVICE_ERROR,
                {"operation": "initialize_user_service"}
            )
            self.logger.error("UserService initialization failed", context={"error": error_response.to_dict()})
            raise
    
    def _get_required_permission(self, operation: str) -> Optional[str]:
        """Get required permission untuk user operations"""
        permission_map = {
            "create_user": "user:create",
            "update_user": "user:update", 
            "delete_user": "user:delete",
            "get_user": "user:read",
            "list_users": "user:read",
            "update_own_profile": None,  # Users can update their own profile
            "get_own_profile": None,     # Users can view their own profile
            "update_ai_preferences": None, # Users can update their AI preferences
        }
        return permission_map.get(operation)
    
    # Core User Management with per-service patterns
    async def create_user(self, request: UserCreateRequest, context: ServiceContext) -> ServiceResult[UserProfile]:
        """Create new user dengan validation dan event streaming"""
        
        # User service specific validation using per-service validator
        if not self._validate_email(request.email):
            error_response = self.error_handler.handle_validation_error(
                "email", request.email, "Invalid email format"
            )
            return ServiceResult.failure("Invalid email format", error_response.to_dict())
        
        async def _create_user_operation():
            # Validate role against user service role permissions
            if request.role not in self.ROLE_PERMISSIONS:
                raise ValueError(f"Invalid role: {request.role}")
            
            # Check email uniqueness
            existing_user = await self._get_user_by_email(request.email, context.tenant_id)
            if existing_user:
                raise ValueError("Email already exists")
            
            user_id = str(uuid.uuid4())
            password_hash = self._hash_password(request.password)
            
            # Default settings for user service
            profile_settings = request.profile_settings or {
                "theme": "light",
                "language": "en",
                "timezone": "UTC",
                "notifications": {
                    "email": True,
                    "push": False,
                    "ai_insights": True
                }
            }
            
            ai_preferences = request.ai_preferences or {
                "preferred_models": ["gpt-4", "claude-3-sonnet"],
                "cost_preference": "balanced",
                "response_style": "professional",
                "auto_save_conversations": True,
                "enable_ai_suggestions": True
            }
            
            # Store in database using per-service database connection
            async with await self.get_db_connection() as conn:
                await conn.execute("""
                    INSERT INTO users (
                        user_id, email, password_hash, full_name, role, 
                        organization_id, is_active, created_at, 
                        profile_settings, ai_preferences
                    ) VALUES ($1, $2, $3, $4, $5, $6, true, NOW(), $7, $8)
                """, 
                user_id, request.email, password_hash, request.full_name, 
                request.role, request.organization_id, profile_settings, ai_preferences)
                
                # Get created user
                user_record = await conn.fetchrow("""
                    SELECT user_id, email, full_name, role, organization_id, 
                           is_active, created_at, last_login, profile_settings, ai_preferences
                    FROM users WHERE user_id = $1
                """, user_id)
            
            # Create user profile
            user_profile = UserProfile(
                user_id=user_record["user_id"],
                email=user_record["email"],
                full_name=user_record["full_name"],
                role=user_record["role"],
                organization_id=user_record["organization_id"],
                is_active=user_record["is_active"],
                created_at=user_record["created_at"],
                last_login=user_record["last_login"],
                profile_settings=user_record["profile_settings"],
                ai_preferences=user_record["ai_preferences"]
            )
            
            # Cache user profile using per-service cache
            await self.set_cached(
                f"user_profile:{user_id}", 
                user_profile, 
                self.profile_cache_ttl,
                context.tenant_id
            )
            
            # Cache email to user_id mapping
            await self.set_cached(
                f"email_mapping:{request.email}",
                user_id,
                self.user_cache_ttl,
                context.tenant_id
            )
            
            # Store user embedding untuk semantic search (if vector DB enabled)
            if self._vector_db:
                user_embedding = await self._generate_user_embedding(user_profile)
                await self.store_embedding(
                    "users",
                    user_id,
                    user_embedding,
                    {
                        "email": request.email,
                        "full_name": request.full_name,
                        "role": request.role,
                        "tenant_id": context.tenant_id
                    }
                )
            
            # Store user relationships in graph (if graph DB enabled)
            if self._graph_db and request.organization_id:
                await self.store_relationship(
                    user_id,
                    request.organization_id,
                    "BELONGS_TO",
                    {"role": request.role, "joined_at": datetime.now().isoformat()}
                )
            
            # Publish user created event using per-service event publisher
            self.event_publisher.publish_user_lifecycle_event(
                "user_created",
                user_id,
                {
                    "email": request.email,
                    "role": request.role,
                    "organization_id": request.organization_id,
                    "tenant_id": context.tenant_id,
                    "created_at": datetime.now().isoformat()
                },
                {"operation": "create_user", "service": "user-service"}
            )
            
            # Also publish to service event system for inter-service communication
            await self.publish(
                "user_created",
                {
                    "user_id": user_id,
                    "email": request.email,
                    "role": request.role,
                    "organization_id": request.organization_id
                },
                context
            )
            
            return user_profile
        
        return await self.execute_with_context(
            "create_user",
            context, 
            _create_user_operation
        )
    
    async def get_user_profile(self, user_id: str, context: ServiceContext) -> ServiceResult[UserProfile]:
        """Get user profile dengan caching"""
        
        # User service specific validation
        if not self._validate_uuid(user_id):
            error_response = self.error_handler.handle_validation_error(
                "user_id", user_id, "Invalid user ID format"
            )
            return ServiceResult.failure("Invalid user ID", error_response.to_dict())
        
        async def _get_user_operation():
            # Try cache first using per-service cache
            cached_profile = await self.get_cached(
                f"user_profile:{user_id}",
                context.tenant_id
            )
            if cached_profile:
                return cached_profile
            
            # Get from database using per-service database connection
            async with await self.get_db_connection() as conn:
                user_record = await conn.fetchrow("""
                    SELECT user_id, email, full_name, role, organization_id,
                           is_active, created_at, last_login, profile_settings, ai_preferences
                    FROM users WHERE user_id = $1 AND is_active = true
                """, user_id)
                
                if not user_record:
                    raise ValueError("User not found")
                
                user_profile = UserProfile(
                    user_id=user_record["user_id"],
                    email=user_record["email"],
                    full_name=user_record["full_name"],
                    role=user_record["role"],
                    organization_id=user_record["organization_id"],
                    is_active=user_record["is_active"],
                    created_at=user_record["created_at"],
                    last_login=user_record["last_login"],
                    profile_settings=user_record["profile_settings"],
                    ai_preferences=user_record["ai_preferences"]
                )
                
                # Cache profile
                await self.set_cached(
                    f"user_profile:{user_id}",
                    user_profile,
                    self.profile_cache_ttl,
                    context.tenant_id
                )
                
                return user_profile
        
        return await self.execute_with_context(
            "get_user" if user_id != context.user_id else "get_own_profile",
            context,
            _get_user_operation
        )
    
    async def update_user_profile(
        self, 
        user_id: str, 
        update_request: UserUpdateRequest, 
        context: ServiceContext
    ) -> ServiceResult[UserProfile]:
        """Update user profile dengan change tracking"""
        
        async def _update_user_operation():
            # Build update query dynamically
            update_fields = []
            update_values = []
            param_index = 1
            changes = {}
            
            if update_request.full_name is not None:
                update_fields.append(f"full_name = ${param_index}")
                update_values.append(update_request.full_name)
                changes["full_name"] = update_request.full_name
                param_index += 1
            
            if update_request.role is not None:
                if update_request.role not in self.ROLE_PERMISSIONS:
                    raise ValueError(f"Invalid role: {update_request.role}")
                update_fields.append(f"role = ${param_index}")
                update_values.append(update_request.role)
                changes["role"] = update_request.role
                param_index += 1
            
            if update_request.profile_settings is not None:
                update_fields.append(f"profile_settings = ${param_index}")
                update_values.append(update_request.profile_settings)
                changes["profile_settings"] = update_request.profile_settings
                param_index += 1
            
            if update_request.ai_preferences is not None:
                update_fields.append(f"ai_preferences = ${param_index}")
                update_values.append(update_request.ai_preferences)
                changes["ai_preferences"] = update_request.ai_preferences
                param_index += 1
            
            if update_request.is_active is not None:
                update_fields.append(f"is_active = ${param_index}")
                update_values.append(update_request.is_active)
                changes["is_active"] = update_request.is_active
                param_index += 1
            
            if not update_fields:
                raise ValueError("No fields to update")
            
            # Add updated_at and user_id
            update_fields.append("updated_at = NOW()")
            update_values.append(user_id)
            
            query = f"""
                UPDATE users 
                SET {', '.join(update_fields)}
                WHERE user_id = ${param_index}
                RETURNING user_id, email, full_name, role, organization_id,
                         is_active, created_at, last_login, profile_settings, ai_preferences
            """
            
            async with await self.get_db_connection() as conn:
                user_record = await conn.fetchrow(query, *update_values)
                
                if not user_record:
                    raise ValueError("User not found")
                
                updated_profile = UserProfile(
                    user_id=user_record["user_id"],
                    email=user_record["email"],
                    full_name=user_record["full_name"],
                    role=user_record["role"],
                    organization_id=user_record["organization_id"],
                    is_active=user_record["is_active"],
                    created_at=user_record["created_at"],
                    last_login=user_record["last_login"],
                    profile_settings=user_record["profile_settings"],
                    ai_preferences=user_record["ai_preferences"]
                )
                
                # Update cache
                await self.set_cached(
                    f"user_profile:{user_id}",
                    updated_profile,
                    self.profile_cache_ttl,
                    context.tenant_id
                )
                
                # Update vector embedding jika profile berubah
                if self._vector_db and (update_request.full_name or update_request.role):
                    user_embedding = await self._generate_user_embedding(updated_profile)
                    await self.store_embedding(
                        "users",
                        user_id,
                        user_embedding,
                        {
                            "email": updated_profile.email,
                            "full_name": updated_profile.full_name,
                            "role": updated_profile.role,
                            "tenant_id": context.tenant_id
                        }
                    )
                
                # Publish user updated event
                self.event_publisher.publish_user_lifecycle_event(
                    "user_updated",
                    user_id,
                    {"changes": changes},
                    {"operation": "update_user_profile", "service": "user-service"}
                )
                
                await self.publish(
                    "user_updated",
                    {"user_id": user_id, "changes": changes},
                    context
                )
                
                return updated_profile
        
        return await self.execute_with_context(
            "update_user" if user_id != context.user_id else "update_own_profile",
            context,
            _update_user_operation
        )
    
    # AI Preferences Management
    async def update_ai_preferences(
        self, 
        user_id: str, 
        ai_preferences: Dict[str, Any], 
        context: ServiceContext
    ) -> ServiceResult[Dict[str, Any]]:
        """Update user AI preferences dengan specialized caching"""
        
        async def _update_ai_preferences_operation():
            async with await self.get_db_connection() as conn:
                await conn.execute("""
                    UPDATE users 
                    SET ai_preferences = $1, updated_at = NOW()
                    WHERE user_id = $2
                """, ai_preferences, user_id)
                
                # Cache AI preferences separately
                await self.set_cached(
                    f"ai_preferences:{user_id}",
                    ai_preferences,
                    self.ai_preferences_cache_ttl,
                    context.tenant_id
                )
                
                # Invalidate user profile cache
                await self.invalidate_cache(f"user_profile:{user_id}", context.tenant_id)
                
                # Publish AI preferences updated event
                self.event_publisher.publish_user_lifecycle_event(
                    "ai_preferences_updated",
                    user_id,
                    {"preferences": ai_preferences},
                    {"operation": "update_ai_preferences", "service": "user-service"}
                )
                
                await self.publish(
                    "ai_preferences_updated",
                    {"user_id": user_id, "preferences": ai_preferences},
                    context
                )
                
                return ai_preferences
        
        return await self.execute_with_context(
            "update_ai_preferences",
            context,
            _update_ai_preferences_operation
        )
    
    async def get_ai_preferences(self, user_id: str, context: ServiceContext) -> ServiceResult[Dict[str, Any]]:
        """Get user AI preferences dengan caching"""
        
        async def _get_ai_preferences_operation():
            # Try cache first
            cached_preferences = await self.get_cached(
                f"ai_preferences:{user_id}",
                context.tenant_id
            )
            if cached_preferences:
                return cached_preferences
            
            # Get from database
            async with await self.get_db_connection() as conn:
                result = await conn.fetchrow("""
                    SELECT ai_preferences FROM users WHERE user_id = $1
                """, user_id)
                
                if not result:
                    raise ValueError("User not found")
                
                ai_preferences = result["ai_preferences"] or {}
                
                # Cache preferences
                await self.set_cached(
                    f"ai_preferences:{user_id}",
                    ai_preferences,
                    self.ai_preferences_cache_ttl,
                    context.tenant_id
                )
                
                return ai_preferences
        
        return await self.execute_with_context(
            "get_own_profile" if user_id == context.user_id else "get_user",
            context,
            _get_ai_preferences_operation
        )
    
    # User Search dan Discovery
    async def search_users(
        self, 
        query: str, 
        context: ServiceContext,
        limit: int = 10
    ) -> ServiceResult[List[UserProfile]]:
        """Search users menggunakan vector similarity"""
        
        async def _search_users_operation():
            results = []
            
            # Vector search jika tersedia
            if self._vector_db:
                query_embedding = await self._generate_search_embedding(query)
                similar_users = await self.search_similar("users", query_embedding, limit)
                
                for match in similar_users:
                    user_id = match["id"]
                    user_profile_result = await self.get_user_profile(user_id, context)
                    if user_profile_result.success:
                        results.append(user_profile_result.data)
            else:
                # Fallback to database search
                async with await self.get_db_connection() as conn:
                    user_records = await conn.fetch("""
                        SELECT user_id, email, full_name, role, organization_id,
                               is_active, created_at, last_login, profile_settings, ai_preferences
                        FROM users 
                        WHERE (full_name ILIKE $1 OR email ILIKE $1) 
                        AND is_active = true
                        LIMIT $2
                    """, f"%{query}%", limit)
                    
                    for record in user_records:
                        results.append(UserProfile(
                            user_id=record["user_id"],
                            email=record["email"],
                            full_name=record["full_name"],
                            role=record["role"],
                            organization_id=record["organization_id"],
                            is_active=record["is_active"],
                            created_at=record["created_at"],
                            last_login=record["last_login"],
                            profile_settings=record["profile_settings"],
                            ai_preferences=record["ai_preferences"]
                        ))
            
            return results
        
        return await self.execute_with_context(
            "list_users",
            context,
            _search_users_operation
        )
    
    # Helper Methods for User Service
    async def _get_user_by_email(self, email: str, tenant_id: Optional[str]) -> Optional[str]:
        """Get user ID by email dengan caching"""
        # Try cache first
        cached_user_id = await self.get_cached(f"email_mapping:{email}", tenant_id)
        if cached_user_id:
            return cached_user_id
        
        # Get from database
        async with await self.get_db_connection() as conn:
            result = await conn.fetchrow(
                "SELECT user_id FROM users WHERE email = $1 AND is_active = true",
                email
            )
            
            if result:
                user_id = result["user_id"]
                await self.set_cached(f"email_mapping:{email}", user_id, self.user_cache_ttl, tenant_id)
                return user_id
        
        return None
    
    async def _generate_user_embedding(self, user_profile: UserProfile) -> List[float]:
        """Generate embedding untuk user profile (mock implementation)"""
        text = f"{user_profile.full_name} {user_profile.email} {user_profile.role}"
        
        # Mock embedding (dalam production gunakan model seperti sentence-transformers)
        hash_object = hashlib.md5(text.encode())
        hash_hex = hash_object.hexdigest()
        
        # Convert hash to embedding vector (784 dimensions)
        embedding = []
        for i in range(0, len(hash_hex), 2):
            val = int(hash_hex[i:i+2], 16) / 255.0
            embedding.append(val)
        
        # Pad to 784 dimensions
        while len(embedding) < 784:
            embedding.append(0.0)
        
        return embedding[:784]
    
    async def _generate_search_embedding(self, query: str) -> List[float]:
        """Generate embedding untuk search query"""
        return await self._generate_user_embedding(
            UserProfile(
                user_id="", email=query, full_name=query, role="", 
                organization_id=None, is_active=True, created_at=datetime.now(),
                last_login=None, profile_settings={}, ai_preferences={}
            )
        )
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format - user service specific"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _validate_uuid(self, uuid_string: str) -> bool:
        """Validate UUID format - user service specific"""
        try:
            uuid.UUID(uuid_string)
            return True
        except ValueError:
            return False
    
    def _hash_password(self, password: str) -> str:
        """Hash password using secure bcrypt - DEPRECATED, use AuthenticationService"""
        # Import the authentication service for secure password hashing
        from .auth_service import AuthenticationService
        auth_service = AuthenticationService()
        return auth_service.hash_password(password)