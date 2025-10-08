"""
Circuit Breaker Pattern - Prevents cascading failures

Usage:
    breaker = CircuitBreaker(failure_threshold=5, timeout_seconds=60)

    try:
        breaker.call(lambda: clickhouse_client.execute(...))
    except CircuitBreakerOpen:
        logger.error("ClickHouse unavailable - circuit breaker OPEN")
        # Don't commit Kafka offset - will retry later

States:
- CLOSED: Normal operation
- OPEN: Failures exceeded threshold, stop trying
- HALF_OPEN: Testing if service recovered
"""
import time
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "CLOSED"       # Normal operation
    OPEN = "OPEN"           # Too many failures, stop trying
    HALF_OPEN = "HALF_OPEN" # Testing recovery


class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is OPEN"""
    pass


class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures

    Protects against:
    - ClickHouse unavailability
    - Network partitions
    - Database overload
    """

    def __init__(self, failure_threshold: int = 5, timeout_seconds: int = 60, name: str = "unknown"):
        """
        Initialize circuit breaker

        Args:
            failure_threshold: Number of failures before opening circuit
            timeout_seconds: Time to wait before attempting HALF_OPEN
            name: Name for logging (e.g., "ClickHouse")
        """
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.name = name

        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

        logger.info(f"🔌 Circuit breaker initialized: {name} (threshold={failure_threshold}, timeout={timeout_seconds}s)")

    def call(self, func, *args, **kwargs):
        """
        Execute function with circuit breaker protection

        Args:
            func: Function to execute
            *args, **kwargs: Arguments to pass to function

        Returns:
            Function result

        Raises:
            CircuitBreakerOpen: If circuit is OPEN
            Exception: If function raises exception
        """
        # Check current state
        if self.state == CircuitState.OPEN:
            # Check if timeout elapsed
            if time.time() - self.last_failure_time > self.timeout_seconds:
                logger.info(f"🔌 Circuit breaker {self.name}: OPEN → HALF_OPEN (testing recovery)")
                self.state = CircuitState.HALF_OPEN
            else:
                remaining = self.timeout_seconds - (time.time() - self.last_failure_time)
                raise CircuitBreakerOpen(
                    f"Circuit breaker OPEN for {self.name} "
                    f"(retry in {remaining:.0f}s)"
                )

        # Try to execute function
        try:
            result = func(*args, **kwargs)

            # Success!
            if self.state == CircuitState.HALF_OPEN:
                # Recovered!
                logger.info(f"✅ Circuit breaker {self.name}: HALF_OPEN → CLOSED (service recovered)")
                self.state = CircuitState.CLOSED
                self.failure_count = 0

            return result

        except Exception as e:
            # Failure
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.state == CircuitState.HALF_OPEN:
                # Still broken
                logger.warning(f"⚠️ Circuit breaker {self.name}: HALF_OPEN → OPEN (service still down)")
                self.state = CircuitState.OPEN

            elif self.failure_count >= self.failure_threshold:
                # Too many failures
                logger.error(
                    f"🔴 Circuit breaker {self.name}: CLOSED → OPEN "
                    f"({self.failure_count} failures)"
                )
                self.state = CircuitState.OPEN

            # Re-raise exception
            raise

    def get_state(self) -> str:
        """Get current circuit breaker state"""
        return self.state.value

    def get_stats(self) -> dict:
        """Get circuit breaker statistics"""
        return {
            'state': self.state.value,
            'failure_count': self.failure_count,
            'last_failure_time': self.last_failure_time,
            'timeout_seconds': self.timeout_seconds
        }

    def reset(self):
        """Manually reset circuit breaker to CLOSED"""
        logger.info(f"🔄 Circuit breaker {self.name}: Manual reset to CLOSED")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
