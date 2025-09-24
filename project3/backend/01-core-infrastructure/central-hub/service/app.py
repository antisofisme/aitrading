#!/usr/bin/env python3
"""
Central Hub Service - Main Application
Provides runtime coordination, service discovery, dan system management
"""

import sys
import os
from pathlib import Path

# Add shared library to path
shared_path = Path(__file__).parent.parent / "shared"
sys.path.insert(0, str(shared_path))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging
from typing import Dict, Any

# Import shared utilities
from utils.base_service import BaseService, ServiceConfig
from utils.patterns.response_formatter import StandardResponse
from logging.error_dna.analyzer import ErrorDNA

# Import service components
from api.health import health_router
from api.discovery import discovery_router
from api.config import config_router
from api.metrics import metrics_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logging.info("🚀 Central Hub Service starting...")

    # Initialize service components
    await central_hub_service.startup()

    yield

    # Shutdown
    logging.info("🛑 Central Hub Service shutting down...")
    await central_hub_service.shutdown()


class CentralHubService(BaseService):
    """Central Hub coordination service"""

    def __init__(self):
        config = ServiceConfig(
            service_name="central-hub",
            version="3.0.0",
            port=7000,
            environment=os.getenv("ENVIRONMENT", "production")
        )
        super().__init__(config)

        self.error_analyzer = ErrorDNA("central-hub")
        self.service_registry: Dict[str, Dict[str, Any]] = {}

    async def startup(self):
        """Service startup initialization"""
        await super().startup()

        # Initialize service registry
        self.service_registry = {}

        # Initialize runtime components
        await self.initialize_runtime_components()

        self.logger.info("Central Hub Service initialized successfully")

    async def initialize_runtime_components(self):
        """Initialize runtime coordination components"""
        # TODO: Initialize service discovery, health monitor, load balancer, circuit breaker
        pass

    async def custom_health_checks(self):
        """Central Hub specific health checks"""
        return {
            "registered_services": len(self.service_registry),
            "runtime_components_active": True,  # TODO: Implement actual check
            "coordination_latency_ms": await self.get_avg_coordination_time(),
        }

    async def get_avg_coordination_time(self) -> float:
        """Get average coordination response time"""
        # TODO: Implement actual coordination time measurement
        return 1.5

    # Backend Coordination Methods
    async def get_service_endpoints(self, service_name: str) -> list:
        """Get available endpoints for a service"""
        service_info = self.service_registry.get(service_name, {})
        endpoints = service_info.get("endpoints", [])

        # Default placeholder if no endpoints registered
        if not endpoints:
            endpoints = [{"url": f"http://{service_name}:8000", "healthy": True}]

        return endpoints

    async def get_service_failure_rate(self, service_name: str, tenant_id: str = None) -> float:
        """Get failure rate for service (placeholder implementation)"""
        # TODO: Implement actual failure rate calculation from metrics
        return 0.05  # 5% default failure rate

    async def get_current_instances(self, service_name: str) -> int:
        """Get current running instances for service (placeholder)"""
        # TODO: Implement actual instance count from container orchestrator
        return 2  # Default 2 instances

    async def get_tenant_performance(self, tenant_id: str) -> dict:
        """Get performance metrics for specific tenant"""
        # TODO: Implement actual performance data collection
        return {
            "response_times": {"avg": 150, "p95": 300, "p99": 500},
            "throughput": {"requests_per_second": 50},
            "error_rates": {"rate": 0.02},
            "resource_usage": {"cpu": 0.3, "memory": 0.4}
        }

    async def get_workflow_services(self, workflow_id: str) -> list:
        """Get services involved in a workflow (placeholder)"""
        # TODO: Implement workflow service mapping
        return [
            {"name": "trading-engine", "priority": 1},
            {"name": "risk-management", "priority": 2},
            {"name": "notification-hub", "priority": 3}
        ]

    def get_current_timestamp(self) -> str:
        """Get current timestamp for coordination tracking"""
        import datetime
        return datetime.datetime.utcnow().isoformat() + "Z"


# Global service instance
central_hub_service = CentralHubService()

# Create FastAPI app
app = FastAPI(
    title="Central Hub Service",
    description="Centralized coordination and service discovery hub",
    version="3.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(discovery_router, prefix="/services", tags=["service-discovery"])
app.include_router(config_router, prefix="/config", tags=["configuration"])
app.include_router(metrics_router, prefix="/metrics", tags=["metrics"])

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    """Global exception handling dengan ErrorDNA"""
    error_analysis = central_hub_service.error_analyzer.analyze_error(
        error_message=str(exc),
        context={"endpoint": str(request.url), "method": request.method}
    )

    central_hub_service.logger.error(
        f"Central Hub error: {error_analysis.suggested_actions}",
        extra={"error_analysis": error_analysis.__dict__}
    )

    return StandardResponse.error_response(
        error_message=str(exc),
        correlation_id=getattr(request.state, "correlation_id", None),
        service_name="central-hub"
    )


# Backend Coordination Endpoints
@app.get("/services/discover/{service_name}")
async def ai_service_discovery(service_name: str, tenant_id: str = None):
    """AI-aware service discovery dengan ML prediction"""
    try:
        # Get available endpoints for service
        endpoints = await central_hub_service.get_service_endpoints(service_name)

        if not endpoints:
            return StandardResponse.error_response(
                error_message=f"Service {service_name} not found",
                service_name="central-hub"
            )

        # Simple health-based selection (ML prediction placeholder)
        healthy_endpoints = [ep for ep in endpoints if ep.get("healthy", True)]

        if not healthy_endpoints:
            return StandardResponse.error_response(
                error_message=f"No healthy endpoints for {service_name}",
                service_name="central-hub"
            )

        # Select best endpoint (round-robin for now, ML optimization later)
        optimal_endpoint = healthy_endpoints[0]

        return StandardResponse.success_response(
            data={
                "service_name": service_name,
                "recommended_endpoint": optimal_endpoint,
                "all_healthy_endpoints": healthy_endpoints,
                "tenant_context": tenant_id,
                "confidence": 0.95,  # Placeholder for ML confidence
                "connection_type": "direct_call",  # Caller connects directly
                "central_hub_role": "information_provider"
            },
            service_name="central-hub"
        )

    except Exception as e:
        central_hub_service.logger.error(f"Service discovery error: {e}")
        return StandardResponse.error_response(
            error_message=str(e),
            service_name="central-hub"
        )


@app.post("/coordination/circuit-breaker/{service_name}")
async def tenant_circuit_breaker(service_name: str, tenant_context: dict):
    """Tenant-aware circuit breaker dengan subscription-based thresholds"""
    try:
        subscription_tier = tenant_context.get("subscription_tier", "free")
        tenant_id = tenant_context.get("tenant_id")

        # Subscription-based thresholds
        thresholds = {
            "free": {"failure_rate": 0.5, "timeout": 60},
            "pro": {"failure_rate": 0.3, "timeout": 30},
            "enterprise": {"failure_rate": 0.1, "timeout": 10}
        }

        config = thresholds.get(subscription_tier, thresholds["free"])

        # Get service health metrics (placeholder implementation)
        failure_rate = await central_hub_service.get_service_failure_rate(service_name, tenant_id)

        should_break = failure_rate > config["failure_rate"]

        return StandardResponse.success_response(
            data={
                "service_name": service_name,
                "tenant_id": tenant_id,
                "subscription_tier": subscription_tier,
                "should_circuit_break": should_break,
                "current_failure_rate": failure_rate,
                "threshold": config["failure_rate"],
                "timeout_seconds": config["timeout"]
            },
            service_name="central-hub"
        )

    except Exception as e:
        central_hub_service.logger.error(f"Circuit breaker error: {e}")
        return StandardResponse.error_response(
            error_message=str(e),
            service_name="central-hub"
        )


@app.post("/services/scale/predict")
async def predictive_scaling(service_name: str, tenant_context: dict):
    """Predictive auto-scaling berdasarkan AI patterns"""
    try:
        tenant_id = tenant_context.get("tenant_id")
        subscription_tier = tenant_context.get("subscription_tier", "free")

        # Get current metrics (placeholder)
        current_instances = await central_hub_service.get_current_instances(service_name)

        # Simple scaling logic (ML prediction placeholder)
        scaling_limits = {
            "free": {"max_instances": 2},
            "pro": {"max_instances": 5},
            "enterprise": {"max_instances": 20}
        }

        max_allowed = scaling_limits.get(subscription_tier, scaling_limits["free"])["max_instances"]
        recommended = min(current_instances + 1, max_allowed)  # Simple +1 logic

        return StandardResponse.success_response(
            data={
                "service_name": service_name,
                "tenant_id": tenant_id,
                "current_instances": current_instances,
                "recommended_instances": recommended,
                "max_allowed_instances": max_allowed,
                "confidence": 0.85,  # ML confidence placeholder
                "scaling_reason": "predictive_load_increase"
            },
            service_name="central-hub"
        )

    except Exception as e:
        central_hub_service.logger.error(f"Predictive scaling error: {e}")
        return StandardResponse.error_response(
            error_message=str(e),
            service_name="central-hub"
        )


@app.get("/monitoring/tenant/{tenant_id}/performance")
async def tenant_performance_metrics(tenant_id: str):
    """Per-tenant performance monitoring"""
    try:
        # Get tenant metrics (placeholder implementation)
        performance_data = await central_hub_service.get_tenant_performance(tenant_id)

        return StandardResponse.success_response(
            data={
                "tenant_id": tenant_id,
                "response_times": performance_data.get("response_times", {}),
                "throughput": performance_data.get("throughput", {}),
                "error_rates": performance_data.get("error_rates", {}),
                "resource_usage": performance_data.get("resource_usage", {}),
                "optimization_suggestions": [
                    "Consider upgrading to Pro tier for better performance",
                    "Enable caching for frequently accessed data"
                ]
            },
            service_name="central-hub"
        )

    except Exception as e:
        central_hub_service.logger.error(f"Performance monitoring error: {e}")
        return StandardResponse.error_response(
            error_message=str(e),
            service_name="central-hub"
        )


@app.post("/coordination/workflow/{workflow_id}")
async def coordinate_backend_workflow(workflow_id: str, tenant_context: dict):
    """Backend service coordination untuk complex workflows"""
    try:
        tenant_id = tenant_context.get("tenant_id")

        # Get workflow services (placeholder)
        workflow_services = await central_hub_service.get_workflow_services(workflow_id)

        coordination_results = []
        for service in workflow_services:
            # Check service health
            endpoints = await central_hub_service.get_service_endpoints(service["name"])
            healthy_endpoints = [ep for ep in endpoints if ep.get("healthy", True)]

            coordination_results.append({
                "service_name": service["name"],
                "status": "healthy" if healthy_endpoints else "unhealthy",
                "assigned_endpoint": healthy_endpoints[0] if healthy_endpoints else None,
                "tenant_context_applied": True
            })

        return StandardResponse.success_response(
            data={
                "workflow_id": workflow_id,
                "tenant_id": tenant_id,
                "coordination_plan": coordination_results,
                "connection_pattern": "direct_service_calls",
                "central_hub_role": "coordination_planner_only",
                "coordination_timestamp": central_hub_service.get_current_timestamp()
            },
            service_name="central-hub"
        )

    except Exception as e:
        central_hub_service.logger.error(f"Workflow coordination error: {e}")
        return StandardResponse.error_response(
            error_message=str(e),
            service_name="central-hub"
        )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "central-hub",
        "version": "3.0.0",
        "status": "active",
        "description": "Centralized coordination and service discovery hub",
        "endpoints": {
            "health": "/health",
            "service_discovery": "/services",
            "configuration": "/config",
            "metrics": "/metrics",
            "ai_service_discovery": "/services/discover/{service_name}",
            "circuit_breaker": "/coordination/circuit-breaker/{service_name}",
            "predictive_scaling": "/services/scale/predict",
            "tenant_performance": "/monitoring/tenant/{tenant_id}/performance",
            "workflow_coordination": "/coordination/workflow/{workflow_id}"
        }
    }


if __name__ == "__main__":
    # Run the service
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=7000,
        reload=os.getenv("ENVIRONMENT") == "development",
        log_level="info"
    )