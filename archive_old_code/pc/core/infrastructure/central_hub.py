"""
Central Hub Service - Phase 1 Infrastructure Core
Basic service orchestration without AI/ML features
Port: 8000
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from ..services.import_manager import ImportManager
from ..services.error_handler import ErrorDNA
from ...shared.config.config_manager import ConfigManager
from ...shared.utils.logger import setup_logger

class ServiceStatus(Enum):
    STARTING = "starting"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"

@dataclass
class ServiceInfo:
    """Basic service information"""
    name: str
    port: int
    status: ServiceStatus
    health_endpoint: str
    last_check: Optional[datetime] = None
    error_message: Optional[str] = None

class CentralHub:
    """
    Central Hub for Phase 1 Infrastructure
    Handles basic service orchestration and management
    """

    def __init__(self, config_path: str = None):
        self.logger = setup_logger("central_hub", level=logging.INFO)
        self.config_manager = ConfigManager(config_path)
        self.import_manager = ImportManager()
        self.error_handler = ErrorDNA()

        # Service registry
        self.services: Dict[str, ServiceInfo] = {}
        self.startup_time = None
        self.is_running = False

        # Basic health tracking
        self.health_checks_enabled = True
        self.health_check_interval = 30  # seconds

        self.logger.info("Central Hub initialized for Phase 1")

    async def start(self) -> bool:
        """Start the Central Hub service"""
        try:
            self.startup_time = datetime.now()
            self.logger.info("Starting Central Hub service...")

            # Initialize basic configuration
            await self._initialize_configuration()

            # Register core services
            await self._register_core_services()

            # Start health monitoring
            if self.health_checks_enabled:
                asyncio.create_task(self._health_monitor_loop())

            self.is_running = True
            startup_duration = (datetime.now() - self.startup_time).total_seconds()

            self.logger.info(f"Central Hub started successfully in {startup_duration:.2f} seconds")
            return True

        except Exception as e:
            self.error_handler.handle_error(e, {"service": "central_hub", "action": "start"})
            return False

    async def stop(self) -> bool:
        """Stop the Central Hub service"""
        try:
            self.logger.info("Stopping Central Hub service...")
            self.is_running = False

            # Update all service statuses
            for service_name in self.services:
                self.services[service_name].status = ServiceStatus.STOPPED

            self.logger.info("Central Hub stopped successfully")
            return True

        except Exception as e:
            self.error_handler.handle_error(e, {"service": "central_hub", "action": "stop"})
            return False

    async def _initialize_configuration(self):
        """Initialize basic configuration"""
        try:
            # Load basic configuration
            config = self.config_manager.get_config()

            # Set default values for Phase 1
            defaults = {
                "central_hub": {
                    "port": 8000,
                    "health_check_interval": 30,
                    "enable_logging": True,
                    "log_level": "INFO"
                },
                "database": {
                    "connection_timeout": 30,
                    "max_connections": 10
                },
                "services": {
                    "startup_timeout": 60,
                    "health_check_timeout": 10
                }
            }

            # Merge with defaults
            for section, values in defaults.items():
                if section not in config:
                    config[section] = values
                else:
                    for key, value in values.items():
                        if key not in config[section]:
                            config[section][key] = value

            self.config_manager.update_config(config)
            self.logger.info("Configuration initialized")

        except Exception as e:
            self.error_handler.handle_error(e, {"action": "initialize_configuration"})
            raise

    async def _register_core_services(self):
        """Register core Phase 1 services"""
        try:
            # Core services for Phase 1
            core_services = [
                ServiceInfo(
                    name="database_service",
                    port=8008,
                    status=ServiceStatus.STARTING,
                    health_endpoint="/health"
                ),
                ServiceInfo(
                    name="import_manager",
                    port=8001,
                    status=ServiceStatus.STARTING,
                    health_endpoint="/health"
                ),
                ServiceInfo(
                    name="error_handler",
                    port=8002,
                    status=ServiceStatus.STARTING,
                    health_endpoint="/health"
                )
            ]

            for service in core_services:
                self.services[service.name] = service
                self.logger.info(f"Registered service: {service.name} on port {service.port}")

        except Exception as e:
            self.error_handler.handle_error(e, {"action": "register_core_services"})
            raise

    async def register_service(self, service_info: ServiceInfo) -> bool:
        """Register a new service"""
        try:
            self.services[service_info.name] = service_info
            self.logger.info(f"Service registered: {service_info.name}")
            return True

        except Exception as e:
            self.error_handler.handle_error(e, {"action": "register_service", "service": service_info.name})
            return False

    async def unregister_service(self, service_name: str) -> bool:
        """Unregister a service"""
        try:
            if service_name in self.services:
                del self.services[service_name]
                self.logger.info(f"Service unregistered: {service_name}")
                return True
            return False

        except Exception as e:
            self.error_handler.handle_error(e, {"action": "unregister_service", "service": service_name})
            return False

    async def get_service_status(self, service_name: str) -> Optional[ServiceInfo]:
        """Get status of a specific service"""
        return self.services.get(service_name)

    async def get_all_services(self) -> Dict[str, ServiceInfo]:
        """Get all registered services"""
        return self.services.copy()

    async def _health_monitor_loop(self):
        """Background health monitoring loop"""
        while self.is_running:
            try:
                await self._check_services_health()
                await asyncio.sleep(self.health_check_interval)

            except Exception as e:
                self.error_handler.handle_error(e, {"action": "health_monitor_loop"})
                await asyncio.sleep(self.health_check_interval)

    async def _check_services_health(self):
        """Check health of all registered services"""
        for service_name, service_info in self.services.items():
            try:
                # Basic health check simulation for Phase 1
                # In a real implementation, this would make HTTP calls to service endpoints
                service_info.last_check = datetime.now()

                # Simulate health check logic
                if service_info.status == ServiceStatus.STARTING:
                    # Check if service should be running by now
                    if self.startup_time and (datetime.now() - self.startup_time).total_seconds() > 60:
                        service_info.status = ServiceStatus.RUNNING

                self.logger.debug(f"Health check completed for {service_name}: {service_info.status.value}")

            except Exception as e:
                service_info.status = ServiceStatus.ERROR
                service_info.error_message = str(e)
                self.error_handler.handle_error(e, {"action": "health_check", "service": service_name})

    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        try:
            total_services = len(self.services)
            running_services = sum(1 for s in self.services.values() if s.status == ServiceStatus.RUNNING)
            error_services = sum(1 for s in self.services.values() if s.status == ServiceStatus.ERROR)

            uptime = (datetime.now() - self.startup_time).total_seconds() if self.startup_time else 0

            health_status = {
                "status": "healthy" if error_services == 0 else "degraded" if running_services > 0 else "critical",
                "uptime_seconds": uptime,
                "services": {
                    "total": total_services,
                    "running": running_services,
                    "error": error_services
                },
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0-phase1"
            }

            return health_status

        except Exception as e:
            self.error_handler.handle_error(e, {"action": "get_system_health"})
            return {"status": "error", "message": str(e)}

    async def restart_service(self, service_name: str) -> bool:
        """Restart a specific service"""
        try:
            if service_name not in self.services:
                return False

            self.logger.info(f"Restarting service: {service_name}")

            # Update service status
            self.services[service_name].status = ServiceStatus.STARTING
            self.services[service_name].error_message = None

            # Simulate restart delay
            await asyncio.sleep(2)

            self.services[service_name].status = ServiceStatus.RUNNING
            self.logger.info(f"Service restarted: {service_name}")

            return True

        except Exception as e:
            self.error_handler.handle_error(e, {"action": "restart_service", "service": service_name})
            return False

    def get_import_manager(self) -> ImportManager:
        """Get the import manager instance"""
        return self.import_manager

    def get_error_handler(self) -> ErrorDNA:
        """Get the error handler instance"""
        return self.error_handler

    def get_config_manager(self) -> ConfigManager:
        """Get the configuration manager instance"""
        return self.config_manager

# Example usage and testing
async def main():
    """Example usage of Central Hub"""
    hub = CentralHub()

    try:
        # Start the hub
        success = await hub.start()
        if not success:
            print("Failed to start Central Hub")
            return

        # Wait a bit
        await asyncio.sleep(5)

        # Get system health
        health = await hub.get_system_health()
        print(f"System Health: {json.dumps(health, indent=2)}")

        # List services
        services = await hub.get_all_services()
        print(f"Registered Services: {len(services)}")
        for name, info in services.items():
            print(f"  - {name}: {info.status.value} (port {info.port})")

        # Stop the hub
        await hub.stop()

    except Exception as e:
        print(f"Error in main: {e}")

if __name__ == "__main__":
    asyncio.run(main())