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
Real-Time Economic Calendar Monitor - Smart Event Processing
Monitors economic events in real-time and processes them when they occur
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
import time
from collections import defaultdict

# Infrastructure integration
try:
    from shared.infrastructure.core.performance_core import performance_tracked
    from shared.infrastructure.core.config_core import CoreConfig
except ImportError:
    pass

# Business components
from .data_source_pipeline import get_data_source_pipeline
from ..data_sources.mql5_scraper import MQL5EconomicEvent
from ..data_sources.tradingview_scraper import DataBridgeEconomicEvent


@dataclass
class ScheduledEvent:
    """Scheduled economic event for monitoring"""
    event_id: str
    event_name: str
    scheduled_time: datetime
    currency: str
    importance: str
    source: str
    forecast: Optional[str] = None
    previous: Optional[str] = None
    processed: bool = False
    
    def is_due(self, current_time: datetime, tolerance_minutes: int = 5) -> bool:
        """Check if event is due for processing"""
        if self.processed:
            return False
            
        # Event is due if current time is past scheduled time + tolerance
        due_time = self.scheduled_time + timedelta(minutes=tolerance_minutes)
        return current_time >= due_time
    
    def time_until_event(self, current_time: datetime) -> timedelta:
        """Get time remaining until event"""
        return self.scheduled_time - current_time


class EconomicCalendarMonitor:
    """Real-time economic calendar monitoring and processing"""
    
    def __init__(self):
        self.logger = get_logger("data-bridge", "economic-monitor")
        self.config = CoreConfig("data-bridge")
        
        # Event scheduling
        self.scheduled_events: Dict[str, ScheduledEvent] = {}
        self.processed_events: Set[str] = set()
        
        # Configuration
        self.check_interval_seconds = self.config.get('economic_calendar.check_interval_seconds', 30)
        self.event_tolerance_minutes = self.config.get('economic_calendar.event_tolerance_minutes', 5)
        self.refresh_interval_hours = self.config.get('economic_calendar.refresh_interval_hours', 4)
        
        # Monitoring stats
        self.stats = {
            "events_scheduled": 0,
            "events_processed": 0,
            "events_missed": 0,
            "last_refresh": None,
            "last_check": None,
            "monitor_uptime_start": datetime.now(timezone.utc)
        }
        
        # Next refresh time
        self.next_refresh = datetime.now(timezone.utc) + timedelta(hours=self.refresh_interval_hours)
        
        self.logger.info(f"Economic Calendar Monitor initialized - check every {self.check_interval_seconds}s, tolerance: {self.event_tolerance_minutes}min")
    
    async def start_monitoring(self):
        """Start real-time economic calendar monitoring"""
        self.logger.info("🕐 Starting Real-Time Economic Calendar Monitor")
        
        # Initial load of today's events
        await self._refresh_calendar()
        
        while True:
            try:
                current_time = datetime.now(timezone.utc)
                self.stats["last_check"] = current_time
                
                # Check if we need to refresh calendar
                if current_time >= self.next_refresh:
                    await self._refresh_calendar()
                    self.next_refresh = current_time + timedelta(hours=self.refresh_interval_hours)
                
                # Process due events
                await self._process_due_events(current_time)
                
                # Clean up old processed events
                await self._cleanup_old_events(current_time)
                
                # Log monitoring status periodically
                if int(current_time.timestamp()) % 300 == 0:  # Every 5 minutes
                    await self._log_monitor_status(current_time)
                
                await asyncio.sleep(self.check_interval_seconds)
                
            except Exception as e:
                self.logger.error(f"❌ Error in economic calendar monitoring: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def _refresh_calendar(self):
        """Refresh economic calendar with latest events"""
        try:
            self.logger.info("📅 Refreshing economic calendar...")
            start_time = time.time()
            
            # Get events from both sources
            mql5_events = await self._fetch_mql5_events()
            tradingview_events = await self._fetch_tradingview_events()
            
            # Schedule new events
            new_events_count = 0
            
            # Process MQL5 events
            for event in mql5_events:
                if await self._schedule_event_from_mql5(event):
                    new_events_count += 1
            
            # Process TradingView events  
            for event in tradingview_events:
                if await self._schedule_event_from_tradingview(event):
                    new_events_count += 1
            
            refresh_duration = (time.time() - start_time) * 1000
            self.stats["last_refresh"] = datetime.now(timezone.utc)
            
            self.logger.info(f"✅ Calendar refreshed: {new_events_count} new events scheduled, "
                           f"{len(self.scheduled_events)} total events, "
                           f"duration: {refresh_duration:.2f}ms")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to refresh calendar: {e}")
    
    async def _fetch_mql5_events(self) -> List[MQL5EconomicEvent]:
        """Fetch events from MQL5"""
        try:
            from ..data_sources.mql5_scraper import get_mql5_widget_events
            events = await get_mql5_widget_events()
            self.logger.debug(f"📡 Fetched {len(events) if events else 0} MQL5 events")
            return events or []
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to fetch MQL5 events: {e}")
            return []
    
    async def _fetch_tradingview_events(self) -> List[DataBridgeEconomicEvent]:
        """Fetch events from TradingView"""
        try:
            from ..data_sources.tradingview_scraper import DataBridgeTradingViewScraper
            from datetime import date
            
            tv_scraper = DataBridgeTradingViewScraper()
            today = date.today()
            tomorrow = today + timedelta(days=1)
            
            events = await tv_scraper.scrape_economic_events(today, tomorrow)
            self.logger.debug(f"📡 Fetched {len(events) if events else 0} TradingView events")
            return events or []
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to fetch TradingView events: {e}")
            return []
    
    async def _schedule_event_from_mql5(self, event: MQL5EconomicEvent) -> bool:
        """Schedule MQL5 event for monitoring"""
        try:
            if not event.datetime:
                return False
                
            event_id = f"mql5_{event.name}_{event.datetime.strftime('%Y%m%d_%H%M')}"
            
            # Skip if already scheduled
            if event_id in self.scheduled_events:
                return False
            
            scheduled_event = ScheduledEvent(
                event_id=event_id,
                event_name=event.name or "Unknown Event",
                scheduled_time=event.datetime,
                currency=event.currency or "USD",
                importance=event.importance or "medium",
                source="mql5",
                forecast=str(event.forecast) if event.forecast is not None else None,
                previous=str(event.previous) if event.previous is not None else None
            )
            
            self.scheduled_events[event_id] = scheduled_event
            self.stats["events_scheduled"] += 1
            
            time_until = scheduled_event.time_until_event(datetime.now(timezone.utc))
            if time_until.total_seconds() > 0:
                self.logger.debug(f"📅 Scheduled MQL5 event: {event.name} at {event.datetime} "
                                f"(in {time_until})")
            
            return True
            
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to schedule MQL5 event: {e}")
            return False
    
    async def _schedule_event_from_tradingview(self, event: DataBridgeEconomicEvent) -> bool:
        """Schedule TradingView event for monitoring"""
        try:
            if not event.datetime:
                return False
                
            event_id = f"tradingview_{event.event_name}_{event.datetime.strftime('%Y%m%d_%H%M')}"
            
            # Skip if already scheduled
            if event_id in self.scheduled_events:
                return False
            
            scheduled_event = ScheduledEvent(
                event_id=event_id,
                event_name=event.event_name or "Unknown Event",
                scheduled_time=event.datetime,
                currency=event.currency or "USD", 
                importance=event.impact or "medium",
                source="tradingview",
                forecast=event.forecast,
                previous=event.previous
            )
            
            self.scheduled_events[event_id] = scheduled_event
            self.stats["events_scheduled"] += 1
            
            time_until = scheduled_event.time_until_event(datetime.now(timezone.utc))
            if time_until.total_seconds() > 0:
                self.logger.debug(f"📅 Scheduled TradingView event: {event.event_name} at {event.datetime} "
                                f"(in {time_until})")
            
            return True
            
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to schedule TradingView event: {e}")
            return False
    
    async def _process_due_events(self, current_time: datetime):
        """Process events that are due"""
        due_events = [
            event for event in self.scheduled_events.values()
            if event.is_due(current_time, self.event_tolerance_minutes)
        ]
        
        if not due_events:
            return
        
        self.logger.info(f"⏰ Processing {len(due_events)} due economic events")
        
        for event in due_events:
            try:
                await self._process_individual_event(event, current_time)
                event.processed = True
                self.processed_events.add(event.event_id)
                self.stats["events_processed"] += 1
                
            except Exception as e:
                self.logger.error(f"❌ Failed to process event {event.event_name}: {e}")
                self.stats["events_missed"] += 1
    
    @performance_tracked("unknown-service", "process_economic_event")
    async def _process_individual_event(self, event: ScheduledEvent, current_time: datetime):
        """Process individual economic event"""
        try:
            self.logger.info(f"🔄 Processing economic event: {event.event_name} "
                           f"({event.currency}, {event.importance})")
            
            # Get updated data for the event (check for actual values)
            updated_event_data = await self._get_updated_event_data(event)
            
            # Store to database through pipeline
            pipeline = await get_data_source_pipeline()
            
            # Create event data for storage
            event_data = {
                "timestamp": current_time.isoformat(),
                "event_name": event.event_name,
                "currency": event.currency,
                "impact": event.importance,
                "forecast": event.forecast,
                "previous": event.previous,
                "actual": updated_event_data.get("actual"),
                "source": event.source,
                "event_id": event.event_id,
                "description": event.event_name,
                "scheduled_time": event.scheduled_time.isoformat(),
                "processed_time": current_time.isoformat(),
                "processing_delay_minutes": (current_time - event.scheduled_time).total_seconds() / 60
            }
            
            # Store event
            success = await pipeline.process_economic_events([event_data], event.source)
            
            if success:
                # Calculate impact metrics
                impact_metrics = await self._calculate_event_impact(event_data)
                
                self.logger.info(f"✅ Economic event processed successfully: {event.event_name}")
                self.logger.info(f"📊 Impact metrics: {impact_metrics}")
                
                # Trigger further analysis if high impact
                if impact_metrics.get("surprise_factor", 0) > 0.5:
                    await self._trigger_high_impact_analysis(event_data, impact_metrics)
                
            else:
                self.logger.warning(f"⚠️ Failed to store economic event: {event.event_name}")
                
        except Exception as e:
            self.logger.error(f"❌ Error processing economic event {event.event_name}: {e}")
            raise
    
    async def _get_updated_event_data(self, event: ScheduledEvent) -> Dict[str, Any]:
        """Get updated event data (including actual values)"""
        try:
            # This would fetch the latest data to get actual values
            # For now, return placeholder
            return {
                "actual": None,  # Would be fetched from real-time source
                "revision": None,
                "release_time": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to get updated data for {event.event_name}: {e}")
            return {}
    
    async def _calculate_event_impact(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate impact metrics for the event"""
        try:
            metrics = {
                "surprise_factor": 0.0,
                "volatility_expected": event_data.get("impact", "medium"),
                "processing_delay": event_data.get("processing_delay_minutes", 0),
                "market_relevance": 1.0 if event_data.get("currency") in ["USD", "EUR", "GBP", "JPY"] else 0.5
            }
            
            # Calculate surprise factor if we have forecast and actual
            if event_data.get("forecast") and event_data.get("actual"):
                try:
                    forecast = float(event_data["forecast"])
                    actual = float(event_data["actual"])
                    if forecast != 0:
                        metrics["surprise_factor"] = abs(actual - forecast) / abs(forecast)
                except (ValueError, ZeroDivisionError):
                    pass
            
            return metrics
            
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to calculate impact metrics: {e}")
            return {"surprise_factor": 0.0}
    
    async def _trigger_high_impact_analysis(self, event_data: Dict[str, Any], impact_metrics: Dict[str, Any]):
        """Trigger analysis for high-impact events"""
        try:
            self.logger.info(f"🚨 HIGH IMPACT EVENT DETECTED: {event_data['event_name']} "
                           f"(surprise factor: {impact_metrics['surprise_factor']:.2f})")
            
            # This would trigger:
            # 1. Market volatility analysis
            # 2. Currency pair impact assessment  
            # 3. Trading strategy alerts
            # 4. Risk management updates
            
            # For now, just log the high-impact event
            high_impact_data = {
                "event": event_data,
                "metrics": impact_metrics,
                "alert_level": "HIGH",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            self.logger.info(f"📈 High-impact analysis triggered: {high_impact_data}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to trigger high-impact analysis: {e}")
    
    async def _cleanup_old_events(self, current_time: datetime):
        """Clean up old processed events"""
        try:
            # Remove events older than 24 hours
            cutoff_time = current_time - timedelta(hours=24)
            
            old_events = [
                event_id for event_id, event in self.scheduled_events.items()
                if event.processed and event.scheduled_time < cutoff_time
            ]
            
            for event_id in old_events:
                del self.scheduled_events[event_id]
                if event_id in self.processed_events:
                    self.processed_events.remove(event_id)
            
            if old_events:
                self.logger.debug(f"🧹 Cleaned up {len(old_events)} old processed events")
                
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to cleanup old events: {e}")
    
    async def _log_monitor_status(self, current_time: datetime):
        """Log monitoring status"""
        try:
            uptime = current_time - self.stats["monitor_uptime_start"]
            
            # Count events by status
            total_scheduled = len(self.scheduled_events)
            pending_events = [e for e in self.scheduled_events.values() if not e.processed]
            upcoming_events = [e for e in pending_events if e.scheduled_time > current_time]
            overdue_events = [e for e in pending_events if e.scheduled_time <= current_time]
            
            status_info = {
                "monitor_uptime_hours": uptime.total_seconds() / 3600,
                "total_scheduled": total_scheduled,
                "pending_events": len(pending_events),
                "upcoming_events": len(upcoming_events), 
                "overdue_events": len(overdue_events),
                "events_processed": self.stats["events_processed"],
                "events_missed": self.stats["events_missed"],
                "last_refresh": self.stats["last_refresh"].isoformat() if self.stats["last_refresh"] else None,
                "next_refresh": self.next_refresh.isoformat()
            }
            
            self.logger.info(f"📊 Economic Calendar Monitor Status: {status_info}")
            
            # List next few upcoming events
            upcoming_sorted = sorted(upcoming_events, key=lambda e: e.scheduled_time)[:5]
            if upcoming_sorted:
                self.logger.info("⏰ Next upcoming events:")
                for event in upcoming_sorted:
                    time_until = event.time_until_event(current_time)
                    self.logger.info(f"   • {event.event_name} ({event.currency}, {event.importance}) "
                                   f"in {time_until}")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to log monitor status: {e}")
    
    def get_monitor_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics"""
        current_time = datetime.now(timezone.utc)
        uptime = current_time - self.stats["monitor_uptime_start"]
        
        return {
            **self.stats,
            "monitor_uptime_hours": uptime.total_seconds() / 3600,
            "total_scheduled": len(self.scheduled_events),
            "pending_events": len([e for e in self.scheduled_events.values() if not e.processed]),
            "next_refresh": self.next_refresh.isoformat(),
            "current_time": current_time.isoformat()
        }


# Global monitor instance
_economic_calendar_monitor: Optional[EconomicCalendarMonitor] = None


async def get_economic_calendar_monitor() -> EconomicCalendarMonitor:
    """Get global economic calendar monitor instance"""
    global _economic_calendar_monitor
    if _economic_calendar_monitor is None:
        _economic_calendar_monitor = EconomicCalendarMonitor()
    return _economic_calendar_monitor


async def start_economic_calendar_monitoring():
    """Start economic calendar monitoring as background task"""
    monitor = await get_economic_calendar_monitor()
    await monitor.start_monitoring()


# Export main classes and functions
__all__ = [
    "EconomicCalendarMonitor",
    "ScheduledEvent",
    "get_economic_calendar_monitor",
    "start_economic_calendar_monitoring"
]