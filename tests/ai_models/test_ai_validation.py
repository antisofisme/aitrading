"""
AI Model Validation and Testing Framework
Comprehensive testing for ML models used in trading
"""

import numpy as np
import pandas as pd
import pytest
import joblib
import json
import time
import logging
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import cross_val_score, TimeSeriesSplit
import tensorflow as tf
import torch
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ModelPerformanceMetrics:
    """Container for model performance metrics"""
    model_name: str
    model_type: str  # 'classification', 'regression', 'timeseries'
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    mse: Optional[float] = None
    mae: Optional[float] = None
    r2_score: Optional[float] = None
    prediction_latency_ms: float = 0
    training_time_seconds: float = 0
    memory_usage_mb: float = 0
    inference_throughput: float = 0  # predictions per second
    validation_passed: bool = False
    error_message: str = None

@dataclass
class BacktestResult:
    """Container for backtesting results"""
    strategy_name: str
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    average_trade_duration: float
    volatility: float
    start_date: datetime
    end_date: datetime
    final_portfolio_value: float

class AIModelValidator:
    """Comprehensive AI model validation and testing framework"""

    def __init__(self, models_directory: str = "models/"):
        self.models_directory = models_directory
        self.test_results: List[ModelPerformanceMetrics] = []
        self.validation_thresholds = {
            'min_accuracy': 0.70,
            'min_precision': 0.65,
            'min_recall': 0.60,
            'max_prediction_latency_ms': 100,
            'min_r2_score': 0.60,
            'max_mse': 0.1,
            'min_throughput': 1000  # predictions per second
        }

    def generate_synthetic_market_data(self, n_samples: int = 10000) -> pd.DataFrame:
        """Generate synthetic market data for testing"""
        np.random.seed(42)

        # Generate time series
        dates = pd.date_range(start='2020-01-01', periods=n_samples, freq='1min')

        # Generate realistic price data with trends and volatility
        price = 100.0
        prices = []
        volumes = []

        for i in range(n_samples):
            # Random walk with drift
            price_change = np.random.normal(0, 0.001) + 0.00001  # Small upward drift
            price *= (1 + price_change)
            prices.append(price)

            # Volume with some correlation to price volatility
            volume = np.random.exponential(1000) * (1 + abs(price_change) * 100)
            volumes.append(volume)

        df = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.002))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.002))) for p in prices],
            'close': prices,
            'volume': volumes
        })

        # Add technical indicators
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['rsi'] = self._calculate_rsi(df['close'])
        df['volatility'] = df['close'].rolling(window=20).std()

        # Generate target variables for different model types
        df['price_direction'] = (df['close'].shift(-1) > df['close']).astype(int)  # Classification
        df['future_return'] = (df['close'].shift(-1) / df['close'] - 1)  # Regression

        return df.dropna()

    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def test_classification_model(self, model, model_name: str, X_test: np.ndarray, y_test: np.ndarray) -> ModelPerformanceMetrics:
        """Test classification model performance"""
        logger.info(f"Testing classification model: {model_name}")

        try:
            # Prediction latency test
            start_time = time.time()
            predictions = model.predict(X_test[:100])  # Test on 100 samples
            prediction_time = (time.time() - start_time) * 1000

            # Full predictions for metrics
            start_time = time.time()
            full_predictions = model.predict(X_test)
            total_prediction_time = time.time() - start_time

            # Calculate metrics
            accuracy = accuracy_score(y_test, full_predictions)
            precision = precision_score(y_test, full_predictions, average='weighted', zero_division=0)
            recall = recall_score(y_test, full_predictions, average='weighted', zero_division=0)
            f1 = f1_score(y_test, full_predictions, average='weighted', zero_division=0)

            # Throughput calculation
            throughput = len(X_test) / total_prediction_time

            # Validation check
            validation_passed = (
                accuracy >= self.validation_thresholds['min_accuracy'] and
                precision >= self.validation_thresholds['min_precision'] and
                recall >= self.validation_thresholds['min_recall'] and
                prediction_time <= self.validation_thresholds['max_prediction_latency_ms'] and
                throughput >= self.validation_thresholds['min_throughput']
            )

            metrics = ModelPerformanceMetrics(
                model_name=model_name,
                model_type='classification',
                accuracy=accuracy,
                precision=precision,
                recall=recall,
                f1_score=f1,
                prediction_latency_ms=prediction_time,
                inference_throughput=throughput,
                validation_passed=validation_passed
            )

            logger.info(f"Classification results for {model_name}:")
            logger.info(f"  Accuracy: {accuracy:.3f}")
            logger.info(f"  Precision: {precision:.3f}")
            logger.info(f"  Recall: {recall:.3f}")
            logger.info(f"  F1-Score: {f1:.3f}")
            logger.info(f"  Latency: {prediction_time:.2f}ms")
            logger.info(f"  Throughput: {throughput:.0f} pred/s")
            logger.info(f"  Validation: {'✅ PASS' if validation_passed else '❌ FAIL'}")

            return metrics

        except Exception as e:
            logger.error(f"❌ Error testing {model_name}: {str(e)}")
            return ModelPerformanceMetrics(
                model_name=model_name,
                model_type='classification',
                validation_passed=False,
                error_message=str(e)
            )

    def test_regression_model(self, model, model_name: str, X_test: np.ndarray, y_test: np.ndarray) -> ModelPerformanceMetrics:
        """Test regression model performance"""
        logger.info(f"Testing regression model: {model_name}")

        try:
            # Prediction latency test
            start_time = time.time()
            predictions = model.predict(X_test[:100])
            prediction_time = (time.time() - start_time) * 1000

            # Full predictions for metrics
            start_time = time.time()
            full_predictions = model.predict(X_test)
            total_prediction_time = time.time() - start_time

            # Calculate metrics
            mse = mean_squared_error(y_test, full_predictions)
            mae = mean_absolute_error(y_test, full_predictions)
            r2 = r2_score(y_test, full_predictions)

            # Throughput calculation
            throughput = len(X_test) / total_prediction_time

            # Validation check
            validation_passed = (
                r2 >= self.validation_thresholds['min_r2_score'] and
                mse <= self.validation_thresholds['max_mse'] and
                prediction_time <= self.validation_thresholds['max_prediction_latency_ms'] and
                throughput >= self.validation_thresholds['min_throughput']
            )

            metrics = ModelPerformanceMetrics(
                model_name=model_name,
                model_type='regression',
                mse=mse,
                mae=mae,
                r2_score=r2,
                prediction_latency_ms=prediction_time,
                inference_throughput=throughput,
                validation_passed=validation_passed
            )

            logger.info(f"Regression results for {model_name}:")
            logger.info(f"  MSE: {mse:.4f}")
            logger.info(f"  MAE: {mae:.4f}")
            logger.info(f"  R²: {r2:.3f}")
            logger.info(f"  Latency: {prediction_time:.2f}ms")
            logger.info(f"  Throughput: {throughput:.0f} pred/s")
            logger.info(f"  Validation: {'✅ PASS' if validation_passed else '❌ FAIL'}")

            return metrics

        except Exception as e:
            logger.error(f"❌ Error testing {model_name}: {str(e)}")
            return ModelPerformanceMetrics(
                model_name=model_name,
                model_type='regression',
                validation_passed=False,
                error_message=str(e)
            )

    def test_deep_learning_model(self, model_path: str, model_name: str, X_test: np.ndarray, y_test: np.ndarray) -> ModelPerformanceMetrics:
        """Test TensorFlow/Keras deep learning model"""
        logger.info(f"Testing deep learning model: {model_name}")

        try:
            # Load model
            if model_path.endswith('.h5'):
                model = tf.keras.models.load_model(model_path)
            else:
                # Assume it's a SavedModel format
                model = tf.saved_model.load(model_path)

            # Prediction latency test
            start_time = time.time()
            predictions = model.predict(X_test[:100])
            prediction_time = (time.time() - start_time) * 1000

            # Full predictions
            start_time = time.time()
            full_predictions = model.predict(X_test)
            total_prediction_time = time.time() - start_time

            # Determine if classification or regression based on output shape
            if len(full_predictions.shape) > 1 and full_predictions.shape[1] > 1:
                # Multi-class classification
                predicted_classes = np.argmax(full_predictions, axis=1)
                accuracy = accuracy_score(y_test, predicted_classes)

                metrics = ModelPerformanceMetrics(
                    model_name=model_name,
                    model_type='deep_learning_classification',
                    accuracy=accuracy,
                    prediction_latency_ms=prediction_time,
                    inference_throughput=len(X_test) / total_prediction_time,
                    validation_passed=accuracy >= self.validation_thresholds['min_accuracy']
                )
            else:
                # Regression
                if len(full_predictions.shape) > 1:
                    full_predictions = full_predictions.flatten()

                mse = mean_squared_error(y_test, full_predictions)
                r2 = r2_score(y_test, full_predictions)

                metrics = ModelPerformanceMetrics(
                    model_name=model_name,
                    model_type='deep_learning_regression',
                    mse=mse,
                    r2_score=r2,
                    prediction_latency_ms=prediction_time,
                    inference_throughput=len(X_test) / total_prediction_time,
                    validation_passed=r2 >= self.validation_thresholds['min_r2_score']
                )

            logger.info(f"Deep learning model {model_name} tested successfully")
            return metrics

        except Exception as e:
            logger.error(f"❌ Error testing deep learning model {model_name}: {str(e)}")
            return ModelPerformanceMetrics(
                model_name=model_name,
                model_type='deep_learning',
                validation_passed=False,
                error_message=str(e)
            )

    def test_model_robustness(self, model, X_test: np.ndarray) -> Dict[str, float]:
        """Test model robustness with noise injection"""
        logger.info("Testing model robustness...")

        robustness_results = {}

        try:
            # Original predictions
            original_predictions = model.predict(X_test)

            # Test with different noise levels
            noise_levels = [0.01, 0.05, 0.10, 0.20]

            for noise_level in noise_levels:
                # Add Gaussian noise
                noise = np.random.normal(0, noise_level, X_test.shape)
                noisy_X = X_test + noise

                # Get predictions on noisy data
                noisy_predictions = model.predict(noisy_X)

                # Calculate prediction stability (correlation)
                if len(original_predictions.shape) > 1:
                    stability = np.corrcoef(original_predictions.flatten(), noisy_predictions.flatten())[0, 1]
                else:
                    stability = np.corrcoef(original_predictions, noisy_predictions)[0, 1]

                robustness_results[f'noise_{noise_level}'] = stability

            return robustness_results

        except Exception as e:
            logger.error(f"Robustness test failed: {str(e)}")
            return {}

    def run_comprehensive_model_validation(self) -> Dict[str, Any]:
        """Run comprehensive validation on all available models"""
        logger.info("🚀 Starting comprehensive AI model validation...")

        # Generate test data
        market_data = self.generate_synthetic_market_data(5000)

        # Prepare features and targets
        feature_columns = ['sma_20', 'sma_50', 'rsi', 'volatility', 'volume']
        X = market_data[feature_columns].fillna(0).values
        y_classification = market_data['price_direction'].values
        y_regression = market_data['future_return'].values

        # Split data
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_class_train, y_class_test = y_classification[:split_idx], y_classification[split_idx:]
        y_reg_train, y_reg_test = y_regression[:split_idx], y_regression[split_idx:]

        # Test simple models (for demonstration)
        from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
        from sklearn.linear_model import LogisticRegression, LinearRegression

        models_to_test = [
            ('RandomForest_Classifier', RandomForestClassifier(n_estimators=100, random_state=42), 'classification'),
            ('RandomForest_Regressor', RandomForestRegressor(n_estimators=100, random_state=42), 'regression'),
            ('LogisticRegression', LogisticRegression(random_state=42), 'classification'),
            ('LinearRegression', LinearRegression(), 'regression')
        ]

        # Train and test models
        for model_name, model, model_type in models_to_test:
            logger.info(f"Training and testing {model_name}...")

            try:
                # Train model
                start_time = time.time()
                if model_type == 'classification':
                    model.fit(X_train, y_class_train)
                    metrics = self.test_classification_model(model, model_name, X_test, y_class_test)
                else:
                    model.fit(X_train, y_reg_train)
                    metrics = self.test_regression_model(model, model_name, X_test, y_reg_test)

                training_time = time.time() - start_time
                metrics.training_time_seconds = training_time

                # Test robustness
                robustness = self.test_model_robustness(model, X_test)

                self.test_results.append(metrics)

                logger.info(f"Training time: {training_time:.2f}s")
                logger.info(f"Robustness scores: {robustness}")

            except Exception as e:
                logger.error(f"Failed to test {model_name}: {str(e)}")

        # Calculate overall validation results
        total_models = len(self.test_results)
        passed_models = sum(1 for result in self.test_results if result.validation_passed)
        success_rate = passed_models / total_models if total_models > 0 else 0

        # Performance summary
        avg_latency = np.mean([r.prediction_latency_ms for r in self.test_results if r.prediction_latency_ms > 0])
        avg_throughput = np.mean([r.inference_throughput for r in self.test_results if r.inference_throughput > 0])

        logger.info("\n" + "="*60)
        logger.info("AI MODEL VALIDATION RESULTS")
        logger.info("="*60)

        for result in self.test_results:
            status = "✅ PASS" if result.validation_passed else "❌ FAIL"
            logger.info(f"{result.model_name} ({result.model_type}): {status}")

        logger.info(f"\nOverall Validation Rate: {success_rate:.1%}")
        logger.info(f"Models Passed: {passed_models}/{total_models}")
        logger.info(f"Average Prediction Latency: {avg_latency:.2f}ms")
        logger.info(f"Average Throughput: {avg_throughput:.0f} pred/s")

        return {
            'validation_results': self.test_results,
            'success_rate': success_rate,
            'total_models': total_models,
            'passed_models': passed_models,
            'average_latency_ms': avg_latency,
            'average_throughput': avg_throughput
        }

# Pytest fixtures and test functions
@pytest.fixture
def ai_validator():
    """Fixture for AI model validator"""
    return AIModelValidator()

@pytest.fixture
def sample_data():
    """Fixture for sample market data"""
    validator = AIModelValidator()
    return validator.generate_synthetic_market_data(1000)

def test_synthetic_data_generation(ai_validator):
    """Test synthetic data generation"""
    data = ai_validator.generate_synthetic_market_data(100)
    assert len(data) > 0
    assert 'close' in data.columns
    assert 'price_direction' in data.columns
    assert not data.isnull().all().any()

def test_classification_model_validation(ai_validator, sample_data):
    """Test classification model validation"""
    from sklearn.ensemble import RandomForestClassifier

    feature_columns = ['sma_20', 'sma_50', 'rsi', 'volatility']
    X = sample_data[feature_columns].fillna(0).values
    y = sample_data['price_direction'].values

    # Train simple model
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X[:800], y[:800])

    # Test validation
    metrics = ai_validator.test_classification_model(model, "TestModel", X[800:], y[800:])
    assert metrics.model_name == "TestModel"
    assert metrics.accuracy is not None
    assert metrics.prediction_latency_ms > 0

def test_regression_model_validation(ai_validator, sample_data):
    """Test regression model validation"""
    from sklearn.ensemble import RandomForestRegressor

    feature_columns = ['sma_20', 'sma_50', 'rsi', 'volatility']
    X = sample_data[feature_columns].fillna(0).values
    y = sample_data['future_return'].values

    # Train simple model
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    model.fit(X[:800], y[:800])

    # Test validation
    metrics = ai_validator.test_regression_model(model, "TestRegressor", X[800:], y[800:])
    assert metrics.model_name == "TestRegressor"
    assert metrics.mse is not None
    assert metrics.r2_score is not None

def test_model_robustness(ai_validator, sample_data):
    """Test model robustness testing"""
    from sklearn.ensemble import RandomForestClassifier

    feature_columns = ['sma_20', 'sma_50', 'rsi', 'volatility']
    X = sample_data[feature_columns].fillna(0).values
    y = sample_data['price_direction'].values

    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X[:800], y[:800])

    robustness = ai_validator.test_model_robustness(model, X[800:])
    assert isinstance(robustness, dict)
    assert len(robustness) > 0

@pytest.mark.integration
def test_comprehensive_validation(ai_validator):
    """Test comprehensive model validation suite"""
    results = ai_validator.run_comprehensive_model_validation()

    assert 'validation_results' in results
    assert 'success_rate' in results
    assert results['total_models'] > 0
    assert 0 <= results['success_rate'] <= 1

if __name__ == "__main__":
    async def main():
        validator = AIModelValidator()
        results = validator.run_comprehensive_model_validation()

        # Store results
        import json
        with open('/tmp/ai_model_validation_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\nAI model validation complete. Success rate: {results['success_rate']:.1%}")

    import asyncio
    asyncio.run(main())