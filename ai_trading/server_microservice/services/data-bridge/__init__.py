"""
Data Bridge Service - MT5 and market data integration
Real-time trading data ingestion and processing
"""
__version__ = "2.0.0"
__service_type__ = "data-bridge"

from .src import api, business, data_sources, infrastructure, models, mt5_specific, websocket

__all__ = ['api', 'business', 'data_sources', 'infrastructure', 'models', 'mt5_specific', 'websocket']

__data_sources__ = [
    'mt5_real_time',
    'historical_data',
    'market_feeds',
    'economic_calendar'
]