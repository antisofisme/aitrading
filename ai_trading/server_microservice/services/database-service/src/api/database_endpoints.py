"""
Database Service API Endpoints - Enterprise Architecture
Clean separation of concerns with proper dependency injection and error handling
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional, Union
import time
from datetime import datetime
import asyncio

# Infrastructure integration
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))
from shared.infrastructure.core.logger_core import get_logger
from shared.infrastructure.core.error_core import get_error_handler
from shared.infrastructure.core.performance_core import get_performance_tracker
from shared.infrastructure.core.cache_core import CoreCache
from ..business.database_manager import DatabaseManager


class ClickHouseEndpoints:
    """ClickHouse database endpoints with enterprise patterns"""
    
    def __init__(self, database_manager: DatabaseManager):
        self.router = APIRouter(prefix="/api/v1/database/clickhouse", tags=["Database-ClickHouse"])
        self.database_manager = database_manager
        self.logger = get_logger("database-service", "clickhouse-api")
        self.error_handler = get_error_handler("database-service")
        self.performance_tracker = get_performance_tracker("database-service")
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup ClickHouse API routes"""
        
        @self.router.get("/query")
        async def execute_clickhouse_query(
            query: str = Query(..., description="ClickHouse SQL query"),
            database: str = Query("trading_data", description="Database name")
        ):
            """Execute ClickHouse query with performance tracking"""
            try:
                start_time = time.time()
                
                # Execute query through database manager
                result = await self.database_manager.execute_clickhouse_query(query, database)
                
                duration_ms = (time.time() - start_time) * 1000
                
                self.logger.log_database_query("SELECT", "clickhouse", duration_ms, len(result) if result else 0)
                
                return {
                    "success": True,
                    "database": database,
                    "query_duration_ms": duration_ms,
                    "records_count": len(result) if result else 0,
                    "result": result
                }
                
            except Exception as e:
                return self.error_handler.handle_database_error(e, "execute_clickhouse_query", {
                    "database": database,
                    "query": query
                })
        
        @self.router.post("/insert")
        async def insert_clickhouse_data(request_data: Dict[str, Any]) -> Union[Dict[str, Any], JSONResponse]:
            """Insert data into ClickHouse with validation"""
            try:
                table = request_data.get("table")
                data = request_data.get("data")
                database = request_data.get("database", "trading_data")
                
                # Enhanced input validation
                if not table or not data:
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Table and data are required", "code": "MISSING_PARAMETERS"}
                    )
                
                # Validate table name to prevent injection
                if not table.replace('_', '').isalnum():
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Invalid table name format", "code": "INVALID_TABLE_NAME"}
                    )
                
                start_time = time.time()
                
                # Execute insert through database manager
                result = await self.database_manager.insert_clickhouse_data(table, data, database)
                
                duration_ms = (time.time() - start_time) * 1000
                records_count = len(data) if isinstance(data, list) else 1
                
                self.logger.log_database_query("INSERT", table, duration_ms, records_count)
                
                return {
                    "success": True,
                    "table": table,
                    "database": database,
                    "records_inserted": records_count,
                    "query_duration_ms": duration_ms
                }
                
            except Exception as e:
                return self.error_handler.handle_database_error(e, "insert_clickhouse_data", {
                    "request_data": request_data
                })
        
        @self.router.post("/ticks")
        async def insert_tick_data(request_data: Dict[str, Any]) -> Union[Dict[str, Any], JSONResponse]:
            """Insert MT5 tick data - Optimized for high-frequency trading"""
            try:
                tick_data = request_data.get("tick_data")
                broker = request_data.get("broker", "FBS-Demo")
                account_type = request_data.get("account_type", "demo")
                
                # Enhanced input validation
                if not tick_data:
                    return JSONResponse(
                        status_code=400,
                        content={"error": "tick_data is required", "code": "MISSING_TICK_DATA"}
                    )
                
                # Validate tick data structure
                if isinstance(tick_data, list):
                    if len(tick_data) > 1000:  # Prevent DOS attacks
                        return JSONResponse(
                            status_code=400,
                            content={"error": "Too many ticks in single request (max 1000)", "code": "BATCH_SIZE_EXCEEDED"}
                        )
                
                start_time = time.time()
                
                # Process and insert ticks through database manager
                result = await self.database_manager.insert_tick_data(tick_data, broker, account_type)
                
                duration_ms = (time.time() - start_time) * 1000
                records_count = len(tick_data) if isinstance(tick_data, list) else 1
                
                self.logger.log_database_query("INSERT", "ticks", duration_ms, records_count)
                
                return {
                    "success": True,
                    "table": "ticks",
                    "database": "trading_data",
                    "records_inserted": records_count,
                    "query_duration_ms": duration_ms,
                    "broker": broker,
                    "account_type": account_type
                }
                
            except Exception as e:
                return self.error_handler.handle_database_error(e, "insert_tick_data", {
                    "request_data": request_data
                })
        
        @self.router.get("/ticks/recent")
        async def get_recent_ticks(
            symbol: str = Query(..., description="Symbol to query"),
            broker: str = Query("FBS-Demo", description="Broker name"),
            limit: int = Query(100, description="Number of recent ticks")
        ) -> Union[Dict[str, Any], JSONResponse]:
            """Get recent tick data for MT5-Bridge monitoring"""
            try:
                start_time = time.time()
                
                # Get recent ticks through database manager
                result = await self.database_manager.get_recent_ticks(symbol, broker, limit)
                
                duration_ms = (time.time() - start_time) * 1000
                
                self.logger.log_database_query("SELECT", "ticks", duration_ms, len(result) if result else 0)
                
                return {
                    "success": True,
                    "symbol": symbol,
                    "broker": broker,
                    "query_duration_ms": duration_ms,
                    "ticks_count": len(result) if result else 0,
                    "ticks": result
                }
                
            except Exception as e:
                return self.error_handler.handle_database_error(e, "get_recent_ticks", {
                    "symbol": symbol,
                    "broker": broker
                })


class PostgreSQLEndpoints:
    """PostgreSQL database endpoints"""
    
    def __init__(self, database_manager: DatabaseManager):
        self.router = APIRouter(prefix="/api/v1/database/postgresql", tags=["Database-PostgreSQL"])
        self.database_manager = database_manager
        self.logger = get_logger("database-service", "postgresql-api")
        self.error_handler = get_error_handler("database-service")
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup PostgreSQL API routes"""
        
        @self.router.get("/query")
        async def execute_postgresql_query(
            query: str = Query(..., description="SQL query to execute"),
            database: str = Query("ai_trading_auth", description="Database name")
        ):
            """Execute PostgreSQL query"""
            try:
                start_time = time.time()
                
                result = await self.database_manager.execute_postgresql_query(query, database)
                
                duration_ms = (time.time() - start_time) * 1000
                
                self.logger.log_database_query("SELECT", "postgresql", duration_ms, len(result) if result else 0)
                
                return {
                    "success": True,
                    "database": database,
                    "query_duration_ms": duration_ms,
                    "result": result
                }
                
            except Exception as e:
                return self.error_handler.handle_database_error(e, "execute_postgresql_query", {
                    "database": database,
                    "query": query
                })
        
        @self.router.post("/execute")
        async def execute_postgresql_command(request_data: Dict[str, Any]):
            """Execute PostgreSQL insert/update/delete operations"""
            try:
                query = request_data.get("query")
                database = request_data.get("database", "ai_trading_auth")
                params = request_data.get("params", {})
                
                # Enhanced input validation
                if not query:
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Query is required", "code": "MISSING_QUERY"}
                    )
                
                # Basic query validation to prevent dangerous operations
                dangerous_keywords = ['DROP', 'TRUNCATE', 'DELETE FROM', 'ALTER TABLE']
                query_upper = query.upper()
                for keyword in dangerous_keywords:
                    if keyword in query_upper:
                        return JSONResponse(
                            status_code=403,
                            content={"error": f"Operation not allowed: {keyword}", "code": "FORBIDDEN_OPERATION"}
                        )
                
                start_time = time.time()
                
                result = await self.database_manager.execute_postgresql_command(query, params, database)
                
                duration_ms = (time.time() - start_time) * 1000
                
                self.logger.log_database_query("EXECUTE", "postgresql", duration_ms, result.get('rows_affected', 0))
                
                return {
                    "success": True,
                    "database": database,
                    "query_duration_ms": duration_ms,
                    "rows_affected": result.get("rows_affected", 0)
                }
                
            except Exception as e:
                return self.error_handler.handle_database_error(e, "execute_postgresql_command", {
                    "request_data": request_data
                })


class ArangoDBEndpoints:
    """ArangoDB document database endpoints"""
    
    def __init__(self, database_manager: DatabaseManager):
        self.router = APIRouter(prefix="/api/v1/arangodb", tags=["ArangoDB"])
        self.database_manager = database_manager
        self.logger = get_logger("database-service", "arangodb-api")
        self.error_handler = get_error_handler("database-service")
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup ArangoDB API routes"""
        
        @self.router.get("/query")
        async def arangodb_query(
            query: str = Query(..., description="AQL query"),
            database: str = Query("trading_system", description="Database name")
        ):
            """Execute ArangoDB AQL query"""
            try:
                start_time = time.time()
                
                result = await self.database_manager.execute_arangodb_query(query, database)
                
                duration_ms = (time.time() - start_time) * 1000
                
                self.logger.log_database_query("AQL", "arangodb", duration_ms, len(result) if result else 0)
                
                return {
                    "success": True,
                    "database": database,
                    "query_duration_ms": duration_ms,
                    "result": result
                }
                
            except Exception as e:
                return self.error_handler.handle_database_error(e, "arangodb_query", {
                    "database": database,
                    "query": query
                })


class WeaviateEndpoints:
    """Weaviate vector database endpoints"""
    
    def __init__(self, database_manager: DatabaseManager):
        self.router = APIRouter(prefix="/api/v1/weaviate", tags=["Weaviate"])
        self.database_manager = database_manager
        self.logger = get_logger("database-service", "weaviate-api")
        self.error_handler = get_error_handler("database-service")
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup Weaviate API routes"""
        
        @self.router.get("/search")
        async def weaviate_search(
            query: str = Query(..., description="Search query"),
            class_name: str = Query("TradingDocument", description="Weaviate class name"),
            limit: int = Query(10, description="Result limit")
        ):
            """Search Weaviate vector database"""
            try:
                start_time = time.time()
                
                result = await self.database_manager.search_weaviate(query, class_name, limit)
                
                duration_ms = (time.time() - start_time) * 1000
                
                self.logger.log_database_query("SEARCH", class_name, duration_ms, len(result) if result else 0)
                
                return {
                    "success": True,
                    "class_name": class_name,
                    "query": query,
                    "query_duration_ms": duration_ms,
                    "result": result
                }
                
            except Exception as e:
                return self.error_handler.handle_database_error(e, "weaviate_search", {
                    "query": query,
                    "class_name": class_name
                })


class CacheEndpoints:
    """DragonflyDB cache endpoints"""
    
    def __init__(self, database_manager: DatabaseManager):
        self.router = APIRouter(prefix="/api/v1/cache", tags=["Cache"])
        self.database_manager = database_manager
        self.logger = get_logger("database-service", "cache-api")
        self.error_handler = get_error_handler("database-service")
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup cache API routes"""
        
        @self.router.get("/get/{key}")
        async def cache_get(key: str):
            """Get value from cache"""
            try:
                start_time = time.time()
                
                value = await self.database_manager.cache_get(key)
                
                duration_ms = (time.time() - start_time) * 1000
                
                self.logger.log_database_query("GET", key, duration_ms)
                
                return {
                    "success": True,
                    "key": key,
                    "value": value,
                    "found": value is not None,
                    "query_duration_ms": duration_ms
                }
                
            except Exception as e:
                return self.error_handler.handle_database_error(e, "cache_get", {"key": key})
        
        @self.router.post("/set")
        async def cache_set(request_data: Dict[str, Any]):
            """Set value in cache"""
            try:
                key = request_data.get("key")
                value = request_data.get("value")
                ttl = request_data.get("ttl", 3600)
                
                # Enhanced input validation
                if not key:
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Key is required", "code": "MISSING_KEY"}
                    )
                
                # Validate key format
                if len(key) > 250 or not key.replace('_', '').replace('-', '').replace(':', '').isalnum():
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Invalid key format", "code": "INVALID_KEY_FORMAT"}
                    )
                
                start_time = time.time()
                
                success = await self.database_manager.cache_set(key, value, ttl)
                
                duration_ms = (time.time() - start_time) * 1000
                
                self.logger.log_database_query("SET", key, duration_ms)
                
                return {
                    "success": success,
                    "key": key,
                    "ttl": ttl,
                    "query_duration_ms": duration_ms
                }
                
            except Exception as e:
                return self.error_handler.handle_database_error(e, "cache_set", {"request_data": request_data})


class SchemaEndpoints:
    """Database schema management endpoints"""
    
    def __init__(self, database_manager: DatabaseManager):
        self.router = APIRouter(prefix="/api/v1/schemas", tags=["Schemas"])
        self.database_manager = database_manager
        self.logger = get_logger("database-service", "schema-api")
        self.error_handler = get_error_handler("database-service")
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup schema management routes"""
        
        @self.router.get("/")
        async def list_schemas():
            """List all available database schemas"""
            try:
                schemas = await self.database_manager.get_all_schemas()
                
                return {
                    "success": True,
                    "schemas": schemas,
                    "total_tables": sum(
                        sum(len(tables) for tables in db_schemas.values()) 
                        for db_schemas in schemas.values()
                    )
                }
                
            except Exception as e:
                return self.error_handler.handle_error(e, context={"operation": "list_schemas"})
        
        @self.router.get("/{database_type}/{table_name}")
        async def get_table_schema(database_type: str, table_name: str):
            """Get specific table schema SQL"""
            try:
                schema_sql = await self.database_manager.get_table_schema(database_type, table_name)
                
                if schema_sql:
                    return {
                        "success": True,
                        "database_type": database_type,
                        "table_name": table_name,
                        "schema_sql": schema_sql
                    }
                else:
                    return JSONResponse(
                        status_code=404,
                        content={
                            "error": f"Table '{table_name}' not found in {database_type} schemas"
                        }
                    )
                    
            except Exception as e:
                return self.error_handler.handle_error(e, context={
                    "operation": "get_table_schema",
                    "database_type": database_type,
                    "table_name": table_name
                })
        
        @self.router.post("/tables/create")
        async def create_database_tables(request_data: Dict[str, Any]):
            """Create database tables from schema definitions"""
            try:
                database_type = request_data.get("database_type", "clickhouse")
                table_names = request_data.get("table_names", [])
                force_recreate = request_data.get("force_recreate", False)
                
                # Validate input
                if not table_names:
                    return JSONResponse(
                        status_code=400,
                        content={"error": "table_names is required", "code": "MISSING_TABLE_NAMES"}
                    )
                
                # Validate database type
                supported_databases = ["clickhouse", "postgresql", "arangodb"]
                if database_type not in supported_databases:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "error": f"Unsupported database type: {database_type}",
                            "supported_types": supported_databases,
                            "code": "UNSUPPORTED_DATABASE_TYPE"
                        }
                    )
                
                start_time = time.time()
                
                # Create tables through database manager
                result = await self.database_manager.create_database_tables(
                    database_type, table_names, force_recreate
                )
                
                duration_ms = (time.time() - start_time) * 1000
                
                self.logger.info(f"Tables creation completed - duration: {duration_ms}ms, tables: {len(result.get('created_tables', []))}")
                
                return {
                    "success": True,
                    "database_type": database_type,
                    "creation_duration_ms": duration_ms,
                    "created_tables": result.get("created_tables", []),
                    "failed_tables": result.get("failed_tables", []),
                    "total_requested": len(table_names)
                }
                
            except Exception as e:
                return self.error_handler.handle_error(e, context={
                    "operation": "create_database_tables",
                    "request_data": request_data
                })
        
        @self.router.post("/tables/{database_type}/{table_name}/create")
        async def create_single_table(database_type: str, table_name: str, request_data: Optional[Dict[str, Any]] = None):
            """Create a single database table"""
            try:
                if request_data is None:
                    request_data = {}
                    
                force_recreate = request_data.get("force_recreate", False)
                
                # Validate database type
                supported_databases = ["clickhouse", "postgresql", "arangodb"]
                if database_type not in supported_databases:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "error": f"Unsupported database type: {database_type}",
                            "supported_types": supported_databases,
                            "code": "UNSUPPORTED_DATABASE_TYPE"
                        }
                    )
                
                start_time = time.time()
                
                # Create single table
                result = await self.database_manager.create_single_table(
                    database_type, table_name, force_recreate
                )
                
                duration_ms = (time.time() - start_time) * 1000
                
                self.logger.info(f"Table creation completed - table: {table_name}, duration: {duration_ms}ms")
                
                return {
                    "success": result["success"],
                    "database_type": database_type,
                    "table_name": table_name,
                    "creation_duration_ms": duration_ms,
                    "message": result.get("message", ""),
                    "schema_applied": result.get("schema_applied", False)
                }
                
            except Exception as e:
                return self.error_handler.handle_error(e, context={
                    "operation": "create_single_table",
                    "database_type": database_type,
                    "table_name": table_name
                })


class HealthEndpoints:
    """Health monitoring and status endpoints"""
    
    def __init__(self, database_manager: DatabaseManager):
        self.router = APIRouter(tags=["Health"])
        self.database_manager = database_manager
        self.logger = get_logger("database-service", "health-api")
        self.error_handler = get_error_handler("database-service")
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup health monitoring routes"""
        
        @self.router.get("/health")
        async def health_check():
            """Basic health check endpoint"""
            return {
                "status": "healthy",
                "service": "database-service",
                "timestamp": time.time(),
                "database_status": await self.database_manager.get_health_status(),
                "active_connections": await self.database_manager.get_active_connections_count()
            }
        
        @self.router.get("/status")
        async def service_status():
            """Detailed service status"""
            try:
                status_info = await self.database_manager.get_detailed_status()
                
                return {
                    "service": "database-service",
                    "status": "running",
                    "uptime": time.time(),
                    **status_info
                }
                
            except Exception as e:
                return self.error_handler.handle_error(e, context={"operation": "service_status"})
        
        @self.router.get("/databases")
        async def list_databases():
            """List all available databases"""
            try:
                databases_info = await self.database_manager.get_databases_info()
                
                return {
                    "databases": databases_info["supported_databases"],
                    "connection_status": databases_info["health_status"],
                    "total_databases": len(databases_info["supported_databases"])
                }
                
            except Exception as e:
                return self.error_handler.handle_error(e, context={"operation": "list_databases"})
        
        @self.router.get("/databases/{database_type}/health")
        async def check_database_health(database_type: str):
            """Check health of specific database"""
            try:
                health_status = await self.database_manager.check_database_health(database_type)
                
                if health_status:
                    return {
                        "database_type": database_type,
                        "status": health_status,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return JSONResponse(
                        status_code=404,
                        content={"error": f"Database type {database_type} not supported"}
                    )
                    
            except Exception as e:
                return self.error_handler.handle_error(e, context={
                    "operation": "check_database_health",
                    "database_type": database_type
                })