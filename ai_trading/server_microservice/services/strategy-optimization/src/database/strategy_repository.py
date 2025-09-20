"""
Strategy Repository - Database operations for strategy management
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.exc import IntegrityError

from ..models.strategy_models import StrategyDefinition, StrategyStatus, StrategyType
from .database_manager import StrategyTable

logger = logging.getLogger(__name__)


class StrategyRepository:
    """Repository for strategy database operations"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    async def create_strategy(self, strategy: StrategyDefinition) -> bool:
        """Create new strategy in database"""
        
        try:
            async with self.db_manager.get_session() as session:
                db_strategy = StrategyTable(
                    strategy_id=strategy.strategy_id,
                    name=strategy.name,
                    description=strategy.description,
                    strategy_type=strategy.strategy_type.value,
                    template_id=strategy.template_id,
                    version=strategy.version,
                    trading_rules=[rule.dict() for rule in strategy.trading_rules],
                    parameters=strategy.parameters.dict(),
                    risk_parameters=strategy.risk_parameters.dict(),
                    symbols=strategy.symbols,
                    timeframe=strategy.timeframe,
                    data_requirements=strategy.data_requirements,
                    optimization_config=strategy.optimization_config.dict() if strategy.optimization_config else None,
                    is_optimized=strategy.is_optimized,
                    performance_metrics=strategy.performance_metrics.dict() if strategy.performance_metrics else None,
                    backtest_results=strategy.backtest_results,
                    optimization_results=strategy.optimization_results,
                    status=strategy.status.value,
                    is_active=strategy.is_active,
                    created_by=strategy.created_by,
                    created_at=strategy.created_at,
                    updated_at=strategy.updated_at,
                    deployed_at=strategy.deployed_at,
                    confidence_score=strategy.confidence_score,
                    validation_errors=strategy.validation_errors
                )
                
                session.add(db_strategy)
                await session.commit()
                
            # Cache strategy
            await self.db_manager.cache_set(f"strategy:{strategy.strategy_id}", strategy.dict(), ttl=3600)
            
            logger.info(f"Strategy created in database: {strategy.strategy_id}")
            return True
            
        except IntegrityError:
            logger.error(f"Strategy already exists: {strategy.strategy_id}")
            return False
        except Exception as e:
            logger.error(f"Failed to create strategy {strategy.strategy_id}: {e}")
            return False
    
    async def get_strategy(self, strategy_id: str) -> Optional[StrategyDefinition]:
        """Get strategy by ID"""
        
        # Check cache first
        cached_data = await self.db_manager.cache_get(f"strategy:{strategy_id}")
        if cached_data:
            return StrategyDefinition(**cached_data)
        
        try:
            async with self.db_manager.get_session() as session:
                result = await session.execute(
                    select(StrategyTable).where(StrategyTable.strategy_id == strategy_id)
                )
                db_strategy = result.scalar_one_or_none()
                
                if not db_strategy:
                    return None
                
                strategy = self._db_to_model(db_strategy)
                
                # Cache result
                await self.db_manager.cache_set(f"strategy:{strategy_id}", strategy.dict(), ttl=3600)
                
                return strategy
                
        except Exception as e:
            logger.error(f"Failed to get strategy {strategy_id}: {e}")
            return None
    
    def _db_to_model(self, db_strategy: StrategyTable) -> StrategyDefinition:
        """Convert database row to strategy model"""
        
        from ..models.strategy_models import (
            StrategyParameters, RiskParameters, TradingRule, 
            PerformanceMetrics, OptimizationConfig
        )
        
        # Convert JSON fields back to models
        trading_rules = [TradingRule(**rule) for rule in db_strategy.trading_rules]
        parameters = StrategyParameters(**db_strategy.parameters)
        risk_parameters = RiskParameters(**db_strategy.risk_parameters)
        
        performance_metrics = None
        if db_strategy.performance_metrics:
            performance_metrics = PerformanceMetrics(**db_strategy.performance_metrics)
        
        optimization_config = None
        if db_strategy.optimization_config:
            optimization_config = OptimizationConfig(**db_strategy.optimization_config)
        
        return StrategyDefinition(
            strategy_id=db_strategy.strategy_id,
            name=db_strategy.name,
            description=db_strategy.description,
            strategy_type=StrategyType(db_strategy.strategy_type),
            template_id=db_strategy.template_id,
            version=db_strategy.version,
            trading_rules=trading_rules,
            parameters=parameters,
            risk_parameters=risk_parameters,
            symbols=db_strategy.symbols,
            timeframe=db_strategy.timeframe,
            data_requirements=db_strategy.data_requirements or [],
            optimization_config=optimization_config,
            is_optimized=db_strategy.is_optimized,
            performance_metrics=performance_metrics,
            backtest_results=db_strategy.backtest_results or [],
            optimization_results=db_strategy.optimization_results or [],
            status=StrategyStatus(db_strategy.status),
            is_active=db_strategy.is_active,
            created_by=db_strategy.created_by,
            created_at=db_strategy.created_at,
            updated_at=db_strategy.updated_at,
            deployed_at=db_strategy.deployed_at,
            confidence_score=db_strategy.confidence_score,
            validation_errors=db_strategy.validation_errors or []
        )
    
    async def update_strategy(self, strategy: StrategyDefinition) -> bool:
        """Update existing strategy"""
        
        try:
            async with self.db_manager.get_session() as session:
                await session.execute(
                    update(StrategyTable)
                    .where(StrategyTable.strategy_id == strategy.strategy_id)
                    .values(
                        name=strategy.name,
                        description=strategy.description,
                        trading_rules=[rule.dict() for rule in strategy.trading_rules],
                        parameters=strategy.parameters.dict(),
                        risk_parameters=strategy.risk_parameters.dict(),
                        symbols=strategy.symbols,
                        optimization_config=strategy.optimization_config.dict() if strategy.optimization_config else None,
                        is_optimized=strategy.is_optimized,
                        performance_metrics=strategy.performance_metrics.dict() if strategy.performance_metrics else None,
                        backtest_results=strategy.backtest_results,
                        optimization_results=strategy.optimization_results,
                        status=strategy.status.value,
                        is_active=strategy.is_active,
                        updated_at=datetime.now(),
                        deployed_at=strategy.deployed_at,
                        confidence_score=strategy.confidence_score,
                        validation_errors=strategy.validation_errors
                    )
                )
                
                await session.commit()
            
            # Update cache
            await self.db_manager.cache_set(f"strategy:{strategy.strategy_id}", strategy.dict(), ttl=3600)
            
            logger.info(f"Strategy updated: {strategy.strategy_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update strategy {strategy.strategy_id}: {e}")
            return False
    
    async def delete_strategy(self, strategy_id: str) -> bool:
        """Delete strategy from database"""
        
        try:
            async with self.db_manager.get_session() as session:
                result = await session.execute(
                    delete(StrategyTable).where(StrategyTable.strategy_id == strategy_id)
                )
                
                if result.rowcount == 0:
                    return False
                
                await session.commit()
            
            # Remove from cache
            await self.db_manager.cache_delete(f"strategy:{strategy_id}")
            
            logger.info(f"Strategy deleted: {strategy_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete strategy {strategy_id}: {e}")
            return False
    
    async def list_strategies(
        self,
        strategy_type: Optional[StrategyType] = None,
        status: Optional[StrategyStatus] = None,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[StrategyDefinition]:
        """List strategies with filtering"""
        
        try:
            async with self.db_manager.get_session() as session:
                query = select(StrategyTable)
                
                # Apply filters
                conditions = []
                if strategy_type:
                    conditions.append(StrategyTable.strategy_type == strategy_type.value)
                if status:
                    conditions.append(StrategyTable.status == status.value)
                if is_active is not None:
                    conditions.append(StrategyTable.is_active == is_active)
                
                if conditions:
                    query = query.where(and_(*conditions))
                
                # Order by creation date (newest first)
                query = query.order_by(StrategyTable.created_at.desc())
                
                # Apply pagination
                query = query.offset(offset).limit(limit)
                
                result = await session.execute(query)
                db_strategies = result.scalars().all()
                
                # Convert to models
                strategies = [self._db_to_model(db_strategy) for db_strategy in db_strategies]
                
                return strategies
                
        except Exception as e:
            logger.error(f"Failed to list strategies: {e}")
            return []
    
    async def search_strategies(self, search_term: str, limit: int = 50) -> List[StrategyDefinition]:
        """Search strategies by name or description"""
        
        try:
            async with self.db_manager.get_session() as session:
                query = select(StrategyTable).where(
                    or_(
                        StrategyTable.name.ilike(f"%{search_term}%"),
                        StrategyTable.description.ilike(f"%{search_term}%")
                    )
                ).order_by(StrategyTable.created_at.desc()).limit(limit)
                
                result = await session.execute(query)
                db_strategies = result.scalars().all()
                
                strategies = [self._db_to_model(db_strategy) for db_strategy in db_strategies]
                
                return strategies
                
        except Exception as e:
            logger.error(f"Failed to search strategies: {e}")
            return []