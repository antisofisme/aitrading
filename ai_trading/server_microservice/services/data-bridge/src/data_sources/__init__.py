"""
Data Sources Module - Historical and Real-time Market Data Collection
Centralized data ingestion from multiple high-quality sources
"""

from .dukascopy_client import DataBridgeDukascopyDownloader
from .mql5_scraper import (
    MQL5WidgetScraper, 
    MQL5EconomicEvent, 
    get_mql5_widget_events,
    get_mql5_batch_historical_events
)
from .tradingview_scraper import DataBridgeTradingViewScraper, DataBridgeEconomicEvent
from .historical_downloader import (
    MassiveDataCollectionExecutor,
    estimate_collection_time,
    estimate_data_storage,
    QUALITY_METRICS,
    run_massive_collection
)

__all__ = [
    # Dukascopy & TrueFX Historical Data
    "DataBridgeDukascopyDownloader",
    
    # MQL5 Economic Calendar
    "MQL5WidgetScraper",
    "MQL5EconomicEvent", 
    "get_mql5_widget_events",
    "get_mql5_batch_historical_events",
    
    # TradingView Economic Calendar
    "DataBridgeTradingViewScraper",
    "DataBridgeEconomicEvent",
    
    # Massive Data Collection Orchestrator
    "MassiveDataCollectionExecutor",
    "estimate_collection_time",
    "estimate_data_storage",
    "QUALITY_METRICS",
    "run_massive_collection"
]

__version__ = "2.0.0"
__module_type__ = "data_sources"
__description__ = "Multi-source market data collection with high-quality feeds"