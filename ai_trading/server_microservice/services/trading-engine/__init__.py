"""
Trading Engine Service - Core trading execution
Real-time trading decisions, risk management, and order execution
"""
__version__ = "2.0.0"
__service_type__ = "trading-engine"

from .src import api, config, business, execution, infrastructure

__all__ = ['api', 'config', 'business', 'execution', 'infrastructure']

__trading_features__ = [
    'order_execution',
    'risk_management',
    'position_tracking',
    'strategy_execution'
]