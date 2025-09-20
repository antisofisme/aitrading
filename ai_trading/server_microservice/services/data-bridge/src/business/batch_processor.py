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
Batch Processor for Tick Data Storage - High-performance batch processing
Collects tick data and processes them in batches for optimal database performance
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict

# Service-specific infrastructure  
from .database_client import get_database_client, DatabaseServiceClient

@dataclass
class BatchConfig:
    """Configuration for batch processing"""
    max_batch_size: int = 100
    max_wait_time_seconds: float = 5.0
    max_memory_batches: int = 10
    flush_on_symbol_change: bool = False
    enable_compression: bool = True

@dataclass
class SymbolBatch:
    """Batch data for a specific symbol"""
    symbol: str
    ticks: List[Dict[str, Any]] = field(default_factory=list)
    first_tick_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_tick_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    batch_id: str = field(default_factory=lambda: f"batch_{int(time.time()*1000)}")
    
    def add_tick(self, tick_data: Dict[str, Any]):
        """Add tick data to batch"""
        self.ticks.append(tick_data)
        self.last_tick_time = datetime.now(timezone.utc)
    
    def is_ready_for_flush(self, config: BatchConfig) -> bool:
        """Check if batch is ready for flushing"""
        # Size-based flush
        if len(self.ticks) >= config.max_batch_size:
            return True
        
        # Time-based flush
        time_diff = (datetime.now(timezone.utc) - self.first_tick_time).total_seconds()
        if time_diff >= config.max_wait_time_seconds:
            return True
        
        return False
    
    def get_batch_info(self) -> Dict[str, Any]:
        """Get batch information"""
        duration = (self.last_tick_time - self.first_tick_time).total_seconds()
        return {
            "batch_id": self.batch_id,
            "symbol": self.symbol,
            "tick_count": len(self.ticks),
            "duration_seconds": duration,
            "first_tick": self.first_tick_time.isoformat(),
            "last_tick": self.last_tick_time.isoformat(),
            "ticks_per_second": len(self.ticks) / duration if duration > 0 else 0
        }

class TickDataBatchProcessor:
    """
    High-performance batch processor for tick data storage
    
    Features:
    - Symbol-based batching for optimal database partitioning
    - Time and size-based flush triggers
    - Background processing with asyncio
    - Error handling and retry logic
    - Performance metrics and monitoring
    """
    
    def __init__(self, config: BatchConfig = None):
        self.config = config or BatchConfig()
        self.logger = get_logger("tick-batch-processor", "001")
        
        # Symbol-based batches
        self.symbol_batches: Dict[str, SymbolBatch] = {}
        self.processing_lock = asyncio.Lock()
        
        # Background processing
        self.processor_task: Optional[asyncio.Task] = None
        self.is_running = False
        
        # Database client
        self.db_client: Optional[DatabaseServiceClient] = None
        
        # Metrics
        self.metrics = {
            "total_ticks_received": 0,
            "total_ticks_processed": 0,
            "total_batches_processed": 0,
            "successful_batches": 0,
            "failed_batches": 0,
            "current_batch_count": 0,
            "average_batch_size": 0.0,
            "processing_rate_per_second": 0.0,
            "last_flush_time": None,
            "processor_start_time": datetime.now(timezone.utc)
        }
        
        self.logger.info(f"Batch processor initialized - max_batch_size: {self.config.max_batch_size}, max_wait_time: {self.config.max_wait_time_seconds}s")
    
    async def start(self):
        """Start the background batch processor"""
        if self.is_running:
            self.logger.warning("Batch processor already running")
            return
        
        try:
            # Initialize database client
            self.db_client = await get_database_client()
            
            # Start background processor
            self.is_running = True
            self.processor_task = asyncio.create_task(self._background_processor())
            
            self.logger.info("Batch processor started successfully")
            
        except Exception as e:
            error_context = {"operation": "start_batch_processor"}
            handle_error("tick-batch-processor", e, context=error_context)
            raise
    
    async def stop(self):
        """Stop the batch processor and flush remaining data"""
        self.logger.info("Stopping batch processor...")
        
        # Stop background processor
        self.is_running = False
        
        if self.processor_task:
            self.processor_task.cancel()
            try:
                await self.processor_task
            except asyncio.CancelledError:
                pass
        
        # Flush remaining batches
        await self._flush_all_batches()
        
        self.logger.info("Batch processor stopped")
    
    @performance_tracked("tick-batch-processor", "add_tick")
    async def add_tick(self, tick_data: Dict[str, Any]):
        """
        Add tick data to batch processing queue
        
        Args:
            tick_data: Tick data dictionary
        """
        try:
            async with self.processing_lock:
                symbol = tick_data.get("symbol", "UNKNOWN")
                
                # Create new batch if doesn't exist
                if symbol not in self.symbol_batches:
                    self.symbol_batches[symbol] = SymbolBatch(symbol=symbol)
                
                # Add tick to symbol batch
                self.symbol_batches[symbol].add_tick(tick_data)
                self.metrics["total_ticks_received"] += 1
                
                # Check if batch is ready for immediate flush
                batch = self.symbol_batches[symbol]
                if batch.is_ready_for_flush(self.config):
                    # Create background task for flushing (non-blocking)
                    asyncio.create_task(self._flush_symbol_batch(symbol))
                
                # Update metrics
                self.metrics["current_batch_count"] = len(self.symbol_batches)
                
                self.logger.debug(f"Tick added to batch: {symbol} (batch size: {len(batch.ticks)})")
                
        except Exception as e:
            error_context = {
                "operation": "add_tick",
                "symbol": tick_data.get("symbol", "unknown")
            }
            handle_error("tick-batch-processor", e, context=error_context)
    
    async def _background_processor(self):
        """Background processor for time-based batch flushing"""
        self.logger.info("Background batch processor started")
        
        while self.is_running:
            try:
                # Sleep for batch check interval
                await asyncio.sleep(1.0)
                
                # Check all batches for time-based flushing
                await self._check_and_flush_time_based_batches()
                
                # Update processing rate metrics
                self._update_processing_metrics()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                error_context = {"operation": "background_processor"}
                handle_error("tick-batch-processor", e, context=error_context)
                # Continue processing even if there's an error
                await asyncio.sleep(1.0)
        
        self.logger.info("Background batch processor stopped")
    
    async def _check_and_flush_time_based_batches(self):
        """Check and flush batches that exceed time limits"""
        symbols_to_flush = []
        
        async with self.processing_lock:
            for symbol, batch in self.symbol_batches.items():
                if batch.is_ready_for_flush(self.config):
                    symbols_to_flush.append(symbol)
        
        # Flush identified batches
        for symbol in symbols_to_flush:
            asyncio.create_task(self._flush_symbol_batch(symbol))
    
    @performance_tracked("tick-batch-processor", "flush_symbol_batch")
    async def _flush_symbol_batch(self, symbol: str):
        """Flush a specific symbol batch to database"""
        try:
            batch_to_flush = None
            
            # Extract batch safely
            async with self.processing_lock:
                if symbol in self.symbol_batches and self.symbol_batches[symbol].ticks:
                    batch_to_flush = self.symbol_batches[symbol]
                    # Create new batch for continued processing
                    self.symbol_batches[symbol] = SymbolBatch(symbol=symbol)
            
            if not batch_to_flush or not batch_to_flush.ticks:
                return
            
            # Store batch in database
            if self.db_client:
                batch_info = batch_to_flush.get_batch_info()
                self.logger.info(f"Flushing batch: {symbol} - {len(batch_to_flush.ticks)} ticks")
                
                result = await self.db_client.store_tick_batch(batch_to_flush.ticks)
                
                if result["success"]:
                    self.metrics["successful_batches"] += 1
                    self.metrics["total_ticks_processed"] += result["stored_count"]
                    self.metrics["total_batches_processed"] += 1
                    self.metrics["last_flush_time"] = datetime.now(timezone.utc)
                    
                    self.logger.info(f"Batch flushed successfully: {batch_info}")
                else:
                    self.metrics["failed_batches"] += 1
                    self.logger.error(f"Failed to flush batch: {symbol} - {result['errors']}")
            else:
                self.logger.error("Database client not available for batch flush")
                
        except Exception as e:
            error_context = {
                "operation": "flush_symbol_batch",
                "symbol": symbol
            }
            handle_error("tick-batch-processor", e, context=error_context)
            self.metrics["failed_batches"] += 1
    
    async def _flush_all_batches(self):
        """Flush all remaining batches"""
        symbols_to_flush = list(self.symbol_batches.keys())
        
        self.logger.info(f"Flushing all remaining batches: {len(symbols_to_flush)} symbols")
        
        # Flush all batches concurrently
        flush_tasks = [self._flush_symbol_batch(symbol) for symbol in symbols_to_flush]
        await asyncio.gather(*flush_tasks, return_exceptions=True)
        
        self.logger.info("All batches flushed")
    
    def _update_processing_metrics(self):
        """Update processing rate and other metrics"""
        current_time = datetime.now(timezone.utc)
        uptime = (current_time - self.metrics["processor_start_time"]).total_seconds()
        
        if uptime > 0:
            self.metrics["processing_rate_per_second"] = self.metrics["total_ticks_processed"] / uptime
        
        if self.metrics["total_batches_processed"] > 0:
            self.metrics["average_batch_size"] = (
                self.metrics["total_ticks_processed"] / self.metrics["total_batches_processed"]
            )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get processor metrics"""
        current_batches_info = {}
        total_pending_ticks = 0
        
        for symbol, batch in self.symbol_batches.items():
            current_batches_info[symbol] = batch.get_batch_info()
            total_pending_ticks += len(batch.ticks)
        
        success_rate = (
            (self.metrics["successful_batches"] / self.metrics["total_batches_processed"] * 100)
            if self.metrics["total_batches_processed"] > 0 else 0
        )
        
        return {
            **self.metrics,
            "success_rate_percent": round(success_rate, 2),
            "pending_ticks": total_pending_ticks,
            "current_batches": current_batches_info,
            "is_running": self.is_running,
            "config": {
                "max_batch_size": self.config.max_batch_size,
                "max_wait_time_seconds": self.config.max_wait_time_seconds
            }
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get processor status"""
        return {
            "status": "running" if self.is_running else "stopped",
            "active_symbols": len(self.symbol_batches),
            "pending_ticks": sum(len(batch.ticks) for batch in self.symbol_batches.values()),
            "total_processed": self.metrics["total_ticks_processed"],
            "processing_rate": round(self.metrics["processing_rate_per_second"], 2),
            "database_connected": self.db_client is not None
        }

# Global batch processor instance
_batch_processor: Optional[TickDataBatchProcessor] = None

async def get_batch_processor() -> TickDataBatchProcessor:
    """Get global batch processor instance"""
    global _batch_processor
    if _batch_processor is None:
        _batch_processor = TickDataBatchProcessor()
        await _batch_processor.start()
    return _batch_processor

async def cleanup_batch_processor():
    """Cleanup global batch processor"""
    global _batch_processor
    if _batch_processor:
        await _batch_processor.stop()
        _batch_processor = None

# Export main classes and functions
__all__ = [
    "TickDataBatchProcessor",
    "BatchConfig",
    "SymbolBatch",
    "get_batch_processor",
    "cleanup_batch_processor"
]