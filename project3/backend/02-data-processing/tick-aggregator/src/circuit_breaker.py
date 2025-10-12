"""
Circuit Breaker Pattern for NATS Publisher

Implements a circuit breaker to prevent cascading failures when NATS is unavailable.

States:
- CLOSED: Normal operation (NATS working)
- OPEN: NATS failing (use fallback - PostgreSQL queue)
- HALF_OPEN: Testing recovery (try NATS again)

Thresholds:
- 5 failures in 60 seconds → circuit OPEN
- 30 seconds timeout → circuit HALF_OPEN
- 1 success in HALF_OPEN → circuit CLOSED
"""
import logging
import time
from enum import Enum
from typing import Optional, Callable, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"        # Normal operation
    OPEN = "open"            # Failing, use fallback
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """
    Circuit breaker for NATS publisher

    Features:
    - Automatic state transitions
    - Configurable failure thresholds
    - Recovery timeout
    - Callback notifications for state changes
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        monitoring_window: int = 60,
        on_state_change: Optional[Callable[[CircuitState, CircuitState], None]] = None
    ):
        """
        Initialize circuit breaker

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before testing recovery (HALF_OPEN)
            monitoring_window: Time window in seconds for counting failures
            on_state_change: Callback function when state changes
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.monitoring_window = monitoring_window
        self.on_state_change = on_state_change

        # State
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._opened_at: Optional[float] = None
        self._failures_in_window = []

        # Statistics
        self.stats = {
            'total_calls': 0,
            'total_failures': 0,
            'total_successes': 0,
            'state_transitions': 0,
            'last_opened': None,
            'last_closed': None
        }

        logger.info(f"Circuit Breaker initialized: "
                   f"threshold={failure_threshold}, "
                   f"recovery_timeout={recovery_timeout}s, "
                   f"window={monitoring_window}s")

    @property
    def state(self) -> CircuitState:
        """Get current circuit state"""
        return self._state

    @property
    def is_open(self) -> bool:
        """Check if circuit is OPEN (failing)"""
        return self._state == CircuitState.OPEN

    @property
    def is_closed(self) -> bool:
        """Check if circuit is CLOSED (normal)"""
        return self._state == CircuitState.CLOSED

    @property
    def is_half_open(self) -> bool:
        """Check if circuit is HALF_OPEN (testing)"""
        return self._state == CircuitState.HALF_OPEN

    def _transition_to(self, new_state: CircuitState):
        """
        Transition to new state

        Args:
            new_state: Target state
        """
        if new_state == self._state:
            return

        old_state = self._state
        self._state = new_state
        self.stats['state_transitions'] += 1

        now = datetime.utcnow().isoformat()

        # Update statistics
        if new_state == CircuitState.OPEN:
            self._opened_at = time.time()
            self.stats['last_opened'] = now
            logger.warning(f"⚠️ CIRCUIT BREAKER: {old_state.value.upper()} → OPEN")
            logger.warning(f"   Reason: {self._failure_count} failures in {self.monitoring_window}s")
            logger.warning(f"   Fallback: Will use PostgreSQL queue for {self.recovery_timeout}s")

        elif new_state == CircuitState.HALF_OPEN:
            logger.info(f"🔄 CIRCUIT BREAKER: {old_state.value.upper()} → HALF_OPEN")
            logger.info(f"   Testing recovery after {self.recovery_timeout}s")

        elif new_state == CircuitState.CLOSED:
            self._failure_count = 0
            self._failures_in_window.clear()
            self._opened_at = None
            self.stats['last_closed'] = now
            logger.info(f"✅ CIRCUIT BREAKER: {old_state.value.upper()} → CLOSED")
            logger.info(f"   NATS recovered, resuming normal operation")

        # Notify callback
        if self.on_state_change:
            try:
                self.on_state_change(old_state, new_state)
            except Exception as e:
                logger.error(f"Circuit breaker callback error: {e}")

    def _prune_old_failures(self):
        """Remove failures outside monitoring window"""
        now = time.time()
        cutoff = now - self.monitoring_window
        self._failures_in_window = [
            failure_time for failure_time in self._failures_in_window
            if failure_time > cutoff
        ]

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try recovery"""
        if self._state != CircuitState.OPEN:
            return False

        if self._opened_at is None:
            return False

        elapsed = time.time() - self._opened_at
        return elapsed >= self.recovery_timeout

    def call(self, func: Callable, *args, **kwargs) -> tuple[bool, Any]:
        """
        Execute function through circuit breaker

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            tuple: (success: bool, result: Any)
                - success=True, result=return value if function succeeded
                - success=False, result=exception if function failed
                - success=False, result=None if circuit is OPEN
        """
        self.stats['total_calls'] += 1

        # Check if circuit is OPEN
        if self._state == CircuitState.OPEN:
            # Check if we should try recovery
            if self._should_attempt_reset():
                self._transition_to(CircuitState.HALF_OPEN)
            else:
                # Circuit still OPEN, return immediately
                return False, None

        # Try to execute function
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return True, result

        except Exception as e:
            self._on_failure()
            return False, e

    async def call_async(self, func: Callable, *args, **kwargs) -> tuple[bool, Any]:
        """
        Execute async function through circuit breaker

        Args:
            func: Async function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            tuple: (success: bool, result: Any)
        """
        self.stats['total_calls'] += 1

        # Check if circuit is OPEN
        if self._state == CircuitState.OPEN:
            # Check if we should try recovery
            if self._should_attempt_reset():
                self._transition_to(CircuitState.HALF_OPEN)
            else:
                # Circuit still OPEN, return immediately
                return False, None

        # Try to execute async function
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return True, result

        except Exception as e:
            self._on_failure()
            return False, e

    def _on_success(self):
        """Handle successful call"""
        self.stats['total_successes'] += 1

        if self._state == CircuitState.HALF_OPEN:
            # Success in HALF_OPEN → back to CLOSED
            self._transition_to(CircuitState.CLOSED)

    def _on_failure(self):
        """Handle failed call"""
        self.stats['total_failures'] += 1
        now = time.time()

        self._last_failure_time = now
        self._failures_in_window.append(now)

        # Prune old failures
        self._prune_old_failures()

        # Count recent failures
        self._failure_count = len(self._failures_in_window)

        # State transitions
        if self._state == CircuitState.HALF_OPEN:
            # Failure in HALF_OPEN → back to OPEN
            logger.warning("⚠️ Recovery test failed, circuit OPEN again")
            self._transition_to(CircuitState.OPEN)

        elif self._state == CircuitState.CLOSED:
            # Check if we should open circuit
            if self._failure_count >= self.failure_threshold:
                self._transition_to(CircuitState.OPEN)
            else:
                logger.warning(f"⚠️ NATS failure {self._failure_count}/{self.failure_threshold} "
                             f"(window={self.monitoring_window}s)")

    def reset(self):
        """Manually reset circuit breaker to CLOSED state"""
        logger.info("🔄 Manual circuit breaker reset")
        self._transition_to(CircuitState.CLOSED)

    def get_stats(self) -> dict:
        """Get circuit breaker statistics"""
        return {
            'state': self._state.value,
            'failure_count': self._failure_count,
            'failures_in_window': len(self._failures_in_window),
            'is_open': self.is_open,
            'opened_at': self.stats.get('last_opened'),
            'closed_at': self.stats.get('last_closed'),
            'total_calls': self.stats['total_calls'],
            'total_successes': self.stats['total_successes'],
            'total_failures': self.stats['total_failures'],
            'state_transitions': self.stats['state_transitions']
        }

    def __str__(self) -> str:
        """String representation"""
        return (f"CircuitBreaker(state={self._state.value}, "
                f"failures={self._failure_count}/{self.failure_threshold})")
