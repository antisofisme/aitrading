"""
Data Manager - Database Abstraction Layer
Main exports for easy import by services

Usage:
    from central_hub.shared.components.data_manager import DataRouter, TickData, CandleData

    router = DataRouter()
    await router.save_tick(tick_data)
"""

# Main router
from .router import DataRouter

# Data models
from .models import (
    TickData,
    CandleData,
    EconomicEvent,
    HealthCheckResponse
)

# Exceptions
from .exceptions import (
    DataManagerError,
    DatabaseConnectionError,
    QueryTimeoutError,
    QueryExecutionError,
    CacheError,
    ValidationError,
    ConfigurationError,
    ConnectionPoolExhaustedError,
    RoutingError,
    CircuitBreakerOpenError,
    RetryExhaustedError
)

# Connection pool manager (for advanced use)
from .pools import DatabasePoolManager, get_pool_manager

# Cache system (for advanced use)
from .cache import MultiLevelCache, L1Cache, L2Cache

__all__ = [
    # Main router (primary interface)
    'DataRouter',

    # Data models
    'TickData',
    'CandleData',
    'EconomicEvent',
    'HealthCheckResponse',

    # Exceptions
    'DataManagerError',
    'DatabaseConnectionError',
    'QueryTimeoutError',
    'QueryExecutionError',
    'CacheError',
    'ValidationError',
    'ConfigurationError',
    'ConnectionPoolExhaustedError',
    'RoutingError',
    'CircuitBreakerOpenError',
    'RetryExhaustedError',

    # Advanced (internal use)
    'DatabasePoolManager',
    'get_pool_manager',
    'MultiLevelCache',
    'L1Cache',
    'L2Cache',
]

__version__ = '1.0.0'
__author__ = 'Suho Trading Platform'
