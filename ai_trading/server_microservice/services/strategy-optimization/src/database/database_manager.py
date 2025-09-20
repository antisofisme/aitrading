"""
Database Manager - Central Database Management
Handles database connections, migrations, and repository coordination
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager
import json
import pickle
import gzip

import asyncpg
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, DateTime, Text, JSON, Float, Integer, Boolean
from sqlalchemy import Index, UniqueConstraint
from alembic.config import Config
from alembic import command

from .strategy_repository import StrategyRepository
from .optimization_repository import OptimizationRepository
from .backtest_repository import BacktestRepository

logger = logging.getLogger(__name__)

Base = declarative_base()


class StrategyTable(Base):
    """SQLAlchemy table for strategy definitions"""
    __tablename__ = "strategies"
    
    strategy_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    strategy_type = Column(String, nullable=False)
    template_id = Column(String)
    version = Column(String, default="1.0.0")
    
    # JSON columns for complex data
    trading_rules = Column(JSON, nullable=False)
    parameters = Column(JSON, nullable=False)  
    risk_parameters = Column(JSON, nullable=False)
    symbols = Column(JSON, nullable=False)
    
    # Strategy metadata
    timeframe = Column(String, default="1D")
    data_requirements = Column(JSON)
    optimization_config = Column(JSON)
    is_optimized = Column(Boolean, default=False)
    
    # Performance tracking
    performance_metrics = Column(JSON)
    backtest_results = Column(JSON, default=list)
    optimization_results = Column(JSON, default=list)
    
    # Status and lifecycle
    status = Column(String, default="draft")
    is_active = Column(Boolean, default=False)
    
    # Timestamps
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    deployed_at = Column(DateTime)
    
    # AI Brain compliance
    confidence_score = Column(Float, default=0.5)
    validation_errors = Column(JSON, default=list)
    
    # Indexes
    __table_args__ = (
        Index('idx_strategy_type_status', 'strategy_type', 'status'),
        Index('idx_strategy_created_at', 'created_at'),
        Index('idx_strategy_active', 'is_active'),
        Index('idx_strategy_template', 'template_id'),
    )


class OptimizationTable(Base):
    """SQLAlchemy table for optimization results"""
    __tablename__ = "optimizations"
    
    optimization_id = Column(String, primary_key=True)
    strategy_id = Column(String, nullable=False)
    optimization_method = Column(String, nullable=False)
    
    # Configuration
    objectives = Column(JSON, nullable=False)
    parameter_bounds = Column(JSON, nullable=False) 
    generations = Column(Integer, nullable=False)
    population_size = Column(Integer, nullable=False)
    
    # Results (compressed for large data)
    best_parameters = Column(Text)  # Compressed JSON
    best_fitness = Column(Float)
    fitness_history = Column(Text)  # Compressed JSON
    pareto_front = Column(Text)     # Compressed JSON
    
    # Analysis
    convergence_generation = Column(Integer)
    convergence_criterion = Column(Float)
    early_stopping = Column(Boolean, default=False)
    
    # Performance
    in_sample_performance = Column(JSON)
    out_of_sample_performance = Column(JSON)
    
    # Statistics
    evaluations_count = Column(Integer)
    optimization_time = Column(Float)
    cpu_time = Column(Float)
    
    # Robustness
    parameter_sensitivity = Column(JSON)
    stability_score = Column(Float)
    
    created_at = Column(DateTime, default=datetime.now)
    
    # Indexes
    __table_args__ = (
        Index('idx_optimization_strategy', 'strategy_id'),
        Index('idx_optimization_method', 'optimization_method'),
        Index('idx_optimization_created', 'created_at'),
        Index('idx_optimization_fitness', 'best_fitness'),
    )


class BacktestTable(Base):
    """SQLAlchemy table for backtest results"""
    __tablename__ = "backtests"
    
    backtest_id = Column(String, primary_key=True)
    strategy_id = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_capital = Column(Float, nullable=False)
    final_capital = Column(Float, nullable=False)
    
    # Performance metrics
    performance_metrics = Column(JSON, nullable=False)
    
    # Time series data (compressed)
    equity_curve = Column(Text)     # Compressed JSON
    drawdown_series = Column(Text)  # Compressed JSON
    returns_series = Column(Text)   # Compressed JSON
    
    # Trade data (compressed)
    trades = Column(Text)           # Compressed JSON
    monthly_returns = Column(JSON)
    
    # Market data info
    symbols_tested = Column(JSON, nullable=False)
    benchmark_symbol = Column(String, default="SPY")
    data_frequency = Column(String, default="1D")
    
    # Execution metrics
    execution_time = Column(Float)
    cpu_time = Column(Float)
    memory_peak = Column(Float)
    
    # Validation flags
    out_of_sample_tested = Column(Boolean, default=False)
    walk_forward_tested = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.now)
    
    # Indexes
    __table_args__ = (
        Index('idx_backtest_strategy', 'strategy_id'),
        Index('idx_backtest_dates', 'start_date', 'end_date'),
        Index('idx_backtest_created', 'created_at'),
        Index('idx_backtest_performance', 'final_capital'),
    )


class DatabaseManager:
    """
    Central database manager for strategy optimization service
    Handles PostgreSQL for structured data and Redis for caching
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize database manager with configuration"""
        self.config = config
        
        # PostgreSQL configuration
        self.pg_host = config.get('postgres_host', 'localhost')
        self.pg_port = config.get('postgres_port', 5432)
        self.pg_database = config.get('postgres_database', 'strategy_optimization')
        self.pg_username = config.get('postgres_username', 'postgres')
        self.pg_password = config.get('postgres_password', 'password')
        
        # Redis configuration
        self.redis_host = config.get('redis_host', 'localhost')
        self.redis_port = config.get('redis_port', 6379)
        self.redis_db = config.get('redis_db', 0)
        self.redis_password = config.get('redis_password')
        
        # Connection pools
        self.pg_engine = None
        self.pg_session_maker = None
        self.redis_pool = None
        
        # Repositories
        self.strategy_repository = None
        self.optimization_repository = None
        self.backtest_repository = None
        
        # Cache settings
        self.cache_ttl = config.get('cache_ttl', 3600)  # 1 hour default
        self.compression_enabled = config.get('compression_enabled', True)
        
        logger.info("DatabaseManager initialized")
    
    async def initialize(self):
        """Initialize database connections and repositories"""
        
        try:
            # Initialize PostgreSQL
            await self._initialize_postgresql()
            
            # Initialize Redis
            await self._initialize_redis()
            
            # Initialize repositories
            await self._initialize_repositories()
            
            # Run migrations
            await self._run_migrations()
            
            logger.info("Database connections initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database connections: {e}")
            raise
    
    async def _initialize_postgresql(self):
        """Initialize PostgreSQL connection"""
        
        # Build connection string
        connection_string = (
            f"postgresql+asyncpg://{self.pg_username}:{self.pg_password}"
            f"@{self.pg_host}:{self.pg_port}/{self.pg_database}"
        )
        
        # Create engine
        self.pg_engine = create_async_engine(
            connection_string,
            echo=False,  # Set to True for SQL debugging
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        
        # Create session maker
        self.pg_session_maker = async_sessionmaker(
            self.pg_engine,
            expire_on_commit=False,
            class_=AsyncSession
        )
        
        logger.info("PostgreSQL connection initialized")
    
    async def _initialize_redis(self):
        """Initialize Redis connection"""
        
        try:
            # Create Redis connection pool
            self.redis_pool = redis.ConnectionPool(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                password=self.redis_password,
                decode_responses=False,  # We handle encoding manually for compression
                max_connections=20
            )
            
            # Test connection
            redis_client = redis.Redis(connection_pool=self.redis_pool)
            await redis_client.ping()
            await redis_client.aclose()
            
            logger.info("Redis connection initialized")
            
        except Exception as e:
            logger.warning(f"Redis initialization failed: {e}. Continuing without cache.")
            self.redis_pool = None
    
    async def _initialize_repositories(self):
        """Initialize data repositories"""
        
        self.strategy_repository = StrategyRepository(self)
        self.optimization_repository = OptimizationRepository(self)
        self.backtest_repository = BacktestRepository(self)
        
        logger.info("Repositories initialized")
    
    async def _run_migrations(self):
        """Run database migrations"""
        
        try:
            # Create all tables
            async with self.pg_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            logger.info("Database migrations completed")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
    
    @asynccontextmanager
    async def get_session(self):
        """Get database session with automatic cleanup"""
        
        async with self.pg_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def get_redis_client(self) -> Optional[redis.Redis]:
        """Get Redis client"""
        
        if not self.redis_pool:
            return None
        
        return redis.Redis(connection_pool=self.redis_pool)
    
    # ==================== CACHE OPERATIONS ====================
    
    async def cache_get(self, key: str) -> Optional[Any]:
        """Get value from cache with optional decompression"""
        
        redis_client = await self.get_redis_client()
        if not redis_client:
            return None
        
        try:
            data = await redis_client.get(key)
            if data is None:
                return None
            
            # Decompress if needed
            if self.compression_enabled:
                try:
                    data = gzip.decompress(data)
                except:
                    pass  # Data might not be compressed
            
            # Deserialize
            return pickle.loads(data)
            
        except Exception as e:
            logger.warning(f"Cache get failed for key {key}: {e}")
            return None
        finally:
            await redis_client.aclose()
    
    async def cache_set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional compression"""
        
        redis_client = await self.get_redis_client()
        if not redis_client:
            return False
        
        try:
            # Serialize
            data = pickle.dumps(value)
            
            # Compress if enabled and data is large enough
            if self.compression_enabled and len(data) > 1024:  # Only compress if >1KB
                data = gzip.compress(data)
            
            # Set with TTL
            ttl = ttl or self.cache_ttl
            await redis_client.setex(key, ttl, data)
            
            return True
            
        except Exception as e:
            logger.warning(f"Cache set failed for key {key}: {e}")
            return False
        finally:
            await redis_client.aclose()
    
    async def cache_delete(self, key: str) -> bool:
        """Delete key from cache"""
        
        redis_client = await self.get_redis_client()
        if not redis_client:
            return False
        
        try:
            await redis_client.delete(key)
            return True
            
        except Exception as e:
            logger.warning(f"Cache delete failed for key {key}: {e}")
            return False
        finally:
            await redis_client.aclose()
    
    async def cache_keys(self, pattern: str) -> List[str]:
        """Get keys matching pattern"""
        
        redis_client = await self.get_redis_client()
        if not redis_client:
            return []
        
        try:
            keys = await redis_client.keys(pattern)
            return [key.decode() for key in keys]
            
        except Exception as e:
            logger.warning(f"Cache keys failed for pattern {pattern}: {e}")
            return []
        finally:
            await redis_client.aclose()
    
    # ==================== UTILITY METHODS ====================
    
    def compress_data(self, data: Any) -> str:
        """Compress data for storage"""
        
        if not self.compression_enabled:
            return json.dumps(data)
        
        try:
            # Serialize to JSON first
            json_data = json.dumps(data).encode('utf-8')
            
            # Compress
            compressed_data = gzip.compress(json_data)
            
            # Encode as base64 for text storage
            import base64
            return base64.b64encode(compressed_data).decode('utf-8')
            
        except Exception as e:
            logger.warning(f"Data compression failed: {e}")
            return json.dumps(data)
    
    def decompress_data(self, compressed_data: str) -> Any:
        """Decompress data from storage"""
        
        if not self.compression_enabled:
            return json.loads(compressed_data)
        
        try:
            import base64
            
            # Decode from base64
            compressed_bytes = base64.b64decode(compressed_data)
            
            # Decompress
            json_data = gzip.decompress(compressed_bytes)
            
            # Deserialize JSON
            return json.loads(json_data.decode('utf-8'))
            
        except Exception as e:
            logger.warning(f"Data decompression failed: {e}")
            # Fallback to regular JSON parsing
            return json.loads(compressed_data)
    
    # ==================== HEALTH AND MONITORING ====================
    
    async def health_check(self) -> Dict[str, Any]:
        """Check database health"""
        
        health_status = {
            "postgresql": {"status": "unknown", "details": {}},
            "redis": {"status": "unknown", "details": {}},
            "overall": "unknown"
        }
        
        # Check PostgreSQL
        try:
            async with self.get_session() as session:
                result = await session.execute("SELECT 1")
                row = result.fetchone()
                
                if row and row[0] == 1:
                    health_status["postgresql"]["status"] = "healthy"
                    health_status["postgresql"]["details"] = {
                        "connection": "active",
                        "response_time": "< 100ms"
                    }
                else:
                    health_status["postgresql"]["status"] = "unhealthy"
                    
        except Exception as e:
            health_status["postgresql"]["status"] = "unhealthy"
            health_status["postgresql"]["details"] = {"error": str(e)}
        
        # Check Redis
        if self.redis_pool:
            try:
                redis_client = await self.get_redis_client()
                if redis_client:
                    await redis_client.ping()
                    health_status["redis"]["status"] = "healthy"
                    health_status["redis"]["details"] = {
                        "connection": "active",
                        "response_time": "< 10ms"
                    }
                    await redis_client.aclose()
                else:
                    health_status["redis"]["status"] = "unavailable"
                    
            except Exception as e:
                health_status["redis"]["status"] = "unhealthy"
                health_status["redis"]["details"] = {"error": str(e)}
        else:
            health_status["redis"]["status"] = "disabled"
        
        # Overall status
        if (health_status["postgresql"]["status"] == "healthy" and 
            health_status["redis"]["status"] in ["healthy", "disabled"]):
            health_status["overall"] = "healthy"
        else:
            health_status["overall"] = "degraded"
        
        return health_status
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        
        stats = {
            "strategies": {"total": 0, "by_status": {}, "by_type": {}},
            "optimizations": {"total": 0, "by_method": {}, "recent": 0},
            "backtests": {"total": 0, "recent": 0},
            "cache": {"keys": 0, "memory_usage": "unknown"}
        }
        
        try:
            # Strategy statistics
            async with self.get_session() as session:
                # Total strategies
                result = await session.execute("SELECT COUNT(*) FROM strategies")
                stats["strategies"]["total"] = result.scalar()
                
                # Strategies by status
                result = await session.execute(
                    "SELECT status, COUNT(*) FROM strategies GROUP BY status"
                )
                for row in result:
                    stats["strategies"]["by_status"][row[0]] = row[1]
                
                # Strategies by type
                result = await session.execute(
                    "SELECT strategy_type, COUNT(*) FROM strategies GROUP BY strategy_type"
                )
                for row in result:
                    stats["strategies"]["by_type"][row[0]] = row[1]
                
                # Total optimizations
                result = await session.execute("SELECT COUNT(*) FROM optimizations")
                stats["optimizations"]["total"] = result.scalar()
                
                # Recent optimizations (last 7 days)
                week_ago = datetime.now() - timedelta(days=7)
                result = await session.execute(
                    "SELECT COUNT(*) FROM optimizations WHERE created_at >= :week_ago",
                    {"week_ago": week_ago}
                )
                stats["optimizations"]["recent"] = result.scalar()
                
                # Optimizations by method
                result = await session.execute(
                    "SELECT optimization_method, COUNT(*) FROM optimizations GROUP BY optimization_method"
                )
                for row in result:
                    stats["optimizations"]["by_method"][row[0]] = row[1]
                
                # Total backtests
                result = await session.execute("SELECT COUNT(*) FROM backtests")
                stats["backtests"]["total"] = result.scalar()
                
                # Recent backtests (last 7 days)
                result = await session.execute(
                    "SELECT COUNT(*) FROM backtests WHERE created_at >= :week_ago",
                    {"week_ago": week_ago}
                )
                stats["backtests"]["recent"] = result.scalar()
        
        except Exception as e:
            logger.error(f"Failed to get database statistics: {e}")
        
        # Cache statistics
        if self.redis_pool:
            try:
                redis_client = await self.get_redis_client()
                if redis_client:
                    info = await redis_client.info()
                    stats["cache"]["keys"] = info.get("db0", {}).get("keys", 0)
                    stats["cache"]["memory_usage"] = info.get("used_memory_human", "unknown")
                    await redis_client.aclose()
            except Exception as e:
                logger.warning(f"Failed to get cache statistics: {e}")
        
        return stats
    
    async def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old data to manage storage"""
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            async with self.get_session() as session:
                # Clean up old optimizations
                result = await session.execute(
                    "DELETE FROM optimizations WHERE created_at < :cutoff_date",
                    {"cutoff_date": cutoff_date}
                )
                optimization_deleted = result.rowcount
                
                # Clean up old backtests (keep those associated with active strategies)
                result = await session.execute(
                    """
                    DELETE FROM backtests 
                    WHERE created_at < :cutoff_date 
                    AND strategy_id NOT IN (
                        SELECT strategy_id FROM strategies WHERE is_active = true
                    )
                    """,
                    {"cutoff_date": cutoff_date}
                )
                backtest_deleted = result.rowcount
                
                await session.commit()
            
            logger.info(f"Cleaned up {optimization_deleted} optimizations and {backtest_deleted} backtests")
            
        except Exception as e:
            logger.error(f"Data cleanup failed: {e}")
    
    async def close(self):
        """Close database connections"""
        
        try:
            if self.pg_engine:
                await self.pg_engine.dispose()
            
            if self.redis_pool:
                await self.redis_pool.disconnect()
            
            logger.info("Database connections closed")
            
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")
    
    # ==================== REPOSITORY ACCESS ====================
    
    def get_strategy_repository(self) -> StrategyRepository:
        """Get strategy repository"""
        return self.strategy_repository
    
    def get_optimization_repository(self) -> OptimizationRepository:
        """Get optimization repository"""
        return self.optimization_repository
    
    def get_backtest_repository(self) -> BacktestRepository:
        """Get backtest repository"""
        return self.backtest_repository