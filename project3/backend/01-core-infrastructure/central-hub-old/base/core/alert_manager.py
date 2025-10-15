"""
Alert Manager - Handles alerts from infrastructure and service failures
"""

import logging
import uuid
import time
from typing import Dict, List, Optional
from pathlib import Path
import yaml

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

from models.infrastructure_model import Alert, AlertSeverity

logger = logging.getLogger("central-hub.alert-manager")


class AlertManager:
    """Manages alerts for infrastructure and service failures"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or str(Path(__file__).parent.parent / "config" / "infrastructure.yaml")
        self.alerts: Dict[str, Alert] = {}  # Active alerts by component name
        self.alert_history: List[Alert] = []  # Historical alerts
        self.config = {}
        self.max_history = 100

    async def initialize(self):
        """Load alert configuration"""
        logger.info("🔧 Initializing Alert Manager...")

        try:
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)
                self.config = config_data.get('alerts', {})

            logger.info(f"✅ Alert Manager initialized (enabled: {self.config.get('enabled', True)})")

        except Exception as e:
            logger.error(f"❌ Failed to load alert config: {e}")
            self.config = {'enabled': True, 'channels': []}

    async def trigger_alert(
        self,
        component: str,
        component_type: str,
        status: str,
        critical: bool = False,
        details: Optional[Dict] = None
    ):
        """
        Trigger an alert for component failure

        Args:
            component: Component name
            component_type: 'infrastructure' or 'service'
            status: Current status
            critical: Whether this is a critical component
            details: Additional details
        """
        if not self.config.get('enabled', True):
            return

        # Determine severity
        if status == 'recovered':
            severity = AlertSeverity.INFO
            message = self._format_recovery_message(component, component_type)
        else:
            severity = AlertSeverity.CRITICAL if critical else AlertSeverity.WARNING
            message = self._format_failure_message(component, component_type, critical)

        # Create alert
        alert = Alert(
            id=str(uuid.uuid4()),
            severity=severity,
            component=component,
            component_type=component_type,
            message=message,
            details=details or {},
            timestamp=int(time.time() * 1000)
        )

        # Handle based on status
        if status == 'recovered':
            await self._handle_recovery(component, alert)
        else:
            await self._handle_failure(component, alert)

    def _format_failure_message(self, component: str, component_type: str, critical: bool) -> str:
        """Format failure alert message"""
        level = "CRITICAL" if critical else "WARNING"

        if component_type == 'infrastructure':
            return f"[{level}] Infrastructure {component} is DOWN"
        else:
            return f"[{level}] Service {component} is DOWN"

    def _format_recovery_message(self, component: str, component_type: str) -> str:
        """Format recovery alert message"""
        if component_type == 'infrastructure':
            return f"[RECOVERY] Infrastructure {component} is now HEALTHY"
        else:
            return f"[RECOVERY] Service {component} is now HEALTHY"

    async def _handle_failure(self, component: str, alert: Alert):
        """Handle failure alert"""
        # Store active alert
        self.alerts[component] = alert

        # Add to history
        self.alert_history.append(alert)
        if len(self.alert_history) > self.max_history:
            self.alert_history.pop(0)

        # Send alert through configured channels
        await self._send_alert(alert)

    async def _handle_recovery(self, component: str, alert: Alert):
        """Handle recovery alert"""
        # Remove from active alerts
        if component in self.alerts:
            del self.alerts[component]

        # Add recovery to history
        self.alert_history.append(alert)
        if len(self.alert_history) > self.max_history:
            self.alert_history.pop(0)

        # Send recovery notification
        await self._send_alert(alert)

    async def _send_alert(self, alert: Alert):
        """Send alert through configured channels"""
        channels = self.config.get('channels', [])

        for channel in channels:
            if not channel.get('enabled', True):
                continue

            channel_type = channel.get('type')

            if channel_type == 'log':
                await self._send_to_log(alert, channel)
            elif channel_type == 'console':
                await self._send_to_console(alert)
            # Future: webhook, email, telegram, etc.

    async def _send_to_log(self, alert: Alert, channel: Dict):
        """Send alert to log"""
        level = channel.get('level', 'error')

        if alert.severity == AlertSeverity.CRITICAL:
            logger.error(f"🚨 {alert.message} | Component: {alert.component}")
        elif alert.severity == AlertSeverity.WARNING:
            logger.warning(f"⚠️ {alert.message} | Component: {alert.component}")
        else:
            logger.info(f"ℹ️ {alert.message} | Component: {alert.component}")

    async def _send_to_console(self, alert: Alert):
        """Send alert to console"""
        symbols = {
            AlertSeverity.CRITICAL: "🔴",
            AlertSeverity.WARNING: "🟡",
            AlertSeverity.INFO: "🟢"
        }

        symbol = symbols.get(alert.severity, "ℹ️")
        print(f"\n{symbol} ALERT: {alert.message}")
        print(f"   Component: {alert.component} ({alert.component_type})")
        print(f"   Time: {alert.timestamp}")
        if alert.details:
            print(f"   Details: {alert.details}\n")

    def get_active_alerts(self) -> List[Dict]:
        """Get all active alerts"""
        return [alert.to_dict() for alert in self.alerts.values()]

    def get_alert_history(self, limit: int = 50) -> List[Dict]:
        """Get alert history"""
        return [alert.to_dict() for alert in self.alert_history[-limit:]]

    def acknowledge_alert(self, component: str) -> bool:
        """Acknowledge an alert"""
        if component in self.alerts:
            self.alerts[component].acknowledged = True
            logger.info(f"✅ Alert acknowledged for: {component}")
            return True
        return False

    def get_alert_stats(self) -> Dict:
        """Get alert statistics"""
        total_active = len(self.alerts)
        critical = sum(1 for a in self.alerts.values() if a.severity == AlertSeverity.CRITICAL)
        warnings = sum(1 for a in self.alerts.values() if a.severity == AlertSeverity.WARNING)

        return {
            'active_alerts': total_active,
            'critical': critical,
            'warnings': warnings,
            'history_count': len(self.alert_history)
        }
