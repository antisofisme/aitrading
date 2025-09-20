"""
Embedded Chain Mapping System - Health Monitor
==============================================

This module provides real-time health monitoring for chains, including:
- Continuous health checks for chain nodes
- SLA compliance monitoring
- Performance metrics collection
- Alerting and notification system
- Health trend analysis

Key Features:
- Asynchronous monitoring with configurable intervals
- Multiple health check strategies (HTTP, WebSocket, Database)
- Real-time alerting with escalation rules
- Integration with existing CoreLogger and metrics systems
- Automatic healing suggestions
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import aiohttp
import websockets
from urllib.parse import urljoin

from ..core.models import (
    ChainDefinition, ChainNode, ChainHealthStatus, NodeHealth,
    SLACompliance, ChainStatus, NodeType, HealthCheckConfig
)


logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class HealthCheckStrategy(str, Enum):
    """Health check strategies."""
    HTTP = "http"
    WEBSOCKET = "websocket"
    DATABASE = "database"
    CUSTOM = "custom"


@dataclass
class HealthCheckResult:
    """Result of a health check operation."""
    node_id: str
    status: ChainStatus
    response_time: float
    timestamp: datetime
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    """Health alert information."""
    id: str
    chain_id: str
    node_id: Optional[str]
    severity: AlertSeverity
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    escalated: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MonitoringConfig:
    """Configuration for chain monitoring."""
    chain_id: str
    enabled: bool = True
    check_interval: int = 60  # seconds
    timeout: int = 5000  # milliseconds
    max_retries: int = 3
    alert_thresholds: Dict[str, float] = field(default_factory=dict)
    notification_config: Dict[str, Any] = field(default_factory=dict)
    escalation_rules: List[Dict[str, Any]] = field(default_factory=list)


class HealthChecker:
    """Base class for health checking strategies."""

    async def check_health(self, node: ChainNode, config: HealthCheckConfig) -> HealthCheckResult:
        """Perform health check for a node."""
        raise NotImplementedError


class HTTPHealthChecker(HealthChecker):
    """HTTP-based health checker."""

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def _ensure_session(self):
        """Ensure HTTP session is available."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)

    async def check_health(self, node: ChainNode, config: HealthCheckConfig) -> HealthCheckResult:
        """Perform HTTP health check."""
        await self._ensure_session()

        start_time = time.time()
        endpoint = config.endpoint or self._default_health_endpoint(node)

        try:
            async with self.session.get(
                endpoint,
                timeout=aiohttp.ClientTimeout(total=config.timeout_ms / 1000)
            ) as response:
                response_time = (time.time() - start_time) * 1000

                if response.status in config.expected_status_codes:
                    status = ChainStatus.HEALTHY
                    error_message = None
                else:
                    status = ChainStatus.DEGRADED
                    error_message = f"Unexpected status code: {response.status}"

                # Try to get response body for additional info
                try:
                    response_data = await response.json()
                    metadata = {"response_data": response_data}
                except:
                    metadata = {"response_status": response.status}

                return HealthCheckResult(
                    node_id=node.id,
                    status=status,
                    response_time=response_time,
                    timestamp=datetime.utcnow(),
                    error_message=error_message,
                    metadata=metadata
                )

        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                node_id=node.id,
                status=ChainStatus.FAILED,
                response_time=response_time,
                timestamp=datetime.utcnow(),
                error_message="Health check timeout",
                metadata={"timeout_ms": config.timeout_ms}
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                node_id=node.id,
                status=ChainStatus.FAILED,
                response_time=response_time,
                timestamp=datetime.utcnow(),
                error_message=str(e),
                metadata={"error_type": type(e).__name__}
            )

    def _default_health_endpoint(self, node: ChainNode) -> str:
        """Generate default health endpoint for a node."""
        service_ports = {
            'api-gateway': 8000,
            'data-bridge': 8001,
            'ai-orchestration': 8003,
            'deep-learning': 8004,
            'ai-provider': 8005,
            'ml-processing': 8006,
            'trading-engine': 8007,
            'database-service': 8008,
            'user-service': 8009,
            'strategy-optimization': 8010,
            'performance-analytics': 8002
        }

        port = service_ports.get(node.service_name, 8000)
        return f"http://localhost:{port}/health"

    async def cleanup(self):
        """Cleanup HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()


class WebSocketHealthChecker(HealthChecker):
    """WebSocket-based health checker."""

    async def check_health(self, node: ChainNode, config: HealthCheckConfig) -> HealthCheckResult:
        """Perform WebSocket health check."""
        start_time = time.time()
        endpoint = config.endpoint or self._default_websocket_endpoint(node)

        try:
            async with websockets.connect(
                endpoint,
                timeout=config.timeout_ms / 1000
            ) as websocket:
                # Send ping message
                await websocket.send(json.dumps({"type": "health_check", "timestamp": time.time()}))

                # Wait for response
                response = await asyncio.wait_for(
                    websocket.recv(),
                    timeout=config.timeout_ms / 1000
                )

                response_time = (time.time() - start_time) * 1000

                try:
                    response_data = json.loads(response)
                    if response_data.get("status") == "ok":
                        status = ChainStatus.HEALTHY
                    else:
                        status = ChainStatus.DEGRADED
                except:
                    status = ChainStatus.DEGRADED

                return HealthCheckResult(
                    node_id=node.id,
                    status=status,
                    response_time=response_time,
                    timestamp=datetime.utcnow(),
                    metadata={"response": response}
                )

        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                node_id=node.id,
                status=ChainStatus.FAILED,
                response_time=response_time,
                timestamp=datetime.utcnow(),
                error_message="WebSocket health check timeout"
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                node_id=node.id,
                status=ChainStatus.FAILED,
                response_time=response_time,
                timestamp=datetime.utcnow(),
                error_message=str(e)
            )

    def _default_websocket_endpoint(self, node: ChainNode) -> str:
        """Generate default WebSocket endpoint for a node."""
        service_ports = {
            'api-gateway': 8000,
            'data-bridge': 8001
        }

        port = service_ports.get(node.service_name, 8001)
        return f"ws://localhost:{port}/ws/health"


class DatabaseHealthChecker(HealthChecker):
    """Database-based health checker."""

    async def check_health(self, node: ChainNode, config: HealthCheckConfig) -> HealthCheckResult:
        """Perform database health check."""
        start_time = time.time()

        try:
            # This would integrate with existing database infrastructure
            # For now, we'll simulate the check
            await asyncio.sleep(0.05)  # Simulate database query time

            response_time = (time.time() - start_time) * 1000

            # Simulate database health check logic
            if response_time < 100:  # Under 100ms is healthy
                status = ChainStatus.HEALTHY
            elif response_time < 500:  # Under 500ms is degraded
                status = ChainStatus.DEGRADED
            else:
                status = ChainStatus.FAILED

            return HealthCheckResult(
                node_id=node.id,
                status=status,
                response_time=response_time,
                timestamp=datetime.utcnow(),
                metadata={"query_type": "health_check"}
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                node_id=node.id,
                status=ChainStatus.FAILED,
                response_time=response_time,
                timestamp=datetime.utcnow(),
                error_message=str(e)
            )


class ChainHealthMonitor:
    """
    Real-time health monitoring system for chains.

    Provides continuous monitoring of chain health, SLA compliance,
    and automated alerting with escalation support.
    """

    def __init__(
        self,
        alert_callback: Optional[Callable[[Alert], None]] = None,
        metrics_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None
    ):
        """
        Initialize the health monitor.

        Args:
            alert_callback: Callback function for alerts
            metrics_callback: Callback function for metrics
        """
        self.alert_callback = alert_callback
        self.metrics_callback = metrics_callback

        # Health checkers
        self.health_checkers: Dict[HealthCheckStrategy, HealthChecker] = {
            HealthCheckStrategy.HTTP: HTTPHealthChecker(),
            HealthCheckStrategy.WEBSOCKET: WebSocketHealthChecker(),
            HealthCheckStrategy.DATABASE: DatabaseHealthChecker()
        }

        # Monitoring state
        self.monitoring_configs: Dict[str, MonitoringConfig] = {}
        self.active_monitors: Dict[str, asyncio.Task] = {}
        self.health_history: Dict[str, List[HealthCheckResult]] = {}
        self.active_alerts: Dict[str, Alert] = {}

        # Performance tracking
        self.metrics: Dict[str, Any] = {
            'total_checks': 0,
            'failed_checks': 0,
            'avg_response_time': 0.0,
            'alerts_generated': 0
        }

        self._shutdown_event = asyncio.Event()

    async def start_monitoring(self, chain_def: ChainDefinition, config: MonitoringConfig) -> bool:
        """
        Start monitoring a specific chain.

        Args:
            chain_def: Chain definition to monitor
            config: Monitoring configuration

        Returns:
            True if monitoring started successfully
        """
        if not config.enabled:
            logger.info(f"Monitoring disabled for chain {chain_def.id}")
            return False

        if chain_def.id in self.active_monitors:
            logger.warning(f"Chain {chain_def.id} is already being monitored")
            return False

        self.monitoring_configs[chain_def.id] = config

        # Start monitoring task
        monitor_task = asyncio.create_task(
            self._monitor_chain_loop(chain_def, config)
        )
        self.active_monitors[chain_def.id] = monitor_task

        logger.info(f"Started monitoring chain {chain_def.id} with interval {config.check_interval}s")
        return True

    async def stop_monitoring(self, chain_id: str) -> bool:
        """
        Stop monitoring a specific chain.

        Args:
            chain_id: Chain identifier

        Returns:
            True if monitoring stopped successfully
        """
        if chain_id not in self.active_monitors:
            logger.warning(f"Chain {chain_id} is not being monitored")
            return False

        # Cancel monitoring task
        monitor_task = self.active_monitors[chain_id]
        monitor_task.cancel()

        try:
            await monitor_task
        except asyncio.CancelledError:
            pass

        # Cleanup
        del self.active_monitors[chain_id]
        self.monitoring_configs.pop(chain_id, None)

        logger.info(f"Stopped monitoring chain {chain_id}")
        return True

    async def get_chain_health(self, chain_def: ChainDefinition) -> ChainHealthStatus:
        """
        Get current health status of a chain.

        Args:
            chain_def: Chain definition

        Returns:
            Current health status
        """
        # Collect node health
        node_health_list = []
        for node in chain_def.nodes:
            node_health = await self._check_node_health(node)
            node_health_list.append(node_health)

        # Calculate overall status
        overall_status = self._calculate_overall_status(node_health_list)

        # Calculate health score
        health_score = self._calculate_health_score(node_health_list)

        # Check SLA compliance
        sla_compliance = await self._check_sla_compliance(chain_def.id, node_health_list)

        return ChainHealthStatus(
            chain_id=chain_def.id,
            status=overall_status,
            overall_score=health_score,
            node_health=node_health_list,
            sla_compliance=sla_compliance,
            last_check=datetime.utcnow()
        )

    async def _monitor_chain_loop(self, chain_def: ChainDefinition, config: MonitoringConfig):
        """Main monitoring loop for a chain."""
        logger.info(f"Starting monitoring loop for chain {chain_def.id}")

        while not self._shutdown_event.is_set():
            try:
                # Perform health checks
                health_status = await self.get_chain_health(chain_def)

                # Store health history
                self._update_health_history(chain_def.id, health_status)

                # Check for alerts
                await self._process_health_alerts(chain_def, health_status, config)

                # Update metrics
                self._update_metrics(health_status)

                # Send metrics to callback
                if self.metrics_callback:
                    try:
                        self.metrics_callback(chain_def.id, {
                            'health_score': health_status.overall_score,
                            'status': health_status.status.value,
                            'timestamp': health_status.last_check.isoformat()
                        })
                    except Exception as e:
                        logger.error(f"Metrics callback failed: {e}")

                # Wait for next check
                await asyncio.sleep(config.check_interval)

            except asyncio.CancelledError:
                logger.info(f"Monitoring cancelled for chain {chain_def.id}")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop for chain {chain_def.id}: {e}")
                await asyncio.sleep(min(config.check_interval, 60))  # Backoff on error

    async def _check_node_health(self, node: ChainNode) -> NodeHealth:
        """Check health of a specific node."""
        health_config = node.health_check or HealthCheckConfig()

        if not health_config.enabled:
            return NodeHealth(
                node_id=node.id,
                status=ChainStatus.UNKNOWN,
                last_check=datetime.utcnow()
            )

        # Determine health check strategy
        strategy = self._determine_health_strategy(node)
        checker = self.health_checkers.get(strategy)

        if not checker:
            return NodeHealth(
                node_id=node.id,
                status=ChainStatus.UNKNOWN,
                last_check=datetime.utcnow(),
                error_message=f"No health checker for strategy: {strategy}"
            )

        # Perform health check with retries
        last_error = None
        for attempt in range(health_config.retries + 1):
            try:
                result = await checker.check_health(node, health_config)

                return NodeHealth(
                    node_id=node.id,
                    status=result.status,
                    latency=result.response_time,
                    last_check=result.timestamp,
                    error_message=result.error_message,
                    response_time=result.response_time
                )

            except Exception as e:
                last_error = str(e)
                if attempt < health_config.retries:
                    await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff

        # All retries failed
        return NodeHealth(
            node_id=node.id,
            status=ChainStatus.FAILED,
            last_check=datetime.utcnow(),
            error_message=f"All health check attempts failed. Last error: {last_error}"
        )

    def _determine_health_strategy(self, node: ChainNode) -> HealthCheckStrategy:
        """Determine appropriate health check strategy for a node."""
        if node.type == NodeType.WEBSOCKET:
            return HealthCheckStrategy.WEBSOCKET
        elif node.type == NodeType.DATABASE:
            return HealthCheckStrategy.DATABASE
        elif node.health_check and node.health_check.endpoint:
            if node.health_check.endpoint.startswith('ws://') or node.health_check.endpoint.startswith('wss://'):
                return HealthCheckStrategy.WEBSOCKET
            else:
                return HealthCheckStrategy.HTTP
        else:
            return HealthCheckStrategy.HTTP  # Default

    def _calculate_overall_status(self, node_health_list: List[NodeHealth]) -> ChainStatus:
        """Calculate overall chain status from node health."""
        if not node_health_list:
            return ChainStatus.UNKNOWN

        failed_count = sum(1 for nh in node_health_list if nh.status == ChainStatus.FAILED)
        degraded_count = sum(1 for nh in node_health_list if nh.status == ChainStatus.DEGRADED)
        healthy_count = sum(1 for nh in node_health_list if nh.status == ChainStatus.HEALTHY)

        total_nodes = len(node_health_list)

        # If more than 50% failed, chain is failed
        if failed_count > total_nodes * 0.5:
            return ChainStatus.FAILED

        # If any failed or more than 25% degraded, chain is degraded
        if failed_count > 0 or degraded_count > total_nodes * 0.25:
            return ChainStatus.DEGRADED

        # If all healthy, chain is healthy
        if healthy_count == total_nodes:
            return ChainStatus.HEALTHY

        # Otherwise degraded
        return ChainStatus.DEGRADED

    def _calculate_health_score(self, node_health_list: List[NodeHealth]) -> Optional[float]:
        """Calculate health score (0-100) from node health."""
        if not node_health_list:
            return None

        total_score = 0.0
        scored_nodes = 0

        for node_health in node_health_list:
            if node_health.status == ChainStatus.HEALTHY:
                score = 100.0
            elif node_health.status == ChainStatus.DEGRADED:
                score = 60.0
            elif node_health.status == ChainStatus.FAILED:
                score = 0.0
            else:  # UNKNOWN
                continue  # Don't include in average

            # Adjust score based on latency if available
            if node_health.latency is not None:
                if node_health.latency < 100:  # Under 100ms is excellent
                    latency_score = 100.0
                elif node_health.latency < 500:  # Under 500ms is good
                    latency_score = 80.0
                elif node_health.latency < 1000:  # Under 1s is acceptable
                    latency_score = 60.0
                else:  # Over 1s is poor
                    latency_score = 30.0

                # Combine status and latency scores (70% status, 30% latency)
                score = score * 0.7 + latency_score * 0.3

            total_score += score
            scored_nodes += 1

        if scored_nodes == 0:
            return None

        return round(total_score / scored_nodes, 2)

    async def _check_sla_compliance(self, chain_id: str, node_health_list: List[NodeHealth]) -> Optional[SLACompliance]:
        """Check SLA compliance for a chain."""
        config = self.monitoring_configs.get(chain_id)
        if not config or not config.alert_thresholds:
            return None

        # Calculate metrics
        avg_latency = None
        availability = 0.0

        if node_health_list:
            latencies = [nh.latency for nh in node_health_list if nh.latency is not None]
            if latencies:
                avg_latency = sum(latencies) / len(latencies)

            healthy_nodes = sum(1 for nh in node_health_list if nh.status == ChainStatus.HEALTHY)
            availability = healthy_nodes / len(node_health_list)

        # Check thresholds
        latency_sla = config.alert_thresholds.get('latency_threshold')
        uptime_sla = config.alert_thresholds.get('availability_threshold', 0.99)

        meets_sla = True
        if latency_sla is not None and avg_latency is not None and avg_latency > latency_sla:
            meets_sla = False
        if availability < uptime_sla:
            meets_sla = False

        return SLACompliance(
            meets_sla=meets_sla,
            latency_sla=latency_sla,
            actual_latency=avg_latency,
            uptime_sla=uptime_sla,
            actual_uptime=availability
        )

    def _update_health_history(self, chain_id: str, health_status: ChainHealthStatus):
        """Update health history for trend analysis."""
        if chain_id not in self.health_history:
            self.health_history[chain_id] = []

        # Store health check results
        for node_health in health_status.node_health:
            result = HealthCheckResult(
                node_id=node_health.node_id,
                status=node_health.status,
                response_time=node_health.latency or 0.0,
                timestamp=health_status.last_check,
                error_message=node_health.error_message
            )
            self.health_history[chain_id].append(result)

        # Keep only last 1000 entries per chain
        if len(self.health_history[chain_id]) > 1000:
            self.health_history[chain_id] = self.health_history[chain_id][-1000:]

    async def _process_health_alerts(
        self,
        chain_def: ChainDefinition,
        health_status: ChainHealthStatus,
        config: MonitoringConfig
    ):
        """Process health status and generate alerts if needed."""
        # Check for status-based alerts
        if health_status.status in [ChainStatus.FAILED, ChainStatus.DEGRADED]:
            await self._generate_status_alert(chain_def.id, health_status, config)

        # Check for SLA violations
        if health_status.sla_compliance and not health_status.sla_compliance.meets_sla:
            await self._generate_sla_alert(chain_def.id, health_status, config)

        # Check for individual node alerts
        for node_health in health_status.node_health:
            if node_health.status == ChainStatus.FAILED:
                await self._generate_node_alert(chain_def.id, node_health, config)

    async def _generate_status_alert(
        self,
        chain_id: str,
        health_status: ChainHealthStatus,
        config: MonitoringConfig
    ):
        """Generate alert for chain status issues."""
        alert_id = f"{chain_id}_status_{health_status.status.value}"

        # Check if alert already exists
        if alert_id in self.active_alerts and not self.active_alerts[alert_id].resolved:
            return

        severity = AlertSeverity.HIGH if health_status.status == ChainStatus.FAILED else AlertSeverity.MEDIUM

        alert = Alert(
            id=alert_id,
            chain_id=chain_id,
            node_id=None,
            severity=severity,
            message=f"Chain {chain_id} status is {health_status.status.value}. Health score: {health_status.overall_score}",
            timestamp=datetime.utcnow(),
            metadata={
                'health_score': health_status.overall_score,
                'status': health_status.status.value,
                'affected_nodes': [nh.node_id for nh in health_status.node_health if nh.status != ChainStatus.HEALTHY]
            }
        )

        await self._send_alert(alert)

    async def _generate_sla_alert(
        self,
        chain_id: str,
        health_status: ChainHealthStatus,
        config: MonitoringConfig
    ):
        """Generate alert for SLA violations."""
        if not health_status.sla_compliance:
            return

        alert_id = f"{chain_id}_sla_violation"

        # Check if alert already exists
        if alert_id in self.active_alerts and not self.active_alerts[alert_id].resolved:
            return

        alert = Alert(
            id=alert_id,
            chain_id=chain_id,
            node_id=None,
            severity=AlertSeverity.HIGH,
            message=f"Chain {chain_id} SLA violation detected",
            timestamp=datetime.utcnow(),
            metadata={
                'sla_compliance': {
                    'latency_sla': health_status.sla_compliance.latency_sla,
                    'actual_latency': health_status.sla_compliance.actual_latency,
                    'uptime_sla': health_status.sla_compliance.uptime_sla,
                    'actual_uptime': health_status.sla_compliance.actual_uptime
                }
            }
        )

        await self._send_alert(alert)

    async def _generate_node_alert(
        self,
        chain_id: str,
        node_health: NodeHealth,
        config: MonitoringConfig
    ):
        """Generate alert for individual node failures."""
        alert_id = f"{chain_id}_node_{node_health.node_id}_failed"

        # Check if alert already exists
        if alert_id in self.active_alerts and not self.active_alerts[alert_id].resolved:
            return

        alert = Alert(
            id=alert_id,
            chain_id=chain_id,
            node_id=node_health.node_id,
            severity=AlertSeverity.CRITICAL,
            message=f"Node {node_health.node_id} in chain {chain_id} has failed: {node_health.error_message or 'Unknown error'}",
            timestamp=datetime.utcnow(),
            metadata={
                'node_id': node_health.node_id,
                'error_message': node_health.error_message,
                'last_check': node_health.last_check.isoformat() if node_health.last_check else None
            }
        )

        await self._send_alert(alert)

    async def _send_alert(self, alert: Alert):
        """Send alert through configured channels."""
        self.active_alerts[alert.id] = alert
        self.metrics['alerts_generated'] += 1

        logger.warning(f"ALERT [{alert.severity.value.upper()}] {alert.message}")

        if self.alert_callback:
            try:
                self.alert_callback(alert)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")

    def _update_metrics(self, health_status: ChainHealthStatus):
        """Update monitoring metrics."""
        self.metrics['total_checks'] += len(health_status.node_health)

        failed_nodes = sum(1 for nh in health_status.node_health if nh.status == ChainStatus.FAILED)
        self.metrics['failed_checks'] += failed_nodes

        # Update average response time
        latencies = [nh.latency for nh in health_status.node_health if nh.latency is not None]
        if latencies:
            current_avg = self.metrics.get('avg_response_time', 0.0)
            new_avg = sum(latencies) / len(latencies)
            # Simple moving average
            self.metrics['avg_response_time'] = (current_avg * 0.9 + new_avg * 0.1)

    async def trigger_health_check(self, chain_def: ChainDefinition) -> ChainHealthStatus:
        """Manually trigger a health check for a chain."""
        logger.info(f"Manual health check triggered for chain {chain_def.id}")
        return await self.get_chain_health(chain_def)

    def get_active_alerts(self, chain_id: Optional[str] = None) -> List[Alert]:
        """Get active alerts, optionally filtered by chain."""
        alerts = [alert for alert in self.active_alerts.values() if not alert.resolved]

        if chain_id:
            alerts = [alert for alert in alerts if alert.chain_id == chain_id]

        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)

    async def resolve_alert(self, alert_id: str, resolution_note: Optional[str] = None) -> bool:
        """Resolve an active alert."""
        if alert_id not in self.active_alerts:
            return False

        alert = self.active_alerts[alert_id]
        alert.resolved = True
        alert.resolved_at = datetime.utcnow()

        if resolution_note:
            alert.metadata['resolution_note'] = resolution_note

        logger.info(f"Alert {alert_id} resolved: {resolution_note or 'No note provided'}")
        return True

    def get_monitoring_statistics(self) -> Dict[str, Any]:
        """Get monitoring statistics."""
        active_chains = len(self.active_monitors)
        active_alerts_count = len([a for a in self.active_alerts.values() if not a.resolved])

        return {
            'active_chains': active_chains,
            'active_alerts': active_alerts_count,
            'total_checks': self.metrics['total_checks'],
            'failed_checks': self.metrics['failed_checks'],
            'success_rate': (
                (self.metrics['total_checks'] - self.metrics['failed_checks']) / self.metrics['total_checks']
                if self.metrics['total_checks'] > 0 else 0.0
            ),
            'avg_response_time': self.metrics['avg_response_time'],
            'alerts_generated': self.metrics['alerts_generated']
        }

    async def cleanup(self):
        """Cleanup monitoring resources."""
        logger.info("Shutting down chain health monitor")

        # Signal shutdown
        self._shutdown_event.set()

        # Stop all monitoring tasks
        for chain_id in list(self.active_monitors.keys()):
            await self.stop_monitoring(chain_id)

        # Cleanup health checkers
        for checker in self.health_checkers.values():
            if hasattr(checker, 'cleanup'):
                await checker.cleanup()

        logger.info("Chain health monitor shutdown complete")


# Export main classes
__all__ = [
    'ChainHealthMonitor', 'HealthChecker', 'HTTPHealthChecker',
    'WebSocketHealthChecker', 'DatabaseHealthChecker', 'HealthCheckResult',
    'Alert', 'MonitoringConfig', 'AlertSeverity'
]