"""
User Service - Base Domain Service
Foundation class for all business domain services in user microservice
"""

import asyncio
from typing import Dict, Any, Optional, TypeVar, Generic
from dataclasses import dataclass
from datetime import datetime

# PER-SERVICE INFRASTRUCTURE INTEGRATION
from ....shared.infrastructure.core.logger_core import CoreLogger
from ....shared.infrastructure.core.config_core import CoreConfig
from ....shared.infrastructure.core.error_core import CoreErrorHandler
from ....shared.infrastructure.base.base_error_handler import ErrorCategory
from ....shared.infrastructure.base.base_performance import BasePerformance
from ....shared.infrastructure.base.base_event_publisher import BaseEventPublisher

T = TypeVar('T')

@dataclass
class ServiceResult(Generic[T]):
    """Standard service result wrapper"""
    success: bool
    data: Optional[T] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    
    @classmethod
    def success_result(cls, data: T) -> 'ServiceResult[T]':
        return cls(success=True, data=data)
    
    @classmethod
    def failure(cls, message: str, details: Optional[Dict[str, Any]] = None) -> 'ServiceResult[T]':
        return cls(success=False, error_message=message, error_details=details)

@dataclass
class ServiceContext:
    """Service operation context"""
    user_id: str
    tenant_id: Optional[str] = None
    organization_id: Optional[str] = None
    correlation_id: Optional[str] = None
    permissions: Optional[list] = None
    metadata: Optional[Dict[str, Any]] = None

class BaseDomainService:
    """
    Base class for all domain services in user microservice
    Provides per-service infrastructure integration and common functionality
    """
    
    def __init__(self, component_name: str = "base"):
        # Per-service infrastructure components
        self.logger = CoreLogger("user-service", component_name)
        self.config = CoreConfig("user-service")
        self.error_handler = CoreErrorHandler("user-service")
        self.event_publisher = BaseEventPublisher("user-service")
        
        # Service state
        self._initialized = False
        self._db_pool = None
        self._cache_client = None
        self._vector_db = None
        self._graph_db = None
        
        # Get config safely
        try:
            db_config = self.config.get_database_config()
            cache_config = self.config.get_cache_config()
            service_config = self.config.get("service", {})
            
            self.logger.info(f"Initialized {component_name} domain service", context={
                "service": "user-service",
                "component": component_name,
                "config_summary": {
                    "database_host": db_config.get("host", "localhost"),
                    "cache_host": cache_config.get("redis_host", "localhost"),
                    "service_port": service_config.get("service_port", 8009)
                }
            })
        except Exception as e:
            self.logger.warning(f"Config access failed during initialization: {e}", context={
                "service": "user-service",
                "component": component_name
            })
    
    async def initialize(self):
        """Initialize service with all dependencies"""
        if self._initialized:
            return
        
        try:
            # Initialize database connection
            await self._initialize_database()
            
            # Initialize cache
            await self._initialize_cache()
            
            # Initialize vector database (optional)
            await self._initialize_vector_db()
            
            # Initialize graph database (optional)
            await self._initialize_graph_db()
            
            # Service-specific initialization
            await self._initialize_service()
            
            self._initialized = True
            self.logger.info("Service initialized successfully")
            
        except Exception as e:
            error_response = self.error_handler.handle_error(
                e, ErrorCategory.SERVICE_ERROR, {"operation": "service_initialization"}
            )
            self.logger.error("Service initialization failed", context={"error": error_response.to_dict()})
            raise
    
    async def _initialize_database(self):
        """Initialize database connection pool"""
        # Mock database initialization - in production use asyncpg
        db_config = self.config.get_database_config()
        self.logger.info("Database connection pool initialized", context={
            "host": db_config.get("host", "localhost"),
            "database": db_config.get("database", "user_service"),
            "pool_size": db_config.get("pool_size", 10)
        })
        
    async def _initialize_cache(self):
        """Initialize cache client"""
        # Mock cache initialization - in production use aioredis
        cache_config = self.config.get_cache_config()
        self.logger.info("Cache client initialized", context={
            "host": cache_config.get("redis_host", "localhost"),
            "db": cache_config.get("redis_db", 0)
        })
    
    async def _initialize_vector_db(self):
        """Initialize vector database (optional)"""
        if self.config.get("enable_ai_features", True):
            # Mock vector DB initialization
            self.logger.info("Vector database initialized for AI features")
    
    async def _initialize_graph_db(self):
        """Initialize graph database (optional)"""
        if self.config.get("enable_multi_tenant", True):
            # Mock graph DB initialization  
            self.logger.info("Graph database initialized for relationships")
    
    async def _initialize_service(self):
        """Override in subclasses for service-specific initialization"""
        pass
    
    # Database Operations (Mock implementations)
    async def get_db_connection(self):
        """Get database connection from pool"""
        # Mock connection - in production return actual asyncpg connection
        return self
    
    async def execute(self, query: str, *args):
        """Execute database query"""
        self.logger.debug(f"Executing query: {query[:100]}...")
        return True
    
    async def fetchrow(self, query: str, *args):
        """Fetch single row"""
        self.logger.debug(f"Fetching row: {query[:100]}...")
        return {"mock": "data"}
    
    async def fetch(self, query: str, *args):
        """Fetch multiple rows"""
        self.logger.debug(f"Fetching rows: {query[:100]}...")
        return [{"mock": "data"}]
    
    async def fetchval(self, query: str, *args):
        """Fetch single value"""
        self.logger.debug(f"Fetching value: {query[:100]}...")
        return "mock_value"
    
    # Cache Operations (Mock implementations)
    async def get_cached(self, key: str, tenant_id: Optional[str] = None):
        """Get value from cache"""
        cache_key = f"{tenant_id}:{key}" if tenant_id else key
        self.logger.debug(f"Cache GET: {cache_key}")
        return None  # Mock - no cached data
    
    async def set_cached(self, key: str, value: Any, ttl: int, tenant_id: Optional[str] = None):
        """Set value in cache"""
        cache_key = f"{tenant_id}:{key}" if tenant_id else key
        self.logger.debug(f"Cache SET: {cache_key} (TTL: {ttl}s)")
        return True
    
    async def invalidate_cache(self, key: str, tenant_id: Optional[str] = None):
        """Invalidate cache entry"""
        cache_key = f"{tenant_id}:{key}" if tenant_id else key
        self.logger.debug(f"Cache INVALIDATE: {cache_key}")
        return True
    
    # Vector Database Operations (Mock implementations)
    async def store_embedding(self, collection: str, id: str, embedding: list, metadata: Dict[str, Any]):
        """Store vector embedding"""
        if self._vector_db:
            self.logger.debug(f"Storing embedding: {collection}:{id}")
        return True
    
    async def search_similar(self, collection: str, query_embedding: list, limit: int = 10):
        """Search similar vectors"""
        if self._vector_db:
            self.logger.debug(f"Vector search: {collection} (limit: {limit})")
            return []  # Mock empty results
        return []
    
    # Graph Database Operations (Mock implementations)  
    async def store_relationship(self, from_id: str, to_id: str, relationship_type: str, properties: Dict[str, Any]):
        """Store relationship in graph"""
        if self._graph_db:
            self.logger.debug(f"Storing relationship: {from_id} -[{relationship_type}]-> {to_id}")
        return True
    
    # Event Publishing
    async def publish(self, event_type: str, payload: Dict[str, Any], context: ServiceContext):
        """Publish service event"""
        enriched_payload = {
            **payload,
            "service": "user-service",
            "user_id": context.user_id,
            "tenant_id": context.tenant_id,
            "correlation_id": context.correlation_id
        }
        self.event_publisher.publish(event_type, enriched_payload, context.correlation_id)
    
    # Permission Checking
    def _get_required_permission(self, operation: str) -> Optional[str]:
        """Override in subclasses to define required permissions"""
        return None
    
    async def _check_permission(self, context: ServiceContext, operation: str) -> bool:
        """Check if user has required permission"""
        required_permission = self._get_required_permission(operation)
        if not required_permission:
            return True  # No permission required
        
        user_permissions = context.permissions or []
        return required_permission in user_permissions
    
    # Context Execution
    async def execute_with_context(
        self, 
        operation: str, 
        context: ServiceContext, 
        operation_func
    ) -> ServiceResult:
        """Execute operation with context, permission checking, and error handling"""
        try:
            # Check permissions
            has_permission = await self._check_permission(context, operation)
            if not has_permission:
                required = self._get_required_permission(operation)
                error_response = self.error_handler.handle_error(
                    PermissionError(f"Missing required permission: {required}"),
                    ErrorCategory.AUTHORIZATION_ERROR,
                    {"operation": operation, "required_permission": required, "user_id": context.user_id}
                )
                return ServiceResult.failure("Permission denied", error_response.to_dict())
            
            # Execute operation
            result = await operation_func()
            return ServiceResult.success_result(result)
            
        except Exception as e:
            # Determine error category based on exception type
            if isinstance(e, ValueError):
                category = ErrorCategory.VALIDATION_ERROR
            elif isinstance(e, PermissionError):
                category = ErrorCategory.AUTHORIZATION_ERROR
            else:
                category = ErrorCategory.SERVICE_ERROR
            
            error_response = self.error_handler.handle_error(e, category, {
                "operation": operation,
                "user_id": context.user_id,
                "tenant_id": context.tenant_id
            })
            
            self.logger.error(f"Operation {operation} failed", context={
                "error": error_response.to_dict(),
                "context": context.__dict__
            })
            
            return ServiceResult.failure(error_response.error_message, error_response.to_dict())