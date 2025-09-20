"""
AI Brain Enhanced Circuit Breaker Core - Fault tolerance with pre-execution safety
Circuit breaker patterns enhanced with AI Brain pre-execution safety checks and emergency stops
"""

import asyncio
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable, Union, Tuple
from enum import Enum
from dataclasses import dataclass, field
from ..base.base_logger import BaseLogger
from ..base.base_performance import BasePerformance

# AI Brain Integration
try:
    import sys
    sys.path.append('/mnt/f/WINDSURF/concept_ai/projects/ai_trading/server_microservice/services')
    from shared.ai_brain_confidence_framework import AiBrainConfidenceFramework
    AI_BRAIN_AVAILABLE = True
except ImportError:
    AI_BRAIN_AVAILABLE = False

class CircuitState(Enum):
    """Circuit breaker state enumeration"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, calls fail fast
    HALF_OPEN = "half_open"  # Testing if service has recovered
    EMERGENCY_STOP = "emergency_stop"  # AI Brain: Emergency stopped for safety

class FailureType(Enum):
    """Failure type classification"""
    TIMEOUT = "timeout"
    CONNECTION_ERROR = "connection_error"
    HTTP_ERROR = "http_error"
    SERVICE_ERROR = "service_error"
    RATE_LIMIT = "rate_limit"
    AUTHENTICATION = "authentication"
    DESTRUCTIVE_OPERATION = "destructive_operation"  # AI Brain: Dangerous operations
    EMERGENCY_STOP = "emergency_stop"  # AI Brain: Emergency halted operation
    SAFETY_VIOLATION = "safety_violation"  # AI Brain: Safety check failed
    UNKNOWN = "unknown"

class RecoveryStrategy(Enum):
    """Recovery strategy enumeration"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_INTERVAL = "fixed_interval"
    ADAPTIVE = "adaptive"

@dataclass
class CircuitBreakerConfig:
    """AI Brain Enhanced Circuit breaker configuration with safety settings"""
    circuit_id: str
    service_name: str
    failure_threshold: int = 5
    success_threshold: int = 3
    timeout_seconds: float = 30.0
    recovery_timeout_seconds: float = 60.0
    recovery_strategy: RecoveryStrategy = RecoveryStrategy.EXPONENTIAL_BACKOFF
    max_recovery_time_seconds: float = 300.0
    failure_rate_threshold: float = 0.5  # 50% failure rate
    min_requests_for_evaluation: int = 10
    sliding_window_size: int = 100
    # AI Brain Safety Settings
    enable_pre_execution_safety: bool = True
    destructive_operations_list: List[str] = field(default_factory=list)
    emergency_stop_threshold: float = 0.9  # 90% confidence for emergency stops
    safety_confidence_threshold: float = 0.85  # 85% confidence for safety checks
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CallAttempt:
    """Individual call attempt record"""
    attempt_id: str
    timestamp: datetime
    duration_ms: float
    success: bool
    failure_type: Optional[FailureType] = None
    error_message: Optional[str] = None
    response_size_bytes: int = 0

@dataclass
class CircuitMetrics:
    """Circuit breaker metrics"""
    circuit_id: str
    current_state: CircuitState
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    timeouts: int = 0
    circuit_open_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    avg_response_time_ms: float = 0.0
    failure_rate: float = 0.0
    uptime_percentage: float = 100.0
    recovery_attempts: int = 0

class CircuitBreakerCore:
    """
    Circuit Breaker domain-specific core infrastructure.
    
    Features:
    - Circuit breaker pattern implementation
    - Failure detection and classification
    - Automatic recovery strategies
    - Performance monitoring and metrics
    - Graceful degradation support
    - Configurable failure thresholds
    """
    
    def __init__(self, service_name: str = "ai-provider"):
        self.service_name = service_name
        
        # Circuit breaker management
        self.circuits: Dict[str, CircuitBreakerConfig] = {}
        self.circuit_states: Dict[str, CircuitState] = {}
        self.circuit_metrics: Dict[str, CircuitMetrics] = {}
        
        # Call tracking
        self.call_history: Dict[str, List[CallAttempt]] = {}
        self.recovery_timers: Dict[str, datetime] = {}
        
        # Global settings
        self.default_timeout = 30.0
        self.max_concurrent_circuits = 50
        self.metrics_retention_hours = 24
        self.auto_recovery_enabled = True
        
        # Performance tracking
        self.response_times: Dict[str, List[float]] = {}
        self.failure_patterns: Dict[str, Dict[FailureType, int]] = {}
        
        # AI Brain Safety Management
        self.emergency_stopped_operations: set = set()
        self.blocked_destructive_operations: Dict[str, datetime] = {}
        self.safety_violations: Dict[str, List[Dict]] = {}
        
        # Initialize logging and performance tracking
        self.logger = BaseLogger(service_name, "circuit_breaker_core")
        self.performance_tracker = BasePerformance(service_name)
        
        # AI Brain Confidence Framework Integration
        self.ai_brain_confidence = None
        if AI_BRAIN_AVAILABLE:
            try:
                self.ai_brain_confidence = AiBrainConfidenceFramework(f"circuit-breaker-{service_name}")
                print(f"✅ AI Brain Confidence Framework initialized for circuit breaker: {service_name}")
            except Exception as e:
                print(f"⚠️ AI Brain Confidence Framework initialization failed: {e}")
        
        # Setup default circuit breakers for AI provider with safety settings
        self._setup_default_circuits()
        
        # Setup AI Brain safety rules
        self._setup_safety_rules()
        
        # Start background tasks
        self._background_tasks: List[asyncio.Task] = []
        self._start_background_tasks()
        
        self.logger.info("AI Brain Enhanced Circuit Breaker Core initialized", extra={
            "service": service_name,
            "max_concurrent_circuits": self.max_concurrent_circuits,
            "auto_recovery": self.auto_recovery_enabled,
            "default_timeout": self.default_timeout,
            "ai_brain_safety_enabled": AI_BRAIN_AVAILABLE,
            "pre_execution_safety": True
        })
    
    def _setup_default_circuits(self):
        """Setup default circuit breakers for AI provider services"""
        default_circuits = [
            CircuitBreakerConfig(
                circuit_id="openai_api",
                service_name="OpenAI API",
                failure_threshold=5,
                success_threshold=3,
                timeout_seconds=30.0,
                recovery_timeout_seconds=60.0,
                failure_rate_threshold=0.6
            ),
            CircuitBreakerConfig(
                circuit_id="anthropic_api",
                service_name="Anthropic API",
                failure_threshold=3,
                success_threshold=2,
                timeout_seconds=45.0,
                recovery_timeout_seconds=90.0,
                failure_rate_threshold=0.5
            ),
            CircuitBreakerConfig(
                circuit_id="google_genai_api",
                service_name="Google GenAI API",
                failure_threshold=4,
                success_threshold=2,
                timeout_seconds=25.0,
                recovery_timeout_seconds=120.0,
                failure_rate_threshold=0.7
            ),
            CircuitBreakerConfig(
                circuit_id="deepseek_api",
                service_name="DeepSeek API",
                failure_threshold=3,
                success_threshold=2,
                timeout_seconds=20.0,
                recovery_timeout_seconds=45.0,
                failure_rate_threshold=0.4
            ),
            CircuitBreakerConfig(
                circuit_id="database_connection",
                service_name="Database Connection",
                failure_threshold=2,
                success_threshold=1,
                timeout_seconds=10.0,
                recovery_timeout_seconds=30.0,
                failure_rate_threshold=0.3
            )
        ]
        
        for circuit_config in default_circuits:
            self.register_circuit(circuit_config)
        
        self.logger.info(f"Default circuit breakers configured: {len(default_circuits)}")
    
    def _start_background_tasks(self):
        """Start background monitoring and recovery tasks"""
        # Recovery monitoring task
        recovery_task = asyncio.create_task(self._recovery_monitoring_loop())
        self._background_tasks.append(recovery_task)
        
        # Metrics cleanup task
        cleanup_task = asyncio.create_task(self._metrics_cleanup_loop())
        self._background_tasks.append(cleanup_task)
        
        # Health assessment task
        health_task = asyncio.create_task(self._health_assessment_loop())
        self._background_tasks.append(health_task)
        
        # AI Brain: Safety monitoring task
        safety_task = asyncio.create_task(self._safety_monitoring_loop())
        self._background_tasks.append(safety_task)
    
    def register_circuit(self, circuit_config: CircuitBreakerConfig) -> str:
        """Register new circuit breaker"""
        circuit_id = circuit_config.circuit_id
        self.circuits[circuit_id] = circuit_config
        
        # Initialize circuit state and metrics
        self.circuit_states[circuit_id] = CircuitState.CLOSED
        self.circuit_metrics[circuit_id] = CircuitMetrics(
            circuit_id=circuit_id,
            current_state=CircuitState.CLOSED
        )
        
        # Initialize tracking data
        self.call_history[circuit_id] = []
        self.response_times[circuit_id] = []
        self.failure_patterns[circuit_id] = {failure_type: 0 for failure_type in FailureType}
        
        self.logger.info(f"Circuit breaker registered: {circuit_id}", extra={
            "service_name": circuit_config.service_name,
            "failure_threshold": circuit_config.failure_threshold,
            "timeout_seconds": circuit_config.timeout_seconds,
            "recovery_strategy": circuit_config.recovery_strategy.value
        })
        
        return circuit_id
    
    def _setup_safety_rules(self):
        """Setup AI Brain safety rules for circuit breakers"""
        # Define high-risk operations that trigger emergency stops
        high_risk_operations = {
            'DELETE_SERVICE',
            'DROP_DATABASE', 
            'DESTROY_INFRASTRUCTURE',
            'PURGE_DATA',
            'RESET_SYSTEM',
            'TRUNCATE_TABLE'
        }
        
        # Block these operations immediately
        for operation in high_risk_operations:
            self.emergency_stopped_operations.add(operation)
        
        self.logger.info("AI Brain safety rules configured", extra={
            "emergency_stopped_operations": len(self.emergency_stopped_operations),
            "safety_confidence_threshold": 0.85
        })
    
    async def call_with_circuit_breaker(self, 
                                      circuit_id: str,
                                      callable_func: Callable,
                                      *args, **kwargs) -> Tuple[bool, Any, Optional[str]]:
        """
        Execute function call with AI Brain enhanced circuit breaker protection.
        
        Includes pre-execution safety checks, emergency stops, and destructive operation prevention.
        
        Args:
            circuit_id: Circuit breaker identifier
            callable_func: Function to execute
            *args, **kwargs: Function arguments
            
        Returns:
            Tuple of (success, result, error_message)
        """
        if circuit_id not in self.circuits:
            self.logger.error(f"Circuit breaker not found: {circuit_id}")
            return False, None, "Circuit breaker not found"
        
        # AI Brain: Pre-execution safety checks
        safety_check = await self._perform_pre_execution_safety_check(circuit_id, callable_func, *args, **kwargs)
        if not safety_check['is_safe']:
            await self._record_call_attempt(circuit_id, False, FailureType.SAFETY_VIOLATION, 
                                          safety_check['reason'])
            return False, None, f"Safety violation: {safety_check['reason']}"
        
        # Check circuit state (including emergency stop)
        current_state = self.circuit_states[circuit_id]
        
        if current_state == CircuitState.OPEN:
            # Circuit is open, fail fast
            await self._record_call_attempt(circuit_id, False, FailureType.SERVICE_ERROR, 
                                          "Circuit breaker is OPEN")
            return False, None, "Service temporarily unavailable (circuit breaker open)"
        
        elif current_state == CircuitState.EMERGENCY_STOP:
            # AI Brain: Emergency stop active, absolute halt
            await self._record_call_attempt(circuit_id, False, FailureType.EMERGENCY_STOP, 
                                          "Operation emergency stopped for safety")
            return False, None, "Operation halted by emergency safety system"
        
        elif current_state == CircuitState.HALF_OPEN:
            # Limited calls allowed during recovery testing
            pass
        
        # Execute the call
        start_time = time.time()
        attempt_id = f"{circuit_id}_{int(time.time() * 1000)}"
        
        try:
            # Apply timeout
            circuit_config = self.circuits[circuit_id]
            result = await asyncio.wait_for(
                self._execute_callable(callable_func, *args, **kwargs),
                timeout=circuit_config.timeout_seconds
            )
            
            # Record successful call
            duration_ms = (time.time() - start_time) * 1000
            await self._record_call_attempt(circuit_id, True, None, None, duration_ms)
            
            # Check if we should close circuit from half-open state
            if current_state == CircuitState.HALF_OPEN:
                await self._evaluate_half_open_circuit(circuit_id)
            
            return True, result, None
            
        except asyncio.TimeoutError:
            # Timeout occurred
            duration_ms = (time.time() - start_time) * 1000
            await self._record_call_attempt(circuit_id, False, FailureType.TIMEOUT, 
                                          "Operation timed out", duration_ms)
            await self._evaluate_circuit_state(circuit_id)
            return False, None, "Operation timed out"
            
        except ConnectionError as e:
            # Connection error
            duration_ms = (time.time() - start_time) * 1000
            await self._record_call_attempt(circuit_id, False, FailureType.CONNECTION_ERROR, 
                                          str(e), duration_ms)
            await self._evaluate_circuit_state(circuit_id)
            return False, None, f"Connection error: {str(e)}"
            
        except Exception as e:
            # Other errors
            duration_ms = (time.time() - start_time) * 1000
            failure_type = self._classify_failure(e)
            await self._record_call_attempt(circuit_id, False, failure_type, str(e), duration_ms)
            await self._evaluate_circuit_state(circuit_id)
            return False, None, f"Service error: {str(e)}"
    
    async def _execute_callable(self, callable_func: Callable, *args, **kwargs):
        """Execute callable function, handling both sync and async"""
        if asyncio.iscoroutinefunction(callable_func):
            return await callable_func(*args, **kwargs)
        else:
            return callable_func(*args, **kwargs)
    
    async def _perform_pre_execution_safety_check(self, circuit_id: str, callable_func: Callable, 
                                                 *args, **kwargs) -> Dict[str, Any]:
        """AI Brain: Perform comprehensive pre-execution safety checks"""
        safety_result = {
            'is_safe': True,
            'reason': None,
            'confidence': 1.0,
            'risk_level': 'LOW',
            'blockers': [],
            'warnings': []
        }
        
        try:
            circuit_config = self.circuits[circuit_id]
            
            # Check 1: Emergency stop list
            operation_name = getattr(callable_func, '__name__', 'unknown_operation')
            if operation_name.upper() in self.emergency_stopped_operations:
                safety_result.update({
                    'is_safe': False,
                    'reason': f"Operation {operation_name} is emergency stopped",
                    'confidence': 0.95,
                    'risk_level': 'CRITICAL'
                })
                return safety_result
            
            # Check 2: Destructive operation detection
            if circuit_config.enable_pre_execution_safety:
                is_destructive = await self._detect_destructive_operation(callable_func, *args, **kwargs)
                if is_destructive['is_destructive']:
                    # Require explicit confirmation for destructive operations
                    confirmation = kwargs.get('confirm_destructive', False)
                    if not confirmation:
                        safety_result.update({
                            'is_safe': False,
                            'reason': f"Destructive operation requires explicit confirmation: {is_destructive['operation_type']}",
                            'confidence': 0.9,
                            'risk_level': 'HIGH'
                        })
                        return safety_result
            
            # Check 3: Circuit health assessment
            circuit_metrics = self.circuit_metrics[circuit_id]
            if circuit_metrics.failure_rate > 0.8:  # 80% failure rate
                safety_result['warnings'].append('Circuit has high failure rate - operation risky')
                safety_result['confidence'] *= 0.7  # Reduce confidence
            
            # Check 4: Resource safety (if AI Brain available)
            if self.ai_brain_confidence:
                confidence_score = await self.ai_brain_confidence.calculate_confidence(
                    'pre_execution_safety',
                    {
                        'circuit_id': circuit_id,
                        'operation': operation_name,
                        'failure_rate': circuit_metrics.failure_rate,
                        'circuit_state': self.circuit_states[circuit_id].value
                    }
                )
                
                if confidence_score < circuit_config.safety_confidence_threshold:
                    safety_result.update({
                        'is_safe': False,
                        'reason': f"AI Brain confidence too low: {confidence_score:.3f} < {circuit_config.safety_confidence_threshold}",
                        'confidence': confidence_score,
                        'risk_level': 'MEDIUM'
                    })
                    return safety_result
            
            return safety_result
            
        except Exception as e:
            # Safety check failure - err on side of caution
            self.logger.error(f"Pre-execution safety check failed: {e}")
            return {
                'is_safe': False,
                'reason': f"Safety check system error: {str(e)}",
                'confidence': 0.0,
                'risk_level': 'CRITICAL'
            }
    
    async def _detect_destructive_operation(self, callable_func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """AI Brain: Detect potentially destructive operations"""
        operation_name = getattr(callable_func, '__name__', 'unknown')
        function_code = getattr(callable_func, '__doc__', '') or ''
        
        # Destructive operation patterns
        destructive_patterns = {
            'DELETE': ['delete', 'remove', 'drop', 'destroy'],
            'MODIFY': ['update', 'modify', 'change', 'alter'],
            'TRUNCATE': ['truncate', 'clear', 'empty', 'purge'],
            'RESET': ['reset', 'restart', 'reboot', 'initialize']
        }
        
        for operation_type, patterns in destructive_patterns.items():
            for pattern in patterns:
                if pattern.lower() in operation_name.lower() or pattern.lower() in function_code.lower():
                    return {
                        'is_destructive': True,
                        'operation_type': operation_type,
                        'detected_pattern': pattern,
                        'confidence': 0.85
                    }
        
        # Check arguments for destructive indicators
        str_args = ' '.join(str(arg) for arg in args if isinstance(arg, str))
        str_kwargs = ' '.join(str(v) for v in kwargs.values() if isinstance(v, str))
        all_params = f"{str_args} {str_kwargs}".lower()
        
        dangerous_keywords = ['drop', 'delete', 'remove', 'truncate', 'destroy', 'purge']
        for keyword in dangerous_keywords:
            if keyword in all_params:
                return {
                    'is_destructive': True,
                    'operation_type': 'PARAMETER_DESTRUCTIVE',
                    'detected_pattern': keyword,
                    'confidence': 0.75
                }
        
        return {
            'is_destructive': False,
            'operation_type': None,
            'detected_pattern': None,
            'confidence': 0.95
        }
    
    def _classify_failure(self, exception: Exception) -> FailureType:
        """Classify failure type based on exception"""
        if isinstance(exception, ConnectionError):
            return FailureType.CONNECTION_ERROR
        elif isinstance(exception, TimeoutError):
            return FailureType.TIMEOUT
        elif "rate limit" in str(exception).lower():
            return FailureType.RATE_LIMIT
        elif "auth" in str(exception).lower():
            return FailureType.AUTHENTICATION
        elif hasattr(exception, 'status_code'):
            return FailureType.HTTP_ERROR
        else:
            return FailureType.UNKNOWN
    
    async def _record_call_attempt(self, circuit_id: str, success: bool, 
                                 failure_type: Optional[FailureType] = None,
                                 error_message: Optional[str] = None,
                                 duration_ms: float = 0.0):
        """Record individual call attempt"""
        attempt = CallAttempt(
            attempt_id=f"{circuit_id}_{int(time.time() * 1000)}",
            timestamp=datetime.now(),
            duration_ms=duration_ms,
            success=success,
            failure_type=failure_type,
            error_message=error_message
        )
        
        # Add to call history
        self.call_history[circuit_id].append(attempt)
        
        # Maintain sliding window
        circuit_config = self.circuits[circuit_id]
        max_history = circuit_config.sliding_window_size
        if len(self.call_history[circuit_id]) > max_history:
            self.call_history[circuit_id] = self.call_history[circuit_id][-max_history:]
        
        # Update metrics
        metrics = self.circuit_metrics[circuit_id]
        metrics.total_requests += 1
        
        if success:
            metrics.successful_requests += 1
            metrics.last_success_time = datetime.now()
        else:
            metrics.failed_requests += 1
            metrics.last_failure_time = datetime.now()
            
            if failure_type == FailureType.TIMEOUT:
                metrics.timeouts += 1
            
            # Update failure patterns
            if failure_type:
                self.failure_patterns[circuit_id][failure_type] += 1
        
        # Update response time tracking
        if duration_ms > 0:
            self.response_times[circuit_id].append(duration_ms)
            
            # Keep only recent measurements
            if len(self.response_times[circuit_id]) > 1000:
                self.response_times[circuit_id] = self.response_times[circuit_id][-1000:]
            
            # Update average response time
            metrics.avg_response_time_ms = (
                sum(self.response_times[circuit_id]) / len(self.response_times[circuit_id])
            )
        
        # Update failure rate
        if metrics.total_requests > 0:
            metrics.failure_rate = metrics.failed_requests / metrics.total_requests
    
    async def _evaluate_circuit_state(self, circuit_id: str):
        """Evaluate whether circuit should be opened"""
        circuit_config = self.circuits[circuit_id]
        metrics = self.circuit_metrics[circuit_id]
        current_state = self.circuit_states[circuit_id]
        
        # Only evaluate if we have minimum requests
        if metrics.total_requests < circuit_config.min_requests_for_evaluation:
            return
        
        # Check failure threshold
        recent_failures = sum(
            1 for attempt in self.call_history[circuit_id][-circuit_config.failure_threshold:]
            if not attempt.success
        )
        
        # Open circuit if failure threshold exceeded
        if (recent_failures >= circuit_config.failure_threshold or 
            metrics.failure_rate >= circuit_config.failure_rate_threshold):
            
            if current_state != CircuitState.OPEN:
                await self._open_circuit(circuit_id)
    
    async def _evaluate_half_open_circuit(self, circuit_id: str):
        """Evaluate half-open circuit for potential closure"""
        circuit_config = self.circuits[circuit_id]
        
        # Count recent successes in half-open state
        recent_attempts = self.call_history[circuit_id][-circuit_config.success_threshold:]
        recent_successes = sum(1 for attempt in recent_attempts if attempt.success)
        
        if recent_successes >= circuit_config.success_threshold:
            # Close the circuit
            await self._close_circuit(circuit_id)
        elif len(recent_attempts) >= circuit_config.success_threshold:
            # Not enough successes, open circuit again
            await self._open_circuit(circuit_id)
    
    async def _open_circuit(self, circuit_id: str):
        """Open circuit breaker"""
        self.circuit_states[circuit_id] = CircuitState.OPEN
        self.circuit_metrics[circuit_id].circuit_open_count += 1
        self.circuit_metrics[circuit_id].current_state = CircuitState.OPEN
        
        # Set recovery timer
        circuit_config = self.circuits[circuit_id]
        self.recovery_timers[circuit_id] = datetime.now() + timedelta(
            seconds=circuit_config.recovery_timeout_seconds
        )
        
        self.logger.warning(f"Circuit breaker OPENED: {circuit_id}", extra={
            "failure_rate": self.circuit_metrics[circuit_id].failure_rate,
            "total_requests": self.circuit_metrics[circuit_id].total_requests,
            "recovery_timeout": circuit_config.recovery_timeout_seconds
        })
    
    async def _close_circuit(self, circuit_id: str):
        """Close circuit breaker"""
        self.circuit_states[circuit_id] = CircuitState.CLOSED
        self.circuit_metrics[circuit_id].current_state = CircuitState.CLOSED
        
        # Remove recovery timer
        if circuit_id in self.recovery_timers:
            del self.recovery_timers[circuit_id]
        
        self.logger.info(f"Circuit breaker CLOSED: {circuit_id}", extra={
            "successful_requests": self.circuit_metrics[circuit_id].successful_requests,
            "total_requests": self.circuit_metrics[circuit_id].total_requests
        })
    
    async def _half_open_circuit(self, circuit_id: str):
        """Set circuit to half-open state"""
        self.circuit_states[circuit_id] = CircuitState.HALF_OPEN
        self.circuit_metrics[circuit_id].current_state = CircuitState.HALF_OPEN
        self.circuit_metrics[circuit_id].recovery_attempts += 1
        
        self.logger.info(f"Circuit breaker HALF-OPEN: {circuit_id}", extra={
            "recovery_attempt": self.circuit_metrics[circuit_id].recovery_attempts
        })
    
    async def _recovery_monitoring_loop(self):
        """Background task for monitoring circuit recovery"""
        while True:
            try:
                current_time = datetime.now()
                
                for circuit_id, recovery_time in list(self.recovery_timers.items()):
                    if current_time >= recovery_time:
                        # Time to try recovery
                        if self.circuit_states[circuit_id] == CircuitState.OPEN:
                            await self._half_open_circuit(circuit_id)
                        
                        # Update recovery timer based on strategy
                        circuit_config = self.circuits[circuit_id]
                        new_timeout = self._calculate_next_recovery_timeout(circuit_id)
                        self.recovery_timers[circuit_id] = current_time + timedelta(seconds=new_timeout)
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                self.logger.error(f"Recovery monitoring error: {e}")
                await asyncio.sleep(10)
    
    def _calculate_next_recovery_timeout(self, circuit_id: str) -> float:
        """Calculate next recovery timeout based on strategy"""
        circuit_config = self.circuits[circuit_id]
        recovery_attempts = self.circuit_metrics[circuit_id].recovery_attempts
        
        if circuit_config.recovery_strategy == RecoveryStrategy.EXPONENTIAL_BACKOFF:
            # Exponential backoff: 2^attempts * base_timeout
            timeout = circuit_config.recovery_timeout_seconds * (2 ** min(recovery_attempts, 8))
        elif circuit_config.recovery_strategy == RecoveryStrategy.LINEAR_BACKOFF:
            # Linear backoff: attempts * base_timeout
            timeout = circuit_config.recovery_timeout_seconds * (1 + recovery_attempts)
        elif circuit_config.recovery_strategy == RecoveryStrategy.ADAPTIVE:
            # Adaptive based on failure rate
            failure_rate = self.circuit_metrics[circuit_id].failure_rate
            timeout = circuit_config.recovery_timeout_seconds * (1 + failure_rate * 2)
        else:
            # Fixed interval
            timeout = circuit_config.recovery_timeout_seconds
        
        # Cap at maximum recovery time
        return min(timeout, circuit_config.max_recovery_time_seconds)
    
    async def _metrics_cleanup_loop(self):
        """Background task for cleaning up old metrics"""
        while True:
            try:
                cutoff_time = datetime.now() - timedelta(hours=self.metrics_retention_hours)
                
                for circuit_id in self.call_history:
                    # Remove old call attempts
                    self.call_history[circuit_id] = [
                        attempt for attempt in self.call_history[circuit_id]
                        if attempt.timestamp > cutoff_time
                    ]
                
                await asyncio.sleep(3600)  # Cleanup every hour
                
            except Exception as e:
                self.logger.error(f"Metrics cleanup error: {e}")
                await asyncio.sleep(3600)
    
    async def _health_assessment_loop(self):
        """Background task for overall health assessment"""
        while True:
            try:
                for circuit_id, metrics in self.circuit_metrics.items():
                    # Calculate uptime percentage
                    if metrics.total_requests > 0:
                        metrics.uptime_percentage = (metrics.successful_requests / metrics.total_requests) * 100
                    
                    # Log health status periodically
                    if metrics.total_requests > 0:
                        self.logger.debug(f"Circuit health: {circuit_id}", extra={
                            "state": metrics.current_state.value,
                            "uptime_percentage": metrics.uptime_percentage,
                            "failure_rate": metrics.failure_rate,
                            "avg_response_time": metrics.avg_response_time_ms
                        })
                
                await asyncio.sleep(300)  # Health assessment every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Health assessment error: {e}")
                await asyncio.sleep(300)
    
    async def _safety_monitoring_loop(self):
        """AI Brain: Background task for continuous safety monitoring"""
        while True:
            try:
                for circuit_id, metrics in self.circuit_metrics.items():
                    # Monitor for patterns indicating need for emergency stop
                    if metrics.failure_rate > 0.9 and metrics.total_requests > 50:
                        # High failure rate with significant request volume
                        if self.circuit_states[circuit_id] != CircuitState.EMERGENCY_STOP:
                            await self._emergency_stop_circuit(circuit_id, 
                                "Pattern analysis indicates critical safety risk")
                    
                    # Monitor for unusual failure patterns
                    if circuit_id in self.failure_patterns:
                        destructive_failures = self.failure_patterns[circuit_id].get(FailureType.DESTRUCTIVE_OPERATION, 0)
                        safety_violations = self.failure_patterns[circuit_id].get(FailureType.SAFETY_VIOLATION, 0)
                        
                        if destructive_failures > 3 or safety_violations > 5:
                            await self._emergency_stop_circuit(circuit_id,
                                f"Multiple safety violations detected: destructive={destructive_failures}, safety={safety_violations}")
                
                await asyncio.sleep(60)  # Safety monitoring every minute
                
            except Exception as e:
                self.logger.error(f"Safety monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _emergency_stop_circuit(self, circuit_id: str, reason: str):
        """AI Brain: Emergency stop a circuit for critical safety reasons"""
        self.circuit_states[circuit_id] = CircuitState.EMERGENCY_STOP
        self.circuit_metrics[circuit_id].current_state = CircuitState.EMERGENCY_STOP
        
        # Record safety violation
        if circuit_id not in self.safety_violations:
            self.safety_violations[circuit_id] = []
        
        self.safety_violations[circuit_id].append({
            'timestamp': datetime.now().isoformat(),
            'reason': reason,
            'action': 'EMERGENCY_STOP',
            'failure_rate': self.circuit_metrics[circuit_id].failure_rate
        })
        
        self.logger.critical(f"EMERGENCY STOP activated for circuit: {circuit_id}", extra={
            "reason": reason,
            "total_requests": self.circuit_metrics[circuit_id].total_requests,
            "failure_rate": self.circuit_metrics[circuit_id].failure_rate,
            "action": "IMMEDIATE_HALT"
        })
    
    def get_circuit_status(self, circuit_id: Optional[str] = None) -> Dict[str, Any]:
        """Get circuit breaker status and metrics"""
        if circuit_id:
            if circuit_id in self.circuits:
                metrics = self.circuit_metrics[circuit_id]
                config = self.circuits[circuit_id]
                
                return {
                    "circuit_id": circuit_id,
                    "service_name": config.service_name,
                    "current_state": metrics.current_state.value,
                    "total_requests": metrics.total_requests,
                    "successful_requests": metrics.successful_requests,
                    "failed_requests": metrics.failed_requests,
                    "failure_rate": metrics.failure_rate,
                    "uptime_percentage": metrics.uptime_percentage,
                    "avg_response_time_ms": metrics.avg_response_time_ms,
                    "circuit_open_count": metrics.circuit_open_count,
                    "recovery_attempts": metrics.recovery_attempts,
                    "last_failure_time": metrics.last_failure_time.isoformat() if metrics.last_failure_time else None,
                    "last_success_time": metrics.last_success_time.isoformat() if metrics.last_success_time else None
                }
            return {}
        
        # Return all circuit statuses
        return {
            cid: self.get_circuit_status(cid)
            for cid in self.circuits.keys()
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health metrics"""
        total_circuits = len(self.circuits)
        open_circuits = len([
            c for c in self.circuit_states.values() 
            if c == CircuitState.OPEN
        ])
        half_open_circuits = len([
            c for c in self.circuit_states.values() 
            if c == CircuitState.HALF_OPEN
        ])
        
        # Calculate overall system health
        healthy_circuits = total_circuits - open_circuits
        system_health_percentage = (healthy_circuits / max(total_circuits, 1)) * 100
        
        return {
            "total_circuits": total_circuits,
            "healthy_circuits": healthy_circuits,
            "open_circuits": open_circuits,
            "half_open_circuits": half_open_circuits,
            "system_health_percentage": system_health_percentage,
            "auto_recovery_enabled": self.auto_recovery_enabled,
            "default_timeout": self.default_timeout,
            "metrics_retention_hours": self.metrics_retention_hours
        }

# Global circuit breaker core instance
_circuit_breaker_core: Optional[CircuitBreakerCore] = None

def get_circuit_breaker_core() -> CircuitBreakerCore:
    """Get the global circuit breaker core instance"""
    global _circuit_breaker_core
    if _circuit_breaker_core is None:
        _circuit_breaker_core = CircuitBreakerCore()
    return _circuit_breaker_core