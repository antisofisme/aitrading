"""
AI Trading System - ML Pipeline Configuration
============================================

This module contains configuration settings for the machine learning pipeline,
including model parameters, feature engineering settings, and deployment configurations.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

class ModelType(Enum):
    """Supported model types in the pipeline"""
    XGBOOST = "xgboost"
    LIGHTGBM = "lightgbm"
    RANDOM_FOREST = "random_forest"
    LSTM = "lstm"
    TRANSFORMER = "transformer"
    CNN = "cnn"
    META_LEARNER = "meta_learner"

class TradingStrategy(Enum):
    """Trading strategy types with different latency requirements"""
    HIGH_FREQUENCY = "high_frequency"  # <1ms
    SWING_TRADING = "swing_trading"    # <1s
    POSITION_TRADING = "position_trading"  # <10s
    RESEARCH_ANALYSIS = "research_analysis"  # >1min

@dataclass
class ModelConfig:
    """Configuration for individual models"""
    model_type: ModelType
    parameters: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    enabled: bool = True
    max_training_time: int = 3600  # seconds
    memory_limit: str = "4GB"

@dataclass
class FeatureConfig:
    """Feature engineering configuration"""
    # Technical indicators
    price_features: List[str] = field(default_factory=lambda: [
        "sma_5", "sma_10", "sma_20", "sma_50", "sma_200",
        "ema_12", "ema_26", "ema_50",
        "rsi_14", "rsi_21",
        "macd", "macd_signal", "macd_histogram",
        "bb_upper", "bb_middle", "bb_lower",
        "atr_14", "atr_21"
    ])

    volume_features: List[str] = field(default_factory=lambda: [
        "volume_sma_10", "volume_sma_20",
        "vwap", "vwap_deviation",
        "accumulation_distribution",
        "on_balance_volume",
        "volume_price_trend"
    ])

    volatility_features: List[str] = field(default_factory=lambda: [
        "realized_volatility_5", "realized_volatility_10", "realized_volatility_20",
        "garch_volatility", "volatility_cone_percentile",
        "high_low_ratio", "close_to_close_volatility"
    ])

    # Market microstructure
    microstructure_features: List[str] = field(default_factory=lambda: [
        "bid_ask_spread", "relative_spread",
        "order_imbalance", "market_depth",
        "trade_size_avg", "trade_frequency",
        "market_impact_estimate"
    ])

    # Cross-asset features
    cross_asset_features: List[str] = field(default_factory=lambda: [
        "sp500_correlation", "vix_level", "vix_term_structure",
        "dollar_index", "sector_rotation_score",
        "yield_curve_slope", "credit_spread"
    ])

    # Alternative data
    alternative_features: List[str] = field(default_factory=lambda: [
        "news_sentiment_score", "social_sentiment_score",
        "earnings_surprise", "analyst_revisions",
        "insider_trading_activity", "institutional_flow"
    ])

    # Temporal features
    temporal_features: List[str] = field(default_factory=lambda: [
        "hour_of_day", "day_of_week", "month_of_year",
        "is_market_open", "session_indicator",
        "is_holiday", "is_earnings_season", "is_fomc_week"
    ])

    # Feature engineering parameters
    lookback_windows: List[int] = field(default_factory=lambda: [5, 10, 20, 50, 200])
    rolling_stats: List[str] = field(default_factory=lambda: ["mean", "std", "min", "max", "skew", "kurt"])
    lag_features: List[int] = field(default_factory=lambda: [1, 2, 3, 5, 10])

    # Feature selection
    max_features: int = 500
    feature_importance_threshold: float = 0.001
    correlation_threshold: float = 0.95

@dataclass
class TrainingConfig:
    """Training configuration for the pipeline"""
    # Data splitting
    train_ratio: float = 0.7
    validation_ratio: float = 0.15
    test_ratio: float = 0.15

    # Time series cross-validation
    cv_folds: int = 5
    cv_gap: int = 1  # Gap between train and validation sets
    min_train_samples: int = 1000

    # Retraining schedule
    daily_incremental: bool = True
    weekly_partial_retrain: bool = True
    monthly_full_retrain: bool = True

    # Early stopping
    early_stopping_rounds: int = 50
    validation_metric: str = "sharpe_ratio"

    # Hyperparameter optimization
    hyperopt_trials: int = 100
    hyperopt_timeout: int = 3600  # seconds

@dataclass
class ValidationConfig:
    """Validation and backtesting configuration"""
    # Backtesting parameters
    initial_capital: float = 1000000.0
    transaction_costs: float = 0.001  # 0.1%
    slippage: float = 0.0005  # 0.05%

    # Walk-forward analysis
    walk_forward_window: int = 252  # Trading days
    walk_forward_step: int = 21  # Rebalancing frequency

    # Out-of-sample testing
    oos_period_months: int = 6
    stress_test_periods: List[str] = field(default_factory=lambda: [
        "2008-09-01:2009-03-01",  # Financial crisis
        "2020-02-01:2020-04-01",  # COVID crash
        "2022-01-01:2022-12-31"   # Rate hike cycle
    ])

    # Performance metrics
    risk_free_rate: float = 0.02
    benchmark_symbol: str = "SPY"
    confidence_levels: List[float] = field(default_factory=lambda: [0.95, 0.99])

@dataclass
class DeploymentConfig:
    """Deployment and serving configuration"""
    # Model serving
    max_prediction_latency_ms: int = 100
    batch_size: int = 1000
    model_cache_size: int = 10

    # Load balancing
    production_traffic_ratio: float = 0.7
    shadow_traffic_ratio: float = 0.2
    experimental_traffic_ratio: float = 0.1

    # Monitoring
    performance_check_frequency: int = 3600  # seconds
    drift_detection_window: int = 7  # days
    alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "sharpe_ratio_drop": 0.5,
        "max_drawdown_increase": 0.1,
        "prediction_latency_ms": 200,
        "error_rate": 0.05
    })

    # Auto-scaling
    cpu_scale_threshold: float = 0.8
    memory_scale_threshold: float = 0.8
    min_replicas: int = 2
    max_replicas: int = 10

class PipelineConfig:
    """Main configuration class for the ML pipeline"""

    def __init__(self, strategy: TradingStrategy = TradingStrategy.SWING_TRADING):
        self.strategy = strategy
        self.feature_config = FeatureConfig()
        self.training_config = TrainingConfig()
        self.validation_config = ValidationConfig()
        self.deployment_config = DeploymentConfig()

        # Model configurations based on strategy
        self.model_configs = self._get_model_configs_for_strategy(strategy)

    def _get_model_configs_for_strategy(self, strategy: TradingStrategy) -> List[ModelConfig]:
        """Get optimal model configurations for trading strategy"""

        if strategy == TradingStrategy.HIGH_FREQUENCY:
            return [
                ModelConfig(
                    model_type=ModelType.XGBOOST,
                    parameters={
                        'objective': 'reg:squarederror',
                        'max_depth': 4,
                        'learning_rate': 0.15,
                        'subsample': 0.8,
                        'colsample_bytree': 0.8,
                        'n_estimators': 100,
                        'tree_method': 'gpu_hist'  # GPU acceleration
                    },
                    weight=0.6
                ),
                ModelConfig(
                    model_type=ModelType.LIGHTGBM,
                    parameters={
                        'objective': 'regression',
                        'metric': 'rmse',
                        'boosting_type': 'gbdt',
                        'num_leaves': 15,
                        'learning_rate': 0.1,
                        'n_estimators': 100,
                        'device': 'gpu'
                    },
                    weight=0.4
                )
            ]

        elif strategy == TradingStrategy.SWING_TRADING:
            return [
                ModelConfig(
                    model_type=ModelType.XGBOOST,
                    parameters={
                        'objective': 'reg:squarederror',
                        'max_depth': 6,
                        'learning_rate': 0.1,
                        'subsample': 0.8,
                        'colsample_bytree': 0.8,
                        'n_estimators': 500
                    },
                    weight=0.35
                ),
                ModelConfig(
                    model_type=ModelType.RANDOM_FOREST,
                    parameters={
                        'n_estimators': 300,
                        'max_depth': 10,
                        'min_samples_split': 5,
                        'min_samples_leaf': 2,
                        'bootstrap': True,
                        'n_jobs': -1
                    },
                    weight=0.35
                ),
                ModelConfig(
                    model_type=ModelType.LSTM,
                    parameters={
                        'hidden_size': 128,
                        'num_layers': 2,
                        'dropout': 0.2,
                        'sequence_length': 20,
                        'learning_rate': 0.001,
                        'batch_size': 64,
                        'epochs': 100
                    },
                    weight=0.3
                )
            ]

        elif strategy == TradingStrategy.POSITION_TRADING:
            return [
                ModelConfig(
                    model_type=ModelType.XGBOOST,
                    parameters={
                        'objective': 'reg:squarederror',
                        'max_depth': 8,
                        'learning_rate': 0.05,
                        'subsample': 0.9,
                        'colsample_bytree': 0.9,
                        'n_estimators': 1000
                    },
                    weight=0.25
                ),
                ModelConfig(
                    model_type=ModelType.LSTM,
                    parameters={
                        'hidden_size': 256,
                        'num_layers': 3,
                        'dropout': 0.3,
                        'sequence_length': 50,
                        'learning_rate': 0.0005,
                        'batch_size': 32,
                        'epochs': 200
                    },
                    weight=0.25
                ),
                ModelConfig(
                    model_type=ModelType.TRANSFORMER,
                    parameters={
                        'd_model': 256,
                        'nhead': 8,
                        'num_layers': 6,
                        'dim_feedforward': 1024,
                        'dropout': 0.1,
                        'sequence_length': 100,
                        'learning_rate': 0.0001,
                        'batch_size': 16,
                        'epochs': 150
                    },
                    weight=0.25
                ),
                ModelConfig(
                    model_type=ModelType.CNN,
                    parameters={
                        'input_channels': 50,
                        'sequence_length': 60,
                        'kernel_sizes': [3, 5, 7],
                        'filters': [64, 128, 256],
                        'dropout': 0.2,
                        'learning_rate': 0.001,
                        'batch_size': 32,
                        'epochs': 100
                    },
                    weight=0.25
                )
            ]

        else:  # RESEARCH_ANALYSIS
            return [
                ModelConfig(
                    model_type=ModelType.TRANSFORMER,
                    parameters={
                        'd_model': 512,
                        'nhead': 16,
                        'num_layers': 12,
                        'dim_feedforward': 2048,
                        'dropout': 0.1,
                        'sequence_length': 200,
                        'learning_rate': 0.00005,
                        'batch_size': 8,
                        'epochs': 300
                    },
                    weight=0.4
                ),
                ModelConfig(
                    model_type=ModelType.LSTM,
                    parameters={
                        'hidden_size': 512,
                        'num_layers': 4,
                        'dropout': 0.3,
                        'sequence_length': 100,
                        'learning_rate': 0.0001,
                        'batch_size': 16,
                        'epochs': 500
                    },
                    weight=0.3
                ),
                ModelConfig(
                    model_type=ModelType.XGBOOST,
                    parameters={
                        'objective': 'reg:squarederror',
                        'max_depth': 10,
                        'learning_rate': 0.03,
                        'subsample': 0.9,
                        'colsample_bytree': 0.9,
                        'n_estimators': 2000
                    },
                    weight=0.3
                )
            ]

    def get_ensemble_weights(self) -> np.ndarray:
        """Get normalized ensemble weights"""
        weights = np.array([config.weight for config in self.model_configs if config.enabled])
        return weights / weights.sum()

    def get_enabled_models(self) -> List[ModelConfig]:
        """Get list of enabled model configurations"""
        return [config for config in self.model_configs if config.enabled]

    def update_model_weight(self, model_type: ModelType, new_weight: float):
        """Update the weight of a specific model"""
        for config in self.model_configs:
            if config.model_type == model_type:
                config.weight = new_weight
                break

    def disable_model(self, model_type: ModelType):
        """Disable a specific model"""
        for config in self.model_configs:
            if config.model_type == model_type:
                config.enabled = False
                break

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'strategy': self.strategy.value,
            'feature_config': self.feature_config.__dict__,
            'training_config': self.training_config.__dict__,
            'validation_config': self.validation_config.__dict__,
            'deployment_config': self.deployment_config.__dict__,
            'model_configs': [
                {
                    'model_type': config.model_type.value,
                    'parameters': config.parameters,
                    'weight': config.weight,
                    'enabled': config.enabled
                }
                for config in self.model_configs
            ]
        }

# Strategy-specific configurations
HFT_CONFIG = PipelineConfig(TradingStrategy.HIGH_FREQUENCY)
SWING_CONFIG = PipelineConfig(TradingStrategy.SWING_TRADING)
POSITION_CONFIG = PipelineConfig(TradingStrategy.POSITION_TRADING)
RESEARCH_CONFIG = PipelineConfig(TradingStrategy.RESEARCH_ANALYSIS)

# Default configuration
DEFAULT_CONFIG = SWING_CONFIG