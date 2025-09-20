"""
Trading Engine Service - AI-Powered Trading Execution and Risk Management

Enterprise-grade trading engine with AI integration, real-time execution,
and comprehensive risk management capabilities.
"""

import asyncio
import sys
import os
import time
import uvicorn
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import asdict
from pydantic import BaseModel, Field

# Add src path to sys.path for proper imports
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# SERVICE-SPECIFIC INFRASTRUCTURE - TRADING-ENGINE SERVICE ONLY
try:
    from ...shared.infrastructure.core.logger_core import CoreLogger
    from ...shared.infrastructure.core.config_core import CoreConfig
    from ...shared.infrastructure.core.error_core import CoreErrorHandler
    from ...shared.infrastructure.core.performance_core import CorePerformance
    from ...shared.infrastructure.optional.event_core import CoreEventManager
    
    # Initialize service-specific infrastructure for trading-engine
    config_core = CoreConfig("trading-engine")
    logger_core = CoreLogger("trading-engine", "main")
    error_handler = CoreErrorHandler("trading-engine")
    performance_core = CorePerformance("trading-engine")
    event_manager = CoreEventManager("trading-engine")
    
    # Service configuration
    service_config = config_core.get_config_summary()
    logger_core.info("Trading Engine infrastructure initialized successfully")
    
except Exception as e:
    print(f"Infrastructure setup failed, using fallback: {e}")
    # Fallback to basic logging
    class FallbackLogger:
        def info(self, msg, *args, **kwargs): print(f"INFO: {msg}")
        def error(self, msg, *args, **kwargs): print(f"ERROR: {msg}")
        def warning(self, msg, *args, **kwargs): print(f"WARNING: {msg}")
    
    logger_core = FallbackLogger()
    config_core = None
    service_config = {
        "host": "0.0.0.0",
        "port": 8007,
        "debug": False,
        "cors_origins": ["*"],
        "environment": "development"
    }

# Import AI Trading Engine Business Logic
try:
    from src.business.ai_trading_engine import (
        AiTradingEngine, AiTradingConfig, TradingOrder, TradingResult,
        TradingSignal, OrderType
    )
    trading_engine_available = True
    logger_core.info("AI Trading Engine business logic imported successfully")
except Exception as e:
    logger_core.error(f"AI Trading Engine import failed: {e}")
    trading_engine_available = False

# AI Brain Integration
try:
    from ..shared.ai_brain_trading_error_dna import trading_error_dna, TradingErrorContext
    from ..shared.ai_brain_confidence_framework import ai_brain_confidence, ConfidenceMetrics
    from ..shared.ai_brain_trading_decision_validator import ai_brain_trading_validator, TradingDecision, TradingDecisionType
    AI_BRAIN_AVAILABLE = True
    logger_core.info("AI Brain trading framework integrated successfully")
except Exception as e:
    logger_core.error(f"AI Brain integration failed: {e}")
    AI_BRAIN_AVAILABLE = False

# Global Trading Engine Instance
trading_engine_instance: Optional[AiTradingEngine] = None

# Pydantic Models for API
class TradePredictionRequest(BaseModel):
    """Request model for AI trade prediction"""
    symbol: str = Field(..., description="Trading symbol (e.g., EURUSD)")
    prediction: Dict[str, Any] = Field(..., description="AI prediction data")
    pattern_result: Optional[Dict[str, Any]] = Field(default=None, description="Pattern analysis result")
    confidence_threshold: Optional[float] = Field(default=0.75, description="Minimum confidence required")
    enable_ai_brain_validation: Optional[bool] = Field(default=True, description="Enable AI Brain validation")

class TradingConfigRequest(BaseModel):
    """Request model for trading configuration"""
    enable_ai_validation: bool = True
    ai_confidence_threshold: float = Field(ge=0.0, le=1.0, default=0.75)
    max_risk_per_trade: float = Field(ge=0.001, le=0.1, default=0.02)
    max_daily_risk: float = Field(ge=0.01, le=0.2, default=0.05)
    max_positions: int = Field(ge=1, le=20, default=5)

@performance_core.track_operation("create_trading_engine_app") if performance_core else lambda f: f
def create_app() -> FastAPI:
    """Create comprehensive Trading Engine FastAPI application"""
    logger_core.info("Creating AI-powered Trading Engine FastAPI application")
    
    app = FastAPI(
        title="Trading Engine Service - AI Trading Platform",
        description="Enterprise-grade AI trading execution with risk management",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Add CORS middleware based on configuration
    cors_config = service_config.get('cors', {}) if config_core else service_config
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_config.get("cors_origins", ["*"]),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Request logging middleware
    if performance_core:
        @app.middleware("http")
        async def log_requests(request, call_next):
            start_time = time.time()
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000
            logger_core.info(f"Request: {request.method} {request.url.path} - {response.status_code} ({process_time:.2f}ms)")
            return response
    
    @app.on_event("startup")
    async def startup_event():
        """Initialize Trading Engine on startup"""
        global trading_engine_instance
        try:
            logger_core.info("🚀 Starting Trading Engine Service with AI integration")
            
            if trading_engine_available:
                # Initialize AI Trading Engine
                config = AiTradingConfig(
                    enable_ai_validation=True,
                    ai_confidence_threshold=0.75,
                    max_risk_per_trade=0.02,
                    max_daily_risk=0.05,
                    max_positions=5
                )
                trading_engine_instance = AiTradingEngine(config)
                logger_core.info("✅ AI Trading Engine initialized successfully")
            else:
                logger_core.warning("⚠️ AI Trading Engine not available - running in limited mode")
            
            if event_manager:
                event_manager.publish_event(
                    event_type="trading_engine_startup",
                    component="trading_engine_main",
                    message="Trading Engine service started successfully",
                    data={
                        "ai_trading_available": trading_engine_available,
                        "version": "2.0.0",
                        "timestamp": time.time()
                    }
                )
                
            logger_core.info("✅ Trading Engine Service started successfully")
            
        except Exception as e:
            logger_core.error(f"❌ Failed to start Trading Engine Service: {e}")
            if error_handler:
                error_handler.handle_error(e, "trading_engine_startup", "startup_event")
            raise

    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup Trading Engine on shutdown"""
        global trading_engine_instance
        try:
            logger_core.info("🛑 Shutting down Trading Engine Service")
            
            if trading_engine_instance:
                await trading_engine_instance.cleanup()
                trading_engine_instance = None
                
            logger_core.info("✅ Trading Engine Service shutdown completed")
            
        except Exception as e:
            logger_core.error(f"❌ Error during Trading Engine shutdown: {e}")

    @app.get("/")
    async def root():
        """Root endpoint with comprehensive service information"""
        return {
            "service": "Trading Engine",
            "version": "2.0.0",
            "description": "AI-powered trading execution and risk management platform",
            "status": "operational",
            "timestamp": datetime.now().isoformat(),
            "features": {
                "ai_trading": trading_engine_available,
                "risk_management": True,
                "real_time_execution": True,
                "performance_analytics": True,
                "pattern_recognition": True
            },
            "endpoints": {
                "health": "/health",
                "docs": "/docs",
                "trading_api": "/api/v1/trading",
                "risk_metrics": "/api/v1/risk",
                "execute_trade": "/api/v1/trading/execute"
            }
        }
    
    @app.get("/health")
    async def health_check():
        """Comprehensive health check for trading engine"""
        try:
            uptime = time.time() - (hasattr(app, 'start_time') and app.start_time or time.time())
            
            health_data = {
                "service": "trading-engine",
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "2.0.0",
                "uptime_seconds": uptime,
                "environment": service_config.get('environment', 'development'),
                "components": {
                    "api": "healthy",
                    "ai_trading_engine": "healthy" if trading_engine_available and trading_engine_instance else "unavailable",
                    "infrastructure": "healthy" if config_core else "degraded",
                    "risk_management": "healthy",
                    "mt5_bridge_client": "healthy" if trading_engine_instance else "unavailable"
                }
            }
            
            return health_data
            
        except Exception as e:
            logger_core.error(f"❌ Health check failed: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "service": "trading-engine",
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )

    @app.get("/status")
    async def detailed_status():
        """Detailed status information"""
        try:
            status_data = {
                "service": "trading-engine",
                "status": "running",
                "version": "2.0.0",
                "timestamp": datetime.now().isoformat(),
                "configuration": {
                    "port": service_config.get('port', 8007),
                    "environment": service_config.get('environment', 'development'),
                    "debug": service_config.get('debug', False)
                },
                "ai_trading": {
                    "available": trading_engine_available,
                    "instance_active": trading_engine_instance is not None,
                    "config": trading_engine_instance.config.__dict__ if trading_engine_instance else {}
                }
            }
            
            if trading_engine_instance:
                risk_metrics = await trading_engine_instance.get_risk_metrics()
                status_data["risk_metrics"] = risk_metrics
                
            return status_data
            
        except Exception as e:
            logger_core.error(f"❌ Status check failed: {e}")
            return JSONResponse(status_code=500, content={"error": str(e)})

    # Import decision endpoints
    try:
        from src.api.decision_endpoints import router as decision_router
        app.include_router(decision_router, tags=["Decision Engine"])
        logger_core.info("✅ Decision endpoints imported successfully")
    except Exception as e:
        logger_core.error(f"❌ Failed to import decision endpoints: {e}")

    # === Trading API Endpoints ===
    
    @app.post("/api/v1/trading/execute")
    async def execute_ai_trade(request: TradePredictionRequest):
        """Execute AI-powered trade with AI Brain validation"""
        try:
            if not trading_engine_instance:
                raise HTTPException(status_code=503, detail="AI Trading Engine not available")
            
            logger_core.info(f"🤖 Executing AI Brain enhanced trade for {request.symbol}")
            
            # AI Brain Enhanced Trading Decision Validation
            ai_brain_analysis = None
            confidence_metrics = None
            validation_result = None
            
            if AI_BRAIN_AVAILABLE and request.enable_ai_brain_validation:
                try:
                    # Create trading decision for validation
                    trading_decision = TradingDecision(
                        decision_type=TradingDecisionType.OPEN_POSITION,
                        symbol=request.symbol,
                        action=request.prediction.get("action", "buy"),
                        position_size=request.prediction.get("position_size", 0.02),
                        confidence=request.prediction.get("confidence", 0.5),
                        reasoning=request.prediction.get("reasoning", "AI prediction based trade"),
                        risk_per_trade=request.prediction.get("risk_per_trade", 0.02),
                        stop_loss=request.prediction.get("stop_loss"),
                        take_profit=request.prediction.get("take_profit"),
                        strategy_id=request.prediction.get("strategy_id"),
                        ml_prediction=request.prediction.get("ml_results"),
                        dl_prediction=request.prediction.get("dl_results"),
                        ai_evaluation=request.prediction.get("ai_evaluation")
                    )
                    
                    # Validate trading decision
                    validation_result = await ai_brain_trading_validator.validate_trading_decision(
                        trading_decision,
                        context={
                            "account_balance": 10000,  # TODO: Get from account service
                            "open_positions": 2,       # TODO: Get from position manager
                            "daily_pnl": 0,           # TODO: Get from analytics
                            "historical_performance": {
                                "win_rate": 0.65,
                                "profit_factor": 1.8,
                                "max_drawdown": -0.08,
                                "total_trades": 150,
                                "recent_30_day_performance": 0.05
                            }
                        }
                    )
                    
                    logger_core.info(f"🛡️ AI Brain validation completed: {validation_result.confidence_score:.2%} confidence")
                    
                    # Check if validation passed
                    if not validation_result.is_valid:
                        if validation_result.fallback_required:
                            logger_core.warning(f"⚠️ Trading decision validation failed - fallback required")
                            return JSONResponse(
                                status_code=400,
                                content={
                                    "success": False,
                                    "error": "Trading decision validation failed",
                                    "validation_result": asdict(validation_result),
                                    "ai_brain_enhanced": True
                                }
                            )
                        else:
                            logger_core.info(f"⚠️ Validation issues found but proceeding with warnings")
                    
                    # Calculate confidence metrics
                    prediction_data = {
                        "ml_confidence": request.prediction.get("ml_confidence", 0.5),
                        "dl_confidence": request.prediction.get("dl_confidence", 0.5),
                        "ai_confidence": request.prediction.get("ai_confidence", 0.5),
                        "position_size": trading_decision.position_size,
                        "risk_per_trade": trading_decision.risk_per_trade
                    }
                    
                    market_data = {
                        "data_completeness": 0.95,
                        "volatility_level": "medium",
                        "liquidity_level": "high",
                        "is_active_trading_session": True,
                        "account_balance": 10000
                    }
                    
                    confidence_metrics = await ai_brain_confidence.calculate_comprehensive_confidence(
                        prediction_data, market_data, {"win_rate": 0.65, "profit_factor": 1.8}
                    )
                    
                    logger_core.info(f"🎯 Confidence analysis: {confidence_metrics.overall_confidence:.2%}")
                    
                except Exception as validation_error:
                    logger_core.error(f"❌ AI Brain validation failed: {validation_error}")
                    # Continue with trade execution but log the error
                    if AI_BRAIN_AVAILABLE:
                        try:
                            trading_context = TradingErrorContext(
                                symbol=request.symbol,
                                market_hours=True,
                                connection_status="active"
                            )
                            ai_brain_analysis = await trading_error_dna.analyze_trading_error(
                                validation_error, trading_context
                            )
                        except Exception as analysis_error:
                            logger_core.error(f"❌ Error analysis also failed: {analysis_error}")
            
            # Execute trade through AI Trading Engine
            result = await trading_engine_instance.execute_ai_trade(
                symbol=request.symbol,
                prediction=request.prediction,
                pattern_result=request.pattern_result
            )
            
            # Convert result to dictionary for JSON response with AI Brain enhancements
            result_dict = {
                "success": result.success,
                "order_ticket": result.order_ticket,
                "execution_price": result.execution_price,
                "slippage": result.slippage,
                "execution_time": result.execution_time,
                "ai_validation_passed": result.ai_validation_passed,
                "risk_validation_passed": result.risk_validation_passed,
                "pattern_confirmation": result.pattern_confirmation,
                "error_code": result.error_code,
                "error_description": result.error_description,
                "timestamp": result.timestamp.isoformat(),
                "execution_id": result.execution_id,
                "ai_brain_enhanced": AI_BRAIN_AVAILABLE,
                "validation_result": asdict(validation_result) if validation_result else None,
                "confidence_metrics": {
                    "overall_confidence": confidence_metrics.overall_confidence,
                    "confidence_level": confidence_metrics.confidence_level.value,
                    "model_confidence": confidence_metrics.model_prediction,
                    "risk_confidence": confidence_metrics.risk_assessment
                } if confidence_metrics else None,
                "ai_brain_analysis": ai_brain_analysis
            }
            
            if event_manager:
                event_manager.publish_event(
                    event_type="ai_trade_executed",
                    component="trading_engine_api",
                    message=f"AI trade executed for {request.symbol}",
                    data={
                        "symbol": request.symbol,
                        "success": result.success,
                        "execution_time": result.execution_time
                    }
                )
            
            return result_dict
            
        except Exception as e:
            logger_core.error(f"❌ AI trade execution failed: {e}")
            
            # Enhanced error handling with AI Brain
            ai_brain_error_analysis = None
            if AI_BRAIN_AVAILABLE:
                try:
                    trading_context = TradingErrorContext(
                        symbol=request.symbol,
                        market_hours=True,
                        connection_status="active"
                    )
                    ai_brain_error_analysis = await trading_error_dna.analyze_trading_error(e, trading_context)
                    logger_core.info(f"🧬 Error DNA analysis completed: {ai_brain_error_analysis['solution']['confidence']:.2%} confidence")
                except Exception as analysis_error:
                    logger_core.error(f"❌ AI Brain error analysis failed: {analysis_error}")
            
            if error_handler:
                error_response = error_handler.handle_error(e, "trading_api", "execute_ai_trade")
                return JSONResponse(status_code=500, content={
                    "error": error_response,
                    "ai_brain_analysis": ai_brain_error_analysis
                })
            else:
                return JSONResponse(status_code=500, content={
                    "error": str(e),
                    "ai_brain_analysis": ai_brain_error_analysis
                })

    @app.get("/api/v1/risk/metrics")
    async def get_risk_metrics():
        """Get current risk management metrics"""
        try:
            if not trading_engine_instance:
                raise HTTPException(status_code=503, detail="AI Trading Engine not available")
            
            risk_data = await trading_engine_instance.get_risk_metrics()
            return risk_data
            
        except Exception as e:
            logger_core.error(f"❌ Risk metrics retrieval failed: {e}")
            return JSONResponse(status_code=500, content={"error": str(e)})
    
    @app.post("/api/v1/trading/config")
    async def update_trading_config(config_request: TradingConfigRequest):
        """Update trading engine configuration"""
        try:
            if not trading_engine_instance:
                raise HTTPException(status_code=503, detail="AI Trading Engine not available")
            
            # Update configuration
            trading_engine_instance.config.enable_ai_validation = config_request.enable_ai_validation
            trading_engine_instance.config.ai_confidence_threshold = config_request.ai_confidence_threshold
            trading_engine_instance.config.max_risk_per_trade = config_request.max_risk_per_trade
            trading_engine_instance.config.max_daily_risk = config_request.max_daily_risk
            trading_engine_instance.config.max_positions = config_request.max_positions
            
            logger_core.info("✅ Trading configuration updated successfully")
            
            return {
                "success": True,
                "message": "Trading configuration updated successfully",
                "config": trading_engine_instance.config.__dict__,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger_core.error(f"❌ Configuration update failed: {e}")
            return JSONResponse(status_code=500, content={"error": str(e)})

    logger_core.info("Trading Engine FastAPI application created successfully")
    app.start_time = time.time()  # Track startup time for uptime calculation
    
    return app

# Create the app instance
trading_engine_app = create_app()

if __name__ == "__main__":
    """Run the Trading Engine service directly"""
    
    # Get service configuration
    host = service_config.get("host", "0.0.0.0")
    port = service_config.get("port", 8007)
    debug = service_config.get("debug", False)
    environment = service_config.get("environment", "development")
    
    logger_core.info(f"Starting Trading Engine Service on {host}:{port}")
    logger_core.info(f"Environment: {environment}, Debug: {debug}")
    logger_core.info(f"AI Trading Available: {trading_engine_available}")
    
    # Display startup banner
    startup_banner = f"""
🤖 Trading Engine v2.0.0 - AI Trading Platform
════════════════════════════════════════════════════════════════
✅ AI-powered trading execution and risk management
⚡ Real-time trade execution with MT5 integration  
🛡️ Advanced risk management and position sizing
📊 Performance analytics and trade optimization
🎯 Pattern recognition and market analysis
🔗 Microservices architecture integration
════════════════════════════════════════════════════════════════
Server: {host}:{port} | Environment: {environment}
AI Engine: {'✅ Active' if trading_engine_available else '❌ Limited Mode'}
════════════════════════════════════════════════════════════════
    """.strip()
    print(startup_banner)
    
    # Configure uvicorn for production deployment
    uvicorn_config = {
        "host": host,
        "port": port,
        "log_level": "debug" if debug else "info",
        "access_log": True,
        "reload": debug and environment == "development",
        "workers": 1  # Single worker for WebSocket compatibility
    }
    
    try:
        logger_core.info("🚀 Starting Trading Engine with AI capabilities")
        
        # Use subprocess for production to avoid event loop conflicts
        if environment == "production":
            logger_core.info("🚀 Starting Trading Engine in production mode")
            import subprocess
            import sys
            cmd = [
                sys.executable, "-m", "uvicorn", "main:trading_engine_app",
                "--host", str(host), "--port", str(port),
                "--log-level", "info", "--no-access-log"
            ]
            subprocess.run(cmd)
        else:
            # Development mode with direct uvicorn
            uvicorn.run("main:trading_engine_app", **uvicorn_config)
            
    except KeyboardInterrupt:
        logger_core.info("\n👋 Trading Engine Service stopped by user")
    except Exception as e:
        logger_core.error(f"❌ Trading Engine Service failed to start: {e}")
        if error_handler:
            error_handler.handle_error(e, "trading_engine_main", "startup")
        sys.exit(1)