"""
Strategy Manager - Core Strategy Management System
Comprehensive CRUD operations, optimization integration, and deployment management
"""

import asyncio
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import json
import pickle
import numpy as np
import pandas as pd

from ..models.strategy_models import (
    StrategyDefinition,
    StrategyParameters,
    StrategyTemplate,
    OptimizationConfig,
    PerformanceMetrics,
    BacktestResult,
    OptimizationResult,
    StrategyComparison,
    StrategyType,
    StrategyStatus,
    OptimizationObjective,
    RiskParameters,
    TradingRule
)

logger = logging.getLogger(__name__)


class StrategyValidationError(Exception):
    """Strategy validation specific error"""
    pass


class StrategyManager:
    """
    Comprehensive strategy management system with full CRUD operations,
    optimization integration, deployment capabilities, and AI Brain compliance
    """
    
    def __init__(self, cache_manager=None, database_manager=None, config=None):
        """Initialize strategy manager with dependencies"""
        self.cache_manager = cache_manager
        self.database_manager = database_manager
        self.config = config or {}
        
        # In-memory storage for development/testing
        self._strategies: Dict[str, StrategyDefinition] = {}
        self._templates: Dict[str, StrategyTemplate] = {}
        self._backtest_results: Dict[str, BacktestResult] = {}
        self._optimization_results: Dict[str, OptimizationResult] = {}
        self._comparisons: Dict[str, StrategyComparison] = {}
        
        # Performance tracking
        self._performance_cache: Dict[str, PerformanceMetrics] = {}
        
        # Configuration
        self.validation_enabled = self.config.get('validation_enabled', True)
        self.ai_brain_compliance = self.config.get('ai_brain_compliance', True)
        self.auto_backup = self.config.get('auto_backup', True)
        
        logger.info("StrategyManager initialized successfully")
    
    # ==================== STRATEGY CRUD OPERATIONS ====================
    
    async def create_strategy(
        self,
        name: str,
        description: str,
        strategy_type: StrategyType,
        trading_rules: List[TradingRule],
        parameters: StrategyParameters,
        risk_parameters: RiskParameters,
        symbols: List[str],
        timeframe: str = "1D",
        template_id: Optional[str] = None,
        created_by: str = "system"
    ) -> StrategyDefinition:
        """Create a new trading strategy with comprehensive validation"""
        
        try:
            # Generate unique strategy ID
            strategy_id = self._generate_strategy_id(name, strategy_type)
            
            # Validate strategy components
            if self.validation_enabled:
                await self._validate_strategy_components(
                    trading_rules, parameters, risk_parameters, symbols
                )
            
            # Create strategy definition
            strategy = StrategyDefinition(
                strategy_id=strategy_id,
                name=name,
                description=description,
                strategy_type=strategy_type,
                template_id=template_id,
                trading_rules=trading_rules,
                parameters=parameters,
                risk_parameters=risk_parameters,
                symbols=symbols,
                timeframe=timeframe,
                status=StrategyStatus.DRAFT,
                created_by=created_by,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                confidence_score=0.5,  # Initial AI Brain confidence
                validation_errors=[]
            )
            
            # AI Brain compliance check
            if self.ai_brain_compliance:
                await self._ai_brain_validation(strategy)
            
            # Store strategy
            self._strategies[strategy_id] = strategy
            
            # Cache performance if available
            if self.cache_manager:
                await self.cache_manager.set(
                    f"strategy:{strategy_id}", 
                    strategy.dict(), 
                    ttl=3600
                )
            
            # Persist to database
            if self.database_manager:
                await self.database_manager.create_strategy(strategy)
            
            logger.info(f"Strategy created successfully: {strategy_id}")
            return strategy
            
        except Exception as e:
            logger.error(f"Failed to create strategy: {e}")
            raise StrategyValidationError(f"Strategy creation failed: {str(e)}")
    
    async def get_strategy(self, strategy_id: str) -> Optional[StrategyDefinition]:
        """Retrieve strategy by ID with caching"""
        
        try:
            # Check cache first
            if self.cache_manager:
                cached_data = await self.cache_manager.get(f"strategy:{strategy_id}")
                if cached_data:
                    return StrategyDefinition(**cached_data)
            
            # Check in-memory storage
            if strategy_id in self._strategies:
                strategy = self._strategies[strategy_id]
                
                # Update cache
                if self.cache_manager:
                    await self.cache_manager.set(
                        f"strategy:{strategy_id}", 
                        strategy.dict(), 
                        ttl=3600
                    )
                
                return strategy
            
            # Check database
            if self.database_manager:
                strategy = await self.database_manager.get_strategy(strategy_id)
                if strategy:
                    self._strategies[strategy_id] = strategy
                    return strategy
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve strategy {strategy_id}: {e}")
            return None
    
    async def update_strategy(
        self,
        strategy_id: str,
        updates: Dict[str, Any]
    ) -> Optional[StrategyDefinition]:
        """Update existing strategy with validation"""
        
        try:
            strategy = await self.get_strategy(strategy_id)
            if not strategy:
                raise ValueError(f"Strategy {strategy_id} not found")
            
            # Create updated strategy
            strategy_dict = strategy.dict()
            strategy_dict.update(updates)
            strategy_dict['updated_at'] = datetime.now()
            
            # Validate updates
            if self.validation_enabled:
                await self._validate_strategy_updates(strategy, updates)
            
            updated_strategy = StrategyDefinition(**strategy_dict)
            
            # AI Brain compliance recheck if significant changes
            if self.ai_brain_compliance and self._requires_ai_brain_recheck(updates):
                await self._ai_brain_validation(updated_strategy)
            
            # Store updated strategy
            self._strategies[strategy_id] = updated_strategy
            
            # Update cache
            if self.cache_manager:
                await self.cache_manager.set(
                    f"strategy:{strategy_id}", 
                    updated_strategy.dict(), 
                    ttl=3600
                )
            
            # Persist to database
            if self.database_manager:
                await self.database_manager.update_strategy(updated_strategy)
            
            logger.info(f"Strategy updated successfully: {strategy_id}")
            return updated_strategy
            
        except Exception as e:
            logger.error(f"Failed to update strategy {strategy_id}: {e}")
            raise StrategyValidationError(f"Strategy update failed: {str(e)}")
    
    async def delete_strategy(self, strategy_id: str) -> bool:
        """Delete strategy with safety checks"""
        
        try:
            strategy = await self.get_strategy(strategy_id)
            if not strategy:
                return False
            
            # Safety check - don't delete active strategies
            if strategy.is_active or strategy.status == StrategyStatus.DEPLOYED:
                raise ValueError(f"Cannot delete active strategy {strategy_id}")
            
            # Remove from storage
            if strategy_id in self._strategies:
                del self._strategies[strategy_id]
            
            # Remove from cache
            if self.cache_manager:
                await self.cache_manager.delete(f"strategy:{strategy_id}")
            
            # Remove from database
            if self.database_manager:
                await self.database_manager.delete_strategy(strategy_id)
            
            # Clean up associated results
            await self._cleanup_strategy_results(strategy_id)
            
            logger.info(f"Strategy deleted successfully: {strategy_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete strategy {strategy_id}: {e}")
            return False
    
    async def list_strategies(
        self,
        strategy_type: Optional[StrategyType] = None,
        status: Optional[StrategyStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[StrategyDefinition]:
        """List strategies with filtering and pagination"""
        
        try:
            strategies = list(self._strategies.values())
            
            # Apply filters
            if strategy_type:
                strategies = [s for s in strategies if s.strategy_type == strategy_type]
            
            if status:
                strategies = [s for s in strategies if s.status == status]
            
            # Sort by creation date (newest first)
            strategies.sort(key=lambda x: x.created_at, reverse=True)
            
            # Apply pagination
            return strategies[offset:offset + limit]
            
        except Exception as e:
            logger.error(f"Failed to list strategies: {e}")
            return []
    
    # ==================== STRATEGY OPTIMIZATION INTEGRATION ====================
    
    async def optimize_strategy(
        self,
        strategy_id: str,
        optimization_config: OptimizationConfig,
        genetic_algorithm_engine=None,
        parameter_optimizer=None
    ) -> OptimizationResult:
        """Optimize strategy parameters using specified algorithms"""
        
        try:
            strategy = await self.get_strategy(strategy_id)
            if not strategy:
                raise ValueError(f"Strategy {strategy_id} not found")
            
            # Update strategy status
            await self.update_strategy(strategy_id, {"status": StrategyStatus.OPTIMIZING})
            
            # Choose optimization engine
            optimization_result = None
            
            if optimization_config.algorithm == "NSGA-II" and genetic_algorithm_engine:
                optimization_result = await genetic_algorithm_engine.optimize(
                    strategy, optimization_config
                )
            elif parameter_optimizer:
                optimization_result = await parameter_optimizer.optimize(
                    strategy, optimization_config
                )
            else:
                raise ValueError(f"Unsupported optimization algorithm: {optimization_config.algorithm}")
            
            # Store optimization results
            self._optimization_results[optimization_result.optimization_id] = optimization_result
            
            # Update strategy with optimized parameters
            if optimization_result.best_parameters:
                await self.update_strategy(strategy_id, {
                    "parameters": optimization_result.best_parameters,
                    "is_optimized": True,
                    "status": StrategyStatus.VALIDATED,
                    "confidence_score": min(0.9, strategy.confidence_score + 0.3)
                })
            
            # Add optimization result to strategy
            strategy.optimization_results.append(optimization_result.optimization_id)
            await self.update_strategy(strategy_id, {
                "optimization_results": strategy.optimization_results
            })
            
            logger.info(f"Strategy optimization completed: {strategy_id}")
            return optimization_result
            
        except Exception as e:
            logger.error(f"Failed to optimize strategy {strategy_id}: {e}")
            # Reset strategy status on failure
            await self.update_strategy(strategy_id, {"status": StrategyStatus.DRAFT})
            raise
    
    async def backtest_strategy(
        self,
        strategy_id: str,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 10000.0,
        backtest_engine=None
    ) -> BacktestResult:
        """Run comprehensive backtest for strategy"""
        
        try:
            strategy = await self.get_strategy(strategy_id)
            if not strategy:
                raise ValueError(f"Strategy {strategy_id} not found")
            
            # Update strategy status
            await self.update_strategy(strategy_id, {"status": StrategyStatus.BACKTESTING})
            
            if not backtest_engine:
                raise ValueError("Backtest engine is required")
            
            # Run backtest
            backtest_result = await backtest_engine.run_backtest(
                strategy, start_date, end_date, initial_capital
            )
            
            # Store backtest results
            self._backtest_results[backtest_result.backtest_id] = backtest_result
            
            # Update strategy with backtest results
            strategy.backtest_results.append(backtest_result.backtest_id)
            await self.update_strategy(strategy_id, {
                "backtest_results": strategy.backtest_results,
                "performance_metrics": backtest_result.performance_metrics,
                "status": StrategyStatus.VALIDATED,
                "confidence_score": min(0.95, strategy.confidence_score + 0.2)
            })
            
            logger.info(f"Strategy backtest completed: {strategy_id}")
            return backtest_result
            
        except Exception as e:
            logger.error(f"Failed to backtest strategy {strategy_id}: {e}")
            # Reset strategy status on failure
            await self.update_strategy(strategy_id, {"status": StrategyStatus.DRAFT})
            raise
    
    async def compare_strategies(
        self,
        strategy_ids: List[str],
        comparison_period: Tuple[datetime, datetime],
        metrics: List[str] = None
    ) -> StrategyComparison:
        """Compare multiple strategies across various metrics"""
        
        try:
            if len(strategy_ids) < 2:
                raise ValueError("At least 2 strategies required for comparison")
            
            # Validate all strategies exist
            strategies = []
            for strategy_id in strategy_ids:
                strategy = await self.get_strategy(strategy_id)
                if not strategy:
                    raise ValueError(f"Strategy {strategy_id} not found")
                strategies.append(strategy)
            
            # Default comparison metrics
            if metrics is None:
                metrics = ["total_return", "sharpe_ratio", "max_drawdown", "win_rate", "volatility"]
            
            # Generate comparison ID
            comparison_id = f"comp_{int(datetime.now().timestamp())}_{len(strategy_ids)}_strategies"
            
            # Perform statistical analysis
            performance_ranking = await self._rank_strategies(strategies, metrics)
            statistical_significance = await self._test_statistical_significance(strategies)
            correlation_matrix = await self._calculate_correlation_matrix(strategies)
            
            # Risk-adjusted rankings
            sharpe_ranking = await self._rank_by_metric(strategies, "sharpe_ratio")
            drawdown_ranking = await self._rank_by_metric(strategies, "max_drawdown", reverse=True)
            
            # Portfolio optimization
            optimal_weights = await self._calculate_optimal_weights(strategies)
            diversification_benefit = await self._calculate_diversification_benefit(strategies)
            
            # Robustness analysis
            stability_scores = await self._calculate_stability_scores(strategies)
            regime_performance = await self._analyze_regime_performance(strategies)
            
            # Create comparison result
            comparison = StrategyComparison(
                comparison_id=comparison_id,
                strategies=strategy_ids,
                comparison_period=comparison_period,
                performance_ranking=performance_ranking,
                statistical_significance=statistical_significance,
                correlation_matrix=correlation_matrix,
                sharpe_ranking=sharpe_ranking,
                drawdown_ranking=drawdown_ranking,
                optimal_weights=optimal_weights,
                diversification_benefit=diversification_benefit,
                stability_scores=stability_scores,
                regime_performance=regime_performance,
                created_at=datetime.now()
            )
            
            # Store comparison results
            self._comparisons[comparison_id] = comparison
            
            logger.info(f"Strategy comparison completed: {comparison_id}")
            return comparison
            
        except Exception as e:
            logger.error(f"Failed to compare strategies: {e}")
            raise
    
    # ==================== STRATEGY DEPLOYMENT MANAGEMENT ====================
    
    async def deploy_strategy(
        self,
        strategy_id: str,
        deployment_config: Dict[str, Any] = None
    ) -> bool:
        """Deploy strategy for live trading"""
        
        try:
            strategy = await self.get_strategy(strategy_id)
            if not strategy:
                raise ValueError(f"Strategy {strategy_id} not found")
            
            # Pre-deployment validation
            await self._validate_for_deployment(strategy)
            
            # Update strategy status
            await self.update_strategy(strategy_id, {
                "status": StrategyStatus.DEPLOYED,
                "is_active": True,
                "deployed_at": datetime.now(),
                "confidence_score": min(1.0, strategy.confidence_score + 0.05)
            })
            
            # Additional deployment logic would go here
            # (e.g., register with trading engine, set up monitoring)
            
            logger.info(f"Strategy deployed successfully: {strategy_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deploy strategy {strategy_id}: {e}")
            return False
    
    async def pause_strategy(self, strategy_id: str) -> bool:
        """Pause active strategy"""
        
        try:
            strategy = await self.get_strategy(strategy_id)
            if not strategy:
                return False
            
            await self.update_strategy(strategy_id, {
                "status": StrategyStatus.PAUSED,
                "is_active": False
            })
            
            logger.info(f"Strategy paused: {strategy_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to pause strategy {strategy_id}: {e}")
            return False
    
    async def retire_strategy(self, strategy_id: str) -> bool:
        """Retire strategy from active use"""
        
        try:
            strategy = await self.get_strategy(strategy_id)
            if not strategy:
                return False
            
            await self.update_strategy(strategy_id, {
                "status": StrategyStatus.RETIRED,
                "is_active": False
            })
            
            logger.info(f"Strategy retired: {strategy_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to retire strategy {strategy_id}: {e}")
            return False
    
    # ==================== STRATEGY ANALYTICS AND REPORTING ====================
    
    async def get_strategy_performance(
        self, 
        strategy_id: str
    ) -> Optional[PerformanceMetrics]:
        """Get comprehensive performance metrics for strategy"""
        
        try:
            strategy = await self.get_strategy(strategy_id)
            if not strategy or not strategy.performance_metrics:
                return None
            
            # Check cache first
            if strategy_id in self._performance_cache:
                return self._performance_cache[strategy_id]
            
            # Cache performance metrics
            self._performance_cache[strategy_id] = strategy.performance_metrics
            
            return strategy.performance_metrics
            
        except Exception as e:
            logger.error(f"Failed to get performance for strategy {strategy_id}: {e}")
            return None
    
    async def get_optimization_history(
        self, 
        strategy_id: str
    ) -> List[OptimizationResult]:
        """Get optimization history for strategy"""
        
        try:
            strategy = await self.get_strategy(strategy_id)
            if not strategy:
                return []
            
            optimization_results = []
            for opt_id in strategy.optimization_results:
                if opt_id in self._optimization_results:
                    optimization_results.append(self._optimization_results[opt_id])
            
            return optimization_results
            
        except Exception as e:
            logger.error(f"Failed to get optimization history for strategy {strategy_id}: {e}")
            return []
    
    async def get_backtest_history(
        self, 
        strategy_id: str
    ) -> List[BacktestResult]:
        """Get backtest history for strategy"""
        
        try:
            strategy = await self.get_strategy(strategy_id)
            if not strategy:
                return []
            
            backtest_results = []
            for bt_id in strategy.backtest_results:
                if bt_id in self._backtest_results:
                    backtest_results.append(self._backtest_results[bt_id])
            
            return backtest_results
            
        except Exception as e:
            logger.error(f"Failed to get backtest history for strategy {strategy_id}: {e}")
            return []
    
    # ==================== PRIVATE HELPER METHODS ====================
    
    def _generate_strategy_id(self, name: str, strategy_type: StrategyType) -> str:
        """Generate unique strategy ID"""
        timestamp = int(datetime.now().timestamp())
        name_part = name.lower().replace(" ", "_")[:20]
        type_part = strategy_type.value[:10]
        return f"{type_part}_{name_part}_{timestamp}"
    
    async def _validate_strategy_components(
        self,
        trading_rules: List[TradingRule],
        parameters: StrategyParameters,
        risk_parameters: RiskParameters,
        symbols: List[str]
    ):
        """Validate strategy components for consistency and correctness"""
        
        # Validate trading rules
        if not trading_rules:
            raise StrategyValidationError("Strategy must have at least one trading rule")
        
        # Check for required entry/exit rules
        has_entry = any(rule.rule_type == "entry" for rule in trading_rules)
        has_exit = any(rule.rule_type == "exit" for rule in trading_rules)
        
        if not has_entry:
            raise StrategyValidationError("Strategy must have at least one entry rule")
        
        if not has_exit:
            raise StrategyValidationError("Strategy must have at least one exit rule")
        
        # Validate risk parameters
        if risk_parameters.stop_loss_percentage >= 0:
            raise StrategyValidationError("Stop loss percentage must be negative")
        
        if risk_parameters.take_profit_percentage <= 0:
            raise StrategyValidationError("Take profit percentage must be positive")
        
        # Validate symbols
        if not symbols:
            raise StrategyValidationError("Strategy must specify at least one symbol")
    
    async def _validate_strategy_updates(
        self,
        strategy: StrategyDefinition,
        updates: Dict[str, Any]
    ):
        """Validate strategy updates for consistency"""
        
        # Validate status transitions
        if "status" in updates:
            new_status = StrategyStatus(updates["status"])
            if not self._is_valid_status_transition(strategy.status, new_status):
                raise StrategyValidationError(
                    f"Invalid status transition: {strategy.status} -> {new_status}"
                )
    
    def _is_valid_status_transition(
        self, 
        current_status: StrategyStatus, 
        new_status: StrategyStatus
    ) -> bool:
        """Check if status transition is valid"""
        
        valid_transitions = {
            StrategyStatus.DRAFT: [StrategyStatus.OPTIMIZING, StrategyStatus.BACKTESTING, StrategyStatus.RETIRED],
            StrategyStatus.OPTIMIZING: [StrategyStatus.VALIDATED, StrategyStatus.DRAFT],
            StrategyStatus.BACKTESTING: [StrategyStatus.VALIDATED, StrategyStatus.DRAFT],
            StrategyStatus.VALIDATED: [StrategyStatus.DEPLOYED, StrategyStatus.OPTIMIZING, StrategyStatus.BACKTESTING],
            StrategyStatus.DEPLOYED: [StrategyStatus.PAUSED, StrategyStatus.RETIRED],
            StrategyStatus.PAUSED: [StrategyStatus.DEPLOYED, StrategyStatus.RETIRED],
            StrategyStatus.RETIRED: []  # Terminal state
        }
        
        return new_status in valid_transitions.get(current_status, [])
    
    async def _ai_brain_validation(self, strategy: StrategyDefinition):
        """Validate strategy using AI Brain compliance framework"""
        
        validation_errors = []
        
        # Check confidence thresholds
        if strategy.confidence_score < 0.3:
            validation_errors.append("Strategy confidence below minimum threshold")
        
        # Validate risk parameters
        if strategy.risk_parameters.max_position_size > 0.2:
            validation_errors.append("Position size exceeds AI Brain risk limits")
        
        # Validate parameter ranges
        if hasattr(strategy.parameters, 'custom_parameters'):
            for param, value in strategy.parameters.custom_parameters.items():
                if isinstance(value, (int, float)) and abs(value) > 100:
                    validation_errors.append(f"Parameter {param} outside reasonable range")
        
        # Update strategy with validation results
        strategy.validation_errors = validation_errors
        
        if validation_errors:
            strategy.confidence_score *= 0.8  # Reduce confidence if issues found
    
    def _requires_ai_brain_recheck(self, updates: Dict[str, Any]) -> bool:
        """Check if updates require AI Brain validation recheck"""
        
        significant_fields = [
            "trading_rules", "parameters", "risk_parameters", "symbols"
        ]
        
        return any(field in updates for field in significant_fields)
    
    async def _cleanup_strategy_results(self, strategy_id: str):
        """Clean up associated backtest and optimization results"""
        
        # Remove optimization results
        to_remove = []
        for opt_id, result in self._optimization_results.items():
            if result.strategy_id == strategy_id:
                to_remove.append(opt_id)
        
        for opt_id in to_remove:
            del self._optimization_results[opt_id]
        
        # Remove backtest results
        to_remove = []
        for bt_id, result in self._backtest_results.items():
            if result.strategy_id == strategy_id:
                to_remove.append(bt_id)
        
        for bt_id in to_remove:
            del self._backtest_results[bt_id]
        
        # Remove from performance cache
        if strategy_id in self._performance_cache:
            del self._performance_cache[strategy_id]
    
    async def _validate_for_deployment(self, strategy: StrategyDefinition):
        """Validate strategy is ready for deployment"""
        
        if strategy.status != StrategyStatus.VALIDATED:
            raise ValueError("Strategy must be validated before deployment")
        
        if not strategy.performance_metrics:
            raise ValueError("Strategy must have performance metrics before deployment")
        
        if strategy.confidence_score < 0.7:
            raise ValueError("Strategy confidence score too low for deployment")
        
        if strategy.validation_errors:
            raise ValueError(f"Strategy has validation errors: {strategy.validation_errors}")
    
    # Strategy comparison helper methods
    
    async def _rank_strategies(
        self, 
        strategies: List[StrategyDefinition], 
        metrics: List[str]
    ) -> List[Dict[str, Any]]:
        """Rank strategies by composite performance metrics"""
        
        rankings = []
        for strategy in strategies:
            if not strategy.performance_metrics:
                continue
            
            score = 0.0
            for metric in metrics:
                if hasattr(strategy.performance_metrics, metric):
                    value = getattr(strategy.performance_metrics, metric)
                    # Normalize and weight metrics (simplified approach)
                    if metric == "max_drawdown":
                        score += abs(value) * 0.2  # Penalize drawdown
                    elif metric in ["total_return", "sharpe_ratio", "win_rate"]:
                        score += value * 0.3  # Reward positive metrics
                    else:
                        score += value * 0.1
            
            rankings.append({
                "strategy_id": strategy.strategy_id,
                "composite_score": score,
                "rank": 0  # Will be set after sorting
            })
        
        # Sort by composite score (descending)
        rankings.sort(key=lambda x: x["composite_score"], reverse=True)
        
        # Assign ranks
        for i, ranking in enumerate(rankings):
            ranking["rank"] = i + 1
        
        return rankings
    
    async def _test_statistical_significance(
        self, 
        strategies: List[StrategyDefinition]
    ) -> Dict[str, float]:
        """Test statistical significance between strategy performances"""
        
        # Simplified implementation - would use actual statistical tests in production
        significance_tests = {}
        
        for i, strategy1 in enumerate(strategies):
            for j, strategy2 in enumerate(strategies[i+1:], i+1):
                test_key = f"{strategy1.strategy_id}_vs_{strategy2.strategy_id}"
                
                # Placeholder t-test result (would implement actual statistical test)
                significance_tests[test_key] = 0.05  # p-value
        
        return significance_tests
    
    async def _calculate_correlation_matrix(
        self, 
        strategies: List[StrategyDefinition]
    ) -> List[List[float]]:
        """Calculate correlation matrix between strategies"""
        
        n = len(strategies)
        correlation_matrix = [[0.0 for _ in range(n)] for _ in range(n)]
        
        # Diagonal elements are 1.0 (perfect correlation with self)
        for i in range(n):
            correlation_matrix[i][i] = 1.0
        
        # Calculate correlations (simplified - would use actual return series)
        for i in range(n):
            for j in range(i+1, n):
                # Placeholder correlation calculation
                correlation = np.random.uniform(-0.5, 0.8)  # Random correlation for demo
                correlation_matrix[i][j] = correlation
                correlation_matrix[j][i] = correlation  # Symmetric matrix
        
        return correlation_matrix
    
    async def _rank_by_metric(
        self, 
        strategies: List[StrategyDefinition], 
        metric: str, 
        reverse: bool = False
    ) -> List[Dict[str, Any]]:
        """Rank strategies by a specific metric"""
        
        rankings = []
        for strategy in strategies:
            if strategy.performance_metrics and hasattr(strategy.performance_metrics, metric):
                value = getattr(strategy.performance_metrics, metric)
                rankings.append({
                    "strategy_id": strategy.strategy_id,
                    metric: value,
                    "rank": 0
                })
        
        # Sort by metric
        rankings.sort(key=lambda x: x[metric], reverse=not reverse)
        
        # Assign ranks
        for i, ranking in enumerate(rankings):
            ranking["rank"] = i + 1
        
        return rankings
    
    async def _calculate_optimal_weights(
        self, 
        strategies: List[StrategyDefinition]
    ) -> Dict[str, float]:
        """Calculate optimal portfolio weights using Modern Portfolio Theory"""
        
        # Simplified equal weight allocation for demo
        n_strategies = len(strategies)
        equal_weight = 1.0 / n_strategies
        
        weights = {}
        for strategy in strategies:
            weights[strategy.strategy_id] = equal_weight
        
        return weights
    
    async def _calculate_diversification_benefit(
        self, 
        strategies: List[StrategyDefinition]
    ) -> float:
        """Calculate diversification benefit of strategy portfolio"""
        
        # Simplified calculation - would use actual covariance matrix in production
        if len(strategies) <= 1:
            return 0.0
        
        # Placeholder diversification benefit
        return 0.15  # 15% reduction in risk through diversification
    
    async def _calculate_stability_scores(
        self, 
        strategies: List[StrategyDefinition]
    ) -> Dict[str, float]:
        """Calculate stability scores for strategies"""
        
        stability_scores = {}
        for strategy in strategies:
            # Base stability on various factors
            score = 0.5  # Base score
            
            if strategy.performance_metrics:
                # Reward low volatility
                if strategy.performance_metrics.volatility < 0.2:
                    score += 0.2
                
                # Reward consistent performance
                if strategy.performance_metrics.sharpe_ratio > 1.0:
                    score += 0.2
                
                # Penalize high drawdown
                if abs(strategy.performance_metrics.max_drawdown) > 0.2:
                    score -= 0.2
            
            stability_scores[strategy.strategy_id] = max(0.0, min(1.0, score))
        
        return stability_scores
    
    async def _analyze_regime_performance(
        self, 
        strategies: List[StrategyDefinition]
    ) -> Dict[str, Dict[str, float]]:
        """Analyze strategy performance in different market regimes"""
        
        regime_performance = {}
        regimes = ["bull_market", "bear_market", "sideways_market", "high_volatility"]
        
        for strategy in strategies:
            if not strategy.performance_metrics:
                continue
            
            performance = {}
            base_return = strategy.performance_metrics.total_return
            
            # Simulate regime-specific performance (would use actual data in production)
            performance["bull_market"] = base_return * 1.2  # Better in bull markets
            performance["bear_market"] = base_return * 0.8  # Worse in bear markets
            performance["sideways_market"] = base_return * 0.9  # Slightly worse in sideways
            performance["high_volatility"] = base_return * 0.7  # Worse in high volatility
            
            regime_performance[strategy.strategy_id] = performance
        
        return regime_performance