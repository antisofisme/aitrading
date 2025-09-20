"""
Database Service Client - HTTP client for data-bridge to database-service integration
Handles communication with database-service for tick data storage
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Service-specific infrastructure - use absolute imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))

try:
    from shared.infrastructure.core.logger_core import get_logger
    from shared.infrastructure.core.error_core import handle_error
    from shared.infrastructure.core.performance_core import performance_tracked
    from shared.infrastructure.core.config_core import CoreConfig
except ImportError as e:
    print(f"⚠️ Infrastructure import issue: {e}")
    # Fallback implementations
    import logging
    
    def get_logger(name, version=None):
        return logging.getLogger(name)
    
    def handle_error(service_name, error, context=None):
        print(f"Error in {service_name}: {error}")
        if context:
            print(f"Context: {context}")
    
    def performance_tracked(service_name, operation_name):
        def decorator(func):
            return func
        return decorator
    
    class CoreConfig:
        def __init__(self, service_name=None):
            pass
        def get(self, key, default=None):
            return default

@dataclass
class TickDataBatch:
    """Batch of tick data for database storage"""
    symbol: str
    ticks: List[Dict[str, Any]]
    timestamp: datetime
    batch_size: int

class DatabaseServiceClient:
    """HTTP client for communicating with database-service"""
    
    def __init__(self, service_name: str = "data-bridge"):
        self.service_name = service_name
        self.logger = get_logger(f"{service_name}-db-client", "001")
        self.config = CoreConfig(service_name)
        
        # CRITICAL FIX: Database service endpoint with proper container hostname
        # Use container hostname for Docker deployments
        service_endpoints = self.config.get_service_endpoints()
        if "database-service" in service_endpoints:
            self.database_service_url = service_endpoints["database-service"]
        else:
            # Check environment to determine if running in Docker
            environment = self.config.get('environment', 'development')
            if environment == 'development':
                # In Docker, use container hostname
                self.database_service_url = "http://service-database-service:8008"
            else:
                # Fallback for local development
                self.database_service_url = "http://localhost:8008"
        
        # HTTP session
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Batch processing configuration
        self.batch_size = self.config.get('database.batch_size', 100)
        self.batch_timeout = self.config.get('database.batch_timeout_seconds', 5.0)
        self.max_retry_attempts = self.config.get('database.max_retry_attempts', 3)
        
        # Metrics
        self.metrics = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_ticks_stored": 0,
            "batch_operations": 0,
            "last_operation": None
        }
        
        self.logger.info(f"Database client initialized - endpoint: {self.database_service_url}")
    
    async def initialize(self):
        """Initialize HTTP client session"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=20)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": f"{self.service_name}-client/1.0"
                }
            )
            self.logger.info("HTTP session initialized")
    
    async def close(self):
        """Close HTTP client session"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.logger.info("HTTP session closed")
    
    @performance_tracked("data-bridge-db-client", "store_tick_data")
    async def store_tick_data(self, tick_data: Dict[str, Any]) -> bool:
        """
        Store single tick data in database
        
        Args:
            tick_data: Tick data dictionary with keys: symbol, bid, ask, spread, timestamp, etc.
            
        Returns:
            Success status
        """
        try:
            await self.initialize()
            self.metrics["total_calls"] += 1
            
            # Prepare tick data for ClickHouse schema
            formatted_tick = self._format_tick_for_database(tick_data)
            
            # Make HTTP request to database-service ticks endpoint
            url = f"{self.database_service_url}/api/v1/database/clickhouse/ticks"
            
            # Format data for database-service API
            payload = {
                "tick_data": [formatted_tick],  # API expects tick_data array
                "broker": formatted_tick.get("broker", "FBS-Demo"),
                "account_type": "demo"
            }
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    self.metrics["successful_calls"] += 1
                    self.metrics["total_ticks_stored"] += 1
                    self.metrics["last_operation"] = datetime.now(timezone.utc)
                    
                    response_data = await response.json()
                    self.logger.debug(f"Tick stored successfully: {formatted_tick['symbol']}")
                    return True
                else:
                    self.metrics["failed_calls"] += 1
                    error_text = await response.text()
                    self.logger.error(f"Failed to store tick data: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.metrics["failed_calls"] += 1
            error_context = {
                "operation": "store_tick_data",
                "tick_symbol": tick_data.get("symbol", "unknown"),
                "database_url": self.database_service_url
            }
            handle_error("data-bridge-db-client", e, context=error_context)
            return False
    
    @performance_tracked("data-bridge-db-client", "store_tick_batch")
    async def store_tick_batch(self, tick_batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Store batch of tick data in database for better performance
        
        Args:
            tick_batch: List of tick data dictionaries
            
        Returns:
            Result dictionary with success count and errors
        """
        try:
            await self.initialize()
            self.metrics["total_calls"] += 1
            self.metrics["batch_operations"] += 1
            
            if not tick_batch:
                return {"success": True, "stored_count": 0, "errors": []}
            
            # Format all ticks for database
            formatted_ticks = [self._format_tick_for_database(tick) for tick in tick_batch]
            
            # Make batch HTTP request to database-service
            url = f"{self.database_service_url}/api/v1/database/clickhouse/ticks"
            payload = {
                "tick_data": formatted_ticks,  # API expects tick_data array
                "broker": formatted_ticks[0].get("broker", "FBS-Demo") if formatted_ticks else "FBS-Demo",
                "account_type": "demo"
            }
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    self.metrics["successful_calls"] += 1
                    self.metrics["total_ticks_stored"] += len(formatted_ticks)
                    self.metrics["last_operation"] = datetime.now(timezone.utc)
                    
                    response_data = await response.json()
                    stored_count = response_data.get("stored_count", len(formatted_ticks))
                    
                    self.logger.info(f"Batch stored successfully: {stored_count} ticks")
                    return {
                        "success": True, 
                        "stored_count": stored_count, 
                        "errors": []
                    }
                else:
                    self.metrics["failed_calls"] += 1
                    error_text = await response.text()
                    self.logger.error(f"Failed to store tick batch: {response.status} - {error_text}")
                    return {
                        "success": False,
                        "stored_count": 0,
                        "errors": [f"HTTP {response.status}: {error_text}"]
                    }
                    
        except Exception as e:
            self.metrics["failed_calls"] += 1
            error_context = {
                "operation": "store_tick_batch",
                "batch_size": len(tick_batch),
                "database_url": self.database_service_url
            }
            handle_error("data-bridge-db-client", e, context=error_context)
            return {
                "success": False,
                "stored_count": 0,
                "errors": [str(e)]
            }
    
    @performance_tracked("data-bridge-db-client", "store_account_info")
    async def store_account_info(self, account_data: Dict[str, Any]) -> bool:
        """
        Store account information in database
        
        Args:
            account_data: Account information dictionary
            
        Returns:
            Success status
        """
        try:
            await self.initialize()
            self.metrics["total_calls"] += 1
            
            # Format account data for ClickHouse schema
            formatted_account = self._format_account_for_database(account_data)
            
            # Make HTTP request to database-service
            url = f"{self.database_service_url}/api/v1/clickhouse/account_info"
            
            async with self.session.post(url, json=formatted_account) as response:
                if response.status == 200:
                    self.metrics["successful_calls"] += 1
                    self.logger.debug(f"Account info stored: {formatted_account.get('account_number')}")
                    return True
                else:
                    self.metrics["failed_calls"] += 1
                    error_text = await response.text()
                    self.logger.error(f"Failed to store account info: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.metrics["failed_calls"] += 1
            error_context = {
                "operation": "store_account_info",
                "database_url": self.database_service_url
            }
            handle_error("data-bridge-db-client", e, context=error_context)
            return False
    
    def _format_tick_for_database(self, tick_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format tick data according to SIMPLIFIED ClickHouse ticks schema
        
        SIMPLIFIED Schema fields (5 columns only):
        - timestamp: DateTime64(3)
        - symbol: String
        - bid: Float64
        - ask: Float64
        - broker: String
        """
        current_time = datetime.now(timezone.utc)
        
        # Extract required data with defaults
        symbol = tick_data.get("symbol", "UNKNOWN")
        bid = float(tick_data.get("bid", 0.0))
        ask = float(tick_data.get("ask", 0.0))
        
        # Format timestamp - handle both 'time' and 'timestamp' field names
        timestamp_value = tick_data.get("time") or tick_data.get("timestamp")
        if timestamp_value:
            try:
                if isinstance(timestamp_value, str):
                    timestamp = datetime.fromisoformat(timestamp_value.replace('Z', '+00:00'))
                elif isinstance(timestamp_value, datetime):
                    timestamp = timestamp_value
                else:
                    timestamp = current_time
            except:
                timestamp = current_time
        else:
            timestamp = current_time
        
        # SIMPLIFIED formatting - only 5 columns for the actual simplified table
        formatted_tick = {
            "timestamp": timestamp.isoformat(),
            "symbol": symbol,
            "bid": bid,
            "ask": ask,
            "broker": tick_data.get("broker", "FBS-Demo")
        }
        
        return formatted_tick
    
    def _format_account_for_database(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format account data according to ClickHouse account_info schema"""
        current_time = datetime.now(timezone.utc)
        
        formatted_account = {
            "timestamp": current_time.isoformat(),
            "account_number": str(account_data.get("login", account_data.get("account_number", "0"))),
            "balance": float(account_data.get("balance", 0.0)),
            "equity": float(account_data.get("equity", 0.0)),
            "margin": float(account_data.get("margin", 0.0)),
            "free_margin": float(account_data.get("free_margin", 0.0)),
            "margin_level": float(account_data.get("margin_level", 0.0)) if account_data.get("margin_level") else None,
            "currency": account_data.get("currency", "USD"),
            "server": account_data.get("server", "Unknown"),
            "company": account_data.get("company", "Unknown"),
            "leverage": int(account_data.get("leverage", 100)),
            "broker": account_data.get("broker", "FBS-Demo"),
            "account_type": account_data.get("account_type", "demo")
        }
        
        return formatted_account
    
    # Removed session detection methods - not needed for simplified 5-column table
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get client metrics"""
        success_rate = (
            (self.metrics["successful_calls"] / self.metrics["total_calls"] * 100) 
            if self.metrics["total_calls"] > 0 else 0
        )
        
        return {
            **self.metrics,
            "success_rate_percent": round(success_rate, 2),
            "database_endpoint": self.database_service_url,
            "batch_size": self.batch_size,
            "session_active": self.session is not None and not self.session.closed
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for database service connectivity"""
        try:
            await self.initialize()
            
            url = f"{self.database_service_url}/health"
            async with self.session.get(url) as response:
                if response.status == 200:
                    response_data = await response.json()
                    return {
                        "status": "healthy",
                        "database_service": "available",
                        "response_time_ms": response.headers.get("X-Response-Time", "unknown"),
                        "database_status": response_data
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "database_service": "unavailable",
                        "http_status": response.status,
                        "error": await response.text()
                    }
                    
        except Exception as e:
            return {
                "status": "error",
                "database_service": "unreachable",
                "error": str(e)
            }
    
    @performance_tracked("unknown-service", "insert_economic_event")
    async def insert_economic_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert economic event data into database
        
        Args:
            event_data: Economic event dictionary with keys: event_name, currency, impact, etc.
            
        Returns:
            Result dictionary with success status
        """
        try:
            await self.initialize()
            self.metrics["total_calls"] += 1
            
            # Format economic event for database
            formatted_event = self._format_economic_event_for_database(event_data)
            
            # Make HTTP request to database service
            # TODO: Database service needs economic events endpoint
            url = f"{self.database_service_url}/api/v1/database/clickhouse/insert"
            payload = {
                "table": "economic_calendar",
                "database": "trading_data",
                "data": [formatted_event]
            }
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    self.metrics["successful_calls"] += 1
                    self.metrics["last_operation"] = datetime.now(timezone.utc)
                    
                    self.logger.info(f"Economic event stored: {formatted_event.get('event_name', 'unknown')}")
                    return {"success": True, "event_stored": True}
                else:
                    self.metrics["failed_calls"] += 1 
                    error_text = await response.text()
                    self.logger.error(f"Failed to store economic event: {response.status} - {error_text}")
                    return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
                    
        except Exception as e:
            self.metrics["failed_calls"] += 1
            error_context = {
                "operation": "insert_economic_event",
                "event_data": event_data
            }
            handle_error("database-client", e, error_context)
            return {"success": False, "error": str(e)}
    
    def _format_economic_event_for_database(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format economic event data for database storage"""
        current_time = datetime.now(timezone.utc)
        
        # Extract event timestamp
        timestamp_value = event_data.get("timestamp") or event_data.get("datetime")
        if timestamp_value:
            try:
                if isinstance(timestamp_value, str):
                    timestamp = datetime.fromisoformat(timestamp_value.replace('Z', '+00:00'))
                elif isinstance(timestamp_value, datetime):
                    timestamp = timestamp_value
                else:
                    timestamp = current_time
            except:
                timestamp = current_time
        else:
            timestamp = current_time
        
        # Format economic event for ClickHouse
        formatted_event = {
            "timestamp": timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],  # ClickHouse DateTime64(3) format
            "event_name": str(event_data.get("event_name", "Unknown Event")),
            "currency": str(event_data.get("currency", "USD")),
            "impact": str(event_data.get("impact", "medium")),
            "forecast": str(event_data.get("forecast")) if event_data.get("forecast") is not None else None,
            "previous": str(event_data.get("previous")) if event_data.get("previous") is not None else None,
            "actual": str(event_data.get("actual")) if event_data.get("actual") is not None else None,
            "source": str(event_data.get("source", "unknown")),
            "event_id": str(event_data.get("event_id", f"event_{int(timestamp.timestamp())}")),
            "description": str(event_data.get("description", ""))
        }
        
        return formatted_event

# Global client instance for reuse
_database_client: Optional[DatabaseServiceClient] = None

async def get_database_client() -> DatabaseServiceClient:
    """Get global database client instance"""
    global _database_client
    if _database_client is None:
        _database_client = DatabaseServiceClient()
        await _database_client.initialize()
    return _database_client

async def cleanup_database_client():
    """Cleanup global database client"""
    global _database_client
    if _database_client:
        await _database_client.close()
        _database_client = None

# Export main classes and functions
__all__ = [
    "DatabaseServiceClient",
    "TickDataBatch", 
    "get_database_client",
    "cleanup_database_client"
]