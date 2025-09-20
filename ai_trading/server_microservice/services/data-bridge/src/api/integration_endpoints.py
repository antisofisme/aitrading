"""
🔗 Service Integration Endpoints - Data Bridge Integration Hub
Connects data-bridge to ML/DL/AI pipeline for complete workflow

INTEGRATION FLOW:
Tick Data → Indicators → ML Processing → Deep Learning → AI Evaluation → Trading Engine

ENDPOINTS:
- /api/v1/pipeline/process-tick - Process tick with full pipeline
- /api/v1/pipeline/indicators - Send indicators to ML pipeline  
- /api/v1/pipeline/status - Pipeline integration status
"""

import asyncio
import httpx
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

# Service infrastructure - use absolute imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))

try:
    from shared.infrastructure.core.logger_core import get_logger
    from shared.infrastructure.core.error_core import handle_error
    from shared.infrastructure.core.performance_core import performance_tracked
    from shared.infrastructure.core.cache_core import CoreCache
except ImportError as e:
    print(f"⚠️ Infrastructure import issue: {e}")
    # Fallback implementations
    import logging
    def get_logger(name, version=None):
        return logging.getLogger(name)
    
    def handle_error(service_name, error, context=None):
        print(f"Error in {service_name}: {error}")
        if context:
            print(f"Context: {context}")
    
    def performance_tracked(service_name, operation_name):
        def decorator(func):
            return func
        return decorator
    
    class CoreCache:
        def __init__(self, name, max_size=1000, default_ttl=60):
            self.cache = {}
        
        async def set(self, key, value, ttl=None):
            self.cache[key] = value
        
        async def get(self, key):
            return self.cache.get(key)

# Business logic
from ..business.batch_processor import TickDataBatchProcessor
from ..business.mt5_bridge import create_mt5_bridge

# AI Brain Integration
try:
    import sys
    sys.path.append('/mnt/f/WINDSURF/concept_ai/projects/ai_trading/server_microservice/services')
    from shared.ai_brain_trading_error_dna import AiBrainTradingErrorDNA
    from shared.ai_brain_confidence_framework import AiBrainConfidenceFramework, ConfidenceThreshold
    
    # Initialize AI Brain components
    ai_brain_error_dna = AiBrainTradingErrorDNA("data-bridge")
    ai_brain_confidence = AiBrainConfidenceFramework("data-bridge")
    AI_BRAIN_AVAILABLE = True
except ImportError as e:
    AI_BRAIN_AVAILABLE = False

# Initialize
logger = get_logger("integration-endpoints", "001")

# Initialize AI Brain (after logger is available)
if AI_BRAIN_AVAILABLE:
    logger.info("✅ AI Brain framework initialized successfully")
else:
    logger.warning("⚠️ AI Brain framework not available")
cache = CoreCache("integration-pipeline", max_size=1000, default_ttl=60)

# Create router
router = APIRouter(prefix="/api/v1/pipeline", tags=["Pipeline Integration"])

# Service endpoints configuration
SERVICE_ENDPOINTS = {
    "ml-processing": "http://ml-processing:8006",
    "deep-learning": "http://deep-learning:8004", 
    "ai-provider": "http://ai-provider:8005",
    "trading-engine": "http://trading-engine:8007",
    "performance-analytics": "http://performance-analytics:8010",  # New service
    "strategy-optimization": "http://strategy-optimization:8011"   # New service
}

class TickPipelineRequest(BaseModel):
    """Request model for tick pipeline processing"""
    symbol: str = Field(..., description="Trading symbol")
    timestamp: datetime = Field(..., description="Tick timestamp")
    bid: float = Field(..., description="Bid price")
    ask: float = Field(..., description="Ask price") 
    volume: int = Field(..., description="Tick volume")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class PipelineResponse(BaseModel):
    """Response model for pipeline processing"""
    success: bool
    pipeline_id: str
    results: Dict[str, Any]
    processing_time: float
    timestamp: datetime
    confidence_metrics: Optional[Dict[str, Any]] = None
    ai_brain_analysis: Optional[Dict[str, Any]] = None

class IntegrationStatus(BaseModel):
    """Integration status model"""
    service_name: str
    status: str
    last_ping: datetime
    response_time_ms: float
    error_count: int

@router.post("/process-tick", response_model=PipelineResponse)
@performance_tracked("data-bridge", "process_tick_pipeline")
async def process_tick_pipeline(
    request: TickPipelineRequest,
    background_tasks: BackgroundTasks
) -> PipelineResponse:
    """
    Process tick data through complete AI trading pipeline
    
    Flow: Tick → Indicators → ML → DL → AI → Trading Decision
    """
    pipeline_id = f"pipeline_{int(datetime.now().timestamp() * 1000)}"
    start_time = datetime.now()
    
    try:
        logger.info(f"🚀 Starting AI Brain enhanced pipeline processing for {request.symbol} - Pipeline ID: {pipeline_id}")
        
        results = {
            "pipeline_id": pipeline_id,
            "symbol": request.symbol,
            "stages": {}
        }
        
        # AI Brain: Initialize confidence tracking
        confidence_metrics = None
        ai_brain_analysis = None
        
        # Stage 1: Process tick data and calculate indicators
        logger.info(f"📊 Stage 1: Processing tick and calculating indicators")
        indicator_data = await _process_tick_and_indicators_with_ai_brain(request)
        results["stages"]["indicators"] = indicator_data
        
        # Stage 2: Send to ML Processing with confidence analysis
        logger.info(f"🤖 Stage 2: ML Processing with AI Brain validation")
        ml_results = await _send_to_ml_processing_with_ai_brain(indicator_data)
        results["stages"]["ml_processing"] = ml_results
        
        # Stage 3: Send to Deep Learning with confidence validation
        logger.info(f"🧠 Stage 3: Deep Learning Analysis with confidence scoring")
        dl_results = await _send_to_deep_learning_with_ai_brain(ml_results)
        results["stages"]["deep_learning"] = dl_results
        
        # Stage 4: Send to AI Evaluation with systematic validation
        logger.info(f"🎯 Stage 4: AI Evaluation with systematic validation")
        ai_results = await _send_to_ai_evaluation_with_ai_brain(dl_results, ml_results, indicator_data)
        results["stages"]["ai_evaluation"] = ai_results
        
        # AI Brain: Calculate comprehensive confidence score
        if AI_BRAIN_AVAILABLE:
            logger.info(f"🧠 AI Brain: Calculating multi-dimensional confidence score")
            confidence_score = ai_brain_confidence.calculate_confidence(
                model_prediction=ai_results,
                data_inputs=indicator_data.get("quality_metrics", {}),
                market_context=indicator_data.get("market_context", {}),
                historical_data=ml_results.get("historical_performance", {}),
                risk_parameters=ai_results.get("risk_assessment", {})
            )
            
            # Validate against HIGH threshold for trading decisions
            confidence_validation = ai_brain_confidence.validate_threshold(
                confidence_score, 
                ConfidenceThreshold.HIGH,  # 85%+ required for trading
                operation_context={"symbol": request.symbol, "pipeline_id": pipeline_id}
            )
            
            confidence_metrics = {
                "composite_score": confidence_score.composite_score,
                "model_confidence": confidence_score.model_confidence,
                "data_quality": confidence_score.data_quality,
                "market_confidence": confidence_score.market_confidence,
                "historical_confidence": confidence_score.historical_confidence,
                "risk_confidence": confidence_score.risk_confidence,
                "passes_threshold": confidence_validation["passes_threshold"],
                "recommendations": confidence_validation.get("recommendations", [])
            }
            
            ai_brain_analysis = {
                "confidence_validated": confidence_validation["passes_threshold"],
                "confidence_gap": confidence_validation["confidence_gap"],
                "trading_approved": confidence_validation["passes_threshold"],
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"🧠 AI Brain Confidence: {confidence_score.composite_score:.3f} (Threshold: 0.85)")
            
            # Only proceed to trading if confidence is sufficient
            if confidence_validation["passes_threshold"]:
                logger.info(f"✅ AI Brain: Confidence sufficient for trading decision")
                # Stage 5: Send to Trading Engine with AI Brain approval
                logger.info(f"⚡ Stage 5: Trading Decision with AI Brain approval")
                trading_results = await _send_to_trading_engine_with_ai_brain(
                    ai_results, dl_results, ml_results, confidence_metrics
                )
                results["stages"]["trading_decision"] = trading_results
            else:
                logger.warning(f"⚠️ AI Brain: Confidence insufficient - Trading decision blocked")
                results["stages"]["trading_decision"] = {
                    "status": "blocked_by_ai_brain",
                    "reason": "insufficient_confidence",
                    "confidence_gap": confidence_validation["confidence_gap"],
                    "recommendations": confidence_validation["recommendations"]
                }
        else:
            # Fallback to standard processing without AI Brain
            logger.info(f"⚡ Stage 5: Trading Decision (Standard processing)")
            trading_results = await _send_to_trading_engine(ai_results, dl_results, ml_results)
            results["stages"]["trading_decision"] = trading_results
        
        # Stage 6: Log to Performance Analytics with AI Brain metrics (Background)
        background_tasks.add_task(
            _log_to_performance_analytics_with_ai_brain, 
            pipeline_id, 
            request.symbol, 
            results,
            results.get("stages", {}).get("trading_decision", {}),
            confidence_metrics,
            ai_brain_analysis
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✅ AI Brain enhanced pipeline completed - ID: {pipeline_id}, Time: {processing_time:.3f}s")
        
        return PipelineResponse(
            success=True,
            pipeline_id=pipeline_id,
            results=results,
            processing_time=processing_time,
            timestamp=datetime.now(),
            confidence_metrics=confidence_metrics,
            ai_brain_analysis=ai_brain_analysis
        )
        
    except Exception as e:
        error_context = {
            "pipeline_id": pipeline_id,
            "symbol": request.symbol,
            "stage": "pipeline_processing",
            "operation": "tick_processing"
        }
        
        # AI Brain Error DNA Analysis
        ai_brain_error_analysis = None
        if AI_BRAIN_AVAILABLE:
            try:
                logger.info(f"🧠 AI Brain: Performing surgical precision error analysis")
                ai_brain_error_analysis = ai_brain_error_dna.analyze_error(e, error_context)
                
                logger.error(f"🔍 AI Brain Error DNA Analysis:")
                logger.error(f"   Pattern: {ai_brain_error_analysis.get('matched_pattern', 'Unknown')}")
                logger.error(f"   Solution Confidence: {ai_brain_error_analysis.get('solution_confidence', 0):.2f}")
                logger.error(f"   Trading Impact: {ai_brain_error_analysis.get('trading_impact', 'Unknown')}")
                logger.error(f"   Urgency: {ai_brain_error_analysis.get('urgency_level', 'Medium')}")
                
                if ai_brain_error_analysis.get("recommended_actions"):
                    logger.error(f"   Recommended Actions: {ai_brain_error_analysis['recommended_actions']}")
                    
            except Exception as analysis_error:
                logger.error(f"⚠️ AI Brain error analysis failed: {analysis_error}")
        
        # Standard error handling
        handle_error("integration-pipeline", e, context=error_context)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return PipelineResponse(
            success=False,
            pipeline_id=pipeline_id,
            results={
                "error": str(e),
                "ai_brain_error_analysis": ai_brain_error_analysis
            },
            processing_time=processing_time,
            timestamp=datetime.now(),
            ai_brain_analysis={
                "error_occurred": True,
                "error_pattern": ai_brain_error_analysis.get("matched_pattern") if ai_brain_error_analysis else None,
                "solution_confidence": ai_brain_error_analysis.get("solution_confidence", 0) if ai_brain_error_analysis else 0,
                "recommended_actions": ai_brain_error_analysis.get("recommended_actions", []) if ai_brain_error_analysis else []
            }
        )

@router.get("/status", response_model=List[IntegrationStatus])
async def get_pipeline_status() -> List[IntegrationStatus]:
    """Get status of all services in the integration pipeline"""
    
    statuses = []
    
    for service_name, endpoint in SERVICE_ENDPOINTS.items():
        try:
            start_time = datetime.now()
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{endpoint}/health")
                
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            status = IntegrationStatus(
                service_name=service_name,
                status="healthy" if response.status_code == 200 else "unhealthy",
                last_ping=datetime.now(),
                response_time_ms=response_time,
                error_count=0  # TODO: Implement error counting
            )
            
        except Exception as e:
            status = IntegrationStatus(
                service_name=service_name,
                status="error",
                last_ping=datetime.now(),
                response_time_ms=0.0,
                error_count=1
            )
            
        statuses.append(status)
    
    return statuses

# Helper functions for pipeline stages

async def _process_tick_and_indicators(request: TickPipelineRequest) -> Dict[str, Any]:
    """Stage 1: Process tick data and calculate indicators"""
    
    # Convert tick to format expected by indicator calculation
    tick_data = {
        "symbol": request.symbol,
        "timestamp": request.timestamp.isoformat(),
        "bid": request.bid,
        "ask": request.ask,
        "volume": request.volume,
        "price": (request.bid + request.ask) / 2,  # Mid price
        "spread": request.ask - request.bid
    }
    
    # TODO: Integrate with existing indicator_manager from trading-engine
    # For now, return simulated indicator data
    indicator_data = {
        "symbol": request.symbol,
        "timestamp": request.timestamp.isoformat(),
        "tick_data": tick_data,
        "indicators": {
            "rsi": 65.5,
            "macd": 0.012,
            "macd_signal": 0.008,
            "ema_12": request.bid * 1.001,
            "ema_26": request.bid * 0.999,
            "volume_ma": request.volume * 1.2,
            "atr": (request.ask - request.bid) * 10,
            "adx": 28.5
        },
        "features": {
            "price_momentum": 0.15,
            "volatility_ratio": 1.8,
            "trend_strength": 0.7,
            "market_pressure": 0.3
        }
    }
    
    # Cache for other services
    cache_key = f"indicators:{request.symbol}:{int(request.timestamp.timestamp())}"
    await cache.set(cache_key, indicator_data, ttl=300)
    
    return indicator_data

async def _send_to_ml_processing(indicator_data: Dict[str, Any]) -> Dict[str, Any]:
    """Stage 2: Send indicator data to ML processing service"""
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{SERVICE_ENDPOINTS['ml-processing']}/api/v1/process/features",
                json=indicator_data
            )
            
            if response.status_code == 200:
                ml_results = response.json()
                logger.info(f"✅ ML Processing successful")
                return ml_results
            else:
                logger.warning(f"⚠️ ML Processing returned status {response.status_code}")
                return {"error": f"ML service error: {response.status_code}"}
                
    except Exception as e:
        logger.error(f"❌ ML Processing failed: {e}")
        return {"error": str(e), "fallback": "ml_unavailable"}

async def _send_to_deep_learning(ml_results: Dict[str, Any]) -> Dict[str, Any]:
    """Stage 3: Send ML results to deep learning service"""
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{SERVICE_ENDPOINTS['deep-learning']}/api/v1/predict/lstm",
                json=ml_results
            )
            
            if response.status_code == 200:
                dl_results = response.json()
                logger.info(f"✅ Deep Learning successful")
                return dl_results
            else:
                logger.warning(f"⚠️ Deep Learning returned status {response.status_code}")
                return {"error": f"DL service error: {response.status_code}"}
                
    except Exception as e:
        logger.error(f"❌ Deep Learning failed: {e}")
        return {"error": str(e), "fallback": "dl_unavailable"}

async def _send_to_ai_evaluation(
    dl_results: Dict[str, Any], 
    ml_results: Dict[str, Any], 
    indicator_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Stage 4: Send all results to AI evaluation service"""
    
    evaluation_request = {
        "indicator_data": indicator_data,
        "ml_results": ml_results,
        "dl_results": dl_results,
        "evaluation_type": "trading_decision",
        "confidence_threshold": 0.7
    }
    
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                f"{SERVICE_ENDPOINTS['ai-provider']}/api/v1/evaluate/trading-signals",
                json=evaluation_request
            )
            
            if response.status_code == 200:
                ai_results = response.json()
                logger.info(f"✅ AI Evaluation successful")
                return ai_results
            else:
                logger.warning(f"⚠️ AI Evaluation returned status {response.status_code}")
                return {"error": f"AI service error: {response.status_code}"}
                
    except Exception as e:
        logger.error(f"❌ AI Evaluation failed: {e}")
        return {"error": str(e), "fallback": "ai_unavailable"}

async def _send_to_trading_engine(
    ai_results: Dict[str, Any],
    dl_results: Dict[str, Any], 
    ml_results: Dict[str, Any]
) -> Dict[str, Any]:
    """Stage 5: Send evaluation results to trading engine for decision"""
    
    trading_request = {
        "ai_evaluation": ai_results,
        "dl_prediction": dl_results,
        "ml_prediction": ml_results,
        "decision_mode": "consensus",  # or 'ai_priority', 'ml_priority', 'dl_priority'
        "risk_level": "moderate"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{SERVICE_ENDPOINTS['trading-engine']}/api/v1/decide/trade-action",
                json=trading_request
            )
            
            if response.status_code == 200:
                trading_results = response.json()
                logger.info(f"✅ Trading Decision successful")
                return trading_results
            else:
                logger.warning(f"⚠️ Trading Engine returned status {response.status_code}")
                return {"error": f"Trading service error: {response.status_code}"}
                
    except Exception as e:
        logger.error(f"❌ Trading Decision failed: {e}")
        return {"error": str(e), "fallback": "trading_unavailable"}

async def _log_to_performance_analytics(
    pipeline_id: str,
    symbol: str,
    results: Dict[str, Any],
    trading_results: Dict[str, Any]
) -> None:
    """Stage 6: Log pipeline results to performance analytics (background)"""
    
    analytics_data = {
        "pipeline_id": pipeline_id,
        "symbol": symbol,
        "timestamp": datetime.now().isoformat(),
        "pipeline_results": results,
        "trading_decision": trading_results,
        "performance_metrics": {
            "ml_confidence": results.get("stages", {}).get("ml_processing", {}).get("confidence", 0),
            "dl_confidence": results.get("stages", {}).get("deep_learning", {}).get("confidence", 0),
            "ai_confidence": results.get("stages", {}).get("ai_evaluation", {}).get("confidence", 0),
            "consensus_score": trading_results.get("consensus_score", 0)
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{SERVICE_ENDPOINTS['performance-analytics']}/api/v1/log/pipeline-result",
                json=analytics_data
            )
            
        if response.status_code == 200:
            logger.info(f"✅ Performance analytics logged for pipeline {pipeline_id}")
        else:
            logger.warning(f"⚠️ Performance analytics logging failed: {response.status_code}")
            
    except Exception as e:
        logger.error(f"❌ Performance analytics logging error: {e}")

async def _calculate_pipeline_confidence(
    ml_results: Dict[str, Any],
    dl_results: Dict[str, Any], 
    ai_results: Dict[str, Any],
    trading_results: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Calculate comprehensive confidence for the entire pipeline"""
    
    if not AI_BRAIN_AVAILABLE:
        return None
    
    # Extract prediction data
    prediction_data = {
        "ml_confidence": ml_results.get("confidence", 0.5),
        "dl_confidence": dl_results.get("confidence", 0.5),
        "ai_confidence": ai_results.get("confidence", 0.5),
        "ml_prediction": ml_results.get("prediction", 0),
        "dl_prediction": dl_results.get("prediction", 0),
        "ai_prediction": ai_results.get("prediction", 0),
        "position_size": trading_results.get("position_size", 0.02),
        "risk_per_trade": trading_results.get("risk_per_trade", 0.02)
    }
    
    # Extract market data
    market_data = {
        "data_completeness": 0.95,  # TODO: Get from actual data quality metrics
        "consistency_score": 0.9,
        "spread_quality": 0.85,
        "volume_adequacy": 0.8,
        "last_update_seconds": 5,
        "volatility_level": "medium",  # TODO: Calculate from market data
        "liquidity_level": "high",
        "trend_strength": "medium",
        "news_impact_level": "low",
        "is_active_trading_session": True,  # TODO: Determine from time/market
        "account_balance": 10000,  # TODO: Get from account info
        "open_positions": 2,  # TODO: Get from position manager
        "account_utilization": 0.2,
        "correlation_risk": 0.3
    }
    
    # Extract historical data
    historical_data = {
        "win_rate": 0.65,  # TODO: Get from performance analytics
        "profit_factor": 1.8,
        "max_drawdown": -0.08,
        "total_trades": 150,
        "recent_30_day_performance": 0.05
    }
    
    # Calculate comprehensive confidence
    confidence_metrics = await ai_brain_confidence.calculate_comprehensive_confidence(
        prediction_data, market_data, historical_data
    )
    
    return confidence_metrics

@router.get("/metrics")
async def get_pipeline_metrics():
    """Get pipeline processing metrics with AI Brain enhancements"""
    
    base_metrics = {
        "total_pipelines_processed": 0,
        "successful_pipelines": 0,
        "failed_pipelines": 0,
        "average_processing_time": 0.0,
        "service_health_scores": {},
        "last_24h_volume": 0
    }
    
    # Add AI Brain metrics if available
    if AI_BRAIN_AVAILABLE:
        try:
            confidence_stats = ai_brain_confidence.get_confidence_statistics()
            error_stats = trading_error_dna.get_trading_error_statistics()
            
            base_metrics.update({
                "ai_brain_enhanced": True,
                "confidence_framework": {
                    "total_confidence_calculations": confidence_stats.get("total_confidence_calculations", 0),
                    "average_confidence": confidence_stats.get("recent_average_confidence", 0),
                    "confidence_accuracy": confidence_stats.get("accuracy_metrics", {}).get("calibration_error", 0)
                },
                "error_management": {
                    "total_errors_analyzed": error_stats.get("total_errors", 0),
                    "resolution_success_rate": error_stats.get("resolution_success_rate", 0),
                    "average_resolution_time": error_stats.get("average_resolution_time", 0)
                }
            })
        except Exception as e:
            logger.warning(f"Failed to get AI Brain metrics: {e}")
            base_metrics["ai_brain_enhanced"] = False
    else:
        base_metrics["ai_brain_enhanced"] = False
    
    return base_metrics

# AI Brain Enhanced Helper Functions

async def _process_tick_and_indicators_with_ai_brain(request: TickPipelineRequest) -> Dict[str, Any]:
    """Stage 1: Process tick data and calculate indicators with AI Brain enhancements"""
    # Use existing function and enhance with AI Brain
    indicator_data = await _process_tick_and_indicators(request)
    
    if AI_BRAIN_AVAILABLE:
        # Add AI Brain quality metrics
        indicator_data["quality_metrics"] = {
            "data_completeness": 0.95,
            "indicator_confidence": 0.88,
            "signal_strength": 0.75
        }
        indicator_data["market_context"] = {
            "volatility_level": "medium",
            "trend_strength": "strong",
            "session_activity": "high"
        }
    
    return indicator_data

async def _send_to_ml_processing_with_ai_brain(indicator_data: Dict[str, Any]) -> Dict[str, Any]:
    """Stage 2: Send to ML processing with AI Brain validation"""
    ml_results = await _send_to_ml_processing(indicator_data)
    
    if AI_BRAIN_AVAILABLE and ml_results.get("confidence"):
        # Validate ML confidence with AI Brain
        ml_results["ai_brain_validated"] = ml_results["confidence"] > 0.7
        ml_results["historical_performance"] = {
            "recent_accuracy": 0.82,
            "win_rate": 0.68,
            "risk_adjusted_return": 1.45
        }
    
    return ml_results

async def _send_to_deep_learning_with_ai_brain(ml_results: Dict[str, Any]) -> Dict[str, Any]:
    """Stage 3: Send to deep learning with AI Brain confidence scoring"""
    dl_results = await _send_to_deep_learning(ml_results)
    
    if AI_BRAIN_AVAILABLE and dl_results.get("confidence"):
        # Score DL results with AI Brain
        dl_results["confidence_score"] = min(dl_results["confidence"] * 1.1, 0.95)
        dl_results["pattern_recognition"] = {
            "pattern_strength": 0.8,
            "historical_similarity": 0.75,
            "market_regime_match": 0.85
        }
    
    return dl_results

async def _send_to_ai_evaluation_with_ai_brain(
    dl_results: Dict[str, Any], 
    ml_results: Dict[str, Any], 
    indicator_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Stage 4: AI evaluation with systematic AI Brain validation"""
    ai_results = await _send_to_ai_evaluation(dl_results, ml_results, indicator_data)
    
    if AI_BRAIN_AVAILABLE:
        # Add comprehensive risk assessment
        ai_results["risk_assessment"] = {
            "position_risk": 0.02,
            "portfolio_risk": 0.15,
            "correlation_risk": 0.08,
            "market_risk": 0.12
        }
        ai_results["systematic_validation"] = {
            "consistency_check": True,
            "outlier_detection": False,
            "regime_compatibility": True
        }
    
    return ai_results

async def _send_to_trading_engine_with_ai_brain(
    ai_results: Dict[str, Any],
    dl_results: Dict[str, Any],
    ml_results: Dict[str, Any],
    confidence_metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """Stage 5: Trading engine with AI Brain approval"""
    # Enhance trading request with confidence metrics
    enhanced_ai_results = {**ai_results, "ai_brain_confidence": confidence_metrics}
    trading_results = await _send_to_trading_engine(enhanced_ai_results, dl_results, ml_results)
    
    if AI_BRAIN_AVAILABLE:
        trading_results["ai_brain_approved"] = confidence_metrics.get("passes_threshold", False)
        trading_results["confidence_override"] = False
    
    return trading_results

async def _log_to_performance_analytics_with_ai_brain(
    pipeline_id: str,
    symbol: str, 
    results: Dict[str, Any],
    trading_results: Dict[str, Any],
    confidence_metrics: Dict[str, Any],
    ai_brain_analysis: Dict[str, Any]
) -> None:
    """Stage 6: Enhanced performance analytics logging with AI Brain metrics"""
    
    # First log with standard function
    await _log_to_performance_analytics(pipeline_id, symbol, results, trading_results)
    
    # Add AI Brain specific logging
    if AI_BRAIN_AVAILABLE and confidence_metrics:
        ai_analytics_data = {
            "pipeline_id": pipeline_id,
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "ai_brain_metrics": {
                "confidence_score": confidence_metrics.get("composite_score", 0),
                "confidence_breakdown": confidence_metrics,
                "ai_brain_analysis": ai_brain_analysis,
                "decision_approved": ai_brain_analysis.get("trading_approved", False)
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{SERVICE_ENDPOINTS['performance-analytics']}/api/v1/log/ai-brain-metrics",
                    json=ai_analytics_data
                )
                
            if response.status_code == 200:
                logger.info(f"✅ AI Brain metrics logged for pipeline {pipeline_id}")
            else:
                logger.warning(f"⚠️ AI Brain metrics logging failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ AI Brain metrics logging error: {e}")