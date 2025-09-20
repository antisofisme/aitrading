"""
🎯 Strategy Optimization Microservice - AI Trading Strategy Development
Intelligent strategy development and optimization for AI trading pipeline

FEATURES:
- Strategy backtesting with historical data validation
- Parameter optimization using genetic algorithms
- Risk-adjusted strategy performance evaluation
- Multi-objective optimization (profit, risk, drawdown)
- Strategy comparison and selection framework
- Real-time strategy adaptation and learning

MICROSERVICE INFRASTRUCTURE:
- Performance tracking for strategy optimization operations
- Centralized error handling for strategy development
- Event publishing for strategy milestone notifications
- Enhanced logging with optimization-specific context
- Comprehensive validation for strategy parameters
- Advanced metrics tracking for optimization convergence
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

# REAL BUSINESS LOGIC IMPORTS
try:
    # Business Logic Components
    from src.business.strategy_manager import StrategyManager
    from src.business.genetic_algorithm import GeneticAlgorithmEngine
    from src.business.backtest_engine import BacktestEngine
    from src.business.parameter_optimizer import ParameterOptimizer
    from src.business.strategy_templates import StrategyTemplateManager
    
    # Database Integration
    from src.database.database_manager import DatabaseManager
    
    # API Endpoints
    from src.api.strategy_endpoints import (
        StrategyEndpoints, CreateStrategyRequest, UpdateStrategyRequest,
        OptimizeStrategyRequest, BacktestStrategyRequest, CompareStrategiesRequest
    )
    from src.api.optimization_endpoints import OptimizationEndpoints
    from src.api.template_endpoints import TemplateEndpoints, CreateFromTemplateRequest
    
    # Data Models
    from src.models.strategy_models import StrategyType, StrategyStatus, OptimizationObjective
    
    business_logic_available = True
    
except ImportError as e:
    print(f"Business logic imports failed, falling back to infrastructure: {e}")
    business_logic_available = False

# SERVICE-SPECIFIC INFRASTRUCTURE - STRATEGY-OPTIMIZATION SERVICE ONLY
try:
    from ...shared.infrastructure.core.logger_core import CoreLogger
    from ...shared.infrastructure.core.config_core import CoreConfig
    from ...shared.infrastructure.core.error_core import CoreErrorHandler
    from ...shared.infrastructure.core.performance_core import CorePerformance
    from ...shared.infrastructure.core.cache_core import CoreCache
    from ...shared.infrastructure.optional.event_core import CoreEventManager
    from ...shared.infrastructure.optional.validation_core import CoreValidator
    
    infrastructure_available = True
    
    # Initialize service-specific infrastructure for STRATEGY-OPTIMIZATION
    config_core = CoreConfig("strategy-optimization")
    logger_core = CoreLogger("strategy-optimization", "main")
    error_handler = CoreErrorHandler("strategy-optimization")
    performance_core = CorePerformance("strategy-optimization")
    cache_core = CoreCache("strategy-optimization", max_size=50000, default_ttl=600)  # Large cache for strategy data
    event_manager = CoreEventManager("strategy-optimization")
    validator = CoreValidator("strategy-optimization")
    
    # Service configuration
    service_config = config_core.get_service_config()
    
except Exception as e:
    print(f"Infrastructure setup failed, using fallback: {e}")
    infrastructure_available = False
    
    # Fallback logger
    class FallbackLogger:
        def info(self, msg, *args, **kwargs): print(f"INFO: {msg}")
        def error(self, msg, *args, **kwargs): print(f"ERROR: {msg}")
        def warning(self, msg, *args, **kwargs): print(f"WARNING: {msg}")
    
    logger_core = FallbackLogger()
    service_config = {
        "host": "0.0.0.0",
        "port": 8011,
        "debug": False,
        "environment": "development"
    }

# Enhanced logger for strategy-optimization microservice
microservice_logger = logger_core

# Strategy Optimization Complete State Management
class StrategyOptimizationServiceState:
    """Complete state management for strategy optimization microservice"""
    
    def __init__(self):
        # Strategy optimization cache
        self.strategy_cache: Dict[str, Any] = {}
        self.optimization_metrics = {
            "total_strategies_created": 0,
            "strategies_backtested": 0,
            "optimization_runs": 0,
            "best_strategy_profit": 0.0,
            "average_strategy_roi": 0.0,
            "strategies_deployed": 0,
            "parameter_combinations_tested": 0
        }
        
        # Service performance tracking
        self.service_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "total_response_time": 0.0,
            "peak_memory_usage": 0,
            "active_optimizations": 0
        }
        
        # Strategy optimization stats
        self.optimization_stats = {
            "startup_time": time.time(),
            "last_optimization_completed": None,
            "backtest_calculations": 0,
            "genetic_algorithm_generations": 0,
            "strategy_comparisons": 0,
            "parameter_optimizations": 0
        }
        
        # Business logic components
        self.strategy_manager = None
        self.genetic_algorithm = None
        self.backtest_engine = None
        self.parameter_optimizer = None
        self.template_manager = None
        self.database_manager = None
        
        # API endpoint handlers
        self.strategy_endpoints = None
        self.optimization_endpoints = None
        self.template_endpoints = None
        
        # Initialize performance tracking
        if infrastructure_available:
            self.performance_tracker = performance_core
        
        microservice_logger.info("🎯 Strategy Optimization Service State initialized")
    
    async def initialize_business_logic(self):
        """Initialize all business logic components"""
        
        if not business_logic_available:
            microservice_logger.warning("Business logic not available, using mock implementations")
            return
        
        try:
            # Database configuration
            db_config = {
                'postgres_host': os.getenv('POSTGRES_HOST', 'localhost'),
                'postgres_port': int(os.getenv('POSTGRES_PORT', 5432)),
                'postgres_database': os.getenv('POSTGRES_DATABASE', 'strategy_optimization'),
                'postgres_username': os.getenv('POSTGRES_USERNAME', 'postgres'),
                'postgres_password': os.getenv('POSTGRES_PASSWORD', 'password'),
                'redis_host': os.getenv('REDIS_HOST', 'localhost'),
                'redis_port': int(os.getenv('REDIS_PORT', 6379)),
                'cache_ttl': 3600,
                'compression_enabled': True
            }
            
            # Initialize database manager
            self.database_manager = DatabaseManager(db_config)
            await self.database_manager.initialize()
            
            # Initialize business components
            self.template_manager = StrategyTemplateManager()
            
            # Algorithm engines
            ga_config = {
                'population_size': 100,
                'generations': 50,
                'crossover_prob': 0.8,
                'mutation_prob': 0.2,
                'use_nsga2': True,
                'parallel_evaluation': True
            }
            self.genetic_algorithm = GeneticAlgorithmEngine(ga_config)
            
            # Backtest engine
            backtest_config = {
                'initial_cash': 10000.0,
                'commission': 0.001,
                'data_source': 'yahoo',
                'benchmark_symbol': 'SPY'
            }
            self.backtest_engine = BacktestEngine(backtest_config)
            
            # Parameter optimizer
            optimizer_config = {
                'n_trials': 100,
                'timeout': 3600,
                'sampler_type': 'tpe',
                'pruner_type': 'median'
            }
            self.parameter_optimizer = ParameterOptimizer(optimizer_config)
            
            # Strategy manager (main orchestrator)
            self.strategy_manager = StrategyManager(
                cache_manager=cache_core if infrastructure_available else None,
                database_manager=self.database_manager,
                config={'validation_enabled': True, 'ai_brain_compliance': True}
            )
            
            # Initialize API endpoints
            self.strategy_endpoints = StrategyEndpoints(
                strategy_manager=self.strategy_manager,
                template_manager=self.template_manager,
                genetic_algorithm=self.genetic_algorithm,
                backtest_engine=self.backtest_engine,
                parameter_optimizer=self.parameter_optimizer
            )
            
            self.optimization_endpoints = OptimizationEndpoints(
                genetic_algorithm=self.genetic_algorithm,
                parameter_optimizer=self.parameter_optimizer
            )
            
            self.template_endpoints = TemplateEndpoints(
                template_manager=self.template_manager
            )
            
            microservice_logger.info("✅ Business logic components initialized successfully")
            
        except Exception as e:
            microservice_logger.error(f"❌ Business logic initialization failed: {e}")
            # Continue with mock implementations
            self.strategy_endpoints = None
    
    async def shutdown_business_logic(self):
        """Cleanup business logic components"""
        
        try:
            if self.database_manager:
                await self.database_manager.close()
            
            microservice_logger.info("✅ Business logic components shutdown complete")
            
        except Exception as e:
            microservice_logger.error(f"❌ Business logic shutdown error: {e}")

# Global service state
service_state = StrategyOptimizationServiceState()

def create_strategy_optimization_app() -> FastAPI:
    """Create Strategy Optimization FastAPI application with comprehensive configuration"""
    
    # Application configuration
    app_config = {
        "title": "Strategy Optimization Microservice",
        "description": "AI Trading Strategy Development and Optimization Service",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }
    
    app = FastAPI(**app_config)
    
    # CORS Configuration for strategy optimization
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
        """Comprehensive health check for strategy optimization service"""
        
        try:
            # Check service health
            current_time = time.time()
            uptime = current_time - service_state.optimization_stats["startup_time"]
            
            health_data = {
                "service": "strategy-optimization",
                "status": "healthy",
                "version": "1.0.0",
                "uptime_seconds": uptime,
                "timestamp": datetime.now().isoformat(),
                "port": 8011,
                "infrastructure": "healthy" if infrastructure_available else "degraded",
                "performance_metrics": {
                    "total_requests": service_state.service_metrics["total_requests"],
                    "successful_requests": service_state.service_metrics["successful_requests"], 
                    "failed_requests": service_state.service_metrics["failed_requests"],
                    "success_rate": service_state.service_metrics["successful_requests"] / max(1, service_state.service_metrics["total_requests"]),
                    "average_response_time": service_state.service_metrics["average_response_time"]
                },
                "optimization_stats": {
                    "strategies_created": service_state.optimization_metrics["total_strategies_created"],
                    "optimization_runs": service_state.optimization_metrics["optimization_runs"],
                    "strategies_backtested": service_state.optimization_metrics["strategies_backtested"],
                    "active_optimizations": service_state.service_metrics["active_optimizations"]
                }
            }
            
            return health_data
            
        except Exception as e:
            microservice_logger.error(f"Health check failed: {e}")
            return JSONResponse(
                status_code=503,
                content={
                    "service": "strategy-optimization",
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint for strategy optimization service"""
        return {
            "service": "strategy-optimization",
            "version": "1.0.0",
            "description": "AI Trading Strategy Development and Optimization Service",
            "status": "operational",
            "endpoints": {
                "health": "/health",
                "optimization": "/api/v1/optimization/*",
                "strategies": "/api/v1/strategies/*",
                "backtesting": "/api/v1/backtest/*",
                "docs": "/docs"
            },
            "capabilities": [
                "Strategy backtesting with historical data",
                "Parameter optimization using genetic algorithms", 
                "Risk-adjusted performance evaluation",
                "Multi-objective optimization framework",
                "Strategy comparison and selection",
                "Real-time strategy adaptation"
            ]
        }
    
    # ==================== REAL STRATEGY OPTIMIZATION API ENDPOINTS ====================
    
    # Strategy Management Endpoints
    @app.post("/api/v1/strategies/create")
    async def create_strategy(
        request: CreateStrategyRequest,
        background_tasks: BackgroundTasks
    ):
        """Create new trading strategy with comprehensive validation"""
        if service_state.strategy_endpoints:
            service_state.optimization_metrics["total_strategies_created"] += 1
            service_state.service_metrics["successful_requests"] += 1
            return await service_state.strategy_endpoints.create_strategy(request, background_tasks)
        else:
            return await create_strategy_fallback()
    
    @app.get("/api/v1/strategies/{strategy_id}")
    async def get_strategy(strategy_id: str):
        """Retrieve strategy with comprehensive details"""
        if service_state.strategy_endpoints:
            return await service_state.strategy_endpoints.get_strategy(strategy_id)
        else:
            return await get_strategy_fallback(strategy_id)
    
    @app.put("/api/v1/strategies/{strategy_id}")
    async def update_strategy(
        strategy_id: str,
        request: UpdateStrategyRequest,
        background_tasks: BackgroundTasks
    ):
        """Update existing strategy with validation"""
        if service_state.strategy_endpoints:
            service_state.service_metrics["successful_requests"] += 1
            return await service_state.strategy_endpoints.update_strategy(strategy_id, request, background_tasks)
        else:
            return await update_strategy_fallback(strategy_id)
    
    @app.delete("/api/v1/strategies/{strategy_id}")
    async def delete_strategy(strategy_id: str):
        """Delete strategy with safety checks"""
        if service_state.strategy_endpoints:
            return await service_state.strategy_endpoints.delete_strategy(strategy_id)
        else:
            return await delete_strategy_fallback(strategy_id)
    
    @app.get("/api/v1/strategies")
    async def list_strategies(
        strategy_type: Optional[StrategyType] = None,
        status: Optional[StrategyStatus] = None,
        limit: int = 100,
        offset: int = 0
    ):
        """List strategies with filtering and pagination"""
        if service_state.strategy_endpoints:
            return await service_state.strategy_endpoints.list_strategies(strategy_type, status, limit, offset)
        else:
            return await list_strategies_fallback()
    
    # Optimization Endpoints
    @app.post("/api/v1/strategies/{strategy_id}/optimize")
    async def optimize_strategy(
        strategy_id: str,
        request: OptimizeStrategyRequest,
        background_tasks: BackgroundTasks
    ):
        """Run comprehensive strategy optimization"""
        if service_state.strategy_endpoints:
            service_state.optimization_metrics["optimization_runs"] += 1
            service_state.optimization_stats["parameter_optimizations"] += 1
            return await service_state.strategy_endpoints.optimize_strategy(strategy_id, request, background_tasks)
        else:
            return await optimize_strategy_fallback()
    
    @app.post("/api/v1/strategies/{strategy_id}/backtest")
    async def backtest_strategy(
        strategy_id: str,
        request: BacktestStrategyRequest,
        background_tasks: BackgroundTasks
    ):
        """Run comprehensive strategy backtesting"""
        if service_state.strategy_endpoints:
            service_state.optimization_metrics["strategies_backtested"] += 1
            service_state.optimization_stats["backtest_calculations"] += 1
            return await service_state.strategy_endpoints.backtest_strategy(strategy_id, request, background_tasks)
        else:
            return await backtest_strategy_fallback()
    
    @app.post("/api/v1/strategies/compare")
    async def compare_strategies(request: CompareStrategiesRequest):
        """Compare multiple strategies across various metrics"""
        if service_state.strategy_endpoints:
            service_state.optimization_stats["strategy_comparisons"] += 1
            return await service_state.strategy_endpoints.compare_strategies(request)
        else:
            return await compare_strategies_fallback()
    
    # Strategy Deployment Endpoints
    @app.post("/api/v1/strategies/{strategy_id}/deploy")
    async def deploy_strategy(strategy_id: str):
        """Deploy strategy for live trading"""
        if service_state.strategy_endpoints:
            service_state.optimization_metrics["strategies_deployed"] += 1
            return await service_state.strategy_endpoints.deploy_strategy(strategy_id)
        else:
            return await deploy_strategy_fallback(strategy_id)
    
    @app.post("/api/v1/strategies/{strategy_id}/pause")
    async def pause_strategy(strategy_id: str):
        """Pause active strategy"""
        if service_state.strategy_endpoints:
            return await service_state.strategy_endpoints.pause_strategy(strategy_id)
        else:
            return {"success": True, "message": "Strategy paused (mock)"}
    
    @app.post("/api/v1/strategies/{strategy_id}/retire")
    async def retire_strategy(strategy_id: str):
        """Retire strategy from active use"""
        if service_state.strategy_endpoints:
            return await service_state.strategy_endpoints.retire_strategy(strategy_id)
        else:
            return {"success": True, "message": "Strategy retired (mock)"}
    
    # Template Endpoints
    @app.get("/api/v1/templates")
    async def list_templates(
        strategy_type: Optional[StrategyType] = None,
        complexity_max: Optional[float] = None
    ):
        """List available strategy templates"""
        if service_state.template_endpoints:
            return await service_state.template_endpoints.list_templates(strategy_type, complexity_max)
        else:
            return await list_templates_fallback()
    
    @app.get("/api/v1/templates/{template_id}")
    async def get_template(template_id: str):
        """Get detailed template information"""
        if service_state.template_endpoints:
            return await service_state.template_endpoints.get_template(template_id)
        else:
            return await get_template_fallback(template_id)
    
    @app.post("/api/v1/templates/{template_id}/create-strategy")
    async def create_strategy_from_template(request: CreateFromTemplateRequest):
        """Create strategy instance from template"""
        if service_state.template_endpoints:
            service_state.optimization_metrics["total_strategies_created"] += 1
            return await service_state.template_endpoints.create_strategy_from_template(request)
        else:
            return await create_from_template_fallback(request)
    
    # Optimization Analysis Endpoints
    @app.get("/api/v1/optimizations/{optimization_id}")
    async def get_optimization_result(optimization_id: str):
        """Get detailed optimization results"""
        if service_state.optimization_endpoints:
            return await service_state.optimization_endpoints.get_optimization_result(optimization_id)
        else:
            return {"success": True, "optimization_id": optimization_id, "status": "completed (mock)"}
    
    @app.get("/api/v1/optimization/methods")
    async def list_optimization_methods():
        """List available optimization methods"""
        if service_state.optimization_endpoints:
            return await service_state.optimization_endpoints.list_optimization_methods()
        else:
            return {
                "success": True,
                "methods": ["NSGA-II", "Optuna-TPE", "Random-Search"],
                "message": "Mock optimization methods"
            }
    
    # Startup event
    @app.on_event("startup")
    async def startup_event():
        """Initialize strategy optimization service on startup"""
        microservice_logger.info("🚀 Starting Strategy Optimization Microservice...")
        
        # Initialize business logic components
        try:
            await service_state.initialize_business_logic()
            
            service_state.optimization_stats["startup_time"] = time.time()
            microservice_logger.info("✅ Strategy Optimization Service started successfully")
            
        except Exception as e:
            microservice_logger.error(f"❌ Failed to start Strategy Optimization Service: {e}")
            # Continue with fallback implementations
    
    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on service shutdown"""
        microservice_logger.info("🛑 Shutting down Strategy Optimization Service...")
        
        try:
            await service_state.shutdown_business_logic()
            microservice_logger.info("✅ Strategy Optimization Service shutdown complete")
            
        except Exception as e:
            microservice_logger.error(f"❌ Shutdown error: {e}")
    
    # ==================== FALLBACK IMPLEMENTATIONS ====================
    
    async def create_strategy_fallback():
        """Fallback strategy creation"""
        strategy_data = {
            "strategy_id": f"strategy_{int(time.time())}",
            "created_at": datetime.now().isoformat(),
            "status": "created",
            "message": "Created with fallback implementation"
        }
        return {"success": True, "strategy": strategy_data}
    
    async def get_strategy_fallback(strategy_id: str):
        """Fallback strategy retrieval"""
        return {
            "success": True,
            "strategy_id": strategy_id,
            "message": "Mock strategy data",
            "status": "active"
        }
    
    async def update_strategy_fallback(strategy_id: str):
        """Fallback strategy update"""
        return {"success": True, "message": "Strategy updated (mock)"}
    
    async def delete_strategy_fallback(strategy_id: str):
        """Fallback strategy deletion"""
        return {"success": True, "message": "Strategy deleted (mock)"}
    
    async def list_strategies_fallback():
        """Fallback strategy listing"""
        return {
            "success": True,
            "strategies": [],
            "message": "Mock strategy list"
        }
    
    async def optimize_strategy_fallback():
        """Fallback optimization"""
        return {
            "success": True,
            "message": "Optimization completed (mock)",
            "best_fitness": 0.145
        }
    
    async def backtest_strategy_fallback():
        """Fallback backtesting"""
        return {
            "success": True,
            "message": "Backtest completed (mock)",
            "total_return": 0.08
        }
    
    async def compare_strategies_fallback():
        """Fallback strategy comparison"""
        return {
            "success": True,
            "message": "Strategy comparison completed (mock)",
            "best_strategy": "strategy_001"
        }
    
    async def deploy_strategy_fallback(strategy_id: str):
        """Fallback strategy deployment"""
        return {"success": True, "message": "Strategy deployed (mock)"}
    
    async def list_templates_fallback():
        """Fallback template listing"""
        return {
            "success": True,
            "templates": [
                {"template_id": "sma_crossover_basic", "name": "SMA Crossover", "type": "momentum"},
                {"template_id": "rsi_mean_reversion", "name": "RSI Mean Reversion", "type": "mean_reversion"}
            ]
        }
    
    async def get_template_fallback(template_id: str):
        """Fallback template retrieval"""
        return {
            "success": True,
            "template_id": template_id,
            "name": "Mock Template",
            "description": "Fallback template implementation"
        }
    
    async def create_from_template_fallback(request):
        """Fallback template-based strategy creation"""
        return {
            "success": True,
            "strategy_id": f"template_strategy_{int(time.time())}",
            "message": "Strategy created from template (mock)"
        }
    
    return app

# Create the application
app = create_strategy_optimization_app()

if __name__ == "__main__":
    # Service configuration
    port = int(os.environ.get("PORT", 8011))
    host = os.environ.get("HOST", "0.0.0.0")
    log_level = os.environ.get("LOG_LEVEL", "info")
    
    microservice_logger.info(f"🚀 Starting Strategy Optimization Microservice on {host}:{port}")
    
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
        microservice_logger.error(f"❌ Failed to start Strategy Optimization Microservice: {e}")
        sys.exit(1)