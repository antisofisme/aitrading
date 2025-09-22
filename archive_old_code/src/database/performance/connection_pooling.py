"""
Database Connection Pooling for Sub-50ms Performance
Phase 1 Infrastructure Migration

Implements high-performance connection pooling for:
- PostgreSQL (user management, authentication)
- ClickHouse (analytics, high-frequency data)
- DragonflyDB (real-time caching)
- Multi-database coordination

Target: Sub-50ms query response time
"""

import asyncio
import asyncpg
import aioredis
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from contextlib import asynccontextmanager
import logging
import time
import threading
from datetime import datetime, timedelta
import json
import hashlib
from urllib.parse import urlparse

# ClickHouse async client
from clickhouse_driver import Client as ClickHouseClient
from clickhouse_driver.dbapi.connection import Connection as ClickHouseConnection

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database connection configuration."""
    host: str
    port: int
    database: str
    username: str
    password: str
    min_connections: int = 5
    max_connections: int = 20
    max_queries: int = 50000
    max_inactive_connection_lifetime: float = 300.0  # 5 minutes
    timeout: float = 10.0
    command_timeout: float = 5.0  # Sub-50ms target
    server_settings: Optional[Dict[str, Any]] = None

@dataclass
class PoolMetrics:
    """Connection pool performance metrics."""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    avg_response_time_ms: float = 0.0
    p95_response_time_ms: float = 0.0
    p99_response_time_ms: float = 0.0
    cache_hit_rate: float = 0.0
    last_updated: datetime = None

class PerformanceTracker:
    """Tracks database performance metrics for optimization."""

    def __init__(self, max_samples: int = 10000):
        self.max_samples = max_samples
        self.response_times: List[float] = []
        self.query_counts = {'total': 0, 'success': 0, 'error': 0}
        self.cache_stats = {'hits': 0, 'misses': 0}
        self._lock = threading.Lock()

    def record_query(self, response_time_ms: float, success: bool = True):
        """Record query performance metrics."""
        with self._lock:
            self.response_times.append(response_time_ms)
            if len(self.response_times) > self.max_samples:
                self.response_times.pop(0)

            self.query_counts['total'] += 1
            if success:
                self.query_counts['success'] += 1
            else:
                self.query_counts['error'] += 1

    def record_cache_hit(self, hit: bool):
        """Record cache performance."""
        with self._lock:
            if hit:
                self.cache_stats['hits'] += 1
            else:
                self.cache_stats['misses'] += 1

    def get_metrics(self) -> PoolMetrics:
        """Get current performance metrics."""
        with self._lock:
            if not self.response_times:
                return PoolMetrics(last_updated=datetime.now())

            response_times = sorted(self.response_times)
            n = len(response_times)

            avg_time = sum(response_times) / n
            p95_time = response_times[int(n * 0.95)] if n > 0 else 0
            p99_time = response_times[int(n * 0.99)] if n > 0 else 0

            cache_total = self.cache_stats['hits'] + self.cache_stats['misses']
            cache_hit_rate = (self.cache_stats['hits'] / cache_total * 100) if cache_total > 0 else 0

            return PoolMetrics(
                total_queries=self.query_counts['total'],
                successful_queries=self.query_counts['success'],
                failed_queries=self.query_counts['error'],
                avg_response_time_ms=avg_time,
                p95_response_time_ms=p95_time,
                p99_response_time_ms=p99_time,
                cache_hit_rate=cache_hit_rate,
                last_updated=datetime.now()
            )

class QueryCache:
    """High-performance query result caching."""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def _get_cache_key(self, query: str, params: tuple = None) -> str:
        """Generate cache key for query and parameters."""
        key_data = f"{query}:{params}" if params else query
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, query: str, params: tuple = None) -> Optional[Any]:
        """Get cached query result."""
        cache_key = self._get_cache_key(query, params)

        with self._lock:
            if cache_key in self.cache:
                entry = self.cache[cache_key]
                if datetime.now() - entry['timestamp'] < timedelta(seconds=self.ttl_seconds):
                    return entry['result']
                else:
                    del self.cache[cache_key]

        return None

    def set(self, query: str, result: Any, params: tuple = None):
        """Cache query result."""
        cache_key = self._get_cache_key(query, params)

        with self._lock:
            # Evict oldest entries if cache is full
            if len(self.cache) >= self.max_size:
                oldest_key = min(self.cache.keys(),
                               key=lambda k: self.cache[k]['timestamp'])
                del self.cache[oldest_key]

            self.cache[cache_key] = {
                'result': result,
                'timestamp': datetime.now()
            }

class PostgreSQLPool:
    """High-performance PostgreSQL connection pool."""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None
        self.performance_tracker = PerformanceTracker()
        self.query_cache = QueryCache()
        self._initialized = False

    async def initialize(self):
        """Initialize the connection pool."""
        if self._initialized:
            return

        try:
            self.pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password,
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
                max_queries=self.config.max_queries,
                max_inactive_connection_lifetime=self.config.max_inactive_connection_lifetime,
                timeout=self.config.timeout,
                command_timeout=self.config.command_timeout,
                server_settings=self.config.server_settings or {}
            )
            self._initialized = True
            logger.info(f"PostgreSQL pool initialized: {self.config.host}:{self.config.port}")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL pool: {e}")
            raise

    async def close(self):
        """Close the connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            self._initialized = False

    @asynccontextmanager
    async def acquire_connection(self):
        """Acquire a connection from the pool."""
        if not self._initialized:
            await self.initialize()

        start_time = time.time()
        try:
            async with self.pool.acquire() as connection:
                yield connection

                response_time = (time.time() - start_time) * 1000
                self.performance_tracker.record_query(response_time, True)

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.performance_tracker.record_query(response_time, False)
            logger.error(f"PostgreSQL connection error: {e}")
            raise

    async def execute_query(self, query: str, *args, use_cache: bool = False) -> Any:
        """Execute a query with optional caching."""
        if use_cache:
            cached_result = self.query_cache.get(query, args)
            if cached_result is not None:
                self.performance_tracker.record_cache_hit(True)
                return cached_result
            self.performance_tracker.record_cache_hit(False)

        async with self.acquire_connection() as conn:
            result = await conn.fetch(query, *args)

            if use_cache:
                self.query_cache.set(query, result, args)

            return result

    async def execute_transaction(self, queries: List[tuple]) -> List[Any]:
        """Execute multiple queries in a transaction."""
        async with self.acquire_connection() as conn:
            async with conn.transaction():
                results = []
                for query, args in queries:
                    result = await conn.fetch(query, *args)
                    results.append(result)
                return results

class ClickHousePool:
    """High-performance ClickHouse connection pool."""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.clients: List[ClickHouseClient] = []
        self.performance_tracker = PerformanceTracker()
        self.query_cache = QueryCache()
        self._lock = asyncio.Lock()
        self._current_client = 0

    async def initialize(self):
        """Initialize ClickHouse client pool."""
        try:
            for _ in range(self.config.max_connections):
                client = ClickHouseClient(
                    host=self.config.host,
                    port=self.config.port,
                    database=self.config.database,
                    user=self.config.username,
                    password=self.config.password,
                    connect_timeout=self.config.timeout,
                    send_receive_timeout=self.config.command_timeout,
                    settings=self.config.server_settings or {}
                )
                self.clients.append(client)

            logger.info(f"ClickHouse pool initialized: {len(self.clients)} clients")
        except Exception as e:
            logger.error(f"Failed to initialize ClickHouse pool: {e}")
            raise

    async def get_client(self) -> ClickHouseClient:
        """Get a ClickHouse client using round-robin."""
        async with self._lock:
            client = self.clients[self._current_client]
            self._current_client = (self._current_client + 1) % len(self.clients)
            return client

    async def execute_query(self, query: str, params: dict = None, use_cache: bool = False) -> Any:
        """Execute a ClickHouse query with optional caching."""
        cache_params = tuple(params.items()) if params else None

        if use_cache:
            cached_result = self.query_cache.get(query, cache_params)
            if cached_result is not None:
                self.performance_tracker.record_cache_hit(True)
                return cached_result
            self.performance_tracker.record_cache_hit(False)

        start_time = time.time()
        try:
            client = await self.get_client()
            result = client.execute(query, params or {})

            response_time = (time.time() - start_time) * 1000
            self.performance_tracker.record_query(response_time, True)

            if use_cache:
                self.query_cache.set(query, result, cache_params)

            return result

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.performance_tracker.record_query(response_time, False)
            logger.error(f"ClickHouse query error: {e}")
            raise

    async def insert_data(self, table: str, data: List[Dict[str, Any]]) -> bool:
        """Optimized bulk insert for high-frequency data."""
        if not data:
            return True

        start_time = time.time()
        try:
            client = await self.get_client()
            client.execute(f"INSERT INTO {table} VALUES", data)

            response_time = (time.time() - start_time) * 1000
            self.performance_tracker.record_query(response_time, True)

            return True

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.performance_tracker.record_query(response_time, False)
            logger.error(f"ClickHouse insert error: {e}")
            return False

class DragonflyDBPool:
    """High-performance DragonflyDB connection pool for real-time caching."""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool: Optional[aioredis.ConnectionPool] = None
        self.redis: Optional[aioredis.Redis] = None
        self.performance_tracker = PerformanceTracker()

    async def initialize(self):
        """Initialize DragonflyDB connection pool."""
        try:
            self.pool = aioredis.ConnectionPool(
                host=self.config.host,
                port=self.config.port,
                db=0,  # DragonflyDB uses default database
                username=self.config.username,
                password=self.config.password,
                max_connections=self.config.max_connections,
                socket_timeout=self.config.command_timeout,
                socket_connect_timeout=self.config.timeout
            )

            self.redis = aioredis.Redis(connection_pool=self.pool)

            # Test connection
            await self.redis.ping()

            logger.info(f"DragonflyDB pool initialized: {self.config.host}:{self.config.port}")
        except Exception as e:
            logger.error(f"Failed to initialize DragonflyDB pool: {e}")
            raise

    async def close(self):
        """Close the connection pool."""
        if self.redis:
            await self.redis.close()
        if self.pool:
            await self.pool.disconnect()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        start_time = time.time()
        try:
            result = await self.redis.get(key)

            response_time = (time.time() - start_time) * 1000
            self.performance_tracker.record_query(response_time, True)

            return json.loads(result) if result else None

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.performance_tracker.record_query(response_time, False)
            logger.error(f"DragonflyDB get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL."""
        start_time = time.time()
        try:
            await self.redis.setex(key, ttl, json.dumps(value))

            response_time = (time.time() - start_time) * 1000
            self.performance_tracker.record_query(response_time, True)

            return True

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.performance_tracker.record_query(response_time, False)
            logger.error(f"DragonflyDB set error: {e}")
            return False

    async def mget(self, keys: List[str]) -> List[Optional[Any]]:
        """Get multiple values efficiently."""
        start_time = time.time()
        try:
            results = await self.redis.mget(keys)

            response_time = (time.time() - start_time) * 1000
            self.performance_tracker.record_query(response_time, True)

            return [json.loads(r) if r else None for r in results]

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.performance_tracker.record_query(response_time, False)
            logger.error(f"DragonflyDB mget error: {e}")
            return [None] * len(keys)

class DatabaseManager:
    """Coordinated database manager for all database connections."""

    def __init__(self):
        self.postgresql: Optional[PostgreSQLPool] = None
        self.clickhouse: Optional[ClickHousePool] = None
        self.dragonflydb: Optional[DragonflyDBPool] = None
        self.initialized = False

    async def initialize(self,
                        postgresql_config: DatabaseConfig,
                        clickhouse_config: DatabaseConfig,
                        dragonflydb_config: DatabaseConfig):
        """Initialize all database pools."""
        try:
            # Initialize PostgreSQL pool
            self.postgresql = PostgreSQLPool(postgresql_config)
            await self.postgresql.initialize()

            # Initialize ClickHouse pool
            self.clickhouse = ClickHousePool(clickhouse_config)
            await self.clickhouse.initialize()

            # Initialize DragonflyDB pool
            self.dragonflydb = DragonflyDBPool(dragonflydb_config)
            await self.dragonflydb.initialize()

            self.initialized = True
            logger.info("All database pools initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database manager: {e}")
            await self.close()
            raise

    async def close(self):
        """Close all database pools."""
        if self.postgresql:
            await self.postgresql.close()
        if self.dragonflydb:
            await self.dragonflydb.close()

        self.initialized = False
        logger.info("All database pools closed")

    async def health_check(self) -> Dict[str, Dict[str, Any]]:
        """Perform health check on all database pools."""
        health = {}

        if self.postgresql:
            try:
                async with self.postgresql.acquire_connection() as conn:
                    await conn.fetchrow("SELECT 1 as test")
                health['postgresql'] = {
                    'status': 'healthy',
                    'metrics': self.postgresql.performance_tracker.get_metrics().__dict__
                }
            except Exception as e:
                health['postgresql'] = {'status': 'unhealthy', 'error': str(e)}

        if self.clickhouse:
            try:
                await self.clickhouse.execute_query("SELECT 1 as test")
                health['clickhouse'] = {
                    'status': 'healthy',
                    'metrics': self.clickhouse.performance_tracker.get_metrics().__dict__
                }
            except Exception as e:
                health['clickhouse'] = {'status': 'unhealthy', 'error': str(e)}

        if self.dragonflydb:
            try:
                await self.dragonflydb.redis.ping()
                health['dragonflydb'] = {
                    'status': 'healthy',
                    'metrics': self.dragonflydb.performance_tracker.get_metrics().__dict__
                }
            except Exception as e:
                health['dragonflydb'] = {'status': 'unhealthy', 'error': str(e)}

        return health

    def get_performance_summary(self) -> Dict[str, PoolMetrics]:
        """Get performance summary for all pools."""
        summary = {}

        if self.postgresql:
            summary['postgresql'] = self.postgresql.performance_tracker.get_metrics()
        if self.clickhouse:
            summary['clickhouse'] = self.clickhouse.performance_tracker.get_metrics()
        if self.dragonflydb:
            summary['dragonflydb'] = self.dragonflydb.performance_tracker.get_metrics()

        return summary

# Global database manager instance
db_manager = DatabaseManager()

async def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    return db_manager

# Configuration factory for different environments
def create_database_configs(environment: str = "development") -> Dict[str, DatabaseConfig]:
    """Create database configurations for different environments."""

    if environment == "production":
        return {
            "postgresql": DatabaseConfig(
                host="localhost",
                port=5432,
                database="aitrading_prod",
                username="aitrading_user",
                password="secure_password",
                min_connections=10,
                max_connections=50,
                max_queries=100000,
                timeout=5.0,
                command_timeout=2.0,  # Production sub-50ms target
                server_settings={
                    "application_name": "aitrading_app",
                    "timezone": "UTC"
                }
            ),
            "clickhouse": DatabaseConfig(
                host="localhost",
                port=9000,
                database="aitrading_analytics",
                username="default",
                password="",
                min_connections=5,
                max_connections=25,
                timeout=5.0,
                command_timeout=2.0,
                server_settings={
                    "max_execution_time": 30,
                    "max_memory_usage": 1000000000  # 1GB
                }
            ),
            "dragonflydb": DatabaseConfig(
                host="localhost",
                port=6379,
                database="0",
                username="",
                password="",
                min_connections=5,
                max_connections=20,
                timeout=2.0,
                command_timeout=0.5  # Ultra-fast cache access
            )
        }
    else:  # development
        return {
            "postgresql": DatabaseConfig(
                host="localhost",
                port=5432,
                database="aitrading_dev",
                username="postgres",
                password="postgres",
                min_connections=3,
                max_connections=10,
                timeout=10.0,
                command_timeout=5.0
            ),
            "clickhouse": DatabaseConfig(
                host="localhost",
                port=9000,
                database="aitrading_dev",
                username="default",
                password="",
                min_connections=2,
                max_connections=8,
                timeout=10.0,
                command_timeout=5.0
            ),
            "dragonflydb": DatabaseConfig(
                host="localhost",
                port=6379,
                database="0",
                username="",
                password="",
                min_connections=2,
                max_connections=5,
                timeout=5.0,
                command_timeout=1.0
            )
        }