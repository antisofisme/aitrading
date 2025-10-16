#!/usr/bin/env python3
"""
Service Coordinator - Central Hub coordination logic
Manages service-to-service communication and coordination

⚠️ PARTIALLY DEPRECATED (2025-10-16) ⚠️

Database coordination_history table removed.

Reason: Not needed for current architecture.
- Services communicate directly via NATS/Kafka
- NATS/Kafka provide message delivery tracking
- Each service has own logging for debugging

Changes:
- coordination_history table: REMOVED (lines 131-141 disabled)
- Coordination logic: Still functional (uses in-memory tracking)

This code continues to work for in-memory coordination,
but database persistence is disabled.
"""

import asyncio
import logging
import time
import httpx
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import warnings

logger = logging.getLogger("central-hub.coordination")

# Issue warning about database coordination history
warnings.warn(
    "ServiceCoordinator database persistence disabled. coordination_history table removed.",
    DeprecationWarning,
    stacklevel=2
)


@dataclass
class ServiceCoordinationRequest:
    """Service coordination request structure"""
    source_service: str
    target_service: str
    operation: str
    data: Dict[str, Any]
    correlation_id: str
    timeout_seconds: int = 30


@dataclass
class CoordinationResult:
    """Coordination result structure"""
    success: bool
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[float] = None


class ServiceCoordinator:
    """
    Central Hub service coordination manager
    Handles inter-service communication and workflow coordination
    """

    def __init__(self, service_registry: Dict[str, Dict[str, Any]], db_manager=None):
        self.service_registry = service_registry
        self.db_manager = db_manager
        self.active_coordinations: Dict[str, ServiceCoordinationRequest] = {}
        self.coordination_history: List[CoordinationResult] = []
        self.logger = logger

    async def coordinate_service_request(self, request: ServiceCoordinationRequest) -> CoordinationResult:
        """
        Coordinate a request between services
        """
        start_time = time.time()

        try:
            # Validate source and target services
            if not await self._validate_services(request.source_service, request.target_service):
                return CoordinationResult(
                    success=False,
                    error_message=f"Invalid services: {request.source_service} -> {request.target_service}",
                    execution_time_ms=(time.time() - start_time) * 1000
                )

            # Store active coordination
            self.active_coordinations[request.correlation_id] = request

            # Execute coordination
            result = await self._execute_coordination(request)

            # Clean up
            self.active_coordinations.pop(request.correlation_id, None)

            # Record result
            result.execution_time_ms = (time.time() - start_time) * 1000
            self.coordination_history.append(result)

            return result

        except Exception as e:
            self.logger.error(f"Coordination failed: {str(e)}")
            return CoordinationResult(
                success=False,
                error_message=str(e),
                execution_time_ms=(time.time() - start_time) * 1000
            )

    async def _validate_services(self, source: str, target: str) -> bool:
        """Validate that services exist and are healthy"""
        return (
            source in self.service_registry and
            target in self.service_registry and
            self.service_registry[source].get('status') == 'active' and
            self.service_registry[target].get('status') == 'active'
        )

    async def _execute_coordination(self, request: ServiceCoordinationRequest) -> CoordinationResult:
        """Execute the actual coordination logic"""

        # Real coordination logic based on operation type
        if request.operation == "data_sync":
            return await self._handle_data_sync(request)
        elif request.operation == "workflow_trigger":
            return await self._handle_workflow_trigger(request)
        elif request.operation == "health_check":
            return await self._handle_health_check(request)
        else:
            return await self._handle_custom_operation(request)

    async def _handle_data_sync(self, request: ServiceCoordinationRequest) -> CoordinationResult:
        """Handle real data synchronization between services"""
        self.logger.info(f"Data sync: {request.source_service} -> {request.target_service}")

        try:
            # Real data sync via HTTP call
            target_service = self.service_registry.get(request.target_service)
            if not target_service:
                raise Exception(f"Target service {request.target_service} not found")

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"http://{target_service['host']}:{target_service['port']}/sync/receive",
                    json=request.data,
                    timeout=request.timeout_seconds
                )
                response.raise_for_status()
                result = response.json()

            # DEPRECATED: Database coordination history removed (2025-10-16)
            # Reason: coordination_history table doesn't exist
            # Services use NATS/Kafka message tracking instead
            # if self.db_manager:
            #     await self.db_manager.execute(
            #         "INSERT INTO coordination_history (correlation_id, source_service, target_service, operation, status, result_data) VALUES ($1, $2, $3, $4, $5, $6)",
            #         {
            #             "correlation_id": request.correlation_id,
            #             "source_service": request.source_service,
            #             "target_service": request.target_service,
            #             "operation": request.operation,
            #             "status": "completed",
            #             "result_data": result
            #         }
            #     )

            return CoordinationResult(
                success=True,
                result_data=result
            )

        except Exception as e:
            self.logger.error(f"Data sync failed: {str(e)}")
            return CoordinationResult(
                success=False,
                error_message=str(e)
            )

    async def _handle_workflow_trigger(self, request: ServiceCoordinationRequest) -> CoordinationResult:
        """Handle real workflow triggering between services"""
        self.logger.info(f"Workflow trigger: {request.source_service} -> {request.target_service}")

        try:
            # Real workflow trigger via HTTP call
            target_service = self.service_registry.get(request.target_service)
            if not target_service:
                raise Exception(f"Target service {request.target_service} not found")

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"http://{target_service['host']}:{target_service['port']}/workflow/trigger",
                    json=request.data,
                    timeout=request.timeout_seconds
                )
                response.raise_for_status()
                result = response.json()

            return CoordinationResult(
                success=True,
                result_data=result
            )

        except Exception as e:
            self.logger.error(f"Workflow trigger failed: {str(e)}")
            return CoordinationResult(
                success=False,
                error_message=str(e)
            )

    async def _handle_health_check(self, request: ServiceCoordinationRequest) -> CoordinationResult:
        """Handle real health check coordination"""
        target_service = self.service_registry.get(request.target_service)

        if not target_service:
            return CoordinationResult(
                success=False,
                error_message=f"Service not found: {request.target_service}"
            )

        try:
            # Real health check via HTTP call
            async with httpx.AsyncClient() as client:
                health_url = f"http://{target_service['host']}:{target_service['port']}{target_service.get('health_endpoint', '/health')}"
                response = await client.get(health_url, timeout=5.0)
                response.raise_for_status()
                health_data = response.json()

            return CoordinationResult(
                success=True,
                result_data={
                    "service": request.target_service,
                    "status": "healthy",
                    "health_data": health_data,
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                }
            )

        except Exception as e:
            return CoordinationResult(
                success=False,
                error_message=f"Health check failed: {str(e)}"
            )

    async def _handle_custom_operation(self, request: ServiceCoordinationRequest) -> CoordinationResult:
        """Handle custom operation via direct service call"""
        target_service = self.service_registry.get(request.target_service)
        if not target_service:
            return CoordinationResult(
                success=False,
                error_message=f"Target service {request.target_service} not found"
            )

        try:
            # Real custom operation via HTTP call
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"http://{target_service['host']}:{target_service['port']}/{request.operation}",
                    json=request.data,
                    timeout=request.timeout_seconds
                )
                response.raise_for_status()
                result = response.json()

            return CoordinationResult(
                success=True,
                result_data=result
            )

        except Exception as e:
            self.logger.error(f"Custom operation {request.operation} failed: {str(e)}")
            return CoordinationResult(
                success=False,
                error_message=str(e)
            )

    def get_coordination_stats(self) -> Dict[str, Any]:
        """Get coordination statistics"""
        successful_coordinations = sum(1 for result in self.coordination_history if result.success)

        return {
            "active_coordinations": len(self.active_coordinations),
            "total_coordinations": len(self.coordination_history),
            "successful_coordinations": successful_coordinations,
            "success_rate": successful_coordinations / len(self.coordination_history) if self.coordination_history else 0,
            "average_execution_time_ms": sum(
                result.execution_time_ms for result in self.coordination_history
                if result.execution_time_ms
            ) / len(self.coordination_history) if self.coordination_history else 0
        }