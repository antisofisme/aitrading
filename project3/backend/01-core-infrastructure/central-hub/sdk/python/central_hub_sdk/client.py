"""
Central Hub Client - Shared module for service registration and health reporting
Used by all data ingestion services to integrate with Central Hub
"""
import asyncio
import logging
import os
import time
from typing import Dict, List, Optional, Any
import httpx

logger = logging.getLogger(__name__)


class CentralHubClient:
    """
    Client for integrating services with Central Hub

    Features:
    - Service registration
    - Periodic heartbeat
    - Health reporting
    - Graceful deregistration
    """

    def __init__(
        self,
        service_name: str,
        service_type: str,
        version: str = "1.0.0",
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.service_name = service_name
        self.service_type = service_type
        self.version = version
        self.capabilities = capabilities or []
        self.metadata = metadata or {}

        # Central Hub configuration
        self.central_hub_url = os.getenv('CENTRAL_HUB_URL', 'http://suho-central-hub:7000')
        self.heartbeat_interval = int(os.getenv('HEARTBEAT_INTERVAL', '30'))  # seconds

        # State
        self.registered = False
        self.heartbeat_task = None
        self.is_running = False

        logger.info(f"Central Hub Client initialized for {service_name}")
        logger.info(f"Central Hub URL: {self.central_hub_url}")

    async def register(self) -> bool:
        """
        Register service with Central Hub

        Returns:
            bool: True if registration successful
        """
        try:
            registration_data = {
                "name": self.service_name,
                "host": os.getenv('HOSTNAME', self.service_name),
                "port": int(os.getenv('SERVICE_PORT', '8080')),
                "protocol": "http",
                "health_endpoint": "/health",
                "version": self.version,
                "metadata": {
                    **self.metadata,
                    "type": self.service_type,
                    "instance_id": os.getenv('INSTANCE_ID', f"{self.service_name}-1"),
                    "start_time": int(time.time() * 1000)
                },
                "capabilities": self.capabilities
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.central_hub_url}/api/discovery/register",
                    json=registration_data
                )

                if response.status_code == 200:
                    result = response.json()
                    self.registered = True
                    logger.info(f"✅ Registered with Central Hub: {self.service_name}")
                    logger.info(f"Registration response: {result}")
                    return True
                else:
                    logger.error(f"❌ Registration failed: HTTP {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    return False

        except httpx.ConnectError:
            logger.warning(f"⚠️ Cannot connect to Central Hub at {self.central_hub_url}")
            logger.warning(f"Service {self.service_name} will run without Central Hub integration")
            return False
        except Exception as e:
            logger.error(f"❌ Registration error: {e}", exc_info=True)
            return False

    async def send_heartbeat(self, metrics: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send heartbeat to Central Hub with optional metrics

        Args:
            metrics: Service-specific metrics to report

        Returns:
            bool: True if heartbeat sent successfully
        """
        if not self.registered:
            logger.debug("Not registered, skipping heartbeat")
            return False

        try:
            heartbeat_data = {
                "service_name": self.service_name,
                "status": "healthy",
                "timestamp": int(time.time() * 1000),
                "metrics": metrics or {}
            }

            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{self.central_hub_url}/api/discovery/heartbeat",
                    json=heartbeat_data
                )

                if response.status_code == 200:
                    logger.debug(f"Heartbeat sent for {self.service_name}")
                    return True
                else:
                    logger.warning(f"Heartbeat failed: HTTP {response.status_code}")
                    return False

        except Exception as e:
            logger.warning(f"Heartbeat error: {e}")
            return False

    async def start_heartbeat_loop(self):
        """Start periodic heartbeat task"""
        self.is_running = True

        while self.is_running:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                await self.send_heartbeat()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")

    async def start(self, metrics_callback=None):
        """
        Start Central Hub integration

        Args:
            metrics_callback: Optional async function that returns metrics dict
        """
        # Register with Central Hub
        await self.register()

        # Start heartbeat loop if registered
        if self.registered:
            async def heartbeat_with_metrics():
                while self.is_running:
                    try:
                        await asyncio.sleep(self.heartbeat_interval)

                        # Get metrics if callback provided
                        metrics = None
                        if metrics_callback:
                            metrics = await metrics_callback() if asyncio.iscoroutinefunction(metrics_callback) else metrics_callback()

                        await self.send_heartbeat(metrics)
                    except asyncio.CancelledError:
                        break
                    except Exception as e:
                        logger.error(f"Heartbeat error: {e}")

            self.heartbeat_task = asyncio.create_task(heartbeat_with_metrics())
            logger.info(f"Started heartbeat loop (interval: {self.heartbeat_interval}s)")

    async def deregister(self):
        """Deregister service from Central Hub (graceful shutdown)"""
        if not self.registered:
            return

        try:
            # Stop heartbeat
            self.is_running = False
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
                try:
                    await self.heartbeat_task
                except asyncio.CancelledError:
                    pass

            # Send deregistration
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    f"{self.central_hub_url}/api/discovery/deregister",
                    json={"service_name": self.service_name}
                )

            logger.info(f"✅ Deregistered {self.service_name} from Central Hub")
            self.registered = False

        except Exception as e:
            logger.warning(f"Deregistration error: {e}")

    async def stop(self):
        """Stop Central Hub integration"""
        await self.deregister()

    async def get_database_config(self, db_name: str) -> Dict[str, Any]:
        """
        Get database configuration from Central Hub

        Args:
            db_name: Database name (postgresql, clickhouse, dragonflydb, arangodb, weaviate)

        Returns:
            Dict containing database configuration

        Raises:
            httpx.HTTPStatusError: If database config not found or request fails
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.central_hub_url}/api/config/database/{db_name}"
                )
                response.raise_for_status()
                result = response.json()
                logger.info(f"✅ Retrieved database config for {db_name}")
                return result['config']

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.error(f"❌ Database config not found: {db_name}")
                raise ValueError(f"Database '{db_name}' not found in Central Hub configuration")
            else:
                logger.error(f"❌ Failed to get database config: HTTP {e.response.status_code}")
                raise
        except Exception as e:
            logger.error(f"❌ Error getting database config: {e}")
            raise

    async def get_messaging_config(self, msg_name: str) -> Dict[str, Any]:
        """
        Get messaging configuration from Central Hub

        Args:
            msg_name: Messaging system name (nats, kafka, zookeeper)

        Returns:
            Dict containing messaging configuration

        Raises:
            httpx.HTTPStatusError: If messaging config not found or request fails
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.central_hub_url}/api/config/messaging/{msg_name}"
                )
                response.raise_for_status()
                result = response.json()
                logger.info(f"✅ Retrieved messaging config for {msg_name}")
                return result['config']

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.error(f"❌ Messaging config not found: {msg_name}")
                raise ValueError(f"Messaging system '{msg_name}' not found in Central Hub configuration")
            else:
                logger.error(f"❌ Failed to get messaging config: HTTP {e.response.status_code}")
                raise
        except Exception as e:
            logger.error(f"❌ Error getting messaging config: {e}")
            raise
