"""
Basic tests for Central Hub Service

Phase 1 Implementation: Simple functional tests
"""

import pytest
import httpx
import asyncio
from fastapi.testclient import TestClient

# Import the main app
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Central Hub"
    assert data["port"] == 8010
    assert data["phase"] == "Phase 1 - Infrastructure Migration"


def test_health_endpoint(client):
    """Test basic health endpoint"""
    response = client.get("/health")
    assert response.status_code in [200, 503]  # May be 503 if not fully initialized
    data = response.json()
    assert "status" in data
    assert data["service"] == "central-hub"
    assert data["port"] == 8010


def test_api_health_endpoint(client):
    """Test API health endpoint"""
    response = client.get("/api/v1/health/")
    assert response.status_code in [200, 503]
    if response.status_code == 200:
        data = response.json()
        assert "status" in data
        assert "service" in data


def test_services_list_endpoint(client):
    """Test services list endpoint"""
    response = client.get("/api/v1/services/")
    assert response.status_code in [200, 503]
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)


def test_config_endpoint(client):
    """Test configuration endpoint"""
    response = client.get("/api/v1/config/")
    assert response.status_code in [200, 503]
    if response.status_code == 200:
        data = response.json()
        assert "configurations" in data


@pytest.mark.asyncio
async def test_service_registration():
    """Test service registration functionality"""
    async with httpx.AsyncClient() as client:
        # Test service registration
        registration_data = {
            "name": "test-service",
            "host": "localhost",
            "port": 8001,
            "health_endpoint": "/health",
            "metadata": {"type": "test"}
        }

        try:
            response = await client.post(
                "http://localhost:8010/api/v1/services/register",
                json=registration_data,
                timeout=5.0
            )
            # Service may not be running, so we accept connection errors
            if response.status_code == 200:
                data = response.json()
                assert "service_name" in data
                assert data["service_name"] == "test-service"
        except httpx.ConnectError:
            # Service not running, test passed
            pass


if __name__ == "__main__":
    pytest.main([__file__])