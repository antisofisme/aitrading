"""
Embedded Chain Mapping System - Core Data Models
================================================================

This module defines the core data models for the embedded chain mapping system
that tracks 30 distinct chains across 5 categories in the AI trading platform.

The models follow Pydantic v2 patterns and are designed for:
- Type safety and validation
- JSON serialization/deserialization
- Integration with existing microservices
- Performance optimization
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict, field_validator, computed_field
from pydantic.types import PositiveInt, NonNegativeFloat


# ================================================================
# Enumerations
# ================================================================

class ChainCategory(str, Enum):
    """Chain categories for classification and organization."""
    DATA_FLOW = "data_flow"
    SERVICE_COMMUNICATION = "service_communication"
    USER_EXPERIENCE = "user_experience"
    AI_ML_PROCESSING = "ai_ml_processing"
    INFRASTRUCTURE = "infrastructure"


class NodeType(str, Enum):
    """Types of nodes within a chain."""
    SERVICE = "service"
    API_ENDPOINT = "api_endpoint"
    DATABASE = "database"
    CACHE = "cache"
    QUEUE = "queue"
    AI_MODEL = "ai_model"
    WEBSOCKET = "websocket"
    EXTERNAL_API = "external_api"


class EdgeType(str, Enum):
    """Types of connections between nodes."""
    HTTP_REQUEST = "http_request"
    WEBSOCKET_MESSAGE = "websocket_message"
    DATABASE_QUERY = "database_query"
    CACHE_OPERATION = "cache_operation"
    EVENT_PUBLISH = "event_publish"
    AI_INFERENCE = "ai_inference"


class DependencyType(str, Enum):
    """Types of external dependencies."""
    SERVICE = "service"
    DATABASE = "database"
    EXTERNAL_API = "external_api"
    CACHE = "cache"
    QUEUE = "queue"
    CONFIGURATION = "configuration"


class CriticalityLevel(str, Enum):
    """Criticality levels for dependencies and components."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ChainStatus(str, Enum):
    """Current operational status of a chain."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    UNKNOWN = "unknown"


class BackoffStrategy(str, Enum):
    """Retry backoff strategies."""
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"


class DiscoveryMethod(str, Enum):
    """Methods for discovering chains."""
    AST_PARSER = "ast_parser"
    RUNTIME_TRACE = "runtime_trace"
    SERVICE_MESH = "service_mesh"
    MANUAL = "manual"


# ================================================================
# Base Models
# ================================================================

class BaseChainModel(BaseModel):
    """Base model with common configuration."""
    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        validate_assignment=True,
        str_strip_whitespace=True
    )


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ================================================================
# Node and Edge Configuration Models
# ================================================================

class NodePosition(BaseChainModel):
    """Position information for graph visualization."""
    x: float = Field(description="X coordinate")
    y: float = Field(description="Y coordinate")
    z: Optional[float] = Field(None, description="Z coordinate for 3D visualization")


class HealthCheckConfig(BaseChainModel):
    """Health check configuration for a node."""
    enabled: bool = Field(True, description="Whether health checks are enabled")
    endpoint: Optional[str] = Field(None, description="Health check endpoint URL")
    timeout_ms: PositiveInt = Field(5000, description="Timeout in milliseconds")
    interval_seconds: PositiveInt = Field(60, description="Check interval in seconds")
    retries: int = Field(3, ge=0, le=10, description="Number of retries")
    expected_status_codes: List[int] = Field([200, 204], description="Expected HTTP status codes")

    @field_validator('endpoint')
    @classmethod
    def validate_endpoint(cls, v: Optional[str]) -> Optional[str]:
        if v and not (v.startswith('http://') or v.startswith('https://') or v.startswith('/')):
            raise ValueError('Endpoint must be a valid URL or path')
        return v


class RetryPolicy(BaseChainModel):
    """Retry policy configuration for edges."""
    max_retries: int = Field(3, ge=0, le=10, description="Maximum number of retries")
    backoff_strategy: BackoffStrategy = Field(BackoffStrategy.EXPONENTIAL, description="Backoff strategy")
    initial_delay_ms: PositiveInt = Field(1000, description="Initial delay in milliseconds")
    max_delay_ms: PositiveInt = Field(30000, description="Maximum delay in milliseconds")
    multiplier: float = Field(2.0, gt=1.0, description="Backoff multiplier for exponential strategy")
    jitter: bool = Field(True, description="Whether to add random jitter")


# ================================================================
# Core Chain Components
# ================================================================

class ChainNode(BaseChainModel):
    """A node within a chain representing a service, endpoint, or component."""
    id: str = Field(description="Unique node identifier within the chain")
    type: NodeType = Field(description="Type of the node")
    service_name: Optional[str] = Field(None, description="Name of the microservice")
    component_name: Optional[str] = Field(None, description="Specific component or function name")
    config: Dict[str, Any] = Field(default_factory=dict, description="Node-specific configuration")
    position: Optional[NodePosition] = Field(None, description="Position for visualization")
    health_check: Optional[HealthCheckConfig] = Field(None, description="Health check configuration")
    tags: Dict[str, str] = Field(default_factory=dict, description="Additional metadata tags")

    @field_validator('id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Node ID cannot be empty')
        if len(v) > 100:
            raise ValueError('Node ID cannot exceed 100 characters')
        return v.strip()

    @computed_field
    @property
    def display_name(self) -> str:
        """Generate a display name for the node."""
        if self.component_name:
            return f"{self.service_name}.{self.component_name}" if self.service_name else self.component_name
        return self.service_name or self.id


class ChainEdge(BaseChainModel):
    """An edge connecting two nodes in a chain."""
    id: Optional[str] = Field(None, description="Edge identifier (auto-generated if not provided)")
    source_node: str = Field(description="Source node ID")
    target_node: str = Field(description="Target node ID")
    type: EdgeType = Field(description="Type of connection")
    condition: Optional[str] = Field(None, description="Execution condition (optional)")
    latency_sla: Optional[PositiveInt] = Field(None, description="Expected latency in milliseconds")
    retry_policy: Optional[RetryPolicy] = Field(None, description="Retry policy for failures")
    weight: float = Field(1.0, ge=0.0, description="Edge weight for routing algorithms")
    tags: Dict[str, str] = Field(default_factory=dict, description="Additional metadata tags")

    def __init__(self, **data):
        super().__init__(**data)
        if not self.id:
            self.id = f"{self.source_node}_to_{self.target_node}"

    @field_validator('source_node', 'target_node')
    @classmethod
    def validate_node_ids(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Node ID cannot be empty')
        return v.strip()

    @field_validator('condition')
    @classmethod
    def validate_condition(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) > 500:
            raise ValueError('Condition expression cannot exceed 500 characters')
        return v


class ChainDependency(BaseChainModel):
    """An external dependency required by a chain."""
    id: Optional[str] = Field(None, description="Dependency identifier (auto-generated if not provided)")
    type: DependencyType = Field(description="Type of dependency")
    target: str = Field(description="Target identifier (service name, URL, etc.)")
    criticality: CriticalityLevel = Field(CriticalityLevel.MEDIUM, description="Criticality level")
    fallback: Optional[str] = Field(None, description="Fallback strategy description")
    timeout_ms: Optional[PositiveInt] = Field(None, description="Timeout for dependency calls")
    tags: Dict[str, str] = Field(default_factory=dict, description="Additional metadata tags")

    def __init__(self, **data):
        super().__init__(**data)
        if not self.id:
            self.id = f"{self.type.value}_{self.target.replace('/', '_').replace(':', '_')}"

    @field_validator('target')
    @classmethod
    def validate_target(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Target cannot be empty')
        if len(v) > 200:
            raise ValueError('Target cannot exceed 200 characters')
        return v.strip()


# ================================================================
# Metrics and Health Models
# ================================================================

class ChainMetrics(BaseChainModel):
    """Performance metrics for a chain."""
    avg_latency: Optional[NonNegativeFloat] = Field(None, description="Average latency in milliseconds")
    p95_latency: Optional[NonNegativeFloat] = Field(None, description="95th percentile latency")
    p99_latency: Optional[NonNegativeFloat] = Field(None, description="99th percentile latency")
    error_rate: Optional[float] = Field(None, ge=0.0, le=1.0, description="Error rate (0.0 to 1.0)")
    throughput: Optional[NonNegativeFloat] = Field(None, description="Requests per second")
    availability: Optional[float] = Field(None, ge=0.0, le=1.0, description="Availability (0.0 to 1.0)")
    last_updated: Optional[datetime] = Field(None, description="Last metric update timestamp")

    @computed_field
    @property
    def health_score(self) -> Optional[float]:
        """Calculate an overall health score (0-100)."""
        if not all([self.availability, self.error_rate, self.avg_latency]):
            return None

        # Weight factors: availability (40%), error rate (30%), latency (30%)
        availability_score = self.availability * 40
        error_score = (1 - self.error_rate) * 30
        latency_score = max(0, (1 - min(self.avg_latency / 1000, 1)) * 30)

        return round(availability_score + error_score + latency_score, 2)


class NodeHealth(BaseChainModel):
    """Health information for a specific node."""
    node_id: str = Field(description="Node identifier")
    status: ChainStatus = Field(description="Current health status")
    latency: Optional[NonNegativeFloat] = Field(None, description="Current latency in milliseconds")
    error_rate: Optional[float] = Field(None, ge=0.0, le=1.0, description="Current error rate")
    last_check: Optional[datetime] = Field(None, description="Last health check timestamp")
    error_message: Optional[str] = Field(None, description="Error message if unhealthy")
    response_time: Optional[NonNegativeFloat] = Field(None, description="Health check response time")


class SLACompliance(BaseChainModel):
    """SLA compliance information for a chain."""
    meets_sla: bool = Field(description="Whether the chain meets its SLA")
    latency_sla: Optional[float] = Field(None, description="Latency SLA threshold")
    actual_latency: Optional[float] = Field(None, description="Actual latency measurement")
    uptime_sla: Optional[float] = Field(None, ge=0.0, le=1.0, description="Uptime SLA threshold")
    actual_uptime: Optional[float] = Field(None, ge=0.0, le=1.0, description="Actual uptime measurement")
    error_rate_sla: Optional[float] = Field(None, ge=0.0, le=1.0, description="Error rate SLA threshold")
    actual_error_rate: Optional[float] = Field(None, ge=0.0, le=1.0, description="Actual error rate")


# ================================================================
# Main Chain Definition Model
# ================================================================

class ChainDefinition(BaseChainModel, TimestampMixin):
    """Complete definition of a chain with all its components."""
    id: str = Field(description="Chain identifier (e.g., A1, B2, C3)")
    name: str = Field(description="Human-readable chain name")
    category: ChainCategory = Field(description="Chain category")
    description: Optional[str] = Field(None, description="Detailed description of the chain")
    nodes: List[ChainNode] = Field(description="List of nodes in the chain")
    edges: List[ChainEdge] = Field(description="List of edges connecting nodes")
    dependencies: List[ChainDependency] = Field(default_factory=list, description="External dependencies")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    status: ChainStatus = Field(ChainStatus.UNKNOWN, description="Current operational status")
    metrics: Optional[ChainMetrics] = Field(None, description="Current performance metrics")
    version: PositiveInt = Field(1, description="Version number for change tracking")
    created_by: Optional[str] = Field(None, description="Creator identifier")

    @field_validator('id')
    @classmethod
    def validate_chain_id(cls, v: str) -> str:
        import re
        if not re.match(r'^[A-E][1-9][0-9]*$', v):
            raise ValueError('Chain ID must follow pattern [A-E][1-9]+')
        return v

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Chain name cannot be empty')
        if len(v) > 255:
            raise ValueError('Chain name cannot exceed 255 characters')
        return v.strip()

    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) > 1000:
            raise ValueError('Description cannot exceed 1000 characters')
        return v

    @field_validator('nodes')
    @classmethod
    def validate_nodes(cls, v: List[ChainNode]) -> List[ChainNode]:
        if not v:
            raise ValueError('Chain must have at least one node')

        # Check for duplicate node IDs
        node_ids = [node.id for node in v]
        if len(node_ids) != len(set(node_ids)):
            raise ValueError('Node IDs must be unique within a chain')

        return v

    @field_validator('edges')
    @classmethod
    def validate_edges(cls, v: List[ChainEdge], info) -> List[ChainEdge]:
        if 'nodes' not in info.data:
            return v

        node_ids = {node.id for node in info.data['nodes']}

        for edge in v:
            if edge.source_node not in node_ids:
                raise ValueError(f'Source node {edge.source_node} not found in nodes')
            if edge.target_node not in node_ids:
                raise ValueError(f'Target node {edge.target_node} not found in nodes')
            if edge.source_node == edge.target_node:
                raise ValueError('Source and target nodes cannot be the same')

        return v

    @computed_field
    @property
    def node_count(self) -> int:
        """Number of nodes in the chain."""
        return len(self.nodes)

    @computed_field
    @property
    def edge_count(self) -> int:
        """Number of edges in the chain."""
        return len(self.edges)

    @computed_field
    @property
    def dependency_count(self) -> int:
        """Number of external dependencies."""
        return len(self.dependencies)

    @computed_field
    @property
    def involved_services(self) -> List[str]:
        """List of unique services involved in this chain."""
        services = {node.service_name for node in self.nodes if node.service_name}
        return sorted(list(services))

    def get_node_by_id(self, node_id: str) -> Optional[ChainNode]:
        """Get a node by its ID."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def get_edges_for_node(self, node_id: str, direction: str = 'both') -> List[ChainEdge]:
        """Get edges connected to a specific node."""
        edges = []
        for edge in self.edges:
            if direction in ['outgoing', 'both'] and edge.source_node == node_id:
                edges.append(edge)
            elif direction in ['incoming', 'both'] and edge.target_node == node_id:
                edges.append(edge)
        return edges

    def validate_connectivity(self) -> List[str]:
        """Validate chain connectivity and return any issues."""
        issues = []

        # Check for isolated nodes
        connected_nodes = set()
        for edge in self.edges:
            connected_nodes.add(edge.source_node)
            connected_nodes.add(edge.target_node)

        isolated_nodes = {node.id for node in self.nodes} - connected_nodes
        if isolated_nodes:
            issues.append(f"Isolated nodes found: {', '.join(isolated_nodes)}")

        # Check for cycles (simplified check)
        # This is a basic implementation; a full cycle detection would use graph algorithms
        for edge in self.edges:
            reverse_edges = [e for e in self.edges
                           if e.source_node == edge.target_node and e.target_node == edge.source_node]
            if reverse_edges:
                issues.append(f"Potential cycle detected between {edge.source_node} and {edge.target_node}")

        return issues


# ================================================================
# Request/Response Models
# ================================================================

class ChainDefinitionCreate(BaseChainModel):
    """Model for creating a new chain definition."""
    name: str = Field(description="Human-readable chain name")
    category: ChainCategory = Field(description="Chain category")
    description: Optional[str] = Field(None, description="Detailed description")
    nodes: List[ChainNode] = Field(description="List of nodes in the chain")
    edges: List[ChainEdge] = Field(description="List of edges connecting nodes")
    dependencies: List[ChainDependency] = Field(default_factory=list, description="External dependencies")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    # Reuse validators from ChainDefinition
    _validate_name = field_validator('name')(ChainDefinition.validate_name.func)
    _validate_description = field_validator('description')(ChainDefinition.validate_description.func)
    _validate_nodes = field_validator('nodes')(ChainDefinition.validate_nodes.func)
    _validate_edges = field_validator('edges')(ChainDefinition.validate_edges.func)


class ChainDefinitionUpdate(BaseChainModel):
    """Model for updating an existing chain definition."""
    name: Optional[str] = Field(None, description="Human-readable chain name")
    description: Optional[str] = Field(None, description="Detailed description")
    nodes: Optional[List[ChainNode]] = Field(None, description="List of nodes in the chain")
    edges: Optional[List[ChainEdge]] = Field(None, description="List of edges connecting nodes")
    dependencies: Optional[List[ChainDependency]] = Field(None, description="External dependencies")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    status: Optional[ChainStatus] = Field(None, description="Chain status")


class ChainHealthStatus(BaseChainModel):
    """Complete health status for a chain."""
    chain_id: str = Field(description="Chain identifier")
    status: ChainStatus = Field(description="Overall chain status")
    overall_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Overall health score")
    node_health: List[NodeHealth] = Field(description="Health status of individual nodes")
    sla_compliance: Optional[SLACompliance] = Field(None, description="SLA compliance information")
    last_check: Optional[datetime] = Field(None, description="Last health check timestamp")
    health_trends: Optional[Dict[str, Any]] = Field(None, description="Health trend data")


# ================================================================
# Discovery and Analysis Models
# ================================================================

class DiscoveredChain(BaseChainModel, TimestampMixin):
    """A chain discovered through automated analysis."""
    discovery_id: UUID = Field(default_factory=uuid4, description="Unique discovery identifier")
    proposed_chain_id: str = Field(description="Proposed chain identifier")
    name: str = Field(description="Discovered chain name")
    category: ChainCategory = Field(description="Detected chain category")
    description: str = Field(description="Auto-generated description")
    discovery_method: DiscoveryMethod = Field(description="Method used for discovery")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence in discovery accuracy")
    nodes: List[ChainNode] = Field(description="Discovered nodes")
    edges: List[ChainEdge] = Field(description="Discovered edges")
    evidence: Dict[str, Any] = Field(description="Evidence supporting the discovery")
    status: str = Field("pending_review", description="Review status")


class ValidationResult(BaseChainModel):
    """Result of validating a chain definition."""
    valid: bool = Field(description="Whether the chain is valid")
    errors: List[Dict[str, str]] = Field(default_factory=list, description="Validation errors")
    warnings: List[Dict[str, str]] = Field(default_factory=list, description="Validation warnings")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")


# ================================================================
# Export all models
# ================================================================

__all__ = [
    # Enums
    'ChainCategory', 'NodeType', 'EdgeType', 'DependencyType',
    'CriticalityLevel', 'ChainStatus', 'BackoffStrategy', 'DiscoveryMethod',

    # Configuration Models
    'NodePosition', 'HealthCheckConfig', 'RetryPolicy',

    # Core Models
    'ChainNode', 'ChainEdge', 'ChainDependency', 'ChainDefinition',

    # Health and Metrics
    'ChainMetrics', 'NodeHealth', 'SLACompliance', 'ChainHealthStatus',

    # Request/Response Models
    'ChainDefinitionCreate', 'ChainDefinitionUpdate',

    # Discovery and Analysis
    'DiscoveredChain', 'ValidationResult',

    # Base Models
    'BaseChainModel', 'TimestampMixin'
]