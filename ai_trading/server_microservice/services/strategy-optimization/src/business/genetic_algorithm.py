"""
Genetic Algorithm Engine - DEAP Framework Integration
Advanced genetic algorithms for strategy parameter optimization with NSGA-II multi-objective optimization
"""

import asyncio
import logging
import random
import time
import uuid
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional, Callable
import numpy as np
import pandas as pd

# DEAP Framework imports
from deap import base, creator, tools, algorithms
from deap.base import Fitness
import deap.algorithms

# Statistical analysis
from scipy import stats
import matplotlib.pyplot as plt
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp

from ..models.strategy_models import (
    StrategyDefinition,
    StrategyParameters,
    OptimizationConfig,
    OptimizationResult,
    PerformanceMetrics,
    OptimizationObjective
)

logger = logging.getLogger(__name__)


class GeneticAlgorithmError(Exception):
    """Genetic algorithm specific errors"""
    pass


class Individual:
    """Individual representation for genetic algorithm with strategy parameters"""
    
    def __init__(self, parameters: Dict[str, Any]):
        self.parameters = parameters
        self.fitness_scores: Dict[str, float] = {}
        self.performance_metrics: Optional[PerformanceMetrics] = None
        self.evaluated = False
        self.generation = 0
    
    def __repr__(self):
        return f"Individual(params={self.parameters}, fitness={self.fitness_scores})"


class GeneticAlgorithmEngine:
    """
    Advanced Genetic Algorithm Engine using DEAP framework
    Supports multi-objective optimization with NSGA-II algorithm
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize genetic algorithm engine with configuration"""
        self.config = config or {}
        
        # Algorithm configuration
        self.population_size = self.config.get('population_size', 100)
        self.generations = self.config.get('generations', 50)
        self.crossover_prob = self.config.get('crossover_prob', 0.8)
        self.mutation_prob = self.config.get('mutation_prob', 0.2)
        self.tournament_size = self.config.get('tournament_size', 3)
        
        # Multi-objective optimization
        self.use_nsga2 = self.config.get('use_nsga2', True)
        self.crowding_factor = self.config.get('crowding_factor', 2.0)
        
        # Performance optimization
        self.parallel_evaluation = self.config.get('parallel_evaluation', True)
        self.max_workers = self.config.get('max_workers', mp.cpu_count())
        
        # Convergence criteria
        self.convergence_threshold = self.config.get('convergence_threshold', 0.01)
        self.stagnation_generations = self.config.get('stagnation_generations', 10)
        
        # Statistics tracking
        self.statistics = tools.Statistics()
        self.logbook = tools.Logbook()
        self.history = []
        
        # DEAP toolbox setup
        self.toolbox = base.Toolbox()
        self._setup_deap_framework()
        
        logger.info("GeneticAlgorithmEngine initialized successfully")
    
    def _setup_deap_framework(self):
        """Setup DEAP framework components"""
        
        # Create fitness class for multi-objective optimization
        if not hasattr(creator, "FitnessMulti"):
            creator.create("FitnessMulti", base.Fitness, weights=(1.0, 1.0, -1.0))  # maximize, maximize, minimize
        
        # Create individual class
        if not hasattr(creator, "Individual"):
            creator.create("Individual", list, fitness=creator.FitnessMulti)
        
        # Register genetic operators
        self.toolbox.register("select", tools.selNSGAII if self.use_nsga2 else tools.selTournament, 
                             tournsize=self.tournament_size)
        self.toolbox.register("mate", self._crossover)
        self.toolbox.register("mutate", self._mutate)
        self.toolbox.register("evaluate", self._evaluate_individual)
        
        # Statistics configuration
        self.statistics.register("avg", np.mean, axis=0)
        self.statistics.register("std", np.std, axis=0)
        self.statistics.register("min", np.min, axis=0)
        self.statistics.register("max", np.max, axis=0)
        
        # Setup parallel execution if enabled
        if self.parallel_evaluation:
            self.toolbox.register("map", self._parallel_map)
        else:
            self.toolbox.register("map", map)
    
    async def optimize(
        self,
        strategy: StrategyDefinition,
        optimization_config: OptimizationConfig,
        backtest_engine=None
    ) -> OptimizationResult:
        """
        Run genetic algorithm optimization for strategy parameters
        
        Args:
            strategy: Strategy definition to optimize
            optimization_config: Optimization configuration
            backtest_engine: Backtesting engine for fitness evaluation
            
        Returns:
            OptimizationResult with optimized parameters and statistics
        """
        
        try:
            logger.info(f"Starting genetic algorithm optimization for strategy: {strategy.strategy_id}")
            start_time = time.time()
            
            # Setup optimization parameters
            self.strategy = strategy
            self.optimization_config = optimization_config
            self.backtest_engine = backtest_engine
            
            # Validate configuration
            await self._validate_optimization_config(optimization_config)
            
            # Initialize parameter bounds and types
            self.parameter_bounds = optimization_config.parameter_bounds
            self.parameter_types = self._infer_parameter_types(optimization_config.parameters_to_optimize)
            
            # Generate optimization ID
            optimization_id = f"ga_opt_{int(time.time())}_{strategy.strategy_id}"
            
            # Create initial population
            population = self._create_initial_population()
            
            # Setup fitness evaluation
            self._setup_fitness_evaluation(optimization_config.objectives)
            
            # Run genetic algorithm
            final_population, logbook, pareto_front = await self._run_genetic_algorithm(
                population, optimization_config
            )
            
            # Extract best individual and results
            best_individual = self._get_best_individual(final_population, optimization_config.objectives)
            best_parameters = self._individual_to_parameters(best_individual)
            
            # Calculate convergence metrics
            convergence_info = self._analyze_convergence(logbook)
            
            # Perform sensitivity analysis
            sensitivity_analysis = await self._perform_sensitivity_analysis(
                best_individual, optimization_config
            )
            
            # Calculate execution metrics
            optimization_time = time.time() - start_time
            cpu_time = optimization_time * self.max_workers  # Approximate CPU time
            
            # Create optimization result
            optimization_result = OptimizationResult(
                optimization_id=optimization_id,
                strategy_id=strategy.strategy_id,
                optimization_method="NSGA-II" if self.use_nsga2 else "Single-Objective GA",
                objectives=optimization_config.objectives,
                parameter_bounds=self.parameter_bounds,
                generations=len(logbook),
                population_size=self.population_size,
                best_parameters=best_parameters,
                best_fitness=max(best_individual.fitness.values),
                fitness_history=[record["max"] for record in logbook],
                pareto_front=self._format_pareto_front(pareto_front),
                convergence_generation=convergence_info.get("convergence_generation"),
                convergence_criterion=self.convergence_threshold,
                early_stopping=convergence_info.get("early_stopping", False),
                in_sample_performance=best_individual.performance_metrics,
                evaluations_count=len(logbook) * self.population_size,
                optimization_time=optimization_time,
                cpu_time=cpu_time,
                parameter_sensitivity=sensitivity_analysis,
                stability_score=self._calculate_stability_score(best_individual, final_population),
                created_at=datetime.now()
            )
            
            logger.info(f"Genetic algorithm optimization completed: {optimization_id}")
            logger.info(f"Best fitness: {best_individual.fitness.values}")
            logger.info(f"Optimization time: {optimization_time:.2f} seconds")
            
            return optimization_result
            
        except Exception as e:
            logger.error(f"Genetic algorithm optimization failed: {e}")
            raise GeneticAlgorithmError(f"Optimization failed: {str(e)}")
    
    def _create_initial_population(self) -> List[creator.Individual]:
        """Create initial population with diverse parameter combinations"""
        
        population = []
        
        for _ in range(self.population_size):
            individual_params = {}
            
            # Generate random parameters within bounds
            for param_name in self.optimization_config.parameters_to_optimize:
                if param_name in self.parameter_bounds:
                    bounds = self.parameter_bounds[param_name]
                    param_type = self.parameter_types.get(param_name, float)
                    
                    if param_type == int:
                        value = random.randint(int(bounds[0]), int(bounds[1]))
                    elif param_type == float:
                        value = random.uniform(bounds[0], bounds[1])
                    else:
                        value = random.uniform(bounds[0], bounds[1])
                    
                    individual_params[param_name] = value
            
            # Create DEAP individual
            individual = creator.Individual(list(individual_params.values()))
            individual.param_dict = individual_params
            
            population.append(individual)
        
        return population
    
    def _setup_fitness_evaluation(self, objectives: List[OptimizationObjective]):
        """Setup fitness evaluation based on objectives"""
        
        self.objectives = objectives
        self.objective_weights = {}
        
        # Setup objective weights and directions
        for obj in objectives:
            if obj == OptimizationObjective.MAXIMIZE_PROFIT:
                self.objective_weights[obj] = 1.0
            elif obj == OptimizationObjective.MAXIMIZE_SHARPE:
                self.objective_weights[obj] = 1.0
            elif obj == OptimizationObjective.MINIMIZE_DRAWDOWN:
                self.objective_weights[obj] = -1.0  # Minimize (negative weight)
            elif obj == OptimizationObjective.MAXIMIZE_WIN_RATE:
                self.objective_weights[obj] = 1.0
            elif obj == OptimizationObjective.MINIMIZE_VOLATILITY:
                self.objective_weights[obj] = -1.0
            elif obj == OptimizationObjective.MAXIMIZE_PROFIT_FACTOR:
                self.objective_weights[obj] = 1.0
        
        # Update fitness weights for DEAP
        weights = tuple(self.objective_weights.values())
        creator.FitnessMulti.weights = weights
    
    async def _run_genetic_algorithm(
        self,
        population: List[creator.Individual],
        optimization_config: OptimizationConfig
    ) -> Tuple[List[creator.Individual], tools.Logbook, List[creator.Individual]]:
        """Run the main genetic algorithm loop"""
        
        # Initial evaluation
        logger.info("Evaluating initial population...")
        await self._evaluate_population(population)
        
        # Initialize statistics
        self.logbook.clear()
        record = self.statistics.compile(population)
        self.logbook.record(gen=0, **record)
        
        # Track convergence
        best_fitness_history = []
        stagnation_counter = 0
        
        # Main evolutionary loop
        for generation in range(1, optimization_config.generations + 1):
            logger.info(f"Generation {generation}/{optimization_config.generations}")
            
            # Selection
            if self.use_nsga2:
                # NSGA-II selection
                offspring = algorithms.varAnd(population, self.toolbox, 
                                            cxpb=self.crossover_prob, 
                                            mutpb=self.mutation_prob)
                
                # Evaluate offspring
                await self._evaluate_population(offspring)
                
                # Select next generation
                population = self.toolbox.select(population + offspring, self.population_size)
            else:
                # Traditional genetic algorithm
                offspring = self.toolbox.select(population, len(population))
                offspring = list(map(self.toolbox.clone, offspring))
                
                # Apply crossover and mutation
                for child1, child2 in zip(offspring[::2], offspring[1::2]):
                    if random.random() < self.crossover_prob:
                        self.toolbox.mate(child1, child2)
                        del child1.fitness.values
                        del child2.fitness.values
                
                for mutant in offspring:
                    if random.random() < self.mutation_prob:
                        self.toolbox.mutate(mutant)
                        del mutant.fitness.values
                
                # Evaluate invalid individuals
                invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
                await self._evaluate_population(invalid_ind)
                
                population[:] = offspring
            
            # Record statistics
            record = self.statistics.compile(population)
            self.logbook.record(gen=generation, **record)
            
            # Check convergence
            current_best = max([ind.fitness.values[0] for ind in population])
            best_fitness_history.append(current_best)
            
            if len(best_fitness_history) > self.stagnation_generations:
                recent_improvement = (
                    max(best_fitness_history[-self.stagnation_generations:]) - 
                    best_fitness_history[-self.stagnation_generations]
                )
                
                if recent_improvement < self.convergence_threshold:
                    stagnation_counter += 1
                else:
                    stagnation_counter = 0
                
                # Early stopping
                if stagnation_counter >= self.stagnation_generations:
                    logger.info(f"Early stopping at generation {generation} due to convergence")
                    break
            
            # Progress logging
            if generation % 10 == 0:
                logger.info(f"Generation {generation}: Best fitness = {current_best:.4f}")
        
        # Extract Pareto front for multi-objective optimization
        if self.use_nsga2:
            pareto_front = tools.emo.sortNondominated(population, len(population), first_front_only=True)[0]
        else:
            pareto_front = [max(population, key=lambda x: x.fitness.values[0])]
        
        return population, self.logbook, pareto_front
    
    async def _evaluate_population(self, population: List[creator.Individual]):
        """Evaluate fitness for entire population"""
        
        # Filter individuals that need evaluation
        invalid_individuals = [ind for ind in population if not ind.fitness.valid]
        
        if not invalid_individuals:
            return
        
        logger.info(f"Evaluating {len(invalid_individuals)} individuals...")
        
        if self.parallel_evaluation and len(invalid_individuals) > 1:
            # Parallel evaluation
            fitness_values = await self._parallel_evaluate(invalid_individuals)
        else:
            # Sequential evaluation
            fitness_values = []
            for individual in invalid_individuals:
                fitness = await self._evaluate_individual_async(individual)
                fitness_values.append(fitness)
        
        # Assign fitness values
        for ind, fitness in zip(invalid_individuals, fitness_values):
            ind.fitness.values = fitness
    
    async def _evaluate_individual_async(self, individual: creator.Individual) -> Tuple[float, ...]:
        """Evaluate single individual asynchronously"""
        
        try:
            # Convert individual to parameters
            parameters = self._individual_to_parameters(individual)
            
            # Create strategy with new parameters
            test_strategy = self.strategy.copy()
            test_strategy.parameters = parameters
            
            # Run backtest if engine available
            if self.backtest_engine:
                backtest_result = await self.backtest_engine.evaluate_strategy(test_strategy)
                performance = backtest_result.performance_metrics
            else:
                # Use synthetic performance for testing
                performance = self._generate_synthetic_performance(parameters)
            
            # Calculate multi-objective fitness
            fitness_values = []
            
            for objective in self.objectives:
                if objective == OptimizationObjective.MAXIMIZE_PROFIT:
                    fitness_values.append(performance.total_return)
                elif objective == OptimizationObjective.MAXIMIZE_SHARPE:
                    fitness_values.append(performance.sharpe_ratio)
                elif objective == OptimizationObjective.MINIMIZE_DRAWDOWN:
                    fitness_values.append(abs(performance.max_drawdown))
                elif objective == OptimizationObjective.MAXIMIZE_WIN_RATE:
                    fitness_values.append(performance.win_rate)
                elif objective == OptimizationObjective.MINIMIZE_VOLATILITY:
                    fitness_values.append(performance.volatility)
                elif objective == OptimizationObjective.MAXIMIZE_PROFIT_FACTOR:
                    fitness_values.append(performance.profit_factor)
            
            # Store performance metrics in individual
            individual.performance_metrics = performance
            individual.evaluated = True
            
            return tuple(fitness_values)
            
        except Exception as e:
            logger.error(f"Individual evaluation failed: {e}")
            # Return poor fitness on evaluation failure
            return tuple([0.0 for _ in self.objectives])
    
    def _generate_synthetic_performance(self, parameters: StrategyParameters) -> PerformanceMetrics:
        """Generate synthetic performance metrics for testing without backtest engine"""
        
        # Base performance influenced by parameters
        base_return = 0.1
        base_sharpe = 1.0
        base_drawdown = -0.05
        
        # Add parameter influence (simplified)
        if hasattr(parameters, 'sma_fast_period') and hasattr(parameters, 'sma_slow_period'):
            ratio = parameters.sma_slow_period / max(parameters.sma_fast_period, 1)
            base_return *= (1 + 0.1 * np.sin(ratio))
            base_sharpe *= (1 + 0.05 * np.cos(ratio))
        
        # Add noise
        noise_factor = 0.1
        return_noise = np.random.normal(0, noise_factor)
        sharpe_noise = np.random.normal(0, noise_factor * 0.5)
        
        return PerformanceMetrics(
            total_return=base_return + return_noise,
            annual_return=base_return + return_noise,
            excess_return=(base_return + return_noise) * 0.8,
            volatility=0.15 + abs(np.random.normal(0, 0.02)),
            sharpe_ratio=base_sharpe + sharpe_noise,
            sortino_ratio=(base_sharpe + sharpe_noise) * 1.2,
            max_drawdown=base_drawdown * (1 + abs(np.random.normal(0, 0.2))),
            var_95=-0.02,
            cvar_95=-0.03,
            total_trades=random.randint(100, 500),
            winning_trades=random.randint(60, 300),
            losing_trades=random.randint(40, 200),
            win_rate=random.uniform(0.5, 0.7),
            profit_factor=random.uniform(1.2, 2.5),
            avg_trade_return=0.001,
            avg_win_return=0.002,
            avg_loss_return=-0.001,
            calmar_ratio=abs(base_return / base_drawdown),
            omega_ratio=1.3,
            tail_ratio=2.1,
            skewness=0.1,
            kurtosis=3.2,
            market_correlation=0.3,
            beta=0.8,
            alpha=0.02,
            up_market_capture=1.1,
            down_market_capture=0.9
        )
    
    async def _parallel_evaluate(self, individuals: List[creator.Individual]) -> List[Tuple[float, ...]]:
        """Evaluate individuals in parallel using thread pool"""
        
        loop = asyncio.get_event_loop()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit evaluation tasks
            tasks = []
            for individual in individuals:
                task = loop.run_in_executor(executor, self._evaluate_individual_sync, individual)
                tasks.append(task)
            
            # Wait for all evaluations to complete
            fitness_values = await asyncio.gather(*tasks)
        
        return fitness_values
    
    def _evaluate_individual_sync(self, individual: creator.Individual) -> Tuple[float, ...]:
        """Synchronous wrapper for individual evaluation (for parallel execution)"""
        
        # This would need to be adapted for actual synchronous evaluation
        # For now, use simplified synthetic evaluation
        parameters = self._individual_to_parameters(individual)
        performance = self._generate_synthetic_performance(parameters)
        
        fitness_values = []
        for objective in self.objectives:
            if objective == OptimizationObjective.MAXIMIZE_PROFIT:
                fitness_values.append(performance.total_return)
            elif objective == OptimizationObjective.MAXIMIZE_SHARPE:
                fitness_values.append(performance.sharpe_ratio)
            elif objective == OptimizationObjective.MINIMIZE_DRAWDOWN:
                fitness_values.append(abs(performance.max_drawdown))
            elif objective == OptimizationObjective.MAXIMIZE_WIN_RATE:
                fitness_values.append(performance.win_rate)
            elif objective == OptimizationObjective.MINIMIZE_VOLATILITY:
                fitness_values.append(performance.volatility)
            elif objective == OptimizationObjective.MAXIMIZE_PROFIT_FACTOR:
                fitness_values.append(performance.profit_factor)
        
        individual.performance_metrics = performance
        return tuple(fitness_values)
    
    def _parallel_map(self, func, iterable):
        """Custom parallel map implementation for DEAP"""
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            return list(executor.map(func, iterable))
    
    def _crossover(self, ind1: creator.Individual, ind2: creator.Individual) -> Tuple[creator.Individual, creator.Individual]:
        """Custom crossover operator for strategy parameters"""
        
        # Blend crossover for numerical parameters
        alpha = 0.5
        
        for i in range(len(ind1)):
            if random.random() < 0.5:  # 50% chance to crossover each parameter
                # Blend crossover
                val1, val2 = ind1[i], ind2[i]
                gamma = (1 + 2 * alpha) * random.random() - alpha
                
                ind1[i] = (1 - gamma) * val1 + gamma * val2
                ind2[i] = gamma * val1 + (1 - gamma) * val2
                
                # Ensure bounds are respected
                param_name = list(self.parameter_bounds.keys())[i]
                bounds = self.parameter_bounds[param_name]
                
                ind1[i] = max(bounds[0], min(bounds[1], ind1[i]))
                ind2[i] = max(bounds[0], min(bounds[1], ind2[i]))
        
        return ind1, ind2
    
    def _mutate(self, individual: creator.Individual) -> Tuple[creator.Individual]:
        """Custom mutation operator for strategy parameters"""
        
        # Gaussian mutation with adaptive step size
        for i in range(len(individual)):
            if random.random() < self.mutation_prob:
                param_name = list(self.parameter_bounds.keys())[i]
                bounds = self.parameter_bounds[param_name]
                
                # Adaptive mutation strength based on parameter range
                mutation_strength = (bounds[1] - bounds[0]) * 0.1
                
                # Apply Gaussian mutation
                individual[i] += random.gauss(0, mutation_strength)
                
                # Ensure bounds
                individual[i] = max(bounds[0], min(bounds[1], individual[i]))
                
                # Handle integer parameters
                param_type = self.parameter_types.get(param_name, float)
                if param_type == int:
                    individual[i] = int(round(individual[i]))
        
        return individual,
    
    def _individual_to_parameters(self, individual: creator.Individual) -> StrategyParameters:
        """Convert DEAP individual to StrategyParameters object"""
        
        param_dict = {}
        param_names = list(self.parameter_bounds.keys())
        
        for i, param_name in enumerate(param_names):
            if i < len(individual):
                param_type = self.parameter_types.get(param_name, float)
                value = individual[i]
                
                if param_type == int:
                    value = int(round(value))
                
                param_dict[param_name] = value
        
        # Create parameters object with current strategy parameters as base
        base_params = self.strategy.parameters.dict()
        base_params.update(param_dict)
        
        return StrategyParameters(**base_params)
    
    def _get_best_individual(
        self, 
        population: List[creator.Individual], 
        objectives: List[OptimizationObjective]
    ) -> creator.Individual:
        """Get best individual based on objectives"""
        
        if len(objectives) == 1:
            # Single objective - return individual with highest fitness
            return max(population, key=lambda x: x.fitness.values[0])
        else:
            # Multi-objective - return individual from Pareto front with best composite score
            pareto_front = tools.emo.sortNondominated(population, len(population), first_front_only=True)[0]
            
            # Calculate composite scores for Pareto front
            best_individual = None
            best_score = float('-inf')
            
            for individual in pareto_front:
                # Weighted sum of normalized objectives
                score = 0.0
                for i, obj in enumerate(objectives):
                    weight = self.objective_weights.get(obj, 1.0)
                    score += weight * individual.fitness.values[i]
                
                if score > best_score:
                    best_score = score
                    best_individual = individual
            
            return best_individual or pareto_front[0]
    
    def _analyze_convergence(self, logbook: tools.Logbook) -> Dict[str, Any]:
        """Analyze convergence characteristics of the optimization run"""
        
        convergence_info = {
            "convergence_generation": None,
            "early_stopping": False,
            "improvement_rate": 0.0,
            "final_diversity": 0.0
        }
        
        if len(logbook) < 2:
            return convergence_info
        
        # Analyze fitness improvement over generations
        max_fitness = [record["max"] for record in logbook]
        
        # Find convergence generation
        for i in range(len(max_fitness) - self.stagnation_generations):
            recent_improvement = max(max_fitness[i:i+self.stagnation_generations]) - max_fitness[i]
            if recent_improvement < self.convergence_threshold:
                convergence_info["convergence_generation"] = i
                break
        
        # Calculate improvement rate
        if len(max_fitness) > 1:
            total_improvement = max_fitness[-1] - max_fitness[0]
            convergence_info["improvement_rate"] = total_improvement / len(max_fitness)
        
        # Early stopping detection
        if len(logbook) < self.generations:
            convergence_info["early_stopping"] = True
        
        return convergence_info
    
    async def _perform_sensitivity_analysis(
        self,
        best_individual: creator.Individual,
        optimization_config: OptimizationConfig
    ) -> Dict[str, float]:
        """Perform parameter sensitivity analysis around best solution"""
        
        sensitivity_results = {}
        base_fitness = best_individual.fitness.values[0]
        
        # Test sensitivity for each parameter
        for i, param_name in enumerate(self.parameter_bounds.keys()):
            if i >= len(best_individual):
                continue
            
            base_value = best_individual[i]
            bounds = self.parameter_bounds[param_name]
            
            # Test parameter perturbations
            perturbations = []
            fitness_changes = []
            
            # Test multiple perturbation levels
            for perturbation_factor in [-0.1, -0.05, 0.05, 0.1]:
                # Calculate perturbed value
                param_range = bounds[1] - bounds[0]
                perturbation = param_range * perturbation_factor
                perturbed_value = base_value + perturbation
                
                # Ensure bounds
                perturbed_value = max(bounds[0], min(bounds[1], perturbed_value))
                
                # Create perturbed individual
                perturbed_individual = creator.Individual(list(best_individual))
                perturbed_individual[i] = perturbed_value
                
                # Evaluate perturbed individual
                try:
                    fitness = await self._evaluate_individual_async(perturbed_individual)
                    fitness_change = fitness[0] - base_fitness
                    
                    perturbations.append(perturbation_factor)
                    fitness_changes.append(fitness_change)
                    
                except Exception as e:
                    logger.warning(f"Sensitivity analysis failed for {param_name}: {e}")
                    continue
            
            # Calculate sensitivity metric
            if len(fitness_changes) > 1:
                # Use standard deviation of fitness changes as sensitivity measure
                sensitivity = np.std(fitness_changes)
                sensitivity_results[param_name] = sensitivity
            else:
                sensitivity_results[param_name] = 0.0
        
        return sensitivity_results
    
    def _calculate_stability_score(
        self,
        best_individual: creator.Individual,
        population: List[creator.Individual]
    ) -> float:
        """Calculate stability score based on population diversity around best solution"""
        
        if not population or len(population) < 2:
            return 0.5
        
        # Calculate distances from best individual to all others
        distances = []
        best_params = list(best_individual)
        
        for individual in population:
            if individual == best_individual:
                continue
            
            # Calculate normalized Euclidean distance
            distance = 0.0
            for i, (param_name, bounds) in enumerate(self.parameter_bounds.items()):
                if i < len(individual) and i < len(best_params):
                    param_range = bounds[1] - bounds[0]
                    normalized_diff = abs(individual[i] - best_params[i]) / param_range
                    distance += normalized_diff ** 2
            
            distances.append(np.sqrt(distance))
        
        if not distances:
            return 0.5
        
        # Stability score based on local convergence
        # Lower average distance indicates higher stability
        avg_distance = np.mean(distances)
        stability_score = max(0.0, min(1.0, 1.0 - avg_distance))
        
        return stability_score
    
    def _format_pareto_front(self, pareto_front: List[creator.Individual]) -> List[Dict[str, Any]]:
        """Format Pareto front for optimization result"""
        
        formatted_front = []
        
        for individual in pareto_front:
            solution = {
                "parameters": self._individual_to_parameters(individual).dict(),
                "fitness_values": list(individual.fitness.values),
                "objectives": [obj.value for obj in self.objectives]
            }
            
            if hasattr(individual, 'performance_metrics') and individual.performance_metrics:
                solution["performance_metrics"] = individual.performance_metrics.dict()
            
            formatted_front.append(solution)
        
        return formatted_front
    
    def _infer_parameter_types(self, parameter_names: List[str]) -> Dict[str, type]:
        """Infer parameter types from names and current strategy parameters"""
        
        parameter_types = {}
        
        # Common integer parameters
        integer_params = [
            "sma_fast_period", "sma_slow_period", "ema_fast_period", "ema_slow_period",
            "rsi_period", "bb_period", "macd_fast", "macd_slow", "macd_signal",
            "lookback_period"
        ]
        
        for param_name in parameter_names:
            if param_name in integer_params:
                parameter_types[param_name] = int
            else:
                parameter_types[param_name] = float
        
        return parameter_types
    
    async def _validate_optimization_config(self, config: OptimizationConfig):
        """Validate optimization configuration"""
        
        if not config.objectives:
            raise GeneticAlgorithmError("At least one optimization objective is required")
        
        if not config.parameters_to_optimize:
            raise GeneticAlgorithmError("At least one parameter to optimize is required")
        
        if not config.parameter_bounds:
            raise GeneticAlgorithmError("Parameter bounds are required")
        
        # Validate parameter bounds
        for param_name in config.parameters_to_optimize:
            if param_name not in config.parameter_bounds:
                raise GeneticAlgorithmError(f"Missing bounds for parameter: {param_name}")
            
            bounds = config.parameter_bounds[param_name]
            if len(bounds) != 2 or bounds[0] >= bounds[1]:
                raise GeneticAlgorithmError(f"Invalid bounds for parameter {param_name}: {bounds}")
    
    def get_optimization_statistics(self) -> Dict[str, Any]:
        """Get detailed optimization statistics"""
        
        if not self.logbook:
            return {}
        
        stats = {
            "generations_completed": len(self.logbook),
            "final_best_fitness": self.logbook[-1]["max"] if self.logbook else 0.0,
            "fitness_improvement": (
                self.logbook[-1]["max"] - self.logbook[0]["max"] 
                if len(self.logbook) > 1 else 0.0
            ),
            "convergence_rate": 0.0,
            "population_diversity": self.logbook[-1]["std"] if self.logbook else 0.0
        }
        
        if len(self.logbook) > 1:
            stats["convergence_rate"] = stats["fitness_improvement"] / len(self.logbook)
        
        return stats