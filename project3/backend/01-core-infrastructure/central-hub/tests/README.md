# Central Hub Tests

## Test Structure

```
tests/
├── unit/                          # Unit tests
│   ├── test_patterns/             # Pattern tests
│   │   ├── test_cache.py          # CacheManager tests
│   │   ├── test_database.py       # DatabaseManager tests
│   │   ├── test_circuit_breaker.py # CircuitBreaker tests
│   │   └── test_health.py         # HealthChecker tests
│   ├── test_domain/               # Domain model tests
│   └── test_api/                  # API endpoint tests
│
├── integration/                   # Integration tests
│   ├── test_database/             # Database integration
│   ├── test_messaging/            # Messaging integration
│   └── test_services/             # Service coordination
│
├── fixtures/                      # Test fixtures
│   ├── database_fixtures.py       # Database test data
│   └── service_fixtures.py        # Service test data
│
├── conftest.py                    # Pytest configuration
└── README.md                      # This file
```

## Running Tests

### All Tests
```bash
pytest tests/
```

### Unit Tests Only
```bash
pytest tests/unit/
```

### Integration Tests Only
```bash
pytest tests/integration/
```

### Specific Test File
```bash
pytest tests/unit/test_patterns/test_cache.py
```

### With Coverage
```bash
pytest --cov=base --cov=shared tests/
```

## Test Requirements

Add to `requirements.txt`:
```
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0
```

## Writing Tests

### Unit Test Example
```python
import pytest
from components.utils.patterns import CacheManager

class TestCacheManager:
    @pytest.fixture
    def cache_manager(self):
        return CacheManager("test-service")

    @pytest.mark.asyncio
    async def test_get_set(self, cache_manager):
        await cache_manager.set("key", "value")
        result = await cache_manager.get("key")
        assert result == "value"
```

### Integration Test Example
```python
import pytest
from central_hub_sdk import CentralHubClient

@pytest.mark.integration
class TestServiceRegistration:
    @pytest.mark.asyncio
    async def test_register_service(self):
        client = CentralHubClient("test-service", "test")
        response = await client.register()
        assert response["status"] == "registered"
```

## Test Status

- ✅ Test infrastructure created
- ⏳ Unit tests (TODO: Implement)
- ⏳ Integration tests (TODO: Implement)
- ⏳ API tests (TODO: Implement)
- ⏳ E2E tests (TODO: Plan)

## Next Steps

1. Implement unit tests for all patterns
2. Add integration tests for database connections
3. Add integration tests for messaging (NATS/Kafka)
4. Add API endpoint tests
5. Add E2E tests for service coordination
6. Set up CI/CD test automation
