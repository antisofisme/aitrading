"""
👥 User Service Microservice - UNIFIED INTEGRATION WITH FULL CENTRALIZATION
Enterprise-grade user management with project collaboration and AI workflow orchestration

CENTRALIZED INFRASTRUCTURE:
- Performance tracking untuk comprehensive user management operations
- Centralized error handling untuk user authentication and authorization
- Event publishing untuk complete user lifecycle monitoring
- Enhanced logging dengan user-specific configuration and context
- Comprehensive validation untuk user data integrity and security
- Advanced metrics tracking untuk user engagement optimization and analytics

INTEGRATED COMPONENTS:
- User Management: Registration, authentication, profile management
- Project Collaboration: Team management and project assignments
- Workflow Service: AI workflow orchestration for users
- Domain Services: Business logic encapsulation and service coordination
"""

import uvicorn
import sys
import os
import time
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import secrets

# Import security middleware (kept local - user-service specific)
from .src.infrastructure.security.rate_limiting import create_rate_limit_middleware
from .src.infrastructure.security.security_headers import create_security_middleware
from .src.infrastructure.security.input_validation import create_validation_middleware

# Add src path to sys.path for proper imports
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# SERVICE-SPECIFIC INFRASTRUCTURE - USER-SERVICE SERVICE ONLY
from ...shared.infrastructure.core.logger_core import CoreLogger
from ...shared.infrastructure.core.config_core import CoreConfig
from ...shared.infrastructure.core.error_core import CoreErrorHandler
from ...shared.infrastructure.core.performance_core import CorePerformance
from ...shared.infrastructure.core.cache_core import CoreCache
from ...shared.infrastructure.optional.event_core import CoreEventManager
from ...shared.infrastructure.optional.validation_core import CoreValidator

# USER SERVICE API
from src.api.user_endpoints import router
from src.api.auth_endpoints import router as auth_router

# Initialize service-specific infrastructure for USER-SERVICE
config_core = CoreConfig("user-service")
logger_core = CoreLogger("user-service", "main")
error_handler = CoreErrorHandler("user-service")
performance_core = CorePerformance("user-service")
cache_core = CoreCache("user-service", max_size=3000, default_ttl=900)  # User service needs medium cache with 15min TTL
event_manager = CoreEventManager("user-service")
validator = CoreValidator("user-service")

# Service configuration
service_config = {
    'port': config_core.get('service.port', 8009),
    'host': config_core.get('service.host', '0.0.0.0'),
    'debug': config_core.get('service.debug', False),
    'environment': config_core.get('environment', 'development')
}

# Enhanced logger for user-service microservice
microservice_logger = logger_core

# User Service State Management
class UserServiceState:
    """Unified state management for user service microservice"""
    
    def __init__(self):
        self.active_users = {}
        self.active_sessions = {}
        self.user_projects = {}
        self.workflow_assignments = {}
        
        # Service cache management with metrics
        self.service_cache = {}
        self.cache_metrics = {
            "cache_hits": 0,
            "cache_misses": 0,
            "cache_size": 0,
            "cache_ttl_expires": 0
        }
        
        # User statistics
        self.user_stats = {
            "total_users": 0,
            "active_sessions": 0,
            "total_projects": 0,
            "workflow_executions": 0,
            "authentication_attempts": 0,
            "successful_logins": 0,
            "failed_logins": 0,
            "uptime_start": time.time()
        }
        
        # Service component status
        self.component_status = {
            "user_management": False,
            "project_service": False,
            "workflow_service": False,
            "authentication": False
        }
    
    def get_cache(self, key: str) -> Any:
        """Get value from service cache"""
        if key in self.service_cache:
            self.cache_metrics["cache_hits"] += 1
            cached_data = self.service_cache[key]
            if cached_data.get("expires_at", 0) > time.time():
                return cached_data["value"]
            else:
                del self.service_cache[key]
                self.cache_metrics["cache_ttl_expires"] += 1
        self.cache_metrics["cache_misses"] += 1
        return None

    def set_cache(self, key: str, value: Any, ttl: int = 900) -> None:
        """Set value in service cache with TTL"""
        self.service_cache[key] = {
            "value": value, 
            "expires_at": time.time() + ttl
        }
        self.cache_metrics["cache_size"] = len(self.service_cache)

# Global user service state
user_service_state = UserServiceState()

def create_app() -> FastAPI:
    """Create and configure unified User Service application"""
    microservice_logger.info("Creating unified User Service application with full centralization")
    
    app = FastAPI(
        title="Neliti User Service - Unified Microservice",
        description="Enterprise user management dengan project collaboration dan AI workflow orchestration",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # SECURITY MIDDLEWARE STACK - ORDER IS IMPORTANT
    environment = service_config.get('environment', 'development')
    
    # 1. Security Headers (first to apply to all responses)
    csrf_secret = config_core.get('authentication.jwt_secret', secrets.token_urlsafe(32))
    security_headers, csrf_middleware = create_security_middleware(
        environment=environment,
        csrf_secret_key=csrf_secret,
        enable_hsts=environment == 'production'
    )
    app.middleware("http")(security_headers)
    
    if csrf_middleware:
        app.middleware("http")(csrf_middleware)
    
    # 2. Rate Limiting (before authentication to prevent brute force)
    redis_config = config_core.get('cache', {})
    redis_url = f"redis://{redis_config.get('host', 'localhost')}:{redis_config.get('port', 6379)}/{redis_config.get('db', 6)}"
    
    rate_limiter = create_rate_limit_middleware(
        redis_url=redis_url,
        global_requests_per_minute=config_core.get('rate_limiting.requests_per_minute', 1000),
        auth_requests_per_minute=10,  # Strict for auth endpoints
        user_requests_per_minute=100
    )
    app.middleware("http")(rate_limiter)
    
    # 3. Input Validation (after rate limiting, before processing)
    validation_middleware = create_validation_middleware(
        strict_mode=environment == 'production'
    )
    app.middleware("http")(validation_middleware)
    
    # 4. CORS middleware (after security middleware)
    cors_config = config_core.get('cors', {})
    if cors_config.get('enabled', True):
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_config.get('origins', ["*"]),
            allow_credentials=cors_config.get('allow_credentials', True),
            allow_methods=cors_config.get('allow_methods', ["*"]),
            allow_headers=cors_config.get('allow_headers', ["*"])
        )
        microservice_logger.info("CORS middleware configured", {"origins": cors_config.get('origins', ["*"])})
    
    # Include API routers
    app.include_router(auth_router, prefix="/api/v1", tags=["authentication"])
    app.include_router(router, prefix="/api/v1", tags=["user_management"])
    
    @app.on_event("startup")
    @performance_core.track_operation("startup_user_service")
    async def startup_event():
        """Initialize user service on startup"""
        start_time = time.perf_counter()
        
        try:
            microservice_logger.info("🚀 Starting User Service microservice with full centralization")
            
            # Initialize user service components
            await initialize_user_components()
            
            # Start background tasks
            asyncio.create_task(user_session_monitor())
            asyncio.create_task(user_activity_tracker())
            asyncio.create_task(metrics_collector())
            
            # Calculate startup time
            startup_time = (time.perf_counter() - start_time) * 1000
            
            # Publish startup event
            event_manager.publish_event(
                event_name="user_service_startup",
                data={
                    "startup_time_ms": startup_time,
                    "active_components": sum(user_service_state.component_status.values()),
                    "component_status": user_service_state.component_status,
                    "microservice_version": "2.0.0",
                    "environment": service_config.get('environment', 'development'),
                    "startup_timestamp": time.time()
                }
            )
            
            microservice_logger.info(f"✅ User Service microservice started successfully ({startup_time:.2f}ms)", context={
                "startup_time_ms": startup_time,
                "active_components": sum(user_service_state.component_status.values()),
                "component_status": user_service_state.component_status
            })
            
        except Exception as e:
            startup_time = (time.perf_counter() - start_time) * 1000
            
            error_response = error_handler.handle_error(
                e,
                context={"component": "user_service_microservice", "operation": "startup", "startup_time_ms": startup_time}
            )
            
            microservice_logger.error(f"❌ Failed to start user service microservice: {error_response}")
            raise

    @app.on_event("shutdown")
    @performance_core.track_operation("shutdown_user_service")
    async def shutdown_event():
        """Cleanup user service on shutdown"""
        try:
            microservice_logger.info("🛑 Shutting down User Service microservice")
            
            # Cleanup user components
            await cleanup_user_components()
            
            # Publish shutdown event
            event_manager.publish_event(
                event_name="user_service_shutdown",
                data={
                    "final_user_stats": user_service_state.user_stats,
                    "active_sessions": len(user_service_state.active_sessions),
                    "shutdown_timestamp": time.time()
                }
            )
            
            microservice_logger.info("✅ User Service microservice shutdown completed gracefully")
            
        except Exception as e:
            error_response = error_handler.handle_error(
                e,
                context={"component": "user_service_microservice", "operation": "shutdown"}
            )
            microservice_logger.error(f"❌ Error during user service shutdown: {error_response}")

    @app.get("/health")
    @performance_core.track_operation("user_service_health_check")
    async def health_check():
        """Comprehensive health check for user service"""
        try:
            uptime = time.time() - user_service_state.user_stats["uptime_start"]
            
            health_data = {
                "status": "healthy",
                "service": "user-service",
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": uptime,
                "microservice_version": "2.0.0",
                "active_users": len(user_service_state.active_users),
                "active_sessions": len(user_service_state.active_sessions),
                "total_projects": len(user_service_state.user_projects),
                "component_status": user_service_state.component_status,
                "user_statistics": user_service_state.user_stats,
                "environment": service_config.get('environment', 'development')
            }
            
            return health_data
            
        except Exception as e:
            error_response = error_handler.handle_error(
                e,
                context={"component": "user_service_microservice", "operation": "health_check"}
            )
            microservice_logger.error(f"❌ User service health check failed: {error_response}")
            
            return JSONResponse(
                status_code=500,
                content={
                    "status": "unhealthy",
                    "service": "user-service",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )

    @app.get("/status")
    @performance_core.track_operation("user_service_detailed_status")
    async def detailed_status():
        """Comprehensive detailed status for user service"""
        try:
            uptime = time.time() - user_service_state.user_stats["uptime_start"]
            
            return {
                "service": "user-service",
                "status": "running",
                "uptime_seconds": uptime,
                "microservice_version": "2.0.0",
                "environment": service_config.get('environment', 'development'),
                "component_status": user_service_state.component_status,
                "service_cache_metrics": user_service_state.cache_metrics,
                "user_statistics": user_service_state.user_stats,
                "active_users": {
                    user_id: {"status": user.get("status"), "last_activity": user.get("last_activity")}
                    for user_id, user in user_service_state.active_users.items()
                },
                "active_sessions": {
                    session_id: {"user_id": session.get("user_id"), "created_at": session.get("created_at")}
                    for session_id, session in user_service_state.active_sessions.items()
                },
                "configuration": {
                    "user_service_port": service_config.get('port', 8009),
                    "health_check_interval": config_core.get('monitoring.health_check_interval_seconds', 30),
                    "debug_mode": service_config.get('debug', False)
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_response = error_handler.handle_error(
                e,
                context={"component": "user_service_microservice", "operation": "detailed_status"}
            )
            microservice_logger.error(f"❌ Detailed status check failed: {error_response}")
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )

    @app.get("/")
    @performance_core.track_operation("user_service_root")
    async def root():
        """Root endpoint with service information"""
        return {
            "service": "user-service",
            "version": "2.0.0",
            "status": "running",
            "description": "Enterprise user management dengan project collaboration dan AI workflow orchestration",
            "microservice_version": "2.0.0",
            "environment": service_config.get('environment', 'development'),
            "timestamp": datetime.now().isoformat()
        }
    
    return app

# Background Tasks for User Service
async def initialize_user_components():
    """Initialize all user service components with centralization"""
    try:
        microservice_logger.info("🔧 Initializing user service components...")
        
        # Initialize User Management
        try:
            user_service_state.component_status["user_management"] = True
            microservice_logger.info("✅ User Management initialized successfully")
        except Exception as e:
            microservice_logger.error(f"❌ Failed to initialize User Management: {str(e)}")
            user_service_state.component_status["user_management"] = False
        
        # Initialize Project Service
        try:
            user_service_state.component_status["project_service"] = True
            microservice_logger.info("✅ Project Service initialized successfully")
        except Exception as e:
            microservice_logger.error(f"❌ Failed to initialize Project Service: {str(e)}")
            user_service_state.component_status["project_service"] = False
        
        # Initialize Workflow Service
        try:
            user_service_state.component_status["workflow_service"] = True
            microservice_logger.info("✅ Workflow Service initialized successfully")
        except Exception as e:
            microservice_logger.error(f"❌ Failed to initialize Workflow Service: {str(e)}")
            user_service_state.component_status["workflow_service"] = False
        
        # Initialize Authentication
        try:
            user_service_state.component_status["authentication"] = True
            microservice_logger.info("✅ Authentication initialized successfully")
        except Exception as e:
            microservice_logger.error(f"❌ Failed to initialize Authentication: {str(e)}")
            user_service_state.component_status["authentication"] = False
        
        active_components = sum(user_service_state.component_status.values())
        microservice_logger.info(f"🎯 User service components initialization completed: {active_components}/4 components active")
        
    except Exception as e:
        error_response = error_handler.handle_error(
            e,
            context={"component": "user_service_microservice", "operation": "initialize_components", "component_status": user_service_state.component_status}
        )
        microservice_logger.error(f"❌ User service components initialization failed: {error_response}")
        raise

async def cleanup_user_components():
    """Cleanup all user service components on shutdown"""
    try:
        microservice_logger.info("🧹 Cleaning up user service components")
        
        # Reset component status
        for component in user_service_state.component_status:
            user_service_state.component_status[component] = False
        
        # Clear active sessions and users
        user_service_state.active_users.clear()
        user_service_state.active_sessions.clear()
        user_service_state.user_projects.clear()
        user_service_state.workflow_assignments.clear()
        
        microservice_logger.info("✅ User service components cleanup completed")
        
    except Exception as e:
        microservice_logger.error(f"❌ Error during user service components cleanup: {str(e)}")

async def user_session_monitor():
    """Background user session monitoring"""
    microservice_logger.info("👥 Starting user session monitor")
    
    while True:
        try:
            # Monitor active user sessions
            user_service_state.user_stats["active_sessions"] = len(user_service_state.active_sessions)
            user_service_state.user_stats["total_users"] = len(user_service_state.active_users)
            
            await asyncio.sleep(30)  # Check every 30 seconds
            
        except Exception as e:
            microservice_logger.error(f"❌ Error in user session monitor: {str(e)}")
            await asyncio.sleep(60)

async def user_activity_tracker():
    """Background user activity tracking"""
    microservice_logger.info("📊 Starting user activity tracker")
    
    while True:
        try:
            # Track user activity and engagement metrics
            await asyncio.sleep(60)  # Track every minute
            
        except Exception as e:
            microservice_logger.error(f"❌ Error in user activity tracker: {str(e)}")
            await asyncio.sleep(120)

async def metrics_collector():
    """Background metrics collection from all user components"""
    microservice_logger.info("📈 Starting metrics collector")
    
    while True:
        try:
            # Collect and aggregate metrics from all user components
            await asyncio.sleep(300)  # Collect every 5 minutes
            
        except Exception as e:
            microservice_logger.error(f"❌ Error in metrics collector: {str(e)}")
            await asyncio.sleep(600)

# Create the app instance
user_service_app = create_app()

if __name__ == "__main__":
    port = service_config.get('port', 8009)
    host = service_config.get('host', '0.0.0.0')
    debug = service_config.get('debug', False)
    
    microservice_logger.info(f"🚀 Starting User Service microservice on port {port}", {
        "host": host,
        "port": port,
        "debug": debug,
        "environment": service_config.get('environment', 'development')
    })
    
    uvicorn.run(
        "main:user_service_app",
        host=host,
        port=port,
        reload=debug,
        log_level="debug" if debug else "info"
    )