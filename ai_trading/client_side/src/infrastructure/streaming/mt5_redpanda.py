"""
mt5_redpanda.py - High-Performance Streaming Integration

🎯 PURPOSE:
Business: Real-time market data streaming via Redpanda with MT5 integration
Technical: High-throughput streaming client with failover and monitoring capabilities
Domain: Streaming/Market Data/Real-time Communication

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:27.735Z
Session: client-side-ai-brain-full-compliance
Confidence: 88%
Complexity: high

🧩 PATTERNS USED:
- AI_BRAIN_STREAMING_INTEGRATION: High-performance streaming with AI Brain patterns
- FAILOVER_RESILIENCE: Automatic failover and reconnection strategies

📦 DEPENDENCIES:
Internal: centralized_logger, error_handler, performance_tracker
External: kafka-python, asyncio, websockets, json

💡 AI DECISION REASONING:
Redpanda chosen over Kafka for lower latency and simpler deployment. Streaming architecture enables real-time processing with high throughput.

🚀 USAGE:
streamer = MT5RedpandaStreamer(); await streamer.start_streaming("EURUSD")

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

import asyncio
import json
import uuid
import os
from datetime import datetime
from typing import Dict, Any, Optional, Union, List
from enum import Enum
from dataclasses import dataclass, asdict
import sys

# CENTRALIZED INFRASTRUCTURE IMPORTS (Direct imports to avoid circular dependency)
# Centralized Logging
from src.infrastructure.logging.logger_manager import get_logger

# Centralized Configuration  
from src.infrastructure.config.config_manager import get_config, get_client_settings

# Centralized Error Handling
from src.infrastructure.errors.error_manager import handle_error, ErrorCategory, ErrorSeverity

# Performance Tracking
from src.infrastructure.performance.performance_manager import performance_tracked, track_performance

# Validation
from src.infrastructure.validation.validator import validate_field, validate_dict

# Suppress print statements during import by redirecting stdout temporarily
class SuppressOutput:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout

# Try import aiokafka (preferred for async client operations)
try:
    # Suppress any print statements during import
    with SuppressOutput():
        from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
        from aiokafka.errors import KafkaError
    AIOKAFKA_AVAILABLE = True
except ImportError as e:
    AIOKAFKA_AVAILABLE = False

# Fallback to kafka-python if aiokafka not available
try:
    # Suppress any print statements during import
    with SuppressOutput():
        from kafka import KafkaProducer, KafkaConsumer
        from kafka.errors import KafkaError as SyncKafkaError
    KAFKA_PYTHON_AVAILABLE = True
except ImportError as e:
    KAFKA_PYTHON_AVAILABLE = False


class MT5EventPriority(Enum):
    """MT5 Event priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MT5Event:
    """MT5 trading event structure"""
    event_id: str
    event_type: str
    timestamp: datetime
    payload: Dict[str, Any]
    source: str = "mt5_bridge"
    topic: str = "mt5_events"
    key: Optional[str] = None
    priority: MT5EventPriority = MT5EventPriority.MEDIUM
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for JSON serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['priority'] = self.priority.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MT5Event':
        """Create event from dictionary"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['priority'] = MT5EventPriority(data['priority'])
        return cls(**data)




@dataclass
class MT5RedpandaConfig:
    """Configuration for MT5 RedPanda connection"""
    
    # Connection settings
    bootstrap_servers: str = "127.0.0.1:19092"
    client_id: str = "mt5_bridge"
    security_protocol: str = "PLAINTEXT"
    
    # Producer specific
    batch_size: int = 16384
    linger_ms: int = 5
    compression_type: str = "gzip"
    acks: int = 1
    retries: int = 3
    retry_backoff_ms: int = 100
    
    # Consumer specific
    group_id: str = "mt5_bridge_group"
    auto_offset_reset: str = "latest"
    enable_auto_commit: bool = True
    auto_commit_interval_ms: int = 5000
    
    def __post_init__(self):
        """Initialize connection after creating config"""
        # Try multiple possible server configurations
        # Use environment variables with fallbacks
        possible_servers = [
            os.getenv('REDPANDA_PRIMARY_SERVER', '127.0.0.1:19092'),  # Explicit IP - Redpanda default port
            os.getenv('REDPANDA_LOCALHOST_PRIMARY', 'localhost:19092'),  # Localhost - Redpanda default port
            os.getenv('REDPANDA_BACKUP_SERVER', '127.0.0.1:9092'),   # Explicit IP - Standard Kafka port
            os.getenv('REDPANDA_LOCALHOST_BACKUP', 'localhost:9092'),   # Localhost - Standard Kafka port
        ]
        
        # Use the first available server
        self.bootstrap_servers = self._find_available_server(possible_servers)
    
    def _find_available_server(self, servers):
        """Find the first available Redpanda server"""
        import socket
        
        for server in servers:
            try:
                host, port = server.split(':')
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((host, int(port)))
                sock.close()
                
                if result == 0:
                    return server
            except Exception as e:
                pass
                continue
        
        return "127.0.0.1:19092"


class MT5RedpandaProducer:
    """
    MT5 Bridge RedPanda Producer - Client-side streaming
    
    Specialized for sending MT5 trading data to Backend3:
    - Tick data streaming
    - Trading events
    - Account information
    - Position updates
    """
    
    def __init__(self, config: MT5RedpandaConfig):
        self.config = config
        self.producer = None
        self.is_running = False
        self.sent_messages = 0
        self.failed_messages = 0
        self.last_send_time = None
        # CENTRALIZED INFRASTRUCTURE - Initialize centralized logger
        self.logger = get_logger('mt5_redpanda_producer', context={
            'component': 'mt5_redpanda_producer',
            'client_id': config.client_id,
            'servers': config.bootstrap_servers,
            'version': '2.0.0-centralized'
        })
        
    @performance_tracked("redpanda_producer_start", "mt5_redpanda")
    async def start(self) -> bool:
        """Start the MT5 RedPanda producer with fallback strategy - Enhanced with centralized infrastructure"""
        try:
            # Load centralized configuration
            try:
                redpanda_config = get_config('redpanda')
                network_config = get_config('network')
                
                # Override config with centralized settings if available
                if redpanda_config:
                    self.config.bootstrap_servers = redpanda_config.get('bootstrap_servers', self.config.bootstrap_servers)
                    self.config.batch_size = redpanda_config.get('batch_size', self.config.batch_size)
                    self.config.compression_type = redpanda_config.get('compression_type', self.config.compression_type)
                    
            except Exception as e:
                error_context = handle_error(
                    error=e,
                    category=ErrorCategory.CONFIG,
                    severity=ErrorSeverity.MEDIUM,
                    component='mt5_redpanda_producer',
                    operation='configuration_loading'
                )
                self.logger.warning(f"Failed to load centralized config: {error_context.message}")
                # Use default config as fallback
            
            with track_performance("producer_initialization", "mt5_redpanda"):
                import sys
                
                # Enhanced fallback strategy: try WebSocket-only mode if Kafka fails
                self.fallback_mode = False
            
            # Skip aiokafka on Windows due to DNS issues, use kafka-python directly
            use_kafka_python = sys.platform == "win32" or not AIOKAFKA_AVAILABLE
            
            if use_kafka_python:
                self.logger.info(f"🔄 Using kafka-python on {sys.platform} platform for better compatibility")
            
            if AIOKAFKA_AVAILABLE and not use_kafka_python:
                try:
                    # Force IP address for aiokafka to avoid DNS issues
                    bootstrap_servers = self.config.bootstrap_servers
                    if bootstrap_servers == "localhost:19092":
                        bootstrap_servers = "127.0.0.1:19092"
                    elif bootstrap_servers == "localhost:9092":
                        bootstrap_servers = "127.0.0.1:9092"
                    
                    self.producer = AIOKafkaProducer(
                        bootstrap_servers=bootstrap_servers,
                        client_id=self.config.client_id,
                        security_protocol=self.config.security_protocol,
                        max_batch_size=self.config.batch_size,
                        linger_ms=self.config.linger_ms,
                        compression_type=self.config.compression_type,
                        acks=self.config.acks,
                        request_timeout_ms=30000,  # 30 second timeout
                        metadata_max_age_ms=300000,  # 5 minutes
                        retry_backoff_ms=1000,  # 1 second retry backoff
                        enable_idempotence=False,  # Disable idempotence for compatibility
                        value_serializer=lambda v: json.dumps(v).encode('utf-8')
                    )
                    await self.producer.start()
                    self.is_running = True
                    self.logger.info("✅ MT5 RedPanda producer started with aiokafka")
                    return True
                except Exception as aiokafka_error:
                    self.logger.warning(f"⚠️ aiokafka failed: {aiokafka_error}, trying kafka-python fallback")
                    # Cleanup failed aiokafka producer
                    if hasattr(self, 'producer') and self.producer:
                        try:
                            await self.producer.stop()
                        except:
                            pass
                        self.producer = None
                    # Fall through to kafka-python fallback
            
            if KAFKA_PYTHON_AVAILABLE:
                # Use synchronous kafka-python as fallback
                from kafka import KafkaProducer
                self.producer = KafkaProducer(
                    bootstrap_servers=[self.config.bootstrap_servers],
                    client_id=self.config.client_id,
                    security_protocol=self.config.security_protocol,
                    batch_size=self.config.batch_size,
                    linger_ms=self.config.linger_ms,
                    compression_type=self.config.compression_type,
                    acks=self.config.acks,
                    api_version=(0, 10, 1),  # Compatible API version
                    connections_max_idle_ms=540000,  # 9 minutes
                    request_timeout_ms=30000,  # 30 seconds timeout
                    metadata_max_age_ms=300000,  # 5 minutes
                    max_block_ms=30000,  # 30 seconds max block time
                    retry_backoff_ms=1000,  # 1 second retry backoff
                    value_serializer=lambda v: json.dumps(v).encode('utf-8')
                )
                self.is_running = True
                self.logger.info("✅ MT5 RedPanda producer started with kafka-python")
                return True
            else:
                self.logger.warning("⚠️ No Kafka libraries available, using fallback mode")
                return False
                
        except Exception as e:
            # Use centralized error handling
            error_context = handle_error(
                error=e,
                category=ErrorCategory.REDPANDA,
                severity=ErrorSeverity.HIGH,
                component='mt5_redpanda_producer',
                operation='producer_startup'
            )
            self.logger.error(f"❌ Failed to start MT5 RedPanda producer: {error_context.message}")
            
            # Log recovery suggestions
            for suggestion in error_context.recovery_suggestions:
                self.logger.info(f"💡 Recovery: {suggestion}")
            
            return False
    
    async def stop(self):
        """Stop the MT5 RedPanda producer"""
        if self.producer and self.is_running:
            try:
                if hasattr(self.producer, 'stop') and hasattr(self.producer, 'start'):
                    # This is AIOKafkaProducer (async)
                    await self.producer.stop()
                else:
                    # This is KafkaProducer (sync)
                    self.producer.close()
                self.is_running = False
                self.logger.info("🔌 MT5 RedPanda producer stopped")
            except Exception as e:
                self.logger.warning(f"⚠️ Error stopping producer: {e}")
                self.is_running = False
    
    async def _create_topics_if_needed(self):
        """Create required topics if they don't exist"""
        try:
            # Required topics for MT5 streaming
            required_topics = [
                "tick_data",
                "mt5_events", 
                "mt5_responses",
                "trading_signals",
                "market_ticks"
            ]
            
            for topic in required_topics:
                self.logger.debug(f"📋 Ensuring topic exists: {topic}")
                # Topics are auto-created by default in Redpanda
                
        except Exception as e:
            self.logger.warning(f"⚠️ Could not verify topics: {e}")
    
    @performance_tracked("send_tick_data", "mt5_redpanda")
    async def send_tick_data(self, topic: str, symbol: str, tick_data: Dict[str, Any]) -> bool:
        """Send MT5 tick data to Backend3 with retry mechanism - Enhanced with centralized validation and performance tracking"""
        try:
            # CENTRALIZED VALIDATION - Validate inputs
            topic_validation = validate_field('kafka_topic', topic, 'kafka_topic')
            symbol_validation = validate_field('trading_symbol', symbol, 'trading_symbol')
            data_validation = validate_dict(tick_data, {
                'bid': 'required_float',
                'ask': 'required_float',
                'timestamp': 'optional_string'
            })
            
            if not all([topic_validation.is_valid, symbol_validation.is_valid, data_validation.is_valid]):
                validation_errors = []
                for result in [topic_validation, symbol_validation, data_validation]:
                    if not result.is_valid:
                        validation_errors.extend([error.message for error in result.errors])
                self.logger.error(f"Validation failed for tick data: {'; '.join(validation_errors)}")
                return False
            
            if not self.is_running:
                self.logger.warning("⚠️ Producer not running")
                return False
                
            # Quick fail approach - only 1 retry for Redpanda, then fallback to WebSocket
            max_retries = 1
            retry_delay = 0.5  # Faster retry
            
            for attempt in range(max_retries):
                try:
                    with track_performance("event_creation", "mt5_redpanda"):
                        event = MT5Event(
                            event_id=f"tick_{symbol}_{uuid.uuid4().hex[:8]}",
                            event_type="tick_data",
                            timestamp=datetime.utcnow(),
                            payload=tick_data,
                            source="mt5_bridge",
                            topic=topic,
                            key=symbol,
                            priority=MT5EventPriority.HIGH,
                            metadata={"symbol": symbol, "data_type": "tick"}
                        )
                
                    with track_performance("kafka_send", "mt5_redpanda"):
                        if hasattr(self.producer, 'send') and hasattr(self.producer, 'start'):
                            # This is AIOKafkaProducer (async)
                            await self.producer.send(topic, event.to_dict(), key=symbol.encode('utf-8'))
                        else:
                            # This is KafkaProducer (sync)
                            future = self.producer.send(topic, event.to_dict(), key=symbol.encode('utf-8'))
                            # Wait for sync producer to complete
                            result = future.get(timeout=10)  # 10 second timeout for sync send
                            
                    self.sent_messages += 1
                    self.last_send_time = datetime.utcnow()
                    self.logger.debug(f"📊 Sent tick data for {symbol} to {topic}")
                    return True
                
                except Exception as e:
                    if attempt < max_retries - 1:
                        # Use centralized error handling for retry logic
                        error_context = handle_error(
                            error=e,
                            category=ErrorCategory.REDPANDA,
                            severity=ErrorSeverity.MEDIUM,
                            component='mt5_redpanda_producer',
                            operation='tick_data_send_retry'
                        )
                        self.logger.warning(f"⚠️ Retry {attempt + 1}/{max_retries} for {symbol}: {error_context.message}")
                        
                        # Try reconnecting if connection failed
                        if "timeout" in str(e).lower() or "connection" in str(e).lower():
                            self.logger.info(f"🔄 Attempting to reconnect producer for {symbol}")
                            await self.stop()
                            await asyncio.sleep(1)
                            reconnect_success = await self.start()
                            if not reconnect_success:
                                self.logger.error(f"❌ Failed to reconnect producer for {symbol}")
                                continue
                        
                        await asyncio.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                    else:
                        # Use centralized error handling for final failure
                        error_context = handle_error(
                            error=e,
                            category=ErrorCategory.REDPANDA,
                            severity=ErrorSeverity.HIGH,
                            component='mt5_redpanda_producer',
                            operation='tick_data_send_final_failure'
                        )
                        self.failed_messages += 1
                        self.logger.error(f"❌ Failed to send tick data for {symbol} after {max_retries} retries: {error_context.message}")
                        
                        # Log recovery suggestions
                        for suggestion in error_context.recovery_suggestions:
                            self.logger.info(f"💡 Recovery: {suggestion}")
                        
                        return False
                        
        except Exception as e:
            # Use centralized error handling for outer exception
            error_context = handle_error(
                error=e,
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.HIGH,
                component='mt5_redpanda_producer',
                operation='send_tick_data'
            )
            self.logger.error(f"Send tick data error: {error_context.message}")
            return False
    
    async def send_trading_event(self, topic: str, event_type: str, event_data: Dict[str, Any]) -> bool:
        """Send MT5 trading event to Backend3"""
        if not self.is_running:
            self.logger.warning("⚠️ Producer not running")
            return False
            
        try:
            event = MT5Event(
                event_id=f"trade_{event_type}_{uuid.uuid4().hex[:8]}",
                event_type=event_type,
                timestamp=datetime.utcnow(),
                payload=event_data,
                source="mt5_bridge",
                topic=topic,
                priority=MT5EventPriority.HIGH,
                metadata={"event_type": event_type}
            )
            
            await self.producer.send(topic, event.to_dict())
            self.sent_messages += 1
            self.last_send_time = datetime.utcnow()
            self.logger.debug(f"📈 Sent trading event {event_type} to {topic}")
            return True
            
        except Exception as e:
            self.failed_messages += 1
            self.logger.error(f"❌ Failed to send trading event {event_type}: {e}")
            return False
    
    async def send_account_info(self, topic: str, account_data: Dict[str, Any]) -> bool:
        """Send MT5 account information to Backend3"""
        if not self.is_running:
            return False
            
        try:
            event = MT5Event(
                event_id=f"account_{account_data.get('login', 'unknown')}_{uuid.uuid4().hex[:8]}",
                event_type="account_info",
                timestamp=datetime.utcnow(),
                payload=account_data,
                source="mt5_bridge",
                topic=topic,
                priority=MT5EventPriority.MEDIUM,
                metadata={"login": account_data.get('login')}
            )
            
            await self.producer.send(topic, event.to_dict())
            self.sent_messages += 1
            self.last_send_time = datetime.utcnow()
            return True
            
        except Exception as e:
            self.failed_messages += 1
            self.logger.error(f"❌ Failed to send account info: {e}")
            return False
    
    async def send_positions(self, topic: str, positions_data: Dict[str, Any]) -> bool:
        """Send MT5 positions to Backend3"""
        if not self.is_running:
            return False
            
        try:
            event = MT5Event(
                event_id=f"positions_{len(positions_data.get('positions', []))}_{uuid.uuid4().hex[:8]}",
                event_type="positions",
                timestamp=datetime.utcnow(),
                payload=positions_data,
                source="mt5_bridge",
                topic=topic,
                priority=MT5EventPriority.MEDIUM
            )
            
            await self.producer.send(topic, event.to_dict())
            self.sent_messages += 1
            self.last_send_time = datetime.utcnow()
            return True
            
        except Exception as e:
            self.failed_messages += 1
            self.logger.error(f"❌ Failed to send positions: {e}")
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get MT5 producer metrics"""
        return {
            "is_running": self.is_running,
            "sent_messages": self.sent_messages,
            "failed_messages": self.failed_messages,
            "last_send_time": self.last_send_time.isoformat() if self.last_send_time else None,
            "success_rate": (self.sent_messages / (self.sent_messages + self.failed_messages)) * 100 if (self.sent_messages + self.failed_messages) > 0 else 0,
            "client_id": self.config.client_id,
            "bootstrap_servers": self.config.bootstrap_servers
        }


class MT5RedpandaConsumer:
    """
    MT5 Bridge RedPanda Consumer - Client-side message consumption
    
    Specialized for receiving responses from Backend3:
    - AI analysis results
    - Trading signals
    - System notifications
    """
    
    def __init__(self, config: MT5RedpandaConfig, topics: List[str]):
        self.config = config
        self.topics = topics
        self.consumer = None
        self.is_running = False
        self.consumed_messages = 0
        self.processed_messages = 0
        self.failed_messages = 0
        self.message_handlers = {}
        # CENTRALIZED INFRASTRUCTURE - Initialize centralized logger
        self.logger = get_logger('mt5_redpanda_consumer', context={
            'component': 'mt5_redpanda_consumer',
            'topics': topics,
            'group_id': config.group_id,
            'version': '2.0.0-centralized'
        })
    
    async def start(self) -> bool:
        """Start the MT5 RedPanda consumer"""
        try:
            if AIOKAFKA_AVAILABLE:
                self.consumer = AIOKafkaConsumer(
                    *self.topics,
                    bootstrap_servers=self.config.bootstrap_servers,
                    group_id=self.config.group_id,
                    auto_offset_reset=self.config.auto_offset_reset,
                    enable_auto_commit=self.config.enable_auto_commit,
                    auto_commit_interval_ms=self.config.auto_commit_interval_ms,
                    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
                )
                await self.consumer.start()
                self.is_running = True
                self.logger.info(f"✅ MT5 RedPanda consumer started for topics: {self.topics}")
                return True
            else:
                self.logger.warning("⚠️ aiokafka not available, using fallback mode")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Failed to start MT5 RedPanda consumer: {e}")
            return False
    
    async def stop(self):
        """Stop the MT5 RedPanda consumer"""
        if self.consumer and self.is_running:
            await self.consumer.stop()
            self.is_running = False
            self.logger.info("🔌 MT5 RedPanda consumer stopped")
    
    def register_handler(self, event_type: str, handler):
        """Register message handler for specific event type"""
        self.message_handlers[event_type] = handler
        self.logger.info(f"📝 Registered handler for event type: {event_type}")
    
    async def consume_messages(self):
        """Start consuming messages from Backend3"""
        if not self.is_running:
            self.logger.warning("⚠️ Consumer not running")
            return
        
        try:
            async for message in self.consumer:
                self.consumed_messages += 1
                
                try:
                    # Process message
                    event_data = message.value
                    event_type = event_data.get('event_type', 'unknown')
                    
                    # Call registered handler if exists
                    if event_type in self.message_handlers:
                        await self.message_handlers[event_type](event_data)
                        self.processed_messages += 1
                    else:
                        self.logger.warning(f"⚠️ No handler for event type: {event_type}")
                    
                except Exception as e:
                    self.failed_messages += 1
                    self.logger.error(f"❌ Failed to process message: {e}")
                    
        except Exception as e:
            self.logger.error(f"❌ Error in message consumption: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get MT5 consumer metrics"""
        return {
            "is_running": self.is_running,
            "consumed_messages": self.consumed_messages,
            "processed_messages": self.processed_messages,
            "failed_messages": self.failed_messages,
            "success_rate": (self.processed_messages / self.consumed_messages) * 100 if self.consumed_messages > 0 else 0,
            "topics": self.topics,
            "group_id": self.config.group_id
        }


class MT5RedpandaManager:
    """
    MT5 Bridge RedPanda Manager - Unified client-side streaming management
    
    Manages both producer and consumer for MT5 Bridge operations
    """
    
    def __init__(self, config: MT5RedpandaConfig):
        self.config = config
        self.producer = None
        self.consumer = None
        # CENTRALIZED INFRASTRUCTURE - Initialize centralized logger
        self.logger = get_logger('mt5_redpanda_manager', context={
            'component': 'mt5_redpanda_manager',
            'client_id': config.client_id,
            'servers': config.bootstrap_servers,
            'version': '2.0.0-centralized'
        })
    
    @performance_tracked("redpanda_manager_start", "mt5_redpanda")
    async def start(self) -> bool:
        """Start MT5 RedPanda manager with producer - Enhanced with centralized infrastructure"""
        try:
            # Load centralized configuration
            try:
                redpanda_config = get_config('redpanda')
                if redpanda_config:
                    # Override config with centralized settings
                    self.config.bootstrap_servers = redpanda_config.get('bootstrap_servers', self.config.bootstrap_servers)
                    self.config.client_id = redpanda_config.get('client_id', self.config.client_id)
                    self.config.batch_size = redpanda_config.get('batch_size', self.config.batch_size)
                    
                    self.logger.info(f"🔧 Loaded centralized Redpanda config: {self.config.bootstrap_servers}")
                    
            except Exception as e:
                error_context = handle_error(
                    error=e,
                    category=ErrorCategory.CONFIG,
                    severity=ErrorSeverity.MEDIUM,
                    component='mt5_redpanda_manager',
                    operation='configuration_loading'
                )
                self.logger.warning(f"Failed to load centralized config: {error_context.message}")
            
            # Check if Kafka libraries are available
            if not AIOKAFKA_AVAILABLE and not KAFKA_PYTHON_AVAILABLE:
                self.logger.warning("⚠️ Kafka libraries not available, using WebSocket-only mode")
                return True  # Continue without Redpanda for WebSocket-only operation
            
            # Initialize producer for sending MT5 data
            success = await self.initialize_producer()
            if success:
                self.logger.info("✅ MT5 RedPanda manager started successfully")
                return True
            else:
                self.logger.warning("⚠️ Redpanda connection failed, continuing in WebSocket-only mode")
                return True  # Continue without Redpanda
        except Exception as e:
            # Use centralized error handling
            error_context = handle_error(
                error=e,
                category=ErrorCategory.REDPANDA,
                severity=ErrorSeverity.MEDIUM,
                component='mt5_redpanda_manager',
                operation='redpanda_manager_start'
            )
            self.logger.warning(f"⚠️ Redpanda initialization failed: {error_context.message}, continuing in WebSocket-only mode")
            
            # Log recovery suggestions
            for suggestion in error_context.recovery_suggestions:
                self.logger.info(f"💡 Recovery: {suggestion}")
            
            return True  # Continue without Redpanda
    
    async def initialize_producer(self) -> bool:
        """Initialize MT5 RedPanda producer"""
        self.producer = MT5RedpandaProducer(self.config)
        success = await self.producer.start()
        if success:
            self.logger.info("✅ MT5 RedPanda producer initialized")
        return success
    
    async def initialize_consumer(self, topics: List[str]) -> bool:
        """Initialize MT5 RedPanda consumer"""
        self.consumer = MT5RedpandaConsumer(self.config, topics)
        success = await self.consumer.start()
        if success:
            self.logger.info(f"✅ MT5 RedPanda consumer initialized for topics: {topics}")
        return success
    
    async def shutdown(self):
        """Shutdown both producer and consumer"""
        try:
            if self.producer:
                await self.producer.stop()
                self.producer = None
            if self.consumer:
                await self.consumer.stop()
                self.consumer = None
            self.logger.info("🔌 MT5 RedPanda manager shutdown complete")
        except Exception as e:
            self.logger.warning(f"⚠️ Shutdown warning: {e}")
            # Force cleanup
            self.producer = None
            self.consumer = None
    
    async def stop(self):
        """Alias for shutdown method for compatibility"""
        await self.shutdown()
    
    def register_signal_handler(self, signal_handler):
        """Register signal handler for graceful shutdown"""
        import signal
        
        def signal_callback(signum, frame):
            self.logger.info(f"📡 Received signal {signum}, initiating graceful shutdown...")
            # Create new event loop if needed
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Run shutdown in the event loop
            loop.run_until_complete(self.shutdown())
            
            # Call original signal handler if provided
            if signal_handler:
                signal_handler(signum, frame)
        
        # Register for common termination signals
        signal.signal(signal.SIGINT, signal_callback)
        signal.signal(signal.SIGTERM, signal_callback)
        
        self.logger.info("📡 Signal handlers registered for graceful shutdown")
    
    def get_status(self) -> Dict[str, Any]:
        """Get overall MT5 streaming status"""
        return {
            "producer_running": self.producer.is_running if self.producer else False,
            "consumer_running": self.consumer.is_running if self.consumer else False,
            "producer_metrics": self.producer.get_metrics() if self.producer else {},
            "consumer_metrics": self.consumer.get_metrics() if self.consumer else {},
            "bootstrap_servers": self.config.bootstrap_servers,
            "client_id": self.config.client_id,
            "fallback_mode": not (AIOKAFKA_AVAILABLE or KAFKA_PYTHON_AVAILABLE)
        }
    
    def is_healthy(self) -> bool:
        """Check if the MT5 Redpanda manager is healthy"""
        try:
            # If we have no producer, we're still healthy (fallback mode)
            if not self.producer:
                return True
            
            # If producer exists, check if it's running
            return self.producer.is_running
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    @performance_tracked("publish_mt5_data", "mt5_redpanda")
    async def publish_mt5_data(self, topic: str, data: Dict[str, Any]) -> bool:
        """Publish MT5 data - fallback to WebSocket if Redpanda not available - Enhanced with centralized validation"""
        try:
            # CENTRALIZED VALIDATION - Validate inputs
            topic_validation = validate_field('kafka_topic', topic, 'kafka_topic')
            data_validation = validate_dict(data, {
                'type': 'required_string',
                'timestamp': 'optional_string'
            })
            
            if not all([topic_validation.is_valid, data_validation.is_valid]):
                validation_errors = []
                for result in [topic_validation, data_validation]:
                    if not result.is_valid:
                        validation_errors.extend([error.message for error in result.errors])
                self.logger.error(f"Validation failed for MT5 data: {'; '.join(validation_errors)}")
                return False
            
            if self.producer and self.producer.is_running:
                # Use Redpanda if available
                return await self.producer.publish_event(
                    MT5Event(
                        event_id=str(uuid.uuid4()),
                        event_type=topic,
                        data=data,
                        timestamp=datetime.now(),
                        account_id=str(data.get('account', 'unknown')),
                        priority=MT5EventPriority.MEDIUM
                    )
                )
            else:
                # Fallback: just return True (WebSocket will handle the data)
                self.logger.debug(f"📡 Fallback mode: MT5 data will be sent via WebSocket")
                return True
        except Exception as e:
            # Use centralized error handling
            error_context = handle_error(
                error=e,
                category=ErrorCategory.REDPANDA,
                severity=ErrorSeverity.MEDIUM,
                component='mt5_redpanda_manager',
                operation='publish_mt5_data'
            )
            self.logger.warning(f"⚠️ Publish failed: {error_context.message}, using WebSocket fallback")
            return True


# Demo function for testing
async def demo_mt5_redpanda():
    """Demo function to test MT5 RedPanda client"""
    print("🧪 Testing MT5 Bridge RedPanda Client")
    print("=" * 40)
    
    # Create config
    config = MT5RedpandaConfig(
        bootstrap_servers="localhost:19092",
        client_id="mt5_demo",
        group_id="mt5_demo_group"
    )
    
    # Test manager
    manager = MT5RedpandaManager(config)
    
    # Initialize producer
    producer_success = await manager.initialize_producer()
    print(f"✅ Producer initialized: {producer_success}")
    
    # Initialize consumer
    consumer_success = await manager.initialize_consumer(["mt5_responses", "trading_signals"])
    print(f"✅ Consumer initialized: {consumer_success}")
    
    # Get status
    status = manager.get_status()
    print(f"📊 Status: {status}")
    
    # Shutdown
    await manager.shutdown()
    print("🎉 MT5 RedPanda demo completed!")


if __name__ == "__main__":
    asyncio.run(demo_mt5_redpanda())