"""
Performance Repository - Data Access Layer for Performance Analytics
High-performance data access with time-series optimization and caching

Features:
- Efficient queries for performance data with indexing strategies
- Time-series data management with automatic partitioning
- Caching layer for frequently accessed metrics
- Batch operations for high-volume data insertion
- Real-time analytics with streaming data support
"""

import asyncio
import asyncpg
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
import logging
import pandas as pd
import numpy as np
from decimal import Decimal
from contextlib import asynccontextmanager

from .database_manager import DatabaseManager
from ..models.performance_models import (
    TradeOutcomeModel, PerformanceMetricsModel, AnalyticsResultModel, 
    ReportDataModel, TimeSeriesModel, PerformanceAggregateModel
)

@dataclass
class QueryPerformanceMetrics:
    """Query performance tracking"""
    query_type: str
    execution_time: float
    rows_returned: int
    rows_affected: int
    cache_hit: bool
    timestamp: datetime

class PerformanceRepository:
    """
    High-Performance Data Repository for Trading Analytics
    
    Provides efficient data access patterns for performance analytics with
    time-series optimization, caching, and real-time capabilities.
    """
    
    def __init__(self, db_manager: DatabaseManager, service_name: str = "performance-analytics"):
        self.db_manager = db_manager
        self.service_name = service_name
        self.logger = logging.getLogger(f"{service_name}.performance_repository")
        
        # Query performance tracking
        self.query_metrics: List[QueryPerformanceMetrics] = []
        
        # Cache settings
        self.cache_ttl = {
            "trade_data": 300,      # 5 minutes
            "metrics": 600,         # 10 minutes
            "aggregates": 1800,     # 30 minutes
            "reports": 3600         # 1 hour
        }
        
        # Batch operation settings
        self.batch_sizes = {
            "trades": 1000,
            "metrics": 500,
            "time_series": 2000
        }
        
        self.logger.info(f"Performance Repository initialized for {service_name}")
    
    # Trade Data Operations
    
    async def insert_trade_outcome(self, trade: TradeOutcomeModel) -> str:
        """
        Insert single trade outcome with optimized performance
        
        Args:
            trade: Trade outcome data model
            
        Returns:
            Inserted trade ID
        """
        start_time = datetime.now()
        
        try:
            async with self.db_manager.get_postgres_session() as session:
                # Convert Decimal fields to float for database storage
                trade_data = trade.dict()
                self._convert_decimals_to_float(trade_data)
                
                # SQL insert with conflict handling
                query = """
                    INSERT INTO trade_outcomes (
                        trade_id, symbol, direction, status, entry_time, exit_time,
                        entry_price, exit_price, quantity, pnl, pnl_percentage,
                        fees, net_pnl, model_predictions, confidence_scores,
                        prediction_accuracy, stop_loss, take_profit, risk_amount,
                        risk_percentage, market_conditions, volatility_at_entry,
                        liquidity_score, holding_period_hours, max_favorable_excursion,
                        max_adverse_excursion, efficiency_ratio, created_at,
                        updated_at, tags, notes, confidence_level, ai_brain_score
                    ) VALUES (
                        :trade_id, :symbol, :direction, :status, :entry_time, :exit_time,
                        :entry_price, :exit_price, :quantity, :pnl, :pnl_percentage,
                        :fees, :net_pnl, :model_predictions, :confidence_scores,
                        :prediction_accuracy, :stop_loss, :take_profit, :risk_amount,
                        :risk_percentage, :market_conditions, :volatility_at_entry,
                        :liquidity_score, :holding_period_hours, :max_favorable_excursion,
                        :max_adverse_excursion, :efficiency_ratio, :created_at,
                        :updated_at, :tags, :notes, :confidence_level, :ai_brain_score
                    )
                    ON CONFLICT (trade_id) DO UPDATE SET
                        status = EXCLUDED.status,
                        exit_time = EXCLUDED.exit_time,
                        exit_price = EXCLUDED.exit_price,
                        pnl = EXCLUDED.pnl,
                        pnl_percentage = EXCLUDED.pnl_percentage,
                        net_pnl = EXCLUDED.net_pnl,
                        updated_at = EXCLUDED.updated_at
                    RETURNING trade_id
                """
                
                # Execute query
                result = await session.execute(query, trade_data)
                await session.commit()
                
                trade_id = result.scalar()
                
                # Track query performance
                self._track_query_performance("insert_trade", start_time, 1, 1, False)
                
                # Invalidate relevant caches
                await self._invalidate_cache(f"trade_{trade.symbol}", f"trades_recent")
                
                self.logger.debug(f"Inserted trade outcome: {trade_id}")
                return trade_id
                
        except Exception as e:
            self.logger.error(f"Failed to insert trade outcome: {e}")
            raise
    
    async def batch_insert_trades(self, trades: List[TradeOutcomeModel]) -> List[str]:
        """
        Batch insert trade outcomes with optimized performance
        
        Args:
            trades: List of trade outcome models
            
        Returns:
            List of inserted trade IDs
        """
        if not trades:
            return []
        
        start_time = datetime.now()
        inserted_ids = []
        
        try:
            # Process in batches
            batch_size = self.batch_sizes["trades"]
            
            for i in range(0, len(trades), batch_size):
                batch = trades[i:i + batch_size]
                
                async with self.db_manager.get_postgres_session() as session:
                    # Prepare batch data
                    batch_data = []
                    for trade in batch:
                        trade_data = trade.dict()
                        self._convert_decimals_to_float(trade_data)
                        batch_data.append(trade_data)
                    
                    # Batch insert query
                    query = """
                        INSERT INTO trade_outcomes (
                            trade_id, symbol, direction, status, entry_time, exit_time,
                            entry_price, exit_price, quantity, pnl, pnl_percentage,
                            fees, net_pnl, model_predictions, confidence_scores,
                            prediction_accuracy, stop_loss, take_profit, risk_amount,
                            risk_percentage, market_conditions, volatility_at_entry,
                            liquidity_score, holding_period_hours, max_favorable_excursion,
                            max_adverse_excursion, efficiency_ratio, created_at,
                            updated_at, tags, notes, confidence_level, ai_brain_score
                        ) VALUES (
                            %(trade_id)s, %(symbol)s, %(direction)s, %(status)s, 
                            %(entry_time)s, %(exit_time)s, %(entry_price)s, %(exit_price)s,
                            %(quantity)s, %(pnl)s, %(pnl_percentage)s, %(fees)s,
                            %(net_pnl)s, %(model_predictions)s, %(confidence_scores)s,
                            %(prediction_accuracy)s, %(stop_loss)s, %(take_profit)s,
                            %(risk_amount)s, %(risk_percentage)s, %(market_conditions)s,
                            %(volatility_at_entry)s, %(liquidity_score)s, %(holding_period_hours)s,
                            %(max_favorable_excursion)s, %(max_adverse_excursion)s,
                            %(efficiency_ratio)s, %(created_at)s, %(updated_at)s,
                            %(tags)s, %(notes)s, %(confidence_level)s, %(ai_brain_score)s
                        )
                        ON CONFLICT (trade_id) DO NOTHING
                        RETURNING trade_id
                    """
                    
                    # Execute batch insert
                    result = await session.execute_many(query, batch_data)
                    await session.commit()
                    
                    # Collect inserted IDs
                    batch_ids = [row[0] for row in result.fetchall()]
                    inserted_ids.extend(batch_ids)
            
            # Track query performance
            self._track_query_performance("batch_insert_trades", start_time, len(inserted_ids), len(trades), False)
            
            self.logger.info(f"Batch inserted {len(inserted_ids)} trade outcomes")
            return inserted_ids
            
        except Exception as e:
            self.logger.error(f"Failed to batch insert trades: {e}")
            raise
    
    async def get_trades_by_timeframe(self, 
                                    start_time: datetime,
                                    end_time: datetime,
                                    symbol: Optional[str] = None,
                                    status: Optional[str] = None,
                                    limit: Optional[int] = None) -> List[TradeOutcomeModel]:
        """
        Get trades within timeframe with optimized filtering
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            symbol: Optional symbol filter
            status: Optional status filter
            limit: Optional result limit
            
        Returns:
            List of trade outcome models
        """
        start_query_time = datetime.now()
        cache_key = f"trades_{start_time}_{end_time}_{symbol}_{status}_{limit}"
        
        try:
            # Check cache first
            cached_result = await self._get_from_cache(cache_key)
            if cached_result:
                self._track_query_performance("get_trades_timeframe", start_query_time, len(cached_result), 0, True)
                return [TradeOutcomeModel(**trade) for trade in cached_result]
            
            # Build query with dynamic filters
            where_clauses = ["entry_time >= :start_time", "entry_time <= :end_time"]
            params = {"start_time": start_time, "end_time": end_time}
            
            if symbol:
                where_clauses.append("symbol = :symbol")
                params["symbol"] = symbol
            
            if status:
                where_clauses.append("status = :status")
                params["status"] = status
            
            where_clause = " AND ".join(where_clauses)
            limit_clause = f"LIMIT {limit}" if limit else ""
            
            query = f"""
                SELECT * FROM trade_outcomes 
                WHERE {where_clause}
                ORDER BY entry_time DESC 
                {limit_clause}
            """
            
            async with self.db_manager.get_postgres_session() as session:
                result = await session.execute(query, params)
                rows = result.fetchall()
                
                # Convert to models
                trades = []
                for row in rows:
                    trade_data = dict(row._mapping)
                    self._convert_floats_to_decimal(trade_data)
                    trades.append(TradeOutcomeModel(**trade_data))
                
                # Cache results
                cache_data = [trade.dict() for trade in trades]
                await self._set_cache(cache_key, cache_data, self.cache_ttl["trade_data"])
                
                # Track query performance
                self._track_query_performance("get_trades_timeframe", start_query_time, len(trades), 0, False)
                
                return trades
                
        except Exception as e:
            self.logger.error(f"Failed to get trades by timeframe: {e}")
            raise
    
    async def get_trade_by_id(self, trade_id: str) -> Optional[TradeOutcomeModel]:
        """
        Get specific trade by ID with caching
        
        Args:
            trade_id: Trade identifier
            
        Returns:
            Trade outcome model or None if not found
        """
        start_time = datetime.now()
        cache_key = f"trade_{trade_id}"
        
        try:
            # Check cache first
            cached_result = await self._get_from_cache(cache_key)
            if cached_result:
                self._track_query_performance("get_trade_by_id", start_time, 1, 0, True)
                return TradeOutcomeModel(**cached_result)
            
            query = "SELECT * FROM trade_outcomes WHERE trade_id = :trade_id"
            
            async with self.db_manager.get_postgres_session() as session:
                result = await session.execute(query, {"trade_id": trade_id})
                row = result.fetchone()
                
                if row:
                    trade_data = dict(row._mapping)
                    self._convert_floats_to_decimal(trade_data)
                    trade = TradeOutcomeModel(**trade_data)
                    
                    # Cache result
                    await self._set_cache(cache_key, trade.dict(), self.cache_ttl["trade_data"])
                    
                    self._track_query_performance("get_trade_by_id", start_time, 1, 0, False)
                    return trade
                
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get trade by ID {trade_id}: {e}")
            raise
    
    # Performance Metrics Operations
    
    async def insert_performance_metric(self, metric: PerformanceMetricsModel) -> str:
        """
        Insert performance metric with time-series optimization
        
        Args:
            metric: Performance metrics model
            
        Returns:
            Inserted metric ID
        """
        start_time = datetime.now()
        
        try:
            async with self.db_manager.get_postgres_session() as session:
                metric_data = metric.dict()
                
                query = """
                    INSERT INTO performance_metrics (
                        metric_id, metric_type, metric_name, timestamp, period_start,
                        period_end, timeframe, value, previous_value, change,
                        change_percentage, mean, median, std_deviation, variance,
                        skewness, kurtosis, confidence_level, lower_bound, upper_bound,
                        margin_of_error, sample_size, data_quality_score,
                        calculation_method, market_regime, benchmark_value,
                        percentile_rank, ai_brain_confidence, validation_status,
                        attributes, tags
                    ) VALUES (
                        :metric_id, :metric_type, :metric_name, :timestamp, :period_start,
                        :period_end, :timeframe, :value, :previous_value, :change,
                        :change_percentage, :mean, :median, :std_deviation, :variance,
                        :skewness, :kurtosis, :confidence_level, :lower_bound, :upper_bound,
                        :margin_of_error, :sample_size, :data_quality_score,
                        :calculation_method, :market_regime, :benchmark_value,
                        :percentile_rank, :ai_brain_confidence, :validation_status,
                        :attributes, :tags
                    )
                    ON CONFLICT (metric_id, timestamp) DO UPDATE SET
                        value = EXCLUDED.value,
                        previous_value = EXCLUDED.previous_value,
                        change = EXCLUDED.change,
                        change_percentage = EXCLUDED.change_percentage
                    RETURNING metric_id
                """
                
                result = await session.execute(query, metric_data)
                await session.commit()
                
                metric_id = result.scalar()
                
                # Track query performance
                self._track_query_performance("insert_metric", start_time, 1, 1, False)
                
                # Invalidate cache
                await self._invalidate_cache(f"metrics_{metric.metric_type}", "metrics_recent")
                
                return metric_id
                
        except Exception as e:
            self.logger.error(f"Failed to insert performance metric: {e}")
            raise
    
    async def get_metrics_time_series(self,
                                    metric_type: str,
                                    start_time: datetime,
                                    end_time: datetime,
                                    timeframe: Optional[str] = None) -> List[PerformanceMetricsModel]:
        """
        Get time-series of performance metrics with efficient querying
        
        Args:
            metric_type: Type of metric to retrieve
            start_time: Start time for series
            end_time: End time for series
            timeframe: Optional timeframe filter
            
        Returns:
            List of performance metrics in time order
        """
        start_query_time = datetime.now()
        cache_key = f"metrics_series_{metric_type}_{start_time}_{end_time}_{timeframe}"
        
        try:
            # Check cache
            cached_result = await self._get_from_cache(cache_key)
            if cached_result:
                self._track_query_performance("get_metrics_series", start_query_time, len(cached_result), 0, True)
                return [PerformanceMetricsModel(**metric) for metric in cached_result]
            
            # Build query
            where_clauses = [
                "metric_type = :metric_type",
                "timestamp >= :start_time", 
                "timestamp <= :end_time"
            ]
            params = {
                "metric_type": metric_type,
                "start_time": start_time,
                "end_time": end_time
            }
            
            if timeframe:
                where_clauses.append("timeframe = :timeframe")
                params["timeframe"] = timeframe
            
            where_clause = " AND ".join(where_clauses)
            
            query = f"""
                SELECT * FROM performance_metrics 
                WHERE {where_clause}
                ORDER BY timestamp ASC
            """
            
            async with self.db_manager.get_postgres_session() as session:
                result = await session.execute(query, params)
                rows = result.fetchall()
                
                # Convert to models
                metrics = []
                for row in rows:
                    metric_data = dict(row._mapping)
                    metrics.append(PerformanceMetricsModel(**metric_data))
                
                # Cache results
                cache_data = [metric.dict() for metric in metrics]
                await self._set_cache(cache_key, cache_data, self.cache_ttl["metrics"])
                
                # Track performance
                self._track_query_performance("get_metrics_series", start_query_time, len(metrics), 0, False)
                
                return metrics
                
        except Exception as e:
            self.logger.error(f"Failed to get metrics time series: {e}")
            raise
    
    # Analytics Results Operations
    
    async def store_analytics_result(self, result: AnalyticsResultModel) -> str:
        """
        Store analytics result with efficient serialization
        
        Args:
            result: Analytics result model
            
        Returns:
            Stored result ID
        """
        start_time = datetime.now()
        
        try:
            async with self.db_manager.get_postgres_session() as session:
                result_data = result.dict()
                
                # Serialize complex data structures
                result_data["data_period"] = json.dumps(result_data.get("data_period", {}), default=str)
                result_data["secondary_results"] = json.dumps(result_data.get("secondary_results", {}))
                result_data["statistical_significance"] = json.dumps(result_data.get("statistical_significance", {}))
                result_data["p_values"] = json.dumps(result_data.get("p_values", {}))
                result_data["confidence_intervals"] = json.dumps(result_data.get("confidence_intervals", {}))
                result_data["input_data_summary"] = json.dumps(result_data.get("input_data_summary", {}))
                result_data["model_parameters"] = json.dumps(result_data.get("model_parameters", {}))
                result_data["accuracy_metrics"] = json.dumps(result_data.get("accuracy_metrics", {}))
                result_data["error_metrics"] = json.dumps(result_data.get("error_metrics", {}))
                result_data["validation_results"] = json.dumps(result_data.get("validation_results", {}))
                result_data["ai_brain_assessment"] = json.dumps(result_data.get("ai_brain_assessment", {}))
                result_data["chart_data"] = json.dumps(result_data.get("chart_data", {}))
                result_data["plot_config"] = json.dumps(result_data.get("plot_config", {}))
                
                query = """
                    INSERT INTO analytics_results (
                        result_id, analysis_type, result_name, timestamp,
                        calculation_time_ms, data_period, primary_result,
                        secondary_results, statistical_significance, p_values,
                        confidence_intervals, result_quality_score, reliability_score,
                        robustness_score, input_data_summary, data_completeness,
                        outliers_detected, model_used, model_version, model_parameters,
                        accuracy_metrics, error_metrics, validation_results,
                        ai_brain_assessment, confidence_framework_score, chart_data,
                        plot_config, insights, recommendations, warnings, tags,
                        export_formats
                    ) VALUES (
                        :result_id, :analysis_type, :result_name, :timestamp,
                        :calculation_time_ms, :data_period, :primary_result,
                        :secondary_results, :statistical_significance, :p_values,
                        :confidence_intervals, :result_quality_score, :reliability_score,
                        :robustness_score, :input_data_summary, :data_completeness,
                        :outliers_detected, :model_used, :model_version, :model_parameters,
                        :accuracy_metrics, :error_metrics, :validation_results,
                        :ai_brain_assessment, :confidence_framework_score, :chart_data,
                        :plot_config, :insights, :recommendations, :warnings, :tags,
                        :export_formats
                    )
                    RETURNING result_id
                """
                
                result_obj = await session.execute(query, result_data)
                await session.commit()
                
                result_id = result_obj.scalar()
                
                # Track performance
                self._track_query_performance("store_analytics_result", start_time, 1, 1, False)
                
                return result_id
                
        except Exception as e:
            self.logger.error(f"Failed to store analytics result: {e}")
            raise
    
    # Aggregation Operations
    
    async def get_performance_aggregates(self,
                                       aggregation_level: str,
                                       start_time: datetime,
                                       end_time: datetime) -> List[PerformanceAggregateModel]:
        """
        Get pre-calculated performance aggregates for faster reporting
        
        Args:
            aggregation_level: Level of aggregation (daily, weekly, monthly)
            start_time: Start time for aggregates
            end_time: End time for aggregates
            
        Returns:
            List of performance aggregate models
        """
        start_query_time = datetime.now()
        cache_key = f"aggregates_{aggregation_level}_{start_time}_{end_time}"
        
        try:
            # Check cache
            cached_result = await self._get_from_cache(cache_key)
            if cached_result:
                self._track_query_performance("get_aggregates", start_query_time, len(cached_result), 0, True)
                return [PerformanceAggregateModel(**agg) for agg in cached_result]
            
            # For ClickHouse queries (better for aggregations)
            query = """
                SELECT 
                    aggregate_id,
                    aggregation_level,
                    period_start,
                    period_end,
                    total_trades,
                    winning_trades,
                    losing_trades,
                    total_pnl,
                    gross_profit,
                    gross_loss,
                    win_rate,
                    profit_factor,
                    average_win,
                    average_loss,
                    max_drawdown,
                    volatility,
                    sharpe_ratio,
                    sortino_ratio,
                    model_accuracy,
                    prediction_accuracy,
                    market_conditions,
                    trading_sessions
                FROM performance_aggregates
                WHERE aggregation_level = {aggregation_level:String}
                  AND period_start >= {start_time:DateTime}
                  AND period_end <= {end_time:DateTime}
                ORDER BY period_start ASC
            """
            
            clickhouse_client = await self.db_manager.get_clickhouse_client()
            result = clickhouse_client.query(
                query,
                parameters={
                    "aggregation_level": aggregation_level,
                    "start_time": start_time,
                    "end_time": end_time
                }
            )
            
            # Convert results to models
            aggregates = []
            if result.result_rows:
                columns = result.column_names
                for row in result.result_rows:
                    row_dict = dict(zip(columns, row))
                    
                    # Handle JSON fields
                    if row_dict.get("model_accuracy"):
                        row_dict["model_accuracy"] = json.loads(row_dict["model_accuracy"])
                    if row_dict.get("market_conditions"):
                        row_dict["market_conditions"] = json.loads(row_dict["market_conditions"])
                    if row_dict.get("trading_sessions"):
                        row_dict["trading_sessions"] = json.loads(row_dict["trading_sessions"])
                    
                    # Create period dict
                    row_dict["period"] = {
                        "start": row_dict["period_start"],
                        "end": row_dict["period_end"]
                    }
                    
                    aggregates.append(PerformanceAggregateModel(**row_dict))
            
            # Cache results
            cache_data = [agg.dict() for agg in aggregates]
            await self._set_cache(cache_key, cache_data, self.cache_ttl["aggregates"])
            
            # Track performance
            self._track_query_performance("get_aggregates", start_query_time, len(aggregates), 0, False)
            
            return aggregates
            
        except Exception as e:
            self.logger.error(f"Failed to get performance aggregates: {e}")
            raise
    
    # Utility Methods
    
    def _convert_decimals_to_float(self, data: Dict[str, Any]) -> None:
        """Convert Decimal fields to float for database storage"""
        decimal_fields = [
            'entry_price', 'exit_price', 'quantity', 'pnl', 'fees', 'net_pnl',
            'stop_loss', 'take_profit', 'risk_amount', 'max_favorable_excursion',
            'max_adverse_excursion', 'total_pnl', 'gross_profit', 'gross_loss',
            'average_win', 'average_loss'
        ]
        
        for field in decimal_fields:
            if field in data and isinstance(data[field], Decimal):
                data[field] = float(data[field])
    
    def _convert_floats_to_decimal(self, data: Dict[str, Any]) -> None:
        """Convert float fields back to Decimal for model creation"""
        decimal_fields = [
            'entry_price', 'exit_price', 'quantity', 'pnl', 'fees', 'net_pnl',
            'stop_loss', 'take_profit', 'risk_amount', 'max_favorable_excursion',
            'max_adverse_excursion', 'total_pnl', 'gross_profit', 'gross_loss',
            'average_win', 'average_loss'
        ]
        
        for field in decimal_fields:
            if field in data and data[field] is not None:
                data[field] = Decimal(str(data[field]))
    
    def _track_query_performance(self, 
                                query_type: str,
                                start_time: datetime,
                                rows_returned: int,
                                rows_affected: int,
                                cache_hit: bool) -> None:
        """Track query performance metrics"""
        execution_time = (datetime.now() - start_time).total_seconds()
        
        metric = QueryPerformanceMetrics(
            query_type=query_type,
            execution_time=execution_time,
            rows_returned=rows_returned,
            rows_affected=rows_affected,
            cache_hit=cache_hit,
            timestamp=datetime.now()
        )
        
        self.query_metrics.append(metric)
        
        # Keep only last 1000 metrics
        if len(self.query_metrics) > 1000:
            self.query_metrics = self.query_metrics[-1000:]
        
        # Log slow queries
        if execution_time > 1.0 and not cache_hit:
            self.logger.warning(f"Slow query detected: {query_type} took {execution_time:.2f}s")
    
    async def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get data from Redis cache"""
        try:
            redis_client = await self.db_manager.get_redis_client()
            cached_data = await redis_client.get(f"perf_analytics:{key}")
            
            if cached_data:
                return json.loads(cached_data)
                
        except Exception as e:
            self.logger.warning(f"Cache get failed for key {key}: {e}")
        
        return None
    
    async def _set_cache(self, key: str, data: Any, ttl: int) -> None:
        """Set data in Redis cache with TTL"""
        try:
            redis_client = await self.db_manager.get_redis_client()
            await redis_client.setex(
                f"perf_analytics:{key}",
                ttl,
                json.dumps(data, default=str)
            )
            
        except Exception as e:
            self.logger.warning(f"Cache set failed for key {key}: {e}")
    
    async def _invalidate_cache(self, *keys: str) -> None:
        """Invalidate multiple cache keys"""
        try:
            redis_client = await self.db_manager.get_redis_client()
            
            cache_keys = [f"perf_analytics:{key}" for key in keys]
            if cache_keys:
                await redis_client.delete(*cache_keys)
                
        except Exception as e:
            self.logger.warning(f"Cache invalidation failed: {e}")
    
    async def get_query_performance_stats(self) -> Dict[str, Any]:
        """Get repository query performance statistics"""
        if not self.query_metrics:
            return {"status": "no_data"}
        
        # Aggregate by query type
        stats_by_type = {}
        total_queries = 0
        cache_hits = 0
        
        for metric in self.query_metrics:
            query_type = metric.query_type
            
            if query_type not in stats_by_type:
                stats_by_type[query_type] = {
                    "count": 0,
                    "total_time": 0.0,
                    "cache_hits": 0,
                    "avg_rows_returned": 0,
                    "times": []
                }
            
            stats = stats_by_type[query_type]
            stats["count"] += 1
            stats["total_time"] += metric.execution_time
            stats["avg_rows_returned"] = (
                (stats["avg_rows_returned"] * (stats["count"] - 1) + metric.rows_returned) /
                stats["count"]
            )
            stats["times"].append(metric.execution_time)
            
            if metric.cache_hit:
                stats["cache_hits"] += 1
                cache_hits += 1
            
            total_queries += 1
        
        # Calculate summary statistics
        for query_type, stats in stats_by_type.items():
            times = stats["times"]
            stats["avg_time"] = stats["total_time"] / stats["count"]
            stats["min_time"] = min(times)
            stats["max_time"] = max(times)
            stats["p95_time"] = np.percentile(times, 95) if len(times) > 20 else max(times)
            stats["cache_hit_rate"] = stats["cache_hits"] / stats["count"]
            del stats["times"]  # Remove raw data
        
        return {
            "total_queries": total_queries,
            "overall_cache_hit_rate": cache_hits / total_queries,
            "query_types": stats_by_type,
            "avg_execution_time": sum(m.execution_time for m in self.query_metrics) / len(self.query_metrics),
            "reporting_period": {
                "start": min(m.timestamp for m in self.query_metrics).isoformat(),
                "end": max(m.timestamp for m in self.query_metrics).isoformat()
            }
        }