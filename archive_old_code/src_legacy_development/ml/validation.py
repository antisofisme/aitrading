"""
AI Trading System - Validation and Backtesting Framework
=======================================================

This module implements comprehensive validation and backtesting capabilities
for trading models, including time series cross-validation, walk-forward analysis,
and trading-specific performance metrics.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import warnings
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import matplotlib.pyplot as plt
import seaborn as sns
warnings.filterwarnings('ignore')

@dataclass
class BacktestResults:
    """Results from backtesting analysis"""
    total_return: float
    annual_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    calmar_ratio: float
    win_rate: float
    profit_factor: float
    var_95: float
    var_99: float
    expected_shortfall_95: float
    beta: float
    alpha: float
    information_ratio: float
    tracking_error: float
    volatility: float
    skewness: float
    kurtosis: float
    trade_count: int
    avg_trade_duration: float

    # Prediction metrics
    directional_accuracy: float
    prediction_correlation: float
    prediction_rmse: float
    prediction_mae: float
    prediction_r2: float

@dataclass
class ValidationMetrics:
    """Validation metrics for model performance"""
    cv_scores: List[float]
    cv_mean: float
    cv_std: float
    oos_score: float
    stability_score: float
    robustness_score: float

class TimeSeriesValidator:
    """Time series cross-validation for financial data"""

    def __init__(
        self,
        n_splits: int = 5,
        test_size: Optional[int] = None,
        gap: int = 0,
        expanding_window: bool = False
    ):
        self.n_splits = n_splits
        self.test_size = test_size
        self.gap = gap
        self.expanding_window = expanding_window

    def split(self, X: np.ndarray, y: np.ndarray = None) -> List[Tuple[np.ndarray, np.ndarray]]:
        """Generate time series cross-validation splits"""
        n_samples = len(X)

        if self.test_size is None:
            test_size = n_samples // (self.n_splits + 1)
        else:
            test_size = self.test_size

        splits = []

        for i in range(self.n_splits):
            if self.expanding_window:
                # Expanding window: training set grows with each split
                train_end = n_samples - (self.n_splits - i) * test_size - self.gap
                train_start = 0
            else:
                # Rolling window: training set size remains constant
                train_end = n_samples - (self.n_splits - i) * test_size - self.gap
                train_start = max(0, train_end - test_size * 3)  # 3x test size for training

            test_start = train_end + self.gap
            test_end = test_start + test_size

            if train_start < train_end and test_start < test_end and test_end <= n_samples:
                train_indices = np.arange(train_start, train_end)
                test_indices = np.arange(test_start, test_end)
                splits.append((train_indices, test_indices))

        return splits

    def cross_validate(
        self,
        model,
        X: np.ndarray,
        y: np.ndarray,
        scoring_func: Callable = None,
        fit_params: Dict = None
    ) -> ValidationMetrics:
        """Perform time series cross-validation"""

        if scoring_func is None:
            scoring_func = lambda y_true, y_pred: np.corrcoef(y_true, y_pred)[0, 1]

        if fit_params is None:
            fit_params = {}

        splits = self.split(X, y)
        cv_scores = []

        for train_idx, test_idx in splits:
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]

            # Clone model to avoid state persistence
            if hasattr(model, 'clone'):
                model_copy = model.clone()
            else:
                # For custom models, assume they can be re-initialized
                model_copy = model

            # Fit model
            if hasattr(model_copy, 'fit'):
                model_copy.fit(X_train, y_train, **fit_params)

            # Predict
            predictions = model_copy.predict(X_test)

            # Score
            score = scoring_func(y_test, predictions)
            cv_scores.append(score)

        # Calculate stability and robustness
        cv_mean = np.mean(cv_scores)
        cv_std = np.std(cv_scores)
        stability_score = 1 - (cv_std / (abs(cv_mean) + 1e-8))  # Higher is more stable
        robustness_score = np.min(cv_scores) / (cv_mean + 1e-8)  # Worst case performance

        # Out-of-sample test on last split
        train_idx, test_idx = splits[-1]
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        if hasattr(model, 'clone'):
            final_model = model.clone()
        else:
            final_model = model

        final_model.fit(X_train, y_train, **fit_params)
        oos_predictions = final_model.predict(X_test)
        oos_score = scoring_func(y_test, oos_predictions)

        return ValidationMetrics(
            cv_scores=cv_scores,
            cv_mean=cv_mean,
            cv_std=cv_std,
            oos_score=oos_score,
            stability_score=stability_score,
            robustness_score=robustness_score
        )

class WalkForwardAnalyzer:
    """Walk-forward analysis for trading strategies"""

    def __init__(
        self,
        train_window: int = 252,  # 1 year of trading days
        test_window: int = 21,   # 1 month
        step_size: int = 21,     # Rebalancing frequency
        min_train_size: int = 100
    ):
        self.train_window = train_window
        self.test_window = test_window
        self.step_size = step_size
        self.min_train_size = min_train_size

    def analyze(
        self,
        model,
        X: pd.DataFrame,
        y: pd.Series,
        prices: pd.Series = None
    ) -> Tuple[pd.DataFrame, BacktestResults]:
        """Perform walk-forward analysis"""

        results = []
        current_pos = self.train_window

        while current_pos + self.test_window <= len(X):
            # Define training and testing periods
            train_start = max(0, current_pos - self.train_window)
            train_end = current_pos
            test_start = current_pos
            test_end = min(len(X), current_pos + self.test_window)

            # Get data
            X_train = X.iloc[train_start:train_end]
            y_train = y.iloc[train_start:train_end]
            X_test = X.iloc[test_start:test_end]
            y_test = y.iloc[test_start:test_end]

            if len(X_train) < self.min_train_size:
                current_pos += self.step_size
                continue

            try:
                # Train model
                if hasattr(model, 'clone'):
                    model_copy = model.clone()
                else:
                    model_copy = model

                model_copy.fit(X_train.values, y_train.values)

                # Predict
                predictions = model_copy.predict(X_test.values)

                # Store results
                test_dates = X_test.index
                for i, (date, pred, actual) in enumerate(zip(test_dates, predictions, y_test.values)):
                    results.append({
                        'date': date,
                        'prediction': pred,
                        'actual': actual,
                        'train_start': X_train.index[0],
                        'train_end': X_train.index[-1]
                    })

            except Exception as e:
                print(f"Error in walk-forward step {current_pos}: {e}")

            current_pos += self.step_size

        # Convert to DataFrame
        results_df = pd.DataFrame(results)
        results_df.set_index('date', inplace=True)

        # Calculate backtest results if prices are provided
        backtest_results = None
        if prices is not None:
            backtest_results = self._calculate_backtest_metrics(
                results_df, prices.reindex(results_df.index)
            )

        return results_df, backtest_results

    def _calculate_backtest_metrics(
        self,
        results_df: pd.DataFrame,
        prices: pd.Series
    ) -> BacktestResults:
        """Calculate comprehensive backtest metrics"""

        # Generate trading signals (simplified: long if prediction > 0)
        signals = np.where(results_df['prediction'] > 0, 1, -1)
        returns = prices.pct_change().dropna()

        # Align signals with returns
        aligned_returns = returns.reindex(results_df.index).fillna(0)
        strategy_returns = signals * aligned_returns.values

        # Remove any remaining NaN values
        strategy_returns = strategy_returns[~np.isnan(strategy_returns)]
        if len(strategy_returns) == 0:
            return self._create_empty_backtest_results()

        # Calculate basic metrics
        total_return = (1 + strategy_returns).prod() - 1
        annual_return = (1 + total_return) ** (252 / len(strategy_returns)) - 1
        volatility = np.std(strategy_returns) * np.sqrt(252)

        # Risk-adjusted metrics
        sharpe_ratio = annual_return / volatility if volatility > 0 else 0
        downside_returns = strategy_returns[strategy_returns < 0]
        downside_vol = np.std(downside_returns) * np.sqrt(252) if len(downside_returns) > 0 else 0
        sortino_ratio = annual_return / downside_vol if downside_vol > 0 else 0

        # Drawdown analysis
        cumulative_returns = (1 + strategy_returns).cumprod()
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdowns = (cumulative_returns - running_max) / running_max
        max_drawdown = np.min(drawdowns)
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0

        # Trading metrics
        win_rate = np.sum(strategy_returns > 0) / len(strategy_returns)
        gross_profits = np.sum(strategy_returns[strategy_returns > 0])
        gross_losses = abs(np.sum(strategy_returns[strategy_returns < 0]))
        profit_factor = gross_profits / gross_losses if gross_losses > 0 else np.inf

        # VaR and Expected Shortfall
        var_95 = np.percentile(strategy_returns, 5)
        var_99 = np.percentile(strategy_returns, 1)
        es_95 = np.mean(strategy_returns[strategy_returns <= var_95])

        # Market comparison (using aligned returns as benchmark)
        benchmark_returns = aligned_returns.values
        if len(benchmark_returns) > 0 and np.std(benchmark_returns) > 0:
            beta = np.cov(strategy_returns, benchmark_returns)[0, 1] / np.var(benchmark_returns)
            benchmark_annual_return = (1 + np.mean(benchmark_returns)) ** 252 - 1
            alpha = annual_return - beta * benchmark_annual_return
            tracking_error = np.std(strategy_returns - benchmark_returns) * np.sqrt(252)
            information_ratio = (annual_return - benchmark_annual_return) / tracking_error if tracking_error > 0 else 0
        else:
            beta = alpha = tracking_error = information_ratio = 0

        # Higher order moments
        skewness = self._calculate_skewness(strategy_returns)
        kurtosis = self._calculate_kurtosis(strategy_returns)

        # Prediction metrics
        predictions = results_df['prediction'].values
        actuals = results_df['actual'].values

        # Remove NaN values for correlation calculation
        mask = ~(np.isnan(predictions) | np.isnan(actuals))
        clean_predictions = predictions[mask]
        clean_actuals = actuals[mask]

        if len(clean_predictions) > 1:
            directional_accuracy = np.mean(np.sign(clean_predictions) == np.sign(clean_actuals))
            prediction_correlation = np.corrcoef(clean_predictions, clean_actuals)[0, 1]
            prediction_rmse = np.sqrt(np.mean((clean_predictions - clean_actuals) ** 2))
            prediction_mae = np.mean(np.abs(clean_predictions - clean_actuals))
            prediction_r2 = r2_score(clean_actuals, clean_predictions)
        else:
            directional_accuracy = prediction_correlation = 0
            prediction_rmse = prediction_mae = prediction_r2 = 0

        return BacktestResults(
            total_return=total_return,
            annual_return=annual_return,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            calmar_ratio=calmar_ratio,
            win_rate=win_rate,
            profit_factor=profit_factor,
            var_95=var_95,
            var_99=var_99,
            expected_shortfall_95=es_95,
            beta=beta,
            alpha=alpha,
            information_ratio=information_ratio,
            tracking_error=tracking_error,
            volatility=volatility,
            skewness=skewness,
            kurtosis=kurtosis,
            trade_count=len(strategy_returns),
            avg_trade_duration=1.0,  # Daily rebalancing
            directional_accuracy=directional_accuracy,
            prediction_correlation=prediction_correlation,
            prediction_rmse=prediction_rmse,
            prediction_mae=prediction_mae,
            prediction_r2=prediction_r2
        )

    def _calculate_skewness(self, returns: np.ndarray) -> float:
        """Calculate skewness of returns"""
        if len(returns) < 3:
            return 0
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        if std_return == 0:
            return 0
        return np.mean(((returns - mean_return) / std_return) ** 3)

    def _calculate_kurtosis(self, returns: np.ndarray) -> float:
        """Calculate excess kurtosis of returns"""
        if len(returns) < 4:
            return 0
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        if std_return == 0:
            return 0
        return np.mean(((returns - mean_return) / std_return) ** 4) - 3

    def _create_empty_backtest_results(self) -> BacktestResults:
        """Create empty backtest results for error cases"""
        return BacktestResults(
            total_return=0, annual_return=0, sharpe_ratio=0, sortino_ratio=0,
            max_drawdown=0, calmar_ratio=0, win_rate=0, profit_factor=0,
            var_95=0, var_99=0, expected_shortfall_95=0, beta=0, alpha=0,
            information_ratio=0, tracking_error=0, volatility=0,
            skewness=0, kurtosis=0, trade_count=0, avg_trade_duration=0,
            directional_accuracy=0, prediction_correlation=0,
            prediction_rmse=0, prediction_mae=0, prediction_r2=0
        )

class PerformanceAnalyzer:
    """Comprehensive performance analysis for trading models"""

    def __init__(self, risk_free_rate: float = 0.02):
        self.risk_free_rate = risk_free_rate

    def analyze_predictions(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        sample_weight: np.ndarray = None
    ) -> Dict[str, float]:
        """Analyze prediction quality"""

        # Remove NaN values
        mask = ~(np.isnan(y_true) | np.isnan(y_pred))
        y_true_clean = y_true[mask]
        y_pred_clean = y_pred[mask]

        if len(y_true_clean) == 0:
            return {}

        metrics = {}

        # Basic prediction metrics
        metrics['rmse'] = np.sqrt(mean_squared_error(y_true_clean, y_pred_clean))
        metrics['mae'] = mean_absolute_error(y_true_clean, y_pred_clean)
        metrics['r2'] = r2_score(y_true_clean, y_pred_clean)

        # Correlation
        if len(y_true_clean) > 1:
            metrics['correlation'] = np.corrcoef(y_true_clean, y_pred_clean)[0, 1]
        else:
            metrics['correlation'] = 0

        # Directional accuracy
        if len(y_true_clean) > 0:
            correct_direction = np.sign(y_true_clean) == np.sign(y_pred_clean)
            metrics['directional_accuracy'] = np.mean(correct_direction)

        # Hit rate for different thresholds
        for threshold in [0.01, 0.02, 0.05]:
            significant_moves = np.abs(y_true_clean) > threshold
            if np.sum(significant_moves) > 0:
                hit_rate = np.mean(
                    np.sign(y_true_clean[significant_moves]) == np.sign(y_pred_clean[significant_moves])
                )
                metrics[f'hit_rate_{int(threshold*100)}pct'] = hit_rate

        # Prediction error analysis
        errors = y_pred_clean - y_true_clean
        metrics['mean_error'] = np.mean(errors)
        metrics['error_std'] = np.std(errors)
        metrics['error_skewness'] = self._calculate_skewness(errors)

        return metrics

    def analyze_trading_performance(
        self,
        returns: np.ndarray,
        benchmark_returns: np.ndarray = None,
        positions: np.ndarray = None
    ) -> Dict[str, float]:
        """Analyze trading strategy performance"""

        # Remove NaN values
        returns_clean = returns[~np.isnan(returns)]
        if len(returns_clean) == 0:
            return {}

        metrics = {}

        # Basic return metrics
        total_return = (1 + returns_clean).prod() - 1
        annual_return = (1 + total_return) ** (252 / len(returns_clean)) - 1
        metrics['total_return'] = total_return
        metrics['annual_return'] = annual_return

        # Risk metrics
        volatility = np.std(returns_clean) * np.sqrt(252)
        metrics['volatility'] = volatility

        # Sharpe ratio
        excess_return = annual_return - self.risk_free_rate
        metrics['sharpe_ratio'] = excess_return / volatility if volatility > 0 else 0

        # Sortino ratio
        downside_returns = returns_clean[returns_clean < 0]
        if len(downside_returns) > 0:
            downside_vol = np.std(downside_returns) * np.sqrt(252)
            metrics['sortino_ratio'] = excess_return / downside_vol
        else:
            metrics['sortino_ratio'] = np.inf

        # Drawdown analysis
        cumulative_returns = (1 + returns_clean).cumprod()
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdowns = (cumulative_returns - running_max) / running_max
        metrics['max_drawdown'] = np.min(drawdowns)
        metrics['avg_drawdown'] = np.mean(drawdowns[drawdowns < 0])
        metrics['calmar_ratio'] = annual_return / abs(metrics['max_drawdown']) if metrics['max_drawdown'] != 0 else 0

        # VaR and Expected Shortfall
        metrics['var_95'] = np.percentile(returns_clean, 5)
        metrics['var_99'] = np.percentile(returns_clean, 1)
        tail_returns = returns_clean[returns_clean <= metrics['var_95']]
        metrics['expected_shortfall_95'] = np.mean(tail_returns) if len(tail_returns) > 0 else 0

        # Win rate and profit factor
        winning_returns = returns_clean[returns_clean > 0]
        losing_returns = returns_clean[returns_clean < 0]
        metrics['win_rate'] = len(winning_returns) / len(returns_clean)

        if len(losing_returns) > 0:
            metrics['profit_factor'] = np.sum(winning_returns) / abs(np.sum(losing_returns))
        else:
            metrics['profit_factor'] = np.inf

        # Higher order moments
        metrics['skewness'] = self._calculate_skewness(returns_clean)
        metrics['kurtosis'] = self._calculate_kurtosis(returns_clean)

        # Benchmark comparison
        if benchmark_returns is not None:
            benchmark_clean = benchmark_returns[~np.isnan(benchmark_returns)]
            if len(benchmark_clean) == len(returns_clean):
                # Beta
                covariance = np.cov(returns_clean, benchmark_clean)[0, 1]
                benchmark_variance = np.var(benchmark_clean)
                beta = covariance / benchmark_variance if benchmark_variance > 0 else 0
                metrics['beta'] = beta

                # Alpha
                benchmark_annual_return = (1 + np.mean(benchmark_clean)) ** 252 - 1
                alpha = annual_return - beta * benchmark_annual_return
                metrics['alpha'] = alpha

                # Information ratio
                active_returns = returns_clean - benchmark_clean
                tracking_error = np.std(active_returns) * np.sqrt(252)
                metrics['tracking_error'] = tracking_error

                if tracking_error > 0:
                    metrics['information_ratio'] = (annual_return - benchmark_annual_return) / tracking_error
                else:
                    metrics['information_ratio'] = 0

        # Position analysis
        if positions is not None:
            positions_clean = positions[~np.isnan(positions)]
            if len(positions_clean) == len(returns_clean):
                # Position turnover
                position_changes = np.abs(np.diff(positions_clean))
                metrics['avg_turnover'] = np.mean(position_changes)

                # Long/short breakdown
                long_returns = returns_clean[positions_clean > 0]
                short_returns = returns_clean[positions_clean < 0]

                if len(long_returns) > 0:
                    metrics['long_win_rate'] = np.sum(long_returns > 0) / len(long_returns)
                    metrics['avg_long_return'] = np.mean(long_returns)

                if len(short_returns) > 0:
                    metrics['short_win_rate'] = np.sum(short_returns > 0) / len(short_returns)
                    metrics['avg_short_return'] = np.mean(short_returns)

        return metrics

    def _calculate_skewness(self, data: np.ndarray) -> float:
        """Calculate skewness"""
        if len(data) < 3:
            return 0
        mean_val = np.mean(data)
        std_val = np.std(data)
        if std_val == 0:
            return 0
        return np.mean(((data - mean_val) / std_val) ** 3)

    def _calculate_kurtosis(self, data: np.ndarray) -> float:
        """Calculate excess kurtosis"""
        if len(data) < 4:
            return 0
        mean_val = np.mean(data)
        std_val = np.std(data)
        if std_val == 0:
            return 0
        return np.mean(((data - mean_val) / std_val) ** 4) - 3

class StressTestAnalyzer:
    """Stress testing framework for trading models"""

    def __init__(self):
        self.stress_scenarios = {
            'market_crash': {'return_shock': -0.20, 'vol_shock': 2.0},
            'volatility_spike': {'return_shock': 0.0, 'vol_shock': 3.0},
            'trending_market': {'trend': 0.15, 'vol_shock': 0.5},
            'low_volatility': {'return_shock': 0.0, 'vol_shock': 0.3},
            'high_correlation': {'correlation_shock': 0.9}
        }

    def run_stress_tests(
        self,
        model,
        X: np.ndarray,
        y: np.ndarray,
        base_metrics: Dict[str, float]
    ) -> Dict[str, Dict[str, float]]:
        """Run stress tests on model"""

        stress_results = {}

        for scenario_name, scenario_params in self.stress_scenarios.items():
            try:
                # Generate stressed data
                X_stressed, y_stressed = self._generate_stressed_data(X, y, scenario_params)

                # Test model on stressed data
                predictions = model.predict(X_stressed)

                # Calculate performance under stress
                analyzer = PerformanceAnalyzer()
                stress_metrics = analyzer.analyze_predictions(y_stressed, predictions)

                # Calculate metric deterioration
                deterioration = {}
                for metric, value in stress_metrics.items():
                    if metric in base_metrics:
                        base_value = base_metrics[metric]
                        if base_value != 0:
                            deterioration[f'{metric}_change'] = (value - base_value) / base_value
                        else:
                            deterioration[f'{metric}_change'] = 0

                stress_results[scenario_name] = {**stress_metrics, **deterioration}

            except Exception as e:
                print(f"Error in stress test {scenario_name}: {e}")
                stress_results[scenario_name] = {}

        return stress_results

    def _generate_stressed_data(
        self,
        X: np.ndarray,
        y: np.ndarray,
        scenario_params: Dict[str, float]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Generate stressed version of data"""

        X_stressed = X.copy()
        y_stressed = y.copy()

        # Apply return shock
        if 'return_shock' in scenario_params:
            shock = scenario_params['return_shock']
            y_stressed = y_stressed + shock

        # Apply volatility shock
        if 'vol_shock' in scenario_params:
            vol_multiplier = scenario_params['vol_shock']
            noise = np.random.normal(0, np.std(y) * (vol_multiplier - 1), len(y))
            y_stressed = y_stressed + noise

        # Apply trend
        if 'trend' in scenario_params:
            trend = scenario_params['trend']
            trend_component = np.linspace(0, trend, len(y))
            y_stressed = y_stressed + trend_component

        # Apply correlation shock (simplified)
        if 'correlation_shock' in scenario_params:
            target_corr = scenario_params['correlation_shock']
            # Add correlated noise to features
            if X.shape[1] > 1:
                corr_noise = np.random.multivariate_normal(
                    np.zeros(X.shape[1]),
                    target_corr * np.ones((X.shape[1], X.shape[1])) + (1 - target_corr) * np.eye(X.shape[1]),
                    X.shape[0]
                )
                X_stressed = X_stressed + 0.1 * corr_noise

        return X_stressed, y_stressed

class ValidationFramework:
    """Comprehensive validation framework orchestrator"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.ts_validator = TimeSeriesValidator(
            n_splits=self.config.get('cv_folds', 5),
            gap=self.config.get('cv_gap', 1)
        )
        self.wf_analyzer = WalkForwardAnalyzer(
            train_window=self.config.get('train_window', 252),
            test_window=self.config.get('test_window', 21)
        )
        self.performance_analyzer = PerformanceAnalyzer(
            risk_free_rate=self.config.get('risk_free_rate', 0.02)
        )
        self.stress_tester = StressTestAnalyzer()

    def comprehensive_validation(
        self,
        model,
        X: pd.DataFrame,
        y: pd.Series,
        prices: pd.Series = None,
        benchmark_returns: pd.Series = None
    ) -> Dict[str, Any]:
        """Run comprehensive validation analysis"""

        results = {}

        # Time series cross-validation
        print("Running time series cross-validation...")
        cv_results = self.ts_validator.cross_validate(model, X.values, y.values)
        results['cross_validation'] = cv_results

        # Walk-forward analysis
        print("Running walk-forward analysis...")
        wf_results, backtest_results = self.wf_analyzer.analyze(model, X, y, prices)
        results['walk_forward'] = wf_results
        results['backtest'] = backtest_results

        # Prediction analysis
        print("Analyzing prediction quality...")
        if not wf_results.empty:
            pred_metrics = self.performance_analyzer.analyze_predictions(
                wf_results['actual'].values,
                wf_results['prediction'].values
            )
            results['prediction_metrics'] = pred_metrics

        # Trading performance analysis
        if backtest_results is not None:
            print("Analyzing trading performance...")
            # Generate simple strategy returns for analysis
            signals = np.where(wf_results['prediction'] > 0, 1, -1)
            if prices is not None:
                returns = prices.pct_change().reindex(wf_results.index).fillna(0)
                strategy_returns = signals * returns.values

                trading_metrics = self.performance_analyzer.analyze_trading_performance(
                    strategy_returns,
                    benchmark_returns.reindex(wf_results.index).values if benchmark_returns is not None else None
                )
                results['trading_metrics'] = trading_metrics

        # Stress testing
        print("Running stress tests...")
        if 'prediction_metrics' in results:
            stress_results = self.stress_tester.run_stress_tests(
                model, X.values, y.values, results['prediction_metrics']
            )
            results['stress_tests'] = stress_results

        return results

    def generate_validation_report(self, results: Dict[str, Any]) -> str:
        """Generate human-readable validation report"""

        report = ["=== MODEL VALIDATION REPORT ===\n"]

        # Cross-validation results
        if 'cross_validation' in results:
            cv = results['cross_validation']
            report.append("Cross-Validation Results:")
            report.append(f"  Mean Score: {cv.cv_mean:.4f}")
            report.append(f"  Std Score: {cv.cv_std:.4f}")
            report.append(f"  Stability: {cv.stability_score:.4f}")
            report.append(f"  Robustness: {cv.robustness_score:.4f}")
            report.append(f"  OOS Score: {cv.oos_score:.4f}\n")

        # Prediction metrics
        if 'prediction_metrics' in results:
            pred = results['prediction_metrics']
            report.append("Prediction Quality:")
            report.append(f"  Correlation: {pred.get('correlation', 0):.4f}")
            report.append(f"  Directional Accuracy: {pred.get('directional_accuracy', 0):.4f}")
            report.append(f"  RMSE: {pred.get('rmse', 0):.4f}")
            report.append(f"  R²: {pred.get('r2', 0):.4f}\n")

        # Backtest results
        if 'backtest' in results and results['backtest'] is not None:
            bt = results['backtest']
            report.append("Backtest Performance:")
            report.append(f"  Annual Return: {bt.annual_return:.2%}")
            report.append(f"  Sharpe Ratio: {bt.sharpe_ratio:.4f}")
            report.append(f"  Max Drawdown: {bt.max_drawdown:.2%}")
            report.append(f"  Win Rate: {bt.win_rate:.2%}")
            report.append(f"  Profit Factor: {bt.profit_factor:.4f}\n")

        # Stress test summary
        if 'stress_tests' in results:
            report.append("Stress Test Summary:")
            for scenario, metrics in results['stress_tests'].items():
                if 'correlation_change' in metrics:
                    change = metrics['correlation_change']
                    report.append(f"  {scenario}: {change:.2%} correlation change")
            report.append("")

        return "\n".join(report)