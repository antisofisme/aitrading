"""
Unit tests for CircuitBreaker pattern
"""

import pytest
import asyncio
from components.utils.patterns import (
    CircuitBreaker,
    CircuitBreakerManager,
    CircuitBreakerConfig,
    CircuitState,
    CircuitBreakerOpenError
)


class TestCircuitBreaker:
    """Test CircuitBreaker functionality"""

    @pytest.fixture
    def config(self):
        """Create CircuitBreakerConfig"""
        return CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=5,
            success_threshold=2,
            timeout=1.0
        )

    @pytest.fixture
    def circuit_breaker(self, config):
        """Create CircuitBreaker instance"""
        return CircuitBreaker("test_service", config)

    def test_initialization(self, circuit_breaker):
        """Test CircuitBreaker initialization"""
        assert circuit_breaker.name == "test_service"
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.metrics.total_requests == 0

    @pytest.mark.asyncio
    async def test_successful_call(self, circuit_breaker):
        """Test successful circuit breaker call"""
        async def success_func():
            return "success"

        result = await circuit_breaker.call(success_func)
        assert result == "success"
        assert circuit_breaker.metrics.successful_requests == 1
        assert circuit_breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_opens_after_failures(self, circuit_breaker):
        """Test circuit opens after threshold failures"""
        async def fail_func():
            raise Exception("Test failure")

        # Make enough failures to open circuit
        for _ in range(3):
            try:
                await circuit_breaker.call(fail_func)
            except Exception:
                pass

        assert circuit_breaker.state == CircuitState.OPEN
        assert circuit_breaker.metrics.failed_requests == 3

    @pytest.mark.asyncio
    async def test_circuit_rejects_when_open(self, circuit_breaker):
        """Test circuit rejects calls when open"""
        # Open the circuit first
        circuit_breaker._change_state(CircuitState.OPEN)

        async def dummy_func():
            return "should_not_run"

        with pytest.raises(CircuitBreakerOpenError):
            await circuit_breaker.call(dummy_func)


class TestCircuitBreakerManager:
    """Test CircuitBreakerManager functionality"""

    @pytest.fixture
    def manager(self, service_name):
        """Create CircuitBreakerManager instance"""
        return CircuitBreakerManager(service_name)

    def test_initialization(self, manager, service_name):
        """Test CircuitBreakerManager initialization"""
        assert manager.service_name == service_name
        assert isinstance(manager.circuit_breakers, dict)
        assert len(manager.circuit_breakers) == 0

    def test_add_circuit_breaker(self, manager):
        """Test adding circuit breaker"""
        cb = manager.add_circuit_breaker("external_api")
        assert "external_api" in manager.circuit_breakers
        assert isinstance(cb, CircuitBreaker)

    def test_auto_create_circuit_breaker(self, manager):
        """Test auto-creation of circuit breaker"""
        cb = manager.get_circuit_breaker("new_service")
        assert "new_service" in manager.circuit_breakers
        assert isinstance(cb, CircuitBreaker)
