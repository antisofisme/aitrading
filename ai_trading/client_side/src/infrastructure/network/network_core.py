"""
network_core.py - Network Communication System

🎯 PURPOSE:
Business: Reliable network communication for trading data and service integration
Technical: Advanced networking with connection pooling, retry logic, and monitoring
Domain: Network Communication/Connection Management/Service Integration

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:27.874Z
Session: client-side-ai-brain-full-compliance
Confidence: 91%
Complexity: high

🧩 PATTERNS USED:
- AI_BRAIN_NETWORK_SYSTEM: Advanced networking with connection pooling
- RESILIENT_COMMUNICATION: Retry logic and connection management

📦 DEPENDENCIES:
Internal: logger_manager, error_manager, security_core
External: aiohttp, asyncio, ssl, socket, urllib3

💡 AI DECISION REASONING:
Trading systems require reliable network communication with automatic retry and connection management for continuous operation.

🚀 USAGE:
network_core.make_request("https://api.example.com/data")

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

import asyncio
import aiohttp
import json
import ssl
import time
import threading
from typing import Dict, Any, Optional, List, Union, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
from pathlib import Path
import hashlib
import uuid

class ConnectionType(Enum):
    """Connection types"""
    HTTP = "http"
    HTTPS = "https"
    WEBSOCKET = "websocket"
    TCP = "tcp"
    UDP = "udp"
    KAFKA = "kafka"
    REDIS = "redis"

class RetryStrategy(Enum):
    """Retry strategies"""
    NONE = "none"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    ADAPTIVE = "adaptive"

class HealthStatus(Enum):
    """Service health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class ServiceEndpoint:
    """Service endpoint configuration"""
    name: str
    url: str
    connection_type: ConnectionType
    timeout: float = 30.0
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    max_retries: int = 3
    health_check_url: Optional[str] = None
    headers: Dict[str, str] = None
    auth: Optional[Dict[str, Any]] = None
    priority: int = 100  # Lower number = higher priority
    enabled: bool = True
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {}
        if self.metadata is None:
            self.metadata = {}

@dataclass
class NetworkRequest:
    """Network request with AI Brain optimization"""
    id: str
    endpoint: str
    method: str
    url: str
    data: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    timeout: Optional[float] = None
    priority: int = 100
    correlation_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}

@dataclass
class NetworkResponse:
    """Network response with analysis"""
    request_id: str
    status_code: int
    data: Optional[Any] = None
    headers: Optional[Dict[str, str]] = None
    error: Optional[str] = None
    duration: float = 0.0
    timestamp: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def is_success(self) -> bool:
        """Check if response indicates success"""
        return 200 <= self.status_code < 300
    
    @property
    def is_client_error(self) -> bool:
        """Check if response indicates client error"""
        return 400 <= self.status_code < 500
    
    @property
    def is_server_error(self) -> bool:
        """Check if response indicates server error"""
        return 500 <= self.status_code < 600

@dataclass
class ServiceHealth:
    """Service health information"""
    endpoint_name: str
    status: HealthStatus
    last_check: datetime
    response_time: Optional[float] = None
    error_rate: float = 0.0
    availability: float = 100.0
    consecutive_failures: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class NetworkStats:
    """Network system statistics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    requests_by_endpoint: Dict[str, int] = None
    error_rates: Dict[str, float] = None
    active_connections: int = 0
    
    def __post_init__(self):
        if self.requests_by_endpoint is None:
            self.requests_by_endpoint = defaultdict(int)
        if self.error_rates is None:
            self.error_rates = defaultdict(float)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_requests > 0:
            return self.successful_requests / self.total_requests
        return 0.0

class NetworkCore:
    """
    AI Brain Network Core System
    Intelligent service communication with adaptive routing and health monitoring
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        # Service management
        self._endpoints: Dict[str, ServiceEndpoint] = {}
        self._service_health: Dict[str, ServiceHealth] = {}
        self._request_queue: asyncio.Queue = None
        self._response_cache: Dict[str, Tuple[NetworkResponse, datetime]] = {}
        
        # AI Brain features
        self._request_patterns: Dict[str, List[datetime]] = defaultdict(list)
        self._response_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self._error_patterns: Dict[str, List[datetime]] = defaultdict(list)
        self._adaptive_timeouts: Dict[str, float] = {}
        
        # Connection pooling
        self._session_pool: Dict[str, aiohttp.ClientSession] = {}
        self._connection_limits = {
            'max_connections': 100,
            'max_connections_per_host': 10,
            'ttl_dns_cache': 300,
            'use_dns_cache': True
        }
        
        # Configuration
        self._enable_caching = True
        self._cache_ttl = 300  # 5 minutes
        self._enable_health_checks = True
        self._health_check_interval = 60  # 1 minute
        self._enable_adaptive_routing = True
        
        # Statistics
        self._stats = NetworkStats()
        self._request_history: deque = deque(maxlen=10000)
        
        # Control
        self._running = False
        self._background_tasks: List[asyncio.Task] = []
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Initialize system
        self._initialize_network_core()
    
    @classmethod
    def get_instance(cls) -> 'NetworkCore':
        """Singleton pattern with thread safety"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def _initialize_network_core(self):
        """Initialize network core system"""
        print("🌐 AI Brain Network Core initializing...")
        
        # Load default endpoints for MT5 Trading Client
        self._load_default_endpoints()
        
        print("🚀 Network Core initialized")
    
    async def start(self):
        """Start the network core system"""
        if self._running:
            return
        
        self._running = True
        
        # Initialize request queue
        if self._request_queue is None:
            self._request_queue = asyncio.Queue(maxsize=1000)
        
        # Create session pools
        await self._create_session_pools()
        
        # Start background tasks
        self._background_tasks = [
            asyncio.create_task(self._request_processor()),
            asyncio.create_task(self._health_monitor()),
            asyncio.create_task(self._performance_analyzer()),
            asyncio.create_task(self._cache_cleanup())
        ]
        
        print("🌐 Network Core started")
    
    async def stop(self):
        """Stop the network core system"""
        if not self._running:
            return
        
        self._running = False
        
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        # Close session pools
        await self._close_session_pools()
        
        print("🛑 Network Core stopped")
    
    # ==================== ENDPOINT MANAGEMENT ====================
    
    def register_endpoint(self, endpoint: ServiceEndpoint) -> bool:
        """Register service endpoint"""
        try:
            with self._lock:
                self._endpoints[endpoint.name] = endpoint
                
                # Initialize health status
                self._service_health[endpoint.name] = ServiceHealth(
                    endpoint_name=endpoint.name,
                    status=HealthStatus.UNKNOWN,
                    last_check=datetime.now()
                )
                
                print(f"📝 Endpoint registered: {endpoint.name} -> {endpoint.url}")
                return True
                
        except Exception as e:
            print(f"❌ Failed to register endpoint {endpoint.name}: {e}")
            return False
    
    def unregister_endpoint(self, endpoint_name: str) -> bool:
        """Unregister service endpoint"""
        try:
            with self._lock:
                if endpoint_name in self._endpoints:
                    del self._endpoints[endpoint_name]
                
                if endpoint_name in self._service_health:
                    del self._service_health[endpoint_name]
                
                print(f"🗑️ Endpoint unregistered: {endpoint_name}")
                return True
            
            return False
                
        except Exception as e:
            print(f"❌ Failed to unregister endpoint {endpoint_name}: {e}")
            return False
    
    def get_endpoint(self, endpoint_name: str) -> Optional[ServiceEndpoint]:
        """Get service endpoint by name"""
        return self._endpoints.get(endpoint_name)
    
    def list_endpoints(self) -> List[str]:
        """List all registered endpoints"""
        return list(self._endpoints.keys())
    
    # ==================== REQUEST PROCESSING ====================
    
    async def request(self, endpoint_name: str, method: str, path: str = "",
                     data: Optional[Dict[str, Any]] = None,
                     headers: Optional[Dict[str, str]] = None,
                     timeout: Optional[float] = None,
                     priority: int = 100,
                     use_cache: bool = True) -> NetworkResponse:
        """Make network request with AI Brain optimization"""
        
        # Get endpoint
        endpoint = self._endpoints.get(endpoint_name)
        if not endpoint:
            return NetworkResponse(
                request_id=str(uuid.uuid4()),
                status_code=404,
                error=f"Endpoint '{endpoint_name}' not found"
            )
        
        if not endpoint.enabled:
            return NetworkResponse(
                request_id=str(uuid.uuid4()),
                status_code=503,
                error=f"Endpoint '{endpoint_name}' is disabled"
            )
        
        # Build request
        request = NetworkRequest(
            id=str(uuid.uuid4()),
            endpoint=endpoint_name,
            method=method.upper(),
            url=f"{endpoint.url.rstrip('/')}/{path.lstrip('/')}",
            data=data,
            headers={**endpoint.headers, **(headers or {})},
            timeout=timeout or endpoint.timeout,
            priority=priority,
            correlation_id=str(uuid.uuid4())
        )
        
        # Check cache if enabled
        if use_cache and self._enable_caching and method.upper() == 'GET':
            cached_response = self._get_cached_response(request)
            if cached_response:
                return cached_response
        
        # AI Brain optimization
        if self._enable_adaptive_routing:
            request = self._optimize_request(request, endpoint)
        
        # Execute request
        response = await self._execute_request(request, endpoint)
        
        # Cache response if appropriate
        if (use_cache and self._enable_caching and response.is_success and 
            method.upper() == 'GET'):
            self._cache_response(request, response)
        
        # Record request/response for learning
        self._record_request_response(request, response)
        
        return response
    
    async def _execute_request(self, request: NetworkRequest, endpoint: ServiceEndpoint) -> NetworkResponse:
        """Execute individual network request"""
        start_time = time.time()
        
        try:
            # Get session for endpoint
            session = await self._get_session(endpoint)
            
            # Prepare request parameters
            request_params = {
                'timeout': aiohttp.ClientTimeout(total=request.timeout),
                'headers': request.headers
            }
            
            # Add data based on method
            if request.method in ['POST', 'PUT', 'PATCH']:
                if request.data:
                    if isinstance(request.data, dict):
                        request_params['json'] = request.data
                    else:
                        request_params['data'] = request.data
            elif request.method == 'GET' and request.data:
                request_params['params'] = request.data
            
            # Execute request with retries
            response = await self._execute_with_retries(
                session, request, request_params, endpoint
            )
            
            duration = time.time() - start_time
            
            # Update statistics
            self._stats.total_requests += 1
            self._stats.requests_by_endpoint[endpoint.name] += 1
            
            if response.is_success:
                self._stats.successful_requests += 1
            else:
                self._stats.failed_requests += 1
            
            # Update average response time
            self._update_average_response_time(duration)
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Update statistics
            self._stats.total_requests += 1
            self._stats.failed_requests += 1
            
            return NetworkResponse(
                request_id=request.id,
                status_code=0,
                error=str(e),
                duration=duration
            )
    
    async def _execute_with_retries(self, session: aiohttp.ClientSession,
                                  request: NetworkRequest, request_params: Dict[str, Any],
                                  endpoint: ServiceEndpoint) -> NetworkResponse:
        """Execute request with retry logic"""
        
        last_error = None
        
        for attempt in range(endpoint.max_retries + 1):
            try:
                # Calculate delay for retry
                if attempt > 0:
                    delay = self._calculate_retry_delay(endpoint.retry_strategy, attempt)
                    await asyncio.sleep(delay)
                
                # Execute request
                async with session.request(request.method, request.url, **request_params) as resp:
                    
                    # Read response data
                    try:
                        if resp.content_type == 'application/json':
                            data = await resp.json()
                        else:
                            data = await resp.text()
                    except Exception:
                        data = None
                    
                    response = NetworkResponse(
                        request_id=request.id,
                        status_code=resp.status,
                        data=data,
                        headers=dict(resp.headers),
                        duration=0.0  # Will be updated by caller
                    )
                    
                    # Return on success or non-retryable errors
                    if response.is_success or response.is_client_error:
                        return response
                    
                    last_error = f"HTTP {resp.status}: {resp.reason}"
                    
            except asyncio.TimeoutError:
                last_error = "Request timeout"
            except aiohttp.ClientError as e:
                last_error = f"Client error: {e}"
            except Exception as e:
                last_error = f"Unexpected error: {e}"
        
        # All retries exhausted
        return NetworkResponse(
            request_id=request.id,
            status_code=0,
            error=f"Request failed after {endpoint.max_retries + 1} attempts: {last_error}"
        )
    
    def _calculate_retry_delay(self, strategy: RetryStrategy, attempt: int) -> float:
        """Calculate retry delay based on strategy"""
        base_delay = 1.0
        
        if strategy == RetryStrategy.LINEAR:
            return base_delay * attempt
        elif strategy == RetryStrategy.EXPONENTIAL:
            return base_delay * (2 ** (attempt - 1))
        elif strategy == RetryStrategy.ADAPTIVE:
            # AI Brain adaptive delay based on service performance
            # For now, use exponential with jitter
            return base_delay * (2 ** (attempt - 1)) * (0.5 + 0.5 * time.time() % 1)
        else:
            return 0.0
    
    # ==================== AI BRAIN OPTIMIZATION ====================
    
    def _optimize_request(self, request: NetworkRequest, endpoint: ServiceEndpoint) -> NetworkRequest:
        """Apply AI Brain optimizations to request"""
        
        # Adaptive timeout based on historical performance
        if endpoint.name in self._adaptive_timeouts:
            adaptive_timeout = self._adaptive_timeouts[endpoint.name]
            if adaptive_timeout > request.timeout:
                request.timeout = adaptive_timeout
                request.metadata['optimized'] = True
                request.metadata['adaptive_timeout'] = adaptive_timeout
        
        # Priority-based optimization
        if request.priority < 50:  # High priority requests
            request.timeout *= 1.5  # Increase timeout for important requests
            request.max_retries += 1  # More retries for critical requests
        
        return request
    
    def _record_request_response(self, request: NetworkRequest, response: NetworkResponse):
        """Record request/response for AI Brain learning"""
        
        # Record request pattern
        pattern_key = f"{request.endpoint}:{request.method}"
        self._request_patterns[pattern_key].append(datetime.now())
        
        # Record response time
        self._response_times[request.endpoint].append(response.duration)
        
        # Record errors
        if not response.is_success:
            error_pattern_key = f"{request.endpoint}:error"
            self._error_patterns[error_pattern_key].append(datetime.now())
        
        # Update adaptive timeouts
        if response.is_success:
            self._update_adaptive_timeout(request.endpoint, response.duration)
        
        # Store in history
        self._request_history.append({
            'request': asdict(request),
            'response': asdict(response),
            'timestamp': datetime.now()
        })
    
    def _update_adaptive_timeout(self, endpoint_name: str, response_duration: float):
        """Update adaptive timeout based on response patterns"""
        response_times = list(self._response_times[endpoint_name])
        
        if len(response_times) >= 10:
            # Calculate 95th percentile response time
            response_times.sort()
            p95_index = int(len(response_times) * 0.95)
            p95_time = response_times[p95_index]
            
            # Set adaptive timeout to 2x P95 response time
            self._adaptive_timeouts[endpoint_name] = p95_time * 2.0
    
    # ==================== CACHING ====================
    
    def _get_cache_key(self, request: NetworkRequest) -> str:
        """Generate cache key for request"""
        key_data = f"{request.method}:{request.url}:{json.dumps(request.data, sort_keys=True) if request.data else ''}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_cached_response(self, request: NetworkRequest) -> Optional[NetworkResponse]:
        """Get cached response if available and valid"""
        cache_key = self._get_cache_key(request)
        
        if cache_key in self._response_cache:
            cached_response, cached_time = self._response_cache[cache_key]
            
            # Check if cache is still valid
            if (datetime.now() - cached_time).total_seconds() < self._cache_ttl:
                # Create new response with current timestamp
                return NetworkResponse(
                    request_id=request.id,
                    status_code=cached_response.status_code,
                    data=cached_response.data,
                    headers=cached_response.headers,
                    duration=0.001,  # Very fast for cached response
                    metadata={'cached': True}
                )
        
        return None
    
    def _cache_response(self, request: NetworkRequest, response: NetworkResponse):
        """Cache response for future use"""
        cache_key = self._get_cache_key(request)
        self._response_cache[cache_key] = (response, datetime.now())
        
        # Clean up old cache entries periodically
        if len(self._response_cache) > 1000:
            asyncio.create_task(self._cleanup_cache())
    
    async def _cache_cleanup(self):
        """Clean up expired cache entries"""
        while self._running:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                current_time = datetime.now()
                expired_keys = []
                
                for cache_key, (response, cached_time) in self._response_cache.items():
                    if (current_time - cached_time).total_seconds() > self._cache_ttl:
                        expired_keys.append(cache_key)
                
                for key in expired_keys:
                    del self._response_cache[key]
                
                if expired_keys:
                    print(f"🧹 Cleaned up {len(expired_keys)} expired cache entries")
                    
            except Exception as e:
                print(f"❌ Cache cleanup error: {e}")
    
    # ==================== HEALTH MONITORING ====================
    
    async def _health_monitor(self):
        """Monitor service health"""
        while self._running:
            try:
                await asyncio.sleep(self._health_check_interval)
                
                if self._enable_health_checks:
                    await self._check_all_endpoints_health()
                    
            except Exception as e:
                print(f"❌ Health monitor error: {e}")
    
    async def _check_all_endpoints_health(self):
        """Check health of all endpoints"""
        health_tasks = []
        
        for endpoint_name, endpoint in self._endpoints.items():
            if endpoint.enabled:
                task = asyncio.create_task(self._check_endpoint_health(endpoint))
                health_tasks.append(task)
        
        if health_tasks:
            await asyncio.gather(*health_tasks, return_exceptions=True)
    
    async def _check_endpoint_health(self, endpoint: ServiceEndpoint):
        """Check individual endpoint health"""
        start_time = time.time()
        
        try:
            # Use health check URL if specified, otherwise use base URL
            health_url = endpoint.health_check_url or endpoint.url
            
            session = await self._get_session(endpoint)
            
            async with session.get(health_url, timeout=aiohttp.ClientTimeout(total=10.0)) as resp:
                response_time = time.time() - start_time
                
                # Determine health status
                if resp.status == 200:
                    status = HealthStatus.HEALTHY
                elif 200 <= resp.status < 400:
                    status = HealthStatus.HEALTHY
                elif 400 <= resp.status < 500:
                    status = HealthStatus.DEGRADED
                else:
                    status = HealthStatus.UNHEALTHY
                
                # Update health information
                health = self._service_health[endpoint.name]
                health.status = status
                health.last_check = datetime.now()
                health.response_time = response_time
                health.consecutive_failures = 0
                
                # Calculate error rate
                recent_errors = len([t for t in self._error_patterns.get(f"{endpoint.name}:error", [])
                                   if (datetime.now() - t).seconds < 3600])  # Last hour
                recent_requests = len([t for t in self._request_patterns.get(f"{endpoint.name}:GET", [])
                                     if (datetime.now() - t).seconds < 3600])
                
                if recent_requests > 0:
                    health.error_rate = recent_errors / recent_requests
                else:
                    health.error_rate = 0.0
                
                # Calculate availability (simplified)
                if health.error_rate < 0.05:  # Less than 5% error rate
                    health.availability = 100.0
                elif health.error_rate < 0.1:  # Less than 10% error rate
                    health.availability = 95.0
                else:
                    health.availability = max(50.0, 100.0 - (health.error_rate * 100))
                
        except Exception as e:
            # Health check failed
            health = self._service_health[endpoint.name]
            health.status = HealthStatus.UNHEALTHY
            health.last_check = datetime.now()
            health.consecutive_failures += 1
            health.availability = max(0.0, health.availability - 10.0)  # Reduce availability
            
            print(f"💔 Health check failed for {endpoint.name}: {e}")
    
    def get_endpoint_health(self, endpoint_name: str) -> Optional[ServiceHealth]:
        """Get health status for specific endpoint"""
        return self._service_health.get(endpoint_name)
    
    def get_healthy_endpoints(self) -> List[str]:
        """Get list of healthy endpoints"""
        healthy = []
        
        for endpoint_name, health in self._service_health.items():
            if health.status == HealthStatus.HEALTHY:
                healthy.append(endpoint_name)
        
        return healthy
    
    # ==================== SESSION MANAGEMENT ====================
    
    async def _create_session_pools(self):
        """Create HTTP session pools for different connection types"""
        
        # Create connector with connection limits
        connector = aiohttp.TCPConnector(
            limit=self._connection_limits['max_connections'],
            limit_per_host=self._connection_limits['max_connections_per_host'],
            ttl_dns_cache=self._connection_limits['ttl_dns_cache'],
            use_dns_cache=self._connection_limits['use_dns_cache'],
            ssl=ssl.create_default_context()
        )
        
        # Create session for HTTP/HTTPS
        self._session_pool['http'] = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'AI-Brain-Network-Core/1.0'}
        )
        
        print("🔗 HTTP session pool created")
    
    async def _close_session_pools(self):
        """Close all session pools"""
        for session_type, session in self._session_pool.items():
            try:
                await session.close()
            except Exception as e:
                print(f"❌ Error closing {session_type} session: {e}")
        
        self._session_pool.clear()
        print("🔗 Session pools closed")
    
    async def _get_session(self, endpoint: ServiceEndpoint) -> aiohttp.ClientSession:
        """Get appropriate session for endpoint"""
        if endpoint.connection_type in [ConnectionType.HTTP, ConnectionType.HTTPS]:
            return self._session_pool['http']
        else:
            # For other connection types, use HTTP session as fallback
            return self._session_pool['http']
    
    # ==================== PERFORMANCE ANALYSIS ====================
    
    async def _performance_analyzer(self):
        """Analyze network performance and optimize"""
        while self._running:
            try:
                await asyncio.sleep(120)  # Run every 2 minutes
                
                self._analyze_performance_patterns()
                self._optimize_connection_settings()
                
            except Exception as e:
                print(f"❌ Performance analyzer error: {e}")
    
    def _analyze_performance_patterns(self):
        """Analyze performance patterns for optimization"""
        
        # Analyze response time patterns
        for endpoint_name, response_times in self._response_times.items():
            if len(response_times) >= 20:
                times = list(response_times)
                avg_time = sum(times) / len(times)
                
                # Update error rates
                error_pattern_key = f"{endpoint_name}:error"
                recent_errors = len([t for t in self._error_patterns.get(error_pattern_key, [])
                                   if (datetime.now() - t).seconds < 3600])
                
                total_requests = len([t for t in self._request_patterns.get(f"{endpoint_name}:GET", [])
                                    if (datetime.now() - t).seconds < 3600])
                
                if total_requests > 0:
                    error_rate = recent_errors / total_requests
                    self._stats.error_rates[endpoint_name] = error_rate
    
    def _optimize_connection_settings(self):
        """Optimize connection settings based on performance"""
        
        # Adjust connection limits based on usage
        total_requests_last_hour = sum(
            len([t for t in pattern_times if (datetime.now() - t).seconds < 3600])
            for pattern_times in self._request_patterns.values()
        )
        
        if total_requests_last_hour > 1000:  # High traffic
            self._connection_limits['max_connections'] = min(200, 
                                                           self._connection_limits['max_connections'] + 10)
        elif total_requests_last_hour < 100:  # Low traffic
            self._connection_limits['max_connections'] = max(50,
                                                           self._connection_limits['max_connections'] - 10)
    
    def _update_average_response_time(self, duration: float):
        """Update global average response time"""
        if self._stats.total_requests > 0:
            # Exponential moving average
            alpha = 0.1
            self._stats.average_response_time = (
                alpha * duration + (1 - alpha) * self._stats.average_response_time
            )
        else:
            self._stats.average_response_time = duration
    
    # ==================== DEFAULT ENDPOINTS ====================
    
    def _load_default_endpoints(self):
        """Load default endpoints for MT5 Trading Client - Updated for 11 Services"""
        default_endpoints = [
            # Server microservices - All 11 services
            ServiceEndpoint(
                name="api_gateway",
                url="http://localhost:8000",
                connection_type=ConnectionType.HTTP,
                health_check_url="http://localhost:8000/health",
                timeout=30.0,
                priority=10
            ),
            
            ServiceEndpoint(
                name="data_bridge",
                url="http://localhost:8001",
                connection_type=ConnectionType.HTTP,
                health_check_url="http://localhost:8001/health",
                timeout=45.0,
                priority=20
            ),
            
            ServiceEndpoint(
                name="performance_analytics",
                url="http://localhost:8002",
                connection_type=ConnectionType.HTTP,
                health_check_url="http://localhost:8002/health",
                timeout=30.0,
                priority=25
            ),
            
            ServiceEndpoint(
                name="ai_orchestration",
                url="http://localhost:8003",
                connection_type=ConnectionType.HTTP,
                health_check_url="http://localhost:8003/health",
                timeout=60.0,
                priority=30
            ),
            
            ServiceEndpoint(
                name="deep_learning",
                url="http://localhost:8004",
                connection_type=ConnectionType.HTTP,
                health_check_url="http://localhost:8004/health",
                timeout=60.0,
                priority=35
            ),
            
            ServiceEndpoint(
                name="ai_provider",
                url="http://localhost:8005",
                connection_type=ConnectionType.HTTP,
                health_check_url="http://localhost:8005/health",
                timeout=30.0,
                priority=40
            ),
            
            ServiceEndpoint(
                name="ml_processing",
                url="http://localhost:8006",
                connection_type=ConnectionType.HTTP,
                health_check_url="http://localhost:8006/health",
                timeout=45.0,
                priority=45
            ),
            
            ServiceEndpoint(
                name="trading_engine",
                url="http://localhost:8007",
                connection_type=ConnectionType.HTTP,
                health_check_url="http://localhost:8007/health",
                timeout=30.0,
                priority=50
            ),
            
            ServiceEndpoint(
                name="database_service",
                url="http://localhost:8008",
                connection_type=ConnectionType.HTTP,
                health_check_url="http://localhost:8008/health",
                timeout=30.0,
                priority=55
            ),
            
            ServiceEndpoint(
                name="user_service",
                url="http://localhost:8009",
                connection_type=ConnectionType.HTTP,
                health_check_url="http://localhost:8009/health",
                timeout=30.0,
                priority=60
            ),
            
            ServiceEndpoint(
                name="strategy_optimization",
                url="http://localhost:8010",
                connection_type=ConnectionType.HTTP,
                health_check_url="http://localhost:8010/health",
                timeout=45.0,
                priority=65
            ),
            
            # External services (examples)
            ServiceEndpoint(
                name="external_market_data",
                url="https://api.example-market-data.com",
                connection_type=ConnectionType.HTTPS,
                timeout=15.0,
                priority=60,
                enabled=False  # Disabled by default
            )
        ]
        
        for endpoint in default_endpoints:
            self.register_endpoint(endpoint)
        
        print(f"📡 Loaded {len(default_endpoints)} default endpoints")
    
    # ==================== BACKGROUND PROCESSING ====================
    
    async def _request_processor(self):
        """Process queued requests"""
        while self._running:
            try:
                # This is a placeholder for request queue processing
                # In practice, you might want to implement priority queues
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Request processor error: {e}")
    
    # ==================== STATISTICS AND REPORTING ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive network statistics"""
        return {
            'total_requests': self._stats.total_requests,
            'successful_requests': self._stats.successful_requests,
            'failed_requests': self._stats.failed_requests,
            'success_rate': self._stats.success_rate,
            'average_response_time': self._stats.average_response_time,
            'requests_by_endpoint': dict(self._stats.requests_by_endpoint),
            'error_rates': dict(self._stats.error_rates),
            'active_connections': self._stats.active_connections,
            'registered_endpoints': len(self._endpoints),
            'healthy_endpoints': len(self.get_healthy_endpoints()),
            'cached_responses': len(self._response_cache),
            'adaptive_timeouts': len(self._adaptive_timeouts)
        }
    
    def get_endpoint_statistics(self, endpoint_name: str) -> Dict[str, Any]:
        """Get statistics for specific endpoint"""
        if endpoint_name not in self._endpoints:
            return {}
        
        endpoint = self._endpoints[endpoint_name]
        health = self._service_health.get(endpoint_name)
        
        # Calculate recent activity
        recent_requests = len([t for t in self._request_patterns.get(f"{endpoint_name}:GET", [])
                             if (datetime.now() - t).seconds < 3600])
        
        recent_errors = len([t for t in self._error_patterns.get(f"{endpoint_name}:error", [])
                           if (datetime.now() - t).seconds < 3600])
        
        response_times = list(self._response_times.get(endpoint_name, []))
        
        return {
            'endpoint_name': endpoint_name,
            'url': endpoint.url,
            'enabled': endpoint.enabled,
            'connection_type': endpoint.connection_type.value,
            'health_status': health.status.value if health else 'unknown',
            'availability': health.availability if health else 0.0,
            'error_rate': health.error_rate if health else 0.0,
            'recent_requests': recent_requests,
            'recent_errors': recent_errors,
            'average_response_time': sum(response_times) / len(response_times) if response_times else 0.0,
            'adaptive_timeout': self._adaptive_timeouts.get(endpoint_name),
            'last_health_check': health.last_check.isoformat() if health else None
        }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        report = {
            'summary': {
                'total_endpoints': len(self._endpoints),
                'healthy_endpoints': len(self.get_healthy_endpoints()),
                'overall_success_rate': self._stats.success_rate,
                'average_response_time': self._stats.average_response_time
            },
            'endpoints': {},
            'top_performers': [],
            'problematic_endpoints': []
        }
        
        # Analyze each endpoint
        for endpoint_name in self._endpoints.keys():
            endpoint_stats = self.get_endpoint_statistics(endpoint_name)
            report['endpoints'][endpoint_name] = endpoint_stats
            
            # Categorize endpoints
            if endpoint_stats.get('error_rate', 1.0) < 0.05 and endpoint_stats.get('availability', 0) > 95:
                report['top_performers'].append(endpoint_name)
            elif endpoint_stats.get('error_rate', 0.0) > 0.1 or endpoint_stats.get('availability', 100) < 80:
                report['problematic_endpoints'].append(endpoint_name)
        
        return report


# ==================== CONVENIENCE FUNCTIONS ====================

# Global instance
network_core = None

def get_network_core() -> NetworkCore:
    """Get global network core instance"""
    global network_core
    if network_core is None:
        network_core = NetworkCore.get_instance()
    return network_core

async def make_request(endpoint_name: str, method: str, path: str = "",
                      data: Optional[Dict[str, Any]] = None,
                      headers: Optional[Dict[str, str]] = None,
                      timeout: Optional[float] = None) -> NetworkResponse:
    """Convenience function to make network request"""
    return await get_network_core().request(endpoint_name, method, path, data, headers, timeout)

async def get_service_health(endpoint_name: str) -> Optional[ServiceHealth]:
    """Convenience function to get service health"""
    return get_network_core().get_endpoint_health(endpoint_name)

def register_service_endpoint(name: str, url: str, connection_type: ConnectionType = ConnectionType.HTTP,
                             timeout: float = 30.0) -> bool:
    """Convenience function to register service endpoint"""
    endpoint = ServiceEndpoint(
        name=name,
        url=url,
        connection_type=connection_type,
        timeout=timeout
    )
    return get_network_core().register_endpoint(endpoint)

# ==================== SPECIALIZED REQUEST FUNCTIONS ====================

async def api_gateway_request(method: str, path: str, data: Optional[Dict[str, Any]] = None) -> NetworkResponse:
    """Make request to API Gateway"""
    return await make_request("api_gateway", method, path, data)

async def data_bridge_request(method: str, path: str, data: Optional[Dict[str, Any]] = None) -> NetworkResponse:
    """Make request to Data Bridge service"""
    return await make_request("data_bridge", method, path, data)

async def database_request(method: str, path: str, data: Optional[Dict[str, Any]] = None) -> NetworkResponse:
    """Make request to Database service"""
    return await make_request("database_service", method, path, data)

async def ai_orchestration_request(method: str, path: str, data: Optional[Dict[str, Any]] = None) -> NetworkResponse:
    """Make request to AI Orchestration service"""
    return await make_request("ai_orchestration", method, path, data)