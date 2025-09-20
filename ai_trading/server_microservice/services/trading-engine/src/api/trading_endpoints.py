"""
Trading Engine API Endpoints

RESTful API endpoints for the Trading-Engine service that coordinate:
- Strategy execution and management
- Risk management and position sizing
- Performance analytics and reporting
- Technical analysis coordination
- Inter-service communication
- Telegram bot notifications

This module provides the main API interface for the Trading-Engine microservice.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import asyncio

from ..core.strategy_executor import StrategyExecutor, StrategyConfiguration, TradingStrategy
from ..core.risk_manager import AdvancedRiskManager, RiskConfiguration
from ..core.performance_analytics import TradingPerformanceAnalytics
from ..core.technical_analysis_coordinator import (
    TechnicalAnalysisCoordinator, TARequest, TATimeframe, get_ta_coordinator
)
from ..core.telegram_bot import TelegramTradingBot
from ...shared.infrastructure.service_client import get_service_client, APIResponse
from ...shared.infrastructure.logging import get_logger
from ...shared.infrastructure.config import get_config

# Initialize router
router = APIRouter(prefix="/api/v1/trading", tags=["Trading Engine"])
logger = get_logger("trading-engine", "api")

# === Pydantic Models for API ===

class StrategyRequest(BaseModel):
    """Request model for strategy operations"""
    strategy_id: str
    symbol: str
    timeframe: str = "1h"
    parameters: Dict[str, Any] = Field(default_factory=dict)
    risk_parameters: Optional[Dict[str, Any]] = None

class TradeExecutionRequest(BaseModel):
    """Request model for trade execution"""
    strategy_id: str
    symbol: str
    action: str  # buy, sell, close
    quantity: Optional[float] = None
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    risk_amount: Optional[float] = None

class TechnicalAnalysisRequest(BaseModel):
    """Request model for technical analysis"""
    symbol: str
    timeframe: str = "1h"
    indicators: List[Dict[str, Any]] = Field(default_factory=list)
    lookback_periods: int = 100

class RiskAssessmentRequest(BaseModel):
    """Request model for risk assessment"""
    symbol: str
    position_size: float
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    strategy_id: Optional[str] = None

class PerformanceAnalysisRequest(BaseModel):
    """Request model for performance analysis"""
    strategy_id: Optional[str] = None
    symbol: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_charts: bool = False

# === Strategy Management Endpoints ===

@router.post("/strategies/create")
async def create_strategy(request: StrategyRequest):
    """Create and register a new trading strategy"""
    try:
        logger.info(f"Creating strategy: {request.strategy_id}")
        
        # Get strategy executor
        config = StrategyConfiguration(
            strategy_id=request.strategy_id,
            parameters=request.parameters
        )
        strategy_executor = StrategyExecutor(config)
        
        # Create strategy configuration
        strategy = TradingStrategy(
            strategy_id=request.strategy_id,
            symbol=request.symbol,
            timeframe=request.timeframe,
            parameters=request.parameters
        )
        
        # Register strategy
        success = await strategy_executor.register_strategy(strategy)
        
        if success:
            return JSONResponse({
                "success": True,
                "message": f"Strategy {request.strategy_id} created successfully",
                "strategy_id": request.strategy_id,
                "symbol": request.symbol,
                "timeframe": request.timeframe
            })
        else:
            raise HTTPException(status_code=400, detail="Failed to create strategy")
    
    except Exception as e:
        logger.error(f"Error creating strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/strategies/{strategy_id}/start")
async def start_strategy(strategy_id: str, background_tasks: BackgroundTasks):
    """Start executing a trading strategy"""
    try:
        logger.info(f"Starting strategy: {strategy_id}")
        
        # Get strategy executor
        strategy_executor = StrategyExecutor()
        
        # Start strategy in background
        background_tasks.add_task(strategy_executor.start_strategy, strategy_id)
        
        return JSONResponse({
            "success": True,
            "message": f"Strategy {strategy_id} started",
            "strategy_id": strategy_id,
            "status": "running"
        })
    
    except Exception as e:
        logger.error(f"Error starting strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/strategies/{strategy_id}/stop")
async def stop_strategy(strategy_id: str):
    """Stop a running trading strategy"""
    try:
        logger.info(f"Stopping strategy: {strategy_id}")
        
        # Get strategy executor
        strategy_executor = StrategyExecutor()
        
        # Stop strategy
        success = await strategy_executor.stop_strategy(strategy_id)
        
        if success:
            return JSONResponse({
                "success": True,
                "message": f"Strategy {strategy_id} stopped",
                "strategy_id": strategy_id,
                "status": "stopped"
            })
        else:
            raise HTTPException(status_code=400, detail="Failed to stop strategy")
    
    except Exception as e:
        logger.error(f"Error stopping strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/strategies")
async def list_strategies():
    """List all registered strategies"""
    try:
        strategy_executor = StrategyExecutor()
        strategies = await strategy_executor.get_strategy_status()
        
        return JSONResponse({
            "success": True,
            "strategies": strategies,
            "count": len(strategies)
        })
    
    except Exception as e:
        logger.error(f"Error listing strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/strategies/{strategy_id}/status")
async def get_strategy_status(strategy_id: str):
    """Get detailed status of a specific strategy"""
    try:
        strategy_executor = StrategyExecutor()
        status = await strategy_executor.get_strategy_status(strategy_id)
        
        if status:
            return JSONResponse({
                "success": True,
                "strategy": status
            })
        else:
            raise HTTPException(status_code=404, detail="Strategy not found")
    
    except Exception as e:
        logger.error(f"Error getting strategy status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === Trade Execution Endpoints ===

@router.post("/execute")
async def execute_trade(request: TradeExecutionRequest):
    """Execute a trading order"""
    try:
        logger.info(f"Executing trade: {request.action} {request.symbol}")
        
        # Get service client for MT5 communication
        service_client = await get_service_client()
        
        # Prepare trade request
        trade_request = {
            "symbol": request.symbol,
            "action": request.action,
            "quantity": request.quantity,
            "price": request.price,
            "stop_loss": request.stop_loss,
            "take_profit": request.take_profit,
            "strategy_id": request.strategy_id
        }
        
        # Execute trade through MT5-Bridge
        response = await service_client.execute_trade(trade_request)
        
        if response.success:
            # Save trade data to database
            await service_client.save_trading_data("trade_execution", {
                "strategy_id": request.strategy_id,
                "trade_request": trade_request,
                "execution_result": response.data,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return JSONResponse({
                "success": True,
                "message": "Trade executed successfully",
                "execution_result": response.data
            })
        else:
            raise HTTPException(status_code=400, detail=response.error)
    
    except Exception as e:
        logger.error(f"Error executing trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/positions")
async def get_positions(symbol: Optional[str] = None):
    """Get current trading positions"""
    try:
        service_client = await get_service_client()
        response = await service_client.get_positions(symbol)
        
        if response.success:
            return JSONResponse({
                "success": True,
                "positions": response.data
            })
        else:
            raise HTTPException(status_code=400, detail=response.error)
    
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === Risk Management Endpoints ===

@router.post("/risk/assess")
async def assess_risk(request: RiskAssessmentRequest):
    """Assess risk for a potential trade"""
    try:
        logger.info(f"Assessing risk for {request.symbol}")
        
        # Get risk manager
        risk_manager = AdvancedRiskManager()
        
        # Calculate risk metrics
        risk_assessment = await risk_manager.calculate_position_size(
            symbol=request.symbol,
            entry_price=request.entry_price,
            stop_loss=request.stop_loss,
            risk_amount=request.position_size
        )
        
        return JSONResponse({
            "success": True,
            "risk_assessment": risk_assessment
        })
    
    except Exception as e:
        logger.error(f"Error assessing risk: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/risk/portfolio")
async def get_portfolio_risk():
    """Get portfolio-wide risk metrics"""
    try:
        risk_manager = AdvancedRiskManager()
        portfolio_risk = await risk_manager.get_portfolio_risk()
        
        return JSONResponse({
            "success": True,
            "portfolio_risk": portfolio_risk
        })
    
    except Exception as e:
        logger.error(f"Error getting portfolio risk: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === Technical Analysis Endpoints ===

@router.post("/analysis/technical")
async def request_technical_analysis(request: TechnicalAnalysisRequest):
    """Request technical analysis for a symbol"""
    try:
        logger.info(f"Requesting TA for {request.symbol}")
        
        ta_coordinator = get_ta_coordinator()
        
        # Request multiple indicators
        results = await ta_coordinator.request_multiple_indicators(
            symbol=request.symbol,
            timeframe=request.timeframe,
            indicators=request.indicators
        )
        
        return JSONResponse({
            "success": True,
            "symbol": request.symbol,
            "timeframe": request.timeframe,
            "indicators": {
                name: {
                    "values": result.values if result else None,
                    "timestamps": [ts.isoformat() for ts in result.timestamps] if result else None,
                    "confidence": result.confidence if result else None
                }
                for name, result in results.items()
            }
        })
    
    except Exception as e:
        logger.error(f"Error requesting technical analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/signals/{symbol}")
async def get_trading_signals(symbol: str, timeframe: str = "1h"):
    """Get AI-generated trading signals"""
    try:
        ta_coordinator = get_ta_coordinator()
        signals = await ta_coordinator.generate_trading_signals(symbol, timeframe)
        
        signal_data = []
        for signal in signals:
            signal_data.append({
                "symbol": signal.symbol,
                "timeframe": signal.timeframe.value,
                "signal_type": signal.signal_type,
                "strength": signal.strength,
                "indicators_used": signal.indicators_used,
                "confirmation_count": signal.confirmation_count,
                "generated_at": signal.generated_at.isoformat(),
                "metadata": signal.metadata
            })
        
        return JSONResponse({
            "success": True,
            "symbol": symbol,
            "timeframe": timeframe,
            "signals": signal_data,
            "count": len(signal_data)
        })
    
    except Exception as e:
        logger.error(f"Error getting trading signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === Performance Analytics Endpoints ===

@router.post("/performance/analyze")
async def analyze_performance(request: PerformanceAnalysisRequest):
    """Analyze trading performance"""
    try:
        logger.info("Analyzing trading performance")
        
        performance_analytics = TradingPerformanceAnalytics()
        
        # Get performance analysis
        analysis = await performance_analytics.generate_comprehensive_report(
            strategy_id=request.strategy_id,
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            include_charts=request.include_charts
        )
        
        return JSONResponse({
            "success": True,
            "performance_analysis": analysis
        })
    
    except Exception as e:
        logger.error(f"Error analyzing performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance/dashboard")
async def get_performance_dashboard():
    """Get real-time performance dashboard data"""
    try:
        performance_analytics = TradingPerformanceAnalytics()
        dashboard_data = await performance_analytics.get_realtime_dashboard()
        
        return JSONResponse({
            "success": True,
            "dashboard": dashboard_data
        })
    
    except Exception as e:
        logger.error(f"Error getting performance dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === Market Data Endpoints ===

@router.get("/market-data/{symbol}")
async def get_market_data(symbol: str, timeframe: str = "TICK"):
    """Get live market data"""
    try:
        service_client = await get_service_client()
        response = await service_client.get_market_data(symbol, timeframe)
        
        if response.success:
            return JSONResponse({
                "success": True,
                "symbol": symbol,
                "timeframe": timeframe,
                "data": response.data
            })
        else:
            raise HTTPException(status_code=400, detail=response.error)
    
    except Exception as e:
        logger.error(f"Error getting market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market-data/{symbol}/historical")
async def get_historical_data(
    symbol: str,
    timeframe: str = "1h",
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
):
    """Get historical market data"""
    try:
        # Default to last 24 hours if no time range specified
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(hours=24)
        
        service_client = await get_service_client()
        response = await service_client.get_historical_data(symbol, timeframe, start_time, end_time)
        
        if response.success:
            return JSONResponse({
                "success": True,
                "symbol": symbol,
                "timeframe": timeframe,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "data": response.data
            })
        else:
            raise HTTPException(status_code=400, detail=response.error)
    
    except Exception as e:
        logger.error(f"Error getting historical data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === System Status Endpoints ===

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check all service connections
        service_client = await get_service_client()
        service_health = await service_client.check_all_services_health()
        
        # Check TA coordinator
        ta_coordinator = get_ta_coordinator()
        ta_health = await ta_coordinator.health_check()
        
        # Overall system status
        all_healthy = all(
            service.get('status') == 'healthy' 
            for service in service_health.values()
        ) and ta_health.get('status') == 'healthy'
        
        return JSONResponse({
            "success": True,
            "status": "healthy" if all_healthy else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "services": service_health,
            "technical_analysis": ta_health,
            "client_statistics": service_client.get_client_statistics()
        })
    
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return JSONResponse({
            "success": False,
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }, status_code=503)

@router.get("/status")
async def get_system_status():
    """Get detailed system status"""
    try:
        # Get strategy executor status
        strategy_executor = StrategyExecutor()
        strategies = await strategy_executor.get_strategy_status()
        
        # Get risk manager status
        risk_manager = AdvancedRiskManager()
        risk_stats = await risk_manager.get_statistics()
        
        # Get performance analytics status
        performance_analytics = TradingPerformanceAnalytics()
        perf_stats = await performance_analytics.get_analytics_summary()
        
        # Get TA coordinator stats
        ta_coordinator = get_ta_coordinator()
        ta_stats = await ta_coordinator.get_cache_statistics()
        
        return JSONResponse({
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "system_status": {
                "strategies": {
                    "total": len(strategies),
                    "running": len([s for s in strategies if s.get('status') == 'running']),
                    "stopped": len([s for s in strategies if s.get('status') == 'stopped'])
                },
                "risk_management": risk_stats,
                "performance_analytics": perf_stats,
                "technical_analysis": ta_stats
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))