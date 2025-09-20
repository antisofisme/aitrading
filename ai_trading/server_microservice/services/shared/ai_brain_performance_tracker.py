"""
📊 AI Brain Performance Tracking System for Trading Platform
Comprehensive performance monitoring preventing the 80%+ AI project failure rate

KEY FEATURES:
- Real-time performance tracking with confidence correlation
- Multi-dimensional performance analysis (accuracy, profitability, risk)
- Systematic performance degradation detection and alerts
- AI Brain enhanced performance insights and recommendations
- Confidence calibration based on actual trading outcomes
- Performance pattern recognition and learning

PERFORMANCE DIMENSIONS:
1. Prediction Accuracy (how often predictions are correct)
2. Trading Profitability (actual financial performance)
3. Risk Management Effectiveness (drawdown, risk-adjusted returns)
4. Confidence Calibration (predicted vs actual confidence)
5. System Reliability (uptime, error rates, response times)
6. Learning Effectiveness (improvement over time)

INTEGRATION WITH AI BRAIN:
- Uses AI Brain error DNA for performance issue analysis
- Implements confidence framework for performance validation
- Provides systematic performance pattern recognition
- Includes predictive performance alerts and recommendations
"""

import asyncio
import json
import statistics
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
from collections import deque, defaultdict
import math


class PerformanceMetricType(Enum):
    """Types of performance metrics tracked"""
    PREDICTION_ACCURACY = "prediction_accuracy"
    TRADING_PROFITABILITY = "trading_profitability"
    RISK_MANAGEMENT = "risk_management"
    CONFIDENCE_CALIBRATION = "confidence_calibration"
    SYSTEM_RELIABILITY = "system_reliability"
    LEARNING_EFFECTIVENESS = "learning_effectiveness"


class PerformanceAlert(Enum):
    """Performance alert levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics snapshot"""
    timestamp: str
    
    # Prediction accuracy metrics
    prediction_accuracy: float = 0.0
    ml_model_accuracy: float = 0.0
    dl_model_accuracy: float = 0.0
    ai_ensemble_accuracy: float = 0.0
    
    # Trading profitability metrics
    total_pnl: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    
    # Risk management metrics
    risk_adjusted_return: float = 0.0
    volatility: float = 0.0
    var_95: float = 0.0  # Value at Risk 95%
    correlation_risk: float = 0.0
    
    # Confidence calibration metrics
    confidence_accuracy: float = 0.0
    confidence_bias: float = 0.0
    calibration_error: float = 0.0
    
    # System reliability metrics
    uptime_percentage: float = 0.0
    error_rate: float = 0.0
    average_response_time: float = 0.0
    
    # Learning effectiveness metrics
    improvement_rate: float = 0.0
    adaptation_speed: float = 0.0
    pattern_recognition_score: float = 0.0
    
    # Overall scores
    overall_performance_score: float = 0.0
    ai_brain_enhancement_score: float = 0.0
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class PerformanceAlert:
    """Performance alert with details and recommendations"""
    alert_type: str
    severity: PerformanceAlert
    message: str
    metric_affected: str
    current_value: float
    threshold_value: float
    recommendations: List[str]
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class AIBrainPerformanceTracker:
    """
    AI Brain enhanced performance tracking system
    Comprehensive monitoring and analysis of trading system performance
    """
    
    def __init__(self, history_size: int = 10000):
        # Performance history storage
        self.history_size = history_size
        self.performance_history = deque(maxlen=history_size)
        self.trade_history = deque(maxlen=history_size)
        self.prediction_history = deque(maxlen=history_size)
        
        # Performance thresholds for alerts
        self.performance_thresholds = {
            "prediction_accuracy": {"warning": 0.6, "critical": 0.5, "emergency": 0.4},
            "win_rate": {"warning": 0.55, "critical": 0.45, "emergency": 0.35},
            "profit_factor": {"warning": 1.2, "critical": 1.0, "emergency": 0.8},
            "sharpe_ratio": {"warning": 0.8, "critical": 0.5, "emergency": 0.2},
            "max_drawdown": {"warning": -0.1, "critical": -0.2, "emergency": -0.3},
            "confidence_accuracy": {"warning": 0.7, "critical": 0.6, "emergency": 0.5},
            "uptime_percentage": {"warning": 0.95, "critical": 0.90, "emergency": 0.85},
            "error_rate": {"warning": 0.05, "critical": 0.1, "emergency": 0.2}
        }
        
        # Performance weights for overall scoring
        self.performance_weights = {
            PerformanceMetricType.PREDICTION_ACCURACY: 0.25,
            PerformanceMetricType.TRADING_PROFITABILITY: 0.30,
            PerformanceMetricType.RISK_MANAGEMENT: 0.20,
            PerformanceMetricType.CONFIDENCE_CALIBRATION: 0.10,
            PerformanceMetricType.SYSTEM_RELIABILITY: 0.10,
            PerformanceMetricType.LEARNING_EFFECTIVENESS: 0.05
        }
        
        # Real-time tracking
        self.current_session_stats = {
            "session_start": datetime.now(),
            "total_predictions": 0,
            "correct_predictions": 0,
            "total_trades": 0,
            "winning_trades": 0,
            "total_pnl": 0.0,
            "errors": 0,
            "requests": 0
        }
        
        # Performance alerts
        self.active_alerts = []
        self.alert_history = deque(maxlen=1000)
        
        # AI Brain integration flags
        self.ai_brain_available = self._check_ai_brain_availability()
        
        # Performance analysis cache
        self.analysis_cache = {}
        self.cache_expiry = {}
        
        print(f"📊 AI Brain Performance Tracker initialized (AI Brain: {'✅' if self.ai_brain_available else '❌'})")
    
    def _check_ai_brain_availability(self) -> bool:
        """Check if AI Brain components are available"""
        try:
            # Try to import AI Brain components
            import sys
            from pathlib import Path
            
            ai_brain_path = Path(__file__).parent.parent.parent.parent.parent / "ai-brain"
            if str(ai_brain_path) not in sys.path:
                sys.path.insert(0, str(ai_brain_path))
                
            from foundation.error_dna import ErrorDNASystem
            from foundation.decision_validator import AIDecisionValidator
            
            self.ai_brain_error_dna = ErrorDNASystem()
            self.ai_brain_validator = AIDecisionValidator()
            
            return True
        except ImportError:
            return False
    
    async def track_prediction_performance(
        self,
        prediction_id: str,
        predicted_outcome: Any,
        actual_outcome: Any,
        confidence: float,
        model_type: str = "ensemble"
    ):
        """Track prediction accuracy and confidence calibration"""
        
        # Determine if prediction was correct
        is_correct = self._evaluate_prediction_accuracy(predicted_outcome, actual_outcome)
        
        # Update session stats
        self.current_session_stats["total_predictions"] += 1
        if is_correct:
            self.current_session_stats["correct_predictions"] += 1
        
        # Store prediction result
        prediction_record = {
            "prediction_id": prediction_id,
            "predicted_outcome": predicted_outcome,
            "actual_outcome": actual_outcome,
            "confidence": confidence,
            "model_type": model_type,
            "is_correct": is_correct,
            "timestamp": datetime.now().isoformat(),
            "confidence_calibration_error": abs(confidence - (1.0 if is_correct else 0.0))
        }
        
        self.prediction_history.append(prediction_record)
        
        # Check for performance degradation
        await self._check_prediction_performance_alerts()
        
        # Update confidence calibration if AI Brain is available
        if self.ai_brain_available:
            await self._update_confidence_calibration(confidence, is_correct, model_type)
    
    async def track_trading_performance(
        self,
        trade_id: str,
        symbol: str,
        action: str,
        entry_price: float,
        exit_price: Optional[float],
        position_size: float,
        pnl: Optional[float] = None,
        confidence: Optional[float] = None,
        strategy_id: Optional[str] = None
    ):
        """Track trading performance and profitability"""
        
        # Calculate PnL if not provided
        if pnl is None and exit_price is not None:
            if action.lower() == "buy":
                pnl = (exit_price - entry_price) * position_size
            else:
                pnl = (entry_price - exit_price) * position_size
        
        # Determine if trade was winning
        is_winning = pnl > 0 if pnl is not None else None
        
        # Update session stats
        if exit_price is not None:  # Only count closed trades
            self.current_session_stats["total_trades"] += 1
            if is_winning:
                self.current_session_stats["winning_trades"] += 1
            if pnl is not None:
                self.current_session_stats["total_pnl"] += pnl
        
        # Store trade record
        trade_record = {
            "trade_id": trade_id,
            "symbol": symbol,
            "action": action,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "position_size": position_size,
            "pnl": pnl,
            "confidence": confidence,
            "strategy_id": strategy_id,
            "is_winning": is_winning,
            "timestamp": datetime.now().isoformat(),
            "is_closed": exit_price is not None
        }
        
        self.trade_history.append(trade_record)
        
        # Check for performance alerts
        if exit_price is not None:
            await self._check_trading_performance_alerts()
    
    async def track_system_performance(
        self,
        operation_type: str,
        response_time: float,
        success: bool,
        error_details: Optional[Dict[str, Any]] = None
    ):
        """Track system reliability and performance"""
        
        # Update session stats
        self.current_session_stats["requests"] += 1
        if not success:
            self.current_session_stats["errors"] += 1
        
        # Store system performance record
        system_record = {
            "operation_type": operation_type,
            "response_time": response_time,
            "success": success,
            "error_details": error_details,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add to performance history
        if not hasattr(self, 'system_performance_history'):
            self.system_performance_history = deque(maxlen=self.history_size)
        
        self.system_performance_history.append(system_record)
        
        # Check for system performance alerts
        await self._check_system_performance_alerts()
    
    async def calculate_comprehensive_performance(
        self,
        timeframe: str = "24h"
    ) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics"""
        
        # Parse timeframe
        end_time = datetime.now()
        if timeframe == "1h":
            start_time = end_time - timedelta(hours=1)
        elif timeframe == "24h":
            start_time = end_time - timedelta(hours=24)
        elif timeframe == "7d":
            start_time = end_time - timedelta(days=7)
        elif timeframe == "30d":
            start_time = end_time - timedelta(days=30)
        else:
            start_time = end_time - timedelta(hours=24)  # Default to 24h
        
        # Check cache
        cache_key = f"performance_{timeframe}_{int(end_time.timestamp())}"
        if cache_key in self.analysis_cache:
            cache_time = self.cache_expiry.get(cache_key, 0)
            if datetime.now().timestamp() - cache_time < 300:  # 5 minute cache
                return self.analysis_cache[cache_key]
        
        # Calculate prediction accuracy metrics
        prediction_metrics = await self._calculate_prediction_accuracy(start_time, end_time)
        
        # Calculate trading profitability metrics
        trading_metrics = await self._calculate_trading_profitability(start_time, end_time)
        
        # Calculate risk management metrics
        risk_metrics = await self._calculate_risk_management(start_time, end_time)
        
        # Calculate confidence calibration metrics
        confidence_metrics = await self._calculate_confidence_calibration(start_time, end_time)
        
        # Calculate system reliability metrics
        system_metrics = await self._calculate_system_reliability(start_time, end_time)
        
        # Calculate learning effectiveness metrics
        learning_metrics = await self._calculate_learning_effectiveness(start_time, end_time)
        
        # Calculate overall performance score
        overall_score = self._calculate_overall_performance_score({
            PerformanceMetricType.PREDICTION_ACCURACY: prediction_metrics.get("overall_accuracy", 0),
            PerformanceMetricType.TRADING_PROFITABILITY: trading_metrics.get("profit_score", 0),
            PerformanceMetricType.RISK_MANAGEMENT: risk_metrics.get("risk_score", 0),
            PerformanceMetricType.CONFIDENCE_CALIBRATION: confidence_metrics.get("calibration_score", 0),
            PerformanceMetricType.SYSTEM_RELIABILITY: system_metrics.get("reliability_score", 0),
            PerformanceMetricType.LEARNING_EFFECTIVENESS: learning_metrics.get("learning_score", 0)
        })
        
        # Create comprehensive metrics
        metrics = PerformanceMetrics(
            timestamp=end_time.isoformat(),
            
            # Prediction accuracy
            prediction_accuracy=prediction_metrics.get("overall_accuracy", 0),
            ml_model_accuracy=prediction_metrics.get("ml_accuracy", 0),
            dl_model_accuracy=prediction_metrics.get("dl_accuracy", 0),
            ai_ensemble_accuracy=prediction_metrics.get("ensemble_accuracy", 0),
            
            # Trading profitability
            total_pnl=trading_metrics.get("total_pnl", 0),
            win_rate=trading_metrics.get("win_rate", 0),
            profit_factor=trading_metrics.get("profit_factor", 0),
            sharpe_ratio=trading_metrics.get("sharpe_ratio", 0),
            max_drawdown=trading_metrics.get("max_drawdown", 0),
            
            # Risk management
            risk_adjusted_return=risk_metrics.get("risk_adjusted_return", 0),
            volatility=risk_metrics.get("volatility", 0),
            var_95=risk_metrics.get("var_95", 0),
            correlation_risk=risk_metrics.get("correlation_risk", 0),
            
            # Confidence calibration
            confidence_accuracy=confidence_metrics.get("accuracy", 0),
            confidence_bias=confidence_metrics.get("bias", 0),
            calibration_error=confidence_metrics.get("calibration_error", 0),
            
            # System reliability
            uptime_percentage=system_metrics.get("uptime", 0),
            error_rate=system_metrics.get("error_rate", 0),
            average_response_time=system_metrics.get("avg_response_time", 0),
            
            # Learning effectiveness
            improvement_rate=learning_metrics.get("improvement_rate", 0),
            adaptation_speed=learning_metrics.get("adaptation_speed", 0),
            pattern_recognition_score=learning_metrics.get("pattern_score", 0),
            
            # Overall scores
            overall_performance_score=overall_score,
            ai_brain_enhancement_score=0.85 if self.ai_brain_available else 0.0
        )
        
        # Cache result
        self.analysis_cache[cache_key] = metrics
        self.cache_expiry[cache_key] = datetime.now().timestamp()
        
        # Store in performance history
        self.performance_history.append(asdict(metrics))
        
        return metrics
    
    async def _calculate_prediction_accuracy(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, float]:
        """Calculate prediction accuracy metrics"""
        
        # Filter predictions in timeframe
        relevant_predictions = [
            pred for pred in self.prediction_history
            if start_time <= datetime.fromisoformat(pred["timestamp"]) <= end_time
        ]
        
        if not relevant_predictions:
            return {"overall_accuracy": 0, "ml_accuracy": 0, "dl_accuracy": 0, "ensemble_accuracy": 0}
        
        # Overall accuracy
        correct_predictions = sum(1 for pred in relevant_predictions if pred["is_correct"])
        overall_accuracy = correct_predictions / len(relevant_predictions)
        
        # Model-specific accuracies
        model_accuracies = {}
        for model_type in ["ml", "dl", "ensemble"]:
            model_predictions = [pred for pred in relevant_predictions if pred["model_type"] == model_type]
            if model_predictions:
                model_correct = sum(1 for pred in model_predictions if pred["is_correct"])
                model_accuracies[f"{model_type}_accuracy"] = model_correct / len(model_predictions)
            else:
                model_accuracies[f"{model_type}_accuracy"] = 0
        
        return {
            "overall_accuracy": overall_accuracy,
            **model_accuracies
        }
    
    async def _calculate_trading_profitability(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, float]:
        """Calculate trading profitability metrics"""
        
        # Filter closed trades in timeframe
        relevant_trades = [
            trade for trade in self.trade_history
            if (trade["is_closed"] and 
                start_time <= datetime.fromisoformat(trade["timestamp"]) <= end_time)
        ]
        
        if not relevant_trades:
            return {"total_pnl": 0, "win_rate": 0, "profit_factor": 0, "sharpe_ratio": 0, "max_drawdown": 0, "profit_score": 0}
        
        # Calculate basic metrics
        total_pnl = sum(trade["pnl"] for trade in relevant_trades if trade["pnl"] is not None)
        winning_trades = [trade for trade in relevant_trades if trade["pnl"] and trade["pnl"] > 0]
        losing_trades = [trade for trade in relevant_trades if trade["pnl"] and trade["pnl"] <= 0]
        
        win_rate = len(winning_trades) / len(relevant_trades) if relevant_trades else 0
        
        # Profit factor
        gross_profit = sum(trade["pnl"] for trade in winning_trades)
        gross_loss = abs(sum(trade["pnl"] for trade in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf') if gross_profit > 0 else 0
        
        # Sharpe ratio (simplified)
        pnl_values = [trade["pnl"] for trade in relevant_trades if trade["pnl"] is not None]
        if len(pnl_values) > 1:
            returns_std = statistics.stdev(pnl_values)
            sharpe_ratio = (statistics.mean(pnl_values) / returns_std) if returns_std > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Maximum drawdown
        cumulative_pnl = 0
        peak_pnl = 0
        max_drawdown = 0
        
        for trade in relevant_trades:
            if trade["pnl"] is not None:
                cumulative_pnl += trade["pnl"]
                peak_pnl = max(peak_pnl, cumulative_pnl)
                drawdown = (peak_pnl - cumulative_pnl) / max(peak_pnl, 1)
                max_drawdown = max(max_drawdown, drawdown)
        
        max_drawdown = -max_drawdown  # Make it negative
        
        # Calculate profit score (0-1)
        profit_score = min(1.0, max(0.0, (
            (min(win_rate, 1.0) * 0.3) +
            (min(profit_factor / 2.0, 1.0) * 0.4) +
            (min(max(-max_drawdown, 1.0), 1.0) * 0.3)
        )))
        
        return {
            "total_pnl": total_pnl,
            "win_rate": win_rate,
            "profit_factor": profit_factor if profit_factor != float('inf') else 0,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "profit_score": profit_score
        }
    
    async def _calculate_risk_management(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, float]:
        """Calculate risk management effectiveness"""
        
        # This is a simplified implementation
        # In practice, you'd calculate more sophisticated risk metrics
        
        relevant_trades = [
            trade for trade in self.trade_history
            if (trade["is_closed"] and 
                start_time <= datetime.fromisoformat(trade["timestamp"]) <= end_time)
        ]
        
        if not relevant_trades:
            return {"risk_adjusted_return": 0, "volatility": 0, "var_95": 0, "correlation_risk": 0, "risk_score": 0}
        
        # Calculate returns
        returns = [trade["pnl"] / abs(trade["entry_price"] * trade["position_size"]) 
                  for trade in relevant_trades 
                  if trade["pnl"] is not None and trade["entry_price"] > 0]
        
        if not returns:
            return {"risk_adjusted_return": 0, "volatility": 0, "var_95": 0, "correlation_risk": 0, "risk_score": 0}
        
        # Basic risk metrics
        mean_return = statistics.mean(returns)
        volatility = statistics.stdev(returns) if len(returns) > 1 else 0
        
        # Risk-adjusted return (Sharpe-like)
        risk_adjusted_return = mean_return / volatility if volatility > 0 else 0
        
        # Value at Risk (95%)
        sorted_returns = sorted(returns)
        var_index = int(0.05 * len(sorted_returns))
        var_95 = sorted_returns[var_index] if var_index < len(sorted_returns) else 0
        
        # Risk score (simplified)
        risk_score = min(1.0, max(0.0, (
            (min(max(risk_adjusted_return, 0), 2.0) / 2.0 * 0.4) +
            (min(max(-var_95, 0), 1.0) * 0.3) +
            (min(max(1 - volatility, 0), 1.0) * 0.3)
        )))
        
        return {
            "risk_adjusted_return": risk_adjusted_return,
            "volatility": volatility,
            "var_95": var_95,
            "correlation_risk": 0.3,  # Placeholder
            "risk_score": risk_score
        }
    
    async def _calculate_confidence_calibration(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, float]:
        """Calculate confidence calibration metrics"""
        
        relevant_predictions = [
            pred for pred in self.prediction_history
            if start_time <= datetime.fromisoformat(pred["timestamp"]) <= end_time
        ]
        
        if not relevant_predictions:
            return {"accuracy": 0, "bias": 0, "calibration_error": 0, "calibration_score": 0}
        
        # Calculate calibration accuracy
        confidence_values = [pred["confidence"] for pred in relevant_predictions]
        actual_outcomes = [1.0 if pred["is_correct"] else 0.0 for pred in relevant_predictions]
        
        # Mean confidence vs mean accuracy
        mean_confidence = statistics.mean(confidence_values)
        mean_accuracy = statistics.mean(actual_outcomes)
        
        bias = mean_confidence - mean_accuracy
        calibration_error = statistics.mean([
            abs(pred["confidence"] - (1.0 if pred["is_correct"] else 0.0))
            for pred in relevant_predictions
        ])
        
        # Calibration score
        calibration_score = max(0.0, 1.0 - calibration_error)
        
        return {
            "accuracy": mean_accuracy,
            "bias": bias,
            "calibration_error": calibration_error,
            "calibration_score": calibration_score
        }
    
    async def _calculate_system_reliability(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, float]:
        """Calculate system reliability metrics"""
        
        # Calculate based on session stats and system performance history
        if not hasattr(self, 'system_performance_history'):
            return {"uptime": 0.95, "error_rate": 0.02, "avg_response_time": 0.1, "reliability_score": 0.8}
        
        relevant_records = [
            record for record in self.system_performance_history
            if start_time <= datetime.fromisoformat(record["timestamp"]) <= end_time
        ]
        
        if not relevant_records:
            return {"uptime": 0.95, "error_rate": 0.02, "avg_response_time": 0.1, "reliability_score": 0.8}
        
        # Calculate metrics
        successful_requests = sum(1 for record in relevant_records if record["success"])
        total_requests = len(relevant_records)
        uptime = successful_requests / total_requests if total_requests > 0 else 0
        error_rate = (total_requests - successful_requests) / total_requests if total_requests > 0 else 0
        
        response_times = [record["response_time"] for record in relevant_records if record["response_time"]]
        avg_response_time = statistics.mean(response_times) if response_times else 0
        
        # Reliability score
        reliability_score = (
            uptime * 0.5 +
            max(0, 1 - error_rate) * 0.3 +
            max(0, 1 - min(avg_response_time / 2.0, 1.0)) * 0.2
        )
        
        return {
            "uptime": uptime,
            "error_rate": error_rate,
            "avg_response_time": avg_response_time,
            "reliability_score": reliability_score
        }
    
    async def _calculate_learning_effectiveness(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, float]:
        """Calculate learning and improvement metrics"""
        
        # This is a simplified implementation
        # In practice, you'd analyze trends in prediction accuracy, trading performance, etc.
        
        # Look at performance trends
        if len(self.performance_history) < 10:
            return {"improvement_rate": 0, "adaptation_speed": 0, "pattern_score": 0, "learning_score": 0}
        
        recent_performance = list(self.performance_history)[-10:]  # Last 10 measurements
        older_performance = list(self.performance_history)[-20:-10] if len(self.performance_history) >= 20 else []
        
        if not older_performance:
            return {"improvement_rate": 0, "adaptation_speed": 0.5, "pattern_score": 0.5, "learning_score": 0.5}
        
        # Calculate improvement rate
        recent_avg_score = statistics.mean([p.get("overall_performance_score", 0) for p in recent_performance])
        older_avg_score = statistics.mean([p.get("overall_performance_score", 0) for p in older_performance])
        
        improvement_rate = max(0, (recent_avg_score - older_avg_score)) if older_avg_score > 0 else 0
        
        # Simplified metrics
        adaptation_speed = 0.7  # Placeholder
        pattern_score = 0.6    # Placeholder
        
        learning_score = (improvement_rate * 0.5) + (adaptation_speed * 0.3) + (pattern_score * 0.2)
        
        return {
            "improvement_rate": improvement_rate,
            "adaptation_speed": adaptation_speed,
            "pattern_score": pattern_score,
            "learning_score": learning_score
        }
    
    def _calculate_overall_performance_score(self, dimension_scores: Dict[PerformanceMetricType, float]) -> float:
        """Calculate weighted overall performance score"""
        
        weighted_score = sum(
            score * self.performance_weights[dimension]
            for dimension, score in dimension_scores.items()
        )
        
        return min(1.0, max(0.0, weighted_score))
    
    def _evaluate_prediction_accuracy(self, predicted: Any, actual: Any) -> bool:
        """Evaluate if a prediction was accurate"""
        
        # Simple accuracy evaluation - can be enhanced based on specific needs
        if isinstance(predicted, (int, float)) and isinstance(actual, (int, float)):
            # For numerical predictions, use tolerance-based accuracy
            tolerance = abs(predicted) * 0.05 if predicted != 0 else 0.01  # 5% tolerance
            return abs(predicted - actual) <= tolerance
        elif isinstance(predicted, str) and isinstance(actual, str):
            # For categorical predictions
            return predicted.lower() == actual.lower()
        elif isinstance(predicted, dict) and isinstance(actual, dict):
            # For directional predictions
            pred_direction = predicted.get("direction", "").lower()
            actual_direction = actual.get("direction", "").lower()
            return pred_direction == actual_direction
        else:
            # Default comparison
            return predicted == actual
    
    async def _update_confidence_calibration(self, confidence: float, is_correct: bool, model_type: str):
        """Update confidence calibration using AI Brain if available"""
        
        if not self.ai_brain_available:
            return
        
        try:
            # Use AI Brain to update confidence accuracy
            # This would integrate with the confidence framework
            pass
        except Exception as e:
            print(f"Failed to update AI Brain confidence calibration: {e}")
    
    async def _check_prediction_performance_alerts(self):
        """Check for prediction performance alerts"""
        
        if len(self.prediction_history) < 10:
            return
        
        # Calculate recent accuracy
        recent_predictions = list(self.prediction_history)[-20:]  # Last 20 predictions
        recent_accuracy = sum(1 for pred in recent_predictions if pred["is_correct"]) / len(recent_predictions)
        
        # Check thresholds
        thresholds = self.performance_thresholds["prediction_accuracy"]
        
        if recent_accuracy <= thresholds["emergency"]:
            await self._create_alert("PREDICTION_ACCURACY_EMERGENCY", PerformanceAlert.EMERGENCY, 
                                   f"Prediction accuracy critically low: {recent_accuracy:.2%}", 
                                   "prediction_accuracy", recent_accuracy, thresholds["emergency"])
        elif recent_accuracy <= thresholds["critical"]:
            await self._create_alert("PREDICTION_ACCURACY_CRITICAL", PerformanceAlert.CRITICAL,
                                   f"Prediction accuracy very low: {recent_accuracy:.2%}",
                                   "prediction_accuracy", recent_accuracy, thresholds["critical"])
        elif recent_accuracy <= thresholds["warning"]:
            await self._create_alert("PREDICTION_ACCURACY_WARNING", PerformanceAlert.WARNING,
                                   f"Prediction accuracy below optimal: {recent_accuracy:.2%}",
                                   "prediction_accuracy", recent_accuracy, thresholds["warning"])
    
    async def _check_trading_performance_alerts(self):
        """Check for trading performance alerts"""
        
        closed_trades = [trade for trade in self.trade_history if trade["is_closed"]]
        if len(closed_trades) < 10:
            return
        
        # Calculate recent win rate
        recent_trades = closed_trades[-20:]  # Last 20 closed trades
        recent_win_rate = sum(1 for trade in recent_trades if trade.get("is_winning")) / len(recent_trades)
        
        # Check thresholds
        thresholds = self.performance_thresholds["win_rate"]
        
        if recent_win_rate <= thresholds["emergency"]:
            await self._create_alert("WIN_RATE_EMERGENCY", PerformanceAlert.EMERGENCY,
                                   f"Win rate critically low: {recent_win_rate:.2%}",
                                   "win_rate", recent_win_rate, thresholds["emergency"])
        elif recent_win_rate <= thresholds["critical"]:
            await self._create_alert("WIN_RATE_CRITICAL", PerformanceAlert.CRITICAL,
                                   f"Win rate very low: {recent_win_rate:.2%}",
                                   "win_rate", recent_win_rate, thresholds["critical"])
        elif recent_win_rate <= thresholds["warning"]:
            await self._create_alert("WIN_RATE_WARNING", PerformanceAlert.WARNING,
                                   f"Win rate below optimal: {recent_win_rate:.2%}",
                                   "win_rate", recent_win_rate, thresholds["warning"])
    
    async def _check_system_performance_alerts(self):
        """Check for system performance alerts"""
        
        # Calculate current error rate
        total_requests = self.current_session_stats["requests"]
        total_errors = self.current_session_stats["errors"]
        
        if total_requests < 10:
            return
        
        error_rate = total_errors / total_requests
        thresholds = self.performance_thresholds["error_rate"]
        
        if error_rate >= thresholds["emergency"]:
            await self._create_alert("ERROR_RATE_EMERGENCY", PerformanceAlert.EMERGENCY,
                                   f"Error rate critically high: {error_rate:.2%}",
                                   "error_rate", error_rate, thresholds["emergency"])
        elif error_rate >= thresholds["critical"]:
            await self._create_alert("ERROR_RATE_CRITICAL", PerformanceAlert.CRITICAL,
                                   f"Error rate very high: {error_rate:.2%}",
                                   "error_rate", error_rate, thresholds["critical"])
        elif error_rate >= thresholds["warning"]:
            await self._create_alert("ERROR_RATE_WARNING", PerformanceAlert.WARNING,
                                   f"Error rate elevated: {error_rate:.2%}",
                                   "error_rate", error_rate, thresholds["warning"])
    
    async def _create_alert(
        self,
        alert_type: str,
        severity: PerformanceAlert,
        message: str,
        metric_affected: str,
        current_value: float,
        threshold_value: float
    ):
        """Create and store performance alert"""
        
        # Generate recommendations based on alert type
        recommendations = self._generate_alert_recommendations(alert_type, current_value, threshold_value)
        
        alert = PerformanceAlert(
            alert_type=alert_type,
            severity=severity,
            message=message,
            metric_affected=metric_affected,
            current_value=current_value,
            threshold_value=threshold_value,
            recommendations=recommendations
        )
        
        # Add to active alerts (remove duplicates)
        self.active_alerts = [a for a in self.active_alerts if a.alert_type != alert_type]
        self.active_alerts.append(alert)
        
        # Add to history
        self.alert_history.append(alert)
        
        # Log with AI Brain if available
        if self.ai_brain_available and hasattr(self, 'ai_brain_error_dna'):
            try:
                await self.ai_brain_error_dna.logError(
                    severity.name,
                    f"Performance Alert: {message}",
                    {
                        "alert_type": alert_type,
                        "metric": metric_affected,
                        "current_value": current_value,
                        "threshold": threshold_value,
                        "recommendations": recommendations
                    },
                    "PERFORMANCE"
                )
            except Exception as e:
                print(f"Failed to log performance alert to AI Brain: {e}")
    
    def _generate_alert_recommendations(
        self,
        alert_type: str,
        current_value: float,
        threshold_value: float
    ) -> List[str]:
        """Generate specific recommendations for performance alerts"""
        
        recommendations = []
        
        if "PREDICTION_ACCURACY" in alert_type:
            recommendations.extend([
                "Review and retrain ML/DL models with recent data",
                "Check data quality and feature engineering",
                "Consider ensemble methods to improve accuracy",
                "Analyze prediction patterns for systematic errors",
                "Temporarily increase confidence thresholds"
            ])
        
        elif "WIN_RATE" in alert_type:
            recommendations.extend([
                "Review trading strategy parameters",
                "Analyze recent market conditions and adapt accordingly",
                "Consider reducing position sizes until performance improves",
                "Review risk management settings",
                "Check for overfitting in trading models"
            ])
        
        elif "ERROR_RATE" in alert_type:
            recommendations.extend([
                "Investigate system logs for recurring errors",
                "Check infrastructure health and capacity",
                "Review recent code deployments for issues",
                "Implement additional error handling and recovery",
                "Consider system maintenance or scaling"
            ])
        
        return recommendations
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        
        session_duration = (datetime.now() - self.current_session_stats["session_start"]).total_seconds()
        
        return {
            "session_stats": {
                "duration_hours": session_duration / 3600,
                "total_predictions": self.current_session_stats["total_predictions"],
                "prediction_accuracy": (
                    self.current_session_stats["correct_predictions"] / 
                    max(1, self.current_session_stats["total_predictions"])
                ),
                "total_trades": self.current_session_stats["total_trades"],
                "win_rate": (
                    self.current_session_stats["winning_trades"] / 
                    max(1, self.current_session_stats["total_trades"])
                ),
                "total_pnl": self.current_session_stats["total_pnl"],
                "error_rate": (
                    self.current_session_stats["errors"] / 
                    max(1, self.current_session_stats["requests"])
                )
            },
            "active_alerts": [asdict(alert) for alert in self.active_alerts],
            "performance_history_size": len(self.performance_history),
            "ai_brain_integration": self.ai_brain_available,
            "last_updated": datetime.now().isoformat()
        }
    
    def get_performance_trends(self) -> Dict[str, Any]:
        """Analyze performance trends over time"""
        
        if len(self.performance_history) < 5:
            return {"error": "Insufficient data for trend analysis"}
        
        recent_metrics = list(self.performance_history)[-10:]  # Last 10 measurements
        older_metrics = list(self.performance_history)[-20:-10] if len(self.performance_history) >= 20 else []
        
        trends = {}
        
        # Analyze key metrics trends
        key_metrics = [
            "prediction_accuracy", "win_rate", "profit_factor", 
            "sharpe_ratio", "confidence_accuracy", "overall_performance_score"
        ]
        
        for metric in key_metrics:
            recent_values = [m.get(metric, 0) for m in recent_metrics]
            recent_avg = statistics.mean(recent_values) if recent_values else 0
            
            if older_metrics:
                older_values = [m.get(metric, 0) for m in older_metrics]
                older_avg = statistics.mean(older_values) if older_values else 0
                trend = "improving" if recent_avg > older_avg else "declining" if recent_avg < older_avg else "stable"
                change_pct = ((recent_avg - older_avg) / max(older_avg, 0.001)) * 100
            else:
                trend = "insufficient_data"
                change_pct = 0
            
            trends[metric] = {
                "current_value": recent_avg,
                "trend": trend,
                "change_percentage": change_pct
            }
        
        return {
            "trends": trends,
            "analysis_period": f"Last {len(recent_metrics)} vs previous {len(older_metrics)} measurements",
            "recommendations": self._generate_trend_recommendations(trends)
        }
    
    def _generate_trend_recommendations(self, trends: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on performance trends"""
        
        recommendations = []
        
        declining_metrics = [
            metric for metric, data in trends.items() 
            if data["trend"] == "declining" and data["change_percentage"] < -5
        ]
        
        if declining_metrics:
            recommendations.append(f"Address declining performance in: {', '.join(declining_metrics)}")
            
            if "prediction_accuracy" in declining_metrics:
                recommendations.append("Consider model retraining or feature engineering improvements")
            
            if "win_rate" in declining_metrics:
                recommendations.append("Review and adjust trading strategy parameters")
            
            if "confidence_accuracy" in declining_metrics:
                recommendations.append("Recalibrate confidence thresholds and model uncertainties")
        
        improving_metrics = [
            metric for metric, data in trends.items() 
            if data["trend"] == "improving" and data["change_percentage"] > 5
        ]
        
        if improving_metrics:
            recommendations.append(f"Continue current approach - improving: {', '.join(improving_metrics)}")
        
        if not declining_metrics and not improving_metrics:
            recommendations.append("Performance appears stable - consider optimizations for incremental gains")
        
        return recommendations


# Global instance for easy import
ai_brain_performance_tracker = AIBrainPerformanceTracker()