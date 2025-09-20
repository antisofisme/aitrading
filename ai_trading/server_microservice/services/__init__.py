"""
Neliti Server Microservices - Enterprise Trading Platform
Microservice architecture for AI-driven trading intelligence
"""
__version__ = "2.0.0"
__architecture__ = "Enterprise Microservices"

# Service registry for lazy loading
def __getattr__(name: str):
    service_map = {
        'ai_orchestration': 'ai-orchestration',
        'ai_provider': 'ai-provider', 
        'api_gateway': 'api-gateway',
        'data_bridge': 'data-bridge',
        'database_service': 'database-service',
        'deep_learning': 'deep-learning',
        'ml_processing': 'ml-processing',
        'trading_engine': 'trading-engine',
        'user_service': 'user-service'
    }
    
    if name in service_map:
        from importlib import import_module
        service_name = service_map[name]
        module = import_module(f'.{service_name}', __name__)
        globals()[name] = module
        return module
    
    raise AttributeError(f"module {__name__} has no attribute {name}")

__all__ = list(__getattr__.__code__.co_names)

__microservices__ = [
    'ai-orchestration',
    'ai-provider', 
    'api-gateway',
    'data-bridge',
    'database-service',
    'deep-learning',
    'ml-processing',
    'trading-engine',
    'user-service'
]