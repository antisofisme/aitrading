# Service infrastructure - use absolute imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))

try:
    from shared.infrastructure.core.logger_core import get_logger
    from shared.infrastructure.core.error_core import handle_error
    from shared.infrastructure.core.performance_core import performance_tracked
    from shared.infrastructure.core.config_core import CoreConfig
    from shared.infrastructure.core.cache_core import CoreCache
except ImportError as e:
    print(f"⚠️ Infrastructure import issue: {e}")
    # Fallback implementations
    import logging
    
    def get_logger(name, version=None):
        return logging.getLogger(name)
    
    def handle_error(service_name, error, context=None):
        print(f"Error in {service_name}: {error}")
        if context:
            print(f"Context: {context}")
    
    def performance_tracked(service_name, operation_name):
        def decorator(func):
            return func
        return decorator
    
    class CoreConfig:
        def __init__(self, service_name=None):
            pass
        def get(self, key, default=None):
            return default
    
    class CoreCache:
        def __init__(self, name, max_size=1000, default_ttl=300):
            self.name = name
            self.max_size = max_size
            self.default_ttl = default_ttl
            self.cache = {}
        
        async def get(self, key): 
            return None
        
        async def set(self, key, value, ttl=None): 
            pass

"""
Data Source Pipeline - Unified integration for external data sources
Connects file-based data sources with database storage infrastructure
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Any, Union, Optional
import pandas as pd
from dataclasses import asdict

# Infrastructure integration
try:
    from shared.infrastructure.core.performance_core import performance_tracked
except ImportError:
    pass

# Business components
from .batch_processor import TickDataBatchProcessor
from .database_client import DatabaseServiceClient
from ..data_sources.mql5_scraper import MQL5EconomicEvent
from ..data_sources.tradingview_scraper import DataBridgeEconomicEvent


class DataSourcePipeline:
    """Unified pipeline for data source to database integration"""
    
    def __init__(self, batch_processor: TickDataBatchProcessor, database_client: DatabaseServiceClient):
        self.batch_processor = batch_processor
        self.database_client = database_client
        self.logger = get_logger("data-bridge", "data-source-pipeline")
        
        # Processing statistics
        self.stats = {
            "ticks_processed": 0,
            "economic_events_processed": 0,
            "errors": 0,
            "last_processing_time": None
        }
    
    @performance_tracked("unknown-service", "process_historical_ticks")
    async def process_historical_ticks(self, dukascopy_data: pd.DataFrame, source_name: str = "dukascopy") -> bool:
        """Transform historical tick data and send to batch processor for database storage"""
        try:
            self.logger.info(f"Processing {len(dukascopy_data)} historical ticks from {source_name}")
            
            # Transform DataFrame to batch processor format
            tick_data_list = []
            for _, row in dukascopy_data.iterrows():
                tick_dict = {
                    "symbol": str(row.get('pair', row.get('symbol', 'UNKNOWN'))),
                    "time": row.get('timestamp', row.get('time', datetime.now(timezone.utc).isoformat())),
                    "bid": float(row.get('bid', 0.0)),
                    "ask": float(row.get('ask', 0.0)),
                    "volume": float(row.get('volume', 1.0)),
                    "spread": float(row.get('spread', row.get('ask', 0.0) - row.get('bid', 0.0))),
                    "broker": str(row.get('broker', source_name.title())),
                    "account_type": "historical"
                }
                tick_data_list.append(tick_dict)
            
            # Send to batch processor for database storage
            success_count = 0
            batch_size = 1000  # Process in manageable batches
            
            for i in range(0, len(tick_data_list), batch_size):
                batch = tick_data_list[i:i + batch_size]
                try:
                    for tick in batch:
                        await self.batch_processor.add_tick(tick)
                        success_count += 1
                except Exception as e:
                    self.logger.error(f"Failed to process tick batch {i//batch_size + 1}: {e}")
                    self.stats["errors"] += 1
            
            self.stats["ticks_processed"] += success_count
            self.stats["last_processing_time"] = datetime.now(timezone.utc)
            
            self.logger.info(f"✅ Successfully processed {success_count}/{len(dukascopy_data)} historical ticks from {source_name}")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"Failed to process historical ticks from {source_name}: {e}")
            self.stats["errors"] += 1
            return False
    
    @performance_tracked("unknown-service", "process_economic_events")
    async def process_economic_events(self, events: List[Union[MQL5EconomicEvent, DataBridgeEconomicEvent]], source_name: str = "unknown") -> bool:
        """Transform economic events and send to database storage"""
        try:
            self.logger.info(f"Processing {len(events)} economic events from {source_name}")
            
            # Transform events to database format
            processed_events = []
            for event in events:
                if isinstance(event, MQL5EconomicEvent):
                    event_dict = self._transform_mql5_event(event)
                elif isinstance(event, DataBridgeEconomicEvent):
                    event_dict = self._transform_tradingview_event(event)
                else:
                    # Handle dict or other formats
                    event_dict = self._transform_generic_event(event, source_name)
                
                if event_dict:
                    processed_events.append(event_dict)
            
            # Send to database service directly (economic events don't use batch processor)
            if processed_events:
                success = await self._store_economic_events(processed_events, source_name)
                if success:
                    self.stats["economic_events_processed"] += len(processed_events)
                    self.stats["last_processing_time"] = datetime.now(timezone.utc)
                    self.logger.info(f"✅ Successfully stored {len(processed_events)} economic events from {source_name}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to process economic events from {source_name}: {e}")
            self.stats["errors"] += 1
            return False
    
    def _transform_mql5_event(self, event: MQL5EconomicEvent) -> Dict[str, Any]:
        """Transform MQL5 economic event to database format"""
        try:
            return {
                "timestamp": event.datetime.isoformat() if event.datetime else datetime.now(timezone.utc).isoformat(),
                "event_name": event.name or "Unknown Event",
                "currency": event.currency or "USD",
                "impact": event.importance or "medium",
                "forecast": str(event.forecast) if event.forecast is not None else None,
                "previous": str(event.previous) if event.previous is not None else None,
                "actual": str(event.actual) if event.actual is not None else None,
                "source": "mql5",
                "event_id": f"mql5_{event.name}_{event.datetime.strftime('%Y%m%d_%H%M') if event.datetime else 'unknown'}",
                "description": event.name or ""
            }
        except Exception as e:
            self.logger.warning(f"Failed to transform MQL5 event: {e}")
            return None
    
    def _transform_tradingview_event(self, event: DataBridgeEconomicEvent) -> Dict[str, Any]:
        """Transform TradingView economic event to database format"""
        try:
            return {
                "timestamp": event.datetime.isoformat() if event.datetime else datetime.now(timezone.utc).isoformat(),
                "event_name": event.event_name or "Unknown Event",
                "currency": event.currency or "USD", 
                "impact": event.impact or "medium",
                "forecast": event.forecast,
                "previous": event.previous,
                "actual": event.actual,
                "source": "tradingview",
                "event_id": f"tradingview_{event.event_name}_{event.datetime.strftime('%Y%m%d_%H%M') if event.datetime else 'unknown'}",
                "description": event.event_name or ""
            }
        except Exception as e:
            self.logger.warning(f"Failed to transform TradingView event: {e}")
            return None
    
    def _transform_generic_event(self, event: Union[Dict, Any], source_name: str) -> Dict[str, Any]:
        """Transform generic event format to database format"""
        try:
            if isinstance(event, dict):
                return {
                    "timestamp": event.get("datetime", event.get("timestamp", datetime.now(timezone.utc).isoformat())),
                    "event_name": event.get("name", event.get("event_name", "Unknown Event")),
                    "currency": event.get("currency", "USD"),
                    "impact": event.get("impact", event.get("importance", "medium")),
                    "forecast": str(event.get("forecast")) if event.get("forecast") is not None else None,
                    "previous": str(event.get("previous")) if event.get("previous") is not None else None,
                    "actual": str(event.get("actual")) if event.get("actual") is not None else None,
                    "source": source_name,
                    "event_id": f"{source_name}_{event.get('name', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M')}",
                    "description": event.get("description", event.get("name", ""))
                }
            else:
                # Try to convert object to dict
                event_dict = asdict(event) if hasattr(event, '__dataclass_fields__') else vars(event)
                return self._transform_generic_event(event_dict, source_name)
                
        except Exception as e:
            self.logger.warning(f"Failed to transform generic event from {source_name}: {e}")
            return None
    
    async def _store_economic_events(self, events: List[Dict[str, Any]], source_name: str) -> bool:
        """Store economic events to database service"""
        try:
            # For now, we'll store each event individually
            # TODO: Implement bulk insert for economic events
            success_count = 0
            
            for event in events:
                try:
                    # Send to database service (implement economic calendar endpoint)
                    response = await self.database_client.insert_economic_event(event)
                    if response and response.get("success", False):
                        success_count += 1
                    else:
                        self.logger.warning(f"Failed to store economic event: {event.get('event_name', 'unknown')}")
                        
                except Exception as e:
                    self.logger.error(f"Failed to send economic event to database: {e}")
            
            self.logger.info(f"Stored {success_count}/{len(events)} economic events from {source_name}")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"Failed to store economic events from {source_name}: {e}")
            return False
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get pipeline processing statistics"""
        return {
            "ticks_processed": self.stats["ticks_processed"],
            "economic_events_processed": self.stats["economic_events_processed"],
            "total_processed": self.stats["ticks_processed"] + self.stats["economic_events_processed"],
            "errors": self.stats["errors"],
            "last_processing_time": self.stats["last_processing_time"].isoformat() if self.stats["last_processing_time"] else None,
            "pipeline_healthy": self.stats["errors"] < 10  # Simple health check
        }


# Global pipeline instance
_data_source_pipeline: Optional[DataSourcePipeline] = None


async def get_data_source_pipeline() -> DataSourcePipeline:
    """Get global data source pipeline instance"""
    global _data_source_pipeline
    if _data_source_pipeline is None:
        # Import here to avoid circular imports
        from .batch_processor import get_batch_processor
        from .database_client import get_database_client
        
        batch_processor = await get_batch_processor()
        database_client = await get_database_client()
        _data_source_pipeline = DataSourcePipeline(batch_processor, database_client)
    
    return _data_source_pipeline


async def cleanup_data_source_pipeline():
    """Cleanup global pipeline"""
    global _data_source_pipeline
    if _data_source_pipeline:
        _data_source_pipeline = None


# Export main classes and functions
__all__ = [
    "DataSourcePipeline",
    "get_data_source_pipeline", 
    "cleanup_data_source_pipeline"
]