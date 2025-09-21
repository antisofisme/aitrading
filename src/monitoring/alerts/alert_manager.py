"""
Advanced Alert Management System
Handles critical threshold monitoring, escalation, and notification routing
"""

import asyncio
import logging
import json
import smtplib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from enum import Enum
import aioredis
import asyncpg
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import boto3
from slack_sdk.web.async_client import AsyncWebClient
import threading
from concurrent.futures import ThreadPoolExecutor

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class AlertStatus(Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"

@dataclass
class AlertRule:
    """Alert rule definition"""
    id: str
    name: str
    service: str
    metric: str
    condition: str  # e.g., ">", "<", ">=", "<=", "=="
    threshold: float
    severity: AlertSeverity
    duration: int  # seconds the condition must persist
    enabled: bool = True
    tags: Dict[str, str] = None
    description: str = ""
    runbook_url: str = ""

@dataclass
class Alert:
    """Alert instance"""
    id: str
    rule_id: str
    service: str
    metric: str
    current_value: float
    threshold: float
    severity: AlertSeverity
    status: AlertStatus
    message: str
    description: str
    tags: Dict[str, str]
    created_at: datetime
    updated_at: datetime
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    escalated: bool = False
    escalation_level: int = 0
    notification_sent: bool = False

    def to_dict(self) -> Dict:
        data = asdict(self)
        data['severity'] = self.severity.value
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        if self.acknowledged_at:
            data['acknowledged_at'] = self.acknowledged_at.isoformat()
        if self.resolved_at:
            data['resolved_at'] = self.resolved_at.isoformat()
        return data

@dataclass
class NotificationChannel:
    """Notification channel configuration"""
    id: str
    type: str  # email, slack, webhook, sms, pagerduty
    name: str
    config: Dict[str, Any]
    enabled: bool = True
    severity_filter: List[AlertSeverity] = None

@dataclass
class EscalationPolicy:
    """Alert escalation policy"""
    id: str
    name: str
    service: str
    rules: List[Dict[str, Any]]  # [{"delay": 300, "channels": ["email"]}, {"delay": 900, "channels": ["slack", "pagerduty"]}]
    enabled: bool = True

class AlertManager:
    """Advanced Alert Management System"""

    def __init__(self,
                 redis_url: str = "redis://localhost:6379",
                 db_url: str = "postgresql://user:pass@localhost/aitrading"):
        self.redis_url = redis_url
        self.db_url = db_url

        # Connections
        self.redis_client: Optional[aioredis.Redis] = None
        self.db_pool: Optional[asyncpg.Pool] = None
        self.http_client: Optional[httpx.AsyncClient] = None

        # Alert state
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_rules: Dict[str, AlertRule] = {}
        self.notification_channels: Dict[str, NotificationChannel] = {}
        self.escalation_policies: Dict[str, EscalationPolicy] = {}

        # Alert processing
        self.alert_queue: asyncio.Queue = asyncio.Queue()
        self.notification_queue: asyncio.Queue = asyncio.Queue()
        self.suppression_rules: Dict[str, Dict] = {}

        # Metrics tracking
        self.alert_history: deque = deque(maxlen=10000)
        self.metric_values: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.condition_timers: Dict[str, datetime] = {}

        # Configuration
        self.default_thresholds = {
            # Response time thresholds (ms)
            "response_time": {
                "gateway": {"warning": 100, "critical": 200},
                "business-api": {"warning": 10, "critical": 15},
                "trading-engine": {"warning": 250, "critical": 500},
                "market-data": {"warning": 50, "critical": 100},
                "database": {"warning": 50, "critical": 100}
            },
            # System resource thresholds (%)
            "cpu_usage": {"warning": 70, "critical": 85},
            "memory_usage": {"warning": 80, "critical": 90},
            "disk_usage": {"warning": 85, "critical": 95},
            # Trading-specific thresholds
            "signal_latency": {"warning": 400, "critical": 500},  # ms
            "tick_processing_rate": {"warning": 15, "critical": 10},  # ticks/sec
            "model_accuracy": {"warning": 0.75, "critical": 0.65},  # accuracy
            "uptime": {"critical": 0.999}  # 99.9% uptime SLA
        }

        # Threading for notification processing
        self.executor = ThreadPoolExecutor(max_workers=10)

        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self.processing_tasks: List[asyncio.Task] = []

    async def initialize(self):
        """Initialize alert management system"""
        try:
            # Initialize Redis connection
            self.redis_client = aioredis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()

            # Initialize database connection
            self.db_pool = await asyncpg.create_pool(
                self.db_url,
                min_size=3,
                max_size=15,
                command_timeout=30
            )

            # Initialize HTTP client
            self.http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
            )

            # Initialize database schema
            await self._init_database()

            # Load configuration
            await self._load_configuration()

            # Initialize default alert rules
            await self._create_default_alert_rules()

            self.logger.info("Alert Manager initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize Alert Manager: {e}")
            raise

    async def _init_database(self):
        """Initialize database schema"""
        async with self.db_pool.acquire() as conn:
            # Alert rules table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS alert_rules (
                    id VARCHAR(100) PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    service VARCHAR(100) NOT NULL,
                    metric VARCHAR(100) NOT NULL,
                    condition VARCHAR(10) NOT NULL,
                    threshold FLOAT NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    duration INTEGER NOT NULL,
                    enabled BOOLEAN DEFAULT TRUE,
                    tags JSONB,
                    description TEXT,
                    runbook_url TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)

            # Alerts table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id VARCHAR(100) PRIMARY KEY,
                    rule_id VARCHAR(100) NOT NULL,
                    service VARCHAR(100) NOT NULL,
                    metric VARCHAR(100) NOT NULL,
                    current_value FLOAT NOT NULL,
                    threshold FLOAT NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    message TEXT NOT NULL,
                    description TEXT,
                    tags JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    acknowledged_at TIMESTAMPTZ,
                    acknowledged_by VARCHAR(100),
                    resolved_at TIMESTAMPTZ,
                    escalated BOOLEAN DEFAULT FALSE,
                    escalation_level INTEGER DEFAULT 0,
                    notification_sent BOOLEAN DEFAULT FALSE,
                    INDEX (service, severity, status),
                    INDEX (created_at, status),
                    FOREIGN KEY (rule_id) REFERENCES alert_rules(id)
                )
            """)

            # Notification channels table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS notification_channels (
                    id VARCHAR(100) PRIMARY KEY,
                    type VARCHAR(50) NOT NULL,
                    name VARCHAR(200) NOT NULL,
                    config JSONB NOT NULL,
                    enabled BOOLEAN DEFAULT TRUE,
                    severity_filter JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)

            # Escalation policies table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS escalation_policies (
                    id VARCHAR(100) PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    service VARCHAR(100) NOT NULL,
                    rules JSONB NOT NULL,
                    enabled BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)

            # Alert notifications table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS alert_notifications (
                    id SERIAL PRIMARY KEY,
                    alert_id VARCHAR(100) NOT NULL,
                    channel_id VARCHAR(100) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    attempt_count INTEGER DEFAULT 0,
                    last_attempt TIMESTAMPTZ,
                    error_message TEXT,
                    sent_at TIMESTAMPTZ,
                    FOREIGN KEY (alert_id) REFERENCES alerts(id)
                )
            """)

    async def _load_configuration(self):
        """Load alert configuration from database"""
        try:
            async with self.db_pool.acquire() as conn:
                # Load alert rules
                rules = await conn.fetch("SELECT * FROM alert_rules WHERE enabled = TRUE")
                for rule_data in rules:
                    rule = AlertRule(
                        id=rule_data['id'],
                        name=rule_data['name'],
                        service=rule_data['service'],
                        metric=rule_data['metric'],
                        condition=rule_data['condition'],
                        threshold=rule_data['threshold'],
                        severity=AlertSeverity(rule_data['severity']),
                        duration=rule_data['duration'],
                        enabled=rule_data['enabled'],
                        tags=rule_data['tags'],
                        description=rule_data['description'],
                        runbook_url=rule_data['runbook_url']
                    )
                    self.alert_rules[rule.id] = rule

                # Load notification channels
                channels = await conn.fetch("SELECT * FROM notification_channels WHERE enabled = TRUE")
                for channel_data in channels:
                    severity_filter = None
                    if channel_data['severity_filter']:
                        severity_filter = [AlertSeverity(s) for s in channel_data['severity_filter']]

                    channel = NotificationChannel(
                        id=channel_data['id'],
                        type=channel_data['type'],
                        name=channel_data['name'],
                        config=channel_data['config'],
                        enabled=channel_data['enabled'],
                        severity_filter=severity_filter
                    )
                    self.notification_channels[channel.id] = channel

                # Load escalation policies
                policies = await conn.fetch("SELECT * FROM escalation_policies WHERE enabled = TRUE")
                for policy_data in policies:
                    policy = EscalationPolicy(
                        id=policy_data['id'],
                        name=policy_data['name'],
                        service=policy_data['service'],
                        rules=policy_data['rules'],
                        enabled=policy_data['enabled']
                    )
                    self.escalation_policies[policy.id] = policy

                self.logger.info(f"Loaded {len(self.alert_rules)} alert rules, "
                               f"{len(self.notification_channels)} channels, "
                               f"{len(self.escalation_policies)} escalation policies")

        except Exception as e:
            self.logger.error(f"Failed to load alert configuration: {e}")

    async def _create_default_alert_rules(self):
        """Create default alert rules if none exist"""
        if self.alert_rules:
            return  # Rules already exist

        default_rules = [
            # Response time alerts
            AlertRule(
                id="gateway_response_time_critical",
                name="Gateway Response Time Critical",
                service="gateway",
                metric="response_time",
                condition=">",
                threshold=200,
                severity=AlertSeverity.CRITICAL,
                duration=60,
                description="Gateway response time exceeds 200ms"
            ),
            AlertRule(
                id="business_api_response_time_critical",
                name="Business API Response Time Critical",
                service="business-api",
                metric="response_time",
                condition=">",
                threshold=15,
                severity=AlertSeverity.CRITICAL,
                duration=30,
                description="Business API response time exceeds 15ms"
            ),
            AlertRule(
                id="trading_signal_latency_critical",
                name="Trading Signal Latency Critical",
                service="trading-engine",
                metric="signal_latency",
                condition=">",
                threshold=500,
                severity=AlertSeverity.CRITICAL,
                duration=30,
                description="Trading signal latency exceeds 500ms"
            ),
            # System resource alerts
            AlertRule(
                id="cpu_usage_critical",
                name="CPU Usage Critical",
                service="system",
                metric="cpu_usage",
                condition=">",
                threshold=85,
                severity=AlertSeverity.CRITICAL,
                duration=300,
                description="CPU usage exceeds 85%"
            ),
            AlertRule(
                id="memory_usage_critical",
                name="Memory Usage Critical",
                service="system",
                metric="memory_usage",
                condition=">",
                threshold=90,
                severity=AlertSeverity.CRITICAL,
                duration=300,
                description="Memory usage exceeds 90%"
            ),
            # AI Model alerts
            AlertRule(
                id="model_accuracy_critical",
                name="Model Accuracy Critical",
                service="ml-models",
                metric="model_accuracy",
                condition="<",
                threshold=0.65,
                severity=AlertSeverity.CRITICAL,
                duration=600,
                description="Model accuracy below 65%"
            ),
            # Service health alerts
            AlertRule(
                id="service_down_critical",
                name="Service Down Critical",
                service="*",
                metric="service_health",
                condition="==",
                threshold=0,
                severity=AlertSeverity.EMERGENCY,
                duration=30,
                description="Service is down"
            )
        ]

        # Store default rules
        for rule in default_rules:
            await self.create_alert_rule(rule)

    async def create_alert_rule(self, rule: AlertRule) -> bool:
        """Create new alert rule"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO alert_rules
                    (id, name, service, metric, condition, threshold, severity, duration,
                     enabled, tags, description, runbook_url)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        service = EXCLUDED.service,
                        metric = EXCLUDED.metric,
                        condition = EXCLUDED.condition,
                        threshold = EXCLUDED.threshold,
                        severity = EXCLUDED.severity,
                        duration = EXCLUDED.duration,
                        enabled = EXCLUDED.enabled,
                        tags = EXCLUDED.tags,
                        description = EXCLUDED.description,
                        runbook_url = EXCLUDED.runbook_url,
                        updated_at = NOW()
                """, rule.id, rule.name, rule.service, rule.metric, rule.condition,
                rule.threshold, rule.severity.value, rule.duration, rule.enabled,
                json.dumps(rule.tags) if rule.tags else None, rule.description, rule.runbook_url)

            self.alert_rules[rule.id] = rule
            self.logger.info(f"Created alert rule: {rule.name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create alert rule {rule.id}: {e}")
            return False

    async def process_metric(self, service: str, metric: str, value: float, tags: Dict[str, str] = None):
        """Process incoming metric and check alert rules"""
        try:
            # Store metric value
            metric_key = f"{service}:{metric}"
            self.metric_values[metric_key].append((time.time(), value))

            # Cache in Redis
            await self.redis_client.hset(
                f"metrics:{service}",
                metric,
                json.dumps({
                    "value": value,
                    "timestamp": time.time(),
                    "tags": tags
                })
            )

            # Check applicable alert rules
            applicable_rules = [
                rule for rule in self.alert_rules.values()
                if rule.enabled and (rule.service == service or rule.service == "*") and rule.metric == metric
            ]

            for rule in applicable_rules:
                await self._check_alert_condition(rule, service, metric, value, tags)

        except Exception as e:
            self.logger.error(f"Error processing metric {service}:{metric}: {e}")

    async def _check_alert_condition(self, rule: AlertRule, service: str, metric: str, value: float, tags: Dict[str, str]):
        """Check if alert condition is met"""
        try:
            condition_met = False

            # Evaluate condition
            if rule.condition == ">":
                condition_met = value > rule.threshold
            elif rule.condition == ">=":
                condition_met = value >= rule.threshold
            elif rule.condition == "<":
                condition_met = value < rule.threshold
            elif rule.condition == "<=":
                condition_met = value <= rule.threshold
            elif rule.condition == "==":
                condition_met = value == rule.threshold
            elif rule.condition == "!=":
                condition_met = value != rule.threshold

            condition_key = f"{rule.id}:{service}:{metric}"
            current_time = datetime.utcnow()

            if condition_met:
                # Check if this is a new condition violation
                if condition_key not in self.condition_timers:
                    self.condition_timers[condition_key] = current_time
                    return

                # Check if condition has persisted long enough
                duration_met = (current_time - self.condition_timers[condition_key]).total_seconds() >= rule.duration

                if duration_met:
                    # Create alert
                    await self._create_alert(rule, service, metric, value, tags)
                    # Remove from condition timers
                    del self.condition_timers[condition_key]
            else:
                # Condition not met, remove from timers
                if condition_key in self.condition_timers:
                    del self.condition_timers[condition_key]

                # Check if we should resolve existing alert
                await self._check_alert_resolution(rule, service, metric, value)

        except Exception as e:
            self.logger.error(f"Error checking alert condition for rule {rule.id}: {e}")

    async def _create_alert(self, rule: AlertRule, service: str, metric: str, value: float, tags: Dict[str, str]):
        """Create new alert"""
        try:
            alert_id = f"{rule.id}_{service}_{metric}_{int(time.time())}"

            # Check if similar alert already exists
            existing_alert = await self._find_existing_alert(rule.id, service, metric)
            if existing_alert and existing_alert.status == AlertStatus.ACTIVE:
                # Update existing alert
                existing_alert.current_value = value
                existing_alert.updated_at = datetime.utcnow()
                await self._update_alert(existing_alert)
                return

            # Create new alert
            alert = Alert(
                id=alert_id,
                rule_id=rule.id,
                service=service,
                metric=metric,
                current_value=value,
                threshold=rule.threshold,
                severity=rule.severity,
                status=AlertStatus.ACTIVE,
                message=f"{rule.severity.value.upper()}: {service} {metric} is {value} (threshold: {rule.threshold})",
                description=rule.description,
                tags=tags or {},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            # Store alert
            await self._store_alert(alert)

            # Add to active alerts
            self.active_alerts[alert.id] = alert

            # Queue for notification
            await self.alert_queue.put(alert)

            self.logger.warning(f"Alert created: {alert.message}")

        except Exception as e:
            self.logger.error(f"Failed to create alert: {e}")

    async def _find_existing_alert(self, rule_id: str, service: str, metric: str) -> Optional[Alert]:
        """Find existing alert for the same rule/service/metric"""
        try:
            async with self.db_pool.acquire() as conn:
                alert_data = await conn.fetchrow("""
                    SELECT * FROM alerts
                    WHERE rule_id = $1 AND service = $2 AND metric = $3
                    AND status = 'active'
                    ORDER BY created_at DESC LIMIT 1
                """, rule_id, service, metric)

                if alert_data:
                    return Alert(
                        id=alert_data['id'],
                        rule_id=alert_data['rule_id'],
                        service=alert_data['service'],
                        metric=alert_data['metric'],
                        current_value=alert_data['current_value'],
                        threshold=alert_data['threshold'],
                        severity=AlertSeverity(alert_data['severity']),
                        status=AlertStatus(alert_data['status']),
                        message=alert_data['message'],
                        description=alert_data['description'],
                        tags=alert_data['tags'] or {},
                        created_at=alert_data['created_at'],
                        updated_at=alert_data['updated_at'],
                        acknowledged_at=alert_data['acknowledged_at'],
                        acknowledged_by=alert_data['acknowledged_by'],
                        resolved_at=alert_data['resolved_at'],
                        escalated=alert_data['escalated'],
                        escalation_level=alert_data['escalation_level'],
                        notification_sent=alert_data['notification_sent']
                    )

                return None

        except Exception as e:
            self.logger.error(f"Error finding existing alert: {e}")
            return None

    async def _store_alert(self, alert: Alert):
        """Store alert in database"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO alerts
                    (id, rule_id, service, metric, current_value, threshold, severity, status,
                     message, description, tags, created_at, updated_at, escalated,
                     escalation_level, notification_sent)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                """, alert.id, alert.rule_id, alert.service, alert.metric, alert.current_value,
                alert.threshold, alert.severity.value, alert.status.value, alert.message,
                alert.description, json.dumps(alert.tags), alert.created_at, alert.updated_at,
                alert.escalated, alert.escalation_level, alert.notification_sent)

        except Exception as e:
            self.logger.error(f"Failed to store alert: {e}")

    async def _update_alert(self, alert: Alert):
        """Update existing alert"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE alerts SET
                        current_value = $2,
                        status = $3,
                        message = $4,
                        updated_at = $5,
                        acknowledged_at = $6,
                        acknowledged_by = $7,
                        resolved_at = $8,
                        escalated = $9,
                        escalation_level = $10,
                        notification_sent = $11
                    WHERE id = $1
                """, alert.id, alert.current_value, alert.status.value, alert.message,
                alert.updated_at, alert.acknowledged_at, alert.acknowledged_by,
                alert.resolved_at, alert.escalated, alert.escalation_level, alert.notification_sent)

        except Exception as e:
            self.logger.error(f"Failed to update alert: {e}")

    async def _check_alert_resolution(self, rule: AlertRule, service: str, metric: str, value: float):
        """Check if alert should be resolved"""
        try:
            # Find active alerts for this rule/service/metric
            existing_alert = await self._find_existing_alert(rule.id, service, metric)

            if existing_alert and existing_alert.status == AlertStatus.ACTIVE:
                # Check if condition is no longer met
                condition_resolved = False

                if rule.condition == ">":
                    condition_resolved = value <= rule.threshold
                elif rule.condition == ">=":
                    condition_resolved = value < rule.threshold
                elif rule.condition == "<":
                    condition_resolved = value >= rule.threshold
                elif rule.condition == "<=":
                    condition_resolved = value > rule.threshold
                elif rule.condition == "==":
                    condition_resolved = value != rule.threshold
                elif rule.condition == "!=":
                    condition_resolved = value == rule.threshold

                if condition_resolved:
                    # Resolve alert
                    existing_alert.status = AlertStatus.RESOLVED
                    existing_alert.resolved_at = datetime.utcnow()
                    existing_alert.updated_at = datetime.utcnow()
                    existing_alert.message = f"RESOLVED: {existing_alert.message}"

                    await self._update_alert(existing_alert)

                    # Remove from active alerts
                    if existing_alert.id in self.active_alerts:
                        del self.active_alerts[existing_alert.id]

                    self.logger.info(f"Alert resolved: {existing_alert.id}")

        except Exception as e:
            self.logger.error(f"Error checking alert resolution: {e}")

    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert"""
        try:
            alert = self.active_alerts.get(alert_id)
            if not alert:
                # Try to get from database
                async with self.db_pool.acquire() as conn:
                    alert_data = await conn.fetchrow("SELECT * FROM alerts WHERE id = $1", alert_id)
                    if not alert_data:
                        return False

            # Update alert
            if alert:
                alert.status = AlertStatus.ACKNOWLEDGED
                alert.acknowledged_at = datetime.utcnow()
                alert.acknowledged_by = acknowledged_by
                alert.updated_at = datetime.utcnow()

                await self._update_alert(alert)

                self.logger.info(f"Alert acknowledged: {alert_id} by {acknowledged_by}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Failed to acknowledge alert {alert_id}: {e}")
            return False

    async def start_monitoring(self):
        """Start alert processing tasks"""
        if self.is_running:
            return

        self.is_running = True

        # Start processing tasks
        tasks = [
            self._process_alert_queue(),
            self._process_notification_queue(),
            self._check_escalations(),
            self._cleanup_old_alerts()
        ]

        self.processing_tasks = [asyncio.create_task(task) for task in tasks]

        self.logger.info("Alert Manager monitoring started")

    async def stop_monitoring(self):
        """Stop alert processing"""
        self.is_running = False

        # Cancel all tasks
        for task in self.processing_tasks:
            task.cancel()

        await asyncio.gather(*self.processing_tasks, return_exceptions=True)
        self.processing_tasks.clear()

        if self.redis_client:
            await self.redis_client.close()
        if self.db_pool:
            await self.db_pool.close()
        if self.http_client:
            await self.http_client.aclose()

        self.logger.info("Alert Manager monitoring stopped")

    async def _process_alert_queue(self):
        """Process alerts from queue"""
        while self.is_running:
            try:
                alert = await asyncio.wait_for(self.alert_queue.get(), timeout=1.0)

                # Queue for notification
                await self.notification_queue.put(alert)

                # Check for escalation policy
                escalation_policy = self._get_escalation_policy(alert.service)
                if escalation_policy:
                    # Schedule escalation
                    asyncio.create_task(self._schedule_escalation(alert, escalation_policy))

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error processing alert queue: {e}")
                await asyncio.sleep(1)

    async def _process_notification_queue(self):
        """Process notifications from queue"""
        while self.is_running:
            try:
                alert = await asyncio.wait_for(self.notification_queue.get(), timeout=1.0)

                # Send notifications
                await self._send_notifications(alert)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error processing notification queue: {e}")
                await asyncio.sleep(1)

    async def _send_notifications(self, alert: Alert):
        """Send notifications for alert"""
        try:
            # Get applicable notification channels
            channels = [
                channel for channel in self.notification_channels.values()
                if channel.enabled and (
                    not channel.severity_filter or
                    alert.severity in channel.severity_filter
                )
            ]

            notification_tasks = []
            for channel in channels:
                task = asyncio.create_task(self._send_notification(alert, channel))
                notification_tasks.append(task)

            # Wait for all notifications to complete
            results = await asyncio.gather(*notification_tasks, return_exceptions=True)

            # Update alert notification status
            alert.notification_sent = any(result is True for result in results if not isinstance(result, Exception))
            await self._update_alert(alert)

        except Exception as e:
            self.logger.error(f"Error sending notifications for alert {alert.id}: {e}")

    async def _send_notification(self, alert: Alert, channel: NotificationChannel) -> bool:
        """Send notification to specific channel"""
        try:
            if channel.type == "email":
                return await self._send_email_notification(alert, channel)
            elif channel.type == "slack":
                return await self._send_slack_notification(alert, channel)
            elif channel.type == "webhook":
                return await self._send_webhook_notification(alert, channel)
            else:
                self.logger.warning(f"Unsupported notification channel type: {channel.type}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to send notification via {channel.type}: {e}")
            return False

    async def _send_email_notification(self, alert: Alert, channel: NotificationChannel) -> bool:
        """Send email notification"""
        try:
            config = channel.config
            smtp_server = config.get("smtp_server", "localhost")
            smtp_port = config.get("smtp_port", 587)
            username = config.get("username")
            password = config.get("password")
            to_emails = config.get("to_emails", [])

            if not to_emails:
                return False

            # Create email
            msg = MIMEMultipart()
            msg["From"] = username
            msg["To"] = ", ".join(to_emails)
            msg["Subject"] = f"[{alert.severity.value.upper()}] {alert.service} Alert"

            body = f"""
Alert Details:
- Service: {alert.service}
- Metric: {alert.metric}
- Current Value: {alert.current_value}
- Threshold: {alert.threshold}
- Severity: {alert.severity.value.upper()}
- Message: {alert.message}
- Time: {alert.created_at.isoformat()}

Description: {alert.description}
            """

            msg.attach(MIMEText(body, "plain"))

            # Send email (run in thread pool to avoid blocking)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                self._send_email_sync,
                smtp_server, smtp_port, username, password, msg.as_string()
            )

            return True

        except Exception as e:
            self.logger.error(f"Failed to send email notification: {e}")
            return False

    def _send_email_sync(self, smtp_server: str, smtp_port: int, username: str, password: str, message: str):
        """Send email synchronously"""
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.send_message(message)

    async def _send_slack_notification(self, alert: Alert, channel: NotificationChannel) -> bool:
        """Send Slack notification"""
        try:
            config = channel.config
            webhook_url = config.get("webhook_url")

            if not webhook_url:
                return False

            # Create Slack message
            color = {
                AlertSeverity.INFO: "#36a64f",
                AlertSeverity.WARNING: "#ffcc00",
                AlertSeverity.CRITICAL: "#ff6600",
                AlertSeverity.EMERGENCY: "#ff0000"
            }.get(alert.severity, "#808080")

            payload = {
                "attachments": [{
                    "color": color,
                    "title": f"{alert.severity.value.upper()} Alert: {alert.service}",
                    "fields": [
                        {"title": "Service", "value": alert.service, "short": True},
                        {"title": "Metric", "value": alert.metric, "short": True},
                        {"title": "Current Value", "value": str(alert.current_value), "short": True},
                        {"title": "Threshold", "value": str(alert.threshold), "short": True},
                        {"title": "Message", "value": alert.message, "short": False}
                    ],
                    "timestamp": alert.created_at.timestamp()
                }]
            }

            # Send webhook
            response = await self.http_client.post(webhook_url, json=payload)
            return response.status_code == 200

        except Exception as e:
            self.logger.error(f"Failed to send Slack notification: {e}")
            return False

    async def _send_webhook_notification(self, alert: Alert, channel: NotificationChannel) -> bool:
        """Send webhook notification"""
        try:
            config = channel.config
            url = config.get("url")
            headers = config.get("headers", {})

            if not url:
                return False

            # Create webhook payload
            payload = alert.to_dict()

            # Send webhook
            response = await self.http_client.post(url, json=payload, headers=headers)
            return response.status_code < 400

        except Exception as e:
            self.logger.error(f"Failed to send webhook notification: {e}")
            return False

    def _get_escalation_policy(self, service: str) -> Optional[EscalationPolicy]:
        """Get escalation policy for service"""
        return next(
            (policy for policy in self.escalation_policies.values()
             if policy.service == service or policy.service == "*"),
            None
        )

    async def _schedule_escalation(self, alert: Alert, policy: EscalationPolicy):
        """Schedule alert escalation"""
        try:
            for i, rule in enumerate(policy.rules):
                delay = rule.get("delay", 300)  # Default 5 minutes

                # Wait for delay
                await asyncio.sleep(delay)

                # Check if alert is still active and not acknowledged
                current_alert = self.active_alerts.get(alert.id)
                if not current_alert or current_alert.status != AlertStatus.ACTIVE:
                    return  # Alert resolved or acknowledged

                # Escalate
                current_alert.escalated = True
                current_alert.escalation_level = i + 1
                await self._update_alert(current_alert)

                # Send escalation notifications
                channel_ids = rule.get("channels", [])
                for channel_id in channel_ids:
                    channel = self.notification_channels.get(channel_id)
                    if channel:
                        await self._send_notification(current_alert, channel)

                self.logger.warning(f"Alert escalated: {alert.id} to level {i + 1}")

        except Exception as e:
            self.logger.error(f"Error in alert escalation: {e}")

    async def _check_escalations(self):
        """Check for alerts that need escalation"""
        while self.is_running:
            try:
                # This is handled by _schedule_escalation, but could add additional logic here
                await asyncio.sleep(60)

            except Exception as e:
                self.logger.error(f"Error checking escalations: {e}")
                await asyncio.sleep(60)

    async def _cleanup_old_alerts(self):
        """Cleanup old resolved alerts"""
        while self.is_running:
            try:
                cutoff_date = datetime.utcnow() - timedelta(days=30)

                async with self.db_pool.acquire() as conn:
                    deleted = await conn.execute("""
                        DELETE FROM alerts
                        WHERE status = 'resolved' AND resolved_at < $1
                    """, cutoff_date)

                if deleted:
                    self.logger.info(f"Cleaned up {deleted} old alerts")

                await asyncio.sleep(86400)  # Daily cleanup

            except Exception as e:
                self.logger.error(f"Error during alert cleanup: {e}")
                await asyncio.sleep(3600)

    async def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary"""
        try:
            summary = {
                "total_active": len(self.active_alerts),
                "by_severity": {severity.value: 0 for severity in AlertSeverity},
                "by_service": defaultdict(int),
                "recent_alerts": []
            }

            # Count by severity and service
            for alert in self.active_alerts.values():
                summary["by_severity"][alert.severity.value] += 1
                summary["by_service"][alert.service] += 1

            # Get recent alerts from database
            async with self.db_pool.acquire() as conn:
                recent = await conn.fetch("""
                    SELECT id, service, metric, severity, status, message, created_at
                    FROM alerts
                    WHERE created_at > NOW() - INTERVAL '24 hours'
                    ORDER BY created_at DESC
                    LIMIT 20
                """)

                summary["recent_alerts"] = [
                    {
                        "id": row["id"],
                        "service": row["service"],
                        "metric": row["metric"],
                        "severity": row["severity"],
                        "status": row["status"],
                        "message": row["message"],
                        "created_at": row["created_at"].isoformat()
                    }
                    for row in recent
                ]

            return summary

        except Exception as e:
            self.logger.error(f"Error generating alert summary: {e}")
            return {"error": str(e)}

# Global alert manager instance
_alert_manager_instance: Optional[AlertManager] = None

async def get_alert_manager() -> AlertManager:
    """Get global alert manager instance"""
    global _alert_manager_instance
    if _alert_manager_instance is None:
        _alert_manager_instance = AlertManager()
        await _alert_manager_instance.initialize()
    return _alert_manager_instance