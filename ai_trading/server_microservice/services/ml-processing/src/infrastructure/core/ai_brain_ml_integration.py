"""
AI Brain ML-Processing Integration Hub
Centralized integration point for all AI Brain validation components

This module provides a unified interface for accessing all AI Brain validation
capabilities specifically designed for ML-Processing operations.

INTEGRATED AI BRAIN COMPONENTS:
1. Error DNA System - ML-specific error pattern analysis
2. Reality Checker - Comprehensive pre-execution validation
3. Decision Validator - ML decision analysis and validation
4. Pre-execution Safety - Safety protocols for ML operations

USAGE:
    from .ai_brain_ml_integration import MLProcessingAIBrain
    
    # Initialize AI Brain
    ai_brain = MLProcessingAIBrain()
    
    # Comprehensive validation before ML operation
    validation_result = ai_brain.comprehensive_validation(
        operation_type="train",
        operation_context={
            "algorithm": "random_forest",
            "training_data": dataframe,
            "features": feature_list,
            "target": "price_return"
        }
    )
    
    if validation_result["can_proceed_safely"]:
        # Proceed with ML operation
        pass
    else:
        # Handle validation failures
        pass
"""

import time
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import json

# Import all AI Brain components
from .ml_processing_error_dna import (
    AiBrainMLProcessingErrorDNA,
    get_ml_error_dna,
    analyze_ml_error
)

from .ml_processing_reality_checker import (
    AiBrainMLProcessingRealityChecker,
    get_ml_reality_checker,
    perform_reality_check
)

from .ml_processing_decision_validator import (
    AiBrainMLProcessingDecisionValidator,
    get_ml_decision_validator,
    validate_model_selection,
    validate_feature_selection
)

from .ml_processing_safety_validator import (
    AiBrainMLProcessingSafetyValidator,
    get_ml_safety_validator,
    perform_safety_check
)


@dataclass
class AIBrainValidationResult:
    """Comprehensive AI Brain validation result"""
    operation_type: str
    operation_id: str
    overall_status: str  # "approved", "rejected", "requires_review", "critical_failure"
    confidence_score: float  # 0.0 to 1.0
    validation_timestamp: datetime
    execution_time_ms: float
    
    # Individual component results
    error_dna_status: str
    reality_check_status: str
    decision_validation_status: str
    safety_validation_status: str
    
    # Validation details
    validation_details: Dict[str, Any]
    recommendations: List[str]
    risk_factors: List[str]
    can_proceed: bool
    requires_monitoring: bool
    
    # Performance metrics
    performance_metrics: Dict[str, float]


class MLProcessingAIBrain:
    """
    ML-Processing AI Brain Integration Hub
    
    Provides unified access to all AI Brain validation capabilities
    with intelligent orchestration and decision aggregation.
    """
    
    def __init__(self, service_name: str = "ml-processing"):
        self.service_name = service_name
        self.logger = logging.getLogger(f"ai_brain_integration_{service_name}")
        
        # Initialize all AI Brain components
        self.error_dna = get_ml_error_dna()
        self.reality_checker = get_ml_reality_checker()
        self.decision_validator = get_ml_decision_validator()
        self.safety_validator = get_ml_safety_validator()
        
        # Integration metrics
        self.integration_metrics = {
            "total_validations": 0,
            "approved_operations": 0,
            "rejected_operations": 0,
            "review_required_operations": 0,
            "average_confidence_score": 0.0,
            "average_execution_time_ms": 0.0
        }
        
        # Validation history
        self.validation_history: List[AIBrainValidationResult] = []
        
        self.logger.info("ML-Processing AI Brain Integration Hub initialized")
    
    def comprehensive_validation(self,
                                operation_type: str,
                                operation_context: Dict[str, Any],
                                validation_level: str = "standard") -> AIBrainValidationResult:
        """
        Perform comprehensive AI Brain validation for ML operation
        
        Args:
            operation_type: Type of ML operation (train, predict, feature_engineering, etc.)
            operation_context: Complete context for the operation
            validation_level: Level of validation (minimal, standard, strict)
            
        Returns:
            AIBrainValidationResult with comprehensive validation outcome
        """
        start_time = time.perf_counter()
        operation_id = f"{operation_type}_{int(time.time() * 1000)}"
        
        try:
            self.logger.info(f"Starting comprehensive AI Brain validation for {operation_type}")
            
            # Step 1: Reality Check - Ensure operation is feasible
            reality_result = self.reality_checker.perform_comprehensive_reality_check(
                operation_type, operation_context
            )
            
            # Step 2: Safety Validation - Ensure operation is safe
            safety_result = self.safety_validator.perform_comprehensive_safety_check(
                operation_type, operation_context, validation_level
            )
            
            # Step 3: Decision Validation (if applicable)
            decision_result = None
            if self._requires_decision_validation(operation_type, operation_context):
                decision_result = self._perform_decision_validation(operation_type, operation_context)
            
            # Calculate overall confidence score
            confidence_score = self._calculate_overall_confidence(
                reality_result, safety_result, decision_result
            )
            
            # Determine overall status
            overall_status = self._determine_overall_status(
                reality_result, safety_result, decision_result, confidence_score
            )
            
            # Generate comprehensive recommendations
            recommendations = self._generate_comprehensive_recommendations(
                reality_result, safety_result, decision_result
            )
            
            # Assess risk factors
            risk_factors = self._assess_overall_risk_factors(
                reality_result, safety_result, decision_result
            )
            
            # Determine if operation can proceed
            can_proceed = self._can_proceed_safely(
                overall_status, reality_result, safety_result, decision_result
            )
            
            # Check if monitoring is required
            requires_monitoring = self._requires_monitoring(
                reality_result, safety_result, decision_result
            )
            
            execution_time = (time.perf_counter() - start_time) * 1000
            
            # Create comprehensive result
            result = AIBrainValidationResult(
                operation_type=operation_type,
                operation_id=operation_id,
                overall_status=overall_status,
                confidence_score=confidence_score,
                validation_timestamp=datetime.now(),
                execution_time_ms=execution_time,
                error_dna_status="ready",  # Error DNA is reactive
                reality_check_status=reality_result["overall_status"],
                decision_validation_status=decision_result.status if decision_result else "not_applicable",
                safety_validation_status=safety_result["overall_safety_status"],
                validation_details={
                    "reality_check": reality_result,
                    "safety_validation": safety_result,
                    "decision_validation": asdict(decision_result) if decision_result else None
                },
                recommendations=recommendations,
                risk_factors=risk_factors,
                can_proceed=can_proceed,
                requires_monitoring=requires_monitoring,
                performance_metrics={
                    "confidence_score": confidence_score,
                    "reality_check_time_ms": reality_result.get("execution_time_ms", 0),
                    "safety_check_time_ms": safety_result.get("execution_time_ms", 0),
                    "decision_validation_time_ms": decision_result.execution_time_ms if decision_result else 0,
                    "total_execution_time_ms": execution_time
                }
            )
            
            # Record validation
            self._record_validation(result)
            
            self.logger.info(f"Comprehensive AI Brain validation completed: {overall_status} "
                           f"(confidence: {confidence_score:.3f}, time: {execution_time:.2f}ms)")
            
            return result
            
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            self.logger.error(f"Comprehensive validation failed: {e}")
            
            # Return error result
            return AIBrainValidationResult(
                operation_type=operation_type,
                operation_id=operation_id,
                overall_status="critical_failure",
                confidence_score=0.0,
                validation_timestamp=datetime.now(),
                execution_time_ms=execution_time,
                error_dna_status="error",
                reality_check_status="error",
                decision_validation_status="error",
                safety_validation_status="error",
                validation_details={"error": str(e)},
                recommendations=["Review AI Brain integration", "Check operation context"],
                risk_factors=["validation_system_failure"],
                can_proceed=False,
                requires_monitoring=True,
                performance_metrics={"execution_time_ms": execution_time}
            )
    
    def handle_ml_error(self, error: Exception, ml_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle ML error using Error DNA System
        
        Args:
            error: The exception that occurred
            ml_context: ML-specific context
            
        Returns:
            Comprehensive error analysis with solution guidance
        """
        try:
            return self.error_dna.analyze_ml_error(error, ml_context)
        except Exception as analysis_error:
            self.logger.error(f"Error DNA analysis failed: {analysis_error}")
            return {
                "error_analysis_failed": True,
                "original_error": str(error),
                "analysis_error": str(analysis_error),
                "recommendations": ["Manual error investigation required"]
            }
    
    def quick_validation(self,
                        operation_type: str,
                        operation_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform quick validation focusing on critical checks only
        
        Args:
            operation_type: Type of ML operation
            operation_context: Operation context
            
        Returns:
            Quick validation result with essential safety checks
        """
        start_time = time.perf_counter()
        
        try:
            # Quick safety check
            safety_result = self.safety_validator.perform_comprehensive_safety_check(
                operation_type, operation_context, "minimal"
            )
            
            # Quick reality check for critical items
            reality_result = self.reality_checker.perform_comprehensive_reality_check(
                operation_type, operation_context
            )
            
            execution_time = (time.perf_counter() - start_time) * 1000
            
            can_proceed = (safety_result["overall_safety_status"] not in ["critical_unsafe"] and
                          reality_result["overall_status"] not in ["critical_failure"])
            
            return {
                "operation_type": operation_type,
                "validation_type": "quick",
                "can_proceed": can_proceed,
                "safety_status": safety_result["overall_safety_status"],
                "reality_status": reality_result["overall_status"],
                "execution_time_ms": execution_time,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            return {
                "operation_type": operation_type,
                "validation_type": "quick",
                "can_proceed": False,
                "error": str(e),
                "execution_time_ms": execution_time,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_ai_brain_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status of all AI Brain components"""
        try:
            return {
                "ai_brain_integration": {
                    "status": "healthy",
                    "components_active": 4,
                    "components_total": 16,
                    "completion_percentage": 25.0,
                    "integration_metrics": self.integration_metrics
                },
                "error_dna": {
                    "status": "active",
                    "patterns_loaded": len(self.error_dna.ml_error_patterns),
                    "error_history_size": len(self.error_dna.ml_training_errors),
                    "statistics": self.error_dna.get_ml_error_statistics()
                },
                "reality_checker": {
                    "status": "active",
                    "algorithm_availability": self.reality_checker.algorithm_availability,
                    "system_baseline": self.reality_checker.system_baseline,
                    "statistics": self.reality_checker.get_reality_check_statistics()
                },
                "decision_validator": {
                    "status": "active",
                    "decision_thresholds": self.decision_validator.decision_thresholds,
                    "statistics": self.decision_validator.get_decision_validation_statistics()
                },
                "safety_validator": {
                    "status": "active",
                    "safety_thresholds": self.safety_validator.safety_thresholds,
                    "safety_locks": self.safety_validator.safety_locks,
                    "statistics": self.safety_validator.get_safety_statistics()
                },
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "ai_brain_integration": {
                    "status": "error",
                    "error": str(e)
                },
                "last_updated": datetime.now().isoformat()
            }
    
    # Helper methods
    
    def _requires_decision_validation(self, operation_type: str, context: Dict[str, Any]) -> bool:
        """Check if operation requires decision validation"""
        decision_required_operations = ["train", "retrain", "feature_engineering", "model_selection"]
        return operation_type in decision_required_operations
    
    def _perform_decision_validation(self, operation_type: str, context: Dict[str, Any]):
        """Perform appropriate decision validation based on operation type"""
        if operation_type in ["train", "retrain"] and "candidate_models" in context:
            return self.decision_validator.validate_model_selection_decision(
                context["candidate_models"],
                context.get("selection_criteria", {}),
                context
            )
        elif "features" in context and "importance_scores" in context:
            return self.decision_validator.validate_feature_selection_decision(
                context["features"],
                context["importance_scores"],
                context.get("selection_threshold", 0.01),
                context
            )
        else:
            # Return default decision result
            return type('DecisionResult', (), {
                'status': 'not_applicable',
                'confidence_score': 1.0,
                'execution_time_ms': 0.0
            })()
    
    def _calculate_overall_confidence(self, reality_result, safety_result, decision_result) -> float:
        """Calculate overall confidence score from all validations"""
        scores = []
        
        # Reality check confidence (based on pass rate)
        if reality_result.get("passed_checks", 0) > 0:
            reality_confidence = reality_result["passed_checks"] / reality_result["total_checks"]
            scores.append(reality_confidence)
        
        # Safety validation confidence
        if safety_result.get("safe_checks", 0) > 0:
            safety_confidence = safety_result["safe_checks"] / safety_result["total_safety_checks"]
            scores.append(safety_confidence)
        
        # Decision validation confidence
        if decision_result and hasattr(decision_result, 'confidence_score'):
            scores.append(decision_result.confidence_score)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _determine_overall_status(self, reality_result, safety_result, decision_result, confidence_score) -> str:
        """Determine overall status from all validation results"""
        # Check for critical failures
        if (reality_result.get("overall_status") == "critical_failure" or
            safety_result.get("overall_safety_status") == "critical_unsafe"):
            return "critical_failure"
        
        # Check for rejections
        if (decision_result and hasattr(decision_result, 'status') and 
            decision_result.status == "rejected"):
            return "rejected"
        
        # Check for high risk
        if (safety_result.get("overall_safety_status") == "high_risk" or
            confidence_score < 0.6):
            return "requires_review"
        
        # Check for warnings
        if (reality_result.get("overall_status") == "warning" or
            safety_result.get("overall_safety_status") == "warning"):
            return "approved_with_warnings"
        
        return "approved"
    
    def _generate_comprehensive_recommendations(self, reality_result, safety_result, decision_result) -> List[str]:
        """Generate comprehensive recommendations from all validation results"""
        recommendations = []
        
        # Add reality check recommendations
        if reality_result.get("recommendations"):
            recommendations.extend(reality_result["recommendations"])
        
        # Add safety validation recommendations
        if safety_result.get("safety_recommendations"):
            recommendations.extend(safety_result["safety_recommendations"])
        
        # Add decision validation recommendations
        if decision_result and hasattr(decision_result, 'recommendations'):
            recommendations.extend(decision_result.recommendations)
        
        return list(set(recommendations))  # Remove duplicates
    
    def _assess_overall_risk_factors(self, reality_result, safety_result, decision_result) -> List[str]:
        """Assess overall risk factors from all validation results"""
        risk_factors = []
        
        # Reality check risks
        if reality_result.get("overall_status") in ["critical_failure", "high_risk"]:
            risk_factors.append("reality_check_failures")
        
        # Safety risks
        if safety_result.get("critical_failures", 0) > 0:
            risk_factors.append("critical_safety_failures")
        
        # Decision risks
        if decision_result and hasattr(decision_result, 'risk_factors'):
            risk_factors.extend(decision_result.risk_factors)
        
        return risk_factors
    
    def _can_proceed_safely(self, overall_status, reality_result, safety_result, decision_result) -> bool:
        """Determine if operation can proceed safely"""
        # Cannot proceed if critical failures
        if overall_status in ["critical_failure"]:
            return False
        
        # Cannot proceed if safety validation blocks
        if not safety_result.get("can_proceed_safely", True):
            return False
        
        # Cannot proceed if reality check blocks
        if not reality_result.get("can_proceed", True):
            return False
        
        return True
    
    def _requires_monitoring(self, reality_result, safety_result, decision_result) -> bool:
        """Check if operation requires continuous monitoring"""
        return (safety_result.get("requires_monitoring", False) or
                reality_result.get("requires_monitoring", False) or
                (decision_result and getattr(decision_result, 'monitoring_required', False)))
    
    def _record_validation(self, result: AIBrainValidationResult):
        """Record validation result in history and update metrics"""
        self.validation_history.append(result)
        
        # Update metrics
        self.integration_metrics["total_validations"] += 1
        
        if result.overall_status == "approved":
            self.integration_metrics["approved_operations"] += 1
        elif result.overall_status in ["critical_failure", "rejected"]:
            self.integration_metrics["rejected_operations"] += 1
        else:
            self.integration_metrics["review_required_operations"] += 1
        
        # Update average confidence
        total_confidence = (self.integration_metrics["average_confidence_score"] * 
                          (self.integration_metrics["total_validations"] - 1) + result.confidence_score)
        self.integration_metrics["average_confidence_score"] = total_confidence / self.integration_metrics["total_validations"]
        
        # Update average execution time
        total_time = (self.integration_metrics["average_execution_time_ms"] * 
                     (self.integration_metrics["total_validations"] - 1) + result.execution_time_ms)
        self.integration_metrics["average_execution_time_ms"] = total_time / self.integration_metrics["total_validations"]
        
        # Keep history limited
        if len(self.validation_history) > 1000:
            self.validation_history = self.validation_history[-1000:]


# Global AI Brain Integration instance
ml_processing_ai_brain = MLProcessingAIBrain("ml-processing")


def get_ml_ai_brain() -> MLProcessingAIBrain:
    """Get the global ML-Processing AI Brain instance"""
    return ml_processing_ai_brain


def comprehensive_ml_validation(operation_type: str,
                               operation_context: Dict[str, Any],
                               validation_level: str = "standard") -> AIBrainValidationResult:
    """Convenience function for comprehensive ML validation"""
    return ml_processing_ai_brain.comprehensive_validation(
        operation_type, operation_context, validation_level
    )


def quick_ml_validation(operation_type: str,
                       operation_context: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function for quick ML validation"""
    return ml_processing_ai_brain.quick_validation(operation_type, operation_context)