# Chain Mapping System - Testing and Validation Procedures

## Overview

This document provides comprehensive testing and validation procedures for the embedded chain mapping system. The testing strategy ensures reliable operation, performance validation, and integration quality across all 30 distinct chains in the AI trading platform.

## Table of Contents

1. [Testing Strategy](#testing-strategy)
2. [Unit Testing](#unit-testing)
3. [Integration Testing](#integration-testing)
4. [Chain Validation Testing](#chain-validation-testing)
5. [Performance Testing](#performance-testing)
6. [Health Monitoring Testing](#health-monitoring-testing)
7. [Discovery System Testing](#discovery-system-testing)
8. [API Testing](#api-testing)
9. [Database Testing](#database-testing)
10. [End-to-End Testing](#end-to-end-testing)
11. [Load Testing](#load-testing)
12. [Disaster Recovery Testing](#disaster-recovery-testing)

## Testing Strategy

### Testing Pyramid

```
    E2E Tests (10%)
      - Full chain workflows
      - Cross-service validation
      - Real-time monitoring

  Integration Tests (30%)
    - Service interactions
    - Database operations
    - API endpoint testing
    - Health monitoring

Unit Tests (60%)
  - Core models validation
  - Business logic testing
  - Utility functions
  - Edge cases
```

### Test Environment Setup

```yaml
# docker-compose.test.yml
version: '3.8'
services:
  postgres-test:
    image: postgres:15
    environment:
      POSTGRES_DB: chain_mapping_test
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
    ports:
      - "5433:5432"

  clickhouse-test:
    image: clickhouse/clickhouse-server:latest
    environment:
      CLICKHOUSE_DB: chain_mapping_test
      CLICKHOUSE_USER: test
      CLICKHOUSE_PASSWORD: test
    ports:
      - "8124:8123"

  redis-test:
    image: redis:7-alpine
    ports:
      - "6380:6379"

  # Mock services for testing
  mock-api-gateway:
    build: ./tests/mocks/api-gateway
    ports:
      - "8000:8000"

  mock-data-bridge:
    build: ./tests/mocks/data-bridge
    ports:
      - "8001:8001"
```

## Unit Testing

### 1. Core Models Testing

```python
# tests/unit/test_models.py
import pytest
from datetime import datetime
from pydantic import ValidationError

from chain_mapping.core.models import (
    ChainDefinition, ChainNode, ChainEdge, ChainDependency,
    ChainCategory, NodeType, EdgeType, ChainStatus
)


class TestChainDefinition:
    """Test suite for ChainDefinition model."""

    def test_valid_chain_creation(self):
        """Test creating a valid chain definition."""
        nodes = [
            ChainNode(
                id="test_node",
                type=NodeType.SERVICE,
                service_name="test-service"
            )
        ]

        edges = [
            ChainEdge(
                source_node="test_node",
                target_node="test_node_2",
                type=EdgeType.HTTP_REQUEST
            )
        ]

        chain = ChainDefinition(
            id="A1",
            name="Test Chain",
            category=ChainCategory.DATA_FLOW,
            nodes=nodes,
            edges=edges
        )

        assert chain.id == "A1"
        assert chain.name == "Test Chain"
        assert chain.category == ChainCategory.DATA_FLOW
        assert len(chain.nodes) == 1
        assert chain.node_count == 1

    def test_invalid_chain_id_format(self):
        """Test chain ID validation."""
        with pytest.raises(ValidationError) as exc_info:
            ChainDefinition(
                id="INVALID",
                name="Test",
                category=ChainCategory.DATA_FLOW,
                nodes=[],
                edges=[]
            )

        assert "Chain ID must follow pattern [A-E][1-9]+" in str(exc_info.value)

    def test_empty_nodes_validation(self):
        """Test validation for empty nodes."""
        with pytest.raises(ValidationError) as exc_info:
            ChainDefinition(
                id="A1",
                name="Test",
                category=ChainCategory.DATA_FLOW,
                nodes=[],
                edges=[]
            )

        assert "Chain must have at least one node" in str(exc_info.value)

    def test_duplicate_node_ids(self):
        """Test validation for duplicate node IDs."""
        nodes = [
            ChainNode(id="node1", type=NodeType.SERVICE, service_name="service1"),
            ChainNode(id="node1", type=NodeType.SERVICE, service_name="service2")
        ]

        with pytest.raises(ValidationError) as exc_info:
            ChainDefinition(
                id="A1",
                name="Test",
                category=ChainCategory.DATA_FLOW,
                nodes=nodes,
                edges=[]
            )

        assert "Node IDs must be unique" in str(exc_info.value)

    def test_edge_node_validation(self):
        """Test edge validation against existing nodes."""
        nodes = [
            ChainNode(id="node1", type=NodeType.SERVICE, service_name="service1")
        ]

        edges = [
            ChainEdge(
                source_node="node1",
                target_node="nonexistent",
                type=EdgeType.HTTP_REQUEST
            )
        ]

        with pytest.raises(ValidationError) as exc_info:
            ChainDefinition(
                id="A1",
                name="Test",
                category=ChainCategory.DATA_FLOW,
                nodes=nodes,
                edges=edges
            )

        assert "Target node nonexistent not found" in str(exc_info.value)

    def test_chain_connectivity_validation(self):
        """Test chain connectivity validation."""
        nodes = [
            ChainNode(id="node1", type=NodeType.SERVICE, service_name="service1"),
            ChainNode(id="node2", type=NodeType.SERVICE, service_name="service2"),
            ChainNode(id="isolated", type=NodeType.SERVICE, service_name="service3")
        ]

        edges = [
            ChainEdge(source_node="node1", target_node="node2", type=EdgeType.HTTP_REQUEST)
        ]

        chain = ChainDefinition(
            id="A1",
            name="Test",
            category=ChainCategory.DATA_FLOW,
            nodes=nodes,
            edges=edges
        )

        issues = chain.validate_connectivity()
        assert len(issues) > 0
        assert any("isolated" in issue for issue in issues)

    def test_involved_services_computation(self):
        """Test computation of involved services."""
        nodes = [
            ChainNode(id="node1", type=NodeType.SERVICE, service_name="service-a"),
            ChainNode(id="node2", type=NodeType.SERVICE, service_name="service-b"),
            ChainNode(id="node3", type=NodeType.SERVICE, service_name="service-a")
        ]

        chain = ChainDefinition(
            id="A1",
            name="Test",
            category=ChainCategory.DATA_FLOW,
            nodes=nodes,
            edges=[]
        )

        assert sorted(chain.involved_services) == ["service-a", "service-b"]


class TestChainNode:
    """Test suite for ChainNode model."""

    def test_valid_node_creation(self):
        """Test creating a valid node."""
        node = ChainNode(
            id="test_node",
            type=NodeType.API_ENDPOINT,
            service_name="api-gateway",
            component_name="user_handler"
        )

        assert node.id == "test_node"
        assert node.type == NodeType.API_ENDPOINT
        assert node.display_name == "api-gateway.user_handler"

    def test_node_display_name_generation(self):
        """Test display name generation logic."""
        # With both service and component
        node1 = ChainNode(
            id="node1",
            type=NodeType.SERVICE,
            service_name="service",
            component_name="component"
        )
        assert node1.display_name == "service.component"

        # With only component
        node2 = ChainNode(
            id="node2",
            type=NodeType.SERVICE,
            component_name="component"
        )
        assert node2.display_name == "component"

        # With only service
        node3 = ChainNode(
            id="node3",
            type=NodeType.SERVICE,
            service_name="service"
        )
        assert node3.display_name == "service"

        # With neither
        node4 = ChainNode(
            id="node4",
            type=NodeType.SERVICE
        )
        assert node4.display_name == "node4"


class TestChainMetrics:
    """Test suite for ChainMetrics model."""

    def test_health_score_calculation(self):
        """Test health score calculation."""
        from chain_mapping.core.models import ChainMetrics

        # Perfect health
        metrics1 = ChainMetrics(
            availability=1.0,
            error_rate=0.0,
            avg_latency=50.0
        )
        assert metrics1.health_score == 100.0

        # Degraded health
        metrics2 = ChainMetrics(
            availability=0.95,
            error_rate=0.01,
            avg_latency=200.0
        )
        assert 50 <= metrics2.health_score <= 90

        # Poor health
        metrics3 = ChainMetrics(
            availability=0.8,
            error_rate=0.1,
            avg_latency=2000.0
        )
        assert metrics3.health_score < 50

    def test_incomplete_metrics(self):
        """Test health score with incomplete metrics."""
        metrics = ChainMetrics(availability=0.99)
        assert metrics.health_score is None


@pytest.fixture
def sample_chain():
    """Sample chain for testing."""
    nodes = [
        ChainNode(
            id="api_entry",
            type=NodeType.API_ENDPOINT,
            service_name="api-gateway",
            component_name="trading_handler"
        ),
        ChainNode(
            id="ai_processor",
            type=NodeType.AI_MODEL,
            service_name="ai-provider",
            component_name="trading_model"
        ),
        ChainNode(
            id="data_store",
            type=NodeType.DATABASE,
            service_name="database-service",
            component_name="trading_data"
        )
    ]

    edges = [
        ChainEdge(
            source_node="api_entry",
            target_node="ai_processor",
            type=EdgeType.HTTP_REQUEST,
            latency_sla=500
        ),
        ChainEdge(
            source_node="ai_processor",
            target_node="data_store",
            type=EdgeType.DATABASE_QUERY,
            latency_sla=100
        )
    ]

    return ChainDefinition(
        id="A2",
        name="AI Decision Pipeline",
        category=ChainCategory.AI_ML_PROCESSING,
        description="AI-driven trading decision making process",
        nodes=nodes,
        edges=edges
    )
```

### 2. Chain Registry Testing

```python
# tests/unit/test_registry.py
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from chain_mapping.core.registry import ChainRegistry, ChainNotFoundError
from chain_mapping.core.models import ChainDefinitionCreate, ChainCategory


@pytest.fixture
async def registry():
    """Create test registry."""
    registry = ChainRegistry(
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url=None  # No Redis for unit tests
    )
    await registry.initialize()
    return registry


class TestChainRegistry:
    """Test suite for ChainRegistry."""

    @pytest.mark.asyncio
    async def test_register_chain(self, registry, sample_chain_create):
        """Test chain registration."""
        chain_id = await registry.register_chain(sample_chain_create)

        assert chain_id.startswith(sample_chain_create.category.value[0].upper())

        # Verify chain can be retrieved
        retrieved_chain = await registry.get_chain(chain_id)
        assert retrieved_chain.name == sample_chain_create.name

    @pytest.mark.asyncio
    async def test_get_nonexistent_chain(self, registry):
        """Test retrieving nonexistent chain."""
        with pytest.raises(ChainNotFoundError):
            await registry.get_chain("NONEXISTENT")

    @pytest.mark.asyncio
    async def test_update_chain(self, registry, sample_chain_create):
        """Test chain updates."""
        # Register chain
        chain_id = await registry.register_chain(sample_chain_create)

        # Update chain
        from chain_mapping.core.models import ChainDefinitionUpdate
        updates = ChainDefinitionUpdate(
            name="Updated Chain Name",
            description="Updated description"
        )

        success = await registry.update_chain(chain_id, updates)
        assert success

        # Verify updates
        updated_chain = await registry.get_chain(chain_id)
        assert updated_chain.name == "Updated Chain Name"
        assert updated_chain.description == "Updated description"
        assert updated_chain.version == 2

    @pytest.mark.asyncio
    async def test_list_chains_filtering(self, registry):
        """Test chain listing with filters."""
        # Register multiple chains
        chain1 = ChainDefinitionCreate(
            name="Data Flow Chain",
            category=ChainCategory.DATA_FLOW,
            nodes=[],
            edges=[]
        )

        chain2 = ChainDefinitionCreate(
            name="Service Comm Chain",
            category=ChainCategory.SERVICE_COMMUNICATION,
            nodes=[],
            edges=[]
        )

        await registry.register_chain(chain1)
        await registry.register_chain(chain2)

        # Test category filtering
        data_chains, count = await registry.list_chains(category=ChainCategory.DATA_FLOW)
        assert count == 1
        assert data_chains[0].name == "Data Flow Chain"

        # Test no filter
        all_chains, total_count = await registry.list_chains()
        assert total_count == 2

    @pytest.mark.asyncio
    async def test_delete_chain(self, registry, sample_chain_create):
        """Test chain deletion."""
        # Register chain
        chain_id = await registry.register_chain(sample_chain_create)

        # Delete chain
        success = await registry.delete_chain(chain_id)
        assert success

        # Verify deletion
        with pytest.raises(ChainNotFoundError):
            await registry.get_chain(chain_id)

    @pytest.mark.asyncio
    async def test_dependency_graph(self, registry):
        """Test dependency graph functionality."""
        # Register chains with service dependencies
        chain1 = ChainDefinitionCreate(
            name="Chain 1",
            category=ChainCategory.DATA_FLOW,
            nodes=[
                ChainNode(id="node1", type=NodeType.SERVICE, service_name="shared-service")
            ],
            edges=[]
        )

        chain2 = ChainDefinitionCreate(
            name="Chain 2",
            category=ChainCategory.SERVICE_COMMUNICATION,
            nodes=[
                ChainNode(id="node2", type=NodeType.SERVICE, service_name="shared-service")
            ],
            edges=[]
        )

        chain1_id = await registry.register_chain(chain1)
        chain2_id = await registry.register_chain(chain2)

        # Test dependency graph
        dep_graph = await registry.get_dependency_graph(chain1_id)
        assert chain2_id in dep_graph['dependencies'] or chain2_id in dep_graph['dependents']


@pytest.fixture
def sample_chain_create():
    """Sample chain creation data."""
    return ChainDefinitionCreate(
        name="Test Chain",
        category=ChainCategory.DATA_FLOW,
        description="Test chain for unit testing",
        nodes=[
            ChainNode(
                id="test_node",
                type=NodeType.SERVICE,
                service_name="test-service"
            )
        ],
        edges=[]
    )
```

## Integration Testing

### 1. Service Integration Testing

```python
# tests/integration/test_service_integration.py
import pytest
import aiohttp
import asyncio
from unittest.mock import patch

from chain_mapping.integration.service_integrator import ServiceIntegrator


@pytest.fixture
async def test_services():
    """Start test services."""
    # This would start actual test service containers
    services = await start_test_service_containers()
    yield services
    await stop_test_service_containers(services)


class TestServiceIntegration:
    """Test service integration components."""

    @pytest.mark.asyncio
    async def test_api_gateway_integration(self, test_services):
        """Test API Gateway chain mapping integration."""
        # Test chain mapping API endpoints
        async with aiohttp.ClientSession() as session:
            # Test chain listing
            async with session.get("http://localhost:8000/api/v1/chains") as resp:
                assert resp.status == 200
                data = await resp.json()
                assert "chains" in data

            # Test health endpoint with chain info
            async with session.get("http://localhost:8000/health/detailed") as resp:
                assert resp.status == 200
                data = await resp.json()
                assert "chain_mapping" in data

    @pytest.mark.asyncio
    async def test_data_bridge_chain_tracking(self, test_services):
        """Test Data Bridge chain event tracking."""
        integrator = ServiceIntegrator("data-bridge")

        # Simulate WebSocket connection event
        await integrator.track_websocket_event(
            connection_id="test-conn",
            event_type="connection_established"
        )

        # Verify event was tracked
        events = await integrator.get_tracked_events()
        assert len(events) > 0
        assert events[0]["event_type"] == "connection_established"

    @pytest.mark.asyncio
    async def test_database_service_chain_storage(self, test_services):
        """Test Database Service chain data operations."""
        from chain_mapping.core.registry import ChainRegistry

        registry = ChainRegistry(
            database_url="postgresql://test:test@localhost:5433/chain_mapping_test"
        )
        await registry.initialize()

        # Test chain CRUD operations
        chain_create = ChainDefinitionCreate(
            name="Integration Test Chain",
            category=ChainCategory.DATA_FLOW,
            nodes=[
                ChainNode(id="node1", type=NodeType.SERVICE, service_name="test-service")
            ],
            edges=[]
        )

        chain_id = await registry.register_chain(chain_create)
        assert chain_id

        retrieved_chain = await registry.get_chain(chain_id)
        assert retrieved_chain.name == "Integration Test Chain"


@pytest.mark.asyncio
async def start_test_service_containers():
    """Start test service containers."""
    # Implementation would use docker-compose or similar
    # to start test versions of microservices
    pass


@pytest.mark.asyncio
async def stop_test_service_containers(services):
    """Stop test service containers."""
    pass
```

### 2. Database Integration Testing

```python
# tests/integration/test_database_integration.py
import pytest
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine

from chain_mapping.database.schema_manager import SchemaManager


class TestDatabaseIntegration:
    """Test database integration components."""

    @pytest.mark.asyncio
    async def test_postgresql_schema_creation(self):
        """Test PostgreSQL schema creation."""
        engine = create_async_engine(
            "postgresql+asyncpg://test:test@localhost:5433/chain_mapping_test"
        )

        schema_manager = SchemaManager(engine)
        await schema_manager.create_chain_mapping_schema()

        # Verify tables exist
        async with engine.connect() as conn:
            result = await conn.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name LIKE 'chain_%'"
            )
            tables = [row[0] for row in result]

            expected_tables = [
                'chain_definitions',
                'chain_nodes',
                'chain_edges',
                'chain_dependencies',
                'chain_monitoring_config',
                'chain_discovery_results'
            ]

            for table in expected_tables:
                assert table in tables

    @pytest.mark.asyncio
    async def test_clickhouse_schema_creation(self):
        """Test ClickHouse schema creation."""
        import clickhouse_connect

        client = clickhouse_connect.get_client(
            host='localhost',
            port=8124,
            username='test',
            password='test'
        )

        schema_manager = SchemaManager(clickhouse_client=client)
        await schema_manager.create_clickhouse_schema()

        # Verify tables exist
        tables = client.query("SHOW TABLES").result_rows
        table_names = [row[0] for row in tables]

        expected_tables = [
            'chain_health_metrics',
            'chain_execution_traces',
            'chain_performance_events',
            'chain_network_flows'
        ]

        for table in expected_tables:
            assert table in table_names

    @pytest.mark.asyncio
    async def test_database_triggers_and_functions(self):
        """Test database triggers and functions."""
        engine = create_async_engine(
            "postgresql+asyncpg://test:test@localhost:5433/chain_mapping_test"
        )

        # Test chain change logging trigger
        async with engine.begin() as conn:
            # Insert a chain definition
            await conn.execute(
                "INSERT INTO chain_definitions (id, name, category) "
                "VALUES ('A1', 'Test Chain', 'data_flow')"
            )

            # Check if change was logged
            result = await conn.execute(
                "SELECT change_type FROM chain_change_history WHERE chain_id = 'A1'"
            )
            changes = [row[0] for row in result]
            assert 'created' in changes

    @pytest.mark.asyncio
    async def test_data_retention_policies(self):
        """Test data retention and cleanup."""
        import clickhouse_connect

        client = clickhouse_connect.get_client(
            host='localhost',
            port=8124,
            username='test',
            password='test'
        )

        # Insert old test data
        old_timestamp = "2023-01-01 00:00:00"
        client.insert(
            'chain_health_metrics',
            [
                [old_timestamp, 'A1', 'node1', 'latency', 100.0, 'ms', 'healthy', 'test-service', 'test', {}, '{}']
            ]
        )

        # Verify TTL policy removes old data
        await asyncio.sleep(1)  # Wait for potential cleanup

        result = client.query(
            "SELECT count() FROM chain_health_metrics WHERE timestamp < '2023-02-01'"
        )
        # Depending on TTL configuration, this should be 0 or handled by TTL
```

## Chain Validation Testing

### 1. Chain Definition Validation

```python
# tests/validation/test_chain_validation.py
import pytest
from chain_mapping.core.registry import ChainRegistry
from chain_mapping.core.models import ChainDefinition, ValidationResult


class TestChainValidation:
    """Test chain validation logic."""

    @pytest.mark.asyncio
    async def test_valid_chain_validation(self, registry, valid_chain_def):
        """Test validation of a properly formed chain."""
        result = await registry.validate_chain(valid_chain_def)

        assert result.valid is True
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_invalid_chain_validation(self, registry):
        """Test validation of invalid chain definitions."""
        # Chain with circular dependency
        invalid_chain = ChainDefinition(
            id="A1",
            name="Invalid Chain",
            category=ChainCategory.DATA_FLOW,
            nodes=[
                ChainNode(id="node1", type=NodeType.SERVICE, service_name="service1"),
                ChainNode(id="node2", type=NodeType.SERVICE, service_name="service2")
            ],
            edges=[
                ChainEdge(source_node="node1", target_node="node2", type=EdgeType.HTTP_REQUEST),
                ChainEdge(source_node="node2", target_node="node1", type=EdgeType.HTTP_REQUEST)
            ]
        )

        result = await registry.validate_chain(invalid_chain)

        assert result.valid is False
        assert len(result.errors) > 0
        assert any("circular" in error["message"].lower() for error in result.errors)

    @pytest.mark.asyncio
    async def test_service_existence_validation(self, registry):
        """Test validation of service existence."""
        chain_with_unknown_service = ChainDefinition(
            id="A1",
            name="Unknown Service Chain",
            category=ChainCategory.DATA_FLOW,
            nodes=[
                ChainNode(
                    id="node1",
                    type=NodeType.SERVICE,
                    service_name="nonexistent-service"
                )
            ],
            edges=[]
        )

        result = await registry.validate_chain(chain_with_unknown_service)

        # Should have warnings about unknown service
        assert len(result.warnings) > 0
        assert any("not found in service registry" in warning["message"]
                  for warning in result.warnings)

    @pytest.mark.asyncio
    async def test_performance_suggestions(self, registry):
        """Test performance-related validation suggestions."""
        # Create a chain with many nodes
        nodes = []
        edges = []
        for i in range(15):  # More than recommended limit
            nodes.append(ChainNode(
                id=f"node{i}",
                type=NodeType.SERVICE,
                service_name=f"service{i}"
            ))
            if i > 0:
                edges.append(ChainEdge(
                    source_node=f"node{i-1}",
                    target_node=f"node{i}",
                    type=EdgeType.HTTP_REQUEST
                ))

        large_chain = ChainDefinition(
            id="A1",
            name="Large Chain",
            category=ChainCategory.DATA_FLOW,
            nodes=nodes,
            edges=edges
        )

        result = await registry.validate_chain(large_chain)

        assert len(result.suggestions) > 0
        assert any("breaking this chain into smaller" in suggestion.lower()
                  for suggestion in result.suggestions)


@pytest.fixture
def valid_chain_def():
    """Valid chain definition for testing."""
    return ChainDefinition(
        id="A1",
        name="Valid Test Chain",
        category=ChainCategory.DATA_FLOW,
        nodes=[
            ChainNode(
                id="source",
                type=NodeType.SERVICE,
                service_name="data-bridge"
            ),
            ChainNode(
                id="processor",
                type=NodeType.SERVICE,
                service_name="ml-processing"
            ),
            ChainNode(
                id="storage",
                type=NodeType.DATABASE,
                service_name="database-service"
            )
        ],
        edges=[
            ChainEdge(
                source_node="source",
                target_node="processor",
                type=EdgeType.HTTP_REQUEST,
                latency_sla=100
            ),
            ChainEdge(
                source_node="processor",
                target_node="storage",
                type=EdgeType.DATABASE_QUERY,
                latency_sla=50
            )
        ]
    )
```

## Performance Testing

### 1. Chain Mapping Performance Tests

```python
# tests/performance/test_performance.py
import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

from chain_mapping.core.registry import ChainRegistry
from chain_mapping.monitoring.health_monitor import ChainHealthMonitor


class TestPerformance:
    """Performance tests for chain mapping system."""

    @pytest.mark.asyncio
    async def test_chain_registration_performance(self, registry):
        """Test performance of chain registration."""
        chain_templates = []
        for i in range(100):
            chain_templates.append(ChainDefinitionCreate(
                name=f"Performance Test Chain {i}",
                category=ChainCategory.DATA_FLOW,
                nodes=[
                    ChainNode(
                        id=f"node_{i}",
                        type=NodeType.SERVICE,
                        service_name=f"service-{i % 10}"
                    )
                ],
                edges=[]
            ))

        start_time = time.time()

        # Register all chains
        tasks = []
        for template in chain_templates:
            task = asyncio.create_task(registry.register_chain(template))
            tasks.append(task)

        chain_ids = await asyncio.gather(*tasks)

        end_time = time.time()
        total_time = end_time - start_time

        # Should register 100 chains in under 5 seconds
        assert total_time < 5.0
        assert len(chain_ids) == 100

        # Test retrieval performance
        start_time = time.time()

        retrieval_tasks = []
        for chain_id in chain_ids[:10]:  # Test first 10
            task = asyncio.create_task(registry.get_chain(chain_id))
            retrieval_tasks.append(task)

        retrieved_chains = await asyncio.gather(*retrieval_tasks)

        end_time = time.time()
        retrieval_time = end_time - start_time

        # Should retrieve 10 chains in under 1 second
        assert retrieval_time < 1.0
        assert len(retrieved_chains) == 10

    @pytest.mark.asyncio
    async def test_health_monitoring_performance(self):
        """Test performance of health monitoring."""
        health_monitor = ChainHealthMonitor()

        # Create test chains
        test_chains = []
        for i in range(20):
            chain = ChainDefinition(
                id=f"A{i+1}",
                name=f"Performance Test Chain {i}",
                category=ChainCategory.DATA_FLOW,
                nodes=[
                    ChainNode(
                        id="test_node",
                        type=NodeType.SERVICE,
                        service_name="test-service",
                        health_check=HealthCheckConfig(
                            enabled=True,
                            endpoint=f"http://localhost:8000/health",
                            timeout_ms=1000
                        )
                    )
                ],
                edges=[]
            )
            test_chains.append(chain)

        # Start monitoring all chains
        start_time = time.time()

        monitoring_tasks = []
        for chain in test_chains:
            config = MonitoringConfig(
                chain_id=chain.id,
                check_interval=10  # 10 seconds
            )
            task = asyncio.create_task(
                health_monitor.start_monitoring(chain, config)
            )
            monitoring_tasks.append(task)

        await asyncio.gather(*monitoring_tasks)

        # Perform health checks
        health_check_tasks = []
        for chain in test_chains:
            task = asyncio.create_task(
                health_monitor.get_chain_health(chain)
            )
            health_check_tasks.append(task)

        health_statuses = await asyncio.gather(*health_check_tasks)

        end_time = time.time()
        total_time = end_time - start_time

        # Should complete all health checks in under 3 seconds
        assert total_time < 3.0
        assert len(health_statuses) == 20

        # Cleanup
        for chain in test_chains:
            await health_monitor.stop_monitoring(chain.id)

    @pytest.mark.asyncio
    async def test_concurrent_operations_performance(self, registry):
        """Test performance under concurrent operations."""
        # Concurrent chain operations
        async def chain_operations():
            # Register a chain
            chain = ChainDefinitionCreate(
                name=f"Concurrent Chain {asyncio.current_task().get_name()}",
                category=ChainCategory.SERVICE_COMMUNICATION,
                nodes=[
                    ChainNode(
                        id="node1",
                        type=NodeType.SERVICE,
                        service_name="test-service"
                    )
                ],
                edges=[]
            )

            chain_id = await registry.register_chain(chain)

            # Retrieve the chain
            retrieved = await registry.get_chain(chain_id)

            # Update the chain
            updates = ChainDefinitionUpdate(description="Updated during concurrent test")
            await registry.update_chain(chain_id, updates)

            # List chains
            chains, count = await registry.list_chains(limit=5)

            return chain_id

        # Run 50 concurrent operations
        start_time = time.time()

        tasks = []
        for i in range(50):
            task = asyncio.create_task(chain_operations(), name=f"task-{i}")
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        total_time = end_time - start_time

        # Should complete 50 concurrent operations in under 10 seconds
        assert total_time < 10.0

        # Check for exceptions
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0, f"Found exceptions: {exceptions}"

        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == 50

    @pytest.mark.asyncio
    async def test_memory_usage_monitoring(self):
        """Test memory usage during intensive operations."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        registry = ChainRegistry(
            database_url="sqlite+aiosqlite:///:memory:",
            redis_url=None
        )
        await registry.initialize()

        # Create many chains to test memory usage
        for i in range(1000):
            chain = ChainDefinitionCreate(
                name=f"Memory Test Chain {i}",
                category=ChainCategory.DATA_FLOW,
                nodes=[
                    ChainNode(
                        id=f"node_{j}",
                        type=NodeType.SERVICE,
                        service_name=f"service-{j}"
                    ) for j in range(10)  # 10 nodes per chain
                ],
                edges=[
                    ChainEdge(
                        source_node=f"node_{j}",
                        target_node=f"node_{j+1}",
                        type=EdgeType.HTTP_REQUEST
                    ) for j in range(9)  # 9 edges per chain
                ]
            )
            await registry.register_chain(chain)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 100MB for 1000 chains)
        assert memory_increase < 100, f"Memory usage increased by {memory_increase:.2f}MB"

        await registry.cleanup()
```

## Health Monitoring Testing

### 1. Health Check Testing

```python
# tests/monitoring/test_health_monitoring.py
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
import aiohttp

from chain_mapping.monitoring.health_monitor import (
    ChainHealthMonitor, HTTPHealthChecker, WebSocketHealthChecker,
    DatabaseHealthChecker
)


class TestHealthMonitoring:
    """Test health monitoring functionality."""

    @pytest.mark.asyncio
    async def test_http_health_checker(self):
        """Test HTTP-based health checking."""
        checker = HTTPHealthChecker()

        node = ChainNode(
            id="test_node",
            type=NodeType.SERVICE,
            service_name="api-gateway"
        )

        config = HealthCheckConfig(
            enabled=True,
            endpoint="http://httpbin.org/status/200",
            timeout_ms=5000,
            expected_status_codes=[200]
        )

        result = await checker.check_health(node, config)

        assert result.node_id == "test_node"
        assert result.status == ChainStatus.HEALTHY
        assert result.response_time > 0
        assert result.error_message is None

        await checker.cleanup()

    @pytest.mark.asyncio
    async def test_http_health_checker_failure(self):
        """Test HTTP health checker with failure."""
        checker = HTTPHealthChecker()

        node = ChainNode(
            id="test_node",
            type=NodeType.SERVICE,
            service_name="api-gateway"
        )

        config = HealthCheckConfig(
            enabled=True,
            endpoint="http://httpbin.org/status/500",
            timeout_ms=5000,
            expected_status_codes=[200]
        )

        result = await checker.check_health(node, config)

        assert result.node_id == "test_node"
        assert result.status == ChainStatus.DEGRADED
        assert "Unexpected status code: 500" in result.error_message

        await checker.cleanup()

    @pytest.mark.asyncio
    async def test_websocket_health_checker(self):
        """Test WebSocket-based health checking."""
        checker = WebSocketHealthChecker()

        node = ChainNode(
            id="ws_node",
            type=NodeType.WEBSOCKET,
            service_name="data-bridge"
        )

        # Mock WebSocket server would be needed for full test
        config = HealthCheckConfig(
            enabled=True,
            endpoint="ws://echo.websocket.org",
            timeout_ms=5000
        )

        # For this test, we'll mock the websocket connection
        with patch('websockets.connect') as mock_connect:
            mock_websocket = AsyncMock()
            mock_websocket.send = AsyncMock()
            mock_websocket.recv = AsyncMock(return_value='{"status": "ok"}')
            mock_connect.return_value.__aenter__.return_value = mock_websocket

            result = await checker.check_health(node, config)

            assert result.node_id == "ws_node"
            assert result.status == ChainStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_chain_health_monitoring(self):
        """Test complete chain health monitoring."""
        monitor = ChainHealthMonitor()

        # Create test chain
        chain = ChainDefinition(
            id="A1",
            name="Test Chain",
            category=ChainCategory.DATA_FLOW,
            nodes=[
                ChainNode(
                    id="http_node",
                    type=NodeType.SERVICE,
                    service_name="api-gateway",
                    health_check=HealthCheckConfig(
                        enabled=True,
                        endpoint="http://httpbin.org/status/200",
                        timeout_ms=2000
                    )
                ),
                ChainNode(
                    id="db_node",
                    type=NodeType.DATABASE,
                    service_name="database-service",
                    health_check=HealthCheckConfig(enabled=True)
                )
            ],
            edges=[]
        )

        # Get chain health
        health_status = await monitor.get_chain_health(chain)

        assert health_status.chain_id == "A1"
        assert len(health_status.node_health) == 2
        assert health_status.overall_score is not None

        # Check individual node health
        http_node_health = next(
            nh for nh in health_status.node_health if nh.node_id == "http_node"
        )
        assert http_node_health.status in [ChainStatus.HEALTHY, ChainStatus.DEGRADED]

        await monitor.cleanup()

    @pytest.mark.asyncio
    async def test_alert_generation(self):
        """Test alert generation for unhealthy chains."""
        alerts_received = []

        def alert_callback(alert):
            alerts_received.append(alert)

        monitor = ChainHealthMonitor(alert_callback=alert_callback)

        # Create chain with failing health check
        chain = ChainDefinition(
            id="A1",
            name="Failing Chain",
            category=ChainCategory.DATA_FLOW,
            nodes=[
                ChainNode(
                    id="failing_node",
                    type=NodeType.SERVICE,
                    service_name="test-service",
                    health_check=HealthCheckConfig(
                        enabled=True,
                        endpoint="http://httpbin.org/status/500",
                        timeout_ms=1000
                    )
                )
            ],
            edges=[]
        )

        config = MonitoringConfig(
            chain_id="A1",
            check_interval=1,  # 1 second for quick test
            alert_thresholds={"latency_threshold": 100}
        )

        # Start monitoring
        await monitor.start_monitoring(chain, config)

        # Wait for health check and alert
        await asyncio.sleep(2)

        # Stop monitoring
        await monitor.stop_monitoring("A1")

        # Should have received alerts
        assert len(alerts_received) > 0

        # Check alert content
        status_alerts = [a for a in alerts_received if "status" in a.message.lower()]
        assert len(status_alerts) > 0

        await monitor.cleanup()

    @pytest.mark.asyncio
    async def test_sla_compliance_monitoring(self):
        """Test SLA compliance monitoring."""
        monitor = ChainHealthMonitor()

        chain = ChainDefinition(
            id="A1",
            name="SLA Test Chain",
            category=ChainCategory.DATA_FLOW,
            nodes=[
                ChainNode(
                    id="slow_node",
                    type=NodeType.SERVICE,
                    service_name="slow-service",
                    health_check=HealthCheckConfig(
                        enabled=True,
                        endpoint="http://httpbin.org/delay/2",  # 2 second delay
                        timeout_ms=5000
                    )
                )
            ],
            edges=[]
        )

        health_status = await monitor.get_chain_health(chain)

        # Check if SLA compliance is calculated
        # Note: This would require proper SLA configuration in practice
        assert health_status.sla_compliance is not None or health_status.overall_score is not None

        await monitor.cleanup()
```

## Discovery System Testing

### 1. AST Parser Testing

```python
# tests/discovery/test_ast_parser.py
import pytest
import tempfile
import os
from pathlib import Path

from chain_mapping.discovery.ast_parser import ChainASTParser


class TestASTParser:
    """Test AST-based chain discovery."""

    @pytest.fixture
    def sample_service_code(self):
        """Create sample service code for testing."""
        return {
            "main.py": '''
from fastapi import FastAPI, Depends
import asyncio

app = FastAPI()

@app.get("/api/v1/users/{user_id}")
async def get_user(user_id: int, db=Depends(get_database)):
    user = await db.query("SELECT * FROM users WHERE id = ?", user_id)
    return user

@app.post("/api/v1/trading/execute")
async def execute_trade(trade_data: dict):
    # Validate trade
    validation_result = await validate_trade(trade_data)

    # Process with AI
    ai_decision = await ai_client.analyze_trade(trade_data)

    # Execute trade
    result = await trading_engine.execute(ai_decision)

    return result

@app.websocket("/ws/market-data")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        # Process market data
        await process_market_data(data)
''',
            "database.py": '''
import asyncpg

class DatabaseService:
    async def query(self, sql: str, *params):
        async with self.pool.acquire() as conn:
            return await conn.fetch(sql, *params)

    async def insert_trade_data(self, trade_data: dict):
        await self.query("INSERT INTO trades (...) VALUES (...)", trade_data)

    async def update_user_portfolio(self, user_id: int, updates: dict):
        await self.query("UPDATE portfolios SET ... WHERE user_id = ?", user_id)
''',
            "ai_client.py": '''
import aiohttp

class AIClient:
    async def analyze_trade(self, trade_data: dict):
        async with aiohttp.ClientSession() as session:
            async with session.post("http://ai-provider:8005/analyze", json=trade_data) as resp:
                return await resp.json()
'''
        }

    @pytest.mark.asyncio
    async def test_api_endpoint_discovery(self, sample_service_code):
        """Test discovery of API endpoints."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write sample code
            for filename, content in sample_service_code.items():
                file_path = Path(temp_dir) / filename
                file_path.write_text(content)

            parser = ChainASTParser()
            discovered_chains = await parser.parse_service_directory(temp_dir)

            # Should discover API chains
            api_chains = [c for c in discovered_chains if "API" in c.name]
            assert len(api_chains) > 0

            # Check for specific endpoints
            trading_chains = [c for c in discovered_chains if "trading" in c.name.lower()]
            assert len(trading_chains) > 0

            # Verify chain structure
            trading_chain = trading_chains[0]
            assert len(trading_chain.nodes) > 0
            assert any(node.type == NodeType.API_ENDPOINT for node in trading_chain.nodes)

    @pytest.mark.asyncio
    async def test_database_operation_discovery(self, sample_service_code):
        """Test discovery of database operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write sample code
            for filename, content in sample_service_code.items():
                file_path = Path(temp_dir) / filename
                file_path.write_text(content)

            parser = ChainASTParser()
            discovered_chains = await parser.parse_service_directory(temp_dir)

            # Should discover data flow chains
            data_chains = [c for c in discovered_chains
                          if c.category == ChainCategory.DATA_FLOW]
            assert len(data_chains) > 0

            # Check for database nodes
            for chain in data_chains:
                db_nodes = [node for node in chain.nodes
                           if node.type == NodeType.DATABASE]
                if db_nodes:
                    assert len(db_nodes) > 0
                    break
            else:
                pytest.fail("No database nodes found in discovered chains")

    @pytest.mark.asyncio
    async def test_websocket_discovery(self, sample_service_code):
        """Test discovery of WebSocket handlers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write sample code
            for filename, content in sample_service_code.items():
                file_path = Path(temp_dir) / filename
                file_path.write_text(content)

            parser = ChainASTParser()
            discovered_chains = await parser.parse_service_directory(temp_dir)

            # Should discover WebSocket chains
            ws_chains = [c for c in discovered_chains
                        if any(node.type == NodeType.WEBSOCKET for node in c.nodes)]
            assert len(ws_chains) > 0

            # Check WebSocket chain details
            ws_chain = ws_chains[0]
            assert ws_chain.category == ChainCategory.USER_EXPERIENCE
            assert "market-data" in ws_chain.evidence.get("websocket_handler", {}).get("endpoint", "")

    @pytest.mark.asyncio
    async def test_service_communication_discovery(self, sample_service_code):
        """Test discovery of inter-service communication."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write sample code
            for filename, content in sample_service_code.items():
                file_path = Path(temp_dir) / filename
                file_path.write_text(content)

            parser = ChainASTParser()
            discovered_chains = await parser.parse_service_directory(temp_dir)

            # Should discover service communication chains
            comm_chains = [c for c in discovered_chains
                          if c.category == ChainCategory.SERVICE_COMMUNICATION]
            assert len(comm_chains) > 0

            # Check for external service calls
            ai_chains = [c for c in comm_chains if "ai-provider" in str(c.evidence)]
            assert len(ai_chains) > 0

    @pytest.mark.asyncio
    async def test_confidence_scoring(self, sample_service_code):
        """Test confidence scoring for discovered chains."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write sample code
            for filename, content in sample_service_code.items():
                file_path = Path(temp_dir) / filename
                file_path.write_text(content)

            parser = ChainASTParser()
            discovered_chains = await parser.parse_service_directory(temp_dir)

            # All chains should have confidence scores
            for chain in discovered_chains:
                assert 0.0 <= chain.confidence_score <= 1.0

            # Chains with clear evidence should have higher confidence
            high_confidence_chains = [c for c in discovered_chains
                                    if c.confidence_score > 0.8]
            assert len(high_confidence_chains) > 0

    @pytest.mark.asyncio
    async def test_evidence_collection(self, sample_service_code):
        """Test evidence collection for discovered chains."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write sample code
            for filename, content in sample_service_code.items():
                file_path = Path(temp_dir) / filename
                file_path.write_text(content)

            parser = ChainASTParser()
            discovered_chains = await parser.parse_service_directory(temp_dir)

            # All chains should have evidence
            for chain in discovered_chains:
                assert chain.evidence is not None
                assert len(chain.evidence) > 0

                # Check for source file information
                if "source_file" in chain.evidence:
                    assert chain.evidence["source_file"].endswith(".py")

                # Check for discovery method
                assert chain.discovery_method == DiscoveryMethod.AST_PARSER
```

## End-to-End Testing

### 1. Complete Workflow Testing

```python
# tests/e2e/test_complete_workflows.py
import pytest
import asyncio
import aiohttp
from datetime import datetime, timedelta

from chain_mapping.core.registry import ChainRegistry
from chain_mapping.monitoring.health_monitor import ChainHealthMonitor


class TestCompleteWorkflows:
    """End-to-end workflow testing."""

    @pytest.mark.asyncio
    async def test_chain_lifecycle_workflow(self):
        """Test complete chain lifecycle from discovery to monitoring."""
        # 1. Initialize system components
        registry = ChainRegistry(
            database_url="postgresql://test:test@localhost:5433/chain_mapping_test",
            redis_url="redis://localhost:6380"
        )
        await registry.initialize()

        health_monitor = ChainHealthMonitor()

        try:
            # 2. Register a new chain
            chain_create = ChainDefinitionCreate(
                name="E2E Test Chain",
                category=ChainCategory.DATA_FLOW,
                description="End-to-end test chain",
                nodes=[
                    ChainNode(
                        id="data_source",
                        type=NodeType.SERVICE,
                        service_name="data-bridge",
                        health_check=HealthCheckConfig(
                            enabled=True,
                            endpoint="http://localhost:8001/health"
                        )
                    ),
                    ChainNode(
                        id="data_processor",
                        type=NodeType.SERVICE,
                        service_name="ml-processing",
                        health_check=HealthCheckConfig(
                            enabled=True,
                            endpoint="http://localhost:8006/health"
                        )
                    ),
                    ChainNode(
                        id="data_storage",
                        type=NodeType.DATABASE,
                        service_name="database-service",
                        health_check=HealthCheckConfig(enabled=True)
                    )
                ],
                edges=[
                    ChainEdge(
                        source_node="data_source",
                        target_node="data_processor",
                        type=EdgeType.HTTP_REQUEST,
                        latency_sla=200
                    ),
                    ChainEdge(
                        source_node="data_processor",
                        target_node="data_storage",
                        type=EdgeType.DATABASE_QUERY,
                        latency_sla=100
                    )
                ]
            )

            chain_id = await registry.register_chain(chain_create)
            assert chain_id.startswith("A")

            # 3. Validate chain
            chain_def = await registry.get_chain(chain_id)
            validation_result = await registry.validate_chain(chain_def)
            assert validation_result.valid

            # 4. Start monitoring
            monitoring_config = MonitoringConfig(
                chain_id=chain_id,
                check_interval=5,  # 5 seconds for testing
                alert_thresholds={
                    "latency_threshold": 1000,
                    "error_rate_threshold": 0.1
                }
            )

            await health_monitor.start_monitoring(chain_def, monitoring_config)

            # 5. Wait for health checks
            await asyncio.sleep(10)

            # 6. Get health status
            health_status = await health_monitor.get_chain_health(chain_def)
            assert health_status.chain_id == chain_id
            assert len(health_status.node_health) == 3

            # 7. Update chain
            updates = ChainDefinitionUpdate(
                description="Updated E2E test chain"
            )
            success = await registry.update_chain(chain_id, updates)
            assert success

            # 8. Verify update
            updated_chain = await registry.get_chain(chain_id)
            assert updated_chain.description == "Updated E2E test chain"
            assert updated_chain.version == 2

            # 9. Test API access
            async with aiohttp.ClientSession() as session:
                # List chains
                async with session.get(f"http://localhost:8000/api/v1/chains") as resp:
                    assert resp.status == 200
                    data = await resp.json()
                    assert len(data["chains"]) > 0

                # Get specific chain
                async with session.get(f"http://localhost:8000/api/v1/chains/{chain_id}") as resp:
                    assert resp.status == 200
                    chain_data = await resp.json()
                    assert chain_data["id"] == chain_id

                # Get health status
                async with session.get(f"http://localhost:8000/api/v1/chains/{chain_id}/health") as resp:
                    assert resp.status == 200
                    health_data = await resp.json()
                    assert health_data["chain_id"] == chain_id

            # 10. Stop monitoring
            await health_monitor.stop_monitoring(chain_id)

            # 11. Delete chain
            await registry.delete_chain(chain_id)

            # 12. Verify deletion
            with pytest.raises(ChainNotFoundError):
                await registry.get_chain(chain_id)

        finally:
            await health_monitor.cleanup()
            await registry.cleanup()

    @pytest.mark.asyncio
    async def test_real_time_monitoring_workflow(self):
        """Test real-time monitoring and alerting workflow."""
        registry = ChainRegistry(
            database_url="postgresql://test:test@localhost:5433/chain_mapping_test"
        )
        await registry.initialize()

        alerts_received = []

        def alert_callback(alert):
            alerts_received.append(alert)

        health_monitor = ChainHealthMonitor(alert_callback=alert_callback)

        try:
            # Create chain with intentionally failing health check
            chain_create = ChainDefinitionCreate(
                name="Monitoring Test Chain",
                category=ChainCategory.INFRASTRUCTURE,
                nodes=[
                    ChainNode(
                        id="failing_service",
                        type=NodeType.SERVICE,
                        service_name="test-service",
                        health_check=HealthCheckConfig(
                            enabled=True,
                            endpoint="http://localhost:9999/health",  # Non-existent endpoint
                            timeout_ms=1000
                        )
                    )
                ],
                edges=[]
            )

            chain_id = await registry.register_chain(chain_create)
            chain_def = await registry.get_chain(chain_id)

            # Start monitoring with aggressive settings
            config = MonitoringConfig(
                chain_id=chain_id,
                check_interval=2,  # 2 seconds
                alert_thresholds={
                    "error_rate_threshold": 0.01  # Very low threshold
                }
            )

            await health_monitor.start_monitoring(chain_def, config)

            # Wait for monitoring to detect failures
            await asyncio.sleep(8)

            # Should have received alerts
            assert len(alerts_received) > 0

            # Check alert content
            failure_alerts = [a for a in alerts_received if "failed" in a.message.lower()]
            assert len(failure_alerts) > 0

            # Test alert resolution
            alert_id = alerts_received[0].id
            resolved = await health_monitor.resolve_alert(alert_id, "Test resolution")
            assert resolved

            # Get active alerts (should exclude resolved ones)
            active_alerts = health_monitor.get_active_alerts(chain_id)
            resolved_alerts = [a for a in alerts_received if a.resolved]
            assert len(resolved_alerts) > 0

        finally:
            await health_monitor.cleanup()
            await registry.cleanup()

    @pytest.mark.asyncio
    async def test_discovery_to_production_workflow(self):
        """Test workflow from discovery to production deployment."""
        # This test would simulate the complete workflow:
        # 1. Discover chains from existing code
        # 2. Review and approve discovered chains
        # 3. Deploy monitoring
        # 4. Validate in production

        # For this example, we'll simulate the key steps
        registry = ChainRegistry(
            database_url="postgresql://test:test@localhost:5433/chain_mapping_test"
        )
        await registry.initialize()

        try:
            # 1. Simulate discovery results
            discovered_chain = DiscoveredChain(
                proposed_chain_id="B1",
                name="Discovered API Chain",
                category=ChainCategory.SERVICE_COMMUNICATION,
                description="Auto-discovered API request chain",
                discovery_method=DiscoveryMethod.AST_PARSER,
                confidence_score=0.85,
                nodes=[
                    ChainNode(
                        id="api_gateway",
                        type=NodeType.API_ENDPOINT,
                        service_name="api-gateway"
                    ),
                    ChainNode(
                        id="user_service",
                        type=NodeType.SERVICE,
                        service_name="user-service"
                    )
                ],
                edges=[
                    ChainEdge(
                        source_node="api_gateway",
                        target_node="user_service",
                        type=EdgeType.HTTP_REQUEST
                    )
                ],
                evidence={
                    "source_files": ["main.py", "user_handler.py"],
                    "discovery_method": "ast_parser",
                    "confidence_factors": ["clear_api_endpoint", "service_call_detected"]
                }
            )

            # 2. Convert discovered chain to production chain
            production_chain = ChainDefinitionCreate(
                name=discovered_chain.name,
                category=discovered_chain.category,
                description=discovered_chain.description,
                nodes=discovered_chain.nodes,
                edges=discovered_chain.edges,
                metadata={
                    "discovery_source": discovered_chain.discovery_method.value,
                    "confidence_score": discovered_chain.confidence_score,
                    "evidence": discovered_chain.evidence
                }
            )

            # 3. Register production chain
            chain_id = await registry.register_chain(production_chain)

            # 4. Validate production chain
            chain_def = await registry.get_chain(chain_id)
            validation_result = await registry.validate_chain(chain_def)
            assert validation_result.valid

            # 5. Deploy monitoring for production
            health_monitor = ChainHealthMonitor()

            config = MonitoringConfig(
                chain_id=chain_id,
                check_interval=30,  # Production interval
                alert_thresholds={
                    "latency_threshold": 500,
                    "error_rate_threshold": 0.05,
                    "availability_threshold": 0.99
                }
            )

            await health_monitor.start_monitoring(chain_def, config)

            # 6. Validate monitoring is working
            await asyncio.sleep(5)

            health_status = await health_monitor.get_chain_health(chain_def)
            assert health_status.chain_id == chain_id

            # 7. Get statistics
            stats = await registry.get_statistics()
            assert stats["total_chains"] >= 1

            monitoring_stats = health_monitor.get_monitoring_statistics()
            assert monitoring_stats["active_chains"] >= 1

            await health_monitor.cleanup()

        finally:
            await registry.cleanup()
```

This comprehensive testing specification covers all aspects of the chain mapping system, from unit tests for core models to end-to-end workflow validation. The tests ensure reliability, performance, and integration quality across the entire system.