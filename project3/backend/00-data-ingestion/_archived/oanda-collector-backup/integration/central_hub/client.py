"""
Central Hub Client - Service discovery and configuration
"""
import logging
import asyncio
from typing import Dict, Any, Optional
import aiohttp
import json

logger = logging.getLogger(__name__)


class CentralHubClient:
    """
    Client for Central Hub service discovery and configuration
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Central Hub client

        Args:
            config: Central Hub configuration
        """
        self.config = config
        self.host = config['central_hub']['host']
        self.port = config['central_hub']['port']
        self.api_version = config['central_hub'].get('api_version', 'v1')

        self.base_url = f"http://{self.host}:{self.port}/api/{self.api_version}"

        self.session: Optional[aiohttp.ClientSession] = None
        self.registered = False
        self.registration_id: Optional[str] = None

        logger.info(f"Central Hub client initialized: {self.base_url}")

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure HTTP session exists"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def register_service(
        self,
        service_name: str,
        host: str,
        port: int,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Register service with Central Hub

        Args:
            service_name: Service name
            host: Service host
            port: Service port
            metadata: Service metadata

        Returns:
            bool: True if registration successful
        """
        try:
            session = await self._ensure_session()

            payload = {
                'service_name': service_name,
                'host': host,
                'port': port,
                'protocol': 'http',
                'version': self.config['service']['version'],
                'environment': self.config.get('environment', 'development'),
                'health_endpoint': '/health',
                'metadata': metadata
            }

            async with session.post(
                f"{self.base_url}/discovery/register",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.registration_id = data.get('registration_id')
                    self.registered = True
                    logger.info(f"Service registered successfully: {self.registration_id}")
                    return True
                else:
                    error = await response.text()
                    logger.error(f"Service registration failed: {response.status} - {error}")
                    return False

        except Exception as e:
            logger.error(f"Error registering service: {e}")
            return False

    async def deregister_service(self, service_name: str) -> bool:
        """
        Deregister service from Central Hub

        Args:
            service_name: Service name to deregister

        Returns:
            bool: True if deregistration successful
        """
        if not self.registered:
            return True

        try:
            session = await self._ensure_session()

            async with session.delete(
                f"{self.base_url}/discovery/register/{service_name}",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    self.registered = False
                    logger.info(f"Service deregistered: {service_name}")
                    return True
                else:
                    logger.error(f"Deregistration failed: {response.status}")
                    return False

        except Exception as e:
            logger.error(f"Error deregistering service: {e}")
            return False

    async def get_configuration(self, service_name: str) -> Optional[Dict[str, Any]]:
        """
        Get service configuration from Central Hub

        Args:
            service_name: Service name

        Returns:
            Dict containing configuration or None
        """
        try:
            session = await self._ensure_session()

            async with session.get(
                f"{self.base_url}/config/{service_name}",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    config = await response.json()
                    logger.info(f"Configuration retrieved for {service_name}")
                    return config
                else:
                    logger.warning(f"Configuration not found: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Error getting configuration: {e}")
            return None

    async def send_health_report(
        self,
        service_name: str,
        health_data: Dict[str, Any]
    ) -> bool:
        """
        Send health report to Central Hub

        Args:
            service_name: Service name
            health_data: Health metrics and status

        Returns:
            bool: True if report sent successfully
        """
        try:
            session = await self._ensure_session()

            async with session.post(
                f"{self.base_url}/health/report",
                json=health_data,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    logger.debug(f"Health report sent for {service_name}")
                    return True
                else:
                    logger.warning(f"Health report failed: {response.status}")
                    return False

        except Exception as e:
            logger.error(f"Error sending health report: {e}")
            return False

    async def discover_service(
        self,
        service_type: Optional[str] = None,
        service_name: Optional[str] = None
    ) -> Optional[list]:
        """
        Discover services from Central Hub

        Args:
            service_type: Filter by service type
            service_name: Filter by service name

        Returns:
            List of discovered services or None
        """
        try:
            session = await self._ensure_session()

            params = {}
            if service_type:
                params['service_type'] = service_type
            if service_name:
                params['service_name'] = service_name

            async with session.get(
                f"{self.base_url}/discovery/services",
                params=params,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('services', [])
                else:
                    logger.warning(f"Service discovery failed: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Error discovering services: {e}")
            return None

    async def heartbeat(self, service_name: str, instance_id: str) -> bool:
        """
        Send heartbeat to Central Hub

        Args:
            service_name: Service name
            instance_id: Instance identifier

        Returns:
            bool: True if heartbeat successful
        """
        try:
            session = await self._ensure_session()

            payload = {
                'service_name': service_name,
                'instance_id': instance_id,
                'timestamp': asyncio.get_event_loop().time()
            }

            async with session.post(
                f"{self.base_url}/discovery/heartbeat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                return response.status == 200

        except Exception as e:
            logger.error(f"Error sending heartbeat: {e}")
            return False

    async def run_heartbeat_loop(
        self,
        service_name: str,
        instance_id: str,
        interval: int = 30
    ) -> None:
        """
        Run continuous heartbeat loop

        Args:
            service_name: Service name
            instance_id: Instance identifier
            interval: Heartbeat interval in seconds
        """
        logger.info(f"Starting heartbeat loop (interval: {interval}s)")

        while True:
            try:
                await self.heartbeat(service_name, instance_id)
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                logger.info("Heartbeat loop cancelled")
                break

            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(interval)

    async def close(self) -> None:
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("Central Hub client session closed")
