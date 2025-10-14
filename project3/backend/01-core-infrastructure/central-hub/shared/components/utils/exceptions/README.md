# Central Hub Exception Hierarchy

## Overview

Comprehensive domain exception hierarchy for structured error handling with error codes, severity levels, and rich context.

## Exception Structure

```
CentralHubError (Base)
├── ServiceRegistrationError
│   ├── ServiceNotFoundError
│   ├── ServiceAlreadyExistsError
│   ├── InvalidServiceConfigError
│   └── ServiceHealthCheckFailedError
├── ServiceDiscoveryError
│   ├── DiscoveryTimeoutError
│   └── NoHealthyInstanceError
├── ConfigurationError
│   ├── ConfigNotFoundError
│   ├── ConfigValidationError
│   └── ConfigReloadError
├── CoordinationError
│   ├── WorkflowExecutionError
│   ├── ServiceCommunicationError
│   └── DeadlockDetectedError
└── InfrastructureError
    ├── DatabaseConnectionError
    ├── CacheConnectionError
    └── MessagingConnectionError
```

## Usage Examples

### Basic Usage

```python
from components.utils.exceptions import (
    ServiceNotFoundError,
    InvalidServiceConfigError,
    DatabaseConnectionError
)

# Raise domain exception
def get_service(service_name: str):
    if service_name not in registry:
        raise ServiceNotFoundError(service_name)
    return registry[service_name]

# Catch specific exception
try:
    service = get_service("api-gateway")
except ServiceNotFoundError as e:
    logger.error(f"[{e.code}] {e.message}")
    # Returns: [CH-2001] Service 'api-gateway' not found in registry
```

### With Error Context

```python
from components.utils.exceptions import InvalidServiceConfigError

def validate_service_config(config: dict):
    errors = {}

    if not config.get("name"):
        errors["name"] = "Service name is required"

    if not config.get("port") or config["port"] < 1:
        errors["port"] = "Valid port number required"

    if errors:
        raise InvalidServiceConfigError(
            validation_errors=errors
        )
```

### Wrapping Original Exceptions

```python
from components.utils.exceptions import DatabaseConnectionError

try:
    await asyncpg.connect(dsn=database_url)
except asyncpg.PostgresConnectionError as e:
    raise DatabaseConnectionError(
        database_name="central_hub",
        host="localhost",
        port=5432,
        cause=e  # Original exception
    )
```

### API Error Responses

```python
from fastapi import HTTPException
from components.utils.exceptions import CentralHubError, ServiceNotFoundError

@app.get("/services/{name}")
async def get_service(name: str):
    try:
        service = await service_registry.get(name)
        return service
    except ServiceNotFoundError as e:
        # Convert to API response
        raise HTTPException(
            status_code=404,
            detail=e.to_dict()
        )
    except CentralHubError as e:
        # Generic error handler
        raise HTTPException(
            status_code=500,
            detail=e.to_dict()
        )
```

**API Response Example:**
```json
{
  "detail": {
    "error": {
      "code": "CH-2001",
      "message": "Service 'api-gateway' not found in registry",
      "severity": "medium",
      "details": {
        "service_name": "api-gateway"
      }
    }
  }
}
```

### Severity-Based Handling

```python
from components.utils.exceptions import CentralHubError, ErrorSeverity

try:
    result = await risky_operation()
except CentralHubError as e:
    if e.severity == ErrorSeverity.CRITICAL:
        # Trigger alert
        await alert_manager.trigger_alert(e)
        # Shutdown gracefully
        await shutdown()
    elif e.severity == ErrorSeverity.HIGH:
        # Log and retry
        logger.error(f"High severity error: {e}")
        await retry_with_backoff()
    else:
        # Log and continue
        logger.warning(f"Recoverable error: {e}")
```

## Error Codes Reference

### Base Codes (1000-1999)
- `CH-1000` - Unknown error
- `CH-1001` - Internal error
- `CH-1002` - Validation error
- `CH-1003` - Not found
- `CH-1004` - Already exists
- `CH-1007` - Timeout

### Service Registry (2000-2999)
- `CH-2000` - Service registration failed
- `CH-2001` - Service not found
- `CH-2002` - Service already exists
- `CH-2003` - Invalid service config
- `CH-2004` - Service health check failed

### Discovery (3000-3999)
- `CH-3000` - Service discovery failed
- `CH-3001` - Discovery timeout
- `CH-3002` - No healthy instance

### Configuration (4000-4999)
- `CH-4000` - Config not found
- `CH-4001` - Config validation failed
- `CH-4002` - Config reload failed

### Coordination (5000-5999)
- `CH-5000` - Coordination failed
- `CH-5001` - Workflow execution failed
- `CH-5002` - Service communication error
- `CH-5003` - Deadlock detected

### Infrastructure (6000-6999)
- `CH-6000` - Database connection error
- `CH-6001` - Cache connection error
- `CH-6002` - Messaging connection error

## Severity Levels

| Level | Description | Action |
|-------|-------------|--------|
| **LOW** | Recoverable, log and continue | Log warning |
| **MEDIUM** | Recoverable with retry | Log error, retry |
| **HIGH** | Service degradation | Log error, alert, failover |
| **CRITICAL** | Service failure | Log critical, alert, shutdown |

## Creating Custom Exceptions

```python
from components.utils.exceptions import CentralHubError, ErrorCode, ErrorSeverity

class CustomOperationError(CentralHubError):
    """Custom operation failed"""
    code = "CH-9000"  # Use custom range
    severity = ErrorSeverity.HIGH
    message = "Custom operation failed"

    def __init__(self, operation_id: str, reason: str, **kwargs):
        super().__init__(
            message=f"Operation {operation_id} failed: {reason}",
            details={
                "operation_id": operation_id,
                "reason": reason
            },
            **kwargs
        )
```

## Best Practices

1. **Always use domain exceptions** instead of generic `Exception`
   ```python
   # ❌ Bad
   raise Exception("Service not found")

   # ✅ Good
   raise ServiceNotFoundError("api-gateway")
   ```

2. **Provide context in details**
   ```python
   raise ServiceCommunicationError(
       source_service="api-gateway",
       target_service="data-bridge",
       operation="fetch_ticks"
   )
   ```

3. **Wrap infrastructure exceptions**
   ```python
   try:
       await database.connect()
   except ConnectionError as e:
       raise DatabaseConnectionError(..., cause=e)
   ```

4. **Use severity levels appropriately**
   - LOW: User mistakes, retryable
   - MEDIUM: Temporary failures
   - HIGH: Service degradation
   - CRITICAL: Complete failure

5. **Log with error codes**
   ```python
   logger.error(f"[{e.code}] {e.message}", extra=e.details)
   ```

## Testing

```python
import pytest
from components.utils.exceptions import ServiceNotFoundError, ErrorCode

def test_service_not_found():
    with pytest.raises(ServiceNotFoundError) as exc_info:
        raise ServiceNotFoundError("test-service")

    error = exc_info.value
    assert error.code == ErrorCode.SERVICE_NOT_FOUND
    assert "test-service" in error.message
    assert error.details["service_name"] == "test-service"
```

## Integration with Patterns

```python
# In service_registry.py
from components.utils.exceptions import (
    ServiceNotFoundError,
    ServiceAlreadyExistsError,
    InvalidServiceConfigError
)

class ServiceRegistry:
    async def register(self, service_data: dict):
        # Validate
        if not service_data.get("name"):
            raise InvalidServiceConfigError(
                validation_errors={"name": "Required"}
            )

        # Check duplicates
        if service_data["name"] in self.services:
            raise ServiceAlreadyExistsError(service_data["name"])

        # Register
        self.services[service_data["name"]] = service_data

    async def get(self, service_name: str):
        if service_name not in self.services:
            raise ServiceNotFoundError(service_name)
        return self.services[service_name]
```

## Migration from Generic Exceptions

**Before:**
```python
if not service_found:
    raise ValueError(f"Service {name} not found")
```

**After:**
```python
if not service_found:
    raise ServiceNotFoundError(name)
```

---

**Benefits:**
- ✅ Structured error handling
- ✅ Client-friendly error codes
- ✅ Rich context for debugging
- ✅ Severity-based routing
- ✅ Better observability
