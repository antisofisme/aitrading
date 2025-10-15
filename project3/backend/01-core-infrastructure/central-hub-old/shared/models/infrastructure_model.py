"""
Infrastructure Models - Type definitions for infrastructure monitoring
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum
import time


class InfrastructureType(Enum):
    """Infrastructure types"""
    POSTGRES = "postgres"
    REDIS = "redis"
    ARANGO = "arango"
    CLICKHOUSE = "clickhouse"
    NATS = "nats"
    KAFKA = "kafka"
    ZOOKEEPER = "zookeeper"
    WEAVIATE = "weaviate"


class HealthCheckMethod(Enum):
    """Health check methods"""
    HTTP = "http"
    REDIS_PING = "redis_ping"
    KAFKA_ADMIN = "kafka_admin"
    TCP = "tcp"


class InfrastructureStatus(Enum):
    """Infrastructure health status"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass
class HealthCheckConfig:
    """Health check configuration"""
    method: HealthCheckMethod
    endpoint: Optional[str] = None
    port: Optional[int] = None
    command: Optional[str] = None
    timeout: int = 5
    interval: int = 30


@dataclass
class InfrastructureConfig:
    """Infrastructure component configuration"""
    name: str
    host: str
    port: int
    type: InfrastructureType
    health_check: HealthCheckConfig
    dependencies: List[str] = field(default_factory=list)
    critical: bool = True
    description: str = ""
    management_port: Optional[int] = None


@dataclass
class InfrastructureHealth:
    """Infrastructure health status"""
    name: str
    type: str
    status: InfrastructureStatus
    last_check: int = field(default_factory=lambda: int(time.time() * 1000))
    response_time_ms: Optional[float] = None
    error: Optional[str] = None
    critical: bool = True
    dependents: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "type": self.type,
            "status": self.status.value if isinstance(self.status, InfrastructureStatus) else self.status,
            "last_check": self.last_check,
            "response_time_ms": self.response_time_ms,
            "error": self.error,
            "critical": self.critical,
            "dependents": self.dependents
        }


@dataclass
class ServiceDependency:
    """Service dependency configuration"""
    service_name: str
    requires: List[str] = field(default_factory=list)
    optional: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class DependencyNode:
    """Dependency graph node"""
    name: str
    type: str  # 'infrastructure' or 'service'
    depends_on: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    required_by: List[str] = field(default_factory=list)  # Services that require this
    optional_for: List[str] = field(default_factory=list)  # Services that optionally use this


@dataclass
class ImpactAnalysis:
    """Impact analysis result"""
    failed_component: str
    component_type: str  # 'infrastructure' or 'service'
    impact_level: str  # 'critical', 'degraded', 'warning', 'none'
    affected_services: List[Dict[str, str]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    timestamp: int = field(default_factory=lambda: int(time.time() * 1000))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "failed_component": self.failed_component,
            "component_type": self.component_type,
            "impact_level": self.impact_level,
            "affected_services": self.affected_services,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp
        }


@dataclass
class SystemHealth:
    """Complete system health status"""
    timestamp: int = field(default_factory=lambda: int(time.time() * 1000))
    overall_status: str = "healthy"  # healthy, degraded, critical
    summary: Dict[str, Any] = field(default_factory=dict)
    infrastructure: List[Dict[str, Any]] = field(default_factory=list)
    services: List[Dict[str, Any]] = field(default_factory=list)
    impact_analysis: List[Dict[str, Any]] = field(default_factory=list)
    dependency_graph: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp,
            "overall_status": self.overall_status,
            "summary": self.summary,
            "infrastructure": self.infrastructure,
            "services": self.services,
            "impact_analysis": self.impact_analysis,
            "dependency_graph": self.dependency_graph
        }


@dataclass
class Alert:
    """Alert message"""
    id: str
    severity: AlertSeverity
    component: str
    component_type: str
    message: str
    timestamp: int = field(default_factory=lambda: int(time.time() * 1000))
    details: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "severity": self.severity.value if isinstance(self.severity, AlertSeverity) else self.severity,
            "component": self.component,
            "component_type": self.component_type,
            "message": self.message,
            "timestamp": self.timestamp,
            "details": self.details,
            "acknowledged": self.acknowledged
        }
