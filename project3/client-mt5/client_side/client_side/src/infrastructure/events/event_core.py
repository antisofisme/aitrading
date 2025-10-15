"""
event_core.py - Event Management System

🎯 PURPOSE:
Business: Asynchronous event handling for trading operations and system notifications
Technical: Publisher-subscriber pattern with event queuing and async processing
Domain: Event Management/Async Processing/System Integration

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:27.841Z
Session: client-side-ai-brain-full-compliance
Confidence: 89%
Complexity: medium

🧩 PATTERNS USED:
- AI_BRAIN_EVENT_SYSTEM: Centralized event management with async processing
- PUBLISHER_SUBSCRIBER: Decoupled event publishing and subscription

📦 DEPENDENCIES:
Internal: logger_manager, error_manager
External: asyncio, threading, queue, typing, dataclasses

💡 AI DECISION REASONING:
Event-driven architecture enables loose coupling between components while supporting real-time trading notifications and system events.

🚀 USAGE:
event_core.publish("trade_executed", {"symbol": "EURUSD", "price": 1.1234})

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

import asyncio
import threading
import weakref
import uuid
import json
import time
from typing import Dict, Any, Optional, List, Union, Callable, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
from pathlib import Path
import inspect

class EventPriority(Enum):
    """Event priority levels"""
    CRITICAL = 1    # System-critical events (errors, failures)
    HIGH = 2        # Important business events (trades, connections)
    MEDIUM = 3      # Standard application events (updates, notifications)
    LOW = 4         # Background events (logging, cleanup)

class EventType(Enum):
    """AI Brain event types for MT5 Trading Client"""
    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"
    SYSTEM_HEALTH_CHECK = "system.health_check"
    
    # MT5 events
    MT5_CONNECTED = "mt5.connected"
    MT5_DISCONNECTED = "mt5.disconnected"
    MT5_LOGIN_SUCCESS = "mt5.login_success"
    MT5_LOGIN_FAILED = "mt5.login_failed"
    MT5_TICK_RECEIVED = "mt5.tick_received"
    MT5_ACCOUNT_INFO = "mt5.account_info"
    
    # WebSocket events
    WS_CONNECTED = "websocket.connected"
    WS_DISCONNECTED = "websocket.disconnected"
    WS_MESSAGE_RECEIVED = "websocket.message_received"
    WS_MESSAGE_SENT = "websocket.message_sent"
    WS_ERROR = "websocket.error"
    
    # Redpanda/Kafka events
    KAFKA_CONNECTED = "kafka.connected"
    KAFKA_DISCONNECTED = "kafka.disconnected"
    KAFKA_MESSAGE_SENT = "kafka.message_sent"
    KAFKA_MESSAGE_RECEIVED = "kafka.message_received"
    KAFKA_ERROR = "kafka.error"
    
    # Configuration events
    CONFIG_LOADED = "config.loaded"
    CONFIG_UPDATED = "config.updated"
    CONFIG_ERROR = "config.error"
    
    # Performance events
    PERFORMANCE_ALERT = "performance.alert"
    CACHE_HIT = "cache.hit"
    CACHE_MISS = "cache.miss"
    
    # Business events
    TRADE_SIGNAL = "trade.signal"
    TRADE_EXECUTED = "trade.executed"
    PORTFOLIO_UPDATE = "portfolio.update"
    MARKET_DATA_UPDATE = "market_data.update"
    
    # Custom events
    CUSTOM = "custom"

@dataclass
class Event:
    """AI Brain Event with comprehensive metadata"""
    id: str
    type: EventType
    source: str
    timestamp: datetime
    priority: EventPriority
    data: Dict[str, Any]
    metadata: Dict[str, Any] = None
    correlation_id: Optional[str] = None
    parent_event_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.correlation_id is None:
            self.correlation_id = str(uuid.uuid4())
    
    @property
    def is_expired(self) -> bool:
        """Check if event is expired"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    @property
    def can_retry(self) -> bool:
        """Check if event can be retried"""
        return self.retry_count < self.max_retries
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            'id': self.id,
            'type': self.type.value,
            'source': self.source,
            'timestamp': self.timestamp.isoformat(),
            'priority': self.priority.value,
            'data': self.data,
            'metadata': self.metadata,
            'correlation_id': self.correlation_id,
            'parent_event_id': self.parent_event_id,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries
        }

@dataclass
class EventHandler:
    """Event handler registration"""
    id: str
    callback: Callable[[Event], Any]
    event_types: Set[EventType]
    priority_filter: Set[EventPriority] = None
    source_filter: Set[str] = None
    async_handler: bool = False
    enabled: bool = True
    
    def __post_init__(self):
        if self.priority_filter is None:
            self.priority_filter = set(EventPriority)
        if self.source_filter is None:
            self.source_filter = set()
    
    def matches_event(self, event: Event) -> bool:
        """Check if this handler matches the event"""
        if not self.enabled:
            return False
        
        # Check event type
        if event.type not in self.event_types and EventType.CUSTOM not in self.event_types:
            return False
        
        # Check priority filter
        if event.priority not in self.priority_filter:
            return False
        
        # Check source filter
        if self.source_filter and event.source not in self.source_filter:
            return False
        
        return True

@dataclass
class EventStats:
    """Event system statistics"""
    events_published: int = 0
    events_processed: int = 0
    events_failed: int = 0
    events_retried: int = 0
    active_handlers: int = 0
    average_processing_time: float = 0.0
    events_by_type: Dict[str, int] = None
    events_by_priority: Dict[str, int] = None
    
    def __post_init__(self):
        if self.events_by_type is None:
            self.events_by_type = defaultdict(int)
        if self.events_by_priority is None:
            self.events_by_priority = defaultdict(int)

class EventCore:
    """
    AI Brain Event Core System
    Intelligent event-driven coordination for microservices
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        # Event storage and processing
        self._event_queue: asyncio.Queue = None
        self._priority_queues: Dict[EventPriority, asyncio.Queue] = {}
        self._event_history: deque = deque(maxlen=10000)
        self._failed_events: deque = deque(maxlen=1000)
        
        # Handler management
        self._handlers: Dict[str, EventHandler] = {}
        self._event_type_handlers: Dict[EventType, Set[str]] = defaultdict(set)
        
        # AI Brain features
        self._event_patterns: Dict[str, List[datetime]] = defaultdict(list)
        self._correlation_chains: Dict[str, List[str]] = defaultdict(list)
        self._performance_metrics: Dict[str, List[float]] = defaultdict(list)
        
        # Configuration
        self._max_queue_size = 10000
        self._max_concurrent_handlers = 50
        self._enable_persistence = True
        self._enable_pattern_learning = True
        
        # Statistics
        self._stats = EventStats()
        self._processing_times = deque(maxlen=1000)
        
        # Control
        self._running = False
        self._worker_tasks: List[asyncio.Task] = []
        self._lock = threading.RLock()
        
        # Persistence
        self._persistence_path = Path("logs/event_core_state.json")
        
        # Initialize system
        self._initialize_event_core()
    
    @classmethod
    def get_instance(cls) -> 'EventCore':
        """Singleton pattern with thread safety"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def _initialize_event_core(self):
        """Initialize the event core system"""
        # Initialize priority queues
        for priority in EventPriority:
            self._priority_queues[priority] = None  # Will be created when event loop is available
        
        # Load persistence if enabled
        if self._enable_persistence:
            self._load_persistence()
        
        print("🔄 AI Brain Event Core initialized")
    
    async def start(self):
        """Start the event core system"""
        if self._running:
            return
        
        self._running = True
        
        # Initialize queues with event loop
        if self._event_queue is None:
            self._event_queue = asyncio.Queue(maxsize=self._max_queue_size)
        
        for priority in EventPriority:
            if self._priority_queues[priority] is None:
                self._priority_queues[priority] = asyncio.Queue(maxsize=self._max_queue_size // len(EventPriority))
        
        # Start worker tasks
        self._worker_tasks = [
            asyncio.create_task(self._event_processor()),
            asyncio.create_task(self._priority_processor()),
            asyncio.create_task(self._pattern_analyzer()),
            asyncio.create_task(self._health_monitor())
        ]
        
        # Publish startup event
        await self.publish(Event(
            id=str(uuid.uuid4()),
            type=EventType.SYSTEM_STARTUP,
            source="event_core",
            timestamp=datetime.now(),
            priority=EventPriority.HIGH,
            data={"component": "event_core", "status": "started"}
        ))
        
        print("🚀 Event Core started with AI Brain coordination")
    
    async def stop(self):
        """Stop the event core system"""
        if not self._running:
            return
        
        self._running = False
        
        # Publish shutdown event
        await self.publish(Event(
            id=str(uuid.uuid4()),
            type=EventType.SYSTEM_SHUTDOWN,
            source="event_core", 
            timestamp=datetime.now(),
            priority=EventPriority.HIGH,
            data={"component": "event_core", "status": "stopping"}
        ))
        
        # Cancel worker tasks
        for task in self._worker_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        
        # Save state if persistence enabled
        if self._enable_persistence:
            self._save_persistence()
        
        print("🛑 Event Core stopped")
    
    # ==================== EVENT PUBLISHING ====================
    
    async def publish(self, event: Event) -> bool:
        """Publish event with AI Brain routing"""
        try:
            if not self._running:
                return False
            
            # Validate event
            if event.is_expired:
                return False
            
            # Update statistics
            self._stats.events_published += 1
            self._stats.events_by_type[event.type.value] += 1
            self._stats.events_by_priority[event.priority.name] += 1
            
            # Add to history
            self._event_history.append(event)
            
            # Record pattern
            if self._enable_pattern_learning:
                self._record_event_pattern(event)
            
            # Route to appropriate queue based on priority
            priority_queue = self._priority_queues[event.priority]
            
            try:
                priority_queue.put_nowait(event)
            except asyncio.QueueFull:
                # If priority queue is full, try main queue
                try:
                    self._event_queue.put_nowait(event)
                except asyncio.QueueFull:
                    print(f"⚠️ Event queue full, dropping event: {event.id}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to publish event {event.id}: {e}")
            return False
    
    def publish_sync(self, event: Event) -> bool:
        """Synchronous event publishing"""
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                # Create task for async publishing
                task = asyncio.create_task(self.publish(event))
                return True
        except RuntimeError:
            # No running event loop, create new one
            try:
                return asyncio.run(self.publish(event))
            except Exception as e:
                print(f"❌ Event publishing failed: {e}")
                return False
    
    # ==================== EVENT HANDLER REGISTRATION ====================
    
    def subscribe(self, 
                 event_types: Union[EventType, List[EventType]], 
                 callback: Callable[[Event], Any],
                 priority_filter: Optional[List[EventPriority]] = None,
                 source_filter: Optional[List[str]] = None,
                 handler_id: Optional[str] = None) -> str:
        """Subscribe to events with filters"""
        
        # Normalize event types
        if isinstance(event_types, EventType):
            event_types = [event_types]
        event_types_set = set(event_types)
        
        # Generate handler ID
        if handler_id is None:
            handler_id = f"handler_{uuid.uuid4().hex[:8]}"
        
        # Create handler
        handler = EventHandler(
            id=handler_id,
            callback=callback,
            event_types=event_types_set,
            priority_filter=set(priority_filter) if priority_filter else None,
            source_filter=set(source_filter) if source_filter else None,
            async_handler=inspect.iscoroutinefunction(callback)
        )
        
        # Register handler
        with self._lock:
            self._handlers[handler_id] = handler
            
            # Update type-based lookup
            for event_type in event_types_set:
                self._event_type_handlers[event_type].add(handler_id)
            
            self._stats.active_handlers += 1
        
        print(f"📋 Handler {handler_id} subscribed to {len(event_types)} event types")
        return handler_id
    
    def unsubscribe(self, handler_id: str) -> bool:
        """Unsubscribe event handler"""
        with self._lock:
            if handler_id not in self._handlers:
                return False
            
            handler = self._handlers[handler_id]
            
            # Remove from type-based lookup
            for event_type in handler.event_types:
                self._event_type_handlers[event_type].discard(handler_id)
            
            # Remove handler
            del self._handlers[handler_id]
            self._stats.active_handlers = max(0, self._stats.active_handlers - 1)
        
        print(f"🗑️ Handler {handler_id} unsubscribed")
        return True
    
    def enable_handler(self, handler_id: str) -> bool:
        """Enable event handler"""
        with self._lock:
            if handler_id in self._handlers:
                self._handlers[handler_id].enabled = True
                return True
            return False
    
    def disable_handler(self, handler_id: str) -> bool:
        """Disable event handler"""
        with self._lock:
            if handler_id in self._handlers:
                self._handlers[handler_id].enabled = False
                return True
            return False
    
    # ==================== EVENT PROCESSING ====================
    
    async def _event_processor(self):
        """Main event processor worker"""
        while self._running:
            try:
                # Get event from main queue
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                await self._process_event(event)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"❌ Event processor error: {e}")
    
    async def _priority_processor(self):
        """Priority-based event processor"""
        while self._running:
            try:
                # Process events from priority queues (highest priority first)
                for priority in sorted(EventPriority, key=lambda x: x.value):
                    queue = self._priority_queues[priority]
                    
                    try:
                        # Try to get event without blocking
                        event = queue.get_nowait()
                        await self._process_event(event)
                        
                    except asyncio.QueueEmpty:
                        continue
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.01)
                
            except Exception as e:
                print(f"❌ Priority processor error: {e}")
    
    async def _process_event(self, event: Event):
        """Process individual event with AI Brain intelligence"""
        start_time = time.time()
        
        try:
            # Check if event is expired
            if event.is_expired:
                return
            
            # Find matching handlers
            matching_handlers = self._find_matching_handlers(event)
            
            if not matching_handlers:
                return
            
            # Process handlers concurrently (up to max concurrent)
            semaphore = asyncio.Semaphore(self._max_concurrent_handlers)
            
            async def process_handler(handler: EventHandler):
                async with semaphore:
                    await self._execute_handler(handler, event)
            
            # Execute all matching handlers
            tasks = [process_handler(handler) for handler in matching_handlers]
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Update statistics
            self._stats.events_processed += 1
            
            # Record performance
            processing_time = time.time() - start_time
            self._processing_times.append(processing_time)
            self._update_average_processing_time()
            
            # Record correlation if applicable
            if event.correlation_id:
                self._correlation_chains[event.correlation_id].append(event.id)
            
        except Exception as e:
            print(f"❌ Failed to process event {event.id}: {e}")
            self._stats.events_failed += 1
            self._failed_events.append(event)
            
            # Retry if possible
            if event.can_retry:
                event.retry_count += 1
                self._stats.events_retried += 1
                await asyncio.sleep(2 ** event.retry_count)  # Exponential backoff
                await self.publish(event)
    
    def _find_matching_handlers(self, event: Event) -> List[EventHandler]:
        """Find handlers that match the event"""
        matching_handlers = []
        
        with self._lock:
            # Get handlers for this event type
            handler_ids = self._event_type_handlers.get(event.type, set())
            
            # Also check custom event handlers
            handler_ids.update(self._event_type_handlers.get(EventType.CUSTOM, set()))
            
            for handler_id in handler_ids:
                handler = self._handlers.get(handler_id)
                if handler and handler.matches_event(event):
                    matching_handlers.append(handler)
        
        return matching_handlers
    
    async def _execute_handler(self, handler: EventHandler, event: Event):
        """Execute individual event handler"""
        try:
            if handler.async_handler:
                await handler.callback(event)
            else:
                handler.callback(event)
                
        except Exception as e:
            print(f"❌ Handler {handler.id} failed for event {event.id}: {e}")
            raise
    
    # ==================== AI BRAIN PATTERN ANALYSIS ====================
    
    def _record_event_pattern(self, event: Event):
        """Record event pattern for AI Brain learning"""
        pattern_key = f"{event.type.value}:{event.source}"
        self._event_patterns[pattern_key].append(event.timestamp)
        
        # Keep only last 1000 occurrences per pattern
        if len(self._event_patterns[pattern_key]) > 1000:
            self._event_patterns[pattern_key] = self._event_patterns[pattern_key][-1000:]
    
    async def _pattern_analyzer(self):
        """Analyze event patterns for insights"""
        while self._running:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                # Analyze patterns
                insights = self._analyze_patterns()
                
                if insights:
                    # Publish pattern insights event
                    await self.publish(Event(
                        id=str(uuid.uuid4()),
                        type=EventType.SYSTEM_HEALTH_CHECK,
                        source="event_core.pattern_analyzer",
                        timestamp=datetime.now(),
                        priority=EventPriority.LOW,
                        data={"insights": insights}
                    ))
                
            except Exception as e:
                print(f"❌ Pattern analyzer error: {e}")
    
    def _analyze_patterns(self) -> Dict[str, Any]:
        """Analyze event patterns and return insights"""
        insights = {
            'high_frequency_patterns': [],
            'anomalies': [],
            'correlations': [],
            'performance_insights': []
        }
        
        # High frequency pattern detection
        for pattern_key, timestamps in self._event_patterns.items():
            if len(timestamps) > 100:  # Pattern with many occurrences
                # Calculate frequency over last hour
                one_hour_ago = datetime.now() - timedelta(hours=1)
                recent_events = [t for t in timestamps if t > one_hour_ago]
                
                if len(recent_events) > 50:  # High frequency
                    insights['high_frequency_patterns'].append({
                        'pattern': pattern_key,
                        'frequency': len(recent_events),
                        'avg_interval': self._calculate_average_interval(recent_events)
                    })
        
        # Performance insights
        if self._processing_times:
            avg_time = sum(self._processing_times) / len(self._processing_times)
            if avg_time > 0.1:  # Slow processing
                insights['performance_insights'].append({
                    'issue': 'slow_event_processing',
                    'average_time': avg_time,
                    'recommendation': 'Consider optimizing event handlers or increasing concurrency'
                })
        
        return insights
    
    def _calculate_average_interval(self, timestamps: List[datetime]) -> float:
        """Calculate average interval between timestamps"""
        if len(timestamps) < 2:
            return 0.0
        
        intervals = []
        for i in range(1, len(timestamps)):
            interval = (timestamps[i] - timestamps[i-1]).total_seconds()
            intervals.append(interval)
        
        return sum(intervals) / len(intervals)
    
    async def _health_monitor(self):
        """Monitor event system health"""
        while self._running:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Check queue sizes
                main_queue_size = self._event_queue.qsize() if self._event_queue else 0
                priority_queue_sizes = {
                    priority.name: queue.qsize() if queue else 0 
                    for priority, queue in self._priority_queues.items()
                }
                
                # Check for problems
                problems = []
                
                if main_queue_size > self._max_queue_size * 0.8:
                    problems.append("main_queue_near_full")
                
                for priority, size in priority_queue_sizes.items():
                    max_size = self._max_queue_size // len(EventPriority)
                    if size > max_size * 0.8:
                        problems.append(f"{priority}_queue_near_full")
                
                if len(self._failed_events) > 100:
                    problems.append("high_failure_rate")
                
                # Publish health status
                health_data = {
                    'main_queue_size': main_queue_size,
                    'priority_queue_sizes': priority_queue_sizes,
                    'active_handlers': self._stats.active_handlers,
                    'problems': problems,
                    'stats': asdict(self._stats)
                }
                
                await self.publish(Event(
                    id=str(uuid.uuid4()),
                    type=EventType.SYSTEM_HEALTH_CHECK,
                    source="event_core.health_monitor",
                    timestamp=datetime.now(),
                    priority=EventPriority.LOW,
                    data=health_data
                ))
                
            except Exception as e:
                print(f"❌ Health monitor error: {e}")
    
    def _update_average_processing_time(self):
        """Update average processing time"""
        if self._processing_times:
            total_time = sum(self._processing_times)
            self._stats.average_processing_time = total_time / len(self._processing_times)
    
    # ==================== UTILITIES AND HELPERS ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive event system statistics"""
        return {
            'events_published': self._stats.events_published,
            'events_processed': self._stats.events_processed,
            'events_failed': self._stats.events_failed,
            'events_retried': self._stats.events_retried,
            'active_handlers': self._stats.active_handlers,
            'average_processing_time_ms': self._stats.average_processing_time * 1000,
            'events_by_type': dict(self._stats.events_by_type),
            'events_by_priority': dict(self._stats.events_by_priority),
            'queue_sizes': {
                'main': self._event_queue.qsize() if self._event_queue else 0,
                'priority': {
                    priority.name: queue.qsize() if queue else 0
                    for priority, queue in self._priority_queues.items()
                }
            },
            'pattern_count': len(self._event_patterns),
            'correlation_chains': len(self._correlation_chains),
            'failed_events': len(self._failed_events),
            'running': self._running
        }
    
    def get_recent_events(self, limit: int = 100, event_type: Optional[EventType] = None) -> List[Dict[str, Any]]:
        """Get recent events"""
        events = list(self._event_history)
        
        if event_type:
            events = [e for e in events if e.type == event_type]
        
        return [event.to_dict() for event in events[-limit:]]
    
    def get_failed_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get failed events"""
        failed = list(self._failed_events)
        return [event.to_dict() for event in failed[-limit:]]
    
    def clear_failed_events(self):
        """Clear failed events queue"""
        self._failed_events.clear()
    
    # ==================== PERSISTENCE ====================
    
    def _save_persistence(self):
        """Save event core state to disk"""
        try:
            self._persistence_path.parent.mkdir(parents=True, exist_ok=True)
            
            state = {
                'stats': asdict(self._stats),
                'event_patterns': {
                    pattern: [t.isoformat() for t in timestamps[-100:]]  # Keep last 100
                    for pattern, timestamps in self._event_patterns.items()
                },
                'correlation_chains': {
                    correlation_id: chain[-10:]  # Keep last 10
                    for correlation_id, chain in self._correlation_chains.items()
                },
                'timestamp': datetime.now().isoformat()
            }
            
            with open(self._persistence_path, 'w') as f:
                json.dump(state, f, indent=2)
                
        except Exception as e:
            print(f"❌ Failed to save event core state: {e}")
    
    def _load_persistence(self):
        """Load event core state from disk"""
        try:
            if not self._persistence_path.exists():
                return
            
            with open(self._persistence_path, 'r') as f:
                state = json.load(f)
            
            # Restore statistics
            if 'stats' in state:
                for key, value in state['stats'].items():
                    if hasattr(self._stats, key):
                        setattr(self._stats, key, value)
            
            # Restore event patterns
            if 'event_patterns' in state:
                for pattern, timestamps in state['event_patterns'].items():
                    self._event_patterns[pattern] = [
                        datetime.fromisoformat(t) for t in timestamps
                    ]
            
            # Restore correlation chains
            if 'correlation_chains' in state:
                self._correlation_chains.update(state['correlation_chains'])
            
            print(f"📥 Event Core state loaded from {self._persistence_path}")
            
        except Exception as e:
            print(f"❌ Failed to load event core state: {e}")


# ==================== CONVENIENCE FUNCTIONS AND DECORATORS ====================

# Global instance
event_core = None

def get_event_core() -> EventCore:
    """Get global event core instance"""
    global event_core
    if event_core is None:
        event_core = EventCore.get_instance()
    return event_core

def publish_event(event_type: EventType, source: str, data: Dict[str, Any], 
                 priority: EventPriority = EventPriority.MEDIUM) -> bool:
    """Convenience function to publish event"""
    event = Event(
        id=str(uuid.uuid4()),
        type=event_type,
        source=source,
        timestamp=datetime.now(),
        priority=priority,
        data=data
    )
    
    return get_event_core().publish_sync(event)

def subscribe_to_events(event_types: Union[EventType, List[EventType]],
                       priority_filter: Optional[List[EventPriority]] = None,
                       source_filter: Optional[List[str]] = None):
    """Decorator for subscribing functions to events"""
    def decorator(func):
        handler_id = get_event_core().subscribe(
            event_types=event_types,
            callback=func,
            priority_filter=priority_filter,
            source_filter=source_filter
        )
        
        # Store handler ID in function for potential unsubscription
        func._event_handler_id = handler_id
        return func
    
    return decorator

# ==================== SPECIALIZED EVENT PUBLISHERS ====================

def publish_mt5_event(event_type: EventType, data: Dict[str, Any], 
                     priority: EventPriority = EventPriority.HIGH) -> bool:
    """Publish MT5-specific event"""
    return publish_event(event_type, "mt5_handler", data, priority)

def publish_websocket_event(event_type: EventType, data: Dict[str, Any],
                          priority: EventPriority = EventPriority.MEDIUM) -> bool:
    """Publish WebSocket-specific event"""
    return publish_event(event_type, "websocket_client", data, priority)

def publish_config_event(event_type: EventType, data: Dict[str, Any],
                        priority: EventPriority = EventPriority.HIGH) -> bool:
    """Publish configuration-specific event"""
    return publish_event(event_type, "config_manager", data, priority)

def publish_performance_event(data: Dict[str, Any]) -> bool:
    """Publish performance-related event"""
    return publish_event(EventType.PERFORMANCE_ALERT, "performance_monitor", data, EventPriority.LOW)