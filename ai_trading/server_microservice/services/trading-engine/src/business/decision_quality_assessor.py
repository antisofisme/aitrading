"""
Decision Quality Assessment System for Trading Engine

This module implements comprehensive decision quality assessment metrics and performance tracking
according to AI Brain methodology. It integrates all decision validation components to provide
holistic quality scores and continuous performance monitoring.

Key Features:
- Multi-dimensional quality scoring
- Performance attribution analysis
- Quality trend analysis
- Benchmark comparison
- AI Brain compliance tracking
- Real-time quality monitoring
- Quality degradation detection
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import asyncio
import logging
import numpy as np
from collections import defaultdict, deque
import json
import statistics

logger = logging.getLogger(__name__)


class QualityDimension(Enum):
    """Quality assessment dimensions"""
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    TIMELINESS = "timeliness"
    RISK_AWARENESS = "risk_awareness"
    CONFIDENCE_CALIBRATION = "confidence_calibration"
    IMPACT_ALIGNMENT = "impact_alignment"
    PATTERN_ADHERENCE = "pattern_adherence"
    COMPLIANCE = "compliance"
    PERFORMANCE = "performance"
    ADAPTABILITY = "adaptability"


class QualityGrade(Enum):
    """Quality assessment grades"""
    EXCELLENT = "excellent"  # 90-100%
    GOOD = "good"           # 80-89%
    SATISFACTORY = "satisfactory"  # 70-79%
    NEEDS_IMPROVEMENT = "needs_improvement"  # 60-69%
    POOR = "poor"           # Below 60%


@dataclass
class QualityMetric:
    """Individual quality metric"""
    dimension: QualityDimension
    score: float  # 0-100
    weight: float
    details: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    trend: str = "stable"  # improving, stable, declining


@dataclass
class QualityAssessment:
    """Comprehensive quality assessment"""
    decision_id: str
    timestamp: datetime
    overall_score: float
    grade: QualityGrade
    dimensions: Dict[QualityDimension, QualityMetric]
    performance_attribution: Dict[str, float]
    benchmark_comparison: Dict[str, float]
    recommendations: List[str]
    risk_flags: List[str]
    compliance_status: Dict[str, bool]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityTrend:
    """Quality trend analysis"""
    period: str
    start_date: datetime
    end_date: datetime
    trend_direction: str  # improving, stable, declining
    trend_strength: float  # 0-1
    quality_progression: List[Tuple[datetime, float]]
    dimension_trends: Dict[QualityDimension, str]
    performance_correlation: float
    recommendations: List[str]


@dataclass
class PerformanceMetrics:
    """Performance tracking metrics"""
    total_decisions: int
    successful_decisions: int
    failed_decisions: int
    average_quality_score: float
    quality_consistency: float
    improvement_rate: float
    compliance_rate: float
    risk_adjusted_performance: float
    benchmark_outperformance: float
    quality_distribution: Dict[QualityGrade, int]


class DecisionQualityAssessor:
    """Comprehensive decision quality assessment and performance tracking system"""
    
    def __init__(self):
        self.quality_history: Dict[str, QualityAssessment] = {}
        self.performance_cache: Dict[str, Any] = {}
        self.quality_weights = self._initialize_quality_weights()
        self.benchmarks = self._initialize_benchmarks()
        self.quality_trends = deque(maxlen=1000)
        self.alert_thresholds = self._initialize_thresholds()
        
        # Integration with other components
        self.audit_system = None
        self.impact_assessor = None
        self.confidence_scorer = None
        self.pattern_recognizer = None
        self.decision_logger = None
        
    def _initialize_quality_weights(self) -> Dict[QualityDimension, float]:
        """Initialize quality dimension weights"""
        return {
            QualityDimension.ACCURACY: 0.15,
            QualityDimension.CONSISTENCY: 0.12,
            QualityDimension.TIMELINESS: 0.08,
            QualityDimension.RISK_AWARENESS: 0.15,
            QualityDimension.CONFIDENCE_CALIBRATION: 0.12,
            QualityDimension.IMPACT_ALIGNMENT: 0.13,
            QualityDimension.PATTERN_ADHERENCE: 0.08,
            QualityDimension.COMPLIANCE: 0.10,
            QualityDimension.PERFORMANCE: 0.15,
            QualityDimension.ADAPTABILITY: 0.07
        }
    
    def _initialize_benchmarks(self) -> Dict[str, float]:
        """Initialize quality benchmarks"""
        return {
            "ai_brain_threshold": 85.0,
            "excellent_threshold": 90.0,
            "good_threshold": 80.0,
            "satisfactory_threshold": 70.0,
            "minimum_acceptable": 60.0,
            "industry_average": 72.0,
            "top_quartile": 82.0,
            "best_practice": 88.0
        }
    
    def _initialize_thresholds(self) -> Dict[str, float]:
        """Initialize alert thresholds"""
        return {
            "quality_decline_threshold": -5.0,  # Percentage points
            "consistency_threshold": 0.15,  # Standard deviation
            "compliance_threshold": 0.95,  # Minimum compliance rate
            "performance_correlation_threshold": 0.7,
            "risk_flag_threshold": 3  # Number of risk flags
        }
    
    async def integrate_components(self, components: Dict[str, Any]):
        """Integrate with other decision validation components"""
        try:
            self.audit_system = components.get('audit_system')
            self.impact_assessor = components.get('impact_assessor')
            self.confidence_scorer = components.get('confidence_scorer')
            self.pattern_recognizer = components.get('pattern_recognizer')
            self.decision_logger = components.get('decision_logger')
            
            logger.info("Successfully integrated with decision validation components")
            
        except Exception as e:
            logger.error(f"Error integrating components: {str(e)}")
            # Continue with standalone operation
    
    async def assess_decision_quality(
        self,
        decision_id: str,
        decision_data: Dict[str, Any],
        execution_results: Optional[Dict[str, Any]] = None,
        market_context: Optional[Dict[str, Any]] = None
    ) -> QualityAssessment:
        """Create comprehensive quality assessment for a trading decision"""
        try:
            logger.info(f"Starting quality assessment for decision: {decision_id}")
            
            # Collect data from integrated components
            audit_data = await self._get_audit_data(decision_id)
            impact_data = await self._get_impact_data(decision_id)
            confidence_data = await self._get_confidence_data(decision_id)
            pattern_data = await self._get_pattern_data(decision_id)
            
            # Assess each quality dimension
            dimensions = {}
            
            dimensions[QualityDimension.ACCURACY] = await self._assess_accuracy(
                decision_data, execution_results, impact_data
            )
            
            dimensions[QualityDimension.CONSISTENCY] = await self._assess_consistency(
                decision_data, audit_data
            )
            
            dimensions[QualityDimension.TIMELINESS] = await self._assess_timeliness(
                decision_data, audit_data
            )
            
            dimensions[QualityDimension.RISK_AWARENESS] = await self._assess_risk_awareness(
                decision_data, impact_data, market_context
            )
            
            dimensions[QualityDimension.CONFIDENCE_CALIBRATION] = await self._assess_confidence_calibration(
                confidence_data, execution_results
            )
            
            dimensions[QualityDimension.IMPACT_ALIGNMENT] = await self._assess_impact_alignment(
                decision_data, impact_data
            )
            
            dimensions[QualityDimension.PATTERN_ADHERENCE] = await self._assess_pattern_adherence(
                decision_data, pattern_data
            )
            
            dimensions[QualityDimension.COMPLIANCE] = await self._assess_compliance(
                decision_data, audit_data
            )
            
            dimensions[QualityDimension.PERFORMANCE] = await self._assess_performance(
                decision_data, execution_results, impact_data
            )
            
            dimensions[QualityDimension.ADAPTABILITY] = await self._assess_adaptability(
                decision_data, market_context, pattern_data
            )
            
            # Calculate overall quality score
            overall_score = self._calculate_overall_score(dimensions)
            grade = self._determine_quality_grade(overall_score)
            
            # Generate performance attribution
            performance_attribution = self._calculate_performance_attribution(dimensions)
            
            # Benchmark comparison
            benchmark_comparison = self._compare_to_benchmarks(overall_score)
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(dimensions, decision_data)
            
            # Identify risk flags
            risk_flags = self._identify_risk_flags(dimensions, decision_data)
            
            # Check compliance status
            compliance_status = self._check_compliance_status(dimensions)
            
            # Create quality assessment
            assessment = QualityAssessment(
                decision_id=decision_id,
                timestamp=datetime.utcnow(),
                overall_score=overall_score,
                grade=grade,
                dimensions=dimensions,
                performance_attribution=performance_attribution,
                benchmark_comparison=benchmark_comparison,
                recommendations=recommendations,
                risk_flags=risk_flags,
                compliance_status=compliance_status,
                metadata={
                    "decision_type": decision_data.get("type", "unknown"),
                    "strategy": decision_data.get("strategy", "unknown"),
                    "market_conditions": market_context.get("conditions", "unknown") if market_context else "unknown"
                }
            )
            
            # Store assessment
            self.quality_history[decision_id] = assessment
            
            # Update performance tracking
            await self._update_performance_tracking(assessment)
            
            # Check for alerts
            await self._check_quality_alerts(assessment)
            
            logger.info(f"Completed quality assessment for decision: {decision_id} - Score: {overall_score:.2f}")
            
            return assessment
            
        except Exception as e:
            logger.error(f"Error in quality assessment for decision {decision_id}: {str(e)}")
            raise
    
    async def _get_audit_data(self, decision_id: str) -> Dict[str, Any]:
        """Get audit data from audit system"""
        try:
            if self.audit_system:
                audit_record = await self.audit_system.get_audit_record(decision_id)
                if audit_record:
                    return {
                        "creation_time": audit_record.creation_time,
                        "validation_time": audit_record.validation_time,
                        "execution_time": audit_record.execution_time,
                        "completion_time": audit_record.completion_time,
                        "validation_results": audit_record.validation_results,
                        "execution_results": audit_record.execution_results,
                        "rollback_actions": audit_record.rollback_actions
                    }
            return {}
        except Exception as e:
            logger.warning(f"Could not retrieve audit data for {decision_id}: {str(e)}")
            return {}
    
    async def _get_impact_data(self, decision_id: str) -> Dict[str, Any]:
        """Get impact data from impact assessor"""
        try:
            if self.impact_assessor:
                impact_assessment = await self.impact_assessor.get_impact_assessment(decision_id)
                if impact_assessment:
                    return {
                        "immediate_impact": impact_assessment.immediate_impact,
                        "short_term_impact": impact_assessment.short_term_impact,
                        "medium_term_impact": impact_assessment.medium_term_impact,
                        "long_term_impact": impact_assessment.long_term_impact,
                        "risk_metrics": impact_assessment.risk_metrics,
                        "performance_attribution": impact_assessment.performance_attribution
                    }
            return {}
        except Exception as e:
            logger.warning(f"Could not retrieve impact data for {decision_id}: {str(e)}")
            return {}
    
    async def _get_confidence_data(self, decision_id: str) -> Dict[str, Any]:
        """Get confidence data from confidence scorer"""
        try:
            if self.confidence_scorer:
                # Retrieve confidence score history
                confidence_history = await self.confidence_scorer.get_confidence_history(decision_id)
                if confidence_history:
                    return {
                        "confidence_score": confidence_history[-1].overall_confidence,
                        "confidence_factors": confidence_history[-1].factors,
                        "calibration_metrics": confidence_history[-1].calibration_metrics,
                        "confidence_trend": confidence_history
                    }
            return {}
        except Exception as e:
            logger.warning(f"Could not retrieve confidence data for {decision_id}: {str(e)}")
            return {}
    
    async def _get_pattern_data(self, decision_id: str) -> Dict[str, Any]:
        """Get pattern data from pattern recognizer"""
        try:
            if self.pattern_recognizer:
                patterns = await self.pattern_recognizer.get_decision_patterns(decision_id)
                if patterns:
                    return {
                        "identified_patterns": patterns.patterns,
                        "pattern_confidence": patterns.confidence,
                        "pattern_recommendations": patterns.recommendations,
                        "historical_performance": patterns.historical_performance
                    }
            return {}
        except Exception as e:
            logger.warning(f"Could not retrieve pattern data for {decision_id}: {str(e)}")
            return {}
    
    async def _assess_accuracy(
        self,
        decision_data: Dict[str, Any],
        execution_results: Optional[Dict[str, Any]],
        impact_data: Dict[str, Any]
    ) -> QualityMetric:
        """Assess decision accuracy"""
        try:
            score = 75.0  # Base score
            details = {}
            
            # Prediction accuracy
            if execution_results and "predicted_outcome" in decision_data:
                predicted = decision_data["predicted_outcome"]
                actual = execution_results.get("actual_outcome")
                
                if actual is not None:
                    accuracy = self._calculate_prediction_accuracy(predicted, actual)
                    score += (accuracy - 0.5) * 50  # Scale to 0-100
                    details["prediction_accuracy"] = accuracy
            
            # Impact alignment
            if impact_data and "immediate_impact" in impact_data:
                expected_impact = decision_data.get("expected_impact", 0)
                actual_impact = impact_data["immediate_impact"].get("total_impact", 0)
                
                if expected_impact != 0:
                    impact_accuracy = 1.0 - min(abs(actual_impact - expected_impact) / abs(expected_impact), 1.0)
                    score = (score + impact_accuracy * 100) / 2
                    details["impact_accuracy"] = impact_accuracy
            
            score = max(0, min(100, score))
            
            return QualityMetric(
                dimension=QualityDimension.ACCURACY,
                score=score,
                weight=self.quality_weights[QualityDimension.ACCURACY],
                details=details,
                confidence=0.8
            )
            
        except Exception as e:
            logger.error(f"Error assessing accuracy: {str(e)}")
            return QualityMetric(
                dimension=QualityDimension.ACCURACY,
                score=50.0,
                weight=self.quality_weights[QualityDimension.ACCURACY],
                confidence=0.3
            )
    
    def _calculate_prediction_accuracy(self, predicted: Any, actual: Any) -> float:
        """Calculate prediction accuracy"""
        try:
            if isinstance(predicted, (int, float)) and isinstance(actual, (int, float)):
                # Numerical prediction
                error = abs(predicted - actual)
                max_value = max(abs(predicted), abs(actual), 1.0)
                accuracy = 1.0 - (error / max_value)
                return max(0.0, min(1.0, accuracy))
            
            elif isinstance(predicted, str) and isinstance(actual, str):
                # Categorical prediction
                return 1.0 if predicted.lower() == actual.lower() else 0.0
            
            elif isinstance(predicted, bool) and isinstance(actual, bool):
                # Boolean prediction
                return 1.0 if predicted == actual else 0.0
            
            else:
                # Default comparison
                return 1.0 if predicted == actual else 0.0
                
        except Exception:
            return 0.5  # Default moderate accuracy
    
    async def _assess_consistency(
        self,
        decision_data: Dict[str, Any],
        audit_data: Dict[str, Any]
    ) -> QualityMetric:
        """Assess decision consistency"""
        try:
            score = 80.0  # Base score
            details = {}
            
            # Check for consistent decision patterns
            decision_type = decision_data.get("type", "unknown")
            strategy = decision_data.get("strategy", "unknown")
            
            # Analyze recent similar decisions
            similar_decisions = self._get_similar_recent_decisions(decision_type, strategy)
            
            if similar_decisions:
                consistency_score = self._calculate_consistency_score(decision_data, similar_decisions)
                score = consistency_score * 100
                details["pattern_consistency"] = consistency_score
                details["similar_decisions_count"] = len(similar_decisions)
            
            # Validation consistency
            if audit_data and "validation_results" in audit_data:
                validation_results = audit_data["validation_results"]
                validation_consistency = self._assess_validation_consistency(validation_results)
                score = (score + validation_consistency * 100) / 2
                details["validation_consistency"] = validation_consistency
            
            score = max(0, min(100, score))
            
            return QualityMetric(
                dimension=QualityDimension.CONSISTENCY,
                score=score,
                weight=self.quality_weights[QualityDimension.CONSISTENCY],
                details=details,
                confidence=0.7
            )
            
        except Exception as e:
            logger.error(f"Error assessing consistency: {str(e)}")
            return QualityMetric(
                dimension=QualityDimension.CONSISTENCY,
                score=70.0,
                weight=self.quality_weights[QualityDimension.CONSISTENCY],
                confidence=0.3
            )
    
    def _get_similar_recent_decisions(self, decision_type: str, strategy: str, limit: int = 10) -> List[QualityAssessment]:
        """Get similar recent decisions for consistency analysis"""
        similar_decisions = []
        
        for assessment in list(self.quality_history.values())[-100:]:  # Last 100 decisions
            if (assessment.metadata.get("decision_type") == decision_type and 
                assessment.metadata.get("strategy") == strategy):
                similar_decisions.append(assessment)
                
                if len(similar_decisions) >= limit:
                    break
        
        return similar_decisions
    
    def _calculate_consistency_score(
        self,
        current_decision: Dict[str, Any],
        similar_decisions: List[QualityAssessment]
    ) -> float:
        """Calculate consistency score based on similar decisions"""
        if not similar_decisions:
            return 0.8  # Default moderate consistency
        
        # Compare key decision parameters
        consistency_factors = []
        
        for assessment in similar_decisions:
            # Compare confidence levels
            current_confidence = current_decision.get("confidence", 0.5)
            historical_confidence = assessment.dimensions.get(QualityDimension.CONFIDENCE_CALIBRATION)
            if historical_confidence:
                confidence_similarity = 1.0 - abs(current_confidence - historical_confidence.score / 100)
                consistency_factors.append(confidence_similarity)
            
            # Compare risk levels
            current_risk = current_decision.get("risk_level", 0.5)
            if QualityDimension.RISK_AWARENESS in assessment.dimensions:
                risk_metric = assessment.dimensions[QualityDimension.RISK_AWARENESS]
                historical_risk = risk_metric.details.get("risk_level", 0.5)
                risk_similarity = 1.0 - abs(current_risk - historical_risk)
                consistency_factors.append(risk_similarity)
        
        if consistency_factors:
            return statistics.mean(consistency_factors)
        
        return 0.8  # Default consistency score
    
    def _assess_validation_consistency(self, validation_results: Dict[str, Any]) -> float:
        """Assess consistency of validation results"""
        if not validation_results:
            return 0.7
        
        # Check for consistent validation outcomes
        consistency_score = 0.8
        
        # Analyze validation step consistency
        validation_steps = validation_results.get("steps", [])
        if validation_steps:
            step_scores = [step.get("score", 0.5) for step in validation_steps]
            if step_scores:
                consistency_score = 1.0 - statistics.stdev(step_scores) if len(step_scores) > 1 else 1.0
        
        return max(0.0, min(1.0, consistency_score))
    
    async def _assess_timeliness(
        self,
        decision_data: Dict[str, Any],
        audit_data: Dict[str, Any]
    ) -> QualityMetric:
        """Assess decision timeliness"""
        try:
            score = 85.0  # Base score
            details = {}
            
            if audit_data:
                creation_time = audit_data.get("creation_time")
                validation_time = audit_data.get("validation_time")
                execution_time = audit_data.get("execution_time")
                
                if creation_time and validation_time:
                    validation_delay = (validation_time - creation_time).total_seconds()
                    expected_validation_time = decision_data.get("expected_validation_time", 30.0)  # seconds
                    
                    if validation_delay <= expected_validation_time:
                        validation_score = 100.0
                    else:
                        validation_score = max(0, 100 - (validation_delay - expected_validation_time) * 2)
                    
                    score = (score + validation_score) / 2
                    details["validation_delay"] = validation_delay
                    details["validation_score"] = validation_score
                
                if validation_time and execution_time:
                    execution_delay = (execution_time - validation_time).total_seconds()
                    expected_execution_time = decision_data.get("expected_execution_time", 60.0)  # seconds
                    
                    if execution_delay <= expected_execution_time:
                        execution_score = 100.0
                    else:
                        execution_score = max(0, 100 - (execution_delay - expected_execution_time) * 1)
                    
                    score = (score + execution_score) / 2
                    details["execution_delay"] = execution_delay
                    details["execution_score"] = execution_score
            
            score = max(0, min(100, score))
            
            return QualityMetric(
                dimension=QualityDimension.TIMELINESS,
                score=score,
                weight=self.quality_weights[QualityDimension.TIMELINESS],
                details=details,
                confidence=0.9
            )
            
        except Exception as e:
            logger.error(f"Error assessing timeliness: {str(e)}")
            return QualityMetric(
                dimension=QualityDimension.TIMELINESS,
                score=75.0,
                weight=self.quality_weights[QualityDimension.TIMELINESS],
                confidence=0.3
            )
    
    async def _assess_risk_awareness(
        self,
        decision_data: Dict[str, Any],
        impact_data: Dict[str, Any],
        market_context: Optional[Dict[str, Any]]
    ) -> QualityMetric:
        """Assess decision risk awareness"""
        try:
            score = 70.0  # Base score
            details = {}
            
            # Risk identification
            identified_risks = decision_data.get("identified_risks", [])
            risk_identification_score = min(100, len(identified_risks) * 20)
            score += (risk_identification_score - 50) * 0.3
            details["identified_risks_count"] = len(identified_risks)
            
            # Risk quantification
            if "risk_metrics" in decision_data:
                risk_metrics = decision_data["risk_metrics"]
                quantification_score = self._assess_risk_quantification(risk_metrics)
                score = (score + quantification_score * 100) / 2
                details["risk_quantification"] = quantification_score
            
            # Risk mitigation
            mitigation_strategies = decision_data.get("risk_mitigation", [])
            mitigation_score = min(100, len(mitigation_strategies) * 25)
            score = (score + mitigation_score) / 2
            details["mitigation_strategies_count"] = len(mitigation_strategies)
            
            # Market risk awareness
            if market_context:
                market_risk_score = self._assess_market_risk_awareness(decision_data, market_context)
                score = (score + market_risk_score * 100) / 2
                details["market_risk_awareness"] = market_risk_score
            
            # Impact-based risk assessment
            if impact_data and "risk_metrics" in impact_data:
                actual_risk_metrics = impact_data["risk_metrics"]
                risk_prediction_accuracy = self._assess_risk_prediction_accuracy(
                    decision_data.get("risk_metrics", {}),
                    actual_risk_metrics
                )
                score = (score + risk_prediction_accuracy * 100) / 2
                details["risk_prediction_accuracy"] = risk_prediction_accuracy
            
            score = max(0, min(100, score))
            
            return QualityMetric(
                dimension=QualityDimension.RISK_AWARENESS,
                score=score,
                weight=self.quality_weights[QualityDimension.RISK_AWARENESS],
                details=details,
                confidence=0.8
            )
            
        except Exception as e:
            logger.error(f"Error assessing risk awareness: {str(e)}")
            return QualityMetric(
                dimension=QualityDimension.RISK_AWARENESS,
                score=60.0,
                weight=self.quality_weights[QualityDimension.RISK_AWARENESS],
                confidence=0.3
            )
    
    def _assess_risk_quantification(self, risk_metrics: Dict[str, Any]) -> float:
        """Assess quality of risk quantification"""
        score = 0.0
        
        # Check for essential risk metrics
        essential_metrics = ["var", "expected_shortfall", "max_drawdown", "volatility"]
        present_metrics = sum(1 for metric in essential_metrics if metric in risk_metrics)
        score += (present_metrics / len(essential_metrics)) * 0.4
        
        # Check for risk metric reasonableness
        if "var" in risk_metrics and "volatility" in risk_metrics:
            var = risk_metrics["var"]
            volatility = risk_metrics["volatility"]
            
            # VaR should be reasonable compared to volatility
            if 0 < var <= volatility * 3:  # Reasonable range
                score += 0.3
        
        # Check for confidence intervals
        if any("confidence" in str(key).lower() for key in risk_metrics.keys()):
            score += 0.3
        
        return max(0.0, min(1.0, score))
    
    def _assess_market_risk_awareness(self, decision_data: Dict[str, Any], market_context: Dict[str, Any]) -> float:
        """Assess awareness of market-specific risks"""
        score = 0.5  # Base score
        
        market_conditions = market_context.get("conditions", {})
        decision_considerations = decision_data.get("market_considerations", {})
        
        # Check if volatile market conditions are considered
        if market_conditions.get("volatility", "normal") == "high":
            if "volatility" in decision_considerations or "high_volatility" in str(decision_considerations).lower():
                score += 0.3
        
        # Check if trend changes are considered
        if market_conditions.get("trend", "stable") != "stable":
            if "trend" in decision_considerations or "market_direction" in decision_considerations:
                score += 0.2
        
        return max(0.0, min(1.0, score))
    
    def _assess_risk_prediction_accuracy(self, predicted_risk: Dict[str, Any], actual_risk: Dict[str, Any]) -> float:
        """Assess accuracy of risk predictions"""
        if not predicted_risk or not actual_risk:
            return 0.5
        
        accuracy_scores = []
        
        for metric in ["var", "expected_shortfall", "max_drawdown", "volatility"]:
            if metric in predicted_risk and metric in actual_risk:
                predicted = predicted_risk[metric]
                actual = actual_risk[metric]
                
                if predicted > 0 and actual > 0:
                    accuracy = 1.0 - min(abs(predicted - actual) / max(predicted, actual), 1.0)
                    accuracy_scores.append(accuracy)
        
        if accuracy_scores:
            return statistics.mean(accuracy_scores)
        
        return 0.5
    
    async def _assess_confidence_calibration(
        self,
        confidence_data: Dict[str, Any],
        execution_results: Optional[Dict[str, Any]]
    ) -> QualityMetric:
        """Assess confidence calibration quality"""
        try:
            score = 75.0  # Base score
            details = {}
            
            if confidence_data:
                confidence_score = confidence_data.get("confidence_score", 0.5)
                calibration_metrics = confidence_data.get("calibration_metrics", {})
                
                # Calibration accuracy
                if calibration_metrics and execution_results:
                    calibration_accuracy = self._calculate_calibration_accuracy(
                        confidence_score,
                        execution_results,
                        calibration_metrics
                    )
                    score = calibration_accuracy * 100
                    details["calibration_accuracy"] = calibration_accuracy
                
                # Confidence appropriateness
                confidence_appropriateness = self._assess_confidence_appropriateness(confidence_score)
                score = (score + confidence_appropriateness * 100) / 2
                details["confidence_appropriateness"] = confidence_appropriateness
                
                # Confidence trend analysis
                confidence_trend = confidence_data.get("confidence_trend", [])
                if confidence_trend:
                    trend_consistency = self._assess_confidence_trend_consistency(confidence_trend)
                    score = (score + trend_consistency * 100) / 2
                    details["trend_consistency"] = trend_consistency
            
            score = max(0, min(100, score))
            
            return QualityMetric(
                dimension=QualityDimension.CONFIDENCE_CALIBRATION,
                score=score,
                weight=self.quality_weights[QualityDimension.CONFIDENCE_CALIBRATION],
                details=details,
                confidence=0.8
            )
            
        except Exception as e:
            logger.error(f"Error assessing confidence calibration: {str(e)}")
            return QualityMetric(
                dimension=QualityDimension.CONFIDENCE_CALIBRATION,
                score=70.0,
                weight=self.quality_weights[QualityDimension.CONFIDENCE_CALIBRATION],
                confidence=0.3
            )
    
    def _calculate_calibration_accuracy(
        self,
        confidence_score: float,
        execution_results: Dict[str, Any],
        calibration_metrics: Dict[str, Any]
    ) -> float:
        """Calculate confidence calibration accuracy"""
        try:
            # Determine if decision was successful
            success = execution_results.get("success", False)
            
            # Expected success rate based on confidence
            expected_success_rate = confidence_score
            
            # Compare with actual outcome
            actual_success = 1.0 if success else 0.0
            
            # Calculate calibration error
            calibration_error = abs(expected_success_rate - actual_success)
            
            # Convert to accuracy (lower error = higher accuracy)
            accuracy = 1.0 - calibration_error
            
            return max(0.0, min(1.0, accuracy))
            
        except Exception:
            return 0.7  # Default moderate accuracy
    
    def _assess_confidence_appropriateness(self, confidence_score: float) -> float:
        """Assess if confidence level is appropriate"""
        # Confidence should be neither too low nor too high for most decisions
        if 0.3 <= confidence_score <= 0.8:
            return 1.0  # Appropriate confidence range
        elif 0.2 <= confidence_score <= 0.9:
            return 0.8  # Acceptable range
        elif 0.1 <= confidence_score <= 0.95:
            return 0.6  # Marginal range
        else:
            return 0.3  # Inappropriate confidence level
    
    def _assess_confidence_trend_consistency(self, confidence_trend: List[Any]) -> float:
        """Assess consistency of confidence trends"""
        if len(confidence_trend) < 2:
            return 0.7  # Default for insufficient data
        
        # Extract confidence values
        confidence_values = []
        for entry in confidence_trend[-10:]:  # Last 10 entries
            if hasattr(entry, 'overall_confidence'):
                confidence_values.append(entry.overall_confidence)
            elif isinstance(entry, dict) and 'confidence' in entry:
                confidence_values.append(entry['confidence'])
        
        if len(confidence_values) < 2:
            return 0.7
        
        # Calculate consistency (lower standard deviation = higher consistency)
        try:
            std_dev = statistics.stdev(confidence_values)
            consistency = 1.0 - min(std_dev, 1.0)  # Cap at 1.0
            return max(0.0, min(1.0, consistency))
        except:
            return 0.7
    
    async def _assess_impact_alignment(
        self,
        decision_data: Dict[str, Any],
        impact_data: Dict[str, Any]
    ) -> QualityMetric:
        """Assess alignment between expected and actual impact"""
        try:
            score = 75.0  # Base score
            details = {}
            
            if impact_data:
                # Compare expected vs actual immediate impact
                expected_impact = decision_data.get("expected_impact", {})
                immediate_impact = impact_data.get("immediate_impact", {})
                
                if expected_impact and immediate_impact:
                    immediate_alignment = self._calculate_impact_alignment(expected_impact, immediate_impact)
                    score = immediate_alignment * 100
                    details["immediate_alignment"] = immediate_alignment
                
                # Check impact attribution accuracy
                if "performance_attribution" in impact_data:
                    attribution_data = impact_data["performance_attribution"]
                    attribution_quality = self._assess_attribution_quality(attribution_data)
                    score = (score + attribution_quality * 100) / 2
                    details["attribution_quality"] = attribution_quality
                
                # Assess risk-adjusted impact
                risk_metrics = impact_data.get("risk_metrics", {})
                if risk_metrics:
                    risk_adjustment_quality = self._assess_risk_adjustment_quality(risk_metrics)
                    score = (score + risk_adjustment_quality * 100) / 2
                    details["risk_adjustment_quality"] = risk_adjustment_quality
            
            score = max(0, min(100, score))
            
            return QualityMetric(
                dimension=QualityDimension.IMPACT_ALIGNMENT,
                score=score,
                weight=self.quality_weights[QualityDimension.IMPACT_ALIGNMENT],
                details=details,
                confidence=0.8
            )
            
        except Exception as e:
            logger.error(f"Error assessing impact alignment: {str(e)}")
            return QualityMetric(
                dimension=QualityDimension.IMPACT_ALIGNMENT,
                score=70.0,
                weight=self.quality_weights[QualityDimension.IMPACT_ALIGNMENT],
                confidence=0.3
            )
    
    def _calculate_impact_alignment(
        self,
        expected_impact: Dict[str, Any],
        actual_impact: Dict[str, Any]
    ) -> float:
        """Calculate alignment between expected and actual impact"""
        alignment_scores = []
        
        # Compare numerical impacts
        for metric in ["return", "profit", "loss", "total_impact"]:
            if metric in expected_impact and metric in actual_impact:
                expected = expected_impact[metric]
                actual = actual_impact[metric]
                
                if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
                    if expected != 0:
                        alignment = 1.0 - min(abs(expected - actual) / abs(expected), 1.0)
                        alignment_scores.append(alignment)
                    elif actual == 0:
                        alignment_scores.append(1.0)  # Both zero = perfect alignment
        
        if alignment_scores:
            return statistics.mean(alignment_scores)
        
        return 0.7  # Default moderate alignment
    
    def _assess_attribution_quality(self, attribution_data: Dict[str, Any]) -> float:
        """Assess quality of performance attribution"""
        score = 0.5  # Base score
        
        # Check for comprehensive attribution
        attribution_categories = ["strategy", "timing", "selection", "interaction"]
        present_categories = sum(1 for cat in attribution_categories if cat in attribution_data)
        score += (present_categories / len(attribution_categories)) * 0.3
        
        # Check attribution completeness (should sum to total)
        total_attribution = sum(v for v in attribution_data.values() if isinstance(v, (int, float)))
        total_impact = attribution_data.get("total", total_attribution)
        
        if total_impact != 0:
            completeness = 1.0 - min(abs(total_attribution - total_impact) / abs(total_impact), 1.0)
            score += completeness * 0.2
        
        return max(0.0, min(1.0, score))
    
    def _assess_risk_adjustment_quality(self, risk_metrics: Dict[str, Any]) -> float:
        """Assess quality of risk adjustments"""
        score = 0.5  # Base score
        
        # Check for essential risk-adjusted metrics
        risk_adjusted_metrics = ["sharpe_ratio", "sortino_ratio", "calmar_ratio"]
        present_metrics = sum(1 for metric in risk_adjusted_metrics if metric in risk_metrics)
        score += (present_metrics / len(risk_adjusted_metrics)) * 0.3
        
        # Check metric reasonableness
        if "sharpe_ratio" in risk_metrics:
            sharpe = risk_metrics["sharpe_ratio"]
            if -2.0 <= sharpe <= 5.0:  # Reasonable range
                score += 0.2
        
        return max(0.0, min(1.0, score))
    
    async def _assess_pattern_adherence(
        self,
        decision_data: Dict[str, Any],
        pattern_data: Dict[str, Any]
    ) -> QualityMetric:
        """Assess adherence to identified successful patterns"""
        try:
            score = 80.0  # Base score
            details = {}
            
            if pattern_data:
                identified_patterns = pattern_data.get("identified_patterns", [])
                pattern_confidence = pattern_data.get("pattern_confidence", 0.5)
                
                # Pattern matching score
                if identified_patterns:
                    matching_score = self._calculate_pattern_matching_score(decision_data, identified_patterns)
                    score = matching_score * 100
                    details["pattern_matching_score"] = matching_score
                    details["patterns_count"] = len(identified_patterns)
                
                # Historical performance alignment
                historical_performance = pattern_data.get("historical_performance", {})
                if historical_performance:
                    performance_alignment = self._assess_historical_performance_alignment(
                        decision_data, historical_performance
                    )
                    score = (score + performance_alignment * 100) / 2
                    details["historical_performance_alignment"] = performance_alignment
                
                # Pattern recommendations adherence
                pattern_recommendations = pattern_data.get("pattern_recommendations", [])
                if pattern_recommendations:
                    recommendation_adherence = self._assess_recommendation_adherence(
                        decision_data, pattern_recommendations
                    )
                    score = (score + recommendation_adherence * 100) / 2
                    details["recommendation_adherence"] = recommendation_adherence
                
                # Adjust score based on pattern confidence
                score = score * (0.5 + pattern_confidence * 0.5)
                details["pattern_confidence"] = pattern_confidence
            
            score = max(0, min(100, score))
            
            return QualityMetric(
                dimension=QualityDimension.PATTERN_ADHERENCE,
                score=score,
                weight=self.quality_weights[QualityDimension.PATTERN_ADHERENCE],
                details=details,
                confidence=0.7
            )
            
        except Exception as e:
            logger.error(f"Error assessing pattern adherence: {str(e)}")
            return QualityMetric(
                dimension=QualityDimension.PATTERN_ADHERENCE,
                score=75.0,
                weight=self.quality_weights[QualityDimension.PATTERN_ADHERENCE],
                confidence=0.3
            )
    
    def _calculate_pattern_matching_score(
        self,
        decision_data: Dict[str, Any],
        identified_patterns: List[Any]
    ) -> float:
        """Calculate how well decision matches identified patterns"""
        if not identified_patterns:
            return 0.7  # Default moderate score
        
        matching_scores = []
        
        for pattern in identified_patterns:
            pattern_score = 0.0
            pattern_features = getattr(pattern, 'features', {}) if hasattr(pattern, 'features') else {}
            
            # Compare decision features with pattern features
            for feature, expected_value in pattern_features.items():
                if feature in decision_data:
                    actual_value = decision_data[feature]
                    
                    if isinstance(expected_value, (int, float)) and isinstance(actual_value, (int, float)):
                        # Numerical comparison
                        if expected_value != 0:
                            similarity = 1.0 - min(abs(expected_value - actual_value) / abs(expected_value), 1.0)
                        else:
                            similarity = 1.0 if actual_value == 0 else 0.0
                        pattern_score += similarity
                    elif expected_value == actual_value:
                        # Exact match
                        pattern_score += 1.0
                    else:
                        # No match
                        pattern_score += 0.0
            
            if pattern_features:
                matching_scores.append(pattern_score / len(pattern_features))
        
        if matching_scores:
            return statistics.mean(matching_scores)
        
        return 0.7  # Default score
    
    def _assess_historical_performance_alignment(
        self,
        decision_data: Dict[str, Any],
        historical_performance: Dict[str, Any]
    ) -> float:
        """Assess alignment with historical performance patterns"""
        score = 0.5  # Base score
        
        # Check if decision characteristics align with high-performing patterns
        decision_type = decision_data.get("type", "unknown")
        strategy = decision_data.get("strategy", "unknown")
        
        # Look for similar historical patterns
        type_performance = historical_performance.get(decision_type, {})
        strategy_performance = historical_performance.get(strategy, {})
        
        if type_performance:
            avg_performance = type_performance.get("average_performance", 0.5)
            score += (avg_performance - 0.5) * 0.3
        
        if strategy_performance:
            avg_performance = strategy_performance.get("average_performance", 0.5)
            score += (avg_performance - 0.5) * 0.2
        
        return max(0.0, min(1.0, score))
    
    def _assess_recommendation_adherence(
        self,
        decision_data: Dict[str, Any],
        pattern_recommendations: List[Any]
    ) -> float:
        """Assess adherence to pattern-based recommendations"""
        if not pattern_recommendations:
            return 0.7
        
        adherence_scores = []
        
        for recommendation in pattern_recommendations:
            if isinstance(recommendation, dict):
                recommendation_type = recommendation.get("type", "unknown")
                recommended_value = recommendation.get("value")
                
                # Check if recommendation is followed
                if recommendation_type in decision_data:
                    actual_value = decision_data[recommendation_type]
                    
                    if recommended_value is not None:
                        if recommended_value == actual_value:
                            adherence_scores.append(1.0)
                        elif isinstance(recommended_value, (int, float)) and isinstance(actual_value, (int, float)):
                            similarity = 1.0 - min(abs(recommended_value - actual_value) / max(abs(recommended_value), abs(actual_value), 1.0), 1.0)
                            adherence_scores.append(similarity)
                        else:
                            adherence_scores.append(0.0)
        
        if adherence_scores:
            return statistics.mean(adherence_scores)
        
        return 0.7  # Default adherence score
    
    async def _assess_compliance(
        self,
        decision_data: Dict[str, Any],
        audit_data: Dict[str, Any]
    ) -> QualityMetric:
        """Assess regulatory and policy compliance"""
        try:
            score = 90.0  # Base score (start high for compliance)
            details = {}
            
            # Check validation compliance
            if audit_data and "validation_results" in audit_data:
                validation_results = audit_data["validation_results"]
                validation_compliance = self._assess_validation_compliance(validation_results)
                score = min(score, validation_compliance * 100)
                details["validation_compliance"] = validation_compliance
            
            # Check position limits compliance
            position_size = decision_data.get("position_size", 0)
            max_position = decision_data.get("max_allowed_position", float('inf'))
            
            if position_size <= max_position:
                details["position_limit_compliance"] = True
            else:
                score = min(score, 50.0)  # Major compliance violation
                details["position_limit_compliance"] = False
                details["position_limit_violation"] = position_size - max_position
            
            # Check risk limits compliance
            risk_level = decision_data.get("risk_level", 0.0)
            max_risk = decision_data.get("max_allowed_risk", 1.0)
            
            if risk_level <= max_risk:
                details["risk_limit_compliance"] = True
            else:
                score = min(score, 60.0)  # Risk limit violation
                details["risk_limit_compliance"] = False
                details["risk_limit_violation"] = risk_level - max_risk
            
            # Check documentation compliance
            required_fields = ["strategy", "rationale", "risk_assessment", "expected_outcome"]
            missing_fields = [field for field in required_fields if not decision_data.get(field)]
            
            if not missing_fields:
                details["documentation_compliance"] = True
            else:
                documentation_score = (len(required_fields) - len(missing_fields)) / len(required_fields)
                score = min(score, documentation_score * 100)
                details["documentation_compliance"] = False
                details["missing_fields"] = missing_fields
            
            # Check approval requirements
            requires_approval = decision_data.get("requires_approval", False)
            has_approval = decision_data.get("approved", False)
            
            if requires_approval and not has_approval:
                score = min(score, 40.0)  # Major compliance violation
                details["approval_compliance"] = False
            else:
                details["approval_compliance"] = True
            
            score = max(0, min(100, score))
            
            return QualityMetric(
                dimension=QualityDimension.COMPLIANCE,
                score=score,
                weight=self.quality_weights[QualityDimension.COMPLIANCE],
                details=details,
                confidence=0.9
            )
            
        except Exception as e:
            logger.error(f"Error assessing compliance: {str(e)}")
            return QualityMetric(
                dimension=QualityDimension.COMPLIANCE,
                score=70.0,
                weight=self.quality_weights[QualityDimension.COMPLIANCE],
                confidence=0.3
            )
    
    def _assess_validation_compliance(self, validation_results: Dict[str, Any]) -> float:
        """Assess compliance with validation requirements"""
        compliance_score = 1.0
        
        # Check if all required validation steps passed
        validation_steps = validation_results.get("steps", [])
        if validation_steps:
            passed_steps = sum(1 for step in validation_steps if step.get("passed", False))
            compliance_score = passed_steps / len(validation_steps)
        
        # Check overall validation status
        overall_passed = validation_results.get("passed", False)
        if not overall_passed:
            compliance_score = min(compliance_score, 0.5)
        
        return compliance_score
    
    async def _assess_performance(
        self,
        decision_data: Dict[str, Any],
        execution_results: Optional[Dict[str, Any]],
        impact_data: Dict[str, Any]
    ) -> QualityMetric:
        """Assess decision performance"""
        try:
            score = 75.0  # Base score
            details = {}
            
            # Execution performance
            if execution_results:
                execution_success = execution_results.get("success", False)
                execution_score = 100.0 if execution_success else 20.0
                score = (score + execution_score) / 2
                details["execution_success"] = execution_success
                
                # Performance metrics
                if "performance_metrics" in execution_results:
                    perf_metrics = execution_results["performance_metrics"]
                    performance_score = self._assess_performance_metrics(perf_metrics)
                    score = (score + performance_score * 100) / 2
                    details["performance_metrics_score"] = performance_score
            
            # Impact-based performance
            if impact_data:
                impact_performance = self._assess_impact_performance(impact_data)
                score = (score + impact_performance * 100) / 2
                details["impact_performance"] = impact_performance
                
                # Risk-adjusted performance
                if "risk_metrics" in impact_data:
                    risk_adjusted_perf = self._assess_risk_adjusted_performance(impact_data["risk_metrics"])
                    score = (score + risk_adjusted_perf * 100) / 2
                    details["risk_adjusted_performance"] = risk_adjusted_perf
            
            # Expected vs actual performance
            expected_return = decision_data.get("expected_return", 0.0)
            if execution_results and "actual_return" in execution_results:
                actual_return = execution_results["actual_return"]
                performance_accuracy = self._calculate_performance_accuracy(expected_return, actual_return)
                score = (score + performance_accuracy * 100) / 2
                details["performance_accuracy"] = performance_accuracy
            
            score = max(0, min(100, score))
            
            return QualityMetric(
                dimension=QualityDimension.PERFORMANCE,
                score=score,
                weight=self.quality_weights[QualityDimension.PERFORMANCE],
                details=details,
                confidence=0.8
            )
            
        except Exception as e:
            logger.error(f"Error assessing performance: {str(e)}")
            return QualityMetric(
                dimension=QualityDimension.PERFORMANCE,
                score=70.0,
                weight=self.quality_weights[QualityDimension.PERFORMANCE],
                confidence=0.3
            )
    
    def _assess_performance_metrics(self, performance_metrics: Dict[str, Any]) -> float:
        """Assess quality of performance metrics"""
        score = 0.5  # Base score
        
        # Check for key performance indicators
        kpis = ["return", "sharpe_ratio", "max_drawdown", "win_rate"]
        present_kpis = sum(1 for kpi in kpis if kpi in performance_metrics)
        score += (present_kpis / len(kpis)) * 0.3
        
        # Assess metric quality
        if "sharpe_ratio" in performance_metrics:
            sharpe = performance_metrics["sharpe_ratio"]
            if sharpe > 1.0:
                score += 0.2
            elif sharpe > 0.5:
                score += 0.1
        
        if "max_drawdown" in performance_metrics:
            drawdown = abs(performance_metrics["max_drawdown"])
            if drawdown < 0.05:  # Less than 5% drawdown
                score += 0.1
            elif drawdown < 0.10:  # Less than 10% drawdown
                score += 0.05
        
        return max(0.0, min(1.0, score))
    
    def _assess_impact_performance(self, impact_data: Dict[str, Any]) -> float:
        """Assess performance based on impact data"""
        score = 0.5  # Base score
        
        immediate_impact = impact_data.get("immediate_impact", {})
        
        # Total impact assessment
        total_impact = immediate_impact.get("total_impact", 0.0)
        if total_impact > 0:
            score += 0.3
        elif total_impact < 0:
            score -= 0.2
        
        # Risk-adjusted impact
        risk_adjusted_impact = immediate_impact.get("risk_adjusted_impact", 0.0)
        if risk_adjusted_impact > 0.05:  # 5% risk-adjusted return
            score += 0.2
        elif risk_adjusted_impact > 0.02:  # 2% risk-adjusted return
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _assess_risk_adjusted_performance(self, risk_metrics: Dict[str, Any]) -> float:
        """Assess risk-adjusted performance quality"""
        score = 0.5  # Base score
        
        # Sharpe ratio assessment
        if "sharpe_ratio" in risk_metrics:
            sharpe = risk_metrics["sharpe_ratio"]
            if sharpe > 2.0:
                score = 1.0
            elif sharpe > 1.0:
                score = 0.8
            elif sharpe > 0.5:
                score = 0.6
            elif sharpe > 0.0:
                score = 0.4
            else:
                score = 0.2
        
        return max(0.0, min(1.0, score))
    
    def _calculate_performance_accuracy(self, expected_return: float, actual_return: float) -> float:
        """Calculate accuracy of performance prediction"""
        if expected_return == 0 and actual_return == 0:
            return 1.0  # Perfect prediction
        
        if expected_return == 0:
            return 0.5  # Can't assess accuracy
        
        error = abs(expected_return - actual_return)
        relative_error = error / abs(expected_return)
        
        accuracy = 1.0 - min(relative_error, 1.0)
        return max(0.0, accuracy)
    
    async def _assess_adaptability(
        self,
        decision_data: Dict[str, Any],
        market_context: Optional[Dict[str, Any]],
        pattern_data: Dict[str, Any]
    ) -> QualityMetric:
        """Assess decision adaptability to changing conditions"""
        try:
            score = 80.0  # Base score
            details = {}
            
            # Market condition adaptability
            if market_context:
                market_adaptability = self._assess_market_adaptability(decision_data, market_context)
                score = (score + market_adaptability * 100) / 2
                details["market_adaptability"] = market_adaptability
            
            # Strategy flexibility
            strategy_flexibility = self._assess_strategy_flexibility(decision_data)
            score = (score + strategy_flexibility * 100) / 2
            details["strategy_flexibility"] = strategy_flexibility
            
            # Learning integration
            if pattern_data:
                learning_integration = self._assess_learning_integration(decision_data, pattern_data)
                score = (score + learning_integration * 100) / 2
                details["learning_integration"] = learning_integration
            
            # Parameter sensitivity
            parameter_sensitivity = self._assess_parameter_sensitivity(decision_data)
            score = (score + parameter_sensitivity * 100) / 2
            details["parameter_sensitivity"] = parameter_sensitivity
            
            score = max(0, min(100, score))
            
            return QualityMetric(
                dimension=QualityDimension.ADAPTABILITY,
                score=score,
                weight=self.quality_weights[QualityDimension.ADAPTABILITY],
                details=details,
                confidence=0.7
            )
            
        except Exception as e:
            logger.error(f"Error assessing adaptability: {str(e)}")
            return QualityMetric(
                dimension=QualityDimension.ADAPTABILITY,
                score=75.0,
                weight=self.quality_weights[QualityDimension.ADAPTABILITY],
                confidence=0.3
            )
    
    def _assess_market_adaptability(
        self,
        decision_data: Dict[str, Any],
        market_context: Dict[str, Any]
    ) -> float:
        """Assess how well decision adapts to market conditions"""
        score = 0.5  # Base score
        
        market_conditions = market_context.get("conditions", {})
        decision_adaptations = decision_data.get("market_adaptations", {})
        
        # Volatility adaptation
        market_vol = market_conditions.get("volatility", "normal")
        if market_vol == "high" and ("volatility_adjustment" in decision_adaptations or "high_vol_mode" in decision_adaptations):
            score += 0.2
        
        # Trend adaptation
        market_trend = market_conditions.get("trend", "stable")
        if market_trend != "stable" and ("trend_adjustment" in decision_adaptations or "trend_following" in decision_adaptations):
            score += 0.2
        
        # Liquidity adaptation
        market_liquidity = market_conditions.get("liquidity", "normal")
        if market_liquidity == "low" and ("liquidity_adjustment" in decision_adaptations or "size_reduction" in decision_adaptations):
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _assess_strategy_flexibility(self, decision_data: Dict[str, Any]) -> float:
        """Assess flexibility of decision strategy"""
        score = 0.5  # Base score
        
        # Check for multiple strategy options
        strategy_alternatives = decision_data.get("strategy_alternatives", [])
        if strategy_alternatives:
            score += min(len(strategy_alternatives) * 0.1, 0.3)
        
        # Check for exit strategies
        exit_strategies = decision_data.get("exit_strategies", [])
        if exit_strategies:
            score += min(len(exit_strategies) * 0.1, 0.2)
        
        # Check for contingency plans
        contingency_plans = decision_data.get("contingency_plans", [])
        if contingency_plans:
            score += min(len(contingency_plans) * 0.1, 0.2)
        
        return max(0.0, min(1.0, score))
    
    def _assess_learning_integration(
        self,
        decision_data: Dict[str, Any],
        pattern_data: Dict[str, Any]
    ) -> float:
        """Assess integration of learned patterns"""
        score = 0.5  # Base score
        
        # Check if recent patterns are incorporated
        pattern_recommendations = pattern_data.get("pattern_recommendations", [])
        if pattern_recommendations:
            recommendation_usage = sum(
                1 for rec in pattern_recommendations 
                if isinstance(rec, dict) and rec.get("type", "") in decision_data
            )
            if recommendation_usage > 0:
                score += min(recommendation_usage * 0.2, 0.3)
        
        # Check for historical performance consideration
        historical_performance = pattern_data.get("historical_performance", {})
        if historical_performance and "historical_analysis" in decision_data:
            score += 0.2
        
        return max(0.0, min(1.0, score))
    
    def _assess_parameter_sensitivity(self, decision_data: Dict[str, Any]) -> float:
        """Assess sensitivity analysis of decision parameters"""
        score = 0.5  # Base score
        
        # Check for sensitivity analysis
        if "sensitivity_analysis" in decision_data:
            sensitivity_data = decision_data["sensitivity_analysis"]
            if isinstance(sensitivity_data, dict) and sensitivity_data:
                score += 0.3
        
        # Check for parameter ranges
        if "parameter_ranges" in decision_data:
            score += 0.2
        
        return max(0.0, min(1.0, score))
    
    def _calculate_overall_score(self, dimensions: Dict[QualityDimension, QualityMetric]) -> float:
        """Calculate weighted overall quality score"""
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for dimension, metric in dimensions.items():
            weight = metric.weight
            score = metric.score
            confidence = metric.confidence
            
            # Adjust weight by confidence
            adjusted_weight = weight * confidence
            
            total_weighted_score += score * adjusted_weight
            total_weight += adjusted_weight
        
        if total_weight == 0:
            return 70.0  # Default score
        
        overall_score = total_weighted_score / total_weight
        return max(0.0, min(100.0, overall_score))
    
    def _determine_quality_grade(self, score: float) -> QualityGrade:
        """Determine quality grade based on score"""
        if score >= 90.0:
            return QualityGrade.EXCELLENT
        elif score >= 80.0:
            return QualityGrade.GOOD
        elif score >= 70.0:
            return QualityGrade.SATISFACTORY
        elif score >= 60.0:
            return QualityGrade.NEEDS_IMPROVEMENT
        else:
            return QualityGrade.POOR
    
    def _calculate_performance_attribution(
        self,
        dimensions: Dict[QualityDimension, QualityMetric]
    ) -> Dict[str, float]:
        """Calculate performance attribution across dimensions"""
        attribution = {}
        total_score = sum(metric.score * metric.weight for metric in dimensions.values())
        
        if total_score == 0:
            return attribution
        
        for dimension, metric in dimensions.items():
            contribution = (metric.score * metric.weight) / total_score * 100
            attribution[dimension.value] = round(contribution, 2)
        
        return attribution
    
    def _compare_to_benchmarks(self, overall_score: float) -> Dict[str, float]:
        """Compare quality score to various benchmarks"""
        comparison = {}
        
        for benchmark_name, benchmark_value in self.benchmarks.items():
            difference = overall_score - benchmark_value
            comparison[benchmark_name] = round(difference, 2)
        
        return comparison
    
    async def _generate_recommendations(
        self,
        dimensions: Dict[QualityDimension, QualityMetric],
        decision_data: Dict[str, Any]
    ) -> List[str]:
        """Generate improvement recommendations based on quality assessment"""
        recommendations = []
        
        # Sort dimensions by score (lowest first for improvement opportunities)
        sorted_dimensions = sorted(dimensions.items(), key=lambda x: x[1].score)
        
        for dimension, metric in sorted_dimensions[:3]:  # Top 3 improvement opportunities
            if metric.score < 80.0:
                rec = self._get_dimension_recommendation(dimension, metric, decision_data)
                if rec:
                    recommendations.append(rec)
        
        # Add AI Brain specific recommendations
        overall_score = self._calculate_overall_score(dimensions)
        if overall_score < self.benchmarks["ai_brain_threshold"]:
            recommendations.append(
                f"Overall quality score ({overall_score:.1f}%) is below AI Brain threshold "
                f"({self.benchmarks['ai_brain_threshold']}%). Focus on improving the lowest-scoring dimensions."
            )
        
        return recommendations
    
    def _get_dimension_recommendation(
        self,
        dimension: QualityDimension,
        metric: QualityMetric,
        decision_data: Dict[str, Any]
    ) -> Optional[str]:
        """Get specific recommendation for a quality dimension"""
        recommendations_map = {
            QualityDimension.ACCURACY: "Improve prediction accuracy by enhancing market analysis and historical backtesting validation.",
            QualityDimension.CONSISTENCY: "Increase decision consistency by standardizing decision-making processes and validation criteria.",
            QualityDimension.TIMELINESS: "Optimize decision timing by streamlining validation processes and improving execution speed.",
            QualityDimension.RISK_AWARENESS: "Enhance risk assessment by implementing more comprehensive risk identification and quantification methods.",
            QualityDimension.CONFIDENCE_CALIBRATION: "Improve confidence calibration through better uncertainty quantification and historical validation.",
            QualityDimension.IMPACT_ALIGNMENT: "Better align expected and actual impacts through improved impact modeling and real-time tracking.",
            QualityDimension.PATTERN_ADHERENCE: "Increase adherence to successful patterns by incorporating more pattern recognition and recommendation systems.",
            QualityDimension.COMPLIANCE: "Strengthen compliance by implementing automated validation checks and comprehensive documentation requirements.",
            QualityDimension.PERFORMANCE: "Enhance performance through better strategy optimization and risk-adjusted return targeting.",
            QualityDimension.ADAPTABILITY: "Improve adaptability by implementing more flexible strategies and market condition monitoring."
        }
        
        base_recommendation = recommendations_map.get(dimension)
        if base_recommendation and metric.score < 75.0:
            return f"{dimension.value.replace('_', ' ').title()}: {base_recommendation} (Current score: {metric.score:.1f}%)"
        
        return None
    
    def _identify_risk_flags(
        self,
        dimensions: Dict[QualityDimension, QualityMetric],
        decision_data: Dict[str, Any]
    ) -> List[str]:
        """Identify risk flags based on quality assessment"""
        risk_flags = []
        
        # Low quality scores
        for dimension, metric in dimensions.items():
            if metric.score < 50.0:
                risk_flags.append(f"Critical quality issue in {dimension.value}: {metric.score:.1f}%")
            elif metric.score < 60.0:
                risk_flags.append(f"Quality concern in {dimension.value}: {metric.score:.1f}%")
        
        # Specific risk conditions
        compliance_metric = dimensions.get(QualityDimension.COMPLIANCE)
        if compliance_metric and compliance_metric.score < 90.0:
            risk_flags.append("Compliance score below acceptable threshold")
        
        risk_metric = dimensions.get(QualityDimension.RISK_AWARENESS)
        if risk_metric and risk_metric.score < 70.0:
            risk_flags.append("Insufficient risk awareness detected")
        
        # Decision-specific risks
        position_size = decision_data.get("position_size", 0)
        max_position = decision_data.get("max_allowed_position", float('inf'))
        
        if position_size > max_position * 0.8:  # Close to limit
            risk_flags.append("Position size approaching maximum limit")
        
        return risk_flags
    
    def _check_compliance_status(
        self,
        dimensions: Dict[QualityDimension, QualityMetric]
    ) -> Dict[str, bool]:
        """Check compliance status across different areas"""
        compliance_status = {}
        
        # AI Brain compliance
        overall_score = self._calculate_overall_score(dimensions)
        compliance_status["ai_brain_compliant"] = overall_score >= self.benchmarks["ai_brain_threshold"]
        
        # Regulatory compliance
        compliance_metric = dimensions.get(QualityDimension.COMPLIANCE)
        compliance_status["regulatory_compliant"] = (
            compliance_metric.score >= 95.0 if compliance_metric else False
        )
        
        # Risk compliance
        risk_metric = dimensions.get(QualityDimension.RISK_AWARENESS)
        compliance_status["risk_compliant"] = (
            risk_metric.score >= 80.0 if risk_metric else False
        )
        
        # Performance compliance
        performance_metric = dimensions.get(QualityDimension.PERFORMANCE)
        compliance_status["performance_compliant"] = (
            performance_metric.score >= 75.0 if performance_metric else False
        )
        
        return compliance_status
    
    async def _update_performance_tracking(self, assessment: QualityAssessment):
        """Update performance tracking metrics"""
        try:
            # Update quality history trends
            self.quality_trends.append((assessment.timestamp, assessment.overall_score))
            
            # Cache performance metrics
            cache_key = f"performance_{datetime.utcnow().strftime('%Y-%m')}"
            
            if cache_key not in self.performance_cache:
                self.performance_cache[cache_key] = {
                    "total_decisions": 0,
                    "successful_decisions": 0,
                    "failed_decisions": 0,
                    "quality_scores": [],
                    "grades": defaultdict(int),
                    "dimension_scores": defaultdict(list)
                }
            
            cache_data = self.performance_cache[cache_key]
            cache_data["total_decisions"] += 1
            cache_data["quality_scores"].append(assessment.overall_score)
            cache_data["grades"][assessment.grade.value] += 1
            
            # Update dimension tracking
            for dimension, metric in assessment.dimensions.items():
                cache_data["dimension_scores"][dimension.value].append(metric.score)
            
            # Determine success/failure based on compliance
            if assessment.compliance_status.get("ai_brain_compliant", False):
                cache_data["successful_decisions"] += 1
            else:
                cache_data["failed_decisions"] += 1
                
        except Exception as e:
            logger.error(f"Error updating performance tracking: {str(e)}")
    
    async def _check_quality_alerts(self, assessment: QualityAssessment):
        """Check for quality-based alerts"""
        try:
            # Quality decline alert
            if len(self.quality_trends) >= 5:
                recent_scores = [score for _, score in list(self.quality_trends)[-5:]]
                trend = np.polyfit(range(len(recent_scores)), recent_scores, 1)[0]
                
                if trend < self.alert_thresholds["quality_decline_threshold"]:
                    if self.decision_logger:
                        await self.decision_logger.log_alert(
                            "quality_decline",
                            f"Quality declining trend detected: {trend:.2f} points per decision",
                            {"trend": trend, "recent_scores": recent_scores}
                        )
            
            # Risk flags alert
            if len(assessment.risk_flags) >= self.alert_thresholds["risk_flag_threshold"]:
                if self.decision_logger:
                    await self.decision_logger.log_alert(
                        "multiple_risk_flags",
                        f"Multiple risk flags detected: {len(assessment.risk_flags)}",
                        {"risk_flags": assessment.risk_flags}
                    )
            
            # Compliance alert
            if not assessment.compliance_status.get("ai_brain_compliant", False):
                if self.decision_logger:
                    await self.decision_logger.log_alert(
                        "ai_brain_non_compliance",
                        f"Decision quality below AI Brain threshold: {assessment.overall_score:.2f}%",
                        {"assessment_id": assessment.decision_id, "score": assessment.overall_score}
                    )
                    
        except Exception as e:
            logger.error(f"Error checking quality alerts: {str(e)}")
    
    async def get_quality_trends(
        self,
        period_days: int = 30,
        dimension: Optional[QualityDimension] = None
    ) -> QualityTrend:
        """Get quality trends over specified period"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_days)
            
            # Filter assessments within period
            period_assessments = [
                assessment for assessment in self.quality_history.values()
                if start_date <= assessment.timestamp <= end_date
            ]
            
            if not period_assessments:
                return QualityTrend(
                    period=f"{period_days}_days",
                    start_date=start_date,
                    end_date=end_date,
                    trend_direction="stable",
                    trend_strength=0.0,
                    quality_progression=[],
                    dimension_trends={},
                    performance_correlation=0.0,
                    recommendations=["Insufficient data for trend analysis"]
                )
            
            # Sort by timestamp
            period_assessments.sort(key=lambda x: x.timestamp)
            
            # Calculate overall trend
            timestamps = [a.timestamp for a in period_assessments]
            scores = [a.overall_score for a in period_assessments]
            
            quality_progression = list(zip(timestamps, scores))
            
            # Calculate trend direction and strength
            if len(scores) >= 2:
                trend_slope = np.polyfit(range(len(scores)), scores, 1)[0]
                trend_strength = abs(trend_slope) / 100.0  # Normalize
                
                if trend_slope > 2.0:
                    trend_direction = "improving"
                elif trend_slope < -2.0:
                    trend_direction = "declining"
                else:
                    trend_direction = "stable"
            else:
                trend_direction = "stable"
                trend_strength = 0.0
            
            # Calculate dimension trends
            dimension_trends = {}
            if dimension:
                dimension_scores = [
                    assessment.dimensions[dimension].score 
                    for assessment in period_assessments 
                    if dimension in assessment.dimensions
                ]
                
                if len(dimension_scores) >= 2:
                    dim_trend = np.polyfit(range(len(dimension_scores)), dimension_scores, 1)[0]
                    if dim_trend > 1.0:
                        dimension_trends[dimension] = "improving"
                    elif dim_trend < -1.0:
                        dimension_trends[dimension] = "declining"
                    else:
                        dimension_trends[dimension] = "stable"
            else:
                # Calculate trends for all dimensions
                for dim in QualityDimension:
                    dim_scores = [
                        assessment.dimensions[dim].score 
                        for assessment in period_assessments 
                        if dim in assessment.dimensions
                    ]
                    
                    if len(dim_scores) >= 2:
                        dim_trend = np.polyfit(range(len(dim_scores)), dim_scores, 1)[0]
                        if dim_trend > 1.0:
                            dimension_trends[dim] = "improving"
                        elif dim_trend < -1.0:
                            dimension_trends[dim] = "declining"
                        else:
                            dimension_trends[dim] = "stable"
            
            # Calculate performance correlation (placeholder)
            performance_correlation = 0.7  # Would correlate with actual performance data
            
            # Generate recommendations based on trends
            recommendations = self._generate_trend_recommendations(
                trend_direction, dimension_trends, period_assessments
            )
            
            return QualityTrend(
                period=f"{period_days}_days",
                start_date=start_date,
                end_date=end_date,
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                quality_progression=quality_progression,
                dimension_trends=dimension_trends,
                performance_correlation=performance_correlation,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error getting quality trends: {str(e)}")
            raise
    
    def _generate_trend_recommendations(
        self,
        trend_direction: str,
        dimension_trends: Dict[QualityDimension, str],
        period_assessments: List[QualityAssessment]
    ) -> List[str]:
        """Generate recommendations based on quality trends"""
        recommendations = []
        
        if trend_direction == "declining":
            recommendations.append("Overall quality is declining. Investigate root causes and implement corrective measures.")
            
            # Identify worst-performing dimensions
            declining_dimensions = [
                dim for dim, trend in dimension_trends.items() 
                if trend == "declining"
            ]
            
            if declining_dimensions:
                recommendations.append(
                    f"Focus on improving declining dimensions: {', '.join([d.value for d in declining_dimensions[:3]])}"
                )
        
        elif trend_direction == "improving":
            recommendations.append("Quality is improving. Continue current practices and identify successful patterns for replication.")
        
        else:  # stable
            avg_score = statistics.mean([a.overall_score for a in period_assessments])
            if avg_score < self.benchmarks["ai_brain_threshold"]:
                recommendations.append("Quality is stable but below AI Brain threshold. Implement systematic improvements.")
        
        # Dimension-specific recommendations
        best_dimension = max(dimension_trends.keys(), key=lambda d: statistics.mean([
            a.dimensions[d].score for a in period_assessments if d in a.dimensions
        ]), default=None)
        
        if best_dimension:
            recommendations.append(f"Leverage best practices from {best_dimension.value} to improve other dimensions.")
        
        return recommendations
    
    async def get_performance_metrics(
        self,
        period: str = "current_month"
    ) -> PerformanceMetrics:
        """Get comprehensive performance metrics"""
        try:
            cache_data = self.performance_cache.get(f"performance_{period}", {
                "total_decisions": 0,
                "successful_decisions": 0,
                "failed_decisions": 0,
                "quality_scores": [],
                "grades": defaultdict(int),
                "dimension_scores": defaultdict(list)
            })
            
            if not cache_data["quality_scores"]:
                return PerformanceMetrics(
                    total_decisions=0,
                    successful_decisions=0,
                    failed_decisions=0,
                    average_quality_score=0.0,
                    quality_consistency=0.0,
                    improvement_rate=0.0,
                    compliance_rate=0.0,
                    risk_adjusted_performance=0.0,
                    benchmark_outperformance=0.0,
                    quality_distribution={}
                )
            
            # Calculate metrics
            total_decisions = cache_data["total_decisions"]
            successful_decisions = cache_data["successful_decisions"]
            failed_decisions = cache_data["failed_decisions"]
            quality_scores = cache_data["quality_scores"]
            
            average_quality_score = statistics.mean(quality_scores)
            quality_consistency = 1.0 - (statistics.stdev(quality_scores) / 100.0) if len(quality_scores) > 1 else 1.0
            
            # Calculate improvement rate
            if len(quality_scores) >= 10:
                first_half = quality_scores[:len(quality_scores)//2]
                second_half = quality_scores[len(quality_scores)//2:]
                improvement_rate = (statistics.mean(second_half) - statistics.mean(first_half)) / statistics.mean(first_half) * 100
            else:
                improvement_rate = 0.0
            
            compliance_rate = successful_decisions / total_decisions if total_decisions > 0 else 0.0
            
            # Risk-adjusted performance (simplified calculation)
            risk_adjusted_performance = average_quality_score * compliance_rate / 100
            
            # Benchmark comparison
            benchmark_outperformance = average_quality_score - self.benchmarks["industry_average"]
            
            # Quality distribution
            quality_distribution = dict(cache_data["grades"])
            
            return PerformanceMetrics(
                total_decisions=total_decisions,
                successful_decisions=successful_decisions,
                failed_decisions=failed_decisions,
                average_quality_score=average_quality_score,
                quality_consistency=quality_consistency,
                improvement_rate=improvement_rate,
                compliance_rate=compliance_rate,
                risk_adjusted_performance=risk_adjusted_performance,
                benchmark_outperformance=benchmark_outperformance,
                quality_distribution=quality_distribution
            )
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            raise
    
    async def export_quality_report(
        self,
        decision_ids: Optional[List[str]] = None,
        period_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """Export comprehensive quality report"""
        try:
            report = {
                "report_generated": datetime.utcnow().isoformat(),
                "report_type": "comprehensive_quality_assessment",
                "metadata": {
                    "ai_brain_threshold": self.benchmarks["ai_brain_threshold"],
                    "total_assessments": len(self.quality_history)
                }
            }
            
            # Filter assessments
            if decision_ids:
                assessments = [
                    self.quality_history[did] for did in decision_ids 
                    if did in self.quality_history
                ]
            elif period_days:
                cutoff_date = datetime.utcnow() - timedelta(days=period_days)
                assessments = [
                    assessment for assessment in self.quality_history.values()
                    if assessment.timestamp >= cutoff_date
                ]
            else:
                assessments = list(self.quality_history.values())
            
            if not assessments:
                report["error"] = "No assessments found for specified criteria"
                return report
            
            # Summary statistics
            scores = [a.overall_score for a in assessments]
            report["summary"] = {
                "total_decisions": len(assessments),
                "average_score": statistics.mean(scores),
                "median_score": statistics.median(scores),
                "std_deviation": statistics.stdev(scores) if len(scores) > 1 else 0.0,
                "min_score": min(scores),
                "max_score": max(scores),
                "ai_brain_compliant": sum(1 for a in assessments if a.compliance_status.get("ai_brain_compliant", False)),
                "compliance_rate": sum(1 for a in assessments if a.compliance_status.get("ai_brain_compliant", False)) / len(assessments)
            }
            
            # Grade distribution
            grade_counts = defaultdict(int)
            for assessment in assessments:
                grade_counts[assessment.grade.value] += 1
            report["grade_distribution"] = dict(grade_counts)
            
            # Dimension analysis
            dimension_analysis = {}
            for dimension in QualityDimension:
                dim_scores = [
                    a.dimensions[dimension].score for a in assessments 
                    if dimension in a.dimensions
                ]
                if dim_scores:
                    dimension_analysis[dimension.value] = {
                        "average_score": statistics.mean(dim_scores),
                        "median_score": statistics.median(dim_scores),
                        "std_deviation": statistics.stdev(dim_scores) if len(dim_scores) > 1 else 0.0,
                        "min_score": min(dim_scores),
                        "max_score": max(dim_scores)
                    }
            report["dimension_analysis"] = dimension_analysis
            
            # Benchmark comparison
            benchmark_comparison = {}
            avg_score = statistics.mean(scores)
            for benchmark_name, benchmark_value in self.benchmarks.items():
                benchmark_comparison[benchmark_name] = {
                    "benchmark_value": benchmark_value,
                    "actual_value": avg_score,
                    "difference": avg_score - benchmark_value,
                    "outperforming": avg_score >= benchmark_value
                }
            report["benchmark_comparison"] = benchmark_comparison
            
            # Recent assessments
            recent_assessments = sorted(assessments, key=lambda x: x.timestamp, reverse=True)[:10]
            report["recent_assessments"] = [
                {
                    "decision_id": a.decision_id,
                    "timestamp": a.timestamp.isoformat(),
                    "score": a.overall_score,
                    "grade": a.grade.value,
                    "compliance": a.compliance_status,
                    "risk_flags_count": len(a.risk_flags)
                }
                for a in recent_assessments
            ]
            
            # Recommendations summary
            all_recommendations = []
            for assessment in assessments[-20:]:  # Last 20 assessments
                all_recommendations.extend(assessment.recommendations)
            
            # Count recommendation frequency
            recommendation_counts = defaultdict(int)
            for rec in all_recommendations:
                # Extract dimension from recommendation
                for dimension in QualityDimension:
                    if dimension.value.replace('_', ' ') in rec.lower():
                        recommendation_counts[dimension.value] += 1
                        break
            
            report["recommendation_priorities"] = dict(
                sorted(recommendation_counts.items(), key=lambda x: x[1], reverse=True)
            )
            
            return report
            
        except Exception as e:
            logger.error(f"Error exporting quality report: {str(e)}")
            raise


# Example usage and integration points
async def example_integration():
    """Example of how to integrate and use the Decision Quality Assessor"""
    
    # Initialize the assessor
    assessor = DecisionQualityAssessor()
    
    # Example integration with other components (would be actual component instances)
    components = {
        'audit_system': None,  # TradingDecisionAuditSystem instance
        'impact_assessor': None,  # DecisionImpactAssessor instance
        'confidence_scorer': None,  # DecisionConfidenceScorer instance
        'pattern_recognizer': None,  # DecisionPatternRecognizer instance
        'decision_logger': None  # DecisionLogger instance
    }
    
    await assessor.integrate_components(components)
    
    # Example decision data
    decision_data = {
        "decision_id": "trade_001",
        "type": "buy_order",
        "strategy": "momentum_trading",
        "position_size": 1000,
        "expected_return": 0.05,
        "risk_level": 0.3,
        "confidence": 0.75,
        "expected_impact": {"return": 0.05, "risk": 0.02},
        "identified_risks": ["market_volatility", "liquidity_risk"],
        "risk_mitigation": ["stop_loss", "position_sizing"],
        "requires_approval": False
    }
    
    execution_results = {
        "success": True,
        "actual_return": 0.045,
        "actual_outcome": "profitable",
        "performance_metrics": {
            "return": 0.045,
            "sharpe_ratio": 1.2,
            "max_drawdown": 0.02
        }
    }
    
    market_context = {
        "conditions": {
            "volatility": "normal",
            "trend": "upward",
            "liquidity": "high"
        }
    }
    
    # Assess decision quality
    assessment = await assessor.assess_decision_quality(
        decision_id="trade_001",
        decision_data=decision_data,
        execution_results=execution_results,
        market_context=market_context
    )
    
    print(f"Quality Assessment:")
    print(f"Overall Score: {assessment.overall_score:.2f}%")
    print(f"Grade: {assessment.grade.value}")
    print(f"AI Brain Compliant: {assessment.compliance_status.get('ai_brain_compliant', False)}")
    print(f"Recommendations: {assessment.recommendations}")
    
    # Get quality trends
    trends = await assessor.get_quality_trends(period_days=30)
    print(f"Quality Trend: {trends.trend_direction} (strength: {trends.trend_strength:.2f})")
    
    # Get performance metrics
    performance = await assessor.get_performance_metrics()
    print(f"Average Quality Score: {performance.average_quality_score:.2f}%")
    print(f"Compliance Rate: {performance.compliance_rate:.2%}")
    
    # Export quality report
    report = await assessor.export_quality_report(period_days=30)
    print(f"Report Summary: {report['summary']}")


if __name__ == "__main__":
    # Run example integration
    asyncio.run(example_integration())