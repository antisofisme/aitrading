"""
Shared Infrastructure Hub - Central Microservices Framework
No dependencies to services - Pure framework code
"""
__version__ = "1.0.0"
__architecture__ = "Hub-and-Spoke Centralization"

# Core patterns (always available)
from .core.logger_core import CoreLogger
from .core.config_core import CoreConfig
from .core.error_core import CoreErrorHandler
from .core.response_core import CoreResponse
from .core.performance_core import CorePerformance
from .core.cache_core import CoreCache

# Base interfaces for service implementations
from .base.base_logger import BaseLogger
from .base.base_config import BaseConfig
from .base.base_error_handler import BaseErrorHandler
from .base.base_response import BaseResponse
from .base.base_performance import BasePerformance
from .base.base_cache import BaseCache

# Network infrastructure
from .network.proxy_manager import ProxyManager

__all__ = [
    # Core implementations
    'CoreLogger',
    'CoreConfig', 
    'CoreErrorHandler',
    'CoreResponse',
    'CorePerformance',
    'CoreCache',
    
    # Base interfaces
    'BaseLogger',
    'BaseConfig',
    'BaseErrorHandler', 
    'BaseResponse',
    'BasePerformance',
    'BaseCache',
    
    # Network infrastructure
    'ProxyManager'
]

# Framework metadata
__critical_patterns__ = [
    "logging", "config", "errors", "response", "performance", "cache"
]
__optional_patterns__ = [
    "events", "validation", "container", "factory", "network"
]