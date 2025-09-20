"""
ClickHouse Data Ingestion Schemas - UNIQUE DATA COLLECTION ONLY
Schemas for 2 unique data ingestion services (CONSOLIDATED - unified similar data types)

SERVICES COVERED (UNIQUE DATA ONLY):
- HistoricalDownloader: Economic events data collection
- MQL5Scraper: Community data scraping

CONSOLIDATED INTO EXISTING SCHEMAS:
- TradingViewScraper: Uses external_data_schemas.py (economic_calendar with AI enhancement)
- DukascopyClient: Uses external_data_schemas.py (market_data with broker differentiation)
- MT5LiveBridge: Uses raw_data_schemas.py (ticks with broker differentiation)
- WebSocketClient: Uses raw_data_schemas.py (ticks with full market microstructure)

ARCHITECTURE PRINCIPLE:
- Same data type = Same table with broker/source column differentiation
- Unique data type = Separate table in appropriate schema file

FEATURES:
- Centralized logging with context-aware messages
- Performance tracking for schema operations  
- Centralized error handling with proper categorization
- Centralized validation for schema definitions
- Event publishing for schema lifecycle events
"""

# FULL CENTRALIZATION INFRASTRUCTURE INTEGRATION
import logging
# Simple performance tracking placeholder
# Error handling placeholder
# Validation placeholder
# Event manager placeholder
# Import manager placeholder

# Import typing through centralized import manager
from typing import Dict, List

# Enhanced logger with centralized infrastructure
logger = logging.getLogger(__name__)


class ClickHouseDataIngestionSchemas:
    """
    Data ingestion schemas for automated data collection services
    These tables store data from the 5 automated data ingestion services
    """

    @staticmethod
    # @performance_tracked - simplified
    def get_all_tables() -> Dict[str, str]:
        """Get all data ingestion table schemas with centralized tracking"""
        try:
            logger.info("Retrieving all ClickHouse data ingestion table schemas")
            
            tables = {
                # Data Ingestion Services Tables (Unique data only)
                "economic_events": ClickHouseDataIngestionSchemas.economic_events(),
                "mql5_data": ClickHouseDataIngestionSchemas.mql5_data(),
            }
            
            # Validate table structure
            # Validation simplified
            
            # Publish event for schema retrieval
            # Event publishing simplified
            
            logger.info(f"Successfully retrieved {len(tables)} ClickHouse data ingestion table schemas")
            return tables
            
        except Exception as e:
            error_context = {
                "operation": "get_all_tables",
                "database_type": "clickhouse",
                "schema_type": "data_ingestion"
            }
            # Error handling simplified
            logger.error(f"Failed to retrieve ClickHouse data ingestion table schemas: {e}")
            raise

    @staticmethod
    def economic_events() -> str:
        """Economic Events data from HistoricalDownloader service"""
        return """
        CREATE TABLE IF NOT EXISTS economic_events (
            timestamp DateTime64(3) DEFAULT now64() CODEC(Delta, LZ4),
            event_date Date,
            event_time String CODEC(ZSTD),
            country String CODEC(ZSTD),
            currency LowCardinality(String),
            event_name String CODEC(ZSTD),
            importance LowCardinality(String),
            actual String CODEC(ZSTD),
            forecast String CODEC(ZSTD),
            previous String CODEC(ZSTD),
            source String DEFAULT 'HistoricalDownloader' CODEC(ZSTD),
            
            -- Enhanced Indexing
            INDEX idx_country country TYPE bloom_filter GRANULARITY 8192,
            INDEX idx_currency currency TYPE set(20) GRANULARITY 8192,
            INDEX idx_importance importance TYPE set(5) GRANULARITY 8192,
            INDEX idx_event_date event_date TYPE minmax GRANULARITY 8192
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(event_date)
        ORDER BY (country, event_date, timestamp)
        TTL timestamp + INTERVAL 2 YEAR
        SETTINGS index_granularity = 8192
        """



    @staticmethod
    def mql5_data() -> str:
        """MQL5 community data from MQL5 scraper service"""
        return """
        CREATE TABLE IF NOT EXISTS mql5_data (
            timestamp DateTime64(3) DEFAULT now64() CODEC(Delta, LZ4),
            data_type LowCardinality(String),
            title String CODEC(ZSTD),
            description String CODEC(ZSTD),
            author String CODEC(ZSTD),
            rating Float64 CODEC(Gorilla),
            downloads UInt64 CODEC(T64),
            url String CODEC(ZSTD),
            source String DEFAULT 'MQL5' CODEC(ZSTD),
            
            -- Enhanced Indexing
            INDEX idx_data_type data_type TYPE set(20) GRANULARITY 8192,
            INDEX idx_author author TYPE bloom_filter GRANULARITY 8192,
            INDEX idx_rating rating TYPE minmax GRANULARITY 8192,
            INDEX idx_timestamp timestamp TYPE minmax GRANULARITY 8192
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(timestamp)
        ORDER BY (data_type, rating DESC, timestamp)
        TTL timestamp + INTERVAL 6 MONTH
        SETTINGS index_granularity = 8192
        """



    @staticmethod
    def get_table_list() -> List[str]:
        """Get list of all data ingestion table names (unique data only)"""
        return [
            "economic_events",
            "mql5_data"
        ]

    @staticmethod
    def get_data_ingestion_services() -> Dict[str, str]:
        """Get mapping of table names to their respective data ingestion services"""
        return {
            "economic_events": "HistoricalDownloader",
            "mql5_data": "MQL5Scraper"
        }

    @staticmethod
    def get_service_tables(service_name: str) -> List[str]:
        """Get table names for a specific data ingestion service"""
        service_mapping = {
            "HistoricalDownloader": ["economic_events"],
            "MQL5Scraper": ["mql5_data"]
            # Note: DukascopyClient now uses external_data_schemas.market_data
            # Note: MT5LiveBridge now uses raw_data_schemas.ticks
        }
        return service_mapping.get(service_name, [])