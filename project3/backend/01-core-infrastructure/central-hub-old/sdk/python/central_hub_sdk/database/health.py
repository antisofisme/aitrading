"""
Unified Database Health Checker
Monitor health of all database connections
"""
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from .router import DatabaseRouter
from .base import DatabaseStatus, DatabaseType

logger = logging.getLogger(__name__)


class DatabaseHealthChecker:
    """
    Unified health checker for all databases

    Features:
    - Real-time health monitoring
    - Connection status tracking
    - Performance metrics
    - Alert triggering (future)
    """

    def __init__(self, router: DatabaseRouter):
        """
        Initialize health checker

        Args:
            router: DatabaseRouter instance
        """
        self.router = router
        self.last_check_time: Optional[datetime] = None
        self.last_results: Dict[str, Any] = {}

    async def check_all(self, force: bool = False) -> Dict[str, Any]:
        """
        Check health of all databases

        Args:
            force: Force check even if recently checked

        Returns:
            Comprehensive health report
        """
        if not self.router.is_initialized():
            return {
                "status": "error",
                "error": "Router not initialized",
                "timestamp": datetime.utcnow().isoformat()
            }

        # Check if we need to run (avoid too frequent checks)
        if not force and self.last_check_time:
            seconds_since_check = (datetime.utcnow() - self.last_check_time).seconds
            if seconds_since_check < 10:  # Don't check more than once per 10 seconds
                return {
                    **self.last_results,
                    "cached": True,
                    "seconds_old": seconds_since_check
                }

        logger.info("🏥 Running database health check...")

        # Get health from router
        db_health = await self.router.health_check_all()

        # Analyze overall status
        statuses = [
            health.get("status", "unknown")
            for health in db_health.values()
            if isinstance(health, dict)
        ]

        overall_status = self._determine_overall_status(statuses)

        # Build comprehensive report
        report = {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "databases": db_health,
            "summary": {
                "total": len(db_health),
                "healthy": sum(1 for s in statuses if s == DatabaseStatus.HEALTHY.value),
                "degraded": sum(1 for s in statuses if s == DatabaseStatus.DEGRADED.value),
                "unhealthy": sum(1 for s in statuses if s == DatabaseStatus.UNHEALTHY.value),
            }
        }

        # Add critical systems check
        report["critical_systems"] = self._check_critical_systems(db_health)

        # Update cache
        self.last_check_time = datetime.utcnow()
        self.last_results = report

        logger.info(
            f"✅ Health check complete: {report['summary']['healthy']}/{report['summary']['total']} healthy"
        )

        return report

    def _determine_overall_status(self, statuses: List[str]) -> str:
        """Determine overall system status from database statuses"""
        if not statuses:
            return "unknown"

        # If any critical system is unhealthy, overall is unhealthy
        unhealthy_count = sum(1 for s in statuses if s == DatabaseStatus.UNHEALTHY.value)
        if unhealthy_count > 0:
            return "unhealthy"

        # If any system is degraded, overall is degraded
        degraded_count = sum(1 for s in statuses if s == DatabaseStatus.DEGRADED.value)
        if degraded_count > 0:
            return "degraded"

        # All healthy
        return "healthy"

    def _check_critical_systems(self, db_health: Dict[str, Any]) -> Dict[str, bool]:
        """
        Check if critical systems are operational

        Critical systems:
        - TimescaleDB (tick data storage)
        - DragonflyDB (caching)
        """
        critical_systems = {
            DatabaseType.TIMESCALEDB.value: False,
            DatabaseType.DRAGONFLYDB.value: False,
        }

        for db_name, health in db_health.items():
            if db_name in critical_systems:
                if isinstance(health, dict):
                    status = health.get("status", "unknown")
                    critical_systems[db_name] = status in [
                        DatabaseStatus.HEALTHY.value,
                        DatabaseStatus.DEGRADED.value
                    ]

        return critical_systems

    async def check_database(self, db_type: DatabaseType) -> Dict[str, Any]:
        """
        Check health of specific database

        Args:
            db_type: Database type to check

        Returns:
            Health status dict
        """
        if not self.router.is_initialized():
            return {
                "status": "error",
                "error": "Router not initialized"
            }

        try:
            manager = self.router.get_manager(db_type=db_type)
            health = await manager.health_check()

            return {
                "database": db_type.value,
                "timestamp": datetime.utcnow().isoformat(),
                **health
            }

        except Exception as e:
            logger.error(f"Health check failed for {db_type.value}: {e}")
            return {
                "database": db_type.value,
                "status": "error",
                "error": str(e)
            }

    def get_last_check(self) -> Optional[Dict[str, Any]]:
        """Get last health check results"""
        return self.last_results if self.last_results else None

    async def wait_for_healthy(
        self,
        timeout: int = 60,
        check_interval: int = 5
    ) -> bool:
        """
        Wait for all critical systems to be healthy

        Args:
            timeout: Maximum wait time in seconds
            check_interval: Check interval in seconds

        Returns:
            bool: True if healthy within timeout
        """
        import asyncio

        elapsed = 0

        logger.info(f"⏳ Waiting for databases to be healthy (timeout: {timeout}s)...")

        while elapsed < timeout:
            report = await self.check_all(force=True)

            if report.get("status") == "healthy":
                logger.info("✅ All databases are healthy")
                return True

            # Check if critical systems are at least degraded (operational)
            critical = report.get("critical_systems", {})
            if all(critical.values()):
                logger.info("✅ All critical systems operational")
                return True

            await asyncio.sleep(check_interval)
            elapsed += check_interval

            logger.debug(f"⏳ Still waiting... ({elapsed}/{timeout}s)")

        logger.warning(f"⚠️  Timeout reached. Database health check incomplete.")
        return False
