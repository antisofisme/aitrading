"""
Service Registry - Manages service registration with Central Hub
"""
import logging
import asyncio
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ServiceRegistry:
    """
    Manages service registration and heartbeat with Central Hub
    """

    def __init__(
        self,
        central_hub_client,
        config: Dict[str, Any]
    ):
        """
        Initialize Service Registry

        Args:
            central_hub_client: Central Hub client instance
            config: Service configuration
        """
        self.central_hub = central_hub_client
        self.config = config

        self.service_name = config['service']['name']
        self.instance_id = config['service']['instance_id']
        self.registered = False

        self.heartbeat_task: Optional[asyncio.Task] = None

    async def register(
        self,
        host: str,
        port: int,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Register service with Central Hub

        Args:
            host: Service host
            port: Service port
            metadata: Service metadata

        Returns:
            bool: True if registration successful
        """
        logger.info(f"Registering service: {self.service_name}")

        success = await self.central_hub.register_service(
            service_name=self.service_name,
            host=host,
            port=port,
            metadata=metadata
        )

        if success:
            self.registered = True
            logger.info(f"Service registered successfully: {self.service_name}")

            # Start heartbeat loop
            if self.config['central_hub']['service_discovery'].get('enabled', True):
                await self.start_heartbeat()

        return success

    async def deregister(self) -> bool:
        """
        Deregister service from Central Hub

        Returns:
            bool: True if deregistration successful
        """
        if not self.registered:
            return True

        logger.info(f"Deregistering service: {self.service_name}")

        # Stop heartbeat
        await self.stop_heartbeat()

        # Deregister
        success = await self.central_hub.deregister_service(self.service_name)

        if success:
            self.registered = False
            logger.info(f"Service deregistered: {self.service_name}")

        return success

    async def start_heartbeat(self) -> None:
        """Start heartbeat loop"""
        if self.heartbeat_task and not self.heartbeat_task.done():
            logger.warning("Heartbeat already running")
            return

        interval = self.config['central_hub']['service_discovery'].get('heartbeat_interval', 30)

        self.heartbeat_task = asyncio.create_task(
            self.central_hub.run_heartbeat_loop(
                service_name=self.service_name,
                instance_id=self.instance_id,
                interval=interval
            )
        )

        logger.info(f"Heartbeat started (interval: {interval}s)")

    async def stop_heartbeat(self) -> None:
        """Stop heartbeat loop"""
        if self.heartbeat_task and not self.heartbeat_task.done():
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass

            logger.info("Heartbeat stopped")

    async def send_health_report(self, health_data: Dict[str, Any]) -> bool:
        """
        Send health report to Central Hub

        Args:
            health_data: Health metrics and status

        Returns:
            bool: True if report sent successfully
        """
        return await self.central_hub.send_health_report(
            service_name=self.service_name,
            health_data=health_data
        )

    def is_registered(self) -> bool:
        """Check if service is registered"""
        return self.registered
