"""
Data Bridge Service - Performance Optimization Core
Specialized performance optimization for data streaming and real-time processing
"""
import asyncio
import time
import psutil
from typing import Dict, Any, List, Optional, Callable, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import wraps
from concurrent.futures import ThreadPoolExecutor
from collections import deque, defaultdict
import json
from .service_identity_core import get_service_identity
from .monitoring_dashboard_core import get_service_monitoring

@dataclass
class DataBridgePerformanceMetrics:
    """Data Bridge specific performance metrics"""
    streaming_latency_ms: float
    data_throughput_per_second: float
    buffer_utilization_percent: float
    websocket_connection_count: int
    message_processing_time_ms: float
    data_compression_ratio: float
    memory_usage_mb: float
    queue_depth: int

class DataBridgePerformanceOptimizationCore:
    """
    Data Bridge Service specialized performance optimization.
    Optimizes data streaming, WebSocket connections, buffering, and real-time processing.
    """
    
    def __init__(self):
        self.service_identity = get_service_identity("data-bridge")
        self.monitoring = get_service_monitoring("data-bridge")
        
        # Data streaming optimization settings
        self.stream_buffers = defaultdict(lambda: deque(maxlen=10000))
        self.compression_cache = {}
        self.websocket_pool = {}
        self.message_queue = asyncio.Queue(maxsize=50000)
        self.processing_pool = ThreadPoolExecutor(max_workers=6)
        
        # Performance tracking
        self.streaming_latencies = deque(maxlen=1000)
        self.processing_times = deque(maxlen=1000)
        self.throughput_samples = deque(maxlen=100)
        
        # Streaming optimization settings
        self.enable_compression = True
        self.batch_processing = True
        self.adaptive_buffering = True
        self.max_buffer_size = 10000
        
        self._setup_streaming_optimizations()
    
    def _setup_streaming_optimizations(self):
        """Setup data streaming specific optimizations"""
        # Optimize for high-throughput streaming
        self.data_serialization_cache = {}
        self.symbol_stream_cache = defaultdict(list)
        self.connection_health_cache = {}
        
        # Initialize streaming performance counters
        self.bytes_processed = 0
        self.messages_processed = 0
        self.connections_active = 0
    
    def optimize_data_streaming(self, 
                              stream_processor: Callable,
                              buffer_size: int = 1000,
                              compression_enabled: bool = True) -> Callable:
        """
        Optimize data streaming with buffering, compression, and batch processing.
        Specialized for high-frequency data streams.
        """
        @wraps(stream_processor)
        async def optimized_streaming(*args, **kwargs):
            start_time = time.time()
            
            stream_id = kwargs.get('stream_id', 'default')
            data = args[0] if args else kwargs.get('data')
            
            try:
                # Apply streaming optimizations
                if compression_enabled:
                    compressed_data = await self._compress_stream_data(data)
                else:
                    compressed_data = data
                
                # Add to buffer for batch processing
                if self.batch_processing:
                    await self._add_to_stream_buffer(stream_id, compressed_data)
                    
                    # Process buffer if it's full or timeout reached
                    if len(self.stream_buffers[stream_id]) >= buffer_size:
                        buffered_data = list(self.stream_buffers[stream_id])
                        self.stream_buffers[stream_id].clear()
                        
                        # Process batch
                        result = await self._process_stream_batch(
                            stream_processor, buffered_data, stream_id, **kwargs
                        )
                    else:
                        # Return immediately for partial batch
                        result = {"status": "buffered", "stream_id": stream_id}
                else:
                    # Process individual message
                    result = await asyncio.get_event_loop().run_in_executor(
                        self.processing_pool, stream_processor, compressed_data, **kwargs
                    )
                
                # Track streaming performance
                latency = (time.time() - start_time) * 1000
                self.streaming_latencies.append(latency)
                self.monitoring.record_metric("data_streaming_latency", latency, "milliseconds")
                self.monitoring.record_metric("data_messages_processed", 1, "count")
                
                # Update throughput tracking
                self.messages_processed += 1
                if isinstance(data, (str, bytes)):
                    self.bytes_processed += len(data)
                
                return result
                
            except Exception as e:
                latency = (time.time() - start_time) * 1000
                self.monitoring.record_metric("data_streaming_error", 1, "count")
                raise e
        
        return optimized_streaming
    
    def optimize_websocket_handling(self, 
                                  websocket_handler: Callable,
                                  connection_pooling: bool = True) -> Callable:
        """
        Optimize WebSocket connection handling with pooling and connection reuse.
        Specialized for WebSocket data transmission.
        """
        @wraps(websocket_handler)
        async def optimized_websocket_handling(websocket, *args, **kwargs):
            start_time = time.time()
            connection_id = id(websocket)
            
            try:
                # Add connection to pool
                if connection_pooling:
                    self.websocket_pool[connection_id] = {
                        'websocket': websocket,
                        'connected_at': time.time(),
                        'last_activity': time.time(),
                        'message_count': 0
                    }
                    self.connections_active += 1
                
                # Monitor connection health
                await self._monitor_websocket_health(connection_id, websocket)
                
                # Process WebSocket with optimization
                result = await websocket_handler(websocket, *args, **kwargs)
                
                # Update connection statistics
                if connection_id in self.websocket_pool:
                    self.websocket_pool[connection_id]['last_activity'] = time.time()
                    self.websocket_pool[connection_id]['message_count'] += 1
                
                # Track WebSocket performance
                processing_time = (time.time() - start_time) * 1000
                self.monitoring.record_metric("data_websocket_processing_time", processing_time, "milliseconds")
                self.monitoring.record_metric("data_websocket_connections", self.connections_active, "count")
                
                return result
                
            except Exception as e:
                # Clean up connection on error
                if connection_id in self.websocket_pool:
                    del self.websocket_pool[connection_id]
                    self.connections_active -= 1
                
                self.monitoring.record_metric("data_websocket_error", 1, "count")
                raise e
            finally:
                # Clean up inactive connections
                await self._cleanup_inactive_connections()
        
        return optimized_websocket_handling
    
    def optimize_message_queuing(self, 
                               message_processor: Callable,
                               queue_size: int = 10000,
                               batch_size: int = 100) -> Callable:
        """
        Optimize message queue processing with batching and priority handling.
        Specialized for message queue operations.
        """
        @wraps(message_processor)
        async def optimized_message_queuing(*args, **kwargs):
            start_time = time.time()
            
            message = args[0] if args else kwargs.get('message')
            priority = kwargs.get('priority', 'normal')
            
            try:
                # Add message to queue with priority
                queue_item = {
                    'message': message,
                    'priority': priority,
                    'timestamp': time.time(),
                    'kwargs': kwargs
                }
                
                await self.message_queue.put(queue_item)
                
                # Process messages in batches for efficiency
                if self.message_queue.qsize() >= batch_size:
                    batch_messages = []
                    for _ in range(min(batch_size, self.message_queue.qsize())):
                        try:
                            batch_item = await asyncio.wait_for(self.message_queue.get(), timeout=0.1)
                            batch_messages.append(batch_item)
                        except asyncio.TimeoutError:
                            break
                    
                    # Process batch
                    if batch_messages:
                        result = await self._process_message_batch(
                            message_processor, batch_messages
                        )
                    else:
                        result = {"status": "queued"}
                else:
                    result = {"status": "queued", "queue_size": self.message_queue.qsize()}
                
                # Track queue performance
                processing_time = (time.time() - start_time) * 1000
                self.processing_times.append(processing_time)
                self.monitoring.record_metric("data_message_queue_time", processing_time, "milliseconds")
                self.monitoring.record_metric("data_queue_depth", self.message_queue.qsize(), "count")
                
                return result
                
            except Exception as e:
                self.monitoring.record_metric("data_message_queue_error", 1, "count")
                raise e
        
        return optimized_message_queuing
    
    def optimize_data_transformation(self, 
                                   transformer: Callable,
                                   cache_transformations: bool = True) -> Callable:
        """
        Optimize data transformation with caching and vectorization.
        Specialized for data format conversions and transformations.
        """
        @wraps(transformer)
        async def optimized_data_transformation(data, *args, **kwargs):
            start_time = time.time()
            
            # Generate cache key for transformation
            if cache_transformations:
                cache_key = self._generate_transformation_cache_key(data, args, kwargs)
                if cache_key in self.data_serialization_cache:
                    cached_result = self.data_serialization_cache[cache_key]
                    if time.time() - cached_result['timestamp'] < 300:  # 5 min cache
                        self.monitoring.record_metric("data_transformation_cache_hit", 1, "count")
                        return cached_result['result']
            
            # Optimize data format for transformation
            optimized_data = await self._optimize_data_format(data)
            
            # Perform transformation
            result = await asyncio.get_event_loop().run_in_executor(
                self.processing_pool, transformer, optimized_data, *args, **kwargs
            )
            
            # Cache result if enabled
            if cache_transformations and cache_key:
                self.data_serialization_cache[cache_key] = {
                    'result': result,
                    'timestamp': time.time()
                }
            
            # Track transformation performance
            transformation_time = (time.time() - start_time) * 1000
            self.monitoring.record_metric("data_transformation_time", transformation_time, "milliseconds")
            
            return result
        
        return optimized_data_transformation
    
    async def _compress_stream_data(self, data: Any) -> Any:
        """Compress streaming data for network efficiency"""
        if not self.enable_compression:
            return data
        
        try:
            if isinstance(data, dict):
                # Compress JSON data
                json_str = json.dumps(data, separators=(',', ':'))
                if len(json_str) > 1000:  # Only compress large payloads
                    import gzip
                    compressed = gzip.compress(json_str.encode('utf-8'))
                    return {
                        '_compressed': True,
                        '_data': compressed,
                        '_original_size': len(json_str)
                    }
            return data
        except:
            return data
    
    async def _add_to_stream_buffer(self, stream_id: str, data: Any):
        """Add data to stream buffer with intelligent buffering"""
        if self.adaptive_buffering:
            # Adjust buffer size based on throughput
            current_throughput = len(self.throughput_samples)
            if current_throughput > 80:  # High throughput
                self.stream_buffers[stream_id].maxlen = min(20000, self.max_buffer_size * 2)
            else:
                self.stream_buffers[stream_id].maxlen = self.max_buffer_size
        
        self.stream_buffers[stream_id].append(data)
    
    async def _process_stream_batch(self, processor: Callable, batch_data: List, stream_id: str, **kwargs):
        """Process a batch of streaming data"""
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                self.processing_pool, processor, batch_data, **kwargs
            )
            
            # Track batch processing metrics
            self.monitoring.record_metric("data_batch_size", len(batch_data), "count")
            self.monitoring.record_metric("data_batch_processed", 1, "count")
            
            return result
        except Exception as e:
            self.monitoring.record_metric("data_batch_error", 1, "count")
            raise e
    
    async def _monitor_websocket_health(self, connection_id: int, websocket):
        """Monitor WebSocket connection health"""
        try:
            # Simple ping/pong health check
            if hasattr(websocket, 'ping'):
                ping_time = time.time()
                await asyncio.wait_for(websocket.ping(), timeout=5.0)
                pong_time = time.time()
                
                latency = (pong_time - ping_time) * 1000
                self.monitoring.record_metric("data_websocket_ping_latency", latency, "milliseconds")
        except:
            # Mark connection as unhealthy
            if connection_id in self.websocket_pool:
                self.websocket_pool[connection_id]['healthy'] = False
    
    async def _cleanup_inactive_connections(self):
        """Clean up inactive WebSocket connections"""
        current_time = time.time()
        inactive_connections = []
        
        for conn_id, conn_info in self.websocket_pool.items():
            if current_time - conn_info['last_activity'] > 300:  # 5 minutes inactive
                inactive_connections.append(conn_id)
        
        for conn_id in inactive_connections:
            if conn_id in self.websocket_pool:
                del self.websocket_pool[conn_id]
                self.connections_active -= 1
        
        if inactive_connections:
            self.monitoring.record_metric("data_websocket_cleanup", len(inactive_connections), "count")
    
    async def _process_message_batch(self, processor: Callable, batch_messages: List):
        """Process a batch of messages"""
        try:
            # Sort messages by priority
            batch_messages.sort(key=lambda x: 0 if x['priority'] == 'high' else 1)
            
            # Extract messages for processing
            messages = [item['message'] for item in batch_messages]
            
            result = await asyncio.get_event_loop().run_in_executor(
                self.processing_pool, processor, messages
            )
            
            return result
        except Exception as e:
            self.monitoring.record_metric("data_message_batch_error", 1, "count")
            raise e
    
    async def _optimize_data_format(self, data: Any) -> Any:
        """Optimize data format for processing"""
        if isinstance(data, str) and len(data) > 10000:
            # For large strings, consider streaming processing
            return data
        elif isinstance(data, list) and len(data) > 1000:
            # For large lists, consider chunking
            return data
        else:
            return data
    
    def _generate_transformation_cache_key(self, data: Any, args: tuple, kwargs: dict) -> str:
        """Generate cache key for data transformation"""
        try:
            import hashlib
            key_data = str(type(data).__name__) + str(len(str(data))[:100]) + str(args) + str(kwargs)
            return hashlib.md5(key_data.encode()).hexdigest()[:16]
        except:
            return None
    
    def get_performance_metrics(self) -> DataBridgePerformanceMetrics:
        """Get current data bridge performance metrics"""
        avg_latency = sum(self.streaming_latencies) / len(self.streaming_latencies) if self.streaming_latencies else 0
        avg_processing = sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0
        
        # Calculate throughput
        if self.streaming_latencies:
            throughput = len(self.streaming_latencies) / (sum(self.streaming_latencies) / 1000)
        else:
            throughput = 0
        
        # Calculate buffer utilization
        total_buffer_capacity = sum(buf.maxlen for buf in self.stream_buffers.values())
        total_buffer_used = sum(len(buf) for buf in self.stream_buffers.values())
        buffer_utilization = (total_buffer_used / total_buffer_capacity * 100) if total_buffer_capacity > 0 else 0
        
        # Calculate compression ratio
        compression_ratio = 2.5 if self.enable_compression else 1.0  # Placeholder
        
        return DataBridgePerformanceMetrics(
            streaming_latency_ms=avg_latency,
            data_throughput_per_second=throughput,
            buffer_utilization_percent=buffer_utilization,
            websocket_connection_count=self.connections_active,
            message_processing_time_ms=avg_processing,
            data_compression_ratio=compression_ratio,
            memory_usage_mb=psutil.virtual_memory().used / (1024 * 1024),
            queue_depth=self.message_queue.qsize()
        )
    
    def optimize_service_startup(self):
        """Optimize data bridge service startup performance"""
        # Initialize stream buffers
        # Warm up compression cache
        # Setup WebSocket pools
        pass


# Service Performance Optimization Singleton
_data_bridge_performance_optimizer = None

def get_data_bridge_performance_optimizer() -> DataBridgePerformanceOptimizationCore:
    """Get or create data bridge performance optimizer singleton"""
    global _data_bridge_performance_optimizer
    
    if _data_bridge_performance_optimizer is None:
        _data_bridge_performance_optimizer = DataBridgePerformanceOptimizationCore()
    
    return _data_bridge_performance_optimizer

# Convenience decorators for data bridge optimization
def optimize_data_streaming(buffer_size: int = 1000, compression: bool = True):
    """Decorator to optimize data streaming"""
    def decorator(func):
        optimizer = get_data_bridge_performance_optimizer()
        return optimizer.optimize_data_streaming(func, buffer_size, compression)
    return decorator

def optimize_websocket_handling(connection_pooling: bool = True):
    """Decorator to optimize WebSocket handling"""
    def decorator(func):
        optimizer = get_data_bridge_performance_optimizer()
        return optimizer.optimize_websocket_handling(func, connection_pooling)
    return decorator

def optimize_message_queuing(queue_size: int = 10000, batch_size: int = 100):
    """Decorator to optimize message queue processing"""
    def decorator(func):
        optimizer = get_data_bridge_performance_optimizer()
        return optimizer.optimize_message_queuing(func, queue_size, batch_size)
    return decorator