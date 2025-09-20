"""
Core Factory - Dynamic object creation with intelligent instantiation
"""
import inspect
from typing import Dict, Any, Optional, Type, Callable, Union, List
from enum import Enum
from abc import ABC, abstractmethod
from datetime import datetime

class FactoryStrategy(Enum):
    SINGLETON = "singleton"        # One instance per factory
    PROTOTYPE = "prototype"        # New instance each time
    CACHED = "cached"             # Cache instances by key
    LAZY = "lazy"                 # Create only when first accessed

class CreationContext:
    """Context information for object creation"""
    
    def __init__(self, 
                 factory_name: str,
                 object_type: str,
                 environment: str = "development",
                 service_name: str = None,
                 metadata: Dict[str, Any] = None):
        self.factory_name = factory_name
        self.object_type = object_type
        self.environment = environment
        self.service_name = service_name
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()

class IFactory(ABC):
    """Base factory interface"""
    
    @abstractmethod
    def create(self, object_type: str, context: CreationContext, **kwargs) -> Any:
        """Create object of specified type"""
        pass
    
    @abstractmethod
    def can_create(self, object_type: str) -> bool:
        """Check if factory can create object of this type"""
        pass

class BaseFactory(IFactory):
    """Base implementation of factory pattern"""
    
    def __init__(self, factory_name: str):
        self.factory_name = factory_name
        self.creators: Dict[str, Callable] = {}
        self.instances: Dict[str, Any] = {}
        self.cached_instances: Dict[str, Any] = {}
        self.creation_stats = {
            "total_created": 0,
            "by_type": {},
            "by_strategy": {}
        }
    
    def register_creator(self, 
                        object_type: str, 
                        creator: Union[Type, Callable],
                        strategy: FactoryStrategy = FactoryStrategy.PROTOTYPE):
        """Register object creator"""
        self.creators[object_type] = {
            "creator": creator,
            "strategy": strategy,
            "registered_at": datetime.utcnow()
        }
    
    def create(self, object_type: str, context: CreationContext, **kwargs) -> Any:
        """Create object of specified type"""
        if not self.can_create(object_type):
            raise ValueError(f"Cannot create object of type '{object_type}'")
        
        creator_info = self.creators[object_type]
        creator = creator_info["creator"]
        strategy = creator_info["strategy"]
        
        # Handle different creation strategies
        if strategy == FactoryStrategy.SINGLETON:
            return self._create_singleton(object_type, creator, context, **kwargs)
        
        elif strategy == FactoryStrategy.PROTOTYPE:
            return self._create_prototype(object_type, creator, context, **kwargs)
        
        elif strategy == FactoryStrategy.CACHED:
            cache_key = self._generate_cache_key(object_type, kwargs)
            return self._create_cached(cache_key, object_type, creator, context, **kwargs)
        
        elif strategy == FactoryStrategy.LAZY:
            return self._create_lazy(object_type, creator, context, **kwargs)
        
        else:
            raise ValueError(f"Unknown creation strategy: {strategy}")
    
    def can_create(self, object_type: str) -> bool:
        """Check if factory can create object of this type"""
        return object_type in self.creators
    
    def _create_singleton(self, object_type: str, creator: Callable, context: CreationContext, **kwargs) -> Any:
        """Create singleton instance"""
        if object_type in self.instances:
            return self.instances[object_type]
        
        instance = self._instantiate(creator, context, **kwargs)
        self.instances[object_type] = instance
        self._record_creation(object_type, FactoryStrategy.SINGLETON)
        
        return instance
    
    def _create_prototype(self, object_type: str, creator: Callable, context: CreationContext, **kwargs) -> Any:
        """Create new instance each time"""
        instance = self._instantiate(creator, context, **kwargs)
        self._record_creation(object_type, FactoryStrategy.PROTOTYPE)
        
        return instance
    
    def _create_cached(self, cache_key: str, object_type: str, creator: Callable, context: CreationContext, **kwargs) -> Any:
        """Create cached instance"""
        if cache_key in self.cached_instances:
            return self.cached_instances[cache_key]
        
        instance = self._instantiate(creator, context, **kwargs)
        self.cached_instances[cache_key] = instance
        self._record_creation(object_type, FactoryStrategy.CACHED)
        
        return instance
    
    def _create_lazy(self, object_type: str, creator: Callable, context: CreationContext, **kwargs) -> Any:
        """Create lazy-loaded instance"""
        # For now, same as prototype - in advanced implementation, this would return a proxy
        instance = self._instantiate(creator, context, **kwargs)
        self._record_creation(object_type, FactoryStrategy.LAZY)
        
        return instance
    
    def _instantiate(self, creator: Callable, context: CreationContext, **kwargs) -> Any:
        """Actually instantiate the object"""
        try:
            if inspect.isclass(creator):
                # Creator is a class - instantiate with constructor
                sig = inspect.signature(creator.__init__)
                filtered_kwargs = self._filter_kwargs(sig, kwargs)
                
                # Add context if constructor expects it
                if 'context' in sig.parameters:
                    filtered_kwargs['context'] = context
                
                return creator(**filtered_kwargs)
            
            elif callable(creator):
                # Creator is a function - call it
                sig = inspect.signature(creator)
                filtered_kwargs = self._filter_kwargs(sig, kwargs)
                
                # Add context if function expects it
                if 'context' in sig.parameters:
                    filtered_kwargs['context'] = context
                
                return creator(**filtered_kwargs)
            
            else:
                # Creator is already an instance
                return creator
                
        except Exception as e:
            raise RuntimeError(f"Failed to instantiate object using {creator}: {str(e)}")
    
    def _filter_kwargs(self, signature: inspect.Signature, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Filter kwargs to only include parameters that the function/constructor accepts"""
        param_names = set(signature.parameters.keys())
        return {k: v for k, v in kwargs.items() if k in param_names}
    
    def _generate_cache_key(self, object_type: str, kwargs: Dict[str, Any]) -> str:
        """Generate cache key for cached strategy"""
        # Simple implementation - in production, might use more sophisticated hashing
        key_parts = [object_type]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")
        
        return ":".join(key_parts)
    
    def _record_creation(self, object_type: str, strategy: FactoryStrategy):
        """Record creation statistics"""
        self.creation_stats["total_created"] += 1
        
        if object_type not in self.creation_stats["by_type"]:
            self.creation_stats["by_type"][object_type] = 0
        self.creation_stats["by_type"][object_type] += 1
        
        strategy_key = strategy.value
        if strategy_key not in self.creation_stats["by_strategy"]:
            self.creation_stats["by_strategy"][strategy_key] = 0
        self.creation_stats["by_strategy"][strategy_key] += 1

class CoreFactory:
    """Core factory manager - manages multiple specialized factories"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.factories: Dict[str, IFactory] = {}
        self.global_context = CreationContext(
            factory_name="core",
            object_type="manager",
            service_name=service_name
        )
        self.setup_default_factories()
    
    def register_factory(self, factory_name: str, factory: IFactory):
        """Register a specialized factory"""
        self.factories[factory_name] = factory
    
    def create(self, 
              factory_name: str,
              object_type: str,
              environment: str = "development",
              metadata: Dict[str, Any] = None,
              **kwargs) -> Any:
        """Create object using specified factory"""
        
        if factory_name not in self.factories:
            raise ValueError(f"Factory '{factory_name}' not found")
        
        factory = self.factories[factory_name]
        
        context = CreationContext(
            factory_name=factory_name,
            object_type=object_type,
            environment=environment,
            service_name=self.service_name,
            metadata=metadata
        )
        
        return factory.create(object_type, context, **kwargs)
    
    def setup_default_factories(self):
        """Setup default factories for common patterns"""
        
        # Database factory
        db_factory = BaseFactory("database")
        self.register_factory("database", db_factory)
        
        # Cache factory
        cache_factory = BaseFactory("cache")
        self.register_factory("cache", cache_factory)
        
        # Client factory (for external services)
        client_factory = BaseFactory("client")
        self.register_factory("client", client_factory)
        
        # Repository factory
        repository_factory = BaseFactory("repository")
        self.register_factory("repository", repository_factory)
    
    # Convenience methods for common creation patterns
    def create_database_connection(self, db_type: str, **config) -> Any:
        """Create database connection"""
        return self.create("database", db_type, **config)
    
    def create_cache_client(self, cache_type: str, **config) -> Any:
        """Create cache client"""
        return self.create("cache", cache_type, **config)
    
    def create_http_client(self, service_name: str, **config) -> Any:
        """Create HTTP client for external service"""
        return self.create("client", "http", service_name=service_name, **config)
    
    def create_repository(self, entity_type: str, **config) -> Any:
        """Create repository for entity"""
        return self.create("repository", entity_type, **config)
    
    # Factory management
    def get_factory_info(self, factory_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a factory"""
        if factory_name not in self.factories:
            return None
        
        factory = self.factories[factory_name]
        
        info = {
            "name": factory_name,
            "type": type(factory).__name__,
            "service": self.service_name
        }
        
        # Add additional info if it's a BaseFactory
        if isinstance(factory, BaseFactory):
            info.update({
                "registered_types": list(factory.creators.keys()),
                "creation_stats": factory.creation_stats,
                "singleton_instances": len(factory.instances),
                "cached_instances": len(factory.cached_instances)
            })
        
        return info
    
    def get_all_factories_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all factories"""
        return {
            name: self.get_factory_info(name)
            for name in self.factories
        }
    
    def get_creation_stats(self) -> Dict[str, Any]:
        """Get overall creation statistics"""
        total_created = 0
        by_factory = {}
        
        for factory_name, factory in self.factories.items():
            if isinstance(factory, BaseFactory):
                factory_total = factory.creation_stats["total_created"]
                total_created += factory_total
                by_factory[factory_name] = factory_total
        
        return {
            "total_objects_created": total_created,
            "by_factory": by_factory,
            "active_factories": len(self.factories),
            "service": self.service_name
        }
    
    # Service-specific factory setup
    def setup_service_factories(self):
        """Setup service-specific factories"""
        if self.service_name == "api-gateway":
            self._setup_api_gateway_factories()
        elif self.service_name == "trading-engine":
            self._setup_trading_engine_factories()
        elif self.service_name == "database-service":
            self._setup_database_service_factories()
    
    def _setup_api_gateway_factories(self):
        """Setup API Gateway specific factories"""
        # Authentication factory
        auth_factory = BaseFactory("authentication")
        # Register different auth types
        # auth_factory.register_creator("jwt", JWTAuthenticator, FactoryStrategy.SINGLETON)
        # auth_factory.register_creator("oauth", OAuthAuthenticator, FactoryStrategy.SINGLETON)
        self.register_factory("authentication", auth_factory)
        
        # Rate limiter factory
        rate_limiter_factory = BaseFactory("rate_limiter")
        # rate_limiter_factory.register_creator("memory", MemoryRateLimiter, FactoryStrategy.CACHED)
        # rate_limiter_factory.register_creator("redis", RedisRateLimiter, FactoryStrategy.CACHED)
        self.register_factory("rate_limiter", rate_limiter_factory)
    
    def _setup_trading_engine_factories(self):
        """Setup Trading Engine specific factories"""
        # Broker factory
        broker_factory = BaseFactory("broker")
        # broker_factory.register_creator("mt5", MT5Broker, FactoryStrategy.SINGLETON)
        # broker_factory.register_creator("demo", DemoBroker, FactoryStrategy.PROTOTYPE)
        self.register_factory("broker", broker_factory)
        
        # Strategy factory
        strategy_factory = BaseFactory("strategy")
        # strategy_factory.register_creator("scalping", ScalpingStrategy, FactoryStrategy.PROTOTYPE)
        # strategy_factory.register_creator("swing", SwingStrategy, FactoryStrategy.PROTOTYPE)
        self.register_factory("strategy", strategy_factory)
    
    def _setup_database_service_factories(self):
        """Setup Database Service specific factories"""
        # Connection factory
        connection_factory = BaseFactory("connection")
        # connection_factory.register_creator("postgresql", PostgreSQLConnection, FactoryStrategy.SINGLETON)
        # connection_factory.register_creator("clickhouse", ClickHouseConnection, FactoryStrategy.SINGLETON)
        self.register_factory("connection", connection_factory)
        
        # Migration factory
        migration_factory = BaseFactory("migration")
        # migration_factory.register_creator("sql", SQLMigration, FactoryStrategy.PROTOTYPE)
        # migration_factory.register_creator("data", DataMigration, FactoryStrategy.PROTOTYPE)
        self.register_factory("migration", migration_factory)
    
    # Utility methods
    def clear_cached_instances(self, factory_name: str = None):
        """Clear cached instances"""
        if factory_name:
            if factory_name in self.factories:
                factory = self.factories[factory_name]
                if isinstance(factory, BaseFactory):
                    factory.cached_instances.clear()
        else:
            # Clear all factories
            for factory in self.factories.values():
                if isinstance(factory, BaseFactory):
                    factory.cached_instances.clear()
    
    def dispose_singletons(self, factory_name: str = None):
        """Dispose singleton instances"""
        factories_to_process = [self.factories[factory_name]] if factory_name else self.factories.values()
        
        for factory in factories_to_process:
            if isinstance(factory, BaseFactory):
                for instance in factory.instances.values():
                    # Call dispose method if available
                    if hasattr(instance, 'dispose') and callable(getattr(instance, 'dispose')):
                        try:
                            getattr(instance, 'dispose')()
                        except Exception as e:
                            print(f"❌ Error disposing singleton: {e}")
                
                factory.instances.clear()
    
    # Health check
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on factories"""
        factory_health = {}
        overall_healthy = True
        
        for factory_name, factory in self.factories.items():
            try:
                # Basic health check - ensure factory can list its creators
                if isinstance(factory, BaseFactory):
                    health_info = {
                        "healthy": True,
                        "registered_types": len(factory.creators),
                        "active_singletons": len(factory.instances),
                        "cached_instances": len(factory.cached_instances)
                    }
                else:
                    health_info = {"healthy": True, "type": "custom"}
                
                factory_health[factory_name] = health_info
                
            except Exception as e:
                factory_health[factory_name] = {
                    "healthy": False,
                    "error": str(e)
                }
                overall_healthy = False
        
        return {
            "factories_healthy": overall_healthy,
            "factories": factory_health,
            "total_factories": len(self.factories),
            "service": self.service_name,
            "timestamp": datetime.utcnow().isoformat()
        }