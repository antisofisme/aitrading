"""
Static Service Configurations
Infrastructure configs that don't change frequently
"""

# Service configurations
from .config_api_gateway import CONFIG_API_GATEWAY
from .config_component_manager import CONFIG_COMPONENT_MANAGER
from .config_market_analyzer import CONFIG_MARKET_ANALYZER
from .config_trading_engine import CONFIG_TRADING_ENGINE

__all__ = [
    'CONFIG_API_GATEWAY',
    'CONFIG_COMPONENT_MANAGER',
    'CONFIG_MARKET_ANALYZER',
    'CONFIG_TRADING_ENGINE'
]