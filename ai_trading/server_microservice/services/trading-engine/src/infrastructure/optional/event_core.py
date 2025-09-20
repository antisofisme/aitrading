"""
Core Event Manager - Event-driven architecture for microservices communication
"""
import json
import uuid
import asyncio
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable, Union
from enum import Enum
from dataclasses import dataclass, asdict

class EventPriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

class EventStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

@dataclass
class Event:
    """Event data structure"""
    id: str
    name: str
    source_service: str
    target_service: Optional[str]
    data: Dict[str, Any]
    priority: EventPriority
    timestamp: datetime
    correlation_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    status: EventStatus = EventStatus.PENDING
    metadata: Optional[Dict[str, Any]] = None

class CoreEventManager:
    """Core event manager for microservices communication"""
    
    def __init__(self, service_name: str, max_events_history: int = 1000):
        self.service_name = service_name
        self.max_events_history = max_events_history
        
        # Thread-safe data structures
        self.event_handlers = {}
        self.event_queue = asyncio.Queue()
        self.published_events = []
        self.received_events = []
        self.failed_events = []
        self.is_running = False
        self.stats = {
            "published": 0,
            "received": 0,
            "failed": 0,
            "retried": 0
        }
        
        # Thread safety locks
        self._handlers_lock = threading.RLock()
        self._events_lock = threading.RLock()
        self._stats_lock = threading.RLock()
    
    async def publish_event(self,
                           event_name: str,
                           data: Dict[str, Any],
                           target_service: Optional[str] = None,
                           priority: EventPriority = EventPriority.NORMAL,
                           correlation_id: Optional[str] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> str:
        """Publish an event to the event system"""
        
        event = Event(
            id=str(uuid.uuid4()),
            name=event_name,
            source_service=self.service_name,
            target_service=target_service,
            data=data,
            priority=priority,
            timestamp=datetime.utcnow(),
            correlation_id=correlation_id,
            metadata=metadata or {}
        )
        
        # Add to published events
        self.published_events.append(event)
        self.stats["published"] += 1
        
        # Automatic cleanup to prevent memory leaks
        self._cleanup_old_events()
        
        # Send to event queue for processing
        await self.event_queue.put(event)
        
        # Log event publication
        await self._log_event_action("published", event)
        
        return event.id
    
    async def subscribe_to_event(self,
                                event_name: str,
                                handler: Callable[[Event], None],
                                source_service: Optional[str] = None):
        """Subscribe to an event type"""
        
        subscription_key = f"{event_name}:{source_service or '*'}"
        
        # Thread-safe handler registration
        with self._handlers_lock:
            if subscription_key not in self.event_handlers:
                self.event_handlers[subscription_key] = []
            self.event_handlers[subscription_key].append(handler)
        
        print(f"🔔 {self.service_name} subscribed to {event_name} from {source_service or 'any service'}")
    
    async def start_event_processing(self):
        """Start the event processing loop"""
        self.is_running = True
        print(f"🚀 Event processing started for {self.service_name}")
        
        while self.is_running:
            try:
                # Get event from queue with timeout
                event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                await self._process_event(event)
                
            except asyncio.TimeoutError:
                # No events in queue, continue
                continue
            except Exception as e:
                print(f"❌ Event processing error: {e}")
    
    async def stop_event_processing(self):
        """Stop the event processing loop"""
        self.is_running = False
        print(f"🛑 Event processing stopped for {self.service_name}")
    
    async def _process_event(self, event: Event):
        """Process a single event"""
        try:
            event.status = EventStatus.PROCESSING
            
            # Check if this event is for this service
            if event.target_service and event.target_service != self.service_name:
                # Forward to target service (in real implementation)
                await self._forward_event(event)
                return
            
            # Find matching handlers
            handlers = self._get_matching_handlers(event)
            
            if not handlers:
                # No handlers for this event
                await self._log_event_action("no_handlers", event)
                return
            
            # Execute all matching handlers
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    print(f"❌ Handler error for event {event.id}: {e}")
                    await self._handle_event_failure(event, e)
                    continue
            
            # Mark as completed
            event.status = EventStatus.COMPLETED
            self.received_events.append(event)
            self.stats["received"] += 1
            
            await self._log_event_action("processed", event)
            
        except Exception as e:
            await self._handle_event_failure(event, e)
    
    def _get_matching_handlers(self, event: Event) -> List[Callable]:
        """Get handlers that match the event"""
        handlers = []
        
        # Check for exact match (event_name:source_service)
        exact_key = f"{event.name}:{event.source_service}"
        if exact_key in self.event_handlers:
            handlers.extend(self.event_handlers[exact_key])
        
        # Check for wildcard match (event_name:*)
        wildcard_key = f"{event.name}:*"
        if wildcard_key in self.event_handlers:
            handlers.extend(self.event_handlers[wildcard_key])
        
        return handlers
    
    async def _handle_event_failure(self, event: Event, error: Exception):
        """Handle event processing failure"""
        event.status = EventStatus.FAILED
        
        # Check if we should retry
        if event.retry_count < event.max_retries:
            event.retry_count += 1
            event.status = EventStatus.RETRYING
            
            # Add back to queue for retry with delay
            await asyncio.sleep(2 ** event.retry_count)  # Exponential backoff
            await self.event_queue.put(event)
            
            self.stats["retried"] += 1
            await self._log_event_action("retried", event)
        else:
            # Max retries reached, add to failed events
            self.failed_events.append(event)
            self.stats["failed"] += 1
            await self._log_event_action("failed", event)
    
    async def _forward_event(self, event: Event):
        """Forward event to target service"""
        # In a real implementation, this would:
        # - Send to message broker (RabbitMQ, Kafka, etc.)
        # - Make HTTP call to target service
        # - Use service mesh communication
        
        print(f"📤 Forwarding event {event.id} to {event.target_service}")
    
    async def _log_event_action(self, action: str, event: Event):
        """Log event action"""
        log_data = {
            "action": action,
            "event_id": event.id,
            "event_name": event.name,
            "source_service": event.source_service,
            "target_service": event.target_service,
            "priority": event.priority.value,
            "retry_count": event.retry_count,
            "service": self.service_name
        }
        
        # In production, this would use the centralized logger
        print(f"📋 Event {action}: {log_data}")
    
    # Business event publishers (common patterns)
    async def publish_user_event(self,
                                action: str,
                                user_id: str,
                                data: Dict[str, Any],
                                correlation_id: Optional[str] = None):
        """Publish user-related event"""
        return await self.publish_event(
            event_name=f"user.{action}",
            data={"user_id": user_id, **data},
            priority=EventPriority.NORMAL,
            correlation_id=correlation_id,
            metadata={"category": "user", "action": action}
        )
    
    async def publish_trading_event(self,
                                  action: str,
                                  symbol: str,
                                  data: Dict[str, Any],
                                  correlation_id: Optional[str] = None):
        """Publish trading-related event"""
        return await self.publish_event(
            event_name=f"trading.{action}",
            data={"symbol": symbol, **data},
            priority=EventPriority.HIGH,  # Trading events are high priority
            correlation_id=correlation_id,
            metadata={"category": "trading", "action": action, "symbol": symbol}
        )
    
    async def publish_system_event(self,
                                 action: str,
                                 data: Dict[str, Any],
                                 priority: EventPriority = EventPriority.NORMAL,
                                 correlation_id: Optional[str] = None):
        """Publish system-related event"""
        return await self.publish_event(
            event_name=f"system.{action}",
            data=data,
            priority=priority,
            correlation_id=correlation_id,
            metadata={"category": "system", "action": action}
        )
    
    async def publish_error_event(self,
                                error: Exception,
                                context: Dict[str, Any],
                                correlation_id: Optional[str] = None):
        """Publish error event for monitoring"""
        return await self.publish_event(
            event_name="system.error",
            data={
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context
            },
            priority=EventPriority.CRITICAL,
            correlation_id=correlation_id,
            metadata={"category": "error", "severity": "high"}
        )
    
    # Event querying and management
    def get_published_events(self, 
                           event_name: Optional[str] = None,
                           since: Optional[datetime] = None) -> List[Event]:
        """Get published events with optional filtering"""
        events = self.published_events
        
        if event_name:
            events = [e for e in events if e.name == event_name]
        
        if since:
            events = [e for e in events if e.timestamp >= since]
        
        return events
    
    def get_failed_events(self) -> List[Event]:
        """Get failed events for debugging"""
        return self.failed_events.copy()
    
    def get_event_stats(self) -> Dict[str, Any]:
        """Get event statistics"""
        return {
            **self.stats,
            "success_rate": (self.stats["received"] / max(self.stats["published"], 1)) * 100,
            "failure_rate": (self.stats["failed"] / max(self.stats["published"], 1)) * 100,
            "active_subscriptions": len(self.event_handlers),
            "service": self.service_name,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def replay_failed_events(self):
        """Replay failed events"""
        failed_events = self.failed_events.copy()
        self.failed_events.clear()
        
        for event in failed_events:
            event.retry_count = 0
            event.status = EventStatus.PENDING
            await self.event_queue.put(event)
        
        print(f"🔄 Replaying {len(failed_events)} failed events")
    
    def _cleanup_old_events(self):
        """Automatic cleanup of old events to prevent memory leaks"""
        with self._events_lock:
            # Clean published events
            if len(self.published_events) > self.max_events_history:
                self.published_events.sort(key=lambda e: e.timestamp, reverse=True)
                self.published_events = self.published_events[:self.max_events_history]
            
            # Clean received events
            if len(self.received_events) > self.max_events_history:
                self.received_events.sort(key=lambda e: e.timestamp, reverse=True)
                self.received_events = self.received_events[:self.max_events_history]
            
            # Clean failed events (keep fewer for investigation)
            max_failed = self.max_events_history // 2
            if len(self.failed_events) > max_failed:
                self.failed_events.sort(key=lambda e: e.timestamp, reverse=True)
                self.failed_events = self.failed_events[:max_failed]
    
    def clear_event_history(self, older_than: Optional[datetime] = None):
        """Clear event history"""
        if older_than:
            self.published_events = [e for e in self.published_events if e.timestamp > older_than]
            self.received_events = [e for e in self.received_events if e.timestamp > older_than]
            self.failed_events = [e for e in self.failed_events if e.timestamp > older_than]
        else:
            self.published_events.clear()
            self.received_events.clear()
            self.failed_events.clear()
    
    # Service-specific event patterns
    async def setup_service_events(self):
        """Setup service-specific event patterns"""
        if self.service_name == "api-gateway":
            await self._setup_api_gateway_events()
        elif self.service_name == "trading-engine":
            await self._setup_trading_engine_events()
        elif self.service_name == "database-service":
            await self._setup_database_service_events()
    
    async def _setup_api_gateway_events(self):
        """Setup API Gateway specific events"""
        # Subscribe to authentication events
        await self.subscribe_to_event("user.login", self._handle_user_login)
        await self.subscribe_to_event("user.logout", self._handle_user_logout)
        
        # Subscribe to rate limiting events
        await self.subscribe_to_event("system.rate_limit_exceeded", self._handle_rate_limit)
    
    async def _setup_trading_engine_events(self):
        """Setup Trading Engine specific events"""
        # Subscribe to market data events
        await self.subscribe_to_event("market.tick", self._handle_market_tick)
        await self.subscribe_to_event("market.signal", self._handle_trading_signal)
        
        # Subscribe to position events
        await self.subscribe_to_event("trading.position_opened", self._handle_position_opened)
        await self.subscribe_to_event("trading.position_closed", self._handle_position_closed)
    
    async def _setup_database_service_events(self):
        """Setup Database Service specific events"""
        # Subscribe to data change events
        await self.subscribe_to_event("data.created", self._handle_data_created)
        await self.subscribe_to_event("data.updated", self._handle_data_updated)
        await self.subscribe_to_event("data.deleted", self._handle_data_deleted)
    
    # Default event handlers (to be overridden by services)
    async def _handle_user_login(self, event: Event):
        """Handle user login event"""
        pass
    
    async def _handle_user_logout(self, event: Event):
        """Handle user logout event"""
        pass
    
    async def _handle_rate_limit(self, event: Event):
        """Handle rate limit event"""
        pass
    
    async def _handle_market_tick(self, event: Event):
        """Handle market tick event"""
        pass
    
    async def _handle_trading_signal(self, event: Event):
        """Handle trading signal event"""
        pass
    
    async def _handle_position_opened(self, event: Event):
        """Handle position opened event"""
        pass
    
    async def _handle_position_closed(self, event: Event):
        """Handle position closed event"""
        pass
    
    async def _handle_data_created(self, event: Event):
        """Handle data created event"""
        pass
    
    async def _handle_data_updated(self, event: Event):
        """Handle data updated event"""
        pass
    
    async def _handle_data_deleted(self, event: Event):
        """Handle data deleted event"""
        pass