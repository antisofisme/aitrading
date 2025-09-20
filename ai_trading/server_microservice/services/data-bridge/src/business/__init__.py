"""
MT5 Bridge Core Module - Core MT5 trading functionality and bridge integration
"""

from .mt5_bridge import (
    MT5Bridge,
    MT5Config,
    TickData,
    TradeOrder,
    OrderType,
    ConnectionStatus,
    MultiTierCache,
    ConnectionPool,
    cached_method,
    create_mt5_bridge,
    get_connection_pool_stats
)

__all__ = [
    "MT5Bridge",
    "MT5Config",
    "TickData", 
    "TradeOrder",
    "OrderType",
    "ConnectionStatus",
    "MultiTierCache",
    "ConnectionPool",
    "cached_method",
    "create_mt5_bridge",
    "get_connection_pool_stats"
]

__version__ = "1.0.0"
__module_type__ = "core_trading"