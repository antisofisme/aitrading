"""
mt5_error_handling.py - MT5 Error Handling Utilities

🎯 PURPOSE:
Business: Specialized error handling for MT5 trading operations
Technical: MT5-specific error codes, recovery strategies, and diagnostics
Domain: Error Handling/MT5 Integration/Trading Operations

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:28.028Z
Session: client-side-ai-brain-full-compliance
Confidence: 92%
Complexity: medium

🧩 PATTERNS USED:
- AI_BRAIN_MT5_ERROR_HANDLING: Specialized MT5 error handling and recovery

📦 DEPENDENCIES:
Internal: error_manager, logger_manager
External: MetaTrader5, enum, typing

💡 AI DECISION REASONING:
MT5 operations have specific error codes and recovery patterns requiring specialized handling for reliable trading.

🚀 USAGE:
mt5_error_handling.handle_mt5_error(error_code, context)

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

import asyncio
import logging
import time
from typing import Callable, Any, Optional, Dict, List
from functools import wraps
from dataclasses import dataclass
from enum import Enum


class MT5ErrorType(Enum):
    """MT5 error types"""
    CONNECTION_ERROR = "connection_error"
    AUTHENTICATION_ERROR = "authentication_error"
    WEBSOCKET_ERROR = "websocket_error"
    STREAMING_ERROR = "streaming_error"
    TRADING_ERROR = "trading_error"
    TIMEOUT_ERROR = "timeout_error"
    NETWORK_ERROR = "network_error"
    CONFIGURATION_ERROR = "configuration_error"


@dataclass
class MT5ErrorContext:
    """MT5 error context information"""
    error_type: MT5ErrorType
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: float = None
    component: str = "mt5_bridge"
    recoverable: bool = True
    retry_count: int = 0
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class MT5ErrorHandler:
    """MT5 error handler with logging and metrics"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_counts = {}
        self.last_errors = []
        self.max_error_history = 100
    
    def handle_error(self, error_context: MT5ErrorContext) -> bool:
        """Handle MT5 error and return whether to retry"""
        # Log error
        self.logger.error(f"MT5 Error [{error_context.error_type.value}]: {error_context.message}")
        if error_context.details:
            self.logger.error(f"Details: {error_context.details}")
        
        # Track error statistics
        error_key = f"{error_context.component}_{error_context.error_type.value}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Add to error history
        self.last_errors.append(error_context)
        if len(self.last_errors) > self.max_error_history:
            self.last_errors.pop(0)
        
        # Determine if error is recoverable
        if error_context.error_type in [MT5ErrorType.AUTHENTICATION_ERROR, MT5ErrorType.CONFIGURATION_ERROR]:
            self.logger.error("❌ Non-recoverable error detected")
            return False
        
        if error_context.retry_count >= 10:
            self.logger.error("❌ Max retry attempts exceeded")
            return False
        
        return error_context.recoverable
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        return {
            "error_counts": self.error_counts,
            "total_errors": sum(self.error_counts.values()),
            "recent_errors": len(self.last_errors),
            "error_types": list(set(error.error_type.value for error in self.last_errors[-10:]))
        }


# Global error handler instance
_error_handler = MT5ErrorHandler()


def retry_with_backoff(
    max_attempts: int = 5,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
    error_type: MT5ErrorType = MT5ErrorType.CONNECTION_ERROR
):
    """
    Retry decorator with exponential backoff for MT5 operations
    
    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        backoff_factor: Exponential backoff factor
        exceptions: Tuple of exceptions to catch and retry
        error_type: Type of MT5 error for logging
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            delay = initial_delay
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    error_context = MT5ErrorContext(
                        error_type=error_type,
                        message=f"Attempt {attempt + 1}/{max_attempts} failed: {str(e)}",
                        details={"function": func.__name__, "attempt": attempt + 1, "exception": str(e)},
                        retry_count=attempt
                    )
                    
                    should_retry = _error_handler.handle_error(error_context)
                    
                    if not should_retry or attempt == max_attempts - 1:
                        break
                    
                    # Wait before retry
                    await asyncio.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)
            
            # All attempts failed
            final_context = MT5ErrorContext(
                error_type=error_type,
                message=f"All {max_attempts} attempts failed for {func.__name__}",
                details={"last_exception": str(last_exception)},
                recoverable=False
            )
            _error_handler.handle_error(final_context)
            
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            delay = initial_delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    error_context = MT5ErrorContext(
                        error_type=error_type,
                        message=f"Attempt {attempt + 1}/{max_attempts} failed: {str(e)}",
                        details={"function": func.__name__, "attempt": attempt + 1, "exception": str(e)},
                        retry_count=attempt
                    )
                    
                    should_retry = _error_handler.handle_error(error_context)
                    
                    if not should_retry or attempt == max_attempts - 1:
                        break
                    
                    # Wait before retry
                    time.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)
            
            # All attempts failed
            final_context = MT5ErrorContext(
                error_type=error_type,
                message=f"All {max_attempts} attempts failed for {func.__name__}",
                details={"last_exception": str(last_exception)},
                recoverable=False
            )
            _error_handler.handle_error(final_context)
            
            raise last_exception
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def handle_mt5_connection_error(error: Exception, context: str = "MT5 Connection") -> MT5ErrorContext:
    """Handle MT5 connection errors"""
    error_context = MT5ErrorContext(
        error_type=MT5ErrorType.CONNECTION_ERROR,
        message=f"MT5 connection failed: {str(error)}",
        details={"context": context, "error_type": type(error).__name__},
        component="mt5_connection"
    )
    
    # Check if it's an authentication error
    if "login" in str(error).lower() or "password" in str(error).lower() or "authentication" in str(error).lower():
        error_context.error_type = MT5ErrorType.AUTHENTICATION_ERROR
        error_context.recoverable = False
    
    _error_handler.handle_error(error_context)
    return error_context


def handle_websocket_error(error: Exception, context: str = "WebSocket Connection") -> MT5ErrorContext:
    """Handle WebSocket connection errors"""
    error_context = MT5ErrorContext(
        error_type=MT5ErrorType.WEBSOCKET_ERROR,
        message=f"WebSocket error: {str(error)}",
        details={"context": context, "error_type": type(error).__name__},
        component="websocket_client"
    )
    
    # Check if it's a network error
    if "network" in str(error).lower() or "connection" in str(error).lower():
        error_context.error_type = MT5ErrorType.NETWORK_ERROR
    
    _error_handler.handle_error(error_context)
    return error_context


def handle_streaming_error(error: Exception, context: str = "Streaming") -> MT5ErrorContext:
    """Handle streaming/RedPanda errors"""
    error_context = MT5ErrorContext(
        error_type=MT5ErrorType.STREAMING_ERROR,
        message=f"Streaming error: {str(error)}",
        details={"context": context, "error_type": type(error).__name__},
        component="streaming_client"
    )
    
    # Check if it's a timeout error
    if "timeout" in str(error).lower():
        error_context.error_type = MT5ErrorType.TIMEOUT_ERROR
    
    _error_handler.handle_error(error_context)
    return error_context


def handle_trading_error(error: Exception, symbol: str = "UNKNOWN", context: str = "Trading") -> MT5ErrorContext:
    """Handle trading operation errors"""
    error_context = MT5ErrorContext(
        error_type=MT5ErrorType.TRADING_ERROR,
        message=f"Trading error for {symbol}: {str(error)}",
        details={"context": context, "symbol": symbol, "error_type": type(error).__name__},
        component="trading_client"
    )
    
    _error_handler.handle_error(error_context)
    return error_context


def get_error_statistics() -> Dict[str, Any]:
    """Get MT5 error statistics"""
    return _error_handler.get_error_stats()


def reset_error_statistics():
    """Reset MT5 error statistics"""
    global _error_handler
    _error_handler = MT5ErrorHandler()


# Circuit breaker pattern for MT5 operations
class MT5CircuitBreaker:
    """Circuit breaker for MT5 operations"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.logger = logging.getLogger(__name__)
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                self.logger.info("🔄 Circuit breaker half-open, trying recovery")
            else:
                raise Exception("Circuit breaker is OPEN - too many failures")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful operation"""
        self.failure_count = 0
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            self.logger.info("✅ Circuit breaker closed - service recovered")
    
    def _on_failure(self):
        """Handle failed operation"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            self.logger.error(f"⚠️ Circuit breaker opened - {self.failure_count} failures")
    
    def get_state(self) -> Dict[str, Any]:
        """Get circuit breaker state"""
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": self.last_failure_time,
            "recovery_timeout": self.recovery_timeout
        }


# Global circuit breaker instance
_circuit_breaker = MT5CircuitBreaker()


def with_circuit_breaker(func: Callable) -> Callable:
    """Decorator to add circuit breaker protection"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        return _circuit_breaker.call(func, *args, **kwargs)
    return wrapper


def get_circuit_breaker_state() -> Dict[str, Any]:
    """Get circuit breaker state"""
    return _circuit_breaker.get_state()


# Demo function for testing
def demo_mt5_error_handling():
    """Demo function to test MT5 error handling"""
    print("🧪 Testing MT5 Bridge Error Handling")
    print("=" * 40)
    
    # Test error context
    error_context = MT5ErrorContext(
        error_type=MT5ErrorType.CONNECTION_ERROR,
        message="Test connection error",
        details={"test": True}
    )
    print(f"✅ Error context: {error_context.error_type.value}")
    
    # Test error handler
    handler = MT5ErrorHandler()
    should_retry = handler.handle_error(error_context)
    print(f"✅ Should retry: {should_retry}")
    
    # Test specific error handlers
    test_error = Exception("Test error")
    mt5_context = handle_mt5_connection_error(test_error)
    print(f"✅ MT5 error context: {mt5_context.error_type.value}")
    
    ws_context = handle_websocket_error(test_error)
    print(f"✅ WebSocket error context: {ws_context.error_type.value}")
    
    streaming_context = handle_streaming_error(test_error)
    print(f"✅ Streaming error context: {streaming_context.error_type.value}")
    
    # Test circuit breaker
    circuit_breaker = MT5CircuitBreaker(failure_threshold=3)
    state = circuit_breaker.get_state()
    print(f"✅ Circuit breaker state: {state['state']}")
    
    # Test error statistics
    stats = get_error_statistics()
    print(f"✅ Error statistics: {stats['total_errors']} total errors")
    
    print("\n🎉 MT5 error handling demo completed!")


if __name__ == "__main__":
    demo_mt5_error_handling()