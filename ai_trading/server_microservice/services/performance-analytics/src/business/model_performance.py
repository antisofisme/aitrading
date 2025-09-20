"""
AI Model Performance Tracker - ML/DL/AI Performance Analysis
Comprehensive performance tracking for machine learning models in trading

Features:
- ML/DL/AI model accuracy assessment algorithms
- Prediction vs actual outcome analysis with error metrics  
- Model confidence calibration validation
- Performance degradation detection with alerts
- Cross-model comparison and ranking system
"""

import numpy as np
import pandas as pd
import scipy.stats as stats
from scipy.optimize import minimize_scalar
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, 
    confusion_matrix, classification_report, mean_squared_error,
    mean_absolute_error, r2_score, log_loss, roc_auc_score
)
from sklearn.calibration import calibration_curve
from sklearn.model_selection import cross_val_score
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
import asyncio
import logging
import warnings
from collections import deque, defaultdict
import json
import sys
import os

# Add shared path for AI Brain imports
shared_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "shared")
sys.path.insert(0, shared_path)

try:
    from ai_brain_confidence_framework import AiBrainConfidenceFramework, ConfidenceScore, ConfidenceThreshold
except ImportError:
    AiBrainConfidenceFramework = None
    ConfidenceScore = None
    ConfidenceThreshold = None

warnings.filterwarnings('ignore', category=RuntimeWarning)

@dataclass
class ModelAccuracyMetrics:
    """Comprehensive accuracy assessment for ML/DL/AI models"""
    model_name: str
    model_type: str  # 'ml', 'dl', 'ai', 'ensemble'
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    auc_roc: float
    log_loss: float
    mse: float
    mae: float
    r_squared: float
    directional_accuracy: float
    hit_rate: float
    false_positive_rate: float
    false_negative_rate: float
    balanced_accuracy: float
    matthews_correlation: float
    kappa_score: float
    confidence_score: float

@dataclass
class PredictionAnalysis:
    """Prediction vs actual outcome analysis"""
    model_name: str
    total_predictions: int
    correct_predictions: int
    prediction_accuracy: float
    prediction_bias: float
    prediction_variance: float
    calibration_score: float
    reliability_score: float
    sharpness_score: float
    overconfidence_ratio: float
    underconfidence_ratio: float
    prediction_consistency: float
    temporal_stability: float
    error_distribution: Dict[str, float]
    residual_analysis: Dict[str, Any]
    confidence_score: float

@dataclass
class ConfidenceCalibration:
    """Model confidence calibration analysis"""
    model_name: str
    calibration_error: float
    expected_calibration_error: float
    maximum_calibration_error: float
    adaptive_calibration_error: float
    brier_score: float
    reliability_diagram: Dict[str, List[float]]
    confidence_histogram: Dict[str, int]
    isotonic_calibration_params: Dict[str, Any]
    platt_scaling_params: Dict[str, Any]
    calibration_improvement: float
    optimal_threshold: float
    confidence_score: float

@dataclass
class PerformanceDegradation:
    """Performance degradation detection and analysis"""
    model_name: str
    degradation_detected: bool
    degradation_severity: str  # 'none', 'mild', 'moderate', 'severe'
    degradation_rate: float
    time_since_degradation: Optional[timedelta]
    performance_trend: List[float]
    rolling_accuracy: List[float]
    concept_drift_detected: bool
    data_drift_detected: bool
    statistical_tests: Dict[str, Dict[str, Any]]
    alert_threshold_breached: bool
    recommended_actions: List[str]
    confidence_score: float

@dataclass
class ModelComparison:
    """Cross-model comparison and ranking"""
    comparison_id: str
    models: List[str]
    ranking_metrics: Dict[str, List[str]]  # metric -> ranked model list
    overall_ranking: List[str]
    statistical_significance: Dict[str, bool]
    performance_matrix: pd.DataFrame
    pairwise_tests: Dict[str, Dict[str, float]]
    ensemble_performance: Dict[str, float]
    diversity_measures: Dict[str, float]
    correlation_matrix: pd.DataFrame
    best_model_by_metric: Dict[str, str]
    model_weights: Dict[str, float]
    confidence_score: float

@dataclass
class ModelHealthMetrics:
    """Overall model health assessment"""
    model_name: str
    health_score: float
    performance_score: float
    reliability_score: float
    calibration_score: float
    stability_score: float
    robustness_score: float
    efficiency_score: float
    last_assessment: datetime
    health_trend: str  # 'improving', 'stable', 'degrading'
    critical_issues: List[str]
    warnings: List[str]
    recommendations: List[str]
    confidence_score: float

class AIModelPerformanceTracker:
    """
    Comprehensive AI Model Performance Tracking System
    
    Tracks and analyzes performance of ML/DL/AI models with real-time
    monitoring, degradation detection, and confidence calibration.
    """
    
    def __init__(self, service_name: str = "performance-analytics"):
        self.service_name = service_name
        self.logger = logging.getLogger(f"{service_name}.model_performance")
        
        # Initialize AI Brain confidence framework if available
        if AiBrainConfidenceFramework:
            self.confidence_framework = AiBrainConfidenceFramework(service_name)
        else:
            self.confidence_framework = None
        
        # Performance tracking settings
        self.settings = {
            "accuracy_threshold": 0.60,  # Minimum acceptable accuracy
            "degradation_threshold": 0.05,  # 5% performance drop triggers alert
            "calibration_bins": 10,
            "rolling_window": 100,  # Number of predictions for rolling metrics
            "significance_level": 0.05,
            "drift_detection_window": 500,
            "min_predictions_for_analysis": 50,
            "confidence_threshold": 0.7
        }
        
        # Model tracking data structures
        self.model_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.model_metadata: Dict[str, Dict[str, Any]] = {}
        self.performance_cache: Dict[str, Any] = {}
        self.alert_history: List[Dict[str, Any]] = []
        
        self.logger.info(f"AI Model Performance Tracker initialized for {service_name}")
    
    async def assess_model_accuracy(self,
                                  model_name: str,
                                  predictions: List[Dict[str, Any]],
                                  actuals: List[Dict[str, Any]],
                                  model_type: str = "ml") -> ModelAccuracyMetrics:
        """
        Comprehensive accuracy assessment for ML/DL/AI models
        
        Args:
            model_name: Name/identifier of the model
            predictions: List of model predictions with confidence scores
            actuals: List of actual outcomes
            model_type: Type of model ('ml', 'dl', 'ai', 'ensemble')
            
        Returns:
            Comprehensive accuracy metrics
        """
        try:
            if not predictions or not actuals:
                raise ValueError("Both predictions and actuals required for accuracy assessment")
            
            if len(predictions) != len(actuals):
                raise ValueError("Predictions and actuals must have same length")
            
            # Convert to arrays for analysis
            pred_df = pd.DataFrame(predictions)
            actual_df = pd.DataFrame(actuals)
            
            # Extract prediction values and confidence scores
            y_pred = pred_df['prediction'].values
            y_true = actual_df['actual'].values
            
            # Handle different prediction types
            is_classification = self._is_classification_task(y_pred, y_true)
            
            if is_classification:
                # Classification metrics
                accuracy = accuracy_score(y_true, y_pred)
                precision = precision_score(y_true, y_pred, average='weighted', zero_division=0)
                recall = recall_score(y_true, y_pred, average='weighted', zero_division=0)
                f1 = f1_score(y_true, y_pred, average='weighted', zero_division=0)
                
                # Calculate AUC-ROC if probabilities available
                if 'probability' in pred_df.columns:
                    y_prob = pred_df['probability'].values
                    try:
                        auc_roc = roc_auc_score(y_true, y_prob)
                        log_loss_val = log_loss(y_true, y_prob)
                    except:
                        auc_roc = 0.5
                        log_loss_val = 1.0
                else:
                    auc_roc = 0.5
                    log_loss_val = 1.0
                
                # Regression metrics (set to 0 for classification)
                mse = mean_squared_error(y_true, y_pred)  # Still valid for discrete values
                mae = mean_absolute_error(y_true, y_pred)
                r_squared = 0.0  # Not applicable for classification
                
                # Additional classification metrics
                tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel() if len(np.unique(y_true)) == 2 else (0, 0, 0, 0)
                false_positive_rate = fp / (fp + tn) if (fp + tn) > 0 else 0
                false_negative_rate = fn / (fn + tp) if (fn + tp) > 0 else 0
                
            else:
                # Regression metrics
                mse = mean_squared_error(y_true, y_pred)
                mae = mean_absolute_error(y_true, y_pred)
                r_squared = r2_score(y_true, y_pred)
                
                # Convert regression to classification-like metrics
                # Direction accuracy: did the model predict the right direction?
                pred_direction = np.sign(y_pred)
                true_direction = np.sign(y_true)
                accuracy = accuracy_score(true_direction, pred_direction)
                
                # Set classification-specific metrics to reasonable defaults
                precision = accuracy
                recall = accuracy
                f1 = accuracy
                auc_roc = 0.5
                log_loss_val = mse  # Use MSE as loss for regression
                false_positive_rate = 1 - accuracy
                false_negative_rate = 1 - accuracy
            
            # Directional accuracy (for trading: did we predict up/down correctly?)
            directional_accuracy = await self._calculate_directional_accuracy(y_pred, y_true)
            
            # Hit rate (percentage of profitable predictions)
            hit_rate = await self._calculate_hit_rate(predictions, actuals)
            
            # Balanced accuracy
            balanced_accuracy = await self._calculate_balanced_accuracy(y_true, y_pred)
            
            # Matthews correlation coefficient
            matthews_correlation = await self._calculate_matthews_correlation(y_true, y_pred)
            
            # Cohen's Kappa
            kappa_score = await self._calculate_kappa_score(y_true, y_pred)
            
            # Store prediction history for trend analysis
            self._store_prediction_history(model_name, predictions, actuals)
            
            # Calculate confidence score
            confidence_score = await self._calculate_accuracy_confidence_score({
                'model_type': model_type,
                'sample_size': len(predictions),
                'accuracy': accuracy,
                'is_classification': is_classification,
                'data_quality': self._assess_prediction_data_quality(predictions, actuals)
            })
            
            accuracy_metrics = ModelAccuracyMetrics(
                model_name=model_name,
                model_type=model_type,
                accuracy=round(accuracy, 4),
                precision=round(precision, 4),
                recall=round(recall, 4),
                f1_score=round(f1, 4),
                auc_roc=round(auc_roc, 4),
                log_loss=round(log_loss_val, 4),
                mse=round(mse, 4),
                mae=round(mae, 4),
                r_squared=round(r_squared, 4),
                directional_accuracy=round(directional_accuracy, 4),
                hit_rate=round(hit_rate, 4),
                false_positive_rate=round(false_positive_rate, 4),
                false_negative_rate=round(false_negative_rate, 4),
                balanced_accuracy=round(balanced_accuracy, 4),
                matthews_correlation=round(matthews_correlation, 4),
                kappa_score=round(kappa_score, 4),
                confidence_score=confidence_score
            )
            
            self.logger.info(f"Model accuracy assessed - {model_name}: {accuracy:.4f} accuracy, {hit_rate:.4f} hit rate")
            
            return accuracy_metrics
            
        except Exception as e:
            self.logger.error(f"Model accuracy assessment failed for {model_name}: {e}")
            raise
    
    async def analyze_predictions(self,
                                model_name: str,
                                predictions: List[Dict[str, Any]],
                                actuals: List[Dict[str, Any]],
                                time_window: Optional[timedelta] = None) -> PredictionAnalysis:
        """
        Detailed prediction vs actual outcome analysis
        
        Args:
            model_name: Name of the model
            predictions: Model predictions with timestamps and confidence
            actuals: Actual outcomes with timestamps
            time_window: Analysis time window
            
        Returns:
            Comprehensive prediction analysis
        """
        try:
            if not predictions or not actuals:
                raise ValueError("Predictions and actuals required for analysis")
            
            # Filter by time window if provided
            if time_window:
                cutoff_time = datetime.now() - time_window
                predictions = [p for p in predictions if 
                             datetime.fromisoformat(p['timestamp']) >= cutoff_time]
                actuals = [a for a in actuals if 
                          datetime.fromisoformat(a['timestamp']) >= cutoff_time]
            
            if len(predictions) != len(actuals):
                # Match predictions to actuals by timestamp or ID
                predictions, actuals = self._align_predictions_actuals(predictions, actuals)
            
            # Basic prediction statistics
            total_predictions = len(predictions)
            
            pred_values = np.array([p['prediction'] for p in predictions])
            actual_values = np.array([a['actual'] for a in actuals])
            confidence_scores = np.array([p.get('confidence', 0.5) for p in predictions])
            
            # Correct predictions (exact match or within tolerance for regression)
            correct_predictions = np.sum(np.isclose(pred_values, actual_values, rtol=0.1))
            prediction_accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
            
            # Prediction bias (systematic over/under estimation)
            prediction_bias = np.mean(pred_values - actual_values)
            
            # Prediction variance (spread of predictions)
            prediction_variance = np.var(pred_values)
            
            # Calibration analysis
            calibration_score = await self._calculate_prediction_calibration(predictions, actuals)
            
            # Reliability score (consistency of confidence scores)
            reliability_score = await self._calculate_prediction_reliability(predictions, actuals)
            
            # Sharpness score (concentration of confidence scores)
            sharpness_score = 1 - np.std(confidence_scores)  # Lower std = higher sharpness
            
            # Over/under confidence ratios
            overconfidence_ratio, underconfidence_ratio = await self._calculate_confidence_ratios(predictions, actuals)
            
            # Prediction consistency over time
            prediction_consistency = await self._calculate_prediction_consistency(predictions)
            
            # Temporal stability
            temporal_stability = await self._calculate_temporal_stability(predictions, actuals)
            
            # Error distribution analysis
            errors = pred_values - actual_values
            error_distribution = {
                'mean_error': float(np.mean(errors)),
                'std_error': float(np.std(errors)),
                'skewness': float(stats.skew(errors)),
                'kurtosis': float(stats.kurtosis(errors)),
                'min_error': float(np.min(errors)),
                'max_error': float(np.max(errors)),
                'median_error': float(np.median(errors)),
                'iqr_error': float(np.percentile(errors, 75) - np.percentile(errors, 25))
            }
            
            # Residual analysis
            residual_analysis = await self._analyze_residuals(pred_values, actual_values)
            
            # Confidence score
            confidence_score = await self._calculate_prediction_confidence_score({
                'prediction_accuracy': prediction_accuracy,
                'calibration_score': calibration_score,
                'sample_size': total_predictions,
                'temporal_stability': temporal_stability,
                'error_consistency': 1 - abs(prediction_bias)
            })
            
            prediction_analysis = PredictionAnalysis(
                model_name=model_name,
                total_predictions=total_predictions,
                correct_predictions=correct_predictions,
                prediction_accuracy=round(prediction_accuracy, 4),
                prediction_bias=round(prediction_bias, 4),
                prediction_variance=round(prediction_variance, 4),
                calibration_score=round(calibration_score, 4),
                reliability_score=round(reliability_score, 4),
                sharpness_score=round(sharpness_score, 4),
                overconfidence_ratio=round(overconfidence_ratio, 4),
                underconfidence_ratio=round(underconfidence_ratio, 4),
                prediction_consistency=round(prediction_consistency, 4),
                temporal_stability=round(temporal_stability, 4),
                error_distribution=error_distribution,
                residual_analysis=residual_analysis,
                confidence_score=confidence_score
            )
            
            self.logger.info(f"Prediction analysis completed - {model_name}: {prediction_accuracy:.4f} accuracy")
            
            return prediction_analysis
            
        except Exception as e:
            self.logger.error(f"Prediction analysis failed for {model_name}: {e}")
            raise
    
    async def validate_confidence_calibration(self,
                                            model_name: str,
                                            predictions: List[Dict[str, Any]],
                                            actuals: List[Dict[str, Any]],
                                            calibration_method: str = "isotonic") -> ConfidenceCalibration:
        """
        Validate and improve model confidence calibration
        
        Args:
            model_name: Name of the model
            predictions: Model predictions with confidence scores
            actuals: Actual outcomes
            calibration_method: Method for calibration ('isotonic', 'platt', 'both')
            
        Returns:
            Confidence calibration analysis and improvement recommendations
        """
        try:
            if not predictions or not actuals:
                raise ValueError("Predictions and actuals required for calibration validation")
            
            # Extract data
            pred_df = pd.DataFrame(predictions)
            actual_df = pd.DataFrame(actuals)
            
            confidence_scores = pred_df['confidence'].values
            predictions_binary = (pred_df['prediction'] > 0).astype(int)  # Convert to binary for calibration
            actuals_binary = (actual_df['actual'] > 0).astype(int)
            
            # Calculate calibration metrics
            calibration_error = await self._calculate_calibration_error(confidence_scores, actuals_binary)
            
            # Expected Calibration Error (ECE)
            expected_calibration_error = await self._calculate_expected_calibration_error(
                confidence_scores, actuals_binary, self.settings["calibration_bins"]
            )
            
            # Maximum Calibration Error (MCE)
            maximum_calibration_error = await self._calculate_maximum_calibration_error(
                confidence_scores, actuals_binary, self.settings["calibration_bins"]
            )
            
            # Adaptive Calibration Error (ACE)
            adaptive_calibration_error = await self._calculate_adaptive_calibration_error(
                confidence_scores, actuals_binary
            )
            
            # Brier Score
            brier_score = np.mean((confidence_scores - actuals_binary) ** 2)
            
            # Reliability diagram data
            reliability_diagram = await self._generate_reliability_diagram(
                confidence_scores, actuals_binary, self.settings["calibration_bins"]
            )
            
            # Confidence histogram
            confidence_histogram = await self._generate_confidence_histogram(confidence_scores)
            
            # Calibration improvement methods
            isotonic_calibration_params = {}
            platt_scaling_params = {}
            
            if calibration_method in ["isotonic", "both"]:
                isotonic_calibration_params = await self._fit_isotonic_calibration(
                    confidence_scores, actuals_binary
                )
            
            if calibration_method in ["platt", "both"]:
                platt_scaling_params = await self._fit_platt_scaling(
                    confidence_scores, actuals_binary
                )
            
            # Calculate improvement potential
            calibration_improvement = max(0, calibration_error - expected_calibration_error)
            
            # Find optimal threshold for binary decisions
            optimal_threshold = await self._find_optimal_threshold(confidence_scores, actuals_binary)
            
            # Confidence score
            confidence_score = await self._calculate_calibration_confidence_score({
                'calibration_error': calibration_error,
                'sample_size': len(predictions),
                'brier_score': brier_score,
                'confidence_distribution': np.std(confidence_scores)
            })
            
            calibration_analysis = ConfidenceCalibration(
                model_name=model_name,
                calibration_error=round(calibration_error, 4),
                expected_calibration_error=round(expected_calibration_error, 4),
                maximum_calibration_error=round(maximum_calibration_error, 4),
                adaptive_calibration_error=round(adaptive_calibration_error, 4),
                brier_score=round(brier_score, 4),
                reliability_diagram=reliability_diagram,
                confidence_histogram=confidence_histogram,
                isotonic_calibration_params=isotonic_calibration_params,
                platt_scaling_params=platt_scaling_params,
                calibration_improvement=round(calibration_improvement, 4),
                optimal_threshold=round(optimal_threshold, 4),
                confidence_score=confidence_score
            )
            
            self.logger.info(f"Confidence calibration validated - {model_name}: ECE={expected_calibration_error:.4f}")
            
            return calibration_analysis
            
        except Exception as e:
            self.logger.error(f"Confidence calibration validation failed for {model_name}: {e}")
            raise
    
    async def detect_performance_degradation(self,
                                           model_name: str,
                                           recent_predictions: List[Dict[str, Any]],
                                           recent_actuals: List[Dict[str, Any]],
                                           baseline_accuracy: Optional[float] = None) -> PerformanceDegradation:
        """
        Detect performance degradation with statistical tests and alerts
        
        Args:
            model_name: Name of the model
            recent_predictions: Recent model predictions
            recent_actuals: Recent actual outcomes
            baseline_accuracy: Baseline accuracy for comparison
            
        Returns:
            Performance degradation analysis with recommendations
        """
        try:
            if not recent_predictions or not recent_actuals:
                raise ValueError("Recent predictions and actuals required for degradation detection")
            
            # Get model history for comparison
            historical_performance = self._get_model_performance_history(model_name)
            
            # Calculate recent performance
            recent_assessment = await self.assess_model_accuracy(
                model_name, recent_predictions, recent_actuals
            )
            recent_accuracy = recent_assessment.accuracy
            
            # Determine baseline
            if baseline_accuracy is None:
                if historical_performance:
                    baseline_accuracy = np.mean([p['accuracy'] for p in historical_performance[-10:]])
                else:
                    baseline_accuracy = self.settings["accuracy_threshold"]
            
            # Calculate degradation
            degradation_rate = (baseline_accuracy - recent_accuracy) / baseline_accuracy if baseline_accuracy > 0 else 0
            degradation_detected = degradation_rate > self.settings["degradation_threshold"]
            
            # Classify degradation severity
            if degradation_rate < 0:
                degradation_severity = "none"  # Performance improved
            elif degradation_rate < 0.05:
                degradation_severity = "mild"
            elif degradation_rate < 0.15:
                degradation_severity = "moderate"
            else:
                degradation_severity = "severe"
            
            # Performance trend analysis
            performance_trend = [p['accuracy'] for p in historical_performance[-20:]] if historical_performance else []
            
            # Rolling accuracy calculation
            rolling_window = min(self.settings["rolling_window"], len(historical_performance))
            rolling_accuracy = []
            if len(historical_performance) >= rolling_window:
                for i in range(rolling_window, len(historical_performance) + 1):
                    window_data = historical_performance[i-rolling_window:i]
                    rolling_acc = np.mean([p['accuracy'] for p in window_data])
                    rolling_accuracy.append(rolling_acc)
            
            # Drift detection
            concept_drift_detected = await self._detect_concept_drift(
                recent_predictions, recent_actuals, historical_performance
            )
            
            data_drift_detected = await self._detect_data_drift(
                recent_predictions, historical_performance
            )
            
            # Statistical tests
            statistical_tests = await self._perform_degradation_tests(
                recent_accuracy, historical_performance
            )
            
            # Alert threshold check
            alert_threshold_breached = (
                degradation_detected or 
                recent_accuracy < self.settings["accuracy_threshold"] or
                concept_drift_detected or 
                data_drift_detected
            )
            
            # Generate recommendations
            recommended_actions = await self._generate_degradation_recommendations(
                degradation_severity, concept_drift_detected, data_drift_detected, recent_accuracy
            )
            
            # Calculate time since degradation started
            time_since_degradation = None
            if degradation_detected and historical_performance:
                for i, perf in enumerate(reversed(historical_performance)):
                    if perf['accuracy'] >= baseline_accuracy - (baseline_accuracy * self.settings["degradation_threshold"]):
                        time_since_degradation = timedelta(days=i)
                        break
            
            # Confidence score
            confidence_score = await self._calculate_degradation_confidence_score({
                'sample_size': len(recent_predictions),
                'historical_data_points': len(historical_performance),
                'statistical_significance': statistical_tests.get('t_test', {}).get('significant', False),
                'trend_consistency': len(performance_trend) > 5
            })
            
            degradation_analysis = PerformanceDegradation(
                model_name=model_name,
                degradation_detected=degradation_detected,
                degradation_severity=degradation_severity,
                degradation_rate=round(degradation_rate, 4),
                time_since_degradation=time_since_degradation,
                performance_trend=performance_trend,
                rolling_accuracy=rolling_accuracy,
                concept_drift_detected=concept_drift_detected,
                data_drift_detected=data_drift_detected,
                statistical_tests=statistical_tests,
                alert_threshold_breached=alert_threshold_breached,
                recommended_actions=recommended_actions,
                confidence_score=confidence_score
            )
            
            # Log alert if degradation detected
            if alert_threshold_breached:
                alert = {
                    'timestamp': datetime.now().isoformat(),
                    'model_name': model_name,
                    'alert_type': 'performance_degradation',
                    'severity': degradation_severity,
                    'degradation_rate': degradation_rate,
                    'recent_accuracy': recent_accuracy,
                    'baseline_accuracy': baseline_accuracy
                }
                self.alert_history.append(alert)
                self.logger.warning(f"Performance degradation alert - {model_name}: {degradation_severity} degradation detected")
            
            self.logger.info(f"Degradation detection completed - {model_name}: {degradation_severity} degradation")
            
            return degradation_analysis
            
        except Exception as e:
            self.logger.error(f"Performance degradation detection failed for {model_name}: {e}")
            raise
    
    async def compare_models(self,
                           model_performances: Dict[str, Dict[str, Any]],
                           comparison_metrics: Optional[List[str]] = None) -> ModelComparison:
        """
        Cross-model comparison and ranking system
        
        Args:
            model_performances: Dictionary of model names to their performance metrics
            comparison_metrics: Specific metrics to compare (defaults to key metrics)
            
        Returns:
            Comprehensive model comparison and ranking
        """
        try:
            if len(model_performances) < 2:
                raise ValueError("At least 2 models required for comparison")
            
            models = list(model_performances.keys())
            metrics = comparison_metrics or [
                'accuracy', 'precision', 'recall', 'f1_score', 'auc_roc', 
                'hit_rate', 'directional_accuracy'
            ]
            
            # Create performance matrix
            performance_data = {}
            for metric in metrics:
                performance_data[metric] = []
                for model in models:
                    perf_value = model_performances[model].get(metric, 0)
                    performance_data[metric].append(perf_value)
            
            performance_matrix = pd.DataFrame(performance_data, index=models)
            
            # Ranking by each metric
            ranking_metrics = {}
            for metric in metrics:
                # Higher is better for most metrics
                ascending = metric in ['log_loss', 'mse', 'mae']  # Lower is better for these
                ranked = performance_matrix[metric].sort_values(ascending=ascending)
                ranking_metrics[metric] = ranked.index.tolist()
            
            # Overall ranking (weighted average of normalized scores)
            metric_weights = {
                'accuracy': 0.2,
                'precision': 0.15,
                'recall': 0.15,
                'f1_score': 0.15,
                'auc_roc': 0.1,
                'hit_rate': 0.15,
                'directional_accuracy': 0.1
            }
            
            # Normalize scores (0-1 scale)
            normalized_matrix = performance_matrix.copy()
            for metric in metrics:
                if metric in normalized_matrix.columns:
                    col_min = normalized_matrix[metric].min()
                    col_max = normalized_matrix[metric].max()
                    if col_max > col_min:
                        if metric in ['log_loss', 'mse', 'mae']:  # Invert for lower-is-better metrics
                            normalized_matrix[metric] = 1 - (normalized_matrix[metric] - col_min) / (col_max - col_min)
                        else:
                            normalized_matrix[metric] = (normalized_matrix[metric] - col_min) / (col_max - col_min)
                    else:
                        normalized_matrix[metric] = 1.0
            
            # Calculate weighted overall scores
            overall_scores = {}
            for model in models:
                score = 0
                total_weight = 0
                for metric, weight in metric_weights.items():
                    if metric in normalized_matrix.columns:
                        score += normalized_matrix.loc[model, metric] * weight
                        total_weight += weight
                overall_scores[model] = score / total_weight if total_weight > 0 else 0
            
            overall_ranking = sorted(models, key=lambda m: overall_scores[m], reverse=True)
            
            # Statistical significance tests
            statistical_significance = {}
            for i, model1 in enumerate(models):
                for model2 in models[i+1:]:
                    sig_test = await self._test_model_difference_significance(
                        model_performances[model1], model_performances[model2]
                    )
                    statistical_significance[f"{model1}_vs_{model2}"] = sig_test
            
            # Pairwise comparison tests
            pairwise_tests = await self._perform_pairwise_tests(model_performances, metrics)
            
            # Ensemble performance prediction
            ensemble_performance = await self._calculate_ensemble_performance(model_performances)
            
            # Diversity measures
            diversity_measures = await self._calculate_model_diversity(model_performances)
            
            # Correlation matrix
            correlation_matrix = normalized_matrix.T.corr()
            
            # Best model by each metric
            best_model_by_metric = {}
            for metric in metrics:
                if metric in performance_matrix.columns:
                    ascending = metric in ['log_loss', 'mse', 'mae']
                    best_model_by_metric[metric] = performance_matrix[metric].idxmin() if ascending else performance_matrix[metric].idxmax()
            
            # Calculate optimal ensemble weights
            model_weights = await self._calculate_optimal_weights(normalized_matrix, overall_scores)
            
            # Confidence score
            confidence_score = await self._calculate_comparison_confidence_score({
                'num_models': len(models),
                'sample_consistency': np.std(list(overall_scores.values())),
                'statistical_significance': np.mean([s for s in statistical_significance.values()]),
                'performance_separation': max(overall_scores.values()) - min(overall_scores.values())
            })
            
            comparison = ModelComparison(
                comparison_id=f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                models=models,
                ranking_metrics=ranking_metrics,
                overall_ranking=overall_ranking,
                statistical_significance=statistical_significance,
                performance_matrix=performance_matrix,
                pairwise_tests=pairwise_tests,
                ensemble_performance=ensemble_performance,
                diversity_measures=diversity_measures,
                correlation_matrix=correlation_matrix,
                best_model_by_metric=best_model_by_metric,
                model_weights=model_weights,
                confidence_score=confidence_score
            )
            
            self.logger.info(f"Model comparison completed - Best overall: {overall_ranking[0]}")
            
            return comparison
            
        except Exception as e:
            self.logger.error(f"Model comparison failed: {e}")
            raise
    
    # Helper methods (truncated for space - full implementation would include all methods)
    
    def _is_classification_task(self, y_pred: np.ndarray, y_true: np.ndarray) -> bool:
        """Determine if this is a classification or regression task"""
        # Simple heuristic: if all values are integers and limited range, it's classification
        pred_range = len(np.unique(y_pred))
        true_range = len(np.unique(y_true))
        
        return (pred_range <= 10 and true_range <= 10 and 
                np.allclose(y_pred, y_pred.astype(int)) and 
                np.allclose(y_true, y_true.astype(int)))
    
    async def _calculate_directional_accuracy(self, y_pred: np.ndarray, y_true: np.ndarray) -> float:
        """Calculate directional accuracy (for trading: up/down prediction accuracy)"""
        try:
            pred_direction = np.sign(y_pred)
            true_direction = np.sign(y_true)
            return np.mean(pred_direction == true_direction)
        except:
            return 0.5
    
    async def _calculate_hit_rate(self, predictions: List[Dict], actuals: List[Dict]) -> float:
        """Calculate hit rate (profitable prediction rate)"""
        try:
            profits = 0
            total = 0
            for pred, actual in zip(predictions, actuals):
                # Assume profit if prediction and actual have same sign
                pred_val = pred.get('prediction', 0)
                actual_val = actual.get('actual', 0)
                if np.sign(pred_val) == np.sign(actual_val) and actual_val != 0:
                    profits += 1
                total += 1
            return profits / total if total > 0 else 0
        except:
            return 0.5
    
    async def _calculate_balanced_accuracy(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calculate balanced accuracy"""
        try:
            from sklearn.metrics import balanced_accuracy_score
            return balanced_accuracy_score(y_true, y_pred)
        except:
            return accuracy_score(y_true, y_pred)
    
    async def _calculate_matthews_correlation(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calculate Matthews correlation coefficient"""
        try:
            from sklearn.metrics import matthews_corrcoef
            return matthews_corrcoef(y_true, y_pred)
        except:
            return 0.0
    
    async def _calculate_kappa_score(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calculate Cohen's Kappa score"""
        try:
            from sklearn.metrics import cohen_kappa_score
            return cohen_kappa_score(y_true, y_pred)
        except:
            return 0.0
    
    def _store_prediction_history(self, model_name: str, predictions: List[Dict], actuals: List[Dict]):
        """Store prediction history for trend analysis"""
        timestamp = datetime.now()
        accuracy = accuracy_score(
            [a['actual'] for a in actuals],
            [p['prediction'] for p in predictions]
        )
        
        history_entry = {
            'timestamp': timestamp,
            'accuracy': accuracy,
            'sample_size': len(predictions),
            'prediction_data': predictions[:100]  # Store only recent samples
        }
        
        self.model_history[model_name].append(history_entry)
    
    def _assess_prediction_data_quality(self, predictions: List[Dict], actuals: List[Dict]) -> float:
        """Assess quality of prediction data"""
        quality_score = 1.0
        
        # Check for missing confidence scores
        missing_confidence = sum(1 for p in predictions if 'confidence' not in p or p['confidence'] is None)
        if missing_confidence > 0:
            quality_score *= (1 - missing_confidence / len(predictions))
        
        # Check for reasonable confidence ranges
        confidences = [p.get('confidence', 0.5) for p in predictions]
        if any(c < 0 or c > 1 for c in confidences):
            quality_score *= 0.8
        
        # Check timestamp consistency
        timestamps = [p.get('timestamp') for p in predictions if 'timestamp' in p]
        if len(timestamps) < len(predictions) * 0.9:  # Less than 90% have timestamps
            quality_score *= 0.9
        
        return quality_score
    
    def _get_model_performance_history(self, model_name: str) -> List[Dict]:
        """Get historical performance data for a model"""
        return list(self.model_history.get(model_name, []))
    
    # Confidence scoring methods
    
    async def _calculate_accuracy_confidence_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate confidence score for accuracy assessment"""
        try:
            if not self.confidence_framework:
                return 0.8
            
            sample_confidence = min(1.0, metrics['sample_size'] / 100)
            accuracy_confidence = metrics['accuracy']
            data_confidence = metrics['data_quality']
            
            # Model type affects confidence
            type_confidence = {
                'ensemble': 0.9,
                'ai': 0.85,
                'dl': 0.8,
                'ml': 0.75
            }.get(metrics['model_type'], 0.75)
            
            return (sample_confidence * 0.3 + accuracy_confidence * 0.3 + 
                   data_confidence * 0.2 + type_confidence * 0.2)
        except:
            return 0.8
    
    async def _calculate_prediction_confidence_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate confidence score for prediction analysis"""
        try:
            accuracy_confidence = metrics['prediction_accuracy']
            calibration_confidence = metrics['calibration_score']
            sample_confidence = min(1.0, metrics['sample_size'] / 100)
            stability_confidence = metrics['temporal_stability']
            
            return (accuracy_confidence * 0.3 + calibration_confidence * 0.25 + 
                   sample_confidence * 0.25 + stability_confidence * 0.2)
        except:
            return 0.75
    
    async def _calculate_calibration_confidence_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate confidence score for calibration analysis"""
        try:
            # Lower calibration error = higher confidence
            calibration_confidence = max(0, 1 - metrics['calibration_error'])
            sample_confidence = min(1.0, metrics['sample_size'] / 100)
            brier_confidence = max(0, 1 - metrics['brier_score'])
            
            return (calibration_confidence * 0.4 + sample_confidence * 0.3 + brier_confidence * 0.3)
        except:
            return 0.7
    
    async def _calculate_degradation_confidence_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate confidence score for degradation detection"""
        try:
            sample_confidence = min(1.0, metrics['sample_size'] / 50)
            historical_confidence = min(1.0, metrics['historical_data_points'] / 20)
            significance_confidence = 0.9 if metrics['statistical_significance'] else 0.6
            trend_confidence = 0.8 if metrics['trend_consistency'] else 0.5
            
            return (sample_confidence * 0.3 + historical_confidence * 0.3 + 
                   significance_confidence * 0.25 + trend_confidence * 0.15)
        except:
            return 0.7
    
    async def _calculate_comparison_confidence_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate confidence score for model comparison"""
        try:
            model_count_confidence = min(1.0, metrics['num_models'] / 5)  # More models = higher confidence
            consistency_confidence = max(0, 1 - metrics['sample_consistency'])
            significance_confidence = metrics['statistical_significance']
            separation_confidence = min(1.0, metrics['performance_separation'] * 2)
            
            return (model_count_confidence * 0.25 + consistency_confidence * 0.25 + 
                   significance_confidence * 0.25 + separation_confidence * 0.25)
        except:
            return 0.75