"""
AI Brain Confidence Framework - Multi-Dimensional Confidence Analysis
5-dimensional confidence scoring with real-time calibration for trading operations
"""

import time
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import statistics

class ConfidenceDimension(Enum):
    """5 core confidence dimensions for trading operations"""
    MODEL_CONFIDENCE = "model_confidence"        # AI/ML model prediction confidence
    DATA_QUALITY = "data_quality"               # Input data reliability
    MARKET_CONFIDENCE = "market_confidence"     # Market condition suitability
    HISTORICAL_CONFIDENCE = "historical_confidence"  # Historical performance correlation
    RISK_CONFIDENCE = "risk_confidence"         # Risk management validation

@dataclass
class ConfidenceScore:
    """Multi-dimensional confidence score"""
    model_confidence: float      # 0.0 to 1.0
    data_quality: float         # 0.0 to 1.0
    market_confidence: float    # 0.0 to 1.0
    historical_confidence: float  # 0.0 to 1.0
    risk_confidence: float      # 0.0 to 1.0
    composite_score: float      # Weighted average
    timestamp: float
    context: Dict[str, Any]

class ConfidenceThreshold(Enum):
    """Confidence threshold levels"""
    CRITICAL = 0.95     # Critical operations require 95%+ confidence
    HIGH = 0.85         # High-risk operations require 85%+ confidence
    MEDIUM = 0.70       # Medium operations require 70%+ confidence
    LOW = 0.55          # Low-risk operations require 55%+ confidence

class AiBrainConfidenceFramework:
    """
    AI Brain Confidence Framework for Trading Operations
    Multi-dimensional confidence analysis with calibration
    """
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.confidence_history: List[ConfidenceScore] = []
        self.calibration_data: Dict[str, Any] = {}
        self.dimension_weights = self._initialize_dimension_weights()
        self.threshold_violations: List[Dict[str, Any]] = []
        
        # Performance tracking
        self.accuracy_tracking: Dict[str, List[float]] = {
            dim.value: [] for dim in ConfidenceDimension
        }
        
    def _initialize_dimension_weights(self) -> Dict[str, float]:
        """Initialize dimension weights for composite scoring"""
        return {
            ConfidenceDimension.MODEL_CONFIDENCE.value: 0.30,
            ConfidenceDimension.DATA_QUALITY.value: 0.25,
            ConfidenceDimension.MARKET_CONFIDENCE.value: 0.20,
            ConfidenceDimension.HISTORICAL_CONFIDENCE.value: 0.15,
            ConfidenceDimension.RISK_CONFIDENCE.value: 0.10
        }
    
    def calculate_confidence(self, 
                           model_prediction: Dict[str, Any],
                           data_inputs: Dict[str, Any],
                           market_context: Dict[str, Any],
                           historical_data: Optional[Dict[str, Any]] = None,
                           risk_parameters: Optional[Dict[str, Any]] = None) -> ConfidenceScore:
        """
        Calculate multi-dimensional confidence score
        
        Args:
            model_prediction: AI/ML model prediction with confidence
            data_inputs: Input data quality metrics
            market_context: Current market conditions
            historical_data: Historical performance data
            risk_parameters: Risk management parameters
            
        Returns:
            Multi-dimensional confidence score
        """
        
        # Calculate individual dimension scores
        model_conf = self._calculate_model_confidence(model_prediction)
        data_conf = self._calculate_data_quality_confidence(data_inputs)
        market_conf = self._calculate_market_confidence(market_context)
        historical_conf = self._calculate_historical_confidence(historical_data or {})
        risk_conf = self._calculate_risk_confidence(risk_parameters or {})
        
        # Calculate weighted composite score
        composite_score = (
            model_conf * self.dimension_weights[ConfidenceDimension.MODEL_CONFIDENCE.value] +
            data_conf * self.dimension_weights[ConfidenceDimension.DATA_QUALITY.value] +
            market_conf * self.dimension_weights[ConfidenceDimension.MARKET_CONFIDENCE.value] +
            historical_conf * self.dimension_weights[ConfidenceDimension.HISTORICAL_CONFIDENCE.value] +
            risk_conf * self.dimension_weights[ConfidenceDimension.RISK_CONFIDENCE.value]
        )
        
        confidence_score = ConfidenceScore(
            model_confidence=model_conf,
            data_quality=data_conf,
            market_confidence=market_conf,
            historical_confidence=historical_conf,
            risk_confidence=risk_conf,
            composite_score=composite_score,
            timestamp=time.time(),
            context={
                "service": self.service_name,
                "prediction": model_prediction,
                "market_context": market_context
            }
        )
        
        # Store for calibration
        self.confidence_history.append(confidence_score)
        
        # Keep only last 1000 scores
        if len(self.confidence_history) > 1000:
            self.confidence_history = self.confidence_history[-1000:]
        
        return confidence_score
    
    def _calculate_model_confidence(self, model_prediction: Dict[str, Any]) -> float:
        """Calculate model confidence dimension"""
        base_confidence = model_prediction.get("confidence", 0.5)
        
        # Adjust based on model type and performance
        model_type = model_prediction.get("model_type", "unknown")
        
        adjustments = {
            "lstm": 0.05,      # LSTM models get slight boost
            "ensemble": 0.10,  # Ensemble models get higher boost
            "transformer": 0.08, # Transformer models get boost
            "traditional_ml": -0.05  # Traditional ML gets slight penalty
        }
        
        adjustment = adjustments.get(model_type, 0.0)
        adjusted_confidence = min(1.0, max(0.0, base_confidence + adjustment))
        
        # Check prediction consistency
        predictions = model_prediction.get("predictions", [])
        if len(predictions) > 1:
            prediction_std = np.std(predictions) if predictions else 0
            if prediction_std > 0.3:  # High variance reduces confidence
                adjusted_confidence *= 0.8
        
        return adjusted_confidence
    
    def _calculate_data_quality_confidence(self, data_inputs: Dict[str, Any]) -> float:
        """Calculate data quality confidence dimension"""
        quality_score = 1.0
        
        # Check for missing data
        missing_ratio = data_inputs.get("missing_ratio", 0.0)
        if missing_ratio > 0.1:
            quality_score *= (1.0 - missing_ratio)
        
        # Check data freshness
        data_age_minutes = data_inputs.get("age_minutes", 0)
        if data_age_minutes > 60:  # Data older than 1 hour
            freshness_penalty = min(0.5, data_age_minutes / 120.0)
            quality_score *= (1.0 - freshness_penalty)
        
        # Check data consistency
        consistency_score = data_inputs.get("consistency_score", 1.0)
        quality_score *= consistency_score
        
        # Check anomaly detection
        anomaly_score = data_inputs.get("anomaly_score", 0.0)
        if anomaly_score > 0.2:
            quality_score *= (1.0 - anomaly_score)
        
        return min(1.0, max(0.0, quality_score))
    
    def _calculate_market_confidence(self, market_context: Dict[str, Any]) -> float:
        """Calculate market confidence dimension"""
        market_score = 0.8  # Base market confidence
        
        # Check market volatility
        volatility = market_context.get("volatility", 0.1)
        if volatility > 0.3:  # High volatility
            market_score *= 0.7
        elif volatility < 0.05:  # Very low volatility
            market_score *= 0.9
        
        # Check market liquidity
        liquidity = market_context.get("liquidity_score", 1.0)
        market_score *= liquidity
        
        # Check trading session
        trading_session = market_context.get("trading_session", "unknown")
        session_multipliers = {
            "london_open": 1.0,
            "new_york_open": 1.0,
            "asian_session": 0.9,
            "weekend": 0.3,
            "low_liquidity": 0.6
        }
        market_score *= session_multipliers.get(trading_session, 0.8)
        
        # Check economic events
        has_major_events = market_context.get("major_events", False)
        if has_major_events:
            market_score *= 0.7
        
        return min(1.0, max(0.0, market_score))
    
    def _calculate_historical_confidence(self, historical_data: Dict[str, Any]) -> float:
        """Calculate historical confidence dimension"""
        if not historical_data:
            return 0.5  # Neutral if no historical data
        
        # Check historical performance
        win_rate = historical_data.get("win_rate", 0.5)
        profit_factor = historical_data.get("profit_factor", 1.0)
        sharpe_ratio = historical_data.get("sharpe_ratio", 0.0)
        
        # Calculate performance-based confidence
        performance_score = (
            min(1.0, win_rate * 1.5) * 0.4 +  # Win rate contribution
            min(1.0, profit_factor / 2.0) * 0.4 +  # Profit factor contribution
            min(1.0, max(0.0, sharpe_ratio) / 2.0) * 0.2  # Sharpe ratio contribution
        )
        
        # Check sample size
        sample_size = historical_data.get("sample_size", 0)
        if sample_size < 100:
            performance_score *= (sample_size / 100.0)
        
        # Check recency of data
        data_age_days = historical_data.get("age_days", 0)
        if data_age_days > 30:
            recency_penalty = min(0.3, data_age_days / 100.0)
            performance_score *= (1.0 - recency_penalty)
        
        return min(1.0, max(0.0, performance_score))
    
    def _calculate_risk_confidence(self, risk_parameters: Dict[str, Any]) -> float:
        """Calculate risk confidence dimension"""
        if not risk_parameters:
            return 0.7  # Neutral if no risk parameters
        
        risk_score = 1.0
        
        # Check position size relative to account
        position_risk = risk_parameters.get("position_risk", 0.02)
        if position_risk > 0.05:  # Risk > 5%
            risk_score *= 0.5
        elif position_risk > 0.03:  # Risk > 3%
            risk_score *= 0.8
        
        # Check stop loss
        has_stop_loss = risk_parameters.get("has_stop_loss", False)
        if not has_stop_loss:
            risk_score *= 0.6
        
        # Check risk-reward ratio
        risk_reward_ratio = risk_parameters.get("risk_reward_ratio", 1.0)
        if risk_reward_ratio < 1.0:
            risk_score *= 0.7
        elif risk_reward_ratio > 2.0:
            risk_score *= 1.1
        
        # Check account utilization
        account_utilization = risk_parameters.get("account_utilization", 0.5)
        if account_utilization > 0.8:
            risk_score *= 0.6
        
        return min(1.0, max(0.0, risk_score))
    
    def validate_threshold(self, confidence_score: ConfidenceScore, 
                          required_threshold: ConfidenceThreshold,
                          operation_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate confidence against required threshold
        
        Returns:
            Validation result with pass/fail and details
        """
        threshold_value = required_threshold.value
        passes_threshold = confidence_score.composite_score >= threshold_value
        
        validation_result = {
            "passes_threshold": passes_threshold,
            "required_threshold": threshold_value,
            "actual_confidence": confidence_score.composite_score,
            "confidence_gap": confidence_score.composite_score - threshold_value,
            "timestamp": time.time(),
            "operation_context": operation_context,
            "dimension_breakdown": {
                "model_confidence": confidence_score.model_confidence,
                "data_quality": confidence_score.data_quality,
                "market_confidence": confidence_score.market_confidence,
                "historical_confidence": confidence_score.historical_confidence,
                "risk_confidence": confidence_score.risk_confidence
            },
            "recommendations": []
        }
        
        # Add recommendations if threshold not met
        if not passes_threshold:
            recommendations = self._generate_threshold_recommendations(confidence_score, threshold_value)
            validation_result["recommendations"] = recommendations
            
            # Log threshold violation
            self.threshold_violations.append(validation_result)
        
        return validation_result
    
    def _generate_threshold_recommendations(self, confidence_score: ConfidenceScore, 
                                          threshold: float) -> List[str]:
        """Generate recommendations for improving confidence"""
        recommendations = []
        
        # Check each dimension
        if confidence_score.model_confidence < 0.7:
            recommendations.append("Improve model confidence through ensemble methods or model retraining")
        
        if confidence_score.data_quality < 0.7:
            recommendations.append("Enhance data quality through better preprocessing and validation")
        
        if confidence_score.market_confidence < 0.7:
            recommendations.append("Wait for better market conditions or adjust strategy parameters")
        
        if confidence_score.historical_confidence < 0.7:
            recommendations.append("Gather more historical performance data or adjust strategy")
        
        if confidence_score.risk_confidence < 0.7:
            recommendations.append("Review risk management parameters and position sizing")
        
        return recommendations
    
    def calibrate_confidence(self, actual_outcomes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calibrate confidence scores based on actual outcomes
        
        Args:
            actual_outcomes: List of actual trading outcomes with confidence scores
            
        Returns:
            Calibration metrics and adjustments
        """
        if len(actual_outcomes) < 10:
            return {"status": "insufficient_data", "required_samples": 10}
        
        calibration_results = {}
        
        for dimension in ConfidenceDimension:
            dim_name = dimension.value
            confidences = []
            accuracies = []
            
            for outcome in actual_outcomes:
                if dim_name in outcome.get("confidence_breakdown", {}):
                    conf = outcome["confidence_breakdown"][dim_name]
                    accuracy = outcome.get("accuracy", 0.0)
                    confidences.append(conf)
                    accuracies.append(accuracy)
            
            if len(confidences) >= 5:
                # Calculate calibration metrics
                correlation = np.corrcoef(confidences, accuracies)[0, 1] if len(confidences) > 1 else 0
                mean_confidence = statistics.mean(confidences)
                mean_accuracy = statistics.mean(accuracies)
                
                calibration_results[dim_name] = {
                    "correlation": correlation,
                    "mean_confidence": mean_confidence,
                    "mean_accuracy": mean_accuracy,
                    "calibration_gap": mean_confidence - mean_accuracy,
                    "sample_size": len(confidences)
                }
        
        # Update calibration data
        self.calibration_data = calibration_results
        
        return calibration_results
    
    def get_confidence_statistics(self) -> Dict[str, Any]:
        """Get comprehensive confidence statistics"""
        if not self.confidence_history:
            return {"status": "no_data"}
        
        recent_scores = [score for score in self.confidence_history 
                        if time.time() - score.timestamp < 86400]  # Last 24 hours
        
        stats = {
            "total_scores": len(self.confidence_history),
            "recent_scores_24h": len(recent_scores),
            "average_confidence": {
                "model": statistics.mean([s.model_confidence for s in recent_scores]) if recent_scores else 0,
                "data_quality": statistics.mean([s.data_quality for s in recent_scores]) if recent_scores else 0,
                "market": statistics.mean([s.market_confidence for s in recent_scores]) if recent_scores else 0,
                "historical": statistics.mean([s.historical_confidence for s in recent_scores]) if recent_scores else 0,
                "risk": statistics.mean([s.risk_confidence for s in recent_scores]) if recent_scores else 0,
                "composite": statistics.mean([s.composite_score for s in recent_scores]) if recent_scores else 0
            },
            "threshold_violations_24h": len([v for v in self.threshold_violations 
                                           if time.time() - v["timestamp"] < 86400]),
            "calibration_status": "calibrated" if self.calibration_data else "not_calibrated"
        }
        
        return stats