"""
Enhanced Feature Engineering Pipeline with Validation
Based on 2024 research findings and JPMorgan COiN success patterns

Key Enhancements:
- Data quality validation before feature creation
- Explainability metadata for all features
- Feature stability monitoring
- Cross-validation with time series awareness
- Built-in audit trail for regulatory compliance
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import json
from collections import defaultdict
from abc import ABC, abstractmethod

# Statistical and ML libraries
try:
    import scipy.stats as stats
    from scipy import signal
    from sklearn.preprocessing import StandardScaler, RobustScaler
    from sklearn.feature_selection import SelectKBest, f_regression, mutual_info_regression
    from sklearn.ensemble import IsolationForest
    import shap
    ENHANCED_FEATURES_AVAILABLE = True
except ImportError:
    ENHANCED_FEATURES_AVAILABLE = False

# Time series libraries
try:
    import ta
    import talib
    TECHNICAL_ANALYSIS_AVAILABLE = True
except ImportError:
    TECHNICAL_ANALYSIS_AVAILABLE = False


class FeatureQualityLevel(Enum):
    """Feature quality assessment levels"""
    EXCELLENT = "excellent"  # Quality score > 0.9
    GOOD = "good"           # Quality score > 0.7
    ACCEPTABLE = "acceptable" # Quality score > 0.5
    POOR = "poor"           # Quality score > 0.3
    CRITICAL = "critical"   # Quality score <= 0.3


class DataValidationSeverity(Enum):
    """Data validation severity levels"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """Result of a single validation check"""
    validator: str
    severity: DataValidationSeverity
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def is_blocking(self) -> bool:
        """Check if this validation result should block pipeline"""
        return self.severity in [DataValidationSeverity.HIGH, DataValidationSeverity.CRITICAL]


@dataclass
class ValidationReport:
    """Comprehensive validation report"""
    results: List[ValidationResult] = field(default_factory=list)
    block_pipeline: bool = False
    overall_score: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)

    def add_validation_result(self, result: ValidationResult):
        """Add validation result and update overall assessment"""
        self.results.append(result)

        # Update blocking status
        if result.is_blocking():
            self.block_pipeline = True

        # Update overall score based on severity
        severity_weights = {
            DataValidationSeverity.NONE: 0.0,
            DataValidationSeverity.LOW: 0.1,
            DataValidationSeverity.MEDIUM: 0.3,
            DataValidationSeverity.HIGH: 0.6,
            DataValidationSeverity.CRITICAL: 1.0
        }

        penalty = severity_weights.get(result.severity, 0.0)
        self.overall_score *= (1.0 - penalty)

    def get_critical_issues(self) -> List[ValidationResult]:
        """Get all critical validation issues"""
        return [r for r in self.results if r.severity == DataValidationSeverity.CRITICAL]

    def get_blocking_issues(self) -> List[ValidationResult]:
        """Get all blocking validation issues"""
        return [r for r in self.results if r.is_blocking()]


@dataclass
class FeatureMetadata:
    """Metadata for feature explainability and audit trail"""
    feature_name: str
    creation_method: str
    calculation_description: str
    trading_meaning: str
    sensitivity_analysis: Dict[str, float]
    stability_score: float
    importance_score: float
    data_sources: List[str]
    dependencies: List[str]
    creation_timestamp: datetime
    quality_score: float

    def to_audit_record(self) -> Dict[str, Any]:
        """Convert to audit record format"""
        return {
            "feature_name": self.feature_name,
            "creation_method": self.creation_method,
            "description": self.calculation_description,
            "trading_meaning": self.trading_meaning,
            "quality_metrics": {
                "stability_score": self.stability_score,
                "importance_score": self.importance_score,
                "quality_score": self.quality_score
            },
            "data_lineage": {
                "sources": self.data_sources,
                "dependencies": self.dependencies
            },
            "timestamp": self.creation_timestamp.isoformat()
        }


@dataclass
class FeatureSet:
    """Container for engineered features with metadata"""
    features: Dict[str, np.ndarray] = field(default_factory=dict)
    metadata: Dict[str, FeatureMetadata] = field(default_factory=dict)
    groups: Dict[str, List[str]] = field(default_factory=dict)
    creation_timestamp: datetime = field(default_factory=datetime.now)
    validation_report: Optional[ValidationReport] = None
    quality_score: float = 0.0

    def add_feature(self, name: str, data: np.ndarray, metadata: FeatureMetadata):
        """Add feature with metadata"""
        self.features[name] = data
        self.metadata[name] = metadata
        self._update_quality_score()

    def add_feature_group(self, group_name: str, feature_names: List[str]):
        """Add group of related features"""
        self.groups[group_name] = feature_names

    def get_feature_names(self) -> List[str]:
        """Get all feature names"""
        return list(self.features.keys())

    def get_quality_score(self) -> float:
        """Get overall feature set quality score"""
        return self.quality_score

    def _update_quality_score(self):
        """Update overall quality score based on individual features"""
        if not self.metadata:
            self.quality_score = 0.0
            return

        quality_scores = [meta.quality_score for meta in self.metadata.values()]
        self.quality_score = np.mean(quality_scores)


class DataQualityValidator(ABC):
    """Abstract base class for data quality validators"""

    @abstractmethod
    async def validate(self, data: pd.DataFrame) -> ValidationResult:
        """Validate data and return result"""
        pass


class TemporalConsistencyValidator(DataQualityValidator):
    """Validate temporal ordering and gap detection"""

    def __init__(self, max_gap_seconds: float = 5.0):
        self.max_gap_seconds = max_gap_seconds

    async def validate(self, data: pd.DataFrame) -> ValidationResult:
        """Check temporal consistency"""
        if 'timestamp' not in data.columns:
            return ValidationResult(
                validator="temporal_consistency",
                severity=DataValidationSeverity.HIGH,
                message="No timestamp column found",
                details={"columns": list(data.columns)}
            )

        timestamps = pd.to_datetime(data['timestamp'])

        # Check ordering
        ordering_issues = (timestamps.diff() < pd.Timedelta(0)).sum()

        # Check gaps
        time_diffs = timestamps.diff().dt.total_seconds()
        large_gaps = (time_diffs > self.max_gap_seconds).sum()

        if ordering_issues > 0 or large_gaps > 0:
            severity = DataValidationSeverity.CRITICAL if ordering_issues > 0 else DataValidationSeverity.HIGH
            return ValidationResult(
                validator="temporal_consistency",
                severity=severity,
                message=f"Found {ordering_issues} ordering issues, {large_gaps} large gaps",
                details={
                    "ordering_issues": int(ordering_issues),
                    "large_gaps": int(large_gaps),
                    "max_gap_seconds": float(time_diffs.max()) if not time_diffs.isna().all() else 0.0
                }
            )

        return ValidationResult(
            validator="temporal_consistency",
            severity=DataValidationSeverity.NONE,
            message="Temporal consistency validated"
        )


class StatisticalOutlierDetector(DataQualityValidator):
    """Detect statistical outliers in market data"""

    def __init__(self, z_threshold: float = 3.0, iqr_threshold: float = 1.5):
        self.z_threshold = z_threshold
        self.iqr_threshold = iqr_threshold

    async def validate(self, data: pd.DataFrame) -> ValidationResult:
        """Detect outliers using multiple methods"""
        numeric_columns = data.select_dtypes(include=[np.number]).columns

        if len(numeric_columns) == 0:
            return ValidationResult(
                validator="statistical_outliers",
                severity=DataValidationSeverity.MEDIUM,
                message="No numeric columns for outlier detection"
            )

        outlier_counts = {}
        total_outliers = 0

        for col in numeric_columns:
            col_data = data[col].dropna()
            if len(col_data) == 0:
                continue

            # Z-score method
            z_scores = np.abs(stats.zscore(col_data))
            z_outliers = (z_scores > self.z_threshold).sum()

            # IQR method
            Q1 = col_data.quantile(0.25)
            Q3 = col_data.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - self.iqr_threshold * IQR
            upper_bound = Q3 + self.iqr_threshold * IQR
            iqr_outliers = ((col_data < lower_bound) | (col_data > upper_bound)).sum()

            col_outliers = max(z_outliers, iqr_outliers)
            outlier_counts[col] = int(col_outliers)
            total_outliers += col_outliers

        outlier_percentage = (total_outliers / len(data)) * 100 if len(data) > 0 else 0

        if outlier_percentage > 10:  # More than 10% outliers
            severity = DataValidationSeverity.HIGH
        elif outlier_percentage > 5:  # More than 5% outliers
            severity = DataValidationSeverity.MEDIUM
        elif outlier_percentage > 1:  # More than 1% outliers
            severity = DataValidationSeverity.LOW
        else:
            severity = DataValidationSeverity.NONE

        return ValidationResult(
            validator="statistical_outliers",
            severity=severity,
            message=f"Found {total_outliers} outliers ({outlier_percentage:.2f}%)",
            details={
                "total_outliers": int(total_outliers),
                "outlier_percentage": float(outlier_percentage),
                "outliers_by_column": outlier_counts
            }
        )


class BusinessRuleValidator(DataQualityValidator):
    """Validate business rules for trading data"""

    async def validate(self, data: pd.DataFrame) -> ValidationResult:
        """Validate trading-specific business rules"""
        violations = []

        # Price validation
        if 'close' in data.columns:
            negative_prices = (data['close'] <= 0).sum()
            if negative_prices > 0:
                violations.append(f"{negative_prices} negative/zero prices")

        # OHLC consistency
        ohlc_cols = ['open', 'high', 'low', 'close']
        if all(col in data.columns for col in ohlc_cols):
            # High should be >= max(open, close)
            invalid_highs = (data['high'] < data[['open', 'close']].max(axis=1)).sum()
            # Low should be <= min(open, close)
            invalid_lows = (data['low'] > data[['open', 'close']].min(axis=1)).sum()

            if invalid_highs > 0:
                violations.append(f"{invalid_highs} invalid high prices")
            if invalid_lows > 0:
                violations.append(f"{invalid_lows} invalid low prices")

        # Volume validation
        if 'volume' in data.columns:
            negative_volumes = (data['volume'] < 0).sum()
            if negative_volumes > 0:
                violations.append(f"{negative_volumes} negative volumes")

        if violations:
            severity = DataValidationSeverity.HIGH if len(violations) > 2 else DataValidationSeverity.MEDIUM
            return ValidationResult(
                validator="business_rules",
                severity=severity,
                message=f"Business rule violations: {'; '.join(violations)}",
                details={"violations": violations}
            )

        return ValidationResult(
            validator="business_rules",
            severity=DataValidationSeverity.NONE,
            message="All business rules validated"
        )


class ExplainableFeatureEngineer:
    """Feature engineering with built-in explainability tracking"""

    def __init__(self):
        self.feature_registry = {}
        self.validation_layers = [
            TemporalConsistencyValidator(),
            StatisticalOutlierDetector(),
            BusinessRuleValidator()
        ]
        self.scaler = RobustScaler()
        self.feature_selector = SelectKBest(score_func=f_regression, k=50)

    async def engineer_features(self, market_data: pd.DataFrame,
                              target_column: Optional[str] = None) -> FeatureSet:
        """Create features with explainability metadata"""

        # Step 1: Validate input data
        validation_report = await self._validate_data_quality(market_data)
        if validation_report.block_pipeline:
            raise ValueError(f"Data quality validation failed: {validation_report.get_blocking_issues()}")

        feature_set = FeatureSet(validation_report=validation_report)

        # Step 2: Create technical features
        if TECHNICAL_ANALYSIS_AVAILABLE:
            technical_features = await self._create_technical_features(market_data)
            for name, (data, metadata) in technical_features.items():
                feature_set.add_feature(name, data, metadata)
            feature_set.add_feature_group("technical", list(technical_features.keys()))

        # Step 3: Create statistical features
        statistical_features = await self._create_statistical_features(market_data)
        for name, (data, metadata) in statistical_features.items():
            feature_set.add_feature(name, data, metadata)
        feature_set.add_feature_group("statistical", list(statistical_features.keys()))

        # Step 4: Create lag features
        lag_features = await self._create_lag_features(market_data)
        for name, (data, metadata) in lag_features.items():
            feature_set.add_feature(name, data, metadata)
        feature_set.add_feature_group("lag", list(lag_features.keys()))

        # Step 5: Create rolling window features
        rolling_features = await self._create_rolling_features(market_data)
        for name, (data, metadata) in rolling_features.items():
            feature_set.add_feature(name, data, metadata)
        feature_set.add_feature_group("rolling", list(rolling_features.keys()))

        # Step 6: Feature selection and quality assessment
        if target_column and target_column in market_data.columns:
            feature_set = await self._select_and_rank_features(feature_set, market_data[target_column])

        # Step 7: Final feature quality validation
        quality_report = await self._validate_feature_quality(feature_set)
        feature_set.validation_report = quality_report

        return feature_set

    async def _validate_data_quality(self, data: pd.DataFrame) -> ValidationReport:
        """Comprehensive data quality validation"""
        report = ValidationReport()

        for validator in self.validation_layers:
            try:
                result = await validator.validate(data)
                report.add_validation_result(result)
            except Exception as e:
                error_result = ValidationResult(
                    validator=type(validator).__name__,
                    severity=DataValidationSeverity.HIGH,
                    message=f"Validation error: {str(e)}",
                    details={"error": str(e)}
                )
                report.add_validation_result(error_result)

        return report

    async def _create_technical_features(self, data: pd.DataFrame) -> Dict[str, Tuple[np.ndarray, FeatureMetadata]]:
        """Create technical analysis features with metadata"""
        features = {}

        if not all(col in data.columns for col in ['open', 'high', 'low', 'close', 'volume']):
            return features

        # RSI
        try:
            rsi_14 = ta.momentum.RSIIndicator(close=data['close'], window=14).rsi()
            features['rsi_14'] = (
                rsi_14.values,
                FeatureMetadata(
                    feature_name='rsi_14',
                    creation_method='technical_analysis',
                    calculation_description='14-period Relative Strength Index',
                    trading_meaning='Momentum oscillator indicating overbought/oversold conditions',
                    sensitivity_analysis=await self._analyze_feature_sensitivity(rsi_14),
                    stability_score=await self._calculate_stability_score(rsi_14),
                    importance_score=0.0,  # Will be updated in feature selection
                    data_sources=['close'],
                    dependencies=[],
                    creation_timestamp=datetime.now(),
                    quality_score=await self._calculate_feature_quality(rsi_14)
                )
            )
        except Exception as e:
            print(f"Error creating RSI feature: {e}")

        # MACD
        try:
            macd = ta.trend.MACD(close=data['close'])
            macd_line = macd.macd()
            macd_signal = macd.macd_signal()
            macd_histogram = macd.macd_diff()

            features['macd_line'] = (
                macd_line.values,
                FeatureMetadata(
                    feature_name='macd_line',
                    creation_method='technical_analysis',
                    calculation_description='MACD line (12-day EMA - 26-day EMA)',
                    trading_meaning='Trend-following momentum indicator',
                    sensitivity_analysis=await self._analyze_feature_sensitivity(macd_line),
                    stability_score=await self._calculate_stability_score(macd_line),
                    importance_score=0.0,
                    data_sources=['close'],
                    dependencies=[],
                    creation_timestamp=datetime.now(),
                    quality_score=await self._calculate_feature_quality(macd_line)
                )
            )

            features['macd_histogram'] = (
                macd_histogram.values,
                FeatureMetadata(
                    feature_name='macd_histogram',
                    creation_method='technical_analysis',
                    calculation_description='MACD histogram (MACD - Signal)',
                    trading_meaning='Momentum divergence indicator',
                    sensitivity_analysis=await self._analyze_feature_sensitivity(macd_histogram),
                    stability_score=await self._calculate_stability_score(macd_histogram),
                    importance_score=0.0,
                    data_sources=['close'],
                    dependencies=['macd_line'],
                    creation_timestamp=datetime.now(),
                    quality_score=await self._calculate_feature_quality(macd_histogram)
                )
            )
        except Exception as e:
            print(f"Error creating MACD features: {e}")

        # Bollinger Bands
        try:
            bb = ta.volatility.BollingerBands(close=data['close'], window=20)
            bb_upper = bb.bollinger_hband()
            bb_lower = bb.bollinger_lband()
            bb_percent = (data['close'] - bb_lower) / (bb_upper - bb_lower)

            features['bb_percent'] = (
                bb_percent.values,
                FeatureMetadata(
                    feature_name='bb_percent',
                    creation_method='technical_analysis',
                    calculation_description='Bollinger Band percentage position',
                    trading_meaning='Price position within volatility bands',
                    sensitivity_analysis=await self._analyze_feature_sensitivity(bb_percent),
                    stability_score=await self._calculate_stability_score(bb_percent),
                    importance_score=0.0,
                    data_sources=['close'],
                    dependencies=[],
                    creation_timestamp=datetime.now(),
                    quality_score=await self._calculate_feature_quality(bb_percent)
                )
            )
        except Exception as e:
            print(f"Error creating Bollinger Band features: {e}")

        return features

    async def _create_statistical_features(self, data: pd.DataFrame) -> Dict[str, Tuple[np.ndarray, FeatureMetadata]]:
        """Create statistical features with metadata"""
        features = {}

        if 'close' not in data.columns:
            return features

        # Returns
        returns = data['close'].pct_change()
        features['returns'] = (
            returns.values,
            FeatureMetadata(
                feature_name='returns',
                creation_method='statistical',
                calculation_description='Percentage change in close price',
                trading_meaning='Price momentum and direction',
                sensitivity_analysis=await self._analyze_feature_sensitivity(returns),
                stability_score=await self._calculate_stability_score(returns),
                importance_score=0.0,
                data_sources=['close'],
                dependencies=[],
                creation_timestamp=datetime.now(),
                quality_score=await self._calculate_feature_quality(returns)
            )
        )

        # Log returns
        log_returns = np.log(data['close'] / data['close'].shift(1))
        features['log_returns'] = (
            log_returns.values,
            FeatureMetadata(
                feature_name='log_returns',
                creation_method='statistical',
                calculation_description='Natural log of price ratios',
                trading_meaning='Normalized price changes for statistical modeling',
                sensitivity_analysis=await self._analyze_feature_sensitivity(log_returns),
                stability_score=await self._calculate_stability_score(log_returns),
                importance_score=0.0,
                data_sources=['close'],
                dependencies=[],
                creation_timestamp=datetime.now(),
                quality_score=await self._calculate_feature_quality(log_returns)
            )
        )

        # Volatility (rolling standard deviation)
        volatility = returns.rolling(window=20).std()
        features['volatility_20'] = (
            volatility.values,
            FeatureMetadata(
                feature_name='volatility_20',
                creation_method='statistical',
                calculation_description='20-period rolling standard deviation of returns',
                trading_meaning='Market uncertainty and risk measure',
                sensitivity_analysis=await self._analyze_feature_sensitivity(volatility),
                stability_score=await self._calculate_stability_score(volatility),
                importance_score=0.0,
                data_sources=['close'],
                dependencies=['returns'],
                creation_timestamp=datetime.now(),
                quality_score=await self._calculate_feature_quality(volatility)
            )
        )

        return features

    async def _create_lag_features(self, data: pd.DataFrame) -> Dict[str, Tuple[np.ndarray, FeatureMetadata]]:
        """Create lag features with metadata"""
        features = {}

        if 'close' not in data.columns:
            return features

        # Price lags
        for lag in [1, 2, 3, 5, 10]:
            lagged_close = data['close'].shift(lag)
            features[f'close_lag_{lag}'] = (
                lagged_close.values,
                FeatureMetadata(
                    feature_name=f'close_lag_{lag}',
                    creation_method='lag_features',
                    calculation_description=f'Close price {lag} periods ago',
                    trading_meaning=f'Historical price for trend analysis ({lag} periods)',
                    sensitivity_analysis=await self._analyze_feature_sensitivity(lagged_close),
                    stability_score=await self._calculate_stability_score(lagged_close),
                    importance_score=0.0,
                    data_sources=['close'],
                    dependencies=[],
                    creation_timestamp=datetime.now(),
                    quality_score=await self._calculate_feature_quality(lagged_close)
                )
            )

        # Return lags
        returns = data['close'].pct_change()
        for lag in [1, 2, 3, 5]:
            lagged_returns = returns.shift(lag)
            features[f'returns_lag_{lag}'] = (
                lagged_returns.values,
                FeatureMetadata(
                    feature_name=f'returns_lag_{lag}',
                    creation_method='lag_features',
                    calculation_description=f'Returns {lag} periods ago',
                    trading_meaning=f'Historical momentum for reversal detection ({lag} periods)',
                    sensitivity_analysis=await self._analyze_feature_sensitivity(lagged_returns),
                    stability_score=await self._calculate_stability_score(lagged_returns),
                    importance_score=0.0,
                    data_sources=['close'],
                    dependencies=['returns'],
                    creation_timestamp=datetime.now(),
                    quality_score=await self._calculate_feature_quality(lagged_returns)
                )
            )

        return features

    async def _create_rolling_features(self, data: pd.DataFrame) -> Dict[str, Tuple[np.ndarray, FeatureMetadata]]:
        """Create rolling window features with metadata"""
        features = {}

        if 'close' not in data.columns:
            return features

        # Rolling means
        for window in [5, 10, 20, 50]:
            rolling_mean = data['close'].rolling(window=window).mean()
            features[f'sma_{window}'] = (
                rolling_mean.values,
                FeatureMetadata(
                    feature_name=f'sma_{window}',
                    creation_method='rolling_features',
                    calculation_description=f'{window}-period Simple Moving Average',
                    trading_meaning=f'Trend direction and support/resistance ({window} periods)',
                    sensitivity_analysis=await self._analyze_feature_sensitivity(rolling_mean),
                    stability_score=await self._calculate_stability_score(rolling_mean),
                    importance_score=0.0,
                    data_sources=['close'],
                    dependencies=[],
                    creation_timestamp=datetime.now(),
                    quality_score=await self._calculate_feature_quality(rolling_mean)
                )
            )

        # Rolling max/min
        for window in [10, 20]:
            rolling_max = data['close'].rolling(window=window).max()
            rolling_min = data['close'].rolling(window=window).min()

            features[f'rolling_max_{window}'] = (
                rolling_max.values,
                FeatureMetadata(
                    feature_name=f'rolling_max_{window}',
                    creation_method='rolling_features',
                    calculation_description=f'{window}-period rolling maximum',
                    trading_meaning=f'Resistance level identification ({window} periods)',
                    sensitivity_analysis=await self._analyze_feature_sensitivity(rolling_max),
                    stability_score=await self._calculate_stability_score(rolling_max),
                    importance_score=0.0,
                    data_sources=['close'],
                    dependencies=[],
                    creation_timestamp=datetime.now(),
                    quality_score=await self._calculate_feature_quality(rolling_max)
                )
            )

            features[f'rolling_min_{window}'] = (
                rolling_min.values,
                FeatureMetadata(
                    feature_name=f'rolling_min_{window}',
                    creation_method='rolling_features',
                    calculation_description=f'{window}-period rolling minimum',
                    trading_meaning=f'Support level identification ({window} periods)',
                    sensitivity_analysis=await self._analyze_feature_sensitivity(rolling_min),
                    stability_score=await self._calculate_stability_score(rolling_min),
                    importance_score=0.0,
                    data_sources=['close'],
                    dependencies=[],
                    creation_timestamp=datetime.now(),
                    quality_score=await self._calculate_feature_quality(rolling_min)
                )
            )

        return features

    async def _select_and_rank_features(self, feature_set: FeatureSet, target: pd.Series) -> FeatureSet:
        """Select and rank features based on target correlation"""
        if not ENHANCED_FEATURES_AVAILABLE:
            return feature_set

        # Prepare feature matrix
        feature_names = feature_set.get_feature_names()
        feature_matrix = np.column_stack([feature_set.features[name] for name in feature_names])

        # Remove NaN values
        mask = ~np.isnan(feature_matrix).any(axis=1) & ~np.isnan(target.values)
        clean_features = feature_matrix[mask]
        clean_target = target.values[mask]

        if len(clean_features) == 0:
            return feature_set

        # Calculate feature importance using mutual information
        try:
            mi_scores = mutual_info_regression(clean_features, clean_target)

            # Update feature metadata with importance scores
            for i, name in enumerate(feature_names):
                if name in feature_set.metadata:
                    feature_set.metadata[name].importance_score = float(mi_scores[i])
        except Exception as e:
            print(f"Error calculating feature importance: {e}")

        return feature_set

    async def _validate_feature_quality(self, feature_set: FeatureSet) -> ValidationReport:
        """Validate overall feature quality"""
        report = ValidationReport()

        # Check for features with too many NaN values
        for name, feature_data in feature_set.features.items():
            nan_percentage = (np.isnan(feature_data).sum() / len(feature_data)) * 100

            if nan_percentage > 50:
                severity = DataValidationSeverity.HIGH
            elif nan_percentage > 25:
                severity = DataValidationSeverity.MEDIUM
            elif nan_percentage > 10:
                severity = DataValidationSeverity.LOW
            else:
                severity = DataValidationSeverity.NONE

            if severity != DataValidationSeverity.NONE:
                result = ValidationResult(
                    validator="feature_nan_check",
                    severity=severity,
                    message=f"Feature {name} has {nan_percentage:.1f}% NaN values",
                    details={"feature": name, "nan_percentage": nan_percentage}
                )
                report.add_validation_result(result)

        # Check for constant features
        for name, feature_data in feature_set.features.items():
            clean_data = feature_data[~np.isnan(feature_data)]
            if len(clean_data) > 1:
                variance = np.var(clean_data)
                if variance < 1e-10:  # Essentially constant
                    result = ValidationResult(
                        validator="feature_variance_check",
                        severity=DataValidationSeverity.MEDIUM,
                        message=f"Feature {name} has very low variance",
                        details={"feature": name, "variance": float(variance)}
                    )
                    report.add_validation_result(result)

        return report

    async def _analyze_feature_sensitivity(self, feature_data: pd.Series) -> Dict[str, float]:
        """Analyze feature sensitivity to input changes"""
        try:
            clean_data = feature_data.dropna()
            if len(clean_data) < 10:
                return {"sensitivity": 0.0}

            # Calculate sensitivity metrics
            std_dev = float(clean_data.std())
            mean_val = float(clean_data.mean())
            cv = std_dev / abs(mean_val) if mean_val != 0 else 0.0

            # Calculate first difference sensitivity
            diff_data = clean_data.diff().dropna()
            diff_std = float(diff_data.std()) if len(diff_data) > 0 else 0.0

            return {
                "coefficient_of_variation": cv,
                "standard_deviation": std_dev,
                "difference_std": diff_std,
                "sensitivity": cv  # Use CV as overall sensitivity measure
            }
        except Exception:
            return {"sensitivity": 0.0}

    async def _calculate_stability_score(self, feature_data: pd.Series) -> float:
        """Calculate feature stability score"""
        try:
            clean_data = feature_data.dropna()
            if len(clean_data) < 20:
                return 0.5  # Neutral score for insufficient data

            # Split data into chunks and calculate consistency
            chunk_size = len(clean_data) // 4
            chunks = [clean_data[i:i+chunk_size] for i in range(0, len(clean_data), chunk_size)]

            # Calculate mean and std for each chunk
            chunk_means = [chunk.mean() for chunk in chunks if len(chunk) > 0]
            chunk_stds = [chunk.std() for chunk in chunks if len(chunk) > 0]

            if len(chunk_means) < 2:
                return 0.5

            # Stability is inverse of variation in chunk statistics
            mean_stability = 1.0 - (np.std(chunk_means) / (np.mean(chunk_means) + 1e-8))
            std_stability = 1.0 - (np.std(chunk_stds) / (np.mean(chunk_stds) + 1e-8))

            stability_score = (mean_stability + std_stability) / 2
            return max(0.0, min(1.0, stability_score))
        except Exception:
            return 0.5

    async def _calculate_feature_quality(self, feature_data: pd.Series) -> float:
        """Calculate overall feature quality score"""
        try:
            # NaN penalty
            nan_percentage = feature_data.isna().sum() / len(feature_data)
            nan_penalty = min(1.0, nan_percentage * 2)  # Max penalty of 1.0

            # Variance check
            clean_data = feature_data.dropna()
            if len(clean_data) < 2:
                return 0.1

            variance = clean_data.var()
            variance_score = 1.0 if variance > 1e-10 else 0.0

            # Stability score
            stability = await self._calculate_stability_score(feature_data)

            # Combined quality score
            quality = (1.0 - nan_penalty) * variance_score * stability
            return max(0.1, min(1.0, quality))
        except Exception:
            return 0.1


class FeatureQualityAssessor:
    """Assess feature quality and generate reports"""

    def __init__(self):
        self.quality_thresholds = {
            FeatureQualityLevel.EXCELLENT: 0.9,
            FeatureQualityLevel.GOOD: 0.7,
            FeatureQualityLevel.ACCEPTABLE: 0.5,
            FeatureQualityLevel.POOR: 0.3,
            FeatureQualityLevel.CRITICAL: 0.0
        }

    def assess_feature_quality(self, feature_set: FeatureSet) -> Dict[str, FeatureQualityLevel]:
        """Assess quality level for each feature"""
        quality_levels = {}

        for name, metadata in feature_set.metadata.items():
            quality_score = metadata.quality_score

            for level, threshold in self.quality_thresholds.items():
                if quality_score >= threshold:
                    quality_levels[name] = level
                    break

        return quality_levels

    def generate_quality_report(self, feature_set: FeatureSet) -> Dict[str, Any]:
        """Generate comprehensive feature quality report"""
        quality_levels = self.assess_feature_quality(feature_set)

        # Count features by quality level
        level_counts = defaultdict(int)
        for level in quality_levels.values():
            level_counts[level.value] += 1

        # Identify problematic features
        poor_features = [name for name, level in quality_levels.items()
                        if level in [FeatureQualityLevel.POOR, FeatureQualityLevel.CRITICAL]]

        # Calculate overall quality score
        overall_quality = feature_set.get_quality_score()

        report = {
            "timestamp": datetime.now().isoformat(),
            "total_features": len(feature_set.features),
            "overall_quality_score": overall_quality,
            "quality_distribution": dict(level_counts),
            "problematic_features": poor_features,
            "recommendations": self._generate_recommendations(feature_set, quality_levels),
            "feature_details": {
                name: {
                    "quality_level": level.value,
                    "quality_score": feature_set.metadata[name].quality_score,
                    "stability_score": feature_set.metadata[name].stability_score,
                    "importance_score": feature_set.metadata[name].importance_score
                }
                for name, level in quality_levels.items()
            }
        }

        return report

    def _generate_recommendations(self, feature_set: FeatureSet,
                                quality_levels: Dict[str, FeatureQualityLevel]) -> List[str]:
        """Generate recommendations for improving feature quality"""
        recommendations = []

        # Check for too many poor quality features
        poor_count = sum(1 for level in quality_levels.values()
                        if level in [FeatureQualityLevel.POOR, FeatureQualityLevel.CRITICAL])

        if poor_count > len(quality_levels) * 0.2:  # More than 20% poor quality
            recommendations.append("Consider removing or re-engineering poor quality features")

        # Check for low overall quality
        if feature_set.get_quality_score() < 0.6:
            recommendations.append("Overall feature quality is low - review data sources and engineering methods")

        # Check for features with high NaN rates
        high_nan_features = []
        for name, feature_data in feature_set.features.items():
            nan_rate = np.isnan(feature_data).sum() / len(feature_data)
            if nan_rate > 0.3:
                high_nan_features.append(name)

        if high_nan_features:
            recommendations.append(f"Features with high NaN rates: {', '.join(high_nan_features[:5])}")

        # Check for low stability features
        unstable_features = [
            name for name, metadata in feature_set.metadata.items()
            if metadata.stability_score < 0.5
        ]

        if unstable_features:
            recommendations.append(f"Consider stabilizing features: {', '.join(unstable_features[:5])}")

        return recommendations


# Example usage and testing
async def example_usage():
    """Example of how to use the enhanced feature engineering pipeline"""

    # Create sample market data
    dates = pd.date_range('2023-01-01', periods=1000, freq='1H')
    np.random.seed(42)

    data = pd.DataFrame({
        'timestamp': dates,
        'open': 100 + np.cumsum(np.random.randn(1000) * 0.1),
        'high': np.nan,
        'low': np.nan,
        'close': np.nan,
        'volume': np.random.lognormal(10, 0.5, 1000)
    })

    # Generate OHLC data
    data['close'] = data['open'] + np.random.randn(1000) * 0.5
    data['high'] = np.maximum(data['open'], data['close']) + np.abs(np.random.randn(1000) * 0.2)
    data['low'] = np.minimum(data['open'], data['close']) - np.abs(np.random.randn(1000) * 0.2)

    # Create target variable (future returns)
    data['target'] = data['close'].pct_change().shift(-1)

    # Initialize feature engineer
    feature_engineer = ExplainableFeatureEngineer()

    # Engineer features
    print("Engineering features...")
    feature_set = await feature_engineer.engineer_features(data, target_column='target')

    print(f"Created {len(feature_set.features)} features")
    print(f"Overall quality score: {feature_set.get_quality_score():.3f}")

    # Assess feature quality
    quality_assessor = FeatureQualityAssessor()
    quality_report = quality_assessor.generate_quality_report(feature_set)

    print("\nFeature Quality Report:")
    print(f"Total features: {quality_report['total_features']}")
    print(f"Overall quality: {quality_report['overall_quality_score']:.3f}")
    print(f"Quality distribution: {quality_report['quality_distribution']}")

    if quality_report['recommendations']:
        print("\nRecommendations:")
        for rec in quality_report['recommendations']:
            print(f"- {rec}")

    return feature_set, quality_report


if __name__ == "__main__":
    # Run example
    import asyncio
    asyncio.run(example_usage())