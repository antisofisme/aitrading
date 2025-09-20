"""
Database Manager - Connection Management and Configuration
High-performance database connection management with connection pooling

Features:
- Multi-database connection support (PostgreSQL, ClickHouse, Redis)
- Connection pooling with automatic failover
- Transaction management with rollback support
- Performance monitoring and optimization
- Production-ready error handling
"""

import asyncio
import asyncpg
import logging
from typing import Dict, List, Any, Optional, Union, AsyncContextManager
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import json
import ssl
import os
from dataclasses import dataclass
import aioredis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool, QueuePool
import clickhouse_connect
from clickhouse_connect.driver.client import Client as ClickHouseClient

@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    host: str
    port: int
    database: str
    username: str
    password: str
    ssl_mode: str = "prefer"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600  # 1 hour
    pool_pre_ping: bool = True
    echo: bool = False

@dataclass
class ConnectionPoolStats:
    """Connection pool statistics"""
    pool_size: int
    checked_in: int
    checked_out: int
    overflow: int
    total_connections: int
    failed_connections: int
    avg_connection_time: float
    last_reset: datetime

class DatabaseManager:
    """
    Comprehensive Database Management System
    
    Manages connections to multiple database systems with connection pooling,
    health monitoring, and automatic failover capabilities.
    """
    
    def __init__(self, service_name: str = "performance-analytics"):
        self.service_name = service_name
        self.logger = logging.getLogger(f"{service_name}.database_manager")
        
        # Connection pools and engines
        self._postgres_engine = None
        self._postgres_session_factory = None
        self._clickhouse_client = None
        self._redis_client = None
        
        # Configuration
        self._postgres_config: Optional[DatabaseConfig] = None
        self._clickhouse_config: Optional[DatabaseConfig] = None
        self._redis_config: Optional[Dict[str, Any]] = None
        
        # Connection monitoring
        self._connection_stats: Dict[str, ConnectionPoolStats] = {}
        self._health_check_interval = 60  # seconds
        self._last_health_check = {}
        
        # Performance tracking
        self._query_performance: Dict[str, List[float]] = {}
        self._connection_errors: List[Dict[str, Any]] = []
        
        self.logger.info(f"Database Manager initialized for {service_name}")
    
    async def initialize_postgres(self, config: DatabaseConfig) -> None:
        """
        Initialize PostgreSQL connection pool
        
        Args:
            config: PostgreSQL database configuration
        """
        try:
            self._postgres_config = config
            
            # Build connection URL
            connection_url = (
                f"postgresql+asyncpg://{config.username}:{config.password}@"
                f"{config.host}:{config.port}/{config.database}"
            )
            
            # SSL configuration
            connect_args = {}
            if config.ssl_mode != "disable":
                ssl_context = ssl.create_default_context()
                if config.ssl_mode == "require":
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
                connect_args["ssl"] = ssl_context
            
            # Create async engine with connection pooling
            self._postgres_engine = create_async_engine(
                connection_url,
                poolclass=QueuePool,
                pool_size=config.pool_size,
                max_overflow=config.max_overflow,
                pool_timeout=config.pool_timeout,
                pool_recycle=config.pool_recycle,
                pool_pre_ping=config.pool_pre_ping,
                echo=config.echo,
                connect_args=connect_args
            )
            
            # Create session factory
            self._postgres_session_factory = async_sessionmaker(
                bind=self._postgres_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Test connection
            async with self._postgres_engine.begin() as conn:
                await conn.execute("SELECT 1")
            
            # Initialize connection stats
            self._connection_stats["postgresql"] = ConnectionPoolStats(
                pool_size=config.pool_size,
                checked_in=0,
                checked_out=0,
                overflow=0,
                total_connections=0,
                failed_connections=0,
                avg_connection_time=0.0,
                last_reset=datetime.now()
            )
            
            self.logger.info(f"PostgreSQL connection pool initialized: {config.host}:{config.port}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize PostgreSQL: {e}")
            raise
    
    async def initialize_clickhouse(self, config: DatabaseConfig) -> None:
        """
        Initialize ClickHouse connection
        
        Args:
            config: ClickHouse database configuration
        """
        try:
            self._clickhouse_config = config
            
            # ClickHouse connection settings
            self._clickhouse_client = clickhouse_connect.get_client(
                host=config.host,
                port=config.port,
                database=config.database,
                username=config.username,
                password=config.password,
                secure=(config.ssl_mode != "disable"),
                pool_mgr=True,
                pool_size=config.pool_size
            )
            
            # Test connection
            result = self._clickhouse_client.query("SELECT 1")
            if not result.result_rows:
                raise Exception("ClickHouse connection test failed")
            
            # Initialize connection stats
            self._connection_stats["clickhouse"] = ConnectionPoolStats(
                pool_size=config.pool_size,
                checked_in=0,
                checked_out=0,
                overflow=0,
                total_connections=1,
                failed_connections=0,
                avg_connection_time=0.0,
                last_reset=datetime.now()
            )
            
            self.logger.info(f"ClickHouse connection initialized: {config.host}:{config.port}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ClickHouse: {e}")
            raise
    
    async def initialize_redis(self, redis_url: str, **kwargs) -> None:
        """
        Initialize Redis connection
        
        Args:
            redis_url: Redis connection URL
            **kwargs: Additional Redis configuration
        """
        try:
            self._redis_config = {"url": redis_url, **kwargs}
            
            # Create Redis connection pool
            self._redis_client = aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=kwargs.get("max_connections", 20),
                retry_on_timeout=True,
                health_check_interval=30,
                **kwargs
            )
            
            # Test connection
            await self._redis_client.ping()
            
            # Initialize connection stats
            self._connection_stats["redis"] = ConnectionPoolStats(
                pool_size=kwargs.get("max_connections", 20),
                checked_in=0,
                checked_out=0,
                overflow=0,
                total_connections=1,
                failed_connections=0,
                avg_connection_time=0.0,
                last_reset=datetime.now()
            )
            
            self.logger.info("Redis connection initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Redis: {e}")
            raise
    
    @asynccontextmanager
    async def get_postgres_session(self) -> AsyncContextManager[AsyncSession]:
        """
        Get PostgreSQL database session with automatic transaction management
        
        Returns:
            Async context manager for database session
        """
        if not self._postgres_session_factory:
            raise RuntimeError("PostgreSQL not initialized")
        
        start_time = datetime.now()
        session = None
        
        try:
            session = self._postgres_session_factory()
            
            # Update connection stats
            stats = self._connection_stats.get("postgresql")
            if stats:
                stats.checked_out += 1
            
            yield session
            
            # Commit transaction
            await session.commit()
            
        except Exception as e:
            if session:
                await session.rollback()
            
            # Update error stats
            error_info = {
                "timestamp": datetime.now(),
                "database": "postgresql",
                "error": str(e),
                "error_type": type(e).__name__
            }
            self._connection_errors.append(error_info)
            
            # Keep only last 100 errors
            if len(self._connection_errors) > 100:
                self._connection_errors = self._connection_errors[-100:]
            
            self.logger.error(f"PostgreSQL session error: {e}")
            raise
            
        finally:
            if session:
                await session.close()
                
                # Update connection stats
                connection_time = (datetime.now() - start_time).total_seconds()
                stats = self._connection_stats.get("postgresql")
                if stats:
                    stats.checked_out -= 1
                    stats.checked_in += 1
                    
                    # Update average connection time
                    if stats.total_connections > 0:
                        stats.avg_connection_time = (
                            (stats.avg_connection_time * (stats.total_connections - 1) + connection_time) /
                            stats.total_connections
                        )
    
    async def get_clickhouse_client(self) -> ClickHouseClient:
        """
        Get ClickHouse client
        
        Returns:
            ClickHouse client instance
        """
        if not self._clickhouse_client:
            raise RuntimeError("ClickHouse not initialized")
        
        return self._clickhouse_client
    
    async def get_redis_client(self) -> aioredis.Redis:
        """
        Get Redis client
        
        Returns:
            Redis client instance
        """
        if not self._redis_client:
            raise RuntimeError("Redis not initialized")
        
        return self._redis_client
    
    async def execute_postgres_query(self, query: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Execute PostgreSQL query with performance tracking
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            Query results as list of dictionaries
        """
        start_time = datetime.now()
        
        try:
            async with self.get_postgres_session() as session:
                result = await session.execute(query, params or {})
                rows = result.fetchall()
                
                # Convert to dictionaries
                if rows:
                    columns = result.keys()
                    return [dict(zip(columns, row)) for row in rows]
                return []
                
        except Exception as e:
            self.logger.error(f"PostgreSQL query failed: {e}")
            raise
            
        finally:
            # Track query performance
            execution_time = (datetime.now() - start_time).total_seconds()
            query_type = query.strip().split()[0].upper()
            
            if query_type not in self._query_performance:
                self._query_performance[query_type] = []
            
            self._query_performance[query_type].append(execution_time)
            
            # Keep only last 1000 measurements per query type
            if len(self._query_performance[query_type]) > 1000:
                self._query_performance[query_type] = self._query_performance[query_type][-1000:]
    
    async def execute_clickhouse_query(self, query: str, parameters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Execute ClickHouse query with performance tracking
        
        Args:
            query: SQL query to execute
            parameters: Query parameters
            
        Returns:
            Query results as list of dictionaries
        """
        start_time = datetime.now()
        
        try:
            client = await self.get_clickhouse_client()
            result = client.query(query, parameters=parameters or {})
            
            # Convert to list of dictionaries
            if result.result_rows:
                columns = result.column_names
                return [dict(zip(columns, row)) for row in result.result_rows]
            return []
            
        except Exception as e:
            self.logger.error(f"ClickHouse query failed: {e}")
            raise
            
        finally:
            # Track query performance
            execution_time = (datetime.now() - start_time).total_seconds()
            query_type = query.strip().split()[0].upper()
            
            if f"clickhouse_{query_type}" not in self._query_performance:
                self._query_performance[f"clickhouse_{query_type}"] = []
            
            self._query_performance[f"clickhouse_{query_type}"].append(execution_time)
    
    async def health_check(self) -> Dict[str, Dict[str, Any]]:
        """
        Comprehensive health check for all database connections
        
        Returns:
            Health status for each database system
        """
        health_status = {}
        
        # PostgreSQL health check
        if self._postgres_engine:
            try:
                async with self.get_postgres_session() as session:
                    await session.execute("SELECT 1")
                
                pool = self._postgres_engine.pool
                health_status["postgresql"] = {
                    "status": "healthy",
                    "pool_size": pool.size(),
                    "checked_in": pool.checkedin(),
                    "checked_out": pool.checkedout(),
                    "overflow": pool.overflow(),
                    "last_checked": datetime.now().isoformat()
                }
            except Exception as e:
                health_status["postgresql"] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "last_checked": datetime.now().isoformat()
                }
        
        # ClickHouse health check
        if self._clickhouse_client:
            try:
                client = await self.get_clickhouse_client()
                client.query("SELECT 1")
                
                health_status["clickhouse"] = {
                    "status": "healthy",
                    "last_checked": datetime.now().isoformat()
                }
            except Exception as e:
                health_status["clickhouse"] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "last_checked": datetime.now().isoformat()
                }
        
        # Redis health check
        if self._redis_client:
            try:
                redis_client = await self.get_redis_client()
                await redis_client.ping()
                
                info = await redis_client.info()
                health_status["redis"] = {
                    "status": "healthy",
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory": info.get("used_memory_human", "unknown"),
                    "last_checked": datetime.now().isoformat()
                }
            except Exception as e:
                health_status["redis"] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "last_checked": datetime.now().isoformat()
                }
        
        return health_status
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get database performance metrics
        
        Returns:
            Performance metrics for all database systems
        """
        metrics = {
            "connection_stats": dict(self._connection_stats),
            "query_performance": {},
            "error_summary": {
                "total_errors": len(self._connection_errors),
                "recent_errors": len([
                    e for e in self._connection_errors
                    if (datetime.now() - e["timestamp"]).total_seconds() < 3600  # Last hour
                ])
            }
        }
        
        # Calculate query performance statistics
        for query_type, times in self._query_performance.items():
            if times:
                metrics["query_performance"][query_type] = {
                    "count": len(times),
                    "avg_time": sum(times) / len(times),
                    "min_time": min(times),
                    "max_time": max(times),
                    "p95_time": sorted(times)[int(len(times) * 0.95)] if len(times) > 20 else max(times)
                }
        
        return metrics
    
    async def optimize_connections(self) -> Dict[str, Any]:
        """
        Optimize database connections and performance
        
        Returns:
            Optimization results and recommendations
        """
        optimization_results = {
            "optimizations_applied": [],
            "recommendations": [],
            "performance_improvements": {}
        }
        
        # PostgreSQL optimizations
        if self._postgres_engine:
            try:
                # Check pool utilization
                pool = self._postgres_engine.pool
                utilization = pool.checkedout() / (pool.size() + pool.overflow())
                
                if utilization > 0.8:
                    optimization_results["recommendations"].append(
                        "Consider increasing PostgreSQL pool size (current utilization: {:.1%})".format(utilization)
                    )
                
                # Check for slow queries
                postgres_queries = {k: v for k, v in self._query_performance.items() if not k.startswith("clickhouse_")}
                for query_type, times in postgres_queries.items():
                    if times and len(times) > 10:
                        avg_time = sum(times) / len(times)
                        if avg_time > 1.0:  # Queries taking more than 1 second on average
                            optimization_results["recommendations"].append(
                                f"Optimize {query_type} queries (avg time: {avg_time:.2f}s)"
                            )
                
            except Exception as e:
                self.logger.error(f"PostgreSQL optimization analysis failed: {e}")
        
        # ClickHouse optimizations
        if self._clickhouse_client:
            try:
                clickhouse_queries = {k: v for k, v in self._query_performance.items() if k.startswith("clickhouse_")}
                for query_type, times in clickhouse_queries.items():
                    if times and len(times) > 10:
                        avg_time = sum(times) / len(times)
                        if avg_time > 2.0:  # ClickHouse queries taking more than 2 seconds
                            optimization_results["recommendations"].append(
                                f"Optimize {query_type.replace('clickhouse_', '')} ClickHouse queries (avg time: {avg_time:.2f}s)"
                            )
                
            except Exception as e:
                self.logger.error(f"ClickHouse optimization analysis failed: {e}")
        
        # General recommendations
        error_rate = len(self._connection_errors) / max(1, sum(
            len(times) for times in self._query_performance.values()
        ))
        
        if error_rate > 0.01:  # More than 1% error rate
            optimization_results["recommendations"].append(
                f"High database error rate detected ({error_rate:.2%}). Review connection stability."
            )
        
        return optimization_results
    
    async def backup_configuration(self) -> Dict[str, Any]:
        """
        Backup current database configuration
        
        Returns:
            Serializable configuration backup
        """
        config_backup = {
            "service_name": self.service_name,
            "timestamp": datetime.now().isoformat(),
            "configurations": {}
        }
        
        if self._postgres_config:
            config_backup["configurations"]["postgresql"] = {
                "host": self._postgres_config.host,
                "port": self._postgres_config.port,
                "database": self._postgres_config.database,
                "username": self._postgres_config.username,
                "pool_size": self._postgres_config.pool_size,
                "max_overflow": self._postgres_config.max_overflow,
                "ssl_mode": self._postgres_config.ssl_mode
                # Note: Password not included for security
            }
        
        if self._clickhouse_config:
            config_backup["configurations"]["clickhouse"] = {
                "host": self._clickhouse_config.host,
                "port": self._clickhouse_config.port,
                "database": self._clickhouse_config.database,
                "username": self._clickhouse_config.username,
                "pool_size": self._clickhouse_config.pool_size
                # Note: Password not included for security
            }
        
        if self._redis_config:
            config_backup["configurations"]["redis"] = {
                "url": self._redis_config["url"].split("@")[-1] if "@" in self._redis_config["url"] else self._redis_config["url"],
                # Note: Credentials stripped from URL for security
            }
        
        return config_backup
    
    async def close_all_connections(self):
        """Close all database connections and clean up resources"""
        try:
            # Close PostgreSQL engine
            if self._postgres_engine:
                await self._postgres_engine.dispose()
                self._postgres_engine = None
                self._postgres_session_factory = None
                self.logger.info("PostgreSQL connections closed")
            
            # Close ClickHouse client
            if self._clickhouse_client:
                self._clickhouse_client.close()
                self._clickhouse_client = None
                self.logger.info("ClickHouse connections closed")
            
            # Close Redis client
            if self._redis_client:
                await self._redis_client.close()
                self._redis_client = None
                self.logger.info("Redis connections closed")
            
            self.logger.info("All database connections closed")
            
        except Exception as e:
            self.logger.error(f"Error closing database connections: {e}")
            raise
    
    def __del__(self):
        """Cleanup on object destruction"""
        # Note: In async context, this won't properly close connections
        # Always call close_all_connections() explicitly
        if self._postgres_engine or self._clickhouse_client or self._redis_client:
            self.logger.warning("Database connections not properly closed. Call close_all_connections() explicitly.")

# Utility functions for database initialization

async def create_database_manager(
    postgres_config: Optional[DatabaseConfig] = None,
    clickhouse_config: Optional[DatabaseConfig] = None,
    redis_url: Optional[str] = None,
    service_name: str = "performance-analytics"
) -> DatabaseManager:
    """
    Create and initialize database manager with all configured databases
    
    Args:
        postgres_config: PostgreSQL configuration
        clickhouse_config: ClickHouse configuration  
        redis_url: Redis connection URL
        service_name: Service name for logging
        
    Returns:
        Initialized DatabaseManager instance
    """
    manager = DatabaseManager(service_name)
    
    if postgres_config:
        await manager.initialize_postgres(postgres_config)
    
    if clickhouse_config:
        await manager.initialize_clickhouse(clickhouse_config)
    
    if redis_url:
        await manager.initialize_redis(redis_url)
    
    return manager

def get_database_config_from_env(db_type: str) -> DatabaseConfig:
    """
    Get database configuration from environment variables
    
    Args:
        db_type: Database type ('postgres' or 'clickhouse')
        
    Returns:
        DatabaseConfig instance
    """
    prefix = f"{db_type.upper()}_"
    
    return DatabaseConfig(
        host=os.getenv(f"{prefix}HOST", "localhost"),
        port=int(os.getenv(f"{prefix}PORT", "5432" if db_type == "postgres" else "8123")),
        database=os.getenv(f"{prefix}DATABASE", "performance_analytics"),
        username=os.getenv(f"{prefix}USERNAME", "postgres" if db_type == "postgres" else "default"),
        password=os.getenv(f"{prefix}PASSWORD", ""),
        ssl_mode=os.getenv(f"{prefix}SSL_MODE", "prefer"),
        pool_size=int(os.getenv(f"{prefix}POOL_SIZE", "10")),
        max_overflow=int(os.getenv(f"{prefix}MAX_OVERFLOW", "20")),
        pool_timeout=int(os.getenv(f"{prefix}POOL_TIMEOUT", "30")),
        pool_recycle=int(os.getenv(f"{prefix}POOL_RECYCLE", "3600")),
        echo=os.getenv(f"{prefix}ECHO", "false").lower() == "true"
    )