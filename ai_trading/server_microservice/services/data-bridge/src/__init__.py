"""
MT5 Bridge Microservice
Production-ready MT5 trading bridge with shared infrastructure integration
"""

from .business.mt5_bridge import (
    MT5Bridge,
    MT5Config,
    TickData,
    TradeOrder, 
    OrderType,
    ConnectionStatus,
    create_mt5_bridge
)

from .api.mt5_endpoints import app as mt5_api
from .websocket.mt5_websocket import websocket_manager

__version__ = "1.0.0"
__service__ = "mt5-bridge"

__all__ = [
    "MT5Bridge",
    "MT5Config",
    "TickData", 
    "TradeOrder",
    "OrderType",
    "ConnectionStatus",
    "create_mt5_bridge",
    "mt5_api",
    "websocket_manager"
]
