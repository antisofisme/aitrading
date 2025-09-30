"""
Central Hub - Health Monitor
Real health monitoring implementation
"""

import asyncio
import logging
import time
import httpx
from typing import Dict, List, Optional, Any


class HealthMonitor:
    """Real health monitoring for all services"""

    def __init__(self, service_registry, db_manager=None, cache_manager=None):
        self.service_registry = service_registry
        self.db_manager = db_manager
        self.cache_manager = cache_manager
        self.logger = logging.getLogger("central-hub.health-monitor")
        self.monitoring_active = False
        self.check_interval = 30  # seconds

    async def start_monitoring(self):
        """Start real health monitoring background task"""
        self.monitoring_active = True
        self.logger.info("🔍 Health monitoring started")

        while self.monitoring_active:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                self.logger.error(f"Health monitoring error: {str(e)}")
                await asyncio.sleep(5)

    async def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring_active = False
        self.logger.info("🛑 Health monitoring stopped")

    async def _perform_health_checks(self):
        """Perform real health checks on all registered services"""
        if not self.service_registry:
            return

        registry = self.service_registry.get_registry()

        async with httpx.AsyncClient(timeout=5.0) as client:
            for service_name, service_info in registry.items():
                try:
                    await self._check_service_health(client, service_name, service_info)
                except Exception as e:
                    self.logger.warning(f"Health check failed for {service_name}: {str(e)}")

    async def _check_service_health(self, client: httpx.AsyncClient, service_name: str, service_info: Dict[str, Any]):
        """Perform real health check on individual service"""
        health_url = f"http://{service_info['host']}:{service_info['port']}{service_info.get('health_endpoint', '/health')}"

        start_time = time.time()
        try:
            response = await client.get(health_url)
            response_time = (time.time() - start_time) * 1000

            if response.status_code == 200:
                # Service is healthy
                await self._record_healthy_service(service_name, service_info, response_time, response.json())
            else:
                # Service responding but unhealthy
                await self._record_unhealthy_service(service_name, service_info, f"HTTP {response.status_code}")

        except Exception as e:
            # Service completely down
            await self._record_unhealthy_service(service_name, service_info, str(e))

    async def _record_healthy_service(self, service_name: str, service_info: Dict[str, Any], response_time: float, health_data: Dict[str, Any]):
        """Record healthy service status"""
        # Update service registry
        service_info['status'] = 'active'
        service_info['last_seen'] = time.time()
        service_info['response_time_ms'] = response_time

        # Store in database
        if self.db_manager:
            import json
            await self.db_manager.execute(
                """
                INSERT INTO health_metrics (service_name, status, response_time_ms, metadata)
                VALUES ($1, $2, $3, $4)
                """,
                [service_name, "healthy", response_time, json.dumps(health_data)]
            )

            # Update service registry table
            await self.db_manager.execute(
                """
                UPDATE service_registry
                SET last_seen = CURRENT_TIMESTAMP, status = 'active'
                WHERE service_name = $1
                """,
                [service_name]
            )

        # Cache health status
        if self.cache_manager:
            await self.cache_manager.set(
                f"health:{service_name}",
                {
                    "status": "healthy",
                    "response_time_ms": response_time,
                    "timestamp": time.time(),
                    "health_data": health_data
                },
                ttl=60
            )

        self.logger.debug(f"✅ {service_name} healthy ({response_time:.1f}ms)")

    async def _record_unhealthy_service(self, service_name: str, service_info: Dict[str, Any], error_message: str):
        """Record unhealthy service status"""
        # Update service registry
        service_info['status'] = 'unhealthy'
        service_info['last_error'] = error_message
        service_info['last_error_time'] = time.time()

        # Store in database
        if self.db_manager:
            import json
            await self.db_manager.execute(
                """
                INSERT INTO health_metrics (service_name, status, metadata)
                VALUES ($1, $2, $3)
                """,
                [service_name, "unhealthy", json.dumps({"error": error_message})]
            )

            # Update service registry table
            await self.db_manager.execute(
                """
                UPDATE service_registry
                SET status = 'unhealthy'
                WHERE service_name = $1
                """,
                [service_name]
            )

        # Cache unhealthy status
        if self.cache_manager:
            await self.cache_manager.set(
                f"health:{service_name}",
                {
                    "status": "unhealthy",
                    "error": error_message,
                    "timestamp": time.time()
                },
                ttl=60
            )

        self.logger.warning(f"❌ {service_name} unhealthy: {error_message}")

    async def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary"""
        if not self.service_registry:
            return {"status": "no_services", "services": {}}

        registry = self.service_registry.get_registry()
        healthy_count = sum(1 for s in registry.values() if s.get('status') == 'active')
        total_count = len(registry)

        return {
            "overall_status": "healthy" if healthy_count == total_count else "degraded" if healthy_count > 0 else "unhealthy",
            "healthy_services": healthy_count,
            "total_services": total_count,
            "services": {
                name: {
                    "status": info.get('status', 'unknown'),
                    "last_seen": info.get('last_seen'),
                    "response_time_ms": info.get('response_time_ms'),
                    "last_error": info.get('last_error')
                }
                for name, info in registry.items()
            },
            "timestamp": time.time()
        }