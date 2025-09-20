"""
AI Trading System - Continuous Learning Framework
================================================

This module implements continuous learning and adaptive retraining strategies
for the AI trading system, including online learning, drift detection,
and automated model updates.
"""

import numpy as np
import pandas as pd
import torch
import pickle
from typing import Dict, List, Optional, Tuple, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging
from sklearn.base import clone
from sklearn.metrics import mean_squared_error, mean_absolute_error
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

@dataclass
class DriftMetrics:
    """Metrics for tracking model and data drift"""
    timestamp: datetime
    performance_drift: float
    data_drift: float
    concept_drift: float
    prediction_drift: float
    confidence_score: float

@dataclass
class RetrainingConfig:
    """Configuration for retraining strategies"""
    # Incremental learning
    enable_online_learning: bool = True
    online_learning_rate: float = 0.001
    online_batch_size: int = 32

    # Partial retraining
    partial_retrain_frequency: str = "weekly"  # daily, weekly, monthly
    partial_retrain_window: int = 30  # days
    partial_retrain_threshold: float = 0.1  # performance drop threshold

    # Full retraining
    full_retrain_frequency: str = "monthly"
    full_retrain_threshold: float = 0.2
    full_retrain_window: int = 90  # days

    # Drift detection
    drift_detection_window: int = 100
    drift_threshold: float = 0.05
    min_samples_for_detection: int = 50

    # Model selection
    enable_model_selection: bool = True
    candidate_models: List[str] = None
    selection_metric: str = "sharpe_ratio"

class DriftDetector(ABC):
    """Abstract base class for drift detection methods"""

    @abstractmethod
    def detect_drift(self, reference_data: np.ndarray, current_data: np.ndarray) -> Tuple[bool, float]:
        """Detect drift between reference and current data"""
        pass

class KSTestDriftDetector(DriftDetector):
    """Kolmogorov-Smirnov test for distribution drift detection"""

    def __init__(self, alpha: float = 0.05):
        self.alpha = alpha

    def detect_drift(self, reference_data: np.ndarray, current_data: np.ndarray) -> Tuple[bool, float]:
        """Detect drift using KS test"""
        if len(reference_data) < 10 or len(current_data) < 10:
            return False, 1.0

        # Flatten arrays if multidimensional
        if reference_data.ndim > 1:
            reference_data = reference_data.flatten()
        if current_data.ndim > 1:
            current_data = current_data.flatten()

        # Remove NaN values
        reference_data = reference_data[~np.isnan(reference_data)]
        current_data = current_data[~np.isnan(current_data)]

        if len(reference_data) < 10 or len(current_data) < 10:
            return False, 1.0

        try:
            statistic, p_value = stats.ks_2samp(reference_data, current_data)
            is_drift = p_value < self.alpha
            return is_drift, p_value
        except Exception:
            return False, 1.0

class PSITestDriftDetector(DriftDetector):
    """Population Stability Index for drift detection"""

    def __init__(self, threshold: float = 0.1, bins: int = 10):
        self.threshold = threshold
        self.bins = bins

    def detect_drift(self, reference_data: np.ndarray, current_data: np.ndarray) -> Tuple[bool, float]:
        """Detect drift using PSI"""
        try:
            # Calculate PSI for each feature
            if reference_data.ndim == 1:
                reference_data = reference_data.reshape(-1, 1)
            if current_data.ndim == 1:
                current_data = current_data.reshape(-1, 1)

            psi_values = []
            for i in range(reference_data.shape[1]):
                ref_col = reference_data[:, i]
                cur_col = current_data[:, i]

                # Remove NaN values
                ref_col = ref_col[~np.isnan(ref_col)]
                cur_col = cur_col[~np.isnan(cur_col)]

                if len(ref_col) < 10 or len(cur_col) < 10:
                    continue

                psi = self._calculate_psi(ref_col, cur_col)
                psi_values.append(psi)

            if not psi_values:
                return False, 0.0

            avg_psi = np.mean(psi_values)
            is_drift = avg_psi > self.threshold
            return is_drift, avg_psi

        except Exception:
            return False, 0.0

    def _calculate_psi(self, reference: np.ndarray, current: np.ndarray) -> float:
        """Calculate Population Stability Index"""
        # Create bins based on reference data
        bins = np.histogram_bin_edges(reference, bins=self.bins)

        # Calculate distributions
        ref_counts, _ = np.histogram(reference, bins=bins)
        cur_counts, _ = np.histogram(current, bins=bins)

        # Convert to proportions
        ref_props = ref_counts / len(reference)
        cur_props = cur_counts / len(current)

        # Avoid division by zero
        ref_props = np.where(ref_props == 0, 0.0001, ref_props)
        cur_props = np.where(cur_props == 0, 0.0001, cur_props)

        # Calculate PSI
        psi = np.sum((cur_props - ref_props) * np.log(cur_props / ref_props))
        return psi

class PerformanceDriftDetector:
    """Detect performance drift in model predictions"""

    def __init__(self, window_size: int = 100, threshold: float = 0.1):
        self.window_size = window_size
        self.threshold = threshold
        self.performance_history = []

    def update_performance(self, actual: np.ndarray, predicted: np.ndarray):
        """Update performance history with new predictions"""
        if len(actual) != len(predicted):
            return

        # Calculate various metrics
        mse = mean_squared_error(actual, predicted)
        mae = mean_absolute_error(actual, predicted)
        correlation = np.corrcoef(actual, predicted)[0, 1] if len(actual) > 1 else 0

        metrics = {
            'timestamp': datetime.now(),
            'mse': mse,
            'mae': mae,
            'correlation': correlation,
            'sample_size': len(actual)
        }

        self.performance_history.append(metrics)

        # Keep only recent history
        if len(self.performance_history) > self.window_size * 2:
            self.performance_history = self.performance_history[-self.window_size:]

    def detect_performance_drift(self) -> Tuple[bool, float]:
        """Detect significant performance degradation"""
        if len(self.performance_history) < self.window_size:
            return False, 0.0

        # Split history into reference and current windows
        split_point = len(self.performance_history) // 2
        reference_metrics = self.performance_history[:split_point]
        current_metrics = self.performance_history[split_point:]

        # Calculate average performance for each period
        ref_correlation = np.mean([m['correlation'] for m in reference_metrics])
        cur_correlation = np.mean([m['correlation'] for m in current_metrics])

        # Calculate performance drift
        performance_drift = abs(ref_correlation - cur_correlation)
        is_drift = performance_drift > self.threshold

        return is_drift, performance_drift

class OnlineLearner:
    """Online learning implementation for continuous model updates"""

    def __init__(self, base_model, learning_rate: float = 0.001):
        self.base_model = base_model
        self.learning_rate = learning_rate
        self.update_count = 0

    def partial_fit(self, X: np.ndarray, y: np.ndarray):
        """Perform incremental learning update"""
        if hasattr(self.base_model, 'partial_fit'):
            # Use scikit-learn partial_fit if available
            self.base_model.partial_fit(X, y)
        elif hasattr(self.base_model, 'model') and hasattr(self.base_model.model, 'state_dict'):
            # Handle PyTorch models
            self._torch_incremental_update(X, y)
        else:
            # Fallback: retrain on recent data
            self._fallback_update(X, y)

        self.update_count += 1

    def _torch_incremental_update(self, X: np.ndarray, y: np.ndarray):
        """Incremental update for PyTorch models"""
        if not hasattr(self.base_model, 'optimizer'):
            return

        device = next(self.base_model.model.parameters()).device
        X_tensor = torch.FloatTensor(X).to(device)
        y_tensor = torch.FloatTensor(y).to(device)

        self.base_model.model.train()
        self.base_model.optimizer.zero_grad()

        if len(X.shape) == 3:  # Sequence data
            predictions = self.base_model.model(X_tensor).squeeze()
        else:
            predictions = self.base_model.model(X_tensor.unsqueeze(0)).squeeze()

        loss = torch.nn.MSELoss()(predictions, y_tensor)
        loss.backward()

        # Apply learning rate decay
        for param_group in self.base_model.optimizer.param_groups:
            param_group['lr'] = self.learning_rate * (0.99 ** (self.update_count // 100))

        self.base_model.optimizer.step()

    def _fallback_update(self, X: np.ndarray, y: np.ndarray):
        """Fallback incremental update using exponential smoothing"""
        # This is a simple heuristic for models without native online learning
        # In practice, you might want to implement more sophisticated methods
        pass

class ModelRetrainer:
    """Manages different retraining strategies"""

    def __init__(self, config: RetrainingConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Drift detectors
        self.data_drift_detector = KSTestDriftDetector()
        self.performance_drift_detector = PerformanceDriftDetector()
        self.psi_drift_detector = PSITestDriftDetector()

        # Historical data storage
        self.historical_features = []
        self.historical_targets = []
        self.historical_predictions = []

        # Retraining schedule
        self.last_partial_retrain = datetime.now()
        self.last_full_retrain = datetime.now()

        # Online learners
        self.online_learners = {}

    def should_retrain(self, current_time: datetime = None) -> Dict[str, bool]:
        """Determine if retraining is needed based on schedule and drift"""
        if current_time is None:
            current_time = datetime.now()

        decisions = {
            'online_update': False,
            'partial_retrain': False,
            'full_retrain': False
        }

        # Check online learning
        if self.config.enable_online_learning:
            decisions['online_update'] = True

        # Check partial retraining schedule
        time_since_partial = current_time - self.last_partial_retrain
        if self.config.partial_retrain_frequency == "daily" and time_since_partial.days >= 1:
            decisions['partial_retrain'] = True
        elif self.config.partial_retrain_frequency == "weekly" and time_since_partial.days >= 7:
            decisions['partial_retrain'] = True
        elif self.config.partial_retrain_frequency == "monthly" and time_since_partial.days >= 30:
            decisions['partial_retrain'] = True

        # Check full retraining schedule
        time_since_full = current_time - self.last_full_retrain
        if self.config.full_retrain_frequency == "monthly" and time_since_full.days >= 30:
            decisions['full_retrain'] = True
        elif self.config.full_retrain_frequency == "quarterly" and time_since_full.days >= 90:
            decisions['full_retrain'] = True

        # Check drift-based retraining
        if len(self.historical_features) >= self.config.drift_detection_window:
            drift_metrics = self.detect_drift()
            if drift_metrics.performance_drift > self.config.partial_retrain_threshold:
                decisions['partial_retrain'] = True
            if drift_metrics.data_drift > self.config.full_retrain_threshold:
                decisions['full_retrain'] = True

        return decisions

    def detect_drift(self) -> DriftMetrics:
        """Detect various types of drift"""
        if len(self.historical_features) < self.config.drift_detection_window:
            return DriftMetrics(
                timestamp=datetime.now(),
                performance_drift=0.0,
                data_drift=0.0,
                concept_drift=0.0,
                prediction_drift=0.0,
                confidence_score=0.0
            )

        # Split data into reference and current windows
        split_point = len(self.historical_features) // 2
        reference_features = np.array(self.historical_features[:split_point])
        current_features = np.array(self.historical_features[split_point:])

        # Data drift detection
        data_drift_detected, data_drift_score = self.data_drift_detector.detect_drift(
            reference_features, current_features
        )

        # PSI-based drift
        psi_drift_detected, psi_score = self.psi_drift_detector.detect_drift(
            reference_features, current_features
        )

        # Performance drift
        if len(self.historical_targets) >= len(self.historical_predictions):
            recent_targets = np.array(self.historical_targets[-len(self.historical_predictions):])
            recent_predictions = np.array(self.historical_predictions)
            self.performance_drift_detector.update_performance(recent_targets, recent_predictions)

        perf_drift_detected, perf_drift_score = self.performance_drift_detector.detect_performance_drift()

        # Concept drift (simplified - based on correlation changes)
        concept_drift_score = self._detect_concept_drift()

        # Prediction drift
        pred_drift_score = self._detect_prediction_drift()

        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(
            data_drift_score, perf_drift_score, concept_drift_score
        )

        return DriftMetrics(
            timestamp=datetime.now(),
            performance_drift=perf_drift_score,
            data_drift=max(data_drift_score, psi_score),
            concept_drift=concept_drift_score,
            prediction_drift=pred_drift_score,
            confidence_score=confidence_score
        )

    def _detect_concept_drift(self) -> float:
        """Detect concept drift by analyzing feature-target correlations"""
        if len(self.historical_features) < 100 or len(self.historical_targets) < 100:
            return 0.0

        try:
            features = np.array(self.historical_features)
            targets = np.array(self.historical_targets)

            # Calculate correlations for first and second half
            split_point = len(features) // 2
            first_half_features = features[:split_point]
            first_half_targets = targets[:split_point]
            second_half_features = features[split_point:]
            second_half_targets = targets[split_point:]

            # Calculate feature correlations with target
            first_corrs = []
            second_corrs = []

            for i in range(features.shape[1]):
                try:
                    corr1 = np.corrcoef(first_half_features[:, i], first_half_targets)[0, 1]
                    corr2 = np.corrcoef(second_half_features[:, i], second_half_targets)[0, 1]
                    if not np.isnan(corr1) and not np.isnan(corr2):
                        first_corrs.append(corr1)
                        second_corrs.append(corr2)
                except:
                    continue

            if len(first_corrs) == 0:
                return 0.0

            # Calculate drift as average absolute difference in correlations
            drift_score = np.mean(np.abs(np.array(first_corrs) - np.array(second_corrs)))
            return drift_score

        except Exception:
            return 0.0

    def _detect_prediction_drift(self) -> float:
        """Detect drift in prediction distributions"""
        if len(self.historical_predictions) < 100:
            return 0.0

        predictions = np.array(self.historical_predictions)
        split_point = len(predictions) // 2
        first_half = predictions[:split_point]
        second_half = predictions[split_point:]

        try:
            _, p_value = stats.ks_2samp(first_half, second_half)
            return 1 - p_value  # Convert p-value to drift score
        except:
            return 0.0

    def _calculate_confidence_score(
        self,
        data_drift: float,
        performance_drift: float,
        concept_drift: float
    ) -> float:
        """Calculate overall confidence score"""
        # Weighted combination of drift scores
        weights = [0.3, 0.5, 0.2]  # performance drift has highest weight
        scores = [data_drift, performance_drift, concept_drift]

        weighted_drift = sum(w * s for w, s in zip(weights, scores))
        confidence = max(0, 1 - weighted_drift)  # Convert to confidence (higher is better)

        return confidence

    def update_data_history(
        self,
        features: np.ndarray,
        targets: np.ndarray,
        predictions: np.ndarray = None
    ):
        """Update historical data for drift detection"""
        # Add new data to history
        if features.ndim == 1:
            self.historical_features.append(features)
        else:
            self.historical_features.extend(features.tolist())

        if targets.ndim == 0:
            self.historical_targets.append(float(targets))
        else:
            self.historical_targets.extend(targets.tolist())

        if predictions is not None:
            if predictions.ndim == 0:
                self.historical_predictions.append(float(predictions))
            else:
                self.historical_predictions.extend(predictions.tolist())

        # Keep only recent history to avoid memory issues
        max_history = self.config.drift_detection_window * 3
        if len(self.historical_features) > max_history:
            self.historical_features = self.historical_features[-max_history:]
            self.historical_targets = self.historical_targets[-max_history:]
            if self.historical_predictions:
                self.historical_predictions = self.historical_predictions[-max_history:]

    def perform_online_update(self, model_id: str, model, X: np.ndarray, y: np.ndarray):
        """Perform online learning update"""
        if model_id not in self.online_learners:
            self.online_learners[model_id] = OnlineLearner(model, self.config.online_learning_rate)

        # Batch the updates for efficiency
        if len(X) >= self.config.online_batch_size:
            batch_indices = np.random.choice(len(X), self.config.online_batch_size, replace=False)
            X_batch = X[batch_indices]
            y_batch = y[batch_indices]
        else:
            X_batch, y_batch = X, y

        self.online_learners[model_id].partial_fit(X_batch, y_batch)
        self.logger.info(f"Performed online update for model {model_id}")

    def perform_partial_retrain(self, model, X: np.ndarray, y: np.ndarray):
        """Perform partial retraining on recent data"""
        # Use only recent data for partial retraining
        window_days = self.config.partial_retrain_window
        if len(X) > window_days * 24:  # Assuming hourly data
            recent_indices = -window_days * 24
            X_recent = X[recent_indices:]
            y_recent = y[recent_indices:]
        else:
            X_recent, y_recent = X, y

        # Retrain model on recent data
        if hasattr(model, 'fit'):
            model.fit(X_recent, y_recent)
        elif hasattr(model, 'model') and hasattr(model.model, 'train'):
            # Handle PyTorch models
            model.fit(X_recent, y_recent)

        self.last_partial_retrain = datetime.now()
        self.logger.info("Performed partial retraining")

    def perform_full_retrain(self, model, X: np.ndarray, y: np.ndarray):
        """Perform full retraining on all available data"""
        # Use full dataset for retraining
        if hasattr(model, 'fit'):
            model.fit(X, y)
        elif hasattr(model, 'model') and hasattr(model.model, 'train'):
            model.fit(X, y)

        self.last_full_retrain = datetime.now()
        self.logger.info("Performed full retraining")

    def adaptive_model_selection(
        self,
        candidate_models: List[Any],
        X_val: np.ndarray,
        y_val: np.ndarray,
        metric_func: Callable = None
    ) -> int:
        """Select best model based on validation performance"""
        if metric_func is None:
            metric_func = lambda y_true, y_pred: -mean_squared_error(y_true, y_pred)

        best_score = float('-inf')
        best_model_idx = 0

        for i, model in enumerate(candidate_models):
            try:
                predictions = model.predict(X_val)
                score = metric_func(y_val, predictions)

                if score > best_score:
                    best_score = score
                    best_model_idx = i

            except Exception as e:
                self.logger.warning(f"Model {i} evaluation failed: {e}")
                continue

        self.logger.info(f"Selected model {best_model_idx} with score {best_score}")
        return best_model_idx

    def save_state(self, filepath: str):
        """Save retrainer state"""
        state = {
            'config': self.config,
            'historical_features': self.historical_features[-1000:],  # Keep recent history
            'historical_targets': self.historical_targets[-1000:],
            'historical_predictions': self.historical_predictions[-1000:],
            'last_partial_retrain': self.last_partial_retrain,
            'last_full_retrain': self.last_full_retrain
        }

        with open(filepath, 'wb') as f:
            pickle.dump(state, f)

    def load_state(self, filepath: str):
        """Load retrainer state"""
        try:
            with open(filepath, 'rb') as f:
                state = pickle.load(f)

            self.config = state['config']
            self.historical_features = state['historical_features']
            self.historical_targets = state['historical_targets']
            self.historical_predictions = state['historical_predictions']
            self.last_partial_retrain = state['last_partial_retrain']
            self.last_full_retrain = state['last_full_retrain']

            self.logger.info("Successfully loaded retrainer state")

        except Exception as e:
            self.logger.error(f"Failed to load retrainer state: {e}")

class ContinuousLearningOrchestrator:
    """Main orchestrator for continuous learning pipeline"""

    def __init__(self, config: RetrainingConfig):
        self.config = config
        self.retrainer = ModelRetrainer(config)
        self.logger = logging.getLogger(__name__)
        self.active_models = {}

    def register_model(self, model_id: str, model):
        """Register a model for continuous learning"""
        self.active_models[model_id] = model
        self.logger.info(f"Registered model {model_id} for continuous learning")

    def process_new_data(
        self,
        X: np.ndarray,
        y: np.ndarray,
        predictions: Dict[str, np.ndarray] = None
    ):
        """Process new data and trigger appropriate learning updates"""

        # Update historical data
        pred_array = None
        if predictions:
            # Use first model's predictions for drift detection
            pred_array = list(predictions.values())[0]

        self.retrainer.update_data_history(X, y, pred_array)

        # Check if retraining is needed
        retraining_decisions = self.retrainer.should_retrain()

        # Perform updates based on decisions
        for model_id, model in self.active_models.items():
            try:
                if retraining_decisions['online_update']:
                    self.retrainer.perform_online_update(model_id, model, X, y)

                if retraining_decisions['partial_retrain']:
                    self.retrainer.perform_partial_retrain(model, X, y)

                if retraining_decisions['full_retrain']:
                    self.retrainer.perform_full_retrain(model, X, y)

            except Exception as e:
                self.logger.error(f"Error updating model {model_id}: {e}")

        # Log drift metrics
        if len(self.retrainer.historical_features) >= self.config.drift_detection_window:
            drift_metrics = self.retrainer.detect_drift()
            self.logger.info(f"Drift metrics: {drift_metrics}")

    def get_model_health_report(self) -> Dict[str, Any]:
        """Generate health report for all models"""
        drift_metrics = self.retrainer.detect_drift()

        report = {
            'timestamp': datetime.now(),
            'drift_metrics': drift_metrics,
            'active_models': list(self.active_models.keys()),
            'data_history_size': len(self.retrainer.historical_features),
            'last_partial_retrain': self.retrainer.last_partial_retrain,
            'last_full_retrain': self.retrainer.last_full_retrain,
            'online_learner_count': len(self.retrainer.online_learners)
        }

        return report