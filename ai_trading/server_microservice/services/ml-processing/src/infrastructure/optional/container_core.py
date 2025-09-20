"""
Core Service Container - Dependency injection and service lifecycle management
"""
import inspect
import asyncio
from typing import Dict, Any, Optional, Type, Callable, Union, List
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

class ServiceLifecycle(Enum):
    SINGLETON = "singleton"     # One instance per container
    TRANSIENT = "transient"     # New instance each time
    SCOPED = "scoped"          # One instance per scope (e.g., per request)

class ServiceStatus(Enum):
    REGISTERED = "registered"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"

@dataclass
class ServiceDefinition:
    """Service definition in the container"""
    name: str
    service_type: Type
    implementation: Union[Type, Callable, Any]
    lifecycle: ServiceLifecycle
    dependencies: List[str]
    initialization_params: Dict[str, Any]
    status: ServiceStatus = ServiceStatus.REGISTERED
    instance: Any = None
    created_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

class CoreServiceContainer:
    """Core dependency injection container"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.services: Dict[str, ServiceDefinition] = {}
        self.instances: Dict[str, Any] = {}
        self.scoped_instances: Dict[str, Dict[str, Any]] = {}
        self.initialization_order: List[str] = []
        self.is_initialized = False
        self.container_stats = {
            "services_registered": 0,
            "services_active": 0,
            "services_failed": 0,
            "instances_created": 0
        }
    
    def register_singleton(self,
                          name: str,
                          service_type: Type,
                          implementation: Union[Type, Callable] = None,
                          dependencies: List[str] = None,
                          **init_params) -> 'CoreServiceContainer':
        """Register a singleton service"""
        return self._register_service(
            name=name,
            service_type=service_type,
            implementation=implementation or service_type,
            lifecycle=ServiceLifecycle.SINGLETON,
            dependencies=dependencies or [],
            init_params=init_params
        )
    
    def register_transient(self,
                          name: str,
                          service_type: Type,
                          implementation: Union[Type, Callable] = None,
                          dependencies: List[str] = None,
                          **init_params) -> 'CoreServiceContainer':
        """Register a transient service"""
        return self._register_service(
            name=name,
            service_type=service_type,
            implementation=implementation or service_type,
            lifecycle=ServiceLifecycle.TRANSIENT,
            dependencies=dependencies or [],
            init_params=init_params
        )
    
    def register_scoped(self,
                       name: str,
                       service_type: Type,
                       implementation: Union[Type, Callable] = None,
                       dependencies: List[str] = None,
                       **init_params) -> 'CoreServiceContainer':
        """Register a scoped service"""
        return self._register_service(
            name=name,
            service_type=service_type,
            implementation=implementation or service_type,
            lifecycle=ServiceLifecycle.SCOPED,
            dependencies=dependencies or [],
            init_params=init_params
        )
    
    def register_instance(self,
                         name: str,
                         instance: Any,
                         service_type: Type = None) -> 'CoreServiceContainer':
        """Register an existing instance"""
        service_def = ServiceDefinition(
            name=name,
            service_type=service_type or type(instance),
            implementation=instance,
            lifecycle=ServiceLifecycle.SINGLETON,
            dependencies=[],
            initialization_params={},
            status=ServiceStatus.ACTIVE,
            instance=instance,
            created_at=datetime.utcnow()
        )
        
        self.services[name] = service_def
        self.instances[name] = instance
        self.container_stats["services_registered"] += 1
        self.container_stats["services_active"] += 1
        
        return self
    
    def _register_service(self,
                         name: str,
                         service_type: Type,
                         implementation: Union[Type, Callable],
                         lifecycle: ServiceLifecycle,
                         dependencies: List[str],
                         init_params: Dict[str, Any]) -> 'CoreServiceContainer':
        """Internal service registration"""
        
        if name in self.services:
            raise ValueError(f"Service '{name}' is already registered")
        
        service_def = ServiceDefinition(
            name=name,
            service_type=service_type,
            implementation=implementation,
            lifecycle=lifecycle,
            dependencies=dependencies,
            initialization_params=init_params,
            metadata={
                "registered_at": datetime.utcnow().isoformat(),
                "container": self.service_name
            }
        )
        
        self.services[name] = service_def
        self.container_stats["services_registered"] += 1
        
        return self
    
    async def get_service(self, name: str, scope_id: str = None) -> Any:
        """Get service instance"""
        if name not in self.services:
            raise ValueError(f"Service '{name}' is not registered")
        
        service_def = self.services[name]
        
        # Handle different lifecycles
        if service_def.lifecycle == ServiceLifecycle.SINGLETON:
            return await self._get_singleton_instance(service_def)
        
        elif service_def.lifecycle == ServiceLifecycle.TRANSIENT:
            return await self._create_instance(service_def)
        
        elif service_def.lifecycle == ServiceLifecycle.SCOPED:
            if scope_id is None:
                raise ValueError("Scope ID required for scoped services")
            return await self._get_scoped_instance(service_def, scope_id)
        
        else:
            raise ValueError(f"Unknown lifecycle: {service_def.lifecycle}")
    
    async def _get_singleton_instance(self, service_def: ServiceDefinition) -> Any:
        """Get or create singleton instance"""
        if service_def.instance is not None:
            return service_def.instance
        
        # Create instance
        instance = await self._create_instance(service_def)
        
        # Store as singleton
        service_def.instance = instance
        service_def.status = ServiceStatus.ACTIVE
        service_def.created_at = datetime.utcnow()
        self.instances[service_def.name] = instance
        self.container_stats["services_active"] += 1
        
        return instance
    
    async def _get_scoped_instance(self, service_def: ServiceDefinition, scope_id: str) -> Any:
        """Get or create scoped instance"""
        if scope_id not in self.scoped_instances:
            self.scoped_instances[scope_id] = {}
        
        scope_instances = self.scoped_instances[scope_id]
        
        if service_def.name in scope_instances:
            return scope_instances[service_def.name]
        
        # Create instance for this scope
        instance = await self._create_instance(service_def)
        scope_instances[service_def.name] = instance
        
        return instance
    
    async def _create_instance(self, service_def: ServiceDefinition) -> Any:
        """Create new service instance"""
        try:
            service_def.status = ServiceStatus.INITIALIZING
            
            # Resolve dependencies
            resolved_deps = {}
            for dep_name in service_def.dependencies:
                if dep_name not in self.services:
                    raise ValueError(f"Dependency '{dep_name}' not found for service '{service_def.name}'")
                
                resolved_deps[dep_name] = await self.get_service(dep_name)
            
            # Prepare initialization parameters
            init_params = {**service_def.initialization_params}
            
            # Add dependencies to init params if the constructor expects them
            if inspect.isclass(service_def.implementation):
                sig = inspect.signature(service_def.implementation.__init__)
                for param_name in sig.parameters:
                    if param_name in resolved_deps:
                        init_params[param_name] = resolved_deps[param_name]
            
            # Create instance
            if inspect.isclass(service_def.implementation):
                instance = service_def.implementation(**init_params)
            elif callable(service_def.implementation):
                instance = service_def.implementation(**init_params)
            else:
                instance = service_def.implementation
            
            # Call async initialization if available
            if hasattr(instance, 'initialize') and callable(getattr(instance, 'initialize')):
                init_method = getattr(instance, 'initialize')
                if asyncio.iscoroutinefunction(init_method):
                    await init_method()
                else:
                    init_method()
            
            self.container_stats["instances_created"] += 1
            return instance
            
        except Exception as e:
            service_def.status = ServiceStatus.ERROR
            self.container_stats["services_failed"] += 1
            raise RuntimeError(f"Failed to create instance of '{service_def.name}': {str(e)}")
    
    async def initialize_container(self):
        """Initialize all singleton services in dependency order"""
        if self.is_initialized:
            return
        
        print(f"🚀 Initializing service container for {self.service_name}")
        
        # Calculate initialization order
        self.initialization_order = self._calculate_initialization_order()
        
        # Initialize singleton services
        for service_name in self.initialization_order:
            service_def = self.services[service_name]
            
            if service_def.lifecycle == ServiceLifecycle.SINGLETON:
                try:
                    await self._get_singleton_instance(service_def)
                    print(f"✅ Initialized {service_name}")
                except Exception as e:
                    print(f"❌ Failed to initialize {service_name}: {e}")
                    raise
        
        self.is_initialized = True
        print(f"🎉 Container initialization completed for {self.service_name}")
    
    def _calculate_initialization_order(self) -> List[str]:
        """Calculate service initialization order based on dependencies"""
        order = []
        visited = set()
        visiting = set()
        
        def visit(service_name: str):
            if service_name in visiting:
                raise ValueError(f"Circular dependency detected involving '{service_name}'")
            
            if service_name in visited:
                return
            
            visiting.add(service_name)
            
            service_def = self.services[service_name]
            for dep_name in service_def.dependencies:
                if dep_name in self.services:
                    visit(dep_name)
            
            visiting.remove(service_name)
            visited.add(service_name)
            order.append(service_name)
        
        for service_name in self.services:
            if service_name not in visited:
                visit(service_name)
        
        return order
    
    async def dispose_container(self):
        """Dispose all services and clean up resources"""
        print(f"🛑 Disposing service container for {self.service_name}")
        
        # Dispose in reverse order
        for service_name in reversed(self.initialization_order):
            await self._dispose_service(service_name)
        
        # Clear scoped instances
        self.scoped_instances.clear()
        
        # Clear instances
        self.instances.clear()
        
        self.is_initialized = False
        print(f"🗑️ Container disposal completed for {self.service_name}")
    
    async def _dispose_service(self, service_name: str):
        """Dispose a specific service"""
        if service_name not in self.services:
            return
        
        service_def = self.services[service_name]
        
        if service_def.instance is not None:
            try:
                service_def.status = ServiceStatus.STOPPING
                
                # Call dispose method if available
                if hasattr(service_def.instance, 'dispose') and callable(getattr(service_def.instance, 'dispose')):
                    dispose_method = getattr(service_def.instance, 'dispose')
                    if asyncio.iscoroutinefunction(dispose_method):
                        await dispose_method()
                    else:
                        dispose_method()
                
                service_def.status = ServiceStatus.STOPPED
                service_def.instance = None
                self.container_stats["services_active"] -= 1
                
                print(f"🗑️ Disposed {service_name}")
                
            except Exception as e:
                print(f"❌ Error disposing {service_name}: {e}")
    
    def dispose_scope(self, scope_id: str):
        """Dispose all services in a scope"""
        if scope_id in self.scoped_instances:
            for service_name, instance in self.scoped_instances[scope_id].items():
                # Call dispose if available
                if hasattr(instance, 'dispose') and callable(getattr(instance, 'dispose')):
                    try:
                        dispose_method = getattr(instance, 'dispose')
                        if asyncio.iscoroutinefunction(dispose_method):
                            asyncio.create_task(dispose_method())
                        else:
                            dispose_method()
                    except Exception as e:
                        print(f"❌ Error disposing scoped {service_name}: {e}")
            
            del self.scoped_instances[scope_id]
    
    # Service management utilities
    def is_registered(self, name: str) -> bool:
        """Check if service is registered"""
        return name in self.services
    
    def get_service_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get service information"""
        if name not in self.services:
            return None
        
        service_def = self.services[name]
        
        return {
            "name": service_def.name,
            "type": service_def.service_type.__name__,
            "lifecycle": service_def.lifecycle.value,
            "status": service_def.status.value,
            "dependencies": service_def.dependencies,
            "created_at": service_def.created_at.isoformat() if service_def.created_at else None,
            "has_instance": service_def.instance is not None,
            "metadata": service_def.metadata
        }
    
    def get_container_stats(self) -> Dict[str, Any]:
        """Get container statistics"""
        active_services = sum(1 for s in self.services.values() if s.status == ServiceStatus.ACTIVE)
        
        return {
            **self.container_stats,
            "services_active": active_services,
            "total_scopes": len(self.scoped_instances),
            "initialization_order": self.initialization_order,
            "is_initialized": self.is_initialized,
            "container_service": self.service_name
        }
    
    def get_all_services(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all services"""
        return {
            name: self.get_service_info(name)
            for name in self.services
        }
    
    # Health checking
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all services"""
        health_results = {}
        overall_healthy = True
        
        for service_name, service_def in self.services.items():
            if service_def.instance is not None:
                try:
                    # Check if service has health check method
                    if hasattr(service_def.instance, 'health_check'):
                        health_method = getattr(service_def.instance, 'health_check')
                        if asyncio.iscoroutinefunction(health_method):
                            result = await health_method()
                        else:
                            result = health_method()
                        
                        health_results[service_name] = result
                        if not result.get('healthy', True):
                            overall_healthy = False
                    else:
                        # Default health check - just check if instance exists
                        health_results[service_name] = {
                            "healthy": True,
                            "status": service_def.status.value
                        }
                        
                except Exception as e:
                    health_results[service_name] = {
                        "healthy": False,
                        "error": str(e)
                    }
                    overall_healthy = False
            else:
                health_results[service_name] = {
                    "healthy": service_def.lifecycle != ServiceLifecycle.SINGLETON,
                    "status": service_def.status.value
                }
        
        return {
            "container_healthy": overall_healthy,
            "container": self.service_name,
            "services": health_results,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Common service registration patterns
    def register_database_services(self, db_config: Dict[str, Any]):
        """Register common database services"""
        # Register database connection
        self.register_singleton(
            "database",
            type(None),  # Will be replaced with actual DB type
            dependencies=[],
            **db_config
        )
        
        # Register repository pattern services
        self.register_singleton(
            "user_repository",
            type(None),  # Will be replaced with actual repo type
            dependencies=["database"]
        )
        
        return self
    
    def register_cache_services(self, cache_config: Dict[str, Any]):
        """Register cache services"""
        self.register_singleton(
            "cache",
            type(None),  # Will be replaced with actual cache type
            dependencies=[],
            **cache_config
        )
        
        return self
    
    def register_api_services(self):
        """Register common API services"""
        self.register_scoped(
            "request_context",
            type(None),  # Will be replaced with actual context type
            dependencies=[]
        )
        
        self.register_singleton(
            "auth_service",
            type(None),  # Will be replaced with actual auth type
            dependencies=["database", "cache"]
        )
        
        return self