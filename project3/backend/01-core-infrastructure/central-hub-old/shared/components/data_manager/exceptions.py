"""
Custom Exceptions for Database Manager
Hierarchical exception structure for better error handling
"""


class DataManagerError(Exception):
    """Base exception for all Data Manager errors"""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self):
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class DatabaseConnectionError(DataManagerError):
    """Database connection failed"""
    def __init__(self, database: str, message: str, details: dict = None):
        self.database = database
        super().__init__(
            f"[{database}] Connection error: {message}",
            details
        )


class QueryTimeoutError(DataManagerError):
    """Query execution timeout"""
    def __init__(self, database: str, query: str, timeout_seconds: int):
        self.database = database
        self.query = query
        self.timeout_seconds = timeout_seconds
        super().__init__(
            f"[{database}] Query timeout after {timeout_seconds}s",
            {"query": query[:200]}  # Truncate long queries
        )


class QueryExecutionError(DataManagerError):
    """Query execution failed"""
    def __init__(self, database: str, query: str, error: str):
        self.database = database
        self.query = query
        self.error = error
        super().__init__(
            f"[{database}] Query failed: {error}",
            {"query": query[:200]}
        )


class CacheError(DataManagerError):
    """Cache operation failed"""
    def __init__(self, operation: str, key: str, error: str):
        self.operation = operation
        self.key = key
        self.error = error
        super().__init__(
            f"Cache {operation} failed for key '{key}': {error}",
            {"operation": operation, "key": key}
        )


class ValidationError(DataManagerError):
    """Data validation failed"""
    def __init__(self, model: str, errors: list):
        self.model = model
        self.errors = errors
        super().__init__(
            f"Validation failed for {model}",
            {"errors": errors}
        )


class ConfigurationError(DataManagerError):
    """Configuration loading or validation failed"""
    def __init__(self, config_type: str, message: str):
        self.config_type = config_type
        super().__init__(
            f"Configuration error ({config_type}): {message}"
        )


class ConnectionPoolExhaustedError(DataManagerError):
    """Connection pool has no available connections"""
    def __init__(self, database: str, pool_size: int, timeout: int):
        self.database = database
        self.pool_size = pool_size
        self.timeout = timeout
        super().__init__(
            f"[{database}] Connection pool exhausted (size: {pool_size}, timeout: {timeout}s)"
        )


class RoutingError(DataManagerError):
    """Smart routing failed to find suitable database"""
    def __init__(self, operation: str, message: str):
        self.operation = operation
        super().__init__(
            f"Routing error for operation '{operation}': {message}"
        )


class CircuitBreakerOpenError(DataManagerError):
    """Circuit breaker is open, preventing requests"""
    def __init__(self, database: str, failure_count: int):
        self.database = database
        self.failure_count = failure_count
        super().__init__(
            f"[{database}] Circuit breaker OPEN after {failure_count} failures"
        )


class RetryExhaustedError(DataManagerError):
    """All retry attempts exhausted"""
    def __init__(self, operation: str, attempts: int, last_error: str):
        self.operation = operation
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(
            f"Retry exhausted for '{operation}' after {attempts} attempts. Last error: {last_error}"
        )
