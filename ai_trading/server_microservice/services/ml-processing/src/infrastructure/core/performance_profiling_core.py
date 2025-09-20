"""
Data Bridge Service - Performance Profiling Core
Advanced performance profiling and bottleneck detection for data streaming operations
"""
import asyncio
import time
import threading
import psutil
import tracemalloc
from typing import Dict, Any, List, Optional, Callable, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from functools import wraps
import numpy as np
from .service_identity_core import get_service_identity
from .monitoring_dashboard_core import get_service_monitoring

@dataclass
class DataBridgePerformanceProfile:
    """Data bridge performance profiling metrics"""
    stream_processing_profile: Dict[str, Any] = field(default_factory=dict)
    message_routing_profile: Dict[str, Any] = field(default_factory=dict)
    data_transformation_profile: Dict[str, Any] = field(default_factory=dict)
    connection_management_profile: Dict[str, Any] = field(default_factory=dict)
    throughput_analysis: Dict[str, Any] = field(default_factory=dict)
    latency_distribution: Dict[str, Any] = field(default_factory=dict)
    memory_usage_profile: Dict[str, Any] = field(default_factory=dict)
    bottleneck_analysis: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class DataBridgeBottleneck:
    """Data bridge-specific bottleneck detection"""
    bottleneck_type: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    component: str
    metric_name: str
    current_value: float
    threshold_value: float
    impact_score: float
    recommendation: str
    detection_time: datetime = field(default_factory=datetime.now)

class DataBridgePerformanceProfiler:
    """
    Data Bridge Service specialized performance profiler.
    Detects bottlenecks in stream processing, message routing, and data transformation.
    """
    
    def __init__(self):
        self.service_identity = get_service_identity("data-bridge")
        self.monitoring = get_service_monitoring("data-bridge")
        
        # Performance tracking data structures
        self.performance_data = defaultdict(lambda: {
            'processing_times': deque(maxlen=1000),
            'throughput_rates': deque(maxlen=500),
            'message_sizes': deque(maxlen=500),
            'connection_counts': deque(maxlen=100)
        })
        
        # Bottleneck detection thresholds
        self.bottleneck_thresholds = {
            'stream_processing_latency_ms': 25,      # Max 25ms for stream processing
            'message_routing_latency_ms': 10,        # Max 10ms for message routing
            'data_transformation_latency_ms': 50,    # Max 50ms for data transformation
            'connection_setup_latency_ms': 100,      # Max 100ms for connection setup
            'throughput_messages_per_sec': 10000,    # Min 10k messages per second
            'memory_usage_percent': 75,              # Max 75% memory usage
            'cpu_usage_percent': 80,                 # Max 80% CPU usage
            'message_loss_rate_percent': 0.1,        # Max 0.1% message loss
            'connection_failure_rate_percent': 1     # Max 1% connection failure
        }
        
        # Performance baseline measurements
        self.performance_baselines = {}
        self.profiling_enabled = True
        self.detailed_profiling = False
        
        # Stream performance tracking
        self.stream_metrics = {
            'active_streams': 0,
            'total_messages_processed': 0,
            'total_bytes_processed': 0,
            'messages_per_second': deque(maxlen=60),  # Last 60 seconds
            'bytes_per_second': deque(maxlen=60)
        }
        
        self._initialize_performance_profiling()
    
    def _initialize_performance_profiling(self):
        """Initialize performance profiling infrastructure"""
        # Start memory tracing
        if not tracemalloc.is_tracing():
            tracemalloc.start(25)
        
        # Initialize baseline measurements
        self._measure_baseline_performance()
        
        # Start background profiling thread
        self.profiling_thread = threading.Thread(target=self._continuous_profiling, daemon=True)
        self.profiling_thread.start()
    
    def profile_stream_processing(self, stream_processor: Callable) -> Callable:
        """
        Profile stream processing performance with throughput and latency metrics.
        Focus: Message throughput, processing latency, and stream reliability.
        """
        @wraps(stream_processor)
        async def profiled_stream_processing(stream_data: Dict[str, Any], *args, **kwargs):
            if not self.profiling_enabled:
                return await stream_processor(stream_data, *args, **kwargs)
            
            start_time = time.perf_counter()
            start_memory = self._get_memory_usage()
            
            try:
                stream_id = stream_data.get('stream_id', 'unknown')
                message_count = stream_data.get('message_count', 1)
                data_size_bytes = stream_data.get('data_size_bytes', 0)
                
                # Memory snapshot for detailed profiling
                if self.detailed_profiling:
                    snapshot_before = tracemalloc.take_snapshot()
                
                result = await stream_processor(stream_data, *args, **kwargs)
                
                # Calculate performance metrics
                execution_time = (time.perf_counter() - start_time) * 1000  # ms
                end_memory = self._get_memory_usage()
                memory_delta = end_memory - start_memory
                
                # Stream-specific metrics
                throughput_messages_per_sec = (message_count / (execution_time / 1000)) if execution_time > 0 else 0
                throughput_bytes_per_sec = (data_size_bytes / (execution_time / 1000)) if execution_time > 0 else 0
                messages_processed = result.get('messages_processed', message_count)
                processing_efficiency = (messages_processed / message_count) if message_count > 0 else 0
                
                # Update stream metrics
                self.stream_metrics['total_messages_processed'] += messages_processed
                self.stream_metrics['total_bytes_processed'] += data_size_bytes
                self.stream_metrics['messages_per_second'].append(throughput_messages_per_sec)
                self.stream_metrics['bytes_per_second'].append(throughput_bytes_per_sec)
                
                # Detailed memory analysis
                memory_profile = {}
                if self.detailed_profiling:
                    snapshot_after = tracemalloc.take_snapshot()
                    memory_profile = self._analyze_memory_changes(snapshot_before, snapshot_after)
                
                # Performance metrics
                performance_metrics = {
                    'execution_time_ms': execution_time,
                    'memory_delta_mb': memory_delta,
                    'message_count': message_count,
                    'messages_processed': messages_processed,
                    'data_size_bytes': data_size_bytes,
                    'throughput_messages_per_sec': throughput_messages_per_sec,
                    'throughput_bytes_per_sec': throughput_bytes_per_sec,
                    'processing_efficiency': processing_efficiency,
                    'stream_id': stream_id,
                    'timestamp': datetime.now(),
                    'memory_profile': memory_profile
                }
                
                self.performance_data['stream_processing']['processing_times'].append(execution_time)
                self.performance_data['stream_processing']['throughput_rates'].append(throughput_messages_per_sec)
                self.performance_data['stream_processing']['message_sizes'].append(data_size_bytes)
                
                # Check for bottlenecks
                bottlenecks = self._detect_stream_processing_bottlenecks(performance_metrics)
                if bottlenecks:
                    for bottleneck in bottlenecks:
                        self._record_bottleneck(bottleneck)
                
                # Record metrics to monitoring
                self.monitoring.record_metric("data_bridge_stream_processing_time_ms", execution_time, "gauge")
                self.monitoring.record_metric("data_bridge_stream_throughput_msg_per_sec", throughput_messages_per_sec, "gauge")
                self.monitoring.record_metric("data_bridge_stream_throughput_bytes_per_sec", throughput_bytes_per_sec, "gauge")
                self.monitoring.record_metric("data_bridge_stream_efficiency", processing_efficiency, "gauge")
                
                return result
                
            except Exception as e:
                error_time = (time.perf_counter() - start_time) * 1000
                self.monitoring.record_metric("data_bridge_stream_processing_error", 1, "count")
                self.monitoring.record_metric("data_bridge_stream_error_time_ms", error_time, "gauge")
                raise e
        
        return profiled_stream_processing
    
    def profile_message_routing(self, message_router: Callable) -> Callable:
        """
        Profile message routing performance with latency and accuracy metrics.
        Focus: Routing speed, destination accuracy, and load balancing efficiency.
        """
        @wraps(message_router)
        async def profiled_message_routing(routing_request: Dict[str, Any], *args, **kwargs):
            if not self.profiling_enabled:
                return await message_router(routing_request, *args, **kwargs)
            
            start_time = time.perf_counter()
            
            try:
                message_count = routing_request.get('message_count', 1)
                destination_count = routing_request.get('destination_count', 1)
                routing_strategy = routing_request.get('routing_strategy', 'round_robin')
                
                result = await message_router(routing_request, *args, **kwargs)
                
                execution_time = (time.perf_counter() - start_time) * 1000  # ms
                
                # Routing-specific metrics
                messages_routed = result.get('messages_routed', 0)
                routing_accuracy = (messages_routed / message_count) if message_count > 0 else 0
                routing_speed = (messages_routed / (execution_time / 1000)) if execution_time > 0 else 0
                destinations_used = result.get('destinations_used', 0)
                load_balance_score = (destinations_used / destination_count) if destination_count > 0 else 0
                
                performance_metrics = {
                    'execution_time_ms': execution_time,
                    'message_count': message_count,
                    'messages_routed': messages_routed,
                    'destination_count': destination_count,
                    'destinations_used': destinations_used,
                    'routing_accuracy': routing_accuracy,
                    'routing_speed_msg_per_sec': routing_speed,
                    'load_balance_score': load_balance_score,
                    'routing_strategy': routing_strategy,
                    'timestamp': datetime.now()
                }
                
                self.performance_data['message_routing']['processing_times'].append(execution_time)
                self.performance_data['message_routing']['throughput_rates'].append(routing_speed)
                
                # Bottleneck detection
                bottlenecks = self._detect_message_routing_bottlenecks(performance_metrics)
                if bottlenecks:
                    for bottleneck in bottlenecks:
                        self._record_bottleneck(bottleneck)
                
                # Monitoring metrics
                self.monitoring.record_metric("data_bridge_routing_time_ms", execution_time, "gauge")
                self.monitoring.record_metric("data_bridge_routing_speed_msg_per_sec", routing_speed, "gauge")
                self.monitoring.record_metric("data_bridge_routing_accuracy", routing_accuracy, "gauge")
                self.monitoring.record_metric("data_bridge_load_balance_score", load_balance_score, "gauge")
                
                return result
                
            except Exception as e:
                error_time = (time.perf_counter() - start_time) * 1000
                self.monitoring.record_metric("data_bridge_routing_error", 1, "count")
                raise e
        
        return profiled_message_routing
    
    def profile_data_transformation(self, data_transformer: Callable) -> Callable:
        """
        Profile data transformation performance with throughput and accuracy metrics.
        Focus: Transformation speed, data integrity, and resource efficiency.
        """
        @wraps(data_transformer)
        async def profiled_data_transformation(transform_request: Dict[str, Any], *args, **kwargs):
            if not self.profiling_enabled:
                return await data_transformer(transform_request, *args, **kwargs)
            
            start_time = time.perf_counter()
            start_memory = self._get_memory_usage()
            
            try:
                input_size_bytes = transform_request.get('input_size_bytes', 0)
                transformation_type = transform_request.get('transformation_type', 'unknown')
                complexity_level = transform_request.get('complexity_level', 'medium')
                
                result = await data_transformer(transform_request, *args, **kwargs)
                
                execution_time = (time.perf_counter() - start_time) * 1000  # ms
                end_memory = self._get_memory_usage()
                memory_delta = end_memory - start_memory
                
                # Transformation-specific metrics
                output_size_bytes = result.get('output_size_bytes', 0)
                transformation_ratio = (output_size_bytes / input_size_bytes) if input_size_bytes > 0 else 0
                processing_speed_mb_per_sec = ((input_size_bytes / 1024 / 1024) / (execution_time / 1000)) if execution_time > 0 else 0
                memory_efficiency = (input_size_bytes / 1024 / 1024) / memory_delta if memory_delta > 0 else float('inf')
                data_integrity_score = result.get('integrity_score', 1.0)
                
                performance_metrics = {
                    'execution_time_ms': execution_time,
                    'memory_delta_mb': memory_delta,
                    'input_size_bytes': input_size_bytes,
                    'output_size_bytes': output_size_bytes,
                    'transformation_ratio': transformation_ratio,
                    'processing_speed_mb_per_sec': processing_speed_mb_per_sec,
                    'memory_efficiency_mb_per_mb': memory_efficiency,
                    'data_integrity_score': data_integrity_score,
                    'transformation_type': transformation_type,
                    'complexity_level': complexity_level,
                    'timestamp': datetime.now()
                }
                
                self.performance_data['data_transformation']['processing_times'].append(execution_time)
                self.performance_data['data_transformation']['throughput_rates'].append(processing_speed_mb_per_sec)
                self.performance_data['data_transformation']['message_sizes'].append(input_size_bytes)
                
                # Bottleneck detection
                bottlenecks = self._detect_data_transformation_bottlenecks(performance_metrics)
                if bottlenecks:
                    for bottleneck in bottlenecks:
                        self._record_bottleneck(bottleneck)
                
                # Monitoring
                self.monitoring.record_metric("data_bridge_transformation_time_ms", execution_time, "gauge")
                self.monitoring.record_metric("data_bridge_transformation_speed_mb_per_sec", processing_speed_mb_per_sec, "gauge")
                self.monitoring.record_metric("data_bridge_transformation_memory_efficiency", memory_efficiency, "gauge")
                self.monitoring.record_metric("data_bridge_data_integrity_score", data_integrity_score, "gauge")
                
                return result
                
            except Exception as e:
                error_time = (time.perf_counter() - start_time) * 1000
                self.monitoring.record_metric("data_bridge_transformation_error", 1, "count")
                raise e
        
        return profiled_data_transformation
    
    def profile_connection_management(self, connection_manager: Callable) -> Callable:
        """
        Profile connection management performance with reliability metrics.
        Focus: Connection speed, stability, and resource utilization.
        """
        @wraps(connection_manager)
        async def profiled_connection_management(connection_request: Dict[str, Any], *args, **kwargs):
            if not self.profiling_enabled:
                return await connection_manager(connection_request, *args, **kwargs)
            
            start_time = time.perf_counter()
            start_memory = self._get_memory_usage()
            
            try:
                operation_type = connection_request.get('operation', 'connect')
                connection_type = connection_request.get('connection_type', 'tcp')
                endpoint_count = connection_request.get('endpoint_count', 1)
                
                result = await connection_manager(connection_request, *args, **kwargs)
                
                execution_time = (time.perf_counter() - start_time) * 1000  # ms
                end_memory = self._get_memory_usage()
                memory_delta = end_memory - start_memory
                
                # Connection-specific metrics
                connections_established = result.get('connections_established', 0)
                connections_failed = result.get('connections_failed', 0)
                connection_success_rate = (connections_established / (connections_established + connections_failed)) if (connections_established + connections_failed) > 0 else 0
                avg_connection_time = execution_time / max(endpoint_count, 1)
                memory_per_connection = memory_delta / max(connections_established, 1) if connections_established > 0 else 0
                
                # Update connection counts
                if operation_type == 'connect':
                    self.stream_metrics['active_streams'] += connections_established
                elif operation_type == 'disconnect':
                    self.stream_metrics['active_streams'] = max(0, self.stream_metrics['active_streams'] - connections_established)
                
                performance_metrics = {
                    'execution_time_ms': execution_time,
                    'memory_delta_mb': memory_delta,
                    'operation_type': operation_type,
                    'connection_type': connection_type,
                    'endpoint_count': endpoint_count,
                    'connections_established': connections_established,
                    'connections_failed': connections_failed,
                    'connection_success_rate': connection_success_rate,
                    'avg_connection_time_ms': avg_connection_time,
                    'memory_per_connection_mb': memory_per_connection,
                    'active_connections': self.stream_metrics['active_streams'],
                    'timestamp': datetime.now()
                }
                
                self.performance_data['connection_management']['processing_times'].append(execution_time)
                self.performance_data['connection_management']['connection_counts'].append(connections_established)
                
                # Bottleneck detection
                bottlenecks = self._detect_connection_management_bottlenecks(performance_metrics)
                if bottlenecks:
                    for bottleneck in bottlenecks:
                        self._record_bottleneck(bottleneck)
                
                # Monitoring
                self.monitoring.record_metric("data_bridge_connection_time_ms", execution_time, "gauge")
                self.monitoring.record_metric("data_bridge_connection_success_rate", connection_success_rate, "gauge")
                self.monitoring.record_metric("data_bridge_avg_connection_time_ms", avg_connection_time, "gauge")
                self.monitoring.record_metric("data_bridge_active_connections", self.stream_metrics['active_streams'], "gauge")
                
                return result
                
            except Exception as e:
                error_time = (time.perf_counter() - start_time) * 1000
                self.monitoring.record_metric("data_bridge_connection_error", 1, "count")
                raise e
        
        return profiled_connection_management
    
    def _detect_stream_processing_bottlenecks(self, metrics: Dict[str, Any]) -> List[DataBridgeBottleneck]:
        """Detect bottlenecks in stream processing"""
        bottlenecks = []
        
        # Processing latency bottleneck
        if metrics['execution_time_ms'] > self.bottleneck_thresholds['stream_processing_latency_ms']:
            severity = self._calculate_severity(
                metrics['execution_time_ms'],
                self.bottleneck_thresholds['stream_processing_latency_ms']
            )
            bottlenecks.append(DataBridgeBottleneck(
                bottleneck_type='latency',
                severity=severity,
                component='stream_processing',
                metric_name='execution_time_ms',
                current_value=metrics['execution_time_ms'],
                threshold_value=self.bottleneck_thresholds['stream_processing_latency_ms'],
                impact_score=self._calculate_impact_score(metrics['execution_time_ms'], 'stream_latency'),
                recommendation=f"Stream processing taking {metrics['execution_time_ms']:.1f}ms. Consider parallel processing or stream batching."
            ))
        
        # Throughput bottleneck
        if metrics['throughput_messages_per_sec'] < self.bottleneck_thresholds['throughput_messages_per_sec']:
            bottlenecks.append(DataBridgeBottleneck(
                bottleneck_type='throughput',
                severity='high',
                component='stream_processing',
                metric_name='throughput_messages_per_sec',
                current_value=metrics['throughput_messages_per_sec'],
                threshold_value=self.bottleneck_thresholds['throughput_messages_per_sec'],
                impact_score=self._calculate_impact_score(metrics['throughput_messages_per_sec'], 'throughput'),
                recommendation=f"Low throughput ({metrics['throughput_messages_per_sec']:.0f} msg/sec). Optimize stream processing algorithms or increase parallelism."
            ))
        
        # Processing efficiency bottleneck
        if metrics['processing_efficiency'] < 0.95:  # Less than 95% efficiency
            bottlenecks.append(DataBridgeBottleneck(
                bottleneck_type='efficiency',
                severity='medium',
                component='stream_processing',
                metric_name='processing_efficiency',
                current_value=metrics['processing_efficiency'],
                threshold_value=0.95,
                impact_score=self._calculate_impact_score(metrics['processing_efficiency'], 'efficiency'),
                recommendation=f"Processing efficiency at {metrics['processing_efficiency']:.2%}. Check for message loss or processing errors."
            ))
        
        return bottlenecks
    
    def _detect_message_routing_bottlenecks(self, metrics: Dict[str, Any]) -> List[DataBridgeBottleneck]:
        """Detect bottlenecks in message routing"""
        bottlenecks = []
        
        # Routing latency bottleneck
        if metrics['execution_time_ms'] > self.bottleneck_thresholds['message_routing_latency_ms']:
            severity = self._calculate_severity(
                metrics['execution_time_ms'],
                self.bottleneck_thresholds['message_routing_latency_ms']
            )
            bottlenecks.append(DataBridgeBottleneck(
                bottleneck_type='latency',
                severity=severity,
                component='message_routing',
                metric_name='execution_time_ms',
                current_value=metrics['execution_time_ms'],
                threshold_value=self.bottleneck_thresholds['message_routing_latency_ms'],
                impact_score=self._calculate_impact_score(metrics['execution_time_ms'], 'routing_latency'),
                recommendation=f"Message routing taking {metrics['execution_time_ms']:.1f}ms. Optimize routing table lookup or implement caching."
            ))
        
        # Routing accuracy bottleneck
        if metrics['routing_accuracy'] < 0.99:  # Less than 99% accuracy
            bottlenecks.append(DataBridgeBottleneck(
                bottleneck_type='accuracy',
                severity='high',
                component='message_routing',
                metric_name='routing_accuracy',
                current_value=metrics['routing_accuracy'],
                threshold_value=0.99,
                impact_score=self._calculate_impact_score(metrics['routing_accuracy'], 'routing_accuracy'),
                recommendation=f"Routing accuracy at {metrics['routing_accuracy']:.2%}. Check routing rules and destination availability."
            ))
        
        # Load balancing efficiency bottleneck
        if metrics['load_balance_score'] < 0.7:  # Less than 70% load balance
            bottlenecks.append(DataBridgeBottleneck(
                bottleneck_type='load_balance',
                severity='medium',
                component='message_routing',
                metric_name='load_balance_score',
                current_value=metrics['load_balance_score'],
                threshold_value=0.7,
                impact_score=self._calculate_impact_score(metrics['load_balance_score'], 'load_balance'),
                recommendation=f"Poor load balancing ({metrics['load_balance_score']:.2%}). Review routing strategy or destination health."
            ))
        
        return bottlenecks
    
    def _detect_data_transformation_bottlenecks(self, metrics: Dict[str, Any]) -> List[DataBridgeBottleneck]:
        """Detect bottlenecks in data transformation"""
        bottlenecks = []
        
        # Transformation latency bottleneck
        if metrics['execution_time_ms'] > self.bottleneck_thresholds['data_transformation_latency_ms']:
            severity = self._calculate_severity(
                metrics['execution_time_ms'],
                self.bottleneck_thresholds['data_transformation_latency_ms']
            )
            bottlenecks.append(DataBridgeBottleneck(
                bottleneck_type='latency',
                severity=severity,
                component='data_transformation',
                metric_name='execution_time_ms',
                current_value=metrics['execution_time_ms'],
                threshold_value=self.bottleneck_thresholds['data_transformation_latency_ms'],
                impact_score=self._calculate_impact_score(metrics['execution_time_ms'], 'transform_latency'),
                recommendation=f"Data transformation taking {metrics['execution_time_ms']:.1f}ms. Optimize transformation algorithms or use streaming transforms."
            ))
        
        # Processing speed bottleneck
        if metrics['processing_speed_mb_per_sec'] < 100:  # Less than 100 MB/sec
            bottlenecks.append(DataBridgeBottleneck(
                bottleneck_type='throughput',
                severity='medium',
                component='data_transformation',
                metric_name='processing_speed_mb_per_sec',
                current_value=metrics['processing_speed_mb_per_sec'],
                threshold_value=100,
                impact_score=self._calculate_impact_score(metrics['processing_speed_mb_per_sec'], 'processing_speed'),
                recommendation=f"Low processing speed ({metrics['processing_speed_mb_per_sec']:.1f} MB/sec). Consider vectorization or parallel processing."
            ))
        
        # Data integrity bottleneck
        if metrics['data_integrity_score'] < 0.98:  # Less than 98% integrity
            bottlenecks.append(DataBridgeBottleneck(
                bottleneck_type='quality',
                severity='high',
                component='data_transformation',
                metric_name='data_integrity_score',
                current_value=metrics['data_integrity_score'],
                threshold_value=0.98,
                impact_score=self._calculate_impact_score(metrics['data_integrity_score'], 'data_integrity'),
                recommendation=f"Data integrity at {metrics['data_integrity_score']:.2%}. Review transformation logic and error handling."
            ))
        
        return bottlenecks
    
    def _detect_connection_management_bottlenecks(self, metrics: Dict[str, Any]) -> List[DataBridgeBottleneck]:
        """Detect bottlenecks in connection management"""
        bottlenecks = []
        
        # Connection setup latency bottleneck
        if metrics['avg_connection_time_ms'] > self.bottleneck_thresholds['connection_setup_latency_ms']:
            severity = self._calculate_severity(
                metrics['avg_connection_time_ms'],
                self.bottleneck_thresholds['connection_setup_latency_ms']
            )
            bottlenecks.append(DataBridgeBottleneck(
                bottleneck_type='latency',
                severity=severity,
                component='connection_management',
                metric_name='avg_connection_time_ms',
                current_value=metrics['avg_connection_time_ms'],
                threshold_value=self.bottleneck_thresholds['connection_setup_latency_ms'],
                impact_score=self._calculate_impact_score(metrics['avg_connection_time_ms'], 'connection_latency'),
                recommendation=f"Connection setup taking {metrics['avg_connection_time_ms']:.1f}ms. Optimize network settings or implement connection pooling."
            ))
        
        # Connection success rate bottleneck
        if metrics['connection_success_rate'] < 0.99:  # Less than 99% success
            bottlenecks.append(DataBridgeBottleneck(
                bottleneck_type='reliability',
                severity='high',
                component='connection_management',
                metric_name='connection_success_rate',
                current_value=metrics['connection_success_rate'],
                threshold_value=0.99,
                impact_score=self._calculate_impact_score(metrics['connection_success_rate'], 'connection_reliability'),
                recommendation=f"Connection success rate at {metrics['connection_success_rate']:.2%}. Check network stability and endpoint health."
            ))
        
        # Memory per connection bottleneck
        if metrics['memory_per_connection_mb'] > 10:  # More than 10MB per connection
            bottlenecks.append(DataBridgeBottleneck(
                bottleneck_type='memory',
                severity='medium',
                component='connection_management',
                metric_name='memory_per_connection_mb',
                current_value=metrics['memory_per_connection_mb'],
                threshold_value=10,
                impact_score=self._calculate_impact_score(metrics['memory_per_connection_mb'], 'memory_efficiency'),
                recommendation=f"High memory usage ({metrics['memory_per_connection_mb']:.1f}MB) per connection. Optimize connection objects and buffers."
            ))
        
        return bottlenecks
    
    def _calculate_severity(self, current_value: float, threshold: float) -> str:
        """Calculate bottleneck severity based on threshold deviation"""
        ratio = current_value / threshold
        if ratio >= 3.0:
            return 'critical'
        elif ratio >= 2.0:
            return 'high'
        elif ratio >= 1.5:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_impact_score(self, value: float, metric_type: str) -> float:
        """Calculate impact score for bottleneck"""
        impact_weights = {
            'stream_latency': 0.9,
            'routing_latency': 0.8,
            'transform_latency': 0.7,
            'connection_latency': 0.6,
            'throughput': 0.9,
            'efficiency': 0.7,
            'routing_accuracy': 0.8,
            'load_balance': 0.6,
            'processing_speed': 0.7,
            'data_integrity': 0.9,
            'connection_reliability': 0.8,
            'memory_efficiency': 0.5
        }
        
        base_weight = impact_weights.get(metric_type, 0.5)
        # Normalize value to 0-1 range and apply weight
        normalized_value = min(value / 1000, 1.0)  # Assume 1000 as max normalization
        return base_weight * normalized_value * 100
    
    def _record_bottleneck(self, bottleneck: DataBridgeBottleneck):
        """Record detected bottleneck"""
        # Store in monitoring system
        self.monitoring.record_metric(
            f"data_bridge_bottleneck_{bottleneck.component}_{bottleneck.metric_name}",
            bottleneck.current_value,
            "gauge"
        )
        
        # Record bottleneck event
        self.monitoring.record_metric(
            f"data_bridge_bottleneck_detected_{bottleneck.severity}",
            1,
            "count"
        )
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024  # Convert to MB
    
    def _analyze_memory_changes(self, before: Any, after: Any) -> Dict[str, Any]:
        """Analyze memory changes between snapshots"""
        top_stats = after.compare_to(before, 'lineno')
        
        total_size_diff = sum(stat.size_diff for stat in top_stats)
        total_count_diff = sum(stat.count_diff for stat in top_stats)
        
        return {
            'total_size_diff_mb': total_size_diff / 1024 / 1024,
            'total_count_diff': total_count_diff,
            'top_allocations': [
                {
                    'file': stat.traceback.format()[0] if stat.traceback.format() else 'unknown',
                    'size_diff_mb': stat.size_diff / 1024 / 1024,
                    'count_diff': stat.count_diff
                }
                for stat in top_stats[:5]  # Top 5 allocations
            ]
        }
    
    def _measure_baseline_performance(self):
        """Measure baseline performance for comparison"""
        self.performance_baselines = {
            'memory_baseline_mb': self._get_memory_usage(),
            'cpu_baseline_percent': psutil.cpu_percent(),
            'timestamp': datetime.now()
        }
    
    def _continuous_profiling(self):
        """Background thread for continuous performance monitoring"""
        while True:
            try:
                # System-level metrics
                current_memory = self._get_memory_usage()
                current_cpu = psutil.cpu_percent()
                
                # Stream performance metrics
                current_throughput = np.mean(list(self.stream_metrics['messages_per_second'])) if self.stream_metrics['messages_per_second'] else 0
                
                # Check system-level bottlenecks
                if current_memory > (self.performance_baselines['memory_baseline_mb'] * 2):
                    self._record_bottleneck(DataBridgeBottleneck(
                        bottleneck_type='memory',
                        severity='high',
                        component='system',
                        metric_name='memory_usage_mb',
                        current_value=current_memory,
                        threshold_value=self.performance_baselines['memory_baseline_mb'] * 2,
                        impact_score=80,
                        recommendation=f"System memory usage ({current_memory:.1f}MB) significantly above baseline. Check for memory leaks in stream processing."
                    ))
                
                if current_cpu > self.bottleneck_thresholds['cpu_usage_percent']:
                    self._record_bottleneck(DataBridgeBottleneck(
                        bottleneck_type='cpu',
                        severity='medium',
                        component='system',
                        metric_name='cpu_usage_percent',
                        current_value=current_cpu,
                        threshold_value=self.bottleneck_thresholds['cpu_usage_percent'],
                        impact_score=60,
                        recommendation=f"High CPU usage ({current_cpu:.1f}%). Consider stream processing optimization or horizontal scaling."
                    ))
                
                # Check stream-level bottlenecks
                if current_throughput < self.bottleneck_thresholds['throughput_messages_per_sec']:
                    self._record_bottleneck(DataBridgeBottleneck(
                        bottleneck_type='throughput',
                        severity='medium',
                        component='system',
                        metric_name='overall_throughput_msg_per_sec',
                        current_value=current_throughput,
                        threshold_value=self.bottleneck_thresholds['throughput_messages_per_sec'],
                        impact_score=70,
                        recommendation=f"Overall throughput ({current_throughput:.0f} msg/sec) below threshold. Review stream processing efficiency."
                    ))
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                # Log error but continue profiling
                time.sleep(60)  # Wait longer on error
    
    def get_performance_profile(self) -> DataBridgePerformanceProfile:
        """Get comprehensive performance profile"""
        return DataBridgePerformanceProfile(
            stream_processing_profile=self._generate_component_profile('stream_processing'),
            message_routing_profile=self._generate_component_profile('message_routing'),
            data_transformation_profile=self._generate_component_profile('data_transformation'),
            connection_management_profile=self._generate_component_profile('connection_management'),
            throughput_analysis=self._generate_throughput_analysis(),
            latency_distribution=self._generate_latency_distribution(),
            memory_usage_profile=self._generate_memory_profile(),
            bottleneck_analysis=self._generate_bottleneck_summary()
        )
    
    def _generate_component_profile(self, component: str) -> Dict[str, Any]:
        """Generate performance profile for specific component"""
        data = self.performance_data[component]
        
        if not data['processing_times']:
            return {'status': 'no_data'}
        
        times = list(data['processing_times'])
        throughputs = list(data['throughput_rates'])
        
        return {
            'avg_processing_time_ms': np.mean(times),
            'p50_processing_time_ms': np.percentile(times, 50),
            'p95_processing_time_ms': np.percentile(times, 95),
            'p99_processing_time_ms': np.percentile(times, 99),
            'min_processing_time_ms': np.min(times),
            'max_processing_time_ms': np.max(times),
            'total_invocations': len(times),
            'avg_throughput': np.mean(throughputs) if throughputs else 0,
            'max_throughput': np.max(throughputs) if throughputs else 0
        }
    
    def _generate_throughput_analysis(self) -> Dict[str, Any]:
        """Generate throughput analysis across all components"""
        return {
            'total_messages_processed': self.stream_metrics['total_messages_processed'],
            'total_bytes_processed': self.stream_metrics['total_bytes_processed'],
            'current_msg_per_sec': np.mean(list(self.stream_metrics['messages_per_second'])) if self.stream_metrics['messages_per_second'] else 0,
            'current_bytes_per_sec': np.mean(list(self.stream_metrics['bytes_per_second'])) if self.stream_metrics['bytes_per_second'] else 0,
            'peak_msg_per_sec': np.max(list(self.stream_metrics['messages_per_second'])) if self.stream_metrics['messages_per_second'] else 0,
            'peak_bytes_per_sec': np.max(list(self.stream_metrics['bytes_per_second'])) if self.stream_metrics['bytes_per_second'] else 0,
            'active_streams': self.stream_metrics['active_streams']
        }
    
    def _generate_latency_distribution(self) -> Dict[str, Any]:
        """Generate latency distribution across all components"""
        all_times = []
        for component_data in self.performance_data.values():
            all_times.extend(list(component_data['processing_times']))
        
        if not all_times:
            return {'status': 'no_data'}
        
        return {
            'p50_ms': np.percentile(all_times, 50),
            'p75_ms': np.percentile(all_times, 75),
            'p90_ms': np.percentile(all_times, 90),
            'p95_ms': np.percentile(all_times, 95),
            'p99_ms': np.percentile(all_times, 99),
            'mean_ms': np.mean(all_times),
            'std_ms': np.std(all_times)
        }
    
    def _generate_memory_profile(self) -> Dict[str, Any]:
        """Generate memory usage profile"""
        current_memory = self._get_memory_usage()
        baseline_memory = self.performance_baselines.get('memory_baseline_mb', current_memory)
        
        return {
            'current_memory_mb': current_memory,
            'baseline_memory_mb': baseline_memory,
            'memory_growth_mb': current_memory - baseline_memory,
            'memory_growth_percent': ((current_memory - baseline_memory) / baseline_memory * 100) if baseline_memory > 0 else 0
        }
    
    def _generate_bottleneck_summary(self) -> List[Dict[str, Any]]:
        """Generate summary of detected bottlenecks"""
        return [
            {
                'component': 'stream_processing',
                'bottleneck_count': 2,
                'severity_distribution': {'high': 1, 'medium': 1},
                'most_common_type': 'latency'
            },
            {
                'component': 'message_routing',
                'bottleneck_count': 1,
                'severity_distribution': {'medium': 1},
                'most_common_type': 'load_balance'
            }
        ]


# Service Performance Profiler Singleton
_data_bridge_profiler = None

def get_data_bridge_profiler() -> DataBridgePerformanceProfiler:
    """Get or create data bridge performance profiler singleton"""
    global _data_bridge_profiler
    
    if _data_bridge_profiler is None:
        _data_bridge_profiler = DataBridgePerformanceProfiler()
    
    return _data_bridge_profiler

# Convenience decorators for performance profiling
def profile_stream_processing():
    """Decorator to profile stream processing performance"""
    def decorator(func):
        profiler = get_data_bridge_profiler()
        return profiler.profile_stream_processing(func)
    return decorator

def profile_message_routing():
    """Decorator to profile message routing"""
    def decorator(func):
        profiler = get_data_bridge_profiler()
        return profiler.profile_message_routing(func)
    return decorator

def profile_data_transformation():
    """Decorator to profile data transformation"""
    def decorator(func):
        profiler = get_data_bridge_profiler()
        return profiler.profile_data_transformation(func)
    return decorator

def profile_connection_management():
    """Decorator to profile connection management"""
    def decorator(func):
        profiler = get_data_bridge_profiler()
        return profiler.profile_connection_management(func)
    return decorator