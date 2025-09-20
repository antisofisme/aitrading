"""
MT5 Bridge API Module - RESTful and WebSocket endpoints for MT5 operations
"""

from .mt5_endpoints import app, get_mt5_bridge
from .mt5_websocket_endpoints import router

__all__ = [
    "app",
    "get_mt5_bridge", 
    "router"
]

__version__ = "1.0.0"
__module_type__ = "api_endpoints"