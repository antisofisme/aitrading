"""
Standard Database Manager untuk semua services
Menyediakan consistent database access patterns
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import aiopg
import asyncpg
from abc import ABC, abstractmethod


@dataclass
class DatabaseConfig:
    """Database connection configuration"""
    host: str
    port: int
    database: str
    username: str
    password: str
    pool_min_size: int = 5
    pool_max_size: int = 20
    timeout: int = 30
    retry_attempts: int = 3


class DatabaseConnection(ABC):
    """Abstract database connection interface"""

    @abstractmethod
    async def connect(self):
        """Establish connection"""
        pass

    @abstractmethod
    async def disconnect(self):
        """Close connection"""
        pass

    @abstractmethod
    async def execute(self, query: str, params: Optional[Dict] = None) -> Any:
        """Execute query"""
        pass

    @abstractmethod
    async def fetch_one(self, query: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Fetch single row"""
        pass

    @abstractmethod
    async def fetch_many(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """Fetch multiple rows"""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Database health check"""
        pass


class PostgreSQLConnection(DatabaseConnection):
    """PostgreSQL connection implementation"""

    def __init__(self, config: DatabaseConfig, service_name: str):
        self.config = config
        self.service_name = service_name
        self.pool = None
        self.logger = logging.getLogger(f"{service_name}.database")

    async def connect(self):
        """Establish PostgreSQL connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password,
                min_size=self.config.pool_min_size,
                max_size=self.config.pool_max_size,
                command_timeout=self.config.timeout
            )
            self.logger.info("PostgreSQL connection pool established")
        except Exception as e:
            self.logger.error(f"Failed to connect to PostgreSQL: {str(e)}")
            raise

    async def disconnect(self):
        """Close PostgreSQL connection pool"""
        if self.pool:
            await self.pool.close()
            self.logger.info("PostgreSQL connection pool closed")

    async def execute(self, query: str, params: Optional[Dict] = None) -> Any:
        """Execute PostgreSQL query"""
        if not self.pool:
            raise RuntimeError("Database not connected")

        for attempt in range(self.config.retry_attempts):
            try:
                async with self.pool.acquire() as conn:
                    if params:
                        result = await conn.execute(query, *params.values())
                    else:
                        result = await conn.execute(query)
                    return result
            except Exception as e:
                self.logger.warning(f"Query attempt {attempt + 1} failed: {str(e)}")
                if attempt == self.config.retry_attempts - 1:
                    raise
                await asyncio.sleep(0.1 * (attempt + 1))

    async def fetch_one(self, query: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Fetch single row from PostgreSQL"""
        if not self.pool:
            raise RuntimeError("Database not connected")

        for attempt in range(self.config.retry_attempts):
            try:
                async with self.pool.acquire() as conn:
                    if params:
                        row = await conn.fetchrow(query, *params.values())
                    else:
                        row = await conn.fetchrow(query)
                    return dict(row) if row else None
            except Exception as e:
                self.logger.warning(f"Fetch attempt {attempt + 1} failed: {str(e)}")
                if attempt == self.config.retry_attempts - 1:
                    raise
                await asyncio.sleep(0.1 * (attempt + 1))

    async def fetch_many(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """Fetch multiple rows from PostgreSQL"""
        if not self.pool:
            raise RuntimeError("Database not connected")

        for attempt in range(self.config.retry_attempts):
            try:
                async with self.pool.acquire() as conn:
                    if params:
                        rows = await conn.fetch(query, *params.values())
                    else:
                        rows = await conn.fetch(query)
                    return [dict(row) for row in rows]
            except Exception as e:
                self.logger.warning(f"Fetch attempt {attempt + 1} failed: {str(e)}")
                if attempt == self.config.retry_attempts - 1:
                    raise
                await asyncio.sleep(0.1 * (attempt + 1))

    async def health_check(self) -> Dict[str, Any]:
        """PostgreSQL health check"""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                return {
                    "type": "postgresql",
                    "status": "healthy",
                    "response_time_ms": 0,  # TODO: measure actual response time
                    "pool_size": self.pool.get_size(),
                    "pool_max_size": self.config.pool_max_size
                }
        except Exception as e:
            return {
                "type": "postgresql",
                "status": "unhealthy",
                "error": str(e)
            }


class StandardDatabaseManager:
    """
    Standard database manager untuk semua services
    Mendukung multiple database types dengan interface yang konsisten
    """

    def __init__(self, service_name: str, max_connections: int = 20):
        self.service_name = service_name
        self.max_connections = max_connections
        self.connections: Dict[str, DatabaseConnection] = {}
        self.logger = logging.getLogger(f"{service_name}.database_manager")

    async def add_connection(self,
                           name: str,
                           db_type: str,
                           config: DatabaseConfig) -> DatabaseConnection:
        """Add database connection"""

        if db_type.lower() == "postgresql":
            connection = PostgreSQLConnection(config, self.service_name)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

        await connection.connect()
        self.connections[name] = connection

        self.logger.info(f"Added {db_type} connection: {name}")
        return connection

    def get_connection(self, name: str = "default") -> DatabaseConnection:
        """Get database connection by name"""
        if name not in self.connections:
            raise ValueError(f"Database connection '{name}' not found")
        return self.connections[name]

    async def connect(self):
        """Connect to default database"""
        # Default connection setup - can be overridden by services
        pass

    async def disconnect(self):
        """Disconnect all database connections"""
        for name, connection in self.connections.items():
            try:
                await connection.disconnect()
                self.logger.info(f"Disconnected from database: {name}")
            except Exception as e:
                self.logger.error(f"Error disconnecting from {name}: {str(e)}")

    async def execute(self, query: str, params: Optional[Dict] = None, connection_name: str = "default") -> Any:
        """Execute query on specified connection"""
        connection = self.get_connection(connection_name)
        return await connection.execute(query, params)

    async def fetch_one(self, query: str, params: Optional[Dict] = None, connection_name: str = "default") -> Optional[Dict]:
        """Fetch single row from specified connection"""
        connection = self.get_connection(connection_name)
        return await connection.fetch_one(query, params)

    async def fetch_many(self, query: str, params: Optional[Dict] = None, connection_name: str = "default") -> List[Dict]:
        """Fetch multiple rows from specified connection"""
        connection = self.get_connection(connection_name)
        return await connection.fetch_many(query, params)

    async def health_check(self) -> Dict[str, Any]:
        """Health check for all database connections"""
        health_status = {
            "overall_status": "healthy",
            "connections": {}
        }

        unhealthy_count = 0
        for name, connection in self.connections.items():
            try:
                connection_health = await connection.health_check()
                health_status["connections"][name] = connection_health

                if connection_health.get("status") != "healthy":
                    unhealthy_count += 1
            except Exception as e:
                health_status["connections"][name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                unhealthy_count += 1

        # Determine overall status
        if unhealthy_count == 0:
            health_status["overall_status"] = "healthy"
        elif unhealthy_count < len(self.connections):
            health_status["overall_status"] = "degraded"
        else:
            health_status["overall_status"] = "unhealthy"

        health_status["total_connections"] = len(self.connections)
        health_status["unhealthy_connections"] = unhealthy_count

        return health_status

    # Common query patterns
    async def get_by_id(self, table: str, id_value: Any, id_column: str = "id", connection_name: str = "default") -> Optional[Dict]:
        """Standard get by ID pattern"""
        query = f"SELECT * FROM {table} WHERE {id_column} = $1"
        return await self.fetch_one(query, {id_column: id_value}, connection_name)

    async def get_by_user_id(self, table: str, user_id: str, connection_name: str = "default") -> List[Dict]:
        """Standard get by user ID pattern"""
        query = f"SELECT * FROM {table} WHERE user_id = $1"
        return await self.fetch_many(query, {"user_id": user_id}, connection_name)

    async def insert_record(self, table: str, data: Dict[str, Any], connection_name: str = "default") -> Any:
        """Standard insert pattern"""
        columns = list(data.keys())
        placeholders = [f"${i+1}" for i in range(len(columns))]

        query = f"""
            INSERT INTO {table} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            RETURNING *
        """

        return await self.execute(query, data, connection_name)

    async def update_record(self, table: str, id_value: Any, data: Dict[str, Any],
                          id_column: str = "id", connection_name: str = "default") -> Any:
        """Standard update pattern"""
        set_clauses = [f"{col} = ${i+2}" for i, col in enumerate(data.keys())]

        query = f"""
            UPDATE {table}
            SET {', '.join(set_clauses)}, updated_at = NOW()
            WHERE {id_column} = $1
            RETURNING *
        """

        params = {id_column: id_value, **data}
        return await self.execute(query, params, connection_name)

    async def delete_record(self, table: str, id_value: Any, id_column: str = "id", connection_name: str = "default") -> Any:
        """Standard delete pattern"""
        query = f"DELETE FROM {table} WHERE {id_column} = $1"
        return await self.execute(query, {id_column: id_value}, connection_name)