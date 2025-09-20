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
Deduplication Management API Endpoints
Provides REST API access to deduplication functionality for historical data downloads

Endpoints:
- GET /deduplication/status - Get deduplication system status
- POST /deduplication/check - Check if download is needed for specific time range
- GET /deduplication/recommendations - Get download recommendations
- POST /deduplication/gaps/detect - Detect gaps in downloaded data
- GET /deduplication/stats - Get comprehensive deduplication statistics
- DELETE /deduplication/cache - Clear deduplication cache
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

# Service-specific infrastructure
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))

try:
    from shared.infrastructure.core.logger_core import get_logger
    from shared.infrastructure.core.performance_core import performance_tracked
except ImportError as e:
    print(f"⚠️ Infrastructure import issue: {e}")
    import logging
    get_logger = lambda name, version=None: logging.getLogger(name)
    performance_tracked = lambda service, operation: lambda func: func
from ..business.deduplication_manager import get_deduplication_manager

logger = get_logger("data-bridge", "deduplication-api")

# Create router
router = APIRouter()

# Pydantic models for request/response validation
class DownloadCheckRequest(BaseModel):
    """Request model for download necessity check"""
    symbol: str = Field(..., description="Trading symbol (e.g., EURUSD)")
    source: str = Field(..., description="Data source (e.g., dukascopy, truefx)")
    start_time: datetime = Field(..., description="Start time for data range")
    end_time: datetime = Field(..., description="End time for data range")

class GapDetectionRequest(BaseModel):
    """Request model for gap detection"""
    symbol: str = Field(..., description="Trading symbol")
    source: str = Field(..., description="Data source")
    overall_start: datetime = Field(..., description="Overall start time for gap analysis")
    overall_end: datetime = Field(..., description="Overall end time for gap analysis")
    expected_frequency: str = Field(default="hourly", description="Expected data frequency")

class DeduplicationStatusResponse(BaseModel):
    """Response model for deduplication status"""
    status: str
    manager_initialized: bool
    total_symbols_tracked: int
    total_records: int
    total_files_tracked: int
    cache_stats: Dict[str, Any]
    last_update: datetime

@router.get("/deduplication/status", response_model=DeduplicationStatusResponse)
@performance_tracked("unknown-service", "dedup_status")
async def get_deduplication_status():
    """
    Get current status of the deduplication system
    
    Returns comprehensive information about the deduplication manager state
    """
    try:
        dedup_manager = await get_deduplication_manager()
        stats = dedup_manager.get_deduplication_stats()
        
        response = DeduplicationStatusResponse(
            status="active",
            manager_initialized=True,
            total_symbols_tracked=stats["registry_summary"]["total_symbols"],
            total_records=stats["registry_summary"]["total_records"],
            total_files_tracked=stats["registry_summary"]["total_files_tracked"],
            cache_stats={
                "downloads_prevented": stats["downloads_prevented"],
                "files_verified": stats["files_verified"],
                "cache_hits": stats["cache_hits"],
                "integrity_failures": stats["integrity_failures"]
            },
            last_update=stats["last_update"]
        )
        
        logger.info("Deduplication status requested", {
            "total_symbols": response.total_symbols_tracked,
            "total_records": response.total_records
        })
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting deduplication status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get deduplication status: {str(e)}")

@router.post("/deduplication/check")
@performance_tracked("unknown-service", "dedup_check_download_needed")
async def check_download_needed(request: DownloadCheckRequest):
    """
    Check if a download is needed for the specified time range
    
    Returns detailed information about missing data ranges and existing coverage
    """
    try:
        dedup_manager = await get_deduplication_manager()
        
        result = await dedup_manager.check_download_needed(
            symbol=request.symbol,
            source=request.source,
            start_time=request.start_time,
            end_time=request.end_time
        )
        
        logger.info(f"Download check completed for {request.symbol} {request.source}", {
            "needed": result["needed"],
            "missing_ranges": len(result["missing_ranges"]),
            "coverage_percent": result["coverage_percent"]
        })
        
        return {
            "status": "success",
            "symbol": request.symbol,
            "source": request.source,
            "time_range": {
                "start": request.start_time.isoformat(),
                "end": request.end_time.isoformat()
            },
            "download_needed": result["needed"],
            "missing_ranges": result["missing_ranges"],
            "existing_ranges": result["existing_ranges"],
            "coverage_percent": result["coverage_percent"],
            "total_hours_missing": result["total_hours_missing"],
            "reason": result["reason"]
        }
        
    except Exception as e:
        logger.error(f"Error checking download needed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check download status: {str(e)}")

@router.get("/deduplication/recommendations")
@performance_tracked("unknown-service", "dedup_get_recommendations")
async def get_download_recommendations(
    symbol: str = Query(..., description="Trading symbol"),
    source: str = Query(..., description="Data source")
):
    """
    Get recommendations for what data should be downloaded next
    
    Returns prioritized list of gaps that should be filled
    """
    try:
        dedup_manager = await get_deduplication_manager()
        
        recommendations = await dedup_manager.get_download_recommendations(symbol, source)
        
        logger.info(f"Download recommendations generated for {symbol} {source}", {
            "total_gaps": recommendations.get("total_gaps", 0),
            "high_priority": recommendations.get("high_priority_gaps", 0)
        })
        
        return {
            "status": "success",
            "symbol": symbol,
            "source": source,
            "timestamp": datetime.now().isoformat(),
            **recommendations
        }
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")

@router.post("/deduplication/gaps/detect")
@performance_tracked("unknown-service", "dedup_detect_gaps")
async def detect_data_gaps(request: GapDetectionRequest):
    """
    Detect gaps in downloaded data for a symbol and source
    
    Analyzes existing data and identifies missing time periods
    """
    try:
        dedup_manager = await get_deduplication_manager()
        
        gaps = await dedup_manager.detect_gaps(
            symbol=request.symbol,
            source=request.source,
            overall_start=request.overall_start,
            overall_end=request.overall_end,
            expected_frequency=request.expected_frequency
        )
        
        gap_list = [
            {
                "gap_start": gap.gap_start.isoformat(),
                "gap_end": gap.gap_end.isoformat(),
                "priority": gap.priority,
                "reason": gap.reason,
                "duration_hours": (gap.gap_end - gap.gap_start).total_seconds() / 3600
            }
            for gap in gaps
        ]
        
        logger.info(f"Gap detection completed for {request.symbol} {request.source}", {
            "gaps_found": len(gaps),
            "high_priority_gaps": len([g for g in gaps if g.priority == "high"])
        })
        
        return {
            "status": "success",
            "symbol": request.symbol,
            "source": request.source,
            "analysis_range": {
                "start": request.overall_start.isoformat(),
                "end": request.overall_end.isoformat()
            },
            "expected_frequency": request.expected_frequency,
            "gaps_detected": len(gaps),
            "gaps": gap_list,
            "summary": {
                "total_gaps": len(gaps),
                "high_priority_gaps": len([g for g in gaps if g.priority == "high"]),
                "medium_priority_gaps": len([g for g in gaps if g.priority == "medium"]),
                "total_gap_hours": sum((gap.gap_end - gap.gap_start).total_seconds() / 3600 for gap in gaps)
            }
        }
        
    except Exception as e:
        logger.error(f"Error detecting gaps: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to detect gaps: {str(e)}")

@router.get("/deduplication/stats")
@performance_tracked("unknown-service", "dedup_get_stats")
async def get_deduplication_statistics():
    """
    Get comprehensive deduplication statistics
    
    Returns detailed metrics about the deduplication system performance
    """
    try:
        dedup_manager = await get_deduplication_manager()
        stats = dedup_manager.get_deduplication_stats()
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "deduplication_stats": stats,
            "performance_summary": {
                "downloads_prevented": stats["downloads_prevented"],
                "efficiency_percent": (
                    stats["downloads_prevented"] / 
                    max(1, stats["downloads_prevented"] + stats.get("downloads_performed", 0))
                ) * 100,
                "integrity_check_success_rate": (
                    (stats["files_verified"] - stats["integrity_failures"]) /
                    max(1, stats["files_verified"])
                ) * 100 if stats["files_verified"] > 0 else 100,
                "cache_hit_rate": (
                    stats["cache_hits"] / 
                    max(1, stats["cache_hits"] + stats.get("cache_misses", 0))
                ) * 100 if "cache_hits" in stats else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting deduplication statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@router.delete("/deduplication/cache")
@performance_tracked("unknown-service", "dedup_clear_cache")
async def clear_deduplication_cache():
    """
    Clear deduplication cache
    
    Forces refresh of all cached deduplication checks
    """
    try:
        dedup_manager = await get_deduplication_manager()
        
        # Clear the cache
        if hasattr(dedup_manager, 'cache'):
            cache_size_before = len(dedup_manager.cache._cache) if hasattr(dedup_manager.cache, '_cache') else 0
            dedup_manager.cache.clear()
            
            logger.info(f"Deduplication cache cleared", {
                "cache_entries_removed": cache_size_before
            })
            
            return {
                "status": "success",
                "message": "Deduplication cache cleared successfully",
                "cache_entries_removed": cache_size_before,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "success",
                "message": "No cache to clear",
                "timestamp": datetime.now().isoformat()
            }
        
    except Exception as e:
        logger.error(f"Error clearing deduplication cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

@router.post("/deduplication/smart-download")
@performance_tracked("unknown-service", "dedup_smart_download")
async def initiate_smart_download(
    background_tasks: BackgroundTasks,
    symbol: str = Query(..., description="Trading symbol"),
    source: str = Query(default="dukascopy", description="Data source"),
    hours_back: int = Query(default=24, description="Hours back from now"),
    auto_process: bool = Query(default=True, description="Auto-process downloaded files")
):
    """
    Initiate a smart download that uses deduplication to avoid redundant downloads
    
    This endpoint starts a background download task that only downloads missing data
    """
    try:
        # Validate inputs
        if hours_back < 1 or hours_back > 8760:  # Max 1 year
            raise HTTPException(status_code=400, detail="hours_back must be between 1 and 8760")
        
        if source not in ["dukascopy", "truefx"]:
            raise HTTPException(status_code=400, detail="source must be 'dukascopy' or 'truefx'")
        
        # Start background download task
        task_id = f"{symbol}_{source}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        background_tasks.add_task(
            _execute_smart_download,
            task_id=task_id,
            symbol=symbol,
            source=source,
            hours_back=hours_back,
            auto_process=auto_process
        )
        
        logger.info(f"Smart download initiated", {
            "task_id": task_id,
            "symbol": symbol,
            "source": source,
            "hours_back": hours_back
        })
        
        return {
            "status": "success",
            "message": "Smart download initiated",
            "task_id": task_id,
            "symbol": symbol,
            "source": source,
            "hours_back": hours_back,
            "estimated_start_time": datetime.now().isoformat(),
            "estimated_duration_minutes": max(1, hours_back // 10)  # Rough estimate
        }
        
    except Exception as e:
        logger.error(f"Error initiating smart download: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate download: {str(e)}")

# Background task for smart downloads
async def _execute_smart_download(task_id: str, symbol: str, source: str, 
                                hours_back: int, auto_process: bool):
    """Execute smart download in background"""
    try:
        logger.info(f"Executing smart download task {task_id}")
        
        if source == "dukascopy":
            from ..data_sources.dukascopy_client import DataBridgeDukascopyDownloader
            downloader = DataBridgeDukascopyDownloader()
            result = await downloader.download_small_batch(
                pair=symbol,
                hours_back=hours_back
            )
        else:
            # Other sources can be added here
            raise NotImplementedError(f"Smart download not yet implemented for {source}")
        
        logger.info(f"Smart download task {task_id} completed", {
            "files_downloaded": result.get("files_downloaded", 0),
            "files_skipped": result.get("files_skipped_dedup", 0),
            "success_rate": result.get("success_rate", 0)
        })
        
    except Exception as e:
        logger.error(f"Smart download task {task_id} failed: {e}")

# Add router tags and metadata
router.tags = ["Deduplication Management"]