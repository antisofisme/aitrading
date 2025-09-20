"""
MT5 Bridge WebSocket Module
Real-time WebSocket communication for MT5 microservice
"""

from .mt5_websocket import (
    MT5WebSocketManager,
    WebSocketMessage,
    AccountInfoMessage,
    TickDataMessage, 
    TradingSignalMessage,
    websocket_manager
)

__version__ = "1.0.0"
__module__ = "websocket"

__all__ = [
    "MT5WebSocketManager",
    "WebSocketMessage",
    "AccountInfoMessage",
    "TickDataMessage",
    "TradingSignalMessage", 
    "websocket_manager"
]