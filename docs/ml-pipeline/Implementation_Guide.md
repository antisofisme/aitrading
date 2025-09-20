# AI Trading System - ML Pipeline Implementation Guide

## Quick Start

This guide provides step-by-step instructions for implementing the ML pipeline for your AI trading system.

## Prerequisites

```bash
# Install required packages
pip install pandas numpy scikit-learn xgboost lightgbm torch transformers ta-lib scipy matplotlib seaborn
```

## 1. Basic Pipeline Setup

### Step 1: Initialize Pipeline Configuration

```python
from src.ml.pipeline_config import PipelineConfig, TradingStrategy

# Choose your trading strategy
config = PipelineConfig(strategy=TradingStrategy.SWING_TRADING)

# Or use predefined configs
from src.ml.pipeline_config import SWING_CONFIG, HFT_CONFIG, POSITION_CONFIG

# View configuration
print(config.to_dict())
```

### Step 2: Prepare Your Data

```python
import pandas as pd
import numpy as np

# Load your market data
df = pd.read_csv('your_market_data.csv', parse_dates=['timestamp'], index_col='timestamp')

# Ensure required columns exist
required_columns = ['open', 'high', 'low', 'close', 'volume']
assert all(col in df.columns for col in required_columns)

# Basic data validation
print(f"Data shape: {df.shape}")
print(f"Date range: {df.index.min()} to {df.index.max()}")
print(f"Missing values: {df.isnull().sum()}")
```

### Step 3: Feature Engineering

```python
from src.ml.feature_engineering import FeatureEngineer

# Initialize feature engineer
feature_engineer = FeatureEngineer(config.feature_config.__dict__)

# Create features
features = feature_engineer.create_features(df)

# Create target variable (next day returns)
target = feature_engineer.create_target(df, target_type='returns', horizon=1)

# Align features and target
common_index = features.index.intersection(target.index)
X = features.loc[common_index].dropna()
y = target.loc[X.index].dropna()

print(f"Features shape: {X.shape}")
print(f"Target shape: {y.shape}")
```

### Step 4: Train Models

```python
from src.ml.models import create_ensemble_from_config
from sklearn.model_selection import train_test_split

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X.values, y.values, test_size=0.2, shuffle=False
)

# Create ensemble model
model_configs = [config.__dict__ for config in config.model_configs]
ensemble = create_ensemble_from_config(model_configs)

# Train ensemble
print("Training ensemble...")
ensemble.fit(X_train, y_train, X_test, y_test)

print("Training completed!")
```

### Step 5: Validate Performance

```python
from src.ml.validation import ValidationFramework

# Initialize validation framework
validator = ValidationFramework(config.validation_config.__dict__)

# Run comprehensive validation
results = validator.comprehensive_validation(
    model=ensemble,
    X=pd.DataFrame(X, index=common_index),
    y=pd.Series(y, index=common_index),
    prices=df['close']
)

# Generate report
report = validator.generate_validation_report(results)
print(report)
```

## 2. Advanced Features

### Continuous Learning Setup

```python
from src.ml.continuous_learning import ContinuousLearningOrchestrator, RetrainingConfig

# Setup continuous learning
retrain_config = RetrainingConfig(
    enable_online_learning=True,
    partial_retrain_frequency="weekly",
    full_retrain_frequency="monthly"
)

orchestrator = ContinuousLearningOrchestrator(retrain_config)

# Register your models
for i, base_model in enumerate(ensemble.base_models):
    orchestrator.register_model(f"model_{i}", base_model)

# Process new data (in production loop)
# orchestrator.process_new_data(new_X, new_y, predictions)
```

### Deployment Setup

```python
from src.ml.deployment import DeploymentOrchestrator, DeploymentConfig

# Setup deployment
deploy_config = DeploymentConfig(
    max_prediction_latency_ms=50,  # For high-frequency trading
    production_traffic_ratio=0.8,
    shadow_traffic_ratio=0.2
)

deployer = DeploymentOrchestrator(deploy_config)

# Deploy model
deployer.deploy_model('models/ensemble_v1.pkl', 'trading_model', 'v1.0')
deployer.start_serving()

# Make predictions
prediction = deployer.predict(new_features)
print(f"Prediction: {prediction.prediction}, Confidence: {prediction.confidence}")
```

## 3. Production Workflow

### Complete Production Pipeline

```python
import logging
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradingMLPipeline:
    def __init__(self, config_path: str = None):
        # Load configuration
        self.config = PipelineConfig(strategy=TradingStrategy.SWING_TRADING)

        # Initialize components
        self.feature_engineer = FeatureEngineer()
        self.validator = ValidationFramework()
        self.orchestrator = None
        self.deployer = None

        # Model storage
        self.current_model = None
        self.model_version = "1.0.0"

    def prepare_data(self, df: pd.DataFrame) -> tuple:
        """Prepare features and targets"""
        logger.info("Preparing features...")

        # Feature engineering
        features = self.feature_engineer.create_features(df)
        target = self.feature_engineer.create_target(df, target_type='returns')

        # Clean and align data
        common_index = features.index.intersection(target.index)
        X = features.loc[common_index].fillna(method='ffill').dropna()
        y = target.loc[X.index].dropna()

        # Feature scaling and selection
        X_scaled = self.feature_engineer.scale_features(X, method='robust')
        X_selected = self.feature_engineer.select_features(X_scaled, y, k=200)

        return X_selected, y

    def train_models(self, X: pd.DataFrame, y: pd.Series):
        """Train ensemble models"""
        logger.info("Training models...")

        # Create ensemble
        model_configs = [config.__dict__ for config in self.config.model_configs]
        self.current_model = create_ensemble_from_config(model_configs)

        # Split data
        split_idx = int(len(X) * 0.8)
        X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]

        # Train
        self.current_model.fit(X_train.values, y_train.values, X_val.values, y_val.values)

        logger.info("Training completed")

    def validate_models(self, X: pd.DataFrame, y: pd.Series, prices: pd.Series):
        """Comprehensive model validation"""
        logger.info("Validating models...")

        results = self.validator.comprehensive_validation(
            model=self.current_model,
            X=X, y=y, prices=prices
        )

        # Log key metrics
        if 'backtest' in results and results['backtest']:
            bt = results['backtest']
            logger.info(f"Backtest Results:")
            logger.info(f"  Sharpe Ratio: {bt.sharpe_ratio:.3f}")
            logger.info(f"  Annual Return: {bt.annual_return:.2%}")
            logger.info(f"  Max Drawdown: {bt.max_drawdown:.2%}")
            logger.info(f"  Win Rate: {bt.win_rate:.2%}")

        return results

    def deploy_to_production(self):
        """Deploy models to production"""
        logger.info("Deploying to production...")

        # Save model
        model_path = f"models/trading_model_{self.model_version}.pkl"
        self.current_model.save(model_path)

        # Setup deployment
        deploy_config = DeploymentConfig()
        self.deployer = DeploymentOrchestrator(deploy_config)

        # Deploy
        self.deployer.deploy_model(model_path, 'trading_model', self.model_version)
        self.deployer.start_serving()

        logger.info("Deployment completed")

    def setup_continuous_learning(self):
        """Setup continuous learning"""
        logger.info("Setting up continuous learning...")

        retrain_config = RetrainingConfig()
        self.orchestrator = ContinuousLearningOrchestrator(retrain_config)

        # Register models
        for i, base_model in enumerate(self.current_model.base_models):
            self.orchestrator.register_model(f"model_{i}", base_model)

        logger.info("Continuous learning setup completed")

    def run_full_pipeline(self, data_path: str):
        """Run complete ML pipeline"""
        logger.info("Starting full ML pipeline...")

        # Load data
        df = pd.read_csv(data_path, parse_dates=['timestamp'], index_col='timestamp')

        # Prepare data
        X, y = self.prepare_data(df)

        # Train models
        self.train_models(X, y)

        # Validate
        validation_results = self.validate_models(X, y, df['close'])

        # Deploy if validation passes
        if self._validation_passes(validation_results):
            self.deploy_to_production()
            self.setup_continuous_learning()
            logger.info("Pipeline completed successfully!")
        else:
            logger.warning("Validation failed - not deploying to production")

    def _validation_passes(self, results: dict) -> bool:
        """Check if validation results meet criteria"""
        if 'backtest' not in results or results['backtest'] is None:
            return False

        bt = results['backtest']

        # Minimum performance criteria
        criteria = {
            'sharpe_ratio': 1.0,
            'max_drawdown': -0.15,  # Maximum 15% drawdown
            'win_rate': 0.45,       # Minimum 45% win rate
            'directional_accuracy': 0.52  # Better than random
        }

        return (
            bt.sharpe_ratio >= criteria['sharpe_ratio'] and
            bt.max_drawdown >= criteria['max_drawdown'] and
            bt.win_rate >= criteria['win_rate'] and
            bt.directional_accuracy >= criteria['directional_accuracy']
        )

# Usage
if __name__ == "__main__":
    pipeline = TradingMLPipeline()
    pipeline.run_full_pipeline('data/market_data.csv')
```

## 4. Monitoring and Maintenance

### Performance Monitoring

```python
from src.ml.metrics import MetricsCalculator

# Setup metrics calculator
metrics_calc = MetricsCalculator(risk_free_rate=0.02)

# Calculate comprehensive metrics
metrics = metrics_calc.calculate_all_metrics(
    y_true=y_test,
    y_pred=predictions,
    returns=strategy_returns,
    benchmark_returns=benchmark_returns
)

# Generate report
report = metrics_calc.create_metric_report(metrics)
print(report)
```

### Health Monitoring

```python
# Monitor deployment health
health_status = deployer.get_health_status()
print(f"System Health: {health_status}")

# Get continuous learning status
if orchestrator:
    health_report = orchestrator.get_model_health_report()
    print(f"Model Health: {health_report}")
```

## 5. Configuration Examples

### High-Frequency Trading Setup

```python
# HFT configuration
hft_config = PipelineConfig(strategy=TradingStrategy.HIGH_FREQUENCY)

# Modify for ultra-low latency
hft_config.deployment_config.max_prediction_latency_ms = 1
hft_config.deployment_config.production_traffic_ratio = 1.0  # No A/B testing

# Use only fast models
hft_config.model_configs = [
    config for config in hft_config.model_configs
    if config.model_type in [ModelType.XGBOOST, ModelType.LIGHTGBM]
]
```

### Research/Analysis Setup

```python
# Research configuration
research_config = PipelineConfig(strategy=TradingStrategy.RESEARCH_ANALYSIS)

# Enable all models and extensive validation
research_config.validation_config.cv_folds = 10
research_config.training_config.hyperopt_trials = 200
research_config.feature_config.max_features = 1000
```

## 6. Troubleshooting

### Common Issues

1. **Memory Issues**
   ```python
   # Reduce feature count
   config.feature_config.max_features = 200

   # Use feature selection
   X_selected = feature_engineer.select_features(X, y, k=100)
   ```

2. **Training Takes Too Long**
   ```python
   # Reduce model complexity
   for model_config in config.model_configs:
       if model_config.model_type == ModelType.XGBOOST:
           model_config.parameters['n_estimators'] = 100
           model_config.parameters['max_depth'] = 4
   ```

3. **Poor Performance**
   ```python
   # Check data quality
   print(f"Missing values: {df.isnull().sum()}")
   print(f"Data distribution: {df.describe()}")

   # Increase training data
   # Use longer lookback period

   # Try different target formulations
   target_volatility = feature_engineer.create_target(df, target_type='volatility')
   target_direction = feature_engineer.create_target(df, target_type='direction')
   ```

4. **Deployment Issues**
   ```python
   # Check model health
   health = deployer.get_health_status()

   # Test with dummy data
   dummy_features = np.zeros((1, X.shape[1]))
   test_pred = deployer.predict(dummy_features)
   ```

## 7. Best Practices

### Data Management
- Always validate data quality before training
- Use forward-looking validation (no data leakage)
- Implement proper train/validation/test splits
- Handle missing data appropriately

### Model Development
- Start with simple models, increase complexity gradually
- Use ensemble methods for robustness
- Implement proper cross-validation
- Monitor for overfitting

### Production Deployment
- Implement gradual rollout (A/B testing)
- Monitor performance continuously
- Have rollback procedures ready
- Use circuit breakers for fault tolerance

### Risk Management
- Set position and exposure limits
- Implement stop-loss mechanisms
- Monitor correlation changes
- Stress test models regularly

This implementation guide provides a solid foundation for building and deploying your AI trading system's ML pipeline. Adjust configurations based on your specific requirements and risk tolerance.