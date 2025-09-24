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
            "metrics": "/metrics"
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