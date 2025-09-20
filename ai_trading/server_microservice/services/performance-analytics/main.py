"""
📊 Performance Analytics Microservice - AI Trading Performance Analysis
Enterprise-grade performance tracking and analytics for AI trading pipeline

FEATURES:
- Trade outcome analysis with detailed performance metrics
- Strategy effectiveness evaluation with AI-powered insights
- ROI/Sharpe ratio calculation and risk-adjusted returns
- Real-time performance monitoring and alerting
- Performance comparison across ML/DL/AI models
- Automated performance reporting and recommendations

MICROSERVICE INFRASTRUCTURE:
- Performance tracking for analytics operations
- Centralized error handling for performance data processing
- Event publishing for performance milestone notifications
- Enhanced logging with analytics-specific context
- Comprehensive validation for performance data integrity
- Advanced metrics tracking for analytics optimization
"""

import uvicorn
import sys
import os
import time
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

# Add src path to sys.path for proper imports
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# SERVICE-SPECIFIC INFRASTRUCTURE - PERFORMANCE-ANALYTICS SERVICE ONLY
from ...shared.infrastructure.core.logger_core import CoreLogger
from ...shared.infrastructure.core.config_core import CoreConfig
from ...shared.infrastructure.core.error_core import CoreErrorHandler
from ...shared.infrastructure.core.performance_core import CorePerformance
from ...shared.infrastructure.core.cache_core import CoreCache
from ...shared.infrastructure.optional.event_core import CoreEventManager
from ...shared.infrastructure.optional.validation_core import CoreValidator

# PERFORMANCE ANALYTICS API
from src.api.analytics_endpoints import router as analytics_router
from src.api.reporting_endpoints import router as reporting_router

# Initialize service-specific infrastructure for PERFORMANCE-ANALYTICS
config_core = CoreConfig("performance-analytics")
logger_core = CoreLogger("performance-analytics", "main")
error_handler = CoreErrorHandler("performance-analytics")
performance_core = CorePerformance("performance-analytics")
cache_core = CoreCache("performance-analytics", max_size=10000, default_ttl=300)  # Large cache for performance data
event_manager = CoreEventManager("performance-analytics")
validator = CoreValidator("performance-analytics")

# Service configuration
service_config = config_core.get_service_config()

# Enhanced logger for performance-analytics microservice
microservice_logger = logger_core

# Performance Analytics Complete State Management
class PerformanceAnalyticsServiceState:
    """Complete state management for performance analytics microservice"""
    
    def __init__(self):
        # Performance data cache
        self.performance_cache: Dict[str, Any] = {}
        self.analytics_metrics = {
            "total_trades_analyzed": 0,
            "successful_trades": 0,
            "failed_trades": 0,
            "total_performance_reports": 0,
            "ai_insights_generated": 0,
            "alerts_sent": 0
        }
        
        # Performance tracking
        self.service_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "total_response_time": 0.0,
            "peak_memory_usage": 0,
            "active_connections": 0
        }
        
        # Analytics-specific stats
        self.analytics_stats = {
            "startup_time": time.time(),
            "last_report_generated": None,
            "performance_calculations": 0,
            "ml_model_comparisons": 0,
            "roi_calculations": 0,
            "sharpe_ratio_calculations": 0
        }
        
        # Initialize performance tracking
        self.performance_tracker = performance_core
        
        microservice_logger.info("📊 Performance Analytics Service State initialized")

# Global service state
service_state = PerformanceAnalyticsServiceState()

def create_performance_analytics_app() -> FastAPI:
    """Create Performance Analytics FastAPI application with comprehensive configuration"""
    
    # Application configuration
    app_config = {
        "title": "Performance Analytics Microservice",
        "description": "AI Trading Performance Analysis and Reporting Service",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }
    
    app = FastAPI(**app_config)
    
    # CORS Configuration for performance analytics
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure based on deployment environment
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"]
    )
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Comprehensive health check for performance analytics service"""
        
        try:
            # Check service health
            current_time = time.time()
            uptime = current_time - service_state.analytics_stats["startup_time"]
            
            health_data = {
                "service": "performance-analytics",
                "status": "healthy",
                "version": "1.0.0",
                "uptime_seconds": uptime,
                "timestamp": datetime.now().isoformat(),
                "port": 8010,
                "performance_metrics": {
                    "total_requests": service_state.service_metrics["total_requests"],
                    "successful_requests": service_state.service_metrics["successful_requests"], 
                    "failed_requests": service_state.service_metrics["failed_requests"],
                    "success_rate": service_state.service_metrics["successful_requests"] / max(1, service_state.service_metrics["total_requests"]),
                    "average_response_time": service_state.service_metrics["average_response_time"]
                },
                "analytics_stats": {
                    "trades_analyzed": service_state.analytics_metrics["total_trades_analyzed"],
                    "reports_generated": service_state.analytics_metrics["total_performance_reports"],
                    "ai_insights_generated": service_state.analytics_metrics["ai_insights_generated"]
                }
            }
            
            return health_data
            
        except Exception as e:
            microservice_logger.error(f"Health check failed: {e}")
            return JSONResponse(
                status_code=503,
                content={
                    "service": "performance-analytics",
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint for performance analytics service"""
        return {
            "service": "performance-analytics",
            "version": "1.0.0",
            "description": "AI Trading Performance Analysis Service",
            "status": "operational",
            "endpoints": {
                "health": "/health",
                "analytics": "/api/v1/analytics/*",
                "reports": "/api/v1/reports/*",
                "docs": "/docs"
            },
            "capabilities": [
                "Trade performance analysis",
                "Strategy effectiveness evaluation", 
                "ROI and risk metrics calculation",
                "AI model performance comparison",
                "Automated performance reporting",
                "Real-time performance monitoring"
            ]
        }
    
    # Include API routers
    microservice_logger.info("🔧 Including Performance Analytics API routers...")
    
    # Analytics endpoints
    app.include_router(analytics_router, tags=["Performance Analytics"])
    microservice_logger.info(f"   Routes after Analytics: {len(app.routes)}")
    
    # Reporting endpoints  
    app.include_router(reporting_router, tags=["Performance Reporting"])
    microservice_logger.info(f"   Routes after Reporting: {len(app.routes)}")
    
    # Startup event
    @app.on_event("startup")
    async def startup_event():
        """Initialize performance analytics service on startup"""
        microservice_logger.info("🚀 Starting Performance Analytics Microservice...")
        
        # Initialize analytics components
        try:
            # TODO: Initialize database connections for performance data
            # TODO: Load historical performance data
            # TODO: Initialize AI models for performance insights
            
            service_state.analytics_stats["startup_time"] = time.time()
            microservice_logger.info("✅ Performance Analytics Service started successfully")
            
        except Exception as e:
            microservice_logger.error(f"❌ Failed to start Performance Analytics Service: {e}")
            raise
    
    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on service shutdown"""
        microservice_logger.info("🛑 Shutting down Performance Analytics Service...")
        
        # TODO: Save performance analytics state
        # TODO: Close database connections
        # TODO: Generate final performance report
        
        microservice_logger.info("✅ Performance Analytics Service shutdown complete")
    
    return app

# Create the application
app = create_performance_analytics_app()

if __name__ == "__main__":
    # Service configuration
    port = int(os.environ.get("PORT", 8010))
    host = os.environ.get("HOST", "0.0.0.0")
    log_level = os.environ.get("LOG_LEVEL", "info")
    
    microservice_logger.info(f"🚀 Starting Performance Analytics Microservice on {host}:{port}")
    
    # Configure uvicorn for production
    uvicorn_config = {
        "app": "main:app",
        "host": host,
        "port": port,
        "log_level": log_level,
        "reload": os.environ.get("ENVIRONMENT") == "development",
        "workers": 1,  # Single worker for microservice
        "access_log": True,
        "use_colors": True
    }
    
    try:
        uvicorn.run(**uvicorn_config)
    except Exception as e:
        microservice_logger.error(f"❌ Failed to start Performance Analytics Microservice: {e}")
        sys.exit(1)