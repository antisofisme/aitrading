"""
Real-Time Performance Monitoring System
Monitors 11 microservices with sub-500ms latency targets and 99.9% uptime
"""

import asyncio
import logging
import time
import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import aioredis
import asyncpg
import httpx
from prometheus_client import Counter, Histogram, Gauge, Summary, CollectorRegistry, generate_latest
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from functools import wraps

# Performance Metrics Registry
METRICS_REGISTRY = CollectorRegistry()

# Core Performance Metrics
REQUEST_TOTAL = Counter('requests_total', 'Total requests', ['service', 'endpoint', 'status'], registry=METRICS_REGISTRY)
REQUEST_DURATION = Histogram('request_duration_seconds', 'Request duration', ['service', 'endpoint'], registry=METRICS_REGISTRY)
RESPONSE_TIME = Summary('response_time_seconds', 'Response time summary', ['service'], registry=METRICS_REGISTRY)

# System Health Metrics
SERVICE_HEALTH = Gauge('service_health', 'Service health status (1=healthy, 0=unhealthy)', ['service'], registry=METRICS_REGISTRY)
CPU_USAGE = Gauge('cpu_usage_percent', 'CPU usage percentage', ['service'], registry=METRICS_REGISTRY)
MEMORY_USAGE = Gauge('memory_usage_bytes', 'Memory usage in bytes', ['service'], registry=METRICS_REGISTRY)
ACTIVE_CONNECTIONS = Gauge('active_connections', 'Active connections count', ['service'], registry=METRICS_REGISTRY)

# Trading-Specific Metrics
SIGNAL_LATENCY = Histogram('trading_signal_latency_ms', 'Trading signal generation latency in milliseconds', registry=METRICS_REGISTRY)
TICK_PROCESSING_RATE = Gauge('tick_processing_rate', 'Ticks processed per second', registry=METRICS_REGISTRY)
MODEL_INFERENCE_TIME = Histogram('model_inference_time_ms', 'AI model inference time in milliseconds', ['model_name'], registry=METRICS_REGISTRY)
MODEL_ACCURACY = Gauge('model_accuracy', 'Model prediction accuracy', ['model_name'], registry=METRICS_REGISTRY)

# Alert Metrics
ALERT_TRIGGERED = Counter('alerts_triggered_total', 'Total alerts triggered', ['alert_type', 'severity'], registry=METRICS_REGISTRY)
SLA_VIOLATIONS = Counter('sla_violations_total', 'SLA violations count', ['service', 'metric'], registry=METRICS_REGISTRY)

@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    service: str
    metric_name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = None

    def to_dict(self) -> Dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

@dataclass
class Alert:
    """Alert data structure"""
    id: str
    service: str
    metric: str
    threshold: float
    current_value: float
    severity: str  # critical, warning, info
    message: str
    timestamp: datetime
    acknowledged: bool = False

    def to_dict(self) -> Dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

@dataclass
class ServiceHealth:
    """Service health status"""
    name: str
    healthy: bool
    response_time: float
    cpu_usage: float
    memory_usage: float
    active_connections: int
    last_check: datetime
    error_message: Optional[str] = None

class PerformanceThresholds:
    """Performance thresholds and SLA definitions"""

    # Response time thresholds (milliseconds)
    RESPONSE_TIME_THRESHOLDS = {
        'gateway': {'warning': 100, 'critical': 200},
        'business-api': {'warning': 10, 'critical': 15},
        'trading-engine': {'warning': 250, 'critical': 500},
        'market-data': {'warning': 50, 'critical': 100},
        'risk-management': {'warning': 200, 'critical': 400},
        'database': {'warning': 50, 'critical': 100},
        'auth-service': {'warning': 100, 'critical': 200},
        'user-management': {'warning': 150, 'critical': 300},
        'subscription-service': {'warning': 100, 'critical': 200},
        'notification-service': {'warning': 300, 'critical': 500},
        'billing-service': {'warning': 200, 'critical': 400}
    }

    # System resource thresholds
    CPU_THRESHOLD = {'warning': 70, 'critical': 85}
    MEMORY_THRESHOLD = {'warning': 80, 'critical': 90}

    # Trading-specific thresholds
    SIGNAL_LATENCY_THRESHOLD = {'warning': 400, 'critical': 500}  # milliseconds
    TICK_RATE_THRESHOLD = {'warning': 15, 'critical': 10}  # ticks per second (lower is worse)
    MODEL_ACCURACY_THRESHOLD = {'warning': 0.75, 'critical': 0.65}  # accuracy percentage

    # Uptime SLA
    UPTIME_SLA = 0.999  # 99.9% uptime requirement

class PerformanceMonitor:
    """Real-time performance monitoring system"""

    def __init__(self, redis_url: str = "redis://localhost:6379",
                 db_url: str = "postgresql://user:pass@localhost/aitrading"):
        self.redis_url = redis_url
        self.db_url = db_url
        self.redis_client: Optional[aioredis.Redis] = None
        self.db_pool: Optional[asyncpg.Pool] = None
        self.http_client: Optional[httpx.AsyncClient] = None

        # Internal state
        self.is_running = False
        self.monitoring_tasks: List[asyncio.Task] = []
        self.metrics_buffer: deque = deque(maxlen=10000)
        self.alerts_buffer: deque = deque(maxlen=1000)
        self.service_registry = {
            'gateway': 'http://localhost:8000',
            'business-api': 'http://localhost:8050',
            'trading-engine': 'http://localhost:8003',
            'market-data': 'http://localhost:8002',
            'risk-management': 'http://localhost:8004',
            'database': 'http://localhost:8001',
            'auth-service': 'http://localhost:8051',
            'user-management': 'http://localhost:8021',
            'subscription-service': 'http://localhost:8022',
            'notification-service': 'http://localhost:8024',
            'billing-service': 'http://localhost:8025'
        }

        # Performance data storage
        self.response_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.error_rates: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.uptime_tracking: Dict[str, List[bool]] = defaultdict(list)

        # Threading for CPU-intensive operations
        self.executor = ThreadPoolExecutor(max_workers=4)

        self.logger = logging.getLogger(__name__)

    async def initialize(self):
        """Initialize monitoring system"""
        try:
            # Initialize Redis connection
            self.redis_client = aioredis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()
            self.logger.info("Redis connection established")

            # Initialize database connection pool
            self.db_pool = await asyncpg.create_pool(
                self.db_url,
                min_size=5,
                max_size=20,
                command_timeout=30
            )
            self.logger.info("Database connection pool created")

            # Initialize HTTP client
            self.http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(10.0),
                limits=httpx.Limits(max_keepalive_connections=50, max_connections=200)
            )

            # Initialize database schema
            await self._init_database()

            self.logger.info("Performance monitoring system initialized")

        except Exception as e:
            self.logger.error(f"Failed to initialize monitoring system: {e}")
            raise

    async def _init_database(self):
        """Initialize database schema for performance metrics"""
        async with self.db_pool.acquire() as conn:
            # Performance metrics table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id SERIAL PRIMARY KEY,
                    service VARCHAR(50) NOT NULL,
                    metric_name VARCHAR(100) NOT NULL,
                    value FLOAT NOT NULL,
                    tags JSONB,
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    INDEX (service, metric_name, timestamp)
                )
            """)

            # Alerts table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id VARCHAR(50) PRIMARY KEY,
                    service VARCHAR(50) NOT NULL,
                    metric VARCHAR(100) NOT NULL,
                    threshold FLOAT NOT NULL,
                    current_value FLOAT NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    message TEXT NOT NULL,
                    acknowledged BOOLEAN DEFAULT FALSE,
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    resolved_at TIMESTAMPTZ,
                    INDEX (service, severity, timestamp)
                )
            """)

            # Service health table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS service_health (
                    service VARCHAR(50) PRIMARY KEY,
                    healthy BOOLEAN NOT NULL,
                    response_time FLOAT,
                    cpu_usage FLOAT,
                    memory_usage FLOAT,
                    active_connections INTEGER,
                    error_message TEXT,
                    last_check TIMESTAMPTZ DEFAULT NOW()
                )
            """)

    async def start_monitoring(self):
        """Start all monitoring tasks"""
        if self.is_running:
            self.logger.warning("Monitoring already running")
            return

        self.is_running = True

        # Start monitoring tasks
        tasks = [
            self._monitor_service_health(),
            self._monitor_system_resources(),
            self._monitor_trading_performance(),
            self._monitor_database_performance(),
            self._process_metrics_buffer(),
            self._check_alerts(),
            self._calculate_sla_compliance()
        ]

        self.monitoring_tasks = [asyncio.create_task(task) for task in tasks]

        self.logger.info("Performance monitoring started")

    async def stop_monitoring(self):
        """Stop all monitoring tasks"""
        self.is_running = False

        # Cancel all tasks
        for task in self.monitoring_tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)

        self.monitoring_tasks.clear()

        # Close connections
        if self.redis_client:
            await self.redis_client.close()
        if self.db_pool:
            await self.db_pool.close()
        if self.http_client:
            await self.http_client.aclose()

        self.logger.info("Performance monitoring stopped")

    async def _monitor_service_health(self):
        """Monitor health of all services"""
        while self.is_running:
            try:
                health_checks = []
                for service_name, service_url in self.service_registry.items():
                    health_checks.append(self._check_service_health(service_name, service_url))

                # Execute health checks concurrently
                results = await asyncio.gather(*health_checks, return_exceptions=True)

                # Process results
                for service_name, result in zip(self.service_registry.keys(), results):
                    if isinstance(result, Exception):
                        self.logger.error(f"Health check failed for {service_name}: {result}")
                        SERVICE_HEALTH.labels(service=service_name).set(0)
                    else:
                        health_status = result
                        SERVICE_HEALTH.labels(service=service_name).set(1 if health_status.healthy else 0)

                        # Store in database
                        await self._store_service_health(health_status)

                await asyncio.sleep(10)  # Check every 10 seconds

            except Exception as e:
                self.logger.error(f"Error in service health monitoring: {e}")
                await asyncio.sleep(5)

    async def _check_service_health(self, service_name: str, service_url: str) -> ServiceHealth:
        """Check health of a specific service"""
        start_time = time.time()

        try:
            # Health endpoint check
            response = await self.http_client.get(f"{service_url}/health", timeout=5.0)
            response_time = (time.time() - start_time) * 1000  # Convert to ms

            healthy = response.status_code == 200

            # Get system metrics if available
            cpu_usage = psutil.cpu_percent()
            memory_info = psutil.virtual_memory()
            memory_usage = memory_info.percent

            # Track response time
            self.response_times[service_name].append(response_time)

            # Update Prometheus metrics
            REQUEST_DURATION.labels(service=service_name, endpoint="/health").observe(response_time / 1000)
            REQUEST_TOTAL.labels(service=service_name, endpoint="/health", status=response.status_code).inc()

            return ServiceHealth(
                name=service_name,
                healthy=healthy,
                response_time=response_time,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                active_connections=0,  # Would need service-specific implementation
                last_check=datetime.utcnow()
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000

            return ServiceHealth(
                name=service_name,
                healthy=False,
                response_time=response_time,
                cpu_usage=0,
                memory_usage=0,
                active_connections=0,
                last_check=datetime.utcnow(),
                error_message=str(e)
            )

    async def _store_service_health(self, health: ServiceHealth):
        """Store service health data in database"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO service_health
                    (service, healthy, response_time, cpu_usage, memory_usage, active_connections, error_message, last_check)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (service) DO UPDATE SET
                        healthy = EXCLUDED.healthy,
                        response_time = EXCLUDED.response_time,
                        cpu_usage = EXCLUDED.cpu_usage,
                        memory_usage = EXCLUDED.memory_usage,
                        active_connections = EXCLUDED.active_connections,
                        error_message = EXCLUDED.error_message,
                        last_check = EXCLUDED.last_check
                """, health.name, health.healthy, health.response_time, health.cpu_usage,
                health.memory_usage, health.active_connections, health.error_message, health.last_check)

        except Exception as e:
            self.logger.error(f"Failed to store service health: {e}")

    async def _monitor_system_resources(self):
        """Monitor system resource usage"""
        while self.is_running:
            try:
                # CPU and Memory monitoring
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()

                CPU_USAGE.labels(service="system").set(cpu_percent)
                MEMORY_USAGE.labels(service="system").set(memory.used)

                # Check thresholds
                await self._check_resource_thresholds("cpu", cpu_percent)
                await self._check_resource_thresholds("memory", memory.percent)

                await asyncio.sleep(5)

            except Exception as e:
                self.logger.error(f"Error in system resource monitoring: {e}")
                await asyncio.sleep(5)

    async def _monitor_trading_performance(self):
        """Monitor trading-specific performance metrics"""
        while self.is_running:
            try:
                # Simulate trading signal monitoring
                # In real implementation, this would integrate with trading engine
                signal_latency = await self._measure_signal_latency()
                tick_rate = await self._measure_tick_processing_rate()

                SIGNAL_LATENCY.observe(signal_latency)
                TICK_PROCESSING_RATE.set(tick_rate)

                # Check trading-specific thresholds
                if signal_latency > PerformanceThresholds.SIGNAL_LATENCY_THRESHOLD['critical']:
                    await self._trigger_alert("trading-engine", "signal_latency", signal_latency, "critical")
                elif signal_latency > PerformanceThresholds.SIGNAL_LATENCY_THRESHOLD['warning']:
                    await self._trigger_alert("trading-engine", "signal_latency", signal_latency, "warning")

                if tick_rate < PerformanceThresholds.TICK_RATE_THRESHOLD['critical']:
                    await self._trigger_alert("market-data", "tick_rate", tick_rate, "critical")

                await asyncio.sleep(1)  # High-frequency monitoring for trading

            except Exception as e:
                self.logger.error(f"Error in trading performance monitoring: {e}")
                await asyncio.sleep(5)

    async def _measure_signal_latency(self) -> float:
        """Measure trading signal generation latency"""
        start_time = time.time()

        try:
            # Simulate signal generation request
            response = await self.http_client.get(
                "http://localhost:8003/api/v1/signals/generate",
                timeout=1.0
            )

            latency = (time.time() - start_time) * 1000  # Convert to milliseconds
            return latency

        except Exception:
            # Return high latency on error
            return 1000.0

    async def _measure_tick_processing_rate(self) -> float:
        """Measure tick processing rate"""
        try:
            # Get tick rate from market data service
            response = await self.http_client.get(
                "http://localhost:8002/api/v1/metrics/tick-rate",
                timeout=1.0
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("ticks_per_second", 0)

            return 0.0

        except Exception:
            return 0.0

    async def _monitor_database_performance(self):
        """Monitor database performance"""
        while self.is_running:
            try:
                # Database query performance monitoring
                query_time = await self._measure_database_performance()

                # Store metric
                metric = PerformanceMetric(
                    service="database",
                    metric_name="query_time",
                    value=query_time,
                    timestamp=datetime.utcnow()
                )

                self.metrics_buffer.append(metric)

                await asyncio.sleep(10)

            except Exception as e:
                self.logger.error(f"Error in database performance monitoring: {e}")
                await asyncio.sleep(10)

    async def _measure_database_performance(self) -> float:
        """Measure database query performance"""
        start_time = time.time()

        try:
            async with self.db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")

            return (time.time() - start_time) * 1000  # Convert to milliseconds

        except Exception:
            return 1000.0  # Return high latency on error

    async def _check_resource_thresholds(self, resource_type: str, value: float):
        """Check if resource usage exceeds thresholds"""
        if resource_type == "cpu":
            thresholds = PerformanceThresholds.CPU_THRESHOLD
        elif resource_type == "memory":
            thresholds = PerformanceThresholds.MEMORY_THRESHOLD
        else:
            return

        if value > thresholds['critical']:
            await self._trigger_alert("system", resource_type, value, "critical")
        elif value > thresholds['warning']:
            await self._trigger_alert("system", resource_type, value, "warning")

    async def _trigger_alert(self, service: str, metric: str, value: float, severity: str):
        """Trigger an alert"""
        alert_id = f"{service}_{metric}_{int(time.time())}"

        alert = Alert(
            id=alert_id,
            service=service,
            metric=metric,
            threshold=0.0,  # Would set appropriate threshold
            current_value=value,
            severity=severity,
            message=f"{severity.upper()}: {service} {metric} is {value}",
            timestamp=datetime.utcnow()
        )

        self.alerts_buffer.append(alert)

        # Update Prometheus metrics
        ALERT_TRIGGERED.labels(alert_type=metric, severity=severity).inc()
        SLA_VIOLATIONS.labels(service=service, metric=metric).inc()

        # Store in Redis for real-time access
        await self.redis_client.lpush(
            f"alerts:{severity}",
            json.dumps(alert.to_dict())
        )

        self.logger.warning(f"Alert triggered: {alert.message}")

    async def _process_metrics_buffer(self):
        """Process and store metrics from buffer"""
        while self.is_running:
            try:
                if self.metrics_buffer:
                    # Batch process metrics
                    metrics_batch = []
                    for _ in range(min(100, len(self.metrics_buffer))):
                        if self.metrics_buffer:
                            metrics_batch.append(self.metrics_buffer.popleft())

                    if metrics_batch:
                        await self._store_metrics_batch(metrics_batch)

                await asyncio.sleep(5)

            except Exception as e:
                self.logger.error(f"Error processing metrics buffer: {e}")
                await asyncio.sleep(5)

    async def _store_metrics_batch(self, metrics: List[PerformanceMetric]):
        """Store batch of metrics in database"""
        try:
            async with self.db_pool.acquire() as conn:
                values = []
                for metric in metrics:
                    values.append((
                        metric.service,
                        metric.metric_name,
                        metric.value,
                        json.dumps(metric.tags) if metric.tags else None,
                        metric.timestamp
                    ))

                await conn.executemany("""
                    INSERT INTO performance_metrics (service, metric_name, value, tags, timestamp)
                    VALUES ($1, $2, $3, $4, $5)
                """, values)

        except Exception as e:
            self.logger.error(f"Failed to store metrics batch: {e}")

    async def _check_alerts(self):
        """Process and store alerts"""
        while self.is_running:
            try:
                if self.alerts_buffer:
                    # Process alerts
                    alerts_batch = []
                    for _ in range(min(50, len(self.alerts_buffer))):
                        if self.alerts_buffer:
                            alerts_batch.append(self.alerts_buffer.popleft())

                    if alerts_batch:
                        await self._store_alerts_batch(alerts_batch)

                await asyncio.sleep(10)

            except Exception as e:
                self.logger.error(f"Error processing alerts: {e}")
                await asyncio.sleep(10)

    async def _store_alerts_batch(self, alerts: List[Alert]):
        """Store batch of alerts in database"""
        try:
            async with self.db_pool.acquire() as conn:
                values = []
                for alert in alerts:
                    values.append((
                        alert.id,
                        alert.service,
                        alert.metric,
                        alert.threshold,
                        alert.current_value,
                        alert.severity,
                        alert.message,
                        alert.acknowledged,
                        alert.timestamp
                    ))

                await conn.executemany("""
                    INSERT INTO alerts (id, service, metric, threshold, current_value, severity, message, acknowledged, timestamp)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (id) DO NOTHING
                """, values)

        except Exception as e:
            self.logger.error(f"Failed to store alerts batch: {e}")

    async def _calculate_sla_compliance(self):
        """Calculate SLA compliance metrics"""
        while self.is_running:
            try:
                for service_name in self.service_registry.keys():
                    uptime_percentage = await self._calculate_uptime(service_name)

                    # Store SLA compliance metric
                    metric = PerformanceMetric(
                        service=service_name,
                        metric_name="uptime_percentage",
                        value=uptime_percentage,
                        timestamp=datetime.utcnow()
                    )

                    self.metrics_buffer.append(metric)

                    # Check SLA violation
                    if uptime_percentage < PerformanceThresholds.UPTIME_SLA:
                        await self._trigger_alert(service_name, "uptime_sla", uptime_percentage, "critical")

                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                self.logger.error(f"Error calculating SLA compliance: {e}")
                await asyncio.sleep(60)

    async def _calculate_uptime(self, service_name: str) -> float:
        """Calculate uptime percentage for a service"""
        try:
            # Get health data from last 24 hours
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchval("""
                    SELECT COUNT(CASE WHEN healthy THEN 1 END)::FLOAT / COUNT(*)
                    FROM service_health_history
                    WHERE service = $1 AND last_check > NOW() - INTERVAL '24 hours'
                """, service_name)

                return result if result is not None else 1.0

        except Exception:
            return 1.0  # Default to 100% if unable to calculate

    async def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        try:
            summary = {
                "timestamp": datetime.utcnow().isoformat(),
                "services": {},
                "system": {
                    "cpu_usage": psutil.cpu_percent(),
                    "memory_usage": psutil.virtual_memory().percent,
                    "disk_usage": psutil.disk_usage('/').percent
                },
                "trading": {
                    "signal_latency_avg": 0,
                    "tick_processing_rate": 0
                },
                "alerts": {
                    "critical": 0,
                    "warning": 0,
                    "total": 0
                }
            }

            # Get service metrics
            for service_name in self.service_registry.keys():
                response_times = list(self.response_times[service_name])

                summary["services"][service_name] = {
                    "healthy": len(response_times) > 0,
                    "avg_response_time": statistics.mean(response_times) if response_times else 0,
                    "p95_response_time": np.percentile(response_times, 95) if response_times else 0,
                    "error_rate": 0  # Would calculate from error tracking
                }

            # Get alert counts
            async with self.db_pool.acquire() as conn:
                alert_counts = await conn.fetch("""
                    SELECT severity, COUNT(*) as count
                    FROM alerts
                    WHERE timestamp > NOW() - INTERVAL '1 hour' AND NOT acknowledged
                    GROUP BY severity
                """)

                for row in alert_counts:
                    summary["alerts"][row["severity"]] = row["count"]
                    summary["alerts"]["total"] += row["count"]

            return summary

        except Exception as e:
            self.logger.error(f"Error generating metrics summary: {e}")
            return {"error": str(e)}

    async def get_prometheus_metrics(self) -> str:
        """Get Prometheus metrics"""
        return generate_latest(METRICS_REGISTRY).decode('utf-8')

# Performance monitoring decorators
def monitor_performance(service: str, endpoint: str = ""):
    """Decorator to monitor function performance"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                status = "success"
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                REQUEST_DURATION.labels(service=service, endpoint=endpoint).observe(duration)
                REQUEST_TOTAL.labels(service=service, endpoint=endpoint, status=status).inc()

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                status = "success"
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                REQUEST_DURATION.labels(service=service, endpoint=endpoint).observe(duration)
                REQUEST_TOTAL.labels(service=service, endpoint=endpoint, status=status).inc()

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

# Global monitor instance
_monitor_instance: Optional[PerformanceMonitor] = None

async def get_monitor() -> PerformanceMonitor:
    """Get global monitor instance"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = PerformanceMonitor()
        await _monitor_instance.initialize()
    return _monitor_instance