"""
Data Bridge Service - Resource Management Core
Specialized resource management for data streaming operations
"""
import asyncio
import time
import psutil
import threading
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict, deque
from .service_identity_core import get_service_identity
from .monitoring_dashboard_core import get_service_monitoring

@dataclass
class DataBridgeResourceMetrics:
    """Data bridge-specific resource performance metrics"""
    memory_usage_mb: float
    cpu_usage_percent: float
    connection_pool_utilization: float
    stream_buffer_utilization: float
    active_websocket_connections: int
    message_queue_size: int
    bandwidth_utilization_mbps: float
    resource_efficiency_score: float

class DataBridgeResourceManagementCore:
    """
    Data Bridge Service specialized resource management.
    Optimizes connection pooling, stream buffering, message queuing, and bandwidth allocation.
    """
    
    def __init__(self):
        self.service_identity = get_service_identity("data-bridge")
        self.monitoring = get_service_monitoring("data-bridge")
        
        # Data bridge-specific resource pools
        self.websocket_connections = {}
        self.stream_buffers = {
            'incoming_stream': deque(maxlen=100000),  # Large buffer for incoming data
            'outgoing_stream': deque(maxlen=50000),   # Outgoing data buffer
            'processing_queue': deque(maxlen=25000),  # Processing queue
            'error_buffer': deque(maxlen=1000)        # Error messages
        }
        self.message_queues = {
            'high_priority': asyncio.Queue(maxsize=10000),
            'normal_priority': asyncio.Queue(maxsize=50000),
            'low_priority': asyncio.Queue(maxsize=100000)
        }
        
        # Resource limits and configuration
        self.resource_limits = {
            'max_memory_mb': 4096,          # 4GB memory limit
            'max_cpu_percent': 75,          # 75% CPU limit
            'max_websocket_connections': 1000,
            'max_bandwidth_mbps': 100,      # 100 Mbps bandwidth limit
            'max_concurrent_streams': 50,
            'max_message_rate_per_sec': 10000
        }
        
        # Resource monitoring
        self.resource_stats = defaultdict(lambda: {
            'current': 0, 'peak': 0, 'average': 0, 'samples': deque(maxlen=100)
        })
        
        # Connection management
        self.connection_pools = {
            'mt5_bridge': {'active': 0, 'max': 20, 'pool': []},
            'external_apis': {'active': 0, 'max': 30, 'pool': []},
            'database': {'active': 0, 'max': 15, 'pool': []},
            'message_brokers': {'active': 0, 'max': 10, 'pool': []}
        }
        
        self._setup_data_bridge_resource_management()
        self._start_resource_monitoring()
    
    def _setup_data_bridge_resource_management(self):
        """Setup data bridge-specific resource management"""
        # Stream processing configuration
        self.stream_config = {
            'batch_size': 1000,
            'processing_timeout': 2.0,
            'buffer_flush_interval': 5.0,
            'compression_enabled': True
        }
        
        # Bandwidth allocation
        self.bandwidth_allocation = {
            'incoming_streams': 0.6,    # 60% for incoming data
            'outgoing_streams': 0.3,    # 30% for outgoing data
            'control_messages': 0.1     # 10% for control/metadata
        }
        
        # Memory allocation strategies
        self.memory_allocation = {
            'stream_buffers': 0.5,      # 50% for stream buffers
            'message_queues': 0.3,      # 30% for message queues
            'connection_pools': 0.1,    # 10% for connections
            'processing': 0.1          # 10% for processing
        }
    
    def _start_resource_monitoring(self):
        """Start background resource monitoring"""
        def monitor_resources():
            while True:
                try:
                    self._collect_resource_metrics()
                    self._check_resource_limits()
                    self._optimize_resource_allocation()
                    self._manage_stream_buffers()
                    time.sleep(5)  # Monitor every 5 seconds for data streaming
                except Exception as e:
                    self.monitoring.record_metric("data_bridge_resource_monitor_error", 1, "count")
        
        monitor_thread = threading.Thread(target=monitor_resources, daemon=True)
        monitor_thread.start()
    
    def _collect_resource_metrics(self):
        """Collect current resource usage metrics"""
        # Memory metrics
        process = psutil.Process()
        process_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        self._update_resource_stat('memory_usage_mb', process_memory)
        self.monitoring.record_metric("data_bridge_memory_usage_mb", process_memory, "gauge")
        
        # CPU metrics
        cpu_percent = process.cpu_percent()
        self._update_resource_stat('cpu_usage_percent', cpu_percent)
        self.monitoring.record_metric("data_bridge_cpu_usage_percent", cpu_percent, "gauge")
        
        # Connection metrics
        total_connections = sum(pool['active'] for pool in self.connection_pools.values())
        connection_utilization = (total_connections / sum(pool['max'] for pool in self.connection_pools.values())) * 100
        self._update_resource_stat('connection_utilization', connection_utilization)
        
        # WebSocket connections
        ws_connections = len(self.websocket_connections)
        self._update_resource_stat('websocket_connections', ws_connections)
        
        # Buffer utilization
        buffer_utilization = self._calculate_buffer_utilization()
        self._update_resource_stat('buffer_utilization', buffer_utilization)
        
        # Message queue metrics
        total_queue_size = sum(queue.qsize() for queue in self.message_queues.values())
        self._update_resource_stat('message_queue_size', total_queue_size)
        
        # Bandwidth utilization (simplified calculation)
        bandwidth_usage = self._estimate_bandwidth_usage()
        self._update_resource_stat('bandwidth_usage_mbps', bandwidth_usage)
    
    def _calculate_buffer_utilization(self) -> float:
        """Calculate stream buffer utilization percentage"""
        total_used = sum(len(buffer) for buffer in self.stream_buffers.values())
        total_capacity = sum(buffer.maxlen for buffer in self.stream_buffers.values())
        return (total_used / total_capacity * 100) if total_capacity > 0 else 0
    
    def _estimate_bandwidth_usage(self) -> float:
        """Estimate current bandwidth usage in Mbps"""
        # Simple estimation based on buffer activity
        incoming_rate = len(self.stream_buffers['incoming_stream']) * 0.001  # Rough estimation
        outgoing_rate = len(self.stream_buffers['outgoing_stream']) * 0.001
        return incoming_rate + outgoing_rate
    
    def _update_resource_stat(self, metric_name: str, value: float):
        """Update resource statistics with new value"""
        stat = self.resource_stats[metric_name]
        stat['current'] = value
        stat['peak'] = max(stat['peak'], value)
        stat['samples'].append(value)
        stat['average'] = sum(stat['samples']) / len(stat['samples'])
    
    def _check_resource_limits(self):
        """Check if resource usage exceeds limits and take action"""
        # Memory limit check
        current_memory = self.resource_stats['memory_usage_mb']['current']
        if current_memory > self.resource_limits['max_memory_mb']:
            self._handle_memory_pressure()
        
        # CPU limit check
        current_cpu = self.resource_stats['cpu_usage_percent']['current']
        if current_cpu > self.resource_limits['max_cpu_percent']:
            self._handle_cpu_pressure()
        
        # WebSocket connections limit
        ws_connections = self.resource_stats['websocket_connections']['current']
        if ws_connections > self.resource_limits['max_websocket_connections']:
            self._handle_connection_pressure()
        
        # Bandwidth limit check
        bandwidth_usage = self.resource_stats['bandwidth_usage_mbps']['current']
        if bandwidth_usage > self.resource_limits['max_bandwidth_mbps']:
            self._handle_bandwidth_pressure()
    
    def _handle_memory_pressure(self):
        """Handle high memory usage"""
        self.monitoring.record_metric("data_bridge_memory_pressure_event", 1, "count")
        
        # Flush stream buffers aggressively
        for buffer_name, buffer in self.stream_buffers.items():
            if len(buffer) > buffer.maxlen * 0.7:
                # Keep only recent 30% of data
                keep_count = int(buffer.maxlen * 0.3)
                new_buffer = deque(list(buffer)[-keep_count:], maxlen=buffer.maxlen)
                self.stream_buffers[buffer_name] = new_buffer
        
        # Clear low priority message queues
        low_priority_queue = self.message_queues['low_priority']
        while not low_priority_queue.empty() and low_priority_queue.qsize() > 1000:
            try:
                low_priority_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
    
    def _handle_cpu_pressure(self):
        """Handle high CPU usage"""
        self.monitoring.record_metric("data_bridge_cpu_pressure_event", 1, "count")
        
        # Reduce batch processing size
        self.stream_config['batch_size'] = max(100, self.stream_config['batch_size'] - 200)
        
        # Increase processing timeout to reduce urgency
        self.stream_config['processing_timeout'] = min(5.0, self.stream_config['processing_timeout'] + 0.5)
    
    def _handle_connection_pressure(self):
        """Handle too many WebSocket connections"""
        self.monitoring.record_metric("data_bridge_connection_pressure_event", 1, "count")
        
        # Close oldest idle connections
        current_time = time.time()
        connections_to_close = []
        
        for conn_id, conn_info in self.websocket_connections.items():
            if current_time - conn_info.get('last_activity', 0) > 300:  # 5 minutes idle
                connections_to_close.append(conn_id)
                if len(connections_to_close) >= 10:  # Close up to 10 connections
                    break
        
        for conn_id in connections_to_close:
            del self.websocket_connections[conn_id]
    
    def _handle_bandwidth_pressure(self):
        """Handle high bandwidth usage"""
        self.monitoring.record_metric("data_bridge_bandwidth_pressure_event", 1, "count")
        
        # Enable compression if not already enabled
        self.stream_config['compression_enabled'] = True
        
        # Increase buffer flush interval to batch more data
        self.stream_config['buffer_flush_interval'] = min(10.0, self.stream_config['buffer_flush_interval'] + 1.0)
    
    def _manage_stream_buffers(self):
        """Actively manage stream buffer sizes and content"""
        current_time = time.time()
        
        # Auto-flush buffers based on time and size
        for buffer_name, buffer in self.stream_buffers.items():
            buffer_age = getattr(buffer, 'last_flush', current_time)
            
            if (current_time - buffer_age > self.stream_config['buffer_flush_interval'] or
                len(buffer) > buffer.maxlen * 0.8):
                
                # Simulate buffer flush (in real implementation, this would process the data)
                processed_count = min(len(buffer), self.stream_config['batch_size'])
                for _ in range(processed_count):
                    if buffer:
                        buffer.popleft()
                
                buffer.last_flush = current_time
                self.monitoring.record_metric(f"data_bridge_{buffer_name}_flushed", processed_count, "count")
    
    def _optimize_resource_allocation(self):
        """Dynamically optimize resource allocation based on usage patterns"""
        # Adjust memory allocation based on buffer usage
        buffer_utilization = self.resource_stats['buffer_utilization']['current']
        
        if buffer_utilization > 80:  # High buffer usage
            # Increase buffer allocation, decrease processing allocation
            self.memory_allocation['stream_buffers'] = min(0.7, self.memory_allocation['stream_buffers'] + 0.05)
            self.memory_allocation['processing'] = max(0.05, self.memory_allocation['processing'] - 0.05)
        elif buffer_utilization < 30:  # Low buffer usage
            # Increase processing allocation
            self.memory_allocation['processing'] = min(0.2, self.memory_allocation['processing'] + 0.05)
            self.memory_allocation['stream_buffers'] = max(0.3, self.memory_allocation['stream_buffers'] - 0.05)
    
    async def acquire_connection(self, pool_type: str, priority: str = "normal") -> Optional[Any]:
        """Acquire a connection from the specified pool"""
        if pool_type not in self.connection_pools:
            return None
        
        pool = self.connection_pools[pool_type]
        
        # Check if we can create new connection
        if pool['active'] >= pool['max']:
            if priority == "high":
                # For high priority, try to reuse existing connection
                if pool['pool']:
                    return pool['pool'][0]  # Return first available
                else:
                    return None
            else:
                return None
        
        # Create/acquire connection
        pool['active'] += 1
        connection_id = f"{pool_type}_{pool['active']}_{int(time.time())}"
        
        connection = {
            'id': connection_id,
            'pool_type': pool_type,
            'acquired_at': time.time(),
            'priority': priority
        }
        
        pool['pool'].append(connection)
        self.monitoring.record_metric(f"data_bridge_{pool_type}_connection_acquired", 1, "count")
        
        return connection
    
    async def release_connection(self, connection: Dict[str, Any]):
        """Release a connection back to the pool"""
        pool_type = connection['pool_type']
        if pool_type in self.connection_pools:
            pool = self.connection_pools[pool_type]
            
            # Remove from pool if exists
            pool['pool'] = [conn for conn in pool['pool'] if conn['id'] != connection['id']]
            pool['active'] = max(0, pool['active'] - 1)
            
            self.monitoring.record_metric(f"data_bridge_{pool_type}_connection_released", 1, "count")
    
    async def register_websocket_connection(self, connection_id: str, metadata: Dict[str, Any] = None) -> bool:
        """Register a new WebSocket connection"""
        if len(self.websocket_connections) >= self.resource_limits['max_websocket_connections']:
            return False
        
        self.websocket_connections[connection_id] = {
            'connected_at': time.time(),
            'last_activity': time.time(),
            'metadata': metadata or {},
            'message_count': 0
        }
        
        self.monitoring.record_metric("data_bridge_websocket_connected", 1, "count")
        return True
    
    async def unregister_websocket_connection(self, connection_id: str):
        """Unregister a WebSocket connection"""
        if connection_id in self.websocket_connections:
            connection_info = self.websocket_connections[connection_id]
            duration = time.time() - connection_info['connected_at']
            
            del self.websocket_connections[connection_id]
            
            self.monitoring.record_metric("data_bridge_websocket_disconnected", 1, "count")
            self.monitoring.record_metric("data_bridge_websocket_duration", duration, "gauge")
    
    async def enqueue_message(self, message: Dict[str, Any], priority: str = "normal") -> bool:
        """Enqueue a message with priority handling"""
        if priority not in self.message_queues:
            priority = "normal"
        
        queue = self.message_queues[priority]
        
        try:
            # Add timestamp and size info
            message['enqueued_at'] = time.time()
            message['size_bytes'] = len(str(message))
            
            await queue.put(message)
            self.monitoring.record_metric(f"data_bridge_message_enqueued_{priority}", 1, "count")
            return True
            
        except asyncio.QueueFull:
            self.monitoring.record_metric(f"data_bridge_message_queue_full_{priority}", 1, "count")
            return False
    
    async def dequeue_message(self, priority: str = "high") -> Optional[Dict[str, Any]]:
        """Dequeue a message with priority handling"""
        # Try high priority first, then normal, then low
        priority_order = ["high", "normal", "low"] if priority == "high" else [priority]
        
        for p in priority_order:
            if p in self.message_queues:
                queue = self.message_queues[p]
                try:
                    message = queue.get_nowait()
                    self.monitoring.record_metric(f"data_bridge_message_dequeued_{p}", 1, "count")
                    return message
                except asyncio.QueueEmpty:
                    continue
        
        return None
    
    def add_to_stream_buffer(self, buffer_type: str, data: Any) -> bool:
        """Add data to stream buffer with resource management"""
        if buffer_type not in self.stream_buffers:
            return False
        
        buffer = self.stream_buffers[buffer_type]
        
        # Check if we're approaching memory limits
        current_memory = self.resource_stats['memory_usage_mb']['current']
        if current_memory > self.resource_limits['max_memory_mb'] * 0.9:
            # Reject new data if memory is critically high
            return False
        
        buffer.append({
            'data': data,
            'timestamp': time.time(),
            'size_bytes': len(str(data))
        })
        
        # Update metrics
        utilization = len(buffer) / buffer.maxlen * 100
        self.monitoring.record_metric(f"data_bridge_{buffer_type}_utilization", utilization, "gauge")
        
        return True
    
    def get_resource_metrics(self) -> DataBridgeResourceMetrics:
        """Get comprehensive resource metrics"""
        total_connections = sum(pool['active'] for pool in self.connection_pools.values())
        total_capacity = sum(pool['max'] for pool in self.connection_pools.values())
        connection_utilization = (total_connections / total_capacity * 100) if total_capacity > 0 else 0
        
        buffer_utilization = self._calculate_buffer_utilization()
        
        # Calculate efficiency score
        memory_efficiency = max(0, 100 - (self.resource_stats['memory_usage_mb']['current'] / self.resource_limits['max_memory_mb'] * 100))
        cpu_efficiency = max(0, 100 - self.resource_stats['cpu_usage_percent']['current'])
        bandwidth_efficiency = max(0, 100 - (self.resource_stats['bandwidth_usage_mbps']['current'] / self.resource_limits['max_bandwidth_mbps'] * 100))
        efficiency_score = (memory_efficiency + cpu_efficiency + bandwidth_efficiency) / 3
        
        return DataBridgeResourceMetrics(
            memory_usage_mb=self.resource_stats['memory_usage_mb']['current'],
            cpu_usage_percent=self.resource_stats['cpu_usage_percent']['current'],
            connection_pool_utilization=connection_utilization,
            stream_buffer_utilization=buffer_utilization,
            active_websocket_connections=len(self.websocket_connections),
            message_queue_size=sum(queue.qsize() for queue in self.message_queues.values()),
            bandwidth_utilization_mbps=self.resource_stats['bandwidth_usage_mbps']['current'],
            resource_efficiency_score=efficiency_score
        )
    
    async def optimize_resources(self):
        """Trigger immediate resource optimization"""
        self._optimize_resource_allocation()
        self._manage_stream_buffers()
        
        # Cleanup expired connections
        current_time = time.time()
        expired_connections = [
            conn_id for conn_id, conn_info in self.websocket_connections.items()
            if current_time - conn_info['last_activity'] > 3600  # 1 hour timeout
        ]
        
        for conn_id in expired_connections:
            await self.unregister_websocket_connection(conn_id)
    
    async def scale_resources(self, scale_factor: float):
        """Scale resources up or down based on demand"""
        if scale_factor > 1.0:
            # Scale up
            for pool in self.connection_pools.values():
                pool['max'] = int(pool['max'] * scale_factor)
            
            # Increase buffer sizes
            for buffer_name, buffer in self.stream_buffers.items():
                new_maxlen = int(buffer.maxlen * scale_factor)
                new_buffer = deque(buffer, maxlen=new_maxlen)
                self.stream_buffers[buffer_name] = new_buffer
            
        elif scale_factor < 1.0:
            # Scale down
            for pool in self.connection_pools.values():
                pool['max'] = max(int(pool['max'] * scale_factor), 5)  # Minimum 5 connections
                pool['active'] = min(pool['active'], pool['max'])
        
        self.monitoring.record_metric("data_bridge_resource_scaling", scale_factor, "gauge")


# Service Resource Management Singleton
_data_bridge_resource_manager = None

def get_data_bridge_resource_manager() -> DataBridgeResourceManagementCore:
    """Get or create data bridge resource manager singleton"""
    global _data_bridge_resource_manager
    
    if _data_bridge_resource_manager is None:
        _data_bridge_resource_manager = DataBridgeResourceManagementCore()
    
    return _data_bridge_resource_manager

# Convenience functions for data bridge resource management
async def acquire_bridge_connection(pool_type: str, priority: str = "normal"):
    """Acquire bridge connection"""
    manager = get_data_bridge_resource_manager()
    return await manager.acquire_connection(pool_type, priority)

async def register_websocket(connection_id: str, metadata: Dict[str, Any] = None) -> bool:
    """Register WebSocket connection"""
    manager = get_data_bridge_resource_manager()
    return await manager.register_websocket_connection(connection_id, metadata)

def add_stream_data(buffer_type: str, data: Any) -> bool:
    """Add data to stream buffer"""
    manager = get_data_bridge_resource_manager()
    return manager.add_to_stream_buffer(buffer_type, data)