"""
AI Brain Enhanced ML-Processing Error DNA System
Surgical precision error analysis specifically for ML operations, training, and model management

ENHANCED ML-SPECIFIC ERROR PATTERNS:
- Model Training Failures (convergence, overfitting, data quality)
- Feature Engineering Errors (missing features, correlation issues)
- Real-time Inference Failures (latency, accuracy degradation)
- Online Learning Adaptation Issues (drift, catastrophic forgetting)
- Resource Management (memory, GPU, computational limits)
- Data Pipeline Integrity (corrupted features, missing targets)
"""

import time
import traceback
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import hashlib
from datetime import datetime

# Import base AI Brain Error DNA
import sys
sys.path.append('/mnt/f/WINDSURF/concept_ai/projects/ai_trading/server_microservice/services')
from shared.ai_brain_trading_error_dna import AiBrainTradingErrorDNA, TradingErrorPattern, TradingErrorCategory


class MLProcessingErrorCategory(Enum):
    """ML-Processing specific error categories for comprehensive coverage"""
    MODEL_TRAINING_FAILURE = "model_training_failure"
    FEATURE_ENGINEERING_ERROR = "feature_engineering_error"
    ONLINE_LEARNING_DRIFT = "online_learning_drift"
    PREDICTION_ACCURACY_DROP = "prediction_accuracy_drop"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    DATA_PIPELINE_CORRUPTION = "data_pipeline_corruption"
    MODEL_CONVERGENCE_FAILURE = "model_convergence_failure"
    ENSEMBLE_CONSISTENCY_ERROR = "ensemble_consistency_error"
    REAL_TIME_LATENCY_BREACH = "real_time_latency_breach"
    CATASTROPHIC_FORGETTING = "catastrophic_forgetting"
    HYPERPARAMETER_VALIDATION = "hyperparameter_validation"
    MODEL_STATE_CORRUPTION = "model_state_corruption"


@dataclass
class MLProcessingErrorPattern:
    """Enhanced ML-Processing error pattern with surgical precision"""
    error_id: str
    category: MLProcessingErrorCategory
    pattern: str
    description: str
    solution_confidence: float  # 0.0 to 1.0
    solution_steps: List[str]
    prevention_strategy: str
    related_patterns: List[str]
    ml_context: Dict[str, Any]  # ML-specific context
    trading_impact: str  # critical, high, medium, low
    urgency_level: str  # immediate, high, medium, low
    recovery_time_estimate: str  # time to resolve
    confidence_threshold: float  # minimum confidence to apply solution


class AiBrainMLProcessingErrorDNA(AiBrainTradingErrorDNA):
    """
    AI Brain Enhanced ML-Processing Error DNA System
    Extends base trading error DNA with ML-specific surgical precision patterns
    """
    
    def __init__(self, service_name: str = "ml-processing"):
        # Initialize base trading error DNA
        super().__init__(service_name)
        
        # ML-Processing specific initialization
        self.ml_error_patterns: Dict[str, MLProcessingErrorPattern] = {}
        self.ml_training_errors: List[Dict[str, Any]] = []
        self.model_performance_degradation: Dict[str, List[float]] = {}
        self.feature_quality_metrics: Dict[str, Dict[str, float]] = {}
        self.online_learning_metrics: Dict[str, Any] = {}
        
        # Initialize ML-specific error patterns
        self._initialize_ml_processing_patterns()
        
        # Setup ML-specific logging
        self.ml_logger = logging.getLogger(f"ai_brain_ml_error_dna_{service_name}")
        
    def _initialize_ml_processing_patterns(self):
        """Initialize comprehensive ML-Processing specific error patterns"""
        ml_patterns = [
            # Model Training Failure Patterns
            MLProcessingErrorPattern(
                error_id="ML_TRAIN_001",
                category=MLProcessingErrorCategory.MODEL_TRAINING_FAILURE,
                pattern="Model training convergence failure",
                description="ML model fails to converge during training process",
                solution_confidence=0.93,
                solution_steps=[
                    "Check learning rate - reduce if too high, increase if too low",
                    "Verify training data quality and balance",
                    "Adjust batch size for stable convergence",
                    "Implement early stopping to prevent overfitting",
                    "Consider different optimizer (Adam vs SGD vs RMSprop)",
                    "Validate feature scaling and normalization"
                ],
                prevention_strategy="Implement adaptive learning rate with convergence monitoring",
                related_patterns=["ML_TRAIN_002", "ML_DATA_001"],
                ml_context={
                    "algorithm_sensitivity": "high",
                    "data_dependency": "critical",
                    "computational_cost": "high"
                },
                trading_impact="high",
                urgency_level="high",
                recovery_time_estimate="30-60 minutes",
                confidence_threshold=0.85
            ),
            
            MLProcessingErrorPattern(
                error_id="ML_TRAIN_002",
                category=MLProcessingErrorCategory.MODEL_TRAINING_FAILURE,
                pattern="Overfitting detected in training metrics",
                description="Model shows signs of overfitting with validation loss increasing",
                solution_confidence=0.91,
                solution_steps=[
                    "Implement dropout regularization",
                    "Add L1/L2 regularization to loss function",
                    "Reduce model complexity (layers, parameters)",
                    "Increase training data or use data augmentation",
                    "Implement cross-validation for better generalization",
                    "Monitor validation metrics continuously"
                ],
                prevention_strategy="Early stopping with validation monitoring and regularization",
                related_patterns=["ML_TRAIN_001", "ML_VALID_001"],
                ml_context={
                    "model_complexity": "high",
                    "generalization_risk": "critical",
                    "validation_importance": "high"
                },
                trading_impact="high",
                urgency_level="medium",
                recovery_time_estimate="45-90 minutes",
                confidence_threshold=0.82
            ),
            
            # Feature Engineering Error Patterns
            MLProcessingErrorPattern(
                error_id="ML_FEATURE_001", 
                category=MLProcessingErrorCategory.FEATURE_ENGINEERING_ERROR,
                pattern="Missing or corrupted market features",
                description="Critical market features are missing or contain invalid values",
                solution_confidence=0.95,
                solution_steps=[
                    "Validate data source connection and integrity",
                    "Implement feature completeness checks",
                    "Create fallback feature computation methods",
                    "Add feature imputation for missing values",
                    "Implement feature validation pipeline",
                    "Setup alerts for feature quality degradation"
                ],
                prevention_strategy="Real-time feature validation with automated quality checks",
                related_patterns=["ML_DATA_001", "ML_PIPELINE_001"],
                ml_context={
                    "feature_criticality": "high",
                    "trading_dependency": "critical",
                    "real_time_impact": "immediate"
                },
                trading_impact="critical",
                urgency_level="immediate",
                recovery_time_estimate="5-15 minutes",
                confidence_threshold=0.90
            ),
            
            MLProcessingErrorPattern(
                error_id="ML_FEATURE_002",
                category=MLProcessingErrorCategory.FEATURE_ENGINEERING_ERROR,
                pattern="Feature correlation matrix singularity",
                description="Feature correlation matrix becomes singular, causing numerical instability",
                solution_confidence=0.88,
                solution_steps=[
                    "Remove highly correlated features (>0.95 correlation)",
                    "Apply PCA or dimensionality reduction",
                    "Implement feature selection based on importance",
                    "Add regularization to handle multicollinearity",
                    "Monitor feature correlation continuously",
                    "Implement variance inflation factor checks"
                ],
                prevention_strategy="Continuous feature correlation monitoring with automated removal",
                related_patterns=["ML_FEATURE_001", "ML_TRAIN_003"],
                ml_context={
                    "numerical_stability": "critical",
                    "feature_redundancy": "high",
                    "model_interpretability": "medium"
                },
                trading_impact="medium",
                urgency_level="medium",
                recovery_time_estimate="20-40 minutes",
                confidence_threshold=0.80
            ),
            
            # Online Learning Drift Patterns
            MLProcessingErrorPattern(
                error_id="ML_DRIFT_001",
                category=MLProcessingErrorCategory.ONLINE_LEARNING_DRIFT,
                pattern="Concept drift detected in model performance",
                description="Model performance degrading due to changing market conditions",
                solution_confidence=0.87,
                solution_steps=[
                    "Detect drift using statistical tests (KS test, ADWIN)",
                    "Implement adaptive learning rate adjustment",
                    "Retrain model on recent data window",
                    "Update feature importance weights",
                    "Implement ensemble with recent models",
                    "Monitor prediction confidence trends"
                ],
                prevention_strategy="Continuous drift detection with adaptive model updates",
                related_patterns=["ML_PERFORMANCE_001", "ML_ONLINE_001"],
                ml_context={
                    "adaptation_speed": "critical",
                    "market_sensitivity": "high",
                    "prediction_stability": "medium"
                },
                trading_impact="high",
                urgency_level="high",
                recovery_time_estimate="15-30 minutes",
                confidence_threshold=0.85
            ),
            
            # Prediction Accuracy Drop Patterns
            MLProcessingErrorPattern(
                error_id="ML_PERFORMANCE_001",
                category=MLProcessingErrorCategory.PREDICTION_ACCURACY_DROP,
                pattern="Significant prediction accuracy degradation",
                description="Model prediction accuracy drops below acceptable threshold",
                solution_confidence=0.90,
                solution_steps=[
                    "Analyze prediction error patterns",
                    "Check for data quality degradation",
                    "Validate model input features",
                    "Implement prediction confidence filtering",
                    "Consider model ensemble or fallback models",
                    "Trigger model retraining if persistent"
                ],
                prevention_strategy="Continuous accuracy monitoring with automated fallback",
                related_patterns=["ML_DRIFT_001", "ML_FEATURE_001"],
                ml_context={
                    "accuracy_threshold": "critical",
                    "trading_reliability": "high",
                    "confidence_calibration": "important"
                },
                trading_impact="critical",
                urgency_level="immediate",
                recovery_time_estimate="5-20 minutes",
                confidence_threshold=0.92
            ),
            
            # Resource Exhaustion Patterns
            MLProcessingErrorPattern(
                error_id="ML_RESOURCE_001",
                category=MLProcessingErrorCategory.RESOURCE_EXHAUSTION,
                pattern="Memory exhaustion during model training",
                description="System runs out of memory during ML model training",
                solution_confidence=0.94,
                solution_steps=[
                    "Implement batch processing with smaller batch sizes",
                    "Use gradient accumulation for effective larger batches",
                    "Implement model checkpointing for recovery",
                    "Optimize data loading and preprocessing",
                    "Consider model parallelism or distributed training",
                    "Monitor memory usage continuously"
                ],
                prevention_strategy="Memory monitoring with adaptive batch size adjustment",
                related_patterns=["ML_TRAIN_001", "ML_PIPELINE_001"],
                ml_context={
                    "resource_optimization": "critical",
                    "training_efficiency": "high",
                    "scalability_impact": "medium"
                },
                trading_impact="medium",
                urgency_level="high",
                recovery_time_estimate="10-25 minutes",
                confidence_threshold=0.88
            ),
            
            # Real-time Latency Breach Patterns
            MLProcessingErrorPattern(
                error_id="ML_LATENCY_001",
                category=MLProcessingErrorCategory.REAL_TIME_LATENCY_BREACH,
                pattern="Model inference latency exceeds real-time requirements",
                description="ML model inference takes longer than acceptable for trading decisions",
                solution_confidence=0.91,
                solution_steps=[
                    "Optimize model architecture for inference speed",
                    "Implement model quantization or pruning",
                    "Use cached predictions for repeated inputs",
                    "Implement parallel prediction processing",
                    "Consider simpler fallback models for speed",
                    "Profile and optimize computational bottlenecks"
                ],
                prevention_strategy="Continuous latency monitoring with performance optimization",
                related_patterns=["ML_RESOURCE_001", "ML_PERFORMANCE_001"],
                ml_context={
                    "speed_requirement": "critical",
                    "trading_timing": "immediate",
                    "accuracy_tradeoff": "balanced"
                },
                trading_impact="high",
                urgency_level="immediate",
                recovery_time_estimate="5-15 minutes",
                confidence_threshold=0.89
            ),
            
            # Model State Corruption Patterns
            MLProcessingErrorPattern(
                error_id="ML_STATE_001",
                category=MLProcessingErrorCategory.MODEL_STATE_CORRUPTION,
                pattern="Model state corruption detected",
                description="ML model internal state becomes corrupted, affecting predictions",
                solution_confidence=0.85,
                solution_steps=[
                    "Restore model from last known good checkpoint",
                    "Validate model parameters for corruption",
                    "Implement model state integrity checks",
                    "Retrain model if corruption is severe",
                    "Implement redundant model storage",
                    "Monitor model consistency continuously"
                ],
                prevention_strategy="Regular model checkpointing with integrity validation",
                related_patterns=["ML_PERFORMANCE_001", "ML_TRAIN_001"],
                ml_context={
                    "state_integrity": "critical",
                    "recovery_complexity": "high",
                    "prediction_reliability": "critical"
                },
                trading_impact="critical",
                urgency_level="immediate",
                recovery_time_estimate="15-45 minutes",
                confidence_threshold=0.90
            )
        ]
        
        # Store ML-specific patterns
        for pattern in ml_patterns:
            self.ml_error_patterns[pattern.error_id] = pattern
    
    def analyze_ml_error(self, error: Exception, ml_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Perform surgical precision ML-specific error analysis
        
        Args:
            error: The exception that occurred
            ml_context: ML-specific context (model_type, training_phase, feature_info, etc.)
            
        Returns:
            Comprehensive ML error analysis with solution guidance
        """
        # First, get base trading analysis
        base_analysis = self.analyze_error(error, ml_context)
        
        # Enhance with ML-specific analysis
        ml_signature = self._generate_ml_error_signature(error, ml_context)
        matched_ml_pattern = self._match_ml_error_pattern(error, ml_context)
        
        ml_analysis = {
            **base_analysis,
            "ml_error_signature": ml_signature,
            "ml_matched_pattern": None,
            "ml_solution_confidence": 0.0,
            "ml_recommended_actions": [],
            "ml_prevention_strategy": "",
            "ml_context_analysis": self._analyze_ml_context(ml_context),
            "resource_impact": "unknown",
            "recovery_time_estimate": "unknown",
            "model_safety_check": "required"
        }
        
        if matched_ml_pattern:
            ml_analysis.update({
                "ml_matched_pattern": matched_ml_pattern.error_id,
                "ml_pattern_description": matched_ml_pattern.description,
                "ml_solution_confidence": matched_ml_pattern.solution_confidence,
                "ml_recommended_actions": matched_ml_pattern.solution_steps,
                "ml_prevention_strategy": matched_ml_pattern.prevention_strategy,
                "resource_impact": matched_ml_pattern.ml_context.get("resource_impact", "unknown"),
                "recovery_time_estimate": matched_ml_pattern.recovery_time_estimate,
                "ml_trading_impact": matched_ml_pattern.trading_impact,
                "ml_urgency_level": matched_ml_pattern.urgency_level
            })
        
        # Learn from ML-specific error
        self._learn_from_ml_error(ml_analysis)
        
        # Log ML analysis
        self.ml_logger.error(f"AI Brain ML Error DNA Analysis: {json.dumps(ml_analysis, indent=2, default=str)}")
        
        return ml_analysis
    
    def _generate_ml_error_signature(self, error: Exception, ml_context: Dict[str, Any] = None) -> str:
        """Generate unique ML-specific error signature"""
        signature_data = {
            "error_type": type(error).__name__,
            "error_message": str(error)[:100],
            "service": self.service_name
        }
        
        if ml_context:
            # Add ML-specific context
            ml_fields = ["model_type", "algorithm", "training_phase", "feature_count", "batch_size", "learning_rate"]
            for field in ml_fields:
                if field in ml_context:
                    signature_data[f"ml_{field}"] = ml_context[field]
        
        signature_str = json.dumps(signature_data, sort_keys=True)
        return hashlib.md5(signature_str.encode()).hexdigest()[:16]  # Longer for ML specificity
    
    def _match_ml_error_pattern(self, error: Exception, ml_context: Dict[str, Any] = None) -> Optional[MLProcessingErrorPattern]:
        """Match error against ML-specific patterns with enhanced precision"""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # ML-specific keyword matching
        ml_keywords = []
        if ml_context:
            # Extract ML context keywords
            if "model_type" in ml_context:
                ml_keywords.append(ml_context["model_type"].lower())
            if "algorithm" in ml_context:
                ml_keywords.append(ml_context["algorithm"].lower())
            if "training_phase" in ml_context:
                ml_keywords.append(ml_context["training_phase"].lower())
        
        best_match = None
        best_score = 0.0
        
        for pattern_id, pattern in self.ml_error_patterns.items():
            pattern_keywords = pattern.pattern.lower().split()
            
            # Calculate matching score
            matches = 0
            total_keywords = len(pattern_keywords) + len(ml_keywords)
            
            # Check pattern keywords against error
            for keyword in pattern_keywords:
                if keyword in error_str or keyword in error_type:
                    matches += 1
            
            # Check ML context keywords
            for keyword in ml_keywords:
                if keyword in pattern.pattern.lower():
                    matches += 2  # Weight ML context higher
            
            # Calculate match score
            if total_keywords > 0:
                score = matches / total_keywords
                
                # Boost score for category relevance
                if ml_context and "training_phase" in ml_context:
                    if ml_context["training_phase"] == "training" and "train" in pattern.category.value:
                        score += 0.2
                    elif ml_context["training_phase"] == "inference" and "prediction" in pattern.category.value:
                        score += 0.2
                
                if score > best_score and score > 0.4:  # Minimum threshold
                    best_score = score
                    best_match = pattern
        
        return best_match
    
    def _analyze_ml_context(self, ml_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze ML context for additional insights"""
        if not ml_context:
            return {"status": "no_context"}
        
        analysis = {
            "context_completeness": 0.0,
            "critical_parameters": [],
            "risk_factors": [],
            "optimization_opportunities": []
        }
        
        # Check context completeness
        expected_fields = ["model_type", "algorithm", "training_phase", "data_shape", "performance_metrics"]
        present_fields = sum(1 for field in expected_fields if field in ml_context)
        analysis["context_completeness"] = present_fields / len(expected_fields)
        
        # Identify critical parameters
        if "learning_rate" in ml_context:
            lr = ml_context["learning_rate"]
            if lr > 0.1:
                analysis["risk_factors"].append("learning_rate_too_high")
            elif lr < 0.0001:
                analysis["risk_factors"].append("learning_rate_too_low")
        
        if "batch_size" in ml_context:
            batch_size = ml_context["batch_size"]
            if batch_size < 32:
                analysis["optimization_opportunities"].append("consider_larger_batch_size")
            elif batch_size > 1024:
                analysis["risk_factors"].append("batch_size_may_cause_memory_issues")
        
        # Check performance metrics trends
        if "accuracy_history" in ml_context:
            accuracies = ml_context["accuracy_history"]
            if len(accuracies) >= 3:
                recent_trend = np.diff(accuracies[-3:])
                if np.all(recent_trend < 0):
                    analysis["risk_factors"].append("accuracy_declining_trend")
        
        return analysis
    
    def _learn_from_ml_error(self, ml_analysis: Dict[str, Any]):
        """Learn from ML-specific error occurrence"""
        ml_signature = ml_analysis["ml_error_signature"]
        
        # Store in ML training errors
        self.ml_training_errors.append({
            "timestamp": time.time(),
            "signature": ml_signature,
            "pattern": ml_analysis.get("ml_matched_pattern"),
            "confidence": ml_analysis.get("ml_solution_confidence", 0.0),
            "context": ml_analysis.get("ml_context_analysis", {})
        })
        
        # Update model performance tracking
        if "model_name" in ml_analysis:
            model_name = ml_analysis["model_name"]
            if model_name not in self.model_performance_degradation:
                self.model_performance_degradation[model_name] = []
            
            # Track error frequency as performance indicator
            self.model_performance_degradation[model_name].append(time.time())
        
        # Keep memory usage under control
        if len(self.ml_training_errors) > 500:
            self.ml_training_errors = self.ml_training_errors[-500:]
    
    def suggest_ml_preventive_actions(self, ml_service_context: Dict[str, Any]) -> List[str]:
        """Suggest ML-specific preventive actions based on error history"""
        suggestions = self.suggest_preventive_actions(ml_service_context)  # Get base suggestions
        
        # Add ML-specific suggestions
        recent_ml_errors = [e for e in self.ml_training_errors if time.time() - e["timestamp"] < 86400]
        
        if len(recent_ml_errors) > 5:
            suggestions.append("🧠 High ML error frequency - implement comprehensive model validation")
        
        # Pattern-based suggestions
        pattern_counts = {}
        for error in recent_ml_errors:
            pattern = error.get("pattern")
            if pattern:
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        for pattern_id, count in pattern_counts.items():
            if count > 2 and pattern_id in self.ml_error_patterns:
                pattern = self.ml_error_patterns[pattern_id]
                suggestions.append(f"🎯 Frequent {pattern.category.value} errors - {pattern.prevention_strategy}")
        
        # Model-specific suggestions
        for model_name, error_times in self.model_performance_degradation.items():
            recent_errors = [t for t in error_times if time.time() - t < 86400]
            if len(recent_errors) > 3:
                suggestions.append(f"⚠️ Model {model_name} showing instability - consider retraining or validation")
        
        return suggestions
    
    def get_ml_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive ML error statistics"""
        base_stats = self.get_error_statistics()
        
        total_ml_errors = len(self.ml_training_errors)
        recent_ml_errors = [e for e in self.ml_training_errors if time.time() - e["timestamp"] < 86400]
        
        ml_category_stats = {}
        for error in self.ml_training_errors:
            pattern_id = error.get("pattern")
            if pattern_id and pattern_id in self.ml_error_patterns:
                category = self.ml_error_patterns[pattern_id].category.value
                ml_category_stats[category] = ml_category_stats.get(category, 0) + 1
        
        ml_stats = {
            **base_stats,
            "ml_specific_stats": {
                "total_ml_errors": total_ml_errors,
                "recent_ml_errors_24h": len(recent_ml_errors),
                "ml_error_rate_24h": len(recent_ml_errors) / 24.0 if recent_ml_errors else 0,
                "ml_category_breakdown": ml_category_stats,
                "ml_pattern_coverage": len([e for e in self.ml_training_errors if e.get("pattern")]) / max(total_ml_errors, 1),
                "average_ml_solution_confidence": sum([e.get("confidence", 0) for e in self.ml_training_errors]) / max(total_ml_errors, 1),
                "models_with_errors": len(self.model_performance_degradation),
                "feature_quality_issues": len(self.feature_quality_metrics)
            }
        }
        
        return ml_stats
    
    def export_ml_error_patterns(self) -> Dict[str, Any]:
        """Export ML-specific error patterns for sharing"""
        base_export = self.export_error_patterns()
        
        ml_export = {
            **base_export,
            "ml_specific_data": {
                "ml_patterns": {pid: asdict(pattern) for pid, pattern in self.ml_error_patterns.items()},
                "ml_training_errors": self.ml_training_errors[-100:],  # Last 100 for export
                "model_performance_degradation": self.model_performance_degradation,
                "feature_quality_metrics": self.feature_quality_metrics,
                "ml_statistics": self.get_ml_error_statistics()["ml_specific_stats"]
            }
        }
        
        return ml_export
    
    def validate_model_health(self, model_name: str, performance_metrics: Dict[str, float]) -> Dict[str, Any]:
        """Validate model health and detect potential issues"""
        health_report = {
            "model_name": model_name,
            "overall_health": "healthy",
            "health_score": 1.0,
            "warnings": [],
            "critical_issues": [],
            "recommendations": []
        }
        
        # Check accuracy trends
        if "accuracy" in performance_metrics:
            accuracy = performance_metrics["accuracy"]
            if accuracy < 0.6:
                health_report["critical_issues"].append("accuracy_below_threshold")
                health_report["overall_health"] = "critical"
                health_report["health_score"] *= 0.5
            elif accuracy < 0.75:
                health_report["warnings"].append("accuracy_degrading")
                health_report["health_score"] *= 0.8
        
        # Check prediction confidence
        if "confidence" in performance_metrics:
            confidence = performance_metrics["confidence"]
            if confidence < 0.7:
                health_report["warnings"].append("low_prediction_confidence")
                health_report["health_score"] *= 0.9
        
        # Check error frequency
        if model_name in self.model_performance_degradation:
            recent_errors = [t for t in self.model_performance_degradation[model_name] if time.time() - t < 86400]
            if len(recent_errors) > 5:
                health_report["critical_issues"].append("high_error_frequency")
                health_report["overall_health"] = "critical"
                health_report["health_score"] *= 0.6
        
        # Generate recommendations based on issues
        if health_report["critical_issues"]:
            health_report["recommendations"].extend([
                "Immediate model validation required",
                "Consider model retraining with recent data",
                "Implement fallback prediction strategy"
            ])
        elif health_report["warnings"]:
            health_report["recommendations"].extend([
                "Monitor model performance closely",
                "Consider hyperparameter tuning",
                "Evaluate data quality"
            ])
        
        return health_report


# Global ML-Processing Error DNA instance
ml_processing_error_dna = AiBrainMLProcessingErrorDNA("ml-processing")


def get_ml_error_dna() -> AiBrainMLProcessingErrorDNA:
    """Get the global ML-Processing Error DNA instance"""
    return ml_processing_error_dna


def analyze_ml_error(error: Exception, ml_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Convenience function for ML error analysis"""
    return ml_processing_error_dna.analyze_ml_error(error, ml_context)


def validate_model_health(model_name: str, performance_metrics: Dict[str, float]) -> Dict[str, Any]:
    """Convenience function for model health validation"""
    return ml_processing_error_dna.validate_model_health(model_name, performance_metrics)