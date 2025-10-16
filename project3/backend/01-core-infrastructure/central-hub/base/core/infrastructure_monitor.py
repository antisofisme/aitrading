"""
Infrastructure Monitor - Monitors all infrastructure components
"""

import asyncio
import logging
import yaml
from pathlib import Path
from typing import Dict, List, Optional
import os

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

from models.infrastructure_model import (
    InfrastructureConfig, InfrastructureHealth, InfrastructureStatus,
    HealthCheckConfig, HealthCheckMethod, InfrastructureType
)
from core.health_checkers import HealthCheckerFactory

logger = logging.getLogger("central-hub.infrastructure-monitor")


class InfrastructureMonitor:
    """Monitors all infrastructure components with health checks"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or str(Path(__file__).parent.parent / "config" / "infrastructure.yaml")
        self.infrastructure_configs: Dict[str, InfrastructureConfig] = {}
        self.infrastructure_status: Dict[str, InfrastructureHealth] = {}
        self.monitoring_tasks: List[asyncio.Task] = []
        self.monitoring_active = False
        self.alert_callback = None  # Will be set by AlertManager

    async def initialize(self):
        """Load configuration and initialize monitoring"""
        logger.info("🔧 Initializing Infrastructure Monitor...")

        # Load configuration
        await self._load_config()

        # Initialize status for all infrastructure
        for name, config in self.infrastructure_configs.items():
            self.infrastructure_status[name] = InfrastructureHealth(
                name=name,
                type=config.type.value,
                status=InfrastructureStatus.UNKNOWN,
                critical=config.critical,
                dependents=[]
            )

        logger.info(f"✅ Initialized monitoring for {len(self.infrastructure_configs)} infrastructure components")

    async def _load_config(self):
        """Load infrastructure configuration from YAML"""
        try:
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)

            # Load databases
            for name, config in config_data.get('databases', {}).items():
                self._parse_infrastructure_config(name, config, 'database')

            # Load messaging
            for name, config in config_data.get('messaging', {}).items():
                self._parse_infrastructure_config(name, config, 'messaging')

            # Load search
            for name, config in config_data.get('search', {}).items():
                self._parse_infrastructure_config(name, config, 'search')

            logger.info(f"✅ Loaded configuration for {len(self.infrastructure_configs)} infrastructure components")

        except Exception as e:
            logger.error(f"❌ Failed to load infrastructure config: {e}", exc_info=True)
            raise

    def _parse_infrastructure_config(self, name: str, config: dict, category: str):
        """Parse infrastructure configuration"""
        try:
            health_check_config = HealthCheckConfig(
                method=HealthCheckMethod(config['health_check']['method']),
                endpoint=config['health_check'].get('endpoint'),
                port=config['health_check'].get('port'),
                command=config['health_check'].get('command'),
                timeout=config['health_check'].get('timeout', 5),
                interval=config['health_check'].get('interval', 30)
            )

            infra_config = InfrastructureConfig(
                name=name,
                host=config['host'],
                port=config['port'],
                type=InfrastructureType(config['type']),
                health_check=health_check_config,
                dependencies=config.get('dependencies', []),
                critical=config.get('critical', True),
                description=config.get('description', ''),
                management_port=config.get('management_port')
            )

            self.infrastructure_configs[name] = infra_config

        except Exception as e:
            logger.error(f"❌ Failed to parse config for {name}: {e}")

    async def start_monitoring(self):
        """Start monitoring all infrastructure"""
        if self.monitoring_active:
            logger.warning("⚠️ Monitoring already active")
            return

        self.monitoring_active = True
        logger.info("🚀 Starting infrastructure monitoring...")

        # Create monitoring task for each infrastructure
        for name in self.infrastructure_configs.keys():
            task = asyncio.create_task(self._monitor_infrastructure(name))
            self.monitoring_tasks.append(task)

        logger.info(f"✅ Started {len(self.monitoring_tasks)} monitoring tasks")

    async def stop_monitoring(self):
        """Stop all monitoring tasks"""
        logger.info("🛑 Stopping infrastructure monitoring...")
        self.monitoring_active = False

        # Cancel all tasks
        for task in self.monitoring_tasks:
            task.cancel()

        # Wait for cancellation
        await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
        self.monitoring_tasks.clear()

        logger.info("✅ Infrastructure monitoring stopped")

    async def _monitor_infrastructure(self, name: str):
        """Monitor single infrastructure component"""
        config = self.infrastructure_configs[name]
        interval = config.health_check.interval

        logger.info(f"📡 Started monitoring: {name} (interval: {interval}s)")

        while self.monitoring_active:
            try:
                # Perform health check
                await self._check_infrastructure_health(name)

                # Wait for next check
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                logger.info(f"🛑 Monitoring cancelled for {name}")
                break
            except Exception as e:
                logger.error(f"❌ Error monitoring {name}: {e}", exc_info=True)
                await asyncio.sleep(interval)

    async def _check_infrastructure_health(self, name: str):
        """Perform health check on infrastructure component"""
        config = self.infrastructure_configs[name]
        health_config = config.health_check

        try:
            # Get appropriate health checker
            checker_class = HealthCheckerFactory.get_checker(health_config.method.value)

            # Perform health check based on method
            if health_config.method == HealthCheckMethod.HTTP:
                port = health_config.port or config.port
                result = await checker_class.check(
                    host=config.host,
                    port=port,
                    endpoint=health_config.endpoint or "/health",
                    timeout=health_config.timeout
                )

            elif health_config.method == HealthCheckMethod.REDIS_PING:
                # Get password from environment if available
                password = (
                    os.getenv('DRAGONFLY_PASSWORD') or
                    os.getenv('DRAGONFLYDB_PASSWORD') or
                    os.getenv('REDIS_PASSWORD')
                )
                result = await checker_class.check(
                    host=config.host,
                    port=config.port,
                    password=password,
                    timeout=health_config.timeout
                )

            elif health_config.method == HealthCheckMethod.KAFKA_ADMIN:
                result = await checker_class.check(
                    host=config.host,
                    port=config.port,
                    timeout=health_config.timeout
                )

            elif health_config.method == HealthCheckMethod.TCP:
                result = await checker_class.check(
                    host=config.host,
                    port=config.port,
                    command=health_config.command,
                    timeout=health_config.timeout
                )

            else:
                logger.error(f"❌ Unknown health check method: {health_config.method}")
                return

            # Update status
            old_status = self.infrastructure_status[name].status
            new_status = InfrastructureStatus.HEALTHY if result.healthy else InfrastructureStatus.UNHEALTHY

            self.infrastructure_status[name].status = new_status
            self.infrastructure_status[name].response_time_ms = result.response_time_ms
            self.infrastructure_status[name].error = result.error
            self.infrastructure_status[name].last_check = int(asyncio.get_event_loop().time() * 1000)

            # Log health check result (like httpx does for HTTP checks)
            # For non-HTTP checks, log at INFO level so they're visible
            if health_config.method != HealthCheckMethod.HTTP:
                status_icon = "✅" if result.healthy else "❌"
                log_message = (
                    f"{status_icon} Health check: {name} "
                    f"[{health_config.method.value.upper()}] "
                    f"{config.host}:{config.port} "
                    f"→ {new_status.value} "
                    f"({result.response_time_ms:.1f}ms)"
                )

                if result.healthy:
                    logger.info(log_message)
                else:
                    logger.warning(f"{log_message} | Error: {result.error}")

            # Trigger alert if status changed
            if old_status != new_status:
                await self._handle_status_change(name, old_status, new_status)

        except Exception as e:
            logger.error(f"❌ Health check failed for {name}: {e}")
            self.infrastructure_status[name].status = InfrastructureStatus.UNHEALTHY
            self.infrastructure_status[name].error = str(e)

    async def _handle_status_change(self, name: str, old_status: InfrastructureStatus, new_status: InfrastructureStatus):
        """Handle infrastructure status change"""
        config = self.infrastructure_configs[name]

        if new_status == InfrastructureStatus.UNHEALTHY:
            # Infrastructure went down
            level = "critical" if config.critical else "warning"
            logger.error(f"🔴 [{level.upper()}] Infrastructure DOWN: {name}")

            # Trigger alert callback if set
            if self.alert_callback:
                await self.alert_callback(name, 'infrastructure', new_status.value, config.critical)

        elif new_status == InfrastructureStatus.HEALTHY and old_status == InfrastructureStatus.UNHEALTHY:
            # Infrastructure recovered
            logger.info(f"🟢 Infrastructure RECOVERED: {name}")

            # Trigger recovery alert
            if self.alert_callback:
                await self.alert_callback(name, 'infrastructure', 'recovered', config.critical)

    def get_infrastructure_status(self, name: str) -> Optional[InfrastructureHealth]:
        """Get status of specific infrastructure"""
        return self.infrastructure_status.get(name)

    def get_all_status(self) -> Dict[str, InfrastructureHealth]:
        """Get status of all infrastructure"""
        return self.infrastructure_status

    def get_unhealthy_infrastructure(self) -> List[str]:
        """Get list of unhealthy infrastructure names"""
        return [
            name for name, health in self.infrastructure_status.items()
            if health.status == InfrastructureStatus.UNHEALTHY
        ]

    def get_critical_down(self) -> List[str]:
        """Get list of critical infrastructure that is down"""
        return [
            name for name, health in self.infrastructure_status.items()
            if health.status == InfrastructureStatus.UNHEALTHY and health.critical
        ]

    async def manual_check(self, name: str) -> InfrastructureHealth:
        """Manually trigger health check for specific infrastructure"""
        if name not in self.infrastructure_configs:
            raise ValueError(f"Unknown infrastructure: {name}")

        logger.info(f"🔄 Manual health check triggered for: {name}")
        await self._check_infrastructure_health(name)
        return self.infrastructure_status[name]

    def set_alert_callback(self, callback):
        """Set callback function for alerts"""
        self.alert_callback = callback
        logger.info("✅ Alert callback registered")
