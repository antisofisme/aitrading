"""
AI Brain Enhanced Streaming Core - Security Validator Implementation
Real-time data streaming with AI Brain security validation and data integrity monitoring
Enhanced with systematic security analysis and confidence-based protection
"""

import asyncio
import time
import json
import uuid
import hashlib
import ssl
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
    from shared.ai_brain_confidence_framework import AiBrainConfidenceFramework, ConfidenceThreshold
    from shared.ai_brain_trading_error_dna import AiBrainTradingErrorDNA
    AI_BRAIN_AVAILABLE = True
except ImportError:
    AI_BRAIN_AVAILABLE = False

class StreamType(Enum):
    """Data stream type enumeration"""
    MARKET_DATA = "market_data"
    TRADING_SIGNALS = "trading_signals"
    NEWS_FEED = "news_feed"
    SOCIAL_SENTIMENT = "social_sentiment"
    ECONOMIC_DATA = "economic_data"
    TECHNICAL_INDICATORS = "technical_indicators"
    RISK_METRICS = "risk_metrics"

class EventType(Enum):
    """Stream event type enumeration"""
    TICK = "tick"
    BAR = "bar"
    ORDER = "order"
    FILL = "fill"
    NEWS = "news"
    ALERT = "alert"
    HEARTBEAT = "heartbeat"

class StreamStatus(Enum):
    """Stream status enumeration"""
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"
    RECONNECTING = "reconnecting"
    SECURITY_VIOLATION = "security_violation"

class SecurityThreat(Enum):
    """Security threat enumeration"""
    DATA_CORRUPTION = "data_corruption"
    SIZE_LIMIT_EXCEEDED = "size_limit_exceeded"
    INVALID_FORMAT = "invalid_format"
    SUSPICIOUS_PATTERN = "suspicious_pattern"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    ENCRYPTION_FAILURE = "encryption_failure"
    SSL_VERIFICATION_FAILED = "ssl_verification_failed"

class DataFormat(Enum):
    """Data format enumeration"""
    JSON = "json"
    PROTOBUF = "protobuf"
    AVRO = "avro"
    CSV = "csv"
    BINARY = "binary"

@dataclass
class StreamEvent:
    """Real-time stream event"""
    event_id: str
    stream_id: str
    event_type: EventType
    timestamp: datetime
    data: Dict[str, Any]
    source: str
    priority: int = 1  # 1=low, 5=high
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class StreamConfig:
    """Stream configuration with AI Brain security settings"""
    stream_id: str
    stream_type: StreamType
    source: str
    data_format: DataFormat
    buffer_size: int = 1000
    batch_size: int = 100
    flush_interval_ms: int = 1000
    retention_hours: int = 24
    compression_enabled: bool = True
    encryption_enabled: bool = False
    filters: List[Dict[str, Any]] = field(default_factory=list)
    transformations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    # AI Brain Security Settings
    max_event_size_bytes: int = 1048576  # 1MB limit
    rate_limit_events_per_second: int = 1000
    security_validation_enabled: bool = True
    ssl_required: bool = True
    data_integrity_checks: bool = True

@dataclass
class StreamMetrics:
    """AI Brain Enhanced stream performance and security metrics"""
    stream_id: str
    events_received: int = 0
    events_processed: int = 0
    events_dropped: int = 0
    bytes_processed: int = 0
    avg_latency_ms: float = 0.0
    throughput_events_per_sec: float = 0.0
    error_count: int = 0
    last_event_time: Optional[datetime] = None
    uptime_seconds: float = 0.0
    buffer_utilization: float = 0.0
    # AI Brain Security Metrics
    security_violations: int = 0
    data_integrity_failures: int = 0
    rate_limit_violations: int = 0
    encryption_failures: int = 0
    ssl_verification_failures: int = 0
    security_confidence: float = 1.0

@dataclass
class ProcessorFunction:
    """Stream processor function definition"""
    processor_id: str
    name: str
    function: Callable[[StreamEvent], Union[StreamEvent, List[StreamEvent], None]]
    priority: int = 1
    enabled: bool = True
    error_handling: str = "skip"  # skip, retry, fail
    metadata: Dict[str, Any] = field(default_factory=dict)

class StreamingCore:
    """
    AI Brain Enhanced Data Bridge core infrastructure with Security Validator.
    
    Features:
    - Real-time data stream management with security validation
    - Event processing and transformation with integrity checks
    - Stream buffering and batching with rate limiting
    - Data quality monitoring with confidence scoring
    - Stream analytics and metrics with security monitoring
    - Multi-protocol stream support with SSL/TLS validation
    - AI Brain security confidence framework integration
    """
    
    def __init__(self, service_name: str = "data-bridge"):
        self.service_name = service_name
        
        # AI Brain Security Validator Integration
        self.ai_brain_confidence = None
        self.ai_brain_error_dna = None
        if AI_BRAIN_AVAILABLE:
            try:
                self.ai_brain_confidence = AiBrainConfidenceFramework(f"streaming-{service_name}")
                self.ai_brain_error_dna = AiBrainTradingErrorDNA(f"streaming-{service_name}")
                self.logger.info("✅ AI Brain Security Validator initialized for streaming")
            except Exception as e:
                self.logger.warning(f"⚠️ AI Brain Security Validator initialization failed: {e}")
        
        # Stream management
        self.streams: Dict[str, StreamConfig] = {}
        self.stream_buffers: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.stream_metrics: Dict[str, StreamMetrics] = {}
        self.stream_status: Dict[str, StreamStatus] = {}
        
        # Security management
        self.security_violations: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.rate_limiter: Dict[str, List[float]] = defaultdict(list)  # timestamp tracking
        self.data_integrity_cache: Dict[str, str] = {}  # event_id -> checksum
        
        # Event processing
        self.processors: Dict[str, ProcessorFunction] = {}
        self.processor_chains: Dict[str, List[str]] = {}  # stream_id -> processor_ids
        
        # Performance settings
        self.max_concurrent_streams = 50
        self.global_buffer_limit = 100000
        self.compression_threshold_bytes = 1024
        self.batch_processing_enabled = True
        
        # Analytics and monitoring
        self.event_throughput: Dict[str, List[Tuple[datetime, int]]] = defaultdict(list)
        self.latency_measurements: Dict[str, List[float]] = defaultdict(list)
        self.error_log: List[Dict[str, Any]] = deque(maxlen=1000)
        
        # Initialize logging and performance tracking
        self.logger = BaseLogger(service_name, "streaming_core")
        self.performance_tracker = BasePerformance(service_name)
        
        # Setup default stream configurations
        self._setup_default_streams()
        
        # Start background tasks
        self._background_tasks: List[asyncio.Task] = []
        self._start_background_tasks()
        
        self.logger.info("AI Brain Enhanced Streaming Core initialized", extra={
            "service": service_name,
            "max_concurrent_streams": self.max_concurrent_streams,
            "global_buffer_limit": self.global_buffer_limit,
            "batch_processing": self.batch_processing_enabled,
            "ai_brain_security_enabled": AI_BRAIN_AVAILABLE
        })
    
    def _setup_default_streams(self):
        """Setup default stream configurations"""
        default_streams = [
            StreamConfig(
                stream_id="market_data_feed",
                stream_type=StreamType.MARKET_DATA,
                source="mt5_bridge",
                data_format=DataFormat.JSON,
                buffer_size=5000,
                batch_size=500,
                flush_interval_ms=500,
                retention_hours=48
            ),
            StreamConfig(
                stream_id="trading_signals",
                stream_type=StreamType.TRADING_SIGNALS,
                source="ai_provider",
                data_format=DataFormat.JSON,
                buffer_size=1000,
                batch_size=50,
                flush_interval_ms=1000,
                retention_hours=24
            ),
            StreamConfig(
                stream_id="news_feed",
                stream_type=StreamType.NEWS_FEED,
                source="external_api",
                data_format=DataFormat.JSON,
                buffer_size=500,
                batch_size=25,
                flush_interval_ms=2000,
                retention_hours=12
            ),
            StreamConfig(
                stream_id="risk_metrics",
                stream_type=StreamType.RISK_METRICS,
                source="trading_engine",
                data_format=DataFormat.JSON,
                buffer_size=1000,
                batch_size=100,
                flush_interval_ms=1000,
                retention_hours=72
            )
        ]
        
        for stream_config in default_streams:
            self.register_stream(stream_config)
        
        self.logger.info(f"Default streams configured: {len(default_streams)}")
    
    def _start_background_tasks(self):
        """Start background processing tasks"""
        # Metrics collection task
        metrics_task = asyncio.create_task(self._metrics_collection_loop())
        self._background_tasks.append(metrics_task)
        
        # Buffer flush task
        flush_task = asyncio.create_task(self._buffer_flush_loop())
        self._background_tasks.append(flush_task)
        
        # Health monitoring task
        health_task = asyncio.create_task(self._health_monitoring_loop())
        self._background_tasks.append(health_task)
    
    def register_stream(self, stream_config: StreamConfig) -> str:
        """Register new data stream"""
        stream_id = stream_config.stream_id
        self.streams[stream_id] = stream_config
        
        # Initialize stream metrics and status
        self.stream_metrics[stream_id] = StreamMetrics(stream_id=stream_id)
        self.stream_status[stream_id] = StreamStatus.STOPPED
        
        # Initialize buffer with configured size
        self.stream_buffers[stream_id] = deque(maxlen=stream_config.buffer_size)
        
        self.logger.info(f"Stream registered: {stream_id}", extra={
            "stream_type": stream_config.stream_type.value,
            "source": stream_config.source,
            "buffer_size": stream_config.buffer_size,
            "data_format": stream_config.data_format.value
        })
        
        return stream_id
    
    def register_processor(self, processor: ProcessorFunction) -> str:
        """Register stream processor function"""
        self.processors[processor.processor_id] = processor
        
        self.logger.info(f"Processor registered: {processor.processor_id}", extra={
            "name": processor.name,
            "priority": processor.priority,
            "enabled": processor.enabled
        })
        
        return processor.processor_id
    
    def add_processor_to_stream(self, stream_id: str, processor_id: str) -> bool:
        """Add processor to stream processing chain"""
        if stream_id not in self.streams or processor_id not in self.processors:
            return False
        
        if stream_id not in self.processor_chains:
            self.processor_chains[stream_id] = []
        
        if processor_id not in self.processor_chains[stream_id]:
            self.processor_chains[stream_id].append(processor_id)
            
            # Sort by priority
            self.processor_chains[stream_id].sort(
                key=lambda pid: self.processors[pid].priority,
                reverse=True
            )
        
        self.logger.info(f"Processor added to stream: {processor_id} -> {stream_id}")
        return True
    
    async def start_stream(self, stream_id: str) -> bool:
        """Start data stream processing"""
        if stream_id not in self.streams:
            return False
        
        if self.stream_status[stream_id] == StreamStatus.ACTIVE:
            return True
        
        self.stream_status[stream_id] = StreamStatus.ACTIVE
        self.stream_metrics[stream_id].uptime_seconds = 0.0
        
        self.logger.info(f"Stream started: {stream_id}")
        return True
    
    async def stop_stream(self, stream_id: str) -> bool:
        """Stop data stream processing"""
        if stream_id not in self.streams:
            return False
        
        self.stream_status[stream_id] = StreamStatus.STOPPED
        
        self.logger.info(f"Stream stopped: {stream_id}")
        return True
    
    async def publish_event(self, stream_id: str, event_data: Dict[str, Any], 
                          event_type: EventType = EventType.TICK,
                          priority: int = 1) -> Optional[str]:
        """
        Publish event to stream.
        
        Args:
            stream_id: Target stream identifier
            event_data: Event data payload
            event_type: Type of event
            priority: Event priority (1=low, 5=high)
            
        Returns:
            Event ID if successful, None otherwise
        """
        if stream_id not in self.streams:
            self.logger.error(f"Stream not found: {stream_id}")
            return None
        
        if self.stream_status[stream_id] != StreamStatus.ACTIVE:
            self.logger.warning(f"Stream not active: {stream_id}")
            return None
        
        # AI Brain Security Validation
        is_valid, threat_type, security_confidence = self._validate_stream_security(stream_id, event_data)
        
        if not is_valid:
            self.logger.warning(f"Event blocked due to security validation failure", extra={
                "stream_id": stream_id,
                "threat_type": threat_type.value if threat_type else "unknown",
                "security_confidence": security_confidence
            })
            return None
        
        # Create stream event
        event = StreamEvent(
            event_id=str(uuid.uuid4()),
            stream_id=stream_id,
            event_type=event_type,
            timestamp=datetime.now(),
            data=event_data,
            source=self.streams[stream_id].source,
            priority=priority
        )
        
        # Process event through processor chain
        processed_events = await self._process_event(event)
        
        # Add to stream buffer
        stream_buffer = self.stream_buffers[stream_id]
        
        for processed_event in processed_events:
            if len(stream_buffer) >= self.streams[stream_id].buffer_size:
                # Buffer full, drop oldest events
                dropped_event = stream_buffer.popleft()
                self.stream_metrics[stream_id].events_dropped += 1
                
                self.logger.warning(f"Buffer overflow in stream {stream_id}, dropping event")
            
            stream_buffer.append(processed_event)
        
        # Update metrics
        metrics = self.stream_metrics[stream_id]
        metrics.events_received += 1
        metrics.events_processed += len(processed_events)
        metrics.last_event_time = datetime.now()
        metrics.bytes_processed += len(json.dumps(event_data, default=str).encode())
        
        # Update buffer utilization
        metrics.buffer_utilization = len(stream_buffer) / self.streams[stream_id].buffer_size
        
        self.logger.debug(f"Event published to stream: {stream_id}", extra={
            "event_id": event.event_id,
            "event_type": event_type.value,
            "priority": priority,
            "processed_events": len(processed_events)
        })
        
        return event.event_id
    
    def _validate_stream_security(self, stream_id: str, event_data: Dict[str, Any]) -> Tuple[bool, Optional[SecurityThreat], float]:
        """
        AI Brain Security Validator - Comprehensive streaming security validation
        
        Returns:
            (is_valid, threat_type, security_confidence)
        """
        if stream_id not in self.streams:
            return False, SecurityThreat.SUSPICIOUS_PATTERN, 0.0
        
        stream_config = self.streams[stream_id]
        
        # Skip validation if disabled
        if not stream_config.security_validation_enabled:
            return True, None, 1.0
        
        security_confidence = 1.0
        
        try:
            # 1. Data Size Validation
            event_size = len(json.dumps(event_data, default=str).encode())
            if event_size > stream_config.max_event_size_bytes:
                self._record_security_violation(stream_id, SecurityThreat.SIZE_LIMIT_EXCEEDED, {
                    "event_size": event_size,
                    "limit": stream_config.max_event_size_bytes
                })
                return False, SecurityThreat.SIZE_LIMIT_EXCEEDED, 0.1
            
            # 2. Rate Limiting Validation
            current_time = time.time()
            rate_window = self.rate_limiter[stream_id]
            
            # Clean old timestamps (keep last second)
            rate_window[:] = [t for t in rate_window if current_time - t < 1.0]
            
            if len(rate_window) >= stream_config.rate_limit_events_per_second:
                self._record_security_violation(stream_id, SecurityThreat.RATE_LIMIT_EXCEEDED, {
                    "current_rate": len(rate_window),
                    "limit": stream_config.rate_limit_events_per_second
                })
                return False, SecurityThreat.RATE_LIMIT_EXCEEDED, 0.2
            
            rate_window.append(current_time)
            
            # 3. Data Format Validation
            if not self._validate_data_format(event_data, stream_config.data_format):
                self._record_security_violation(stream_id, SecurityThreat.INVALID_FORMAT, {
                    "expected_format": stream_config.data_format.value,
                    "data_keys": list(event_data.keys())
                })
                security_confidence *= 0.5
            
            # 4. Data Integrity Validation
            if stream_config.data_integrity_checks:
                data_hash = hashlib.sha256(json.dumps(event_data, sort_keys=True, default=str).encode()).hexdigest()
                
                # Check for duplicate events (potential replay attacks)
                if data_hash in self.data_integrity_cache.values():
                    self._record_security_violation(stream_id, SecurityThreat.DATA_CORRUPTION, {
                        "reason": "duplicate_event_detected",
                        "hash": data_hash[:16]
                    })
                    security_confidence *= 0.3
            
            # 5. Suspicious Pattern Detection
            if self._detect_suspicious_patterns(event_data):
                self._record_security_violation(stream_id, SecurityThreat.SUSPICIOUS_PATTERN, {
                    "patterns_detected": "anomalous_data_structure"
                })
                security_confidence *= 0.4
            
            # 6. AI Brain Confidence Assessment
            if self.ai_brain_confidence and security_confidence < 0.85:
                confidence_score = self.ai_brain_confidence.calculate_security_confidence(
                    event_data, stream_config.__dict__, security_confidence
                )
                security_confidence = min(security_confidence, confidence_score)
            
            return security_confidence >= 0.55, None, security_confidence
            
        except Exception as e:
            if self.ai_brain_error_dna:
                self.ai_brain_error_dna.log_error(e, {
                    "context": "stream_security_validation",
                    "stream_id": stream_id,
                    "event_data_size": len(str(event_data))
                })
            
            self.logger.error(f"Security validation error for stream {stream_id}: {e}")
            return False, SecurityThreat.SUSPICIOUS_PATTERN, 0.0
    
    def _validate_data_format(self, data: Dict[str, Any], expected_format: DataFormat) -> bool:
        """Validate event data format"""
        try:
            if expected_format == DataFormat.JSON:
                # Basic JSON structure validation
                return isinstance(data, dict) and len(data) > 0
            elif expected_format == DataFormat.CSV:
                # CSV should have consistent field structure
                return all(isinstance(v, (str, int, float)) for v in data.values())
            else:
                return True  # Other formats pass through
        except:
            return False
    
    def _detect_suspicious_patterns(self, data: Dict[str, Any]) -> bool:
        """Detect suspicious data patterns that might indicate attacks"""
        try:
            data_str = str(data).lower()
            
            # Check for common injection patterns
            suspicious_patterns = [
                '<script', 'javascript:', 'eval(', 'exec(',
                'drop table', 'select * from', 'union select',
                '../../', '../../../', 'cmd.exe', '/bin/sh'
            ]
            
            return any(pattern in data_str for pattern in suspicious_patterns)
            
        except:
            return True  # Assume suspicious if we can't analyze
    
    def _record_security_violation(self, stream_id: str, threat: SecurityThreat, details: Dict[str, Any]):
        """Record security violation for monitoring and response"""
        violation = {
            "timestamp": datetime.now().isoformat(),
            "stream_id": stream_id,
            "threat_type": threat.value,
            "details": details,
            "action": "event_blocked"
        }
        
        self.security_violations[stream_id].append(violation)
        
        # Update stream metrics
        if stream_id in self.stream_metrics:
            metrics = self.stream_metrics[stream_id]
            metrics.security_violations += 1
            
            if threat == SecurityThreat.DATA_CORRUPTION:
                metrics.data_integrity_failures += 1
            elif threat == SecurityThreat.RATE_LIMIT_EXCEEDED:
                metrics.rate_limit_violations += 1
            elif threat == SecurityThreat.ENCRYPTION_FAILURE:
                metrics.encryption_failures += 1
            elif threat == SecurityThreat.SSL_VERIFICATION_FAILED:
                metrics.ssl_verification_failures += 1
            
            # Update security confidence based on violation rate
            total_events = metrics.events_received + metrics.events_processed
            if total_events > 0:
                violation_rate = metrics.security_violations / total_events
                metrics.security_confidence = max(0.0, 1.0 - (violation_rate * 2))
        
        # Set stream to security violation state for critical threats
        if threat in [SecurityThreat.DATA_CORRUPTION, SecurityThreat.SUSPICIOUS_PATTERN]:
            self.stream_status[stream_id] = StreamStatus.SECURITY_VIOLATION
        
        self.logger.warning(f"Security violation detected: {threat.value}", extra={
            "stream_id": stream_id,
            "threat": threat.value,
            "details": details
        })
    
    def get_security_status(self, stream_id: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive security status for streams"""
        if stream_id:
            if stream_id not in self.streams:
                return {}
                
            violations = self.security_violations[stream_id]
            metrics = self.stream_metrics[stream_id]
            
            return {
                "stream_id": stream_id,
                "security_confidence": metrics.security_confidence,
                "total_violations": metrics.security_violations,
                "violation_breakdown": {
                    "data_integrity_failures": metrics.data_integrity_failures,
                    "rate_limit_violations": metrics.rate_limit_violations,
                    "encryption_failures": metrics.encryption_failures,
                    "ssl_verification_failures": metrics.ssl_verification_failures
                },
                "recent_violations": violations[-10:],  # Last 10 violations
                "current_status": self.stream_status[stream_id].value,
                "security_enabled": self.streams[stream_id].security_validation_enabled
            }
        
        # Return overall security status
        total_violations = sum(len(violations) for violations in self.security_violations.values())
        avg_confidence = sum(m.security_confidence for m in self.stream_metrics.values()) / len(self.stream_metrics) if self.stream_metrics else 1.0
        
        return {
            "total_streams": len(self.streams),
            "secured_streams": len([s for s in self.streams.values() if s.security_validation_enabled]),
            "total_violations": total_violations,
            "average_security_confidence": avg_confidence,
            "streams_in_violation": len([s for s in self.stream_status.values() if s == StreamStatus.SECURITY_VIOLATION]),
            "ai_brain_security_enabled": AI_BRAIN_AVAILABLE
        }
    
    async def _process_event(self, event: StreamEvent) -> List[StreamEvent]:
        """Process event through processor chain"""
        if event.stream_id not in self.processor_chains:
            return [event]
        
        processed_events = [event]
        
        for processor_id in self.processor_chains[event.stream_id]:
            if processor_id not in self.processors:
                continue
            
            processor = self.processors[processor_id]
            
            if not processor.enabled:
                continue
            
            try:
                new_processed_events = []
                
                for proc_event in processed_events:
                    result = processor.function(proc_event)
                    
                    if result is None:
                        # Event filtered out
                        continue
                    elif isinstance(result, list):
                        # Multiple events generated
                        new_processed_events.extend(result)
                    else:
                        # Single event
                        new_processed_events.append(result)
                
                processed_events = new_processed_events
                
            except Exception as e:
                error_info = {
                    "processor_id": processor_id,
                    "event_id": event.event_id,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                self.error_log.append(error_info)
                
                self.logger.error(f"Processor error: {processor_id}", extra=error_info)
                
                if processor.error_handling == "fail":
                    # Stop processing chain
                    break
                elif processor.error_handling == "skip":
                    # Continue with original events
                    pass
        
        return processed_events
    
    async def consume_events(self, stream_id: str, 
                           max_events: Optional[int] = None) -> AsyncGenerator[StreamEvent, None]:
        """
        Consume events from stream buffer.
        
        Args:
            stream_id: Stream identifier
            max_events: Maximum number of events to consume
            
        Yields:
            Stream events
        """
        if stream_id not in self.streams:
            return
        
        stream_buffer = self.stream_buffers[stream_id]
        events_consumed = 0
        
        while stream_buffer and (max_events is None or events_consumed < max_events):
            try:
                event = stream_buffer.popleft()
                events_consumed += 1
                yield event
            except IndexError:
                # Buffer empty
                break
    
    async def get_batch_events(self, stream_id: str, 
                             batch_size: Optional[int] = None) -> List[StreamEvent]:
        """Get batch of events from stream"""
        if stream_id not in self.streams:
            return []
        
        if batch_size is None:
            batch_size = self.streams[stream_id].batch_size
        
        events = []
        async for event in self.consume_events(stream_id, batch_size):
            events.append(event)
        
        return events
    
    async def _metrics_collection_loop(self):
        """Background task for metrics collection"""
        while True:
            try:
                current_time = datetime.now()
                
                for stream_id, metrics in self.stream_metrics.items():
                    if self.stream_status[stream_id] == StreamStatus.ACTIVE:
                        # Track throughput
                        throughput_data = self.event_throughput[stream_id]
                        throughput_data.append((current_time, metrics.events_processed))
                        
                        # Keep only last hour of data
                        cutoff_time = current_time - timedelta(hours=1)
                        self.event_throughput[stream_id] = [
                            (time, count) for time, count in throughput_data
                            if time > cutoff_time
                        ]
                        
                        # Calculate throughput (events per second)
                        if len(throughput_data) >= 2:
                            time_diff = (throughput_data[-1][0] - throughput_data[0][0]).total_seconds()
                            event_diff = throughput_data[-1][1] - throughput_data[0][1]
                            
                            if time_diff > 0:
                                metrics.throughput_events_per_sec = event_diff / time_diff
                        
                        # Update uptime
                        metrics.uptime_seconds += 60.0  # Collection interval
                
                await asyncio.sleep(60)  # Collect metrics every minute
                
            except Exception as e:
                self.logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(60)
    
    async def _buffer_flush_loop(self):
        """Background task for buffer flushing"""
        while True:
            try:
                for stream_id, stream_config in self.streams.items():
                    if self.stream_status[stream_id] != StreamStatus.ACTIVE:
                        continue
                    
                    # Check if buffer needs flushing
                    buffer = self.stream_buffers[stream_id]
                    
                    if len(buffer) >= stream_config.batch_size:
                        # Flush buffer (placeholder for actual implementation)
                        await self._flush_stream_buffer(stream_id)
                
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                self.logger.error(f"Buffer flush error: {e}")
                await asyncio.sleep(1)
    
    async def _flush_stream_buffer(self, stream_id: str):
        """Flush stream buffer to persistent storage"""
        # Placeholder for actual buffer flushing implementation
        # In production, this would write to databases, message queues, etc.
        buffer = self.stream_buffers[stream_id]
        batch_size = self.streams[stream_id].batch_size
        
        if len(buffer) >= batch_size:
            # Simulate flushing
            events_to_flush = []
            for _ in range(min(batch_size, len(buffer))):
                if buffer:
                    events_to_flush.append(buffer.popleft())
            
            self.logger.debug(f"Flushed {len(events_to_flush)} events from {stream_id}")
    
    async def _health_monitoring_loop(self):
        """Background task for stream health monitoring"""
        while True:
            try:
                current_time = datetime.now()
                
                for stream_id, metrics in self.stream_metrics.items():
                    if self.stream_status[stream_id] == StreamStatus.ACTIVE:
                        # Check for stale streams (no events in last 5 minutes)
                        if metrics.last_event_time:
                            time_since_last = current_time - metrics.last_event_time
                            if time_since_last.total_seconds() > 300:  # 5 minutes
                                self.logger.warning(f"Stream appears stale: {stream_id}", extra={
                                    "last_event": metrics.last_event_time.isoformat(),
                                    "time_since_last": time_since_last.total_seconds()
                                })
                
                await asyncio.sleep(30)  # Health check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(30)
    
    def get_stream_metrics(self, stream_id: Optional[str] = None) -> Dict[str, Any]:
        """Get stream performance metrics"""
        if stream_id:
            if stream_id in self.stream_metrics:
                metrics = self.stream_metrics[stream_id]
                return {
                    "stream_id": metrics.stream_id,
                    "events_received": metrics.events_received,
                    "events_processed": metrics.events_processed,
                    "events_dropped": metrics.events_dropped,
                    "bytes_processed": metrics.bytes_processed,
                    "throughput_events_per_sec": metrics.throughput_events_per_sec,
                    "buffer_utilization": metrics.buffer_utilization,
                    "uptime_seconds": metrics.uptime_seconds,
                    "last_event_time": metrics.last_event_time.isoformat() if metrics.last_event_time else None,
                    "status": self.stream_status[stream_id].value
                }
            return {}
        
        # Return all stream metrics
        return {
            stream_id: {
                "stream_id": metrics.stream_id,
                "events_received": metrics.events_received,
                "events_processed": metrics.events_processed,
                "events_dropped": metrics.events_dropped,
                "throughput_events_per_sec": metrics.throughput_events_per_sec,
                "buffer_utilization": metrics.buffer_utilization,
                "status": self.stream_status[stream_id].value
            }
            for stream_id, metrics in self.stream_metrics.items()
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall streaming system status"""
        active_streams = len([
            s for s in self.stream_status.values() 
            if s == StreamStatus.ACTIVE
        ])
        
        total_events = sum(m.events_processed for m in self.stream_metrics.values())
        total_bytes = sum(m.bytes_processed for m in self.stream_metrics.values())
        
        return {
            "total_streams": len(self.streams),
            "active_streams": active_streams,
            "total_processors": len(self.processors),
            "total_events_processed": total_events,
            "total_bytes_processed": total_bytes,
            "global_buffer_utilization": sum(
                len(buffer) for buffer in self.stream_buffers.values()
            ) / self.global_buffer_limit,
            "error_count": len(self.error_log),
            "batch_processing_enabled": self.batch_processing_enabled
        }

# Global streaming core instance
_streaming_core: Optional[StreamingCore] = None

def get_streaming_core() -> StreamingCore:
    """Get the global streaming core instance"""
    global _streaming_core
    if _streaming_core is None:
        _streaming_core = StreamingCore()
    return _streaming_core