"""
Strategy Management API Endpoints
Real implementations with comprehensive business logic integration
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from ..models.strategy_models import (
    StrategyDefinition, StrategyParameters, RiskParameters, 
    TradingRule, StrategyType, StrategyStatus, OptimizationObjective
)
from ..business.strategy_manager import StrategyManager
from ..business.genetic_algorithm import GeneticAlgorithmEngine
from ..business.backtest_engine import BacktestEngine
from ..business.parameter_optimizer import ParameterOptimizer
from ..business.strategy_templates import StrategyTemplateManager

logger = logging.getLogger(__name__)


class CreateStrategyRequest(BaseModel):
    """Request model for creating strategy"""
    name: str = Field(description="Strategy display name")
    description: str = Field(description="Strategy description")
    strategy_type: StrategyType = Field(description="Strategy category")
    template_id: Optional[str] = Field(None, description="Base template ID")
    
    # Strategy components
    trading_rules: List[Dict[str, Any]] = Field(description="Trading rules definition")
    parameters: Dict[str, Any] = Field(description="Strategy parameters")
    risk_parameters: Dict[str, Any] = Field(description="Risk management settings")
    
    # Market requirements
    symbols: List[str] = Field(description="Tradeable instruments")
    timeframe: str = Field(default="1D", description="Trading timeframe")
    
    # Creator info
    created_by: str = Field(default="api_user", description="Strategy creator")


class UpdateStrategyRequest(BaseModel):
    """Request model for updating strategy"""
    name: Optional[str] = None
    description: Optional[str] = None
    trading_rules: Optional[List[Dict[str, Any]]] = None
    parameters: Optional[Dict[str, Any]] = None
    risk_parameters: Optional[Dict[str, Any]] = None
    symbols: Optional[List[str]] = None


class OptimizeStrategyRequest(BaseModel):
    """Request model for strategy optimization"""
    optimization_method: str = Field(default="NSGA-II", description="Optimization algorithm")
    objectives: List[OptimizationObjective] = Field(description="Optimization objectives")
    parameters_to_optimize: List[str] = Field(description="Parameters to optimize")
    parameter_bounds: Dict[str, List[float]] = Field(description="Parameter search bounds")
    
    # Algorithm settings
    population_size: int = Field(default=100, ge=10, le=1000)
    generations: int = Field(default=50, ge=10, le=1000)
    
    # Validation settings
    validation_split: float = Field(default=0.2, ge=0.1, le=0.5)
    cross_validation_folds: int = Field(default=5, ge=2, le=10)


class BacktestStrategyRequest(BaseModel):
    """Request model for strategy backtesting"""
    start_date: datetime = Field(description="Backtest start date")
    end_date: datetime = Field(description="Backtest end date")
    initial_capital: float = Field(default=10000.0, gt=0, description="Starting capital")
    benchmark_symbol: str = Field(default="SPY", description="Benchmark for comparison")


class CompareStrategiesRequest(BaseModel):
    """Request model for strategy comparison"""
    strategy_ids: List[str] = Field(min_items=2, description="Strategies to compare")
    comparison_period: List[datetime] = Field(description="[start_date, end_date]")
    metrics: Optional[List[str]] = Field(None, description="Metrics to compare")


class StrategyEndpoints:
    """
    Comprehensive strategy management endpoints with real business logic
    """
    
    def __init__(
        self,
        strategy_manager: StrategyManager,
        template_manager: StrategyTemplateManager,
        genetic_algorithm: GeneticAlgorithmEngine,
        backtest_engine: BacktestEngine,
        parameter_optimizer: ParameterOptimizer
    ):
        self.strategy_manager = strategy_manager
        self.template_manager = template_manager
        self.genetic_algorithm = genetic_algorithm
        self.backtest_engine = backtest_engine
        self.parameter_optimizer = parameter_optimizer
    
    async def create_strategy(
        self,
        request: CreateStrategyRequest,
        background_tasks: BackgroundTasks
    ) -> Dict[str, Any]:
        """Create new trading strategy with comprehensive validation"""
        
        try:
            # Convert request to domain models
            trading_rules = [TradingRule(**rule_data) for rule_data in request.trading_rules]
            parameters = StrategyParameters(**request.parameters)
            risk_parameters = RiskParameters(**request.risk_parameters)
            
            # Create strategy
            strategy = await self.strategy_manager.create_strategy(
                name=request.name,
                description=request.description,
                strategy_type=request.strategy_type,
                trading_rules=trading_rules,
                parameters=parameters,
                risk_parameters=risk_parameters,
                symbols=request.symbols,
                timeframe=request.timeframe,
                template_id=request.template_id,
                created_by=request.created_by
            )
            
            # Background validation and initial analysis
            background_tasks.add_task(
                self._perform_initial_strategy_analysis,
                strategy.strategy_id
            )
            
            logger.info(f"Strategy created via API: {strategy.strategy_id}")
            
            return {
                "success": True,
                "strategy_id": strategy.strategy_id,
                "message": "Strategy created successfully",
                "strategy": strategy.dict()
            }
            
        except Exception as e:
            logger.error(f"Strategy creation failed: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    async def get_strategy(self, strategy_id: str) -> Dict[str, Any]:
        """Retrieve strategy with comprehensive details"""
        
        try:
            strategy = await self.strategy_manager.get_strategy(strategy_id)
            
            if not strategy:
                raise HTTPException(status_code=404, detail="Strategy not found")
            
            # Get additional context
            performance_metrics = await self.strategy_manager.get_strategy_performance(strategy_id)
            optimization_history = await self.strategy_manager.get_optimization_history(strategy_id)
            backtest_history = await self.strategy_manager.get_backtest_history(strategy_id)
            
            return {
                "success": True,
                "strategy": strategy.dict(),
                "performance_metrics": performance_metrics.dict() if performance_metrics else None,
                "optimization_count": len(optimization_history),
                "backtest_count": len(backtest_history),
                "last_updated": strategy.updated_at.isoformat() if strategy.updated_at else None
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get strategy {strategy_id}: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def update_strategy(
        self,
        strategy_id: str,
        request: UpdateStrategyRequest,
        background_tasks: BackgroundTasks
    ) -> Dict[str, Any]:
        """Update existing strategy with validation"""
        
        try:
            # Build updates dictionary
            updates = {}
            
            if request.name is not None:
                updates["name"] = request.name
            
            if request.description is not None:
                updates["description"] = request.description
            
            if request.trading_rules is not None:
                trading_rules = [TradingRule(**rule_data) for rule_data in request.trading_rules]
                updates["trading_rules"] = trading_rules
            
            if request.parameters is not None:
                updates["parameters"] = StrategyParameters(**request.parameters)
            
            if request.risk_parameters is not None:
                updates["risk_parameters"] = RiskParameters(**request.risk_parameters)
            
            if request.symbols is not None:
                updates["symbols"] = request.symbols
            
            # Update strategy
            updated_strategy = await self.strategy_manager.update_strategy(strategy_id, updates)
            
            if not updated_strategy:
                raise HTTPException(status_code=404, detail="Strategy not found")
            
            # Background re-validation if significant changes
            if any(key in updates for key in ["trading_rules", "parameters", "risk_parameters"]):
                background_tasks.add_task(
                    self._revalidate_strategy,
                    strategy_id
                )
            
            return {
                "success": True,
                "message": "Strategy updated successfully",
                "strategy": updated_strategy.dict()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to update strategy {strategy_id}: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    async def delete_strategy(self, strategy_id: str) -> Dict[str, Any]:
        """Delete strategy with safety checks"""
        
        try:
            success = await self.strategy_manager.delete_strategy(strategy_id)
            
            if not success:
                raise HTTPException(status_code=404, detail="Strategy not found or cannot be deleted")
            
            return {
                "success": True,
                "message": "Strategy deleted successfully"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete strategy {strategy_id}: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def list_strategies(
        self,
        strategy_type: Optional[StrategyType] = None,
        status: Optional[StrategyStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List strategies with filtering and pagination"""
        
        try:
            strategies = await self.strategy_manager.list_strategies(
                strategy_type=strategy_type,
                status=status,
                limit=limit,
                offset=offset
            )
            
            # Add summary information
            strategy_summaries = []
            for strategy in strategies:
                summary = {
                    "strategy_id": strategy.strategy_id,
                    "name": strategy.name,
                    "strategy_type": strategy.strategy_type.value,
                    "status": strategy.status.value,
                    "is_active": strategy.is_active,
                    "symbols": strategy.symbols,
                    "created_at": strategy.created_at.isoformat() if strategy.created_at else None,
                    "confidence_score": strategy.confidence_score,
                    "performance_summary": {
                        "total_return": strategy.performance_metrics.total_return if strategy.performance_metrics else None,
                        "sharpe_ratio": strategy.performance_metrics.sharpe_ratio if strategy.performance_metrics else None,
                        "max_drawdown": strategy.performance_metrics.max_drawdown if strategy.performance_metrics else None
                    }
                }
                strategy_summaries.append(summary)
            
            return {
                "success": True,
                "strategies": strategy_summaries,
                "total_count": len(strategies),
                "limit": limit,
                "offset": offset
            }
            
        except Exception as e:
            logger.error(f"Failed to list strategies: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def optimize_strategy(
        self,
        strategy_id: str,
        request: OptimizeStrategyRequest,
        background_tasks: BackgroundTasks
    ) -> Dict[str, Any]:
        """Run comprehensive strategy optimization"""
        
        try:
            # Get strategy
            strategy = await self.strategy_manager.get_strategy(strategy_id)
            if not strategy:
                raise HTTPException(status_code=404, detail="Strategy not found")
            
            # Create optimization configuration
            from ..models.strategy_models import OptimizationConfig
            
            optimization_config = OptimizationConfig(
                config_id=f"opt_config_{strategy_id}_{int(datetime.now().timestamp())}",
                strategy_id=strategy_id,
                algorithm=request.optimization_method,
                objectives=request.objectives,
                population_size=request.population_size,
                generations=request.generations,
                parameters_to_optimize=request.parameters_to_optimize,
                parameter_bounds=request.parameter_bounds,
                validation_split=request.validation_split,
                cross_validation_folds=request.cross_validation_folds
            )
            
            # Start optimization in background
            background_tasks.add_task(
                self._run_optimization_task,
                strategy_id,
                optimization_config
            )
            
            return {
                "success": True,
                "message": "Optimization started successfully",
                "optimization_config": optimization_config.dict(),
                "estimated_duration": f"{request.generations * request.population_size * 0.1:.0f} seconds"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to start optimization for {strategy_id}: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    async def backtest_strategy(
        self,
        strategy_id: str,
        request: BacktestStrategyRequest,
        background_tasks: BackgroundTasks
    ) -> Dict[str, Any]:
        """Run comprehensive strategy backtesting"""
        
        try:
            # Get strategy
            strategy = await self.strategy_manager.get_strategy(strategy_id)
            if not strategy:
                raise HTTPException(status_code=404, detail="Strategy not found")
            
            # Validate date range
            if request.start_date >= request.end_date:
                raise HTTPException(status_code=400, detail="Start date must be before end date")
            
            if request.end_date > datetime.now():
                raise HTTPException(status_code=400, detail="End date cannot be in the future")
            
            # Start backtesting in background
            background_tasks.add_task(
                self._run_backtest_task,
                strategy_id,
                request.start_date,
                request.end_date,
                request.initial_capital
            )
            
            return {
                "success": True,
                "message": "Backtesting started successfully",
                "backtest_parameters": {
                    "start_date": request.start_date.isoformat(),
                    "end_date": request.end_date.isoformat(),
                    "initial_capital": request.initial_capital,
                    "symbols": strategy.symbols
                },
                "estimated_duration": f"{(request.end_date - request.start_date).days * 0.1:.0f} seconds"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to start backtest for {strategy_id}: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    async def compare_strategies(
        self,
        request: CompareStrategiesRequest
    ) -> Dict[str, Any]:
        """Compare multiple strategies across various metrics"""
        
        try:
            if len(request.comparison_period) != 2:
                raise HTTPException(status_code=400, detail="Comparison period must have start and end dates")
            
            start_date, end_date = request.comparison_period
            
            # Run comparison
            comparison_result = await self.strategy_manager.compare_strategies(
                strategy_ids=request.strategy_ids,
                comparison_period=(start_date, end_date),
                metrics=request.metrics
            )
            
            return {
                "success": True,
                "comparison_result": comparison_result.dict(),
                "analysis_summary": {
                    "best_strategy": comparison_result.performance_ranking[0] if comparison_result.performance_ranking else None,
                    "strategies_compared": len(request.strategy_ids),
                    "comparison_period": f"{start_date.date()} to {end_date.date()}",
                    "diversification_benefit": comparison_result.diversification_benefit
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Strategy comparison failed: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    async def deploy_strategy(self, strategy_id: str) -> Dict[str, Any]:
        """Deploy strategy for live trading"""
        
        try:
            success = await self.strategy_manager.deploy_strategy(strategy_id)
            
            if not success:
                raise HTTPException(status_code=400, detail="Strategy deployment failed - check validation requirements")
            
            return {
                "success": True,
                "message": "Strategy deployed successfully",
                "deployment_time": datetime.now().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to deploy strategy {strategy_id}: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def pause_strategy(self, strategy_id: str) -> Dict[str, Any]:
        """Pause active strategy"""
        
        try:
            success = await self.strategy_manager.pause_strategy(strategy_id)
            
            if not success:
                raise HTTPException(status_code=404, detail="Strategy not found or not active")
            
            return {
                "success": True,
                "message": "Strategy paused successfully"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to pause strategy {strategy_id}: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def retire_strategy(self, strategy_id: str) -> Dict[str, Any]:
        """Retire strategy from active use"""
        
        try:
            success = await self.strategy_manager.retire_strategy(strategy_id)
            
            if not success:
                raise HTTPException(status_code=404, detail="Strategy not found")
            
            return {
                "success": True,
                "message": "Strategy retired successfully"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to retire strategy {strategy_id}: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    # ==================== BACKGROUND TASKS ====================
    
    async def _perform_initial_strategy_analysis(self, strategy_id: str):
        """Background task for initial strategy analysis"""
        
        try:
            logger.info(f"Starting initial analysis for strategy: {strategy_id}")
            
            # Get strategy
            strategy = await self.strategy_manager.get_strategy(strategy_id)
            if not strategy:
                return
            
            # Run quick validation backtest (last 30 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            backtest_result = await self.strategy_manager.backtest_strategy(
                strategy_id=strategy_id,
                start_date=start_date,
                end_date=end_date,
                initial_capital=10000.0,
                backtest_engine=self.backtest_engine
            )
            
            # Update strategy confidence based on initial results
            confidence_adjustment = 0.1 if backtest_result.performance_metrics.sharpe_ratio > 0.5 else -0.1
            await self.strategy_manager.update_strategy(
                strategy_id,
                {"confidence_score": min(1.0, max(0.0, strategy.confidence_score + confidence_adjustment))}
            )
            
            logger.info(f"Initial analysis completed for strategy: {strategy_id}")
            
        except Exception as e:
            logger.error(f"Initial analysis failed for strategy {strategy_id}: {e}")
    
    async def _revalidate_strategy(self, strategy_id: str):
        """Background task for strategy revalidation after updates"""
        
        try:
            logger.info(f"Revalidating strategy: {strategy_id}")
            
            strategy = await self.strategy_manager.get_strategy(strategy_id)
            if not strategy:
                return
            
            # Reset confidence score for revalidation
            await self.strategy_manager.update_strategy(
                strategy_id,
                {"confidence_score": 0.5, "status": StrategyStatus.DRAFT}
            )
            
            # Run initial analysis again
            await self._perform_initial_strategy_analysis(strategy_id)
            
        except Exception as e:
            logger.error(f"Strategy revalidation failed for {strategy_id}: {e}")
    
    async def _run_optimization_task(
        self,
        strategy_id: str,
        optimization_config
    ):
        """Background task for running strategy optimization"""
        
        try:
            logger.info(f"Starting optimization for strategy: {strategy_id}")
            
            # Run optimization
            optimization_result = await self.strategy_manager.optimize_strategy(
                strategy_id=strategy_id,
                optimization_config=optimization_config,
                genetic_algorithm_engine=self.genetic_algorithm if optimization_config.algorithm == "NSGA-II" else None,
                parameter_optimizer=self.parameter_optimizer
            )
            
            logger.info(f"Optimization completed for strategy: {strategy_id}")
            logger.info(f"Best fitness achieved: {optimization_result.best_fitness}")
            
        except Exception as e:
            logger.error(f"Optimization failed for strategy {strategy_id}: {e}")
            
            # Update strategy status to indicate failure
            await self.strategy_manager.update_strategy(
                strategy_id,
                {
                    "status": StrategyStatus.DRAFT,
                    "validation_errors": [f"Optimization failed: {str(e)}"]
                }
            )
    
    async def _run_backtest_task(
        self,
        strategy_id: str,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float
    ):
        """Background task for running strategy backtesting"""
        
        try:
            logger.info(f"Starting backtest for strategy: {strategy_id}")
            
            # Run backtest
            backtest_result = await self.strategy_manager.backtest_strategy(
                strategy_id=strategy_id,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                backtest_engine=self.backtest_engine
            )
            
            logger.info(f"Backtest completed for strategy: {strategy_id}")
            logger.info(f"Total return: {backtest_result.performance_metrics.total_return:.2%}")
            
        except Exception as e:
            logger.error(f"Backtest failed for strategy {strategy_id}: {e}")
            
            # Update strategy with error information
            await self.strategy_manager.update_strategy(
                strategy_id,
                {
                    "validation_errors": [f"Backtest failed: {str(e)}"]
                }
            )