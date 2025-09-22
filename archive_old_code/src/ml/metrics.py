"""
AI Trading System - Performance Metrics Module
==============================================

This module defines comprehensive performance metrics for evaluating
ML models in trading applications, including prediction accuracy,
risk-adjusted returns, and trading-specific metrics.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
import warnings
from scipy import stats
warnings.filterwarnings('ignore')

@dataclass
class MetricResult:
    """Container for metric calculation results"""
    name: str
    value: float
    interpretation: str
    benchmark: Optional[float] = None
    percentile_rank: Optional[float] = None
    confidence_interval: Optional[Tuple[float, float]] = None

class BaseMetric(ABC):
    """Abstract base class for performance metrics"""

    def __init__(self, name: str, higher_is_better: bool = True):
        self.name = name
        self.higher_is_better = higher_is_better

    @abstractmethod
    def calculate(self, *args, **kwargs) -> float:
        """Calculate the metric value"""
        pass

    def interpret(self, value: float) -> str:
        """Provide interpretation of the metric value"""
        return f"{self.name}: {value:.4f}"

    def compare_to_benchmark(self, value: float, benchmark: float) -> str:
        """Compare metric value to benchmark"""
        if benchmark is None:
            return "No benchmark available"

        diff = value - benchmark
        direction = "better" if (diff > 0) == self.higher_is_better else "worse"
        return f"{abs(diff):.4f} {direction} than benchmark"

class PredictionAccuracyMetrics:
    """Prediction accuracy and quality metrics"""

    @staticmethod
    def correlation(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Pearson correlation between predictions and actual values"""
        if len(y_true) < 2:
            return 0.0
        mask = ~(np.isnan(y_true) | np.isnan(y_pred))
        if np.sum(mask) < 2:
            return 0.0
        return np.corrcoef(y_true[mask], y_pred[mask])[0, 1]

    @staticmethod
    def directional_accuracy(y_true: np.ndarray, y_pred: np.ndarray, threshold: float = 0) -> float:
        """Percentage of correct directional predictions"""
        mask = ~(np.isnan(y_true) | np.isnan(y_pred))
        if np.sum(mask) == 0:
            return 0.0

        y_true_clean = y_true[mask]
        y_pred_clean = y_pred[mask]

        true_direction = np.sign(y_true_clean - threshold)
        pred_direction = np.sign(y_pred_clean - threshold)

        return np.mean(true_direction == pred_direction)

    @staticmethod
    def hit_rate(y_true: np.ndarray, y_pred: np.ndarray, threshold: float = 0.01) -> float:
        """Hit rate for significant moves above threshold"""
        mask = ~(np.isnan(y_true) | np.isnan(y_pred))
        if np.sum(mask) == 0:
            return 0.0

        y_true_clean = y_true[mask]
        y_pred_clean = y_pred[mask]

        significant_moves = np.abs(y_true_clean) > threshold
        if np.sum(significant_moves) == 0:
            return 0.0

        true_direction = np.sign(y_true_clean[significant_moves])
        pred_direction = np.sign(y_pred_clean[significant_moves])

        return np.mean(true_direction == pred_direction)

    @staticmethod
    def prediction_confidence(y_pred: np.ndarray, confidence_levels: List[float] = [0.5, 0.8, 0.9]) -> Dict[str, float]:
        """Calculate prediction confidence at different levels"""
        results = {}
        pred_abs = np.abs(y_pred[~np.isnan(y_pred)])

        for level in confidence_levels:
            threshold = np.percentile(pred_abs, level * 100)
            high_confidence_preds = pred_abs >= threshold
            results[f'confidence_{int(level*100)}pct'] = np.mean(high_confidence_preds)

        return results

    @staticmethod
    def calibration_score(y_true: np.ndarray, y_pred: np.ndarray, n_bins: int = 10) -> float:
        """Calibration score for probability predictions"""
        mask = ~(np.isnan(y_true) | np.isnan(y_pred))
        if np.sum(mask) < n_bins:
            return 0.0

        y_true_clean = y_true[mask]
        y_pred_clean = y_pred[mask]

        # Convert to probabilities if needed
        if y_pred_clean.min() < 0 or y_pred_clean.max() > 1:
            # Normalize predictions to [0, 1]
            y_pred_clean = (y_pred_clean - y_pred_clean.min()) / (y_pred_clean.max() - y_pred_clean.min())

        # Binary targets (positive/negative returns)
        y_true_binary = (y_true_clean > 0).astype(int)

        # Calculate calibration
        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        bin_lowers = bin_boundaries[:-1]
        bin_uppers = bin_boundaries[1:]

        calibration_error = 0
        for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
            in_bin = (y_pred_clean >= bin_lower) & (y_pred_clean < bin_upper)
            prop_in_bin = in_bin.mean()

            if prop_in_bin > 0:
                accuracy_in_bin = y_true_binary[in_bin].mean()
                avg_confidence_in_bin = y_pred_clean[in_bin].mean()
                calibration_error += np.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin

        return 1 - calibration_error  # Higher is better

class RiskAdjustedMetrics:
    """Risk-adjusted return metrics"""

    @staticmethod
    def sharpe_ratio(returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
        """Sharpe ratio calculation"""
        if len(returns) == 0 or np.std(returns) == 0:
            return 0.0

        excess_returns = returns - risk_free_rate / 252  # Daily risk-free rate
        return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)

    @staticmethod
    def sortino_ratio(returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
        """Sortino ratio (downside deviation)"""
        if len(returns) == 0:
            return 0.0

        excess_returns = returns - risk_free_rate / 252
        downside_returns = excess_returns[excess_returns < 0]

        if len(downside_returns) == 0:
            return np.inf

        downside_deviation = np.std(downside_returns)
        if downside_deviation == 0:
            return np.inf

        return np.mean(excess_returns) / downside_deviation * np.sqrt(252)

    @staticmethod
    def calmar_ratio(returns: np.ndarray) -> float:
        """Calmar ratio (annual return / max drawdown)"""
        if len(returns) == 0:
            return 0.0

        annual_return = (1 + np.mean(returns)) ** 252 - 1
        max_drawdown = RiskAdjustedMetrics.max_drawdown(returns)

        if max_drawdown == 0:
            return np.inf

        return annual_return / abs(max_drawdown)

    @staticmethod
    def max_drawdown(returns: np.ndarray) -> float:
        """Maximum drawdown calculation"""
        if len(returns) == 0:
            return 0.0

        cumulative_returns = (1 + returns).cumprod()
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdowns = (cumulative_returns - running_max) / running_max

        return np.min(drawdowns)

    @staticmethod
    def var(returns: np.ndarray, confidence_level: float = 0.05) -> float:
        """Value at Risk calculation"""
        if len(returns) == 0:
            return 0.0

        return np.percentile(returns, confidence_level * 100)

    @staticmethod
    def expected_shortfall(returns: np.ndarray, confidence_level: float = 0.05) -> float:
        """Expected Shortfall (Conditional VaR)"""
        if len(returns) == 0:
            return 0.0

        var_threshold = RiskAdjustedMetrics.var(returns, confidence_level)
        tail_returns = returns[returns <= var_threshold]

        if len(tail_returns) == 0:
            return var_threshold

        return np.mean(tail_returns)

    @staticmethod
    def omega_ratio(returns: np.ndarray, threshold: float = 0.0) -> float:
        """Omega ratio calculation"""
        if len(returns) == 0:
            return 1.0

        gains = returns[returns > threshold] - threshold
        losses = threshold - returns[returns <= threshold]

        if np.sum(losses) == 0:
            return np.inf

        return np.sum(gains) / np.sum(losses)

class TradingSpecificMetrics:
    """Trading-specific performance metrics"""

    @staticmethod
    def information_ratio(portfolio_returns: np.ndarray, benchmark_returns: np.ndarray) -> float:
        """Information ratio calculation"""
        if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) == 0:
            return 0.0

        active_returns = portfolio_returns - benchmark_returns
        tracking_error = np.std(active_returns)

        if tracking_error == 0:
            return 0.0

        return np.mean(active_returns) / tracking_error * np.sqrt(252)

    @staticmethod
    def tracking_error(portfolio_returns: np.ndarray, benchmark_returns: np.ndarray) -> float:
        """Tracking error calculation"""
        if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) == 0:
            return 0.0

        active_returns = portfolio_returns - benchmark_returns
        return np.std(active_returns) * np.sqrt(252)

    @staticmethod
    def beta(portfolio_returns: np.ndarray, market_returns: np.ndarray) -> float:
        """Beta calculation"""
        if len(portfolio_returns) != len(market_returns) or len(portfolio_returns) < 2:
            return 1.0

        covariance = np.cov(portfolio_returns, market_returns)[0, 1]
        market_variance = np.var(market_returns)

        if market_variance == 0:
            return 1.0

        return covariance / market_variance

    @staticmethod
    def alpha(portfolio_returns: np.ndarray, market_returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
        """Alpha calculation (Jensen's alpha)"""
        if len(portfolio_returns) != len(market_returns) or len(portfolio_returns) == 0:
            return 0.0

        portfolio_excess = np.mean(portfolio_returns) - risk_free_rate / 252
        market_excess = np.mean(market_returns) - risk_free_rate / 252
        beta = TradingSpecificMetrics.beta(portfolio_returns, market_returns)

        return (portfolio_excess - beta * market_excess) * 252

    @staticmethod
    def profit_factor(returns: np.ndarray) -> float:
        """Profit factor calculation"""
        if len(returns) == 0:
            return 1.0

        winning_trades = returns[returns > 0]
        losing_trades = returns[returns < 0]

        gross_profit = np.sum(winning_trades)
        gross_loss = abs(np.sum(losing_trades))

        if gross_loss == 0:
            return np.inf

        return gross_profit / gross_loss

    @staticmethod
    def win_rate(returns: np.ndarray) -> float:
        """Win rate calculation"""
        if len(returns) == 0:
            return 0.0

        return np.sum(returns > 0) / len(returns)

    @staticmethod
    def average_trade_duration(positions: np.ndarray) -> float:
        """Average trade duration"""
        if len(positions) < 2:
            return 1.0

        # Find position changes
        position_changes = np.diff(positions) != 0
        trade_durations = []

        current_duration = 1
        for is_change in position_changes:
            if is_change:
                trade_durations.append(current_duration)
                current_duration = 1
            else:
                current_duration += 1

        if len(trade_durations) == 0:
            return len(positions)

        return np.mean(trade_durations)

    @staticmethod
    def turnover_rate(positions: np.ndarray) -> float:
        """Portfolio turnover rate"""
        if len(positions) < 2:
            return 0.0

        position_changes = np.abs(np.diff(positions))
        return np.mean(position_changes)

class ModelStabilityMetrics:
    """Model stability and robustness metrics"""

    @staticmethod
    def prediction_stability(predictions_history: List[np.ndarray]) -> float:
        """Stability of predictions over time"""
        if len(predictions_history) < 2:
            return 1.0

        correlations = []
        for i in range(1, len(predictions_history)):
            prev_pred = predictions_history[i-1]
            curr_pred = predictions_history[i]

            # Align arrays (in case of different lengths)
            min_len = min(len(prev_pred), len(curr_pred))
            if min_len < 2:
                continue

            corr = np.corrcoef(prev_pred[:min_len], curr_pred[:min_len])[0, 1]
            if not np.isnan(corr):
                correlations.append(corr)

        return np.mean(correlations) if correlations else 0.0

    @staticmethod
    def feature_importance_stability(importance_history: List[Dict[str, float]]) -> float:
        """Stability of feature importance over time"""
        if len(importance_history) < 2:
            return 1.0

        # Get common features
        common_features = set(importance_history[0].keys())
        for importance_dict in importance_history[1:]:
            common_features = common_features.intersection(set(importance_dict.keys()))

        if len(common_features) == 0:
            return 0.0

        common_features = list(common_features)
        correlations = []

        for i in range(1, len(importance_history)):
            prev_importance = [importance_history[i-1][feat] for feat in common_features]
            curr_importance = [importance_history[i][feat] for feat in common_features]

            if len(prev_importance) > 1:
                corr = np.corrcoef(prev_importance, curr_importance)[0, 1]
                if not np.isnan(corr):
                    correlations.append(corr)

        return np.mean(correlations) if correlations else 0.0

    @staticmethod
    def performance_consistency(performance_history: List[float]) -> float:
        """Consistency of performance over time"""
        if len(performance_history) < 2:
            return 1.0

        mean_performance = np.mean(performance_history)
        if mean_performance == 0:
            return 0.0

        return 1 - (np.std(performance_history) / abs(mean_performance))

class AdvancedMetrics:
    """Advanced and specialized metrics"""

    @staticmethod
    def tail_ratio(returns: np.ndarray, percentile: float = 0.05) -> float:
        """Tail ratio (right tail / left tail)"""
        if len(returns) == 0:
            return 1.0

        right_tail = np.percentile(returns, (1 - percentile) * 100)
        left_tail = abs(np.percentile(returns, percentile * 100))

        if left_tail == 0:
            return np.inf

        return right_tail / left_tail

    @staticmethod
    def gain_to_pain_ratio(returns: np.ndarray) -> float:
        """Gain-to-pain ratio"""
        if len(returns) == 0:
            return 0.0

        total_return = (1 + returns).prod() - 1
        pain = np.sum(np.abs(returns[returns < 0]))

        if pain == 0:
            return np.inf

        return total_return / pain

    @staticmethod
    def ulcer_index(returns: np.ndarray) -> float:
        """Ulcer Index (downside risk measure)"""
        if len(returns) == 0:
            return 0.0

        cumulative_returns = (1 + returns).cumprod()
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdowns = (cumulative_returns - running_max) / running_max

        # Square the drawdowns and take the square root of the mean
        return np.sqrt(np.mean(drawdowns ** 2))

    @staticmethod
    def sterling_ratio(returns: np.ndarray) -> float:
        """Sterling ratio (annual return / average max drawdown)"""
        if len(returns) == 0:
            return 0.0

        annual_return = (1 + np.mean(returns)) ** 252 - 1

        # Calculate rolling maximum drawdowns
        window_size = min(252, len(returns))  # 1 year or less
        rolling_drawdowns = []

        for i in range(window_size, len(returns) + 1):
            window_returns = returns[i-window_size:i]
            max_dd = RiskAdjustedMetrics.max_drawdown(window_returns)
            rolling_drawdowns.append(abs(max_dd))

        if len(rolling_drawdowns) == 0 or np.mean(rolling_drawdowns) == 0:
            return np.inf

        return annual_return / np.mean(rolling_drawdowns)

    @staticmethod
    def kappa_ratio(returns: np.ndarray, n: int = 3) -> float:
        """Kappa ratio (higher moment risk measure)"""
        if len(returns) == 0:
            return 0.0

        mean_return = np.mean(returns)
        lower_partial_moment = np.mean(np.maximum(0 - returns, 0) ** n)

        if lower_partial_moment == 0:
            return np.inf

        return mean_return / (lower_partial_moment ** (1/n))

class MetricsCalculator:
    """Main calculator class that orchestrates all metric calculations"""

    def __init__(self, risk_free_rate: float = 0.02):
        self.risk_free_rate = risk_free_rate
        self.prediction_metrics = PredictionAccuracyMetrics()
        self.risk_metrics = RiskAdjustedMetrics()
        self.trading_metrics = TradingSpecificMetrics()
        self.stability_metrics = ModelStabilityMetrics()
        self.advanced_metrics = AdvancedMetrics()

    def calculate_all_metrics(
        self,
        y_true: np.ndarray = None,
        y_pred: np.ndarray = None,
        returns: np.ndarray = None,
        benchmark_returns: np.ndarray = None,
        positions: np.ndarray = None,
        predictions_history: List[np.ndarray] = None,
        importance_history: List[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """Calculate comprehensive set of metrics"""

        metrics = {}

        # Prediction accuracy metrics
        if y_true is not None and y_pred is not None:
            metrics.update(self._calculate_prediction_metrics(y_true, y_pred))

        # Risk-adjusted metrics
        if returns is not None:
            metrics.update(self._calculate_risk_metrics(returns))

        # Trading-specific metrics
        if returns is not None:
            metrics.update(self._calculate_trading_metrics(returns, benchmark_returns, positions))

        # Stability metrics
        if predictions_history is not None or importance_history is not None:
            metrics.update(self._calculate_stability_metrics(predictions_history, importance_history))

        # Advanced metrics
        if returns is not None:
            metrics.update(self._calculate_advanced_metrics(returns))

        return metrics

    def _calculate_prediction_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """Calculate prediction accuracy metrics"""
        metrics = {}

        metrics['correlation'] = self.prediction_metrics.correlation(y_true, y_pred)
        metrics['directional_accuracy'] = self.prediction_metrics.directional_accuracy(y_true, y_pred)
        metrics['hit_rate_1pct'] = self.prediction_metrics.hit_rate(y_true, y_pred, 0.01)
        metrics['hit_rate_2pct'] = self.prediction_metrics.hit_rate(y_true, y_pred, 0.02)
        metrics['hit_rate_5pct'] = self.prediction_metrics.hit_rate(y_true, y_pred, 0.05)
        metrics['calibration_score'] = self.prediction_metrics.calibration_score(y_true, y_pred)

        # Confidence metrics
        confidence_metrics = self.prediction_metrics.prediction_confidence(y_pred)
        metrics.update(confidence_metrics)

        return metrics

    def _calculate_risk_metrics(self, returns: np.ndarray) -> Dict[str, float]:
        """Calculate risk-adjusted metrics"""
        metrics = {}

        metrics['sharpe_ratio'] = self.risk_metrics.sharpe_ratio(returns, self.risk_free_rate)
        metrics['sortino_ratio'] = self.risk_metrics.sortino_ratio(returns, self.risk_free_rate)
        metrics['calmar_ratio'] = self.risk_metrics.calmar_ratio(returns)
        metrics['max_drawdown'] = self.risk_metrics.max_drawdown(returns)
        metrics['var_95'] = self.risk_metrics.var(returns, 0.05)
        metrics['var_99'] = self.risk_metrics.var(returns, 0.01)
        metrics['expected_shortfall_95'] = self.risk_metrics.expected_shortfall(returns, 0.05)
        metrics['expected_shortfall_99'] = self.risk_metrics.expected_shortfall(returns, 0.01)
        metrics['omega_ratio'] = self.risk_metrics.omega_ratio(returns)

        return metrics

    def _calculate_trading_metrics(
        self,
        returns: np.ndarray,
        benchmark_returns: np.ndarray = None,
        positions: np.ndarray = None
    ) -> Dict[str, float]:
        """Calculate trading-specific metrics"""
        metrics = {}

        metrics['profit_factor'] = self.trading_metrics.profit_factor(returns)
        metrics['win_rate'] = self.trading_metrics.win_rate(returns)

        if benchmark_returns is not None and len(benchmark_returns) == len(returns):
            metrics['information_ratio'] = self.trading_metrics.information_ratio(returns, benchmark_returns)
            metrics['tracking_error'] = self.trading_metrics.tracking_error(returns, benchmark_returns)
            metrics['beta'] = self.trading_metrics.beta(returns, benchmark_returns)
            metrics['alpha'] = self.trading_metrics.alpha(returns, benchmark_returns, self.risk_free_rate)

        if positions is not None:
            metrics['avg_trade_duration'] = self.trading_metrics.average_trade_duration(positions)
            metrics['turnover_rate'] = self.trading_metrics.turnover_rate(positions)

        return metrics

    def _calculate_stability_metrics(
        self,
        predictions_history: List[np.ndarray] = None,
        importance_history: List[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """Calculate stability metrics"""
        metrics = {}

        if predictions_history is not None:
            metrics['prediction_stability'] = self.stability_metrics.prediction_stability(predictions_history)

        if importance_history is not None:
            metrics['feature_importance_stability'] = self.stability_metrics.feature_importance_stability(importance_history)

        return metrics

    def _calculate_advanced_metrics(self, returns: np.ndarray) -> Dict[str, float]:
        """Calculate advanced metrics"""
        metrics = {}

        metrics['tail_ratio'] = self.advanced_metrics.tail_ratio(returns)
        metrics['gain_to_pain_ratio'] = self.advanced_metrics.gain_to_pain_ratio(returns)
        metrics['ulcer_index'] = self.advanced_metrics.ulcer_index(returns)
        metrics['sterling_ratio'] = self.advanced_metrics.sterling_ratio(returns)
        metrics['kappa_ratio'] = self.advanced_metrics.kappa_ratio(returns)

        return metrics

    def create_metric_report(self, metrics: Dict[str, float]) -> str:
        """Create a human-readable metrics report"""
        report = ["=== PERFORMANCE METRICS REPORT ===\n"]

        # Group metrics by category
        prediction_metrics = {k: v for k, v in metrics.items() if k in [
            'correlation', 'directional_accuracy', 'hit_rate_1pct', 'hit_rate_2pct', 'hit_rate_5pct', 'calibration_score'
        ]}

        risk_metrics = {k: v for k, v in metrics.items() if k in [
            'sharpe_ratio', 'sortino_ratio', 'calmar_ratio', 'max_drawdown', 'var_95', 'var_99'
        ]}

        trading_metrics = {k: v for k, v in metrics.items() if k in [
            'profit_factor', 'win_rate', 'information_ratio', 'tracking_error', 'beta', 'alpha'
        ]}

        # Prediction Quality
        if prediction_metrics:
            report.append("PREDICTION QUALITY:")
            for name, value in prediction_metrics.items():
                interpretation = self._interpret_metric(name, value)
                report.append(f"  {name}: {value:.4f} - {interpretation}")
            report.append("")

        # Risk-Adjusted Performance
        if risk_metrics:
            report.append("RISK-ADJUSTED PERFORMANCE:")
            for name, value in risk_metrics.items():
                interpretation = self._interpret_metric(name, value)
                report.append(f"  {name}: {value:.4f} - {interpretation}")
            report.append("")

        # Trading Performance
        if trading_metrics:
            report.append("TRADING PERFORMANCE:")
            for name, value in trading_metrics.items():
                interpretation = self._interpret_metric(name, value)
                report.append(f"  {name}: {value:.4f} - {interpretation}")
            report.append("")

        return "\n".join(report)

    def _interpret_metric(self, metric_name: str, value: float) -> str:
        """Provide interpretation for specific metrics"""
        interpretations = {
            'correlation': lambda v: f"{'Strong' if v > 0.7 else 'Moderate' if v > 0.4 else 'Weak'} predictive power",
            'directional_accuracy': lambda v: f"{'Excellent' if v > 0.6 else 'Good' if v > 0.55 else 'Fair'} direction prediction",
            'sharpe_ratio': lambda v: f"{'Excellent' if v > 2 else 'Good' if v > 1 else 'Fair'} risk-adjusted returns",
            'sortino_ratio': lambda v: f"{'Excellent' if v > 2 else 'Good' if v > 1 else 'Fair'} downside risk-adjusted returns",
            'max_drawdown': lambda v: f"{'Low' if abs(v) < 0.1 else 'Moderate' if abs(v) < 0.2 else 'High'} maximum loss",
            'win_rate': lambda v: f"{'High' if v > 0.6 else 'Moderate' if v > 0.5 else 'Low'} win percentage",
            'information_ratio': lambda v: f"{'Excellent' if v > 1 else 'Good' if v > 0.5 else 'Fair'} excess return per unit risk"
        }

        return interpretations.get(metric_name, lambda v: "No interpretation available")(value)