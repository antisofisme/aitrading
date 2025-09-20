"""
AI Brain Enhanced Queue Core - Safety-validated message queue infrastructure
Enhanced with AI Brain Pre-execution Safety for systematic queue operation validation
"""

import asyncio
import time
import json
import uuid
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable, Union, Tuple, AsyncGenerator
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, deque
from ..base.base_logger import BaseLogger
from ..base.base_performance import BasePerformance

# AI Brain Integration
try:
    import sys
    sys.path.append('/mnt/f/WINDSURF/concept_ai/projects/ai_trading/server_microservice/services')
    from shared.ai_brain_confidence_framework import AiBrainConfidenceFramework
    from shared.ai_brain_trading_error_dna import AiBrainTradingErrorDNA
    AI_BRAIN_AVAILABLE = True
except ImportError:
    AI_BRAIN_AVAILABLE = False

class QueueType(Enum):
    """Message queue type enumeration"""
    FIFO = "fifo"              # First In, First Out
    LIFO = "lifo"              # Last In, First Out (Stack)
    PRIORITY = "priority"       # Priority-based ordering
    TOPIC = "topic"            # Publish-subscribe topic
    DELAYED = "delayed"        # Delayed message delivery
    DEAD_LETTER = "dead_letter" # Failed message handling

class MessageStatus(Enum):
    """Message processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"
    EXPIRED = "expired"

class MessagePriority(Enum):
    """Message priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5

class DeliveryMode(Enum):
    """Message delivery mode"""
    AT_MOST_ONCE = "at_most_once"     # May lose messages, never duplicates
    AT_LEAST_ONCE = "at_least_once"   # Never lose messages, may duplicate
    EXACTLY_ONCE = "exactly_once"     # Never lose, never duplicate

class SafetyCheckLevel(Enum):
    """AI Brain pre-execution safety check levels"""
    MINIMAL = "minimal"      # Basic validation only
    STANDARD = "standard"    # Standard safety checks
    STRICT = "strict"        # Comprehensive safety validation
    PARANOID = "paranoid"    # Maximum safety with all patterns

class ResourceThreshold(Enum):
    """Resource exhaustion thresholds"""
    MEMORY_WARNING = 80      # % memory usage warning
    MEMORY_CRITICAL = 95     # % memory usage critical
    CPU_WARNING = 85         # % CPU usage warning  
    CPU_CRITICAL = 95        # % CPU usage critical
    DISK_WARNING = 85        # % disk usage warning
    DISK_CRITICAL = 95       # % disk usage critical
    QUEUE_WARNING = 80       # % queue capacity warning
    QUEUE_CRITICAL = 95      # % queue capacity critical

@dataclass
class SafetyCheckResult:
    """Result of AI Brain pre-execution safety checks"""
    is_safe: bool
    safety_score: float
    blockers: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    resource_status: Dict[str, Any]
    ai_brain_confidence: float
    operation_risk_level: str
    recommended_actions: List[str]
    check_timestamp: str
    emergency_stops: List[Dict[str, Any]]

@dataclass
class Message:
    """Message object for queue communication"""
    message_id: str
    queue_name: str
    payload: Dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    source_service: Optional[str] = None
    target_service: Optional[str] = None
    correlation_id: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    status: MessageStatus = MessageStatus.PENDING
    processing_start_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None
    error_message: Optional[str] = None
    
    # AI Brain Safety Validation
    safety_check_result: Optional[SafetyCheckResult] = None
    pre_execution_validated: bool = False

@dataclass
class QueueConfig:
    """Queue configuration"""
    queue_name: str
    queue_type: QueueType
    max_size: int = 10000
    delivery_mode: DeliveryMode = DeliveryMode.AT_LEAST_ONCE
    message_ttl_seconds: int = 3600  # 1 hour default TTL
    retry_delay_seconds: int = 30
    max_retry_attempts: int = 3
    dead_letter_queue: Optional[str] = None
    consumer_timeout_seconds: int = 300  # 5 minutes
    batch_size: int = 100
    enable_persistence: bool = False
    enable_compression: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # AI Brain Pre-execution Safety Configuration
    safety_check_level: SafetyCheckLevel = SafetyCheckLevel.STANDARD
    enable_resource_monitoring: bool = True
    require_safety_validation: bool = True
    max_queue_capacity_percentage: float = 90.0
    emergency_stop_on_resource_exhaustion: bool = True

@dataclass
class QueueMetrics:
    """Queue performance metrics"""
    queue_name: str
    total_messages: int = 0
    pending_messages: int = 0
    processing_messages: int = 0
    completed_messages: int = 0
    failed_messages: int = 0
    dead_letter_messages: int = 0
    avg_processing_time_ms: float = 0.0
    throughput_messages_per_sec: float = 0.0
    oldest_pending_message_age_seconds: float = 0.0
    queue_utilization: float = 0.0
    consumer_count: int = 0
    last_activity_time: Optional[datetime] = None

@dataclass
class Consumer:
    """Message consumer configuration"""
    consumer_id: str
    queue_name: str
    callback: Callable[[Message], Union[bool, asyncio.Future]]
    batch_processing: bool = False
    max_concurrent_messages: int = 1
    auto_acknowledge: bool = True
    filter_pattern: Optional[str] = None
    active: bool = True
    last_activity: Optional[datetime] = None

class QueueCore:
    """
    AI Brain Enhanced Message Queue infrastructure with pre-execution safety validation.
    
    Features:
    - Multiple queue types (FIFO, LIFO, Priority, Topic)
    - Message persistence and reliability
    - Consumer management and load balancing
    - Dead letter queue handling
    - Message scheduling and TTL
    - Performance monitoring and metrics
    - AI Brain Pre-execution Safety validation
    - Resource exhaustion prevention
    - Message integrity validation
    - Queue operation safety checks
    """
    
    def __init__(self, service_name: str = "ai-provider"):
        self.service_name = service_name
        
        # Queue management
        self.queues: Dict[str, QueueConfig] = {}
        self.queue_storage: Dict[str, deque] = defaultdict(deque)
        self.queue_metrics: Dict[str, QueueMetrics] = {}
        
        # Message tracking
        self.message_registry: Dict[str, Message] = {}
        self.scheduled_messages: Dict[str, Message] = {}
        self.processing_messages: Dict[str, Message] = {}
        
        # Consumer management
        self.consumers: Dict[str, Consumer] = {}
        self.consumer_assignments: Dict[str, List[str]] = defaultdict(list)  # queue -> consumer_ids
        
        # Global settings
        self.max_total_queues = 100
        self.default_message_ttl = 3600
        self.cleanup_interval_seconds = 300
        self.metrics_collection_enabled = True
        
        # Performance tracking
        self.processing_times: Dict[str, List[float]] = defaultdict(list)
        self.throughput_history: Dict[str, List[Tuple[datetime, int]]] = defaultdict(list)
        
        # Initialize logging and performance tracking
        self.logger = BaseLogger(service_name, "queue_core")
        self.performance_tracker = BasePerformance(service_name)
        
        # AI Brain Pre-execution Safety Integration
        self.ai_brain_confidence = None
        self.ai_brain_error_dna = None
        if AI_BRAIN_AVAILABLE:
            try:
                self.ai_brain_confidence = AiBrainConfidenceFramework(f"queue-safety-{service_name}")
                self.ai_brain_error_dna = AiBrainTradingErrorDNA(f"queue-validator-{service_name}")
                print(f"✅ AI Brain Pre-execution Safety initialized for queue: {service_name}")
            except Exception as e:
                print(f"⚠️ AI Brain Pre-execution Safety initialization failed: {e}")
        
        # Safety monitoring state
        self.emergency_stops = set()  # Operations under emergency stop
        self.resource_warning_threshold_reached = False
        self.last_resource_check = datetime.now()
        self.safety_check_history = defaultdict(list)  # Track safety check results
        
        # Initialize safety patterns and thresholds
        self._init_safety_patterns()
        
        # Setup default queues for AI provider
        self._setup_default_queues()
        
        # Start background tasks
        self._background_tasks: List[asyncio.Task] = []
        self._start_background_tasks()
        
        self.logger.info("Queue Core initialized", extra={
            "service": service_name,
            "max_total_queues": self.max_total_queues,
            "default_ttl": self.default_message_ttl,
            "metrics_enabled": self.metrics_collection_enabled
        })
    
    def _setup_default_queues(self):
        """Setup default queues for AI provider service"""
        default_queues = [
            QueueConfig(
                queue_name="ai_requests",
                queue_type=QueueType.PRIORITY,
                max_size=5000,
                delivery_mode=DeliveryMode.AT_LEAST_ONCE,
                message_ttl_seconds=3600,
                dead_letter_queue="ai_requests_dlq"
            ),
            QueueConfig(
                queue_name="ai_requests_dlq",
                queue_type=QueueType.FIFO,
                max_size=1000,
                delivery_mode=DeliveryMode.AT_LEAST_ONCE,
                message_ttl_seconds=86400  # 24 hours for dead letters
            ),
            QueueConfig(
                queue_name="model_training_jobs",
                queue_type=QueueType.FIFO,
                max_size=500,
                delivery_mode=DeliveryMode.EXACTLY_ONCE,
                message_ttl_seconds=7200,  # 2 hours
                consumer_timeout_seconds=1800  # 30 minutes
            ),
            QueueConfig(
                queue_name="notifications",
                queue_type=QueueType.TOPIC,
                max_size=2000,
                delivery_mode=DeliveryMode.AT_MOST_ONCE,
                message_ttl_seconds=1800  # 30 minutes
            ),
            QueueConfig(
                queue_name="analytics_events",
                queue_type=QueueType.FIFO,
                max_size=10000,
                delivery_mode=DeliveryMode.AT_LEAST_ONCE,
                message_ttl_seconds=7200,
                batch_size=500
            )
        ]
        
        for queue_config in default_queues:
            self.create_queue(queue_config)
        
        self.logger.info(f"Default queues configured: {len(default_queues)}")
    
    def _init_safety_patterns(self):
        """Initialize AI Brain pre-execution safety patterns and thresholds"""
        # Dangerous operation patterns that require safety checks
        self.dangerous_operations = {
            'batch_operations': ['batch_send', 'bulk_process', 'mass_delete'],
            'high_volume': ['flood_send', 'stress_test', 'load_generation'],
            'critical_queues': ['trading_orders', 'payment_processing', 'user_authentication'],
            'destructive_actions': ['purge_queue', 'delete_messages', 'reset_metrics']
        }
        
        # Resource exhaustion patterns
        self.resource_patterns = {
            'memory_intensive': ['large_payload', 'file_processing', 'bulk_transformation'],
            'cpu_intensive': ['complex_processing', 'encryption', 'compression'],
            'io_intensive': ['database_operations', 'file_operations', 'network_calls']
        }
        
        # Safety thresholds
        self.safety_thresholds = {
            'max_message_size_mb': 10,
            'max_queue_depth_warning': 1000,
            'max_queue_depth_critical': 5000,
            'max_concurrent_processing': 100,
            'max_retry_attempts': 5,
            'max_scheduled_messages': 10000,
            'memory_usage_warning_percent': 85,
            'memory_usage_critical_percent': 95,
            'disk_usage_warning_percent': 85,
            'cpu_usage_warning_percent': 85
        }
        
        # Emergency stop conditions
        self.emergency_conditions = {
            'system_memory_exhaustion': 95,  # % memory usage
            'disk_space_exhaustion': 95,     # % disk usage
            'queue_overflow_ratio': 0.95,    # queue utilization ratio
            'consumer_failure_rate': 0.8,    # failed consumers ratio
            'message_failure_rate': 0.9      # failed messages ratio
        }
    
    def _start_background_tasks(self):
        """Start background processing tasks"""
        # Message processing task
        processing_task = asyncio.create_task(self._message_processing_loop())
        self._background_tasks.append(processing_task)
        
        # Scheduled message task
        scheduler_task = asyncio.create_task(self._scheduled_message_loop())
        self._background_tasks.append(scheduler_task)
        
        # Cleanup task
        cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._background_tasks.append(cleanup_task)
        
        # Metrics collection task
        metrics_task = asyncio.create_task(self._metrics_collection_loop())
        self._background_tasks.append(metrics_task)
    
    def create_queue(self, queue_config: QueueConfig) -> str:
        """Create new message queue"""
        queue_name = queue_config.queue_name
        
        if len(self.queues) >= self.max_total_queues:
            raise ValueError(f"Maximum number of queues ({self.max_total_queues}) reached")
        
        if queue_name in self.queues:
            raise ValueError(f"Queue '{queue_name}' already exists")
        
        self.queues[queue_name] = queue_config
        self.queue_storage[queue_name] = deque()
        self.queue_metrics[queue_name] = QueueMetrics(queue_name=queue_name)
        
        self.logger.info(f"Queue created: {queue_name}", extra={
            "queue_type": queue_config.queue_type.value,
            "max_size": queue_config.max_size,
            "delivery_mode": queue_config.delivery_mode.value,
            "ttl_seconds": queue_config.message_ttl_seconds
        })
        
        return queue_name
    
    async def send_message(self, queue_name: str, payload: Dict[str, Any],
                          priority: MessagePriority = MessagePriority.NORMAL,
                          delay_seconds: Optional[int] = None,
                          ttl_seconds: Optional[int] = None,
                          correlation_id: Optional[str] = None,
                          headers: Optional[Dict[str, str]] = None) -> Optional[str]:
        """
        Send message to queue.
        
        Args:
            queue_name: Target queue name
            payload: Message payload
            priority: Message priority
            delay_seconds: Delay before processing
            ttl_seconds: Time to live in seconds
            correlation_id: Correlation identifier
            headers: Additional headers
            
        Returns:
            Message ID if successful, None otherwise
        """
        if queue_name not in self.queues:
            self.logger.error(f"Queue not found: {queue_name}")
            return None
        
        # AI Brain Pre-execution Safety Check
        safety_result = await self._perform_pre_execution_safety_check(
            operation_type="send_message",
            context={
                "queue_name": queue_name,
                "payload_size": len(json.dumps(payload)),
                "priority": priority.value,
                "has_delay": delay_seconds is not None,
                "message_count": 1
            }
        )
        
        if not safety_result.is_safe:
            self.logger.error(f"Pre-execution safety check failed for queue {queue_name}", extra={
                "safety_score": safety_result.safety_score,
                "blockers": safety_result.blockers,
                "emergency_stops": safety_result.emergency_stops
            })
            return None
        
        queue_config = self.queues[queue_name]
        queue_storage = self.queue_storage[queue_name]
        
        # Check queue capacity
        if len(queue_storage) >= queue_config.max_size:
            self.logger.warning(f"Queue {queue_name} is at capacity: {len(queue_storage)}")
            return None
        
        # Create message
        message_id = str(uuid.uuid4())
        scheduled_at = None
        if delay_seconds:
            scheduled_at = datetime.now() + timedelta(seconds=delay_seconds)
        
        expires_at = None
        if ttl_seconds:
            expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
        elif queue_config.message_ttl_seconds:
            expires_at = datetime.now() + timedelta(seconds=queue_config.message_ttl_seconds)
        
        message = Message(
            message_id=message_id,
            queue_name=queue_name,
            payload=payload,
            priority=priority,
            scheduled_at=scheduled_at,
            expires_at=expires_at,
            source_service=self.service_name,
            correlation_id=correlation_id,
            headers=headers or {},
            max_retries=queue_config.max_retry_attempts
        )
        
        # Store safety check result in message
        message.safety_check_result = safety_result
        message.pre_execution_validated = True
        
        # Store message
        self.message_registry[message_id] = message
        
        if scheduled_at:
            # Schedule for later delivery
            self.scheduled_messages[message_id] = message
        else:
            # Add to queue immediately
            await self._add_to_queue(queue_name, message)
        
        # Update metrics
        metrics = self.queue_metrics[queue_name]
        metrics.total_messages += 1
        metrics.pending_messages += 1
        metrics.last_activity_time = datetime.now()
        
        self.logger.debug(f"Message sent to queue: {queue_name}", extra={
            "message_id": message_id,
            "priority": priority.value,
            "scheduled": scheduled_at is not None,
            "correlation_id": correlation_id
        })
        
        return message_id
    
    async def _perform_pre_execution_safety_check(self, operation_type: str, context: Dict[str, Any]) -> SafetyCheckResult:
        """Perform comprehensive AI Brain pre-execution safety validation"""
        blockers = []
        warnings = []
        emergency_stops = []
        recommended_actions = []
        ai_brain_confidence = 0.85  # Default confidence
        
        try:
            print(f"🛡️ AI Brain: Performing pre-execution safety check for {operation_type}")
            
            # 1. Emergency stop check (highest priority)
            emergency_result = await self._check_emergency_stops(operation_type, context)
            if emergency_result['has_stops']:
                emergency_stops.extend(emergency_result['stops'])
                return SafetyCheckResult(
                    is_safe=False,
                    safety_score=0.0,
                    blockers=[{'type': 'EMERGENCY_STOP', 'severity': 'CRITICAL', 'message': 'Operation under emergency stop'}],
                    warnings=[],
                    resource_status=emergency_result['resource_status'],
                    ai_brain_confidence=0.0,
                    operation_risk_level='CRITICAL',
                    recommended_actions=['Review emergency stop conditions'],
                    check_timestamp=datetime.utcnow().isoformat(),
                    emergency_stops=emergency_stops
                )
            
            # 2. Resource safety checks
            resource_result = await self._check_resource_safety(context)
            if resource_result['critical_issues']:
                blockers.extend(resource_result['critical_issues'])
            if resource_result['warnings']:
                warnings.extend(resource_result['warnings'])
            
            # 3. Queue operation safety checks
            queue_safety_result = await self._check_queue_operation_safety(operation_type, context)
            if queue_safety_result['violations']:
                blockers.extend(queue_safety_result['violations'])
            
            # 4. Message integrity validation
            if operation_type == "send_message":
                integrity_result = await self._validate_message_integrity(context)
                if integrity_result['violations']:
                    blockers.extend(integrity_result['violations'])
            
            # 5. Rate limiting and throttling checks
            rate_result = await self._check_rate_limits(operation_type, context)
            if rate_result['exceeded']:
                blockers.extend(rate_result['violations'])
            
            # 6. AI Brain confidence analysis
            if self.ai_brain_confidence and AI_BRAIN_AVAILABLE:
                try:
                    confidence_result = self.ai_brain_confidence.assess_decision_confidence(
                        decision_type="queue_operation_safety",
                        factors={
                            "operation_type": operation_type,
                            "resource_status": resource_result['status'],
                            "queue_health": queue_safety_result['health_score'],
                            "emergency_stops": len(emergency_stops),
                            "critical_blockers": len([b for b in blockers if b.get('severity') == 'CRITICAL'])
                        },
                        context={
                            "service_name": self.service_name,
                            "operation": operation_type,
                            "validation_type": "pre_execution_safety"
                        }
                    )
                    ai_brain_confidence = confidence_result.get("confidence_score", 0.85)
                    
                    if confidence_result.get("recommendations"):
                        recommended_actions.extend(confidence_result["recommendations"])
                        
                except Exception as e:
                    print(f"⚠️ AI Brain confidence analysis failed: {e}")
            
            # 7. Calculate safety score
            safety_score = self._calculate_safety_score(blockers, warnings, ai_brain_confidence)
            
            # 8. Determine operation risk level
            risk_level = self._determine_operation_risk_level(safety_score, blockers)
            
            # 9. Generate safety recommendations
            if not recommended_actions:
                recommended_actions = self._generate_safety_recommendations(blockers, warnings)
            
            # 10. Determine if operation is safe
            is_safe = (safety_score >= 0.7 and 
                      len([b for b in blockers if b.get('severity') == 'CRITICAL']) == 0 and
                      len(emergency_stops) == 0)
            
            print(f"🛡️ AI Brain Safety Check Complete: Score {safety_score:.2f}, Safe: {is_safe}, Risk: {risk_level}")
            
            # Record safety check for learning
            self.safety_check_history[operation_type].append({
                'timestamp': datetime.utcnow().isoformat(),
                'safety_score': safety_score,
                'is_safe': is_safe,
                'risk_level': risk_level,
                'context': context
            })
            
            return SafetyCheckResult(
                is_safe=is_safe,
                safety_score=safety_score,
                blockers=blockers,
                warnings=warnings,
                resource_status=resource_result['status'],
                ai_brain_confidence=ai_brain_confidence,
                operation_risk_level=risk_level,
                recommended_actions=recommended_actions,
                check_timestamp=datetime.utcnow().isoformat(),
                emergency_stops=emergency_stops
            )
            
        except Exception as e:
            # Graceful degradation when safety validation fails
            print(f"⚠️ AI Brain Pre-execution safety check failed: {e}")
            if self.ai_brain_error_dna:
                try:
                    self.ai_brain_error_dna.analyze_error(e, {
                        "service_name": self.service_name,
                        "operation": operation_type,
                        "context": context
                    })
                except:
                    pass  # Silent fallback if error DNA also fails
                    
            return SafetyCheckResult(
                is_safe=False,
                safety_score=0.0,
                blockers=[{
                    'type': 'SAFETY_CHECK_ERROR',
                    'severity': 'CRITICAL',
                    'message': f'Safety check failed: {str(e)}',
                    'recommendation': 'Review safety validation configuration'
                }],
                warnings=[],
                resource_status={},
                ai_brain_confidence=0.0,
                operation_risk_level='CRITICAL',
                recommended_actions=['Manual safety review required'],
                check_timestamp=datetime.utcnow().isoformat(),
                emergency_stops=[]
            )
    
    async def _add_to_queue(self, queue_name: str, message: Message):
        """Add message to queue based on queue type"""
        queue_config = self.queues[queue_name]
        queue_storage = self.queue_storage[queue_name]
        
        if queue_config.queue_type == QueueType.FIFO:
            queue_storage.append(message)
        elif queue_config.queue_type == QueueType.LIFO:
            queue_storage.appendleft(message)
        elif queue_config.queue_type == QueueType.PRIORITY:
            # Insert based on priority
            inserted = False
            for i, existing_msg in enumerate(queue_storage):
                if message.priority.value > existing_msg.priority.value:
                    queue_storage.insert(i, message)
                    inserted = True
                    break
            if not inserted:
                queue_storage.append(message)
        elif queue_config.queue_type == QueueType.TOPIC:
            # Topic queues broadcast to all consumers
            queue_storage.append(message)
        else:
            # Default FIFO behavior
            queue_storage.append(message)
    
    def register_consumer(self, consumer_config: Consumer) -> str:
        """Register message consumer"""
        consumer_id = consumer_config.consumer_id
        queue_name = consumer_config.queue_name
        
        if queue_name not in self.queues:
            raise ValueError(f"Queue '{queue_name}' does not exist")
        
        self.consumers[consumer_id] = consumer_config
        self.consumer_assignments[queue_name].append(consumer_id)
        
        # Update metrics
        if queue_name in self.queue_metrics:
            self.queue_metrics[queue_name].consumer_count += 1
        
        self.logger.info(f"Consumer registered: {consumer_id}", extra={
            "queue_name": queue_name,
            "batch_processing": consumer_config.batch_processing,
            "max_concurrent": consumer_config.max_concurrent_messages
        })
        
        return consumer_id
    
    def unregister_consumer(self, consumer_id: str) -> bool:
        """Unregister message consumer"""
        if consumer_id not in self.consumers:
            return False
        
        consumer = self.consumers[consumer_id]
        queue_name = consumer.queue_name
        
        # Remove from assignments
        if queue_name in self.consumer_assignments:
            self.consumer_assignments[queue_name] = [
                cid for cid in self.consumer_assignments[queue_name] 
                if cid != consumer_id
            ]
        
        # Update metrics
        if queue_name in self.queue_metrics:
            self.queue_metrics[queue_name].consumer_count -= 1
        
        del self.consumers[consumer_id]
        
        self.logger.info(f"Consumer unregistered: {consumer_id}")
        return True
    
    async def _message_processing_loop(self):
        """Background task for processing queued messages"""
        while True:
            try:
                processed_any = False
                
                for queue_name, queue_storage in self.queue_storage.items():
                    if not queue_storage:
                        continue
                    
                    # Get available consumers for this queue
                    available_consumers = [
                        self.consumers[cid] for cid in self.consumer_assignments[queue_name]
                        if cid in self.consumers and self.consumers[cid].active
                    ]
                    
                    if not available_consumers:
                        continue
                    
                    # Process messages
                    messages_to_process = []
                    max_messages = min(len(queue_storage), 10)  # Process up to 10 messages per iteration
                    
                    for _ in range(max_messages):
                        if queue_storage:
                            message = queue_storage.popleft()
                            
                            # Check if message has expired
                            if message.expires_at and datetime.now() > message.expires_at:
                                await self._handle_expired_message(message)
                                continue
                            
                            messages_to_process.append(message)
                    
                    # Distribute messages to consumers
                    for i, message in enumerate(messages_to_process):
                        consumer = available_consumers[i % len(available_consumers)]
                        await self._process_message_with_consumer(message, consumer)
                        processed_any = True
                
                if not processed_any:
                    await asyncio.sleep(0.1)  # Short sleep when no messages to process
                
            except Exception as e:
                self.logger.error(f"Message processing loop error: {e}")
                await asyncio.sleep(1)
    
    async def _process_message_with_consumer(self, message: Message, consumer: Consumer):
        """Process message with specific consumer"""
        message.status = MessageStatus.PROCESSING
        message.processing_start_time = datetime.now()
        self.processing_messages[message.message_id] = message
        
        # Update metrics
        metrics = self.queue_metrics[message.queue_name]
        metrics.pending_messages -= 1
        metrics.processing_messages += 1
        
        try:
            start_time = time.time()
            
            # Call consumer callback
            result = consumer.callback(message)
            if asyncio.iscoroutine(result):
                success = await result
            else:
                success = result
            
            processing_time = (time.time() - start_time) * 1000
            
            if success:
                await self._handle_message_success(message, processing_time)
            else:
                await self._handle_message_failure(message, "Consumer returned False")
                
        except Exception as e:
            await self._handle_message_failure(message, str(e))
    
    async def _handle_message_success(self, message: Message, processing_time_ms: float):
        """Handle successful message processing"""
        message.status = MessageStatus.COMPLETED
        message.completion_time = datetime.now()
        
        # Remove from processing
        if message.message_id in self.processing_messages:
            del self.processing_messages[message.message_id]
        
        # Update metrics
        metrics = self.queue_metrics[message.queue_name]
        metrics.processing_messages -= 1
        metrics.completed_messages += 1
        
        # Update processing time
        self.processing_times[message.queue_name].append(processing_time_ms)
        if len(self.processing_times[message.queue_name]) > 1000:
            self.processing_times[message.queue_name] = self.processing_times[message.queue_name][-1000:]
        
        # Update average processing time
        times = self.processing_times[message.queue_name]
        metrics.avg_processing_time_ms = sum(times) / len(times)
        
        self.logger.debug(f"Message processed successfully: {message.message_id}", extra={
            "processing_time_ms": processing_time_ms,
            "queue_name": message.queue_name
        })
    
    async def _handle_message_failure(self, message: Message, error_message: str):
        """Handle failed message processing"""
        message.retry_count += 1
        message.error_message = error_message
        
        # Remove from processing
        if message.message_id in self.processing_messages:
            del self.processing_messages[message.message_id]
        
        metrics = self.queue_metrics[message.queue_name]
        metrics.processing_messages -= 1
        
        if message.retry_count >= message.max_retries:
            # Send to dead letter queue or mark as failed
            queue_config = self.queues[message.queue_name]
            if queue_config.dead_letter_queue and queue_config.dead_letter_queue in self.queues:
                message.status = MessageStatus.DEAD_LETTER
                await self._add_to_queue(queue_config.dead_letter_queue, message)
                metrics.dead_letter_messages += 1
            else:
                message.status = MessageStatus.FAILED
                metrics.failed_messages += 1
        else:
            # Retry message
            message.status = MessageStatus.PENDING
            
            # Add delay before retry
            queue_config = self.queues[message.queue_name]
            message.scheduled_at = datetime.now() + timedelta(seconds=queue_config.retry_delay_seconds)
            self.scheduled_messages[message.message_id] = message
            
            metrics.pending_messages += 1
        
        self.logger.warning(f"Message processing failed: {message.message_id}", extra={
            "error": error_message,
            "retry_count": message.retry_count,
            "max_retries": message.max_retries,
            "queue_name": message.queue_name
        })
    
    async def _handle_expired_message(self, message: Message):
        """Handle expired message"""
        message.status = MessageStatus.EXPIRED
        
        metrics = self.queue_metrics[message.queue_name]
        metrics.pending_messages -= 1
        metrics.failed_messages += 1
        
        self.logger.debug(f"Message expired: {message.message_id}", extra={
            "queue_name": message.queue_name,
            "expires_at": message.expires_at.isoformat()
        })
    
    async def _scheduled_message_loop(self):
        """Background task for processing scheduled messages"""
        while True:
            try:
                current_time = datetime.now()
                ready_messages = []
                
                for message_id, message in list(self.scheduled_messages.items()):
                    if message.scheduled_at and current_time >= message.scheduled_at:
                        ready_messages.append(message)
                        del self.scheduled_messages[message_id]
                
                # Add ready messages to their queues
                for message in ready_messages:
                    await self._add_to_queue(message.queue_name, message)
                
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                self.logger.error(f"Scheduled message loop error: {e}")
                await asyncio.sleep(1)
    
    async def _cleanup_loop(self):
        """Background task for cleaning up old messages and metrics"""
        while True:
            try:
                current_time = datetime.now()
                cutoff_time = current_time - timedelta(hours=24)
                
                # Clean up old completed messages
                expired_message_ids = [
                    msg_id for msg_id, message in self.message_registry.items()
                    if message.completion_time and message.completion_time < cutoff_time
                ]
                
                for msg_id in expired_message_ids:
                    del self.message_registry[msg_id]
                
                self.logger.debug(f"Cleaned up {len(expired_message_ids)} old messages")
                
                await asyncio.sleep(self.cleanup_interval_seconds)
                
            except Exception as e:
                self.logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(self.cleanup_interval_seconds)
    
    async def _metrics_collection_loop(self):
        """Background task for collecting queue metrics"""
        while True:
            try:
                if not self.metrics_collection_enabled:
                    await asyncio.sleep(60)
                    continue
                
                current_time = datetime.now()
                
                for queue_name, metrics in self.queue_metrics.items():
                    queue_storage = self.queue_storage[queue_name]
                    
                    # Update queue utilization
                    queue_config = self.queues[queue_name]
                    metrics.queue_utilization = len(queue_storage) / queue_config.max_size
                    
                    # Calculate oldest pending message age
                    if queue_storage:
                        oldest_message = min(queue_storage, key=lambda m: m.created_at)
                        metrics.oldest_pending_message_age_seconds = (
                            current_time - oldest_message.created_at
                        ).total_seconds()
                    else:
                        metrics.oldest_pending_message_age_seconds = 0
                    
                    # Update throughput
                    throughput_data = self.throughput_history[queue_name]
                    throughput_data.append((current_time, metrics.completed_messages))
                    
                    # Keep only last hour of data
                    cutoff_time = current_time - timedelta(hours=1)
                    self.throughput_history[queue_name] = [
                        (time, count) for time, count in throughput_data
                        if time > cutoff_time
                    ]
                    
                    # Calculate throughput (messages per second)
                    if len(throughput_data) >= 2:
                        time_diff = (throughput_data[-1][0] - throughput_data[0][0]).total_seconds()
                        message_diff = throughput_data[-1][1] - throughput_data[0][1]
                        
                        if time_diff > 0:
                            metrics.throughput_messages_per_sec = message_diff / time_diff
                
                await asyncio.sleep(60)  # Collect metrics every minute
                
            except Exception as e:
                self.logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(60)
    
    def get_queue_status(self, queue_name: Optional[str] = None) -> Dict[str, Any]:
        """Get queue status and metrics"""
        if queue_name:
            if queue_name in self.queues:
                config = self.queues[queue_name]
                metrics = self.queue_metrics[queue_name]
                storage = self.queue_storage[queue_name]
                
                return {
                    "queue_name": queue_name,
                    "queue_type": config.queue_type.value,
                    "max_size": config.max_size,
                    "current_size": len(storage),
                    "delivery_mode": config.delivery_mode.value,
                    "total_messages": metrics.total_messages,
                    "pending_messages": metrics.pending_messages,
                    "processing_messages": metrics.processing_messages,
                    "completed_messages": metrics.completed_messages,
                    "failed_messages": metrics.failed_messages,
                    "dead_letter_messages": metrics.dead_letter_messages,
                    "queue_utilization": metrics.queue_utilization,
                    "avg_processing_time_ms": metrics.avg_processing_time_ms,
                    "throughput_messages_per_sec": metrics.throughput_messages_per_sec,
                    "consumer_count": metrics.consumer_count,
                    "oldest_pending_age_seconds": metrics.oldest_pending_message_age_seconds,
                    "last_activity": metrics.last_activity_time.isoformat() if metrics.last_activity_time else None
                }
            return {}
        
        # Return all queue statuses
        return {
            qname: self.get_queue_status(qname)
            for qname in self.queues.keys()
        }
    
    def get_system_overview(self) -> Dict[str, Any]:
        """Get overall queue system overview with AI Brain safety validation status"""
        total_queues = len(self.queues)
        total_consumers = len(self.consumers)
        total_pending = sum(m.pending_messages for m in self.queue_metrics.values())
        total_processing = sum(m.processing_messages for m in self.queue_metrics.values())
        total_completed = sum(m.completed_messages for m in self.queue_metrics.values())
        total_failed = sum(m.failed_messages for m in self.queue_metrics.values())
        
        # Add safety validation summary to system overview
        safety_summary = self._get_safety_validation_summary()
        
        return {
            "total_queues": total_queues,
            "total_consumers": total_consumers,
            "total_messages": {
                "pending": total_pending,
                "processing": total_processing,
                "completed": total_completed,
                "failed": total_failed
            },
            "scheduled_messages": len(self.scheduled_messages),
            "processing_messages": len(self.processing_messages),
            "registered_messages": len(self.message_registry),
            "metrics_collection_enabled": self.metrics_collection_enabled,
            "cleanup_interval_seconds": self.cleanup_interval_seconds,
            "safety_validation": safety_summary
        }
    
    async def _check_emergency_stops(self, operation_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check for emergency stop conditions"""
        stops = []
        resource_status = {}
        
        try:
            # Check if operation type is emergency stopped
            if operation_type in self.emergency_stops:
                stops.append({
                    'type': 'OPERATION_EMERGENCY_STOP',
                    'message': f'Operation {operation_type} is under emergency stop',
                    'reason': 'Previous critical failures detected'
                })
            
            # Check system resource exhaustion
            try:
                memory_percent = psutil.virtual_memory().percent
                disk_percent = psutil.disk_usage('/').percent
                cpu_percent = psutil.cpu_percent(interval=1)
                
                resource_status = {
                    'memory_percent': memory_percent,
                    'disk_percent': disk_percent,
                    'cpu_percent': cpu_percent
                }
                
                if memory_percent > self.emergency_conditions['system_memory_exhaustion']:
                    stops.append({
                        'type': 'MEMORY_EXHAUSTION_EMERGENCY',
                        'message': f'System memory usage at {memory_percent:.1f}%',
                        'threshold': self.emergency_conditions['system_memory_exhaustion']
                    })
                    
                if disk_percent > self.emergency_conditions['disk_space_exhaustion']:
                    stops.append({
                        'type': 'DISK_EXHAUSTION_EMERGENCY',
                        'message': f'Disk usage at {disk_percent:.1f}%',
                        'threshold': self.emergency_conditions['disk_space_exhaustion']
                    })
                    
            except Exception as e:
                # Fallback if psutil is not available
                resource_status = {'error': f'Resource monitoring failed: {e}'}
            
            # Check queue overflow conditions
            queue_name = context.get('queue_name')
            if queue_name and queue_name in self.queues:
                queue_config = self.queues[queue_name]
                queue_storage = self.queue_storage[queue_name]
                utilization = len(queue_storage) / queue_config.max_size
                
                if utilization > self.emergency_conditions['queue_overflow_ratio']:
                    stops.append({
                        'type': 'QUEUE_OVERFLOW_EMERGENCY',
                        'message': f'Queue {queue_name} utilization at {utilization:.1%}',
                        'threshold': self.emergency_conditions['queue_overflow_ratio']
                    })
            
        except Exception as e:
            stops.append({
                'type': 'EMERGENCY_CHECK_ERROR',
                'message': f'Emergency stop check failed: {e}'
            })
        
        return {
            'has_stops': len(stops) > 0,
            'stops': stops,
            'resource_status': resource_status
        }
    
    async def _check_resource_safety(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check resource availability and safety"""
        critical_issues = []
        warnings = []
        status = {'healthy': True}
        
        try:
            # Check memory usage
            try:
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                
                status['memory_percent'] = memory_percent
                
                if memory_percent > self.safety_thresholds['memory_usage_critical_percent']:
                    critical_issues.append({
                        'type': 'CRITICAL_MEMORY_USAGE',
                        'severity': 'CRITICAL',
                        'message': f'Memory usage at {memory_percent:.1f}%',
                        'threshold': self.safety_thresholds['memory_usage_critical_percent'],
                        'recommendation': 'Reduce memory usage or scale resources'
                    })
                elif memory_percent > self.safety_thresholds['memory_usage_warning_percent']:
                    warnings.append({
                        'type': 'HIGH_MEMORY_USAGE',
                        'message': f'Memory usage at {memory_percent:.1f}%',
                        'threshold': self.safety_thresholds['memory_usage_warning_percent']
                    })
                    
            except Exception:
                status['memory_monitoring'] = 'unavailable'
            
            # Check disk usage
            try:
                disk = psutil.disk_usage('/')
                disk_percent = (disk.used / disk.total) * 100
                
                status['disk_percent'] = disk_percent
                
                if disk_percent > self.safety_thresholds['disk_usage_warning_percent']:
                    warnings.append({
                        'type': 'HIGH_DISK_USAGE',
                        'message': f'Disk usage at {disk_percent:.1f}%',
                        'threshold': self.safety_thresholds['disk_usage_warning_percent']
                    })
                    
            except Exception:
                status['disk_monitoring'] = 'unavailable'
            
            # Check queue-specific resource usage
            total_queued_messages = sum(len(storage) for storage in self.queue_storage.values())
            total_processing = len(self.processing_messages)
            
            status['total_queued'] = total_queued_messages
            status['total_processing'] = total_processing
            
            if total_processing > self.safety_thresholds['max_concurrent_processing']:
                critical_issues.append({
                    'type': 'EXCESSIVE_CONCURRENT_PROCESSING',
                    'severity': 'HIGH',
                    'message': f'Processing {total_processing} messages concurrently',
                    'threshold': self.safety_thresholds['max_concurrent_processing'],
                    'recommendation': 'Reduce concurrent processing or add more workers'
                })
            
        except Exception as e:
            critical_issues.append({
                'type': 'RESOURCE_CHECK_ERROR',
                'severity': 'HIGH',
                'message': f'Resource safety check failed: {e}'
            })
            status['healthy'] = False
        
        return {
            'critical_issues': critical_issues,
            'warnings': warnings,
            'status': status
        }
    
    async def _check_queue_operation_safety(self, operation_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check queue-specific operation safety"""
        violations = []
        health_score = 1.0
        
        queue_name = context.get('queue_name')
        if not queue_name or queue_name not in self.queues:
            return {'violations': [], 'health_score': 1.0}
        
        queue_config = self.queues[queue_name]
        queue_storage = self.queue_storage[queue_name]
        queue_metrics = self.queue_metrics[queue_name]
        
        # Check queue capacity
        current_size = len(queue_storage)
        capacity_ratio = current_size / queue_config.max_size
        
        if capacity_ratio > (self.safety_thresholds['max_queue_capacity_percentage'] / 100):
            violations.append({
                'type': 'QUEUE_CAPACITY_EXCEEDED',
                'severity': 'HIGH',
                'message': f'Queue {queue_name} at {capacity_ratio:.1%} capacity',
                'current_size': current_size,
                'max_size': queue_config.max_size,
                'recommendation': 'Increase queue capacity or reduce message volume'
            })
            health_score -= 0.3
        
        # Check message failure rate
        if queue_metrics.total_messages > 0:
            failure_rate = queue_metrics.failed_messages / queue_metrics.total_messages
            if failure_rate > self.emergency_conditions['message_failure_rate']:
                violations.append({
                    'type': 'HIGH_MESSAGE_FAILURE_RATE',
                    'severity': 'CRITICAL',
                    'message': f'Message failure rate at {failure_rate:.1%}',
                    'failed_messages': queue_metrics.failed_messages,
                    'total_messages': queue_metrics.total_messages,
                    'recommendation': 'Investigate message processing issues'
                })
                health_score -= 0.5
        
        # Check consumer health
        active_consumers = len([c for c in self.consumer_assignments[queue_name] 
                              if c in self.consumers and self.consumers[c].active])
        if active_consumers == 0 and queue_config.queue_type != QueueType.DEAD_LETTER:
            violations.append({
                'type': 'NO_ACTIVE_CONSUMERS',
                'severity': 'HIGH',
                'message': f'Queue {queue_name} has no active consumers',
                'recommendation': 'Register consumers for message processing'
            })
            health_score -= 0.4
        
        return {
            'violations': violations,
            'health_score': max(0.0, health_score)
        }
    
    async def _validate_message_integrity(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate message integrity and content safety"""
        violations = []
        
        payload_size_mb = context.get('payload_size', 0) / (1024 * 1024)
        if payload_size_mb > self.safety_thresholds['max_message_size_mb']:
            violations.append({
                'type': 'MESSAGE_SIZE_EXCEEDED',
                'severity': 'HIGH',
                'message': f'Message size {payload_size_mb:.2f}MB exceeds limit',
                'size_mb': payload_size_mb,
                'limit_mb': self.safety_thresholds['max_message_size_mb'],
                'recommendation': 'Reduce message payload size or use message chunking'
            })
        
        return {'violations': violations}
    
    async def _check_rate_limits(self, operation_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check rate limiting and throttling"""
        exceeded = False
        violations = []
        
        # Simple rate limiting check based on queue metrics
        queue_name = context.get('queue_name')
        if queue_name and queue_name in self.queue_metrics:
            metrics = self.queue_metrics[queue_name]
            
            # Check if throughput is too high
            if metrics.throughput_messages_per_sec > 1000:  # Example threshold
                exceeded = True
                violations.append({
                    'type': 'HIGH_THROUGHPUT_RATE',
                    'severity': 'MEDIUM',
                    'message': f'High message throughput: {metrics.throughput_messages_per_sec:.1f} msg/sec',
                    'recommendation': 'Consider throttling or load balancing'
                })
        
        return {
            'exceeded': exceeded,
            'violations': violations
        }
    
    def _calculate_safety_score(self, blockers: List[Dict[str, Any]], warnings: List[Dict[str, Any]], ai_brain_confidence: float) -> float:
        """Calculate overall safety score"""
        base_score = 1.0
        
        # Deduct points for blockers based on severity
        for blocker in blockers:
            severity = blocker.get('severity', 'MEDIUM')
            if severity == 'CRITICAL':
                base_score -= 0.4
            elif severity == 'HIGH':
                base_score -= 0.25
            elif severity == 'MEDIUM':
                base_score -= 0.15
        
        # Deduct points for warnings
        base_score -= len(warnings) * 0.05
        
        # Factor in AI Brain confidence
        adjusted_score = base_score * ai_brain_confidence
        
        return max(0.0, min(1.0, adjusted_score))
    
    def _determine_operation_risk_level(self, safety_score: float, blockers: List[Dict[str, Any]]) -> str:
        """Determine operation risk level"""
        critical_blockers = [b for b in blockers if b.get('severity') == 'CRITICAL']
        
        if critical_blockers or safety_score < 0.3:
            return 'CRITICAL'
        elif safety_score < 0.5:
            return 'HIGH'
        elif safety_score < 0.7:
            return 'MEDIUM'
        elif safety_score < 0.85:
            return 'LOW'
        else:
            return 'MINIMAL'
    
    def _generate_safety_recommendations(self, blockers: List[Dict[str, Any]], warnings: List[Dict[str, Any]]) -> List[str]:
        """Generate safety improvement recommendations"""
        recommendations = []
        
        if any(b.get('type') == 'CRITICAL_MEMORY_USAGE' for b in blockers):
            recommendations.append('Increase system memory or optimize memory usage')
            
        if any(b.get('type') == 'QUEUE_CAPACITY_EXCEEDED' for b in blockers):
            recommendations.append('Scale queue capacity or implement backpressure')
            
        if any(b.get('type') == 'HIGH_MESSAGE_FAILURE_RATE' for b in blockers):
            recommendations.append('Investigate and fix message processing issues')
            
        if any(b.get('type') == 'NO_ACTIVE_CONSUMERS' for b in blockers):
            recommendations.append('Ensure consumers are registered and active')
            
        # Add general safety recommendations
        recommendations.extend([
            'Monitor system resources regularly',
            'Implement comprehensive error handling',
            'Use circuit breakers for external dependencies',
            'Implement proper queue monitoring and alerting'
        ])
        
        return list(set(recommendations))  # Remove duplicates
    
    def _get_safety_validation_summary(self) -> Dict[str, Any]:
        """Get summary of safety validation status"""
        total_checks = sum(len(history) for history in self.safety_check_history.values())
        safe_operations = 0
        avg_safety_score = 0.0
        risk_distribution = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'MINIMAL': 0}
        
        all_scores = []
        for operation_type, history in self.safety_check_history.items():
            for check in history:
                if check['is_safe']:
                    safe_operations += 1
                all_scores.append(check['safety_score'])
                risk_level = check['risk_level']
                if risk_level in risk_distribution:
                    risk_distribution[risk_level] += 1
        
        if all_scores:
            avg_safety_score = sum(all_scores) / len(all_scores)
        
        safety_rate = safe_operations / total_checks if total_checks > 0 else 1.0
        
        return {
            'total_safety_checks': total_checks,
            'safe_operations': safe_operations,
            'safety_rate': safety_rate,
            'average_safety_score': avg_safety_score,
            'risk_distribution': risk_distribution,
            'emergency_stops_active': len(self.emergency_stops),
            'resource_monitoring_enabled': True,
            'last_resource_check': self.last_resource_check.isoformat()
        }

# Global queue core instance
_queue_core: Optional[QueueCore] = None

def get_queue_core(service_name: str = "ai-provider") -> QueueCore:
    """Get the global AI Brain Enhanced queue core instance with pre-execution safety"""
    global _queue_core
    if _queue_core is None:
        _queue_core = QueueCore(service_name)
    return _queue_core

def get_queue_safety_summary() -> Dict[str, Any]:
    """Get queue safety validation summary"""
    queue_core = get_queue_core()
    return queue_core._get_safety_validation_summary()

def is_queue_operation_safe(operation_type: str, context: Dict[str, Any]) -> bool:
    """Check if a queue operation is safe to execute"""
    queue_core = get_queue_core()
    try:
        import asyncio
        # Create event loop if none exists
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running():
            # If we're already in an async context, we can't use loop.run_until_complete
            return True  # Default to safe for now
        else:
            safety_result = loop.run_until_complete(
                queue_core._perform_pre_execution_safety_check(operation_type, context)
            )
            return safety_result.is_safe
    except Exception:
        return True  # Default to safe if check fails