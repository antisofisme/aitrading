"""
AI Model Performance Tracking System
Tracks performance, accuracy, and inference times of ML models
"""

import asyncio
import logging
import time
import json
import pickle
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import asyncpg
import aioredis
from prometheus_client import Histogram, Gauge, Counter
import joblib
from pathlib import Path

# Model Performance Metrics
MODEL_INFERENCE_TIME = Histogram('model_inference_time_seconds', 'Model inference time', ['model_name', 'model_version'])
MODEL_ACCURACY = Gauge('model_accuracy_score', 'Model accuracy', ['model_name', 'model_version'])
MODEL_PREDICTIONS_TOTAL = Counter('model_predictions_total', 'Total predictions', ['model_name', 'model_version', 'status'])
MODEL_DRIFT_SCORE = Gauge('model_drift_score', 'Model drift detection score', ['model_name'])
MODEL_LATENCY_P95 = Gauge('model_latency_p95_ms', 'Model 95th percentile latency in ms', ['model_name'])

@dataclass
class ModelPrediction:
    """Individual model prediction record"""
    model_name: str
    model_version: str
    prediction_id: str
    input_hash: str
    prediction: Any
    confidence: float
    inference_time: float
    timestamp: datetime
    features: Optional[Dict] = None
    actual_outcome: Optional[Any] = None

    def to_dict(self) -> Dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['prediction'] = json.dumps(self.prediction) if not isinstance(self.prediction, (str, int, float)) else self.prediction
        return data

@dataclass
class ModelMetrics:
    """Model performance metrics"""
    model_name: str
    model_version: str
    total_predictions: int
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    avg_inference_time: float
    p95_inference_time: float
    p99_inference_time: float
    drift_score: float
    last_updated: datetime

    def to_dict(self) -> Dict:
        data = asdict(self)
        data['last_updated'] = self.last_updated.isoformat()
        return data

@dataclass
class ModelDriftReport:
    """Model drift detection report"""
    model_name: str
    drift_detected: bool
    drift_score: float
    reference_period: Tuple[datetime, datetime]
    current_period: Tuple[datetime, datetime]
    statistical_tests: Dict[str, float]
    feature_drift: Dict[str, float]
    recommendation: str
    timestamp: datetime

class AIModelTracker:
    """AI Model Performance Tracking System"""

    def __init__(self,
                 redis_url: str = "redis://localhost:6379",
                 db_url: str = "postgresql://user:pass@localhost/aitrading",
                 model_storage_path: str = "/tmp/model_storage"):
        self.redis_url = redis_url
        self.db_url = db_url
        self.model_storage_path = Path(model_storage_path)
        self.model_storage_path.mkdir(exist_ok=True)

        # Connections
        self.redis_client: Optional[aioredis.Redis] = None
        self.db_pool: Optional[asyncpg.Pool] = None

        # Model registry and cache
        self.active_models: Dict[str, Dict] = {}
        self.model_cache: Dict[str, Any] = {}
        self.prediction_buffer: deque = deque(maxlen=10000)
        self.metrics_cache: Dict[str, ModelMetrics] = {}

        # Performance tracking
        self.inference_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.accuracy_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.prediction_outcomes: Dict[str, List[Tuple]] = defaultdict(list)

        # Drift detection
        self.reference_data: Dict[str, pd.DataFrame] = {}
        self.drift_thresholds = {
            'warning': 0.1,
            'critical': 0.2
        }

        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self.monitoring_tasks: List[asyncio.Task] = []

    async def initialize(self):
        """Initialize model tracking system"""
        try:
            # Initialize Redis connection
            self.redis_client = aioredis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()

            # Initialize database connection
            self.db_pool = await asyncpg.create_pool(
                self.db_url,
                min_size=3,
                max_size=10,
                command_timeout=30
            )

            # Initialize database schema
            await self._init_database()

            # Load registered models
            await self._load_registered_models()

            self.logger.info("AI Model Tracker initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize AI Model Tracker: {e}")
            raise

    async def _init_database(self):
        """Initialize database schema"""
        async with self.db_pool.acquire() as conn:
            # Model registry table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS model_registry (
                    model_name VARCHAR(100) PRIMARY KEY,
                    model_version VARCHAR(50) NOT NULL,
                    model_type VARCHAR(50) NOT NULL,
                    model_path TEXT,
                    metadata JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)

            # Model predictions table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS model_predictions (
                    prediction_id VARCHAR(100) PRIMARY KEY,
                    model_name VARCHAR(100) NOT NULL,
                    model_version VARCHAR(50) NOT NULL,
                    input_hash VARCHAR(64) NOT NULL,
                    prediction JSONB NOT NULL,
                    confidence FLOAT,
                    inference_time FLOAT NOT NULL,
                    features JSONB,
                    actual_outcome JSONB,
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    INDEX (model_name, timestamp),
                    INDEX (model_name, model_version, timestamp),
                    FOREIGN KEY (model_name) REFERENCES model_registry(model_name)
                )
            """)

            # Model metrics table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS model_metrics (
                    id SERIAL PRIMARY KEY,
                    model_name VARCHAR(100) NOT NULL,
                    model_version VARCHAR(50) NOT NULL,
                    metric_name VARCHAR(100) NOT NULL,
                    metric_value FLOAT NOT NULL,
                    metadata JSONB,
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    INDEX (model_name, metric_name, timestamp)
                )
            """)

            # Drift detection table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS model_drift_reports (
                    id SERIAL PRIMARY KEY,
                    model_name VARCHAR(100) NOT NULL,
                    drift_detected BOOLEAN NOT NULL,
                    drift_score FLOAT NOT NULL,
                    reference_start TIMESTAMPTZ NOT NULL,
                    reference_end TIMESTAMPTZ NOT NULL,
                    current_start TIMESTAMPTZ NOT NULL,
                    current_end TIMESTAMPTZ NOT NULL,
                    statistical_tests JSONB,
                    feature_drift JSONB,
                    recommendation TEXT,
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    INDEX (model_name, timestamp)
                )
            """)

    async def _load_registered_models(self):
        """Load registered models from database"""
        try:
            async with self.db_pool.acquire() as conn:
                models = await conn.fetch("""
                    SELECT model_name, model_version, model_type, model_path, metadata, is_active
                    FROM model_registry
                    WHERE is_active = TRUE
                """)

                for model in models:
                    self.active_models[model['model_name']] = {
                        'version': model['model_version'],
                        'type': model['model_type'],
                        'path': model['model_path'],
                        'metadata': model['metadata'],
                        'is_active': model['is_active']
                    }

                self.logger.info(f"Loaded {len(self.active_models)} active models")

        except Exception as e:
            self.logger.error(f"Failed to load registered models: {e}")

    async def register_model(self,
                           model_name: str,
                           model_version: str,
                           model_type: str,
                           model_path: Optional[str] = None,
                           metadata: Optional[Dict] = None) -> bool:
        """Register a new model for tracking"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO model_registry (model_name, model_version, model_type, model_path, metadata)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (model_name) DO UPDATE SET
                        model_version = EXCLUDED.model_version,
                        model_type = EXCLUDED.model_type,
                        model_path = EXCLUDED.model_path,
                        metadata = EXCLUDED.metadata,
                        updated_at = NOW()
                """, model_name, model_version, model_type, model_path, json.dumps(metadata) if metadata else None)

            # Update active models
            self.active_models[model_name] = {
                'version': model_version,
                'type': model_type,
                'path': model_path,
                'metadata': metadata,
                'is_active': True
            }

            self.logger.info(f"Registered model: {model_name} v{model_version}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to register model {model_name}: {e}")
            return False

    async def track_prediction(self,
                             model_name: str,
                             prediction_id: str,
                             input_data: Any,
                             prediction: Any,
                             confidence: float = None,
                             inference_time: float = None,
                             features: Dict = None) -> bool:
        """Track a model prediction"""
        try:
            # Generate input hash for tracking
            input_hash = hashlib.md5(str(input_data).encode()).hexdigest()

            # Create prediction record
            prediction_record = ModelPrediction(
                model_name=model_name,
                model_version=self.active_models.get(model_name, {}).get('version', 'unknown'),
                prediction_id=prediction_id,
                input_hash=input_hash,
                prediction=prediction,
                confidence=confidence or 0.0,
                inference_time=inference_time or 0.0,
                timestamp=datetime.utcnow(),
                features=features
            )

            # Add to buffer for batch processing
            self.prediction_buffer.append(prediction_record)

            # Track inference time
            if inference_time:
                self.inference_times[model_name].append(inference_time)
                MODEL_INFERENCE_TIME.labels(
                    model_name=model_name,
                    model_version=prediction_record.model_version
                ).observe(inference_time)

            # Update prediction counter
            MODEL_PREDICTIONS_TOTAL.labels(
                model_name=model_name,
                model_version=prediction_record.model_version,
                status='success'
            ).inc()

            # Cache in Redis for real-time access
            await self.redis_client.hset(
                f"predictions:{model_name}",
                prediction_id,
                json.dumps(prediction_record.to_dict())
            )

            return True

        except Exception as e:
            self.logger.error(f"Failed to track prediction for {model_name}: {e}")
            MODEL_PREDICTIONS_TOTAL.labels(
                model_name=model_name,
                model_version='unknown',
                status='error'
            ).inc()
            return False

    async def update_prediction_outcome(self,
                                      model_name: str,
                                      prediction_id: str,
                                      actual_outcome: Any) -> bool:
        """Update prediction with actual outcome for accuracy calculation"""
        try:
            # Update in database
            async with self.db_pool.acquire() as conn:
                result = await conn.execute("""
                    UPDATE model_predictions
                    SET actual_outcome = $3
                    WHERE model_name = $1 AND prediction_id = $2
                """, model_name, prediction_id, json.dumps(actual_outcome))

            # Get the original prediction for accuracy calculation
            prediction_data = await self.redis_client.hget(f"predictions:{model_name}", prediction_id)
            if prediction_data:
                prediction = json.loads(prediction_data)

                # Store for batch accuracy calculation
                self.prediction_outcomes[model_name].append((
                    prediction['prediction'],
                    actual_outcome,
                    datetime.fromisoformat(prediction['timestamp'])
                ))

            return True

        except Exception as e:
            self.logger.error(f"Failed to update prediction outcome: {e}")
            return False

    async def calculate_model_metrics(self, model_name: str, days: int = 1) -> Optional[ModelMetrics]:
        """Calculate comprehensive model metrics"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)

            async with self.db_pool.acquire() as conn:
                # Get predictions for the period
                predictions = await conn.fetch("""
                    SELECT prediction, actual_outcome, inference_time, confidence
                    FROM model_predictions
                    WHERE model_name = $1
                    AND timestamp BETWEEN $2 AND $3
                    AND actual_outcome IS NOT NULL
                """, model_name, start_time, end_time)

            if not predictions:
                self.logger.warning(f"No predictions found for {model_name} in the last {days} days")
                return None

            # Extract data for metrics calculation
            y_true = []
            y_pred = []
            inference_times = []
            confidences = []

            for pred in predictions:
                try:
                    prediction = json.loads(pred['prediction']) if isinstance(pred['prediction'], str) else pred['prediction']
                    actual = json.loads(pred['actual_outcome']) if isinstance(pred['actual_outcome'], str) else pred['actual_outcome']

                    y_true.append(actual)
                    y_pred.append(prediction)
                    inference_times.append(pred['inference_time'])
                    if pred['confidence']:
                        confidences.append(pred['confidence'])

                except Exception as e:
                    self.logger.warning(f"Skipping prediction due to parsing error: {e}")
                    continue

            if not y_true:
                return None

            # Calculate accuracy metrics
            accuracy = accuracy_score(y_true, y_pred) if len(set(y_true)) > 1 else 0.0

            try:
                precision = precision_score(y_true, y_pred, average='weighted')
                recall = recall_score(y_true, y_pred, average='weighted')
                f1 = f1_score(y_true, y_pred, average='weighted')
            except:
                precision = recall = f1 = 0.0

            # Calculate inference time metrics
            avg_inference_time = np.mean(inference_times)
            p95_inference_time = np.percentile(inference_times, 95)
            p99_inference_time = np.percentile(inference_times, 99)

            # Calculate drift score
            drift_score = await self._calculate_drift_score(model_name)

            # Create metrics object
            metrics = ModelMetrics(
                model_name=model_name,
                model_version=self.active_models.get(model_name, {}).get('version', 'unknown'),
                total_predictions=len(predictions),
                accuracy=accuracy,
                precision=precision,
                recall=recall,
                f1_score=f1,
                avg_inference_time=avg_inference_time,
                p95_inference_time=p95_inference_time,
                p99_inference_time=p99_inference_time,
                drift_score=drift_score,
                last_updated=datetime.utcnow()
            )

            # Update Prometheus metrics
            MODEL_ACCURACY.labels(
                model_name=model_name,
                model_version=metrics.model_version
            ).set(accuracy)

            MODEL_LATENCY_P95.labels(model_name=model_name).set(p95_inference_time * 1000)  # Convert to ms

            # Cache metrics
            self.metrics_cache[model_name] = metrics

            # Store in database
            await self._store_model_metrics(metrics)

            return metrics

        except Exception as e:
            self.logger.error(f"Failed to calculate metrics for {model_name}: {e}")
            return None

    async def _calculate_drift_score(self, model_name: str) -> float:
        """Calculate model drift score using statistical tests"""
        try:
            # Get recent predictions (current period)
            end_time = datetime.utcnow()
            current_start = end_time - timedelta(days=7)

            # Get reference predictions (reference period)
            ref_end = current_start
            ref_start = ref_end - timedelta(days=14)

            async with self.db_pool.acquire() as conn:
                # Get reference period data
                ref_data = await conn.fetch("""
                    SELECT features, prediction, confidence
                    FROM model_predictions
                    WHERE model_name = $1
                    AND timestamp BETWEEN $2 AND $3
                    AND features IS NOT NULL
                """, model_name, ref_start, ref_end)

                # Get current period data
                current_data = await conn.fetch("""
                    SELECT features, prediction, confidence
                    FROM model_predictions
                    WHERE model_name = $1
                    AND timestamp BETWEEN $2 AND $3
                    AND features IS NOT NULL
                """, model_name, current_start, end_time)

            if len(ref_data) < 100 or len(current_data) < 100:
                return 0.0  # Not enough data for drift detection

            # Calculate statistical drift using Kolmogorov-Smirnov test
            from scipy import stats

            # Extract prediction distributions
            ref_predictions = [json.loads(d['prediction']) if isinstance(d['prediction'], str) else d['prediction'] for d in ref_data]
            current_predictions = [json.loads(d['prediction']) if isinstance(d['prediction'], str) else d['prediction'] for d in current_data]

            # Convert to numerical values for KS test
            if all(isinstance(p, (int, float)) for p in ref_predictions + current_predictions):
                ks_stat, p_value = stats.ks_2samp(ref_predictions, current_predictions)
                drift_score = ks_stat
            else:
                # For categorical predictions, use chi-square test
                from collections import Counter
                ref_counts = Counter(ref_predictions)
                current_counts = Counter(current_predictions)

                # Align categories
                all_categories = set(ref_counts.keys()) | set(current_counts.keys())
                ref_freq = [ref_counts.get(cat, 0) for cat in all_categories]
                current_freq = [current_counts.get(cat, 0) for cat in all_categories]

                chi2_stat, p_value = stats.chisquare(current_freq, ref_freq)
                drift_score = min(chi2_stat / 100, 1.0)  # Normalize to 0-1 range

            # Update Prometheus metric
            MODEL_DRIFT_SCORE.labels(model_name=model_name).set(drift_score)

            return drift_score

        except Exception as e:
            self.logger.error(f"Failed to calculate drift score for {model_name}: {e}")
            return 0.0

    async def _store_model_metrics(self, metrics: ModelMetrics):
        """Store model metrics in database"""
        try:
            async with self.db_pool.acquire() as conn:
                metric_values = [
                    (metrics.model_name, metrics.model_version, 'accuracy', metrics.accuracy),
                    (metrics.model_name, metrics.model_version, 'precision', metrics.precision),
                    (metrics.model_name, metrics.model_version, 'recall', metrics.recall),
                    (metrics.model_name, metrics.model_version, 'f1_score', metrics.f1_score),
                    (metrics.model_name, metrics.model_version, 'avg_inference_time', metrics.avg_inference_time),
                    (metrics.model_name, metrics.model_version, 'p95_inference_time', metrics.p95_inference_time),
                    (metrics.model_name, metrics.model_version, 'p99_inference_time', metrics.p99_inference_time),
                    (metrics.model_name, metrics.model_version, 'drift_score', metrics.drift_score),
                    (metrics.model_name, metrics.model_version, 'total_predictions', metrics.total_predictions)
                ]

                await conn.executemany("""
                    INSERT INTO model_metrics (model_name, model_version, metric_name, metric_value, timestamp)
                    VALUES ($1, $2, $3, $4, NOW())
                """, metric_values)

        except Exception as e:
            self.logger.error(f"Failed to store model metrics: {e}")

    async def detect_model_drift(self, model_name: str) -> Optional[ModelDriftReport]:
        """Comprehensive model drift detection"""
        try:
            drift_score = await self._calculate_drift_score(model_name)

            # Determine if drift is detected
            drift_detected = drift_score > self.drift_thresholds['warning']

            # Generate recommendation
            if drift_score > self.drift_thresholds['critical']:
                recommendation = "CRITICAL: Immediate model retraining recommended"
            elif drift_score > self.drift_thresholds['warning']:
                recommendation = "WARNING: Monitor model performance closely, consider retraining"
            else:
                recommendation = "Model performance is stable"

            # Create drift report
            end_time = datetime.utcnow()
            current_start = end_time - timedelta(days=7)
            ref_end = current_start
            ref_start = ref_end - timedelta(days=14)

            report = ModelDriftReport(
                model_name=model_name,
                drift_detected=drift_detected,
                drift_score=drift_score,
                reference_period=(ref_start, ref_end),
                current_period=(current_start, end_time),
                statistical_tests={'ks_statistic': drift_score},
                feature_drift={},  # Would implement feature-level drift detection
                recommendation=recommendation,
                timestamp=datetime.utcnow()
            )

            # Store drift report
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO model_drift_reports
                    (model_name, drift_detected, drift_score, reference_start, reference_end,
                     current_start, current_end, statistical_tests, recommendation)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """, model_name, drift_detected, drift_score, ref_start, ref_end,
                current_start, end_time, json.dumps(report.statistical_tests), recommendation)

            return report

        except Exception as e:
            self.logger.error(f"Failed to detect drift for {model_name}: {e}")
            return None

    async def start_monitoring(self):
        """Start model performance monitoring"""
        if self.is_running:
            return

        self.is_running = True

        # Start monitoring tasks
        tasks = [
            self._process_prediction_buffer(),
            self._update_model_metrics(),
            self._check_model_drift(),
            self._cleanup_old_data()
        ]

        self.monitoring_tasks = [asyncio.create_task(task) for task in tasks]

        self.logger.info("AI Model monitoring started")

    async def stop_monitoring(self):
        """Stop model performance monitoring"""
        self.is_running = False

        # Cancel all tasks
        for task in self.monitoring_tasks:
            task.cancel()

        await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
        self.monitoring_tasks.clear()

        if self.redis_client:
            await self.redis_client.close()
        if self.db_pool:
            await self.db_pool.close()

        self.logger.info("AI Model monitoring stopped")

    async def _process_prediction_buffer(self):
        """Process prediction buffer and store in database"""
        while self.is_running:
            try:
                if self.prediction_buffer:
                    batch = []
                    for _ in range(min(100, len(self.prediction_buffer))):
                        if self.prediction_buffer:
                            batch.append(self.prediction_buffer.popleft())

                    if batch:
                        await self._store_predictions_batch(batch)

                await asyncio.sleep(5)

            except Exception as e:
                self.logger.error(f"Error processing prediction buffer: {e}")
                await asyncio.sleep(5)

    async def _store_predictions_batch(self, predictions: List[ModelPrediction]):
        """Store batch of predictions in database"""
        try:
            async with self.db_pool.acquire() as conn:
                values = []
                for pred in predictions:
                    values.append((
                        pred.prediction_id,
                        pred.model_name,
                        pred.model_version,
                        pred.input_hash,
                        json.dumps(pred.prediction),
                        pred.confidence,
                        pred.inference_time,
                        json.dumps(pred.features) if pred.features else None,
                        json.dumps(pred.actual_outcome) if pred.actual_outcome else None,
                        pred.timestamp
                    ))

                await conn.executemany("""
                    INSERT INTO model_predictions
                    (prediction_id, model_name, model_version, input_hash, prediction,
                     confidence, inference_time, features, actual_outcome, timestamp)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    ON CONFLICT (prediction_id) DO NOTHING
                """, values)

        except Exception as e:
            self.logger.error(f"Failed to store predictions batch: {e}")

    async def _update_model_metrics(self):
        """Periodically update model metrics"""
        while self.is_running:
            try:
                for model_name in self.active_models.keys():
                    await self.calculate_model_metrics(model_name)

                await asyncio.sleep(300)  # Update every 5 minutes

            except Exception as e:
                self.logger.error(f"Error updating model metrics: {e}")
                await asyncio.sleep(60)

    async def _check_model_drift(self):
        """Periodically check for model drift"""
        while self.is_running:
            try:
                for model_name in self.active_models.keys():
                    await self.detect_model_drift(model_name)

                await asyncio.sleep(3600)  # Check every hour

            except Exception as e:
                self.logger.error(f"Error checking model drift: {e}")
                await asyncio.sleep(600)

    async def _cleanup_old_data(self):
        """Cleanup old prediction data"""
        while self.is_running:
            try:
                cutoff_date = datetime.utcnow() - timedelta(days=90)

                async with self.db_pool.acquire() as conn:
                    # Delete old predictions
                    deleted = await conn.execute("""
                        DELETE FROM model_predictions
                        WHERE timestamp < $1
                    """, cutoff_date)

                    # Delete old metrics
                    await conn.execute("""
                        DELETE FROM model_metrics
                        WHERE timestamp < $1
                    """, cutoff_date)

                self.logger.info(f"Cleaned up old prediction data")

                await asyncio.sleep(86400)  # Cleanup daily

            except Exception as e:
                self.logger.error(f"Error during cleanup: {e}")
                await asyncio.sleep(3600)

    async def get_model_summary(self) -> Dict[str, Any]:
        """Get summary of all tracked models"""
        try:
            summary = {
                "total_models": len(self.active_models),
                "models": {}
            }

            for model_name in self.active_models.keys():
                metrics = self.metrics_cache.get(model_name)
                if metrics:
                    summary["models"][model_name] = metrics.to_dict()
                else:
                    # Get basic info
                    summary["models"][model_name] = {
                        "model_name": model_name,
                        "version": self.active_models[model_name]['version'],
                        "type": self.active_models[model_name]['type'],
                        "status": "active"
                    }

            return summary

        except Exception as e:
            self.logger.error(f"Error generating model summary: {e}")
            return {"error": str(e)}

# Global model tracker instance
_tracker_instance: Optional[AIModelTracker] = None

async def get_model_tracker() -> AIModelTracker:
    """Get global model tracker instance"""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = AIModelTracker()
        await _tracker_instance.initialize()
    return _tracker_instance