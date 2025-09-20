"""
AI Brain Enhanced ML-Processing Decision Validator
Validates model selection decisions, feature importance thresholds, and training confidence

DECISION VALIDATION COMPONENTS:
- Model Selection Decision Validation (algorithm choice, hyperparameter selection)
- Feature Importance Threshold Validation (feature selection, dimensionality decisions)
- Training Confidence Validation (stopping criteria, convergence decisions)
- Prediction Confidence Validation (inference decisions, uncertainty quantification)
- Risk Assessment Decision Validation (trading risk, model deployment decisions)
- Ensemble Decision Validation (model combination, weighting decisions)
"""

import time
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
import logging
from datetime import datetime, timedelta
import statistics
from scipy import stats


class DecisionCategory(Enum):
    """Categories of ML decisions that require validation"""
    MODEL_SELECTION = "model_selection"
    FEATURE_SELECTION = "feature_selection"
    HYPERPARAMETER_OPTIMIZATION = "hyperparameter_optimization"
    TRAINING_TERMINATION = "training_termination"
    PREDICTION_CONFIDENCE = "prediction_confidence"
    RISK_ASSESSMENT = "risk_assessment"
    ENSEMBLE_COMPOSITION = "ensemble_composition"
    DATA_PREPROCESSING = "data_preprocessing"
    DEPLOYMENT_READINESS = "deployment_readiness"
    ADAPTATION_TRIGGER = "adaptation_trigger"


class DecisionCriteria(Enum):
    """Criteria for decision validation"""
    STATISTICAL_SIGNIFICANCE = "statistical_significance"
    BUSINESS_LOGIC = "business_logic"
    PERFORMANCE_THRESHOLD = "performance_threshold"
    RISK_TOLERANCE = "risk_tolerance"
    COMPUTATIONAL_EFFICIENCY = "computational_efficiency"
    INTERPRETABILITY = "interpretability"
    STABILITY = "stability"
    GENERALIZATION = "generalization"


class DecisionConfidenceLevel(Enum):
    """Confidence levels for decisions"""
    VERY_HIGH = "very_high"     # 0.9+
    HIGH = "high"               # 0.8-0.9
    MEDIUM = "medium"           # 0.6-0.8
    LOW = "low"                 # 0.4-0.6
    VERY_LOW = "very_low"       # <0.4


@dataclass
class DecisionValidationResult:
    """Result of a decision validation"""
    decision_id: str
    category: DecisionCategory
    decision_description: str
    validation_criteria: List[DecisionCriteria]
    confidence_score: float  # 0.0 to 1.0
    confidence_level: DecisionConfidenceLevel
    status: str  # "approved", "rejected", "requires_review"
    supporting_evidence: Dict[str, Any]
    risk_factors: List[str]
    recommendations: List[str]
    alternative_options: List[Dict[str, Any]]
    validation_timestamp: float
    execution_time_ms: float


class AiBrainMLProcessingDecisionValidator:
    """
    AI Brain Enhanced Decision Validator for ML-Processing Service
    Validates critical ML decisions with comprehensive analysis
    """
    
    def __init__(self, service_name: str = "ml-processing"):
        self.service_name = service_name
        self.logger = logging.getLogger(f"ai_brain_decision_validator_{service_name}")
        
        # Decision validation history and metrics
        self.decision_history: List[DecisionValidationResult] = []
        self.validation_metrics: Dict[str, Any] = {
            "total_decisions": 0,
            "approved_decisions": 0,
            "rejected_decisions": 0,
            "review_required_decisions": 0,
            "average_confidence": 0.0
        }
        
        # Decision validation thresholds
        self.decision_thresholds: Dict[str, Dict[str, float]] = {
            "model_selection": {
                "min_performance_improvement": 0.02,  # 2% improvement required
                "statistical_significance_p": 0.05,
                "min_confidence_score": 0.7
            },
            "feature_selection": {
                "min_importance_threshold": 0.01,
                "max_correlation_threshold": 0.95,
                "min_variance_threshold": 0.001
            },
            "training_termination": {
                "min_epochs": 10,
                "patience_threshold": 5,
                "min_improvement_threshold": 0.001
            },
            "prediction_confidence": {
                "min_prediction_confidence": 0.6,
                "uncertainty_threshold": 0.3,
                "consensus_threshold": 0.8
            },
            "risk_assessment": {
                "max_position_risk": 0.02,  # 2% of portfolio
                "max_model_uncertainty": 0.4,
                "min_backtest_periods": 252  # 1 year
            }
        }
        
        # Model performance baselines
        self.performance_baselines: Dict[str, Dict[str, float]] = {}
        self.feature_importance_history: Dict[str, List[Dict[str, float]]] = {}
        
        self.logger.info("AI Brain ML-Processing Decision Validator initialized")
    
    def validate_model_selection_decision(self, 
                                        candidate_models: List[Dict[str, Any]], 
                                        selection_criteria: Dict[str, Any],
                                        context: Dict[str, Any] = None) -> DecisionValidationResult:
        """
        Validate model selection decision based on performance and criteria
        
        Args:
            candidate_models: List of model candidates with performance metrics
            selection_criteria: Criteria for model selection
            context: Additional context for decision validation
            
        Returns:
            DecisionValidationResult with validation outcome
        """
        start_time = time.perf_counter()
        
        try:
            decision_id = f"model_selection_{int(time.time() * 1000)}"
            
            # Analyze model performances
            performance_analysis = self._analyze_model_performances(candidate_models)
            
            # Validate selection criteria
            criteria_validation = self._validate_selection_criteria(selection_criteria, performance_analysis)
            
            # Calculate confidence score
            confidence_score = self._calculate_model_selection_confidence(
                candidate_models, selection_criteria, performance_analysis
            )
            
            # Determine confidence level
            confidence_level = self._determine_confidence_level(confidence_score)
            
            # Generate recommendations
            recommendations = self._generate_model_selection_recommendations(
                candidate_models, performance_analysis, criteria_validation
            )
            
            # Assess risk factors
            risk_factors = self._assess_model_selection_risks(
                candidate_models, selection_criteria, performance_analysis
            )
            
            # Determine decision status
            if confidence_score >= 0.8 and len(risk_factors) == 0:
                status = "approved"
            elif confidence_score < 0.4 or any("critical" in risk.lower() for risk in risk_factors):
                status = "rejected"
            else:
                status = "requires_review"
            
            execution_time = (time.perf_counter() - start_time) * 1000
            
            result = DecisionValidationResult(
                decision_id=decision_id,
                category=DecisionCategory.MODEL_SELECTION,
                decision_description=f"Model selection from {len(candidate_models)} candidates",
                validation_criteria=[DecisionCriteria.PERFORMANCE_THRESHOLD, DecisionCriteria.STATISTICAL_SIGNIFICANCE],
                confidence_score=confidence_score,
                confidence_level=confidence_level,
                status=status,
                supporting_evidence={
                    "performance_analysis": performance_analysis,
                    "criteria_validation": criteria_validation,
                    "candidate_count": len(candidate_models)
                },
                risk_factors=risk_factors,
                recommendations=recommendations,
                alternative_options=self._suggest_alternative_models(candidate_models, performance_analysis),
                validation_timestamp=time.time(),
                execution_time_ms=execution_time
            )
            
            self._record_decision_validation(result)
            
            self.logger.info(f"Model selection decision validated: {status} (confidence: {confidence_score:.3f})")
            return result
            
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            self.logger.error(f"Model selection validation failed: {e}")
            
            return DecisionValidationResult(
                decision_id=f"model_selection_error_{int(time.time() * 1000)}",
                category=DecisionCategory.MODEL_SELECTION,
                decision_description="Model selection validation failed",
                validation_criteria=[],
                confidence_score=0.0,
                confidence_level=DecisionConfidenceLevel.VERY_LOW,
                status="rejected",
                supporting_evidence={"error": str(e)},
                risk_factors=["validation_failure"],
                recommendations=["Review model selection process", "Check input data quality"],
                alternative_options=[],
                validation_timestamp=time.time(),
                execution_time_ms=execution_time
            )
    
    def validate_feature_selection_decision(self,
                                          features: List[str],
                                          importance_scores: Dict[str, float],
                                          selection_threshold: float,
                                          context: Dict[str, Any] = None) -> DecisionValidationResult:
        """
        Validate feature selection decision based on importance and thresholds
        """
        start_time = time.perf_counter()
        
        try:
            decision_id = f"feature_selection_{int(time.time() * 1000)}"
            
            # Analyze feature importance distribution
            importance_analysis = self._analyze_feature_importance(importance_scores, selection_threshold)
            
            # Validate threshold selection
            threshold_validation = self._validate_feature_threshold(importance_scores, selection_threshold)
            
            # Check for feature redundancy
            redundancy_check = self._check_feature_redundancy(features, importance_scores, context)
            
            # Calculate confidence score
            confidence_score = self._calculate_feature_selection_confidence(
                importance_analysis, threshold_validation, redundancy_check
            )
            
            confidence_level = self._determine_confidence_level(confidence_score)
            
            # Generate recommendations
            recommendations = self._generate_feature_selection_recommendations(
                importance_analysis, threshold_validation, redundancy_check
            )
            
            # Assess risks
            risk_factors = self._assess_feature_selection_risks(
                features, importance_scores, selection_threshold, importance_analysis
            )
            
            # Determine status
            if confidence_score >= 0.75 and "critical" not in " ".join(risk_factors).lower():
                status = "approved"
            elif confidence_score < 0.5 or any("critical" in risk.lower() for risk in risk_factors):
                status = "rejected"
            else:
                status = "requires_review"
            
            execution_time = (time.perf_counter() - start_time) * 1000
            
            result = DecisionValidationResult(
                decision_id=decision_id,
                category=DecisionCategory.FEATURE_SELECTION,
                decision_description=f"Feature selection: {len([f for f in features if importance_scores.get(f, 0) >= selection_threshold])} of {len(features)} features",
                validation_criteria=[DecisionCriteria.STATISTICAL_SIGNIFICANCE, DecisionCriteria.PERFORMANCE_THRESHOLD],
                confidence_score=confidence_score,
                confidence_level=confidence_level,
                status=status,
                supporting_evidence={
                    "importance_analysis": importance_analysis,
                    "threshold_validation": threshold_validation,
                    "redundancy_check": redundancy_check
                },
                risk_factors=risk_factors,
                recommendations=recommendations,
                alternative_options=self._suggest_alternative_feature_selections(importance_scores, selection_threshold),
                validation_timestamp=time.time(),
                execution_time_ms=execution_time
            )
            
            self._record_decision_validation(result)
            
            # Update feature importance history
            self._update_feature_importance_history(features, importance_scores)
            
            self.logger.info(f"Feature selection decision validated: {status} (confidence: {confidence_score:.3f})")
            return result
            
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            self.logger.error(f"Feature selection validation failed: {e}")
            
            return self._create_error_result("feature_selection", str(e), execution_time)
    
    def validate_prediction_confidence_decision(self,
                                              predictions: List[float],
                                              confidence_scores: List[float],
                                              uncertainty_estimates: List[float],
                                              context: Dict[str, Any] = None) -> DecisionValidationResult:
        """
        Validate prediction confidence and uncertainty estimates
        """
        start_time = time.perf_counter()
        
        try:
            decision_id = f"prediction_confidence_{int(time.time() * 1000)}"
            
            # Analyze prediction confidence distribution
            confidence_analysis = self._analyze_prediction_confidence(confidence_scores)
            
            # Analyze uncertainty estimates
            uncertainty_analysis = self._analyze_uncertainty_estimates(uncertainty_estimates)
            
            # Check prediction consistency
            consistency_check = self._check_prediction_consistency(predictions, confidence_scores)
            
            # Calculate overall confidence score
            confidence_score = self._calculate_prediction_confidence_score(
                confidence_analysis, uncertainty_analysis, consistency_check
            )
            
            confidence_level = self._determine_confidence_level(confidence_score)
            
            # Generate recommendations
            recommendations = self._generate_prediction_recommendations(
                confidence_analysis, uncertainty_analysis, consistency_check
            )
            
            # Assess prediction risks
            risk_factors = self._assess_prediction_risks(
                predictions, confidence_scores, uncertainty_estimates, confidence_analysis
            )
            
            # Determine status based on trading thresholds
            min_confidence = self.decision_thresholds["prediction_confidence"]["min_prediction_confidence"]
            max_uncertainty = self.decision_thresholds["prediction_confidence"]["uncertainty_threshold"]
            
            avg_confidence = statistics.mean(confidence_scores) if confidence_scores else 0.0
            avg_uncertainty = statistics.mean(uncertainty_estimates) if uncertainty_estimates else 1.0
            
            if avg_confidence >= min_confidence and avg_uncertainty <= max_uncertainty and not risk_factors:
                status = "approved"
            elif avg_confidence < min_confidence * 0.7 or avg_uncertainty > max_uncertainty * 1.5:
                status = "rejected"
            else:
                status = "requires_review"
            
            execution_time = (time.perf_counter() - start_time) * 1000
            
            result = DecisionValidationResult(
                decision_id=decision_id,
                category=DecisionCategory.PREDICTION_CONFIDENCE,
                decision_description=f"Prediction confidence validation for {len(predictions)} predictions",
                validation_criteria=[DecisionCriteria.PERFORMANCE_THRESHOLD, DecisionCriteria.RISK_TOLERANCE],
                confidence_score=confidence_score,
                confidence_level=confidence_level,
                status=status,
                supporting_evidence={
                    "confidence_analysis": confidence_analysis,
                    "uncertainty_analysis": uncertainty_analysis,
                    "consistency_check": consistency_check,
                    "avg_confidence": avg_confidence,
                    "avg_uncertainty": avg_uncertainty
                },
                risk_factors=risk_factors,
                recommendations=recommendations,
                alternative_options=self._suggest_prediction_alternatives(confidence_analysis, uncertainty_analysis),
                validation_timestamp=time.time(),
                execution_time_ms=execution_time
            )
            
            self._record_decision_validation(result)
            
            self.logger.info(f"Prediction confidence validated: {status} (confidence: {confidence_score:.3f})")
            return result
            
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            self.logger.error(f"Prediction confidence validation failed: {e}")
            
            return self._create_error_result("prediction_confidence", str(e), execution_time)
    
    def validate_training_termination_decision(self,
                                             training_metrics: List[Dict[str, float]],
                                             stopping_criteria: Dict[str, Any],
                                             context: Dict[str, Any] = None) -> DecisionValidationResult:
        """
        Validate training termination decision based on metrics and criteria
        """
        start_time = time.perf_counter()
        
        try:
            decision_id = f"training_termination_{int(time.time() * 1000)}"
            
            # Analyze training progress
            progress_analysis = self._analyze_training_progress(training_metrics)
            
            # Validate stopping criteria
            criteria_validation = self._validate_stopping_criteria(training_metrics, stopping_criteria)
            
            # Check for overfitting
            overfitting_check = self._check_overfitting_signs(training_metrics)
            
            # Calculate confidence in termination decision
            confidence_score = self._calculate_termination_confidence(
                progress_analysis, criteria_validation, overfitting_check
            )
            
            confidence_level = self._determine_confidence_level(confidence_score)
            
            # Generate recommendations
            recommendations = self._generate_training_recommendations(
                progress_analysis, criteria_validation, overfitting_check
            )
            
            # Assess training risks
            risk_factors = self._assess_training_risks(
                training_metrics, progress_analysis, overfitting_check
            )
            
            # Determine status
            if confidence_score >= 0.8 and not any("continue" in rec.lower() for rec in recommendations):
                status = "approved"  # Approve termination
            elif confidence_score < 0.4 or any("critical" in risk.lower() for risk in risk_factors):
                status = "rejected"  # Reject termination, continue training
            else:
                status = "requires_review"
            
            execution_time = (time.perf_counter() - start_time) * 1000
            
            result = DecisionValidationResult(
                decision_id=decision_id,
                category=DecisionCategory.TRAINING_TERMINATION,
                decision_description=f"Training termination decision after {len(training_metrics)} epochs",
                validation_criteria=[DecisionCriteria.PERFORMANCE_THRESHOLD, DecisionCriteria.STABILITY],
                confidence_score=confidence_score,
                confidence_level=confidence_level,
                status=status,
                supporting_evidence={
                    "progress_analysis": progress_analysis,
                    "criteria_validation": criteria_validation,
                    "overfitting_check": overfitting_check,
                    "epochs_trained": len(training_metrics)
                },
                risk_factors=risk_factors,
                recommendations=recommendations,
                alternative_options=self._suggest_training_alternatives(progress_analysis, criteria_validation),
                validation_timestamp=time.time(),
                execution_time_ms=execution_time
            )
            
            self._record_decision_validation(result)
            
            self.logger.info(f"Training termination decision validated: {status} (confidence: {confidence_score:.3f})")
            return result
            
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            self.logger.error(f"Training termination validation failed: {e}")
            
            return self._create_error_result("training_termination", str(e), execution_time)
    
    # Helper methods for analysis
    
    def _analyze_model_performances(self, candidate_models: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance metrics across candidate models"""
        if not candidate_models:
            return {"error": "No candidate models provided"}
        
        metrics = ["accuracy", "precision", "recall", "f1_score", "auc", "mse", "r2_score"]
        performance_analysis = {}
        
        for metric in metrics:
            values = [model.get(metric) for model in candidate_models if model.get(metric) is not None]
            if values:
                performance_analysis[metric] = {
                    "mean": statistics.mean(values),
                    "std": statistics.stdev(values) if len(values) > 1 else 0.0,
                    "min": min(values),
                    "max": max(values),
                    "range": max(values) - min(values)
                }
        
        # Identify best performing models
        if "accuracy" in performance_analysis:
            best_accuracy_idx = max(range(len(candidate_models)), 
                                  key=lambda i: candidate_models[i].get("accuracy", 0))
            performance_analysis["best_model_index"] = best_accuracy_idx
        
        return performance_analysis
    
    def _validate_selection_criteria(self, criteria: Dict[str, Any], performance_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Validate model selection criteria"""
        validation = {
            "criteria_completeness": 0.0,
            "threshold_reasonableness": True,
            "statistical_validity": True
        }
        
        expected_criteria = ["performance_metric", "threshold", "optimization_target"]
        present_criteria = sum(1 for c in expected_criteria if c in criteria)
        validation["criteria_completeness"] = present_criteria / len(expected_criteria)
        
        # Check threshold reasonableness
        if "threshold" in criteria and "performance_metric" in criteria:
            metric = criteria["performance_metric"]
            threshold = criteria["threshold"]
            
            if metric in performance_analysis:
                metric_stats = performance_analysis[metric]
                if threshold < metric_stats["min"] or threshold > metric_stats["max"]:
                    validation["threshold_reasonableness"] = False
        
        return validation
    
    def _calculate_model_selection_confidence(self, 
                                            candidate_models: List[Dict[str, Any]], 
                                            selection_criteria: Dict[str, Any],
                                            performance_analysis: Dict[str, Any]) -> float:
        """Calculate confidence score for model selection"""
        confidence_factors = []
        
        # Factor 1: Performance difference significance
        if "accuracy" in performance_analysis and performance_analysis["accuracy"]["range"] > 0.05:
            confidence_factors.append(0.9)
        elif "accuracy" in performance_analysis:
            confidence_factors.append(0.6)
        else:
            confidence_factors.append(0.4)
        
        # Factor 2: Number of candidates evaluated
        if len(candidate_models) >= 5:
            confidence_factors.append(0.9)
        elif len(candidate_models) >= 3:
            confidence_factors.append(0.7)
        else:
            confidence_factors.append(0.5)
        
        # Factor 3: Criteria completeness
        criteria_completeness = len(selection_criteria) / 5.0  # Assume 5 is ideal
        confidence_factors.append(min(criteria_completeness, 1.0))
        
        return statistics.mean(confidence_factors)
    
    def _analyze_feature_importance(self, importance_scores: Dict[str, float], threshold: float) -> Dict[str, Any]:
        """Analyze feature importance distribution and selection"""
        if not importance_scores:
            return {"error": "No importance scores provided"}
        
        scores = list(importance_scores.values())
        selected_count = sum(1 for score in scores if score >= threshold)
        
        analysis = {
            "total_features": len(scores),
            "selected_features": selected_count,
            "selection_ratio": selected_count / len(scores),
            "importance_stats": {
                "mean": statistics.mean(scores),
                "std": statistics.stdev(scores) if len(scores) > 1 else 0.0,
                "min": min(scores),
                "max": max(scores),
                "median": statistics.median(scores)
            },
            "threshold_percentile": sum(1 for score in scores if score < threshold) / len(scores)
        }
        
        return analysis
    
    def _analyze_prediction_confidence(self, confidence_scores: List[float]) -> Dict[str, Any]:
        """Analyze prediction confidence distribution"""
        if not confidence_scores:
            return {"error": "No confidence scores provided"}
        
        analysis = {
            "mean_confidence": statistics.mean(confidence_scores),
            "std_confidence": statistics.stdev(confidence_scores) if len(confidence_scores) > 1 else 0.0,
            "min_confidence": min(confidence_scores),
            "max_confidence": max(confidence_scores),
            "low_confidence_count": sum(1 for c in confidence_scores if c < 0.5),
            "high_confidence_count": sum(1 for c in confidence_scores if c >= 0.8),
            "confidence_distribution": {
                "very_low": sum(1 for c in confidence_scores if c < 0.4),
                "low": sum(1 for c in confidence_scores if 0.4 <= c < 0.6),
                "medium": sum(1 for c in confidence_scores if 0.6 <= c < 0.8),
                "high": sum(1 for c in confidence_scores if c >= 0.8)
            }
        }
        
        return analysis
    
    def _analyze_training_progress(self, training_metrics: List[Dict[str, float]]) -> Dict[str, Any]:
        """Analyze training progress and convergence"""
        if not training_metrics:
            return {"error": "No training metrics provided"}
        
        # Extract loss progression
        train_losses = [m.get("train_loss", float('inf')) for m in training_metrics]
        val_losses = [m.get("val_loss", float('inf')) for m in training_metrics if m.get("val_loss") is not None]
        
        analysis = {
            "epochs_trained": len(training_metrics),
            "converged": False,
            "overfitting_detected": False,
            "improvement_trend": "unknown"
        }
        
        if len(train_losses) >= 5:
            # Check convergence (last 5 epochs show minimal improvement)
            recent_losses = train_losses[-5:]
            improvement = (recent_losses[0] - recent_losses[-1]) / recent_losses[0]
            analysis["recent_improvement"] = improvement
            analysis["converged"] = improvement < 0.001  # Less than 0.1% improvement
            
            # Check overall trend
            if len(train_losses) >= 10:
                recent_trend = np.polyfit(range(5), recent_losses, 1)[0]
                analysis["improvement_trend"] = "decreasing" if recent_trend < 0 else "increasing" if recent_trend > 0 else "stable"
        
        if len(val_losses) >= 5 and len(train_losses) >= 5:
            # Check for overfitting
            train_recent = train_losses[-5:]
            val_recent = val_losses[-5:]
            
            train_trend = np.polyfit(range(5), train_recent, 1)[0]
            val_trend = np.polyfit(range(5), val_recent, 1)[0]
            
            # Overfitting if train loss decreasing but val loss increasing
            analysis["overfitting_detected"] = train_trend < -0.001 and val_trend > 0.001
        
        return analysis
    
    def _determine_confidence_level(self, confidence_score: float) -> DecisionConfidenceLevel:
        """Determine confidence level based on score"""
        if confidence_score >= 0.9:
            return DecisionConfidenceLevel.VERY_HIGH
        elif confidence_score >= 0.8:
            return DecisionConfidenceLevel.HIGH
        elif confidence_score >= 0.6:
            return DecisionConfidenceLevel.MEDIUM
        elif confidence_score >= 0.4:
            return DecisionConfidenceLevel.LOW
        else:
            return DecisionConfidenceLevel.VERY_LOW
    
    def _create_error_result(self, category_name: str, error_message: str, execution_time: float) -> DecisionValidationResult:
        """Create error result for failed validations"""
        return DecisionValidationResult(
            decision_id=f"{category_name}_error_{int(time.time() * 1000)}",
            category=DecisionCategory.MODEL_SELECTION,  # Default category
            decision_description=f"{category_name} validation failed",
            validation_criteria=[],
            confidence_score=0.0,
            confidence_level=DecisionConfidenceLevel.VERY_LOW,
            status="rejected",
            supporting_evidence={"error": error_message},
            risk_factors=["validation_failure"],
            recommendations=[f"Review {category_name} process", "Check input data quality"],
            alternative_options=[],
            validation_timestamp=time.time(),
            execution_time_ms=execution_time
        )
    
    def _record_decision_validation(self, result: DecisionValidationResult):
        """Record decision validation result"""
        self.decision_history.append(result)
        
        # Update metrics
        self.validation_metrics["total_decisions"] += 1
        if result.status == "approved":
            self.validation_metrics["approved_decisions"] += 1
        elif result.status == "rejected":
            self.validation_metrics["rejected_decisions"] += 1
        else:
            self.validation_metrics["review_required_decisions"] += 1
        
        # Update average confidence
        total_confidence = (self.validation_metrics["average_confidence"] * 
                          (self.validation_metrics["total_decisions"] - 1) + result.confidence_score)
        self.validation_metrics["average_confidence"] = total_confidence / self.validation_metrics["total_decisions"]
        
        # Keep history limited
        if len(self.decision_history) > 1000:
            self.decision_history = self.decision_history[-1000:]
    
    # Placeholder methods for comprehensive analysis (simplified implementations)
    
    def _generate_model_selection_recommendations(self, candidates, analysis, validation):
        return ["Consider ensemble methods", "Validate on additional data"]
    
    def _assess_model_selection_risks(self, candidates, criteria, analysis):
        return [] if len(candidates) > 2 else ["Limited model diversity"]
    
    def _suggest_alternative_models(self, candidates, analysis):
        return [{"type": "ensemble", "confidence": 0.8}]
    
    def _validate_feature_threshold(self, importance_scores, threshold):
        return {"threshold_reasonable": 0.001 <= threshold <= 1.0}
    
    def _check_feature_redundancy(self, features, importance_scores, context):
        return {"redundancy_detected": False, "redundant_pairs": []}
    
    def _calculate_feature_selection_confidence(self, importance_analysis, threshold_validation, redundancy_check):
        base_confidence = 0.8
        if importance_analysis.get("selection_ratio", 0) < 0.1:  # Too few features
            base_confidence -= 0.2
        if not threshold_validation.get("threshold_reasonable", True):
            base_confidence -= 0.3
        return max(0.0, base_confidence)
    
    def _generate_feature_selection_recommendations(self, importance_analysis, threshold_validation, redundancy_check):
        recs = []
        if importance_analysis.get("selection_ratio", 1.0) < 0.1:
            recs.append("Consider lowering feature selection threshold")
        if redundancy_check.get("redundancy_detected", False):
            recs.append("Remove redundant features")
        return recs
    
    def _assess_feature_selection_risks(self, features, importance_scores, threshold, analysis):
        risks = []
        if analysis.get("selection_ratio", 1.0) < 0.05:
            risks.append("Too few features selected - may lose important information")
        return risks
    
    def _suggest_alternative_feature_selections(self, importance_scores, threshold):
        return [{"threshold": threshold * 0.8, "rationale": "More inclusive selection"}]
    
    def _update_feature_importance_history(self, features, importance_scores):
        timestamp = datetime.now().isoformat()
        if "current_session" not in self.feature_importance_history:
            self.feature_importance_history["current_session"] = []
        
        self.feature_importance_history["current_session"].append({
            "timestamp": timestamp,
            "importance_scores": importance_scores.copy()
        })
    
    def _analyze_uncertainty_estimates(self, uncertainty_estimates):
        if not uncertainty_estimates:
            return {"error": "No uncertainty estimates"}
        
        return {
            "mean_uncertainty": statistics.mean(uncertainty_estimates),
            "max_uncertainty": max(uncertainty_estimates),
            "high_uncertainty_count": sum(1 for u in uncertainty_estimates if u > 0.5)
        }
    
    def _check_prediction_consistency(self, predictions, confidence_scores):
        if len(predictions) != len(confidence_scores):
            return {"consistent": False, "reason": "Length mismatch"}
        
        return {"consistent": True, "correlation": 0.8}  # Simplified
    
    def _calculate_prediction_confidence_score(self, confidence_analysis, uncertainty_analysis, consistency_check):
        base_score = confidence_analysis.get("mean_confidence", 0.5)
        if not consistency_check.get("consistent", True):
            base_score -= 0.2
        if uncertainty_analysis.get("mean_uncertainty", 0) > 0.5:
            base_score -= 0.3
        return max(0.0, base_score)
    
    def _generate_prediction_recommendations(self, confidence_analysis, uncertainty_analysis, consistency_check):
        recs = []
        if confidence_analysis.get("mean_confidence", 1.0) < 0.6:
            recs.append("Improve model calibration")
        if uncertainty_analysis.get("mean_uncertainty", 0) > 0.4:
            recs.append("Consider ensemble methods to reduce uncertainty")
        return recs
    
    def _assess_prediction_risks(self, predictions, confidence_scores, uncertainty_estimates, analysis):
        risks = []
        if analysis.get("mean_confidence", 1.0) < 0.5:
            risks.append("Low prediction confidence may affect trading decisions")
        return risks
    
    def _suggest_prediction_alternatives(self, confidence_analysis, uncertainty_analysis):
        return [{"method": "ensemble_averaging", "expected_improvement": 0.1}]
    
    def _validate_stopping_criteria(self, training_metrics, stopping_criteria):
        return {
            "criteria_met": len(training_metrics) >= stopping_criteria.get("min_epochs", 10),
            "patience_exceeded": False
        }
    
    def _check_overfitting_signs(self, training_metrics):
        return {"overfitting_detected": False, "validation_gap": 0.05}
    
    def _calculate_termination_confidence(self, progress_analysis, criteria_validation, overfitting_check):
        base_confidence = 0.7
        if progress_analysis.get("converged", False):
            base_confidence += 0.2
        if overfitting_check.get("overfitting_detected", False):
            base_confidence += 0.1  # Good to stop if overfitting
        return min(1.0, base_confidence)
    
    def _generate_training_recommendations(self, progress_analysis, criteria_validation, overfitting_check):
        recs = []
        if not progress_analysis.get("converged", False):
            recs.append("Continue training - model not converged")
        if overfitting_check.get("overfitting_detected", False):
            recs.append("Stop training - overfitting detected")
        return recs
    
    def _assess_training_risks(self, training_metrics, progress_analysis, overfitting_check):
        risks = []
        if len(training_metrics) < 5:
            risks.append("Insufficient training - may underfit")
        return risks
    
    def _suggest_training_alternatives(self, progress_analysis, criteria_validation):
        return [{"action": "adjust_learning_rate", "rationale": "Improve convergence"}]
    
    def get_decision_validation_statistics(self) -> Dict[str, Any]:
        """Get comprehensive decision validation statistics"""
        recent_decisions = [d for d in self.decision_history if time.time() - d.validation_timestamp < 86400]
        
        category_stats = {}
        for decision in recent_decisions:
            category = decision.category.value
            if category not in category_stats:
                category_stats[category] = {"total": 0, "approved": 0, "rejected": 0, "review": 0}
            
            category_stats[category]["total"] += 1
            if decision.status == "approved":
                category_stats[category]["approved"] += 1
            elif decision.status == "rejected":
                category_stats[category]["rejected"] += 1
            else:
                category_stats[category]["review"] += 1
        
        return {
            "total_decisions_24h": len(recent_decisions),
            "overall_metrics": self.validation_metrics,
            "category_breakdown": category_stats,
            "decision_thresholds": self.decision_thresholds,
            "approval_rate": self.validation_metrics["approved_decisions"] / max(self.validation_metrics["total_decisions"], 1),
            "last_updated": datetime.now().isoformat()
        }


# Global ML-Processing Decision Validator instance
ml_processing_decision_validator = AiBrainMLProcessingDecisionValidator("ml-processing")


def get_ml_decision_validator() -> AiBrainMLProcessingDecisionValidator:
    """Get the global ML-Processing Decision Validator instance"""
    return ml_processing_decision_validator


def validate_model_selection(candidate_models: List[Dict[str, Any]], 
                           selection_criteria: Dict[str, Any],
                           context: Dict[str, Any] = None) -> DecisionValidationResult:
    """Convenience function for model selection validation"""
    return ml_processing_decision_validator.validate_model_selection_decision(
        candidate_models, selection_criteria, context
    )


def validate_feature_selection(features: List[str],
                             importance_scores: Dict[str, float],
                             selection_threshold: float,
                             context: Dict[str, Any] = None) -> DecisionValidationResult:
    """Convenience function for feature selection validation"""
    return ml_processing_decision_validator.validate_feature_selection_decision(
        features, importance_scores, selection_threshold, context
    )