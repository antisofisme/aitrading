"""
Trading Engine Technical Analysis Module

This module provides technical analysis capabilities for the Trading-Engine service.
All indicator calculations are performed here before being sent to ML services.

Components:
- indicator_manager.py: 14 advanced trading indicators calculation
- Integration with Trading Engine infrastructure
"""

from .indicator_manager import (
    TradingIndicatorManager,
    IndicatorType,
    IndicatorConfig,
    MarketData,
    MarketIndicator,
    FeatureSet,
    create_trading_indicator_manager
)

__all__ = [
    "TradingIndicatorManager",
    "IndicatorType", 
    "IndicatorConfig",
    "MarketData",
    "MarketIndicator",
    "FeatureSet",
    "create_trading_indicator_manager"
]