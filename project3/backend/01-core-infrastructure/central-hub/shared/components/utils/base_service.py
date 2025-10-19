"""
Base Service Class untuk standardisasi internal patterns
Digunakan oleh semua backend services untuk konsistensi
"""

import time
import asyncio
import logging as python_logging
from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from abc import ABC, abstractmethod

from .patterns.database import DatabaseManager
from .patterns.cache import CacheManager
from .patterns.config import InfrastructureConfigManager
from .patterns.tracing import RequestTracer
from .patterns.circuit_breaker import CircuitBreakerManager
from .patterns.response import StandardResponse


@dataclass
class ServiceConfig:
    """Standard service configuration"""
    service_name: str
    version: str
    port: int
    environment: str = "development"
    enable_tracing: bool = True
    enable_circuit_breaker: bool = True
    health_check_interval: int = 30
    cache_ttl_default: int = 300
    max_connections: int = 100


class BaseService(ABC):
    """
    Base class untuk semua backend services
    Menyediakan standard patterns untuk:
    - Database access
    - Caching
    - Configuration management
    - Request tracing
    - Circuit breaker protection
    - Error handling
    - Performance monitoring
    """

    def __init__(self, config: ServiceConfig):
        self.config = config
        self.service_name = config.service_name
        self.version = config.version
        self.start_time = datetime.utcnow()

        # Initialize standard components
        self._initialize_components()

        # Setup logging
        self.logger = self._setup_logging()

        # Service state
        self.is_healthy = True
        self.active_connections = 0

    def _initialize_components(self):
        """Initialize standard service components"""

        # Database manager
        self.db = DatabaseManager(
            service_name=self.service_name,
            max_connections=self.config.max_connections
        )

        # Cache manager
        self.cache = CacheManager(
            service_name=self.service_name,
            default_ttl=self.config.cache_ttl_default
        )

        # Infrastructure configuration manager (for Central Hub internal use)
        self.config_manager = InfrastructureConfigManager(
            service_name=self.service_name,
            environment=self.config.environment
        )

        # Request tracer
        if self.config.enable_tracing:
            self.tracer = RequestTracer(
                service_name=self.service_name
            )

        # Circuit breaker
        if self.config.enable_circuit_breaker:
            self.circuit_breaker = CircuitBreakerManager(
                service_name=self.service_name
            )

    def _setup_logging(self) -> python_logging.Logger:
        """Setup structured logging with newline format"""
        logger = python_logging.getLogger(self.service_name)
        logger.setLevel(python_logging.INFO)

        # Structured formatter with newline for better readability
        formatter = python_logging.Formatter(
            '%(asctime)s - %(name)s\n%(levelname)s - %(message)s'
        )

        handler = python_logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    async def process_with_tracing(self,
                                 operation_name: str,
                                 func: Callable,
                                 correlation_id: Optional[str] = None,
                                 *args, **kwargs) -> StandardResponse:
        """
        Standard wrapper untuk processing dengan tracing dan error handling
        """
        start_time = time.time()

        try:
            # Start tracing if enabled
            if hasattr(self, 'tracer') and correlation_id:
                with self.tracer.trace(operation_name, correlation_id):
                    result = await func(*args, **kwargs)
            else:
                result = await func(*args, **kwargs)

            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000

            # Log success
            self.logger.info(f"{operation_name} completed", extra={
                "operation": operation_name,
                "processing_time_ms": processing_time_ms,
                "correlation_id": correlation_id,
                "success": True
            })

            return StandardResponse(
                success=True,
                data=result,
                processing_time_ms=processing_time_ms,
                correlation_id=correlation_id
            )

        except Exception as e:
            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000

            # Log error
            self.logger.error(f"{operation_name} failed: {str(e)}", extra={
                "operation": operation_name,
                "processing_time_ms": processing_time_ms,
                "correlation_id": correlation_id,
                "error": str(e),
                "success": False
            })

            # Add error to trace if tracing enabled
            if hasattr(self, 'tracer') and correlation_id:
                self.tracer.add_error(correlation_id, str(e))

            return StandardResponse(
                success=False,
                error_message=str(e),
                processing_time_ms=processing_time_ms,
                correlation_id=correlation_id
            )

    async def get_config(self, key: str, default: Any = None) -> Any:
        """Standard configuration access"""
        return await self.config_manager.get(key, default)

    async def cache_get(self, key: str, default: Any = None) -> Any:
        """Standard cache access"""
        return await self.cache.get(key, default)

    async def cache_set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Standard cache storage"""
        return await self.cache.set(key, value, ttl)

    async def db_execute(self, query: str, params: Optional[Dict] = None) -> Any:
        """Standard database execution"""
        return await self.db.execute(query, params)

    async def check_circuit_breaker(self, external_service: str) -> bool:
        """Check if circuit breaker is open for external service"""
        if hasattr(self, 'circuit_breaker'):
            return self.circuit_breaker.is_open(external_service)
        return False

    async def record_external_success(self, external_service: str):
        """Record successful external service call"""
        if hasattr(self, 'circuit_breaker'):
            await self.circuit_breaker.record_success(external_service)

    async def record_external_failure(self, external_service: str):
        """Record failed external service call"""
        if hasattr(self, 'circuit_breaker'):
            await self.circuit_breaker.record_failure(external_service)

    async def health_check(self) -> Dict[str, Any]:
        """
        Standard health check implementation
        Override this method in child classes for service-specific checks
        """
        health_status = {
            "service": self.service_name,
            "status": "healthy" if self.is_healthy else "unhealthy",
            "version": self.version,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": int((datetime.utcnow() - self.start_time).total_seconds()),
            "active_connections": self.active_connections
        }

        try:
            # Check database connection
            if hasattr(self, 'db'):
                db_status = await self.db.health_check()
                health_status["database"] = db_status

            # Check cache connection
            if hasattr(self, 'cache'):
                cache_status = await self.cache.health_check()
                health_status["cache"] = cache_status

            # Check circuit breaker status
            if hasattr(self, 'circuit_breaker'):
                circuit_status = await self.circuit_breaker.get_status()
                health_status["circuit_breakers"] = circuit_status

            # Add service-specific health checks
            custom_health = await self.custom_health_checks()
            if custom_health:
                health_status.update(custom_health)

        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            health_status["status"] = "degraded"
            health_status["error"] = str(e)
            self.is_healthy = False

        return health_status

    @abstractmethod
    async def custom_health_checks(self) -> Dict[str, Any]:
        """
        Service-specific health checks
        Implement this method in child classes
        """
        return {}

    async def start(self):
        """Start the service"""
        self.logger.info(f"Starting {self.service_name} v{self.version}")

        # Initialize connections
        await self.db.connect()
        await self.cache.connect()
        await self.config_manager.load_config()

        # Start health check scheduler
        if self.config.health_check_interval > 0:
            asyncio.create_task(self._health_check_scheduler())

        # Custom startup logic
        await self.on_startup()

        self.logger.info(f"{self.service_name} started successfully")

    async def stop(self):
        """Stop the service gracefully"""
        self.logger.info(f"Stopping {self.service_name}")

        # Custom shutdown logic
        await self.on_shutdown()

        # Close connections
        await self.db.disconnect()
        await self.cache.disconnect()

        self.logger.info(f"{self.service_name} stopped")

    async def _health_check_scheduler(self):
        """Periodic health check scheduler"""
        while True:
            try:
                await self.health_check()
                await asyncio.sleep(self.config.health_check_interval)
            except Exception as e:
                self.logger.error(f"Health check scheduler error: {str(e)}")
                await asyncio.sleep(self.config.health_check_interval)

    @abstractmethod
    async def on_startup(self):
        """Custom startup logic - implement in child classes"""
        pass

    @abstractmethod
    async def on_shutdown(self):
        """Custom shutdown logic - implement in child classes"""
        pass