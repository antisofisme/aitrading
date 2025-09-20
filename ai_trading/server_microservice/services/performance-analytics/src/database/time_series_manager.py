"""
Time Series Manager - Specialized Time-Series Data Management
High-performance time-series data operations with automatic partitioning

Features:
- Automatic time-based partitioning for optimal performance
- Real-time data ingestion with batch optimization
- Time-series specific query optimizations
- Data retention management with automated cleanup
- Compression and storage optimization
"""

import asyncio
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
import numpy as np
import pandas as pd
from enum import Enum
import json

from .database_manager import DatabaseManager
from ..models.performance_models import TimeSeriesModel, TimeSeriesDataPoint

class PartitionStrategy(str, Enum):
    """Time-based partitioning strategies"""
    DAILY = "daily"
    WEEKLY = "weekly" 
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"

class CompressionLevel(str, Enum):
    """Data compression levels"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

@dataclass
class RetentionPolicy:
    """Data retention policy configuration"""
    partition_type: PartitionStrategy
    retain_for_days: int
    compression_after_days: int
    compression_level: CompressionLevel
    archive_after_days: Optional[int] = None

@dataclass  
class TimeSeriesMetadata:
    """Time series metadata and statistics"""
    series_id: str
    total_points: int
    first_timestamp: datetime
    last_timestamp: datetime
    avg_interval_seconds: float
    data_gaps: List[Tuple[datetime, datetime]]
    partition_count: int
    total_size_bytes: int
    compression_ratio: Optional[float] = None

class TimeSeriesManager:
    """
    Specialized Time-Series Data Management System
    
    Provides high-performance operations for time-series data with automatic
    partitioning, retention management, and query optimization.
    """
    
    def __init__(self, db_manager: DatabaseManager, service_name: str = "performance-analytics"):
        self.db_manager = db_manager
        self.service_name = service_name
        self.logger = logging.getLogger(f"{service_name}.time_series_manager")
        
        # Default retention policies by data type
        self.default_retention_policies = {
            "tick_data": RetentionPolicy(
                partition_type=PartitionStrategy.DAILY,
                retain_for_days=90,
                compression_after_days=7,
                compression_level=CompressionLevel.HIGH,
                archive_after_days=365
            ),
            "minute_data": RetentionPolicy(
                partition_type=PartitionStrategy.WEEKLY,
                retain_for_days=365,
                compression_after_days=30,
                compression_level=CompressionLevel.MEDIUM
            ),
            "daily_data": RetentionPolicy(
                partition_type=PartitionStrategy.MONTHLY,
                retain_for_days=1825,  # 5 years
                compression_after_days=90,
                compression_level=CompressionLevel.LOW
            ),
            "performance_metrics": RetentionPolicy(
                partition_type=PartitionStrategy.MONTHLY,
                retain_for_days=1095,  # 3 years
                compression_after_days=30,
                compression_level=CompressionLevel.MEDIUM
            )
        }
        
        # Batch operation settings
        self.batch_settings = {
            "default_batch_size": 10000,
            "max_batch_size": 50000,
            "batch_timeout_seconds": 30,
            "concurrent_batches": 5
        }
        
        # Performance monitoring
        self.operation_stats: Dict[str, List[float]] = {}
        
        self.logger.info(f"Time Series Manager initialized for {service_name}")
    
    async def create_time_series_table(self,
                                     table_name: str,
                                     data_type: str = "performance_metrics",
                                     custom_retention: Optional[RetentionPolicy] = None) -> None:
        """
        Create time-series table with optimal partitioning strategy
        
        Args:
            table_name: Name of the time series table
            data_type: Type of data for retention policy selection
            custom_retention: Custom retention policy override
        """
        try:
            retention_policy = custom_retention or self.default_retention_policies.get(
                data_type, self.default_retention_policies["performance_metrics"]
            )
            
            # Use ClickHouse for time-series tables (better performance)
            clickhouse_client = await self.db_manager.get_clickhouse_client()
            
            # Create the main table with partitioning
            partition_by = self._get_partition_expression(retention_policy.partition_type)
            
            create_table_query = f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    series_id String,
                    timestamp DateTime64(3),
                    value Float64,
                    volume Nullable(Float64),
                    metadata String DEFAULT '{{}}',
                    ingestion_time DateTime DEFAULT now(),
                    partition_key String MATERIALIZED {partition_by}
                ) ENGINE = MergeTree()
                PARTITION BY partition_key
                ORDER BY (series_id, timestamp)
                TTL timestamp + INTERVAL {retention_policy.retain_for_days} DAY DELETE
                SETTINGS index_granularity = 8192
            """
            
            clickhouse_client.execute(create_table_query)
            
            # Create compression policy if specified
            if retention_policy.compression_level != CompressionLevel.NONE:
                compression_query = f"""
                    ALTER TABLE {table_name} 
                    MODIFY TTL timestamp + INTERVAL {retention_policy.compression_after_days} DAY 
                    TO DISK '{retention_policy.compression_level.value}_compression'
                """
                try:
                    clickhouse_client.execute(compression_query)
                except Exception as e:
                    self.logger.warning(f"Compression policy creation failed: {e}")
            
            # Create indexes for common query patterns
            index_queries = [
                f"ALTER TABLE {table_name} ADD INDEX idx_series_time (series_id, timestamp) TYPE minmax GRANULARITY 1",
                f"ALTER TABLE {table_name} ADD INDEX idx_value_range (value) TYPE minmax GRANULARITY 4"
            ]
            
            for index_query in index_queries:
                try:
                    clickhouse_client.execute(index_query)
                except Exception as e:
                    self.logger.debug(f"Index creation skipped (may already exist): {e}")
            
            self.logger.info(f"Time-series table created: {table_name} with {retention_policy.partition_type} partitioning")
            
        except Exception as e:
            self.logger.error(f"Failed to create time-series table {table_name}: {e}")
            raise
    
    async def insert_time_series_data(self,
                                    table_name: str,
                                    series_id: str,
                                    data_points: List[TimeSeriesDataPoint],
                                    batch_size: Optional[int] = None) -> int:
        """
        Insert time-series data with batch optimization
        
        Args:
            table_name: Target table name
            series_id: Time series identifier
            data_points: List of data points to insert
            batch_size: Optional batch size override
            
        Returns:
            Number of data points inserted
        """
        if not data_points:
            return 0
        
        start_time = datetime.now()
        batch_size = batch_size or self.batch_settings["default_batch_size"]
        total_inserted = 0
        
        try:
            clickhouse_client = await self.db_manager.get_clickhouse_client()
            
            # Process in batches
            for i in range(0, len(data_points), batch_size):
                batch = data_points[i:i + batch_size]
                
                # Prepare batch data
                batch_data = []
                for point in batch:
                    batch_data.append([
                        series_id,
                        point.timestamp,
                        point.value,
                        point.volume,
                        json.dumps(point.metadata) if point.metadata else "{}"
                    ])
                
                # Insert batch
                insert_query = f"""
                    INSERT INTO {table_name} (series_id, timestamp, value, volume, metadata)
                    VALUES
                """
                
                clickhouse_client.insert(
                    table_name,
                    batch_data,
                    column_names=['series_id', 'timestamp', 'value', 'volume', 'metadata']
                )
                
                total_inserted += len(batch)
            
            # Track performance
            execution_time = (datetime.now() - start_time).total_seconds()
            self._track_operation_performance("insert_time_series", execution_time, total_inserted)
            
            self.logger.debug(f"Inserted {total_inserted} data points into {table_name}")
            return total_inserted
            
        except Exception as e:
            self.logger.error(f"Failed to insert time-series data: {e}")
            raise
    
    async def query_time_series(self,
                              table_name: str,
                              series_id: str,
                              start_time: datetime,
                              end_time: datetime,
                              aggregation: Optional[str] = None,
                              interval: Optional[str] = None,
                              limit: Optional[int] = None) -> List[TimeSeriesDataPoint]:
        """
        Query time-series data with optional aggregation
        
        Args:
            table_name: Source table name
            series_id: Time series identifier
            start_time: Query start time
            end_time: Query end time
            aggregation: Optional aggregation function (avg, sum, min, max)
            interval: Optional aggregation interval (1m, 5m, 1h, 1d)
            limit: Optional result limit
            
        Returns:
            List of time series data points
        """
        query_start = datetime.now()
        
        try:
            clickhouse_client = await self.db_manager.get_clickhouse_client()
            
            # Build query based on aggregation requirements
            if aggregation and interval:
                # Aggregated query
                agg_func = self._get_aggregation_function(aggregation)
                interval_expr = self._get_interval_expression(interval)
                
                query = f"""
                    SELECT 
                        series_id,
                        {interval_expr} as timestamp,
                        {agg_func}(value) as value,
                        {agg_func}(volume) as volume,
                        '{{}}' as metadata
                    FROM {table_name}
                    WHERE series_id = {{series_id:String}}
                      AND timestamp >= {{start_time:DateTime}}
                      AND timestamp <= {{end_time:DateTime}}
                    GROUP BY series_id, timestamp
                    ORDER BY timestamp ASC
                    {f'LIMIT {limit}' if limit else ''}
                """
            else:
                # Raw data query
                query = f"""
                    SELECT series_id, timestamp, value, volume, metadata
                    FROM {table_name}
                    WHERE series_id = {{series_id:String}}
                      AND timestamp >= {{start_time:DateTime}}
                      AND timestamp <= {{end_time:DateTime}}
                    ORDER BY timestamp ASC
                    {f'LIMIT {limit}' if limit else ''}
                """
            
            # Execute query
            result = clickhouse_client.query(
                query,
                parameters={
                    "series_id": series_id,
                    "start_time": start_time,
                    "end_time": end_time
                }
            )
            
            # Convert results to data points
            data_points = []
            if result.result_rows:
                columns = result.column_names
                for row in result.result_rows:
                    row_dict = dict(zip(columns, row))
                    
                    # Parse metadata
                    metadata = {}
                    if row_dict.get("metadata"):
                        try:
                            metadata = json.loads(row_dict["metadata"])
                        except:
                            pass
                    
                    data_point = TimeSeriesDataPoint(
                        timestamp=row_dict["timestamp"],
                        value=row_dict["value"],
                        volume=row_dict.get("volume"),
                        metadata=metadata
                    )
                    data_points.append(data_point)
            
            # Track performance
            execution_time = (datetime.now() - query_start).total_seconds()
            self._track_operation_performance("query_time_series", execution_time, len(data_points))
            
            return data_points
            
        except Exception as e:
            self.logger.error(f"Failed to query time-series data: {e}")
            raise
    
    async def get_time_series_metadata(self, 
                                     table_name: str,
                                     series_id: str) -> Optional[TimeSeriesMetadata]:
        """
        Get comprehensive metadata for a time series
        
        Args:
            table_name: Table name
            series_id: Series identifier
            
        Returns:
            Time series metadata or None if not found
        """
        try:
            clickhouse_client = await self.db_manager.get_clickhouse_client()
            
            # Get basic statistics
            stats_query = f"""
                SELECT 
                    count(*) as total_points,
                    min(timestamp) as first_timestamp,
                    max(timestamp) as last_timestamp,
                    sum(length(toString(value)) + length(toString(volume)) + length(metadata)) as total_size_bytes
                FROM {table_name}
                WHERE series_id = {{series_id:String}}
            """
            
            stats_result = clickhouse_client.query(
                stats_query,
                parameters={"series_id": series_id}
            )
            
            if not stats_result.result_rows:
                return None
            
            stats_row = stats_result.result_rows[0]
            total_points, first_timestamp, last_timestamp, total_size_bytes = stats_row
            
            # Calculate average interval
            avg_interval_seconds = 0.0
            if total_points > 1 and first_timestamp and last_timestamp:
                total_duration = (last_timestamp - first_timestamp).total_seconds()
                avg_interval_seconds = total_duration / (total_points - 1)
            
            # Get partition count
            partition_query = f"""
                SELECT count(DISTINCT partition_key) as partition_count
                FROM {table_name}
                WHERE series_id = {{series_id:String}}
            """
            
            partition_result = clickhouse_client.query(
                partition_query,
                parameters={"series_id": series_id}
            )
            
            partition_count = partition_result.result_rows[0][0] if partition_result.result_rows else 0
            
            # Detect data gaps (simplified implementation)
            data_gaps = await self._detect_data_gaps(table_name, series_id, first_timestamp, last_timestamp, avg_interval_seconds)
            
            metadata = TimeSeriesMetadata(
                series_id=series_id,
                total_points=total_points,
                first_timestamp=first_timestamp,
                last_timestamp=last_timestamp,
                avg_interval_seconds=avg_interval_seconds,
                data_gaps=data_gaps,
                partition_count=partition_count,
                total_size_bytes=total_size_bytes or 0
            )
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Failed to get time-series metadata: {e}")
            return None
    
    async def optimize_time_series_storage(self, table_name: str) -> Dict[str, Any]:
        """
        Optimize time-series storage with compression and cleanup
        
        Args:
            table_name: Table to optimize
            
        Returns:
            Optimization results and statistics
        """
        optimization_start = datetime.now()
        
        try:
            clickhouse_client = await self.db_manager.get_clickhouse_client()
            optimization_results = {
                "operations_performed": [],
                "space_saved_bytes": 0,
                "partitions_optimized": 0,
                "old_partitions_dropped": 0
            }
            
            # Force merge of parts in all partitions
            optimize_query = f"OPTIMIZE TABLE {table_name} FINAL"
            clickhouse_client.execute(optimize_query)
            optimization_results["operations_performed"].append("partition_merge")
            
            # Get storage statistics before and after
            size_query = f"""
                SELECT 
                    sum(bytes_on_disk) as total_bytes,
                    sum(rows) as total_rows,
                    count(distinct partition) as partition_count
                FROM system.parts
                WHERE table = '{table_name}' AND active = 1
            """
            
            size_result = clickhouse_client.query(size_query)
            if size_result.result_rows:
                total_bytes, total_rows, partition_count = size_result.result_rows[0]
                optimization_results["final_size_bytes"] = total_bytes or 0
                optimization_results["total_rows"] = total_rows or 0
                optimization_results["partitions_optimized"] = partition_count or 0
            
            # Drop old partitions based on TTL (if any expired)
            ttl_query = f"ALTER TABLE {table_name} DROP PARTITION WHERE toYYYYMM(timestamp) < toYYYYMM(now() - INTERVAL 1 YEAR)"
            try:
                clickhouse_client.execute(ttl_query)
                optimization_results["operations_performed"].append("old_partition_cleanup")
            except Exception as e:
                self.logger.debug(f"TTL cleanup skipped: {e}")
            
            # Track optimization performance
            execution_time = (datetime.now() - optimization_start).total_seconds()
            self._track_operation_performance("optimize_storage", execution_time, 1)
            
            optimization_results["optimization_time_seconds"] = execution_time
            self.logger.info(f"Storage optimization completed for {table_name}")
            
            return optimization_results
            
        except Exception as e:
            self.logger.error(f"Failed to optimize time-series storage: {e}")
            raise
    
    async def create_time_series_view(self,
                                    view_name: str,
                                    source_tables: List[str],
                                    aggregation_rules: Dict[str, Any]) -> None:
        """
        Create materialized view for common time-series aggregations
        
        Args:
            view_name: Name of the materialized view
            source_tables: List of source table names
            aggregation_rules: Rules for aggregation (interval, functions, etc.)
        """
        try:
            clickhouse_client = await self.db_manager.get_clickhouse_client()
            
            # Build aggregation query
            interval = aggregation_rules.get("interval", "1h")
            functions = aggregation_rules.get("functions", ["avg"])
            
            interval_expr = self._get_interval_expression(interval)
            
            # Build SELECT clause with aggregation functions
            select_clauses = ["series_id", f"{interval_expr} as timestamp"]
            for func in functions:
                agg_func = self._get_aggregation_function(func)
                select_clauses.append(f"{agg_func}(value) as {func}_value")
                if "volume" in aggregation_rules.get("include_columns", []):
                    select_clauses.append(f"{agg_func}(volume) as {func}_volume")
            
            select_clause = ", ".join(select_clauses)
            
            # Build FROM clause with UNION for multiple tables
            from_clauses = []
            for table in source_tables:
                from_clauses.append(f"SELECT series_id, timestamp, value, volume FROM {table}")
            
            from_clause = " UNION ALL ".join(from_clauses)
            
            # Create materialized view
            create_view_query = f"""
                CREATE MATERIALIZED VIEW IF NOT EXISTS {view_name} (
                    {select_clause.replace(" as ", " ")}
                ) ENGINE = SummingMergeTree()
                ORDER BY (series_id, timestamp)
                AS SELECT {select_clause}
                FROM ({from_clause})
                GROUP BY series_id, timestamp
            """
            
            clickhouse_client.execute(create_view_query)
            
            self.logger.info(f"Materialized view created: {view_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to create time-series view: {e}")
            raise
    
    async def get_storage_statistics(self, table_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive storage statistics for time-series tables
        
        Args:
            table_name: Optional specific table name
            
        Returns:
            Storage statistics and recommendations
        """
        try:
            clickhouse_client = await self.db_manager.get_clickhouse_client()
            
            # Base query for storage stats
            where_clause = f"WHERE table = '{table_name}'" if table_name else ""
            
            stats_query = f"""
                SELECT 
                    table,
                    sum(bytes_on_disk) as total_bytes,
                    sum(rows) as total_rows,
                    count(*) as part_count,
                    count(distinct partition) as partition_count,
                    avg(compression_codec) as avg_compression
                FROM system.parts
                {where_clause} AND active = 1
                GROUP BY table
                ORDER BY total_bytes DESC
            """
            
            result = clickhouse_client.query(stats_query)
            
            statistics = {
                "tables": {},
                "total_storage_bytes": 0,
                "recommendations": []
            }
            
            if result.result_rows:
                for row in result.result_rows:
                    table, total_bytes, total_rows, part_count, partition_count, avg_compression = row
                    
                    table_stats = {
                        "storage_bytes": total_bytes or 0,
                        "total_rows": total_rows or 0,
                        "part_count": part_count or 0,
                        "partition_count": partition_count or 0,
                        "avg_bytes_per_row": (total_bytes or 0) / max(1, total_rows or 1),
                        "compression_ratio": avg_compression or 1.0
                    }
                    
                    statistics["tables"][table] = table_stats
                    statistics["total_storage_bytes"] += table_stats["storage_bytes"]
                    
                    # Generate recommendations
                    if table_stats["part_count"] > 100:
                        statistics["recommendations"].append(f"Consider optimizing {table} - high part count ({part_count})")
                    
                    if table_stats["avg_bytes_per_row"] > 1000:
                        statistics["recommendations"].append(f"Consider compression for {table} - large row size")
            
            return statistics
            
        except Exception as e:
            self.logger.error(f"Failed to get storage statistics: {e}")
            raise
    
    # Utility Methods
    
    def _get_partition_expression(self, strategy: PartitionStrategy) -> str:
        """Get ClickHouse partition expression for strategy"""
        expressions = {
            PartitionStrategy.DAILY: "toYYYYMMDD(timestamp)",
            PartitionStrategy.WEEKLY: "toYYYYMM(timestamp) * 100 + toWeek(timestamp)",
            PartitionStrategy.MONTHLY: "toYYYYMM(timestamp)",
            PartitionStrategy.QUARTERLY: "toYear(timestamp) * 10 + intDiv(toMonth(timestamp) - 1, 3) + 1"
        }
        return expressions.get(strategy, expressions[PartitionStrategy.MONTHLY])
    
    def _get_aggregation_function(self, function_name: str) -> str:
        """Get ClickHouse aggregation function"""
        functions = {
            "avg": "avg",
            "sum": "sum", 
            "min": "min",
            "max": "max",
            "count": "count",
            "median": "quantile(0.5)",
            "p95": "quantile(0.95)",
            "p99": "quantile(0.99)",
            "stddev": "stddevPop"
        }
        return functions.get(function_name, "avg")
    
    def _get_interval_expression(self, interval: str) -> str:
        """Get ClickHouse interval expression"""
        expressions = {
            "1m": "toStartOfMinute(timestamp)",
            "5m": "toDateTime(intDiv(toUInt32(timestamp), 300) * 300)",
            "15m": "toDateTime(intDiv(toUInt32(timestamp), 900) * 900)",
            "1h": "toStartOfHour(timestamp)",
            "4h": "toDateTime(intDiv(toUInt32(timestamp), 14400) * 14400)",
            "1d": "toStartOfDay(timestamp)",
            "1w": "toStartOfWeek(timestamp)",
            "1M": "toStartOfMonth(timestamp)"
        }
        return expressions.get(interval, expressions["1h"])
    
    async def _detect_data_gaps(self,
                              table_name: str,
                              series_id: str,
                              first_timestamp: datetime,
                              last_timestamp: datetime,
                              expected_interval: float) -> List[Tuple[datetime, datetime]]:
        """
        Detect gaps in time series data (simplified implementation)
        
        Returns:
            List of gap periods as (start, end) tuples
        """
        try:
            if expected_interval <= 0 or expected_interval > 86400:  # Skip if interval is unreasonable
                return []
            
            clickhouse_client = await self.db_manager.get_clickhouse_client()
            
            # Sample-based gap detection for performance
            sample_query = f"""
                SELECT timestamp
                FROM {table_name}
                WHERE series_id = {{series_id:String}}
                  AND timestamp >= {{start_time:DateTime}}
                  AND timestamp <= {{end_time:DateTime}}
                ORDER BY timestamp
                LIMIT 10000
            """
            
            result = clickhouse_client.query(
                sample_query,
                parameters={
                    "series_id": series_id,
                    "start_time": first_timestamp,
                    "end_time": last_timestamp
                }
            )
            
            gaps = []
            if result.result_rows and len(result.result_rows) > 1:
                timestamps = [row[0] for row in result.result_rows]
                
                for i in range(1, len(timestamps)):
                    time_diff = (timestamps[i] - timestamps[i-1]).total_seconds()
                    
                    # If gap is more than 2x expected interval, consider it a gap
                    if time_diff > expected_interval * 2:
                        gap_start = timestamps[i-1] + timedelta(seconds=expected_interval)
                        gap_end = timestamps[i] - timedelta(seconds=expected_interval)
                        gaps.append((gap_start, gap_end))
                        
                        # Limit gap detection to avoid performance issues
                        if len(gaps) >= 100:
                            break
            
            return gaps
            
        except Exception as e:
            self.logger.warning(f"Gap detection failed: {e}")
            return []
    
    def _track_operation_performance(self, operation: str, execution_time: float, rows_processed: int) -> None:
        """Track operation performance metrics"""
        if operation not in self.operation_stats:
            self.operation_stats[operation] = []
        
        self.operation_stats[operation].append(execution_time)
        
        # Keep only last 1000 measurements
        if len(self.operation_stats[operation]) > 1000:
            self.operation_stats[operation] = self.operation_stats[operation][-1000:]
        
        # Log slow operations
        if execution_time > 5.0:
            self.logger.warning(f"Slow time-series operation: {operation} took {execution_time:.2f}s for {rows_processed} rows")
    
    async def get_performance_statistics(self) -> Dict[str, Any]:
        """Get time-series operation performance statistics"""
        stats = {}
        
        for operation, times in self.operation_stats.items():
            if times:
                stats[operation] = {
                    "count": len(times),
                    "avg_time": sum(times) / len(times),
                    "min_time": min(times),
                    "max_time": max(times),
                    "p95_time": np.percentile(times, 95) if len(times) > 20 else max(times)
                }
        
        return {
            "operation_stats": stats,
            "total_operations": sum(len(times) for times in self.operation_stats.values()),
            "avg_operation_time": sum(sum(times) for times in self.operation_stats.values()) / 
                                max(1, sum(len(times) for times in self.operation_stats.values()))
        }