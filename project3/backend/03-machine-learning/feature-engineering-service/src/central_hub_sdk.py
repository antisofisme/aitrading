"""
Central Hub SDK for ML Services

Lightweight SDK for:
1. Service registration
2. Configuration retrieval
3. Heartbeat sending
"""

import logging
import httpx
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class CentralHubSDK:
    """Central Hub SDK for ML services"""

    def __init__(self, base_url: str = "http://suho-central-hub:7000"):
        self.base_url = base_url
        self.service_name = None
        self.registered = False

        logger.info(f"📡 Central Hub SDK initialized: {base_url}")

    async def register(
        self,
        service_name: str,
        service_type: str,
        version: str,
        metadata: Optional[Dict] = None
    ):
        """Register service with Central Hub"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/discovery/register",
                    json={
                        "name": service_name,
                        "type": service_type,
                        "version": version,
                        "host": "feature-engineering-service",
                        "port": 8000,
                        "metadata": metadata or {}
                    }
                )

                if response.status_code == 200:
                    self.service_name = service_name
                    self.registered = True
                    logger.info(f"✅ Registered with Central Hub: {service_name}")
                else:
                    logger.error(f"❌ Registration failed: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error(f"❌ Registration error: {e}")

    async def get_database_config(self, db_type: str) -> Dict[str, Any]:
        """Get database configuration from Central Hub"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/config/database/{db_type}"
                )

                if response.status_code == 200:
                    config = response.json()
                    logger.info(f"✅ Retrieved {db_type} config from Central Hub")
                    return config
                else:
                    logger.error(f"❌ Config retrieval failed: {response.status_code}")
                    return {}

        except Exception as e:
            logger.error(f"❌ Config retrieval error: {e}")
            return {}

    async def send_heartbeat(self, metrics: Optional[Dict] = None):
        """Send heartbeat to Central Hub"""
        if not self.registered:
            logger.warning("⚠️ Service not registered, skipping heartbeat")
            return

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/discovery/heartbeat",
                    json={
                        "service_name": self.service_name,
                        "metrics": metrics or {}
                    }
                )

                if response.status_code == 200:
                    logger.debug(f"💓 Heartbeat sent: {self.service_name}")
                else:
                    logger.warning(f"⚠️ Heartbeat failed: {response.status_code}")

        except Exception as e:
            logger.warning(f"⚠️ Heartbeat error: {e}")

    async def deregister(self):
        """Deregister service from Central Hub"""
        if not self.registered:
            return

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/discovery/deregister",
                    json={"service_name": self.service_name}
                )

                if response.status_code == 200:
                    logger.info(f"✅ Deregistered from Central Hub: {self.service_name}")
                    self.registered = False

        except Exception as e:
            logger.error(f"❌ Deregistration error: {e}")
