"""
Pytest configuration and fixtures for Central Hub tests
"""

import pytest
import sys
from pathlib import Path

# Add shared to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent.parent / "base"))


@pytest.fixture
def service_name():
    """Common service name for tests"""
    return "test-service"


@pytest.fixture
async def mock_database():
    """Mock database connection for tests"""
    # TODO: Implement mock database
    pass


@pytest.fixture
async def mock_cache():
    """Mock cache connection for tests"""
    # TODO: Implement mock cache
    pass


@pytest.fixture
async def mock_messaging():
    """Mock messaging connection for tests"""
    # TODO: Implement mock messaging (NATS/Kafka)
    pass
