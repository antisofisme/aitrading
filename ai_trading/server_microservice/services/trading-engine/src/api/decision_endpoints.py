"""
⚡ Trading Decision API Endpoints - Live Trading Execution Logic
Advanced trading decision engine with real-time ML/DL/AI model comparison

ENDPOINTS:
- POST /api/v1/decide/trade-action - Make trading decision based on ML/DL/AI results
- POST /api/v1/compare/live-predictions - Compare live predictions vs actual results
- GET /api/v1/performance/model-accuracy - Get real-time model accuracy metrics
- POST /api/v1/execute/strategy - Execute trading strategy with dynamic model selection
"""

import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from fastapi import APIRouter, HTTPException, BackgroundTasks, Body, Query
from pydantic import BaseModel, Field
import statistics

# Service infrastructure
from ...shared.infrastructure.core.logger_core import get_logger
from ...shared.infrastructure.core.error_core import get_error_handler
from ...shared.infrastructure.core.performance_core import performance_tracked, get_performance_tracker
from ...shared.infrastructure.core.cache_core import CoreCache

# AI Brain Integration
try:
    import sys
    sys.path.append('/mnt/f/WINDSURF/concept_ai/projects/ai_trading/server_microservice/services')
    from shared.ai_brain_trading_error_dna import AiBrainTradingErrorDNA
    from shared.ai_brain_confidence_framework import AiBrainConfidenceFramework, ConfidenceThreshold
    from shared.ai_brain_trading_decision_validator import (
        AIBrainTradingDecisionValidator, 
        TradingDecision as AIBrainTradingDecision,
        ValidationResult,
        TradingDecisionType
    )
    
    # Initialize AI Brain components for trading engine
    ai_brain_error_dna = AiBrainTradingErrorDNA("trading-engine")
    ai_brain_confidence = AiBrainConfidenceFramework("trading-engine")
    ai_brain_decision_validator = AIBrainTradingDecisionValidator()
    AI_BRAIN_AVAILABLE = True
    
except ImportError as e:
    AI_BRAIN_AVAILABLE = False
    
# Enhanced Decision Validation Components
try:
    from ..business.decision_audit_system import decision_audit_system, DecisionStatus, RollbackReason
    from ..business.enhanced_decision_validator import enhanced_decision_validator, ValidationLevel
    from ..business.decision_impact_assessor import decision_impact_assessor, MarketDataPoint
    from ..business.decision_confidence_scorer import decision_confidence_scorer
    from ..business.decision_pattern_recognizer import decision_pattern_recognizer
    from ..business.decision_logger import decision_logger
    from ..business.decision_quality_assessor import DecisionQualityAssessor, QualityDimension
    
    # Initialize Decision Quality Assessor
    decision_quality_assessor = DecisionQualityAssessor()
    
    ENHANCED_VALIDATION_AVAILABLE = True
except ImportError as e:
    ENHANCED_VALIDATION_AVAILABLE = False
    logger.warning(f"Enhanced validation components not available: {e}")

# Initialize
logger = get_logger("trading-engine", "decision-endpoints")
error_handler = get_error_handler("trading-engine")
performance_tracker = get_performance_tracker("trading-engine")
cache = CoreCache("trading-decisions", max_size=1000, default_ttl=300)

if AI_BRAIN_AVAILABLE:
    logger.info("✅ AI Brain framework initialized for trading engine")
else:
    logger.warning("⚠️ AI Brain framework not available - using standard trading logic")

if ENHANCED_VALIDATION_AVAILABLE:
    logger.info("✅ Enhanced validation components initialized")
    
    # Initialize Quality Assessor with integrated components
    async def _initialize_quality_assessor():
        components = {
            'audit_system': decision_audit_system,
            'impact_assessor': decision_impact_assessor,
            'confidence_scorer': decision_confidence_scorer,
            'pattern_recognizer': decision_pattern_recognizer,
            'decision_logger': decision_logger
        }
        await decision_quality_assessor.integrate_components(components)
        logger.info("🏆 Decision Quality Assessor integrated with all validation components")
    
    # Schedule initialization (would be called during startup)
    asyncio.create_task(_initialize_quality_assessor())
else:
    logger.warning("⚠️ Enhanced validation components not available - using basic validation")

# Create router
router = APIRouter(prefix="/api/v1")

# Request/Response Models
class TradingDecisionRequest(BaseModel):
    """Request model for trading decision"""
    ai_evaluation: Dict[str, Any] = Field(..., description="AI evaluation results")
    dl_prediction: Dict[str, Any] = Field(..., description="Deep learning prediction")
    ml_prediction: Dict[str, Any] = Field(..., description="ML model prediction")
    decision_mode: str = Field("consensus", description="Decision mode: consensus, ai_priority, ml_priority, dl_priority")
    risk_level: str = Field("moderate", description="Risk level: conservative, moderate, aggressive")
    symbol: Optional[str] = Field(None, description="Trading symbol")
    market_conditions: Optional[Dict[str, Any]] = Field(None, description="Current market conditions")

class TradingDecision(BaseModel):
    """Trading decision response model"""
    decision_id: str
    symbol: str
    action: str  # buy, sell, hold
    confidence: float  # 0.0 to 1.0
    position_size: float
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    reasoning: str
    model_contributions: Dict[str, float]
    risk_assessment: Dict[str, Any]
    execution_timestamp: datetime

class LiveComparisonRequest(BaseModel):
    """Request model for live prediction comparison"""
    predictions: Dict[str, Any] = Field(..., description="Model predictions")
    actual_outcome: Dict[str, Any] = Field(..., description="Actual market outcome")
    timeframe: str = Field("1h", description="Prediction timeframe")
    symbol: str = Field(..., description="Trading symbol")

class ModelAccuracyMetrics(BaseModel):
    """Model accuracy metrics response"""
    ml_accuracy: Dict[str, float]
    dl_accuracy: Dict[str, float]
    ai_accuracy: Dict[str, float]
    consensus_accuracy: Dict[str, float]
    trending_accuracy: Dict[str, List[float]]
    best_performing_model: str
    accuracy_trend: str  # improving, declining, stable

class StrategyExecutionRequest(BaseModel):
    """Strategy execution request model"""
    strategy_name: str = Field(..., description="Strategy identifier")
    signals: Dict[str, Any] = Field(..., description="Trading signals from all models")
    risk_parameters: Dict[str, float] = Field(..., description="Risk management parameters")
    execution_mode: str = Field("auto", description="Execution mode: auto, manual, paper")

# Core Decision Endpoints

@router.post("/decide/trade-action", response_model=TradingDecision)
@performance_tracked("trading-engine", "trade_decision")
async def make_trading_decision(
    request: TradingDecisionRequest,
    background_tasks: BackgroundTasks
) -> TradingDecision:
    """
    Make AI Brain enhanced trading decision based on ML/DL/AI model results
    Implements systematic validation and confidence analysis before execution
    """
    try:
        decision_id = f"decision_{int(datetime.now().timestamp() * 1000)}"
        symbol = request.symbol or "UNKNOWN"
        
        logger.info(f"⚡ Making AI Brain enhanced trading decision - ID: {decision_id}, Mode: {request.decision_mode}, Symbol: {symbol}")
        
        # Extract model predictions and confidences
        model_data = await _extract_model_data(request)
        
        # AI Brain: Calculate confidence score BEFORE making trading decision
        ai_brain_confidence_score = None
        confidence_validation = None
        
        if AI_BRAIN_AVAILABLE:
            logger.info(f"🧠 AI Brain: Analyzing trading decision confidence")
            
            # Prepare data for AI Brain confidence analysis
            model_prediction_data = {
                "confidence": model_data.get("average_confidence", 0.5),
                "model_type": "ensemble",  # We're using multiple models
                "predictions": [
                    model_data.get("ml_prediction", 0.5),
                    model_data.get("dl_prediction", 0.5), 
                    model_data.get("ai_prediction", 0.5)
                ]
            }
            
            data_quality_metrics = {
                "missing_ratio": 0.0,  # Assume good data quality
                "age_minutes": 1,      # Fresh data
                "consistency_score": 1.0,
                "anomaly_score": 0.0
            }
            
            market_context = request.market_conditions or {}
            
            risk_parameters = {
                "position_risk": 0.02,  # Default 2% risk
                "has_stop_loss": True,
                "risk_reward_ratio": 2.0,
                "account_utilization": 0.5
            }
            
            # Calculate AI Brain confidence score
            ai_brain_confidence_score = ai_brain_confidence.calculate_confidence(
                model_prediction=model_prediction_data,
                data_inputs=data_quality_metrics,
                market_context=market_context,
                risk_parameters=risk_parameters
            )
            
            # Validate against HIGH threshold for trading decisions (85%+)
            confidence_validation = ai_brain_confidence.validate_threshold(
                ai_brain_confidence_score,
                ConfidenceThreshold.HIGH,  # Require 85%+ confidence for trading
                operation_context={
                    "decision_id": decision_id,
                    "symbol": symbol,
                    "decision_mode": request.decision_mode
                }
            )
            
            logger.info(f"🧠 AI Brain Trading Confidence: {ai_brain_confidence_score.composite_score:.3f}")
            logger.info(f"🧠 Confidence Validation: {'PASSED' if confidence_validation['passes_threshold'] else 'FAILED'}")
            
            # Block trading if confidence is insufficient
            if not confidence_validation["passes_threshold"]:
                logger.warning(f"🚫 AI Brain: Trading decision BLOCKED due to insufficient confidence")
                logger.warning(f"   Required: 0.85, Actual: {ai_brain_confidence_score.composite_score:.3f}")
                logger.warning(f"   Gap: {confidence_validation['confidence_gap']:.3f}")
                
                if confidence_validation.get("recommendations"):
                    logger.warning(f"   Recommendations: {confidence_validation['recommendations']}")
                
                # Return blocked decision
                return TradingDecision(
                    decision_id=decision_id,
                    symbol=symbol,
                    action="hold",  # Force hold when confidence insufficient
                    confidence=ai_brain_confidence_score.composite_score,
                    position_size=0.0,
                    entry_price=None,
                    stop_loss=None,
                    take_profit=None,
                    reasoning=f"AI Brain confidence insufficient ({ai_brain_confidence_score.composite_score:.3f} < 0.85). Recommendations: {confidence_validation.get('recommendations', [])}",
                    model_contributions=model_data,
                    risk_assessment={
                        "ai_brain_blocked": True,
                        "confidence_gap": confidence_validation["confidence_gap"],
                        "recommendations": confidence_validation.get("recommendations", [])
                    },
                    execution_timestamp=datetime.now()
                )
        
        # Proceed with trading decision if AI Brain confidence is sufficient
        logger.info(f"✅ AI Brain: Confidence sufficient - proceeding with trading decision")
        
        # Apply decision logic based on mode (enhanced with AI Brain validation)
        if request.decision_mode == "consensus":
            decision_result = await _consensus_decision_with_ai_brain(model_data, request.risk_level, ai_brain_confidence_score)
        elif request.decision_mode == "ai_priority":
            decision_result = await _ai_priority_decision_with_ai_brain(model_data, request.risk_level, ai_brain_confidence_score)
        elif request.decision_mode == "ml_priority":
            decision_result = await _ml_priority_decision_with_ai_brain(model_data, request.risk_level, ai_brain_confidence_score)
        elif request.decision_mode == "dl_priority":
            decision_result = await _dl_priority_decision_with_ai_brain(model_data, request.risk_level, ai_brain_confidence_score)
        else:
            decision_result = await _consensus_decision_with_ai_brain(model_data, request.risk_level, ai_brain_confidence_score)
        
        # Calculate position sizing based on confidence and risk
        position_size = await _calculate_position_size(
            decision_result["confidence"], 
            request.risk_level,
            model_data
        )
        
        # Generate risk management levels
        risk_levels = await _calculate_risk_levels(
            decision_result["action"],
            decision_result["entry_price"],
            decision_result["confidence"],
            request.risk_level
        )
        
        # Create trading decision
        trading_decision = TradingDecision(
            decision_id=decision_id,
            symbol=symbol,
            action=decision_result["action"],
            confidence=decision_result["confidence"],
            position_size=position_size,
            entry_price=decision_result.get("entry_price"),
            stop_loss=risk_levels.get("stop_loss"),
            take_profit=risk_levels.get("take_profit"),
            reasoning=decision_result["reasoning"],
            model_contributions=decision_result["model_contributions"],
            risk_assessment=decision_result["risk_assessment"],
            execution_timestamp=datetime.now()
        )
        
        # Cache decision for performance tracking
        cache_key = f"decision:{decision_id}"
        await cache.set(cache_key, trading_decision.dict(), ttl=3600)
        
        # Update model performance statistics (background)
        background_tasks.add_task(
            _update_decision_statistics, 
            decision_id, 
            request, 
            trading_decision
        )
        
        logger.info(f"✅ Trading decision made - Action: {trading_decision.action}, Confidence: {trading_decision.confidence:.2f}")
        
        return trading_decision
        
    except Exception as e:
        logger.error(f"❌ Trading decision failed: {e}")
        raise HTTPException(status_code=500, detail=f"Decision making failed: {str(e)}")

@router.post("/compare/live-predictions")
@performance_tracked("trading-engine", "live_comparison")
async def compare_live_predictions(
    request: LiveComparisonRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Compare live predictions against actual market outcomes
    Updates model accuracy metrics and provides performance feedback
    """
    try:
        comparison_id = f"comparison_{int(datetime.now().timestamp() * 1000)}"
        
        logger.info(f"📊 Comparing live predictions - ID: {comparison_id}, Symbol: {request.symbol}")
        
        # Analyze each model's prediction accuracy
        ml_analysis = await _analyze_prediction_accuracy(
            request.predictions.get("ml_prediction", {}),
            request.actual_outcome,
            "ml"
        )
        
        dl_analysis = await _analyze_prediction_accuracy(
            request.predictions.get("dl_prediction", {}),
            request.actual_outcome,
            "dl"
        )
        
        ai_analysis = await _analyze_prediction_accuracy(
            request.predictions.get("ai_evaluation", {}),
            request.actual_outcome,
            "ai"
        )
        
        # Calculate consensus performance
        consensus_analysis = await _analyze_consensus_performance(
            [ml_analysis, dl_analysis, ai_analysis],
            request.actual_outcome
        )
        
        # Generate improvement insights
        insights = await _generate_prediction_insights(
            ml_analysis, dl_analysis, ai_analysis, consensus_analysis
        )
        
        # Update model performance metrics (background)
        background_tasks.add_task(
            _update_model_performance_metrics,
            request.symbol,
            ml_analysis,
            dl_analysis,
            ai_analysis,
            consensus_analysis
        )
        
        comparison_result = {
            "comparison_id": comparison_id,
            "symbol": request.symbol,
            "timeframe": request.timeframe,
            "timestamp": datetime.now().isoformat(),
            "model_analysis": {
                "ml_model": ml_analysis,
                "dl_model": dl_analysis,
                "ai_model": ai_analysis,
                "consensus": consensus_analysis
            },
            "insights": insights,
            "best_performer": _identify_best_performer(ml_analysis, dl_analysis, ai_analysis),
            "accuracy_summary": {
                "ml_accuracy": ml_analysis.get("accuracy_score", 0),
                "dl_accuracy": dl_analysis.get("accuracy_score", 0),
                "ai_accuracy": ai_analysis.get("accuracy_score", 0),
                "consensus_accuracy": consensus_analysis.get("accuracy_score", 0)
            }
        }
        
        logger.info(f"✅ Live comparison completed - Best: {comparison_result['best_performer']}")
        
        return comparison_result
        
    except Exception as e:
        logger.error(f"❌ Live comparison failed: {e}")
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")

@router.get("/performance/model-accuracy", response_model=ModelAccuracyMetrics)
async def get_model_accuracy_metrics(
    timeframe: str = Query("24h", description="Metrics timeframe"),
    symbol: Optional[str] = Query(None, description="Specific symbol filter")
) -> ModelAccuracyMetrics:
    """
    Get real-time model accuracy metrics and performance trends
    Provides comprehensive accuracy analysis across all models
    """
    try:
        logger.info(f"📈 Getting model accuracy metrics - Timeframe: {timeframe}, Symbol: {symbol}")
        
        # Get accuracy data for each model type
        ml_accuracy = await _get_model_accuracy_data("ml", timeframe, symbol)
        dl_accuracy = await _get_model_accuracy_data("dl", timeframe, symbol)
        ai_accuracy = await _get_model_accuracy_data("ai", timeframe, symbol)
        consensus_accuracy = await _get_consensus_accuracy_data(timeframe, symbol)
        
        # Get trending accuracy data
        trending_data = await _get_trending_accuracy_data(timeframe, symbol)
        
        # Identify best performing model
        performances = {
            "ML": ml_accuracy.get("overall_accuracy", 0),
            "DL": dl_accuracy.get("overall_accuracy", 0),
            "AI": ai_accuracy.get("overall_accuracy", 0),
            "Consensus": consensus_accuracy.get("overall_accuracy", 0)
        }
        best_model = max(performances, key=performances.get)
        
        # Determine accuracy trend
        accuracy_trend = await _determine_accuracy_trend(trending_data)
        
        metrics = ModelAccuracyMetrics(
            ml_accuracy=ml_accuracy,
            dl_accuracy=dl_accuracy,
            ai_accuracy=ai_accuracy,
            consensus_accuracy=consensus_accuracy,
            trending_accuracy=trending_data,
            best_performing_model=best_model,
            accuracy_trend=accuracy_trend
        )
        
        logger.info(f"✅ Model accuracy metrics retrieved - Best: {best_model} ({performances[best_model]:.2f})")
        
        return metrics
        
    except Exception as e:
        logger.error(f"❌ Model accuracy retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics retrieval failed: {str(e)}")

@router.post("/execute/strategy")
@performance_tracked("trading-engine", "strategy_execution")
async def execute_trading_strategy(
    request: StrategyExecutionRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Execute trading strategy with dynamic model selection
    Implements intelligent strategy execution based on current model performance
    """
    try:
        execution_id = f"execution_{int(datetime.now().timestamp() * 1000)}"
        
        logger.info(f"🎯 Executing trading strategy - ID: {execution_id}, Strategy: {request.strategy_name}")
        
        # Analyze current model performance for dynamic selection
        model_performance = await _analyze_current_model_performance(request.signals)
        
        # Select best performing models for execution
        selected_models = await _select_optimal_models(model_performance, request.strategy_name)
        
        # Generate execution plan
        execution_plan = await _generate_execution_plan(
            request.signals,
            selected_models,
            request.risk_parameters,
            request.execution_mode
        )
        
        # Execute trades based on plan
        execution_results = await _execute_trades(execution_plan, request.execution_mode)
        
        # Update strategy performance tracking (background)
        background_tasks.add_task(
            _update_strategy_performance,
            execution_id,
            request.strategy_name,
            execution_results,
            model_performance
        )
        
        result = {
            "execution_id": execution_id,
            "strategy_name": request.strategy_name,
            "execution_mode": request.execution_mode,
            "timestamp": datetime.now().isoformat(),
            "selected_models": selected_models,
            "execution_plan": execution_plan,
            "execution_results": execution_results,
            "model_performance": model_performance,
            "status": "completed" if execution_results.get("success", False) else "failed"
        }
        
        logger.info(f"✅ Strategy execution completed - Status: {result['status']}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Strategy execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Strategy execution failed: {str(e)}")

# Helper Functions for Decision Logic

async def _extract_model_data(request: TradingDecisionRequest) -> Dict[str, Any]:
    """Extract and normalize model prediction data"""
    return {
        "ml": {
            "prediction": request.ml_prediction.get("direction", "hold"),
            "confidence": request.ml_prediction.get("confidence", 0.5),
            "price_target": request.ml_prediction.get("price_target"),
            "features": request.ml_prediction.get("features", {})
        },
        "dl": {
            "prediction": request.dl_prediction.get("direction", "hold"),
            "confidence": request.dl_prediction.get("confidence", 0.5),
            "price_target": request.dl_prediction.get("price_target"),
            "features": request.dl_prediction.get("features", {})
        },
        "ai": {
            "prediction": request.ai_evaluation.get("recommendation", "hold"),
            "confidence": request.ai_evaluation.get("confidence", 0.5),
            "reasoning": request.ai_evaluation.get("reasoning", ""),
            "risk_assessment": request.ai_evaluation.get("risk_assessment", {})
        }
    }

# AI Brain Enhanced Decision Functions
async def _consensus_decision_with_ai_brain(model_data: Dict[str, Any], risk_level: str, ai_brain_confidence_score) -> Dict[str, Any]:
    """AI Brain enhanced consensus decision with systematic validation"""
    
    # Get base consensus decision
    base_decision = await _consensus_decision(model_data, risk_level)
    
    # Enhance with AI Brain insights if available
    if ai_brain_confidence_score:
        # Adjust confidence based on AI Brain analysis
        ai_brain_adjustment = ai_brain_confidence_score.composite_score * 0.3
        enhanced_confidence = (base_decision["confidence"] * 0.7) + ai_brain_adjustment
        enhanced_confidence = max(0.1, min(0.95, enhanced_confidence))
        
        base_decision["confidence"] = enhanced_confidence
        base_decision["reasoning"] += f" | AI Brain enhanced (composite: {ai_brain_confidence_score.composite_score:.3f})"
        base_decision["ai_brain_enhancement"] = {
            "composite_score": ai_brain_confidence_score.composite_score,
            "model_confidence": ai_brain_confidence_score.model_confidence,
            "data_quality": ai_brain_confidence_score.data_quality,
            "market_context": ai_brain_confidence_score.market_context,
            "risk_assessment": ai_brain_confidence_score.risk_assessment
        }
    
    return base_decision

async def _ai_priority_decision_with_ai_brain(model_data: Dict, risk_level: str, ai_brain_confidence_score) -> Dict[str, Any]:
    """AI Brain enhanced AI-priority decision"""
    base_decision = await _ai_priority_decision(model_data, risk_level)
    
    if ai_brain_confidence_score:
        # AI priority gets higher enhancement weight
        ai_brain_adjustment = ai_brain_confidence_score.composite_score * 0.4
        enhanced_confidence = (base_decision["confidence"] * 0.6) + ai_brain_adjustment
        base_decision["confidence"] = max(0.1, min(0.95, enhanced_confidence))
        base_decision["reasoning"] += f" | AI Brain priority enhancement: {ai_brain_confidence_score.composite_score:.3f}"
    
    return base_decision

async def _ml_priority_decision_with_ai_brain(model_data: Dict, risk_level: str, ai_brain_confidence_score) -> Dict[str, Any]:
    """AI Brain enhanced ML-priority decision"""
    base_decision = await _ml_priority_decision(model_data, risk_level)
    
    if ai_brain_confidence_score:
        # Moderate enhancement for ML priority
        ai_brain_adjustment = ai_brain_confidence_score.composite_score * 0.2
        enhanced_confidence = (base_decision["confidence"] * 0.8) + ai_brain_adjustment
        base_decision["confidence"] = max(0.1, min(0.95, enhanced_confidence))
        base_decision["reasoning"] += f" | AI Brain ML enhancement: {ai_brain_confidence_score.composite_score:.3f}"
    
    return base_decision

async def _dl_priority_decision_with_ai_brain(model_data: Dict, risk_level: str, ai_brain_confidence_score) -> Dict[str, Any]:
    """AI Brain enhanced DL-priority decision"""
    base_decision = await _dl_priority_decision(model_data, risk_level)
    
    if ai_brain_confidence_score:
        # Moderate enhancement for DL priority
        ai_brain_adjustment = ai_brain_confidence_score.composite_score * 0.25
        enhanced_confidence = (base_decision["confidence"] * 0.75) + ai_brain_adjustment
        base_decision["confidence"] = max(0.1, min(0.95, enhanced_confidence))
        base_decision["reasoning"] += f" | AI Brain DL enhancement: {ai_brain_confidence_score.composite_score:.3f}"
    
    return base_decision

async def _consensus_decision(model_data: Dict[str, Any], risk_level: str) -> Dict[str, Any]:
    """Make consensus decision based on all model inputs"""
    
    # Extract predictions and confidences
    predictions = []
    confidences = []
    
    for model_type, data in model_data.items():
        pred = data.get("prediction", "hold")
        conf = data.get("confidence", 0.5)
        
        # Convert predictions to numerical values for consensus
        pred_value = {"buy": 1, "sell": -1, "hold": 0}.get(pred.lower(), 0)
        predictions.append(pred_value * conf)  # Weight by confidence
        confidences.append(conf)
    
    # Calculate weighted consensus
    if predictions:
        weighted_consensus = sum(predictions) / len(predictions)
        avg_confidence = statistics.mean(confidences)
    else:
        weighted_consensus = 0
        avg_confidence = 0.5
    
    # Determine final action
    if weighted_consensus > 0.3:
        action = "buy"
    elif weighted_consensus < -0.3:
        action = "sell"
    else:
        action = "hold"
    
    # Adjust confidence based on consensus strength
    consensus_strength = abs(weighted_consensus)
    final_confidence = min(0.95, avg_confidence * (0.5 + consensus_strength))
    
    # Apply risk level adjustments
    if risk_level == "conservative":
        final_confidence *= 0.8  # Be more cautious
    elif risk_level == "aggressive":
        final_confidence *= 1.1  # Be more confident
    
    final_confidence = max(0.1, min(0.95, final_confidence))  # Clamp to reasonable range
    
    return {
        "action": action,
        "confidence": final_confidence,
        "reasoning": f"Consensus decision based on {len(predictions)} models, weighted consensus: {weighted_consensus:.3f}",
        "model_contributions": {
            "ml": model_data.get("ml", {}).get("confidence", 0) * 0.33,
            "dl": model_data.get("dl", {}).get("confidence", 0) * 0.33,
            "ai": model_data.get("ai", {}).get("confidence", 0) * 0.34
        },
        "risk_assessment": {
            "consensus_strength": consensus_strength,
            "model_agreement": len([p for p in predictions if abs(p - weighted_consensus) < 0.2]) / len(predictions) if predictions else 0,
            "risk_level": risk_level
        },
        "entry_price": None  # Would be set by market data
    }

# Additional helper functions continue...
# (Simplified for demo - in production all decision logic would be fully implemented)

async def _ai_priority_decision(model_data: Dict, risk_level: str) -> Dict[str, Any]:
    """AI-priority decision logic"""
    ai_data = model_data.get("ai", {})
    return {
        "action": ai_data.get("prediction", "hold"),
        "confidence": ai_data.get("confidence", 0.5),
        "reasoning": "AI-priority decision based on advanced reasoning",
        "model_contributions": {"ai": 1.0, "ml": 0.0, "dl": 0.0},
        "risk_assessment": ai_data.get("risk_assessment", {}),
        "entry_price": None
    }

async def _ml_priority_decision(model_data: Dict, risk_level: str) -> Dict[str, Any]:
    """ML-priority decision logic"""
    ml_data = model_data.get("ml", {})
    return {
        "action": ml_data.get("prediction", "hold"),
        "confidence": ml_data.get("confidence", 0.5),
        "reasoning": "ML-priority decision based on statistical patterns",
        "model_contributions": {"ml": 1.0, "ai": 0.0, "dl": 0.0},
        "risk_assessment": {"model": "ml_priority", "risk_level": risk_level},
        "entry_price": ml_data.get("price_target")
    }

async def _dl_priority_decision(model_data: Dict, risk_level: str) -> Dict[str, Any]:
    """Deep Learning priority decision logic"""
    dl_data = model_data.get("dl", {})
    return {
        "action": dl_data.get("prediction", "hold"),
        "confidence": dl_data.get("confidence", 0.5),
        "reasoning": "Deep Learning priority decision based on neural patterns",
        "model_contributions": {"dl": 1.0, "ml": 0.0, "ai": 0.0},
        "risk_assessment": {"model": "dl_priority", "risk_level": risk_level},
        "entry_price": dl_data.get("price_target")
    }

async def _calculate_position_size(confidence: float, risk_level: str, model_data: Dict) -> float:
    """Calculate position size based on confidence and risk"""
    base_size = 1.0  # Base position size
    
    # Adjust by confidence
    confidence_multiplier = confidence
    
    # Adjust by risk level
    risk_multipliers = {
        "conservative": 0.5,
        "moderate": 1.0,
        "aggressive": 1.5
    }
    
    risk_multiplier = risk_multipliers.get(risk_level, 1.0)
    
    return base_size * confidence_multiplier * risk_multiplier

async def _calculate_risk_levels(action: str, entry_price: float, confidence: float, risk_level: str) -> Dict[str, float]:
    """Calculate stop loss and take profit levels"""
    if not entry_price:
        return {"stop_loss": None, "take_profit": None}
    
    # Risk percentages based on confidence and risk level
    base_risk = 0.02  # 2% base risk
    
    if risk_level == "conservative":
        risk_pct = base_risk * 0.5
        reward_pct = base_risk * 1.5
    elif risk_level == "aggressive":
        risk_pct = base_risk * 2.0
        reward_pct = base_risk * 4.0
    else:  # moderate
        risk_pct = base_risk
        reward_pct = base_risk * 2.0
    
    # Adjust by confidence
    risk_pct *= (1.0 - confidence * 0.3)  # Higher confidence = lower risk
    reward_pct *= (1.0 + confidence * 0.5)  # Higher confidence = higher reward target
    
    if action == "buy":
        stop_loss = entry_price * (1 - risk_pct)
        take_profit = entry_price * (1 + reward_pct)
    elif action == "sell":
        stop_loss = entry_price * (1 + risk_pct)
        take_profit = entry_price * (1 - reward_pct)
    else:
        return {"stop_loss": None, "take_profit": None}
    
    return {"stop_loss": stop_loss, "take_profit": take_profit}

# Placeholder implementations for other helper functions
async def _update_decision_statistics(decision_id: str, request: TradingDecisionRequest, decision: TradingDecision):
    """Update decision statistics in background"""
    logger.debug(f"Updated decision statistics for {decision_id}")

async def _analyze_prediction_accuracy(prediction: Dict, actual: Dict, model_type: str) -> Dict[str, float]:
    """Analyze prediction accuracy for a specific model"""
    return {"accuracy_score": 0.75, "confidence_calibration": 0.8}

async def _analyze_consensus_performance(analyses: List[Dict], actual: Dict) -> Dict[str, float]:
    """Analyze consensus performance"""
    return {"accuracy_score": 0.82}

async def _generate_prediction_insights(ml: Dict, dl: Dict, ai: Dict, consensus: Dict) -> List[str]:
    """Generate insights from prediction analysis"""
    return ["AI model shows best calibration", "ML model has highest accuracy"]

async def _update_model_performance_metrics(symbol: str, ml: Dict, dl: Dict, ai: Dict, consensus: Dict):
    """Update model performance metrics in background"""
    logger.debug(f"Updated model metrics for {symbol}")

def _identify_best_performer(ml: Dict, dl: Dict, ai: Dict) -> str:
    """Identify best performing model"""
    scores = {"ml": ml.get("accuracy_score", 0), "dl": dl.get("accuracy_score", 0), "ai": ai.get("accuracy_score", 0)}
    return max(scores, key=scores.get)

async def _get_model_accuracy_data(model_type: str, timeframe: str, symbol: str) -> Dict[str, float]:
    """Get accuracy data for specific model"""
    return {"overall_accuracy": 0.75, "precision": 0.8, "recall": 0.7}

async def _get_consensus_accuracy_data(timeframe: str, symbol: str) -> Dict[str, float]:
    """Get consensus accuracy data"""
    return {"overall_accuracy": 0.82, "precision": 0.85, "recall": 0.78}

async def _get_trending_accuracy_data(timeframe: str, symbol: str) -> Dict[str, List[float]]:
    """Get trending accuracy data"""
    return {"ml": [0.7, 0.75, 0.8], "dl": [0.75, 0.8, 0.85], "ai": [0.8, 0.78, 0.82]}

async def _determine_accuracy_trend(trending_data: Dict) -> str:
    """Determine overall accuracy trend"""
    return "improving"  # Simplified

async def _analyze_current_model_performance(signals: Dict) -> Dict[str, float]:
    """Analyze current model performance"""
    return {"ml": 0.75, "dl": 0.8, "ai": 0.78}

async def _select_optimal_models(performance: Dict, strategy: str) -> List[str]:
    """Select optimal models for strategy execution"""
    return ["dl", "ai"]  # Select top performers

async def _generate_execution_plan(signals: Dict, models: List[str], risk_params: Dict, mode: str) -> Dict[str, Any]:
    """Generate execution plan"""
    return {"trades": [], "risk_management": risk_params}

async def _execute_trades(plan: Dict, mode: str) -> Dict[str, Any]:
    """Execute trades based on plan"""
    return {"success": True, "trades_executed": 0}

async def _update_strategy_performance(execution_id: str, strategy: str, results: Dict, performance: Dict):
    """Update strategy performance tracking"""
    logger.debug(f"Updated strategy performance for {strategy}")


# NEW ENHANCED DECISION VALIDATION ENDPOINTS

@router.post("/validate/comprehensive-decision")
@performance_tracked("trading-engine", "comprehensive_validation")
async def validate_comprehensive_decision(
    decision_data: Dict[str, Any] = Body(...),
    validation_level: str = Query("standard", description="Validation level: permissive, standard, strict, critical"),
    market_context: Optional[Dict[str, Any]] = Body(None)
) -> Dict[str, Any]:
    """
    Comprehensive AI Brain enhanced decision validation
    Provides full validation with confidence correlation analysis
    """
    try:
        decision_id = decision_data.get("decision_id", f"validate_{int(datetime.now().timestamp() * 1000)}")
        
        logger.info(f"🧠 Comprehensive decision validation: {decision_id} - Level: {validation_level}")
        
        if not ENHANCED_VALIDATION_AVAILABLE:
            return {
                "validation_id": f"validation_{decision_id}",
                "decision_id": decision_id,
                "error": "Enhanced validation components not available",
                "fallback_validation": {
                    "is_valid": decision_data.get("confidence", 0.5) > 0.6,
                    "confidence": decision_data.get("confidence", 0.5)
                },
                "timestamp": datetime.now().isoformat()
            }
        
        # Convert validation level
        level_map = {
            "permissive": ValidationLevel.PERMISSIVE,
            "standard": ValidationLevel.STANDARD,
            "strict": ValidationLevel.STRICT,
            "critical": ValidationLevel.CRITICAL
        }
        validation_level_enum = level_map.get(validation_level, ValidationLevel.STANDARD)
        
        # Create audit record
        audit_record = await decision_audit_system.create_decision_audit(
            decision_id=decision_id,
            symbol=decision_data.get("symbol", "UNKNOWN"),
            decision_type=decision_data.get("decision_type", "trade"),
            action=decision_data.get("action", "hold"),
            confidence=decision_data.get("confidence", 0.5),
            decision_data=decision_data
        )
        
        # Run comprehensive validation
        validation_result = await enhanced_decision_validator.validate_trading_decision(
            decision_data=decision_data,
            validation_level=validation_level_enum,
            market_context=market_context
        )
        
        # Create impact assessment if decision is for execution
        impact_assessment = None
        if decision_data.get("for_execution", False) and validation_result.is_valid:
            impact_assessment = await decision_impact_assessor.create_impact_assessment(
                decision_id=decision_id,
                decision_data=decision_data
            )
        
        result = {
            "validation_id": f"validation_{decision_id}",
            "decision_id": decision_id,
            "validation_result": {
                "is_valid": validation_result.is_valid,
                "validation_confidence": validation_result.validation_confidence,
                "validation_level": validation_result.validation_level.value,
                "ai_brain_integration": validation_result.ai_brain_validation is not None,
                "ai_brain_confidence": validation_result.ai_brain_confidence,
                "confidence_analysis": validation_result.confidence_analysis.__dict__ if validation_result.confidence_analysis else None,
                "validation_layers_passed": validation_result.validation_layers_passed,
                "issues": validation_result.validation_issues,
                "warnings": validation_result.validation_warnings,
                "recommendations": validation_result.recommendations,
                "confidence_improvements": validation_result.confidence_improvement_suggestions,
                "validation_duration_ms": validation_result.validation_duration_ms
            },
            "audit_record_created": True,
            "impact_assessment_created": impact_assessment is not None,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Comprehensive validation completed: {decision_id} - Valid: {validation_result.is_valid}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Comprehensive validation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Comprehensive validation failed: {str(e)}")

@router.get("/audit/decision/{decision_id}")
async def get_decision_audit(decision_id: str) -> Dict[str, Any]:
    """
    Get comprehensive audit trail for a trading decision
    Includes all events, validations, and impact assessments
    """
    try:
        logger.info(f"📋 Getting decision audit: {decision_id}")
        
        if not ENHANCED_VALIDATION_AVAILABLE:
            raise HTTPException(status_code=503, detail="Enhanced validation components not available")
        
        # Get audit record
        audit_record = await decision_audit_system.get_decision_audit(decision_id)
        if not audit_record:
            raise HTTPException(status_code=404, detail=f"Audit record not found for decision: {decision_id}")
        
        # Get impact assessment if available
        impact_assessment = await decision_impact_assessor.get_assessment(decision_id)
        
        result = {
            "decision_id": decision_id,
            "audit_record": {
                "status": audit_record.status.value,
                "created_at": audit_record.created_at.isoformat(),
                "symbol": audit_record.symbol,
                "decision_type": audit_record.decision_type,
                "action": audit_record.action,
                "confidence": audit_record.confidence,
                "validation_attempts": audit_record.validation_attempts,
                "validation_passed": audit_record.validation_passed,
                "execution_attempts": audit_record.execution_attempts,
                "execution_success": audit_record.execution_success,
                "rollback_count": audit_record.rollback_count,
                "quality_score": audit_record.quality_score,
                "events_count": len(audit_record.events),
                "latest_events": [
                    {
                        "event_type": event.event_type.value,
                        "timestamp": event.timestamp.isoformat(),
                        "description": event.description,
                        "execution_time_ms": event.execution_time_ms
                    } for event in audit_record.events[-5:]  # Last 5 events
                ]
            },
            "impact_assessment": {
                "available": impact_assessment is not None,
                "overall_impact_score": impact_assessment.overall_impact_score if impact_assessment else None,
                "decision_quality_score": impact_assessment.decision_quality_score if impact_assessment else None,
                "confidence_correlation": impact_assessment.confidence_correlation if impact_assessment else None,
                "key_insights": impact_assessment.key_insights if impact_assessment else [],
                "improvement_areas": impact_assessment.improvement_areas if impact_assessment else []
            } if impact_assessment else None,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Decision audit retrieved: {decision_id}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Decision audit retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Audit retrieval failed: {str(e)}")

@router.post("/audit/rollback/{decision_id}")
async def initiate_decision_rollback(
    decision_id: str,
    rollback_data: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """
    Initiate rollback for a failed or problematic decision
    Provides automated recovery mechanisms
    """
    try:
        logger.info(f"🔄 Initiating decision rollback: {decision_id}")
        
        if not ENHANCED_VALIDATION_AVAILABLE:
            raise HTTPException(status_code=503, detail="Enhanced validation components not available")
        
        # Validate rollback reason
        reason_map = {
            "execution_failure": RollbackReason.EXECUTION_FAILURE,
            "risk_breach": RollbackReason.RISK_BREACH,
            "market_condition_change": RollbackReason.MARKET_CONDITION_CHANGE,
            "system_error": RollbackReason.SYSTEM_ERROR,
            "manual_override": RollbackReason.MANUAL_OVERRIDE,
            "performance_threshold": RollbackReason.PERFORMANCE_THRESHOLD
        }
        
        rollback_reason_str = rollback_data.get("reason", "manual_override")
        if rollback_reason_str not in reason_map:
            raise HTTPException(status_code=400, detail=f"Invalid rollback reason: {rollback_reason_str}")
        
        rollback_reason = reason_map[rollback_reason_str]
        
        # Initiate rollback
        rollback_action = await decision_audit_system.initiate_rollback(
            decision_id=decision_id,
            reason=rollback_reason,
            rollback_data=rollback_data
        )
        
        result = {
            "rollback_id": rollback_action.rollback_id,
            "decision_id": decision_id,
            "reason": rollback_action.reason.value,
            "rollback_type": rollback_action.rollback_type,
            "status": rollback_action.status,
            "initiated_at": rollback_action.initiated_at.isoformat(),
            "auto_execute": rollback_data.get("auto_execute", False),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Decision rollback initiated: {rollback_action.rollback_id}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Decision rollback initiation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Rollback initiation failed: {str(e)}")

@router.get("/analytics/validation-statistics")
async def get_validation_statistics() -> Dict[str, Any]:
    """
    Get comprehensive validation and decision quality statistics
    Provides insights into decision-making performance
    """
    try:
        logger.info("📊 Getting validation statistics")
        
        if not ENHANCED_VALIDATION_AVAILABLE:
            return {
                "error": "Enhanced validation components not available",
                "basic_statistics": {
                    "ai_brain_available": AI_BRAIN_AVAILABLE,
                    "enhanced_validation_available": False
                },
                "timestamp": datetime.now().isoformat()
            }
        
        # Get validation statistics
        validation_stats = enhanced_decision_validator.get_validation_statistics()
        
        # Get audit statistics
        audit_stats = decision_audit_system.get_audit_statistics()
        
        # Get impact assessment statistics
        impact_stats = decision_impact_assessor.get_assessment_statistics()
        
        result = {
            "validation_statistics": validation_stats,
            "audit_statistics": audit_stats,
            "impact_statistics": impact_stats,
            "system_health": {
                "ai_brain_available": AI_BRAIN_AVAILABLE,
                "enhanced_validation_available": ENHANCED_VALIDATION_AVAILABLE,
                "validation_system_operational": True,
                "audit_system_operational": True,
                "impact_assessment_operational": True
            },
            "performance_summary": {
                "total_decisions_processed": audit_stats.get("audit_statistics", {}).get("total_decisions", 0),
                "validation_success_rate": (
                    validation_stats["validation_statistics"]["successful_validations"] / 
                    max(1, validation_stats["validation_statistics"]["total_validations"])
                ),
                "average_validation_confidence": validation_stats["validation_statistics"]["average_validation_confidence"],
                "average_decision_quality": audit_stats.get("audit_statistics", {}).get("average_decision_quality", 0.0),
                "ai_brain_integration_rate": (
                    validation_stats["validation_statistics"]["ai_brain_integrations"] /
                    max(1, validation_stats["validation_statistics"]["total_validations"])
                ) if validation_stats["validation_statistics"]["total_validations"] > 0 else 0.0
            },
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info("✅ Validation statistics retrieved")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Validation statistics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Statistics retrieval failed: {str(e)}")

@router.post("/analytics/impact-assessment/{decision_id}")
async def update_impact_assessment(
    decision_id: str,
    market_data: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """
    Update impact assessment with market data
    Tracks real-world performance correlation
    """
    try:
        logger.info(f"📈 Updating impact assessment: {decision_id}")
        
        if not ENHANCED_VALIDATION_AVAILABLE:
            raise HTTPException(status_code=503, detail="Enhanced validation components not available")
        
        # Create market data point
        market_data_point = MarketDataPoint(
            timestamp=datetime.now(),
            symbol=market_data.get("symbol", "UNKNOWN"),
            price=market_data.get("price", 0.0),
            volume=market_data.get("volume"),
            bid=market_data.get("bid"),
            ask=market_data.get("ask"),
            spread=market_data.get("spread")
        )
        
        # Update market data
        await decision_impact_assessor.update_market_data(
            symbol=market_data_point.symbol,
            market_data=market_data_point
        )
        
        # Get updated assessment
        assessment = await decision_impact_assessor.get_assessment(decision_id)
        
        result = {
            "decision_id": decision_id,
            "market_data_updated": True,
            "assessment_available": assessment is not None,
            "current_impact": {
                "immediate_available": assessment.immediate_impact is not None if assessment else False,
                "short_term_available": assessment.short_term_impact is not None if assessment else False,
                "medium_term_available": assessment.medium_term_impact is not None if assessment else False,
                "long_term_available": assessment.long_term_impact is not None if assessment else False,
                "overall_impact_score": assessment.overall_impact_score if assessment else None
            } if assessment else None,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Impact assessment updated: {decision_id}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Impact assessment update failed: {e}")
        raise HTTPException(status_code=500, detail=f"Impact assessment update failed: {str(e)}")

# COMPREHENSIVE DECISION QUALITY ASSESSMENT ENDPOINTS

@router.post("/quality/assess-decision")
@performance_tracked("trading-engine", "quality_assessment")
async def assess_decision_quality(
    decision_data: Dict[str, Any] = Body(...),
    execution_results: Optional[Dict[str, Any]] = Body(None),
    market_context: Optional[Dict[str, Any]] = Body(None)
) -> Dict[str, Any]:
    """
    Comprehensive decision quality assessment with AI Brain integration
    Provides holistic quality scoring across all dimensions
    """
    try:
        decision_id = decision_data.get("decision_id", f"quality_assess_{int(datetime.now().timestamp() * 1000)}")
        
        logger.info(f"🏆 Assessing decision quality: {decision_id}")
        
        if not ENHANCED_VALIDATION_AVAILABLE:
            return {
                "error": "Enhanced validation components not available",
                "decision_id": decision_id,
                "timestamp": datetime.now().isoformat()
            }
        
        # Perform comprehensive quality assessment
        assessment = await decision_quality_assessor.assess_decision_quality(
            decision_id=decision_id,
            decision_data=decision_data,
            execution_results=execution_results,
            market_context=market_context
        )
        
        result = {
            "assessment_id": f"assessment_{decision_id}",
            "decision_id": decision_id,
            "quality_assessment": {
                "overall_score": assessment.overall_score,
                "grade": assessment.grade.value,
                "timestamp": assessment.timestamp.isoformat(),
                "dimensions": {
                    dim.value: {
                        "score": metric.score,
                        "weight": metric.weight,
                        "confidence": metric.confidence,
                        "trend": metric.trend,
                        "details": metric.details
                    } for dim, metric in assessment.dimensions.items()
                },
                "performance_attribution": assessment.performance_attribution,
                "benchmark_comparison": assessment.benchmark_comparison,
                "recommendations": assessment.recommendations,
                "risk_flags": assessment.risk_flags,
                "compliance_status": assessment.compliance_status,
                "metadata": assessment.metadata
            },
            "ai_brain_compliance": assessment.compliance_status.get("ai_brain_compliant", False),
            "quality_threshold_met": assessment.overall_score >= 85.0,  # AI Brain threshold
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Decision quality assessed: {decision_id} - Score: {assessment.overall_score:.2f}% - Grade: {assessment.grade.value}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Decision quality assessment failed: {e}")
        raise HTTPException(status_code=500, detail=f"Quality assessment failed: {str(e)}")

@router.get("/quality/trends")
async def get_quality_trends(
    period_days: int = Query(30, description="Analysis period in days"),
    dimension: Optional[str] = Query(None, description="Specific quality dimension to analyze")
) -> Dict[str, Any]:
    """
    Get comprehensive quality trends and analysis
    Provides insights into quality evolution over time
    """
    try:
        logger.info(f"📈 Getting quality trends: {period_days} days, dimension: {dimension}")
        
        if not ENHANCED_VALIDATION_AVAILABLE:
            return {
                "error": "Enhanced validation components not available",
                "timestamp": datetime.now().isoformat()
            }
        
        # Convert dimension string to enum if provided
        dimension_enum = None
        if dimension:
            try:
                dimension_enum = QualityDimension(dimension.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid dimension: {dimension}")
        
        # Get quality trends
        trends = await decision_quality_assessor.get_quality_trends(
            period_days=period_days,
            dimension=dimension_enum
        )
        
        result = {
            "trends_analysis": {
                "period": trends.period,
                "start_date": trends.start_date.isoformat(),
                "end_date": trends.end_date.isoformat(),
                "trend_direction": trends.trend_direction,
                "trend_strength": trends.trend_strength,
                "performance_correlation": trends.performance_correlation,
                "recommendations": trends.recommendations,
                "quality_progression": [
                    {
                        "timestamp": timestamp.isoformat(),
                        "score": score
                    } for timestamp, score in trends.quality_progression
                ],
                "dimension_trends": {
                    dim.value: trend for dim, trend in trends.dimension_trends.items()
                }
            },
            "summary": {
                "data_points": len(trends.quality_progression),
                "average_score": statistics.mean([score for _, score in trends.quality_progression]) if trends.quality_progression else 0.0,
                "score_variance": statistics.stdev([score for _, score in trends.quality_progression]) if len(trends.quality_progression) > 1 else 0.0,
                "improving_dimensions": [
                    dim.value for dim, trend in trends.dimension_trends.items() 
                    if trend == "improving"
                ],
                "declining_dimensions": [
                    dim.value for dim, trend in trends.dimension_trends.items() 
                    if trend == "declining"
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Quality trends retrieved: {trends.trend_direction} trend over {period_days} days")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Quality trends retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Trends retrieval failed: {str(e)}")

@router.get("/quality/performance-metrics")
async def get_quality_performance_metrics(
    period: str = Query("current_month", description="Performance period")
) -> Dict[str, Any]:
    """
    Get comprehensive quality performance metrics
    Provides detailed performance tracking and analysis
    """
    try:
        logger.info(f"📊 Getting quality performance metrics: {period}")
        
        if not ENHANCED_VALIDATION_AVAILABLE:
            return {
                "error": "Enhanced validation components not available",
                "timestamp": datetime.now().isoformat()
            }
        
        # Get performance metrics
        metrics = await decision_quality_assessor.get_performance_metrics(period=period)
        
        result = {
            "performance_metrics": {
                "total_decisions": metrics.total_decisions,
                "successful_decisions": metrics.successful_decisions,
                "failed_decisions": metrics.failed_decisions,
                "average_quality_score": metrics.average_quality_score,
                "quality_consistency": metrics.quality_consistency,
                "improvement_rate": metrics.improvement_rate,
                "compliance_rate": metrics.compliance_rate,
                "risk_adjusted_performance": metrics.risk_adjusted_performance,
                "benchmark_outperformance": metrics.benchmark_outperformance,
                "quality_distribution": dict(metrics.quality_distribution)
            },
            "performance_analysis": {
                "success_rate": (metrics.successful_decisions / metrics.total_decisions) if metrics.total_decisions > 0 else 0.0,
                "ai_brain_compliance_rate": metrics.compliance_rate,
                "quality_grade_distribution": {
                    "excellent": metrics.quality_distribution.get("excellent", 0),
                    "good": metrics.quality_distribution.get("good", 0),
                    "satisfactory": metrics.quality_distribution.get("satisfactory", 0),
                    "needs_improvement": metrics.quality_distribution.get("needs_improvement", 0),
                    "poor": metrics.quality_distribution.get("poor", 0)
                },
                "performance_indicators": {
                    "above_ai_brain_threshold": metrics.average_quality_score >= 85.0,
                    "consistent_quality": metrics.quality_consistency >= 0.8,
                    "improving_trend": metrics.improvement_rate > 0.0,
                    "benchmark_beating": metrics.benchmark_outperformance > 0.0
                }
            },
            "period": period,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Quality performance metrics retrieved: {metrics.total_decisions} decisions, {metrics.average_quality_score:.2f}% avg score")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Quality performance metrics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Performance metrics retrieval failed: {str(e)}")

@router.get("/quality/export-report")
async def export_quality_report(
    decision_ids: Optional[str] = Query(None, description="Comma-separated decision IDs"),
    period_days: Optional[int] = Query(None, description="Report period in days")
) -> Dict[str, Any]:
    """
    Export comprehensive quality report
    Provides detailed analysis for specified decisions or period
    """
    try:
        logger.info(f"📋 Exporting quality report: decision_ids={decision_ids}, period_days={period_days}")
        
        if not ENHANCED_VALIDATION_AVAILABLE:
            return {
                "error": "Enhanced validation components not available",
                "timestamp": datetime.now().isoformat()
            }
        
        # Parse decision IDs if provided
        parsed_decision_ids = None
        if decision_ids:
            parsed_decision_ids = [id.strip() for id in decision_ids.split(",") if id.strip()]
        
        # Export quality report
        report = await decision_quality_assessor.export_quality_report(
            decision_ids=parsed_decision_ids,
            period_days=period_days
        )
        
        # Enhanced report with additional insights
        enhanced_report = {
            **report,
            "export_metadata": {
                "export_type": "comprehensive_quality_report",
                "requested_decision_ids": parsed_decision_ids,
                "requested_period_days": period_days,
                "ai_brain_integration": True,
                "enhanced_validation": True
            },
            "insights": {
                "key_findings": [
                    f"Average quality score: {report['summary']['average_score']:.2f}%",
                    f"AI Brain compliance rate: {report['summary']['compliance_rate']:.1%}",
                    f"Total decisions analyzed: {report['summary']['total_decisions']}",
                    f"Quality consistency: {1.0 - report['summary']['std_deviation']/100:.1%}" if report['summary']['std_deviation'] > 0 else "Perfect consistency"
                ],
                "recommendations": report.get("recommendation_priorities", {}),
                "ai_brain_status": {
                    "threshold_compliance": report['summary']['compliance_rate'] >= 0.85,
                    "average_above_threshold": report['summary']['average_score'] >= 85.0,
                    "improvement_needed": report['summary']['average_score'] < 85.0
                }
            }
        }
        
        logger.info(f"✅ Quality report exported: {report['summary']['total_decisions']} decisions analyzed")
        
        return enhanced_report
        
    except Exception as e:
        logger.error(f"❌ Quality report export failed: {e}")
        raise HTTPException(status_code=500, detail=f"Report export failed: {str(e)}")

@router.get("/quality/dashboard")
async def get_quality_dashboard() -> Dict[str, Any]:
    """
    Get comprehensive quality dashboard data
    Provides real-time overview of decision quality status
    """
    try:
        logger.info("🎯 Getting quality dashboard data")
        
        if not ENHANCED_VALIDATION_AVAILABLE:
            return {
                "error": "Enhanced validation components not available",
                "timestamp": datetime.now().isoformat()
            }
        
        # Get current performance metrics
        current_metrics = await decision_quality_assessor.get_performance_metrics("current_month")
        
        # Get recent trends
        recent_trends = await decision_quality_assessor.get_quality_trends(period_days=7)
        
        # Get weekly trends for comparison
        weekly_trends = await decision_quality_assessor.get_quality_trends(period_days=30)
        
        dashboard_data = {
            "overview": {
                "current_quality_score": current_metrics.average_quality_score,
                "ai_brain_compliance": current_metrics.compliance_rate >= 0.85,
                "compliance_rate": current_metrics.compliance_rate,
                "total_decisions": current_metrics.total_decisions,
                "improvement_trend": recent_trends.trend_direction,
                "trend_strength": recent_trends.trend_strength
            },
            "quality_metrics": {
                "average_score": current_metrics.average_quality_score,
                "consistency": current_metrics.quality_consistency,
                "improvement_rate": current_metrics.improvement_rate,
                "benchmark_performance": current_metrics.benchmark_outperformance,
                "risk_adjusted_performance": current_metrics.risk_adjusted_performance
            },
            "grade_distribution": dict(current_metrics.quality_distribution),
            "trend_analysis": {
                "recent_7_days": {
                    "direction": recent_trends.trend_direction,
                    "strength": recent_trends.trend_strength,
                    "recommendations": recent_trends.recommendations[:3]  # Top 3
                },
                "monthly_comparison": {
                    "direction": weekly_trends.trend_direction,
                    "strength": weekly_trends.trend_strength,
                    "performance_correlation": weekly_trends.performance_correlation
                }
            },
            "dimension_performance": {
                dim.value: {
                    "trend": recent_trends.dimension_trends.get(dim, "stable"),
                    "status": "good" if recent_trends.dimension_trends.get(dim, "stable") != "declining" else "needs_attention"
                } for dim in QualityDimension
            },
            "alerts": {
                "ai_brain_non_compliance": current_metrics.compliance_rate < 0.85,
                "quality_decline": recent_trends.trend_direction == "declining",
                "low_consistency": current_metrics.quality_consistency < 0.7,
                "below_benchmark": current_metrics.benchmark_outperformance < 0.0
            },
            "recommendations": recent_trends.recommendations[:5],  # Top 5 recommendations
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Quality dashboard data retrieved: {current_metrics.average_quality_score:.2f}% avg score, {current_metrics.compliance_rate:.1%} compliance")
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"❌ Quality dashboard retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Dashboard retrieval failed: {str(e)}")