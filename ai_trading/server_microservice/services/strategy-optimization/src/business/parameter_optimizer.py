"""
Parameter Optimizer - Optuna Framework Integration
Advanced hyperparameter optimization with Bayesian optimization, grid search, and random search
"""

import asyncio
import logging
import time
import uuid
import json
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional, Callable
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import optuna
from optuna import Trial
from optuna.samplers import TPESampler, GridSampler, RandomSampler, CmaEsSampler
from optuna.pruners import MedianPruner, SuccessiveHalvingPruner
from optuna.storages import InMemoryStorage
import plotly.graph_objects as go
import plotly.express as px
from concurrent.futures import ThreadPoolExecutor
import pickle
import joblib

from ..models.strategy_models import (
    StrategyDefinition,
    StrategyParameters,
    OptimizationConfig,
    OptimizationResult,
    PerformanceMetrics,
    OptimizationObjective
)

logger = logging.getLogger(__name__)


class ParameterOptimizerError(Exception):
    """Parameter optimizer specific errors"""
    pass


class OptimizationObjectiveHandler:
    """Handle different optimization objectives and multi-objective optimization"""
    
    def __init__(self, objectives: List[OptimizationObjective]):
        self.objectives = objectives
        self.is_multi_objective = len(objectives) > 1
        
        # Objective weights for composite scoring
        self.weights = {
            OptimizationObjective.MAXIMIZE_PROFIT: 0.3,
            OptimizationObjective.MAXIMIZE_SHARPE: 0.3,
            OptimizationObjective.MINIMIZE_DRAWDOWN: 0.2,
            OptimizationObjective.MAXIMIZE_WIN_RATE: 0.1,
            OptimizationObjective.MINIMIZE_VOLATILITY: 0.05,
            OptimizationObjective.MAXIMIZE_PROFIT_FACTOR: 0.05
        }
    
    def calculate_objective_value(
        self, 
        performance: PerformanceMetrics,
        objective: OptimizationObjective
    ) -> float:
        """Calculate objective value from performance metrics"""
        
        if objective == OptimizationObjective.MAXIMIZE_PROFIT:
            return performance.total_return
        elif objective == OptimizationObjective.MAXIMIZE_SHARPE:
            return performance.sharpe_ratio
        elif objective == OptimizationObjective.MINIMIZE_DRAWDOWN:
            return -abs(performance.max_drawdown)  # Negative for minimization
        elif objective == OptimizationObjective.MAXIMIZE_WIN_RATE:
            return performance.win_rate
        elif objective == OptimizationObjective.MINIMIZE_VOLATILITY:
            return -performance.volatility  # Negative for minimization
        elif objective == OptimizationObjective.MAXIMIZE_PROFIT_FACTOR:
            return performance.profit_factor
        else:
            return 0.0
    
    def calculate_composite_score(self, performance: PerformanceMetrics) -> float:
        """Calculate weighted composite score for multi-objective optimization"""
        
        score = 0.0
        for objective in self.objectives:
            value = self.calculate_objective_value(performance, objective)
            weight = self.weights.get(objective, 0.1)
            score += value * weight
        
        return score
    
    def get_optuna_directions(self) -> List[str]:
        """Get optimization directions for Optuna multi-objective optimization"""
        
        directions = []
        for objective in self.objectives:
            if objective in [OptimizationObjective.MINIMIZE_DRAWDOWN, OptimizationObjective.MINIMIZE_VOLATILITY]:
                directions.append("minimize")
            else:
                directions.append("maximize")
        
        return directions


class ParameterOptimizer:
    """
    Advanced Parameter Optimizer using Optuna framework
    Supports Bayesian optimization, grid search, random search, and CMA-ES
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize parameter optimizer with configuration"""
        self.config = config or {}
        
        # Optimization configuration
        self.n_trials = self.config.get('n_trials', 100)
        self.timeout = self.config.get('timeout', 3600)  # 1 hour default
        self.n_jobs = self.config.get('n_jobs', 1)
        
        # Sampler configuration
        self.sampler_type = self.config.get('sampler_type', 'tpe')  # tpe, random, grid, cmaes
        self.pruner_type = self.config.get('pruner_type', 'median')  # median, successive_halving, none
        
        # Study configuration
        self.study_name_prefix = self.config.get('study_name_prefix', 'strategy_optimization')
        self.storage_url = self.config.get('storage_url', None)  # None for in-memory
        
        # Early stopping
        self.early_stopping_rounds = self.config.get('early_stopping_rounds', 20)
        self.min_improvement = self.config.get('min_improvement', 0.01)
        
        # Caching and persistence
        self.cache_results = self.config.get('cache_results', True)
        self.save_intermediate = self.config.get('save_intermediate', True)
        
        # Results storage
        self.optimization_cache: Dict[str, Any] = {}
        self.trial_history: List[Dict[str, Any]] = []
        
        logger.info("ParameterOptimizer initialized successfully")
    
    async def optimize(
        self,
        strategy: StrategyDefinition,
        optimization_config: OptimizationConfig,
        backtest_engine=None
    ) -> OptimizationResult:
        """
        Run parameter optimization using Optuna framework
        
        Args:
            strategy: Strategy definition to optimize
            optimization_config: Optimization configuration
            backtest_engine: Backtesting engine for evaluation
            
        Returns:
            OptimizationResult with optimized parameters and analysis
        """
        
        try:
            logger.info(f"Starting parameter optimization for strategy: {strategy.strategy_id}")
            start_time = time.time()
            
            # Setup optimization
            self.strategy = strategy
            self.optimization_config = optimization_config
            self.backtest_engine = backtest_engine
            
            # Validate configuration
            await self._validate_optimization_config(optimization_config)
            
            # Setup objective handler
            self.objective_handler = OptimizationObjectiveHandler(optimization_config.objectives)
            
            # Generate optimization ID
            optimization_id = f"optuna_opt_{int(time.time())}_{strategy.strategy_id}"
            
            # Create Optuna study
            study = self._create_optuna_study(optimization_config, optimization_id)
            
            # Run optimization
            best_trial, all_trials = await self._run_optuna_optimization(study, optimization_config)
            
            # Extract results
            best_parameters = self._trial_to_parameters(best_trial)
            
            # Analyze optimization results
            convergence_info = self._analyze_convergence(all_trials)
            sensitivity_analysis = await self._perform_sensitivity_analysis(best_trial, all_trials)
            
            # Calculate stability score
            stability_score = self._calculate_stability_score(best_trial, all_trials)
            
            # Generate Pareto front for multi-objective
            pareto_front = self._extract_pareto_front(all_trials) if self.objective_handler.is_multi_objective else []
            
            # Get performance metrics for best parameters
            best_performance = await self._evaluate_parameters(best_parameters)
            
            # Calculate execution metrics
            optimization_time = time.time() - start_time
            cpu_time = optimization_time * self.n_jobs
            
            # Create optimization result
            optimization_result = OptimizationResult(
                optimization_id=optimization_id,
                strategy_id=strategy.strategy_id,
                optimization_method=f"Optuna-{self.sampler_type.upper()}",
                objectives=optimization_config.objectives,
                parameter_bounds=optimization_config.parameter_bounds,
                generations=len(all_trials),  # Using trials as generations
                population_size=1,  # Optuna processes one trial at a time
                best_parameters=best_parameters,
                best_fitness=best_trial.value if best_trial.value is not None else 0.0,
                fitness_history=self._extract_fitness_history(all_trials),
                pareto_front=pareto_front,
                convergence_generation=convergence_info.get("convergence_trial"),
                convergence_criterion=self.min_improvement,
                early_stopping=convergence_info.get("early_stopping", False),
                in_sample_performance=best_performance,
                evaluations_count=len(all_trials),
                optimization_time=optimization_time,
                cpu_time=cpu_time,
                parameter_sensitivity=sensitivity_analysis,
                stability_score=stability_score,
                created_at=datetime.now()
            )
            
            # Store optimization results
            if self.cache_results:
                self.optimization_cache[optimization_id] = {
                    'study': study,
                    'result': optimization_result,
                    'trials': all_trials
                }
            
            logger.info(f"Parameter optimization completed: {optimization_id}")
            logger.info(f"Best objective value: {best_trial.value}")
            logger.info(f"Optimization time: {optimization_time:.2f} seconds")
            
            return optimization_result
            
        except Exception as e:
            logger.error(f"Parameter optimization failed: {e}")
            raise ParameterOptimizerError(f"Optimization failed: {str(e)}")
    
    def _create_optuna_study(
        self,
        optimization_config: OptimizationConfig,
        optimization_id: str
    ) -> optuna.Study:
        """Create Optuna study with appropriate sampler and pruner"""
        
        # Setup sampler
        if self.sampler_type == 'tpe':
            sampler = TPESampler(
                n_startup_trials=max(10, len(optimization_config.parameters_to_optimize) * 2),
                n_ei_candidates=24
            )
        elif self.sampler_type == 'random':
            sampler = RandomSampler()
        elif self.sampler_type == 'cmaes':
            sampler = CmaEsSampler()
        elif self.sampler_type == 'grid':
            # Grid sampler requires search space definition
            search_space = self._create_grid_search_space(optimization_config)
            sampler = GridSampler(search_space)
        else:
            sampler = TPESampler()  # Default fallback
        
        # Setup pruner
        if self.pruner_type == 'median':
            pruner = MedianPruner(
                n_startup_trials=5,
                n_warmup_steps=10,
                interval_steps=1
            )
        elif self.pruner_type == 'successive_halving':
            pruner = SuccessiveHalvingPruner()
        else:
            pruner = optuna.pruners.NopPruner()  # No pruning
        
        # Setup storage
        if self.storage_url:
            storage = optuna.storages.RDBStorage(url=self.storage_url)
        else:
            storage = InMemoryStorage()
        
        # Create study
        study_name = f"{self.study_name_prefix}_{optimization_id}"
        
        if self.objective_handler.is_multi_objective:
            directions = self.objective_handler.get_optuna_directions()
            study = optuna.create_study(
                study_name=study_name,
                storage=storage,
                sampler=sampler,
                pruner=pruner,
                directions=directions,
                load_if_exists=True
            )
        else:
            # Single objective optimization
            direction = "maximize"  # Default, will be adjusted based on objective
            if optimization_config.objectives[0] in [OptimizationObjective.MINIMIZE_DRAWDOWN, OptimizationObjective.MINIMIZE_VOLATILITY]:
                direction = "minimize"
            
            study = optuna.create_study(
                study_name=study_name,
                storage=storage,
                sampler=sampler,
                pruner=pruner,
                direction=direction,
                load_if_exists=True
            )
        
        return study
    
    def _create_grid_search_space(self, optimization_config: OptimizationConfig) -> Dict[str, List[Any]]:
        """Create grid search space for GridSampler"""
        
        search_space = {}
        
        for param_name in optimization_config.parameters_to_optimize:
            if param_name in optimization_config.parameter_bounds:
                bounds = optimization_config.parameter_bounds[param_name]
                
                # Create grid points (simplified approach)
                if self._is_integer_parameter(param_name):
                    values = list(range(int(bounds[0]), int(bounds[1]) + 1, max(1, (int(bounds[1]) - int(bounds[0])) // 10)))
                else:
                    values = np.linspace(bounds[0], bounds[1], num=11).tolist()  # 11 points
                
                search_space[param_name] = values
        
        return search_space
    
    async def _run_optuna_optimization(
        self,
        study: optuna.Study,
        optimization_config: OptimizationConfig
    ) -> Tuple[optuna.Trial, List[optuna.Trial]]:
        """Run Optuna optimization with progress tracking"""
        
        # Define objective function
        if self.objective_handler.is_multi_objective:
            objective_func = self._multi_objective_function
        else:
            objective_func = self._single_objective_function
        
        # Setup early stopping callback
        early_stopping_callback = self._create_early_stopping_callback()
        
        # Run optimization
        logger.info(f"Running optimization with {self.n_trials} trials...")
        
        if self.n_jobs > 1:
            # Parallel optimization
            study.optimize(
                objective_func,
                n_trials=self.n_trials,
                timeout=self.timeout,
                n_jobs=self.n_jobs,
                callbacks=[early_stopping_callback] if early_stopping_callback else None
            )
        else:
            # Sequential optimization with progress tracking
            for trial_idx in range(self.n_trials):
                try:
                    study.optimize(objective_func, n_trials=1, timeout=None)
                    
                    if trial_idx % 10 == 0:
                        logger.info(f"Completed trial {trial_idx + 1}/{self.n_trials}")
                        if study.best_trial:
                            logger.info(f"Current best value: {study.best_trial.value}")
                    
                    # Check early stopping
                    if early_stopping_callback and early_stopping_callback(study, None):
                        logger.info(f"Early stopping triggered at trial {trial_idx + 1}")
                        break
                        
                except Exception as e:
                    logger.warning(f"Trial {trial_idx} failed: {e}")
                    continue
        
        # Get results
        best_trial = study.best_trial
        all_trials = study.trials
        
        logger.info(f"Optimization completed with {len(all_trials)} trials")
        logger.info(f"Best trial: {best_trial.number} with value: {best_trial.value}")
        
        return best_trial, all_trials
    
    def _single_objective_function(self, trial: Trial) -> float:
        """Single objective function for Optuna optimization"""
        
        try:
            # Sample parameters
            parameters = self._sample_parameters(trial)
            
            # Evaluate parameters
            performance = asyncio.run(self._evaluate_parameters(parameters))
            
            # Calculate objective value
            objective_value = self.objective_handler.calculate_objective_value(
                performance, self.optimization_config.objectives[0]
            )
            
            # Store trial information
            trial.set_user_attr('performance_metrics', performance.dict())
            trial.set_user_attr('parameters', parameters.dict())
            
            # Add to trial history
            self.trial_history.append({
                'trial_number': trial.number,
                'value': objective_value,
                'parameters': parameters.dict(),
                'performance': performance.dict()
            })
            
            return objective_value
            
        except Exception as e:
            logger.error(f"Trial {trial.number} evaluation failed: {e}")
            # Return poor value for failed trials
            if self.optimization_config.objectives[0] in [OptimizationObjective.MINIMIZE_DRAWDOWN, OptimizationObjective.MINIMIZE_VOLATILITY]:
                return 1.0  # High value for minimization objectives
            else:
                return -1.0  # Low value for maximization objectives
    
    def _multi_objective_function(self, trial: Trial) -> List[float]:
        """Multi-objective function for Optuna optimization"""
        
        try:
            # Sample parameters
            parameters = self._sample_parameters(trial)
            
            # Evaluate parameters
            performance = asyncio.run(self._evaluate_parameters(parameters))
            
            # Calculate objective values
            objective_values = []
            for objective in self.optimization_config.objectives:
                value = self.objective_handler.calculate_objective_value(performance, objective)
                objective_values.append(value)
            
            # Store trial information
            trial.set_user_attr('performance_metrics', performance.dict())
            trial.set_user_attr('parameters', parameters.dict())
            
            # Add to trial history
            self.trial_history.append({
                'trial_number': trial.number,
                'values': objective_values,
                'parameters': parameters.dict(),
                'performance': performance.dict()
            })
            
            return objective_values
            
        except Exception as e:
            logger.error(f"Multi-objective trial {trial.number} evaluation failed: {e}")
            # Return poor values for failed trials
            return [0.0 for _ in self.optimization_config.objectives]
    
    def _sample_parameters(self, trial: Trial) -> StrategyParameters:
        """Sample parameters using Optuna trial interface"""
        
        sampled_params = {}
        
        for param_name in self.optimization_config.parameters_to_optimize:
            if param_name not in self.optimization_config.parameter_bounds:
                continue
            
            bounds = self.optimization_config.parameter_bounds[param_name]
            
            if self._is_integer_parameter(param_name):
                value = trial.suggest_int(param_name, int(bounds[0]), int(bounds[1]))
            else:
                value = trial.suggest_float(param_name, bounds[0], bounds[1])
            
            sampled_params[param_name] = value
        
        # Create parameters object with current strategy parameters as base
        base_params = self.strategy.parameters.dict()
        base_params.update(sampled_params)
        
        return StrategyParameters(**base_params)
    
    async def _evaluate_parameters(self, parameters: StrategyParameters) -> PerformanceMetrics:
        """Evaluate strategy parameters using backtest engine"""
        
        try:
            if self.backtest_engine:
                # Create test strategy with new parameters
                test_strategy = self.strategy.copy()
                test_strategy.parameters = parameters
                
                # Run backtest evaluation
                backtest_result = await self.backtest_engine.evaluate_strategy(test_strategy)
                return backtest_result.performance_metrics
            else:
                # Use synthetic performance for testing
                return self._generate_synthetic_performance(parameters)
                
        except Exception as e:
            logger.error(f"Parameter evaluation failed: {e}")
            # Return poor performance metrics
            return PerformanceMetrics(
                total_return=-0.1, annual_return=-0.1, excess_return=-0.1,
                volatility=0.3, sharpe_ratio=-0.5, sortino_ratio=-0.5,
                max_drawdown=-0.2, var_95=-0.05, cvar_95=-0.08,
                total_trades=10, winning_trades=3, losing_trades=7,
                win_rate=0.3, profit_factor=0.5, avg_trade_return=-0.01,
                avg_win_return=0.02, avg_loss_return=-0.02, calmar_ratio=-0.5,
                omega_ratio=0.8, tail_ratio=1.5, skewness=-1.0, kurtosis=4.0,
                market_correlation=0.5, beta=1.2, alpha=-0.05,
                up_market_capture=0.8, down_market_capture=1.2
            )
    
    def _generate_synthetic_performance(self, parameters: StrategyParameters) -> PerformanceMetrics:
        """Generate synthetic performance metrics for testing"""
        
        # Base performance with parameter influence
        base_return = 0.08
        base_sharpe = 1.0
        base_drawdown = -0.06
        
        # Parameter influence (simplified model)
        if hasattr(parameters, 'sma_fast_period') and hasattr(parameters, 'sma_slow_period'):
            ratio = parameters.sma_slow_period / max(parameters.sma_fast_period, 1)
            return_multiplier = 1 + 0.2 * np.sin(ratio * 0.1)
            sharpe_multiplier = 1 + 0.1 * np.cos(ratio * 0.15)
            
            base_return *= return_multiplier
            base_sharpe *= sharpe_multiplier
        
        if hasattr(parameters, 'rsi_period'):
            rsi_effect = 1 + 0.05 * np.sin(parameters.rsi_period * 0.1)
            base_return *= rsi_effect
        
        # Add controlled randomness
        noise_factor = 0.05
        return_noise = np.random.normal(0, noise_factor * base_return)
        sharpe_noise = np.random.normal(0, noise_factor * base_sharpe)
        
        final_return = base_return + return_noise
        final_sharpe = base_sharpe + sharpe_noise
        
        return PerformanceMetrics(
            total_return=final_return,
            annual_return=final_return,
            excess_return=final_return * 0.8,
            volatility=0.12 + abs(np.random.normal(0, 0.02)),
            sharpe_ratio=final_sharpe,
            sortino_ratio=final_sharpe * 1.2,
            max_drawdown=base_drawdown * (1 + abs(np.random.normal(0, 0.3))),
            var_95=-0.015,
            cvar_95=-0.025,
            total_trades=random.randint(80, 300),
            winning_trades=random.randint(50, 200),
            losing_trades=random.randint(30, 100),
            win_rate=random.uniform(0.55, 0.75),
            profit_factor=random.uniform(1.3, 2.2),
            avg_trade_return=final_return / 150,
            avg_win_return=0.015,
            avg_loss_return=-0.008,
            calmar_ratio=abs(final_return / base_drawdown) if base_drawdown != 0 else 0.0,
            omega_ratio=1.4,
            tail_ratio=2.2,
            skewness=0.2,
            kurtosis=3.5,
            market_correlation=0.4,
            beta=0.9,
            alpha=0.015,
            up_market_capture=1.05,
            down_market_capture=0.95
        )
    
    def _trial_to_parameters(self, trial: optuna.Trial) -> StrategyParameters:
        """Convert Optuna trial to StrategyParameters"""
        
        # Get parameters from trial
        trial_params = {}
        for param_name in self.optimization_config.parameters_to_optimize:
            if param_name in trial.params:
                trial_params[param_name] = trial.params[param_name]
        
        # Create parameters object with base parameters
        base_params = self.strategy.parameters.dict()
        base_params.update(trial_params)
        
        return StrategyParameters(**base_params)
    
    def _create_early_stopping_callback(self) -> Optional[Callable]:
        """Create early stopping callback for Optuna optimization"""
        
        if self.early_stopping_rounds <= 0:
            return None
        
        def early_stopping_callback(study: optuna.Study, trial: optuna.Trial) -> None:
            """Early stopping callback function"""
            
            if len(study.trials) < self.early_stopping_rounds:
                return
            
            # Get recent trial values
            recent_values = []
            for t in study.trials[-self.early_stopping_rounds:]:
                if t.value is not None:
                    recent_values.append(t.value)
            
            if len(recent_values) < self.early_stopping_rounds:
                return
            
            # Check for improvement
            if len(recent_values) > 1:
                best_recent = max(recent_values)
                worst_recent = min(recent_values)
                improvement = abs(best_recent - worst_recent)
                
                if improvement < self.min_improvement:
                    study.stop()
                    logger.info(f"Early stopping: No improvement > {self.min_improvement} in last {self.early_stopping_rounds} trials")
        
        return early_stopping_callback
    
    def _analyze_convergence(self, trials: List[optuna.Trial]) -> Dict[str, Any]:
        """Analyze convergence characteristics of optimization"""
        
        convergence_info = {
            "convergence_trial": None,
            "early_stopping": False,
            "improvement_rate": 0.0,
            "final_stability": 0.0
        }
        
        if len(trials) < 10:
            return convergence_info
        
        # Extract trial values
        values = [trial.value for trial in trials if trial.value is not None]
        
        if len(values) < 10:
            return convergence_info
        
        # Find convergence point
        window_size = min(self.early_stopping_rounds, len(values) // 4)
        for i in range(window_size, len(values)):
            window_values = values[i-window_size:i]
            improvement = max(window_values) - min(window_values)
            
            if improvement < self.min_improvement:
                convergence_info["convergence_trial"] = trials[i].number
                break
        
        # Calculate improvement rate
        if len(values) > 1:
            total_improvement = max(values) - values[0]
            convergence_info["improvement_rate"] = total_improvement / len(values)
        
        # Check if optimization was stopped early
        convergence_info["early_stopping"] = len(trials) < self.n_trials
        
        # Final stability (coefficient of variation in last 20% of trials)
        final_portion = max(10, len(values) // 5)
        final_values = values[-final_portion:]
        if len(final_values) > 1 and np.mean(final_values) != 0:
            cv = np.std(final_values) / abs(np.mean(final_values))
            convergence_info["final_stability"] = 1.0 / (1.0 + cv)  # Higher is more stable
        
        return convergence_info
    
    async def _perform_sensitivity_analysis(
        self,
        best_trial: optuna.Trial,
        all_trials: List[optuna.Trial]
    ) -> Dict[str, float]:
        """Perform parameter sensitivity analysis"""
        
        sensitivity_results = {}
        
        if not best_trial.params:
            return sensitivity_results
        
        # For each parameter, calculate correlation with objective value
        for param_name in best_trial.params.keys():
            param_values = []
            objective_values = []
            
            for trial in all_trials:
                if trial.value is not None and param_name in trial.params:
                    param_values.append(trial.params[param_name])
                    objective_values.append(trial.value)
            
            if len(param_values) > 5:  # Minimum samples for correlation
                correlation = np.corrcoef(param_values, objective_values)[0, 1]
                sensitivity_results[param_name] = abs(correlation) if not np.isnan(correlation) else 0.0
            else:
                sensitivity_results[param_name] = 0.0
        
        return sensitivity_results
    
    def _calculate_stability_score(
        self,
        best_trial: optuna.Trial,
        all_trials: List[optuna.Trial]
    ) -> float:
        """Calculate stability score based on parameter distribution around best solution"""
        
        if not best_trial.params or len(all_trials) < 10:
            return 0.5
        
        # Get top 10% of trials
        sorted_trials = sorted(
            [t for t in all_trials if t.value is not None],
            key=lambda x: x.value,
            reverse=True
        )
        
        top_trials = sorted_trials[:max(1, len(sorted_trials) // 10)]
        
        if len(top_trials) < 2:
            return 0.5
        
        # Calculate parameter stability across top trials
        stability_scores = []
        
        for param_name in best_trial.params.keys():
            param_values = [t.params[param_name] for t in top_trials if param_name in t.params]
            
            if len(param_values) > 1:
                # Coefficient of variation
                cv = np.std(param_values) / (abs(np.mean(param_values)) + 1e-8)
                stability = 1.0 / (1.0 + cv)  # Higher is more stable
                stability_scores.append(stability)
        
        return np.mean(stability_scores) if stability_scores else 0.5
    
    def _extract_pareto_front(self, trials: List[optuna.Trial]) -> List[Dict[str, Any]]:
        """Extract Pareto front for multi-objective optimization"""
        
        if not self.objective_handler.is_multi_objective:
            return []
        
        # Get completed trials with values
        completed_trials = [t for t in trials if t.values is not None]
        
        if not completed_trials:
            return []
        
        # Simple Pareto front extraction
        pareto_trials = []
        
        for trial in completed_trials:
            is_dominated = False
            
            for other_trial in completed_trials:
                if trial == other_trial:
                    continue
                
                # Check if trial is dominated by other_trial
                dominates = True
                for i, (val1, val2) in enumerate(zip(trial.values, other_trial.values)):
                    direction = self.objective_handler.get_optuna_directions()[i]
                    
                    if direction == "maximize" and val1 > val2:
                        dominates = False
                        break
                    elif direction == "minimize" and val1 < val2:
                        dominates = False
                        break
                
                if dominates:
                    # Check if other_trial strictly dominates trial
                    strict_dominance = False
                    for i, (val1, val2) in enumerate(zip(trial.values, other_trial.values)):
                        direction = self.objective_handler.get_optuna_directions()[i]
                        
                        if direction == "maximize" and val2 > val1:
                            strict_dominance = True
                        elif direction == "minimize" and val2 < val1:
                            strict_dominance = True
                    
                    if strict_dominance:
                        is_dominated = True
                        break
            
            if not is_dominated:
                pareto_trials.append(trial)
        
        # Format Pareto front
        pareto_front = []
        for trial in pareto_trials:
            solution = {
                "parameters": self._trial_to_parameters(trial).dict(),
                "objective_values": list(trial.values),
                "objectives": [obj.value for obj in self.optimization_config.objectives]
            }
            
            if hasattr(trial, 'user_attrs') and 'performance_metrics' in trial.user_attrs:
                solution["performance_metrics"] = trial.user_attrs['performance_metrics']
            
            pareto_front.append(solution)
        
        return pareto_front
    
    def _extract_fitness_history(self, trials: List[optuna.Trial]) -> List[float]:
        """Extract fitness history from trials"""
        
        if self.objective_handler.is_multi_objective:
            # Use composite score for multi-objective
            fitness_history = []
            for trial in trials:
                if trial.values is not None and hasattr(trial, 'user_attrs') and 'performance_metrics' in trial.user_attrs:
                    try:
                        performance = PerformanceMetrics(**trial.user_attrs['performance_metrics'])
                        composite_score = self.objective_handler.calculate_composite_score(performance)
                        fitness_history.append(composite_score)
                    except:
                        fitness_history.append(0.0)
                else:
                    fitness_history.append(0.0)
        else:
            # Single objective
            fitness_history = [trial.value if trial.value is not None else 0.0 for trial in trials]
        
        return fitness_history
    
    def _is_integer_parameter(self, param_name: str) -> bool:
        """Check if parameter should be treated as integer"""
        
        integer_params = [
            "sma_fast_period", "sma_slow_period", "ema_fast_period", "ema_slow_period",
            "rsi_period", "bb_period", "macd_fast", "macd_slow", "macd_signal",
            "lookback_period"
        ]
        
        return param_name in integer_params
    
    async def _validate_optimization_config(self, config: OptimizationConfig):
        """Validate optimization configuration"""
        
        if not config.objectives:
            raise ParameterOptimizerError("At least one optimization objective is required")
        
        if not config.parameters_to_optimize:
            raise ParameterOptimizerError("At least one parameter to optimize is required")
        
        if not config.parameter_bounds:
            raise ParameterOptimizerError("Parameter bounds are required")
        
        # Validate parameter bounds
        for param_name in config.parameters_to_optimize:
            if param_name not in config.parameter_bounds:
                raise ParameterOptimizerError(f"Missing bounds for parameter: {param_name}")
            
            bounds = config.parameter_bounds[param_name]
            if len(bounds) != 2 or bounds[0] >= bounds[1]:
                raise ParameterOptimizerError(f"Invalid bounds for parameter {param_name}: {bounds}")
    
    def get_optimization_statistics(self) -> Dict[str, Any]:
        """Get detailed optimization statistics"""
        
        if not self.trial_history:
            return {}
        
        values = [trial['value'] if 'value' in trial else max(trial.get('values', [0])) 
                 for trial in self.trial_history]
        
        stats = {
            "trials_completed": len(self.trial_history),
            "best_value": max(values) if values else 0.0,
            "final_value": values[-1] if values else 0.0,
            "improvement": max(values) - values[0] if len(values) > 1 else 0.0,
            "convergence_rate": (max(values) - values[0]) / len(values) if len(values) > 1 else 0.0,
            "value_std": np.std(values) if len(values) > 1 else 0.0
        }
        
        return stats
    
    def generate_optimization_plots(
        self,
        optimization_id: str,
        save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate optimization visualization plots"""
        
        if optimization_id not in self.optimization_cache:
            return {}
        
        study = self.optimization_cache[optimization_id]['study']
        plots = {}
        
        try:
            # Optimization history plot
            history_fig = optuna.visualization.plot_optimization_history(study)
            plots['optimization_history'] = history_fig
            
            # Parameter importance plot
            importance_fig = optuna.visualization.plot_param_importances(study)
            plots['parameter_importance'] = importance_fig
            
            # Parallel coordinate plot
            parallel_fig = optuna.visualization.plot_parallel_coordinate(study)
            plots['parallel_coordinate'] = parallel_fig
            
            # Slice plot
            slice_fig = optuna.visualization.plot_slice(study)
            plots['slice_plot'] = slice_fig
            
            # Multi-objective plots if applicable
            if self.objective_handler.is_multi_objective:
                pareto_fig = optuna.visualization.plot_pareto_front(study)
                plots['pareto_front'] = pareto_fig
            
            # Save plots if path provided
            if save_path:
                import os
                os.makedirs(save_path, exist_ok=True)
                
                for plot_name, fig in plots.items():
                    fig.write_html(os.path.join(save_path, f"{plot_name}.html"))
                    fig.write_image(os.path.join(save_path, f"{plot_name}.png"))
            
            return plots
            
        except Exception as e:
            logger.error(f"Plot generation failed: {e}")
            return {}