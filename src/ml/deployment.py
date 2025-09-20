"""
AI Trading System - Model Deployment Framework
==============================================

This module implements comprehensive model deployment strategies for
production trading systems, including real-time serving, A/B testing,
monitoring, and auto-scaling capabilities.
"""

import numpy as np
import pandas as pd
import pickle
import joblib
import json
import logging
import time
import threading
from typing import Dict, List, Optional, Tuple, Any, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from collections import deque
from concurrent.futures import ThreadPoolExecutor
import warnings
warnings.filterwarnings('ignore')

@dataclass
class DeploymentConfig:
    """Configuration for model deployment"""
    # Serving configuration
    max_prediction_latency_ms: int = 100
    batch_size: int = 1000
    max_queue_size: int = 10000
    timeout_seconds: int = 30

    # Load balancing
    production_traffic_ratio: float = 0.8
    shadow_traffic_ratio: float = 0.15
    experimental_traffic_ratio: float = 0.05

    # Auto-scaling
    cpu_threshold: float = 0.8
    memory_threshold: float = 0.8
    min_replicas: int = 2
    max_replicas: int = 10
    scale_up_cooldown: int = 300  # seconds
    scale_down_cooldown: int = 600  # seconds

    # Monitoring
    health_check_interval: int = 30  # seconds
    metrics_collection_interval: int = 60  # seconds
    alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
        'latency_p95_ms': 200,
        'error_rate': 0.05,
        'throughput_drop': 0.3,
        'memory_usage': 0.9
    })

    # Circuit breaker
    failure_threshold: int = 5
    recovery_timeout: int = 60
    half_open_max_calls: int = 3

@dataclass
class PredictionRequest:
    """Request for model prediction"""
    request_id: str
    features: np.ndarray
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1  # 1=high, 2=medium, 3=low

@dataclass
class PredictionResponse:
    """Response from model prediction"""
    request_id: str
    prediction: Union[float, np.ndarray]
    confidence: float
    model_version: str
    processing_time_ms: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ModelMetrics:
    """Metrics for model monitoring"""
    model_id: str
    version: str
    timestamp: datetime
    predictions_count: int
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    error_rate: float
    throughput_per_second: float
    memory_usage_mb: float
    cpu_usage_percent: float

class CircuitBreaker:
    """Circuit breaker pattern for fault tolerance"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60, half_open_max_calls: int = 3):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.half_open_calls = 0

    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
                self.half_open_calls = 0
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        return (
            self.last_failure_time is not None and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )

    def _on_success(self):
        """Handle successful call"""
        if self.state == "HALF_OPEN":
            self.half_open_calls += 1
            if self.half_open_calls >= self.half_open_max_calls:
                self.state = "CLOSED"
                self.failure_count = 0
        elif self.state == "CLOSED":
            self.failure_count = 0

    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == "HALF_OPEN" or self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

class ModelServer(ABC):
    """Abstract base class for model servers"""

    @abstractmethod
    def load_model(self, model_path: str, version: str):
        """Load model from storage"""
        pass

    @abstractmethod
    def predict(self, features: np.ndarray) -> Tuple[np.ndarray, float]:
        """Make prediction and return confidence"""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if model server is healthy"""
        pass

    @abstractmethod
    def get_metrics(self) -> ModelMetrics:
        """Get current model metrics"""
        pass

class PythonModelServer(ModelServer):
    """Python-based model server implementation"""

    def __init__(self, model_id: str, config: DeploymentConfig):
        self.model_id = model_id
        self.config = config
        self.model = None
        self.version = None
        self.is_loaded = False

        # Metrics tracking
        self.prediction_times = deque(maxlen=1000)
        self.error_count = 0
        self.total_requests = 0
        self.last_metrics_time = time.time()

        # Circuit breaker
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=config.failure_threshold,
            recovery_timeout=config.recovery_timeout,
            half_open_max_calls=config.half_open_max_calls
        )

        self.logger = logging.getLogger(f"ModelServer-{model_id}")

    def load_model(self, model_path: str, version: str):
        """Load model from file"""
        try:
            if model_path.endswith('.pkl'):
                with open(model_path, 'rb') as f:
                    self.model = pickle.load(f)
            elif model_path.endswith('.joblib'):
                self.model = joblib.load(model_path)
            else:
                raise ValueError(f"Unsupported model format: {model_path}")

            self.version = version
            self.is_loaded = True
            self.logger.info(f"Loaded model version {version} from {model_path}")

        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            raise

    def predict(self, features: np.ndarray) -> Tuple[np.ndarray, float]:
        """Make prediction with circuit breaker protection"""
        if not self.is_loaded:
            raise RuntimeError("Model not loaded")

        return self.circuit_breaker.call(self._predict_internal, features)

    def _predict_internal(self, features: np.ndarray) -> Tuple[np.ndarray, float]:
        """Internal prediction method"""
        start_time = time.time()

        try:
            # Validate input
            if features is None or len(features) == 0:
                raise ValueError("Empty features provided")

            # Make prediction
            if hasattr(self.model, 'predict'):
                prediction = self.model.predict(features)
            else:
                raise ValueError("Model does not have predict method")

            # Calculate confidence (simplified)
            if hasattr(self.model, 'predict_proba'):
                probabilities = self.model.predict_proba(features)
                confidence = np.max(probabilities, axis=1).mean()
            else:
                confidence = 0.8  # Default confidence

            # Track metrics
            processing_time = (time.time() - start_time) * 1000
            self.prediction_times.append(processing_time)
            self.total_requests += 1

            return prediction, confidence

        except Exception as e:
            self.error_count += 1
            self.logger.error(f"Prediction error: {e}")
            raise

    def health_check(self) -> bool:
        """Check server health"""
        try:
            if not self.is_loaded:
                return False

            # Test prediction with dummy data
            dummy_features = np.zeros((1, 10))  # Adjust based on expected input size
            _ = self.predict(dummy_features)
            return True

        except Exception:
            return False

    def get_metrics(self) -> ModelMetrics:
        """Get current performance metrics"""
        current_time = time.time()
        time_window = current_time - self.last_metrics_time

        # Calculate metrics
        avg_latency = np.mean(self.prediction_times) if self.prediction_times else 0
        p95_latency = np.percentile(self.prediction_times, 95) if self.prediction_times else 0
        p99_latency = np.percentile(self.prediction_times, 99) if self.prediction_times else 0

        error_rate = self.error_count / self.total_requests if self.total_requests > 0 else 0
        throughput = self.total_requests / time_window if time_window > 0 else 0

        # Reset counters
        self.error_count = 0
        self.total_requests = 0
        self.last_metrics_time = current_time

        return ModelMetrics(
            model_id=self.model_id,
            version=self.version or "unknown",
            timestamp=datetime.now(),
            predictions_count=len(self.prediction_times),
            avg_latency_ms=avg_latency,
            p95_latency_ms=p95_latency,
            p99_latency_ms=p99_latency,
            error_rate=error_rate,
            throughput_per_second=throughput,
            memory_usage_mb=0.0,  # Would need psutil for actual memory usage
            cpu_usage_percent=0.0  # Would need psutil for actual CPU usage
        )

class LoadBalancer:
    """Load balancer for distributing requests across model servers"""

    def __init__(self, config: DeploymentConfig):
        self.config = config
        self.servers: Dict[str, List[ModelServer]] = {
            'production': [],
            'shadow': [],
            'experimental': []
        }
        self.current_index = {'production': 0, 'shadow': 0, 'experimental': 0}
        self.logger = logging.getLogger("LoadBalancer")

    def add_server(self, server: ModelServer, tier: str = 'production'):
        """Add server to specific tier"""
        if tier not in self.servers:
            raise ValueError(f"Unknown tier: {tier}")

        self.servers[tier].append(server)
        self.logger.info(f"Added server to {tier} tier")

    def remove_server(self, server: ModelServer, tier: str = 'production'):
        """Remove server from tier"""
        if tier in self.servers and server in self.servers[tier]:
            self.servers[tier].remove(server)
            self.logger.info(f"Removed server from {tier} tier")

    def route_request(self, request: PredictionRequest) -> PredictionResponse:
        """Route request to appropriate server"""
        # Determine tier based on traffic ratios
        tier = self._select_tier()

        # Get server from tier
        server = self._get_server(tier)

        if server is None:
            raise RuntimeError(f"No healthy servers available in {tier} tier")

        try:
            # Make prediction
            start_time = time.time()
            prediction, confidence = server.predict(request.features)
            processing_time = (time.time() - start_time) * 1000

            return PredictionResponse(
                request_id=request.request_id,
                prediction=prediction,
                confidence=confidence,
                model_version=server.version or "unknown",
                processing_time_ms=processing_time,
                timestamp=datetime.now(),
                metadata={'tier': tier, 'server_id': server.model_id}
            )

        except Exception as e:
            self.logger.error(f"Request routing failed: {e}")
            raise

    def _select_tier(self) -> str:
        """Select tier based on traffic ratios"""
        rand = np.random.random()

        if rand < self.config.production_traffic_ratio:
            return 'production'
        elif rand < self.config.production_traffic_ratio + self.config.shadow_traffic_ratio:
            return 'shadow'
        else:
            return 'experimental'

    def _get_server(self, tier: str) -> Optional[ModelServer]:
        """Get next healthy server from tier using round-robin"""
        servers = self.servers[tier]
        if not servers:
            return None

        # Try to find healthy server
        for _ in range(len(servers)):
            server = servers[self.current_index[tier]]
            self.current_index[tier] = (self.current_index[tier] + 1) % len(servers)

            if server.health_check():
                return server

        return None

    def get_tier_health(self) -> Dict[str, Dict[str, Any]]:
        """Get health status for all tiers"""
        health_status = {}

        for tier, servers in self.servers.items():
            healthy_count = sum(1 for server in servers if server.health_check())
            health_status[tier] = {
                'total_servers': len(servers),
                'healthy_servers': healthy_count,
                'health_ratio': healthy_count / len(servers) if servers else 0
            }

        return health_status

class ModelMonitor:
    """Monitor model performance and health"""

    def __init__(self, config: DeploymentConfig):
        self.config = config
        self.metrics_history: List[ModelMetrics] = []
        self.alert_handlers: List[Callable] = []
        self.is_monitoring = False
        self.monitor_thread = None
        self.logger = logging.getLogger("ModelMonitor")

    def add_alert_handler(self, handler: Callable[[str, Dict[str, Any]], None]):
        """Add alert handler function"""
        self.alert_handlers.append(handler)

    def start_monitoring(self, servers: List[ModelServer]):
        """Start monitoring servers"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(servers,),
            daemon=True
        )
        self.monitor_thread.start()
        self.logger.info("Started model monitoring")

    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        self.logger.info("Stopped model monitoring")

    def _monitoring_loop(self, servers: List[ModelServer]):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Collect metrics from all servers
                current_metrics = []
                for server in servers:
                    try:
                        metrics = server.get_metrics()
                        current_metrics.append(metrics)
                        self.metrics_history.append(metrics)
                    except Exception as e:
                        self.logger.error(f"Failed to collect metrics from {server.model_id}: {e}")

                # Keep only recent metrics (last 24 hours)
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.metrics_history = [
                    m for m in self.metrics_history if m.timestamp > cutoff_time
                ]

                # Check for alerts
                self._check_alerts(current_metrics)

                time.sleep(self.config.metrics_collection_interval)

            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                time.sleep(self.config.metrics_collection_interval)

    def _check_alerts(self, metrics_list: List[ModelMetrics]):
        """Check metrics against alert thresholds"""
        for metrics in metrics_list:
            alerts = []

            # Check latency
            if metrics.p95_latency_ms > self.config.alert_thresholds['latency_p95_ms']:
                alerts.append({
                    'type': 'HIGH_LATENCY',
                    'value': metrics.p95_latency_ms,
                    'threshold': self.config.alert_thresholds['latency_p95_ms']
                })

            # Check error rate
            if metrics.error_rate > self.config.alert_thresholds['error_rate']:
                alerts.append({
                    'type': 'HIGH_ERROR_RATE',
                    'value': metrics.error_rate,
                    'threshold': self.config.alert_thresholds['error_rate']
                })

            # Check memory usage
            if metrics.memory_usage_mb > self.config.alert_thresholds['memory_usage'] * 1024:  # Convert to MB
                alerts.append({
                    'type': 'HIGH_MEMORY_USAGE',
                    'value': metrics.memory_usage_mb,
                    'threshold': self.config.alert_thresholds['memory_usage'] * 1024
                })

            # Trigger alerts
            for alert in alerts:
                self._trigger_alert(metrics.model_id, alert)

    def _trigger_alert(self, model_id: str, alert: Dict[str, Any]):
        """Trigger alert to all handlers"""
        alert_message = f"ALERT: {alert['type']} for model {model_id}"
        alert_data = {
            'model_id': model_id,
            'alert_type': alert['type'],
            'value': alert['value'],
            'threshold': alert['threshold'],
            'timestamp': datetime.now()
        }

        self.logger.warning(alert_message)

        for handler in self.alert_handlers:
            try:
                handler(alert_message, alert_data)
            except Exception as e:
                self.logger.error(f"Alert handler failed: {e}")

    def get_metrics_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get metrics summary for the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [m for m in self.metrics_history if m.timestamp > cutoff_time]

        if not recent_metrics:
            return {}

        # Aggregate metrics
        total_predictions = sum(m.predictions_count for m in recent_metrics)
        avg_latency = np.mean([m.avg_latency_ms for m in recent_metrics])
        avg_error_rate = np.mean([m.error_rate for m in recent_metrics])
        avg_throughput = np.mean([m.throughput_per_second for m in recent_metrics])

        return {
            'time_window_hours': hours,
            'total_predictions': total_predictions,
            'avg_latency_ms': avg_latency,
            'avg_error_rate': avg_error_rate,
            'avg_throughput_per_second': avg_throughput,
            'unique_models': len(set(m.model_id for m in recent_metrics))
        }

class ABTestManager:
    """A/B testing framework for model comparison"""

    def __init__(self):
        self.active_tests: Dict[str, Dict[str, Any]] = {}
        self.test_results: Dict[str, List[Dict[str, Any]]] = {}
        self.logger = logging.getLogger("ABTestManager")

    def create_test(
        self,
        test_id: str,
        control_model: str,
        treatment_model: str,
        traffic_split: float = 0.5,
        duration_hours: int = 24,
        success_metric: str = 'accuracy'
    ):
        """Create new A/B test"""
        self.active_tests[test_id] = {
            'control_model': control_model,
            'treatment_model': treatment_model,
            'traffic_split': traffic_split,
            'start_time': datetime.now(),
            'duration_hours': duration_hours,
            'success_metric': success_metric,
            'control_results': [],
            'treatment_results': []
        }

        self.test_results[test_id] = []
        self.logger.info(f"Created A/B test {test_id}")

    def route_for_test(self, test_id: str, request: PredictionRequest) -> str:
        """Determine which model to use for A/B test"""
        if test_id not in self.active_tests:
            raise ValueError(f"Test {test_id} not found")

        test = self.active_tests[test_id]

        # Check if test is still active
        elapsed = datetime.now() - test['start_time']
        if elapsed.total_seconds() > test['duration_hours'] * 3600:
            return test['control_model']  # Use control if test expired

        # Route based on traffic split
        if np.random.random() < test['traffic_split']:
            return test['treatment_model']
        else:
            return test['control_model']

    def record_result(
        self,
        test_id: str,
        model_used: str,
        prediction: float,
        actual: float,
        metadata: Dict[str, Any] = None
    ):
        """Record test result"""
        if test_id not in self.active_tests:
            return

        test = self.active_tests[test_id]
        result = {
            'timestamp': datetime.now(),
            'prediction': prediction,
            'actual': actual,
            'error': abs(prediction - actual),
            'correct_direction': np.sign(prediction) == np.sign(actual),
            'metadata': metadata or {}
        }

        if model_used == test['control_model']:
            test['control_results'].append(result)
        elif model_used == test['treatment_model']:
            test['treatment_results'].append(result)

    def analyze_test(self, test_id: str) -> Dict[str, Any]:
        """Analyze A/B test results"""
        if test_id not in self.active_tests:
            raise ValueError(f"Test {test_id} not found")

        test = self.active_tests[test_id]
        control_results = test['control_results']
        treatment_results = test['treatment_results']

        if len(control_results) == 0 or len(treatment_results) == 0:
            return {'status': 'insufficient_data'}

        # Calculate metrics for both groups
        control_metrics = self._calculate_test_metrics(control_results)
        treatment_metrics = self._calculate_test_metrics(treatment_results)

        # Statistical significance test (simplified)
        significance = self._test_significance(control_results, treatment_results)

        return {
            'test_id': test_id,
            'status': 'completed',
            'control_metrics': control_metrics,
            'treatment_metrics': treatment_metrics,
            'significance': significance,
            'recommendation': self._get_recommendation(control_metrics, treatment_metrics, significance)
        }

    def _calculate_test_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate metrics for test group"""
        if not results:
            return {}

        errors = [r['error'] for r in results]
        directions = [r['correct_direction'] for r in results]

        return {
            'sample_size': len(results),
            'mean_error': np.mean(errors),
            'directional_accuracy': np.mean(directions),
            'rmse': np.sqrt(np.mean([e**2 for e in errors]))
        }

    def _test_significance(self, control_results: List[Dict], treatment_results: List[Dict]) -> Dict[str, float]:
        """Test statistical significance of difference"""
        control_errors = [r['error'] for r in control_results]
        treatment_errors = [r['error'] for r in treatment_results]

        # T-test for difference in means
        from scipy.stats import ttest_ind
        try:
            t_stat, p_value = ttest_ind(control_errors, treatment_errors)
            return {'t_statistic': t_stat, 'p_value': p_value}
        except:
            return {'t_statistic': 0, 'p_value': 1}

    def _get_recommendation(
        self,
        control_metrics: Dict[str, float],
        treatment_metrics: Dict[str, float],
        significance: Dict[str, float]
    ) -> str:
        """Get recommendation based on test results"""
        if significance['p_value'] > 0.05:
            return "No significant difference - keep control model"

        treatment_better = (
            treatment_metrics['directional_accuracy'] > control_metrics['directional_accuracy'] and
            treatment_metrics['mean_error'] < control_metrics['mean_error']
        )

        if treatment_better:
            return "Treatment model is significantly better - consider switching"
        else:
            return "Control model performs better - keep current model"

class DeploymentOrchestrator:
    """Main orchestrator for model deployment"""

    def __init__(self, config: DeploymentConfig):
        self.config = config
        self.load_balancer = LoadBalancer(config)
        self.monitor = ModelMonitor(config)
        self.ab_test_manager = ABTestManager()
        self.request_queue = deque()
        self.is_serving = False
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.logger = logging.getLogger("DeploymentOrchestrator")

    def deploy_model(self, model_path: str, model_id: str, version: str, tier: str = 'production'):
        """Deploy new model version"""
        try:
            # Create and load model server
            server = PythonModelServer(model_id, self.config)
            server.load_model(model_path, version)

            # Add to load balancer
            self.load_balancer.add_server(server, tier)

            self.logger.info(f"Deployed model {model_id} v{version} to {tier} tier")

        except Exception as e:
            self.logger.error(f"Failed to deploy model: {e}")
            raise

    def start_serving(self):
        """Start serving predictions"""
        if self.is_serving:
            return

        self.is_serving = True

        # Start monitoring
        all_servers = []
        for tier_servers in self.load_balancer.servers.values():
            all_servers.extend(tier_servers)
        self.monitor.start_monitoring(all_servers)

        self.logger.info("Started serving predictions")

    def stop_serving(self):
        """Stop serving predictions"""
        self.is_serving = False
        self.monitor.stop_monitoring()
        self.executor.shutdown(wait=True)
        self.logger.info("Stopped serving predictions")

    def predict(self, features: np.ndarray, request_id: str = None) -> PredictionResponse:
        """Make prediction request"""
        if not self.is_serving:
            raise RuntimeError("Deployment not serving")

        request = PredictionRequest(
            request_id=request_id or f"req_{int(time.time()*1000)}",
            features=features,
            timestamp=datetime.now()
        )

        return self.load_balancer.route_request(request)

    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status"""
        return {
            'serving': self.is_serving,
            'timestamp': datetime.now(),
            'tier_health': self.load_balancer.get_tier_health(),
            'metrics_summary': self.monitor.get_metrics_summary(),
            'active_ab_tests': len(self.ab_test_manager.active_tests)
        }

    def create_deployment_report(self) -> str:
        """Create deployment status report"""
        health = self.get_health_status()

        report = ["=== MODEL DEPLOYMENT STATUS ===\n"]
        report.append(f"Serving Status: {'ACTIVE' if health['serving'] else 'INACTIVE'}")
        report.append(f"Timestamp: {health['timestamp']}\n")

        # Tier health
        report.append("TIER HEALTH:")
        for tier, tier_health in health['tier_health'].items():
            status = f"{tier_health['healthy_servers']}/{tier_health['total_servers']} healthy"
            report.append(f"  {tier}: {status} ({tier_health['health_ratio']:.1%})")

        # Metrics summary
        if health['metrics_summary']:
            metrics = health['metrics_summary']
            report.append("\nPERFORMANCE SUMMARY (last hour):")
            report.append(f"  Total Predictions: {metrics['total_predictions']}")
            report.append(f"  Average Latency: {metrics['avg_latency_ms']:.1f}ms")
            report.append(f"  Error Rate: {metrics['avg_error_rate']:.2%}")
            report.append(f"  Throughput: {metrics['avg_throughput_per_second']:.1f}/sec")

        report.append(f"\nActive A/B Tests: {health['active_ab_tests']}")

        return "\n".join(report)