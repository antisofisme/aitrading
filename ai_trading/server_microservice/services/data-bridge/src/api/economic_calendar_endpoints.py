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
Economic Calendar API Endpoints - Comprehensive REST API for Economic Events
Production-ready endpoints for the data-bridge microservice

FEATURES:
- Real-time economic event monitoring
- Historical event access with filtering
- Monitor control (start/stop/status)
- Data sources health checks
- Integration with MQL5 and TradingView scrapers
- Performance tracking and error handling
"""

import json
from datetime import datetime, timezone, timedelta, date
from typing import Dict, Any, List, Optional
from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Query, Body, BackgroundTasks, Depends
from pydantic import BaseModel, Field, validator
from fastapi.responses import JSONResponse

# Shared infrastructure
try:
    from shared.infrastructure.core.error_core import handle_error
    from shared.infrastructure.core.performance_core import performance_tracked
    from shared.infrastructure.core.config_core import CoreConfig
except ImportError:
    pass

# Business logic components
from ..business.economic_calendar_monitor import get_economic_calendar_monitor, start_economic_calendar_monitoring
from ..business.data_source_pipeline import get_data_source_pipeline
from ..data_sources.mql5_scraper import get_mql5_widget_events, MQL5EconomicEvent
from ..data_sources.tradingview_scraper import DataBridgeTradingViewScraper, DataBridgeEconomicEvent

# Initialize logger and config
logger = get_logger("data-bridge", "economic-calendar-api")
config = CoreConfig("data-bridge")

# Create router
router = APIRouter()

# Pydantic models for API requests/responses
class EventFilterRequest(BaseModel):
    """Request model for filtering economic events"""
    currencies: Optional[List[str]] = Field(None, description="Filter by currencies (e.g., ['USD', 'EUR'])")
    importance: Optional[str] = Field(None, description="Filter by importance: low, medium, high")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD format)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD format)")
    event_name: Optional[str] = Field(None, description="Filter by event name (partial match)")
    source: Optional[str] = Field(None, description="Filter by source: mql5, tradingview")
    limit: Optional[int] = Field(100, ge=1, le=1000, description="Maximum number of events to return")
    
    @validator('importance')
    def validate_importance(cls, v):
        if v and v.lower() not in ['low', 'medium', 'high']:
            raise ValueError("Importance must be 'low', 'medium', or 'high'")
        return v.lower() if v else v
    
    @validator('source')
    def validate_source(cls, v):
        if v and v.lower() not in ['mql5', 'tradingview']:
            raise ValueError("Source must be 'mql5' or 'tradingview'")
        return v.lower() if v else v


class MonitorConfigRequest(BaseModel):
    """Request model for monitor configuration"""
    check_interval_seconds: Optional[int] = Field(None, ge=10, le=3600, description="Check interval in seconds")
    event_tolerance_minutes: Optional[int] = Field(None, ge=1, le=60, description="Event tolerance in minutes")
    refresh_interval_hours: Optional[int] = Field(None, ge=1, le=24, description="Refresh interval in hours")


class ScraperTestRequest(BaseModel):
    """Request model for testing scrapers"""
    source: str = Field(..., description="Source to test: mql5 or tradingview")
    start_date: Optional[str] = Field(None, description="Start date for TradingView (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date for TradingView (YYYY-MM-DD)")
    
    @validator('source')
    def validate_source(cls, v):
        if v.lower() not in ['mql5', 'tradingview']:
            raise ValueError("Source must be 'mql5' or 'tradingview'")
        return v.lower()


# ===== MONITOR STATUS AND CONTROL ENDPOINTS =====

@router.get("/status")
@performance_tracked("economic-calendar-api", "get_monitor_status")
async def get_economic_calendar_status():
    """Get comprehensive economic calendar monitoring status"""
    try:
        logger.info("Getting economic calendar monitoring status")
        
        try:
            monitor = await get_economic_calendar_monitor()
            stats = monitor.get_monitor_stats()
            
            # Get upcoming events count
            current_time = datetime.now(timezone.utc)
            upcoming_events = [
                event for event in monitor.scheduled_events.values()
                if event.scheduled_time > current_time and not event.processed
            ]
            
            return {
                "success": True,
                "status": "active",
                "monitor_healthy": True,
                "monitoring_stats": stats,
                "upcoming_events_count": len(upcoming_events),
                "next_events": [
                    {
                        "event_name": event.event_name,
                        "scheduled_time": event.scheduled_time.isoformat(),
                        "currency": event.currency,
                        "importance": event.importance,
                        "time_until_minutes": (event.scheduled_time - current_time).total_seconds() / 60
                    }
                    for event in sorted(upcoming_events, key=lambda e: e.scheduled_time)[:5]
                ],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as monitor_error:
            logger.warning(f"Economic calendar monitor not available: {monitor_error}")
            
            return {
                "success": True,
                "status": "fallback_mode", 
                "monitor_healthy": False,
                "message": "Real-time monitoring not active, using periodic collection",
                "error": str(monitor_error),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
    except Exception as e:
        logger.error(f"Error getting economic calendar status: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


@router.post("/monitor/start")
@performance_tracked("economic-calendar-api", "start_monitor")
async def start_economic_calendar_monitor(background_tasks: BackgroundTasks):
    """Start the economic calendar monitor"""
    try:
        logger.info("Starting economic calendar monitor")
        
        # Add monitoring as background task
        background_tasks.add_task(start_economic_calendar_monitoring)
        
        return {
            "success": True,
            "message": "Economic calendar monitor started",
            "status": "starting",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting economic calendar monitor: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


@router.post("/monitor/configure")
@performance_tracked("economic-calendar-api", "configure_monitor") 
async def configure_monitor(config_request: MonitorConfigRequest):
    """Configure economic calendar monitor settings"""
    try:
        logger.info("Configuring economic calendar monitor")
        
        monitor = await get_economic_calendar_monitor()
        
        # Update configuration
        if config_request.check_interval_seconds:
            monitor.check_interval_seconds = config_request.check_interval_seconds
            
        if config_request.event_tolerance_minutes:
            monitor.event_tolerance_minutes = config_request.event_tolerance_minutes
            
        if config_request.refresh_interval_hours:
            monitor.refresh_interval_hours = config_request.refresh_interval_hours
            # Update next refresh time
            monitor.next_refresh = datetime.now(timezone.utc) + timedelta(hours=config_request.refresh_interval_hours)
        
        return {
            "success": True,
            "message": "Monitor configuration updated",
            "configuration": {
                "check_interval_seconds": monitor.check_interval_seconds,
                "event_tolerance_minutes": monitor.event_tolerance_minutes,
                "refresh_interval_hours": monitor.refresh_interval_hours,
                "next_refresh": monitor.next_refresh.isoformat()
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error configuring monitor: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


# ===== EVENT RETRIEVAL ENDPOINTS =====

@router.get("/events/upcoming")
@performance_tracked("economic-calendar-api", "get_upcoming_events")
async def get_upcoming_economic_events(
    hours: int = Query(24, ge=1, le=168, description="Hours ahead to look for events"),
    currencies: Optional[str] = Query(None, description="Comma-separated currencies (e.g., 'USD,EUR,GBP')"),
    importance: Optional[str] = Query(None, description="Filter by importance: low, medium, high"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of events to return")
):
    """Get upcoming economic events with filtering"""
    try:
        logger.info(f"Getting upcoming economic events (next {hours} hours)")
        
        try:
            monitor = await get_economic_calendar_monitor()
            current_time = datetime.now(timezone.utc)
            end_time = current_time + timedelta(hours=hours)
            
            # Filter events
            upcoming_events = []
            for event in monitor.scheduled_events.values():
                if (event.scheduled_time > current_time and 
                    event.scheduled_time <= end_time and 
                    not event.processed):
                    
                    # Apply filters
                    if currencies:
                        currency_list = [c.strip().upper() for c in currencies.split(',')]
                        if event.currency not in currency_list:
                            continue
                    
                    if importance:
                        if event.importance.lower() != importance.lower():
                            continue
                    
                    upcoming_events.append({
                        "event_id": event.event_id,
                        "event_name": event.event_name,
                        "scheduled_time": event.scheduled_time.isoformat(),
                        "currency": event.currency,
                        "importance": event.importance,
                        "source": event.source,
                        "forecast": event.forecast,
                        "previous": event.previous,
                        "time_until_minutes": (event.scheduled_time - current_time).total_seconds() / 60,
                        "processed": event.processed
                    })
            
            # Sort by scheduled time and apply limit
            upcoming_events.sort(key=lambda x: x["scheduled_time"])
            upcoming_events = upcoming_events[:limit]
            
            return {
                "success": True,
                "upcoming_events": upcoming_events,
                "count": len(upcoming_events),
                "filters_applied": {
                    "hours_ahead": hours,
                    "currencies": currencies.split(',') if currencies else None,
                    "importance": importance,
                    "limit": limit
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as monitor_error:
            logger.warning(f"Monitor not available, using fallback data: {monitor_error}")
            
            return {
                "success": True,
                "upcoming_events": [],
                "count": 0,
                "message": "Real-time monitoring not active",
                "error": str(monitor_error),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
    except Exception as e:
        logger.error(f"Error getting upcoming events: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


@router.post("/events/filter")
@performance_tracked("economic-calendar-api", "filter_events")
async def filter_economic_events(filter_request: EventFilterRequest):
    """Filter economic events with advanced criteria"""
    try:
        logger.info("Filtering economic events with advanced criteria")
        
        monitor = await get_economic_calendar_monitor()
        filtered_events = []
        
        for event in monitor.scheduled_events.values():
            # Apply filters
            if filter_request.currencies and event.currency not in filter_request.currencies:
                continue
                
            if filter_request.importance and event.importance.lower() != filter_request.importance:
                continue
                
            if filter_request.source and event.source.lower() != filter_request.source:
                continue
                
            if filter_request.event_name and filter_request.event_name.lower() not in event.event_name.lower():
                continue
                
            # Date filtering
            if filter_request.start_date:
                start_date = datetime.fromisoformat(filter_request.start_date).replace(tzinfo=timezone.utc)
                if event.scheduled_time < start_date:
                    continue
                    
            if filter_request.end_date:
                end_date = datetime.fromisoformat(filter_request.end_date).replace(tzinfo=timezone.utc)
                if event.scheduled_time > end_date:
                    continue
            
            filtered_events.append({
                "event_id": event.event_id,
                "event_name": event.event_name,
                "scheduled_time": event.scheduled_time.isoformat(),
                "currency": event.currency,
                "importance": event.importance,
                "source": event.source,
                "forecast": event.forecast,
                "previous": event.previous,
                "processed": event.processed
            })
        
        # Sort and limit
        filtered_events.sort(key=lambda x: x["scheduled_time"])
        filtered_events = filtered_events[:filter_request.limit]
        
        return {
            "success": True,
            "filtered_events": filtered_events,
            "count": len(filtered_events),
            "filters_applied": asdict(filter_request),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error filtering events: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


@router.get("/events/today")
@performance_tracked("economic-calendar-api", "get_today_events")
async def get_today_events():
    """Get today's economic events"""
    try:
        logger.info("Getting today's economic events")
        
        current_date = datetime.now(timezone.utc).date()
        start_of_day = datetime.combine(current_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_of_day = datetime.combine(current_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        monitor = await get_economic_calendar_monitor()
        today_events = []
        
        for event in monitor.scheduled_events.values():
            if start_of_day <= event.scheduled_time <= end_of_day:
                today_events.append({
                    "event_id": event.event_id,
                    "event_name": event.event_name,
                    "scheduled_time": event.scheduled_time.isoformat(),
                    "currency": event.currency,
                    "importance": event.importance,
                    "source": event.source,
                    "forecast": event.forecast,
                    "previous": event.previous,
                    "processed": event.processed
                })
        
        # Sort by scheduled time
        today_events.sort(key=lambda x: x["scheduled_time"])
        
        return {
            "success": True,
            "today_events": today_events,
            "count": len(today_events),
            "date": current_date.isoformat(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting today's events: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


# ===== DATA SOURCES ENDPOINTS =====

@router.get("/sources/health")
@performance_tracked("economic-calendar-api", "check_sources_health")
async def check_data_sources_health():
    """Check health of all economic data sources"""
    try:
        logger.info("Checking economic data sources health")
        
        health_status = {
            "mql5": {"status": "unknown", "last_check": None, "error": None},
            "tradingview": {"status": "unknown", "last_check": None, "error": None},
            "pipeline": {"status": "unknown", "last_check": None, "error": None}
        }
        
        # Test MQL5 scraper
        try:
            result = await get_mql5_widget_events()
            events = result.get('events', []) if isinstance(result, dict) else []
            if events:
                health_status["mql5"] = {
                    "status": "healthy",
                    "events_available": len(events),
                    "last_check": datetime.now(timezone.utc).isoformat(),
                    "error": None
                }
            else:
                health_status["mql5"] = {
                    "status": "no_data",
                    "events_available": 0,
                    "last_check": datetime.now(timezone.utc).isoformat(),
                    "error": "No events returned"
                }
        except Exception as e:
            health_status["mql5"] = {
                "status": "error",
                "last_check": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }
        
        # Test TradingView scraper
        try:
            tv_scraper = DataBridgeTradingViewScraper()
            today = date.today()
            result = await tv_scraper.scrape_economic_events(today, today)
            if result and result.get("status") == "completed" and result.get("total_events", 0) > 0:
                health_status["tradingview"] = {
                    "status": "healthy",
                    "events_available": result.get("total_events", 0),
                    "last_check": datetime.now(timezone.utc).isoformat(),
                    "error": None
                }
            else:
                health_status["tradingview"] = {
                    "status": "no_data",
                    "events_available": 0,
                    "last_check": datetime.now(timezone.utc).isoformat(),
                    "error": "No events returned"
                }
        except Exception as e:
            health_status["tradingview"] = {
                "status": "error",
                "last_check": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }
        
        # Test data pipeline
        try:
            pipeline = await get_data_source_pipeline()
            pipeline_stats = pipeline.get_pipeline_stats()
            health_status["pipeline"] = {
                "status": "healthy" if pipeline_stats.get("pipeline_healthy", False) else "degraded",
                "last_check": datetime.now(timezone.utc).isoformat(),
                "stats": pipeline_stats,
                "error": None if pipeline_stats.get("pipeline_healthy", False) else "Pipeline reported unhealthy"
            }
        except Exception as e:
            health_status["pipeline"] = {
                "status": "error",
                "last_check": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }
        
        # Overall health assessment
        healthy_sources = sum(1 for source in health_status.values() if source["status"] == "healthy")
        total_sources = len(health_status)
        overall_health = "healthy" if healthy_sources == total_sources else "degraded" if healthy_sources > 0 else "unhealthy"
        
        return {
            "success": True,
            "overall_health": overall_health,
            "healthy_sources": healthy_sources,
            "total_sources": total_sources,
            "sources": health_status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error checking data sources health: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


@router.post("/sources/test")
@performance_tracked("economic-calendar-api", "test_scraper")
async def test_scraper(test_request: ScraperTestRequest):
    """Test specific scraper functionality"""
    try:
        logger.info(f"Testing {test_request.source} scraper")
        
        if test_request.source == "mql5":
            result = await get_mql5_widget_events()
            events = result.get('events', []) if isinstance(result, dict) else []
            
            return {
                "success": True,
                "source": "mql5",
                "events_retrieved": len(events),
                "sample_events": events[:3] if events else [],
                "scraper_status": result.get('status', 'unknown') if isinstance(result, dict) else 'unknown',
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        elif test_request.source == "tradingview":
            tv_scraper = DataBridgeTradingViewScraper()
            
            # Use provided dates or default to today
            start_date = date.fromisoformat(test_request.start_date) if test_request.start_date else date.today()
            end_date = date.fromisoformat(test_request.end_date) if test_request.end_date else start_date
            
            result = await tv_scraper.scrape_economic_events(start_date, end_date)
            events = result.get("events", []) if result else []
            
            return {
                "success": True,
                "source": "tradingview",
                "date_range": {"start": start_date.isoformat(), "end": end_date.isoformat()},
                "events_retrieved": len(events),
                "sample_events": events[:3],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
    except Exception as e:
        logger.error(f"Error testing {test_request.source} scraper: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "source": test_request.source,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


@router.get("/sources/mql5/events")
@performance_tracked("economic-calendar-api", "get_mql5_events")
async def get_mql5_events():
    """Get current MQL5 economic events"""
    try:
        logger.info("Fetching MQL5 economic events")
        
        result = await get_mql5_widget_events()
        events = result.get('events', []) if isinstance(result, dict) else []
        
        return {
            "success": True,
            "source": "mql5",
            "events": events,
            "count": len(events),
            "scraper_status": result.get('status', 'unknown') if isinstance(result, dict) else 'unknown',
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting MQL5 events: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "source": "mql5",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


@router.get("/sources/tradingview/events")
@performance_tracked("economic-calendar-api", "get_tradingview_events")
async def get_tradingview_events(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get TradingView economic events for date range"""
    try:
        logger.info(f"Fetching TradingView economic events")
        
        # Default to today if no dates provided
        start = date.fromisoformat(start_date) if start_date else date.today()
        end = date.fromisoformat(end_date) if end_date else start
        
        tv_scraper = DataBridgeTradingViewScraper()
        result = await tv_scraper.scrape_economic_events(start, end)
        events = result.get("events", []) if result else []
        
        return {
            "success": True,
            "source": "tradingview",
            "date_range": {"start": start.isoformat(), "end": end.isoformat()},
            "events": events,
            "count": len(events),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting TradingView events: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "source": "tradingview",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


# ===== DATA PIPELINE ENDPOINTS =====

@router.get("/pipeline/status")
@performance_tracked("economic-calendar-api", "get_pipeline_status")
async def get_pipeline_status():
    """Get data source pipeline status"""
    try:
        logger.info("Getting data source pipeline status")
        
        pipeline = await get_data_source_pipeline()
        stats = pipeline.get_pipeline_stats()
        
        return {
            "success": True,
            "pipeline_status": stats,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting pipeline status: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


@router.post("/pipeline/process")
@performance_tracked("economic-calendar-api", "process_events")
async def process_economic_events(
    events: List[Dict[str, Any]] = Body(..., description="Economic events to process"),
    source: str = Body(..., description="Source of the events (mql5 or tradingview)")
):
    """Process economic events through the data pipeline"""
    try:
        logger.info(f"Processing {len(events)} economic events from {source}")
        
        pipeline = await get_data_source_pipeline()
        success = await pipeline.process_economic_events(events, source)
        
        if success:
            return {
                "success": True,
                "message": f"Successfully processed {len(events)} events",
                "source": source,
                "events_processed": len(events),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": "Failed to process events through pipeline",
                    "source": source,
                    "events_count": len(events),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
    except Exception as e:
        logger.error(f"Error processing events: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


# ===== HEALTH AND DIAGNOSTICS =====

@router.get("/health")
@performance_tracked("economic-calendar-api", "health_check")
async def economic_calendar_health():
    """Comprehensive health check for economic calendar system"""
    try:
        health_data = {
            "service": "economic-calendar",
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": {}
        }
        
        # Check monitor health
        try:
            monitor = await get_economic_calendar_monitor()
            stats = monitor.get_monitor_stats()
            health_data["components"]["monitor"] = {
                "status": "healthy",
                "uptime_hours": stats.get("monitor_uptime_hours", 0),
                "events_processed": stats.get("events_processed", 0),
                "events_scheduled": stats.get("total_scheduled", 0)
            }
        except Exception as e:
            health_data["components"]["monitor"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_data["status"] = "degraded"
        
        # Check data sources
        try:
            result = await get_mql5_widget_events()
            events = result.get('events', []) if isinstance(result, dict) else []
            health_data["components"]["mql5"] = {
                "status": "healthy" if events else "no_data",
                "events_available": len(events)
            }
        except Exception as e:
            health_data["components"]["mql5"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_data["status"] = "degraded"
        
        # Check pipeline
        try:
            pipeline = await get_data_source_pipeline()
            pipeline_stats = pipeline.get_pipeline_stats()
            health_data["components"]["pipeline"] = {
                "status": "healthy" if pipeline_stats.get("pipeline_healthy", False) else "degraded",
                "total_processed": pipeline_stats.get("total_processed", 0)
            }
        except Exception as e:
            health_data["components"]["pipeline"] = {
                "status": "unhealthy", 
                "error": str(e)
            }
            health_data["status"] = "degraded"
        
        return health_data
        
    except Exception as e:
        logger.error(f"Error in economic calendar health check: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "service": "economic-calendar",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


# Export router
__all__ = ["router"]