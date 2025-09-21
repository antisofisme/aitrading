#!/usr/bin/env python3
"""
Central Hub Service - Port 8010

Phase 1 Infrastructure Migration Service

🎯 PURPOSE:
Business: Central service orchestration and coordination hub
Technical: Service registry, health monitoring, configuration management
Domain: Infrastructure/Central Management/Service Coordination

🔧 CAPABILITIES:
- Service orchestration and coordination
- Service registry and discovery
- Health monitoring and status aggregation
- Configuration management
- Basic logging without complex retention
- Port 8010 service setup

Phase 1 Focus: Infrastructure migration only, no AI/ML features
"""

import asyncio
import logging
import signal
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Import our infrastructure components
from src.infrastructure.core.config_manager import ConfigManager
from src.infrastructure.core.logger import setup_logger
from src.infrastructure.registry.service_registry import ServiceRegistry
from src.infrastructure.health.health_monitor import HealthMonitor
from src.api.health import health_router
from src.api.services import services_router
from src.api.config import config_router

# Global instances
config_manager = None
service_registry = None
health_monitor = None
logger = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    global config_manager, service_registry, health_monitor, logger
    
    # Startup
    try:
        # Initialize configuration
        config_manager = ConfigManager()
        await config_manager.initialize()
        
        # Setup logging
        logger = setup_logger(
            name="central-hub",
            level=config_manager.get("logging.level", "INFO"),
            log_file=config_manager.get("logging.file", "logs/central-hub.log")
        )
        
        logger.info("🚀 Starting Central Hub Service on port 8010")
        
        # Initialize service registry
        service_registry = ServiceRegistry(logger=logger)
        await service_registry.initialize()
        
        # Initialize health monitor
        health_monitor = HealthMonitor(
            service_registry=service_registry,
            logger=logger
        )
        await health_monitor.start()
        
        # Store instances in app state
        app.state.config_manager = config_manager
        app.state.service_registry = service_registry
        app.state.health_monitor = health_monitor
        app.state.logger = logger
        
        logger.info("✅ Central Hub Service initialized successfully")
        
        yield
        
    except Exception as e:
        if logger:
            logger.error(f"❌ Failed to initialize Central Hub Service: {e}")
        raise
    finally:
        # Shutdown
        if logger:
            logger.info("🛑 Shutting down Central Hub Service")
        
        if health_monitor:
            await health_monitor.stop()
        
        if service_registry:
            await service_registry.shutdown()
        
        if logger:
            logger.info("✅ Central Hub Service shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="Central Hub Service",
    description="Phase 1 Infrastructure Migration - Service Orchestration and Coordination",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, prefix="/api/v1/health", tags=["health"])
app.include_router(services_router, prefix="/api/v1/services", tags=["services"])
app.include_router(config_router, prefix="/api/v1/config", tags=["configuration"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Central Hub",
        "version": "1.0.0",
        "status": "operational",
        "port": 8010,
        "phase": "Phase 1 - Infrastructure Migration"
    }

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    try:
        return {
            "status": "healthy",
            "service": "central-hub",
            "port": 8010,
            "timestamp": health_monitor.get_current_timestamp() if health_monitor else None
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")

@app.get("/status")
async def get_status():
    """Get comprehensive service status"""
    try:
        if not all([service_registry, health_monitor]):
            raise HTTPException(status_code=503, detail="Service not fully initialized")
        
        # Get service registry status
        registry_status = await service_registry.get_all_services()
        
        # Get health monitor status
        health_status = await health_monitor.get_system_health()
        
        return {
            "service": "central-hub",
            "port": 8010,
            "phase": "Phase 1 - Infrastructure Migration",
            "registry": {
                "total_services": len(registry_status),
                "services": registry_status
            },
            "health": health_status,
            "timestamp": health_monitor.get_current_timestamp()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status retrieval failed: {str(e)}")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    if logger:
        logger.info(f"Received signal {signum}, shutting down gracefully...")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the service
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8010,
        reload=False,  # Set to True for development
        log_level="info"
    )
