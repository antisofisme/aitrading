"""
Standard Circuit Breaker untuk semua services
Menyediakan consistent circuit breaker patterns untuk external service protection
"""

import time
import asyncio
import logging as python_logging
from typing import Any, Dict, Optional, Callable, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from collections import deque, defaultdict


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"        # Normal operation
    OPEN = "open"           # Circuit is open, requests fail fast
    HALF_OPEN = "half_open" # Testing if service is recovered


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5          # Number of failures to open circuit
    recovery_timeout: int = 60          # Seconds to wait before trying half-open
    success_threshold: int = 3          # Successes needed in half-open to close
    timeout: float = 30.0               # Request timeout in seconds
    monitoring_window: int = 300        # Window for monitoring failures (seconds)
    max_calls_in_half_open: int = 3     # Max calls allowed in half-open state


@dataclass
class CircuitBreakerMetrics:
    """Circuit breaker metrics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    timeout_requests: int = 0
    circuit_open_rejections: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    state_changes: int = 0


class CircuitBreaker:
    """
    Circuit breaker implementation untuk protecting external service calls
    """

    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitState.CLOSED
        self.metrics = CircuitBreakerMetrics()
        self.failure_times = deque()
        self.half_open_calls = 0
        self.half_open_successes = 0
        self.last_state_change = time.time()
        self.logger = python_logging.getLogger(f"circuit_breaker.{name}")

    def _clean_old_failures(self):
        """Remove failures outside monitoring window"""
        current_time = time.time()
        cutoff_time = current_time - self.config.monitoring_window

        while self.failure_times and self.failure_times[0] < cutoff_time:
            self.failure_times.popleft()

    def _should_open_circuit(self) -> bool:
        """Check if circuit should be opened"""
        self._clean_old_failures()
        return len(self.failure_times) >= self.config.failure_threshold

    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset to half-open"""
        if self.state != CircuitState.OPEN:
            return False

        current_time = time.time()
        time_since_open = current_time - self.last_state_change
        return time_since_open >= self.config.recovery_timeout

    def _change_state(self, new_state: CircuitState):
        """Change circuit breaker state"""
        old_state = self.state
        self.state = new_state
        self.last_state_change = time.time()
        self.metrics.state_changes += 1

        if new_state == CircuitState.HALF_OPEN:
            self.half_open_calls = 0
            self.half_open_successes = 0

        self.logger.info(f"Circuit breaker state changed: {old_state.value} -> {new_state.value}")

    def is_open(self) -> bool:
        """Check if circuit is open"""
        return self.state == CircuitState.OPEN

    def is_closed(self) -> bool:
        """Check if circuit is closed"""
        return self.state == CircuitState.CLOSED

    def is_half_open(self) -> bool:
        """Check if circuit is half-open"""
        return self.state == CircuitState.HALF_OPEN

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function call with circuit breaker protection"""
        return await self._execute_call(func, args, kwargs)

    async def _execute_call(self, func: Callable, args: tuple, kwargs: dict) -> Any:
        """Internal method to execute call with circuit breaker logic"""
        current_time = time.time()

        # Check if we should attempt reset
        if self._should_attempt_reset():
            self._change_state(CircuitState.HALF_OPEN)

        # Handle different states
        if self.state == CircuitState.OPEN:
            self.metrics.circuit_open_rejections += 1
            raise CircuitBreakerOpenError(f"Circuit breaker {self.name} is OPEN")

        elif self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls >= self.config.max_calls_in_half_open:
                self.metrics.circuit_open_rejections += 1
                raise CircuitBreakerOpenError(f"Circuit breaker {self.name} is HALF_OPEN with max calls reached")

        # Execute the call
        self.metrics.total_requests += 1

        if self.state == CircuitState.HALF_OPEN:
            self.half_open_calls += 1

        try:
            # Set timeout for the call
            if asyncio.iscoroutinefunction(func):
                result = await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=self.config.timeout
                )
            else:
                result = func(*args, **kwargs)

            # Call succeeded
            await self._record_success()
            return result

        except asyncio.TimeoutError:
            self.metrics.timeout_requests += 1
            await self._record_failure()
            raise CircuitBreakerTimeoutError(f"Call to {self.name} timed out after {self.config.timeout}s")

        except Exception as e:
            await self._record_failure()
            raise

    async def _record_success(self):
        """Record successful call"""
        current_time = time.time()
        self.metrics.successful_requests += 1
        self.metrics.last_success_time = current_time

        if self.state == CircuitState.HALF_OPEN:
            self.half_open_successes += 1

            # Check if we have enough successes to close circuit
            if self.half_open_successes >= self.config.success_threshold:
                self._change_state(CircuitState.CLOSED)
                self.failure_times.clear()

        self.logger.debug(f"Recorded success for {self.name}")

    async def _record_failure(self):
        """Record failed call"""
        current_time = time.time()
        self.metrics.failed_requests += 1
        self.metrics.last_failure_time = current_time
        self.failure_times.append(current_time)

        if self.state == CircuitState.HALF_OPEN:
            # Failure in half-open state immediately opens circuit
            self._change_state(CircuitState.OPEN)
        elif self.state == CircuitState.CLOSED:
            # Check if we should open circuit
            if self._should_open_circuit():
                self._change_state(CircuitState.OPEN)

        self.logger.debug(f"Recorded failure for {self.name}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics"""
        current_time = time.time()
        self._clean_old_failures()

        success_rate = 0.0
        if self.metrics.total_requests > 0:
            success_rate = self.metrics.successful_requests / self.metrics.total_requests

        return {
            "name": self.name,
            "state": self.state.value,
            "total_requests": self.metrics.total_requests,
            "successful_requests": self.metrics.successful_requests,
            "failed_requests": self.metrics.failed_requests,
            "timeout_requests": self.metrics.timeout_requests,
            "circuit_open_rejections": self.metrics.circuit_open_rejections,
            "success_rate": success_rate,
            "recent_failures": len(self.failure_times),
            "failure_threshold": self.config.failure_threshold,
            "last_failure_time": self.metrics.last_failure_time,
            "last_success_time": self.metrics.last_success_time,
            "state_changes": self.metrics.state_changes,
            "time_since_last_state_change": current_time - self.last_state_change
        }

    def reset(self):
        """Manually reset circuit breaker to closed state"""
        self._change_state(CircuitState.CLOSED)
        self.failure_times.clear()
        self.logger.info(f"Circuit breaker {self.name} manually reset")


class CircuitBreakerManager:
    """
    Circuit breaker manager untuk semua services
    Manages multiple circuit breakers for different external services
    """

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.default_config = CircuitBreakerConfig()
        self.logger = python_logging.getLogger(f"{service_name}.circuit_breaker_manager")

    def add_circuit_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Add circuit breaker for external service"""
        config = config or self.default_config
        circuit_breaker = CircuitBreaker(name, config)
        self.circuit_breakers[name] = circuit_breaker

        self.logger.info(f"Added circuit breaker for {name}")
        return circuit_breaker

    def get_circuit_breaker(self, name: str) -> CircuitBreaker:
        """Get circuit breaker by name"""
        if name not in self.circuit_breakers:
            # Auto-create circuit breaker with default config
            return self.add_circuit_breaker(name)
        return self.circuit_breakers[name]

    def is_open(self, external_service: str) -> bool:
        """Check if circuit breaker is open for external service"""
        circuit_breaker = self.get_circuit_breaker(external_service)
        return circuit_breaker.is_open()

    async def call(self, external_service: str, func: Callable, *args, **kwargs) -> Any:
        """Execute call with circuit breaker protection"""
        circuit_breaker = self.get_circuit_breaker(external_service)
        return await circuit_breaker.call(func, *args, **kwargs)

    async def record_success(self, external_service: str):
        """Record successful external service call"""
        circuit_breaker = self.get_circuit_breaker(external_service)
        await circuit_breaker._record_success()

    async def record_failure(self, external_service: str):
        """Record failed external service call"""
        circuit_breaker = self.get_circuit_breaker(external_service)
        await circuit_breaker._record_failure()

    def reset_circuit_breaker(self, external_service: str):
        """Reset specific circuit breaker"""
        if external_service in self.circuit_breakers:
            self.circuit_breakers[external_service].reset()

    def reset_all_circuit_breakers(self):
        """Reset all circuit breakers"""
        for circuit_breaker in self.circuit_breakers.values():
            circuit_breaker.reset()

    async def get_status(self) -> Dict[str, Any]:
        """Get status of all circuit breakers"""
        status = {
            "service": self.service_name,
            "total_circuit_breakers": len(self.circuit_breakers),
            "circuit_breakers": {}
        }

        open_count = 0
        half_open_count = 0

        for name, circuit_breaker in self.circuit_breakers.items():
            metrics = circuit_breaker.get_metrics()
            status["circuit_breakers"][name] = metrics

            if circuit_breaker.is_open():
                open_count += 1
            elif circuit_breaker.is_half_open():
                half_open_count += 1

        status["open_circuit_breakers"] = open_count
        status["half_open_circuit_breakers"] = half_open_count
        status["closed_circuit_breakers"] = len(self.circuit_breakers) - open_count - half_open_count

        return status

    def configure_circuit_breaker(self, name: str, config: CircuitBreakerConfig):
        """Configure specific circuit breaker"""
        if name in self.circuit_breakers:
            self.circuit_breakers[name].config = config
            self.logger.info(f"Updated configuration for circuit breaker {name}")
        else:
            self.add_circuit_breaker(name, config)

    def remove_circuit_breaker(self, name: str):
        """Remove circuit breaker"""
        if name in self.circuit_breakers:
            del self.circuit_breakers[name]
            self.logger.info(f"Removed circuit breaker {name}")

    # Common patterns for external service calls
    async def call_database(self, func: Callable, *args, **kwargs) -> Any:
        """Call database with circuit breaker protection"""
        return await self.call("database", func, *args, **kwargs)

    async def call_cache(self, func: Callable, *args, **kwargs) -> Any:
        """Call cache with circuit breaker protection"""
        return await self.call("cache", func, *args, **kwargs)

    async def call_external_api(self, api_name: str, func: Callable, *args, **kwargs) -> Any:
        """Call external API with circuit breaker protection"""
        return await self.call(f"external_api_{api_name}", func, *args, **kwargs)

    async def call_message_queue(self, func: Callable, *args, **kwargs) -> Any:
        """Call message queue with circuit breaker protection"""
        return await self.call("message_queue", func, *args, **kwargs)


# Custom exceptions
class CircuitBreakerError(Exception):
    """Base circuit breaker exception"""
    pass


class CircuitBreakerOpenError(CircuitBreakerError):
    """Circuit breaker is open"""
    pass


class CircuitBreakerTimeoutError(CircuitBreakerError):
    """Circuit breaker call timed out"""
    pass